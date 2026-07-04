"""
mealpy_comparison.py
====================
Extended, independent comparison of the Chess Algorithm (CA) against six
widely used metaheuristics taken from the third-party `mealpy` library
(https://github.com/thieu1995/mealpy):

    WOA - Whale Optimization Algorithm      (Mirjalili & Lewis, 2016)
    SCA - Sine Cosine Algorithm             (Mirjalili, 2016)
    ALO - Ant Lion Optimizer                (Mirjalili, 2015)
    MFO - Moth-Flame Optimization           (Mirjalili, 2015)
    HHO - Harris Hawks Optimization         (Heidari et al., 2019)
    DE  - Differential Evolution            (Storn & Price, 1997)

Using an independent library removes any suspicion that the baselines
were implemented weakly in-house: every competitor runs exactly as its
maintainers shipped it, with default hyperparameters.

Two transportation engineering problems are solved:

P1  Arterial signal coordination (16 variables)
    The eight-intersection Webster/HCM signal timing problem defined in
    traffic_case_study.py.

P2  Continuous berth allocation (30 variables)
    Example 1.9 of Teodorovic & Janic (2020), "Quantitative Methods in
    Transportation", Ch. 1: fifteen ships with known lengths, arrival
    and service times must be moored along a 1,000 m quay within a
    1,920 min horizon so that total time in port is minimized. The
    mixed-integer optimum is known: 4,860 min (every ship moors on
    arrival, zero waiting), which lets us report exact optimality gaps.
    Decision variables per ship: mooring time u_i in [a_i, T - p_i] and
    berth position v_i in [0, S - s_i]; the box bounds therefore encode
    the arrival-time and quay-length constraints, while ship-pair
    rectangle overlaps in the time-space diagram are penalized.

All algorithms search the SAME unit hypercube (bounds are folded into
the decoding), with population 30, 300 iterations, and 30 independent
runs per (algorithm, problem) pair; run r of every algorithm uses seed
SEED0 + r.

Reproduce with:  python src/mealpy_comparison.py
"""

import time
import warnings

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from algorithms import chess_algorithm
from traffic_case_study import total_delay, LB as SIG_LB, UB as SIG_UB

warnings.filterwarnings("ignore")

# ----------------------------------------------------------------------
# P2: continuous berth allocation (book Example 1.9)
# ----------------------------------------------------------------------
QUAY = 1000.0          # m
HORIZON = 1920.0       # min
# ship data: length (m), arrival (min), service time (min)
SHIPS = np.array([
    [150.,   15., 300.],
    [200.,   60., 240.],
    [250.,   90., 360.],
    [100.,  210., 180.],
    [300.,  255., 360.],
    [150.,  360., 480.],
    [200.,  410., 180.],
    [250.,  480., 540.],
    [130.,  590., 300.],
    [180.,  750., 240.],
    [200., 1000., 420.],
    [150., 1215., 360.],
    [180., 1270., 120.],
    [250., 1370., 540.],
    [200., 1410., 240.],
])
S_LEN, S_ARR, S_SRV = SHIPS[:, 0], SHIPS[:, 1], SHIPS[:, 2]
N_SHIPS = SHIPS.shape[0]
BERTH_OPT = float(S_SRV.sum())                 # 4860 min, known MIP optimum
LAMBDA = 1.0                                   # overlap penalty per min*m

BERTH_LB = np.concatenate([S_ARR, np.zeros(N_SHIPS)])
BERTH_UB = np.concatenate([HORIZON - S_SRV, QUAY - S_LEN])
_II, _JJ = np.triu_indices(N_SHIPS, 1)


def berth_objective(Z):
    """Total time in port (min) + LAMBDA * total pairwise overlap area.

    Z has shape (P, 30): mooring times u then berth positions v.
    Feasible plans have zero overlap; the global optimum is 4,860.
    """
    Z = np.atleast_2d(Z)
    u, v = Z[:, :N_SHIPS], Z[:, N_SHIPS:]
    tip = (u - S_ARR + S_SRV).sum(axis=1)      # total time in port

    u1, u2 = u[:, _II], u[:, _JJ]
    v1, v2 = v[:, _II], v[:, _JJ]
    ot = np.clip(np.minimum(u1 + S_SRV[_II], u2 + S_SRV[_JJ])
                 - np.maximum(u1, u2), 0.0, None)
    ov = np.clip(np.minimum(v1 + S_LEN[_II], v2 + S_LEN[_JJ])
                 - np.maximum(v1, v2), 0.0, None)
    penalty = (ot * ov).sum(axis=1)
    return tip + LAMBDA * penalty


def berth_overlap(z):
    """Total overlap area (min*m) of a single decoded plan."""
    z = np.atleast_2d(z)
    u, v = z[:, :N_SHIPS], z[:, N_SHIPS:]
    u1, u2 = u[:, _II], u[:, _JJ]
    v1, v2 = v[:, _II], v[:, _JJ]
    ot = np.clip(np.minimum(u1 + S_SRV[_II], u2 + S_SRV[_JJ])
                 - np.maximum(u1, u2), 0.0, None)
    ov = np.clip(np.minimum(v1 + S_LEN[_II], v2 + S_LEN[_JJ])
                 - np.maximum(v1, v2), 0.0, None)
    return float((ot * ov).sum())


# ----------------------------------------------------------------------
# unit-hypercube wrappers (identical search space for every algorithm)
# ----------------------------------------------------------------------
def make_unit(fun, lb, ub):
    span = ub - lb

    def f_vec(U):                              # for CA (vectorized)
        Z = lb + span * np.clip(np.atleast_2d(U), 0.0, 1.0)
        return fun(Z)

    def f_scalar(u):                           # for mealpy (per solution)
        z = lb + span * np.clip(np.asarray(u), 0.0, 1.0)
        return float(fun(z[None, :])[0])

    return f_vec, f_scalar


PROBLEMS = {
    "signal": dict(fun=total_delay, lb=SIG_LB, ub=SIG_UB, dim=SIG_LB.size,
                   label="Arterial signal timing (P1)", fmt="{:.3f}"),
    "berth": dict(fun=berth_objective, lb=BERTH_LB, ub=BERTH_UB,
                  dim=BERTH_LB.size,
                  label="Continuous berth allocation (P2)", fmt="{:.1f}"),
}

# ----------------------------------------------------------------------
# experiment
# ----------------------------------------------------------------------
POP, ITERS, RUNS = 30, 300, 30
SEED0 = 20260705

MEALPY_ALGS = ["WOA", "SCA", "ALO", "MFO", "HHO", "DE"]
ALL_ALGS = ["CA"] + MEALPY_ALGS

COLORS = {"CA": "#1a1a2e", "WOA": "#2980b9", "SCA": "#c0392b",
          "ALO": "#8e44ad", "MFO": "#d35400", "HHO": "#16a085",
          "DE": "#7f8c8d"}
STYLES = {"CA": "-", "WOA": "--", "SCA": "-.", "ALO": ":",
          "MFO": (0, (3, 1, 1, 1)), "HHO": (0, (5, 2)),
          "DE": (0, (1, 1))}

plt.rcParams.update({
    "font.family": "serif", "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 300,
})


def make_mealpy_model(name):
    """Fresh mealpy optimizer instance with default hyperparameters."""
    from mealpy import WOA, SCA, ALO, MFO, HHO, DE
    lib = {"WOA": WOA.OriginalWOA, "SCA": SCA.OriginalSCA,
           "ALO": ALO.OriginalALO, "MFO": MFO.OriginalMFO,
           "HHO": HHO.OriginalHHO, "DE": DE.OriginalDE}
    return lib[name](epoch=ITERS, pop_size=POP)


def run_problem(pname):
    from mealpy import FloatVar
    spec = PROBLEMS[pname]
    f_vec, f_scalar = make_unit(spec["fun"], spec["lb"], spec["ub"])
    dim = spec["dim"]

    curves = {a: np.empty((RUNS, ITERS)) for a in ALL_ALGS}
    finals = {a: np.empty(RUNS) for a in ALL_ALGS}
    best_x = {a: None for a in ALL_ALGS}
    best_f = {a: np.inf for a in ALL_ALGS}

    for alg in ALL_ALGS:
        t0 = time.time()
        for r in range(RUNS):
            seed = SEED0 + r
            if alg == "CA":
                rng = np.random.default_rng(seed)
                bx, bf, curve = chess_algorithm(
                    f_vec, 0.0, 1.0, dim, POP, ITERS, rng)
            else:
                problem = {"obj_func": f_scalar,
                           "bounds": FloatVar(lb=(0.0,) * dim,
                                              ub=(1.0,) * dim),
                           "minmax": "min", "log_to": None}
                model = make_mealpy_model(alg)
                gb = model.solve(problem, seed=seed)
                bx = np.asarray(gb.solution, dtype=float)
                bf = float(gb.target.fitness)
                hist = np.asarray(model.history.list_global_best_fit,
                                  dtype=float)
                curve = np.interp(np.linspace(0, 1, ITERS),
                                  np.linspace(0, 1, hist.size), hist)
            curves[alg][r], finals[alg][r] = curve, bf
            if bf < best_f[alg]:
                best_f[alg], best_x[alg] = bf, bx.copy()
        print(f"{pname:7s} {alg:4s} mean={finals[alg].mean():.4f} "
              f"std={finals[alg].std():.4f} best={finals[alg].min():.4f} "
              f"({time.time()-t0:.1f}s)", flush=True)
    return curves, finals, best_x


def write_table(pname, finals, best_x):
    spec = PROBLEMS[pname]
    fmt = spec["fmt"]
    lines = ["| Algorithm | Mean | Std | Best | Worst | p-value (vs CA) "
             "| Result (α = 0.05) |",
             "|---|---:|---:|---:|---:|---:|---|"]
    best_mean = min(finals[a].mean() for a in ALL_ALGS)
    ca = finals["CA"]
    for a in ALL_ALGS:
        B = finals[a]
        m = fmt.format(B.mean())
        if np.isclose(B.mean(), best_mean, rtol=1e-12):
            m = f"**{m}**"
        if a == "CA":
            pcol, verdict = "—", "—"
        else:
            _, p = stats.ranksums(ca, B)
            pcol = f"{p:.3e}"
            verdict = ("CA better" if (p < .05 and ca.mean() < B.mean())
                       else "CA worse" if p < .05 else "not significant")
        lines.append(f"| {a} | {m} | {fmt.format(B.std())} | "
                     f"{fmt.format(B.min())} | {fmt.format(B.max())} | "
                     f"{pcol} | {verdict} |")
    with open(f"../results/table_mealpy_{pname}.md", "w",
              encoding="utf8") as f:
        f.write("\n".join(lines) + "\n")

    if pname == "berth":
        # optimality gaps and feasibility of best plans
        lines = ["| Algorithm | Best objective (min) | Gap to optimum "
                 "| Overlap of best plan (min·m) |",
                 "|---|---:|---:|---:|"]
        span = BERTH_UB - BERTH_LB
        for a in ALL_ALGS:
            z = BERTH_LB + span * np.clip(best_x[a], 0, 1)
            ov = berth_overlap(z)
            bf = finals[a].min()
            gap = 100.0 * (bf - BERTH_OPT) / BERTH_OPT
            lines.append(f"| {a} | {bf:.1f} | {gap:.2f}% | {ov:.1f} |")
        with open("../results/table_berth_gap.md", "w", encoding="utf8") as f:
            f.write("\n".join(lines) + "\n")


def berth_plan_figure(best_x_ca):
    """Time-space diagram of CA's best berth plan (book-style Fig. 1.43)."""
    span = BERTH_UB - BERTH_LB
    z = BERTH_LB + span * np.clip(best_x_ca, 0, 1)
    u, v = z[:N_SHIPS], z[N_SHIPS:]

    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    cmap = plt.get_cmap("tab20")
    for i in range(N_SHIPS):
        ax.add_patch(plt.Rectangle((u[i], v[i]), S_SRV[i], S_LEN[i],
                                   fc=cmap(i % 20), ec="#1a1a2e",
                                   lw=0.8, alpha=0.75))
        ax.text(u[i] + S_SRV[i] / 2, v[i] + S_LEN[i] / 2,
                f"{i+1}", ha="center", va="center", fontsize=8,
                weight="bold", color="#1a1a2e")
        ax.plot([S_ARR[i], S_ARR[i]], [v[i], v[i] + S_LEN[i]],
                color="#1a1a2e", lw=0.8, linestyle=":", alpha=0.6)
    ax.set_xlim(0, HORIZON)
    ax.set_ylim(0, QUAY)
    ax.set_xlabel("Time (min)")
    ax.set_ylabel("Quay position (m)")
    fig.tight_layout()
    fig.savefig("../figures/berth_best_plan.png", bbox_inches="tight")
    plt.close(fig)


def convergence_figure(all_curves):
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.0))
    for ax, pname in zip(axes, ["signal", "berth"]):
        curves = all_curves[pname]
        for a in ALL_ALGS:
            m = np.median(curves[a], axis=0)
            ax.plot(m, color=COLORS[a], linestyle=STYLES[a],
                    lw=1.4, label=a)
        ax.set_title(PROBLEMS[pname]["label"], fontsize=10)
        ax.set_xlabel("Iteration", fontsize=9)
        if pname == "signal":
            ax.set_ylabel("Total delay (veh·h/h)", fontsize=9)
            ax.set_ylim(165, 230)
        else:
            ax.set_yscale("log")
            ax.set_ylabel("Objective (min, log)", fontsize=9)
            ax.axhline(BERTH_OPT, color="#999", lw=0.8, linestyle="--")
            ax.annotate("known optimum 4,860", (ITERS * 0.55, BERTH_OPT),
                        textcoords="offset points", xytext=(0, -12),
                        fontsize=7.5, color="#555")
        ax.tick_params(labelsize=8)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=7, frameon=False)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig("../figures/mealpy_convergence.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs("../results", exist_ok=True)
    os.makedirs("../figures", exist_ok=True)

    t0 = time.time()
    all_curves, all_finals, all_best = {}, {}, {}
    for pname in PROBLEMS:
        c, f, b = run_problem(pname)
        all_curves[pname], all_finals[pname], all_best[pname] = c, f, b
        write_table(pname, f, b)

    berth_plan_figure(all_best["berth"]["CA"])
    convergence_figure(all_curves)

    np.savez_compressed(
        "../results/raw_mealpy.npz",
        **{f"{p}__{a}": all_finals[p][a] for p in PROBLEMS for a in ALL_ALGS})
    print(f"\nTotal wall time: {time.time()-t0:.1f}s")
