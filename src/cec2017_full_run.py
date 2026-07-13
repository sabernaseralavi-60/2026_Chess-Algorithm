"""
cec2017_full_run.py
===================
Phase 2: full CEC-2017 comparison for the adaptive Chess Algorithm.

Roster : CA-v3 (adaptive), CA-v2 (static ablation), GWO, PSO, GA (ours),
         WOA (third-party, mealpy defaults).
Suite  : all opfunu CEC-2017 classes except F5 (near-flat Schaffer F7 in
         opfunu) and F9 (buggy Schwefel: optimizers descend below the
         claimed f_global). Every remaining function is pre-flight
         checked with f(x_global) == f_global; failures are excluded
         and logged.
Setup  : D=30, pop=30, iters=500, 30 runs, seed = SEED0 + r shared by
         all algorithms at run index r. All algorithms search the unit
         hypercube; real bounds are folded into the decoder.

Outputs (checkpointed after every function):
    results/cec2017_stats.csv      best/mean/std/median/worst per cell
    results/cec2017_wilcoxon.csv   CA-v3 vs every competitor
    results/raw_cec2017.npz        all final errors + median/quartile curves

Usage:
    python src/cec2017_full_run.py            # full run
    python src/cec2017_full_run.py --smoke    # 2 funcs, 3 runs, 50 iters
    python src/cec2017_full_run.py --part i/n # functions i::n only
                                              # (parallel partitions;
                                              #  outputs suffixed _parti)
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

from opfunu.cec_based import cec2017

warnings.filterwarnings("ignore")

SMOKE = "--smoke" in sys.argv
PART_I, PART_N = 0, 1
if "--part" in sys.argv:
    _spec = sys.argv[sys.argv.index("--part") + 1]
    PART_I, PART_N = (int(x) for x in _spec.split("/"))

SEED0 = 20260713
DIM = 30
POP = 30
ITERS = 50 if SMOKE else 500
RUNS = 3 if SMOKE else 30
EXCLUDE = {"F52017", "F92017"}          # flawed opfunu implementations

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
os.makedirs(RESULTS, exist_ok=True)
_SUF = f"_part{PART_I}" if PART_N > 1 else ""
STATS_CSV = os.path.join(RESULTS, f"cec2017_stats{_SUF}.csv")
WILC_CSV = os.path.join(RESULTS, f"cec2017_wilcoxon{_SUF}.csv")
RAW_NPZ = os.path.join(RESULTS, f"raw_cec2017{_SUF}.npz")

ALGOS = ["CA-v3", "CA-v2", "GWO", "PSO", "GA", "WOA"]


def make_problem(cls):
    prob = cls(ndim=DIM)
    lo, sp = prob.lb.copy(), prob.ub - prob.lb

    def f_vec(U):
        Z = lo + sp * np.clip(np.atleast_2d(U), 0.0, 1.0)
        return np.array([prob.evaluate(z) for z in Z])

    def f_scalar(u):
        z = lo + sp * np.clip(np.asarray(u), 0.0, 1.0)
        return float(prob.evaluate(z))

    return prob, f_vec, f_scalar


def run_our(optimizer, f_vec, seed):
    rng = np.random.default_rng(seed)
    _, bf, curve = optimizer(f_vec, 0.0, 1.0, DIM, POP, ITERS, rng)
    return bf, np.asarray(curve, dtype=float)


def run_woa(f_scalar, seed):
    from mealpy import WOA, FloatVar
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
    "CA-v3": lambda fv, fs, s: run_our(alg.chess_algorithm_v3, fv, s),
    "CA-v2": lambda fv, fs, s: run_our(alg.chess_algorithm_v2, fv, s),
    "GWO":   lambda fv, fs, s: run_our(alg.grey_wolf, fv, s),
    "PSO":   lambda fv, fs, s: run_our(alg.particle_swarm, fv, s),
    "GA":    lambda fv, fs, s: run_our(alg.genetic_algorithm, fv, s),
    "WOA":   lambda fv, fs, s: run_woa(fs, s),
}


def main():
    t_start = time.time()

    # ---- build the validated function list ----
    names = sorted([n for n in dir(cec2017) if n.endswith("2017")
                    and n.startswith("F")],
                   key=lambda n: int(n[1:-4]))
    funcs = []
    for n in names:
        if n in EXCLUDE:
            print(f"[preflight] {n}: EXCLUDED (known flawed)", flush=True)
            continue
        try:
            prob = getattr(cec2017, n)(ndim=DIM)
            err = abs(prob.evaluate(prob.x_global) - prob.f_global)
            if err > 1e-6 * max(1.0, abs(prob.f_global)):
                print(f"[preflight] {n}: EXCLUDED "
                      f"(f(x*) off by {err:.3g})", flush=True)
                continue
        except Exception as e:                       # noqa: BLE001
            print(f"[preflight] {n}: EXCLUDED (error: {e})", flush=True)
            continue
        funcs.append(n)
    if SMOKE:
        funcs = funcs[:1] + funcs[-1:]
    funcs = funcs[PART_I::PART_N]
    print(f"[preflight] {len(funcs)} functions in this partition: "
          f"{[f[1:-4] for f in funcs]}", flush=True)

    stats_rows, wilc_rows, raw = [], [], {}

    for fi, fname in enumerate(funcs):
        prob, f_vec, f_scalar = make_problem(getattr(cec2017, fname))
        label = f"F{fname[1:-4]}"
        finals = {}
        for aname in ALGOS:
            t0 = time.time()
            vals = np.empty(RUNS)
            curves = np.empty((RUNS, ITERS))
            for r in range(RUNS):
                bf, curve = RUNNERS[aname](f_vec, f_scalar, SEED0 + r)
                vals[r] = bf - prob.f_global
                curves[r] = curve - prob.f_global
            finals[aname] = vals
            raw[f"{label}__{aname}__finals"] = vals
            raw[f"{label}__{aname}__med"] = np.median(curves, axis=0)
            raw[f"{label}__{aname}__q25"] = np.quantile(curves, .25, axis=0)
            raw[f"{label}__{aname}__q75"] = np.quantile(curves, .75, axis=0)
            stats_rows.append(dict(
                func=label, algo=aname, best=vals.min(), mean=vals.mean(),
                std=vals.std(), median=np.median(vals), worst=vals.max()))
            print(f"[{fi+1:2d}/{len(funcs)}] {label:4s} {aname:6s} "
                  f"mean={vals.mean():12.5g} std={vals.std():10.4g} "
                  f"best={vals.min():12.5g} ({time.time()-t0:5.1f}s)",
                  flush=True)

        for aname in ALGOS:
            if aname == "CA-v3":
                continue
            _, p = ranksums(finals["CA-v3"], finals[aname])
            direction = ("better" if finals["CA-v3"].mean()
                         < finals[aname].mean() else "worse")
            sig = "yes" if p < 0.05 else "no"
            wilc_rows.append(dict(func=label, competitor=aname, p_value=p,
                                  v3_mean_direction=direction,
                                  significant=sig))

        # ---- checkpoint after every function ----
        pd.DataFrame(stats_rows).to_csv(STATS_CSV, index=False)
        pd.DataFrame(wilc_rows).to_csv(WILC_CSV, index=False)
        np.savez_compressed(RAW_NPZ, **raw)

    # ---- Friedman-style mean ranks over functions (by mean error) ----
    if PART_N == 1:
        df = pd.DataFrame(stats_rows)
        piv = df.pivot(index="func", columns="algo", values="mean")
        ranks = piv.rank(axis=1, method="average")
        ranks.mean().sort_values().to_csv(
            os.path.join(RESULTS, "cec2017_mean_ranks.csv"),
            header=["mean_rank"])
        print("\nMean ranks (lower is better):", flush=True)
        print(ranks.mean().sort_values().to_string(), flush=True)
    print(f"\nPartition {PART_I}/{PART_N} total wall time: "
          f"{(time.time()-t_start)/60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
