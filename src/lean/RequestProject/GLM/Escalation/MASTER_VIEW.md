# The GLM master view: escalation boundaries, checked and rebuilt (Round 43)

## Tier 0 — the coarse read

**Question.** Which statements of the owner's escalation sketch hold for the GLM that actually ships?

**Verdict.** Each statement of the sketch is kept, incomplete or false, with the evidence: the snap is the only place the layer changes, roll-back is incomplete, and the five moduli are not forced by the layer order.

**Deciding figure.** Ledger rows C393–C399; 144 = 8·18, so the claim that 8 does not divide 144 is false.

**Recomputed by.** (hand-written argument; nothing to recompute)

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `tools/tier0_check.py` (or the GLM's corpus check, after a merge) fails if they stop being.*

This is the revised version of the owner's concept sketch `GLM_Escalation_Boundaries_Exploration.md`.
The sketch was written against the GLM Technical Specification alone. This version keeps its
structure: the master equation, the five layers, escalation, the snap, the unified equation, the
analogies and the open questions. It anchors each part in two things: the GLM that actually ships
(`glm_repo.zip`: `dimension_layers.py`, `golay_decode.py`, `deep_holes.py`, and the Lean files
`Layers.lean`, `LayerChain.lean`, `Escalation.lean`), and theorems checked in this package.

Evidence tags, as in `../Rule30/claims.csv`:
* **FORMAL**: a Lean proof with standard axioms only.
* **CERT**: a Lean finite certificate (`native_decide`).
* **SCRIPT**: checked by `rule30_round43/escalation_checks.py`, not in Lean.
* **REPORTED**: stated by the GLM repository; not re-checked here.

Ledger rows: C393–C399.

---

## 0. Verdicts at a glance

| # | Sketch statement | Verdict | Evidence |
|---|---|---|---|
| 1 | The state should be a pair (carrier, layer); the snap is the only place the layer changes | **kept**; proved for the step as defined | FORMAL `Machine.layer_preserved_of_snap` |
| 2 | TCT failure "rolls back" the state | **incomplete**: with a fixed target, a rejected state stays rejected for ever | FORMAL `Machine.iterate_of_reject` |
| 3 | Five moduli 2, 4, 8, 144, 256 are forced by the layer order | **false** as stated | below |
| 3a | "8 ∤ 144", so Rational → Griess is not arithmetic | **false**: 144 = 8·18 | FORMAL `residue_144_refines_8` |
| 3b | mod 256 refines mod 144 (Griess ≺ Universal) | **false** | FORMAL `residue_256_not_refines_144` |
| 3c | Rational perceives the identity and Griess/Universal (mod 144/256) sit above it | **impossible**: only injective views refine the identity | FORMAL `View.refines_identity_iff`, `residue_not_refines_identity` |
| 4 | Graded escalation: the mod-8 filter resolves 1/2 + 1/2 | **false** for every floor-residue filter (mod m, m ≥ 2) | FORMAL `floorResidue_add_not_congruent`, `graded_escalation_claim_false` |
| 4a | "mod 4 fails: perceive₄(1) = 1 ≠ 2 + 2" | **arithmetic error**: ⌊4·1⌋ mod 4 = 0 = 2 + 2 | FORMAL `scaled_four_half_consistent` |
| 4b | Escalating upward can only help | **false**: congruence is not monotone under refinement | FORMAL `congruent_not_monotone` |
| 4c | Escalate to the first layer that resolves | **kept**; correct, minimal, and always succeeds when the top layer is lossless | FORMAL `escalate_spec`, `escalate_isSome_of_top` |
| 5 | A fixed syndrome table removes snapping instability | **false**: no choice of coset leaders is continuous | FORMAL `no_continuous_leader` |
| 5a | Syndromes mod 2, 4, 8, 144, 256 classify the 23 deep-hole types | **unsupported, and mod 8/144/256 carry no information** | SCRIPT (8ℤ²⁴ ⊂ √8·Λ₂₄) |
| 5b | Λ₂₄ quotient mod m is a finite group of order m²⁴ | **false**: ℝ²⁴/(Λ + mℤ²⁴) is a torus | SCRIPT |
| 5c | The list of 23 Niemeier root systems | **22 listed; E₆⁴ missing** (also missing from `DeepHoleType`) | SCRIPT |
| 5d | "plus the shallow hole corresponding to Λ₂₄ itself" | **wrong**: Λ₂₄ has no roots and corresponds to no hole; shallow holes are classified separately | — |
| 5e | Substrate ambiguity happens at deep holes | **at the substrate it is the six-way tie at Golay weight 4** | CERT `golay_decoding_dichotomy`, `golay_coset_census` |
| 6 | The layer can give the run a direction (owner's "arrow") | **true when the snap only escalates**: layer non-decreasing, eventually constant | FORMAL `Machine.layer_monotone`, `layer_eventually_const` |
| 7 | GLM ≈ type system | **sharpened**: `descends_iff_congruent` is the universal property of a quotient (`Quotient.lift₂`) | — |

---

## 1. The stack that actually ships

The sketch assigns layers by modulus. The shipped GLM assigns them by **what each layer
reads**. Every layer carries the reading of the layer below it, which makes the stack cumulative.
This is the table in the GLM's own `LayerChain.lean` (REPORTED):

| Layer | Code | Perceives (two carriers are the same when…) |
|---|---|---|
| Substrate | `LAYER_SUBSTRATE` | the 24 parity bits ⌊cᵢ⌋ mod 2 agree |
| Integer | `LAYER_INTEGER` | parity bits **and** the seven SI7 exponents agree |
| Rational | `LAYER_RATIONAL` | the exact rational carriers agree |
| Griess | `LAYER_GRIESS` | carriers agree **and** the 2A axes agree |
| Universal | `LAYER_UNIVERSAL` | every lower reading agrees |

Consequences:

* **Refinement is by construction.** Each layer is the cumulative pair (its own reading, the
  reading below), so it refines the layer below. No divisibility argument is needed, and none
  would work for 144 → 256 (3b).
* **Above the Rational layer, resolution stops growing.** The Rational layer is lossless, so the
  layers above it are lossless too (3c). They add *structure* (2A axes, the Griess product), not
  *resolution*. The GLM's register audit shows this: 1,040 entries resolve into 415 → 544 → 757 →
  757 → 757 classes, and 757 is the number of distinct carriers (REPORTED).
* **Moduli that do mean something.** mod 2 is the substrate's parity, exactly. The substrate's
  error-correcting structure is the 12-bit Golay syndrome (4096 cosets), not a residue filter.
  144 and 256 have no role in the shipped stack.

**Improvement 1 (revised).** The two kinds of refinement are *resolution* refinement
(Substrate → Integer → Rational) and *structural* enrichment (Rational → Griess → Universal).
Structural enrichment adds operations and observables, not distinctions. The sketch's
"arithmetic vs geometric" split points at the right boundary, the Rational layer, but for the
wrong reason.

## 2. Escalation, made correct

The correct graded escalation (FORMAL, `MasterStep.lean`):

```
escalate(cong, k) = the least layer j ≥ k at which `cong j` holds, if any
```

* `escalate_spec`: the returned layer resolves, and no layer between `k` and it does.
* `escalate_eq_none_iff`: it fails exactly when no layer at or above `k` resolves.
* `escalate_isSome_of_top`: if the top layer resolves, escalation always succeeds. A lossless
  layer is congruent for every operation (`View.congruent_of_injective`). In the shipped stack
  the Rational, Griess and Universal layers are lossless, so escalation always stops by the
  Rational layer.

Skipping layers is legitimate: it is just the minimum. What does **not** hold:

* Escalation is not a threshold search. Congruence is not monotone under refinement
  (`congruent_not_monotone`): a coarse layer can be congruent where a finer one is not. Each layer
  must be tested on its own.
* The five floor-residue filters of the sketch never resolve the half-unit sum
  (`five_floor_filters_fail`). On the sketch's own stack, escalation from the substrate returns
  "none". The half-unit sum is resolved in the shipped GLM because the Rational layer reads the
  carrier exactly. This is the GLM's own theorem pair `substrate_addition_not_congruent` /
  `glmRationalLayer_congruentOn` (REPORTED).
* "Kinds of failure" do not map to filters. The failure at mod 2 and the failure at mod 4 are
  the same failure, floor not commuting with addition. Only a lossless reading removes it.

## 3. The snap: what complete decoding can and cannot do

**At the substrate (the Golay code the GLM ships), CERT `GolayTies.lean`:**

* Every 24-bit word has either **exactly one** codeword within distance 3, or **none** within
  distance 3 and **exactly six** at distance 4 (`golay_decoding_dichotomy`).
* By distance from the code, the 4096 cosets split 1, 24, 276, 2024, 1771 at distance 0, 1, 2,
  3, 4, so the covering radius is 4 (`golay_coset_census`, `golay_covering_radius`).
* An error of weight ≥ 5 is never decoded correctly by **any** nearest-codeword rule
  (`golay_heavy_error_never_decoded`).

So the only ambiguity at the substrate is the six-way tie on the 1,771 weight-4 cosets
(1771 · 4096 of the 2²⁴ words). A fixed table hides this tie; it does not resolve it. The GLM's
`golay_decode.decode_complete` already does the right thing: it returns all six leaders with
status `ambiguous`, and `decode_or_detect` turns the tie into detection rather than a guess.

**On the Leech lattice:**

* No complete decoder is continuous (`no_continuous_leader`, FORMAL). Write ℓ(x) for the lattice
  point that x decodes to. Suppose some lattice vector v is read as 1 by an integer-valued linear
  functional; for Λ₂₄, which is unimodular, take the inner product with a suitable lattice vector.
  Then the function t ↦ φ(ℓ(t·v) − t·v) is integer-valued and loses 1 between t = 0 and t = 1, so
  it must jump. A fixed table makes the snap **deterministic**, not **stable**. Jumps happen at
  every Voronoi wall, not only at deep holes, which are Voronoi vertices.
* Residue syndromes do not see deep-hole types. In the standard integer coordinates,
  8ℤ²⁴ ⊂ √8·Λ₂₄ (SCRIPT: each 8eᵢ is a norm-8 Leech vector). So Λ + mℤ²⁴ = Λ for m = 8, 144,
  256: those three "filters" all return the same syndrome, the Λ-coset itself. The quotient
  ℝ²⁴/(Λ + mℤ²⁴) is a torus, not a finite group of order m²⁴.
* How the shipped GLM classifies deep holes: it walks to the hole, certifies its vertex set,
  and reads the extended Dynkin diagram (`deep_holes.classify_carrier`). Its escalation study
  climbs a pre-registered ladder in the reading budget, not in a modulus. It reports the sanity
  count rising from 3/10 to 10/10 and 40 of 44 queries named at the passing cell (REPORTED). This
  is the real "escalation at the deep-hole boundary": escalating the **reading** until the law
  descends, which is exactly `escalate` of §2.

**Improvement 3 (revised).** The snap returns (point, status, layer). Status is `unique`,
`tie(k)` (k leaders) or `beyond-radius`. A tie is an escalation trigger, not something the table
should hide. "The snap is the layer selection" survives in this form: the layer is chosen by
`escalate` applied to "the reading at this layer has a unique answer".

## 4. The unified master step (compiled form)

`MasterStep.lean` compiles the sketch's §6 as `Machine.step`. The state is
(carrier, layer). One tick modulates, snaps (which returns a carrier and a layer), and commits
`gate(snapped)` only if TCT accepts; otherwise it returns the state unchanged. Proved about it:

* **Roll-back deadlocks** (`iterate_of_reject`). With a fixed target, a rejected state is a
  fixed point for every number of ticks. So TCT rejection must change *something*: the target,
  the layer (escalate), or the carrier (perturb). The recommended semantics combines §2 and §3:
  **on rejection, escalate**. If the top layer is reached and TCT still rejects, report a stall;
  that is a real event, as the sketch says, but a terminal one.
* **The snap is the only layer-changer** (`layer_preserved_of_snap`, `layer_preserved_iterate`).
* **Layer as a property of the input** (`layer_of_input`): if the snap ignores the incoming layer,
  accepted ticks from the same carrier land on the same layer.

## 5. The arrow: perspective and direction (the owner's Wobble/Observer idea)

`layer_monotone`, `layer_eventually_const` (FORMAL). Suppose the snap only escalates, never
lowering the layer. Then along every run the layer index is non-decreasing, and in a finite stack
it is eventually constant. This is a precise version of the owner's idea that the read position
of the Observer (Y) gives the GLM "an arrow": the layer orders the run and names the layer the
run settles on. Two cautions:

* If the snap may de-escalate (the sketch's §6.2 trajectory goes Substrate → Rational → Griess
  and back), neither conclusion holds, and the layer gives no arrow.
* At the Rule 30 level, the corresponding Wobble results are in `../Rule30/Wobble*.lean`,
  `ReadAngle.lean` and `Perspective.lean`. Those give a read direction on the space-time diagram.
  The layer arrow here is a separate, coarser direction, on the stack.

## 6. Rule 30 at the escalation boundary

`Rule30Parity.lean` (FORMAL). For a finite Rule 30 row:

  parity(next row) = parity(row) + (number of adjacent `11` pairs) mod 2.

* One Rule 30 step does **not** descend to the substrate (parity) layer. The rows `11` and `101`
  have the same parity, and their successors have different parity.
* Escalating one rung to (parity, pair parity) fixes the next parity but not the next pair
  parity: rows `1` and `111`. Escalation does not stop after one rung.
* The pair term is exactly the non-linear term C·R of Rule 30 = L + C + R + C·R. Rule 90 (L + R)
  always produces an even row from a finite row, so its step descends to the parity layer.

How this connects to the prize questions. P1 says the centre column is not eventually periodic.
That is the same as saying the column descends to **no** finite-state reading
(`problem1_iff_no_jumpRule` and the half-line machine results in `../Rule30`). In the language of
this document, P1 asks whether escalation along finite readings of the centre column ever stops.
The parity law is the first rung of that question for whole rows. P1, P2 and P3 all remain
**open**.

## 7. Real-system correspondences, graded

The sketch's analogies stand as analogies. One of them can be made exact:

* **Type systems / quotients (exact).** A layer's indistinguishability is an equivalence
  relation. "op descends to the layer" is `Quotient.lift₂` / `Quotient.map₂` being definable, and
  its side condition is literally `CongruentOn`. So `descends_iff_congruent` is the universal
  property of the quotient. The universe-hierarchy reading (Type_k) remains an analogy:
  refinement here is between quotients of one carrier type, not between universes.
* **Floating point (good analogy).** Status flags correspond to the snap status of §3 (tie,
  beyond radius), and trap handlers correspond to "on rejection, escalate".
* **CPU rings, OSI, isolation levels (weak).** These are about privilege, wrapping and
  concurrency, not resolution. Keep them for intuition only.

## 8. Improvements and open questions (revised)

Improvements adopted:
1. The state is (carrier, layer). The snap is the only layer-changer. The snap returns a status.
2. Escalation is least-resolving-layer search (`escalate`), with no monotonicity assumption. It
   terminates because the top of the shipped stack is lossless.
3. On TCT rejection, escalate rather than roll back (roll-back alone deadlocks).
4. Ties are reported (Golay: six leaders at weight 4), never hidden by a table.
5. Escalation-only snaps give an arrow (monotone, eventually constant layer).
6. Drop the 2/4/8/144/256 modulus table. Keep mod 2 (parity) and the 12-bit Golay syndrome at
   the substrate. Classify deep holes geometrically (vertex diagram), as the GLM already does.

Open:
* **TCT semantics in full.** What should TCT compare after an escalation, the old or the new
  layer's reading? Lean can state this once TCT has a definition; the sketch does not give one.
* **De-escalation.** When may a run go back down without losing the arrow? A natural sufficient
  condition is a strictly decreasing potential (TCT-accepted ticks lower an error measure). This is
  not formalised.
* **Rule 30 escalation ladder.** Does any finite cumulative reading of finite rows (counts of
  patterns up to length r, mod 2) make one Rule 30 step congruent? Rung 2 already fails (§6). A
  negative answer for every r would be a structural statement about Rule 30's non-linearity. It
  would not by itself settle P1.
