"""
engineering_problems.py
=======================
Seven classic constrained engineering design problems in the standard
formulations used throughout the metaheuristics literature (Coello 2000;
Mirjalili et al. 2014-2017). Constraints are handled with a static
penalty:  f_pen(x) = f(x) + 1e6 * sum(max(0, g_i)^2),
identical to the approach used elsewhere in this project.

Every problem is exposed as:  (fun, lb, ub, dim, name, f_ref)
where `fun` maps a (P, D) population matrix to (P,) penalized objectives
and `f_ref` is the best value commonly reported in the literature for
that formulation (for orientation only; not used by the optimizers).
"""

import numpy as np

PEN = 1e6


def _pen(cost, G):
    return cost + PEN * np.sum(np.maximum(G, 0.0) ** 2, axis=1)


# ----------------------------------------------------------------------
# 1. Welded beam design (4 vars, 7 constraints) -- best ~1.7249
# ----------------------------------------------------------------------
def welded_beam(X):
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
    Gm = np.stack([
        tau - tau_max,
        sigma - sigma_max,
        h - b,
        0.10471 * h**2 + 0.04811 * t * b * (14.0 + l) - 5.0,
        0.125 - h,
        delta - delta_max,
        P - Pc,
    ], axis=1)
    return _pen(cost, Gm)


# ----------------------------------------------------------------------
# 2. Tension/compression spring (3 vars, 4 constraints) -- best ~0.012665
# ----------------------------------------------------------------------
def spring(X):
    X = np.atleast_2d(X)
    d, D, N = X[:, 0], X[:, 1], X[:, 2]
    cost = (N + 2.0) * D * d**2
    Gm = np.stack([
        1.0 - D**3 * N / (71785.0 * d**4),
        (4.0 * D**2 - d * D) / (12566.0 * (D * d**3 - d**4))
        + 1.0 / (5108.0 * d**2) - 1.0,
        1.0 - 140.45 * d / (D**2 * N),
        (D + d) / 1.5 - 1.0,
    ], axis=1)
    return _pen(cost, Gm)


# ----------------------------------------------------------------------
# 3. Pressure vessel (4 vars, 4 constraints), continuous thicknesses
#    -- best ~5885.33 for the continuous formulation
# ----------------------------------------------------------------------
def pressure_vessel(X):
    X = np.atleast_2d(X)
    Ts, Th, R, L = X[:, 0], X[:, 1], X[:, 2], X[:, 3]
    cost = (0.6224 * Ts * R * L + 1.7781 * Th * R**2
            + 3.1661 * Ts**2 * L + 19.84 * Ts**2 * R)
    Gm = np.stack([
        -Ts + 0.0193 * R,
        -Th + 0.00954 * R,
        -np.pi * R**2 * L - (4.0 / 3.0) * np.pi * R**3 + 1296000.0,
        L - 240.0,
    ], axis=1)
    return _pen(cost, Gm)


# ----------------------------------------------------------------------
# 4. Speed reducer (7 vars, 11 constraints) -- best ~2994.47
# ----------------------------------------------------------------------
def speed_reducer(X):
    X = np.atleast_2d(X)
    x1, x2, x3, x4, x5, x6, x7 = (X[:, i] for i in range(7))
    cost = (0.7854 * x1 * x2**2
            * (3.3333 * x3**2 + 14.9334 * x3 - 43.0934)
            - 1.508 * x1 * (x6**2 + x7**2)
            + 7.4777 * (x6**3 + x7**3)
            + 0.7854 * (x4 * x6**2 + x5 * x7**2))
    Gm = np.stack([
        27.0 / (x1 * x2**2 * x3) - 1.0,
        397.5 / (x1 * x2**2 * x3**2) - 1.0,
        1.93 * x4**3 / (x2 * x3 * x6**4) - 1.0,
        1.93 * x5**3 / (x2 * x3 * x7**4) - 1.0,
        np.sqrt((745.0 * x4 / (x2 * x3))**2 + 16.9e6) / (110.0 * x6**3)
        - 1.0,
        np.sqrt((745.0 * x5 / (x2 * x3))**2 + 157.5e6) / (85.0 * x7**3)
        - 1.0,
        x2 * x3 / 40.0 - 1.0,
        5.0 * x2 / x1 - 1.0,
        x1 / (12.0 * x2) - 1.0,
        (1.5 * x6 + 1.9) / x4 - 1.0,
        (1.1 * x7 + 1.9) / x5 - 1.0,
    ], axis=1)
    return _pen(cost, Gm)


# ----------------------------------------------------------------------
# 5. Three-bar truss (2 vars, 3 constraints) -- best ~263.8958
# ----------------------------------------------------------------------
def three_bar_truss(X):
    X = np.atleast_2d(X)
    x1, x2 = X[:, 0], X[:, 1]
    Lc, P, s = 100.0, 2.0, 2.0
    cost = (2.0 * np.sqrt(2.0) * x1 + x2) * Lc
    den = np.sqrt(2.0) * x1**2 + 2.0 * x1 * x2
    Gm = np.stack([
        (np.sqrt(2.0) * x1 + x2) / np.maximum(den, 1e-12) * P - s,
        x2 / np.maximum(den, 1e-12) * P - s,
        1.0 / np.maximum(np.sqrt(2.0) * x2 + x1, 1e-12) * P - s,
    ], axis=1)
    return _pen(cost, Gm)


# ----------------------------------------------------------------------
# 6. Gear train (4 vars, integer-rounded inside) -- best ~2.7e-12
# ----------------------------------------------------------------------
def gear_train(X):
    X = np.atleast_2d(X)
    Z = np.round(np.clip(X, 12.0, 60.0))
    x1, x2, x3, x4 = Z[:, 0], Z[:, 1], Z[:, 2], Z[:, 3]
    return (1.0 / 6.931 - x1 * x2 / (x3 * x4)) ** 2


# ----------------------------------------------------------------------
# 7. Cantilever beam (5 vars, 1 constraint) -- best ~1.33996
# ----------------------------------------------------------------------
def cantilever_beam(X):
    X = np.atleast_2d(X)
    cost = 0.0624 * X.sum(axis=1)
    g = (61.0 / X[:, 0]**3 + 37.0 / X[:, 1]**3 + 19.0 / X[:, 2]**3
         + 7.0 / X[:, 3]**3 + 1.0 / X[:, 4]**3 - 1.0)
    return _pen(cost, g[:, None])


ENGINEERING = {
    "WeldedBeam": (welded_beam,
                   np.array([0.1, 0.1, 0.1, 0.1]),
                   np.array([2.0, 10.0, 10.0, 2.0]), 4, 1.7249),
    "Spring": (spring,
               np.array([0.05, 0.25, 2.0]),
               np.array([2.0, 1.3, 15.0]), 3, 0.012665),
    "PressureVessel": (pressure_vessel,
                       np.array([0.0625, 0.0625, 10.0, 10.0]),
                       np.array([6.1875, 6.1875, 200.0, 240.0]), 4,
                       5885.33),
    "SpeedReducer": (speed_reducer,
                     np.array([2.6, 0.7, 17.0, 7.3, 7.3, 2.9, 5.0]),
                     np.array([3.6, 0.8, 28.0, 8.3, 8.3, 3.9, 5.5]), 7,
                     2994.47),
    "ThreeBarTruss": (three_bar_truss,
                      np.array([0.0, 0.0]),
                      np.array([1.0, 1.0]), 2, 263.8958),
    "GearTrain": (gear_train,
                  np.array([12.0, 12.0, 12.0, 12.0]),
                  np.array([60.0, 60.0, 60.0, 60.0]), 4, 2.7e-12),
    "CantileverBeam": (cantilever_beam,
                       np.array([0.01, 0.01, 0.01, 0.01, 0.01]),
                       np.array([100.0, 100.0, 100.0, 100.0, 100.0]), 5,
                       1.33996),
}
