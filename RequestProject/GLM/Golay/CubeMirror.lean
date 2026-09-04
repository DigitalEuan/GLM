import Mathlib
import RequestProject.GLM.Cube.Stabiliser

/-!
# The diagonal mirror, and why 24 is the ceiling

`Cube/Stabiliser.lean` shows that the cube's 48 surface symmetries split for a
Golay code placed on the 24 surface cells: the canonical MOG placement frees the
tetrahedral group of order 12, and a second placement frees the whole rotation
group of order 24.  It also records that no placement frees more, and that the
claim rested on a Python search over invariant subspaces — *not* verified there.

This file verifies the essential half of it, for the mirrors, and by counting
rather than by search.  Nothing about any particular code is used: the argument
rules out **every** Golay code on the surface at once, because it only needs the
Steiner property that the octads of a Golay code have.

## The argument

Let `σ` be the diagonal mirror — the reflection in the plane `x = y`, one of the
six mirrors of `T_d`.  On the 24 surface cells it

* is an involution (`mirror_involutive`),
* is not a rotation (`sigmaD_not_rotation`),
* fixes exactly **4** cells and transposes the other 20 in **10** pairs
  (`mirror_fixed_card`, `mirror_moved_card`).

A set of cells is *invariant* when `σ` maps it onto itself, so an invariant set
is built from fixed cells and whole pairs.  Two counts follow, both by
enumeration:

* there are exactly **220** invariant five-sets (`invFives_card`) — one fixed
  cell and two pairs, `4 · 45 = 180`, or three fixed cells and one pair,
  `4 · 10 = 40`;
* an invariant eight-set contains an even number of fixed cells, so 0, 2 or 4 of
  them, and the invariant five-subsets it holds number **0, 6 or 12**
  accordingly — every fibre is a multiple of six (`fibre_card_dvd_six`).  There
  are 975 invariant eight-sets in all (`invariant_octads_card`).

Now suppose a Golay code on these 24 cells had a mirror-invariant octad family
`F`.  Every five-set lies in exactly one octad — that is `S(5, 8, 24)` — so the
220 invariant five-sets are distributed among the octads with no five-set
counted twice.  An octad holding an invariant five-set is itself invariant, by
that same uniqueness: the mirror image of the octad also contains the five-set,
so it *is* the octad.  Hence 220 is a sum of fibres each divisible by six.

But `220 = 6 · 36 + 4`.  The arrangement is impossible, and that is
`no_mirror_invariant_steiner`: **no Golay code on the cube's surface survives a
diagonal mirror**, whatever the placement.  The order-24 rotation group is the
ceiling because the 24 extra improper symmetries include this mirror.

The counting statements are settled by `native_decide` over all
`C(24,5) = 42,504` five-sets and all `C(24,8) = 735,471` eight-sets; the
deduction from them is an ordinary proof.

The runtime counterpart is
`overlay/glm_universal/reasoning/salvage_second.py`, `cube_mirror_report`.
-/

namespace GLM.CubeMirror

open GLM.CubeStab Finset

set_option maxRecDepth 100000

/-! ## 1. The mirror -/

/-- The diagonal mirror: exchange the `x` and `y` axes, flip no sign.  It is the
reflection in the plane `x = y`, one of the six mirrors of `T_d`. -/
def sigmaD : CubeSym := (2, ![false, false, false])

/-- The mirror's action on the 24 surface cells. -/
def mirror (x : Cell) : Cell := actCell sigmaD x

theorem sigmaD_not_rotation : IsRot sigmaD = false := by decide

theorem mirror_involutive : ∀ x : Cell, mirror (mirror x) = x := by native_decide

/-- The mirror fixes four of the twenty-four cells. -/
theorem mirror_fixed_card :
    (univ.filter fun x : Cell => mirror x = x).card = 4 := by native_decide

/-- The other twenty are transposed, in ten pairs. -/
theorem mirror_moved_card :
    (univ.filter fun x : Cell => mirror x ≠ x).card = 20 := by native_decide

/-! ## 2. Invariant sets, counted -/

/-- The invariant five-sets: five cells the mirror maps onto themselves. -/
def invFives : Finset (Finset Cell) :=
  (univ.powersetCard 5).filter fun s => s.image mirror = s

/-- **220 invariant five-sets**: one fixed cell and two pairs (`4 · 45`), or
three fixed cells and one pair (`4 · 10`). -/
theorem invFives_card : invFives.card = 220 := by native_decide

/-- The invariant eight-sets: candidates for an octad of a mirror-invariant
Golay code. -/
def invOctads : Finset (Finset Cell) :=
  ((univ : Finset Cell).powersetCard 8).filter fun t => t.image mirror = t

/-- The invariant five-subsets of a set of cells. -/
def fibre (t : Finset Cell) : Finset (Finset Cell) :=
  (t.powersetCard 5).filter fun s => s.image mirror = s

/-- How many invariant five-subsets a set of cells holds. -/
def fibreCard (t : Finset Cell) : Nat := (fibre t).card

/-- There are 975 invariant eight-sets: `C(10,4)` with no fixed cell, `6·C(10,3)`
with two, and `C(10,2)` with all four. -/
theorem invOctads_card : invOctads.card = 975 := by native_decide

/-- No invariant eight-set has a fibre outside the multiples of six.  Stated as
an empty count because a `Finset` cardinality compiles to a loop, while a
decidable `∀` over 975 sets does not. -/
theorem no_fibre_off_six :
    (invOctads.filter fun t => fibreCard t % 6 ≠ 0).card = 0 := by native_decide

/-- Every invariant eight-set holds 0, 6 or 12 invariant five-subsets — a
multiple of six either way. -/
theorem fibre_card_dvd_six {t : Finset Cell} (hcard : t.card = 8)
    (hinv : t.image mirror = t) : 6 ∣ fibreCard t := by
  have hmem : t ∈ invOctads :=
    mem_filter.mpr ⟨mem_powersetCard_univ.mpr hcard, hinv⟩
  by_contra hdvd
  have hbad : t ∈ invOctads.filter fun t => fibreCard t % 6 ≠ 0 :=
    mem_filter.mpr ⟨hmem, by simpa [Nat.dvd_iff_mod_eq_zero] using hdvd⟩
  have hpos := Finset.card_pos.mpr ⟨t, hbad⟩
  rw [no_fibre_off_six] at hpos
  exact absurd hpos (lt_irrefl 0)

/-! ## 3. No mirror-invariant Golay code on the surface -/

/-- **The ceiling.**  There is no family of octads on the cube's 24 surface
cells that has the Steiner property of a Golay code and is closed under the
diagonal mirror.

The hypotheses are exactly what a Golay code supplies: its octads have eight
cells (`hcard`), every five-set lies in exactly one of them (`hsteiner` — the
`S(5, 8, 24)` design), and the family is carried to itself by the symmetry under
consideration (`hclosed`), which is what "the code is invariant" means.  No
generator matrix, no placement and no linearity is used, so the conclusion holds
for every Golay code on the surface at once. -/
theorem no_mirror_invariant_steiner
    (F : Finset (Finset Cell))
    (hcard : ∀ t ∈ F, t.card = 8)
    (hclosed : ∀ t ∈ F, t.image mirror ∈ F)
    (hsteiner : ∀ s : Finset Cell, s.card = 5 → ∃! t, t ∈ F ∧ s ⊆ t) :
    False := by
  classical
  -- the invariant five-sets are exactly the invariant five-subsets of octads
  have hunion : invFives = F.biUnion fibre := by
    ext s
    simp only [invFives, fibre, mem_filter, mem_powersetCard, mem_biUnion,
      subset_univ, true_and]
    constructor
    · rintro ⟨hs5, hsinv⟩
      obtain ⟨t, ⟨htF, hst⟩, -⟩ := hsteiner s hs5
      exact ⟨t, htF, ⟨hst, hs5⟩, hsinv⟩
    · rintro ⟨t, -, ⟨-, hs5⟩, hsinv⟩
      exact ⟨hs5, hsinv⟩
  -- distinct octads share no invariant five-set
  have hdisj : ∀ t₁ ∈ F, ∀ t₂ ∈ F, t₁ ≠ t₂ → Disjoint (fibre t₁) (fibre t₂) := by
    intro t₁ h₁ t₂ h₂ hne
    refine disjoint_left.mpr ?_
    intro s hs₁ hs₂
    simp only [fibre, mem_filter, mem_powersetCard] at hs₁ hs₂
    obtain ⟨t, -, huniq⟩ := hsteiner s hs₁.1.2
    exact hne ((huniq t₁ ⟨h₁, hs₁.1.1⟩).trans (huniq t₂ ⟨h₂, hs₂.1.1⟩).symm)
  -- every fibre is a multiple of six
  have hsix : ∀ t ∈ F, 6 ∣ (fibre t).card := by
    intro t htF
    rcases Finset.eq_empty_or_nonempty (fibre t) with hempty | ⟨s, hs⟩
    · simp [hempty]
    · have hs' := hs
      simp only [fibre, mem_filter, mem_powersetCard] at hs'
      obtain ⟨⟨hst, hs5⟩, hsinv⟩ := hs'
      obtain ⟨t', -, huniq⟩ := hsteiner s hs5
      -- the mirror image of `t` also contains `s`, so it is `t`
      have himg : t.image mirror ∈ F := hclosed t htF
      have hsub : s ⊆ t.image mirror := by
        calc s = s.image mirror := hsinv.symm
        _ ⊆ t.image mirror := image_subset_image hst
      have htinv : t.image mirror = t :=
        (huniq (t.image mirror) ⟨himg, hsub⟩).trans (huniq t ⟨htF, hst⟩).symm
      exact fibre_card_dvd_six (hcard t htF) htinv
  -- so six divides 220, which it does not
  have hsum : (220 : ℕ) = ∑ t ∈ F, (fibre t).card := by
    rw [← invFives_card, hunion, card_biUnion hdisj]
  have : (6 : ℕ) ∣ 220 := by
    rw [hsum]
    exact Finset.dvd_sum hsix
  omega

end GLM.CubeMirror
