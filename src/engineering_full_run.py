"""
engineering_full_run.py
=======================
Phase 3: seven classic constrained engineering design problems.

Roster, protocol, and outputs mirror src/cec2017_full_run.py:
CA-v3, CA-v2, GWO, PSO, GA (ours) + WOA (mealpy defaults);
pop 30, 500 iterations, 30 runs, seed SEED0 + r; unit-hypercube search
with bounds folded into the decoder; static penalty in the objectives.

Outputs:
    results/engineering_stats.csv
    results/engineering_wilcoxon.csv
    results/raw_engineering.npz

Usage:  python src/engineering_full_run.py
"""

import os
import sys
import time
import warnings

import numpy as np
import pandas as pd
from scipy.stats import ranksums

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import algorithms as alg
from engineering_problems import ENGINEERING

warnings.filterwarnings("ignore")

SEED0 = 20260713
POP = 30
ITERS = 500
RUNS = 30

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
os.makedirs(RESULTS, exist_ok=True)

ALGOS = ["CA-v3", "CA-v2", "GWO", "PSO", "GA", "WOA"]


def make_unit(fun, lb, ub):
    span = ub - lb

    def f_vec(U):
        Z = lb + span * np.clip(np.atleast_2d(U), 0.0, 1.0)
        return fun(Z)

    def f_scalar(u):
        z = lb + span * np.clip(np.asarray(u), 0.0, 1.0)
        return float(fun(z[None, :])[0])

    return f_vec, f_scalar


def run_our(optimizer, f_vec, dim, seed):
    rng = np.random.default_rng(seed)
    bx, bf, curve = optimizer(f_vec, 0.0, 1.0, dim, POP, ITERS, rng)
    return bx, bf, np.asarray(curve, dtype=float)


def run_woa(f_scalar, dim, seed):
    from mealpy import WOA, FloatVar
    problem = {"obj_func": f_scalar,
               "bounds": FloatVar(lb=(0.0,) * dim, ub=(1.0,) * dim),
               "minmax": "min", "log_to": None}
    model = WOA.OriginalWOA(epoch=ITERS, pop_size=POP)
    gb = model.solve(problem, seed=seed)
    bx = np.asarray(gb.solution, dtype=float)
    bf = float(gb.target.fitness)
    hist = np.asarray(model.history.list_global_best_fit, dtype=float)
    curve = np.interp(np.linspace(0, 1, ITERS),
                      np.linspace(0, 1, hist.size), hist)
    return bx, bf, curve


RUNNERS = {
    "CA-v3": lambda fv, fs, d, s: run_our(alg.chess_algorithm_v3, fv, d, s),
    "CA-v2": lambda fv, fs, d, s: run_our(alg.chess_algorithm_v2, fv, d, s),
    "GWO":   lambda fv, fs, d, s: run_our(alg.grey_wolf, fv, d, s),
    "PSO":   lambda fv, fs, d, s: run_our(alg.particle_swarm, fv, d, s),
    "GA":    lambda fv, fs, d, s: run_our(alg.genetic_algorithm, fv, d, s),
    "WOA":   lambda fv, fs, d, s: run_woa(fs, d, s),
}


def main():
    t_start = time.time()
    stats_rows, wilc_rows, raw = [], [], {}

    for pname, (fun, lb, ub, dim, f_ref) in ENGINEERING.items():
        f_vec, f_scalar = make_unit(fun, lb, ub)
        finals = {}
        best_x = {}
        for aname in ALGOS:
            t0 = time.time()
            vals = np.empty(RUNS)
            curves = np.empty((RUNS, ITERS))
            bx_best, bf_best = None, np.inf
            for r in range(RUNS):
                bx, bf, curve = RUNNERS[aname](f_vec, f_scalar, dim,
                                               SEED0 + r)
                vals[r] = bf
                curves[r] = curve
                if bf < bf_best:
                    bf_best, bx_best = bf, np.asarray(bx, dtype=float)
            finals[aname] = vals
            best_x[aname] = bx_best
            raw[f"{pname}__{aname}__finals"] = vals
            raw[f"{pname}__{aname}__med"] = np.median(curves, axis=0)
            raw[f"{pname}__{aname}__q25"] = np.quantile(curves, .25, axis=0)
            raw[f"{pname}__{aname}__q75"] = np.quantile(curves, .75, axis=0)
            raw[f"{pname}__{aname}__bestx"] = bx_best
            stats_rows.append(dict(
                problem=pname, algo=aname, best=vals.min(),
                mean=vals.mean(), std=vals.std(),
                median=np.median(vals), worst=vals.max(), f_ref=f_ref))
            print(f"{pname:15s} {aname:6s} mean={vals.mean():14.8g} "
                  f"std={vals.std():10.4g} best={vals.min():14.8g} "
                  f"({time.time()-t0:4.1f}s)", flush=True)

        for aname in ALGOS:
            if aname == "CA-v3":
                continue
            _, p = ranksums(finals["CA-v3"], finals[aname])
            direction = ("better" if finals["CA-v3"].mean()
                         < finals[aname].mean() else "worse")
            wilc_rows.append(dict(problem=pname, competitor=aname,
                                  p_value=p, v3_mean_direction=direction,
                                  significant="yes" if p < .05 else "no"))

        pd.DataFrame(stats_rows).to_csv(
            os.path.join(RESULTS, "engineering_stats.csv"), index=False)
        pd.DataFrame(wilc_rows).to_csv(
            os.path.join(RESULTS, "engineering_wilcoxon.csv"), index=False)
        np.savez_compressed(os.path.join(RESULTS, "raw_engineering.npz"),
                            **raw)

    df = pd.DataFrame(stats_rows)
    piv = df.pivot(index="problem", columns="algo", values="mean")
    ranks = piv.rank(axis=1, method="average")
    ranks.mean().sort_values().to_csv(
        os.path.join(RESULTS, "engineering_mean_ranks.csv"),
        header=["mean_rank"])
    print("\nMean ranks (lower is better):", flush=True)
    print(ranks.mean().sort_values().to_string(), flush=True)
    print(f"\nTotal wall time: {(time.time()-t_start)/60:.1f} min",
          flush=True)


if __name__ == "__main__":
    main()
