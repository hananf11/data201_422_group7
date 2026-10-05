import gzip
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def month_to_quarter(month_year):
    year = int(month_year[:4])
    month = int(month_year[5:7])
    quarter_start = (month - 1) // 3 * 3 + 1
    return f"{year:04d}-{quarter_start:02d}"


def analyze_property_counts(
    listings_file="./output/christchurch_listings_clean_with_area.csv",
    rental_file="./output/cleaned_rental_bond_data.csv",
    detailed_file="./data/detailed/listings_detailed_2026-06-19.csv.gz",
    output_dir="./output",
    latest_quarter="2026-04"
):
    os.makedirs(output_dir, exist_ok=True)

    # ---------------- load ----------------
    print("Loading Airbnb listings...")
    listings = pd.read_csv(
        listings_file,
        dtype={"id": str, "host_id": str, "location_id": str}
    )

    # The with_area file may store IDs as floats such as "40183765.0"
    listings["id"] = listings["id"].str.replace(r"\.0$", "", regex=True)

    print("Loading rental bond data...")
    rental = pd.read_csv(
        rental_file,
        dtype={"location_id": str}
    )

    # Keep territorial-authority / SA2-level rows only
    rental = rental[
        rental["location_id"].notna()
        & (rental["location_id"] != "-99")
    ]

    # ---------------- area labels ----------------
    sa2_ward = (
        listings.groupby("location_id")["neighbourhood"]
        .agg(lambda s: s.mode().iat[0])
        .rename("ward")
    )

    # ---------------- property counts per area & quarter ----------------
    print("Calculating Airbnb listing counts...")

    listings["quarter"] = listings["month_year"].map(month_to_quarter)

    # Count unique listings per location per month,
    # then average the monthly counts within each quarter.
    monthly = (
        listings
        .groupby(["location_id", "quarter", "month_year"])["id"]
        .nunique()
    )

    airbnb_counts = (
        monthly
        .groupby(["location_id", "quarter"])
        .mean()
        .rename("airbnb_listings")
        .reset_index()
    )

    print("Calculating long-term rental counts...")

    bond_counts = rental[
        (rental["dwelling_type"] == "ALL")
        & (rental["number_of_beds"] == "ALL")
    ][
        ["location_id", "time_frame", "active_bonds"]
    ].copy()

    bond_counts["quarter"] = (
        bond_counts["time_frame"].str[:4]
        + "-"
        + (
            (
                bond_counts["time_frame"].str[5:7].astype(int) - 1
            ) // 3 * 3 + 1
        ).astype(str).str.zfill(2)
    )

    bond_counts = (
        bond_counts
        .groupby(["location_id", "quarter"], as_index=False)["active_bonds"]
        .sum()
    )

    counts = airbnb_counts.merge(
        bond_counts,
        on=["location_id", "quarter"],
        how="outer"
    )

    counts["airbnb_share_pct"] = (
        100
        * counts["airbnb_listings"]
        / (counts["airbnb_listings"] + counts["active_bonds"])
    )

    counts = counts.join(sa2_ward, on="location_id")

    counts_file = os.path.join(
        output_dir,
        "step8_counts_by_location.csv"
    )

    counts.to_csv(counts_file, index=False)

    # ---------------- latest quarter counts ----------------
    latest = counts[
        counts["quarter"] == latest_quarter
    ].dropna(
        subset=["airbnb_listings", "active_bonds"]
    )

    latest = latest.sort_values(
        "active_bonds",
        ascending=False
    )

    print(
        f"\nProperty counts in {latest_quarter} "
        "(top 15 by long-term stock):"
    )

    print(
        latest.head(15)[
            [
                "ward",
                "airbnb_listings",
                "active_bonds",
                "airbnb_share_pct"
            ]
        ]
        .round(1)
        .to_string(index=False)
    )

    # ---------------- property count barplot ----------------
    top20 = latest.head(20).copy()

    label = (
        top20["location_id"]
        + "\n"
        + top20["ward"].str.replace(" Ward", "")
    )

    x = range(len(top20))
    w = 0.4

    fig, ax = plt.subplots(figsize=(13, 6))

    ax.bar(
        [i - w / 2 for i in x],
        top20["active_bonds"],
        w,
        label="Long-term rentals (active bonds)"
    )

    ax.bar(
        [i + w / 2 for i in x],
        top20["airbnb_listings"],
        w,
        label="AirBnB listings"
    )

    ax.set_ylabel("Properties")
    ax.set_title(
        f"Long-term rentals vs AirBnB listings by area "
        f"({latest_quarter})"
    )

    ax.set_xticks(
        list(x),
        label,
        rotation=45,
        ha="right",
        fontsize=8
    )

    ax.legend()

    plt.tight_layout()

    counts_plot = os.path.join(
        output_dir,
        "step8_counts_barplot.png"
    )

    plt.savefig(counts_plot, dpi=150)
    plt.close()

    # ---------------- bed comparison ----------------
    print("Calculating bed comparison...")

    beds_map = {
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "5+": 5
    }

    bond_beds = rental[
        (rental["dwelling_type"] == "ALL")
        & rental["location_id"].notna()
        & (
            rental["time_frame"].str[:7]
            == latest_quarter
        )
    ].copy()

    bond_beds["beds"] = (
        bond_beds["number_of_beds"]
        .astype(str)
        .map(beds_map)
    )

    bond_beds = (
        bond_beds
        .dropna(subset=["beds"])
        .assign(
            rental_beds=lambda d:
                d["beds"] * d["active_bonds"]
        )
        .groupby("location_id", as_index=False)["rental_beds"]
        .sum()
    )

    # ---------------- detailed Airbnb bedroom data ----------------
    print("Loading detailed Airbnb bedroom data...")

    with gzip.open(
        detailed_file,
        "rt",
        encoding="utf-8"
    ) as f:

        detailed = pd.read_csv(
            f,
            low_memory=False,
            usecols=[
                "id",
                "latitude",
                "longitude",
                "bedrooms"
            ]
        )

    # The with_area file has precision issues with long listing IDs,
    # so match using rounded coordinates instead.
    coords = (
        listings[
            listings["month_year"] == "2026-06"
        ][
            [
                "latitude",
                "longitude",
                "location_id"
            ]
        ]
        .dropna(subset=["location_id"])
        .drop_duplicates(
            ["latitude", "longitude"]
        )
    )

    coords = coords.assign(
        lat_key=coords["latitude"].round(6),
        lon_key=coords["longitude"].round(6)
    )

    june = detailed.merge(
        coords,
        left_on=[
            detailed["latitude"].round(6),
            detailed["longitude"].round(6)
        ],
        right_on=[
            "lat_key",
            "lon_key"
        ],
        how="inner"
    )

    print(
        "Detailed listings matched to areas by coordinates: "
        f"{len(june):,}"
    )

    airbnb_beds = (
        june
        .dropna(subset=["bedrooms"])
        .groupby(
            "location_id",
            as_index=False
        )["bedrooms"]
        .sum()
        .rename(
            columns={
                "bedrooms": "airbnb_beds"
            }
        )
    )

    # Restrict rental areas to areas appearing in Airbnb data.
    chch_areas = set(
        listings["location_id"].dropna()
    )

    bond_beds = bond_beds[
        bond_beds["location_id"].isin(chch_areas)
    ]

    beds = (
        airbnb_beds
        .merge(
            bond_beds,
            on="location_id",
            how="outer"
        )
        .join(
            sa2_ward,
            on="location_id"
        )
    )

    beds["airbnb_beds"] = (
        beds["airbnb_beds"].fillna(0)
    )

    beds["airbnb_bed_share_pct"] = (
        100
        * beds["airbnb_beds"]
        / (
            beds["airbnb_beds"]
            + beds["rental_beds"]
        )
    )

    beds = beds.sort_values(
        "rental_beds",
        ascending=False
    )

    beds_file = os.path.join(
        output_dir,
        "step8_beds_by_location.csv"
    )

    beds.to_csv(
        beds_file,
        index=False
    )

    print(
        f"\nBed comparison in {latest_quarter} "
        "(top 15 by long-term beds):"
    )

    print(
        beds.head(15)[
            [
                "ward",
                "airbnb_beds",
                "rental_beds",
                "airbnb_bed_share_pct"
            ]
        ]
        .round(1)
        .to_string(index=False)
    )

    # ---------------- bed comparison barplot ----------------
    top20b = beds.head(20).copy()

    label = (
        top20b["location_id"]
        + "\n"
        + top20b["ward"].str.replace(" Ward", "")
    )

    x = range(len(top20b))

    fig, ax = plt.subplots(figsize=(13, 6))

    ax.bar(
        [i - w / 2 for i in x],
        top20b["rental_beds"],
        w,
        label="Beds in long-term rentals"
    )

    ax.bar(
        [i + w / 2 for i in x],
        top20b["airbnb_beds"],
        w,
        label="AirBnB bedrooms"
    )

    ax.set_ylabel("Beds")
    ax.set_title(
        f"Beds: long-term rentals vs AirBnB by area "
        f"({latest_quarter})"
    )

    ax.set_xticks(
        list(x),
        label,
        rotation=45,
        ha="right",
        fontsize=8
    )

    ax.legend()

    plt.tight_layout()

    beds_plot = os.path.join(
        output_dir,
        "step8_beds_barplot.png"
    )

    plt.savefig(
        beds_plot,
        dpi=150
    )

    plt.close()

    print(f"\nSaved outputs to {output_dir}")

    return {
        "counts": counts,
        "latest_counts": latest,
        "beds": beds,
        "airbnb_beds": airbnb_beds,
        "rental_beds": bond_beds
    }