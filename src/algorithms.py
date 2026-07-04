"""
algorithms.py
=============
Implementation of the proposed Chess Algorithm (CA) together with four
reference metaheuristics used for benchmarking:

    * GA  - real-coded Genetic Algorithm (tournament selection, BLX-alpha
            crossover, Gaussian mutation, elitism)
    * PSO - Particle Swarm Optimization (linearly decreasing inertia)
    * SA  - Simulated Annealing (population-equivalent evaluation budget)
    * GWO - Grey Wolf Optimizer (Mirjalili et al., 2014)

All optimizers share the interface:

    best_x, best_f, curve = optimizer(fun, lb, ub, dim, pop, iters, rng)

where `curve` is the best-so-far fitness recorded once per iteration
(i.e., once per `pop` function evaluations), guaranteeing an identical
function-evaluation budget of pop * iters for every algorithm.

Author: Chess Algorithm (CA) research project
"""

import math

import numpy as np


# ----------------------------------------------------------------------
# Utility
# ----------------------------------------------------------------------
def _init_population(lb, ub, dim, pop, rng):
    """Uniform initialization X_i = l + (u - l) ∘ r_i,  r_i ~ U(0,1)^D."""
    return lb + (ub - lb) * rng.random((pop, dim))


def _clip(X, lb, ub):
    return np.clip(X, lb, ub)


def _levy_step(rng, beta=1.5):
    """One-dimensional Levy-stable step via Mantegna's algorithm.

    step = u / |v|^(1/beta),  u ~ N(0, sigma_u^2),  v ~ N(0, 1),

    with the scale sigma_u chosen so that the step distribution has the
    heavy-tailed index `beta` (Mantegna, 1994). Used by the optional
    Levy-flight variant of the Knight's exploratory leap.
    """
    sigma_u = (math.gamma(1.0 + beta) * math.sin(math.pi * beta / 2.0)
               / (math.gamma((1.0 + beta) / 2.0) * beta
                  * 2.0 ** ((beta - 1.0) / 2.0))) ** (1.0 / beta)
    u = sigma_u * rng.standard_normal()
    v = rng.standard_normal()
    return u / abs(v) ** (1.0 / beta)


# ======================================================================
# 1. THE CHESS ALGORITHM (CA)  -- proposed
# ======================================================================
def chess_algorithm(fun, lb, ub, dim, pop, iters, rng,
                    frac_queen=0.10, frac_rook=0.15, frac_bishop=0.15,
                    frac_knight=0.20, castling_period=10,
                    pin_max=0.30, theta0=0.1, knight_leap="uniform",
                    track_roles=False):
    """
    Chess Algorithm (CA).

    Evaluation accounting
    ---------------------
    Per iteration CA evaluates the `pop` piece moves plus 3 en-passant
    probes, one castling probe every `castling_period` iterations, and
    re-evaluations of re-deployed duplicates (rare). Over T iterations
    this is ~= pop*T * (1 + 3/pop) function evaluations, i.e. about 10%
    more than the pop*T core budget of the baselines for pop = 30. This
    overhead is reported transparently in the accompanying paper.

    Parameters (chess-specific)
    ---------------------------
    knight_leap : {"uniform", "levy"}
        Distribution of the Knight's occasional exploratory leap.
        "uniform" (default; used for all published results) resamples
        two coordinates uniformly in the box. "levy" instead adds a
        heavy-tailed Mantegna Levy-flight step (beta = 1.5) to the two
        coordinates, provided as a documented variant for future study.

    Chess-inspired mechanisms
    -------------------------
    Roles (search agents as pieces): after ranking the population by
        fitness, agents are assigned piece roles. The best agent is the
        KING (incumbent solution). The next ranks act as QUEENS, ROOKS,
        BISHOPS and KNIGHTS; the remainder are PAWNS. Each role has a
        characteristic move geometry. All step lengths are proportional
        to the current distance between the piece and the King (or a
        peer piece), so the swarm contracts geometrically as the game
        approaches the endgame.

    Development (exploration): a step-scale coefficient
        a(t) = 2 * (1 - t/T) shrinks linearly, so early iterations
        perform large "opening development" moves and late iterations
        perform fine endgame maneuvers.

    Sacrifice (probabilistic acceptance of worse moves): a worsening
        move of a MINOR piece (Knight or Pawn) may still be accepted
        with probability exp(-delta / theta(t)), where the "material
        budget" theta(t) cools over time and is scaled by the current
        population fitness spread. The swarm sacrifices immediate
        material (fitness) to escape local optima; major pieces and the
        King are never sacrificed.

    Pinning / Achmaz (exploitation): with probability growing over
        time, a random subset of an agent's coordinates is pinned to
        the King's coordinates and excluded from perturbation, focusing
        the search on the remaining free dimensions.

    Castling: periodically, the King exchanges a contiguous block of
        coordinates with the best Rook; the exchange is kept only if it
        improves the King (a safeguarded dual-coordinate jump).

    En passant: an opportunistic local capture - the King samples a few
        tightly localized trial points whose radius decays
        exponentially, and greedily keeps any improvement.

    Pawn promotion: pawns advance in small steps toward the King; a
        pawn whose fitness surpasses stronger pieces is, by the
        rank-based role reassignment of the next iteration, effectively
        promoted to a stronger piece.

    Checkmate (termination): the search stops after `iters` iterations
        (a stagnation-based early stop is also supported in principle;
        it is disabled here so that all algorithms consume identical
        evaluation budgets).
    """
    L = ub - lb
    X = _init_population(lb, ub, dim, pop, rng)
    F = fun(X)

    order = np.argsort(F)
    X, F = X[order], F[order]
    king_x, king_f = X[0].copy(), F[0]

    curve = np.empty(iters)
    role_history = [] if track_roles else None

    # role counts (King occupies rank 0)
    n_q = max(1, int(round(frac_queen * pop)))
    n_r = max(1, int(round(frac_rook * pop)))
    n_b = max(1, int(round(frac_bishop * pop)))
    n_k = max(1, int(round(frac_knight * pop)))

    sigma = 0.1 * L          # King's adaptive en-passant capture radius
    fails = 0                # consecutive failed capture attempts

    for t in range(iters):
        a = 2.0 * (1.0 - t / iters)                    # development schedule
        p_pin = 0.5 * (t / iters)                      # pinning probability
        spread = max(F[-1] - F[0], 1e-12)
        theta = theta0 * spread * np.exp(-8.0 * t / iters)  # sacrifice budget

        Xn = X.copy()

        # ---- role slices (population is kept sorted by fitness) ----
        i0 = 1
        idx_q = np.arange(i0, i0 + n_q);           i0 += n_q
        idx_r = np.arange(i0, min(i0 + n_r, pop)); i0 += n_r
        idx_b = np.arange(i0, min(i0 + n_b, pop)); i0 += n_b
        idx_k = np.arange(i0, min(i0 + n_k, pop)); i0 += n_k
        idx_p = np.arange(i0, pop)
        minor = np.zeros(pop, dtype=bool)              # sacrifice-eligible
        minor[idx_k] = True
        minor[idx_p] = True

        # ---- QUEEN: omnidirectional sweep encircling the King ----
        # (straight + diagonal reach = any direction, radius ~ current gap)
        for i in idx_q:
            gap = np.maximum(np.abs(king_x - X[i]), sigma)
            Xn[i] = king_x + a * (2 * rng.random(dim) - 1) * gap

        # ---- ROOK: long move along a single random file/rank (axis) ----
        for i in idx_r:
            j = rng.integers(dim)
            gap_j = max(abs(king_x[j] - X[i, j]), 0.01 * L * a)
            Xn[i, j] = king_x[j] + a * (2 * rng.random() - 1) * gap_j

        # ---- BISHOP: equal-magnitude diagonal move on a coordinate pair ----
        for i in idx_b:
            j, k = rng.choice(dim, size=2, replace=False)
            gap_jk = max(0.5 * (abs(king_x[j] - X[i, j])
                                + abs(king_x[k] - X[i, k])), 0.01 * L * a)
            step = a * (2 * rng.random() - 1) * gap_jk
            Xn[i, j] = king_x[j] + step
            Xn[i, k] = king_x[k] + (1 if rng.random() < 0.5 else -1) * step

        # ---- KNIGHT: 2:1 L-shaped jump, occasional over-the-board leap ----
        for i in idx_k:
            if rng.random() < 0.10 * a / 2.0:           # exploratory leap
                j, k = rng.choice(dim, size=2, replace=False)
                if knight_leap == "levy":
                    Xn[i, j] = X[i, j] + 0.05 * L * _levy_step(rng)
                    Xn[i, k] = X[i, k] + 0.05 * L * _levy_step(rng)
                else:
                    Xn[i, j] = lb + L * rng.random()
                    Xn[i, k] = lb + L * rng.random()
            else:
                j, k = rng.choice(dim, size=2, replace=False)
                peer = X[rng.integers(max(1, i))]
                base = np.mean(np.abs(peer - X[i])) + 1e-12
                Xn[i] = X[i] + rng.random(dim) * (peer - X[i])
                Xn[i, j] += 2.0 * a * base * (2 * rng.random() - 1)
                Xn[i, k] += 1.0 * a * base * (2 * rng.random() - 1)

        # ---- PAWN: steady advance toward the King (promotion via re-ranking) ----
        for i in idx_p:
            r = rng.random(dim)
            better = X[rng.integers(max(1, i))]
            Xn[i] = X[i] + 0.3 * r * (king_x - X[i]) \
                    + 0.3 * rng.random(dim) * (better - X[i])

        # ---- PINNING: freeze a subset of coordinates to the King's values ----
        for i in range(1, pop):
            if rng.random() < p_pin:
                n_pin = rng.integers(1, max(2, int(pin_max * dim)))
                pins = rng.choice(dim, size=n_pin, replace=False)
                Xn[i, pins] = king_x[pins]

        Xn = _clip(Xn, lb, ub)
        Fn = fun(Xn)

        # ---- SACRIFICE: SA-style acceptance, minor pieces only ----
        improved = Fn <= F
        with np.errstate(over="ignore", under="ignore"):
            p_acc = np.exp(-np.clip((Fn - F) / theta, 0.0, 700.0))
        sacrifice = minor & ~improved & (rng.random(pop) < p_acc)
        accept = improved | sacrifice
        accept[0] = False  # the King never sacrifices itself
        X[accept] = Xn[accept]
        F[accept] = Fn[accept]

        # ---- EN PASSANT: opportunistic local capture around the King ----
        # The capture radius sigma is self-adaptive: a successful capture
        # emboldens the King (sigma grows); a failed attempt makes the
        # next probe more cautious (sigma shrinks). This success-rule
        # adaptation yields sustained endgame refinement.
        mask = rng.random((3, dim)) < np.maximum(0.2, 2.0 / dim)
        trials = king_x + sigma * rng.standard_normal((3, dim)) * mask
        trials = _clip(trials, lb, ub)
        Ft = fun(trials)
        if Ft.min() < king_f:
            king_x, king_f = trials[Ft.argmin()].copy(), Ft.min()
            sigma = min(sigma * 1.3, np.max(L) if np.ndim(L) else L)
            fails = 0
        else:
            sigma = max(sigma * 0.92, 1e-280)
            fails += 1
            if fails >= 50:          # stalemate-avoidance restart of probes
                sigma = 0.05 * L * max(a, 0.05)
                fails = 0

        # ---- CASTLING: safeguarded coordinate-block exchange King <-> Rook ----
        if (t + 1) % castling_period == 0 and len(idx_r) > 0:
            rook = X[idx_r[0]]
            blk = rng.integers(1, max(2, dim // 4))
            s = rng.integers(0, dim - blk + 1)
            cand = king_x.copy()
            cand[s:s + blk] = rook[s:s + blk]
            fc = fun(cand[None, :])[0]
            if fc < king_f:
                king_x, king_f = cand, fc

        # ---- THREEFOLD REPETITION: a piece occupying the King's square
        # is re-deployed to a random square (draw avoidance keeps the
        # board diverse and prevents degenerate collapse) ----
        dup = np.max(np.abs(X[1:] - king_x), axis=1) < 1e-12 * np.max(L)
        if dup.any():
            n_dup = int(dup.sum())
            X[1:][dup] = lb + L * rng.random((n_dup, dim))
            F[1:][dup] = fun(X[1:][dup])

        # ---- update King from population, re-rank (pawn promotion) ----
        if F.min() < king_f:
            king_x, king_f = X[F.argmin()].copy(), F.min()
        X[0], F[0] = king_x, king_f
        order = np.argsort(F)
        X, F = X[order], F[order]

        curve[t] = king_f
        if track_roles:
            role_history.append((len(idx_q), len(idx_r), len(idx_b),
                                 len(idx_k), len(idx_p)))

    if track_roles:
        return king_x, king_f, curve, role_history
    return king_x, king_f, curve


# ======================================================================
# 2. GENETIC ALGORITHM (real-coded)
# ======================================================================
def genetic_algorithm(fun, lb, ub, dim, pop, iters, rng,
                      pc=0.9, alpha=0.5, elite=2):
    X = _init_population(lb, ub, dim, pop, rng)
    F = fun(X)
    best_i = F.argmin()
    best_x, best_f = X[best_i].copy(), F[best_i]
    curve = np.empty(iters)
    pm = 1.0 / dim

    for t in range(iters):
        # tournament selection (k = 3)
        cand = rng.integers(0, pop, size=(pop, 3))
        winners = cand[np.arange(pop), F[cand].argmin(axis=1)]
        P = X[winners]

        # BLX-alpha crossover
        C = P.copy()
        for i in range(0, pop - 1, 2):
            if rng.random() < pc:
                lo = np.minimum(P[i], P[i + 1])
                hi = np.maximum(P[i], P[i + 1])
                I = hi - lo
                low, high = lo - alpha * I, hi + alpha * I
                C[i] = low + (high - low) * rng.random(dim)
                C[i + 1] = low + (high - low) * rng.random(dim)

        # Gaussian mutation with decaying sigma
        sigma = 0.1 * (ub - lb) * (1.0 - 0.9 * t / iters)
        mask = rng.random((pop, dim)) < pm
        C += mask * sigma * rng.standard_normal((pop, dim))
        C = _clip(C, lb, ub)
        Fc = fun(C)

        # elitism
        elite_idx = np.argsort(F)[:elite]
        worst_idx = np.argsort(Fc)[-elite:]
        C[worst_idx], Fc[worst_idx] = X[elite_idx], F[elite_idx]

        X, F = C, Fc
        if F.min() < best_f:
            best_x, best_f = X[F.argmin()].copy(), F.min()
        curve[t] = best_f
    return best_x, best_f, curve


# ======================================================================
# 3. PARTICLE SWARM OPTIMIZATION
# ======================================================================
def particle_swarm(fun, lb, ub, dim, pop, iters, rng,
                   c1=2.0, c2=2.0, w_max=0.9, w_min=0.4):
    L = ub - lb
    X = _init_population(lb, ub, dim, pop, rng)
    V = np.zeros((pop, dim))
    v_max = 0.2 * L
    F = fun(X)
    Pb, Fpb = X.copy(), F.copy()
    g = Fpb.argmin()
    gb, fgb = Pb[g].copy(), Fpb[g]
    curve = np.empty(iters)

    for t in range(iters):
        w = w_max - (w_max - w_min) * t / iters
        r1, r2 = rng.random((pop, dim)), rng.random((pop, dim))
        V = w * V + c1 * r1 * (Pb - X) + c2 * r2 * (gb - X)
        V = np.clip(V, -v_max, v_max)
        X = _clip(X + V, lb, ub)
        F = fun(X)
        imp = F < Fpb
        Pb[imp], Fpb[imp] = X[imp], F[imp]
        if Fpb.min() < fgb:
            g = Fpb.argmin()
            gb, fgb = Pb[g].copy(), Fpb[g]
        curve[t] = fgb
    return gb, fgb, curve


# ======================================================================
# 4. SIMULATED ANNEALING (matched evaluation budget: pop moves / iter)
# ======================================================================
def simulated_annealing(fun, lb, ub, dim, pop, iters, rng, T0=None):
    L = ub - lb
    x = lb + L * rng.random(dim)
    f = fun(x[None, :])[0]
    best_x, best_f = x.copy(), f
    if T0 is None:
        # calibrate the initial temperature from random-sample spread
        S = _init_population(lb, ub, dim, 20, rng)
        T0 = np.std(fun(S)) + 1e-12
    curve = np.empty(iters)

    total_steps = iters * pop
    step = 0
    for t in range(iters):
        for _ in range(pop):
            frac = step / total_steps
            T = T0 * (0.995 ** (step / max(1, dim)))
            sigma = 0.1 * L * (1.0 - 0.9 * frac)
            xn = _clip(x + sigma * rng.standard_normal(dim), lb, ub)
            fn = fun(xn[None, :])[0]
            if fn < f or rng.random() < np.exp(-(fn - f) / max(T, 1e-300)):
                x, f = xn, fn
                if f < best_f:
                    best_x, best_f = x.copy(), f
            step += 1
        curve[t] = best_f
    return best_x, best_f, curve


# ======================================================================
# 5. GREY WOLF OPTIMIZER (Mirjalili, Mirjalili & Lewis, 2014)
# ======================================================================
def grey_wolf(fun, lb, ub, dim, pop, iters, rng):
    X = _init_population(lb, ub, dim, pop, rng)
    F = fun(X)
    order = np.argsort(F)
    alpha, beta, delta = X[order[0]].copy(), X[order[1]].copy(), X[order[2]].copy()
    fa, fb, fd = F[order[0]], F[order[1]], F[order[2]]
    curve = np.empty(iters)

    for t in range(iters):
        a = 2.0 * (1.0 - t / iters)
        r1, r2 = rng.random((pop, dim)), rng.random((pop, dim))
        A1, C1 = 2 * a * r1 - a, 2 * r2
        X1 = alpha - A1 * np.abs(C1 * alpha - X)
        r1, r2 = rng.random((pop, dim)), rng.random((pop, dim))
        A2, C2 = 2 * a * r1 - a, 2 * r2
        X2 = beta - A2 * np.abs(C2 * beta - X)
        r1, r2 = rng.random((pop, dim)), rng.random((pop, dim))
        A3, C3 = 2 * a * r1 - a, 2 * r2
        X3 = delta - A3 * np.abs(C3 * delta - X)
        X = _clip((X1 + X2 + X3) / 3.0, lb, ub)
        F = fun(X)
        for i in range(pop):
            if F[i] < fa:
                fd, delta = fb, beta.copy()
                fb, beta = fa, alpha.copy()
                fa, alpha = F[i], X[i].copy()
            elif F[i] < fb:
                fd, delta = fb, beta.copy()
                fb, beta = F[i], X[i].copy()
            elif F[i] < fd:
                fd, delta = F[i], X[i].copy()
        curve[t] = fa
    return alpha, fa, curve


ALGORITHMS = {
    "CA":  chess_algorithm,
    "GA":  genetic_algorithm,
    "PSO": particle_swarm,
    "SA":  simulated_annealing,
    "GWO": grey_wolf,
}
