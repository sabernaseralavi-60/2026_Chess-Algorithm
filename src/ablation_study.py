"""
ablation_study.py
===================
Step A3 of PLAN_cec2022_and_reply.md: granular per-mechanism ablation of
CA (chess_algorithm_v3). Each of the 12 tactical mechanisms is switched
off one at a time (all else at published defaults) and compared against
full CA and CA-static on 6 representative problems:

    CEC-2017 F1, F4, F13, F22 @ D=30  (pop 30, iters 500, SEED0=20260713)
    WeldedBeam (engineering)          (pop 30, iters 500, SEED0=20260713)
    Berth allocation P2 (transport)   (pop 30, iters 300, SEED0=20260705)

each problem reusing its own suite's protocol/seed exactly, per the
project's established convention (see src/cec2017_full_run.py,
src/engineering_full_run.py, src/mealpy_comparison.py).

Prerequisite: the bit-identity check (chess_algorithm_v3's new ablation
kwargs default to the published behavior) has been run and passed -- see
the module docstring of chess_algorithm_v3 in src/algorithms.py.

Outputs:
    results/ablation_stats.csv   best/mean/std/median/worst per cell
    results/table_ablation.md    mean-error ratio vs full CA per mechanism
                                  (averaged across the 6 problems) + a
                                  per-problem detail table, Wilcoxon flags

Usage:
    python src/ablation_study.py
    python src/ablation_study.py --smoke    # 2 problems, 3 runs, 20 iters
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
STATS_CSV = os.path.join(RESULTS, "ablation_stats.csv")
TABLE_MD = os.path.join(RESULTS, "table_ablation.md")

# ----------------------------------------------------------------------
# the 12 single-mechanism-off variants
# ----------------------------------------------------------------------
MECHANISMS = {
    "pinning":          dict(enable_pinning=False),
    "en_passant":       dict(enable_enpassant=False),
    "windmill":         dict(enable_windmill=False),
    "threefold":        dict(enable_threefold=False),
    "royal_council":    dict(p_council_scale=0.0),
    "castling":         dict(castling_period=10 ** 9),
    "sacrifice":        dict(theta0=0.0),
    "knight_fork":      dict(p_fork=0.0),
    "blockade":         dict(stall_break=10 ** 9),
    "interference":     dict(intf_open=0.0, intf_mid=0.0),
    "discovered_attack": dict(p_da_mid=0.0, p_da_late=0.0),
    "opposition_init":  dict(opp_init=False),
}
VARIANTS = ["CA", "CA-static"] + list(MECHANISMS.keys())


# ----------------------------------------------------------------------
# 6 problems, each with its own native protocol
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
    if vname == "CA":
        _, bf, _ = alg.chess_algorithm_v3(f_vec, 0.0, 1.0, dim, pop, iters, rng)
    elif vname == "CA-static":
        _, bf, _ = alg.chess_algorithm_v2(f_vec, 0.0, 1.0, dim, pop, iters, rng)
    else:
        _, bf, _ = alg.chess_algorithm_v3(f_vec, 0.0, 1.0, dim, pop, iters, rng,
                                          **MECHANISMS[vname])
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
            print(f"[ablation] {label:8s} {vname:18s} "
                  f"mean={vals.mean():14.6g} std={vals.std():10.4g} "
                  f"({time.time()-t0:5.1f}s)", flush=True)

        ca_mean = finals["CA"].mean()
        for mname in MECHANISMS:
            m_mean = finals[mname].mean()
            ratio = m_mean / ca_mean if ca_mean != 0 else np.nan
            _, p = ranksums(finals["CA"], finals[mname])
            ratio_rows.append(dict(
                problem=label, mechanism=mname, ratio_vs_full_ca=ratio,
                p_value=p, significant="yes" if p < 0.05 else "no"))

        pd.DataFrame(stats_rows).to_csv(STATS_CSV, index=False)

    write_table(ratio_rows)
    print(f"\nTotal ablation wall time: {(time.time()-t_start)/60:.1f} min",
          flush=True)


MECH_NAME = {
    "en_passant": "En passant (success-rule local capture)",
    "knight_fork": "Knight's fork",
    "threefold": "Threefold repetition",
    "sacrifice": "Sacrifice",
    "pinning": "Pinning",
    "windmill": "Windmill",
    "opposition_init": "Opposition-based initialization",
    "discovered_attack": "Discovered attack",
    "blockade": "Blockade response",
    "interference": "Novotny interference",
    "castling": "Castling",
    "royal_council": "Royal council",
}


def write_table(ratio_rows):
    """Include-safe markdown (no headings) so the tables can be pulled
    into paper.qmd via {{< include >}} under Quarto captions."""
    df = pd.DataFrame(ratio_rows)
    df.to_csv(os.path.join(RESULTS, "ablation_ratios.csv"), index=False)

    summary = (df.groupby("mechanism")["ratio_vs_full_ca"]
               .mean().sort_values(ascending=False))
    sig_counts = df[df["significant"] == "yes"].groupby("mechanism").size()

    lines = ["| Mechanism disabled | Mean error ratio (ablated / full CA) "
             "| Significant on (of 6 problems) |",
             "|---|---:|---:|"]
    for mech, ratio in summary.items():
        r = f"{ratio:.3f}" if ratio < 100 else f"{ratio:.1f}"
        lines.append(f"| {MECH_NAME[mech]} | {r} | "
                     f"{int(sig_counts.get(mech, 0))} |")
    with open(TABLE_MD, "w", encoding="utf8") as f:
        f.write("\n".join(lines) + "\n")

    lines = ["| Problem | Mechanism disabled | Ratio | p-value "
             "| Significant |",
             "|---|---|---:|---:|---|"]
    for _, row in df.iterrows():
        r = row["ratio_vs_full_ca"]
        rs = f"{r:.3f}" if r < 100 else f"{r:.1f}"
        lines.append(f"| {row['problem']} | {MECH_NAME[row['mechanism']]} | "
                     f"{rs} | {row['p_value']:.2e} | {row['significant']} |")
    with open(os.path.join(RESULTS, "table_ablation_detail.md"), "w",
              encoding="utf8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
