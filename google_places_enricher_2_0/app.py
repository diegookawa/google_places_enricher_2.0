from flask import Flask, render_template, request, redirect, url_for, jsonify
from google_places_enricher_2_0.flows import calculate_coordinates, request_google_places
from google_places_enricher_2_0.utils import create_estab_phrase, calculate_similarity_sentences
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np
import csv
import os
import argparse
import datetime
from google_places_enricher_2_0.config import get_config_value, set_config_value

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#load_dotenv()

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
            return f"Error: File {csv_path} not found."
        except Exception as e:
            return f"Error reading the CSV file: {str(e)}"

        required_columns = {'place_id', 'categories', 'lat', 'lon', 'business_status', 
                            'name', 'price_level', 'rating', 'types', 'user_ratings_total', 'vicinity'}
        missing_columns = required_columns - set(data.columns)
        if missing_columns:
            return f"Error: Missing columns in CSV: {missing_columns}"

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
        return f"Unexpected error: {str(e)}"

@app.route('/update_coordinates_csv', methods=['POST'])
def update_coordinates_csv():
    data = request.get_json()
    coordinates = data.get('coordinates')

    csv_file_path = 'static/data/output/lat_lon_calculated.csv'

    try:
        os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)
        with open(csv_file_path, mode='w', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(['lat', 'lon'])
            for coord in coordinates:
                writer.writerow(coord)
        return jsonify({"message": "Coordinates updated successfully"}), 200
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

@app.route('/update_categories_and_process_data', methods=['POST'])
def update_categories_and_process_data():
    data = request.get_json()
    categories = data.get('categories')

    if not categories:
        return jsonify({"error": "No categories provided"}), 400 

    csv_file_path = 'static/data/input/categories_request.csv'

    try:
        print(f"Received categories: {categories}")

        with open(csv_file_path, mode='w', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(['category'])
            for cat in categories:
                writer.writerow(cat) 
        
        result = request_google_places()
        print(f"Result from request_google_places: {result}")

        if not result:
            return jsonify({"error": "Google Places API returned no response"}), 500
        if "successfully" not in result.lower():
            return jsonify({"error": result}), 500

        return jsonify({"message": "CSV updated successfully"}), 200 

    except Exception as e:
        print(f"Exception occurred: {str(e)}")
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
            set_config_value("API_KEY", api_key)
            return redirect(url_for("coordinates_definition"))
    return render_template("main_page.html")

@app.route("/coordinates_definition")
def coordinates_definition():
    api_key = get_config_value("API_KEY")
    return render_template("coordinates_definition.html", api_key=api_key)

@app.route("/components_result")
def components_result():
    return render_template("components_result.html")

@app.route("/coordinates_result")
def coordinates_results():
    file_name = request.args.get("file", "../data/output/lat_lon_calculated.csv")
    return render_template("coordinates_result.html", file_name=file_name)

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    file = request.files.get('csv-file')
    if not file:
        return jsonify({"error": "No file uploaded"}), 400
    
    df = pd.read_csv(file)
    categories = df.iloc[:, 0].dropna().tolist()

    os.makedirs('static/data/input', exist_ok=True)
    df.to_csv('static/data/input/categories_request.csv', index=False)

    return jsonify({"message": "Upload successful", "categories": categories})

@app.route('/categories', methods=['GET', 'POST'])
def categories():
    if request.method == 'POST':
        if 'csv-file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        file = request.files['csv-file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
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
            try:
                reader = csv.DictReader(csvfile, delimiter=';')
                expected_fields = {'category', 'matching_phrase'}
                if not expected_fields.issubset(set(reader.fieldnames or [])):
                    return jsonify({'error': 'Malformed CSV: missing required columns'}), 500
                for row in reader:
                    cat = row.get('category', '')
                    phrase = row.get('matching_phrase', '')
                    if not phrase:
                        phrase = cat
                    categories.append({'category': cat, 'matching_phrase': phrase})
            except csv.Error as e:
                return jsonify({'error': f'CSV parsing error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'categories': categories})

@app.route('/enrichment_categories', methods=['POST'])
def enrichment_categories():
    data = request.get_json()
    categories = data.get('categories')

    csv_file_path = 'static/data/input/enrichment_categories.csv'

    try:
        os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)
        with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(['category', 'matching_phrase'])
            for cat in categories:
                if not isinstance(cat, dict):
                    return jsonify({'error': 'Invalid data structure. Each category must be a dictionary.'}), 400
                category = cat.get('category', '')
                phrase = cat.get('matching_phrase', '') or category
                writer.writerow([category, phrase])

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
                # Return only the filename instead of full path
                datasets.append({
                    'name': file,
                    'path': file  # Just the filename
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
            save_dir = 'static/data/output'
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, filename)
            file.save(save_path)
            
            # TODO: Maybe don't require all columns to be present
            # Validate file structure
            df = pd.read_csv(save_path)
            required_columns = {'place_id', 'categories', 'lat', 'lon', 'business_status', 
                            'name', 'price_level', 'rating', 'types', 'user_ratings_total', 'vicinity'}
            missing_columns = required_columns - set(df.columns)
            if missing_columns:
                os.remove(save_path)  # Remove invalid file
                expected_structure = ', '.join(required_columns)
                return jsonify({'error': f'Missing required columns: {missing_columns}. Expected structure: {expected_structure}'}), 400
                
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
        enrichment_file = 'static/data/input/enrichment_categories.csv'
        if not os.path.exists(enrichment_file):
            return jsonify({'error': 'Enrichment categories file not found'}), 404

        df_enrichment = pd.read_csv(enrichment_file, delimiter=';')
        if 'matching_phrase' not in df_enrichment.columns:
            df_enrichment['matching_phrase'] = df_enrichment['category']

        dataset_path = request.args.get('dataset_path', 'establishments.csv')
        dataset_full_path = os.path.join('static/data/output', dataset_path)
        if not os.path.exists(dataset_full_path):
            return jsonify({'error': f'Dataset {dataset_path} not found'}), 404

        google_data = pd.read_csv(dataset_full_path)
        df_estab_phrases = create_estab_phrase(google_data)

        # Filter unique, multi-word establishment phrases
        df_estab = (
            df_estab_phrases
            .drop_duplicates(subset="phrase_establishment")[['phrase_establishment', 'category']]
            .assign(words_phrase_estab=lambda df: df['phrase_establishment'].apply(lambda phrase: len(str(phrase).split(' '))))
        )
        df_estab = df_estab[df_estab['words_phrase_estab'] > 1].reset_index(drop=True)

        # Use pandas to ensure all relevant columns are strings
        estab_phrases = df_estab['phrase_establishment'].astype(str).tolist()
        estab_categories = df_estab['category'].astype(str).tolist()
        yelp_phrases = df_enrichment['matching_phrase'].astype(str).tolist()
        yelp_categories_col = df_enrichment['category'].astype(str).tolist()

        # Build yelp_categories as array of [category, phrase]
        yelp_categories = [[cat, phr] for cat, phr in zip(yelp_categories_col, yelp_phrases)]

        # Calculate similarities
        sim_df = calculate_similarity_sentences(estab_phrases, yelp_phrases)

        # Build establishment_phrases as per spec
        establishment_phrases = []
        for estab_idx, (category, phrase) in enumerate(zip(estab_categories, estab_phrases)):
            matches = sim_df[sim_df.estab_idx == estab_idx]
            options = []
            for row in matches.itertuples(index=False):
                score = float(row.score)
                if not pd.notnull(score) or not np.isfinite(score):
                    score = -1.0
                options.append({"category_index": int(row.yelp_idx), "score": score})
            options_sorted = sorted(options, key=lambda x: x['score'], reverse=True)
            best_score = options_sorted[0]['score'] if options_sorted else -1.0
            selected_option = 0 if options_sorted else None
            selected_score = options_sorted[0]['score'] if options_sorted else -1.0
            establishment_phrases.append({
                "category": category,
                "phrase": phrase,
                "best_score": best_score,
                "selected_score": selected_score,
                "selected_option": selected_option,
                "options": options_sorted
            })

        response_data = {
            "establishment_phrases": establishment_phrases,
            "yelp_categories": yelp_categories
        }
        return jsonify(response_data)
    except Exception as e:
        print(f"Error in get_categories_to_match: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/export_enriched_dataset', methods=['POST'])
def export_enriched_dataset():
    try:
        data = request.get_json()
        establishment_phrases = data.get('establishment_phrases', [])
        yelp_categories = data.get('yelp_categories', [])
        dataset_path = data.get('dataset_path', 'establishments.csv')
        dataset_full_path = os.path.join('static/data/output', dataset_path)
        if not os.path.exists(dataset_full_path):
            return jsonify({'error': f'Dataset {dataset_path} not found'}), 404
        df = pd.read_csv(dataset_full_path)
        # Try to find the phrase column
        phrase_col = None
        for col in ['phrase', 'phrase_establishment', 'matching_phrase']:
            if col in df.columns:
                phrase_col = col
                break
        # If not found, generate it using create_estab_phrase
        if not phrase_col:
            df_phrases = create_estab_phrase(df)
            df = df.merge(df_phrases, on='place_id', how='left')
            phrase_col = 'phrase_establishment'
        # Build phrase -> establishment_phrase object lookup
        phrase_to_obj = {ep['phrase']: ep for ep in establishment_phrases}
        enriched_rows = []
        for idx, row in df.iterrows():
            phrase_val = row[phrase_col]
            establishment_phrases = phrase_to_obj.get(str(phrase_val)) if pd.notnull(phrase_val) else None
            matched_phrase = establishment_phrases['phrase'] if establishment_phrases else None
            selected_option = establishment_phrases['selected_option'] if establishment_phrases and 'selected_option' in establishment_phrases and establishment_phrases['selected_option'] is not None and establishment_phrases['selected_option'] >= 0 else None
            selected_score = None
            best_score = establishment_phrases['best_score'] if establishment_phrases else None
            category_index = None
            matched_category = None
            if establishment_phrases and selected_option is not None and isinstance(establishment_phrases.get('options'), list) and selected_option < len(establishment_phrases['options']):
                selected_opt = establishment_phrases['options'][selected_option]
                selected_score = selected_opt['score']
                category_index = selected_opt['category_index']
                if category_index is not None and category_index < len(yelp_categories):
                    matched_category = yelp_categories[category_index][0]
            enriched_row = row.to_dict()
            enriched_row['matched_phrase'] = matched_phrase
            enriched_row['category_index'] = category_index
            enriched_row['matched_category'] = matched_category
            enriched_row['selected_score'] = selected_score
            enriched_row['best_score'] = best_score
            enriched_rows.append(enriched_row)
        df_enriched = pd.DataFrame(enriched_rows)
        now = datetime.datetime.now()
        out_name = f"enriched_{now.strftime('%Y%m%d_%H%M%S')}.csv"
        out_path = os.path.join('static/data/output', out_name)
        df_enriched.to_csv(out_path, index=False)
        download_url = url_for('static', filename=f'data/output/{out_name}')
        return jsonify({'download_url': download_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the Flask application')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the application on')
    args = parser.parse_args()
    
    app.run(host='127.0.0.1', port=args.port)
