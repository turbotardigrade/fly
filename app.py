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

def allowed_file(filename):
   return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
   if request.form['use_example'] == "1":
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

   # render templatee
   for i, poi in enumerate(pois):
      lat, lon = poi['position']['lat'], poi['position']['lng']
      pois[i]['nearbyAirports'] = model.getNearestAirports(lat, lon)

   return render_template('map.html', pois=pois, data_size=data_size)

@app.route('/airlines', methods=['GET'])
def list_airlines():
   homes = request.args.get('homes').split(',')
   iatas = request.args.get('IATAs').split(',')

   homes = map(lambda x: urllib.unquote(x).decode('utf8'), homes)
   iatas = map(lambda x: urllib.unquote(x).decode('utf8'), iatas)

   # Home airports must be in the list
   for h in homes:
      if h not in iatas:
         iatas.append(h)
         
   resp = {}
   suggestions = suggester.get_suggestion(homes, iatas)
   suggestions['airlines'] = model.getAirlinesCoveringAirports(suggestions['iatas'])
   resp['suggestions'] = suggestions
   
   return jsonify(resp)

if __name__ == "__main__":
   app.secret_key = 'It was the best of times, it was the worst of times'
   app.config['SESSION_TYPE'] = 'filesystem'

   # This is needed to log errors to heroku
   app.logger.addHandler(logging.StreamHandler(sys.stdout))
   app.logger.setLevel(logging.ERROR)

   app.run(debug=True)
