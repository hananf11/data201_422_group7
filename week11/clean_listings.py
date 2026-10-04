"""
Stage 2: Clean the Christchurch Airbnb listings.

Python port of delivery4/christchurch_data_cleaner.R (Deliverable 7).

- Removes the license and host_name columns.
- Replaces empty strings with NA.
- Removes duplicate rows (reporting how many were removed).

Input : delivery4/data/christchurch_listings_v2.csv
Output: delivery4/output/christchurch_listings_clean.csv
"""

import os

import pandas as pd

INPUT_FILE = "delivery4/data/christchurch_listings_v2.csv"
OUTPUT_FILE = "delivery4/output/christchurch_listings_clean.csv"


def main():
    listings = pd.read_csv(INPUT_FILE)

    # remove license and host_name columns
    listings_clean = listings.drop(columns=["license", "host_name"])

    # replace empty strings with NA
    for col in listings_clean.columns:
        if listings_clean[col].dtype == object:
            listings_clean[col] = listings_clean[col].replace("", pd.NA)

    # remove duplicates
    rows_before = len(listings_clean)
    duplicates = int(listings_clean.duplicated().sum())
    listings_clean = listings_clean.drop_duplicates()
    rows_after = len(listings_clean)
    print(f"Rows before: {rows_before}, exact duplicates removed: {duplicates}, "
          f"rows after: {rows_after}")

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    listings_clean.to_csv(OUTPUT_FILE, index=False, na_rep="NA")
    print(f"Wrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
