from dotenv import load_dotenv

GOOGLE_MAPS_API = 'https://maps.googleapis.com/maps/api'
API = '/place'
SEARCH_COMPONENT = '/nearbysearch'
OUTPUT_TYPE = '/json?'

RADIUS = 4444
NORTHEAST_LAT = -25.33550052462907
NORTHEAST_LON = -49.17066258983612
SOUTHWEST_LAT = -25.517200145632895
SOUTHWEST_LON = -49.344040580558776

load_dotenv('.env')