# Data Wrangling Group 7

Our group repo

Rules:

1. Be nice: Treat each other with respect.
2. Show up for class or let the group know.
3. Do your work: Don't be lazy, be cool instead :sunglasses:

Punishments:

1. One free pass
2. No more free passes, bring a snack to share with the group for your penance.

## Airbnb Data

This project looks at the [Airbnb Data](https://www.insideairbnb.com/get-the-data.html).

### Listings

Here are the details for ths listings.csv file.

| Field                          | Type     | Description                                                                                                                                                                                           |
| ------------------------------ | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| id                             | integer  | Unique identifier of the listing                                                                                                                                                                      |
| name                           | text     | Name of the listing                                                                                                                                                                                   |
| host_id                        | integer  | Unique identifier of the host                                                                                                                                                                         |
| host_name                      | text     | The name of the listing's host                                                                                                                                                                        |
| neighbourhood                  | text     | The neighbourhood of the listing                                                                                                                                                                      |
| neighbourhood_group            | text     | The neighbourhood group of the listing                                                                                                                                                                |
| latitude                       | numeric  | Uses the World Geodetic System (WGS84) projection for latitude and longitude.                                                                                                                         |
| longitude                      | numeric  | Uses the World Geodetic System (WGS84) projection for latitude and longitude.                                                                                                                         |
| room_type                      | text     | Rooms belong to a room group according to [this list](https://www.airbnb.com/help/article/5/what-does-the-room-type-of-a-listing-mean)                                                                |
| price                          | currency | "daily price in local currency. NOTE: the $ sign is a technical artifact of the export, please ignore it"                                                                                             |
| minimum_nights                 | integer  | minimum number of night stay for the listing (calendar rules may be different)                                                                                                                        |
| availability_365               | integer  | avaliability_x. The availability of the listing x days in the future as determined by the calendar. Note a listing may not be available because it has been booked by a guest or blocked by the host. |
| number_of_reviews              | integer  | The number of reviews the listing has                                                                                                                                                                 |
| number_of_reviews_ltm          | integer  | The number of reviews the listing has (in the last 12 months)                                                                                                                                         |
| last_review                    | date     | The date of the last/newest review                                                                                                                                                                    |
| license                        | text     | The licence/permit/registration number                                                                                                                                                                |
| calculated_host_listings_count | integer  | The number of listings the host has in the current scrape, in the city/region geography.                                                                                                              |
| reviews_per_month              | numeric  | The average number of reviews per month the listing has over the lifetime of the listing.                                                                                                             |


## Cleaning christchurch_listing dataset
- Column "license" was removed because its value in all row is the same("NA").
- Exact duplicate rows were checked and removed.
- Empty cell value was replaced with "NA" for easier reading and overall file consistency.

## Cleaning Rental Bond Data
- Filtered by TimeFrame to match the other dataset.
- NULL strings in place of real missing values → converted to NA on import.
- Location Id sentinel codes (-99, blank) are legitimate aggregate rows, not errors — retained, but flagged with a derived location_scope column.
- Number Of Beds mixes numeric codes, "ALL", "5+", and the literal string "NA" — the literal "NA" was not treated as missing on import (it is a distinct category in the source data), and a separate numeric column was added for rows where a true numeric bedroom count exists.
- Rent and dispersion columns were read in as character (due to quoting) and converted to numeric.

### Columns

| Column | Meaning |
|---|---|
| `TimeFrame` | The quarter summarised, based on tenancy start date (e.g. `2026-04-01` = Q2 2026). |
| `Location Id` | Geographic area code using the SA2-2019 classification (Statistics NZ). Special codes: `-99` = all of New Zealand (national total); blank/`NULL` = unclassified/unknown location. |
| `Dwelling Type` | Type of rental property: `ALL` (aggregate), `House`, `Apartment`, `Flat`, `Boarding House`, `Room`. |
| `Number Of Beds` | Bedroom count for the group: `ALL` (aggregate), `0`–`5`, or `5+` (5 or more, used when individual counts are suppressed for privacy). |
| `Total Bonds` | Number of new bonds lodged in that quarter for the group. |
| `Active Bonds` | Number of bonds that were active (in force) at some point during the quarter. |
| `Closed Bonds` | Number of bonds closed (tenancy ended) during the quarter. |
| `Median Rent` | Median weekly rent (NZD) for the group. |
| `Geometric Mean Rent` | Geometric mean of weekly rent (NZD). MBIE uses this instead of the median because rents cluster at round dollar values, which makes the plain median "plateau" for months at a time. |
| `Upper Quartile Rent` | Synthetic 75th-percentile weekly rent, modelled assuming a log-normal rent distribution (not a raw quartile of the observed values). |
| `Lower Quartile Rent` | Synthetic 25th-percentile weekly rent, calculated the same way. |
| `Log Std Dev Weekly Rent` | Standard deviation of the natural log of weekly rent — a measure of how spread out rents are within the group. |