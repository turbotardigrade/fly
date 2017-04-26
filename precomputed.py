import json
import pprint

airports = []

with open('./data/airports.json') as data_file:    
    airports = json.load(data_file)
    airports = filter(lambda x: x['iata'] is not None, airports)
    airports = filter(lambda x: len(x['iata'].strip()) == 3, airports)
    airports.sort(key=lambda x: x['iata'])
    print '%d airport preloaded' % len(airports)
