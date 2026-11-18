# 19 — Collection run: what we tried, what we learned, and where the GLM edge is

**Run 51, 2026-11-18.** A reading pass over runs 1–50 of this project, one
document, no new measurements except the record check in §1.

*Updated at run 61, 2026-11-18.* §1 now reports the record as it stands (thedrift it described was fixed at run 52), §10 records runs 52–61 in full, and
§3 gains L9–L12. The run-51 text below is otherwise unchanged so the earlier
reading stays auditable. Sources are the
numbered records `00`–`18`, the ledgers in `workspace/push/`, and the run log;
every figure below is traceable to one of them. Read-only: no row changed, no
score claimed, nothing committed.

The short version:

* **The table is at 22.218056945, 553 of 1000 rows beating grid**, and that
  number is now guarded by an assertion (`sqscore.guard`), which also confirms
  the record is inconsistent in ten other places (§1).
* **Six campaigns have been run.** Two produced score-bearing structure (imports
  + exact provenance; the constructive families), one produced a theorem (the
  cascade), three produced firm negatives (local search, the Λ₂₄ address, the
  rigidity class), and one produced the only *learned* object that works — a
  relation potential that tightens corrupted seeds and has never broken the push
  wall.
* **The recurring finding is the same finding in five costumes: score is a
  property of which algebraic words a packing uses, not of how hard we search.**
  Rotation (i.e. the √2 word) predicts "beats grid" with AUC 1.0000; every metric
  address fails for the same reason — quantisation cannot see the field; and the
  one lever with a price on it (slack in open columns, 52.38 score per unit) is a
  construction problem, not a search problem.
* **Aim, from the GLM side:** build the *grammar* rather than the *map*. Declared
  alphabet + rewrite rule + grammar score + an expressiveness ladder. §6 turns
  that into four ordered moves with falsifiers; §5 says why this is the shape our
  machinery is actually good at.

---

## 1. State of the record

`python3 scripts/sqscore.py` (run now): **score 22.218056945, 553 beats, 447
grid, 1000 rows** — so the CSV is canonical and the guard passes.

**As originally written (run 51), this section reported drift**: `00-OVERVIEW`
quoting 22.642386651, `table.json` at 22.645991 with 357 of 1000 rows disagreeing,
`02`'s title at 875/1000 against a body saying 929, the run log's header at
22.887471 while its body stopped at run 39, and ten documents quoting one of the
four old totals. That drift is **fixed** — `record_guard.py` was implemented at
run 52 explicitly to close it (§7), and it now passes on every run of the check
batch.

Record as it stands at run 67:

| item | state |
| --- | --- |
| delivered table | **22.218056945, 553 beats, 447 grid, 1000 rows**, asserted by `sqscore.guard` |
| `record_guard.py` | **OK** — 34 documents, 153 totals scanned; 93 historical totals quoted below title blocks are inventoried, not claimed |
| documents quoting an old total | all carry an explicit historical/stale tag; none presented as current |
| `04-RUN-LOG.md` | entries through **run 67** (52–61 in §10 here, 62–67 in §12) |
| implementation records | `20`–`26` — one per G-2 experiment, each with its ledger; `27`–`30` for runs 62–67 |
| ledgers | **125** files in `workspace/push/` |
| uncommitted paths | **117** under this subproject (nothing has been committed in this campaign) |

Two structural hazards survive and should stay flagged. `table.json` must not be
written back (it would regress the submission by 0.43), and `cascade_predict.py`
reads it deliberately as a different file — so "stale" is its correct state, not
a defect to fix.

The honest residue: the run log's *entry count* is not a measure of the campaign.
Fifteen entries share the `## Run NN` heading form; the rest of the history lives
in the numbered records, and §10 exists so that runs 52–61 can be read in one
place rather than reconstructed from nine documents and 119 ledgers.

---

## 2. What we have tried

### 2.1 Table assembly, imports, exactness (runs 1–38)

Score history: 22.887471 → 22.823536 (atlas import + closure fixpoint, 454
beats) → 22.645991 (run-32/36 consolidation) → **22.218056945** (current, 553
beats). The leader is 22.0544, so 0.1637 separates us.

| work | result |
| --- | --- |
| provenance pipeline, 9 sources | every row carries a construction source; census by exact material: 674 cert-rational, 134 design-quadratic, 124 derived, 68 float-only (05 §2) |
| exact verification | **929/1000** rows exact on one of two tracks (853 field-certificate + 76 Fraction replay at 76/76, drift ≤ 1.9e-9) |
| atlas import | 76 applied, 244 rejected, +0.050264; all 76 replay exactly in `Fraction` |
| t-basis census | every import is rational-geometry; the "45°" rows are rational ≈ √2−1 + O(1e-10); 22 rows at arctan(½) |
| process audit / layer audit | 879/1000 "fits" at strict budget were spurious → certification moved to certificates |
| table laws | shell law 937/937; deletion lemma 999/999 pairs monotone |

This is the part of the project that is unambiguously sound. It is also the part
that cannot win anything: imports are at grid on every open root for everyone
(run 16), and the register has not drifted since Oct-17.

### 2.2 Constructive families (runs 12–42)

| family | what it is | outcome |
| --- | --- | --- |
| **cascade / band step** | from `k²+r` at side `k+δ`, add `2k+1` squares → `(k+1)²+r` at `k+1+δ` | **theorem**: invariant is `(r, δ)`, not `r` (09 §2) |
| cascade as a solver | carry every base to its column end | **saturated**: 0.000000000 score change, 0 gate failures; 931/969 covered, table beats the chain by **0.481427** on 415 rows |
| Göbel / strip / k²+1 families | gobel2/3/5/6, band mosaic, strip, two-block, notch | near-misses (159 states at gap exactly 0 on 23 tied rows); no records |
| motif wheels | 4 declared wheels, 81 cells, one gate, one scorer, strict-JSON ledger, selftest 10/10 | **81 cells, 0 survivors, 81 refused** — every refusal names its law (area_exact, n_cap, no_gain, packlib_rejected, worse_than_grid) |
| beyond 1000 | closed-form easy rows | **4,794 rows / 4,794 distinct n**, 53.27% of the 9,000-row window; 340 provably optimal; the rest median depth 0.0103 |

The cascade is the only *proved* structure in the project that touches the
score, and its measured message is that it has already been fully applied. The
motif wheels are the cleanest instrument built here: a declaration, a count law,
and a refusal that names which law failed.

### 2.3 Search and local descent (runs 39–50)

| attempt | result |
| --- | --- |
| `relax` + `coordinate_polish` from delivered states | returns them **bit-identical** — the rows are fixed points |
| `sa_push.anneal` from compressed seeds | every target fails the gate |
| compiled physics-analogy engines (P-04, P-05, P-11, P-12) | **236 cells, 0 finds** → **write-off W-01** |
| `hop_search` (reconstructed engine) | n=5 control **passes** after the collective-kick fix (L ≈ 2.70806–2.70810, 3–4/4 hard hops); **n=11 control still fails** — it needs 8 tilt angles, the kick family has 0/45/90 |
| r=1 base hunt (PL-32) | no base below 0.520815; sweep k=8..25 → 18/18 k, 0 rows below 0.520815 → **NO BASE**, no score change |
| re-slot vs rotation kicks at the n=5 trap | rotation alone 0/300; with a re-slot component **25/150** |

The engine story is worth recording exactly: `cent_discovery`, `engine_variants`
and `oracle_basin` were imported by eight scripts and **never existed in the
repository's git history** (13 §1). They were reconstructed to contract;
`settle_to` validated; the control that mattered (n=5) was only passed once the
collective kick was made correct (two real bugs: `0.5*d_local`, and `% π` applied
to the whole `(n,3)` array).

### 2.4 The language campaign (runs 39–41, `06`, `07`)

Four mechanisms were translated from arXiv:2611.17309v1 and measured separately.

| mechanism | verdict |
| --- | --- |
| relation cost as a ranking rule | **stands**: 21,602 contacts, 18 cells; AUC 1.000 vs angle-destroyed control, 0.794 vs position-destroyed; Spearman 0.368/0.744/0.562 (n = 40/70/110) |
| calibrated threshold | **does not transfer**: τ = 0 exactly (1000/1000 rows at E ≤ 1e-12), so E is the feasibility test and grades nothing |
| focused relaxation | **not demonstrated**: loses at n=240, amp 0.08 (+39%) *with* 6× the moves |
| two-layer settle | weak, inconsistent positive (1.17e-2 vs 1.84e-2 at n=240) |

Then the objective work: the learned cost is a **step function** (`cbar` moves by
a median 9.5e-2 for any perturbation from 1e-3 to 1e-1; λ = 0.1, 1, 1e3, 1e6 give
identical states). Replacing it with a kernel-density potential (360×240, σ = ½
bin, U = −log p) is the only learned object here that improves anything: **10/16
cells improve after the polish, best 5.9×, language cost falling with the
energy**. With λ scheduled by corruption and fitted on all 156 proved rows:
**geo 0.782, 8 better, 0 worse, worst cell 1.028** — the first rule with no bad
cells.

And then the wall: **0 of 8 gated, 0 of 8 below the record, across five distinct
attacks** (four weightings, then angular freedom). The jam classifies **liquid in
12/16 states** (rigid only at n=60, ρ = 1.000); rotation-rich retry makes states
*more* crystalline (rigid 4/16 → 7/16) and 46% worse. The contact word is never
recovered: Jaccard with the record's contact set **0.018–0.054** at every energy.

### 2.5 Addresses: the layer tower, pockets, Λ₂₄, and the contact graph (runs 11–50)

| address | construction | verdict |
| --- | --- | --- |
| **layer tower** (`01`) | Substrate → Integer → Rational → Scan → Certificate, Golay as substrate | **the theory is real**: all 4,096 codewords enumerated, 759 octads computed, 2,325 error patterns of weight ≤ 3 with distinct syndromes, boundary theorems proved; one was **false as stated** and corrected (`scan_blind_to_clearance` → \|Δscan\| ≤ 1) |
| **24-pocket address** (PL-25/27/33) | 6 angle sectors × 4 shells → 24-bit word → nearest Golay codeword | **refuted, post-audit**: 50 distinct addresses for 1000 rows, entropy 2.811/12 bits. The per-square statistics looked promising (decisiveness gap, MI 0.2276 bits) until the rotation control: **AUC(rotation→beats) 1.0000 vs AUC(gap→beats) 0.9861, MI(rot;beats) 0.9919, MI(gap; beats \| rotation) = 0.0000**. Every pocket number is rotation. (The earlier MI 0.1930 was measured against the mislabelled target and is superseded — PL-33.) |
| **Λ₂₄ map** (`16`) | encode `(x, y, L)` at scale S into 24 ints; exact integer membership test | **codec, not address**: window is `2n+1 ≤ 24 ⇒ n ≤ 11` (989 of 1000 rows outside by dimension); membership validated on **196,560/196,560** minimal vectors; crosstab over 255 rows and 8 scales is **perfect: tilted → illegal 87/87, untilted → legal 168/168** |
| **combinatorial address** (`17`) | tilt bit per square + WL signature of the tilt-coloured segment-contact graph + \|E\| | **real invariant, weak predictor**: R² 0.978 raw but 0.728 vs null max 0.755 stratified; on a contact-bearing ensemble **0.624 vs null max 0.545 (0/200)** — the only address statistic here that beats its null |
| **rigidity class** (`18`) | Maxwell/Laman count, exact sparsity rank, wall bars, pinned | **no information**: R² exactly = \|E\| (0.391 both), exactly 0 inside an address class; **0/220 rows** has a redundant contact, so `cls = (2n−3−\|E\|, 0)` |

Two structural facts came out of this that are worth more than the negatives.
Square contact graphs cannot reach the Laman threshold: best headroom by cluster
size is `|S|=3: 0, 4: −1, 5: −1, 6: −2, …` — the only tight cluster is a
**triangle of three mutually touching squares**, the degenerate case. And the
delivered optima are **pinned but never Laman-tight** (0/38 for n ≥ 3), with
m/n = 1.347: the container is what removes the mechanism, not the contact graph.

### 2.6 Instruments and process (interleaved)

The scorer guard (`sqscore.guard`) is the most valuable single artifact built in
these runs: it turns "which score?" into an assertion. Everything below was found
*because* of it or in the same spirit.

| defect | cost | fix |
| --- | --- | --- |
| `area_ceiling.py` scored `10/L` and inflated the bbox by two half-extents | reported 593.279 for a 22.218 table; mislabelled **253 of 553** beating rows as grid; invented "39 base-less columns" and a 0.081-bit "genuine" MI | rebuilt in `leech_audit_fix.py`; two claims **withdrawn** (PL-33) |
| eight leech instruments each had a private score/box | same class of error, silently | all wired to `sqscore`; grep for the old idioms returns nothing |
| `scan_blind_to_clearance` as stated | false (0.49e-12 vs 0.51e-12) | corrected to \|Δscan\| ≤ 1 |
| `sub_packings` deleted one square and skipped `src > n+1` | made two thirds of an ensemble dead; "two-level" ensemble | fixed (run 49); guarded by a selftest check that the family spans several sides |
| `conditional_r2` on a zero-variance cell | printed **+0.5000** from SS ≈ 1e-30 | returns *undefined* at round-off |
| jam classifier with ρ = `nan` | fell through to "liquid", unlabelled | falls back to contact fraction, flags `degenerate` |
| census criterion "mean \|log ratio\|" | degenerate — rewards λ → 0 | replaced by min-max regret (PL-13/14) |

---

## 3. What we have learned

**L1. The energy is a gate, not a landscape.** At a feasible packing E = 0
*exactly*, for 1000/1000 rows; a 0.1% squeeze puts 0/400 rows at the threshold
(median E 4.33e-4). So an E-descent cannot prefer one feasible arrangement to
another, and "better settle" is not a source of score — the r=1 rows are
bit-identical fixed points of their own relaxer. Everything that scores had to be
*constructed*.

**L2. The score is the √2 word.** Rotation predicts "beats grid" with AUC 1.0000
and MI 0.9919 bits against H = 0.992. The r=1 column (30/31 rows beating, slack
0.52–0.71) is entirely 45° geometry. Every tilted row in the window is illegal as
a Λ₂₄ point at every tested scale (87/87), and every untilted row is legal
somewhere (168/168) — the lattice condition is an integrality condition, and √2
is not an integer at any scale. The import frontier's "45°" is a *rational*
√2−1 + O(1e-10): the same word, written exactly.

**L3. Quantisation destroys exactly the structure that pays.** Four addresses
have now failed the same way: 24 pockets (MI collapses under a rotation control),
Λ₂₄ legality (incompatible with the field), the metric codec (loses √2 at every
scale), the rigidity class (adds nothing to |E|). The ones that survived are
**discrete and combinatorial** — the tilt bit, the contact graph, the t-basis.

**L4. The cascade is a rewrite rule with an invariant, and it is saturated.**
`(r, δ)` is preserved by `n ↦ n + 2k + 1`; 931/969 rows are covered; applying the
rule everywhere changes the score by 0.000000000, and the table beats its own
chains by 0.481427 on 415 rows. A rewrite rule that is already fully applied is a
statement about *atoms*, not about rewriting.

**L5. Local search cannot create geometry.** Fixed points, 236 engine cells / 0
finds, 0/8 gated at the push wall under five different objective weightings,
n=5 reachable only with a re-slot kick. The one positive local result (the
corruption-scheduled relation potential) **tightens what is already feasible** —
it wins at amp 0.04–0.08 and is inert at the records, where the gradient is zero
because the record sits at the density maximum.

**L6. Instruments lie before ideas do.** Seven instrument defects are catalogued
in §2.6, three of them producing published-looking numbers that had to be
withdrawn. The pattern in all seven: a private scale, a silent branch, or an
unguarded ratio. Guards are cheaper than retractions.

**L7. Contact graphs are too sparse for rigidity theory.** `|E|/n` is 0.86 on a
contact-bearing ensemble and 1.347 on the delivered rows, against the 2 − 3/n a
Laman-tight graph needs; the best headroom for any cluster of ≥ 4 squares is −1.
Rigidity bookkeeping in this domain is arithmetic on |E|. The walls, not the
graph, are what pin a packing.

**L8. The remaining score is in slack, and slack is a construction.** Grid rows
hold a zero-waste ceiling of 7.195366; the 270 rows in already-open columns hold
6.388578 of it at **0.0237/row**, versus 0.806788 at 0.0046/row for the 177 rows
in base-less columns. The exchange rate over the open columns is **52.3830 score
per unit of slack (0.5238 per 0.01)**, and r=1 alone is worth 3.6453 per unit.
Beating the leader's 0.1637 needs ≈0.003 of slack across the open columns — or a
concentrated gain of the same size in one or two columns.

---

## 4. Review of the project

### 4.1 What is strong

1. **Exactness as a first-class citizen.** The gate is one function; 929/1000
   rows are exact on a certificate track; the t-basis makes transcendental angles
   rational-verifiable. Very few competition projects can say what is proved and
   what is merely gated, row by row.
2. **Provenance.** Every row has a source and a construction class. That is why
   the cascade, the ceiling and the column arithmetic can be stated at all.
3. **Negative discipline.** A write-off register rebuilt from ledgers, refusals
   that name the law they failed, and a habit of recording the *measurement* next
   to the claim. The Λ₂₄ crosstab (255 rows, 0 off-diagonal) is worth more than a
   weak positive would have been.
4. **The layer tower.** `01-LAYERS.md` is the project's theory: a ladder of what
   each representation can see, with boundary theorems. It has already earned its
   keep twice (the scan-blindness correction; explaining why imports are exact).

### 4.2 What is weak

1. **The record drifts.** Three different scores in three documents (§1), a
   stale `table.json` that a script could still write back, a run log that stops
   at 39 while the instrument work continues to 50. In a project whose selling
   point is provenance, this is the most damaging weakness — and the cheapest to
   fix.
2. **No single entry point.** 78+ scripts, many reachable only by remembering a
   flag. `REPRODUCE.md` is long and partly historical. A newcomer cannot answer
   "what is the current state, and what is the next command" without reading four
   documents.
3. **Dead and reconstructed modules.** `cent_discovery` (and two siblings) never
   existed in git; `lm_exactify` and `pressure_settle` still do not; three
   scripts still cannot import. Reconstructions are honestly marked, but the tree
   carries a dependency debt that a fresh clone would expose.
4. **Several docs overclaim, then retract in a later doc.** PL-30, the
   0.081-bit MI, "the wall is mechanical", "39 base-less columns" were all
   published and all withdrawn. Retraction is the right behaviour; publishing
   before a control is not. The single rule that would have prevented all four is
   in §2.6: no statistic without its null, no scale without the guard.
5. **The Lean side is stalled behind a build the owner owes**, so the strongest
   formal statements (the tower, the codec) live only in Python and prose.

### 4.3 Where the score actually stands

22.218056945 against a leader at 22.0544. The distance is 0.1637, which in slack
terms is ~0.003 across the open columns, or one new column opened well, or ~0.05
off the r=1 base. Everything else in the 22.2 is held by grid rows that need a
*new construction*, not a better search. The three sub-goals that price out are:

| target | price | what it needs |
| --- | ---: | --- |
| r=1 base below δ = 0.520815 | 0.0365 per 0.01 | a construction for `k²+1` that beats the current family (PL-32; no base found in two searches) |
| one base-less column opened | 0.10–0.26 per residue at δ ≈ 0.8 | any packing with slack < 1 at the first row of the column (24 of the 60 columns; deep ones r = 38…60) |
| tightening every open column by 0.01 | 0.5238 | a uniform improvement in slack — i.e. one better atom per column |

---

## 5. The GLM perspective

The question that matters is *what can this repository do that a competent entrant
cannot?* On the evidence of fifty runs, four things — and they are the four things
the repository already does elsewhere.

**1. Declared-law objects ("wheels") instead of searches.** A wheel here is a
finite parameter grid, an exact count law, an exact builder, one gate, one
scorer, one ledger. `motif_wheels.py` is the template: 81 cells, 0 survivors, and
every refusal cites a law. A search reports what it found; a wheel reports what
is *expressible* and why the rest is not. This is the repository's native move
(`cent_wheels`: 24 wheels, exact monomial laws, Lean-emitted theorems) and it
transfers to packings unchanged.

**2. Expressiveness as a lattice, with boundary theorems.** `01-LAYERS.md` says
what each representation cannot see, and proves it. The packing work keeps
rediscovering this: the float gate cannot see √2, the Λ₂₄ predicate cannot see
√2, the pocket address cannot see anything but rotation, the contact graph cannot
see a mechanism, the Laman count cannot exceed |E|. **Five boundary results, all
of the same shape, none of them written down as one ladder.** Writing them as one
ladder — a "what the score can be addressed by" theorem set — is a theory
deliverable that nobody else in this competition will produce, and it is
essentially free: the measurements already exist.

**3. Instruments as decidable predicates.** `in_leech24` is checked against all
196,560 minimal vectors; `sparsity_rank` against brute-force enumeration;
`sqscore.guard` against a fixed score. The repository's habit of turning a slogan
into a predicate ("is this a Λ₂₄ point", "is this cluster tight") is the thing
that makes negatives trustable. `packlib.verify` is already that for geometry.

**4. Write-offs with ledgers.** 236 cells and 0 finds is a *result*; it stops the
next run from paying again. `writeoffs.json` is rebuilt from campaign ledgers,
not typed by hand. This is the discipline that makes a long campaign cumulative
instead of circular.

And the corresponding anti-pattern, which the project has now paid for twice:
**"map the object to a famous structure and hope the structure knows the
answer."** The Λ₂₄ map is exact, validated, beautiful, and provably blind to the
only geometry that scores — because the question "is this a lattice point" is an
integrality question and the score lives in ℚ(√2). The lesson is not that
lattices are useless; it is that **a representation must be chosen for what it
can express, and the expressible thing here is an algebraic word, not a point.**

So the GLM-consistent reading of this whole project is:

> A packing is a **sentence** over an exact relation alphabet — axis-aligned,
> 45°, arctan(½), arctan(⅓), the rational t-basis — and the score is a property
> of the sentence: which words it uses, how many, and how tightly they tile. The
> cascade is a rewrite rule on sentences with an invariant. The relation cost is
> a grammar score. The exact-verification track works because the sentence is
> written in the field, not in floats. Nothing in this project has ever scored
> without a new word being added to the alphabet.

That reading is not decoration: it predicts which routes pay. Search over
arrangements adds no words (L5). A construction adds one word and a family (L8,
the r=1 and base-less columns). A grammar score ranks candidate sentences but
cannot generate them (§2.4). So the productive side is the **generative** one,
and the theory side is the ladder of what each representation can say.

---

## 6. What I would aim at, in order

Four moves. Each has a first command and a falsifier, so a run cannot drift.

### G-1 (score, cheapest first): the r=1 atom, read as a field element

The k=8..24 rows sit at δ = 0.535534 and k=25..31 at 0.520815 — a *step*, not a
trend, which means two different atoms. Compute the exact t-basis of every
delivered r=1 state (rational t per square, `Fraction`), cluster, and ask what
distinguishes the k ≥ 25 atom: a different angle word, a different count of the
√2 word, or a different wall pattern. The answer is a construction target, not a
search target.

* first command: a `r1_atoms.py` that prints, per delivered `k²+1` row, the multiset
  of exact t values and the tilt-pattern address from `leech_comb`.
* pays: 0.0365 per 0.01 of slack on r=1 (30/31 rows beating); the column is the
  single most valuable object in the table.
* falsifier: if the k ≥ 25 rows use the *same* t-multiset as k = 8..24, then the
  difference is geometric arrangement and not a word — then stop and go to G-2.

**Result (run 52, `20-R1-ATOMS.md`).** The falsifier fires.

**Result (run 53, `21-SEAM-WHEELS.md`).** G-2 was redirected by review: build the
seam before more angles. Both r = 1 atoms were reconstructed from integers in
ℚ(√2) — n = 65 as p = 5, 8+8 wall columns, δ = `5/√2 − 3`; n = 626 as p = 17,
25+24 columns, δ = `17/√2 − 23/2` — and then solved: an LP over (side, diamond
translation) with one declared separating axis per seam pair returns **exactly
the delivered algebraic side on all 12 full-diamond r = 1 rows**, pinned and
free. Mirroring the block is a no-op (the atoms are mirror-symmetric), turning
the seam costs `3√2/2 − 1`, and moving one partial row costs exactly 0.5. So the
boundary is already optimal for this arrangement: the r = 1 atom is a
**different-block** target, not a better-boundary one.

**Run 54 corrects every number in this paragraph** (`22-DIAMOND-MASK.md`): the
0.5 figure is the *full-block* declaration's cost and the tilted part of these
rows is really a five-deep diagonal **strip** (mask), not a square block; and the
payoffs below were produced by replaying a column-wide slack backwards. Re-priced
per legal start and forward only, no delivered column gains at all from
re-placing its own base (`now` = 0), the best base-less start is r = 38 at
n = 614 worth at most **0.058535**, and the optimistic per-start bounds run from
0.971 (r = 1 at n = 10) down to 0.401 (r = 8 at n = 108). Both bands use the
alphabet `{axis, π/4}` and only that; what changes is the coefficient of the √2
word — δ = 5/√2 − 3 for k = 8..24 against 17/√2 − 23/2 for k ≥ 25 — carried by a
17×17 diamond that is half-full at k = 24 (145/289) and full from k = 25
(289/289, side 17√2, the zero-waste 45° block). So the step is an arrangement,
not a word: there is no vocabulary target here, and G-2 inherits the parameter —
a declared `M-diamond(p, t)` wheel with p the diamond size, not a search. The
by-product is larger than the answer: across all 31 rows the field of δ is the
field of the alphabet (the one rational-t row, k = 7, has δ = 4/7; the two rows
with undeclared angles, k = 4 and 6, are the two with no small algebraic δ).

### G-2 (score, largest pool): open a base-less column with a declared wheel

**24 of the 60 residue columns have no beating row** (area-ceiling count, `11`
§2; `09` §5 names the deep ones, r = 38…60 — note `11` withdraws the earlier
"39 base-less" figure, which came from the broken box). Build a wheel per residue,
not a search: parameter grid = the band architectures the register already uses (corner
tilted band at a free angle + wall-hugging axis fill, run-16's design intel),
count law = the closure identity `n = k² + r` with the band's own arithmetic,
builder exact in the t-basis, one gate, one scorer.

* first command: extend `motif_wheels.py` with an `M-band(t, j)` wheel over the
  rational t grid {0, √2−1, 1/2, 1/3, 3/4, 1} × band widths j ∈ [1, k], and spin it
  at the first row of residues 38–47.
* pays: **superseded by runs 53 and 54** — the 0.10–0.26 per residue below
  assumed a *shallow* base for the column. Residues 38..60 cannot start below
  k = r−1, and pricing **every** legal start forward-only (run 54) puts the best
  whole-column bound at **0.058535** (r = 38, starting at n = 614), against the
  0.1637 gap. See `21-SEAM-WHEELS.md` §6 and `22-DIAMOND-MASK.md` §6. The banked
  example (residue 38: 0.257 at δ = 0.5, 0.103 at δ = 0.8) is a hypothetical
  shallow row, not a row of the delivered table.
* falsifier: a wheel that produces 0 gated cells across the t-grid for three
  residues is evidence the architecture is absent, and should be written off like
  W-01 rather than re-run.

### G-3 (theory, unique to us): the expressiveness ladder

One document, five boundary results already measured, each stated as "this
representation cannot distinguish these two packings that differ in score", with
the witness and the ledger:

1. float/scan layer — blind below 2.5e-13 (`scan_blind_to_clearance`, corrected);
2. 24-pocket address — sees rotation and nothing else (`MI(gap; beats|rot)=0`);
3. Λ₂₄ integrality — tilted rows illegal at every scale (255 rows, 8 scales);
4. contact graph — Laman-tight unreachable except K₃ (cluster headroom table);
5. WL address — complete for the combinatorial part, silent on geometry.

Plus the positive companion: **the exact layer loses nothing that is written in a
field** (929/1000 rows exact on one of two tracks, 133/133 Fraction replays), which
is the constructive corollary. This is the deliverable
that makes the project a GLM item rather than a leaderboard entry, and its Lean
counterpart is small enough to be worth the owner's build.

### G-4 (evaluative, keep but do not over-invest): the relation potential as a ranker

The kernel-density potential with the full-set rule (geo 0.782, 0 worse) is
already the best learned object here. Use it for what it demonstrably does —
ranking and repairing corrupted candidates — not as a descent objective. The
one unmeasured question worth an hour: refit on the **frontier** (553 beating
rows, depth-weighted), per PL-6, and re-measure the AUC on the two destroyed
controls.

* falsifier: if the frontier refit does not hold AUC ≥ 0.95 against the
  angle-destroyed control, the ranking claim was an artefact of the older table
  and should be retired with the rest.

### What not to do (register)

| route | why not |
| --- | --- |
| compiled physics-analogy moves | W-01: 236 cells, 0 finds; a move cannot add a word |
| metric addresses to a famous lattice | exact and blind: integrality vs ℚ(√2); window n ≤ 11 by dimension |
| rigidity class beyond \|E\| | 0/220 redundant contacts; the container is the constraint |
| better settle / more polish | rows are fixed points; E is a gate |
| rotation-rich retry at the push wall | makes states more crystalline, 46% worse (PL-19) |
| writing `table.json` back | 357 rows disagree; it would cost 0.43 |

---

## 7. The one process change I would make

**A record guard, alongside the scorer guard.** `sqscore.guard` stops a wrong
score from being printed. Nothing stops a stale score from being *read*. Four
lines of the same kind — assert that every document quoting a total quotes
22.218056945, or carries an "historical" tag; assert `table.json` is either
current or marked read-only; assert the run log's last entry is the last ledger —
would have caught every inconsistency in §1 and most of the retractions in §2.6
and §4.2. In a project whose product is a trustworthy record, that is worth more
than one more search campaign.

**Implemented at run 52** — `scripts/record_guard.py`, exit 1 on a violation.
Two fatal rules: R1, a line that claims currency (current/canonical/submission
score/delivered table/latest score/stands at) must quote 22.218056945; R2, the
first total in a document's title block must be the current one. A line opts out
by carrying an explicit tag (historical / stale / superseded / withdrawn), which
is the convention the prose already uses; a line that quotes the current score
is never a violation, so score-history arrows stay legal. Two notes are
non-fatal: `table.json`'s disagreement with the delivered table (still stale,
read-only) and the run log lagging the ledgers. On first run it flagged 49
claims across twelve documents; the ten current-facing ones were corrected to
the run-47 table (00, 04, 05, README, RECONCILIATION, REPRODUCE, STATUS, 02's
title, NEXT_STEPS, GLM_INVESTIGATION) and the rest are now inventoried as
history rather than presented as current.

---

## 8. Limits of this collection

* It is a reading pass: no new measurements except the guard check in §1. Every
  number is quoted from a numbered record or ledger, and where two records
  disagree the later, guarded instrument wins (noted inline: the area ceiling is
  11's, not 09's).
* Runs 40–50 have instruments and ledgers but the run log stops at 39; §2.5's
  figures come from `17`/`18` and `workspace/push/leech_comb.json`.
* The GLM reading in §5 is an interpretation, not a measurement. It is offered
  because it predicts the two routes that pay (§6) and the four that do not, which
  a leaderboard-only reading does not.
* No score is claimed and no row changed. Sixty-five paths under this subproject
  remain uncommitted; this document adds one of them.

## 9. Files

* this document — `19-COLLECTION-AND-REVIEW.md`
* records read: `00`, `01`, `02`, `04`, `05`, `09`, `11`, `12`, `13`, `14`, `16`,
  `17`, `18`; ledgers `workspace/push/{leech_comb,leech_map,leech24_design,
  motif_spin,cascade_predict,leech_audit_fix,pl32_sweep,writeoffs}.json`
* the guards: `python3 scripts/sqscore.py` (score) and
  `python3 scripts/record_guard.py` (record)
* the G-1 record — `20-R1-ATOMS.md`, `scripts/r1_atoms.py`,
  `workspace/push/r1_atoms.json`
* the G-2 record — `21-SEAM-WHEELS.md`, `scripts/seam_wheels.py`,
  `workspace/push/seam_wheels.json`
* continued in §12: `27-BUI-STAIRCASE.md`, `28-EXPRESSIVENESS-LADDER.md`,
  `29-SAT-PROBE-AND-RESOLUTION.md`, `30-EARNED-FREE-SET.md`, with instruments
  `bui_wheel.py`, `ladder.py`, `disj_census.py`, `sat_probe.py`,
  `resolution_probe.py`, `extreme_probe.py` and ledgers of the same names
* run 68 — the algebraic-word framing, audited claim by claim against the
  delivered table: `31-GLM-ALGEBRAIC-WORDS.md` (three closures confirmed, four
  figures corrected, one external result entered as reported, one nomination
  recorded unpriced)
* run 69 — the wall margin defined and computed on all 1000 rows, then spent on
  one row: `32-WALL-MARGIN-AND-BRANCH-ROT.md` with `wall_margin.py` and
  `branch_rot.py`, ledgers `wall_margin.json` and `branch_rot.json`. 184/656/819
  are mid-table, not special; n = 18 searched over 5,560 cells, 0 gains; the
  s(11) proved/open contradiction recorded, not resolved
* run 70 — the cent-compiler contract audited and its T1/SAT-axis-branch flip
  implemented: `33-CENT-CONTRACT-T1-GLIDE.md` with `t1_glide.py` and ledger
  `t1_glide.json`. 7,803 cells at n = 18/20/30 (base + 1/2-edge branch flips +
  re-worded flips), 0 feasible, 0 gated, 0 gains; four card figures corrected,
  one test case rejected as ill-posed (n = 5 is proved)
* continued in §10: `22-DIAMOND-MASK.md`, `23-SEED-WHEELS.md`,
  `24-N10-OPTIMAL.md`, `25-OPEN-ROW-CROSSWALK.md`, `26-FRONTIER-CROSSWALK.md`,
  and their instruments `diamond_mask.py`, `seed_wheels.py`, `optima.py`,
  `crosswalk.py`, `frontier.py`, `parse_tt.py` with ledgers of the same names
  (plus `tt.json`), and the raw catalogue pages kept in `workspace/raw/`

---

## 10. Runs 52–61 — the G-2 campaign, in order

### 10.1 What was being asked, and the rules it was held to

The direction was G-2 read literally: **build declared grammars ("wheels") for the
open columns, certify them exactly, and rank candidate rows by verified score
impact rather than by bound slack.** A reviewer set four standing rules, and every
run below was checked against them:

1. a general lower bound with a large gap is **not** room (n = 10 is the witness —
   L9);
2. a catalogued geometry is a **nomination** until an exact builder plus the
   canonical scorer certifies it (§2.6, L6);
3. price a column only if the family has an **explicit extension rule**, and price
   it **per legal start, forward only** — never by replaying a slack backwards;
4. every wheel declares its **scope**, so a refusal says what was excluded rather
   than only that nothing gated.

Runs 52–61 are the record of applying those rules and of the three places where
they caught this campaign's own errors.

### 10.2 Run by run

| run | instrument | what it did | outcome |
| --- | --- | --- | --- |
| **52** | `record_guard.py` | guard on the written record, alongside `sqscore.guard` | implemented; ten documents corrected; passes since |
| **52** | `r1_atoms.py` | G-1: exact t-basis of every delivered `k²+1` row | **falsifier fired** — k ≥ 25 uses the same t-multiset as k = 8..24, so the δ step is arrangement, not a word (`20`) |
| **53** | `seam_wheels.py` | reconstructed both r = 1 atoms from integers in ℚ(√2), then solved the seam by LP | n = 65: p = 5, 8+8 columns, δ = `5/√2 − 3`. n = 626: p = 17, 25+24, δ = `17/√2 − 23/2`. **All 12 full-diamond rows return exactly the delivered algebraic side**, pinned and free; penetration 0; no tilted square touches a wall (`21`) |
| **54** | `diamond_mask.py` | the "block" was mis-declared: the tilted part is a five-deep diagonal **strip** | every number in 53's seam pricing corrected. Re-priced per legal start, forward only: **`now` = 0 for every delivered column**; best base-less start r = 38 at n = 614 → **0.058535**; optimistic per-start bounds 0.971 (r = 1, n = 10) → 0.401 (r = 8, n = 108). Reconstructs n = 226 as a 5×5 full diamond, 325 / 530 / 577 as 19×5, 26×5, 29×5 strips; all boundary edits cost 0.76–0.92, **0 gains** (`22`) |
| **55** | `seed_wheels.py` | two-tilt grammar spun at n = 10, the one row where the optimum is known | 436 cells, 80 certified, **0 gains**; wall-anchored best = **4.000000** (the grid), centred best = **3.707106791** = the delivered row, i.e. the optimum. `describe_two` reconstructs n = 290 as two frames (25+25, offset 0.2721·√2) and n = 226 as one frame (`23`) |
| **56** | `optima.py` | battery of published optimality proofs | **42 proved rows, at = 42, above = 0, below = 0.** n = 10 = `3 + ½√2` exactly (Stromquist); Karakuş's 3.192582 is **0.514524 below the optimum**, i.e. not a packing of ten unit squares (`24`) |
| **57** | `crosswalk.py` | 12 open rows against published constructions | 10 `at_published`, **2 `beats_published`** (n = 28 by 3.98e-3 vs Göbel's `3+2√2`; n = 29 by 5.67e-4), **0 above**. Forward value at the published side = 0.000000 on every row. n = 11 identified as Trump's construction (Δ = −8.5e-9, angle 49.8181° ≡ 40.1819°, below the 0°/45° optimum 3.885618) (`25`) |
| **58** | `frontier.py` | all 1000 rows against the catalogue | 231 at / 56 beats / 713 unresolved, **0 targets** — but computed on a **wrong reading of the catalogue's rule** (`26` §1–§3, now marked superseded) |
| **59** | `frontier.py` + `packlib.verify` | rule corrected to the catalogue's own words ("the closest packing shown to the right of *n*") | 316 rows resolved, **0 targets**. The suspicion that the 56 beats were a label-offset artifact was **refuted** — values sit next to their own *n*; 61 rows are same-*n* comparisons. Validity confirmed: every row holds exactly *n* squares, `packlib.verify` passes 51 sampled rows at worst_pen −1.3e-10..−2.6e-10 (`26` §8) |
| **60** | `parse_tt.py` | the page fetched with `curl`, not the truncating reader | 230,852 bytes, **215 entry cells**, 0 unparseable. Structural finding: **the triangular table's scope ends at n = 324** (complete file, zero `square-<n>.svg` links above it) |
| **61** | `frontier.py` | corrected again: the trivial grid is **not** the catalogue's best known above 324 | final state **325 rows determined (246 at, 79 beats, 0 above); 675 open** with `best_known = null` (`26` §9) |

Totals across the campaign: **no row of the table was changed and no score was
claimed.** Every run is read-only with respect to the submission.

### 10.3 What the campaign established

Four positive results, each with a witness:

1. **The r = 1 seam is exactly solvable.** Both atoms are reconstructible from
   integers in ℚ(√2), and an LP over (side, diamond translation) with one declared
   separating axis per seam pair reproduces the delivered algebraic side exactly on
   all 12 full-diamond rows. The atoms are mirror-symmetric, so mirroring the block
   is a no-op, and turning the seam costs `3√2/2 − 1` — the boundary is already
   optimal for this arrangement.
2. **The δ step is carried by the diamond, not by a new word.** `5/√2 − 3` for
   k = 8..24 against `17/√2 − 23/2` for k ≥ 25 is the same alphabet `{axis, π/4}`
   with a different coefficient, carried by a 17×17 diamond that is half-full at
   k = 24 (145/289) and full from k = 25 (289/289, side 17√2 — the zero-waste 45°
   block). Across all 31 rows the field of δ is the field of the alphabet.
3. **Proved rows are out of the ranking, and that is checkable.** 42 rows are
   proved optimal and the table sits at the optimum on all 42. n = 10 and n = 11
   are both *below* their proved optima — which is how we know a published
   lower-bound gap at those rows is a phantom, not an opportunity.
4. **The table already holds two published improvements** — n = 28 over Göbel's
   `3+2√2` and n = 29 over the 2025 record — certified by the canonical scorer.

And one negative that closes a route: **importing is closed**. Across the 325 rows
the catalogue determines, there is no row where a catalogued construction beats the
delivered one; the best whole-column bound from a fresh base-less start is
0.058535 against a 0.163635 gap, so G-2 cannot close the gap even on its own
optimistic pricing.

### 10.4 Corrections this campaign had to make to itself

Recorded because they are the same failure as §2.6 and §4.2, and because the count
matters: **eight** defects, five of them caught by a check rather than by review.

| defect | run | caught by | fix |
| --- | --- | --- | --- |
| LP zeroed `cL` while the side was pinned | 53 | a row returning the wrong side | pin carried through the solve |
| orientation matching sorted on dense rows | 53 | wrong atom pairing | match on declared orientation, not sorted keys |
| `frac` wrap-around read one lattice as `24+1/three` | 54 | frame total ≠ n | residue check on the recovered lattice |
| residue filter missing in `cascade_rank` | 54 | column replay crossing residues | filter `nn − isqrt(nn)² == r` |
| pair shapes declared as 3 classes where D4 gives 2 | 52 | class count ≠ orbit count | collapse under D4 |
| comparison rounded at 6 dp, turning the finalizer pad into 1e-6 | 56 | a "match" that was a pad | compare at 1e-9 with the pad declared |
| ad-hoc float verifier misused `seam_wheels.EXT/AXES_OF` → `+2.9e-1` penetrations on rows that match to 2e-9 | 59 | `packlib.verify` disagreeing | **retracted in the same run**; `packlib.verify` is the only verifier used |
| the catalogue's coverage rule read from the wrong page statement | 58 | a 0.479 margin at n = 677 | corrected at 59, then 61 (§10.5) |

### 10.5 The two errors in the record itself

Both were in the *instrument*, not the table, and both are worth keeping:

**The wrong rule (58 → 59).** The catalogue's gallery page says "for the n ≤ 324
not pictured, the trivial packing is the best known"; its triangular page says "for
the n not shown, the closest packing shown to the right of it is the best known".
Taken at face value the second is the stronger statement, and 58 used the first.
The error could only *hide* targets (it made the delivered side look better), which
is why the zero-target result survived it — and is now measured against a value
that is ≥ the true one.

**The trivial fallback (60 → 61).** To reach 1000/1000 the last 675 rows were given
the trivial grid. That is a confident-looking comparison in the direction that
hides targets, and the catalogue's own numbers refute it: it carries the `s(k²+1)`
family at a constant offset — 145 → 12.5355339, 170 → 13.5355339, 197 → 14.5355339,
226 → 15.5355339, 290 → 17.5355339 — and applied at 325 = 18²+1 that gives 18.5355
against the trivial 19. The tell was n = 677 = 26²+1 coming out 0.479 below 27: an
ordinary family member, not a record. Those 675 rows are now `null`.

### 10.6 Lessons added

**L9. A general lower bound with a big gap is not room.** n = 10 is proved optimal
at `3 + ½√2` = 3.7071; Karakuş's 3.192582 sits 0.514524 *below* the optimum, so it
is not a packing of ten unit squares at all. Any pricing that treats such a gap as
available is pricing a phantom — and the project published exactly that claim once.

**L10. A catalogue is a nomination, and a catalogue's *rule* is a second,
separate claim.** Two pages of one catalogue state different coverage rules; the
weaker one understates best-known on about a hundred rows. Read the rule, quote it,
and test it against the catalogue's own numbers before building on it.

**L11. "Resolved" is a claim about the source, not about the instrument.** Coverage
moved 287 → 316 → 325 → (briefly, and falsely) 1000 → 325 with no row changed and
no new mathematics. The number worth stating is how many rows the source
*determines*, and it has to be stated with its basis attached.

**L12. When a comparison produces a huge margin, suspect the comparison before the
record.** This project has now paid for this twice — `area_ceiling` at 593.279, and
the 1000/1000 count whose tell was a 0.479 "improvement". Being fast at the wrong
comparison is the most expensive failure mode here, and the check that catches it is
cheap: ask what the number would mean physically (a density, a square count, a
family membership) before believing it.

### 10.7 Status of the four moves

| move | status |
| --- | --- |
| **G-1** r = 1 atom as a field element | **closed** — falsifier fired at run 52: same t-multiset on both sides of the δ step, so the step is arrangement, not vocabulary |
| **G-2** open a column with a declared wheel | **closed as an import route** by verified impact: 0 targets over the 325 rows the catalogue determines, and the best whole-column bound (0.058535) is below the gap (0.163635) even optimistically. The wheel work itself succeeded — three exact wheels built and certified, each refusing with a named scope |
| **G-3** the expressiveness ladder | **delivered, run 63** — `28-EXPRESSIVENESS-LADDER.md` + `scripts/ladder.py`: six rungs, **4 recomputed and checked, 2 honestly quoted** (float/scan, rigidity). The sixth rung is the catalogue's own n ≤ 324 boundary |
| **G-4** the relation potential as a ranker | **open** — still the best learned object here (geo 0.782, 0 worse); the frontier refit and its two destroyed controls are unrun |

### 10.8 What is still owed

* **The 675 rows above n = 324.** Not a mathematics problem: they need a source
  with above-324 coverage (a maintained flat grid, or the record list behind the
  five known records 626, 1453, 1765, 1850, 2043). No re-reading of this catalogue
  will produce it, because its own scope ends at 324.
* **The Lean build** the owner owes, which is what would make the tower and the
  codec formal rather than Python-and-prose.
* **Bui's construction — done and refused (run 62).** Source identified
  (arXiv:2508.04603v2), §3.1.1 implemented exactly over ℚ, 132 cells, **132/132
  verified by `packlib.verify`, 0 gains** (best −0.078). The primitive is a
  slanted band: sealed in a square its density is 0.23–0.82 against the table's
  ≈0.95. Reopening it needs §4 (trapezoid) + §5 (square reduction), not another
  spin — see `27-BUI-STAIRCASE.md`.
* **The `cent_discovery` n = 11 selftest control**, which still fails on a
  pre-existing defect (8 tilt angles against a 0/45/90 kick family).

### 10.9 Re-running the campaign

    python3 scripts/sqscore.py            # 22.218056945, 553 beats, 1000 rows
    python3 scripts/record_guard.py       # record consistency (must exit 0)
    python3 scripts/seam_wheels.py --selftest      # 20/20
    python3 scripts/diamond_mask.py --selftest     # 10/10
    python3 scripts/seed_wheels.py --selftest      #  7/7
    python3 scripts/motif_wheels.py --selftest     # 13/13
    python3 scripts/optima.py             # 42 proved rows, at = 42
    python3 scripts/crosswalk.py          # 12 open rows, 0 above
    python3 scripts/parse_tt.py           # catalogue -> workspace/push/tt.json
    python3 scripts/frontier.py           # 1000 rows classified, 0 targets

Ledgers land in `workspace/push/`; the raw catalogue pages kept for audit are in
`workspace/raw/`. Nothing in this list writes to the submission.

---

## 11. The SAT / disjunctive model: what we have and haven't done (run 64)

**Question put to us:** write the packing as 3n poses with the separating-axis
condition per pair, enforce containment, minimise L — i.e. an exact geometric
constraint-satisfaction/optimisation model. Have we tried it?

Three different answers, because the question names three different things.

### 11.1 As the non-overlap *test*: yes, and it is the project's gate

The condition as stated,

    h_i(q) = ½(|q·u_i| + |q·v_i|)
    non-overlap(i,j)  ⇔  ∃ q ∈ {u_i, v_i, u_j, v_j} : |(c_j−c_i)·q| ≥ h_i(q) + h_j(q)

is **exactly** what `packlib.verify` evaluates. Its docstring, verbatim:

> pair penetration = min over the 4 SAT axes of (ext_i + ext_j − |d.axis|);
> overlap iff pen > 0 on all 4 axes; `worst_pen` = max over pairs.

with `ext` = the same half-width `h_i(q)`, and it exploits two proved facts of the
same family (the axis-owner's own extent is exactly ½; `ext_j(u_i) = ext_j(v_i)`).
Containment is the same expression `|x_i| + ½(|cos θ_i| + |sin θ_i|) ≤ L/2` in the
`w`/`h` it returns. So the model is not untried — it is the predicate that has
gated every row, every wheel and every import across 64 runs, and `ladder.py`
rung 3 depends on the same machinery. If the question is "do we have this exact
reformulation", the answer is yes, in production.

### 11.2 As an *optimisation with the disjunction fixed*: yes, and it has been decisive

`seam_wheels.lp_seam` minimises `L` over `(L, t_x, t_y)` subject to one **declared**
separating axis per binding pair — precisely the θ-fixed, branch-assigned member of
this model family. Results: it reproduces the delivered algebraic side exactly on
all 12 full-diamond r = 1 rows, and re-pricing every column with it forward-only
gives `now = 0` (no delivered column gains from re-placing its own base) and a best
base-less bound of 0.058535. So the LP member of the family has been run and has
already closed a route — with the honest caveat recorded in `21` §9: it certifies
*feasibility for the declared axes*, not optimality.

### 11.3 As the *global* disjunctive solve: no — and here is the measured reason

Nothing in the tree uses a MILP/CP-SAT/z3/branch-and-bound formulation: `grep` for
`ortools|pulp|milp|big-M|cpsat|disjunct|branch_and_bound` across `scripts/` and every
document returns **zero** files. Only `scipy` is installed (no `ortools`, `pulp`,
`z3`, `cvxpy`, `mip`). So the model as a global optimiser is genuinely untried.

`scripts/disj_census.py` (new, `disj/1`) measures what it would face. For each
delivered row, over all `n(n−1)/2` pairs: how many are **tight** (pen ≤ 1e-9, i.e.
the disjunction is load-bearing), how many are slack, which of the four axes
resolves each tight pair, and the naive branch count `4^pairs`.

| n | pairs | tight | tight % | slack | `4^pairs` |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 10 | 45 | 11 | 24.4 % | 34 | 1e27 |
| 11 | 55 | 14 | 25.5 % | 41 | 1e33 |
| 25 | 300 | 72 | 24.0 % | 228 | 1e181 |
| 50 | 1225 | 105 | 8.6 % | 1120 | 1e738 |
| 100 | 4950 | 342 | 6.9 % | 4608 | 1e2980 |
| 200 | 19900 | 638 | 3.2 % | 19262 | 1e11981 |
| 500 | 124750 | 1019 | 0.82 % | 123401 | 1e75107 |
| 1000 | 499500 | 3811 | 0.76 % | 495689 | 1e300729 |

Two readings, both useful:

1. **The disjunction is almost entirely slack.** At n = 1000 only 0.76 % of pairs
   bind; 99.2 % of the model's disjunctions are inactive at the optimum. So the
   combinatorics of this formulation *is* the combinatorics of the contact set.
   And rungs 4–5 of the ladder say the contact set carries no score information
   (`R² = |E|`; WL beats its null only on a contact-bearing ensemble). A global
   solver here would spend its whole budget scheduling contacts, which is a
   quantity we have already measured to be score-blind.
2. **Branch count is hopeless by enumeration**, and the tight set is not small:
   n = 10 already has `4^45 ≈ 1e27` branches with 11 tight pairs; a CP-SAT would
   have to be driven by warm starts and large-neighbourhood moves — which is what
   `diamond_mask.py` already does (trim / boundary run / move row end), at
   **0 gains** across its cells.

The axis census also shows the structural asymmetry: for n = 1000 the resolving
axis is square *i*'s own axis in 3,811 of 3,811 tight pairs (`u_i` 2146, `v_i`
1665, `u_j`/`v_j` 0) — i.e. with a canonical index order, the disjunction
effectively collapses to *two* branches per pair, not four. That halves the
exponent and changes nothing about the count above.

### 11.4 Why even a perfect global solve would not hand us the score

`L1` (energy is a gate, not a landscape) is the substantive objection, and it is
independent of the solver: on this model the feasible set at side `L` has `E = 0`
*exactly*, so the objective is flat across all feasible poses and the only signal
is at the boundary. That is why 0/8 gated at the push wall under five objective
weightings, and why delivered rows are bit-identical fixed points of their own
relaxer. A CP-SAT at fixed `L` would answer *feasibility* — which for rows the
table already occupies is the wrong question, and for rows it does not is exactly
the open problem in 26 §9.

### 11.5 What would actually be worth building

If someone does want this formulation implemented, the version with a chance is
**feasibility at fixed L with a warm-start neighbourhood**, not global minimisation:

1. fix the side to `L_delivered − ε` for a target row;
2. allow only `k` squares to move (the `diamond_mask` grammar, `k` ~ 8–20);
3. give the solver the tight-pair set of the delivered state as its branch
   assignment (2 branches per pair by 11.3);
4. require a certificate from `packlib.verify` plus the exact gate.

That is a bounded, falsifiable experiment, and it is the only shape in which the
model is not asking a score-blind question.

**Run at run 65 — see `29` Part A.** With θ frozen and the delivered axis
assignment frozen the model is exactly an LP, so feasibility is a certificate rather
than a heuristic. Result: **18 cells (6 slack-heaviest rows × k = 8, 12, 20),
0 feasible at any ε ≥ 1e−6, 0 gains.** Every refusal is diagnosed, not merely
reported: after removing the k free squares the *rigid core still spans the full
side*, so the side is not theirs to lower. Same fact as `L7` — the walls pin the
packing.

**Corrected at run 67 — see `30`.** That free set made the refusal circular. Growing
the free set from the squares that actually achieve the four extremes, through their
tight-pair partners, the core stops spanning only at k = 161 / 184 / 267 / 298 of
n = 294 / 295 / 299 / 298 (55–100%), and the LP **still refuses at every one of
those k and every larger ring up to k = n.** At k = n the refusal is a certificate:
the delivered side is the exact optimum of the declared-axis, fixed-orientation LP.
The original LP had three defects (sign order, inequality direction, separation
constant) and now carries the permanent check `sat_probe.py --selftest` — *the
delivered state must be feasible at its own side* — which fails on any of them.

### 11.6 Files

* `scripts/disj_census.py` — per-row tight/slack pair census, `disj/1`.
* `workspace/push/disj_census.json` — the table above, plus axis counts.
* `scripts/packlib.py` — `verify`, the SAT predicate itself (§11.1).
* `scripts/seam_wheels.py` — `lp_seam`, the declared-axis LP (§11.2).

---

## 12. Runs 62–67 — the theory closure, in order

With G-2 closed by verified impact, the campaign turned from *what can be searched*
to *what can be decided*: each run either prices a nominated route exactly or states
a boundary the material has actually reached. No row of the table changed.

### 12.1 Run by run

| run | instrument | what it did | outcome |
| --- | --- | --- | --- |
| **62** | `bui_wheel.py` | the Bui nomination (arXiv:2508.04603v2) implemented exactly — §3.1.1 in ℚ, sealed in its bounding square with a greedy cell fill; the figure-dependent §3.1.2 closure explicitly **not** claimed | 132 cells, **132/132 `packlib.verify`, 0 gains**; best cell −0.078 (n = 294, L = 19 vs 17.6568); density 0.227–0.823 against the table's ≈0.95. Recorded bug: squares rotate by **−θ** (`27`) |
| **63** | `ladder.py` | G-3 delivered: six expressiveness rungs, each computed here or quoted with its source | **4 recomputed and checked, 2 honestly quoted** (float/scan, rigidity). Rung 3 (the Λ₂₄ resolution sweep) is the load-bearing one: tilted rows illegal **87/87 at all eight scales**, untilted legal **168/168** somewhere — coarsening never creates the structure (`28`) |
| **64** | `disj_census.py` | the SAT/disjunctive model audited as a decision procedure, not a slogan | at n = 1000, **3811/499500 pairs tight (0.76 %)**, each effectively 2 branches → **1e300729** leaves. The model is decisive *with the disjunction fixed* and untouchable without it (`19` §11) |
| **65** | `sat_probe.py` | the §11.5 bounded experiment: feasibility at `L₀−ε`, θ frozen, delivered axis assignment frozen, six slack-heaviest rows × k ∈ {8,12,20} | **18 cells, 0 feasible, 0 gains** — but the free set was chosen by wall contact, so the refusal was **built in**, and the LP carried three defects. Withdrawn and superseded by run 67; the `rigid core spans` filter is outside the LP, so those refusals stand as facts, not as findings (`29` Part A + erratum) |
| **66** | `resolution_probe.py` | the resolution-reduction / dithering question, tested against the *answers*: snap ten delivered rows to a `1/m` lattice | **invalid at every m, including m = 128** — at an optimum every load-bearing contact has penetration exactly 0, so any displacement opens a violation elsewhere. Side loss −0.0050 at m = 128 (irrelevant: the gate is binary); at m ≤ 4 it exceeds the gap (−0.1643 at m = 2 with θ snapped). Dithering has no admissible residual here (`29` Part B) |
| **67** | `extreme_probe.py` | the §11.5 probe with an **earned** free set: seed with the four extreme achievers, grow by tight-pair rings, price every ring where the core stops spanning | core stops spanning only at **k = 161 / 184 / 267 / 298** of n = 294 / 295 / 299 / 298 (55–100 %); the LP **refuses at every such k and every larger ring up to k = n**. At k = n that is a **certificate**: the delivered side is the exact optimum of the declared-axis, fixed-orientation LP (`30`) |
| **68** | — | the proposed algebraic-word framing, audited against the delivered table | **three closures confirmed** (run 5: 280 certificates, 0 conversions; run 52: same `{axis, π/4}` alphabet across the 0.520815 step; run 55: 436 cells, 80 certified, 0 gains). **Four figures corrected**: the 45° rung carries 43.2 % of the total gain and 23.2 % of the 553 beats, not 70 %; no ledger holds a `0.67k + 4` density wall; `n = 184/656/819` are **at the grid** (`L = k`, gain 0, `r = 12/20/22`) so the quoted margins are not reproducible and the nomination is unearned; and T-298 (`s(k²−5) = k`) is **external and reported**, its 25-row contact check (`n = 44…956`) showing 25/25 at grid (`31`) |

### 12.2 What these runs established

* **The catalogue's boundary is 324, and it is the catalogue's, not ours.** 215
  cells, zero `square-<n>.svg` above 324; `s(k²+1) = k + 0.5355339` proves trivial
  is not best-known above it. 675 rows are open for want of a source, not for want
  of method (`26` §9).
* **A nomination is priced, not dismissed.** Bui's construction was implemented to
  the letter and refused on measurement (density, not opinion), with the part that
  could not be built named as not built.
* **Coarsening is dead twice over.** The Λ₂₄ scale sweep (rung 3) and the lattice
  snapping test (run 66) both fail at every scale, for the same reason: the paying
  structure is algebraic, and contacts are equalities with no neighbourhood.
* **The declared-axis LP is now a certificate over whole rows, not one seam.**
  `lp_seam` pinned the 12 full-diamond rows; run 67 extends the same statement to
  all n squares of a row, and it holds at ε = 1e−6.
* **Where the residue actually lives.** Not in a k-neighbourhood (runs 65–67), not
  in resolution (66), not in a bigger catalogue read (60–61): in the **branch
  assignment and rotation**, which is `L4`–`L6` and the 0.76 %-tight census.

### 12.3 The error this session had to correct in itself

The §11.5 probe was wrong twice — once circularly (run 65: a free set that
guarantees its own refusal) and once arithmetically (three LP defects: global
translation in pair rows; `i`/`j` coefficient order plus a `≤` where the condition
is `≥`; and `h_i + h_j` instead of `0.5 + Eu[owner, other]`). All three were caught
by one invariant that should have existed from the start: **the delivered state must
be feasible at its own side.** It is now `sat_probe.py --selftest` (6/6) and runs
with the check batch.

**Consolidation after run 70.** That defect survived because the same constraint
system had three copies — `sat_probe.solve_lp` (65/67), `branch_rot.lp_feasible`
(69) and `t1_glide.lp` (70) — and copies drift by one term. There is now one:
`scripts/declp.py` holds `solve` (the declared-axis LP), `gate` (12-dp state,
`packlib.verify`, canonical gain), `price` (the ε ladder), `max_shrink`, the
geometry tables and the exact word alphabet. Each caller keeps only its own
declared profile — `branch_rot`/`t1_glide`: every translation free, 5e−10 pad, free
offsets within ±2L; `sat_probe`: a free *subset*, no pad, ±L — so a difference that
was an accident of copying is now a named argument. `sat_probe.solve_lp` remains as
a signature-only shim for `extreme_probe` and the run-65/67 record; a dead
`optima.PROVED` import that never read a live attribute is gone. The old copies and
the new builder were compared on 235 sampled cells (feasibility, centres, flags,
contact lists, the `max_shrink` bisection, the cell enumeration): identical. The
three ledgers were regenerated and diff to zero — 18 cells at n = 294…300, 5,560 +
1,171 cells at n = 18, 7,803 cells at n = 18/20/30 — and `declp.py --selftest`
states the invariant on 46,672 declared branches, 22,705 of which the old
own-extent form would have understated.

### 12.4 What is still owed

Unchanged from §10.8, with one addition:

* **675 rows above n = 324** — needs a source with above-324 coverage.
* **The Lean build** — what would make the tower and codec formal.
* **G-4** — the relation potential as a ranker: still open.
* **New: rotation + branch search at one row.** Every instrument now points at the
  same object — which pair is tight on which axis, and what a rotation does to that
  assignment. Nothing in 62–67 touched it, because a branch-aware search is a
  different instrument, not a wider LP.

### 12.5 Re-running 62–67

    python3 scripts/bui_wheel.py --selftest        # 8/8
    python3 scripts/ladder.py                      # 6 rungs: 4 checked, 2 quoted
    python3 scripts/disj_census.py                 # 3811/499500 tight at n=1000
    python3 scripts/sat_probe.py --selftest        # 6/6  (the invariant)
    python3 scripts/declp.py --selftest            # same invariant, the one builder
    python3 scripts/sat_probe.py                   # 18 cells, 0 feasible
    python3 scripts/resolution_probe.py            # 7 resolutions, validity table
    python3 scripts/extreme_probe.py               # rings -> k(unspan) -> LP

Archives of the fetched pages (`bui.html`, `triangular_table.html`, `gallery.html`)
are in `workspace/raw/`; every ledger lands in `workspace/push/`. None of these
writes to the submission.
