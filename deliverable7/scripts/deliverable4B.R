clean_rental_bond_data <- function(
    input_file = "./data/Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv",
    output_file = "./output/cleaned_rental_bond_data.csv",
    start_date = as.Date("2025-10-01"),
    end_date = as.Date("2026-09-30")
) {

  raw <- read_csv(
    input_file,
    na = c("NULL"),
    col_types = cols(.default = col_character())
  )

  clean <- raw %>%
    clean_names()

  clean <- clean %>%
    mutate(
      time_frame             = as.Date(time_frame, format = "%Y-%m-%d"),
      total_bonds            = as.numeric(total_bonds),
      active_bonds           = as.numeric(active_bonds),
      closed_bonds           = as.numeric(closed_bonds),
      median_rent            = as.numeric(median_rent),
      geometric_mean_rent    = as.numeric(geometric_mean_rent),
      upper_quartile_rent    = as.numeric(upper_quartile_rent),
      lower_quartile_rent    = as.numeric(lower_quartile_rent),
      log_std_dev_weekly_rent = as.numeric(log_std_dev_weekly_rent)
    )

  clean <- clean %>%
    filter(
      time_frame >= start_date,
      time_frame <= end_date
    )

  clean <- clean %>%
    mutate(
      location_scope = case_when(
        location_id == "-99" ~ "National",
        is.na(location_id) ~ "Unclassified",
        TRUE ~ "Territorial Authority"
      )
    )

  clean <- clean %>%
    mutate(
      beds_category = if_else(
        number_of_beds == "NA",
        NA_character_,
        number_of_beds
      ),
      beds_numeric = suppressWarnings(as.numeric(number_of_beds))
    )

  message("Rental bond cleaning complete.")
  message("Rows after filtering: ", nrow(clean))
  message(
    "Date range: ",
    min(clean$time_frame, na.rm = TRUE),
    " to ",
    max(clean$time_frame, na.rm = TRUE)
  )

  write_csv(clean, output_file)

  return(clean)
}