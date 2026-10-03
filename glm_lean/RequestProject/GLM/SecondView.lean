/-
# Second readings: what several views of one carrier can and cannot resolve

Phase 96 (`studies/SECOND_VIEW_STUDY.md`). A framed register stores one Golay
codeword `c` in several views; a burst `e` read through view `k` becomes the
error `rot(e, k)`. This file proves the structure the round's marks were
declared from.

* `dist_ge_four`, `dist_eq_four_iff` — **the fork of a burst.** For a
  codeword `c` and a four-set `e`, every codeword is at distance at least 4
  from the read `c ∆ e`, and exactly the codewords `c` and `c ∆ o` with `o` an
  octad containing `e` are at distance 4.
* `common_iff` — **what two views allow.** A codeword is in the fork of both
  reads `c ∆ e` and `c ∆ f` exactly when it is `c` or `c ∆ o` with `o` an
  octad containing `e ∪ f`. `resolved_iff` and `five_leaves_one` are the two
  readings of it the study uses.
* `pair_dist_ge`, `pair_dist_eq_iff` — **the soft channel of the views is the
  second reading.** The sum of the two view distances is at least 8, with
  equality exactly on the codewords both forks allow. `soft_mean_dist` says
  the squared distance from the mean of two views to a word is half that sum
  minus a quarter of the views' disagreement, so ranking by the soft reading
  is ranking by the sum; `pair_likelihood_strictAnti` says the pair
  likelihood at any rate below one half ranks the same way.
* `no_single_frame_separates` — **one second frame never suffices.** For
  every permutation of the 24 coordinates there is a four-set whose union
  with its image lies in an octad, so the two-view register leaves that burst
  open.
* `three_frames_separate` — **three frames do.** For every four-set `e`, no
  octad contains `e ∪ (e + 1) ∪ (e + 3)`. This is a finite check over the
  10,626 four-sets, discharged by `native_decide` through the decidable
  `noOctadAbove`, which `through_eq_empty_of_noOctadAbove` connects to the
  octads of `Steiner.lean` (`noOctadAbove_iff` is the exact equivalence).
* `pair_frame_open_count` — **what one second frame leaves.** With the single
  second frame at offset one, exactly 174 of the 10,626 four-sets leave an
  octad through the union, which is the figure the round's mark V1 reproduces
  at runtime.
-/
import RequestProject.GLM.Steiner

namespace GLM.SecondView

open Finset GLM.Golay24

/-! ## 1. The fork of a burst -/

/-- Distance from a codeword `c'` to the read `c ∆ e` is the weight of
`(c ∆ c') ∆ e`. -/
theorem hdist_read (c c' e : Word) :
    hdist c' (symmDiff c e) = (symmDiff (symmDiff c c') e).card := by
  unfold hdist
  rw [symmDiff_left_comm, ← symmDiff_assoc]

/-- The weight of `d ∆ e` for a codeword difference `d` and a four-set `e`. -/
private theorem card_symmDiff_four {d e : Word} (he : e.card = 4) :
    (symmDiff d e).card = d.card + 4 - 2 * (d ∩ e).card ∧ (d ∩ e).card ≤ 4 ∧
      (d ∩ e).card ≤ d.card := by
  refine ⟨by rw [card_symmDiff_eq, he], ?_, card_le_card inter_subset_left⟩
  rw [← he]; exact card_le_card inter_subset_right

/-- Every codeword is at distance at least four from a burst of four. -/
theorem dist_ge_four {c c' e : Word} (hc : IsCodeword c) (hc' : IsCodeword c')
    (he : e.card = 4) : 4 ≤ hdist c' (symmDiff c e) := by
  rw [hdist_read]
  set d := symmDiff c c'
  have hd : IsCodeword d := isCodeword_symmDiff hc hc'
  obtain ⟨h1, h2, h3⟩ := card_symmDiff_four (d := d) he
  by_cases h0 : d = ∅
  · rw [h0, show symmDiff (∅ : Word) e = e by ext y; simp [mem_symmDiff], he]
  · have h8 : 8 ≤ wt d := golay_min_weight hd h0
    unfold wt at h8
    omega

/-- **The fork of a burst.** The codewords at distance four from `c ∆ e` are
`c` and the `c ∆ o` with `o` an octad through `e`. -/
theorem dist_eq_four_iff {c c' e : Word} (hc : IsCodeword c) (hc' : IsCodeword c')
    (he : e.card = 4) :
    hdist c' (symmDiff c e) = 4 ↔ c' = c ∨ symmDiff c c' ∈ through e := by
  rw [hdist_read]
  set d := symmDiff c c' with hdd
  have hd : IsCodeword d := isCodeword_symmDiff hc hc'
  obtain ⟨h1, h2, h3⟩ := card_symmDiff_four (d := d) he
  have hcc : c' = c ↔ d = ∅ := by
    rw [hdd]
    constructor
    · rintro rfl; simp
    · intro h; exact (symmDiff_eq_bot.1 h).symm
  rw [hcc, mem_through, mem_octads]
  constructor
  · intro h4
    by_cases h0 : d = ∅
    · exact Or.inl h0
    · right
      have h8 : 8 ≤ wt d := golay_min_weight hd h0
      have hm := golay_weight_mem hd
      unfold wt at h8 hm
      have hdc : d.card = 8 := by omega
      have hk : (d ∩ e).card = e.card := by omega
      refine ⟨⟨hd, hdc⟩, ?_⟩
      have := eq_of_subset_of_card_le (inter_subset_right (s₁ := d) (s₂ := e)) (by omega)
      rw [← this]; exact inter_subset_left
  · rintro (h0 | ⟨⟨_, hw⟩, hsub⟩)
    · rw [h0, show symmDiff (∅ : Word) e = e by ext y; simp [mem_symmDiff], he]
    · unfold wt at hw
      rw [inter_eq_right.2 hsub, he, hw] at h1
      omega

/-! ## 2. What two views allow -/

/-- **What two views allow.** -/
theorem common_iff {c c' e f : Word} (hc : IsCodeword c) (hc' : IsCodeword c')
    (he : e.card = 4) (hf : f.card = 4) :
    (hdist c' (symmDiff c e) = 4 ∧ hdist c' (symmDiff c f) = 4) ↔
      c' = c ∨ symmDiff c c' ∈ through (e ∪ f) := by
  rw [dist_eq_four_iff hc hc' he, dist_eq_four_iff hc hc' hf]
  constructor
  · rintro ⟨h1 | h1, h2⟩
    · exact Or.inl h1
    · rcases h2 with h2 | h2
      · exact Or.inl h2
      · rw [mem_through] at h1 h2
        exact Or.inr (mem_through.2 ⟨h1.1, union_subset h1.2 h2.2⟩)
  · rintro (h | h)
    · exact ⟨Or.inl h, Or.inl h⟩
    · rw [mem_through] at h
      exact ⟨Or.inr (mem_through.2 ⟨h.1, subset_union_left.trans h.2⟩),
        Or.inr (mem_through.2 ⟨h.1, subset_union_right.trans h.2⟩)⟩

/-- Two views resolve the burst exactly when no octad contains the union of
the errors they read. -/
theorem resolved_iff {c e f : Word} (hc : IsCodeword c) (he : e.card = 4)
    (hf : f.card = 4) :
    (∀ c', IsCodeword c' → hdist c' (symmDiff c e) = 4 →
        hdist c' (symmDiff c f) = 4 → c' = c) ↔ through (e ∪ f) = ∅ := by
  constructor
  · intro h
    by_contra hne
    obtain ⟨o, ho⟩ := nonempty_iff_ne_empty.2 hne
    have hoc : IsCodeword o := (mem_octads.1 (mem_through.1 ho).1).1
    have hc' : IsCodeword (symmDiff c o) := isCodeword_symmDiff hc hoc
    have hback : symmDiff c (symmDiff c o) = o := symmDiff_symmDiff_cancel_left c o
    have hboth := (common_iff hc hc' he hf).2 (Or.inr (by rw [hback]; exact ho))
    have heq := h _ hc' hboth.1 hboth.2
    have : o = ∅ := by
      rw [← hback, heq]; simp
    have hw := (mem_octads.1 (mem_through.1 ho).1).2
    rw [this] at hw
    simp [wt] at hw
  · intro h c' hc' h1 h2
    rcases (common_iff hc hc' he hf).1 ⟨h1, h2⟩ with h0 | h0
    · exact h0
    · rw [h] at h0; simp at h0

/-- When the two errors share three points, exactly one octad survives. -/
theorem five_leaves_one {e f : Word} (h : (e ∪ f).card = 5) :
    (through (e ∪ f)).card = 1 :=
  card_through_five h

/-- Nine or more points lie in no octad. -/
theorem through_eq_empty_of_nine {u : Word} (h : 9 ≤ u.card) : through u = ∅ := by
  rw [eq_empty_iff_forall_notMem]
  intro o ho
  obtain ⟨ho8, hsub⟩ := mem_through.1 ho
  have hw := (mem_octads.1 ho8).2
  unfold wt at hw
  have := card_le_card hsub
  omega

/-! ## 3. The soft channel of the views is the second reading -/

theorem pair_dist_ge {c c' e f : Word} (hc : IsCodeword c) (hc' : IsCodeword c')
    (he : e.card = 4) (hf : f.card = 4) :
    8 ≤ hdist c' (symmDiff c e) + hdist c' (symmDiff c f) := by
  have := dist_ge_four hc hc' he
  have := dist_ge_four hc hc' hf
  omega

/-- **The minimum of the summed view distances is the intersection.** -/
theorem pair_dist_eq_iff {c c' e f : Word} (hc : IsCodeword c) (hc' : IsCodeword c')
    (he : e.card = 4) (hf : f.card = 4) :
    hdist c' (symmDiff c e) + hdist c' (symmDiff c f) = 8 ↔
      c' = c ∨ symmDiff c c' ∈ through (e ∪ f) := by
  rw [← common_iff hc hc' he hf]
  have := dist_ge_four hc hc' he
  have := dist_ge_four hc hc' hf
  omega

/-- The indicator of a word, as a rational vector. -/
def ind (a : Word) (j : Fin 24) : ℚ := if j ∈ a then 1 else 0

/-- Hamming distance as a sum of squared coordinate differences. -/
theorem hdist_eq_sum (a x : Word) :
    (hdist a x : ℚ) = ∑ j : Fin 24, (ind a j - ind x j) ^ 2 := by
  have hj : ∀ j : Fin 24, (ind a j - ind x j) ^ 2 =
      if j ∈ symmDiff a x then 1 else 0 := by
    intro j
    unfold ind
    by_cases ha : j ∈ a <;> by_cases hx : j ∈ x <;> simp [ha, hx, mem_symmDiff]
  rw [Finset.sum_congr rfl (fun j _ => hj j), Finset.sum_boole,
    Finset.filter_mem_eq_inter, univ_inter]
  rfl

/-- **The soft reading of two views.** The squared distance from the
coordinatewise mean of two views to a word `x` is half the sum of the view
distances minus a quarter of the views' disagreement. -/
theorem soft_mean_dist (a b x : Word) :
    ∑ j : Fin 24, ((ind a j + ind b j) / 2 - ind x j) ^ 2 =
      ((hdist a x : ℚ) + hdist b x) / 2 - (hdist a b : ℚ) / 4 := by
  rw [hdist_eq_sum a x, hdist_eq_sum b x, hdist_eq_sum a b, ← Finset.sum_add_distrib,
    Finset.sum_div, Finset.sum_div, ← Finset.sum_sub_distrib]
  refine Finset.sum_congr rfl (fun j _ => ?_)
  ring

/-- The pair likelihood `p^D (1-p)^(48-D)` is strictly decreasing in `D` at
every rate `0 < p < 1/2`. -/
theorem pair_likelihood_strictAnti {p : ℚ} (hp : 0 < p) (hp2 : p < 1 / 2)
    {D₁ D₂ : ℕ} (h : D₁ < D₂) (h₂ : D₂ ≤ 48) :
    p ^ D₂ * (1 - p) ^ (48 - D₂) < p ^ D₁ * (1 - p) ^ (48 - D₁) := by
  obtain ⟨k, rfl⟩ : ∃ k, D₂ = D₁ + (k + 1) := ⟨D₂ - D₁ - 1, by omega⟩
  have hm : 48 - D₁ = (48 - (D₁ + (k + 1))) + (k + 1) := by omega
  have hpq : p < 1 - p := by linarith
  have hlt : p ^ (k + 1) < (1 - p) ^ (k + 1) := pow_lt_pow_left₀ hpq hp.le (by omega)
  have hpos : 0 < p ^ D₁ * (1 - p) ^ (48 - (D₁ + (k + 1))) := by
    have : 0 < 1 - p := by linarith
    positivity
  have := mul_lt_mul_of_pos_left hlt hpos
  calc p ^ (D₁ + (k + 1)) * (1 - p) ^ (48 - (D₁ + (k + 1)))
      = p ^ D₁ * (1 - p) ^ (48 - (D₁ + (k + 1))) * p ^ (k + 1) := by rw [pow_add]; ring
    _ < p ^ D₁ * (1 - p) ^ (48 - (D₁ + (k + 1))) * (1 - p) ^ (k + 1) := this
    _ = p ^ D₁ * (1 - p) ^ (48 - D₁) := by rw [hm, pow_add (1 - p)]; ring

/-! ## 4. One second frame never suffices -/

private theorem exists_outside (s : Word) (h : s.card < 24) : ∃ d, d ∉ s := by
  by_contra hcon
  push_neg at hcon
  have : (univ : Finset (Fin 24)) ⊆ s := fun y _ => hcon y
  have := card_le_card this
  simp at this
  omega

/-- Some three points move under `σ` with at most one image outside them. -/
theorem exists_triple (σ : Equiv.Perm (Fin 24)) :
    ∃ T : Word, T.card = 3 ∧ ∃ d ∉ T, T.map σ.toEmbedding ⊆ insert d T := by
  suffices h : ∃ T : Word, T.card = 3 ∧ ∃ x, T.map σ.toEmbedding ⊆ insert x T by
    obtain ⟨T, hT, x, hx⟩ := h
    by_cases hxT : x ∈ T
    · obtain ⟨d, hd⟩ := exists_outside T (by omega)
      refine ⟨T, hT, d, hd, ?_⟩
      rw [insert_eq_of_mem hxT] at hx
      exact hx.trans (subset_insert _ _)
    · exact ⟨T, hT, x, hxT, hx⟩
  by_cases h1 : ∃ a, σ a ≠ a ∧ σ (σ a) ≠ a
  · obtain ⟨a, ha1, ha2⟩ := h1
    have h3 : σ a ≠ σ (σ a) := fun h => ha1 (σ.injective h).symm
    refine ⟨{a, σ a, σ (σ a)}, ?_, σ (σ (σ a)), ?_⟩
    · rw [card_insert_of_notMem, card_insert_of_notMem, card_singleton]
      · simpa using h3
      · simp only [mem_insert, mem_singleton, not_or]
        exact ⟨Ne.symm ha1, Ne.symm ha2⟩
    · intro y hy
      simp only [mem_map, mem_insert, mem_singleton, Equiv.coe_toEmbedding] at hy
      obtain ⟨z, hz, rfl⟩ := hy
      rcases hz with rfl | rfl | rfl <;> simp
  · push_neg at h1
    by_cases h2 : ∃ a, σ a ≠ a
    · obtain ⟨a, ha⟩ := h2
      have haa : σ (σ a) = a := h1 a ha
      obtain ⟨b, hb⟩ := exists_outside ({a, σ a} : Word)
        (lt_of_le_of_lt (card_insert_le _ _) (by simp))
      simp only [mem_insert, mem_singleton, not_or] at hb
      refine ⟨{a, σ a, b}, ?_, σ b, ?_⟩
      · rw [card_insert_of_notMem, card_insert_of_notMem, card_singleton]
        · simpa using Ne.symm hb.2
        · simp only [mem_insert, mem_singleton, not_or]
          exact ⟨Ne.symm ha, Ne.symm hb.1⟩
      · intro y hy
        simp only [mem_map, mem_insert, mem_singleton, Equiv.coe_toEmbedding] at hy
        obtain ⟨z, hz, rfl⟩ := hy
        rcases hz with rfl | rfl | rfl <;> simp [haa]
    · push_neg at h2
      refine ⟨{0, 1, 2}, by decide, 0, ?_⟩
      intro y hy
      simp only [mem_map, Equiv.coe_toEmbedding, h2] at hy
      obtain ⟨z, hz, rfl⟩ := hy
      exact subset_insert _ _ hz

/-- **One second frame never suffices.** For every permutation `σ` of the
coordinates some four-set `e` has an octad through `e ∪ σ e`. -/
theorem no_single_frame_separates (σ : Equiv.Perm (Fin 24)) :
    ∃ e : Word, e.card = 4 ∧ (through (e ∪ e.map σ.toEmbedding)).Nonempty := by
  obtain ⟨T, hT, d, hd, hsub⟩ := exists_triple σ
  refine ⟨insert d T, by rw [card_insert_of_notMem hd, hT], ?_⟩
  set V : Word := insert (σ d) (insert d T)
  have hU : insert d T ∪ (insert d T).map σ.toEmbedding ⊆ V := by
    rw [map_insert]
    intro y hy
    rcases mem_union.1 hy with hy | hy
    · exact subset_insert _ _ hy
    · rcases mem_insert.1 hy with rfl | hy
      · exact mem_insert_self _ _
      · exact subset_insert _ _ (hsub hy)
  have hV : V.card ≤ 5 := by
    calc V.card ≤ (insert d T).card + 1 := card_insert_le _ _
      _ = 5 := by rw [card_insert_of_notMem hd, hT]
  obtain ⟨W, hVW, hW⟩ := exists_superset_card_eq hV (by simp)
  obtain ⟨o, ⟨ho, hWo⟩, _⟩ := unique_octad hW
  exact ⟨o, mem_through.2 ⟨ho, (hU.trans hVW).trans hWo⟩⟩

/-! ## 5. Three frames do -/

/-- A decidable form of "no octad contains `u`": either `u` has more than
eight points, or no completion of `u` to eight points has zero syndrome. -/
def noOctadAbove (u : Word) : Bool :=
  decide (8 < u.card) ||
    (((univ \ u).powersetCard (8 - u.card)).filter (fun T => key (u ∪ T) = 0)).card == 0

private theorem key_eq_zero_iff (s : Word) : key s = 0 ↔ IsCodeword s := by
  have h0 : key (∅ : Word) = 0 := by simp [key, syn_empty, packSyn]
  rw [← h0, key_eq_iff, syn_empty]
  rfl

/-- `noOctadAbove` decides exactly that no octad contains `u`. -/
theorem noOctadAbove_iff (u : Word) : noOctadAbove u = true ↔ through u = ∅ := by
  unfold noOctadAbove
  simp only [Bool.or_eq_true, decide_eq_true_eq, beq_iff_eq, card_eq_zero,
    filter_eq_empty_iff]
  constructor
  · rintro (h | h)
    · exact through_eq_empty_of_nine (by omega)
    · rw [eq_empty_iff_forall_notMem]
      intro o ho
      obtain ⟨ho8, hsub⟩ := mem_through.1 ho
      obtain ⟨hoc, hw⟩ := mem_octads.1 ho8
      unfold wt at hw
      have hT : o \ u ∈ (univ \ u).powersetCard (8 - u.card) := by
        rw [mem_powersetCard]
        refine ⟨sdiff_subset_sdiff (subset_univ _) (Subset.refl u), ?_⟩
        rw [card_sdiff_of_subset hsub, hw]
      apply h hT
      rw [union_sdiff_of_subset hsub, key_eq_zero_iff]
      exact hoc
  · intro h
    by_cases h8 : 8 < u.card
    · exact Or.inl h8
    · right
      intro T hT hkey
      rw [mem_powersetCard] at hT
      have hdisj : Disjoint u T := by
        rw [disjoint_left]
        intro y hyu hyT
        exact (mem_sdiff.1 (hT.1 hyT)).2 hyu
      have hcard : (u ∪ T).card = 8 := by
        rw [card_union_of_disjoint hdisj, hT.2]; omega
      have hmem : u ∪ T ∈ through u :=
        mem_through.2 ⟨mem_octads.2 ⟨(key_eq_zero_iff _).1 hkey, hcard⟩, subset_union_left⟩
      rw [h] at hmem
      simp at hmem

/-- The errors the three views of the framed register read. -/
def frameUnion (e : Word) : Word :=
  e ∪ e.image (· + 1) ∪ e.image (· + 3)

theorem frameUnion_check :
    ((univ.powersetCard 4).filter (fun e : Word => noOctadAbove (frameUnion e) = false)).card
      = 0 := by
  native_decide

/-- **Three frames separate every burst.** -/
theorem three_frames_separate {e : Word} (he : e.card = 4) :
    through (frameUnion e) = ∅ := by
  have h := frameUnion_check
  rw [card_eq_zero, filter_eq_empty_iff] at h
  have := h (mem_powersetCard.2 ⟨subset_univ _, he⟩)
  rw [← noOctadAbove_iff]
  simpa using this

theorem pairUnion_check :
    ((univ.powersetCard 4).filter
      (fun e : Word => noOctadAbove (e ∪ e.image (· + 1)) = false)).card = 174 := by
  native_decide

/-- **The two-view register's open bursts.** With the single second frame at
offset one, exactly 174 of the 10,626 four-sets leave an octad through the
union of the errors the two views read. -/
theorem pair_frame_open_count :
    ((univ.powersetCard 4).filter
      (fun e : Word => (through (e ∪ e.image (· + 1))).Nonempty)).card = 174 := by
  have hf : (univ.powersetCard 4).filter
        (fun e : Word => (through (e ∪ e.image (· + 1))).Nonempty) =
      (univ.powersetCard 4).filter
        (fun e : Word => noOctadAbove (e ∪ e.image (· + 1)) = false) := by
    apply filter_congr
    intro e _
    rw [nonempty_iff_ne_empty, ne_eq, ← noOctadAbove_iff, Bool.not_eq_true]
  calc _ = _ := congrArg card hf
    _ = 174 := pairUnion_check

end GLM.SecondView
