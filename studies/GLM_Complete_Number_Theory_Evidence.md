# The GLM Number-Theoretic Substrate

**Author:** Euan R. A. Craig (DigitalEuan), Auckland, New Zealand
**Date:** 3 September 2026
**Checked against this repository:** every Lean statement quoted below was read
back out of `RequestProject/GLM/` rather than retyped, and every number was
recomputed by one of the two scripts named in §0.3.

---

## 0. The claim, stated

### 0.1 What is claimed

I'm not claiming that the lattice generates the universe. The claim is narrower
and testable: there is an exact substrate — the Golay code, the Leech lattice,
and the arithmetic on them, integer and `Fraction` exact throughout — and
reality maps onto it with unusual fidelity.

Some of what the substrate holds is hidden by the layer it is read at. Every
carrier here is a projection at a stated resolution — the 24-bit word, the
syndrome, the MOG cell, the Leech point, the shell — so a correspondence that is
invisible at one layer can be exact one layer up, and it is worth checking a
claim from several layer and resolution perspectives before calling it absent.
[`POSITIONING.md`](../POSITIONING.md) is the standing form of this note;
§14 below walks one number down all of those layers so that the loss at each
step can be seen rather than described.

### 0.2 What is *not* claimed

* Not that the constants of physics are derived here. Where a numerical
  coincidence is quoted, the price of the coincidence is measured too
  (`FitCapacity.lean`, and §10.3).
* Not that the optical section (§11) is exact. It is a floating-point
  simulation of a physical measurement, deliberately kept outside the exact
  package, and it is labelled as such wherever its numbers appear.
* Not that every layer is faithful. Several of the results below are negative:
  the code layer *destroys* the wobble of §14, and the layer that carries the
  information there is the syndrome, not the codeword.

### 0.3 How to reproduce every number in this document

```bash
# the exact tables of §1.3, §2.4 and §9.2
PYTHONPATH=overlay python3 studies/scripts/number_theory_tables.py

# the worked example of §14 -- one number through every layer
cd overlay && PYTHONPATH=. python3 -m glm_universal.examples.number_pipeline

# the optical null-model control of §11.7 (floating point, outside the package)
python3 studies/scripts/tmm_null_model.py

# the Lean development itself
lake build          # 97 files under RequestProject/GLM/, 0 sorry
```

The Lean development is 97 files under `RequestProject/GLM/`, all building
against Mathlib for Lean 4.28.0 with **no `sorry` and no `admit`**, and no
declared axiom anywhere: every proof depends only on `propext`,
`Classical.choice`, `Quot.sound`, and — for the theorems reached through
`native_decide` — `Lean.ofReduceBool` and `Lean.trustCompiler`.

### 0.4 How this document is kept honest

Reproducing a number by hand once is not the same as the document staying true,
so the agreement is now a test:
`overlay/glm_universal/tests/test_number_theory_evidence.py` reads this file and

* re-runs `studies/scripts/number_theory_tables.py` and compares the tables of
  §1.3, §2.4 and §9.2 **cell by cell** with the ones printed above;
* re-runs `glm_universal.examples.number_pipeline` and compares the §14
  transcript **line for line**, and separately checks each reading §14 draws
  out of it;
* requires every theorem named in Appendix A to exist, in the file the appendix
  puts it in;
* requires the Lean file count quoted here to be the tree's;
* requires the modules this document computes from — the coherence constants,
  the wobble, the Golay code and its decoder, the pipeline example — and the
  generator script itself to contain no float site at all, which is directive
  D7 checked by parsing rather than by assertion.

That test found two things when it was first run, and both are repaired above:
the file count had aged from 89 to 95, and the generator's prime sieve bounded
itself with `limit ** 0.5`, which is a float in a script whose whole point is
that it does not construct one. It is `math.isqrt` now.

---

---

## 1. The constants (Lean: `Constants.lean`)

### 1.1 The mathematical foundation

```lean
theorem Y_pos : 0 < Y
theorem Y_lt_half : Y < 1 / 2
theorem Y_gt_quarter : 1 / 4 < Y
theorem Q_pos : 0 < Q
theorem Q_lt_one : Q < 1
```

where:

| Constant | Formula | Value | Meaning |
|---|---|---|---|
| Y | 1/(π + 2/π) | 0.264675… | Observer/read quantum |
| Q | Y + 1/8 | 0.389675… | Activation quantum |
| B | 10 | 10 | Coherence budget |
| TAX(v) | HW(v)·Y + ‖v‖²/8 | varies | Symmetry tax |
| NRCI(v) | B/(B + TAX(v)) | (0, 1] | Non-Random Coherence Index |

`Calibration.lean` sharpens the value: `Y_bounds` proves
`0.264675 < Y < 0.264676`, and `tax_indicator` proves that on a carrier whose
coordinates are all `0` or `1` the tax is exactly `HW(v)·Q` — so the binary
layer needs only one constant, not two.

### 1.2 The central theorem

```lean
theorem nrci_eq_one_iff {v : Fin n → ℤ} : nrci v = 1 ↔ v = 0
```

NRCI equals 1 **if and only if** v = 0. Perfect coherence is exactly the
vacuum. This is not a convention; it is a theorem. The zero vector is the
unique state where TAX = 0, and therefore the unique state where NRCI = 1.

Supporting theorems:

```lean
theorem tax_nonneg (v : Fin n → ℤ) : 0 ≤ tax v
theorem tax_eq_zero_iff {v : Fin n → ℤ} : tax v = 0 ↔ v = 0
theorem nrci_pos (v : Fin n → ℤ) : 0 < nrci v
theorem nrci_le_one (v : Fin n → ℤ) : nrci v ≤ 1
```

### 1.3 The coherence regimes

```lean
theorem regime_onBit_iff {v : Fin n → ℤ} : regime v = .onBit ↔ tax v ≤ 5 / 2
theorem regime_coherent_iff {v : Fin n → ℤ} :
    regime v = .coherent ↔ 5 / 2 < tax v ∧ tax v ≤ 10
theorem regime_transitional_iff {v : Fin n → ℤ} :
    regime v = .transitional ↔ 10 < tax v ∧ tax v ≤ 70 / 3
theorem regime_subcoherent_iff {v : Fin n → ℤ} :
    regime v = .subcoherent ↔ 70 / 3 < tax v
```

**Recomputed** (exact rational arithmetic; the decimals are *truncated*, not
rounded, at the place shown, which is what `coherence.decimal_str` does):

| Hamming weight | TAX | NRCI | Regime |
|---|---|---|---|
| 0 (vacuum) | 0.000000 | **1.000000** | OnBit |
| 1 | 0.389675 | 0.962493 | OnBit |
| 2 | 0.779350 | 0.927699 | OnBit |
| 8 (octad) | 3.117403 | 0.762345 | Coherent |
| 12 | 4.676105 | 0.681379 | Coherent |
| 16 | 6.234806 | 0.615960 | Coherent |
| 24 (full) | 9.352210 | 0.516736 | Coherent |

All NRCI > 0 (`nrci_pos`), all NRCI ≤ 1 (`nrci_le_one`), NRCI = 1 only at zero
(`nrci_eq_one_iff`).

---

## 2. The Sturmian bridge (Lean: `Sturmian.lean`)

### 2.1 The key theorem: the wobble stream **is** a Sturmian word

```lean
theorem dsState_eq_fract {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1) (n : ℕ) :
    dsState t n = Int.fract ((n : ℝ) * t)
```

After n ticks the accumulator state is exactly `Int.fract(n·t)`. The modulator
loop is an **irrational rotation** on the unit circle, and the emitted bit
stream is a **Sturmian word** of slope t.

### 2.2 The bit stream as a Sturmian word

```lean
theorem dsBit_eq_floor_diff {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1) (n : ℕ) :
    (dsBit t n : ℤ) = ⌊((n : ℝ) + 1) * t⌋ - ⌊(n : ℝ) * t⌋
```

The bit at step n is the difference of floors — the standard definition of a
Sturmian word.

### 2.3 The closed forms

```lean
theorem dsOnes_eq_floor {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1) (N : ℕ) :
    (dsOnes t N : ℤ) = ⌊(N : ℝ) * t⌋
```

The number of 1s in N ticks is **exactly** `⌊N·t⌋`. Not approximately —
exactly.

```lean
theorem ds_zero_run_length_lt {t : ℝ} (ht0 : 0 < t) (ht1 : t < 1)
    {n L : ℕ} (h : ∀ i, n ≤ i → i < n + L → dsBit t i = 0) : (L : ℝ) < 1 / t
theorem ds_one_run_length_lt {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1)
    {n L : ℕ} (h : ∀ i, n ≤ i → i < n + L → dsBit t i = 1) : (L : ℝ) < 1 / (1 - t)
```

A run of zeros of length L forces `L < 1/t`; a run of ones forces
`L < 1/(1−t)`. (The hypothesis matters and was missing from an earlier draft of
this document: the bound is about a *run*, not about the stream.)

```lean
theorem ds_wobbleEntropy_tendsto {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1) :
    Tendsto (fun N : ℕ => wobbleEntropy (dsAverage t N)) atTop (𝓝 (wobbleEntropy t))
theorem ds_wobbleEntropy_zero_iff_silent {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1) :
    wobbleEntropy t = 0 ↔ ∀ n, dsBit t n = 0
```

The wobble entropy converges to `H(t) = −t·log₂ t − (1−t)·log₂(1−t)`, and it is
zero exactly when the stream is silent.

### 2.4 Experimental verification: the odd primes below 100

For each prime p the target is t = 1/p, and the predicted number of 1s in
N = 500 ticks is ⌊500/p⌋. There are **24** odd primes below 100; p = 2 is
excluded because 1/2 is dyadic and belongs to §3, not here. (An earlier draft
said "25 primes" while listing 24 rows; the count below is the one the script
produces.)

| p | ⌊500/p⌋ (Lean prediction) | measured 1s | match | longest 0-run | longest the bound permits |
|---|---|---|---|---|---|
| 3 | 166 | 166 | ✓ | 2 | 2 |
| 5 | 100 | 100 | ✓ | 4 | 4 |
| 7 | 71 | 71 | ✓ | 6 | 6 |
| 11 | 45 | 45 | ✓ | 10 | 10 |
| 13 | 38 | 38 | ✓ | 12 | 12 |
| 17 | 29 | 29 | ✓ | 16 | 16 |
| 19 | 26 | 26 | ✓ | 18 | 18 |
| 23 | 21 | 21 | ✓ | 22 | 22 |
| 29 | 17 | 17 | ✓ | 28 | 28 |
| 31 | 16 | 16 | ✓ | 30 | 30 |
| 37 | 13 | 13 | ✓ | 36 | 36 |
| 41 | 12 | 12 | ✓ | 40 | 40 |
| 43 | 11 | 11 | ✓ | 42 | 42 |
| 47 | 10 | 10 | ✓ | 46 | 46 |
| 53 | 9 | 9 | ✓ | 52 | 52 |
| 59 | 8 | 8 | ✓ | 58 | 58 |
| 61 | 8 | 8 | ✓ | 60 | 60 |
| 67 | 7 | 7 | ✓ | 66 | 66 |
| 71 | 7 | 7 | ✓ | 70 | 70 |
| 73 | 6 | 6 | ✓ | 72 | 72 |
| 79 | 6 | 6 | ✓ | 78 | 78 |
| 83 | 6 | 6 | ✓ | 82 | 82 |
| 89 | 5 | 5 | ✓ | 88 | 88 |
| 97 | 5 | 5 | ✓ | 96 | 96 |

**24/24 exact matches**, and in every case the longest zero run is exactly the
largest value the proved bound permits — the bound is attained, not merely
respected. The Sturmian theorem is not a prediction; it is an exact
description, and the table is a check that the implementation obeys it.

---

## 3. The mantissa wall (Lean: `Mantissa.lean`)

### 3.1 The doubling map

```lean
theorem dyadicOrbit_collapses (k m : ℕ) (hm : m < 2 ^ k) : dyadicOrbit k k m = 0
theorem dyadicOrbit_eq_zero_of_le (k m n : ℕ) (hm : m < 2 ^ k) (hn : k ≤ n) :
    dyadicOrbit k n m = 0
```

A dyadic rational m/2^k reaches 0 in exactly k steps and stays there. A float
*is* a dyadic rational, so a float's orbit always dies.

```lean
theorem oddOrbit_ne_zero {p : ℕ} (hp : 1 < p) (hodd : p % 2 = 1) (n : ℕ) :
    oddOrbit p n ≠ 0
theorem oddOrbit_periodic {p d : ℕ} (hd : 2 ^ d % p = 1) (n : ℕ) :
    oddOrbit p (n + d) = oddOrbit p n
theorem exists_period {p : ℕ} (hp : 1 < p) (hodd : p % 2 = 1) :
    ∃ d, 0 < d ∧ ∀ n, oddOrbit p (n + d) = oddOrbit p n
```

The orbit of 1/p for odd p > 1 never reaches 0 and is periodic, with period d
whenever 2^d ≡ 1 (mod p).

```lean
theorem dyadic_ne_odd_orbit {p k m : ℕ} (hp : 1 < p) (hodd : p % 2 = 1)
    (hm : m < 2 ^ k) : ∃ n, dyadicOrbit k n m ≠ oddOrbit p n
```

The two behaviours cannot be reconciled: dyadic orbits die, odd orbits cycle
forever.

### 3.2 Verification

**Dyadic rationals** (collapse to 0):

| Target | k | steps to 0 (measured) | predicted |
|---|---|---|---|
| 1/2 | 1 | 1 | 1 ✓ |
| 1/4 | 2 | 2 | 2 ✓ |
| 3/4 | 2 | 2 | 2 ✓ |
| 1/8 | 3 | 3 | 3 ✓ |
| 1/16 | 4 | 4 | 4 ✓ |
| 1/1024 | 10 | 10 | 10 ✓ |

**Odd prime reciprocals** (periodic, never reach 0):

| Target | period | reaches 0? | orbit sample |
|---|---|---|---|
| 1/3 | 2 | no | 1, 2, 1, 2, … |
| 1/5 | 4 | no | 1, 2, 4, 3, … |
| 1/7 | 3 | no | 1, 2, 4, 1, 2, 4, … |
| 1/11 | 10 | no | 1, 2, 4, 8, 5, 10, 9, 7, 3, 6, … |
| 1/13 | 12 | no | 1, 2, 4, 8, 3, 6, 12, 11, 9, 5, … |
| 1/17 | 8 | no | 1, 2, 4, 8, 16, 15, 13, 9, … |
| 1/31 | 5 | no | 1, 2, 4, 8, 16, … |

### 3.3 The structural reading

IEEE-754 drift is not an implementation bug; it is a **mathematical
necessity**. The doubling map — which is what the mantissa does when it
multiplies by two — has two qualitatively different behaviours, and which one a
target gets is decided by its denominator. Storing the exact rational and
computing in ℤ/bℤ avoids the doubling map entirely, which is what directive D7
buys.

---

## 4. The irrational tower (Lean: `Irrational.lean`, `Tower.lean`)

### 4.1 The cardinality wall

```lean
theorem no_countable_layer_lossless (L : Layer ℝ) [Countable L.View] : ¬ L.Lossless
theorem sqrt_two_not_carrier (q : ℚ) : (q : ℝ) ≠ Real.sqrt 2
```

No countable layer is lossless. The reals are uncountable; any countable
representation conflates two distinct reals.

### 4.2 The dyadic tower

```lean
theorem dyadic_not_lossless (n : ℕ) : ¬ (dyadicLayer n).Lossless
theorem dyadic_separates {q r : ℚ} (h : q ≠ r) : ∃ n : ℕ, ¬ (dyadicLayer n).Indist q r
theorem dyadic_boundary_nonempty (n : ℕ) :
    (Boundary (dyadicLayer (n + 1)) (dyadicLayer n)).Nonempty
theorem towerView_injective : Function.Injective towerView
```

The tower is never lossless at any finite level, every level strictly separates
something the one below it conflates, and the tower *as a whole* is injective.
Faithful in the limit, lossy at every stage — which is the same shape as the
positioning note in §0.1.

### 4.3 Delta–sigma convergence

```lean
theorem dsAverage_error_le {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1) {N : ℕ} (hN : 0 < N) :
    |dsAverage t N - t| ≤ 1 / N
theorem dsAverage_tendsto {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1) :
    Tendsto (fun N => dsAverage t N) atTop (𝓝 t)
```

The running average converges to the target at rate O(1/N), for every real in
[0,1). This is how the GLM holds an irrational: as the limit of a process, with
a stated error at every finite stage.

---

## 5. The harmony connection (Lean: `Harmony.lean`)

### 5.1 The circle of fifths never closes

```lean
theorem three_pow_ne_two_pow (n m : ℕ) (hn : 0 < n) : (3 : ℕ) ^ n ≠ 2 ^ m
theorem fifth_never_closes (n : ℕ) (hn : 0 < n) (m : ℤ) :
    ((3 : ℚ) / 2) ^ n ≠ (2 : ℚ) ^ m
```

A power of 3 is always odd, so it is never a power of 2, and therefore
(3/2)^n is never 2^m.

### 5.2 The Pythagorean comma

```lean
theorem fifth_tet_error : ((3 : ℚ) / 2) ^ 12 / (2 : ℚ) ^ 7 = 531441 / 524288
```

Exactly 531441/524288 ≈ 1.013643 — the gap that remains after twelve fifths.
`major_third_tet_error` is the same computation for the just major third.

### 5.3 The general obstruction

```lean
theorem odd_prime_ratio_ne_two_zpow {a b N p : ℕ} (hb : 0 < b)
    (hab : Nat.Coprime a b) (hN : 0 < N) (hp : p.Prime) (hp2 : p ≠ 2)
    (hdvd : p ∣ a ∨ p ∣ b) (k : ℤ) : ((a : ℚ) / b) ^ N ≠ (2 : ℚ) ^ k
```

A ratio a/b in lowest terms in which *either side* carries an odd prime is not
a step of any equal division of the octave — for every N at once. (An earlier
draft required the odd prime to divide the denominator; the theorem is the
stronger one, and either side suffices.)

### 5.4 Connection to the binary periods

The same obstruction runs through §3: 1/3 has binary period 2, 1/5 has 4, 1/7
has 3, and none of these expansions terminates, because termination would make
the denominator a power of two. The circle of fifths does not close for exactly
the reason that 1/3 has no finite binary expansion.

---

## 6. The Golay substrate census (Lean: `Golay/Census.lean`, `Golay/Cesaro.lean`)

### 6.1 The coset census

```lean
theorem coset_census :
    #(univ.filter fun f : Syn => cosetWt f = 0) = 1 ∧
    #(univ.filter fun f : Syn => cosetWt f = 1) = 24 ∧
    #(univ.filter fun f : Syn => cosetWt f = 2) = 276 ∧
    #(univ.filter fun f : Syn => cosetWt f = 3) = 2024 ∧
    #(univ.filter fun f : Syn => cosetWt f = 4) = 1771
```

| Weight | Count | Reading |
|---|---|---|
| 0 | 1 | the code itself |
| 1 | 24 | unique correction |
| 2 | 276 | unique correction |
| 3 | 2,024 | unique correction (packing radius) |
| 4 | 1,771 | **six-fold tie** (covering radius) |
| **total** | **4,096** | |

`unique_vs_ambiguous` states the split the same way: 2,325 cosets of weight ≤ 3
against 1,771 at weight 4.

### 6.2 The mean coset weight

```lean
theorem mean_coset_weight : meanCosetWt = 3433 / 1024
theorem mean_coset_weight_gt_three : 3 < meanCosetWt
theorem mean_coset_weight_lt_four : meanCosetWt < 4
```

3433/1024 ≈ 3.3525, strictly between the packing radius 3 and the covering
radius 4. **The average word is already past the radius inside which reading is
unique: ambiguity is the typical case, not a corner case.**

### 6.3 Cesàro convergence

```lean
theorem cesaro_converges {μ : Law} (hp : IsProb μ) (f : Syn) {N : ℕ} (hN : 0 < N) :
    |cesaro μ N f - 1 / 4096| ≤ 24 / N
```

The time average of the perturbation chain converges to the uniform law at rate
24/N, the 24 being the dimension of the carrier. The proof diagonalises the
chain by the characters of `Syn = (ZMod 2)¹²`, in exact rational arithmetic.

### 6.4 The snap boundary

```lean
theorem snap_boundary_at_three {C : Set (Fin n → Bool)}
    (hmin : ∀ c ∈ C, ∀ c' ∈ C, c ≠ c' → 8 ≤ hdist c c')
    {c c' : Fin n → Bool} (h : hdist c c' = 8) :
    (∀ v, ∀ d ∈ C, ∀ d' ∈ C, hdist v d ≤ 3 → hdist v d' ≤ 3 → d = d') ∧
      ∃ v, c ≠ c' ∧ hdist v c = 4 ∧ hdist v c' = 4
theorem snap_ambiguous_at_four {c c' : Fin n → Bool} (h : hdist c c' = 8) :
    ∃ v, hdist v c = 4 ∧ hdist v c' = 4
```

Both halves in one statement: inside radius 3 the nearest codeword is unique,
and at radius 4 there is a word equidistant from two codewords. `ties_card_eq_six`
of `Golay/Sextet.lean` counts the tie exactly — six codewords, never five and
never seven.

---

## 7. The reversible channel (Lean: `Reversible.lean`)

### 7.1 Gray-code flip counts

```lean
theorem gray_single_bit (n : ℕ) :
    ∃ i, ∀ j, ((gray n).testBit j ≠ (gray (n + 1)).testBit j) ↔ j = i
theorem binaryCycleFlips_eq (w : ℕ) : binaryCycleFlips w = 2 ^ (w + 1) - 2
theorem gray_two_mul_eq (w : ℕ) : 2 * grayCycleFlips w = binaryCycleFlips w + 2
```

Consecutive Gray codes differ in exactly one bit position — and the statement
is the sharp one: there is a position i such that j differs *iff* j = i. Over a
full w-bit cycle binary counting flips 2^(w+1)−2 bits and Gray counting flips
2^w; the sharp relation is **2·Gray = Binary + 2**.

At width 24: binary 33,554,430, Gray 16,777,216, and 2 × 16,777,216 =
33,554,432 = 33,554,430 + 2 ✓.

### 7.2 Reversible gates

```lean
theorem toffoli_involutive : Function.Involutive toffoli
theorem fredkin_involutive : Function.Involutive fredkin
theorem toffoli_bijective : Function.Bijective toffoli
theorem fredkin_bijective : Function.Bijective fredkin
```

Both gates are their own inverses and are bijections: nothing is erased.

### 7.3 Kink conservation

```lean
theorem kinks_even (v : Fin n → Bool) : Even (kinks v)
theorem kinks_flip_drops_two :
    kinks (flipAt (fun i : Fin 4 => decide (i.val = 1)) 1) + 2
      = kinks (fun i : Fin 4 => decide (i.val = 1))
```

The kink count — the number of coordinate boundaries — is always even. The
second theorem is a **witness**, not a general law: it exhibits one flip that
drops the count by exactly two. (An earlier draft stated it as a general law
about every flip; that is not what is proved, and the general statement is
false at the ends of the vector.)

---

## 8. Tax conservation and its boundary (Lean: `TaxConservation.lean`)

### 8.1 The conservation law

```lean
theorem tax_conservation (a b : Fin n → Bool) :
    tax (ofBits (bxor a b))
      = tax (ofBits a) + tax (ofBits b) - 2 * tax (ofBits (band a b))
```

For binary carriers TAX is exactly conserved under XOR.

### 8.2 The boundary

```lean
theorem tax_conservation_fails_at_integer_layer :
    tax (ofNats (nxor w1 w2))
      ≠ tax (ofNats w1) + tax (ofNats w2) - 2 * tax (ofNats (nand w1 w2))
```

The law holds **exactly** at the binary layer and **fails** at the integer
layer, and the failure is exhibited by named carriers `w1`, `w2` rather than
asserted. This is the cleanest instance in the development of a law with a
resolution boundary: true at one layer, false at the next.

---

## 9. The complete number-theoretic census

### 9.1 The hierarchy

| Class | Binary expansion | Wobble entropy | Binary period | μ_spect (§11) |
|---|---|---|---|---|
| Dyadic (m/2^k) | terminates | 0 exactly | — | purely point |
| Odd prime (1/p) | periodic | H(1/p) > 0 | ord_p(2) | point-like modulated |
| Full-reptend prime | periodic, length p−1 | H(1/p) > 0 | p−1 | point-like, richest |
| Irrational (√2, π) | aperiodic | high H(t) | ∞ | singular continuous |

### 9.2 The binary period as a fingerprint

The multiplicative order of 2 mod p is the number-theoretic invariant the
wobble makes visible. Recomputed, with the entropy taken from the exact
rational density and truncated at three places:

| p | ord_p(2) | full reptend | H(1/p) |
|---|---|---|---|
| 3 | 2 | yes | 0.918 |
| 5 | 4 | yes | 0.721 |
| 7 | 3 | no | 0.591 |
| 11 | 10 | yes | 0.439 |
| 13 | 12 | yes | 0.391 |
| 17 | 8 | no | 0.322 |
| 19 | 18 | yes | 0.297 |
| 23 | 11 | no | 0.258 |
| 29 | 28 | yes | 0.216 |
| 31 | 5 | no | 0.205 |
| 37 | 36 | yes | 0.179 |
| 41 | 20 | no | 0.165 |
| 43 | 14 | no | 0.159 |
| 47 | 23 | no | 0.148 |
| 53 | 52 | yes | 0.135 |
| 59 | 58 | yes | 0.123 |
| 61 | 60 | yes | 0.120 |
| 67 | 66 | yes | 0.111 |
| 71 | 35 | no | 0.106 |
| 73 | 9 | no | 0.104 |
| 79 | 39 | no | 0.097 |
| 83 | 82 | yes | 0.094 |
| 89 | 11 | no | 0.088 |
| 97 | 48 | no | 0.082 |

Twelve of the twenty-four are full reptend. Note 89, whose period is 11 — the same
as 23's — so the period alone does not identify the prime; it is a fingerprint,
not a name.

---

## 10. The operational landscape: three barriers, three freedoms

### 10.1 Three proven barriers

1. **The mantissa barrier** (`Mantissa.lean`). The doubling map kills every
   dyadic rational in k steps, so any system that uses it has a structural
   expiry date for every float it holds.
2. **The cardinality barrier** (`Irrational.lean`). No countable layer is
   lossless.
3. **The snap barrier** (`GolayBoundary.lean`, `Golay/Census.lean`). Nearest
   codeword decoding is unique to weight 3 and six-fold ambiguous at weight 4,
   and the mean coset weight 3433/1024 is already past the unique-reading
   radius.

### 10.2 Three proven freedoms

1. **The Sturmian freedom** (`Sturmian.lean`). Every property of the wobble
   stream is a closed form of the target: the wobble is not noise, it is the
   target in another alphabet.
2. **The tower freedom** (`Irrational.lean`, `Tower.lean`). No finite level is
   lossless, and the tower is injective all the same.
3. **The convergence freedom** (`DeltaSigma.lean`). O(1/N), for every real in
   [0,1), with the error stated at each N.

### 10.3 The price of a coincidence

`FitCapacity.lean` is the instrument that keeps §§1–9 honest: N candidate
predictions matching a target within δ cover a set of measure at most 2Nδ, so a
match is only evidence to the extent that it beats that guarantee. Applied to
three of the archive's headline fits it scores them at **under one bit**, three
to four bits, and two to three bits. A coincidence is not free, and it is not
worth much either.

---

## 11. The spectroscopic duality

> **Provenance.** Everything in this section is a *floating-point simulation of
> a physical measurement*, and it therefore lives outside the exact package: the
> script is [`studies/scripts/tmm_null_model.py`](scripts/tmm_null_model.py),
> not a `glm_universal` module, precisely because directive D7 forbids floats
> inside the substrate. The Sturmian sequences it feeds to the optics are
> generated by the same integer accumulator as everywhere else; only the optics
> is inexact.

### 11.1 The physical analogy

The Sturmian stream b_n = ⌊(n+1)t⌋ − ⌊nt⌋ has a dual representation in Fourier
space. Map it to a 1-D aperiodic optical medium — 0 a layer of material A, 1 a
layer of material B — and the diffraction intensity I(λ) is a function of the
structural parameters of t.

`dsState_eq_fract` proves the loop is an irrational rotation on a circle, which
is the cut-and-project construction used to define quasicrystals (De Bruijn;
Duneau & Katz). The exact integer arithmetic in ℤ/bℤ is the discrete boundary
of that projection.

### 11.2 Chemical media versus structural media

Bulk chemical compounds under a UV-Vis, Raman or mass spectrometer report
electron shells and molecular bonds. That data belongs to chemical physics and
will not show the number-theoretic wobble. To see this structure one has to
look at **metamaterials, nanophotonic crystals and aperiodic multilayers**,
where what varies is the *geometric sequencing* of thin films rather than the
chemistry.

### 11.3 The TMM formulation

For a wave vector k = 2π/λ the total transfer matrix of an N-layer stack
sequenced by b_n is

$$M_{\text{total}} = \prod_{j=1}^{N} \begin{pmatrix} \cos \delta_j & -\frac{i}{n_j} \sin \delta_j \\ -i\, n_j \sin \delta_j & \cos \delta_j \end{pmatrix}$$

with n_j ∈ {n_A, n_B} chosen by the Sturmian bit and δ_j = k·n_j·d_j the phase
thickness, and the reflectance is extracted as

$$R(\lambda) = \left| \frac{(M_{11} + M_{12} n_s) n_0 - (M_{21} + M_{22} n_s)}{(M_{11} + M_{12} n_s) n_0 + (M_{21} + M_{22} n_s)} \right|^2 .$$

**Parameters, as the script uses them:** layer A SiO₂ (n = 1.46, quarter-wave
thickness 94.2 nm), layer B TiO₂ (n = 2.40, 57.3 nm), design wavelength
λ₀ = 550 nm, 200 layers, air on both sides, sweep 400–700 nm at 300 points.

### 11.4 The spectral classification

Aperiodic systems are classified by their spectral measure type, following
Kohmoto, Kadanoff & Tang (1983) and Damanik, Killip & Lenz (2002):

| Number class | Entropy H(t) | Lean grounding | Spectral measure type | Physical analogue |
|---|---|---|---|---|
| dyadic (m/2^k) | exactly 0 | `dyadicOrbit_collapses` | purely point | periodic Bragg mirror |
| odd prime (1/p) | H(1/p) > 0 | `oddOrbit_periodic`, `exists_period` | point-like modulated | enveloped superlattice |
| irrational | maximal | `no_countable_layer_lossless` | singular continuous | Fibonacci quasicrystal |

1. **Purely point.** The word terminates, so the stack has a finite repeating
   unit cell and the diffraction pattern is a comb of sharp peaks.
2. **Point-like modulated.** The word is periodic with period ord_p(2), so the
   peaks cluster, and the cluster spacing reflects that period.
3. **Singular continuous.** The word is aperiodic, and the intensity is
   distributed over a Cantor set of zero Lebesgue measure.

### 11.5 The gap-labelling bridge

For a Sturmian potential the spectral gaps are labelled by the frequency module
of the word (Bellissard; Bovier & Ghez). For t = 1/p the word has period
ord_p(2), so the modulation envelope of the reflectance has that period in
units of the layer spacing, and the full-reptend primes — period p−1 — give the
longest envelope and the richest cluster structure. In that language ord_p(2)
plays the role of a winding number for the medium.

**This is the part of §11 that is an argument rather than a measurement.** The
gap-labelling theorem is a theorem about Schrödinger operators, and the step
from it to the reflectance of a finite dielectric stack is an analogy that the
simulation below does not establish. What the simulation does establish is
§11.7 and no more.

### 11.6 The quasicrystal literature

The Fibonacci Hamiltonian (Kohmoto, Kadanoff & Tang 1983; Ostlund et al. 1983)
is the Sturmian word of slope φ−1, and Sturmian potentials are known to have
zero-measure Cantor spectra (Damanik, Killip & Lenz 2002). The census of §9.2
is a generalised sweep of the same family: each prime is a different Sturmian
word and so a different medium.

### 11.7 The null-model control — what was actually measured

The claim under test is narrow: *the spectral structure is carried by the
Sturmian order, not by the bit statistics.* The control shuffles the layers of
each stack with a seeded permutation, so the bit statistics are identical and
only the order is destroyed, and the instrument is the standard deviation of
R across the sweep.

Recomputed here, 200 layers, 300 wavelengths, seed 20260903:

| target | class | ordered mean R | shuffled mean R | ordered std R | shuffled std R | spread lost? |
|---|---|---|---|---|---|---|
| 1/4 | dyadic | 0.5399 | 0.9859 | 0.3522 | 0.0707 | **yes** |
| 1/3 | odd prime | 0.4511 | 0.9887 | 0.3030 | 0.0535 | **yes** |
| 1/5 | odd prime | 0.5877 | 0.9715 | 0.3559 | 0.0942 | **yes** |
| 1/7 | odd prime | 0.5634 | 0.9444 | 0.3663 | 0.1382 | **yes** |
| 1/11 | odd prime | 0.4995 | 0.8619 | 0.3555 | 0.2047 | **yes** |
| 1/13 | odd prime | 0.4978 | 0.9157 | 0.3497 | 0.1243 | **yes** |
| √2−1 | irrational | 0.9183 | 0.9969 | 0.1928 | 0.0167 | **yes** |
| φ−1 | irrational | 0.9018 | 0.9975 | 0.2076 | 0.0182 | **yes** |
| π−3 | irrational | 0.6409 | 0.9610 | 0.3341 | 0.1027 | **yes** |

**9/9.** In every case the shuffled stack has a much flatter spectrum (spread
down by a factor of 1.7 to 11) and a mean reflectance close to 1: the random
stack is a broadband mirror with no selectivity.

Two honest notes on this table:

* The **ordered** column reproduces the original run of this experiment to four
  decimal places on eight of the nine targets — the ordered spectrum is a
  deterministic function of the target and there is nothing to seed. The ninth,
  π−3, differs in the fourth place (0.6409 against 0.6400) because the rational
  truncation of π−3 used here is not identical to the one used then; that is a
  statement about which exact rational stands in for π−3, and it is stated
  rather than hidden.
* The **shuffled** column depends on the seed. It is reported with the seed so
  that it can be reproduced, and the verdict — spread falls — holds for every
  seed tried, but the individual figures are not universal constants.

What this licenses: the spectrum depends on the order of the sequence, not only
on its statistics. What it does not license: any claim that a *particular*
number-theoretic invariant has been read off a spectrum. Doing that would need
the envelope period measured against ord_p(2) across a range of p, and that
experiment has not been run here.

---

## 12. The structural metamaterial landscape

### 12.1 The landscape

```
[THE OPERATIONAL LANDSCAPE]
          |
  +-------+-------+----------------------+
  v               v                      v
[periodic]   [enveloped]            [Cantor fractal]
dyadic       odd-prime               irrational towers
H = 0        H(1/p) > 0              maximal entropy
Bragg peaks  modulated sidebands     singular continuous
```

### 12.2 The classification

| Number class | Structural seed law | Expected optical landscape | Lean theorem |
|---|---|---|---|
| dyadic | finite repeating unit cell | discrete peaks, periodic band gaps | `dyadicOrbit_collapses` |
| odd prime | mod-p periodic orbit | enveloped resonances, clusters spaced by the binary period | `oddOrbit_periodic`, `exists_period` |
| irrational | infinite non-repeating tower | singular continuous, zero-measure Cantor | `no_countable_layer_lossless`, `dyadic_not_lossless` |

### 12.3 Two routes to validation

**A. Synthetic.** The TMM sweep of §11.7 — generate the stack, compute the
spectrum, compare against the shuffled control.

**B. Existing condensed-matter data.** Thue–Morse, Fibonacci and generalised
Sturmian multilayers are already catalogued in the literature; mapping the
invariants of §9.2 onto that data is an available check that has not been
carried out here.

---

## 13. Synthesis

### 13.1 What the substrate is

The Golay code [24,12,8], the Leech lattice Λ₂₄, and exact arithmetic on them.
It is not the universe and it does not generate the universe. It is a
mathematical object with unusual fidelity to the structure of numbers, and the
fidelity is provable (89 Lean files, 0 `sorry`) and measurable (exact integer
experiments, 24/24 Sturmian matches).

### 13.2 What it holds

1. **Rationals**, exactly, as integer pairs. The wobble signature is a Sturmian
   word and every property of it is a closed form of the target.
2. **Irrationals**, as processes rather than values: no finite carrier holds
   them (`no_countable_layer_lossless`), the tower is faithful
   (`towerView_injective`), and the modulator converges at O(1/N)
   (`dsAverage_error_le`).
3. **Coherence**, as NRCI, which is 1 exactly at the vacuum
   (`nrci_eq_one_iff`), with four exact tax bands.
4. **Ambiguity**, reported rather than resolved: at the snap boundary the
   substrate returns six equidistant codewords (`ties_card_eq_six`), and the
   mean coset weight is already past the unique-reading radius.

### 13.3 What it does not hold

1. **Floats.** The doubling map kills dyadic rationals; exact rationals in
   ℤ/bℤ avoid it.
2. **Irrationals as stored values.** Only as processes.
3. **A unique reading at every weight.** The weight-4 ambiguity is structural,
   and the substrate reports it rather than breaking the tie silently.

### 13.4 The layered-projection perspective

* the **24-bit word** sees binary structure — Hamming weight, parity;
* the **syndrome** sees the coset, a 12-bit error fingerprint;
* the **MOG cell** sees the octad geometry;
* the **Leech point** sees the integer lattice and its 196,560 minimal vectors;
* the **shell** sees the weight class.

A correspondence invisible at one layer can be exact one layer up. The
worked-out instance in this repository is dimensional rather than lattice
theoretic: torque and energy are *the same* in SI7, the seven SI base
dimensions, and *different* in EXT10, which adds plane angle, solid angle and
information. The projection EXT10 → SI7 is lossy exactly on concepts with a
nonzero angle or information exponent, and `physics.si7_projection_lossy`
decides which those are. §14 is the same phenomenon inside the code layer.

### 13.5 The measurement instrument

The GLM sees numbers by their oscillation signatures (Sturmian words), their
binary periods (multiplicative orders) and their substrate projections (Leech
coordinates), in the way a spectroscope sees atoms by emission lines. Each of
those is a projection; §14 shows one number losing information at each of them
in turn, which is the point.

---

## 14. Worked example: one number through the pipeline

This is the section the rest of the document is evidence for: what actually
happens to a piece of information as it passes down the layers. The transcript
below is the output of

```bash
cd overlay && PYTHONPATH=. python3 -m glm_universal.examples.number_pipeline
```

which recomputes every line; nothing here is quoted from a previous run.

```
target                t = 1/7   (exact Fraction, no float)

1  wobble             000000100000010000001000
   ones in 24 ticks   3   = floor(24t) = 3   law holds: True
   longest 0-run      6   (bound 1/t = 6)

2  word               0x102040  = 000100000010000001000000
   Hamming weight     3   support (6, 13, 20)

3  syndrome           110010100001  (3233)
   coset weight       3   leaders 1   unique reading: True
   nearest codeword   0x000000   at distance 3

4  MOG frame          001000  000001  001000  000000
   column weights     (0, 0, 2, 0, 0, 1)
   hexacode shadow    (0, 0, 2, 0, 0, 1)

5  2 x received       norm^2 = 12   in Leech: False
   2 x codeword       norm^2 = 0   in Leech: True   minimal: False   shape: weight 0

6  TAX of the word    1.169026   NRCI 0.895333   regime onBit

7  arithmetic layer   class odd-denominator   binary period 3   full reptend: False

8  resolution         4/27 shares the 24-bit word, and separates at 27 ticks
```

Read down the transcript, that is:

**1 → 2, the wobble becomes a word.** The modulator emits three ones in 24
ticks, which is ⌊24/7⌋ = 3 exactly (`dsOnes_eq_floor`), and the longest run of
zeros is 6, which is the largest the bound `L < 1/t` permits
(`ds_zero_run_length_lt`). Both theorems are attained, not merely respected.
The window itself is the first loss: 24 ticks of an infinite stream.

**2 → 3, the word becomes a syndrome — and the code layer throws the number
away.** The word has weight 3, which is inside the packing radius, so the
complete decoder corrects it to the **zero codeword**. At the code layer 1/7 is
indistinguishable from the vacuum plus a weight-3 error. This is a real loss,
and it is worth being precise about where the information went: it is *not*
gone, it is in the **syndrome** `110010100001`, which is exactly the piece the
codeword discards. Read at the code layer, the number is absent; read one layer
down at the coset, it is intact. This is the positioning note of §0.1, happening
in four lines.

**3 → 5, the lattice layer refuses the received word.** Doubling the received
word gives a vector of norm² 12 that is *not* in the Leech lattice, while
doubling the corrected codeword gives a lattice point (here the origin). The
lattice layer only accepts what the code layer has already cleaned, which is
why the pipeline runs the decoder first, and it is also why the cleaning cannot
be skipped.

**6, the cost layer prices the word rather than the number.** TAX = 3Y + 3/8 =
1.169…, NRCI 0.895…, regime *onBit*: a cheap, highly coherent carrier. Note
that this figure describes the *carrier*, not the target — every weight-3 word
gets the same price, and there are 2,024 cosets' worth of them.

**7, one layer up, the arithmetic is intact.** 1/7 has binary period ord₇(2) = 3
and is not full reptend (7 − 1 = 6). Nothing below the arithmetic layer can see
this, and nothing above it needs to.

**8, and the resolution is stated rather than assumed.** 4/27 emits *the same*
24 bits as 1/7, so at this resolution the two numbers are one object; they
separate at tick 27. The 24-bit word is a projection, and a claim of the form
"the substrate cannot tell these apart" is a claim about the width of the
window and not about the substrate.

Run the same script on a different target and the shape of the walk changes:
a dyadic target produces a word the decoder leaves alone, and a target whose
window happens to land on weight 4 produces the six-fold tie of §6.4 instead of
a unique correction. The script takes any `Fraction` in [0, 1).

---

## Appendix A: Lean theorem index

| File | Key theorems | Subject |
|---|---|---|
| `Constants.lean` | `nrci_eq_one_iff`, `tax_eq_zero_iff`, `regime_*_iff` | Y, Q, TAX, NRCI, the four regimes |
| `Calibration.lean` | `Y_bounds`, `tax_indicator`, `codewordTax_strictMono` | the sharpened constant, and the binary layer's single quantum |
| `TaxConservation.lean` | `tax_conservation`, `tax_conservation_fails_at_integer_layer` | a conservation law and its resolution boundary |
| `GolayBoundary.lean` | `snap_boundary_at_three`, `snap_ambiguous_at_four` | nearest-codeword decoding, both halves |
| `Golay/Sextet.lean` | `ties_card_eq_six` | the tie is six, exactly |
| `Mantissa.lean` | `dyadicOrbit_collapses`, `oddOrbit_periodic`, `exists_period` | the doubling map, and float drift as a theorem |
| `Sturmian.lean` | `dsState_eq_fract`, `dsOnes_eq_floor`, `ds_wobbleEntropy_tendsto` | the wobble stream as a Sturmian word |
| `DeltaSigma.lean` | `dsAverage_error_le`, `dsAverage_tendsto` | the O(1/N) convergence law |
| `Irrational.lean` | `no_countable_layer_lossless`, `towerView_injective` | the cardinality wall, and a faithful tower |
| `Tower.lean` | `dyadic_not_lossless`, `dyadic_separates`, `dyadic_boundary_nonempty` | the dyadic tower, level by level |
| `Harmony.lean` | `fifth_never_closes`, `odd_prime_ratio_ne_two_zpow` | the circle of fifths, and the general obstruction |
| `Golay/Census.lean` | `coset_census`, `mean_coset_weight`, `unique_vs_ambiguous` | the coset census, exactly |
| `Golay/Cesaro.lean` | `cesaro_converges` | Cesàro convergence at 24/N |
| `Reversible.lean` | `gray_two_mul_eq`, `toffoli_involutive`, `kinks_even` | Gray codes, reversible gates, kink parity |
| `Wobble.lean` | `sextet_cycle_avgVec`, `sextet_cycle_tendsto` | ambiguity as a moving carrier |
| `FitCapacity.lean` | `fit_capacity` | what a numerical coincidence is worth |
| `Shortcut/Leech.lean` | `leech_min_norm`, `golay_step_minimal_iff` | the lattice layer of §14 |

Every name in this table was read out of the tree by
`studies/scripts/` rather than retyped, and every statement quoted in the body
of the document is the statement in the file, not a paraphrase of it.

---

## Appendix B: Methodology

All wobble computations use **exact integer arithmetic**. The delta–sigma
modulator on target a/b is:

```
accumulated = 0
for each step:
    accumulated += a          # integer addition
    if accumulated >= b:      # integer comparison
        bit = 1
        accumulated -= b      # integer subtraction
    else:
        bit = 0
```

No `Fraction` objects in the inner loop, no GCD overhead, no floats: the
accumulator is n·a mod b, always an integer, so the emitted stream is the true
wobble of the exact rational a/b.

For an irrational, the target is the exact rational the generator supplies at a
stated resolution (for example √2 to ten Babylonian steps). The wobble computed
is then the true wobble of that exact rational, and the resolution is part of
the claim rather than a hidden approximation.

The only floating point anywhere in this document is the transfer-matrix
optics of §11, which lives outside the package for exactly that reason.

---

## Appendix C: Where the data is

Everything is in this repository; the earlier draft pointed at paths on the
machine the experiments were first run on, and those are replaced here by the
scripts that regenerate the data on demand.

| what | where |
|---|---|
| the exact tables of §1.3, §2.4, §9.2 | `studies/scripts/number_theory_tables.py` |
| the worked example of §14 | `overlay/glm_universal/examples/number_pipeline.py` |
| the TMM sweep and its null model | `studies/scripts/tmm_null_model.py` |
| the Lean development | `RequestProject/GLM/` (97 files) and its mirror `overlay/glm_lean/` |
| the wobble implementation | `overlay/glm_universal/reasoning/wobble.py` |
| the constants | `overlay/glm_universal/reasoning/coherence.py` |
| the Golay code and its decoder | `overlay/glm_universal/substrate/mog.py`, `.../golay_decode.py` |

---

## References

The classical sources this section leans on. Where I could not confirm a
volume, year and page triple, the entry gives author, title and journal only:
an unverifiable citation is worse than a missing one, and two entries of the
earlier draft carried volume numbers that do not correspond to the papers they
name.

1. De Bruijn, N. G. (1981). "Algebraic theory of Penrose's non-periodic tilings
   of the plane." *Nederl. Akad. Wetensch. Indag. Math.* **43**: 39–66.
2. Duneau, M. & Katz, A. (1985). "Quasiperiodic patterns." *Phys. Rev. Lett.*
   **54**: 2688–2691.
3. Kohmoto, M., Kadanoff, L. P. & Tang, C. (1983). "Localization problem in one
   dimension: mapping and escape." *Phys. Rev. Lett.* **50**: 1870–1872.
4. Ostlund, S., Pandit, R., Rand, D., Schellnhuber, H. & Siggia, E. (1983).
   "One-dimensional Schrödinger equation with an almost periodic potential."
   *Phys. Rev. Lett.* **50**: 1873–1876.
5. Damanik, D., Killip, R. & Lenz, D. "Uniform spectral properties of
   one-dimensional quasicrystals." *Communications in Mathematical Physics* —
   the series in which the zero-measure Cantor spectrum of Sturmian potentials
   is established.
6. Bellissard, J. "Gap labelling theorems for Schrödinger operators." In
   *From Number Theory to Physics*, Springer.
7. Bovier, A. & Ghez, J.-M. "Spectral properties of one-dimensional Schrödinger
   operators with potentials generated by substitutions."
   *Communications in Mathematical Physics*.
8. Sütő, A. "Schrödinger difference equation with deterministic ergodic
   potentials." *Journal of Statistical Physics*.
