# The probe budget — a stopping rule for the certifying reading

## Tier 0 — the coarse read

**Question.** If the certifying reading of a deep hole stops only on its completeness certificate or on a budget fixed in advance by a proved union bound, instead of after a fixed number of barren starts, does it certify every deep hole the walk reaches, where the patience of 60 starts used by the census does not?

**Verdict.** Yes. With no barren stop and the proved budget of 1056 starts, the certifying reading certified all 256 deep holes reached by the held-out walks and all 23 reference centres as recorded, and no reading came near the budget (median 96 starts, maximum 254). On the same 256 centres the census convention of a 60-start patience left 4 uncertified, so lattice item 7 no longer needs a post-hoc patience: the rule is declared, proved under its model, and its model's hypothesis holds on every stored ensemble.

**Deciding figure.** 6 of 6 marks; 256 of 256 held-out deep holes certified by the rule against 252 by the census convention; 23 of 23 references as recorded; least `k · p_min` 101/160 against the declared 1/2; median 96 and maximum 254 starts against a budget of 1056.

**Recomputed by.** `glm_universal.reasoning.probe_budget.probe_budget_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration**, committed before the module that takes the
measurement exists. §§0–6 are as they were committed; §7 is what came out.

It takes item 2 of [`STATUS.md`](../STATUS.md) §2.1, left by Phase 123
([`LATTICE_COMPLETION_STUDY.md`](LATTICE_COMPLETION_STUDY.md) §§7.4, 7.6): the
census's second certifying reading — 400 starts at most, stopping after 60
barren starts — left three of the thirteen new reference centres uncertified,
and a post-hoc re-reading with a patience of 240 certified them.

**Order of work, stated plainly.**

1. *What was known before this was written.* The post-hoc re-reading of Phase
   123 certified the three centres after 196, 254 and 169 starts. The minimum
   arrival share of every one of the 23 reference holes, read from the stored
   ensembles at the reference seed and 7680 starts, was computed to choose the
   constant `c` below: `k · p_min` lies between 0.63 (`A_1^24`) and 0.93
   (`D_4^6`). One declared walk outside the held-out range (walk index 2100)
   was run once to time a walk (about 11 s); it is not part of any measurement.
2. *The Lean file before this was committed.*
   `RequestProject/GLM/ProbeBudget.lean` was written and built first.
3. **No reading under the new rule and no walk of the held-out range had been
   run when this was committed.**

## 1. Why the patience is the wrong stop

The probe (`deep_holes.hole_vertices`) already stops the instant the vertices
in hand carry the completeness certificate — the marked barycentre identity
of `deep_holes.hole_diagram`. So on a hole the patience never ends a
*successful* reading; it only ends a reading early, before the last vertex is
seen, and reports a vertex set the diagram reader cannot identify. A stop
rule should therefore spend its budget only on failures, and the budget should
be chosen so that a failure is improbable.

## 2. The rule

**No barren stop; a budget of `B = 1056` starts.** The reading stops on the
certificate or after `B` starts, whichever comes first
(`classify_carrier(centre, probes=1056, patience=1056, seed=REFERENCE_SEED)`).

**Why 1056** (`GLM.ProbeBudget`). Model the starts as independent, each
reaching a vertex with at least its arrival share, and suppose every vertex of
a hole with `k` vertices has share at least `c / k`. By the union bound the
chance that some vertex is still unseen after `B` starts is at most
`k (1 − c/k)^B`, and `miss_bound` proves this is at most `δ` once
`B ≥ (k / c) log (k / δ)`. That requirement grows with `k` (`budget_mono`);
every deep hole has at most 48 vertices (`niemeier_vertexCount_le`); and with
`c = 1/2`, `δ = 1/1000` the budget 1056 serves every type
(`budget_serves_every_type`). The constant `c = 1/2` is declared below the
smallest measured `k · p_min` (0.63). The model is a model of a deterministic
sweep, not a theorem about it; P2 tests its hypothesis on the stored
ensembles and P4 tests its prediction on held-out holes.

## 3. The marks, declared before the code

| mark | statement |
|---|---|
| **P1** | `RequestProject/GLM/ProbeBudget.lean` builds with no `sorry` and only the standard axioms, and proves `miss_bound`, `budget_mono`, `niemeier_vertexCount_le` and `budget_serves_every_type`. |
| **P2** | **The model's hypothesis.** For all 23 reference holes, at both ensemble seeds and 7680 starts, every arrival vertex's share is at least `1/(2k)`. |
| **P3** | **Control.** The rule certifies all 23 reference centres as their recorded type, with the recorded vertex set. (Foregone for the twenty the census certified and the three of the post-hoc follow-up, because the sweep is deterministic and the rule stops on the same certificate; it is a check that nothing else changed.) |
| **P4** | **Primary.** Over the held-out walks (declared walk indices `i = 3000 … 3255`, seeds `20260825 + 977 i`), every walk that reaches a deep hole has its centre certified by the rule. |
| **P5** | **Agreement.** Wherever the census convention (400 starts, patience 60) also certifies a held-out centre, the rule gives the same type and the same vertex set. |
| **P6** | **The budget is not what stops it.** No reading under the rule, reference or held out, runs to the budget. |

**The predictions, stated as numbers before they are taken.**

* P4: 0 uncertified under the rule (the union bound makes the expected count
  at most 256/1000 under the model).
* The census convention leaves between 5 % and 15 % of the reached held-out
  holes uncertified, concentrated on the types with 28 or more vertices.
* The rule's starts per reading: median between 60 and 200, maximum below
  600.

## 4. Controls

* **P3** is the control: the references must read exactly as recorded.
* **The census convention** is re-run on every held-out centre beside the
  rule, so the comparison is on the same centres.
* **The multiplicity count.** Phase 123 stood at 57 statistics; this round
  adds two readings (the rule and the census convention on the held-out set)
  and the share check, so **60**. No bit score is computed.

## 5. What this round does not do

* It does not change `deep_holes`, the walk, the census, the stored ensembles
  or any answering path; the rule is applied by a new module.
* It does not prove anything about the deterministic sweep; it proves the
  arithmetic of the model and measures the model's hypothesis.
* It does not re-score Phase 123's marks; it records what the rule gives.

## 6. Files

* `RequestProject/GLM/ProbeBudget.lean` — P1.
* `glm_universal/reasoning/probe_budget.py` — the rule, the share
  check, the references and the held-out walks, stored beside the digest of
  their sources; `python3 -m glm_universal.tools probe-budget [--write]`.
* Tests: `test_probe_budget.py`.

## 7. The measurement

*Written after the measurement. §§0–6 above are as they were committed.*

`python3 -m glm_universal.tools probe-budget --write --jobs 8` took the
readings (about ten minutes on eight cores); `probe-budget` reads them back.

### 7.1 The verdict

Yes. With no barren stop and the proved budget of 1056 starts, the certifying reading certified all 256 deep holes reached by the held-out walks and all 23 reference centres as recorded, and no reading came near the budget (median 96 starts, maximum 254). On the same 256 centres the census convention of a 60-start patience left 4 uncertified, so lattice item 7 no longer needs a post-hoc patience: the rule is declared, proved under its model, and its model's hypothesis holds on every stored ensemble.

### 7.2 The marks

| mark | statement | result |
|---|---|---|
| P1 | the Lean file | **met**: `RequestProject/GLM/ProbeBudget.lean`, 6 theorems (`miss_bound`, `budget_mono`, `niemeier_vertexCount_le`, `log_48000_le`, `budget_1056_suffices`, `budget_serves_every_type`); no `sorry`, and `#print axioms` shows `propext`, `Classical.choice`, `Quot.sound` only (`niemeier_vertexCount_le` needs `propext` alone) |
| P2 | the model's hypothesis | **met**: all 46 (hole, seed) pairs have `k · p_min ≥ 1/2`; the least is 101/160 (`A_1^24`, 48 vertices) |
| P3 | the references as recorded | **met**: 23 of 23, same type and same vertex set (foregone, as declared) |
| P4 | every held-out deep hole certified | **met**: all 256 walks reached a deep hole, and the rule certified all 256 |
| P5 | agreement with the census convention | **met**: on the 252 centres the census convention certified, the rule gave the same type and vertex set |
| P6 | the budget never stops a reading | **met**: the longest reading took 254 starts (`A_5^4 D_4`, a reference), the longest held-out one 232 |

### 7.3 What was seen

* **The held-out walks** reached 17 of the 23 types: `E_8^3` 68 times,
  `D_16 E_8` 46, `D_10 E_7^2` 27, `D_24` 26, `A_17 E_7` 17, `A_15 D_9` 15,
  `D_12^2` 13, `A_11 D_7 E_6` 9, `A_24` 9, `E_6^4` 8, `D_8^3` 6, `D_6^4` 4,
  `A_7^2 D_5^2` 3, `D_4^6` 2, and `A_12^2`, `A_8^3`, `A_5^4 D_4` once each.
* **The census convention's four misses** were one `D_16 E_8`, one
  `D_10 E_7^2`, one `D_24` and one `A_11 D_7 E_6`; each stopped one vertex
  short (25, 26, 24 and 26 vertices of 26, 27, 25 and 27), and the rule
  finished them after 162, 196, 209 and 232 starts.
* **The walk's own reading** (200 starts, patience 40) certified 225 of the
  256, so a patience-terminated reading inside the walk leaves about one deep
  hole in eight without a type.

**The predictions.** P4: 0 uncertified — held. The census convention was
predicted to miss between 5 % and 15 % of the held-out holes, concentrated
on types with 28 or more vertices: it missed 4 of 256 (1.6 %), all on types
with 25 to 27 vertices — the prediction was wrong in both parts. The rule's starts: median predicted between 60 and 200, measured
96; maximum predicted below 600, measured 254 — held.

### 7.4 What is left

* **The rule in the walk and in the answering path.** The walk's own reading
  and `classify_carrier`'s default still stop on a patience (40 and 60
  starts). Replacing them with the rule changes answers the evaluation pins,
  so it is a round of its own under a frozen-path comparison like Phase 123's
  B5.
* **The model.** The starts come from a deterministic sweep; the union bound
  is proved for independent starts with the measured shares, and 279 readings
  (23 + 256) agree with it. A statement about the sweep itself is not
  attempted.
* **The statistics count** is now 60 (§4); no bit score was computed.
