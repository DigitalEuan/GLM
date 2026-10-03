# The contract matrix — candidate P's two contract changes, tested four ways

## Tier 0 — the coarse read

**Question.** Of the current contract, the upper-credible rate rule, the session-marginal confidence and both together, which should the plain readings ship, judged exactly over every fixed-rate cell in two frames?

**Verdict.** The combined candidate P (variant D, the upper-credible rule over the session's reads) qualifies and keeps the most right answers among the variants that qualify; it is the production baseline, and the upper-credible rule alone and the session-marginal confidence alone are set aside, still callable by name.

**Deciding figure.** 525 cells per variant and frame; on-grid breaks in frame I: A 2, B 0, C 2, D 0; in frame II: A 0, B 0, C 2, D 0; mean on-grid retention in frame II: A 0.7420, B 0.5562, C 0.8003, D 0.6881; prior-averaged promise broken in 0 of 35 cells for every variant.

**Recomputed by.** `glm_universal.reasoning.contract_matrix.matrix`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Phase 86 ([`RATE_POSTERIOR_STUDY.md`](RATE_POSTERIOR_STUDY.md) §4) measured
repairs to the soft confidence floor and left two changes of contract to the
owner, because each changes what a printed confidence means:

* **P-a, the upper-credible rule** — answer the floor with the confidence at
  the largest grid rate whose posterior mass is at least `1/100` (Phase 86's
  R4), refusing at the edge when that rate is the guard, instead of the
  posterior-marginal confidence of Phase 82;
* **P-b, the session-marginal confidence** — let the plain readings take the
  rate posterior over every read the session has seen so far, not only the
  reads the call passes.

The owner's Phase 89 request asked for both to be tested alone and together
against the current contract, as a 4-way matrix, and for the best to become
the production baseline with the others set aside, not removed. The same
request supplied the outside question sets
([`QUESTION_SET_B_STUDY.md`](QUESTION_SET_B_STUDY.md)), where §6 re-runs the
framed questions under each variant.

## 1. The four variants

| name | what it is | posterior over | rule |
|---|---|---|---|
| A | control (current contract) | the call's own read | marginal |
| B | upper-credible rate rule alone | the call's own read | upper credible |
| C | session-marginal confidence alone | every read of the session | marginal |
| D | combined candidate P | every read of the session | upper credible |

## 2. The model and the decision rule, declared before the table was read

A **session** is `S` plain calls at one fixed true rate `r` (J3's model: one
rate for every read). Call `k` presents one subject read with its own truth.
Under A and B the posterior at call `k` sees one read; under C and D it sees
the `k` reads of calls `1..k` — a printed confidence never waits for reads
that have not arrived. The subject's own coset class decides the answer as
before, so call `k` of a session variant is exactly the count-vector engine's
cell of `k` reads, and a session is the pooled sum of its calls. Everything is
exact (`Fraction`), with no sampling.

The cells are those of the rate-posterior study: 15 fixed true rates × the
session lengths 1, 2, 5, 10, 20 × the 7 floors of the confidence-floor hunt
(9/10 … 9999/10000), which is 525 cells per variant and frame. A cell is
**on grid** when its true rate is one of the hunted rates (up to 1/10); 1/5 is
twice the highest hunted rate and is reported separately.

Two frames:

* **frame I** — one call of `n` reads, the subject and the `n − 1` corpus
  reads the caller passes, with no session history (J3's table). A session
  variant with no history is its call variant, so here C reads as A and D as
  B by construction;
* **frame II** — a session of plain calls, as above.

**The decision rule.** A variant qualifies for production only if it keeps
the prior-averaged promise (J2's: the pooled residual with the rate drawn
from the uniform prior over the grid, guard included, is at most `1 − t`) in
every cell, and breaks **no on-grid cell in either frame**. Among those that
qualify, the highest mean on-grid retention in frame II wins; a tie goes to
the smaller contract change (A 0, B and C 1, D 2).

## 3. The matrix

`PYTHONPATH=. python3 -m glm_universal.tools contract-matrix` from `overlay/`
(about two minutes):

| variant | frame I broken (on grid, at 1/5) | frame I worst residual/(1−t) | frame II broken (on grid, at 1/5) | frame II worst on grid | retention S=20 at 1/20, floor 999/1000 | at 1/10 | mean on-grid retention | prior promise broken |
|---|---|---|---|---|---|---|---|---|
| A | 37 (2, 35) | 208.03 | 35 (0, 35) | 0.1764 | 0.3009 | 0.1015 | 0.7420 | 0 of 35 |
| B | 32 (0, 32) | 116.01 | 20 (0, 20) | 0.1764 | 0.3009 | 0.1015 | 0.5562 | 0 of 35 |
| C | 37 (2, 35) | 208.03 | 37 (2, 35) | 1.3322 | 0.7623 | 0.2825 | 0.8003 | 0 of 35 |
| D | 32 (0, 32) | 116.01 | 28 (0, 28) | 0.3552 | 0.7264 | 0.2703 | 0.6881 | 0 of 35 |

(Retentions are printed truncated to four places; the pinned test rounds
them, so A's 0.3009… is 0.3010 there and D's 0.7264… is 0.7265.)

Frame I reproduces Phase 86's repairs table exactly: the marginal rule breaks
37 cells, 2 of them on grid, and the upper-credible rule 32, none on grid.

**What the table says.**

* **A, the control, fails the rule.** It breaks 2 on-grid cells in frame I —
  the two on-grid breaks Phase 86 found.
* **C fails it too, in both frames.** Pooling the session's reads sharpens
  the posterior and keeps the most right answers (mean on-grid retention
  0.8003, and 0.7623 against A's 0.3009 at the 1/20 reference cell), but the
  marginal rule over the pooled reads breaks 2 on-grid cells in frame II, with
  a worst on-grid factor of 1.3322: the residual exceeds the floor's promise.
* **B and D qualify.** Neither breaks an on-grid cell in either frame, and
  both keep the prior-averaged promise everywhere.
* **D keeps more right answers than B**: mean on-grid retention 0.6881
  against 0.5562, and 0.7264 against 0.3009 at the 1/20 reference cell. The
  session's reads give back most of what the upper rule's caution costs.
* **Every variant breaks cells at 1/5.** At twice the highest hunted rate no
  rule keeps the promise in every cell; D breaks 28 of them in frame II and B
  20. This is Phase 86's identity at the guard and is not repaired by either
  change. The prior-averaged promise, which includes the guard rate, holds for
  all four.

**The decision: D**, the combined candidate P, `contract_matrix.PRODUCTION`.
B and C are `contract_matrix.SET_ASIDE`: kept, named and callable for a later
round. In one sentence: the combined candidate P (variant D, the
upper-credible rule over the session's reads) qualifies and keeps the most
right answers among the variants that qualify; it is the production baseline,
and the upper-credible rule alone and the session-marginal confidence alone
are set aside, still callable by name.

## 4. Calibration of the printed confidence

The calibration figure is the largest excess, over the on-grid cells, of the
mean printed (unfloored) confidence over the actual accuracy among answered
calls, bracketed exactly at a resolution of `10⁻¹²`:

| variant | largest excess |
|---|---|
| A | −0.00007795 |
| B | 0.00000000 |
| C | −0.00000406 |
| D | 0.00002621 |

D's printed confidence overstates its accuracy by at most 0.00002621 on
average in its worst on-grid cell, where A, B and C never overstate it. That
is a small cost of the change, recorded rather than hidden; the floor's
promise, which is what the decision rule tests, is kept on grid.

## 5. What was changed in the runtime

* `reasoning/rate_posterior.py`: `PRODUCTION_RULE = "upper"`, with
  `UPPER_EPS = 1/100`; `marginal` remains callable by name, and
  `session_confidence` takes the posterior over the session's reads.
* `runtime/question_frames.py`: the frames that print a confidence read
  through the production variant (`contract_matrix.PRODUCTION`), carrying the
  session's reads in `SESSION_READS`; `CONTRACT_VARIANT` lets the question-set
  scorer run all four.
* On the outside question sets the change moves nothing: the 41 framed
  questions give the same verdicts under A, B, C and D (31 answered, 10
  refused with the same codes), because the questions fix the rate wherever
  they ask for a confidence ([`QUESTION_SET_B_STUDY.md`](QUESTION_SET_B_STUDY.md)
  §6). The decision rests on the exhaustive matrix above.

## 6. What is proved

`RequestProject/GLM/QuestionSetB.lean`, `upper_rule_safe`: when the printed
confidence is antitone in the rate and the true rate lies at or below the
upper end of the credible set, the upper-credible confidence never overstates
the confidence at the true rate. Built with no `sorry` and standard axioms
only.

## 7. Re-running

`PYTHONPATH=. python3 -m glm_universal.tools contract-matrix` (`--json` for
every row). Tests: `glm_universal/tests/test_contract_matrix.py` — the fast
cases check the engine's identities on short sessions; the whole matrix, which
decides the production baseline, is an exhaustive case.
