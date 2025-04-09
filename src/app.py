from flask import Flask, render_template, request, redirect, url_for, jsonify
from dotenv import load_dotenv, set_key
from flows import calculate_coordinates, request_google_places
from werkzeug.utils import secure_filename
from utils import calculate_similarity_sentences

import pandas as pd
import csv
import os
import uuid
import datetime

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

# @app.route('/call_google_places_api', methods=['POST'])
# def call_api():
#     result = request_google_places()
#     if "successfully" not in result.lower():
#         return jsonify({"error": result}), 500

#     return jsonify({"message": "CSV updated and Google Places API called successfully!"}), 200

@app.route('/update_coordinates_csv', methods=['POST'])
def update_coordinates_csv():
    data = request.get_json()
    coordinates = data.get('coordinates')

    csv_file_path = 'static/data/output/lat_lon_calculated.csv'

    try:
        with open(csv_file_path, mode='w', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(['lat', 'lon'])
            for coord in coordinates:
                writer.writerow(coord)
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_categories', methods=['GET'])
def get_categories():
    categories = []
    file_path = 'static/data/input/categories_request.csv' 
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 500 

    try:
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=';') 
            next(reader, None) 
            for row in reader:
                categories.append(row[0])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'categories': categories})

@app.route('/update_categories_csv', methods=['POST'])
def update_categories_csv():
    data = request.get_json()
    categories = data.get('categories')
    print(categories)

    csv_file_path = 'static/data/input/categories_request.csv'

    try:
        with open(csv_file_path, mode='w', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(['category'])
            for cat in categories:
                writer.writerow(cat) 
        
        result = request_google_places()
        if "successfully" not in result.lower():
            return jsonify({"error": result}), 500

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

@app.route('/enrich_data')
def enrich_data():
    return render_template('enrich_data.html')

@app.route('/get_enrichment_categories', methods=['GET'])
def get_enrichment_categories():
    categories = []
    file_path = 'static/data/input/enrichment_categories.csv'
    if not os.path.exists(file_path):
        return jsonify({'categories': categories})

    try:
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            next(reader, None)
            for row in reader:
                categories.append(row[0])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'categories': categories})

@app.route('/enrichment_categories', methods=['POST'])
def enrichment_categories():
    data = request.get_json()
    categories = data.get('categories')

    csv_file_path = 'static/data/input/enrichment_categories.csv'

    try:
        with open(csv_file_path, mode='w', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(['category'])
            for cat in categories:
                writer.writerow([cat['category']])

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'message': 'Categories updated successfully.'}), 200

@app.route('/get_available_datasets', methods=['GET'])
def get_available_datasets():
    datasets = []
    output_dir = 'static/data/output'
    try:
        for file in os.listdir(output_dir):
            if file.endswith('.csv'):
                datasets.append({
                    'name': file,
                    'path': os.path.join(output_dir, file)
                })
        return jsonify({'datasets': datasets})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload_dataset', methods=['POST'])
def upload_dataset():
    if 'dataset' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['dataset']
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            save_path = os.path.join('static/data/output', filename)
            file.save(save_path)
            
            # TODO: Maybe don't require all columns to be present
            # Validate file structure
            df = pd.read_csv(save_path)
            required_columns = {'place_id', 'categories', 'lat', 'lon', 'business_status', 
                            'name', 'price_level', 'rating', 'types', 'user_ratings_total', 'vicinity'}
            missing_columns = required_columns - set(df.columns)
            if missing_columns:
                os.remove(save_path)  # Remove invalid file
                return jsonify({'error': f'Missing required columns: {missing_columns}'}), 400
                
            return jsonify({'message': 'Dataset uploaded successfully', 'filename': filename})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'Invalid file format'}), 400

@app.route('/match_categories')
def match_categories():
    return render_template('match_categories.html')

@app.route('/get_categories_to_match', methods=['GET'])
def get_categories_to_match():
    try:
        # Read enrichment categories
        enrichment_categories = []
        enrichment_file = 'static/data/input/enrichment_categories.csv'
        if os.path.exists(enrichment_file):
            with open(enrichment_file, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile, delimiter=';')
                next(reader, None)
                for row in reader:
                    enrichment_categories.append(row[0])

        # Read Google Places data to get business types
        google_data = pd.read_csv('static/data/output/establishments.csv')
        all_types = [item.split(',')[0].strip("[]' ") for sublist in google_data['types'] for item in sublist.split(',')]
        unique_types = list(set(all_types))
        
        # Create a mapping from type text to integer ID
        type_to_id = {}
        id_to_type = {}
        for idx, type_name in enumerate(unique_types):
            type_to_id[type_name] = idx
            id_to_type[idx] = type_name
        
        # Use semantic similarity for matching
        similarity_results = calculate_similarity_sentences(
            sentences_estab=pd.Series(enrichment_categories), 
            sentences_yelp=pd.Series(unique_types),
            top_n=20  # Get top 20 matches for each category
        )
        
        # Format the results for the frontend
        categories_with_matches = []
        for result in similarity_results:
            category_name = result['sentence']
            matches = result['matches']
            
            # Extract top matches with their scores, converting text to integer IDs
            top_matches = [
                {
                    'id': type_to_id.get(match['text'], -1),  # Convert text to ID
                    'score': match['score']
                }
                for match in matches
            ]
            
            # Get the best match (highest score)
            best_match_id = top_matches[0]['id'] if top_matches else -1
            best_score = top_matches[0]['score'] if top_matches else 0
            
            # Add to the results list
            categories_with_matches.append({
                'name': category_name,
                'best_match_id': best_match_id,
                'best_score': best_score,
                'matches': top_matches
            })
            
        # Sort categories by best_score in ascending order
        # This will put categories with worst matches (lowest scores) at the top
        categories_with_matches.sort(key=lambda x: x['best_score'])

        # Prepare the response with optimized data structure
        response_data = {
            'categories': categories_with_matches,
            'types': id_to_type  # Return the mapping from ID to type text
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/save_category_matches', methods=['POST'])
def save_category_matches():
    try:
        data = request.get_json()
        matches = data.get('matches', [])

        # Save matches to a CSV file
        matches_file = 'static/data/input/category_matches.csv'
        with open(matches_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(['category', 'best_score', 'match'])
            for match in matches:
                writer.writerow([match['category'], match['best_score'], match['match']])

        return jsonify({'message': 'Category matches saved successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/load_category_matches', methods=['GET'])
def load_category_matches():
    try:
        matches_file = 'static/data/input/category_matches.csv'
        matches = []
        
        if os.path.exists(matches_file):
            with open(matches_file, newline='', encoding='utf-8') as file:
                reader = csv.reader(file, delimiter=';')
                next(reader, None)  # Skip header
                for row in reader:
                    matches.append({
                        'category': row[0],
                        'best_score': float(row[1]),
                        'match': row[2]
                    })
            
            return jsonify({'matches': matches}), 200
        else:
            return jsonify({'matches': []}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export_enriched_dataset', methods=['POST'])
def export_enriched_dataset():
    try:
        data = request.get_json()
        matches = data.get('matches', [])
        
        # Create a dictionary for quick lookup of category matches
        category_matches = {}
        for match in matches:
            category = match['category']
            match_id = match['match']
            # Only store valid matches (not -1)
            if match_id != "-1":
                category_matches[category] = match_id
        
        # Read the Google Places data
        establishments_df = pd.read_csv('static/data/output/establishments.csv')
        
        # Read the type mapping to get actual type names
        types_map = {}
        google_data = pd.read_csv('static/data/output/establishments.csv')
        all_types = [item.split(',')[0].strip("[]' ") for sublist in google_data['types'] for item in sublist.split(',')]
        unique_types = list(set(all_types))
        for idx, type_name in enumerate(unique_types):
            types_map[str(idx)] = type_name
        
        # Add a new column for matched categories
        establishments_df['matched_categories'] = establishments_df.apply(
            lambda row: get_matched_categories(row, category_matches, types_map),
            axis=1
        )
        
        # Generate a unique filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enriched_dataset_{timestamp}.csv"
        file_path = os.path.join('static/data/output', filename)
        
        # Save the enriched dataset
        establishments_df.to_csv(file_path, index=False)
        
        # Return the download URL
        download_url = url_for('static', filename=f'data/output/{filename}')
        return jsonify({'download_url': download_url, 'message': 'Dataset exported successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_matched_categories(row, category_matches, types_map):
    """
    Match establishment types against the category matches.
    
    Parameters:
    row (Series): A row from the establishments DataFrame
    category_matches (dict): Dictionary mapping category names to type IDs
    types_map (dict): Dictionary mapping type IDs to type names
    
    Returns:
    str: A comma-separated string of matched categories
    """
    # Get the establishment types
    types_str = row['types']
    if pd.isna(types_str) or not types_str:
        return ""
    
    establishment_types = [t.strip("[]' ") for t in types_str.split(',')]
    
    # Find which categories match this establishment's types
    matched_categories = []
    for category, type_id in category_matches.items():
        # Convert the type_id to the actual type name
        type_name = types_map.get(type_id)
        if type_name and type_name in establishment_types:
            matched_categories.append(category)
    
    return ", ".join(matched_categories)

if __name__ == "__main__":
    app.run()
