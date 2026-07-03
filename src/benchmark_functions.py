"""
benchmark_functions.py
======================
Standard continuous benchmark functions for evaluating metaheuristic
optimization algorithms. All functions are implemented in vectorized
NumPy form and accept a population matrix X of shape (N, D), returning
a fitness vector of shape (N,).

Global minimum of every function below is f* = 0 (Schwefel is shifted
so that its known optimum maps to zero as well).

Author: Chess Algorithm (CA) research project
"""

import numpy as np


def sphere(X):
    """F1 - Sphere. Unimodal, separable. Domain [-100, 100]^D."""
    return np.sum(X ** 2, axis=1)


def rosenbrock(X):
    """F2 - Rosenbrock. Unimodal, non-separable valley. Domain [-30, 30]^D."""
    return np.sum(100.0 * (X[:, 1:] - X[:, :-1] ** 2) ** 2
                  + (X[:, :-1] - 1.0) ** 2, axis=1)


def rastrigin(X):
    """F3 - Rastrigin. Highly multimodal, separable. Domain [-5.12, 5.12]^D."""
    D = X.shape[1]
    return 10.0 * D + np.sum(X ** 2 - 10.0 * np.cos(2 * np.pi * X), axis=1)


def griewank(X):
    """F4 - Griewank. Multimodal, non-separable. Domain [-600, 600]^D."""
    D = X.shape[1]
    idx = np.sqrt(np.arange(1, D + 1))
    return (np.sum(X ** 2, axis=1) / 4000.0
            - np.prod(np.cos(X / idx), axis=1) + 1.0)


def ackley(X):
    """F5 - Ackley. Multimodal with a nearly flat outer region. Domain [-32, 32]^D."""
    D = X.shape[1]
    s1 = np.sum(X ** 2, axis=1)
    s2 = np.sum(np.cos(2 * np.pi * X), axis=1)
    return (-20.0 * np.exp(-0.2 * np.sqrt(s1 / D))
            - np.exp(s2 / D) + 20.0 + np.e)


def schwefel_222(X):
    """F6 - Schwefel 2.22. Unimodal, non-separable. Domain [-10, 10]^D."""
    absX = np.abs(X)
    return np.sum(absX, axis=1) + np.prod(absX, axis=1)


# Registry: name -> (callable, lower bound, upper bound, formal label)
BENCHMARKS = {
    "F1_Sphere":       (sphere,       -100.0, 100.0, "Sphere"),
    "F2_Rosenbrock":   (rosenbrock,    -30.0,  30.0, "Rosenbrock"),
    "F3_Rastrigin":    (rastrigin,    -5.12,  5.12, "Rastrigin"),
    "F4_Griewank":     (griewank,     -600.0, 600.0, "Griewank"),
    "F5_Ackley":       (ackley,       -32.0,  32.0, "Ackley"),
    "F6_Schwefel222":  (schwefel_222,  -10.0,  10.0, "Schwefel 2.22"),
}
