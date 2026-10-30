module

public import Mathlib
public import RequestProject.GLM.ReverseTCTTwo

/-!
# Reverse Three Column Thinking, round three: the integer sort

The formal half of round three of `studies/REVERSE_TCT_STUDY.md` (§10,
Phase 69). `glm_universal/reasoning/reverse_tct_int.py` answers
`entails over the integers:` and `bounds over the integers of x:` by

1. splitting every floor quotient and remainder `A // b`, `A % b` of an
   integer-valued linear `A` by a nonzero integer constant `b` into one case
   per residue `r`, with a fresh integer `q` and the equation `A = b*q + r`;
2. tightening every row over ℤ: a strict row `e < 0` becomes `e + 1 ≤ 0`, and
   a row `g*t + k ≤ 0` becomes `t + ⌈k/g⌉ ≤ 0`;
3. eliminating, every derived row a positive combination of two rows,
   tightened; a derived `0 + k ≤ 0` with `k > 0` refutes the case.

This file proves each step sound, and the first two exact:

* `residue_split_pos`, `residue_split_neg` — for integers `a`, `q`, `r` and a
  divisor `b`, Python's `a // b = q` and `a % b = r` (as round two defines
  them, over ℚ) hold exactly when `a = b*q + r` with `r` in the residue range
  of `b`: `0 ≤ r < b` for `b > 0`, `b < r ≤ 0` for `b < 0`.
* `residue_exists_pos`, `residue_exists_neg` — the residue cases are
  exhaustive.
* `strict_tighten`, `gcd_tighten` — the two tightenings are exact over ℤ.
* `combine_sound`, `step_sound`, `derivation_sound`, `refuted_no_point` — a
  derivation whose steps are positive combinations followed by a gcd
  tightening leaves every integer point of the input rows satisfying every
  derived row, so a derived contradiction leaves no integer point.
* `rational_refutation_suffices` — a system with no rational point has no
  integer point (why a rational refutation is still an integer one).
* `two_x_eq_one` — the example behind declared case `i22`: `2x = 1` has a
  rational solution and no integer one, and the gcd tightening is what sees it.
-/

@[expose] public section

namespace GLM.ReverseTCTThree

open GLM.ReverseTCTTwo

/-! ## The residue split -/

/-- For a positive divisor, Python's floor quotient and remainder of integers
are exactly the quotient and residue of `a = b*q + r`, `0 ≤ r < b`. -/
theorem residue_split_pos (a b q r : ℤ) (hb : 0 < b) :
    (pyFloorDiv a b = q ∧ pyMod a b = r) ↔ (a = b * q + r ∧ 0 ≤ r ∧ r < b) := by
  unfold pyMod pyFloorDiv
  have hb' : (0 : ℚ) < b := by exact_mod_cast hb
  constructor
  · rintro ⟨hq, hr⟩
    rw [hq] at hr
    obtain ⟨h1, h2⟩ := Int.floor_eq_iff.mp hq
    rw [le_div_iff₀ hb'] at h1
    rw [div_lt_iff₀ hb'] at h2
    have e : a - b * q = r := by exact_mod_cast hr
    have h1' : q * b ≤ a := by exact_mod_cast h1
    have h2' : a < (q + 1) * b := by exact_mod_cast h2
    refine ⟨by linarith, by nlinarith, by nlinarith⟩
  · rintro ⟨rfl, h0, h1⟩
    have hq : ⌊((b * q + r : ℤ) : ℚ) / (b : ℚ)⌋ = q := by
      rw [Int.floor_eq_iff, le_div_iff₀ hb', div_lt_iff₀ hb']
      constructor
      · push_cast
        have : (0 : ℚ) ≤ r := by exact_mod_cast h0
        nlinarith
      · push_cast
        have : (r : ℚ) < b := by exact_mod_cast h1
        nlinarith
    refine ⟨hq, ?_⟩
    rw [hq]; push_cast; ring

/-- For a negative divisor, the residue lies in `(b, 0]`. -/
theorem residue_split_neg (a b q r : ℤ) (hb : b < 0) :
    (pyFloorDiv a b = q ∧ pyMod a b = r) ↔ (a = b * q + r ∧ b < r ∧ r ≤ 0) := by
  unfold pyMod pyFloorDiv
  have hb' : (b : ℚ) < 0 := by exact_mod_cast hb
  constructor
  · rintro ⟨hq, hr⟩
    rw [hq] at hr
    obtain ⟨h1, h2⟩ := Int.floor_eq_iff.mp hq
    rw [le_div_iff_of_neg hb'] at h1
    rw [div_lt_iff_of_neg hb'] at h2
    have e : a - b * q = r := by exact_mod_cast hr
    have h1' : a ≤ q * b := by exact_mod_cast h1
    have h2' : (q + 1) * b < a := by exact_mod_cast h2
    refine ⟨by linarith, by nlinarith, by nlinarith⟩
  · rintro ⟨rfl, h0, h1⟩
    have hq : ⌊((b * q + r : ℤ) : ℚ) / (b : ℚ)⌋ = q := by
      rw [Int.floor_eq_iff, le_div_iff_of_neg hb', div_lt_iff_of_neg hb']
      constructor
      · push_cast
        have : (r : ℚ) ≤ 0 := by exact_mod_cast h1
        nlinarith
      · push_cast
        have : (b : ℚ) < r := by exact_mod_cast h0
        nlinarith
    refine ⟨hq, ?_⟩
    rw [hq]; push_cast; ring

/-- The residue cases of a positive divisor are exhaustive. -/
theorem residue_exists_pos (a b : ℤ) (hb : 0 < b) :
    ∃ r ∈ Finset.Ico 0 b, ∃ q, a = b * q + r := by
  obtain ⟨e, h0, h1⟩ := (residue_split_pos a b (pyFloorDiv a b)
    (a - b * pyFloorDiv a b) hb).mp ⟨rfl, by unfold pyMod; push_cast; ring⟩
  exact ⟨_, Finset.mem_Ico.mpr ⟨h0, h1⟩, _, e⟩

/-- The residue cases of a negative divisor are exhaustive. -/
theorem residue_exists_neg (a b : ℤ) (hb : b < 0) :
    ∃ r ∈ Finset.Ioc b 0, ∃ q, a = b * q + r := by
  obtain ⟨e, h0, h1⟩ := (residue_split_neg a b (pyFloorDiv a b)
    (a - b * pyFloorDiv a b) hb).mp ⟨rfl, by unfold pyMod; push_cast; ring⟩
  exact ⟨_, Finset.mem_Ioc.mpr ⟨h0, h1⟩, _, e⟩

/-! ## Tightening over ℤ -/

/-- A strict row over ℤ is the row with its constant raised by one. -/
theorem strict_tighten (e : ℤ) : e < 0 ↔ e + 1 ≤ 0 := by
  omega

/-- Dividing a row by a positive common factor of its coefficients, with the
constant rounded up (`-((-k) / g)` is `⌈k / g⌉`), keeps exactly its integer
points. -/
theorem gcd_tighten (t k g : ℤ) (hg : 0 < g) :
    g * t + k ≤ 0 ↔ t + -((-k) / g) ≤ 0 := by
  have := Int.le_ediv_iff_mul_le (a := t) (b := -k) hg
  constructor
  · intro h
    have : t ≤ (-k) / g := this.mpr (by linarith)
    linarith
  · intro h
    have := this.mp (by linarith)
    linarith

/-! ## Rows and derivations -/

/-- A row over `n` integer variables: `∑ cᵢ xᵢ + k ≤ 0`. -/
abbrev Row (n : ℕ) := (Fin n → ℤ) × ℤ

/-- The row holds at the integer point `x`. -/
def Row.Holds {n : ℕ} (r : Row n) (x : Fin n → ℤ) : Prop :=
  ∑ i, r.1 i * x i + r.2 ≤ 0

/-- A non-negative combination of two rows. -/
def Row.comb {n : ℕ} (a : ℤ) (r : Row n) (b : ℤ) (s : Row n) : Row n :=
  (fun i => a * r.1 i + b * s.1 i, a * r.2 + b * s.2)

/-- A non-negative combination of two valid rows is valid. -/
theorem combine_sound {n : ℕ} (r s : Row n) (a b : ℤ) (ha : 0 ≤ a) (hb : 0 ≤ b)
    (x : Fin n → ℤ) (hr : r.Holds x) (hs : s.Holds x) :
    (Row.comb a r b s).Holds x := by
  unfold Row.Holds Row.comb at *
  have e : ∑ i, (a * r.1 i + b * s.1 i) * x i + (a * r.2 + b * s.2) =
      a * (∑ i, r.1 i * x i + r.2) + b * (∑ i, s.1 i * x i + s.2) := by
    simp only [add_mul, Finset.sum_add_distrib, mul_add, Finset.mul_sum]
    ring_nf
  simp only
  rw [e]
  nlinarith

/-- One derivation step, as the column-3 script checks it: the new row `t`,
multiplied by a positive `g`, has the coefficients of the combination
`a·rᵢ + b·rⱼ` (`a, b > 0`), and its constant is the combination's constant
divided by `g`, rounded up. -/
def ValidStep {n : ℕ} (rows : List (Row n)) (t : Row n) : Prop :=
  ∃ i j : Fin rows.length, ∃ a b g : ℤ, 0 < a ∧ 0 < b ∧ 0 < g ∧
    (∀ v, g * t.1 v = (Row.comb a rows[i] b rows[j]).1 v) ∧
    t.2 = -((-(Row.comb a rows[i] b rows[j]).2) / g)

/-- A valid step keeps every integer point of the rows it is taken from. -/
theorem step_sound {n : ℕ} (rows : List (Row n)) (t : Row n)
    (h : ValidStep rows t) (x : Fin n → ℤ) (hx : ∀ r ∈ rows, r.Holds x) :
    t.Holds x := by
  obtain ⟨i, j, a, b, g, ha, hb, hg, hco, hk⟩ := h
  have hc := combine_sound rows[i] rows[j] a b ha.le hb.le x
    (hx _ (List.getElem_mem _)) (hx _ (List.getElem_mem _))
  unfold Row.Holds at hc ⊢
  have e : ∑ v, (Row.comb a rows[i] b rows[j]).1 v * x v =
      g * ∑ v, t.1 v * x v := by
    rw [Finset.mul_sum]
    refine Finset.sum_congr rfl (fun v _ => ?_)
    rw [← hco v]; ring
  rw [e] at hc
  rw [hk]
  exact (gcd_tighten _ _ g hg).mp hc

/-- A derivation: each derived row is a valid step from the input rows and
the rows derived before it. -/
def Derivation {n : ℕ} (inputs : List (Row n)) : List (Row n) → Prop
  | [] => True
  | t :: ts => Derivation inputs ts ∧ ValidStep (inputs ++ ts.reverse) t

/-- Every integer point of the input rows satisfies every derived row. -/
theorem derivation_sound {n : ℕ} (inputs : List (Row n)) :
    ∀ (ds : List (Row n)), Derivation inputs ds → ∀ x : Fin n → ℤ,
      (∀ r ∈ inputs, r.Holds x) → ∀ r ∈ ds, r.Holds x := by
  intro ds
  induction ds with
  | nil => intro _ _ _ r hr; simp at hr
  | cons t ts ih =>
    intro hd x hx r hr
    obtain ⟨hts, hstep⟩ := hd
    have hall : ∀ r ∈ inputs ++ ts.reverse, r.Holds x := by
      intro r hr
      rcases List.mem_append.mp hr with h | h
      · exact hx r h
      · exact ih hts x hx r (List.mem_reverse.mp h)
    rcases List.mem_cons.mp hr with rfl | h
    · exact step_sound _ _ hstep x hall
    · exact ih hts x hx r h

/-- A derived row with no variables and a positive constant refutes the
input rows: they have no integer point. -/
theorem refuted_no_point {n : ℕ} (inputs ds : List (Row n))
    (hd : Derivation inputs ds) (t : Row n) (ht : t ∈ ds)
    (h0 : ∀ v, t.1 v = 0) (hk : 0 < t.2) :
    ¬ ∃ x : Fin n → ℤ, ∀ r ∈ inputs, r.Holds x := by
  rintro ⟨x, hx⟩
  have := derivation_sound inputs ds hd x hx t ht
  unfold Row.Holds at this
  simp [h0] at this
  omega

/-- A system with no rational point has no integer point. -/
theorem rational_refutation_suffices {n : ℕ} (rows : List (Row n))
    (h : ¬ ∃ y : Fin n → ℚ, ∀ r ∈ rows, ∑ i, (r.1 i : ℚ) * y i + r.2 ≤ 0) :
    ¬ ∃ x : Fin n → ℤ, ∀ r ∈ rows, r.Holds x := by
  rintro ⟨x, hx⟩
  refine h ⟨fun i => (x i : ℚ), fun r hr => ?_⟩
  have := hx r hr
  unfold Row.Holds at this
  have c : ((∑ i, r.1 i * x i + r.2 : ℤ) : ℚ) ≤ 0 := by exact_mod_cast this
  push_cast at c
  exact c

/-- Declared case `i22`: `2x = 1` has the rational solution `1/2` and no
integer solution — the two rows `2x - 1 ≤ 0` and `-2x + 1 ≤ 0` tighten to
`x ≤ 0` and `x ≥ 1`. -/
theorem two_x_eq_one :
    (∃ y : ℚ, 2 * y = 1) ∧ (¬ ∃ x : ℤ, 2 * x = 1) ∧
      ∀ x : ℤ, (2 * x - 1 ≤ 0 ↔ x ≤ 0) ∧ (-2 * x + 1 ≤ 0 ↔ 1 ≤ x) := by
  refine ⟨⟨1 / 2, by norm_num⟩, by omega, fun x => ⟨by omega, by omega⟩⟩

end GLM.ReverseTCTThree
