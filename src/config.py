from dotenv import load_dotenv

GOOGLE_MAPS_API = 'https://maps.googleapis.com/maps/api'
API = '/place'
SEARCH_COMPONENT = '/nearbysearch'
OUTPUT_TYPE = '/json?'

RADIUS = 4444
NORTHEAST_LAT = -25.329914975179992
NORTHEAST_LON = -49.20322728948593
SOUTHWEST_LAT = -25.512242704374355
SOUTHWEST_LON = -49.32304693059921

load_dotenv('.env')