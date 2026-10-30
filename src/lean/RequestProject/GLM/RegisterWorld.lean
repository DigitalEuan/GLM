import Mathlib
import RequestProject.GLM.Completion

/-!
# The register against the world

Round 6 of the order of work (`glm_universal.runtime.register_world`,
Phase 93, `studies/REGISTER_WORLD_STUDY.md`) compares every row of the element
register, in the three fields an outside source holds, with that source — the
CIAAW standard atomic weights and the NIST ionization energies and ground
configurations — and never writes to the register.  It also tightens the
completion gate of `GLM.Completion` with a nested holdout.  This file states
the reading and proves what each verdict is worth.

* **A discrepancy is earned** (`compare_discrepant_iff`): a cell is reported
  `discrepant` exactly when no value is allowed both by the register, read at
  the precision it is held to, and by the world.  So a register value that is
  a correct rounding of some value the world allows is never reported
  discrepant (`not_discrepant_of_correct_rounding`), and the report's other
  numeric verdicts mean what they say (`compare_agrees_iff`,
  `compare_atPrecision_iff`).
* **An injected error is caught** (`discrepant_of_above`,
  `discrepant_of_below`): a register value held wholly outside the world's
  interval is reported `discrepant` — the mutation audit of mark R4.
* **Every cell is decided once** (`compare_cases`): the six verdicts are
  exhaustive, and which one applies is fixed by which side is silent.
* **A molecule inherits its discrepancy** (`sum_meets`,
  `exists_disjoint_of_sum_disjoint`): if every element's held interval meets
  its standard interval, then any non-negative combination of them meets the
  combined standard, so a molecule can be discrepant only if one of its
  elements is (mark R5).
* **A configuration is an occupation** (`occ_perm`, `occ_append`): the
  occupation read off a written configuration does not depend on the order
  the subshells are written in, and expanding a core adds the core's
  occupation.
* **The nested gate only removes** (`filled_of_restrict`,
  `coverage_restrict`, `measured_restrict`): a stricter gate — fewer fields
  admitted, or a rule admitted on fewer elements — fills no cell the looser
  one left empty, and leaves the measured layer exactly the register.
-/

namespace GLM.RegisterWorld

/-! ## 1.  Intervals, and the reading of a held value -/

/-- A closed interval of rationals. -/
structure Iv where
  /-- The lower end. -/
  lo : ℚ
  /-- The upper end. -/
  hi : ℚ

/-- Membership in a closed interval. -/
def Iv.mem (I : Iv) (x : ℚ) : Prop := I.lo ≤ x ∧ x ≤ I.hi

/-- Two closed intervals meet. -/
def Iv.meets (I J : Iv) : Prop := I.lo ≤ J.hi ∧ J.lo ≤ I.hi

/-- A register value `x` read at its stated precision: half a unit `h` of its
last place either side (`Interval.as_held`). -/
def held (x h : ℚ) : Iv := ⟨x - h, x + h⟩

/-- Two well-formed intervals meet exactly when some value lies in both. -/
theorem meets_iff_exists {I J : Iv} (hI : I.lo ≤ I.hi) (hJ : J.lo ≤ J.hi) :
    I.meets J ↔ ∃ y, I.mem y ∧ J.mem y := by
  constructor
  · rintro ⟨h1, h2⟩
    exact ⟨max I.lo J.lo, ⟨le_max_left _ _, max_le hI h2⟩,
      ⟨le_max_right _ _, max_le h1 hJ⟩⟩
  · rintro ⟨y, ⟨h1, h2⟩, h3, h4⟩
    exact ⟨h1.trans h4, h3.trans h2⟩

/-! ## 2.  The six verdicts -/

/-- The verdict one cell may receive. -/
inductive Verdict
  /-- The register's point lies inside the world's interval. -/
  | agrees
  /-- Outside, but the held interval meets the world's. -/
  | agreesAtPrecision
  /-- No value both allow exists. -/
  | discrepant
  /-- The world holds no value. -/
  | worldSilent
  /-- The register holds no value. -/
  | registerSilent
  /-- Neither holds a value. -/
  | bothSilent
  deriving DecidableEq

/-- The reading of a numeric cell (`register_world.compare_number`): the
register's value `x` held to half-unit `h`, against the world's interval. -/
def compare (reg : Option ℚ) (h : ℚ) (world : Option Iv) : Verdict :=
  match world, reg with
  | none, none => Verdict.bothSilent
  | none, some _ => Verdict.worldSilent
  | some _, none => Verdict.registerSilent
  | some W, some x =>
      if W.lo ≤ x ∧ x ≤ W.hi then Verdict.agrees
      else if W.lo ≤ x + h ∧ x - h ≤ W.hi then Verdict.agreesAtPrecision
      else Verdict.discrepant

/-- Which side is silent decides the silent verdicts, and only they. -/
theorem compare_cases (reg : Option ℚ) (h : ℚ) (world : Option Iv) :
    (world = none ∧ reg = none ∧ compare reg h world = Verdict.bothSilent)
    ∨ (world = none ∧ reg.isSome ∧ compare reg h world = Verdict.worldSilent)
    ∨ (world.isSome ∧ reg = none
        ∧ compare reg h world = Verdict.registerSilent)
    ∨ (world.isSome ∧ reg.isSome ∧
        (compare reg h world = Verdict.agrees
          ∨ compare reg h world = Verdict.agreesAtPrecision
          ∨ compare reg h world = Verdict.discrepant)) := by
  rcases world with _ | W <;> rcases reg with _ | x
  · simp [compare]
  · simp [compare]
  · simp [compare]
  · right; right; right
    refine ⟨rfl, rfl, ?_⟩
    simp only [compare]
    split_ifs <;> simp

/-- `agrees` means the point lies inside the world's interval. -/
theorem compare_agrees_iff (x h : ℚ) (W : Iv) :
    compare (some x) h (some W) = Verdict.agrees ↔ W.mem x := by
  simp only [compare, Iv.mem]
  split_ifs with h1 h2 <;> simp_all

/-- `discrepant` means exactly that no value is allowed by both the held
register value and the world. -/
theorem compare_discrepant_iff (x : ℚ) {h : ℚ} (hh : 0 ≤ h) (W : Iv)
    (hW : W.lo ≤ W.hi) :
    compare (some x) h (some W) = Verdict.discrepant ↔
      ¬ ∃ y, (held x h).mem y ∧ W.mem y := by
  have hheld : (held x h).lo ≤ (held x h).hi := by
    simp only [held]; linarith
  rw [← meets_iff_exists hheld hW]
  simp only [compare, Iv.meets, held]
  split_ifs with h1 h2
  · obtain ⟨a, b⟩ := h1
    constructor
    · intro hc; cases hc
    · intro hn; exact absurd ⟨by linarith, by linarith⟩ hn
  · constructor
    · intro hc; cases hc
    · intro hn; exact absurd ⟨h2.2, h2.1⟩ hn
  · constructor
    · intro _ hm; exact h2 ⟨hm.2, hm.1⟩
    · intro _; rfl

/-- `agreesAtPrecision` means the point lies outside the world's interval,
but some value both allow exists. -/
theorem compare_atPrecision_iff (x : ℚ) {h : ℚ} (hh : 0 ≤ h) (W : Iv)
    (hW : W.lo ≤ W.hi) :
    compare (some x) h (some W) = Verdict.agreesAtPrecision ↔
      ¬ W.mem x ∧ ∃ y, (held x h).mem y ∧ W.mem y := by
  have hheld : (held x h).lo ≤ (held x h).hi := by
    simp only [held]; linarith
  rw [← meets_iff_exists hheld hW]
  simp only [compare, Iv.meets, Iv.mem, held]
  split_ifs with h1 h2
  · constructor
    · intro hc; cases hc
    · intro hn; exact absurd h1 hn.1
  · constructor
    · intro _; exact ⟨h1, h2.2, h2.1⟩
    · intro _; rfl
  · constructor
    · intro hc; cases hc
    · intro hn; exact absurd ⟨hn.2.2, hn.2.1⟩ h2

/-- **Soundness.**  If the register's value is a correct rounding of some
value the world allows — that value lies within half a unit of it — the cell
is never reported discrepant. -/
theorem not_discrepant_of_correct_rounding {x h t : ℚ} (hh : 0 ≤ h)
    {W : Iv} (hW : W.lo ≤ W.hi) (ht : W.mem t) (hr : |t - x| ≤ h) :
    compare (some x) h (some W) ≠ Verdict.discrepant := by
  rw [Ne, compare_discrepant_iff x hh W hW, not_not]
  refine ⟨t, ⟨?_, ?_⟩, ht⟩ <;> simp only [held] <;>
    [linarith [neg_abs_le (t - x)]; linarith [le_abs_self (t - x)]]

/-- **Detection, above.**  A register value held wholly above the world's
interval is reported discrepant. -/
theorem discrepant_of_above {x h : ℚ} (hh : 0 ≤ h) {W : Iv}
    (hx : W.hi < x - h) :
    compare (some x) h (some W) = Verdict.discrepant := by
  simp only [compare]
  split_ifs with h1 h2
  · obtain ⟨-, b⟩ := h1; linarith
  · obtain ⟨-, b⟩ := h2; linarith
  · rfl

/-- **Detection, below.** -/
theorem discrepant_of_below {x h : ℚ} (hh : 0 ≤ h) {W : Iv}
    (hx : x + h < W.lo) :
    compare (some x) h (some W) = Verdict.discrepant := by
  simp only [compare]
  split_ifs with h1 h2
  · obtain ⟨a, -⟩ := h1; linarith
  · obtain ⟨a, -⟩ := h2; linarith
  · rfl

/-! ## 3.  Molecules: the standard carried through a formula -/

section Molecule

variable {ι : Type*}

/-- The combination `∑ nᵢ Iᵢ` of intervals with non-negative counts. -/
def combine (s : Finset ι) (n : ι → ℚ) (I : ι → Iv) : Iv :=
  ⟨∑ i ∈ s, n i * (I i).lo, ∑ i ∈ s, n i * (I i).hi⟩

/-- If every element's held interval meets its standard interval, the
molecule's combined held interval meets the combined standard. -/
theorem sum_meets (s : Finset ι) (n : ι → ℚ) (hn : ∀ i ∈ s, 0 ≤ n i)
    (H W : ι → Iv) (hm : ∀ i ∈ s, (H i).meets (W i)) :
    (combine s n H).meets (combine s n W) := by
  constructor
  · apply Finset.sum_le_sum
    intro i hi
    exact mul_le_mul_of_nonneg_left (hm i hi).1 (hn i hi)
  · apply Finset.sum_le_sum
    intro i hi
    exact mul_le_mul_of_nonneg_left (hm i hi).2 (hn i hi)

/-- So a molecule whose combined intervals are disjoint has an element whose
own intervals are: a molecule can be discrepant only if one of its elements
is. -/
theorem exists_disjoint_of_sum_disjoint (s : Finset ι) (n : ι → ℚ)
    (hn : ∀ i ∈ s, 0 ≤ n i) (H W : ι → Iv)
    (hd : ¬ (combine s n H).meets (combine s n W)) :
    ∃ i ∈ s, ¬ (H i).meets (W i) := by
  by_contra hall
  push_neg at hall
  exact hd (sum_meets s n hn H W hall)

/-- And a point inside every element's standard gives a combined point
inside the combined standard: an agreeing molecule needs no element to
disagree. -/
theorem sum_mem (s : Finset ι) (n : ι → ℚ) (hn : ∀ i ∈ s, 0 ≤ n i)
    (x : ι → ℚ) (W : ι → Iv) (hm : ∀ i ∈ s, (W i).mem (x i)) :
    (combine s n W).mem (∑ i ∈ s, n i * x i) := by
  constructor
  · apply Finset.sum_le_sum
    intro i hi
    exact mul_le_mul_of_nonneg_left (hm i hi).1 (hn i hi)
  · apply Finset.sum_le_sum
    intro i hi
    exact mul_le_mul_of_nonneg_left (hm i hi).2 (hn i hi)

end Molecule

/-! ## 4.  Configurations as occupations -/

section Configuration

variable {σ : Type*} [DecidableEq σ]

/-- The occupation a written configuration gives one subshell: the electrons
written against it, summed (a subshell may be written twice, once in the core
and once after it). -/
def occ (l : List (σ × ℕ)) (s : σ) : ℕ :=
  ((l.filter fun p => p.1 = s).map Prod.snd).sum

/-- The order the subshells are written in is not part of the occupation:
`[Ar]4s2 3d6` and `[Ar].3d6.4s2` are one configuration. -/
theorem occ_perm {l l' : List (σ × ℕ)} (hp : l.Perm l') : occ l = occ l' := by
  funext s
  exact ((hp.filter _).map Prod.snd).sum_eq

/-- Expanding a core: the occupation of `core ++ rest` is the core's plus the
rest's. -/
theorem occ_append (core rest : List (σ × ℕ)) (s : σ) :
    occ (core ++ rest) s = occ core s + occ rest s := by
  simp [occ, List.filter_append]

end Configuration

/-! ## 5.  The nested gate only removes -/

section Gate

open GLM.Completion

variable {Name Field Value : Type}

/-- `R'` is a restriction of `R`: it admits no field `R` does not, and where
it estimates a cell, `R` estimates the same value.  The nested gate and the
main-group narrowing both produce a restriction of the first gate's rules. -/
structure Restricts (R' R : Rules Name Field Value) : Prop where
  derivable : ∀ f, R'.derivable f = R.derivable f
  admitted : ∀ f, R'.admitted f = true → R.admitted f = true
  estimate : ∀ n f v, R'.admitted f = true → R'.estimate n f = some v →
    R.estimate n f = some v

/-- A cell the stricter rules fill, the looser rules fill. -/
theorem filled_of_restrict (B : Base Name Field Value)
    {R' R : Rules Name Field Value} (hr : Restricts R' R) (n : Name)
    (f : Field) (hf : filled (cell B R' n f) = true) :
    filled (cell B R n f) = true := by
  unfold cell at hf ⊢
  cases hv : B.value n f with
  | some v => rfl
  | none =>
      rw [hv] at hf
      simp only at hf ⊢
      by_cases hd : R'.derivable f = true
      · have hd' : R.derivable f = true := by rw [← hr.derivable f]; exact hd
        by_cases ha : R'.admitted f = true
        · have ha' := hr.admitted f ha
          cases he : R'.estimate n f with
          | none => simp [hd, ha, he, filled] at hf
          | some v =>
              have he' := hr.estimate n f v ha he
              simp [hd', ha', he', filled]
        · simp [hd, ha, filled] at hf
      · simp [hd, filled] at hf

/-- So over any finite set of cells the stricter gate fills no more. -/
theorem coverage_restrict [DecidableEq Name] [DecidableEq Field]
    (B : Base Name Field Value) {R' R : Rules Name Field Value}
    (hr : Restricts R' R) (s : Finset (Name × Field)) :
    (s.filter fun p => filled (cell B R' p.1 p.2) = true).card
      ≤ (s.filter fun p => filled (cell B R p.1 p.2) = true).card := by
  apply Finset.card_le_card
  intro p hp
  simp only [Finset.mem_filter] at hp ⊢
  exact ⟨hp.1, filled_of_restrict B hr p.1 p.2 hp.2⟩

/-- And the measured layer is the register under either gate. -/
theorem measured_restrict (B : Base Name Field Value)
    (R' R : Rules Name Field Value) (n : Name) (f : Field) (v : Value) :
    cell B R' n f = Cell.measured v ↔ cell B R n f = Cell.measured v := by
  rw [cell_measured_iff, cell_measured_iff]

end Gate

/-! ## 6.  The ledgers of the round

The counts are measured by `register_world.world_report` and
`element_completion.element_completion_report`; what is checked here is that
they are partitions of what they are about. -/

/-- 354 cells, three fields of 118 rows, each decided once: atomic weight
(73 agree, 11 at stated precision, 34 world-silent), ionization energy
(10, 68, 24 discrepant, 6 register-silent, 10 both-silent) and configuration
(107 agree, 1 discrepant, 10 world-silent). -/
theorem world_ledger :
    (73 + 11 + 0 + 34 + 0 + 0) + (10 + 68 + 24 + 0 + 6 + 10)
      + (107 + 0 + 1 + 10 + 0 + 0) = 3 * 118 := by norm_num

/-- Under the nested gate the 395 empty cells are decided four ways, and the
completed view fills 1,344 of 1,652. -/
theorem nested_ledger : 87 + 62 + 233 + 13 = 1652 - 1257 ∧ 1257 + 87 = 1344 := by
  norm_num

/-- The estimated cells lost are exactly the two fields' (mark R7): 75
covalent radii and the 23 electron affinities outside the main group. -/
theorem nested_loss : 185 - 75 - 23 = 87 := by norm_num

end GLM.RegisterWorld
