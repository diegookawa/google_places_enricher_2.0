from dotenv import load_dotenv

GOOGLE_MAPS_API = 'https://maps.googleapis.com/maps/api'
API = '/place'
SEARCH_COMPONENT = '/nearbysearch'
OUTPUT_TYPE = '/json?'

RADIUS = 3333
NORTHEAST_LAT = -25.338603496267517
NORTHEAST_LON = -49.173993893432616
SOUTHWEST_LAT = -25.478464689595437
SOUTHWEST_LON = -49.32265264587402

load_dotenv('.env')