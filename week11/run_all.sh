#!/bin/bash
# Deliverable 7 — one-command pipeline: run every stage, in order.
#
# Usage:
#   bash week11/run_all.sh        (works from any directory)
#
# Stage 5 (geocoding) needs a Koordinates API key in week11/.env
# (KOORDINATES_API_KEY=...). Without it the stage is skipped with a warning
# and the existing data/christchurch_listings_clean_with_area.csv is kept,
# so the rest of the pipeline still runs.
set -e
cd "$(dirname "${BASH_SOURCE[0]}")"
PYTHON="${PYTHON:-python}"

echo "[1/8] combine monthly listings"
"$PYTHON" load_all.py
cp data/listings_christchurch.csv data/christchurch_listings_v2.csv

echo "[3/8] clean the listings"
"$PYTHON" clean_listings.py

echo "[4/8] clean the rental bond data"
"$PYTHON" clean_rental_bond.py

echo "[5/8] geocode listings via the Koordinates API"
if [ -n "${KOORDINATES_API_KEY:-}" ] || [ -f .env ]; then
    "$PYTHON" main.py
else
    echo "  WARN: KOORDINATES_API_KEY not set - keeping existing" \
         "data/christchurch_listings_clean_with_area.csv (add week11/.env to refresh)"
fi

echo "[6/8] merge rentals with listings"
"$PYTHON" merge_rental_listings.py

echo "[7/8] step 7: short vs long-term price gap"
"$PYTHON" step7_rental_gap.py

echo "[8/8] step 8: AirBnB vs long-term rental supply"
"$PYTHON" step8_supply_comparison.py

echo "Pipeline finished. Outputs are in week11/output/."
