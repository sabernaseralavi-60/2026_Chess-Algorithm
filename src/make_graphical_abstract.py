"""Build the Elsevier graphical abstract from two existing manuscript figures.

Elsevier's guidance: minimum 1328 x 531 pixels (w x h), 300 dpi, readable when
shrunk to 200 px high for the table of contents; preferred file types are
TIFF, EPS, PDF or MS Office, though a high-resolution PNG is accepted in
practice by every journal's Editorial Manager (files are categorized by the
uploader, not by extension).

Composition: the "Chess Algorithm" column of the introduction's motivation
figure (concept_motivation.png) as the method half, stacked over the
cross-suite standing figure (standing_ranks.png) as the result half -- two
figures the manuscript already uses, not new artwork, so the abstract can't
claim anything the paper doesn't.

    python src/make_graphical_abstract.py

Writes figures/graphical_abstract.png and .pdf.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FIGURES = ROOT / "figures"

TOP_SRC = FIGURES / "concept_motivation.png"
BOTTOM_SRC = FIGURES / "standing_ranks.png"
OUT_PNG = FIGURES / "graphical_abstract.png"
OUT_PDF = FIGURES / "graphical_abstract.pdf"

WIDTH = 2400            # px; well above Elsevier's 1328 px minimum width
TITLE_H = 130
PAD = 24
INK = (31, 41, 55)      # matches figstyle.INK
RULE = (203, 213, 225)
BG = (255, 255, 255)
DPI = 300

TITLE = "The Chess Algorithm: a ranked, role-differentiated population under adaptive tactical control"
SUBTITLE = ("Best mean Friedman rank among classical baselines on CEC-2017, CEC-2022 and "
            "engineering design; L-SHADE and CMA-ES ahead throughout")


def scaled(path: Path, width: int) -> Image.Image:
    img = Image.open(path).convert("RGB")
    h = round(img.height * width / img.width)
    return img.resize((width, h), Image.LANCZOS)


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(rf"C:\Windows\Fonts\{name}", size)
    except OSError:
        return ImageFont.load_default()


def main() -> None:
    top = scaled(TOP_SRC, WIDTH - 2 * PAD)
    bottom = scaled(BOTTOM_SRC, WIDTH - 2 * PAD)

    total_h = TITLE_H + PAD + top.height + PAD + 2 + PAD + bottom.height + PAD
    canvas = Image.new("RGB", (WIDTH, total_h), BG)
    draw = ImageDraw.Draw(canvas)

    title_font = font("timesbd.ttf", 34)
    sub_font = font("times.ttf", 24)
    draw.text((PAD, 22), TITLE, font=title_font, fill=INK)
    draw.text((PAD, 22 + 46), SUBTITLE, font=sub_font, fill=INK)

    y = TITLE_H
    canvas.paste(top, (PAD, y))
    y += top.height + PAD
    draw.line([(PAD, y), (WIDTH - PAD, y)], fill=RULE, width=2)
    y += 2 + PAD
    canvas.paste(bottom, (PAD, y))

    canvas.save(OUT_PNG, dpi=(DPI, DPI))
    canvas.save(OUT_PDF, resolution=DPI)
    print(f"wrote {OUT_PNG.relative_to(ROOT)} ({canvas.width}x{canvas.height}px @ {DPI}dpi)")
    print(f"wrote {OUT_PDF.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
