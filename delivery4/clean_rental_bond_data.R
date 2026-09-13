#install.packages("dplyr")
#install.packages("readr")
#install.packages("janitor")
library(dplyr)
library(readr)
library(janitor)

start_date <- as.Date("2025-01-01")
end_date   <- as.Date("2026-09-30")

raw <- read_csv("delivery4/data/Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv", na = c("NULL"), col_types = cols(.default = col_character()))


# clean headers and convert to appropriate data types
clean <- raw %>% clean_names()

clean <- clean %>%
  mutate(
    time_frame              = as.Date(time_frame, format = "%Y-%m-%d"),
    total_bonds              = as.numeric(total_bonds),
    active_bonds             = as.numeric(active_bonds),
    closed_bonds             = as.numeric(closed_bonds),
    median_rent              = as.numeric(median_rent),
    geometric_mean_rent      = as.numeric(geometric_mean_rent),
    upper_quartile_rent      = as.numeric(upper_quartile_rent),
    lower_quartile_rent      = as.numeric(lower_quartile_rent),
    log_std_dev_weekly_rent  = as.numeric(log_std_dev_weekly_rent)
  )

# filtered to the time frame of interest
clean <- clean %>% filter(time_frame >= start_date, time_frame <= end_date)

# add a new column to classify the location scope based on the location_id
clean <- clean %>%
  mutate(
    location_scope = case_when(
      location_id == "-99" ~ "National",
      is.na(location_id)   ~ "Unclassified",
      TRUE                 ~ "Territorial Authority"
    )
  )

# add new columns to categorize the number of beds and convert to numeric
clean <- clean %>%
  mutate(
    beds_category = if_else(number_of_beds == "NA", NA_character_, number_of_beds),
    beds_numeric  = suppressWarnings(as.numeric(number_of_beds))
  )
  
# view data structure and summary statistics
#glimpse(clean)
#summary(clean$median_rent)
#count(clean, dwelling_type)
#count(clean, beds_category)
#count(clean, location_scope)
#range(clean$time_frame)

write_csv(clean, "delivery4/data/cleaned_rental_bond_data.csv")