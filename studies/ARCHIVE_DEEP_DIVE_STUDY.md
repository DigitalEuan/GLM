# Two questions the archive audit left open

*[`SOURCE_SALVAGE_AUDIT.md`](SOURCE_SALVAGE_AUDIT.md) closed eleven retrievals
from the supplied archive. Two of them closed with a number rather than with a
verdict, and both numbers invited a second question that the audit did not ask.
This document asks them. Both answers are negative, and both are more useful
than the positive would have been.*

Module: [`overlay/glm_universal/reasoning/deep_dive.py`](../overlay/glm_universal/reasoning/deep_dive.py)
— one call, `deep_dive_report()`.
Tests: `overlay/glm_universal/tests/test_deep_dive.py` — 23 test methods.
Specification: `RequestProject/GLM/TriadChance.lean` and
`RequestProject/GLM/Relaxation.lean` (D8).
Arithmetic: exact `int` and `Fraction` (D7). Every census below is a full
enumeration, never a sample (D2).

```bash
cd overlay
PYTHONPATH=. python3 -c "from glm_universal.reasoning.deep_dive import deep_dive_report as r; print(r())"
```

---

## 1. Is the "44 balanced octads" a property of the code, or of chance?

The archive counts, of the 759 octads, those whose three eight-bit blocks are
pairwise at Hamming distance four, calls them *balanced*, finds **44**, and
reads the count as structure. The salvage audit confirmed the count. It did not
ask what the count would be if the code were not there.

### 1.1 The null distribution, enumerated

There are `C(24,8) = 735,471` eight-subsets of the coordinates. Walking all of
them — this is the control the archive never ran — the deviation census is

| deviation | 0 | 2 | 4 | 6 | 8 | 10 | 12 |
|---|---|---|---|---|---|---|---|
| eight-subsets | 37,800 | 319,200 | 314,580 | 55,440 | 7,728 | 720 | 3 |

So a set of 759 eight-subsets drawn with no knowledge of the code would contain

```
759 × 37800 / 735471 = 12600/323 ≈ 39.01
```

balanced ones. The observed count is 44. The excess is `1612/323`, **under five
octads**, on a measure whose spread is in the hundreds.

The octads' own census — `0: 44, 2: 336, 4: 312, 6: 58, 8: 9` — differs from the
null one in shape, and that difference is real: the code has no eight-subset at
deviation 10 or 12, and it is short of deviation-2 sets relative to chance. What
it does not have is an *excess of balance*.

### 1.2 The measure is not even an invariant

The deeper objection is that balance is a property of the coordinate *order*,
not of the code. Relabelling by each of the 276 transpositions of the 24
coordinates gives a balanced count ranging over

| minimum | mean | maximum | identity | transpositions that keep 44 |
|---|---|---|---|---|
| **27** | `5777/138 ≈ 41.86` | **63** | 44 | 21 of 276 |

A single swap of two coordinates moves the count by up to 19. The explicit
witness kept in the report is the swap `(0, 8)`: it takes the count from 44 to
**49**, and creates a deviation-10 octad where the identity labelling has none.

The block structure itself is symmetric — each block contributes deviation 12
in total — so nothing about the code privileges the labelling the archive
happened to use.

**Verdict.** The 44 is a coincidence of the coordinate order, sitting five above
a chance expectation of 39, on a measure a single transposition can move by
nineteen. The three extreme octads recorded in the report (block splits
`(2,5,1)`, `(2,5,1)`, `(3,3,2)`, with distance triples `(7,1,6)` and `(2,1,1)`)
are there so that a reader can see what "unbalanced" looks like. This is a
negative result, and it is why `TriadChance.lean` exists.

---

## 2. Is the archive's "relaxation" a decoder?

`LDP.lean` proved that every excited word descends: the energy — the weight of
the syndrome — strictly drops under a named flip, and the descent reaches the
code. The archive reads this as decoding. It does not follow, because reaching
*the code* is not reaching *the nearest codeword*.

### 2.1 The descent arithmetic

The check matrix is `H = [B | I₁₂]`, so the column weights are

```
11, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1
```

— the message half is dense, the parity half is a single bit each. The best
single flip drops the energy by an odd amount, and the census over the 4,096
syndromes is `1: 1486, 3: 1342, 5: 957, 7: 286, 9: 22, 11: 2`.

The longest strictly-descending path from a syndrome is exactly its weight
(`equals_popcount` is `True`), so the census of longest paths is the binomial
`1, 12, 66, 220, 495, 792, 924, 792, 495, 220, 66, 12, 1` over 24,576 steps in
total, mean 6. The energy bound is therefore tight, and this is what
`Relaxation.lean` proves in general.

### 2.2 Where it fails to decode

The fastest strictly-descending path, per coset:

| steps | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|---|
| cosets | 1 | 24 | 210 | 1,298 | 1,771 | 726 | 66 |

Mean `1931/512 ≈ 3.77` steps; 3,304 cosets within four, 4,030 within five, all
4,096 within six. Against that, the coset **leader** census is
`0: 1, 1: 24, 2: 276, 3: 2024, 4: 1771` — never more than four.

Comparing them coset by coset, **792 of the 4,096** need strictly more
descending flips than their leader has weight:

* 726 cosets whose leader has weight 3 need 5 steps;
* **66** cosets whose leader has weight 2 need 6 steps.

Those 66 are exactly the pairs of message-half coordinates
(`worst_case_is_the_message_pairs`) — the columns of weight 7, where flipping
one of the two coordinates the leader names would *raise* the energy, so a
strictly descending path can never take it.

### 2.3 Greedy is not optimal either

Taking the largest available drop at each step costs 16,020 flips over all
cosets (mean `4005/1024`), and preferring the last coordinate on a tie costs
16,152 (mean `2019/512`), against 15,448 for the fastest paths. Greedy descent
is not optimal, on either tie-break.

**Verdict.** Descent is a relaxation, not a decoder. It always terminates in the
code, it never terminates at the leader for 792 of the 4,096 cosets, and the
worst case is a structural family rather than an accident. Syndrome decoding —
which the package does have, in `substrate/golay_decode.py` — is what reaches
the leader.

---

## 3. What the two answers have in common

Both archive claims are of the same shape: *a computation was run, a number came
out, and the number was read as structure*. In both cases the missing step is
the control.

| claim | what was measured | what was missing | what the control shows |
|---|---|---|---|
| 44 balanced octads | the count | the chance count, and the invariance | 39 by chance; 27–63 under relabelling |
| relaxation decodes | that descent terminates | that it terminates at the leader | 792 cosets where it does not |

This is the same discipline the positioning note states: a correspondence is
asserted only against a control, and *check a claim from several layers before
calling it present* cuts both ways — a claim can also look present at one layer
and dissolve one layer up.

---

## 4. Where this sits

* The audit these two questions came out of:
  [`SOURCE_SALVAGE_AUDIT.md`](SOURCE_SALVAGE_AUDIT.md).
* The Lean half of the archive round:
  [`RETRIEVED_LEAN_STUDY.md`](RETRIEVED_LEAN_STUDY.md).
* The second pass over the archive:
  [`SOURCE_SALVAGE_SECOND_PASS.md`](SOURCE_SALVAGE_SECOND_PASS.md).
