
data_dir <- "week5/origin_data"                
out_file <- "christchurch_listings.csv"   
sum_file <- "summary_statistics.csv"                       

# Months required 
required_months <- c("October, 2025",  "November, 2025", "December, 2025",
                     "January, 2026",  "February, 2026", "March, 2026",
                     "April, 2026",    "May, 2026",      "June, 2026")

# Map month name
month_num <- c(January = 1, February = 2, March = 3, April = 4, May = 5, June = 6,
               July = 7, August = 8, September = 9, October = 10, November = 11,
               December = 12)


all_files <- list.files(data_dir, pattern = "\\.csv$", full.names = TRUE)
if (length(all_files) == 0) stop("No CSV files found in: ", data_dir)

keep <- vapply(all_files,
               function(f) any(vapply(required_months, function(m)
                 grepl(m, basename(f), fixed = TRUE), logical(1))),
               logical(1))
files <- all_files[keep]

message("Found ", length(files), " file(s) covering Oct 2025 - Jun 2026:")
print(basename(files))

missing_months <- required_months[!vapply(required_months, function(m)
  any(grepl(m, basename(files), fixed = TRUE)), logical(1))]
if (length(missing_months) > 0)
  warning("No file found for: ", paste(missing_months, collapse = ", "))

read_opts <- list(stringsAsFactors = FALSE, check.names = FALSE,
                  colClasses = c(id = "character", host_id = "character"))

all_data <- vector("list", length(files))

for (i in seq_along(files)) {
  f  <- files[i]
  d  <- do.call(read.csv, c(list(file = f), read_opts))

  # filter: Christchurch
  n_before <- nrow(d)
  d <- d[d$neighbourhood_group == "Christchurch City", , drop = FALSE]
  message(sprintf("  %-28s %8d rows -> %6d Christchurch rows",
                  basename(f), n_before, nrow(d)))
  if (nrow(d) == 0) warning("No Christchurch rows in ", basename(f))

  # add month + year column
  nm  <- basename(f)
  yr  <- regmatches(nm, regexpr("20[0-9]{2}", nm))            # e.g. "2025"
  mo  <- regmatches(nm, regexpr("[A-Za-z]+,", nm))            # e.g. "October,"
  mo  <- sub(",", "", mo, fixed = TRUE)                        # e.g. "October"
  d$month_year <- sprintf("%s-%02d", yr, month_num[[mo]])     # e.g. "2025-10"

  all_data[[i]] <- d
}

chch_all <- do.call(rbind, all_data)
row.names(chch_all) <- NULL

# --- defensive de-duplication: if two team members downloaded the same
# --- month, the identical (id + month) rows are removed -----------------
#before_dedup <- nrow(chch_all)
#chch_all <- chch_all[!duplicated(chch_all[, c("id", "month_year")]), ]
#message("Duplicated (listing, month) rows removed: ", before_dedup - nrow(chch_all))

message("\nConcatenated dataset: ", nrow(chch_all), " rows x ",
        ncol(chch_all), " columns")
print(table(chch_all$month_year))

# --- format check: month_year must be "YYYY-MM" (e.g. 2026-06), same as summary ---
#if (!all(grepl("^[0-9]{4}-[0-9]{2}$", chch_all$month_year)))
#  warning("Some month_year values are NOT in YYYY-MM format - check file names!")


summarise_col <- function(x, name) {
  is_num <- is.numeric(x)
  n_obs  <- sum(!is.na(x))          # number of non-missing values

  stat <- function(fun) if (n_obs > 0) round(fun(x, na.rm = TRUE), 2) else NA
  row <- data.frame(
    column       = name,
    type         = if (is_num) "numeric" else "character",
    n            = length(x),
    n_missing    = sum(is.na(x)),
    pct_missing  = round(100 * mean(is.na(x)), 2),
    n_unique     = length(unique(x[!is.na(x)])),
    min          = if (is_num) stat(min) else NA,
    max          = if (is_num) stat(max) else NA,
    mean         = if (is_num) stat(mean) else NA,
    median       = if (is_num) stat(median) else NA,
    sd           = if (is_num) stat(sd) else NA,
    most_common  = if (!is_num) {
                    tt <- sort(table(x), decreasing = TRUE)
                    if (length(tt) == 0) NA else paste0(names(tt)[1], " (", tt[1], ")")
                  } else NA,
    stringsAsFactors = FALSE
  )
  row
}

summary_tbl <- do.call(rbind, lapply(names(chch_all),
                                     function(nm) summarise_col(chch_all[[nm]], nm)))
row.names(summary_tbl) <- NULL

cat("\n==================== SUMMARY STATISTICS ====================\n")
print(summary_tbl, row.names = FALSE)
cat("=============================================================\n")

# ---------------------------------------------------------------------
# 6. Save outputs
# ---------------------------------------------------------------------
write.csv(chch_all, out_file, row.names = FALSE)
write.csv(summary_tbl, sum_file, row.names = FALSE)

message("\nSaved concatenated dataset -> ", out_file)
message("Saved summary statistics -> ", sum_file)
