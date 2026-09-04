# Can the system speak Lean results?

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
  one of 2,826 cases, with 0 coordinate errors out of 67,824.
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
looks past a leading attribute bracket. The corpus moved from 804 to 849
declarations across 35 files when that was fixed, stood at 1,270 across 48
files for several rounds, reached **2,118** across **73** after the retrieval
round, stood at **2,764** across **95** once the second pass and the restored
files had joined it, and stands at **2,826** declarations across **97** files
now that `Retrieval.lean` (38) and `Controller.lean` (24) have been added — the
round documented in
[`RETRIEVED_LEAN_STUDY.md`](RETRIEVED_LEAN_STUDY.md) has brought **848**
declarations in 25 files back from the supplied archive: the MOG cube
(`Cube/Surface.lean` 82, `Cube/Stabiliser.lean` 48, `Cube/Three.lean` 48,
`Cube/Tax.lean` 32, `Cube/HexTiles.lean` 22), the Leech-lattice shortcut
(`Shortcut/` — 128 across eight files), the three generations of the paper's
formal companion (`Gen3.lean` 98, `Gen2.lean` 69, `Foundations.lean` 41), the
electromagnetic calibration chain (`Calibration.lean` 70,
`AlignmentPoints.lean` 17), the first-principles sub-study (`FitCapacity.lean`
54, `Packing.lean` 32, `Triad.lean` 4), the projection sub-study
(`SeedLayers.lean` 41), the graded cost model (`StepCost.lean` 28), spatial
arithmetic (`SpatialArithmetic.lean` 22) and the ARC-era reasoning loop
(`ReasoningLoop.lean` 12).

| kind | count |
|---|---|
| theorem | 1,871 |
| def | 740 |
| lemma | 110 |
| abbrev | 38 |
| structure | 27 |
| instance | 24 |
| inductive | 14 |
| example | 2 |
| **total** | **2,826** |

The two `example` rows are `Denotation.lean`'s anonymous check that the physics
register does not dimension the word *gravity* and one retrieved with
`Gen3.lean`; the reader gives each a positional name (`_example_366`,
`_example_745`) exactly as it does an anonymous `instance` — of which the
retrieved files supply fourteen more — so an unnamed declaration is addressed
rather than silently dropped.

Largest single file: `Gen3.lean`, 98 declarations.

Two independent checks keep the reader honest.

* `parser_agreement()` reports **2,826 parsed, 0 duplicates** — no name is
  claimed twice — and will compare against the compiler's own list of names
  when one is supplied.
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
few hundredths — still not something to do 2,826 times per query, and the
address book is unchanged by the swap, declaration for declaration.

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

| scale | read back exactly | moved by the decoder | worst residual | verdict |
|---|---|---|---|---|
| 4 | 34 / 60 | 26 | — | **lossy** |
| 6 | 60 / 60 | 60 | 2 | lossless, non-degenerate |
| 8 | 60 / 60 | **0** | 0 | **degenerate** |
| **9** | **60 / 60** | **60** | **2** | **lossless, non-degenerate** |
| 12 | 60 / 60 | 26 | 4 | lossless, partly degenerate |
| 16 | 60 / 60 | **0** | 0 | **degenerate** |

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

| | measured |
|---|---|
| declarations checked | 2826 |
| read back exactly | **2,826 / 2,826** (rate 1) |
| coordinates checked | 67,824 |
| coordinate errors | **0** |
| moved by the decoder | 2,826 / 2,826 |
| worst observed residual | **3**, at `GLM.Gen2.Meaning.pseudoscalar_parity_ne_zero` |
| half a scale step | `9/2` |
| covering radius | 4 |

The worst residual anywhere in the development is 3, against a half-step of
`9/2 = 4.5`. So the guarantee is not merely satisfied, it is satisfied with
room: the bound that makes read-back *provable* is 4, and the worst case
actually observed is 3.

This is what makes the sentence in §8 well defined rather than a guess. Under
scale 9 the encoding is a bijection onto its image, and "the address means the
declaration" is, at this point, a statement about the feature map alone.

---

## 6. Injectivity, and where the layer boundary falls

| scheme | distinct addresses | distinct feature vectors | classes | declarations conflated | quantisation adds conflation? |
|---|---|---|---|---|---|
| `feature` | 2,486 / 2,826 | 2,486 | 230 | 570 | **no** |
| `hash_control` | **2,826 / 2,826** | 2,486 | 0 | 0 | — |
| `shuffled` | 2,486 / 2,826 | 2,486 | 230 | 570 | no |

Two things to read off this table.

**The conflation is the feature map's, not the lattice's.** The number of
distinct addresses equals the number of distinct feature vectors, exactly. The
quantiser adds nothing: every collision is a pair of declarations the 24 counts
genuinely cannot tell apart. That is `address_congr` observed rather than
proved, and `injective_features_of_injective_address` is the direction that
*is* proved — an injective address forces an injective feature map, never the
other way round.

**The control is injective and that means nothing.** SHA-256 of the name
separates all 2,826, because a digest separates anything; §7 shows it separates
them into a cloud with no structure in it. Injectivity is cheap. It is the
wrong thing to optimise, and the control is in the report to make that visible.

The 230 classes are still small — 175 pairs, 30 triples, 15 classes of four,
three of five, three of six, two of seven, one of eight and one of fifteen —
and they are recognisably the *right* classes, in the sense that a reader shown
only the 24 counts would also fail to tell the members apart:

```
15 GLM.Calibration.dEnergy, GLM.Calibration.dLength, GLM.Calibration.dTime,
   GLM.DimensionCarrier.Dim, GLM.DimensionCarrier.energyDim,
   GLM.DimensionCarrier.mc4Shift, GLM.Foundations.Dim,
   GLM.Foundations.energyDim, GLM.Foundations.mc4Shift,
   GLM.Lightspeed.dEnergy, GLM.Lightspeed.dLength, GLM.Lightspeed.dMass,
   GLM.Lightspeed.dSpeed, GLM.Lightspeed.dTime, GLM.VOA.vac
8  GLM.Facets.Carrier, GLM.Gen2.Exps, GLM.Gen2.mass, GLM.Gen2.speed,
   GLM.Golay24.Word, GLM.GolayHex.w, GLM.Info.Carrier24, GLM.Info.tea
7  GLM.Calibration.NA_pos, GLM.Calibration.cSI_pos, GLM.Calibration.hSI_pos,
   GLM.Lightspeed.NA_pos, GLM.Lightspeed.cSI_pos, GLM.Lightspeed.hSI_pos,
   GLM.Lightspeed.molarPlanck_pos
7  GLM.DimensionCarrier.mc4Dim, GLM.Foundations.mc4Dim, GLM.Gen2.energy,
   GLM.Golay24.Syn, GLM.GolayHex.w2, GLM.Heisenberg.V,
   GLM.Semantics.energyDim
6  GLM.Calibration.NA, GLM.Calibration.molarPlanck, GLM.Lightspeed.NA,
   GLM.Lightspeed.cSI, GLM.Lightspeed.hSI, GLM.Lightspeed.molarPlanck
6  GLM.Calibration.cellDuration_bounds, GLM.Calibration.tick_bounds,
   GLM.Calibration.workEnergy_bounds, GLM.Lightspeed.cellDuration_bounds,
   GLM.Lightspeed.tick_bounds, GLM.Lightspeed.workEnergy_bounds
```

The largest class is the sharpest statement of what the layer cannot see: it is
one dimension vector, written out in four different files — the calibration
chain, the dimension carrier, the paper's `Foundations`, the restored
`Lightspeed` — plus the vacuum vector of the VOA. Fifteen declarations, each a
short definition of a tuple of exponents, and as *shapes* they are the same
declaration. The two classes of seven make the same point twice over: three
positivity facts about SI constants restated in two files, and a family of
one-line carrier definitions. The two classes of six are the calibration chain
against its own restored copy — a genuine duplication in the development, which
the address layer notices and a reader would not.

The second line is a class of naming, and it has stayed at eight members across
two re-measurements: one-line abbreviations for a carrier or a named datum — a
function on `Fin 24`, a Golay word, a hexacode digit vector, an exponent tuple,
a 24-coordinate carrier — which have, as *shapes*, nothing to tell them apart.
That is the expected behaviour of a conflation class under a larger corpus and
is worth stating plainly: a resolution's boundary widens when more statements of
the same shape arrive. So the boundary of this layer is, almost exactly, "the
same statement about a different member of the same family", which is a fair
description of what a 24-count structural summary should be unable to see. What
the growth from 119 classes to 230 adds is a second kind of member: the same
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

The chance rate is not `1/97`. It is computed from the actual file sizes — the
probability that a uniformly chosen other declaration shares a file — which
comes to `54247/3991725 ≈ 1.36%`.

| scheme | nearest shares a file | rate | mean tie size |
|---|---|---|---|
| `feature` | **578 / 2,826** | ≈ **20.5 %** | 1.70 |
| `hash_control` | 35 / 2,826 | ≈ 1.24 % | 1.00 |
| `shuffled` | 37 / 2,826 | ≈ 1.31 % | 1.70 |
| *chance* | — | ≈ 1.36 % | — |

| scheme | nearest is cited, either way | rate |
|---|---|---|
| `feature` | **108 / 2,826** | ≈ 3.82 % |
| `hash_control` | 8 / 2,826 | ≈ 0.28 % |
| `shuffled` | 3 / 2,826 | ≈ 0.11 % |
| *chance* | — | ≈ 0.21 % |

And on all pairs, not just nearest ones — 54,247 same-file pairs against
3,937,478 cross-file ones:

| scheme | mean d² within a file | mean d² across files | ratio |
|---|---|---|---|
| `feature` | 5,711.6 | 6,586.2 | **0.867** |
| `hash_control` | 54,471.8 | 54,294.3 | 1.003 |
| `shuffled` | 6,452.2 | 6,576.0 | 0.981 |

The two controls do exactly what they are there for.

* **`hash_control`** is deterministic, stable and injective, and lands within a
  hair of chance on every measure: 1.24 % against 1.36 %, and a within-file
  distance 0.3 % *above* the across-file one. This is what an address looks like
  when it carries no information about its subject. It is the empirical content
  of directive **D3** — *a digest addresses integrity, never meaning* — and the
  reason the project has moved all of its SHA-256 use into a single
  `integrity` module one level above the six core sub-packages, where a purity
  audit can enforce that the core never imports `hashlib` at all. The one
  digest that touches meaning in this repository is this control, and it is
  labelled as a control.
* **`shuffled`** is the stronger null. It is the *same multiset of feature
  addresses*, re-assigned by a seeded permutation, so it has precisely the same
  geometry — same distances available, same tie structure (mean tie size 1.70,
  identical to `feature`), same 230 collision classes — and only the pairing
  between address and declaration is destroyed. It lands at 1.31 %, just below
  chance, and its within-file mean distance is 1.9 % below the across-file one
  against `feature`'s 13.3 % below — a residue of the fact that the shuffle
  keeps the multiset of addresses and so keeps the corpus's clustering, while
  losing the pairing that would make it mean anything. So the 20.5 % is not the
  lattice being clever with a lot of points; it is information the features
  supplied.

Verdict, as the report computes it: `feature` beats chance, beats the digest
control, and beats the shuffle, on both the file test and the citation test.
The digest control is chance-like. Just over fifteen times chance on the file
test, and just under eighteen times chance on the citation test, from an
encoding that is never shown a file name. Both multiples have risen again on a
larger corpus — the file-test multiple has gone 13.2×, 14.5×, 15.0× over the
last three measurements — which is the one thing a file-proxy measurement could
not have been arranged to do by growing: the absolute rate is flat (24.3 %,
20.3 %, 20.5 %) while the chance rate keeps falling (1.84 %, 1.40 %, 1.36 %),
which is what a real signal does when the population grows.

Two honest qualifications. First, 20.5 % is not 90 %: nearest-by-address is a
weak retrieval signal, useful for "show me results shaped like this one" and
not for "find the lemma I need". Second, the file test is a proxy — declarations
in one file *are* usually about one thing, but the encoding is being credited
for a correlation, not for understanding.

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
            GLM.Foundations.shift_sign_comm_off_diag      d² = 1424
            GLM.Foundations.shift_sign_anticomm           d² = 1904

GLM.Info.Layer.Visible.mono                       (Layers.lean:91)
  "a theorem, over Prop/Bool, citing 3 and cited by 1"
  |address|² = 4160,  read back exactly
  nearest:  GLM.Golay.hdist_bitReverse                    d² = 320
            GLM.Info.Layer.boundary_verdict               d² = 320
            GLM.Info.Layer.cumulativeTower_zero           d² = 320

GLM.Address.address_congr                         (Address.lean:150)
  "a theorem, stating 2 equality/-ies, citing 5 and cited by 2"
  |address|² = 8944,  read back exactly
  nearest:  GLM.ModeAlgebra.definitionOk_is_a_function_of_dominant_role  d² = 608
            GLM.Shell.shSum_eq                            d² = 608
            GLM.Info.namedResolution_of_injective         d² = 704

GLM.Info.glmChain_refines_of_le                   (LayerChain.lean:189)
  "a theorem, stating 1 order relation(s), over N, citing 4 and cited by 1"
  |address|² = 4672,  read back exactly
  nearest:  GLM.CubeTax.xor_codeword_free                 d² = 256
            GLM.Facets.proj_add                           d² = 256
            GLM.Golay24.card_symmDiff_eq                  d² = 256
```

Two of the four moved again this round, and again neither moved because
anything about the declaration changed: two Lean files were added and the
ranking is over a larger population. That is what a *weak* similarity signal
does, and the examples are re-measured rather than re-picked.

The first two are the stable ones. `Visible.mono` keeps the same three
neighbours in the same tie at 320, two of them from its own `Layers.lean`. The
Barnes–Wall divisibility result keeps its modular-sum lemma from `TieBreak.lean`
at d² = 1232, nearly four times further than anything in the second example,
and its own file still supplies no neighbour at all in the top three; its
neighbourhood has improved steadily as the corpus grew (1952, then 1488, now
1232), which is what a thin region looks like when statements of a shape it was
short of arrive. The two that moved both moved because a *citation count*
changed, which is a coordinate: `address_congr` is now cited twice rather than
once — `Retrieval.lean` cites it — so its own address shifted, its old tie at
352/384 is gone, and the same mode-algebra result now sits at 608 beside a
shell identity with its own file's `conflates_symm` out of the top three.
`glmChain_refines_of_le` did not move at all (norm 4672, same sentence); its
old nearest neighbour `ds_refines_of_le` did, its own citation count having
risen, and at d² = 544 it is displaced by a three-way tie at 256 of statements
of the same `≤ ⇒ something` shape from three different files — the encoding
reads the shape, not the subject.
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

Everything else in this document is a measurement: 2,826, 2,486, 578, 35, 37,
108, 0 coordinate errors, worst residual 3. Those are properties of *this*
development at *this* commit, they move when the Lean sources move, and the
digest guard is what makes them say so instead of going quietly stale.

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
license retrieval: 20.5 % same-file is far above the 1.36 % chance rate and
far below useful — and
[`ADDRESS_RETRIEVAL_STUDY.md`](ADDRESS_RETRIEVAL_STUDY.md) has since made that
precise by putting the address book to work as an index and measuring it
against a plain lexical search, which beats it decisively.

**The load-bearing negative result** is the digest control. It is injective,
deterministic, stable across runs and machines, trivial to compute — every
property one might naively want from an addressing scheme — and it is
indistinguishable from chance on every measure that asks whether the address
knows anything. That is the whole content of directive D3, measured on 2,826
declarations, and it is why the project's SHA-256 use now lives in one module
that the core sub-packages are audited not to import.

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
