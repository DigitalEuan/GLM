/-
# The designed substrate: is the Golay carrier optimal, and what resolves its ties?

The formal half of `studies/DESIGNED_SUBSTRATE_STUDY.md` (Phase 133). The
owner's substrate study (`source_material/substrate_study/`) asked whether the
Golay–Leech substrate is optimal for the GLM or whether a designed dimensional
system could do better. This file proves the parts of its answer that the GLM
uses, on the GLM's own code (`Golay/Code.lean`), so that nothing is quoted.

**Optimality, for every design.** A *design* is any finite set `C` of 24-bit
words and any decoder `D` that answers with a word of `C`. Nothing is assumed
about `C` being linear, or about how `D` decides.

* `decoder_sum_le` — for any weights `w` that do not increase with distance
  (from distance 3 to 4 and beyond), the total `Σ_y w(d(y, D y))` is at most
  `|C| · Σ_{e small} (w(wt e) − w 4) + 2²⁴ · w 4`. With `w i = pⁱ(1−p)^(24−i)`
  this total is `|C|` times the probability of decoding correctly on the binary
  symmetric channel.
* `golay_attains` — the GLM's code with any nearest-codeword decoder meets the
  bound with equality.
* `golay_optimal` — so no design with 4,096 words, linear or not, with any
  decoder, decodes correctly more often than the GLM's Golay code, at any flip
  rate `p ≤ 1/2`.
* `negative_space_floor` — every design leaves at least `2²⁴ − |C| · 2325`
  received words at distance 4 or more from its answer: 7,254,016 words
  (43.2 %) for 4,096 words. The negative space belongs to the parameters,
  not to Golay.
* `weight4_resolved_le` — a design that corrects every corruption of weight
  at most 3 can correct at most `2²⁴ − |C| · 2325` of the pairs (codeword,
  weight-4 corruption): for 4,096 words that is 7,254,016 of 43,524,096, one
  sixth. The six of the sextet is a volume ratio.

**What resolves a tie.** At coset weight 4 every function of the received word
is constant on the six candidates (the GLM's carried fork proves its stages
need new information). Two new sources of information are proved sound here:

* `tag_resolves` — the **sender tag**: seven parities of the carrier, computed
  by the sender without knowing the error. Two codewords within distance 4 of
  one received word with the same tag are equal. The finite step is
  `tag_nonzero_on_octads`, checked over the 4,096 messages.
* `soft_certificate` — the **soft certificate**: if a soft reading `x` is
  within squared distance `8` of the `±1` image of a codeword, every other
  codeword is more than `8` away, so at most one candidate can pass.
  `soft_certificate_sharp` shows the radius cannot be enlarged.
-/
import Mathlib
import RequestProject.GLM.Golay.Code
import RequestProject.GLM.Golay.Sextet
import RequestProject.GLM.GolayWeightEnum

namespace GLM.Golay24

open Finset

/-! ## 1. Balls of radius three -/

theorem pcDisj {i j : ℕ} (h : i ≠ j) :
    Disjoint (powersetCard i (univ : Finset (Fin 24))) (powersetCard j univ) := by
  rw [disjoint_left]
  intro s hs ht
  rw [mem_powersetCard] at hs ht
  exact h (hs.2.symm.trans ht.2)

/-- The words within distance `3` of `c` are `c` moved by a small word. -/
theorem ball_eq_image (c : Word) :
    (univ.filter fun y : Word => hdist y c ≤ 3) = small.image (fun e => symmDiff c e) := by
  ext y
  simp only [mem_filter, mem_univ, true_and, mem_image, mem_small]
  constructor
  · intro h
    refine ⟨symmDiff c y, ?_, symmDiff_symmDiff_self c y⟩
    rw [← hdist_eq_wt_symmDiff, hdist_comm]
    exact h
  · rintro ⟨e, he, rfl⟩
    rw [hdist_comm, hdist_eq_wt_symmDiff, symmDiff_symmDiff_self]
    exact he

theorem card_small : #small = 2325 := by
  have h01 : Disjoint (powersetCard 0 (univ : Finset (Fin 24))) (powersetCard 1 univ) :=
    pcDisj (by decide)
  have h2 : Disjoint (powersetCard 0 (univ : Finset (Fin 24)) ∪ powersetCard 1 univ)
      (powersetCard 2 univ) := by
    rw [disjoint_union_left]
    exact ⟨pcDisj (by decide),
      pcDisj (by decide)⟩
  have h3 : Disjoint (powersetCard 0 (univ : Finset (Fin 24)) ∪ powersetCard 1 univ ∪
      powersetCard 2 univ) (powersetCard 3 univ) := by
    rw [disjoint_union_left, disjoint_union_left]
    exact ⟨⟨pcDisj (by decide),
      pcDisj (by decide)⟩,
      pcDisj (by decide)⟩
  unfold small
  rw [card_union_of_disjoint h3, card_union_of_disjoint h2, card_union_of_disjoint h01]
  simp [card_powersetCard]
  decide

theorem card_ball (c : Word) : #(univ.filter fun y : Word => hdist y c ≤ 3) = 2325 := by
  rw [ball_eq_image, card_image_of_injective _ (symmDiff_right_injective c), card_small]

/-- A sum over the small words, by weight. -/
theorem sum_small_eq (f : ℕ → ℝ) :
    ∑ e ∈ small, f (wt e) = ∑ i ∈ range 4, (Nat.choose 24 i : ℝ) * f i := by
  have h01 : Disjoint (powersetCard 0 (univ : Finset (Fin 24))) (powersetCard 1 univ) :=
    pcDisj (by decide)
  have h2 : Disjoint (powersetCard 0 (univ : Finset (Fin 24)) ∪ powersetCard 1 univ)
      (powersetCard 2 univ) := by
    rw [disjoint_union_left]
    exact ⟨pcDisj (by decide),
      pcDisj (by decide)⟩
  have h3 : Disjoint (powersetCard 0 (univ : Finset (Fin 24)) ∪ powersetCard 1 univ ∪
      powersetCard 2 univ) (powersetCard 3 univ) := by
    rw [disjoint_union_left, disjoint_union_left]
    exact ⟨⟨pcDisj (by decide),
      pcDisj (by decide)⟩,
      pcDisj (by decide)⟩
  have hk : ∀ k : ℕ, ∑ e ∈ powersetCard k (univ : Finset (Fin 24)), f (wt e)
      = (Nat.choose 24 k : ℝ) * f k := by
    intro k
    rw [sum_congr rfl (g := fun _ => f k)]
    · simp [card_powersetCard]
    · intro e he
      rw [mem_powersetCard] at he
      simp [wt, he.2]
  unfold small
  rw [sum_union h3, sum_union h2, sum_union h01, hk, hk, hk, hk]
  simp [sum_range_succ]

/-! ## 2. Optimality for every design -/

/-- The words at distance at most `3` from `c`, summed through the small words. -/
theorem sum_ball (c : Word) (g : ℕ → ℝ) :
    ∑ y ∈ univ.filter (fun y : Word => hdist y c ≤ 3), g (hdist y c)
      = ∑ e ∈ small, g (wt e) := by
  rw [ball_eq_image, sum_image (fun a _ b _ h => symmDiff_right_injective c h)]
  refine sum_congr rfl fun e _ => ?_
  rw [hdist_comm, hdist_eq_wt_symmDiff, symmDiff_symmDiff_self]

/-- Splitting the decoder's answers inside radius `3` by the word answered. -/
theorem sum_inside_split (C : Finset Word) (D : Word → Word) (hD : ∀ y, D y ∈ C)
    (g : ℕ → ℝ) :
    ∑ y : Word, (if hdist y (D y) ≤ 3 then g (hdist y (D y)) else 0)
      = ∑ c ∈ C, ∑ y ∈ univ.filter (fun y : Word => D y = c ∧ hdist y c ≤ 3),
          g (hdist y c) := by
  rw [← sum_fiberwise_of_maps_to (s := univ) (t := C) (g := D) (fun y _ => hD y)]
  refine sum_congr rfl fun c _ => ?_
  rw [sum_filter, sum_filter]
  refine sum_congr rfl fun y _ => ?_
  by_cases hy : D y = c
  · subst hy; simp
  · simp [hy]

theorem card_univ_word : (univ : Finset Word).card = 2 ^ 24 := by
  simp

/-- **The decoder bound.** For any set `C` of words, any decoder `D` into `C`
and any weights that are at least `w 4` up to distance `3` and at most `w 4`
from distance `4` on, the total weight of the decoder's answers is at most
what filling every radius-3 ball and spending the rest at distance `4` gives. -/
theorem decoder_sum_le (C : Finset Word) (D : Word → Word) (hD : ∀ y, D y ∈ C)
    (w : ℕ → ℝ) (hlo : ∀ i ≤ 3, w 4 ≤ w i) (hhi : ∀ i, 4 ≤ i → w i ≤ w 4) :
    ∑ y : Word, w (hdist y (D y))
      ≤ (C.card : ℝ) * ∑ e ∈ small, (w (wt e) - w 4) + 2 ^ 24 * w 4 := by
  have hsplit : ∑ y : Word, w (hdist y (D y))
      = ∑ y : Word, (w (hdist y (D y)) - w 4) + 2 ^ 24 * w 4 := by
    rw [sum_sub_distrib, sum_const, card_univ_word, nsmul_eq_mul]
    push_cast
    ring
  have h1 : ∑ y : Word, (w (hdist y (D y)) - w 4)
      ≤ ∑ y : Word, (if hdist y (D y) ≤ 3 then w (hdist y (D y)) - w 4 else 0) := by
    refine sum_le_sum fun y _ => ?_
    split_ifs with h
    · exact le_rfl
    · have := hhi (hdist y (D y)) (by omega)
      linarith
  have h2 := sum_inside_split C D hD (fun i => w i - w 4)
  have h3 : ∀ c ∈ C, ∑ y ∈ univ.filter (fun y : Word => D y = c ∧ hdist y c ≤ 3),
      (w (hdist y c) - w 4) ≤ ∑ e ∈ small, (w (wt e) - w 4) := by
    intro c _
    rw [← sum_ball c (fun i => w i - w 4)]
    refine sum_le_sum_of_subset_of_nonneg ?_ ?_
    · intro y hy
      simp only [mem_filter, mem_univ, true_and] at hy ⊢
      exact hy.2
    · intro y hy _
      simp only [mem_filter, mem_univ, true_and] at hy
      have := hlo _ hy
      linarith
  have h4 := sum_le_sum h3
  rw [sum_const, nsmul_eq_mul] at h4
  rw [hsplit]
  have := h1.trans (h2.trans_le h4)
  linarith

/-- A nearest-codeword decoder for the GLM's code: it answers with a codeword
and no codeword is nearer. -/
def IsNearestDecoder (D : Word → Word) : Prop :=
  ∀ y, IsCodeword (D y) ∧ ∀ c, IsCodeword c → hdist y (D y) ≤ hdist y c

/-- One nearest-codeword decoder exists. -/
theorem exists_nearestDecoder : ∃ D : Word → Word, IsNearestDecoder D := by
  have h : ∀ y : Word, ∃ c ∈ codewords, ∀ c' ∈ codewords, hdist y c ≤ hdist y c' :=
    fun y => exists_min_image codewords (hdist y) ⟨∅, mem_codewords.2 isCodeword_empty⟩
  choose D hD hmin using h
  exact ⟨D, fun y => ⟨mem_codewords.1 (hD y),
    fun c hc => hmin y c (mem_codewords.2 hc)⟩⟩

/-- **Golay attains the bound.** -/
theorem golay_attains (D : Word → Word) (hD : IsNearestDecoder D)
    (w : ℕ → ℝ) :
    ∑ y : Word, w (hdist y (D y))
      = (4096 : ℝ) * ∑ e ∈ small, (w (wt e) - w 4) + 2 ^ 24 * w 4 := by
  have hle4 : ∀ y, hdist y (D y) ≤ 4 := by
    intro y
    obtain ⟨c, hc, hyc⟩ := covering_radius_le_four y
    exact ((hD y).2 c hc).trans hyc
  have hsplit : ∑ y : Word, w (hdist y (D y))
      = ∑ y : Word, (w (hdist y (D y)) - w 4) + 2 ^ 24 * w 4 := by
    rw [sum_sub_distrib, sum_const, card_univ_word, nsmul_eq_mul]
    push_cast
    ring
  have h1 : ∑ y : Word, (w (hdist y (D y)) - w 4)
      = ∑ y : Word, (if hdist y (D y) ≤ 3 then w (hdist y (D y)) - w 4 else 0) := by
    refine sum_congr rfl fun y _ => ?_
    split_ifs with h
    · rfl
    · have : hdist y (D y) = 4 := by have := hle4 y; omega
      rw [this]; ring
  have hDC : ∀ y, D y ∈ codewords := fun y => mem_codewords.2 (hD y).1
  have h2 := sum_inside_split codewords D hDC (fun i => w i - w 4)
  have h3 : ∀ c ∈ codewords, ∑ y ∈ univ.filter (fun y : Word => D y = c ∧ hdist y c ≤ 3),
      (w (hdist y c) - w 4) = ∑ e ∈ small, (w (wt e) - w 4) := by
    intro c hc
    rw [← sum_ball c (fun i => w i - w 4)]
    congr 1
    ext y
    simp only [mem_filter, mem_univ, true_and]
    constructor
    · exact fun h => h.2
    · intro h
      refine ⟨?_, h⟩
      have hc' : IsCodeword c := mem_codewords.1 hc
      have hy : hdist y (D y) ≤ 3 := ((hD y).2 c hc').trans h
      exact unique_nearest_of_le_three (hD y).1 hc' hy h
  rw [hsplit, h1, h2, sum_congr rfl h3, sum_const, card_codewords, nsmul_eq_mul]
  push_cast
  ring

/-- The binary symmetric channel: the probability that a sent word arrives at
distance `i`, for one fixed received word. -/
noncomputable def bscWeight (p : ℝ) (i : ℕ) : ℝ := p ^ i * (1 - p) ^ (24 - i)

/-- The probability of decoding correctly with decoder `D` into a 4,096-word
design on the binary symmetric channel with flip rate `p`, the sent word
uniform: `(1/4096) Σ_c Σ_{y : D y = c} P(y | c)`, which is the sum below. -/
noncomputable def successProb (D : Word → Word) (p : ℝ) : ℝ :=
  (1 / 4096) * ∑ y : Word, bscWeight p (hdist y (D y))

/-- For `0 ≤ p ≤ 1/2` the channel weight never increases with distance. -/
theorem bscWeight_antitone {p : ℝ} (hp0 : 0 ≤ p) (hp : p ≤ 1 / 2) :
    Antitone (bscWeight p) := by
  refine antitone_nat_of_succ_le fun i => ?_
  unfold bscWeight
  have hq : p ≤ 1 - p := by linarith
  have hq0 : 0 ≤ 1 - p := by linarith
  rcases Nat.lt_or_ge i 24 with h | h
  · have h1 : 24 - i = (24 - (i + 1)) + 1 := by omega
    rw [h1, pow_succ, pow_succ]
    have : 0 ≤ p ^ i * (1 - p) ^ (24 - (i + 1)) := by positivity
    nlinarith
  · have h1 : 24 - i = 0 := by omega
    have h2 : 24 - (i + 1) = 0 := by omega
    rw [h1, h2, pow_succ]
    simp only [pow_zero, mul_one]
    have : 0 ≤ p ^ i := by positivity
    nlinarith

/-- **The Golay code is optimal.** No design of 4,096 words in 24 bits, linear
or not, with any decoder, decodes correctly more often on the binary symmetric
channel than the GLM's Golay code with a nearest-codeword decoder, at any flip
rate `0 ≤ p ≤ 1/2`. -/
theorem golay_optimal (C : Finset Word) (hC : C.card = 4096) (D : Word → Word)
    (hD : ∀ y, D y ∈ C) (G : Word → Word) (hG : IsNearestDecoder G)
    (p : ℝ) (hp0 : 0 ≤ p) (hp : p ≤ 1 / 2) :
    successProb D p ≤ successProb G p := by
  have hA := bscWeight_antitone hp0 hp
  have hle := decoder_sum_le C D hD (bscWeight p) (fun i hi => hA (by omega))
    (fun i hi => hA hi)
  have heq := golay_attains G hG (bscWeight p)
  rw [hC] at hle
  unfold successProb
  rw [heq]
  push_cast at hle
  linarith

/-- **The negative-space floor.** Every design leaves at least
`2²⁴ − |C| · 2325` received words at distance `4` or more from the answer its
decoder gives. -/
theorem negative_space_floor (C : Finset Word) (D : Word → Word) (hD : ∀ y, D y ∈ C) :
    2 ^ 24 ≤ #(univ.filter fun y : Word => 4 ≤ hdist y (D y)) + C.card * 2325 := by
  have hin : (univ.filter fun y : Word => hdist y (D y) ≤ 3)
      ⊆ C.biUnion (fun c => univ.filter fun y : Word => hdist y c ≤ 3) := by
    intro y hy
    simp only [mem_filter, mem_univ, true_and] at hy
    exact mem_biUnion.2 ⟨D y, hD y, by simpa using hy⟩
  have hcard : #(univ.filter fun y : Word => hdist y (D y) ≤ 3) ≤ C.card * 2325 := by
    refine (card_le_card hin).trans (card_biUnion_le.trans ?_)
    rw [sum_congr rfl fun c _ => card_ball c, sum_const, smul_eq_mul]
  have hsum := card_filter_add_card_filter_not
    (s := (univ : Finset Word)) (fun y => hdist y (D y) ≤ 3)
  have hneg : (univ.filter fun y : Word => ¬ hdist y (D y) ≤ 3)
      = univ.filter fun y : Word => 4 ≤ hdist y (D y) := by
    ext y; simp only [mem_filter, mem_univ, true_and]; omega
  rw [hneg, card_univ_word] at hsum
  omega

/-- For 4,096 words: at least 7,254,016 received words, 43.2 % of the space. -/
theorem negative_space_floor_4096 (C : Finset Word) (hC : C.card = 4096)
    (D : Word → Word) (hD : ∀ y, D y ∈ C) :
    7254016 ≤ #(univ.filter fun y : Word => 4 ≤ hdist y (D y)) := by
  have := negative_space_floor C D hD
  rw [hC] at this
  omega

/-- **At most one sixth of the weight-4 corruptions.** A design whose decoder
corrects every corruption of weight at most `3` corrects at most
`2²⁴ − |C| · 2325` pairs (codeword, weight-4 corruption). -/
theorem weight4_resolved_le (C : Finset Word) (D : Word → Word)
    (hcorr : ∀ c ∈ C, ∀ e, wt e ≤ 3 → D (symmDiff c e) = c) :
    #((C ×ˢ tetrads).filter fun q => D (symmDiff q.1 q.2) = q.1) + C.card * 2325
      ≤ 2 ^ 24 := by
  set R := (C ×ˢ tetrads).filter fun q => D (symmDiff q.1 q.2) = q.1
  have hS : ∀ q ∈ C ×ˢ small, D (symmDiff q.1 q.2) = q.1 := by
    intro q hq
    rw [mem_product] at hq
    exact hcorr q.1 hq.1 q.2 (mem_small.1 hq.2)
  have hdisj : Disjoint R (C ×ˢ small) := by
    rw [disjoint_left]
    intro q hqR hqS
    simp only [R, mem_filter, mem_product, mem_tetrads] at hqR
    rw [mem_product, mem_small] at hqS
    omega
  have hinj : Set.InjOn (fun q : Word × Word => symmDiff q.1 q.2) ↑(R ∪ C ×ˢ small) := by
    intro q hq q' hq' h
    have hD : ∀ r ∈ R ∪ C ×ˢ small, D (symmDiff r.1 r.2) = r.1 := by
      intro r hr
      rcases mem_union.1 hr with hr | hr
      · simp only [R, mem_filter] at hr; exact hr.2
      · exact hS r hr
    have h1 : q.1 = q'.1 := by
      rw [← hD q hq, ← hD q' hq']; exact congrArg D h
    have h2 : q.2 = q'.2 := by
      have := congrArg (symmDiff q.1) h
      simp only at this
      rw [symmDiff_symmDiff_self, h1, symmDiff_symmDiff_self] at this
      exact this
    exact Prod.ext h1 h2
  have hle : #(R ∪ C ×ˢ small) ≤ #(univ : Finset Word) :=
    card_le_card_of_injOn _ (fun _ _ => by simp) hinj
  rw [card_union_of_disjoint hdisj, card_product, card_small, card_univ_word] at hle
  exact hle

/-- For 4,096 words: at most 7,254,016 of the `4096 · 10626 = 43,524,096`
pairs, exactly one sixth. -/
theorem weight4_resolved_le_4096 (C : Finset Word) (hC : C.card = 4096) (D : Word → Word)
    (hcorr : ∀ c ∈ C, ∀ e, wt e ≤ 3 → D (symmDiff c e) = c) :
    #((C ×ˢ tetrads).filter fun q => D (symmDiff q.1 q.2) = q.1) ≤ 7254016 ∧
      6 * 7254016 = 4096 * Nat.choose 24 4 := by
  refine ⟨?_, by decide⟩
  have := weight4_resolved_le C D hcorr
  rw [hC] at this
  omega

/-! ## 3. The sender tag -/

/-- The seven tag masks, as 24-bit integers (bit `k` is coordinate `k`); the
same constants as `TAG_MASKS` in `glm_universal/reasoning/designed_substrate.py`. -/
def tagMasks : List ℕ :=
  [7442265, 11191954, 5298992, 12955048, 9854244, 14599079, 3151149]

/-- Coordinate `k`'s contribution to the tag: which masks contain `k`. -/
def tagCol (k : Fin 24) : Fin 7 → ZMod 2 :=
  fun i => if (tagMasks.getD i 0).testBit k then 1 else 0

/-- The seven-bit tag of a word: the parity of its overlap with each mask. -/
def tagOf (w : Word) : Fin 7 → ZMod 2 := ∑ k ∈ w, tagCol k

theorem tag_neg_self (x : Fin 7 → ZMod 2) : -x = x := by
  funext i
  have : ∀ y : ZMod 2, -y = y := by decide
  exact this (x i)

/-- The tag is linear: the tag of a symmetric difference is the sum. -/
theorem tagOf_symmDiff (a b : Word) : tagOf (symmDiff a b) = tagOf a + tagOf b := by
  have hsub : a ∩ b ⊆ a ∪ b := (inter_subset_left).trans subset_union_left
  have hsd : symmDiff a b = (a ∪ b) \ (a ∩ b) := by
    rw [symmDiff_eq_sup_sdiff_inf]; rfl
  have h1 : ∑ k ∈ (a ∪ b) \ (a ∩ b), tagCol k
      = (∑ k ∈ a ∪ b, tagCol k) - ∑ k ∈ a ∩ b, tagCol k := Finset.sum_sdiff_eq_sub hsub
  have h2 : (∑ k ∈ a ∪ b, tagCol k) + ∑ k ∈ a ∩ b, tagCol k
      = (∑ k ∈ a, tagCol k) + ∑ k ∈ b, tagCol k := Finset.sum_union_inter
  unfold tagOf
  rw [hsd, h1, sub_eq_add_neg, tag_neg_self]
  linear_combination (norm := abel) h2

/-- **The finite step.** No octad has tag zero, checked over all 4,096 messages. -/
theorem tag_nonzero_on_octads :
    ∀ m : Fin 12 → ZMod 2, wt (encode m) = 8 → tagOf (encode m) ≠ 0 := by
  unfold wt; native_decide

/-- **The sender tag resolves every tie.** Two codewords within distance `4`
of one received word that carry the same tag are the same codeword. -/
theorem tag_resolves {y c c' : Word} (hc : IsCodeword c) (hc' : IsCodeword c')
    (h : hdist y c ≤ 4) (h' : hdist y c' ≤ 4) (ht : tagOf c = tagOf c') : c = c' := by
  by_contra hne
  have ho : IsCodeword (symmDiff c c') := isCodeword_symmDiff hc hc'
  have hne' : symmDiff c c' ≠ ∅ := by
    intro h0
    exact hne (symmDiff_eq_bot.1 h0)
  have h8 : 8 ≤ wt (symmDiff c c') := golay_min_weight ho hne'
  have htri : wt (symmDiff c c') ≤ hdist y c + hdist y c' := by
    have hsub : symmDiff c c' ⊆ symmDiff c y ∪ symmDiff y c' := symmDiff_triangle c y c'
    have := (card_le_card hsub).trans (card_union_le _ _)
    unfold wt
    rw [hdist_comm y c]
    exact this
  have hw8 : wt (symmDiff c c') = 8 := by
    rcases golay_weight_mem ho with h0 | h0 | h0 | h0 | h0 <;> omega
  obtain ⟨m, hm⟩ := exists_encode ho
  have hz : tagOf (symmDiff c c') = 0 := by
    rw [tagOf_symmDiff, ht]
    funext i
    have hy : ∀ y : ZMod 2, y + y = 0 := by decide
    exact hy _
  rw [← hm] at hz hw8
  exact tag_nonzero_on_octads m hw8 hz

/-! ## 4. The soft certificate -/

/-- The `±1` image of a word: `+1` off the support, `−1` on it. -/
def pm (c : Word) (k : Fin 24) : ℝ := if k ∈ c then -1 else 1

/-- Squared Euclidean distance from a soft reading to the image of a word. -/
noncomputable def sqd (x : Fin 24 → ℝ) (c : Word) : ℝ := ∑ k, (x k - pm c k) ^ 2

/-- Two images are `4 · d` apart in squared distance. -/
theorem sqd_pm (c c' : Word) : ∑ k, (pm c k - pm c' k) ^ 2 = 4 * (hdist c c' : ℝ) := by
  have hterm : ∀ k, (pm c k - pm c' k) ^ 2 = if k ∈ symmDiff c c' then 4 else 0 := by
    intro k
    by_cases h1 : k ∈ c <;> by_cases h2 : k ∈ c' <;>
      simp [pm, h1, h2, Finset.mem_symmDiff] <;> norm_num
  rw [sum_congr rfl fun k _ => hterm k, sum_ite_mem, univ_inter, sum_const, nsmul_eq_mul]
  unfold hdist
  ring

/-- **The soft certificate.** If a soft reading is within squared distance `8`
of a codeword's image, every other codeword's image is more than `8` away. -/
theorem soft_certificate {x : Fin 24 → ℝ} {c c' : Word} (hc : IsCodeword c)
    (hc' : IsCodeword c') (hne : c ≠ c') (h : sqd x c < 8) : 8 < sqd x c' := by
  have ho : IsCodeword (symmDiff c c') := isCodeword_symmDiff hc hc'
  have hne' : symmDiff c c' ≠ ∅ := fun h0 => hne (symmDiff_eq_bot.1 h0)
  have h8 : (8 : ℝ) ≤ hdist c c' := by
    have := golay_min_weight ho hne'
    unfold wt at this
    unfold hdist
    exact_mod_cast this
  have hpar : ∑ k, (pm c k - pm c' k) ^ 2 ≤ 2 * sqd x c + 2 * sqd x c' := by
    unfold sqd
    rw [mul_sum, mul_sum, ← sum_add_distrib]
    refine sum_le_sum fun k _ => ?_
    nlinarith [sq_nonneg (x k - pm c k + (x k - pm c' k))]
  rw [sqd_pm] at hpar
  linarith

/-- **The radius is sharp.** Some soft reading is at squared distance exactly
`8` from two distinct codewords. -/
theorem soft_certificate_sharp :
    ∃ x : Fin 24 → ℝ, ∃ c c' : Word, IsCodeword c ∧ IsCodeword c' ∧ c ≠ c' ∧
      sqd x c = 8 ∧ sqd x c' = 8 := by
  obtain ⟨o, ho, hw⟩ := golay_min_distance_eight.2
  refine ⟨fun k => if k ∈ o then 0 else 1, ∅, o, isCodeword_empty, ho, ?_, ?_, ?_⟩
  · intro h0
    rw [← h0] at hw
    simp [wt] at hw
  · unfold sqd
    have hterm : ∀ k, ((if k ∈ o then (0 : ℝ) else 1) - pm ∅ k) ^ 2
        = if k ∈ o then 1 else 0 := by
      intro k; by_cases h : k ∈ o <;> simp [pm, h]
    rw [sum_congr rfl fun k _ => hterm k, sum_ite_mem, univ_inter, sum_const, nsmul_eq_mul]
    unfold wt at hw
    rw [hw]; norm_num
  · unfold sqd
    have hterm : ∀ k, ((if k ∈ o then (0 : ℝ) else 1) - pm o k) ^ 2
        = if k ∈ o then 1 else 0 := by
      intro k; by_cases h : k ∈ o <;> simp [pm, h]
    rw [sum_congr rfl fun k _ => hterm k, sum_ite_mem, univ_inter, sum_const, nsmul_eq_mul]
    unfold wt at hw
    rw [hw]; norm_num

end GLM.Golay24
