module

public import Mathlib
public import RequestProject.GLM.FrobeniusRadicals

/-!
# Roots with no expression in radicals, in composite degree

`studies/PRIMITIVE_RADICAL_STUDY.md` (Phase 114) carries the radical-free
statement of `solve symbolically` past prime degree.  Phase 113's certificate
(`GLM.FrobeniusRadicals.no_radical_root_of_frobenius_shape`) rests on
Galois's theorem for groups of prime degree, where transitivity already gives
primitivity.  In composite degree a transitive group can be imprimitive and
solvable while holding a transposition (the wreath products), so a second
element is needed to make the group primitive first.

## What is proved here

* `isPreprimitive_of_isCycle_fixing_one`: a transitive permutation group
  holding a single cycle that moves every point but one is primitive.  (A
  block through the fixed point is carried to itself by every power of the
  cycle, and those powers reach every other point.)
* `not_solvable_of_long_cycle_of_swap_or_three_cycle`: if the Galois group of
  an irreducible polynomial over `ℚ` of degree `n ≥ 5` holds such an
  `(n - 1)`-cycle and a transposition or a 3-cycle, it is not solvable
  (Jordan's theorem, from Mathlib, applied to the primitive group).
* `no_radical_root_of_primitive_pattern` — **the certificate the layer
  cites**: the same conclusion for roots, with the two elements given by
  their cycle types — one of type `(n - 1, 1)`, one with exactly one cycle of
  length `ℓ ∈ {2, 3}` and every other cycle length prime to `ℓ`, which has a
  power that is a transposition or a 3-cycle
  (`GLM.FrobeniusRadicals.exists_pow_cycleType_singleton`).

## What is not proved here

As in Phase 113, the layer reads the two elements off factorisations of the
polynomial modulo primes, through Dedekind's theorem, which is not proved in
Lean; the factorisations are decided by the Python side.  The test is
sufficient and not necessary.  `PGL(2, 5)` acting on the six points of the
projective line over `𝔽₅` is isomorphic to `S₅`, so not solvable, yet it holds
no element with a power that is a transposition or a 3-cycle (a primitive
group of degree 6 holding one would contain `A₆`, of order 360 > 120); for a
sextic with that group the layer stays silent.
-/

@[expose] public section

namespace GLM.PrimitiveRadicals

open Equiv Equiv.Perm Polynomial Polynomial.Gal MulAction
open scoped Pointwise

attribute [local instance] splits_ℚ_ℂ

/-! ### §1.  Primitivity from one long cycle -/

/-- A transitive permutation group holding a cycle that moves every point but
one is primitive. -/
theorem isPreprimitive_of_isCycle_fixing_one {α : Type*} [Fintype α] [DecidableEq α]
    (H : Subgroup (Perm α)) [IsPretransitive H α] {σ : Perm α} (hσH : σ ∈ H)
    (hσ : σ.IsCycle) (hcard : σ.support.card + 1 = Fintype.card α) :
    IsPreprimitive H α := by
  classical
  -- the one point the cycle fixes
  have hlt : σ.support.card < Fintype.card α := by omega
  obtain ⟨a, ha⟩ : ∃ a, a ∉ σ.support := by
    by_contra h
    push_neg at h
    have : σ.support = Finset.univ := Finset.eq_univ_of_forall h
    rw [this, Finset.card_univ] at hlt
    exact lt_irrefl _ hlt
  have hsupp : ∀ b, b ≠ a → b ∈ σ.support := by
    intro b hb
    by_contra hb'
    have hsub : σ.support ⊆ Finset.univ.erase a ∩ Finset.univ.erase b := by
      intro x hx
      simp only [Finset.mem_inter, Finset.mem_erase, Finset.mem_univ, and_true]
      exact ⟨fun h => ha (h ▸ hx), fun h => hb' (h ▸ hx)⟩
    have hc := Finset.card_le_card hsub
    have : (Finset.univ.erase a ∩ Finset.univ.erase b).card = Fintype.card α - 2 := by
      rw [show Finset.univ.erase a ∩ Finset.univ.erase b = (Finset.univ.erase a).erase b by
        ext x; simp [and_comm]]
      rw [Finset.card_erase_of_mem (by simp [hb]), Finset.card_erase_of_mem (Finset.mem_univ _),
        Finset.card_univ]
      omega
    have h2 : 2 ≤ Fintype.card α := by
      have := Finset.card_le_univ ({a, b} : Finset α)
      rwa [Finset.card_pair hb.symm] at this
    omega
  refine IsPreprimitive.of_isTrivialBlock_base a ?_
  intro B haB hB
  by_cases hsub : B.Subsingleton
  · exact Or.inl hsub
  right
  obtain ⟨b, hbB, hba⟩ : ∃ b ∈ B, b ≠ a := by
    by_contra h
    push_neg at h
    exact hsub (fun x hx y hy => (h x hx).trans (h y hy).symm)
  ext c
  simp only [Set.mem_univ, iff_true]
  by_cases hca : c = a
  · exact hca ▸ haB
  obtain ⟨k, hk⟩ := hσ.sameCycle (Perm.mem_support.mp (hsupp b hba))
    (Perm.mem_support.mp (hsupp c hca))
  have hkH : σ ^ k ∈ H := H.zpow_mem hσH k
  have hfix : (σ ^ k) a = a := by
    rw [Perm.notMem_support] at ha
    exact Perm.zpow_apply_eq_self_of_apply_eq_self ha k
  have hBB : (⟨σ ^ k, hkH⟩ : H) • B = B :=
    hB.smul_eq_of_mem haB (by
      change (σ ^ k) a ∈ B
      rw [hfix]; exact haB)
  rw [← hBB, ← hk]
  exact Set.smul_mem_smul_set (a := (⟨σ ^ k, hkH⟩ : H)) hbB

/-! ### §2.  Jordan, for a Galois group of any degree -/

/-- If the Galois group of an irreducible polynomial over `ℚ` of degree at
least 5 holds an element acting on the complex roots as a cycle moving all but
one of them, and an element acting as a transposition or a 3-cycle, it is not
solvable. -/
theorem not_solvable_of_long_cycle_of_swap_or_three_cycle {p : ℚ[X]} (p_irr : Irreducible p)
    (p_five : 5 ≤ p.natDegree) (τ σ : p.Gal)
    (hτ : (galActionHom p ℂ τ).IsCycle)
    (hτcard : (galActionHom p ℂ τ).support.card + 1 = p.natDegree)
    (hσ : IsSwap (galActionHom p ℂ σ) ∨ IsThreeCycle (galActionHom p ℂ σ)) :
    ¬ IsSolvable p.Gal := by
  classical
  intro hsolv
  set H := (galActionHom p ℂ).range with hH
  have hHsolv : IsSolvable H :=
    solvable_of_surjective (galActionHom p ℂ).rangeRestrict_surjective
  have hcard := GLM.FrobeniusRadicals.card_complex_roots p_irr
  haveI : MulAction.IsPretransitive H (p.rootSet ℂ) := by
    have := galAction_isPretransitive p ℂ p_irr
    refine ⟨fun x y => ?_⟩
    obtain ⟨g, hg⟩ := MulAction.exists_smul_eq p.Gal x y
    exact ⟨⟨galActionHom p ℂ g, g, rfl⟩, hg⟩
  have hprim : MulAction.IsPreprimitive H (p.rootSet ℂ) :=
    isPreprimitive_of_isCycle_fixing_one H ⟨τ, rfl⟩ hτ (by rw [hcard]; exact hτcard)
  have hmem : galActionHom p ℂ σ ∈ H := ⟨σ, rfl⟩
  have hA : alternatingGroup (p.rootSet ℂ) ≤ H := by
    rcases hσ with h | h
    · rw [subgroup_eq_top_of_isPreprimitive_of_isSwap_mem hprim _ h hmem]; exact le_top
    · exact alternatingGroup_le_of_isPreprimitive_of_isThreeCycle_mem hprim h hmem
  exact GLM.FrobeniusRadicals.not_solvable_of_alternating_le (by rw [hcard]; exact p_five) hA
    hHsolv

/-! ### §3.  The certificate, in cycle types -/

/-- **The certificate for any degree.**  Let `p` be irreducible over `ℚ` of
degree `n ≥ 5`, and suppose its Galois group holds an element of cycle type
`(n - 1, 1)` on the complex roots, and an element whose cycle type has exactly
one cycle of length `ℓ`, where `ℓ` is 2 or 3, and every other cycle of length
prime to `ℓ`.  Then no root of `p` is solvable by radicals.  (The layer reads
the two elements off factorisations of `p` modulo primes, through Dedekind's
theorem, which is not proved here.) -/
theorem no_radical_root_of_primitive_pattern {p : ℚ[X]} (p_irr : Irreducible p)
    (p_five : 5 ≤ p.natDegree) (τ σ : p.Gal)
    (hτ : (galActionHom p ℂ τ).cycleType = {p.natDegree - 1}) {ℓ : ℕ}
    (hℓ : ℓ = 2 ∨ ℓ = 3)
    (hcount : (galActionHom p ℂ σ).cycleType.count ℓ = 1)
    (hrest : ∀ k ∈ (galActionHom p ℂ σ).cycleType, k ≠ ℓ → ¬ ℓ ∣ k)
    (x : ℂ) (hx : aeval x p = 0) : ¬ IsSolvableByRad ℚ x := by
  classical
  have hτcyc : (galActionHom p ℂ τ).IsCycle := by
    rw [← Equiv.Perm.card_cycleType_eq_one, hτ, Multiset.card_singleton]
  have hτcard : (galActionHom p ℂ τ).support.card + 1 = p.natDegree := by
    rw [← Equiv.Perm.sum_cycleType, hτ, Multiset.sum_singleton]
    omega
  have hℓp : ℓ.Prime := by rcases hℓ with rfl | rfl <;> norm_num
  obtain ⟨n, hn⟩ := GLM.FrobeniusRadicals.exists_pow_cycleType_singleton hℓp hcount hrest
  rw [← map_pow] at hn
  have hσ' : IsSwap (galActionHom p ℂ (σ ^ n)) ∨ IsThreeCycle (galActionHom p ℂ (σ ^ n)) := by
    rcases hℓ with rfl | rfl
    · left
      rw [← Equiv.Perm.card_support_eq_two, ← sum_cycleType, hn]
      rfl
    · right
      exact hn
  exact mt (solvableByRad.isSolvable' p_irr hx)
    (not_solvable_of_long_cycle_of_swap_or_three_cycle p_irr p_five τ (σ ^ n) hτcyc hτcard hσ')

end GLM.PrimitiveRadicals
