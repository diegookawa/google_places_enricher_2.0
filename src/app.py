from flask import Flask, render_template, request, redirect, url_for, jsonify
from dotenv import load_dotenv, set_key
from flows import calculate_coordinates, request_google_places
from werkzeug.utils import secure_filename
from collections import Counter
import ast

import pandas as pd
import csv
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

load_dotenv()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_top_business_types(data):
    all_types = [item.split(',')[0].strip("[]' ") for sublist in data['types'] for item in sublist.split(',')]
    return pd.Series(all_types).value_counts().to_dict()

@app.route('/view_data')
def view_data():
    try:
        csv_path = 'static/data/output/establishments.csv'
        try:
            data = pd.read_csv(csv_path)
        except FileNotFoundError:
            return f"Erro: Arquivo {csv_path} não encontrado."
        except Exception as e:
            return f"Erro ao ler o arquivo CSV: {str(e)}"

        required_columns = {'place_id', 'categories', 'lat', 'lon', 'business_status', 
                            'name', 'price_level', 'rating', 'types', 'user_ratings_total', 'vicinity'}
        missing_columns = required_columns - set(data.columns)
        if missing_columns:
            return f"Erro: Colunas ausentes no CSV: {missing_columns}"

        data.fillna({
            "rating": 0,
            "business_status": "UNKNOWN",
            "name": "Unnamed",
            "user_ratings_total": 0,
            "price_level": "Unknown",
            "categories": "Unknown",
            "types": "Unknown"
        }, inplace=True)

        data['rating'] = pd.to_numeric(data['rating'], errors='coerce').fillna(0)
        data['user_ratings_total'] = pd.to_numeric(data['user_ratings_total'], errors='coerce').fillna(0)

        category_counts = data['categories'].astype(str).value_counts().to_dict()

        price_level_counts = data['price_level'].astype(str).value_counts().to_dict()

        rating_vs_reviews = data[['user_ratings_total', 'rating']].to_dict(orient='records')

        business_status_counts = data['business_status'].value_counts().to_dict()

        business_type_counts = get_top_business_types(data)

        data_json = data.to_dict(orient='records')

        return render_template(
            'view_data.html',
            data=data_json,
            category_counts=category_counts,
            price_level_counts=price_level_counts,
            rating_vs_reviews=rating_vs_reviews,
            business_status_counts=business_status_counts,
            business_type_counts=business_type_counts
        )

    except Exception as e:
        return f"Erro inesperado: {str(e)}"


@app.route('/update_csv', methods=['POST'])
def update_csv():
    data = request.get_json()
    coordinates = data.get('coordinates')

    csv_file_path = 'static/data/output/lat_lon_calculated.csv'

    try:
        with open(csv_file_path, mode='w', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(['lat', 'lon'])
            for coord in coordinates:
                writer.writerow(coord)
        
        result = request_google_places()
        if "successfully" not in result.lower():
            return jsonify({"error": result}), 500

        return jsonify({"message": "CSV updated and Google Places API called successfully!"}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
            return jsonify({'error': 'No file uploaded'}), 400
        file = request.files['csv-file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            df = pd.read_csv(file_path, delimiter=';')
            categories = df['category'].tolist()
            return jsonify({'categories': categories})
        else:
            return jsonify({'error': 'Invalid file format'}), 400
    return render_template('categories.html')

if __name__ == "__main__":
    app.run()
