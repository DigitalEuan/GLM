# The configuration reading in the other deep-hole reports — each round's question asked of `L5`

## Tier 0 — the coarse read

**Question.** Can the three deep-hole reports that still named a hole only with their own rounds' readings — `report hole classifier`, `report hole ladder` and `report hole failures` — answer by the configuration reading `L5` as well, keeping each round's record verbatim, under a frozen-path comparison of the whole evaluation?

**Verdict.** Yes. Each of the three reports keeps its round's answer verbatim and adds what `L5` says to that round's question. For the classifier, the sanity query that stopped the first round holds at `L5` for 10 of 10 seed queries, and all 44 queries are answered correctly. For the ladder, `L5` passes the escalation gate at every one of its 8 measured sizes, already at 240 starts, where the joint reading needed 1920. At 480 starts it passes with ρ above one, which is the global criterion being sufficient but not necessary. For the failures, `L5` answers all four of the joint reading's failures correctly and meets the criterion for 10 of 10 types at 1920 starts. The whole evaluation keeps all 212 statuses, and only the three intended texts moved, each with its old text as its prefix. 6 of 6 measured marks were met, and L1 by the build. Taking column 3 also found that the `report hole ladder` script had never verified, because its template missed one key. That is now fixed.

**Deciding figure.** 6 of 6 measured marks and L1; seed queries 10/10 and 44/44 answered correctly at `L5`; gate at 8/8 sizes, smallest 240 starts, passing with ρ ≥ 1 at 480; 4/4 joint failures answered correctly, 10/10 types certified at 1920 starts (ρ = 0.3048); battery 4/4 answered, 4/4 scripts verify, 8/8 mutants rejected; frozen path 212/212 same status, 209 same text, 3/3 prefixes kept, 0 undeclared.

**Recomputed by.** `glm_universal.reasoning.hole_reports_l5_study.hole_reports_l5_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration** for Phase 149, item 1 of [`STATUS.md`](../STATUS.md)
§2.1 (*`L5` in the other deep-hole reports*, left by Phase 123,
[`LATTICE_COMPLETION_STUDY.md`](LATTICE_COMPLETION_STUDY.md) §7.6). §§0–6
were committed with the Lean file and the answering-path code, before the
frozen-path comparison was run; §7 is what came out.

**What the item asked.** Since Phase 123 only `report hole configuration`
answers by `L5`. The other three deep-hole reports each report a closed
round: the first round (240 starts, the arrival-share profile, stopped at its
sanity query), the escalation ladder (four readings at four sizes, passing
the gate only at the joint reading's extension rung, 1920 starts) and the
failure round (the four queries the joint reading names wrongly). Each is a
record, and a record is not rewritten. So the round gives each report a
**clause**: the old answer is kept verbatim and the new text is appended,
saying what `L5` answers to the question that round asked.

* **classifier** — the round's question was whether the arrivals name the
  hole, and its stopping rule the sanity query (the same hole under a bare
  seed change). `L5`'s answer: the ten seed queries through the answer rule,
  and all 44 queries.
* **ladder** — the gate is that every reference recognises itself under a
  seed change. `L5`'s answer: the gate at every ensemble size the
  configuration reading was measured at, the smallest size that passes, and
  the sizes where it passes with `ρ ≥ 1`.
* **failures** — `L5`'s answer: each of the joint reading's four failures
  through the answer rule at the same cell (1920 starts), and `L5`'s own
  criterion type by type there.

**What was known before this was written.** Phase 123's stored figures
(44 of 44 answered correctly under the rule; `L5` passes the gate at every
size of Phase 122's cells). While building the answering path the three
readings of `reasoning/hole_reports_l5.py` were run once, and the three
reports with column 3 and one mutant each. Running column 3 found that the
`report hole ladder` template never recomputed the `winner_is_extension` key
its report states, so that report's script had never verified; the template
now recomputes it. The baseline of the whole evaluation was taken before any
answering-path file was edited; the Lean file was written while it was being
taken, before it reached `report lean`, so the baseline's Lean declaration
count already includes it (this sentence was added at the close). **The frozen-path comparison had not been run
when this was committed.**

## 1. What is proved before any code

`RequestProject/GLM/HoleReportsL5.lean` (namespace `GLM.HoleReportsL5`), on
top of `GLM.DeepHoleFailure`; no `sorry`, standard axioms only.

* `rule_fires_of_resolvesAt` — if a type's per-type criterion holds at spread
  `w` and a query lies within `w` of its reference, the answer rule fires: the
  rule is never more conservative than the criterion the failure round reads.
* `rule_sound` — the answer rule makes its answer the strict nearest
  reference, for any rung (`config_answer_sound`, stated for an abstract
  reading).
* `gate_of_rule` — if every re-read query satisfies the rule against its own
  reference, every reference recognises itself: the gate, query by query,
  with no global criterion.
* `criterion_not_necessary` — a two-reference table on the line where the
  global criterion fails at the measured spread and every query is still
  named correctly.

## 2. The rule

As §0. The clauses read the stores that already exist
(`configuration_queries`, `share_ensemble`); nothing decodes a lattice point.
Each report's column-3 template recomputes the `L5` keys beside the round's
own.

## 3. The questions

The battery: `report hole classifier`, `report hole ladder`, `report hole
failures`, and `report hole configuration` (unchanged, the control). No
evaluation case is added.

## 4. The marks, declared before the measurement

| mark | claim |
|---|---|
| **L1** | `HoleReportsL5.lean` builds with the full `lake build`, no `sorry`, standard axioms only |
| **C1** | at `L5` the classifier's sanity query holds (10 of 10 seed queries named as themselves) and the 44 queries are answered 44 correctly, 0 wrongly |
| **D1** | at `L5` the escalation gate passes at every measured size, the smallest at 240 starts (the first round's budget) |
| **E1** | each of the joint reading's 4 failures is answered correctly by `L5`'s rule, and at 1920 starts `L5` meets the criterion for every reference type with `ρ < 1` |
| **R1** | every query inside its own type's certified radius is answered (`rule_fires_of_resolvesAt` on the data) |
| **Q1** | the four reports answer, three carry the `L5` clause, every column-3 script verifies, and two mutants of each are rejected (one of the round's own keys; an `L5` key, or a second own key for the control) |
| **F1** | every evaluation case of the baseline frozen before the answering-path edit (`reasoning/_data/hole_l5_baseline.json`) is present with the same status; every moved text has a declared cause; the three reports' old texts are kept verbatim as prefixes |

## 5. What would count against

C1, D1 or E1 failing would mean `L5` does not answer the earlier rounds'
questions as Phase 123's stored figures suggest. F1 failing on a status, or
on a prefix, would mean the clause rewrote a record or moved an answer it
had no business moving.

## 6. What is not claimed

The clauses do not re-run the earlier rounds and do not change their
verdicts: the first round still stopped at its sanity query, and the joint
reading still has four failures. `L5` was measured after those rounds and
with more starts (1920 for the queries) than the first round used (240); the
comparison is across readings, and it is stated as such.

## 7. What came out

`python3 -m glm_universal.tools hole-reports-l5` (stored in
`reasoning/_data/hole_reports_l5.json`, digest-guarded).

In short: each report keeps its round's answer verbatim and adds the `L5`
clause; the whole evaluation keeps all 212 statuses, and only the three
intended texts moved. No mark was missed. The ladder's column-3 script, whose
template missed one key, is fixed (§7.3).

### 7.1 The marks

| mark | result | met |
|---|---|---|
| **L1** | `HoleReportsL5.lean` builds in the full `lake build`; no `sorry`; `propext`, `Classical.choice`, `Quot.sound` only | yes |
| **C1** | seed queries 10 of 10 named as themselves; 44 correct, 0 wrong, 0 refused of 44 | yes |
| **D1** | the gate passes at 8 of 8 sizes (240 … 30720 starts), the smallest at 240 | yes |
| **E1** | the four failures (`hole 5 · translation`, `hole 7 · translation`, `hole 9 · negation`, `hole 9 · permutation`) all answered correctly; 10 of 10 types certified at 1920 starts, ρ = 0.3048 | yes |
| **R1** | 44 queries inside their own radius, 44 answered | yes |
| **Q1** | 4 of 4 reports answered, 3 with the clause; 4 of 4 scripts verify; 8 of 8 mutants rejected | yes |
| **F1** | 212 of 212 present, 212 same status, 209 same text; the moved three are the declared ones, each with its old text as a verbatim prefix; 0 undeclared | yes |

### 7.2 What the clauses say

* `report hole classifier` now ends: *read at L5 (the configuration reading,
  1920 starts) under its answer rule the sanity query holds — 10 of 10 seed
  queries named as themselves — and the 44 queries are answered 44 correctly,
  0 wrongly and 0 refused.*
* `report hole ladder` now ends: *read at L5 the gate passes at 8 of 8
  ensemble sizes, first at 240 starts where the joint reading needed 1920, and
  at 480 starts it passes with rho at or above one, so the global criterion is
  sufficient, not necessary.*
* `report hole failures` now ends: *read at L5 under its answer rule the 4
  failures are answered 4 correctly, 0 wrongly and 0 refused, and at 1920
  starts L5 meets the criterion for 10 of 10 types (rho = 0.3048).*

### 7.3 A defect found on the way

Taking column 3 showed that the `report hole ladder` script had **never
verified**. The report states `winner_is_extension` in its expected values,
and the template never recomputed it, so every run ended in a missing key.
Nothing pinned the script's verdict, so the defect went unnoticed from the
escalation round on. The template now recomputes the key, and
`tests/test_hole_reports_l5.py` pins the script verifying.

### 7.4 What is left

* `L5` at 240 starts passes the gate, but the 44 queries were profiled only at
  1920 starts (`configuration_queries.STARTS`). Whether the answer rule names
  all 44 at the first round's 240 starts was not measured. That would need the
  queries re-profiled at 240.
* The 480-start cell is the one place where the gate holds without the global
  criterion. Its per-type criterion holds for 9 of 10 types, so the tenth
  type's self-recognition there is observed, not certified.
