# The Chess Algorithm (CA)

**A Novel Metaheuristic Optimization Technique with Applications in Transportation Network Engineering**

Seyed Saber Naseralavi (Shahid Bahonar University of Kerman) — corresponding author
Seyedali Mirjalili (Torrens University Australia) — *invited co-author; participation pending confirmation*

## 📖 Where to read the paper

| Output | Online | Local build |
|---|---|---|
| HTML article (English) | **<https://sabernaseralavi-60.github.io/2026_Chess-Algorithm/>** | `_article/index.html` |
| PDF manuscript (English, journal-ready) | **<https://sabernaseralavi-60.github.io/2026_Chess-Algorithm/paper.pdf>** | `_article/paper.pdf` |

The online copies are published to GitHub Pages from the `gh-pages` branch. To rebuild locally, run `quarto render` (outputs land in `_article/`).

A Persian (RTL) Word translation can be built locally from `paper-fa.qmd` (`quarto render paper-fa.qmd --to docx`); it is kept as a local-only build and is not published online.

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

On top of this, CA carries an **adaptive control layer**: a lightweight state machine reads the population's divergence, initiative, and local-search success every iteration and decides which of a richer tactical set applies — Novotny interference (bishops), the knight's fork, and, when the search is genuinely stuck, a blockade response combining a King's march with a Tal-style speculative-sacrifice reheat. An ablation configuration, **CA-static**, is the identical operator set with this adaptive layer switched off, and is carried through every experiment below to isolate what it contributes.

## Headline results

**CEC-2017 (24 validated functions, D=30, 30 independent runs)** against GWO, PSO, GA, and WOA: CA takes the **best mean Friedman rank** of the six algorithms compared, with zero losses to GWO or WOA and only 3/24 losses to PSO. Its one honestly-reported weak spot is against GA specifically (7 wins / 7 ties / 10 losses), concentrated on long-range, unstructured multimodal landscapes where GA's macro-scale crossover has a structural edge — read in the paper as a clean illustration of the No-Free-Lunch theorem, not argued away.

**Seven classic constrained engineering design problems** (welded beam, pressure vessel, speed reducer, spring, three-bar truss, gear train, cantilever beam), same roster: CA again ranks first, losing exactly once across 35 pairwise comparisons.

**Data-integrity audit:** before trusting any CEC-2017 result, every function was checked against its own claimed global optimum and, where that passed, checked empirically for whether *any* algorithm's best run beat the claimed optimum — a definitional impossibility if it's correct. Five of 29 functions failed this audit (F5, F9, F15, F19, F21) and were excluded; the pre-audit numbers are kept on record in `results/cec2017_stats_raw_unaudited.csv` rather than quietly dropped.

**Transportation applications:** on an eight-intersection arterial signal-timing problem, CA is significantly better than GA and GWO, statistically tied with CA-static, and — reported plainly — significantly worse in mean delay than PSO, even though CA and CA-static both reach the single best plan found by any method. Against six independent third-party implementations from the [`mealpy`](https://github.com/thieu1995/mealpy) library (WOA, SCA, ALO, MFO, HHO, DE) on this same signal-timing problem and on a continuous berth-allocation instance with a known global optimum, CA is significantly better on both.

Six classical 30-D benchmark functions (F1–F6) against GA, PSO, SA, and GWO under matched budgets round out the evidence: CA beats PSO and SA on every function and GA on five of six, while GWO — as is well documented on this classical suite — keeps its edge.

## Repository layout

```
├── _quarto.yml                    # Quarto article project configuration
├── paper.qmd                      # English article (renders to HTML + PDF)
├── paper-fa.qmd                   # Persian article (renders to Word .docx, RTL)
├── adaptive_ca_math_update.md     # Full equations for the adaptive control layer
├── index.qmd, chapters/           # Legacy book sources (superseded by paper.qmd)
├── theme.scss                     # Chessboard-derived academic theme
├── references.bib                 # Bibliography (APA, via apa.csl)
├── src/
│   ├── algorithms.py               # CA (chess_algorithm_v3), CA-static (chess_algorithm_v2),
│   │                                #   GA, PSO, SA, GWO — shared interface
│   ├── benchmark_functions.py      # F1–F6 classical test suite
│   ├── engineering_problems.py     # 7 constrained engineering design problems
│   ├── run_benchmarks.py           # Six-function benchmark → results/, figures/
│   ├── traffic_case_study.py       # Arterial signal timing → results/, figures/
│   ├── mealpy_comparison.py        # CA vs mealpy (WOA/SCA/ALO/MFO/HHO/DE) on
│   │                                #   signal timing + continuous berth allocation
│   ├── cec2017_full_run.py         # Full CEC-2017 suite (partitionable, --part i/4)
│   ├── engineering_full_run.py     # Full engineering-design benchmark
│   ├── phase2_3_analysis.py        # Merge partitions, data-integrity audit,
│   │                                #   Friedman/Wilcoxon stats, convergence figures
│   ├── generate_markdown_tables.py # Quarto-includable result tables
│   └── generate_latex_tables.py    # Camera-ready LaTeX tables (results/latex_tables_final.tex)
├── results/                        # Committed CSVs + Markdown tables (reproducible)
├── figures/                        # Committed publication figures (300 DPI)
├── assets/                         # Author photo
├── Letter_to_Dr_Mirjalili.md
└── _ci/publish.yml                 # Render & deploy workflow (see below)
```

## Reproducing everything

Requirements: Python ≥ 3.10 with `numpy`, `scipy`, `pandas`, `matplotlib`; [Quarto](https://quarto.org) ≥ 1.4 (with TinyTeX for PDF); [`opfunu`](https://github.com/thieu1995/opfunu) for the CEC-2017 suite; [`mealpy`](https://github.com/thieu1995/mealpy) for the third-party comparison.

```bash
pip install numpy scipy pandas matplotlib opfunu
pip install --no-deps mealpy    # on Python >= 3.12, mealpy's pinned numpy fails
                                 # to build otherwise; --no-deps sidesteps it

python src/run_benchmarks.py               # six-function benchmark
python src/traffic_case_study.py           # arterial signal-timing case study
python src/mealpy_comparison.py            # extended third-party comparison
python src/cec2017_full_run.py --part 0/4  # full CEC-2017 suite (run parts 0..3,
python src/cec2017_full_run.py --part 1/4  #   in parallel or in sequence)
python src/cec2017_full_run.py --part 2/4
python src/cec2017_full_run.py --part 3/4
python src/engineering_full_run.py         # 7 engineering design problems
python src/phase2_3_analysis.py            # merge + audit + stats + figures
python src/generate_markdown_tables.py     # paper-facing result tables
python src/generate_latex_tables.py        # camera-ready LaTeX tables

quarto render                              # builds _article/ (EN: HTML + PDF; FA: docx)
```

All random seeds are fixed; the committed `results/` and `figures/` correspond exactly to the numbers in the paper. The CEC-2017 full run takes on the order of hours across its four partitions (mostly spent on the third-party baselines, not CA); everything else completes in minutes.

## Publication & deployment

A ready-made GitHub Actions workflow is provided at **`_ci/publish.yml`**. It renders the Quarto article (HTML + PDF via TinyTeX) on every push to `main` and publishes it to the `gh-pages` branch.

> **One-time activation required.** The access token used to create this repository did not carry the `workflow` scope, so GitHub rejected pushing the file directly into `.github/workflows/`. To activate CI, run once from a clone (or move the file in the GitHub web editor):
>
> ```bash
> mkdir -p .github/workflows
> git mv _ci/publish.yml .github/workflows/publish.yml
> git commit -m "Activate publish workflow"
> git push
> ```
>
> Then enable **Settings → Pages → Deploy from branch → `gh-pages`** after the first successful run. Alternatively, render locally with `quarto render` and publish with `quarto publish gh-pages`.

## Authorship note

Professor Seyedali Mirjalili is listed as an **invited co-author whose participation is pending confirmation** (see `Letter_to_Dr_Mirjalili.md`). His name will be retained in the author list only upon his explicit consent, and will otherwise be removed.

## Citation

If you use CA in your research, please cite this repository until a journal version is available:

```bibtex
@misc{naseralavi2026chess,
  title        = {The Chess Algorithm: A Novel Metaheuristic Optimization Technique
                  with Applications in Transportation Network Engineering},
  author       = {Naseralavi, Seyed Saber},
  year         = {2026},
  howpublished = {Preprint},
  url          = {https://github.com/sabernaseralavi-60/2026_Chess-Algorithm}
}
```

## License

MIT — see [LICENSE](LICENSE).
