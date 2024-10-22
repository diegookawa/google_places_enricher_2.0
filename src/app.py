from flask import Flask, render_template, request, redirect, url_for, jsonify
from dotenv import load_dotenv, set_key
from flows import calculate_coordinates
import pandas as pd
import os

app = Flask(__name__)

load_dotenv()


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


if __name__ == "__main__":
    app.run()