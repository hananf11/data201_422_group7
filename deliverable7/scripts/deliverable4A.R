clean_airbnb_data <- function(
    input_file = "./output/christchurch_listings.csv",
    output_file = "./output/christchurch_listings_clean.csv"
) {

  listings <- read_csv(input_file)

  listings_clean <- listings %>%
    select(-license, -host_name)

  listings_clean <- listings_clean %>%
    mutate(across(where(is.character), ~na_if(.x, "")))

  duplicates <- sum(duplicated(listings_clean))

  rows_before <- nrow(listings_clean)

  listings_clean <- listings_clean %>%
    distinct()

  rows_after <- nrow(listings_clean)

  rows_removed <- rows_before - rows_after

  message("Airbnb cleaning complete.")
  message("Rows before removing duplicates: ", rows_before)
  message("Rows after removing duplicates: ", rows_after)
  message("Rows removed: ", rows_removed)

  write_csv(listings_clean, output_file)

  return(listings_clean)
}