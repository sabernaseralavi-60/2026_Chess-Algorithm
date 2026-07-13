"""
traffic_case_study.py
=====================
Transportation engineering case study for the Chess Algorithm (CA):
coordinated fixed-time signal timing optimization along a four-
intersection urban arterial.

Problem statement
-----------------
An urban arterial contains four signalized intersections I1..I4 with
inter-intersection spacings of 450, 380 and 520 m and an arterial
progression speed of 50 km/h. Each intersection operates a two-phase
plan (arterial through phase vs. cross-street phase). The decision
vector is

    z = [C, g1, g2, g3, g4, o2, o3, o4]  in R^8

    C   : common cycle length [s],          60 <= C <= 140
    gi  : arterial green split at Ii,      0.30 <= gi <= 0.75
    oi  : offset of Ii relative to I1 [-], 0 <= oi < 1 (fraction of C)

Objective: minimize total vehicle delay (veh-h/h) over all approaches.
Approach delay is computed with Webster's two-term formula with the
degree of saturation capped at 0.98 (near-saturated regime), plus a
progression term for arterial platoons: the platoon arriving at a
downstream intersection suffers additional stop delay proportional to
the mismatch between the signal offset and the platoon travel time,
scaled by the red duration it can encounter.

The model, while simplified relative to microsimulation, is a standard
analytic formulation that produces a non-convex, multimodal objective
(offset terms are periodic), making it an appropriate testbed for
metaheuristics.

Reproduce with:  python src/traffic_case_study.py
"""

import time
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from algorithms import (chess_algorithm_v3, chess_algorithm_v2,
                        genetic_algorithm, particle_swarm, grey_wolf)

# ----------------------------------------------------------------------
# Network data
# ----------------------------------------------------------------------
N_INT = 8
SPACING = np.array([450., 380., 520., 300., 610., 420., 350.])  # m
SPEED = 50.0 / 3.6                               # m/s arterial progression
TRAVEL = SPACING / SPEED                         # s travel time per link

SAT_FLOW = 1800.0                                # veh/h/lane saturation flow
LANES_ART = 2                                    # arterial lanes per direction
LANES_CRS = 1                                    # cross-street lanes

# demand (veh/h): [arterial EB, arterial WB, cross N, cross S] per intersection
# several intersections operate near saturation, making the split/cycle
# trade-off sharp and the landscape strongly non-convex
DEMAND = np.array([
    [1240., 1050., 420., 380.],
    [1310., 1120., 640., 560.],
    [1350., 1180., 380., 330.],
    [1270., 1090., 700., 620.],
    [1400., 1230., 460., 400.],
    [1290., 1110., 590., 540.],
    [1360., 1170., 350., 300.],
    [1250., 1060., 680., 610.],
])

LOST_TIME = 8.0                                  # s lost time per cycle
T_ANALYSIS = 0.25                                # h, HCM analysis period
K_HCM, I_HCM = 0.5, 1.0                          # HCM incremental-delay params

LB = np.concatenate([[60.], np.full(N_INT, .30), np.zeros(N_INT - 1)])
UB = np.concatenate([[140.], np.full(N_INT, .75), np.ones(N_INT - 1)])
DIM = LB.size                                    # 1 + 8 + 7 = 16 variables


def approach_delay(q, s_flow, C, g_eff):
    """
    Control delay per vehicle (s/veh): Webster uniform term plus the
    HCM time-dependent incremental (overflow) term, which remains
    finite and smooth for degrees of saturation approaching and
    exceeding 1.0 (near-saturated urban operation).
    """
    lam = g_eff / C
    cap = np.maximum(s_flow * lam, 1e-6)
    x = q / cap
    xu = np.minimum(x, 1.0)
    d1 = 0.5 * C * (1 - lam) ** 2 / np.maximum(1 - lam * xu, 1e-6)
    d2 = 900.0 * T_ANALYSIS * ((x - 1)
         + np.sqrt((x - 1) ** 2 + 8 * K_HCM * I_HCM * x / (cap * T_ANALYSIS)))
    return d1 + d2


def total_delay(Z):
    """
    Vectorized objective: total network delay in veh-h/h for a population
    of decision vectors Z with shape (N, 8). Returns shape (N,).
    """
    Z = np.atleast_2d(Z)
    C = Z[:, 0]
    G = Z[:, 1:1 + N_INT]                # arterial splits g1..g8
    O = Z[:, 1 + N_INT:]                 # offsets of I2..I8 (fraction of C)

    total = np.zeros(Z.shape[0])
    t_end = TRAVEL.sum()                 # EB travel time from I1 to I8
    for i in range(N_INT):
        g_art = np.maximum(G[:, i] * C - LOST_TIME / 2, 5.0)
        g_crs = np.maximum((1 - G[:, i]) * C - LOST_TIME / 2, 5.0)

        q_eb, q_wb, q_n, q_s = DEMAND[i]
        d_eb = approach_delay(q_eb, SAT_FLOW * LANES_ART, C, g_art)
        d_wb = approach_delay(q_wb, SAT_FLOW * LANES_ART, C, g_art)
        d_n = approach_delay(q_n, SAT_FLOW * LANES_CRS, C, g_crs)
        d_s = approach_delay(q_s, SAT_FLOW * LANES_CRS, C, g_crs)

        red = (1 - G[:, i]) * C
        off_i = 0.0 if i == 0 else O[:, i - 1]

        # eastbound platoon progression (I1 -> I8): mismatch between the
        # signal offset and the platoon arrival time causes extra stops
        if i > 0:
            ideal_eb = (TRAVEL[:i].sum() / C) % 1.0
            mism = np.abs(off_i - ideal_eb)
            mism = np.minimum(mism, 1.0 - mism)
            d_eb = d_eb + 2.0 * mism * red

        # westbound platoon progression (I8 -> I1): the SAME offsets must
        # also serve the reverse platoon, creating conflicting objectives
        if i < N_INT - 1:
            t_wb = (t_end - (TRAVEL[:i].sum() if i > 0 else 0.0))
            ideal_wb = (t_wb / C) % 1.0
            mism = np.abs(off_i - ideal_wb)
            mism = np.minimum(mism, 1.0 - mism)
            d_wb = d_wb + 2.0 * mism * red

        total += (q_eb * d_eb + q_wb * d_wb + q_n * d_n + q_s * d_s)
    return total / 3600.0                                # veh-h per hour


# objective wrapper compatible with the optimizers (per-dimension bounds
# handled by rescaling to the unit hypercube)
def make_unit_objective():
    span = UB - LB

    def f(U):
        Z = LB + span * np.clip(U, 0.0, 1.0)
        return total_delay(Z)
    return f


# ----------------------------------------------------------------------
# Experiment
# ----------------------------------------------------------------------
POP, ITERS, RUNS = 30, 300, 30
SEED0 = 20260704
# "CA" is the adaptive Chess Algorithm; "CA-static" is the same operator
# set with the adaptive phase-selection machinery disabled (the ablation
# baseline used throughout this paper).
ALGORITHMS = {
    "CA": chess_algorithm_v3, "CA-static": chess_algorithm_v2,
    "GA": genetic_algorithm, "PSO": particle_swarm, "GWO": grey_wolf,
}
ALGS = ["CA", "CA-static", "GA", "PSO", "GWO"]
COLORS = {"CA": "#1a1a2e", "CA-static": "#5b6ee1", "GA": "#c0392b",
          "PSO": "#2980b9", "GWO": "#27ae60"}
STYLES = {"CA": "-", "CA-static": (0, (4, 1)), "GA": "--", "PSO": "-.",
          "GWO": (0, (3, 1, 1, 1))}

plt.rcParams.update({
    "font.family": "serif", "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 300,
})


def run_experiment():
    f = make_unit_objective()
    curves, finals, bests = {}, {}, {}
    for alg in ALGS:
        opt = ALGORITHMS[alg]
        C = np.empty((RUNS, ITERS))
        B = np.empty(RUNS)
        BX = None
        bf_global = np.inf
        t0 = time.time()
        for r in range(RUNS):
            rng = np.random.default_rng(SEED0 + r)
            bx, bf, curve = opt(f, 0.0, 1.0, DIM, POP, ITERS, rng)
            C[r], B[r] = curve, bf
            if bf < bf_global:
                bf_global, BX = bf, bx
        curves[alg], finals[alg], bests[alg] = C, B, BX
        print(f"{alg:4s} mean={B.mean():.4f} std={B.std():.4f} "
              f"best={B.min():.4f}  ({time.time()-t0:.1f}s)", flush=True)
    return curves, finals, bests


def make_outputs(curves, finals, bests):
    # ---- statistics table ----
    rows = []
    for alg in ALGS:
        B = finals[alg]
        rows.append({"Algorithm": alg, "Mean delay (veh-h/h)": B.mean(),
                     "Std": B.std(), "Best": B.min(), "Worst": B.max()})
    df = pd.DataFrame(rows)
    df.to_csv("../results/traffic_stats.csv", index=False)

    with open("../results/table_traffic.md", "w", encoding="utf8") as fmd:
        fmd.write("| Algorithm | Mean delay (veh·h/h) | Std | Best | Worst |\n")
        fmd.write("|---|---:|---:|---:|---:|\n")
        best_mean = df["Mean delay (veh-h/h)"].min()
        for _, r in df.iterrows():
            m = f"{r['Mean delay (veh-h/h)']:.3f}"
            if np.isclose(r["Mean delay (veh-h/h)"], best_mean):
                m = f"**{m}**"
            fmd.write(f"| {r['Algorithm']} | {m} | {r['Std']:.3f} | "
                      f"{r['Best']:.3f} | {r['Worst']:.3f} |\n")

    # Wilcoxon: CA vs each
    with open("../results/table_traffic_wilcoxon.md", "w", encoding="utf8") as fmd:
        fmd.write("| Comparison | p-value | Result (α = 0.05) |\n|---|---:|---|\n")
        for alg in ALGS[1:]:
            _, p = stats.ranksums(finals["CA"], finals[alg])
            verdict = ("CA better" if (p < .05 and finals["CA"].mean()
                                       < finals[alg].mean())
                       else "CA worse" if p < .05 else "not significant")
            fmd.write(f"| CA vs {alg} | {p:.3e} | {verdict} |\n")

    # ---- convergence figure ----
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    for alg in ALGS:
        ax.plot(curves[alg].mean(axis=0), color=COLORS[alg],
                linestyle=STYLES[alg], lw=1.5, label=alg)
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Total network delay (veh·h/h)")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig("../figures/traffic_convergence.png", bbox_inches="tight")
    plt.close(fig)

    # ---- box plot ----
    fig, ax = plt.subplots(figsize=(5.4, 3.6))
    bp = ax.boxplot([finals[a] for a in ALGS], tick_labels=ALGS,
                    patch_artist=True, medianprops=dict(color="black"))
    for patch, alg in zip(bp["boxes"], ALGS):
        patch.set_facecolor(COLORS[alg])
        patch.set_alpha(0.55)
    ax.set_ylabel("Final delay (veh·h/h)")
    fig.tight_layout()
    fig.savefig("../figures/traffic_boxplot.png", bbox_inches="tight")
    plt.close(fig)

    # ---- network schematic ----
    fig, ax = plt.subplots(figsize=(10.5, 2.9))
    ax.axis("off")
    xs = np.concatenate([[0], np.cumsum(SPACING)])
    xs_n = xs / xs.max()
    ax.plot([-.05, 1.05], [0.5, 0.5], color="#666", lw=6, zorder=1,
            solid_capstyle="round")
    for i, x in enumerate(xs_n):
        ax.plot([x, x], [0.15, 0.85], color="#999", lw=3, zorder=1)
        ax.add_patch(plt.Circle((x, 0.5), 0.028, fc="#1a1a2e", zorder=3))
        ax.text(x, 0.95, f"I{i+1}", ha="center", fontsize=11, weight="bold")
        # stagger the cross-street demand labels on two rows so that
        # closely spaced intersections do not overlap
        y_lab = 0.02 if i % 2 == 0 else -0.10
        ax.text(x, y_lab, f"cross: {DEMAND[i,2]:.0f}/{DEMAND[i,3]:.0f} veh/h",
                ha="center", fontsize=6.8, color="#555")
    for i, s in enumerate(SPACING):
        xm = (xs_n[i] + xs_n[i + 1]) / 2
        ax.annotate(f"{s:.0f} m", (xm, 0.60), ha="center", fontsize=8)
    # direction labels centred in the widest gap (I5-I6) to avoid the
    # vertical cross-street lines
    x_gap = (xs_n[4] + xs_n[5]) / 2
    ax.annotate("arterial EB  →", (x_gap, 0.76), ha="center", fontsize=9)
    ax.annotate("←  arterial WB", (x_gap, 0.26), ha="center", fontsize=9)
    ax.set_xlim(-0.08, 1.08)
    ax.set_ylim(-0.16, 1.05)
    fig.savefig("../figures/traffic_network.png", bbox_inches="tight")
    plt.close(fig)

    # ---- best CA timing plan ----
    span = UB - LB
    z = LB + span * np.clip(bests["CA"], 0, 1)
    C = z[0]
    with open("../results/best_ca_plan.md", "w", encoding="utf8") as fmd:
        fmd.write("| Parameter | Value |\n|---|---:|\n")
        fmd.write(f"| Cycle length C | {C:.1f} s |\n")
        for i in range(N_INT):
            fmd.write(f"| Arterial green split g{i+1} | {z[1+i]:.3f} "
                      f"({z[1+i]*C:.1f} s) |\n")
        for i in range(N_INT - 1):
            fmd.write(f"| Offset o{i+2} | {z[1+N_INT+i]*C:.1f} s |\n")
        fmd.write(f"| **Total delay** | **{total_delay(z[None,:])[0]:.3f} "
                  f"veh·h/h** |\n")

    fig, ax = plt.subplots(figsize=(6.6, 4.6))
    labels = [f"I{i+1}" for i in range(N_INT)]
    g_art = z[1:1 + N_INT] * C
    g_crs = C - g_art
    ax.barh(labels, g_art, color="#27ae60", alpha=.8, label="Arterial green")
    ax.barh(labels, g_crs, left=g_art, color="#c0392b", alpha=.75,
            label="Cross-street green")
    offs = np.concatenate([[0.0], z[1 + N_INT:] * C])
    for i, o in enumerate(offs):
        ax.text(C + 1.5, i, f"offset {o:.0f} s", va="center", fontsize=8)
    ax.set_xlabel("Time within cycle (s)")
    ax.set_xlim(0, C * 1.25)
    # legend below the axes so it cannot collide with the offset labels
    ax.legend(frameon=False, fontsize=8, ncol=2,
              loc="upper center", bbox_to_anchor=(0.5, -0.14))
    fig.tight_layout()
    fig.savefig("../figures/traffic_best_plan.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs("../results", exist_ok=True)
    os.makedirs("../figures", exist_ok=True)
    CURVES, FINALS, BESTS = run_experiment()
    make_outputs(CURVES, FINALS, BESTS)
    np.savez_compressed("../results/raw_traffic.npz", **FINALS)
    print("done")
