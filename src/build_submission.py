"""Render the camera-ready manuscript and assemble the Elsevier submission package.

``quarto render paper.qmd --to elsevier-pdf`` writes ``paper.tex`` (kept via
``keep-tex``) next to the source and ``_article/paper.pdf`` -- the Elsevier
build is this project's only PDF format, so it needs no output-file override.
This script drives that render itself, collects the LaTeX source together with
everything it needs into ``submission/<journal>/``, and then re-compiles the
collected copy in a scratch directory, so the package is checked to build on its
own rather than only inside the project tree.

The render is not optional by default and for a reason: rendering any *other*
format of ``paper.qmd`` deletes ``paper.tex``, because only the Elsevier format
sets ``keep-tex``.  Driving the render from here means the package can never be
assembled from a stale or missing intermediate.

    python src/build_submission.py              # render, assemble, verify
    python src/build_submission.py --no-render  # reuse an existing paper.tex
    python src/build_submission.py --no-verify  # skip the standalone re-compile

Run it from anywhere; paths are resolved against the repository root.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TEX = ROOT / "paper.tex"
PDF = ROOT / "_article" / "paper.pdf"
BIB = ROOT / "references.bib"
CLS = ROOT / "_extensions" / "quarto-journals" / "elsevier" / "elsarticle.cls"
BST = ROOT / "_extensions" / "quarto-journals" / "elsevier" / "bib" / "elsarticle-num.bst"

# Journal the package is currently addressed to (Knowledge-Based Systems takes
# elsarticle sources).  Keep in step with journal.name in paper.qmd.
JOURNAL = "knowledge-based-systems"

# name the manuscript carries inside the package
STEM = "chess_algorithm_manuscript"


def referenced_figures(tex: str) -> list[Path]:
    """Return the figure files the LaTeX source actually includes."""
    names = sorted(set(re.findall(r"\{(figures/[^}]+)\}", tex)))
    missing = [n for n in names if not (ROOT / n).is_file()]
    if missing:
        raise SystemExit(f"figures referenced but not on disk: {missing}")
    return [Path(n) for n in names]


def render() -> None:
    """Render the Elsevier format, which is what produces paper.tex."""
    print("rendering paper.qmd --to elsevier-pdf ...")
    proc = subprocess.run(
        ["quarto", "render", "paper.qmd", "--to", "elsevier-pdf"],
        cwd=ROOT, capture_output=True, text=True, shell=(sys.platform == "win32"),
    )
    if proc.returncode != 0:
        tail = "\n".join((proc.stdout + proc.stderr).splitlines()[-25:])
        raise SystemExit(f"quarto render FAILED\n{tail}")


def build(verify: bool = True, do_render: bool = True) -> Path:
    if do_render:
        render()

    for required in (TEX, PDF, BIB, CLS, BST):
        if not required.is_file():
            raise SystemExit(
                f"missing {required.relative_to(ROOT)}; "
                "run `quarto render paper.qmd --to elsevier-pdf` first "
                "(rendering any other format of paper.qmd removes paper.tex)"
            )

    tex = TEX.read_text(encoding="utf-8")
    figures = referenced_figures(tex)

    out = ROOT / "submission" / JOURNAL
    latex = out / "latex-source"
    if latex.exists():
        shutil.rmtree(latex)
    (latex / "figures").mkdir(parents=True)

    # Elsevier compiles the .tex we ship, so the class and bibliography style
    # travel with it rather than being assumed present on their system.
    shutil.copy2(TEX, latex / f"{STEM}.tex")
    shutil.copy2(BIB, latex / "references.bib")
    shutil.copy2(CLS, latex / "elsarticle.cls")
    shutil.copy2(BST, latex / "elsarticle-num.bst")
    for fig in figures:
        shutil.copy2(ROOT / fig, latex / fig)

    out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PDF, out / f"{STEM}.pdf")

    # Standalone copies for Editorial Manager's separate "Graphical Abstract"
    # upload slot, in addition to the one embedded in the manuscript PDF via
    # elsarticle's graphicalabstract environment (journal.graphical-abstract
    # in paper.qmd). Optional: only copied if src/make_graphical_abstract.py
    # has been run.
    ga_png = ROOT / "figures" / "graphical_abstract.png"
    ga_pdf = ROOT / "figures" / "graphical_abstract.pdf"
    if ga_png.is_file():
        shutil.copy2(ga_png, out / "graphical_abstract.png")
    if ga_pdf.is_file():
        shutil.copy2(ga_pdf, out / "graphical_abstract.pdf")

    if verify:
        verify_standalone(latex)

    archive = out / f"{STEM}_latex_source.zip"
    if archive.exists():
        archive.unlink()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(latex.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(latex))

    n_files = sum(1 for p in latex.rglob("*") if p.is_file())
    print(f"package:  {out.relative_to(ROOT)}")
    print(f"latex:    {n_files} files ({len(figures)} figures)")
    print(f"archive:  {archive.relative_to(ROOT)} "
          f"({archive.stat().st_size / 1e6:.1f} MB)")
    return out


def verify_standalone(latex: Path) -> None:
    """Compile the collected sources in a scratch copy and check the log."""
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "build"
        shutil.copytree(latex, work)
        proc = subprocess.run(
            ["latexmk", "-lualatex", "-interaction=nonstopmode", f"{STEM}.tex"],
            cwd=work, capture_output=True, text=True,
        )
        log_path = work / f"{STEM}.log"
        log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else ""

        if proc.returncode != 0 or not (work / f"{STEM}.pdf").is_file():
            tail = "\n".join((proc.stdout + proc.stderr).splitlines()[-25:])
            raise SystemExit(f"standalone compile FAILED\n{tail}")

        problems = {
            "undefined citations": len(re.findall(r"Citation .* undefined", log)),
            "undefined references": len(re.findall(r"Reference .* undefined", log)),
            "missing characters": log.count("Missing character"),
        }
        overfull = [float(m) for m in re.findall(r"Overfull \\hbox \(([0-9.]+)pt", log)]
        pages = re.search(r"Output written on .*? \((\d+) pages", log)

        print("standalone compile: OK"
              f" ({pages.group(1) if pages else '?'} pages)")
        for label, count in problems.items():
            print(f"  {label:22s} {count}")
        print(f"  {'overfull hboxes':22s} {len(overfull)}"
              f" (max {max(overfull):.1f}pt)" if overfull else
              f"  {'overfull hboxes':22s} 0")

        if any(problems.values()):
            raise SystemExit("standalone compile produced unresolved references or glyphs")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--no-verify", action="store_true",
                    help="skip the standalone re-compile check")
    ap.add_argument("--no-render", action="store_true",
                    help="reuse the existing paper.tex instead of re-rendering")
    args = ap.parse_args()
    build(verify=not args.no_verify, do_render=not args.no_render)
