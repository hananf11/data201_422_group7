#!/bin/bash
listing_url=https://data.insideairbnb.com/new-zealand/2026-06-19/data/listings.csv.gz
curl -o listings.csv.gz "$listing_url"
gunzip -f listings.csv.gz
