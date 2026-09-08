"""
make_method_figures.py
======================
Mechanism figures for the proposed-method section.

The geometry panels are not drawn by hand: every candidate point is
produced by evaluating the manuscript's own equations in a
two-dimensional section with a fixed seed, using the same formulas as
`src/algorithms.py`.  The schedule panel of the state-machine figure
reprints the values of the manuscript's phase-schedule table.

    fig_architecture()  -> figures/ca_architecture.png
    fig_roles()         -> figures/ca_roles.png
    fig_tactics()       -> figures/ca_tactics.png
    fig_statemachine()  -> figures/ca_statemachine.png

Equation and section numbers printed inside the figures are read from
paper.qmd at drawing time (figstyle.eq / eqs / sec), so they cannot
drift from the rendered manuscript.

Usage:  python src/make_method_figures.py
"""

import os

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from figstyle import (CAND, ELITE, EXPLORE, FILL, FILL2, FILL3, INK,  # noqa: E402
                      KING, MUTED, arrow, blank, box, eq, eqs, label,
                      save, sec, tbl, use_style)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGURES = os.path.join(ROOT, "figures")

SEED = 20260908
A_T = 1.0          # development coefficient a(t) used for the sketches
L = np.array([10.0, 10.0])


# --------------------------------------------------------------------
# Figure 3 -- one iteration of CA
# --------------------------------------------------------------------
def fig_architecture():
    use_style()
    fig = plt.figure(figsize=(7.4, 4.9))
    ax = blank(fig.add_axes([0, 0, 1, 1]))

    w, h, dy = 0.250, 0.100, 0.145
    col1, col2, col3 = 0.035, 0.375, 0.715
    ys = [0.055 + k * dy for k in range(6)]          # bottom to top

    def b(x, y, text, fc=FILL, fs=7.3, hh=h):
        return box(ax, x, y, w, hh, text, fc=fc, fontsize=fs)

    def down(x, y):
        arrow(ax, (x + w / 2, y), (x + w / 2, y - (dy - h)), lw=1.0)

    # ---- left column: the population pipeline
    b(col1, ys[5], "population $\\mathbf{X}^{(t)}$\n$N$ agents",
      fc=FILL2)
    b(col1, ys[4], "rank and assign roles\nK | Q | R | B | N | P "
                   f"({eq('eq-roles')})")
    b(col1, ys[3], "role movement operators\n"
                   f"({eqs('eq-queen', 'eq-pawn')})")
    b(col1, ys[2], "strategic mechanisms\npinning, interference, fork")
    b(col1, ys[1], "clip to bounds; evaluate")
    b(col1, ys[0], "accept improvements; worse\nminor pieces with "
                   "$e^{-\\Delta/\\theta}$ "
                   f"({eq('eq-sacrifice')})")
    for y in ys[1:]:
        down(col1, y)

    # ---- middle column: the adaptive controller
    b(col2, 0.760, "read the position "
                   f"({eqs('eq-divergence', 'eq-fifty-move')})\n"
                   "$\\tilde d$ | $\\alpha$ | $\\varepsilon$ | $s$",
      fc=FILL2, hh=0.12)
    b(col2, 0.575, f"select the phase ({eq('eq-phase')})\n"
                   "Opening | Middlegame |\nClosed | Endgame",
      hh=0.135)
    b(col2, 0.390, "phase-conditioned rates\n"
                   f"({tbl('tbl-phase-schedule')})", hh=0.115)
    b(col2, 0.205, f"overlays\nzugzwang ({eq('eq-zugzwang')})\n"
                   "blockade at $s\\geq 25$", hh=0.135)
    for y0, y1 in ((0.760, 0.710), (0.575, 0.525), (0.390, 0.340)):
        arrow(ax, (col2 + w / 2, y0), (col2 + w / 2, y1), lw=1.0,
              color=MUTED)

    # ---- right column: the King's own moves
    b(col3, ys[5], "King's local search", fc=FILL2)
    b(col3, ys[4], "en passant: 3 masked\nGaussian trials "
                   f"({eq('eq-enpassant')})")
    b(col3, ys[3], "council / discovered\nattack probe "
                   f"({eqs('eq-discovered', 'eq-council')})")
    b(col3, ys[2], "castling every $c=10$\niterations")
    b(col3, ys[1], "windmill extension\n"
                   f"(Endgame, {eq('eq-windmill')})")
    b(col3, ys[0], "update King; re-rank\n(pawn promotion)")
    for y in ys[1:]:
        down(col3, y)

    # ---- population -> King's block, and the iteration loop
    arrow(ax, (col1 + w, ys[0] + h / 2), (col3, ys[0] + h / 2), lw=1.0,
          connection="arc3,rad=-0.10")
    for p1, p2 in (((col3 + w, ys[0] + h / 2), (0.985, ys[0] + h / 2)),
                   ((0.985, ys[0] + h / 2), (0.985, 0.935)),
                   ((0.985, 0.935), (col1 + w / 2, 0.935))):
        arrow(ax, p1, p2, lw=1.0, style="-")
    arrow(ax, (col1 + w / 2, 0.935), (col1 + w / 2, ys[5] + h), lw=1.0)

    # ---- control edges
    ctrl = dict(ls=(0, (2.5, 1.5)), color=EXPLORE, lw=0.95)
    arrow(ax, (col1 + w, ys[1] + h / 2), (col2, 0.790), **ctrl)
    arrow(ax, (col2, 0.440), (col1 + w, ys[3] + h / 2), **ctrl)
    arrow(ax, (col2 + w, 0.440), (col3, ys[4] + h / 2), **ctrl)
    arrow(ax, (col2 + w, 0.265), (col3, ys[0] + h / 2), **ctrl)

    label(ax, 0.035, 0.975, "solid: population and King flow      "
                            "dashed: control signals read and written "
                            "by the adaptive layer",
          fontsize=7.6, color=MUTED, ha="left")
    label(ax, 0.5, 0.022, "one iteration; repeated until $t=T$ "
                          "(checkmate)", fontsize=7.8, color=INK)
    save(fig, os.path.join(FIGURES, "ca_architecture.png"))



# --------------------------------------------------------------------
# Figure 4 -- role-based search geometry
# --------------------------------------------------------------------
def _role_samples(rng, n=45):
    """Candidates produced by each role operator in a 2-D section,
    evaluated straight from the movement equations of the
    manuscript."""
    K = np.array([0.0, 0.0])
    X = np.array([2.6, -1.9])          # the moving agent
    P = np.array([-1.4, 1.7])          # better-ranked peer
    sigma = np.array([0.35, 0.35])     # King's capture radius
    out = {}

    # Queen: omnidirectional sweep (eq-queen)
    r = rng.random((n, 2))
    out["Queen"] = K + A_T * (2 * r - 1) * np.maximum(np.abs(K - X),
                                                      sigma)
    # Rook (eq-rook): one random axis moves, the other is kept
    cand = np.tile(X, (n, 1))
    j = rng.integers(0, 2, n)
    rr = rng.random(n)
    for i in range(n):
        cand[i, j[i]] = K[j[i]] + A_T * (2 * rr[i] - 1) * max(
            abs(K[j[i]] - X[j[i]]), 0.01 * L[j[i]] * A_T)
    out["Rook"] = cand
    # Bishop (eq-bishop): equal-magnitude step on two axes
    rr = rng.random(n)
    d = A_T * (2 * rr - 1) * max(
        0.5 * (abs(K[0] - X[0]) + abs(K[1] - X[1])),
        0.01 * L[0] * A_T)
    sign = rng.choice([-1.0, 1.0], n)
    out["Bishop"] = np.column_stack([K[0] + d, K[1] + sign * d])
    # Knight (eq-knight): drift to a better peer plus a 2:1 jump
    r = rng.random((n, 2))
    base = X + r * (P - X)
    beta = np.mean(np.abs(P - X))
    jump = np.zeros((n, 2))
    jump[:, 0] = 2 * A_T * beta * (2 * rng.random(n) - 1)
    jump[:, 1] = 1 * A_T * beta * (2 * rng.random(n) - 1)
    out["Knight"] = base + jump
    # Pawn: steady advance (eq-pawn)
    r, r2 = rng.random((n, 2)), rng.random((n, 2))
    out["Pawn"] = X + 0.3 * r * (K - X) + 0.3 * r2 * (P - X)
    return K, X, P, out


def fig_roles():
    use_style()
    rng = np.random.default_rng(SEED)
    K, X, P, samples = _role_samples(rng)

    fig = plt.figure(figsize=(7.4, 4.0))
    axtop = fig.add_axes([0.055, 0.620, 0.90, 0.150])
    blank(axtop, (0, 1), (0, 1))

    # ---- (a) the rank partition
    fracs = [("King", 1 / 30), ("Queens", 0.10), ("Rooks", 0.15),
             ("Bishops", 0.15), ("Knights", 0.20), ("Pawns", 0.3667)]
    cols = [KING, "#93c5fd", "#a7f3d0", "#fbcfe8", "#ddd6fe", "#fde68a"]
    x = 0.0
    for (name, f), c in zip(fracs, cols):
        axtop.add_patch(plt.Rectangle((x, 0.18), f, 0.34, facecolor=c,
                                      edgecolor=INK, lw=0.7))
        axtop.text(x + f / 2, 0.35, name, ha="center", va="center",
                   fontsize=7.2,
                   color="white" if name == "King" else INK)
        if name != "King":
            axtop.text(x + f / 2, 0.03, f"{f:.2f}".lstrip("0"),
                       ha="center", fontsize=6.8, color=MUTED)
        x += f
    axtop.annotate("", xy=(1.0, 0.72), xytext=(0.0, 0.72),
                   arrowprops=dict(arrowstyle="-|>", color=MUTED,
                                   lw=0.9))
    axtop.text(0.5, 0.90, "population sorted by fitness "
                          "(re-ranked every iteration: promotion)",
               ha="center", fontsize=7.6, color=MUTED)
    axtop.text(0.0, 1.14, "(a)  rank-based role assignment "
               f"({tbl('tbl-params')})",
               fontsize=8.4, ha="left", weight="bold")

    # ---- (b)-(f) move geometry
    order = [("Queen", "(b)", eq("eq-queen"), "exploration", EXPLORE),
             ("Rook", "(c)", eq("eq-rook"), "axis-aligned", ELITE),
             ("Bishop", "(d)", eq("eq-bishop"), "axis-pair", ELITE),
             ("Knight", "(e)", eq("eq-knight"), "exploration", EXPLORE),
             ("Pawn", "(f)", eq("eq-pawn"), "exploitation", CAND)]
    for k, (name, tag, eqlab, role, rcol) in enumerate(order):
        ax = fig.add_axes([0.055 + k * 0.191, 0.195, 0.163,
                           0.163 * 7.4 / 4.0])
        pts = samples[name]
        ax.scatter(pts[:, 0], pts[:, 1], s=7, color=CAND, alpha=0.75,
                   linewidths=0, zorder=3, label="candidates")
        ax.plot(*K, "o", color=KING, ms=6, zorder=5, label="King")
        ax.plot(*X, "o", color=MUTED, ms=4.5, zorder=5, label="agent")
        if name in ("Knight", "Pawn"):
            ax.plot(*P, "o", color=ELITE, ms=4.5, zorder=5,
                    label="better-ranked peer")
        ax.set_xlim(-5.2, 5.2)
        ax.set_ylim(-5.2, 5.2)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_aspect("equal")
        for s in ax.spines.values():
            s.set_visible(True)
            s.set_linewidth(0.7)
            s.set_color(FILL3)
        ax.set_title(f"{tag}  {name}   ({eqlab})", fontsize=8.2,
                     pad=4)
        ax.text(0.5, -0.075, role, transform=ax.transAxes, ha="center",
                fontsize=7.4, color=rcol)

    handles = [plt.Line2D([], [], marker="o", ls="", color=KING,
                          ms=5, label="King $\\mathbf{K}$"),
               plt.Line2D([], [], marker="o", ls="", color=MUTED,
                          ms=4.5, label="moving agent $\\mathbf{X}_i$"),
               plt.Line2D([], [], marker="o", ls="", color=ELITE,
                          ms=4.5,
                          label="better-ranked peer $\\mathbf{P}$"),
               plt.Line2D([], [], marker="o", ls="", color=CAND,
                          ms=4.0, label="candidates $\\mathbf{X}_i'$ "
                                        "(45 draws)")]
    fig.legend(handles=handles, loc="lower center", ncol=4,
               frameon=False, fontsize=7.8, bbox_to_anchor=(0.5, 0.015))
    save(fig, os.path.join(FIGURES, "ca_roles.png"))


# --------------------------------------------------------------------
# Figure 5 -- tactical operator geometry
# --------------------------------------------------------------------
def fig_tactics():
    use_style()
    rng = np.random.default_rng(SEED + 1)
    fig, axes = plt.subplots(2, 3, figsize=(7.4, 4.6))
    K = np.array([0.0, 0.0])

    def frame(ax, tag, title, eqlab):
        ax.set_xlim(-3.4, 3.4)
        ax.set_ylim(-3.4, 3.4)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_aspect("equal")
        for s in ax.spines.values():
            s.set_visible(True)
            s.set_linewidth(0.7)
            s.set_color(FILL3)
        ax.set_title(f"{tag}  {title}   ({eqlab})", fontsize=8.4,
                     pad=4)

    # ---- (a) en passant: masked Gaussian trials + success rule
    ax = axes[0, 0]
    sigma = 1.1
    for rad, ls, c, txt in ((sigma, "--", MUTED, r"$\sigma$"),
                            (1.3 * sigma, ":", ELITE,
                             r"$1.3\,\sigma$ after a capture"),
                            (0.92 * sigma, ":", CAND,
                             r"$0.92\,\sigma$ after a failure")):
        th = np.linspace(0, 2 * np.pi, 200)
        ax.plot(rad * np.cos(th), rad * np.sin(th), ls=ls, lw=0.9,
                color=c)
    # three representative draws of the masked Gaussian trial of
    # eq-enpassant, scaled so all three stay in the plotted box
    dirs = np.array([[0.62, 0.78], [-1.0, 0.0], [0.34, -0.94]])
    trials = K + dirs * np.array([0.85, 1.05, 0.55])[:, None] * sigma
    trials[1, 1] = K[1]          # a masked coordinate stays put
    for t in trials:
        arrow(ax, K, t, color=CAND, lw=0.9)
        ax.plot(*t, "o", color=CAND, ms=4, zorder=5)
    ax.plot(*K, "o", color=KING, ms=6, zorder=6)
    ax.text(0.02, 0.03, "3 trials, coordinates masked\nwith prob. "
                        r"$\max(0.2,\,2/D)$",
            transform=ax.transAxes, fontsize=6.9, color=MUTED)
    for k, (txt, col) in enumerate(
            ((r"$\sigma$ now", MUTED),
             (r"$\times 1.3$ after a capture", ELITE),
             (r"$\times 0.92$ after a failure", CAND))):
        ax.text(0.035, 0.955 - 0.072 * k, txt, transform=ax.transAxes,
                fontsize=6.6, color=col, ha="left", va="top")
    frame(ax, "(a)", "En passant", eq("eq-enpassant"))

    # ---- (b) knight's fork: difference vector of two better peers
    ax = axes[0, 1]
    Xi = np.array([-2.2, -2.0])
    Xa, Xb = np.array([1.6, 1.5]), np.array([-0.4, 2.2])
    r = np.array([0.45, 0.45])       # one representative draw
    cand = Xi + r * (K - Xi) + 0.8 * (Xa - Xb)
    ax.plot(*Xi, "o", color=MUTED, ms=4.5, zorder=5)
    ax.plot(*Xa, "o", color=ELITE, ms=4.5, zorder=5)
    ax.plot(*Xb, "o", color=ELITE, ms=4.5, zorder=5)
    ax.plot(*K, "o", color=KING, ms=6, zorder=6)
    arrow(ax, Xb, Xa, color=ELITE, lw=1.0, ls=(0, (3, 1.5)))
    arrow(ax, Xi, Xi + r * (K - Xi), color=MUTED, lw=1.0)
    arrow(ax, Xi + r * (K - Xi), cand, color=CAND, lw=1.1)
    ax.plot(*cand, "o", color=CAND, ms=4.5, zorder=6)
    ax.text(Xa[0] - 0.15, Xa[1] + 0.25, r"$\mathbf{X}_a$", fontsize=7.2,
            color=ELITE)
    ax.text(Xb[0] - 0.55, Xb[1] + 0.25, r"$\mathbf{X}_b$", fontsize=7.2,
            color=ELITE)
    ax.text(0.02, 0.03, r"drift to $\mathbf{K}$ $+$ "
                        r"$0.8(\mathbf{X}_a-\mathbf{X}_b)$",
            transform=ax.transAxes, fontsize=6.9, color=MUTED)
    frame(ax, "(b)", "Knight's fork", eq("eq-fork"))

    # ---- (c) royal council: reflection away from the elite midpoint
    ax = axes[0, 2]
    Q1, R1 = np.array([-1.9, 1.0]), np.array([-1.1, -2.1])
    c = 0.5 * (Q1 + R1)
    u = 0.75
    Y = K + 1.5 * u * (K - c)
    ax.plot(*Q1, "o", color=ELITE, ms=4.5, zorder=5)
    ax.plot(*R1, "o", color=ELITE, ms=4.5, zorder=5)
    ax.plot(*c, "s", color=MUTED, ms=4.5, zorder=5)
    ax.plot(*K, "o", color=KING, ms=6, zorder=6)
    ax.plot([Q1[0], R1[0]], [Q1[1], R1[1]], ls=(0, (3, 1.5)), lw=0.9,
            color=ELITE)
    arrow(ax, c, Y, color=CAND, lw=1.1)
    ax.plot(*Y, "o", color=CAND, ms=4.5, zorder=6)
    ax.text(Q1[0] - 0.2, Q1[1] + 0.3, r"$\mathbf{X}_{Q_1}$",
            fontsize=7.2, color=ELITE)
    ax.text(R1[0] + 0.25, R1[1] - 0.35, r"$\mathbf{X}_{R_1}$",
            fontsize=7.2, color=ELITE)
    ax.text(c[0] - 0.9, c[1] + 0.25, r"$\mathbf{c}$", fontsize=7.2,
            color=MUTED)
    ax.text(0.02, 0.955, "reflect the King away\nfrom the elite midpoint",
            transform=ax.transAxes, fontsize=6.9, color=MUTED, va="top")
    frame(ax, "(c)", "Royal council", eq("eq-council"))

    # ---- (d) Novotny interference: convex recombination
    ax = axes[1, 0]
    Xa, Xb = np.array([-2.3, -1.4]), np.array([2.2, 1.9])
    ax.plot([Xa[0], Xb[0]], [Xa[1], Xb[1]], ls=(0, (3, 1.5)), lw=0.9,
            color=ELITE)
    ax.plot(*Xa, "o", color=ELITE, ms=4.5, zorder=5)
    ax.plot(*Xb, "o", color=ELITE, ms=4.5, zorder=5)
    for beta in rng.uniform(0.3, 0.7, 6):
        p = beta * Xa + (1 - beta) * Xb + 0.02 * A_T * L * rng.normal(
            size=2)
        ax.plot(*p, "o", color=CAND, ms=4, zorder=6)
    ax.plot(*K, "o", color=KING, ms=6, zorder=6)
    ax.text(Xa[0] - 0.1, Xa[1] - 0.65, r"$\mathbf{X}_a$", fontsize=7.2,
            color=ELITE)
    ax.text(Xb[0] - 0.3, Xb[1] + 0.35, r"$\mathbf{X}_b$", fontsize=7.2,
            color=ELITE)
    ax.text(0.02, 0.03, r"$\beta\sim\mathcal{U}(0.3,0.7)$ on the"
                        "\nsegment; rotation-invariant",
            transform=ax.transAxes, fontsize=6.9, color=MUTED)
    frame(ax, "(d)", "Novotny interference", eq("eq-interference"))

    # ---- (e) discovered attack: extrapolation through the King
    ax = axes[1, 1]
    Xe = np.array([-2.0, -1.5])
    ax.plot(*Xe, "o", color=ELITE, ms=4.5, zorder=5)
    ax.plot(*K, "o", color=KING, ms=6, zorder=6)
    for u in (1.2, 1.7, 2.2):
        Y = Xe + u * (K - Xe)
        ax.plot(*Y, "o", color=CAND, ms=4, zorder=6)
    arrow(ax, Xe, Xe + 2.2 * (K - Xe), color=CAND, lw=1.0)
    ax.text(Xe[0] - 0.1, Xe[1] - 0.7, r"$\mathbf{X}_e$", fontsize=7.2,
            color=ELITE)
    ax.text(0.02, 0.03, r"$u\sim\mathcal{U}(1.2,2.2)$: probes the far"
                        "\nside of the incumbent",
            transform=ax.transAxes, fontsize=6.9, color=MUTED)
    frame(ax, "(e)", "Discovered attack", eq("eq-discovered"))

    # ---- legend panel
    ax = axes[1, 2]
    ax.axis("off")
    handles = [
        plt.Line2D([], [], marker="o", ls="", color=KING, ms=6,
                   label="King $\\mathbf{K}$ (incumbent)"),
        plt.Line2D([], [], marker="o", ls="", color=ELITE, ms=5,
                   label="better-ranked / elite piece"),
        plt.Line2D([], [], marker="o", ls="", color=MUTED, ms=5,
                   label="moving agent, elite midpoint"),
        plt.Line2D([], [], marker="o", ls="", color=CAND, ms=5,
                   label="candidate produced by the operator"),
        plt.Line2D([], [], color=CAND, lw=1.1, label="candidate step"),
        plt.Line2D([], [], color=ELITE, lw=0.9, ls=(0, (3, 1.5)),
                   label="elite structure the operator exploits"),
    ]
    ax.legend(handles=handles, loc="center", frameon=False,
              fontsize=7.6)
    ax.text(0.5, 0.045, "Each panel is a two-dimensional section;\n"
                        "points are produced by the equation named in\n"
                        "the panel title, with a fixed seed.",
            transform=ax.transAxes, ha="center", fontsize=6.9,
            color=MUTED)
    fig.tight_layout(w_pad=1.2, h_pad=1.4)
    save(fig, os.path.join(FIGURES, "ca_tactics.png"))


# --------------------------------------------------------------------
# Figure 6 -- adaptive tactical state machine
# --------------------------------------------------------------------
# values reproduced from the manuscript's phase-schedule table; the
# validation script checks this block against the table in paper.qmd
SCHEDULE = {
    "Opening":    ["0", "2.0", "0", "0", "0.30", "0.30"],
    "Middlegame": [r"$0.5\phi$", "1.0", "0.5", "0", "0.15", "0.30"],
    "Closed":     ["0", "2.0", "0.5", "0.15", "0.15", "0.30"],
    "Endgame":    [r"$0.1{+}0.75\phi$", "0.5", "0.7", "0.15", "0",
                   "0.45"],
}
SCHED_NUM = {          # numeric value used only for the cell shading
    "Opening":    [0.0, 1.0, 0.0, 0.0, 0.30, 0.30],
    "Middlegame": [0.25, 0.5, 0.5, 0.0, 0.15, 0.30],
    "Closed":     [0.0, 1.0, 0.5, 0.15, 0.15, 0.30],
    "Endgame":    [0.48, 0.25, 0.7, 0.15, 0.0, 0.45],
}
SCHED_COLS = [r"$p_{\mathrm{pin}}$", "leap mult.", r"$p_{\mathrm{c}}$",
              r"$p_{\mathrm{DA}}$", r"$p_{\mathrm{intf}}$",
              "pawn gain"]


def fig_statemachine():
    use_style()
    fig = plt.figure(figsize=(7.4, 5.1))
    ax = blank(fig.add_axes([0, 0, 1, 1]))

    # ---- inputs
    inputs = [
        (r"divergence $\tilde d(t)$" f"\n({eq('eq-divergence')})",
         0.030),
        (r"initiative $\alpha(t)$" f"\n({eq('eq-acceptance')})", 0.265),
        (r"local-search success $\varepsilon(t)$"
         f"\n({eq('eq-epsilon')})", 0.500),
        (r"stagnation $s(t)$" f"\n({eq('eq-fifty-move')})", 0.735),
    ]
    for text, x in inputs:
        box(ax, x, 0.855, 0.235, 0.095, text, fc=FILL2, fontsize=7.6)
        arrow(ax, (x + 0.1175, 0.855), (0.5, 0.805), lw=0.85,
              color=MUTED)

    box(ax, 0.315, 0.705, 0.370, 0.098,
        "adaptive controller\n"
        r"read once per iteration, $\lambda=0.8$ smoothing",
        fc=FILL3, fontsize=8.0)

    # ---- phases
    phases = [
        ("Opening", r"$\tilde d > 0.22$", 0.020),
        ("Middlegame", r"$0.045 < \tilde d \leq 0.22$", 0.263),
        ("Closed", r"$\tilde d \leq 0.045$, $\phi \leq 0.5$", 0.506),
        ("Endgame", r"$\tilde d \leq 0.045$, $\phi > 0.5$", 0.749),
    ]
    for name, cond, x in phases:
        box(ax, x, 0.545, 0.231, 0.100, f"{name}\n{cond}", fc=FILL,
            fontsize=7.8)
        arrow(ax, (0.5, 0.705), (x + 0.1155, 0.647), lw=0.85,
              color=MUTED)
    label(ax, 0.022, 0.672, f"phase selection ({eq('eq-phase')})", fontsize=7.4,
          color=MUTED, ha="left")

    # ---- overlays
    box(ax, 0.020, 0.415, 0.455, 0.078,
        f"zugzwang overlay, any phase ({eq('eq-zugzwang')}): " r"$\phi>0.2$, "
        r"$\alpha<0.04$, $\varepsilon<0.05$" "\n"
        r"$\Rightarrow$ halve $a(t)$ for one iteration",
        fc=FILL2, fontsize=7.4)
    box(ax, 0.525, 0.415, 0.455, 0.078,
        f"blockade response, any phase ({sec('sec-blockade')}): "
        r"$s \geq 25$" "\n"
        "pawn break, King's march, reheated sacrifice budget",
        fc=FILL2, fontsize=7.4)
    # the two overlays act independently of the phase, so their control
    # edges leave the controller and pass through the gaps between the
    # phase boxes rather than out of any one phase
    ctrl = dict(ls=(0, (2.5, 1.5)), color=EXPLORE, lw=0.9)
    for x_gap, x_in in ((0.257, 0.315), (0.743, 0.685)):
        arrow(ax, (x_in, 0.710), (x_gap, 0.640), style="-", **ctrl)
        arrow(ax, (x_gap, 0.640), (x_gap, 0.496), **ctrl)

    # ---- schedule strip
    label(ax, 0.5, 0.368,
          "phase-conditioned operator rates "
          f"({tbl('tbl-phase-schedule')})", fontsize=8.2,
          weight="bold")
    x0, y0, cw, ch = 0.175, 0.075, 0.132, 0.062
    for j, cname in enumerate(SCHED_COLS):
        label(ax, x0 + (j + 0.5) * cw, 0.333, cname, fontsize=7.6)
    for i, (pname, vals) in enumerate(SCHEDULE.items()):
        y = y0 + (3 - i) * ch
        label(ax, x0 - 0.012, y + ch / 2, pname, fontsize=7.8,
              ha="right")
        for j, v in enumerate(vals):
            num = SCHED_NUM[pname][j]
            shade = plt.cm.Blues(0.10 + 0.42 * min(num / 1.0, 1.0))
            ax.add_patch(plt.Rectangle(
                (x0 + j * cw, y), cw, ch, facecolor=shade,
                edgecolor="white", lw=1.0, zorder=1))
            ax.text(x0 + (j + 0.5) * cw, y + ch / 2, v, ha="center",
                    va="center", fontsize=7.4, color=INK, zorder=2)
    label(ax, 0.5, 0.035,
          r"$\phi(t)=t/T$; Endgame pinning is capped at $0.5$. "
          "Shading is proportional to the rate and carries no "
          "information beyond the printed value.",
          fontsize=6.9, color=MUTED)
    save(fig, os.path.join(FIGURES, "ca_statemachine.png"))


def main():
    fig_architecture()
    fig_roles()
    fig_tactics()
    fig_statemachine()


if __name__ == "__main__":
    main()
