# The two companion studies, tested

**What this document is.** Two companion preprints sit beside the main GLM
paper:

* **`GLM_Generators_Containers (2).pdf`** — *The Generators and Containers of
  Real Processes*: eight constants profiled through three "containers" — the
  algorithmic one (the generator that produces the constant, and how many
  steps it needs), the temporal one (the delta-sigma stream whose running
  average converges to it) and the geometric one (the constant projected into
  24 coordinates and tested against the convex hull of the Leech minimal
  vectors);
* **`GLM_Iteration_Study (1).pdf`** — *GLM Iteration Study and Lattice
  Survey*: a parametric recurrence over the odd primes run in three arithmetic
  regimes, and a survey of the code-lattice landscape the GLM's substrate sits
  inside.

[`GLM_STUDY_CATALOG_AUDIT.md`](GLM_STUDY_CATALOG_AUDIT.md) already audits
`glm_study_findings_catalog.md`, which *summarises* both of these. A summary
loses the definitions, and several of that ledger's open verdicts were open
only because the summary never stated the projection, the indexing or the
alphabet the study used. The preprints do state them. This document is
therefore a second, finer ledger over the same material: it tests the studies'
own tables, row by row, against the definitions the studies give.

Nothing below is quoted. Every figure is produced by the call that settles it,
on demand, by `glm_universal.reasoning.companion` and the instrument it is
built on, `glm_universal.reasoning.containers`. Ask the running system:

```bash
cd overlay
PYTHONPATH=. python3 GLM.py -q "report companion"  --verify-tct
PYTHONPATH=. python3 GLM.py -q "report containers" --verify-tct
```

Both return `VERIFIED True`: column 3 of the Three Column Thinking payload
re-derives every figure in a fresh interpreter and compares it with what was
printed.

**No float is constructed anywhere in either module.** Precision is decided by
integer comparison against a 200-bit reference, the streams are exact
`Fraction` recurrences, and the hull certificates are integer inequalities.

---

## The four verdicts

| verdict | meaning |
|---|---|
| **confirmed** | the package reproduces the study's figure |
| **refuted** | the package reproduces a *different* figure; the ledger records what is true instead |
| **not reproduced** | the claim is well posed, but the measurement does not show what it says — most often because a parameter the figure depends on is never stated |
| **not implemented** | the claim describes a structure the package does not have, and is recorded as an open gap rather than as a pass |

## The result

**49 testable claims: 26 confirmed, 17 refuted, 5 not reproduced, 1 not
implemented** — 28 drawn from the first study and 21 from the second.

Four findings are worth stating plainly.

1. **The hull census is unestablished by its own method.** The first study
   decides whether a projected constant lies in the convex hull of the
   196,560 Leech minimal vectors by running a linear program over a *sample*
   of 150 of them. A sample can only ever establish *inside*: a convex
   combination over a subset is a convex combination over the whole set, but
   the infeasibility of the sampled program says nothing about the full one.
   Every "outside" verdict in the study's Table 3 is therefore unsupported —
   and two of them are wrong. Here both verdicts are certificates checked
   against all 196,560 vectors, and no linear program is needed at all: the
   support function `max_p ⟨u, p⟩` is one pass.
2. **The wobble signature is a fingerprint of the fractional part and of
   nothing else.** Every column of the study's Table 2 — entropy, mean run
   length, autocorrelation at each lag — is a closed form in the target,
   proved of the exact modulator in `RequestProject/GLM/Sturmian.lean`. Two
   different constants with the same fractional part have the same signature,
   so the ten-thousand-tick measurement tests the modulator, not the constant.
3. **The recurrence runs to minus infinity, not plus.** The accumulative rule's
   closed form is `1 − ((p−1)/p)((p+1)/p)^n`: one minus a growing positive
   term. What grows is `|X_n|`, which is what the study's own figure captions
   plot; at `p = 3` and `n = 200` the exact value is `−6.48e+24`.
4. **Three of the lattice survey's arithmetic identities are wrong while their
   totals are right.** The octad count 97,152 is `759 × 2⁷`, not `759 × 2⁸`,
   because only the even sign patterns lie in the lattice; the odd-coset count
   98,304 is `24 × 4096`, not `24 × 2²³`, because the sign pattern is a Golay
   codeword; and the claimed covering radius `√(2·47/13) ≈ 2.69` is below the
   packing radius `2.83`, which no covering radius can be.

---

## 1. The algorithmic container

`containers.precision_bits` returns the largest `b` with
`|x − x*| / |x*| ≤ 2⁻ᵇ`, decided by integer comparison against a reference
held to 200 bits. No logarithm is taken. Steps are counted from `x₀`, the
generator's first value — the study does not state an indexing, and this is
the one that reproduces its `pi` and `e` rows.

| constant | 10 bits | 30 bits | 50 bits | verdict |
|---|---|---|---|---|
| `sqrt(2)` (Heron) | 3 | 4 | 5 | confirmed |
| `phi` (Heron on 5) | 3 | 5 | 6 | confirmed |
| `pi` (Machin) | 1 | 5 | 9 | confirmed |
| `e` (series) | 5 | 11 | 17 | confirmed |
| Champernowne | 10 | 29 | never | not reproduced (the study gives 11, 30) |
| Liouville | 1 | 2 | 2 | not reproduced (the study gives 2, 3, 3) |
| Omega surrogate | 6 | 30 | never | not reproduced (no seed is stated) |
| `1/3` (rigid) | 0 | 0 | 0 | confirmed |

The two "not reproduced" digit rows are off by exactly one throughout, which
is what a row counting *terms revealed* rather than *step index* looks like.
The Omega surrogate cannot be reproduced at all: the study states the
congruential multiplier, modulus and increment, but neither the seed nor the
rule that reads a bit out of the state.

Heron's quadratic convergence is confirmed directly: the correct bits of
`sqrt(2)` at steps 0…6 are `1, 4, 9, 19, 39, 80, 161`.

## 2. The temporal container

The stream statistics are `reasoning/wobble`'s, which prints the proved closed
form beside every measured column. Seven of the eight rows of the study's
Table 2 reproduce to the tabulated decimals; the Omega surrogate is the
exception, for the same missing-seed reason.

What the ledger records against the study is the *reading* of the table, in
four places:

* the signature is a closed form of the target, not a fingerprint of the
  constant (**refuted**);
* the algebraic irrationals do not have decaying autocorrelation — a Sturmian
  stream is almost periodic, so the value recurs; `sqrt(2)` gives the same
  `−0.657` at lag 1 and at lag 100, in the study's own table (**refuted**);
* the autocorrelation of `e` is negative at lag one, so "positive at all lags"
  is false as written (**refuted**);
* the rigid baseline's stream is **not** `010101…`. That word has density
  `1/2`; a first-order modulator chasing `1/3` emits one 1 in every three
  ticks, and its least period is 3 — the denominator of the target
  (**refuted**). The tabulated autocorrelation `−1/3` is exactly the
  period-three value on the ±1 alphabet, so the study's figure and its
  explanation cannot both hold.

**A note on periods.** The least period of the modulator's stream for a
rational target is the denominator of that target in lowest terms, so the
package *decides* the period from the target and then checks it, rather than
searching a window for a repetition. A search is not safe here: over 400
places, `sqrt(2)`'s stream repeats at 169 — the denominator of the convergent
`70/169` — and disagrees with its own 169-shift at place 407.
`containers.near_period_coincidence` records exactly that.

## 3. The geometric container

The study projects a scalar `c` to `vᵢ = 4c/(i+1)` and asks whether the result
lies in the convex hull `K` of the 196,560 minimal vectors. Both verdicts are
certificates here:

* **outside** — an integer direction `u` with `⟨u, x⟩ > max_p ⟨u, p⟩` over all
  196,560 vectors. Two directions are used: the study's own proposal `u = x`,
  and one tuned by descent, which is what settles Champernowne's constant.
* **inside** — the target lies in `{x : |x|₁ ≤ 8, |x|∞ ≤ 4}`, whose extreme
  points are exactly the 1,104 minimal vectors of shape `(±4, ±4, 0²²)` and
  which is therefore contained in `K`.

| constant | ‖v‖² | ‖v‖₁ | ‖v‖∞ | verdict | settled by |
|---|---|---|---|---|---|
| `sqrt(2)` | 51.332 | 21.360 | 5.657 | outside | the target direction |
| `phi` | 67.194 | 24.439 | 6.472 | outside | the target direction |
| `pi` | 253.313 | 47.450 | 12.566 | outside | the target direction |
| `e` | 189.647 | 41.056 | 10.873 | outside | the target direction |
| Champernowne | 19.082 | 13.023 | 3.449 | outside | the tuned direction |
| Liouville | 0.311 | 1.661 | 0.440 | **inside** | the cross-polytope |
| Omega surrogate | 9.290 | 9.087 | 2.406 | undetermined | neither certificate fires |
| `1/3` | 2.852 | 5.035 | 1.333 | **inside** | the cross-polytope |

Seven of the eight rows are settled; the eighth is reported `undetermined`,
which is the honest answer and not a failure.

Three consequences for the study's Table 3:

* "only Liouville's constant sits inside" is **refuted**: `1/3` is inside as
  well, with `‖v‖₁ = 5.035 ≤ 8` and `‖v‖∞ = 1.333 ≤ 4`.
* The threshold is not the Leech minimal norm. Because every target is a
  positive multiple of one direction, both tests reduce to a comparison on
  `c`: the projection is **inside for every `c ≤ 0.5297`** and **outside for
  every `c > 0.8011`**. Champernowne's constant is 0.862 — well under the
  study's stated 1.4 — and is separated by an explicit functional.
* The margin column is **not reproduced** by any distance: it runs about 3
  below the norm for the first five rows and neither 3 below nor any multiple
  of the norm for the other three, and it contradicts its own caption, since
  two rows carry negative margins and are listed as outside.

The target-norm column itself is **confirmed** for seven of the eight rows,
which is what fixes the projection as the one the study used.

## 4. The recurrence

Both rules have exact closed forms over `ℚ`, and the package checks them
rather than trusting them: **854 of 854 iterates agree exactly**, over seven
primes, both rules and steps 0 to 60. The fixed points are `−1` (contractive)
and `+1` (accumulative, unstable). Error amplification is exact rather than
asymptotic — both maps are affine, so a perturbation `d` of `X₀` moves `Xₙ` by
exactly `aⁿd` — and `1/p` has no finite binary expansion for any odd prime, so
none of these trajectories is natively representable in IEEE-754.

The one refutation is the direction of divergence, item 3 above.

## 5. The lattice survey

Confirmed: the ladder `48 → 98,256 → 196,560` by direct enumeration on the
extended binary Golay code, at minimal squared norms `16, 32, 32`; the growth
factors 2,047 and 2.0005; Construction A at kissing 48; agreement of the
ladder's Construction C with an independently built Leech lattice over 721
membership questions with no disagreement; the packing radius `√8`; the
unique nearest codeword out to distance 3 and exactly six at distance 4; and
the existence of 23 Niemeier root systems in bijection with the deep-hole
types.

Refuted:

* the octad and odd-coset arithmetic (item 4 above), whose *totals* are right;
* "every congruence condition is necessary" — the two congruence conditions
  are, but dropping the odd glue coset leaves Construction B, whose minimum
  squared norm is still 32. The coset is necessary for the lattice to *be* the
  Leech lattice, not to keep short vectors out;
* the minimum squared norm of Construction A stated as `min(4, d_min)`, which
  differs from the package's 16 by the factor of 4 the study's own figure
  uses;
* the covering radius (item 4 above);
* "distance 5 or more is beyond the covering radius and decoding fails" — the
  covering radius is 4, so nothing is beyond it, and the real failure is
  silent miscorrection: a weight-5 error lies inside the packing radius of the
  codeword supported on the octad containing it, so a bounded-distance decoder
  returns a wrong answer with no flag;
* the list of 23 root systems, which omits `A_24` and `D_10 E_7²`, contains
  `A_23`, which is not a Niemeier root system, and repeats `D_16 E_8` — which
  is how it still reaches 23 entries.

Not implemented: the two extremal rows of the canonical-pairings table, the
Quebbemann lattice `Q_32` and `P_48n`. The package builds and can decide the
`d = 4, 8, 24` rows; it has no 32- or 48-dimensional construction, so those
rows are recorded as an open gap rather than as a pass.

---

## How to re-run it

```bash
cd overlay
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_containers.py \
                              glm_universal/tests/test_companion.py -q
PYTHONPATH=. python3 GLM.py -q "report containers" --verify-tct
PYTHONPATH=. python3 GLM.py -q "report companion"  --verify-tct
```

The verdicts above are allowed to move when the package does — that is what a
live ledger is for. What the tests hold fixed is that every claim is settled
by a computation, that a disagreement says what holds instead, and that the
hull verdicts are the census's rather than the ledger's.
