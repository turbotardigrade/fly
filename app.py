from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename

import sys
import os
import json
import logging

import location_analyzer
import db

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

@app.route('/', methods=['GET', 'POST'])
def upload_file():
   if request.method == 'POST':
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
      pois, data_size = location_analyzer.analyze(raw_data)

      for i, poi in enumerate(pois):
         lat, lon = poi['position']['lat'], poi['position']['lng']
         pois[i]['nearbyAirports'] = model.getNearestAirports(lat, lon)

      return render_template('map.html', pois=pois, data_size=data_size)

   # Default
   return render_template('upload.html')

if __name__ == "__main__":
   app.secret_key = 'It was the best of times, it was the worst of times'
   app.config['SESSION_TYPE'] = 'filesystem'

   # This is needed to log errors to heroku
   app.logger.addHandler(logging.StreamHandler(sys.stdout))
   app.logger.setLevel(logging.ERROR)

   app.run(debug=True)
