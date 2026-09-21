files <- list.files("./data/listings", pattern = "*.csv", full.names = TRUE)

listings <- data.frame()

for (file in files) {
    file_basename <- basename(file)
    month_listings <- read.csv(file)

    year <- substr(file_basename, 1, 4)
    month <- substr(file_basename, 6, 7)

    month_listings['year'] <- year
    month_listings['month'] <- month

    listings <- rbind(listings, month_listings)
}

print("Loaded all files. Unique year / month combinations:")
print(unique(listings[c('year', 'month')]))

listings_christchurch <- listings[listings$neighbourhood_group == "Christchurch City",]

na_counts <- sapply(listings_christchurch, function(x) sum(is.na(x)))

na_counts <- data.frame(
  Column = names(na_counts),
  `Missing Values` = as.integer(na_counts),
  row.names = NULL
)

print(na_counts)

count_per_room_type <- table(listings_christchurch$room_type)

print(count_per_room_type)

# store the data in a csv file
write.csv(listings_christchurch, "./data/listings_christchurch.csv", row.names = FALSE)

print(hist(
  listings_christchurch$price, main = "Price Distribution in Christchurch", xlab = "Price", ylab = "Frequency", col = "blue", breaks = 100))
