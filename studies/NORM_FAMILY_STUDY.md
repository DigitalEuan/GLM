# The norm family — the ladder re-indexed by minimum squared norm, and the rung that had to be retired

## Tier 0 — the coarse read

**Question.** Escalation reads a carrier at rung after rung until one rung resolves it, and what decides whether a rung can resolve a perturbed query is its minimum squared norm. Does indexing the rungs by that quantity — one rung at every power of two, generated rather than named — read more queries than the eleven named construction rungs, and does it still refuse rather than answer wrongly?

**Verdict.** The complete power-of-two family answers more queries than the named rungs and answers one of them wrongly, so the declared retirement rule retires the rung at fault, and the repaired ladder answers 467 of 568 with 0 wrong against 462 for the named construction rungs.

**Deciding figure.** <!--figure:normesc-correct-->467<!--/figure--> of <!--figure:normesc-queries-->568<!--/figure--> queries answered correctly with <!--figure:normesc-wrong-->0<!--/figure--> wrong, against <!--figure:normesc-named-correct-->462<!--/figure--> for the eleven named construction rungs and <!--figure:normesc-family-correct-->470<!--/figure--> with <!--figure:normesc-family-wrong-->1<!--/figure--> wrong for the unrepaired family.

**Recomputed by.** `glm_universal.reasoning.norm_escalation.measure`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

[`CONSTRUCTION_LADDER_STUDY.md`](CONSTRUCTION_LADDER_STUDY.md) built a ladder
out of the constructions somebody had written down: `Z`, `D`, `A`, `B`, `C`,
and six scalings of them. That list is a list of *objects*. This round
re-indexes it by the *quantity the escalation actually uses* — the minimum
squared norm, which is what decides how large a perturbation a rung can absorb
— and asks for one rung at every power of two.

§1 is the arithmetic that makes the family possible and forces its shape. §2
is the family, generated. §3 is the tower, and what is proved about it in Lean.
§4 is the escalation measurement re-taken over the new rungs, including the
rung that had to be retired and why. §5 is the sweep that locates the breaking
point. §6 is what is left.

Everything is exact: integers and `Fraction`s, no float on any decision path,
and every table below is emitted by the code that measures it.

## 1. Why a power-of-two family needs two constructions

One fact decides the shape of the whole family:

> **Doubling a lattice multiplies every squared norm by four.**

So a single construction, scaled by powers of two, visits the norms
`m, 4m, 16m, …` — one residue class of the powers of two, and never the ones
between. `2ᵏZ²⁴` gives `1, 4, 16, 64, …`; `2ᵏD₂₄` gives `2, 8, 32, 128, …`;
`2ᵏA` gives `16, 64, 256, …`. A family with a rung at *every* power of two can
only be built by interleaving constructions with scalings, and a list that
leaves the interleaving out has a gap in it whatever it is called.

The same three facts are checked for each base rather than asserted:

<!-- generated: normfamily-scaling -->
| doubling | minimum norm | covolume | kissing number |
|---|---|---|---|
| `Z` → `2Z` | 1 → 4 | 2^0 → 2^24 | 48 → 48 |
| `D` → `2D` | 2 → 8 | 2^1 → 2^25 | 1,104 → 1,104 |
| `A` → `2A` | 16 → 64 | 2^36 → 2^60 | 48 → 48 |
| `B` → `2B` | 32 → 128 | 2^37 → 2^61 | 98,256 → 98,256 |
| `C` → `2C` | 32 → 128 | 2^36 → 2^60 | 196,560 → 196,560 |

Norm × 4 in every case = `True`; covolume × 2^24 = `True`; kissing number unchanged = `True`.  A single construction scaled by powers of two visits the norms m, 4m, 16m, ... -- one residue class of the powers of two -- so a complete power-of-two family needs the Z/D/A-type rungs interleaved with the scalings.  The same arithmetic is proved in Lean as `GLM.NormFamily.dbl_normSq, GLM.NormFamily.scaled_normSq`.
<!-- end generated -->

## 2. The family, generated

Every rung below is generated on demand from its base and its exponent:
`glm_universal.substrate.construction_ladder.rung_spec` parses a key like `8C`
into `(C, 3)` and builds the specification; `in_rung` tests membership by
undoing the scaling; `theta_series` re-indexes the base rung's series;
`contains` composes the containment from a handful of relative rules. Nothing
in the table is stored, and each rung's declared minimum norm and kissing
number is *checked* against its own generated theta series rather than printed
beside it.

<!-- generated: normfamily-rungs -->
| min. norm | rungs generated at it | densest | its kissing number | its covolume | chain rung |
|---|---|---|---|---|---|
| 1 | `Z` | `Z` | 48 | 2^0 | `Z` |
| 2 | `D` | `D` | 1,104 | 2^1 | `D` |
| 4 | `A/2`, `2Z` | `A/2` | 48 | 2^12 | `A/2` |
| 8 | `2D` | `2D` | 1,104 | 2^25 | `2D` |
| 16 | `A`, `4Z` | `A` | 48 | 2^36 | `A` |
| 32 | `C`, `B`, `4D` | `C` | 196,560 | 2^36 | `B` |
| 64 | `2A`, `8Z` | `2A` | 48 | 2^60 | `2A` |
| 128 | `2C`, `2B`, `8D` | `2C` | 196,560 | 2^60 | `2B` |
| 256 | `4A`, `16Z` | `4A` | 48 | 2^84 | `4A` |
| 512 | `4C`, `4B`, `16D` | `4C` | 196,560 | 2^84 | `4B` |
| 1,024 | `8A`, `32Z` | `8A` | 48 | 2^108 | `8A` |
| 2,048 | `8C`, `8B`, `32D` | `8C` | 196,560 | 2^108 | `8B` |

25 rungs are generated in all, and every one of the 12 powers of two from 1 to 2,048 carries at least one: gaps = `[]`, complete = `True`.  Each rung's declared minimum norm and kissing number is checked against its own generated theta series rather than printed beside it — all agree = `True`.
<!-- end generated -->

Two things in that table are worth reading twice. The norms `4`, `16`, `32`,
`128`, `512` and `2,048` carry more than one rung, and the densest is not
always the one the named ladder used — at norm 32 it is the Leech lattice, at
norm 4 it is the unscaled Golay lift rather than `2ℤ²⁴`. And the rung that
fills a norm is not free: a rung at norm 256 is what breaks the safety property
in §4, and it is in the family because the family is complete, not because it
earns its place. <!--figure:normfamily-rung-count-->25<!--/figure--> rungs are
generated in all, over <!--figure:normfamily-norms-->12<!--/figure--> powers of
two.

## 3. The tower, and what is proved

The densest rung at each norm is **not** a containment chain: `C` and `A` are
incomparable, which is the diamond `GLM.ConstructionLadder.ladder_not_chain`
proves with two explicit witnesses. Taking Construction `B` instead of the
Leech lattice at the norms they share gives a family that *is* a chain, one
rung per power of two, and every step of it is derived and then tried on
generated points of the coarser rung:

<!-- generated: normfamily-chain -->
| step | norms | derived | points tried / missed | holds |
|---|---|---|---|---|
| `D` ⊆ `Z` | 2 ⊂ 1 | `True` | 5 / 0 | `True` |
| `A/2` ⊆ `D` | 4 ⊂ 2 | `True` | 12 / 0 | `True` |
| `2D` ⊆ `A/2` | 8 ⊂ 4 | `True` | 5 / 0 | `True` |
| `A` ⊆ `2D` | 16 ⊂ 8 | `True` | 12 / 0 | `True` |
| `B` ⊆ `A` | 32 ⊂ 16 | `True` | 11 / 0 | `True` |
| `2A` ⊆ `B` | 64 ⊂ 32 | `True` | 12 / 0 | `True` |
| `2B` ⊆ `2A` | 128 ⊂ 64 | `True` | 11 / 0 | `True` |
| `4A` ⊆ `2B` | 256 ⊂ 128 | `True` | 12 / 0 | `True` |
| `4B` ⊆ `4A` | 512 ⊂ 256 | `True` | 11 / 0 | `True` |
| `8A` ⊆ `4B` | 1,024 ⊂ 512 | `True` | 12 / 0 | `True` |
| `8B` ⊆ `8A` | 2,048 ⊂ 1,024 | `True` | 11 / 0 | `True` |

The chain is 12 rungs — `8B` ⊂ `8A` ⊂ `4B` ⊂ `4A` ⊂ `2B` ⊂ `2A` ⊂ `B` ⊂ `A` ⊂ `2D` ⊂ `A/2` ⊂ `D` ⊂ `Z` — and every step holds = `True`.  The Lean proofs are `GLM.NormFamily.chain_step_A, GLM.NormFamily.chain_step_B, GLM.NormFamily.norm_family_chain, GLM.NormFamily.family_tower`.
<!-- end generated -->

`RequestProject/GLM/NormFamily.lean`, 0 `sorry`, is the formal half:

* `scaled_witness`, `scaled_normSq`, `dbl_normSq` — a vector of `2ᵏL` is `2ᵏ`
  times a vector of `L`, so its squared norm is `4ᵏ` times that one's. This is
  §1 as a theorem;
* `scaled_min_norm` — a lattice of minimum squared norm `m` scales to one of
  minimum squared norm `4ᵏm`, which is what licenses indexing the family by
  minimum norm at all;
* `dbl_isD_isG` (`2D₂₄ ⊆ G`), `dbl_isA_isB` (`2A ⊆ B`) and `dbl_isC_isA`
  (`2Λ₂₄ ⊆ A`) — the three containments the re-indexed family needs and the
  earlier files did not have;
* `chain_step_A` and `chain_step_B` — those steps at *every* scale, so the
  tower is infinite rather than as long as somebody wrote down;
* `family_tower` — the whole ladder in one statement: `ℤ²⁴ ⊃ D₂₄ ⊃ G ⊃ 2D₂₄ ⊃
  A ⊃ B ⊃ 2A ⊃ 2B ⊃ 4A ⊃ …`, with one rung at every power-of-two minimum norm.

The Python side does not take any of that on trust: `contains` *derives* each
containment from the relative rules and `family_containment_spot_check` then
tries every derived containment on generated points of the lower rung, so a
wrong derivation is caught rather than believed.

## 4. The escalation, re-taken

**Unchanged from the previous round, deliberately:** the same 142 carriers (the
first 24 named objects of each of six registers), the same four declared
perturbations (8 coordinates by `1/8`, `1/4`, `1/2`, `3/4`, with the support and
signs read off a Golay codeword), the same stopping rule (stop at the first rung
whose cell holds exactly one carrier), the same three visiting orders, and the
same controls (each rung alone, and an oracle allowed to pick the rung after the
fact). `142 × 4 = 568` queries.

**Changed:** the rungs. The declared ladder is the densest rung at each
power-of-two norm from 1 to 2,048, coarsest first, and each one's quantiser is
the base quantiser applied to the shrunk vector — no new decoder was written
for any of them.

<!-- generated: normesc-measurement -->
| reading | rungs | correct | wrong | refused | refuses rather than answers wrongly | oracle | matches oracle |
|---|---|---|---|---|---|---|---|
| the full power-of-two family | 12 | 470 | 1 | 97 | `NO` | 470 | `True` |
| the family after the declared retirement rule | 10 | 467 | 0 | 101 | `yes` | 467 | `True` |
| the same family through `B` (a chain) | 12 | 469 | 1 | 98 | `NO` | 469 | `True` |
| the eleven named construction rungs (the recorded before) | 11 | 462 | 0 | 106 | `yes` | 462 | `True` |

All three visiting orders return the same answers in every row — the rungs never name different carriers (`rungs_disagree = 0`) — so the order is a cost decision, which is `GLM.ConstructionLadder.firstNamed_order_independent`.  The best single rung of the repaired ladder is `4C` at 328 correct, so escalation is worth +139 queries over it.  The full family answers 470 — more than the repaired ladder — and is reported as a **failure** anyway, because 1 of those queries is answered wrongly.
<!-- end generated -->

**The failure, stated as a failure.** The complete family —
<!--figure:normesc-family-rungs-->12<!--/figure--> rungs, answering
<!--figure:normesc-family-correct-->470<!--/figure--> — answers more queries
than anything before it *and answers
<!--figure:normesc-family-wrong-->1<!--/figure--> of them wrongly*. Refusing rather than
answering wrongly is the property the escalation exists for, so a reading that
gains three queries and loses that property has not improved; it has changed
what it is. The repaired ladder pays for the property in refusals and states
the price: it refuses <!--figure:normesc-refused-->101<!--/figure--> of the
<!--figure:normesc-queries-->568<!--/figure--> queries, four more than the
unsafe family it replaces, and each of them is a query no rung of the ladder
answers at all. The rule that follows was declared before it was run, and it has two
clauses: it retires a rung that answers any query wrongly, and retires a rung that
answers nothing the rest of the ladder cannot while taking part in a
disagreement.

<!-- generated: normesc-audit -->
| rung | min. norm | correct | wrong | refused | only rung to answer it | disagreements |
|---|---|---|---|---|---|---|
| `8C` | 2,048 | 302 | 0 | 266 | 1 | 0 |
| `8A` | 1,024 | 286 | 0 | 282 | 0 | 0 |
| `4C` | 512 | 328 | 0 | 240 | 0 | 0 |
| `4A` | 256 | 326 | 1 | 241 | 3 | 0 |
| `2C` | 128 | 273 | 0 | 295 | 1 | 0 |
| `2A` | 64 | 283 | 0 | 285 | 0 | 0 |
| `C` | 32 | 205 | 0 | 363 | 3 | 0 |
| `A` | 16 | 196 | 0 | 372 | 1 | 0 |
| `2D` | 8 | 113 | 0 | 455 | 6 | 0 |
| `A/2` | 4 | 137 | 0 | 431 | 3 | 0 |
| `D` | 2 | 164 | 0 | 404 | 0 | 0 |
| `Z` | 1 | 194 | 0 | 374 | 3 | 0 |

**The retirement rule, declared before it was run:** retire a rung that answers any query wrongly, and retire a rung with unique_correct = 0 that takes part in a disagreement.

* round 1: `4A` retired — it answers 1 query wrongly, which is the one thing the escalation is supposed not to do; it uniquely answers 3, and that is the price of retiring it; replaced by `16Z`, the next rung the family generates at norm 256.
* round 2: `16Z` retired — it answers 4 queries wrongly, which is the one thing the escalation is supposed not to do; it uniquely answers 2, and that is the price of retiring it; dropped: the family has no other untried rung at norm 256.
* round 2: `D` retired — it answers no query the rest of the ladder cannot (unique_correct = 0) and takes part in 2 disagreement(s); dropped: the family has no other untried rung at norm 2.

After 2 round(s) the ladder is `8C` `8A` `4C` `2C` `2A` `C` `A` `2D` `A/2` `Z`, safe = `True`, with the norms `[2, 256]` left empty — the price of the rule, stated rather than hidden.
<!-- end generated -->

**What the rule cost, in full.** `4A` uniquely answered 3 queries and is gone;
the family's other rung at norm 256, `16Z`, answers 4 wrongly and is gone too,
so the repaired ladder has no rung at norm 256 at all. `D` was retired under the
second clause. The repaired ladder is
<!--figure:normesc-rungs-->10<!--/figure--> rungs with two norms empty, it
answers <!--figure:normesc-correct-->467<!--/figure--> of
<!--figure:normesc-queries-->568<!--/figure--> with
<!--figure:normesc-wrong-->0<!--/figure--> wrong, it matches the after-the-fact
oracle exactly, and no two of its rungs ever name different carriers. Against
the <!--figure:normesc-named-rungs-->11<!--/figure--> named construction rungs —
<!--figure:normesc-named-correct-->462<!--/figure--> correct, 0 wrong — it
answers five more queries with the safety property intact.

So the answer to the question the round asked has two parts, and they have to be
read separately. The re-indexed family does read more: every reading in the
table above beats the named rungs on raw count. But the complete family is not
safe, the rung at fault has to be retired, and what survives the retirement is a
smaller gain than the unrepaired count suggests. That is the honest success, and
the failure that preceded it is the more useful half of the result.

**The chain costs something too.** Reading the family through Construction `B`
instead of the Leech lattice makes it a containment tower, which is the version
Lean proves; it answers 469 with 1 wrong. So the tower is the better object and
the worse reading, and the honest statement is that the two are different
choices rather than one being the refinement of the other.

## 5. Where it breaks

The family is generated, so the question *how long is too long* is measured
rather than argued. Each length is the densest rung at each of the norms 1 to
`2^(n-1)`:

<!-- generated: normesc-sweep -->
| rungs | highest norm | correct | wrong | refused | rungs disagree | order-independent | refuses rather than answers wrongly |
|---|---|---|---|---|---|---|---|
| 6 | 32 | 356 | 0 | 212 | 0 | yes | yes |
| 7 | 64 | 423 | 0 | 145 | 0 | yes | yes |
| 8 | 128 | 437 | 0 | 131 | 0 | yes | yes |
| 9 | 256 | 462 | 1 | 105 | 0 | yes | **NO** |
| 10 | 512 | 466 | 1 | 101 | 0 | yes | **NO** |
| 11 | 1,024 | 469 | 1 | 98 | 0 | yes | **NO** |
| 12 | 2,048 | 470 | 1 | 97 | 0 | yes | **NO** |
| 13 | 4,096 | 470 | 1 | 97 | 0 | yes | **NO** |
| 14 | 8,192 | 470 | 1 | 97 | 0 | yes | **NO** |

The longest safe family on this sample is **8 rungs** at 437 correct; the first unsafe one is **9 rungs**.  The break is not the order-independence theorem failing — the rungs still agree — it is a rung whose cell holds exactly one carrier and the wrong one, so the ladder answers where it should have refused.
<!-- end generated -->

The longest safe length is
<!--figure:normesc-longest-safe-->8<!--/figure--> rungs and the first unsafe one
is <!--figure:normesc-first-broken-->9<!--/figure-->.

Two things are worth separating here, because the previous round's break and
this one's are not the same failure. In
[`CONSTRUCTION_LADDER_STUDY.md`](CONSTRUCTION_LADDER_STUDY.md) §4a the fifteen-
rung ladder broke by making two rungs *disagree*: the hypothesis of
`GLM.ConstructionLadder.firstNamed_order_independent` failed and the answer
became order-dependent. Here the rungs never disagree — order-independence holds
at every length — and the break is simpler and worse: a coarse rung's cell holds
exactly one carrier and it is the wrong one, so the ladder answers confidently
where it should have refused. Order-independence is not safety, and this sweep
is the measurement that separates them.

## 6. Limits, and what the next round should take

**Limits of what is claimed.** The figures are about this sample (142 carriers
of six registers) and this sweep (four declared perturbations). The retirement
rule is a rule about *this* measurement: a rung retired on this sample might
earn its place on another, and the repaired ladder is therefore a measured
artefact rather than a mathematical object. The family itself is not: its
completeness, its containments and its scaling arithmetic hold for every
sample.

**Named for the next round.**

1. *Fill norm 256 properly.* Both rungs the family generates there are unsafe
   on this sample. Construction `A` over a **shortened** code, or the `D₄`/`E₈`
   layers below `D₂₄`, would give rungs the scaling does not generate, and one
   of them may sit at 256 safely.
2. *Make the retirement rule cheaper.* It currently costs a full re-measurement
   per round. A rung's wrong answers are decided by its cell occupancy, which
   is computable from the index alone.
3. *Carry the repair into the operations.* §4's repair is about retrieval;
   [`OPERATION_ESCALATION_STUDY.md`](OPERATION_ESCALATION_STUDY.md) measures six
   other operations over the *unrepaired* family, and one of them is unsafe
   there too.

**How to re-run any of this.**

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools normladder          # the stored measurement
PYTHONPATH=. python3 -m glm_universal.tools normladder --write  # re-take it (about half an hour)
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_norm_family.py -q
cd .. && lake build RequestProject.GLM.NormFamily
```
