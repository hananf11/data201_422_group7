# Week 11 / Deliverable 7 — one-command pipeline automation

The whole wrangling pipeline is now Python and runs end to end with **one
command** from anywhere:

```
bash week11/run_all.sh
```

No R is needed anymore; the former R scripts (`Load_All.r`,
`delivery4/christchurch_data_cleaner.R`, `delivery4/clean_rental_bond_data.R`,
`week9/main.R`) are kept in the repo as history but are superseded by the
Python ports in `week11/`.

## What gets automated

| Stage | Script | Input | Output |
|---|---|---|---|
| 1. Combine monthly listings | `week11/load_all.py` | `data/listings/*.csv` | `data/listings_christchurch.csv` + price histogram |
| 2. Place combined file | (sync copy) | stage 1 output | `delivery4/data/christchurch_listings_v2.csv`, `week9/data/…` |
| 3. Clean listings | `week11/clean_listings.py` | `delivery4/data/christchurch_listings_v2.csv` | `delivery4/output/christchurch_listings_clean.csv` |
| 4. Sync cleaned listings | (sync copy) | stage 3 output | `week9/data/christchurch_listings_clean.csv` |
| 5. Clean rental bond data | `week11/clean_rental_bond.py` | `delivery4/data/Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv` | `delivery4/output/cleaned_rental_bond_data.csv` |
| 6. Sync cleaned bond data | (sync copy) | stage 5 output | `week9/data/cleaned_rental_bond_data.csv` |
| 7. Geocode listings (SA2 areas) | `week9/main.py` (Koordinates API) | `week9/data/christchurch_listings_clean.csv` | `week9/data/christchurch_listings_clean_with_area.csv` |
| 8. Merge rentals + listings | `week11/merge_rental_listings.py` | stages 6 + 7 outputs | `week9/output/merged_rental_and_listings_data.csv` |
| 9. Price-gap analysis | `week9/step7_rental_gap.py` | stages 6 + 7 outputs | `week9/output/step7_*` (tables + boxplots) |
| 10. Supply comparison | `week9/step8_supply_comparison.py` | stages 6 + 7 outputs | `week9/output/step8_*` (tables + barplots) |

## Updating results when new months arrive

1. Put the new monthly files (e.g. `2026-07-12_listings.csv`,
   `2026-08-13_listings.csv`) into `data/listings/`.
2. Run `bash week11/run_all.sh`.

Every stage checks its inputs/outputs: a stage whose inputs did not change
since its outputs were written is **skipped**, so only the work that is
actually needed is redone — the new months flow through cleaning, geocoding,
merging, and all plots are regenerated.

## Requirements

- Python 3 with `pandas` and `matplotlib` (stages 1–6, 8–10).
- Stage 7 additionally needs `requests` + `python-dotenv` and a Koordinates
  API key in `week9/.env` (`KOORDINATES_API_KEY=...`). Without the key the
  stage is skipped and the existing `…_with_area.csv` is kept (a warning is
  printed), so the rest of the pipeline still runs.
- Raw inputs (`data/listings/`, `delivery4/data/`) are gitignored; on a fresh
  machine they must be obtained first (download step is out of scope here).

## Options

- `ALLOW_MISSING_INPUTS=1 bash week11/run_all.sh` — tolerate missing raw
  inputs (demo/partial machines) as long as downstream outputs exist.
- `PYTHON=/path/to/python bash week11/run_all.sh` — choose the interpreter.

## Fidelity of the Python ports

- Re-running the ported pipeline on the same inputs reproduces the published
  results: step 7 reports a city-wide median gap of **$126/night (2.6× the
  long-term nightly rate)** with the same top areas (Fendalton $216,
  Heathcote $199, Innes $195, Central $175), and step 8 reports the same
  AirBnB share of rental stock (26% in the busiest central area, 22–34% of
  beds).
- `week11/merge_rental_listings.py` also fixes a latent bug in `week9/main.R`,
  which used `%>%`/`filter()` without ever loading dplyr (it only ran inside
  an R session that had dplyr attached).
- `week9/main.py` now reads listing ids as strings (`dtype={"id": str}`) —
  previously 19-digit ids were float-converted and corrupted (e.g.
  `1.33e+18`), a known issue recorded in the week 9 README. Files already
  written with corrupted ids (the current `…_with_area.csv`) are unaffected
  retroactively; they will be correct the next time stage 7 runs with an API
  key.
