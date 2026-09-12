/-
# The wobble landscape: the three theorems behind a bit score

`studies/WOBBLE_LANDSCAPE_STUDY.md` asks whether the fine-structure constant's
gap-structure signature is distinctive against a stated null, and answers with
one number.  Most of that study is a *measurement*, and measurements belong in
`overlay/glm_universal/reasoning/wobble_landscape.py`.  Three of its ingredients
are not measurements but theorems, and they are here.

## 1.  The gap bound — the two-distance form of the Three-Distance Theorem

`Sturmian.lean` proves that the delta–sigma stream chasing `t` is the
mechanical word `⌊(n+1)t⌋ - ⌊n t⌋`, whose `j`-th one sits at `⌈j/t⌉ - 1`.  With
`s = 1/t` the gap between consecutive ones is `⌈(j+1)s⌉ - ⌈j s⌉`, and

* `gap_lower`, `gap_upper` — that gap lies between `⌊s⌋` and `⌊s⌋ + 1`;
* `gap_mem_pair` — so it takes **one of two values**, whatever `j` and whatever
  `s`;
* `gap_image_card_le_two`, `gap_image_card_le_three` — hence the set of gap
  lengths occurring anywhere in a run has at most two elements, and *a fortiori*
  at most the three of the Three-Distance Theorem, whose third length is the
  truncated boundary gap of a finite window.

Nothing here needs `s` irrational: the bound is unconditional, which is why the
Python module may apply it to the exact rational surrogates it computes with.

## 2.  The sphere count behind the Golay null

The study's null for "how close is a 24-bit word to the code?" is the exact
count of words within distance 3 of a codeword.  That count is a theorem about
*any* code whose minimum distance exceeds twice the radius:

* `ball_card` — a Hamming ball of radius `r` in `n` bits holds
  `∑ i ≤ r, C(n, i)` words, for every centre;
* `ball_disjoint` — balls of radius `r` about codewords at distance `≥ 2r+1`
  are disjoint;
* `code_ball_card` — so the union holds exactly `|C| * ∑ i ≤ r, C(n, i)`;
* `golay_ball_count`, `golay_ball_fraction` — instantiated at `n = 24`,
  `r = 3`, `|C| = 4096`: `9,523,200` words of `16,777,216`, a probability of
  exactly `2325/4096`.

The corrected reading the study takes from this: `d_min ≤ 3` is the **majority**
case under a uniform word, worth less than one bit, and not a structural
coincidence.

## 3.  Monotonicity of the bit score

The study scores a result as `B = log₂(1/p) - log₂ m`.  `bitScore_antitone` is
the property that makes that a score at all: a *larger* tail probability can
only give a *smaller* number of bits, so `B` cannot be inflated by weakening
the test.  `bitScore_one` pins the origin — a tail of one scores zero — and
`corrected_lt_iff_lt` says the multiplicity correction shifts the gate without
reordering anything.

Words are modelled as `Finset (Fin n)` — the set of positions where the word is
`1` — and Hamming distance as the cardinality of the symmetric difference,
which is `Finset.card_symmDiff` territory rather than a new definition.
-/
import Mathlib
import RequestProject.GLM.GolayWeightEnum

namespace GLM.Landscape

open Finset

/-! ## 1.  The gap between consecutive ones takes at most two values -/

/-- The position of the `j`-th one in the mechanical word of slope `1/s`. -/
noncomputable def onePos (s : ℝ) (j : ℕ) : ℤ := ⌈(j : ℝ) * s⌉ - 1

/-- The gap between the `j`-th and the `(j+1)`-st one, `s = 1/t`. -/
noncomputable def gap (s : ℝ) (j : ℕ) : ℤ := ⌈((j : ℝ) + 1) * s⌉ - ⌈(j : ℝ) * s⌉

lemma onePos_sub (s : ℝ) (j : ℕ) :
    onePos s (j + 1) - onePos s j = gap s j := by
  simp [onePos, gap, Nat.cast_add, Nat.cast_one]

/-- **The gap is at least `⌊s⌋`.** -/
theorem gap_lower (s : ℝ) (j : ℕ) : ⌊s⌋ ≤ gap s j := by
  have hexp : ((j : ℝ) + 1) * s = (j : ℝ) * s + s := by ring
  have hle : (j : ℝ) * s + ((⌊s⌋ : ℤ) : ℝ) ≤ ((j : ℝ) + 1) * s := by
    rw [hexp]
    have := Int.floor_le s
    linarith
  have hmono : ⌈(j : ℝ) * s + ((⌊s⌋ : ℤ) : ℝ)⌉ ≤ ⌈((j : ℝ) + 1) * s⌉ :=
    Int.ceil_le_ceil hle
  rw [Int.ceil_add_intCast] at hmono
  simp only [gap]
  omega

/-- **The gap is at most `⌊s⌋ + 1`.** -/
theorem gap_upper (s : ℝ) (j : ℕ) : gap s j ≤ ⌊s⌋ + 1 := by
  have hexp : ((j : ℝ) + 1) * s = (j : ℝ) * s + s := by ring
  have hle : ((j : ℝ) + 1) * s ≤ (j : ℝ) * s + ((⌈s⌉ : ℤ) : ℝ) := by
    rw [hexp]
    have := Int.le_ceil s
    linarith
  have hmono : ⌈((j : ℝ) + 1) * s⌉ ≤ ⌈(j : ℝ) * s + ((⌈s⌉ : ℤ) : ℝ)⌉ :=
    Int.ceil_le_ceil hle
  rw [Int.ceil_add_intCast] at hmono
  have hcf : ⌈s⌉ ≤ ⌊s⌋ + 1 := Int.ceil_le_floor_add_one s
  simp only [gap]
  omega

/-- **Two distances, and no more.**  Every gap is `⌊s⌋` or `⌊s⌋ + 1`. -/
theorem gap_mem_pair (s : ℝ) (j : ℕ) :
    gap s j = ⌊s⌋ ∨ gap s j = ⌊s⌋ + 1 := by
  have h1 := gap_lower s j
  have h2 := gap_upper s j
  omega

/-- The gap lengths occurring in any finite window form a set of size ≤ 2. -/
theorem gap_image_card_le_two (s : ℝ) (window : Finset ℕ) :
    (window.image (gap s)).card ≤ 2 := by
  have hsub : window.image (gap s) ⊆ ({⌊s⌋, ⌊s⌋ + 1} : Finset ℤ) := by
    intro g hg
    obtain ⟨j, _, rfl⟩ := Finset.mem_image.mp hg
    rcases gap_mem_pair s j with h | h <;> simp [h]
  calc (window.image (gap s)).card
      ≤ ({⌊s⌋, ⌊s⌋ + 1} : Finset ℤ).card := Finset.card_le_card hsub
    _ ≤ 2 := Finset.card_insert_le _ _ |>.trans (by simp)

/-- The Three-Distance bound, in the form the study quotes it. -/
theorem gap_image_card_le_three (s : ℝ) (window : Finset ℕ) :
    (window.image (gap s)).card ≤ 3 :=
  le_trans (gap_image_card_le_two s window) (by norm_num)

/-! ## 2.  The sphere count behind the Golay null -/

variable {n : ℕ}

/-- The Hamming ball of radius `r` about a word, as a set of words. -/
def ball (r : ℕ) (x : Finset (Fin n)) : Finset (Finset (Fin n)) :=
  (univ : Finset (Finset (Fin n))).filter fun y => (symmDiff x y).card ≤ r

lemma mem_ball {r : ℕ} {x y : Finset (Fin n)} :
    y ∈ ball r x ↔ (symmDiff x y).card ≤ r := by
  simp [ball]

/-- **A ball has the same size wherever it is centred**, namely the number of
error patterns of weight at most `r`. -/
theorem ball_card (r : ℕ) (x : Finset (Fin n)) :
    (ball r x).card = ∑ i ∈ range (r + 1), n.choose i := by
  classical
  have hbij : (ball r x).card
      = ((univ : Finset (Finset (Fin n))).filter fun z => z.card ≤ r).card := by
    refine Finset.card_nbij' (fun y => symmDiff x y) (fun z => symmDiff x z)
      ?_ ?_ ?_ ?_
    · intro y hy
      simp only [Finset.coe_filter, Set.mem_setOf_eq, Finset.mem_univ,
        true_and]
      exact mem_ball.mp (by simpa using hy)
    · intro z hz
      simp only [Finset.coe_filter, Set.mem_setOf_eq, Finset.mem_univ,
        true_and] at hz
      have : symmDiff x (symmDiff x z) = z := symmDiff_symmDiff_cancel_left x z
      simp only [Finset.mem_coe, mem_ball, this]
      exact hz
    · intro y _
      exact symmDiff_symmDiff_cancel_left x y
    · intro z _
      exact symmDiff_symmDiff_cancel_left x z
  rw [hbij]
  have hsplit : ((univ : Finset (Finset (Fin n))).filter fun z => z.card ≤ r)
      = (range (r + 1)).biUnion fun i => powersetCard i univ := by
    ext z
    simp [Finset.mem_powersetCard, eq_comm]
  rw [hsplit, Finset.card_biUnion]
  · refine Finset.sum_congr rfl ?_
    intro i _
    simp [Finset.card_powersetCard]
  · intro i _ j _ hij
    refine Finset.disjoint_left.mpr ?_
    intro z hi hj
    exact hij ((Finset.mem_powersetCard.mp hi).2 ▸
      (Finset.mem_powersetCard.mp hj).2 ▸ rfl)

/-- The Hamming distance obeys the triangle inequality. -/
theorem card_symmDiff_triangle (x y z : Finset (Fin n)) :
    (symmDiff x z).card ≤ (symmDiff x y).card + (symmDiff y z).card := by
  classical
  have hsub : symmDiff x z ⊆ symmDiff x y ∪ symmDiff y z := by
    intro a ha
    simp only [Finset.mem_symmDiff] at ha
    simp only [Finset.mem_union, Finset.mem_symmDiff]
    by_cases hy : a ∈ y
    · rcases ha with ⟨hx, hz⟩ | ⟨hz, hx⟩
      · exact Or.inr (Or.inl ⟨hy, hz⟩)
      · exact Or.inl (Or.inr ⟨hy, hx⟩)
    · rcases ha with ⟨hx, hz⟩ | ⟨hz, hx⟩
      · exact Or.inl (Or.inl ⟨hx, hy⟩)
      · exact Or.inr (Or.inr ⟨hz, hy⟩)
  calc (symmDiff x z).card ≤ (symmDiff x y ∪ symmDiff y z).card :=
        Finset.card_le_card hsub
    _ ≤ (symmDiff x y).card + (symmDiff y z).card := Finset.card_union_le _ _

/-- **Balls about far-apart centres are disjoint.** -/
theorem ball_disjoint {r : ℕ} {x y : Finset (Fin n)}
    (h : 2 * r + 1 ≤ (symmDiff x y).card) : Disjoint (ball r x) (ball r y) := by
  refine Finset.disjoint_left.mpr ?_
  intro z hx hy
  have h1 : (symmDiff x z).card ≤ r := mem_ball.mp hx
  have h2 : (symmDiff y z).card ≤ r := mem_ball.mp hy
  have h3 : (symmDiff z y).card = (symmDiff y z).card := by
    rw [symmDiff_comm]
  have := card_symmDiff_triangle x z y
  omega

/-- **The exact count the Golay null is built from.**  A code whose minimum
distance exceeds `2r` covers exactly `|C| · ∑ i ≤ r, C(n, i)` words with its
balls of radius `r`. -/
theorem code_ball_card {r : ℕ} (C : Finset (Finset (Fin n)))
    (hC : ∀ x ∈ C, ∀ y ∈ C, x ≠ y → 2 * r + 1 ≤ (symmDiff x y).card) :
    (C.biUnion (ball r)).card = C.card * ∑ i ∈ range (r + 1), n.choose i := by
  classical
  rw [Finset.card_biUnion]
  · rw [Finset.sum_congr rfl fun x _ => ball_card r x, Finset.sum_const,
      smul_eq_mul]
  · intro x hx y hy hxy
    exact ball_disjoint (hC x hx y hy hxy)

/-- The radius-3 sphere sum in 24 bits: `1 + 24 + 276 + 2024`. -/
theorem golay_sphere_sum : ∑ i ∈ range 4, Nat.choose 24 i = 2325 := by decide

/-- **The Golay null, exactly.**  4096 codewords, minimum distance 8, so the
balls of radius 3 are disjoint and hold 9,523,200 of the 16,777,216 words. -/
theorem golay_ball_count (C : Finset (Finset (Fin 24))) (hcard : C.card = 4096)
    (hC : ∀ x ∈ C, ∀ y ∈ C, x ≠ y → 7 ≤ (symmDiff x y).card) :
    (C.biUnion (ball 3)).card = 9523200 := by
  have h := code_ball_card (r := 3) C (by simpa using hC)
  rw [h, hcard, golay_sphere_sum]

/-- **The same count, for the substrate's own code.**  `GolayWeightEnum.lean`
supplies the two facts this needs — 4,096 codewords, and every nonzero codeword
of weight at least 8 — so the null the study quotes is the null of the code the
rest of the repository computes with, not of a code assumed to exist. -/
theorem golay_code_ball_count :
    ((GLM.Golay24.codewords).biUnion (ball 3)).card = 9523200 := by
  refine golay_ball_count _ GLM.Golay24.card_codewords ?_
  intro x hx y hy hxy
  have hxc : GLM.Golay24.IsCodeword x := GLM.Golay24.mem_codewords.mp hx
  have hyc : GLM.Golay24.IsCodeword y := GLM.Golay24.mem_codewords.mp hy
  have hs : GLM.Golay24.IsCodeword (symmDiff x y) :=
    GLM.Golay24.isCodeword_symmDiff hxc hyc
  have hne : symmDiff x y ≠ ∅ := by
    intro h
    exact hxy (symmDiff_eq_bot.mp h)
  have hcard : (symmDiff x y).card ≠ 0 := by
    simpa [Finset.card_eq_zero] using hne
  have hw := GLM.Golay24.golay_weight_mem hs
  unfold GLM.Golay24.wt at hw
  omega

/-- The same statement as a probability: exactly `2325/4096`, about 0.82 bits,
which is the majority of the space. -/
theorem golay_ball_fraction :
    (9523200 : ℚ) / 16777216 = 2325 / 4096 := by norm_num

theorem golay_ball_majority : (1 : ℚ) / 2 < 2325 / 4096 := by norm_num

/-! ## 3.  The bit score -/

/-- The score a study reports: `log₂(1/p)` bits against a tail probability. -/
noncomputable def bitScore (p : ℝ) : ℝ := Real.logb 2 (1 / p)

/-- The score after the multiplicity correction for `m` statistics tried. -/
noncomputable def corrected (p : ℝ) (m : ℕ) : ℝ := bitScore p - Real.logb 2 m

@[simp] theorem bitScore_one : bitScore 1 = 0 := by
  simp [bitScore]

/-- **The bit score is antitone in the tail probability.**  A weaker result —
a larger `p` — can never score more bits. -/
theorem bitScore_antitone {p q : ℝ} (hp : 0 < p) (hpq : p ≤ q) :
    bitScore q ≤ bitScore p := by
  have hq : 0 < q := lt_of_lt_of_le hp hpq
  have hinv : 1 / q ≤ 1 / p := one_div_le_one_div_of_le hp hpq
  have hpos : 0 < 1 / q := by positivity
  exact Real.logb_le_logb_of_le (by norm_num) hpos hinv

/-- A tail probability of one is worth nothing. -/
theorem bitScore_nonneg {p : ℝ} (hp : 0 < p) (hp1 : p ≤ 1) : 0 ≤ bitScore p := by
  have := bitScore_antitone hp hp1
  simpa using this

/-- The correction shifts the gate and reorders nothing. -/
theorem corrected_antitone {p q : ℝ} (m : ℕ) (hp : 0 < p) (hpq : p ≤ q) :
    corrected q m ≤ corrected p m := by
  have := bitScore_antitone hp hpq
  simp only [corrected]
  linarith

theorem corrected_lt_iff_lt (p : ℝ) (m : ℕ) (gate : ℝ) :
    corrected p m < gate ↔ bitScore p < gate + Real.logb 2 m := by
  simp only [corrected]
  constructor <;> intro h <;> linarith

end GLM.Landscape
