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


def analyze_price_gap(
    listings_file="./output/christchurch_listings_clean_with_area.csv",
    rental_file="./output/cleaned_rental_bond_data.csv",
    output_dir="./output"
):

    os.makedirs(output_dir, exist_ok=True)

    print("Loading Airbnb listings...")
    listings = pd.read_csv(
        listings_file,
        dtype={
            "id": str,
            "host_id": str,
            "location_id": str
        }
    )

    print("Loading rental bond data...")
    rental = pd.read_csv(
        rental_file,
        dtype={
            "location_id": str
        }
    )

    print("Preparing rental bond data...")

    rental_sa2 = rental[
        (rental["dwelling_type"] == "ALL")
        & (rental["number_of_beds"] == "ALL")
        & rental["median_rent"].notna()
    ].copy()

    rental_sa2["quarter"] = (
        rental_sa2["time_frame"].str[:4]
        + "-"
        + (
            (
                rental_sa2["time_frame"].str[5:7].astype(int) - 1
            ) // 3 * 3 + 1
        ).astype(str).str.zfill(2)
    )

    rental_sa2 = rental_sa2[
        ["location_id", "quarter", "median_rent"]
    ]

    rental_sa2 = rental_sa2.rename(
        columns={
            "median_rent": "median_weekly_rent"
        }
    )

    print("Converting Airbnb months to quarters...")

    listings["quarter"] = listings["month_year"].map(
        month_to_quarter
    )

    print("Joining Airbnb and rental bond data...")

    df = listings.merge(
        rental_sa2,
        on=["location_id", "quarter"],
        how="inner"
    )

    df = df[df["price"].notna()].copy()

    df["lt_nightly"] = df["median_weekly_rent"] / 7.0

    df["gap"] = (
        df["price"] - df["lt_nightly"]
    )

    df["ratio"] = (
        df["price"] / df["lt_nightly"]
    )

    print(
        f"Listings matched to bond data: "
        f"{len(df):,} listing-months, "
        f"{df['id'].nunique():,} unique listings, "
        f"{df['location_id'].nunique()} areas"
    )

    print(
        f"Median gap city-wide: "
        f"${df['gap'].median():.0f}/night "
        f"(median ratio: "
        f"{df['ratio'].median():.1f}x long-term)"
    )

    print("Calculating area-level summary...")

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
        .sort_values(
            "median_gap",
            ascending=False
        )
    )

    by_area["median_lt_nightly"] = (
        by_area["median_weekly_rent"] / 7.0
    )

    sa2_ward = (
        df.groupby("location_id")["neighbourhood"]
        .agg(lambda s: s.mode().iat[0])
    )

    by_area.insert(
        0,
        "ward",
        sa2_ward
    )

    by_area.to_csv(
        os.path.join(
            output_dir,
            "step7_gap_by_location.csv"
        )
    )

    reliable = by_area[
        by_area["n_listings"] >= 10
    ]

    top = reliable.head(15)

    print(
        "\nTop 15 areas (>=10 listings) by "
        "median short-term vs long-term gap ($/night):"
    )

    print(
        top[
            [
                "ward",
                "n_listings",
                "median_airbnb_price",
                "median_lt_nightly",
                "median_gap",
                "median_ratio"
            ]
        ]
        .round(1)
        .to_string()
    )

    print("Saving listing-level results...")

    df[
        [
            "id",
            "month_year",
            "quarter",
            "location_id",
            "neighbourhood",
            "room_type",
            "price",
            "median_weekly_rent",
            "lt_nightly",
            "gap",
            "ratio",
        ]
    ].to_csv(
        os.path.join(
            output_dir,
            "step7_gap_per_listing.csv"
        ),
        index=False
    )

    print("Creating area-level boxplot...")

    order = top.index.tolist()

    data = [
        df.loc[
            df["location_id"] == area,
            "gap"
        ].values
        for area in order
    ]

    labels = [
        f"{area}\n"
        f"{top.loc[area, 'ward'].replace(' Ward', '')}"
        for area in order
    ]

    fig, ax = plt.subplots(
        figsize=(12, 6)
    )

    ax.boxplot(
        data,
        tick_labels=labels,
        showfliers=False
    )

    ax.axhline(
        0,
        color="grey",
        lw=0.8
    )

    ax.set_ylabel(
        "AirBnB price - long-term nightly equivalent ($/night)"
    )

    ax.set_title(
        "Short-term vs long-term rental gap by area "
        "(top 15 by median gap)"
    )

    plt.xticks(
        rotation=45,
        ha="right",
        fontsize=8
    )

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            output_dir,
            "step7_gap_boxplot_by_location.png"
        ),
        dpi=150
    )

    plt.close()

    print("Creating ward-level boxplot...")

    wards = df.groupby(
        "neighbourhood"
    ).filter(
        lambda g: g["id"].nunique() >= 30
    )

    ward_order = (
        wards.groupby("neighbourhood")["gap"]
        .median()
        .sort_values(ascending=False)
        .index
    )

    fig, ax = plt.subplots(
        figsize=(12, 6)
    )

    ward_data = [
        wards.loc[
            wards["neighbourhood"] == ward,
            "gap"
        ].values
        for ward in ward_order
    ]

    ax.boxplot(
        ward_data,
        tick_labels=[
            ward.replace(" Ward", "")
            for ward in ward_order
        ],
        showfliers=False
    )

    ax.axhline(
        0,
        color="grey",
        lw=0.8
    )

    ax.set_ylabel(
        "AirBnB price - long-term nightly equivalent ($/night)"
    )

    ax.set_title(
        "Short-term vs long-term rental gap, "
        "pooled by ward"
    )

    plt.xticks(
        rotation=45,
        ha="right",
        fontsize=9
    )

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            output_dir,
            "step7_gap_boxplot_by_ward.png"
        ),
        dpi=150
    )

    plt.close()

    print(f"\nSaved outputs to {output_dir}")

    return {
        "listing_data": df,
        "area_summary": by_area,
        "ward_data": wards
    }