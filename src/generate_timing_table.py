"""
generate_timing_table.py
==========================
Markdown table for src/timing_study.py's results/timing_stats.csv (step
A5): mean wall-clock time, exact evaluation count, evaluation overhead
vs. the pop*iters core budget, and time relative to GA, per (problem,
algorithm) cell, plus a summary row of CA's overhead averaged across all
6 timing problems -- the number that replaces the paper's prior
"ten to fifteen percent more evaluations" estimate.

Usage:  python src/generate_timing_table.py
"""

import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")

ALGOS = ["CA", "CA-static", "GWO", "PSO", "GA", "WOA", "L-SHADE", "CMA-ES"]


def main():
    """Include-safe markdown (no headings) so the table can be pulled
    into paper.qmd via {{< include >}} under a Quarto caption."""
    df = pd.read_csv(os.path.join(RESULTS, "timing_stats.csv"))
    problems = list(df["problem"].unique())

    lines = ["| Problem | Algorithm | Mean time (s) | Mean evals "
             "| Evals / core budget | Time vs GA |",
             "|---|---|---:|---:|---:|---:|"]
    for pname in problems:
        sub = df[df.problem == pname].set_index("algo")
        for a in ALGOS:
            row = sub.loc[a]
            lines.append(
                f"| {pname} | {a} | {row['mean_time_s']:.3f} | "
                f"{row['mean_evals']:.0f} | "
                f"{row['evals_over_core']:.3f} | "
                f"{row['relative_time_vs_GA']:.2f} |")

    with open(os.path.join(RESULTS, "table_timing.md"), "w",
             encoding="utf8") as f:
        f.write("\n".join(lines) + "\n")

    ca_overhead = (df[df.algo == "CA"]["evals_over_core"].mean() - 1.0) * 100
    ca_static_overhead = (df[df.algo == "CA-static"]["evals_over_core"].mean()
                          - 1.0) * 100
    print(f"CA overhead: {ca_overhead:.1f}%  (CA-static: "
         f"{ca_static_overhead:.1f}%)")


if __name__ == "__main__":
    main()
