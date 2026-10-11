module

public import Mathlib
public import RequestProject.GLM.DerivationsTwo

/-!
# Past the Shannon cone, past the tight range, past closed form (Phase 118)

`studies/DERIVATION_THREE_STUDY.md` takes the limits the second derivation
study left (`DERIVATION_TWO_STUDY.md` §6) that are derivations.  This file
proves what the new readings rest on.

* **Zhang–Yeung from one copy** (`zhang_yeung_of_copy`): a set function on
  five points `A, B, C, D, R` meeting every Shannon inequality, in which `R`
  is a copy of `C` over `{A, D}` (same joint values with every subset of
  `{A, D}`, and `I(R; B, C | A, D) = 0`), satisfies the Zhang–Yeung
  inequality on `A, B, C, D`.  The proof is the eleven-term certificate the
  machine prints.  The copy lemma — that every distribution of four random
  variables has such a fifth variable — is the standard construction
  `p(a, b, c, d) p(r | a, d)` and is *not* proved here; the reading says so.
* **Zhang–Yeung is not Shannon-type** (`zhang_yeung_not_shannon`): an
  integer polymatroid on four points violates it, so no Shannon-type
  certificate exists.
* **Ingleton fails for entropy** (`ingleton_violated`): four random
  variables on four atoms with probabilities `1/3, 1/3, 1/6, 1/6` violate
  Ingleton's inequality by `2 log 3 - 3 log 2 > 0` nats.
* **The dual lower bound for rate distortion** (`rd_dual_lower_bound`): for
  any joint law with source marginal `p` and expected distortion at most
  `D`, and any `s ≥ 0`, `μ > 0` with `Σₓ p(x) μ(x) e^{-s d(x, y)} ≤ 1` for
  every `y`, the mutual information is at least `Σₓ p(x) log μ(x) - s D`.
  The machine's rate–distortion pieces print a rational test channel and a
  rational dual point that meet this bound with equality.
* **Robin eigenvalues** (`robin_root_exists`, `robin_eigenfunction`): for
  `y(0) = 0`, `y'(L) + h y(L) = 0` with `h, L > 0`, the equation
  `k cos(kL) + h sin(kL) = 0` has a root in every interval
  `((n - 1/2)π/L, nπ/L)`, and at a root `sin(kx)` solves `y'' + k² y = 0`
  with both conditions.
-/

@[expose] public section

namespace GLM.NonShannon

open GLM.DerivationsTwo Real

/-! ## 1. Zhang–Yeung -/

/-- **The Zhang–Yeung inequality from one copy.**  Points `0 = A`, `1 = B`,
`2 = C`, `3 = D`, `4 = R`. -/
theorem zhang_yeung_of_copy (h : Finset (Fin 5) → ℝ)
    (hsh : ∀ A B C, 0 ≤ cmi h A B C)
    (c1 : h {4} = h {2}) (c2 : h {3, 4} = h {2, 3}) (c3 : h {0, 4} = h {0, 2})
    (c4 : h {0, 3, 4} = h {0, 2, 3}) (ci : cmi h {4} {1, 2} {0, 3} = 0) :
    2 * cmi h {2} {3} ∅ ≤
      cmi h {0} {1} ∅ + cmi h {0} {2, 3} ∅ + 3 * cmi h {2} {3} {0} +
        cmi h {2} {3} {1} := by
  have e0 := hsh {2} {3} {1, 4}
  have e1 := hsh {2} {4} {3}
  have e2 := hsh {2} {4} {0}
  have e3 := hsh {2} {4} {0, 1}
  have e4 := hsh {3} {0} {2, 4}
  have e5 := hsh {3} {4} {0, 1, 2}
  have e6 := hsh {0} {1} {4}
  have e7 := hsh {0} {4} {1, 2, 3}
  have e8 := hsh {1} {4} {2}
  have e9 := hsh {1} {4} {3}
  have e10 := hsh {1} {4} {0, 2, 3}
  simp only [cmi] at *
  simp only [show ({0, 1} ∪ {4} : Finset (Fin 5)) = {0, 1, 4} by decide, show ({0, 1} ∪ ∅ : Finset (Fin 5)) = {0, 1} by decide, show ({0, 2, 3} ∪ ∅ : Finset (Fin 5)) = {0, 2, 3} by decide, show ({0, 3} ∪ {2, 4} : Finset (Fin 5)) = {0, 2, 3, 4} by decide, show ({0, 4} ∪ {1, 2, 3} : Finset (Fin 5)) = {0, 1, 2, 3, 4} by decide, show ({0} ∪ {1, 2, 3} : Finset (Fin 5)) = {0, 1, 2, 3} by decide, show ({0} ∪ {1} : Finset (Fin 5)) = {0, 1} by decide, show ({0} ∪ {2, 3} : Finset (Fin 5)) = {0, 2, 3} by decide, show ({0} ∪ {2, 4} : Finset (Fin 5)) = {0, 2, 4} by decide, show ({0} ∪ {4} : Finset (Fin 5)) = {0, 4} by decide, show ({0} ∪ ∅ : Finset (Fin 5)) = {0} by decide, show ({1, 2, 4} ∪ {0, 3} : Finset (Fin 5)) = {0, 1, 2, 3, 4} by decide, show ({1, 2} ∪ {0, 3} : Finset (Fin 5)) = {0, 1, 2, 3} by decide, show ({1, 4} ∪ {0, 2, 3} : Finset (Fin 5)) = {0, 1, 2, 3, 4} by decide, show ({1, 4} ∪ {2} : Finset (Fin 5)) = {1, 2, 4} by decide, show ({1, 4} ∪ {3} : Finset (Fin 5)) = {1, 3, 4} by decide, show ({1} ∪ {0, 2, 3} : Finset (Fin 5)) = {0, 1, 2, 3} by decide, show ({1} ∪ {2} : Finset (Fin 5)) = {1, 2} by decide, show ({1} ∪ {3} : Finset (Fin 5)) = {1, 3} by decide, show ({1} ∪ {4} : Finset (Fin 5)) = {1, 4} by decide, show ({1} ∪ ∅ : Finset (Fin 5)) = {1} by decide, show ({2, 3} ∪ {0} : Finset (Fin 5)) = {0, 2, 3} by decide, show ({2, 3} ∪ {1, 4} : Finset (Fin 5)) = {1, 2, 3, 4} by decide, show ({2, 3} ∪ {1} : Finset (Fin 5)) = {1, 2, 3} by decide, show ({2, 3} ∪ ∅ : Finset (Fin 5)) = {2, 3} by decide, show ({2, 4} ∪ {0, 1} : Finset (Fin 5)) = {0, 1, 2, 4} by decide, show ({2, 4} ∪ {0} : Finset (Fin 5)) = {0, 2, 4} by decide, show ({2, 4} ∪ {3} : Finset (Fin 5)) = {2, 3, 4} by decide, show ({2} ∪ {0, 1} : Finset (Fin 5)) = {0, 1, 2} by decide, show ({2} ∪ {0} : Finset (Fin 5)) = {0, 2} by decide, show ({2} ∪ {1, 4} : Finset (Fin 5)) = {1, 2, 4} by decide, show ({2} ∪ {1} : Finset (Fin 5)) = {1, 2} by decide, show ({2} ∪ {3} : Finset (Fin 5)) = {2, 3} by decide, show ({2} ∪ {4} : Finset (Fin 5)) = {2, 4} by decide, show ({2} ∪ ∅ : Finset (Fin 5)) = {2} by decide, show ({3, 4} ∪ {0, 1, 2} : Finset (Fin 5)) = {0, 1, 2, 3, 4} by decide, show ({3} ∪ {0, 1, 2} : Finset (Fin 5)) = {0, 1, 2, 3} by decide, show ({3} ∪ {0} : Finset (Fin 5)) = {0, 3} by decide, show ({3} ∪ {1, 4} : Finset (Fin 5)) = {1, 3, 4} by decide, show ({3} ∪ {1} : Finset (Fin 5)) = {1, 3} by decide, show ({3} ∪ {2, 4} : Finset (Fin 5)) = {2, 3, 4} by decide, show ({3} ∪ {4} : Finset (Fin 5)) = {3, 4} by decide, show ({3} ∪ ∅ : Finset (Fin 5)) = {3} by decide, show ({4} ∪ {0, 1, 2} : Finset (Fin 5)) = {0, 1, 2, 4} by decide, show ({4} ∪ {0, 1} : Finset (Fin 5)) = {0, 1, 4} by decide, show ({4} ∪ {0, 2, 3} : Finset (Fin 5)) = {0, 2, 3, 4} by decide, show ({4} ∪ {0, 3} : Finset (Fin 5)) = {0, 3, 4} by decide, show ({4} ∪ {0} : Finset (Fin 5)) = {0, 4} by decide, show ({4} ∪ {1, 2, 3} : Finset (Fin 5)) = {1, 2, 3, 4} by decide, show ({4} ∪ {1, 2} : Finset (Fin 5)) = {1, 2, 4} by decide, show ({4} ∪ {2} : Finset (Fin 5)) = {2, 4} by decide, show ({4} ∪ {3} : Finset (Fin 5)) = {3, 4} by decide] at *
  linarith

/-- The Zhang–Yeung inequality on four points, as a predicate on a set
function. -/
def ZhangYeung (h : Finset (Fin 4) → ℝ) : Prop :=
  2 * cmi h {2} {3} ∅ ≤
    cmi h {0} {1} ∅ + cmi h {0} {2, 3} ∅ + 3 * cmi h {2} {3} {0} +
      cmi h {2} {3} {1}

/-- The polymatroid witness, integer-valued: `2` on points, `3` on pairs
except `{A, B}`, `4` on `{A, B}` and on every larger set. -/
def zyWitness (S : Finset (Fin 4)) : ℤ :=
  if S.card = 0 then 0 else if S.card = 1 then 2
  else if S.card = 2 ∧ S ≠ {0, 1} then 3 else 4

/-- The witness meets every Shannon inequality (all `4096` triples, decided). -/
theorem zyWitness_shannon : ∀ A B C : Finset (Fin 4),
    0 ≤ zyWitness (A ∪ C) + zyWitness (B ∪ C) - zyWitness (A ∪ B ∪ C) - zyWitness C := by
  decide

/-- The witness violates Zhang–Yeung: `2 I(C;D) = 2` while the right side is `1`. -/
theorem zyWitness_violates :
    ¬ (2 * (zyWitness {2} + zyWitness {3} - zyWitness {2, 3} - zyWitness ∅) ≤
      (zyWitness {0} + zyWitness {1} - zyWitness {0, 1} - zyWitness ∅) +
      (zyWitness {0} + zyWitness {2, 3} - zyWitness {0, 2, 3} - zyWitness ∅) +
      3 * (zyWitness {0, 2} + zyWitness {0, 3} - zyWitness {0, 2, 3} - zyWitness {0}) +
      (zyWitness {1, 2} + zyWitness {1, 3} - zyWitness {1, 2, 3} - zyWitness {1})) := by
  decide

/-- **Zhang–Yeung is not Shannon-type**: a polymatroid violates it. -/
theorem zhang_yeung_not_shannon :
    ∃ h : Finset (Fin 4) → ℝ, h ∅ = 0 ∧ (∀ A B C, 0 ≤ cmi h A B C) ∧
      ¬ ZhangYeung h := by
  refine ⟨fun S => (zyWitness S : ℝ), by simp [zyWitness], fun A B C => ?_, ?_⟩
  · have := zyWitness_shannon A B C
    simp only [cmi]
    exact_mod_cast this
  · intro hzy
    apply zyWitness_violates
    have e1 : ({2} ∪ ∅ : Finset (Fin 4)) = {2} := by decide
    have e2 : ({3} ∪ ∅ : Finset (Fin 4)) = {3} := by decide
    have e3 : ({2} ∪ {3} ∪ ∅ : Finset (Fin 4)) = {2, 3} := by decide
    have e4 : ({0} ∪ ∅ : Finset (Fin 4)) = {0} := by decide
    have e5 : ({1} ∪ ∅ : Finset (Fin 4)) = {1} := by decide
    have e6 : ({0} ∪ {1} ∪ ∅ : Finset (Fin 4)) = {0, 1} := by decide
    have e7 : ({2, 3} ∪ ∅ : Finset (Fin 4)) = {2, 3} := by decide
    have e8 : ({0} ∪ {2, 3} ∪ ∅ : Finset (Fin 4)) = {0, 2, 3} := by decide
    have e9 : ({2} ∪ {0} : Finset (Fin 4)) = {0, 2} := by decide
    have e10 : ({3} ∪ {0} : Finset (Fin 4)) = {0, 3} := by decide
    have e11 : ({2} ∪ {3} ∪ {0} : Finset (Fin 4)) = {0, 2, 3} := by decide
    have e12 : ({2} ∪ {1} : Finset (Fin 4)) = {1, 2} := by decide
    have e13 : ({3} ∪ {1} : Finset (Fin 4)) = {1, 3} := by decide
    have e14 : ({2} ∪ {3} ∪ {1} : Finset (Fin 4)) = {1, 2, 3} := by decide
    simp only [ZhangYeung, cmi, e1, e2, e3, e4, e5, e6, e7, e8, e9, e10, e11, e12, e13,
      e14] at hzy
    exact_mod_cast hzy

/-! ## 2. Ingleton -/

/-- The entropy (nats) of `f(ω)` when `ω` has law `p` on a finite space:
`H = -Σ_ω p(ω) log P(f = f ω)` — the grouping form of `-Σ_y P(y) log P(y)`. -/
noncomputable def entropyOf {Ω β : Type*} [Fintype Ω] [DecidableEq β]
    (p : Ω → ℝ) (f : Ω → β) : ℝ :=
  -∑ ω, p ω * Real.log (∑ ω', if f ω' = f ω then p ω' else 0)

/-- The law on four atoms. -/
noncomputable def ingletonLaw : Fin 4 → ℝ := ![1/3, 1/3, 1/6, 1/6]

/-- The four variables on the atoms `(0,0,0,0)`, `(1,1,1,1)`, `(1,0,1,0)`,
`(1,0,0,1)`. -/
def ingA : Fin 4 → Bool := ![false, true, true, true]
def ingB : Fin 4 → Bool := ![false, true, false, false]
def ingC : Fin 4 → Bool := ![false, true, true, false]
def ingD : Fin 4 → Bool := ![false, true, false, true]

/-- Entropy under the law on four atoms. -/
noncomputable def ingH {β : Type*} [DecidableEq β] (f : Fin 4 → β) : ℝ :=
  entropyOf ingletonLaw f

/-- `I(A;B)` under the law. -/
noncomputable def ingIAB : ℝ := ingH ingA + ingH ingB - ingH (fun ω => (ingA ω, ingB ω))

/-- `I(A;B|C) + I(A;B|D) + I(C;D)` under the law. -/
noncomputable def ingRHS : ℝ :=
  (ingH (fun ω => (ingA ω, ingC ω)) + ingH (fun ω => (ingB ω, ingC ω)) -
      ingH (fun ω => (ingA ω, ingB ω, ingC ω)) - ingH ingC) +
    (ingH (fun ω => (ingA ω, ingD ω)) + ingH (fun ω => (ingB ω, ingD ω)) -
      ingH (fun ω => (ingA ω, ingB ω, ingD ω)) - ingH ingD) +
    (ingH ingC + ingH ingD - ingH (fun ω => (ingC ω, ingD ω)))

/-- **Ingleton's inequality fails for entropy**:
`I(A;B) - (I(A;B|C) + I(A;B|D) + I(C;D)) = 2 log 3 - 3 log 2 > 0`. -/
theorem ingleton_violated :
    ingIAB - ingRHS = 2 * Real.log 3 - 3 * Real.log 2 ∧ ingRHS < ingIAB := by
  have h6 : Real.log 6 = Real.log 2 + Real.log 3 := by
    rw [show (6:ℝ) = 2 * 3 by norm_num, Real.log_mul (by norm_num) (by norm_num)]
  have h12 : Real.log (1/2) = - Real.log 2 := by simp
  have h13 : Real.log (1/3) = - Real.log 3 := by simp
  have h16 : Real.log (1/6) = -(Real.log 2 + Real.log 3) := by simp [h6]
  have h23 : Real.log (2/3) = Real.log 2 - Real.log 3 := Real.log_div (by norm_num) (by norm_num)
  have h32 : Real.log (3/2) = Real.log 3 - Real.log 2 := Real.log_div (by norm_num) (by norm_num)
  have key : ingIAB - ingRHS = 2 * Real.log 3 - 3 * Real.log 2 := by
    simp [ingIAB, ingRHS, ingH, entropyOf, Fin.sum_univ_four, ingletonLaw, ingA, ingB, ingC, ingD]
    norm_num [h6, h12, h13, h16, h23, h32]
    ring
  refine ⟨key, ?_⟩
  have h89 : Real.log 8 < Real.log 9 := Real.log_lt_log (by norm_num) (by norm_num)
  rw [show (8:ℝ) = 2 ^ 3 by norm_num, show (9:ℝ) = 3 ^ 2 by norm_num, Real.log_pow,
    Real.log_pow] at h89
  push_cast at h89
  linarith

/-! ## 3. Rate distortion: the dual lower bound -/

/-- **The dual (Lagrangian) lower bound on the rate.**  `P` is a joint law of
`(X, X̂)` with marginal `p`; `q` its reproduction marginal. -/
theorem rd_dual_lower_bound {α β : Type*} [Fintype α] [Fintype β]
    (P : α → β → ℝ) (p : α → ℝ) (d : α → β → ℝ) (D s : ℝ) (μ : α → ℝ)
    (hP : ∀ x y, 0 ≤ P x y) (hp : ∀ x, ∑ y, P x y = p x)
    (hsum : ∑ x, p x = 1) (hD : ∑ x, ∑ y, P x y * d x y ≤ D) (hs : 0 ≤ s)
    (hμ : ∀ x, 0 < μ x)
    (hdual : ∀ y, ∑ x, p x * μ x * Real.exp (-s * d x y) ≤ 1) :
    ∑ x, p x * Real.log (μ x) - s * D ≤
      ∑ x, ∑ y, P x y * Real.log (P x y / (p x * ∑ x', P x' y)) := by
  set q : β → ℝ := fun y => ∑ x', P x' y with hq
  have hp0 : ∀ x, 0 ≤ p x := fun x => by rw [← hp x]; exact Finset.sum_nonneg fun y _ => hP x y
  have hq0 : ∀ y, 0 ≤ q y := fun y => Finset.sum_nonneg fun x _ => hP x y
  have Ple_p : ∀ x y, P x y ≤ p x := fun x y => by
    rw [← hp x]; exact Finset.single_le_sum (fun y _ => hP x y) (Finset.mem_univ y)
  have Ple_q : ∀ x y, P x y ≤ q y := fun x y =>
    Finset.single_le_sum (f := fun x' => P x' y) (fun x _ => hP x y) (Finset.mem_univ x)
  have key : ∀ x y, P x y * Real.log (μ x) - s * (P x y * d x y) + P x y
      - p x * q y * μ x * Real.exp (-s * d x y) ≤ P x y * Real.log (P x y / (p x * q y)) := by
    intro x y
    have hnn := mul_nonneg (mul_nonneg (mul_nonneg (hp0 x) (hq0 y)) (hμ x).le)
      (Real.exp_pos (-s * d x y)).le
    rcases (hP x y).eq_or_lt with h0 | hpos
    · rw [← h0]; simp only [zero_mul, mul_zero, zero_div]; linarith
    · have px : 0 < p x := lt_of_lt_of_le hpos (Ple_p x y)
      have qy : 0 < q y := lt_of_lt_of_le hpos (Ple_q x y)
      have pq : 0 < p x * q y := mul_pos px qy
      have A : 0 < μ x * Real.exp (-s * d x y) := mul_pos (hμ x) (Real.exp_pos _)
      set t := p x * q y * μ x * Real.exp (-s * d x y) / P x y with ht
      have tpos : 0 < t := by
        rw [ht, mul_assoc (p x * q y)]; exact div_pos (mul_pos pq A) hpos
      have h1 : Real.log (P x y / (p x * q y)) = Real.log (P x y) - Real.log (p x * q y) :=
        Real.log_div hpos.ne' pq.ne'
      have h2 : Real.log t = Real.log (p x * q y) + (Real.log (μ x) + -s * d x y)
          - Real.log (P x y) := by
        rw [ht, mul_assoc (p x * q y), Real.log_div (mul_pos pq A).ne' hpos.ne',
          Real.log_mul pq.ne' A.ne', Real.log_mul (hμ x).ne' (Real.exp_pos _).ne', Real.log_exp]
      have hlt := Real.log_le_sub_one_of_pos tpos
      have : P x y * t = p x * q y * μ x * Real.exp (-s * d x y) := by
        rw [ht]; field_simp
      rw [h1]
      nlinarith
  have S := Finset.sum_le_sum fun x (_ : x ∈ Finset.univ) =>
    Finset.sum_le_sum fun y (_ : y ∈ Finset.univ) => key x y
  simp only [Finset.sum_add_distrib, Finset.sum_sub_distrib] at S
  have e1 : ∑ x, ∑ y, P x y * Real.log (μ x) = ∑ x, p x * Real.log (μ x) := by
    refine Finset.sum_congr rfl fun x _ => ?_
    rw [← Finset.sum_mul, hp x]
  have e2 : ∑ x, ∑ y, s * (P x y * d x y) = s * ∑ x, ∑ y, P x y * d x y := by
    simp [Finset.mul_sum]
  have e3 : ∑ x, ∑ y, P x y = 1 := by simp [hp, hsum]
  have e4 : ∑ x, ∑ y, p x * q y * μ x * Real.exp (-s * d x y) ≤ 1 := by
    rw [Finset.sum_comm]
    calc ∑ y, ∑ x, p x * q y * μ x * Real.exp (-s * d x y)
        = ∑ y, q y * ∑ x, p x * μ x * Real.exp (-s * d x y) := by
          refine Finset.sum_congr rfl fun y _ => ?_
          rw [Finset.mul_sum]; exact Finset.sum_congr rfl fun x _ => by ring
      _ ≤ ∑ y, q y * 1 := Finset.sum_le_sum fun y _ => mul_le_mul_of_nonneg_left (hdual y) (hq0 y)
      _ = 1 := by simp only [mul_one, hq]; rw [Finset.sum_comm]; exact e3
  rw [e1, e2, e3] at S
  have : s * ∑ x, ∑ y, P x y * d x y ≤ s * D := mul_le_mul_of_nonneg_left hD hs
  linarith

/-! ## 4. Robin eigenvalues -/

/-- **A root in every interval**: for `h, L > 0` and `n ≥ 1`,
`k cos(kL) + h sin(kL) = 0` has a root with `(n - 1/2)π/L < k < nπ/L`. -/
theorem robin_root_exists {h L : ℝ} (hh : 0 < h) (hL : 0 < L) (n : ℕ)
    (hn : 1 ≤ n) :
    ∃ k, (n - 1/2) * π / L < k ∧ k < n * π / L ∧
      k * Real.cos (k * L) + h * Real.sin (k * L) = 0 := by
  set f : ℝ → ℝ := fun k => (-1) ^ n * (k * Real.cos (k * L) + h * Real.sin (k * L)) with hf
  set a := (n - 1/2) * π / L
  set b := n * π / L
  have hab : a < b := by
    simp only [a, b]; apply div_lt_div_of_pos_right _ hL; nlinarith [pi_pos]
  have ha : a * L = n * π - π / 2 := by simp only [a]; field_simp
  have hb : b * L = n * π := by simp only [b]; field_simp
  have hpow : ((-1:ℝ) ^ n) * (-1) ^ n = 1 := by rw [← mul_pow]; simp
  have fa : f a = -h := by
    simp only [hf, ha, Real.cos_sub_pi_div_two, Real.sin_sub_pi_div_two, Real.sin_nat_mul_pi,
      Real.cos_nat_mul_pi]
    linear_combination (-h) * hpow
  have bpos : 0 < b := by
    simp only [b]; have : (1:ℝ) ≤ n := by exact_mod_cast hn
    positivity
  have fb : f b = b := by
    simp only [hf, hb, Real.sin_nat_mul_pi, Real.cos_nat_mul_pi]
    linear_combination b * hpow
  have hc : ContinuousOn f (Set.Icc a b) := by
    apply Continuous.continuousOn; simp only [hf]; fun_prop
  have h0 : (0:ℝ) ∈ Set.Ioo (f a) (f b) := by rw [fa, fb]; exact ⟨by linarith, by linarith⟩
  obtain ⟨k, hk, hfk⟩ := intermediate_value_Ioo hab.le hc h0
  refine ⟨k, hk.1, hk.2, ?_⟩
  have : (-1:ℝ) ^ n ≠ 0 := by simp
  simp only [hf] at hfk
  exact (mul_eq_zero.mp hfk).resolve_left this

/-- **The eigenfunction**: at a root `k` of `k cos(kL) + h sin(kL) = 0`,
`y = sin(k x)` solves `y'' + k² y = 0`, `y(0) = 0` and `y'(L) + h y(L) = 0`. -/
theorem robin_eigenfunction {h L k : ℝ}
    (hk : k * Real.cos (k * L) + h * Real.sin (k * L) = 0) :
    (∀ x, deriv (deriv fun t => Real.sin (k * t)) x + k ^ 2 * Real.sin (k * x) = 0) ∧
      Real.sin (k * 0) = 0 ∧
      deriv (fun t => Real.sin (k * t)) L + h * Real.sin (k * L) = 0 := by
  have d1 : deriv (fun t => Real.sin (k * t)) = fun t => k * Real.cos (k * t) := by
    funext t
    have := ((hasDerivAt_id t).const_mul k).sin
    simpa [mul_comm] using this.deriv
  have d2 : deriv (fun t => k * Real.cos (k * t)) = fun t => -(k ^ 2 * Real.sin (k * t)) := by
    funext t
    have e := ((((hasDerivAt_id t).const_mul k).cos).const_mul k).deriv
    simp only [id] at e
    rw [e]; ring
  refine ⟨fun x => ?_, by simp, ?_⟩
  · rw [d1, d2]; ring
  · rw [d1]; linarith

end GLM.NonShannon
