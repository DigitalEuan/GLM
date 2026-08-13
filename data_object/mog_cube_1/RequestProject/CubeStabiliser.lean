import Mathlib
import RequestProject.CubeSurfaceMOG

/-!
# Experiment 1: the stabiliser test

The 24 surface cells of a cube are the pairs *(corner, axis)*: eight corners,
three faces meeting at each.  Equivalently — and this is the identification
used in `CubeSurfaceMOG.lean` — a cell is a *face* (an axis together with a
sign, six of them) plus a *quadrant of that face* (the signs of the other two
axes, four of them).  So

    24 surface cells = 6 faces × 4 quadrants = the 4 × 6 MOG grid.

The cube's surface symmetry group is the signed permutation group `B₃`, of
order 48: an axis permutation `σ` together with three signs `ε`.  Twenty-four
of its elements are rotations (`det = +1`), twenty-four are improper.

**The test.**  For each of the 48 symmetries, does the induced permutation of
the 24 MOG cells send the Golay code to itself?

* `stabiliser_card` — **exactly 12 of the 48 do**, under the coordinate
  identification of `CubeSurfaceMOG.lean`.
* `preserves_iff_tetrahedral` — and they are exactly the elements with an even
  axis permutation and an even number of sign flips: the rotation group of an
  inscribed **tetrahedron**, `T ≅ A₄`, order 12.  Every quarter-turn of a face
  and every reflection costs syndrome.
* `quarterTurn_not_preserving` — a named witness: the quarter-turn about the
  `z`-axis is a rotation of the cube that is *not* free.

**But the identification is a choice.**  Section 3 shows that a different
placement of the Golay code on the same 24 cube cells does better: `oBasis`
spans a `[24, 12, 8]` code (`oCode_card`, `oCode_min_weight`,
`oCode_weight_enumerator`) which

* `oCode_rotations_free` — is preserved by **all 24 rotations** of the cube, so
  the whole rotation group is a free instruction set; and
* `oCode_improper_priced` — is preserved by **no** improper symmetry, so every
  reflection is still a priced move.

An exhaustive search over the *G*-invariant subspaces of `F₂²⁴`
(`glm_clean/exp7_cube_surface.py`, function `invariant_golay_codes`) reports
that 24 is the ceiling: there is no placement of a Golay code on the cube's
surface invariant under the full group of order 48, nor under the full
tetrahedral group `T_d`.  That search is a Python computation and is *not*
verified here; what is verified here is the positive half — the order-24
rotation group can be made free, and the canonical MOG placement gives 12.
-/

namespace CubeStab

open CubeMOG GolayHex

set_option maxRecDepth 100000
set_option maxHeartbeats 4000000

/-! ## 1. The cube's surface, cell by cell -/

/-- A surface cell: a face and one of its four quadrants. -/
abbrev Cell := Fin 6 × Fin 4

/-- A corner of the cube: a sign for each axis (`true` = negative). -/
abbrev Corner := Fin 3 → Bool

/-- The cell `(corner, axis)` as a face/quadrant pair: the face is the axis
together with the corner's sign along it, the quadrant is the pair of signs
along the other two axes. -/
def cellOfCorner (p : Corner) (a : Fin 3) : Cell :=
  (⟨2 * (a : Nat) + (if p a then 1 else 0), by have := a.isLt; split <;> omega⟩,
   ⟨2 * (if p (a + 1) then 1 else 0) + (if p (a + 2) then 1 else 0), by
      split <;> split <;> omega⟩)

/-- The inverse reading: a face/quadrant pair as a corner and an axis. -/
def cornerOfCell (x : Cell) : Corner × Fin 3 :=
  let a : Fin 3 := ⟨(x.1 : Nat) / 2, by have := x.1.isLt; omega⟩
  (fun k => if k = a then decide ((x.1 : Nat) % 2 = 1)
            else if k = a + 1 then decide ((x.2 : Nat) / 2 = 1)
            else decide ((x.2 : Nat) % 2 = 1), a)

theorem cornerOfCell_cellOfCorner : ∀ (p : Corner) (a : Fin 3),
    cornerOfCell (cellOfCorner p a) = (p, a) := by native_decide

theorem cellOfCorner_cornerOfCell : ∀ x : Cell,
    cellOfCorner (cornerOfCell x).1 (cornerOfCell x).2 = x := by native_decide

/-! ## 2. The 48 surface symmetries -/

/-- The six permutations of the three axes, as a table. -/
def axPerm : Fin 6 → Fin 3 → Fin 3 :=
  ![![0, 1, 2], ![0, 2, 1], ![1, 0, 2], ![2, 1, 0], ![1, 2, 0], ![2, 0, 1]]

/-- Their inverses. -/
def axPermInv : Fin 6 → Fin 3 → Fin 3 :=
  ![![0, 1, 2], ![0, 2, 1], ![1, 0, 2], ![2, 1, 0], ![2, 0, 1], ![1, 2, 0]]

theorem axPerm_inv : ∀ (s : Fin 6) (k : Fin 3),
    axPermInv s (axPerm s k) = k ∧ axPerm s (axPermInv s k) = k := by decide

/-- Which axis permutations are even. -/
def axEven : Fin 6 → Bool := ![true, false, false, false, true, true]

/-- A surface symmetry of the cube: an axis permutation and three sign flips. -/
abbrev CubeSym := Fin 6 × (Fin 3 → Bool)

/-- The parity of the sign flips (`true` = an odd number of them). -/
def epsPar (e : Fin 3 → Bool) : Bool := xor (e 0) (xor (e 1) (e 2))

/-- Rotations are the symmetries of determinant `+1`. -/
def IsRot (g : CubeSym) : Bool := axEven g.1 = !(epsPar g.2)

theorem rotation_count : (Finset.univ.filter fun g : CubeSym => IsRot g).card = 24 := by
  native_decide

theorem cubeSym_card : Fintype.card CubeSym = 48 := by simp

/-- The inverse symmetry. -/
def csinv (g : CubeSym) : CubeSym :=
  ((![0, 1, 2, 3, 5, 4] : Fin 6 → Fin 6) g.1, fun k => g.2 (axPerm g.1 k))

/-- The action on cells: the corner moves by the signed permutation, the axis
moves by the permutation. -/
def actCell (g : CubeSym) (x : Cell) : Cell :=
  let pa := cornerOfCell x
  cellOfCorner (fun k => xor (g.2 k) (pa.1 (axPermInv g.1 k))) (axPerm g.1 pa.2)

theorem actCell_csinv : ∀ (g : CubeSym) (x : Cell), actCell g (actCell (csinv g) x) = x := by
  native_decide

theorem csinv_actCell : ∀ (g : CubeSym) (x : Cell), actCell (csinv g) (actCell g x) = x := by
  native_decide

/-- The action on grids: `actGrid g G` carries the value of `G` at `x` to the
cell `actCell g x`. -/
def actGrid (g : CubeSym) (G : Grid) : Grid := fun j i =>
  G (actCell (csinv g) (j, i)).1 (actCell (csinv g) (j, i)).2

theorem actGrid_spec (g : CubeSym) (G : Grid) (x : Cell) :
    actGrid g G (actCell g x).1 (actCell g x).2 = G x.1 x.2 := by
  have h : actCell (csinv g) (actCell g x) = x := csinv_actCell g x
  simp only [actGrid]
  rw [show ((actCell g x).1, (actCell g x).2) = actCell g x from rfl, h]

/-! ## 3. The stabiliser test on the canonical identification -/

/-- `g` is a **free** operation: it maps the Golay code onto itself. -/
def PreservesMog (g : CubeSym) : Prop := ∀ G : Grid, IsMog G → IsMog (actGrid g G)

/-- The decidable form.  Since the action is `F₂`-linear and the code is spanned
by twelve generators, it is enough to test the twelve. -/
def PreservesMogB (g : CubeSym) : Bool :=
  decide (∀ k : Fin 12, IsMogB (actGrid g (mogBasis k)) = true)

theorem actGrid_selL (g : CubeSym) (B : Fin 12 → Grid) (m : Fin 12 → Bool) :
    ∀ l : List (Fin 12), actGrid g (selL B m l) = selL (fun k => actGrid g (B k)) m l
  | [] => rfl
  | k :: l => by
      have ih := actGrid_selL g B m l
      funext j i
      have hih := congrFun (congrFun ih j) i
      simp only [actGrid, selL] at hih ⊢
      rw [hih]

theorem actGrid_selG (g : CubeSym) (B : Fin 12 → Grid) (m : Fin 12 → Bool) :
    actGrid g (selG B m) = selG (fun k => actGrid g (B k)) m := actGrid_selL g B m _

theorem preserves_iff (g : CubeSym) : PreservesMog g ↔ PreservesMogB g = true := by
  constructor
  · intro h
    simp only [PreservesMogB, decide_eq_true_eq]
    exact fun k => (isMogB_iff _).mpr (h _ (mogBasis_isMog k))
  · intro h G hG
    simp only [PreservesMogB, decide_eq_true_eq] at h
    obtain ⟨m, rfl⟩ := mog_spanned hG
    rw [actGrid_selG]
    exact selG_isMog _ (fun k => (isMogB_iff _).mp (h k)) m

/-- **Experiment 1.**  Exactly 12 of the cube's 48 surface symmetries are free
under the canonical MOG identification. -/
theorem stabiliser_card :
    (Finset.univ.filter fun g : CubeSym => PreservesMogB g).card = 12 := by native_decide

/-- The 12 free symmetries are exactly those with an even axis permutation and
an even number of sign flips: the rotation group of an inscribed tetrahedron,
`T ≅ A₄`. -/
theorem preserves_iff_tetrahedral :
    ∀ g : CubeSym, PreservesMogB g = true ↔ (axEven g.1 = true ∧ epsPar g.2 = false) := by
  native_decide

/-- Every free symmetry is a rotation. -/
theorem preserving_is_rotation (g : CubeSym) (h : PreservesMogB g = true) : IsRot g = true := by
  obtain ⟨h1, h2⟩ := (preserves_iff_tetrahedral g).mp h
  simp [IsRot, h1, h2]

/-- The quarter-turn about the `z`-axis: a genuine rotation of the cube that is
**not** free — it costs syndrome. -/
def quarterTurn : CubeSym := (2, ![false, true, false])

theorem quarterTurn_isRot : IsRot quarterTurn = true := by decide

theorem quarterTurn_not_preserving : PreservesMogB quarterTurn = false := by native_decide

/-! ## 4. A placement in which every rotation is free -/

/-- Twelve grids spanning a Golay code on the cube's surface which is invariant
under the whole rotation group of the cube.  Found by an exhaustive search over
the invariant subspaces of `F₂²⁴` (`glm_clean/exp7_cube_surface.py`); every
property it is used for is re-verified below. -/
def oBasis : Fin 12 → Grid :=
  ![![![false, true, false, false], ![true, true, true, false], ![true, true, false, false],
     ![false, false, false, false], ![true, false, false, false], ![false, false, false, true]],
   ![![false, true, true, true], ![false, true, false, false], ![false, true, true, false],
     ![false, false, false, false], ![true, false, false, false], ![false, false, true, false]],
   ![![true, true, true, false], ![true, false, false, false], ![true, false, true, false],
     ![false, false, false, false], ![true, false, false, false], ![false, true, false, false]],
   ![![false, false, true, false], ![false, false, true, false], ![true, true, true, true],
     ![false, false, false, false], ![true, false, false, false], ![true, false, false, false]],
   ![![true, true, false, false], ![false, true, true, false], ![false, false, true, true],
     ![false, false, false, false], ![true, false, false, true], ![false, false, false, false]],
   ![![true, false, false, true], ![true, false, true, false], ![true, false, false, true],
     ![false, false, false, false], ![true, false, true, false], ![false, false, false, false]],
   ![![true, false, true, false], ![true, true, false, false], ![false, true, false, true],
     ![false, false, false, false], ![true, true, false, false], ![false, false, false, false]],
   ![![true, true, false, true], ![false, false, true, false], ![true, true, true, false],
     ![false, false, false, true], ![false, false, false, false], ![false, false, false, false]],
   ![![false, true, true, true], ![true, false, false, false], ![true, true, false, true],
     ![false, false, true, false], ![false, false, false, false], ![false, false, false, false]],
   ![![true, false, true, true], ![false, true, false, false], ![true, false, true, true],
     ![false, true, false, false], ![false, false, false, false], ![false, false, false, false]],
   ![![false, false, false, true], ![true, true, true, false], ![false, true, true, true],
     ![true, false, false, false], ![false, false, false, false], ![false, false, false, false]],
   ![![true, true, true, true], ![true, true, true, true], ![false, false, false, false],
     ![false, false, false, false], ![false, false, false, false], ![false, false, false, false]]]

/-- The codeword with coefficients `m`. -/
def oSpan (m : Fin 12 → Bool) : Grid := selG oBasis m

/-- The information set of the code: twelve cells that carry the coefficients. -/
def oInfo : Fin 12 → Cell :=
  ![(5, 3), (5, 2), (5, 1), (5, 0), (4, 3), (4, 2), (4, 1), (3, 3), (3, 2), (3, 1), (3, 0), (1, 3)]

/-- Reading the coefficients back off a grid. -/
def oDecode (G : Grid) : Fin 12 → Bool := fun k => G (oInfo k).1 (oInfo k).2

theorem oDecode_oSpan : ∀ m : Fin 12 → Bool, oDecode (oSpan m) = m := by native_decide

/-- Membership in the code, decidably. -/
def IsOCode (G : Grid) : Bool := decide (oSpan (oDecode G) = G)

theorem isOCode_iff (G : Grid) : IsOCode G = true ↔ ∃ m, oSpan m = G := by
  constructor
  · intro h
    exact ⟨oDecode G, by simpa [IsOCode] using h⟩
  · rintro ⟨m, rfl⟩
    simp [IsOCode, oDecode_oSpan m]

theorem oSpan_injective : Function.Injective oSpan := by
  intro m m' h
  rw [← oDecode_oSpan m, ← oDecode_oSpan m', h]

/-- The code has `2¹²` words. -/
theorem oCode_card : (Finset.univ.image oSpan).card = 2 ^ 12 := by
  rw [Finset.card_image_of_injective _ oSpan_injective, Finset.card_univ]
  simp

/-- Its minimum weight is 8, so it is a `[24, 12, 8]` code — a Golay code
placed on the cube's surface. -/
theorem oCode_min_weight : ∀ m : Fin 12 → Bool, oSpan m ≠ 0 → 8 ≤ wtG (oSpan m) := by
  native_decide

/-- And it has the Golay weight enumerator. -/
theorem oCode_weight_enumerator :
    (Finset.univ.filter fun m : Fin 12 → Bool => wtG (oSpan m) = 8).card = 759 ∧
    (Finset.univ.filter fun m : Fin 12 → Bool => wtG (oSpan m) = 12).card = 2576 ∧
    (Finset.univ.filter fun m : Fin 12 → Bool => wtG (oSpan m) = 16).card = 759 ∧
    (Finset.univ.filter fun m : Fin 12 → Bool => wtG (oSpan m) = 24).card = 1 := by
  refine ⟨?_, ?_, ?_, ?_⟩ <;> native_decide

/-- The code contains the zero grid and is closed under XOR. -/
theorem oCode_zero : IsOCode 0 = true := by native_decide

theorem oCode_gxor {A B : Grid} (hA : IsOCode A = true) (hB : IsOCode B = true) :
    IsOCode (gxor A B) = true := by
  obtain ⟨m, rfl⟩ := (isOCode_iff A).mp hA
  obtain ⟨m', rfl⟩ := (isOCode_iff B).mp hB
  refine (isOCode_iff _).mpr ⟨fun k => xor (m k) (m' k), ?_⟩
  simpa [oSpan] using (selG_xor oBasis m m').symm

/-- **All 24 rotations of the cube are free** for this placement: each of the
twelve generators is carried into the code. -/
theorem oCode_rotations_free :
    ∀ g : CubeSym, IsRot g = true → ∀ k : Fin 12, IsOCode (actGrid g (oBasis k)) = true := by
  native_decide

/-- **No improper symmetry is free**, even for this placement: every reflection
carries some generator out of the code. -/
theorem oCode_improper_priced :
    ∀ g : CubeSym, IsRot g = false → ∃ k : Fin 12, IsOCode (actGrid g (oBasis k)) = false := by
  native_decide

/-- The rotation group maps the whole code onto itself. -/
theorem oCode_invariant (g : CubeSym) (hg : IsRot g = true) (G : Grid)
    (hG : IsOCode G = true) : IsOCode (actGrid g G) = true := by
  obtain ⟨m, rfl⟩ := (isOCode_iff G).mp hG
  rw [oSpan, actGrid_selG]
  refine selG_closed (P := fun X => IsOCode X = true) oCode_zero
    (fun _ _ h h' => oCode_gxor h h') _ (fun k => oCode_rotations_free g hg k) m

end CubeStab
