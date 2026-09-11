"""
figstyle.py
===========
One visual language for every figure in the paper.

Before this module the manuscript carried two different palettes: the
classical-suite figures (run_benchmarks.py) coloured CA `#1a1a2e` while
the CEC/engineering figures (phase2_3_analysis.py) coloured it
`#1d4ed8`, so the same algorithm changed colour between sections.  The
identity palette below is the second one -- already validated for
lightness band, chroma floor, colour-vision-deficiency separation and
contrast on a light surface -- extended with an entry for SA, which
appears only in the classical suite.

Schematic figures (conceptual and mechanism diagrams) use the small
secondary palette at the bottom: incumbent, elite, candidate, neutral
structure.  No gradients, no 3-D, no decorative artwork.
"""

import os
import re

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PAPER = os.path.join(_ROOT, "paper.qmd")
_EQ_CACHE = {}
_SEC_CACHE = {}
_TBL_CACHE = {}


def _load_labels():
    """Equation and section numbers, read from the manuscript source.

    A figure that hard-codes "Eq. 15" goes stale the moment an equation
    is inserted before it.  Quarto numbers equations in the order their
    `{#eq-...}` labels appear and sections by their heading hierarchy,
    so both can be derived from paper.qmd at drawing time and can never
    drift from the rendered manuscript.
    """
    if _EQ_CACHE:
        return
    text = open(_PAPER, encoding="utf8").read()
    for n, m in enumerate(re.finditer(r"\{#(eq-[a-z0-9-]+)\}", text),
                          start=1):
        _EQ_CACHE[m.group(1)] = n
    for n, m in enumerate(re.finditer(r"\{#(tbl-[a-z0-9-]+)", text),
                          start=1):
        _TBL_CACHE[m.group(1)] = n
    counters = [0, 0, 0, 0]
    depth = 0
    for line in text.split("\n"):
        fence = re.match(r"^(:{3,})(.*)$", line.rstrip())
        if fence:
            depth += 1 if fence.group(2).strip() else -1
            depth = max(depth, 0)
            continue
        # headings inside a fenced div (a proposition title, a
        # format-conditional block) are not numbered sections
        if depth:
            continue
        m = re.match(r"^(#{1,4}) (.*)$", line)
        if not m or "{.unnumbered}" in m.group(2):
            continue
        level = len(m.group(1))
        counters[level - 1] += 1
        for k in range(level, 4):
            counters[k] = 0
        num = ".".join(str(c) for c in counters[:level] if True)
        lab = re.search(r"\{#(sec-[a-z0-9-]+)", m.group(2))
        if lab:
            _SEC_CACHE[lab.group(1)] = num


def eq(label, prefix="Eq. "):
    """'Eq. 5' for the equation labelled #eq-queen in paper.qmd."""
    _load_labels()
    return f"{prefix}{_EQ_CACHE[label]}"


def eqs(first, last):
    """'Eqs. 5-10' spanning two equation labels."""
    _load_labels()
    return f"Eqs. {_EQ_CACHE[first]}-{_EQ_CACHE[last]}"


def tbl(label, prefix="Table "):
    """'Table 4' for the table labelled #tbl-operator-families."""
    _load_labels()
    return f"{prefix}{_TBL_CACHE[label]}"


def sec(label, prefix="Sec. "):
    """'Sec. 2.8.4' for the section labelled #sec-blockade."""
    _load_labels()
    return f"{prefix}{_SEC_CACHE[label]}"

# ---- algorithm identity palette -----------------------------------
COLORS = {"CA": "#1d4ed8", "CA-static": "#c2410c", "GWO": "#059669",
          "PSO": "#be123c", "GA": "#a16207", "WOA": "#9333ea",
          "L-SHADE": "#0891b2", "CMA-ES": "#65a30d", "SA": "#7c3aed"}
STYLES = {"CA": "-", "CA-static": "--", "GWO": "-.", "PSO": ":",
          "GA": (0, (3, 1, 1, 1)), "WOA": (0, (5, 2)),
          "L-SHADE": (0, (1, 1)), "CMA-ES": (0, (4, 1, 1, 1, 1, 1)),
          "SA": (0, (2, 1, 1, 1, 1, 1))}

# ---- schematic palette --------------------------------------------
INK = "#1f2937"        # text and outlines
KING = "#1d4ed8"       # incumbent / best-so-far
ELITE = "#0f766e"      # better-ranked peers
CAND = "#c2410c"       # candidate produced by an operator
MUTED = "#64748b"      # ordinary population members, secondary text
EXPLORE = "#7c3aed"    # exploration-side annotation
FILL = "#f8fafc"       # primary box fill
FILL2 = "#eef2f7"      # secondary box fill
FILL3 = "#e2e8f0"      # tertiary / grouping fill

RC = {
    "font.family": "serif", "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.labelsize": 9, "axes.titlesize": 10,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "legend.fontsize": 8.5, "legend.frameon": False,
    "figure.dpi": 300, "savefig.dpi": 300,
    "savefig.bbox": "tight", "pdf.fonttype": 42,
}


def use_style():
    mpl.rcParams.update(RC)


def box(ax, x, y, w, h, text, fc=FILL, ec=INK, fontsize=8.0, lw=0.9,
        ha="center", weight="normal", color=INK, rounding=0.02,
        zorder=2, style="round"):
    """Rounded rectangle with centred text; returns the (x, y, w, h)."""
    pad = 0.0
    bs = (f"{style},pad=0" if style == "square"
          else f"{style},pad=0,rounding_size={rounding}")
    ax.add_patch(FancyBboxPatch(
        (x + pad, y + pad), w - 2 * pad, h - 2 * pad, boxstyle=bs,
        facecolor=fc, edgecolor=ec, linewidth=lw, zorder=zorder))
    ax.text(x + w / 2 if ha == "center" else x + 0.012,
            y + h / 2, text, ha=ha, va="center", fontsize=fontsize,
            color=color, weight=weight, zorder=zorder + 1,
            linespacing=1.35)
    return (x, y, w, h)


def process(ax, x, y, w, h, text, fc=FILL, fontsize=7.6, lw=0.9):
    """Flowchart process step: a plain rectangle (ISO 5807)."""
    return box(ax, x, y, w, h, text, fc=fc, fontsize=fontsize, lw=lw,
               rounding=0.0, style="square")


def terminator(ax, x, y, w, h, text, fc=FILL3, fontsize=7.8, lw=1.0):
    """Flowchart terminal: a stadium (start / stop)."""
    return box(ax, x, y, w, h, text, fc=fc, fontsize=fontsize, lw=lw,
               rounding=h / 2.0, style="round")


def parallelogram(ax, x, y, w, h, text, fc=FILL2, fontsize=7.6, lw=0.9,
                  skew=0.055):
    """Flowchart input / output symbol."""
    pts = [(x + skew, y), (x + w, y), (x + w - skew, y + h), (x, y + h)]
    ax.add_patch(Polygon(pts, closed=True, facecolor=fc, edgecolor=INK,
                         linewidth=lw, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fontsize, color=INK, zorder=3, linespacing=1.3)
    return (x, y, w, h)


def diamond(ax, x, y, w, h, text, fc=FILL2, fontsize=7.6, lw=0.9):
    """Flowchart decision symbol."""
    cx, cy = x + w / 2, y + h / 2
    pts = [(cx, y + h), (x + w, cy), (cx, y), (x, cy)]
    ax.add_patch(Polygon(pts, closed=True, facecolor=fc, edgecolor=INK,
                         linewidth=lw, zorder=2))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fontsize,
            color=INK, zorder=3, linespacing=1.3)
    return (x, y, w, h)


def arrow(ax, p1, p2, color=INK, lw=0.9, style="-|>", ls="-",
          shrink=1.5, connection="arc3,rad=0", zorder=3, alpha=1.0):
    ax.add_patch(FancyArrowPatch(
        p1, p2, arrowstyle=style, mutation_scale=9, linewidth=lw,
        linestyle=ls, color=color, shrinkA=shrink, shrinkB=shrink,
        connectionstyle=connection, zorder=zorder, alpha=alpha))


def label(ax, x, y, text, fontsize=8.0, color=INK, ha="center",
          va="center", weight="normal", style="normal", zorder=5,
          rotation=0):
    ax.text(x, y, text, fontsize=fontsize, color=color, ha=ha, va=va,
            weight=weight, style=style, zorder=zorder, rotation=rotation)


def panel_tag(ax, tag, x=0.0, y=1.0, fontsize=9.0):
    ax.text(x, y, tag, transform=ax.transAxes, fontsize=fontsize,
            weight="bold", va="bottom", ha="left", color=INK)


def blank(ax, xlim=(0, 1), ylim=(0, 1)):
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis("off")
    ax.set_aspect("auto")
    return ax


def save(fig, path):
    fig.savefig(path)
    plt.close(fig)
    print(f"wrote {path}")
