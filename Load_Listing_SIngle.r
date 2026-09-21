target_csv <- "./data/listings/2026-06-19_listings.csv"

listings <- read.csv(target_csv)

listings['month'] = '06'
listings['year'] = '2026'

christchuch_neighbourhood_group = "Christchurch City"

# print(unique(listings['neighbourhood_group']))
christchurch_listings <- listings[listings$neighbourhood_group == christchuch_neighbourhood_group,]

head(christchurch_listings)