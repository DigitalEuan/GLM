# Run 93 — the Q(√7) family, its one word, and a ring that refuses

Run 92 read one row of the census and named its word. This run reads **every** row whose
side lies in Q(√7), decides honestly whether they follow n = 18's law or split, derives the
Ring side law in the field — and then reports the part that did not work: the ring
*sentence* has no gated member yet, and the family says so with a declared refusal instead
of a claim.

## 1. The five rows

Run 86's field sweep (`workspace/push/field_triage.json`) records exactly five rows whose
side is Q(√7)-expressible: **n = 18, 53, 151, 234, 747**. Control 23 re-derives each one
from the pose itself:

| n | axis | tilted | at the census word | distinct tilt angles | side | k |
|---|---|---|---|---|---|---|
| 18 | 10 | 8 | 8 | 1 | `7/2 + ½√7` | 1 |
| 53 | 39 | 14 | 6 | 3 | `13/2 + ½√7` | 5/2 |
| 151 | 125 | 26 | 24 | 2 | `23/2 + ½√7` | 5 |
| 234 | 198 | 36 | 36 | 1 | `29/2 + ½√7` | 13/2 |
| 747 | 83 | 664 | 2 | 663 | `53/2 + ½√7` | 25/2 |

Every side was read exactly: the extremes of the centre span are recovered in Q(√7) at
70-digit precision (`recover_scalar`, denominators ≤ 16, height ≤ 8) and the side is
`far − near + 1`, equal from x and from y.

**One word.** Every one of the five rows carries the unit word
`((1+√7)/4, (√7−1)/4)` — the word identified in run 92 — each verified on the circle
(`cos² + sin² = 1` exactly) after its own tilt angle is recovered from that row's radians.
n = 53 and n = 151 carry *other* tilts as well (3 and 2 distinct tilt angles); n = 747
carries 663, of which only 2 are the census word. So the word is shared; the alphabets are
not.

## 2. The law, and the split

Run 92's reading of n = 18 was `L = 3 + 2cos`, an *odd* rational part plus twice a cosine.
That is a special case. In general the corner squares of a ring sit at `±(k + c)` and are
flush, so

```
L = 2(k + c) + 1 = 2k + 3/2 + (c + s)          ring_side(cls, c, s, k)
```

because `c − s = 1/2` for this word. At `k = 1` this is `7/2 + ½√7` — n = 18 exactly —
and `2cos = 1/2 + ½√7`, so run 92's "odd part plus 2cos" is the `k = 1` case of a single
law.

Solving the law against each row's side gives an integer `k` for **two** rows and a
half-integer for **three**:

- integer: n = 18 (`k = 1`), n = 151 (`k = 5`);
- half-integer: n = 53 (`k = 5/2`), n = 234 (`k = 13/2`), n = 747 (`k = 25/2`).

So the answer to the question this run was given is: **the family does not split by the
side law — one law covers all five — it splits by parity of `k`**, two rows at integer `k`
and three at half-integer `k`. The half-integer cases are what a ring one half-square out of
step would give; they are not constructed here either.

## 3. The Ring family, and why it refuses

`glm_wheels` now carries the family, derivation-first:

- `ring_side(cls, c, s, k)` — the side above, derived from the corner squares' flushness;
- `ring_frame(cls, c, s, k)` — four corner squares at `±(k+c)` plus integer runs on the
  four edges (`2k−1` on the horizontal edges, `2k` on the vertical ones: ten axis squares at
  `k = 1`, the n = 18 count);
- `ring_candidates` — every point where a module square is tangent to one horizontal and one
  vertical frame square, `|d·e| = 1/2 + (|c|+|s|)/2`, solved exactly in the field;
- `ring_field` — builds each candidate, and the **exact gate is the arbiter**: a
  declaration is the ring only if it packs at clearance 0 with the side the law derives;
- `p_ring` — the claim, with the four-witness suite and the table calibration.

**No candidate gates.** Every `(k, word)` pair tried — Q(√7) and 45°, `k = 1, 2`, and every
candidate point in the tangency set — either collides or lands at the wrong side, and the
family refuses with the declared law `ring_unresolved`.

Reading the census's own pose says why. Its 18 squares are **10 boundary axis squares + 4
tilted squares in the four edge gaps + 4 tilted squares in a pinwheel around the centre**,
not four corner modules: the corner-module grammar is the wrong sentence *shape*. Two
further facts, both measured on the pose:

- the tilted squares do form 4 edge-to-edge pairs — every sibling pair's centre distance
  squares to `1 + 1e-9` in the table's 12-dp coordinates — so the *module* reading is
  right;
- but each module's distance to the frame it faces carries a slack of about 0.03–0.07, so
  the recorded pose is a **polished decimal packing, not an exact contact sentence**. There
  is nothing exact in the table to copy: the exact ring at that side is a construction, and
  its module placement has to be tangent to the frame *and* to its gap/pinwheel neighbours
  at once — a coupled two-parameter solve per corner that this run did not finish.

So the honest state of the request:

- the ring **law** is derived and it reproduces all five rows exactly, and its `k = 1`
  member is n = 18's side (`ring_side` = `7/2 + ½√7`, asserted against
  `(7 + √7)/2` in the field);
- the ring **sentence** is not constructed. `p_ring` refuses `ring_unresolved` at every
  tried `(k, word)`, the refusal is a declared law, and no Ring cell is registered, so the
  wheel reports nothing it cannot certify. **n = 18 is not yet built from grammar.**

## 4. Verification

`glm_wheels --selftest` **23 controls**, exit 0 (control 23 is the census recovery, the law,
the split and the ring's refusal); spin spatial **46/46** certified, sequences 6/7, lattice
24/28; float audit **200 decision functions, 0 offenders**;
`grammar_induction --selftest` 3/3; `qsqrt2 --selftest` 11/11; `field_triage --selftest`
4/4; `record_guard.py` OK. No row changed; `WHITEBOARD.md` and `submission.csv` untouched.

## 5. What would finish it

The pinwheel is the missing primitive: four tilted squares, C4-related, each tangent to the
next and to the two gap squares beside it. Given `(c, s)`, the four positions are one
two-parameter solve (the pinwheel's radius and its rotation offset both collapse under the
4-fold symmetry), and the ring then closes as `L = 2k + 3/2 + (c+s)` by construction. That
is the next run's first job, with the gate as the arbiter as usual.

Records `31`–`56`.
