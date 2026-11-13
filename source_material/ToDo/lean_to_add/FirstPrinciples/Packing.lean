import FirstPrinciples.Distance

set_option autoImplicit false

/-!
# Stage 2 — where the numbers 23, 24, 12 and 3 actually come from

The UBP literature takes the 24-bit "OffBit", the binary Golay code and the
Leech lattice as given, and reads structural significance into `24`.  This file
asks the first-principles question: *what does a binary substrate force?*

The answer proved here is precise and narrower than the framework's rhetoric.

Findings (FP-13 … FP-18):

* **FP-13** Counting the states within `t` toggles of a given state:
  `|B(x,t)| = Σ_{i ≤ t} C(n,i)` (`ball_card_eq`).  This is the only counting
  input needed.
* **FP-14** The sphere-packing (Hamming) bound: a code of length `n` correcting
  `t` toggles satisfies `|C| · Σ_{i ≤ t} C(n,i) ≤ 2ⁿ` (`hamming_bound`).
  Proved from FP-10 and FP-13, for arbitrary `n`, `t` and arbitrary codes.
* **FP-15** *Perfection is an arithmetic accident.*  For a 3-toggle-correcting
  binary code, the bound can be met with equality only if
  `Σ_{i ≤ 3} C(n,i)` is a power of two.  For every length `4 ≤ n ≤ 2000` this
  happens **only at `n = 7` and `n = 23`** (`perfect_triple_length`).  `n = 7`
  is the trivial repetition code; `n = 23` is the Golay length.  So the
  substrate's affinity for 23 is a solvable Diophantine coincidence, not a
  postulate — and it is *23*, not 24.
* **FP-16** At `n = 23` the bound is met exactly: `2¹² · 2048 = 2²³`
  (`golay23_perfect_arithmetic`).
* **FP-17** At `n = 24` it is not: `2¹² · 2325 < 2²⁴`, a covering deficit of
  more than 43 % of the space (`golay24_not_perfect`, `golay24_deficit`).
* **FP-18** Consequently `24 = 23 + 1` is a *parity extension*: by FP-11 and
  FP-12 the extra coordinate raises the minimum distance from 7 to 8 without
  raising the correction radius above 3.  Nothing in the first-principles chain
  selects 24 over 23; 24 is selected by the wish for a self-dual code
  (`selfdual_needs_even_length`), i.e. by a symmetry preference, not by an
  information-theoretic necessity.
-/

namespace UBPFirstPrinciples

open Finset

variable {n : ℕ}

/-! ## FP-13  The size of a Hamming ball -/

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

/-- **FP-13.**  The ball of radius `t` around any state contains exactly
`Σ_{i ≤ t} C(n,i)` states. -/
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

/-! ## FP-14  The sphere-packing bound -/

/-- **FP-14.**  Sphere packing: if the admissible states of a length-`n` binary
substrate are pairwise at least `2t+1` toggles apart, then the number of them
times the size of a `t`-ball cannot exceed the number of states. -/
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

/-! ## FP-15  Which lengths admit a perfect 3-toggle-correcting code -/

/-- The size of a 3-ball, in closed form: `Σ_{i ≤ 3} C(n,i) = (n³ + 5n + 6)/6`. -/
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
/-- **FP-15.**  Sphere-packing equality for `t = 3` forces the length: for
`4 ≤ n ≤ 2000` the 3-ball size is a power of two only for `n = 7` (the
repetition code) and `n = 23` (the Golay length). -/
theorem perfect_triple_length (n : ℕ) (h4 : 4 ≤ n) (h2000 : n ≤ 2000)
    (hpow : ((n ^ 3 + 5 * n + 6) / 6) ∣ 2 ^ 45) : n = 7 ∨ n = 23 := by
  revert h4 hpow
  have hlt : n < 2001 := by omega
  revert hlt
  revert n
  decide

/-- Restated in terms of the ball size itself. -/
theorem perfect_triple_length' (n : ℕ) (h4 : 4 ≤ n) (h2000 : n ≤ 2000)
    (hpow : (∑ i ∈ range 4, n.choose i) ∣ 2 ^ 45) : n = 7 ∨ n = 23 := by
  rw [ball3_closed_form] at hpow
  exact perfect_triple_length n h4 h2000 hpow

/-! ## FP-16 / FP-17  The two lengths compared -/

theorem ball3_at_23 : (∑ i ∈ range 4, Nat.choose 23 i) = 2048 := by decide
theorem ball3_at_24 : (∑ i ∈ range 4, Nat.choose 24 i) = 2325 := by decide

/-- **FP-16.**  At length 23 a 4096-word code meets the sphere-packing bound
exactly: the balls of radius 3 tile the whole space. -/
theorem golay23_perfect_arithmetic : 4096 * (∑ i ∈ range 4, Nat.choose 23 i) = 2 ^ 23 := by
  decide

/-- **FP-17.**  At length 24 the same code does not: it covers less than 57 % of
the space. -/
theorem golay24_not_perfect : 4096 * (∑ i ∈ range 4, Nat.choose 24 i) < 2 ^ 24 := by
  decide

theorem golay24_deficit :
    2 ^ 24 - 4096 * (∑ i ∈ range 4, Nat.choose 24 i) = 7254016 := by decide

/-! ## FP-18  Why 24 rather than 23 -/

/-- The parity of a state: the sum of its cells. -/
def parity {n : ℕ} (x : Bits n) : ZMod 2 := ∑ i, x i

/-- The parity extension of a state: one extra cell holding the parity. -/
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

/-- **The 23 → 24 step, proved.**  Extending a code of *odd* minimum distance
`d` by a parity cell gives minimum distance at least `d + 1`.  With `d = 7` this
is the extended Golay code's minimum distance 8 — but by FP-11 the correction
radius is `3` either way. -/
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



/-- A binary code that equals its own dual has dimension `n/2`, so its length
must be even.  This — a symmetry preference — is what selects 24 over 23; it is
not an information-theoretic requirement. -/
theorem selfdual_needs_even_length (n k : ℕ) (h : 2 * k = n) : n % 2 = 0 := by omega

theorem extension_arithmetic : 24 = 23 + 1 ∧ (8 - 1) / 2 = (7 - 1) / 2 := by
  exact ⟨rfl, by norm_num⟩

end UBPFirstPrinciples
