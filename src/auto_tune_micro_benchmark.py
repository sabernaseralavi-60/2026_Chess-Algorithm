"""
auto_tune_micro_benchmark.py
============================
Fast micro-benchmark used during the autonomous improvement loop of the
Chess Algorithm (CA). NOT part of the published experiments.

Problems
--------
  M1  CEC2017 F5  (D=30)  Shifted & Rotated Rastrigin        (multimodal)
  M2  CEC2017 F13 (D=30)  Hybrid Function 4                  (hybrid)
  M3  CEC2017 F22 (D=30)  Composition Function 3             (composition)
  M4  Welded beam design  (4 vars, 7 constraints, penalty)   (engineering)

Protocol: pop=30, iters=300, RUNS paired seeds shared by all algorithms.
Reported per problem: mean, std, best of final error (f - f_global for
CEC; raw penalized cost for welded beam), plus Wilcoxon signed-rank p
(paired seeds) for CA-variant vs GWO.

Usage:
    python src/auto_tune_micro_benchmark.py [ca_variant ...]
        ca_variant in {v1, v2}; default: v1 gwo
"""

import sys
import time

import numpy as np
from scipy.stats import wilcoxon

sys.path.insert(0, "src")
import algorithms as alg

from opfunu.cec_based import cec2017

SEED0 = 20260713
RUNS = 10
POP = 30
ITERS = 300
DIM = 30


# ----------------------------------------------------------------------
# Problem wrappers (population-matrix interface used by algorithms.py).
# All problems are presented to the optimizers on the unit hypercube
# [0,1]^D — real bounds are folded into the decoding step, exactly as in
# the paper's mealpy comparison — so scalar-bound optimizers work as-is.
# ----------------------------------------------------------------------
def unit_box(fun_real, lb_real, ub_real):
    lb_real = np.asarray(lb_real, dtype=float)
    ub_real = np.asarray(ub_real, dtype=float)

    def fun(U):
        U = np.atleast_2d(U)
        return fun_real(lb_real + (ub_real - lb_real) * U)

    return fun


def make_cec(cls, ndim):
    prob = cls(ndim=ndim)

    def fun_real(X):
        return np.array([prob.evaluate(x) for x in np.atleast_2d(X)])

    return (unit_box(fun_real, prob.lb, prob.ub),
            0.0, 1.0, ndim, prob.f_global)


def welded_beam(X):
    """Welded beam design, static penalty. x = (h, l, t, b).
    Known best ~ 1.7249 (Coello 2000 formulation, P=6000 lb, L=14 in)."""
    X = np.atleast_2d(X)
    h, l, t, b = X[:, 0], X[:, 1], X[:, 2], X[:, 3]
    P, Lc, E, G = 6000.0, 14.0, 30e6, 12e6
    tau_max, sigma_max, delta_max = 13600.0, 30000.0, 0.25

    cost = 1.10471 * h**2 * l + 0.04811 * t * b * (14.0 + l)

    M = P * (Lc + l / 2.0)
    R = np.sqrt(l**2 / 4.0 + ((h + t) / 2.0) ** 2)
    J = 2.0 * (np.sqrt(2.0) * h * l * (l**2 / 12.0 + ((h + t) / 2.0) ** 2))
    tau1 = P / (np.sqrt(2.0) * h * l)
    tau2 = M * R / J
    tau = np.sqrt(tau1**2 + 2.0 * tau1 * tau2 * l / (2.0 * R) + tau2**2)
    sigma = 6.0 * P * Lc / (b * t**2)
    delta = 4.0 * P * Lc**3 / (E * t**3 * b)
    Pc = (4.013 * E * np.sqrt(t**2 * b**6 / 36.0) / Lc**2
          * (1.0 - t / (2.0 * Lc) * np.sqrt(E / (4.0 * G))))

    g = np.stack([
        tau - tau_max,
        sigma - sigma_max,
        h - b,
        0.10471 * h**2 + 0.04811 * t * b * (14.0 + l) - 5.0,
        0.125 - h,
        delta - delta_max,
        P - Pc,
    ], axis=1)
    viol = np.sum(np.maximum(g, 0.0) ** 2, axis=1)
    return cost + 1e6 * viol


PROBLEMS = {}


def build_problems():
    PROBLEMS["M1_Rastrigin_SR"] = make_cec(cec2017.F42017, DIM)
    # NB: opfunu's F92017 (Schwefel) is buggy — optimizers reach values
    # below its claimed f_global — so it is deliberately avoided here.
    PROBLEMS["M2_BiRastrigin_SR"] = make_cec(cec2017.F62017, DIM)
    PROBLEMS["M3_Hybrid4"] = make_cec(cec2017.F132017, DIM)
    PROBLEMS["M4_Composition3"] = make_cec(cec2017.F222017, DIM)
    wb_lb = np.array([0.1, 0.1, 0.1, 0.1])
    wb_ub = np.array([2.0, 10.0, 10.0, 2.0])
    PROBLEMS["M5_WeldedBeam"] = (unit_box(welded_beam, wb_lb, wb_ub),
                                 0.0, 1.0, 4, 0.0)


def get_algo(name):
    if name == "v1":
        return "CA-v1", alg.chess_algorithm
    if name == "v2":
        return "CA-v2", alg.chess_algorithm_v2
    if name == "v3":
        return "CA-v3", alg.chess_algorithm_v3
    if name == "gwo":
        return "GWO", alg.grey_wolf
    raise ValueError(name)


def main(variants):
    build_problems()
    algos = [get_algo(v) for v in variants]
    finals = {label: {} for label, _ in algos}

    for pname, (fun, lb, ub, dim, fg) in PROBLEMS.items():
        t0 = time.time()
        for label, optimizer in algos:
            vals = np.empty(RUNS)
            for r in range(RUNS):
                rng = np.random.default_rng(SEED0 + r)
                _, bf, _ = optimizer(fun, lb, ub, dim, POP, ITERS, rng)
                vals[r] = bf - fg
            finals[label][pname] = vals
        dt = time.time() - t0
        print(f"[{pname}] done in {dt:.1f}s")

    # ---- report ----
    labels = [label for label, _ in algos]
    print()
    header = f"{'problem':<18}" + "".join(
        f"{lab + ' mean':>14}{lab + ' std':>12}{lab + ' best':>13}"
        for lab in labels)
    print(header)
    for pname in PROBLEMS:
        row = f"{pname:<18}"
        for lab in labels:
            v = finals[lab][pname]
            row += f"{v.mean():>14.4g}{v.std():>12.3g}{v.min():>13.4g}"
        print(row)

    if "GWO" in labels:
        print("\nPaired Wilcoxon (variant vs GWO), p-values:")
        for lab in labels:
            if lab == "GWO":
                continue
            for pname in PROBLEMS:
                a, b = finals[lab][pname], finals["GWO"][pname]
                try:
                    p = wilcoxon(a, b).pvalue
                except ValueError:
                    p = 1.0
                sign = "<" if a.mean() < b.mean() else ">"
                print(f"  {lab} vs GWO  {pname:<18} p={p:.4f}  "
                      f"(mean {sign} GWO mean)")


if __name__ == "__main__":
    args = sys.argv[1:] or ["v1", "gwo"]
    main(args)
