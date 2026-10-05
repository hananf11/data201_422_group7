rental_csv <- read.csv("./cleaned_rental_bond_data.csv")
listings_csv <- read.csv("./christchurch_listings_clean_with_area.csv")

# merge on column rental_csv "time_frame", "location_id" listings_csv "month_year", "location_id"
date_to_quarter <- function(dates) {
    # dates like "YYYY-MM" or "YYYY-MM-DD"
    dates <- as.character(dates)
    year <- as.numeric(substr(dates, 1, 4))
    month <- as.numeric(substr(dates, 6, 7))
    quarter_start_month <- (ceiling(month / 3) - 1) * 3 + 1
    sprintf("%04d-%02d", year, quarter_start_month)
}

rental_csv$quarter <- date_to_quarter(rental_csv$time_frame)
listings_csv$quarter <- date_to_quarter(listings_csv$month_year)

# listings_csv$month_year <- sapply(listings_csv$time_frame, date_to_quarter)

# print(rental_csv[1:5,])
# print(listings_csv[1:5,])

# join on columns "quarter", "location_id"
merged_csv <- merge(rental_csv, listings_csv, by = c("quarter", "location_id"))

christchurch_central_id <- "326600"
merged_christchurch_data <- merged_csv %>%
  filter(location_id == christchurch_central_id)

# print(merged_christchurch_data$price[1:5])
median_christchurch_price <- median(merged_christchurch_data$price, na.rm = TRUE)
print(paste0("The median price of rentals in Christchurch Central is: $", median_christchurch_price))

# save merged data to output folder
dir.create("./output", showWarnings = FALSE, recursive = TRUE)
write.csv(merged_csv, "./output/merged_rental_and_listings_data.csv", row.names = FALSE)

