"""
Stage 5: Merge the cleaned rental bond data with the geocoded AirBnB listings.

Python port of week9/main.R (Deliverable 7). main.R used the %>% pipe without
loading dplyr, so it only ran inside an R session that had dplyr attached —
the Python port fixes that by not depending on any R package.

- Converts both datasets to a common quarterly time variable:
  month_year / time_frame -> quarter ("YYYY-MM" of the quarter start).
- Merges on quarter + location_id (inner join, like R's merge()).
- Prints the median AirBnB price for Christchurch Central (location 326600).

Inputs : week9/data/cleaned_rental_bond_data.csv
         week9/data/christchurch_listings_clean_with_area.csv
Output : week9/output/merged_rental_and_listings_data.csv
"""

import os

import pandas as pd

RENTAL_CSV = "week9/data/cleaned_rental_bond_data.csv"
LISTINGS_CSV = "week9/data/christchurch_listings_clean_with_area.csv"
OUTPUT_FILE = "week9/output/merged_rental_and_listings_data.csv"

CHRISTCHURCH_CENTRAL_ID = "326600"


def date_to_quarter(dates: pd.Series) -> pd.Series:
    """'YYYY-MM' or 'YYYY-MM-DD' -> 'YYYY-MM' of the quarter start."""
    dates = dates.astype(str)
    year = dates.str[:4]
    month = pd.to_numeric(dates.str[5:7], errors="coerce")
    quarter_start_month = ((month - 1) // 3) * 3 + 1
    return year + "-" + quarter_start_month.astype("Int64").astype(str).str.zfill(2)


def main():
    rental = pd.read_csv(RENTAL_CSV, dtype={"location_id": str})
    listings = pd.read_csv(LISTINGS_CSV, dtype={"location_id": str})

    rental["quarter"] = date_to_quarter(rental["time_frame"])
    listings["quarter"] = date_to_quarter(listings["month_year"])

    # join on columns "quarter", "location_id"
    merged = rental.merge(listings, on=["quarter", "location_id"], how="inner")
    print(f"Merged rows: {len(merged)}")

    christchurch_data = merged[
        merged["location_id"] == CHRISTCHURCH_CENTRAL_ID
    ]
    median_price = christchurch_data["price"].median()
    print(f"The median price of rentals in Christchurch Central is: "
          f"${median_price:,.0f}")

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    merged.to_csv(OUTPUT_FILE, index=False)
    print(f"Wrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
