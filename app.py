from flask import Flask, flash, request, redirect, url_for, render_template, jsonify
from werkzeug.utils import secure_filename

import sys
import os
import json
import logging
import urllib
   
import location_analyzer
import suggester
import db
import precomputed

app = Flask(__name__, static_url_path='/static')
model = db.model(os.environ['PSQL_URI'])

######################################################################
### Constants

ALLOWED_EXTENSIONS = set(['json'])
app.config['UPLOAD_FOLDER'] = 'upload/'

######################################################################
### Routes

@app.route("/static/<path:path>")
def get_static(path):
    """
    Endpoint that serves static files
    """
    return send_from_directory('static', path)

@app.route('/', methods=['GET'])
def home():
   return render_template('upload.html', airports=precomputed.airports)
 
@app.route('/', methods=['POST'])
def upload_location():
   raw_data = ''

   # get location data
   if len(request.form) != 0 and request.form['use_example'] == "1":
      file = open('./data/example_locations.json', 'r')
      raw_data = ''.join(file.readlines())
   else:
      # check if the post request has the file part
      if 'file' not in request.files:
         flash('No file part')
         return redirect(request.url)

      file = request.files['file']
      if file.filename == '':
         flash('No selected file')
         return redirect(request.url)

      if not allowed_file(file.filename):
         flash('Filetype not allowed')
         return redirect(request.url)

      if not file:
         flash('Problems with uploaded file')
         return redirect(request.url)
      
      raw_data = ''.join(file.stream.readlines())

   # analyze location data to get Points of Interests and their
   # probabilities
   pois, data_size = location_analyzer.analyze(raw_data)
   for i, poi in enumerate(pois):
      lat, lon = poi['position']['lat'], poi['position']['lng']
      nearest = model.getNearestAirports(lat, lon)

      if poi['label'] > 30:
         for j in xrange(len(nearest)):
            nearest[j]['is_home'] = True

      nearest.sort(key=lambda x: x['distance'])
      pois[i]['nearbyAirports'] = nearest
      
   return render_template('map.html', pois=pois, data_size=data_size)

@app.route('/map', methods=['GET'])
def show_map_from_manual_entry():
   homes, iatas = get_airport_params(request)
   pois = []
   selected = []
   pos = model.get_airport_locations(iatas)

   for iata in iatas:
      label, is_home = 5, False
      if iata in homes:
         label, is_home = 33, True

      pois.append({'position': pos[iata], 'label': label})
      selected.append({'name': precomputed.iata2name[iata], 'iata': iata, 'is_home': is_home})

   for i, poi in enumerate(pois):
      lat, lon = poi['position']['lat'], poi['position']['lng']
      nearest = model.getNearestAirports(lat, lon)

      if poi['label'] > 30:
         for j in xrange(len(nearest)):
            nearest[j]['is_home'] = True

      nearest.sort(key=lambda x: x['distance'])
      pois[i]['nearbyAirports'] = nearest

   return render_template('map.html', pois=pois, data_size=len(pois), selected=selected)

@app.route('/suggestions', methods=['GET'])
def show_suggestion():
   homes, iatas = get_airport_params(request)
   return jsonify({'suggestions': suggester.get_suggestion(homes, iatas)})

@app.route('/airlines', methods=['GET'])
def show_airlines():
   iatas = request.args.get('IATAs').split(',')
   return jsonify({'airlines': model.getAirlinesCoveringAirports(iatas)})

@app.route('/airlines/<code>', methods=['GET'])
def show_airline_details(code):
   reviews = model.get_airline_reviews(code)
   details = model.get_airline_data(code)
   return render_template('airline.html', code=code, reviews=reviews, details=details)

######################################################################
### Helpers

def get_airport_params(request):
   homes = request.args.get('homes').split(',')
   iatas = request.args.get('IATAs').split(',')

   homes = map(lambda x: urllib.unquote(x).decode('utf8'), homes)
   iatas = map(lambda x: urllib.unquote(x).decode('utf8'), iatas)

   # Home airports must be in the list
   for h in homes:
      if h not in iatas:
         iatas.append(h)

   return homes, iatas

def allowed_file(filename):
   return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

######################################################################
### Main

if __name__ == "__main__":
   app.secret_key = 'It was the best of times, it was the worst of times. Turbo-the-tardigrade'
   app.config['SESSION_TYPE'] = 'filesystem'

   # This is needed to log errors to heroku
   app.logger.addHandler(logging.StreamHandler(sys.stdout))
   app.logger.setLevel(logging.ERROR)

   app.run(debug=True)

