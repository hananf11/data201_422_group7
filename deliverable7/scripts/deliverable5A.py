import os
import requests
import pandas as pd
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()


def search_api_for_location(
    longitude,
    latitude,
    api_key,
    layer_id="123515"
):
    url = "https://koordinates.com/services/query/v1/vector.json"

    params = {
        "key": api_key,
        "x": longitude,
        "y": latitude,
        "layer": layer_id,
        "with_field_names": "true"
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        if response.status_code == 200:
            response_json = response.json()

            features = response_json["vectorQuery"]["layers"][
                layer_id
            ]["features"]

            if features:
                return features[0]["properties"]["SA22026_V1_00"]

            return None

        print(
            f"Failed request ({response.status_code}) "
            f"for {longitude}, {latitude}"
        )
        return None

    except requests.RequestException as e:
        print(
            f"Request failed for {longitude}, {latitude}: {e}"
        )
        return None


def lookup_listing(row, api_key, layer_id):
    listing_id = row["id"]

    location_id = search_api_for_location(
        row["longitude"],
        row["latitude"],
        api_key,
        layer_id
    )

    return listing_id, location_id


def add_location_ids(
    input_file="./output/christchurch_listings_clean.csv",
    output_file="./output/christchurch_listings_clean_with_area.csv",
    api_key=None,
    layer_id="123515",
    max_workers=10
):
    if api_key is None:
        api_key = os.getenv("KOORDINATES_API_KEY")

    if not api_key:
        raise ValueError(
            "KOORDINATES_API_KEY was not found."
        )

    df = pd.read_csv(input_file)

    unique_listings = (
        df[["id", "longitude", "latitude"]]
        .drop_duplicates(subset="id")
        .copy()
    )

    print(f"Total rows: {len(df)}")
    print(f"Unique listings: {len(unique_listings)}")
    print(f"Concurrent requests: {max_workers}")

    location_map = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:

        futures = {
            executor.submit(
                lookup_listing,
                row,
                api_key,
                layer_id
            ): row["id"]
            for _, row in unique_listings.iterrows()
        }

        completed = 0
        total = len(futures)

        for future in as_completed(futures):

            listing_id = futures[future]

            try:
                listing_id, location_id = future.result()
                location_map[listing_id] = location_id

            except Exception as e:
                print(
                    f"Failed listing {listing_id}: {e}"
                )
                location_map[listing_id] = None

            completed += 1

            if completed % 100 == 0 or completed == total:
                print(
                    f"Completed {completed}/{total}"
                )

    df["location_id"] = df["id"].map(location_map)

    df.to_csv(output_file, index=False)

    print(f"Saved to {output_file}")

    return df