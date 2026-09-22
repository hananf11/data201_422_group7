"""
Step 7: Where in Christchurch is the gap between short-term (AirBnB) and
long-term (rental bond) prices the largest?

Approach
--------
- Long-term nightly equivalent for an area & quarter = median weekly bond rent / 7
  (bond data rows where dwelling_type == "ALL" and number_of_beds == "ALL").
- For every AirBnB listing-month with a known price:
      gap  = airbnb_price - median_weekly_rent / 7
      ratio = airbnb_price / (median_weekly_rent / 7)
- Summarise and plot the distribution of gaps per location_id, and pooled
  into the larger AirBnB "ward" (neighbourhood) areas.

Inputs : week9/data/christchurch_listings_clean_with_area.csv
         week9/data/cleaned_rental_bond_data.csv
Outputs: week9/output/step7_gap_per_listing.csv
         week9/output/step7_gap_by_location.csv
         week9/output/step7_gap_boxplot_by_location.png
         week9/output/step7_gap_boxplot_by_ward.png
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "output")
os.makedirs(OUT, exist_ok=True)


def month_to_quarter(month_year: str) -> str:
    """'2025-10' -> '2025-10'; '2025-12' -> '2025-10'; '2026-02' -> '2026-01'."""
    year, month = int(month_year[:4]), int(month_year[5:7])
    quarter_start = (month - 1) // 3 * 3 + 1
    return f"{year:04d}-{quarter_start:02d}"


# ---------------- load ----------------
listings = pd.read_csv(
    os.path.join(DATA, "christchurch_listings_clean_with_area.csv"),
    dtype={"id": str, "host_id": str, "location_id": str},
)
rental = pd.read_csv(
    os.path.join(DATA, "cleaned_rental_bond_data.csv"),
    dtype={"location_id": str},
)

# SA2-level median weekly rent per quarter (all dwellings, all bed counts)
rental_sa2 = rental[
    (rental["dwelling_type"] == "ALL")
    & (rental["number_of_beds"] == "ALL")
    & rental["median_rent"].notna()
].copy()
rental_sa2["quarter"] = (
    rental_sa2["time_frame"].str[:4] + "-"
    + ((rental_sa2["time_frame"].str[5:7].astype(int) - 1) // 3 * 3 + 1).astype(str).str.zfill(2)
)
rental_sa2 = rental_sa2[["location_id", "quarter", "median_rent"]]
rental_sa2 = rental_sa2.rename(columns={"median_rent": "median_weekly_rent"})

listings["quarter"] = listings["month_year"].map(month_to_quarter)

# ---------------- join ----------------
df = listings.merge(rental_sa2, on=["location_id", "quarter"], how="inner")
df = df[df["price"].notna()].copy()
df["lt_nightly"] = df["median_weekly_rent"] / 7.0
df["gap"] = df["price"] - df["lt_nightly"]
df["ratio"] = df["price"] / df["lt_nightly"]

print(
    f"Listings matched to bond data: {len(df):,} listing-months, "
    f"{df['id'].nunique():,} unique listings, {df['location_id'].nunique()} areas"
)
print(
    f"Median gap city-wide: ${df['gap'].median():.0f}/night  "
    f"(median ratio: {df['ratio'].median():.1f}x long-term)"
)

# ---------------- per-area summary ----------------
by_area = (
    df.groupby("location_id")
    .agg(
        n_listings=("id", "nunique"),
        median_airbnb_price=("price", "median"),
        median_weekly_rent=("median_weekly_rent", "median"),
        median_gap=("gap", "median"),
        mean_gap=("gap", "mean"),
        median_ratio=("ratio", "median"),
    )
    .sort_values("median_gap", ascending=False)
)
by_area["median_lt_nightly"] = by_area["median_weekly_rent"] / 7.0

# name each SA2 by the dominant AirBnB ward (larger-area label for readability)
sa2_ward = df.groupby("location_id")["neighbourhood"].agg(lambda s: s.mode().iat[0])
by_area.insert(0, "ward", sa2_ward)

by_area.to_csv(os.path.join(OUT, "step7_gap_by_location.csv"))

# only rank areas with a reasonable sample of listings
reliable = by_area[by_area["n_listings"] >= 10]
top = reliable.head(15)
print("\nTop 15 areas (>=10 listings) by median short-term vs long-term gap ($/night):")
print(
    top[["ward", "n_listings", "median_airbnb_price", "median_lt_nightly",
         "median_gap", "median_ratio"]].round(1).to_string()
)

# save listing-level table
df[[
    "id", "month_year", "quarter", "location_id", "neighbourhood", "room_type",
    "price", "median_weekly_rent", "lt_nightly", "gap", "ratio",
]].to_csv(os.path.join(OUT, "step7_gap_per_listing.csv"), index=False)

# ---------------- plots ----------------
# boxplot of gaps for the 15 areas with the largest median gap
order = top.index.tolist()
data = [df.loc[df["location_id"] == a, "gap"].values for a in order]
labels = [f"{a}\n{top.loc[a, 'ward'].replace(' Ward', '')}" for a in order]

fig, ax = plt.subplots(figsize=(12, 6))
ax.boxplot(data, tick_labels=labels, showfliers=False)
ax.axhline(0, color="grey", lw=0.8)
ax.set_ylabel("AirBnB price - long-term nightly equivalent ($/night)")
ax.set_title("Short-term vs long-term rental gap by area (top 15 by median gap)")
plt.xticks(rotation=45, ha="right", fontsize=8)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "step7_gap_boxplot_by_location.png"), dpi=150)
plt.close()

# pooled to wards (larger areas)
wards = df.groupby("neighbourhood").filter(lambda g: g["id"].nunique() >= 30)
ward_order = (
    wards.groupby("neighbourhood")["gap"].median().sort_values(ascending=False).index
)
fig, ax = plt.subplots(figsize=(12, 6))
ward_data = [wards.loc[wards["neighbourhood"] == w, "gap"].values for w in ward_order]
ax.boxplot(ward_data, tick_labels=[w.replace(" Ward", "") for w in ward_order], showfliers=False)
ax.axhline(0, color="grey", lw=0.8)
ax.set_ylabel("AirBnB price - long-term nightly equivalent ($/night)")
ax.set_title("Short-term vs long-term rental gap, pooled by ward")
plt.xticks(rotation=45, ha="right", fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "step7_gap_boxplot_by_ward.png"), dpi=150)
plt.close()

print(f"\nSaved outputs to {OUT}")
