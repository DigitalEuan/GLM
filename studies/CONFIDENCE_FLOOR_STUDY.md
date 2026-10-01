# The confidence floor, hunted — which threshold works, and a confidence score where none does

## Tier 0 — the coarse read

**Question.** Is there a confidence threshold at which the decoder and the carried fork should refuse, and where there is none, can the reading answer with its confidence instead of refusing?

**Verdict.** There is a working threshold at every declared rate up to 1/20 — 999/1000 at 1/20 and 9999/10000 below it, so both of the owner's candidates work there — and none at 1/10, where the complete decoder is the reading that binds; there the reading answers with its confidence instead of refusing. The one declared clause that missed was a wrong declaration about one program, not a wrong answer.

**Deciding figure.** 6 of 7 marks met; 35 of 35 grid cells classified, working threshold 9999/10000 at 1/1000, 1/100 and 1/50, 999/1000 at 1/20, none at 1/10; the promise kept in 210 of 210 cells, and in 210 of 210 with the rate overdeclared; 15 of 16 runtime programs as declared.

**Recomputed by.** `glm_universal.reasoning.confidence_floor_marks.confidence_floor_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Candidate P of [`STATUS.md`](../STATUS.md) §3.4, item **P3**, named by
[`DECODER_CONFIDENCE_STUDY.md`](DECODER_CONFIDENCE_STUDY.md) §3: *a confidence
floor as a refusal — answer a resolved fork only above a declared confidence
at a declared rate (the owner's threshold is needed), and print the confidence
beside every `resolve` and `agree` answer rather than only when asked.*

Phase 77 asked the owner for the threshold: 99 %, 99.9 %, or skip. The
owner's answer, given at the start of this round, was neither: *test some
threshold variations and hunt for the working one; if there isn't a working
version, have a confidence score rather than a refusal.* So this round does
not pick a threshold. It declares what *working* means, measures every
threshold of a declared grid against it exactly, and gives the readings a
graded answer — the value with its confidence — that never refuses on
confidence at all.

What Phase 77 measured and what it could not. Phase 77 attached the exact
posterior to each reading and counted, over K1's reads (every truth plus
every weight-4 error), how many resolved forks fall below 99 %. That is a
count of reads, not a probability: K1's reads are not drawn from the channel,
so it says nothing about how often a floor would refuse a right answer, or
how many wrong answers it would remove. This round measures those two
numbers exactly, over the channel itself.

## 1. Declarations — written before any code of this round

**The floor.** A reading at declared bit-flip rate `p` with floor `t`
(`0 < t ≤ 1`) answers when its confidence (Phase 77's posterior) is at least
`t`, and otherwise refuses `BELOW_FLOOR`, naming the confidence. It refuses
where the reading refuses, by the same name.

**The graded answer.** The same reading without a floor: it answers the
value *and* its confidence, and never refuses on confidence. Its language
column names a band, declared here: *near-certain* at or above 999/1000,
*confident* at or above 99/100, *probable* at or above 9/10, *uncertain*
below 9/10. The band is wording; the answer is the exact confidence.

**The channel measure.** The truth is drawn uniformly from the reading's
allowed candidates (the declared cases for the context stage, the closed
world; all 4096 codewords for the decoder) and each of its 24 bits flips
independently at the true rate. Every probability below is exact — a sum over
every received word, not a sample:

* `P(right)`, `P(wrong)`, `P(refused)` of the unfloored reading;
* for each floor `t`: `P(right, answered)`, `P(wrong, answered)`;
* the **residual error** `P(wrong | answered)` and the **retention**
  `P(right, answered at t) / P(right, unfloored)`.

**The readings.** The complete decoder, and the context stage (`resolve`)
over each of K1's five case sets `S_2, S_4, S_8, S_16, S_32` — six readings.
(The second reading, `agree`, has no exact channel measure here: its reads
are pairs, and a sum over every pair of received words is out of reach. It
gets the floor and the graded answer in the runtime, not a place in the
hunt.)

**The grid.** Rates `H = 1/1000, 1/100, 1/50, 1/20, 1/10`. Thresholds
`T = 9/10, 19/20, 49/50, 99/100, 199/200, 999/1000, 9999/10000` — the owner's
two candidates and five around them.

**What working means.** A threshold `t` **works** at rate `p` when, for every
one of the six readings,

* (a) *the promise*: `P(wrong | answered) ≤ 1 − t`, and
* (b) *the cost*: the floor keeps at least 9/10 of the unfloored reading's
  right answers (retention ≥ 9/10).

The **working threshold** at a rate is the highest `t` of `T` that works
there. A threshold **works robustly** if it also keeps (a) when the true rate
is twice the declared one (the reads at `2p`, the confidence computed at
`p`).

**The owner's fallback, as a rule.** At a rate where some `t ≥ 99/100`
works, the floor at the working threshold is the recommended reading. At a
rate where none does, the recommended reading is the graded answer: a
confidence score, not a refusal.

**F1 — the census is right.** (i) For the decoder at every rate of `H`,
`P(right) + P(wrong) + P(refused) = 1` exactly, with `P(refused)` (the tie at
a deep hole) computed by a separate route from the 1,771 deep-hole cosets.
(ii) For the context stage, the census counts, per case set, exactly the
resolved weight-4 reads K1 counts (592,268 over the five sets); and on a
declared stride of the resolved reads, the census's confidence equals the
runtime's `decode_confidence` and a brute-force `Fraction` sum, 0
disagreements.

**F2 — the promise.** In every cell of the grid (six readings, five rates,
seven thresholds), `P(wrong | answered) ≤ 1 − t` exactly. (The Lean theorem
of F7 says this must hold; the mark checks the implementation.)

**F3 — the hunt.** Every one of the 35 (rate, threshold) cells classified
works or does not, with its least retention and its greatest residual error
printed; the working threshold named per rate; and the classification
monotone — a threshold that works at a rate works at every lower threshold of
`T` at that rate (a theorem) and at every lower rate of `H` (not a theorem: a
claim about these codes, declared here). Declared expectation, not a mark:
the working threshold falls as the rate rises.

**F4 — the declared rate.** (i) Overdeclared — reads at `p/2`, confidence at
`p` — the promise holds in every cell (the Lean theorem of F7 predicts it).
(ii) Underdeclared — reads at `2p` — reported: every cell where the promise
breaks, and by how much. The mark is (i).

**F5 — the runtime.** Four builtins in the Python dialect:
`resolve_at(rate, subject, *cases)` → `(index, confidence)` and
`agree_at(rate, *reads)` → `(value, confidence)` — the graded answer, the
confidence printed beside every answer; `resolve_floor(rate, floor, subject,
*cases)` and `agree_floor(rate, floor, *reads)` — the floor, refusing
`BELOW_FLOOR`. A floor outside `(0, 1]` or not an exact rational refuses
`FLOOR_OUT_OF_RANGE`. Every answer carries a script that recomputes the
confidence by a brute-force sum in a fresh interpreter. A declared set of
programs, each with its declared outcome: all as declared, 0 wrong.

**F6 — nothing else moves.** `resolve`, `agree`, `decode_confidence` and
`agree_confidence` answer exactly as before; the carried fork's K1 and K2
figures and the Phase 77 marks stand; the Python speech programs and the
evaluation are the release's instruments.

**F7 — Lean** (`RequestProject/GLM/ConfidenceFloor.lean`).
`floor_error_le`: if every answered read has posterior at least `t`, the
mass-weighted error among the answered is at most `1 − t`.
`floor_retention_antitone`: raising the floor never raises what it keeps.
`posterior_antitone_rate`: a survivor no further from the read than any
rival loses posterior as the rate rises. `floor_safe_overdeclared`: hence a
floor passed at a declared rate is passed at every lower true rate. No
`sorry`; the standard axioms only.

## 2. Results

`glm_universal.reasoning.confidence_floor_marks.confidence_floor_report`
(and `python3 -m glm_universal.tools confidence-floor`, about twenty seconds).
**6 of 7 marks met.**

### 2.1 F1 — the census: met

For the decoder at every rate of `H`, `P(right) + P(wrong) + P(refused)` is
exactly 1, with the refused tie weighed by an enumerator counted directly from
one deep hole. For the context stage the census counts 21,112, 41,676, 81,256,
156,512 and 291,712 resolved weight-4 reads over `S_2 … S_32` — exactly K1's
counts, 592,268 in all. On a stride of 3,489 resolved reads the census's
confidence equals the runtime's `decode_confidence` and a brute-force
`Fraction` sum: 0 disagreements.

What the census says before any floor (rounded; each is an exact fraction):

| reading | p | P(right) | P(wrong) | P(wrong \| answered) | least confidence |
|---|---|---|---|---|---|
| decoder | 1/100 | 0.9999095 | 0.0000035 | 0.0000035 | 0.9978602 |
| decoder | 1/20 | 0.9702175 | 0.0052600 | 0.0053923 | 0.9438641 |
| decoder | 1/10 | 0.7857378 | 0.0668416 | 0.0783993 | 0.7775457 |
| `S_2` | 1/10 | 0.9140741 | 0.0002287 | 0.0002502 | 0.9878049 |
| `S_32` | 1/20 | 0.9906422 | 0.0002703 | 0.0002727 | 0.9782462 |
| `S_32` | 1/10 | 0.8965670 | 0.0046459 | 0.0051552 | 0.9088391 |

(All thirty rows are the tool's output.) This is the number K1's *0 wrong*
and Phase 77's count of reads below 99 % could not give: at 1/10 the complete
decoder answers wrong with probability 0.067, and the context stage over 32
cases with probability 0.0046.

### 2.2 F2 — the promise: met

In all 210 cells (six readings, five rates, seven thresholds),
`P(wrong | answered) ≤ 1 − t` exactly: 0 broken. That is
`GLM.ConfidenceFloor.floor_error_le` holding in the implementation.

### 2.3 F3 — the hunt: met

All 35 (rate, threshold) cells are classified, and the classification is
monotone in the threshold and in the rate. The working threshold, and the
reading that decides it:

| rate | working threshold | the owner's 99/100 | the owner's 999/1000 | where the cost clause binds |
|---|---|---|---|---|
| 1/1000 | 9999/10000 | works | works | nowhere (retention 1 everywhere) |
| 1/100 | 9999/10000 | works | works | decoder, retention 0.9984 at 999/1000 |
| 1/50 | 9999/10000 | works | works | decoder, retention 0.9894 at 199/200 |
| 1/20 | 999/1000 | works | works | decoder, retention 0.9112; 0.6811 at 9999/10000 |
| 1/10 | none | does not work | does not work | decoder, retention 0.7181 at 9/10, 0.3722 at 99/100 |

The declared expectation holds: the working threshold falls as the rate
rises. At every rate the reading that binds is the complete decoder. Its
confidence takes only four values, one per coset weight, so a floor can only
drop a whole weight: at 1/10 a floor anywhere from 9/10 to 49/50 drops every
weight-3 read (confidence 0.7775457), and a floor at 99/100 drops weight 2 as
well. At 1/20, 999/1000 drops the weight-3 reads (0.9438641) and keeps 91.1 %
of the right answers while removing 97.4 % of the wrong ones.

**The owner's fallback, applied.** At 1/1000, 1/100, 1/50 and 1/20 a
threshold at or above 99/100 works, so the recommended reading is the floor at
the working threshold. At 1/10 none does, so the recommended reading is the
graded answer: `resolve_at` and `agree_at` answer with the confidence beside
the value, and nothing is refused on confidence.

*Not declared, so not counted.* Each reading on its own: the context stage
has a working threshold at 1/10 as well — 999/1000 over `S_2`, `S_4` and
`S_8`, 49/50 over `S_16`, 19/20 over `S_32` — because its confidences are
spread over many values and a floor removes the wrong answers first. Over
`S_2` at 1/10, a floor at 99/100 keeps 98.1 % of the right answers and removes
91.9 % of the wrong ones; over `S_32`, it keeps 84.4 % and removes 94.9 %. It
is the decoder alone that has no working floor at 1/10.

### 2.4 F4 — the declared rate: met

With the rate overdeclared (reads at `p/2`, confidence at `p`) the promise
holds in 210 of 210 cells, as `GLM.ConfidenceFloor.floor_safe_overdeclared`
says it must. With the rate underdeclared (reads at `2p`) it breaks in 30 of
210: at 1/20 in six cells (the decoder at 199/200 and above; the context
stage over `S_8`, `S_16`, `S_32` at 9999/10000), and at 1/10 in twenty-four.
The worst is the decoder declared at 1/10 and read at 1/5, floored at
9999/10000: it promises a residual error of 0.0001 and delivers 0.0116. The
thresholds whose promise survives a doubled rate: every one of `T` at 1/1000,
1/100 and 1/50; up to 99/100 at 1/20; none at 1/10. So when the rate is
uncertain, declare the higher one: the floor is then safe, not merely
calibrated.

### 2.5 F5 — the runtime: not met

16 programs declared; 15 as declared. Every answer's script, run in a fresh
interpreter, recomputes the confidence by a brute-force sum and prints
`VERIFIED True`; the refusals `UNCORRECTABLE`, `AMBIGUOUS` (twice),
`RATE_OUT_OF_RANGE`, `FLOOR_OUT_OF_RANGE` (twice) and `BELOW_FLOOR` are named
as declared, and a `BELOW_FLOOR` refusal carries a certificate its script
checks.

The miss is **one wrong declaration**. The program
`resolve_floor(Fraction(1, 10), Fraction(999, 1000), golay_encode(1) ^ 0b111,
golay_encode(1), golay_encode(2))` was declared to refuse `BELOW_FLOOR`, on the
reasoning that a weight-3 read at 1/10 is about 78 % sure. That is the
decoder's figure, over all 4096 codewords. With two declared cases the read's
one rival lies four further away, so its confidence is `1/(1 + (1/9)^4) =
6561/6562`, above the floor, and the machine answered. The machine gave no
wrong answer; the declaration was wrong, and it is recorded as missed rather
than re-read.

### 2.6 F6 — nothing else moves: met

K1 answers 592,268 of 658,812 reads and K2 4,224 of 4,224, both with 0
wrong, as stated. On 198 reads the graded reading returns exactly what
`resolve` returns, and refuses by the same name where it refuses. The existing
builtins are untouched: `resolve_at`, `agree_at`, `resolve_floor` and
`agree_floor` are new names.

### 2.7 F7 — Lean: met

`RequestProject/GLM/ConfidenceFloor.lean`: `floor_error_le`,
`floor_retention_antitone`, `posterior_antitone_rate`,
`floor_safe_overdeclared` (and `posterior_eq_ratio`, `ratio_sum_ge_one`,
`odds_mono`, `floor_pass_lower_rate`). No `sorry`; the theorems depend on the
standard axioms only.

## 3. What this round moved, and what it leaves

**Built.** `reasoning/confidence_floor.py` (the graded answer and the floor),
`reasoning/confidence_floor_marks.py` (the exact channel census, the hunt and
the marks), four dialect builtins with their plain-Python prelude twins, the
refusal names `BELOW_FLOOR` and `FLOOR_OUT_OF_RANGE`,
`tools confidence-floor`, `tests/test_confidence_floor.py`, and the Lean file.

**Against the target.** Refusal: a floor now removes wrong answers at a
counted cost in right ones, and the cost is known exactly before the floor is
chosen — at 1/20 a floor at 999/1000 removes 97.4 % of the decoder's wrong
answers for 8.9 % of its right ones. Where no floor is worth its cost, the
graded answer says how far to trust the value instead of refusing it.

**Not done.** (1) The second reading has no exact channel measure: its reads
are pairs, and the hunt covers the decoder and the context stage only. (2) The
rate is still declared by the caller; the underdeclared result says the price
of a wrong declaration, and estimating the rate from the machine's own
readings is candidate J's soft-channel item. (3) The plain `resolve` and
`agree` still print no confidence, because they take no rate; the graded
builtins are where the confidence is printed beside every answer.
