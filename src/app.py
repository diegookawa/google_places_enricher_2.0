from flask import Flask, render_template, request, redirect, url_for, jsonify
from dotenv import load_dotenv, set_key
from flows import calculate_coordinates
from werkzeug.utils import secure_filename
import pandas as pd
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

load_dotenv()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/calculate_coordinates", methods=["POST"])
def calculate_coordinates_route():
    data = request.get_json()
    radius = data.get("radius")
    southwest_lat = data.get("southwestLat")
    southwest_lon = data.get("southwestLon")
    northeast_lat = data.get("northeastLat")
    northeast_lon = data.get("northeastLon")
    result = calculate_coordinates(
        radius, southwest_lat, southwest_lon, northeast_lat, northeast_lon
    )
    
    return jsonify(result)

@app.route("/get_coordinates", methods=["GET"])
def get_coordinates_route():
    data = pd.read_csv("../data/output/lat_lon_calculated.csv")
    json_data = data.to_json(orient="records")
    return json_data

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        api_key = request.form.get("apiKey")
        if api_key:
            dotenv_path = "../.env"
            set_key(dotenv_path, "KEY", api_key)
            return redirect(url_for("coordinates_definition"))
    return render_template("main_page.html")

@app.route("/coordinates_definition")
def coordinates_definition():
    api_key = os.getenv("KEY")
    return render_template("coordinates_definition.html", api_key=api_key)

@app.route("/components_result")
def components_result():
    return render_template("components_result.html")

@app.route("/coordinates_result")
def coordinates_results():
    file_name = request.args.get("file", "../data/output/lat_lon_calculated.csv")
    return render_template("coordinates_result.html", file_name=file_name)

@app.route('/categories', methods=['GET', 'POST'])
def categories():
    if request.method == 'POST':
        if 'csv-file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        file = request.files['csv-file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            df = pd.read_csv(file_path, delimiter=';')
            categories = df['category'].tolist()
            return jsonify({'categories': categories})
        else:
            return jsonify({'error': 'Formato de arquivo não permitido'}), 400
    return render_template('categories.html')

if __name__ == "__main__":
    app.run()