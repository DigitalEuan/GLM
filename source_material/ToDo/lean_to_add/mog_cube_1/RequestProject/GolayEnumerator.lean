import RequestProject.GolaySteiner

/-!
# The weight enumerator of *any* code with the four defining properties

`FINAL_REPORT.md` §8 item 4 is the one standard fact the package quoted rather
than proved:

> **Classification.**  `IsGolay` is the four defining properties; that they pin
> the extended Golay code up to equivalence is the one standard fact the package
> quotes rather than proves.

Full uniqueness is not proved here either.  What is proved is the first half of
it, and the half the package actually leans on: **every** code satisfying the
four properties — dimension 12, self-orthogonal, doubly even, minimum weight 8 —
has the Golay weight distribution

    1, 759, 2576, 759, 1

on weights `0, 8, 12, 16, 24`.  So the numbers `CubeSurfaceMOG.lean`,
`ThreeCube.lean` and `CubeStabiliser.lean` each verify by enumeration for their
particular code are not properties of those constructions: they follow from the
definition, for every code that meets it.

The proof uses only what `GolaySteiner.lean` already established, and no
MacWilliams identity:

* `octad_count` — double counting 5-sets against octads.  Every 5-set lies in
  exactly one octad (`unique_octad`) and every octad contains `C(8,5) = 56` of
  them, so there are `C(24,5) / 56 = 759` octads.
* `card_wt_eq_eight` — a codeword is determined by its support, so the weight-8
  words are in bijection with the octads.
* `card_wt_eq_sixteen` — complementation is an involution of the code carrying
  weight 8 to weight 16.
* `card_wt_eq_twelve` — what is left of the 4096 codewords.
-/

namespace GolayInv

open Finset

variable {C : Submodule (ZMod 2) V}

/-! ## 1. A codeword is its support -/

theorem supp_injective : Function.Injective (supp : V → Finset (Fin 24)) := by
  intro c d h
  funext i
  have hx : ∀ x : ZMod 2, x ≠ 1 → x = 0 := by decide
  by_cases hc : c i = 1
  · have : i ∈ supp d := h ▸ mem_supp.mpr hc
    rw [hc, mem_supp.mp this]
  · have hd : i ∉ supp d := fun hi => hc (mem_supp.mp (h ▸ hi))
    rw [hx _ hc, hx _ (fun hh => hd (mem_supp.mpr hh))]

/-! ## 2. There are 759 octads -/

/-- The 5-subsets of the 24 points. -/
noncomputable def fiveSets : Finset (Finset (Fin 24)) := powersetCard 5 (univ : Finset (Fin 24))

theorem card_fiveSets : fiveSets.card = 42504 := by
  rw [fiveSets, card_powersetCard, card_univ]
  rfl

/-- The 5-subsets of an octad are `C(8,5) = 56` in number. -/
theorem card_fiveSets_in (B : Finset (Fin 24)) (hB : B.card = 8) :
    (fiveSets.filter fun T => T ⊆ B).card = 56 := by
  have hfil : (fiveSets.filter fun T => T ⊆ B) = powersetCard 5 B := by
    ext T
    simp only [fiveSets, mem_filter, mem_powersetCard, subset_univ, true_and]
    exact ⟨fun h => ⟨h.2, h.1⟩, fun h => ⟨h.2, h.1⟩⟩
  rw [hfil, card_powersetCard, hB]
  rfl

/-- **759 octads**, by double counting: `C(24,5) = 56 · 759`. -/
theorem octad_count (h : IsGolay C) : (octads C).card = 759 := by
  classical
  have hdouble : ∑ T ∈ fiveSets, ((octads C).filter fun B => T ⊆ B).card
      = ∑ B ∈ octads C, (fiveSets.filter fun T => T ⊆ B).card := by
    simp only [card_filter]
    exact Finset.sum_comm
  have hleft : ∑ T ∈ fiveSets, ((octads C).filter fun B => T ⊆ B).card = 42504 := by
    have hone : ∀ T ∈ fiveSets, ((octads C).filter fun B => T ⊆ B).card = 1 := by
      intro T hT
      have hT5 : T.card = 5 := (mem_powersetCard.mp hT).2
      obtain ⟨B, ⟨hB, hTB⟩, huniq⟩ := unique_octad h hT5
      refine card_eq_one.mpr ⟨B, ?_⟩
      ext B'
      simp only [mem_filter, mem_singleton]
      exact ⟨fun hB' => huniq B' hB', fun hB' => hB' ▸ ⟨hB, hTB⟩⟩
    rw [Finset.sum_congr rfl hone]
    simp [card_fiveSets]
  have hright : ∑ B ∈ octads C, (fiveSets.filter fun T => T ⊆ B).card
      = 56 * (octads C).card := by
    rw [Finset.sum_congr rfl fun B hB => card_fiveSets_in B (card_of_mem_octads hB)]
    simp [Nat.mul_comm]
  rw [hleft, hright] at hdouble
  omega

/-! ## 3. The five weight classes -/

/-- The codewords of a given weight. -/
noncomputable def wtClass (C : Submodule (ZMod 2) V) (k : ℕ) : Finset V :=
  (cwords C).filter fun c => wt c = k

/-- **759 words of weight 8** — one for each octad. -/
theorem card_wt_eq_eight (h : IsGolay C) : (wtClass C 8).card = 759 := by
  classical
  have himg : (wtClass C 8).image supp = octads C := rfl
  have hinj : Set.InjOn supp (wtClass C 8) := fun a _ b _ hab => supp_injective hab
  have := Finset.card_image_of_injOn hinj
  rw [himg, octad_count h] at this
  exact this.symm

/-- **759 words of weight 16** — the complements of the octads. -/
theorem card_wt_eq_sixteen (h : IsGolay C) : (wtClass C 16).card = 759 := by
  classical
  have hmap : ∀ c ∈ wtClass C 8, (fun i => 1 + c i : V) ∈ wtClass C 16 := by
    intro c hc
    simp only [wtClass, mem_filter, mem_cwords] at hc ⊢
    refine ⟨C.add_mem (allOnes_mem h) hc.1, ?_⟩
    rw [wt_complement c, hc.2]
  have hmap' : ∀ c ∈ wtClass C 16, (fun i => 1 + c i : V) ∈ wtClass C 8 := by
    intro c hc
    simp only [wtClass, mem_filter, mem_cwords] at hc ⊢
    refine ⟨C.add_mem (allOnes_mem h) hc.1, ?_⟩
    rw [wt_complement c, hc.2]
  have hinv : ∀ c : V, (fun i => 1 + (1 + c i) : V) = c := by
    intro c
    funext i
    have : (1 : ZMod 2) + 1 = 0 := by decide
    rw [← add_assoc, this, zero_add]
  have hcard := Finset.card_bij' (fun c _ => (fun i => 1 + c i : V))
    (fun c _ => (fun i => 1 + c i : V)) hmap hmap'
    (fun c _ => hinv c) (fun c _ => hinv c)
  rw [← hcard, card_wt_eq_eight h]

/-- Only the zero word has weight 0. -/
theorem card_wt_eq_zero : (wtClass C 0).card = 1 := by
  classical
  refine card_eq_one.mpr ⟨0, ?_⟩
  ext c
  simp only [wtClass, mem_filter, mem_cwords, mem_singleton]
  constructor
  · rintro ⟨_, hw⟩
    exact wt_eq_zero_iff.mp hw
  · rintro rfl
    exact ⟨C.zero_mem, by simp [wt, supp]⟩

/-- Only the all-ones word has weight 24. -/
theorem card_wt_eq_twentyfour (h : IsGolay C) : (wtClass C 24).card = 1 := by
  classical
  refine card_eq_one.mpr ⟨(fun _ => 1 : V), ?_⟩
  ext c
  simp only [wtClass, mem_filter, mem_cwords, mem_singleton]
  constructor
  · rintro ⟨_, hw⟩
    exact eq_allOnes_of_wt_24 hw
  · rintro rfl
    refine ⟨allOnes_mem h, ?_⟩
    simp [wt, supp]

/-- The five classes exhaust the code. -/
theorem card_cwords_split (h : IsGolay C) :
    (cwords C).card = (wtClass C 0).card + (wtClass C 8).card + (wtClass C 12).card
      + (wtClass C 16).card + (wtClass C 24).card := by
  classical
  have hfib := Finset.card_eq_sum_card_fiberwise
    (f := fun c : V => wt c) (s := cwords C) (t := ({0, 8, 12, 16, 24} : Finset ℕ))
    (fun c hc => by
      have hc' : c ∈ cwords C := by simpa using hc
      have hw := wt_mem_weights h (mem_cwords.mp hc')
      simp only [coe_insert, Set.mem_insert_iff, coe_singleton, Set.mem_singleton_iff]
      tauto)
  rw [hfib]
  simp only [wtClass]
  rw [show ({0, 8, 12, 16, 24} : Finset ℕ) = {0, 8, 12, 16, 24} from rfl]
  repeat rw [Finset.sum_insert (by decide)]
  rw [Finset.sum_singleton]
  ring

/-- **The weight enumerator of any code with the four defining properties**:
`1, 759, 2576, 759, 1`.  The numbers the package verifies by enumeration for
each particular construction are consequences of the definition. -/
theorem golay_weight_enumerator (h : IsGolay C) :
    (wtClass C 0).card = 1 ∧ (wtClass C 8).card = 759 ∧ (wtClass C 12).card = 2576 ∧
      (wtClass C 16).card = 759 ∧ (wtClass C 24).card = 1 := by
  have hsplit := card_cwords_split h
  rw [card_cwords h, card_wt_eq_zero, card_wt_eq_eight h, card_wt_eq_sixteen h,
    card_wt_eq_twentyfour h] at hsplit
  exact ⟨card_wt_eq_zero, card_wt_eq_eight h, by omega, card_wt_eq_sixteen h,
    card_wt_eq_twentyfour h⟩

end GolayInv
