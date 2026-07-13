"""
phase_threshold_check.py
=========================
Small grid check of the two phase-transition thresholds (div_open,
div_end) used in the adaptive control layer's phase classifier
(Eq. eq-phase in paper.qmd, @sec-adaptive). Not an exhaustive
sensitivity sweep -- four threshold combinations checked against two
CEC-2017 functions -- but enough to confirm the defaults used
throughout the paper (0.22, 0.045) are a reasonable, empirically
checked choice rather than an arbitrary one. A full sensitivity study
across the complete parameter space remains future work (see the
paper's Limitations section).

Reproduce with:  python src/phase_threshold_check.py
"""
import sys
import os

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import algorithms as alg

from opfunu.cec_based import cec2017

POP, ITERS, RUNS = 30, 300, 8
SEED0 = 900001

GRID = [(0.15, 0.03), (0.22, 0.045), (0.30, 0.06), (0.22, 0.09)]


def unit_box(fun_real, lb, ub):
    lb, ub = np.asarray(lb, float), np.asarray(ub, float)

    def fun(U):
        U = np.atleast_2d(U)
        return fun_real(lb + (ub - lb) * U)

    return fun


def build_problems():
    probs = {}
    for name, cls in [("F4_Rastrigin", cec2017.F42017),
                      ("F13_Hybrid4", cec2017.F132017)]:
        p = cls(ndim=30)
        fr = lambda X, p=p: np.array([p.evaluate(x)
                                      for x in np.atleast_2d(X)])
        probs[name] = (unit_box(fr, p.lb, p.ub), p.f_global)
    return probs


def main():
    probs = build_problems()
    rows = []
    for div_open, div_end in GRID:
        for name, (f, fg) in probs.items():
            vals = np.empty(RUNS)
            for r in range(RUNS):
                rng = np.random.default_rng(SEED0 + r)
                _, bf, _ = alg.chess_algorithm_v3(
                    f, 0.0, 1.0, 30, POP, ITERS, rng,
                    div_open=div_open, div_end=div_end)
                vals[r] = bf - fg
            rows.append(dict(div_open=div_open, div_end=div_end,
                             function=name, mean_error=vals.mean(),
                             std_error=vals.std()))
            print(f"div_open={div_open} div_end={div_end} {name}: "
                  f"mean={vals.mean():.4g}", flush=True)

    df = pd.DataFrame(rows)
    out_dir = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "results")
    df.to_csv(os.path.join(out_dir, "phase_threshold_check.csv"),
             index=False)
    print("\nWrote results/phase_threshold_check.csv")


if __name__ == "__main__":
    main()
