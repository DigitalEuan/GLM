import Mathlib
import RequestProject.GLM.LeechShells

/-!
# Every Golay tie is a deep hole of the Leech lattice (Phase 182)

*Created 22 October 2026.*

The second formal half of `studies/LORENTZIAN_LIFT_STUDY.md`. The ambiguous
space the owner's `iter10_lorentzian.py` set out to resolve is the Golay
decoder's tie space: the 1771 of 4096 cosets of weight 4, `1771/4096 ≈ 43 %`
of all 24-bit words, where six codewords are equally near. The script embedded
a word as a `0/1` vector, which is not in the Leech lattice's scale. In the
coordinates of `LeechShells.lean` (`IsLeech`, squared length `normSq`, true
norm `normSq / 8`) the right embedding doubles it: `dbl b` is `2` on `b` and
`0` off it, and `dbl c` is a lattice vector for every codeword `c`.

* `normSq_dbl_sub` — `normSq (dbl b − dbl c) = 4 · hdist b c`;
* `dbl_isLeech` — `dbl c` is in the lattice for every codeword `c`;
* `leech_far` — every lattice vector `x` is at least `4 · hdist b c` from
  `dbl b` for some codeword `c`, or at least `24`;
* `leech_dist_coset_weight` — **the Leech distance of a doubled word is its
  Golay coset weight**: if `c` is a nearest codeword at Hamming distance
  `k ≤ 6`, then no lattice vector is nearer to `dbl b` than `4k`, and `dbl c`
  attains it. In true norm the squared distance is `k/2`;
* `golay_tie_deep_hole` — at coset weight `4` the squared distance is `16`,
  true norm `2`, which is the Leech covering radius squared (Conway, Parker
  and Sloane; cited, not proved here). So **every Golay tie is a deep hole**,
  and the six tied codewords are vertices of it;
* `summed_score_le` — summed Lorentzian scores over several readings never
  rank any codeword above one that is a nearest codeword of every reading.
-/

namespace GLM.GolayDeepHole

open Finset GLM.Golay24 GLM.LeechShells

/-- The doubled word: `2` on `b`, `0` off it. -/
def dbl (b : Word) : Fin 24 → ℤ := fun i => if i ∈ b then 2 else 0

lemma dbl_sub_sq (b c : Word) (i : Fin 24) :
    (dbl b i - dbl c i) ^ 2 = if i ∈ symmDiff b c then 4 else 0 := by
  unfold dbl
  by_cases hb : i ∈ b <;> by_cases hc : i ∈ c <;> simp [hb, hc, Finset.mem_symmDiff]

/-- **`normSq (dbl b − dbl c) = 4 · hdist b c`.** -/
theorem normSq_dbl_sub (b c : Word) : normSq (dbl b - dbl c) = 4 * (hdist b c : ℤ) := by
  unfold normSq hdist
  simp only [Pi.sub_apply, dbl_sub_sq]
  rw [← Finset.sum_filter, Finset.sum_const, nsmul_eq_mul]
  simp [mul_comm]

/-- **The doubled codeword is a lattice vector.** -/
theorem dbl_isLeech {c : Word} (hc : IsCodeword c) : IsLeech (dbl c) := by
  left
  refine ⟨fun i => ?_, ?_, ?_⟩
  · unfold dbl; split_ifs <;> decide
  · have : (univ.filter fun i => dbl c i % 4 = 2) = c := by
      ext i; unfold dbl; by_cases h : i ∈ c <;> simp [h]
    rw [this]; exact hc
  · have hs : (∑ i, dbl c i) = 2 * (c.card : ℤ) := by
      unfold dbl; rw [Finset.sum_ite_mem, Finset.univ_inter, Finset.sum_const, nsmul_eq_mul]
      ring
    rw [hs]
    obtain ⟨k, hk⟩ := GLM.Golay24.golay_doubly_even hc
    unfold wt at hk; rw [hk]; push_cast; omega

lemma four_le_sq (d : ℤ) (h : d % 4 = 2) : 4 ≤ d ^ 2 := by
  rcases (show 2 ≤ d ∨ d ≤ -2 by omega) with h1 | h1 <;> nlinarith

lemma one_le_sq (d : ℤ) (h : d % 2 = 1) : 1 ≤ d ^ 2 := by
  rcases (show 1 ≤ d ∨ d ≤ -1 by omega) with h1 | h1 <;> nlinarith

/-- **Every lattice vector is far from a doubled word**: at least `4 · hdist b c`
for the codeword `c` its residues mod 4 name, or at least `24` if it is odd. -/
theorem leech_far (b : Word) {x : Fin 24 → ℤ} (hx : IsLeech x) :
    (∃ c, IsCodeword c ∧ 4 * (hdist b c : ℤ) ≤ normSq (dbl b - x)) ∨
      24 ≤ normSq (dbl b - x) := by
  rcases hx with ⟨heven, hcw, -⟩ | ⟨hodd, -, -⟩
  · left
    set c := univ.filter fun i => x i % 4 = 2 with hcdef
    refine ⟨c, hcw, ?_⟩
    have hterm : ∀ i ∈ symmDiff b c, 4 ≤ (dbl b - x) i ^ 2 := by
      intro i hi
      apply four_le_sq
      have he := heven i
      rw [Finset.mem_symmDiff] at hi
      simp only [Pi.sub_apply, dbl, hcdef, mem_filter, mem_univ, true_and] at hi ⊢
      rcases hi with ⟨hb, hc⟩ | ⟨hc, hb⟩
      · rw [if_pos hb]; omega
      · rw [if_neg hb]; omega
    unfold normSq hdist
    calc 4 * ((symmDiff b c).card : ℤ) = ∑ i ∈ symmDiff b c, (4 : ℤ) := by
          rw [Finset.sum_const, nsmul_eq_mul]; ring
      _ ≤ ∑ i ∈ symmDiff b c, (dbl b - x) i ^ 2 := Finset.sum_le_sum hterm
      _ ≤ ∑ i, (dbl b - x) i ^ 2 :=
          Finset.sum_le_sum_of_subset_of_nonneg (subset_univ _) (fun i _ _ => sq_nonneg _)
  · right
    have hterm : ∀ i ∈ (univ : Finset (Fin 24)), 1 ≤ (dbl b - x) i ^ 2 := by
      intro i _
      apply one_le_sq
      have := hodd i
      simp only [Pi.sub_apply, dbl]; split_ifs <;> omega
    unfold normSq
    calc (24 : ℤ) = ∑ i : Fin 24, (1 : ℤ) := by simp
      _ ≤ _ := Finset.sum_le_sum hterm

/-- **The Leech distance of a doubled word is its Golay coset weight.** If `c`
is a nearest codeword to `b`, at Hamming distance `k ≤ 6`, then every lattice
vector is at squared length at least `4k` from `dbl b`, and `dbl c` is at
exactly `4k`. (Coset weights are at most `4`, so `k ≤ 6` always holds.) -/
theorem leech_dist_coset_weight (b c : Word) (hc : IsCodeword c)
    (hmin : ∀ c', IsCodeword c' → hdist b c ≤ hdist b c') (h6 : hdist b c ≤ 6) :
    (∀ x, IsLeech x → 4 * (hdist b c : ℤ) ≤ normSq (dbl b - x)) ∧
      IsLeech (dbl c) ∧ normSq (dbl b - dbl c) = 4 * (hdist b c : ℤ) := by
  refine ⟨fun x hx => ?_, dbl_isLeech hc, normSq_dbl_sub b c⟩
  rcases leech_far b hx with ⟨c', hc', h⟩ | h
  · have := hmin c' hc'
    have : (hdist b c : ℤ) ≤ hdist b c' := by exact_mod_cast this
    linarith
  · have : (hdist b c : ℤ) ≤ 6 := by exact_mod_cast h6
    linarith

/-- **Every Golay tie is a deep hole.** If no codeword is within Hamming
distance `3` of `b` and `c` is one at distance `4`, then `dbl b` is at squared
length at least `16` (true norm `2`) from every lattice vector, and exactly
`16` from `dbl c`. True norm `2` is the covering radius squared of the Leech
lattice, so `dbl b` is a deep hole, and every codeword at distance `4` gives
one of its vertices. -/
theorem golay_tie_deep_hole (b c : Word) (hc : IsCodeword c) (h4 : hdist b c = 4)
    (hmin : ∀ c', IsCodeword c' → 4 ≤ hdist b c') :
    (∀ x, IsLeech x → 16 ≤ normSq (dbl b - x)) ∧ normSq (dbl b - dbl c) = 16 := by
  obtain ⟨h1, -, h3⟩ := leech_dist_coset_weight b c hc (fun c' hc' => h4 ▸ hmin c' hc')
    (by omega)
  rw [h4] at h1 h3
  exact ⟨fun x hx => by have := h1 x hx; push_cast at this; linarith, by rw [h3]; norm_num⟩

/-- **Summed scores never prefer a wrong codeword over a common nearest one.**
The Lorentzian score of a codeword `c` against a reading `b` is
`1 − hdist b c / 4` (`LorentzianLift.inner_lift_root` with the squared
distance `hdist b c / 2` of `normSq_dbl_sub`). If the sent codeword `c` is a
nearest codeword of every reading, no codeword has a larger summed score, so
the summed-score rule is right or refuses a tie -- it is never wrong. -/
theorem summed_score_le {k : ℕ} (b : Fin k → Word) (c : Word)
    (hnear : ∀ j c', IsCodeword c' → hdist (b j) c ≤ hdist (b j) c') {c' : Word}
    (hc' : IsCodeword c') :
    ∑ j, (1 - (hdist (b j) c' : ℚ) / 4) ≤ ∑ j, (1 - (hdist (b j) c : ℚ) / 4) := by
  apply Finset.sum_le_sum
  intro j _
  have : (hdist (b j) c : ℚ) ≤ hdist (b j) c' := by exact_mod_cast hnear j c' hc'
  linarith

end GLM.GolayDeepHole
