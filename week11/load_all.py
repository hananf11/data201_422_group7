"""
Stage 1: Combine the monthly Inside Airbnb listings files into one
Christchurch-only dataset.

Python port of Load_All.r (Deliverable 7: pipeline unified to Python).

- Reads every *.csv in data/listings/ (files named "YYYY-MM-DD_listings.csv",
  as saved by the download step).
- Extracts month_year ("YYYY-MM") from each filename.
- Keeps only neighbourhood_group == "Christchurch City".
- Prints missing-value counts and the room-type distribution.
- Writes data/listings_christchurch.csv and the price histogram PNG.

Input : data/listings/*.csv
Output: data/listings_christchurch.csv
        data/listings_christchurch_price_hist.png
"""

import glob
import os
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_DIR = "data/listings"
OUT_CSV = "data/listings_christchurch.csv"
OUT_PNG = "data/listings_christchurch_price_hist.png"

CHRISTCHURCH = "Christchurch City"


def main():
    files = sorted(glob.glob(os.path.join(DATA_DIR, "*.csv")))
    if not files:
        raise FileNotFoundError(
            f"No listings CSVs found in {DATA_DIR}/ — download the monthly "
            "listings.csv files first (see README)."
        )

    frames = []
    for file in files:
        match = re.search(r"(\d{4})-(\d{2})", os.path.basename(file))
        if not match:
            print(f"Skipping {file}: filename has no YYYY-MM date")
            continue
        month_listings = pd.read_csv(file)
        month_listings["month_year"] = f"{match.group(1)}-{match.group(2)}"
        frames.append(month_listings)
        print(f"Loaded {os.path.basename(file)} ({len(month_listings)} rows)")

    listings = pd.concat(frames, ignore_index=True)
    print(f"Combined: {len(listings)} rows, {len(frames)} months")

    listings_christchurch = listings[
        listings["neighbourhood_group"] == CHRISTCHURCH
    ].copy()
    print(f"Christchurch City listings: {len(listings_christchurch)} rows")
    print("Unique months:", sorted(listings_christchurch["month_year"].unique()))

    na_counts = listings_christchurch.isna().sum()
    print("\nMissing values per column:")
    print(na_counts.to_string())

    print("\nListings per room type:")
    print(listings_christchurch["room_type"].value_counts().to_string())

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    listings_christchurch.to_csv(OUT_CSV, index=False, na_rep="NA")
    print(f"\nWrote {OUT_CSV}")

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(listings_christchurch["price"].dropna(), bins=100, color="tab:blue")
    ax.set_title("Price Distribution in Christchurch")
    ax.set_xlabel("Price")
    ax.set_ylabel("Frequency")
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=150)
    print(f"Wrote {OUT_PNG}")


if __name__ == "__main__":
    main()
