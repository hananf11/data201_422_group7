"""
Stage 3: Clean the quarterly rental bond data.

Python port of delivery4/clean_rental_bond_data.R (Deliverable 7).

- Reads every column as text; only the literal string "NULL" means missing.
  (The literal "NA" in Number Of Beds is a distinct source category, not
  missing, and is kept as text on import.)
- Converts column headers to snake_case (janitor::clean_names equivalent).
- Converts date and numeric columns to proper types.
- Restricts rows to the study period.
- Adds location_scope and the beds_category / beds_numeric columns.

Input : delivery4/data/Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv
Output: delivery4/output/cleaned_rental_bond_data.csv
"""

import os
import re

import pandas as pd

START_DATE = "2025-10-01"
END_DATE = "2026-09-30"

INPUT_FILE = "delivery4/data/Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv"
OUTPUT_FILE = "delivery4/output/cleaned_rental_bond_data.csv"

NUMERIC_COLUMNS = [
    "total_bonds", "active_bonds", "closed_bonds", "median_rent",
    "geometric_mean_rent", "upper_quartile_rent", "lower_quartile_rent",
    "log_std_dev_weekly_rent",
]


def to_snake(name: str) -> str:
    """janitor::clean_names-style snake_case: 'TimeFrame' -> 'time_frame'."""
    name = name.lstrip("\ufeff").strip()
    name = re.sub(r"\W", "_", name)
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    return re.sub(r"_+", "_", name).strip("_").lower()


def main():
    raw = pd.read_csv(INPUT_FILE, dtype=str, keep_default_na=False,
                      na_values=["NULL"])
    raw.columns = [to_snake(c) for c in raw.columns]

    clean = raw.copy()
    clean["time_frame"] = pd.to_datetime(clean["time_frame"],
                                         format="%Y-%m-%d", errors="coerce")
    for col in NUMERIC_COLUMNS:
        clean[col] = pd.to_numeric(clean[col], errors="coerce")

    # filtered to the time frame of interest
    start, end = pd.Timestamp(START_DATE), pd.Timestamp(END_DATE)
    before = len(clean)
    clean = clean[(clean["time_frame"] >= start) & (clean["time_frame"] <= end)]
    print(f"Rows: {before} -> {len(clean)} after filtering to "
          f"{START_DATE}..{END_DATE}")

    # classify the location scope based on location_id
    clean["location_scope"] = pd.NA
    clean.loc[clean["location_id"] == "-99", "location_scope"] = "National"
    clean.loc[clean["location_id"].isna(), "location_scope"] = "Unclassified"
    clean["location_scope"] = clean["location_scope"].fillna(
        "Territorial Authority")

    # categorise the number of beds and add a numeric version
    clean["beds_category"] = clean["number_of_beds"].where(
        clean["number_of_beds"] != "NA", other=pd.NA)
    clean["beds_numeric"] = pd.to_numeric(clean["number_of_beds"],
                                          errors="coerce")

    counts = clean["location_scope"].value_counts(dropna=False)
    print("Rows per location scope:")
    print(counts.to_string())

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    clean.to_csv(OUTPUT_FILE, index=False, na_rep="NA",
                 date_format="%Y-%m-%d")
    print(f"Wrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
