"""
generate_transposed_tables.py
=============================
Primary comparison tables in the orientation requested by the co-author
review: **rows are algorithms, columns are test functions**, cells are
``mean +/- std`` with the best mean per function column in bold.

Every number is read from the committed result CSVs in ``results/``; no
value is typed by hand and nothing is recomputed from raw runs, so the
tables are regenerable and traceable.  The detailed function-major
tables (mean/std/best/worst) that these replace in the main text are
still produced by ``generate_markdown_tables.py`` and are included in
the manuscript's Appendix A, so no information is lost -- only moved.

Outputs (results/):
    table_t_classical.md          classical suite, 6 functions
    table_t_classical_wilcoxon.md classical Wilcoxon, transposed
    table_t_classical_anova.md    classical ANOVA, transposed
    table_t_cec2017_summary.md    rank + W/T/L + best-mean count
    table_t_cec2017_unimodal.md   official category groups
    table_t_cec2017_multimodal.md
    table_t_cec2017_hybrid.md
    table_t_cec2017_composition.md
    table_t_cec2022_summary.md
    table_t_cec2022_D10.md        one table per official dimensionality
    table_t_cec2022_D20.md
    table_t_engineering_summary.md
    table_t_engineering.md
    table_t_timing.md             cost, algorithms as rows
    table_t_traffic.md            signal timing + Wilcoxon, merged

Usage:  python src/generate_transposed_tables.py
"""

import os
from decimal import ROUND_HALF_UP, Decimal

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")

# row order used in every eight-algorithm table: CA and its ablation
# first, then the classical/moderate roster, then the two
# competition-grade methods
ALGOS8 = ["CA", "CA-static", "GWO", "PSO", "GA", "WOA", "L-SHADE",
          "CMA-ES"]
ALGOS_CLASSICAL = ["CA", "CA-static", "GWO", "PSO", "GA", "SA"]
ALGOS_TRAFFIC = ["CA", "CA-static", "GWO", "PSO", "GA"]

ENG_ORDER = ["WeldedBeam", "Spring", "PressureVessel", "SpeedReducer",
             "ThreeBarTruss", "GearTrain", "CantileverBeam"]
ENG_LABEL = {"WeldedBeam": "Welded beam", "Spring": "Spring",
             "PressureVessel": "Pressure vessel",
             "SpeedReducer": "Speed reducer",
             "ThreeBarTruss": "Three-bar truss", "GearTrain": "Gear train",
             "CantileverBeam": "Cantilever beam"}

# official CEC-2017 categories, expressed in this paper's opfunu labels.
# The suite withdraws official F2, and opfunu renumbers the remainder
# consecutively, so paper label Fn = official F(n+1) for n >= 2 (see the
# numbering footnote in the manuscript).  Official categories are
# unimodal F1,F3 | simple multimodal F4-F10 | hybrid F11-F20 |
# composition F21-F30, which maps onto the labels below.
# A category with more than seven functions is split into consecutive
# parts, so that no table exceeds six function columns and every cell
# keeps four significant digits without crowding.
CEC2017_GROUPS = [
    ("unimodal", "Unimodal", [1, 2]),
    ("multimodal", "Simple multimodal", list(range(3, 10))),
    ("hybrid_a", "Hybrid (part 1)", list(range(10, 15))),
    ("hybrid_b", "Hybrid (part 2)", list(range(15, 20))),
    ("composition_a", "Composition (part 1)", list(range(20, 25))),
    ("composition_b", "Composition (part 2)", list(range(25, 30))),
]

TIMING_ORDER = ["F1", "F13", "F22", "F8-2022-D20", "WeldedBeam",
                "SignalP1"]
TIMING_LABEL = {"F1": "CEC17 F1", "F13": "CEC17 F13", "F22": "CEC17 F22",
                "F8-2022-D20": "CEC22 F8 (D20)",
                "WeldedBeam": "Welded beam", "SignalP1": "Signal P1"}


# --------------------------------------------------------------------
# formatting helpers
# --------------------------------------------------------------------
def fmt(x, sig=4):
    """Compact, journal-readable number.

    Plain decimal with `sig` significant digits inside the range a
    reader can parse at a glance, three-significant-digit scientific
    notation outside it.  The same rule is applied to a mean and to its
    standard deviation, so the two halves of a cell are always in the
    same notation.  Full precision (and the best/worst runs) stays in
    the appendix tables and in the source CSVs.
    """
    if not np.isfinite(x):
        return "--"
    if x == 0:
        return "0"
    if 1e-3 <= abs(x) < 1e5:
        return f"{x:.{sig}g}"
    return f"{x:.{max(sig - 2, 1)}e}"


def cell(mean, std, best=False, sig=4):
    """`mean +/- std`; the space before the sign lets a narrow PDF
    column wrap the cell into two lines without a resizebox."""
    m = fmt(mean, sig)
    if best:
        m = f"**{m}**"
    return f"{m} ±{fmt(std, sig)}"


def write(lines, name):
    path = os.path.join(RESULTS, name)
    with open(path, "w", encoding="utf8") as f:
        f.write("\n".join(lines) + "\n")
    return path


# --------------------------------------------------------------------
# generic transposed statistics table
# --------------------------------------------------------------------
def transposed_stats(df, index_col, items, labels, algos, out_name):
    """rows = algorithms, columns = test functions, cells = mean +/- std."""
    piv_m = df.pivot(index=index_col, columns="algo", values="mean")
    piv_s = df.pivot(index=index_col, columns="algo", values="std")
    header = "| Algorithm | " + " | ".join(labels) + " |"
    align = "|:---|" + "---:|" * len(items)
    lines = [header, align]
    best = {it: piv_m.loc[it, algos].idxmin() for it in items}
    for a in algos:
        row = [a]
        for it in items:
            row.append(cell(piv_m.loc[it, a], piv_s.loc[it, a],
                            best=(best[it] == a)))
        lines.append("| " + " | ".join(row) + " |")
    return write(lines, out_name)


# --------------------------------------------------------------------
# suite summary: Friedman rank + best-mean count + W/T/L against CA
# --------------------------------------------------------------------
def summary_table(ranks_csv, wilcoxon_csv, stats_csv, index_col,
                  out_name):
    ranks = pd.read_csv(ranks_csv).sort_values("mean_rank")
    wilc = pd.read_csv(wilcoxon_csv)
    stats = pd.read_csv(stats_csv)

    piv = stats.pivot(index=index_col, columns="algo", values="mean")
    best_counts = piv[ALGOS8].idxmin(axis=1).value_counts()
    n_items = piv.shape[0]

    lines = ["| Algorithm | Mean Friedman rank | Rank | Best mean on | "
             "CA's W / T / L against it |",
             "|:---|---:|---:|---:|:---:|"]
    for pos, (_, row) in enumerate(ranks.iterrows(), start=1):
        a = row["algo"]
        nbest = int(best_counts.get(a, 0))
        if a == "CA":
            wtl = "--"
        else:
            sub = wilc[wilc.competitor == a]
            w = int(((sub.significant == "yes")
                     & (sub.v3_mean_direction == "better")).sum())
            lo = int(((sub.significant == "yes")
                      & (sub.v3_mean_direction == "worse")).sum())
            wtl = f"{w} / {n_items - w - lo} / {lo}"
        name = f"**{a}**" if a == "CA" else a
        # half-up rounding, so a rank of exactly x.xx5 prints as the
        # manuscript's prose already quotes it (3.625 -> 3.63)
        rank = str(Decimal(repr(row["mean_rank"])).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP))
        if a == "CA":
            rank = f"**{rank}**"
        lines.append(f"| {name} | {rank} | {pos} | {nbest} of {n_items} | "
                     f"{wtl} |")
    return write(lines, out_name)


# --------------------------------------------------------------------
# individual tables
# --------------------------------------------------------------------
def classical_tables():
    df = pd.read_csv(os.path.join(RESULTS, "benchmark_stats.csv"))
    df = df.rename(columns={"Function": "func", "Algorithm": "algo",
                            "Mean": "mean", "Std": "std"})
    funcs = ["Sphere", "Rosenbrock", "Rastrigin", "Griewank", "Ackley",
             "Schwefel 2.22"]
    labels = ["F1 Sphere", "F2 Rosenbrock", "F3 Rastrigin",
              "F4 Griewank", "F5 Ackley", "F6 Schwefel 2.22"]
    transposed_stats(df, "func", funcs, labels, ALGOS_CLASSICAL,
                     "table_t_classical.md")

    # Wilcoxon, transposed: rows = comparison, columns = function
    wl = pd.read_csv(os.path.join(RESULTS, "wilcoxon.csv"))
    mark = {"CA better": "(+)", "CA worse": "(-)",
            "not significant": "(=)"}
    lines = ["| Comparison | " + " | ".join(labels) + " |",
             "|:---|" + "---:|" * len(funcs)]
    for comp in ["CA vs CA-static", "CA vs GWO", "CA vs PSO", "CA vs GA",
                 "CA vs SA"]:
        row = [comp]
        for fn in funcs:
            r = wl[(wl.Comparison == comp) & (wl.Function == fn)].iloc[0]
            row.append(f"{r['p-value']:.2e} "
                       f"{mark[r['Significant (a=0.05)']]}")
        lines.append("| " + " | ".join(row) + " |")
    write(lines, "table_t_classical_wilcoxon.md")

    # ANOVA, transposed: two rows
    an = pd.read_csv(os.path.join(RESULTS, "anova.csv")).set_index(
        "Function")
    lines = ["| Statistic | " + " | ".join(labels) + " |",
             "|:---|" + "---:|" * len(funcs)]
    lines.append("| $F$ | " + " | ".join(
        f"{an.loc[f, 'F-statistic']:.1f}" for f in funcs) + " |")
    lines.append("| $p$ | " + " | ".join(
        f"{an.loc[f, 'p-value']:.1e}" for f in funcs) + " |")
    write(lines, "table_t_classical_anova.md")


def cec2017_tables():
    stats = pd.read_csv(os.path.join(RESULTS, "cec2017_stats.csv"))
    summary_table(os.path.join(RESULTS, "cec2017_mean_ranks.csv"),
                  os.path.join(RESULTS, "cec2017_wilcoxon.csv"),
                  os.path.join(RESULTS, "cec2017_stats.csv"), "func",
                  "table_t_cec2017_summary.md")
    present = set(stats["func"].unique())
    for key, _label, nums in CEC2017_GROUPS:
        items = [f"F{n}" for n in nums if f"F{n}" in present]
        transposed_stats(stats, "func", items, items, ALGOS8,
                         f"table_t_cec2017_{key}.md")


def cec2022_tables():
    stats = pd.read_csv(os.path.join(RESULTS, "cec2022_stats.csv"))
    summary_table(os.path.join(RESULTS, "cec2022_mean_ranks.csv"),
                  os.path.join(RESULTS, "cec2022_wilcoxon.csv"),
                  os.path.join(RESULTS, "cec2022_stats.csv"), "func",
                  "table_t_cec2022_summary.md")
    for dim in ("D10", "D20"):
        items = sorted([f for f in stats["func"].unique()
                        if f.endswith(f"-{dim}")],
                       key=lambda s: int(s[1:s.index("-")]))
        labels = [it.split("-")[0] for it in items]
        transposed_stats(stats, "func", items, labels, ALGOS8,
                         f"table_t_cec2022_{dim}.md")


def engineering_tables():
    stats = pd.read_csv(os.path.join(RESULTS, "engineering_stats.csv"))
    summary_table(os.path.join(RESULTS, "engineering_mean_ranks.csv"),
                  os.path.join(RESULTS, "engineering_wilcoxon.csv"),
                  os.path.join(RESULTS, "engineering_stats.csv"),
                  "problem", "table_t_engineering_summary.md")
    labels = [ENG_LABEL[p] for p in ENG_ORDER]
    transposed_stats(stats, "problem", ENG_ORDER, labels, ALGOS8,
                     "table_t_engineering.md")


def timing_table():
    t = pd.read_csv(os.path.join(RESULTS, "timing_stats.csv"))
    time_p = t.pivot(index="problem", columns="algo",
                     values="mean_time_s")
    over = t.pivot(index="problem", columns="algo",
                   values="evals_over_core")
    rel = t.pivot(index="problem", columns="algo",
                  values="relative_time_vs_GA")
    labels = [TIMING_LABEL[p] for p in TIMING_ORDER]
    lines = ["| Algorithm | " + " | ".join(labels)
             + " | Evals / core budget | Time vs GA |",
             "|:---|" + "---:|" * (len(TIMING_ORDER) + 2)]
    for a in ALGOS8:
        row = [a] + [f"{time_p.loc[p, a]:.2f}" for p in TIMING_ORDER]
        row.append(f"{over[a].mean():.3f}")
        row.append(f"{rel[a].mean():.2f}")
        lines.append("| " + " | ".join(row) + " |")
    write(lines, "table_t_timing.md")


def traffic_table():
    st = pd.read_csv(os.path.join(RESULTS, "traffic_stats.csv"))
    st = st.set_index("Algorithm")
    wl_path = os.path.join(RESULTS, "table_traffic_wilcoxon.md")
    pvals, verdict = {}, {}
    with open(wl_path, encoding="utf8") as f:
        for line in f:
            parts = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(parts) >= 3 and parts[0].startswith("CA vs "):
                comp = parts[0][len("CA vs "):]
                pvals[comp] = parts[1]
                verdict[comp] = parts[2]
    lines = ["| Algorithm | Mean delay ± std (veh·h/h) | Best | Worst | "
             "$p$ vs CA | Outcome |",
             "|:---|---:|---:|---:|---:|:---|"]
    best_mean = st.loc[ALGOS_TRAFFIC, "Mean delay (veh-h/h)"].idxmin()
    for a in ALGOS_TRAFFIC:
        r = st.loc[a]
        # the five means differ only in the third decimal, so this table
        # is printed at six significant digits (the spread the paper's
        # own discussion reports); everywhere else four is enough
        c = cell(r["Mean delay (veh-h/h)"], r["Std"],
                 best=(a == best_mean), sig=6)
        p = pvals.get(a, "--")
        v = verdict.get(a, "--")
        if a == "CA":
            p, v = "--", "--"
        lines.append(f"| {a} | {c} | {fmt(r['Best'], 6)} | "
                     f"{fmt(r['Worst'], 6)} | {p} | {v} |")
    write(lines, "table_t_traffic.md")


def main():
    classical_tables()
    cec2017_tables()
    cec2022_tables()
    engineering_tables()
    timing_table()
    traffic_table()
    print("Wrote transposed tables (algorithms as rows) to results/")


if __name__ == "__main__":
    main()
