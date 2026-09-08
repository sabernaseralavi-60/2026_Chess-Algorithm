# PRESENTATION AUDIT — Chess Algorithm manuscript

**Manuscript:** *The Chess Algorithm: A Novel Metaheuristic Optimization Technique with Applications in Transportation Network Engineering* (`paper.qmd`, 923 lines, Quarto → HTML + PDF).
**Audit date:** 2026-09-08.
**Trigger:** editorial feedback from Dr. Seyedali Mirjalili (invited co-author), 2026-08-31.

Dr. Mirjalili's three requests, verbatim:

> 1. "One suggestion is to present the results and improve the presentation in a more standard format. If you have a look at some of our recent optimization algorithms, they provide a good template to follow."
> 2. "Like to have some figures in the introduction and also have some in the proposed method to show the key mechanisms of the search method."
> 3. "Presenting the tables in a way that columns show test functions and rows show the algorithms."

This document is the **read-only** phase of the revision: it records what the manuscript currently
contains, what is wrong with the presentation, and what should change. No scientific content,
numeric result, equation, protocol, or claim is altered anywhere in this revision; every issue that
looks scientific rather than presentational is recorded in §K (Audit of possible scientific issues)
instead of being silently fixed.

Change categories used throughout:

| Tag | Meaning |
|---|---|
| `[DIRECT REQUEST]` | Explicitly requested by Dr. Mirjalili |
| `[STRONG PRESENTATION RECOMMENDATION]` | Follows from the presentation conventions of the reference papers in §B |
| `[OPTIONAL]` | Improves the paper but is not required |
| `[DO NOT CHANGE]` | Deliberately preserved |

---

## A. Current manuscript structure

| # | Section | Label | Content | Assessment |
|---|---|---|---|---|
| 1 | Introduction | — | Motivation, landscape map, "Why chess?", contributions | **No figures at all.** Text-only, 6 paragraphs. `[DIRECT REQUEST]` to fix |
| 2 | The Chess Algorithm | `sec-ca` | Mapping table, initialization, roles, movement operators, strategic mechanisms, parameters, pseudocode, flowchart, convergence proposition, adaptive control, operator-family mapping | **One figure** (a generic flowchart). 23 equations, no geometric illustration of any of them. `[DIRECT REQUEST]` to fix |
| 3 | Benchmark Experiments | `sec-benchmarks` | 6 classical functions, protocol, results, ANOVA, Wilcoxon | Tables function-major `[DIRECT REQUEST]` to transpose |
| 4 | CEC-2017 | `sec-cec2017` | Roster, `opfunu` data-integrity audit, restoration audit, results | 232-row stats table; function-major |
| 5 | CEC-2022 | `sec-cec2022` | Protocol, audit, results | 128-row stats table; function-major |
| 6 | Engineering design | `sec-engineering` | 7 constrained problems | 56-row stats table; function-major |
| 7 | Component/parameter/cost | `sec-analysis` | 12-mechanism ablation, OAT sensitivity, measured cost | **Three tables, zero figures** — the most information-dense section of the paper is entirely tabular |
| 8 | Signal coordination | `sec-transport` | 8-intersection arterial | Network sketch present; no figure connecting the network to the decision vector |
| 9 | mealpy comparison | `sec-mealpy` | 6 third-party algorithms + L-SHADE/CMA-ES, 2 transportation problems | Berth time–space diagram present but under-annotated |
| 10 | Conclusions | `sec-conclusions` | Summary, limitations, future work | Text-only; acceptable |

**Structural verdict.** The scientific content is complete and, by the standards of this literature,
unusually thorough (two data-integrity audits, a 12-mechanism ablation, an OAT sensitivity study, a
measured cost study, competition-grade baselines). The *presentation* does not match the content:
the paper reads as a technical report — a wall of prose interleaved with long tables — rather than
as a Q1 optimization article, in which the reader is carried by a figure sequence
(motivation → mechanism → benchmark → statistics → application).

---

## B. Presentation references consulted (Phase 2)

Presentation *principles* only were extracted; no wording, artwork, or graphical style is copied
(RULE 4).

| Ref | Paper | Principle extracted |
|---|---|---|
| A | Harris Hawks Optimization — Heidari et al. (2019), *FGCS*, 10.1016/j.future.2019.02.028 | Inspiration is introduced **conceptually first and mathematically second**, and each search phase gets its own geometric diagram before its equation. Exploration and exploitation phases are visually separated. |
| B | Mountain Gazelle Optimizer — Abdollahzadeh et al. (2022), *AES*, 10.1016/j.advengsoft.2022.103282 | Multi-suite results are carried by **compact rank summaries** (Friedman mean rank, W/T/L) placed *before* the detailed per-function tables; engineering problems are a separate validation block. |
| C | RIME (2023), *Neurocomputing*, 10.1016/j.neucom.2023.02.010 | Qualitative search-behaviour analysis, parameter analysis and statistical comparison are each given a dedicated, self-contained subsection with one figure that answers one question. |
| D | Glider Snake Optimizer — El-kenawy et al. (2026), *Artif. Intell. Rev.*, 10.1007/s10462-026-11504-x | Current (2026) template: conceptual figure in the introduction, mechanism figures in the method, grouped benchmark tables, rank/box-plot visual summaries. |
| E | NTOA — Ben Youssef et al. (2026), *KBS*, 10.1016/j.knosys.2026.116776 | Adaptive operator activation is presented as an explicit **state/controller diagram**, not as prose plus a parameter table. |
| F | ORLGSFOA (2026), *KBS*, 10.1016/j.knosys.2026.115522 | Every mechanism is presented with an explicit statement of *why it exists* and what failure mode it answers. |
| G | Aquila Optimizer (2021), *CIE*, 10.1016/j.cie.2021.107250 — presentation reference only, **not** a Mirjalili paper | Benchmark tables with algorithms on one axis and functions on the other, statistics stacked inside the cell, best value in bold. |

Distilled into five rules used for the rest of this revision:

1. **A figure precedes every mechanism it explains** (HHO, GSO).
2. **Rank summary before detail** (MGO).
3. **One figure = one scientific question** (RIME).
4. **The controller gets a diagram** (NTOA).
5. **Algorithms as rows, problems as columns, best in bold** (Aquila, MGO) — which is also request 3.

---

## C. Current figure inventory

12 figures. "Question answered" is the test of §17 of the revision brief.

| # | ID | File | Section | Question it answers | Verdict |
|---|---|---|---|---|---|
| 1 | `fig-flowchart` | `ca_flowchart.png` | Method | What is the iteration loop? | **Redesign.** Generic box-and-arrow flowchart; shows control flow but not a single *search mechanism*. Does not show roles, tactics, or the adaptive controller |
| 2 | `fig-convergence` | `convergence_all.png` | Classical suite | How fast does each algorithm converge on 6 classical functions? | Keep, **restyle** (uses a different palette from every other figure in the paper) |
| 3 | `fig-boxplots` | `boxplots_all.png` | Classical suite | How spread are the final values? | Keep, restyle |
| 4 | `fig-cec2017` | `cec2017_convergence.png` | CEC-2017 | Convergence on 6 representative functions | Keep; caption should justify the representative choice |
| 5 | `fig-cec2022` | `cec2022_convergence.png` | CEC-2022 | Convergence on 6 representative cells | Keep |
| 6 | `fig-engineering` | `engineering_convergence.png` | Engineering | Convergence on 7 design problems | Keep |
| 7 | `fig-network` | `traffic_network.png` | Transport | What is the test bed? | Keep; **does not connect the network to the decision vector** |
| 8 | `fig-traffic-conv` | `traffic_convergence.png` | Transport | Convergence on signal timing | Keep |
| 9 | `fig-traffic-box` | `traffic_boxplot.png` | Transport | Spread of final delays | Keep |
| 10 | `fig-plan` | `traffic_best_plan.png` | Transport | What does the best plan look like? | Keep |
| 11 | `fig-mealpy-convergence` | `mealpy_convergence.png` | mealpy | Convergence vs third-party implementations | Keep |
| 12 | `fig-berth-plan` | `berth_best_plan.png` | mealpy | Is CA's best berth plan feasible? | Keep; **optimality gap not annotated on the figure** |

**Distribution of figures across the paper:**

```
Introduction        0  ← Dr. Mirjalili's request 2
Method              1  ← Dr. Mirjalili's request 2 (a flowchart is not a mechanism figure)
Classical suite     2
CEC-2017            1
CEC-2022            1
Engineering         1
Analysis            0  ← ablation, sensitivity, cost: 3 tables, no figure
Transport           4
mealpy              2
Conclusions         0
```

Eleven of the twelve figures are result plots. **The paper contains no figure that explains how the
algorithm works.**

---

## D. Current table inventory

29 tables (`#tbl-` labels). Row counts are of the rendered body.

| ID | Rows | Orientation | Purpose | Verdict |
|---|---:|---|---|---|
| `tbl-mapping` | 15 | concept-major | Chess ↔ algorithm mapping | Keep `[DO NOT CHANGE]` |
| `tbl-params` | 8 | parameter-major | Parameter values | Keep |
| `tbl-phase-schedule` | 4 | phase-major | Phase-conditioned rates | Keep; **should also be shown as a diagram** (§E) |
| `tbl-operator-families` | 15 | mechanism-major | Metaphor→operator-family disclosure | Keep `[DO NOT CHANGE]` — this is the paper's answer to Sörensen |
| `tbl-suite` | 6 | function-major | Classical benchmark definitions | Keep (definition table, not a result table) |
| `tbl-stats` | 36 | **function-major** | Classical results (mean/std/best/worst) | **Transpose** `[DIRECT REQUEST]` |
| `tbl-anova` | 6 | function-major | ANOVA per function | Transpose to one row `[STRONG]` |
| `tbl-wilcoxon` | 30 | function-major | CA vs each competitor | **Transpose** `[DIRECT REQUEST]` |
| `tbl-opfunu-audit` | 6 | label-major | CEC-2017 exclusions | Keep `[DO NOT CHANGE]` — audit evidence |
| `tbl-cec2017-restoration` | 6 | label-major | Restoration evidence | Keep `[DO NOT CHANGE]` |
| `tbl-cec2017-ranks` | 8 | algorithm-major | Friedman ranks | Keep, **merge into one summary table** with W/T/L |
| `tbl-cec2017-wtl` | 7 | competitor-major | W/T/L vs CA | Merge into summary |
| `tbl-cec2017-stats` | **232** | **function-major** | Full per-function statistics | **Transpose + group by official category** `[DIRECT REQUEST]` |
| `tbl-cec2022-audit` | 6 | cell-major | CEC-2022 exclusions | Keep `[DO NOT CHANGE]` |
| `tbl-cec2022-ranks` | 8 | algorithm-major | Friedman ranks | Merge into summary |
| `tbl-cec2022-wtl` | 7 | competitor-major | W/T/L | Merge into summary |
| `tbl-cec2022-stats` | **128** | **function-major** | Full per-cell statistics | **Transpose, split by dimensionality** `[DIRECT REQUEST]` |
| `tbl-engineering-ranks` | 8 | algorithm-major | Friedman ranks | Merge into summary |
| `tbl-engineering-wtl` | 7 | competitor-major | W/T/L | Merge into summary |
| `tbl-engineering-stats` | **56** | **function-major** | Full per-problem statistics | **Transpose** `[DIRECT REQUEST]` |
| `tbl-ablation` | 12 | mechanism-major | Ablation ratios | Keep table, **add figure** `[STRONG]` |
| `tbl-sensitivity` | 10 | variant-major | OAT sensitivity | Keep table, **add figure** `[STRONG]` |
| `tbl-timing` | **48** | **problem-major** | Cost per problem × algorithm | **Transpose** `[DIRECT REQUEST]` |
| `tbl-traffic` | 5 | algorithm-major | Signal-timing results | Already correct orientation; merge with Wilcoxon |
| `tbl-traffic-wilcoxon` | 4 | comparison-major | CA vs competitors | Merge into `tbl-traffic` |
| `tbl-plan` | 8 | intersection-major | Best plan | Keep `[DO NOT CHANGE]` |
| `tbl-mealpy-signal` | 9 | algorithm-major | P1 results | Already correct orientation |
| `tbl-mealpy-berth` | 9 | algorithm-major | P2 results | Already correct orientation |
| `tbl-berth-gap` | 9 | algorithm-major | Optimality gap | Keep `[DO NOT CHANGE]` |

**Total main-text table rows: ≈ 640.** Of these, **416 rows (65 %)** sit in three
function-major statistics tables that a reader cannot scan horizontally to compare algorithms —
exactly the defect request 3 identifies.

---

## E. Problems with readability

| # | Problem | Evidence | Fix |
|---|---|---|---|
| E1 | Result tables are function-major, so comparing two algorithms on one function requires reading 8 non-adjacent rows | `results/table_cec2017_stats.md`: 232 rows, 29 blocks of 8 | Transpose: algorithms as rows, functions as columns `[DIRECT REQUEST]` |
| E2 | The 232-row CEC-2017 table spans several printed pages and cannot be read as a unit | `tbl-cec2017-stats` | Split by official CEC-2017 category (unimodal / simple multimodal / hybrid / composition) |
| E3 | Ranks and W/T/L are in separate tables, so "who leads and by how much" needs two lookups per suite | `tbl-cec2017-ranks` + `tbl-cec2017-wtl` (and the same pair ×3 suites) | One summary table per suite: rank, rank position, W/T/L vs CA, count of best means |
| E4 | Paragraphs carry numbers that the reader must hold in memory while reading (e.g. the six-rank list in §CEC-2017 Discussion) | line 624 of `paper.qmd` | Keep the prose, but let the summary table and the cross-suite rank figure carry the numbers |
| E5 | The abstract is a single 700-word paragraph | lines 14 | `[OPTIONAL]` — out of scope for a presentation revision; left unchanged |
| E6 | Cost table interleaves 6 problems × 8 algorithms in problem-major order | `tbl-timing` | Transpose: algorithms as rows, problems as columns |

---

## F. Problems with visual communication

| # | Problem | Fix |
|---|---|---|
| F1 | **No figure in the Introduction.** The reader reaches the mathematics without a picture of the idea | New conceptual figure(s) `[DIRECT REQUEST]` |
| F2 | **No mechanism figure in the method.** Twenty-three equations, zero geometry. A reader cannot see what a Rook move, a fork, or a council probe *does* in the search space | New mechanism figures `[DIRECT REQUEST]` |
| F3 | The adaptive controller — the paper's most distinctive contribution — exists only as a table of rates and two inequalities | State-machine diagram `[DIRECT REQUEST]` (mechanism figure) |
| F4 | Two different colour palettes are in use: `run_benchmarks.py` (`#1a1a2e`/`#c0392b`/…) vs `phase2_3_analysis.py` (`#1d4ed8`/`#c2410c`/…). The same algorithm is a different colour in different figures | Single shared style module `[STRONG]` |
| F5 | The ablation — the paper's strongest scientific story — has no visual form | Ablation contribution figure `[STRONG]` |
| F6 | CA's honest standing (competitive with classical, behind L-SHADE/CMA-ES) must be assembled by the reader from four separate rank tables | Cross-suite rank figure `[STRONG]`, §21 of the brief |
| F7 | The signal-timing decision vector (16 variables) is never drawn against the network | Signal-timing model figure `[STRONG]` |
| F8 | The berth figure does not mark the optimality gap or the known optimum | Annotate `[STRONG]` |
| F9 | Distribution information exists only for the classical suite and signal timing; CEC-2017 run-to-run spread is invisible | Add one distribution figure for the 6 representative CEC-2017 functions (per-run finals are committed in `results/raw_cec2017.npz`) `[STRONG]` |

---

## G. Problems with table orientation `[DIRECT REQUEST]`

Current primary comparison format:

```
| Function | Algorithm | Mean | Std | Best | Worst |
| F1       | CA        | ...  | ... | ...  | ...   |
| F1       | CA-static | ...  | ... | ...  | ...   |
   ... 8 rows per function, 29 functions = 232 rows
```

Required format:

```
| Algorithm | F1 | F2 | F3 | ... |
| CA        | mean ± std | ... |
| CA-static | mean ± std | ... |
   ... 8 rows total per function group
```

Consequences that must be handled rather than ignored:

1. **Best/worst do not fit** in a transposed primary table. Per §7 of the brief they move to a
   supplementary table that retains the full four statistics — nothing is deleted, only relocated,
   and each primary cell remains traceable to the supplement and to the source CSV.
2. **Width.** 29 functions cannot be one table. Grouping follows the *official* CEC-2017
   categories (§H), never invented ones.
3. **Bolding** marks the best *mean* per function column only — never a best run.

---

## H. CEC-2017 grouping (official categories only)

The manuscript's labels follow `opfunu`'s consecutive renumbering after the withdrawal of official
F2; footnote `cec-numbering` states label F*n* = official F(*n*+1) for *n* ≥ 2. Mapping the paper's
labels onto the official categories of Awad et al. (2017) therefore gives:

| Official category | Official functions | **Paper labels** | Count |
|---|---|---|---:|
| Unimodal | F1, F3 (F2 withdrawn) | **F1, F2** | 2 |
| Simple multimodal | F4–F10 | **F3–F9** | 7 |
| Hybrid | F11–F20 | **F10–F19** | 10 |
| Composition | F21–F30 | **F20–F29** | 10 |
| | | | **29** |

Cross-check against the manuscript's own function names: label F1 = Bent Cigar (official F1,
unimodal) ✓; label F4 = Rastrigin (official F5, simple multimodal) ✓; label F13 = Hybrid 4
(official F14, hybrid) ✓; label F22 = Composition 3 (official F23, composition) ✓. The grouping
is therefore derived from the suite definition, not invented.

CEC-2022 is grouped by its two official dimensionalities (D = 10, D = 20), 8 validated cells each.

---

## I. Redundancies

| # | Redundancy | Action |
|---|---|---|
| I1 | Ranks table + W/T/L table for each of three suites (6 tables) | Merge into 3 summary tables `[STRONG]` |
| I2 | `tbl-traffic` + `tbl-traffic-wilcoxon` | Merge (p-value becomes a column) `[STRONG]` |
| I3 | The classical-suite ANOVA table (6 rows × 2 numbers) is a full table for one sentence | Transpose to a two-row table `[OPTIONAL]` |
| I4 | The flowchart and a new architecture diagram would overlap | The architecture diagram replaces the flowchart in the manuscript; `ca_flowchart.png` stays in the repository `[STRONG]` |
| I5 | Full per-function stats appear once in the main text and once in `results/latex_tables_final.tex` | Keep both; they serve different consumers `[DO NOT CHANGE]` |

---

## J. Missing scientific visuals

| # | Missing visual | Scientific question it would answer | Priority |
|---|---|---|---|
| J1 | Motivation / conceptual architecture | *Why does a heterogeneous, adaptively scheduled search population make sense at all?* | `[DIRECT REQUEST]` |
| J2 | Chess → optimization abstraction | *What exactly does each piece become, mathematically?* | `[DIRECT REQUEST]` |
| J3 | Role-based search geometry | *How do the five role operators differ in the search space, and which explore vs exploit?* | `[DIRECT REQUEST]` |
| J4 | Tactical operator geometry | *Where does each tactical probe place a candidate relative to the King and the elite?* | `[DIRECT REQUEST]` |
| J5 | Adaptive state machine | *What does the controller read, and what does it switch?* | `[DIRECT REQUEST]` |
| J6 | Integrated architecture | *What is one CA iteration, end to end?* | `[DIRECT REQUEST]` (replaces flowchart) |
| J7 | Mechanism contribution (ablation) | *Which mechanisms actually carry the performance?* | `[STRONG]` |
| J8 | Parameter sensitivity profile | *Which parameters does a practitioner have to tune?* | `[STRONG]` |
| J9 | Cross-suite rank standing | *Where does CA stand against classical and against competition-grade methods?* | `[STRONG]` (§21) |
| J10 | CEC-2017 final-value distributions | *Is CA's ranking driven by means or by outliers?* | `[STRONG]` |
| J11 | Signal-timing model | *How does the arterial map onto 16 decision variables?* | `[STRONG]` |

---

## K. Audit of possible scientific issues (reported, **not** changed)

Per RULE 2, these are recorded here rather than acted on.

| # | Observation | Location | Status |
|---|---|---|---|
| K1 | `tbl-params` lists role fractions summing to 0.60, with Pawns taking the remainder (0.40). This is consistent with the text and the code, but the table never states the Pawn fraction explicitly | line 267 | **Presentation gap only.** The revised parameter table may state the Pawn remainder; no value changes |
| K2 | The abstract states CA "loses only once … across 35 comparisons" on engineering; `tbl-engineering-wtl` is the source. Verified consistent | line 14 / 698 | No action |
| K3 | Classical-suite roster (CA, CA-static, GA, PSO, SA, GWO) differs from the 8-algorithm roster used everywhere else; SA appears only there and WOA/L-SHADE/CMA-ES do not appear at all | §benchmarks | **Reported.** The cross-suite rank figure therefore covers only the three suites sharing the 8-algorithm roster; this limitation is stated in its caption |
| K4 | `results/table_ablation.md` reports the en-passant ratio as 603.3 while the prose says "roughly 600" and "a factor of 3.6×10³ on Bent Cigar" — the per-problem detail file gives 3610.7 for F1. Consistent | 712 | No action |
| K5 | The convergence figures label the y-axis "Median error $f-f^*$" (CEC) vs "Best fitness (log)" (classical) vs "Median objective" (engineering) — three different phrasings for closely related quantities | figures | **Presentation.** Harmonized in the revision; the plotted quantity itself is unchanged |
| K6 | `tbl-timing` "Evals / core budget" for GWO/PSO/GA is 1.002, i.e. the N×T core budget plus the initial population evaluation. Correct, but the ratio's definition deserves a caption sentence | 732 | Caption clarified; numbers unchanged |

No discrepancy was found that requires a change to any result.

---

## L. Recommended new manuscript architecture

Changes are marked; everything unmarked stays where it is.

```
1  Introduction
     1.1 Motivation                       + FIG 1  Motivation & conceptual architecture   [DIRECT]
     1.2 Metaheuristic landscape
     1.3 Why chess?                       + FIG 2  Chess → optimization abstraction        [DIRECT]
     1.4 Contributions and scope
2  The Chess Algorithm
     2.1 Conceptual mapping               (tbl-mapping)
     2.2 Architecture overview            + FIG 3  Integrated CA architecture (replaces flowchart) [DIRECT]
     2.3 Initialization / roles           + FIG 4  Heterogeneous role-based search geometry  [DIRECT]
     2.4 Movement operators
     2.5 Strategic mechanisms
     2.6 Parameters, pseudocode
     2.7 Adaptive tactical control        + FIG 5  Tactical operator geometry (5 panels)    [DIRECT]
                                          + FIG 6  Adaptive state machine                   [DIRECT]
     2.8 Operator-family mapping
3  Benchmark experiments (classical)      TABLES TRANSPOSED                                 [DIRECT]
4  CEC-2017                               SUMMARY TABLE + 4 CATEGORY TABLES (transposed)    [DIRECT]
                                          + FIG 8  final-value distributions                [STRONG]
5  CEC-2022                               SUMMARY TABLE + 2 DIMENSION TABLES (transposed)   [DIRECT]
6  Engineering design                     SUMMARY TABLE + 1 TABLE (transposed)              [DIRECT]
7  Component, parameter and cost analysis + FIG 10 mechanism contribution                   [STRONG]
                                          + FIG 11 parameter sensitivity                    [STRONG]
                                          COST TABLE TRANSPOSED                             [DIRECT]
   7.4 Where CA stands (new subsection)    + FIG 12 cross-suite Friedman ranks               [STRONG, §21]
8  Transportation: signal coordination    + FIG 13 optimization model ↔ network             [STRONG]
9  Extended comparison (mealpy)           berth figure annotated with the optimum & gap     [STRONG]
10 Conclusions
Appendix A  Supplementary tables: full mean/std/best/worst, per-function, all suites        [STRONG, §19]
```

Figure count: 12 → 20 (8 new: 2 introduction, 4 method, 4 analysis/application, minus the
flowchart which is replaced). Main-text result-table rows: ≈ 640 → ≈ 210, with the removed detail
relocated (not deleted) to Appendix A and to the committed CSV/markdown files.

---

## M. Per-change register

| Change | Current location | New location | Reason | Category |
|---|---|---|---|---|
| Add motivation figure | — | §1.1 | Request 2; HHO/GSO convention | `[DIRECT REQUEST]` |
| Add chess→optimization abstraction figure | — | §1.3 | Request 2 | `[DIRECT REQUEST]` |
| Replace flowchart with architecture diagram | §2 flowchart | §2.2 | Request 2; flowchart shows control flow, not mechanism | `[DIRECT REQUEST]` |
| Add role-geometry figure | — | §2.4 | Request 2 | `[DIRECT REQUEST]` |
| Add tactical-operator geometry figure | — | §2.7 | Request 2 | `[DIRECT REQUEST]` |
| Add state-machine figure | — | §2.7 | Request 2; NTOA convention | `[DIRECT REQUEST]` |
| Transpose classical results table | §3 | §3 | Request 3 | `[DIRECT REQUEST]` |
| Transpose + group CEC-2017 table | §4 | §4 + Appendix A | Request 3 + readability | `[DIRECT REQUEST]` |
| Transpose + split CEC-2022 table | §5 | §5 + Appendix A | Request 3 | `[DIRECT REQUEST]` |
| Transpose engineering table | §6 | §6 + Appendix A | Request 3 | `[DIRECT REQUEST]` |
| Transpose cost table | §7.3 | §7.3 | Request 3 | `[DIRECT REQUEST]` |
| Transpose Wilcoxon table | §3 | §3 | Request 3 | `[DIRECT REQUEST]` |
| Merge rank + W/T/L into one summary per suite | §4, §5, §6 | §4, §5, §6 | MGO convention; removes a lookup | `[STRONG]` |
| Add ablation figure | — | §7.1 | The paper's key scientific story is invisible | `[STRONG]` |
| Add sensitivity figure | — | §7.2 | RIME convention | `[STRONG]` |
| Add cross-suite rank figure + "Where CA stands" | — | §7.4 | Brief §21 | `[STRONG]` |
| Add CEC-2017 distribution figure | — | §4 | Brief §11; data available | `[STRONG]` |
| Add signal-timing model figure | — | §8.2 | Brief §15 | `[STRONG]` |
| Annotate berth figure with optimum and gap | §9 | §9 | Brief §15 | `[STRONG]` |
| Unify the two colour palettes | figures | figures | Brief §16 | `[STRONG]` |
| Harmonize convergence axis labels | figures | figures | Brief §10 | `[STRONG]` |
| Move best/worst statistics to Appendix A | §3–§6 | Appendix A | Brief §19; required by transposition | `[STRONG]` |
| Keep both data-integrity audit tables in the main text | §4, §5 | unchanged | Brief §8: audits must not be hidden | `[DO NOT CHANGE]` |
| Keep the operator-family table | §2.8 | unchanged | The paper's answer to the metaphor critique | `[DO NOT CHANGE]` |
| Keep every honest negative result and its wording | throughout | unchanged | RULE 3 | `[DO NOT CHANGE]` |
| Keep all equations, protocols, seeds, rosters | throughout | unchanged | RULE 2 | `[DO NOT CHANGE]` |

---

## N. Reproducibility constraints discovered during the audit

| Artefact | Regenerable without re-running experiments? | Consequence |
|---|---|---|
| All transposed tables | **Yes** — from `results/*.csv` | New generator script; no re-runs |
| Ablation / sensitivity / rank / distribution figures | **Yes** — from `results/*.csv` and `results/raw_*.npz` (per-run finals are committed) | New figure script; no re-runs |
| Conceptual and mechanism figures | **Yes** — schematic, drawn from the equations already in the manuscript | No data involved |
| Classical-suite convergence curves | **No** — per-iteration curves are not archived (`raw_finals.npz` stores final values only) | Re-running `run_benchmarks.py` is required to restyle them; seeds are fixed, so the re-run must reproduce `results/benchmark_stats.csv` **exactly**, and the validation script checks this |
| mealpy convergence / berth-plan figures | **No** — curves and best-x are not archived in `raw_mealpy.npz` | Same treatment; annotation added on re-run |

**Rule adopted for this revision:** no figure or table cell is typed by hand. Every number is read
from a committed result file by a committed script, and any re-run must reproduce the committed
statistics bit-for-bit before its output is accepted (checked in `VALIDATION_REPORT.md`).
