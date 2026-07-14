"""
sota_algorithms.py
===================
Wrappers for the two competition-grade SOTA baselines added in response to
reviewer concern #3 (outdated baselines) -- see PLAN_cec2022_and_reply.md,
steps A0/A2:

    * L-SHADE - Success-History Adaptive DE with Linear Population Size
                Reduction (Tanabe & Fukunaga, CEC-2014). Source: the
                `niapy` package's LpsrSuccessHistoryAdaptiveDifferentialEvolution.
                (`pyade` / "pyade-python" is NOT usable in this environment:
                the source repository xKuZz/pyade no longer exists on
                GitHub -- confirmed via the GitHub API, not just a failed
                `pip install` -- and no working PyPI package under that
                name exists either, despite third-party index pages
                claiming otherwise. niapy is a maintained, JOSS-reviewed
                package that ships the same published algorithm under its
                original name and citation, so it is used directly rather
                than falling back to JADE.)
    * CMA-ES  - Covariance Matrix Adaptation Evolution Strategy
                (Hansen & Ostermeier, 2001), via `pycma` (the `cma`
                package), the reference implementation.

Both wrappers share the interface used throughout this project:

    best_f, curve = run_xxx(fun, lb, ub, dim, pop, iters, seed)

where `fun` is a vectorized objective fun(X) -> array (X shape (n, dim)),
lb/ub are scalars (the unit-box convention used everywhere else in this
project), and `curve` is a best-so-far array of length `iters` so that
convergence plots align with every other algorithm in the roster.

Population-size note: CMA-ES uses `pop` as a constant per-generation
population size (lambda), so it consumes exactly pop * iters evaluations,
one curve point per generation -- identical bookkeeping to CA/GWO/PSO/GA.
L-SHADE instead uses `pop` as its *initial* population size and linearly
shrinks it toward 4 following its published schedule as the evaluation
budget is consumed (this is intrinsic to the algorithm, not a deviation
from it); its curve is therefore resampled onto an `iters`-point grid from
the algorithm's own evaluation-indexed history so it can be overlaid with
the fixed-population curves.
"""

import numpy as np
import cma

from niapy.algorithms.modified import (
    LpsrSuccessHistoryAdaptiveDifferentialEvolution as _LSHADE)
from niapy.problems import Problem as _NiaProblem
from niapy.task import Task as _NiaTask


class _VectorFunProblem(_NiaProblem):
    """Adapts a vectorized fun(X) -> array objective to niapy's per-row
    Problem interface (niapy evaluates one candidate vector at a time)."""

    def __init__(self, fun, dim, lower, upper):
        super().__init__(dimension=dim, lower=lower, upper=upper)
        self._fun = fun

    def _evaluate(self, x):
        return float(self._fun(x[None, :])[0])


def run_lshade(fun, lb, ub, dim, pop, iters, seed, max_evals=None,
              return_x=False):
    """L-SHADE (Tanabe & Fukunaga, 2014). See module docstring.

    return_x=True additionally returns the best solution vector, as the
    first element: (best_x, best_f, curve). Default False keeps the
    standard (best_f, curve) interface used by the full-suite runners.
    """
    budget = int(max_evals) if max_evals is not None else pop * iters
    problem = _VectorFunProblem(fun, dim, float(lb), float(ub))
    task = _NiaTask(problem=problem, max_evals=budget, enable_logging=False)
    algo = _LSHADE(population_size=pop, seed=seed)
    best_x, best_f = algo.run(task)

    evals, fits = task.convergence_data(x_axis='evals')
    evals, fits = np.asarray(evals, dtype=float), np.asarray(fits, dtype=float)
    grid = np.linspace(1, budget, iters)
    curve = np.interp(grid, evals, fits)
    if return_x:
        return np.asarray(best_x, dtype=float), float(best_f), curve
    return float(best_f), curve


def run_cmaes(fun, lb, ub, dim, pop, iters, seed, return_x=False):
    """CMA-ES (Hansen & Ostermeier, 2001). See module docstring.

    return_x=True additionally returns the best solution vector, as the
    first element: (best_x, best_f, curve). Default False keeps the
    standard (best_f, curve) interface used by the full-suite runners.
    """
    lb_f, ub_f = float(lb), float(ub)
    rng = np.random.default_rng(seed)
    x0 = lb_f + (ub_f - lb_f) * rng.random(dim)
    sigma0 = 0.3 * (ub_f - lb_f)
    seed_i = int(seed) % (2 ** 31 - 1)
    opts = {"popsize": pop, "bounds": [lb_f, ub_f], "seed": seed_i or 1,
            "verbose": -9, "maxiter": iters,
            "tolfun": 0, "tolfunhist": 0, "tolx": 0,
            "tolstagnation": 10 ** 9, "tolflatfitness": 10 ** 9}
    es = cma.CMAEvolutionStrategy(x0, sigma0, opts)

    curve = np.empty(iters)
    best_f = np.inf
    best_x = x0.copy()
    for t in range(iters):
        if es.stop():
            curve[t:] = best_f
            break
        X = es.ask()
        F = fun(np.asarray(X))
        es.tell(X, F.tolist())
        i_min = int(np.argmin(F))
        if F[i_min] < best_f:
            best_f = float(F[i_min])
            best_x = np.asarray(X[i_min], dtype=float)
        curve[t] = best_f
    if return_x:
        return best_x, float(best_f), curve
    return float(best_f), curve
