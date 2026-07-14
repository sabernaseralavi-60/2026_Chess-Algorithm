"""
cec2022_full_run.py
====================
Step A1 of PLAN_cec2022_and_reply.md: full CEC-2022 comparison, extending
the roster from six to eight algorithms.

Roster : CA (adaptive), CA-static (ablation), GWO, PSO, GA (ours),
         WOA (third-party, mealpy defaults), L-SHADE (niapy, see
         src/sota_algorithms.py -- pyade is unavailable, see CP0 note in
         PLAN_cec2022_and_reply.md), CMA-ES (pycma).
Suite  : all opfunu CEC-2022 classes F1-F12, ndim in {10, 20}. Every
         function is pre-flight checked with f(x_global) == f_global (all
         12 pass at both dims, unlike CEC-2017; see A0 facts in the plan).
Setup  : pop=30, iters=500, 30 runs, seed = SEED0 + r shared by all
         algorithms at run index r. All algorithms search the unit
         hypercube; real bounds are folded into the decoder. Official
         CEC-2022 budgets (200k/1M evals) are not used, for comparability
         with the rest of this project's sections.

Outputs (checkpointed after every function):
    results/cec2022_stats_part*.csv      best/mean/std/median/worst per cell
    results/cec2022_wilcoxon_part*.csv   CA vs every competitor
    results/raw_cec2022_part*.npz        finals + median/quartile curves

Function label convention: "F1-D10" (func number + dimensionality), so
CEC-2022 rows never collide with CEC-2017's "F1"-style labels when tables
are merged or compared.

Usage:
    python src/cec2022_full_run.py            # full serial run (all dims)
    python src/cec2022_full_run.py --smoke    # 2 funcs, 3 runs, 50 iters
    python src/cec2022_full_run.py --part i/4 # i in {0,1,2,3}:
                                              #   0 = F1-6  @ D10
                                              #   1 = F7-12 @ D10
                                              #   2 = F1-6  @ D20
                                              #   3 = F7-12 @ D20
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
from sota_algorithms import run_lshade, run_cmaes

from opfunu.cec_based import cec2022

warnings.filterwarnings("ignore")

SMOKE = "--smoke" in sys.argv
PART_I, PART_N = 0, 1
if "--part" in sys.argv:
    _spec = sys.argv[sys.argv.index("--part") + 1]
    PART_I, PART_N = (int(x) for x in _spec.split("/"))

SEED0 = 20260714
POP = 30
ITERS = 10 if SMOKE else 500
RUNS = 3 if SMOKE else 30
BUDGET = POP * ITERS + 500      # parity cap for L-SHADE (matches A0's margin)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
os.makedirs(RESULTS, exist_ok=True)
_SUF = f"_part{PART_I}" if PART_N > 1 else ""
STATS_CSV = os.path.join(RESULTS, f"cec2022_stats{_SUF}.csv")
WILC_CSV = os.path.join(RESULTS, f"cec2022_wilcoxon{_SUF}.csv")
RAW_NPZ = os.path.join(RESULTS, f"raw_cec2022{_SUF}.npz")

ALGOS = ["CA", "CA-static", "GWO", "PSO", "GA", "WOA", "L-SHADE", "CMA-ES"]


def make_problem(cls, dim):
    prob = cls(ndim=dim)
    lo, sp = prob.lb.copy(), prob.ub - prob.lb

    def f_vec(U):
        Z = lo + sp * np.clip(np.atleast_2d(U), 0.0, 1.0)
        return np.array([prob.evaluate(z) for z in Z])

    def f_scalar(u):
        z = lo + sp * np.clip(np.asarray(u), 0.0, 1.0)
        return float(prob.evaluate(z))

    return prob, f_vec, f_scalar


def run_our(optimizer, f_vec, dim, seed):
    rng = np.random.default_rng(seed)
    _, bf, curve = optimizer(f_vec, 0.0, 1.0, dim, POP, ITERS, rng)
    return bf, np.asarray(curve, dtype=float)


def run_woa(f_scalar, dim, seed):
    from mealpy import WOA, FloatVar
    problem = {"obj_func": f_scalar,
               "bounds": FloatVar(lb=(0.0,) * dim, ub=(1.0,) * dim),
               "minmax": "min", "log_to": None}
    model = WOA.OriginalWOA(epoch=ITERS, pop_size=POP)
    gb = model.solve(problem, seed=seed)
    bf = float(gb.target.fitness)
    hist = np.asarray(model.history.list_global_best_fit, dtype=float)
    curve = np.interp(np.linspace(0, 1, ITERS),
                      np.linspace(0, 1, hist.size), hist)
    return bf, curve


RUNNERS = {
    "CA":        lambda fv, fs, d, s: run_our(alg.chess_algorithm_v3, fv, d, s),
    "CA-static": lambda fv, fs, d, s: run_our(alg.chess_algorithm_v2, fv, d, s),
    "GWO":       lambda fv, fs, d, s: run_our(alg.grey_wolf, fv, d, s),
    "PSO":       lambda fv, fs, d, s: run_our(alg.particle_swarm, fv, d, s),
    "GA":        lambda fv, fs, d, s: run_our(alg.genetic_algorithm, fv, d, s),
    "WOA":       lambda fv, fs, d, s: run_woa(fs, d, s),
    "L-SHADE":   lambda fv, fs, d, s: run_lshade(fv, 0.0, 1.0, d, POP, ITERS, s, max_evals=BUDGET),
    "CMA-ES":    lambda fv, fs, d, s: run_cmaes(fv, 0.0, 1.0, d, POP, ITERS, s),
}


def build_partition():
    """Return the (dim, [func_names]) list this process is responsible
    for, honoring the fixed 4-way split described in the module docstring."""
    names = sorted([n for n in dir(cec2022) if n.endswith("2022")
                    and n.startswith("F")],
                   key=lambda n: int(n[1:-4]))
    if SMOKE:
        names = names[:1] + names[-1:]

    if PART_N == 1:
        return [(10, names), (20, names)]
    if PART_N == 4:
        half1, half2 = names[:6], names[6:]
        groups = [(10, half1), (10, half2), (20, half1), (20, half2)]
        return [groups[PART_I]]
    raise ValueError("--part must be i/4 (or omitted for a full serial run)")


def preflight(fname, dim):
    prob = getattr(cec2022, fname)(ndim=dim)
    err = abs(prob.evaluate(prob.x_global) - prob.f_global)
    tol = 1e-6 * max(1.0, abs(prob.f_global))
    if err > tol:
        print(f"[preflight] {fname} D{dim}: EXCLUDED (f(x*) off by {err:.3g})",
              flush=True)
        return False
    return True


def main():
    t_start = time.time()
    partition = build_partition()
    total_cells = sum(len(names) for _, names in partition)
    print(f"[partition {PART_I}/{PART_N}] {total_cells} function(s): "
          f"{[(d, [n[1:-4] for n in names]) for d, names in partition]}",
          flush=True)

    stats_rows, wilc_rows, raw = [], [], {}
    fi = 0
    for dim, names in partition:
        for fname in names:
            fi += 1
            if not preflight(fname, dim):
                continue
            label = f"F{fname[1:-4]}-D{dim}"
            prob, f_vec, f_scalar = make_problem(getattr(cec2022, fname), dim)
            finals = {}
            for aname in ALGOS:
                t0 = time.time()
                vals = np.empty(RUNS)
                curves = np.empty((RUNS, ITERS))
                for r in range(RUNS):
                    bf, curve = RUNNERS[aname](f_vec, f_scalar, dim, SEED0 + r)
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
                print(f"[{fi:2d}/{total_cells}] {label:8s} {aname:9s} "
                      f"mean={vals.mean():12.5g} std={vals.std():10.4g} "
                      f"best={vals.min():12.5g} ({time.time()-t0:5.1f}s)",
                      flush=True)

            for aname in ALGOS:
                if aname == "CA":
                    continue
                _, p = ranksums(finals["CA"], finals[aname])
                direction = ("better" if finals["CA"].mean()
                             < finals[aname].mean() else "worse")
                sig = "yes" if p < 0.05 else "no"
                wilc_rows.append(dict(func=label, competitor=aname, p_value=p,
                                      v3_mean_direction=direction,
                                      significant=sig))

            # ---- checkpoint after every function ----
            pd.DataFrame(stats_rows).to_csv(STATS_CSV, index=False)
            pd.DataFrame(wilc_rows).to_csv(WILC_CSV, index=False)
            np.savez_compressed(RAW_NPZ, **raw)

    print(f"\nPartition {PART_I}/{PART_N} total wall time: "
          f"{(time.time()-t_start)/60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
