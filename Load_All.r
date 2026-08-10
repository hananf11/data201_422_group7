files = list.files("./data/listings", pattern = "*.csv", full.names = TRUE)

listings <- data.frame()

for (file in files) {
    file_basename = basename(file)
    month_listings <- read.csv(file)

    year <- substr(file_basename, 1, 4)
    month <- substr(file_basename, 6, 7)

    month_listings['year'] = year
    month_listings['month'] = month

    listings <- rbind(listings, month_listings)
}

print("Loaded all files. Unique year / month combinations:")
print(unique(listings[c('year', 'month')]))

print(colnames(listings))