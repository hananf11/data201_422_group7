combine_airbnb_data <- function(
    data_dir = "./data/listings",
    out_file = "./output/christchurch_listings.csv",
    sum_file = "./output/summary_statistics.csv"
) {

  required_months <- c(
    "2025-10", "2025-11", "2025-12",
    "2026-01", "2026-02", "2026-03",
    "2026-04", "2026-05", "2026-06"
  )

  all_files <- list.files(
    data_dir,
    pattern = "\\.csv$",
    full.names = TRUE
  )

  if (length(all_files) == 0) {
    stop("No CSV files found in: ", data_dir)
  }

  keep <- vapply(
    all_files,
    function(f) {
      any(vapply(
        required_months,
        function(m) grepl(m, basename(f), fixed = TRUE),
        logical(1)
      ))
    },
    logical(1)
  )

  files <- all_files[keep]

  message(
    "Found ", length(files),
    " file(s) covering Oct 2025 - Jun 2026:"
  )

  print(basename(files))

  missing_months <- required_months[
    !vapply(
      required_months,
      function(m) any(grepl(m, basename(files), fixed = TRUE)),
      logical(1)
    )
  ]

  if (length(missing_months) > 0) {
    warning(
      "No file found for: ",
      paste(missing_months, collapse = ", ")
    )
  }

  read_opts <- list(
    stringsAsFactors = FALSE,
    check.names = FALSE,
    colClasses = c(
      id = "character",
      host_id = "character",
      last_review = "character"
    )
  )

  all_data <- vector("list", length(files))

  for (i in seq_along(files)) {

    f <- files[i]

    d <- do.call(
      read.csv,
      c(list(file = f), read_opts)
    )

    n_before <- nrow(d)

    d <- d[
      d$neighbourhood_group == "Christchurch City",
      ,
      drop = FALSE
    ]

    message(
      sprintf(
        "  %-40s %8d rows -> %6d Christchurch rows",
        basename(f),
        n_before,
        nrow(d)
      )
    )

    if (nrow(d) == 0) {
      warning("No Christchurch rows in ", basename(f))
    }

    # Extract YYYY-MM from filenames such as:
    # new-zealand_2025-10-05_listings.csv
    nm <- basename(f)

    date_match <- regmatches(
      nm,
      regexpr("[0-9]{4}-[0-9]{2}-[0-9]{2}", nm)
    )

    if (length(date_match) == 0 || is.na(date_match)) {
      stop(
        "Could not extract date from filename: ",
        basename(f)
      )
    }

    d$month_year <- substr(date_match, 1, 7)

    all_data[[i]] <- d
  }

  chch_all <- do.call(rbind, all_data)

  row.names(chch_all) <- NULL

  message(
    "\nConcatenated dataset: ",
    nrow(chch_all),
    " rows x ",
    ncol(chch_all),
    " columns"
  )

  print(table(chch_all$month_year))

  summarise_col <- function(x, name) {

    is_num <- is.numeric(x)
    n_obs <- sum(!is.na(x))

    stat <- function(fun) {
      if (n_obs > 0) {
        round(fun(x, na.rm = TRUE), 2)
      } else {
        NA
      }
    }

    top_value <- function(x) {

      x <- x[!is.na(x) & x != ""]

      if (length(x) == 0) {
        return(NA)
      }

      tt <- sort(table(x), decreasing = TRUE)

      if (length(tt) == 0) {
        return(NA)
      }

      mx <- tt[1]
      ties <- names(tt)[tt == mx]

      if (length(ties) == 1) {

        paste0(ties, " (", mx, ")")

      } else if (length(ties) <= 5) {

        paste0(
          paste(ties, collapse = ", "),
          " (each ",
          mx,
          ")"
        )

      } else {

        paste0(
          length(ties),
          " values tied at ",
          mx,
          " (e.g. ",
          paste(head(ties, 3), collapse = ", "),
          ", ...)"
        )
      }
    }

    data.frame(
      column = name,
      type = if (is_num) "numeric" else "character",
      n = length(x),
      n_missing = sum(is.na(x)),
      pct_missing = round(100 * mean(is.na(x)), 2),
      n_unique = length(unique(x[!is.na(x)])),
      min = if (is_num) stat(min) else NA,
      max = if (is_num) stat(max) else NA,
      mean = if (is_num) stat(mean) else NA,
      median = if (is_num) stat(median) else NA,
      sd = if (is_num) stat(sd) else NA,
      most_common = if (!is_num) top_value(x) else NA,
      stringsAsFactors = FALSE
    )
  }

  summary_tbl <- do.call(
    rbind,
    lapply(
      names(chch_all),
      function(nm) {
        summarise_col(chch_all[[nm]], nm)
      }
    )
  )

  row.names(summary_tbl) <- NULL

  print(summary_tbl, row.names = FALSE)

  write.csv(
    chch_all,
    out_file,
    row.names = FALSE
  )

  write.csv(
    summary_tbl,
    sum_file,
    row.names = FALSE
  )

  message(
    "\nSaved concatenated dataset -> ",
    out_file
  )

  message(
    "Saved summary statistics -> ",
    sum_file
  )

  return(chch_all)
}
