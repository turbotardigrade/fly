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

SELECT airports.iata,
       airports.name,
       airport_rankings.rank,
        St_distance(airport_spatial.location, St_makepoint(%(lat)s, %(lon)s)::geography) as distance
FROM   airports

INNER JOIN airport_spatial
      ON airports.id = airport_spatial.id 
      AND St_dwithin(
      	  airport_spatial.location, 
	  St_makepoint(%(lat)s, %(lon)s)::geography, 50000)

LEFT JOIN airport_rankings
     ON airports.IATA = airport_rankings.IATA

WHERE airports.IATA is not NULL

ORDER BY airport_rankings.rank, St_distance(location, St_makepoint(%(lat)s, %(lon)s) :: geography);

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

    def getAirlineReviews(self, iata):
        cur = self.conn.cursor()
        cur.execute("""

SELECT content, helpful_percentage, rating
FROM flightdiary_airline_comments
WHERE airline_id = (SELECT id FROM flightdiary_airlines WHERE iata = %(iata)s LIMIT 1)
ORDER BY helpful_percentage DESC
LIMIT 10;

        """, {'iata':iata})

        rows = cur.fetchall()
        res = []
        for row in rows:
            it = {}
            it['content'] = row[0]
            it['helpful_percentage'] = row[1]
            it['rating'] = row[2]
            it['from'] = 'flightdiary'
            res.append(it)

        return res
