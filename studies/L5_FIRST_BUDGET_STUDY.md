# `L5` at the first round's budget — the 44 queries re-profiled at 240 starts

## Tier 0 — the coarse read

**Question.** Does the configuration reading `L5`'s answer rule name the escalation round's 44 queries at 240 starts, the classifier round's budget, where Phase 149 had measured them only at 1920?

**Verdict.** At the first round's budget `L5` names 43 of the 44 queries correctly and refuses the 44th; nothing is named wrongly. The refused query is the sibling centre of walk 6 (`E_8^3`): its nearest reference is the right one, but at 240 starts its distance is not below that reference's certified radius. The classifier round's sanity query holds: 10 of 10 seed queries are named as themselves. The same query is the only false absence of the 397 absences issued, so an absence at 240 starts is not certified for every query, as it is at 1920. 3 of 3 marks were met.

**Deciding figure.** 3 of 3 marks; at 240 starts 43 correct, 0 wrong, 1 refused of 44 (1920 starts: 44, 0, 0); seed queries 10/10; 43 of 44 inside their own radius, all 43 answered; 397 absences, 1 false (1920: 396, 0); prefix property 6/6 seeds.

**Recomputed by.** `glm_universal.reasoning.l5_first_budget.l5_first_budget_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration** for Phase 152, the first follow-up of
[`STATUS.md`](../STATUS.md) §2.2 (*`L5` in the other deep-hole reports, the
rest*, left by Phase 149,
[`HOLE_REPORTS_L5_STUDY.md`](HOLE_REPORTS_L5_STUDY.md) §7.4). §§0–6 were
committed with the measurement code, before the measurement was run; §7 is
what came out.

**What the follow-up asked.** Phase 149 found that `L5` passes the
escalation gate already at 240 starts, the first (classifier) round's budget,
where the joint reading needed 1920. But the 44 queries of the escalation
round were profiled only at 1920 starts (`configuration_queries.STARTS`), so
whether `L5`'s answer rule names them at 240 starts was not measured. This
round measures it. It is a measurement, not an answering-path change: no
answer moves, and no evaluation case is added.

**How.** The ensembles are the declared ones
(`deep_hole_escalation.emissions`) at the same centres and seeds as
`deep_hole_failures.plan`, cut at 240 starts. A 240-start ensemble is the
first 240 starts of the 1920-start one, because the offsets of a seed are
drawn in order from one sweep (`deep_hole_classifier.offsets`); P0 checks
this seed by seed. The ten references and the 44 queries are profiled under
`L5` and read by the same answer rule
(`configuration_classifier.classify_queries`), with the certified radii
(half the distance to the nearest other reference) of the 240-start
reference table.

**What was known before this was written.** The 1920-start figures (44 of 44
correct, 10 of 10 seed queries, 44 inside their own radius), recomputed from
the stored profiles while the code was written. One 240-start reference
ensemble was run to time it. **No 240-start query profile had been computed
when this was committed.**

## 1. What is proved before any code

Nothing new. The answer rule and its soundness are
`GLM.HoleReportsL5.rule_sound` (the rule's answer is the strict nearest
reference, for any reading) and `rule_fires_of_resolvesAt` (the rule fires
wherever the per-type criterion certifies), both from Phase 149; they hold
for any budget, so they hold at 240 starts. R1 is the second one on the
data.

## 2. The rule

As §0: `configuration_classifier.name` — the nearest reference by
configuration distance, answered only when the distance is below that
reference's certified radius, refused otherwise.

## 3. The questions

The 44 used queries of the escalation round (ten seed queries, the
transformed holes, the sibling centres), and the ten references at the
reference seed, each at 240 starts.

## 4. The marks, declared before the measurement

| mark | claim |
|---|---|
| **P0** | for every seed the 54 ensembles use, the 240 offsets are the first 240 of the 1920 |
| **W1** | 0 of the 44 queries is answered wrongly at 240 starts: the rule refuses rather than misnames |
| **R1** | every query inside its own type's certified radius at 240 starts is answered |

Reported, with **no threshold declared**, because either outcome answers the
follow-up: the ten seed queries named as themselves (the classifier round's
sanity query, asked of `L5`), and the counts answered correctly, refused and
inside their own radius, beside the 1920-start figures.

## 5. What would count against

W1 failing would mean the rule misnames a query at the smaller budget even
though it refuses outside its radii. R1 failing would contradict
`rule_fires_of_resolvesAt` on the data, which would point to a defect in the
code. Fewer than 44 answered is not a failure of a mark; it is the answer to
the question.

## 6. What is not claimed

The first round's own reading (the arrival-share profile) is not re-run; the
comparison is `L5` at two budgets, and `L5` against the record of the first
round. The 480-start pass observed for one type without its per-type
criterion (Phase 149 §7.4) is not addressed. Nothing in the answering path
changes.

## 7. What came out

`python3 -m glm_universal.tools l5-first-budget` (stored in
`reasoning/_data/l5_first_budget.json`, digest-guarded).

In short: at the first round's budget `L5` names 43 of the 44 queries
correctly and refuses the 44th; nothing is named wrongly. No mark was missed.

### 7.1 The marks

| mark | result | met |
|---|---|---|
| **P0** | the 240 offsets are the first 240 of the 1920 for all 6 seeds the 54 ensembles use | yes |
| **W1** | 0 of 44 answered wrongly | yes |
| **R1** | 43 queries inside their own radius, 43 answered | yes |

### 7.2 The reported counts

| | 240 starts | 1920 starts |
|---|---|---|
| seed queries named as themselves | 10 of 10 | 10 of 10 |
| correct / wrong / refused | 43 / 0 / 1 | 44 / 0 / 0 |
| nearest reference the right one | 44 of 44 | 44 of 44 |
| inside their own radius | 43 of 44 | 44 of 44 |
| absences issued / false | 397 / 1 | 396 / 0 |

The refused query is `walk 6 · sibling centre` (truth `E_8^3`). Its nearest
reference is `E_8^3`, but at 240 starts its distance is not below that
reference's certified radius (half the distance from `E_8^3` to the nearest
other reference in the 240-start table), so the rule refuses rather than
answer. The same distance is above the radius, so the rule also counts
`E_8^3` among the query's absences. That absence is false: an absence is a
theorem only for a query inside its own type's radius (the faithfulness
condition of `GLM.LatticeCompletion.config_absent`), and this query is not.
It is the only false absence at either budget.

### 7.3 What this answers

Phase 149 found that `L5` passes the escalation gate already at 240 starts.
The gate is that every reference recognises itself under a seed change; the
44 queries are a harder test (transformed holes and sibling centres). At 240
starts the rule still never misnames one, and answers all but one. The
sanity query that stopped the classifier round in its own reading holds at
the same budget under `L5`.

### 7.4 What is left

* An absence issued at 240 starts is not certified for every query: one of
  397 is false, on the one query outside its radius. Nothing in the
  answering path reads `L5` at 240 starts, so no answer states it; a reading
  at that budget would have to refuse its absences as well as its answer
  outside the radius.
* The 480-start pass observed for one type without its per-type criterion
  (Phase 149 §7.4) is still observed, not certified.
