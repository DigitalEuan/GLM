import Mathlib
import RequestProject.GLM.Cube.Surface
import RequestProject.GLM.Constants

/-!
# The price list of the cube's instruction set

The brief proposes a partition of the cube's operations:

* **free / reversible** — XOR with a codeword, and the code-preserving
  symmetries (`CubeStabiliser`);
* **priced** — nonlinear face transforms (AND, OR), which produce a nonzero
  syndrome and cost `HW(leader σ)·Q ≤ 4Q`;
* **certified repair** — the snap back into the code, unique when the damage is
  at most 3 cells;
* **ambiguous** — results at distance 4, where the cube must genuinely read.

This file proves the arithmetic that makes that price list true, in particular
the bound `≤ 4Q` and its sharpness.

## What is proved

* `synd` — the 12-bit syndrome of a grid: three GF(4) hexacode checks (faces
  3, 4, 5 against the re-encoding of faces 0, 1, 2) and six parity checks.
  `synd_eq_zero_iff` : `synd g = 0 ↔ IsMog g`; `synd_gxor` : it is linear.
* `leader` — a coset leader for each of the 4096 syndromes, produced by
  searching all `12951` grids of weight `≤ 4` (`leader_ok`, by evaluation).
* `covering_radius_le_four` : **every** grid is within 4 cells of a codeword,
  hence `tax_le_four_Q` : the repair of any damage costs at most `4·Q`.
* `covering_radius_ge_four` : the bound is attained — a weight-4 grid is at
  distance exactly 4 from the code (its own coset has no smaller member), so
  `4Q` is not a pessimistic estimate but the true worst case.
* `repair_unique_of_le_three` : below the boundary the repair is unique, and
  `repair_ambiguous_at_four` : at 4 it is not.
* `and_is_priced` : AND of two codewords need not be a codeword — the concrete
  reason the nonlinear class is priced at all — and `and_repair_le_four`
  bounds its repair.
-/

namespace GLM.CubeTax

open CubeMOG GolayHex

set_option maxRecDepth 4000

/-! ## 1. The syndrome -/

/-- The three faces that the hexacode check re-encodes. -/
def lift3 : Fin 3 → Fin 6 := ![3, 4, 5]

/-- The syndrome of a grid: three GF(4) hexacode residuals and six parity
residuals.  `4³ · 2⁶ = 4096` values, one per coset of the code. -/
abbrev Syn := (Fin 3 → F4) × (Fin 6 → Bool)

/-- The zero syndrome. -/
def synZero : Syn := (fun _ => 0, fun _ => false)

/-- The syndrome map. -/
def synd (g : Grid) : Syn :=
  (fun k => symbols g (lift3 k) +₄ combo (symbols g 0) (symbols g 1) (symbols g 2) (lift3 k),
   fun j => xor (par (g j)) (topPar g))

theorem combo_info : ∀ a b c : F4,
    combo a b c 0 = a ∧ combo a b c 1 = b ∧ combo a b c 2 = c := by decide

theorem add4_eq_zero : ∀ a b : F4, (a +₄ b = 0) ↔ a = b := by decide

theorem add4_self (a : F4) : a +₄ a = 0 := by revert a; decide

theorem add4_shuffle : ∀ a b c d : F4, (a +₄ b) +₄ (c +₄ d) = (a +₄ c) +₄ (b +₄ d) := by decide

/-- **The syndrome detects exactly the code.** -/
theorem synd_eq_zero_iff (g : Grid) : synd g = synZero ↔ IsMog g := by
  constructor
  · intro h
    have h1 : ∀ k : Fin 3, symbols g (lift3 k)
        = combo (symbols g 0) (symbols g 1) (symbols g 2) (lift3 k) := by
      intro k
      have := congrFun (congrArg Prod.fst h) k
      exact (add4_eq_zero _ _).mp this
    have h2 : ∀ j, par (g j) = topPar g := by
      intro j
      have hj := congrFun (congrArg Prod.snd h) j
      simp only [synd, synZero] at hj
      revert hj
      cases par (g j) <;> cases topPar g <;> simp
    refine ⟨(isHex_iff_info _).mpr ?_, h2⟩
    funext j
    obtain ⟨c0, c1, c2⟩ := combo_info (symbols g 0) (symbols g 1) (symbols g 2)
    fin_cases j
    · exact c0
    · exact c1
    · exact c2
    · exact (h1 0).symm
    · exact (h1 1).symm
    · exact (h1 2).symm
  · rintro ⟨hhex, hpar⟩
    have hcombo := (isHex_iff_info _).mp hhex
    refine Prod.ext ?_ ?_
    · funext k
      have : combo (symbols g 0) (symbols g 1) (symbols g 2) (lift3 k) = symbols g (lift3 k) :=
        congrFun hcombo _
      simp only [synd, this, synZero]
      exact add4_self _
    · funext j
      simp only [synd, synZero, hpar j, Bool.xor_self]

/-- **The syndrome is linear.** -/
theorem synd_gxor (g h : Grid) :
    synd (gxor g h)
      = (fun k => (synd g).1 k +₄ (synd h).1 k, fun j => xor ((synd g).2 j) ((synd h).2 j)) := by
  refine Prod.ext ?_ ?_
  · funext k
    have hs : ∀ j : Fin 6, symbols (gxor g h) j = symbols g j +₄ symbols h j := fun j =>
      symb_xor (g j) (h j)
    simp only [synd, hs]
    rw [← congrFun (combo_add (symbols g 0) (symbols g 1) (symbols g 2)
      (symbols h 0) (symbols h 1) (symbols h 2)) (lift3 k)]
    exact add4_shuffle _ _ _ _
  · funext j
    have hp : par (gxor g h j) = xor (par (g j)) (par (h j)) := par_xor (g j) (h j)
    simp only [synd, hp, topPar_gxor]
    cases par (g j) <;> cases par (h j) <;> cases topPar g <;> cases topPar h <;> rfl

/-- Two grids with the same syndrome differ by a codeword. -/
theorem isMog_of_synd_eq {g e : Grid} (h : synd e = synd g) : IsMog (gxor g e) := by
  rw [← synd_eq_zero_iff, synd_gxor, h]
  refine Prod.ext ?_ ?_
  · funext k; exact add4_self _
  · funext j; simp [synZero]

/-! ## 2. Coset leaders of weight at most 4 -/

/-- The 24 cells of the cube surface. -/
def cellList : List (Fin 6 × Fin 4) :=
  (List.finRange 6).flatMap fun j => (List.finRange 4).map fun i => (j, i)

/-- The grid whose set cells are the listed ones. -/
def gridOf (l : List (Fin 6 × Fin 4)) : Grid := fun j i => l.contains (j, i)

/-- All grids of weight at most 4: `1 + 24 + 276 + 2024 + 10626 = 12951` of them. -/
def smallErrors : List Grid :=
  ((List.range 5).flatMap fun k => cellList.sublistsLen k).map gridOf

/-- An index for a syndrome, `0 ≤ · < 4096`. -/
def synIdx (s : Syn) : Nat :=
  (s.1 0).val + 4 * (s.1 1).val + 16 * (s.1 2).val +
    64 * ((if s.2 0 then 1 else 0) + 2 * (if s.2 1 then 1 else 0) +
      4 * (if s.2 2 then 1 else 0) + 8 * (if s.2 3 then 1 else 0) +
      16 * (if s.2 4 then 1 else 0) + 32 * (if s.2 5 then 1 else 0))

/-- The table of coset leaders, filled by scanning the grids of weight `≤ 4`. -/
def leaderTable : Array Grid := Id.run do
  let mut t : Array Grid := Array.replicate 4096 (0 : Grid)
  let mut seen : Array Bool := Array.replicate 4096 false
  for g in smallErrors do
    let n := synIdx (synd g)
    if n < 4096 then
      if !seen[n]! then
        t := t.set! n g
        seen := seen.set! n true
  return t

/-- A minimal-weight representative of the coset with syndrome `s`. -/
def leader (s : Syn) : Grid := leaderTable[synIdx s]!

/-- **Every coset has a representative of weight at most 4.**  Verified by
evaluating the table on all 4096 syndromes. -/
theorem leader_ok : ∀ s : Syn, wtG (leader s) ≤ 4 ∧ synd (leader s) = s := by native_decide

/-! ## 3. The covering radius, hence the tax bound -/

/-- **Covering radius at most 4**: every grid is within four cells of a
codeword. -/
theorem covering_radius_le_four (g : Grid) : ∃ e, wtG e ≤ 4 ∧ IsMog (gxor g e) := by
  obtain ⟨hw, hs⟩ := leader_ok (synd g)
  exact ⟨leader (synd g), hw, isMog_of_synd_eq hs⟩

theorem wtG_gxor_le (a b : Grid) : wtG (gxor a b) ≤ wtG a + wtG b := by
  unfold wtG
  rw [← Finset.sum_add_distrib]
  refine Finset.sum_le_sum fun j _ => ?_
  rw [← Finset.sum_add_distrib]
  refine Finset.sum_le_sum fun i _ => ?_
  simp only [gxor]
  rcases Bool.eq_false_or_eq_true (a j i) with h1 | h1 <;>
    rcases Bool.eq_false_or_eq_true (b j i) with h2 | h2 <;> simp [h1, h2]

theorem gxor_eq_zero_iff (a b : Grid) : gxor a b = 0 ↔ a = b := by
  constructor
  · intro h
    funext j i
    have := congrFun (congrFun h j) i
    simp only [gxor, zero_apply] at this
    revert this
    cases a j i <;> cases b j i <;> simp
  · rintro rfl
    funext j i
    simp only [gxor, Bool.xor_self]
    rfl

/-- A full face: four cells, and not a codeword. -/
def oneFace : Grid := gridOf [(0, 0), (0, 1), (0, 2), (0, 3)]

theorem oneFace_wt : wtG oneFace = 4 := by native_decide

/-- **The bound 4 is attained.**  For the weight-4 grid `oneFace`, no repair of
three cells or fewer reaches the code: its distance to the code is exactly 4.
So the covering radius is 4 and the worst-case tax `4Q` is real. -/
theorem covering_radius_ge_four : ∀ e : Grid, IsMog (gxor oneFace e) → 4 ≤ wtG e := by
  intro e he
  by_contra hlt
  push_neg at hlt
  have hle : wtG (gxor oneFace e) ≤ 7 := by
    have := wtG_gxor_le oneFace e
    rw [oneFace_wt] at this
    omega
  have hz : gxor oneFace e = 0 := by
    by_contra hne
    have := mog_min_weight _ he hne
    omega
  have : oneFace = e := (gxor_eq_zero_iff _ _).mp hz
  rw [← this, oneFace_wt] at hlt
  omega

/-! ## 4. Certified repair below the boundary, ambiguity at it -/

/-- **Unique repair up to three cells.**  If two corrections of at most three
cells both land in the code, they are the same correction. -/
theorem repair_unique_of_le_three {g e e' : Grid} (he : wtG e ≤ 3) (he' : wtG e' ≤ 3)
    (h : IsMog (gxor g e)) (h' : IsMog (gxor g e')) : e = e' := by
  have hcode : IsMog (gxor (gxor g e) (gxor g e')) := IsMog_gxor h h'
  have hEq : gxor (gxor g e) (gxor g e') = gxor e e' := by
    funext j i
    simp only [gxor]
    cases g j i <;> cases e j i <;> cases e' j i <;> rfl
  rw [hEq] at hcode
  by_contra hne
  have hz : gxor e e' ≠ 0 := fun h0 => hne ((gxor_eq_zero_iff _ _).mp h0)
  have h8 := mog_min_weight _ hcode hz
  have := wtG_gxor_le e e'
  omega

/-- **Ambiguity at four.**  There is a grid with two different corrections of
weight 4 that both land in the code: at the covering radius the cube must
choose, and that choice is a read, not a computation. -/
theorem repair_ambiguous_at_four :
    ∃ (g e e' : Grid), e ≠ e' ∧ wtG e = 4 ∧ wtG e' = 4 ∧
      IsMog (gxor g e) ∧ IsMog (gxor g e') := by
  refine ⟨oneFace, oneFace, gridOf [(1, 0), (1, 1), (1, 2), (1, 3)], ?_, ?_, ?_, ?_, ?_⟩ <;>
    native_decide

/-! ## 5. The nonlinear class really is nonlinear -/

/-- Cellwise AND of two grids. -/
def gand (g h : Grid) : Grid := fun j i => (g j i && h j i)

/-- **AND is a priced operation**: two codewords whose AND is not a codeword. -/
theorem and_is_priced :
    IsMog (mogBasis 0) ∧ IsMog (mogBasis 2) ∧ ¬ IsMog (gand (mogBasis 0) (mogBasis 2)) :=
  ⟨mogBasis_isMog 0, mogBasis_isMog 2, by native_decide⟩

/-- …and its damage is repaired for at most `4·Q`, like any other damage. -/
theorem and_repair_le_four (g h : Grid) :
    ∃ e, wtG e ≤ 4 ∧ IsMog (gxor (gand g h) e) := covering_radius_le_four _

/-! ## 6. The price, in the substrate's own unit -/

/-- The tax of a repair of `n` cells. -/
noncomputable def taxCells (n : Nat) : ℝ := (n : ℝ) * Q

/-- **The tax bound.**  Any grid can be returned to the code for at most `4·Q`,
and by `covering_radius_ge_four` that bound is attained. -/
theorem tax_le_four_Q (g : Grid) :
    ∃ e, IsMog (gxor g e) ∧ taxCells (wtG e) ≤ 4 * Q := by
  obtain ⟨e, hw, hm⟩ := covering_radius_le_four g
  refine ⟨e, hm, ?_⟩
  have hQ : (0 : ℝ) ≤ Q := le_of_lt Q_pos
  have : (wtG e : ℝ) ≤ 4 := by exact_mod_cast hw
  rw [taxCells]
  nlinarith

/-- XOR with a codeword is free: it never leaves the code. -/
theorem xor_codeword_free {g c : Grid} (hg : IsMog g) (hc : IsMog c) : IsMog (gxor g c) :=
  IsMog_gxor hg hc

end GLM.CubeTax
