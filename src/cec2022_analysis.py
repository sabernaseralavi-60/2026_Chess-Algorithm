"""
cec2022_analysis.py
=====================
Phase B post-processing for CEC-2022 (adapted from phase2_3_analysis.py):
merge the 4 partitioned outputs, run the same below-optimum integrity
audit used for CEC-2017, apply the F3 near-flatness mechanical rule,
compute Friedman ranks and CA win/tie/loss overall AND per dimension,
and render the convergence figure.

Outputs:
    results/cec2022_stats.csv, cec2022_wilcoxon.csv, raw_cec2022.npz
        (merged from *_part* files)
    results/cec2022_stats_raw_unaudited.csv   (pre-audit, for transparency)
    results/cec2022_mean_ranks.csv, cec2022_mean_ranks_D10.csv,
        cec2022_mean_ranks_D20.csv
    results/table_cec2022_audit.md
    results/cec2022_summary.txt          (win/tie/loss + Friedman, overall
                                          and per-dim)
    figures/cec2022_convergence.png      (2x3: 3 representative functions
                                          per dimension)

Usage:  python src/cec2022_analysis.py
"""

import glob
import os

import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
FIGURES = os.path.join(ROOT, "figures")
os.makedirs(FIGURES, exist_ok=True)

ALGOS = ["CA", "CA-static", "GWO", "PSO", "GA", "WOA", "L-SHADE", "CMA-ES"]
COLORS = {"CA": "#1d4ed8", "CA-static": "#c2410c", "GWO": "#059669",
          "PSO": "#be123c", "GA": "#a16207", "WOA": "#9333ea",
          "L-SHADE": "#0891b2", "CMA-ES": "#65a30d"}
STYLES = {"CA": "-", "CA-static": "--", "GWO": "-.", "PSO": ":",
          "GA": (0, (3, 1, 1, 1)), "WOA": (0, (5, 2)),
          "L-SHADE": (0, (1, 1)), "CMA-ES": (0, (4, 1, 1, 1, 1, 1))}

plt.rcParams.update({
    "font.family": "serif", "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 300, "savefig.dpi": 300,
})


def parse_label(label):
    """'F10-D20' -> (10, 20)"""
    fpart, dpart = label.split("-D")
    return int(fpart[1:]), int(dpart)


def merge():
    stats_parts = sorted(glob.glob(
        os.path.join(RESULTS, "cec2022_stats_part*.csv")))
    if stats_parts:
        df = pd.concat([pd.read_csv(p) for p in stats_parts])
        df = df.sort_values(["func", "algo"],
                            key=lambda s: (s.map(lambda l: parse_label(l))
                                           if s.name == "func" else s))
        df.to_csv(os.path.join(RESULTS, "cec2022_stats.csv"), index=False)
        wl = pd.concat([pd.read_csv(p) for p in sorted(glob.glob(
            os.path.join(RESULTS, "cec2022_wilcoxon_part*.csv")))])
        wl.to_csv(os.path.join(RESULTS, "cec2022_wilcoxon.csv"), index=False)
        raw = {}
        for p in sorted(glob.glob(
                os.path.join(RESULTS, "raw_cec2022_part*.npz"))):
            with np.load(p) as z:
                raw.update({k: z[k] for k in z.files})
        np.savez_compressed(os.path.join(RESULTS, "raw_cec2022.npz"), **raw)
    stats = pd.read_csv(os.path.join(RESULTS, "cec2022_stats.csv"))
    wilc = pd.read_csv(os.path.join(RESULTS, "cec2022_wilcoxon.csv"))
    raw = dict(np.load(os.path.join(RESULTS, "raw_cec2022.npz")))
    return stats, wilc, raw


def audit_below_optimum(stats, wilc, raw, out_lines, tol=1.0):
    """Same integrity rule as CEC-2017's post-hoc audit: exclude any
    (function, dimension) cell where an algorithm's best error dips
    below -tol, i.e. found a point better than the library's claimed
    global optimum."""
    bad = sorted(stats.loc[stats["best"] < -tol, "func"].unique(),
                key=parse_label)
    if bad:
        out_lines.append(f"\n== Post-hoc integrity audit: EXCLUDED "
                         f"{len(bad)} function(s) with best error < "
                         f"-{tol:g} (below the library's claimed "
                         f"f_global -- an opfunu defect, not a CA "
                         f"artifact) ==")
        for b in bad:
            worst_neg = stats.loc[stats.func == b, "best"].min()
            out_lines.append(f"  {b}: min best error = {worst_neg:.4g}")
        stats = stats[~stats.func.isin(bad)].copy()
        wilc = wilc[~wilc.func.isin(bad)].copy()
        raw = {k: v for k, v in raw.items()
              if not any(k.startswith(f"{b}__") for b in bad)}
    else:
        out_lines.append("\n== Post-hoc integrity audit: all functions "
                         "clean (no algorithm went below f_global) ==")
    return stats, wilc, raw


def f3_flatness_rule(stats, wilc, raw, out_lines, flat_tol=1.0):
    """Mechanical rule: exclude F3 at a dimension only if the worst-mean
    algorithm's median final error is < flat_tol there (near-flat, not
    meaningfully discriminating); otherwise keep it, no mention."""
    excluded = []
    for dim in (10, 20):
        label = f"F3-D{dim}"
        sub = stats[stats.func == label]
        if sub.empty:
            continue
        worst_algo = sub.set_index("algo")["mean"].idxmax()
        med_curve = raw.get(f"{label}__{worst_algo}__med")
        if med_curve is None:
            continue
        final_err = float(med_curve[-1])
        if final_err < flat_tol:
            excluded.append((label, worst_algo, final_err))
    if excluded:
        out_lines.append("\n== F3 near-flatness rule ==")
        for label, worst_algo, final_err in excluded:
            out_lines.append(
                f"  {label}: EXCLUDED (worst-mean algorithm {worst_algo}, "
                f"median final error {final_err:.4g} < {flat_tol:g})")
        bad = [l for l, _, _ in excluded]
        stats = stats[~stats.func.isin(bad)].copy()
        wilc = wilc[~wilc.func.isin(bad)].copy()
        raw = {k: v for k, v in raw.items()
              if not any(k.startswith(f"{b}__") for b in bad)}
    return stats, wilc, raw


def summarize(stats, wilc, out_lines, dim_filter=None):
    tag = "cec2022" if dim_filter is None else f"cec2022_D{dim_filter}"
    s = stats if dim_filter is None else stats[
        stats.func.apply(lambda l: parse_label(l)[1] == dim_filter)]
    w = wilc if dim_filter is None else wilc[
        wilc.func.apply(lambda l: parse_label(l)[1] == dim_filter)]
    if s.empty:
        return None

    piv = s.pivot(index="func", columns="algo", values="mean")
    ranks = piv.rank(axis=1, method="average")
    mean_ranks = ranks.mean().sort_values()
    mean_ranks.to_csv(os.path.join(RESULTS, f"{tag}_mean_ranks.csv"),
                      header=["mean_rank"])
    fr = friedmanchisquare(*[piv[a].values for a in ALGOS])
    out_lines.append(f"\n== {tag}: mean Friedman ranks "
                     f"(chi2={fr.statistic:.2f}, p={fr.pvalue:.3g}) ==")
    out_lines.append(mean_ranks.to_string())

    out_lines.append(f"\n== {tag}: CA win/tie/loss "
                     f"(Wilcoxon rank-sum, alpha=0.05) ==")
    n_items = w["func"].nunique()
    for comp in [a for a in ALGOS if a != "CA"]:
        sub = w[w.competitor == comp]
        win = ((sub.significant == "yes")
              & (sub.v3_mean_direction == "better")).sum()
        loss = ((sub.significant == "yes")
               & (sub.v3_mean_direction == "worse")).sum()
        tie = n_items - win - loss
        out_lines.append(f"  vs {comp:9s}: {win:2d} win / {tie:2d} tie / "
                         f"{loss:2d} loss")
    return mean_ranks


def convergence_figure(raw, stats):
    present = set(stats["func"].unique())
    reps10 = [f for f in ["F1-D10", "F6-D10", "F9-D10"] if f in present]
    reps20 = [f for f in ["F1-D20", "F6-D20", "F9-D20"] if f in present]
    reps = reps10 + reps20
    fig, axes = plt.subplots(2, 3, figsize=(11.0, 6.2))
    for ax, label in zip(axes.ravel(), reps):
        for a in ALGOS:
            med = raw[f"{label}__{a}__med"]
            ax.plot(np.maximum(med, 1e-12), color=COLORS[a],
                    linestyle=STYLES[a], lw=1.4, label=a)
        ax.set_yscale("log")
        ax.set_title(label, fontsize=9.5)
        ax.tick_params(labelsize=7.5)
        ax.set_xlabel("Iteration", fontsize=8)
        ax.set_ylabel("Median error $f - f^{*}$", fontsize=8)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=8, frameon=False,
               fontsize=8.5)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(os.path.join(FIGURES, "cec2022_convergence.png"),
               bbox_inches="tight")
    plt.close(fig)


def write_audit_table(n_before, excluded_below, excluded_f3):
    lines = ["| Function | Reason excluded |", "|---|---|"]
    for label in excluded_below:
        lines.append(f"| {label} | below-optimum (opfunu defect) |")
    for label, worst_algo, final_err in excluded_f3:
        lines.append(f"| {label} | near-flat (worst-mean {worst_algo} "
                     f"median final error {final_err:.3g} < 1.0) |")
    with open(os.path.join(RESULTS, "table_cec2022_audit.md"), "w",
             encoding="utf8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    out_lines = []
    stats_raw, wilc, raw = merge()
    stats_raw.to_csv(
        os.path.join(RESULTS, "cec2022_stats_raw_unaudited.csv"),
        index=False)

    n_before = sorted(stats_raw["func"].unique())
    stats, wilc, raw = audit_below_optimum(stats_raw, wilc, raw, out_lines)
    excluded_below = sorted(set(n_before) - set(stats["func"].unique()))

    before_f3 = set(stats["func"].unique())
    stats, wilc, raw = f3_flatness_rule(stats, wilc, raw, out_lines)
    excluded_f3_labels = sorted(before_f3 - set(stats["func"].unique()))
    # recompute the (label, worst_algo, final_err) triples for the table
    excluded_f3 = []
    for label in excluded_f3_labels:
        sub = stats_raw[stats_raw.func == label]
        worst_algo = sub.set_index("algo")["mean"].idxmax()
        raw_full = dict(np.load(os.path.join(RESULTS, "raw_cec2022.npz")))
        final_err = float(raw_full[f"{label}__{worst_algo}__med"][-1])
        excluded_f3.append((label, worst_algo, final_err))

    stats.to_csv(os.path.join(RESULTS, "cec2022_stats.csv"), index=False)
    wilc.to_csv(os.path.join(RESULTS, "cec2022_wilcoxon.csv"), index=False)

    write_audit_table(len(n_before), excluded_below, excluded_f3)

    n_funcs = stats["func"].nunique()
    out_lines.append(f"\nCEC-2022: {n_funcs} (function, dim) cells x "
                     f"{len(ALGOS)} algorithms x 30 runs "
                     f"(D10={stats.func.apply(lambda l: parse_label(l)[1]==10).sum()}, "
                     f"D20={stats.func.apply(lambda l: parse_label(l)[1]==20).sum()})")
    summarize(stats, wilc, out_lines, dim_filter=None)
    summarize(stats, wilc, out_lines, dim_filter=10)
    summarize(stats, wilc, out_lines, dim_filter=20)
    convergence_figure(raw, stats)

    report = "\n".join(out_lines)
    with open(os.path.join(RESULTS, "cec2022_summary.txt"), "w",
             encoding="utf8") as f:
        f.write(report + "\n")
    print(report)


if __name__ == "__main__":
    main()
