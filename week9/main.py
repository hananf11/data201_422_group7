import os

from pprint import pprint
import requests
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

KOORDINATES_API_KEY = os.getenv("KOORDINATES_API_KEY")
STATS_NZ_AREA_LAYER_ID = "123515"


def search_api_for_location(longitude, latitude):
    print(f"Searching for location {longitude}, {latitude}")
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
        print(f"Found {len(features)} features")
        print(f"Features: {features}")
        return features[0]["properties"]["SA22026_V1_00"]
    else:
        print(f"Failed to get data from API: {response.status_code}")
        raise Exception(f"Failed to get data from API: {response.status_code}")


def main():
    csv_in = "./christchurch_listings_clean.csv"
    csv_out = "./christchurch_listings_clean_with_area.csv"
    df = pd.read_csv(csv_in)
    # test with point 172.8294261, -43.65541852, in area "Banks Peninsula Eastern Bays"
    df["area"] = df.apply(
        lambda row: search_api_for_location(row["longitude"], row["latitude"]), axis=1
    )
    df.to_csv(csv_out, index=False)


if __name__ == "__main__":
    main()
