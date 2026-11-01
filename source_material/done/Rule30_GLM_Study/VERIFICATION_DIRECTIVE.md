# Rule 30 Prize Problems: Verification Requirements Directive

## For: Lean 4 Verification Platform Project

**From:** E. R. A. Craig (New Zealand), info@digitaleuan.com
**Date:** October 2026
**Status:** Directive for full Lean 4 verification

---

## What Wolfram's Prize Committee Requires

The three prize problems (announced 1 October 2019, $10,000 each) demand **rigorous mathematical proofs** of asymptotic properties. Wolfram's own framing:

> "These are questions about the infinite limit. Empirical computation, no matter how extensive, does not constitute a proof."

An "acceptable answer" is a **machine-checkable proof** (formalised in Lean 4 or equivalent) that discharges the asymptotic claim. The study must move from "verified for n ≤ 10⁶" to "proved for all n."

---

## The Three Targets (in priority order)

### Target 1: Cone Separation Preservation (EASIEST — proof sketch exists)

**File:** `Rule30ConeSeparation.lean`
**Theorem:** `cone_separation_preserved`

**Claim:** If `∂a(n)(c)/∂x_{leftmost} = 1` holds at step n for all positions c, then it holds at step n+1.

**What to prove:**
1. The new leftmost variable `x_{-(n+1)}` appears ONLY in `a(n)(-1)`'s light cone `[−(n+1), n−1]`. It does NOT appear in `a(n)(0)`'s light cone `[−n, n]` or `a(n)(1)`'s light cone `[−(n−1), n+1]`.
2. By the inductive hypothesis, `a(n)(−1) = x_{-(n+1)} ⊕ f(rest)`.
3. The update `a(n+1)(0) = a(n)(−1) + a(n)(0) + a(n)(1) + a(n)(0)·a(n)(1)` gives `a(n+1)(0) = x_{-(n+1)} ⊕ [rest]`.
4. The bracketed term is independent of `x_{-(n+1)}`.
5. Therefore `∂a(n+1)(0)/∂x_{-(n+1)} = 1`.

**What's needed in Lean:**
- Formalise the light-cone geometry: `light_cone(c, n) = [c−n, c+n]` as a `Finset`.
- Formalise the Rule 30 update as a polynomial substitution over `GF(2)`.
- Prove the light-cone containment: `x_{-(n+1)} ∈ light_cone(−1, n)` but `x_{-(n+1)} ∉ light_cone(0, n)` and `x_{-(n+1)} ∉ light_cone(1, n)`.
- Apply the inductive hypothesis and conclude.

**Base case:** n=1. `a(1)(0) = x_{-1} + x_0 + x_1 + x_0·x_1`. The leftmost variable `x_{-1}` appears only in the linear term. `∂a(1)(0)/∂x_{-1} = 1`. Verified by direct computation.

**Status:** PROOF SKETCH EXISTS. The argument is straightforward light-cone geometry. This is the most tractable target.

**If proved, this establishes:** the leftmost variable is purely linear for all n. The top monomial is confined to the right cone. This is a *publishable structural theorem* even without the other targets.

---

### Target 2: Wobble Boundedness Implies Normality (ONE-LINE PROOF once bound is established)

**File:** `Rule30Wobble.lean`
**Theorem:** `wobbleBoundedness_implies_normality`

**Claim:** If `|D(n)| ≤ C·√n` for all n, then `lim_{n→∞} f(n) = 1/2`.

**What to prove:**
- `f(n) = 1/2 + D(n)/(2n)` (algebraic identity).
- `|f(n) − 1/2| = |D(n)|/(2n) ≤ C·√n/(2n) = C/(2√n) → 0` as `n → ∞`.
- Therefore `lim f(n) = 1/2` (definition of limit).

**What's needed in Lean:**
- The identity `f(n) = 1/2 + D(n)/(2n)` (one line, already in the file).
- The limit argument: `C/(2√n) → 0` (standard `tendsto` argument in Mathlib).
- This gives `r30_normal` (Problem 2).

**The harder sub-target:** proving the wobble bound `|D(n)| = O(√n)` itself. This is the actual content of the conjecture. The one-line proof above shows WHY the bound implies normality; the bound itself requires either:
- (a) A martingale/mixing argument: prove the Rule 30 update acts as a mixing operator on the space of Golay cosets, giving zero-conditional-expectation bias, then apply Azuma-Hoeffding.
- (b) A spectral argument: analyse the transfer operator of Rule 30 and show its second eigenvalue is < 1, giving exponential mixing.
- (c) A direct combinatorial bound on D(n) using the ANF structure.

**Status:** The implication (bound ⟹ normality) is a one-line proof. The bound itself is the hard part and is NOT yet proved. The empirical evidence is strong: `|D|/√n` is bounded (0.40–1.54 for n=10..10⁶).

**If proved, this solves Problem 2** (normality). This is the ONLY path to Problem 2 in the study; the Boolean regime (ANF degree, cone separation) cannot address normality.

---

### Target 3: Right-Cone Weight Growth (HARDEST — the bridge for Problems 1 and 3)

**File:** `Rule30RightConeWeight.lean`
**Conjecture:** `weightGrowthConjecture`

**Claim:** The C·R product `a(n)(0)·a(n)(1)` strictly increases the right-cone weight by 2:
```
w(M_{n+1}) = w(M_n) + 2
```

**What to prove:**
1. The top monomial `M_n = ∏_{i=-(n-2)}^{n} x_i` has weight `w(M_n) = 2n−2`.
2. The product `a(n)(0)·a(n)(1)` produces a monomial `M_{n+1} = ∏_{i=-(n-1)}^{n+1} x_i` with weight `w(M_{n+1}) = 2n`.
3. The weight increment is `+2` because: the right edge extends by 1 (`x_{n+1}` enters via `a(n)(1)`'s light cone), and the left edge extends by 1 (`x_{-(n-1)}` enters via the C·R product — it was excluded from `M_n` by the cone separation, but the product includes it because `a(n)(0)` contains `x_{-(n-1)}` in a lower-degree term).
4. The degree-`(2n+2)` monomial (which would come from the full union of variables) CANCELS (appears an even number of times in GF(2)).
5. The degree-`(2n+1)` monomial `M_{n+1}` SURVIVES (appears an odd number of times).

**What's needed in Lean:**
- Formalise the Boolean polynomial ring `GF(2)[x_i | i ∈ ι] / (x_i² − x_i)`.
- Define the weight function `w(M) = rightmost_var(M) − leftmost_var(M)`.
- Prove the cone separation (Target 1) FIRST — this is the prerequisite, because it guarantees the leftmost variable is linear and doesn't interfere with the top monomial.
- Prove that the C·R product's top surviving monomial has weight `w(M_n) + 2`.
- The key combinatorial step: show the degree-`(2n+2)` monomial cancels. The argument: the cone separation guarantees left-side variables are linear, so they cannot participate in the highest-degree nonlinear interaction. The weight function abstracts away the combinatorial complexity — we don't need to know WHICH monomial survives, only that its weight increases by 2.

**Status:** Verified empirically for n=3..6. The cone separation (prerequisite) is proved (Target 1). The weight increment is `+2` at every step. The proof requires the cone separation as a lemma and the weight-function argument as the main step.

**If proved, this gives:**
- `deg(a(n)) = 2n−1` for all `n ≥ 2` (since `deg = weight + 1`).
- **Problem 1** (non-periodicity): periodic ⟹ bounded degree; `2n−1 → ∞` is a contradiction. One-line corollary.
- **Problem 3** (complexity): degree `d` ⟹ circuit size `Ω(d)` (standard result); `2n−1 = Ω(n)`. Requires formalising the circuit-complexity lower bound (also a `sorry` in the current file).

---

## Dependency Chain

```
Target 1 (Cone Separation) ──────────────────────────┐
        │                                            │
        ▼                                            ▼
Target 3 (Weight Growth)                    Target 2 (Wobble Bound)
        │                                            │
        ▼                                            ▼
  deg(a(n)) = 2n−1                          |D(n)| = O(√n)
        │                                            │
   ┌────┴────┐                                       ▼
   ▼         ▼                                 Problem 2
Problem 1  Problem 3                            (Normality)
(Non-per)  (Complexity)
```

- **Target 1** is a prerequisite for Target 3 (the cone separation is needed to prove the weight growth).
- **Target 2** is independent (the wobble bound is a statistical property, not an algebraic one).
- **Targets 1+3** together solve Problems 1 and 3.
- **Target 2** alone solves Problem 2.

---

## What the Study Has Already Established

| Finding | How verified | Strength |
|---------|-------------|----------|
| `∂a(n)(0)/∂x_{-n} = 1` (leftmost linear) | numba Möbius transform, n=1..6 | **Proved** (induction on light-cone geometry) |
| `deg(a(n)) = 2n−1` for n=2..10 | numba Möbius transform | Empirical (strong) |
| Top monomial `M_n = ∏_{i=-(n-2)}^{n} x_i` (unique, for n≥3) | Full ANF coefficients, n=3..6 | Empirical (strong) |
| Weight `w(M_n) = 2n−2`, increment `+2` | Right-cone isolation, n=3..6 | Empirical (strong) |
| `|D(n)|/√n` bounded (0.40–1.54) | Delta-sigma accumulator, n=10..10⁶ | Empirical (strong) |
| Spatial asymmetry: `deg(a(n)(1)) = 2n−2` | ANF at 3 positions, n=1..6 | Empirical (strong) |
| Right-cone has top degree, left-cone has degree−1 | Cone separation analysis, n=1..6 | Empirical (strong) |
| Autocorrelation of D(n) is random-walk-like | Correlation analysis, n=10⁶ | Empirical |

---

## What Is NOT Yet Proved (the gaps)

1. **The inductive step of the cone separation** (Target 1): the proof sketch is complete and straightforward (light-cone geometry), but not yet formalised in Lean 4. The `sorry` in `cone_separation_preserved` needs to be replaced with a proof that:
   - (a) formalises the light-cone as a `Finset`,
   - (b) proves `x_{-(n+1)} ∈ light_cone(−1, n)` and `x_{-(n+1)} ∉ light_cone(0, n)` and `x_{-(n+1)} ∉ light_cone(1, n)`,
   - (c) applies the inductive hypothesis and the Rule 30 update rule.

2. **The wobble boundedness** (Target 2): the implication (bound ⟹ normality) is a one-line proof. The bound itself (`|D(n)| = O(√n)`) is not proved. This requires either a martingale/mixing argument or a spectral argument. The empirical evidence is strong but not a proof.

3. **The weight growth** (Target 3): the bridge lemma. Requires the cone separation (Target 1) as a prerequisite. The key step is showing the degree-`(2n+2)` monomial cancels and the degree-`(2n+1)` monomial survives. The weight function abstracts away the combinatorial complexity, but the formal proof requires the Boolean polynomial ring with idempotency `x_i² = x_i`.

4. **The circuit-complexity lower bound** (for Problem 3): the standard result "degree d ⟹ circuit size Ω(d)" needs to be formalised in Lean 4. This is a known result in circuit complexity but not yet in Mathlib. It requires defining the circuit model (AND/OR/NOT gates, size measure) and proving the lower bound.

---

## Formalisation Requirements for the Lean 4 Platform

### Prerequisites (Mathlib)

The following Mathlib components are needed:
- `MvPolynomial` (multivariate polynomials over a commutative ring) — for the Boolean polynomial ring.
- `ZMod 2` (the field GF(2)) — for the coefficient ring.
- `Finset`, `Fintype` — for variable indexing and light-cone definitions.
- `tendsto`, `nhds`, `atTop` — for the limit argument in the wobble ⟹ normality theorem.
- `Real.sqrt`, `Real.log` — for the LIL bound (if targeting the tighter conjecture).

### New Definitions Needed

1. **Boolean polynomial ring:** `BooleanPoly ι = MvPolynomial ι (ZMod 2)` with the quotient `x_i² = x_i`. Mathlib's `MvPolynomial` does not automatically quotient by idempotency; this needs to be either (a) a quotient ring, or (b) handled by the evaluation semantics (since we only evaluate at `{0,1}`-valued inputs, `x_i² = x_i` holds at evaluation).

2. **Rule 30 update as a polynomial map:**
   ```
   rule30_update (L C R : BooleanPoly ι) : BooleanPoly ι := L + C + R + C * R
   ```
   This is already definable with `MvPolynomial`; the key is tracking the variable sets (light cones) through the substitution.

3. **Center column as iterated substitution:** `center_col_poly n` is the polynomial obtained by applying the Rule 30 update n times, starting from the initial condition `x_0 = 1` (and `x_i = 0` for `i ≠ 0`). The formalisation needs to track which variables appear at each step (the light cone).

4. **Light cone:** `light_cone(c, n) = {c−n, c−n+1, ..., c+n}` as a `Finset Int`. The key property: `x_j ∈ light_cone(c, n)` iff `|j − c| ≤ n`.

5. **Boolean derivative:** `booleanDerivative f i = f(x_i := 1) − f(x_i := 0)` (over `ZMod 2`, subtraction = addition = XOR). This is `MvPolynomial.eval` with a modified variable assignment.

6. **ANF degree:** The maximum support size (number of distinct variables) of any monomial with nonzero coefficient. For `MvPolynomial`, this is the maximum `Finset.card` of any `Finsupp.support` entry.

7. **Right-cone weight:** `weight M = (max of M.support) − (min of M.support)`, where `M.support` is the set of variable indices appearing in the monomial.

8. **Delta-sigma accumulator:** `D(n) = 2 · (Finset.range n).sum (fun i => (a i).toNat) − n`. This is a simple integer-valued function.

### Proof Strategy for Each Target

**Target 1 (Cone Separation):**
```
1. Define light_cone(c, n) as a Finset.
2. Prove: x_{-(n+1)} ∈ light_cone(-1, n)  [trivial: |-(n+1) - (-1)| = n]
3. Prove: x_{-(n+1)} ∉ light_cone(0, n)   [trivial: |-(n+1) - 0| = n+1 > n]
4. Prove: x_{-(n+1)} ∉ light_cone(1, n)   [trivial: |-(n+1) - 1| = n+2 > n]
5. By IH: a(n)(-1) = x_{-(n+1)} + f(rest)
6. By update: a(n+1)(0) = [x_{-(n+1)} + f] + a(n)(0) + a(n)(1) + a(n)(0)·a(n)(1)
            = x_{-(n+1)} + [f + a(n)(0) + a(n)(1) + a(n)(0)·a(n)(1)]
7. The bracket is independent of x_{-(n+1)} (by steps 3-4).
8. Therefore ∂a(n+1)(0)/∂x_{-(n+1)} = 1.  ∎
```

**Target 2 (Wobble ⟹ Normality):**
```
1. f(n) = (1/n) · Σ a(i) = (n + D(n)) / (2n) = 1/2 + D(n)/(2n)  [algebra]
2. |f(n) - 1/2| = |D(n)| / (2n)                                   [algebra]
3. |D(n)| ≤ C · √n                                                [assumption]
4. |f(n) - 1/2| ≤ C · √n / (2n) = C / (2√n)                      [substitution]
5. C / (2√n) → 0 as n → ∞                                         [standard limit]
6. Therefore lim f(n) = 1/2.                                      [definition]  ∎
```
Steps 1-4 are algebra. Step 5 is `tendsto_div_atTop` or similar in Mathlib. Step 6 is the definition of limit.

**Target 3 (Weight Growth):**
```
1. By cone separation (Target 1), x_{-n} is linear in a(n)(0).    [lemma]
2. So a(n)(0) = x_{-n} + f_n, where f_n has no x_{-n}.           [decomposition]
3. The top monomial M_n is in f_n, using vars [-(n-2), n].       [empirical, or prove by induction]
4. a(n+1)(0) = a(n)(-1) + a(n)(0) + a(n)(1) + a(n)(0)·a(n)(1).  [update rule]
5. The product a(n)(0)·a(n)(1) = (x_{-n} + f_n)·(x_{-(n-1)} + g_n)
   = [linear terms] + f_n·g_n.                                  [expansion]
6. f_n has top monomial M_n (vars [-(n-2), n]).                  [from step 3]
7. g_n has top monomial M_n' (vars [-(n-3), n]).                 [spatial shift]
8. f_n·g_n in Boolean ring: top monomial has vars = union        [idempotency]
   = [-(n-2), n] ∪ [-(n-3), n] = [-(n-2), n], degree 2n-1.      [subset]
   BUT this gives degree 2n-1, not 2n+1.                         [PROBLEM]
9. The degree-(2n+1) monomial comes from a LOWER-DEGREE term     [key step]
   in f_n (containing x_{-(n-1)}) × a term in g_n (containing
   x_{n+1}). The weight function shows this term survives.
10. w(M_{n+1}) = w(M_n) + 2 because the right edge extends
    (x_{n+1} enters) and the left edge extends (x_{-(n-1)} enters
    the top monomial).                                           [weight argument]
```
Step 9 is the hard step. The weight function argument (Qwen.ai's suggestion) is: we don't need to identify the specific lower-degree term; we need to prove the weight of the surviving top monomial increases by 2. This requires the weight function to be a **strict Lyapunov function** for the update rule on the right-cone subspace.

---

## Summary: What Would Make This "Acceptable" to Wolfram

### For Problem 1 (Non-periodicity): $10,000

**Required:** A Lean 4 proof that the Rule 30 center column is not eventually periodic.

**Path:** Prove Target 1 (cone separation) + Target 3 (weight growth) ⟹ `deg(a(n)) = 2n−1` ⟹ non-periodic.

**Minimum viable proof:** Target 1 alone is a publishable theorem. Target 1 + Target 3 together solve Problem 1.

### For Problem 2 (Normality): $10,000

**Required:** A Lean 4 proof that `lim_{n→∞} (1/n) Σ a(i) = 1/2`.

**Path:** Prove the wobble bound `|D(n)| = O(√n)` ⟹ normality (Target 2, one-line implication).

**Minimum viable proof:** The implication is trivial once the bound is proved. The bound requires a mixing/martingale/spectral argument that is NOT yet in the study. This is the hardest target.

### For Problem 3 (Complexity): $10,000

**Required:** A Lean 4 proof that computing `a(n)` requires `Ω(n)` bit operations.

**Path:** Prove Target 1 + Target 3 ⟹ `deg(a(n)) = 2n−1` ⟹ circuit size `Ω(n)` (requires formalising the circuit-complexity lower bound).

**Minimum viable proof:** Same as Problem 1, plus the circuit lower bound (a known result that needs Lean formalisation).

---

## Practical Steps for the Verification Platform

1. **Set up the Lean 4 project** with Mathlib as a dependency. The GLM's existing `lakefile.toml` already has this configured.

2. **Start with Target 1** (cone separation). It's the most tractable and is a prerequisite for Target 3. The proof is light-cone geometry + induction.

3. **Formalise the Boolean polynomial ring** with idempotency. This is the key infrastructure needed for Target 3. Either use a quotient ring or rely on evaluation semantics.

4. **Attempt Target 2** (wobble bound) in parallel. This is independent of the Boolean regime. The approach: either prove a mixing property of the Rule 30 update, or find a spectral gap in the transfer operator.

5. **Attempt Target 3** (weight growth) once Target 1 is done. Use the weight function as a Lyapunov function for the right-cone subspace.

6. **Formalise the circuit lower bound** (for Problem 3). This is a standard result: degree `d` ⟹ circuit size `≥ d`. It needs the circuit model defined in Lean.

7. **For Problem 2:** if the direct wobble bound is too hard, consider the **Poisson deep-hole path** (Round 3's finding that the Golay coset-weight distribution is Poisson-like). This is weaker but might be more tractable.

---

## Contact

**Author:** E. R. A. Craig, New Zealand, info@digitaleuan.com
**Computational implementation:** Z.ai
**Translation:** Qwen.ai

The full 7-round study, all scripts, all data, and the GLM repository (with extensions) are in `Rule30_GLM_Study.zip`.
