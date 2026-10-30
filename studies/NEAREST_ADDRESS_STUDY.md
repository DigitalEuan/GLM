# The guarded read in `nearest` — a point no register holds, ranked and certified

## Tier 0 — the coarse read

**Question.** Can the `nearest` kind rank a point no register holds — a moved carrier or 24 exact coordinates — against the construction ladder's carriers, with the guarded read certifying the head of the ranking and the gap after it, while no unguarded reading of the ladder remains anywhere in the answering path?

**Verdict.** Yes. `nearest` now ranks a moved carrier or 24 exact coordinates against the 142 carriers of the address table, and the guarded read certifies the head and the gap after it. On every point of the six sets that the read answers, the head of the ranking is the read's answer, no other carrier is inside the reported margin, and a certified origin is in the head. Over the whole evaluation, no unguarded reading of the construction ladder is called. The frozen path keeps all 202 statuses. 7 of 7 measured marks were met, and L1 by the build. The pre-registration's predicted count of certified points was wrong, though the marks hold: it quoted a mis-summed point total and the plain read's answers, where the path reads with the junction read.

**Deciding figure.** 7 of 7 measured marks and L1; 2362 certified points of 2982, 0 head disagreements, 0 gap violations, 0 origin violations; of 620 refused points the head is the origin 441, tied 128, another carrier 51; battery 8/8 as declared, reads sound 5/5, column 3 8/8, mutants 16/16 rejected; 0 unguarded ladder readings over 212 questions; frozen path 202/202 same status, 199 same text.

**Recomputed by.** `glm_universal.reasoning.nearest_address_study.nearest_address_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration** for Phase 148, the rest of item 1 of
[`STATUS.md`](../STATUS.md) §2.1 (*the placement guard in the answering
path*, left by Phases 129 and 143). §§0–6 were committed with the Lean file
and the answering-path code, and before the module that takes the
measurement had been run; §7 is what came out.

**What the item asked, and what was found when it was read against the
code.** The item named three readings to give the guarded read: "the
escalation reports, the `nearest` kind and the evaluation's pinned cases".
Read against the code:

* **The `nearest` kind** does not read the ladder. It ranks one register's
  carriers by exact distance — a full scan, which is what the guard's
  certificate is checked against. What it lacked was reach: it refused a
  point that no register holds (`nearest to C moved 8 by 1/2`: *names no
  carrier*).
* **The escalation reports** that sit in the answering path —
  `report escalation`, `report query escalation`, and `report hole
  ladder`/`classifier`/`failures`/`configuration` — read other ladders: the
  register layer stack, the query loop's rungs, the deep-hole ensemble cells.
  None of them reads the construction ladder of carriers the placement guard
  certifies. Phase 130 had already found that no module a query loads reads
  that ladder unguarded ([`COUNTER_LASSO_STUDY.md`](COUNTER_LASSO_STUDY.md)
  §0).
* **The evaluation's pinned cases** reach the ladder only through `locate`,
  which has been guarded since Phase 143.

So this round does two things. It gives `nearest` the guarded read where it
adds something, the points no register holds. And it measures the claim that
no unguarded reading is left (mark A0): every unguarded reading function of
the ladder's measurement modules is wrapped and counted while the whole
evaluation is asked.

**What this round does.**

1. `nearest` gains an address path (`reasoning/nearest_address.py`). A
   request whose operand is a move (`<ref> moved <s> by <m> [word <k>]`) or a
   list of exact coordinates is ranked against the 142 carriers of the address
   table by exact squared distance, ties broken by `register:name`. The same
   point is read by the guarded read (Phase 143's, with Phase 144's
   junctions). The answer lists the ranking. When the read answers, it says
   the head is certified, with the margin, and with the origin when the move
   is stated and inside the margin. When the read refuses, it says that no
   margin is certified. A carrier name keeps the register ranking it always
   had. `nearest 3 to …` and `… top 3` set the length of the list.
2. Column 3 re-ranks the point by full scan without the table and checks the
   claimed gap.

**Order of work, stated plainly.**

1. *What was known before this was written.* Phase 143's figures (2,169
   answers over 3,550 points of six sets, all certified nearest). While
   building the path, these were run once, with column 3 and a mutant of
   each: `nearest to C moved 8 by 1/2`, `nearest 3 to
   harmonics:perfect_fifth moved 2 by 2`, `nearest to albedo moved 4 by 1/4`,
   and the 24-coordinate `golay_codeword_1`.
2. *The Lean file before this was committed.*
   `RequestProject/GLM/NearestAddress.lean` was written and built first. The
   frozen-path baseline was taken after it and before any answering-path code
   changed. It is shared with Phase 147
   ([`BUDGET_READING_STUDY.md`](BUDGET_READING_STUDY.md)).
3. **No set of §3 had been ranked, the battery had not been asked, and the
   audit had not been run when this was committed.**

## 1. What is proved before any code

`RequestProject/GLM/NearestAddress.lean` (namespace `GLM.NearestAddress`), on
top of `GLM.AddressRead`; no `sorry`, standard axioms only. A *ranking* is a
duplicate-free list of every carrier in which each is no farther from the
query than every carrier after it.

* `ranking_head_eq_read` — on a sound table, if the read answers `i`, the
  head of every ranking is `i`.
* `ranking_tail_outside` — there is a margin `D` with the head strictly
  inside and every later carrier outside.
* `ranking_head_origin` — a query that is `c t` moved by at most `δ`, with
  the margin exceeding `δ` at the answering rung, has `t` at its head.
* `ranking_head_of_strict` — without the read, the head is the strict nearest
  carrier whenever there is one.

## 2. The rule

As §0 item 1. The pool is the 142 carriers of the address table, in all 24
coordinates, and the metric is the read's exact squared Euclidean distance.

## 3. The sets and the questions, declared here

**The sets.** Phase 143's six sets: the four of Phase 129, the fifth set and
the clean set, 3,550 points.

**The battery** (13 questions):

| # | question | declared |
|---|---|---|
| R1 | `nearest to water moved 8 by 1/2` | refused `ambiguous-name` |
| R2 | `nearest to Fe moved 8 by 1/2` | refused `unknown-name` |
| R3 | `nearest to 1, 2, 3` | refused `dimension` |
| R4 | `nearest to C moved 30 by 1/2` | refused `malformed` |
| R5 | `nearest 0 to C moved 8 by 1/2` | refused `malformed` |
| B1 | `nearest to C moved 8 by 1/2` | head `chemistry:C`, certified |
| B2 | `nearest to` the 24 coordinates of `golay_codeword_1` | head `mathematics:golay_codeword_1`, certified |
| B3 | `nearest 3 to harmonics:perfect_fifth moved 2 by 2` | head `harmonics:perfect_fifth`, not certified |
| B4 | `nearest to albedo moved 4 by 1/4` | read |
| B5 | `nearest to energy moved 24 by 1/4` | read |
| B6 | `nearest 2 to golay_codeword_1 moved 4 by 3/2` | read |
| B7 | `nearest to` 24 zeros | read |
| B8 | `nearest to physics:acceleration moved 8 by 1/4 word 7` | read |

**New evaluation cases:** `nearest-address-moved`, `nearest-address-point`,
`nearest-address-uncertified`, `nearest-address-junction`,
`nearest-address-ambiguous`.

## 4. The marks, declared before the measurement

| mark | claim |
|---|---|
| **L1** | `NearestAddress.lean` builds with the full `lake build`, no `sorry`, standard axioms only |
| **N1** | on every point of the six sets that the guarded read answers, the head of the ranking is the read's answer (for a junction, the least-distance set is the junction) |
| **N2** | on every such point, every carrier off the head is at least the reported margin from the point |
| **N3** | on every such point whose origin is certified, the origin is in the head |
| **Q1** | the battery comes out as declared (R1–R5 on the address path, B1–B3); the reads B4–B8 are on the address path and sound; every answered question's column-3 script verifies, and two mutants of each are rejected (a wrong head; an overstated margin, or a false distance list when uncertified) |
| **W1** | the wiring census passes with `nearest_address` reached; no earlier `nearest` evaluation case is diverted to the address path |
| **A0** | over the whole evaluation after both rounds, 0 calls of the unguarded readings of the construction ladder (`budget_guard_frozen.UNGUARDED`: the readings of `ladder_escalation`, `norm256_hex`, `cell_guard` and `placement_guard`) |
| **F1** | the frozen path, as in Phase 147 (one measurement, shared) |

**N4, described and not predicted:** where the read refuses, how often the
head of the ranking is the point's origin, a tie, or another carrier.

**Predictions.** N1–N3 hold by theorem: 2,169 certified points, 0
disagreements, 0 violations. Q1: B4 certified as the junction {absorptance,
albedo}; B5 and B8 certified on their origin; B6 and B7 not predicted. A0: 0.
W1 and F1 hold.

## 5. What this round does not do

* It does not change what `nearest` answers for a carrier name. The register
  ranking, its subspace and its pool are unchanged.
* It does not grow the pool past the 142 carriers of the address table. A
  point is ranked against the declared sample, not against the registers in
  full.
* It does not put the guarded read into the escalation reports, because they
  do not read the construction ladder (§0).

## 6. Files

* `glm_lean/RequestProject/GLM/NearestAddress.lean` — §1.
* `glm_universal/reasoning/nearest_address.py` — the request, the
  ranking, the read.
* `glm_universal/runtime/parser.py` (the address path of `nearest`),
  `runtime/session.py` (`_solve_nearest_address`), `runtime/tct_engine.py`
  (the `nearest_address` template), `runtime/toolbox.py`.
* `glm_universal/reasoning/nearest_address_study.py` — the marks;
  `python3 -m glm_universal.tools nearest-address [--write]`.
* `glm_universal/reasoning/budget_guard_frozen.py` — F1 and A0.
* `glm_universal/tests/test_nearest_address.py`.

## 7. What came out

Taken with `python3 -m glm_universal.tools nearest-address --write`, after
`tools budget-guard-frozen --write` (whose stored result it reads for F1 and
A0); stored in `reasoning/_data/nearest_address_study.json`. **7 of 7
measured marks were met, and L1 by the build.** Over the whole evaluation no unguarded
reading of the construction ladder is called, and the frozen path keeps all
202 statuses. The pre-registration's predicted count was wrong: it quoted a
mis-summed point total and the plain read's answers (§7.2).

### 7.1 The marks

| mark | result | met |
|---|---|---|
| L1 | `NearestAddress.lean` builds in the full `lake build` (8248 jobs), no `sorry`; `#print axioms` names only `propext`, `Classical.choice`, `Quot.sound` | yes |
| N1 | 0 disagreements over 2362 certified points of 2982: the least-distance set of the ranking is the read's answer (a single carrier, or the junction) | yes |
| N2 | 0 gap violations: on all 2362, every carrier off the head is at least the reported margin away, and every margin is positive | yes |
| N3 | 0 origin violations over 2362 certified origins | yes |
| Q1 | R1–R5 and B1–B3 as declared (8 of 8); the reads B4–B8 on the address path and sound (5 of 5); column 3 verifies 8 of 8 answered questions and rejects 16 of 16 mutants | yes |
| W1 | the wiring census passes with `nearest_address` reached; none of the 4 earlier `nearest` evaluation cases is diverted to the address path | yes |
| A0 | 0 calls of the 18 unguarded ladder functions watched, over the 212 evaluation questions after both rounds | yes |
| F1 | as in Phase 147: 202 of 202 present and same status, 199 same text, every moved text declared | yes |

### 7.2 The prediction that was wrong

§4 predicted "2,169 certified points" over the "3,550 points" of the six sets.
Both figures were copied from Phase 143's record, and both are wrong for this
measurement:

* **The point total.** The six sets hold 2982 points (142 clean points and
  five sets of 568). The 3,550 in Phase 143's text was a mis-sum; its own
  stored measurement (`address_read_study.json`) counts 2982 queries, and
  its 2,169 answers are 125 + 402 + 402 + 402 + 445 + 393 over those.
* **The answer count.** The address path reads with the junction read of
  Phase 144 (`coordinate_junction.read_point`), which answers a junction
  where the plain read refuses. It certified 2362 points, exactly Phase
  144's stored count, not the plain read's 2,169.

The marks are unaffected (each is a count of zero disagreements), but the
prediction is recorded as missed, not re-stated.

### 7.3 N4: where the read refuses

Of the 620 refused points, the head of the ranking is the point's origin on
441, a tie of two or more carriers on 128, and another carrier on 51. A
refusal is therefore not a sign that the scan is wrong (on most it is right),
but the 51 show what the answer says when it refuses: *no margin is
certified*, and the head may not be where the point came from.

### 7.4 The battery

* B4 `nearest to albedo moved 4 by 1/4` — certified at rung C as the junction
  {`physics:absorptance`, `physics:albedo`}, margin 3.105, the origin a member
  (as predicted).
* B5 `nearest to energy moved 24 by 1/4` — `lexicon:energy`, certified at rung
  C with margin 23.035, origin certified (as predicted).
* B8 `nearest to physics:acceleration moved 8 by 1/4 word 7` — certified at
  rung Z with margin 1.292, origin certified (as predicted).
* B6 `nearest 2 to golay_codeword_1 moved 4 by 3/2` — refused: the head,
  `mathematics:golay_codeword_1`, is the strict nearest by scan, but no
  margin is certified.
* B7 the 24 zeros — refused: `golay_codeword_0` and `hexacode_word_0` are at
  distance 0 together, and no margin is certified.

### 7.5 What is left

* The escalation reports (`report query escalation` and the others) do
  not read the construction ladder at all, so there was nothing there to
  guard; A0 confirms that no unguarded reading is reached from any evaluation
  question.
* The pool is the 142 carriers of the address table, not the registers in
  full; ranking a point against a whole register would need a table over it.
* A refused point gets the scan's ranking with *no margin is certified*; it
  does not get a question that would split a tie (the *question at the other ties* item of `STATUS.md` §2.1).
