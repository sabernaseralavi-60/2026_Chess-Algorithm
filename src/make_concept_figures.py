"""
make_concept_figures.py
=======================
Conceptual figures for the Introduction and for the transportation
application.  These are schematic: they contain no experimental value.
Every statement drawn in a box is a restatement of a claim the
manuscript already makes in the text, and the sketched landscapes are
generated analytically, not traced by hand.

    fig_motivation()    -> figures/concept_motivation.png
    fig_abstraction()   -> figures/concept_abstraction.png
    fig_signal_model()  -> figures/signal_model.png

Equation and table numbers printed inside the figures are read from
paper.qmd at drawing time (figstyle.eq / tbl), so they cannot drift
from the rendered manuscript.

Usage:  python src/make_concept_figures.py
"""

import os

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from figstyle import (CAND, ELITE, EXPLORE, FILL, FILL2, FILL3, INK,  # noqa: E402
                      KING, MUTED, arrow, blank, box, eq, label, save,
                      tbl, use_style)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGURES = os.path.join(ROOT, "figures")


# --------------------------------------------------------------------
# Figure 1 -- motivation and conceptual architecture
# --------------------------------------------------------------------
def fig_motivation():
    use_style()
    fig = plt.figure(figsize=(7.2, 3.15))
    ax = blank(fig.add_axes([0, 0, 1, 1]))

    # ---- column headers
    heads = [(0.025, 0.295, "Structure of the problems"),
             (0.355, 0.255, "Homogeneous population search:\n"
                            "two structural limitations"),
             (0.645, 0.345, "Chess Algorithm")]
    for x, w, t in heads:
        label(ax, x + w / 2, 0.945, t, fontsize=9.0, weight="bold")

    # ---- column 1: problem structure, with an analytic landscape
    box(ax, 0.025, 0.535, 0.295, 0.32, "", fc=FILL2, ec=INK)
    lx = np.linspace(-2.6, 2.6, 400)
    ly = 0.35 * lx ** 2 + np.sin(3.1 * lx) * 1.15 + 1.4
    axl = fig.add_axes([0.045, 0.575, 0.255, 0.235])
    axl.patch.set_alpha(0.0)
    axl.plot(lx, ly, color=INK, lw=1.1)
    imin = int(np.argmin(ly))
    axl.plot(lx[imin], ly[imin], "o", color=KING, ms=4.0, zorder=4)
    for j in (60, 205, 340):
        axl.plot(lx[j], ly[j], "o", color=MUTED, ms=2.8, zorder=4)
    axl.set_xticks([])
    axl.set_yticks([])
    for s in axl.spines.values():
        s.set_visible(False)
    axl.text(0.5, -0.13, r"$f(\mathbf{x})$ on a box-constrained $\Omega$",
             transform=axl.transAxes, ha="center", fontsize=7.2,
             color=MUTED)

    box(ax, 0.025, 0.09, 0.295, 0.395,
        "non-convex, multimodal\n"
        "many local optima\n"
        "often non-differentiable\n"
        "expensive to evaluate\n"
        r"(signal timing, network design, $\dots$)",
        fc=FILL, fontsize=7.9)

    # ---- column 2: what a homogeneous population does
    box(ax, 0.355, 0.535, 0.255, 0.32,
        "one update equation\napplied to every agent\n"
        "(agents differ only by\nposition and fitness)",
        fc=FILL, fontsize=7.9)
    box(ax, 0.355, 0.09, 0.255, 0.395,
        "exploration $\\rightarrow$ exploitation\n"
        "scheduled on elapsed time\n"
        r"$t/T$ alone, not on the" "\nobserved state of the search",
        fc=FILL, fontsize=7.9)

    # ---- column 3: CA's two answers
    box(ax, 0.645, 0.605, 0.345, 0.25,
        "heterogeneous roles\n"
        "King, Queen, Rook, Bishop, Knight, Pawn,\n"
        "reassigned by rank every iteration",
        fc=FILL, fontsize=7.9)
    box(ax, 0.645, 0.315, 0.345, 0.235,
        "adaptive tactical control\n"
        "divergence, initiative, local-search\n"
        "success and stagnation select the phase",
        fc=FILL, fontsize=7.9)
    box(ax, 0.645, 0.09, 0.345, 0.17,
        "exploration$-$exploitation balance",
        fc=FILL3, fontsize=8.4, weight="bold")

    # ---- flow
    arrow(ax, (0.325, 0.29), (0.352, 0.29), lw=1.0)
    arrow(ax, (0.613, 0.44), (0.642, 0.70), lw=1.0,
          connection="arc3,rad=-0.15")
    arrow(ax, (0.613, 0.36), (0.642, 0.44), lw=1.0,
          connection="arc3,rad=0.15")
    arrow(ax, (0.8175, 0.602), (0.8175, 0.554), lw=0.9, color=MUTED)
    arrow(ax, (0.8175, 0.312), (0.8175, 0.264), lw=0.9, color=MUTED)

    save(fig, os.path.join(FIGURES, "concept_motivation.png"))


# --------------------------------------------------------------------
# Figure 2 -- chess -> optimization abstraction
# --------------------------------------------------------------------
# the abstraction figure draws its glyphs in figure-fraction
# coordinates, so every horizontal offset is scaled by the figure's
# aspect ratio; without this a circle would render as an ellipse
ASPECT = 3.7 / 7.2


def _pt(cx, cy, dx, dy, s):
    return (cx + dx * s * ASPECT, cy + dy * s)


def _glyph_king(ax, cx, cy, s):
    ax.plot([cx], [cy], "o", color=KING, ms=6.5, zorder=4)
    label(ax, *_pt(cx, cy, 0, 1.15, s), r"$\mathbf{K}$", fontsize=7.5,
          color=KING)


def _glyph_queen(ax, cx, cy, s):
    th = np.linspace(0, 2 * np.pi, 200)
    ax.plot(cx + s * ASPECT * np.cos(th), cy + s * np.sin(th), ls=":",
            lw=0.8, color=MUTED)
    ax.plot([cx], [cy], "o", color=KING, ms=4.5, zorder=4)
    for a in (0.5, 2.1, 3.6, 5.2):
        arrow(ax, (cx, cy), _pt(cx, cy, np.cos(a), np.sin(a), s),
              color=CAND, lw=0.8)


def _glyph_rook(ax, cx, cy, s):
    ax.plot([cx], [cy], "o", color=KING, ms=4.5, zorder=4)
    arrow(ax, (cx, cy), _pt(cx, cy, 1.5, 0, s), color=CAND, lw=0.9)
    arrow(ax, (cx, cy), _pt(cx, cy, -1.5, 0, s), color=CAND, lw=0.9)


def _glyph_bishop(ax, cx, cy, s):
    ax.plot([cx], [cy], "o", color=KING, ms=4.5, zorder=4)
    arrow(ax, (cx, cy), _pt(cx, cy, 1.05, 1.05, s), color=CAND, lw=0.9)
    arrow(ax, (cx, cy), _pt(cx, cy, -1.05, 1.05, s), color=CAND, lw=0.9)


def _glyph_knight(ax, cx, cy, s):
    agent = _pt(cx, cy, -1.5, -0.9, s)
    peer = _pt(cx, cy, -0.4, 0.1, s)
    drift = _pt(cx, cy, -0.75, -0.25, s)
    ax.plot(*peer, "o", color=ELITE, ms=4.0, zorder=4)
    ax.plot(*agent, "o", color=MUTED, ms=3.4, zorder=4)
    arrow(ax, agent, drift, color=ELITE, lw=0.8)
    arrow(ax, drift, _pt(cx, cy, -0.75, 1.15, s), color=CAND, lw=0.9)
    arrow(ax, _pt(cx, cy, -0.75, 1.15, s), _pt(cx, cy, 0.05, 1.15, s),
          color=CAND, lw=0.9)
    arrow(ax, agent, _pt(cx, cy, 1.7, 0.6, s), color=EXPLORE, lw=0.8,
          ls=(0, (2, 1.2)))


def _glyph_pawn(ax, cx, cy, s):
    king = _pt(cx, cy, 1.3, 0.9, s)
    peer = _pt(cx, cy, 0.2, 1.2, s)
    agent = _pt(cx, cy, -1.3, -0.9, s)
    ax.plot(*king, "o", color=KING, ms=4.5, zorder=4)
    ax.plot(*peer, "o", color=ELITE, ms=4.0, zorder=4)
    ax.plot(*agent, "o", color=MUTED, ms=3.4, zorder=4)
    arrow(ax, agent, _pt(cx, cy, 0.0, 0.0, s), color=CAND, lw=0.85)
    arrow(ax, agent, _pt(cx, cy, -0.6, 0.15, s), color=CAND, lw=0.85)


def fig_abstraction():
    use_style()
    fig = plt.figure(figsize=(7.2, 3.7))
    ax = blank(fig.add_axes([0, 0, 1, 1]))

    cols = [(0.045, "Piece"), (0.215, "Move geometry"),
            (0.45, "Search behaviour around the incumbent"),
            (0.845, "Primary contribution")]
    for x, t in cols:
        label(ax, x, 0.955, t, fontsize=8.6, weight="bold", ha="left")
    ax.plot([0.03, 0.975], [0.925, 0.925], color=INK, lw=0.9)

    rows = [
        ("King", _glyph_king,
         r"incumbent best solution $\mathbf{K}$, never lost",
         "elitism", INK),
        ("Queen", _glyph_queen,
         "omnidirectional sweep at a radius tied to\n"
         r"the current distance $|\mathbf{K}-\mathbf{X}_i|$   " f"({eq('eq-queen')})",
         "exploration", EXPLORE),
        ("Rook", _glyph_rook,
         "single-axis move: one coordinate of the\n"
         "incumbent is perturbed   " f"({eq('eq-rook')})",
         "axis-aligned search", ELITE),
        ("Bishop", _glyph_bishop,
         "two-axis move of equal magnitude, the\n"
         "box-constrained analogue of a diagonal   " f"({eq('eq-bishop')})",
         "axis-pair search", ELITE),
        ("Knight", _glyph_knight,
         "drift toward a better-ranked peer plus a 2:1\n"
         "jump; occasionally a long-range leap (dashed)   " f"({eq('eq-knight')})",
         "exploration", EXPLORE),
        ("Pawn", _glyph_pawn,
         "small advance toward the incumbent and\n"
         "toward a better-ranked peer   " f"({eq('eq-pawn')})",
         "exploitation", CAND),
    ]

    y0, dy = 0.855, 0.138
    for k, (name, glyph, text, tag, tcol) in enumerate(rows):
        y = y0 - k * dy
        label(ax, 0.045, y, name, fontsize=8.6, ha="left", weight="bold")
        glyph(ax, 0.265, y, 0.046)
        label(ax, 0.35, y, text, fontsize=7.9, ha="left")
        label(ax, 0.845, y, tag, fontsize=8.0, ha="left", color=tcol)
        if k < len(rows) - 1:
            ax.plot([0.03, 0.975], [y - dy / 2, y - dy / 2],
                    color=FILL3, lw=0.7, zorder=0)

    label(ax, 0.03, 0.028,
          "Every role operator is an instance of the elite-guided "
          "stochastic-perturbation family; " f"{tbl('tbl-operator-families')}" " gives the operator "
          "family and canonical reference of each\nmechanism. The "
          "metaphor names the composition, not any operator that the "
          "table cannot name.", fontsize=7.3, ha="left", color=MUTED)
    save(fig, os.path.join(FIGURES, "concept_abstraction.png"))


# --------------------------------------------------------------------
# Figure 13 -- signal-timing model: arterial -> decision vector
# --------------------------------------------------------------------
# intersection spacings and progression speed of the test bed,
# as stated in the transportation section of the manuscript
SPACING = [450, 380, 520, 300, 610, 420, 350]     # m
SPEED_KMH = 50


def fig_signal_model():
    use_style()
    fig = plt.figure(figsize=(7.4, 4.7))
    axa = fig.add_axes([0.06, 0.635, 0.90, 0.31])
    axb = fig.add_axes([0.09, 0.135, 0.87, 0.375])

    # ---- (a) the arterial and what each variable controls
    blank(axa, (0, 1), (0, 1))
    xs = np.cumsum([0] + SPACING, dtype=float)
    xs = 0.06 + 0.88 * xs / xs[-1]
    axa.plot([0.03, 0.99], [0.45, 0.45], color=MUTED, lw=2.2,
             solid_capstyle="butt", zorder=1)
    for i, x in enumerate(xs, start=1):
        axa.plot([x, x], [0.30, 0.60], color=INK, lw=1.6, zorder=2)
        axa.plot([x], [0.45], "s", color=FILL, mec=INK, ms=7.5, mew=0.9,
                 zorder=3)
        axa.text(x, 0.68, f"$I_{i}$", fontsize=7.6, ha="center",
                 color=INK)
        axa.text(x, 0.19, f"$g_{{{i}}}$", fontsize=7.4, ha="center",
                 color=ELITE)
        if i >= 2:
            axa.text(x, 0.05, f"$o_{{{i}}}$", fontsize=7.4, ha="center",
                     color=CAND)
    for i, s in enumerate(SPACING):
        axa.text((xs[i] + xs[i + 1]) / 2, 0.80, f"{s} m", fontsize=6.8,
                 ha="center", color=MUTED)
    axa.annotate("", xy=(0.185, 0.57), xytext=(0.09, 0.57),
                 arrowprops=dict(arrowstyle="-|>", color=KING, lw=1.1))
    axa.text(0.20, 0.57, "eastbound", fontsize=6.8, ha="left",
             va="center", color=KING)
    axa.annotate("", xy=(0.09, 0.33), xytext=(0.185, 0.33),
                 arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.1))
    axa.text(0.20, 0.33, "westbound", fontsize=6.8, ha="left",
             va="center", color=MUTED)
    axa.text(0.03, 0.95,
             "(a)  common cycle $C$ (all intersections)   |   "
             "arterial green split $g_i$ (green)   |   "
             "offset $o_i$ relative to $I_1$ (orange)",
             fontsize=8.0, ha="left", color=INK)
    axa.text(0.03, -0.06,
             r"$\mathbf{z}=(C,\ g_1,\dots,g_8,\ o_2,\dots,o_8)"
             r"\in\mathbb{R}^{16}$   " f"({eq('eq-decision')})",
             fontsize=8.6, ha="left", color=INK)

    # ---- (b) how offsets move the green windows in time
    # Illustrative cycle and split; the offsets of I2-I5 are set to the
    # travel time from I1 (a coordinated green wave) and those of I6-I8
    # are set half a cycle away from it, so the same figure shows a
    # platoon that is held and one that is not.
    C, green, depart = 90.0, 0.55 * 90.0, 10.0
    cum = np.cumsum([0.0] + SPACING)
    travel = cum / (SPEED_KMH / 3.6)                    # s
    coordinated = [True, True, True, True, True, False, False, False]
    starts = [(travel[i] if coordinated[i] else travel[i] + C / 2) % C
              for i in range(8)]
    for i in range(8):
        y = 8 - i
        for k in (0, 1, 2):
            axb.add_patch(plt.Rectangle(
                (starts[i] + k * C, y - 0.30), green, 0.60,
                facecolor="#cdeccf" if coordinated[i] else "#f2dcd6",
                edgecolor="#15803d" if coordinated[i] else "#b45309",
                lw=0.6, zorder=1))
    arrival = depart + travel
    axb.plot(arrival, np.arange(8, 0, -1), color=KING, lw=1.6, zorder=3,
             label="eastbound platoon")
    axb.plot(arrival, np.arange(8, 0, -1), "o", color=KING, ms=3.0,
             zorder=4)
    axb.annotate("arrives inside the green window",
                 xy=(arrival[2], 6.0), xytext=(arrival[2] + 34, 6.85),
                 fontsize=7.2, color="#15803d",
                 arrowprops=dict(arrowstyle="-|>", color="#15803d",
                                 lw=0.8))
    axb.annotate("arrives after it: the platoon waits",
                 xy=(arrival[6], 2.0), xytext=(arrival[6] - 118, 1.05),
                 fontsize=7.2, color="#b45309",
                 arrowprops=dict(arrowstyle="-|>", color="#b45309",
                                 lw=0.8))
    axb.set_xlim(0, 250)
    axb.set_ylim(0.4, 8.8)
    axb.set_yticks(range(1, 9))
    axb.set_yticklabels([f"$I_{i}$" for i in range(8, 0, -1)])
    axb.set_xlabel("Time (s)")
    axb.set_xticks([0, 45, 90, 135, 180, 225])
    axb.legend(loc="lower right", bbox_to_anchor=(1.0, 1.0),
               fontsize=7.6, ncol=1)
    axb.text(0.0, 1.03,
             "(b)  offsets displace each local green window; whether a "
             "platoon meets the next window or waits for it is what "
             "makes the objective multimodal",
             transform=axb.transAxes, fontsize=8.0, ha="left",
             color=INK)
    for s in ("top", "right"):
        axb.spines[s].set_visible(False)
    fig.text(0.09, 0.012,
             "Schematic: an illustrative cycle and split are used to "
             "show the coupling between the offsets $o_i$, the spacings "
             "of panel (a) and the 50 km/h progression speed. No "
             "optimization result is plotted here.",
             fontsize=6.9, ha="left", color=MUTED)
    save(fig, os.path.join(FIGURES, "signal_model.png"))


def main():
    fig_motivation()
    fig_abstraction()
    fig_signal_model()


if __name__ == "__main__":
    main()
