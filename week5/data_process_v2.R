# 数据文件夹路径
# Path to the data folder
data_dir <- "week5/origin_data"

# 输出文件：拼接后的数据集 / 汇总统计表
# Output files: concatenated dataset / summary statistics
out_file <- "christchurch_listings.csv"
sum_file <- "summary_statistics.csv"

# 文件名形如 "05_October, 2025.csv"，按 "月, 年" 匹配
# Required months (in "Month, Year" format) to match filenames like "05_October, 2025.csv"
required_months <- c("October, 2025", "November, 2025", "December, 2025",
                     "January, 2026", "February, 2026", "March, 2026",
                     "April, 2026", "May, 2026", "June, 2026")

# 月份名转数字
# Map month name to number
month_num <- c(January = 1, February = 2, March = 3, April = 4, May = 5, June = 6,
               July = 7, August = 8, September = 9, October = 10, November = 11,
               December = 12)

# 列出数据文件夹里的所有 CSV 文件
# List all CSV files in the data folder
all_files <- list.files(data_dir, pattern = "\\.csv$", full.names = TRUE)
if (length(all_files) == 0) stop("No CSV files found in: ", data_dir)

# 只保留覆盖所需月份的 9 个文件
# Keep only the 9 files that cover the required months
keep <- vapply(all_files,
               function(f) any(vapply(required_months, function(m)
                 grepl(m, basename(f), fixed = TRUE), logical(1))),
               logical(1))
files <- all_files[keep]

message("Found ", length(files), " file(s) covering Oct 2025 - Jun 2026:")
print(basename(files))

# 提示哪些月份缺少文件
# Warn about months with no file
# missing_months <- required_months[!vapply(required_months, function(m)
#   any(grepl(m, basename(files), fixed = TRUE)), logical(1))]
# if (length(missing_months) > 0)
#   warning("No file found for: ", paste(missing_months, collapse = ", "))

# id / host_id/ last_review按字符读入
# Read id / host_id/ last_review as character
read_opts <- list(stringsAsFactors = FALSE, check.names = FALSE,
                  colClasses = c(id = "character", host_id = "character", last_review = "character"))

all_data <- vector("list", length(files))


for (i in seq_along(files)) {
  f  <- files[i]
  d  <- do.call(read.csv, c(list(file = f), read_opts))

  # 只保留基督城
  # Keep Christchurch rows only
  n_before <- nrow(d)
  d <- d[d$neighbourhood_group == "Christchurch City", , drop = FALSE]
  message(sprintf("  %-28s %8d rows -> %6d Christchurch rows",
                  basename(f), n_before, nrow(d)))
  if (nrow(d) == 0) warning("No Christchurch rows in ", basename(f))

  # 生成 month_year
  # build month_year
  nm  <- basename(f)
  yr  <- regmatches(nm, regexpr("20[0-9]{2}", nm))
  mo  <- regmatches(nm, regexpr("[A-Za-z]+,", nm))
  mo  <- sub(",", "", mo, fixed = TRUE)
  d$month_year <- sprintf("%s-%02d", yr, month_num[[mo]])

  all_data[[i]] <- d
}

# 纵向拼接所有月份
# Bind all months together
chch_all <- do.call(rbind, all_data)
row.names(chch_all) <- NULL

# # 去重：若两位成员下载了同一个月，相同的 (id, month_year) 行只保留一条
# # De-duplicate: if two members downloaded the same month, keep one row per (id, month_year)
# before_dedup <- nrow(chch_all)
# chch_all <- chch_all[!duplicated(chch_all[, c("id", "month_year")]), ]
# message("Duplicated (listing, month) rows removed: ", before_dedup - nrow(chch_all))

message("\nConcatenated dataset: ", nrow(chch_all), " rows x ",
        ncol(chch_all), " columns")
print(table(chch_all$month_year))


# 对每一列生成汇总统计
# summary statistics for every column
summarise_col <- function(x, name) {
  is_num <- is.numeric(x)
  n_obs  <- sum(!is.na(x))

  # 无有效观测时返回 NA，避免出现 Inf/NaN（如全空的 license 列）
  # Return NA when there are no valid observations, avoiding Inf/NaN
  stat <- function(fun) if (n_obs > 0) round(fun(x, na.rm = TRUE), 2) else NA

  # 出现次数最多的取值；并列第一时全部列出，并列过多时只列数量并举例）
  # Most frequent value(s); list all when tied, or give the count plus examples when ties are many
  top_value <- function(x) {

    # 过滤掉空字符串和 NA
    #filter out empty strings and NA
    x <- x[!is.na(x) & x != ""]
    if (length(x) == 0) return(NA)

    tt <- sort(table(x), decreasing = TRUE)
    if (length(tt) == 0) return(NA)
    mx  <- tt[1]
    ties <- names(tt)[tt == mx]
    if (length(ties) == 1) {
      paste0(ties, " (", mx, ")")
    } else if (length(ties) <= 5) {
      paste0(paste(ties, collapse = ", "), " (each ", mx, ")")
    } else {
      paste0(length(ties), " values tied at ", mx, " (e.g. ",
             paste(head(ties, 3), collapse = ", "), ", ...)")
    }
  }

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
    most_common  = if (!is_num) top_value(x) else NA,
    stringsAsFactors = FALSE
  )
  row
}

summary_tbl <- do.call(rbind, lapply(names(chch_all),
                                     function(nm) summarise_col(chch_all[[nm]], nm)))
row.names(summary_tbl) <- NULL

# 打印汇总表
# Print the summary table
print(summary_tbl, row.names = FALSE)

# 保存拼接后的数据集和汇总表
# Save the concatenated dataset and the summary table
write.csv(chch_all, out_file, row.names = FALSE)
write.csv(summary_tbl, sum_file, row.names = FALSE)

message("\nSaved concatenated dataset -> ", out_file)
message("Saved summary statistics -> ", sum_file)
