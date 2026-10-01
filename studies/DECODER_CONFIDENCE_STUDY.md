# Decoder confidence — the absorbed law attached to the decoder's own readings

## Tier 0 — the coarse read

**Question.** When the decoder, the carried fork or the second reading gives an answer, how likely is that answer to be the codeword that was sent, and can the GLM say so exactly?

**Verdict.** Every answer of the decoder, the context stage and the second reading now carries the exact probability that it is the codeword sent, at a declared bit-flip rate. A resolved fork is not certain: at a rate of 1/10, nearly half of the resolved forks fall below 99 %. The one declared clause that missed was a wrong declaration about the witness, not a wrong answer.

**Deciding figure.** 5 of 6 marks met; 1,776,804 resolved-fork readings each equal to a brute-force posterior and at least the proved floor; at 1/10, 294,976 of 592,268 resolved forks below 99 %; 15 of 15 runtime programs as declared.

**Recomputed by.** `glm_universal.reasoning.decoder_confidence_marks.decoder_confidence_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Candidate P of [`STATUS.md`](../STATUS.md) §3.4, item **P1**, named by
[`LAW_ABSORPTION_STUDY.md`](LAW_ABSORPTION_STUDY.md) §3: *the confidence fact
is answered as a question but not yet attached to the decoder's own readings
inside the runtime (the carried fork and the second reading still report a
decoding without it).* Phase 75 absorbed `FOURTH_FLIP_001` and `COMP_005` as
the `confidence` fact: a word decoded at distance `d ≤ 3` is the sent codeword
with probability `p^d q^(24−d) / Σ_w A_w p^w q^(24−w)`, where `A_w` is the
weight enumerator of the received word's coset and each bit flips
independently at rate `p` (`q = 1 − p`). The GLM can say that number when asked
for it by distance. It does not say it when it decodes.

Three readings answer without it:

* **the complete decoder** — a read at coset weight `d ≤ 3` decodes to one
  codeword, reported as *corrected*;
* **the carried fork's context stage** (`resolve(s, *cases)` in the Python
  dialect, K1 of [`CARRIED_FORK_STUDY.md`](CARRIED_FORK_STUDY.md)) — a deep-hole
  read pruned to the declared cases under the closed world, reported as
  *resolved*;
* **the second reading** (`agree(*reads)`, K2) — two reads of one carrier,
  their forks intersected, reported as *resolved*.

K1's pass mark was *0 wrong*, and it was met: over 658,812 reads, every
resolved fork held the truth. But every one of those reads was a truth plus a
weight-4 error. On a channel that flips bits independently, the same received
word can also come from another declared case plus a heavier error, and the
answer *resolved* says nothing about how often that happens. That is the
number this round attaches.

## 1. Declarations — written before any code of this round

**The object.** A reading at a declared bit-flip rate `p` with `0 < p < 1/2`.
The likelihood of a candidate codeword `c` given reads `r₁ … r_m` is
`Π_i p^(d(r_i, c)) q^(24 − d(r_i, c))` (the reads are independent); the prior
is uniform over the candidates the reading allows — every codeword for the
decoder and the second reading, the declared cases for the context stage (the
closed world, stated). The **confidence** of an answer is the posterior of the
answered codeword: its likelihood over the sum of the likelihoods of every
allowed candidate. The confidence is attached to a reading's own answer and
refuses where the reading refuses, by the same name.

**C1 — the decoder.** For every coset weight `d ≤ 3`, on a declared sample of
received words (each of the codewords of `S_8` plus every error of weight
`≤ 3` at a stride of 37 through the patterns of that weight), at the three
declared rates `1/100`, `1/20`, `1/10`: the attached confidence equals the
absorbed law's `confidence(d, p)` and a brute-force sum over the 4096
codewords. 0 disagreements. At coset weight 4 the confidence refuses `TIE`,
and the brute-force posteriors of the six candidates are equal.

**C2 — the context stage.** For every read of K1 (the five case sets
`S_2 … S_32`, every truth, every weight-4 error) at the three rates: every
resolved fork carries a confidence equal to the brute-force posterior over its
case set, and at least the bound proved in Lean,
`1 / (1 + (k − 1)(p/q)^2)`, because every other declared case lies at least
two further from the read than the survivor. Reported: the least confidence
per case set and rate, and how many resolved forks fall below 99 %.
Declared expectation, not a mark: the least confidence falls with `k` and with
`p`.

**C3 — the second reading.** For every pair of K2 (4,224 double reads) at the
three rates: every resolved pair carries the confidence of the agreed codeword
by the product of the two likelihoods, computed in integers over the joint
distance census of the 4096 codewords; on every 16th pair (264 pairs) it
equals a brute-force `Fraction` sum over the 4096 codewords. For K2's
witness (two reads whose forks keep the truth and the truth plus an octad) the
two survivors carry exactly `1/2` each, so the refusal is not a lack of
evidence but a proof of a coin toss.

**C4 — the runtime.** Two builtins in the Python dialect,
`decode_confidence(rate, subject, *cases)` and
`agree_confidence(rate, *reads)`. Each answer is an exact `Fraction` in three
columns, and its script recomputes the posterior in a fresh interpreter by a
brute-force sum over the 4096 codewords — a different computation from the
runtime's. Refusals are named: `TIE` (coset weight 4 with no cases),
`AMBIGUOUS` and `UNCORRECTABLE` (where `resolve` or `agree` refuses),
`RATE_OUT_OF_RANGE` (unless `0 < p < 1/2`), `OUTSIDE_SUBSTRATE` (a case that
is not a codeword). A declared set of programs, each with its declared outcome;
all as declared, 0 wrong.

**C5 — nothing else moves.** The carried fork's K1–K4 figures, the Python
speech study's programs and the evaluation (177 cases) are unchanged: the
confidence is new output, never a changed answer.

**C6 — Lean** (`RequestProject/GLM/DecoderConfidence.lean`). The posteriors
over a finite candidate set sum to 1 (`posterior_sum_one`); restricting the
candidates never lowers a survivor's posterior (`posterior_restrict_le`);
equal likelihoods give equal posteriors (`equal_weight_equal_posterior`); a
survivor whose rivals each have at most `r` times its likelihood has
posterior at least `1 / (1 + (k − 1) r)` (`resolved_bound`); on the binary
symmetric channel a candidate `e` further away has `(p/q)^e` times the
likelihood (`bsc_ratio`), so a survivor whose rivals are all at least `g`
further has posterior at least `1 / (1 + (k − 1)(p/q)^g)`
(`fork_confidence_bound`). Builds with no `sorry` and only the standard
axioms.

## 2. Results

`glm_universal.reasoning.decoder_confidence_marks.decoder_confidence_report`
(and `python3 -m glm_universal.tools decoder-confidence`, about four minutes;
`--quick` samples the context stage). **5 of 6 marks met.**

### 2.1 C1 — the decoder: met

2,112 reads checked at the three rates, **0 disagreements** between the
attached confidence, the absorbed law and a brute-force sum over the 4096
codewords. At coset weight 4 the confidence refused `TIE` on 102 of 102 reads,
and the six candidates' brute-force posteriors were equal on all 102.

The confidence of a decoding, by coset weight and rate (rounded to 7 places;
the attached value is the exact fraction):

| coset weight | p = 1/100 | p = 1/20 | p = 1/10 |
|---|---|---|---|
| 0 | 1.0000000 | 1.0000000 | 0.9999824 |
| 1 | 1.0000000 | 0.9999946 | 0.9995120 |
| 2 | 0.9999992 | 0.9994020 | 0.9877317 |
| 3 | 0.9978602 | 0.9438641 | 0.7775457 |

A read at coset weight 3 is *corrected* by the decoder, and at a rate of 1/10
that correction is right about 78 % of the time. The decoder said nothing of
that before.

### 2.2 C2 — the context stage: met

Every read of K1 at the three rates: 592,268 resolved forks per rate, 1,776,804
resolved-fork readings in all. Every one carries a confidence equal to the
brute-force posterior over its case set (0 disagreements) and at least the
proved floor `1 / (1 + (k − 1)(p/q)^2)` (0 below it). The least gap between
the survivor and its nearest rival is 2 at every case set and rate, as the
floor assumes.

| case set | p | resolved | least confidence | proved floor | below 99 % |
|---|---|---|---|---|---|
| `S_2` | 1/100 | 21,112 | 0.9998980 | 0.9998980 | 0 |
| `S_2` | 1/10 | 21,112 | 0.9878049 | 0.9878049 | 1,792 |
| `S_8` | 1/20 | 81,256 | 0.9890261 | 0.9809783 | 672 |
| `S_8` | 1/10 | 81,256 | 0.9526644 | 0.9204545 | 28,896 |
| `S_32` | 1/100 | 291,712 | 0.9991843 | 0.9968470 | 0 |
| `S_32` | 1/20 | 291,712 | 0.9782462 | 0.9209184 | 31,200 |
| `S_32` | 1/10 | 291,712 | 0.9088391 | 0.7232143 | 176,800 |

(The full table, all fifteen rows, is the tool's output.) With one rival
(`S_2`) the floor is attained. Summed over the case sets: at 1/100 no resolved
fork falls below 99 %; at 1/20, 43,136 of 592,268 do; at 1/10, 294,976 of
592,268 — nearly half of the resolved forks. The declared expectation holds: the
least confidence falls with `k` and with `p`.

This is the number K1's *0 wrong* could not give. K1 measured every truth
with a weight-4 error, and on that set the fork is never wrong. On a channel
that flips bits independently, the same read can come from another declared
case with a heavier error, and at 1/10 with 32 cases that happens often enough
to take a resolved answer down to 0.909. A resolved fork is not certain.

### 2.3 C3 — the second reading: not met

At each of the three rates: 4,224 of 4,224 double reads answered, 0 wrong,
the least confidence 0.9995918 (1/100), 0.9888897 (1/20) and 0.9500759
(1/10); on the 264 pairs of the declared stride the integer computation equals
the brute-force `Fraction` sum, 0 disagreements.

The witness clause is **missed as declared**. The declaration said the two
survivors carry exactly `1/2` each. They are exactly equal at every rate — the
tie is proved, not estimated, and the refusal `AMBIGUOUS` is right — but each
is slightly below `1/2` (0.4999984 at 1/10), because the other 4,094 codewords
keep some of the mass. Given that the carrier is one of the two survivors, each
is `1/2` exactly. That was the quantity the declaration meant, but not the one
it named, so the clause is recorded as missed and not re-read. The machine gave
no wrong answer here; the declaration was wrong.

### 2.4 C4 — the runtime: met

15 of 15 declared programs as declared: 8 answers, each an exact `Fraction`
whose script, run in a fresh interpreter, recomputes the posterior by a
brute-force sum over the 4096 codewords and prints `VERIFIED True`; and 7
refusals named as declared (`TIE`, `UNCORRECTABLE`, `AMBIGUOUS` twice,
`RATE_OUT_OF_RANGE` twice, `OUTSIDE_SUBSTRATE`). A program can use the answer:
`c = decode_confidence(Fraction(1, 100), golay_encode(3) ^ 0b11)` then
`c > Fraction(99, 100)` is `True`.

### 2.5 C5 — nothing else moves: met

K1 answers 592,268 of 658,812 reads and K2 4,224 of 4,224, both with 0 wrong,
as [`CARRIED_FORK_STUDY.md`](CARRIED_FORK_STUDY.md) states. The Python speech
programs and the 177 evaluation cases are the release's instruments, and they
were run in this round's release.

### 2.6 C6 — Lean: met

`RequestProject/GLM/DecoderConfidence.lean`: `posterior_sum_one`,
`posterior_restrict_le`, `equal_weight_equal_posterior`, `resolved_bound`,
`bsc_ratio`, `bsc_anti`, `fork_confidence_bound` (and `product_posterior`).
No `sorry`; the theorems depend on the standard axioms only.

## 3. What this round moved, and what it leaves

**Built.** `reasoning/decoder_confidence.py` (the runtime computation),
`reasoning/decoder_confidence_marks.py` (the marks), two dialect builtins and
their plain-Python prelude twins, the refusal names `TIE` and
`RATE_OUT_OF_RANGE`, `tools decoder-confidence`,
`tests/test_decoder_confidence.py`, and the Lean file.

**Against the target.** Refusal and derivation both: an answer now says how far
it can be trusted, and a refusal at a tie now carries the proof that the tie
is exact.

**Not done.** (1) The confidence is attached where a caller asks for it — the
two builtins — and not yet printed beside every `resolve` and `agree` answer,
because that would change the text of answers the Python speech study pins.
(2) A floor on confidence as a refusal (answer only above a declared
confidence) is the obvious next step, and it needs a declared threshold from
the owner. (3) The rate is declared by the caller; estimating it from the
machine's own readings is candidate J's soft-channel item.

*Items (1) and (2) were taken by Phase 80
([`CONFIDENCE_FLOOR_STUDY.md`](CONFIDENCE_FLOOR_STUDY.md)): the owner asked
for a hunt over thresholds rather than one threshold, and for a confidence
score where none works.*
