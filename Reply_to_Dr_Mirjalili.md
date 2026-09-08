# Reply — Presentation Revision Complete

**From:** Seyedsaber Naseralavi, Ph.D.
Assistant Professor, Department of Civil Engineering
Shahid Bahonar University of Kerman, Kerman, Iran
Email: saber_naseralavi@uk.ac.ir

**To:** Professor Seyedali Mirjalili
Centre for Artificial Intelligence Research and Optimization
Torrens University Australia, Brisbane, Australia

**Date:** September 9, 2026

**Subject:** Re: The Chess Algorithm — presentation revised per your comments

---

Dear Professor Mirjalili,

Thank you for taking the time to read the draft and for such actionable feedback — all three of your comments have been addressed, and I wanted to summarize exactly what changed before you look at the updated version yourself.

**On presenting the results in a more standard format.** I looked closely at the presentation conventions of several of your recent papers (Harris Hawks Optimization, the Mountain Gazelle Optimizer, and a few other current papers in the field) and restructured the results architecture around them: a compact standing table (Friedman rank, rank position, wins/ties/losses) now opens each benchmark suite, ahead of the detailed per-function tables, so a reader sees where CA stands before working through the evidence. A new figure at the end of the analysis section puts the three main suites' rankings side by side in one picture — the honest result that L-SHADE and CMA-ES lead, CA is the best of the remaining six, is now visible at a glance rather than something a reader has to assemble from separate tables.

**On figures in the introduction and the proposed method.** The introduction previously had none; it now opens with a conceptual figure connecting the structure of the optimization problem to CA's two design decisions (heterogeneous roles, adaptive control), followed by a figure mapping each chess piece onto its search operator. The proposed-method section replaces the old generic flowchart with four new figures: one showing a full iteration of the algorithm, one showing the search geometry of each of the five role operators, one showing the geometry of the five tactical operators (en passant, the knight's fork, the royal council, and so on), and one laying out the adaptive controller itself — what it reads, and which tactics each phase activates. None of these are decorative; every point plotted in them is generated directly from the paper's own equations, with a fixed seed, so the figures cannot drift from the mathematics they illustrate.

**On table orientation.** Every comparison table now has algorithms as rows and test functions as columns, as you suggested, with cells reported as mean ± standard deviation and the best mean in each column in bold. The CEC-2017 suite's 29 functions are grouped into the suite's own official categories (unimodal, simple multimodal, hybrid, composition) rather than one unreadable table. The best/worst run values that no longer fit that layout were not dropped — they moved to an appendix, with every relocated cell checked programmatically against the original.

To be direct about scope: none of this touched the science. Every equation, protocol, seed, and result is exactly what it was when you read the draft; a validation script re-checks every number in every new table and figure against the underlying result files before I trust any of it myself, and the negative results — CA losing to L-SHADE and CMA-ES throughout, the record against GA, the loss to PSO on signal timing — are reported with the same honesty as before, now easier to see rather than harder.

I have attached the updated PDF to this email for your convenience; the full source, data, and code are at the same repository as before:

https://github.com/sabernaseralavi-60/2026_Chess-Algorithm

One more thing, on a personal note, since I owe you the explanation directly rather than letting you notice it in passing: you'll see I now sign as Seyedsaber rather than Seyed Saber. I've decided to merge the two the way you write Seyedali — we share the same "Seyed" — and I'll admit the resemblance to your name was very much the point. It is a small gesture, but a sincere one, from someone whose work you have shaped more than you probably know.

I would very much welcome any further comments — on this round of changes or on anything else in the paper — whenever your schedule allows.

With continued gratitude and highest regards,

Seyedsaber Naseralavi, Ph.D.
Assistant Professor of Civil Engineering
Shahid Bahonar University of Kerman
saber_naseralavi@uk.ac.ir | saber.naseralavi@gmail.com
