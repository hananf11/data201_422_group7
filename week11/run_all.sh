#!/bin/bash
# Deliverable 7 — one-command orchestration of the Christchurch rental data
# pipeline (all stages Python).
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

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
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
    local have="" f m oldest=""
    for f in "$@"; do
        [ -e "$f" ] || continue
        m=$(stat -c %Y "$f") || continue
        if [ -z "$oldest" ] || [ "$m" -lt "$oldest" ]; then oldest=$m; fi
        have=1
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

    # already up to date? (every output exists and is newer than every input)
    local out_min in_max
    out_min=$(oldest_output_mtime "${outputs[@]}")
    in_max=$(newest_mtime "${inputs[@]}")
    for f in "${outputs[@]}"; do [ -e "$f" ] || all_out=0; done
    # ">=" (not ">") because cp -p preserves source mtimes: an exact copy of
    # its input has the same timestamp and must not be rebuilt forever.
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

api_key_available() {
    [ -n "${KOORDINATES_API_KEY:-}" ] || [ -f week9/.env ]
}

command -v "$PYTHON" >/dev/null 2>&1 || { err "python interpreter '$PYTHON' not found"; exit 1; }

log "Pipeline root: $ROOT"

# ---- Stage 1: combine monthly listings -> Christchurch dataset -----------
run_stage "1_load_listings" \
    data/listings/*.csv \
    --out data/listings_christchurch.csv data/listings_christchurch_price_hist.png \
    -- "$PYTHON" week11/load_all.py

# ---- Stage 2: place combined file where the cleaning stage expects it ----
run_stage "2_sync_combined" \
    data/listings_christchurch.csv \
    --out delivery4/data/christchurch_listings_v2.csv week9/data/christchurch_listings_v2.csv \
    -- bash -c 'mkdir -p delivery4/data week9/data
                cp -p data/listings_christchurch.csv delivery4/data/christchurch_listings_v2.csv
                cp -p data/listings_christchurch.csv week9/data/christchurch_listings_v2.csv'

# ---- Stage 3: clean the listings -----------------------------------------
run_stage "3_clean_listings" \
    delivery4/data/christchurch_listings_v2.csv \
    --out delivery4/output/christchurch_listings_clean.csv \
    -- "$PYTHON" week11/clean_listings.py

# ---- Stage 4: copy cleaned listings into week9/data ----------------------
run_stage "4_sync_clean" \
    delivery4/output/christchurch_listings_clean.csv \
    --out week9/data/christchurch_listings_clean.csv \
    -- bash -c 'mkdir -p week9/data
                cp -p delivery4/output/christchurch_listings_clean.csv week9/data/christchurch_listings_clean.csv'

# ---- Stage 5: clean the rental bond data ---------------------------------
run_stage "5_clean_bond" \
    delivery4/data/Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv \
    --out delivery4/output/cleaned_rental_bond_data.csv \
    -- "$PYTHON" week11/clean_rental_bond.py

# ---- Stage 6: copy cleaned bond data into week9/data ---------------------
run_stage "6_sync_bond" \
    delivery4/output/cleaned_rental_bond_data.csv \
    --out week9/data/cleaned_rental_bond_data.csv \
    -- bash -c 'mkdir -p week9/data
                cp -p delivery4/output/cleaned_rental_bond_data.csv week9/data/cleaned_rental_bond_data.csv'

# ---- Stage 7: geocode listings via the Koordinates API -------------------
# Only new/changed listings trigger API calls; the stage is skipped when the
# API key is unavailable and a previous output already exists.
if api_key_available; then
    run_stage "7_geocode_areas" \
        week9/data/christchurch_listings_clean.csv \
        --out week9/data/christchurch_listings_clean_with_area.csv \
        -- bash -c 'cd week9/data && "$0" main.py' "$PYTHON"
else
    if [ -e week9/data/christchurch_listings_clean_with_area.csv ]; then
        warn "7_geocode_areas: KOORDINATES_API_KEY not set — keeping existing with_area output (add week9/.env to refresh)"
    else
        err "7_geocode_areas: no API key (week9/.env) and no previous output"
        FAILED=1
    fi
fi

# ---- Stage 8: merge rentals with listings --------------------------------
run_stage "8_merge" \
    week9/data/cleaned_rental_bond_data.csv week9/data/christchurch_listings_clean_with_area.csv \
    --out week9/output/merged_rental_and_listings_data.csv \
    -- "$PYTHON" week11/merge_rental_listings.py

# ---- Stage 9: analysis — short vs long-term price gap --------------------
run_stage "9_step7_gap" \
    week9/data/christchurch_listings_clean_with_area.csv week9/data/cleaned_rental_bond_data.csv \
    --out week9/output/step7_gap_by_location.csv week9/output/step7_gap_per_listing.csv \
          week9/output/step7_gap_boxplot_by_location.png week9/output/step7_gap_boxplot_by_ward.png \
    -- "$PYTHON" week9/step7_rental_gap.py

# ---- Stage 10: analysis — AirBnB vs long-term supply ---------------------
run_stage "10_step8_supply" \
    week9/data/christchurch_listings_clean_with_area.csv week9/data/cleaned_rental_bond_data.csv \
    week9/data/detailed/listings_detailed_2026-06-19.csv.gz \
    --out week9/output/step8_counts_by_location.csv week9/output/step8_beds_by_location.csv \
          week9/output/step8_counts_barplot.png week9/output/step8_beds_barplot.png \
    -- "$PYTHON" week9/step8_supply_comparison.py

echo ""
if [ "$FAILED" -eq 0 ]; then
    ok "Pipeline finished (stages whose outputs were already current were skipped)."
else
    err "Pipeline finished WITH ERRORS — see [FAIL] lines above."
fi
exit "$FAILED"
