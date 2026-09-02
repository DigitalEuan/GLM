# Escalation at register scale — what the layer stack does on the machine's own data

*What `reasoning/escalation.py`, `RequestProject/GLM/Escalation.lean` and
`report escalation` are for, and what they measured.*

Every figure below is recomputed by the code that reports it. Run

```bash
cd overlay
PYTHONPATH=. python3 GLM.py -q "report escalation" --verify-tct
```

and the third column re-derives the whole study in a fresh interpreter and
checks it key by key (`VERIFIED True`).

---

## 1. The question this answers

[`INFORMATION_LOSS_STUDY.md`](INFORMATION_LOSS_STUDY.md) measures the
five-layer stack on **seven** carriers, each one picked to exhibit a boundary:
a half unit for the integer layer, a unit on coordinate 10 for the SI7 window,
two carriers repairing to one 2A axis for the Griess measure. That set answers
*does each boundary exist*, and it answers it well, because every carrier in it
was chosen to make a point.

It cannot answer the question
[`RELATIVE_MEASURE_PROPOSAL.md`](RELATIVE_MEASURE_PROPOSAL.md) §4 left open:

> how does escalation work out as the databases grow?

That needs a carrier set nobody chose. This study uses the one the machine
already holds — **one carrier per named object of every shipped register**:

| register | entries |
|---|---|
| physics | 726 |
| chemistry | 118 |
| molecules | 51 |
| mathematics | 22 |
| harmonics | 28 |
| lexicon | 95 |
| **total** | **1,040** |

Nothing is sampled, and the order is the registers' own, so the carrier set is
a deterministic function of the data files.

## 2. Why the audit had to be rewritten before it could be run

`information_loss.py` compares carriers pairwise. `classes` is quadratic,
`congruence_witness` is quartic, and a single comparison at the rational layer
runs a Leech nearest-point decode. On 1,040 carriers the congruence search
alone is on the order of 10¹² decodes: not a slow computation, an impossible
one.

The way out is not an approximation. Each layer's `measure` is a **sum of
non-negative exact terms**, so it is zero exactly when a small reading of the
two carriers agrees — that reading is the layer's *class key*:

| layer | key | why it is the zero set of the measure |
|---|---|---|
| `substrate` | the 24 parity bits | `_substrate_measure` is their Hamming distance |
| `integer` | the seven SI7 exponents **and** the parity bits | an L1 term plus a Hamming term, both non-negative |
| `rational` | the exact carrier | `metric.distance2`, positive definite over ℚ |
| `griess` | the exact carrier | algebraic distance **plus** `distance2`; equal carriers force equal algebra elements |
| `universal` | the exact carrier | the same measure as the Griess layer |
| `integer_raw` | the seven SI7 exponents alone | an L1 term on them and nothing else |

Keys are hashable, so resolution, loss, boundary sizes and refinement
violations are all computed by grouping rather than by comparing, in one pass.
The whole 1,040-carrier audit then takes seconds.

**The identification is checked, not assumed.** `key_agreement` re-runs each
layer's own `perceive` and `measure` over every pair of a fixed 18-carrier
sample — three per register, evenly spread, chosen by index so the sample is
the same in every interpreter — and compares the verdicts: **918 pairs across
six layers, 0 disagreements**. `tests/test_escalation.py` goes further and
re-runs the *slow* functions of `information_loss` on a 25-carrier mixed set,
checking that the keyed classes, the boundary counts, the violation counts and
the quartic congruence search all agree with the fast path; and it breaks the
key deliberately to confirm the check can fail.

## 3. What each layer resolves

| layer | resolves | loses | largest class | addition descends |
|---|---|---|---|---|
| substrate | 415 / 1,040 | 625 | 142 | no |
| integer | 544 / 1,040 | 496 | 118 | no |
| rational | 757 / 1,040 | 283 | 78 | yes |
| griess | 757 / 1,040 | 283 | 78 | yes |
| universal | 757 / 1,040 | 283 | 78 | yes |
| *`integer_raw` (rejected)* | *359 / 1,040* | *681* | *177* | *no* |

Resolution rises and then stops. It stops at the rational layer because that
layer's view **is** the carrier, and the two layers above it add readings that
are functions of the carrier, so there is nothing left for them to gain.
`GLM.Info.entryResolution_mono` proves the rise cannot invert for any register
and any pair of layers, so growing the registers can move these numbers but not
their order.

## 4. What each boundary gains, and that none of them loses

| boundary | pairs gained | refinement violations | is a refinement |
|---|---|---|---|
| substrate → integer | 5,883 | 0 | yes |
| integer → rational | 5,475 | 0 | yes |
| rational → griess | 0 | 0 | yes |
| griess → universal | 0 | 0 | yes |

`refinement_chain_intact : True` — now on a thousand carriers rather than
seven. This is the property [`MASTER_PLAN.md`](../MASTER_PLAN.md) §14.2 closed
by widening the integer layer, and it survives contact with real data.

## 5. The ceiling, which the seven carriers could not have shown

A register is a **naming**: it maps names to carriers, and nothing makes that
map injective. Two entries with the same 24 coordinates are indistinguishable
at *every* layer, because a layer's view is a function of the carrier alone —
`GLM.Info.indist_of_carrier_eq`. The number of distinct carriers is therefore
a hard ceiling on what escalation can ever resolve
(`GLM.Info.entryResolution_le_distinct`), and the rational layer already
attains it (`GLM.Info.entryResolution_rational`).

Measured: **757 distinct carriers under 1,040 named entries.** 283 entries —
27% of the corpus — are beyond every layer of the stack, in **104 collision
classes**, and **every one of those classes lies inside a single register**;
there is not one cross-register collision.

| register | entries | substrate | integer | distinct carriers | unreachable |
|---|---|---|---|---|---|
| physics | 726 | 128 | 245 | 451 | 275 |
| chemistry | 118 | 117 | 118 | 118 | 0 |
| molecules | 51 | 43 | 51 | 51 | 0 |
| mathematics | 22 | 10 | 12 | 14 | 8 |
| harmonics | 28 | 28 | 28 | 28 | 0 |
| lexicon | 95 | 91 | 91 | 95 | 0 |

So the ceiling is almost entirely one register's, and the reason is not a
defect of the layers. The four largest classes:

| size | register | members (first four) |
|---|---|---|
| 78 | physics | `absorptance`, `albedo`, `archimedes_number`, `aspect_ratio` |
| 12 | physics | `abbe_dispersion_number`, `birefringence`, `f_number`, `finesse` |
| 9 | physics | `bit_error_rate`, `crest_factor`, `damping_ratio`, `gain_margin` |
| 9 | physics | `bohr_radius`, `compton_wavelength`, `compton_wavelength_electron`, `de_broglie_wavelength` |

The 78 are the **dimensionless ratios**: a physics carrier holds ten EXT10
exponents, their SI7 projection, a scale, a rank, three gradings, a kind index
and a domain index, and two dimensionless quantities of the same kind in the
same domain agree on all 24. The class of 9 wavelengths is the same story one
dimension up: they are all lengths at the same scale in the same domain.

That is worth saying precisely, because it is a statement about the encoding
rather than about the stack. *Albedo* and *absorptance* differ in what they
are **of**, not in what they **are**: the register carries no coordinate for
provenance, so the difference is not in the carrier and no perspective on the
carrier can recover it. The eight unreachable entries of the mathematics
register are the same phenomenon by construction — `filled_1x24`,
`filled_2x12`, `filled_3x8` and the rest are one vector under six names.

**What the ceiling does not say** is that the machine confuses these
quantities. The register indexes them by name, `describe albedo` answers about
albedo, and the analogy layer transports named relations rather than
coordinates. What it says is that *escalation* — the mechanism this project
uses when one perspective is not enough — has nothing left to offer here, and
that a seventh coordinate of provenance, not a sixth layer, is what would.

## 6. Where addition still descends

An operation descends to a layer when the layer's own resolution determines the
result. At scale:

* **rational, griess, universal — yes.** Their view is the carrier, so
  indistinguishable carriers are *equal* and their sums are equal.
  `GLM.Info.glmRationalLayer_congruentOn` proves it for every operation and
  every region, which is why the scaled audit reports these three as congruent
  without a search rather than by failing to find a witness.
* **substrate, integer, integer_raw — no**, and the witness is drawn from the
  registers themselves: `abbe_dispersion_number` and `high_denominator_2x3`
  are indistinguishable at all three, yet adding `absorbed_dose` to each
  separates them. The mechanism is that all three readings take an *integer
  part* first, and ⌊·⌋ does not commute with addition. The minimal form of the
  same witness is in Lean: a half unit and the vacuum agree at the substrate
  and at the integer layer, and their doubles do not
  (`GLM.Info.substrate_addition_not_congruent`,
  `GLM.Info.glmIntegerLayer_addition_not_congruent`).

## 7. The rejected reading, measured at scale

`LAYER_INTEGER_RAW` — the seven SI7 exponents with the substrate's view
discarded rather than kept — is retained in the codebase precisely so its cost
can be shown rather than described. On the seven fixture carriers it lost one
pair. On the registers:

* it resolves **359** where the cumulative reading resolves **544**;
* it conflates **11,176** pairs the substrate below it already separates, so it
  is not a refinement of the substrate by a wide margin (first pair, in index
  order: `abbe_dispersion_number` and `acoustic_absorption`);
* the shipped cumulative reading has **0** such violations.

The decision recorded in `INFORMATION_LOSS_STUDY.md` §3.1 — widen the layer
above rather than narrow the layer below — was taken on one pair. At scale it
is worth 11,176.

## 8. What is machine-checked

`RequestProject/GLM/Escalation.lean`, on `Carrier24 = Fin 24 → ℚ` and the five
layers of `LayerChain.lean`:

| theorem | what it says |
|---|---|
| `indist_of_carrier_eq` | entries sharing a carrier are indistinguishable at every layer |
| `entryResolution_le_distinct` | no layer resolves more entries than there are distinct carriers — the ceiling |
| `entryResolution_rational`, `entryResolution_eq_of_lossless` | the rational layer, and every lossless layer, attains it |
| `entryResolution_mono` | resolution rises with the layer, for any register |
| `congruentOn_of_lossless`, `glmRationalLayer_congruentOn`, `glmGriessLayer_congruentOn`, `glmUniversalLayer_congruentOn` | every operation descends where the view is the carrier |
| `substrate_addition_not_congruent`, `glmIntegerLayer_addition_not_congruent` | addition does not descend below that, with the half-unit witness |

The file builds under `lake build` with no `sorry`, and the theorems depend
only on Lean's standard axioms.

## 9. Where it is reachable

| surface | what it gives |
|---|---|
| `report escalation` (aliases `scale`, `registers`, `ceiling`, `resolution`) | the whole study in three columns, the third re-deriving it in a fresh interpreter |
| `reasoning/escalation.py` | the keys, the keyed audit, the ceiling and the carrier set, all as functions |
| `report information loss` | the same audit on the seven boundary fixtures |
| `tests/test_escalation.py` | 34 tests: the keys against the slow audit, the carrier set, the resolution column, the boundaries, the ceiling and its per-register attribution, descent, the rejected reading, and the report subject |
| `RequestProject/GLM/Escalation.lean` | the six results above |

## 10. What this leaves open

* **A coordinate for provenance.** The 275 unreachable physics entries are a
  statement about what a physics carrier holds, and closing it means deciding
  what *of* means as a coordinate — not adding a layer. It is not attempted
  here, and nothing in the machine currently pretends otherwise.
* **The rest of the relative-measure proposal.**
  [`RELATIVE_MEASURE_PROPOSAL.md`](RELATIVE_MEASURE_PROPOSAL.md) lists this
  audit as step 1 of five; steps 2–5 (converting `related_to` triples, the
  comparison-class register, the measure view as a widening, and a query with a
  tested refusal) are untouched. Step 1's result is a reason to take the
  proposal's warning seriously: adding *data* to a register moves these numbers
  much more than adding machinery to the stack does.
