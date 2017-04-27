import os
import psycopg2
import urlparse # import urllib.parse for python 3+

class model:
    def __init__(self, uri):
        parsed = urlparse.urlparse(uri)
        
        username = parsed.username
        password = parsed.password
        database = parsed.path[1:]
        hostname = parsed.hostname
        
        self.conn = psycopg2.connect(
            database = database,
            user = username,
            password = password,
            host = hostname
        )

    def getNearestAirports(self, lat, lon):
        cur = self.conn.cursor()
        cur.execute("""

SELECT *
FROM
(SELECT airports.iata as iata,
       airports.name as name,
       airport_rankings.rank as rank,
        St_distance(airport_spatial.location, St_makepoint(%(lat)s, %(lon)s)::geography)::int as distance
FROM   airports

INNER JOIN airport_spatial
      ON airports.id = airport_spatial.id 

JOIN airport_rankings
     ON airports.IATA = airport_rankings.IATA

        WHERE airports.IATA != '' AND St_distance(airport_spatial.location, St_makepoint(%(lat)s, %(lon)s)::geography)::int < 300000

ORDER BY distance
LIMIT 5) as t1
UNION
(SELECT airports.iata as iata,
       airports.name as name,
       airport_rankings.rank as rank,
       St_distance(airport_spatial.location, St_makepoint(%(lat)s, %(lon)s)::geography)::int as distance
FROM   airports

INNER JOIN airport_spatial
      ON airports.id = airport_spatial.id 

LEFT JOIN airport_rankings
     ON airports.IATA = airport_rankings.IATA

WHERE airports.IATA != ''
ORDER BY distance
LIMIT 5)

ORDER BY distance;

        """, {'lat': lat, 'lon': lon})

        rows = cur.fetchall()
        res = []
        for row in rows:
            it = {}
            it['IATA'] = row[0]
            it['name'] = row[1]
            it['ranking'] = row[2]
            it['distance'] = row[3]
            res.append(it)

        return res

    def get_airline_data(self, iata):
        cur = self.conn.cursor()
        cur.execute("""

SELECT name, alias, iata, icao, callsign, country, active
FROM airlines
WHERE iata = %(iata)s
LIMIT 1;

        """, {'iata':iata})

        rows = cur.fetchall()
        row = map(lambda x: unicode(str(x), 'utf-8'), rows[0])
        it = {}
        it['name'] = row[0]
        it['alias'] = row[1]
        it['iata'] = row[2]
        it['icao'] = row[3]
        it['callsign'] = row[4]
        it['country'] = row[5]
        it['active'] = row[6]

        return it

    def get_airline_reviews(self, iata):
        cur = self.conn.cursor()
        cur.execute("""

SELECT content, helpful_percentage, rating, name, url
FROM flightdiary_airline_comments
WHERE airline_id = (SELECT id FROM flightdiary_airlines WHERE iata = %(iata)s LIMIT 1)
ORDER BY helpful_percentage DESC
LIMIT 10;

        """, {'iata':iata})

        rows = cur.fetchall()
        res = []
        for row in rows:
            row = map(lambda x: unicode(str(x), 'utf-8'), row)
            it = {}
            it['content'] = row[0]
            it['helpful_percentage'] = row[1]
            it['rating'] = row[2]
            it['name'] = row[3]
            it['from'] = 'flightdiary'
            it['url'] = row[4]
            res.append(it)

        return res

    def getAirlinesCoveringAirports(self, iatas):
        cur = self.conn.cursor()
        cur.execute("""
SELECT airline, count(*) as num_routes, (count(*) * 1.0) / sum(count(*)) over() as p
FROM routes
INNER JOIN (
  SELECT src, dest FROM routes_unique
  WHERE src = ANY(%(iatas)s) OR dest = ANY(%(iatas)s)
  ) AS my_routes
ON (routes.src_airport = my_routes.src AND routes.dest_airport = my_routes.dest)
GROUP BY airline
ORDER BY p DESC;
        """, {'iatas': iatas})

        rows = cur.fetchall()
        res = []
        for row in rows:
            it = {}
            it['iata'] = row[0]
            it['num_routes'] = row[1]
            it['p'] = str(row[2])
            res.append(it)

        return res

    def get_airport_locations(self, iatas):
        cur = self.conn.cursor()
        cur.execute("""

SELECT iata, latitude as lat, longitude as lon
FROM airports
WHERE iata IN (%s)

        """ % ','.join(map(lambda x: "'"+x+"'", iatas))) # UNSAFE

        locations = {}
        for row in cur.fetchall():
            locations[row[0]] = {'lat': row[1], 'lng': row[2]}

        return locations

    def getPricesCoveringAirports(self, iatas):
        cur = self.conn.cursor()
        # The last join condition is really long because skyscanner prices are for return tickets
        # which may have different outbound and inbound carriers
        # therefore we need to match both directions of a quote separately, and use DISTINCT to deduplicate
        # when they happen to be the same carrier
        cur.execute("""
SELECT DISTINCT prices.origin, prices.destination, prices.minprice, airlines.name
FROM routes
INNER JOIN (
  SELECT src, dest FROM routes_unique
  WHERE src = ANY(%(iatas)s) OR dest = ANY(%(iatas)s)
) AS my_routes
ON (routes.src_airport = my_routes.src AND routes.dest_airport = my_routes.dest)
INNER JOIN airlines
ON routes.airline = airlines.iata
INNER JOIN sky_open_join
ON sky_open_join.open_name = airlines.name
INNER JOIN prices
ON (
  prices.origin = routes.src_airport
  AND prices.destination = routes.dest_airport
  AND prices.outboundcarrier = sky_open_join.sky_name)
  OR (
  prices.origin = routes.dest_airport
  AND prices.destination = routes.src_airport
  AND prices.inboundcarrier = sky_open_join.sky_name);
        """, {'iatas': iatas})

        rows = cur.fetchall()
        res = []
        for row in rows:
            it = {}
            it['origin'] = rows[0]
            it['destination'] = rows[1]
            it['minprice'] = str(rows[2])
            it['airline'] = rows[3]
            res.append(it)

        return res
