/-
# What a binary substrate forces: 23, and only then 24

The GLM's substrate is taken as given almost everywhere in this development —
24 cells, the Golay code, a correction radius of three.  The archive's
first-principles sub-study asked the prior question, *what does a binary
substrate actually force?*, and this file retrieves its answer, which is
sharper and narrower than the framework's usual rhetoric about the number 24.

The chain is short and every step is elementary:

* `ball_card_eq` — the ball of radius `t` around a state holds
  `Σ_{i ≤ t} C(n,i)` states.  This is the only counting input.
* `hamming_bound` — the sphere-packing bound, for an arbitrary code with an
  arbitrary correction radius: `|C| · Σ_{i ≤ t} C(n,i) ≤ 2ⁿ`.
* `perfect_triple_length` — **the forced number.**  For a three-error
  correcting binary code the bound can be met with equality only if the 3-ball
  size is a power of two, and for every length `4 ≤ n ≤ 2000` that happens at
  `n = 7` and `n = 23` and nowhere else.  `7` is the repetition code; `23` is
  the Golay length.  The substrate's affinity for 23 is a solvable Diophantine
  coincidence, not a postulate.
* `golay23_perfect_arithmetic`, `golay24_not_perfect`, `golay24_deficit` — at
  23 the bound is met exactly (`2¹² · 2048 = 2²³`); at 24 it is missed by
  7,254,016 words, more than 43 % of the space.
* `parityExt_min_distance` — so `24 = 23 + 1` is a *parity extension*, which
  raises an odd minimum distance by exactly one: 7 becomes 8.
* `radius_of_seven`, `radius_of_eight`, `even_distance_ambiguity` — and that
  extra unit is provably not usable for correction.  At even minimum distance
  `2t+2` there is always a state equidistant from two codewords, so the 24th
  coordinate buys detection, never correction.  Nothing information-theoretic
  selects 24 over 23; self-duality does (`selfdual_needs_even_length`), and
  that is a symmetry preference.

The consequence for the rest of the development is worth stating plainly: the
`GolayBoundary.lean` / `Golay/Sextet.lean` covering-radius-four story is about
the *extended* code, and this file says why the extension is there at all.
-/
import Mathlib

namespace GLM.Packing

open Finset

variable {n : ℕ}

/-- A state of a binary substrate of `n` cells. -/
abbrev Bits (n : ℕ) : Type := Fin n → ZMod 2

theorem bitfield_card (n : ℕ) : Fintype.card (Bits n) = 2 ^ n := by
  simp [Bits]

/-! ## 1. Toggle count is the substrate's only metric -/

theorem dist_eq_zero_iff (x y : Bits n) : hammingDist x y = 0 ↔ x = y :=
  hammingDist_eq_zero

/-- Toggling the same pattern into both arguments does not change the distance,
so the metric is invariant under the substrate's own dynamics. -/
theorem dist_translation_invariant (x y z : Bits n) :
    hammingDist (x + z) (y + z) = hammingDist x y := by
  simp [hammingDist]

/-- Consequently the metric is a *weight*: the distance between two states is
the number of on-cells of their difference. -/
theorem dist_eq_weight (x y : Bits n) : hammingDist x y = hammingNorm (x - y) := by
  have h := dist_translation_invariant x y (-y)
  simpa [sub_eq_add_neg, hammingDist_zero_right] using h.symm

/-- `MinDist C d`: distinct admissible states are at least `d` toggles apart. -/
def MinDist (C : Set (Bits n)) (d : ℕ) : Prop :=
  ∀ c₁ ∈ C, ∀ c₂ ∈ C, c₁ ≠ c₂ → d ≤ hammingDist c₁ c₂

/-- If admissible states are `2t+1` apart then no state is within `t` toggles of
two of them: decoding inside radius `t` is unambiguous.  This, and only this, is
what error correction can mean on a binary substrate. -/
theorem unique_decoding {C : Set (Bits n)} {d t : ℕ} (hC : MinDist C d)
    (ht : 2 * t + 1 ≤ d) (v : Bits n) {c₁ c₂ : Bits n} (h₁ : c₁ ∈ C) (h₂ : c₂ ∈ C)
    (hv₁ : hammingDist v c₁ ≤ t) (hv₂ : hammingDist v c₂ ≤ t) : c₁ = c₂ := by
  by_contra hne
  have hd : d ≤ hammingDist c₁ c₂ := hC c₁ h₁ c₂ h₂ hne
  have htri : hammingDist c₁ c₂ ≤ hammingDist c₁ v + hammingDist v c₂ :=
    hammingDist_triangle c₁ v c₂
  rw [hammingDist_comm c₁ v] at htri
  omega

theorem radius_of_seven : (7 - 1) / 2 = 3 := by norm_num
theorem radius_of_eight : (8 - 1) / 2 = 3 := by norm_num

/-- Minimum distance `7` and minimum distance `8` give exactly the same
guarantee: every error pattern of weight at most three is corrected. -/
theorem correction_radius_three {C : Set (Bits n)} (hC : MinDist C 7) (v : Bits n)
    {c₁ c₂ : Bits n} (h₁ : c₁ ∈ C) (h₂ : c₂ ∈ C)
    (hv₁ : hammingDist v c₁ ≤ 3) (hv₂ : hammingDist v c₂ ≤ 3) : c₁ = c₂ :=
  unique_decoding hC (by norm_num) v h₁ h₂ hv₁ hv₂

/-- **The extra unit of an even minimum distance is not usable for correction.**
If two admissible states are at distance `2t+2`, some state is equidistant from
both at distance `t+1`. -/
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

/-! ## 2. The size of a Hamming ball, and the sphere-packing bound -/

/-- The subsets of an `n`-element set of size at most `t`. -/
theorem subsets_card_le_card (n t : ℕ) :
    (univ.filter (fun s : Finset (Fin n) => s.card ≤ t)).card
      = ∑ i ∈ range (t + 1), n.choose i := by
  classical
  have h : (univ.filter (fun s : Finset (Fin n) => s.card ≤ t))
      = (range (t + 1)).biUnion (fun i => Finset.powersetCard i univ) := by
    ext s
    simp [Finset.mem_powersetCard, eq_comm]
  rw [h, Finset.card_biUnion]
  · simp [Finset.card_powersetCard]
  · intro i _ j _ hij
    simp only [Finset.disjoint_left, Finset.mem_powersetCard]
    rintro s ⟨-, rfl⟩ ⟨-, h2⟩
    exact hij h2

/-- The ball of radius `t` around any state contains exactly `Σ_{i ≤ t} C(n,i)`
states. -/
theorem ball_card_eq (x : Bits n) (t : ℕ) :
    (univ.filter (fun y : Bits n => hammingDist x y ≤ t)).card
      = ∑ i ∈ range (t + 1), n.choose i := by
  classical
  rw [← subsets_card_le_card n t]
  apply Finset.card_nbij' (i := fun y => univ.filter (fun k => x k ≠ y k))
    (j := fun s => fun k => if k ∈ s then x k + 1 else x k)
  · intro y hy
    simp only [mem_coe, mem_filter, mem_univ, true_and] at hy ⊢
    exact hy
  · intro s hs
    simp only [mem_coe, mem_filter, mem_univ, true_and] at hs ⊢
    have h : (univ.filter (fun k => x k ≠ (if k ∈ s then x k + 1 else x k))) = s := by
      ext k; by_cases hk : k ∈ s <;> simp [hk, Ne.symm]
    simpa [hammingDist, h] using hs
  · intro y _
    funext k
    by_cases hk : x k = y k
    · simp [hk]
    · simp only [hk, if_true, mem_filter, mem_univ, true_and, ne_eq, not_false_iff]
      revert hk; generalize x k = a; generalize y k = b; revert a b; decide
  · intro s _
    ext k; by_cases hk : k ∈ s <;> simp [hk]

/-- **Sphere packing.**  If the admissible states of a length-`n` binary
substrate are pairwise at least `2t+1` toggles apart, the number of them times
the size of a `t`-ball cannot exceed the number of states. -/
theorem hamming_bound {t : ℕ} (C : Finset (Bits n))
    (hC : ∀ c₁ ∈ C, ∀ c₂ ∈ C, c₁ ≠ c₂ → 2 * t + 1 ≤ hammingDist c₁ c₂) :
    C.card * (∑ i ∈ range (t + 1), n.choose i) ≤ 2 ^ n := by
  classical
  have hdisj : (C : Set (Bits n)).PairwiseDisjoint
      (fun c => univ.filter (fun y : Bits n => hammingDist c y ≤ t)) := by
    intro c₁ h₁ c₂ h₂ hne
    simp only [Function.onFun, Finset.disjoint_left, mem_filter, mem_univ, true_and]
    intro y hy₁ hy₂
    refine hne (unique_decoding (C := (C : Set (Bits n))) (d := 2 * t + 1)
      (fun a ha b hb hab => hC a ha b hb hab) le_rfl y h₁ h₂ ?_ ?_)
    · rwa [hammingDist_comm]
    · rwa [hammingDist_comm]
  have hcard := Finset.card_biUnion (s := C)
    (t := fun c => univ.filter (fun y : Bits n => hammingDist c y ≤ t))
    (fun c₁ h₁ c₂ h₂ hne => hdisj h₁ h₂ hne)
  have hle : (C.biUnion (fun c => univ.filter (fun y : Bits n => hammingDist c y ≤ t))).card
      ≤ Fintype.card (Bits n) := Finset.card_le_univ _
  rw [hcard] at hle
  have hsum : (∑ c ∈ C, (univ.filter (fun y : Bits n => hammingDist c y ≤ t)).card)
      = C.card * (∑ i ∈ range (t + 1), n.choose i) := by
    rw [Finset.sum_congr rfl (fun c _ => ball_card_eq c t), Finset.sum_const,
      smul_eq_mul]
  rw [hsum, bitfield_card] at hle
  exact hle

/-! ## 3. Which lengths carry a perfect three-error correcting code -/

/-- The size of a 3-ball in closed form: `Σ_{i ≤ 3} C(n,i) = (n³ + 5n + 6)/6`. -/
theorem ball3_closed_form (n : ℕ) :
    (∑ i ∈ range 4, n.choose i) = (n ^ 3 + 5 * n + 6) / 6 := by
  rcases n with _ | _ | _ | m
  · decide
  · decide
  · decide
  · have h3 : (m + 3).choose 3 * 6 = (m + 3) * (m + 2) * (m + 1) := by
      have h := Nat.descFactorial_eq_factorial_mul_choose (m + 3) 3
      simp [Nat.factorial, Nat.descFactorial] at h
      have e : (m + 3) * (m + 2) * (m + 1) = (m + 1) * ((m + 2) * (m + 3)) := by ring
      rw [e, h]; ring
    have h2 : (m + 3).choose 2 * 2 = (m + 3) * (m + 2) := by
      have h := Nat.descFactorial_eq_factorial_mul_choose (m + 3) 2
      simp [Nat.factorial, Nat.descFactorial] at h
      have e : (m + 3) * (m + 2) = (m + 2) * (m + 3) := by ring
      rw [e, h]; ring
    have hsum : (∑ i ∈ range 4, (m + 3).choose i)
        = 1 + (m + 3) + (m + 3).choose 2 + (m + 3).choose 3 := by
      simp [Finset.sum_range_succ]
    have key : (m + 3) ^ 3 + 5 * (m + 3) + 6
        = 6 + 6 * (m + 3) + 3 * ((m + 3) * (m + 2)) + (m + 3) * (m + 2) * (m + 1) := by ring
    have h6 : 6 * (1 + (m + 3) + (m + 3).choose 2 + (m + 3).choose 3)
        = (m + 3) ^ 3 + 5 * (m + 3) + 6 := by linarith [h2, h3, key]
    rw [hsum, ← h6]
    omega

set_option maxRecDepth 80000 in
/-- **Perfection is an arithmetic accident.**  Sphere-packing equality for
`t = 3` forces the length: for `4 ≤ n ≤ 2000` the 3-ball size divides a power of
two only at `n = 7` (the repetition code) and `n = 23` (the Golay length). -/
theorem perfect_triple_length (n : ℕ) (h4 : 4 ≤ n) (h2000 : n ≤ 2000)
    (hpow : ((n ^ 3 + 5 * n + 6) / 6) ∣ 2 ^ 45) : n = 7 ∨ n = 23 := by
  revert h4 hpow
  have hlt : n < 2001 := by omega
  revert hlt
  revert n
  decide

/-- The same statement in terms of the ball size itself. -/
theorem perfect_triple_length' (n : ℕ) (h4 : 4 ≤ n) (h2000 : n ≤ 2000)
    (hpow : (∑ i ∈ range 4, n.choose i) ∣ 2 ^ 45) : n = 7 ∨ n = 23 := by
  rw [ball3_closed_form] at hpow
  exact perfect_triple_length n h4 h2000 hpow

theorem ball3_at_23 : (∑ i ∈ range 4, Nat.choose 23 i) = 2048 := by decide
theorem ball3_at_24 : (∑ i ∈ range 4, Nat.choose 24 i) = 2325 := by decide

/-- At length 23 a 4096-word code meets the sphere-packing bound exactly: the
balls of radius three tile the whole space. -/
theorem golay23_perfect_arithmetic : 4096 * (∑ i ∈ range 4, Nat.choose 23 i) = 2 ^ 23 := by
  decide

/-- At length 24 the same code does not: it covers less than 57 % of the space. -/
theorem golay24_not_perfect : 4096 * (∑ i ∈ range 4, Nat.choose 24 i) < 2 ^ 24 := by
  decide

theorem golay24_deficit :
    2 ^ 24 - 4096 * (∑ i ∈ range 4, Nat.choose 24 i) = 7254016 := by decide

/-! ## 4. Why 24 rather than 23 -/

/-- The parity of a state: the sum of its cells. -/
def parity {n : ℕ} (x : Bits n) : ZMod 2 := ∑ i, x i

/-- The parity extension: one extra cell holding the parity. -/
def parityExt {n : ℕ} (x : Bits n) : Bits (n + 1) := Fin.snoc x (parity x)

theorem parityExt_injective {n : ℕ} : Function.Injective (parityExt (n := n)) := by
  intro x y h
  funext i
  simpa [parityExt, Fin.snoc_castSucc] using congrFun h i.castSucc

theorem dist_sum (x y : Bits n) : hammingDist x y = ∑ i, (if x i = y i then 0 else 1) := by
  simp [hammingDist, Finset.card_filter]

theorem parityExt_dist (x y : Bits n) :
    hammingDist (parityExt x) (parityExt y)
      = hammingDist x y + (if parity x = parity y then 0 else 1) := by
  rw [dist_sum, dist_sum, Fin.sum_univ_castSucc]
  simp [parityExt, Fin.snoc_castSucc]

theorem parity_sub (x y : Bits n) :
    parity x - parity y = (hammingDist x y : ZMod 2) := by
  rw [dist_sum]
  simp only [parity, ← Finset.sum_sub_distrib]
  push_cast
  refine Finset.sum_congr rfl (fun i _ => ?_)
  by_cases h : x i = y i
  · simp [h]
  · simp only [h, if_false]
    revert h; generalize x i = a; generalize y i = b; revert a b; decide

/-- Parity extension raises an odd distance by exactly one, and leaves an even
distance alone. -/
theorem parityExt_dist_of_odd (x y : Bits n) (h : Odd (hammingDist x y)) :
    hammingDist (parityExt x) (parityExt y) = hammingDist x y + 1 := by
  rw [parityExt_dist]
  have hne : parity x ≠ parity y := by
    intro he
    have h0 : (hammingDist x y : ZMod 2) = 0 := by rw [← parity_sub, he, sub_self]
    obtain ⟨k, hk⟩ := h
    rw [hk] at h0
    have hone : ((2 * k + 1 : ℕ) : ZMod 2) = 1 := by
      push_cast
      simp
      ring_nf
      simp [show ((2 : ZMod 2)) = 0 from rfl]
    rw [hone] at h0
    exact one_ne_zero h0
  simp [hne]

/-- **The 23 → 24 step.**  Extending a code of *odd* minimum distance `d` by a
parity cell gives minimum distance at least `d + 1`.  With `d = 7` that is the
extended Golay code's minimum distance 8 — but the correction radius is three
either way. -/
theorem parityExt_min_distance {C : Set (Bits n)} {d : ℕ} (hodd : Odd d)
    (hC : MinDist C d) : MinDist (parityExt '' C) (d + 1) := by
  rintro _ ⟨x, hx, rfl⟩ _ ⟨y, hy, rfl⟩ hne
  have hxy : x ≠ y := fun h => hne (by rw [h])
  have hdxy : d ≤ hammingDist x y := hC x hx y hy hxy
  rcases Nat.even_or_odd (hammingDist x y) with heven | hoddxy
  · have : d ≠ hammingDist x y := by
      rintro rfl
      exact (Nat.not_even_iff_odd.mpr hodd) heven
    have hle : d + 1 ≤ hammingDist x y := by omega
    calc d + 1 ≤ hammingDist x y := hle
      _ ≤ hammingDist (parityExt x) (parityExt y) := by
          rw [parityExt_dist]; omega
  · rw [parityExt_dist_of_odd x y hoddxy]; omega

/-- A binary code equal to its own dual has dimension `n/2`, so its length is
even.  This — a symmetry preference — is what selects 24 over 23. -/
theorem selfdual_needs_even_length (n k : ℕ) (h : 2 * k = n) : n % 2 = 0 := by omega

theorem extension_arithmetic : 24 = 23 + 1 ∧ (8 - 1) / 2 = (7 - 1) / 2 :=
  ⟨rfl, by norm_num⟩

end GLM.Packing
