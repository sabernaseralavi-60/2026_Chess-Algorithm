"""
phase2_3_analysis.py
====================
Post-processing for Phases 2-3: merge the partitioned CEC-2017 outputs,
compute Friedman statistics and win/tie/loss summaries, and render the
300-DPI convergence figures.

Outputs:
    results/cec2017_stats.csv, cec2017_wilcoxon.csv, raw_cec2017.npz
        (merged from *_part* files)
    results/cec2017_mean_ranks.csv, engineering_mean_ranks.csv
    results/phase2_3_summary.txt        (win/tie/loss + Friedman)
    figures/cec2017_convergence.png     (6 representative functions)
    figures/engineering_convergence.png (7 problems)

Usage:  python src/phase2_3_analysis.py
"""

import glob
import os
import sys

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

# identity palette (validated: lightness band, chroma floor, CVD
# separation, contrast — all PASS on light surface) + line styles as
# secondary encoding for print/CVD
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


def fnum(label):
    return int(label[1:])


def merge_cec():
    """Merge *_part*.csv / *_part*.npz into single files."""
    stats_parts = sorted(glob.glob(
        os.path.join(RESULTS, "cec2017_stats_part*.csv")))
    if stats_parts:
        df = pd.concat([pd.read_csv(p) for p in stats_parts])
        df = df.sort_values(["func", "algo"],
                            key=lambda s: (s.map(fnum) if s.name == "func"
                                           else s))
        df.to_csv(os.path.join(RESULTS, "cec2017_stats.csv"), index=False)
        wl = pd.concat([pd.read_csv(p) for p in sorted(glob.glob(
            os.path.join(RESULTS, "cec2017_wilcoxon_part*.csv")))])
        wl = wl.sort_values("func", key=lambda s: s.map(fnum))
        wl.to_csv(os.path.join(RESULTS, "cec2017_wilcoxon.csv"),
                  index=False)
        raw = {}
        for p in sorted(glob.glob(
                os.path.join(RESULTS, "raw_cec2017_part*.npz"))):
            with np.load(p) as z:
                raw.update({k: z[k] for k in z.files})
        np.savez_compressed(os.path.join(RESULTS, "raw_cec2017.npz"),
                            **raw)
    stats = pd.read_csv(os.path.join(RESULTS, "cec2017_stats.csv"))
    wilc = pd.read_csv(os.path.join(RESULTS, "cec2017_wilcoxon.csv"))
    raw = dict(np.load(os.path.join(RESULTS, "raw_cec2017.npz")))
    return stats, wilc, raw


def audit_below_optimum(stats, wilc, raw, out_lines, tol=1.0):
    """Post-hoc integrity audit: exclude any function where an
    algorithm's best error dips below -tol, i.e. the optimizer found a
    point better than the library's claimed global optimum. Caught F9
    this way during Phase 1 tuning; F15 (Hybrid 6) surfaced the same
    defect during the Phase 2 run despite passing the f(x*) preflight
    check (the bug lies elsewhere in the domain, not at x*)."""
    bad = sorted(stats.loc[stats["best"] < -tol, "func"].unique(),
                key=fnum)
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


def summarize(stats, wilc, index_col, out_lines, tag):
    piv = stats.pivot(index=index_col, columns="algo", values="mean")
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
    n_items = wilc[index_col].nunique()
    for comp in [a for a in ALGOS if a != "CA"]:
        sub = wilc[wilc.competitor == comp]
        w = ((sub.significant == "yes")
             & (sub.v3_mean_direction == "better")).sum()
        lo = ((sub.significant == "yes")
              & (sub.v3_mean_direction == "worse")).sum()
        tie = n_items - w - lo
        out_lines.append(f"  vs {comp:6s}: {w:2d} win / {tie:2d} tie / "
                         f"{lo:2d} loss")
    return mean_ranks


def cec_figure(raw):
    reps = ["F1", "F4", "F10", "F13", "F22", "F26"]
    titles = {"F1": "F1 Bent Cigar", "F4": "F4 Rastrigin (S&R)",
              "F10": "F10 Hybrid 1", "F13": "F13 Hybrid 4",
              "F22": "F22 Composition 3", "F26": "F26 Composition 7"}
    fig, axes = plt.subplots(2, 3, figsize=(11.0, 6.2))
    for ax, label in zip(axes.ravel(), reps):
        for a in ALGOS:
            med = raw[f"{label}__{a}__med"]
            ax.plot(np.maximum(med, 1e-12), color=COLORS[a],
                    linestyle=STYLES[a], lw=1.4, label=a)
        ax.set_yscale("log")
        ax.set_title(titles.get(label, label), fontsize=9.5)
        ax.tick_params(labelsize=7.5)
        ax.set_xlabel("Iteration", fontsize=8)
        ax.set_ylabel("Median error $f - f^{*}$", fontsize=8)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=8, frameon=False,
               fontsize=8.5)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(os.path.join(FIGURES, "cec2017_convergence.png"),
                bbox_inches="tight")
    plt.close(fig)


def eng_figure(raw, problems):
    fig, axes = plt.subplots(2, 4, figsize=(12.6, 6.0))
    axs = axes.ravel()
    for ax, pname in zip(axs, problems):
        for a in ALGOS:
            med = raw[f"{pname}__{a}__med"]
            ax.plot(np.maximum(med, 1e-14), color=COLORS[a],
                    linestyle=STYLES[a], lw=1.4, label=a)
        ax.set_yscale("log")
        ax.set_title(pname, fontsize=9.5)
        ax.tick_params(labelsize=7.5)
        ax.set_xlabel("Iteration", fontsize=8)
        ax.set_ylabel("Median objective", fontsize=8)
    axs[-1].axis("off")
    handles, labels = axs[0].get_legend_handles_labels()
    axs[-1].legend(handles, labels, loc="center", frameon=False,
                   fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES, "engineering_convergence.png"),
                bbox_inches="tight")
    plt.close(fig)


def main():
    out_lines = []

    stats_raw, wilc, raw = merge_cec()
    # preserve the pre-audit merge (includes F15/F19/F21) for transparency
    stats_raw.to_csv(
        os.path.join(RESULTS, "cec2017_stats_raw_unaudited.csv"),
        index=False)
    stats, wilc, raw = audit_below_optimum(stats_raw, wilc, raw, out_lines)
    # cec2017_stats.csv / cec2017_wilcoxon.csv now hold ONLY the validated
    # functions used in the paper's headline analysis
    stats.to_csv(os.path.join(RESULTS, "cec2017_stats.csv"), index=False)
    wilc.to_csv(os.path.join(RESULTS, "cec2017_wilcoxon.csv"), index=False)
    n_funcs = stats["func"].nunique()
    out_lines.append(f"CEC-2017: {n_funcs} functions x {len(ALGOS)} "
                     f"algorithms x 30 runs")
    summarize(stats, wilc, "func", out_lines, "cec2017")
    cec_figure(raw)

    est = pd.read_csv(os.path.join(RESULTS, "engineering_stats.csv"))
    ewl = pd.read_csv(os.path.join(RESULTS, "engineering_wilcoxon.csv"))
    eraw = dict(np.load(os.path.join(RESULTS, "raw_engineering.npz")))
    summarize(est, ewl, "problem", out_lines, "engineering")
    eng_figure(eraw, list(est["problem"].unique()))

    report = "\n".join(out_lines)
    with open(os.path.join(RESULTS, "phase2_3_summary.txt"), "w",
              encoding="utf8") as f:
        f.write(report + "\n")
    print(report)


if __name__ == "__main__":
    main()
