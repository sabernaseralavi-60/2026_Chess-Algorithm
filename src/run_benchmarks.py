"""
run_benchmarks.py
=================
Full experimental protocol for benchmarking the Chess Algorithm (CA)
against GA, PSO, SA and GWO on six standard test functions.

Protocol
--------
* dimension D = 30, population N = 30, iterations T = 500
* identical evaluation budget: N * T = 15,000 evaluations per run
* R = 30 independent runs per (algorithm, function) pair
* statistics: mean, std, best, worst; Wilcoxon rank-sum tests
  (CA vs. each competitor); one-way ANOVA per function
* outputs: results/*.csv, results/*.md (Quarto-includable tables),
  figures/*.png (300 dpi convergence curves and box plots)

Reproduce with:  python src/run_benchmarks.py
"""

import time
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from benchmark_functions import BENCHMARKS
from algorithms import (chess_algorithm_v3, chess_algorithm_v2,
                        genetic_algorithm, particle_swarm,
                        simulated_annealing, grey_wolf)

# ----------------------------------------------------------------------
DIM, POP, ITERS, RUNS = 30, 30, 500, 30
SEED0 = 20260703
OUT_RES, OUT_FIG = "../results", "../figures"

# "CA" is the adaptive Chess Algorithm; "CA-static" is the same operator
# set with the adaptive phase-selection machinery disabled, used
# throughout this paper as the ablation baseline.
ALGORITHMS = {
    "CA": chess_algorithm_v3, "CA-static": chess_algorithm_v2,
    "GA": genetic_algorithm, "PSO": particle_swarm,
    "SA": simulated_annealing, "GWO": grey_wolf,
}
ALG_ORDER = ["CA", "CA-static", "GA", "PSO", "SA", "GWO"]
COLORS = {"CA": "#1a1a2e", "CA-static": "#5b6ee1", "GA": "#c0392b",
          "PSO": "#2980b9", "SA": "#8e44ad", "GWO": "#27ae60"}
STYLES = {"CA": "-", "CA-static": (0, (4, 1)), "GA": "--", "PSO": "-.",
          "SA": ":", "GWO": (0, (3, 1, 1, 1))}

plt.rcParams.update({
    "font.family": "serif", "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 300,
})


def run_all():
    curves = {}   # (fname, alg) -> array (RUNS, ITERS)
    finals = {}   # (fname, alg) -> array (RUNS,)

    for fi, (fname, (fun, lb, ub, label)) in enumerate(BENCHMARKS.items()):
        for alg in ALG_ORDER:
            opt = ALGORITHMS[alg]
            C = np.empty((RUNS, ITERS))
            B = np.empty(RUNS)
            t0 = time.time()
            for r in range(RUNS):
                rng = np.random.default_rng(SEED0 + 1000 * fi + r)
                _, bf, curve = opt(fun, lb, ub, DIM, POP, ITERS, rng)
                C[r], B[r] = curve, bf
            curves[(fname, alg)] = C
            finals[(fname, alg)] = B
            print(f"{fname:16s} {alg:4s} mean={B.mean():.3e} "
                  f"std={B.std():.3e}  ({time.time()-t0:.1f}s)", flush=True)
    return curves, finals


def make_tables(finals):
    # ---- descriptive statistics ----
    rows = []
    for fname, (_, _, _, label) in BENCHMARKS.items():
        for alg in ALG_ORDER:
            B = finals[(fname, alg)]
            rows.append({"Function": label, "Algorithm": alg,
                         "Mean": B.mean(), "Std": B.std(),
                         "Best": B.min(), "Worst": B.max()})
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT_RES}/benchmark_stats.csv", index=False)

    # ---- Wilcoxon rank-sum: CA vs each competitor ----
    wrows = []
    for fname, (_, _, _, label) in BENCHMARKS.items():
        ca = finals[(fname, "CA")]
        for alg in ALG_ORDER[1:]:
            other = finals[(fname, alg)]
            stat, p = stats.ranksums(ca, other)
            verdict = ("CA better" if (p < 0.05 and ca.mean() < other.mean())
                       else "CA worse" if (p < 0.05) else "not significant")
            wrows.append({"Function": label, "Comparison": f"CA vs {alg}",
                          "p-value": p, "Significant (a=0.05)": verdict})
    wf = pd.DataFrame(wrows)
    wf.to_csv(f"{OUT_RES}/wilcoxon.csv", index=False)

    # ---- one-way ANOVA per function ----
    arows = []
    for fname, (_, _, _, label) in BENCHMARKS.items():
        groups = [finals[(fname, a)] for a in ALG_ORDER]
        Fstat, p = stats.f_oneway(*groups)
        arows.append({"Function": label, "F-statistic": Fstat, "p-value": p})
    af = pd.DataFrame(arows)
    af.to_csv(f"{OUT_RES}/anova.csv", index=False)

    # ---- markdown tables for direct Quarto inclusion ----
    def sci(x):
        return f"{x:.3e}"

    with open(f"{OUT_RES}/table_stats.md", "w", encoding="utf8") as fmd:
        fmd.write("| Function | Algorithm | Mean | Std | Best | Worst |\n")
        fmd.write("|---|---|---:|---:|---:|---:|\n")
        for fname, (_, _, _, label) in BENCHMARKS.items():
            sub = df[df.Function == label]
            best_mean = sub.Mean.min()
            for _, r in sub.iterrows():
                m = sci(r.Mean)
                if np.isclose(r.Mean, best_mean, rtol=1e-12, atol=0):
                    m = f"**{m}**"
                fmd.write(f"| {r.Function} | {r.Algorithm} | {m} | "
                          f"{sci(r.Std)} | {sci(r.Best)} | {sci(r.Worst)} |\n")

    with open(f"{OUT_RES}/table_wilcoxon.md", "w", encoding="utf8") as fmd:
        fmd.write("| Function | Comparison | p-value | Result (α = 0.05) |\n")
        fmd.write("|---|---|---:|---|\n")
        for _, r in wf.iterrows():
            fmd.write(f"| {r['Function']} | {r['Comparison']} | "
                      f"{r['p-value']:.3e} | {r['Significant (a=0.05)']} |\n")

    with open(f"{OUT_RES}/table_anova.md", "w", encoding="utf8") as fmd:
        fmd.write("| Function | F-statistic | p-value |\n|---|---:|---:|\n")
        for _, r in af.iterrows():
            fmd.write(f"| {r['Function']} | {r['F-statistic']:.3f} | "
                      f"{r['p-value']:.3e} |\n")
    return df, wf, af


def make_figures(curves):
    # ---- convergence curves (2 x 3 grid) ----
    fig, axes = plt.subplots(2, 3, figsize=(11, 6.2))
    for ax, (fname, (_, _, _, label)) in zip(axes.ravel(), BENCHMARKS.items()):
        for alg in ALG_ORDER:
            m = curves[(fname, alg)].mean(axis=0)
            m = np.maximum(m, 1e-300)
            ax.semilogy(m, color=COLORS[alg], linestyle=STYLES[alg],
                        linewidth=1.4, label=alg)
        ax.set_title(label, fontsize=10)
        ax.set_xlabel("Iteration", fontsize=8)
        ax.set_ylabel("Best fitness (log)", fontsize=8)
        ax.tick_params(labelsize=7)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=5, frameon=False)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(f"{OUT_FIG}/convergence_all.png", bbox_inches="tight")
    plt.close(fig)

    # ---- box plots of final fitness ----
    fig, axes = plt.subplots(2, 3, figsize=(11, 6.2))
    for ax, (fname, (_, _, _, label)) in zip(axes.ravel(), BENCHMARKS.items()):
        data = [np.maximum(FINALS[(fname, a)], 1e-300) for a in ALG_ORDER]
        bp = ax.boxplot(data, tick_labels=ALG_ORDER, patch_artist=True,
                        medianprops=dict(color="black"))
        for patch, alg in zip(bp["boxes"], ALG_ORDER):
            patch.set_facecolor(COLORS[alg])
            patch.set_alpha(0.55)
        ax.set_yscale("log")
        ax.set_title(label, fontsize=10)
        ax.tick_params(labelsize=7)
    fig.tight_layout()
    fig.savefig(f"{OUT_FIG}/boxplots_all.png", bbox_inches="tight")
    plt.close(fig)


def make_flowchart():
    """Render the CA flowchart as a publication figure (matplotlib)."""
    fig, ax = plt.subplots(figsize=(6.4, 9.2))
    ax.axis("off")

    def box(x, y, w, h, text, fc="#f4f4f8", shape="rect"):
        if shape == "diamond":
            xs = [x, x + w / 2, x + w, x + w / 2, x]
            ys = [y + h / 2, y + h, y + h / 2, y, y + h / 2]
            ax.fill(xs, ys, fc, ec="#1a1a2e", lw=1.0, zorder=2)
        else:
            ax.add_patch(plt.Rectangle((x, y), w, h, fc=fc, ec="#1a1a2e",
                                       lw=1.0, zorder=2,
                                       joinstyle="round"))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=7.6, zorder=3)

    def arrow(x1, y1, x2, y2, label=None):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color="#1a1a2e", lw=1.0))
        if label:
            ax.text((x1 + x2) / 2 + 0.02, (y1 + y2) / 2, label, fontsize=7)

    W, H, X0 = 0.56, 0.052, 0.22
    steps = [
        ("Initialize board:\nrandom population, evaluate fitness", "#e8e8f0"),
        ("Rank pieces and assign roles\n(King · Queens · Rooks · Bishops · Knights · Pawns)", "#f4f4f8"),
        ("Development schedule a(t);\npinning probability p_pin(t); budget θ(t)", "#f4f4f8"),
        ("Apply role moves\n(Queen / Rook / Bishop / Knight / Pawn)", "#f4f4f8"),
        ("Pinning: freeze subset of coordinates\nto the King's values", "#f4f4f8"),
        ("Sacrifice: accept worsening moves\nwith prob. exp(−Δ/θ)", "#f4f4f8"),
        ("En passant: local capture\naround the King", "#f4f4f8"),
        ("Castling every c iterations:\nsafeguarded block exchange", "#f4f4f8"),
        ("Update King; re-rank\n(pawn promotion)", "#f4f4f8"),
    ]
    ys = np.linspace(0.90, 0.16, len(steps))
    for (txt, fc), y in zip(steps, ys):
        box(X0, y, W, H, txt, fc)
    for y1, y2 in zip(ys[:-1], ys[1:]):
        arrow(X0 + W / 2, y1, X0 + W / 2, y2 + H)

    box(X0 + 0.06, 0.045, W - 0.12, 0.055, "Checkmate?\n(t = T)", "#e8e8f0",
        shape="diamond")
    arrow(X0 + W / 2, ys[-1], X0 + W / 2, 0.10)
    # loop back
    ax.annotate("", xy=(X0 + W + 0.06, ys[1] + H / 2),
                xytext=(X0 + W - 0.05, 0.072),
                arrowprops=dict(arrowstyle="->", color="#1a1a2e", lw=1.0,
                                connectionstyle="angle,angleA=0,angleB=90"))
    ax.text(X0 + W + 0.075, 0.5, "No", fontsize=8, ha="left")
    # "Yes" branch: arrow stops at the Return-King box edge, label above it
    arrow(X0 + 0.06, 0.0725, 0.135, 0.0725)
    ax.text((X0 + 0.06 + 0.135) / 2, 0.088, "Yes", fontsize=8, ha="center")
    box(0.005, 0.042, 0.12, 0.06, "Return\nKing", "#dcdce8")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    fig.savefig(f"{OUT_FIG}/ca_flowchart.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(OUT_RES, exist_ok=True)
    os.makedirs(OUT_FIG, exist_ok=True)

    t0 = time.time()
    CURVES, FINALS = run_all()
    make_tables(FINALS)
    make_figures(CURVES)
    make_flowchart()
    np.savez_compressed(f"{OUT_RES}/raw_finals.npz",
                        **{f"{f}__{a}": FINALS[(f, a)]
                           for f in BENCHMARKS for a in ALG_ORDER})
    print(f"\nTotal wall time: {time.time()-t0:.1f}s")
