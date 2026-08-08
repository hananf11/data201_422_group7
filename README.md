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
