"""
phase1_sanity_check.py
======================
Phase-1 sanity check for the adaptive Chess Algorithm (CA-v3): verify
that the redesign has not lost the edge on the paper's two transportation
problems.

    P1  Arterial signal timing (16 vars)  -- traffic_case_study.total_delay
    P2  Continuous berth allocation (30 vars, known optimum 4,860 min)

Protocol identical to src/mealpy_comparison.py: unit-hypercube search
space, pop 30, 300 iterations, 30 runs, seed SEED0 + r with
SEED0 = 20260705. CA-v1 therefore reproduces the paper's published CA
column exactly (same RNG stream), which doubles as a regression test.

Usage:  python src/phase1_sanity_check.py
"""

import sys
import time

import numpy as np
from scipy.stats import ranksums

sys.path.insert(0, "src")
import algorithms as alg
from mealpy_comparison import PROBLEMS, make_unit, BERTH_OPT, berth_overlap
from mealpy_comparison import BERTH_LB, BERTH_UB

POP, ITERS, RUNS = 30, 300, 30
SEED0 = 20260705

ALGOS = [
    ("CA-v1", alg.chess_algorithm),
    ("CA-v2", alg.chess_algorithm_v2),
    ("CA-v3", alg.chess_algorithm_v3),
    ("GWO", alg.grey_wolf),
]


def main():
    out = {}
    for pname, spec in PROBLEMS.items():
        f_vec, _ = make_unit(spec["fun"], spec["lb"], spec["ub"])
        dim = spec["dim"]
        finals = {}
        bests = {}
        for lab, opt in ALGOS:
            t0 = time.time()
            vals = np.empty(RUNS)
            bx_best, bf_best = None, np.inf
            for r in range(RUNS):
                rng = np.random.default_rng(SEED0 + r)
                bx, bf, _ = opt(f_vec, 0.0, 1.0, dim, POP, ITERS, rng)
                vals[r] = bf
                if bf < bf_best:
                    bf_best, bx_best = bf, bx.copy()
            finals[lab] = vals
            bests[lab] = (bf_best, bx_best)
            print(f"{pname:7s} {lab:6s} mean={vals.mean():10.4f} "
                  f"std={vals.std():8.4f} best={vals.min():10.4f} "
                  f"median={np.median(vals):10.4f} "
                  f"({time.time()-t0:.0f}s)", flush=True)
        out[pname] = (finals, bests)

        print(f"  -- rank-sum vs GWO and vs CA-v1 ({pname}) --")
        for lab in ("CA-v1", "CA-v2", "CA-v3"):
            _, pg = ranksums(finals[lab], finals["GWO"])
            _, p1 = ranksums(finals[lab], finals["CA-v1"])
            print(f"  {lab}: vs GWO p={pg:.4f} "
                  f"({'better' if finals[lab].mean() < finals['GWO'].mean() else 'worse'} mean); "
                  f"vs CA-v1 p={p1:.4f}")

        if pname == "berth":
            span = BERTH_UB - BERTH_LB
            print("  -- best-plan optimality gap & feasibility --")
            for lab, _ in ALGOS:
                bf, bx = bests[lab]
                z = BERTH_LB + span * np.clip(bx, 0, 1)
                ov = berth_overlap(z)
                gap = 100.0 * (bf - BERTH_OPT) / BERTH_OPT
                print(f"  {lab:6s} best={bf:9.1f}  gap={gap:6.2f}%  "
                      f"overlap={ov:.1f}")

    np.savez("results/raw_phase1_sanity.npz",
             **{f"{p}__{l}": out[p][0][l] for p in out for l in out[p][0]})


if __name__ == "__main__":
    main()
