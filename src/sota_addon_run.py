"""
sota_addon_run.py
===================
Step A2 of PLAN_cec2022_and_reply.md: add L-SHADE and CMA-ES to the three
already-published suites, without disturbing the existing six-algorithm
results:

    (i)   CEC-2017, the 24 validated functions, D=30, SEED0=20260713
          (matches src/cec2017_full_run.py's protocol).
    (ii)  7 engineering design problems, SEED0=20260713
          (matches src/engineering_full_run.py's protocol).
    (iii) Transportation P1 (signal) / P2 (berth), SEED0=20260705, T=300
          (matches src/mealpy_comparison.py's protocol).

Existing stats/wilcoxon/raw files are extended in place: any pre-existing
L-SHADE/CMA-ES rows are dropped and replaced (idempotent reruns), every
other row/key is preserved untouched. A one-time backup of the pre-merge
files is written to results/_backup_pre_sota/ (only if not already there).

Usage:
    python src/sota_addon_run.py               # all three suites
    python src/sota_addon_run.py --suite cec2017
    python src/sota_addon_run.py --suite engineering
    python src/sota_addon_run.py --suite transport
    python src/sota_addon_run.py --smoke        # 2 cells/suite, 3 runs, 20 iters
"""

import os
import sys
import shutil
import time
import warnings

import numpy as np
import pandas as pd
from scipy.stats import ranksums

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sota_algorithms import run_lshade, run_cmaes
from engineering_problems import ENGINEERING
from opfunu.cec_based import cec2017

warnings.filterwarnings("ignore")

SMOKE = "--smoke" in sys.argv
if "--suite" in sys.argv:
    SUITES = [sys.argv[sys.argv.index("--suite") + 1]]
else:
    SUITES = ["cec2017", "engineering", "transport"]

NEW_ALGOS = ["L-SHADE", "CMA-ES"]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
BACKUP = os.path.join(RESULTS, "_backup_pre_sota")


def backup_once(names):
    os.makedirs(BACKUP, exist_ok=True)
    for name in names:
        src = os.path.join(RESULTS, name)
        dst = os.path.join(BACKUP, name)
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)


def run_new_algo(aname, f_vec, dim, pop, iters, seed, budget, return_x=False):
    if aname == "L-SHADE":
        return run_lshade(f_vec, 0.0, 1.0, dim, pop, iters, seed,
                          max_evals=budget, return_x=return_x)
    return run_cmaes(f_vec, 0.0, 1.0, dim, pop, iters, seed,
                     return_x=return_x)


# ----------------------------------------------------------------------
# (i) CEC-2017
# ----------------------------------------------------------------------
def addon_cec2017():
    POP = 30
    ITERS = 20 if SMOKE else 500
    RUNS = 3 if SMOKE else 30
    SEED0 = 20260713
    BUDGET = POP * ITERS + 500

    stats_csv = os.path.join(RESULTS, "cec2017_stats.csv")
    wilc_csv = os.path.join(RESULTS, "cec2017_wilcoxon.csv")
    raw_npz = os.path.join(RESULTS, "raw_cec2017.npz")
    backup_once(["cec2017_stats.csv", "cec2017_wilcoxon.csv", "raw_cec2017.npz"])

    stats = pd.read_csv(stats_csv)
    wilc = pd.read_csv(wilc_csv)
    raw = dict(np.load(raw_npz))

    funcs = sorted(stats["func"].unique(), key=lambda s: int(s[1:]))
    if SMOKE:
        funcs = funcs[:2]

    stats = stats[~stats["algo"].isin(NEW_ALGOS)]
    wilc = wilc[~wilc["competitor"].isin(NEW_ALGOS)]
    stats_rows = stats.to_dict("records")
    wilc_rows = wilc.to_dict("records")

    t_start = time.time()
    for fi, label in enumerate(funcs):
        n = int(label[1:])
        prob = getattr(cec2017, f"F{n}2017")(ndim=30)
        lo, sp = prob.lb.copy(), prob.ub - prob.lb

        def f_vec(U, lo=lo, sp=sp, prob=prob):
            Z = lo + sp * np.clip(np.atleast_2d(U), 0.0, 1.0)
            return np.array([prob.evaluate(z) for z in Z])

        ca_finals = raw[f"{label}__CA__finals"]
        for aname in NEW_ALGOS:
            t0 = time.time()
            vals = np.empty(RUNS)
            curves = np.empty((RUNS, ITERS))
            for r in range(RUNS):
                bf, curve = run_new_algo(aname, f_vec, 30, POP, ITERS,
                                         SEED0 + r, BUDGET)
                vals[r] = bf - prob.f_global
                curves[r] = curve - prob.f_global
            raw[f"{label}__{aname}__finals"] = vals
            raw[f"{label}__{aname}__med"] = np.median(curves, axis=0)
            raw[f"{label}__{aname}__q25"] = np.quantile(curves, .25, axis=0)
            raw[f"{label}__{aname}__q75"] = np.quantile(curves, .75, axis=0)
            stats_rows.append(dict(
                func=label, algo=aname, best=vals.min(), mean=vals.mean(),
                std=vals.std(), median=np.median(vals), worst=vals.max()))
            _, p = ranksums(ca_finals, vals)
            direction = "better" if ca_finals.mean() < vals.mean() else "worse"
            wilc_rows.append(dict(func=label, competitor=aname, p_value=p,
                                  v3_mean_direction=direction,
                                  significant="yes" if p < .05 else "no"))
            print(f"[cec2017 {fi+1:2d}/{len(funcs)}] {label:4s} {aname:8s} "
                  f"mean={vals.mean():12.5g} std={vals.std():10.4g} "
                  f"best={vals.min():12.5g} ({time.time()-t0:5.1f}s)",
                  flush=True)

        pd.DataFrame(stats_rows).to_csv(stats_csv, index=False)
        pd.DataFrame(wilc_rows).to_csv(wilc_csv, index=False)
        np.savez_compressed(raw_npz, **raw)

    print(f"[cec2017 addon] wall time: {(time.time()-t_start)/60:.1f} min",
          flush=True)


# ----------------------------------------------------------------------
# (ii) Engineering
# ----------------------------------------------------------------------
def addon_engineering():
    POP = 30
    ITERS = 20 if SMOKE else 500
    RUNS = 3 if SMOKE else 30
    SEED0 = 20260713
    BUDGET = POP * ITERS + 500

    stats_csv = os.path.join(RESULTS, "engineering_stats.csv")
    wilc_csv = os.path.join(RESULTS, "engineering_wilcoxon.csv")
    raw_npz = os.path.join(RESULTS, "raw_engineering.npz")
    backup_once(["engineering_stats.csv", "engineering_wilcoxon.csv",
                 "raw_engineering.npz"])

    stats = pd.read_csv(stats_csv)
    wilc = pd.read_csv(wilc_csv)
    raw = dict(np.load(raw_npz))

    problems = list(ENGINEERING.items())
    if SMOKE:
        problems = problems[:2]

    stats = stats[~stats["algo"].isin(NEW_ALGOS)]
    wilc = wilc[~wilc["competitor"].isin(NEW_ALGOS)]
    stats_rows = stats.to_dict("records")
    wilc_rows = wilc.to_dict("records")

    t_start = time.time()
    for pname, (fun, lb, ub, dim, f_ref) in problems:
        span = ub - lb

        def f_vec(U, lb=lb, span=span, fun=fun):
            Z = lb + span * np.clip(np.atleast_2d(U), 0.0, 1.0)
            return fun(Z)

        ca_finals = raw[f"{pname}__CA__finals"]
        for aname in NEW_ALGOS:
            t0 = time.time()
            vals = np.empty(RUNS)
            curves = np.empty((RUNS, ITERS))
            bx_best, bf_best = None, np.inf
            for r in range(RUNS):
                bx, bf, curve = run_new_algo(aname, f_vec, dim, POP, ITERS,
                                             SEED0 + r, BUDGET, return_x=True)
                vals[r] = bf
                curves[r] = curve
                if bf < bf_best:
                    bf_best, bx_best = bf, bx
            raw[f"{pname}__{aname}__finals"] = vals
            raw[f"{pname}__{aname}__med"] = np.median(curves, axis=0)
            raw[f"{pname}__{aname}__q25"] = np.quantile(curves, .25, axis=0)
            raw[f"{pname}__{aname}__q75"] = np.quantile(curves, .75, axis=0)
            raw[f"{pname}__{aname}__bestx"] = bx_best
            stats_rows.append(dict(
                problem=pname, algo=aname, best=vals.min(), mean=vals.mean(),
                std=vals.std(), median=np.median(vals), worst=vals.max(),
                f_ref=f_ref))
            _, p = ranksums(ca_finals, vals)
            direction = "better" if ca_finals.mean() < vals.mean() else "worse"
            wilc_rows.append(dict(problem=pname, competitor=aname, p_value=p,
                                  v3_mean_direction=direction,
                                  significant="yes" if p < .05 else "no"))
            print(f"[engineering] {pname:15s} {aname:8s} "
                  f"mean={vals.mean():14.8g} std={vals.std():10.4g} "
                  f"best={vals.min():14.8g} ({time.time()-t0:5.1f}s)",
                  flush=True)

        pd.DataFrame(stats_rows).to_csv(stats_csv, index=False)
        pd.DataFrame(wilc_rows).to_csv(wilc_csv, index=False)
        np.savez_compressed(raw_npz, **raw)

    print(f"[engineering addon] wall time: {(time.time()-t_start)/60:.1f} min",
          flush=True)


# ----------------------------------------------------------------------
# (iii) Transport (mealpy_comparison protocol)
# ----------------------------------------------------------------------
def addon_transport():
    import mealpy_comparison as mc

    POP, ITERS = mc.POP, mc.ITERS
    RUNS = 3 if SMOKE else 30
    SEED0 = mc.SEED0
    BUDGET = POP * ITERS + 500

    raw_npz = os.path.join(RESULTS, "raw_mealpy.npz")
    backup_once(["raw_mealpy.npz", "table_mealpy_signal.md",
                 "table_mealpy_berth.md", "table_berth_gap.md"])
    raw = dict(np.load(raw_npz))

    all_finals = {}
    all_best_x = {}
    t_start = time.time()
    for pname, spec in mc.PROBLEMS.items():
        f_vec, _ = mc.make_unit(spec["fun"], spec["lb"], spec["ub"])
        dim = spec["dim"]

        finals = {}
        best_x = {}
        for aname in NEW_ALGOS:
            t0 = time.time()
            vals = np.empty(RUNS)
            bx_best, bf_best = None, np.inf
            for r in range(RUNS):
                bx, bf, _ = run_new_algo(aname, f_vec, dim, POP, ITERS,
                                         SEED0 + r, BUDGET, return_x=True)
                vals[r] = bf
                if bf < bf_best:
                    bf_best, bx_best = bf, bx
            finals[aname] = vals
            best_x[aname] = bx_best
            raw[f"{pname}__{aname}"] = vals
            print(f"[transport] {pname:7s} {aname:8s} "
                  f"mean={vals.mean():.4f} std={vals.std():.4f} "
                  f"best={vals.min():.4f} ({time.time()-t0:.1f}s)",
                  flush=True)
        all_finals[pname] = finals
        all_best_x[pname] = best_x
        np.savez_compressed(raw_npz, **raw)

    _rewrite_transport_tables(all_finals, all_best_x, raw)
    print(f"[transport addon] wall time: {(time.time()-t_start)/60:.1f} min",
          flush=True)


def _rewrite_transport_tables(all_finals, all_best_x, raw):
    """Extend table_mealpy_{signal,berth}.md and table_berth_gap.md with
    the two new algorithms, preserving the existing rows/algorithms."""
    import mealpy_comparison as mc
    from scipy import stats as sstats

    for pname, spec in mc.PROBLEMS.items():
        fmt = spec["fmt"]
        old_algos = mc.ALL_ALGS
        finals = {a: raw[f"{pname}__{a}"] for a in old_algos}
        finals.update(all_finals[pname])
        algos = old_algos + NEW_ALGOS

        ca = finals["CA"]
        best_mean = min(finals[a].mean() for a in algos)
        lines = ["| Algorithm | Mean | Std | Best | Worst | p-value (vs CA) "
                 "| Result (α = 0.05) |",
                 "|---|---:|---:|---:|---:|---:|---|"]
        for a in algos:
            B = finals[a]
            m = fmt.format(B.mean())
            if np.isclose(B.mean(), best_mean, rtol=1e-12):
                m = f"**{m}**"
            if a == "CA":
                pcol, verdict = "—", "—"
            else:
                _, p = sstats.ranksums(ca, B)
                pcol = f"{p:.3e}"
                verdict = ("CA better" if (p < .05 and ca.mean() < B.mean())
                           else "CA worse" if p < .05 else "not significant")
            lines.append(f"| {a} | {m} | {fmt.format(B.std())} | "
                         f"{fmt.format(B.min())} | {fmt.format(B.max())} | "
                         f"{pcol} | {verdict} |")
        with open(os.path.join(RESULTS, f"table_mealpy_{pname}.md"), "w",
                  encoding="utf8") as f:
            f.write("\n".join(lines) + "\n")

        if pname == "berth":
            # best_x for the original 7 algorithms was never persisted to
            # disk (mealpy_comparison.py only saves `finals`), so their
            # gap-table rows are preserved verbatim from the existing file
            # rather than recomputed; only the 2 new algorithms are added.
            old_rows = {}
            gap_path = os.path.join(RESULTS, "table_berth_gap.md")
            if os.path.exists(gap_path):
                with open(gap_path, encoding="utf8") as f:
                    old_lines = [ln for ln in f.read().splitlines() if ln]
                for ln in old_lines[2:]:
                    algo = ln.split("|")[1].strip()
                    old_rows[algo] = ln

            span = mc.BERTH_UB - mc.BERTH_LB
            lines = ["| Algorithm | Best objective (min) | Gap to optimum "
                     "| Overlap of best plan (min·m) |",
                     "|---|---:|---:|---:|"]
            for a in algos:
                if a in NEW_ALGOS:
                    bx = all_best_x[pname][a]
                    z = mc.BERTH_LB + span * np.clip(bx, 0, 1)
                    ov = mc.berth_overlap(z)
                    bf = finals[a].min()
                    gap = 100.0 * (bf - mc.BERTH_OPT) / mc.BERTH_OPT
                    lines.append(f"| {a} | {bf:.1f} | {gap:.2f}% | {ov:.1f} |")
                elif a in old_rows:
                    lines.append(old_rows[a])
            with open(gap_path, "w", encoding="utf8") as f:
                f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    t0 = time.time()
    if "cec2017" in SUITES:
        addon_cec2017()
    if "engineering" in SUITES:
        addon_engineering()
    if "transport" in SUITES:
        addon_transport()
    print(f"\nTotal A2 wall time: {(time.time()-t0)/60:.1f} min", flush=True)
