# The Chess Algorithm (CA)

**A Novel Metaheuristic Optimization Technique with Applications in Transportation Network Engineering**

Seyed Saber Naseralavi (Shahid Bahonar University of Kerman) — corresponding author
Seyedali Mirjalili (Torrens University Australia) — *invited co-author; participation pending confirmation*

📖 **Read the book online:** https://sabernaseralavi-60.github.io/2026_Chess-Algorithm/ (published via GitHub Actions on every push)

## What is this?

The Chess Algorithm (CA) is a population-based metaheuristic in which search agents play heterogeneous roles inspired by chess pieces (King, Queens, Rooks, Bishops, Knights, Pawns), governed by strategic mechanisms translated from chess theory:

| Chess concept | Algorithmic mechanism |
|---|---|
| Development | Time-decaying exploration schedule `a(t) = 2(1 − t/T)` |
| Sacrifice | Spread-scaled Metropolis acceptance (minor pieces only) |
| Pinning | Progressive freezing of coordinates to the King's values |
| Castling | Safeguarded coordinate-block exchange King ↔ Rook |
| En passant | Self-adaptive local capture with an ES-style success rule |
| Threefold repetition | Re-deployment of agents that collapse onto the King |
| Promotion | Rank-based role reassignment every iteration |

CA is benchmarked against **GA, PSO, SA, and GWO** on six classical 30-D functions (30 runs, identical evaluation budgets, ANOVA + Wilcoxon tests) and applied to a **coordinated signal timing problem** on an eight-intersection urban arterial (Webster/HCM time-dependent delay model).

**Honest headline results:** CA significantly outperforms GA, PSO, and SA on the majority of the benchmark suite; GWO remains stronger on the classical functions; on the arterial signal coordination case study CA is statistically indistinguishable from GA/PSO/GWO and attains the best solution found by any method.

## Repository layout

```
├── _quarto.yml            # Quarto book configuration (HTML + PDF)
├── index.qmd              # Title page, abstract, author bio
├── chapters/              # 01 Introduction … 06 References
├── theme.scss             # Chessboard-derived academic theme
├── references.bib         # Bibliography (APA)
├── src/
│   ├── algorithms.py          # CA + GA, PSO, SA, GWO (shared interface)
│   ├── benchmark_functions.py # F1–F6 test suite
│   ├── run_benchmarks.py      # Benchmark experiments → results/, figures/
│   └── traffic_case_study.py  # Arterial signal timing → results/, figures/
├── results/               # Committed CSVs + Markdown tables (reproducible)
├── figures/               # Committed publication figures
├── assets/                # Author photo
├── Letter_to_Dr_Mirjalili.md
└── .github/workflows/publish.yml  # Render & deploy to GitHub Pages
```

## Reproducing everything

Requirements: Python ≥ 3.10 with `numpy`, `scipy`, `matplotlib`; [Quarto](https://quarto.org) ≥ 1.4 (with TinyTeX for PDF).

```bash
pip install numpy scipy matplotlib

python src/run_benchmarks.py       # ~ a few minutes; regenerates all benchmark tables/figures
python src/traffic_case_study.py   # regenerates the case-study tables/figures

quarto render                      # builds _book/ (HTML + PDF)
```

All random seeds are fixed; the committed `results/` and `figures/` correspond exactly to the numbers in the book.

## Publication & deployment

A ready-made GitHub Actions workflow is provided at **`_ci/publish.yml`**. It renders the Quarto book (HTML + PDF via TinyTeX) on every push to `main` and publishes it to the `gh-pages` branch.

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
@book{naseralavi2026chess,
  title     = {The Chess Algorithm: A Novel Metaheuristic Optimization Technique
               with Applications in Transportation Network Engineering},
  author    = {Naseralavi, Seyed Saber},
  year      = {2026},
  publisher = {GitHub},
  url       = {https://github.com/sabernaseralavi-60/2026_Chess-Algorithm}
}
```

## License

MIT — see [LICENSE](LICENSE).
