# The attention simulator — attention from elementary operations, ported, measured

## Tier 0 — the coarse read

**Question.** Can the supplied paper's universal attention simulator (arXiv 2506.18739v2, "On the Existence of Universal Simulators of Attention") run on this substrate — attention built from the elementary operations the package already ships — and what does it cost, exactly?

**Verdict.** Yes, exactly: every elementary operation of the paper's construction agrees with the shipped ground truth with zero error, the simulator `U` reproduces the paper's own demonstrations with zero error on every exact stage (the paper's float error 3.38e-06 becomes 6.4e-105 at declared depth), and every head count matches the paper's tables — but the exponential is not exact and cannot be, two of the paper's stated conditions are looser than the truth (the coverage bound is conservative by a factor of two; the hierarchy corollary silently needs a padding mask), and on the live registers raw attention scoring is norm-dominated and inverts at low depth, so the module stays in the sandbox: a compiled library, not yet a faculty.

**Deciding figure.** 5 of 7 stages exactly zero against ground truth, 64 heads where the paper's accounting says 64, the coverage refusal measured at n = 7 where the paper's bound says n ≤ 3, and 1 of 12 rows where inner-product argmax agrees with the shipped nearest.

**Recomputed by.** `glm_universal.sandbox.attention_simulator.attention_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

**Code:** [`../glm_universal/sandbox/attention_simulator.py`](../glm_universal/sandbox/attention_simulator.py)
(the sandbox occupant; nothing the system computes with imports it)
**Run:** `PYTHONPATH=. python3 -c "from glm_universal.sandbox import attention_simulator as a; a.attention_report()"`
**Paper:** arXiv 2506.18739v2 (Dutta, Chakrabarty, Ansari, Das; the uploaded preprint).

Yes, exactly: every elementary operation of the paper's construction agrees with the shipped ground truth with zero error, the simulator `U` reproduces the paper's own demonstrations with zero error on every exact stage (the paper's float error 3.38e-06 becomes 6.4e-105 at declared depth), and every head count matches the paper's tables — but the exponential is not exact and cannot be, two of the paper's stated conditions are looser than the truth (the coverage bound is conservative by a factor of two; the hierarchy corollary silently needs a padding mask), and on the live registers raw attention scoring is norm-dominated and inverts at low depth, so the module stays in the sandbox: a compiled library, not yet a faculty.

---

## 1. What this study is

The paper proves that a network of transformer encoders can simulate *any*
single-layer attention `sigma(X A X^T) X V` using nothing but transposition,
matrix multiplication, softmax, hard selection and exact `3 x 3` inversion —
each an average-hard-attention program in RASP.  "Attention is not
primitive" is the paper's claim; this study asks whether the claim survives
contact with this substrate, whose discipline is exact rational arithmetic,
24-coordinate carriers, and refusals rather than silent approximation.

The questions were fixed before the measurements below were taken:

1. **Exactness.** Does the port agree with the shipped ground truth
   (`RationalMatrix.transpose`, `compose_matrices`, `product._inverse3`)
   with zero error, on every carrier-exact shape?
2. **Fidelity.** Does the port reproduce the paper's Figure 2 and Figure 3
   demonstrations, and does its head count match the paper's own Tables 1
   and 2 accounting?
3. **Coverage.** Where does the construction's feasibility rule actually
   bite, measured, versus where the paper's Theorem 6 says it bites?
4. **Cost.** What does simulating attention through elementary operations
   cost, against computing it directly — the simulator tax?
5. **Utility.** What does soft attention add over the shipped hard
   selection (`metric.nearest`) and bundling on a live register — and what
   does the register do to naive scoring?

Declared unreachable before the run: an *exact* softmax (transcendental —
no finite rational form exists; the paper itself approximates with
`2.73^x`), and a Lean specification (no Lean toolchain was available in the
measuring environment; the obligation is recorded in the promotion
checklist, not discharged).

## 2. The paper reproduced exactly

Figure 2 of the paper runs `U` on `3 x 3` inputs and reports float errors:
`3.376358e-06` at the softmax stage, `3.040329e-07` at the output.  This
port runs the same demo with exact arithmetic and a declared Taylor depth:

| stage | paper (float) | this port (exact) |
|---|---|---|
| `Y1 = X A` | ≈ 0 | 0 |
| `XT = X^T` | 0 | 0 |
| `Y2 = Y1 X^T` | ≈ 0 | 0 |
| `Y3 = softmax(Y2)` | 3.376358e-06 | 6.44e-105 |
| `Y4 = X V` | ≈ 0 | 0 |
| `Y = Y3 Y4` given its inputs | 3.040329e-07 | 0 |
| `Y` vs a fourfold-depth reference | — | 2.34e-105 |

The head count is 64 — exactly the paper's accounting: four matrix
multiplications at `r + c + rc = 15` heads each, one transposition head,
`r = 3` softmax heads.  The remaining differences from the paper's *printed*
values (4.9e-04) are its three-decimal printing, not computation.

Figure 3 of the paper inverts an integer matrix and prints decimals
(`4.333, -4.267, ...`).  The exact inverse is rational; the port returns
`13/3, -8/3, -4/3 / -64/15, 41/15, 19/15 / 2/5, -4/15, -1/15` with
determinant 45, and it agrees with the shipped Gauss–Jordan
`product._inverse3` exactly.

## 3. Ground truth and head counts

Transposition agrees with `RationalMatrix.transpose` with zero error on all
eight carrier-exact shapes (`1x24` … `24x1`).  Matrix multiplication agrees
with `compose_matrices` (or the direct exact product beyond 24 entries) on
every measured shape pair, and the measured head count equals `r + c + rc`
in every case — the paper's Table 2 law, verified rather than quoted:

| shape | measured heads | paper's `r + c + rc` |
|---|---|---|
| `3x3 . 3x3` | 15 | 15 |
| `3x4 . 4x4` | 19 | 19 |
| `2x12 . 12x2` | 8 | 8 |
| `4x6 . 6x4` | 24 | 24 |
| `6x4 . 4x6` | 48 | 48 |

## 4. The exponential: declared precision, and the inversion

Softmax cannot be exact over the rationals.  The port truncates the
exponential's Taylor series at a declared integer depth, and the depth is
*computed* from the measured shifted-logit range: after the row-max shift
every exponent is non-positive and the alternating-series remainder is at
most `R^(D+1)/(D+1)!` — a rigorous rational bound (`softmax_depth_needed`
solves for the least `D`).  On the paper's demo (range ≈ 7), measured error
tracks the bound down to 1e-100 territory.

The finding that matters came from the live register.  The lexicon's
carriers live at very different radii (`‖quark‖² ≈ 4.4e5`, `‖energy‖² ≈
2.3e3`), so raw identity scoring produces logit ranges of order `4e5`.  At
any affordable depth the truncated exponential does not approximate the
softmax — it **inverts** it: the even-power truncation of `e^{-R}` for
large `R` is a large *positive* number, so the weights order by distance
from the row maximum, backwards.  Measured (a four-row register block at
rational temperature 1/1000, range 24.7): top-1 correct on 0 of 4 rows for
every depth below the range, recovering to 4 of 4 only as the depth crosses
it.  A depth-24 softmax on the unscaled register looks like a plausible
distribution while being backwards — the most dangerous kind of wrong.

The substrate's own answer is Cauchy–Schwarz scaling:
`normalized_identity` scores with `A = I / max_j ‖x_j‖²`, which bounds every
score in `[-1, 1]` *by theorem*, keeps the paper's `X A X^T` form, and
preserves the argmax (a positive scale cannot reorder).  Measured range
after scaling: 0.74; depth needed: 13–14.

## 5. The simulator tax

The construction costs what the paper's Table 2 says it costs.  Measured on
square inputs, wall time against the direct exact formula:

| shape | heads (measured = formula) | time ratio |
|---|---|---|
| `3x3` | 64 | ×7 |
| `4x6` | 131 | ×9 |
| `6x6` | 199 | ×8 |
| `8x8` | 329 | ×13 |
| `12x12` | 685 | ×13 |

Every run agrees with the direct form exactly.  The tax is the price of
*proof*: the construction is the theorem made executable, and the theorem
was never a claim of efficiency — the paper's own comparison table counts
layers and heads, not seconds.

## 6. The register bridge: three scorings and the dial

Over the first rows of the live lexicon register, for the query row
`energy`:

* **Raw identity scoring** — the paper's form, unmodified — is
  norm-dominated: the largest carriers win every row (`quark`, `neutron`,
  `proton`), and at low depth it is the inversion of §4, not a softmax.
* **Cauchy–Schwarz-scaled scoring** is exact at depth 13, but still
  norm-dominated in ordering: the top attendees of `energy` are the
  register's giants, not its meanings.
* **The shipped controls** are the semantically valid selectors:
  `metric.nearest` (distance) returns `force`; the shipped
  `signed_cosine_squared` returns `mass` (0.989), `vector`, `golay`,
  `atom`, `matrix`.  Inner-product argmax agrees with the shipped
  distance-nearest on 1 of 12 measured rows — the `‖k‖²` term the
  softmax discards is doing all of the work on this register.

The temperature dial is where the paper's construction meets faculties the
substrate already ships.  Measured on twelve rows with scaled scores:

| temperature | 0 | 1 | 4 | 16 | 64 | 256 | 1024 |
|---|---|---|---|---|---|---|---|
| max weight | 1/12 | 0.089 | 0.109 | 0.212 | 0.720 | 0.9994 | 0.9999999999 |
| depth needed | — | 14 | 16 | 22 | 40 | 66 | 107 |

At temperature 0 the attended mixture is the coordinatewise mean of the
register — the rational bundle — *exactly*.  As the temperature grows the
weight concentrates on the inner-product argmax (a positive scale cannot
reorder, so the hard limit is the same selection at every temperature), and
the exact exponential's depth grows with the dial: the cost of exactness,
reported, not hidden.  The substrate's two shipped ends — bundling and
nearest — are the two ends of this dial, and the paper's `U` is a working
dial between them.

## 7. Coverage, hierarchy, multi-head

* **Coverage.**  Theorem 6 states `n <= min(d, dv)` (the sufficient form
  `k >= min(r, c)` of Lemma 5).  The literal condition `k(r+c) >= rc` is
  weaker, and the port enforces it as a refusal.  Measured at `d = 3`:
  the construction passes through `n = 6` and refuses at `n = 7` — the
  paper's bound of 3 is conservative by a factor of two.  On 24-wide
  carriers the construction covers 48-row blocks; register scale beyond
  that blocks, and the direct equal form (verified equal to the
  construction block-by-block) does not need to.
* **Hierarchy.**  Corollary 6.2's padding embedding is measured to need a
  **padding mask** the corollary does not mention: unmasked, the padded
  rows attend with weight `e^{-s}` each and the upper-left block comes out
  shrunk by 1.09e-05 (measured on a `2x3` guest in the MOG's own `4x6`
  frame as host); masked with an ordinary RASP `select` predicate, the
  embedding is exact.  The corollary is true with the paper's own masking
  machinery applied; it is not true as literally printed.
* **Multi-head.**  Theorem 9's `H` independent simulations agree with the
  direct equal form at the same depth (interference-freedom, measured),
  and Lemma 8's identify/shift rearrangement is verified as the exact
  permutation it claims to be.

Two smaller scholarship notes from the porting itself: Algorithm 3 line 5
indexes the output-combining attentions with the inner dimension `k` where
the construction requires the column count `c` (the paper's own RASP
Listing 3 writes the `c`-strided form); and Algorithm 2's block-printed
attention matrices do not parse into the row spans the accompanying text
states, while its Listing 2 does — the port follows the listings in both
cases and this paragraph is the record.

## What is proved rather than measured

Nothing here is machine-checked yet — the Lean obligation is open and
recorded in the promotion checklist.  What *is* proved, by exact arithmetic
rather than by probability, is agreement: every elementary operation agrees
with the shipped ground truth with zero error on every measured shape, and
the construction agrees with the direct formula given identical inputs on
every measured run.  The Cauchy–Schwarz score bound `|<x_i, x_j>| <= k` and
the alternating-series remainder bound `R^(D+1)/(D+1)!` are theorems the
module's depth computation relies on; both are one-line Lean candidates in
the style of `Constants.lean`.  The natural Lean file would state: the
transposition construction equals `RationalMatrix.transpose`; the
multiplication construction equals `compose_matrices` where the carrier
fits; and masked hierarchy embedding equals direct simulation — the three
statements this study only measures.

## What it decides, and what it does not

It decides that the paper's concept **runs on this substrate exactly**,
with costs the paper's own tables predict, and with two precision
corrections the substrate forced (scaled scoring, computed depth) and two
corrections to the paper itself (the conservative coverage bound, the
missing mask).  It does not decide that the system should *use* it: no
query kind consumes soft attention, nothing in the shipped package imports
the module, and on the meaning registers the shipped distance-nearest and
cosine-squared selectors are the semantically valid forms while raw
attention is norm-dominated.  Where the construction plausibly earns its
place is the dial of §6 — exact mixtures between the bundle and the hard
selection the substrate already ships — and that case is not made by this
study; it is the first line of the work that would follow promotion.

## Limits

* The softmax error is bounded and measured, never zero; the bound is for
  the exponential stage, and the end-to-end propagation is measured against
  a fourfold-depth reference rather than bounded symbolically.
* The register experiments cover the lexicon register (149 rows; dial on
  the first 12) and one four-row construction block; the other seven
  registers were not dialled, and physics-scale carriers (range 4e5) were
  scaled rather than computed at raw depth, because the exact arithmetic
  at that range needs five-digit-exponent integers and minutes per entry.
* The `3 x 3` inversion is the paper's own scope; arbitrary-order inversion
  needs the recursive cofactor the paper itself declines to build.
* This study's numbers are the recorded run of 13 October 2026 and are not
  yet wired into the corpus's generated blocks; re-running the commands
  below re-derives every one of them.

## Re-running it

```bash
cd overlay
PYTHONPATH=. python3 -c "from glm_universal.sandbox import attention_simulator as a; import json; print(json.dumps(a.promotion_checklist(), default=str, indent=2))"
PYTHONPATH=. python3 -c "
from glm_universal.runtime.session import GeometricSession
from glm_universal.sandbox import attention_simulator as a
print(a.attention_report()['paper_demo']['stage_errors'])
print(a.temperature_report(GeometricSession()))"
PYTHONPATH=. python3 -c "from glm_universal import sandbox; print(sandbox.occupancy_report()['modules'])"
```

The experiment harness that produced the figures this memo quotes (head
counts, precision and inversion curves, tax, dial) lives outside the
package, at `scripts/attention_experiments.py` in the working tree that
produced this study; its figures and `results.json` are archived beside
this document.
