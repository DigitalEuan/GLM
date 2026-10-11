module

public import Mathlib
public import RequestProject.GLM.NonShannon

/-!
# The copy lemma, and Zhang–Yeung for every distribution (Phase 119)

`studies/DERIVATION_FOUR_STUDY.md` takes the limits the third derivation study
left (`DERIVATION_THREE_STUDY.md` §6).  Its first item: Phase 118 proved the
Zhang–Yeung inequality *given* a copy variable (`zhang_yeung_of_copy`), and
named the copy lemma — that such a variable always exists — as not formalised.
This file formalises it.

Random variables are functions on a finite probability space `(Ω, p)`, and
the entropy of `f : Ω → β` is `entropyOf p f`, the grouping form
`-Σ_ω p(ω) log P(f = f ω)` (Phase 118).

* **Entropy sees only the partition** (`entropy_congr`): two variables that
  separate the same pairs of positive-probability outcomes have the same
  entropy.
* **Shannon's inequalities** (`condMI_nonneg`): `I(f; g | k) ≥ 0` for every
  three variables on every finite probability space; so the entropy function
  of any family of variables is a polymatroid (`entropicFn_shannon`).
* **The copy lemma** (`copy_lemma`): for every finite probability space and
  every variable `b`, there is a space `Ω × Ω` with two maps to `Ω` such that
  every variable read through either map has its old law's entropy, `b` reads
  the same through both, and anything read through the first map is
  conditionally independent of anything read through the second given `b`.
  The law is `p'(ω, ω') = p(ω) p(ω') [b ω = b ω'] / P(b = b ω)`.
* **Zhang–Yeung for every distribution** (`zhang_yeung_entropic`): the
  entropy function of any four random variables on any finite probability
  space satisfies the Zhang–Yeung inequality — Phase 118's certificate
  together with the copy lemma, with nothing left unproved.
-/

@[expose] public section

namespace GLM.CopyLemma

open GLM.DerivationsTwo GLM.NonShannon Real Finset

/-! ## 1. Fibres and the partition -/

section Basics

variable {Ω : Type*} [Fintype Ω]

/-- The probability of the fibre of `f` through `ω`: `P(f = f ω)`. -/
noncomputable def fib (p : Ω → ℝ) {β : Type*} [DecidableEq β] (f : Ω → β)
    (ω : Ω) : ℝ :=
  ∑ ω', if f ω' = f ω then p ω' else 0

lemma entropyOf_eq_fib (p : Ω → ℝ) {β : Type*} [DecidableEq β] (f : Ω → β) :
    entropyOf p f = -∑ ω, p ω * Real.log (fib p f ω) := rfl

lemma fib_nonneg {p : Ω → ℝ} (hp0 : ∀ ω, 0 ≤ p ω) {β : Type*} [DecidableEq β]
    (f : Ω → β) (ω : Ω) : 0 ≤ fib p f ω :=
  Finset.sum_nonneg fun ω' _ => ite_nonneg (hp0 ω') le_rfl

lemma le_fib {p : Ω → ℝ} (hp0 : ∀ ω, 0 ≤ p ω) {β : Type*} [DecidableEq β]
    (f : Ω → β) (ω : Ω) : p ω ≤ fib p f ω := by
  have := Finset.single_le_sum (f := fun ω' => if f ω' = f ω then p ω' else 0)
    (fun ω' _ => ite_nonneg (hp0 ω') le_rfl) (Finset.mem_univ ω)
  simpa using this

lemma fib_congr (p : Ω → ℝ) {β : Type*} [DecidableEq β] (f : Ω → β) {ω₁ ω₂ : Ω}
    (h : f ω₁ = f ω₂) : fib p f ω₁ = fib p f ω₂ := by
  simp only [fib, h]

/-- **Entropy sees only the partition of the positive-probability outcomes.** -/
theorem entropy_congr (p : Ω → ℝ) {β γ : Type*} [DecidableEq β] [DecidableEq γ]
    (f : Ω → β) (g : Ω → γ)
    (h : ∀ ω ω', p ω ≠ 0 → p ω' ≠ 0 → (f ω' = f ω ↔ g ω' = g ω)) :
    entropyOf p f = entropyOf p g := by
  simp only [entropyOf_eq_fib, fib]
  congr 1
  refine Finset.sum_congr rfl fun ω _ => ?_
  by_cases hω : p ω = 0
  · simp [hω]
  · congr 2
    refine Finset.sum_congr rfl fun ω' _ => ?_
    by_cases hω' : p ω' = 0
    · simp [hω']
    · simp only [h ω ω' hω hω']

/-- Conditional mutual information of three variables:
`I(f; g | k) = H(f,k) + H(g,k) - H(f,g,k) - H(k)`. -/
noncomputable def condMI (p : Ω → ℝ) {α β γ : Type*} [DecidableEq α]
    [DecidableEq β] [DecidableEq γ] (f : Ω → α) (g : Ω → β) (k : Ω → γ) : ℝ :=
  entropyOf p (fun ω => (f ω, k ω)) + entropyOf p (fun ω => (g ω, k ω)) -
    entropyOf p (fun ω => (f ω, g ω, k ω)) - entropyOf p k

/-- The key bound of Shannon's inequality: for fixed `ω₁, ω₂`, the outcomes
whose `(f, k)` is that of `ω₁` and whose `(g, k)` is that of `ω₂` form one
`(f, g, k)`-fibre, so the weighted count is at most `[k ω₂ = k ω₁] / P(k = k ω₁)`. -/
private lemma inner_bound {p : Ω → ℝ} (hp0 : ∀ ω, 0 ≤ p ω) {α β γ : Type*}
    [DecidableEq α] [DecidableEq β] [DecidableEq γ]
    (f : Ω → α) (g : Ω → β) (k : Ω → γ) (ω₁ ω₂ : Ω) :
    ∑ ω, (if (f ω₁, k ω₁) = (f ω, k ω) ∧ (g ω₂, k ω₂) = (g ω, k ω) then
        p ω / (fib p (fun ω => (f ω, g ω, k ω)) ω * fib p k ω) else 0) ≤
      (if k ω₂ = k ω₁ then 1 / fib p k ω₁ else 0) := by
  by_cases hex : ∃ ω0, (f ω₁, k ω₁) = (f ω0, k ω0) ∧ (g ω₂, k ω₂) = (g ω0, k ω0)
  · obtain ⟨ω0, h1, h2⟩ := hex
    simp only [Prod.mk.injEq] at h1 h2
    have hk : k ω₂ = k ω₁ := by rw [h2.2, h1.2]
    rw [if_pos hk]
    set c := fib p (fun ω => (f ω, g ω, k ω)) ω0 with hcdef
    set K := fib p k ω₁ with hKdef
    have step : ∀ ω, (if (f ω₁, k ω₁) = (f ω, k ω) ∧ (g ω₂, k ω₂) = (g ω, k ω) then
        p ω / (fib p (fun ω => (f ω, g ω, k ω)) ω * fib p k ω) else 0) =
        (if (f ω, g ω, k ω) = (f ω0, g ω0, k ω0) then p ω else 0) / (c * K) := by
      intro ω
      have hiff : ((f ω₁, k ω₁) = (f ω, k ω) ∧ (g ω₂, k ω₂) = (g ω, k ω)) ↔
          (f ω, g ω, k ω) = (f ω0, g ω0, k ω0) := by
        simp only [Prod.mk.injEq]
        constructor
        · rintro ⟨⟨a1, a2⟩, b1, b2⟩
          exact ⟨by rw [← a1, h1.1], by rw [← b1, h2.1], by rw [← a2, h1.2]⟩
        · rintro ⟨a1, b1, c1⟩
          exact ⟨⟨by rw [a1, h1.1], by rw [c1, h1.2]⟩, by rw [b1, h2.1], by rw [c1, h2.2]⟩
      by_cases hc : (f ω, g ω, k ω) = (f ω0, g ω0, k ω0)
      · rw [if_pos (hiff.mpr hc), if_pos hc]
        have e1 : fib p (fun ω => (f ω, g ω, k ω)) ω = c := fib_congr _ _ hc
        have e2 : fib p k ω = K := fib_congr _ _ (by
          have := ((hiff.mpr hc).1)
          simp only [Prod.mk.injEq] at this
          exact this.2.symm)
        rw [e1, e2]
      · rw [if_neg (mt hiff.mp hc), if_neg hc, zero_div]
    rw [Finset.sum_congr rfl fun ω _ => step ω, ← Finset.sum_div]
    change c / (c * K) ≤ 1 / K
    rcases (fib_nonneg hp0 (fun ω => (f ω, g ω, k ω)) ω0).eq_or_lt with hc0 | hcpos
    · rw [← hcdef] at hc0
      rw [← hc0, zero_div]
      exact div_nonneg zero_le_one (fib_nonneg hp0 k ω₁)
    · rw [← hcdef] at hcpos
      rw [← div_div, div_self hcpos.ne']
  · push_neg at hex
    rw [Finset.sum_eq_zero fun ω _ => if_neg (fun h => hex ω h.1 h.2)]
    split_ifs
    · exact div_nonneg zero_le_one (fib_nonneg hp0 k ω₁)
    · exact le_rfl

/-- **Shannon's inequality**: `I(f; g | k) ≥ 0` on every finite probability
space. -/
theorem condMI_nonneg {p : Ω → ℝ} (hp0 : ∀ ω, 0 ≤ p ω) (hp1 : ∑ ω, p ω = 1)
    {α β γ : Type*} [DecidableEq α] [DecidableEq β] [DecidableEq γ]
    (f : Ω → α) (g : Ω → β) (k : Ω → γ) : 0 ≤ condMI p f g k := by
  set A := fib p (fun ω => (f ω, k ω)) with hA
  set B := fib p (fun ω => (g ω, k ω)) with hB
  set C := fib p (fun ω => (f ω, g ω, k ω)) with hC
  set K := fib p k with hK
  have hval : condMI p f g k =
      ∑ ω, p ω * (Real.log (C ω) + Real.log (K ω) - Real.log (A ω) - Real.log (B ω)) := by
    simp only [condMI, entropyOf_eq_fib, hA, hB, hC, hK, mul_add, mul_sub,
      Finset.sum_add_distrib, Finset.sum_sub_distrib]
    ring
  have hterm : ∀ ω, p ω - p ω * (A ω * B ω / (C ω * K ω)) ≤
      p ω * (Real.log (C ω) + Real.log (K ω) - Real.log (A ω) - Real.log (B ω)) := by
    intro ω
    rcases (hp0 ω).eq_or_lt with h0 | hpos
    · rw [← h0]; simp
    · have pA : 0 < A ω := lt_of_lt_of_le hpos (le_fib hp0 _ ω)
      have pB : 0 < B ω := lt_of_lt_of_le hpos (le_fib hp0 _ ω)
      have pC : 0 < C ω := lt_of_lt_of_le hpos (le_fib hp0 _ ω)
      have pK : 0 < K ω := lt_of_lt_of_le hpos (le_fib hp0 _ ω)
      have hx : 0 < C ω * K ω / (A ω * B ω) := by positivity
      have hl := Real.one_sub_inv_le_log_of_pos hx
      rw [inv_div, Real.log_div (by positivity) (by positivity),
        Real.log_mul pC.ne' pK.ne', Real.log_mul pA.ne' pB.ne'] at hl
      have := mul_le_mul_of_nonneg_left hl hpos.le
      linarith [this]
  have hexpand : ∀ ω, p ω * (A ω * B ω / (C ω * K ω)) =
      ∑ ω₁, ∑ ω₂, p ω₁ * p ω₂ *
        (if (f ω₁, k ω₁) = (f ω, k ω) ∧ (g ω₂, k ω₂) = (g ω, k ω) then
          p ω / (C ω * K ω) else 0) := by
    intro ω
    simp only [hA, hB, fib]
    rw [Finset.sum_mul_sum, Finset.sum_div, Finset.mul_sum]
    refine Finset.sum_congr rfl fun ω₁ _ => ?_
    rw [Finset.sum_div, Finset.mul_sum]
    refine Finset.sum_congr rfl fun ω₂ _ => ?_
    by_cases h1 : (f ω₁, k ω₁) = (f ω, k ω) <;> by_cases h2 : (g ω₂, k ω₂) = (g ω, k ω) <;>
      simp [h1, h2]
    ring
  have hS : ∑ ω, p ω * (A ω * B ω / (C ω * K ω)) ≤ 1 := by
    rw [Finset.sum_congr rfl fun ω _ => hexpand ω, Finset.sum_comm]
    calc ∑ ω₁, ∑ ω, ∑ ω₂, p ω₁ * p ω₂ *
          (if (f ω₁, k ω₁) = (f ω, k ω) ∧ (g ω₂, k ω₂) = (g ω, k ω) then
            p ω / (C ω * K ω) else 0)
        = ∑ ω₁, ∑ ω₂, p ω₁ * p ω₂ * ∑ ω,
          (if (f ω₁, k ω₁) = (f ω, k ω) ∧ (g ω₂, k ω₂) = (g ω, k ω) then
            p ω / (C ω * K ω) else 0) := by
          refine Finset.sum_congr rfl fun ω₁ _ => ?_
          rw [Finset.sum_comm]
          exact Finset.sum_congr rfl fun ω₂ _ => by rw [Finset.mul_sum]
      _ ≤ ∑ ω₁, ∑ ω₂, p ω₁ * p ω₂ * (if k ω₂ = k ω₁ then 1 / K ω₁ else 0) := by
          refine Finset.sum_le_sum fun ω₁ _ => Finset.sum_le_sum fun ω₂ _ => ?_
          exact mul_le_mul_of_nonneg_left (inner_bound hp0 f g k ω₁ ω₂)
            (mul_nonneg (hp0 ω₁) (hp0 ω₂))
      _ = ∑ ω₁, p ω₁ * (K ω₁ * (1 / K ω₁)) := by
          refine Finset.sum_congr rfl fun ω₁ _ => ?_
          simp only [hK, fib, Finset.sum_mul, Finset.mul_sum]
          refine Finset.sum_congr rfl fun ω₂ _ => ?_
          split_ifs <;> ring
      _ ≤ ∑ ω₁, p ω₁ := by
          refine Finset.sum_le_sum fun ω₁ _ => ?_
          rcases (fib_nonneg hp0 k ω₁).eq_or_lt with h0 | hpos
          · rw [hK, ← h0]; simp [hp0 ω₁]
          · rw [hK, mul_one_div_cancel hpos.ne', mul_one]
      _ = 1 := hp1
  have := Finset.sum_le_sum fun ω (_ : ω ∈ Finset.univ) => hterm ω
  rw [Finset.sum_sub_distrib, hp1] at this
  rw [hval]
  linarith

end Basics

/-! ## 2. The entropy function of a family of variables -/

section SetFn

variable {Ω : Type*} [Fintype Ω] {ι V : Type*} [DecidableEq ι] [DecidableEq V]

/-- The entropy function of a family of variables: `S ↦ H(X_i : i ∈ S)`. -/
noncomputable def entropicFn (p : Ω → ℝ) (X : ι → Ω → V) (S : Finset ι) : ℝ :=
  entropyOf p (fun ω (i : S) => X i ω)

omit [Fintype Ω] [DecidableEq ι] [DecidableEq V] in
lemma restrict_eq_iff (X : ι → Ω → V) (S : Finset ι) (ω ω' : Ω) :
    ((fun i : S => X i ω') = fun i : S => X i ω) ↔ ∀ i ∈ S, X i ω' = X i ω := by
  simp [funext_iff]

/-- **The entropy function of any family of random variables is a polymatroid**:
every Shannon inequality `I(A; B | C) ≥ 0` holds. -/
theorem entropicFn_shannon {p : Ω → ℝ} (hp0 : ∀ ω, 0 ≤ p ω) (hp1 : ∑ ω, p ω = 1)
    (X : ι → Ω → V) (A B C : Finset ι) : 0 ≤ cmi (entropicFn p X) A B C := by
  have h := condMI_nonneg hp0 hp1 (fun ω (i : A) => X i ω) (fun ω (i : B) => X i ω)
    (fun ω (i : C) => X i ω)
  unfold condMI at h
  unfold cmi entropicFn
  have e1 := entropy_congr p (fun ω (i : ↥(A ∪ C)) => X i ω)
    (fun ω => ((fun i : A => X i ω), (fun i : C => X i ω))) (fun ω ω' _ _ => by
      simp only [restrict_eq_iff, Prod.mk.injEq, Finset.mem_union, or_imp, forall_and])
  have e2 := entropy_congr p (fun ω (i : ↥(B ∪ C)) => X i ω)
    (fun ω => ((fun i : B => X i ω), (fun i : C => X i ω))) (fun ω ω' _ _ => by
      simp only [restrict_eq_iff, Prod.mk.injEq, Finset.mem_union, or_imp, forall_and])
  have e3 := entropy_congr p (fun ω (i : ↥(A ∪ B ∪ C)) => X i ω)
    (fun ω => ((fun i : A => X i ω), (fun i : B => X i ω), (fun i : C => X i ω)))
    (fun ω ω' _ _ => by
      simp only [restrict_eq_iff, Prod.mk.injEq, Finset.mem_union, or_imp, forall_and, and_assoc])
  rw [e1, e2, e3]
  exact h

end SetFn

/-! ## 3. The copy lemma -/

section Copy

variable {Ω : Type*} [Fintype Ω]

/-- **Entropy is unchanged by relabelling the sample space.** -/
lemma entropyOf_equiv {Ω' : Type*} [Fintype Ω'] (e : Ω' ≃ Ω) (q : Ω → ℝ)
    {β : Type*} [DecidableEq β] (f : Ω → β) :
    entropyOf (q ∘ e) (f ∘ e) = entropyOf q f := by
  simp only [entropyOf_eq_fib, fib, Function.comp]
  congr 1
  rw [← Equiv.sum_comp e]
  refine Finset.sum_congr rfl fun ω _ => ?_
  congr 2
  exact Equiv.sum_comp e (fun ω' => if f ω' = f (e ω) then q ω' else 0)

/-- Sums against a law on a product, of a function of the first coordinate,
are sums against its first marginal. -/
lemma sum_fst {Ω' : Type*} [Fintype Ω'] (q : Ω × Ω' → ℝ) (p : Ω → ℝ)
    (hq : ∀ ω, ∑ ω', q (ω, ω') = p ω) (F : Ω → ℝ) :
    ∑ z, q z * F z.1 = ∑ ω, p ω * F ω := by
  rw [Fintype.sum_prod_type]
  refine Finset.sum_congr rfl fun ω _ => ?_
  rw [← hq ω, Finset.sum_mul]

/-- **Marginals keep their entropy**: on a law with first marginal `p`, a
variable read through the first coordinate has its entropy under `p`. -/
lemma entropy_fst {Ω' : Type*} [Fintype Ω'] (q : Ω × Ω' → ℝ) (p : Ω → ℝ)
    (hq : ∀ ω, ∑ ω', q (ω, ω') = p ω) {β : Type*} [DecidableEq β] (g : Ω → β) :
    entropyOf q (fun z => g z.1) = entropyOf p g := by
  have hfib : ∀ z : Ω × Ω', fib q (fun z => g z.1) z = fib p g z.1 := by
    intro z
    simp only [fib]
    rw [Fintype.sum_prod_type]
    refine Finset.sum_congr rfl fun η _ => ?_
    rw [← hq η]
    split_ifs <;> simp
  simp only [entropyOf_eq_fib, hfib]
  rw [sum_fst q p hq (fun ω => Real.log (fib p g ω))]

lemma entropy_snd {Ω' : Type*} [Fintype Ω'] (q : Ω' × Ω → ℝ) (p : Ω → ℝ)
    (hq : ∀ ω, ∑ ω', q (ω', ω) = p ω) {β : Type*} [DecidableEq β] (g : Ω → β) :
    entropyOf q (fun z => g z.2) = entropyOf p g := by
  have := entropyOf_equiv (Equiv.prodComm Ω Ω') q (fun z : Ω' × Ω => g z.2)
  rw [← this]
  exact entropy_fst (q ∘ Equiv.prodComm Ω Ω') p hq g

/-- **The copy law** of `p` over `b`:
`p'(ω, ω') = p(ω) p(ω') [b ω' = b ω] / P(b = b ω)`. -/
noncomputable def copyLaw (p : Ω → ℝ) {β : Type*} [DecidableEq β] (b : Ω → β)
    (z : Ω × Ω) : ℝ :=
  if b z.2 = b z.1 then p z.1 * p z.2 / fib p b z.1 else 0

variable {p : Ω → ℝ} {β : Type*} [DecidableEq β] {b : Ω → β}

lemma copyLaw_nonneg (hp0 : ∀ ω, 0 ≤ p ω) (z : Ω × Ω) : 0 ≤ copyLaw p b z := by
  unfold copyLaw
  split_ifs
  · exact div_nonneg (mul_nonneg (hp0 _) (hp0 _)) (fib_nonneg hp0 _ _)
  · exact le_rfl

lemma copyLaw_swap (z : Ω × Ω) : copyLaw p b z.swap = copyLaw p b z := by
  unfold copyLaw
  simp only [Prod.fst_swap, Prod.snd_swap]
  by_cases h : b z.2 = b z.1
  · rw [if_pos h.symm, if_pos h, fib_congr p b h, mul_comm]
  · rw [if_neg (Ne.symm h), if_neg h]

lemma copyLaw_marg (hp0 : ∀ ω, 0 ≤ p ω) (ω : Ω) : ∑ ω', copyLaw p b (ω, ω') = p ω := by
  unfold copyLaw
  have : ∑ ω', (if b ω' = b ω then p ω * p ω' / fib p b ω else 0) =
      p ω / fib p b ω * fib p b ω := by
    rw [fib, Finset.mul_sum]
    refine Finset.sum_congr rfl fun ω' _ => ?_
    split_ifs <;> ring
  simp only
  rw [this]
  rcases (fib_nonneg hp0 b ω).eq_or_lt with h0 | hpos
  · have : p ω = 0 := le_antisymm (h0 ▸ le_fib hp0 b ω) (hp0 ω)
    rw [← h0, this]; simp
  · exact div_mul_cancel₀ _ hpos.ne'

lemma copyLaw_marg_snd (hp0 : ∀ ω, 0 ≤ p ω) (ω : Ω) :
    ∑ ω', copyLaw p b (ω', ω) = p ω := by
  rw [← copyLaw_marg (b := b) hp0 ω]
  refine Finset.sum_congr rfl fun ω' _ => ?_
  exact copyLaw_swap (p := p) (b := b) (ω, ω')

lemma copyLaw_sum (hp0 : ∀ ω, 0 ≤ p ω) (hp1 : ∑ ω, p ω = 1) :
    ∑ z, copyLaw p b z = 1 := by
  rw [Fintype.sum_prod_type]
  simp only [copyLaw_marg hp0]
  exact hp1

lemma copyLaw_support {z : Ω × Ω} (h : copyLaw p b z ≠ 0) :
    b z.2 = b z.1 ∧ p z.1 ≠ 0 ∧ p z.2 ≠ 0 := by
  unfold copyLaw at h
  split_ifs at h with hb
  · refine ⟨hb, fun h1 => h (by simp [h1]), fun h2 => h (by simp [h2])⟩
  · exact absurd rfl h

/-- A variable read through the first copy keeps its entropy. -/
theorem copy_fst (hp0 : ∀ ω, 0 ≤ p ω) {γ : Type*} [DecidableEq γ] (g : Ω → γ) :
    entropyOf (copyLaw p b) (fun z => g z.1) = entropyOf p g :=
  entropy_fst _ p (copyLaw_marg hp0) g

/-- A variable read through the second copy keeps its entropy. -/
theorem copy_snd (hp0 : ∀ ω, 0 ≤ p ω) {γ : Type*} [DecidableEq γ] (g : Ω → γ) :
    entropyOf (copyLaw p b) (fun z => g z.2) = entropyOf p g :=
  entropy_snd _ p (copyLaw_marg_snd hp0) g

/-- The fibre of `(w ∘ snd, u ∘ fst, b ∘ fst)` at a point of the support
factorises: `P(u, b) P(w, b) / P(b)`. -/
private lemma copy_fib {α δ : Type*} [DecidableEq α] [DecidableEq δ] (u : Ω → α)
    (w : Ω → δ) {z : Ω × Ω} (hz : b z.2 = b z.1) :
    fib (copyLaw p b) (fun z => (w z.2, u z.1, b z.1)) z =
      fib p (fun ω => (u ω, b ω)) z.1 * fib p (fun ω => (w ω, b ω)) z.2 /
        fib p b z.1 := by
  obtain ⟨ω, ω'⟩ := z
  simp only at hz ⊢
  simp only [fib]
  rw [Finset.sum_mul_sum, Finset.sum_div, Fintype.sum_prod_type]
  refine Finset.sum_congr rfl fun η _ => ?_
  rw [Finset.sum_div]
  refine Finset.sum_congr rfl fun η' _ => ?_
  unfold copyLaw
  simp only [Prod.mk.injEq]
  by_cases h1 : u η = u ω ∧ b η = b ω
  · by_cases h2 : w η' = w ω'
    · have hf : fib p b η = fib p b ω := fib_congr p b h1.2
      by_cases h3 : b η' = b η
      · rw [if_pos ⟨h2, h1.1, h1.2⟩, if_pos h3, if_pos h1, if_pos ⟨h2, by rw [h3, h1.2, hz]⟩,
          hf]
        rfl
      · rw [if_pos ⟨h2, h1.1, h1.2⟩, if_neg h3, if_pos h1,
          if_neg (fun h => h3 (by rw [h.2, hz, h1.2]))]
        ring
    · simp [h2]
  · rw [if_neg (fun h => h1 ⟨h.2.1, h.2.2⟩), if_neg h1]
    ring

/-- **The copy is conditionally independent of the original given `b`**:
`I(w ∘ snd; u ∘ fst | b ∘ fst) = 0` for every `u, w`. -/
theorem copy_condMI_zero (hp0 : ∀ ω, 0 ≤ p ω) {α δ : Type*} [DecidableEq α]
    [DecidableEq δ] (u : Ω → α) (w : Ω → δ) :
    condMI (copyLaw p b) (fun z => w z.2) (fun z => u z.1) (fun z => b z.1) = 0 := by
  unfold condMI
  have e1 : entropyOf (copyLaw p b) (fun z => (w z.2, b z.1)) =
      entropyOf p (fun ω => (w ω, b ω)) := by
    rw [← copy_snd (b := b) hp0 (fun ω => (w ω, b ω))]
    refine entropy_congr _ _ _ fun z z' hz hz' => ?_
    have a := (copyLaw_support hz).1
    have a' := (copyLaw_support hz').1
    simp only [Prod.mk.injEq, a, a']
  have e2 : entropyOf (copyLaw p b) (fun z => (u z.1, b z.1)) =
      entropyOf p (fun ω => (u ω, b ω)) := copy_fst hp0 (fun ω => (u ω, b ω))
  have e3 : entropyOf (copyLaw p b) (fun z => b z.1) = entropyOf p b := copy_fst hp0 b
  have e4 : entropyOf (copyLaw p b) (fun z => (w z.2, u z.1, b z.1)) =
      entropyOf p (fun ω => (u ω, b ω)) + entropyOf p (fun ω => (w ω, b ω)) -
        entropyOf p b := by
    have hpt : ∀ z, copyLaw p b z * Real.log (fib (copyLaw p b)
        (fun z => (w z.2, u z.1, b z.1)) z) =
        copyLaw p b z * Real.log (fib p (fun ω => (u ω, b ω)) z.1) +
        copyLaw p b z * Real.log (fib p (fun ω => (w ω, b ω)) z.2) -
        copyLaw p b z * Real.log (fib p b z.1) := by
      intro z
      by_cases hz : copyLaw p b z = 0
      · simp [hz]
      · obtain ⟨hb, h1, h2⟩ := copyLaw_support hz
        have q1 : 0 < fib p (fun ω => (u ω, b ω)) z.1 :=
          lt_of_lt_of_le (lt_of_le_of_ne (hp0 _) (Ne.symm h1)) (le_fib hp0 _ _)
        have q2 : 0 < fib p (fun ω => (w ω, b ω)) z.2 :=
          lt_of_lt_of_le (lt_of_le_of_ne (hp0 _) (Ne.symm h2)) (le_fib hp0 _ _)
        have q3 : 0 < fib p b z.1 :=
          lt_of_lt_of_le (lt_of_le_of_ne (hp0 _) (Ne.symm h1)) (le_fib hp0 _ _)
        rw [copy_fib u w hb, Real.log_div (by positivity) q3.ne',
          Real.log_mul q1.ne' q2.ne']
        ring
    simp only [entropyOf_eq_fib, hpt, Finset.sum_add_distrib, Finset.sum_sub_distrib]
    rw [sum_fst (copyLaw p b) p (copyLaw_marg hp0)
        (fun ω => Real.log (fib p (fun ω => (u ω, b ω)) ω)),
      sum_fst (copyLaw p b) p (copyLaw_marg hp0) (fun ω => Real.log (fib p b ω))]
    have hs : ∑ z, copyLaw p b z * Real.log (fib p (fun ω => (w ω, b ω)) z.2) =
        ∑ ω, p ω * Real.log (fib p (fun ω => (w ω, b ω)) ω) := by
      rw [Fintype.sum_prod_type, Finset.sum_comm]
      refine Finset.sum_congr rfl fun ω' _ => ?_
      rw [← copyLaw_marg_snd (b := b) hp0 ω', Finset.sum_mul]
    rw [hs]
    ring
  rw [e1, e2, e3, e4]
  ring

/-- **The copy lemma.**  For every finite probability space `(Ω, p)` and every
variable `b`, there is a finite probability space `(Ω', p')` with two maps
`π₁, π₂ : Ω' → Ω` such that every variable read through either map keeps its
entropy, `b` reads the same through both on every outcome of positive
probability, and whatever is read through `π₂` is conditionally independent
of whatever is read through `π₁` given `b ∘ π₁`. -/
theorem copy_lemma (hp0 : ∀ ω, 0 ≤ p ω) (hp1 : ∑ ω, p ω = 1) (b : Ω → β) :
    ∃ (Ω' : Type u_1) (_ : Fintype Ω') (p' : Ω' → ℝ) (π₁ π₂ : Ω' → Ω),
      (∀ z, 0 ≤ p' z) ∧ ∑ z, p' z = 1 ∧
      (∀ {γ : Type u_1} [DecidableEq γ] (g : Ω → γ),
        entropyOf p' (g ∘ π₁) = entropyOf p g ∧ entropyOf p' (g ∘ π₂) = entropyOf p g) ∧
      (∀ z, p' z ≠ 0 → b (π₂ z) = b (π₁ z)) ∧
      (∀ {α δ : Type u_1} [DecidableEq α] [DecidableEq δ] (u : Ω → α) (w : Ω → δ),
        condMI p' (w ∘ π₂) (u ∘ π₁) (b ∘ π₁) = 0) :=
  ⟨Ω × Ω, inferInstance, copyLaw p b, Prod.fst, Prod.snd, copyLaw_nonneg hp0,
    copyLaw_sum hp0 hp1, fun g => ⟨copy_fst hp0 g, copy_snd hp0 g⟩,
    fun _ hz => (copyLaw_support hz).1, fun u w => copy_condMI_zero hp0 u w⟩

end Copy

/-! ## 4. Zhang–Yeung for every distribution -/

section ZY

variable {Ω : Type*} [Fintype Ω] {V : Type*} [DecidableEq V]

/-- The five variables on the copy space: `A, B, C, D` read through the first
copy, and `R = C` read through the second. -/
def copyVars (X : Fin 4 → Ω → V) : Fin 5 → Ω × Ω → V :=
  fun i z => if h : (i : ℕ) < 4 then X ⟨i, h⟩ z.1 else X 2 z.2

omit [Fintype Ω] [DecidableEq V] in
lemma copyVars_castSucc (X : Fin 4 → Ω → V) (i : Fin 4) (z : Ω × Ω) :
    copyVars X (Fin.castSucc i) z = X i z.1 := by
  simp [copyVars]

omit [Fintype Ω] [DecidableEq V] in
lemma copyVars_four (X : Fin 4 → Ω → V) (z : Ω × Ω) : copyVars X 4 z = X 2 z.2 := by
  simp [copyVars]

omit [Fintype Ω] [DecidableEq V] in
lemma copyVars_lt (X : Fin 4 → Ω → V) (z : Ω × Ω) :
    copyVars X 0 z = X 0 z.1 ∧ copyVars X 1 z = X 1 z.1 ∧ copyVars X 2 z = X 2 z.1 ∧
      copyVars X 3 z = X 3 z.1 :=
  ⟨copyVars_castSucc X 0 z, copyVars_castSucc X 1 z, copyVars_castSucc X 2 z,
    copyVars_castSucc X 3 z⟩

/-- **The Zhang–Yeung inequality holds for every distribution** of four
random variables on a finite probability space: Phase 118's copy certificate
(`zhang_yeung_of_copy`) applied to the copy law of `p` over `(A, D)`. -/
theorem zhang_yeung_entropic {p : Ω → ℝ} (hp0 : ∀ ω, 0 ≤ p ω) (hp1 : ∑ ω, p ω = 1)
    (X : Fin 4 → Ω → V) : ZhangYeung (entropicFn p X) := by
  set b : Ω → V × V := fun ω => (X 0 ω, X 3 ω) with hb
  set q := copyLaw p b with hq
  set h5 := entropicFn q (copyVars X) with hh5
  have q0 : ∀ z, 0 ≤ q z := copyLaw_nonneg hp0
  have q1 : ∑ z, q z = 1 := copyLaw_sum hp0 hp1
  have hsh : ∀ A B C, 0 ≤ cmi h5 A B C := entropicFn_shannon q0 q1 (copyVars X)
  have ev := copyVars_lt X
  have e4 := copyVars_four X
  have supp : ∀ z, q z ≠ 0 → X 0 z.2 = X 0 z.1 ∧ X 3 z.2 = X 3 z.1 := fun z hz => by
    have := (copyLaw_support hz).1
    simpa [hb] using this
  -- the copy conditions
  have c1 : h5 {4} = h5 {2} := by
    have l : h5 {4} = entropyOf p (X 2) := by
      rw [← copy_snd (b := b) hp0 (X 2)]
      exact entropy_congr _ _ _ fun z z' _ _ => by
        simp [restrict_eq_iff, e4]
    have r : h5 {2} = entropyOf p (X 2) := by
      rw [← copy_fst (b := b) hp0 (X 2)]
      exact entropy_congr _ _ _ fun z z' _ _ => by
        simp [restrict_eq_iff, (ev _).2.2.1]
    rw [l, r]
  have c2 : h5 {3, 4} = h5 {2, 3} := by
    have l : h5 {3, 4} = entropyOf p (fun ω => (X 2 ω, X 3 ω)) := by
      rw [← copy_snd (b := b) hp0 (fun ω => (X 2 ω, X 3 ω))]
      exact entropy_congr _ _ _ fun z z' hz hz' => by
        simp only [restrict_eq_iff, Finset.mem_insert, Finset.mem_singleton,
          forall_eq_or_imp, forall_eq, e4, (ev _).2.2.2, (supp z hz).2, (supp z' hz').2,
          Prod.mk.injEq]
        tauto
    have r : h5 {2, 3} = entropyOf p (fun ω => (X 2 ω, X 3 ω)) := by
      rw [← copy_fst (b := b) hp0 (fun ω => (X 2 ω, X 3 ω))]
      exact entropy_congr _ _ _ fun z z' _ _ => by
        simp only [restrict_eq_iff, Finset.mem_insert, Finset.mem_singleton,
          forall_eq_or_imp, forall_eq, (ev _).2.2.1, (ev _).2.2.2, Prod.mk.injEq]
    rw [l, r]
  have c3 : h5 {0, 4} = h5 {0, 2} := by
    have l : h5 {0, 4} = entropyOf p (fun ω => (X 0 ω, X 2 ω)) := by
      rw [← copy_snd (b := b) hp0 (fun ω => (X 0 ω, X 2 ω))]
      exact entropy_congr _ _ _ fun z z' hz hz' => by
        simp only [restrict_eq_iff, Finset.mem_insert, Finset.mem_singleton,
          forall_eq_or_imp, forall_eq, e4, (ev _).1, (supp z hz).1, (supp z' hz').1,
          Prod.mk.injEq]
    have r : h5 {0, 2} = entropyOf p (fun ω => (X 0 ω, X 2 ω)) := by
      rw [← copy_fst (b := b) hp0 (fun ω => (X 0 ω, X 2 ω))]
      exact entropy_congr _ _ _ fun z z' _ _ => by
        simp only [restrict_eq_iff, Finset.mem_insert, Finset.mem_singleton,
          forall_eq_or_imp, forall_eq, (ev _).1, (ev _).2.2.1, Prod.mk.injEq]
    rw [l, r]
  have c4 : h5 {0, 3, 4} = h5 {0, 2, 3} := by
    have l : h5 {0, 3, 4} = entropyOf p (fun ω => (X 0 ω, X 2 ω, X 3 ω)) := by
      rw [← copy_snd (b := b) hp0 (fun ω => (X 0 ω, X 2 ω, X 3 ω))]
      exact entropy_congr _ _ _ fun z z' hz hz' => by
        simp only [restrict_eq_iff, Finset.mem_insert, Finset.mem_singleton,
          forall_eq_or_imp, forall_eq, e4, (ev _).1, (ev _).2.2.2, (supp z hz).1,
          (supp z' hz').1, (supp z hz).2, (supp z' hz').2, Prod.mk.injEq]
        tauto
    have r : h5 {0, 2, 3} = entropyOf p (fun ω => (X 0 ω, X 2 ω, X 3 ω)) := by
      rw [← copy_fst (b := b) hp0 (fun ω => (X 0 ω, X 2 ω, X 3 ω))]
      exact entropy_congr _ _ _ fun z z' _ _ => by
        simp only [restrict_eq_iff, Finset.mem_insert, Finset.mem_singleton,
          forall_eq_or_imp, forall_eq, (ev _).1, (ev _).2.2.1, (ev _).2.2.2,
          Prod.mk.injEq]
    rw [l, r]
  have ci : cmi h5 {4} {1, 2} {0, 3} = 0 := by
    have z0 := copy_condMI_zero (b := b) hp0 (fun ω => (X 1 ω, X 2 ω)) (X 2)
    unfold condMI at z0
    unfold cmi
    have f1 : h5 ({4} ∪ {0, 3}) = entropyOf q (fun z => (X 2 z.2, b z.1)) :=
      entropy_congr _ _ _ fun z z' _ _ => by
        simp only [restrict_eq_iff, Finset.mem_union, Finset.mem_insert,
          Finset.mem_singleton, or_imp, forall_and, forall_eq, e4,
          (ev _).1, (ev _).2.2.2, hb, Prod.mk.injEq]
    have f2 : h5 ({1, 2} ∪ {0, 3}) =
        entropyOf q (fun z => ((X 1 z.1, X 2 z.1), b z.1)) :=
      entropy_congr _ _ _ fun z z' _ _ => by
        simp only [restrict_eq_iff, Finset.mem_union, Finset.mem_insert,
          Finset.mem_singleton, or_imp, forall_and, forall_eq,
          (ev _).1, (ev _).2.1, (ev _).2.2.1, (ev _).2.2.2, hb, Prod.mk.injEq]
    have f3 : h5 ({4} ∪ {1, 2} ∪ {0, 3}) =
        entropyOf q (fun z => (X 2 z.2, (X 1 z.1, X 2 z.1), b z.1)) :=
      entropy_congr _ _ _ fun z z' _ _ => by
        simp only [restrict_eq_iff, Finset.mem_union, Finset.mem_insert,
          Finset.mem_singleton, or_imp, forall_and, forall_eq, e4,
          (ev _).1, (ev _).2.1, (ev _).2.2.1, (ev _).2.2.2, hb, Prod.mk.injEq]
        tauto
    have f4 : h5 {0, 3} = entropyOf q (fun z => b z.1) :=
      entropy_congr _ _ _ fun z z' _ _ => by
        simp only [restrict_eq_iff, Finset.mem_insert, Finset.mem_singleton,
          forall_eq_or_imp, forall_eq, (ev _).1, (ev _).2.2.2, hb, Prod.mk.injEq]
    rw [f1, f2, f3, f4]
    exact z0
  have key := zhang_yeung_of_copy h5 hsh c1 c2 c3 c4 ci
  -- back to the four original variables
  have tr : ∀ S : Finset (Fin 4), h5 (S.map Fin.castSuccEmb) = entropicFn p X S := by
    intro S
    rw [hh5, entropicFn, entropicFn, ← copy_fst (b := b) hp0 (fun ω (i : S) => X i ω)]
    exact entropy_congr _ _ _ fun z z' _ _ => by
      simp only [restrict_eq_iff, Finset.mem_map, Fin.castSuccEmb_apply,
        forall_exists_index, and_imp, forall_apply_eq_imp_iff₂, copyVars_castSucc]
  have trc : ∀ A B C : Finset (Fin 4), cmi h5 (A.map Fin.castSuccEmb)
      (B.map Fin.castSuccEmb) (C.map Fin.castSuccEmb) = cmi (entropicFn p X) A B C := by
    intro A B C
    simp only [cmi, ← Finset.map_union, tr]
  have k1 : cmi h5 {2} {3} ∅ = cmi (entropicFn p X) {2} {3} ∅ := by
    rw [← trc]; rfl
  have k2 : cmi h5 {0} {1} ∅ = cmi (entropicFn p X) {0} {1} ∅ := by
    rw [← trc]; rfl
  have k3 : cmi h5 {0} {2, 3} ∅ = cmi (entropicFn p X) {0} {2, 3} ∅ := by
    rw [← trc]; rfl
  have k4 : cmi h5 {2} {3} {0} = cmi (entropicFn p X) {2} {3} {0} := by
    rw [← trc]; rfl
  have k5 : cmi h5 {2} {3} {1} = cmi (entropicFn p X) {2} {3} {1} := by
    rw [← trc]; rfl
  unfold ZhangYeung
  rw [← k1, ← k2, ← k3, ← k4, ← k5]
  exact key

end ZY

end GLM.CopyLemma
