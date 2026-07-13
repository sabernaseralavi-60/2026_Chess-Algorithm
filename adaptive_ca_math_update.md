# The Adaptive Chess Algorithm (CA-v3): Mathematical Formulation and Empirical Validation

*Draft methodology update for Section 2 (and the corresponding parts of Sections 3–6) of "The Chess Algorithm: A Novel Metaheuristic Optimization Technique with Applications in Transportation Network Engineering." Written to be copy-pasted into `paper.qmd`; equation labels follow the paper's existing `{#eq-name}` Quarto cross-reference convention, and the LaTeX tables referenced below live in `results/latex_tables_final.tex`.*

---

## 1. From a Fixed Repertoire to an Adaptive One

The original Chess Algorithm (CA-v1, published) and its refinement (CA-v2) apply the same fixed set of operators — Queen, Rook, Bishop, Knight, and Pawn moves; pinning; sacrifice; en passant; castling; threefold repetition — identically at every iteration, differing only through the deterministic schedules $a(t)$, $p_{\text{pin}}(t)$, and $\theta(t)$. This is faithful to the *mechanics* of chess but not to how a strong player actually behaves: a grandmaster does not play the same combination of tactics in an open middlegame as in a locked pawn structure or a simplified endgame. The choice of tactic is conditioned on the **position**, not on the move counter alone.

CA-v3 (the "Adaptive" or "Grandmaster" variant) replaces the fixed schedule with a lightweight **state machine** that reads four cheap statistics of the population each iteration and switches the active tactical repertoire accordingly. Every mechanism introduced below is implemented in `chess_algorithm_v3` (`src/algorithms.py`) and validated empirically in the CEC-2017 and engineering-design experiments reported in Sections 3–4 of this update.

## 2. Reading the Position

Four exponentially-smoothed signals ($\lambda = 0.8$) are recomputed every iteration:

$$
d(t) = \frac{1}{\mathrm{Lspan}\sqrt{D}} \cdot \frac{1}{N-1}\sum_{i=2}^{N} \lVert \mathbf{X}_i^{(t)} - \mathbf{K}^{(t)} \rVert_2 ,
\qquad
\tilde{d}(t) = 0.8\,\tilde{d}(t-1) + 0.2\, d(t),
$$ {#eq-divergence}

the mean normalized distance of the population to the King — "is the position open or closed?" — where $\mathrm{Lspan} = \max_j (u_j - l_j)$. Two further EMAs track the *initiative*,

$$
\alpha(t) = 0.8\,\alpha(t-1) + 0.2 \cdot \frac{1}{N}\sum_{i=1}^{N} \mathbb{1}[\text{move}_i \text{ accepted}],
$$ {#eq-acceptance}

and the *technical success rate* of the King's own local search,

$$
\varepsilon(t) =
\begin{cases}
0.8\,\varepsilon(t-1) + 0.2 & \text{en-passant capture succeeded at } t,\\
0.8\,\varepsilon(t-1) & \text{otherwise.}
\end{cases}
$$ {#eq-epsilon}

Finally, a **fifty-move-rule** counter $s(t)$ tracks stagnation. Unlike a naive "iterations since the last strictly-improving move" counter, $s(t)$ resets only on a *materially significant* improvement — the same principle chess uses to call a draw only when fifty moves pass with no pawn move or capture, not merely "no improvement to the fortieth decimal":

$$
s(t) =
\begin{cases}
0, & f(\mathbf{K}^{(t)}) < f_{\text{ref}} - \max\!\big(10^{-4}\,|f_{\text{ref}}|,\ 10^{-10}\big),\\[2pt]
s(t-1) + 1, & \text{otherwise,}
\end{cases}
\qquad f_{\text{ref}} \leftarrow f(\mathbf{K}^{(t)}) \text{ whenever } s(t) = 0.
$$ {#eq-fifty-move}

Early tuning without this rule showed the natural culprit: sub-threshold en-passant refinements (routine in the endgame) kept resetting a naive stall counter, so the BLOCKADE overlay (§4) never fired even in runs that were visibly stuck in a secondary basin for hundreds of iterations.

## 3. Game Phases

The smoothed divergence $\tilde{d}(t)$ and the fraction of the budget elapsed, $\phi(t) = t/T$, jointly select one of four phases:

$$
\text{phase}(t) =
\begin{cases}
\textsc{Opening}, & \tilde{d}(t) > \delta_{\text{open}},\\
\textsc{Middlegame}, & \delta_{\text{end}} < \tilde{d}(t) \le \delta_{\text{open}},\\
\textsc{Closed}, & \tilde{d}(t) \le \delta_{\text{end}} \text{ and } \phi(t) \le 0.5,\\
\textsc{Endgame}, & \tilde{d}(t) \le \delta_{\text{end}} \text{ and } \phi(t) > 0.5,
\end{cases}
\qquad \delta_{\text{open}} = 0.22,\ \ \delta_{\text{end}} = 0.045.
$$ {#eq-phase}

The **Closed** phase is the one genuine surprise of the tuning process. A population can collapse to a small radius around the King *early* in the search — a premature convergence, not a genuine endgame — and early prototypes that treated every low-divergence state as "endgame" made this worse: the endgame's own tactics (heavy pinning, aggressive pawn advance) accelerate collapse rather than reversing it. Reading this as a **prematurely closed position** and answering with Nimzowitschian *prophylaxis* — restraint rather than immediate commitment, reopening lines before storming them — fixed the pathology (§7 documents the empirical effect).

Each phase activates a different parameter vector $(p_{\text{pin}}, \ell, p_{\text{council}}, p_{\text{DA}}, p_{\text{intf}}, g_{\text{pawn}})$:

| Phase | $p_{\text{pin}}$ | leap mult. $\ell$ | $p_{\text{council}}$ | $p_{\text{DA}}$ | $p_{\text{intf}}$ | pawn gain $g_{\text{pawn}}$ |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Opening | $0$ | $2.0$ | $0$ | $0$ | $0.30$ | $0.30$ |
| Middlegame | $0.5\,\phi(t)$ | $1.0$ | $0.5$ | $0$ | $0.15$ | $0.30$ |
| Closed | $0$ | $2.0$ | $0.5$ | $0.15$ | $0.15$ | $0.30$ |
| Endgame | $\min(0.5,\ 0.75\,\phi(t)+0.1)$ | $0.5$ | $0.7$ | $0.15$ | $0$ | $0.45$ |

: Phase-conditioned tactical schedule. {#tbl-phase-schedule}

Superimposed on any phase is a **Zugzwang** check: if the population has lost the initiative and the King's local search has gone quiet simultaneously,

$$
\text{Zugzwang}(t) \iff \phi(t) > 0.2 \ \wedge\ \alpha(t) < 0.04 \ \wedge\ \varepsilon(t) < 0.05,
$$ {#eq-zugzwang}

the development coefficient is halved for that iteration only, $a(t) \leftarrow a(t)/2$ — a **triangulation** move: change nothing structurally, spend a tempo, and let the next reading of the position be more informative before committing to a new phase.

## 4. New Tactical Operators

### 4.1 Novotny Interference (Bishops)

Named for the classical *interference* motif in which a piece is sacrificed on a square that simultaneously blocks two enemy lines of defense. Here, a Bishop is occasionally interposed on the segment between two **distant, higher-ranked** pieces rather than moving diagonally around the King:

$$
\mathbf{X}_i' = \beta\, \mathbf{X}_a + (1-\beta)\, \mathbf{X}_b + 0.02\, a(t)\, \mathbf{L} \circ \mathbf{z},
\qquad \beta \sim \mathcal{U}(0.3, 0.7),\quad \mathbf{z} \sim \mathcal{N}(\mathbf{0}, \mathbf{I}),
$$ {#eq-interference}

with $a, b$ drawn without replacement from the fitter half of the population, activated with probability $p_{\text{intf}}$ (@tbl-phase-schedule). Being a convex recombination of two arbitrary population members rather than a step along a coordinate axis, it is rotation-invariant and recombines "building blocks" discovered in different regions of the search — the mechanism most directly responsible for CA-v3's gains on the CEC-2017 hybrid and composition functions (§6).

### 4.2 Knight's Fork

$$
\mathbf{X}_i' = \mathbf{X}_i + \mathbf{r} \circ (\mathbf{K} - \mathbf{X}_i) + 0.8\,(\mathbf{X}_a - \mathbf{X}_b), \qquad a, b \sim \mathcal{U}\{1,\dots,i-1\},\ \ \mathbf{r}\sim\mathcal{U}(0,1)^D,
$$ {#eq-fork}

played with probability $p_{\text{fork}} = 0.5$ whenever a Knight does not take its exploratory leap. Like Interference, this is a differential (rotation-invariant) move, but drawn only from *better-ranked* peers — it "attacks two targets at once," drifting toward the King while inheriting the differential structure of two elites simultaneously.

### 4.3 Discovered Attack (King's probe)

An early version of this operator applied the discovered-attack geometry as a *population* move for Rooks; it was reclassified after tuning revealed it as **tactically unsound at that scale**: the candidate $\mathbf{X}_e + u(\mathbf{K}-\mathbf{X}_e)$ is accepted by the ordinary improvement rule almost every time it is tried, which collapses the Rook sub-population onto the King–elite line and destroys diversity within a handful of iterations. Restricting it to a single **King-only, strictly elitist probe** — active only in the Closed and Endgame phases, where the risk of diversity collapse is no longer relevant — recovered the intended effect without the pathology:

$$
\mathbf{Y}_{\text{DA}} = \mathbf{X}_e + u\,(\mathbf{K} - \mathbf{X}_e), \qquad u \sim \mathcal{U}(1.2, 2.2),\quad e \sim \mathcal{U}\{1,2,3\},
$$ {#eq-discovered}

replacing one of the three en-passant trial points with probability $p_{\text{DA}}$, and kept only if it strictly improves the King, exactly as the original en-passant acceptance rule of CA-v1/v2. The lesson generalizes: a tactic that is sound for a single elite piece can be destabilizing when applied to an entire role class, exactly as a discovered attack that wins material for one grandmaster is a blunder if every club player tries it at once.

### 4.4 Royal Council

$$
\mathbf{Y}_{\text{council}} = \mathbf{K} + 1.5\,u\,(\mathbf{K} - \mathbf{c}), \qquad \mathbf{c} = \tfrac{1}{2}(\mathbf{X}_{\text{Q}_1} + \mathbf{X}_{\text{R}_1}),\quad u \sim \mathcal{U}(0,1),
$$ {#eq-council}

a reflection of the King away from the midpoint of the best Queen and best Rook, also competing for the second en-passant slot (probability $p_{\text{council}}$, mutually exclusive with the Discovered Attack draw). Where isotropic Gaussian probes are blind to the *shape* of the elite, Royal Council is population-shaped and anisotropic: when the elite is strung along a narrow curved valley — the typical geometry along an active inequality constraint in the engineering-design problems (§7) — the reflection points down the valley rather than across it. This single mechanism closed most of the CA-v2$\to$v1 welded-beam gap during Phase 1 tuning.

### 4.5 Windmill

A chess *windmill* is a repeating sequence of discovered checks that harvests material on every repetition. In the Endgame phase only, a successful en-passant or Council capture with displacement $\boldsymbol{\delta} = \mathbf{K}^{(t)} - \mathbf{K}^{(t)}_{\text{pre}}$ is extended:

$$
\mathbf{K} \leftarrow \mathbf{K} + \boldsymbol{\delta} \quad \text{while } f(\mathbf{K}+\boldsymbol{\delta}) < f(\mathbf{K}),\quad \text{up to 3 repetitions.}
$$ {#eq-windmill}

### 4.6 Overprotection Archive

Aron Nimzowitsch's *overprotection* principle counsels defending a strategically valuable point with more force than immediately necessary, so that pieces freed from other duties have a strong square to fall back on. CA-v3 archives up to $A_{\max}=5$ mutually distant past King positions,

$$
\text{admit } \mathbf{K}^{(t)} \text{ to the archive} \iff f(\mathbf{K}^{(t)}) < f(\mathbf{K}^{(t-1)}) \ \wedge\ \min_{\mathbf{a}\in\mathcal{A}} \frac{\lVert \mathbf{K}^{(t)}-\mathbf{a}\rVert}{\mathrm{Lspan}\sqrt{D}} > 0.15,
$$ {#eq-archive}

evicting the worst archived point by fitness when the archive overflows. These are the "strongpoints" a Blockade event (§4.7) falls back on.

### 4.7 Blockade Overlay: Pawn Break, King's March, and Tal's Speculative Sacrifice

When $s(t) \ge s_{\text{break}} = 25$ (@eq-fifty-move), three mechanisms fire together:

**Pawn break.** All Pawns are re-deployed uniformly at random — "in a closed position, open lines with a pawn lever."

**King's March, with consolidation.** The King probes six long-radius candidates at three scales,

$$
\mathbf{Y}_m = \mathbf{K} + \rho_m\, \mathbf{L}\circ\mathbf{z}_m, \qquad \rho_m \in \{0.1,0.1,0.2,0.2,0.4,0.4\},\quad \mathbf{z}_m \sim \mathcal{N}(\mathbf{0},\mathbf{I}),
$$ {#eq-march}

then **consolidates** the best candidate with an 8-step greedy local refinement of shrinking radius ($\times 0.7$ on failure) *before* comparing it against the incumbent King. This refine-then-compare order is deliberate: it lets the march accept a basin whose raw landing point is worse than the incumbent but whose refined optimum is better — "the King marches to the other flank and castles by hand into the new shelter" — while the final elitist comparison guarantees the King's fitness sequence never worsens.

**Tal's speculative sacrifice.** For the next $r_{\text{heat}}=10$ iterations the sacrifice budget is reheated tenfold, $\theta(t) \leftarrow 10\,\theta(t)$, echoing Mikhail Tal's willingness to give up material for an initiative he could not yet fully calculate — "rip the position open" rather than continue playing safe, calculable moves that have already stopped producing progress.

**Overprotection regroup.** If the archive is non-empty, the worst-ranked Queen is replaced by a random archived strongpoint, giving the population a proven foothold to build from rather than restarting blind.

## 5. Opening Principle: Opposition-Based Initialization

The initial population is evaluated together with its reflection through the board's center, $\mathbf{X}^{(0)}_{\text{mirror}} = \mathbf{l}+\mathbf{u}-\mathbf{X}^{(0)}$, and the fitter half of the combined $2N$ candidates is kept — "develop with the whole board in view" rather than committing to one half of it by chance. We report this honestly rather than dress it up: component-isolation experiments during tuning found a **mixed** effect (better on 2 of the 4 micro-benchmark problems tested, worse on the other 2), not a consistent gain. It is retained as the default (`opp_init=True`) because it never produced a large regression and is essentially free (one extra population evaluation, paid once); a dedicated ablation across the full 24-function suite is left for future work rather than asserted here.

## 6. Data Integrity: Detection of Defective Benchmark Implementations {#sec-opfunu-audit}

CEC-2017 was accessed through `opfunu` v1.0.1, a third-party Python port of the official MATLAB/C suite. Two independent checks were applied before any result was trusted.

**Preflight check.** For every candidate function, $|f(\mathbf{x}^{*}) - f^{*}| \le 10^{-6}\max(1, |f^{*}|)$ was verified at the library's own reported global optimizer $\mathbf{x}^{*}$. This alone excluded **F5** (Shifted-and-Rotated Schaffer F7, reporting a near-flat surface across the whole box — no optimizer could descend meaningfully below the initial population) and **F9** (Shifted-and-Rotated Schwefel, where optimizers routinely returned values *below* the claimed $f^{*}=900$).

**Post-hoc empirical audit.** The preflight check alone is insufficient: it verifies the function only *at* $\mathbf{x}^{*}$, and says nothing about the rest of the domain. Three further functions were caught only because all six competing algorithms — not CA specifically — returned a best-of-30-runs value more than $1.0$ below the claimed global optimum, which is definitionally impossible if $f^{*}$ is correct:

| Function | Min. observed error $\left(\min_a \min_r f - f^{*}\right)$ |
|---|---:|
| F15 (Hybrid 6) | $-634.7$ |
| F19 (Hybrid Function 10) | $-429.3$ |
| F21 (Composition 2) | $-9{,}592.4$ |

: Post-hoc audit results. F21 is the most severe: essentially every algorithm in the roster, including the weakest (WOA), found points the library's own optimum could not explain — strong evidence of a genuine implementation defect (most plausibly in the shift/rotation or composition-weighting bookkeeping) rather than an artifact of any single algorithm's search behavior. {#tbl-audit}

All five functions (F5, F9, F15, F19, F21) were excluded from the headline analysis, leaving **24 validated functions**. The audit protocol, thresholds, and the full pre-audit numbers are preserved in `results/cec2017_stats_raw_unaudited.csv` and reproduced programmatically by `src/phase2_3_analysis.py::audit_below_optimum`, so a reviewer or future user of a newer `opfunu` release can re-run the same check rather than trust our exclusion list blindly.

## 7. Results Summary

Full protocol: $D=30$, population $30$, $500$ iterations, $30$ independent runs, run $r$ of every algorithm seeded at $\text{SEED}_0+r$ on the shared unit-hypercube search space (bounds folded into the decoder). Roster: CA-v3, CA-v2 (ablation — the same operator set with the adaptive phase machine removed, i.e. every mechanism from Section 4 disabled), GWO, PSO, GA (in-house), and WOA (third-party, `mealpy` defaults). Full tables (Best/Mean/Std per function or problem, Friedman ranks, Wilcoxon win/tie/loss) are in `results/latex_tables_final.tex`, generated programmatically from `results/cec2017_stats.csv` and `results/engineering_stats.csv`.

**CEC-2017 (24 valid functions).** Mean Friedman rank: CA-v3 $2.000$, GA $2.167$, CA-v2 $2.208$, PSO $4.375$, GWO $4.417$, WOA $5.833$ ($\chi^2=87.40$, $p=2.4\times10^{-17}$). CA-v3 wins $23/24$ against GWO, $21/24$ against PSO, and $24/24$ against WOA, with zero losses to any of the three. Against its own ablation, CA-v2, it wins $4$, ties $18$, and loses $2$ — the adaptive machinery helps on balance without a dramatic swing, which is the expected signature of a well-tuned control layer over an already-competitive base algorithm.

**Engineering design (7 problems).** Mean Friedman rank: CA-v3 $2.000$, CA-v2 $2.286$, GWO $3.143$, PSO $3.714$, GA $4.286$, WOA $5.571$ ($\chi^2=17.61$, $p=0.0035$). CA-v3 loses only once across all $35$ pairwise comparisons (to PSO, on the welded-beam problem, where PSO's near-zero variance around the known optimum is difficult for any exploration-retaining method to match).

## 8. Limitation, the No-Free-Lunch Theorem, and "Pawn Promotion" as Future Work

The one result that does **not** flatter CA-v3 is its standing against GA on CEC-2017: a near-tied mean rank ($2.167$ vs. $2.000$) conceals a **10-loss / 7-win / 7-tie** record function-by-function. Inspecting *which* functions CA-v3 loses is informative rather than embarrassing: F4, F11, F12, F16, F20, F22, and F24–F27 — Rastrigin-family and composition/hybrid landscapes whose basins are separated by distances comparable to the search domain itself. GA's BLX-$\alpha$ crossover routinely proposes offspring *outside* the interval spanned by two parents, an operator that — by construction — can relocate a candidate solution across the domain in a single step. Every CA-v3 operator in Section 4, by contrast, is anchored to the King, an elite peer, or a bounded local neighborhood; even the Knight's exploratory leap resamples only two of $D=30$ coordinates.

This is not a flaw to be argued away but close to a textbook illustration of the No-Free-Lunch theorem [@wolpert1997nfl]: CA-v3's operators were tuned (Phase 1, this document, §3–4) specifically against constrained engineering geometry and smooth hybrid/composition exploitation, and that specialization has an opportunity cost on landscapes whose defining difficulty is long-range, unstructured basin-hopping. We report the full function-by-function breakdown (Table `tab:cec2017-detail`) rather than only the aggregate rank, precisely so this trade-off is visible to the reader rather than smoothed over by a summary statistic.

**Future work: Pawn Promotion to Queen.** The chess metaphor suggests its own remedy. A pawn that reaches the eighth rank is not incrementally improved — it is instantaneously promoted to the most powerful piece on the board, a discontinuous, large-scale change in capability. We propose an analogous operator: an agent that survives $k$ consecutive Blockade events (§4.7) without producing a King improvement is "promoted" — for one iteration, its move is drawn not from the bounded Pawn/Knight/Bishop geometry of Section 4 but from a BLX-$\alpha$-style macro-crossover against a randomly chosen distant population member,
$$
\mathbf{X}_i' = \mathbf{X}_{\text{lo}} + (1+2\gamma)\,\mathbf{r}\circ(\mathbf{X}_{\text{hi}}-\mathbf{X}_{\text{lo}}) - \gamma\,(\mathbf{X}_{\text{hi}}-\mathbf{X}_{\text{lo}}),
$$
with $\mathbf{X}_{\text{lo}}, \mathbf{X}_{\text{hi}}$ the coordinatewise min/max of two distant parents and $\gamma$ an extrapolation margin — deliberately capable of landing outside the segment joining them, unlike any operator currently in CA's repertoire. An alternative framing, closer to a second chess variant, is a **Bughouse/Crazyhouse piece drop**: a captured piece from anywhere on the board (any population member's *coordinate subset*, not the whole vector) is "dropped" onto a *different* board region, i.e. spliced onto an unrelated agent — a large-scale, cross-dimensional recombination distinct from the segment-local Novotny Interference of Section 4.1. Both proposals are deliberately **not implemented or benchmarked here**; they are natural next steps precisely because Section 7's evidence identifies, rather than merely speculates about, the class of landscape where CA-v3's current operator set is under-powered.

## 9. Reproducibility

| Artifact | Path |
|---|---|
| CA-v3 implementation | `src/algorithms.py::chess_algorithm_v3` |
| CA-v2 ablation baseline | `src/algorithms.py::chess_algorithm_v2` |
| Phase 1 tuning / component isolation | conversation record; final config is the function default |
| CEC-2017 full run | `src/cec2017_full_run.py` (`--part i/4` for the 4-way parallel partitioning used here) |
| Engineering-design full run | `src/engineering_full_run.py`, problems in `src/engineering_problems.py` |
| Merge, integrity audit, Friedman/Wilcoxon, figures | `src/phase2_3_analysis.py` |
| LaTeX tables | `src/generate_latex_tables.py` → `results/latex_tables_final.tex` |
| Raw results | `results/cec2017_stats.csv`, `engineering_stats.csv`, `raw_cec2017.npz`, `raw_engineering.npz` |
| Convergence figures (300 DPI) | `figures/cec2017_convergence.png`, `figures/engineering_convergence.png` |
