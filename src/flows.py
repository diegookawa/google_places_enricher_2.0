import os
import time
import shapely.geometry
import pyproj
import requests
from dotenv import load_dotenv
from config import RADIUS, NORTHEAST_LAT, NORTHEAST_LON, SOUTHWEST_LAT, SOUTHWEST_LON
from utils import read_file, initialize_variables_request, create_url_request, export_data_request, create_message_request

def update_config_file(radius, southwest_lat, southwest_lon, northeast_lat, northeast_lon):
    """
    Updates the config.py file with the new configuration values.

    Parameters
    ----------
    radius : float
        The new radius value.
    southwest_lat : float
        The new southwest latitude.
    southwest_lon : float
        The new southwest longitude.
    northeast_lat : float
        The new northeast latitude.
    northeast_lon : float
        The new northeast longitude.
    """
    config_path = "./config.py"

    # Read the content of the config.py file
    with open(config_path, "r") as f:
        config_content = f.readlines()

    # Update the lines with the new values
    for i, line in enumerate(config_content):
        if line.startswith("RADIUS"):
            config_content[i] = f"RADIUS = {radius}\n"
        elif line.startswith("SOUTHWEST_LAT"):
            config_content[i] = f"SOUTHWEST_LAT = {southwest_lat}\n"
        elif line.startswith("SOUTHWEST_LON"):
            config_content[i] = f"SOUTHWEST_LON = {southwest_lon}\n"
        elif line.startswith("NORTHEAST_LAT"):
            config_content[i] = f"NORTHEAST_LAT = {northeast_lat}\n"
        elif line.startswith("NORTHEAST_LON"):
            config_content[i] = f"NORTHEAST_LON = {northeast_lon}\n"

    # Write the updated content back to the file
    with open(config_path, "w") as f:
        f.writelines(config_content)

def calculate_coordinates(radius, southwest_lat, southwest_lon, northeast_lat, northeast_lon):
    """
    Generates a CSV file with the geographic coordinates of a rectangular area
    and according to a predetermined step in meters and updates the values in the config file.

    Parameters
    ----------
    No Parameters.

    Raises
    ------
    No raises.

    Returns
    -------
    str
        Message indicating the end of execution.
    """

    RADIUS = radius
    SOUTHWEST_LAT = southwest_lat
    NORTHEAST_LAT = northeast_lat
    NORTHEAST_LON = northeast_lon
    SOUTHWEST_LON = southwest_lon

    # Update the values in the config file
    update_config_file(RADIUS, SOUTHWEST_LAT, SOUTHWEST_LON, NORTHEAST_LAT, NORTHEAST_LON)

    to_proxy_transformer = pyproj.Transformer.from_crs("epsg:4326", "epsg:3857")
    to_original_transformer = pyproj.Transformer.from_crs("epsg:3857", "epsg:4326")

    sw = shapely.geometry.Point(SOUTHWEST_LAT, SOUTHWEST_LON)
    ne = shapely.geometry.Point(NORTHEAST_LAT, NORTHEAST_LON)

    stepsize = RADIUS + (RADIUS / 2)

    transformed_sw = to_proxy_transformer.transform(sw.x, sw.y)
    transformed_ne = to_proxy_transformer.transform(ne.x, ne.y)

    gridpoints = []
    x = transformed_sw[0] + (3 / 4 * RADIUS)
    while x < transformed_ne[0]:
        y = transformed_sw[1] + (3 / 4 * RADIUS)
        while y < transformed_ne[1]:
            p = shapely.geometry.Point(to_original_transformer.transform(x, y))
            gridpoints.append(p)
            y += stepsize
        x += stepsize

    with open("./static/data/output/lat_lon_calculated.csv", "w") as of:
        of.write("lat;lon\n")
        for p in gridpoints:
            of.write("{:f};{:f}\n".format(p.x, p.y))

    return "Execution performed successfully."

def make_request(url, params=None):
    """
    Makes an HTTP GET request and returns the JSON response.

    Parameters
    ----------
    url : str
        The URL to make the request.
    params : dict
        Optional parameters to include in the request.

    Returns
    -------
    dict
        The JSON response.
    """
    try:
        response = requests.get(url, params=params)
        print("Request URL:", response.url)  # Log the request URL
        response_data = response.json()
        print("Response:", response_data)  # Log the API response
        return response_data
    except Exception as e:
        print("Error during request:", str(e))  # Log any errors
        return {"status": "ERROR", "error_message": str(e)}

def request_google_places():
    """
    Performs requests to the Google Places API, according to the geographic coordinates
    defined in the input file and a predetermined radius.
    It enriches the data according to the categories also defined in the input file
    and handles the return of the API, making the data available in a CSV file.

    Returns
    -------
    str
        Message indicating if the flow was executed successfully or
        otherwise the error that interrupted the execution.
    """

    df_latlon = read_file("Coordinates", "./static/data/output/lat_lon_calculated.csv")
    if type(df_latlon) == str:
        return df_latlon

    df_categories = read_file("Categories", "./static/data/input/categories_request.csv")
    if type(df_categories) == str:
        return df_categories
    if len(df_categories) == 0:
        df_categories.loc[0] = [""]

    establishments_features_data, establishments_features_labels = (
        initialize_variables_request()
    )

    for lat_lon in df_latlon.iterrows():
        lat = lat_lon[1]["lat"]
        lon = lat_lon[1]["lon"]

        for cat in df_categories["category"]:
            establishments = []

            url = create_url_request(lat, lon, cat)
            results = make_request(url)
            if not results["status"] == "OK":
                export_data_request(
                    establishments_features_labels, establishments_features_data
                )
                return create_message_request(results)

            establishments.extend(results["results"])

            pages = 1
            params = {}
            time.sleep(2)
            while "next_page_token" in results:
                pages += 1
                params["pagetoken"] = results["next_page_token"]
                results = make_request(url, params)
                if not results["status"] == "OK":
                    export_data_request(
                        establishments_features_labels, establishments_features_data
                    )
                    return create_message_request(results)
                establishments.extend(results["results"])
                time.sleep(2)

            for establishment in establishments:
                for feature_index in range(len(establishments_features_labels) - 1):
                    try:
                        establishments_features_data[feature_index].append(
                            establishment[establishments_features_labels[feature_index]]
                        )
                    except KeyError:
                        establishments_features_data[feature_index].append(None)

                establishments_features_data[ 
                    len(establishments_features_data) - 1
                ].append(cat)

    export_data_request(establishments_features_labels, establishments_features_data)
    return "Execution performed successfully."
