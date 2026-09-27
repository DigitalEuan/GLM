/-
# The Steiner system `S(5, 8, 24)`

This file is **retrieved material**: `data_object/mog_cube_1/RequestProject/`
of the supplied archive (`source_material/GLM-main.zip`) is the largest Lean
development in the archive — 736 theorems — and its `GolaySteiner.lean` proves,
by a two-moment count over the codewords covering a five-set, that any five of
the twenty-four points lie in exactly one octad. Nothing in the present
development said anything about how the 759 octads sit on the 24 points, so
this is the piece worth carrying across.

The proof here is not the archive's. Everything needed is already available in
`GolayWeightEnum.lean`, and putting those pieces together gives the design
directly and without any new computation:

* `card_inter_le_four` — two distinct octads meet in at most four points. The
  symmetric difference of two codewords is a codeword, its weight lies in
  `{0, 8, 12, 16, 24}` by the weight enumerator, and for two octads it equals
  `16 − 2·|o₁ ∩ o₂|`; being nonzero it is at least 8, so the intersection is at
  most 4. This is the uniqueness half.
* `pairwiseDisjoint_fiveSubsets` — hence distinct octads share no five-subset,
  so the families of five-subsets they carry are pairwise disjoint.
* `card_octads` (759, from the weight enumerator) and `Nat.choose 8 5 = 56` give
  `759 × 56 = 42 504` five-subsets covered, and `Nat.choose 24 5 = 42 504` is
  the number of five-subsets there are. The covered ones are therefore *all* of
  them — `fiveSubsets_biUnion_eq` — which is the existence half.
* `unique_octad` — **the Steiner system `S(5,8,24)`**: every five-subset of the
  twenty-four points lies in exactly one octad.
* `card_octads_through_four` — and the standard corollary `λ₄ = 5`: every
  four-subset lies in exactly five octads.

The design is what makes the substrate's error-correction sharp: it is the
reason a five-cell violation pattern names its octad, and the counting above is
the same double count the `Golay/Census.lean` coset census performs from the
other side.
-/
import RequestProject.GLM.GolayWeightEnum


namespace GLM.Golay24

open Finset

/-! ## 1. The octads -/

/-- The octads: the codewords of weight eight. -/
def octads : Finset Word := codewords.filter fun c => wt c = 8

theorem mem_octads {o : Word} : o ∈ octads ↔ IsCodeword o ∧ wt o = 8 := by
  simp [octads, mem_codewords]

/-- There are 759 octads. -/
theorem card_octads : octads.card = 759 :=
  golay_weight_enumerator.2.1

-- `codewords` and `octads` are filters over the `2²⁴` words, so any attempt to
-- evaluate them by unfolding is hopeless. Everything below goes through
-- `mem_octads` and `card_octads`, so seal them.
attribute [local irreducible] codewords octads

/-! ## 2. Two octads meet in at most four points -/

theorem card_symmDiff_eq (s t : Word) :
    (symmDiff s t).card = s.card + t.card - 2 * (s ∩ t).card := by
  have hsub : s ∩ t ⊆ s ∪ t := inter_subset_left.trans subset_union_left
  have hsd : symmDiff s t = (s ∪ t) \ (s ∩ t) := by
    rw [symmDiff_eq_sup_sdiff_inf]; rfl
  have hu : (s ∪ t).card + (s ∩ t).card = s.card + t.card :=
    Finset.card_union_add_card_inter s t
  have hle : (s ∩ t).card ≤ (s ∪ t).card := Finset.card_le_card hsub
  rw [hsd, Finset.card_sdiff, Finset.inter_eq_left.2 hsub]
  omega

/-- **Two distinct octads meet in at most four points.** Their symmetric
difference is a nonzero codeword, hence of weight at least eight, and that
weight is `16 − 2·|o₁ ∩ o₂|`. -/
theorem card_inter_le_four {o₁ o₂ : Word} (h₁ : o₁ ∈ octads) (h₂ : o₂ ∈ octads)
    (hne : o₁ ≠ o₂) : (o₁ ∩ o₂).card ≤ 4 := by
  obtain ⟨hc₁, hw₁⟩ := mem_octads.1 h₁
  obtain ⟨hc₂, hw₂⟩ := mem_octads.1 h₂
  have hcard₁ : o₁.card = 8 := hw₁
  have hcard₂ : o₂.card = 8 := hw₂
  have hd : IsCodeword (symmDiff o₁ o₂) := isCodeword_symmDiff hc₁ hc₂
  have hne' : symmDiff o₁ o₂ ≠ ∅ := fun h => hne (symmDiff_eq_bot.1 h)
  have hpos : 0 < (symmDiff o₁ o₂).card :=
    Finset.card_pos.2 (Finset.nonempty_iff_ne_empty.2 hne')
  have hmem : (symmDiff o₁ o₂).card = 0 ∨ (symmDiff o₁ o₂).card = 8 ∨
      (symmDiff o₁ o₂).card = 12 ∨ (symmDiff o₁ o₂).card = 16 ∨
      (symmDiff o₁ o₂).card = 24 := golay_weight_mem hd
  have hcard : (symmDiff o₁ o₂).card = 8 + 8 - 2 * (o₁ ∩ o₂).card := by
    rw [card_symmDiff_eq, hcard₁, hcard₂]
  have hle : (o₁ ∩ o₂).card ≤ 8 := by
    have hsub : o₁ ∩ o₂ ⊆ o₁ := inter_subset_left
    have := Finset.card_le_card hsub
    omega
  rw [hcard] at hpos hmem
  omega

/-! ## 3. The design -/

/-- The five-subsets of the twenty-four points. -/
def fiveSubsets : Finset Word := (univ : Finset (Fin 24)).powersetCard 5

theorem mem_fiveSubsets {T : Word} : T ∈ fiveSubsets ↔ T.card = 5 := by
  simp [fiveSubsets, mem_powersetCard]

theorem card_fiveSubsets : fiveSubsets.card = 42504 := by
  rw [fiveSubsets, Finset.card_powersetCard, Finset.card_univ, Fintype.card_fin]
  decide

/-- Distinct octads carry disjoint families of five-subsets: a common
five-subset would put five points in their intersection. -/
theorem pairwiseDisjoint_fiveSubsets :
    (octads : Set Word).PairwiseDisjoint fun o => o.powersetCard 5 := by
  intro o₁ h₁ o₂ h₂ hne
  have hm₁ : o₁ ∈ octads := h₁
  have hm₂ : o₂ ∈ octads := h₂
  simp only [Finset.disjoint_left]
  intro T hT₁ hT₂
  rw [mem_powersetCard] at hT₁ hT₂
  have hsub : T ⊆ o₁ ∩ o₂ := Finset.subset_inter hT₁.1 hT₂.1
  have hcard := Finset.card_le_card hsub
  have h4 := card_inter_le_four hm₁ hm₂ hne
  omega

/-- The five-subsets carried by the octads: `759 × 56 = 42 504` of them. -/
theorem card_biUnion_fiveSubsets :
    (octads.biUnion fun o => o.powersetCard 5).card = 42504 := by
  have h : ∀ o ∈ octads, (o.powersetCard 5).card = 56 := by
    intro o ho
    rw [Finset.card_powersetCard, show o.card = 8 from (mem_octads.1 ho).2]
    decide
  rw [Finset.card_biUnion pairwiseDisjoint_fiveSubsets, Finset.sum_congr rfl h,
    Finset.sum_const, card_octads, smul_eq_mul]

/-- **Every five-subset lies on an octad.** There are `Nat.choose 24 5 = 42 504`
five-subsets and the octads carry `42 504` distinct ones, so they carry all. -/
theorem fiveSubsets_biUnion_eq :
    octads.biUnion (fun o => o.powersetCard 5) = fiveSubsets := by
  refine Finset.eq_of_subset_of_card_le ?_ ?_
  · intro T hT
    rw [Finset.mem_biUnion] at hT
    have hTo := mem_powersetCard.1 hT.choose_spec.2
    exact mem_fiveSubsets.2 hTo.2
  · rw [card_biUnion_fiveSubsets, card_fiveSubsets]

/-- **The Steiner system `S(5,8,24)`.** Any five of the twenty-four points lie
in exactly one octad. -/
theorem unique_octad {T : Word} (hT : T.card = 5) :
    ∃! o, o ∈ octads ∧ T ⊆ o := by
  have hmem : T ∈ octads.biUnion fun o => o.powersetCard 5 := by
    rw [fiveSubsets_biUnion_eq]
    exact mem_fiveSubsets.2 hT
  rw [Finset.mem_biUnion] at hmem
  have hspec := hmem.choose_spec
  have hTo := mem_powersetCard.1 hspec.2
  refine ⟨hmem.choose, ⟨hspec.1, hTo.1⟩, ?_⟩
  intro o' ho'
  by_contra hne
  have hsub : T ⊆ o' ∩ hmem.choose := Finset.subset_inter ho'.2 hTo.1
  have hcard := Finset.card_le_card hsub
  have h4 := card_inter_le_four ho'.1 hspec.1 hne
  omega

/-! ## 4. The corollary `λ₄ = 5` -/

/-- The octads through a given set of points. -/
def through (T : Word) : Finset Word := octads.filter fun o => T ⊆ o

theorem mem_through {T o : Word} : o ∈ through T ↔ o ∈ octads ∧ T ⊆ o := by
  simp [through]

/-- Restated: exactly one octad passes through any five points. -/
theorem card_through_five {T : Word} (hT : T.card = 5) : (through T).card = 1 := by
  obtain ⟨o, ho, huniq⟩ := unique_octad hT
  rw [Finset.card_eq_one]
  refine ⟨o, ?_⟩
  ext o'
  simp only [mem_through, Finset.mem_singleton]
  exact ⟨fun h => huniq o' h, fun h => h ▸ ho⟩

/-- Adding a point to the set restricts the octads through it. -/
theorem through_insert (p : Fin 24) (F : Word) :
    through (insert p F) = (through F).filter fun o => p ∈ o := by
  ext o
  simp only [mem_through, Finset.mem_filter, Finset.insert_subset_iff]
  constructor
  · rintro ⟨ho, hp, hF⟩
    exact ⟨⟨ho, hF⟩, hp⟩
  · rintro ⟨⟨ho, hF⟩, hp⟩
    exact ⟨ho, hp, hF⟩

/-- **`λ₄ = 5`.** Every four of the twenty-four points lie in exactly five
octads: the twenty five-subsets extending the four-set each determine one
octad, and each such octad accounts for four of them. -/
theorem card_octads_through_four {F : Word} (hF : F.card = 4) :
    (through F).card = 5 := by
  classical
  set P : Finset (Fin 24) := univ \ F with hP
  have hPcard : P.card = 20 := by
    rw [hP, Finset.card_sdiff, Finset.inter_eq_left.2 (Finset.subset_univ F), hF,
      Finset.card_univ, Fintype.card_fin]
  -- Double count the incidences between the points outside `F` and the octads
  -- through `F`.
  have key : ∑ p ∈ P, ((through F).filter fun o => p ∈ o).card
      = ∑ o ∈ through F, (P.filter fun p => p ∈ o).card := by
    simp only [Finset.card_filter]
    exact Finset.sum_comm
  -- Each point outside `F` lies on exactly one octad through `F`.
  have hrow : ∀ p ∈ P, ((through F).filter fun o => p ∈ o).card = 1 := by
    intro p hp
    have hpn : p ∉ F := (Finset.mem_sdiff.1 hp).2
    rw [← through_insert]
    exact card_through_five (by rw [Finset.card_insert_of_notMem hpn, hF])
  -- Each octad through `F` has exactly four further points.
  have hcol : ∀ o ∈ through F, (P.filter fun p => p ∈ o).card = 4 := by
    intro o ho
    rw [mem_through] at ho
    have hw : o.card = 8 := (mem_octads.1 ho.1).2
    have hset : (P.filter fun p => p ∈ o) = o \ F := by
      ext p
      simp only [Finset.mem_filter, hP, Finset.mem_sdiff, Finset.mem_univ, true_and]
      exact ⟨fun h => ⟨h.2, h.1⟩, fun h => ⟨h.2, h.1⟩⟩
    rw [hset, Finset.card_sdiff, Finset.inter_eq_left.2 ho.2, hw, hF]
  rw [Finset.sum_congr rfl hrow, Finset.sum_congr rfl hcol, Finset.sum_const,
    Finset.sum_const, hPcard] at key
  simp only [smul_eq_mul, mul_one] at key
  omega

end GLM.Golay24
