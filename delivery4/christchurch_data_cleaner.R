library(tidyverse)

listings <- read_csv("delivery4/data/christchurch_listings_v2.csv")

# remove license column
listings_clean <- listings %>%
  select(-license)

# replace empty strings with NA
listings_clean <- listings_clean %>%
  mutate(across(where(is.character), ~na_if(.x, "")))

# remove duplicates
duplicates <- sum(duplicated(listings_clean))

rows_before <- nrow(listings_clean)

listings_clean <- listings_clean %>%
  distinct()

rows_after <- nrow(listings_clean)

rows_removed <- rows_before - rows_after

write_csv(
  listings_clean,
  "delivery4/data/christchurch_listings_clean.csv"
)