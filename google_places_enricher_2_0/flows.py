import shapely.geometry
import pyproj
import requests
from google_places_enricher_2_0.config import set_config_value
from google_places_enricher_2_0.utils import (
    read_file,
    initialize_variables_request,
    create_places_post_request,
    export_data_request, 
    create_message_request
)


def calculate_coordinates(radius, southwest_lat, southwest_lon, northeast_lat, northeast_lon):
    """
    Generates a CSV file with geographic coordinates of a rectangular area
    according to a predefined step in meters, and updates the config values in config.json.
    """

    set_config_value("RADIUS", radius)
    set_config_value("SOUTHWEST_LAT", southwest_lat)
    set_config_value("SOUTHWEST_LON", southwest_lon)
    set_config_value("NORTHEAST_LAT", northeast_lat)
    set_config_value("NORTHEAST_LON", northeast_lon)

    RADIUS = radius
    SOUTHWEST_LAT = southwest_lat
    NORTHEAST_LAT = northeast_lat
    NORTHEAST_LON = northeast_lon
    SOUTHWEST_LON = southwest_lon

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

    return "Execution went successfully."

def make_request(url, params=None, method="GET", headers=None):
    """
    Makes an HTTP request according to the specified method and returns the JSON response.

    Parameters
    ----------
    url : str
        The URL for the request.
    params : dict
        Optional parameters to include in the request.
    method : str
        The HTTP method to use (GET or POST).

    Returns
    -------
    dict
        The JSON response.
    """
    try:
        if method.upper() == "POST":
            response = requests.post(url, json=params, headers=headers)
        else:
            response = requests.get(url, params=params, headers=headers)
        print("Request URL:", response.url)
        response_data = response.json()
        print("Response:", response_data)
        return response_data
    except Exception as e:
        print("Error during request:", str(e))
        return {"status": "ERROR", "error_message": str(e)}

def request_google_places():
    """
    Makes requests to the new Google Places Nearby Search API (POST),
    enriching data based on provided coordinates and categories.

    Returns
    -------
    str
        Message indicating if the flow was successfully executed or
        any error that interrupted execution.
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

            url, headers, payload = create_places_post_request(lat, lon, cat)

            # Use POST method for the request
            response = make_request(url, params=payload, method="POST", headers=headers)

            if response.get("status") == "ERROR":
                return f"Error: {response.get('error_message')}"

            if "places" not in response:
                return f"Error: {response}"

            establishments.extend(response["places"])

            # TODO: Handle pagination if required by the API
            for establishment in establishments:
                for feature_index, label in enumerate(establishments_features_labels):
                    try:
                        if label == "business_status":
                            value = establishment.get("businessStatus")
                        elif label == "geometry":
                            location = establishment.get("location", {})
                            value = f"{location.get('latitude')}, {location.get('longitude')}"
                        elif label == "name":
                            value = establishment.get("displayName", {}).get("text")
                        elif label == "place_id":
                            value = establishment.get("id")
                        elif label == "price_level":
                            value = establishment.get("priceLevel")
                        elif label == "rating":
                            value = establishment.get("rating")
                        elif label == "types":
                            value = ", ".join(establishment.get("types", []))
                        elif label == "user_ratings_total":
                            value = establishment.get("userRatingCount")
                        elif label == "vicinity":
                            value = establishment.get("formattedAddress")
                        elif label == "category":
                            value = cat  # Custom category
                        else:
                            value = None
                        establishments_features_data[feature_index].append(value)
                    except Exception as e:
                        establishments_features_data[feature_index].append(None)

    print(establishments_features_data)
    print(establishments_features_labels)
    export_data_request(establishments_features_labels, establishments_features_data)
    return "Execution went successfully."
