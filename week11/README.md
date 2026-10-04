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
├── fix_with_area_ids.py          one-off repair of corrupted listing ids
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

The orchestrator simply runs every stage in order (`set -e`, so the first
failure stops the run), and the new months flow through cleaning, geocoding,
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
  issue recorded in the week 9 README.
- The already-written `christchurch_listings_clean_with_area.csv` was repaired
  with `week11/fix_with_area_ids.py`: since the old geocoding step wrote its
  output in the same row order as its input, the correct string ids were
  re-attached positionally from `christchurch_listings_v2.csv` (whose ids were
  never corrupted) after a row-for-row verification — no API calls needed.
  With the ids fixed, step 8's bed comparison matches the detailed scrape by
  listing id again instead of the 6-dp coordinate workaround (3,469 vs 3,468
  matched listings — the two methods agree).

## Development history (commit iteration)

How the Deliverable 7 pipeline evolved, commit by commit:

| Commit | What changed | Why |
|---|---|---|
| (week 9 baseline: `caf443f`, `c6a2eb9`) | Week 9 scripts: `main.py` (Koordinates geocoding), `main.R` (merge), `step7/step8` analyses and plots | the analyses the pipeline now automates |
| `e195659` 2026-10-04 | Rewrote the four R scripts as Python (`load_all.py`, `clean_listings.py`, `clean_rental_bond.py`, `merge_rental_listings.py`) | unify the whole pipeline to one language; the ports reproduce the published step 7/8 results on the same inputs. Also surfaced that `main.R` used `%>%` without loading dplyr and only ran inside an R session |
| `96989c9` 2026-10-04 | Added `run_all.sh` (orchestrator with per-stage input/output checks and skip-when-up-to-date logic) + this README | the assignment's "one command" requirement; skipping avoids re-running the ~35k-call geocoding stage when nothing changed |
| `ce42fcd` 2026-10-04 | Fixed `main.py` to read listing ids as strings; gitignored `week9/data/`; regenerated the step 8 output | 19-digit ids had been float-corrupted (a known week 9 issue); the detailed scrape `.gz` was not ignored |
| `c14b472` 2026-10-05 | Made the pipeline self-contained inside `week11/`: moved `main.py`/`step7/step8` and all data here, 10 stages → 8 (cross-directory sync copies removed) | one directory holds the whole deliverable; runs identically from anywhere |
| `766df1c` 2026-10-05 | Repaired the corrupted ids in `christchurch_listings_clean_with_area.csv` (`fix_with_area_ids.py`, positional repair from `christchurch_listings_v2.csv`, no API calls); step 8's bed comparison simplified back to matching by listing id (3,469 vs 3,468 matched); `run_all.sh` reduced to plain sequential execution | with correct ids the coordinate workaround was unnecessary; after weighing the options the orchestrator was deliberately kept "dumb" (run every stage in order, `set -e`) — an intermediate version with mtime/fingerprint skip logic worked but was more complex than the team wanted to maintain |
| `1695409` 2026-10-05 | Incremental geocoding in `main.py`: the with_area output is now a cache — rows with an already-geocoded id reuse their area, only unknown ids call the API (once per id, deduplicated across months) | a listing's coordinates never change so its area never changes; with all 13 months in the pipeline (41,614 listing-month rows) a full refresh needs **277 calls instead of 41,614** (~150×); missing key / missing `requests`+`python-dotenv` now exit with clear messages, and both imports are lazy so the stage still runs when nothing is new |

Lessons recorded along the way:

- The historical raw monthly files and the pre-repair `v2`/`clean` CSVs were
  recovered from a group backup after a partial re-run overwrote them — keep
  `week11/data/listings/` complete; it is the only source of truth.
- Two data bugs were found and fixed during the unification: 19-digit listing
  ids corrupted by float conversion (fixed in `main.py`, repaired in the
  existing output), and `main.R` running without dplyr (fixed in the Python
  port).
- Incremental caching is in place (`1695409`): `main.py` geocodes only the
  277 ids not yet in the with_area output, so the one command stays cheap
  even though the orchestrator itself runs every stage in order.
