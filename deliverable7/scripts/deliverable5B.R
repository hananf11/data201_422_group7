library(dplyr)

merge_rental_airbnb_data <- function(
    rental_file = "./output/cleaned_rental_bond_data.csv",
    listings_file = "./output/christchurch_listings_clean_with_area.csv",
    output_file = "./output/merged_rental_and_listings_data.csv",
    christchurch_central_id = "326600"
) {

  rental_csv <- read.csv(rental_file)
  listings_csv <- read.csv(listings_file)

  date_to_quarter <- function(dates) {
    dates <- as.character(dates)

    year <- as.numeric(substr(dates, 1, 4))
    month <- as.numeric(substr(dates, 6, 7))

    quarter_start_month <- (ceiling(month / 3) - 1) * 3 + 1

    sprintf("%04d-%02d", year, quarter_start_month)
  }

  rental_csv$quarter <- date_to_quarter(
    rental_csv$time_frame
  )

  listings_csv$quarter <- date_to_quarter(
    listings_csv$month_year
  )

  merged_csv <- merge(
    rental_csv,
    listings_csv,
    by = c("quarter", "location_id")
  )

  merged_christchurch_data <- merged_csv %>%
    filter(location_id == christchurch_central_id)

  median_christchurch_price <- median(
    merged_christchurch_data$price,
    na.rm = TRUE
  )

  print(
    paste0(
      "The median price of rentals in Christchurch Central is: $",
      median_christchurch_price
    )
  )

  dir.create(
    dirname(output_file),
    showWarnings = FALSE,
    recursive = TRUE
  )

  write.csv(
    merged_csv,
    output_file,
    row.names = FALSE
  )

  message("Merged dataset saved to: ", output_file)

  return(merged_csv)
}