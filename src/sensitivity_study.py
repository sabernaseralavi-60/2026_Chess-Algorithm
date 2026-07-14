"""
sensitivity_study.py
======================
Step A4 of PLAN_cec2022_and_reply.md: one-at-a-time (OAT) parameter
sensitivity analysis for CA (chess_algorithm_v3), around the published
default configuration:

    role fractions   {(.05,.10,.10,.15), default (.10,.15,.15,.20),
                       (.15,.20,.20,.25)}
    theta0           {0.05, default 0.1, 0.2}
    castling_period  {5, default 10, 20}
    stall_break      {15, default 25, 40}
    pin_max          {0.15, default 0.30, 0.50}

Each group is varied one at a time (all other parameters held at their
published defaults); the "low"/"high" levels bracket the default. Phase
thresholds (div_open/div_end) are NOT re-swept here -- see the existing
results/phase_threshold_check.csv.

Same 6 problems and per-suite protocols as src/ablation_study.py:
    CEC-2017 F1, F4, F13, F22 @ D=30  (pop 30, iters 500, SEED0=20260713)
    WeldedBeam (engineering)          (pop 30, iters 500, SEED0=20260713)
    Berth allocation P2 (transport)   (pop 30, iters 300, SEED0=20260705)

Outputs:
    results/sensitivity_stats.csv   best/mean/std/median/worst per cell
    results/table_sensitivity.md    ratio vs default per (problem, variant),
                                     '>20% deviation' flagged

Usage:
    python src/sensitivity_study.py
    python src/sensitivity_study.py --smoke   # 2 problems, 3 runs, 20 iters
"""

import os
import sys
import time
import warnings

import numpy as np
import pandas as pd
from scipy.stats import ranksums

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import algorithms as alg
from engineering_problems import ENGINEERING
from opfunu.cec_based import cec2017

warnings.filterwarnings("ignore")

SMOKE = "--smoke" in sys.argv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
os.makedirs(RESULTS, exist_ok=True)
STATS_CSV = os.path.join(RESULTS, "sensitivity_stats.csv")
TABLE_MD = os.path.join(RESULTS, "table_sensitivity.md")

# ----------------------------------------------------------------------
# OAT sweep: one group at a time, low/high bracketing the default
# ----------------------------------------------------------------------
PARAM_GROUPS = {
    "role_fractions": [
        ("low", dict(frac_queen=0.05, frac_rook=0.10, frac_bishop=0.10,
                    frac_knight=0.15)),
        ("high", dict(frac_queen=0.15, frac_rook=0.20, frac_bishop=0.20,
                     frac_knight=0.25)),
    ],
    "theta0": [("low", dict(theta0=0.05)), ("high", dict(theta0=0.2))],
    "castling_period": [("low", dict(castling_period=5)),
                        ("high", dict(castling_period=20))],
    "stall_break": [("low", dict(stall_break=15)),
                    ("high", dict(stall_break=40))],
    "pin_max": [("low", dict(pin_max=0.15)), ("high", dict(pin_max=0.50))],
}
VARIANTS = ["default"] + [f"{g}_{lvl}" for g in PARAM_GROUPS
                          for lvl, _ in PARAM_GROUPS[g]]
_KWARGS = {"default": {}}
for _g, _levels in PARAM_GROUPS.items():
    for _lvl, _kw in _levels:
        _KWARGS[f"{_g}_{_lvl}"] = _kw


# ----------------------------------------------------------------------
# 6 problems, each with its own native protocol (mirrors ablation_study.py)
# ----------------------------------------------------------------------
def _cec2017_problem(n):
    prob = cec2017.__dict__[f"F{n}2017"](ndim=30)
    lo, sp = prob.lb.copy(), prob.ub - prob.lb

    def f_vec(U, lo=lo, sp=sp, prob=prob):
        Z = lo + sp * np.clip(np.atleast_2d(U), 0.0, 1.0)
        return np.array([prob.evaluate(z) for z in Z])

    return dict(f_vec=f_vec, dim=30, pop=30, iters=20 if SMOKE else 500,
                seed0=20260713, offset=prob.f_global, label=f"F{n}")


def _engineering_problem(name):
    fun, lb, ub, dim, f_ref = ENGINEERING[name]
    span = ub - lb

    def f_vec(U, lb=lb, span=span, fun=fun):
        Z = lb + span * np.clip(np.atleast_2d(U), 0.0, 1.0)
        return fun(Z)

    return dict(f_vec=f_vec, dim=dim, pop=30, iters=20 if SMOKE else 500,
                seed0=20260713, offset=0.0, label=name)


def _berth_problem():
    import mealpy_comparison as mc
    spec = mc.PROBLEMS["berth"]
    f_vec, _ = mc.make_unit(spec["fun"], spec["lb"], spec["ub"])
    return dict(f_vec=f_vec, dim=spec["dim"], pop=mc.POP,
                iters=20 if SMOKE else mc.ITERS, seed0=mc.SEED0,
                offset=0.0, label="BerthP2")


def build_problems():
    probs = [_cec2017_problem(n) for n in (1, 4, 13, 22)]
    probs.append(_engineering_problem("WeldedBeam"))
    probs.append(_berth_problem())
    if SMOKE:
        probs = probs[:2]
    return probs


def run_variant(vname, f_vec, dim, pop, iters, seed):
    rng = np.random.default_rng(seed)
    _, bf, _ = alg.chess_algorithm_v3(f_vec, 0.0, 1.0, dim, pop, iters, rng,
                                      **_KWARGS[vname])
    return bf


def main():
    RUNS = 3 if SMOKE else 30
    problems = build_problems()

    stats_rows = []
    ratio_rows = []
    t_start = time.time()

    for prob in problems:
        label = prob["label"]
        finals = {}
        for vname in VARIANTS:
            t0 = time.time()
            vals = np.empty(RUNS)
            for r in range(RUNS):
                bf = run_variant(vname, prob["f_vec"], prob["dim"],
                                 prob["pop"], prob["iters"], prob["seed0"] + r)
                vals[r] = bf - prob["offset"]
            finals[vname] = vals
            stats_rows.append(dict(
                problem=label, variant=vname, best=vals.min(),
                mean=vals.mean(), std=vals.std(), median=np.median(vals),
                worst=vals.max()))
            print(f"[sensitivity] {label:8s} {vname:20s} "
                  f"mean={vals.mean():14.6g} std={vals.std():10.4g} "
                  f"({time.time()-t0:5.1f}s)", flush=True)

        def_mean = finals["default"].mean()
        for vname in VARIANTS:
            if vname == "default":
                continue
            v_mean = finals[vname].mean()
            ratio = v_mean / def_mean if def_mean != 0 else np.nan
            _, p = ranksums(finals["default"], finals[vname])
            ratio_rows.append(dict(
                problem=label, variant=vname, ratio_vs_default=ratio,
                deviation_pct=100.0 * (ratio - 1.0), p_value=p,
                flag_20pct="yes" if abs(ratio - 1.0) > 0.20 else "no"))

        pd.DataFrame(stats_rows).to_csv(STATS_CSV, index=False)

    write_table(ratio_rows)
    print(f"\nTotal sensitivity wall time: {(time.time()-t_start)/60:.1f} min",
          flush=True)


VAR_NAME = {
    "role_fractions_low": "Role fractions (.05/.10/.10/.15)",
    "role_fractions_high": "Role fractions (.15/.20/.20/.25)",
    "theta0_low": r"$\theta_0 = 0.05$",
    "theta0_high": r"$\theta_0 = 0.2$",
    "castling_period_low": "Castling period $c = 5$",
    "castling_period_high": "Castling period $c = 20$",
    "stall_break_low": "Blockade threshold $= 15$",
    "stall_break_high": "Blockade threshold $= 40$",
    "pin_max_low": "Pin cap $= 0.15$",
    "pin_max_high": "Pin cap $= 0.50$",
}


def write_table(ratio_rows):
    """Include-safe markdown (no headings) so the table can be pulled
    into paper.qmd via {{< include >}} under a Quarto caption."""
    df = pd.DataFrame(ratio_rows)
    df.to_csv(os.path.join(RESULTS, "sensitivity_ratios.csv"), index=False)

    summary = (df.groupby("variant")["ratio_vs_default"]
               .mean().sort_values())
    flag_counts = df[df["flag_20pct"] == "yes"].groupby("variant").size()
    sig_counts = df[df["p_value"] < 0.05].groupby("variant").size()

    lines = ["| Parameter variant | Mean error ratio (variant / default) "
             "| $>20\\%$ deviation on (of 6) | Significant on (of 6) |",
             "|---|---:|---:|---:|"]
    for var, ratio in summary.items():
        lines.append(f"| {VAR_NAME[var]} | {ratio:.3f} | "
                     f"{int(flag_counts.get(var, 0))} | "
                     f"{int(sig_counts.get(var, 0))} |")
    with open(TABLE_MD, "w", encoding="utf8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
