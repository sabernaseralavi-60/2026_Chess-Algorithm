"""
cec2017_restore_run.py
========================
Second half of step A6: all six labels excluded for opfunu defects (F5,
F9, F15, F16, F19, F21) passed the restoration audit
(src/cec2017_restoration_audit.py) against the independent tilleyd
implementation -- exact preflight match, discriminative landscape, and
no below-optimum behavior in 10 CA probe runs each.

NUMBERING (load-bearing -- see the audit script's docstring for the full
derivation): this paper's labels follow opfunu, which renumbers the
official suite consecutively after the official withdrawal of F2, so
paper label Fn corresponds to the official function F(n+1) for n >= 2,
i.e. tilleyd f(n+1), with official optimum 100*(n+1).

This script runs the full 8-algorithm roster on the restored labels,
D=30, pop=30, iters=500, 30 runs, SEED0=20260713 -- the exact protocol
of src/cec2017_full_run.py -- sourced from `cec2017` (tilleyd/cec2017-py)
since that is the implementation that passed the audit, NOT opfunu
(whose versions of these labels were shown defective in the project's
audits). Results are merged into the existing cec2017_stats/wilcoxon/raw
files exactly like src/sota_addon_run.py does for the new SOTA
algorithms: existing rows for these labels are dropped and replaced
(idempotent reruns), everything else is preserved. A one-time pre-merge
backup is written if not already present from a prior addon run.

Usage:  python src/cec2017_restore_run.py               # all six labels
        python src/cec2017_restore_run.py --funcs 16    # specific label(s)
        python src/cec2017_restore_run.py --smoke       # 3 runs, 20 iters
"""

import os
import sys
import shutil
import time
import warnings

import numpy as np
import pandas as pd
from scipy.stats import ranksums

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import algorithms as alg
from sota_algorithms import run_lshade, run_cmaes
import cec2017.functions as til

warnings.filterwarnings("ignore")

SMOKE = "--smoke" in sys.argv
POP = 30
ITERS = 20 if SMOKE else 500
RUNS = 3 if SMOKE else 30
SEED0 = 20260713
DIM = 30
BUDGET = POP * ITERS + 500
LO, HI = -100.0, 100.0

RESTORED = [5, 9, 15, 16, 19, 21]      # paper (opfunu) labels
if "--funcs" in sys.argv:
    RESTORED = [int(x) for x in
                sys.argv[sys.argv.index("--funcs") + 1].split(",")]


def official_num(label_n):
    """Paper label Fn (opfunu numbering) -> official function number."""
    return label_n + 1 if label_n >= 2 else label_n

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
BACKUP = os.path.join(RESULTS, "_backup_pre_sota")
STATS_CSV = os.path.join(RESULTS, "cec2017_stats.csv")
WILC_CSV = os.path.join(RESULTS, "cec2017_wilcoxon.csv")
RAW_NPZ = os.path.join(RESULTS, "raw_cec2017.npz")

ALGOS = ["CA", "CA-static", "GWO", "PSO", "GA", "WOA", "L-SHADE", "CMA-ES"]


def backup_once(names):
    os.makedirs(BACKUP, exist_ok=True)
    for name in names:
        src = os.path.join(RESULTS, name)
        dst = os.path.join(BACKUP, name)
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)


def make_f_vec(n):
    f = getattr(til, f"f{official_num(n)}")

    def f_vec(U):
        Z = LO + (HI - LO) * np.clip(np.atleast_2d(U), 0.0, 1.0)
        return np.asarray(f(Z), dtype=float)

    return f_vec


def run_our(optimizer, f_vec, seed):
    rng = np.random.default_rng(seed)
    _, bf, curve = optimizer(f_vec, 0.0, 1.0, DIM, POP, ITERS, rng)
    return bf, np.asarray(curve, dtype=float)


def run_woa(f_vec, seed):
    from mealpy import WOA, FloatVar

    def f_scalar(u):
        return float(f_vec(np.atleast_2d(u))[0])

    problem = {"obj_func": f_scalar,
               "bounds": FloatVar(lb=(0.0,) * DIM, ub=(1.0,) * DIM),
               "minmax": "min", "log_to": None}
    model = WOA.OriginalWOA(epoch=ITERS, pop_size=POP)
    gb = model.solve(problem, seed=seed)
    bf = float(gb.target.fitness)
    hist = np.asarray(model.history.list_global_best_fit, dtype=float)
    curve = np.interp(np.linspace(0, 1, ITERS),
                      np.linspace(0, 1, hist.size), hist)
    return bf, curve


RUNNERS = {
    "CA":        lambda fv, s: run_our(alg.chess_algorithm_v3, fv, s),
    "CA-static": lambda fv, s: run_our(alg.chess_algorithm_v2, fv, s),
    "GWO":       lambda fv, s: run_our(alg.grey_wolf, fv, s),
    "PSO":       lambda fv, s: run_our(alg.particle_swarm, fv, s),
    "GA":        lambda fv, s: run_our(alg.genetic_algorithm, fv, s),
    "WOA":       lambda fv, s: run_woa(fv, s),
    "L-SHADE":   lambda fv, s: run_lshade(fv, 0.0, 1.0, DIM, POP, ITERS, s, max_evals=BUDGET),
    "CMA-ES":    lambda fv, s: run_cmaes(fv, 0.0, 1.0, DIM, POP, ITERS, s),
}


def main():
    backup_once(["cec2017_stats.csv", "cec2017_wilcoxon.csv", "raw_cec2017.npz"])

    stats = pd.read_csv(STATS_CSV)
    wilc = pd.read_csv(WILC_CSV)
    raw = dict(np.load(RAW_NPZ))

    labels = [f"F{n}" for n in RESTORED]
    stats = stats[~stats["func"].isin(labels)]
    wilc = wilc[~wilc["func"].isin(labels)]
    stats_rows = stats.to_dict("records")
    wilc_rows = wilc.to_dict("records")

    t_start = time.time()
    for n in RESTORED:
        label = f"F{n}"
        f_global = 100.0 * official_num(n)
        f_vec = make_f_vec(n)
        finals = {}
        for aname in ALGOS:
            t0 = time.time()
            vals = np.empty(RUNS)
            curves = np.empty((RUNS, ITERS))
            for r in range(RUNS):
                bf, curve = RUNNERS[aname](f_vec, SEED0 + r)
                vals[r] = bf - f_global
                curves[r] = curve - f_global
            finals[aname] = vals
            raw[f"{label}__{aname}__finals"] = vals
            raw[f"{label}__{aname}__med"] = np.median(curves, axis=0)
            raw[f"{label}__{aname}__q25"] = np.quantile(curves, .25, axis=0)
            raw[f"{label}__{aname}__q75"] = np.quantile(curves, .75, axis=0)
            stats_rows.append(dict(
                func=label, algo=aname, best=vals.min(), mean=vals.mean(),
                std=vals.std(), median=np.median(vals), worst=vals.max()))
            print(f"[restore] {label:4s} {aname:9s} "
                  f"mean={vals.mean():12.5g} std={vals.std():10.4g} "
                  f"best={vals.min():12.5g} ({time.time()-t0:5.1f}s)",
                  flush=True)

        for aname in ALGOS:
            if aname == "CA":
                continue
            _, p = ranksums(finals["CA"], finals[aname])
            direction = "better" if finals["CA"].mean() < finals[aname].mean() else "worse"
            wilc_rows.append(dict(func=label, competitor=aname, p_value=p,
                                  v3_mean_direction=direction,
                                  significant="yes" if p < 0.05 else "no"))

        pd.DataFrame(stats_rows).to_csv(STATS_CSV, index=False)
        pd.DataFrame(wilc_rows).to_csv(WILC_CSV, index=False)
        np.savez_compressed(RAW_NPZ, **raw)

    n_funcs = pd.read_csv(STATS_CSV)["func"].nunique()
    print(f"\nRestored {labels} into cec2017_stats.csv "
          f"({n_funcs} validated functions total now).")
    print(f"Total restore wall time: {(time.time()-t_start)/60:.1f} min",
          flush=True)


if __name__ == "__main__":
    main()
