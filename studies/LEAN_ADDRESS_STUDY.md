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
  one of 1,270 cases, with 0 coordinate errors out of 30,480.
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
declarations across 35 files when that was fixed, and stands at **1,270**
declarations across **48** files now that `LLVQTable.lean` has added the
formal side of the constant-time quantiser table — the class-minimum min-sum,
the 32-codeword class size and the branch-and-bound bound (18 declarations) —
beside `QuestionNested.lean`'s
three remaining pieces of description language — a list, a modifier and a
nested side (53 declarations) — beside `Question.lean`'s question shape as an
object and the matcher it forces (57), `Recipe.lean`'s domain description and
the path *it* forces (35), `Denotation.lean`'s vocabulary decision over the
`related_to` residue (35), `MeasureView.lean`'s relative-measure layer over
comparison classes (40), `Heisenberg.lean`'s infinite-dimensional half of the
VOA bridge — the Fock space, its modes and the trace obstruction to any finite
model (39), `LogBucket.lean`'s exact magnitude bucket the economic register
reads its prices through (15) — and `Comparative.lean`'s comparative over those
measure-word uses (41).

| kind | count |
|---|---|
| theorem | 813 |
| def | 328 |
| lemma | 84 |
| structure | 18 |
| abbrev | 13 |
| inductive | 8 |
| instance | 5 |
| example | 1 |
| **total** | **1,270** |

The `example` row is `Denotation.lean`'s one anonymous check that the physics
register does not dimension the word *gravity*; the reader gives it a
positional name (`_example_366`) exactly as it does an anonymous `instance`,
so an unnamed declaration is addressed rather than silently dropped.

Largest single file: `Question.lean`, 57 declarations.

Two independent checks keep the reader honest.

* `parser_agreement()` reports **1,270 parsed, 0 duplicates** — no name is
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
few hundredths — still not something to do 1,270 times per query, and the
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
| 4 | 33 / 60 | 27 | — | **lossy** |
| 6 | 60 / 60 | 60 | 2 | lossless, non-degenerate |
| 8 | 60 / 60 | **0** | 0 | **degenerate** |
| **9** | **60 / 60** | **60** | **2** | **lossless, non-degenerate** |
| 12 | 60 / 60 | 27 | 4 | lossless, partly degenerate |
| 16 | 60 / 60 | **0** | 0 | **degenerate** |

The two failures are different in kind.

**Lossy, below 8.** The covering radius of the lattice in this integer model is
4, so quantising moves no coordinate by more than 4. A scale above twice the
radius keeps every coordinate strictly inside half a step, and then the feature
vector is recoverable; below that it is not, and at scale 4 nearly half the
sample cannot be read back.

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
| declarations checked | 1270 |
| read back exactly | **1,270 / 1,270** (rate 1) |
| coordinates checked | 30,480 |
| coordinate errors | **0** |
| moved by the decoder | 1,270 / 1,270 |
| worst observed residual | **3**, at `GLM.Info.Layer.card_le_capacity_of_lossless` |
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
| `feature` | 1,182 / 1,270 | 1,182 | 71 | 159 | **no** |
| `hash_control` | **1,270 / 1,270** | 1,182 | 0 | 0 | — |
| `shuffled` | 1,182 / 1,270 | 1,182 | 71 | 159 | no |

Two things to read off this table.

**The conflation is the feature map's, not the lattice's.** The number of
distinct addresses equals the number of distinct feature vectors, exactly. The
quantiser adds nothing: every collision is a pair of declarations the 24 counts
genuinely cannot tell apart. That is `address_congr` observed rather than
proved, and `injective_features_of_injective_address` is the direction that
*is* proved — an injective address forces an injective feature map, never the
other way round.

**The control is injective and that means nothing.** SHA-256 of the name
separates all 1,270, because a digest separates anything; §7 shows it separates
them into a cloud with no structure in it. Injectivity is cheap. It is the
wrong thing to optimise, and the control is in the report to make that visible.

The 71 classes are small — 57 pairs, 11 triples, three classes of four — and
they are recognisably the *right* classes, in the sense that a reader shown
only the 24 counts would also fail to tell the members apart:

```
4  GLM.Facets.Carrier, GLM.Golay24.Word, GLM.Info.Carrier24, GLM.Info.tea
4  GLM.Info.axisLayer, GLM.Question.deriveOpening,
   GLM.Question.deriveDomainWord, GLM.QuestionNested.comparativeOperator
4  GLM.Reversible.fredkin_involutive, GLM.Reversible.toffoli_bijective,
   GLM.Reversible.toffoli_involutive, GLM.Semantics.meaningLayer_lossless
3  GLM.Info.integerModel_refines_si7Model, GLM.Semantics.dim_refines_si7,
   GLM.Semantics.si7_conflates_energy_torque
3  GLM.Facets.facet, GLM.Golay24.col, GLM.Sakuma.axisProduct
3  GLM.Golay24.Syn, GLM.Heisenberg.V, GLM.Heisenberg.vac
```

The first line is a class of naming: four one-line abbreviations for a carrier
or a named datum — a function on `Fin 24`, a Golay word, a 24-coordinate
carrier, a comparison class — which have, as *shapes*, nothing to tell them
apart. The second is this round's own contribution and makes the same point
about description language: a layer, two phrasings of a question shape and a
comparative operator are each a structure filled in with constants, and the 24
counts record exactly that and no more. The fourth line is a family:
refinements and conflations of one chain of models, differing in *which* model
they are about, which the feature map does not record — it records that the
statement is a refinement of that size, citing that many results. The fifth is
the same phenomenon among definitions, three one-line projections; the sixth
puts a type abbreviation beside two distinguished elements of a space. So the
boundary of this layer is, almost exactly, "the same statement about a
different member of the same family", which is a fair description of what a
24-count structural summary should be unable to see. The third line is the
honest counterexample and has survived every re-measurement: two involutivity
results and a bijectivity result of the reversible gates sit in one class with
a losslessness theorem about the meaning layer, conflated for no reason a
reader would endorse.

---

## 7. Does distance mean anything? Three schemes, two null models

The test: for each declaration, take its nearest neighbour by address and ask
whether that neighbour came from the same file, and whether the two cite one
another. Ties are broken by taking all of them, and the tie sizes are reported,
so a scheme cannot win by being vague.

The chance rate is not `1/48`. It is computed from the actual file sizes — the
probability that a uniformly chosen other declaration shares a file — which
comes to `1334/53721 ≈ 2.48%`.

| scheme | nearest shares a file | rate | mean tie size |
|---|---|---|---|
| `feature` | **386 / 1,270** | ≈ **30.4 %** | 1.40 |
| `hash_control` | 26 / 1,270 | ≈ 2.05 % | 1.00 |
| `shuffled` | 14 / 1,270 | ≈ 1.10 % | 1.40 |
| *chance* | — | ≈ 2.48 % | — |

| scheme | nearest is cited, either way | rate |
|---|---|---|
| `feature` | **66 / 1,270** | ≈ 5.20 % |
| `hash_control` | 9 / 1,270 | ≈ 0.71 % |
| `shuffled` | 3 / 1,270 | ≈ 0.24 % |
| *chance* | — | ≈ 0.54 % |

And on all pairs, not just nearest ones — 20,010 same-file pairs against
785,805 cross-file ones:

| scheme | mean d² within a file | mean d² across files | ratio |
|---|---|---|---|
| `feature` | 6,032.5 | 6,912.6 | **0.873** |
| `hash_control` | 54,298.8 | 54,395.2 | 0.998 |
| `shuffled` | 6,941.3 | 6,889.5 | 1.008 |

The two controls do exactly what they are there for.

* **`hash_control`** is deterministic, stable and injective, and lands within a
  hair of chance on every measure: 2.05 % against 2.48 %, and a within-file
  distance 0.2 % below the across-file one. This is what an address looks like
  when it carries no information about its subject. It is the empirical content
  of directive **D3** — *a digest addresses integrity, never meaning* — and the
  reason the project has moved all of its SHA-256 use into a single
  `integrity` module one level above the six core sub-packages, where a purity
  audit can enforce that the core never imports `hashlib` at all. The one
  digest that touches meaning in this repository is this control, and it is
  labelled as a control.
* **`shuffled`** is the stronger null. It is the *same multiset of feature
  addresses*, re-assigned by a seeded permutation, so it has precisely the same
  geometry — same distances available, same tie structure (mean tie size 1.40,
  identical to `feature`), same 71 collision classes — and only the pairing
  between address and declaration is destroyed. It lands at 1.10 %, below
  chance, with a within-file mean distance 0.8 % *above* the across-file one.
  So the 30.4 % is not the lattice being clever with a lot of points;
  it is information the features supplied.

Verdict, as the report computes it: `feature` beats chance, beats the digest
control, and beats the shuffle, on both the file test and the citation test.
The digest control is chance-like. Just over twelve times chance on the file
test, and nearly ten times chance on the citation test, from an encoding that
is never shown a file name.

Two honest qualifications. First, 30.4 % is not 90 %: nearest-by-address is a
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
  nearest:  GLM.Golay24.sextet_cycle_tendsto              d² = 1952
            GLM.Feedback.efAverage_error_le_identity      d² = 2368
            GLM.Golay24.perturb_correct_returns           d² = 2448

GLM.Info.Layer.Visible.mono                       (Layers.lean:91)
  "a theorem, over Prop/Bool, citing 3 and cited by 1"
  |address|² = 4160,  read back exactly
  nearest:  GLM.Recipe.Spec.answer_of_mem                 d² = 256
            GLM.Golay.hdist_bitReverse                    d² = 320
            GLM.Info.Layer.boundary_verdict               d² = 320

GLM.Address.address_congr                         (Address.lean:150)
  "a theorem, stating 2 equality/-ies, citing 5 and cited by 1"
  |address|² = 8608,  read back exactly
  nearest:  GLM.Info.reading_of_match                     d² = 352
            GLM.Address.conflates_symm                    d² = 384
            GLM.Info.namedResolution_of_injective         d² = 384

GLM.Info.glmChain_refines_of_le                   (LayerChain.lean:189)
  "a theorem, stating 1 order relation(s), over N, citing 4 and cited by 1"
  |address|² = 4672,  read back exactly
  nearest:  GLM.Info.ds_refines_of_le                   d² = 128
            GLM.Facets.proj_add                         d² = 256
            GLM.Info.mBit_const                         d² = 256
```

The second example is the good case: two of `Visible.mono`'s three nearest
neighbours are layer lemmas from its own file, tied at the same distance as an
unrelated Hamming-distance lemma — the encoding is reading a shape, and two of
the three things with that shape are its neighbours in the source. The third
is an earlier round's honest movement: `address_congr`'s nearest neighbour used to be
from its own file, and is now `GLM.Info.reading_of_match` from the newly added
`Comparative.lean`, with `conflates_symm` displaced to second place. Nothing
about `address_congr` changed; the corpus grew a statement of the same shape.
That is what a *weak* similarity signal does when the population it ranks over
changes, and it is worth stating plainly rather than re-picking the example.
The fourth is the clearest hit — the refinement chain of the shipped layers
lands next to another "every layer refines every layer below it" statement from
a different file at d² = 128, closer than anything else in these four examples,
because the encoding is reading the shape `≤ ⇒ something` rather than the
subject. The first is the instructive one — a Barnes–Wall divisibility result
whose nearest neighbour is a Sturmian limit from `Wobble.lean`, at a squared
distance of 1952, six times further than anything in the second example. Its
own file supplies no neighbour at all in the top three.
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

Everything else in this document is a measurement: 1,270, 1,182, 386, 26, 14,
66, 0 coordinate errors, worst residual 3. Those are properties of *this*
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
license retrieval: 30.9 % same-file is far above the 2.53 % chance rate and
far below useful.

**The load-bearing negative result** is the digest control. It is injective,
deterministic, stable across runs and machines, trivial to compute — every
property one might naively want from an addressing scheme — and it is
indistinguishable from chance on every measure that asks whether the address
knows anything. That is the whole content of directive D3, measured on 1,270
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
