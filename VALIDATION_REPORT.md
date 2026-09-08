# VALIDATION REPORT

Validation of the presentation revision of *The Chess Algorithm* (2026-09-08). The revision
transposed every primary comparison table, relocated the best/worst statistics to an appendix, added
ten figures, and replaced one. None of that is allowed to change a number, so every claim below is
checked mechanically rather than asserted.

Reproduce with:

```bash
python src/generate_transposed_tables.py   # primary tables
python src/generate_markdown_tables.py     # appendix tables
python src/make_concept_figures.py
python src/make_method_figures.py
python src/make_result_figures.py
python src/validate_presentation.py        # the checks below
quarto render paper.qmd
```

---

## 1. Automated checks — 52 / 52 passed

`src/validate_presentation.py` re-reads every rendered table cell and compares it against the
committed source CSV. It reports discrepancies; it never corrects them.

### 1.1 Numerical checks on the transposed tables (33 checks)

For each of the eleven primary statistics tables — classical, CEC-2017 (six category tables),
CEC-2022 (two dimensionality tables), engineering — three checks:

| Check | Result |
|---|---|
| Every `mean` in the table equals the value in the source CSV (relative tolerance $5\times10^{-3}$, the precision of four significant digits) | **PASS** for all 11 tables |
| Every `std` in the table equals the value in the source CSV | **PASS** for all 11 tables |
| The bolded cell in each function column is exactly the algorithm with the lowest mean — and no other cell in that column is bold | **PASS** for all 11 tables |

Source files: `benchmark_stats.csv`, `cec2017_stats.csv`, `cec2022_stats.csv`,
`engineering_stats.csv`.

### 1.2 Derived summary columns (9 checks)

For each of the three suite standing tables (CEC-2017, CEC-2022, engineering):

| Check | Result |
|---|---|
| Mean Friedman rank equals the value in `*_mean_ranks.csv` (half-up rounding to two decimals) | **PASS** ×3 |
| "Best mean on *n* of *N*" equals the count of functions on which that algorithm holds the lowest mean in the stats CSV | **PASS** ×3 |
| "CA's W / T / L" equals the counts recomputed from `*_wilcoxon.csv` at $\alpha=0.05$ | **PASS** ×3 |

The rank values printed in the revised tables reproduce the values quoted in the manuscript's own
prose exactly (L-SHADE 1.76, CMA-ES 2.28, CA 3.62 on CEC-2017; L-SHADE 1.88, CMA-ES 2.06, CA 3.63,
CA-static 3.75, GA 4.75, PSO 5.63, GWO 6.44, WOA 7.88 on CEC-2022; L-SHADE 1.57, CMA-ES 2.14,
CA 3.71 on engineering). One rounding convention had to be fixed to achieve this: `%.2f` rounds
3.625 to 3.62 (half-to-even), while the prose quotes 3.63, so the generator now rounds half-up.
No underlying value changed.

### 1.3 Suite coverage and statistical tables (2 checks)

| Check | Result |
|---|---|
| The six CEC-2017 category tables cover all 29 validated functions exactly once, and the grouping follows the official categories mapped through the manuscript's `opfunu` renumbering footnote | **PASS** |
| The transposed classical Wilcoxon table reproduces every $p$-value in `wilcoxon.csv` and every direction marker `(+) / (-) / (=)` | **PASS** |

### 1.4 Figure inputs (2 checks)

| Check | Result |
|---|---|
| The mean ablation ratios plotted in Fig. 13 reproduce the twelve published values of `results/table_ablation.md` (en passant 603.3, knight's fork 46.842, threefold 1.213, sacrifice 1.070, pinning 1.050, windmill 1.043, opposition init. 1.030, discovered attack 1.024, blockade 1.006, interference 0.999, castling 0.999, royal council 0.990) | **PASS** |
| The phase-schedule values printed in Fig. 5 are identical, cell by cell, to the manuscript's own phase-schedule table (Table 3) | **PASS** |

### 1.5 Structural and cross-reference checks (6 checks)

| Check | Result |
|---|---|
| Every figure file referenced by `paper.qmd` exists on disk (22 figures) | **PASS** |
| Every `{{< include >}}` target exists (24 includes) | **PASS** |
| No dangling cross-reference: every `@tbl-`, `@fig-`, `@eq-`, `@sec-`, `@prp-` reference has a definition | **PASS** |
| Every table and figure defined is referenced at least once in the text | **PASS** |
| No duplicate table or figure label | **PASS** |
| The equation, table and section numbers **printed inside the figures** resolve to the same objects in the rendered PDF | **PASS** — see §1.7 below |

Full output: run `python src/validate_presentation.py` (52/52). Three of the 52 are new since the first pass (§1.7): a hard check that `table_mealpy_signal.md`, `table_mealpy_berth.md` and `table_berth_gap.md` each carry an L-SHADE and a CMA-ES row, added after the transportation-pipeline dependency gap of §5 was closed with `src/run_transportation_pipeline.py`.

### 1.6 Transportation-table completeness (3 checks)

| Check | Result |
|---|---|
| `table_mealpy_signal.md` contains a row for L-SHADE and for CMA-ES | **PASS** |
| `table_mealpy_berth.md` contains a row for L-SHADE and for CMA-ES | **PASS** |
| `table_berth_gap.md` contains a row for L-SHADE and for CMA-ES | **PASS** |

These close the reproducibility gap of §5: `mealpy_comparison.py` alone writes these three files
with seven algorithms; `sota_addon_run.py --suite transport` must run afterward to add the other
two. `src/run_transportation_pipeline.py` is now the only supported way to (re)produce them, and
runs this exact check as its last step.

### 1.7 Figure-embedded references

The first draft of the mechanism figures hard-coded equation numbers ("Eq. 15"), and **all of them
were wrong** — the guessed numbers were off by one to three places, because Quarto numbers only
labelled equations. They are now derived at drawing time from `paper.qmd` itself
(`figstyle.eq`, `figstyle.eqs`, `figstyle.tbl`, `figstyle.sec`), so a figure can no longer drift
from the manuscript when an equation, table or section is inserted before it. The validator
closes the loop by checking a sample of those derived numbers against the text of the rendered
PDF (section headings, table captions, and the number printed beside an equation).

---

## 2. Reproducibility checks — re-runs accepted only on exact reproduction

Two figures could not be restyled from committed data, because per-iteration curves and best-x
vectors are not archived. Both scripts were re-run, and the re-run was accepted only after its
statistics were compared against the committed ones.

| Re-run | Purpose | Reproduction test | Result |
|---|---|---|---|
| `src/run_benchmarks.py` (133 s) | Restyle the classical-suite convergence and box-plot figures onto the paper's shared identity palette | `results/benchmark_stats.csv`, `results/wilcoxon.csv`, `results/anova.csv` compared to the pre-run copies with `DataFrame.equals` | **Bit-for-bit identical.** Restyled figures accepted |
| `src/mealpy_comparison.py` | Annotate the berth-allocation figure with the known optimum, the plan's objective, its optimality gap and its residual overlap | `results/table_mealpy_signal.md`, `results/table_mealpy_berth.md`, `results/table_berth_gap.md` compared to the pre-run copies | See §5 |

Everything else — CEC-2017, CEC-2022, engineering, ablation, sensitivity, timing, traffic — was
**not** re-run. All of their figures and tables are regenerated from the committed
`results/*.csv` and `results/raw_*.npz` files.

---

## 3. Rendering checks

| Check | Result |
|---|---|
| `quarto render paper.qmd --to html` | Clean; no unresolved cross-reference warnings |
| `quarto render paper.qmd --to pdf` (lualatex, 3 passes) | Clean; 66 pages, 4.8 MB |
| Wide transposed tables fit the A4 text block | **PASS** — verified by rendering pages 21, 27, 28, 34 and 39 to images and inspecting them. No table is scaled with `\resizebox`; width is controlled by `\scriptsize` inside table environments (via `etoolbox`) plus explicit `tbl-colwidths` |
| Numbers collide across columns | **Fixed.** The first draft of the hybrid and composition tables (11 columns) overlapped adjacent cells; those two categories are now split into two five-function tables each, so no table exceeds six function columns and every cell keeps four significant digits |
| Figure legibility at print size | Verified on the rendered PDF pages for Figs. 1–6, 13–15, 17 |
| Final numbering | 22 figures, 37 tables (31 in the main text, 6 in Appendix A), all auto-numbered by Quarto and consistent between HTML and PDF |

---

## 4. Discrepancies found — reported, not corrected

| # | Finding | Status |
|---|---|---|
| V1 | The classical-suite convergence figure plots the **mean** of the 30 runs, while its caption and axis label said *median*; the CEC-2017, CEC-2022 and engineering figures do plot medians | The plotted quantity was **not** changed. The axis label and the manuscript caption now say "averaged over the 30 runs", and the caption states explicitly that the other suites plot medians. **Flagged for the authors to confirm which was intended** — if the median was intended, only `src/run_benchmarks.py` line 148 changes (`.mean(axis=0)` → `np.median(..., axis=0)`), and the figure must be regenerated |
| V2 | `%.2f` formatting of Friedman ranks disagreed with the prose in two places (3.625 → "3.62" vs "3.63"; 5.625 → "5.62" vs "5.63") | Generator switched to half-up rounding, which matches the prose. No underlying rank changed |
| V3 | The parameter table gives four role fractions summing to 0.60 without stating the Pawn remainder | Stated in the caption of Fig. 4; no value changed |
| V4 | The classical six-function suite uses a different roster from every other suite (SA present; WOA, L-SHADE, CMA-ES absent) | Reported; Fig. 15 excludes that suite and its caption says why |
| V5 | A draft caption for the new CEC-2017 distribution figure claimed the competition-grade methods were "lower and tighter" on the unimodal panel and that the composition comparisons "frequently return ties". Checking against `cec2017_wilcoxon.csv` showed both claims to be false: CA holds the lowest mean on F1 (and ties both methods there, $p=0.21$), while on F22 and F26 CA loses to both significantly | The caption was corrected before publication; no result changed |
| V6 | All equation numbers hard-coded in the first draft of the figures were wrong (see §1.7) | Replaced by numbers derived from `paper.qmd`; now checked against the rendered PDF |

**No discrepancy was found between any number in the revised manuscript and its source data file.**

---

## 5. Status of the mealpy re-run

The berth-allocation figure annotation requires the best decoded plan, which is not archived, so
`src/mealpy_comparison.py` was re-executed. The acceptance rule is the same one applied to the
classical re-run: the regenerated `table_mealpy_signal.md`, `table_mealpy_berth.md` and
`table_berth_gap.md` must reproduce the committed files exactly. If they do not, the re-run is
rejected, the committed files and the original figure are restored, and the discrepancy is
reported here rather than absorbed into the manuscript.

**Result: the numbers reproduced exactly; the tables were nevertheless restored, and the reason is
a reproducibility gap worth recording.**

| Artefact | Comparison against the committed version | Action |
|---|---|---|
| `results/raw_mealpy.npz` | Every array shared with the committed file is **bit-identical** (`np.array_equal` on all 14 keys) | Committed file restored (see below) |
| `figures/mealpy_convergence.png` | **Byte-identical** to the committed figure | Kept |
| `table_mealpy_signal.md`, `table_mealpy_berth.md`, `table_berth_gap.md` | The seven CA + `mealpy` rows are **character-for-character identical**; the L-SHADE and CMA-ES rows are **absent** | Committed files restored |
| `figures/berth_best_plan.png` | Redrawn with the annotation; the objective it prints (6,278 min) and the gap (29.2 %) match the committed `table_berth_gap.md` (6277.9, 29.17 %), so it is the same plan | **Accepted** |

**The gap.** `src/mealpy_comparison.py` writes the three transportation tables and
`raw_mealpy.npz` with the seven CA + `mealpy` algorithms only; the L-SHADE and CMA-ES rows in the
committed versions are added afterwards by `src/sota_addon_run.py`. Running
`mealpy_comparison.py` on its own therefore **silently truncates** those files. Nothing in the
repository documents that ordering constraint. It is reported here, and the correct sequence is:

```bash
python src/mealpy_comparison.py    # CA + six mealpy algorithms
python src/sota_addon_run.py       # then adds L-SHADE and CMA-ES to the same tables
```

No number changed as a result: the committed tables were restored from a copy taken before the
re-run, and the only file the re-run contributed to the manuscript is the annotated berth figure,
whose printed objective and gap were checked against those restored tables.

---

## 6. Round 2 — follow-up fixes (2026-09-08, second pass)

A second QA pass, prompted by a full read-through of the rendered PDF, found and fixed four more
issues. None changed a committed number; all are confirmed by the same 52/52 validation run.

| # | Finding | Fix | Verified by |
|---|---|---|---|
| R1 | The best-plan time–space figure (§8.5) overflowed off the bottom of the page: two tall floats (the delay box plot of §8.4 and the seven-parameter table of §8.5) were competing for space on one page, and the figure lost. | Added an explicit `\clearpage` before §8.5, so the deferred box plot is flushed and the table + figure get a full fresh page. | Scanned every page's image bounding boxes against the text-block margins (`fitz`); zero overflowing images after the fix, versus one before it |
| R2 | The classical-suite convergence and box-plot figures plotted the **mean** of 30 runs while the traffic-signal convergence figure and every CEC/engineering figure plotted the **median** — an inconsistency, not a deliberate choice (flagged as V1 in the first pass). | Standardized on the **median** everywhere: a median best-so-far curve is not dragged by the single worst run the way a mean is on a log axis, which is the reason the CEC-2017/CEC-2022/engineering scripts already used it — the classical and traffic scripts were the outliers, not the rule. `run_benchmarks.py` and `traffic_case_study.py` were changed to match and re-run. | `benchmark_stats.csv`, `wilcoxon.csv`, `anova.csv`, `traffic_stats.csv`, `table_traffic.md`, `table_traffic_wilcoxon.md`, `best_ca_plan.md` compared byte-for-byte / `DataFrame.equals` against pre-run copies — all identical; only the two convergence figures' pixels changed |
| R3 | Structural placement, not correctness: the manuscript put Appendix A before the Data-and-code-availability note and the References list, and closed with a half-page author photo and biography. Checked against the actual structure of the paper's own presentation references (HHO, MGO, RIME — all Elsevier venues): those journals place the Appendix immediately before References, and none carries an author-biography section in the main text. | Reordered to Conclusions → Data and code availability → Appendix A → References; removed the "About the corresponding author" section entirely (the photo file is untouched in `assets/`, just unused). The reproducibility statement was also cut from a 30-line script inventory to a three-sentence paragraph pointing at `README.md`, which now carries that detail once instead of twice. | Re-rendered; `validate_presentation.py`'s cross-reference and include checks (which would fail on a broken `{{< include >}}` or moved label) still pass at 52/52 |
| R4 | The reproducibility gap identified in this report's §5 (`mealpy_comparison.py` alone silently omits L-SHADE/CMA-ES) had no guard against recurring. | Added `src/run_transportation_pipeline.py` as the one supported entry point (`mealpy_comparison.py` → `sota_addon_run.py --suite transport` → hard validation), a matching hard check in `validate_presentation.py`, and a "Transportation pipeline" subsection in `README.md`. | New checks §1.6, 52/52 total |

Nothing in this round touched a result value, an equation, a protocol, or a claim; R2 is the one
change that alters what a figure looks like, and it does so by picking one already-used convention
consistently rather than introducing a new one.
