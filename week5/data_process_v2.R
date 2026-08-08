# Week 5 作业：Airbnb listings（基督城，2025年10月-2026年6月）
# Week 5 assignment: Airbnb listings (Christchurch, Oct 2025 - Jun 2026)
#
# 只依赖基础 R，无需安装任何包
# Requires base R only, no extra packages needed
#
# 运行方式：把本脚本放在包含 origin_data 文件夹的目录下，然后 source("listings_processing.R")
# How to run: put this script in the folder containing the origin_data folder, then source("listings_processing.R")

# 数据文件夹路径（按需修改）
# Path to the data folder (change if needed)
data_dir <- "origin_data"

# 输出文件：拼接后的数据集 / 汇总统计表
# Output files: concatenated dataset / summary statistics
out_file <- "christchurch_listings.csv"
sum_file <- "summary_statistics.csv"

# 作业要求的月份范围，文件名形如 "05_October, 2025.csv"，按 "月, 年" 匹配
# Required month range; file names look like "05_October, 2025.csv", matched by "Month, Year"
required_months <- c("October, 2025", "November, 2025", "December, 2025",
                     "January, 2026", "February, 2026", "March, 2026",
                     "April, 2026", "May, 2026", "June, 2026")

# 月份名转数字，用于生成 "YYYY-MM" 列
# Map month names to numbers for the "YYYY-MM" column
month_num <- c(January = 1, February = 2, March = 3, April = 4, May = 5, June = 6,
               July = 7, August = 8, September = 9, October = 10, November = 11,
               December = 12)

# 列出数据文件夹里的所有 CSV 文件
# List all CSV files in the data folder
all_files <- list.files(data_dir, pattern = "\\.csv$", full.names = TRUE)
if (length(all_files) == 0) stop("No CSV files found in: ", data_dir)

# 只保留覆盖所需月份的 9 个文件
# Keep only the files covering the 9 required months
keep <- vapply(all_files,
               function(f) any(vapply(required_months, function(m)
                 grepl(m, basename(f), fixed = TRUE), logical(1))),
               logical(1))
files <- all_files[keep]

message("Found ", length(files), " file(s) covering Oct 2025 - Jun 2026:")
print(basename(files))

# 提示哪些月份缺少文件
# Warn about months with no file
missing_months <- required_months[!vapply(required_months, function(m)
  any(grepl(m, basename(files), fixed = TRUE)), logical(1))]
if (length(missing_months) > 0)
  warning("No file found for: ", paste(missing_months, collapse = ", "))

# id / host_id 按字符读入，避免 19 位大整数在数值型下丢失精度
# Read id / host_id as character to keep the full 19-digit IDs exact
read_opts <- list(stringsAsFactors = FALSE, check.names = FALSE,
                  colClasses = c(id = "character", host_id = "character"))

all_data <- vector("list", length(files))

# 逐文件读取、筛选基督城、添加月份列，存入列表
# Read each file, filter Christchurch, add the month column, store in a list
for (i in seq_along(files)) {
  f  <- files[i]
  d  <- do.call(read.csv, c(list(file = f), read_opts))

  # 只保留基督城的数据
  # Keep Christchurch rows only
  n_before <- nrow(d)
  d <- d[d$neighbourhood_group == "Christchurch City", , drop = FALSE]
  message(sprintf("  %-28s %8d rows -> %6d Christchurch rows",
                  basename(f), n_before, nrow(d)))
  if (nrow(d) == 0) warning("No Christchurch rows in ", basename(f))

  # 从文件名提取年份和月份，生成 month_year（如 "2025-10"）
  # Extract year and month from the file name to build month_year (e.g. "2025-10")
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

# 去重：若两位成员下载了同一个月，相同的 (id, month_year) 行只保留一条
# De-duplicate: if two members downloaded the same month, keep one row per (id, month_year)
before_dedup <- nrow(chch_all)
chch_all <- chch_all[!duplicated(chch_all[, c("id", "month_year")]), ]
message("Duplicated (listing, month) rows removed: ", before_dedup - nrow(chch_all))

message("\nConcatenated dataset: ", nrow(chch_all), " rows x ",
        ncol(chch_all), " columns")
print(table(chch_all$month_year))

# 校验 month_year 全部为 "YYYY-MM" 格式，与汇总保持一致
# Check that all month_year values are "YYYY-MM", consistent with the summary
if (!all(grepl("^[0-9]{4}-[0-9]{2}$", chch_all$month_year)))
  warning("Some month_year values are NOT in YYYY-MM format - check file names!")

# 对每一列生成类型感知的汇总统计
# Type-aware summary statistics for every column
summarise_col <- function(x, name) {
  is_num <- is.numeric(x)
  n_obs  <- sum(!is.na(x))

  # 无有效观测时返回 NA，避免出现 Inf/NaN（如全空的 license 列）
  # Return NA when there are no valid observations, avoiding Inf/NaN (e.g. all-NA license)
  stat <- function(fun) if (n_obs > 0) round(fun(x, na.rm = TRUE), 2) else NA

  # 出现次数最多的取值；并列第一时全部列出（并列过多时只列数量并举例）
  # Most frequent value(s); list all when tied, or give the count plus examples when ties are many
  top_value <- function(x) {
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
