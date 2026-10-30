# The budget rule in the answering path — a deep hole read to its certificate

## Tier 0 — the coarse read

**Question.** If the answering path reads a deep hole under the budget rule of Phase 124 (no barren stop, 1056 starts) instead of a patience, does it certify every hole the walk reaches without moving any answer the evaluation pins?

**Verdict.** Yes. Under the budget rule every one of the 256 held-out walks has its deep hole certified, where the walk's own patience reading certified 225. Wherever the patience reading had certified, the rule gives the same type and the same vertex set, and no reading ran to the budget. The answering path now reads a hole on request (the `hole` kind), and `report deep holes` reads under the rule with the same five types. The frozen path keeps all 202 statuses; the only moved texts have declared causes. 8 of 8 measured marks were met, and L1 by the build.

**Deciding figure.** 8 of 8 measured marks and L1; held-out walks 256/256 certified under the rule (frozen walk reading 225), 0 disagreements, 0 type disagreements with Phase 124 over 256 centres; 0 readings at the budget, median 25 and maximum 174 starts; battery 11/11 as declared, column 3 8/8, mutants 16/16 rejected; frozen path 202/202 same status, 199 same text.

**Recomputed by.** `glm_universal.reasoning.budget_reading_study.budget_reading_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration** for Phase 147, item 2 of [`STATUS.md`](../STATUS.md)
§2.1 (*the budget rule in the walk and the answering path*, left by Phase
124, [`PROBE_BUDGET_STUDY.md`](PROBE_BUDGET_STUDY.md) §7.4). §§0–6 were
committed with the Lean file and the answering-path code and before the
module that takes the measurement had been run; §7 is what came out.

**Where the system stood.** Phase 124 declared the rule — the certifying
reading of a deep hole stops on its completeness certificate or after a
budget of 1056 starts, never after a run of barren starts — and proved the
budget enough under its model (`GLM.ProbeBudget`). It applied the rule only in
a measurement module. The answering path still read with a patience:
`report deep holes` ran `deep_holes.deep_holes_report(walks=3)` with the
walk's reading (200 starts, patience 40), and no question could ask for one
hole to be read at all.

**What this round does.**

1. A new module, `reasoning/hole_reading.py`, is the answering path's reader
   of a deep hole under the rule. At the covering radius it reads with no
   barren stop and a budget of 1056 starts. Below it, start 0 already decides
   that there is no type to name, and the frozen convention (400 starts,
   patience 60) is kept for the count of nearest points it reports.
2. `report deep holes` reads its walks and its two constructions under the
   rule.
3. A new query kind, **`hole`**, reads one carrier under the rule:
   `hole walk <n>` (the declared walk seeds `20260825 + 977 n`), `hole octad
   pair`, `hole dodecad triangle`, or `hole <24 coordinates>`. It answers with
   the certified Niemeier type, or refuses as `lattice-point`, `shallow`,
   `uncertified`, `dimension` or `malformed`. Column 3 re-reads the hole in a
   fresh interpreter and checks the certificate from the vertex set.

**What is not changed, and why.** `deep_holes.classify_carrier` keeps its
default arguments, and so do the frozen walk parameters of the measurement
modules (`deep_hole_classifier.WALK_PROBES`/`WALK_PATIENCE`, the census
convention of `probe_budget`). Every caller passes its parameters explicitly,
so no answer reads the defaults. But six stored measurements (the classifier,
the escalation, the failures, the hole census, the patience census and the
probe budget) are kept beside a digest of `deep_holes.py`, so editing the
default would invalidate all six over a parameter no caller reads. The rule
reaches the answering path through `hole_reading` instead. The frozen
parameters remain the records of the rounds that declared them.

**Order of work, stated plainly.**

1. *What was known before this was written.* Phase 124's stored readings: on
   the 256 held-out walks (indices 3000–3255), the walk's own reading
   certified 225 of the 256 deep holes, and the rule, read at the reference
   seed, certified all 256. While building the reader, these were run once:
   `report deep holes`'s census under both parameter sets (the same five
   types, every case certified both ways, the octad-pair reading taking 195
   starts under the patience and 240 under the rule), the `hole` reader on
   walks 0 and 1, the two constructions and two points that are not deep
   holes, and walk 3006 (one of the 31 the walk's own reading left
   uncertified; certified `D_16 E_8` after 83 starts under the rule), to
   choose an evaluation case.
2. *The Lean file before this was committed.* `RequestProject/GLM/BudgetReading.lean`
   was written and built first (§1). The frozen-path baseline (§3) was taken
   after it and before any answering-path code changed.
3. **No held-out walk had been read under the rule inside the walk, and the
   battery of §3 had not been asked, when this was committed.**

## 1. What is proved before any code

`RequestProject/GLM/BudgetReading.lean` (namespace `GLM.BudgetReading`), no
`sorry`, standard axioms only. The model: everything after start `n` is a
function of `n` (the sweep is deterministic). `V n` is the set of vertices in
hand, growing and never more than the hole's vertex set `T`. `cl` is the
closure step run after the probe stops. `cert n` is the stop certificate,
which holds only when the closed set is `T`. The reading is certified at its
stop `s` when `cl (V s) = T`.

* `certified_mono` — once certified, every later stop is certified.
* `budget_agrees` — **the frozen path is kept**: whenever the patience
  reading is certified, the budget reading with any budget at least as large
  is certified, and both return `T`, so the same type. The number of starts
  may differ.
* `budget_refuses_only_without_cert` — the budget reading is uncertified only
  if no start inside its budget carries the stop certificate.
* `patience_may_refuse` — a concrete reading that the patience stops before
  its certificate and the budget certifies: the only way an answer can move.

## 2. The rule

As in [`PROBE_BUDGET_STUDY.md`](PROBE_BUDGET_STUDY.md) §2. The budget is 1056,
equal to `probe_budget.BUDGET` (a test holds the two together). Readings below
the covering radius name no type, whatever stops them.

## 3. The sets and the questions, declared here

**The held-out walks.** Phase 124's walk indices 3000–3255. Each walk is run
once, and its hole is read from the same walk twice: by the walk's frozen
reading (200 starts, patience 40, the walk's seed and its active vertices) and
under the rule (1056 starts, no barren stop, the same seed and vertices). The
second is exactly what `hole walk <n>` reads.

**The frozen-path baseline.** All 202 evaluation cases asked through the
session before the answering path moved
(`reasoning/_data/budget_guard_baseline.json`), shared with Phase 148.

**The battery** (13 questions):

| # | question | declared |
|---|---|---|
| R1 | `hole walk x` | refused `malformed` |
| R2 | `hole 1, 2, 3` | refused `dimension` |
| R3 | `hole` with 24 zeros | refused `lattice-point` |
| R4 | `hole` with 23 × `1/8` and one `3/8` | refused `shallow` |
| R5 | `hole the moon` | refused `malformed` |
| B1 | `hole walk 0` | `E_8^3` |
| B2 | `hole walk 1` | `D_24` |
| B3 | `hole walk 2` | `A_12^2` |
| B4 | `hole octad pair` | `A_1^24` |
| B5 | `hole dodecad triangle` | `A_2^12` |
| B6 | `hole walk 3006` | `D_16 E_8` |
| B7 | `deep hole of walk 3013` | read; outcome not predicted |
| B8 | `hole walk 3067` | read; outcome not predicted |

**New evaluation cases:** `hole-walk`, `hole-octad-pair`,
`hole-patience-refused` (walk 3006), `hole-lattice-point`, `hole-malformed`.

## 4. The marks, declared before the measurement

| mark | claim |
|---|---|
| **L1** | `BudgetReading.lean` builds with the full `lake build`, no `sorry`, standard axioms only |
| **H1** | **primary**: under the rule, every held-out walk that reaches a deep hole has its hole certified |
| **H2** | wherever the walk's frozen reading certified a held-out hole, the rule gives the same type and the same vertex set (`budget_agrees`) |
| **H3** | no reading under the rule runs to the budget |
| **H4** | on every held-out hole the rule's type inside the walk is the type Phase 124 stored for the same centre (read at the reference seed) |
| **R1** | `report deep holes` under the rule exhibits the same types as under the frozen parameters, with its walks and constructions certified |
| **Q1** | the battery comes out as declared (R1–R5, B1–B6); B7 and B8 are sound (answered and verified by column 3, or refused); every answered question's column-3 script verifies, and two mutants of each (a wrong type, a vertex count plus one) are rejected |
| **W1** | the wiring census passes with `hole_reading` reached from the answering path; no earlier evaluation case reads as `hole` |
| **F1** | the frozen path: every baseline case is present and keeps its status (answered or refused); every moved text has a declared cause (`budget_guard_frozen.DECLARED_CAUSES`: the tree's self-measurements, the refusal's list of kinds, the language report, the query-escalation report and the route table) |

**Predictions.** H1: 256 reached, 256 certified. H2 holds by theorem, over
225 holes. H3: maximum starts below 600. H4 holds (a hole's type is the
hole's). R1: the same five types. `report deep holes` keeps its answer text,
because the text names no start count. Q1: B7 and B8, two of the walks the
frozen reading left uncertified, are predicted certified, with moderate
confidence. F1 holds.

## 5. What this round does not do

* It does not change `deep_holes`, the walk, the census modules, their stored
  measurements or their frozen parameters.
* It does not put the rule into `report hole classifier`, `hole ladder`,
  `hole failures` or `hole configuration`. Those read stored measurements of
  their own rounds (item 3 of `STATUS.md` §2.1 is about them).
* It proves nothing about the deterministic sweep beyond the model of §1.

## 6. Files

* `glm_lean/RequestProject/GLM/BudgetReading.lean` — §1.
* `glm_universal/reasoning/hole_reading.py` — the reader, the
  request grammar.
* `glm_universal/runtime/session.py` (`_solve_hole`),
  `runtime/parser.py` (the `hole` kind), `runtime/reports/lattice_geometry.py`
  (`report deep holes`), `runtime/tct_engine.py` (the `hole` template; the
  census template under the rule), `runtime/toolbox.py` (the census).
* `glm_universal/reasoning/budget_reading_study.py` — the marks;
  `python3 -m glm_universal.tools budget-reading [--write]`.
* `glm_universal/reasoning/budget_guard_frozen.py` — F1, shared with
  Phase 148; `tools budget-guard-frozen [--write]`.
* `glm_universal/tests/test_budget_reading.py`.

## 7. What came out

Taken with `python3 -m glm_universal.tools budget-guard-frozen --write`,
then `tools budget-reading --write --jobs 8`; stored in
`reasoning/_data/budget_guard_frozen.json` and
`reasoning/_data/budget_reading_study.json` beside the digests of the modules
they read. **8 of 8 measured marks were met, and L1 by the build.** The frozen path keeps all 202 statuses.

### 7.1 The marks

| mark | result | met |
|---|---|---|
| L1 | `BudgetReading.lean` builds in the full `lake build` (8248 jobs), no `sorry`; `#print axioms` names only `propext`, `Classical.choice`, `Quot.sound` (`patience_may_refuse` none) | yes |
| H1 | 256 of 256 held-out walks reached a deep hole, and 256 of 256 were certified under the rule; the frozen walk reading certified 225 | yes |
| H2 | 0 disagreements of type or vertex set on the 225 holes the frozen reading certified | yes |
| H3 | 0 readings ran to the budget; the median reading stopped at 25 starts, the longest at 174 | yes |
| H4 | 0 type disagreements with the types Phase 124 stored, over 256 centres | yes |
| R1 | `report deep holes` exhibits the same five types under the rule (`A_12^2`, `A_1^24`, `A_2^12`, `D_24`, `E_8^3`), walks and constructions certified; the octad-pair midpoint takes 240 starts under the rule against 195 under the frozen parameters | yes |
| Q1 | R1–R5 and B1–B6 as declared (11 of 11); the two reads B7 and B8 sound (2 of 2); column 3 verifies 8 of 8 answered questions and rejects 16 of 16 mutants | yes |
| W1 | the wiring census passes with `hole_reading` reached from the answering path; no earlier evaluation case reads as `hole` | yes |
| F1 | 202 of 202 baseline cases present and keep their status; 199 keep their text; the three moved texts (`unknown-nonsense`, `report-language`, `report-query-escalation`) each have a declared cause | yes |

### 7.2 What the rule moved

The 31 held-out walks the frozen reading left uncertified are all certified
under the rule, after 41 to 174 starts — past the walk's 200-start, patience-40
reading only because its barren stop fired first. Their types spread over eleven
Niemeier types (`E_8^3` eleven times, `D_10 E_7^2` four, `D_16 E_8` three,
and `D_8^3`, `E_6^4`, `A_17 E_7`, `D_12^2`, `A_11 D_7 E_6` twice each,
`A_12^2`, `A_15 D_9` and `A_7^2 D_5^2` once). This is `patience_may_refuse`
seen in the data: a patience can stop where the certificate is still ahead,
and the rule cannot (`budget_refuses_only_without_cert`).

The two predictions left open came out certified, as predicted with moderate
confidence: B7 (`deep hole of walk 3013`) is `A_12^2` from 26 vertices, and
B8 (`hole walk 3067`) is `D_10 E_7^2` from 27 vertices. B6 (`hole walk 3006`)
is `D_16 E_8` from 26 vertices at 83 starts, where the frozen reading stopped
at 25 vertices.

`report deep holes` kept its answer text, as predicted: the frozen-path
comparison shows it among the 199 unchanged texts.

### 7.3 What it answers

```
hole walk 3006
  walk 3006 (seed 23197687) sits in a deep hole of type D_16 E_8 (Coxeter
  number 30), from 26 vertices certified complete by the marked-barycentre
  identity ...
hole 0, 0, ..., 0
  unsolved: hole (lattice-point): the given point is a lattice point ...
```

Column 3 re-reads the hole from the walk's seed under the same rule in a fresh
interpreter: it checks the depth with the exact decoder, that every vertex
found lies at the covering radius, and the type, the vertex count and the
certificate.

### 7.4 What is left

* The other deep-hole reports (`report hole classifier`, `hole ladder`,
  `hole failures`) still read stored measurements of their own rounds under
  the patience they were taken with; moving them is the *`L5` in the other deep-hole
  reports* item of `STATUS.md` §2.1, under its own frozen-path comparison.
* `deep_holes.py` keeps its frozen defaults (200 starts, patience 40 in the
  walk; 60 in `classify_carrier`), because six stored measurements digest that
  file. No caller in the answering path uses those defaults any more; changing
  them is a re-take of those six measurements, not an answer change.
* The `hole` kind reads a walk, the two constructions or 24 coordinates; it
  does not read a hole named by its Niemeier type.
