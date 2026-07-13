"""
generate_latex_tables.py
=========================
Phase 4: publication-ready LaTeX tables for the CEC-2017 and engineering-
design results, generated programmatically from the result CSVs (never
transcribed by hand, to avoid copy errors).

Reads:
    results/cec2017_stats.csv, cec2017_wilcoxon.csv, cec2017_mean_ranks.csv
    results/engineering_stats.csv, engineering_wilcoxon.csv,
    engineering_mean_ranks.csv

Writes:
    results/latex_tables_final.tex

Required LaTeX packages (add to the manuscript preamble if not already
present): booktabs, multirow, longtable, array. The paper's PDF preamble
(paper.qmd) already loads booktabs; multirow/longtable/array must be
added.

Usage:  python src/generate_latex_tables.py
"""

import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")

ALGOS = ["CA", "CA-static", "GWO", "PSO", "GA", "WOA"]
ALGO_TEX = {"CA": "CA", "CA-static": "CA-static", "GWO": "GWO", "PSO": "PSO",
            "GA": "GA", "WOA": "WOA"}
DISPLAY_NAME = {
    "WeldedBeam": "Welded Beam", "Spring": "Spring",
    "PressureVessel": "Pressure Vessel", "SpeedReducer": "Speed Reducer",
    "ThreeBarTruss": "Three-Bar Truss", "GearTrain": "Gear Train",
    "CantileverBeam": "Cantilever Beam",
}


def fnum(label):
    return int(label[1:])


def fmt_sci(x, sig=3):
    """Compact '$m \\times 10^{e}$' formatting; plain fixed-point for
    numbers that don't need it."""
    if x == 0:
        return "0"
    ax = abs(x)
    sign = "-" if x < 0 else ""
    if 1e-3 <= ax < 1e5:
        if ax >= 1:
            decimals = max(0, sig - int(np.floor(np.log10(ax))) - 1)
        else:
            decimals = sig - int(np.floor(np.log10(ax))) - 1
        s = f"{x:.{max(decimals,0)}f}"
        return s
    e = int(np.floor(np.log10(ax)))
    m = ax / 10**e
    m_str = f"{m:.{sig-1}f}"
    if m_str.startswith("10"):        # rounding rolled over, e.g. 9.995->10.0
        e += 1
        m = ax / 10**e
        m_str = f"{m:.{sig-1}f}"
    return f"{sign}{m_str}\\times 10^{{{e}}}"


def fmt_math(x, sig=3):
    s = fmt_sci(x, sig)
    return f"${s}$" if "\\times" in s else s


# ----------------------------------------------------------------------
# helpers shared by both suites
# ----------------------------------------------------------------------
def rank_table(ranks_csv, caption, label):
    df = pd.read_csv(ranks_csv)
    df = df.sort_values("mean_rank")
    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        rf"\caption{{{caption}}}",
        rf"\label{{{label}}}",
        r"\begin{tabular}{@{}lc@{}}",
        r"\toprule",
        r"Algorithm & Mean Friedman rank \\",
        r"\midrule",
    ]
    for _, row in df.iterrows():
        algo = ALGO_TEX[row["algo"]]
        bold = algo == "CA"
        val = f"{row['mean_rank']:.3f}"
        if bold:
            algo, val = rf"\textbf{{{algo}}}", rf"\textbf{{{val}}}"
        lines.append(rf"{algo} & {val} \\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    return "\n".join(lines)


def wtl_table(wilc_csv, index_col, caption, label):
    wl = pd.read_csv(wilc_csv)
    n_items = wl[index_col].nunique()
    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        rf"\caption{{{caption}}}",
        rf"\label{{{label}}}",
        r"\begin{tabular}{@{}lccc@{}}",
        r"\toprule",
        r"Competitor & Win & Tie & Loss \\",
        r"\midrule",
    ]
    for comp in [a for a in ALGOS if a != "CA"]:
        sub = wl[wl.competitor == comp]
        w = ((sub.significant == "yes")
             & (sub.v3_mean_direction == "better")).sum()
        lo = ((sub.significant == "yes")
              & (sub.v3_mean_direction == "worse")).sum()
        tie = n_items - w - lo
        lines.append(rf"{ALGO_TEX[comp]} & {w} & {tie} & {lo} \\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    return "\n".join(lines)


# ----------------------------------------------------------------------
# CEC-2017 detailed longtable (mean +/- std, best per function bolded,
# +/=/- significance marker relative to CA)
# ----------------------------------------------------------------------
def sig_marker(wilc, item, algo, index_col="func"):
    if algo == "CA":
        return ""
    row = wilc[(wilc[index_col] == item) & (wilc.competitor == algo)]
    if row.empty or row.iloc[0]["significant"] != "yes":
        return "$^{=}$"
    return ("$^{-}$" if row.iloc[0]["v3_mean_direction"] == "better"
            else "$^{+}$")


def cec_detail_longtable(stats_csv, wilc_csv):
    stats = pd.read_csv(stats_csv)
    wilc = pd.read_csv(wilc_csv)
    funcs = sorted(stats["func"].unique(), key=fnum)

    lines = [
        r"\begin{longtable}{@{}l" + "c" * len(ALGOS) + r"@{}}",
        r"\caption{CEC-2017 results (D=30): mean error $f-f^{*}$ over "
        r"30 runs, best mean per function in bold. Superscripts mark "
        r"CA vs. the column algorithm under a two-sided Wilcoxon "
        r"rank-sum test at $\alpha=0.05$: $^{+}$ column algorithm "
        r"significantly better, $^{-}$ column algorithm significantly "
        r"worse, $^{=}$ not significant. F5, F9, F15, F19, and F21 are "
        r"excluded (see Section~\ref{sec:opfunu-audit}).}",
        r"\label{tab:cec2017-detail}\\",
        r"\toprule",
        "Func & " + " & ".join(ALGO_TEX[a] for a in ALGOS) + r" \\",
        r"\midrule",
        r"\endfirsthead",
        r"\multicolumn{" + str(len(ALGOS) + 1)
        + r"}{c}{\tablename\ \thetable{} -- continued}\\",
        r"\toprule",
        "Func & " + " & ".join(ALGO_TEX[a] for a in ALGOS) + r" \\",
        r"\midrule",
        r"\endhead",
        r"\bottomrule",
        r"\endfoot",
    ]
    for label in funcs:
        sub = stats[stats["func"] == label].set_index("algo")
        best_algo = sub["mean"].idxmin()
        cells = []
        for a in ALGOS:
            m, s = sub.loc[a, "mean"], sub.loc[a, "std"]
            cell = f"{fmt_sci(m)} ({fmt_sci(s, 2)})"
            cell += sig_marker(wilc, label, a)
            if a == best_algo:
                cell = rf"\textbf{{{cell}}}"
            cells.append(cell)
        lines.append(f"{label} & " + " & ".join(cells) + r" \\")
    lines.append(r"\end{longtable}")
    return "\n".join(lines)


# ----------------------------------------------------------------------
# Engineering detail table (multirow: Best / Mean / Std per problem)
# ----------------------------------------------------------------------
def engineering_detail_table(stats_csv, wilc_csv):
    stats = pd.read_csv(stats_csv)
    wilc = pd.read_csv(wilc_csv)
    problems = list(stats["problem"].unique())

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Constrained engineering design problems: Best, Mean "
        r"and Std over 30 independent runs (best mean per problem in "
        r"bold). Superscripts as in Table~\ref{tab:cec2017-detail}. "
        r"$f_{\mathrm{ref}}$ is the best value commonly reported in the "
        r"literature for each formulation, shown for orientation only.}",
        r"\label{tab:engineering-detail}",
        r"\resizebox{\textwidth}{!}{%",
        r"\begin{tabular}{@{}ll" + "c" * len(ALGOS) + r"@{}}",
        r"\toprule",
        "Problem ($f_{\\mathrm{ref}}$) & Stat & "
        + " & ".join(ALGO_TEX[a] for a in ALGOS) + r" \\",
        r"\midrule",
    ]
    for pname in problems:
        sub = stats[stats["problem"] == pname].set_index("algo")
        f_ref = sub["f_ref"].iloc[0]
        best_algo = sub["mean"].idxmin()
        disp = DISPLAY_NAME.get(pname, pname)
        label = rf"\multirow{{2}}{{*}}{{{disp} ({fmt_sci(f_ref)})}}"

        mean_cells = []
        for a in ALGOS:
            cell = fmt_sci(sub.loc[a, "mean"])
            cell += sig_marker(wilc, pname, a, index_col="problem")
            if a == best_algo:
                cell = rf"\textbf{{{cell}}}"
            mean_cells.append(cell)
        lines.append(f"{label} & Mean & " + " & ".join(mean_cells)
                     + r" \\")

        std_cells = [fmt_sci(sub.loc[a, "std"], 2) for a in ALGOS]
        lines.append(" & Std & " + " & ".join(std_cells) + r" \\")
        lines.append(r"\addlinespace")
    lines += [r"\bottomrule", r"\end{tabular}%", "}", r"\end{table}", ""]
    return "\n".join(lines)


def main():
    parts = [
        "% ============================================================\n"
        "% Auto-generated by src/generate_latex_tables.py -- do not edit\n"
        "% by hand; re-run the script after any change to the result\n"
        "% CSVs. Requires \\usepackage{booktabs,multirow,longtable,array}\n"
        "% in the manuscript preamble.\n"
        "% ============================================================\n",

        "% ---- CEC-2017 (24 valid functions; see the data-integrity\n"
        "%      audit for the 5 excluded functions) ----\n",
        rank_table(os.path.join(RESULTS, "cec2017_mean_ranks.csv"),
                  "CEC-2017 (D=30, 24 valid functions): mean Friedman "
                  "rank over 30 independent runs per function (lower is "
                  "better).",
                  "tab:cec2017-friedman"),
        wtl_table(os.path.join(RESULTS, "cec2017_wilcoxon.csv"), "func",
                 "CEC-2017: CA win/tie/loss against each competitor "
                 "(Wilcoxon rank-sum, $\\alpha=0.05$, 24 functions).",
                 "tab:cec2017-wtl"),
        cec_detail_longtable(
            os.path.join(RESULTS, "cec2017_stats.csv"),
            os.path.join(RESULTS, "cec2017_wilcoxon.csv")),

        "\n% ---- Constrained engineering design problems ----\n",
        rank_table(os.path.join(RESULTS, "engineering_mean_ranks.csv"),
                  "Engineering design problems: mean Friedman rank over "
                  "30 independent runs per problem (lower is better).",
                  "tab:engineering-friedman"),
        wtl_table(os.path.join(RESULTS, "engineering_wilcoxon.csv"),
                 "problem",
                 "Engineering design problems: CA win/tie/loss "
                 "against each competitor (Wilcoxon rank-sum, "
                 "$\\alpha=0.05$, 7 problems).",
                 "tab:engineering-wtl"),
        engineering_detail_table(
            os.path.join(RESULTS, "engineering_stats.csv"),
            os.path.join(RESULTS, "engineering_wilcoxon.csv")),
    ]

    out_path = os.path.join(RESULTS, "latex_tables_final.tex")
    with open(out_path, "w", encoding="utf8") as f:
        f.write("\n".join(parts))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
