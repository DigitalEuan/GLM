/-
# Past the Griess layer: an infinite-dimensional vertex algebra, and why it has to be

`VOA.lean` builds the state–field map `Y(u, z) = ∑ₙ uₙ z^{-n-1}` on the
three-dimensional `2A` Sakuma algebra, keeps the one mode the Griess product
supplies, and then proves that this is as far as a finite-dimensional model
reaches: `borcherds_commutator_fails` exhibits an axis triple on which
Borcherds' commutator formula, with every other mode discarded, is false.  That
file closes by saying that the modes the truncation throws away are
load-bearing, that reinstating them leaves the finite-dimensional setting, and
that the infinite-dimensional half is *not built there*.

This file builds it.

## What is built

The Fock space of one free boson — the rank-one Heisenberg vertex algebra —
over the exact rationals:

* `V = MvPolynomial ℕ ℚ`, polynomials in `x₀, x₁, x₂, …`.  The variable `xᵢ`
  is the state created by the mode `a_{-(i+1)}`, so `V` is spanned by
  `a_{-n₁} a_{-n₂} ⋯ vac` exactly as a Fock space should be.
* `create i` — multiplication by `xᵢ`, the creation operator `a_{-(i+1)}`.
* `annihilate i` — `(i+1) ∂/∂xᵢ`, the annihilation operator `a_{i+1}`.
* `a k` — the `k`-th mode for every `k : ℤ`, positive, negative or zero,
  assembled from the two families.  This is the field `Y(α, z) = ∑ aₖ z^{-k-1}`
  of the weight-one generator `α = a₋₁ vac`.

## What is proved

* `mode_commutator` — **the Heisenberg relation** `⁅aₘ, aₙ⁆ = m δ_{m+n,0} · id`,
  for all integers `m, n` at once.  This is the commutator formula the Griess
  layer could not satisfy, and here it is an identity of operators rather than
  a hope.
* `mode_truncated` — every state is annihilated by all sufficiently high modes,
  so `Y(α, z) v` is a genuine formal Laurent series: the field is *truncated*,
  which is the axiom that makes the infinite sum meaningful.
* `borcherds_commutator` — the same bracket written in Borcherds' own form,
  `⁅aₘ, aₙ⁆ = ∑_{i ≥ 0} C(m, i) (aᵢ α)_{m+n-i}`, with the generalised binomial
  coefficient `intChoose` and the state–field map `Yfield`.  The sum is finite
  because `alpha_mode_eq_zero_of_two_le` kills every term past the first two —
  that is the state-truncation axiom, not a convenience, and
  `borcherds_tail_vanishes` records it.
* `no_finite_dimensional_model` — **the obstruction, proved in general.**  In
  characteristic zero no pair of endomorphisms of a nonzero finite-dimensional
  space can satisfy `⁅A, B⁆ = c · id` with `c ≠ 0`: the trace of a commutator
  is `0` and the trace of `c · id` is `c · dim`.  So the relation
  `⁅a₁, a₋₁⁆ = id` cannot be modelled on any finite-dimensional space at all.
* `fock_infinite_dimensional` — hence `V` itself is infinite-dimensional, and
  `griess_layer_discards_nonzero_modes` names specific discarded modes that do
  the damage: `a₂` and `a₋₂` are nonzero and their bracket is `2 · id`, while
  the Griess-layer truncation of `VOA.lean` sets both to zero.

Taken with `VOA.lean` the pair says something exact.  The finite layer carries
real structure — a Frobenius algebra, an invariant form that is forced rather
than chosen — and *cannot* carry the commutator formula.  The infinite layer
carries the commutator formula, and by `no_finite_dimensional_model` nothing
finite-dimensional ever could.  The infinite-dimensional half of the bridge is
therefore necessary rather than traditional, and it is built here rather than
asserted.

What is still not built is the Monster.  This is the rank-one Heisenberg
algebra, not the Moonshine module, and the Griess algebra of `Sakuma.lean` is
not reconstructed inside it.  That is said here so that nothing is implicitly
claimed.
-/
import Mathlib

namespace GLM.Heisenberg

open MvPolynomial Finset

/-! ## 1.  The Fock space and its operators -/

/-- The Fock space of one free boson over the exact rationals: polynomials in
`x₀, x₁, x₂, …`, where `xᵢ` is the state `a_{-(i+1)} vac`. -/
abbrev V : Type := MvPolynomial ℕ ℚ

/-- `∂/∂xᵢ` as a plain linear map. -/
noncomputable def D (i : ℕ) : V →ₗ[ℚ] V :=
  (pderiv i : Derivation ℚ V V).toLinearMap

@[simp] theorem D_apply (i : ℕ) (f : V) : D i f = pderiv i f := rfl

/-- The creation operator `a_{-(i+1)}`: multiplication by `xᵢ`. -/
noncomputable def create (i : ℕ) : V →ₗ[ℚ] V := LinearMap.mulLeft ℚ (X i)

@[simp] theorem create_apply (i : ℕ) (f : V) : create i f = X i * f := rfl

/-- The annihilation operator `a_{i+1} = (i+1) ∂/∂xᵢ`. -/
noncomputable def annihilate (i : ℕ) : V →ₗ[ℚ] V := ((i : ℚ) + 1) • D i

@[simp] theorem annihilate_apply (i : ℕ) (f : V) :
    annihilate i f = ((i : ℚ) + 1) • pderiv i f := rfl

/-- The `k`-th mode of the weight-one generator, for every integer `k`:
creation below zero, annihilation above it, and zero momentum at `k = 0`. -/
noncomputable def a (k : ℤ) : V →ₗ[ℚ] V :=
  if 0 < k then annihilate (k.toNat - 1)
  else if k < 0 then create ((-k).toNat - 1)
  else 0

@[simp] theorem a_zero : a 0 = 0 := by simp [a]

theorem a_pos (i : ℕ) : a (i + 1 : ℤ) = annihilate i := by
  have h : (0 : ℤ) < (i : ℤ) + 1 := by positivity
  have h2 : ((i : ℤ) + 1).toNat - 1 = i := by omega
  simp only [a, if_pos h, h2]

theorem a_neg (i : ℕ) : a (-(i + 1 : ℤ)) = create i := by
  have h : ¬ (0 : ℤ) < -((i : ℤ) + 1) := by omega
  have h' : -((i : ℤ) + 1) < 0 := by omega
  have h2 : (-(-((i : ℤ) + 1))).toNat - 1 = i := by omega
  simp only [a, if_neg h, if_pos h', h2]

/-- Every positive mode index is `i + 1` for a natural `i`. -/
theorem exists_succ_of_pos {k : ℤ} (hk : 0 < k) : ∃ i : ℕ, k = (i : ℤ) + 1 :=
  ⟨k.toNat - 1, by omega⟩

/-- Every negative mode index is `-(i + 1)` for a natural `i`. -/
theorem exists_neg_succ_of_neg {k : ℤ} (hk : k < 0) :
    ∃ i : ℕ, k = -((i : ℤ) + 1) :=
  ⟨(-k).toNat - 1, by omega⟩

/-! ## 2.  The three brackets -/

/-- A commutator, evaluated at a state. -/
theorem lie_apply (A B : V →ₗ[ℚ] V) (f : V) : ⁅A, B⁆ f = A (B f) - B (A f) := by
  simp [Ring.lie_def]

/-- Partial derivatives commute. -/
theorem pderiv_comm (i j : ℕ) (f : V) :
    (pderiv i) ((pderiv j) f) = (pderiv j) ((pderiv i) f) := by
  classical
  induction f using MvPolynomial.induction_on with
  | C a => simp
  | add p q hp hq => simp [hp, hq]
  | mul_X p k hp =>
      simp only [pderiv_mul, pderiv_X, map_add, hp]
      by_cases h1 : i = k <;> by_cases h2 : j = k <;>
        simp [h1, h2, Pi.single_apply, add_comm]

/-- Creation operators commute with each other: the Fock space is a commutative
ring and they are multiplications. -/
theorem lie_create_create_apply (i j : ℕ) (f : V) :
    ⁅create i, create j⁆ f = 0 := by
  rw [lie_apply]
  simp
  ring

/-- Annihilation operators commute with each other. -/
theorem lie_annihilate_annihilate_apply (i j : ℕ) (f : V) :
    ⁅annihilate i, annihilate j⁆ f = 0 := by
  rw [lie_apply]
  simp only [annihilate_apply, map_smul, smul_smul]
  rw [pderiv_comm i j f]
  ring_nf

/-- The one bracket that is not zero: `[(i+1) ∂/∂xᵢ, xⱼ ·] = (i+1) δᵢⱼ`. -/
theorem lie_annihilate_create_apply (i j : ℕ) (f : V) :
    ⁅annihilate i, create j⁆ f
      = (if i = j then ((i : ℚ) + 1) else 0) • f := by
  rw [lie_apply]
  simp only [annihilate_apply, create_apply]
  rw [pderiv_mul]
  by_cases h : i = j
  · subst h
    simp [smul_add]
  · simp [pderiv_X_of_ne (Ne.symm h), h]

/-! ## 3.  The Heisenberg relation -/

/-- **The commutator formula, on all of `ℤ`.**  `⁅aₘ, aₙ⁆ = m δ_{m+n,0} id`:
the modes of the field `Y(α, z)` close into the Heisenberg algebra with central
term `1`.  This is the identity the Griess layer of `VOA.lean` could not
satisfy. -/
theorem mode_commutator (m n : ℤ) :
    ⁅a m, a n⁆ = (if m + n = 0 then (m : ℚ) else 0) • LinearMap.id := by
  refine LinearMap.ext fun f => ?_
  rw [LinearMap.smul_apply, LinearMap.id_apply]
  -- one mixed case is the whole content; everything else vanishes on both sides
  have key : ∀ p q : ℤ, 0 < p → q < 0 →
      ⁅a p, a q⁆ f = (if p + q = 0 then (p : ℚ) else 0) • f := by
    intro p q hp hq
    obtain ⟨i, rfl⟩ := exists_succ_of_pos hp
    obtain ⟨j, rfl⟩ := exists_neg_succ_of_neg hq
    rw [a_pos, a_neg, lie_annihilate_create_apply]
    by_cases h : i = j
    · subst h
      have hz : ((i : ℤ) + 1) + -((i : ℤ) + 1) = 0 := by omega
      rw [if_pos rfl, if_pos hz]
      push_cast
      ring_nf
    · have hsum : ¬ (((i : ℤ) + 1) + -((j : ℤ) + 1) = 0) := by
        intro hc
        exact h (by omega)
      rw [if_neg h, if_neg hsum]
  rcases lt_trichotomy m 0 with hm | hm | hm
  · rcases lt_trichotomy n 0 with hn | hn | hn
    · obtain ⟨i, rfl⟩ := exists_neg_succ_of_neg hm
      obtain ⟨j, rfl⟩ := exists_neg_succ_of_neg hn
      have hsum : ¬ (-((i : ℤ) + 1) + -((j : ℤ) + 1) = 0) := by omega
      rw [a_neg, a_neg, lie_create_create_apply, if_neg hsum, zero_smul]
    · subst hn
      have hz : ¬ (m + 0 = 0) := by omega
      rw [a_zero, if_neg hz, zero_smul]
      simp
    · have h := key n m hn hm
      have hsk : ⁅a m, a n⁆ = -⁅a n, a m⁆ := by rw [← lie_skew (a n) (a m), neg_neg]
      rw [hsk, LinearMap.neg_apply, h]
      by_cases hs : n + m = 0
      · have hs' : m + n = 0 := by omega
        have hmn : (m : ℚ) = -(n : ℚ) := by
          have hmn' : m = -n := by omega
          exact_mod_cast congrArg (fun z : ℤ => (z : ℚ)) hmn'
        rw [if_pos hs, if_pos hs', hmn, neg_smul]
      · have hs' : ¬ (m + n = 0) := by omega
        rw [if_neg hs, if_neg hs', zero_smul, neg_zero]
  · subst hm
    rw [a_zero]
    by_cases hn : (0 : ℤ) + n = 0
    · rw [if_pos hn]
      simp
    · rw [if_neg hn]
      simp
  · rcases lt_trichotomy n 0 with hn | hn | hn
    · exact key m n hm hn
    · subst hn
      have hz : ¬ (m + 0 = 0) := by omega
      rw [a_zero, if_neg hz, zero_smul]
      simp
    · obtain ⟨i, rfl⟩ := exists_succ_of_pos hm
      obtain ⟨j, rfl⟩ := exists_succ_of_pos hn
      have hsum : ¬ (((i : ℤ) + 1) + ((j : ℤ) + 1) = 0) := by omega
      rw [a_pos, a_pos, lie_annihilate_annihilate_apply, if_neg hsum, zero_smul]

/-- The central term is genuinely there: `⁅a₁, a₋₁⁆ = id`. -/
theorem lie_a_one_a_neg_one : ⁅a 1, a (-1)⁆ = LinearMap.id := by
  have h := mode_commutator 1 (-1)
  simpa using h

/-! ## 4.  Truncation: the field really is a formal Laurent series -/

/-- Every state is killed by all high enough modes, so `Y(α, z) f` has only
finitely many positive-power coefficients. -/
theorem mode_truncated (f : V) :
    ∃ N : ℕ, ∀ k : ℤ, (N : ℤ) ≤ k → a k f = 0 := by
  classical
  refine ⟨f.vars.sup id + 2, fun k hk => ?_⟩
  have hkpos : 0 < k := by
    have h0 : (0 : ℤ) ≤ ((f.vars.sup id : ℕ) : ℤ) := Int.natCast_nonneg _
    push_cast at hk
    omega
  obtain ⟨i, rfl⟩ := exists_succ_of_pos hkpos
  have hi : f.vars.sup id < i := by push_cast at hk; omega
  have hnot : i ∉ f.vars := by
    intro hmem
    have hle : id i ≤ f.vars.sup id := Finset.le_sup hmem
    simp only [id] at hle
    omega
  rw [a_pos]
  simp [pderiv_eq_zero_of_notMem_vars hnot]

/-! ## 5.  The obstruction: no finite-dimensional model, ever -/

/-- **In characteristic zero the Heisenberg relation has no finite-dimensional
model.**  If `W` is a nonzero finite-dimensional `ℚ`-space then no two
endomorphisms of it satisfy `⁅A, B⁆ = c · id` with `c ≠ 0`, because the trace of
a commutator is `0` while the trace of `c · id` is `c · dim W`.

This is what makes the infinite-dimensional half of the bridge *necessary*.
`VOA.lean` shows one finite algebra failing the commutator formula; this shows
that every finite one must. -/
theorem no_finite_dimensional_model {W : Type} [AddCommGroup W] [Module ℚ W]
    [FiniteDimensional ℚ W] [Nontrivial W] (A B : W →ₗ[ℚ] W) {c : ℚ}
    (hc : c ≠ 0) : ⁅A, B⁆ ≠ c • LinearMap.id := by
  intro h
  have ht : LinearMap.trace ℚ W ⁅A, B⁆ = 0 := by
    simp [Ring.lie_def, map_sub, LinearMap.trace_mul_comm]
  rw [h, map_smul, LinearMap.trace_id] at ht
  have hr : 0 < Module.finrank ℚ W := Module.finrank_pos
  have hne : (Module.finrank ℚ W : ℚ) ≠ 0 := by positivity
  simp [hc, hne] at ht

/-- Hence the Fock space is infinite-dimensional.  It is not a modelling
choice: `⁅a₁, a₋₁⁆ = id`, and no finite-dimensional space admits that. -/
theorem fock_infinite_dimensional : ¬ FiniteDimensional ℚ V := by
  intro hfin
  exact no_finite_dimensional_model (a 1) (a (-1)) (c := 1) one_ne_zero
    (by simpa using lie_a_one_a_neg_one)

/-- The modes the Griess-layer truncation of `VOA.lean` discards are not zero
operators, and they do not commute. -/
theorem griess_layer_discards_nonzero_modes :
    a 2 ≠ 0 ∧ a (-2) ≠ 0 ∧ ⁅a 2, a (-2)⁆ = (2 : ℚ) • LinearMap.id := by
  refine ⟨?_, ?_, ?_⟩
  · intro h
    have hz : a 2 (X 1) = 0 := by rw [h]; simp
    rw [show (2 : ℤ) = ((1 : ℕ) : ℤ) + 1 by norm_num, a_pos] at hz
    simp at hz
  · intro h
    have hz : a (-2) 1 = 0 := by rw [h]; simp
    rw [show (-2 : ℤ) = -(((1 : ℕ) : ℤ) + 1) by norm_num, a_neg] at hz
    simp only [create_apply, mul_one] at hz
    exact (X_ne_zero (R := ℚ) (1 : ℕ)) hz
  · have h := mode_commutator 2 (-2)
    norm_num at h
    exact h

/-! ## 6.  Borcherds' commutator formula, in its own form -/

/-- The vacuum. -/
noncomputable def vac : V := 1

/-- The weight-one generator `α = a₋₁ vac`. -/
noncomputable def alpha : V := X 0

/-- The modes of the vacuum: `Y(vac, z) = id`, so `(vac)ₖ = δ_{k,-1} id`. -/
noncomputable def vacMode (k : ℤ) : V →ₗ[ℚ] V :=
  if k = -1 then LinearMap.id else 0

/-- The state–field map on the span of the vacuum and the generator, which is
where Borcherds' formula for `⁅aₘ, aₙ⁆` lives.  The coefficients are read off
the state itself, so this is a total function of the state. -/
noncomputable def Yfield (u : V) (k : ℤ) : V →ₗ[ℚ] V :=
  (coeff 0 u) • vacMode k + (coeff (Finsupp.single 0 1) u) • a k

@[simp] theorem Yfield_zero_state (k : ℤ) : Yfield 0 k = 0 := by
  simp [Yfield]

@[simp] theorem Yfield_vac (k : ℤ) : Yfield vac k = vacMode k := by
  have h1 : coeff 0 (vac : V) = 1 := by simp [vac]
  have h2 : coeff (Finsupp.single 0 1) (vac : V) = 0 := by
    rw [vac, coeff_one]
    simp [Ne.symm (Finsupp.single_ne_zero.mpr one_ne_zero)]
  simp [Yfield, h1, h2]

@[simp] theorem Yfield_alpha (k : ℤ) : Yfield alpha k = a k := by
  have h1 : coeff 0 (alpha : V) = 0 := by
    rw [alpha, coeff_X']
    simp [Finsupp.single_ne_zero.mpr one_ne_zero]
  have h2 : coeff (Finsupp.single 0 1) (alpha : V) = 1 := by simp [alpha]
  simp [Yfield, h1, h2]

/-- The generalised binomial coefficient `C(m, i)` for an integer `m`, which is
what Borcherds' formula uses: `∏_{j < i} (m - j) / i!`. -/
noncomputable def intChoose (m : ℤ) (i : ℕ) : ℚ :=
  (∏ j ∈ range i, ((m : ℚ) - j)) / (i.factorial : ℚ)

@[simp] theorem intChoose_zero (m : ℤ) : intChoose m 0 = 1 := by
  simp [intChoose]

@[simp] theorem intChoose_one (m : ℤ) : intChoose m 1 = (m : ℚ) := by
  simp [intChoose]

/-- `a₀ α = 0`: the zero mode has no momentum. -/
@[simp] theorem alpha_mode_zero : a 0 alpha = 0 := by simp

/-- `a₁ α = vac`: the one nonzero non-negative mode of `α` on itself, and the
reason the central term of the Heisenberg relation is exactly `1`. -/
@[simp] theorem alpha_mode_one : a 1 alpha = vac := by
  rw [show (1 : ℤ) = ((0 : ℕ) : ℤ) + 1 by norm_num, a_pos]
  simp [alpha, vac]

/-- Every mode past the first kills `α`, so Borcherds' sum is finite: this is
the state-truncation axiom, not a convenience. -/
theorem alpha_mode_eq_zero_of_two_le {i : ℕ} (hi : 2 ≤ i) :
    a (i : ℤ) alpha = 0 := by
  obtain ⟨j, rfl⟩ : ∃ j : ℕ, i = j + 1 := ⟨i - 1, by omega⟩
  have hj : (0 : ℕ) ≠ j := by omega
  push_cast
  rw [a_pos]
  simp [alpha, pderiv_X_of_ne hj]

/-- **Borcherds' commutator formula holds here.**

`⁅aₘ, aₙ⁆ = ∑_{i ≥ 0} C(m, i) (aᵢ α)_{m+n-i}`, the identity that
`VOA.lean`'s `borcherds_commutator_fails` shows the Griess layer violating.
The sum runs over `i < 2` because `alpha_mode_eq_zero_of_two_le` makes every
later term zero, so this is the whole of the right-hand side. -/
theorem borcherds_commutator (m n : ℤ) :
    ⁅a m, a n⁆
      = ∑ i ∈ range 2, intChoose m i • Yfield (a (i : ℤ) alpha) (m + n - i) := by
  rw [Finset.sum_range_succ, Finset.sum_range_one]
  norm_num
  rw [mode_commutator, vacMode]
  by_cases h : m + n = 0
  · have h' : m + n - 1 = -1 := by omega
    rw [if_pos h, if_pos h']
  · have h' : ¬ (m + n - 1 = -1) := by omega
    rw [if_neg h, if_neg h']
    simp

/-- The terms `borcherds_commutator` leaves out are zero, so nothing was swept
under the range. -/
theorem borcherds_tail_vanishes {i : ℕ} (hi : 2 ≤ i) (m : ℤ) (k : ℤ) :
    intChoose m i • Yfield (a (i : ℤ) alpha) k = 0 := by
  rw [alpha_mode_eq_zero_of_two_le hi]
  simp

end GLM.Heisenberg
