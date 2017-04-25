import logging
import sys
import os
from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import shortuuid
import json
import location_analyzer

ALLOWED_EXTENSIONS = set(['json'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'upload/'
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)

def allowed_file(filename):
   return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
      pois = location_analyzer.analyze(raw_data)
      return render_template('map.html', pois=pois)

   # Default
   return render_template('upload.html')

if __name__ == "__main__":
   app.secret_key = 'It was the best of times, it was the worst of times'
   app.config['SESSION_TYPE'] = 'filesystem'

   app.run(debug=True)
