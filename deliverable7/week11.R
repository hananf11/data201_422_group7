# install.packages("reticulate")

library(dplyr)
library(readr)
library(janitor)
library(reticulate)


log_step <- function(message) {
  cat(
    "\n",
    format(Sys.time(), "%Y-%m-%d %H:%M:%S"),
    " | ",
    message,
    "\n",
    sep = ""
  )
}


log_step("Starting pipeline")


log_step("Loading Deliverable 3 script")
source("./scripts/deliverable3.R", encoding = "UTF-8")


log_step("Loading Deliverable 4A script")
source("./scripts/deliverable4A.R", encoding = "UTF-8")


log_step("Loading Deliverable 4B script")
source("./scripts/deliverable4B.R", encoding = "UTF-8")


log_step("Loading Deliverable 5B script")
source("./scripts/deliverable5B.R", encoding = "UTF-8")


log_step("Step 1: Combining Airbnb monthly data")
chch_all <- combine_airbnb_data()
log_step("Step 1 complete")


log_step("Step 2: Cleaning Airbnb data")
chch_clean <- clean_airbnb_data(
  input_file = "./output/christchurch_listings.csv",
  output_file = "./output/christchurch_listings_clean.csv"
)
log_step("Step 2 complete")


log_step("Step 3: Cleaning rental bond data")
rental_bond_clean <- clean_rental_bond_data(
  input_file = "./data/Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv",
  output_file = "./output/cleaned_rental_bond_data.csv",
  start_date = as.Date("2025-10-01"),
  end_date = as.Date("2026-09-30")
)
log_step("Step 3 complete")


log_step("Step 4: Setting up Python environment")

py_require(
  packages = c("requests", "pandas", "python-dotenv", "matplotlib")
)

if (!py_module_available("requests")) {
  stop("Python package 'requests' is not available.")
}

log_step("Python environment ready")


log_step("Step 5: Loading Koordinates location script")
source_python("./scripts/deliverable5A.py")
source_python("./scripts/deliverable5C.py")
source_python("./scripts/deliverable5D.py")


log_step("Step 6: Adding Stats NZ location IDs using Koordinates")
chch_with_location <- add_location_ids(
  input_file = "./output/christchurch_listings_clean.csv",
  output_file = "./output/christchurch_listings_clean_with_area.csv",
  max_workers = 10
)
log_step("Step 6 complete")


log_step("Step 7: Merging rental and Airbnb data")
merged_data <- merge_rental_airbnb_data(
  rental_file = "./output/cleaned_rental_bond_data.csv",
  listings_file = "./output/christchurch_listings_clean_with_area.csv",
  output_file = "./output/merged_rental_and_listings_data.csv",
  christchurch_central_id = "326600"
)
log_step("Step 7 complete")

log_step("Step 8 : Analyzing price gap and property counts")
price_gap_results <- analyze_price_gap(
  listings_file = "./output/christchurch_listings_clean_with_area.csv",
  rental_file = "./output/cleaned_rental_bond_data.csv",
  output_dir = "./output"
)
log_step("Step 8 complete")

log_step("Step 9 : Analyzing property counts")
price_count_results <- analyze_property_counts(
  listings_file = "./output/christchurch_listings_clean_with_area.csv",
  rental_file = "./output/cleaned_rental_bond_data.csv",
  detailed_file = "./data/listings_detailed_2026-06-19.csv.gz",
  output_dir = "./output",
  latest_quarter = "2026-04"
)
log_step("Step 9 complete")

log_step("Pipeline completed successfully")