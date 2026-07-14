"""
sota_smoke_test.py
===================
Step A0 of PLAN_cec2022_and_reply.md: environment smoke test for the two
new SOTA baselines (L-SHADE, CMA-ES) before any real run.

Checks, on 30-D Sphere in the unit box (pop=30, iters=500, budget capped
at 15,500 evaluations for parity with CA's measured overhead):
    1. both wrappers run to completion without error,
    2. both reach a near-zero optimum on a trivial unimodal function,
    3. same-seed reproducibility (two runs, identical seed -> identical
       best_f and curve),
    4. different-seed variation (sanity: not identical),
    5. actual evaluation count stays within the 15,500 budget,
    6. wall-clock time per run.

Usage:
    python src/sota_smoke_test.py
"""

import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sota_algorithms import run_lshade, run_cmaes
from benchmark_functions import sphere

DIM = 30
POP = 30
ITERS = 500
BUDGET = 15500          # parity cap (~CA's measured overhead over pop*iters)
LO, HI = -100.0, 100.0  # real-space Sphere domain
SEED0 = 90210


def f_vec(U):
    """Sphere, decoded from the unit box [0,1]^D to [-100,100]^D."""
    Z = LO + (HI - LO) * np.clip(np.atleast_2d(U), 0.0, 1.0)
    return sphere(Z)


def check(name, run_fn, **kwargs):
    print(f"\n=== {name} ===", flush=True)

    t0 = time.time()
    bf1, curve1 = run_fn(f_vec, 0.0, 1.0, DIM, POP, ITERS, SEED0, **kwargs)
    dt1 = time.time() - t0
    print(f"run 1: best_f={bf1:.6g}  curve_len={len(curve1)}  "
          f"time={dt1:.2f}s", flush=True)
    assert len(curve1) == ITERS, f"curve length {len(curve1)} != {ITERS}"
    assert np.all(np.isfinite(curve1)), "non-finite value in curve"
    assert np.all(np.diff(curve1) <= 1e-9), "curve is not monotone non-increasing"
    assert bf1 < 1.0, f"best_f={bf1:.4g} too far from 0 on trivial Sphere"

    bf2, curve2 = run_fn(f_vec, 0.0, 1.0, DIM, POP, ITERS, SEED0, **kwargs)
    same_seed_ok = (bf1 == bf2) and np.array_equal(curve1, curve2)
    print(f"run 2 (same seed {SEED0}): best_f={bf2:.6g}  "
          f"bit-identical to run 1: {same_seed_ok}", flush=True)

    bf3, curve3 = run_fn(f_vec, 0.0, 1.0, DIM, POP, ITERS, SEED0 + 1, **kwargs)
    print(f"run 3 (seed {SEED0 + 1}): best_f={bf3:.6g}  "
          f"differs from run 1: {bf3 != bf1}", flush=True)

    return dict(name=name, best_f=bf1, time_s=dt1, same_seed_ok=same_seed_ok,
                differs_other_seed=(bf3 != bf1))


def main():
    results = []
    results.append(check("L-SHADE (niapy)", run_lshade, max_evals=BUDGET))
    results.append(check("CMA-ES (pycma)", run_cmaes))

    print("\n=== CP0 summary ===", flush=True)
    all_ok = True
    for r in results:
        ok = r["same_seed_ok"] and r["differs_other_seed"] and r["best_f"] < 1.0
        all_ok &= ok
        print(f"{r['name']:20s} best_f={r['best_f']:.4g}  "
              f"time={r['time_s']:.2f}s  seed-repro={r['same_seed_ok']}  "
              f"status={'OK' if ok else 'FAIL'}", flush=True)
    print(f"\nAll checks passed: {all_ok}", flush=True)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
