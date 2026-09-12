---
format:
  pdf:
    documentclass: scrartcl
    papersize: a4
    geometry: [margin=2.5cm]
    fontsize: 11pt
    colorlinks: true
---

| **The Editor-in-Chief**
| *Advanced Engineering Informatics*

12 September 2026

**Re: submission of the manuscript "The Chess Algorithm: A Novel Metaheuristic Optimization Technique with Applications in Transportation Network Engineering"**

Dear Editor,

We submit the manuscript named above for consideration as a full-length research article in *Advanced Engineering Informatics*.

The paper introduces the Chess Algorithm (CA), a population-based metaheuristic in which the population is deliberately heterogeneous: agents are ranked each iteration, assigned the roles of King, Queen, Rook, Bishop, Knight and Pawn, and moved by an operator abstracted from the geometry of the corresponding piece, while a lightweight state machine reads the divergence, initiative and local-search success of the population and selects which strategic mechanisms are active.

We are aware that the literature on metaphor-named metaheuristics has drawn severe and largely justified criticism, and we would rather meet that criticism directly than work around it. The paper is built so that the metaphor carries no explanatory weight. Every mechanism of CA is specified mathematically, mapped in a dedicated table onto the established operator family it belongs to with the canonical citation, and then measured in isolation through a per-mechanism ablation. We believe this transparency-first treatment, rather than the algorithm alone, is the contribution most relevant to your readership.

Two features of the evaluation may be of particular interest.

First, the comparison is deliberately unfavourable to our own method. Alongside GA, PSO, SA, GWO and WOA, the roster includes the competition-grade optimizers L-SHADE and CMA-ES. CA obtains the best mean Friedman rank among the classical and widely used baselines on all three standard suites, but L-SHADE and CMA-ES rank ahead of CA on every problem class we tested, and we report this throughout without qualification. The ablation then explains the ordering rather than merely recording it: the two mechanisms that carry most of CA's measured performance are a success-rule step-size adaptation and a differential mutation, and L-SHADE and CMA-ES are the competition-refined members of exactly those two families.

Second, in the course of validating the benchmark study we ran a two-library data-integrity audit and identified six defective function implementations in a widely used third-party CEC-2017 port, all six of which we restored from an independent implementation carrying the official reference data. The raw statistics behind every exclusion are committed alongside the results, so the audit can be re-run rather than taken on trust.

The work is evaluated on six classical functions in 30 dimensions, on all 29 usable CEC-2017 functions, on CEC-2022 at both official dimensionalities, on seven constrained engineering design problems, and on two transportation problems: arterial signal coordination and continuous berth allocation. The engineering and transportation studies, together with the reproducibility apparatus, are why we believe the manuscript belongs in *Advanced Engineering Informatics* rather than in a purely algorithmic venue.

All source code, experiment scripts and raw results are maintained under version control for exact reproducibility, with fixed random seeds throughout; every number reported in the paper corresponds to a committed output. The complete repository will be made publicly available at <https://github.com/sabernaseralavi-60/2026_Chess-Algorithm> upon acceptance.

We confirm that this manuscript is original, has not been published previously, and is not under consideration for publication elsewhere. All authors have read and approved the submitted version and declare no competing interests.

Thank you for your time and consideration.

Yours sincerely,

| **Seyedsaber Naseralavi**, corresponding author
| Department of Civil Engineering, Faculty of Engineering
| Shahid Bahonar University of Kerman, Kerman, Iran
| `saber_naseralavi@uk.ac.ir`
|
| on behalf of the authors: Seyedsaber Naseralavi and Seyedali Mirjalili
