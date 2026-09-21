import os

from pprint import pprint
import requests
from dotenv import load_dotenv

load_dotenv()

KOORDINATES_API_KEY = os.getenv("KOORDINATES_API_KEY")
STATS_NZ_AREA_LAYER_ID = "123515"


def search_api_for_location(longitude, latitude):
    url = "https://koordinates.com/services/query/v1/vector.json?"
    url += f"key={KOORDINATES_API_KEY}&"
    url += f"x={longitude}&y={latitude}&"
    url += f"layer={STATS_NZ_AREA_LAYER_ID}&with_field_names=true"
    response = requests.get(url)
    if response.status_code == 200:
        response_json = response.json()
        features = response_json["vectorQuery"]["layers"][STATS_NZ_AREA_LAYER_ID][
            "features"
        ]
        return features[0]["properties"]["SA22026_V1_00"]
    else:
        raise Exception(f"Failed to get data from API: {response.status_code}")


# test with point 172.8294261, -43.65541852, in area "Banks Peninsula Eastern Bays"
pprint(search_api_for_location(172.8294261, -43.65541852))
