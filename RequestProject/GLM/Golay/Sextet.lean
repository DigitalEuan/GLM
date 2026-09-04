/-
# Six equidistant codewords: the sextet at the covering radius

The engineering directive that motivates this file asks for the tie at the
Golay covering radius to be carried forward as an *active parallel hypothesis
space* rather than broken arbitrarily.  It fixes the size of that space by
name — `GOLAY_COVERING_RADIUS_TIE_COUNT = 6`.  This file proves the constant,
for the actual code the substrate uses, together with everything the parallel
hypothesis engine needs in order to be well defined:

* `golay_min_weight` / `golay_min_distance_eight` — the code really is
  `[24, 12, 8]`: every nonzero codeword has weight at least `8`, and weight `8`
  occurs.
* `unique_nearest_of_le_three` — inside the packing radius the nearest codeword
  is unique, so there is nothing to carry forward.
* `covering_radius_le_four`, `covering_radius_eq_four` — every word is within
  distance `4` of the code, and some words are at exactly `4`.
* `ties_card_eq_six` — **the constant**: a word at distance `4` from the code
  has exactly six nearest codewords.
* `ties_pairwise_disjoint_diffs`, `sextet_partition` — the six error patterns
  are pairwise disjoint tetrads whose union is the whole 24-point set: the six
  tetrads of a MOG sextet.
* `ties_pairwise_hdist_eight` — the six candidates are mutually as far apart as
  the code allows, so the hypothesis space is maximally spread.

Everything specific to this `B` is settled by five finite computations over the
2,325 words of weight `≤ 3` and the 10,626 tetrads, checked by the kernel-level
evaluator; the mathematics around them is ordinary coset algebra.
-/
import RequestProject.GLM.Golay.Code

namespace GLM.Golay24

open Finset

/-! ## Enumerations, and syndromes as machine keys -/

/-- Every word of weight at most `3`: the error patterns the code corrects. -/
def small : Finset Word :=
  powersetCard 0 univ ∪ powersetCard 1 univ ∪ powersetCard 2 univ ∪ powersetCard 3 univ

/-- Every word of weight exactly `4`: the tetrads. -/
def tetrads : Finset Word := powersetCard 4 univ

theorem mem_tetrads {s : Word} : s ∈ tetrads ↔ wt s = 4 := by
  simp [tetrads, Finset.mem_powersetCard, wt]

theorem mem_small {s : Word} : s ∈ small ↔ wt s ≤ 3 := by
  simp only [small, Finset.mem_union, Finset.mem_powersetCard, Finset.subset_univ, true_and, wt]
  omega

/-- A syndrome packed into a machine integer, so that the finite checks below
run over `ℕ` keys rather than over functions. -/
def packSyn (f : Syn) : ℕ := ∑ i : Fin 12, if f i = 1 then 2 ^ (i : ℕ) else 0

/-- The inverse packing, used only to prove `packSyn` injective. -/
def unpackSyn (n : ℕ) : Syn := fun i => if n.testBit i then 1 else 0

theorem unpackSyn_packSyn (f : Syn) : unpackSyn (packSyn f) = f := by
  revert f; native_decide

theorem packSyn_injective : Function.Injective packSyn := by
  intro f g h
  rw [← unpackSyn_packSyn f, ← unpackSyn_packSyn g, h]

/-- The syndrome key of a word. -/
def key (s : Word) : ℕ := packSyn (syn s)

theorem key_eq_iff {a b : Word} : key a = key b ↔ syn a = syn b :=
  ⟨fun h => packSyn_injective h, fun h => by unfold key; rw [h]⟩

/-- The keys of the words of weight at most `3`. -/
def skeys : Multiset ℕ := small.val.map key

/-- The keys of the tetrads. -/
def tkeys : Multiset ℕ := tetrads.val.map key

/-- The tetrads, tagged with their keys. -/
def tpairs : Multiset (ℕ × Word) := tetrads.val.map (fun s => (key s, s))

/-! ## The five finite checks -/

set_option maxRecDepth 100000

/-- **Check 1.**  Distinct words of weight `≤ 3` have distinct syndromes: the
code corrects every error of weight at most `3`. -/
theorem skeys_nodup : skeys.Nodup := by native_decide

/-- **Check 2.**  Every syndrome realised by a tetrad is realised by exactly six
tetrads.  This is the constant `GOLAY_COVERING_RADIUS_TIE_COUNT`. -/
theorem tkeys_count_six : ∀ k ∈ tkeys, tkeys.count k = 6 := by native_decide

/-- **Check 3.**  No tetrad shares a syndrome with a word of weight `≤ 3`: the
weight-4 cosets really have weight `4`. -/
theorem tkeys_not_mem_skeys : ∀ k ∈ tkeys, k ∉ skeys := by native_decide

/-- **Check 4.**  Two distinct tetrads with the same syndrome are disjoint. -/
theorem tpairs_disjoint :
    ∀ p ∈ tpairs, ∀ q ∈ tpairs, p.1 = q.1 → p.2 ≠ q.2 → Disjoint p.2 q.2 := by
  native_decide

/-- **Check 5.**  The words of weight `≤ 4` realise 4,096 distinct syndromes —
all of them.  The covering radius is therefore at most `4`. -/
theorem keys_card : (skeys + tkeys).toFinset.card = 4096 := by native_decide

/-! ## Coset algebra -/

/-- Words of weight `≤ 3` are determined by their syndrome. -/
theorem small_syn_inj {a b : Word} (ha : wt a ≤ 3) (hb : wt b ≤ 3)
    (h : syn a = syn b) : a = b := by
  have hkey : key a = key b := key_eq_iff.2 h
  exact Multiset.inj_on_of_nodup_map skeys_nodup a (mem_small.2 ha) b (mem_small.2 hb) hkey

/-- No word of weight `≤ 3` shares a syndrome with a tetrad. -/
theorem small_syn_ne_tetrad {a t : Word} (ha : wt a ≤ 3) (ht : wt t = 4) :
    syn a ≠ syn t := by
  intro h
  have hmem : key t ∈ tkeys := Multiset.mem_map_of_mem _ (mem_tetrads.2 ht)
  have hsmall : key a ∈ skeys := Multiset.mem_map_of_mem _ (mem_small.2 ha)
  exact tkeys_not_mem_skeys (key t) hmem (by rwa [← key_eq_iff.2 h])

/-- If `a ⊆ c`, then `c` is the symmetric difference of `a` and `c \ a`. -/
theorem symmDiff_sdiff_of_subset {a c : Word} (h : a ⊆ c) : symmDiff a (c \ a) = c := by
  ext i
  simp only [Finset.mem_symmDiff, Finset.mem_sdiff]
  constructor
  · rintro (⟨hi, _⟩ | ⟨⟨hi, _⟩, _⟩) <;> [exact h hi; exact hi]
  · intro hi
    by_cases hia : i ∈ a
    · exact Or.inl ⟨hia, by simp [hia]⟩
    · exact Or.inr ⟨⟨hi, hia⟩, hia⟩

/-- A codeword splits into two halves with equal syndromes. -/
theorem syn_eq_of_split {c a : Word} (hc : IsCodeword c) (h : a ⊆ c) :
    syn a = syn (c \ a) := by
  rw [syn_eq_iff_isCodeword_symmDiff, symmDiff_sdiff_of_subset h]
  exact hc

/-! ## The code is `[24, 12, 8]` -/

/-- **Minimum weight.**  Every nonzero codeword has weight at least `8`. -/
theorem golay_min_weight {c : Word} (hc : IsCodeword c) (hne : c ≠ ∅) : 8 ≤ wt c := by
  by_contra hlt
  push_neg at hlt
  unfold wt at hlt
  rcases Nat.lt_or_ge c.card 4 with hlt3 | hgt
  · -- a light codeword is the zero word
    have : c = ∅ := by
      refine small_syn_inj (by unfold wt; omega) (by simp [wt]) ?_
      rw [hc, syn_empty]
    exact hne this
  · -- split off three coordinates
    obtain ⟨a, hsub, hcard⟩ : ∃ a ⊆ c, a.card = 3 := Finset.exists_subset_card_eq (by omega)
    have hsplit : syn a = syn (c \ a) := syn_eq_of_split hc hsub
    have hbcard : (c \ a).card = c.card - 3 := by
      rw [Finset.card_sdiff, Finset.inter_eq_left.2 hsub, hcard]
    rcases Nat.lt_or_ge c.card 7 with h6 | h7
    · -- both halves have weight ≤ 3, so they coincide — impossible, they are disjoint
      have hb3 : wt (c \ a) ≤ 3 := by unfold wt; omega
      have heq : a = c \ a := small_syn_inj (by unfold wt; omega) hb3 hsplit
      have hdisj : Disjoint a (c \ a) := disjoint_sdiff_self_right
      rw [← heq] at hdisj
      have hempty : a = ∅ := disjoint_self.1 hdisj
      rw [hempty] at hcard
      simp at hcard
    · -- weight 7: a weight-3 word would share a syndrome with a tetrad
      have hb4 : wt (c \ a) = 4 := by unfold wt; omega
      exact small_syn_ne_tetrad (a := a) (t := c \ a) (by unfold wt; omega) hb4 hsplit

/-- Two distinct tetrads with the same syndrome differ by a codeword of weight
exactly `8`: an octad.  In particular the minimum distance `8` is attained. -/
theorem octad_of_tetrads {u u' : Word} (hu : wt u = 4) (hu' : wt u' = 4)
    (hne : u ≠ u') (hsyn : syn u = syn u') :
    IsCodeword (symmDiff u u') ∧ wt (symmDiff u u') = 8 := by
  have hdisj : Disjoint u u' := by
    have hmem : (key u, u) ∈ tpairs := Multiset.mem_map_of_mem _ (mem_tetrads.2 hu)
    have hmem' : (key u', u') ∈ tpairs := Multiset.mem_map_of_mem _ (mem_tetrads.2 hu')
    exact tpairs_disjoint _ hmem _ hmem' (key_eq_iff.2 hsyn) hne
  refine ⟨(syn_eq_iff_isCodeword_symmDiff u u').1 hsyn, ?_⟩
  have : symmDiff u u' = u ∪ u' := by
    ext i
    simp only [Finset.mem_symmDiff, Finset.mem_union]
    constructor
    · rintro (⟨hi, _⟩ | ⟨hi, _⟩) <;> [exact Or.inl hi; exact Or.inr hi]
    · rintro (hi | hi)
      · exact Or.inl ⟨hi, fun hc => (Finset.disjoint_left.1 hdisj hi) hc⟩
      · exact Or.inr ⟨hi, fun hc => (Finset.disjoint_left.1 hdisj hc) hi⟩
  unfold wt at hu hu' ⊢
  rw [this, Finset.card_union_of_disjoint hdisj, hu, hu']

/-! ## Cosets, and where a word sits -/

/-- A word sits at the covering radius when its coset contains a tetrad. -/
def CosetHasTetrad (v : Word) : Prop := ∃ t : Word, wt t = 4 ∧ syn t = syn v

/-- The words at distance `m` from `v` that are codewords correspond exactly to
the words of weight `m` in the coset of `v`. -/
theorem card_codewords_at_dist (v : Word) (m : ℕ) :
    #(univ.filter fun c => IsCodeword c ∧ hdist v c = m)
      = #(univ.filter fun u => wt u = m ∧ syn u = syn v) := by
  refine Finset.card_nbij' (fun c => symmDiff v c) (fun u => symmDiff v u) ?_ ?_ ?_ ?_
  · intro c hc
    simp only [Finset.coe_filter, Set.mem_setOf_eq, Finset.mem_univ, true_and] at hc ⊢
    exact ⟨hc.2, syn_symmDiff_codeword hc.1⟩
  · intro u hu
    simp only [Finset.coe_filter, Set.mem_setOf_eq, Finset.mem_univ, true_and] at hu ⊢
    refine ⟨?_, ?_⟩
    · show syn (symmDiff v u) = 0
      rw [syn_symmDiff, hu.2]
      funext i
      have hy : ∀ y : ZMod 2, y + y = 0 := by decide
      exact hy _
    · show hdist v (symmDiff v u) = m
      rw [hdist_eq_wt_symmDiff, symmDiff_symmDiff_self, hu.1]
  · intro c _; exact symmDiff_symmDiff_self v c
  · intro u _; exact symmDiff_symmDiff_self v u

/-- The weight-4 words of a coset, as a filter of the tetrads. -/
theorem filter_wt_four (v : Word) :
    (univ.filter fun u => wt u = 4 ∧ syn u = syn v)
      = tetrads.filter (fun u => syn u = syn v) := by
  ext u
  simp [mem_tetrads]

/-- **The tie count.**  Every syndrome class of tetrads has exactly six members. -/
theorem tetrad_class_card {t : Word} (ht : wt t = 4) :
    #(tetrads.filter fun u => syn u = syn t) = 6 := by
  have hmem : key t ∈ tkeys := Multiset.mem_map_of_mem _ (mem_tetrads.2 ht)
  have hcount := tkeys_count_six (key t) hmem
  rw [tkeys, Multiset.count_map] at hcount
  have hfil : Multiset.filter (fun a => key t = key a) tetrads.val
      = Multiset.filter (fun u => syn u = syn t) tetrads.val := by
    refine Multiset.filter_congr ?_
    intro u _
    constructor
    · intro h; exact (key_eq_iff.1 h).symm
    · intro h; exact key_eq_iff.2 h.symm
  rw [hfil] at hcount
  simpa [Finset.card, Finset.filter_val] using hcount

/-! ## The main theorems -/

/-- Inside the packing radius the nearest codeword is unique. -/
theorem unique_nearest_of_le_three {v c c' : Word} (hc : IsCodeword c) (hc' : IsCodeword c')
    (h : hdist v c ≤ 3) (h' : hdist v c' ≤ 3) : c = c' := by
  have h1 : syn (symmDiff v c) = syn v := syn_symmDiff_codeword hc
  have h2 : syn (symmDiff v c') = syn v := syn_symmDiff_codeword hc'
  have := small_syn_inj (a := symmDiff v c) (b := symmDiff v c') h h' (h1.trans h2.symm)
  have hcc : symmDiff v (symmDiff v c) = symmDiff v (symmDiff v c') := by rw [this]
  rwa [symmDiff_symmDiff_self, symmDiff_symmDiff_self] at hcc

/-- If the coset of `v` contains a tetrad, no codeword is nearer than `4`. -/
theorem dist_ge_four_of_cosetHasTetrad {v : Word} (h : CosetHasTetrad v)
    {c : Word} (hc : IsCodeword c) : 4 ≤ hdist v c := by
  obtain ⟨t, ht, hts⟩ := h
  by_contra hlt
  push_neg at hlt
  have hsyn : syn (symmDiff v c) = syn v := syn_symmDiff_codeword hc
  refine small_syn_ne_tetrad (a := symmDiff v c) (t := t) ?_ ht ?_
  · show wt (symmDiff v c) ≤ 3
    rw [← hdist_eq_wt_symmDiff]
    omega
  · rw [hsyn, hts]

/-- **Six equidistant codewords.**  A word whose coset contains a tetrad — that
is, a word at distance exactly `4` from the code — has exactly six nearest
codewords.  This is the directive's `GOLAY_COVERING_RADIUS_TIE_COUNT`. -/
theorem ties_card_eq_six {v : Word} (h : CosetHasTetrad v) :
    #(univ.filter fun c => IsCodeword c ∧ hdist v c = 4) = 6 := by
  obtain ⟨t, ht, hts⟩ := h
  rw [card_codewords_at_dist, filter_wt_four]
  have : (tetrads.filter fun u => syn u = syn v) = tetrads.filter fun u => syn u = syn t := by
    rw [hts]
  rw [this, tetrad_class_card ht]

/-- The six error patterns of a tie are pairwise disjoint. -/
theorem ties_pairwise_disjoint_diffs {v u u' : Word}
    (hu : wt u = 4) (hu' : wt u' = 4) (hsu : syn u = syn v) (hsu' : syn u' = syn v)
    (hne : u ≠ u') : Disjoint u u' := by
  have hmem : (key u, u) ∈ tpairs := Multiset.mem_map_of_mem _ (mem_tetrads.2 hu)
  have hmem' : (key u', u') ∈ tpairs := Multiset.mem_map_of_mem _ (mem_tetrads.2 hu')
  exact tpairs_disjoint _ hmem _ hmem' (key_eq_iff.2 (hsu.trans hsu'.symm)) hne

/-- **The sextet.**  The six weight-4 words of a coset at the covering radius
are pairwise disjoint tetrads whose union is the whole 24-point set: they
partition the coordinates into the six tetrads of a MOG sextet. -/
theorem sextet_partition {v : Word} (h : CosetHasTetrad v) :
    #(tetrads.filter fun u => syn u = syn v) = 6 ∧
    (∀ u ∈ tetrads.filter fun u => syn u = syn v,
      ∀ u' ∈ tetrads.filter fun u => syn u = syn v, u ≠ u' → Disjoint u u') ∧
    (tetrads.filter fun u => syn u = syn v).biUnion (fun u => u) = (univ : Word) := by
  obtain ⟨t, ht, hts⟩ := h
  have hcard : #(tetrads.filter fun u => syn u = syn v) = 6 := by
    have : (tetrads.filter fun u => syn u = syn v) = tetrads.filter fun u => syn u = syn t := by
      rw [hts]
    rw [this, tetrad_class_card ht]
  have hdisj : ∀ u ∈ tetrads.filter fun u => syn u = syn v,
      ∀ u' ∈ tetrads.filter fun u => syn u = syn v, u ≠ u' → Disjoint u u' := by
    intro u hu u' hu' hne
    simp only [Finset.mem_filter, mem_tetrads] at hu hu'
    exact ties_pairwise_disjoint_diffs hu.1 hu'.1 hu.2 hu'.2 hne
  refine ⟨hcard, hdisj, ?_⟩
  have hbcard : #((tetrads.filter fun u => syn u = syn v).biUnion (fun u => u)) = 24 := by
    rw [Finset.card_biUnion (t := fun u => u) (fun x hx y hy hxy => hdisj x hx y hy hxy)]
    have : ∀ u ∈ tetrads.filter fun u => syn u = syn v, (u : Word).card = 4 := by
      intro u hu
      simp only [Finset.mem_filter, mem_tetrads] at hu
      exact hu.1
    rw [Finset.sum_congr rfl this, Finset.sum_const, hcard]
    simp
  exact Finset.eq_univ_of_card _ (by simpa using hbcard)

/-- The six candidates are mutually at distance `8`, the minimum distance of the
code: the hypothesis space is as spread out as the code allows. -/
theorem ties_pairwise_hdist_eight {v c c' : Word}
    (hc : IsCodeword c) (hc' : IsCodeword c') (hd : hdist v c = 4) (hd' : hdist v c' = 4)
    (hne : c ≠ c') : hdist c c' = 8 := by
  have hu : wt (symmDiff v c) = 4 := hd
  have hu' : wt (symmDiff v c') = 4 := hd'
  have hsu : syn (symmDiff v c) = syn v := syn_symmDiff_codeword hc
  have hsu' : syn (symmDiff v c') = syn v := syn_symmDiff_codeword hc'
  have hnee : symmDiff v c ≠ symmDiff v c' := by
    intro hcon
    apply hne
    have := congrArg (fun x => symmDiff v x) hcon
    simpa [symmDiff_symmDiff_self] using this
  obtain ⟨_, hw⟩ := octad_of_tetrads hu hu' hnee (hsu.trans hsu'.symm)
  have : symmDiff (symmDiff v c) (symmDiff v c') = symmDiff c c' := by
    rw [symmDiff_symmDiff_symmDiff_comm]
    simp
  rwa [this] at hw

/-! ## The covering radius -/

/-- Every syndrome is realised by a word of weight at most `4`. -/
theorem exists_small_of_syn (v : Word) : ∃ u : Word, wt u ≤ 4 ∧ syn u = syn v := by
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
  have hmem : packSyn (syn v) ∈ K := by
    rw [heq]
    exact Finset.mem_image.2 ⟨syn v, Finset.mem_univ _, rfl⟩
  simp only [hK, Multiset.mem_toFinset, Multiset.mem_add] at hmem
  rcases hmem with hk | hk
  · obtain ⟨u, hu, hku⟩ := Multiset.mem_map.1 hk
    exact ⟨u, le_trans (mem_small.1 hu) (by norm_num), packSyn_injective hku⟩
  · obtain ⟨u, hu, hku⟩ := Multiset.mem_map.1 hk
    exact ⟨u, le_of_eq (mem_tetrads.1 hu), packSyn_injective hku⟩

/-- **Covering radius at most 4.**  Every word is within distance `4` of a
codeword. -/
theorem covering_radius_le_four (v : Word) : ∃ c : Word, IsCodeword c ∧ hdist v c ≤ 4 := by
  obtain ⟨u, hu, hsu⟩ := exists_small_of_syn v
  refine ⟨symmDiff v u, ?_, ?_⟩
  · show syn (symmDiff v u) = 0
    rw [syn_symmDiff, hsu]
    funext i
    have hy : ∀ y : ZMod 2, y + y = 0 := by decide
    exact hy _
  · rw [hdist_eq_wt_symmDiff, symmDiff_symmDiff_self]
    exact hu

/-- Either a word is corrected uniquely, or it sits at the covering radius with
six candidates.  There is no third case. -/
theorem coset_dichotomy (v : Word) :
    (∃ u : Word, wt u ≤ 3 ∧ syn u = syn v) ∨ CosetHasTetrad v := by
  obtain ⟨u, hu, hsu⟩ := exists_small_of_syn v
  rcases Nat.lt_or_ge (wt u) 4 with h | h
  · exact Or.inl ⟨u, by omega, hsu⟩
  · exact Or.inr ⟨u, by omega, hsu⟩

/-- **The covering radius is exactly 4.**  Some word is at distance `4` from
every codeword, and has six nearest ones. -/
theorem covering_radius_eq_four :
    ∃ v : Word, (∀ c : Word, IsCodeword c → 4 ≤ hdist v c) ∧
      #(univ.filter fun c => IsCodeword c ∧ hdist v c = 4) = 6 := by
  classical
  -- any tetrad is at distance 4 from the code, because its coset has weight 4
  obtain ⟨t, ht⟩ : ∃ t : Word, wt t = 4 := by
    refine ⟨{0, 1, 2, 3}, ?_⟩
    decide
  have hcos : CosetHasTetrad t := ⟨t, ht, rfl⟩
  exact ⟨t, fun c hc => dist_ge_four_of_cosetHasTetrad hcos hc, ties_card_eq_six hcos⟩

/-- **The code is `[24, 12, 8]`.**  Nonzero codewords have weight at least `8`,
and weight `8` is attained. -/
theorem golay_min_distance_eight :
    (∀ c : Word, IsCodeword c → c ≠ ∅ → 8 ≤ wt c) ∧
    (∃ c : Word, IsCodeword c ∧ wt c = 8) := by
  refine ⟨fun c hc hne => golay_min_weight hc hne, ?_⟩
  -- two distinct tetrads in one syndrome class differ by an octad
  obtain ⟨t, ht⟩ : ∃ t : Word, wt t = 4 := ⟨{0, 1, 2, 3}, by decide⟩
  have hcard : #(tetrads.filter fun u => syn u = syn t) = 6 := tetrad_class_card ht
  have hone : ∃ u ∈ tetrads.filter fun u => syn u = syn t, u ≠ t := by
    by_contra hcon
    push_neg at hcon
    have hsub : (tetrads.filter fun u => syn u = syn t) ⊆ {t} := by
      intro u hu; simp [hcon u hu]
    have := Finset.card_le_card hsub
    simp [hcard] at this
  obtain ⟨u, hu, hne⟩ := hone
  simp only [Finset.mem_filter, mem_tetrads] at hu
  obtain ⟨hcw, hw⟩ := octad_of_tetrads hu.1 ht hne hu.2
  exact ⟨symmDiff u t, hcw, hw⟩

end GLM.Golay24
