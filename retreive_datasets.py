import os
import subprocess
from datetime import date

DATA_DIR = "./data/listings"
os.makedirs(DATA_DIR, exist_ok=True)

# Known New Zealand release dates (from the "show archived data" table).
# Add/remove dates here as new releases come out or older ones get archived.
RELEASE_DATES = [
    date(2025, 10, 5),
    date(2025, 11, 7),
    date(2025, 12, 11),
    date(2026, 1, 16),
    date(2026, 2, 13),
    date(2026, 3, 17),
    date(2026, 4, 16),
    date(2026, 5, 23),
    date(2026, 6, 19),
]

URL_TEMPLATE = "https://data.insideairbnb.com/new-zealand/{date}/visualisations/listings.csv"

downloaded = 0
failed = 0

for release_date in RELEASE_DATES:
    date_str = release_date.strftime("%Y-%m-%d")

    url = URL_TEMPLATE.format(date=date_str)
    filename = f"new-zealand_{date_str}_listings.csv"
    filepath = os.path.join(DATA_DIR, filename)

    print(f"Downloading {date_str}...")
    result = subprocess.run(
        ["curl", "-fsSL", "-o", filepath, url],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"  ERROR downloading {date_str}")
        print(result.stderr)
        if os.path.exists(filepath):
            os.remove(filepath)
        failed += 1
    else:
        downloaded += 1
        print("  OK")

print("\n" + "=" * 70)
print("DOWNLOAD COMPLETE")
print("=" * 70)
print(f"Downloaded: {downloaded}")
print(f"Failed:     {failed}")
print(f"\nFiles saved under: {DATA_DIR}")