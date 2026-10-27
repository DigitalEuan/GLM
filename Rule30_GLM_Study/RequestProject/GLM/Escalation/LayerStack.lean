module

public import Mathlib

/-!
# Round 43: the layer stack of `GLM_Escalation_Boundaries_Exploration.md`, checked

A *view* of carriers `C` is a map `perceive : C → V`. Two carriers are indistinguishable at the
view when they have the same image; a view `L'` *refines* `L` when everything `L'` conflates, `L`
conflates too; an operation is *congruent* for a view when the view's kernel is a congruence for
it (so the operation can be computed on views alone). This is the same vocabulary as the GLM's
own layer theory; it is restated here in a self-contained form so that the checks below can be
moved without the rest of the GLM.

The exploration document assigns the five GLM layers the moduli `2, 4, 8, 144, 256` and claims
that the refinement order `Substrate ≺ Integer ≺ Rational ≺ Griess ≺ Universal` is forced by
them. The checks:

| statement in the exploration | verdict | Lean |
|---|---|---|
| residue views refine by "inclusion of residue classes" | true, and exactly: mod `m'` refines mod `m` iff `m ∣ m'` | `residue_refines_iff` |
| "`8 ∤ 144`" (so Rational → Griess is not arithmetic) | **false**: `144 = 8 · 18`, mod 144 refines mod 8 | `residue_144_refines_8` |
| mod 256 refines mod 144 (Griess ≺ Universal) | **false** | `residue_256_not_refines_144` |
| — (repair) | the cumulative view (mod 144, mod 256) is exactly mod `2304 = lcm` | `residue_pair_indist_iff` |
| Rational perceives the identity, and Griess / Universal refine it | **impossible**: only injective views refine the identity, and no residue view is injective | `refines_identity_iff`, `residue_not_refines_identity` |
| graded escalation: addition of `1/2 + 1/2` is resolved by the mod 8 filter | **false** for every floor-residue filter `⌊q⌋ mod m`, `m ≥ 2` | `floorResidue_add_not_congruent` |
| "mod 4 fails: `perceive₄(1) = 1 ≠ 2 + 2`" (scaled reading `⌊4q⌋ mod 4`) | **false**: `⌊4·1⌋ = 4 ≡ 0 = 2 + 2 (mod 4)` | `scaled_four_half_consistent` |
| a finer layer is congruent whenever a coarser one is (escalating "upward" only helps) | **false**: congruence is not monotone in refinement | `congruent_not_monotone` |
| every lossless layer is congruent for every operation | true | `congruent_of_injective` |
-/

@[expose] public section

namespace GLM.Escalation

/-- A view (layer) of carriers `C`: what the layer can see of a carrier. -/
structure View (C : Type*) where
  /-- The type of observations. -/
  Obs : Type*
  /-- How a carrier is perceived. -/
  perceive : C → Obs

namespace View

variable {C : Type*}

/-- Two carriers are indistinguishable at a view. -/
def Indist (L : View C) (a b : C) : Prop := L.perceive a = L.perceive b

/-- `L'` refines `L`: whatever `L'` conflates, `L` conflates. -/
def Refines (L' L : View C) : Prop := ∀ a b, L'.Indist a b → L.Indist a b

/-- An operation descends to a view (is congruent for it) on a region `S`. -/
def Congruent (L : View C) (S : Set C) (op : C → C → C) : Prop :=
  ∀ a b a' b', a ∈ S → b ∈ S → a' ∈ S → b' ∈ S →
    L.Indist a a' → L.Indist b b' → L.Indist (op a b) (op a' b')

theorem Refines.trans {L L' L'' : View C} (h₁ : L''.Refines L') (h₂ : L'.Refines L) :
    L''.Refines L := fun a b h => h₂ a b (h₁ a b h)

/-- The identity view (the exact carrier). -/
def ident (C : Type*) : View C := ⟨C, id⟩

/-- **Only injective views refine the identity.** Nothing can sit strictly above an exact view. -/
theorem refines_identity_iff (L : View C) :
    L.Refines (ident C) ↔ Function.Injective L.perceive := by
  constructor
  · intro h a b hab; exact h a b hab
  · intro h a b hab; exact h hab

/-- Every operation is congruent for a lossless (injective) view. -/
theorem congruent_of_injective (L : View C) (hL : Function.Injective L.perceive)
    (S : Set C) (op : C → C → C) : L.Congruent S op := by
  intro a b a' b' _ _ _ _ ha hb
  rw [hL ha, hL hb]
  rfl

/-- The trivial view (sees nothing). -/
def trivial (C : Type*) : View C := ⟨Unit, fun _ => ()⟩

end View

open View

/-! ## Residue views on integers -/

/-- The residue view mod `m` on the integers. -/
def residue (m : ℕ) : View ℤ := ⟨ZMod m, fun z => (z : ZMod m)⟩

/-- **Residue views refine exactly by divisibility.** -/
theorem residue_refines_iff (m m' : ℕ) : (residue m').Refines (residue m) ↔ m ∣ m' := by
  constructor
  · intro h
    have h0 : (residue m').Indist (m' : ℤ) 0 := by
      simp [View.Indist, residue]
    have := h _ _ h0
    simp only [View.Indist, residue, Int.cast_natCast, Int.cast_zero] at this
    exact (ZMod.natCast_eq_zero_iff m' m).1 this
  · intro hd a b hab
    simp only [View.Indist, residue] at hab ⊢
    rw [ZMod.intCast_eq_intCast_iff_dvd_sub] at hab ⊢
    exact dvd_trans (Int.natCast_dvd_natCast.2 hd) hab

/-- `8 ∣ 144`: the exploration's "`8 ∤ 144`" is false. -/
theorem eight_dvd_144 : (8 : ℕ) ∣ 144 := ⟨18, rfl⟩

/-- So the Griess filter (mod 144) refines the Rational filter (mod 8) arithmetically. -/
theorem residue_144_refines_8 : (residue 144).Refines (residue 8) :=
  (residue_refines_iff 8 144).2 eight_dvd_144

/-- **The Universal filter (mod 256) does not refine the Griess filter (mod 144)**: `0` and
`256` look the same mod 256 and different mod 144. -/
theorem residue_256_not_refines_144 : ¬ (residue 256).Refines (residue 144) := by
  rw [residue_refines_iff]; decide

/-- The cumulative view: carry both readings. -/
def pairView (m m' : ℕ) : View ℤ := ⟨ZMod m × ZMod m', fun z => ((z : ZMod m), (z : ZMod m'))⟩

/-- **Repair.** Carrying both the mod-144 and the mod-256 reading is exactly the residue view
mod `2304 = lcm 144 256`; it refines both. -/
theorem residue_pair_indist_iff (a b : ℤ) :
    (pairView 144 256).Indist a b ↔ (residue 2304).Indist a b := by
  simp only [View.Indist, pairView, residue, Prod.mk.injEq, ZMod.intCast_eq_intCast_iff_dvd_sub]
  constructor
  · rintro ⟨h1, h2⟩
    have : ((Nat.lcm 144 256 : ℕ) : ℤ) ∣ b - a := by
      rw [Int.natCast_dvd] at h1 h2 ⊢
      exact Nat.lcm_dvd h1 h2
    simpa using this
  · intro h
    exact ⟨dvd_trans (by norm_num) h, dvd_trans (by norm_num) h⟩

theorem lcm_144_256 : Nat.lcm 144 256 = 2304 := by norm_num

/-- No residue view of `ℤ` with `m ≥ 1` is injective, so none refines the exact view. -/
theorem residue_not_refines_identity (m : ℕ) (hm : 0 < m) :
    ¬ (residue m).Refines (ident ℤ) := by
  rw [refines_identity_iff]
  intro h
  have : ((m : ℤ) : ZMod m) = ((0 : ℤ) : ZMod m) := by simp
  have := h this
  omega

/-! ## Floor-residue filters on rationals: the half-unit case -/

/-- The floor-residue filter `q ↦ ⌊q⌋ mod m` on rationals (the exploration's Substrate /
Integer perception for `m = 2, 4`). -/
def floorResidue (m : ℕ) : View ℚ := ⟨ZMod m, fun q => ((⌊q⌋ : ℤ) : ZMod m)⟩

/-- **No floor-residue filter resolves the half-unit sum.** For every modulus `m ≥ 2`, addition
is not congruent for `⌊q⌋ mod m` on `{0, 1/2}`: `1/2 ~ 0` but `1/2 + 1/2 = 1 ≁ 0 = 0 + 0`.
So the graded escalation of the exploration can never stop at a floor-residue layer on this
example, whatever the modulus (8, 144, 256 included). -/
theorem floorResidue_add_not_congruent (m : ℕ) (hm : 2 ≤ m) :
    ¬ (floorResidue m).Congruent {0, 1/2} (· + ·) := by
  intro h
  have hhalf' : ⌊(2⁻¹ : ℚ)⌋ = 0 := by norm_num [Int.floor_eq_iff]
  have h1 := h (1/2) (1/2) 0 0 (by simp) (by simp) (by simp) (by simp)
    (by simp [View.Indist, floorResidue, hhalf']) (by simp [View.Indist, floorResidue, hhalf'])
  simp only [View.Indist, floorResidue] at h1
  norm_num at h1
  have h1' : ((1 : ℕ) : ZMod m) = 0 := by exact_mod_cast h1
  rw [ZMod.natCast_eq_zero_iff] at h1'
  have := Nat.le_of_dvd one_pos h1'
  omega

/-- The scaled reading `q ↦ ⌊m q⌋ mod m` used in the exploration's mod-4 computation. -/
def scaledResidue (m : ℕ) : View ℚ := ⟨ZMod m, fun q => ((⌊(m : ℚ) * q⌋ : ℤ) : ZMod m)⟩

/-- **The exploration's mod-4 computation is wrong**: with its own scaled reading,
`perceive₄(1/2) + perceive₄(1/2) = 2 + 2 = 0 = perceive₄(1)` in `ZMod 4`. -/
theorem scaled_four_half_consistent :
    (((⌊(4 : ℚ) * (1/2)⌋ : ℤ) : ZMod 4) + ((⌊(4 : ℚ) * (1/2)⌋ : ℤ) : ZMod 4) =
      ((⌊(4 : ℚ) * (1/2 + 1/2)⌋ : ℤ) : ZMod 4)) ∧
    (scaledResidue 4).perceive (1/2) = ((⌊(4 : ℚ) * (1/2)⌋ : ℤ) : ZMod 4) := by
  refine ⟨?_, rfl⟩
  have e1 : ⌊(4 : ℚ) * (1/2)⌋ = 2 := by norm_num
  have e2 : ⌊(4 : ℚ) * (1/2 + 1/2)⌋ = 4 := by norm_num
  rw [e1, e2]
  decide

/-! ## Congruence is not monotone in refinement -/

/-- **Escalating to a finer layer can lose congruence.** The trivial view is congruent for
addition on all rationals; the floor-parity view refines it and is not. So "the first layer up
the stack that resolves" is not a monotone notion, and graded escalation needs an explicit
resolving test at every layer, not a search for a threshold. -/
theorem congruent_not_monotone :
    (floorResidue 2).Refines (View.trivial ℚ) ∧
    (View.trivial ℚ).Congruent Set.univ (· + ·) ∧
    ¬ (floorResidue 2).Congruent Set.univ (· + ·) := by
  refine ⟨fun _ _ _ => rfl, fun _ _ _ _ _ _ _ _ _ _ => rfl, fun h => ?_⟩
  exact floorResidue_add_not_congruent 2 le_rfl
    (fun a b a' b' _ _ _ _ => h a b a' b' trivial trivial trivial trivial)

end GLM.Escalation
