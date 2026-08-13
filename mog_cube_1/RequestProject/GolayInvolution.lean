import RequestProject.GolaySteiner
import RequestProject.CubeStabiliser

/-!
# No Golay code on the cube's surface survives a diagonal mirror

Third and last of the three files, and the one that closes the gap left by
report 1 and by `FINAL_REPORT.md` §6:

> The claim that **no** Golay code on the cube's surface is invariant under the
> full 48-element group `O_h` (nor under `T_d`) comes from the exhaustive Python
> search in `glm_clean/exp7_cube_surface.py`.

It is not a search.  One element of `T_d` already settles it, and the reason is
a parity count.

## The argument

A *diagonal mirror* of the cube — the reflection that swaps two axes, `sigmaD`
below — acts on the 24 surface cells as an involution with **exactly four fixed
cells** (`sigmaD_fixed_card`): the four quadrants of the two faces it fixes that
lie on the mirror plane.

Now suppose some Golay code `C` on those 24 cells were invariant under it.  By
`GolaySteiner.unique_octad` the octads of `C` form a Steiner system `S(5,8,24)`,
so every 5-set lies in exactly one octad; if the 5-set is carried to itself by
the mirror, so is its octad.  Count the mirror-invariant 5-sets, sorted by which
octad they lie in:

* there are `4 · C(10,2) + C(4,3) · 10 = 220` of them (`inv5_card`);
* an invariant octad meets the four fixed cells in an even number of points, so
  in `0`, `2` or `4` of them, and contains respectively `4`, `3` or `2` mirror
  pairs.  The invariant 5-subsets it contains therefore number `0`, `6` or `12`
  (`six_dvd_fiber`) — always a multiple of six.

So `6 ∣ 220`, which is false.  No such code exists — for **any** placement of
**any** Golay code on the surface, not merely the ones a search reached.

Since a diagonal mirror lies in `T_d` and in `O_h`, both negative rows of the
report's table are now theorems: `no_Td_invariant_golay`, `no_Oh_invariant_golay`.
The positive rows stay as they were (`CubeStab.oCode_rotations_free`).

## The one caveat

`IsGolay` asks for the four standard defining properties of the extended Golay
code — dimension 12, self-orthogonal, doubly even, minimum weight 8.  The Python
search asked only for dimension 12 and minimum weight 8, and appealed to
uniqueness for the rest.  The two agree on every code either could mean, but
the identification is a classification theorem that is not proved here.
-/

namespace GolayInv

open Finset

/-! ## 1. Invariant sets, from the block structure of an involution -/

variable {C : Submodule (ZMod 2) V}

/-- The support of `c ∘ σ` is the image of the support of `c`, for an
involution `σ`. -/
theorem supp_comp {σ : Fin 24 → Fin 24} (hσ : ∀ i, σ (σ i) = i) (c : V) :
    supp (fun i => c (σ i)) = (supp c).image σ := by
  classical
  ext i
  simp only [mem_supp, Finset.mem_image]
  constructor
  · intro hi
    exact ⟨σ i, by simpa [mem_supp] using hi, hσ i⟩
  · rintro ⟨j, hj, rfl⟩
    rw [hσ j]
    exact hj

/-- An involution is a bijection. -/
theorem involutive_injective {σ : Fin 24 → Fin 24} (hσ : ∀ i, σ (σ i) = i) :
    Function.Injective σ := fun a b h => by
  have : σ (σ a) = σ (σ b) := by rw [h]
  rwa [hσ, hσ] at this

/-- The image of an octad under a code automorphism is an octad. -/
theorem octads_image {σ : Fin 24 → Fin 24} (hσ : ∀ i, σ (σ i) = i)
    (hinv : ∀ c ∈ C, (fun i => c (σ i)) ∈ C) {B : Finset (Fin 24)} (hB : B ∈ octads C) :
    B.image σ ∈ octads C := by
  classical
  obtain ⟨c, hcC, hcw, rfl⟩ := mem_octads.mp hB
  refine mem_octads.mpr ⟨fun i => c (σ i), hinv c hcC, ?_, supp_comp hσ c⟩
  rw [show wt (fun i => c (σ i)) = (supp (fun i => c (σ i))).card from rfl, supp_comp hσ c,
    Finset.card_image_of_injective _ (involutive_injective hσ)]
  exact hcw

/-- **The octad of an invariant 5-set is invariant.** -/
theorem octad_invariant (h : IsGolay C) {σ : Fin 24 → Fin 24} (hσ : ∀ i, σ (σ i) = i)
    (hinv : ∀ c ∈ C, (fun i => c (σ i)) ∈ C) {S B : Finset (Fin 24)}
    (hS5 : S.card = 5) (hSinv : S.image σ = S) (hB : B ∈ octads C) (hSB : S ⊆ B) :
    B.image σ = B := by
  classical
  obtain ⟨B0, hB0, huniq⟩ := unique_octad h hS5
  clear hB0
  have h1 : B.image σ = B0 := by
    refine huniq _ ⟨octads_image hσ hinv hB, ?_⟩
    rw [← hSinv]
    exact Finset.image_subset_image hSB
  have h2 : B = B0 := huniq _ ⟨hB, hSB⟩
  rw [h1, h2]

/-! ## 2. The parity contradiction -/

/-- **The heart of the matter.**  If the invariant 5-sets number `220` while
every invariant 8-set contains a multiple of six of them, the code cannot be
invariant: the 5-sets are partitioned by their octads, so `6 ∣ 220`. -/
theorem no_invariant_of_counts (h : IsGolay C) {σ : Fin 24 → Fin 24}
    (hσ : ∀ i, σ (σ i) = i) (hinv : ∀ c ∈ C, (fun i => c (σ i)) ∈ C)
    (I : Finset (Finset (Fin 24)))
    (hI : ∀ S, S ∈ I ↔ (S.card = 5 ∧ S.image σ = S))
    (hIcard : I.card = 220)
    (h6 : ∀ B : Finset (Fin 24), B.card = 8 → B.image σ = B →
      6 ∣ (I.filter fun S => S ⊆ B).card) :
    False := by
  classical
  set t : Finset (Finset (Fin 24)) := (octads C).filter fun B => B.image σ = B with ht
  set f : Finset (Fin 24) → Finset (Fin 24) :=
    fun S => if hex : ∃ B, B ∈ octads C ∧ S ⊆ B then hex.choose else ∅ with hf
  have hspec : ∀ S ∈ I, f S ∈ octads C ∧ S ⊆ f S := by
    intro S hS
    have h5 := ((hI S).mp hS).1
    have hex : ∃ B, B ∈ octads C ∧ S ⊆ B := (unique_octad h h5).exists
    simp only [hf, dif_pos hex]
    exact hex.choose_spec
  have hmaps : ((I : Set (Finset (Fin 24)))).MapsTo f t := by
    intro S hS
    rw [Finset.mem_coe] at hS
    obtain ⟨hoc, hsub⟩ := hspec S hS
    obtain ⟨h5, hinvS⟩ := (hI S).mp hS
    refine Finset.mem_coe.mpr (Finset.mem_filter.mpr ⟨hoc, ?_⟩)
    exact octad_invariant h hσ hinv h5 hinvS hoc hsub
  have hfib : ∀ B ∈ t, (I.filter fun S => f S = B) = (I.filter fun S => S ⊆ B) := by
    intro B hB
    obtain ⟨hoc, hBinv⟩ := Finset.mem_filter.mp hB
    ext S
    simp only [Finset.mem_filter]
    constructor
    · rintro ⟨hS, rfl⟩
      exact ⟨hS, (hspec S hS).2⟩
    · rintro ⟨hS, hsub⟩
      refine ⟨hS, ?_⟩
      obtain ⟨h5, -⟩ := (hI S).mp hS
      obtain ⟨B0, -, huniq⟩ := unique_octad h h5
      rw [huniq _ ⟨(hspec S hS).1, (hspec S hS).2⟩, huniq _ ⟨hoc, hsub⟩]
  have hsum : I.card = ∑ B ∈ t, (I.filter fun S => S ⊆ B).card := by
    rw [Finset.card_eq_sum_card_fiberwise hmaps]
    exact Finset.sum_congr rfl fun B hB => by rw [hfib B hB]
  have hdvd : (6 : ℕ) ∣ I.card := by
    rw [hsum]
    refine Finset.dvd_sum fun B hB => ?_
    obtain ⟨hoc, hBinv⟩ := Finset.mem_filter.mp hB
    exact h6 B (card_of_mem_octads hoc) hBinv
  rw [hIcard] at hdvd
  norm_num at hdvd

/-! ## 3. The diagonal mirror of the cube -/

open CubeStab

/-- The standard labelling of the 24 surface cells by coordinates. -/
def lab : Cell ≃ Fin 24 := finProdFinEquiv

/-- A cube symmetry, read as a permutation of the 24 coordinates. -/
def cellPerm (g : CubeSym) (i : Fin 24) : Fin 24 := lab (actCell g (lab.symm i))

/-- The diagonal mirror: the reflection that swaps the `x` and `y` axes. -/
def sigmaD : CubeSym := (2, ![false, false, false])

/-- It is improper — a reflection, not a rotation. -/
theorem sigmaD_not_rotation : IsRot sigmaD = false := by decide

/-- It lies in `T_d`: an even number of sign flips. -/
theorem sigmaD_mem_Td : epsPar sigmaD.2 = false := by decide

/-- Its action on the cells is an involution. -/
theorem sigmaD_involutive : ∀ i, cellPerm sigmaD (cellPerm sigmaD i) = i := by
  decide

/-- **It fixes exactly four of the 24 cells.** -/
theorem sigmaD_fixed_card :
    (univ.filter fun i => cellPerm sigmaD i = i).card = 4 := by
  decide

/-- The block index of a cell: fixed cells get their own block, the two cells of
a mirror pair share one.  There are 14 blocks — 4 fixed cells and 10 pairs. -/
def blk (i : Fin 24) : Fin 24 := min i (cellPerm sigmaD i)

/-- The block representatives: 14 of them, one per fixed cell and one per
mirror pair. -/
def reps : List (Fin 24) := ((List.finRange 24).map blk).dedup

/-- Every invariant set, listed once: a set is carried to itself by the mirror
exactly when it is a union of blocks, and the blocks are indexed by the subsets
of `reps`. -/
def invList : List (Finset (Fin 24)) :=
  reps.sublists.map fun t => univ.filter fun i => blk i ∈ t

/-- The block index is either the cell or its mirror image. -/
private theorem blk_choice : ∀ i, blk i = i ∨ blk i = cellPerm sigmaD i := by decide

/-- Mirror images share a block. -/
private theorem blk_comp : ∀ i, blk (cellPerm sigmaD i) = blk i := by decide

/-- Every block index occurs among the representatives. -/
private theorem blk_mem_reps : ∀ i, blk i ∈ reps := by decide

/-- A mirror-invariant set contains a cell exactly when it contains its
image. -/
private theorem mem_iff_of_inv {B : Finset (Fin 24)} (hB : B.image (cellPerm sigmaD) = B)
    (i : Fin 24) : cellPerm sigmaD i ∈ B ↔ i ∈ B := by
  constructor
  · intro hi
    have h2 : cellPerm sigmaD (cellPerm sigmaD i) ∈ B.image (cellPerm sigmaD) :=
      Finset.mem_image_of_mem _ hi
    rw [hB, sigmaD_involutive] at h2
    exact h2
  · intro hi
    have h2 : cellPerm sigmaD i ∈ B.image (cellPerm sigmaD) := Finset.mem_image_of_mem _ hi
    rwa [hB] at h2

/-- A mirror-invariant set contains a cell exactly when it contains its block
representative. -/
private theorem blk_mem_iff {B : Finset (Fin 24)} (hB : B.image (cellPerm sigmaD) = B)
    (i : Fin 24) : blk i ∈ B ↔ i ∈ B := by
  rcases blk_choice i with hi | hi <;> rw [hi]
  exact mem_iff_of_inv hB i

theorem mem_invList {B : Finset (Fin 24)} :
    B ∈ invList ↔ B.image (cellPerm sigmaD) = B := by
  classical
  constructor
  · intro hB
    simp only [invList, List.mem_map] at hB
    obtain ⟨t, -, rfl⟩ := hB
    ext i
    simp only [Finset.mem_image, Finset.mem_filter, Finset.mem_univ, true_and]
    constructor
    · rintro ⟨j, hj, rfl⟩
      rw [blk_comp]
      exact hj
    · intro hi
      exact ⟨cellPerm sigmaD i, by rw [blk_comp]; exact hi, sigmaD_involutive i⟩
  · intro hB
    refine List.mem_map.mpr ⟨reps.filter fun r => decide (r ∈ B), ?_, ?_⟩
    · exact List.mem_sublists.mpr List.filter_sublist
    · ext i
      simp only [Finset.mem_filter, Finset.mem_univ, true_and, List.mem_filter,
        decide_eq_true_eq]
      constructor
      · rintro ⟨-, hmem⟩
        exact (blk_mem_iff hB i).mp hmem
      · intro hi
        exact ⟨blk_mem_reps i, (blk_mem_iff hB i).mpr hi⟩

/-- The invariant 5-sets. -/
def inv5 : Finset (Finset (Fin 24)) := (invList.filter fun S => S.card = 5).toFinset

/-- The invariant 8-sets. -/
def inv8 : List (Finset (Fin 24)) := invList.filter fun B => B.card = 8

theorem mem_inv5 {S : Finset (Fin 24)} :
    S ∈ inv5 ↔ (S.card = 5 ∧ S.image (cellPerm sigmaD) = S) := by
  simp only [inv5, List.mem_toFinset, List.mem_filter, decide_eq_true_eq, mem_invList]
  tauto

/-- **There are 220 invariant 5-sets** — one fixed cell and two pairs, or three
fixed cells and one pair. -/
theorem inv5_card : inv5.card = 220 := by
  native_decide

/-- The fibre count, over the listed invariant 8-sets. -/
theorem six_dvd_fiber_all :
    inv8.all (fun B => decide (6 ∣ (inv5.filter fun S => S ⊆ B).card)) = true := by
  native_decide

theorem six_dvd_fiber_list (B : Finset (Fin 24)) (hB : B ∈ inv8) :
    6 ∣ (inv5.filter fun S => S ⊆ B).card := by
  have := List.all_eq_true.mp six_dvd_fiber_all B hB
  simpa using this

/-- **Every invariant 8-set contains a multiple of six invariant 5-sets** — `0`,
`6` or `12` of them, according as it contains `0`, `2` or `4` fixed cells. -/
theorem six_dvd_fiber (B : Finset (Fin 24)) (hB8 : B.card = 8)
    (hBinv : B.image (cellPerm sigmaD) = B) :
    6 ∣ (inv5.filter fun S => S ⊆ B).card := by
  refine six_dvd_fiber_list B ?_
  simp only [inv8, List.mem_filter, decide_eq_true_eq]
  exact ⟨mem_invList.mpr hBinv, hB8⟩

/-! ## 4. The verdict -/

/-- **No Golay code on the cube's surface is invariant under a diagonal
mirror.** -/
theorem no_diagonal_mirror_invariant_golay (hC : IsGolay C)
    (hinv : ∀ c ∈ C, (fun i => c (cellPerm sigmaD i)) ∈ C) : False := by
  exact no_invariant_of_counts hC sigmaD_involutive hinv inv5
    (fun _ => mem_inv5) inv5_card six_dvd_fiber

/-- **No Golay code on the cube's surface is invariant under `T_d`** — the
tetrahedral group with its mirrors, of order 24.  This was the second negative
row of the report's table. -/
theorem no_Td_invariant_golay (hC : IsGolay C)
    (hinv : ∀ g : CubeSym, epsPar g.2 = false → ∀ c ∈ C, (fun i => c (cellPerm g i)) ∈ C) :
    False :=
  no_diagonal_mirror_invariant_golay hC (hinv sigmaD sigmaD_mem_Td)

/-- **No Golay code on the cube's surface is invariant under the full cube group
`O_h`** of order 48.  This was the first negative row. -/
theorem no_Oh_invariant_golay (hC : IsGolay C)
    (hinv : ∀ g : CubeSym, ∀ c ∈ C, (fun i => c (cellPerm g i)) ∈ C) :
    False :=
  no_diagonal_mirror_invariant_golay hC (hinv sigmaD)

end GolayInv
