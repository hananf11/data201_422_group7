#!/bin/bash
# This file was made with help from Composer 2.5 Fast.

set -euo pipefail

DATA_DIR="${1:-./data/listings}"
mkdir -p "$DATA_DIR"

urls=(
  "https://data.insideairbnb.com/new-zealand/2026-06-19/visualisations/listings.csv"
  "https://data.insideairbnb.com/new-zealand/2026-05-23/visualisations/listings.csv"
  "https://data.insideairbnb.com/new-zealand/2026-04-16/visualisations/listings.csv"
  "https://data.insideairbnb.com/new-zealand/2026-03-17/visualisations/listings.csv"
  "https://data.insideairbnb.com/new-zealand/2026-02-13/visualisations/listings.csv"
  "https://data.insideairbnb.com/new-zealand/2026-01-16/visualisations/listings.csv"
  "https://data.insideairbnb.com/new-zealand/2025-12-11/visualisations/listings.csv"
  "https://data.insideairbnb.com/new-zealand/2025-11-07/visualisations/listings.csv"
  "https://data.insideairbnb.com/new-zealand/2025-10-05/visualisations/listings.csv"
)

for url in "${urls[@]}"; do
  # take out the date from the url
  date=$(echo "$url" | sed -E 's#https://data.insideairbnb.com/new-zealand/##; s#/visualisations/listings.csv##')
  outfile="$DATA_DIR/${date}_listings.csv"
  echo "Downloading $date..."
  curl -fsSL -o "$outfile" "$url" && echo "Downloaded $date"
done

echo "Downloaded ${#urls[@]} listing files to $DATA_DIR"