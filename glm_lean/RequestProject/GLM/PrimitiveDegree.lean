module

public import Mathlib
public import RequestProject.GLM.PrimitiveRadicals

/-!
# Primitive groups of degree not a prime power are not solvable

`studies/PRIMITIVE_DEGREE_STUDY.md` (Phase 116) takes the limit Phase 114
left: Phase 114's certificate
(`GLM.PrimitiveRadicals.no_radical_root_of_primitive_pattern`) needs a second
Frobenius element with a power that is a transposition or a 3-cycle, so a
sextic whose group is `PGL(2, 5)` acting on six points (isomorphic to `S₅`)
stays silent.

The classical fact that removes the second element in most composite degrees
is Galois's: a solvable primitive permutation group has prime-power degree.
So in a degree that is not a prime power (6, 10, 12, 14, 15, …) primitivity
alone rules solvability out, and Phase 114 already proves primitivity from one
element of cycle type `(n - 1, 1)`.

## What is proved here

* `exists_normal_comm_ne_bot`: a nontrivial solvable group has a nontrivial
  normal abelian subgroup (the last nontrivial term of its derived series).
* `exists_normal_pGroup_ne_bot`: a nontrivial finite solvable group has a
  nontrivial normal `p`-subgroup (the Sylow `p`-subgroup of that abelian
  subgroup, which is characteristic in it).
* `card_dvd_of_normal_ne_bot`: in a primitive permutation group a nontrivial
  normal subgroup is transitive, so its order is a multiple of the degree.
* `isPrimePow_card_of_isPreprimitive_of_isSolvable` — **Galois's theorem**,
  the half needed: a solvable primitive permutation group on at least two
  points has prime-power degree.
* `not_solvable_of_long_cycle_of_not_isPrimePow`: the Galois group of an
  irreducible polynomial over `ℚ` whose degree is not a prime power, holding
  an element of cycle type `(n - 1, 1)` on the complex roots, is not solvable.
* `no_radical_root_of_long_cycle_of_not_isPrimePow` — **the certificate the
  layer cites**: under the same hypotheses no root is expressible in radicals.

## What is not proved here

As in Phases 113 to 115, the layer reads the element off a factorisation of
the polynomial modulo a prime through Dedekind's theorem, which is not proved
in Lean, and the factorisation is decided by the Python side.  In prime-power
degree (8, 9, 16, …) the affine groups are solvable, primitive and hold
`(n - 1, 1)` elements, so the certificate rightly does not apply there and the
layer keeps Phase 114's two-element test.
-/

@[expose] public section

namespace GLM.PrimitiveDegree

open Equiv Equiv.Perm Polynomial Polynomial.Gal MulAction

attribute [local instance] splits_ℚ_ℂ

/-! ### §1.  A nontrivial normal `p`-subgroup in a solvable group -/

/-- A nontrivial solvable group has a nontrivial normal abelian subgroup: the
last nontrivial term of its derived series. -/
theorem exists_normal_comm_ne_bot {G : Type*} [Group G] [IsSolvable G] [Nontrivial G] :
    ∃ A : Subgroup G, A.Normal ∧ A ≠ ⊥ ∧ ∀ x ∈ A, ∀ y ∈ A, x * y = y * x := by
  classical
  have hex : ∃ n, derivedSeries G n = ⊥ := (isSolvable_def G).1 inferInstance
  have hn0spec : derivedSeries G (Nat.find hex) = ⊥ := Nat.find_spec hex
  have hn0ne : Nat.find hex ≠ 0 := by
    intro h
    rw [h, derivedSeries_zero] at hn0spec
    exact top_ne_bot hn0spec
  obtain ⟨m, hm⟩ : ∃ m, Nat.find hex = m + 1 := ⟨Nat.find hex - 1, by omega⟩
  refine ⟨derivedSeries G m, derivedSeries_normal G m, Nat.find_min hex (by omega), ?_⟩
  intro x hx y hy
  have hc : ⁅x, y⁆ ∈ derivedSeries G (m + 1) := by
    rw [derivedSeries_succ]
    exact Subgroup.commutator_mem_commutator hx hy
  rwa [← hm, hn0spec, Subgroup.mem_bot, commutatorElement_eq_one_iff_mul_comm] at hc

/-- A nontrivial finite solvable group has a nontrivial normal `p`-subgroup
for some prime `p`. -/
theorem exists_normal_pGroup_ne_bot {G : Type*} [Group G] [Finite G] [IsSolvable G]
    [Nontrivial G] :
    ∃ (p : ℕ) (K : Subgroup G), p.Prime ∧ K.Normal ∧ K ≠ ⊥ ∧ IsPGroup p K := by
  classical
  obtain ⟨A, hAn, hA, hcomm⟩ := exists_normal_comm_ne_bot (G := G)
  have hcard : Nat.card A ≠ 1 := by
    rw [Ne, Subgroup.card_eq_one]; exact hA
  obtain ⟨p, hp, hpd⟩ := Nat.exists_prime_and_dvd hcard
  haveI := Fact.mk hp
  obtain ⟨P⟩ : Nonempty (Sylow p A) := inferInstance
  have hPn : (P : Subgroup A).Normal := by
    refine ⟨fun n hn g => ?_⟩
    have : g * n * g⁻¹ = n := by
      apply Subtype.ext
      simp only [Subgroup.coe_mul, Subgroup.coe_inv]
      rw [hcomm _ g.2 _ n.2, mul_assoc, mul_inv_cancel, mul_one]
    rw [this]; exact hn
  haveI : (P : Subgroup A).Characteristic := Sylow.characteristic_of_normal P hPn
  refine ⟨p, (P : Subgroup A).map A.subtype, hp, inferInstance, ?_, P.2.map _⟩
  intro h
  apply P.ne_bot_of_dvd_card hpd
  rwa [Subgroup.map_eq_bot_iff_of_injective _ A.subtype_injective] at h

/-! ### §2.  Galois's theorem on solvable primitive groups -/

/-- In a primitive permutation group, a nontrivial normal subgroup is
transitive, so its order is a multiple of the degree. -/
theorem card_dvd_of_normal_ne_bot {α : Type*} [Fintype α] (H : Subgroup (Perm α))
    [IsPreprimitive H α] (K : Subgroup H) [K.Normal] (hK : K ≠ ⊥) :
    Fintype.card α ∣ Nat.card K := by
  have hfix : fixedPoints K α ≠ Set.univ := by
    obtain ⟨k, hk1⟩ := (Subgroup.ne_bot_iff_exists_ne_one).1 hK
    intro h
    apply hk1
    ext a
    have : k • a = a := (h ▸ Set.mem_univ a : a ∈ fixedPoints K α) k
    simpa using this
  haveI : IsPretransitive K α := IsQuasiPreprimitive.isPretransitive_of_normal hfix
  obtain ⟨a⟩ : Nonempty α := by
    by_contra h
    exact hfix (Set.eq_univ_of_forall fun x => (h ⟨x⟩).elim)
  rw [← Nat.card_eq_fintype_card, ← index_stabilizer_of_transitive K a]
  exact Subgroup.index_dvd_card _

/-- **Galois's theorem on solvable primitive groups**, the half needed here:
a solvable primitive permutation group on at least two points has prime-power
degree. -/
theorem isPrimePow_card_of_isPreprimitive_of_isSolvable {α : Type*} [Fintype α]
    (H : Subgroup (Perm α)) [IsPreprimitive H α] [IsSolvable H]
    (h2 : 2 ≤ Fintype.card α) : IsPrimePow (Fintype.card α) := by
  classical
  haveI : Nontrivial H := by
    obtain ⟨a, b, hab⟩ := Fintype.exists_pair_of_one_lt_card (by omega : 1 < Fintype.card α)
    obtain ⟨h, hh⟩ := exists_smul_eq H a b
    refine ⟨⟨h, 1, fun e => hab ?_⟩⟩
    rw [← hh, e, one_smul]
  obtain ⟨p, K, hp, hKn, hK, hpK⟩ := exists_normal_pGroup_ne_bot (G := H)
  haveI := Fact.mk hp
  obtain ⟨k, hk⟩ := (IsPGroup.iff_card).1 hpK
  have hd := card_dvd_of_normal_ne_bot H K hK
  rw [hk, Nat.dvd_prime_pow hp] at hd
  obtain ⟨i, -, hi⟩ := hd
  rw [isPrimePow_nat_iff]
  refine ⟨p, i, hp, Nat.pos_of_ne_zero ?_, hi.symm⟩
  rintro rfl
  simp at hi; omega

/-! ### §3.  The certificate for Galois groups -/

/-- The Galois group of an irreducible polynomial over `ℚ` whose degree is not
a prime power, holding an element that fixes one complex root and cycles all
the others, is not solvable. -/
theorem not_solvable_of_long_cycle_of_not_isPrimePow {p : ℚ[X]} (p_irr : Irreducible p)
    (hdeg : ¬ IsPrimePow p.natDegree) (τ : p.Gal)
    (hτ : (galActionHom p ℂ τ).cycleType = {p.natDegree - 1}) :
    ¬ IsSolvable p.Gal := by
  classical
  intro hsolv
  have h2 : 2 ≤ p.natDegree - 1 :=
    Equiv.Perm.two_le_of_mem_cycleType (by rw [hτ]; exact Multiset.mem_singleton_self _)
  have hτcyc : (galActionHom p ℂ τ).IsCycle := by
    rw [← Equiv.Perm.card_cycleType_eq_one, hτ, Multiset.card_singleton]
  have hτcard : (galActionHom p ℂ τ).support.card + 1 = p.natDegree := by
    rw [← Equiv.Perm.sum_cycleType, hτ, Multiset.sum_singleton]
    omega
  set H := (galActionHom p ℂ).range with hH
  haveI hHsolv : IsSolvable H :=
    solvable_of_surjective (galActionHom p ℂ).rangeRestrict_surjective
  have hcard := GLM.FrobeniusRadicals.card_complex_roots p_irr
  haveI : MulAction.IsPretransitive H (p.rootSet ℂ) := by
    have := galAction_isPretransitive p ℂ p_irr
    refine ⟨fun x y => ?_⟩
    obtain ⟨g, hg⟩ := MulAction.exists_smul_eq p.Gal x y
    exact ⟨⟨galActionHom p ℂ g, g, rfl⟩, hg⟩
  haveI : MulAction.IsPreprimitive H (p.rootSet ℂ) :=
    GLM.PrimitiveRadicals.isPreprimitive_of_isCycle_fixing_one H ⟨τ, rfl⟩ hτcyc
      (by rw [hcard]; exact hτcard)
  apply hdeg
  rw [← hcard]
  exact isPrimePow_card_of_isPreprimitive_of_isSolvable H (by rw [hcard]; omega)

/-- **The certificate the layer cites.**  Let `p` be irreducible over `ℚ` of a
degree `n` that is not a prime power, and suppose its Galois group holds an
element of cycle type `(n - 1, 1)` on the complex roots.  Then no root of `p`
is solvable by radicals.  (The layer reads the element off a factorisation of
`p` modulo a prime, through Dedekind's theorem, which is not proved here.) -/
theorem no_radical_root_of_long_cycle_of_not_isPrimePow {p : ℚ[X]} (p_irr : Irreducible p)
    (hdeg : ¬ IsPrimePow p.natDegree) (τ : p.Gal)
    (hτ : (galActionHom p ℂ τ).cycleType = {p.natDegree - 1})
    (x : ℂ) (hx : aeval x p = 0) : ¬ IsSolvableByRad ℚ x :=
  mt (solvableByRad.isSolvable' p_irr hx)
    (not_solvable_of_long_cycle_of_not_isPrimePow p_irr hdeg τ hτ)

end GLM.PrimitiveDegree
