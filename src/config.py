from dotenv import load_dotenv

GOOGLE_MAPS_API = 'https://maps.googleapis.com/maps/api'
API = '/place'
SEARCH_COMPONENT = '/nearbysearch'
OUTPUT_TYPE = '/json?'

RADIUS = 3333
NORTHEAST_LAT = -25.39498613304645
NORTHEAST_LON = -49.2234658976078
SOUTHWEST_LAT = -25.44955990914098
SOUTHWEST_LON = -49.283547379541396

load_dotenv('.env')