import Mathlib

/-!
# GolayHex-Υ: the MOG as a tiling, formalised

`GolaySemantics.lean` proves what the 24-cell MOG object costs and when its
violations can be diagnosed.  This file proves what happens when the objects
are laid out in space.

The geometry is the one that survives contact with the arithmetic: a tile is a
cube, its six faces are the six columns of the MOG, and each face carries one
GF(4) digit.  A lawful tile's six digits form a word of the **hexacode**, the
`[6, 3, 4]` code over GF(4) that Curtis's MOG construction puts on the columns
(`glm_clean/glm_clean/hexacode.py` verifies, exhaustively, that this really is
the binary Golay code: 4096 words, weight enumerator `1, 759, 2576, 759, 1`,
self-dual, doubly even, and every word decomposing into a hexacode word and a
parity with no failures).

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
* `nrci_calibrated`, `nrci_ladder`, `nrci_cal_strictAnti` — the regime ladder
  `1, 1/2, 2/5, 1/3, 1/4`, which is independent of `Q` once the budget is
  calibrated to `8Q`.
* `sinks_balance` — the thirteen sinks carry the wobble exactly.  (That there
  are thirteen of them is a stipulation, not a theorem; see the discussion in
  `glm_clean/glm_clean/tiles.py`.)
* `no_algebraic_growth_of_e` — if `e` is transcendental then it is not the
  growth ratio of any integer substitution.  The transcendence is carried as an
  explicit hypothesis because Mathlib does not have it; the label `[open]`
  stays on it, as it should.
-/

namespace GolayHex

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

/-! ## The prices -/

open Real

/-- The read quantum `Y = 1/(π + 2/π)`. -/
noncomputable def Y : ℝ := 1 / (π + 2 / π)

/-- The activation quantum `Q = Y + 1/8`. -/
noncomputable def Q : ℝ := Y + 1 / 8

theorem Y_pos : 0 < Y := by
  have hpi := Real.pi_pos
  have h : 0 < π + 2 / π := by positivity
  unfold Y
  positivity

theorem Q_pos : 0 < Q := by
  have := Y_pos
  unfold Q
  linarith

/-- **The read operator is capped by AM–GM.**  `Y[Π] = 1/(Π + 2/Π) ≤ 1/(2√2)`
for every positive loop-check `Π`, with equality exactly at `Π = √2`. -/
theorem readCost_le_amgm {x : ℝ} (hx : 0 < x) :
    1 / (x + 2 / x) ≤ 1 / (2 * Real.sqrt 2) := by
  have hsq : Real.sqrt 2 ^ 2 = 2 := Real.sq_sqrt (by norm_num)
  have hsn : (0:ℝ) ≤ Real.sqrt 2 := Real.sqrt_nonneg 2
  have hge : 2 * Real.sqrt 2 ≤ x + 2 / x := by
    have hx' : x ≠ 0 := ne_of_gt hx
    have hrw : x + 2 / x = (x ^ 2 + 2) / x := by field_simp
    rw [hrw, le_div_iff₀ hx]
    nlinarith [sq_nonneg (x - Real.sqrt 2)]
  have hpos : 0 < 2 * Real.sqrt 2 := by
    have : (0:ℝ) < Real.sqrt 2 := Real.sqrt_pos.mpr (by norm_num)
    linarith
  exact one_div_le_one_div_of_le hpos hge

/-- `Y` is strictly below the cap: `π ≠ √2`. -/
theorem Y_lt_amgm : Y < 1 / (2 * Real.sqrt 2) := by
  have hpi1 : (3.14 : ℝ) < π := Real.pi_gt_d2
  have hpi2 : π < 3.15 := Real.pi_lt_d2
  have hx : (0:ℝ) < π := by linarith
  have h2 : (0.6 : ℝ) < 2 / π := by
    have hmul : (0.6 : ℝ) * π < 2 := by nlinarith
    exact (lt_div_iff₀ hx).mpr hmul
  have hden : (3.7 : ℝ) < π + 2 / π := by linarith
  have hY : Y < 1 / 3.7 := by
    unfold Y
    exact one_div_lt_one_div_of_lt (by norm_num) hden
  have hsq : Real.sqrt 2 ^ 2 = 2 := Real.sq_sqrt (by norm_num)
  have hsn : (0:ℝ) ≤ Real.sqrt 2 := Real.sqrt_nonneg 2
  have hs : Real.sqrt 2 < 1.4143 := by nlinarith
  have hpos : (0:ℝ) < 2 * Real.sqrt 2 := by
    have : (0:ℝ) < Real.sqrt 2 := Real.sqrt_pos.mpr (by norm_num)
    linarith
  have hcap : 1 / (2 * 1.4143 : ℝ) < 1 / (2 * Real.sqrt 2) :=
    one_div_lt_one_div_of_lt hpos (by linarith)
  have : (1:ℝ) / 3.7 < 1 / (2 * 1.4143) := by norm_num
  linarith

/-- The coherence index with a budget `b`. -/
noncomputable def nrciB (b t : ℝ) : ℝ := b / (b + t)

/-- **The calibrated ladder is free of `Q`.**  Once the budget is calibrated to
`B = 8Q`, the coherence index of a weight-`n` tile is `8/(8+n)` whatever `Q`
happens to be. -/
theorem nrci_calibrated (n : ℕ) : nrciB (8 * Q) (n * Q) = 8 / (8 + n) := by
  have hQ : Q ≠ 0 := ne_of_gt Q_pos
  have hpos : (0:ℝ) < 8 + n := by positivity
  unfold nrciB
  rw [show 8 * Q + n * Q = (8 + n) * Q by ring]
  rw [div_eq_div_iff (by positivity) (by positivity)]
  ring

/-- The four regimes: vacuum, octad, dodecad, hexadecad, universe. -/
theorem nrci_ladder :
    nrciB (8 * Q) (0 * Q) = 1 ∧ nrciB (8 * Q) (8 * Q) = 1 / 2 ∧
    nrciB (8 * Q) (12 * Q) = 2 / 5 ∧ nrciB (8 * Q) (16 * Q) = 1 / 3 ∧
    nrciB (8 * Q) (24 * Q) = 1 / 4 := by
  have hQ : 0 < Q := Q_pos
  refine ⟨?_, ?_, ?_, ?_, ?_⟩
  · unfold nrciB; rw [zero_mul, add_zero, div_self (by linarith)]
  all_goals
    · unfold nrciB
      rw [div_eq_div_iff (by linarith) (by norm_num)]
      ring

/-- Heavier tiles are less coherent, strictly. -/
theorem nrci_cal_strictAnti {m n : ℕ} (h : m < n) :
    (8 : ℝ) / (8 + n) < 8 / (8 + m) := by
  have hm : (0:ℝ) < 8 + m := by positivity
  have hn : (0:ℝ) < 8 + n := by positivity
  have : (m : ℝ) < n := by exact_mod_cast h
  exact div_lt_div_of_pos_left (by norm_num) hm (by linarith)

/-! ## The thirteen sinks -/

/-- The wobble: the amount by which the compound loop `π·φ·e` fails to close. -/
noncomputable def wobble : ℝ := Int.fract (π * goldenRatio * Real.exp 1)

/-- The charge carried by each of the thirteen sinks. -/
noncomputable def sinkL : ℝ := wobble / 13

/-- The conservation law of the tiling: thirteen sinks carry the wobble
exactly.  (That the number is thirteen is a stipulation; nothing in the code,
in `M₂₄`, or in the tiling forces it.) -/
theorem sinks_balance : 13 * sinkL = wobble := by
  unfold sinkL; ring

theorem wobble_mem : 0 ≤ wobble ∧ wobble < 1 :=
  ⟨Int.fract_nonneg _, Int.fract_lt_one _⟩

/-! ## What `e` would have to be -/

/-- **`e` cannot be an assembly growth ratio while it is transcendental.**  A
growth ratio of a finite integer substitution is a root of the characteristic
polynomial of an integer matrix, hence algebraic.  Mathlib does not (yet) carry
the transcendence of `e`, so it is an explicit hypothesis here: the label
`[open]` stays on it. -/
theorem no_algebraic_growth_of_e
    (he : Transcendental ℚ (Real.exp 1))
    (p : Polynomial ℚ) (hp : p ≠ 0) :
    Polynomial.aeval (Real.exp 1) p ≠ 0 := by
  intro h
  exact he ⟨p, hp, h⟩

end GolayHex

/-! ## Axiom audit -/

#print axioms GolayHex.hexacode_card
#print axioms GolayHex.hexacode_mds
#print axioms GolayHex.update_linear
#print axioms GolayHex.update_matrix_order_three
#print axioms GolayHex.determined_by_boundary
#print axioms GolayHex.readCost_le_amgm
#print axioms GolayHex.Y_lt_amgm
#print axioms GolayHex.nrci_calibrated
#print axioms GolayHex.nrci_ladder
#print axioms GolayHex.sinks_balance
