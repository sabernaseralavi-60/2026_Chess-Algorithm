# The Chess Algorithm (CA)

**A Novel Metaheuristic Optimization Technique with Applications in Transportation Network Engineering**

Seyedsaber Naseralavi (Shahid Bahonar University of Kerman) — corresponding author
Seyedali Mirjalili (Torrens University Australia)

**Status:** under review at *Advanced Engineering Informatics* (Elsevier).

## 📖 Where to read the paper

| Output | Online | Local build |
|---|---|---|
| HTML article (English) | **<https://sabernaseralavi-60.github.io/2026_Chess-Algorithm/>** | `_article/index.html` |
| PDF manuscript (English, journal-ready) | **<https://sabernaseralavi-60.github.io/2026_Chess-Algorithm/paper.pdf>** | `_article/paper.pdf` |

The online copies are published to GitHub Pages from the `gh-pages` branch. To rebuild locally, render each format separately rather than with a bare `quarto render` (outputs land in `_article/`):

```bash
quarto render paper.qmd --to html
quarto render paper.qmd --to pdf
quarto render paper.qmd --to elsevier-pdf
```

**Do not render with no `--to`, and do not use `quarto publish` without `--no-render`.** Both render every format in paper.qmd in one process, and something in that combined pass — most likely metadata state the Elsevier extension's Lua filter sets for its own format (`cite-method: natbib`) — leaks into the plain `pdf` format's citeproc-based run, which otherwise needs no such thing. The result is every citation in `paper.pdf` rendering as an unresolved `[?]` instead of a number, silently (no error, no warning) — this shipped once and was only caught by inspecting the built PDF's text. `src/build_submission.py` is unaffected: it always renders the single `elsevier-pdf` target.

## What is this?

The Chess Algorithm (CA) is a population-based metaheuristic in which search agents play heterogeneous roles inspired by chess pieces (King, Queens, Rooks, Bishops, Knights, Pawns), each moving according to an operator abstracted from that piece's geometry. Strategic mechanisms translated from chess theory supply the control layer:

| Chess concept | Algorithmic mechanism |
|---|---|
| Development | Time-decaying exploration schedule `a(t) = 2(1 − t/T)` |
| Sacrifice | Spread-scaled Metropolis acceptance (minor pieces only) |
| Pinning | Progressive freezing of coordinates to the King's values |
| Castling | Safeguarded coordinate-block exchange King ↔ Rook |
| En passant | Self-adaptive local capture, with a royal-council / discovered-attack probe in later phases |
| Threefold repetition | Re-deployment of agents that collapse onto the King |
| Promotion | Rank-based role reassignment every iteration |

On top of this, CA carries an **adaptive control layer**: a lightweight state machine reads the population's divergence, initiative, and local-search success every iteration and decides which of a richer tactical set applies — Novotny interference (bishops), the knight's fork, and, when the search is genuinely stuck, a blockade response combining a King's march with a Tal-style speculative-sacrifice reheat. Every mechanism is mapped explicitly onto its established operator family (success-rule step adaptation, differential mutation, arithmetic recombination, etc.) in direct response to the standard "metaphor exposed" criticism of nature-inspired metaheuristics. An ablation configuration, **CA-static**, is the identical operator set with this adaptive layer switched off, and is carried through every experiment below to isolate what it contributes.

## Headline results

**Roster:** CA and CA-static are compared against six algorithms — the classical/widely used GWO, PSO, GA, and WOA, plus two competition-grade adaptive optimizers, **L-SHADE** and **CMA-ES**, included specifically so CA's standing is measured against the strongest representatives of the operator families it borrows from, not only against other metaphor-derived methods.

**CEC-2017 (all 29 usable functions, D=30, 30 independent runs):** L-SHADE and CMA-ES rank first and second and beat CA on the large majority of functions — reported without qualification. Among the classical/moderate roster, CA takes the **best mean Friedman rank**, with a single loss each to GWO and PSO (both on F5) and zero to WOA. Its one honestly-reported weak spot within that group is against GA specifically (10 wins / 9 ties / 10 losses), concentrated on long-range, unstructured multimodal landscapes where GA's macro-scale crossover has a structural edge — read in the paper as a clean illustration of the No-Free-Lunch theorem, not argued away.

**CEC-2022 (16 validated function×dimension cells, D∈{10,20}):** the same ordering holds — L-SHADE and CMA-ES first and second, CA best of the classical/moderate roster.

**Seven classic constrained engineering design problems**, same roster: CA is again the best of the classical/moderate roster, losing exactly once across 35 comparisons to that group; L-SHADE and CMA-ES beat it on the large majority of problems, several times reaching literature-optimum values with near-zero run-to-run variance.

**Granular ablation (12 mechanisms) and parameter sensitivity:** disabling each of CA's mechanisms one at a time shows that two — **en passant** and the **knight's fork** — carry the large majority of CA's measured performance (mean error ratios of ~600× and ~47× when removed); the other ten measure near-zero individual contribution. Those two mechanisms are exactly the fixed-rate analogues of the operator families CMA-ES and L-SHADE embody in fully adaptive form — which is the mechanistic reason those two algorithms win. A one-at-a-time parameter sweep finds CA robust to every tested parameter except the population's role fractions.

**Measured cost:** an exact evaluation-counting wrapper and wall-clock timing replace an earlier "ten to fifteen percent" estimate with a measured **12.4%** evaluation overhead for CA over the shared core budget.

**Data-integrity audits:** before trusting any CEC-2017 or CEC-2022 result, every function was checked against its own claimed global optimum and, where that passed, checked empirically for whether *any* algorithm's best run beat the claimed optimum — a definitional impossibility if it's correct. Six CEC-2017 labels (F5, F9, F15, F16, F19, F21) failed this audit in the primary `opfunu` port; all six were cross-validated against an independent, official-data implementation ([`cec2017-py`](https://github.com/tilleyd/cec2017-py)), passed cleanly, and were restored — so all 29 usable CEC-2017 functions are validated, none excluded. (The numbering is a subtlety worth knowing if you cross-check: `opfunu` renumbers the suite consecutively after the official withdrawal of F2, so its F*n* is official F*(n+1)* for n≥2.) On CEC-2022, six (function, dimension) cells failed the same audit and one function proved non-discriminative under a mechanical pre-registered rule; sixteen cells remain validated. Pre-audit numbers are kept on record (`results/cec2017_opfunu_defect_evidence.csv`, `results/cec2022_stats_raw_unaudited.csv`) rather than quietly dropped.

**Transportation applications:** on an eight-intersection arterial signal-timing problem, CA is significantly better than GA and GWO, statistically tied with CA-static, and — reported plainly — significantly worse in mean delay than PSO, L-SHADE, and CMA-ES (the last two by small margins), even though CA and CA-static both reach the single best plan found by any method. Against six independent third-party implementations from the [`mealpy`](https://github.com/thieu1995/mealpy) library (WOA, SCA, ALO, MFO, HHO, DE) plus L-SHADE and CMA-ES on this same signal-timing problem and on a continuous berth-allocation instance with a known global optimum, CA beats all six `mealpy` baselines on both problems and loses to L-SHADE/CMA-ES on both, decisively on berth allocation.

Six classical 30-D benchmark functions (F1–F6) against GA, PSO, SA, and GWO under matched budgets round out the evidence: CA beats PSO and SA on every function and GA on five of six, while GWO — as is well documented on this classical suite — keeps its edge.

## Repository layout

```
├── _quarto.yml                    # Quarto article project configuration
├── paper.qmd                      # English article (HTML + PDF + Elsevier camera-ready)
├── _partials/before-body.tex      # elsarticle front matter, one fix over the extension's
├── submission/                    # journal submission packages (see submission/README.md)
├── adaptive_ca_math_update.md     # Full equations for the adaptive control layer
├── index.qmd, chapters/           # Legacy book sources (superseded by paper.qmd)
├── theme.scss                     # Chessboard-derived academic theme
├── references.bib                 # Bibliography (IEEE via ieee.csl; elsarticle-num for Elsevier)
├── src/
│   ├── algorithms.py               # CA (chess_algorithm_v3), CA-static (chess_algorithm_v2),
│   │                                #   GA, PSO, SA, GWO — shared interface; CA-v3 also
│   │                                #   exposes the 12 ablation kwargs used by ablation_study.py
│   ├── sota_algorithms.py          # L-SHADE (via niapy) and CMA-ES (via pycma) wrappers,
│   │                                #   same shared interface
│   ├── benchmark_functions.py      # F1–F6 classical test suite
│   ├── engineering_problems.py     # 7 constrained engineering design problems
│   ├── run_benchmarks.py           # Six-function benchmark → results/, figures/
│   ├── traffic_case_study.py       # Arterial signal timing → results/, figures/
│   ├── mealpy_comparison.py        # CA vs mealpy (WOA/SCA/ALO/MFO/HHO/DE) on
│   │                                #   signal timing + continuous berth allocation
│   │                                #   (run via run_transportation_pipeline.py, not directly)
│   ├── run_transportation_pipeline.py # mealpy_comparison.py -> sota_addon_run.py
│   │                                #   --suite transport -> validates both ran
│   ├── cec2017_full_run.py         # Full CEC-2017 suite (partitionable, --part i/4)
│   ├── cec2022_full_run.py         # Full CEC-2022 suite, both dims (partitionable, --part i/4)
│   ├── sota_addon_run.py           # Adds L-SHADE/CMA-ES to CEC-2017/engineering/transport
│   ├── cec2017_restoration_audit.py # Cross-validates excluded CEC-2017 labels against
│   │                                #   the official-data cec2017-py port
│   ├── cec2017_restore_run.py      # 8-algorithm rerun of the restored labels
│   ├── engineering_full_run.py     # Full engineering-design benchmark
│   ├── ablation_study.py           # 12 single-mechanism-off variants, 6 problems
│   ├── sensitivity_study.py        # One-at-a-time parameter sensitivity, 6 problems
│   ├── timing_study.py             # Measured wall-clock + exact evaluation counts
│   ├── phase2_3_analysis.py        # Merge partitions, data-integrity audit,
│   │                                #   Friedman/Wilcoxon stats, convergence figures
│   ├── cec2022_analysis.py         # CEC-2022 merge, audit, F3 flatness rule, ranks, figure
│   ├── generate_markdown_tables.py # Detailed function-major tables (paper Appendix A)
│   ├── generate_transposed_tables.py # Primary tables: algorithms as rows, functions as
│   │                                #   columns, mean +/- std, best mean in bold
│   ├── generate_timing_table.py    # Measured-cost table
│   ├── generate_latex_tables.py    # Camera-ready LaTeX tables (results/latex_tables_final.tex)
│   ├── figstyle.py                 # One identity palette and figure style for every figure
│   ├── make_concept_figures.py     # Conceptual figures (introduction, signal-timing model)
│   ├── make_method_figures.py      # Mechanism figures (architecture, roles, tactics, controller)
│   ├── make_result_figures.py      # Ablation, sensitivity, cross-suite ranks, CEC-2017 boxplots
│   └── validate_presentation.py    # Re-checks every rendered table cell against its source CSV
├── results/                        # Committed CSVs + Markdown tables (reproducible)
├── figures/                        # Committed publication figures (300 DPI)
├── assets/                         # Author photo
└── _ci/publish.yml                 # Render & deploy workflow (see below)
```

## Reproducing everything

Requirements: Python ≥ 3.10 with `numpy`, `scipy`, `pandas`, `matplotlib`; [Quarto](https://quarto.org) ≥ 1.4 (with TinyTeX for PDF); [`opfunu`](https://github.com/thieu1995/opfunu) for the CEC-2017/CEC-2022 suites; [`mealpy`](https://github.com/thieu1995/mealpy) for the third-party comparison; [`niapy`](https://github.com/NiaOrg/NiaPy) (L-SHADE) and [`cma`](https://github.com/CMA-ES/pycma) (CMA-ES) for the two competition-grade baselines; [`cec2017-py`](https://github.com/tilleyd/cec2017-py) (installed from source; not on PyPI) for the CEC-2017 restoration audit.

```bash
pip install numpy scipy pandas matplotlib opfunu niapy cma
pip install --no-deps mealpy    # on Python >= 3.12, mealpy's pinned numpy fails
                                 # to build otherwise; --no-deps sidesteps it
pip install git+https://github.com/tilleyd/cec2017-py.git

python src/run_benchmarks.py               # six-function benchmark
python src/traffic_case_study.py           # arterial signal-timing case study
python src/run_transportation_pipeline.py  # extended third-party comparison (Sec. 9);
                                            #   see "Transportation pipeline" below --
                                            #   do not call mealpy_comparison.py directly
python src/cec2017_full_run.py --part 0/4  # full CEC-2017 suite (run parts 0..3,
python src/cec2017_full_run.py --part 1/4  #   in parallel or in sequence)
python src/cec2017_full_run.py --part 2/4
python src/cec2017_full_run.py --part 3/4
python src/cec2022_full_run.py --part 0/4  # full CEC-2022 suite, same partitioning
python src/cec2022_full_run.py --part 1/4
python src/cec2022_full_run.py --part 2/4
python src/cec2022_full_run.py --part 3/4
python src/engineering_full_run.py         # 7 engineering design problems
python src/sota_addon_run.py --suite cec2017      # adds L-SHADE/CMA-ES to CEC-2017
python src/sota_addon_run.py --suite engineering  #   and to engineering (transport is
                                                   #   covered by the pipeline above)
python src/cec2017_restoration_audit.py    # audits the excluded CEC-2017 labels
python src/cec2017_restore_run.py          # 8-algorithm rerun of the restored labels
python src/ablation_study.py               # 12-mechanism ablation
python src/sensitivity_study.py            # parameter sensitivity
python src/timing_study.py                 # measured cost (run on an otherwise-idle machine)
python src/phase2_3_analysis.py            # merge + audit + stats + figures (CEC-2017/engineering)
python src/cec2022_analysis.py             # merge + audit + F3 rule + stats + figure (CEC-2022)
python src/generate_markdown_tables.py     # detailed tables (paper Appendix A)
python src/generate_transposed_tables.py   # primary tables (algorithms as rows)
python src/generate_timing_table.py        # measured-cost table
python src/generate_latex_tables.py        # camera-ready LaTeX tables
python src/make_concept_figures.py         # conceptual figures
python src/make_method_figures.py          # mechanism figures
python src/make_result_figures.py          # analysis figures
python src/validate_presentation.py        # numerical + cross-reference validation
quarto render paper.qmd --to html          # build HTML (see the note above on
quarto render paper.qmd --to pdf           #   why these must be separate calls)
```

### Transportation pipeline

Section 9's tables need **two** scripts to run, in order, because the second depends on a file
the first writes:

```bash
python src/run_transportation_pipeline.py
#   1. mealpy_comparison.py           -- CA + six third-party mealpy algorithms
#   2. sota_addon_run.py --suite transport   -- adds L-SHADE and CMA-ES
#   3. validates that every transportation table contains both, and fails loudly if not
```

Do not call `mealpy_comparison.py` on its own: it writes `table_mealpy_signal.md`,
`table_mealpy_berth.md`, and `table_berth_gap.md` with seven algorithms, silently short of the
nine the manuscript reports, until `sota_addon_run.py --suite transport` adds the other two. The
pipeline script exists so that dependency can't be missed; `python src/run_transportation_pipeline.py --validate-only` re-checks it against whatever is already on disk without re-running the experiment.

All random seeds are fixed; the committed `results/` and `figures/` correspond exactly to the numbers in the paper. The CEC-2017 and CEC-2022 full runs each take on the order of tens of minutes to a few hours across their four partitions (mostly spent on the slower baselines, not CA); everything else completes in minutes.

## Publication & deployment

GitHub Pages is configured to serve the `gh-pages` branch directly (Settings → Pages → Deploy from branch), so any push to `gh-pages` goes live within a couple of minutes with no build step on GitHub's side.

**Do not publish with `quarto publish gh-pages` on its own** — by default it re-renders the whole project itself, which triggers the combined-render citation bug described above and would ship a broken `paper.pdf`. Render each format separately first (see *Reproducing everything*), then publish without letting quarto touch the render:

```bash
quarto render paper.qmd --to html
quarto render paper.qmd --to pdf
quarto render paper.qmd --to elsevier-pdf
quarto publish gh-pages --no-render --no-prompt --no-browser
```

If `--no-render` errors with "Output file index.html does not exist" (seen once in this project), publish manually instead: check out `gh-pages` into a worktree, mirror `index.html`, `figures/`, `paper_files/`, `paper.pdf`, `paper-elsevier.pdf`, and `.nojekyll` from `_article/` into it (excluding `_article/assets/` and `_article/results/`, which were never part of the published site), commit, and push. **Whichever way you publish, verify the citations afterward** — extract text from both downloaded PDFs and check for the literal string `[?`:

```python
import fitz  # PyMuPDF
for f in ["paper.pdf", "paper-elsevier.pdf"]:
    d = fitz.open(f)
    text = "".join(p.get_text() for p in d)
    print(f, text.count("[?"))  # must be 0
```

A ready-made GitHub Actions workflow that would do this automatically on every push to `main` is kept at **`_ci/publish.yml`**, not yet active: two different tokens across this project's life have both lacked the fine-grained `Workflows` permission GitHub requires to write into `.github/workflows/`, so pushing or API-writing the file there is rejected even with `Contents: admin`. To activate it, either add the `Workflows: Read and write` permission to the token in use and push once —

```bash
mkdir -p .github/workflows
git mv _ci/publish.yml .github/workflows/publish.yml
git commit -m "Activate publish workflow"
git push
```

— or move the file in the GitHub web editor, which isn't subject to this restriction. Until then, run the `quarto publish` command above after any content change.

## Journal submission

The manuscript is prepared for **Advanced Engineering Informatics** (Elsevier) in `elsarticle` camera-ready format, with **Knowledge-Based Systems** and then **Cluster Computing** as the agreed fallbacks. One command renders the manuscript and assembles a verified package:

```bash
python src/build_submission.py
```

It renders `paper.qmd --to elsevier-pdf`, collects the LaTeX source with its class file, bibliography style and figures into `submission/advanced-engineering-informatics/`, then re-compiles that collected copy in a scratch directory and fails if the log shows an undefined citation or reference or a dropped glyph — so the package is checked to build standalone, the way the publisher's system builds it.

See **`submission/README.md`** for what to upload where, the items that still need a human decision, and why Cluster Computing needs a different template (it is Springer, not Elsevier).

## Citation

The manuscript is under review at *Advanced Engineering Informatics*. Until a journal version is available, please cite this repository:

```bibtex
@misc{naseralavi2026chess,
  title        = {The Chess Algorithm: A Novel Metaheuristic Optimization Technique
                  with Applications in Transportation Network Engineering},
  author       = {Naseralavi, Seyedsaber and Mirjalili, Seyedali},
  year         = {2026},
  howpublished = {Preprint},
  url          = {https://github.com/sabernaseralavi-60/2026_Chess-Algorithm}
}
```

## License

MIT — see [LICENSE](LICENSE).
