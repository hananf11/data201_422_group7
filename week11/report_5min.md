# 5-minute live-demo report — Deliverable 7 (Week 11 pipeline automation)

> 形式:无 PPT,直接在电脑上边讲边演示(展示文件 + 现场运行)。
> 实测:完整流水线 **11 秒**跑完(13 个月数据,地理编码缓存已热、0 次 API 调用)。首次把 7/8 月并入时花了 **277 次 API 调用、约 4 分钟**——一次性成本,之后每次重跑都免费。
> 每节给出英文讲稿(可照读)+ 【中文提示】(操作 + 要点 + 必须说到的数字)。
> 加粗的数字是老师最可能记住的东西,放慢说清楚。人称用 we;要强调个人贡献就把对应 we 改成 I。

---

## 0:00–0:45 Open the folder — "the deliverable is the pipeline itself"

**EN:**
"Deliverable 7 asked us to automate our data wrangling pipeline, so that when Inside Airbnb publishes new months, updating our analysis takes one command. No slides — let me just show you the pipeline. Everything lives in one folder, `week11`: the eight pipeline scripts you see here, the raw monthly Airbnb files in `data/listings` — thirteen months of them — and the `output` folder with our results. Watch: this entire thing runs with one command."

**操作:** 打开文件管理器/VS Code 展示 `week11/` 目录结构(scripts → data → output)。
【中文提示】一句话点题(代替被删掉的开场),然后立刻展示目录:8 个脚本、`data/listings` 里 13 个月的原始文件、`output` 产物。落点:"整个东西就是一条命令"。

---

## 0:45–2:15 Live run — one command, eight stages, ~11 seconds

**EN:**
"I'll run it now. `bash week11/run_all.sh` — and it works from any directory. [run it] Stage 1 combines the thirteen monthly files — 636,000 rows New Zealand-wide — and keeps the 41,614 Christchurch listings. Stages 3 and 4 clean the listings and the rental-bond data. Stage 5 is the geocoding step — watch the output: it says all **41,614 rows reuse cached areas, zero new ids to geocode**. We already paid the API cost once; a listing's coordinates never change, so its statistical area never changes, and the repeat run is free. Stage 6 merges rentals with listings — 191,000 rows. And stages 7 and 8 produce our analyses. Total: about eleven seconds."

**操作:** 终端现场执行 `bash week11/run_all.sh`(约 11 秒),滚动过程中按阶段口头跟随。
【中文提示】关键动作:现场跑,边滚边说。必须点到的数字:**13 个月、636,213 行 → 41,614 行 Christchurch、合并 191,368 行、全程约 11 秒**。阶段 5 主动念出来:"41,614 rows reuse cached areas, 0 new ids"——缓存命中,重跑免费。

---

## 2:15–3:15 Show the outputs — the plots updated themselves

**EN:**
"Here's the output folder. The price histogram is rebuilt from all thirteen months. The step-7 boxplots show the gap between short-term and long-term prices by area — city-wide the median gap is **126 dollars a night, about 2.7 times the long-term rate**, and the biggest gaps are in Fendalton, Heathcote and Innes — around 200 dollars a night. The step-8 barplots compare Airbnb supply with long-term rental stock per area — in the busiest central area Airbnb is about **27 percent of the combined rental stock**. These are the same numbers we published in week 9, which is exactly the point: the automated pipeline reproduces our analysis. One honest caveat the pipeline itself surfaced: the histogram covers all thirteen months, but the gap and supply plots currently end at **quarter two of 2026** — July and August are quarter three, and the government's rental-bond file doesn't contain quarter-three rents yet; we checked, there are zero rows for 2026-07. That's MBIE's publishing lag, not our pipeline. The moment they publish, one command pulls July and August into those plots too."

**操作:** 依次打开 `output/listings_christchurch_price_hist.png`、`step7_gap_boxplot_by_location.png`、`step8_counts_barplot.png`(提前把这几张图在看图软件/浏览器标签页里备好,现场只需切换)。
【中文提示】看图说话:直方图(13 个月)、step7 箱线图(**$126/晚、2.7×**、Fendalton/Heathcote/Innes ~$200)、step8 柱状图(最热 central 区域 **27%**)。收两句:① 和 week9 发布的数字一致 = 自动化复现了分析;② 诚实说明 gap/supply 图目前止于 2026-Q2——7/8 月属于 Q3,而 bond 文件里 2026-07 行数为零(我们核查过),是 MBIE 的发布滞后,数据一发布一条命令即可刷新。

---

## 3:15–4:15 Highlight — incremental geocoding: 150× fewer API calls

**EN:**
"Geocoding is where the interesting engineering is, and we've already run it for real. The old script called the Koordinates API once per row — with our full dataset that would be 41,614 calls. But a listing's coordinates never change, so its statistical area never changes either. That means the output of the geocoding step is really a cache. `main.py` now reads the previous output, reuses every id it already knows, and queries the API only for brand-new listings, once each. When the API key arrived, that's exactly what happened: adding July and August — releases 2026-07-12 and 2026-08-13, which we found by querying the JSON behind the website's 'show archived data' panel instead of hard-coding URLs — took **277 calls instead of 41,614, about 150 times fewer**. And you just saw the payoff in the live run: stage 5 found zero new ids and finished instantly. Every future month will cost only its genuinely new listings."

**操作:** 打开 `week11/main.py` 展示 `load_known_areas` / 缓存复用逻辑;再切到 `data/listings/` 指出 `2026-07-12_listings.csv` 和 `2026-08-13_listings.csv`。
【中文提示】核心观察:坐标不变 → 区域码永久 → 输出文件即缓存。关键对比:**41,614 行 vs 277 次调用(约 150 倍)**——而且这 277 次已经真实跑完(拿到 key 后),刚才现场演示里阶段 5 显示 0 new ids 就是缓存在工作。顺手指一下 7/8 月两个文件:日期是从网站 JSON 发现的,不是硬编码。

---

## 4:15–5:00 What automation surfaced — three real bugs, fixed

**EN:**
"Automating this also paid for itself in data quality, because you can't orchestrate scripts that don't actually run. We found three things. Our old merge script used R's pipe operator without ever loading dplyr — it only worked by luck inside an interactive session. Our geocoder was reading listing ids as numbers, silently corrupting all 19-digit ids into scientific notation — we fixed the reader and repaired the existing output, all 28,795 rows, with a verified positional repair, no API calls. And a .gitignore gap meant a 30-megabyte raw file was one `git add` away from the repository. Each fix is small — the point is that a pipeline that must run end-to-end, unattended, forces you to find them. That, plus caching that makes re-runs cheap, is what we take away from this week. Thank you — happy to show any part of the code."

【中文提示】三个 bug 各一句:① main.R 用 %>% 却没加载 dplyr(侥幸能跑);② 19 位 id 被 float 损坏 → 修读取 + 对存量 **28,795 行**做有验证的位置修复(零 API 调用);③ .gitignore 漏洞差点提交 30MB。收尾:无人值守必须跑通的流水线会逼你发现这些问题 + 缓存让重跑便宜。留一句"欢迎看任何代码"。

---

## 演示前检查清单(当天早上过一遍)

- [ ] 先完整跑一遍 `bash week11/run_all.sh` 确认正常(约 11 秒;阶段 5 应显示 "41,614 rows reuse cached areas, 0 new ids to geocode")
- [ ] 把 3 张图(price_hist、step7 箱线、step8 柱状)在图片查看器/浏览器标签页里预先打开
- [ ] VS Code 预开标签:`week11/` 目录树、`main.py`、`README.md`(fallback 顺序)
- [ ] 终端字号调大(投影可读)、关掉通知、插电源
- [ ] `data/listings/` 里确认 13 个文件都在(尤其 2026-07-12 和 2026-08-13)
- [ ] 确认 `week11/.env` 存在(已被 .gitignore 忽略,git status 应看不到它——**不要**提交)
- [ ] 若现场运行万一失败:output 里的产物是早上刚生成的,直接切到第 3 节看图继续讲

## 可能被问到的问题(备答)

- **"Why Python and not R?"** — One language for the whole pipeline lowers maintenance cost; the ports were verified to reproduce identical results, so nothing was lost. (统一语言降低维护成本,移植经结果一致性验证。)
- **"What if a listing's coordinates DID change?"** — In practice Airbnb listings keep fixed locations; if one ever moved, deleting the cache file forces a full re-geocode. (坐标实际不变;真要重算,删缓存即全量重跑。)
- **"Is 277 the final number?"** — It's today's count of not-yet-geocoded ids; each future month adds only its genuinely new listings, typically a few hundred. (277 是当前存量缺口;以后每月只加真正的新 listing。)
- **"Why does stage 5 run every time — isn't that wasteful?"** — The stage runs, but the calls don't: with the cache warm it printed zero new ids and took about a second. Only genuinely new listings trigger API calls. (阶段每次都跑,但调用不重复:缓存命中时 0 次调用,约 1 秒;只有真正的新 listing 才花调用。)
- **"Where do the plots change with July and August?"** — The histogram already covers all 13 months. The gap and supply plots currently end at 2026-Q2 because July/August are 2026-Q3 and MBIE hasn't published quarter-three rents yet (zero 2026-07 rows in the bond file — we checked). When they do, one command refreshes those plots automatically. (直方图已含 13 个月;gap/supply 图止于 Q2,因为 MBIE 尚未发布 Q3 租金——已核实 bond 文件无 2026-07 行;发布后一条命令即自动刷新。)
