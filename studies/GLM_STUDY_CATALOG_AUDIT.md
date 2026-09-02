# The external study findings, tested

**What this document is.** `glm_study_findings_catalog.md` is a record of
measurements: the empirical findings of a series of GLM studies run outside
this package — iteration drift over the odd primes and the code-to-lattice
ladder, the generators and containers of irrational numbers, the 53-bit
mantissa question, the physical-mechanical engine family, substrate-native bit
dynamics and reversible computing, and a landscape study of domain
applications. A record of measurements is exactly the kind of document that
drifts away from the system it describes without anybody noticing.

This study turns it into a **live claim ledger**, in the same form as
[`GLM_UNIFICATION_BLUEPRINT_AUDIT.md`](GLM_UNIFICATION_BLUEPRINT_AUDIT.md):
every testable sentence of the catalogue is restated as a claim, recomputed
against the package as it stands, and given a verdict.

Nothing below is quoted from the catalogue. Every figure is produced by the
call that settles it, on demand, by `glm_universal.reasoning.catalog`. Ask the
running system for it:

```
python GLM.py -q "report catalog" --verify-tct
python GLM.py -q "report signature" --verify-tct
python GLM.py -q "report drift" --verify-tct
```

The ledger's own numbers are re-derived in a fresh interpreter by column 3 of
the Three Column Thinking payload, so this audit is falsifiable in the same way
as everything else the system says.

**No float is constructed anywhere in it.** The drift table's binary64 regime
is the package's own IEEE-754 model (`reasoning/mantissa`), the entropies are
exact rational brackets around a proved error bound, and the resonance curve's
square root is an exact rational within `2**-64`.

---

## The four verdicts

| verdict | meaning |
|---|---|
| **confirmed** | the package reproduces the catalogue's figure exactly |
| **refuted** | the package reproduces a *different* figure; the ledger records what is true instead |
| **not reproduced** | the claim is well posed, but the measurement it names does not show what it says |
| **not implemented** | the claim describes a subsystem the package does not have, so it cannot be tested at all |

## The result

**58 testable claims. 33 confirmed, 14 refuted, 7 not reproduced, 4 not
implemented.**

*(Updated after the harmony round: §6.2 named three domains under one verdict,
and is now carried as two claims — see the section on it below.)*

The headline is that the catalogue is *substantially* right about what the
substrate does and *systematically* over-reads what its own measurements show.
Where it reports a number produced by running a loop, the number is almost
always reproduced to the digit. Where it reports that a measured column *is* a
property of the thing measured, the column usually turns out to be a closed
form of the input — true, but not evidence.

Three findings in the catalogue are worth stating plainly, because they are new
here rather than inherited:

1. **The spectral signature is not a measurement.** Every column of the
   catalogue's §2.3 table — entropy, maximum run length, transition rate, mean
   run length — is a closed form of the target constant, proved of the exact
   modulator in `RequestProject/GLM/Sturmian.lean`. Running the loop for ten
   thousand ticks and tabulating the result does not test anything the target
   did not already determine.
2. **Construction A does not climb the whole ladder.** The rungs into `D_4` and
   `E_8` are right; the rung into Barnes-Wall is not, and cannot be, because at
   minimum distance 8 the `±2` vectors are already the shortest and the code is
   invisible to the construction.
3. **The entropy dip at resonance is local, not global.** Zero entropy does
   identify lock-in, but a far-detuned circuit is nearly as quiet as a locked
   one, so entropy alone separates resonance from mistuning only inside the
   band.

---

## Section 1.3 — iteration drift over the odd primes

The same recurrence `X_(n+1) = r X_n - 1/p`, iterated 200 times from
`X_0 = 1/p`, in three regimes: exact rational arithmetic, binary64, and
binary64 truncated to six or four significant decimal digits.
`glm_universal.reasoning.drift` recomputes all of it.

| § | claim | verdict | figure |
|---|---|---|---|
| 1.3 | the contractive rule holds every regime inside its own ceiling for all 200 steps | **confirmed** | every contractive row ends below 1e-12 lossless, 1e-5 at six digits, 1e-3 at four |
| 1.3 | at p = 3 the accumulative lossless drift is 7.5e10 | **confirmed** | 7.49e+10 |
| 1.3 | at p = 3 the display drifts are 6.0e19 and 2.2e22 | **confirmed** | 6.05e+19 and 2.22e+22 |
| 1.3 | at p = 5 the accumulative drifts are 4.2e1, 1.6e10, 2.1e12 | **confirmed** | 4.19e+1, 1.65e+10, 2.05e+12 |
| 1.3 | at p = 23 the accumulative drifts are 2.9e-11, 7.9e-2, 1.5e0 | **confirmed** | 2.94e-11, 7.92e-2, 1.53e+0 |
| 1.3 | at p = 23 the contractive lossless drift is exactly 0 | **refuted** | 2.66e-17 — small, but not zero |
| 1.3 | `X_200 = 7.5e10` at p = 3 | **refuted** | `X_200 = -6.48e+24`; 7.5e10 is that row's *drift* |
| 1.3 | the display regimes first exceed 1e-9 at step 1 or 2, for every prime | **refuted** | true for six of seven primes; at p = 5 the onsets are step 6 and step 4 |
| 1.3 | the lossless regime first diverges at step 46 at p = 3 and never within 200 for p ≥ 17 | **confirmed** | onset 46; none within 200 at p = 17 or 23 |

Two of the three refutations are labelling rather than arithmetic. `1/23` is not
dyadic, so the stored double is never the exact value and the drift cannot be
exactly zero; and the catalogue's `X_200` column carries the same number as its
own drift column, which the exact orbit (`-6.48e+24`) settles. The third is
real: `1/5` is close enough to a short decimal that truncation is harmless for
several steps, so the "diverges immediately" reading has an exception.

## Section 1.4 — the code-to-lattice ladder

| § | claim | verdict | figure |
|---|---|---|---|
| 1.4 | parity [4,3,2] → `D_4`, kissing 24 | **confirmed** | kissing 24 at squared norm 2 |
| 1.4 | extended Hamming [8,4,4] → `E_8`, kissing 240 | **confirmed** | 240 = 14·16 + 2·8 |
| 1.4 | Reed-Muller RM(1,4) → Barnes-Wall, kissing 4,320 | **refuted** | Construction A on that code gives kissing 32 at squared norm 4 |
| 1.4 | extended binary Golay → Leech, kissing 196,560 | **confirmed** | Construction A alone gives 48; the A→B→C ladder gives 196,560 |
| 1.4 | ternary Golay → `K_12`, extremal [48,24,12] → `P_48n` | **not implemented** | no Construction A over `F_3`, no length-48 extremal code |

The Barnes-Wall rung is the interesting one. Construction A takes the union of
the cosets `c + 2Z^n` for `c` in the code; the shortest vectors it can ever
produce are the `±2` coordinate vectors, of squared norm 4, unless the code has
words of weight below 4. RM(1,4) has minimum distance 8, so the construction
never sees the code at all and returns the trivial `2Z^16` kissing number 32.
Barnes-Wall `BW_16` needs Construction D, which stacks a whole chain of
Reed-Muller codes rather than one.

## Section 2.2 — the cost of generating an irrational

| § | claim | verdict | figure |
|---|---|---|---|
| 2.2 | Heron: 5 steps to 50 bits for √2, √3; 6 for √5–√13; 7 for √15–√23 | **not reproduced** | the whole column reproduces except √13, which needs 7 |
| 2.2 | Heron: 8 steps to 100 bits for √2 | **refuted** | 6, because the correct bits double at every step |
| 2.2 | Machin: 50 bits in 9 terms | **refuted** | 11 terms, which is 50/log₂(25) rounded up on the exact tail bound |
| 2.2 | the 1/25 ratio per Machin term is 2.32 bits per step | **refuted** | log₂(25) = 4.64 bits per term; 2.32 is log₂(5) |
| 2.2 | the exponential series: 50 bits in 17 terms, tail bounded by 2/(k+1)! | **confirmed** | 17, solved in exact integers |
| 2.2 | Liouville's constant: 50 bits in 3 terms | **confirmed** | 3; the fourth already carries 80 bits |

The 50-bit Heron column is reproduced exactly from the start point `x_0 = N`,
with one exception at √13, whose seventh step puts it in the next band. The
placement of 13 is start-point dependent and the catalogue does not record the
start point, which is why this is *not reproduced* rather than refuted.

The 100-bit column cannot be right as a whole: it is uniformly three steps
above the 50-bit one, and quadratic convergence does not allow that. One step
past 50 correct bits already carries 100.

## Section 2.3 — the spectral signature

This is where the catalogue's reading and the package's disagree most sharply,
and the disagreement is settled by proof rather than by measurement.
`RequestProject/GLM/Sturmian.lean` proves that the first-order modulator
chasing a constant `t` emits

```
bit n  =  floor((n+1) t)  −  floor(n t)
```

— the mechanical word of slope `t`, an irrational rotation read through the
unit interval. Every column of the study's table follows:

| measured column | what it actually is | theorem |
|---|---|---|
| ones in `N` ticks | exactly `floor(N t)`, no error term | `dsOnes_eq_floor` |
| longest run of zeros | `< 1/t` | `ds_zero_run_length_lt` |
| longest run of ones | `< 1/(1 − t)` | `ds_one_run_length_lt` |
| transitions in `N` ticks | `2·floor(N t) + bit N` for `t < 1/2` | `dsTransitions_eq` |
| mean run length | `→ 1/(2 min(t, 1 − t))` | `dsMeanRunLength_tendsto` |
| Shannon entropy | the binary entropy of the density | `wobbleEntropy` |
| entropy zero | the stream is constant | `ds_wobbleEntropy_zero_iff_silent` |

| § | claim | verdict | figure |
|---|---|---|---|
| 2.3 | the tabulated wobble entropies | **confirmed** | 8 of 8 to three decimals — but each is the binary entropy of the target, so the column is a function of the constant |
| 2.3 | the Chaitin-Ω surrogate has entropy 0.980 | **refuted** | the modulator on 0.567143 gives 0.987; the surrogate is an LCG stream, not this loop |
| 2.3 | the tabulated maximum run lengths | **confirmed** | 8 of 8, and each equals the proved bound `ceil(1/min(t, 1−t)) − 1` |
| 2.3 | the tabulated mean run lengths | **not reproduced** | seven of nine to two decimals; α gives 68.97 against 68.49 (limit 68.52) and e^π−π gives 526.32 against 500.00 (limit 555.54) |
| 2.3 | the lag-1 autocorrelation column | **not reproduced** | seven rows are the ±1 mean product, two are the centred Pearson coefficient; no single definition gives the column |
| 2.3 | the algebraic irrationals produce Sturmian words | **confirmed** | true, and true of *every* target, algebraic or not |

The two mean-run-length exceptions are small-sample effects and the module says
so: at α's density, ten thousand ticks hold only nineteen runs.

The autocorrelation column is worth a note on method. Seven of the nine rows
are the mean of the products of consecutive bits on the ±1 alphabet; the two
extreme-density rows are the centred Pearson coefficient instead. Both are
computed for every row by `wobble.signature_table`, so the ledger can say which
is which rather than picking whichever makes the column come out right. The
windows are linear, not cyclic: wrapping the window invents an adjacency, and
for e^π−π — whose return time 1111 divides 9999 — the wrap turns a lag-1
correlation of −0.001 into +0.099.

## Section 2.4 — the 24-dimensional hull census

| § | claim | verdict | figure |
|---|---|---|---|
| 2.4 | the Leech minimal vectors have norm √32 | **confirmed** | 196,560 vectors of squared norm 32 |
| 2.4 | projected into 24 dimensions, √2 has norm 7.16, π 15.92, e 13.77, Liouville 0.56 | **not reproduced** | under the stated construction the norm is `t·√24`: 6.93, 15.39, 13.32, 0.54 |

The catalogue's four figures are a uniform 1.034 times the computed ones, which
no stated scaling explains. The containment verdict is unaffected either way:
of the four, only Liouville's constant lies inside a ball of radius √32.

## Section 3.2 — the 53-bit mantissa question

| § | claim | verdict | figure |
|---|---|---|---|
| 3.2 | the binary period of 1/p is `ord_2(p)`, table 2, 4, 3, 10, 12, 8, 11 | **confirmed** | `{3: 2, 5: 4, 7: 3, 11: 10, 13: 12, 17: 8, 23: 11}` |
| 3.2 | 10 full mantissa bits are lost on the first operation, for every odd prime | **not reproduced** | the stored double keeps at least 53 bits of relative precision, and its significand differs from the exact expansion in at most 3 of 53 bits |
| 3.2 | the loss is structural: a double is dyadic | **confirmed** | every double collapses to 0 within its bit count while the exact orbit repeats for ever |
| 3.2 | the drift is substrate-faithful at p = 3 (Hamming 0) and inverted at p = 5 (Hamming 24) | **refuted** | both values occur, but they belong to the *phase* rather than to the prime — and the two primes are the other way round |

The structural claim is the one that matters and it is confirmed, with a Lean
counterpart in `RequestProject/GLM/Mantissa.lean`: a double is a dyadic
rational, so its orbit under the doubling map reaches zero and stays there,
while the exact orbit of `1/p` is periodic with period `ord_2(p)` and never
terminates. That is the loss located at its source, one step earlier than the
drift table measures it.

## Section 4 — the physical-mechanical engine family

Every stage of the engine series is present in `glm_universal.reasoning.engine`
and every behavioural claim about it is confirmed: the four-stage baseline
route, the radiator that bleeds strain and prevents premature escalation, the
two generators run in parallel with a swap to the faster path, the turbocharger
that skips a snap under strain and the integer operations that buys, and the
runtime gearbox that classifies a target and shifts configuration.

| § | claim | verdict | figure |
|---|---|---|---|
| 4 | the four-stage baseline route | **confirmed** | one run on 1/3 over 64 ticks: error 1/192, drum period 2304, 8 relaxed snaps, 57 escalations |
| 4 | the radiator prevents premature escalation | **confirmed** | 4 bleeds leave strain 0 against 60 uncooled, 36 escalations against 57 |
| 4 | two generators in parallel, swap to the faster | **confirmed** | Heron clears 40 bits at tick 5, the convergents at 16, the switching strategy at 5 |
| 4 | the turbocharger conserves integer operations | **confirmed** | 6 snaps skipped, 150 integer operations saved under the stated cost model |
| 4 | the gearbox classifies and shifts at runtime | **confirmed** | rational → skip, algebraic → relaxed with radiator 8, transcendental → relaxed with radiator 4 |
| 4 | a 2.7× precision leap over naive solvers | **not reproduced** | against bitwise truncation the ratio is 7/64 (the engine loses); against half the tick budget it is between 1 and 7/6 |
| 4.4 | 100% TCT verification over 15 workloads | **not implemented** | the package verifies every report it answers, but has no fifteen-workload engine suite to score |

The 2.7× figure names no measurement: three natural baselines were tried and
none of them yields it. That is a claim about a comparison whose second term
was never written down.

## Section 5 — bit dynamics and reversible computing

| § | claim | verdict | figure |
|---|---|---|---|
| 5.1 | binary counting has an 11-bit transition cliff, Gray code has 1 | **confirmed** | over an 11-bit counter: 11 against 1 |
| 5.1 | Gray code halves the cumulative cost — exactly 2:1 | **refuted** | 2047/1024 = 1.9990 in bit flips; 2 only in the limit |
| 5.1 | Gray code has zero transition entropy | **confirmed** | the step-size distribution is the point mass at 1 |
| 5.2 | BRGC changes exactly one bit per step | **confirmed** | max step 1 over 256 steps |
| 5.2 | BRGC transition entropy is exactly zero | **confirmed** | step-size variance 0 |
| 5.2 | BRGC dissipates exactly half the cumulative symmetry TAX | **refuted** | TAX 8 against 749/16; less than half |
| 5.2 | Toffoli and Fredkin are self-inverse and bijective | **confirmed** | checked on all 8 inputs of each |
| 5.2 | 100 forward then 100 backward rounds return the carrier byte-identically | **confirmed** | 1,600 gate applications, Hamming distance 0 |
| 5.2 | the Golay syndrome weight is conserved through the cycle | **refuted** | it takes the values 4 and 7 during the run |
| 5.3 | the kink count is invariant under rotation | **confirmed** | all 24 rotations give 14 kinks |
| 5.3 | a single bit flip changes the kink count by exactly ±2 | **refuted** | over all 256 circular 8-bit words the deltas are `{−2: 512, 0: 1024, +2: 512}` |
| 5.4 | persistence diagrams classify 100 carriers with 100% accuracy | **not implemented** | the package computes no persistent homology |

The reversibility results are the strongest part of the catalogue: the gate
algebra, the exact round-trip and the rotational invariance of the kink count
all hold as stated. The two "exactly" claims do not — the 2:1 ratios are limits
approached from below, never attained at a finite width — and the ±2 soliton
claim is right only half the time: a flip *inside* a run of equal coordinates
leaves the kink count alone.

## Section 6.1 — the electrical oscillator

| § | claim | verdict | figure |
|---|---|---|---|
| 6.1 | at exact resonance the loop locks and the entropy collapses to 0.0000 | **confirmed** | at gain one the loop emits nothing but ones after the accumulator fills |
| 6.1 | SNR *is* wobble entropy: 0.000, 0.011, 0.081, 0.469, 1.000 | **confirmed** | 5 of 5 rows to three decimals; each is the binary entropy of the row's density and nothing else |
| 6.1 | the off-resonance ratios 0.9 and 1.1 give 0.985 and 0.996 | **refuted** | the 0.9 row is reproduced *exactly*, at quality factor q = 7.9 — but the 1.1 row then reads 1.000, and no q on a grid of 391 values from 1 to 40 gives both |
| 6.1 | the dip is a sharp V, so entropy identifies resonance | **not reproduced** | the sweep over ratios 0.5 … 1.5 reads 0.649, 0.710, 0.798, 0.920, 0.987, **0.000**, 1.000, 0.840, 0.672, 0.552, 0.465 |

The resonance model used here is the textbook normalised amplitude response

```
gain(r)  =  1 / sqrt( q² (1 − r²)² + r² )
```

which is exactly 1 at `r = 1` — the lock-in condition — and is computed as an
exact rational to `2**-64` with no float anywhere. Two things fall out.

*The two off-resonance figures are inconsistent with each other.* The response
is not symmetric about `r = 1`, and the asymmetry runs the wrong way: any `q`
that puts the 0.9 row at 0.985 puts the 1.1 row at 1.000, not 0.996. They were
not measured on the same circuit.

*The V is local.* The entropy is exactly zero at lock, rises steeply on both
sides, peaks where the gain crosses 1/2 — the half-power points — and then
**falls away again** as the circuit is detuned further, because a gain near
zero is a stream of almost nothing but zeros, which is as quiet as a stream of
almost nothing but ones. Zero entropy is a reliable signature of lock-in; *low*
entropy is not a reliable signature of anything, unless the circuit is already
known to be inside its band.

## Section 6.2 — the unified synthesis of homeostasis

| § | claim | verdict | figure |
|---|---|---|---|
| 6.2 | musical harmony maps to Leech proximity | **not reproduced** | the 28 intervals of the harmonic register separate at scale 8 and distance from the unison orders them at Kendall tau `53/63`, but the same distance taken *before* the decoder runs scores `53/63` too and the decoder reorders no pair |
| 6.2 | market price discovery maps to Leech proximity | **not implemented** | chemistry is a register and its equilibria are not; there is no economic register at all |

When this audit was first written, all three domains were untestable here and
the sentence was recorded as one open gap, with a harmonic register named as
the cheapest of the three to attempt. That register was then built —
`data_objects/harmonics.py`, `reasoning/harmony.py`,
`RequestProject/GLM/Harmony.lean`, `report harmony` — so two thirds of the
sentence now have a verdict and one still does not, and the ledger carries it
as two claims rather than one.

The musical half is **not reproduced**, and the reason is the control rather
than the measurement: proximity in the lattice does order the intervals by
consonance, at an exact Kendall tau of `53/63` — but the same distance measured
on the undecoded tuning vectors scores exactly the same, and from scale 8
upwards the decoder reorders no pair at all. What the study measures is the
prime-exponent vector; the lattice is a change of coordinates on top of it.
The full write-up is [`HARMONY_STUDY.md`](HARMONY_STUDY.md).

The economic half remains the largest open gap in the catalogue, and it is
recorded as one. The semantics layer refuses a term it has no coordinate for
rather than inventing one, which is the behaviour that makes the rest of the
ledger worth reading — but it means that third of the universality claim cannot
be tested here at all. A price, unlike an interval, is a measurement rather
than an arithmetic object, which is what makes it the expensive one.

---

## What was added to the system by this audit

* `RequestProject/GLM/Sturmian.lean` — the modulator as an irrational rotation:
  the mechanical-word identity, the exact ones count, the run-length bounds,
  the transition rate, the mean-run-length limit, and the wobble entropy with
  its collapse-at-lock characterisation. No `sorry`.
* `glm_universal/reasoning/wobble.py` — the spectral signature laboratory, with
  the law beside every measured column, plus the oscillator table, the exact
  resonance sweep and the quality-factor scan.
* `glm_universal/reasoning/drift.py` — the three-regime prime-iteration stress
  test, in exact arithmetic over the package's own IEEE-754 model.
* `glm_universal/reasoning/catalog.py` — the ledger itself.
* Three report subjects — `report signature`, `report drift`, `report catalog`
  — each with a Three Column Thinking template that re-derives its figures in a
  fresh interpreter.
