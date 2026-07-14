"""
cec2017_restoration_audit.py
==============================
Step A6 of PLAN_cec2022_and_reply.md: cross-validate the CEC-2017
functions excluded for opfunu defects against a second, independent
Python port -- `cec2017` (tilleyd/cec2017-py, installed from GitHub
source; adapted directly from Awad's official C implementation and the
official data files).

NUMBERING. The two libraries number the suite differently, and the
difference is load-bearing. The official suite defines F1-F30 with F2
(Sum of Different Power) withdrawn from the competition for numerical
instability. tilleyd keeps the official numbering (f1..f30, f2 included
but unused here). opfunu ships 29 classes renumbered consecutively after
the withdrawal, so opfunu's F{n}2017 implements the official function
F(n+1) for n >= 2 -- verified against the libraries' own function names
(opfunu F2 = "Zakharov" = official F3; opfunu F4 = "Rastrigin" =
official F5; opfunu F16 = "Hybrid 7" = official F17; etc.). This
paper's labels follow opfunu's numbering, so the tilleyd counterpart of
paper label Fn is tilleyd f(n+1). (Empirically, opfunu pairs the
formula of official F(n+1) with the shift-data slot n, which is itself
the likely origin of several of the defects the audit catches.)

For each audited label:
    1. preflight: tilleyd f(n+1) evaluated 1e-6 off its own shift point
       vs the official optimum 100*(n+1). (The offset sidesteps a
       divide-by-zero singularity that the composition functions'
       distance-weight term has exactly at the shift point.)
    2. flatness: std of f over 100 random points in the box.
    3. below-optimum probe: 10 independent CA (chess_algorithm_v3)
       runs, D=30, pop=30, iters=500, SEED0=20260713 (the CEC-2017
       suite protocol). A label FAILS if any run's best value drops
       more than 1.0 below the official optimum -- the same tolerance
       as src/phase2_3_analysis.py::audit_below_optimum.

Audited labels: F5, F9, F15, F16, F19, F21 -- every label excluded for
an opfunu defect (F5 near-flat; F9/F15/F19/F21 below-optimum in the
original audit; F16 below-optimum once the stronger 8-algorithm roster
was added).

Outputs:
    results/table_cec2017_restoration_audit.md

Usage:  python src/cec2017_restoration_audit.py
"""

import os
import sys
import time
import warnings

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import algorithms as alg
import cec2017.functions as til
from cec2017 import transforms

warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
os.makedirs(RESULTS, exist_ok=True)

DIM = 30
POP = 30
ITERS = 500
RUNS = 10
SEED0 = 20260713
TOL = 1.0  # matches audit_below_optimum's below-optimum tolerance

TARGET_LABELS = [5, 9, 15, 16, 19, 21]   # paper (opfunu) labels
LO, HI = -100.0, 100.0


def official_num(label_n):
    """Paper label Fn (opfunu numbering) -> official function number."""
    return label_n + 1 if label_n >= 2 else label_n


def make_f_vec(label_n):
    f = getattr(til, f"f{official_num(label_n)}")

    def f_vec(U):
        Z = LO + (HI - LO) * np.clip(np.atleast_2d(U), 0.0, 1.0)
        return np.asarray(f(Z), dtype=float)

    return f_vec, f


def preflight(label_n, f_real):
    m = official_num(label_n)
    f_global = 100.0 * m
    if m <= 20:
        shift = transforms.shifts[m - 1][:DIM].copy()
    else:
        shift = transforms.shifts_cf[m - 21][0][:DIM].copy()
    probe = shift[None, :] + 1e-6
    val = float(f_real(probe)[0])
    return val, f_global, abs(val - f_global)


def flatness(f_vec, seed):
    rng = np.random.default_rng(seed)
    X = rng.random((100, DIM))
    F = f_vec(X)
    return float(np.std(F)), float(np.mean(F))


def below_optimum_probe(f_vec, f_global):
    worst_below = 0.0
    finals = np.empty(RUNS)
    for r in range(RUNS):
        rng = np.random.default_rng(SEED0 + r)
        _, bf, _ = alg.chess_algorithm_v3(f_vec, 0.0, 1.0, DIM, POP, ITERS, rng)
        finals[r] = bf
        worst_below = min(worst_below, bf - f_global)
    return finals, worst_below


def main():
    rows = []
    t0 = time.time()
    for n in TARGET_LABELS:
        f_vec, f_real = make_f_vec(n)
        m = official_num(n)

        val_at_shift, f_global, pf_err = preflight(n, f_real)
        pf_pass = pf_err < 1e-3 * max(1.0, abs(f_global))

        std_flat, mean_flat = flatness(f_vec, seed=999)
        flat_fail = std_flat < 1.0

        finals, worst_below = below_optimum_probe(f_vec, f_global)
        below_fail = worst_below < -TOL

        verdict = ("Pass" if (pf_pass and not below_fail and not flat_fail)
                   else "Fail")

        rows.append(dict(
            label=f"F{n}", official=f"F{m}", til_f_at_shift=val_at_shift,
            f_global=f_global, preflight_err=pf_err, preflight_pass=pf_pass,
            random_std=std_flat, random_mean=mean_flat,
            ca_min_final=float(finals.min()),
            ca_mean_final=float(finals.mean()),
            worst_below_optimum=worst_below, below_optimum_fail=below_fail,
            verdict=verdict))
        print(f"[audit] label F{n:2d} (official F{m:2d})  "
              f"preflight_err={pf_err:10.4f} (pass={pf_pass})  "
              f"rand_std={std_flat:12.4g}  "
              f"worst_below={worst_below:+10.3f} (fail={below_fail})  "
              f"-> {verdict}  ({time.time()-t0:.1f}s elapsed)", flush=True)

    write_table(rows)
    print(f"\nTotal A6 audit wall time: {(time.time()-t0)/60:.1f} min",
          flush=True)


def write_table(rows):
    lines = ["## CEC-2017 restoration audit (tilleyd/cec2017-py, "
             "independent official-data implementation)",
             "",
             "| Label | Official func | f(shift+eps) | Official f* "
             "| Preflight err | Random-100 std | CA min (10 runs) "
             "| Worst below f* | Verdict |",
             "|---|---|---:|---:|---:|---:|---:|---:|---|"]
    for row in rows:
        lines.append(
            f"| {row['label']} | {row['official']} | "
            f"{row['til_f_at_shift']:.3f} | {row['f_global']:.1f} | "
            f"{row['preflight_err']:.4f} | {row['random_std']:.4g} | "
            f"{row['ca_min_final']:.3f} | "
            f"{row['worst_below_optimum']:+.3f} | **{row['verdict']}** |")
    with open(os.path.join(RESULTS, "table_cec2017_restoration_audit.md"),
              "w", encoding="utf8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
