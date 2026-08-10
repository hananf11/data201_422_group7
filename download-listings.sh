#!/bin/bash
# This file was made with help from Composer 2.5 Fast.

set -euo pipefail

DATA_DIR="${1:-./data/listings}"
mkdir -p "$DATA_DIR"

mapfile -t listing_urls < <(
  curl -fsSL "https://insideairbnb.com/get-the-data/" |
    grep -oE 'https://data\.insideairbnb\.com/[^"]+/visualisations/listings\.csv' |
    tr -d '\r' |
    sort -u
)

for listing_url in "${listing_urls[@]}"; do
  slug=$(echo "$listing_url" | sed -E 's#https://data.insideairbnb.com/##; s#/visualisations/listings.csv##; s#[0-9]{4}-[0-9]{2}-[0-9]{2}$##; s#/$##; s#/#_#g')
  outfile="$DATA_DIR/${slug}_listings.csv"
  echo "Downloading $slug..."
  curl -fsSL -o "$outfile" "$listing_url"
done

echo "Downloaded ${#listing_urls[@]} listing files to $DATA_DIR"
