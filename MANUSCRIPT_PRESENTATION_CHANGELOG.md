# MANUSCRIPT PRESENTATION CHANGELOG

Revision of *The Chess Algorithm: A Novel Metaheuristic Optimization Technique with Applications in
Transportation Network Engineering* in response to Dr. Seyedali Mirjalili's editorial review
(2026-08-31). Completed 2026-09-08.

**Scope.** Presentation only. No equation, protocol, seed, roster, result value, statistical test,
or claim was changed. Every number in every new table and figure is read from the committed result
files by a committed script; `src/validate_presentation.py` re-checks each of them against its
source and reports discrepancies rather than absorbing them (49/49 checks pass — see
`VALIDATION_REPORT.md`).

Change categories:

* `[DIRECT REQUEST FROM MIRJALILI]` — one of the three review comments
* `[SUPPORTED BY RECENT OPTIMIZATION LITERATURE]` — the presentation conventions of HHO (2019),
  MGO (2022), RIME (2023), GSO (2026), NTOA (2026), ORLGSFOA (2026), Aquila Optimizer (2021)
* `[EDITORIAL RECOMMENDATION]` — the revising author's judgement

---

## 1. Figures added

The manuscript went from 12 figures to 22. Ten are new, one was replaced, and none of the
pre-existing result figures had their data changed.

| New figure | Location | Change category | Why |
|---|---|---|---|
| **Fig. 1** Motivation and conceptual architecture | §1.1 | `[DIRECT REQUEST FROM MIRJALILI]` — "like to have some figures in the introduction" | The introduction had no figure at all; this one carries its argument (problem structure → limits of a homogeneous population → CA's two answers) |
| **Fig. 2** The chess abstraction as a mapping onto search operators | §1.3 | `[DIRECT REQUEST FROM MIRJALILI]` | States what each piece becomes mathematically, and marks each role as exploration- or exploitation-side, before any equation appears |
| **Fig. 3** One iteration of CA (architecture) | §2.2 (new subsection) | `[DIRECT REQUEST FROM MIRJALILI]` — "some in the proposed method to show the key mechanisms" | Replaces the generic flowchart with a diagram that separates the population strand, the King's local search, and the adaptive control signals |
| **Fig. 4** Heterogeneous role-based search geometry | §2.6 | `[DIRECT REQUEST FROM MIRJALILI]` | Shows what the five movement equations *do*: candidate clouds are 45 draws from each equation, evaluated with a fixed seed, not drawn by hand |
| **Fig. 5** Adaptive tactical controller | §2.11 | `[DIRECT REQUEST FROM MIRJALILI]`, `[SUPPORTED BY RECENT LITERATURE]` (NTOA presents its adaptive layer as a controller diagram) | The paper's most distinctive contribution existed only as prose plus a rate table |
| **Fig. 6** Geometry of the five tactical operators | §2.11.3 | `[DIRECT REQUEST FROM MIRJALILI]` | Five panels, one per operator, each generated from its own equation |
| **Fig. 10** CEC-2017 final-error distributions | §4.3 | `[SUPPORTED BY RECENT LITERATURE]` (box plots are standard in MGO/RIME/GSO) | Answers whether the ranking is carried by typical runs or outliers; uses the per-run finals already committed in `results/raw_cec2017.npz` |
| **Fig. 13** Mechanism contribution (ablation) | §7.1 | `[EDITORIAL RECOMMENDATION]` | The paper's strongest scientific story — two of twelve mechanisms carry the performance — had no visual form |
| **Fig. 14** Parameter sensitivity profile | §7.2 | `[SUPPORTED BY RECENT LITERATURE]` (RIME devotes a figure to parameter analysis) | Makes the one-at-a-time design and its local scope visible |
| **Fig. 15** Where CA stands (cross-suite Friedman ranks) | §7.4 (new subsection) | `[EDITORIAL RECOMMENDATION]` | Lets a reader see in one picture which algorithms outperform CA and where CA is competitive, instead of assembling it from three rank tables |
| **Fig. 17** From the arterial to the decision vector | §8.2 | `[EDITORIAL RECOMMENDATION]` | Connects the 16 decision variables to the physical network and shows why the objective is multimodal |

**Figure removed:** the original flowchart (`figures/ca_flowchart.png`) no longer appears in the
manuscript; Fig. 3 supersedes it. The file and its generating code remain in the repository.

## 2. Figure style

| Change | Category |
|---|---|
| Single algorithm-identity palette across every figure in the paper, in a new shared module `src/figstyle.py`. The classical-suite figures previously used a private palette, so the same algorithm changed colour between sections | `[EDITORIAL RECOMMENDATION]` |
| Line style used as a redundant second encoding (colour-blind and greyscale safe) in every multi-algorithm plot | `[EDITORIAL RECOMMENDATION]` |
| Harmonized axis labels on the convergence figures | `[EDITORIAL RECOMMENDATION]` |
| Schematic figures restricted to one restrained secondary palette; no gradients, no 3-D, no chess clip-art | `[EDITORIAL RECOMMENDATION]` |

## 3. Tables restructured — the core of the review

> "Presenting the tables in a way that columns show test functions and rows show the algorithms."

Every primary comparison table was transposed. `[DIRECT REQUEST FROM MIRJALILI]` throughout this
section.

| Table | Before | After |
|---|---|---|
| Classical suite (Table 6) | 36 rows, function-major, mean/std/best/worst | 6 rows (algorithms) × 6 function columns, `mean ± std`, best mean bold |
| Classical Wilcoxon (Table 8) | 30 rows, one per (function, comparison) | 5 rows (comparisons) × 6 function columns, $p$-value with a direction marker |
| Classical ANOVA (Table 7) | 6 rows | 2 rows ($F$, $p$) × 6 function columns |
| CEC-2017 (Tables 12–17) | **one 232-row table** | 6 tables, algorithms as rows, grouped by the **official** categories of the suite: unimodal (F1–F2), simple multimodal (F3–F9), hybrid (F10–F14, F15–F19), composition (F20–F24, F25–F29). No table exceeds six function columns |
| CEC-2022 (Tables 20–21) | one 128-row table | 2 tables, one per official dimensionality, 8 validated functions each |
| Engineering (Table 23) | 56 rows | 8 rows × 7 problem columns |
| Cost (Table 26) | 48 rows, problem-major | 8 rows × 6 problem columns + two summary columns |
| Signal timing (Table 27) | results table + separate Wilcoxon table | one table: mean ± std, best, worst, $p$ vs CA, outcome |

Supporting decisions:

| Decision | Category | Rationale |
|---|---|---|
| Cell format `mean ± std`, four significant digits (six for the signal-timing table, whose means differ only in the third decimal) | `[DIRECT REQUEST]` + `[EDITORIAL]` | The requested orientation cannot carry four statistics per cell |
| Best **mean** per function column in bold; a best *run* is never bolded | `[SUPPORTED BY RECENT LITERATURE]` | Standard in this literature (MGO, Aquila) |
| Rank table and win/tie/loss table merged into one "standing" table per suite (Tables 11, 19, 22), adding a "best mean on *n* of *N*" column | `[SUPPORTED BY RECENT LITERATURE]` (MGO puts a compact rank summary before the detail) | Removes a second lookup; makes the ordering scannable |
| The CEC-2017 grouping uses the **official** categories only, mapped through the manuscript's own `opfunu` renumbering footnote (label F*n* = official F(*n*+1) for *n* ≥ 2) | `[EDITORIAL]` | The brief forbids invented categories; the mapping is derived in `PRESENTATION_AUDIT.md` §H and checked by the validator |
| PDF tables typeset at `\scriptsize` inside `longtable`/`tabular` via `etoolbox`, with explicit `tbl-colwidths` | `[EDITORIAL]` | Fits wide tables on the A4 block without `\resizebox` rescaling |

## 4. Main text vs supplement

| Change | Category |
|---|---|
| New **Appendix A** (Tables 32–37) carries the full mean/std/**best/worst** statistics for every suite, the per-problem ablation detail (previously repository-only), and the per-problem cost detail | `[EDITORIAL RECOMMENDATION]` |
| Nothing was deleted: every relocated table is still generated by `src/generate_markdown_tables.py` and committed under `results/` | `[EDITORIAL RECOMMENDATION]` |
| Main-text result-table rows reduced from ≈ 640 to ≈ 210 | `[DIRECT REQUEST]` (consequence of the transposition) |

## 5. Text changed

Prose was rewritten only where the presentation changed under it.

| Change | Category |
|---|---|
| New §2.2 "Architecture overview" introducing Fig. 3 | `[DIRECT REQUEST]` |
| New §7.4 "Where CA stands", stating the cross-suite ordering and its two qualifications (rank compression, roster dependence) | `[EDITORIAL RECOMMENDATION]` |
| Sentences introducing each new figure, and the pointers from primary tables to their appendix counterparts | `[EDITORIAL RECOMMENDATION]` |
| The cost paragraph now describes the transposed table's columns | `[EDITORIAL RECOMMENDATION]` |
| The former "Flowchart" subsection replaced by one sentence tying the pseudocode to Fig. 3 | `[DIRECT REQUEST]` |
| **No performance claim was strengthened.** Every honest negative result — CA behind L-SHADE and CMA-ES everywhere, the 10–9–10 record against GA on CEC-2017, the loss to PSO on signal timing, the 29 % berth-allocation gap, CA-static beating CA on the classical suite — is retained verbatim, and the new Fig. 15 makes the first of them easier to see, not harder | `[EDITORIAL RECOMMENDATION]` |

## 6. Reproducibility

| Artefact | Status |
|---|---|
| `src/figstyle.py` | New: the shared visual language |
| `src/generate_transposed_tables.py` | New: every primary table |
| `src/make_concept_figures.py` | New: Figs. 1, 2, 17 |
| `src/make_method_figures.py` | New: Figs. 3–6 |
| `src/make_result_figures.py` | New: Figs. 10, 13, 14, 15 |
| `src/validate_presentation.py` | New: 48 numerical and structural checks |
| `src/generate_markdown_tables.py` | Unchanged; now feeds Appendix A |
| `src/run_benchmarks.py` | Figure styling only (shared palette, axis label); protocol, seeds and statistics untouched |
| `src/mealpy_comparison.py` | Berth-plan figure annotated with the known optimum, the plan's objective, its optimality gap and its residual overlap; the objective function, protocol and seeds are untouched. The re-run reproduced every committed number exactly (see `VALIDATION_REPORT.md` §5), which also exposed an undocumented ordering constraint: this script must be followed by `sota_addon_run.py` or the L-SHADE/CMA-ES rows are lost from the transportation tables |
| The "Data and code availability" section | Updated with the new scripts |
| `README.md` | Repository map and reproduction commands updated with the new scripts |
| `paper-fa.qmd` (Persian translation) | **Not updated.** It still mirrors the pre-revision English manuscript; bringing it in line is a separate translation task and is listed here so the gap is visible rather than silent |

## 7. Inconsistencies found and **reported rather than silently fixed**

| # | Finding | Action taken |
|---|---|---|
| K5/K7 | The classical-suite convergence figure averages the 30 runs, while its caption and axis label said *median*; the CEC and engineering figures do plot medians | The plotted quantity was **not** changed. The axis label now says "Mean best-so-far objective" and the manuscript caption is corrected to match what the code computes. Flagged here and in `VALIDATION_REPORT.md` for the authors' confirmation |
| K1 | The parameter table lists four role fractions summing to 0.60 without stating the Pawn remainder explicitly | Stated in the caption of Fig. 4 ("the Pawns taking the remainder"); no value changed |
| K3 | The classical six-function suite uses a different roster (SA present; WOA, L-SHADE, CMA-ES absent) from every other suite | Reported in the audit; Fig. 15 excludes that suite and says so in its caption |
| K6 | "Evals / core budget" exceeds 1 for every population method because the initial population evaluation lies outside $N \times T$ | Explained in the caption of Table 26; no value changed |

No discrepancy was found between any rendered number and its source file.
