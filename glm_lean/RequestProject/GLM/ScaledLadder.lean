import RequestProject.GLM.ConstructionLadder

/-!
# The scaled rungs: filling the gap between the checkerboard and Construction A

`GLM.ConstructionLadder` formalises the five rungs the attached note names, and
the diamond they make.  Those five leave one very long step: the checkerboard
lattice `D₂₄` has minimum norm `2` and Construction `A` has minimum norm `16`,
with nothing in between for a reading to stop at.

The step is an artefact of the *list*, not of the construction.  Construction
`A` over the trivial code is `2ℤ²⁴` and over the even-weight code it is `D₂₄`,
so the lattices that fill the step are Construction rungs too — and the
scaling `L ↦ 2L` generates as many more of them as are wanted.  This file is
that scaling, and the containments the thickened ladder rests on.

## §1 Scaling

`Dbl P` describes `2L` when `P` describes `L`, and `Scaled k P` describes
`2^k L`.  `dbl_mono` and `scaled_mono` say the scaling is monotone, which is
what lets one containment between base rungs be reused at every scale.

## §2 The unscaled Golay lift

In the integral (`×√8`) scaling this development uses, rung `A` is already
*twice* a lattice: `isA_iff_dbl_isG` proves `A = 2G`, where `IsG` asks that the
even coordinates of a vector form a Golay codeword.  So `G` is a rung of the
same family one step finer than `A`, and `2ℤ²⁴`, `2D₂₄`, `4ℤ²⁴` and `4D₂₄` are
the rungs between.

## §3 The containments

The one that carries the thickening is `isA_dbl_isD`: **Construction `A` sits
inside the doubled checkerboard lattice.**  It rests on the Golay code being
doubly even (`GLM.LatticeShortcut.golay_weight_div_four`): halving a vector of
`A` turns its coordinates outside the codeword odd, and there are `24 - w` of
them, which is even because `w` is.

The rest of the chain is proved beside it — `dbl_isZ_isG` (`2ℤ²⁴ ⊆ G`),
`isG_isD` (`G ⊆ D₂₄`), `isC_isG` (the Leech lattice is inside `G`, because all
its coordinates share a parity), `scaled_two_isZ_isA` (`4ℤ²⁴ ⊆ A`) and
`scaled_two_isD_isB` (`4D₂₄ ⊆ B`) — and `gap_chain` states the filled step as
one theorem: `A ⊆ 2D₂₄ ⊆ 2ℤ²⁴ ⊆ G ⊆ D₂₄ ⊆ ℤ²⁴`, five steps where the note had
one.
-/

namespace GLM.ScaledLadder

open GLM.ConstructionLadder GLM.LatticeShortcut

/-! ## §1 Scaling -/

/-- `Dbl P` describes the lattice `2L` when `P` describes `L`. -/
def Dbl (P : (Fin 24 → ℤ) → Prop) (x : Fin 24 → ℤ) : Prop :=
  ∃ y, P y ∧ ∀ i, x i = 2 * y i

/-- `Scaled k P` describes `2^k L` when `P` describes `L`. -/
def Scaled (k : ℕ) (P : (Fin 24 → ℤ) → Prop) : (Fin 24 → ℤ) → Prop := Dbl^[k] P

theorem scaled_zero (P : (Fin 24 → ℤ) → Prop) : Scaled 0 P = P := rfl

theorem scaled_succ (k : ℕ) (P : (Fin 24 → ℤ) → Prop) :
    Scaled (k + 1) P = Dbl (Scaled k P) := by
  simp [Scaled, Function.iterate_succ_apply']

/-- Scaling is monotone: a containment between two rungs is a containment
between their doubles. -/
theorem dbl_mono {P Q : (Fin 24 → ℤ) → Prop} (h : ∀ x, P x → Q x) :
    ∀ x, Dbl P x → Dbl Q x := by
  rintro x ⟨y, hy, hx⟩
  exact ⟨y, h y hy, hx⟩

theorem scaled_mono {P Q : (Fin 24 → ℤ) → Prop} (h : ∀ x, P x → Q x) :
    ∀ k x, Scaled k P x → Scaled k Q x := by
  intro k
  induction k with
  | zero => simpa [scaled_zero] using h
  | succ k ih =>
      intro x hx
      rw [scaled_succ] at hx ⊢
      exact dbl_mono ih x hx

/-! ## §2 The unscaled Golay lift `G` -/

/-- Rung `G`: the unscaled Golay lift — the even coordinates of the vector form
a Golay codeword.  Rung `A` is exactly `2G`. -/
def IsG (y : Fin 24 → ℤ) : Prop :=
  IsGolay (maskOf fun i => decide ((2 : ℤ) ∣ y i))

/-- **Construction `A` is the double of the unscaled Golay lift.** -/
theorem isA_iff_dbl_isG {x : Fin 24 → ℤ} : IsA x ↔ Dbl IsG x := by
  constructor
  · rintro ⟨heven, hgolay⟩
    have hhalf : ∀ i, x i = 2 * (x i / 2) := by
      intro i
      obtain ⟨c, hc⟩ := heven i
      omega
    refine ⟨fun i => x i / 2, ?_, hhalf⟩
    have hp : (fun i => decide ((2 : ℤ) ∣ x i / 2))
        = fun i => decide ((4 : ℤ) ∣ (x i - 0)) := by
      funext i
      have h2 := hhalf i
      simp only [sub_zero, decide_eq_decide]
      constructor
      · rintro ⟨d, hd⟩; exact ⟨d, by omega⟩
      · rintro ⟨d, hd⟩; exact ⟨d, by omega⟩
    simpa [IsG, hp] using hgolay
  · rintro ⟨y, hy, hx⟩
    refine ⟨fun i => ⟨y i, hx i⟩, ?_⟩
    have hp : (fun i => decide ((4 : ℤ) ∣ (x i - 0)))
        = fun i => decide ((2 : ℤ) ∣ y i) := by
      funext i
      have h2 := hx i
      simp only [sub_zero, decide_eq_decide]
      constructor
      · rintro ⟨d, hd⟩; exact ⟨d, by omega⟩
      · rintro ⟨d, hd⟩; exact ⟨d, by omega⟩
    rw [hp]
    exact hy

/-! ## §3 The containments the thickened ladder rests on -/

/-- The coordinate sum, modulo two, counts the odd coordinates. -/
private theorem sum_odd_card (y : Fin 24 → ℤ) :
    ∃ t : ℤ, ∑ i, y i
      = 2 * t + ((Finset.univ.filter fun i : Fin 24 => ¬ (2 : ℤ) ∣ y i).card : ℤ) := by
  classical
  refine ⟨∑ i, y i / 2, ?_⟩
  have hterm : ∀ i : Fin 24, y i = 2 * (y i / 2)
      + (if ¬ (2 : ℤ) ∣ y i then 1 else 0) := by
    intro i
    by_cases hd : (2 : ℤ) ∣ y i
    · simp only [hd, not_true_eq_false, if_false]
      omega
    · simp only [hd, not_false_eq_true, if_true]
      omega
  calc ∑ i, y i
      = ∑ i, (2 * (y i / 2) + (if ¬ (2 : ℤ) ∣ y i then 1 else 0)) :=
        Finset.sum_congr rfl fun i _ => hterm i
    _ = 2 * ∑ i, y i / 2
          + ((Finset.univ.filter fun i : Fin 24 => ¬ (2 : ℤ) ∣ y i).card : ℤ) := by
        rw [Finset.sum_add_distrib, ← Finset.mul_sum, Finset.sum_ite,
          Finset.sum_const, Finset.sum_const]
        simp

/-- **The unscaled Golay lift sits inside the checkerboard lattice.**  The
even coordinates form a codeword, so the odd ones are the `24 - w` positions
outside it, and `w` is even because the Golay code is doubly even. -/
theorem isG_isD {y : Fin 24 → ℤ} (h : IsG y) : IsD y := by
  classical
  have hpop : 4 ∣ pop (maskOf fun i => decide ((2 : ℤ) ∣ y i)) :=
    golay_weight_div_four h
  rw [pop_maskOf] at hpop
  have heven : (Finset.univ.filter fun i : Fin 24 => (2 : ℤ) ∣ y i).card
      = (Finset.univ.filter fun i : Fin 24 =>
          decide ((2 : ℤ) ∣ y i) = true).card := by
    simp
  have hodd : (Finset.univ.filter fun i : Fin 24 => ¬ (2 : ℤ) ∣ y i).card
      = 24 - (Finset.univ.filter fun i : Fin 24 => (2 : ℤ) ∣ y i).card := by
    have := Finset.card_filter_add_card_filter_not
      (s := (Finset.univ : Finset (Fin 24)))
      (p := fun i : Fin 24 => (2 : ℤ) ∣ y i)
    simp only [Finset.card_univ, Fintype.card_fin] at this
    omega
  obtain ⟨t, ht⟩ := sum_odd_card y
  refine ⟨t + (12 - ((Finset.univ.filter fun i : Fin 24 =>
    (2 : ℤ) ∣ y i).card : ℤ) / 2), ?_⟩
  rw [ht, hodd]
  have hle : (Finset.univ.filter fun i : Fin 24 => (2 : ℤ) ∣ y i).card ≤ 24 := by
    have := Finset.card_filter_le (Finset.univ : Finset (Fin 24))
      (fun i : Fin 24 => (2 : ℤ) ∣ y i)
    simpa using this
  have hpop' : 4 ∣ (Finset.univ.filter fun i : Fin 24 => (2 : ℤ) ∣ y i).card := by
    rw [heven]; exact hpop
  obtain ⟨k, hk⟩ := hpop'
  rw [hk]
  push_cast
  omega

/-- **Construction `A` sits inside the doubled checkerboard lattice.**  This is
the containment that fills the note's long step, and it is the Golay code's
doubly-even weight that forces it. -/
theorem isA_dbl_isD {x : Fin 24 → ℤ} (h : IsA x) : Dbl IsD x := by
  obtain ⟨y, hy, hx⟩ := isA_iff_dbl_isG.mp h
  exact ⟨y, isG_isD hy, hx⟩

/-- **`2ℤ²⁴` sits inside the unscaled Golay lift**: every coordinate is even,
so the mask is the all-ones word, which is a codeword. -/
theorem dbl_isZ_isG : ∀ x : Fin 24 → ℤ, Dbl IsZ x → IsG x := by
  rintro x ⟨y, -, hx⟩
  have hp : (fun i => decide ((2 : ℤ) ∣ x i)) = fun _ => true := by
    funext i
    have := hx i
    simp [this]
  have hmask : (maskOf fun i => decide ((2 : ℤ) ∣ x i)) = 2 ^ 24 - 1 := by
    rw [hp, maskOf]; decide
  simpa [IsG, hmask] using golay_allOnes

/-- **The Leech lattice sits inside the unscaled Golay lift**: all its
coordinates share a parity, so the even ones are none of them or all of them,
and both the zero word and the all-ones word are codewords. -/
theorem isC_isG {x : Fin 24 → ℤ} (h : IsC x) : IsG x := by
  obtain ⟨m, hm, hpar, -, -⟩ := h
  rcases hm with hm | hm
  · subst hm
    have hp : (fun i => decide ((2 : ℤ) ∣ x i)) = fun _ => true := by
      funext i
      have := hpar i
      simp only [sub_zero] at this
      simp [this]
    have hmask : (maskOf fun i => decide ((2 : ℤ) ∣ x i)) = 2 ^ 24 - 1 := by
      rw [hp, maskOf]; decide
    simpa [IsG, hmask] using golay_allOnes
  · subst hm
    have hp : (fun i => decide ((2 : ℤ) ∣ x i)) = fun _ => false := by
      funext i
      obtain ⟨c, hc⟩ := hpar i
      have : ¬ (2 : ℤ) ∣ x i := by
        rintro ⟨d, hd⟩; omega
      simp [this]
    have hmask : (maskOf fun i => decide ((2 : ℤ) ∣ x i)) = 0 := by
      rw [hp, maskOf]; decide
    simpa [IsG, hmask] using golay_zero

/-- **`4ℤ²⁴ ⊆ A`**: Construction `A` over the trivial code.  Every coordinate
divisible by `4` makes the mod-4 support the all-ones codeword. -/
theorem scaled_two_isZ_isA : ∀ x : Fin 24 → ℤ, Scaled 2 IsZ x → IsA x := by
  intro x hx
  rw [scaled_succ] at hx
  obtain ⟨y, hy, hxy⟩ := hx
  exact isA_iff_dbl_isG.mpr ⟨y, dbl_isZ_isG y hy, hxy⟩

/-- **`4D₂₄ ⊆ B`**: every coordinate divisible by `4` gives the all-ones
codeword, and the coordinate sum is four times an even number. -/
theorem scaled_two_isD_isB : ∀ x : Fin 24 → ℤ, Scaled 2 IsD x → IsB x := by
  intro x hx
  rw [scaled_succ] at hx
  obtain ⟨y, hy, hxy⟩ := hx
  rw [scaled_succ] at hy
  obtain ⟨z, hz, hyz⟩ := hy
  have hx4 : ∀ i, x i = 4 * z i := by
    intro i
    have h1 := hxy i
    have h2 := hyz i
    omega
  constructor
  · refine ⟨fun i => ⟨2 * z i, by rw [hx4 i]; ring⟩, ?_⟩
    have hp : (fun i => decide ((4 : ℤ) ∣ (x i - 0))) = fun _ => true := by
      funext i
      have h4 : (4 : ℤ) ∣ x i := ⟨z i, hx4 i⟩
      simp [sub_zero, h4]
    have hmask : (maskOf fun i => decide ((4 : ℤ) ∣ (x i - 0))) = 2 ^ 24 - 1 := by
      rw [hp, maskOf]; decide
    rw [hmask]
    exact golay_allOnes
  · obtain ⟨t, ht⟩ := hz
    refine ⟨t, ?_⟩
    have : ∑ i, x i = 4 * ∑ i, z i := by
      rw [Finset.mul_sum]
      exact Finset.sum_congr rfl fun i _ => hx4 i
    rw [this, ht]; ring

/-- **The filled step, as one statement.**  Where the note had a single jump
from the checkerboard lattice to Construction `A`, the thickened ladder has
five: `A ⊆ 2D₂₄ ⊆ 2ℤ²⁴ ⊆ G ⊆ D₂₄ ⊆ ℤ²⁴`. -/
theorem gap_chain :
    (∀ x : Fin 24 → ℤ, IsA x → Dbl IsD x)
      ∧ (∀ x : Fin 24 → ℤ, Dbl IsD x → Dbl IsZ x)
      ∧ (∀ x : Fin 24 → ℤ, Dbl IsZ x → IsG x)
      ∧ (∀ y : Fin 24 → ℤ, IsG y → IsD y)
      ∧ (∀ y : Fin 24 → ℤ, IsD y → IsZ y) :=
  ⟨fun _ h => isA_dbl_isD h,
   dbl_mono fun _ h => isD_isZ h,
   dbl_isZ_isG,
   fun _ h => isG_isD h,
   fun _ h => isD_isZ h⟩

end GLM.ScaledLadder
