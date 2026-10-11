# Norm 256 and the hex colour — a rotated Leech rung, the hex-digit readings, and a hex shortcut

## Tier 0 — the coarse read

**Question.** Can the empty norm-256 rung of the power-of-two family be filled by a construction other than the scaled `√2`-lattices — the Leech lattice rotated by `√2`, or a reading that keeps the first hex digit of each coordinate — and does the norm-256 rung give the hex colours of the Leech classes a usable shortcut?

**Verdict.** Partly. Norm 256 is filled, by the reading that keeps the first hex digit of each coordinate (`H16`): it answers none of the 568 queries wrongly and none of the 568 held-out queries wrongly, but it answers nothing the rest of the ladder cannot on the 568 and one query more on the held-out set. The rotated Leech rung and the nearest-hex-digit rung are retired, each for wrong answers. The hex shortcut held on every point checked: a point of `2C` lies on the rotated Leech rung exactly when the hex colour of its half lies in a 4096-colour subspace. The held-out set also shows that the ladder Phase 123 left is not safe on new perturbations: it answers 8 of 568 wrongly, with or without the new rung.

**Deciding figure.** 7 of 8 marks (L1, C1, F1, F2, H1, X1, X2; H2 missed); `H16` 0 wrong on both query sets (119 and 77 correct); held-out ladder 440 correct, 8 wrong (439 and 8 without `H16`); the shortcut agrees on 1,000 of 1,000 points.

**Recomputed by.** `glm_universal.reasoning.norm256_hex.norm256_hex_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration** for Phase 127. §§0–6 are as they were committed; §7 is
what came out.

It takes item 1 of [`STATUS.md`](../STATUS.md) §2.1, *norm 256 of the
power-of-two family*, left by Phase 123
([`LATTICE_COMPLETION_STUDY.md`](LATTICE_COMPLETION_STUDY.md) §7.6): both
candidates tried there, `8E8^3` and `8D4^6`, answered six of the 568 queries
wrongly and were retired, and a rung at norm 256 that does not conflate "needs
a construction other than the scaled `√2`-lattices".

The owner's note for this round: *norm 256 could align with hex colour, for
some kind of GLM reasoning or shortcut.* The arithmetic behind the note is
exact and is the starting point here: one colour channel has `256 = 16²`
values (two hex digits); a minimum norm of 256 is a minimum distance of 16,
one hex digit; a hex colour is `16⁶ = 2²⁴` values, which is exactly the number
of classes of the Leech lattice modulo twice itself; and `16³ = 4096`, the
short `#RGB` form, is the number of Golay codewords. Whether any of that buys
a rung or a shortcut is what is measured.

**Order of work, stated plainly — this is not a blind test on the 568
queries.**

1. *Exploration before this was written.* Each of the three candidates of §2
   was run once, alone, over the 568 queries of the norm family, during the
   search for a construction: the rotated Leech rung answered **2** wrongly
   (both from `septimal_tritone`), the hex-digit rounding `16Z` **4** wrongly
   (all from `minor_third`), and the hex-bucket reading `H16` **0** wrongly
   (119 correct, 449 refused). Its tie-down variant (150 correct, 0 wrong) was
   also run and is *not* a candidate: the hex digit of a value is its floor,
   so ties go up, and that was fixed before the variant was run. No candidate
   was run inside the ladder, so no `unique_correct`, disagreement or
   retirement figure was seen.
2. *The Lean file before this was committed.*
   `RequestProject/GLM/HexRung.lean` was written and built first (§1).
3. **The held-out query set of §4 has not been generated or run.** It is the
   blind part of this round; the filling over the 568 queries (§3, mark F1) is
   reported as a reproduction of what exploration already showed.

## 1. What is proved before any code

`RequestProject/GLM/HexRung.lean`, no `sorry`, `#print axioms` showing
`propext`, `Classical.choice` and `Quot.sound` only:

* **A rotation by `√2`.** For a fixed-point-free involution `P` and signs `e`
  opposite on each pair, the signed permutation `rot x j = e (P j) · x (P j)`
  satisfies `rot ∘ rot = −1` (`rot_rot`), `x ⊥ rot x` (`inner_rot_self`),
  `‖x + rot x‖² = 2‖x‖²` (`normSq_add_rot`) and `(1 − rot)(1 + rot) = 2`
  (`sub_rot_add_rot`); so `(1 + rot) L` has twice the minimum norm of `L`
  (`min_norm_doubles`), and its nearest point to `y` is `1 + rot` applied to
  the nearest point of `L` to `(y − rot y)/2` (`nearest_transfer`).
* **The concrete rotation of the Leech lattice.** `hexP` (a fixed-point-free
  involution found by a backtracking search over octads) is a Golay
  automorphism (`golay_perm_closed`, from a 4096-message table checked by the
  kernel), the dodecad `hexS = 466837` is a transversal of its pairs
  (`hexSign_pair`), and the rotation maps `Λ₂₄` to itself
  (`hexRot_isLeech`). The candidate `R256 = (1 + hexRot)(2Λ₂₄)` has minimum
  norm at least 256 (`rotLeech_min_norm`).
* **The hex-digit reading.** Reading a coordinate by its hex bucket `⌊v/16⌋`
  is the nearest-point map of the coset `16ℤ + 8`, ties going up
  (`floor_bucket_nearest`); `hex_counts` records `16² = 256`, `16³ = 4096`,
  `16⁶ = 2²⁴`.

## 2. The candidates, and the order they are tried in

All three have minimum distance 16, so all three sit at norm 256.

| key | construction | kissing | covolume | quantiser |
|---|---|---|---|---|
| `R256` | `(1 + hexRot)(2Λ₂₄)`: the Leech rung `2C` rotated by `√2` | 196,560 | `2^72` | `nearest_transfer` over the family's own `2C` quantiser |
| `16Z` | `16 ℤ²⁴`: each coordinate rounded to a multiple of 16 (the nearest hex digit) | 48 | `2^96` | per coordinate, ties down (the family's rounding) |
| `H16` | the coset `16 ℤ²⁴ + (8, …, 8)`: each coordinate read by its first hex digit `⌊v/16⌋` | 48 | `2^96` | per coordinate, `floor_bucket_nearest` |

**The order, declared:** densest first (largest kissing number), the rule the
family already uses; at a tie, a lattice before a translate. So `R256`, then
`16Z`, then `H16`.

**The filling rule** is Phase 123's, unchanged: insert the candidate into the
ladder Phase 123 left (the repaired ladder with `D12^2` at norm 2), re-read the
568 queries, and **keep** it if `norm_escalation.retirement` retires no rung of
the result; otherwise try the next. A translate is admitted because the rule
reads a rung only through its quantiser: a query is answered when the cell it
falls in holds exactly one carrier.

## 3. The marks, declared before the code

| mark | statement |
|---|---|
| **L1** | `RequestProject/GLM/HexRung.lean` builds with no `sorry` and the standard axioms only, with the theorems of §1. |
| **C1** | Each candidate's quantiser returns a point of its rung on 200 declared test vectors (the Phase 123 sweep), and for `R256` the returned point satisfies `‖y − p‖² = 2‖z − q‖²` with `q` the `2C` point it came from; `16Z` and `H16` have kissing number 48 by enumeration. |
| **F1** | *Reproduction, not blind.* The filling over the 568 queries keeps exactly one of the three, `H16`; `R256` and `16Z` are retired under clause 1. |
| **F2** | The ladder with `H16` in it is safe (0 wrong), order-independent and equal to its oracle, and answers at least as many queries correctly as Phase 123's filled ladder (467). |
| **H1** | *Blind.* On the held-out set of §4, the kept norm-256 rung answers 0 queries wrongly. |
| **H2** | *Blind.* On the held-out set, the filled ladder with the kept rung answers 0 queries wrongly. |
| **X1** | The image `W` of `1 + hexRot` on `Λ₂₄/2Λ₂₄` — read through the package's 24-bit class of a Leech vector, i.e. its hex colour — has dimension 12, so `4096 = 16³` colours, and the class quadratic form vanishes on it. |
| **X2** | **The hex shortcut.** For a point `p` of `2C`, `p ∈ R256` exactly when the hex colour of `p/2` lies in `W`: twelve parity checks on six hex digits. Checked on 1,000 declared points of `R256` (all must say yes) and 1,000 declared points of `2C` (the shortcut and the direct test must agree on every one). |

**What the marks do not claim.** No mark says the norm-256 rung improves an
answer the system gives; the rung is measured beside the ladder, as Phase 123's
candidates were, and the answering path is not touched (§5).

## 4. The held-out query set, declared here

The same 142 carriers; four perturbations not used by any earlier round,
applied with `ladder_escalation.perturb` to the carrier of index `i` with the
codeword index `i + 2048` (so the coordinates and signs differ from the 568):

| support | magnitude | squared length |
|---|---|---|
| 12 coordinates | 1/3 | 4/3 |
| 12 coordinates | 2/3 | 16/3 |
| 6 coordinates | 1 | 6 |
| 24 coordinates | 1/2 | 6 |

568 held-out queries. They are generated and read once, after this document is
committed.

**Predictions.** F1 and F2 as stated (from exploration). On the held-out set:
H1 is predicted to hold but with low confidence — `H16`'s cell walls sit at
coordinate value 0, where most carrier coordinates are, so most queries leave
their carrier's cell; a wrong answer needs the cell they enter to hold exactly
one other carrier, and nothing rules that out. H2 is less likely than H1,
because the other rungs were themselves chosen on the 568 queries and have
never been read on new perturbations. `R256` and `16Z` will also be read on
the held-out set, as description only.

## 5. What this round does not do

* It does not put any norm-256 rung into the answering path, the deep-hole
  reports or the evaluation: that changes pinned answers and needs a
  frozen-path comparison of its own.
* It does not compare other rotations of the Leech lattice (other choices of
  `hexP` and `hexS`): choosing one by its score on the 568 queries would be
  choosing on the test set.
* It does not claim the hex-colour correspondence is more than arithmetic plus
  the one structural fact X1–X2 measure.

## 6. Files

| file | what |
|---|---|
| `RequestProject/GLM/HexRung.lean` | §1 |
| `glm_universal/reasoning/norm256_hex.py` | the candidates, the filling, the held-out set, the hex shortcut, `norm256_hex_report` |
| `glm_universal/tests/test_norm256_hex.py` | the marks |
| `python3 -m glm_universal.tools norm256-hex` | the measurement |

## 7. The measurement

*Written after the measurement. §§0–6 above are as they were committed.*

`python3 -m glm_universal.tools norm256-hex --write` takes it and stores it
beside the digest of its sources (`reasoning/_data/norm256_hex.json`);
`tools norm256-hex` reads it back.

### 7.1 The verdict

Partly. Norm 256 is filled, by the reading that keeps the first hex digit of each coordinate (`H16`): it answers none of the 568 queries wrongly and none of the 568 held-out queries wrongly, but it answers nothing the rest of the ladder cannot on the 568 and one query more on the held-out set. The rotated Leech rung and the nearest-hex-digit rung are retired, each for wrong answers. The hex shortcut held on every point checked: a point of `2C` lies on the rotated Leech rung exactly when the hex colour of its half lies in a 4096-colour subspace. The held-out set also shows that the ladder Phase 123 left is not safe on new perturbations: it answers 8 of 568 wrongly, with or without the new rung.

### 7.2 The marks

| mark | statement | result |
|---|---|---|
| L1 | the Lean file | **met**: `RequestProject/GLM/HexRung.lean`, 11 named theorems, no `sorry`, `#print axioms` showing `propext`, `Classical.choice`, `Quot.sound` only; the Golay-automorphism table and the dodecad's even meetings are checked by the kernel (`decide +kernel`, about two and a half minutes) |
| C1 | the quantisers | **met**: 0 failures on 200 vectors for each candidate; `16Z` and `H16` minimum norm 256 and kissing 48 by enumeration |
| F1 | the filling keeps `H16` (reproduction) | **met**: `R256` answers 2 wrongly (unique 3) and is retired under clause 1; `16Z` answers 4 wrongly (unique 2) and is retired under clause 1 — and with it in the ladder `D12^2` would also be retired, under clause 2; `H16` answers 119 correctly, 0 wrongly, 0 uniquely, takes part in no disagreement, and is kept |
| F2 | the filled ladder is safe and no weaker | **met**: 467 correct, 0 wrong, 101 refused, the same in all three orders and equal to the oracle — identical to Phase 123's ladder, because `H16` adds no answer there |
| H1 | blind: `H16` safe on the held-out set | **met**: 77 correct, 0 wrong, 491 refused |
| H2 | blind: the filled ladder safe on the held-out set | **missed**: 8 wrong in the middle-out and coarse-to-fine orders, 4 in fine-to-coarse; 440 correct (the oracle). Without `H16` the ladder gives 439 correct and the same 8 wrong, so the wrong answers are the old rungs' (§7.3) |
| X1 | `W` is 12-dimensional and singular | **met**: dimension 12 (4096 colours), the class quadratic form and its bilinear form vanish on a basis |
| X2 | the hex shortcut | **met**: 1,000 of 1,000 points of `R256` say yes; on 1,000 points of `2C` the shortcut and the direct test agree on all 1,000 (none of them lies on `R256`, as expected at index `2^12`) |

**Scored as declared: 7 of 8.** The predictions: F1 and F2 held as
exploration said they would; H1 held, against the low confidence declared for
it; H2 failed, as declared more likely.

### 7.3 Post hoc: where the held-out wrong answers come from

*Read after the marks, labelled post hoc.* Over the held-out set the ladder's
rungs give nine wrong rung-level answers, all from three carrier pairs:
`hexacode_word_2` read as `hexacode_word_3` (five times: the Leech rung `C`
four times, `A` once), `acoustic_impedance` read as `acoustic_attenuation`
(three: `A/2` once, `2D` twice) and `high_denominator_2x3` read as
`axis_root_e0` (once, at `Z`). Every one of the four held-out perturbations
produces at least one. None is at a norm-256 rung. So the safety the repaired
ladder has on the 568 queries is partly a property of those 568: its
retirement rule was applied on them, and a fresh set finds pairs of carriers
that sit across a cell wall from each other at rungs the rule kept.

The held-out set read by the candidates alone (description): `R256` 235
correct and 3 wrong, `16Z` 260 correct and 3 wrong, `H16` 77 correct and 0
wrong.

### 7.4 What the hex colour turned out to be, here

* **As a rung**, the hex colour is the hex-bucket reading `H16`: read each
  coordinate by its first hex digit. It is the only norm-256 construction of
  the three that answered nothing wrongly on either query set, and the reason
  is visible in its cells: their walls are at multiples of 16, i.e. at
  coordinate value 0, where most carrier coordinates sit, so a perturbation
  usually carries a query out of its carrier's cell into a cell that holds no
  single carrier, and it refuses (449 of 568, and 491 of 568 held out). It is
  a cautious rung, not a strong one.
* **As a shortcut**, the hex colour is exact on every point checked: the classes of the Leech lattice
  modulo twice itself are the `2²⁴` six-digit hex colours, and the rotated
  rung `R256` picks out a subspace of `16³ = 4096` of them (the size of the
  short `#RGB` form, and of the Golay code), totally singular for the class
  quadratic form. Membership in that rung is twelve parity checks on a colour
  (checked on 2,000 points; the Lean file proves the rotation keeps the Leech
  lattice, not the shortcut itself).
  `R256` itself was retired for wrong answers, so the shortcut is a fact about
  the lattice, not yet a reasoning step the system takes.

### 7.5 What is left

* **The ladder on held-out perturbations.** The repaired ladder answers 8 of
  568 held-out queries wrongly (§7.3). A retirement rule read on one
  perturbation set is not a safety guarantee on another; a margin guard (the second reading of
  [`SECOND_READING_STUDY.md`](SECOND_READING_STUDY.md)) or a retirement read on both sets is the next
  measurement.
* **`H16` in the answering path.** It is measured beside the ladder only; it
  adds one correct answer on the held-out set and none on the 568.
* **Other rotations of the Leech lattice** were not compared (§5), and should
  not be compared on these 568 queries.
* **The hex shortcut as a step**: a use for the 4096-colour subspace — for
  instance as an address for coarse readings — needs a rung that survives.
