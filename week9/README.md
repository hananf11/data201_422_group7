# Week 9 — Steps 7 & 8: rental gap and supply comparison

Scripts (Python, run from repo root):

```
python week9/step7_rental_gap.py
python week9/step8_supply_comparison.py
```

Inputs live in `week9/data/` (gitignored): the Koordinates-queried listings file
(`christchurch_listings_clean_with_area.csv`), the cleaned rental bond data
(`cleaned_rental_bond_data.csv`), and the detailed June-2026 Inside Airbnb scrape
(`detailed/listings_detailed_2026-06-19.csv.gz`, used only for bedroom counts).

## Step 7 — short-term vs long-term price gap

For every listing-month, the long-term nightly equivalent is the SA2 + quarter
median weekly bond rent ÷ 7; the gap is the AirBnB nightly price minus that
value. City-wide the median gap is **$126/night (AirBnB is ~2.6× the long-term
nightly rate)**.

Among areas with ≥10 listings, the largest gaps are:

| location_id | Ward | listings | median gap $/night | AirBnB ÷ long-term |
|---|---|---|---|---|
| 322600 | Fendalton | 17 | 216 | 2.9× |
| 332700 | Heathcote | 76 | 199 | 3.3× |
| 322100 | Innes | 18 | 195 | 3.2× |
| 325700 | Central | 140 | 175 | 3.3× |

So the biggest short-term premium sits in the affluent western suburbs
(Fendalton / Innes) and the hill-side Heathcote area; a few tiny central SA2s
show even higher ratios (up to 6×) but on only 1–3 listings — see
`step7_gap_by_location.csv` (the `n_listings` filter flag is worth discussing).

Outputs: `step7_gap_by_location.csv`, `step7_gap_per_listing.csv`,
`step7_gap_boxplot_by_location.png` (top-15 boxplot), `step7_gap_boxplot_by_ward.png`
(distribution pooled into the larger AirBnB ward areas).

## Step 8 — AirBnB vs long-term rental supply per area

Per area & quarter we compare unique AirBnB listings (monthly average) with
active rental bonds. In 2026-Q2:

- Central-city SA2s have by far the highest AirBnB presence — up to
  **~350 AirBnB listings ≈ 26% of the combined rental stock** in the busiest
  central area, versus only **2–5%** in typical suburban areas.
- Bed comparison (extra ambitious): AirBnB bedrooms come from the detailed
  June-2026 scrape (matched to areas by 6-dp coordinates because the
  `with_area.csv` file corrupted 19-digit listing ids via float conversion);
  long-term beds = Σ active bonds × beds per bed-size category ("5+" = 5).
  In the most AirBnB-dense central areas **22–34% of all rental beds sit on
  AirBnB**, while suburbs are around 2–9%.

Outputs: `step8_counts_by_location.csv`, `step8_counts_barplot.png`,
`step8_beds_by_location.csv`, `step8_beds_barplot.png`.
