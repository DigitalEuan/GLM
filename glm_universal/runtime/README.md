# `glm_universal/runtime` — the interactive geometric language runtime


## Tier 0 — the coarse read

**Question.** How is the machine actually asked a question, and what can it be asked?

**Verdict.** `session.DOMAINS` is the authoritative list.

**Deciding figure.** 8 registers holding 1,143 carriers, loaded lazily and cached.

**Recomputed by.** `glm_universal.figures.package_figures`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

**Parent:** [`../README.md`](../README.md) · **Repository root:**
[`../../README.md`](../../README.md)

A few modules turn the substrate, the carriers and the reasoning kernel
into something a person can hold a conversation with:

```
runtime/
├── parser.py      deterministic semantic query parser (20 answering kinds + `unknown`)
├── session.py     GeometricSession: one solver per kind, registers, history
├── solution.py    Solution, Step, InferenceRecord, SolverError — what a solver returns
├── payload.py     the shared payload helpers every solver formats its facts with
├── reports/       the 47 `report` solvers, as eleven mixins — see below
├── tct_engine.py  Three Column Thinking trace generation + verification
└── __init__.py    public API exports
```

## The registers

`session.DOMAINS` is the authoritative list: **<!--figure:registers-->8 registers<!--/figure-->**, loaded lazily
and cached, holding 1,143 carriers between them — physics 726, chemistry 118,
molecules 51, mathematics 22, lexicon 149, spatial 28, harmonics 28,
economics 21.  `molecules` is the
newest: 51 molecules and ions, every coordinate derived from the element
register rather than tabulated.  The counts here are the ones
[`../../FIGURES.md`](../../FIGURES.md) recomputes under *Registers*.

## The query kinds

`parser.KINDS` is the authoritative list: **<!--figure:query-kinds-->24 query kinds<!--/figure-->** — twenty-three
answering kinds plus `unknown`, the honest fallback.

| Kind | Surface | What it does | Wired in |
|---|---|---|---|
| `verify` | `force = mass * acceleration` | multi-plane equation audit | v0.4.0 |
| `analogy` | `A : B :: C : ?` | proportional analogy in a named subspace | v0.4.0 |
| `describe` | `describe carbon` | the dossier of one carrier (with lattice projection) | v0.4.0, augmented v0.5.3 |
| `nearest` | `nearest 5 to pressure` | ranking under the Griess metric (the Leech inner product on Q²⁴) | v0.4.0 |
| `product` | `sakuma product` | the Norton-Sakuma 2A algebra | v0.4.0 |
| `cluster` | `cluster C, N, O into 2` | exact agglomerative clustering (`linkage = single \| complete`) | v0.4.0 |
| `spatial` | `mog grid of oxygen` | the MOG presentation of a carrier | v0.4.0 |
| `project` | `project carbon oxygen` | walk all five dimension-projection layers | v0.5.3 |
| `trilinear` | `trilinear 127 432 463` | the invariant form ⟨A·B, C⟩ | v0.5.3 |
| `coherence` | `coherence carbon` | the five-shell NRCI breakdown | v0.5.3 |
| `angle` | `angle carbon oxygen` | exact cosine comparison | v0.5.4 |
| `report` | `report <subject>` | on-demand recomputation of a body of facts — see below | v0.5.4 |
| `task` | `task grid` | a worked end-to-end task: `grid`, `physics`, `concepts` | v0.8.0 |
| `pi_groups` | `pi groups force, mass, acceleration, length, time` | Buckingham-Pi: the dimensionless groups of a set of quantities, from the rational nullspace of the EXT10 exponent matrix | v1.0.0 |
| `meaning` | `meaning of water`, `relate energy torque` | what a notation denotes, its 24-coordinate meaning carrier and its round trip; with two terms, every relation derivable between the two meanings, each re-checked from the meanings alone. A term with no determinate referent is refused with its reason | v1.1.0 |
| `real` | `approximate sqrt(2) to 20 places`, `approximate (1+sqrt(5))/2 to 12 places`, `approximate exp(1) to 20 places` | reads the expression as a *process* over `reasoning/real_expr.py` — which since v1.2.0 also reads `exp`, `log`, `sin`, `cos`, `tan` and a non-integer exponent through `reasoning/transcendental.py` — and asks it for enough precision to settle the requested decimal places. No float is constructed, and the answer says plainly that no carrier holds the value: what the machine holds is the rule that converges to it | v1.2.0 |
| `compare` | `is pi less than 355/113`, `compare sqrt(2) and 1.5`, `which is bigger e or pi`, `is 2^pi less than 9` | reads both sides as processes and refines them along the ladder `2⁻⁸, 2⁻¹⁶, …, 2⁻²⁵⁶` until the intervals come apart, reporting the precision that settled it. Inequality is decided; two sides that never separate come back "not distinguished", because equality of processes is not decidable and the machine does not claim it | v1.2.0 |
| `measure` | `measure hot in tea`, `measure hot`, `measure 300 in tea` | a measure word read against a comparison class, as an exact magnitude — `low + position * (high - low)` over the 45-class register, with the same word against every class of its quantity when no class is named, and the inverse reading when the subject is a magnitude. A word measured against a class of another quantity (`measure large in room`: `large` measures volume and `room` brackets a length), or a word on no scale at all, is refused with the reason, which `GLM.Info.boundary_empty_of_unmeasured` says is forced rather than missing | v1.5.0 |
| `comparative` | `is cold in stellar_surface hotter than hot in tea`, `is hot in tea as hot as hot in tea` | the comparative and the equative between two *uses*, recognised structurally rather than by keyword: both sides are read as exact rationals and compared, and the direction is the degree word's position relative to the midpoint of its scale. Refuses across quantities, on an unmeasured use, and on a word that sits exactly at the midpoint and so names no direction. The word order does not decide it — `cold` for a star is hotter than `hot` for a cup of tea — which `GLM.Info.comparative_not_determined_by_word_order` proves and `comparative_audit()` measures at 151 of 204 cross-class pairs | v1.9.0 |
| `derive` | `derive span_ratio of tea`, `derive numerator of perfect_fifth in harmonics` | one coordinate of one object, answered off the domain descriptions in `glm_universal.recipe` rather than off a hand-written phrase: the answering path holds no rule of its own, so a new description costs no new parsing rule. The rule that computed the value and the held quantity it came from are reported beside it, and a coordinate no description derives is refused with the reason, which `GLM.Recipe.Spec.answer_eq_none_iff` says is exactly the boundary | v1.11.0 |
| `field` | `field atomic_weight_u of carbon`, `fields of water` | one named field of one named row, over the declared tables of `glm_universal.runtime.fields`: the element and molecule source rows, each register's carrier attributes, the Lean address book, the package's own top-level definitions, and a declared registry of zero-argument functions addressable by key. The second shape names the fields a row answers to. It is `table`, the weakest faculty, and says so in every answer; it refuses an unknown row, an unknown field and a field the register records as missing, and `GLM.FieldSurface.lookup_eq_none_iff` says the answerable pairs are exactly the declared ones | v1.18.0 |
| `ordering` | `order abstract_concrete of energy and water`, `order atomic_weight_u of carbon and oxygen` | one coordinate read off *two* rows and ordered exactly, or refused. Each side is a reading — a value with the scale it was read on, `table:field` — and a coordinate held inside a mapping field, which is how the lexicon register keeps its ten semantic primitives, is read as a coordinate of that field. It refuses in three named ways: a coordinate the row does not hold, a reading that is a label rather than a quantity, and two readings on different scales. The last is the point of it: `GLM.CoordinateOrder.naive_order_is_not_scale_free` exhibits a positive rescaling that flips the comparison of two raw numbers, and `order_scale_invariant` shows that no rescaling of a shared scale can | v1.19.0 |
| `extremum` | `largest atomic_weight_u in element`, `largest abstract_concrete in carrier:lexicon` | one coordinate read off **every** row of one declared table and folded to its extremum, or refused. The end is read off the opening word — `largest`, `highest`, `maximum` against `smallest`, `lowest`, `minimum` — and every row attaining the end is named rather than one of them picked. It refuses in four named ways, two of them the reason it exists: a column with a hole in it, because `GLM.ColumnExtremum.extremum_over_present_is_not_the_extremum` exhibits a column whose extremum over the rows that are filled in is a different value at a different row, and a column gathered from more than one scale, because `extremum_not_invariant_under_one_row_rescaling` exhibits a one-row rescaling that moves the winner while `extremum_scale_invariant` shows that rescaling the shared scale cannot. The other two are `not-ordered` and `no-such-column` | v1.20.0 |
| `unknown` | (fallback) | diagnostics + suggestions | v0.4.0 |

## The `report` subjects

`session.REPORT_SUBJECTS` is the authoritative list: **<!--figure:report-subjects-->65 report subjects<!--/figure-->**.
Every subject recomputes its facts on demand and has a Three Column Thinking
template that reproduces them in a fresh interpreter.

### Where the solvers live

`session.py` holds the dispatcher — the subject-to-solver decision, and
nothing else about a report. The solvers themselves are in `reports/`, one
module per family, each a mixin `GeometricSession` composes and each *named for
the sub-package whose subjects it answers*:

| module | mixin | solvers | the family |
|---|---|---|---|
| `reports/substrate.py` | `SubstrateReports` | 5 | the Golay code, decoding, the frame bridge, the transform decoder |
| `reports/lattice_geometry.py` | `LatticeGeometryReports` | 10 | Leech geometry, deep holes, the rungs above 24, the algebra layers |
| `reports/registers.py` | `RegisterReports` | 7 | what the eight registers hold, and their audits |
| `reports/resolution.py` | `ResolutionReports` | 4 | the layer chain, the ceiling, the name coordinate, escalation |
| `reports/signal.py` | `SignalReports` | 8 | delta-sigma, noise, drift, mantissas, containers, shells |
| `reports/ledgers.py` | `LedgerReports` | 5 | the supplied documents read as live claim ledgers |
| `reports/semantics.py` | `SemanticsReports` | 1 | the concept graph audited and the grounded graph that replaces it |
| `reports/migration.py` | `MigrationReports` | 3 | the stored state brought in literally |
| `reports/development.py` | `DevelopmentReports` | 3 | the project's own instruments: directives, pipeline, capabilities |
| `reports/recipe.py` | `RecipeReports` | 1 | the domain descriptions, and the domains regenerated from them |
| `reports/language.py` | `LanguageReports` | 1 | the question descriptions — the three slot shapes the parser now reads instead of the branches it used to have, and the infix family measured against the branches it has not yet replaced |

The modules live under `runtime/` rather than inside the sub-packages they are
named for, so that the import direction stays one-way — the runtime imports a
sub-package and never the reverse. `reports/__init__.py` exports
`REPORT_MIXINS`, and `tests/test_runtime.py` fails if a `_report_` solver
reappears in `session.py`, if the eleven do not hold exactly 47 between them,
or if a module in `reports/` is not registered.

| Subject | What it recomputes |
|---|---|
| `relations` | the 222 scalar + 71 tensor relation audit, with facet attribution |
| `leech distribution` | the Λ/2Λ class census (98,280 type-2 classes) |
| `theta` | the theta-series coefficients of Λ₂₄: 1, 0, 196560, 16773120, 398034000, 4629381120 |
| `subalgebra` | the Norton-Sakuma 2A subalgebra: closed, commutative, nowhere associative |
| `information loss` | what each layer loses, where the boundaries are, whether addition descends (aliases: `report loss`, `report boundaries`) |
| `golay decoding` | the coset table and complete decoding, including the weight-5 miscorrection theorem |
| `leech construction` | the Construction A/B/C ladder, 48 / 98,256 / 196,560 |
| `facets` | the six-facet partition of the 24 coordinates: strictly linear, orthogonal, no facet redundant |
| `monster stack` | the ten-plane 2-adic Monster stack: 5 planes compose strictly, 8 with pair repair |
| `multiresolution` | the F₂⁴ ↔ GF(4) × Z₄ fibration and the cross-level products |
| `migration` | the legacy → canonical Golay frame bridge: the two codes share 8 of 4,096 codewords, and the bridge is a weight- and distance-preserving isometry |
| `state migration` | the literal migration of the stored state: 4,282 concepts and 4,014 edges into the canonical frame, 398 carriers minted |
| `concept store` | the indexed payload — 4,680 concepts, 4,014 edges — with labelled paths and Hamming neighbourhoods |
| `fusion` | the Ising fusion layer: adjoint action, eigenspaces, both Miyamoto involutions |
| `benchmarks` | every suite score against its published baseline, with the findings |
| `infinite values` | the whole value layer recomputed: `sqrt(2)`, `pi`, `e` and `phi` to 20 places, the tower's stand-ins and the level that exposes each, the `1/N` law at `N = 10, 100, 1000`, the 24-D carrier on a reachable target (deviation 0) and on the ramp target (deviation `19/300`, accumulator `311/24`, separating certificate with gap `13/5760`), and the undecidability of equality |
| `capabilities` | the 33 capability probes of `glm_universal/capabilities/`, run for real: how many hold, how many break, and the exact place each break stops. A probe whose verdict differs from its declared expectation is reported as a *surprise* |
| `superposition` | the six-fold tie at a deep hole of the Golay code, held as one value: the sextet partition, the F₂ bundle that collapses to all-ones against the rational bundle that is injective and invertible, contextual collapse (`collapsed` / `superposed` / `refuted`, never broken by member order), and the separating certificate behind alphabet expansion (aliases: `report ambiguity`, `report tie`, `report sextet`, `report bundling`, `report parallel hypotheses`, `report list decoding`) |
| `semantics` | the audit of the inherited concept graph — how many of its 4,282 concepts denote anything, how its 4,015 edges classify, what its stored carriers turn out to measure — and the grounded graph that replaces it (aliases: `report meaning`, `report grounding`) |
| `analogies` | the named relation models re-solved case by case: which model recognised the relation, what it answered, and whether the mathematics of the case agrees. A refusal is a row like any other (aliases: `report analogy`, `report analogy models`, `report relation models`, `report proportional analogy`) |
| `transform decoder` | the 4,096 Golay coset costs as one Walsh–Hadamard transform, and the tier at which the constant-time lookup can prove its own answer (aliases: `report fwht`, `report walsh`, `report hadamard`, `report transform`, `report o(1) lookup`, `report certificate`, `report llvq`, `report soft decoding`) |
| `deep holes` | classification of a carrier by its nearest Niemeier type as a *process* — walk to a hole, climb to the covering radius, read the vertices off the trajectory, certify the reading — with nothing stored but a derived catalogue (aliases: `report deep hole`, `report holes`, `report niemeier`, `report hole census`, `report covering radius`, `report voronoi`) |
| `units` | every quantity states what it is twice, as a unit string and as EXT10 exponents; this parses the first and checks it against the second, and prices the SI reading of the steradian (aliases: `report unit parser`, `report steradian`, `report unit audit`, `report dimensional audit`) |
| `molecules` | the multi-carrier register: 51 molecules and ions held twice, as the faithful bundle of element carriers with multiplicities and as one composite summary carrier, with the losslessness of each checked rather than asserted (aliases: `report molecule`, `report formulae`, `report multi-carrier`, `report compounds`) |
| `chemistry coverage` | how sparse the element register is (1,257 of 1,652 cells filled) and the three honest repairs — derive, estimate with the error measured, cross-check without merging — each run and labelled with what it is (aliases: `report coverage`, `report element coverage`, `report sparsity`, `report covalent radius`) |
| `blueprint` | `glm_unification_blueprint.md` as a live claim ledger: each testable sentence recomputed against the package and given one of four verdicts — confirmed, refuted with what holds instead, unsupported by the measurement it names, or describing a subsystem that does not exist (aliases: `report unification blueprint`, `report claims`, `report claim ledger`, `report ledger`, `report audit`) |
| `reversible` | Part V measured at width 24: binary counting against the binary reflected Gray code, the Toffoli and Fredkin gates returning the carrier unchanged, and the kink invariant of a circular string — with the blueprint's "exactly half" reported as false and the sharp statement given instead (aliases: `report reversibility`, `report gray`, `report gray code`, `report toffoli`, `report fredkin`, `report solitons`, `report kinks`) |
| `mantissa` | where a binary64 float's precision goes, in an exact model in which no float is ever constructed: the bit spectrum of `1/p`, the period of the exact expansion as the multiplicative order of 2 mod p, and the structural loss — every stored orbit collapses while no exact orbit does (aliases: `report ptb`, `report aoo`, `report float`, `report floats`, `report metrology`, `report ieee754`, `report ieee-754`) |
| `engine` | Part III's thermo-dynamic carrier engine, assembled from parts the package already had — cam, accumulator, escapement, lattice snap, radiator, two fuels, turbocharger, gearbox — each stage measured, and the claimed precision leap checked against the three baselines it could mean (aliases: `report tdce`, `report carrier engine`, `report gearbox`, `report radiator`, `report turbocharger`, `report multi-fuel`) |
| `noise` | noise used as the computation rather than as a representation: a modulator tracking a two-tone signal inside the `1/N` law, a periodic input whose orbit closes exactly when its period sum is whole, the MASH 1-1 cascade whose error is a second difference and which beats a single loop by a factor growing with the window, the exact Walsh spectrum of an interacting pair, a subtractive-dither sweep trading the idle tone down for a stated bias, and the vector loop whose quantisation error returns through a rational matrix — the `1/(2N)` law at the identity, the dead zone when the feedback contracts, and exact equivariance under a permutation the matrix respects (aliases: `report wobble`, `report wiggle`, `report dither`, `report cascade`, `report noise lab`) |
| `signature` | the spectral signature of a constant, with the law beside every measured column: the modulator's stream is the mechanical word of its target, so the ones are exactly `⌊N t⌋`, the entropy is the binary entropy of the density, and the longest run sits on `1/min(t, 1−t)`; the oscillator table is the same function, and the entropy dip at resonance is local to the band (aliases: `report spectral`, `report sturmian`, `report resonance`, `report oscillator`, `report snr`) |
| `drift` | the prime-iteration stress test over 200 steps in three regimes — exact rationals, an exact binary64 model and binary64 truncated to a fixed number of displayed digits — showing the contractive rule safe in every regime and the accumulative rule amplifying the first rounding, with no float constructed anywhere (aliases: `report iteration drift`, `report prime drift`, `report divergence`) |
| `catalog` | `glm_study_findings_catalog.md` as a live claim ledger: 57 testable sentences recomputed against the package and given one of four verdicts — 32 confirmed, 14 refuted, 7 not reproduced, 4 describing a subsystem the package does not have (aliases: `report catalogue`, `report study findings`, `report external studies`) |
| `containers` | eight constants through three containers: the exact generator with the steps it needs to reach 10, 30 and 50 bits (decided by integer comparison, no logarithm and no float), the delta-sigma stream with the closed form beside every measured column, and the 24-dimensional projection tested against the convex hull of the Leech minimal vectors — inside by an explicit polytope, outside by a separating direction checked against all 196,560, so 7 of the 8 rows are settled by certificate and the eighth is left undetermined (aliases: `report container`, `report generators`, `report generators and containers`, `report hull census`, `report convergence`) |
| `companion` | the two companion preprints as a live claim ledger: 49 testable sentences recomputed and given the same four verdicts, and the definitions the summary omits — the projection, the indexing, the alphabet — supplied so that a verdict turns on a measurement rather than on a missing definition (aliases: `report companion studies`, `report companion study`, `report preprints`, `report iteration study`, `report lattice survey`) |
| `lattices` | the two rungs above the Leech lattice: the ladder in dimensions 8, 16, 24, 32 and 48 with each centre density recomputed from its minimum, the 32-dimensional Barnes–Wall lattice built by Construction D over `RM(1,5) ⊂ RM(3,5)` and its three nested resolutions, and the 48-dimensional extremal lattice from a self-dual ternary code and a neighbour step (aliases: `report lattice`, `report higher lattices`, `report barnes-wall`, `report 32`, `report 48`, `report extremal`, `report ladder`) |
| `shells` | delta–sigma with the alphabet widened to a Leech shell, so it no longer covers its own hull: the nearest and matched rules side by side, the shell's support function in closed form, a target tracked inside the hull and a target certified unreachable outside it, and the Gibbs-style rule realised deterministically by greedy error feedback (aliases: `report shell`, `report shell sigma`, `report gibbs`, `report leech noise`, `report leech sigma`, `report lattice alphabet`) |
| `llvq` | the Leech quantiser's 4,096-codeword scan replaced by the MOG's own class structure: the 16-entry column table, the 64 hexacode words and the 128 classes of 32 codewords, with the three conditions that characterise the code checked on all 4,096, the branch-and-bound search cost measured against the scan, and the agreement of the two decoders reported rather than assumed (aliases: `report llvq table`, `report lookup table`, `report quantiser`, `report class table`, `report hexacode`) |
| `harmony` | the harmonic register measured rather than described: the exact rational by which twelve-tone equal temperament misses each of the 28 intervals, the stack of fifths that is never a stack of octaves (searched here, proved for every `n` in `Harmony.lean`), Kendall's tau between Tenney height and Euler's gradus, and the catalogue's universality claim decided by decoding each interval's prime exponents to the nearest Leech point and scoring the result against the same distance taken before the decoder runs (aliases: `report harmonics`, `report music`, `report intervals`, `report tuning`, `report temperament`, `report consonance`) |
| `lean` | every declaration of the Lean development given a deterministic Leech address from 24 structural counts of its statement: how many read back exactly, how many addresses are distinct and whether the quantiser adds conflation of its own, and whether address distance tracks the file and the citation graph — scored against a SHA-256-of-the-name control and a seeded reshuffle of the same addresses (aliases: `report lean addresses`, `report lean address`, `report declarations`, `report address book`, `report addresses`) |
| `escalation` | the five-layer audit of `report information loss` re-run on every register carrier the package ships rather than on seven hand-picked ones — 1,040 in all — by grouping carriers under each layer's own zero-measure class key, which turns a quadratic scan and a quartic congruence search into a single pass and is itself checked against the layers' `perceive` and `measure` on 918 pairs: resolution 415 → 544 → 757 then flat, every boundary a refinement with zero violations, a resolution ceiling of 757 distinct carriers that puts 283 named entries in 104 within-register collision classes beyond every layer, and the rejected SI7-only reading conflating 11,176 pairs the substrate separates (aliases: `report scale`, `report registers`, `report ceiling`, `report resolution`, `report at scale`, `report escalation at scale`) |
| `directives` | the standing rules of `PROJECT_DIRECTIVES.md` parsed rather than paraphrased, each with the instrument it names and that instrument's current verdict (aliases: `report directive`, `report standing orders`, `report rules`, `report working practice`) |
| `measure` | the relative-measure study recomputed: 45 comparison classes over 11 quantities and 11 scales carrying 64 degree words, making all 12 of the lexicon's adjectives measurable; the scales checked against the lexicon on the 12 words the two registers share; the widening audit over 56 uses — the static reading resolves 12, the widened one 56, gaining 108 pairs with 0 refinement violations, with the rejected replacement's cost kept measurable by a witness set of 68 uses on which it violates refinement 66 times; the comparative audit over the 228 comparable pairs; and 27 of the 66 `related_to` triples converted to a measured relation, the other 39 declined with a reason (aliases: `report measure words`, `report measure view`, `report relative measure`, `report comparison classes`, `report comparison class`, `report scales`) |
| `recipe` | the recipe every register in this package was built from, run as an object: three domains built by hand in earlier rounds — comparison classes, harmonics and prices — written down as declarative descriptions, and one generic path from each description to the carrier encoding, the layer chain, the widening audit, the query surface and the refusal boundary. 72 coordinates, of which 66 are shared primitives and 6 judgements the domain states for itself, and the test of the whole thing: each register deleted and rebuilt from its description alone, 94 of 94 carriers identical coordinate by coordinate with every measured figure unchanged (aliases: `report recipes`, `report descriptions`, `report domain descriptions`, `report regeneration`, `report generic path`) |
| `pipeline` | the stage each piece of work has reached — studied, implemented, wired, tested, formalised, verified — read off the tree at call time rather than claimed in prose, so a row cannot report a stage it has not reached (aliases: `report stages`, `report study pipeline`, `report readiness`, `report board`) |

## The session API

```python
from glm_universal.runtime import GeometricSession

sess = GeometricSession()
sol = sess.ask("nearest 5 to pressure")     # parse, then solve
sol2 = sess.solve(sol.query, raw="nearest 3 to pressure")
```

`ask(text)` parses and delegates to `solve(query, raw=None)`.  `solve`
takes an already-parsed `Query`, which is what makes it possible to edit
a query object and re-run it without going back through the surface
string.  Both record an `InferenceRecord` in `sess.history`, whether or
not the query succeeded.

## A conversation over the session

```python
from glm_universal.runtime.conversation import Conversation

talk = Conversation()
talk.ask("describe carbon")
talk.ask("describe water")
talk.ask("field electronegativity_pauling of it")   # binds carbon, not water
```

`conversation.py` keeps an episodic register of turns in front of the
session so that a turn may refer back to an earlier one.  Exactly three
surface shapes are follow-ups — a pronoun (`describe it`), an end-flip
(`and the smallest?`) and a subject substitution (`and oxygen?`) — and
anything else is passed to `session.ask` untouched.

A candidate antecedent is **licensed** when the query it produces
actually solves, which is the only test applied: recency decides
between turns, newest first and answer side before subject side, and
licensing decides within one.  Where the deciding side offers two
licensed candidates the layer raises `FollowUpError` with reason
`ambiguous-antecedent` rather than choosing; the other two reasons are
`no-antecedent` and `unlicensed`.  Every rewritten query is answered by
the ordinary solver, so this layer can add an answer and never change
one.  `GLM.Conversation` is the proved half and
`../../../studies/CONVERSATION_STUDY.md` the measurement.

### The plan store

```python
from glm_universal.runtime.conversation import Conversation
from glm_universal.runtime.plan_store import PlanStore

talk = Conversation(store=PlanStore())
```

`plan_store.py` keeps a follow-up that has already been resolved under a
digest of **the whole conversation it was resolved in**, and a refusal is
stored exactly as an answer is, with its reason and its wording — which
is the case worth storing, because the follow-up that costs the most
licensing trials here is the one that refuses.  The digest addresses
integrity and never meaning (D3): it is taken through
`glm_universal.integrity`, and a hit is checked against the stored plan's
own prefix and text before it is used, so a collision costs a miss and
cannot cost an answer.  The control is the coarse key, which keys a plan
by its follow-up text alone and is kept so that what the exact key buys
is measured rather than asserted.  `GLM.PlanStore` is the proved half and
`../../../studies/SUPPLIED_PORTS_STUDY.md` §4 the measurement.

## The `GLM.py` CLI

The CLI entry point lives at the **repo root** (`../../GLM.py`), not in
this folder.  It is a thin shell over this package.  See the root
README's "Quick Start" for usage.

## Design invariants

- **No float anywhere**, in the runtime sources *or* in the scripts
  they generate.  `script_is_exact` checks generated source by AST.
- **No RNG and no wall clock.** A trace must be byte-identical between
  runs.
- **XOR only where it is addition.** On the F₂ module Λ/2Λ.
- **Failures are results.** An unsolved query returns a Solution with
  `ok=False` and is recorded in the history.
