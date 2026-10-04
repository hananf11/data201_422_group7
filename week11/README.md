# Week 11 / Deliverable 7 — one-command pipeline automation

The whole wrangling pipeline is Python and **self-contained inside
`week11/`**: scripts, data (`week11/data/`) and outputs (`week11/output/`)
all live here, and everything runs with **one command** from anywhere:

```
bash week11/run_all.sh
```

No R is needed anymore; the former R scripts (`Load_All.r`,
`delivery4/christchurch_data_cleaner.R`, `delivery4/clean_rental_bond_data.R`,
`week9/main.R`) are kept in the repo as history but are superseded by the
Python ports in `week11/`. The week 9 analysis scripts (`main.py`,
`step7_rental_gap.py`, `step8_supply_comparison.py`) have moved from `week9/`
into `week11/` so the pipeline can run entirely in this directory.

## Layout

```
week11/
├── run_all.sh                    one-command orchestrator
├── load_all.py                   stage 1: combine monthly listings
├── clean_listings.py             stage 3: clean the listings
├── clean_rental_bond.py          stage 4: clean the rental bond data
├── main.py                       stage 5: geocode via Koordinates API
├── merge_rental_listings.py      stage 6: merge rentals + listings
├── step7_rental_gap.py           stage 7: price-gap analysis
├── step8_supply_comparison.py    stage 8: supply comparison
├── data/                         inputs + intermediates (gitignored)
│   ├── listings/                 raw monthly listings.csv downloads
│   ├── detailed/                 detailed scrape (bed counts)
│   └── *.csv                     combined/cleaned/geocoded datasets
└── output/                       final outputs: merged CSV, plots (gitignored)
```

## Stages

| Stage | Script | Input | Output |
|---|---|---|---|
| 1. Combine monthly listings | `load_all.py` | `data/listings/*.csv` | `data/listings_christchurch.csv` + price histogram |
| 2. Publish combined file | (sync copy) | stage 1 output | `data/christchurch_listings_v2.csv` |
| 3. Clean listings | `clean_listings.py` | `data/christchurch_listings_v2.csv` | `data/christchurch_listings_clean.csv` |
| 4. Clean rental bond data | `clean_rental_bond.py` | `data/Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv` | `data/cleaned_rental_bond_data.csv` |
| 5. Geocode listings (SA2 areas) | `main.py` (Koordinates API) | `data/christchurch_listings_clean.csv` | `data/christchurch_listings_clean_with_area.csv` |
| 6. Merge rentals + listings | `merge_rental_listings.py` | stages 4 + 5 outputs | `output/merged_rental_and_listings_data.csv` |
| 7. Price-gap analysis | `step7_rental_gap.py` | stages 4 + 5 outputs | `output/step7_*` (tables + boxplots) |
| 8. Supply comparison | `step8_supply_comparison.py` | stages 4 + 5 outputs | `output/step8_*` (tables + barplots) |

## Updating results when new months arrive

1. Put the new monthly files (e.g. `2026-07-12_listings.csv`,
   `2026-08-13_listings.csv`) into `week11/data/listings/` — use the
   zero-padded official file names (`YYYY-MM-DD_listings.csv`).
2. Run `bash week11/run_all.sh`.

Every stage checks its inputs/outputs: a stage whose inputs did not change
since its outputs were written is **skipped**, so only the work that is
actually needed is redone — the new months flow through cleaning, geocoding,
merging, and all plots are regenerated.

## Requirements

- Python 3 with `pandas` and `matplotlib` (stages 1–4, 6–8), run from any
  directory — the orchestrator changes into `week11/` itself.
- Stage 5 additionally needs `requests` + `python-dotenv` and a Koordinates
  API key in `week11/.env` (`KOORDINATES_API_KEY=...`). Without the key the
  stage is skipped and the existing `…_with_area.csv` is kept (a warning is
  printed), so the rest of the pipeline still runs.
- Raw inputs (`data/listings/`, `data/Detailed-…csv`, `data/detailed/`) are
  gitignored; on a fresh machine they must be obtained first (the download
  step is out of scope here).

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
- `merge_rental_listings.py` also fixes a latent bug in `week9/main.R`, which
  used `%>%`/`filter()` without ever loading dplyr (it only ran inside an R
  session that had dplyr attached).
- `main.py` reads listing ids as strings (`dtype={"id": str}`) — previously
  19-digit ids were float-converted and corrupted (e.g. `1.33e+18`), a known
  issue recorded in the week 9 README. Files already written with corrupted
  ids are unaffected retroactively; they will be correct the next time
  stage 5 runs with an API key.
