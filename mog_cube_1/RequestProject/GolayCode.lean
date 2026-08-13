import Mathlib

/-!
# Extended Golay codes, abstractly

`CubeStabiliser.lean` and the reports left one claim resting on a Python search:
that **no** Golay code on the 24 cells of the cube's surface is invariant under
the full symmetry group `O_h` of order 48, nor under `T_d`.  This file is the
first of three that replace that search by a proof.

Here the abstract object is set up.  A code is a subspace `C` of `F₂²⁴`; it is
an *extended Golay code* (`IsGolay`) when

* `finrank C = 12`;
* `C` is self-orthogonal — every two codewords, including a codeword with
  itself, have zero dot product;
* every nonzero codeword has weight at least `8`;
* every codeword has weight divisible by `4` (doubly even).

These are the standard defining properties: any code with them is equivalent to
the extended binary Golay code.  Nothing below uses uniqueness — every result is
proved from the four properties directly.

## What is proved here

* `dual_le` — self-orthogonality plus dimension 12 gives *self-duality*: a
  vector orthogonal to every codeword is itself a codeword.
* `restrict_surjective`, `fiber_card` — the consequence that does all the work
  later: because the code has no nonzero word of weight ≤ 7, the restriction of
  `C` to any `k ≤ 7` coordinates is onto, so **exactly `2^(12-k)` codewords
  carry any prescribed pattern on those coordinates**.
* `allOnes_mem`, `wt_mem_weights` — the weight of a codeword is `0`, `8`, `12`,
  `16` or `24`, and nothing else.
-/

namespace GolayInv

open Finset

instance : Fact (Nat.Prime 2) := ⟨Nat.prime_two⟩

/-! ## 0. The dot product as a bilinear form, on any finite index set -/

section Perp

variable {ι : Type} [Fintype ι] [DecidableEq ι]

/-- The dot product, as a bilinear form. -/
noncomputable def bilf : LinearMap.BilinForm (ZMod 2) (ι → ZMod 2) :=
  LinearMap.mk₂ (ZMod 2) (fun a b => ∑ i, a i * b i)
    (by intros; simp [add_mul, Finset.sum_add_distrib])
    (by intros; simp [Finset.mul_sum, mul_assoc])
    (by intros; simp [mul_add, Finset.sum_add_distrib])
    (by intros; simp [Finset.mul_sum]; ring_nf; simp [mul_comm, mul_left_comm])

omit [DecidableEq ι] in
@[simp] theorem bilf_apply (a b : ι → ZMod 2) : bilf a b = ∑ i, a i * b i := rfl

omit [DecidableEq ι] in
theorem bilf_isRefl : (bilf (ι := ι)).IsRefl :=
  LinearMap.IsSymm.isRefl ⟨fun x y => by simp [mul_comm]⟩

theorem bilf_orthogonal_top : (bilf (ι := ι)).orthogonal ⊤ = ⊥ := by
  ext a
  simp only [Submodule.mem_bot, LinearMap.BilinForm.mem_orthogonal_iff]
  constructor
  · intro h
    funext i
    have := h (Pi.single i 1) Submodule.mem_top
    simpa [LinearMap.BilinForm.IsOrtho, Pi.single_apply, mul_comm] using this
  · rintro rfl
    intro n _
    simp [LinearMap.BilinForm.IsOrtho]

/-- The dimension formula for the orthogonal complement of the dot product. -/
theorem finrank_add_orthogonal (U : Submodule (ZMod 2) (ι → ZMod 2)) :
    Module.finrank (ZMod 2) U + Module.finrank (ZMod 2) (bilf.orthogonal U)
      = Fintype.card ι := by
  have h := LinearMap.BilinForm.finrank_add_finrank_orthogonal
    (B := bilf (ι := ι)) bilf_isRefl U
  rw [bilf_orthogonal_top, inf_bot_eq] at h
  simpa using h

/-- A subspace with trivial orthogonal complement is everything. -/
theorem eq_top_of_orthogonal_trivial {U : Submodule (ZMod 2) (ι → ZMod 2)}
    (h : ∀ a : ι → ZMod 2, (∀ u ∈ U, ∑ i, a i * u i = 0) → a = 0) : U = ⊤ := by
  have hbot : bilf.orthogonal U = ⊥ := by
    ext a
    simp only [Submodule.mem_bot, LinearMap.BilinForm.mem_orthogonal_iff]
    constructor
    · intro ha
      refine h a fun u hu => ?_
      have := ha u hu
      simp only [LinearMap.BilinForm.IsOrtho, bilf_apply] at this
      simpa [mul_comm] using this
    · rintro rfl
      intro n _
      simp [LinearMap.BilinForm.IsOrtho]
  have := finrank_add_orthogonal U
  rw [hbot] at this
  simp only [finrank_bot, add_zero] at this
  exact Submodule.eq_top_of_finrank_eq (by simpa using this)

end Perp

/-! ## 1. Golay codes -/

/-- The ambient space: 24 coordinates over `F₂`. -/
abbrev V := Fin 24 → ZMod 2

/-- The support of a vector. -/
def supp (c : V) : Finset (Fin 24) := univ.filter fun i => c i = 1

/-- The Hamming weight. -/
def wt (c : V) : ℕ := (supp c).card

/-- The standard dot product. -/
def dotp (c d : V) : ZMod 2 := ∑ i, c i * d i

/-- An **extended Golay code**: a self-orthogonal, doubly even 12-dimensional
subspace of `F₂²⁴` whose nonzero words all have weight at least 8. -/
structure IsGolay (C : Submodule (ZMod 2) V) : Prop where
  dim : Module.finrank (ZMod 2) C = 12
  selfOrth : ∀ c ∈ C, ∀ d ∈ C, dotp c d = 0
  minWt : ∀ c ∈ C, c ≠ 0 → 8 ≤ wt c
  doublyEven : ∀ c ∈ C, 4 ∣ wt c

variable {C : Submodule (ZMod 2) V}

theorem mem_supp {c : V} {i : Fin 24} : i ∈ supp c ↔ c i = 1 := by simp [supp]

theorem wt_eq_zero_iff {c : V} : wt c = 0 ↔ c = 0 := by
  constructor
  · intro h
    funext i
    by_contra hi
    have hx : ∀ x : ZMod 2, x ≠ 0 → x = 1 := by decide
    have : c i = 1 := hx _ hi
    have : i ∈ supp c := mem_supp.mpr this
    simp [wt, Finset.card_eq_zero] at h
    simp [h] at this
  · rintro rfl
    simp [wt, supp]

theorem wt_le : ∀ c : V, wt c ≤ 24 := by
  intro c
  simpa [wt] using (supp c).card_le_univ

/-- The codewords, as a finite set. -/
noncomputable def cwords (C : Submodule (ZMod 2) V) : Finset V :=
  letI := Classical.decPred (· ∈ C)
  univ.filter (· ∈ C)

theorem mem_cwords {c : V} : c ∈ cwords C ↔ c ∈ C := by
  letI := Classical.decPred (· ∈ C)
  simp [cwords]

/-- **Self-duality.**  A vector orthogonal to every codeword is a codeword. -/
theorem dual_le (h : IsGolay C) {a : V} (ha : ∀ c ∈ C, dotp a c = 0) : a ∈ C := by
  have hle : C ≤ bilf.orthogonal C := by
    intro c hc
    rw [LinearMap.BilinForm.mem_orthogonal_iff]
    intro d hd
    simpa [LinearMap.BilinForm.IsOrtho, dotp] using h.selfOrth d hd c hc
  have hrank := finrank_add_orthogonal C
  rw [h.dim] at hrank
  simp only [Fintype.card_fin] at hrank
  have hdim : Module.finrank (ZMod 2) C = Module.finrank (ZMod 2) (bilf.orthogonal C) := by
    rw [h.dim]; omega
  have := Submodule.eq_of_le_of_finrank_eq hle hdim
  rw [this, LinearMap.BilinForm.mem_orthogonal_iff]
  intro d hd
  simpa [LinearMap.BilinForm.IsOrtho, dotp, mul_comm] using ha d hd

/-- A submodule's elements, counted. -/
theorem card_filter_mem (W : Submodule (ZMod 2) V) :
    letI := Classical.decPred (· ∈ W)
    (univ.filter (· ∈ W)).card = 2 ^ Module.finrank (ZMod 2) W := by
  letI := Classical.decPred (· ∈ W)
  classical
  have h1 : (univ.filter (· ∈ W)).card = Fintype.card W := by
    rw [Fintype.card_subtype]
  rw [h1]
  have := Module.card_eq_pow_finrank (K := ZMod 2) (V := W)
  simpa using this

/-- The code has 4096 words. -/
theorem card_cwords (h : IsGolay C) : (cwords C).card = 4096 := by
  rw [cwords, card_filter_mem C, h.dim]
  norm_num


/-! ## 2. Restriction to few coordinates -/

/-- The vectors vanishing on `S`. -/
def zeroOn (S : Finset (Fin 24)) : Submodule (ZMod 2) V where
  carrier := {v | ∀ i ∈ S, v i = 0}
  add_mem' := by intro a b ha hb i hi; simp [ha i hi, hb i hi]
  zero_mem' := by intro i _; rfl
  smul_mem' := by intro t a ha i hi; simp [ha i hi]

/-- Restriction of a vector to the coordinates in `S`. -/
def restr (S : Finset (Fin 24)) : V →ₗ[ZMod 2] (↥S → ZMod 2) where
  toFun v := fun i => v i.1
  map_add' := by intros; rfl
  map_smul' := by intros; rfl

/-- Extension of a pattern on `S` by zero. -/
def extend (S : Finset (Fin 24)) (a : ↥S → ZMod 2) : V :=
  fun j => if hj : j ∈ S then a ⟨j, hj⟩ else 0

theorem supp_extend {S : Finset (Fin 24)} (a : ↥S → ZMod 2) : supp (extend S a) ⊆ S := by
  intro j hj
  rw [mem_supp] at hj
  by_contra hjS
  simp [extend, hjS] at hj

theorem restr_extend {S : Finset (Fin 24)} (a : ↥S → ZMod 2) : restr S (extend S a) = a := by
  funext i
  simp [restr, extend, i.2]

theorem dotp_extend {S : Finset (Fin 24)} (a : ↥S → ZMod 2) (c : V) :
    dotp (extend S a) c = ∑ i : ↥S, a i * c i.1 := by
  have h1 : ∀ i : ↥S, a i * c i.1 = extend S a i.1 * c i.1 := by
    intro i; simp [extend, i.2]
  rw [dotp]
  rw [Finset.sum_congr rfl (fun i (_ : i ∈ (univ : Finset ↥S)) => h1 i)]
  rw [Finset.sum_coe_sort S (fun j => extend S a j * c j)]
  refine (Finset.sum_subset (Finset.subset_univ S) ?_).symm
  intro j _ hj
  simp [extend, hj]

/-- **Restriction to at most seven coordinates is onto.**  If it were not, the
functional cutting the image out would be a nonzero codeword of weight at most
seven. -/
theorem restrict_surjective (h : IsGolay C) {S : Finset (Fin 24)} (hS : S.card ≤ 7) (y : V) :
    ∃ c ∈ C, ∀ i ∈ S, c i = y i := by
  have htop : C.map (restr S) = ⊤ := by
    refine eq_top_of_orthogonal_trivial ?_
    intro a ha
    have hmem : extend S a ∈ C := by
      refine dual_le h ?_
      intro c hc
      have h2 := ha (restr S c) ⟨c, hc, rfl⟩
      rw [dotp_extend]
      simpa [restr] using h2
    have hzero : extend S a = 0 := by
      by_contra hne
      have h8 := h.minWt _ hmem hne
      have h7 : wt (extend S a) ≤ 7 :=
        le_trans (Finset.card_le_card (supp_extend a)) hS
      omega
    funext i
    have := congrFun hzero i.1
    simpa [extend, i.2] using this
  have hy : restr S y ∈ C.map (restr S) := by rw [htop]; trivial
  obtain ⟨c, hc, hcy⟩ := hy
  exact ⟨c, hc, fun i hi => congrFun hcy ⟨i, hi⟩⟩

/-- The restriction map, from the code. -/
def rho (C : Submodule (ZMod 2) V) (S : Finset (Fin 24)) : C →ₗ[ZMod 2] (↥S → ZMod 2) :=
  (restr S).comp C.subtype

theorem rho_range (h : IsGolay C) {S : Finset (Fin 24)} (hS : S.card ≤ 7) :
    (rho C S).range = ⊤ := by
  rw [LinearMap.range_eq_top]
  intro p
  obtain ⟨c, hc, hcp⟩ := restrict_surjective h hS (extend S p)
  refine ⟨⟨c, hc⟩, ?_⟩
  funext i
  have := hcp i.1 i.2
  simpa [rho, restr, extend, i.2] using this

theorem finrank_ker_rho (h : IsGolay C) {S : Finset (Fin 24)} (hS : S.card ≤ 7) :
    Module.finrank (ZMod 2) (LinearMap.ker (rho C S)) = 12 - S.card := by
  have hsum := LinearMap.finrank_range_add_finrank_ker (rho C S)
  rw [rho_range h hS, h.dim] at hsum
  have : Module.finrank (ZMod 2) (⊤ : Submodule (ZMod 2) (↥S → ZMod 2)) = S.card := by
    rw [finrank_top]
    simp
  rw [this] at hsum
  omega

/-- The codewords vanishing on `S`, counted. -/
theorem card_zero_fiber (h : IsGolay C) {S : Finset (Fin 24)} (hS : S.card ≤ 7) :
    ((cwords C).filter fun c => ∀ i ∈ S, c i = 0).card = 2 ^ (12 - S.card) := by
  classical
  have hequiv : {v : V // v ∈ C ∧ ∀ i ∈ S, v i = 0} ≃ LinearMap.ker (rho C S) :=
    { toFun := fun v => ⟨⟨v.1, v.2.1⟩, by
        ext i
        simpa [rho, restr] using v.2.2 i.1 i.2⟩
      invFun := fun c => ⟨c.1.1, c.1.2, by
        intro i hi
        have hk := LinearMap.mem_ker.mp c.2
        exact congrFun hk ⟨i, hi⟩⟩
      left_inv := by intro v; rfl
      right_inv := by intro c; rfl }
  have hcard : ((cwords C).filter fun c => ∀ i ∈ S, c i = 0).card
      = Fintype.card {v : V // v ∈ C ∧ ∀ i ∈ S, v i = 0} := by
    rw [Fintype.card_subtype]
    congr 1
    ext c
    simp [cwords]
  rw [hcard, Fintype.card_congr hequiv]
  have := Module.card_eq_pow_finrank (K := ZMod 2) (V := LinearMap.ker (rho C S))
  rw [this, finrank_ker_rho h hS]
  simp

/-- **The count that does the work.**  Exactly `2^(12-k)` codewords agree with a
prescribed pattern on `k ≤ 7` given coordinates. -/
theorem fiber_card (h : IsGolay C) {S : Finset (Fin 24)} (hS : S.card ≤ 7) (y : V) :
    ((cwords C).filter fun c => ∀ i ∈ S, c i = y i).card = 2 ^ (12 - S.card) := by
  classical
  obtain ⟨c₀, hc₀, hc₀y⟩ := restrict_surjective h hS y
  rw [← card_zero_fiber h hS]
  refine Finset.card_bij' (fun c _ => c + c₀) (fun c _ => c + c₀) ?_ ?_ ?_ ?_
  · intro c hc
    simp only [Finset.mem_filter, mem_cwords] at hc ⊢
    refine ⟨C.add_mem hc.1 hc₀, ?_⟩
    intro i hi
    have h1 := hc.2 i hi
    have h2 := hc₀y i hi
    have hcc : (c + c₀) i = y i + y i := by simp [h1, h2]
    rw [hcc]
    exact CharTwo.add_self_eq_zero (y i)
  · intro c hc
    simp only [Finset.mem_filter, mem_cwords] at hc ⊢
    refine ⟨C.add_mem hc.1 hc₀, ?_⟩
    intro i hi
    have h1 := hc.2 i hi
    have h2 := hc₀y i hi
    simp [h1, h2]
  · intro c _
    funext i
    show c i + c₀ i + c₀ i = c i
    rw [add_assoc, CharTwo.add_self_eq_zero, add_zero]
  · intro c _
    funext i
    show c i + c₀ i + c₀ i = c i
    rw [add_assoc, CharTwo.add_self_eq_zero, add_zero]

/-! ## 3. The five possible weights -/

theorem sum_eq_wt (c : V) : ∑ i, c i = (wt c : ZMod 2) := by
  classical
  have h1 : ∑ i, c i = ∑ i ∈ supp c, c i := by
    refine (Finset.sum_subset (Finset.subset_univ _) ?_).symm
    intro j _ hj
    rw [mem_supp] at hj
    have hx : ∀ x : ZMod 2, x ≠ 1 → x = 0 := by decide
    exact hx _ hj
  rw [h1, Finset.sum_congr rfl (fun j hj => mem_supp.mp hj)]
  simp [wt]

/-- The all-ones vector is a codeword. -/
theorem allOnes_mem (h : IsGolay C) : (fun _ => 1 : V) ∈ C := by
  refine dual_le h ?_
  intro c hc
  have h4 := h.doublyEven c hc
  obtain ⟨k, hk⟩ := h4
  have : dotp (fun _ => 1 : V) c = (wt c : ZMod 2) := by
    simp [dotp, sum_eq_wt c]
  rw [this, hk]
  push_cast
  have h4 : (4 : ZMod 2) = 0 := by decide
  rw [h4, zero_mul]

theorem wt_complement (c : V) : wt (fun i => 1 + c i) = 24 - wt c := by
  classical
  have hs : supp (fun i => 1 + c i) = (supp c)ᶜ := by
    ext j
    simp only [mem_supp, Finset.mem_compl]
    constructor
    · intro hj hjc
      rw [hjc] at hj
      exact absurd hj (by decide)
    · intro hj
      have hx : ∀ x : ZMod 2, x ≠ 1 → x = 0 := by decide
      rw [hx _ hj]
      ring
  rw [wt, hs, Finset.card_compl]
  simp [wt]

/-- **The weight of a codeword is 0, 8, 12, 16 or 24.** -/
theorem wt_mem_weights (h : IsGolay C) {c : V} (hc : c ∈ C) :
    wt c = 0 ∨ wt c = 8 ∨ wt c = 12 ∨ wt c = 16 ∨ wt c = 24 := by
  classical
  obtain ⟨k, hk⟩ := h.doublyEven c hc
  have hle := wt_le c
  by_cases hzero : c = 0
  · left; rw [hzero]; simp [wt, supp]
  have h8 := h.minWt c hc hzero
  -- the complement of a weight-20 word would have weight 4
  have hcomp : wt c ≠ 20 := by
    intro h20
    have hmem : (fun i => 1 + c i : V) ∈ C := C.add_mem (allOnes_mem h) hc
    have hne : (fun i => 1 + c i : V) ≠ 0 := by
      intro hzz
      have := wt_complement c
      rw [hzz, h20] at this
      simp [wt, supp] at this
    have := h.minWt _ hmem hne
    rw [wt_complement c, h20] at this
    omega
  omega

end GolayInv
