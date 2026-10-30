import Mathlib

/-!
# The MOG as a tiling: the hexacode layer

Retrieved from the `mog_cube_1` sub-study of the legacy archive.  Where
`GLM/Golay/Code.lean` works with the Golay code as a set of 24-bit words, this
file lays the same object out in space and asks what the geometry forces.

The geometry is the one that survives contact with the arithmetic: a tile is a
cube, its six faces are the six columns of the MOG, and each face carries one
GF(4) digit.  A lawful tile's six digits form a word of the **hexacode**, the
`[6, 3, 4]` code over GF(4) that Curtis's MOG construction puts on the columns.
`GLM/Cube/Surface.lean` then completes the identification and recovers the
binary Golay code — 4096 words, weight enumerator `1, 759, 2576, 759, 1`,
minimum weight 8 — on the cube's 24 surface cells.

Two cubes glued along an axis must show each other the same digit.  The
theorems below say what that forces.

* `hexacode_card` — there are 64 lawful face-configurations.
* `hexacode_mds` — the three *incoming* faces determine the tile uniquely.
  This is the MDS property of the hexacode, and it is the engine of everything
  else.
* `update_linear`, `update_matrix_order_three` — the resulting update rule is
  GF(4)-linear with matrix `[[ω,ω̄,ω̄],[ω̄,ω,ω̄],[ω̄,ω̄,ω]]`, whose cube is the
  identity: the substrate propagates with period three.
* `determined_by_boundary` — a legal assembly of the octant is *determined* by
  the digits entering through its three boundary planes.  The interior is
  computed, not chosen; the entropy of the hexacode layer is a surface entropy.

The archive file continued with a price section (the read quantum, the
calibrated coherence ladder, the thirteen sinks) and a growth-ratio remark
about `e`.  Those are not retrieved here: the development already carries them,
in `GLM/StepCost.lean` (`nrci_gauge_independent`, `nrci_ladder`) and
`GLM/SeedLayers.lean` respectively.
-/

namespace GLM.GolayHex

/-! ## GF(4) -/

/-- The field with four elements, as `0, 1, ω, ω̄ = 0, 1, 2, 3`. -/
abbrev F4 := Fin 4

/-- `ω`. -/
def w : F4 := 2
/-- `ω̄ = ω²`. -/
def w2 : F4 := 3

/-- Addition of GF(4), which is bitwise. -/
def add4 (a b : F4) : F4 :=
  (![![0, 1, 2, 3], ![1, 0, 3, 2], ![2, 3, 0, 1], ![3, 2, 1, 0]] : F4 → F4 → F4) a b

/-- Multiplication of GF(4). -/
def mul4 (a b : F4) : F4 :=
  (![![0, 0, 0, 0], ![0, 1, 2, 3], ![0, 2, 3, 1], ![0, 3, 1, 2]] : F4 → F4 → F4) a b

scoped infixl:65 " +₄ " => add4
scoped infixl:70 " *₄ " => mul4

theorem add4_comm (a b : F4) : a +₄ b = b +₄ a := by revert a b; decide
theorem mul4_comm (a b : F4) : a *₄ b = b *₄ a := by revert a b; decide
theorem add4_self (a : F4) : a +₄ a = 0 := by revert a; decide

/-! ## The hexacode -/

/-- The generator rows of the hexacode `[6, 3, 4]` over GF(4). -/
def hexGen : Fin 3 → Fin 6 → F4 :=
  ![![1, 0, 0, 1, 2, 3],
    ![0, 1, 0, 1, 3, 2],
    ![0, 0, 1, 1, 1, 1]]

/-- The word `a·g₀ + b·g₁ + c·g₂`. -/
def combo (a b c : F4) : Fin 6 → F4 := fun j =>
  (a *₄ hexGen 0 j) +₄ ((b *₄ hexGen 1 j) +₄ (c *₄ hexGen 2 j))

/-- A face-configuration is lawful when it is a hexacode word. -/
def IsHex (h : Fin 6 → F4) : Prop := ∃ a b c, combo a b c = h

instance : DecidablePred IsHex := fun _ => inferInstanceAs (Decidable (∃ _ _ _, _))

/-- The hexacode has 64 words. -/
theorem hexacode_card :
    (Finset.univ.filter fun h : Fin 6 → F4 => IsHex h).card = 64 := by
  native_decide

/-- Faces `1, 3, 5` are the `-x, -y, -z` faces: what the neighbours hand in. -/
def incoming (h : Fin 6 → F4) : F4 × F4 × F4 := (h 1, h 3, h 5)

/-- Faces `0, 2, 4` are the `+x, +y, +z` faces: what the tile hands on. -/
def outgoing (h : Fin 6 → F4) : F4 × F4 × F4 := (h 0, h 2, h 4)

/-- **The tile is determined by what enters it.**  Every triple of coordinates
of the hexacode is an information set (the code is MDS, `d = n - k + 1`), and
in particular the three incoming faces are: for each triple of incoming digits
there is exactly one lawful tile. -/
theorem hexacode_mds_card : ∀ a b c : F4,
    (Finset.univ.filter fun h : Fin 6 → F4 => IsHex h ∧ incoming h = (a, b, c)).card = 1 := by
  native_decide

/-- The same fact as a uniqueness statement. -/
theorem hexacode_mds (a b c : F4) :
    ∃! h : Fin 6 → F4, IsHex h ∧ incoming h = (a, b, c) := by
  obtain ⟨h, hh⟩ := Finset.card_eq_one.mp (hexacode_mds_card a b c)
  refine ⟨h, ?_, ?_⟩
  · have : h ∈ ({h} : Finset (Fin 6 → F4)) := Finset.mem_singleton_self h
    rw [← hh] at this
    simpa using (Finset.mem_filter.mp this).2
  · intro y hy
    have : y ∈ Finset.univ.filter fun g : Fin 6 → F4 => IsHex g ∧ incoming g = (a, b, c) :=
      Finset.mem_filter.mpr ⟨Finset.mem_univ _, hy⟩
    rw [hh] at this
    simpa using this

/-- The update rule: the outgoing digits are a fixed GF(4)-linear function of
the incoming ones, with matrix `[[ω,ω̄,ω̄],[ω̄,ω,ω̄],[ω̄,ω̄,ω]]`. -/
def step (t : F4 × F4 × F4) : F4 × F4 × F4 :=
  ((w *₄ t.1) +₄ ((w2 *₄ t.2.1) +₄ (w2 *₄ t.2.2)),
   (w2 *₄ t.1) +₄ ((w *₄ t.2.1) +₄ (w2 *₄ t.2.2)),
   (w2 *₄ t.1) +₄ ((w2 *₄ t.2.1) +₄ (w *₄ t.2.2)))

set_option maxHeartbeats 2000000 in
theorem update_linear : ∀ h : Fin 6 → F4, IsHex h → outgoing h = step (incoming h) := by
  native_decide

/-- The propagator has order three: three diagonal steps return every
configuration to itself. -/
theorem update_matrix_order_three : ∀ t, step (step (step t)) = t := by native_decide

/-! ## Assemblies -/

/-- A legal assembly of the positive octant: every cube lawful, and glued
cubes showing each other the same digit on the shared face. -/
structure Legal (F : ℕ → ℕ → ℕ → Fin 6 → F4) : Prop where
  lawful : ∀ x y z, IsHex (F x y z)
  matchx : ∀ x y z, F x y z 0 = F (x + 1) y z 1
  matchy : ∀ x y z, F x y z 2 = F x (y + 1) z 3
  matchz : ∀ x y z, F x y z 4 = F x y (z + 1) 5

/-- **The interior is computed, not chosen.**  Two legal assemblies of the
octant that agree on the digits entering through the three boundary planes
`x = 0`, `y = 0`, `z = 0` are equal everywhere.  So the hexacode layer of the
tiling carries surface entropy only. -/
theorem determined_by_boundary
    (F G : ℕ → ℕ → ℕ → Fin 6 → F4) (hF : Legal F) (hG : Legal G)
    (bx : ∀ y z, F 0 y z 1 = G 0 y z 1)
    (by' : ∀ x z, F x 0 z 3 = G x 0 z 3)
    (bz : ∀ x y, F x y 0 5 = G x y 0 5) :
    F = G := by
  have key : ∀ n x y z, x + y + z = n → F x y z = G x y z := by
    intro n
    induction n using Nat.strong_induction_on with
    | _ n ih =>
      intro x y z hxyz
      have hin : incoming (F x y z) = incoming (G x y z) := by
        have h1 : F x y z 1 = G x y z 1 := by
          match x with
          | 0 => exact bx y z
          | x + 1 =>
            have hlt : x + y + z < n := by omega
            have := ih (x + y + z) hlt x y z rfl
            rw [← hF.matchx x y z, ← hG.matchx x y z, this]
        have h3 : F x y z 3 = G x y z 3 := by
          match y with
          | 0 => exact by' x z
          | y + 1 =>
            have hlt : x + y + z < n := by omega
            have := ih (x + y + z) hlt x y z rfl
            rw [← hF.matchy x y z, ← hG.matchy x y z, this]
        have h5 : F x y z 5 = G x y z 5 := by
          match z with
          | 0 => exact bz x y
          | z + 1 =>
            have hlt : x + y + z < n := by omega
            have := ih (x + y + z) hlt x y z rfl
            rw [← hF.matchz x y z, ← hG.matchz x y z, this]
        simp [incoming, h1, h3, h5]
      obtain ⟨_, _, huniq⟩ := hexacode_mds (F x y z 1) (F x y z 3) (F x y z 5)
      have e1 : F x y z = _ := huniq _ ⟨hF.lawful x y z, rfl⟩
      have e2 : G x y z = _ := huniq _ ⟨hG.lawful x y z, by
        simpa [incoming] using hin.symm⟩
      rw [e1, e2]
  funext x y z
  exact key (x + y + z) x y z rfl

end GLM.GolayHex
