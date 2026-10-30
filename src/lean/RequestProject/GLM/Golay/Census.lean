/-
# The coset census, and where the code sits on average

`Golay/Sextet.lean` settles the two extreme readings: a word of coset weight at
most `3` is read uniquely, and a word of coset weight `4` has exactly six
nearest codewords.  This file counts how often each happens.

For a syndrome `f`, `cosetWt f` is the weight of a minimum-weight word carrying
it — equivalently the distance from any word of that syndrome to the code.  The
census is

| coset weight | syndromes |
|---|---|
| 0 | 1 |
| 1 | 24 |
| 2 | 276 |
| 3 | 2024 |
| 4 | 1771 |

so `2325` of the `4096` cosets are read uniquely and `1771` are six-fold ties,
and the mean coset weight is `13732 / 4096 = 3433 / 1024 ≈ 3.352`.

The last number is the point of the file.  The packing radius of the code is
`3` and its covering radius is `4`; the *average* word sits strictly between
them (`mean_coset_weight_gt_three`, `mean_coset_weight_lt_four`).  A word drawn
at random is therefore, on average, already past the radius inside which the
reading is unique — ambiguity is the typical case for this code, not a corner
case, and a machine that only ever reports a single nearest codeword is
suppressing information on `1771 / 4096 ≈ 43%` of its inputs.
-/
import RequestProject.GLM.Golay.Sextet

namespace GLM.Golay24

open Finset

/-! ## The coset weight of a syndrome -/

/-- Every syndrome is carried by a word of weight at most `4`: the covering
radius bound, stated for syndromes rather than for words. -/
theorem exists_word_syn (f : Syn) : ∃ u : Word, wt u ≤ 4 ∧ syn u = f := by
  classical
  set K : Finset ℕ := (skeys + tkeys).toFinset with hK
  have himg : K ⊆ Finset.image packSyn univ := by
    intro k hk
    simp only [hK, Multiset.mem_toFinset, Multiset.mem_add] at hk
    rcases hk with hk | hk
    · obtain ⟨u, _, hu⟩ := Multiset.mem_map.1 hk
      exact Finset.mem_image.2 ⟨syn u, Finset.mem_univ _, hu⟩
    · obtain ⟨u, _, hu⟩ := Multiset.mem_map.1 hk
      exact Finset.mem_image.2 ⟨syn u, Finset.mem_univ _, hu⟩
  have hcard : #(Finset.image packSyn (univ : Finset Syn)) = 4096 := by
    rw [Finset.card_image_of_injective _ packSyn_injective]
    simp [Finset.card_univ]
  have heq : K = Finset.image packSyn univ :=
    Finset.eq_of_subset_of_card_le himg (by rw [hcard, keys_card])
  have hmem : packSyn f ∈ K := by
    rw [heq]
    exact Finset.mem_image.2 ⟨f, Finset.mem_univ _, rfl⟩
  simp only [hK, Multiset.mem_toFinset, Multiset.mem_add] at hmem
  rcases hmem with hk | hk
  · obtain ⟨u, hu, hku⟩ := Multiset.mem_map.1 hk
    exact ⟨u, le_trans (mem_small.1 hu) (by norm_num), packSyn_injective hku⟩
  · obtain ⟨u, hu, hku⟩ := Multiset.mem_map.1 hk
    exact ⟨u, le_of_eq (mem_tetrads.1 hu), packSyn_injective hku⟩

/-- The weight of a minimum-weight word carrying the syndrome `f`. -/
noncomputable def cosetWt (f : Syn) : ℕ := sInf {n | ∃ u : Word, syn u = f ∧ wt u = n}

theorem cosetWt_le (u : Word) : cosetWt (syn u) ≤ wt u :=
  Nat.sInf_le ⟨u, rfl, rfl⟩

/-- The minimum is attained: some word of that weight carries the syndrome. -/
theorem exists_wt_eq_cosetWt (f : Syn) : ∃ u : Word, syn u = f ∧ wt u = cosetWt f := by
  obtain ⟨u, _, hu⟩ := exists_word_syn f
  have hne : {n | ∃ u : Word, syn u = f ∧ wt u = n}.Nonempty := ⟨wt u, u, hu, rfl⟩
  exact Nat.sInf_mem hne

theorem cosetWt_le_four (f : Syn) : cosetWt f ≤ 4 := by
  obtain ⟨u, hu, hsu⟩ := exists_word_syn f
  calc cosetWt f = cosetWt (syn u) := by rw [hsu]
    _ ≤ wt u := cosetWt_le u
    _ ≤ 4 := hu

/-- Inside the packing radius the coset weight is the weight itself. -/
theorem cosetWt_of_wt_le_three {u : Word} (hu : wt u ≤ 3) : cosetWt (syn u) = wt u := by
  refine le_antisymm (cosetWt_le u) ?_
  obtain ⟨u', hsu', hwu'⟩ := exists_wt_eq_cosetWt (syn u)
  by_contra hlt
  push_neg at hlt
  have hu'3 : wt u' ≤ 3 := by omega
  have : u' = u := small_syn_inj hu'3 hu hsu'
  rw [this] at hwu'
  omega

/-- A tetrad's coset has weight exactly `4`. -/
theorem cosetWt_of_wt_four {u : Word} (hu : wt u = 4) : cosetWt (syn u) = 4 := by
  refine le_antisymm (by rw [← hu]; exact cosetWt_le u) ?_
  obtain ⟨u', hsu', hwu'⟩ := exists_wt_eq_cosetWt (syn u)
  by_contra hlt
  push_neg at hlt
  exact small_syn_ne_tetrad (a := u') (t := u) (by omega) hu hsu'

/-! ## The census -/

/-- For `w ≤ 3` the syndromes of coset weight `w` are exactly the syndromes of
the words of weight `w`. -/
theorem filter_cosetWt_eq_image {w : ℕ} (hw : w ≤ 3) :
    (univ.filter fun f : Syn => cosetWt f = w)
      = (powersetCard w (univ : Word)).image syn := by
  ext f
  simp only [Finset.mem_filter, Finset.mem_univ, true_and, Finset.mem_image,
    Finset.mem_powersetCard, Finset.subset_univ]
  constructor
  · intro hf
    obtain ⟨u, hsu, hwu⟩ := exists_wt_eq_cosetWt f
    exact ⟨u, by rw [show u.card = wt u from rfl, hwu, hf], hsu⟩
  · rintro ⟨u, hcard, rfl⟩
    have hwu : wt u = w := hcard
    rw [cosetWt_of_wt_le_three (by omega), hwu]

theorem card_filter_cosetWt {w : ℕ} (hw : w ≤ 3) :
    #(univ.filter fun f : Syn => cosetWt f = w) = Nat.choose 24 w := by
  rw [filter_cosetWt_eq_image hw, Finset.card_image_of_injOn, Finset.card_powersetCard]
  · simp
  · intro a ha b hb hab
    simp only [Finset.mem_coe, Finset.mem_powersetCard] at ha hb
    exact small_syn_inj (by rw [show wt a = a.card from rfl, ha.2]; omega)
      (by rw [show wt b = b.card from rfl, hb.2]; omega) hab

/-- The syndromes of coset weight `4` are exactly the syndromes of the tetrads. -/
theorem filter_cosetWt_four :
    (univ.filter fun f : Syn => cosetWt f = 4) = tetrads.image syn := by
  ext f
  simp only [Finset.mem_filter, Finset.mem_univ, true_and, Finset.mem_image, mem_tetrads]
  constructor
  · intro hf
    obtain ⟨u, hsu, hwu⟩ := exists_wt_eq_cosetWt f
    exact ⟨u, by rw [hwu, hf], hsu⟩
  · rintro ⟨u, hu, rfl⟩
    exact cosetWt_of_wt_four hu

/-- Each of those syndromes is carried by exactly six tetrads, and there are
`10626` tetrads, so there are `1771` of them. -/
theorem card_image_syn_tetrads : #(tetrads.image syn) = 1771 := by
  have hfib : ∀ f ∈ tetrads.image syn, #(tetrads.filter fun u => syn u = f) = 6 := by
    intro f hf
    obtain ⟨u, hu, rfl⟩ := Finset.mem_image.1 hf
    exact tetrad_class_card (mem_tetrads.1 hu)
  have hsum : #tetrads = #(tetrads.image syn) * 6 :=
    (Finset.card_eq_sum_card_image syn tetrads).trans (Finset.sum_const_nat hfib)
  have htot : #tetrads = 10626 := by
    rw [tetrads, Finset.card_powersetCard, Finset.card_univ]
    norm_num [Nat.choose]
  omega

theorem card_filter_cosetWt_four :
    #(univ.filter fun f : Syn => cosetWt f = 4) = 1771 := by
  rw [filter_cosetWt_four]
  exact card_image_syn_tetrads

/-- **The census.**  How many of the `4096` cosets sit at each distance from the
code. -/
theorem coset_census :
    #(univ.filter fun f : Syn => cosetWt f = 0) = 1 ∧
    #(univ.filter fun f : Syn => cosetWt f = 1) = 24 ∧
    #(univ.filter fun f : Syn => cosetWt f = 2) = 276 ∧
    #(univ.filter fun f : Syn => cosetWt f = 3) = 2024 ∧
    #(univ.filter fun f : Syn => cosetWt f = 4) = 1771 :=
  ⟨by simpa using card_filter_cosetWt (w := 0) (by norm_num),
   by simpa using card_filter_cosetWt (w := 1) (by norm_num),
   by simpa using card_filter_cosetWt (w := 2) (by norm_num),
   by simpa using card_filter_cosetWt (w := 3) (by norm_num),
   card_filter_cosetWt_four⟩

/-- The census exhausts the `4096` syndromes. -/
theorem census_total :
    (1 : ℕ) + 24 + 276 + 2024 + 1771 = Fintype.card Syn := by
  simp

/-! ## The mean coset weight -/

/-- The average distance from a word to the code, as an exact rational. -/
noncomputable def meanCosetWt : ℚ := (∑ f : Syn, (cosetWt f : ℚ)) / 4096

theorem sum_cosetWt : (∑ f : Syn, (cosetWt f : ℚ)) = 13732 := by
  classical
  have hmaps : ∀ f ∈ (univ : Finset Syn), cosetWt f ∈ Finset.range 5 := by
    intro f _
    simp only [Finset.mem_range]
    have := cosetWt_le_four f
    omega
  have hfib := Finset.sum_fiberwise_of_maps_to hmaps (fun f => (cosetWt f : ℚ))
  rw [← hfib]
  have hstep : ∀ w ∈ Finset.range 5,
      (∑ f ∈ univ.filter fun f : Syn => cosetWt f = w, (cosetWt f : ℚ))
        = (w : ℚ) * #(univ.filter fun f : Syn => cosetWt f = w) := by
    intro w _
    rw [Finset.sum_congr rfl (fun f hf => by
      simp only [Finset.mem_filter] at hf
      rw [hf.2]), Finset.sum_const, nsmul_eq_mul]
    ring
  rw [Finset.sum_congr rfl hstep]
  obtain ⟨h0, h1, h2, h3, h4⟩ := coset_census
  rw [show (Finset.range 5) = {0, 1, 2, 3, 4} from rfl]
  rw [Finset.sum_insert (by decide), Finset.sum_insert (by decide),
    Finset.sum_insert (by decide), Finset.sum_insert (by decide), Finset.sum_singleton,
    h0, h1, h2, h3, h4]
  norm_num

/-- **The mean coset weight.**  `13732 / 4096 = 3433 / 1024`. -/
theorem mean_coset_weight : meanCosetWt = 3433 / 1024 := by
  rw [meanCosetWt, sum_cosetWt]
  norm_num

/-- The average word sits **past** the packing radius: unique reading is not the
typical case. -/
theorem mean_coset_weight_gt_three : 3 < meanCosetWt := by
  rw [mean_coset_weight]; norm_num

/-- …and inside the covering radius, so the tie is never worse than six-fold. -/
theorem mean_coset_weight_lt_four : meanCosetWt < 4 := by
  rw [mean_coset_weight]; norm_num

/-- **The critical split.**  Of the `4096` cosets, `2325` are read uniquely and
`1771` are six-fold ties; no coset is anything else. -/
theorem unique_vs_ambiguous :
    #(univ.filter fun f : Syn => cosetWt f ≤ 3) = 2325 ∧
    #(univ.filter fun f : Syn => cosetWt f = 4) = 1771 := by
  classical
  refine ⟨?_, card_filter_cosetWt_four⟩
  have hsplit : (univ.filter fun f : Syn => cosetWt f ≤ 3)
      = (univ.filter fun f : Syn => cosetWt f = 0) ∪
        ((univ.filter fun f : Syn => cosetWt f = 1) ∪
          ((univ.filter fun f : Syn => cosetWt f = 2) ∪
            (univ.filter fun f : Syn => cosetWt f = 3))) := by
    ext f
    simp only [Finset.mem_filter, Finset.mem_univ, true_and, Finset.mem_union]
    omega
  obtain ⟨h0, h1, h2, h3, -⟩ := coset_census
  rw [hsplit]
  rw [Finset.card_union_of_disjoint, Finset.card_union_of_disjoint,
    Finset.card_union_of_disjoint, h0, h1, h2, h3]
  · simp only [Finset.disjoint_left, Finset.mem_filter]
    omega
  · simp only [Finset.disjoint_left, Finset.mem_filter, Finset.mem_union]
    omega
  · simp only [Finset.disjoint_left, Finset.mem_filter, Finset.mem_union]
    omega

/-! ## The coset weight is the distance to the code -/

/-- `cosetWt (syn v)` is exactly the distance from `v` to the nearest codeword:
it is attained, and nothing is nearer. -/
theorem cosetWt_eq_dist (v : Word) :
    (∃ c : Word, IsCodeword c ∧ hdist v c = cosetWt (syn v)) ∧
    (∀ c : Word, IsCodeword c → cosetWt (syn v) ≤ hdist v c) := by
  constructor
  · obtain ⟨u, hsu, hwu⟩ := exists_wt_eq_cosetWt (syn v)
    refine ⟨symmDiff v u, ?_, ?_⟩
    · show syn (symmDiff v u) = 0
      rw [syn_symmDiff, hsu]
      funext i
      have hy : ∀ y : ZMod 2, y + y = 0 := by decide
      exact hy _
    · rw [hdist_eq_wt_symmDiff, symmDiff_symmDiff_self]
      exact hwu
  · intro c hc
    have hsyn : syn (symmDiff v c) = syn v := syn_symmDiff_codeword hc
    calc cosetWt (syn v) = cosetWt (syn (symmDiff v c)) := by rw [hsyn]
      _ ≤ wt (symmDiff v c) := cosetWt_le _
      _ = hdist v c := (hdist_eq_wt_symmDiff v c).symm

end GLM.Golay24
