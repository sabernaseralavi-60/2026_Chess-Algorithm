# LANGUAGE AND PRESENTATION CHANGELOG (round 2)

Revision of *The Chess Algorithm: A Novel Metaheuristic Optimization Technique with Applications in
Transportation Network Engineering* in response to Dr. Seyedali Mirjalili's second review
(2026-09-11). Completed 2026-09-11.

**Scope.** Language and presentation only. No equation, protocol, seed, roster, result value,
statistical test, or claim changed. `src/validate_presentation.py` passes 52/52 checks against the
committed result files after the revision, including the numerical-consistency checks on every
table and the figure-embedded equation, table, and section numbers against the rendered PDF.

The reviewer raised thirteen points. Each is listed below with what was done and where.

---

## 1. Abstract length

* **Was:** 637 words, one block, reciting individual benchmark figures.
* **Now:** 232 words, one paragraph. States the problem, the architecture, the evaluation scope,
  the honest outcome (L-SHADE and CMA-ES ahead of CA throughout; CA best of the classical roster)
  and the ablation finding that explains both.
* **File:** `paper.qmd`, YAML `abstract:`.

## 2. Lists and subsections

* **Was:** 75 headings (13 level-1, 51 level-2, 11 level-3).
* **Now:** 41 headings (13 level-1, 28 level-2, 0 level-3).
* Section 2: `Initialization`, `Role assignment` and `Development schedule` merged into
  `Initialization and role assignment`; the six `###` strategic-mechanism headings (pinning,
  sacrifice, en passant, castling, threefold repetition, checkmate) and the five `###` headings
  inside `Adaptive tactical control` became run-in bold paragraphs in continuous prose;
  `Parameter summary` and `Pseudocode` merged; `Properties and design rationale` absorbed into
  `Strategic mechanisms`.
* Section 3: `Descriptive results`, `Convergence behavior` and `Statistical tests` merged into a
  single `Results`.
* Sections 5 and 6: `Motivation and protocol` and `Problems and roster` folded into the section
  openers; `Results` and `Discussion` merged into `Results and discussion`.
* Section 7 (transport): six subsections reduced to three.
* Section 9 (mealpy): four subsections reduced to two.
* Section 10 (conclusion): four subsections reduced to none.
* Cross-reference targets `sec-enpassant` and `sec-blockade` disappeared with their headings;
  the three references to each were retargeted to `@eq-enpassant` and `@eq-march`, and
  `src/make_method_figures.py` now prints the equation number instead of the section number in the
  state-machine figure.

## 3. Em-dashes

* **Was:** 182 in `paper.qmd`.
* **Now:** 4, all of them table cells where a dash is a "not applicable" marker, not punctuation.
* This was not a substitution pass. Every sentence built around an em-dash was rewritten, which is
  the bulk of the work behind point 13.

## 4. Figure caption length

* Every caption is now one or two typeset lines (longest 172 characters, most under 110).
* Interpretation that used to live in a caption moved into the body text beside the figure, so no
  content was dropped. Largest reductions: `fig-roles` (871 to 123 characters),
  `fig-cec2017-dist` (851 to 97, with the reading of the distributions now a short paragraph
  after the figure), `fig-statemachine` (762 to 151), `fig-tactics` (753 to 141),
  `fig-ablation` (730 to 151), `fig-signal-model` (704 to 172), `fig-sensitivity` (638 to 164),
  `fig-motivation` (634 to 134), `fig-berth-plan` (621 to 145), `fig-standing` (495 to 133).

## 5. Style of recent optimization-algorithm papers

* Introduction is now continuous prose with no subsections, closing with a paragraph on the
  organization of the paper.
* Method section runs: conceptual mapping, architecture (flowchart), specification, pseudocode,
  operator-family disclosure, complexity. Complexity closes the method section, as is conventional.
* Conclusion is a single unsegmented section.

## 6. IEEE referencing

* `_quarto.yml`: `csl: apa.csl` replaced with `csl: ieee.csl`; `ieee.csl` added to the repository
  (CSL project, IEEE Reference Guide 11.29.2023).
* Narrative citations rewritten so that they read correctly with a bracketed number, e.g.
  "the convention popularized by Mirjalili et al. [11]", "the recommendations of Derrac et al.", "the criticism articulated by
  Sörensen [18]", "Example 1.9 of Teodorović and Janić".
* Multi-reference cells in `tbl-operator-families` wrapped in `[@a; @b]` so they render as
  "[7], [11]" rather than "[7]; [11]".

## 7. Flowchart, Figure 3

* **Was:** a three-column box-and-arrow schematic with no standard symbols.
* **Now:** a conventional single-column flowchart in ISO 5807 notation: stadium terminators
  (Start, Stop), parallelograms for input and output, diamonds for the three decisions
  (acceptance rule, blockade trigger `s >= 25`, termination `t = T`), rectangles for process steps,
  side branches for the two conditional actions, and the iteration loop closed back to the
  controller with `t <- t+1`.
* **Files:** `src/figstyle.py` gains `process()`, `terminator()`, `parallelogram()` and `diamond()`
  helpers plus a `rotation` argument on `label()`; `src/make_method_figures.py::fig_architecture()`
  rewritten; `figures/ca_architecture.png` regenerated. Equation and table numbers inside the
  figure are still read from `paper.qmd` at drawing time, so they cannot drift.
* Caption reduced to one line: "Flowchart of the Chess Algorithm."; width raised 72% to 82%.

## 8. Pseudocode verbosity

* **Was:** 17 lines of prose-like text with multi-clause continuation lines.
* **Now:** a conventional numbered algorithm, 18 lines, explicit `Input:` and `Output:`, one action
  per line, a short equation reference where it helps, no line over 72 characters so nothing wraps.
* `\usepackage{needspace}` plus a `\Needspace{27\baselineskip}` guard keeps the block off a page
  break in the PDF.

## 9. Proposition and proof

* `Proposition (Elitist convergence in probability)` and its "proof sketch" **removed**, along with
  the `prp-convergence` callout block and its cross-reference.
* Replaced by two sentences of plain text in `Strategic mechanisms`: the King sequence is elitist,
  the knight's leap and threefold-repetition rule keep uniform probability mass on the whole box,
  and this places CA in the standard class of elitist random search methods, citing
  Solis and Wets (1981) rather than offering a proof of our own. The note that asymptotic
  statements say nothing at a 15,000-evaluation budget is retained.
* **File:** `references.bib` gains `solis1981minimization`.

## 10. "Parameter economy"

* Term **removed** from the paper. The paragraph it headed is folded into the parameter-table
  discussion, which now states the plain facts: no per-problem tuning for any method, one
  configuration for every result, and a forward reference to `@sec-sensitivity` for what that costs.

## 11. Computational and memory complexity

* **New subsection 2.9, `{#sec-complexity}`**, closing the method section immediately before the
  experiments.
* Time: per-iteration derivation (sort `O(N log N)`, elementwise moves/pin/clip `O(ND)`,
  `N` objective calls, the King's constant probe count, controller statistics, archive test),
  giving `O(T(ND + N log N + (N + kappa) C_f))` with `kappa <= 8` and the fourteen blockade calls
  accounted for separately; tied to the measured 12.4% overhead of `@sec-cost` and compared against
  GA, PSO, GWO and WOA.
* Memory: array-by-array accounting giving `O(ND + T)`, independent of the number of mechanisms,
  compared against PSO's `3ND` and GWO's population plus three leaders.
* `src/validate_presentation.py` now checks `sec-complexity` and `sec-ca` numbers against the
  rendered PDF in place of the removed `sec-blockade` and `sec-enpassant`.

## 12. Conclusion length

* **Was:** about 1,560 words across `Summary of findings`, `Limitations`, `Future work` and
  `Concluding remark`.
* **Now:** about 670 words, one section titled `Conclusion`, five paragraphs: what was proposed,
  what the experiments showed, what the ablation explains, where the evidence stops, what comes
  next. `Concluding remark` deleted.

## 13. Overall language and narrative

* Whole-manuscript rewrite rather than local patching. Section by section:
  introduction, method, benchmarks, CEC-2017, CEC-2022, engineering, analysis, transport, mealpy,
  conclusion.
* Removed rhetorical scaffolding ("it is important to state", "it is worth noting",
  "rather than merely", "the response this paper owes the reader") and sentences whose only
  function was to announce the next sentence.
* Reduced bold run-in labelling outside the mechanism definitions, where it is doing real work.
* Narrative arc made explicit: the transportation problem motivates the design, the design is
  specified and mapped to known operator families, the experiments rank it honestly, and the
  ablation shows that two of twelve mechanisms carry it and that the two algorithms which beat it
  are the specialists in precisely those two families.

---

## Files touched

| File | Change |
|---|---|
| `paper.qmd` | abstract, all ten sections, captions, pseudocode, complexity subsection, proposition removal, header `needspace` |
| `_quarto.yml` | `csl: apa.csl` to `csl: ieee.csl` |
| `ieee.csl` | added (CSL project, IEEE Reference Guide 11.29.2023) |
| `references.bib` | `solis1981minimization` added |
| `src/figstyle.py` | flowchart symbol helpers, `square` boxstyle fix, `label(rotation=)` |
| `src/make_method_figures.py` | `fig_architecture()` rewritten as a standard flowchart; state-machine figure references `eq-march` |
| `src/validate_presentation.py` | section-number checks retargeted; en-passant anchor updated |
| `figures/ca_architecture.png` | regenerated as a standard flowchart |
| `figures/ca_roles.png`, `figures/ca_statemachine.png`, `figures/ca_tactics.png` | regenerated (equation/table numbers shifted with the removed proposition) |
| `Reply_to_Dr_Mirjalili.md` | rewritten for this round |

## Verification

```
python src/validate_presentation.py     # 52/52 checks pass
quarto render paper.qmd                 # HTML and PDF, 59 pages
```
