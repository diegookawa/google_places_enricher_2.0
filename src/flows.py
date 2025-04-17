import os
import time
import shapely.geometry
import pyproj
import requests
from dotenv import load_dotenv
from config import RADIUS, NORTHEAST_LAT, NORTHEAST_LON, SOUTHWEST_LAT, SOUTHWEST_LON
from utils import read_file, initialize_variables_request, create_places_post_request, export_data_request, create_message_request

def update_config_file(radius, southwest_lat, southwest_lon, northeast_lat, northeast_lon):
    """
    Atualiza o arquivo config.py com os novos valores de configuração.

    Parâmetros
    ----------
    radius : float
        O novo valor de raio.
    southwest_lat : float
        A nova latitude sudoeste.
    southwest_lon : float
        A nova longitude sudoeste.
    northeast_lat : float
        A nova latitude nordeste.
    northeast_lon : float
        A nova longitude nordeste.
    """
    config_path = "./config.py"

    # Lê o conteúdo do arquivo config.py
    with open(config_path, "r") as f:
        config_content = f.readlines()

    # Atualiza as linhas com os novos valores
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

    # Escreve o conteúdo atualizado de volta no arquivo
    with open(config_path, "w") as f:
        f.writelines(config_content)

def calculate_coordinates(radius, southwest_lat, southwest_lon, northeast_lat, northeast_lon):
    """
    Gera um arquivo CSV com as coordenadas geográficas de uma área retangular
    e de acordo com um passo predeterminado em metros, além de atualizar os valores no arquivo de configuração.

    Parâmetros
    ----------
    Nenhum parâmetro.

    Retorna
    -------
    str
        Mensagem indicando o fim da execução.
    """

    RADIUS = radius
    SOUTHWEST_LAT = southwest_lat
    NORTHEAST_LAT = northeast_lat
    NORTHEAST_LON = northeast_lon
    SOUTHWEST_LON = southwest_lon

    # Atualiza os valores no arquivo de configuração
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

    return "Execução realizada com sucesso."

def make_request(url, params=None, method="GET"):
    """
    Faz uma requisição HTTP de acordo com o método especificado e retorna a resposta JSON.

    Parâmetros
    ----------
    url : str
        A URL para fazer a requisição.
    params : dict
        Parâmetros opcionais a serem incluídos na requisição.
    method : str
        O método HTTP a ser utilizado (GET ou POST).

    Retorna
    -------
    dict
        A resposta JSON.
    """
    try:
        if method.upper() == "POST":
            response = requests.post(url, json=params)
        else:
            response = requests.get(url, params=params)
        print("Request URL:", response.url)  # Log da URL da requisição
        response_data = response.json()
        print("Response:", response_data)  # Log da resposta da API
        return response_data
    except Exception as e:
        print("Erro durante a requisição:", str(e))  # Log de erros
        return {"status": "ERROR", "error_message": str(e)}

def request_google_places():
    """
    Realiza requisições à nova API Google Places Nearby Search (POST),
    enriquecendo os dados com base nas coordenadas e categorias fornecidas.

    Retorna
    -------
    str
        Mensagem indicando se o fluxo foi executado com sucesso ou
        qualquer erro que interrompeu a execução.
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

            # Usar o método POST para a requisição
            response = make_request(url, params=payload, method="POST")

            if response.get("status") == "ERROR":
                return f"Error: {response.get('error_message')}"

            if "places" not in response:
                return f"Error: {response}"

            establishments.extend(response["places"])

            # TODO: Lidar com paginação, caso a API precise
            for establishment in establishments:
                for feature_index in range(len(establishments_features_labels) - 1):
                    label = establishments_features_labels[feature_index]
                    try:
                        if label == "name":
                            value = establishment["displayName"]["text"]
                        elif label == "formatted_address":
                            value = establishment["formattedAddress"]
                        else:
                            value = establishment.get(label)
                        establishments_features_data[feature_index].append(value)
                    except Exception:
                        establishments_features_data[feature_index].append(None)

                establishments_features_data[len(establishments_features_data) - 1].append(cat)

    export_data_request(establishments_features_labels, establishments_features_data)
    return "Execução realizada com sucesso."
