import FirstPrinciples.Distinction

set_option autoImplicit false

/-!
# Stage 1 — the only metric the substrate has, and what it can correct

Once the substrate is a field of `n` binary cells with toggling as its dynamics
(Stage 0), a notion of "how far apart" two states are is not a modelling choice
either: the number of cells that must be toggled to get from one state to the
other *is* the Hamming distance, and it is a metric, invariant under the
substrate's own dynamics.

Findings proved here (FP-8 … FP-12):

* **FP-8** Toggle-count is a metric: symmetric, zero exactly on equal states,
  and subadditive (`dist_comm'`, `dist_eq_zero_iff`, `dist_triangle'`).
* **FP-9** It is invariant under the substrate's dynamics, and therefore is
  determined by a weight function on states alone
  (`dist_translation_invariant`, `dist_eq_weight`).
* **FP-10** Unique decoding: a set of admissible states whose members are at
  least `2t+1` apart is unambiguously recoverable from any state within `t`
  toggles (`unique_decoding`).  This, and only this, is what "error correction"
  can mean on a binary substrate.
* **FP-11** The correction radius is `⌊(d−1)/2⌋`; for `d = 7` and for `d = 8`
  it is the same number, `3` (`radius_of_seven`, `radius_of_eight`).
* **FP-12** At even minimum distance the extra unit of distance is provably not
  usable for correction: whenever two admissible states are exactly `2t+2`
  apart there is a state equidistant from both, at distance `t+1`
  (`even_distance_ambiguity`).  Hence the 24th coordinate of the extended Golay
  code buys *detection*, never *correction* — a point the study's "24-bit
  OffBit" narrative elides.
-/

namespace UBPFirstPrinciples

open Finset

variable {n : ℕ}

/-! ## FP-8  Toggle count is a metric -/

theorem dist_eq_zero_iff (x y : Bits n) : hammingDist x y = 0 ↔ x = y :=
  hammingDist_eq_zero

theorem dist_comm' (x y : Bits n) : hammingDist x y = hammingDist y x :=
  hammingDist_comm x y

theorem dist_triangle' (x y z : Bits n) :
    hammingDist x z ≤ hammingDist x y + hammingDist y z :=
  hammingDist_triangle x y z

/-! ## FP-9  Invariance under the dynamics -/

/-- Toggling the same pattern into both arguments does not change the
distance. -/
theorem dist_translation_invariant (x y z : Bits n) :
    hammingDist (x + z) (y + z) = hammingDist x y := by
  simp [hammingDist]

/-- Consequently the metric is a *weight*: the distance between two states is
the number of cells of their difference that are on. -/
theorem dist_eq_weight (x y : Bits n) : hammingDist x y = hammingNorm (x - y) := by
  have h := dist_translation_invariant x y (-y)
  simpa [sub_eq_add_neg, hammingDist_zero_right] using h.symm

/-! ## FP-10  Unique decoding -/

/-- `MinDist C d` : distinct admissible states are at least `d` toggles apart. -/
def MinDist (C : Set (Bits n)) (d : ℕ) : Prop :=
  ∀ c₁ ∈ C, ∀ c₂ ∈ C, c₁ ≠ c₂ → d ≤ hammingDist c₁ c₂

/-- If admissible states are `2t+1` apart, then no state is within `t` toggles
of two of them: decoding inside radius `t` is unambiguous. -/
theorem unique_decoding {C : Set (Bits n)} {d t : ℕ} (hC : MinDist C d)
    (ht : 2 * t + 1 ≤ d) (v : Bits n) {c₁ c₂ : Bits n} (h₁ : c₁ ∈ C) (h₂ : c₂ ∈ C)
    (hv₁ : hammingDist v c₁ ≤ t) (hv₂ : hammingDist v c₂ ≤ t) : c₁ = c₂ := by
  by_contra hne
  have hd : d ≤ hammingDist c₁ c₂ := hC c₁ h₁ c₂ h₂ hne
  have htri : hammingDist c₁ c₂ ≤ hammingDist c₁ v + hammingDist v c₂ :=
    hammingDist_triangle c₁ v c₂
  rw [hammingDist_comm c₁ v] at htri
  omega

/-! ## FP-11  The correction radius -/

theorem radius_of_seven : (7 - 1) / 2 = 3 := by norm_num
theorem radius_of_eight : (8 - 1) / 2 = 3 := by norm_num

/-- Both a minimum distance of `7` and a minimum distance of `8` give exactly
the same guarantee: every error pattern of weight `≤ 3` is corrected. -/
theorem correction_radius_three {C : Set (Bits n)} (hC : MinDist C 7) (v : Bits n)
    {c₁ c₂ : Bits n} (h₁ : c₁ ∈ C) (h₂ : c₂ ∈ C)
    (hv₁ : hammingDist v c₁ ≤ 3) (hv₂ : hammingDist v c₂ ≤ 3) : c₁ = c₂ :=
  unique_decoding hC (by norm_num) v h₁ h₂ hv₁ hv₂

/-! ## FP-12  Even minimum distance is not fully usable -/

/-- If two admissible states are at even distance `2t+2`, some state is
equidistant from both at distance `t+1`: the last unit of an even minimum
distance can only ever be used for *detection*. -/
theorem even_distance_ambiguity {c₁ c₂ : Bits n} {t : ℕ}
    (h : hammingDist c₁ c₂ = 2 * t + 2) :
    ∃ v, hammingDist v c₁ = t + 1 ∧ hammingDist v c₂ = t + 1 := by
  classical
  set S : Finset (Fin n) := univ.filter (fun i => c₁ i ≠ c₂ i) with hS
  have hcard : S.card = 2 * t + 2 := h
  obtain ⟨T, hTS, hT⟩ := Finset.exists_subset_card_eq (s := S) (n := t + 1) (by omega)
  refine ⟨fun i => if i ∈ T then c₂ i else c₁ i, ?_, ?_⟩
  · have : (univ.filter (fun i => (if i ∈ T then c₂ i else c₁ i) ≠ c₁ i)) = T := by
      ext i
      simp only [mem_filter, mem_univ, true_and]
      by_cases hi : i ∈ T
      · have : i ∈ S := hTS hi
        rw [hS] at this
        simp only [mem_filter, mem_univ, true_and] at this
        simp [hi, Ne.symm this]
      · simp [hi]
    rw [show hammingDist (fun i => if i ∈ T then c₂ i else c₁ i) c₁ = T.card by
      simp only [hammingDist, this], hT]
  · have : (univ.filter (fun i => (if i ∈ T then c₂ i else c₁ i) ≠ c₂ i)) = S \ T := by
      ext i
      simp only [mem_filter, mem_univ, true_and, mem_sdiff, hS]
      by_cases hi : i ∈ T
      · simp [hi]
      · simp [hi]
    rw [show hammingDist (fun i => if i ∈ T then c₂ i else c₁ i) c₂ = (S \ T).card by
      simp only [hammingDist, this], Finset.card_sdiff_of_subset hTS, hcard, hT]
    omega

end UBPFirstPrinciples
