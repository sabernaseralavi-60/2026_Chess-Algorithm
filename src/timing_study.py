"""
timing_study.py
=================
Step A5 of PLAN_cec2022_and_reply.md: measured wall-clock time AND exact
function-evaluation counts for all 8 algorithms, replacing the paper's
prior "ten to fifteen percent more evaluations" estimate for CA with a
measured figure.

Problems (6, spanning every section of the paper): F1, F13, F22 @ D=30
(CEC-2017); F8-2022 @ D=20 (CEC-2022); WeldedBeam (engineering); signal
timing P1 (transport, iters=300 per the mealpy_comparison protocol; every
other problem here uses pop=30/iters=500). 10 runs per (problem, algorithm)
cell, machine otherwise idle -- run this only once the other Phase-A
background jobs have finished, or the wall-clock numbers (not the
evaluation counts, which are deterministic) will be inflated by CPU
contention.

Evaluation counting: every objective call is intercepted by a counting
wrapper (counts rows for vectorized calls, +1 for scalar calls), so the
reported eval count is exact, not inferred from pop*iters.

Outputs:
    results/timing_stats.csv   mean_time_s, mean_evals, evals_over_popiters,
                                relative_time_vs_GA, per (problem, algo)

Usage:
    python src/timing_study.py
    python src/timing_study.py --smoke   # 2 problems, 2 runs, 20 iters
"""

import os
import sys
import time
import warnings

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import algorithms as alg
from sota_algorithms import run_lshade, run_cmaes
from engineering_problems import ENGINEERING
from opfunu.cec_based import cec2017, cec2022

warnings.filterwarnings("ignore")

SMOKE = "--smoke" in sys.argv
RUNS = 2 if SMOKE else 10

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
os.makedirs(RESULTS, exist_ok=True)
STATS_CSV = os.path.join(RESULTS, "timing_stats.csv")

ALGOS = ["CA", "CA-static", "GWO", "PSO", "GA", "WOA", "L-SHADE", "CMA-ES"]


# ----------------------------------------------------------------------
# counting wrapper
# ----------------------------------------------------------------------
def make_counted(f_vec):
    """Wraps a vectorized fun(X)->array so every call is tallied by row
    count. A scalar-call shim (1 row at a time) is derived from the same
    counter for mealpy's per-solution WOA interface."""
    count = [0]

    def cf_vec(U):
        U = np.atleast_2d(U)
        count[0] += U.shape[0]
        return f_vec(U)

    def cf_scalar(u):
        count[0] += 1
        return float(f_vec(np.atleast_2d(u))[0])

    return cf_vec, cf_scalar, count


# ----------------------------------------------------------------------
# problems
# ----------------------------------------------------------------------
def _cec2017(n):
    prob = cec2017.__dict__[f"F{n}2017"](ndim=30)
    lo, sp = prob.lb.copy(), prob.ub - prob.lb

    def f_vec(U, lo=lo, sp=sp, prob=prob):
        Z = lo + sp * np.clip(np.atleast_2d(U), 0.0, 1.0)
        return np.array([prob.evaluate(z) for z in Z])

    return dict(f_vec=f_vec, dim=30, pop=30, iters=20 if SMOKE else 500,
                seed0=20260713, label=f"F{n}")


def _cec2022(n, dim):
    prob = cec2022.__dict__[f"F{n}2022"](ndim=dim)
    lo, sp = prob.lb.copy(), prob.ub - prob.lb

    def f_vec(U, lo=lo, sp=sp, prob=prob):
        Z = lo + sp * np.clip(np.atleast_2d(U), 0.0, 1.0)
        return np.array([prob.evaluate(z) for z in Z])

    return dict(f_vec=f_vec, dim=dim, pop=30, iters=20 if SMOKE else 500,
                seed0=20260714, label=f"F{n}-2022-D{dim}")


def _engineering(name):
    fun, lb, ub, dim, f_ref = ENGINEERING[name]
    span = ub - lb

    def f_vec(U, lb=lb, span=span, fun=fun):
        Z = lb + span * np.clip(np.atleast_2d(U), 0.0, 1.0)
        return fun(Z)

    return dict(f_vec=f_vec, dim=dim, pop=30, iters=20 if SMOKE else 500,
                seed0=20260713, label=name)


def _signal_p1():
    import mealpy_comparison as mc
    spec = mc.PROBLEMS["signal"]
    f_vec, _ = mc.make_unit(spec["fun"], spec["lb"], spec["ub"])
    return dict(f_vec=f_vec, dim=spec["dim"], pop=mc.POP,
                iters=20 if SMOKE else mc.ITERS, seed0=mc.SEED0,
                label="SignalP1")


def build_problems():
    probs = [_cec2017(1), _cec2017(13), _cec2017(22), _cec2022(8, 20),
            _engineering("WeldedBeam"), _signal_p1()]
    if SMOKE:
        probs = probs[:2]
    return probs


# ----------------------------------------------------------------------
# runners (mirrors cec2022_full_run.py's RUNNERS, plus counting)
# ----------------------------------------------------------------------
def run_one(aname, f_vec, dim, pop, iters, seed):
    cf_vec, cf_scalar, count = make_counted(f_vec)
    budget = pop * iters + 500

    t0 = time.perf_counter()
    if aname == "CA":
        rng = np.random.default_rng(seed)
        alg.chess_algorithm_v3(cf_vec, 0.0, 1.0, dim, pop, iters, rng)
    elif aname == "CA-static":
        rng = np.random.default_rng(seed)
        alg.chess_algorithm_v2(cf_vec, 0.0, 1.0, dim, pop, iters, rng)
    elif aname == "GWO":
        rng = np.random.default_rng(seed)
        alg.grey_wolf(cf_vec, 0.0, 1.0, dim, pop, iters, rng)
    elif aname == "PSO":
        rng = np.random.default_rng(seed)
        alg.particle_swarm(cf_vec, 0.0, 1.0, dim, pop, iters, rng)
    elif aname == "GA":
        rng = np.random.default_rng(seed)
        alg.genetic_algorithm(cf_vec, 0.0, 1.0, dim, pop, iters, rng)
    elif aname == "WOA":
        from mealpy import WOA, FloatVar
        problem = {"obj_func": cf_scalar,
                   "bounds": FloatVar(lb=(0.0,) * dim, ub=(1.0,) * dim),
                   "minmax": "min", "log_to": None}
        model = WOA.OriginalWOA(epoch=iters, pop_size=pop)
        model.solve(problem, seed=seed)
    elif aname == "L-SHADE":
        run_lshade(cf_vec, 0.0, 1.0, dim, pop, iters, seed, max_evals=budget)
    elif aname == "CMA-ES":
        run_cmaes(cf_vec, 0.0, 1.0, dim, pop, iters, seed)
    else:
        raise ValueError(aname)
    elapsed = time.perf_counter() - t0
    return elapsed, count[0]


def main():
    problems = build_problems()
    rows = []
    t_start = time.time()

    for prob in problems:
        label = prob["label"]
        pop, iters = prob["pop"], prob["iters"]
        core_budget = pop * iters
        cell_times = {}
        for aname in ALGOS:
            times = np.empty(RUNS)
            evals = np.empty(RUNS)
            for r in range(RUNS):
                t, e = run_one(aname, prob["f_vec"], prob["dim"], pop, iters,
                               prob["seed0"] + r)
                times[r], evals[r] = t, e
            cell_times[aname] = times.mean()
            rows.append(dict(
                problem=label, algo=aname, mean_time_s=times.mean(),
                std_time_s=times.std(), mean_evals=evals.mean(),
                core_budget=core_budget,
                evals_over_core=evals.mean() / core_budget))
            print(f"[timing] {label:12s} {aname:9s} "
                  f"time={times.mean():7.3f}s  evals={evals.mean():9.1f} "
                  f"({evals.mean()/core_budget:6.3f}x core)", flush=True)

        for row in rows:
            if row["problem"] == label:
                row["relative_time_vs_GA"] = (
                    cell_times[row["algo"]] / cell_times["GA"])

        pd.DataFrame(rows).to_csv(STATS_CSV, index=False)

    print(f"\nTotal timing wall time: {(time.time()-t_start)/60:.1f} min",
          flush=True)

    df = pd.DataFrame(rows)
    ca_overhead = (df[df.algo == "CA"]["evals_over_core"].mean() - 1.0) * 100
    print(f"\nCA measured evaluation overhead vs pop*iters core budget: "
          f"{ca_overhead:.1f}% (averaged over {len(problems)} problems)")


if __name__ == "__main__":
    main()
