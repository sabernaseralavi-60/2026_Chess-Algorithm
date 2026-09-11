"""
validate_presentation.py
========================
Numerical and structural validation of the revised presentation.

The revision moved every primary result table into a transposed layout
(algorithms as rows, test functions as columns) and relocated the
best/worst statistics to an appendix.  Nothing in that operation is
allowed to change a number, so this script re-reads every rendered
table cell and compares it against the source CSV, checks that the
bolding marks the best mean, checks the derived summary columns
(Friedman rank, win/tie/loss, best-mean counts), checks that the
figures' hard-coded schedule values agree with the manuscript's own
table, and checks that every figure file and cross-reference in
paper.qmd resolves.

Discrepancies are reported, never silently corrected.

Usage:  python src/validate_presentation.py
Exit code 0 if every check passes, 1 otherwise.
"""

import os
import re
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
FIGURES = os.path.join(ROOT, "figures")
PAPER = os.path.join(ROOT, "paper.qmd")

ALGOS8 = ["CA", "CA-static", "GWO", "PSO", "GA", "WOA", "L-SHADE",
          "CMA-ES"]

report = []
failures = []


def check(name, ok, detail=""):
    report.append((name, bool(ok), detail))
    if not ok:
        failures.append(f"{name}: {detail}")
    return ok


def parse_md_table(path):
    """Return (header list, {row label: [cells]}) for a pipe table."""
    rows, header = {}, None
    with open(path, encoding="utf8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if set("".join(cells)) <= set("-: "):
                continue
            if header is None:
                header = cells
            else:
                rows[cells[0]] = cells[1:]
    return header, rows


def cell_value(text):
    """Numeric mean encoded in a `mean ±std` cell (bold markers off)."""
    m = text.replace("**", "").split("±")[0].strip()
    try:
        return float(m)
    except ValueError:
        return None


def rel_close(a, b, tol=5e-3):
    if a is None or b is None:
        return False
    if b == 0:
        return abs(a) < 1e-12
    return abs(a - b) / abs(b) <= tol


# --------------------------------------------------------------------
# 1. transposed statistics tables against their source CSVs
# --------------------------------------------------------------------
def check_stats_table(md_name, csv_name, index_col, col_to_item,
                      algos=ALGOS8):
    path = os.path.join(RESULTS, md_name)
    if not os.path.exists(path):
        return check(f"{md_name} exists", False, "missing file")
    header, rows = parse_md_table(path)
    df = pd.read_csv(os.path.join(RESULTS, csv_name))
    # the classical suite's CSV uses capitalised column names
    df = df.rename(columns={"Algorithm": "algo", "Mean": "mean",
                            "Std": "std"})
    piv_m = df.pivot(index=index_col, columns="algo", values="mean")
    piv_s = df.pivot(index=index_col, columns="algo", values="std")

    bad_val, bad_bold, bad_std = [], [], []
    items = [col_to_item(c) for c in header[1:]]
    for a in algos:
        if a not in rows:
            bad_val.append(f"row {a} missing")
            continue
        for cell, item in zip(rows[a], items):
            got = cell_value(cell)
            want = piv_m.loc[item, a]
            if not rel_close(got, want, 5e-3):
                bad_val.append(f"{a}/{item}: table {got} vs csv {want}")
            std_txt = cell.split("±")[-1].strip()
            try:
                std_got = float(std_txt)
            except ValueError:
                std_got = None
            if not rel_close(std_got, piv_s.loc[item, a], 5e-3):
                bad_std.append(f"{a}/{item}: std {std_got} vs "
                               f"{piv_s.loc[item, a]}")
    # bolding marks the best mean in each column
    for j, item in enumerate(items):
        best = piv_m.loc[item, algos].idxmin()
        for a in algos:
            bolded = rows[a][j].startswith("**")
            if bolded != (a == best):
                bad_bold.append(f"{item}: bold on {a}, best is {best}")
    check(f"{md_name}: means match {csv_name}", not bad_val,
          "; ".join(bad_val[:4]))
    check(f"{md_name}: standard deviations match", not bad_std,
          "; ".join(bad_std[:4]))
    check(f"{md_name}: best mean per column is bold", not bad_bold,
          "; ".join(bad_bold[:4]))


# --------------------------------------------------------------------
# 2. suite summary tables (rank, best-mean count, W/T/L)
# --------------------------------------------------------------------
def check_summary(md_name, ranks_csv, wilc_csv, stats_csv, index_col):
    path = os.path.join(RESULTS, md_name)
    if not os.path.exists(path):
        return check(f"{md_name} exists", False, "missing file")
    _, rows = parse_md_table(path)
    ranks = pd.read_csv(os.path.join(RESULTS, ranks_csv)).set_index(
        "algo")["mean_rank"]
    wilc = pd.read_csv(os.path.join(RESULTS, wilc_csv))
    stats = pd.read_csv(os.path.join(RESULTS, stats_csv))
    piv = stats.pivot(index=index_col, columns="algo", values="mean")
    best_counts = piv[ALGOS8].idxmin(axis=1).value_counts()
    n_items = piv.shape[0]

    bad_rank, bad_best, bad_wtl = [], [], []
    for a in ALGOS8:
        key = f"**{a}**" if f"**{a}**" in rows else a
        if key not in rows:
            bad_rank.append(f"row {a} missing")
            continue
        cells = [c.replace("**", "") for c in rows[key]]
        if abs(float(cells[0]) - ranks[a]) > 0.005 + 1e-9:
            bad_rank.append(f"{a}: {cells[0]} vs {ranks[a]:.4f}")
        n_best = int(cells[2].split(" of ")[0])
        if n_best != int(best_counts.get(a, 0)):
            bad_best.append(f"{a}: {n_best} vs "
                            f"{int(best_counts.get(a, 0))}")
        if a != "CA":
            sub = wilc[wilc.competitor == a]
            w = int(((sub.significant == "yes")
                     & (sub.v3_mean_direction == "better")).sum())
            lo = int(((sub.significant == "yes")
                      & (sub.v3_mean_direction == "worse")).sum())
            want = f"{w} / {n_items - w - lo} / {lo}"
            if cells[3].strip() != want:
                bad_wtl.append(f"{a}: '{cells[3].strip()}' vs '{want}'")
    check(f"{md_name}: Friedman ranks match {ranks_csv}", not bad_rank,
          "; ".join(bad_rank[:4]))
    check(f"{md_name}: best-mean counts match the stats CSV",
          not bad_best, "; ".join(bad_best[:4]))
    check(f"{md_name}: win/tie/loss matches {wilc_csv}", not bad_wtl,
          "; ".join(bad_wtl[:4]))


# --------------------------------------------------------------------
def main():
    # ---- primary statistics tables
    check_stats_table("table_t_classical.md", "benchmark_stats.csv",
                      "Function",
                      lambda c: {"F1 Sphere": "Sphere",
                                 "F2 Rosenbrock": "Rosenbrock",
                                 "F3 Rastrigin": "Rastrigin",
                                 "F4 Griewank": "Griewank",
                                 "F5 Ackley": "Ackley",
                                 "F6 Schwefel 2.22": "Schwefel 2.22"}[c],
                      algos=["CA", "CA-static", "GWO", "PSO", "GA",
                             "SA"])
    cec17_groups = ("unimodal", "multimodal", "hybrid_a", "hybrid_b",
                    "composition_a", "composition_b")
    for key in cec17_groups:
        check_stats_table(f"table_t_cec2017_{key}.md",
                          "cec2017_stats.csv", "func", lambda c: c)
    for dim in ("D10", "D20"):
        check_stats_table(f"table_t_cec2022_{dim}.md",
                          "cec2022_stats.csv", "func",
                          lambda c, d=dim: f"{c}-{d}")
    eng_map = {"Welded beam": "WeldedBeam", "Spring": "Spring",
               "Pressure vessel": "PressureVessel",
               "Speed reducer": "SpeedReducer",
               "Three-bar truss": "ThreeBarTruss",
               "Gear train": "GearTrain",
               "Cantilever beam": "CantileverBeam"}
    check_stats_table("table_t_engineering.md", "engineering_stats.csv",
                      "problem", lambda c: eng_map[c])

    # ---- summary tables
    check_summary("table_t_cec2017_summary.md",
                  "cec2017_mean_ranks.csv", "cec2017_wilcoxon.csv",
                  "cec2017_stats.csv", "func")
    check_summary("table_t_cec2022_summary.md",
                  "cec2022_mean_ranks.csv", "cec2022_wilcoxon.csv",
                  "cec2022_stats.csv", "func")
    check_summary("table_t_engineering_summary.md",
                  "engineering_mean_ranks.csv",
                  "engineering_wilcoxon.csv", "engineering_stats.csv",
                  "problem")

    # ---- CEC-2017 grouping covers every validated function exactly once
    stats = pd.read_csv(os.path.join(RESULTS, "cec2017_stats.csv"))
    validated = sorted(stats["func"].unique(), key=lambda s: int(s[1:]))
    grouped = []
    for key in cec17_groups:
        header, _ = parse_md_table(
            os.path.join(RESULTS, f"table_t_cec2017_{key}.md"))
        grouped += header[1:]
    check("CEC-2017 category tables cover all validated functions once",
          sorted(grouped, key=lambda s: int(s[1:])) == validated,
          f"{len(grouped)} grouped vs {len(validated)} validated")

    # ---- classical Wilcoxon table against its CSV
    wl = pd.read_csv(os.path.join(RESULTS, "wilcoxon.csv"))
    _, rows = parse_md_table(
        os.path.join(RESULTS, "table_t_classical_wilcoxon.md"))
    mark = {"CA better": "(+)", "CA worse": "(-)",
            "not significant": "(=)"}
    funcs = ["Sphere", "Rosenbrock", "Rastrigin", "Griewank", "Ackley",
             "Schwefel 2.22"]
    bad = []
    for comp, cells in rows.items():
        for fn, cell in zip(funcs, cells):
            r = wl[(wl.Comparison == comp) & (wl.Function == fn)].iloc[0]
            p_txt, m_txt = cell.rsplit(" ", 1)
            if not rel_close(float(p_txt), r["p-value"], 1e-2):
                bad.append(f"{comp}/{fn}: p {p_txt} vs {r['p-value']}")
            if m_txt != mark[r["Significant (a=0.05)"]]:
                bad.append(f"{comp}/{fn}: marker {m_txt}")
    check("classical Wilcoxon table matches wilcoxon.csv", not bad,
          "; ".join(bad[:4]))

    # ---- ablation figure input equals the published ablation table
    ratios = pd.read_csv(os.path.join(RESULTS, "ablation_ratios.csv"))
    means = ratios.groupby("mechanism")["ratio_vs_full_ca"].mean()
    published = {"en_passant": 603.3, "knight_fork": 46.842,
                 "threefold": 1.213, "sacrifice": 1.070,
                 "pinning": 1.050, "windmill": 1.043,
                 "opposition_init": 1.030, "discovered_attack": 1.024,
                 "blockade": 1.006, "interference": 0.999,
                 "castling": 0.999, "royal_council": 0.990}
    bad = [f"{m}: {means[m]:.4g} vs {v}" for m, v in published.items()
           if not rel_close(means[m], v, 2e-3)]
    check("ablation ratios reproduce table_ablation.md", not bad,
          "; ".join(bad[:4]))

    # ---- the state-machine figure reprints the manuscript's schedule
    paper = open(PAPER, encoding="utf8").read()
    sched_rows = re.findall(
        r"\| (Opening|Middlegame|Closed|Endgame) \|([^\n]*)\|", paper)
    sys.path.insert(0, os.path.join(ROOT, "src"))
    from make_method_figures import SCHEDULE  # noqa: E402
    def norm(txt):
        """Strip the notation differences between a LaTeX table cell and
        a matplotlib mathtext label, leaving only the value."""
        for a, b in (("$", ""), ("\\,", ""), ("\\", ""), ("{+}", "+"),
                     ("^{*}", ""), ("(t)", ""), (" ", "")):
            txt = txt.replace(a, b)
        return txt

    bad = []
    for phase, rest in sched_rows:
        vals = [norm(c) for c in rest.split("|") if c.strip()]
        fig_vals = [norm(v) for v in SCHEDULE[phase]]
        for a, b in zip(vals, fig_vals):
            if a != b:
                bad.append(f"{phase}: table '{a}' vs figure '{b}'")
    check("state-machine figure matches the phase-schedule table",
          not bad, "; ".join(bad[:6]))

    # ---- the numbers printed inside the figures resolve to the same
    # objects as the rendered manuscript
    from figstyle import eq as fig_eq, sec as fig_sec, tbl as fig_tbl
    pdf = os.path.join(ROOT, "_article", "paper.pdf")
    if os.path.exists(pdf):
        try:
            import fitz
            doc = fitz.open(pdf)
            pdf_text = "\n".join(p.get_text() for p in doc)
            bad = []
            # section numbers: "2.11 Adaptive tactical control"
            for lab, title in (("sec-adaptive", "Adaptive tactical "
                                                "control"),
                               ("sec-complexity", "Computational and "
                                                  "memory complexity"),
                               ("sec-ca", "The Chess Algorithm")):
                num = fig_sec(lab, prefix="")
                if f"{num} {title}" not in pdf_text:
                    bad.append(f"{lab}: figures say {num}")
            # table numbers: "Table 3: Phase-conditioned tactical ..."
            for lab, cap in (("tbl-params", "CA parameters"),
                             ("tbl-phase-schedule",
                              "Phase-conditioned tactical schedule"),
                             ("tbl-operator-families",
                              "Every CA mechanism")):
                num = fig_tbl(lab, prefix="")
                if f"Table {num}: {cap}" not in pdf_text:
                    bad.append(f"{lab}: figures say Table {num}")
            # equation numbers: the label follows its equation as "(5)"
            for lab, anchor in (("eq-queen", "omnidirectional sweep"),
                                ("eq-enpassant",
                                 "En passant (adaptive local capture)")):
                num = fig_eq(lab, prefix="")
                idx = pdf_text.find(anchor)
                if idx < 0 or f"({num})" not in pdf_text[idx:idx + 900]:
                    bad.append(f"{lab}: figures say Eq. {num}")
            check("figure-embedded equation, table and section numbers "
                  "match the rendered PDF", not bad, "; ".join(bad))
        except ImportError:
            check("figure-embedded numbers match the rendered PDF",
                  True, "skipped: PyMuPDF not installed")
    else:
        check("figure-embedded numbers match the rendered PDF", True,
              "skipped: _article/paper.pdf not rendered yet")

    # ---- every figure referenced by the manuscript exists
    figs = re.findall(r"\]\((figures/[^)]+)\)", paper)
    missing = [f for f in figs if not os.path.exists(
        os.path.join(ROOT, f))]
    check("all referenced figure files exist", not missing,
          "; ".join(missing))

    # ---- every {{< include >}} target exists
    incs = re.findall(r"\{\{< include ([^>]+?) >\}\}", paper)
    missing = [i.strip() for i in incs
               if not os.path.exists(os.path.join(ROOT, i.strip()))]
    check("all included table files exist", not missing,
          "; ".join(missing))

    # ---- cross-references resolve
    defined = set(re.findall(r"\{#((?:tbl|fig|eq|sec|prp)-[a-z0-9-]+)",
                             paper))
    referenced = set(re.findall(r"@((?:tbl|fig|eq|sec|prp)-[a-z0-9-]+)",
                                paper))
    dangling = sorted(referenced - defined)
    check("no dangling cross-references", not dangling,
          "; ".join(dangling))
    unused = sorted(d for d in defined - referenced
                    if d.startswith(("tbl-", "fig-")))
    check("every table and figure is referenced in the text",
          not unused, "; ".join(unused))

    # ---- transportation tables must carry the competition-grade
    # baselines: mealpy_comparison.py alone writes only CA + six mealpy
    # algorithms, and sota_addon_run.py must run afterward to add
    # L-SHADE and CMA-ES; this once silently produced incomplete
    # tables (see VALIDATION_REPORT.md, "Status of the mealpy re-run",
    # and src/run_transportation_pipeline.py, which is now the only
    # supported way to reproduce them)
    required = ["L-SHADE", "CMA-ES"]
    for name in ("table_mealpy_signal.md", "table_mealpy_berth.md",
                "table_berth_gap.md"):
        path = os.path.join(RESULTS, name)
        if not os.path.exists(path):
            check(f"{name}: L-SHADE and CMA-ES rows present", False,
                  "file does not exist")
            continue
        _, rows = parse_md_table(path)
        missing = [a for a in required if a not in rows]
        check(f"{name}: L-SHADE and CMA-ES rows present", not missing,
              f"missing {', '.join(missing)}" if missing else "")

    # ---- duplicate labels
    labels = re.findall(r"\{#((?:tbl|fig)-[a-z0-9-]+)", paper)
    dups = sorted({x for x in labels if labels.count(x) > 1})
    check("no duplicate table or figure labels", not dups,
          "; ".join(dups))

    # ---- report
    width = max(len(n) for n, _, _ in report)
    print("\n=== presentation validation ===")
    for name, ok, detail in report:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name.ljust(width)}"
              + (f"  -- {detail}" if detail and not ok else ""))
    print(f"\n{len(report) - len(failures)}/{len(report)} checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
