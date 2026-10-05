import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

KOORDINATES_API_KEY = os.getenv("KOORDINATES_API_KEY")
STATS_NZ_AREA_LAYER_ID = "123515"


def search_api_for_location(longitude, latitude):
    print(f"Searching for location {longitude}, {latitude}")

    url = "https://koordinates.com/services/query/v1/vector.json"

    params = {
        "key": KOORDINATES_API_KEY,
        "x": longitude,
        "y": latitude,
        "layer": STATS_NZ_AREA_LAYER_ID,
        "with_field_names": "true"
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        response_json = response.json()

        features = response_json["vectorQuery"]["layers"][
            STATS_NZ_AREA_LAYER_ID
        ]["features"]

        if features:
            return features[0]["properties"]["SA22026_V1_00"]

        return None

    else:
        print(f"Failed to get data from API: {response.status_code}")
        return None


def main():
    csv_in = "./christchurch_listings_clean.csv"
    csv_out = "./christchurch_listings_clean_with_area.csv"

    df = pd.read_csv(csv_in)

    # Get one row per unique Airbnb listing
    unique_listings = df[
        ["id", "longitude", "latitude"]
    ].drop_duplicates(subset="id").copy()

    print(f"Total rows: {len(df)}")
    print(f"Unique listings: {len(unique_listings)}")

    # Create dictionary: Airbnb ID -> Stats NZ location ID
    location_map = {}

    for _, row in unique_listings.iterrows():
        listing_id = row["id"]

        location_id = search_api_for_location(
            row["longitude"],
            row["latitude"]
        )

        location_map[listing_id] = location_id

    # Add location ID based on Airbnb listing ID
    df["location_id"] = df["id"].map(location_map)

    df.to_csv(csv_out, index=False)

    print(f"Saved to {csv_out}")


if __name__ == "__main__":
    main()