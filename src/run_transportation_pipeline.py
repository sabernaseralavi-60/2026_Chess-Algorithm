"""
run_transportation_pipeline.py
===============================
Single reproducible entry point for the transportation comparison of
Sec. 9 of the manuscript ("Extended Comparison on Independent
Implementations").

The problem this closes
------------------------
That section's three result tables (`table_mealpy_signal.md`,
`table_mealpy_berth.md`, `table_berth_gap.md`) and the archive behind
them (`raw_mealpy.npz`) are built by **two** scripts, in a fixed order,
because the second depends on a file the first writes:

    1. mealpy_comparison.py        -- CA + six third-party mealpy
                                       algorithms; writes the tables
                                       and raw_mealpy.npz from scratch
    2. sota_addon_run.py --suite transport
                                    -- reads raw_mealpy.npz, adds
                                       L-SHADE and CMA-ES, and rewrites
                                       the same three tables in place

Running step 1 without step 2 produces tables that silently omit the
two competition-grade baselines the manuscript reports throughout
Sec. 9 -- there is no error, just seven rows where the paper expects
nine. That happened once during the 2026-09 presentation revision
(see VALIDATION_REPORT.md, "Status of the mealpy re-run") because
nothing in the repository stated the dependency.

What this script does
----------------------
It is now the only supported way to (re)produce Sec. 9's tables:

    1. runs mealpy_comparison.py
    2. runs sota_addon_run.py --suite transport
    3. hard-validates that every transportation table contains both
       an L-SHADE and a CMA-ES row -- and exits non-zero, loudly, if
       either script failed to leave one there
    4. reports the paths of the tables and figures the pipeline
       produced

Usage
-----
    python src/run_transportation_pipeline.py            # full run
    python src/run_transportation_pipeline.py --smoke     # fast smoke test
    python src/run_transportation_pipeline.py --validate-only
        # skip both experiments; only run step 3 against whatever
        # tables are already on disk (use this to check a re-run someone
        # else performed, or the committed results/ directory)
"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
RESULTS = os.path.join(ROOT, "results")
FIGURES = os.path.join(ROOT, "figures")

REQUIRED_ALGOS = ["L-SHADE", "CMA-ES"]
TRANSPORT_TABLES = ["table_mealpy_signal.md", "table_mealpy_berth.md",
                    "table_berth_gap.md"]
TRANSPORT_FIGURES = ["mealpy_convergence.png", "berth_best_plan.png"]


def _run(cmd, **kw):
    print(f"\n$ {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, cwd=SRC, **kw)
    if result.returncode != 0:
        sys.exit(
            f"\nFAILED: {' '.join(cmd)} exited {result.returncode}. "
            "The transportation pipeline stops here -- rerun after "
            "fixing the underlying error rather than proceeding to "
            "the next step on partial output.")


def validate_transport_tables():
    """Hard check: every transportation table must carry a row for
    every algorithm in REQUIRED_ALGOS. Raises SystemExit(1) -- rather
    than warning -- if one is missing, so a broken pipeline cannot
    pass silently into the manuscript."""
    problems = []
    for name in TRANSPORT_TABLES:
        path = os.path.join(RESULTS, name)
        if not os.path.exists(path):
            problems.append(f"{name}: file does not exist")
            continue
        text = open(path, encoding="utf8").read()
        rows = [line.split("|")[1].strip()
                for line in text.splitlines()
                if line.startswith("|") and not set(line) <= set("|-: ")]
        rows = rows[1:]  # drop the header row
        missing = [a for a in REQUIRED_ALGOS if a not in rows]
        if missing:
            problems.append(
                f"{name}: missing row(s) for {', '.join(missing)} "
                f"(found rows: {', '.join(rows)}) -- run "
                "`sota_addon_run.py --suite transport` after "
                "`mealpy_comparison.py`, not instead of it")
    for name in TRANSPORT_FIGURES:
        path = os.path.join(FIGURES, name)
        if not os.path.exists(path):
            problems.append(f"{name}: figure does not exist")

    if problems:
        sys.exit(
            "Transportation pipeline validation FAILED:\n  - "
            + "\n  - ".join(problems)
        )
    print("Transportation pipeline validation PASSED: "
          f"{', '.join(REQUIRED_ALGOS)} present in all "
          f"{len(TRANSPORT_TABLES)} tables; all "
          f"{len(TRANSPORT_FIGURES)} figures present.")


def main():
    smoke = "--smoke" in sys.argv
    validate_only = "--validate-only" in sys.argv

    if not validate_only:
        step1 = [sys.executable, "mealpy_comparison.py"]
        step2 = [sys.executable, "sota_addon_run.py", "--suite",
                 "transport"] + (["--smoke"] if smoke else [])
        # mealpy_comparison.py has no --smoke switch of its own; a
        # smoke run is meant only to exercise the dependency chain,
        # not to reproduce a full 30-run experiment
        _run(step1)
        _run(step2)

    validate_transport_tables()

    print("\nTransportation pipeline complete. Outputs:")
    for name in TRANSPORT_TABLES:
        print(f"  results/{name}")
    for name in TRANSPORT_FIGURES:
        print(f"  figures/{name}")


if __name__ == "__main__":
    main()
