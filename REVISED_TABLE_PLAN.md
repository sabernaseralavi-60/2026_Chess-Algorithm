# REVISED TABLE PLAN

Governing rule, from Dr. Mirjalili's third comment:

> "Presenting the tables in a way that columns show test functions and rows show the algorithms."

Every **primary comparison table** in the revised manuscript therefore has

```
column 1 = Algorithm     columns 2…n = test functions / problems     one row per algorithm
```

Detailed statistics that do not fit that orientation (best and worst run, per-function p-values in
full precision) are **relocated, never deleted**: they move to Appendix A of the manuscript and
remain in the committed `results/*.md` and `results/*.csv` files, so every primary cell stays
traceable to the detail.

---

## Conventions

**Cell format.** `mean ±std`, both in the same notation, three significant digits, e.g.
`6.16e-05 ±1.15e-04`. The space before `±` and none after lets a narrow PDF column wrap the cell
into two lines (mean over std) without a `resizebox`.

**Bolding.** The best *mean* in each function column is bold. A best *run* is never bolded
(brief §7). In the summary tables, CA's own row is bold so the reader can find it.

**Statistical marking.** In the transposed Wilcoxon tables, each p-value carries a direction
marker: `(+)` CA significantly better, `(-)` CA significantly worse, `(=)` not significant at
α = 0.05. ASCII only, so the marker renders identically in HTML and PDF.

**Width control.** Pandoc renders these as `longtable`s; the PDF header adds
`\AtBeginEnvironment{longtable}{\scriptsize}` (etoolbox) so wide tables fit the A4 text block at a
legible size without `\resizebox`. `booktabs` rules are already enabled in the manuscript header.
No vertical rules.

**Grouping.** No table has more than 10 function columns. CEC-2017 is split by its **official**
categories (see `PRESENTATION_AUDIT.md` §H — the mapping from the paper's `opfunu` labels to the
official categories is derived from the suite definition, not invented). CEC-2022 is split by its
two **official** dimensionalities.

**Generation.** All primary tables are written by `src/generate_transposed_tables.py` from the
committed CSVs; the pre-existing `src/generate_markdown_tables.py` continues to produce the
detailed function-major tables that now live in Appendix A. No table cell is typed by hand.

---

## Primary tables (main text)

### T1 — `tbl-stats` — Classical suite, transposed
* **Purpose.** Final-error comparison on the six classical 30-D functions.
* **Rows.** CA, CA-static, GA, PSO, SA, GWO (this suite's roster).
* **Columns.** F1 Sphere, F2 Rosenbrock, F3 Rastrigin, F4 Griewank, F5 Ackley, F6 Schwefel 2.22.
* **Cells.** `mean ±std`, best mean per column bold.
* **Source.** `results/benchmark_stats.csv`.
* **Placement.** Main text §3. Best/worst → Appendix A (`results/table_stats.md`, unchanged).
* **Statistical summary required.** Yes — T2 (Wilcoxon) immediately after.
* **Category.** `[DIRECT REQUEST]`

### T2 — `tbl-wilcoxon` — Classical suite Wilcoxon, transposed
* **Purpose.** Is each pairwise difference significant, and in which direction?
* **Rows.** CA vs CA-static / GA / PSO / SA / GWO.
* **Columns.** The six functions.
* **Cells.** `p (+)` / `p (-)` / `p (=)` as defined above.
* **Source.** `results/wilcoxon.csv`.
* **Category.** `[DIRECT REQUEST]`

### T3 — `tbl-anova` — Classical suite ANOVA, transposed
* **Purpose.** Does the algorithm factor matter at all?
* **Rows.** F-statistic, p-value. **Columns.** The six functions.
* **Source.** `results/anova.csv`. **Category.** `[STRONG]`

### T4 — `tbl-cec2017-summary` — CEC-2017 standing (merges the old ranks + W/T/L tables)
* **Purpose.** Who leads the suite, by how much, and what is CA's record against each competitor?
* **Rows.** The eight algorithms, ordered by mean Friedman rank.
* **Columns.** Mean Friedman rank | Rank position | Functions with the best mean | W/T/L vs CA.
* **Source.** `results/cec2017_mean_ranks.csv`, `results/cec2017_wilcoxon.csv`,
  `results/cec2017_stats.csv`.
* **Reader decision it supports.** Which algorithms outperform CA and which do not — in one look.
* **Category.** `[STRONG]` (MGO convention; replaces two tables with one)

### T5–T8 — `tbl-cec2017-unimodal`, `-multimodal`, `-hybrid`, `-composition`
* **Purpose.** Full per-function mean ± std comparison, in the requested orientation.
* **Rows.** The eight algorithms. **Columns.** The functions of one official category:
  * T5 Unimodal — F1, F2 (2 columns)
  * T6 Simple multimodal — F3–F9 (7 columns)
  * T7 Hybrid — F10–F19 (10 columns)
  * T8 Composition — F20–F29 (10 columns)
* **Cells.** `mean ±std`, best mean per function bold.
* **Source.** `results/cec2017_stats.csv`.
* **Placement.** Main text §4; best/worst per function → Appendix A.
* **Category.** `[DIRECT REQUEST]`

### T9 — `tbl-cec2022-summary`
* As T4, for the 16 validated CEC-2022 cells.
* **Source.** `results/cec2022_mean_ranks.csv`, `results/cec2022_wilcoxon.csv`,
  `results/cec2022_stats.csv`. **Category.** `[STRONG]`

### T10–T11 — `tbl-cec2022-d10`, `tbl-cec2022-d20`
* **Rows.** Eight algorithms. **Columns.** The 8 validated functions at that dimensionality.
* **Cells.** `mean ±std`, best bold. **Source.** `results/cec2022_stats.csv`.
* **Note in caption.** The excluded cells and the reason for each remain in `tbl-cec2022-audit`,
  which stays in the main text (brief §8: the audit must not be hidden).
* **Category.** `[DIRECT REQUEST]`

### T12 — `tbl-engineering-summary`
* As T4, for the seven constrained engineering problems.
* **Source.** `results/engineering_mean_ranks.csv`, `results/engineering_wilcoxon.csv`,
  `results/engineering_stats.csv`. **Category.** `[STRONG]`

### T13 — `tbl-engineering-stats`
* **Rows.** Eight algorithms. **Columns.** Welded Beam, Spring, Pressure Vessel, Speed Reducer,
  Three-Bar Truss, Gear Train, Cantilever Beam.
* **Cells.** `mean ±std`, best bold. **Source.** `results/engineering_stats.csv`.
* **Category.** `[DIRECT REQUEST]`

### T14 — `tbl-timing` — Computational cost, transposed
* **Purpose.** What does each algorithm cost, in evaluations and in wall-clock time?
* **Rows.** Eight algorithms.
* **Columns.** Two blocks: mean seconds per run on each of the six timed problems, then two summary
  columns — mean evaluations / core budget, and mean time relative to GA.
* **Source.** `results/timing_stats.csv`.
* **Caption must state.** That "evals / core budget" is measured with an exact counting wrapper
  against N × T, that the ratio slightly exceeds 1 for every algorithm because the initial
  population evaluation sits outside N × T, and that the measured 12.4 % figure for CA replaces
  the earlier estimate. The measured/estimated distinction of the current text is preserved.
* **Category.** `[DIRECT REQUEST]`

### T15 — `tbl-traffic` — Signal timing (merges the old results + Wilcoxon tables)
* **Rows.** CA, CA-static, GA, PSO, GWO. **Columns.** Mean ± std | Best | Worst | p vs CA | Result.
* **Rationale for keeping algorithms as rows and statistics as columns.** There is only one problem
  here, so "functions as columns" does not apply; the algorithms are already the rows.
* **Source.** `results/traffic_stats.csv`, `results/table_traffic_wilcoxon.md`.
* **Category.** `[STRONG]` (removes one redundant table)

---

## Tables kept unchanged `[DO NOT CHANGE]`

| Table | Why |
|---|---|
| `tbl-mapping` | Definition table; chess concept → algorithmic role |
| `tbl-params` | Parameter definitions (a clarifying note on the Pawn remainder is added; no value changes) |
| `tbl-phase-schedule` | Definition table; also mirrored in FIG 6 |
| `tbl-operator-families` | The paper's answer to the metaphor critique; must stay intact |
| `tbl-suite` | Benchmark definitions, not results |
| `tbl-opfunu-audit`, `tbl-cec2017-restoration`, `tbl-cec2022-audit` | Data-integrity evidence; the brief requires that it stay visible |
| `tbl-ablation`, `tbl-sensitivity` | Already mechanism-major, which is the correct orientation for them; each gains a figure |
| `tbl-plan` | The best coordination plan |
| `tbl-mealpy-signal`, `tbl-mealpy-berth`, `tbl-berth-gap` | Already algorithm-major |

---

## Appendix A — supplementary tables (relocated detail, main-text manuscript appendix)

| ID | Content | Source file | Why relocated |
|---|---|---|---|
| `tbl-app-classical` | Classical suite: mean, std, best, worst per function × algorithm | `results/table_stats.md` | Best/worst do not fit the transposed primary table |
| `tbl-app-cec2017` | CEC-2017: mean, std, best, worst, all 29 functions × 8 algorithms | `results/table_cec2017_stats.md` | 232 rows; unreadable in the main text |
| `tbl-app-cec2022` | CEC-2022: same, 16 cells | `results/table_cec2022_stats.md` | 128 rows |
| `tbl-app-engineering` | Engineering: same, 7 problems | `results/table_engineering_stats.md` | 56 rows |
| `tbl-app-ablation` | Per-problem ablation ratios and p-values | `results/table_ablation_detail.md` | Was repository-only; promoting it to an appendix improves traceability |
| `tbl-app-timing` | Full per-problem × algorithm timing detail | `results/table_timing.md` | The transposed primary table drops the per-problem evaluation counts |

Every primary cell has a counterpart in exactly one appendix table, and
`src/validate_presentation.py` checks that correspondence numerically (mean and std of every
primary cell are re-read from the source CSV and compared to the rendered string).

---

## Table-content test (brief §18)

| Table | What is compared? | Why necessary? | Reader decision | Figure better? | Shortenable? |
|---|---|---|---|---|---|
| T1 | 6 algorithms on 6 classical functions | The entry-level suite everyone reports | Is CA competitive on classical terrain? | No — exact values matter | Already minimal |
| T2 | Significance of T1 | A mean without a test is not evidence | Which differences are real? | No | No |
| T3 | Algorithm factor per function | Precondition for the pairwise tests | — | No | Two rows only |
| T4/T9/T12 | 8 algorithms, whole suite | The paper's headline standing | Who leads; where CA sits | Complemented by FIG 12 | Already merged from two tables |
| T5–T8 | 8 algorithms × 29 functions | The suite's per-function evidence | Where exactly CA wins and loses | No | Split by official category |
| T10/T11 | 8 algorithms × 8 cells per D | Same, at two official dimensionalities | Does the ordering survive a newer suite? | No | Already minimal |
| T13 | 8 algorithms × 7 design problems | Constrained-engineering validation | Does the ordering survive constraints? | No | Already minimal |
| T14 | Cost of all 8 algorithms | Answers "what does CA's overhead cost?" | Is the 12.4 % overhead material? | Partly, but exact counts are the point | Detail → Appendix A |
| T15 | 5 algorithms on one instance | The motivating application | Can CA be used for signal coordination? | No | Merged from two tables |
