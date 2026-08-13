import RequestProject.GolayCode

/-!
# The octads of a Golay code form a Steiner system `S(5,8,24)`

Second of the three files.  `GolayCode.lean` proved that exactly `2^(12-k)`
codewords carry any prescribed pattern on `k ≤ 7` coordinates.  That is enough
to pin the number of octads through five given points, by counting moments —
no weight enumerator, no MacWilliams identity, no uniqueness theorem.

Fix a 5-set `T` and let `A` be the codewords that are `1` all over `T`.  Then

* `|A| = 2^7 = 128`;
* summing `wt c - 5` over `A` counts pairs *(codeword, point outside `T` it
  covers)*, which is `19 · 2^6`;
* summing `(wt c - 5) choose 2` counts pairs *(codeword, 2-set outside `T` it
  covers)*, which is `171 · 2^5`.

Every word of `A` has weight `8`, `12`, `16` or `24`, and only the all-ones
word has weight 24.  Three linear equations in three unknowns then force

    #octads through T = 1,   #weight-12 words = 48,   #weight-16 words = 78.

`unique_octad` is the first of these: **any five of the 24 points lie in exactly
one octad**, which is the Steiner system `S(5,8,24)`.
-/

namespace GolayInv

open Finset

variable {C : Submodule (ZMod 2) V}

/-! ## 1. Two double counts -/

/-- Counting the pairs *(vector of `A`, point of `D` in its support)* two
ways. -/
theorem sum_card_supp_inter (A : Finset V) (D : Finset (Fin 24)) :
    ∑ c ∈ A, ((supp c) ∩ D).card = ∑ p ∈ D, (A.filter fun c => c p = 1).card := by
  classical
  have h1 : ∀ c : V, ((supp c) ∩ D).card = ∑ p ∈ D, if c p = 1 then 1 else 0 := by
    intro c
    have : (supp c) ∩ D = D.filter fun p => c p = 1 := by
      ext p
      simp [mem_supp, and_comm]
    rw [this, Finset.card_filter]
  simp only [h1, Finset.card_filter]
  exact Finset.sum_comm

/-- Counting the pairs *(vector of `A`, 2-subset of `D` inside its support)*
two ways. -/
theorem sum_card_pairs (A : Finset V) (D : Finset (Fin 24)) :
    ∑ c ∈ A, ((D.powersetCard 2).filter fun P => P ⊆ supp c).card
      = ∑ P ∈ D.powersetCard 2, (A.filter fun c => P ⊆ supp c).card := by
  classical
  simp only [Finset.card_filter]
  exact Finset.sum_comm

/-! ## 2. The words that cover a 5-set -/

/-- The codewords that are `1` on all of `T`. -/
noncomputable def cover (C : Submodule (ZMod 2) V) (T : Finset (Fin 24)) : Finset V :=
  (cwords C).filter fun c => ∀ i ∈ T, c i = 1

theorem mem_cover {T : Finset (Fin 24)} {c : V} :
    c ∈ cover C T ↔ (c ∈ C ∧ ∀ i ∈ T, c i = 1) := by
  simp [cover, mem_cwords]

/-- The pattern on `T` that `cover` prescribes. -/
theorem cover_eq_fiber (T : Finset (Fin 24)) :
    cover C T = (cwords C).filter fun c => ∀ i ∈ T, c i = (fun _ => 1 : V) i := rfl

/-- There are `2^7` of them. -/
theorem card_cover (h : IsGolay C) {T : Finset (Fin 24)} (hT : T.card = 5) :
    (cover C T).card = 128 := by
  rw [cover_eq_fiber, fiber_card h (by omega) (fun _ => 1), hT]
  norm_num

/-- A covering word has weight at least five, hence is nonzero. -/
theorem five_le_wt_of_mem_cover {T : Finset (Fin 24)} (hT : T.card = 5)
    {c : V} (hc : c ∈ cover C T) : 5 ≤ wt c := by
  rw [mem_cover] at hc
  have : T ⊆ supp c := fun i hi => mem_supp.mpr (hc.2 i hi)
  calc 5 = T.card := hT.symm
    _ ≤ (supp c).card := Finset.card_le_card this
    _ = wt c := rfl

/-- Each has weight 8, 12, 16 or 24. -/
theorem wt_of_mem_cover (h : IsGolay C) {T : Finset (Fin 24)} (hT : T.card = 5)
    {c : V} (hc : c ∈ cover C T) :
    wt c = 8 ∨ wt c = 12 ∨ wt c = 16 ∨ wt c = 24 := by
  have h5 := five_le_wt_of_mem_cover hT hc
  rcases wt_mem_weights h (mem_cover.mp hc).1 with h0 | h8 | h12 | h16 | h24
  · omega
  · exact Or.inl h8
  · exact Or.inr (Or.inl h12)
  · exact Or.inr (Or.inr (Or.inl h16))
  · exact Or.inr (Or.inr (Or.inr h24))

/-- A vector of weight 24 is the all-ones vector. -/
theorem eq_allOnes_of_wt_24 {c : V} (hc : wt c = 24) : c = (fun _ => 1 : V) := by
  classical
  have hsupp : supp c = univ := by
    apply Finset.eq_univ_of_card
    simpa [wt] using hc
  funext i
  have : i ∈ supp c := by rw [hsupp]; exact Finset.mem_univ i
  exact mem_supp.mp this

/-- Exactly one of them has weight 24, namely the all-ones word. -/
theorem card_cover_wt24 (h : IsGolay C) {T : Finset (Fin 24)} :
    ((cover C T).filter fun c => wt c = 24).card = 1 := by
  classical
  have hset : ((cover C T).filter fun c => wt c = 24) = {(fun _ => 1 : V)} := by
    ext c
    simp only [Finset.mem_filter, Finset.mem_singleton]
    constructor
    · rintro ⟨_, h24⟩
      exact eq_allOnes_of_wt_24 h24
    · rintro rfl
      refine ⟨mem_cover.mpr ⟨allOnes_mem h, fun i _ => rfl⟩, ?_⟩
      have : supp (fun _ => 1 : V) = univ := by
        ext i; simp [mem_supp]
      simp [wt, this]
  rw [hset, Finset.card_singleton]

/-- The first moment: `∑ (wt c - 5) = 19 · 64`. -/
theorem cover_moment_one (h : IsGolay C) {T : Finset (Fin 24)} (hT : T.card = 5) :
    ∑ c ∈ cover C T, (wt c - 5) = 19 * 64 := by
  classical
  have hstep : ∀ c ∈ cover C T, wt c - 5 = ((supp c) ∩ Tᶜ).card := by
    intro c hc
    rw [mem_cover] at hc
    have hTsub : T ⊆ supp c := fun i hi => mem_supp.mpr (hc.2 i hi)
    have hsplit : ((supp c) ∩ T).card + ((supp c) ∩ Tᶜ).card = (supp c).card := by
      rw [← Finset.sdiff_eq_inter_compl]
      exact Finset.card_inter_add_card_sdiff _ _
    have hT' : (supp c) ∩ T = T := Finset.inter_eq_right.mpr hTsub
    rw [hT', hT] at hsplit
    simp only [wt]
    omega
  rw [Finset.sum_congr rfl hstep, sum_card_supp_inter]
  have hterm : ∀ p ∈ Tᶜ, ((cover C T).filter fun c => c p = 1).card = 64 := by
    intro p hp
    have hpT : p ∉ T := by simpa using hp
    have hins : ((cover C T).filter fun c => c p = 1)
        = (cwords C).filter fun c => ∀ i ∈ insert p T, c i = (fun _ => 1 : V) i := by
      ext c
      simp only [Finset.mem_filter, cover, Finset.mem_insert]
      constructor
      · rintro ⟨⟨hcw, hcT⟩, hcp⟩
        exact ⟨hcw, by rintro i (rfl | hi); · exact hcp
                       · exact hcT i hi⟩
      · rintro ⟨hcw, hall⟩
        exact ⟨⟨hcw, fun i hi => hall i (Or.inr hi)⟩, hall p (Or.inl rfl)⟩
    have hcard : (insert p T).card = 6 := by
      rw [Finset.card_insert_of_notMem hpT, hT]
    rw [hins, fiber_card h (by rw [hcard]; omega) (fun _ => 1), hcard]
    norm_num
  rw [Finset.sum_congr rfl hterm, Finset.sum_const, Finset.card_compl, hT]
  norm_num

/-- The second moment: `∑ (wt c - 5) choose 2 = 171 · 32`. -/
theorem cover_moment_two (h : IsGolay C) {T : Finset (Fin 24)} (hT : T.card = 5) :
    ∑ c ∈ cover C T, Nat.choose (wt c - 5) 2 = 171 * 32 := by
  classical
  have hstep : ∀ c ∈ cover C T,
      Nat.choose (wt c - 5) 2 = ((Tᶜ.powersetCard 2).filter fun P => P ⊆ supp c).card := by
    intro c hc
    have hcc := hc
    rw [mem_cover] at hcc
    have hTsub : T ⊆ supp c := fun i hi => mem_supp.mpr (hcc.2 i hi)
    have hsplit : ((supp c) ∩ T).card + ((supp c) ∩ Tᶜ).card = (supp c).card := by
      rw [← Finset.sdiff_eq_inter_compl]
      exact Finset.card_inter_add_card_sdiff _ _
    have hT' : (supp c) ∩ T = T := Finset.inter_eq_right.mpr hTsub
    rw [hT', hT] at hsplit
    have hfil : ((Tᶜ.powersetCard 2).filter fun P => P ⊆ supp c)
        = (Tᶜ ∩ supp c).powersetCard 2 := by
      ext P
      simp only [Finset.mem_filter, Finset.mem_powersetCard, Finset.subset_inter_iff]
      tauto
    rw [hfil, Finset.card_powersetCard]
    congr 1
    rw [Finset.inter_comm]
    simp only [wt] at hsplit ⊢
    omega
  rw [Finset.sum_congr rfl hstep, sum_card_pairs]
  have hterm : ∀ P ∈ Tᶜ.powersetCard 2,
      ((cover C T).filter fun c => P ⊆ supp c).card = 32 := by
    intro P hP
    rw [Finset.mem_powersetCard] at hP
    obtain ⟨hPT, hP2⟩ := hP
    have hdisj : Disjoint T P := by
      refine Finset.disjoint_left.mpr fun a ha haP => ?_
      have := hPT haP
      simp at this
      exact this ha
    have hins : ((cover C T).filter fun c => P ⊆ supp c)
        = (cwords C).filter fun c => ∀ i ∈ T ∪ P, c i = (fun _ => 1 : V) i := by
      ext c
      simp only [Finset.mem_filter, cover, Finset.mem_union]
      constructor
      · rintro ⟨⟨hcw, hcT⟩, hcP⟩
        refine ⟨hcw, ?_⟩
        rintro i (hi | hi)
        · exact hcT i hi
        · exact mem_supp.mp (hcP hi)
      · rintro ⟨hcw, hall⟩
        refine ⟨⟨hcw, fun i hi => hall i (Or.inl hi)⟩, ?_⟩
        intro i hi
        exact mem_supp.mpr (hall i (Or.inr hi))
    have hcard : (T ∪ P).card = 7 := by
      rw [Finset.card_union_of_disjoint hdisj, hT, hP2]
    rw [hins, fiber_card h (le_of_eq hcard) (fun _ => 1), hcard]
    norm_num
  rw [Finset.sum_congr rfl hterm, Finset.sum_const, Finset.card_powersetCard,
    Finset.card_compl, hT]
  norm_num
  decide

/-! ## 3. Solving for the number of octads -/

/-- Summing any function of the weight over the covering words, split by
weight. -/
theorem cover_sum_split (h : IsGolay C) {T : Finset (Fin 24)} (hT : T.card = 5) (f : ℕ → ℕ) :
    ∑ c ∈ cover C T, f (wt c)
      = ((cover C T).filter fun c => wt c = 8).card * f 8
      + ((cover C T).filter fun c => wt c = 12).card * f 12
      + ((cover C T).filter fun c => wt c = 16).card * f 16
      + ((cover C T).filter fun c => wt c = 24).card * f 24 := by
  classical
  have hmaps : ∀ c ∈ cover C T, wt c ∈ ({8, 12, 16, 24} : Finset ℕ) := by
    intro c hc
    rcases wt_of_mem_cover h hT hc with hw | hw | hw | hw <;> simp [hw]
  rw [← Finset.sum_fiberwise_of_maps_to hmaps (fun c => f (wt c))]
  have hin : ∀ w : ℕ, ∑ c ∈ (cover C T).filter (fun c => wt c = w), f (wt c)
      = ((cover C T).filter fun c => wt c = w).card * f w := by
    intro w
    rw [Finset.sum_congr rfl (fun c hc => by
      rw [(Finset.mem_filter.mp hc).2]), Finset.sum_const, smul_eq_mul]
  rw [show ({8, 12, 16, 24} : Finset ℕ) = {8, 12, 16, 24} from rfl]
  rw [Finset.sum_insert (by decide), Finset.sum_insert (by decide),
    Finset.sum_insert (by decide), Finset.sum_singleton]
  rw [hin, hin, hin, hin]
  ring

/-- **Exactly one codeword of weight 8 covers a given 5-set.** -/
theorem card_cover_wt8 (h : IsGolay C) {T : Finset (Fin 24)} (hT : T.card = 5) :
    ((cover C T).filter fun c => wt c = 8).card = 1 := by
  classical
  set n8 := ((cover C T).filter fun c => wt c = 8).card with hn8
  set n12 := ((cover C T).filter fun c => wt c = 12).card with hn12
  set n16 := ((cover C T).filter fun c => wt c = 16).card with hn16
  set n24 := ((cover C T).filter fun c => wt c = 24).card with hn24
  have e0 : n8 + n12 + n16 + n24 = 128 := by
    have hs := cover_sum_split h hT (fun _ => 1)
    simp only [mul_one, Finset.sum_const, smul_eq_mul, card_cover h hT] at hs
    omega
  have e1 : 3 * n8 + 7 * n12 + 11 * n16 + 19 * n24 = 1216 := by
    have hsplit := cover_sum_split h hT (fun w => w - 5)
    rw [cover_moment_one h hT] at hsplit
    norm_num at hsplit
    omega
  have e2 : 3 * n8 + 21 * n12 + 55 * n16 + 171 * n24 = 5472 := by
    have hsplit := cover_sum_split h hT (fun w => Nat.choose (w - 5) 2)
    rw [cover_moment_two h hT] at hsplit
    have c8 : Nat.choose (8 - 5) 2 = 3 := rfl
    have c12 : Nat.choose (12 - 5) 2 = 21 := rfl
    have c16 : Nat.choose (16 - 5) 2 = 55 := rfl
    have c24 : Nat.choose (24 - 5) 2 = 171 := rfl
    rw [c8, c12, c16, c24] at hsplit
    omega
  have e3 : n24 = 1 := card_cover_wt24 h
  omega

/-! ## 4. The Steiner system -/

/-- The octads: the supports of the weight-8 codewords. -/
noncomputable def octads (C : Submodule (ZMod 2) V) : Finset (Finset (Fin 24)) :=
  ((cwords C).filter fun c => wt c = 8).image supp

theorem mem_octads {B : Finset (Fin 24)} :
    B ∈ octads C ↔ ∃ c ∈ C, wt c = 8 ∧ supp c = B := by
  simp only [octads, Finset.mem_image, Finset.mem_filter, mem_cwords]
  constructor
  · rintro ⟨c, ⟨hc, hw⟩, hs⟩; exact ⟨c, hc, hw, hs⟩
  · rintro ⟨c, hc, hw, hs⟩; exact ⟨c, ⟨hc, hw⟩, hs⟩

theorem card_of_mem_octads {B : Finset (Fin 24)} (hB : B ∈ octads C) : B.card = 8 := by
  obtain ⟨c, _, hw, hs⟩ := mem_octads.mp hB
  rw [← hs]
  exact hw

/-- **The Steiner system `S(5,8,24)`.**  Any five of the 24 points lie in
exactly one octad. -/
theorem unique_octad (h : IsGolay C) {T : Finset (Fin 24)} (hT : T.card = 5) :
    ∃! B, B ∈ octads C ∧ T ⊆ B := by
  classical
  obtain ⟨c, hc⟩ := Finset.card_eq_one.mp (card_cover_wt8 h hT)
  have hcmem : c ∈ (cover C T).filter fun c => wt c = 8 := by
    rw [hc]; exact Finset.mem_singleton_self c
  rw [Finset.mem_filter, mem_cover] at hcmem
  obtain ⟨⟨hcC, hcT⟩, hcw⟩ := hcmem
  refine ⟨supp c, ⟨mem_octads.mpr ⟨c, hcC, hcw, rfl⟩, fun i hi => mem_supp.mpr (hcT i hi)⟩, ?_⟩
  rintro B ⟨hB, hTB⟩
  obtain ⟨d, hdC, hdw, hds⟩ := mem_octads.mp hB
  have hdmem : d ∈ (cover C T).filter fun c => wt c = 8 := by
    rw [Finset.mem_filter, mem_cover]
    refine ⟨⟨hdC, fun i hi => ?_⟩, hdw⟩
    exact mem_supp.mp (hds ▸ hTB hi)
  rw [hc, Finset.mem_singleton] at hdmem
  rw [← hds, hdmem]

end GolayInv
