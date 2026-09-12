# Submission package

Camera-ready material for the Chess Algorithm manuscript, in Elsevier
`elsarticle` format, prepared for the submission order agreed with the
co-author:

1. **Advanced Engineering Informatics** (Elsevier) — prepared, in
   `advanced-engineering-informatics/`
2. **Knowledge-Based Systems** (Elsevier) — same LaTeX source, see *Fallbacks*
3. **Cluster Computing** (**Springer**) — needs a different template, see
   *Fallbacks*

## How it is built

The manuscript is one source, `paper.qmd` at the repository root, which renders
to three formats. The Elsevier build is the third, and one command does all of
it:

```sh
python src/build_submission.py
```

That renders `paper.qmd --to elsevier-pdf`, collects the LaTeX source, the
bibliography, the class and bibliography-style files and only the 22 figures the
source actually includes, then **re-compiles the collected copy in a scratch
directory** and fails if the log shows an undefined citation or reference or a
dropped glyph. The package is therefore checked to build on its own, which is
what Elsevier's system does with it. Last verified run: 55 pages, 0 undefined
citations, 0 undefined references, 0 missing characters, 20 overfull hboxes at
most 4.1 pt (≈1.4 mm, inside the wide comparison tables).

The script drives the render itself rather than trusting you to have run it,
because rendering any *other* format of `paper.qmd` deletes `paper.tex` — only
the Elsevier format sets `keep-tex`. Pass `--no-render` to reuse an existing
`paper.tex`, `--no-verify` to skip the re-compile.

Everything the script generates is gitignored, in the same way `_article/` is:
the committed things are the manuscript source and these documents, and the
package is rebuilt from them. **Tag the commit you submit from** so the exact
package can be regenerated later:

```sh
git tag submission-aei-2026-09 && git push origin submission-aei-2026-09
```

Format details live in the `elsevier-pdf` block of `paper.qmd`:
`elsarticle` with `preprint,3p,onecolumn,number`, `elsarticle-num` bibliography
style, journal name set for the running footer. Single column is deliberate —
the transposed comparison tables carry one column per test function and do not
survive a two-column layout.

## What is in `advanced-engineering-informatics/`

| File | Upload as |
|---|---|
| `chess_algorithm_manuscript.pdf` | Manuscript (PDF) |
| `chess_algorithm_manuscript_latex_source.zip` | LaTeX source (26 files) |
| `latex-source/` | the unzipped same, for inspection |
| `cover_letter.md` | Cover letter |
| `highlights.md` | Highlights |
| `declaration_of_interest.md` | Declaration of Interest + CRediT |
| `suggested_reviewers.md` | working notes — **not** uploaded |

The CRediT statement, the competing-interest declaration, the generative-AI
declaration and the data-availability statement are also inside the manuscript
itself, before the appendix, which is where Elsevier expects them.

Render the three `.md` documents to PDF if Editorial Manager wants files rather
than pasted text:

```sh
quarto render submission/advanced-engineering-informatics/cover_letter.md
```

## Open items — these need you, not the build

1. **Dr. Mirjalili's editorial roles.** He sits on the editorial boards of
   several optimization journals. If he holds a role at the journal being
   submitted to, Elsevier requires it to be declared at submission and the paper
   is handled by an independent editor. Check this for Advanced Engineering
   Informatics *and* for Knowledge-Based Systems before submitting, and amend
   `declaration_of_interest.md` if it applies.
2. **Cover letter salutation.** It opens with "Dear Editor". Personalise it with
   the current Editor-in-Chief's name if you would rather.
3. **Suggested reviewers.** `suggested_reviewers.md` has candidates but
   deliberately no email addresses. Verify affiliations and look up institutional
   emails before entering them.
4. **ORCID and institutional details** for both authors are entered in Editorial
   Manager, not in the files here.
5. **Confirm the author note is gone.** The manuscript previously carried a note
   saying Dr. Mirjalili's co-authorship was pending his consent. His approval to
   proceed removed the reason for it and it has been deleted; confirm you are
   content with that before submitting.

## Fallbacks

**Knowledge-Based Systems** is also Elsevier and also takes `elsarticle`. The
same LaTeX source submits unchanged. Change the journal name so the running
footer is right, re-render, and rebuild into a new folder:

```yaml
# paper.qmd, elsevier-pdf format
journal:
  name: "Knowledge-Based Systems"
```

then set `JOURNAL = "knowledge-based-systems"` in `src/build_submission.py` and
rerun it.

Re-point the cover letter at the new journal as well; the scope paragraph argues
specifically for Advanced Engineering Informatics and should be rewritten rather
than have the title swapped.

**Cluster Computing is published by Springer, not Elsevier.** `elsarticle` does
not apply. It needs the Springer Nature LaTeX template (`sn-jnl.cls`), which is
a different front-matter structure, a different bibliography style and a
different figure convention. If the paper reaches that point, the manuscript
body and figures carry over but the front matter has to be rebuilt — budget for
that rather than assuming the package here is reusable.
