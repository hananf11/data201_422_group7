#!/bin/bash
# Deliverable 7 — one-command orchestration of the Christchurch rental data
# pipeline (all stages Python).
#
# The whole pipeline runs INSIDE the week11/ directory: data lives in
# week11/data/, outputs in week11/output/. This script may be invoked from
# any directory; it changes into its own location first.
#
# Usage:
#   bash week11/run_all.sh
#
# Optional environment:
#   ALLOW_MISSING_INPUTS=1   tolerate stages whose inputs are absent (demo /
#                            partial machines) instead of failing the run
#   PYTHON=/path/to/python   python interpreter to use (default: python)
#
# Each stage is skipped when its outputs are already newer than its inputs,
# so re-running the whole pipeline after new months arrive only redoes the
# work that is actually needed.
set -uo pipefail

WEEK11="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$WEEK11"
PYTHON="${PYTHON:-python}"

log()  { printf '\033[1;34m[run_all]\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m[  ok  ]\033[0m %s\n' "$*"; }
skip() { printf '\033[1;33m[ skip ]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[ WARN ]\033[0m %s\n' "$*"; }
err()  { printf '\033[1;31m[ FAIL ]\033[0m %s\n' "$*"; }

FAILED=0

newest_mtime() {  # newest mtime among the given files (0 if none exist)
    local t=0 f m
    for f in "$@"; do
        [ -e "$f" ] || continue
        m=$(stat -c %Y "$f") || continue
        [ "$m" -gt "$t" ] && t=$m
    done
    echo "$t"
}

oldest_output_mtime() {  # oldest mtime among existing outputs (empty if none)
    local f m oldest=""
    for f in "$@"; do
        [ -e "$f" ] || continue
        m=$(stat -c %Y "$f") || continue
        if [ -z "$oldest" ] || [ "$m" -lt "$oldest" ]; then oldest=$m; fi
    done
    echo "$oldest"
}

# run_stage NAME in... [--out out...] -- command...
run_stage() {
    local name="$1"; shift
    local -a inputs=() outputs=() cmd=()
    local mode=in
    while [ $# -gt 0 ]; do
        case "$1" in
            --out) mode=out ;;
            --)    mode=cmd ;;
            *)  case "$mode" in
                    in)  inputs+=("$1") ;;
                    out) outputs+=("$1") ;;
                    cmd) cmd+=("$1") ;;
                esac ;;
        esac
        shift
    done

    log "Stage: $name"

    local f missing_in=0 any_out=0 all_out=1
    for f in "${inputs[@]}"; do
        if [ ! -e "$f" ]; then
            if [ "${ALLOW_MISSING_INPUTS:-0}" = "1" ]; then
                warn "$name: missing input $f"
            else
                err "$name: missing input $f"
            fi
            missing_in=1
        fi
    done
    if [ "$missing_in" -eq 1 ]; then
        for f in "${outputs[@]}"; do [ -e "$f" ] && any_out=1; done
        if [ "${ALLOW_MISSING_INPUTS:-0}" = "1" ] || [ "$any_out" -eq 1 ]; then
            skip "$name: inputs missing${any_out:+ (keeping existing outputs)}"
            return 0
        fi
        err "$name: cannot proceed — run stopped"
        FAILED=1
        return 1
    fi

    # already up to date? (every output exists and is at least as new as every
    # input; ">=" because an exact copy of its input must not be rebuilt)
    local out_min in_max
    out_min=$(oldest_output_mtime "${outputs[@]}")
    in_max=$(newest_mtime "${inputs[@]}")
    for f in "${outputs[@]}"; do [ -e "$f" ] || all_out=0; done
    if [ "$all_out" -eq 1 ] && [ -n "$out_min" ] && [ "$out_min" -ge "$in_max" ]; then
        skip "$name: outputs up to date"
        return 0
    fi

    if "${cmd[@]}"; then
        for f in "${outputs[@]}"; do
            if [ ! -e "$f" ]; then
                err "$name: command succeeded but output $f was not produced"
                FAILED=1
                return 1
            fi
        done
        ok "$name"
    else
        err "$name: command failed"
        FAILED=1
        return 1
    fi
}

command -v "$PYTHON" >/dev/null 2>&1 || { err "python interpreter '$PYTHON' not found"; exit 1; }

log "Pipeline directory: $WEEK11"

# ---- Stage 1: combine monthly listings -> Christchurch dataset -----------
run_stage "1_load_listings" \
    data/listings/*.csv \
    --out data/listings_christchurch.csv output/listings_christchurch_price_hist.png \
    -- "$PYTHON" load_all.py

# ---- Stage 2: publish combined file under its canonical name -------------
run_stage "2_sync_combined" \
    data/listings_christchurch.csv \
    --out data/christchurch_listings_v2.csv \
    -- bash -c 'cp -p data/listings_christchurch.csv data/christchurch_listings_v2.csv'

# ---- Stage 3: clean the listings -----------------------------------------
run_stage "3_clean_listings" \
    data/christchurch_listings_v2.csv \
    --out data/christchurch_listings_clean.csv \
    -- "$PYTHON" clean_listings.py

# ---- Stage 4: clean the rental bond data ---------------------------------
run_stage "4_clean_bond" \
    data/Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv \
    --out data/cleaned_rental_bond_data.csv \
    -- "$PYTHON" clean_rental_bond.py

# ---- Stage 5: geocode listings via the Koordinates API -------------------
# Only listings not yet geocoded need API calls; the stage is skipped when
# the API key is unavailable and a previous output already exists.
if [ -n "${KOORDINATES_API_KEY:-}" ] || [ -f .env ]; then
    run_stage "5_geocode_areas" \
        data/christchurch_listings_clean.csv \
        --out data/christchurch_listings_clean_with_area.csv \
        -- "$PYTHON" main.py
else
    if [ -e data/christchurch_listings_clean_with_area.csv ]; then
        warn "5_geocode_areas: KOORDINATES_API_KEY not set — keeping existing with_area output (add week11/.env to refresh)"
    else
        err "5_geocode_areas: no API key (.env) and no previous output"
        FAILED=1
    fi
fi

# ---- Stage 6: merge rentals with listings --------------------------------
run_stage "6_merge" \
    data/cleaned_rental_bond_data.csv data/christchurch_listings_clean_with_area.csv \
    --out output/merged_rental_and_listings_data.csv \
    -- "$PYTHON" merge_rental_listings.py

# ---- Stage 7: analysis — short vs long-term price gap --------------------
run_stage "7_step7_gap" \
    data/christchurch_listings_clean_with_area.csv data/cleaned_rental_bond_data.csv \
    --out output/step7_gap_by_location.csv output/step7_gap_per_listing.csv \
          output/step7_gap_boxplot_by_location.png output/step7_gap_boxplot_by_ward.png \
    -- "$PYTHON" step7_rental_gap.py

# ---- Stage 8: analysis — AirBnB vs long-term supply ----------------------
run_stage "8_step8_supply" \
    data/christchurch_listings_clean_with_area.csv data/cleaned_rental_bond_data.csv \
    data/detailed/listings_detailed_2026-06-19.csv.gz \
    --out output/step8_counts_by_location.csv output/step8_beds_by_location.csv \
          output/step8_counts_barplot.png output/step8_beds_barplot.png \
    -- "$PYTHON" step8_supply_comparison.py

echo ""
if [ "$FAILED" -eq 0 ]; then
    ok "Pipeline finished (stages whose outputs were already current were skipped)."
else
    err "Pipeline finished WITH ERRORS — see [FAIL] lines above."
fi
exit "$FAILED"
