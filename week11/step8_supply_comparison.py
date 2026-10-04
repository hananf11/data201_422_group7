"""
Step 8: Compare how many AirBnB listings and long-term rental properties
(bond data) we have in each location - plus the ambitious bed comparison.

Approach
--------
- AirBnB count per area & quarter: average number of unique listings observed
  per month in that quarter.
- Long-term rental count per area & quarter: active_bonds (dwelling_type ALL,
  number_of_beds ALL).
- Bed comparison (extra ambitious), latest quarter (2026-Q2):
    * AirBnB beds: sum of `bedrooms` from the detailed Inside Airbnb file
      (2026-06-19 scrape), matched to location_id via listing id.
    * Long-term beds: sum over bed categories of active_bonds x beds
      (1-4 as-is, "5+" counted as 5).

Inputs : week9/data/christchurch_listings_clean_with_area.csv
         week9/data/cleaned_rental_bond_data.csv
         week9/data/detailed/listings_detailed_2026-06-19.csv.gz
Outputs: week9/output/step8_counts_by_location.csv
         week9/output/step8_beds_by_location.csv
         week9/output/step8_counts_barplot.png
         week9/output/step8_beds_barplot.png
"""

import gzip
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "output")
os.makedirs(OUT, exist_ok=True)

LATEST_QUARTER = "2026-04"  # 2026-Q2, matches the 2026-06-19 detailed scrape


def month_to_quarter(month_year: str) -> str:
    year, month = int(month_year[:4]), int(month_year[5:7])
    quarter_start = (month - 1) // 3 * 3 + 1
    return f"{year:04d}-{quarter_start:02d}"


# ---------------- load ----------------
listings = pd.read_csv(
    os.path.join(DATA, "christchurch_listings_clean_with_area.csv"),
    dtype={"id": str, "host_id": str, "location_id": str},
)
# the with_area file stores ids as floats ("40183765.0"); normalise to plain ids
listings["id"] = listings["id"].str.replace(r"\.0$", "", regex=True)
rental = pd.read_csv(
    os.path.join(DATA, "cleaned_rental_bond_data.csv"),
    dtype={"location_id": str},
)
# keep territorial-authority (SA2-level) rows only; drop national aggregate / NA
rental = rental[rental["location_id"].notna() & (rental["location_id"] != "-99")]

sa2_ward = (
    listings.groupby("location_id")["neighbourhood"]
    .agg(lambda s: s.mode().iat[0])
    .rename("ward")
)

# ---------------- property counts per area & quarter ----------------
listings["quarter"] = listings["month_year"].map(month_to_quarter)

# unique listings per location per month, averaged within each quarter
monthly = listings.groupby(["location_id", "quarter", "month_year"])["id"].nunique()
airbnb_counts = (
    monthly.groupby(["location_id", "quarter"]).mean().rename("airbnb_listings")
    .reset_index()
)

bond_counts = rental[
    (rental["dwelling_type"] == "ALL") & (rental["number_of_beds"] == "ALL")
][["location_id", "time_frame", "active_bonds"]].copy()
bond_counts["quarter"] = (
    bond_counts["time_frame"].str[:4] + "-"
    + ((bond_counts["time_frame"].str[5:7].astype(int) - 1) // 3 * 3 + 1)
    .astype(str).str.zfill(2)
)
bond_counts = bond_counts.groupby(["location_id", "quarter"], as_index=False)[
    "active_bonds"
].sum()

counts = airbnb_counts.merge(bond_counts, on=["location_id", "quarter"], how="outer")
counts["airbnb_share_pct"] = 100 * counts["airbnb_listings"] / (
    counts["airbnb_listings"] + counts["active_bonds"]
)
counts = counts.join(sa2_ward, on="location_id")
counts.to_csv(os.path.join(OUT, "step8_counts_by_location.csv"), index=False)

latest = counts[counts["quarter"] == LATEST_QUARTER].dropna(
    subset=["airbnb_listings", "active_bonds"]
)
latest = latest.sort_values("active_bonds", ascending=False)
print(f"\nProperty counts in {LATEST_QUARTER} (top 15 by long-term stock):")
print(
    latest.head(15)[
        ["ward", "airbnb_listings", "active_bonds", "airbnb_share_pct"]
    ].round(1).to_string(index=False)
)

top20 = latest.head(20).copy()
label = top20["location_id"] + "\n" + top20["ward"].str.replace(" Ward", "")
x = range(len(top20))
w = 0.4
fig, ax = plt.subplots(figsize=(13, 6))
ax.bar([i - w / 2 for i in x], top20["active_bonds"], w, label="Long-term rentals (active bonds)")
ax.bar([i + w / 2 for i in x], top20["airbnb_listings"], w, label="AirBnB listings")
ax.set_ylabel("Properties")
ax.set_title(f"Long-term rentals vs AirBnB listings by area ({LATEST_QUARTER})")
ax.set_xticks(list(x), label, rotation=45, ha="right", fontsize=8)
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(OUT, "step8_counts_barplot.png"), dpi=150)
plt.close()

# ---------------- bed comparison (extra ambitious, latest quarter) ----------------
beds_map = {"1": 1, "2": 2, "3": 3, "4": 4, "5+": 5}
bond_beds = rental[
    (rental["dwelling_type"] == "ALL")
    & rental["location_id"].notna()
    & (rental["time_frame"].str[:7] == LATEST_QUARTER)
].copy()
bond_beds["beds"] = bond_beds["number_of_beds"].astype(str).map(beds_map)
bond_beds = (
    bond_beds.dropna(subset=["beds"])
    .assign(rental_beds=lambda d: d["beds"] * d["active_bonds"])
    .groupby("location_id", as_index=False)["rental_beds"]
    .sum()
)

# detailed scrape has real bedroom counts; take location_id from our area file
with gzip.open(
    os.path.join(DATA, "detailed/listings_detailed_2026-06-19.csv.gz"), "rt", encoding="utf-8"
) as f:
    detailed = pd.read_csv(
        f, low_memory=False, usecols=["id", "latitude", "longitude", "bedrooms"]
    )

# The with_area file corrupted long listing ids to scientific-notation floats
# (precision loss), so match on 6-dp coordinates instead of id.
coords = (
    listings[listings["month_year"] == "2026-06"][["latitude", "longitude", "location_id"]]
    .dropna(subset=["location_id"])
    .drop_duplicates(["latitude", "longitude"])
)
june = detailed.merge(
    coords.assign(
        lat_key=coords["latitude"].round(6), lon_key=coords["longitude"].round(6)
    ),
    left_on=[detailed["latitude"].round(6), detailed["longitude"].round(6)],
    right_on=["lat_key", "lon_key"],
    how="inner",
)
print(f"Detailed listings matched to areas by coordinates: {len(june):,}")
airbnb_beds = (
    june.dropna(subset=["bedrooms"])
    .groupby("location_id", as_index=False)["bedrooms"]
    .sum()
    .rename(columns={"bedrooms": "airbnb_beds"})
)

# restrict the bond side to Christchurch areas present in the AirBnB data
chch_areas = set(listings["location_id"].dropna())
bond_beds = bond_beds[bond_beds["location_id"].isin(chch_areas)]

beds = airbnb_beds.merge(bond_beds, on="location_id", how="outer").join(
    sa2_ward, on="location_id"
)
beds["airbnb_beds"] = beds["airbnb_beds"].fillna(0)
beds["airbnb_bed_share_pct"] = 100 * beds["airbnb_beds"] / (
    beds["airbnb_beds"] + beds["rental_beds"]
)
beds = beds.sort_values("rental_beds", ascending=False)
beds.to_csv(os.path.join(OUT, "step8_beds_by_location.csv"), index=False)

print(f"\nBed comparison in {LATEST_QUARTER} (top 15 by long-term beds):")
print(
    beds.head(15)[
        ["ward", "airbnb_beds", "rental_beds", "airbnb_bed_share_pct"]
    ].round(1).to_string(index=False)
)

top20b = beds.head(20).copy()
label = top20b["location_id"] + "\n" + top20b["ward"].str.replace(" Ward", "")
fig, ax = plt.subplots(figsize=(13, 6))
ax.bar([i - w / 2 for i in x], top20b["rental_beds"], w, label="Beds in long-term rentals")
ax.bar([i + w / 2 for i in x], top20b["airbnb_beds"], w, label="AirBnB bedrooms")
ax.set_ylabel("Beds")
ax.set_title(f"Beds: long-term rentals vs AirBnB by area ({LATEST_QUARTER})")
ax.set_xticks(list(x), label, rotation=45, ha="right", fontsize=8)
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(OUT, "step8_beds_barplot.png"), dpi=150)
plt.close()

print(f"\nSaved outputs to {OUT}")
