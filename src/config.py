from dotenv import load_dotenv

GOOGLE_MAPS_API = 'https://maps.googleapis.com/maps/api'
API = '/place'
SEARCH_COMPONENT = '/nearbysearch'
OUTPUT_TYPE = '/json?'

RADIUS = 1000
NORTHEAST_LAT = -25.423491016468454
NORTHEAST_LON = -49.26416344932349
SOUTHWEST_LAT = -25.453603302800552
SOUTHWEST_LON = -49.27641578010352

load_dotenv('.env')