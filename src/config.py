import os
import json

CONFIG_PATH = "config.json"
DEFAULT_CONFIG = {
    "GOOGLE_MAPS_API": "https://maps.googleapis.com/maps/api",
    "API": "/place",
    "SEARCH_COMPONENT": "/nearbysearch",
    "OUTPUT_TYPE": "/json?",
    "RADIUS": 4444,
    "NORTHEAST_LAT": -25.329914975179992,
    "NORTHEAST_LON": -49.20322728948593,
    "SOUTHWEST_LAT": -25.512242704374355,
    "SOUTHWEST_LON": -49.32304693059921,
    "API_KEY": ""
}

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return DEFAULT_CONFIG.copy()
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    # Fill in any missing keys with defaults
    for k, v in DEFAULT_CONFIG.items():
        config.setdefault(k, v)
    return config

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

def get_config_value(key):
    config = load_config()
    return config.get(key)

def set_config_value(key, value):
    config = load_config()
    config[key] = value
    save_config(config)
