"""
Stage 5: geocode listings via the Koordinates API — incrementally.

A listing's coordinates never change, so its SA2 area never changes either.
The previous output file (data/christchurch_listings_clean_with_area.csv)
therefore acts as a cache: only listing ids that are not in it yet trigger an
API call, every other row reuses the area it already has.

With the full history this makes adding July + August cost one call per NEW
listing (~2,700) instead of one call per listing-month row (~35,800).

Run with no previous output file -> every unique id is geocoded (full run).
"""

import os

import pandas as pd

CSV_IN = "data/christchurch_listings_clean.csv"
CSV_OUT = "data/christchurch_listings_clean_with_area.csv"

STATS_NZ_AREA_LAYER_ID = "123515"


def search_api_for_location(longitude, latitude):
    try:
        import requests
    except ImportError:
        raise SystemExit(
            "requests is not installed — run: pip install requests python-dotenv"
        )

    import time

    api_key = os.getenv("KOORDINATES_API_KEY")
    url = "https://koordinates.com/services/query/v1/vector.json?"
    url += f"key={api_key}&"
    url += f"x={longitude}&y={latitude}&"
    url += f"layer={STATS_NZ_AREA_LAYER_ID}&with_field_names=true"

    response = None
    for attempt in range(3):  # transient 429s / network hiccups: retry twice
        response = requests.get(url)
        if response.status_code == 200:
            break
        time.sleep(2 * (attempt + 1))
    if response.status_code != 200:
        raise RuntimeError(
            f"Koordinates API returned {response.status_code} for "
            f"{longitude}, {latitude}"
        )
    features = response.json()["vectorQuery"]["layers"][
        STATS_NZ_AREA_LAYER_ID
    ]["features"]
    return features[0]["properties"]["SA22026_V1_00"]


def load_known_areas():
    """id -> location_id from the previous output, if it exists."""
    if not os.path.exists(CSV_OUT):
        return {}
    previous = pd.read_csv(CSV_OUT, dtype={"id": str, "location_id": str})
    previous["id"] = previous["id"].str.replace(r"\.0$", "", regex=True)
    previous = previous.dropna(subset=["location_id"])
    return dict(zip(previous["id"], previous["location_id"]))


def geocode_new_ids(new_ids):
    """Query the API once per unknown listing id; {id: location_id}."""
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        raise SystemExit(
            "python-dotenv is not installed — run: pip install requests python-dotenv"
        )
    if not os.getenv("KOORDINATES_API_KEY"):
        raise SystemExit(
            f"KOORDINATES_API_KEY missing (week11/.env) but {len(new_ids)} "
            "listing ids are not geocoded yet — add the key and re-run"
        )
    areas = {}
    for i, (listing_id, longitude, latitude) in enumerate(new_ids, 1):
        areas[listing_id] = search_api_for_location(longitude, latitude)
        if i % 250 == 0 or i == len(new_ids):
            print(f"  geocoded {i}/{len(new_ids)} new ids")
    return areas


def main():
    # ids must stay strings: float conversion corrupts 19-digit listing ids
    df = pd.read_csv(CSV_IN, dtype={"id": str, "host_id": str})
    known = load_known_areas()

    df["location_id"] = df["id"].map(known)

    unknown = df[df["location_id"].isna()][["id", "longitude", "latitude"]]
    unknown = unknown.dropna(subset=["longitude", "latitude"])
    new_ids = list(unknown.drop_duplicates("id").itertuples(index=False, name=None))

    print(
        f"{len(df)} listing-month rows, {df['id'].nunique()} unique ids: "
        f"{len(df) - df['id'].map(known).isna().sum():.0f} rows reuse cached "
        f"areas, {len(new_ids)} new ids to geocode"
    )

    if new_ids:
        areas = geocode_new_ids(new_ids)
        known = {**known, **areas}
        df["location_id"] = df["id"].map(known)

    no_coords = int(df["location_id"].isna().sum())
    if no_coords:
        print(f"  WARN: {no_coords} rows have no coordinates and could not be geocoded")

    df.to_csv(CSV_OUT, index=False)
    print(f"Wrote {CSV_OUT}")


if __name__ == "__main__":
    main()
