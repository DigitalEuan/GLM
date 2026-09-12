# The wobble landscape: is the fine-structure constant structurally distinctive?

## Tier 0 — the coarse read

**Question.** Is alpha's arithmetic signature distinctive within the space the Golay–Leech substrate permits, or is it what a magnitude-matched number looks like?

**Verdict.** The signature is not distinctive enough to spend on: the score falls below the gate that was fixed before the measurement, so the landscape enumeration was not run.

**Deciding figure.** One primary statistic against a magnitude-matched null, corrected for the 4 statistics tried, read against the gate of 3 bits.

**Recomputed by.** `glm_universal.reasoning.wobble_landscape.landscape_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

**Read this first.** Two figures the existing documents quote were re-examined
while this study was being designed, and both readings are corrected below
before anything new is measured.

* The **"wobble entropy 0.062"** row for alpha in
  [`source_material/glm_study_findings_catalog.md`](../source_material/glm_study_findings_catalog.md)
  is not a measurement of structure. The density of ones in the stream is
  exactly the slope, so the Shannon entropy of the raw bit stream is the binary
  entropy of the slope and nothing else: it carries the *magnitude* of alpha
  and no further information. Two numbers with the same fractional part have
  the same wobble entropy to the last bit. It is therefore refused as a
  statistic here.
* The **Golay-correctability** reading — that a 24-bit word landing within
  distance 3 of a Golay codeword would be a structural coincidence — is wrong
  by the code's own arithmetic. The number of 24-bit words within Hamming
  distance 3 of some codeword is `4096 * (1 + 24 + 276 + 2024) = 9,523,200` of
  `16,777,216`, so `d_min <= 3` has probability `2325/4096` under a uniform
  word: it is the **majority case**, worth less than one bit. The corrected
  reading is in §5.

**What this document is.** A pre-registered test, written and committed before
the measurement module was written. It does **not** derive alpha and must not
be read as deriving it. It asks one question — is alpha's gap-structure
signature unusual against a stated null? — and answers with one number.

---

## 1. What is already known, and is used rather than simulated

The delta–sigma modulator chasing a constant `t` in `(0, 1)` emits
`b_n = floor((n+1)t) - floor(n t)`, which is the **Sturmian (mechanical) word of
slope `t`**. That identity is `GLM.Info.dsBit_eq_floor_diff` in
[`RequestProject/GLM/Sturmian.lean`](../RequestProject/GLM/Sturmian.lean), and
everything below is a consequence of it rather than an experimental finding.

Write `s = 1/t`. The `j`-th one sits at `n_j = ceil(j*s) - 1`, so the gap
between consecutive ones is

```
gap_j = ceil((j+1)*s) - ceil(j*s)
```

and `floor(s) <= gap_j <= floor(s) + 1` for every `j` — **at most two distinct
gap lengths**, which is the two-distance form of the Three-Distance Theorem for
the first-return map. (The three-distance count appears at finite `N` only
because the last, truncated gap is counted as a third length.) The bound is a
theorem, not an observation:
[`RequestProject/GLM/WobbleLandscape.lean`](../RequestProject/GLM/WobbleLandscape.lean),
`GLM.Landscape.gap_mem_pair`.

The multiplicities are closed-form too. With `a_0 = floor(s)` and
`t_1 = s - a_0` the fractional part, the number of long gaps among the first
`K` gaps is exactly

```
long(K) = ceil((K + 1) * t_1) - 1
```

so the long-gap frequency tends to `t_1`, and the sequence of gap *types* is
itself the Sturmian word of slope `t_1`. Iterating is the Gauss map, so the
whole ladder of gap spectra is the **continued fraction of `s`**, stage by
stage: this is Ostrowski numeration, and no simulation is needed to obtain it.
The module implements the closed form and checks it against a finite simulated
run at a stated depth; the test perturbs the closed form and requires the
comparison to fail, so a passing check is evidence and not a tautology.

Two consequences are stated plainly here because older material in this
repository reads them the other way.

* **The entropy of the stream is `H2(t)`.** It is a function of the magnitude
  of `t` alone. It is not used as a statistic in this study.
* **The run length ~137 for alpha is `a_0` of the continued fraction of
  `1/alpha`, and nothing more.** `1/alpha = 137.03...`, so the gaps are 137 and
  138 and the longest run of zeros is 137. It is not caused by the lattice, it
  is not evidence of anything, and it is a restatement of the value of alpha.

---

## 2. The pre-registered primary test

The statistic, the nulls, the tail and the gate are fixed before any
measurement is taken. Here they are.

**Target.** `alpha = 7.2973525643e-3` (CODATA 2022) as the exact
`Fraction(72973525643, 10**13)`. The study reports the continued fraction of
`1/alpha` as computed from that exact value; the expansion quoted in the brief
that commissioned this study is checked against the computation rather than
copied.

**Primary statistic.** `S(t)`, the **stage-0 long-gap frequency**: the
frequency of the longer of the two gap lengths in the Sturmian word of slope
`t`, which by §1 is exactly `frac(1/t)`. Equivalently the gap spectrum at
Ostrowski stage 0 is the pair of lengths `(floor(1/t), floor(1/t) + 1)` with
frequencies `(1 - S, S)`.

*Why this one.* It is the frequency vector of the two gap lengths at a stated
stage, so it is a statistic of the *structure* of the stream rather than of its
density; it is exactly computable in closed form from the continued fraction,
so chance can be enumerated rather than sampled; it is invariant under the
depth of the run, so the depth sweep tests stability rather than defining the
answer; and it is not the bit entropy, which §"Read this first" refuses. It is
also the statistic the substrate claim would have to move if it moved anything:
a slope whose gap structure the lattice preferred would show as an unusual
frequency vector, not as an unusual density.

**Tail.** Two-sided about the balanced value `1/2`:

```
p_tail = Pr[ |S(x) - 1/2| >= |S(alpha) - 1/2| ]  for x drawn from the null
```

Two-sided because "distinctive" means far from a balanced two-gap mixture in
either direction, and because a one-sided choice would be a direction picked
after knowing which side alpha falls on.

**Nulls, both magnitude-matched, both exhaustive, neither sampled.**

* **Null B (primary) — stride-selected exact rationals.** Every rational
  `j / 10**7` lying strictly inside `(1/138, 1/136)`. The stride and the
  interval are stated, the enumeration is complete, and `p_tail` is an exact
  `Fraction`: a count over a count.
* **Null A (secondary) — the `k`-sweep.** The numbers whose reciprocal is
  `[137; k]` exactly, that is `1 / (137 + 1/k)`, for `k = 1 .. 100`. Reported
  beside the primary, and **not** primary, for a reason fixed in advance: the
  answer under this null is entirely a function of the measure put on `k`, and
  a uniform sweep over `k` is a choice with no justification behind it, whereas
  the stride null carries the natural measure of the interval. Where the two
  disagree, that disagreement is the finding about the null, not about alpha.

**Chance.** Computed by exhaustive enumeration in exact arithmetic in both
cases. Nothing is sampled and no seed is used anywhere in this study.

**Score.** One number:

```
B = log2(1 / p_tail) - log2(m)
```

with `m = 4` the number of statistics tried anywhere in this study that could
have been reported as the primary one: the stage-0 long-gap frequency, the
stage-1 long-gap frequency, the stage-1 partial quotient `a_1`, and the Golay
minimum distance `d_min`. The correction is applied whatever the outcome. `B`
is computed as an exact rational bracket around `log2`, never as a float.

**Depth.** One depth is primary: the closed-form statistic is depth-free, and
the empirical estimate quoted beside it is taken at `K = 100` gaps. The sweep
over `10, 20, 50, 100, 500` is a **stability check and is exploratory**.

---

## 3. The decision tree, fixed before measuring

| outcome | reading | what happens next |
|---|---|---|
| `B < 1` | not evidence | stop; record the null result; the landscape enumeration is **not** run |
| `1 <= B < 3` | weak, and not enough to spend on | stop; record it as weak; the landscape enumeration is **not** run |
| `B >= 3` | worth spending on | continue to the substrate-native enumeration: the dimensionless subset of the register quantities the controller can reach, the same primary statistic for each, alpha's rank and the fraction at or below it, with the pruning ladder reported filter by filter |

`B < 1` is a publishable result here and is the expected one. A null result
that was pre-registered costs the project nothing and protects it from the
alternative, which is a statistic chosen after the data and reported as though
it had been chosen before.

---

## 4. The verdict: one number, and what it is not

The statistic, the nulls, the tail and the gate above were fixed and committed
before the measurement module existed. What follows is the measurement. **The
signature is not distinctive enough to spend on: the score falls below the gate
that was fixed before the measurement, so the landscape enumeration was not
run.**

<!-- generated: landscape-verdict -->
**B = 1.79 bits** against the magnitude-matched stride null: 77 of 1066 exact rationals of `(1/138, 1/136)` at stride 10,000,000 have a gap-frequency deviation at least as large as alpha's, a tail of `77/1066` and 3.79 bits raw, 1.79 after correcting for 4 statistics tried.  By the gate fixed before the measurement that is **weak**: stop; record it as weak, and the landscape enumeration is not run (`enumerate: False`).

Under the secondary `k`-sweep null the same statistic scores -1.57 bits (tail `37/50`), which is *not evidence*; the two nulls disagree, and that disagreement is a fact about the measure a `k`-sweep puts on `k` rather than about alpha.

**What it is not.**  It is not a derivation of alpha, and it is not a claim that the substrate selects alpha.  The Golay reading, which looks like 0.82 bits against a uniform word and more against a naive one, is worth 0.00 bits against the magnitude-matched null: every one of the 1066 members reproduces alpha's `d_min = 0`.
<!-- end generated -->

Read in words: `1/alpha` lies within about 0.036 of an integer, and among
magnitude-matched numbers that happens about seven times in a hundred. That is
the whole of the finding. It is worth under two bits after the multiplicity
correction, it is a restatement of the value of alpha rather than an
explanation of it, and by the pre-registered tree it stops the study.

---

## 5. Phase 1: alpha's gap spectrum, exactly

<!-- generated: landscape-spectrum -->
| Ostrowski stage | short gap | long gap | long-gap frequency |
|---|---|---|---|
| 0 | 137 | 138 | 0.035999 |
| 1 | 27 | 28 | 0.778412 |
| 2 | 1 | 2 | 0.284666 |
| 3 | 3 | 4 | 0.512887 |
| 4 | 1 | 2 | 0.949746 |
| 5 | 1 | 2 | 0.052913 |

The continued fraction of `1/alpha` is `[137, 27, 1, 3, 1, 1, 18, 1, 8, 1]` — computed from the exact CODATA 2022 value, not copied.  Stage 0's short gap, 137, is the run length the older material reports: it is `a_0` and nothing more.  The Shannon entropy of the raw stream is 0.062 bits, which is `H2(alpha)` — a function of the magnitude alone, which is why it is not the statistic.

**The closed form against the run.**  Over 20,000 emitted bits the stream shows 144 gaps, of lengths [137, 138] and no others (`lengths_hold: True`); the closed form predicts 5 long gaps and the run has 5 (`count_holds: True`).
<!-- end generated -->

The brief that commissioned this study quoted the expansion of `1/alpha` as
`[137; 28, 1, 1, 2, 1, 1, 4, ...]`. Computed from the exact CODATA 2022 value
it is not: the second partial quotient is 27, not 28, and the tail differs from
the fourth term. The table above is what the arithmetic gives, and it is the
table the test pins. Nothing downstream depends on which of the two it is — the
statistic is the *frequency*, `frac(1/alpha)`, and 27 versus 28 is the integer
part of its reciprocal — but a quoted expansion that does not survive
recomputation is exactly the kind of figure directive D6 exists to catch.

The depth sweep, exploratory:

<!-- generated: landscape-depth -->
| gaps | bits needed | estimate of S | distance from the closed form |
|---|---|---|---|
| 10 | 1,380 | 0.000000 | 0.035999 |
| 20 | 2,760 | 0.000000 | 0.035999 |
| 50 | 6,900 | 0.020000 | 0.015999 |
| 100 | 13,800 | 0.030000 | 0.005999 |
| 500 | 69,000 | 0.036000 | 0.000001 |

Exploratory.  The primary statistic is the closed form and is depth-free; this table only shows how fast a finite run would reach it, and the estimate at any depth is exact.
<!-- end generated -->

The comparison rows — the other dimensionless constants of physics and the
substrate's own constants, read at the same resolution:

<!-- generated: landscape-comparison -->
| rank | constant | as taken | gap lengths | S | tail | bits | partial quotients |
|---|---|---|---|---|---|---|---|
| 1 | alpha | 7.2973525643e-3 (CODATA 2022) | 137/138 | 0.035999 | `77/1066` | 1.79 | [137, 27, 1, 3, 1, 1] |
| 2 | pi | pi | 7/8 | 0.062513 | `67/533` | 0.99 | [7, 15, 1, 292, 1, 1] |
| 3 | Y | 1/(pi + 2/pi), as carried | 3/4 | 0.778212 | `237/533` | -0.83 | [3, 1, 3, 1, 1, 27] |
| 4 | MONAD | pi * phi * e | 1/2 | 0.223122 | `238/533` | -0.84 | [1, 4, 2, 13, 3, 1] |
| 5 | sin^2 theta_W | 0.23122 (PDG, MS-bar) | 4/5 | 0.324885 | `346/533` | -1.38 | [4, 3, 12, 1, 4, 1] |
| 6 | (g-2)/2 | 0.00115965218059 (electron anomaly) | 862/863 | 0.327530 | `699/1066` | -1.39 | [862, 3, 18, 1, 4, 3] |
| 7 | phi | (1 + sqrt(5))/2 | 1/2 | 0.618034 | `407/533` | -1.61 | [1, 1, 1, 1, 1, 1] |
| 8 | e | e | 1/2 | 0.392211 | `837/1066` | -1.65 | [1, 2, 1, 1, 4, 1] |
| 9 | Q | Y + 1/8 | 2/3 | 0.566238 | `925/1066` | -1.80 | [2, 1, 1, 3, 3, 1] |
| 10 | m_p/m_e | 1836.152673426 (CODATA 2022) | 6/7 | 0.549928 | `480/533` | -1.85 | [6, 1, 1, 4, 1, 1] |
| 11 | alpha_s(M_Z) | 0.1180 (PDG) | 8/9 | 0.474576 | `506/533` | -1.93 | [8, 2, 9, 3] |

The tail column applies *alpha's* null — the stride-selected rationals of `(1/138, 1/136)` — to each row's own deviation, so it answers "how unusual would this signature be at alpha's magnitude".  It is a comparison, not a claim that these constants live in that interval.  The ranking is exploratory: the pre-registered test is the alpha row against its null, above.
<!-- end generated -->

Alpha does lead that table. It is eleven rows chosen by hand, so the lead is
worth exactly what a lead among eleven hand-chosen rows is worth, which is why
the pre-registered test is against an enumerated null of a thousand and not
against this table.

---

## 6. Phase 2: the neighbourhood test, which decides the study

<!-- generated: landscape-primary -->
| null | members | at least as extreme | tail | raw bits | corrected bits |
|---|---|---|---|---|---|
| stride 10,000,000 in (1/138, 1/136) — **primary** | 1066 | 77 | `77/1066` | 3.79 | 1.79 |
| reciprocal [137; k], k = 1 … 100 — secondary | 100 | 74 | `37/50` | 0.43 | -1.57 |

`S(alpha) = 0.035999` exactly `2626986909/72973525643`, so the two gap lengths are 137 and 138 with frequencies 0.964001 and 0.035999.  The empirical estimate at the primary depth of 100 gaps is 0.030000.

Gate: 1.79 bits is **weak** (not evidence below 1, weak below 3).  Stop; record it as weak.
<!-- end generated -->

The two nulls disagree by more than four bits, and the study said before
measuring which of them would be primary and why. The `k`-sweep puts a uniform
measure on the partial quotient `k`, under which large `k` is *common* — 74 of
100 members of that null are at least as extreme as alpha — while the stride
null carries the natural measure of the interval, under which large `k` is
rare. Neither is wrong; they are answers to different questions, and reporting
only the one that flatters the target is the failure this pre-registration was
written to prevent.

---

## 7. What this study does not do

* It does **not** derive alpha, and no reading of any number below supports
  that.
* It does **not** claim the run length 137 is caused by the lattice, that the
  substrate selects alpha, or that the reachable register quantities are
  candidate values of alpha. They are quantities the controller can build; that
  is all.
* It does **not** search over modular evaluations, `p`-adic amplitudes or
  Adinkra constructions for something near `1/137.036`. A mapping from those
  frameworks to alpha that is fixed after seeing the answer is fitting, and a
  bit score computed from it means nothing. §10 lists them as bridges not yet
  tested, with what a falsifiable test would look like, and marks them
  unimplemented.
* It does **not** report a statistic chosen after seeing the data as if it were
  the primary test. The primary statistic is fixed in §2, above, and the
  document is committed before the measurement module exists.

---

## 8. The Golay question, done properly

The exact null comes first, before any word is decoded. The binary Golay code
has 4096 codewords in a space of `2**24 = 16,777,216` words and minimum
distance 8, so the balls of radius 3 about the codewords are disjoint and

```
|words within distance 3| = 4096 * (1 + 24 + 276 + 2024) = 4096 * 2325 = 9,523,200
```

giving `Pr[d_min <= 3] = 9523200 / 16777216 = 2325 / 4096` exactly, which is
about 0.82 bits. The identity is `GLM.Landscape.golay_ball_count` in
[`RequestProject/GLM/WobbleLandscape.lean`](../RequestProject/GLM/WobbleLandscape.lean).
The full coset-weight distribution — 1, 24, 276, 2024, 1771 cosets of weight 0,
1, 2, 3, 4 — is recomputed from the code itself, so the tail at any observed
distance is exact.

Against that null the study reports alpha's `d_min` at depths 24, 48 and 72 —
the first `D` bits of the stream cut into `D/24` words — and the same statistic
for every other dimensionless constant in the comparison table. The correction
to the plan is stated where the measurement is: `d_min <= 3` is not a
structural coincidence, it is what the majority of words do.

<!-- generated: landscape-golay -->
| distance to the code | cosets | probability | cumulative |
|---|---|---|---|
| 0 | 1 | `1/4096` | `1/4096` |
| 1 | 24 | `3/512` | `25/4096` |
| 2 | 276 | `69/1024` | `301/4096` |
| 3 | 2,024 | `253/512` | `2325/4096` |
| 4 | 1,771 | `1771/4096` | `1` |

So `d_min <= 3` holds for 4,096 × (1 + 24 + 276 + 2024) = 9,523,200 of 16,777,216 words, a probability of exactly `2325/4096` and 0.817 bits.  It is the majority case.  The identity is `GLM.Landscape.golay_code_ball_count`, proved of the substrate's own code.

| constant | slope | d_min by depth | d_min | all-zero word |
|---|---|---|---|---|
| alpha | 0.007297 | 24: 0, 48: 0, 72: 0 | 0 | True |
| m_p/m_e | 0.152673 | 24: 3, 48: 3, 72: 3 | 3 | False |
| sin^2 theta_W | 0.231220 | 24: 3, 48: 3, 72: 3 | 3 | False |
| alpha_s(M_Z) | 0.118000 | 24: 2, 48: 2, 72: 2 | 2 | False |
| (g-2)/2 | 0.001160 | 24: 0, 48: 0, 72: 0 | 0 | True |
| pi | 0.141593 | 24: 3, 48: 3, 72: 3 | 3 | False |
| e | 0.718282 | 24: 3, 48: 3, 72: 3 | 3 | False |
| phi | 0.618034 | 24: 4, 48: 3, 72: 3 | 3 | False |
| Y | 0.264675 | 24: 2, 48: 2, 72: 2 | 2 | False |
| Q | 0.389675 | 24: 3, 48: 3, 72: 3 | 3 | False |
| MONAD | 0.817580 | 24: 3, 48: 3, 72: 3 | 3 | False |

**And the magnitude-matched control removes it entirely.**  At depth 72, 1066 of 1066 members of the stride null reach `d_min <= 0` — that is all of them — so the tail is `1` and the score is 0.00 bits.  A slope below `1/72` emits no one at all in 72 bits, so the word is all zeros, which is a codeword; that is arithmetic about the magnitude of alpha and carries nothing about the code.
<!-- end generated -->

Two corrections, then, rather than one. The first is the plan's: `d_min <= 3`
is the majority case and worth under a bit. The second is sharper and applies
to alpha in particular: at these depths alpha's word is all zeros because its
slope is smaller than one over the depth, so its distance to the code is a fact
about the *magnitude* of alpha and nothing else — and the magnitude-matched
null reproduces it for every single member, which is a tail of one and a score
of zero. The electron anomaly `(g-2)/2` does the same thing for the same
reason. A statistic that a magnitude-matched control reproduces exactly is not
a measurement of structure.

---

## 9. Exactness, and how to re-take every number

No float is constructed anywhere in the module, in the cache or in the tables.
Slopes, frequencies and tail probabilities are exact `Fraction` values;
logarithms are exact rational brackets with a proved error bound, from
`glm_universal.reasoning.transcendental`; rendering is by integer arithmetic.
Directive D7, and `tests/test_exactness.py` is its instrument.

```bash
cd overlay
PYTHONPATH=. python3 GLM.py -q "report landscape" -c 1
PYTHONPATH=. python3 -m glm_universal.tools landscape --write
PYTHONPATH=. python3 -m glm_universal.corpus --write
```

Every table below is a generated block emitted from a measurement cache that is
guarded by a digest of the module that produced it: when the module changes the
cache reports itself stale, the blocks say so, and
`glm_universal.corpus.checks.corpus_checks` fails. No number in this document
is typed by hand.

---

## 10. Bridges not yet tested

Four routes from a wider framework to alpha have been proposed around this
project. **None of them is implemented, and none of them is tested here.** Each
is listed with what a falsifiable test would have to look like and what it
would cost, so that the next round can either build one properly or drop it.

1. **Three-Distance / Ostrowski.** *Already used, and it is the one route that
   is fixed in advance:* the gap spectrum is determined by the continued
   fraction, so the map from a number to its signature is a function with no
   free parameters. A test is exactly what §2 does. Cost: implemented here.
2. **Gates's doubly-even code / Adinkra correspondence.** The claim would be
   that the error-correcting code attached to an Adinkra with a stated number
   of colours is forced to be a particular doubly-even code, and that a stated
   invariant of that code — a fixed function, written down before looking —
   evaluates to something near `1/alpha`. A falsifiable test fixes the
   invariant and the code family first, enumerates the family exhaustively, and
   reports where alpha's value falls in the resulting distribution. Cost: the
   Adinkra codes for `n <= 8` colours are enumerable, so a few days of work;
   the hard part is not the enumeration but committing to the invariant before
   seeing it. **Unimplemented.**
3. **2-adic string amplitudes.** The claim would be that a `p`-adic Veneziano
   amplitude at `p = 2`, evaluated at a stated argument fixed in advance,
   reproduces a dimensionless constant. A falsifiable test states the argument
   and the normalisation before evaluating, and reports the result against the
   distribution over the other primes `p` as the null. Cost: small — the
   amplitudes are closed-form — but worthless unless the argument is fixed
   first, and this project has no principled way to fix it. **Unimplemented.**
4. **Modular forms at CM points.** The claim would be that `j` or an
   Eisenstein series at a stated CM point produces `1/alpha` under a stated
   normalisation. The null is the other CM points of small discriminant, which
   is a finite enumerable set, and the test is alpha's rank within it. Cost:
   modest, and it needs exact arithmetic for the CM values, which this project
   has. The obstruction is again the normalisation, which must be fixed before
   the enumeration. **Unimplemented.**

The common shape: each becomes a test the moment the map from the framework to
the number is fixed in advance and stated falsifiably, and none of them is one
before that.
