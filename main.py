import os
from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import shortuuid
import json
import location_analyzer

ALLOWED_EXTENSIONS = set(['json'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'upload/'

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
      
      filename = shortuuid.uuid()
      filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
      file.save(filepath)
      
      pois = location_analyzer.analyze(filepath)
      return render_template('map.html', pois=pois)

   # Default
   return render_template('upload.html')

if __name__ == "__main__":
   if not os.path.exists(app.config['UPLOAD_FOLDER']):
      os.makedirs(app.config['UPLOAD_FOLDER'])
    
   app.secret_key = 'It was the best of times, it was the worst of times'
   app.config['SESSION_TYPE'] = 'filesystem'

   app.run(debug=True)
