"""Render paper.qmd safely and publish it to gh-pages.

``quarto publish gh-pages`` and a bare ``quarto render`` (no ``--to``) both
render every format declared in ``paper.qmd`` in one process. This project
used to carry two PDF formats -- a plain one (citeproc) and the Elsevier
camera-ready one (natbib, forced by the vendored extension's Lua filter) --
and rendering them together in one process let something from the second
leak into the first: every citation in that plain PDF came out as an
unresolved ``[?]`` instead of a number, silently, no error or warning in the
render log. The plain PDF was dropped as redundant once Elsevier became the
sole camera-ready target (2026-09-12), which removes this project's only way
to trigger that specific bug -- but this script still renders each format
with its own separate call and verifies the result before publishing, on
principle, since adding a second PDF-producing format back in the future
could reintroduce the same risk.

This script also never calls ``quarto publish``: it copies the already
verified ``_article/`` contents to ``gh-pages`` through a throwaway git
worktree, so quarto never gets a chance to re-render anything at publish
time.

    python src/publish_site.py              # render, verify, publish
    python src/publish_site.py --no-render  # reuse the existing _article/
    python src/publish_site.py --no-push    # render + verify, stop before publishing

Run it from anywhere; paths are resolved against the repository root.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARTICLE = ROOT / "_article"
PAPER_QMD = ROOT / "paper.qmd"

# What actually gets published -- deliberately not the whole of _article/:
# assets/ (unused old figure) and results/ (raw data, not part of the site)
# were never part of the live gh-pages tree and are left out on purpose.
# figures/ is expanded to only the files paper.qmd currently references --
# _article/figures/ is never cleaned between renders, so copying it wholesale
# republishes every figure a past revision ever used, including ones no
# manuscript section still points to (this happened once: a superseded
# flowchart figure that no longer existed in paper.qmd got republished
# because it was still sitting in _article/figures/ from an old render).
PUBLISHED_ITEMS = ["index.html", "paper_files", "paper.pdf"]

STRAY_ROOT_FILES = ["paper.tex", "paper.aux", "paper.bbl", "paper.blg",
                     "elsarticle.cls", "elsarticle-num.bst"]


def referenced_figures() -> list[str]:
    text = PAPER_QMD.read_text(encoding="utf-8")
    names = sorted(set(re.findall(r"figures/([^})\s]+)", text)))
    missing = [n for n in names if not (ARTICLE / "figures" / n).is_file()]
    if missing:
        raise SystemExit(f"figures referenced but not rendered: {missing}")
    return names


def clean_root() -> None:
    """Remove LaTeX intermediates a prior render may have left at the repo root.

    Each `quarto render --to X` call below must start from a clean root, or a
    leftover .aux/.bbl from a previous format's compile can be picked up by
    the next one -- the same class of cross-contamination this script exists
    to avoid, just at the filesystem level instead of within one process.
    """
    for name in STRAY_ROOT_FILES:
        (ROOT / name).unlink(missing_ok=True)


def render() -> None:
    for fmt in ("html", "elsevier-pdf"):
        clean_root()
        print(f"rendering paper.qmd --to {fmt} ...")
        proc = subprocess.run(
            ["quarto", "render", "paper.qmd", "--to", fmt],
            cwd=ROOT, capture_output=True, text=True, shell=(sys.platform == "win32"),
        )
        if proc.returncode != 0:
            tail = "\n".join((proc.stdout + proc.stderr).splitlines()[-25:])
            raise SystemExit(f"quarto render --to {fmt} FAILED\n{tail}")
    clean_root()


def verify_pdf() -> None:
    import fitz  # PyMuPDF

    path = ARTICLE / "paper.pdf"
    if not path.is_file():
        raise SystemExit(f"missing {path.relative_to(ROOT)}; render first")
    doc = fitz.open(path)
    text = "".join(page.get_text() for page in doc)
    bad = text.count("[?")
    print(f"  paper.pdf: {doc.page_count} pages, {bad} unresolved citation marker(s)")
    if bad:
        raise SystemExit(
            f"paper.pdf has {bad} occurrence(s) of '[?' -- unresolved citations. "
            "This is the combined-render bug; re-render with separate --to calls."
        )


def publish() -> None:
    for item in PUBLISHED_ITEMS:
        if not (ARTICLE / item).exists():
            raise SystemExit(f"missing _article/{item}; render first")
    figures = referenced_figures()

    with tempfile.TemporaryDirectory() as tmp:
        wt = Path(tmp) / "gh-pages-wt"
        subprocess.run(["git", "worktree", "add", str(wt), "gh-pages"], cwd=ROOT, check=True)
        try:
            for entry in wt.iterdir():
                if entry.name != ".git":
                    shutil.rmtree(entry) if entry.is_dir() else entry.unlink()
            for item in PUBLISHED_ITEMS:
                src, dst = ARTICLE / item, wt / item
                shutil.copytree(src, dst) if src.is_dir() else shutil.copy2(src, dst)
            (wt / "figures").mkdir()
            for name in figures:
                shutil.copy2(ARTICLE / "figures" / name, wt / "figures" / name)
            (wt / ".nojekyll").touch()

            subprocess.run(["git", "add", "-A"], cwd=wt, check=True)
            if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=wt).returncode == 0:
                print("gh-pages already up to date, nothing to publish")
                return
            subprocess.run(
                ["git", "commit", "-q", "-m", "Publish site (src/publish_site.py)"],
                cwd=wt, check=True,
            )
            subprocess.run(["git", "push", "origin", "gh-pages"], cwd=wt, check=True)
            print("pushed to gh-pages")
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(wt)], cwd=ROOT)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--no-render", action="store_true",
                    help="reuse the existing _article/ instead of re-rendering")
    ap.add_argument("--no-push", action="store_true",
                    help="render and verify, but stop before publishing")
    args = ap.parse_args()

    if not args.no_render:
        render()
    verify_pdf()
    if not args.no_push:
        publish()
    else:
        print("--no-push: stopping before publish")
