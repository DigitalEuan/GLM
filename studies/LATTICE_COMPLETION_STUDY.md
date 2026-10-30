# The lattice round — the configuration reading answers, all 23 holes are reached, and the empty norms are tried

## Tier 0 — the coarse read

**Question.** Can the three lattice items of the To-Do list be closed together: the configuration reading `L5` put into the deep-hole answering path with certified answers and absences, a reference centre reached for every one of the 23 Niemeier types and read by `L5`, and the two empty norms (2 and 256) of the power-of-two family filled by Construction A rungs that keep the ladder safe?

**Verdict.** Partly. The configuration reading now answers in the deep-hole path: under the declared answer rule it names all 44 escalation queries correctly with no refusal, where the joint reading named 40, and issues 396 certified absences of which none is false. The declared walk reached all thirteen missing Niemeier types, but three of its centres failed the second certifying reading, so the pre-registered census certifies 20 of 23 types; a post-hoc re-reading with more patience certifies the other three, and over all 23 the configuration reading recognises every type with a ratio of 0.1929 at 7680 starts. Norm 2 is filled by `D12^2`; norm 256 stays empty, because both candidates answer six queries wrongly.

**Deciding figure.** 10 of 14 marks met as declared (A1, A3, A4 and C2 missed); 44 of 44 queries answered correctly with 0 false absences; 20 of 23 types certified as declared and 23 of 23 post hoc, `ρ = 0.1929` at `(L5, 7680)` over all 23; norm 2 filled, norm 256 empty; 10 theorems, 0 `sorry`.

**Recomputed by.** `glm_universal.reasoning.lattice_completion.lattice_completion_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration**, committed before the modules that take the
measurements exist. §§0–6 are as they were committed; §7 is what came out.

The owner asked for the three lines of `STATUS.md` §2.1 to be taken as one
round, because they are one subject — the Leech lattice's deep holes and the
ladder of lattices the system reads through:

* **Part A — lattice item 7, the thirteen unreached Niemeier types.** The deep
  hole ensembles reach 10 of the 23 types from 14 declared centres.
* **Part B — `L5` in the answering path** (left by Phase 122). The
  configuration reading certifies all ten reference holes but is a study
  instrument; the deep-hole classifier still names a hole with the ladder's
  readings, and `GLM.DeepHoleFailure.per_type_absent` is instantiated
  nowhere.
* **Part C — lattice item 3, the empty rungs.** The repaired power-of-two
  ladder ([`NORM_FAMILY_STUDY.md`](NORM_FAMILY_STUDY.md) §4) has no rung at
  norms 2 and 256, because every rung the scaling generates there was retired.

**Order of work, stated plainly.**

1. *A pilot, before this was written.* To choose a method for Part A, the
   frozen walk (`deep_holes.walked_hole`) was run at the 1,591 integer seeds
   1000–2995 (not the declared walk seeds). It reached 21 of the 23 types by
   walking (every type but `A_1^24`, which is a construction, and `A_8^3`),
   with frequencies from 331 (`E_8^3`) down to 1 (`D_4^6`, first at seed
   1922; `A_4^6` first at 1633). A second pilot tried the cycle construction
   of §2.A for `A_8^3` once: its first attempt gave a centre the frozen path
   certifies as `A_8^3`. These pilots are why the method below has three
   stages; no ensemble of any new hole was taken.
2. *The Lean file before this was committed.*
   `RequestProject/GLM/LatticeCompletion.lean` was written and built first
   (it needs no measurement).
3. **No `L5` reading of any query, no ensemble of a new hole, and no
   escalation over a new rung had been computed when this was committed.**

## 1. What is used rather than re-derived

* The frozen path to a hole and its certificate (`deep_holes`), the walk
  (`voronoi_walk`), the exact decoder, and the escalation round's ensemble
  (`deep_hole_escalation.emissions`, the two seeds 20260825 and 20260826).
* The ten reference holes and their stored ensembles to 30720 starts
  (`share_ensemble`), unchanged.
* The configuration reading `L5`, its keys and its metric
  (`configuration_reading`), unchanged.
* The escalation round's 44-query set (`deep_hole_escalation.query_set`) and
  its passing cell `(joint, 1920)`.
* The norm family, its 568 queries, its stopping rule, its three visiting
  orders, its audit and its retirement rule (`norm_escalation`), unchanged.

## 2. The three parts

### A. Reaching all 23 types

The reference rule is the first round's: *the first centre certified of a
type is that type's reference centre*. The ten references stand. For the
other thirteen, in three declared stages, each used only for the types the
stages before it left unreached:

1. **The walk, continued.** The declared walk seeds are
   `20260825 + 977·i`; `i < 12` were the first round's. Stage 1 continues
   the same sequence, `i = 12, 13, …`, in chunks of 256, stopping after the
   chunk in which the last type is reached or at `i = 12 + 2047` (a budget of
   2,048 walks). Per type, the smallest `i` that certifies it is the reference.
2. **The cycle construction**, for a type with an `A_n` component. Every
   component of a deep hole has the hole's Coxeter number `h`, and only one
   Niemeier type has an `A_n` component (`h = n + 1`), so a deep hole with an
   `Ã_n` component is of that type. The construction picks `n + 1` lattice
   points with the `Ã_n` Gram matrix — `v_0 = 0`, the `n − 2` points not
   adjacent to it minimal vectors chosen in turn by the declared sweep
   (seed 20260901), the two neighbours of `v_0` as a minimal-vector point plus
   a minimal vector — takes the centroid, and keeps it only if the frozen path
   certifies it as a deep hole of the wanted type. At most 64 attempts per type.
3. **The pilot's seeds**, for anything left: the walk at the pilot's seeds
   1000, 1001, … 2995, in order, first certificate of the type.

Each new reference is run through the ensemble at both seeds to **7680
starts** (nested prefixes 240 … 7680), stored as sufficient statistics like
Phase 121's. The `L5` cell over all 23 references is then read at the six
sizes 240 … 7680, the ten old holes from their stored ensembles.

### B. `L5` in the answering path

**The classifier.** `L5` profiles at the escalation round's cell, 1920 starts.
The reference table is the ten reference profiles at the reference seed.

**The answer rule** (`GLM.LatticeCompletion.config_answer_sound`). For a query
profile `x`, let `T` be the nearest reference. Answer `T` when
`2·d(x, p_T) < B_T`, where `B_T` is the distance from `p_T` to the nearest
other reference; otherwise **refuse**. Where the rule answers, `T` is provably
the strict nearest reference. Each type's **certified radius** is `r_T = B_T/2`.

**The absences** (`GLM.LatticeCompletion.config_absent`, which is
`per_type_absent` at `L5`). For every query and every type `U` that is not
the query's answer, the absence "this hole is not of type `U`" is issued when
`d(x, p_U) > r_U`. It is a theorem under *faithfulness at `r_U`* — every hole
of type `U` reads within `r_U` of `p_U` — which is a hypothesis, not a
measurement; the held-out queries test it (B4).

**In the answering path.** A new report subject, `report hole configuration`,
answers from a cache guarded by the digest of its sources (D4), exactly as the
other deep-hole reports do; the existing reports are not changed. The
**frozen-path comparison**: the end-to-end evaluation must return the same
answer and the same refusal for every case it had before; one case is added
for the new subject.

**Secondary: the 23-reference table.** Once Part A has its references, the
answer rule is re-run on the same 44 queries against all 23 reference
profiles at 1920 starts.

### C. The empty norms

Candidates, all Construction A over a direct sum of short binary codes, so
`GLM.LatticeCompletion.constructionA_normSq_ge` gives their minimum norm:

| norm | candidate (in the order tried) | code | min. norm | kissing | covolume |
|---|---|---|---|---|---|
| 2 | `D12^2` | even-weight `[12,11,2]`² | 2 | 528 | 2^2 |
| 2 | `D8^3` | even-weight `[8,7,2]`³ | 2 | 336 | 2^3 |
| 2 | `D4^6` | even-weight `[4,3,2]`⁶ | 2 | 144 | 2^6 |
| 256 | `8E8^3` | `8 ×` Construction A over the extended Hamming code `[8,4,4]`³ (`√2 E_8³`, norm 4) | 256 | 720 | 2^84 |
| 256 | `8D4^6` | `8 ×` Construction A over the repetition code `[4,1,4]`⁶ (`√2 D_4⁶`, norm 4) | 256 | 144 | 2^90 |

The order at each norm is densest first (largest kissing number), the rule the
family already uses. Each candidate's quantiser is the exact nearest point,
block by block (for Construction A over a code `C` of length `m`: for each of
the `|C|` codewords, round each coordinate to the nearest integer of that
codeword's parity, and keep the nearest).

**The filling rule, declared here.** Norm 2 first, then norm 256. Insert the
candidate into the repaired ladder at its norm; run the audit over the 568
queries; the candidate is **kept** if the declared retirement rule retires
*no* rung of the resulting ladder. Otherwise try the next candidate at that
norm. If none is kept the norm stays empty and that is reported. The norm-256
candidates are tried with the norm-2 result in place.

## 3. The marks, declared before the code

| mark | statement |
|---|---|
| **L1** | The Lean file builds with no `sorry` and only the standard axioms, and proves: `L5` is a `Reading`; the answer rule is sound (`config_answer_sound`); `per_type_absent` at `L5` (`config_absent`); all 253 pairs of Niemeier types at least `4/9` apart in the uniform limit (`uniform_floor`); Construction A has minimum norm `min 4 d` (`constructionA_normSq_ge`). |
| **A1** | A certified reference centre for all 23 types. |
| **A2** | **Control.** At 7680 starts, for every new hole and both seeds, the arrival vertices are exactly the certified vertex set and their diagram has the label's keys. |
| **A3** | **Primary of A.** At `(L5, 7680)` over all 23 references, `Q0 = 23` and `ρ = 2W/B < 1`. |
| **A4** | At `(L5, 7680)` the per-hole criterion certifies all 23. |
| **B1** | **Stopping rule.** The 44-query set is rebuilt and the joint reading at 1920 starts names 40 of 44, as the escalation round recorded. If not, B2–B5 are not read. |
| **B2** | **Primary of B.** The answer rule answers at least 41 of the 44 queries and answers none wrongly. |
| **B3** | `L5`'s nearest reference names all 44 correctly. |
| **B4** | **Faithfulness on held-out queries.** Every one of the 44 queries reads within its own type's certified radius `r_T`, so no absence certificate is issued against a query's own type. |
| **B5** | **Frozen path.** Every evaluation case present before the round returns the same answer and refusal after it. |
| **B6** | **Secondary.** Against the 23-reference table, the answer rule answers none of the 44 wrongly. |
| **C1** | Each candidate's minimum norm and kissing number agree with an enumeration of its short vectors, and its quantiser passes the local check (no lattice point at a minimal-vector step from the answer is nearer) on 200 declared vectors. |
| **C2** | **Primary of C.** Both empty norms are filled by kept candidates. |
| **C3** | The filled ladder answers no query wrongly, all three visiting orders agree, it matches the after-the-fact oracle, and it answers at least the repaired ladder's 467. |

**The predictions, stated as numbers before they are taken.**

* *A.* Stage 1 reaches 11 or 12 of the 13 (the pilot's rarest types are
  `A_8^3`, never walked, and `D_4^6`, once in 1,591); stage 2 supplies
  `A_8^3`. A3: `B` about `0.43` (the closest pair stays `E_8^3`/`D_8^3`,
  whose limit is `4/9`), `W` below `0.08`, `ρ` between `0.1` and `0.4`.
  Holes whose components are all `A_n` read with zero spread, because every
  vertex has the one key `(n+1, 2)`.
* *B.* The joint reading's four failures sat on its two closest pairs; under
  `L5` the closest pair is `4/9` apart and the spreads at 1920 were at most
  `0.06`. Predicted: B3 met (44 of 44) and the answer rule answers 44 of 44.
  B4 is the risky mark: a translated or permuted centre is a different
  ensemble, and its shift is not bounded by the seed shift.
* *C.* Norm 2 is filled (the `D_n^k` lattices are coarser than `D_24` and
  conflate less). Norm 256 is the harder half: both rungs the scaling put
  there answered wrongly, and a coarse rung whose cell holds one wrong
  carrier is exactly the failure. Predicted: norm 2 filled, norm 256 left
  empty — C2 missed.

## 4. Controls

* **A2** is the control on Part A: a new hole whose arrival set is not its
  certified vertex set is reported and A3–A4 are read without it.
* **B1** is the control on Part B: the reproduction of the recorded 40 of 44.
* **The repaired ladder itself** (467 correct, 0 wrong) is re-measured beside
  every candidate ladder, so a change in the shared code would show.
* **The multiplicity count.** Phase 122 stood at 44 statistics. This round
  adds six `L5` cells (A), two classifier readings (B) and five candidate
  audits (C), so **57**. No bit score is computed.

## 5. What this round does not do

* It does not change the ladder's four readings, the existing deep-hole
  reports, the escalation's query set or the norm family's declared ladder.
* It does not re-take any stored ensemble.
* It does not claim faithfulness: absences are theorems under it, and the
  held-out queries are a test of it on this sample, not a proof.
* It does not extend the norm family beyond 2,048 or change the retirement
  rule.

## 6. Files

* `RequestProject/GLM/LatticeCompletion.lean` — L1.
* `glm_universal/reasoning/hole_census.py` — Part A: the three
  stages, the new ensembles, the 23-reference cells.
* `glm_universal/reasoning/configuration_classifier.py` — Part B.
* `glm_universal/reasoning/empty_rungs.py` — Part C.
* `glm_universal/reasoning/lattice_completion.py` — the marks.
* `python3 -m glm_universal.tools hole-census | configuration-classifier |
  empty-rungs` and `report hole configuration`.
* Tests: `test_hole_census.py`, `test_configuration_classifier.py`,
  `test_empty_rungs.py`.

## 7. The measurement

*Written after the measurement. §§0–6 above are as they were committed.*

The measurements are stored beside the digests of their sources:
`python3 -m glm_universal.tools hole-census --write` (the census and the
thirteen new ensembles), `patience-census --write` (the post-hoc follow-up,
§7.4), `configuration-classifier --write` (the 44 queries' profiles),
`empty-rungs --write` (the five candidates and the filling) and
`frozen-path --write` (B5). Every mark is read back by
`glm_universal.reasoning.lattice_completion.lattice_completion_report`.

### 7.1 The verdict

Partly. The configuration reading now answers in the deep-hole path: under the declared answer rule it names all 44 escalation queries correctly with no refusal, where the joint reading named 40, and issues 396 certified absences of which none is false. The declared walk reached all thirteen missing Niemeier types, but three of its centres failed the second certifying reading, so the pre-registered census certifies 20 of 23 types; a post-hoc re-reading with more patience certifies the other three, and over all 23 the configuration reading recognises every type with a ratio of 0.1929 at 7680 starts. Norm 2 is filled by `D12^2`; norm 256 stays empty, because both candidates answer six queries wrongly.

### 7.2 The marks

| mark | statement | result |
|---|---|---|
| L1 | the Lean file | **met**: `RequestProject/GLM/LatticeCompletion.lean`, 10 theorems and the reading `configReading` (`L5` as a `Reading`); `config_answer_sound`, `config_absent`, `config_radius_pos`, `uniform_floor` (all 253 pairs at least `4/9`), `constructionA_normSq_ge`; no `sorry`, and `#print axioms` shows `propext`, `Classical.choice`, `Quot.sound` only |
| A1 | a certified reference for all 23 types | **missed**: 20 of 23. The walk named all thirteen new types within 1,280 walks (stage 1 only; stages 2 and 3 were never needed), but the census's second certifying reading — 400 probes, patience 60 starts — returned 25, 28 and 29 vertices for the centres the walk named `A_17 E_7`, `A_5^4 D_4` and `D_4^6`, sets the diagram reader cannot identify |
| A2 | the control on the new holes | **met**: 20 of 20 (10 certified new holes × 2 seeds) arrival sets are exactly the certified vertex set with the label's keys |
| A3 | `Q0 = 23` and `ρ < 1` at `(L5, 7680)` | **missed** as declared (`Q0 = 20` of the 20 certified; `ρ = 0.1720 < 1`, `W = 0.0348` at `E_8^3`, `B = 0.4043` at `E_8^3`/`D_8^3`) |
| A4 | the per-hole criterion certifies all 23 | **missed** as declared: 20 of the 20 certified |
| B1 | the stopping rule | **met**: the rebuilt query set gives the joint reading 40 of 44, as recorded |
| B2 | at least 41 answered, none wrongly | **met**: 44 answered, 44 correct, 0 wrong, 0 refused |
| B3 | `L5`'s nearest reference names all 44 | **met**: 44 of 44 |
| B4 | faithfulness on the held-out queries | **met**: 44 of 44 read inside their own type's certified radius, so 0 of the 396 absences issued is false |
| B5 | the frozen path | **met**: 178 of 178 baseline cases keep their status (answered or refused); the text is identical for 169, and each of the nine that moved has a declared cause (§7.5) |
| B6 | the larger reference table answers none wrongly | **met**: against the 20 references the census certified, 44 correct, 0 wrong, 0 refused (836 absences, 0 false); against all 23 (with the post-hoc three) the same, 968 absences, 0 false |
| C1 | candidates' norms, kissing numbers and quantisers | **met**: all five agree with an enumeration (`D12^2` 2/528, `D8^3` 2/336, `D4^6` 2/144, `8E8^3` 256/720, `8D4^6` 256/144) and 0 quantiser failures on 200 vectors each |
| C2 | both empty norms filled | **missed**: norm 2 is filled by `D12^2`, the first candidate (kept: the audit retires no rung). At norm 256, `8E8^3` answers 6 queries wrongly (uniquely answering 5) and `8D4^6` answers 6 wrongly (uniquely answering 3); each is retired under clause 1, so norm 256 stays empty |
| C3 | the filled ladder is safe and no weaker | **met**: 467 correct, 0 wrong, 101 refused, the same in all three visiting orders, equal to the oracle's 467 and to the repaired ladder's |

**Scored as declared: 10 of 14** (L1, A2, B1–B6, C1, C3). The three part-A misses
are one event — three centres the second reading could not finish — and
§7.4 reads them post hoc. C2 was missed as predicted.

### 7.3 The `L5` cells

Over the references the census certified (the ten old holes from their stored
ensembles, the ten new ones from this round's), `Q0` is 20 of 20 at every size:

| starts | `W` (worst hole) | `B` (closest pair) | `ρ` | per-hole |
|---|---|---|---|---|
| 240 | 0.2010 (`A_11 D_7 E_6`) | 0.3831 | 1.0494 | 20 |
| 480 | 0.1741 (`A_11 D_7 E_6`) | 0.2891 | 1.2041 | 19 |
| 960 | 0.1187 (`D_16 E_8`) | 0.3025 | 0.7844 | 20 |
| 1920 | 0.0578 (`D_16 E_8`) | 0.3793 | 0.3048 | 20 |
| 3840 | 0.0526 (`D_10 E_7^2`) | 0.4124 | 0.2550 | 20 |
| 7680 | 0.0348 (`E_8^3`) | 0.4043 | 0.1720 | 20 |

The closest pair is `E_8^3`/`D_8^3` at every size, as predicted.

**The predictions.** Part A: stage 1 was predicted to reach 11 or 12 of the
13 and stage 2 to supply `A_8^3`; the walk in fact reached all 13 (`A_8^3`
first at walk `i = 1082`, `D_4^6` at `i = 15`), so stage 2 never ran.
`B ≈ 0.43`: 0.4043. `W < 0.08`: 0.0348 (0.0390 over all 23). `ρ` between 0.1
and 0.4: 0.1720 (0.1929 over all 23). Holes whose components are all `A_n`
read with zero spread: confirmed for all eight (`A_24`, `A_12^2`, `A_8^3`,
`A_6^4`, `A_4^6`, `A_3^8`, `A_2^12`, `A_1^24`). Part B: predicted 44 of 44
for both B3 and the answer rule — both held; B4, the risky mark, held.
Part C: predicted norm 2 filled and norm 256 empty — exactly so.

### 7.4 Post hoc: the three centres re-read with more patience

*Declared after the census and labelled post hoc wherever it is reported
(`reasoning/patience_census.py`).* The same three centres, the same reference
seed and the frozen path unchanged, with 1,600 probes and a patience of 240
starts. All three are certified as the type the walk named: `A_17 E_7` (26
vertices, 196 starts), `A_5^4 D_4` (29, 254 starts) and `D_4^6` (30, 169
starts); each needed more than the census's 60-start patience. Each was then
run through the ensemble at both seeds to 7680 starts. Over all 23:

* the control holds for 26 of 26 (13 new holes × 2 seeds);
* at 7680 starts `Q0 = 23`, `ρ = 0.1929` (`W = 0.0390` at `A_17 E_7`,
  `B = 0.4043`), and the per-hole criterion certifies 23 of 23 — so A1, A3
  and A4 would be met on the follow-up;
* at 240 starts `ρ = 2.1842` (the new `A_5^4 D_4` reads 0.4184 from its own
  reference there), and from 960 starts on the ratio is the same as over the
  20.

This answers lattice item 7 for the reference holes, post hoc: every
Niemeier type now has a reference centre that the frozen path certifies and
that the configuration reading recognises under a seed change.

### 7.5 The frozen path (B5)

The baseline is the answer of every evaluation case before the round touched
the answering path, as the query-escalation store had recorded it
(`reasoning/_data/lattice_frozen_baseline.json`). That store was taken before
Phase 121, so figures the tree measures of itself had already moved by the
start of this round.

`python3 -m glm_universal.tools frozen-path` asks every one of the 178
baseline cases again. All 178 are still present and **all 178 keep their
status**: no case moved between answered and refused. The answer text is
identical for 169, every deep-hole report among them (`report deep holes`,
`hole classifier`, `hole ladder`, `hole failures`). The nine that moved are
each listed with a declared cause, none undeclared:

* **four from this round's own additions**, which self-describing reports
  count: the refusal for an unknown report subject lists one more subject
  (`hole configuration`); `report pipeline` has one more row (33 of 33 pass
  all six stages); `report language` counts one more evaluation question of
  the undescribed kinds (159); `report query escalation` counts 179 cases
  (safety still holds over all of them);
* **five figures the tree measures of itself**, which moved with the Lean
  corpus and the stored bytes since the baseline was taken: `report lean`
  (4,903 declarations, all read back exactly), `report retrieval`,
  `report relay` and `report anonymous` (whose query strides are drawn from
  the declarations: 818 queries, the relay still ahead of the text control
  on every set and losing none, the text search still within twice chance
  in the anonymous register), and `report generated`.

The evaluation's own pins for `report relay` and `report anonymous` were
re-pinned to the new figures, as in earlier rounds; their claims are
unchanged. The new case, `report-hole-configuration`, passes.

### 7.6 What is left

* **Norm 256** stays empty. Both candidates were retired because they
  answered wrongly, not because they added nothing: each answered queries no
  other rung could (5 and 3). A coarse rung that does not conflate there needs
  a different construction from the scaled `√2`-lattices tried here.
* **Patience as a parameter.** The census's second reading used the first
  round's convention (patience 60), and three of the 23 types needed 169–254
  starts. A rule that sets the patience from the vertex count would have
  certified them as declared.
* **The other report subjects** still name a deep hole with the ladder's
  readings; only `report hole configuration` answers by `L5`. *(Taken by
  Phase 149: `report hole classifier`, `ladder` and `failures` each keep
  their answer and add an `L5` clause —
  [`HOLE_REPORTS_L5_STUDY.md`](HOLE_REPORTS_L5_STUDY.md).)*
* **The statistics count** is now 57 (§4); no bit score was computed.
