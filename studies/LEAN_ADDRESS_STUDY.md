# Can the system speak Lean results?


## Tier 0 — the coarse read

**Question.** Can the system speak Lean results — is a declaration's Leech address unique, readable back, and meaningful?

**Verdict.** Yes to determinism, partly to meaning, and the two are not the same thing.

**Deciding figure.** Every declaration read back exactly from its address, and nearest-by-address shares a source file many times more often than chance.

**Recomputed by.** `glm_universal.reasoning.lean_address.lean_address_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

*Every declaration of the formal development is given a deterministic point of
the Leech lattice, and the three questions that decides are then measured
rather than asserted: is the address unique, can the declaration be read back
out of it, and does address distance track anything a reader would call
related. Two null models are run beside the real encoding — a SHA-256 control
that is deterministic and knows nothing, and a seeded reshuffle that keeps the
geometry and destroys the pairing — so that "the address means the
declaration" is a claim with a number attached rather than a metaphor.*

Code:
[`overlay/glm_universal/reasoning/lean_address.py`](../overlay/glm_universal/reasoning/lean_address.py),
[`overlay/glm_universal/integrity.py`](../overlay/glm_universal/integrity.py).
Query: `report lean`.
Command line: `python3 -m glm_universal.tools lean-address`.
Formal development:
[`RequestProject/GLM/Address.lean`](../RequestProject/GLM/Address.lean).
Tests: `overlay/glm_universal/tests/test_lean_address.py` (54 tests).

---

## 1. The question

The rest of this project addresses *physical quantities* by lattice point: a
quantity becomes a vector of exponents and units, the vector is scaled and sent
to its nearest Leech point, and "nearby address" is then a statement about the
quantities. The formal development under `RequestProject/GLM/` has meanwhile
grown to several hundred declarations, and the to-do list asked whether the
same machinery reaches them:

> Can a Lean result be held the way a physical quantity is held — as a point of
> Λ₂₄ — and does the geometry then say anything true about the development?

The honest answer this study measures is **yes to determinism, yes to
losslessness, and partly to meaning — and the three are different claims.**

* **Determinism** is free. Any function of the source text gives a
  reproducible address; the SHA-256 control below is perfectly deterministic
  and perfectly useless.
* **Losslessness** is a design question about the scale, and it is settled
  exactly: at scale 9 the feature vector is recovered from the address in every
  case in the development, with no coordinate error anywhere (§5).
* **Meaning** is the only interesting one, and it is a property of the *feature
  map*, not of the lattice. `Address.lean` proves this rather than arguing it:
  equal features force equal addresses, so the address cannot carry a single
  distinction the features have already thrown away.

An address is therefore a **resolution** in exactly the sense of
[`INFORMATION_LOSS_STUDY.md`](INFORMATION_LOSS_STUDY.md) and `Layers.lean`: it
shows whatever its coordinates carry and conflates everything else, and the
conflation classes are the boundary of the layer. This study measures where
that boundary falls.

No float is constructed anywhere below. Coordinates are integers, distances are
integers (squared Euclidean), and every rate is an exact `Fraction`.

---

## 2. The corpus: reading Lean without a compiler

The address book is built from a line reader over the `.lean` sources, not from
the compiler's environment. That is a deliberate cost — the reader can be
wrong, and it *was* wrong in two ways that this round found and fixed:

* **Block comments.** `/- … -/` regions were being scanned for declarations,
  so prose that happened to begin with the word `theorem` inside a file header
  was entering the corpus as a declaration.
* **Attributes.** A declaration written `@[simp] lemma dsBit_zero_eq_zero …`
  sits at column zero behind its attribute, and the reader was skipping the
  whole line. `GLM.Info.dsBit_zero_eq_zero` is now in the corpus, and a test
  pins it there.

The reader now tracks comment depth line by line (`_comment_depth_after`) and
looks past a leading attribute bracket. The corpus was 804 declarations across
35 files before that was fixed and has grown with the development ever since —
most of the growth being the retrieval round of
[`RETRIEVED_LEAN_STUDY.md`](RETRIEVED_LEAN_STUDY.md), which brought the MOG
cube, the Leech-lattice shortcut, the three generations of the paper's formal
companion, the electromagnetic calibration chain, the first-principles
sub-study, the projection sub-study, the graded cost model, spatial arithmetic
and the ARC-era reasoning loop back from the supplied archive. Its size now is
not written down here; it is emitted:

<!-- generated: lean-corpus -->
| kind | count |
|---|---|
| abbrev | 45 |
| def | 869 |
| example | 18 |
| inductive | 23 |
| instance | 27 |
| lemma | 112 |
| structure | 43 |
| theorem | 2,246 |
| **total** | **3,383** |

3,383 declarations across 119 files, the largest being `Gen3.lean` with 98.
<!-- end generated -->

The two `example` rows are `Denotation.lean`'s anonymous check that the physics
register does not dimension the word *gravity* and one retrieved with
`Gen3.lean`; the reader gives each a positional name (`_example_366`,
`_example_745`) exactly as it does an anonymous `instance` — of which the
retrieved files supply fourteen more — so an unnamed declaration is addressed
rather than silently dropped.

Two independent checks keep the reader honest.

* `parser_agreement()` reports every declaration parsed and **0 duplicates** —
  no name is claimed twice — and will compare against the compiler's own list
  of names when one is supplied.
* A new audit in `test_lean_address.py` scans **every** Python file of the
  package for tokens of the form `GLM.…` and requires each to resolve to a real
  declaration or a real namespace of the corpus. Nothing else in the project
  could check that a Lean name quoted in a docstring still exists. It found two
  stale citations on its first run — one theorem cited under a namespace it
  does not live in — both now corrected. Its blind spot is the *unqualified*
  citation, and this module's own header had two: it named the separation
  theorems `address_dist_le` and `ne_address_of_far`, which are in fact
  `GLM.Address.Quantiser.dist_le` and `GLM.Address.Quantiser.ne_of_far`. Both
  are now written in full, which puts them inside the audit's reach.

### The cache, and why it is digest-guarded

One exact nearest-point decode used to cost about a tenth of a second, and
since the class table of
[`LLVQ_TABLE_STUDY.md`](LLVQ_TABLE_STUDY.md) took over the hot path it costs a
few hundredths — still not something to do once per declaration per query, and
the address book is unchanged by the swap, declaration for declaration.

The address book is computed once and stored
in `reasoning/_data/lean_addresses.json` **next to the SHA-256 digest of the
Lean tree it was computed from**. Every read recomputes that digest and
compares. If one byte of one `.lean` file changes, the digest changes and the
report says `stale` rather than answering from a book that no longer describes
the sources. That is the sign-off discipline of `glm_universal.signoff` applied
to a derived artefact: *unchanged input plus recorded digest is a licence to
reuse; anything else is recomputed.*

---

## 3. The feature map, and what is deliberately absent

A declaration is reduced to 24 non-negative integers, each capped at 12 so that
no single declaration can dominate the geometry. Only the **statement**
supplies the syntactic counts — a proof is a route to a result, not the result,
and two proofs of one theorem should land on one address.

| # | coordinate | what it counts |
|---|---|---|
| 1–2 | `forall`, `exists` | quantifiers `∀`, `∃` |
| 3–7 | `implication`, `iff`, `conjunction`, `disjunction`, `negation` | `→`, `↔`, `∧`, `∨`, `¬`/`≠` |
| 8–11 | `equality`, `order`, `divisibility`, `big_operator` | genuine `=` signs, `≤ ≥ < >`, `∣`/`%`, `∑`/`∏` |
| 12–13 | `numeral`, `binder` | literals, opening parentheses |
| 14–19 | `nat`, `int`, `rat_real`, `fin`, `collection`, `prop_bool` | which carrier types the statement names |
| 20 | `statement_size` | words of the statement, in blocks of four |
| 21–22 | `cites`, `cited_by` | edges of the development's own citation graph |
| 23 | `namespace_depth` | dots in the namespace, plus one |
| 24 | `kind` | theorem / lemma / def / abbrev / structure / inductive / instance |

Note what is **not** there: the name, the file, the namespace *string*. So
"declarations from one file land near each other" is a prediction the encoding
can fail, and §7 is where it is scored. The two citation coordinates are the
only ones that see the development as a whole; the rest are local to one
statement.

Equality is counted carefully — `_statement_equalities` skips the `=` of `:=`,
`<=`, `>=`, `!=` and `=>` — and the order coordinate subtracts the arrows it
would otherwise double-count. These are the sort of details that decide whether
a "structural" encoding is structure or noise.

---

## 4. The scale: why 9, and not the obvious 8

The feature vector is multiplied by `SCALE` before decoding. Two conditions
pull in opposite directions, and `scale_sweep()` measures both on the first 60
declarations in source order rather than asserting either:

<!-- generated: lean-scale -->
| scale | read back exactly | moved by the decoder | worst residual | verdict |
|---|---|---|---|---|
| 4 | 30 / 60 | 30 | — | **lossy** |
| 6 | 60 / 60 | 60 | 2 | lossless, non-degenerate |
| 8 | 60 / 60 | 0 | 0 | **degenerate** |
| **9** | **60 / 60** | **60** | **2** | **lossless, non-degenerate** |
| 12 | 60 / 60 | 30 | 4 | lossless, partly degenerate |
| 16 | 60 / 60 | 0 | 0 | **degenerate** |

On the first 60 declarations in source order, decoding being the expensive step.  The chosen scale is 9.
<!-- end generated -->

The two failures are different in kind.

**Lossy, below 8.** The covering radius of the lattice in this integer model is
4, so quantising moves no coordinate by more than 4. A scale above twice the
radius keeps every coordinate strictly inside half a step, and then the feature
vector is recoverable; below that it is not, and at scale 4 more than two fifths
of the sample cannot be read back.

**Degenerate, at 8 and 16.** `8ℤ²⁴` is *contained* in the Leech lattice —
proved in `Address.lean` as `eightZ_mem_leech`: the parity condition holds with
`m = 0`, the mod-4 support is the empty word which is a Golay codeword, and the
coordinate sum is a multiple of 8. Combined with `Quantiser.fixed` (a point
already in `L` is its own address) that says the decoder at scale 8 *returns its
input*. The "Leech address" would be the feature vector times 8 — a relabelled
cube, with the lattice doing no work whatever. The sweep sees exactly that:
0 points moved.

The degeneracy really is a property of 8 rather than of scaling in general:
`nineZ_not_mem_leech` shows `(9, 0, …, 0) ∉ Λ`, because 9 is odd and 0 is even,
so no single parity `m` covers both coordinates.

**Nine is the smallest scale that is both lossless and non-degenerate**, and
`readback_unique` is the theorem that licenses the first half: if two integer
feature vectors are both within `ρ` of the same address coordinatewise and the
scale exceeds `2ρ`, they are equal. Here `2 · 4 < 9`.

---

## 5. Read-back: the address *is* the feature vector

Reading an address back inverts the quantiser — divide by 9, round to the
nearest integer — and it succeeds exactly when the quantisation error stayed
below half a scale unit in every coordinate.

<!-- generated: lean-readback -->
|  | measured |
|---|---|
| declarations checked | 3,383 |
| read back exactly | **3,383 / 3,383** (rate 1) |
| coordinates checked | 81,192 |
| coordinate errors | **0** |
| moved by the decoder | 3,383 / 3,383 |
| worst observed residual | **3**, at `GLM.DeepHoleLadder.Reading.cumulative_ge_right` |
| half a scale step | `9/2` |
| covering radius | 4 |
| bound respected | yes |
<!-- end generated -->

The worst residual anywhere in the development is strictly below the half-step
of `9/2`. So the guarantee is not merely satisfied, it is satisfied with room:
the bound that makes read-back *provable* is the covering radius 4, and the
worst case actually observed is smaller than that.

This is what makes the sentence in §8 well defined rather than a guess. Under
scale 9 the encoding is a bijection onto its image, and "the address means the
declaration" is, at this point, a statement about the feature map alone.

---

## 6. Injectivity, and where the layer boundary falls

<!-- generated: lean-injectivity -->
| scheme | distinct addresses | distinct feature vectors | classes | declarations conflated | quantisation adds conflation? |
|---|---|---|---|---|---|
| `feature` | 3,002 / 3,383 | 3,002 | 263 | 644 | no |
| `hash_control` | **3,383 / 3,383** | 3,002 | 0 | 0 | — |
| `shuffled` | 3,002 / 3,383 | 3,002 | 263 | 644 | no |
<!-- end generated -->

Two things to read off this table.

**The conflation is the feature map's, not the lattice's.** The number of
distinct addresses equals the number of distinct feature vectors, exactly. The
quantiser adds nothing: every collision is a pair of declarations the 24 counts
genuinely cannot tell apart. That is `address_congr` observed rather than
proved, and `injective_features_of_injective_address` is the direction that
*is* proved — an injective address forces an injective feature map, never the
other way round.

**The control is injective and that means nothing.** SHA-256 of the name
separates every declaration, because a digest separates anything; §7 shows it
separates them into a cloud with no structure in it. Injectivity is cheap. It
is the wrong thing to optimise, and the control is in the report to make that
visible.

The classes are still small, and they are recognisably the *right* classes, in
the sense that a reader shown only the 24 counts would also fail to tell the
members apart:

<!-- generated: lean-classes -->
263 classes: 207 pairs, 27 triples, 15 classes of 4, 6 classes of 5, 5 classes of 6, 2 classes of 7, 1 class of 15.

The widest, written out, because the point they make can only be read from the names:

```
15  GLM.Calibration.dEnergy, GLM.Calibration.dLength, GLM.Calibration.dTime,
    GLM.DimensionCarrier.Dim, GLM.DimensionCarrier.energyDim,
    GLM.DimensionCarrier.mc4Shift, GLM.Foundations.Dim,
    GLM.Foundations.energyDim, GLM.Foundations.mc4Shift,
    GLM.Lightspeed.dEnergy, GLM.Lightspeed.dLength, GLM.Lightspeed.dMass,
    GLM.Lightspeed.dSpeed, GLM.Lightspeed.dTime, GLM.VOA.vac
7   GLM.Calibration.NA_pos, GLM.Calibration.cSI_pos,
    GLM.Calibration.hSI_pos, GLM.Lightspeed.NA_pos, GLM.Lightspeed.cSI_pos,
    GLM.Lightspeed.hSI_pos, GLM.Lightspeed.molarPlanck_pos
7   GLM.Conjugate.energyDim, GLM.DimensionCarrier.mc4Dim,
    GLM.Foundations.mc4Dim, GLM.Gen2.energy, GLM.GolayHex.w2,
    GLM.Heisenberg.V, GLM.Semantics.energyDim
6   GLM.Admission.ledger_refusals, GLM.Completion.ledger_coverage,
    GLM.Gen3.dimensionless_counts, GLM.GrayJump.d2_1000033_1000034,
    GLM.LatticeShortcut.d2_1000033_1000034,
    GLM.Vagueness.ledger_conjugate_conversions
6   GLM.Calibration.NA, GLM.Calibration.molarPlanck, GLM.Lightspeed.NA,
    GLM.Lightspeed.cSI, GLM.Lightspeed.hSI, GLM.Lightspeed.molarPlanck
6   GLM.Calibration.cellDuration_bounds, GLM.Calibration.tick_bounds,
    GLM.Calibration.workEnergy_bounds, GLM.Lightspeed.cellDuration_bounds,
    GLM.Lightspeed.tick_bounds, GLM.Lightspeed.workEnergy_bounds
```
<!-- end generated -->

The largest class is the sharpest statement of what the layer cannot see: it is
one dimension vector, written out in five different files — the calibration
chain, the dimension carrier, the conjugate register, the paper's `Foundations`,
the restored `Lightspeed` — plus the vacuum vector of the VOA. Sixteen
declarations, each a short definition of a tuple of exponents, and as *shapes*
they are the same declaration. The first class of seven makes the same point:
positivity facts about SI constants restated in two files. Several of the
classes of six are the calibration chain against its own restored copy — a
genuine duplication in the development, which the address layer notices and a
reader would not.

The second class of seven is a class of naming: one-line abbreviations for a
carrier or a named datum — a function on `Fin 24`, a Golay word, a hexacode
digit vector, an exponent tuple, a 24-coordinate carrier — which have, as *shapes*, nothing
to tell them apart. That is the expected behaviour of a conflation class under
a larger corpus and is worth stating plainly: a resolution's boundary widens
when more statements of the same shape arrive. So the boundary of this layer
is, almost exactly, "the same statement about a different member of the same
family", which is a fair description of what a 24-count structural summary
should be unable to see. What growth adds is a second kind of member: the same
statement in a different *file*, because a retrieved file and the file it was
retrieved beside often state the same definition. That is a fact about the
development, not about the encoding, and the address layer is the thing that
made it visible.

---

## 7. Does distance mean anything? Three schemes, two null models

The test: for each declaration, take its nearest neighbour by address and ask
whether that neighbour came from the same file, and whether the two cite one
another. Ties are broken by taking all of them, and the tie sizes are reported,
so a scheme cannot win by being vague.

The chance rate is not one over the number of files. It is computed in closed
form from the actual file sizes — the probability that a uniformly chosen other
declaration shares a file — and it appears as the *chance* row below.

The third table is on *all* pairs, not just nearest ones.

<!-- generated: lean-neighbours -->
| scheme | nearest shares a file | rate | mean tie size |
|---|---|---|---|
| `feature` | **672 / 3,383** | ≈ **19.86 %** | 1.67 |
| `hash_control` | 33 / 3,383 | ≈ 0.98 % | 1.00 |
| `shuffled` | 35 / 3,383 | ≈ 1.03 % | 1.67 |
| *chance* | — | ≈ 1.09 % | — |

| scheme | nearest is cited, either way | rate |
|---|---|---|
| `feature` | **120 / 3,383** | ≈ **3.55 %** |
| `hash_control` | 6 / 3,383 | ≈ 0.18 % |
| `shuffled` | 3 / 3,383 | ≈ 0.09 % |
| *chance* | — | ≈ 0.18 % |

| scheme | mean d² within a file | mean d² across files | ratio |
|---|---|---|---|
| `feature` | 5,805.3 | 6,717.1 | **0.864** |
| `hash_control` | 54,429.2 | 54,272.3 | 1.003 |
| `shuffled` | 6,706.7 | 6,707.2 | 1.000 |

Against closed-form chance the feature encoding runs 18.2× on the file test and 19.3× on the citation test, from an encoding that is never shown a file name.

Over 62,406 same-file pairs and 5,658,247 cross-file pairs.  The feature encoding beats the hash control: yes; beats the seeded reshuffle: yes; beats closed-form chance: yes.
<!-- end generated -->

The two controls do exactly what they are there for.

* **`hash_control`** is deterministic, stable and injective, and lands within a
  hair of chance on every measure, with a within-file mean distance slightly
  *above* the across-file one. This is what an address looks like when it
  carries no information about its subject. It is the empirical content
  of directive **D3** — *a digest addresses integrity, never meaning* — and the
  reason the project has moved all of its SHA-256 use into a single
  `integrity` module one level above the six core sub-packages, where a purity
  audit can enforce that the core never imports `hashlib` at all. The one
  digest that touches meaning in this repository is this control, and it is
  labelled as a control.
* **`shuffled`** is the stronger null. It is the *same multiset of feature
  addresses*, re-assigned by a seeded permutation, so it has precisely the same
  geometry — same distances available, same tie structure (its mean tie size is
  identical to `feature`'s), same collision classes — and only the pairing
  between address and declaration is destroyed. It lands at chance, and its
  within-file mean distance sits far closer to its across-file one than
  `feature`'s does — a residue of the fact that the shuffle keeps the multiset
  of addresses and so keeps the corpus's clustering, while losing the pairing
  that would make it mean anything. So the feature encoding's rate is not the
  lattice being clever with a lot of points; it is information the features
  supplied.

Verdict, as the report computes it: `feature` beats chance, beats the digest
control, and beats the shuffle, on both the file test and the citation test,
and the digest control is chance-like. The multiple over chance has held or
risen across every re-measurement on a growing corpus, which is the one thing a
file-proxy measurement could not have been arranged to do by growing: the
absolute rate stays flat while the chance rate falls, which is what a real
signal does when the population grows.

Two honest qualifications. First, a fifth is not nine tenths:
nearest-by-address is a weak retrieval signal, useful for "show me results
shaped like this one" and not for "find the lemma I need". Second, the file
test is a proxy — declarations in one file *are* usually about one thing, but
the encoding is being credited for a correlation, not for understanding.

**How the three tables are computed, and why they are no longer quadratic.**
Both measurements above are over pairs, and on a corpus of this size the
straightforward loops were the slowest thing the system did: answering
`report lean` took about 203 seconds, of which 69 went on the all-pairs means
and 133 on the nearest-neighbour search, and the evaluation's per-query ceiling
of 300 seconds was close enough that a busy machine crossed it. Neither loop
needs to be run.

* The all-pairs means are a closed form. For any finite set of points,
  `sum over i<j of |x_i - x_j|^2  =  n * sum_i |x_i|^2 - |sum_i x_i|^2` —
  Lagrange's identity, every term an integer. The same-file total is that
  identity applied file by file, the cross-file total is the difference, and
  the whole third table costs one pass over the declarations instead of one
  over their 5,720,653 pairs.
* The nearest-neighbour search is pruned rather than rearranged, because
  *which* declaration is nearest has no closed form. Two lower bounds do the
  work, both exact: the addresses are held in order of their most spread-out
  coordinate, so a scan outward from a declaration stops in a direction as soon
  as the gap in that coordinate alone exceeds the best distance found; and
  before the 24-coordinate distance is computed, the next three most spread-out
  coordinates bound it from below. A bound can only discard a candidate that
  the full distance would have discarded, so the minimum and the full set of
  ties are the ones brute force reports. Declarations that share an address are
  each other's nearest neighbours at distance zero, so the search runs over the
  3,002 distinct addresses and reads the collision classes off directly.

`report lean` now answers in about 77 seconds, and every number in the three
tables above is unchanged — which is the point of preferring an identity and an
exact bound to a tolerance. `test_lean_address.py` checks both routines
against brute force rather than against their previous output:
`nearest_points` against `nearest_points_exhaustive` on corpus addresses under
all three schemes, on a tie by construction, and on repeated points, and the
identity against the pairwise loop.

---

## 8. Speaking Lean back

`describe_address` reads the coordinates off as the sentence they came from.
This is what "the machine speaks Lean" amounts to here: not the proof, and not
the statement verbatim, but the shape of the statement and its place in the
development, recovered from 24 integers.

```
GLM.HigherLattices.BarnesWall.norm_dvd_eight      (HigherLattices.lean:198)
  "a theorem, stating a divisibility, over Z, Fin, citing 6 and cited by 0"
  |address|² = 20720,  read back exactly
  nearest:  GLM.TieBreak.sum_raise_mod_eight              d² = 1232
            GLM.Foundations.shift_sign_comm_off_diag      d² = 1488
            GLM.Foundations.shift_sign_anticomm           d² = 1904

GLM.Info.Layer.Visible.mono                       (Layers.lean:91)
  "a theorem, over Prop/Bool, citing 3 and cited by 1"
  |address|² = 4160,  read back exactly
  nearest:  GLM.Recipe.Spec.answer_of_mem                 d² = 256
            GLM.Golay.hdist_bitReverse                    d² = 320
            GLM.Info.Layer.cumulativeTower_zero           d² = 320

GLM.Address.address_congr                         (Address.lean:150)
  "a theorem, stating 2 equality/-ies, citing 5 and cited by 2"
  |address|² = 8944,  read back exactly
  nearest:  GLM.Conjugate.rel_injective                   d² = 384
            GLM.Shell.shSum_eq                            d² = 592
            GLM.Completion.estimated_of_empty             d² = 608

GLM.Info.glmChain_refines_of_le                   (LayerChain.lean:189)
  "a theorem, stating 1 order relation(s), over N, citing 5 and cited by 1"
  |address|² = 5312,  read back exactly
  nearest:  GLM.DeepHoleLadder.Reading.cumulative_ge_left d² = 128
            GLM.Address.conflates_refl                    d² = 256
            GLM.Info.namedLayer                           d² = 256
```

Two of the four moved this round, and in the way the encoding predicts they
should. On a corpus 52 declarations larger (3,135 → 3,187) the two lattice
results keep their addresses, their read-back sentences and their three nearest
neighbours at the same distances. The other two moved because their *citation*
coordinates moved, which is the encoding working rather than drifting:
`glmChain_refines_of_le` is now read as citing 5 rather than 4, so its address
grew from 4672 to 5312 and its neighbourhood re-sorted; `address_congr` keeps its
address exactly and admits one new neighbour, `GLM.Shell.shSum_eq` at d² = 592,
between the two it had. The examples are re-measured rather than re-picked, so
this is a property of the round and not of the choice.

The Barnes–Wall divisibility result is the stable one: it keeps its modular-sum
lemma from `TieBreak.lean` at d² = 1232, then the two `Foundations.lean`
statements at 1488 and 1904, unchanged, and its own file still supplies no
neighbour at all in the top three; its neighbourhood improved steadily as the
corpus grew (1952, then 1488, then 1232) and has now held for a round, which is
what a thin region looks like once statements of a shape it was short of have
arrived. `Visible.mono` keeps `Recipe.Spec.answer_of_mem` at 256 ahead of the
pair at 320, so `boundary_verdict` stays out of the top three. `address_congr`
keeps norm 8944 and its citation count of two, with two statements still
between it and the mode-algebra result it used to tie with:
`Conjugate.rel_injective` at 384 and `Completion.estimated_of_empty` at 608.
`glmChain_refines_of_le` did not move either (norm 4672, same sentence), and
its three-way tie at 256 is still led by
`DeepHoleLadder.Reading.cumulative_ge_left` at 192 — a statement of the same
`≤ ⇒ something` shape from the escalation file, which is a fourth file rather
than a fourth subject. The encoding reads the shape, not the subject.
A declaration far from everything gets a neighbour that means little, and the
distance says so; a declaration in a dense region gets neighbours that mean
something. The geometry reports its own confidence, and nothing in the pipeline
suppresses the first case to make the average look better.

---

## 9. What is proved, and what is only measured

`Address.lean` (`sorry`-free, standard axioms only) carries the part that is a
theorem. It is deliberately abstract: a `Quantiser X L ρ` is any map into `L`
that moves nothing further than `ρ` and never returns a point of `L` further
away than the nearest one, and everything below follows from those three
properties with no mention of which lattice is used.

| Lean name | what it says | what it licenses here |
|---|---|---|
| `Quantiser.fixed` | a point of `L` is its own address | §4: the scale-8 degeneracy |
| `Quantiser.dist_le` | `dist (Q x) (Q y) ≤ dist x y + 2ρ` | nearby features ⇒ nearby addresses |
| `Quantiser.ne_of_far` | `2ρ < dist x y ⇒ Q x ≠ Q y` | a distance bound is a separation certificate |
| `address_congr` | equal features ⇒ equal addresses | §6: the address cannot out-mean its features |
| `Conflates` (+ `refl`/`symm`/`trans`) | the induced equivalence | §6: the layer boundary, as a relation |
| `injective_features_of_injective_address` | injective address ⇒ injective features | §6: never the converse |
| `ne_of_address_ne` | distinct addresses certify distinct subjects | the usable half of injectivity |
| `readback_unique` | within `ρ` coordinatewise and `2ρ < scale` ⇒ equal | §5: read-back is well defined |
| `eightZ_mem_leech` | `8ℤ²⁴ ⊆ Λ` | §4: why not 8 |
| `nineZ_not_mem_leech` | `(9,0,…,0) ∉ Λ` | §4: the degeneracy is 8's, not scaling's |

Everything else in this document is a measurement, and no measurement is
written here by hand: every table above is a generated block, emitted from
`glm_universal.corpus.measurements` and rewritten by `python3 -m
glm_universal.corpus --write`. Those figures are properties of *this*
development at *this* commit, they move when the Lean sources move, and the
digest guard is what makes them say so instead of going quietly stale — a block
whose measurements were taken from an older tree prints that it is stale rather
than printing a number.

---

## 10. What this licenses, and what it does not

**It licenses:** holding a Lean result in the same space, the same metric and
the same decoder as a physical quantity, with no loss — the address is the
feature vector, provably and observably. It licenses reading a declaration back
out of its address as a sentence. It licenses treating address distance as a
weak, calibrated similarity signal, with two null models establishing what
"weak" means. And it licenses the general claim the project has been making
about layers: a resolution shows what its coordinates carry, its conflation
classes are its boundary, and both can be exhibited rather than argued about.

**It does not license:** calling the address a *meaning*. The feature map is 24
integer counts of surface syntax; it does not know what a theorem says, only
what shape it is. Two statements about different objects of the same family
share an address, and the study names them rather than hiding them. Nor does it
license retrieval: the same-file rate is far above chance and far below useful
— and
[`ADDRESS_RETRIEVAL_STUDY.md`](ADDRESS_RETRIEVAL_STUDY.md) has since made that
precise by putting the address book to work as an index and measuring it
against a plain lexical search, which beats it decisively.

**The load-bearing negative result** is the digest control. It is injective,
deterministic, stable across runs and machines, trivial to compute — every
property one might naively want from an addressing scheme — and it is
indistinguishable from chance on every measure that asks whether the address
knows anything. That is the whole content of directive D3, measured on every
declaration of the development, and it is why the project's SHA-256 use now
lives in one module that the core sub-packages are audited not to import.

---

## 11. Reproducing every number here

```bash
cd overlay

# the report, and the same thing as JSON
PYTHONPATH=. python3 -m glm_universal.tools lean-address
PYTHONPATH=. python3 -m glm_universal.tools lean-address --json

# one declaration, spoken
PYTHONPATH=. python3 -m glm_universal.tools lean-address \
    --speak GLM.Address.address_congr

# through the query surface, with column-3 verification
PYTHONPATH=. python3 GLM.py -q "report lean" --no-banner
PYTHONPATH=. python3 GLM.py -q "report lean" --verify-tct --no-banner

# the scale sweep of section 4
PYTHONPATH=. python3 -c "from glm_universal.reasoning import lean_address as la; \
    [print(r) for r in la.scale_sweep()['rows']]"

# rebuild the address book (slow: one exact decode per declaration)
PYTHONPATH=. python3 -m glm_universal.tools lean-address --write

# re-take the measurements this document's tables are emitted from,
# and rewrite every generated block in it
PYTHONPATH=. python3 -m glm_universal.corpus --remeasure
PYTHONPATH=. python3 -m glm_universal.corpus --write

# the tests
PYTHONPATH=. python3 -m unittest glm_universal.tests.test_lean_address
```

The Lean side:

```bash
lake build
```

`Address.lean` is `sorry`-free, and every theorem named in §9 depends only on
the standard axioms (`propext`, `Classical.choice`, `Quot.sound`).

If the address book reports `stale`, the Lean sources have changed since it was
written and every number above is out of date by exactly that much; `--write`
is the fix, and the report will not answer from the old book in the meantime.
