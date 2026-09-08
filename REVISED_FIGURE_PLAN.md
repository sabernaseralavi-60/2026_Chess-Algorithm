# REVISED FIGURE PLAN

Every figure below states the single scientific question it answers (brief §17). A figure with no
such question is not in this plan. All figures are produced by committed scripts from committed
data; no figure contains a hand-typed number.

**Shared visual language** (`src/figstyle.py`, new): serif type family, 10 pt base / 8 pt axis /
7.5 pt tick, `figure.dpi = savefig.dpi = 300`, top and right spines removed, one algorithm-identity
palette used in every figure of the paper, line style as a redundant (colour-blind- and
print-safe) second encoding, panel labels `(a) (b) (c)` in the upper-left of multi-panel figures,
consistent arrow style (`-|>`, 0.9 pt) and a single neutral box fill for schematic figures.

Algorithm identity palette (carried over unchanged from `phase2_3_analysis.py`, which was already
validated for lightness band, chroma floor, CVD separation and contrast):

| CA | CA-static | GWO | PSO | GA | WOA | L-SHADE | CMA-ES | SA |
|---|---|---|---|---|---|---|---|---|
| `#1d4ed8` | `#c2410c` | `#059669` | `#be123c` | `#a16207` | `#9333ea` | `#0891b2` | `#65a30d` | `#7c3aed` |

Schematic figures use a restrained secondary palette: incumbent/King `#1d4ed8`, elite peers
`#0f766e`, candidate/probe `#c2410c`, neutral structure `#475569`, fills `#f1f5f9` /
`#e2e8f0`. No gradients, no 3-D, no chess clip-art, no decorative icons (brief §16).

---

## New figures

### FIG 1 — `fig-motivation`
* **Caption (proposed).** *From problem structure to algorithmic response. Transportation and
  engineering design objectives are non-convex, multimodal and often expensive to evaluate (left);
  a homogeneous population applies one update rule to every agent and schedules its
  exploration–exploitation transition on elapsed time alone (centre); CA answers both properties
  with heterogeneous, rank-assigned roles and a controller that schedules tactics on the observed
  state of the population (right).*
* **Location.** §1.1 Motivation, immediately after @eq-problem.
* **Question answered.** Why does a heterogeneous, state-scheduled search population make sense at
  all?
* **Content.** Three-column diagram. Left: problem characteristics (non-convexity, many local
  optima, non-differentiability, expensive evaluation) with a small 1-D multimodal landscape sketch
  drawn from an actual analytic function. Centre: the two structural limitations named in §1.2 of
  the manuscript (identical agents; time-only transition). Right: CA's two answers (heterogeneous
  roles; adaptive phase control) converging into the exploration–exploitation balance box.
* **Data / source.** No experimental data. Every claim in the boxes is a restatement of manuscript
  lines 75–83 (Motivation and landscape), with the landscape sketch generated analytically.
* **New or redesigned.** New. `[DIRECT REQUEST]`
* **Script.** `src/make_concept_figures.py::fig_motivation`
* **Size.** 7.2 × 3.0 in, `width="100%"`.
* **Placement.** Main text.

### FIG 2 — `fig-abstraction`
* **Caption (proposed).** *The chess abstraction, stated as a mapping onto search operators. Each
  piece contributes one movement geometry around the incumbent King, and each is an instance of an
  established operator family (right column, with @tbl-operator-families giving the canonical
  reference). The metaphor names the composition; it does not supply an operator that the operator
  column cannot.*
* **Location.** §1.3 "Why chess?", after the paragraph introducing the pieces.
* **Question answered.** What, precisely, does each piece become mathematically — and does the
  metaphor add anything beyond vocabulary?
* **Content.** Two-column mapping. Left: King, Queen, Rook, Bishop, Knight, Pawn, each with a
  minimal 2-D geometry glyph (a circle sweep, an axis segment, a diagonal pair, an L-jump, a short
  advance) drawn to scale from the corresponding equation. Right: incumbent / omnidirectional
  perturbation / single-axis / two-axis / peer-guided jump + long-range leap / local exploitation,
  and the operator family. Colour codes exploration vs exploitation.
* **Data / source.** @eq-queen, @eq-rook, @eq-bishop, @eq-knight, @eq-pawn and
  @tbl-operator-families. No experimental data.
* **New or redesigned.** New. `[DIRECT REQUEST]`
* **Script.** `src/make_concept_figures.py::fig_abstraction`
* **Size.** 7.2 × 3.6 in, `width="92%"`.
* **Placement.** Main text.

### FIG 3 — `fig-architecture` (replaces `fig-flowchart`)
* **Caption (proposed).** *One iteration of CA. Ranking assigns roles, roles move under their own
  geometry, the controller of @sec-adaptive reads four statistics of the population and conditions
  which tactical operators fire, candidates are evaluated and accepted (improvements always, worse
  minor pieces under @eq-sacrifice), the King is updated by its own probes, and re-ranking
  implements promotion. Dashed arrows are control signals, solid arrows are population flow.*
* **Location.** §2.2 (new "Architecture overview" subsection), replacing the flowchart at line 323.
* **Question answered.** What happens, end to end, in one CA iteration, and where does the adaptive
  layer intervene?
* **Content.** Population → role assignment → role movement → strategic operators → controller
  (dashed control edges into role movement, tactical probes and the sacrifice budget) → evaluation
  → acceptance → King update (en passant / castling / windmill / blockade) → re-ranking →
  termination. Every box is annotated with the equation or section that defines it.
* **Data / source.** Pseudocode at lines 280–317 of `paper.qmd`; no numbers.
* **New or redesigned.** New; supersedes `figures/ca_flowchart.png` in the manuscript. The old file
  stays in the repository. `[DIRECT REQUEST]`
* **Script.** `src/make_method_figures.py::fig_architecture`
* **Size.** 7.4 × 4.6 in, `width="100%"`.
* **Placement.** Main text.

### FIG 4 — `fig-roles`
* **Caption (proposed).** *Heterogeneous role-based search. (a) Ranking partitions the population
  each iteration into King, Queens, Rooks, Bishops, Knights and Pawns in the fixed proportions of
  @tbl-params. (b)–(f) The move geometry of each role in a two-dimensional section of the search
  space: the King (blue) is the incumbent, grey points are population members, and orange points
  are candidates produced by that role's operator. The bar at the bottom of each panel records
  whether the role's principal contribution is exploration, exploitation or diversification.*
* **Location.** §2.4 Piece movement operators, before @eq-queen.
* **Question answered.** How do the five role operators differ geometrically, and which of them
  explore rather than exploit?
* **Content.** Panel (a): the rank partition as a horizontal band with the role fractions.
  Panels (b)–(f): Queen (isotropic sweep at the current King distance), Rook (single-axis),
  Bishop (two-axis equal-magnitude), Knight (drift to a better-ranked peer + 2:1 jump, plus the
  long-range leap shown as a separate arrow), Pawn (double drift toward K and toward a better
  peer). Each panel carries its equation number.
* **Data / source.** Candidate clouds are **sampled from the manuscript's own equations**
  (@eq-queen–@eq-pawn) with a fixed seed, not drawn by hand; the script implements the same
  formulas as `src/algorithms.py`.
* **New or redesigned.** New. `[DIRECT REQUEST]`
* **Script.** `src/make_method_figures.py::fig_roles`
* **Size.** 7.4 × 4.4 in, `width="100%"`.
* **Placement.** Main text.

### FIG 5 — `fig-tactics`
* **Caption (proposed).** *Geometry of the five tactical operators of @sec-adaptive, each in a
  two-dimensional section. (a) En passant: three masked Gaussian trials at the adaptive radius σ,
  which is multiplied by 1.3 after a success and by 0.92 after a failure (@eq-enpassant).
  (b) Knight's fork: a drift toward the King plus the difference vector of two better-ranked peers
  (@eq-fork). (c) Royal council: the King reflected away from the midpoint of the best Queen and
  best Rook (@eq-council). (d) Novotny interference: convex recombination of two members of the
  fitter half (@eq-interference). (e) Discovered attack: extrapolation through the King along an
  elite–King line (@eq-discovered). Blue = incumbent King, teal = elite peers, orange = candidate.*
* **Location.** §2.7, opening the "New tactical operators" subsection.
* **Question answered.** Where does each tactical probe place a candidate relative to the incumbent
  and the elite?
* **Content.** Five panels, each with current point(s), candidate point(s), vectors, labels, and
  the equation reference; the en-passant panel additionally shows the success-rule radius update as
  two concentric dashed circles.
* **Data / source.** Points generated from @eq-enpassant, @eq-fork, @eq-council,
  @eq-interference, @eq-discovered with a fixed seed. No interpretation is added beyond the
  equations themselves.
* **New or redesigned.** New. `[DIRECT REQUEST]`
* **Script.** `src/make_method_figures.py::fig_tactics`
* **Size.** 7.4 × 3.2 in, `width="100%"`.
* **Placement.** Main text.

### FIG 6 — `fig-statemachine`
* **Caption (proposed).** *The adaptive tactical controller. Four smoothed statistics — population
  divergence d̃ (@eq-divergence), initiative α (@eq-acceptance), en-passant success rate ε
  (@eq-epsilon) and the fifty-move stagnation counter s (@eq-fifty-move) — are read every
  iteration. Divergence and elapsed budget select one of four phases by the thresholds of
  @eq-phase; each phase activates the operator rates of @tbl-phase-schedule, reproduced in the
  lower panel. Two overlays act independently of the phase: zugzwang halves the development
  coefficient when initiative and local-search success are simultaneously low (@eq-zugzwang), and
  the blockade response fires at s ≥ 25 (@sec-blockade).*
* **Location.** §2.7, opening "Adaptive tactical control".
* **Question answered.** What does the controller read, and what exactly does it switch?
* **Content.** Upper panel: four input statistics → controller → four phase states with the
  literal transition conditions of @eq-phase on the edges; the two overlays enter as dashed
  edges. Lower panel: the phase-conditioned rate schedule of @tbl-phase-schedule drawn as a
  small heat-strip per parameter, with the numeric value printed in each cell — **values read
  directly from the manuscript table, none invented**.
* **Data / source.** @eq-phase, @eq-zugzwang, @tbl-phase-schedule (values hard-coded in the script
  from the manuscript table and checked by `src/validate_presentation.py`).
* **New or redesigned.** New. `[DIRECT REQUEST]`
* **Script.** `src/make_method_figures.py::fig_statemachine`
* **Size.** 7.4 × 5.0 in, `width="100%"`.
* **Placement.** Main text.

### FIG 8 — `fig-cec2017-dist`
* **Caption (proposed).** *Distribution of final error over 30 runs on the same six representative
  CEC-2017 functions as @fig-cec2017 (log scale; boxes are the interquartile range, whiskers the
  1.5 IQR rule, points the outliers). The functions are those spanning the four official
  categories, chosen before the results were examined and identical to the convergence panel;
  they are not selected for CA's advantage — F4 and F22 are among the functions on which CA is
  beaten by both competition-grade methods.*
* **Location.** §4 Results, after @fig-cec2017.
* **Question answered.** Is the CEC-2017 ranking driven by means or by outliers — and how does
  CA's run-to-run variability compare with that of L-SHADE and CMA-ES?
* **Content.** 2 × 3 box plots, 8 algorithms per panel, identity palette.
* **Data / source.** `results/raw_cec2017.npz` per-run finals (30 per algorithm-function pair) —
  already committed; no re-run required.
* **New or redesigned.** New. `[STRONG PRESENTATION RECOMMENDATION]` (brief §11)
* **Script.** `src/make_result_figures.py::fig_cec2017_distributions`
* **Size.** 11.0 × 6.2 in, `width="100%"`.
* **Placement.** Main text.

### FIG 10 — `fig-ablation`
* **Caption (proposed).** *Mechanism contribution. For each of CA's twelve mechanisms, the bar
  gives the ratio of the mean final error obtained with that mechanism disabled to the mean final
  error of full CA, averaged over the six problems of @sec-ablation (log scale; a ratio above 1
  means the ablated variant is worse, i.e. the mechanism helps). The marker count above each bar
  is the number of the six problems on which the Wilcoxon rank-sum difference is significant at
  α = 0.05. The right panel gives the per-problem ratio for the two load-bearing mechanisms. The
  metric is a ratio of means, not an "importance score": it is defined only relative to full CA
  under one-at-a-time removal, and mechanisms with overlapping function can each appear
  individually dispensable.*
* **Location.** §7.1, after @tbl-ablation.
* **Question answered.** Which of CA's twelve mechanisms actually carry its performance?
* **Content.** Left: horizontal log-scale bars, ordered by ratio, coloured by significance count,
  with a reference line at ratio = 1. Right: per-problem ratios for en passant and the knight's
  fork across the six problems.
* **Data / source.** `results/ablation_ratios.csv` (per problem × mechanism ratio, p-value,
  significance) and `results/table_ablation.md`. Nothing is recomputed beyond averaging what the
  ablation script already produced.
* **New or redesigned.** New. `[STRONG]` (brief §12)
* **Script.** `src/make_result_figures.py::fig_ablation`
* **Size.** 9.6 × 4.2 in, `width="100%"`.
* **Placement.** Main text.

### FIG 11 — `fig-sensitivity`
* **Caption (proposed).** *One-at-a-time parameter sensitivity. Each row perturbs one parameter
  group of @tbl-params around the published default, holding all others fixed; the marker gives
  the ratio of the perturbed configuration's mean final error to the default's, averaged over the
  six problems of @sec-ablation, and the horizontal line spans the per-problem range. Filled
  markers indicate at least one statistically significant per-problem deviation. Because the
  design is one-at-a-time, these are local sensitivities around one configuration, not a global
  sensitivity analysis: interactions between parameters are not measured.*
* **Location.** §7.2, after @tbl-sensitivity.
* **Question answered.** Which parameters does a practitioner actually have to tune?
* **Content.** Dot-and-range plot on a log ratio axis, ordered by mean ratio, reference line at 1,
  role-fraction rows visually separated from the rest.
* **Data / source.** `results/sensitivity_ratios.csv` (per problem × variant ratio, p-value).
* **New or redesigned.** New. `[STRONG]` (brief §13)
* **Script.** `src/make_result_figures.py::fig_sensitivity`
* **Size.** 7.4 × 4.0 in, `width="88%"`.
* **Placement.** Main text.

### FIG 12 — `fig-standing`
* **Caption (proposed).** *Where CA stands. Mean Friedman rank of each algorithm (lower is better)
  on the three suites evaluated under the identical eight-algorithm roster and protocol: CEC-2017
  (29 validated functions), CEC-2022 (16 validated cells) and the seven constrained engineering
  design problems. The ordering is stable across all three suites: the two competition-grade
  methods lead, CA is the best of the remaining six, and CA-static follows it. The classical
  six-function suite of @sec-benchmarks is not shown because it was run under a different roster
  (it includes SA and excludes WOA, L-SHADE and CMA-ES).*
* **Location.** §7.4 (new "Where CA stands" subsection), closing the analysis section.
* **Question answered.** In one picture: which algorithms outperform CA, where is CA competitive,
  and is that ordering stable across suites?
* **Content.** Grouped horizontal bars (or slope lines) of mean Friedman rank per algorithm across
  the three suites, with the two competition-grade methods visually banded apart from the
  classical/moderate roster.
* **Data / source.** `results/cec2017_mean_ranks.csv`, `results/cec2022_mean_ranks.csv`,
  `results/engineering_mean_ranks.csv` — read verbatim, no recomputation.
* **New or redesigned.** New. `[STRONG]` (brief §21)
* **Script.** `src/make_result_figures.py::fig_standing`
* **Size.** 7.4 × 3.8 in, `width="92%"`.
* **Placement.** Main text.

### FIG 13 — `fig-signal-model`
* **Caption (proposed).** *From the arterial to the decision vector. The eight intersections of the
  test bed (@fig-network) share one cycle length C; each intersection i contributes an arterial
  green split g_i and, for i ≥ 2, an offset o_i relative to intersection 1 — the sixteen variables
  of @eq-decision. The lower panel shows how the offsets displace the local green windows in time
  and thereby determine whether an eastbound platoon arrives inside or outside the green band,
  which is the mechanism that makes the objective multimodal.*
* **Location.** §8.2 Optimization model, after @eq-decision.
* **Question answered.** How does the physical arterial map onto the 16 decision variables, and why
  is the resulting landscape multimodal?
* **Content.** Upper: schematic arterial with the decision variables labelled on the objects they
  control. Lower: a time–space band showing green windows displaced by offsets and one platoon
  trajectory crossing them.
* **Data / source.** Schematic; intersection spacings and progression speed are those stated at
  line 742 of `paper.qmd`. No result values are plotted.
* **New or redesigned.** New. `[STRONG]` (brief §15)
* **Script.** `src/make_concept_figures.py::fig_signal_model`
* **Size.** 7.4 × 4.4 in, `width="100%"`.
* **Placement.** Main text.

---

## Redesigned figures

### FIG 7a/7b — `fig-convergence`, `fig-boxplots` (classical suite)
* **Change.** Restyle only: adopt the shared identity palette and the harmonized axis labels
  ("Iteration" / "Median best-so-far objective"). No data, protocol or seed changes.
* **Constraint.** Per-iteration curves are not archived, so the restyle requires re-running
  `src/run_benchmarks.py`. Seeds are fixed; the re-run is accepted **only if**
  `results/benchmark_stats.csv` and `results/wilcoxon.csv` reproduce bit-for-bit. If they do not,
  the original figures are retained and the discrepancy is reported, not absorbed.
* **Category.** `[STRONG]` (brief §16), conditional on exact reproduction.

### FIG 9 / 14 / 15 — `fig-cec2017`, `fig-cec2022`, `fig-engineering`
* **Change.** Axis-label harmonization and caption rewrite (state why the representative functions
  were chosen, and note explicitly that difficult cases are included). Palette already conforms.
* **Category.** `[STRONG]` (brief §10).

### FIG 22 — `fig-berth-plan`
* **Change.** Add the known global optimum and the optimality gap of the plotted plan as an
  annotation, label the waiting time of one ship explicitly, and improve the legend so the reader
  can tell a waiting interval from a service rectangle. Requires re-running
  `src/mealpy_comparison.py` (best-x is not archived); accepted only on exact reproduction of
  `results/table_mealpy_berth.md` and `results/table_berth_gap.md`.
* **Category.** `[STRONG]` (brief §15), conditional on exact reproduction.

---

## Figures deliberately left unchanged `[DO NOT CHANGE]`

| Figure | Reason |
|---|---|
| `fig-network` | Serves its purpose (what the test bed is); the new `fig-signal-model` covers the variable mapping |
| `fig-traffic-conv`, `fig-traffic-box`, `fig-plan` | Already conform to the visual language and answer a clear question |
| `fig-mealpy-convergence` | Conforms; restyling would require a re-run for no presentational gain |

---

## Final figure order in the revised manuscript

| # | ID | Section | Status |
|---:|---|---|---|
| 1 | `fig-motivation` | 1.1 | new |
| 2 | `fig-abstraction` | 1.3 | new |
| 3 | `fig-architecture` | 2.2 | new (replaces flowchart) |
| 4 | `fig-roles` | 2.4 | new |
| 5 | `fig-tactics` | 2.7 | new |
| 6 | `fig-statemachine` | 2.7 | new |
| 7 | `fig-convergence` | 3 | restyled |
| 8 | `fig-boxplots` | 3 | restyled |
| 9 | `fig-cec2017` | 4 | caption/labels |
| 10 | `fig-cec2017-dist` | 4 | new |
| 11 | `fig-cec2022` | 5 | caption/labels |
| 12 | `fig-engineering` | 6 | caption/labels |
| 13 | `fig-ablation` | 7.1 | new |
| 14 | `fig-sensitivity` | 7.2 | new |
| 15 | `fig-standing` | 7.4 | new |
| 16 | `fig-network` | 8.1 | unchanged |
| 17 | `fig-signal-model` | 8.2 | new |
| 18 | `fig-traffic-conv` | 8.4 | unchanged |
| 19 | `fig-traffic-box` | 8.4 | unchanged |
| 20 | `fig-plan` | 8.5 | unchanged |
| 21 | `fig-mealpy-convergence` | 9 | unchanged |
| 22 | `fig-berth-plan` | 9 | annotated |
