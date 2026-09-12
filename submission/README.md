# Submission package

Camera-ready material for the Chess Algorithm manuscript, in Elsevier
`elsarticle` format, addressed to **Knowledge-Based Systems** (Elsevier). The
package lives in `knowledge-based-systems/`.

## How it is built

The manuscript is one source, `paper.qmd` at the repository root, which renders
to three formats. The Elsevier build is the third, and one command does all of
it:

```sh
python src/build_submission.py
```

That renders `paper.qmd --to elsevier-pdf`, collects the LaTeX source, the
bibliography, the class and bibliography-style files and only the figures the
source actually includes, then **re-compiles the collected copy in a scratch
directory** and fails if the log shows an undefined citation or reference or a
dropped glyph. The package is therefore checked to build on its own, which is
what Elsevier's system does with it.

The script drives the render itself rather than trusting you to have run it,
because rendering any *other* format of `paper.qmd` deletes `paper.tex` — only
the Elsevier format sets `keep-tex`. Pass `--no-render` to reuse an existing
`paper.tex`, `--no-verify` to skip the re-compile.

Everything the script generates is gitignored, in the same way `_article/` is:
the committed things are the manuscript source and the documents below, and the
package is rebuilt from them.

Format details live in the `elsevier-pdf` block of `paper.qmd`: `elsarticle`
with `preprint,3p,onecolumn,number`, `elsarticle-num` bibliography style,
journal name set for the running footer. Single column is deliberate — the
transposed comparison tables carry one column per test function and do not
survive a two-column layout.

## What is in `knowledge-based-systems/`

| File | Upload as |
|---|---|
| `chess_algorithm_manuscript.pdf` | Manuscript (PDF) |
| `chess_algorithm_manuscript_latex_source.zip` | LaTeX source |
| `latex-source/` | the unzipped same, for inspection |
| `cover_letter.md` | Cover letter |
| `highlights.md` | Highlights (5 bullets, each within the 85-character limit) |
| `declaration_of_interest.md` | Declaration of Interest + CRediT |
| `graphical_abstract.png` / `.pdf` | Graphical abstract, if the form has a slot (optional for this journal) |

The CRediT statement, the competing-interest declaration, the generative-AI
declaration and the data-availability statement are also inside the manuscript
itself, before the appendix, which is where Elsevier expects them.

Render the three `.md` documents to PDF if Editorial Manager wants files rather
than pasted text:

```sh
quarto render submission/knowledge-based-systems/cover_letter.md
```

## Open items — these need you, not the build

1. **Cover letter salutation.** It opens with "Dear Editor". Personalise it with
   the current Editor-in-Chief's name if you would rather; check the journal's
   page for who that is now.
2. **Dr. Mirjalili's editorial roles.** Declare it at submission if he holds any
   editorial role at Knowledge-Based Systems. An earlier web search found board
   memberships elsewhere but none at this journal; that is not authoritative, so
   confirm with him directly.
3. **ORCID and institutional details** for both authors are entered in Editorial
   Manager, not in the files here.
4. **Suggested reviewers** are left blank. Most Elsevier journals treat the
   field as optional.

## Fallback: Cluster Computing

**Cluster Computing is published by Springer, not Elsevier.** `elsarticle` does
not apply. It needs the Springer Nature LaTeX template (`sn-jnl.cls`), which is
a different front-matter structure, a different bibliography style and a
different figure convention. The manuscript body and figures carry over but the
front matter has to be rebuilt.
