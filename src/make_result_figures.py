"""
make_result_figures.py
======================
Result figures that the manuscript previously carried only as tables.

Everything here is read from committed result files -- no experiment is
re-run and no value is recomputed beyond the averaging that the source
tables already document:

    fig_cec2017_distributions()  results/raw_cec2017.npz (per-run finals)
    fig_ablation()               results/ablation_ratios.csv
    fig_sensitivity()            results/sensitivity_ratios.csv
    fig_standing()               results/*_mean_ranks.csv

Usage:  python src/make_result_figures.py
"""

import os

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from figstyle import (CAND, COLORS, ELITE, FILL3, INK, KING, MUTED,  # noqa: E402
                      save, use_style)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
FIGURES = os.path.join(ROOT, "figures")

ALGOS8 = ["CA", "CA-static", "GWO", "PSO", "GA", "WOA", "L-SHADE",
          "CMA-ES"]
SPECIALIZED = ("L-SHADE", "CMA-ES")

# the six representative CEC-2017 functions of the convergence figure,
# one or more per official category
REPS = ["F1", "F4", "F10", "F13", "F22", "F26"]
REP_TITLES = {"F1": "F1 Bent Cigar (unimodal)",
              "F4": "F4 Rastrigin (multimodal)",
              "F10": "F10 Hybrid 1", "F13": "F13 Hybrid 4",
              "F22": "F22 Composition 3", "F26": "F26 Composition 7"}

MECH_LABEL = {
    "en_passant": "En passant", "knight_fork": "Knight's fork",
    "threefold": "Threefold repetition", "sacrifice": "Sacrifice",
    "pinning": "Pinning", "windmill": "Windmill",
    "opposition_init": "Opposition-based init.",
    "discovered_attack": "Discovered attack",
    "blockade": "Blockade response",
    "interference": "Novotny interference", "castling": "Castling",
    "royal_council": "Royal council",
}
PROB_LABEL = {"F1": "CEC17 F1", "F4": "CEC17 F4", "F13": "CEC17 F13",
              "F22": "CEC17 F22", "WeldedBeam": "Welded beam",
              "BerthP2": "Berth P2"}
SENS_LABEL = {
    "role_fractions_low": "Role fractions, low (.05/.10/.10/.15)",
    "role_fractions_high": "Role fractions, high (.15/.20/.20/.25)",
    "theta0_low": r"Sacrifice constant $\theta_0=0.05$",
    "theta0_high": r"Sacrifice constant $\theta_0=0.2$",
    "castling_period_low": r"Castling period $c=5$",
    "castling_period_high": r"Castling period $c=20$",
    "stall_break_low": "Blockade threshold $=15$",
    "stall_break_high": "Blockade threshold $=40$",
    "pin_max_low": "Pinning cap $=0.15$",
    "pin_max_high": "Pinning cap $=0.50$",
}


# --------------------------------------------------------------------
def fig_cec2017_distributions():
    use_style()
    raw = np.load(os.path.join(RESULTS, "raw_cec2017.npz"))
    fig, axes = plt.subplots(2, 3, figsize=(11.0, 6.0))
    for ax, label in zip(axes.ravel(), REPS):
        data = [np.maximum(raw[f"{label}__{a}__finals"], 1e-12)
                for a in ALGOS8]
        bp = ax.boxplot(data, patch_artist=True, widths=0.62,
                        medianprops=dict(color="black", lw=1.0),
                        flierprops=dict(marker="o", ms=2.0,
                                        markerfacecolor=MUTED,
                                        markeredgecolor="none"))
        for patch, a in zip(bp["boxes"], ALGOS8):
            patch.set_facecolor(COLORS[a])
            patch.set_alpha(0.55)
            patch.set_edgecolor(COLORS[a])
        for element in ("whiskers", "caps"):
            for line in bp[element]:
                line.set_color(MUTED)
                line.set_linewidth(0.8)
        ax.set_yscale("log")
        ax.set_xticks(range(1, len(ALGOS8) + 1))
        ax.set_xticklabels(ALGOS8, rotation=45, ha="right", fontsize=7)
        ax.set_ylabel("Final error $f - f^{*}$ (30 runs)", fontsize=8)
        ax.set_title(REP_TITLES[label], fontsize=9.5)
    fig.tight_layout()
    save(fig, os.path.join(FIGURES, "cec2017_boxplots.png"))


# --------------------------------------------------------------------
def fig_ablation():
    use_style()
    df = pd.read_csv(os.path.join(RESULTS, "ablation_ratios.csv"))
    mean_ratio = df.groupby("mechanism")["ratio_vs_full_ca"].mean()
    nsig = (df[df.significant == "yes"].groupby("mechanism").size()
            .reindex(mean_ratio.index).fillna(0).astype(int))
    order = mean_ratio.sort_values().index.tolist()

    fig = plt.figure(figsize=(9.8, 4.3))
    axl = fig.add_axes([0.185, 0.135, 0.415, 0.79])
    axr = fig.add_axes([0.705, 0.135, 0.275, 0.79])

    ypos = np.arange(len(order))
    vals = mean_ratio.loc[order].values
    colors = [CAND if nsig[m] >= 3 else ("#94a3b8" if nsig[m] == 0
                                         else ELITE) for m in order]
    axl.barh(ypos, vals, color=colors, height=0.68, alpha=0.85,
             edgecolor="none")
    axl.axvline(1.0, color=INK, lw=0.9)
    axl.set_xscale("log")
    axl.set_yticks(ypos)
    axl.set_yticklabels([MECH_LABEL[m] for m in order], fontsize=8)
    axl.set_xlabel("Mean final-error ratio, mechanism disabled / full CA "
                   "(log scale)", fontsize=8.2)
    axl.set_xlim(0.75, 4000)
    for y, m, v in zip(ypos, order, vals):
        axl.text(v * 1.12, y, f"{v:,.3g}  ({nsig[m]}/6)", va="center",
                 fontsize=7.2, color=INK)
    axl.text(1.03, len(order) - 0.35, "no effect", fontsize=7.0,
             color=MUTED)
    axl.set_title("(a)  mean over the six problems; (n/6) = problems "
                  "with a significant difference", fontsize=8.6,
                  loc="left")
    keys = [plt.Rectangle((0, 0), 1, 1, facecolor=c, alpha=0.85,
                          edgecolor="none", label=t)
            for c, t in ((CAND, "significant on 3 or more"),
                         (ELITE, "significant on 1-2"),
                         ("#94a3b8", "significant on none"))]
    axl.legend(handles=keys, loc="lower right", fontsize=7.2,
               title="of the six problems", title_fontsize=7.2)

    probs = ["F1", "F4", "F13", "F22", "WeldedBeam", "BerthP2"]
    width = 0.38
    xs = np.arange(len(probs))
    for k, (mech, col) in enumerate((("en_passant", CAND),
                                     ("knight_fork", KING))):
        sub = df[df.mechanism == mech].set_index("problem")
        vals = [sub.loc[p, "ratio_vs_full_ca"] for p in probs]
        sig = [sub.loc[p, "significant"] == "yes" for p in probs]
        axr.bar(xs + (k - 0.5) * width, vals, width=width, color=col,
                alpha=0.85, label=MECH_LABEL[mech])
        for x, v, s in zip(xs + (k - 0.5) * width, vals, sig):
            if s:
                axr.text(x, v * 1.25, "*", ha="center", fontsize=8.5,
                         color=INK)
    axr.axhline(1.0, color=INK, lw=0.9)
    axr.set_yscale("log")
    axr.set_xticks(xs)
    axr.set_xticklabels([PROB_LABEL[p] for p in probs], rotation=45,
                        ha="right", fontsize=7.4)
    axr.set_ylabel("Ratio (log scale)", fontsize=8.2)
    axr.legend(loc="upper right", fontsize=7.4)
    axr.set_title("(b)  the two load-bearing mechanisms, per problem "
                  "($*$: $p<0.05$)", fontsize=8.6, loc="left")
    save(fig, os.path.join(FIGURES, "ablation_contribution.png"))


# --------------------------------------------------------------------
def fig_sensitivity():
    use_style()
    df = pd.read_csv(os.path.join(RESULTS, "sensitivity_ratios.csv"))
    g = df.groupby("variant")["ratio_vs_default"]
    mean_r, lo, hi = g.mean(), g.min(), g.max()
    nsig = (df[df.p_value < 0.05].groupby("variant").size()
            .reindex(mean_r.index).fillna(0).astype(int))
    order = mean_r.sort_values().index.tolist()

    fig = plt.figure(figsize=(7.4, 4.0))
    ax = fig.add_axes([0.375, 0.145, 0.60, 0.80])
    ypos = np.arange(len(order))
    for y, v in zip(ypos, order):
        col = CAND if nsig[v] else MUTED
        ax.plot([lo[v], hi[v]], [y, y], color=col, lw=1.1, alpha=0.55,
                solid_capstyle="round")
        ax.plot([mean_r[v]], [y], "o", ms=6,
                color=col if nsig[v] else "white",
                markeredgecolor=col, markeredgewidth=1.1, zorder=4)
    ax.axvline(1.0, color=INK, lw=0.9)
    ax.set_xscale("log")
    ax.set_yticks(ypos)
    ax.set_yticklabels([SENS_LABEL[v] for v in order], fontsize=8)
    ax.set_xlabel("Mean final-error ratio, perturbed / default "
                  "configuration (log scale)", fontsize=8.2)
    for y, v in zip(ypos, order):
        if nsig[v]:
            ax.text(hi[v] * 1.35, y, f"significant on {nsig[v]}/6",
                    va="center", fontsize=7.0, color=CAND)
    ax.set_xlim(0.55, 400)
    ax.set_title("filled marker: at least one significant per-problem "
                 "deviation;\nline: per-problem range over the six "
                 "problems", fontsize=8.2, loc="left")
    save(fig, os.path.join(FIGURES, "sensitivity_profile.png"))


# --------------------------------------------------------------------
def fig_standing():
    use_style()
    suites = [("CEC-2017 (29 functions)", "cec2017_mean_ranks.csv"),
              ("CEC-2022 (16 cells)", "cec2022_mean_ranks.csv"),
              ("Engineering (7 problems)", "engineering_mean_ranks.csv")]
    ranks = {name: pd.read_csv(os.path.join(RESULTS, f)).set_index(
        "algo")["mean_rank"] for name, f in suites}
    avg = pd.DataFrame(ranks).mean(axis=1).sort_values()
    order = avg.index.tolist()

    fig = plt.figure(figsize=(7.4, 4.1))
    ax = fig.add_axes([0.135, 0.215, 0.685, 0.735])
    ypos = np.arange(len(order))[::-1]
    height, alphas = 0.26, (0.95, 0.68, 0.42)
    for k, (name, _) in enumerate(suites):
        vals = [ranks[name][a] for a in order]
        ax.barh(ypos + (1 - k) * height, vals, height=height,
                color=[COLORS[a] for a in order], alpha=alphas[k],
                edgecolor="none")
    for y, a in zip(ypos, order):
        ax.text(-0.12, y, a, ha="right", va="center", fontsize=8.4,
                weight="bold" if a == "CA" else "normal")
    n_spec = sum(a in SPECIALIZED for a in order[:2])
    ax.axhspan(ypos[n_spec - 1] - 0.5, ypos[0] + 0.55, color=FILL3,
               zorder=0)
    ax.text(8.15, ypos[0] - 0.5, "competition-grade\n(L-SHADE, "
                                 "CMA-ES)", fontsize=7.4, color=MUTED,
            va="center")
    ax.text(8.15, ypos[4], "classical / moderate roster,\nCA best of "
                           "these", fontsize=7.4, color=MUTED,
            va="center")
    ax.set_yticks([])
    ax.set_xlim(0, 8.0)
    ax.set_ylim(ypos[-1] - 0.6, ypos[0] + 0.6)
    ax.set_xlabel("Mean Friedman rank (lower is better)", fontsize=8.6)
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=MUTED,
                             alpha=alphas[k], edgecolor="none",
                             label=name)
               for k, (name, _) in enumerate(suites)]
    ax.legend(handles=handles, loc="upper center", ncol=3,
              bbox_to_anchor=(0.5, -0.135), fontsize=7.6)
    for s in ("left",):
        ax.spines[s].set_visible(False)
    save(fig, os.path.join(FIGURES, "standing_ranks.png"))


def main():
    fig_cec2017_distributions()
    fig_ablation()
    fig_sensitivity()
    fig_standing()


if __name__ == "__main__":
    main()
