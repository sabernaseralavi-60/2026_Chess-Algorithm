"""
generate_markdown_tables.py
============================
Markdown-table equivalents of the Phase 2-3 results, in the same style
as the paper's existing results/table_stats.md and table_wilcoxon.md,
for {{< include >}} into paper.qmd (HTML + PDF via Quarto/pandoc, unlike
the raw-LaTeX results/latex_tables_final.tex which only targets the PDF
build).

Usage:  python src/generate_markdown_tables.py
"""

import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")

ALGOS = ["CA-v3", "CA-v2", "GWO", "PSO", "GA", "WOA"]

# camelCase dict keys (engineering_problems.py) are fine for code but
# render as unreadable, unbreakable strings in a narrow PDF table column
DISPLAY_NAME = {
    "WeldedBeam": "Welded Beam", "Spring": "Spring",
    "PressureVessel": "Pressure Vessel", "SpeedReducer": "Speed Reducer",
    "ThreeBarTruss": "Three-Bar Truss", "GearTrain": "Gear Train",
    "CantileverBeam": "Cantilever Beam",
}


def fnum(label):
    return int(label[1:])


def fmt(x, sig=4):
    return f"{x:.{sig}e}" if (abs(x) >= 1e5 or 0 < abs(x) < 1e-3) \
        else f"{x:.4g}"


def stats_table(stats_csv, index_col, order, out_name):
    df = pd.read_csv(stats_csv)
    lines = [f"| {index_col.capitalize()} | Algorithm | Mean | Std | "
            "Best | Worst |",
            "|---|---|---:|---:|---:|---:|"]
    for item in order:
        sub = df[df[index_col] == item].set_index("algo")
        best_algo = sub["mean"].idxmin()
        label = DISPLAY_NAME.get(item, item)
        for a in ALGOS:
            m = fmt(sub.loc[a, "mean"])
            if a == best_algo:
                m = f"**{m}**"
            lines.append(f"| {label} | {a} | {m} | "
                        f"{fmt(sub.loc[a,'std'])} | "
                        f"{fmt(sub.loc[a,'best'])} | "
                        f"{fmt(sub.loc[a,'worst'])} |")
    with open(os.path.join(RESULTS, out_name), "w", encoding="utf8") as f:
        f.write("\n".join(lines) + "\n")


def rank_table(ranks_csv, out_name):
    df = pd.read_csv(ranks_csv).sort_values("mean_rank")
    lines = ["| Algorithm | Mean Friedman rank |", "|---|---:|"]
    for _, row in df.iterrows():
        algo = row["algo"]
        val = f"{row['mean_rank']:.3f}"
        if algo == "CA-v3":
            algo, val = f"**{algo}**", f"**{val}**"
        lines.append(f"| {algo} | {val} |")
    with open(os.path.join(RESULTS, out_name), "w", encoding="utf8") as f:
        f.write("\n".join(lines) + "\n")


def wtl_table(wilc_csv, index_col, out_name):
    wl = pd.read_csv(wilc_csv)
    n_items = wl[index_col].nunique()
    lines = ["| Competitor | Win | Tie | Loss |", "|---|---:|---:|---:|"]
    for comp in [a for a in ALGOS if a != "CA-v3"]:
        sub = wl[wl.competitor == comp]
        w = ((sub.significant == "yes")
             & (sub.v3_mean_direction == "better")).sum()
        lo = ((sub.significant == "yes")
              & (sub.v3_mean_direction == "worse")).sum()
        tie = n_items - w - lo
        lines.append(f"| {comp} | {w} | {tie} | {lo} |")
    with open(os.path.join(RESULTS, out_name), "w", encoding="utf8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    cec = pd.read_csv(os.path.join(RESULTS, "cec2017_stats.csv"))
    cec_funcs = sorted(cec["func"].unique(), key=fnum)
    stats_table(os.path.join(RESULTS, "cec2017_stats.csv"), "func",
               cec_funcs, "table_cec2017_stats.md")
    rank_table(os.path.join(RESULTS, "cec2017_mean_ranks.csv"),
              "table_cec2017_ranks.md")
    wtl_table(os.path.join(RESULTS, "cec2017_wilcoxon.csv"), "func",
             "table_cec2017_wtl.md")

    eng = pd.read_csv(os.path.join(RESULTS, "engineering_stats.csv"))
    eng_problems = list(eng["problem"].unique())
    stats_table(os.path.join(RESULTS, "engineering_stats.csv"), "problem",
               eng_problems, "table_engineering_stats.md")
    rank_table(os.path.join(RESULTS, "engineering_mean_ranks.csv"),
              "table_engineering_ranks.md")
    wtl_table(os.path.join(RESULTS, "engineering_wilcoxon.csv"), "problem",
             "table_engineering_wtl.md")

    print("Wrote 6 markdown tables to results/")


if __name__ == "__main__":
    main()
