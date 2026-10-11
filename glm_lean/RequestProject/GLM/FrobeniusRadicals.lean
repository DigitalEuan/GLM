module

public import Mathlib

/-!
# Roots with no expression in radicals, read from one Galois element

`studies/FROBENIUS_RADICAL_STUDY.md` (Phase 113) widens the radical-free
statement of the branch layer of `solve symbolically`
(`overlay/glm_universal/reasoning/symbolic_factor.py`).  Phase 112's
certificate (`GLM.QuinticRadicals.no_radical_root_of_prime_degree`) needs
exactly two non-real roots, so it is silent on `x⁵ - x - 1`, which has one
real root and no root in radicals.  The new certificate reads the Galois group
through one of its elements instead of through complex conjugation.

## What is proved here

* §1 (pure group theory). `exists_pow_cycleType_singleton`: a permutation with
  exactly one cycle of prime length `ℓ`, all of whose other cycle lengths are
  prime to `ℓ`, has a power that is a single `ℓ`-cycle.
  `not_solvable_of_alternating_le`: a permutation group on at least five
  letters that contains the alternating group is not solvable.
* §2 (Jordan, for a Galois group). `not_solvable_of_swap_or_three_cycle` and
  `no_radical_root_of_cycle_pattern`: a transposition or a 3-cycle in the
  Galois group of an irreducible polynomial over `ℚ` of prime degree `n ≥ 5`
  rules out roots in radicals.
* §3 (Galois, the complete form).  `eq_one_of_two_fixed_of_solvable`: in a
  solvable transitive permutation group of prime degree only the identity
  fixes two points.  `exists_pow_two_fixed`: a permutation of non-affine shape
  (`NotAffineShape`) has a power that moves something and fixes two points.
  `no_radical_root_of_frobenius_shape` — **the certificate the layer cites**:
  if the Galois group of an irreducible polynomial over `ℚ` of prime degree
  holds an element of non-affine shape, no root is solvable by radicals.
  Every non-solvable group of prime degree holds such an element (the other
  half of Galois's theorem, not proved here), `PSL(2, 7)` included, which §2
  cannot reach.

## What is not proved here

The layer finds that element by factoring the polynomial modulo a prime `q`
not dividing its discriminant or leading coefficient: by Dedekind's theorem
the Frobenius element at `q` has the degrees of the irreducible factors modulo
`q` as its cycle type.  Dedekind's theorem is *not* proved in this file, and
the factorisation modulo `q` is decided by the Python side, not checked here.
What is proved is the inference from "the group contains an element of that
cycle type" to "no root is solvable by radicals".
-/

@[expose] public section

namespace GLM.FrobeniusRadicals

open Equiv Equiv.Perm Polynomial Polynomial.Gal

attribute [local instance] splits_ℚ_ℂ

/-! ### §1.  Group theory -/

/-- A permutation group on at least five letters that contains the alternating
group is not solvable. -/
theorem not_solvable_of_alternating_le {α : Type*} [Fintype α] [DecidableEq α]
    (h5 : 5 ≤ Fintype.card α) {G : Subgroup (Perm α)} (hG : alternatingGroup α ≤ G) :
    ¬ IsSolvable G := by
  have key : Nonempty (Fin 5 ↪ α) := Function.Embedding.nonempty_of_card_le (by simpa using h5)
  obtain ⟨ι⟩ := key
  let φ := viaEmbeddingHom ι
  have hmem : ∀ e : Perm (Fin 5), sign e = 1 → φ e ∈ G := fun e he => by
    apply hG
    rw [mem_alternatingGroup]
    simp only [φ, viaEmbeddingHom, extendDomainHom_apply, sign_extendDomain, he]
  -- a 3-cycle, and two even permutations exhibiting it as a conjugate of a commutator
  let x : Perm (Fin 5) := ⟨![1, 2, 0, 3, 4], ![2, 0, 1, 3, 4], by decide, by decide⟩
  let y : Perm (Fin 5) := ⟨![0, 3, 4, 1, 2], ![0, 3, 4, 1, 2], by decide, by decide⟩
  let z : Perm (Fin 5) := ⟨![0, 1, 4, 2, 3], ![0, 1, 3, 4, 2], by decide, by decide⟩
  have key : x = z * ⁅x, y * x * y⁻¹⁆ * z⁻¹ := by unfold x y z; decide
  let X : G := ⟨φ x, hmem x (by unfold x; decide)⟩
  let Y : G := ⟨φ y, hmem y (by unfold y; decide)⟩
  let Z : G := ⟨φ z, hmem z (by unfold z; decide)⟩
  have key' : X = Z * ⁅X, Y * X * Y⁻¹⁆ * Z⁻¹ := by
    apply Subtype.ext
    simp only [X, Y, Z, Subgroup.coe_mul, Subgroup.coe_inv, commutatorElement_def]
    conv_lhs => rw [key]
    simp [commutatorElement_def, map_mul, map_inv]
  have hX : X ≠ 1 := by
    intro h
    have : φ x = 1 := congrArg Subtype.val h
    exact absurd (viaEmbeddingHom_injective ι (this.trans (map_one φ).symm)) (by unfold x; decide)
  refine not_solvable_of_mem_derivedSeries hX fun n => ?_
  induction n with
  | zero => exact Subgroup.mem_top X
  | succ n ih =>
    rw [key', (derivedSeries_normal _ _).mem_comm_iff, inv_mul_cancel_left]
    exact Subgroup.commutator_mem_commutator ih ((derivedSeries_normal _ _).conj_mem _ ih _)

/-- A permutation with exactly one cycle of prime length `ℓ`, whose other
cycle lengths are all prime to `ℓ`, has a power that is a single `ℓ`-cycle
(the power is the product of the other cycle lengths). -/
theorem exists_pow_cycleType_singleton {α : Type*} [Fintype α] [DecidableEq α]
    {σ : Perm α} {ℓ : ℕ} (hℓ : ℓ.Prime) (hcount : σ.cycleType.count ℓ = 1)
    (hrest : ∀ k ∈ σ.cycleType, k ≠ ℓ → ¬ ℓ ∣ k) :
    ∃ n : ℕ, (σ ^ n).cycleType = {ℓ} := by
  haveI := Fact.mk hℓ
  set m := (σ.cycleType.filter (· ≠ ℓ)).prod with hm
  have hkm : ∀ k ∈ σ.cycleType, k ≠ ℓ → k ∣ m := fun k hk hne =>
    Multiset.dvd_prod (Multiset.mem_filter.mpr ⟨hk, hne⟩)
  have hℓm : ¬ ℓ ∣ m := by
    intro h
    obtain ⟨k, hk, hdvd⟩ := (Nat.prime_iff.mp hℓ).exists_mem_multiset_dvd h
    obtain ⟨hk1, hk2⟩ := Multiset.mem_filter.mp hk
    exact hrest k hk1 hk2 hdvd
  have hℓmem : ℓ ∈ σ.cycleType := Multiset.count_pos.mp (by omega)
  refine ⟨m, ?_⟩
  set τ := σ ^ m with hτ
  have hτℓ : τ ^ ℓ = 1 := by
    rw [hτ, ← pow_mul, ← orderOf_dvd_iff_pow_eq_one, ← lcm_cycleType]
    refine Multiset.lcm_dvd.mpr fun k hk => ?_
    by_cases hk' : k = ℓ
    · subst hk'; exact dvd_mul_left k m
    · exact (hkm k hk hk').mul_right ℓ
  have hτ1 : τ ≠ 1 := by
    intro h
    apply hℓm
    have : orderOf σ ∣ m := orderOf_dvd_of_pow_eq_one h
    rw [← lcm_cycleType] at this
    exact (Multiset.dvd_lcm hℓmem).trans this
  obtain ⟨c, hc, hcℓ⟩ : ∃ c ∈ σ.cycleFactorsFinset, c.support.card = ℓ := by
    rw [cycleType_def, Multiset.mem_map] at hℓmem
    obtain ⟨c, hc, h⟩ := hℓmem
    exact ⟨c, hc, h⟩
  have huniq : ∀ c' ∈ σ.cycleFactorsFinset, c'.support.card = ℓ → c' = c := by
    intro c' hc' hc'ℓ
    by_contra hne
    have hsub : ({c', c} : Finset (Perm α)) ⊆
        σ.cycleFactorsFinset.filter (fun d => ℓ = d.support.card) := by
      intro d hd
      simp only [Finset.mem_insert, Finset.mem_singleton] at hd
      rcases hd with rfl | rfl
      · exact Finset.mem_filter.mpr ⟨hc', hc'ℓ.symm⟩
      · exact Finset.mem_filter.mpr ⟨hc, hcℓ.symm⟩
    have h2 := Finset.card_le_card hsub
    rw [Finset.card_pair hne] at h2
    have : σ.cycleType.count ℓ =
        (σ.cycleFactorsFinset.filter (fun d => ℓ = d.support.card)).card := by
      rw [cycleType_def, Multiset.count_map]
      rfl
    omega
  have hsupp : τ.support ⊆ c.support := by
    intro x hx
    rw [mem_support] at hx
    have hxσ : x ∈ σ.support := by
      by_contra h
      rw [notMem_support] at h
      exact hx (pow_apply_eq_self_of_apply_eq_self h m)
    have hcyc : σ.cycleOf x ∈ σ.cycleFactorsFinset := cycleOf_mem_cycleFactorsFinset_iff.mpr hxσ
    have hlen : (σ.cycleOf x).support.card = ℓ := by
      by_contra hne
      apply hx
      have hk : (σ.cycleOf x).support.card ∈ σ.cycleType := by
        rw [cycleType_def]; exact Multiset.mem_map_of_mem _ hcyc
      have hd := hkm _ hk hne
      rw [hτ, ← cycleOf_pow_apply_self]
      rw [← (isCycle_cycleOf σ (mem_support.mp hxσ)).orderOf] at hd
      rw [orderOf_dvd_iff_pow_eq_one.mp hd]
      rfl
    rw [← huniq _ hcyc hlen]
    exact mem_support_cycleOf_iff.mpr ⟨SameCycle.refl _ _, hxσ⟩
  have hk := Equiv.Perm.cycleType_of_pow_prime_eq_one hτℓ
  have hsum := sum_cycleType τ
  have hle := Finset.card_le_card hsupp
  rw [hk, Multiset.sum_replicate, smul_eq_mul] at hsum
  have hN : τ.cycleType.card ≠ 0 := by
    rw [Ne, Multiset.card_eq_zero, cycleType_eq_zero]; exact hτ1
  have hN1 : τ.cycleType.card = 1 := by
    rcases Nat.lt_or_ge τ.cycleType.card 2 with h | h
    · omega
    · have := Nat.mul_le_mul_right ℓ h
      have := hℓ.pos
      omega
  rw [hk, hN1, Multiset.replicate_one]

/-! ### §2.  Galois groups -/

/-- The number of complex roots of an irreducible polynomial over `ℚ` is its
degree. -/
theorem card_complex_roots {p : ℚ[X]} (p_irr : Irreducible p) :
    Fintype.card (p.rootSet ℂ) = p.natDegree :=
  card_rootSet_eq_natDegree p_irr.separable (IsAlgClosed.splits _)

/-- **Jordan, for a Galois group.** If the Galois group of an irreducible
polynomial over `ℚ` of prime degree at least 5 contains an element acting on
the complex roots as a transposition or as a 3-cycle, it is not solvable. -/
theorem not_solvable_of_swap_or_three_cycle {p : ℚ[X]} (p_irr : Irreducible p)
    (p_deg : p.natDegree.Prime) (p_five : 5 ≤ p.natDegree) (σ : p.Gal)
    (hσ : IsSwap (galActionHom p ℂ σ) ∨ IsThreeCycle (galActionHom p ℂ σ)) :
    ¬ IsSolvable p.Gal := by
  classical
  intro hsolv
  set H := (galActionHom p ℂ).range with hH
  have hHsolv : IsSolvable H := solvable_of_surjective (galActionHom p ℂ).rangeRestrict_surjective
  have hcard := card_complex_roots p_irr
  haveI : MulAction.IsPretransitive H (p.rootSet ℂ) := by
    have := galAction_isPretransitive p ℂ p_irr
    refine ⟨fun x y => ?_⟩
    obtain ⟨g, hg⟩ := MulAction.exists_smul_eq p.Gal x y
    exact ⟨⟨galActionHom p ℂ g, g, rfl⟩, hg⟩
  have hprim : MulAction.IsPreprimitive H (p.rootSet ℂ) :=
    MulAction.IsPreprimitive.of_prime_card (by rw [Nat.card_eq_fintype_card, hcard]; exact p_deg)
  have hmem : galActionHom p ℂ σ ∈ H := ⟨σ, rfl⟩
  have hA : alternatingGroup (p.rootSet ℂ) ≤ H := by
    rcases hσ with h | h
    · rw [subgroup_eq_top_of_isPreprimitive_of_isSwap_mem hprim _ h hmem]; exact le_top
    · exact alternatingGroup_le_of_isPreprimitive_of_isThreeCycle_mem hprim h hmem
  exact not_solvable_of_alternating_le (by rw [hcard]; exact p_five) hA hHsolv

/-- If the Galois group contains a transposition or a 3-cycle (prime degree at
least 5, irreducible over `ℚ`), no root is solvable by radicals. -/
theorem no_radical_root_of_swap_or_three_cycle {p : ℚ[X]} (p_irr : Irreducible p)
    (p_deg : p.natDegree.Prime) (p_five : 5 ≤ p.natDegree) (σ : p.Gal)
    (hσ : IsSwap (galActionHom p ℂ σ) ∨ IsThreeCycle (galActionHom p ℂ σ))
    (x : ℂ) (hx : aeval x p = 0) : ¬ IsSolvableByRad ℚ x :=
  mt (solvableByRad.isSolvable' p_irr hx) (not_solvable_of_swap_or_three_cycle p_irr p_deg p_five σ hσ)

/-- **The certificate.** Let `p` be irreducible over `ℚ` of prime degree at
least 5, and suppose its Galois group contains an element whose cycle type on
the complex roots has exactly one cycle of length `ℓ`, where `ℓ` is 2 or 3,
and every other cycle of length prime to `ℓ`.  Then no root of `p` is solvable
by radicals.  (The layer reads such an element off a factorisation of `p`
modulo a prime, through Dedekind's theorem, which is not proved here.) -/
theorem no_radical_root_of_cycle_pattern {p : ℚ[X]} (p_irr : Irreducible p)
    (p_deg : p.natDegree.Prime) (p_five : 5 ≤ p.natDegree) (σ : p.Gal) {ℓ : ℕ}
    (hℓ : ℓ = 2 ∨ ℓ = 3)
    (hcount : (galActionHom p ℂ σ).cycleType.count ℓ = 1)
    (hrest : ∀ k ∈ (galActionHom p ℂ σ).cycleType, k ≠ ℓ → ¬ ℓ ∣ k)
    (x : ℂ) (hx : aeval x p = 0) : ¬ IsSolvableByRad ℚ x := by
  classical
  have hℓp : ℓ.Prime := by rcases hℓ with rfl | rfl <;> norm_num
  obtain ⟨n, hn⟩ := exists_pow_cycleType_singleton hℓp hcount hrest
  rw [← map_pow] at hn
  refine no_radical_root_of_swap_or_three_cycle p_irr p_deg p_five (σ ^ n) ?_ x hx
  rcases hℓ with rfl | rfl
  · left
    rw [← Equiv.Perm.card_support_eq_two, ← sum_cycleType, hn]
    rfl
  · right
    exact hn

/-! ### §3.  Galois's theorem on groups of prime degree, and the complete shape test -/

/-- **Galois's theorem** (the half used here). In a solvable transitive
permutation group of prime degree, an element fixing two distinct points is
the identity.  (The last nontrivial term of the derived series is an abelian
normal subgroup; it is transitive because the group is primitive, hence
regular of prime order, hence generated by any of its non-identity elements;
an element fixing two points commutes with one of them, so with all of it,
so it fixes every point.) -/
theorem eq_one_of_two_fixed_of_solvable {α : Type*} [Fintype α] [DecidableEq α]
    (hp : (Fintype.card α).Prime) {G : Subgroup (Perm α)} [MulAction.IsPretransitive G α]
    (hG : IsSolvable G) {g : Perm α} (hg : g ∈ G) {x y : α} (hxy : x ≠ y)
    (hx : g x = x) (hy : g y = y) : g = 1 := by
  classical
  have hprim : MulAction.IsPreprimitive G α :=
    MulAction.IsPreprimitive.of_prime_card (by rw [Nat.card_eq_fintype_card]; exact hp)
  have hex : ∃ n, derivedSeries G n = ⊥ := (isSolvable_def G).mp hG
  set n₀ := Nat.find hex with hn₀
  have hn₀spec : derivedSeries G n₀ = ⊥ := Nat.find_spec hex
  rcases Nat.eq_zero_or_pos n₀ with h0 | hpos
  · rw [h0] at hn₀spec
    have : (⟨g, hg⟩ : G) ∈ derivedSeries G 0 := by simp
    rw [hn₀spec, Subgroup.mem_bot] at this
    exact congrArg Subtype.val this
  set N := derivedSeries G (n₀ - 1) with hN
  have hNbot : N ≠ ⊥ := Nat.find_min hex (by omega)
  have hNcomm : ∀ a ∈ N, ∀ b ∈ N, a * b = b * a := by
    intro a ha b hb
    have : ⁅a, b⁆ ∈ derivedSeries G n₀ := by
      have h1 : n₀ = (n₀ - 1) + 1 := by omega
      rw [h1, derivedSeries_succ]
      exact Subgroup.commutator_mem_commutator ha hb
    rw [hn₀spec, Subgroup.mem_bot, commutatorElement_eq_one_iff_mul_comm] at this
    exact this
  haveI hNn : N.Normal := derivedSeries_normal G _
  -- `N` is transitive: its orbits are blocks of a primitive group
  have htrans : ∀ z, ∃ a ∈ N, (a : Perm α) x = z := by
    have hb := MulAction.IsBlock.orbit_of_normal (G := G) (N := N) x
    rcases hprim.isTrivialBlock_of_isBlock hb with hs | hu
    · exfalso
      apply hNbot
      rw [eq_bot_iff]
      intro a ha
      rw [Subgroup.mem_bot]
      have hfixx : ∀ b ∈ N, (b : Perm α) x = x := fun b hb' =>
        hs (MulAction.mem_orbit x (⟨b, hb'⟩ : N)) (MulAction.mem_orbit_self x)
      apply Subtype.ext
      ext w
      obtain ⟨h, hh⟩ := MulAction.exists_smul_eq G x w
      have hc : h⁻¹ * a * h ∈ N := by
        have := hNn.conj_mem a ha h⁻¹
        simpa using this
      have := hfixx _ hc
      simp only [Subgroup.coe_mul, Subgroup.coe_inv, Perm.mul_apply] at this
      rw [← hh]
      show (a : Perm α) ((h : Perm α) x) = (h : Perm α) x
      have h2 := congrArg (h : Perm α) this
      simpa using h2
    · intro z
      have : z ∈ MulAction.orbit N x := by rw [hu]; trivial
      obtain ⟨⟨a, ha⟩, rfl⟩ := this
      exact ⟨a, ha, rfl⟩
  -- `N` acts freely: it is abelian and transitive
  have hfree : ∀ a ∈ N, ∀ z, (a : Perm α) z = z → a = 1 := by
    intro a ha z hz
    apply Subtype.ext
    ext w
    obtain ⟨b, hb, rfl⟩ := htrans z
    obtain ⟨c, hc, rfl⟩ := htrans w
    have hcb : c * b⁻¹ ∈ N := N.mul_mem hc (N.inv_mem hb)
    have hx' : (c : Perm α) x = ((c * b⁻¹ : G) : Perm α) ((b : Perm α) x) := by simp
    rw [hx']
    have hcomm := hNcomm a ha _ hcb
    generalize c * b⁻¹ = d at hcomm ⊢
    have := congrArg (fun f : G => (f : Perm α) ((b : Perm α) x)) hcomm
    simp only [Subgroup.coe_mul, Perm.mul_apply] at this
    rw [Subgroup.coe_one, Perm.one_apply, this, hz]
  -- so `N` has `p` elements
  let f : N → α := fun a => ((a : G) : Perm α) x
  have hf : Function.Bijective f := by
    constructor
    · intro a a' h
      have h1 : ((a'⁻¹ * a : N) : G) = 1 := by
        apply hfree _ (a'⁻¹ * a).2 x
        simp only [Subgroup.coe_mul, Subgroup.coe_inv, Perm.mul_apply]
        have : ((a : G) : Perm α) x = ((a' : G) : Perm α) x := h
        rw [this]; simp
      have : a'⁻¹ * a = 1 := Subtype.ext h1
      exact (inv_mul_eq_one.mp this).symm
    · intro z
      obtain ⟨a, ha, h⟩ := htrans z
      exact ⟨⟨a, ha⟩, h⟩
  have hcardN : Nat.card N = Fintype.card α := by
    rw [Nat.card_congr (Equiv.ofBijective f hf), Nat.card_eq_fintype_card]
  haveI : Fact (Nat.card N).Prime := ⟨hcardN ▸ hp⟩
  obtain ⟨b, hb, hbx⟩ := htrans y
  set b' : N := ⟨b, hb⟩
  have hb1 : b' ≠ 1 := by
    intro h
    apply hxy
    have : b = 1 := congrArg Subtype.val h
    rw [← hbx, this]; rfl
  have hzp : Subgroup.zpowers b' = ⊤ := by
    rcases Subgroup.eq_bot_or_eq_top_of_prime_card (Subgroup.zpowers b') with h | h
    · exact absurd (Subgroup.zpowers_eq_bot.mp h) hb1
    · exact h
  set g' : G := ⟨g, hg⟩
  -- `g` commutes with `b`, hence with all of `N`
  have hc : g' * b * g'⁻¹ = b := by
    have hcN : g' * b * g'⁻¹ ∈ N := hNn.conj_mem b hb g'
    have h1 : b⁻¹ * (g' * b * g'⁻¹) = 1 := by
      apply hfree _ (N.mul_mem (N.inv_mem hb) hcN) x
      have hgi : g⁻¹ x = x := by rw [Perm.inv_eq_iff_eq]; exact hx.symm
      simp only [Subgroup.coe_mul, Subgroup.coe_inv, Perm.mul_apply, g', hgi, hbx, hy]
      rw [← hbx]; simp
    exact (inv_mul_eq_one.mp h1).symm
  have hcomm : ∀ a ∈ N, g' * a * g'⁻¹ = a := by
    intro a ha
    have : (⟨a, ha⟩ : N) ∈ Subgroup.zpowers b' := by rw [hzp]; trivial
    obtain ⟨k, hk⟩ := this
    have hk' : a = b ^ k := by
      have := congrArg Subtype.val hk
      simpa [b'] using this.symm
    rw [hk', ← conj_zpow, hc]
  ext z
  obtain ⟨a, ha, rfl⟩ := htrans z
  have h := congrArg (fun u : G => (u : Perm α) x) (hcomm a ha)
  simp only [Subgroup.coe_mul, Subgroup.coe_inv, Perm.mul_apply, g'] at h
  have hgi : g⁻¹ x = x := by rw [Perm.inv_eq_iff_eq]; exact hx.symm
  rw [hgi] at h
  rw [Perm.one_apply, h]

/-- The cycle shapes the layer accepts: those of a permutation that is *not* of
the affine shape `x ↦ a x + b` modulo a prime.  Either it is not the identity
and fixes at least two points, or two of its cycle lengths `k`, `k'` (both at
least 2) have `k'` not dividing `k`.  For a permutation of a prime number of
points this fails exactly for the identity, a single cycle through every point,
and one fixed point with all other cycles of one length. -/
def NotAffineShape {α : Type*} [Fintype α] [DecidableEq α] (σ : Perm α) : Prop :=
  (σ ≠ 1 ∧ 2 + σ.support.card ≤ Fintype.card α) ∨
    ∃ k ∈ σ.cycleType, ∃ k' ∈ σ.cycleType, ¬ k' ∣ k

/-- A permutation of a non-affine shape has a power that is not the identity
and fixes two distinct points. -/
theorem exists_pow_two_fixed {α : Type*} [Fintype α] [DecidableEq α] {σ : Perm α}
    (h : NotAffineShape σ) :
    ∃ m : ℕ, σ ^ m ≠ 1 ∧ ∃ x y : α, x ≠ y ∧ (σ ^ m) x = x ∧ (σ ^ m) y = y := by
  classical
  rcases h with ⟨h1, h2⟩ | ⟨k, hk, k', hk', hdvd⟩
  · refine ⟨1, by simpa using h1, ?_⟩
    have hc : 2 ≤ (σ.supportᶜ).card := by
      rw [Finset.card_compl]; omega
    obtain ⟨x, hx, y, hy, hxy⟩ := Finset.one_lt_card.mp hc
    refine ⟨x, y, hxy, ?_, ?_⟩
    · simpa using Finset.mem_compl.mp hx
    · simpa using Finset.mem_compl.mp hy
  · refine ⟨k, ?_, ?_⟩
    · intro h1
      apply hdvd
      have : orderOf σ ∣ k := orderOf_dvd_of_pow_eq_one h1
      rw [← lcm_cycleType] at this
      exact (Multiset.dvd_lcm hk').trans this
    · rw [cycleType_def, Multiset.mem_map] at hk
      obtain ⟨c, hc, hck⟩ := hk
      have hc' : c ∈ σ.cycleFactorsFinset := hc
      have hcyc : c.IsCycle := (mem_cycleFactorsFinset_iff.mp hc').1
      have h2 : 1 < c.support.card := by
        have := hcyc.two_le_card_support; omega
      obtain ⟨x, hx, y, hy, hxy⟩ := Finset.one_lt_card.mp h2
      have hfix : ∀ z ∈ c.support, (σ ^ k) z = z := by
        intro z hz
        have hco : σ.cycleOf z = c := (cycle_is_cycleOf hz hc').symm
        rw [← cycleOf_pow_apply_self, hco]
        have : orderOf c = k := by rw [hcyc.orderOf]; exact hck
        rw [← this, pow_orderOf_eq_one]; rfl
      exact ⟨x, y, hxy, hfix x hx, hfix y hy⟩

/-- **The complete certificate for prime degree.** If the Galois group of an
irreducible polynomial over `ℚ` of prime degree holds an element of
non-affine shape on the complex roots, no root is solvable by radicals.  (By
Chebotarev's density theorem such an element appears as a Frobenius element
whenever the group is not solvable, so the test the layer runs is complete in
the limit; that direction is not used or proved here.) -/
theorem no_radical_root_of_frobenius_shape {p : ℚ[X]} (p_irr : Irreducible p)
    (p_deg : p.natDegree.Prime) (σ : p.Gal) (hσ : NotAffineShape (galActionHom p ℂ σ))
    (x : ℂ) (hx : aeval x p = 0) : ¬ IsSolvableByRad ℚ x := by
  classical
  apply mt (solvableByRad.isSolvable' p_irr hx)
  intro hsolv
  set H := (galActionHom p ℂ).range with hH
  have hHsolv : IsSolvable H := solvable_of_surjective (galActionHom p ℂ).rangeRestrict_surjective
  have hcard := card_complex_roots p_irr
  haveI : MulAction.IsPretransitive H (p.rootSet ℂ) := by
    have := galAction_isPretransitive p ℂ p_irr
    refine ⟨fun x y => ?_⟩
    obtain ⟨g, hg⟩ := MulAction.exists_smul_eq p.Gal x y
    exact ⟨⟨galActionHom p ℂ g, g, rfl⟩, hg⟩
  obtain ⟨m, hm1, a, b, hab, ha, hb⟩ := exists_pow_two_fixed hσ
  rw [← map_pow] at hm1 ha hb
  exact hm1 (eq_one_of_two_fixed_of_solvable (by rw [hcard]; exact p_deg) hHsolv
    ⟨σ ^ m, rfl⟩ hab ha hb)

end GLM.FrobeniusRadicals
