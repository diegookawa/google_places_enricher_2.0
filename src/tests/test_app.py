import os
import io
import csv
import shutil
import tempfile
import pandas as pd
import numpy as np
import pytest
from flask import url_for

from app import app
import config as app_config
import json

@pytest.fixture
def client(tmp_path, monkeypatch):
    # Setup temp dirs and files for static/data/output and input
    static_dir = tmp_path / "static"
    (static_dir / "data" / "output").mkdir(parents=True, exist_ok=True)
    (static_dir / "data" / "input").mkdir(parents=True, exist_ok=True)
    (static_dir / "uploads").mkdir(parents=True, exist_ok=True)
    # Patch app config paths
    monkeypatch.setattr(app, "static_folder", str(static_dir))
    app.config["UPLOAD_FOLDER"] = str(static_dir / "uploads")
    # Patch os.path.exists to work with tmp_path
    orig_exists = os.path.exists
    def exists_patch(path):
        if path.startswith("static/"):
            return orig_exists(str(tmp_path / path))
        return orig_exists(path)
    monkeypatch.setattr(os.path, "exists", exists_patch)
    # Patch os.listdir to work with tmp_path
    orig_listdir = os.listdir
    def listdir_patch(path):
        if path == "static/data/output":
            return orig_listdir(str(static_dir / "data" / "output"))
        return orig_listdir(path)
    monkeypatch.setattr(os, "listdir", listdir_patch)
    # Patch os.remove to work with tmp_path
    orig_remove = os.remove
    def remove_patch(path):
        if path.startswith("static/"):
            orig_remove(str(tmp_path / path))
        else:
            orig_remove(path)
    monkeypatch.setattr(os, "remove", remove_patch)
    # Patch config.CONFIG_PATH to use a temp config file
    app_config.CONFIG_PATH = str(tmp_path / "config.json")
    # Write minimal config.json for tests
    with open(app_config.CONFIG_PATH, "w") as f:
        json.dump({
            "GOOGLE_MAPS_API": "https://maps.googleapis.com/maps/api",
            "API": "/place",
            "SEARCH_COMPONENT": "/nearbysearch",
            "OUTPUT_TYPE": "/json?",
            "RADIUS": 4444,
            "NORTHEAST_LAT": -25.329914975179992,
            "NORTHEAST_LON": -49.20322728948593,
            "SOUTHWEST_LAT": -25.512242704374355,
            "SOUTHWEST_LON": -49.32304693059921,
            "API_KEY": "dummy_key"
        }, f)
    # Patch pd.read_csv to support relative paths
    orig_read_csv = pd.read_csv
    def read_csv_patch(path, *args, **kwargs):
        if isinstance(path, str) and path.startswith("static/"):
            return orig_read_csv(str(tmp_path / path), *args, **kwargs)
        if isinstance(path, str) and path.startswith("../data/output/"):
            return orig_read_csv(str(tmp_path / "static" / "data" / "output" / os.path.basename(path)), *args, **kwargs)
        return orig_read_csv(path, *args, **kwargs)
    monkeypatch.setattr(pd, "read_csv", read_csv_patch)
    # Patch pd.DataFrame.to_csv to always write to tmp_path
    orig_to_csv = pd.DataFrame.to_csv
    def to_csv_patch(self, path_or_buf, *args, **kwargs):
        if isinstance(path_or_buf, str) and path_or_buf.startswith("static/"):
            return orig_to_csv(self, str(tmp_path / path_or_buf), *args, **kwargs)
        return orig_to_csv(self, path_or_buf, *args, **kwargs)
    monkeypatch.setattr(pd.DataFrame, "to_csv", to_csv_patch)
    # Patch open for writing files in static/data/input/output
    orig_open = open
    def open_patch(path, *args, **kwargs):
        if isinstance(path, str) and path.startswith("static/"):
            return orig_open(str(tmp_path / path), *args, **kwargs)
        return orig_open(path, *args, **kwargs)
    monkeypatch.setattr("builtins.open", open_patch)
    # Patch url_for to not fail outside request context
    monkeypatch.setattr("src.app.url_for", lambda endpoint, **values: f"/static/data/output/{values['filename']}")
    # Provide test client
    with app.test_client() as client:
        yield client

def test_view_data_success(client, tmp_path):
    # Prepare a well-formed establishments.csv
    output_dir = tmp_path / "static" / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([{
        "place_id": "abc123",
        "categories": "Cafe",
        "lat": 1.23,
        "lon": 4.56,
        "business_status": "OPERATIONAL",
        "name": "Test Cafe",
        "price_level": "2",
        "rating": 4.5,
        "types": "cafe,food,point_of_interest,establishment",
        "user_ratings_total": 10,
        "vicinity": "123 Main St"
    }])
    df.to_csv(output_dir / "establishments.csv", index=False)
    resp = client.get("/view_data")
    assert resp.status_code == 200
    assert b"Test Cafe" in resp.data
    assert b"OPERATIONAL" in resp.data
    assert b"Cafe" in resp.data

def test_update_categories_and_process_data_success(client, tmp_path, mocker):
    # Prepare categories_request.csv path
    input_dir = tmp_path / "static" / "data" / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    # Prepare lat_lon_calculated.csv for request_google_places
    output_dir = tmp_path / "static" / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    latlon_path = output_dir / "lat_lon_calculated.csv"
    pd.DataFrame({"lat": [1.0], "lon": [2.0]}).to_csv(latlon_path, index=False)
    # Mock request_google_places to return success
    mocker.patch("app.request_google_places", return_value="Execution went successfully.")
    resp = client.post("/update_categories_and_process_data", json={"categories": [["cafe"], ["restaurant"]]})
    assert resp.status_code == 200
    assert resp.json["message"] == "CSV updated successfully"
    # Check file written
    cat_path = input_dir / "categories_request.csv"
    assert cat_path.exists()
    with open(cat_path, newline="") as f:
        reader = csv.reader(f, delimiter=";")
        header = next(reader)
        assert header == ["category"]
        rows = list(reader)
        assert rows == [["cafe"], ["restaurant"]]

def test_upload_dataset_success(client, tmp_path):
    output_dir = tmp_path / "static" / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    # Prepare a valid CSV in memory
    csv_content = io.StringIO()
    writer = csv.writer(csv_content)
    writer.writerow(["place_id", "categories", "lat", "lon", "business_status", "name", "price_level", "rating", "types", "user_ratings_total", "vicinity"])
    writer.writerow(["id1", "Cafe", "1.0", "2.0", "OPERATIONAL", "CafeName", "2", "4.5", "cafe,food", "10", "Addr"])
    csv_content.seek(0)
    data = {
        "dataset": (io.BytesIO(csv_content.read().encode()), "dataset.csv")
    }
    resp = client.post("/upload_dataset", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    assert resp.json["message"] == "Dataset uploaded successfully"
    assert resp.json["filename"] == "dataset.csv"
    # File should exist
    assert (output_dir / "dataset.csv").exists()

def test_view_data_file_not_found(client, tmp_path):
    # No establishments.csv present
    resp = client.get("/view_data")
    assert resp.status_code == 200
    assert b"Error: File static/data/output/establishments.csv not found." in resp.data

def test_update_categories_and_process_data_no_categories(client):
    resp = client.post("/update_categories_and_process_data", json={})
    assert resp.status_code == 400
    assert resp.json["error"] == "No categories provided"

def test_upload_dataset_missing_columns(client, tmp_path):
    output_dir = tmp_path / "static" / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    # CSV missing required columns
    csv_content = io.StringIO()
    writer = csv.writer(csv_content)
    writer.writerow(["place_id", "categories", "lat", "lon"])  # missing many columns
    writer.writerow(["id1", "Cafe", "1.0", "2.0"])
    csv_content.seek(0)
    data = {
        "dataset": (io.BytesIO(csv_content.read().encode()), "bad.csv")
    }
    resp = client.post("/upload_dataset", data=data, content_type="multipart/form-data")
    assert resp.status_code == 400
    assert "Missing required columns" in resp.json["error"]
    # File should be removed
    assert not (output_dir / "bad.csv").exists()

def test_export_enriched_dataset_success(client, tmp_path):
    # Prepare dataset and enrichment data
    output_dir = tmp_path / "static" / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([{
        "place_id": "abc123",
        "categories": "Cafe",
        "lat": 1.23,
        "lon": 4.56,
        "business_status": "OPERATIONAL",
        "name": "Test Cafe",
        "price_level": "2",
        "rating": 4.5,
        "types": "cafe,food,point_of_interest,establishment",
        "user_ratings_total": 10,
        "vicinity": "123 Main St",
        "phrase_establishment": "Cafe food"
    }])
    df.to_csv(output_dir / "establishments.csv", index=False)
    establishment_phrases = [{
        "category": "Cafe",
        "phrase": "Cafe food",
        "best_score": 0.99,
        "selected_score": 0.99,
        "selected_option": 0,
        "options": [{"category_index": 0, "score": 0.99}]
    }]
    yelp_categories = [["Cafe", "Cafe food"]]
    data = {
        "establishment_phrases": establishment_phrases,
        "yelp_categories": yelp_categories,
        "dataset_path": "establishments.csv"
    }
    resp = client.post("/export_enriched_dataset", json=data)
    assert resp.status_code == 200
    assert "download_url" in resp.json
    # File should exist
    out_file = resp.json["download_url"].split("/")[-1]
    assert any(f.name == out_file for f in (output_dir).iterdir())

def test_get_categories_to_match_enrichment_file_missing(client, tmp_path):
    # No enrichment_categories.csv present
    resp = client.get("/get_categories_to_match")
    assert resp.status_code == 404
    assert resp.json["error"] == "Enrichment categories file not found"

def test_categories_upload_and_retrieve_success(client, tmp_path):
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    # Prepare a valid categories CSV
    csv_content = io.StringIO()
    writer = csv.writer(csv_content, delimiter=";")
    writer.writerow(["category"])
    writer.writerow(["Cafe"])
    writer.writerow(["Restaurant"])
    csv_content.seek(0)
    data = {
        "csv-file": (io.BytesIO(csv_content.read().encode()), "categories.csv")
    }
    resp = client.post("/categories", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    assert resp.json["categories"] == ["Cafe", "Restaurant"]

def test_enrichment_categories_invalid_structure(client, tmp_path):
    # Send a list of strings instead of dicts
    data = {"categories": ["Cafe", "Restaurant"]}
    resp = client.post("/enrichment_categories", json=data)
    assert resp.status_code == 400
    assert "Invalid data structure" in resp.json["error"]

def test_get_available_datasets_success(client, tmp_path):
    output_dir = tmp_path / "static" / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    # Create two CSVs
    (output_dir / "file1.csv").write_text("a,b\n1,2")
    (output_dir / "file2.csv").write_text("a,b\n3,4")
    resp = client.get("/get_available_datasets")
    assert resp.status_code == 200
    datasets = resp.json["datasets"]
    names = {d["name"] for d in datasets}
    assert "file1.csv" in names
    assert "file2.csv" in names

def test_get_categories_file_missing(client, tmp_path):
    # categories_request.csv does not exist
    resp = client.get("/get_categories")
    assert resp.status_code == 500
    assert resp.json["error"] == "File not found"

def test_update_coordinates_csv_success(client, tmp_path):
    # Setup temp dirs for static/data/output
    output_dir = tmp_path / "static" / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    coordinates = [[1.23, 4.56], [7.89, 0.12]]
    resp = client.post("/update_coordinates_csv", json={"coordinates": coordinates})
    assert resp.status_code == 200 or resp.status_code == 204
    
    # Check file written and contents
    csv_file_path = output_dir / "lat_lon_calculated.csv"
    assert csv_file_path.exists()
    with open(csv_file_path, newline="") as f:
        reader = csv.reader(f, delimiter=";")
        header = next(reader)
        assert header == ["lat", "lon"]
        rows = list(reader)
        assert rows == [["1.23", "4.56"], ["7.89", "0.12"]]

def test_get_coordinates_success(client, tmp_path):
    # Prepare lat_lon_calculated.csv
    output_dir = tmp_path / "static" / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([{"lat": 1.23, "lon": 4.56}, {"lat": 7.89, "lon": 0.12}])
    df.to_csv(output_dir / "lat_lon_calculated.csv", index=False)
    resp = client.get("/get_coordinates")
    assert resp.status_code == 200
    data = pd.read_json(io.StringIO(resp.data.decode()), orient="records")
    assert list(data.columns) == ["lat", "lon"]
    assert data.shape[0] == 2
    assert data.iloc[0]["lat"] == pytest.approx(1.23)
    assert data.iloc[0]["lon"] == pytest.approx(4.56)

def test_upload_csv_success(client, tmp_path):
    # Prepare a valid CSV in memory
    csv_content = io.StringIO()
    writer = csv.writer(csv_content)
    writer.writerow(["category"])
    writer.writerow(["Cafe"])
    writer.writerow(["Restaurant"])
    csv_content.seek(0)
    data = {
        "csv-file": (io.BytesIO(csv_content.read().encode()), "categories.csv")
    }
    resp = client.post("/upload_csv", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    assert resp.json["message"] == "Upload successful"
    assert resp.json["categories"] == ["Cafe", "Restaurant"]
    # File should exist
    cat_path = tmp_path / "static" / "data" / "input" / "categories_request.csv"
    assert cat_path.exists()

def test_enrichment_categories_success(client, tmp_path):
    # Prepare enrichment categories payload
    categories = [
        {"category": "Cafe", "matching_phrase": "Cafe food"},
        {"category": "Restaurant", "matching_phrase": "Restaurant meal"}
    ]
    resp = client.post("/enrichment_categories", json={"categories": categories})
    assert resp.status_code == 200
    assert resp.json["message"] == "Categories updated successfully."
    # File should exist and have correct content
    csv_file_path = tmp_path / "static" / "data" / "input" / "enrichment_categories.csv"
    assert csv_file_path.exists()
    with open(csv_file_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        header = next(reader)
        assert header == ["category", "matching_phrase"]
        rows = list(reader)
        assert rows == [["Cafe", "Cafe food"], ["Restaurant", "Restaurant meal"]]


def test_update_coordinates_csv_missing_coordinates(client, tmp_path):
    # Send POST without 'coordinates' field
    resp = client.post("/update_coordinates_csv", json={})
    assert resp.status_code == 500
    assert "error" in resp.json
    assert "coordinates" in resp.json["error"] or "object is not iterable" in resp.json["error"]

def test_get_enrichment_categories_malformed_csv(client, tmp_path):
    # Write a malformed CSV (missing delimiter)
    input_dir = tmp_path / "static" / "data" / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    file_path = input_dir / "enrichment_categories.csv"
    file_path.write_text("category,matching_phrase\nCafe Cafe food\nRestaurant Restaurant meal")
    resp = client.get("/get_enrichment_categories")
    assert resp.status_code == 500
    assert "error" in resp.json

def test_components_result_success(client):
    resp = client.get("/components_result")
    assert resp.status_code == 200

def test_coordinates_result_success(client):
    resp = client.get("/coordinates_result")
    assert resp.status_code == 200

def test_categories_post_no_file(client):
    resp = client.post("/categories", data={}, content_type="multipart/form-data")
    assert resp.status_code == 400

@pytest.mark.parametrize(
    "data,expected_error",
    [
        ({"csv-file": (io.BytesIO(b"bad"), "bad.txt")}, None),  # invalid file content
        ({"csv-file": (io.BytesIO(b"not,a,csv"), "categories.txt")}, "Invalid file format"),  # invalid extension
    ]
)
def test_categories_invalid_file_cases(client, data, expected_error):
    resp = client.post("/categories", data=data, content_type="multipart/form-data")
    assert resp.status_code == 400
    if expected_error:
        assert resp.json["error"] == expected_error

def test_enrich_data_success(client):
    resp = client.get("/enrich_data")
    assert resp.status_code == 200

def test_get_enrichment_categories_missing_file(client, monkeypatch):
    # Simulate missing file
    monkeypatch.setattr(os.path, "exists", lambda p: False)
    resp = client.get("/get_enrichment_categories")
    assert resp.status_code == 200
    # Should return empty or default structure
    assert resp.json == {} or resp.json == {"categories": []}

def test_get_enrichment_categories_file_error(client, monkeypatch):
    # Simulate file read error
    monkeypatch.setattr(os.path, "exists", lambda p: True)
    import builtins
    orig_open = builtins.open
    def raise_ioerror(*a, **k): raise IOError("fail")
    monkeypatch.setattr("builtins.open", raise_ioerror)
    resp = client.get("/get_enrichment_categories")
    assert resp.status_code == 500

def test_match_categories_success(client):
    resp = client.get("/match_categories")
    assert resp.status_code == 200

def test_get_categories_to_match_missing_enrichment_file(client, monkeypatch):
    # Simulate missing enrichment file
    monkeypatch.setattr(os.path, "exists", lambda p: False)
    resp = client.get("/get_categories_to_match")
    assert resp.status_code == 404

def test_get_categories_to_match_invalid_data(client, monkeypatch):
    # Simulate invalid data in enrichment file
    monkeypatch.setattr(os.path, "exists", lambda p: True)
    import pandas as pd
    monkeypatch.setattr(pd, "read_csv", lambda p, **k: pd.DataFrame({"category": [1]}))
    import app
    monkeypatch.setattr(app, "create_estab_phrase", lambda df: pd.DataFrame({"phrase_establishment": [123]}))
    resp = client.get("/get_categories_to_match")
    assert resp.status_code in (400, 500)

def test_export_enriched_dataset_missing_file(client, monkeypatch):
    # Simulate missing establishments file
    monkeypatch.setattr(os.path, "exists", lambda p: False)
    resp = client.post("/export_enriched_dataset", json={})
    assert resp.status_code == 404

def test_export_enriched_dataset_file_error(client, monkeypatch):
    # Simulate file read error
    monkeypatch.setattr(os.path, "exists", lambda p: True)
    import pandas as pd
    monkeypatch.setattr(pd, "read_csv", lambda p, **k: (_ for _ in ()).throw(IOError("fail")))
    resp = client.post("/export_enriched_dataset", json={})
    assert resp.status_code == 500

def test_update_categories_and_process_data_external_failure(client, mocker):
    # Simulate external dependency failure
    mocker.patch("app.request_google_places", side_effect=Exception("fail"))
    resp = client.post("/update_categories_and_process_data", json={"categories": ["cat"]})
    assert resp.status_code == 500

def test_update_categories_and_process_data_file_error(client, mocker):
    # Simulate file write error
    import builtins
    mocker.patch("app.request_google_places", return_value="Successfully processed")
    orig_open = builtins.open
    def raise_ioerror(*a, **k): raise IOError("fail")
    mocker.patch("builtins.open", raise_ioerror)
    resp = client.post("/update_categories_and_process_data", json={"categories": ["cat"]})
    assert resp.status_code == 500

def test_update_coordinates_csv_file_error(client, mocker):
    # Simulate file write error
    import builtins
    def raise_ioerror(*a, **k): raise IOError("fail")
    mocker.patch("builtins.open", raise_ioerror)
    resp = client.post("/update_coordinates_csv", json={"coordinates": [[1, 2]]})
    assert resp.status_code == 500

@pytest.mark.parametrize(
    "data,patch_file_error,expected_status,expected_error",
    [
        ({"dataset": (io.BytesIO(b"bad"), "bad.txt")}, False, 400, None),  # invalid file content
        ({"dataset": (io.BytesIO(b"foo"), "test.csv")}, True, 500, None),  # file write error
    ]
)
def test_upload_dataset_invalid_file_cases(client, mocker, data, patch_file_error, expected_status, expected_error):
    if patch_file_error:
        import builtins
        def raise_ioerror(*a, **k): raise IOError("fail")
        mocker.patch("builtins.open", raise_ioerror)
    resp = client.post("/upload_dataset", data=data, content_type="multipart/form-data")
    assert resp.status_code == expected_status
    if expected_error:
        assert resp.json["error"] == expected_error

def test_upload_csv_no_file(client):
    resp = client.post("/upload_csv", data={}, content_type="multipart/form-data")
    assert resp.status_code == 400
