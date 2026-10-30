# Status — archive of closed rounds and closed candidates

*Moved into `archive/` from [`STATUS.md`](../STATUS.md) in Phase 111, when the
status document was cut down to a list of what is still to do. Only the
relative link prefixes were adjusted for the new depth, and the inline-figure
markers were taken out with each value left as it stood, because a record
holds no live figure; no sentence and no number was touched. The full record of every round is
[`MASTER_PLAN.md`](../MASTER_PLAN.md) and
[`archive/MASTER_PLAN_ARCHIVE.md`](MASTER_PLAN_ARCHIVE.md); this file keeps the
status document's own running account, as it stood at the close of Phase 110.*

<!-- figures:history -->

*Everything in this file is an archive: each paragraph records what was
measured when it was written, and those counts are deliberately left alone.
For the project as it is now, see [`STATUS.md`](../STATUS.md),
[`SYSTEM.md`](../SYSTEM.md) and [`FIGURES.md`](../FIGURES.md).*

---

## 1. The round-by-round account (Phases 46–110)

**Just closed: Phase 110** (the record is [`MASTER_PLAN.md`](../MASTER_PLAN.md),
"Phase 110"; the study is
[`STRAY_BLIND_STUDY.md`](../studies/STRAY_BLIND_STUDY.md), with 4 of 4 marks
met). **Lattice item 10:** which pairs a stray-blind reading must conflate.
`RequestProject/GLM/StrayBlind.lean` has no sorry and proves the answer.
Two emission records of equal size have the same distance profile exactly
when their stray spectra agree, whatever the hole types
(`distances_eq_iff`), because the arrivals all sit at the one covering
radius. Every stray-free pair is conflated, and a reading blind to strays as
well conflates every deep hole. `reasoning/stray_blind.py`
(`tools stray-blind`) checks the prediction against the escalation ladder's
own ensembles. At 240, 480, 960 and 1920 starts the predicted pairs equal
the measured `L₃` conflations: `A_1^24`/`A_2^12`, the only two stray-free
holes, all ten holes at one radius. **Item 6:** a conflated pair makes the
separation criterion fail at every spread (`not_resolves_of_indist`), so the
`L₃` rung never reaches `ρ < 1` at a measured size. Item 6 stays open,
narrowed to the share-carrying rungs. **The Phase 109 close, finished:** the
`report-relay` pin and the hand-quoted counts were brought into line, the
missing tests README row added, and the stage-0 cache census now re-reads a
cache re-taken in a subprocess instead of reporting it still stale.
`tests/test_stray_blind.py`.

**The round before: Phase 109** (the record is [`MASTER_PLAN.md`](../MASTER_PLAN.md),
"Phase 109"). The three items the sharpening pass left, and the close made a
single pass. **Four or more degrees of freedom stepwise:** when `M` is
positive definite, `derivation._linearise` no longer hands a quartic or
quintic in letters to the branch layer (where a quartic ran for minutes);
the decision point `modes.higher` takes **ferrari** for four (the
characteristic quartic depressed, its resolvent cubic solved by Viète, the
four `w^2` from square roots of the resolvent's roots, all real and
positive) and **named** for five or more (no general radical form, so the
roots are named `w2_1 >= ... >= w2_n` through the coefficients, with their
sum and product stated); a pair that is not definite keeps the **solver**
route. The quadruple and quintuple pendulum are answered and verified in
seconds; the column-3 check counts the real roots by Sturm on the
characteristic polynomial (and on the resolvent for a quartic) and rejects
a mutant. **The discriminant's sign by factorisation:**
`reasoning/sign_factor.py` takes the square-free factorisation (Yun) and
decides the sign when every odd-power factor is plainly signed and every
even-power factor is a square, so `x^3 + 3*(a - b)^2*x = 2*(a - b)^3`
takes Cardano and `x^3 - (a^2 + a*b + b^2)*x + a*b*(a + b) = 0` takes Viète
instead of the case split (the decider `cubic.letters:factor` switches it
off for A/B readings). **`report routes`:** every decision point, its
routes and deciders, what is switched off, and one reference problem per
route run live -- 3 points, 8 routes, 9 of 9 reference problems as
expected, every route reached. **The close in one pass:** `signoff --close`
re-takes stale measurement caches first (stage 0), runs every counted unit
with the document checks (`test_corpus`, `test_figures`, `figures`) held
back, refreshes the corpus only when they are owed, and then runs them; the
run-measured figures are masked from the package units' digests and the
session notes are out of every unit closure but the document checks, so the
refresh does not make the package stale again ([`ITERATE.md`](../ITERATE.md)
§0). `RequestProject/GLM/QuarticResolvent.lean` (Ferrari's resolvent and
the recovery of the four roots) and `RequestProject/GLM/SignFactor.lean`
(the sign of a factored form) have no sorry. `tests/test_route_choices.py`.

**The round before: a sharpening pass after Phase 108** (not a numbered round;
the record is [`MASTER_PLAN.md`](../MASTER_PLAN.md), "Sharpening pass after
Phase 108"). At the owner's request: pytest is noted as missing from this
environment (`python3 -m pip install pytest`; the sign-off commands check
for it); the cubic routes are now *chosen* by the GLM per problem through
`reasoning/routes.py` (each route with the fact that makes it sound, the
choice and its reason written into column 2), not reached through a switch;
a cubic in letters whose discriminant sign is not decided is answered **by
cases** (Cardano's root when `4p^3 + 27q^2 > 0`, Viète's three roots when
`< 0`, each branch checked); and the **unequal triple pendulum** — which ran
for more than fifteen minutes — is answered and verified in about two
seconds (a monomial fast path in `poly_gcd`; `M` and `K` read off the
Lagrangian's Hessian and found positive definite by Sylvester's criterion,
so the modes take the **stepwise** route: the characteristic cubic's
coefficients, then `P`, `Q`, `K`, then the three Viète `w^2`, checked
against the script's own `det(K - w^2 M)` and counted by Sturm). A review of
the wiring fixed six places where a capability was built but not reached:
plain `solve ...` / `roots of ...` phrasings, a reverse-surface refusal now
handed to the symbolic frame (also from `GLM.py -q`), the chain-pendulum
frame reading "normal modes" / "equations of motion" / "small
oscillations", the unequal double pendulum's radicand, tracked bytecode, and
two aged evaluation pins. `tests/test_sharpening.py`, 17 tests. What it
left (four or more degrees of freedom stepwise, a discriminant sign decided
by factorisation, a report subject for the route trace) Phase 109 took.

**Before that, Phase 108 took the first limit of the cubic
radical study's §8, a cubic in letters with three real roots**
([`CUBIC_TRIG_STUDY.md`](../studies/CUBIC_TRIG_STUDY.md)), at the owner's
request for another item while Phase 107's close was finished (the corpus
refreshed, the test runner installed where it was missing, the collected
count re-taken). Phase 104 refused such a cubic (`NONLINEAR`, no real
radical form), and the refusal blocked the normal modes of
three-degree-of-freedom systems. The branch layer now answers it two ways,
behind the switch `TRIG` (off, it is Phase 104's exactly): when the
depressed coefficients scale together (`P^3/Q^2` a number), as a ratio of
the letters times a bracketed root of a rational cubic; otherwise by
Viète's form `2*sqrt(-P/3)*cos(acos(K)/3 - 2*pi*k/3)`, three roots in
decreasing order, each a generator whose relation is the cubic, with
`4*P^3 + 27*Q^2 < 0` stated. The identical triple pendulum's squared
frequencies are now `g*λ/l`, with `λ` the three roots of
`λ^3 - 9λ^2 + 18λ - 6`. The motion check verifies them exactly in `Q[t]/f`.
One Phase 104 reading printed Cardano's root under a condition no value of
the letters meets. It is now answered by the trigonometric form. 9 of 9
marks met: 4 of 4 homogeneous and 3 of 3 Viète cubics, 7 of 7 scripts and
7 of 7 mutants rejected, both three-degree-of-freedom systems, batteries
30 of 30 and 30 of 30, Phase 104's marks still met, 303 texts read with
the switch off and on and 0 moved. `RequestProject/GLM/CubicTrig.lean`
proves the trigonometric root, its domain, the order of the three roots,
that they are all the roots, and the homogeneous scaling, with no sorry.
[`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 108 is the record.

**The round before that (Phase 107) took the rest of track P, at the
owner's direction** ([`DERIVATION_TWO_STUDY.md`](../studies/DERIVATION_TWO_STUDY.md)).
Of the fourteen class-P outside questions Phase 106 left, eleven are
derivations and three (29, 39, 96) ask for accounts; the three were declared
to stay refused before any code, and do. Eight new operations, each with a
stand-alone column-3 script: **`prove information inequality: GIVENS |-
CLAIM`** (`reasoning/info_inequality.py` — an exact-simplex Shannon prover
that prints its certificate; a GF(2) linear distribution as counterexample;
a Farkas polymatroid witness when no Shannon proof exists, the verdict
`NOT_SHANNON` for Zhang–Yeung and Ingleton), **`decide unique
decodability`** and **`construct prefix code`** (Sardinas–Patterson with the
shortest ambiguous string; Kraft; the canonical code), **`derive rate
distortion function`** (Hamming; printed only where the Shannon lower bound
is tight, `NOT_TIGHT` on the gap), **`derive rate posterior`** (on the
machine's rate grid), **`derive maximum entropy density`**, **`solve
eigenvalue problem`** (Dirichlet, Neumann, mixed, periodic),
**`derive transmission coefficient`** (delta and step at one point) and
**`derive decimation-in-frequency fft`**. 11 of 11 marks met: inequalities
16 of 16, codes 11 of 11, rate distortion 5 of 5, maximum entropy 4 of 4,
eigenvalue problems 6 of 6, transmission/FFT/posterior 13 of 13, refusals
14 of 14; 55 of 55 scripts verify and 55 of 55 mutants rejected; 400 random
inequalities and 600 random codes, 0 unsound, 0 undecided, 0 disagreements;
outside questions 19, 28, 49, 52, 54, 55, 56, 59, 81, 86 and 95 now
answered, 0 of 292 other texts moved. Three of them (56 Kraft–McMillan, 81
compactness, 86 Tarski) are *Lean-anchored*: the general statement is a
theorem of `RequestProject/GLM/DerivationsTwo.lean`, which proves sixteen
theorems with no sorry (Gibbs, mutual information, soundness of the Shannon
certificates, data processing, McMillan, the radix-2 split, the delta
barrier, the ring and Dirichlet eigenfunctions, Lawvere and Tarski, a theory
with arbitrarily large finite models has an infinite model).
[`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 107 is the record.

**The round before those (Phase 106) took track P, derivations and proofs,
at the owner's direction** ([`DERIVATION_STUDY.md`](../studies/DERIVATION_STUDY.md)).
The owner judged the open retrieval items of round 9 (the AST index and
citation-scope follow-ups, N5, the document tree's §6) not to be producing
strong results; they are **parked**, with a *Disposition (Phase 106)* section
in [`AST_INDEX_STUDY.md`](../studies/AST_INDEX_STUDY.md) and
[`CITATION_SCOPE_STUDY.md`](../studies/CITATION_SCOPE_STUDY.md), and every
operation those rounds built stays. The machine now *derives* as well as
retrieves and checks, through four new operations: **`prove: PREMISES |-
GOAL`** (`reasoning/proof_search.py` — a terminating G4ip prover; a
tautology with no constructive proof is proved from the fewest instances of
excluded middle and shown non-constructive by a Kripke countermodel; a
non-tautology refused with a falsifying valuation), **`derive equations of
motion for …`** (Euler–Lagrange, linearisation and normal modes,
`reasoning/derivation.py`), **`derive transfer functions from … to …`** and
**`solve boundary value problem for Y(X): …`** (flux-form profiles). Every
answer carries a stand-alone column-3 script that shares no code with the
layer. 9 of 9 marks met: 16 of 16 proofs, 8 of 8 equations of motion, 6 of 6
transfer models, 6 of 6 profiles, 8 of 8 refusals as declared; 36 of 36
scripts verify and 36 of 36 mutants rejected; 2000 random formulas, 0
unsound, 0 gaps; outside questions 18, 24, 30 and 85 now answered, 0 of 299
other texts moved. On the way the nonlinear layer's crash on a cubic in
casus irreducibilis became a named refusal. Proved in
`RequestProject/GLM/Derivations.lean` (the prover's rules sound for every
valuation, Curry's derivation, the three shell profiles, the double
pendulum's modes). [`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 106 is the record.

**Earlier (Phase 105) took I3 of round 9, the AST address as
a retrieval key** ([`AST_INDEX_STUDY.md`](../studies/AST_INDEX_STUDY.md)).
Every statement-level expression that computes something — 3,438 in the live
code, 8,231 in the owner's archived GLM tree (`source_material/GLM-main.zip`)
— is held in a frozen index (`reasoning/ast_index.py`), keyed by a bucket key
that no renaming of variables and no change of operand order at a
commutative operator can move, and decided inside the bucket by an exact
structural matcher checked against a separately written brute-force
reference (8,398 of 8,398 calls agree). The new operation **where is
`EXPR` computed?** (also *where in the archive …*, *where in the live code
…*; `runtime/ast_index_frames.py`) answers with every structurally equal
site and the renaming that witnesses each, or with an empty answer that the
proved completeness of the bucket makes an answer. Under rename-and-commute
the structural key finds a structurally equal site at rank 1 on 467 of 467
query sites against 343 for the token overlap (124 : 0); the Phase 64
address, read as it is, moves under renaming on 94 of them and merges 23
classes that are not structurally equal. 5 of 7 marks met: A2 missed by one
declaration error (`(a + b) + c` and `a + (b + c)` are structurally equal by
a renaming), A4 missed as §0 of the study predicted. Proved in
`RequestProject/GLM/AstIndex.lean`. [`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase
105 is the record.

**Before those (Phase 104) the round took the nonlinear elimination study's
§6, at the owner's request: cubics, nested square roots, and the
positive-root convention** ([`CUBIC_RADICAL_STUDY.md`](../studies/CUBIC_RADICAL_STUDY.md)).
The branch layer of `solve symbolically` now answers a numeric polynomial of
degree 3 or more root by root as an exact bracketed algebraic number
(`root(t^3 - 3*t + 1, 0, 1)`, about 0.347296), using Sturm isolation and
factoring over the rationals up to degree 6 (`reasoning/symbolic_algebraic.py`);
answers nested square roots as towers (`x = ±sqrt(p ± sqrt(p^2 - q))`);
answers a cubic in letters by Cardano's root when it has one real root, with
that inequality stated; states the real condition on a radicand in letters;
and drops a non-real conjugate by deciding the sign of a constant radicand
exactly. Under the owner's rule (keep both tracks, default to the stronger),
a substitution reading given by the positive-root convention, or holding an
unknown it does not print, now consults the branch layer: the full branch
set is the default answer and the substitution reading is kept beside it
when its own script verifies. *Circle and line* now gives both points, with
neither unknown in terms of the other and no `m ≠ 0` condition. Both planted
conic batteries answer 60 of 60 with the planted point and 0 wrong (Phase
103: 19 of 60); 40 of 40 cubics. 8 of 9 marks met: the no-regression mark
was declared as "unchanged" and one Phase 98 reading (`x^2 + x = c`) gained
a stated real condition. Proved in `RequestProject/GLM/CubicRadicals.lean`.
[`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 104 is the record.

**The round before those (Phase 103) took nonlinear elimination, out of
order, because the owner asked this push to broaden the GLM's reasoning**
([`NONLINEAR_ELIMINATION_STUDY.md`](../studies/NONLINEAR_ELIMINATION_STUDY.md)).
The `solve symbolically` operation now has a second layer
(`reasoning/symbolic_nonlinear.py`), consulted only when substitution
refuses `NONLINEAR`: it isolates, splits on a coefficient that holds
unknowns, takes the roots of an equation left in one unknown (two rational
branches from a square discriminant, otherwise a named `sqrt(R)` with
`sqrt(R)^2 = R` and its conjugate), and eliminates by the resultant, then
checks every branch against every original equation. It answers 9 of 10
declared systems with exactly the declared branches — among them the elastic
collision (`v1 = u, v2 = 0` or `v1 = u*(m1 - m2)/(m1 + m2),
v2 = 2*m1*u/(m1 + m2)`) and two conics whose resultant offers four
extraneous pairs that the check discards — refuses 5 of 5 by name, and moves
no earlier answer (24 of 26 Phase 98 questions unchanged; the other 2 were
its `NONLINEAR` refusals). 4 of 7 marks met: one system was mis-declared
(Phase 98 answers it with the positive root only), and a planted battery of
random conics answered 19 of 60 with 0 wrong, the rest refused on a cubic.
The battery found a defect first — isolating through a coefficient holding
unknowns lost the solutions where it vanishes — repaired by a case split
before the marks were taken. Proved in
`RequestProject/GLM/NonlinearElimination.lean`.
[`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 103 is the record.

**The round before those (Phase 102) took N2 of round 9, the document tree
as a third native book** ([`DOCUMENT_TREE_STUDY.md`](../studies/DOCUMENT_TREE_STUDY.md)).
The document benchmark counts a section relevant exactly when it shares the
query's document, so the item's literal book — the section's document as a
Golay word — names the answer: it was declared as the leak control and scores
a hit at 1 on all 1,506 queries, as `GLM.DocumentTree.separating_key_head`
proves it must. The leak-free part of the tree, where in its document a
section sits, was measured as a third layer on a frozen snapshot of the
corpus (`reasoning/document_tree.py`, `tools document-tree`; 1,506 units, so
the figures no longer move with the documents): hit@5 / relatives in the top
five 324 / 413 against the raw lexical vector's 323 / 414, identical to the
two-book ranking on every query. The first two books tie across the top-five
boundary on only 30 queries, and the oracle third layer gains one query, so
no third book can carry the documents past parity. F1, F3 and F5 met; F2, F4
and F6 not met. N2 is closed in the negative; the round moves nothing under
D15 and leaves the frozen benchmark as an instrument. Proved in
`RequestProject/GLM/DocumentTree.lean`. [`MASTER_PLAN.md`](../MASTER_PLAN.md)
Phase 102 is the record.

**The round before those (Phase 101) took item 5 with the citation leak, at the
owner's request** ([`CITATION_SCOPE_STUDY.md`](../studies/CITATION_SCOPE_STUDY.md)).
`lean_address.citation_graph` now reads citations in Lean's scope: comments
and strings are stripped, a name bound in the declaration (a binder, a `fun`,
a `∀`, a pattern, an `intro`, a `variable`) is never a citation, and a short
name resolves through the file's namespaces and `open` lines in Lean's order,
not by being unique in the corpus. The elaborator itself was asked for the
true graph (`glm_lean/tools/CitationReference.lean`, 11,790 constants,
`reasoning/citation_reference.py`), and both readers were scored against it:
the repaired reader's edges are **99.1 %** confirmed (9,834 of 9,920) against
52.1 % for the legacy reader (7,795 of 14,949), it finds 90.9 % of the visible
real edges against 71.9 %, and edges into the ten one-letter declarations
that the elaborator does not confirm fall from 3,162 to 4. The type words now
count whole identifiers only, so no goal loses a structural coordinate when
its names go (41 of 836 before, 0 after). Every Lean-corpus retrieval figure
was re-taken under the repaired relevance, the old ones kept as the record:
the structural address gains most (hits at 1/3/5/10 on 209 declaration
queries 41/64/77/89 → 54/70/79/101), every qualitative verdict survives, and
the resampling's one effect still holds (95.3 % and 95.5 %, census 227 : 29);
the held-fixed price M5 falls from 12,541 to 1,881. The repaired graph carries
a new operation: **does A rest on B**, **what does A rest on**, **what rests
on A** (`reasoning/proof_dependency.py`, `runtime/dependency_frames.py`),
answered from the elaborator's graph with a witness path its column-3 script
re-checks, refusing an unknown or ambiguous name and a stale reference. D1
was not met as declared (7 of 12, 0 wrong, 5 refused as ambiguous); reading
an ambiguous name in the other name's scope met it, 12 of 12. 7 of 7 L marks
met. Proved in `RequestProject/GLM/CitationScope.lean`.
[`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 101 is the record.

**The round before those (Phase 100) took round 9 of the order, retrieval,
starting with candidate N1, the declared resampling**
([`CORPUS_RESAMPLE_STUDY.md`](../studies/CORPUS_RESAMPLE_STUDY.md)). The
native-parity and native-words studies had re-read their small leads at five
later closes and seen several flip by a query; each reading was one draw.
`reasoning/corpus_resample.py` ranks every one of the 4,572 declarations as a
declaration query and as a goal query under ten rankings, once, and reads off
that census every sub-corpus that drops one Lean file (171, each with its
query sample re-drawn) and every offset of the query stride (22 and 45), under
a rule declared before the code: an effect holds in at least 95 % of both
families. Of 18 reading-and-set pairs one is an effect: the two-book native
ranking at least the raw structural vector on the declarations (N6; 99.4 %
and 95.5 %, census 185 : 29 at 5). Everything else is a draw as stated — the
single-book marks N1 and N2, the tie-break marks W4 and W6, the three
post-hoc readings of the native-words study, and the shipped words mark W2,
which fails at the top rank while at least level at 3, 5 and 10 in at least
88.9 % of every resample. The declared control failed: `native2` and
`features2` share two keys, not three, and their hits differ in 11.7 % to
24.4 % of resamples (M4, 6 of 7 marks met). Pricing the held-fixed
addresses found a defect older than the round: the citation index reads a
bound variable `a`, `A`, `e`, … as a citation of the ten declarations with a
one-letter name, 3,231 of 15,012 citation edges, and the retrieval relevance
sets inherit it. No default changes. Proved in
`RequestProject/GLM/CorpusResample.lean`. [`MASTER_PLAN.md`](../MASTER_PLAN.md)
Phase 100 is the record.

**Before that (Phase 99) added a register that holds a Celsius
reading, at the owner's request** ([`CELSIUS_REGISTER_STUDY.md`](../studies/CELSIUS_REGISTER_STUDY.md))
— the item round 1 of the order (1a) and candidate 1 had waited on. The
register is the fourteen ITS-90 defining fixed points with an assigned
temperature (`data_objects/fixed_points.py`, the field surface's table
`fixed_point`), holding `temperature_C` only; the scale table's first offset
row, `fixed_point:temperature_C` (factor 1, offset 273.15), carries all 14
onto ITS-90's own kelvin column exactly. The ordering and extremum
operations compare it with the element register's kelvins (*order
temperature_C of water triple point and melting_point_K of mercury* is `gt`,
273.16 K against 234.32 K), and the stepwise planner reads a Celsius register
value as a level through `scale_into_si_affine` (*given the temperature of
the water triple point and energy = 2731600, what is the entropy* is 10000,
its column-3 script recomputing the offset from the row), refusing it
`LEVEL_AS_DIFFERENCE` where a law reads a difference. 10 of 10 ordering, 3 of
3 column and 9 of 9 planner cases as declared, 0 wrong; the machine answered
0 of the 9 planner questions before and 6 after; with the offset dropped 3
ordering verdicts flip and 6 of 6 planner answers are wrong; earlier corpora
unchanged; 8 of 8 marks met. Reported beside it: the element register's
aluminium melting point (933.437 K) is 0.036 K below ITS-90's 933.473 K, a
transposition left for the owner. The study's §6 is how the next register,
wheel or junction goes in. Proved in `RequestProject/GLM/CelsiusRegister.lean`.
Round 9 of the order, retrieval, is still where the next round starts.
[`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 99 is the record.

**The round before that (Phase 98) took boundary tracks S and T of Question
Set B, at the owner's request for more reasoning ability**
([`SYMBOLIC_PARAMETERS_STUDY.md`](../studies/SYMBOLIC_PARAMETERS_STUDY.md)) —
answers that are formulas in letters. `reasoning/symbolic.py` is an exact
algebra of rational functions over named parameters (radicals and `sin`,
`cos`, `tan`, `exp`, `ln` as named atoms, no float), and the new operation
`solve symbolically for T: EQ; EQ` eliminates the unknowns by declared
substitution (Cramer's rule with Bareiss determinants for square linear
systems of four or more), printing the formula with the nonzero conditions it
was derived under, and refusing by name what it cannot solve. Fourteen outside
frames use it: 13 of 13 class-S questions answered and verified, 0 wrong;
13 of 13 variants; 18 of 18 declared systems; 8 of 8 refusals; the class-T
crossover bracketed to 1/10000 (ω_co in [3.6731, 3.6732]); 27 of 27 earlier
framed answers and 14 of 14 Set B verdicts unchanged. S5 was 43 of 44 as first
measured (a ×2 control of a zero answer altered nothing) and 44 of 44 after
the control was repaired. A post-hoc battery of 90 random systems then found
a printer fault no mark had seen (53 of 87 verified) and a speed limit at four
unknowns; both repaired, 87 of 87 verified. Proved in
`RequestProject/GLM/SymbolicParameters.lean`, including `cramer_solves`.
Round 9 of the order, retrieval, is still where the next round starts.
[`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 98 is the record.

**The round before it (Phase 97) re-scored round 8's two misses, at the
owner's request** ([`UNPACKING_RESCORE_STUDY.md`](../studies/UNPACKING_RESCORE_STUDY.md))
— Phase 96's V8 was a gap in the dialect and its V4 a declaration on a false
analogy. The Python dialect now admits argument unpacking: `f(*xs)` at a
call, spliced in place through the same iteration a `for` loop uses, and
`def f(a, *rest)` at a definition, each a named step re-checked in column 3;
keywords, `**`, defaults and starred displays stay refused by name. The
program Phase 96 refused, `read_views(*store_views(golay_encode(1234)))`, is
answered equal to CPython as a fresh declared case, beside 21 further
programs and 10 refusals as declared (0 of the 33 before); none of 311
earlier declared programs moves but U1's own source, and the differential
battery is unchanged. The framed register gains `read_on_demand`, which
reads the third view only while two views leave the fork open: on Phase 96's
full common-mode probe it gives the three-view answer on 680,064 of 680,064
reads while reading 1,371,264 views instead of 2,040,192, and on weight-5
bursts, outside the fault model, it costs Phase 96's two-view 384 wrong
answers where three views refuse. Independent faults, declared correctly on
a fresh probe: two views' live count predicted on all 8,448 reads, three
views resolve 84,480 of 84,480, 0 wrong, and for every first error exactly
346 second errors leave two views open whatever the frame — so no frame
could have met V4. 12 of 12 marks met. Proved in
`RequestProject/GLM/OnDemandView.lean`: a third view cannot change a read
two views resolve, the 346 for every permutation, and the binding of
unpacked arguments. Round 9 of the order, retrieval, or the lattice items 3,
6, 7 and 10 beside round 8, is where the next round starts.
[`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 97 is the record.

**The round before it (Phase 96) took round 8 of the order, second
readings** ([`SECOND_VIEW_STUDY.md`](../studies/SECOND_VIEW_STUDY.md)) — J2 with
H's X1, then J1, then J3. `reasoning/second_view.py` is a framed register: a
codeword stored in views rotated by `0, 1, 3`, read by carrying the fork of
view 0 and pruning it by every further view, so the second reading is a path
the runtime takes on its own rather than a read the caller supplies; the
dialect reaches it as `store_views` and `read_views`. Under a common-mode
four-error burst, two views leave 174 of 10,626 bursts open (each with
exactly two live candidates, as predicted on all 680,064 reads) and three
views resolve 680,064 of 680,064 with 0 wrong; no single second frame can
resolve every burst. J1's composition, declared this time and run on a fresh
probe, answers 658,258 of 658,812 with 0 wrong and leaves open exactly the
predicted 2, 8, 32, 128 and 384. J3 is closed in the negative: the Leech
escalation on the views' own soft reading equals the intersection on 46,728
of 46,728 reads and resolves nothing beyond it, and that is a theorem.
On weight-5 bursts outside the fault model one view is wrong on every read
and three views refuse every read. 7 of 9 marks met: V4 (X1's probe through
two views, 4,160 of 4,224, 0 wrong — the register's second view reads X1's
second error rotated) and V8 (one declared program uses argument unpacking,
which the dialect refuses) are not. Proved in
`RequestProject/GLM/SecondView.lean`: the fork of a four-error read is the
truth and the truth plus each octad through the error, so views allow exactly
the octads through the union of their errors; no permutation suffices as one
second frame; the frames `(0, 1, 3)` separate every burst; the views' soft
channel ranks as the summed view distance, whose minimum is the
intersection. Its two misses were re-scored by the next round (Phase 97).
[`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 96 is the record.

**The round before that (Phase 95) took the second half of round 7 of the
order, M's imperative grammar** ([`IMPERATIVE_GRAMMAR_STUDY.md`](../studies/IMPERATIVE_GRAMMAR_STUDY.md))
— sentences for assignment, simultaneous assignment, `for` and `while`
loops, branches, conditional expressions, functions with recursion and
`match`. `reasoning/reverse_tct_imp.py` spells every construct head first
with every list counted (*the program of two steps: …; while b is nonzero,
do one step: set together two names a, b to b, the remainder of a and b. the
result is a.*), reads it back, runs it on an interpreter with CPython's
semantics for the fragment, counted steps and bounded depth (`STEP_LIMIT`,
`DEPTH_LIMIT`, `NO_RESULT`, `UNBOUND`, `ARITY`), and puts a trace of the
first 24 assignments, the final values and the result in column 1, which its
own column-3 script replays. `say:` asks it only after the third sort cannot
read the text. All 7 Phase 64 programs with state are said (0 before), 13 of
13 declared sentences word for word, 21 of 21 further programs equal CPython,
41 of 41 scripts verified and 41 mutants rejected, a battery of 1412
programs with 1412 distinct sentences, 0 of 41 answers moved by limits ×10,
and 0 wrong of 450 on a post-hoc battery of 600 programs (values past 4096
bits or characters are refused `SIZE_LIMIT`). 8 of 9 marks met:
I7 is not met as declared, because Phase 68's `unpack-self` refusal is now
the more specific `UNBOUND`. Proved in
`RequestProject/GLM/ImperativeGrammar.lean`: any grammar whose every
construct is a head with a counted list of parts is uniquely readable, a
step limit only withholds, and the Euclid loop, the telescoping accumulation
and the factorial recursion of the Phase 64 programs compute what they say.
Round 8 of the order, second readings, was taken by the next round
(Phase 96). [`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 95 is the record.

**The round before that (Phase 94) took the first half of round 7 of the
order, the third sort** ([`THIRD_SORT_STUDY.md`](../studies/THIRD_SORT_STUDY.md))
— I1 with M's strings, tuples and ranges. `reasoning/reverse_tct_seq.py` adds
a third sort beside numbers and Golay masks to the reverse grammar: strings
(every character spelled by name), tuples of any sort and ranges, each literal
spelled with its count first, with slices, items, concatenation, repetition,
`len`, `sum`, `ord`, `chr`, `min` and `max`, an exact evaluator and its own
column-3 script. `say:` asks the earlier grammar first, so no earlier answer
can move. The Python dialect now answers string methods over code points
(ASCII where Unicode tables would be needed) and admits lists and dicts as
immutable snapshots, refusing every in-place change `MUTABLE_CONTAINER`
(`reasoning/python_containers.py`). 28 of 28 say cases as declared (0 before);
the depth-two battery of 1116 terms reads back with 1116 distinct sentences;
21 of 21 dialect programs inside the grammar; 63 of 63 dialect cases equal
CPython in type and value (0 before), every script verified and every mutant
rejected; the differential battery 0 wrong of 2830 answered; 10 of 10 marks
met. Proved in `RequestProject/GLM/ThirdSort.lean`: count-first literals are
uniquely readable for any item spelling that is, ranges and slices read what
the evaluator says. M's imperative grammar, the second half of round 7, was
left to the next round, which took it (Phase 95). [`MASTER_PLAN.md`](../MASTER_PLAN.md)
Phase 94 is the record.

**The round before that (Phase 93) took round 6 of the order, the register
against the world** ([`REGISTER_WORLD_STUDY.md`](../studies/REGISTER_WORLD_STUDY.md))
— candidate C with H's first item. Two outside sources were fetched once and
frozen with their URL, date and digest (CIAAW 2024 standard atomic weights;
NIST ASD first ionization energies and ground configurations).
`runtime/register_world.py` reads every one of the register's 354 cells of
atomic weight, ionization energy and configuration against them at the
precision each side is held to, with six verdicts (agrees, agrees at the
register's stated precision, discrepant, and three silences), and never writes
to the register: atomic weight 73 / 11 / 0 discrepant / 34 world-silent,
ionization energy 10 / 68 / 24 discrepant / 6 register-silent / 10 both-silent,
configuration 107 / 1 discrepant (lawrencium) / 10 world-silent. The
consistency frame now answers any element and any of the three fields, and a
list frame returns a field's discrepancies from one question. 24 of 24 declared
questions came out as declared, with 0 wrong (2 before); 186 of 186 injected
errors are caught and 0 of 186 world values flagged. The completion gate now
reads the nested holdout as well: the covalent-radius rule is demoted and the
electron-affinity rule narrowed to the main group (nested skill 0.187, 31 of
31 folds), so the completed view is 1,344 rather than 1,442 — 98 estimates
withdrawn. The one declared move is Phase 63's iron question, now answered
*yes* at the register's stated precision. Proved in
`RequestProject/GLM/RegisterWorld.lean`. [`MASTER_PLAN.md`](../MASTER_PLAN.md)
Phase 93 is the record.

**The round before that (Phase 92) took round 5 of the order, discourse
state** ([`DISCOURSE_STATE_STUDY.md`](../studies/DISCOURSE_STATE_STUDY.md)) —
0b first, then D = 0a, then K3. The conversation layer of Phase 55 bound one
substituted name or refused, and its sharpest refusal was the tie.
`runtime/discourse.py` reads a fold's tie as a set the turn **produced**: *it*
or *them* names the set, the question is asked of every row by the asker that
would answer it written out, and the answer is the column of their answers —
refused `column-incomplete` when some row does not answer, as a hole refuses
a fold. The fourth shape is read: *the one before that* (the deciding turn
before the one *that* names), *them* and *both of them* (a set, the rows a
turn was about, or for *both* two single-row turns; `number-mismatch`
otherwise) and *why?* (the turn before, explained from the record). With the
router as the licence a follow-up whose rewritten question only the typed or
the stepwise planner answers is bound, and a text the machine answers as
written is answered as written (whole first). `GLM.py --converse` holds one
conversation over every surface. 29 of 29 declared follow-ups came out as
declared, with 0 wrong; Phase 55's layer gives 0 of the 20 new-behaviour
cases as declared, the session alone as the licence 0 of the 5 surface
answers, and `carry=False` returns every tie to the refusal. 15 of 15 of
Phase 55's follow-ups hold but the one declared move, 32 of 32 column cells
equal the answer asked alone, and no answer to any of 3056 earlier strings changes. Proved in
`RequestProject/GLM/DiscourseState.lean`. [`MASTER_PLAN.md`](../MASTER_PLAN.md)
Phase 92 is the record.

**The round before that (Phase 91) took round 4 of the order, the planner
widenings** ([`DECLARED_FRAMES_STUDY.md`](../studies/DECLARED_FRAMES_STUDY.md))
— H's E6 first, then O7's remainder and candidate 2's §6. Every widening of
the stepwise planner before it was a hand-written frame. Its fold frames are
now generated from one declaration (`runtime/frame_declarations.py`): 638 of
638 texts of rounds one to five and of the router's declared sets read alike
by the generated and the hand-written readers, and with the declaration
emptied no fold question is read. The widenings are entries in it: the
`k`-th largest and smallest value and the quartiles (bounded under holes by
round four's rule), superlatives and the top `k` (`TOP_K_TIE`; refused
`COLUMN_HOLE` under a hole), *the bounds on* a sum, a mean or a parity count
(a sum or a mean only through a declared, argued physical range —
electronegativity and ionization energy — else `RANGE_UNDECLARED`), the
present-rows parity count, *the metals* and *the rare earths*, the twelve
remaining exact SI prefixes, and *heavier*/*lighter* over the molecule table.
54 of 54 declared questions and 2 of 2 follow-ups came out as declared, with
0 wrong; round four's reader answers 0 of them, and the whole machine
answered 5 before and 41 after. Removing the round-five entries returns
every case to round four's verdict. 10 of 10 bounded answers hold over 200
completions with both ends attained, 41 of 41 scripts verify, every mutation
is rejected, and three earlier refusals move as declared. Proved in
`RequestProject/GLM/DeclaredFrames.lean`. [`MASTER_PLAN.md`](../MASTER_PLAN.md)
Phase 91 is the record.

**The round before that (Phase 90) took round 3 of the order, typed
operators** ([`TYPED_OPERATORS_STUDY.md`](../studies/TYPED_OPERATORS_STUDY.md))
— candidate F. Monomial wheels multiply magnitudes, so they could not tell
real, reactive and apparent power apart, nor the work (a dot product) from
the torque (a cross product). `runtime/typed_operators.py` computes complex
power `S = V * conj(I)` over the Smith chart's Gaussian rationals (and
through an impedance), the real power, reactive power, apparent power and
power factor with its sense as exact values and surds, the power triangle
from any two sides, and the dot against the cross product of rational
vectors. The watt, the var and the volt-ampere are kind-restricted names, so
*the reactive power in watts* is refused `KIND_MISMATCH`. A reactive power
whose sign the question leaves open is refused `PF_SENSE_UNDECLARED`. A
declared frame read ahead of the planner's *given* phrasing reaches all of it
through the router and `GLM.py -q`, gated by each reading's own column-3
script. 43 of 43 declared cases came out as declared, with 0 wrong. Through
the router 0 were answered before and 43 after. The naive monomial control
answers 19 and gets 15 of them wrong. 0 of 2971 earlier questions are read,
43 of 43 scripts verify, and 29 of 29 mutated claims are rejected. Proved in
`RequestProject/GLM/TypedOperators.lean`. [`MASTER_PLAN.md`](../MASTER_PLAN.md)
Phase 90 is the record.

**The round before that (Phase 89) took the owner's outside material and
gated decisions** ([`QUESTION_SET_B_STUDY.md`](../studies/QUESTION_SET_B_STUDY.md),
[`CONTRACT_MATRIX_STUDY.md`](../studies/CONTRACT_MATRIX_STUDY.md)) — out of the
order of §3.4, at the owner's request. Two outside question sets were
supplied: Set B (14 items, each with an expected status and refusal code) and
Outside O1 (112 questions written to find boundaries). Before this round the
router read none of the 126. Declared question frames
(`runtime/question_frames.py`), each answer re-derived by its own column-3
script before output, now read every Set B item — 14 of 14 by audit (protocol
+10: 11 right, two refusals under a code other than the file's, and one
answer where the file expects a refusal, which the audit finds right:
`3x + 5y = 1` is decided by `gcd(3, 5) = 1`) — and 27 of the
112 outside questions, answered or correctly refused exactly, with **0
confidently wrong**. The other 85 are located boundaries, classed in a
Capability Failure Matrix: explanations 32, derivations and proofs 18, meta
questions about the GLM's own engineering 18, symbolic parameters 13,
designs 3, one transcendental equation. K1 is taken: `GLM.py -q` goes through
the multi-surface router, and all 177 contract questions give byte-identical
output through the routed `-q` and the old `--plan` path. Candidate P's two
contract changes were run as a 4-way matrix over 525 exact cells in two
frames: the combined change (variant D, the upper-credible rule over the
session's reads) breaks no on-grid cell in either frame and keeps more right
answers than the upper rule alone (mean on-grid retention 0.6881 against
0.5562), so it is the production baseline; the control and the
session-marginal confidence alone each break 2 on-grid cells. On the 41
framed questions the four variants give identical verdicts. Proved in
`RequestProject/GLM/QuestionSetB.lean`. [`MASTER_PLAN.md`](../MASTER_PLAN.md)
Phase 89 is the record.

**The round before that (Phase 88) took round 2 of the order, the loop
through the planner** ([`PLANNER_LOOP_STUDY.md`](../studies/PLANNER_LOOP_STUDY.md))
— candidates K4, I2 and O3 = M3, then a re-reading of item 9. Every surface
answered its question alone; a question whose next step depends on the value
of the last answer had no reader. The Python dialect now has three builtins
that call the rest of the machine and return exact values — `derive(target,
(name, value), …)` (the stepwise planner's goal mode), `ask(question)` (one
stepwise question) and `solve(var, equation, …)` (the reverse surface's
linear solve) — and a declared frame (*what does `E` return*, *is `E` true*)
hands a question about a Python expression to the evaluator, so a loop is the
program's own control flow: `while derive("current", ("voltage", 12),
("resistance", r)) >= 1: r = r + 1` answers 13. The program's column-3 script
re-runs every sub-answer's own script in a fresh interpreter, checks the
value is bound to that record (a solve's root substituted back and shown
unique), and re-runs the program under CPython against the checked table.
44 of 44 declared cases as declared, 0 wrong; through the router 29 of 29
answer cases answered where 0 were before; with the bridge off 0 of 34; all 66
declared mutations rejected, each at the check written for it; the contract
census unmoved (0 of 530); earlier rounds unchanged. Item 9 re-read: the same
questions asked in English are answered by no surface — the first measured
instance of a tool a problem-driven front end reaches and the kind-driven
dispatcher does not; the reverse-call planner is still not promoted (D14).
Proved in `RequestProject/GLM/PlannerLoop.lean`. [`MASTER_PLAN.md`](../MASTER_PLAN.md)
Phase 88 is the record.

**Earlier, Phase 87 began by reading the open candidates
together** ([`ROADMAP_STUDY.md`](../studies/ROADMAP_STUDY.md)), at the owner's
request: the 49 open items of §3.4 reduce to seven tracks, several items are
one piece of work under two or three letters, and the rounds are now ordered
so that each reads what the one before built (the order is at the head of
§3.4). **It then took round 1 of that order, the measurand register**
([`MEASURAND_REGISTER_STUDY.md`](../studies/MEASURAND_REGISTER_STUDY.md)) —
candidate K2, the rest of O5 and the second half of candidate 1. The
stepwise planner now reads a register value through the measurand it holds:
a first ionization energy or an electron affinity is the least energy one
photon must carry to ionize the atom or detach the electron, so *given the
ionization energy of hydrogen and wave speed = 299792458, what is the
wavelength in nanometres* is answered (about 91.18 nm, the Lyman limit),
where before the value was a molar energy no wheel could read. A power
crosses a motor, generator, pump or turbine only through a stated efficiency
in (0, 1] — a law of its own across the junction table's non-identities —
and an efficiency outside that range, stated or derived, is refused
`EFFICIENCY_OUT_OF_RANGE`, one that names no declared conversion
`EFFICIENCY_UNDECLARED`. The elementary charge is an exact unit. 30 of 30
declared questions as declared, 0 wrong; through `GLM.py --ask` the machine
answered 2 of the 30 before and 18 after; the naive control (the conversion
read as an identity) answers 7 conversion cases, all wrongly; earlier rounds
unchanged. The scale table's offset row (candidate 1's first half) was then
still not shipped, for want of a register holding a Celsius reading; Phase 99
shipped it ([`CELSIUS_REGISTER_STUDY.md`](../studies/CELSIUS_REGISTER_STUDY.md)). Proved in
`RequestProject/GLM/MeasurandRegister.lean`. [`MASTER_PLAN.md`](../MASTER_PLAN.md)
Phase 87 is the record.

**The round before that (Phase 86) began with a quick tidy of candidate P
and then took candidate O5** ([`MEASURANDS_STUDY.md`](../studies/MEASURANDS_STUDY.md)):
measurands rather than units. The unit check compared dimensions only, so it
could not tell a torque from an energy or a frequency from an angular
velocity. The stepwise planner now holds the SI Brochure's restrictions on
special unit names (the hertz is not an angular velocity, the newton metre
not an energy) and refuses `KIND_MISMATCH`; it reads a temperature in degrees
Celsius or Fahrenheit as a level or a difference by the quantity it feeds,
refusing `LEVEL_AS_DIFFERENCE`, `DIFFERENCE_AS_LEVEL`, `KIND_CONFLATION` and
`BELOW_ABSOLUTE_ZERO`; and it supplies the exactly defined Planck constant and
speed of light when the givens alone derive nothing (*given frequency = 5
terahertz, what is the energy*). 31 of 31 declared questions as declared, 0
wrong; the dimension check alone answers all 5 declared kind mismatches with
a number. Five earlier declared verdicts of stepwise round two were wrong in
the physics — they fed a melting point, a temperature level, to `energy =
mass · specific heat · temperature`, which reads a difference — and are
amended to `LEVEL_AS_DIFFERENCE`; as a consequence mark H3 of the
held-precision study is no longer met (both its witnesses were that
conflation). The P tidy measured the soft floor's named repairs: a finer grid
or a higher guard repairs nothing; an upper-credible rate rule removes both
on-grid breaks; the breaks above the grid stay (runtime contract unchanged,
the owner's call). Proved in `RequestProject/GLM/MeasurandKinds.lean` and
`RequestProject/GLM/RateRepair.lean`. [`MASTER_PLAN.md`](../MASTER_PLAN.md)
Phase 86 is the record.

**The round before that (Phase 85) took candidate 2 and the last item of
O7** ([`HOLE_FOLDS_STUDY.md`](../studies/HOLE_FOLDS_STUDY.md)): folds with a
hole. The stepwise planner now reads the median, the largest and the smallest
value and the rank of a row (*the rank of gold by density among the
transition metals*) over every element or a declared class. Over a column with
missing readings, a median or a rank is answered as the exact interval every
completion of the holes lands in — *between 6 and 15*; the median valence
electrons of the transition metals is `2` with four readings missing, because
the interval closes — and a side the holes leave open is refused
`COLUMN_HOLE` by name (the largest density of the transition metals is open
above). The present-rows question asked as its own (*the average
electronegativity of the noble gases that have one*) is answered over the rows
that hold a reading, with the missing rows named in the answer; `NOT_A_MEMBER`
and `COLUMN_EMPTY` are the new refusals. 34 of 34 declared questions and 2 of
2 follow-ups as declared, 0 wrong; through `GLM.py --ask` the machine
answered 0 of the 34 before the round and 25 after; every bounded answer held
on each of 200 completions with both ends attained; 26 of 26 chain scripts
verified with every mutation rejected; round three unchanged (8 of 8 marks).
The rule is proved in `RequestProject/GLM/HoleBounds.lean`.
[`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 85 is the record.

**Before that, Phase 84 took item O7 of candidate O**
([`STEPWISE_THREE_STUDY.md`](../studies/STEPWISE_THREE_STUDY.md)): the stepwise
planner's widenings. It now reads comparatives through a declared register
field (*which is denser, gold or lead*, *is oxygen older than hydrogen*, *how
much heavier is gold than iron*), *how many more* electrons and valence
electrons, the tera- and pico- prefixes, and sums, means and parity counts over
every element or a declared `group_block` class (*the average atomic number of
the noble gases*, *how many of the lanthanides have an odd atomic number*). It
refuses by name where a comparative has no declared field
(`COMPARATIVE_UNDECLARED`), where the register records a value as missing
(`VALUE_MISSING`), where a column has a missing reading (`COLUMN_HOLE`, the
missing rows named), and where a class is not the register's
(`SET_UNDECLARED`). 47 of 47 declared questions and 2 of 2 follow-ups as
declared, 0 wrong; through `GLM.py --ask` the machine answered 6 of the 47
before the round and 32 after; 34 of 34 chain scripts verified with every
mutation rejected; rounds one and two unchanged (8 of 8 marks).
[`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 84 is the record.

**The round before it (Phases 81–83) finished candidate P.** Phase 81
([`AGREE_CHANNEL_STUDY.md`](../studies/AGREE_CHANNEL_STUDY.md)) gave the second
reading (`agree`) an exact channel measure — a census of every pair of reads,
164,051,805 resolved pairs in 28 rate-independent histograms — and put it in
the confidence-floor hunt: its working threshold is 9999/10000 up to 1/20 and
999/1000 at 1/10, where the decoder alone has none (8 of 8 marks). Phase 82
([`RATE_POSTERIOR_STUDY.md`](../studies/RATE_POSTERIOR_STUDY.md)) estimates the
rate from the reads: an exact posterior over a declared grid with a guard
point, a marginal confidence, `RATE_GRID_EXCEEDED`, and the dialect builtins
`decode_soft`, `decode_soft_floor`, `agree_soft`; the soft floor keeps its
promise on the prior average in every cell, but at a fixed rate it broke in 2
grid cells (1/10, floor 9999/10000) and at 1/5, above the grid (7 of 7 marks;
one declared expectation failed). Phase 83
([`LAW_TRIAGE_STUDY.md`](../studies/LAW_TRIAGE_STUDY.md)) triaged the 106
unresolved knowledge-base laws under a service rule: 0 absorbed, 3 already
served, 3 refuted, 100 retired with a reason (5 of 5 marks).
[`MASTER_PLAN.md`](../MASTER_PLAN.md) Phases 81–83 are the record.

**The round before that (Phase 80) moved the target**: under directive
**D15** it moved **refusal**. It took item P3 of candidate P
([`CONFIDENCE_FLOOR_STUDY.md`](../studies/CONFIDENCE_FLOOR_STUDY.md)): a
confidence floor as a refusal. At the owner's direction no threshold was
picked in advance: a declared grid of seven thresholds was hunted at five
bit-flip rates over an exact channel census — every probability a sum over
every received word — against a declared meaning of *working* (the floor keeps
its promise `P(wrong | answered) ≤ 1 − t` and keeps at least 9/10 of the right
answers, for the decoder and the context stage over each of K1's case sets).
The working threshold is 9999/10000 up to 1/50 and 999/1000 at 1/20, so the
owner's candidates 99 % and 99.9 % both work there; at 1/10 no threshold
works, because the complete decoder's confidence takes one value per coset
weight and any floor costs it more than a tenth of its right answers. There
the owner's fallback applies: the graded answer, the value with its exact
confidence beside it and nothing refused on confidence. The Python dialect
reaches both as `resolve_at` / `agree_at` (graded) and `resolve_floor` /
`agree_floor` (`BELOW_FLOOR`). Overstating the rate is proved safe
(`RequestProject/GLM/ConfidenceFloor.lean`); understating it breaks the
promise in 30 of 210 cells. 6 of 7 marks met; the miss is one program whose
declared refusal was wrong. [`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 80 is the
record.

**The round before that (Phase 79) moved the target**: under directive
**D15** it moved **refusal into derivation**. It took the third item of
candidate M: a complete integer decision behind the integer sort of Reverse
Three Column Thinking
([`INTEGER_DECISION_STUDY.md`](../studies/INTEGER_DECISION_STUDY.md)). Where round
three's elimination with rounding left a case open and refused
`INTEGER_UNDECIDED`, the Omega test now decides it — an integer point, or a
refutation tree of combinations, fresh-variable substitutions and splits that
the column-3 script checks by arithmetic alone. 22 of 22 declared questions
(Pugh's parallelogram among them) are answered as declared with 0 wrong, where
round three refused all 22; a declared battery of 600 questions agrees with
enumeration everywhere, 0 undecided against 31; nothing round three answered
moved. `INTEGER_UNDECIDED` is kept only for a declared limit of 5000 search
steps. The facts the search relies on are proved in
`RequestProject/GLM/IntegerDecision.lean`; `tools integer-decision` re-takes
the marks. The round began by completing Phase 78's release, which had been
written up but not signed. [`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 79 is the
record.

**The round before that (Phase 78) cut the cost of an iteration**, at the
owner's request. The Lean development is held once, in
`glm_lean/RequestProject/`, and `lake build` compiles it in place; the
repository-root copy, its mirror step and the instrument that compared the
two are gone. A unit's closure now follows what the unit reads: data files by
name, docstrings not dependencies, and the generated figure and block regions
of a document masked from every unit except the three that render or check
them — so a refresh that only moves counts (they all live in
`corpus/render.py`, recomputed into [`FIGURES.md`](../FIGURES.md))
no longer re-opens the units that quote them. The mean closure fell from 284
files to 183. A round closes with one command, `signoff --close`, which re-runs
only what is stale and then verifies the release
([`ITERATION_COST_STUDY.md`](../studies/ITERATION_COST_STUDY.md) §5g;
[`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 78 is the record).

**The round before it (Phase 77) moved the target**: under directive
**D15** it moved **refusal** and **derivation**. It took item P1 of candidate
P ([`DECODER_CONFIDENCE_STUDY.md`](../studies/DECODER_CONFIDENCE_STUDY.md)): the
confidence law Phase 75 absorbed is now attached to the decoder's own
readings. At a declared bit-flip rate, the complete decoder, the carried
fork's context stage and the second reading each give their answer with the
exact probability that it is the codeword sent, and refuse where they refused
before, by the same name; the Python dialect reaches them as
`decode_confidence(rate, s, *cases)` and `agree_confidence(rate, *reads)`,
each answer with a fresh-interpreter script that recomputes the posterior by a
brute-force sum. The measurement K1's *0 wrong* could not give: at a rate of
1/10, 294,976 of the 592,268 resolved forks fall below 99 %, the least at
0.909 with 32 cases, and every one of them is at least the floor proved in
`RequestProject/GLM/DecoderConfidence.lean`. 5 of 6 marks met; the sixth
missed on a wrongly declared clause about the witness (an exact tie, each
survivor just below one half, not exactly one half). Closing the round also
repaired a closure leak the two rounds before had opened (three provenance
labels in `salvage.py` had put the whole Lean development into every unit that
builds a session; [`ITERATION_COST_STUDY.md`](../studies/ITERATION_COST_STUDY.md)
§5). [`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 77 is the record.

**The two rounds before it (Phases 75 and 76) moved the target**: under
directive **D15** they moved **derivation** and **refusal**. *Phase 75* took
the owner's reading of candidate P — not another subsystem, but each retained
law tested, improved where it can be, and absorbed where it is of use
([`LAW_ABSORPTION_STUDY.md`](../studies/LAW_ABSORPTION_STUDY.md)). Eleven laws
are absorbed as computed self-knowledge of the substrate: the typed planner
now answers questions about the GLM's own code, decoder and lattice (the
codewords, the rate, the minimum distance, the covering radius, how many
errors are corrected, the outcome and exact probability of a decoding at an
error weight or a noise rate, the confidence of a decoding at a distance, the
kissing number, XOR closure, descent) by computing from the running
substrate, and each answer names the law it was absorbed from — 36 of 36
declared questions as declared, 0 wrong, against 0 answered before; two laws
were already GLM definitions, three were retested in dimensionless form and
refused, forty-nine are retired with a reason each. Absorbing the decoder laws
turned up a statement none of them made, now proved: an odd-weight error is
never refused, and one of weight 5 or more is always miscorrected
(`RequestProject/GLM/LawAbsorption.lean`). *Phase 76* took item O6
([`HELD_PRECISION_STUDY.md`](../studies/HELD_PRECISION_STUDY.md)): every answered
derivation that reads a register value now states the exact interval its
answer lies in, carried from the precision the register wrote the value at —
8 of 39 goal and narrative chains, 2 of them exact because the held value
cancels, where step-by-step interval arithmetic would have reported a spread;
the corner bound is proved in `RequestProject/GLM/HeldPrecision.lean`. No
existing verdict or value moved in either round.
[`MASTER_PLAN.md`](../MASTER_PLAN.md) Phases 75 and 76 are the record.

**The round before (Phase 74) moved the target**: under directive
**D15** it moved **refusal**. It took the owner's request to review two files
from an older study rather than a candidate of §3.4: a GLM-lens review of the
426 laws of the UBP knowledge base and the 65 laws it retained
(`source_material/UBP_LAW_GLM_REVIEW.md`,
`source_material/retained_laws_verified_65.csv`;
[`LAW_REGISTER_STUDY.md`](../studies/LAW_REGISTER_STUDY.md)). The sixteen exact
rows re-grade as 8 structural, 2 overclaimed, 3 definitional, 2 arithmetic and
1 near-miss; every structural row now cites a Lean theorem, most of which were
already in the tree. Three decoder laws are made exact — a complete decoder is
right exactly when the error has weight at most 3, a weight-4 error is always
refused, a weight-5 error is always wrong — and the outcome of every error
weight is tabulated, which refutes "hardened storage guarantees 100% integrity
at noise ≤ 3%" (0.005321 not right, 0.0005925 silently wrong) and prices the
GLM's own refusal at a six-way tie: 5 wrong answers withheld per right answer
given up. `LAW_LOGIC_GEO_001` holds for XOR only (AND and OR are not code
operations), the review's "descent in exactly d steps" is contradicted by the
exhaustive descent census, and the review's two "equal" NRCI means differ by
2.3 × 10⁻⁸ (the first seven weight moments of the code are binomial, the
eighth is not). Of the forty-nine numeric rows, 30 are not predictions of a
measured dimensionless number (unit-dependent, a bound or range, KB-internal,
a restatement, a duplicate); of the 21 external formulas a within-template
look-elsewhere test admits 2, both for m_μ/m_e, and both miss the measurement
by over a hundred standard deviations. `reasoning/law_register.py` is the
refusal faculty (`admit`, and `look_elsewhere` for any new claim), reachable
as `tools law-register` and the toolbox tool `law register`;
`RequestProject/GLM/LawRegister.lean` proves the decoder, closure and moment
facts. [`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 74 is the record.

**Two rounds before (Phase 73) moved the target**: under directive
**D15** it moved **derivation** and **refusal**. It took items two and four
of candidate O below — the frames the stepwise planner's leaves lacked, givens
written with units, and register values fed to the wheels
([`STEPWISE_TWO_STUDY.md`](../studies/STEPWISE_TWO_STUDY.md)). The stepwise
planner now reads *how many more protons does iron have than carbon* (20;
the reverse order is refused `DIFFERENCE_REVERSED`), *is the atomic number of
gold odd* (with the witness `79 = 2 x 39 + 1`) and *the average of the
melting points of iron, copper and gold* (45061/30). A given may be written
with a unit (*voltage = 12 kilovolts*, *36 kilometres per hour*) and a target
asked in one (*the current in milliamperes*): the unit is read through a
declared exact table whose dimensions are derived from the register's own
unit definitions (`runtime/quantity_units.py`), checked against the wheel
quantity's dimension and converted into SI, and a unit that is unknown, of
another dimension, inexact (π, the dalton) or offset (degrees Celsius) is
refused by name. A given may be a register value (*temperature = the melting
point of iron*), carried into SI through the Phase 55 scale table, so the
entropy of 2 kg at iron's melting point is derived with the stored heat
stitched in. Every new step has its own three columns and the chain's script
re-derives each conversion factor from the tables. On 53 declared questions,
2 narratives and 2 follow-ups: all as declared, 0 wrong, where round one's
reader answers 0 of the 53; a strip-the-units reading gets 6 of them wrong and
answers 7 of the unit refusals; 39 of 39 scripts verified and 22 of 22 unit
lies rejected; round one's corpus unchanged. It also fixed a round-one defect:
a decimal given failed its own script. `RequestProject/GLM/StepwiseFrames.lean`
proves the mean order-free and bounded, a monomial law unit-invariant exactly
when dimensionally homogeneous, an offset no multiplication, and a register
feed sound when the register is right. [`MASTER_PLAN.md`](../MASTER_PLAN.md)
Phase 73 is the record.

**An earlier round (Phase 71) moved the target**: under directive
**D15** it moved **address**. It took items N3 and N4 of candidate N
([`NATIVE_WORDS_STUDY.md`](../studies/NATIVE_WORDS_STUDY.md)): the word-overlap
ranking — the standard method Phase 70's ledger left far ahead of every
lexical address — computed on Golay words of the tokens. A token's parts
(split at `_`, `.`, `'` and digits) each give a **letter word**, the 24-bit
mask of their letter buckets, whose **Golay class** is every nearest codeword
of the complete decoder; a token's **Golay name** is its letter word and an
index that separates the vocabulary's tokens sharing it. The names carry the
token overlap exactly (W1; `jaccard_names`), so the native ranking
`words_native` — names, then part letter words, then classes, then Leech
distance — can move a candidate only inside a tie of the standard's overlap
(`take_map_overlap_eq`), and it moves them well: 190 against 182 hits at 5 on
211 declaration queries, 94 against 92 on 103 goal queries, and level on 60
document queries. The live document ranking (`corpus.address.retrieve`)
now reads it. Overlap on Golay letter words alone beats the lexical Leech
address of ledger rows 4 and 5 (187 against 147 on the declarations). The
Leech tie-break alone (`text_leech`) loses five queries at k = 1 and is not shipped
(W6). `RequestProject/GLM/NativeWords.lean` proves the name overlap exact, the
refinement confined to ties and a shared Golay class a near letter set.
[`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 71 is the record.

**An earlier round (Phase 70) moved the target**: under directive
**D15** it moved **address**. It took the owner's instruction — *where a
standard method is equal to or only slightly better than a Golay-Leech or 24D
native method, retain the native method and refine it to match or beat the
standard one* — rather than a candidate of §3.4
([`NATIVE_PARITY_STUDY.md`](../studies/NATIVE_PARITY_STUDY.md)). Every measured
native/standard pair was put in one ledger (8 rows: 3 native ahead, 1 parity,
1 standard narrowly ahead, 3 standard far ahead) and the middle classes were
taken. A Leech address at scale 9 is `9f + e` with every `|eᵢ| ≤ 4`, so it
reads back to its features exactly by rounding (3,976 of 3,976 stored and 102
of 102 goal addresses). Reading **two** native books (structural, then
identifier-letter), each in its two layers, gives 83 hits at 5 on 210
declaration queries against 80 for the raw features and 31 against 27 on 102
goal queries, identical query for query to the like-for-like standard
ranking; `retrieval.retrieve` defaults to it (`native2`). The controller's
read-back scorer solves 24 of 24 tasks, all minimal, with the exact scorer's
2,140 proposals, where the shipped Leech scorer solves 18. One book in two
layers is a draw that moves with the corpus, as `residue_congr` predicts (the
residue is a function of the features). On the documents the native rankings
stay within one relevant section of the raw vector, and the live word-overlap
ranking now breaks its ties by Leech distance at no cost. `RequestProject/GLM/NativeParity.lean`
proves the read-back exact, the residue a function of the features, and that
a refinement can reorder only inside ties. [`MASTER_PLAN.md`](../MASTER_PLAN.md)
Phase 70 is the record.

**An earlier round (Phase 69) moved the target**: under directive
**D15** it moved **derivation** and **refusal**. It took the integer-sort item
of candidate M ([`REVERSE_TCT_STUDY.md`](../studies/REVERSE_TCT_STUDY.md)
§10–§12). `entails over the integers:` and `bounds over the integers of x:`
decide the round-two statements with every variable an integer: a floor
quotient or remainder of a variable by a constant is split into one case per
residue with a fresh integer quotient, and each case is decided by elimination
with every row tightened over ℤ, a refutation certified by its derivation.
All 29 declared entailment cases and all 10 bounds cases are answered as
declared, 0 wrong; 34 of 34 column-3 scripts `VERIFIED True` and 34 of 34
mutated certificates rejected; 116 battery questions agree with brute force
over a box. Over ℚ the same 29 questions get 20 `NOT_POLYNOMIAL` refusals and
9 different answers (`x > 2` does not entail `x ≥ 3` there). Where
elimination with rounding stops the answer is the new refusal
`INTEGER_UNDECIDED` (Pugh's system). `RequestProject/GLM/ReverseTCTThree.lean`
proves the residue split exact and exhaustive, the tightenings exact and the
derivation sound. [`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 69 is the record.

**An earlier round (Phase 68) moved the target**: under directive
**D15** it moved **derivation** and **refusal**. It was candidate L, round
two of [`REVERSE_TCT_STUDY.md`](../studies/REVERSE_TCT_STUDY.md) (§7–§9), on the
owner's three notes. **The fragment is wider**: floor quotient, remainder,
`abs`, `min`, `max`, negative exponents, the bitwise operators and shifts, and
Golay masks as a second sort (count-first literals, the four set operators,
`len`, Hamming distance, `in`, subset) — 216,723 widened terms and 18,500 mask
terms round-trip with 0 collisions, and 36 of the 83 Phase 64 dialect programs
are now inside, each agreeing with the dialect's value (8 before).
**Disjunction** (`either …, or …`) makes a statement a conjunction of clauses,
so `negate` is closed under De Morgan: the `NOT_IN_FRAGMENT` refusal for a
compound negation is gone, and over a declared battery of 650 normal forms the
double negation is certified for all 650 and the negation is exact at every
grid point. `entails`, `bounds` and `equivalent` split disjunctions and
`abs`/`min`/`max` into cases. **The loop**: `relay:` hands what column 2
holds to the planner as a question in the planner's own language, reads the
answer back into column 2 and realises it as reverse-grammar sentences — 20
of 20 relay cases as declared, 32 of 32 handoffs agree or are consistent,
0 disagree, where the relayed sentences given verbatim are answered 0 of 15 and
the planner chained to itself recovers 11 of 13 values. 92 of 92 round-two
column-3 scripts `VERIFIED True`, 84 of 84 mutated certificates rejected; the
Phase 67 cases all hold (four superseded on purpose).
`RequestProject/GLM/ReverseTCTTwo.lean` proves the widened and clause grammars
uniquely readable, negation by distribution and its simplification exact, the
case splits exact, and Python's floor-remainder convention.
[`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 68 is the record.

**An earlier round (Phase 67) moved the target**: under directive
**D15** it moved **derivation** and **refusal**. It took the owner's
instruction — *a reverse three column thinking function where the script and
math generate the language column* — rather than a candidate of §3.4
([`REVERSE_TCT_STUDY.md`](../studies/REVERSE_TCT_STUDY.md)). Column 1 is now a
function of column 2: a declared prefix-first grammar realises an exact term
or statement over ℚ as English, a declared reader parses it back, and
`RequestProject/GLM/ReverseTCT.lean` proves the realisation uniquely readable.
All 176,617 terms of the declared battery round-trip with 0 collisions where
the natural infix realiser has 5,684. On that footing seven semantic
operations are taken on the mathematics and realised back into sentences —
`say`, `equivalent`, `paraphrase`, `negate`, `solve`, `entails`, `bounds` —
and every declared case is answered as declared, 0 wrong, where the default
path answered 0 of the 58 entailment, solve and bounds questions. Each
answer's column-3 script re-reads column 1 and re-checks the certificate in a
fresh interpreter: 94 of 94 `VERIFIED True`, 69 of 69 mutated certificates
rejected. `GLM.py --ask "entails: … ; …"` (a fifth surface on the router) and
`GLM.py --reverse TEXT` reach it. [`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 67
is the record.

**An earlier round (Phase 66) moved the target**: under directive
**D15** it moved **derivation** and **refusal**, and connected what was
already built. It took the owner's instruction — *find a way to increase GLM
capability and ensure the working parts are connected and available as
needed* — together with candidates E and 3 of §3.4
([`CONNECTED_MACHINE_STUDY.md`](../studies/CONNECTED_MACHINE_STUDY.md)). One
path, `GLM.py --ask TEXT`, now gives any text to the first surface that reads
it — the toolbox, the Python dialect, the engineering surface, then the
planner — and names the surface: 136 more of the declared questions are
answered correctly on it than on the planner alone, with no wrong answer
added, and none of the 177 contract cases changes surface. The eight tested
modules nothing reached are tools (`--ask "tool moonshine"`, …), and the
wiring audit reads 0 of 96 reasoning modules unreached. The engineering
surface derives *across wheels*: naive composition of the ten wheels licenses
161 formulas no wheel does and 158 of them are wrong
(`energy = 2 * mass * speed_of_light^2` among them); with a declared junction
table it answers the 3 laws and refuses the 158, 0 wrong.
`RequestProject/GLM/ConnectedMachine.lean` proves the router's rule and the
soundness of splitting. [`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 66 is the
record.

**An earlier round (Phase 65) moved the target**: under directive
**D15** it moved **refusal** and **address**, and moved **derivation**
conditionally. It took the owner's instruction on the `AMBIGUOUS` Golay reads
rather than a candidate of §3.4: the six equidistant candidates of a
deep-hole read are now **carried** as a fork with a ledger until a later
decision resolves them, and the read is escalated to the Leech lattice
([`CARRIED_FORK_STUDY.md`](../studies/CARRIED_FORK_STUDY.md)). Four of the six
marks declared before the module existed were met and two were not. Every
certified stage — the declared cases (under a named closed-world assumption),
a second reading, an unsure set — gave 0 wrong: 592,268 of the 658,812
declared-case reads that `classify` refuses are answered, the declared 90 %
mark missed at 32 cases (85.8 %); X1's second reading is reproduced (4,224 of
4,224) and reachable; the unsure set answers all 3,840 of its reads. Escalated
without new information, every one of the 1,771 ties lifts to a certified
**A₁²⁴** deep hole of the Leech lattice (48 vertices, 8 over each candidate);
the soft-reading estimate is right on 512 of 768 and missed its mark. The
Python dialect reaches it through `nearest`, `resolve`, `agree` and
`resolve_unsure`; `tools carried-fork` re-takes it.
[`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 65 is the record.

**An earlier round (Phase 64) moved the target**: under directive
**D15** it moved **derivation**, **refusal** and **address**. The GLM now
speaks a declared dialect of Python
([`PYTHON_SPEECH_STUDY.md`](../studies/PYTHON_SPEECH_STUDY.md)): it evaluates a
program exactly on the substrate — bitwise operations through the eight
Toffoli/Fredkin sub-registers, shifts as dyadic moves, slices as index maps
onto MOG cells, sets as Golay masks, `match` by coset decoding — and returns a
Three Column payload whose third column re-derives every step in a fresh
`python3 -I`. All six pass marks declared before the module existed were met:
83 of 83 declared programs equal CPython in type and value with every script
`VERIFIED True` and every mutated claim caught, 26 of 26 refusals named, and
0 wrong over a 7128-expression differential battery; the existing question
surface solves 0 of the 83. `GLM.py --python SOURCE` reaches it.
[`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 64 is the record.

**An earlier round (Phase 63) moved the target**: under directive
**D15** it moved **derivation** and **address**, and sharpened **refusal**. It
was round two of
[`SUBSTRATE_NATIVE_COGNITION_STUDY.md`](../studies/SUBSTRATE_NATIVE_COGNITION_STUDY.md):
three near misses of the first round were looked at again and refined into
planner frames — interval consistency, rational recognition with a uniqueness
certificate, and dimensional derivation — which answer 26 of 33 declared
questions and refuse the other 7 as declared, with 0 wrong where the grammar
answers none. The typed planner is now the default path of `GLM.py`
(`--grammar` asks the grammar alone); the 177 contract cases give the same
outcomes either way. A language model as parser (G1) is declined for good.
[`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 63 is the record.

**An earlier round (Phase 60) was a documentation round** taken at the
owner's request: it moved none of **derivation**, **address** or **refusal**
(D15). [`GLM_ACADEMIC_PAPER.md`](../studies/GLM_ACADEMIC_PAPER.md) now covers
the system as a whole (the machine, addressing, measured capability, negative
results, method, and a ledger of the supplied material taken and left), and
[`GLM_Complete_Number_Theory_Evidence.md`](../studies/GLM_Complete_Number_Theory_Evidence.md)
gained §15–§21. It also resynced the overlay Lean mirror, which Phase 59 had
left one file short. [`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 60 is the
record.

**The round before it (Phase 59) moved the target**: under directive
**D15** it moved **derivation** and **refusal**, with five **address**
answers and no **table**. It took the supplied formula-wheel session record
(`source_material/formula_wheel/`) rather than a candidate of §3.4, because
the request was to have the GLM reason in electrical and mechanical terms and
the record's own first priority is to run its studies against the GLM's
substrate. `glm_universal.engineering` reads formula wheels as rational spans
with certificates, the Smith chart over Gaussian rationals, the force-voltage
and force-current analogies as maps on laws, and the delta-sigma loop by
theorem, and `engineering/speak.py` lets the machine be asked in words
(`GLM.py --eng`, `GeometricSession.ask_engineering`). On 63 questions
committed before any of that code, both existing paths refused all 53
answerable ones; through the surface it answers **53** correctly and refuses
**10** correctly with **0** wrong, and it reads none of the 374 questions the
machine already answers. The register agrees with the corrected formula study
on all 41 cases at SI7 and at EXT10, the force-voltage analogy preserves 9 of
9 laws each way, and `RequestProject/GLM/EngineeringWheels.lean` proves the
licensing rules (span membership, translation, the Smith disc, the periods of
the bitstream). [`studies/ENGINEERING_LANGUAGE_STUDY.md`](../studies/ENGINEERING_LANGUAGE_STUDY.md)
is the study and [`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 59 the record.

**The round before that (Phase 58) moved the target**: under directive
**D15** it moved **derivation** and **refusal**, and most of what it gained
is **table** — coverage of operations the machine already had. It took the
supplied roadmap (`source_material/GLM_IMPROVEMENT_ROADMAP.md`) rather than a
candidate of §3.4, because the measurement the roadmap quotes still held: the
frozen language probe, asked through `GeometricSession.ask`, scored two
correct of twenty although the answers to most of it were held behind the
formal grammar. `glm_universal.runtime.semantic_plan` reads a question into
typed plans over the operations the session already has — each slot grounded
against what the registers hold, each plan run, and an answer given only when
every licensed plan agrees — and adds two things that compute rather than
route: exact integer arithmetic and conversion between units whose relation
is a definition. Through it the frozen probe scores
**19** correct and
**0** wrong, passing the mark
declared before the probe was first run; on the
**110** held-out questions
committed before the planner existed it answers
**86** correctly and refuses
**22** correctly with
**1** wrong — a register holding
iron's atomic weight to four figures where the world uses five, recorded as a
data-truth finding rather than edited away. Two readings that disagree are
refused, not chosen between: *does energy have the same dimensions as
torque?* is yes in the SI projection and no in the extended vector, and the
answer names both. It is opt-in (`GLM.py --plan`,
`GeometricSession.ask_planned`), so the 177-case contract set is untouched.
`RequestProject/GLM/SemanticPlan.lean` proves the licensing rule order-free,
sound and conservative over the grammar, and refutes the first-licensed rule.
[`studies/SEMANTIC_PLAN_STUDY.md`](../studies/SEMANTIC_PLAN_STUDY.md) is the study
and [`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 58 the record.

The round before these (Phase 55) **moved the
target**: under directive **D15** it moved **refusal**, and widened
**derivation** to a fold over rows of two tables at once. It took candidate 1
of §3.4 — the scales neither operation could bridge — and wrote them down.
`glm_universal.reasoning.scale_conversion` declares nine scales over four
quantities (mass in `u`, molar energy in `kJ·mol⁻¹`, temperature in `K`,
length in `pm`), each row an exact positive-affine map into its quantity's
canonical unit with the source its numbers came from, so that a conversion is
a fact someone wrote down rather than a guess from a name. Seven of twelve
questions declared before the run are answered and five refused, every one of
the twelve as declared; the ordering and extremum operations come out on their
own declared sets exactly as they did — 7 of 7 and 8 of 8 — and `largest mass`
now gathers the element rows and the molecule rows into one unit and folds
them. What the table does not reach it still refuses: it relates 6 of the
7,750 pairs of the 125 numeric scales the field surface holds, and every other
pair is `different-scale` with the table's own reason.
`RequestProject/GLM/ScaleConversion.lean` is the proved half —
`cmpQ_apply` and `order_conversion_invariant` that a positive conversion
leaves the verdict alone, `orderWith_conservative` that the wider operation
never changes an answer the bare one gave, `orderWith_eq_none_iff` that its
silence is still exactly stated, `the_table_carries_the_claim` that the
declaration and not the code is what licenses a bridge, and
`negative_factor_flips_the_verdict` and `raw_gather_names_the_wrong_row` for
the two things it must not do.
[`studies/SCALE_CONVERSION_STUDY.md`](../studies/SCALE_CONVERSION_STUDY.md) is
the study and [`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 55 the record.

The round before it **moved the target** too: under directive **D15** it moved
**addressing** and **refusal**. It
did not take a candidate from §3.4; it took the material supplied with it —
`source_material/conversation_experiment/`, eight scripts and a research
document on a conversational GLM, every one of which runs unmodified against
the package — tested its claims, and built the one thing in it this system
could not do at all: a **turn that refers back to an earlier turn**. *describe
it*, *and the smallest?* and *and oxygen?* are now bound to what the
conversation has already said, by the only test that makes the reference a
reading of the registers rather than a guess about word order — a candidate is
**licensed** when the query it produces actually solves. Eight of fifteen
declared follow-ups are bound and seven refused, every one of the fifteen as
declared, where the same fifteen texts asked of a session with no memory are
answered **none** of the time; and the rule a reader would assume — bind to
the most recent mention — differs on three of the ten pronoun follow-ups,
losing one answer the registers hold and giving two confident answers to
questions that have no single answer.
`GLM.Conversation.most_recent_mention_is_not_the_antecedent` is that control
refuted as a theorem rather than as a measurement. Two claims of the supplied
material did **not** survive being re-run, and are recorded as refuted: the
higher-order analogy whose second constraint has no exact solution and
contributes nothing, and the periodic-table reading that is a renaming of two
carrier coordinates.
[`studies/CONVERSATION_STUDY.md`](../studies/CONVERSATION_STUDY.md) is the study,
`RequestProject/GLM/Conversation.lean` the proved half, and
[`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 54 the record.

The round before that **moved the target** too: under directive **D15** it
moved **derivation** and **refusal**. It
took candidate 1 of §3.4 — the column rather than the pair — and built the
operation that closes it: `extremum`, one coordinate read off *every* row of
one declared table and folded to its end, or refused. Four of eight declared
columns are folded and four refused, every one of the eight as declared before
the run, and the two refusals it was built for are the result rather than the
cost: a column with a hole in it has no extremum, because
`GLM.ColumnExtremum.extremum_over_present_is_not_the_extremum` exhibits a
column whose extremum over the rows that are filled in is a different value at
a different row, and a column gathered from two scales is not one column,
because `extremum_not_invariant_under_one_row_rescaling` exhibits a one-row
rescaling that moves the winner where `extremum_scale_invariant` shows that
rescaling the shared scale cannot. Where the end is a tie every row attaining
it is named — fourteen of them, on the lexicon register's `abstract_concrete`.
What it does **not** move is addressing: the table and the coordinate are the
names the question already gives.
[`studies/COLUMN_EXTREMUM_STUDY.md`](../studies/COLUMN_EXTREMUM_STUDY.md) is the
study, `RequestProject/GLM/ColumnExtremum.lean` the proved half, and
[`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 53 the record.

The round before that was **maintenance**, and said so: under directive **D15**
it moved none of derivation, addressing or refusal. It finished the round
before it — which
had stopped with its counts re-taken in the working note but not written into
the documents, and with no release run — by re-taking eight counts the tree
quotes about itself, four of them measurements rather than tallies: the formal
development at 3,422 declarations, the relay's strict gain now holding across
the whole declared gate band with 19 queries carried and none lost, the
planner consulted on ten refusals rather than four, and the end-to-end set at
164 cases with 22 expected refusals. One unit was brittle rather than wrong —
it asserted that a two-digit sentinel never reaches the recorded totals, and
the suite reached 99 counted test files — and was fixed at the root. The
release then earned: **every test file of that suite and all 7 instruments**
signed with the exhaustive cases on. [`MASTER_PLAN.md`](../MASTER_PLAN.md)
Phase 52 is the record.

The round before that **moved the target** too: under directive **D15** it
moved **derivation** and **refusal**. It took candidate 1 of §3.4 as it then
stood — the comparison a field surface
could not make — and built the operation that closes it: `ordering`, one
coordinate read off two rows and ordered exactly in rationals, or refused.
Four of seven declared comparisons are answered and three refused, every one
of the seven as declared before the run, and the refusals are the result
rather than the cost — two readings are comparable only on one scale, and
`GLM.CoordinateOrder.naive_order_is_not_scale_free` exhibits a positive
rescaling that flips the comparison of the bare numbers where
`order_scale_invariant` shows that no rescaling of a shared scale can. It
closes the last of the probe's ten held-and-unreachable questions: *is energy
more abstract than water?* is answered *energy*, by an exact `3/4`, on the
lexicon register's own scale and its own declared poles. What it does **not**
move is addressing, and the derivation it moves is one exact subtraction over
two addressed readings, which is the honest size of it.
[`studies/ORDERING_STUDY.md`](../studies/ORDERING_STUDY.md) is the study,
`RequestProject/GLM/CoordinateOrder.lean` the twelve theorems, and
[`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 51 the record.

The round before it was **maintenance**, and said so: under directive **D15**
it moved none of derivation, addressing or refusal. It asked the release
question the round before it had left unasked, and repaired the six units that
failed it — the UBP source audit, which had no way to say that a float inside
the core was a *declared* site and now reads the declared list off the D11
inventory rather than loosening the check; the reasoning kernel's import
audit, told about the one integer-nanosecond timing; two counts of the tree
that had drifted; and two measurements that had moved with the corpus and were
re-taken. [`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 50 is the record.

The round before *that* took the four supplied *History Recorded in the Now*
studies seriously enough to decide them. Under directive **D15** it moved
**refusal**, on a declared task set: the supplied recipe answers all nine
history questions and is wrong on the four whose answer the receipt does not
determine, and the module answers five and refuses four, each refusal carrying
the pair of histories that share the receipt.
[`studies/NOW_RECEIPT_STUDY.md`](../studies/NOW_RECEIPT_STUDY.md) is the study and
`RequestProject/GLM/NowReceipt.lean` the nine theorems; Phases 21–51 of
[`MASTER_PLAN.md`](../MASTER_PLAN.md) are the rest of the record.

Last reconciled against a full re-run on 2026-09-21.

Every count below is produced by `glm_universal/figures.py` and written
to [`FIGURES.md`](../FIGURES.md);
`glm_universal/tests/test_figures.py` fails if this document and the
code disagree. If a number here looks wrong, regenerate rather than edit:

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.figures --write
```


---

## 2. Named as untouched — all closed, and what each closure left

Every item that used to stand on this list is closed; each is recorded in
[`MASTER_PLAN.md`](../MASTER_PLAN.md) with the study that closed it. What the
closures left behind is §3.4.

* **The infinite-dimensional half of the VOA bridge.** `VOA.lean` builds the
  state–field map at the Griess layer (the partial 2A axial algebra on axes) and shows where a finite model stops
  (`borcherds_commutator_fails`); `Heisenberg.lean` builds the Fock space of
  one free boson and proves `no_finite_dimensional_model`.
* **`heat : temperature :: force : ?`** — closed by the energy-conjugate
  register, with the four criteria a transportable relation must meet
  ([`CONJUGATE_STUDY.md`](../studies/CONJUGATE_STUDY.md)).
* **The `O(1)` LLVQ table** — built and on the hot path, with the claim
  narrowed to *constant-bounded* and measured rather than asserted.
* **The Niemeier deep-hole census** — the trajectory distribution classifies
  (**40 of 44** at the escalated reading, **10 of 10** labels kept under a
  change of seed); what it does not do is certify, which is §3.4 item 1a
  ([`DEEP_HOLE_STUDY.md`](../studies/DEEP_HOLE_STUDY.md),
  [`DEEP_HOLE_ESCALATION_STUDY.md`](../studies/DEEP_HOLE_ESCALATION_STUDY.md)).
* **Open vocabulary** — closed as a mechanism: a name is admissible exactly
  when a stated route gives it coordinates computed from a register the machine
  already checks, and *justice* is refused by a condition it names rather than
  by kind ([`ADMISSION_STUDY.md`](../studies/ADMISSION_STUDY.md)).
* **Words as projections** — closed for all twelve lexicon adjectives and for
  the comparative; what is open is data, which
  `replacement_witness()` keeps measured
  ([`RELATIVE_MEASURE_STUDY.md`](../studies/RELATIVE_MEASURE_STUDY.md)).
* **The geometric items** — sigma–delta on the Leech shells, the 32- and
  48-dimensional lattices, the harmonic register and the economic register are
  all built, the last two with the honest verdict `not reproduced` against
  their controls ([`HIGHER_LATTICE_STUDY.md`](../studies/HIGHER_LATTICE_STUDY.md),
  [`HARMONY_STUDY.md`](../studies/HARMONY_STUDY.md),
  [`ECONOMICS_STUDY.md`](../studies/ECONOMICS_STUDY.md)).


---

## 3. Named for the next round — the candidate list as it stood at Phase 110

Every open item this list still held is carried, one line each, in the To-Do
list of [`STATUS.md`](../STATUS.md); the letters and numbers below are the
names those lines cite.

**Read this section first on the next development push.** The head of
[`MASTER_PLAN.md`](../MASTER_PLAN.md) names where the next round
starts and points back here.

**The order of work — merged and sequenced in Phase 87**
([`ROADMAP_STUDY.md`](../studies/ROADMAP_STUDY.md)). The candidates below are
kept under the letters they were named with, but they are no longer taken in
that order. The 49 open items reduce to seven tracks; several items are one
piece of work under two or three letters, and the rounds are ordered so that
each reads what the one before built:

1. **The measurand register** — K2, O5b, O5c, O5d, 1a and 1b, one round:
   **taken by Phase 87** ([`MEASURAND_REGISTER_STUDY.md`](../studies/MEASURAND_REGISTER_STUDY.md));
   all but 1a met; 1a, which waited on a register holding a Celsius reading,
   **taken by Phase 99** ([`CELSIUS_REGISTER_STUDY.md`](../studies/CELSIUS_REGISTER_STUDY.md)).
2. **The loop through the planner** — K4 (`derive` as a value), I2 (a Python
   expression as a planner question), O3 = M3 (the planner's answer chooses
   the next reverse operation); then re-read item 9, the utility gate:
   **taken by Phase 88** ([`PLANNER_LOOP_STUDY.md`](../studies/PLANNER_LOOP_STUDY.md));
   every mark met. Item 9 re-read: the loop's questions asked in English are
   answered by no surface, so the problem-driven reach item 9 asked about
   now exists and is measured; promoting the supplied planner is still not
   earned.
3. **Typed operators** — F, on the measurand register: **taken by Phase 90**
   ([`TYPED_OPERATORS_STUDY.md`](../studies/TYPED_OPERATORS_STUDY.md)); every
   mark met.
4. **Planner widenings** — H's E6 (frames from a declaration) first, then
   O7's remainder and candidate 2's §6: **taken by Phase 91**
   ([`DECLARED_FRAMES_STUDY.md`](../studies/DECLARED_FRAMES_STUDY.md)); every
   mark met. What it leaves is that study's §6 (cross-table comparison,
   differences between molecules, a nuclide register, one-sided ranges, the
   top `k` under a hole).
5. **Discourse state** — 0b (a tie carried as a column, now that set folds
   exist), then D = 0a, then K3: **taken by Phase 92**
   ([`DISCOURSE_STATE_STUDY.md`](../studies/DISCOURSE_STATE_STUDY.md)); every
   mark met. What it leaves is that study's §7 (the column handed to the
   planner's folds, a present-rows column, further phrasings, the plan store
   for the new shapes, an outside multi-turn set).
6. **The register against the world** — C with H's first item: **taken by
   Phase 93** ([`REGISTER_WORLD_STUDY.md`](../studies/REGISTER_WORLD_STUDY.md));
   every mark met. What it leaves is that study's §6 (sources for the other
   fields — electron affinity, melting and boiling points; isotope masses for
   the 34 world-silent weights; a held-out check of the narrowing; the owner's
   decision on writing any discrepancy back).
7. **The third sort** — I1 with M's strings, tuples and ranges; then M's
   imperative grammar. The first half is **taken by Phase 94**
   ([`THIRD_SORT_STUDY.md`](../studies/THIRD_SORT_STUDY.md)); every mark met.
   What it leaves is that study's §6 (Unicode case and whitespace tables as a
   register, booleans as a term of the grammar, sets and comprehensions).
   M's imperative grammar is **taken by Phase 95**
   ([`IMPERATIVE_GRAMMAR_STUDY.md`](../studies/IMPERATIVE_GRAMMAR_STUDY.md));
   8 of 9 marks met (I7 not met: one earlier refusal made more specific).
   What it leaves is that study's §6 (`break`, closures, the truth of
   sequences, a trace inside calls, a program with state handed to the
   planner as a sentence).
8. **Second readings** — J2 with H's X1, then J1, then J3 (now well-posed
   on Phase 82's rate posterior); the lattice items 3, 6, 7 and 10 beside it.
   J2, X1, J1 and J3 are **taken by Phase 96**
   ([`SECOND_VIEW_STUDY.md`](../studies/SECOND_VIEW_STUDY.md)); 7 of 9 marks met
   (V4 and V8 not met). J3 is closed in the negative by a theorem: a soft
   channel built from the machine's own views adds nothing to the second
   reading. What it leaves is that study's §6 (framing an existing register
   by default, a soft channel with reliabilities from outside the views), and
   the lattice items 3, 6, 7 and 10, not taken (item 10 since taken by Phase 110). Its two misses were
   **re-scored by Phase 97** at the owner's request
   ([`UNPACKING_RESCORE_STUDY.md`](../studies/UNPACKING_RESCORE_STUDY.md)):
   argument unpacking added to the dialect and the refused program answered;
   independent faults re-declared (three views, 0 wrong; no frame helps two);
   the third view read on demand; 12 of 12 marks met. What it leaves is that
   study's §6 (keywords and defaults, starred displays, unpacking in the
   imperative grammar).
9. **Retrieval** — N1 first, then item 5, then N2, N5 and I3. N1 is **taken
   by Phase 100** ([`CORPUS_RESAMPLE_STUDY.md`](../studies/CORPUS_RESAMPLE_STUDY.md));
   6 of 7 marks met (M4 not met: the control `native2` = `features2` is a
   near identity, not an identity). One lead is an effect (N6 on the
   declarations); the rest are draws. It found the **citation leak** — the
   citation index reads a one-letter bound variable as a citation, 3,231 of
   15,012 edges, and the retrieval relevance sets inherit it — which joins
   item 5 as the same kind of leak. **Item 5 with the citation leak is taken
   by Phase 101** ([`CITATION_SCOPE_STUDY.md`](../studies/CITATION_SCOPE_STUDY.md)):
   citations read in Lean's scope, 99.1 % confirmed by the elaborator; type
   words counted as whole identifiers; every Lean-corpus retrieval figure
   re-taken; and the dependency operation (*does A rest on B*) built on the
   repaired graph. **N2 is taken by Phase 102**
   ([`DOCUMENT_TREE_STUDY.md`](../studies/DOCUMENT_TREE_STUDY.md)) and closed in
   the negative: the literal tree book reads the relevance relation (a leak),
   and the leak-free place word changes no hit, because the first two books
   leave a tie at the top-five boundary on only 30 of 1,506 queries. **I3 is
   taken by Phase 105** ([`AST_INDEX_STUDY.md`](../studies/AST_INDEX_STUDY.md)):
   the statement-level expressions of the live code and the archive in a
   frozen index, a bucket key no renaming or commutation moves, an exact
   matcher, and the operation *where is `EXPR` computed?*; 5 of 7 marks met
   (A2 by a declaration error, A4 as predicted). **Round 9 is closed at the
   owner's direction (Phase 106)**: N5, the AST index study's §8, the
   citation-scope study's §6 and the document-tree study's §6 are **parked**
   — kept as the record, not carried as the next round — because the owner
   judged the retrieval line not to be producing strong results. Every
   operation round 9 built stays in the system.

**Taken out of order by Phase 103, at the owner's request for broader
reasoning** ([`NONLINEAR_ELIMINATION_STUDY.md`](../studies/NONLINEAR_ELIMINATION_STUDY.md)):
the first item of the symbolic-parameters study's §6, nonlinear systems by
resultants. 4 of 7 marks met. Its §6 was **taken by Phase 104**
([`CUBIC_RADICAL_STUDY.md`](../studies/CUBIC_RADICAL_STUDY.md)): cubics,
nested radicals, positive-root readings through the branch layer (both
tracks kept, the branch set the default) and real-root conditions; 8 of 9
marks met. What it leaves is that study's §8 (a cubic in letters with three
real roots, numeric degree above 6, the quintic in letters, Cardano's long
printed form). Its first item was **taken by Phase 108**
([`CUBIC_TRIG_STUDY.md`](../studies/CUBIC_TRIG_STUDY.md)): the homogeneous
route and Viète's trigonometric form; 9 of 9 marks met. What it leaves is
that study's §5 (the regime split `D < 0` beside Cardano when the sign of
the discriminant is not decided, a syntactic test of a negative
discriminant, Viète roots in the motion check, the unequal triple
pendulum). The regime split, Viète roots in the motion check and the
unequal triple pendulum were **taken by the sharpening pass after Phase
108** (cases, the stepwise route, `reasoning/routes.py`); what is left of
it is a discriminant sign decided by factorisation and the stepwise route
for four or more degrees of freedom.

**Taken out of order by Phase 89, at the owner's request**
([`QUESTION_SET_B_STUDY.md`](../studies/QUESTION_SET_B_STUDY.md),
[`CONTRACT_MATRIX_STUDY.md`](../studies/CONTRACT_MATRIX_STUDY.md)): the gated
items the owner released — K1 (`-q` routed through the multi-surface router,
Option A; the contract set gives 177 of 177 identical verdicts through the
command line), P's two contract changes (run as a 4-way matrix; the combined
change, variant D, is the production baseline and the other two are set
aside), and B = O1 (two outside question sets supplied: Set B 14 of 14 by
audit, Outside O1 27 of 112 framed and correct with 0 confidently wrong and
85 located boundaries). The boundaries it located are new tracks, ordered in
that study's §8: symbolic parameters (13), derivations and proofs (18), meta
questions about the GLM's own engineering (18), explanations (32), designs
and one transcendental equation, and the planner's two vacuous denotation
answers. Tracks S (symbolic parameters) and T (the transcendental equation)
were **taken by Phase 98** at the owner's request
([`SYMBOLIC_PARAMETERS_STUDY.md`](../studies/SYMBOLIC_PARAMETERS_STUDY.md));
8 of 8 marks met, S5 after a control repair. What it leaves is that study's
§6 (nonlinear systems by resultants, the P, M and E tracks, the two vacuous
answers). Track P (derivations and proofs) was **taken by Phase 106** at the owner's
direction ([`DERIVATION_STUDY.md`](../studies/DERIVATION_STUDY.md)); 9 of 9
marks met. The rest of track P was **taken by Phase 107** at the owner's
direction ([`DERIVATION_TWO_STUDY.md`](../studies/DERIVATION_TWO_STUDY.md)); 11
of 11 marks met, outside questions 19, 28, 49, 52, 54, 55, 56, 59, 81, 86
and 95 answered, and 29, 39 and 96 — accounts rather than derivations — left
refused as declared. Round 9 of the order, retrieval, is closed and its
remaining items parked (round 8 was taken by Phase 96; round 9's N1 by Phase
100, item 5 with the citation leak by Phase 101, N2 by Phase 102 and I3 by
Phase 105).
**The next round starts from one of:** track M
(meta questions answered from the project's own documents) or track E
(explanations anchored in the registers — which is where outside
questions 29, 39 and 96 now sit), the second derivation study's §6 (a
non-Shannon inequality to try on `NOT_SHANNON` claims, rate distortion past
the tight range, Robin conditions), the rest of the cubic radical study's §8
(numeric degree above 6, the quintic in letters), or the lattice items
beside round 8: item 6 for the share-carrying rungs (item 10 was taken by
Phase 110, and the cubic trig study's §5 by the sharpening pass and Phase
109), and items 3 and 7, which need new pre-registrations.

Gated on outside material: item 4. Proposed
for retirement: P's 42 PIPELINE laws and H's concept 6. The letters below
are the record of what each item is.

The candidates as they were named follow.

**P. The laws in use — named by Phase 74, reworded and taken by Phase 75,
P1 taken by Phase 77, P3 by Phase 80, P4 by Phase 81, P5 by Phase 82, P2 by
Phase 83: closed; the named repairs measured by Phase 86.** At the owner's direction this was never a second law
subsystem: each law tested, improved where it can be, and absorbed only where
it is of use. What the closed items leave, for a later round if the owner
wants it: the soft floor's fixed-rate misses — Phase 86 measured the repairs
([`RATE_POSTERIOR_STUDY.md`](../studies/RATE_POSTERIOR_STUDY.md) §4): a finer
grid and a higher guard point repair nothing, an upper-credible rate rule
removes every on-grid break at a small retention cost, and the breaks above
the grid remain; adopting the upper-credible rule is a change of contract and
the owner's call; the
plain `resolve` and `agree` printing a session-marginal confidence (a change
of contract, the owner's call) — *both decided by Phase 89's 4-way matrix*
([`CONTRACT_MATRIX_STUDY.md`](../studies/CONTRACT_MATRIX_STUDY.md)): the combined
change (D) breaks no on-grid cell in either frame and keeps more right answers
than the upper rule alone, so it is the production baseline; the upper rule
alone and the session-marginal confidence alone are set aside; the breaks at
1/5 remain under every variant; and the 42 PIPELINE laws, which could only be
re-read through UBP pipelines the GLM does not implement.
[`AGREE_CHANNEL_STUDY.md`](../studies/AGREE_CHANNEL_STUDY.md) §3,
[`RATE_POSTERIOR_STUDY.md`](../studies/RATE_POSTERIOR_STUDY.md) §3,
[`LAW_TRIAGE_STUDY.md`](../studies/LAW_TRIAGE_STUDY.md) §3.

**O. The stepwise planner, round four — named by Phase 72, narrowed by
Phases 73 and 84.** In order: (O1) a held-out set of compound, goal, unit and register
questions written by someone outside the project (the corpora and the module
share an author, and every mark of both rounds was met on the first reading;
this is candidate B's point, sharpest here); (O3) the reverse relay into the
chain, so that `relay:` hands a column-2 value to the stepwise planner and its
multi-step answer chooses the next reverse operation (the last item of
candidate M) — *taken by Phase 88* as a program: a branch on a derived value
chooses which reverse equation `solve` reads
([`PLANNER_LOOP_STUDY.md`](../studies/PLANNER_LOOP_STUDY.md)); (O5) measurands by name — Phase 86 took the kinds of quantity
(a torque is no longer an energy, a temperature level no longer a
difference: [`MEASURANDS_STUDY.md`](../studies/MEASURANDS_STUDY.md)), and
Phase 87 took the rest — the declared map from register measurands to wheel
quantities, conversions through a stated efficiency and the elementary charge
([`MEASURAND_REGISTER_STUDY.md`](../studies/MEASURAND_REGISTER_STUDY.md)); a
radius, argued, feeds no wheel by name. What it leaves is that study's §6;
(O7) the widenings of
[`STEPWISE_TWO_STUDY.md`](../studies/STEPWISE_TWO_STUDY.md) §6 (tera and pico,
*heavier* with a declared field, folds over a whole column).
[`STEPWISE_PLANNER_STUDY.md`](../studies/STEPWISE_PLANNER_STUDY.md) §6,
[`STEPWISE_TWO_STUDY.md`](../studies/STEPWISE_TWO_STUDY.md) §6. *O2 (the frames
and givens with units) and O4 (register values feeding a wheel derivation)
were taken by Phase 73 and are met: every mark of the round-two study is
met. O7's first widenings (declared comparatives, *electrons* and *valence
electrons*, tera and pico, folds over every element or a declared class) were
taken by Phase 84 and are met ([`STEPWISE_THREE_STUDY.md`](../studies/STEPWISE_THREE_STUDY.md));
the present-rows question asked as its own was taken by Phase 85 and is met
([`HOLE_FOLDS_STUDY.md`](../studies/HOLE_FOLDS_STUDY.md)); the molecule table's
comparatives, further prefixes and the classes the register does not hold as
one value were taken by Phase 91 and are met
([`DECLARED_FRAMES_STUDY.md`](../studies/DECLARED_FRAMES_STUDY.md)); what O7
still holds is neutrons (a nuclide register) and differences between
molecules. O6 (a register value's stated precision carried through a derivation)
was taken by Phase 76 and is met ([`HELD_PRECISION_STUDY.md`](../studies/HELD_PRECISION_STUDY.md)).*

**N. Native past parity — named by Phase 70, narrowed by Phase 71; N1 taken
by Phase 100.** In
order: (N1) a declared resampling of the Lean corpus (every sub-corpus that
drops one file), to say whether the single-book figures of
[`NATIVE_PARITY_STUDY.md`](../studies/NATIVE_PARITY_STUDY.md) and the post-hoc
readings of [`NATIVE_WORDS_STUDY.md`](../studies/NATIVE_WORDS_STUDY.md) §3.3 —
Golay letter words alone ahead of the token overlap on hits, and ahead of the
part strings on the Lean corpus — are draws or effects; (N2, *taken by Phase 102 and closed in the negative*,
[`DOCUMENT_TREE_STUDY.md`](../studies/DOCUMENT_TREE_STUDY.md)) a third native
book for the documents — a section's position in the document tree as a Golay
word — to move the document rankings past parity with the raw vector; (N5) a
native word ranking with the part letter words as its **first** layer, which
would change the order outside the standard's ties, and a document letter word
that collides less on prose (study §6). *N1 was taken by Phase 100
([`CORPUS_RESAMPLE_STUDY.md`](../studies/CORPUS_RESAMPLE_STUDY.md)): the
single-book figures and the post-hoc readings are draws, N6 on the
declarations an effect. N3 (the native word ranking) was
taken by Phase 71 and is met; N4 (ledger row 6 on the live Lean ranking) was
measured there and missed at k = 1 (mark W6), so it is recorded, not shipped.*
*The owner's standing instruction: where a standard method ties or narrowly
beats a native one, keep the native one and refine it.*

**M. Reverse Three Column Thinking, round four — named by Phase 68, narrowed
by Phases 69 and 79; its first two items taken by Phases 94 and 95.** In the order of the study's §12: strings, tuples and
ranges as a third sort with count-first literals (22 of the 47 dialect
programs still outside act on them); a small imperative grammar, so that the
7 programs with state have sentences; and the loop further — let `relay:` read the integer certificate kinds, hand an
`INDEPENDENT` verdict's witness to the question layer as a follow-up, and let
the planner's answer choose the next reverse operation.
[`REVERSE_TCT_STUDY.md`](../studies/REVERSE_TCT_STUDY.md) §12. *The integer sort
(§9's third item) was taken by Phase 69 and is closed: every mark of §10.2 is
met (§11). The complete integer decision (§12's second item) was taken by
Phase 79 and is closed: every mark of
[`INTEGER_DECISION_STUDY.md`](../studies/INTEGER_DECISION_STUDY.md) is met.*

*L (Reverse Three Column Thinking, round two, named by Phase 67) was taken by
Phase 68 and is closed: every mark of the study's §7.2 is met (§8).*

**K. The connected machine, round two — named by Phase 66.** In the order of
the study's §6: (K1) route `-q` itself, once the owner agrees, and re-run the
contract set through the command line rather than by census — *taken by
Phase 89* on the owner's Option A: 177 of 177 contract questions identical
through the routed `-q` and `--plan`
([`QUESTION_SET_B_STUDY.md`](../studies/QUESTION_SET_B_STUDY.md) §5); (K2) a register
of **measurands** — *taken by Phase 87*: conversions through a stated
efficiency are laws across the junction table's non-identities
([`MEASURAND_REGISTER_STUDY.md`](../studies/MEASURAND_REGISTER_STUDY.md));
(K3) bind conversation follow-ups on every surface, not only the planner's —
*taken by Phase 92*: the router is the licence, and `GLM.py --converse` holds
the conversation ([`DISCOURSE_STATE_STUDY.md`](../studies/DISCOURSE_STATE_STUDY.md));
(K4) a Python builtin `derive(target, y, z)` so a derivation is a value a
program can use — *taken by Phase 88*
([`PLANNER_LOOP_STUDY.md`](../studies/PLANNER_LOOP_STUDY.md)). [`CONNECTED_MACHINE_STUDY.md`](../studies/CONNECTED_MACHINE_STUDY.md) §6.

**J. The carried fork, round two — named by Phase 65.** In the order of
the study's §6: declare and measure the composition of stages (the declared
cases, then a second reading, which resolved 35,872 of the 48,320 forks left
open at 32 cases post hoc, 0 wrong); give the runtime a second independent
view of one carrier so the second reading is routine rather than supplied by
the caller; and test the Leech escalation on a soft channel whose
reliabilities come from the machine's own readings rather than a declared
formula. [`CARRIED_FORK_STUDY.md`](../studies/CARRIED_FORK_STUDY.md) §6.
*All three taken by Phase 96*
([`SECOND_VIEW_STUDY.md`](../studies/SECOND_VIEW_STUDY.md)): the composition
declared and met on a fresh probe, the second view produced by a framed
register, and the soft channel of the machine's own views proved to add
nothing to the second reading.

**I. Python speech, round two — named by Phase 64.** In the order of the
study's §7: widen the dialect where the refusals cluster (string methods over
code points; list and dict literals as immutable snapshots); route a
question about a Python expression through a typed planner frame to the
evaluator (*taken by Phase 88*,
[`PLANNER_LOOP_STUDY.md`](../studies/PLANNER_LOOP_STUDY.md)); and index the AST address beside the Lean corpus addresses as a
retrieval key (*taken by Phase 105*,
[`AST_INDEX_STUDY.md`](../studies/AST_INDEX_STUDY.md)). [`PYTHON_SPEECH_STUDY.md`](../studies/PYTHON_SPEECH_STUDY.md) §7.

**H. Substrate-native cognition, round three — named by Phase 63.** In the
order of the study's §8: demote (or narrow) the two chemistry completion rules
that fail nested holdouts, `covalent_radius_pm` and `electron_affinity_eV`
(*taken by Phase 93 and met*: the first demoted, the second narrowed to the
main group, [`REGISTER_WORLD_STUDY.md`](../studies/REGISTER_WORLD_STUDY.md));
semantic judgements as annotated provenance (E4); frames generated from a
declaration rather than written by hand (E6, *taken by Phase 91 and met*,
[`DECLARED_FRAMES_STUDY.md`](../studies/DECLARED_FRAMES_STUDY.md)); deeper PCGS proofs (E7); a second
independent reading for the deep-hole fork (X1, *taken by Phase 96*: the
framed register produces it); and concept 6, which waits on
a trilinear object in the runtime.
[`SUBSTRATE_NATIVE_COGNITION_STUDY.md`](../studies/SUBSTRATE_NATIVE_COGNITION_STUDY.md) §8.

**E. Derivation across a declared union of wheels — done in Phase 66**, as the
*across wheels* frame with a declared junction table (study §3.5–§3.7). What
follows is the note as it was written. The
engineering surface derives inside one wheel at a time, as the formula study's
protocol does, and so refuses *derive power from pressure and volume flow
rate*; across the union of the ten wheels that formula (hydraulic power)
follows from W5 and W6. A second mode that names the union it used in the
answer, measured on a set written for it, would say what composition gains
and what it gets wrong. [`ENGINEERING_LANGUAGE_STUDY.md`](../studies/ENGINEERING_LANGUAGE_STUDY.md) §3.

**F. Typed physical operators — named by Phase 59, taken by Phase 90: closed.**
Monomial wheels cannot separate real, reactive and apparent power (W2-03),
nor dot from cross product. Complex power with conjugation, over the Gaussian
rationals the Smith chart already uses, is the smallest step. The record's
Priority 5. *Taken by Phase 90* ([`TYPED_OPERATORS_STUDY.md`](../studies/TYPED_OPERATORS_STUDY.md)):
every mark met. What it leaves is that study's §6: polar phasors, three-phase
power and power-factor correction, the planner's own DC `power` with an
alternating question (an earlier verdict, the owner's call), and the
verifier's rank algebra joined to the typed values.

**G. The archive Lean left behind — named by Phase 60, narrowed by Phase 61.**
Phase 61 rebuilt the small files the supplied-material ledger named —
`GolayMOG.lean`, `Distinction.lean`, `Seeds.lean`, `Fibre.lean`,
`Cheapest.lean` and `Independence.lean` — as `RequestProject/GLM/GolayMOG.lean`,
`Distinction.lean` and `SeedRoles.lean`, proving the irrationality of `e` that
they had assumed. What remains (Appendix C.3 of
[`GLM_ACADEMIC_PAPER.md`](../studies/GLM_ACADEMIC_PAPER.md)) is the language half of
`mog_cube_1`, about thirty files, and the unported part of `ObserverY.lean`; no
code path reads either yet. The vision experiments script
(`glm_vision_experiments_v14.py`) is the same kind of candidate on the Python
side.

**A. The planner as the default path — done in Phase 63.** The planner now
reads first, and `--grammar` opts out. What follows is the note as it was
written: the typed planner was opt-in because the command line renders every answer as a three-column
trace and a computed plan (an exact sum, a conversion, a primality witness)
has no trace kind yet. Asked in-process, the 177 contract cases differ in two
answers through the planner and both still pass; what remains is a trace for
the planner's own computations, then the switch, then the contract set run
through it. [`SEMANTIC_PLAN_STUDY.md`](../studies/SEMANTIC_PLAN_STUDY.md) §8.

**B. A held-out set nobody on the project wrote — named this round.** The
held-out sets were committed before the planner and share its author; an
independently written set of questions, with labels from outside the
registers, is the test that would separate reach from anticipation. The
scoring rule and the harness exist (`evaluation/heldout.py`,
`reasoning/typed_plans.py`). *Taken by Phase 89 with the owner's two outside
sets* ([`QUESTION_SET_B_STUDY.md`](../studies/QUESTION_SET_B_STUDY.md)): before
any frame the router read none of the 126 questions; with declared question
frames Set B is 14 of 14 by audit and Outside O1 27 of 112, 0 confidently
wrong. What it leaves is that study's §8, the located boundaries.

**C. The register against the world — partly done in Phase 63, taken by
Phase 93** ([`REGISTER_WORLD_STUDY.md`](../studies/REGISTER_WORLD_STUDY.md): all
354 cells of atomic weight, ionization energy and configuration read against
frozen CIAAW and NIST sources; 24 ionization energies and one configuration
discrepant; the register never written). What follows is the note as it was
written. A question
can now ask whether a register value is consistent with the declared standard
table, at the precision each is held to; the full discrepancy report over
every row is still open. The planner's one
wrong answer is the element register holding iron's atomic weight as `55.84`
where the IUPAC value is `55.845`. The roadmap's external-truth layer — a
discrepancy report of register values against cited standard values, never
overwriting the register — would find every such row rather than the one a
question happened to reach.

**D. Discourse state, typed — taken by Phase 92**
([`DISCOURSE_STATE_STUDY.md`](../studies/DISCOURSE_STATE_STUDY.md): *the one
before that*, the plurals and *why?* are read). The conversation layer bound
three surface shapes of follow-up; the planner's typed slots are the state a fourth shape
needs (*the one before that*, *both of them*), and a set-valued referent is
what candidate 0 below asks for.

**0. The second turn, carried further — named the round before last; both
halves taken by Phase 92** ([`DISCOURSE_STATE_STUDY.md`](../studies/DISCOURSE_STATE_STUDY.md):
the tie is carried as a column, refused `column-incomplete` under a hole, and
the fourth shape is read). The conversation
layer binds three declared shapes of follow-up and refuses everything else,
and the two things it most obviously cannot do are each a round: a **fourth
shape** that is not a surface pattern at all — *the one before that*, *both of
them*, *why?* — and a **tie carried forward rather than refused**, so that
*describe it* after a fourteen-row tie asks its question of all fourteen and
reports a column rather than a refusal. The second is the more interesting:
it turns the layer's sharpest refusal into the extremum operation's kind of
answer, and it needs a statement of what *the answer for several rows at once*
is before it needs any code.
[`CONVERSATION_STUDY.md`](../studies/CONVERSATION_STUDY.md) §8, whose §9 now
records the outcome of every piece of the supplied material: four were taken
in Phase 56 — two shipped, one measured into the sandbox and one refuted — and
the rest stand with what they would have to measure to earn a round.

**1. The two halves of the conversion table — named by Phase 55; the
measurand half taken by Phase 87, the offset half by Phase 99: closed.**
*The measurand half* ([`MEASURAND_REGISTER_STUDY.md`](../studies/MEASURAND_REGISTER_STUDY.md)):
every scale of the table has a declared measurand, and every pair the table
relates is a pair of one kind, so none is withdrawn. *The offset half*
([`CELSIUS_REGISTER_STUDY.md`](../studies/CELSIUS_REGISTER_STUDY.md)): a
register now holds a Celsius reading — the fourteen ITS-90 defining fixed
points in `data_objects/fixed_points.py`, the field surface's table
`fixed_point`, `temperature_C` only — and the scale table has its first
offset row, `fixed_point:temperature_C` (factor 1, offset 27315/100). That
row carries 14 of 14 points onto ITS-90's own kelvin column exactly, so the
offset half of `GLM.ScaleConversion.cmpQ_apply` is now exercised by a
declared row rather than proved and unshipped
(`RequestProject/GLM/CelsiusRegister.lean`). The ordering and extremum
operations carry a Celsius reading into kelvins before comparing; the
stepwise planner reads it as a level through `scale_into_si_affine` and
refuses it `LEVEL_AS_DIFFERENCE` where a law reads a difference; the
factor-only `scale_into_si` refuses an offset row `OFFSET_UNIT`. Phase 86's
Celsius and Fahrenheit *givens* in the planner
([`MEASURANDS_STUDY.md`](../studies/MEASURANDS_STUDY.md)) are unchanged beside
it. What it leaves is that study's §7: a register in degrees Fahrenheit (a
declaration — factor 5/9, offset 45967/180 — that
`GLM.MeasurandKinds.fahrenheit_kelvin` already states), an answer *stated* in
degrees Celsius (a level out through the offset), the ITS-90 vapour-pressure
ranges as values with an interval, and the owner's decision on the element
register's aluminium melting point (933.437 K, 0.036 K below ITS-90's
933.473 K). What follows is the note as it was written, before either half
was taken. The declared table relates nine scales over four quantities, and two
of its commitments are written but untested. The affine shape admits an
**offset** and no declared row uses one, so the half of
`GLM.ScaleConversion.cmpQ_apply` that the offset exercises is proved and not
shipped: a register holding a temperature in degrees Celsius, or any scale
that does not start at its quantity's zero, is what would settle it. And the
table declares a **unit** rather than a measurand, so it cannot say that an
atomic radius and a covalent radius are two different measurements that happen
to share picometres. A second declaration — measurands, and which pairs of
them are comparable — is the harder and more interesting of the two, because
it is the first thing in this system that would have to be argued for rather
than looked up.
[`SCALE_CONVERSION_STUDY.md`](../studies/SCALE_CONVERSION_STUDY.md) §9.

**2. What a fold other than a maximum does with a hole — done in Phase 85**
([`HOLE_FOLDS_STUDY.md`](../studies/HOLE_FOLDS_STUDY.md)): a median or a rank
over a column with holes is the exact interval every completion lands in,
proved sharp in `RequestProject/GLM/HoleBounds.lean`; the ends are refused as
open; the present-rows question is answered as its own with the missing rows
named. What it leaves is the study's §6: top-*k* and other quantiles as
frames, a mean bounded by a declared range, and present-rows parity counts —
all three taken by Phase 91 and met
([`DECLARED_FRAMES_STUDY.md`](../studies/DECLARED_FRAMES_STUDY.md)), the top
*k* under a hole refused whole.
What follows is the note as it was written. The extremum
operation refuses a column with a missing reading, and proves why. A rank, a
median or a top-*k* over the same column each need their own statement of what
a hole does to them — a median over the present rows is not the median, but it
is wrong in a different way and by a different amount — and none of the three
is built. The narrower question beside it is the answerable one the refusal
declines: *of the rows that are filled in, which is the largest?* is a
different question, and it would have to be asked as one, with the missing
rows named in the answer rather than in the refusal.
[`COLUMN_EXTREMUM_STUDY.md`](../studies/COLUMN_EXTREMUM_STUDY.md) §7.

**3. The eight reasoning modules nothing runs — done in Phase 66**: each is
reachable as a tool, and the audit reads 0 of 96 unreached. What follows is
the note as it was written. **The other half of the wiring
audit.** The wiring
audit recorded in [`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 56 reads the import
graph of the package from every entry point it actually runs from, and finds **8** of the
**89** `reasoning/` modules outside the closure: `deep_dive`, `llvq`,
`moonshine`, `pcgs`, `salvage`, `salvage_second`, `stability` and `tie_break`.
Every one of them has a test file and a study, so each is a result that was
reached, checked and written up — and then left where nothing on the machine's
own path can call it. Two of them (`llvq`, `salvage`) are named only inside a
generated recompute script, which is real but runs only when a reader
recomputes a receipt; three more (`deep_dive`, `pcgs`, `salvage_second`) are
catalogued as file paths in `reasoning/combiner.py`'s source table without
ever being imported. The round this becomes is not a port: it is one decision
per module, *reachable or retired*, taken with its study open, and the honest
outcome for some of them is the archive. Re-read it with
`python3 studies/scripts/wiring_audit.py`.

*Closed this round (Phase 57):* candidate 4 of the list as it stood, *the
measurements no reader sees*. All **20** registered figure keys that no
document quoted are now quoted — none was retired, because each was a number
its document was already saying by hand or should have been saying — and the
converse of **D6** is a checked rule rather than a habit:
`tests/test_figures.py::TestEveryRegisteredFigureIsQuoted` fails when a
registered key is read by no document, and when a document quotes a key the
registry does not hold. Closing it exposed a defect worth the round on its
own: `corpus-documents` counted **98** documents where the corpus study's own
inventory counted **95**, because the key counted the three documents the
machine *generates*, which are outputs of the corpus rather than parts of it;
the three document-count keys are now taken over the written corpus, the set
the digest guards. It also turned up a plain D6 breach — the
operation-escalation study was typing its deciding figure by hand. The audit
now reads **135 registered, 135 quoted, 0 never quoted**
(`python3 studies/scripts/wiring_audit.py`).
[`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 57.

*Closed in Phase 56:* not a candidate from this list but the four
rows of [`CONVERSATION_STUDY.md`](../studies/CONVERSATION_STUDY.md) §9 — the
supplied conversational material Phase 54 read, ran and left unported. The
**role–filler binding** and the **procedural-plan store** ship:
`reasoning/role_binding.py` writes a typed relation between two named carriers
as one 24-bit word whose inverse is itself, and `runtime/plan_store.py` keeps
a resolved follow-up — refusals exactly as answers — under a digest of the
whole conversation it was resolved in, wired into `runtime/conversation.py` as
an optional `store=`. `RequestProject/GLM/RoleBinding.lean` and
`RequestProject/GLM/PlanStore.lean` prove what is a theorem rather than a rate:
unbinding inverts binding for every role and pair, recovery by name is sound
and refuses exactly when the reading is not unique, replay agrees with running
and preserves a refusal, and the exact key separates two conversations that
share a follow-up where the coarse one does not. The **four-register memory
split** and the **Lean-source generator** were measured and declined: both sit
in `glm_universal/sandbox/` with a computed checklist that says `ready is
False`. Under directive **D15** it moved **addressing** and **refusal**.
[`SUPPLIED_PORTS_STUDY.md`](../studies/SUPPLIED_PORTS_STUDY.md). It also carried
the wiring audit that became candidate 3 above and the round Phase 57 then
took, and it closed on two
defects of its own that the suite found: the plan store's digest went round
`hashlib` instead of `glm_universal.integrity`, which breaks **D3**, and the
binding was an unclassified exclusive-or site in `reasoning/combiner.py`'s
table. Both are fixed, and the sandbox now reads its own occupancy rather than
asserting it (`glm_universal.sandbox.occupancy_report`).

*Closed in Phase 55:* candidate 1 of the list as it then stood — the scales
neither operation could bridge. `glm_universal.reasoning.scale_conversion`
declares nine scales over four quantities, each row an exact positive-affine
map into the quantity's canonical unit with the source its numbers came from,
and `RequestProject/GLM/ScaleConversion.lean` proves that a positive
conversion composed into the comparison leaves the verdict alone, that the
wider operation never changes an answer the bare one gave, that its silence is
still exactly stated, and that the declaration itself carries the claim. On a
declared set of twelve questions it answers seven and refuses five, all twelve
as declared, and it leaves the two operations underneath it unchanged on their
own declared sets. Under directive **D15** it moved **refusal** — three of the
five refusals are comparisons the table was given the chance to license and
did not — and widened **derivation** to a fold over rows of two tables at
once. [`SCALE_CONVERSION_STUDY.md`](../studies/SCALE_CONVERSION_STUDY.md).

*Closed in Phase 54:* not a candidate from this list but the
material supplied with the round — `source_material/conversation_experiment/`,
tested rather than believed. All eight of its scripts run unmodified against
the package; two of its headline claims are refuted (the higher-order analogy
whose second constraint has no exact solution, and the periodic-table reading
that renames two carrier coordinates); and the one thing in it the system
could not do is built, measured, proved and released: a turn that refers back
to an earlier turn, bound by licensing, `8` of `15` declared follow-ups bound
and `7` refused against `0` for a session with no memory. Under directive
**D15** it moved **addressing** and **refusal**.
[`CONVERSATION_STUDY.md`](../studies/CONVERSATION_STUDY.md).

*Closed in Phase 53:* candidate 1 of the round before it — the column
rather than the pair. The `extremum` query kind and
`reasoning/column_extremum.py` read one coordinate off every row of one
declared table and fold it exactly, naming every row that attains the end, or
refuse under one of four named reasons, and
`RequestProject/GLM/ColumnExtremum.lean` proves that the silence is exactly
the second scale, the hole and the empty column, that the value returned is
one of the column's own with nothing past it, that the rows named are exactly
the rows attaining it, and that both refusals are results rather than
fussiness. Under directive **D15** it moved **derivation** — a fold over
addressed readings, which no register holds — and **refusal**, on a declared
task set of eight columns, all eight as declared.
[`COLUMN_EXTREMUM_STUDY.md`](../studies/COLUMN_EXTREMUM_STUDY.md).

*Closed in Phase 51:* candidate 1 of the last round — the comparison
the field surface could not make. The `ordering` query kind and
`reasoning/coordinate_order.py` read one coordinate off two rows and order it
exactly, or refuse under one of three named reasons, and
`RequestProject/GLM/CoordinateOrder.lean` proves that the silence is exactly
the missing reading and the mismatched scale, that the answer is the order of
the two values, and that *same scale* is the right side condition because a
rescaling of one reading alone flips the comparison. Under directive **D15**
it moved **derivation** — of the weakest interesting kind, one exact
subtraction over two addressed readings — and **refusal**, on a declared task
set of seven comparisons, all seven as declared. All
10 of the probe's held-and-unreachable
questions are now parsed. [`ORDERING_STUDY.md`](../studies/ORDERING_STUDY.md).

*Closed in Phase 50 (maintenance):* the release Phase 49 had not run,
and the six units that failed it — the UBP source audit taught to read the
declared float sites off the D11 inventory, the reasoning kernel's import
audit, the Lean file count, the query-escalation cache, and the relay and
anonymous measurements re-taken over the grown corpus. It moved none of
derivation, addressing or refusal, and leaves the candidates above unchanged.

*Closed in Phase 49:* the supplied *History Recorded in the Now*
material, decided rather than illustrated — nine claims settled, three of them
refuted, the refusal faculty moved on a declared task set, and the shipped
modulator's loop replaced by the closed form it was always computing.
[`NOW_RECEIPT_STUDY.md`](../studies/NOW_RECEIPT_STUDY.md). It leaves two things
named there and not taken: the v4 query-loop reading, which has no control, and
the v4 higher-lattice escalation, which was argued rather than run.

*Closed in Phase 48 (maintenance):* the handover the round before it
left open — the generated layer refreshed and every unit re-signed — and the
cost of `report lean`, which had grown through the evaluation's 300-second
ceiling. It is now 77 seconds, by an exact identity and an exact pruning
bound, with every figure of
[`LEAN_ADDRESS_STUDY.md`](../studies/LEAN_ADDRESS_STUDY.md) §7 unchanged. Neither
is a claim about reasoning, and the candidates above are unchanged by it.

*Closed in Phase 47 (maintenance):* the round loop itself. The
ledger's Lean selectivity, undone by the field surface reading the development
on the runtime's import path, is restored and pinned by tests — a median Lean
edit costs **27** of 98 units rather than 79 — and a passing documents check
is no longer re-derived over a tree in which nothing has moved. Neither is a
claim about reasoning; both are recorded as what they are, in §5e and §5f of
[`ITERATION_COST_STUDY.md`](../studies/ITERATION_COST_STUDY.md). The candidates
above are unchanged by it.

*Closed in Phase 46:* the field surface itself — candidate 1 of the round
before it. It answers 9 of the
10 questions the translation
experiment found held and unreachable, exactly the number declared reachable
before the run, and it is reported as coverage rather than reasoning:
[`FIELD_SURFACE_STUDY.md`](../studies/FIELD_SURFACE_STUDY.md), with the
description in §2 and the proved boundary in `GLM.FieldSurface`.

**3. The empty rungs of the power-of-two family.** The family is complete as a
family and deliberately incomplete as a *ladder*: norms 2 and 256 are empty in
the ladder actually used, because the rungs that would fill them conflate. What
would close it is a rung at those norms that does not — Construction `A` over a
shortened code, or the `D₄`/`E₈` layers, which the scaling does not generate.
[`NORM_FAMILY_STUDY.md`](../studies/NORM_FAMILY_STUDY.md).

**4. A register that arrives anonymous on its own.** Renaming is a faithful
model of a cross-vocabulary goal and it is still a model. The measurement to
want is the same table over goals from a second Lean development, or from a
generator, scored against the same controls — a register nobody constructed.

**5. The leak in the feature map.** The shipped map counts the type vocabulary
wherever it occurs, including inside an identifier, so 39 of 883 queries lose a
coordinate when their names go: a name creeping into a reading that is supposed
to be structural. Either the map is narrowed to count type words only where
they are types, or the leak is priced. *Phase 100 found its twin in the
citation index* ([`CORPUS_RESAMPLE_STUDY.md`](../studies/CORPUS_RESAMPLE_STUDY.md)
§4.4): a token resolves to a declaration by a unique short name, and ten
declarations have one-letter short names, so every bound variable `a`, `A`,
`e`, … counts as a citation — 3,231 of 15,012 citation edges, 2,448
declarations carrying one, `GLM.Heisenberg.a` "cited" by 1,920. It reaches
the `cites` and `cited by` coordinates of the structural address and the
retrieval relevance sets (a citation in either direction is relevance). The
two are one round: narrow both readings, then re-take every Lean-corpus
retrieval figure under the repaired relevance, keeping the old ones as the
record.
*Taken by Phase 101 and met*
([`CITATION_SCOPE_STUDY.md`](../studies/CITATION_SCOPE_STUDY.md)): the type
words count whole identifiers (0 of 836 goals lose a coordinate), citations
are read in Lean's scope and scored against the elaborator's own graph
(99.1 % precision against 52.1 %), and every Lean-corpus retrieval figure was
re-taken with the old ones kept.

**6. The separation criterion, still unmet.** `nearest_correct` in
`DeepHoleLadder.lean` says a reading names holes correctly whenever
`ρ = 2W/B < 1`. Measured, `ρ` falls from `3.90` to **`2.59`** across the ladder
and never crosses `1`, so a classifier that names 40 of 44 still cannot certify
a single *absence*: faithfulness needs `r ≥ 0.0659` where separation permits
`r < 0.0179`. Either a rung is found where `ρ < 1`, or a bound is proved saying
no reading of this family reaches it. Its companion is
`GLM.DeepHoleFailure.per_type_absent`, the certificate whose hypothesis is
currently unmet, so the theorem is instantiated nowhere.

**7. The thirteen unreached Niemeier types.** The ensemble reaches **10** of
the 23 root systems from the 14 declared centres; the other **13** are reported
as unreached and nothing is claimed about them. Reaching them means new
centres, and new centres mean a new pre-registration.

**8. What the adopted guard costs, and why the metric reading is safe.** The
guard refuses 137 queries it used to answer correctly. The room is in the
*reading* rather than in the contract — the weaker guard is measured and never
reaches safety — and the metric reading answers nothing wrongly on any of the
six operations while losing to the primary on four, which is a decomposition
worth understanding. A margin other than twice the nearest distance is the
obvious sweep. [`SECOND_READING_STUDY.md`](../studies/SECOND_READING_STUDY.md) §9.

**9. The planner's utility gate.** The reverse-call planner satisfies every
safety line of its promotion checklist and fails the one that decides it: on
this project's own evaluation set it gains nothing, because the refusals it is
offered are refusals it agrees with. The question that would close it is about
the **tool registry** — whether a tool exists that a problem-driven front end
could reach and the kind-driven dispatcher cannot. Until one does, directive
**D14** keeps the planner in the sandbox, imported by nothing the system
computes with. *Re-read by Phase 88*
([`PLANNER_LOOP_STUDY.md`](../studies/PLANNER_LOOP_STUDY.md)): the loop's
questions are answered when written as programs and by no surface when asked
in English — the first measured instance of the reach this item asks for. The
promotion line is still failed, because the supplied planner itself does not
reach them; reading such a question from English is the next measurable step.

**10. A conflation the rational reading must make.** Read alone, the exact
distance measure conflates `A_1^24` with `A_2^12`. That is a capacity boundary
of the kind [`INFORMATION_LOSS_STUDY.md`](../studies/INFORMATION_LOSS_STUDY.md) is
about, and it is recorded as an observation rather than as a theorem. The
theorem to want says *which* pairs any stray-blind reading must conflate.
*Taken by Phase 110 and met*
([`STRAY_BLIND_STUDY.md`](../studies/STRAY_BLIND_STUDY.md)): a reading of
distances alone conflates two equal-size records exactly when their stray
spectra agree (`GLM.StrayBlind.distances_eq_iff`), and one blind to the
strays as well conflates every deep hole. The measured ladder agrees at
every size: `A_1^24`/`A_2^12`, the only two stray-free holes. For item 6 this
means the `L₃` rung cannot reach `ρ < 1` at a measured size
(`not_resolves_of_indist`); item 6 stays open, narrowed to the
share-carrying rungs.

**The discipline any of them is taken under**, unchanged: the thing must be
described or measured rather than asserted, what does not generalise must be
counted rather than hidden, the path it replaces must be frozen so the new one
has something to agree with, and the end-to-end evaluation must return the same
answers and the same refusals. What should **not** generalise is the
judgements — which brackets count as ordinary cases, which factor basis may
explain a dimensional difference, which pole a word names, which phrasings are
the same question — and a `Phrasing` cannot be constructed without the sentence
that justifies it. Coverage stays two figures rather than one: three of the
eight registers are described, and seven of the twenty-three answerable query
kinds are.

