# AEI Editorial Manager: "Specific contributions" comments box

Pasted verbatim into the required comments field on the submission form
("Papers published in Advanced Engineering Informatics must make a
contribution to the core body of knowledge..."). 2182 characters, well under
the 20000-character limit.

---

This paper's contribution to engineering informatics is methodological transparency in metaheuristic design, applied to two real network-engineering problems, not a claim of a new dominant optimizer.

The literature on metaphor-named metaheuristics (Grey Wolf, Whale, Ant Lion, and dozens of others building on the swarm-intelligence line this paper also draws from) has drawn severe and largely justified criticism (Sorensen, 2015) for repackaging established operators under new vocabulary without advancing the underlying science. We accept that criticism and build the response into the study itself, which is where this paper differs from prior work in the same space: every mechanism of the proposed Chess Algorithm is specified mathematically, mapped explicitly onto its established operator family (success-rule step-size adaptation, differential mutation, arithmetic recombination) with the canonical citation, and then measured in isolation through a twelve-mechanism ablation. That ablation is the paper's central engineering-informatics contribution: it shows that only two mechanisms carry the algorithm's measured performance, and that these are exactly the operator families that the competition-grade optimizers L-SHADE and CMA-ES implement in fully adaptive form, which is why those two outperform it throughout. This turns a ranking exercise into a mechanistic explanation, a distinction we believe matters more to the field's advancement than the ranking itself.

The paper also reports a two-library data-integrity audit that identified six defective function implementations in a widely used third-party CEC-2017 benchmark port, restored from an independent reference implementation and committed for reproducibility, a methodological check we believe the field's benchmarking practice needs more of, not less.

Finally, the algorithm is evaluated on two real engineering-informatics problems, arterial traffic-signal coordination and continuous berth allocation, rather than synthetic functions alone, so its standing is reported against both classical metaheuristics and, where they apply, third-party implementations from independent optimization libraries.
