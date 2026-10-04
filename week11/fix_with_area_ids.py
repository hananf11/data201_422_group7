"""
One-off repair: fix the listing ids in christchurch_listings_clean_with_area.csv.

The old week9/main.py read the clean listings without dtype=str, so the id and
host_id columns were float-converted and 19-digit ids lost precision
(scientific notation like "1.33e+18"). The corruption only affects those two
columns: the API results (location_id) and the coordinates are intact, and
main.py wrote its output in the same row order as its input.

This script therefore re-attaches the correct string ids positionally from a
row-aligned copy of christchurch_listings_clean.csv — no API calls needed —
after verifying the two files really are row-for-row the same data.

Usage:
    python fix_with_area_ids.py [path/to/christchurch_listings_clean.csv]

By default the clean file inside week11/data/ is used; pass the full-history
copy explicitly if the week11 one has already been regenerated from a partial
set of months (e.g. only the new July/August files).
"""

import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
WITH_AREA = os.path.join(HERE, "data", "christchurch_listings_clean_with_area.csv")

ID_COLUMNS = ["id", "host_id"]
# columns present in both files, used to verify the rows line up positionally
CHECK_COLUMNS = [
    "name", "neighbourhood_group", "neighbourhood", "room_type", "price",
    "minimum_nights", "number_of_reviews", "last_review", "month_year",
    "availability_365",
]


def main():
    clean_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        HERE, "data", "christchurch_listings_clean.csv")
    print(f"Repairing {WITH_AREA}")
    print(f"Using id source: {clean_path}")
    clean = pd.read_csv(clean_path, dtype={c: str for c in ID_COLUMNS})
    with_area = pd.read_csv(WITH_AREA, dtype={c: str for c in ID_COLUMNS})

    if len(clean) != len(with_area):
        raise SystemExit(
            f"ABORT: row counts differ (clean={len(clean)}, "
            f"with_area={len(with_area)}) — files are not row-aligned."
        )

    # sanity check: the shared columns must match row by row
    for col in CHECK_COLUMNS:
        if col not in clean.columns or col not in with_area.columns:
            raise SystemExit(f"ABORT: column {col} missing — layout changed?")
        a, b = clean[col], with_area[col]
        if a.dtype.kind == "f" or b.dtype.kind == "f":
            same = np.isclose(
                pd.to_numeric(a, errors="coerce"),
                pd.to_numeric(b, errors="coerce"),
                rtol=0, atol=1e-9, equal_nan=True,
            )
        else:
            # normalise CRLF/CR inside quoted fields (R vs pandas line endings)
            a = a.astype(str).str.replace("\r\n", "\n", regex=False).str.replace("\r", "\n", regex=False)
            b = b.astype(str).str.replace("\r\n", "\n", regex=False).str.replace("\r", "\n", regex=False)
            same = (a == b) | (a.isna() & b.isna())
        if not same.all():
            bad = int((~same).sum())
            raise SystemExit(
                f"ABORT: column {col} differs in {bad} row(s) — "
                "with_area was not written from this clean file."
            )
    print(f"Row-for-row check passed on {len(CHECK_COLUMNS)} columns, "
          f"{len(clean)} rows.")

    corrupted = with_area["id"].str.contains(r"e\+|\.0$", regex=True, na=False)
    print(f"Corrupted ids before repair: {int(corrupted.sum())}")

    with_area[ID_COLUMNS] = clean[ID_COLUMNS]
    with_area.to_csv(WITH_AREA, index=False)
    print(f"Repaired ids written to {WITH_AREA}")

    check = pd.read_csv(WITH_AREA, dtype={"id": str, "host_id": str})
    still_bad = check["id"].str.contains(r"e\+|\.0$", regex=True, na=False)
    print(f"Corrupted ids after repair: {int(still_bad.sum())}")
    print(f"Unique listing ids now: {check['id'].nunique()}")


if __name__ == "__main__":
    main()
