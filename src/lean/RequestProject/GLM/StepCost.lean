/-
# The graded cost model: gauges, clocks and the 13-shortcut

`Constants.lean` fixes the coherence index `NRCI(v) = B/(B + TAX(v))` with the
shipped budget `B = 10`.  The archive's cost study asked a prior question about
that formula — *which part of it is observable?* — and answered it, together
with two other questions about pricing that the GLM keeps asking.  All three
answers are retrieved here.

## 1. The quantum is a gauge, not an observable

Calibrate the budget to the quantum, `B = 8Q`, and the coherence of a
weight-`n` pattern is `8/(8+n)` **whatever `Q` is** (`nrci_calibrated`,
`nrci_gauge_independent`).  The ladder at the Golay weights — `1, 1/2, 2/5,
1/3, 1/4` at `0, 8, 12, 16, 24` — is therefore `Q`-free (`nrci_ladder`), and
strictly decreasing (`nrci_strictAnti`).  No statement about the ladder can
depend on the value of `Y`.

## 2. A constant rate is not a clock

A graded cost model is a non-negative cost per step indexed by the step number;
`GradedCost.total` accumulates it.  `total_mono` says cost never decreases, and
`total_const` says a *constant* rate contributes nothing beyond the step count.
So a "frequency" is content only where the grading is non-constant.

## 3. A shortcut is a distortion of the word metric

Cost is a homomorphism from the word monoid to `(ℝ, +)` (`wordCost_append`), and
a shortcut is a place where the word metric falls strictly below the naive path
cost.  The concrete instance is the GLM's own step set: moves of size `1` and of
size `13`, the integer part of the monad.

* `wordLen_le_div_add_mod` — reaching `n` costs at most `n/13 + n%13` moves;
* `natAbs_le_thirteen_mul_wordLen` — and at least `|n|/13`: there is no free
  lunch, the shortcut is bounded;
* `shortcut_thirteen`, `shortcut_distortion` — and for every target of size at
  least 14 the word metric is *strictly* below the naive cost.

That last is a distortion theorem, and it is the precise version of "levels give
shortcuts".
-/
import Mathlib

namespace GLM.StepCost

/-! ## 1. The coherence ladder is gauge-independent -/

/-- Coherence with budget `B` and tax `t`.  `GLM.nrci` of `Constants.lean` is
this function with the shipped budget. -/
noncomputable def nrciB (B t : ℝ) : ℝ := B / (B + t)

/-- With the budget calibrated to the quantum, the coherence of a weight-`n`
pattern is `8/(8+n)` for **every** non-zero quantum `Q`. -/
theorem nrci_calibrated (Q : ℝ) (hQ : Q ≠ 0) (n : ℕ) :
    nrciB (8 * Q) (n * Q) = 8 / (8 + n) := by
  have hpos : (0 : ℝ) < 8 + n := by positivity
  unfold nrciB
  rw [show 8 * Q + (n : ℝ) * Q = (8 + n) * Q by ring]
  rw [div_eq_div_iff (by simp [hQ, ne_of_gt hpos]) (ne_of_gt hpos)]
  ring

/-- **The quantum is a gauge, not an observable**: two different quanta give the
same ladder. -/
theorem nrci_gauge_independent (Q Q' : ℝ) (hQ : Q ≠ 0) (hQ' : Q' ≠ 0) (n : ℕ) :
    nrciB (8 * Q) (n * Q) = nrciB (8 * Q') (n * Q') := by
  rw [nrci_calibrated Q hQ, nrci_calibrated Q' hQ']

/-- The ladder at the Golay weights. -/
theorem nrci_ladder (Q : ℝ) (hQ : Q ≠ 0) :
    nrciB (8 * Q) (0 * Q) = 1 ∧ nrciB (8 * Q) (8 * Q) = 1 / 2 ∧
      nrciB (8 * Q) (12 * Q) = 2 / 5 ∧ nrciB (8 * Q) (16 * Q) = 1 / 3 ∧
      nrciB (8 * Q) (24 * Q) = 1 / 4 := by
  refine ⟨?_, ?_, ?_, ?_, ?_⟩
  · have := nrci_calibrated Q hQ 0; norm_num at this ⊢; exact this
  · have := nrci_calibrated Q hQ 8; norm_num at this ⊢; exact this
  · have := nrci_calibrated Q hQ 12; norm_num at this ⊢; exact this
  · have := nrci_calibrated Q hQ 16; norm_num at this ⊢; exact this
  · have := nrci_calibrated Q hQ 24; norm_num at this ⊢; exact this

/-- Heavier patterns are strictly less coherent. -/
theorem nrci_strictAnti {m n : ℕ} (h : m < n) : (8 : ℝ) / (8 + n) < 8 / (8 + m) := by
  have hm : (0 : ℝ) < 8 + m := by positivity
  have hmn : (m : ℝ) < n := by exact_mod_cast h
  exact div_lt_div_of_pos_left (by norm_num) hm (by linarith)

/-! ## 2. The graded cost model — adding a clock -/

/-- A **graded cost model**: a non-negative cost for each step, indexed by the
step number.  The grading *is* the clock. -/
structure GradedCost where
  /-- The cost of the `k`-th step. -/
  step : ℕ → ℝ
  /-- Costs are non-negative. -/
  nonneg : ∀ k, 0 ≤ step k

namespace GradedCost

/-- The accumulated cost of the first `n` steps. -/
def total (G : GradedCost) (n : ℕ) : ℝ := ∑ k ∈ Finset.range n, G.step k

theorem total_zero (G : GradedCost) : G.total 0 = 0 := by simp [total]

theorem total_succ (G : GradedCost) (n : ℕ) : G.total (n + 1) = G.total n + G.step n := by
  simp [total, Finset.sum_range_succ]

/-- Cost never decreases with more steps. -/
theorem total_mono (G : GradedCost) : Monotone G.total := by
  intro m n hmn
  have hsub : Finset.range m ⊆ Finset.range n := by
    intro x hx
    simp only [Finset.mem_range] at hx ⊢
    omega
  exact Finset.sum_le_sum_of_subset_of_nonneg hsub (fun k _ _ => G.nonneg k)

/-- **A constant rate adds nothing to the step count.**  A "frequency" is
content only when the grading is non-constant. -/
theorem total_const (c : ℝ) (hc : 0 ≤ c) (n : ℕ) :
    (GradedCost.mk (fun _ => c) (fun _ => hc)).total n = n * c := by
  simp [total]

end GradedCost

/-! ## 3. Cost as a homomorphism, and the 13-shortcut -/

/-- The cost of a word: the sum of the costs of its letters. -/
def wordCost {X : Type*} (c : X → ℝ) (l : List X) : ℝ := (l.map c).sum

/-- Cost is a monoid homomorphism from words to `(ℝ, +)`. -/
theorem wordCost_append {X : Type*} (c : X → ℝ) (l m : List X) :
    wordCost c (l ++ m) = wordCost c l + wordCost c m := by
  simp [wordCost]

theorem wordCost_nil {X : Type*} (c : X → ℝ) : wordCost c ([] : List X) = 0 := by
  simp [wordCost]

/-- The available moves: a unit step and a hull-sized step, in both directions. -/
def stepMoves : Set ℤ := {1, -1, 13, -13}

theorem mem_stepMoves {x : ℤ} (h : x ∈ stepMoves) : x = 1 ∨ x = -1 ∨ x = 13 ∨ x = -13 := by
  simpa [stepMoves] using h

theorem abs_le_thirteen_of_mem {x : ℤ} (h : x ∈ stepMoves) : |x| ≤ 13 := by
  rcases mem_stepMoves h with h | h | h | h <;> rw [h] <;> decide

/-- `ReachIn n k`: the integer `n` is the sum of a word of `k` moves. -/
def ReachIn (n : ℤ) (k : ℕ) : Prop :=
  ∃ l : List ℤ, (∀ x ∈ l, x ∈ stepMoves) ∧ l.sum = n ∧ l.length = k

/-- The word metric: the least number of moves reaching `n`. -/
noncomputable def wordLen (n : ℤ) : ℕ := sInf {k | ReachIn n k}

theorem reachIn_natAbs (n : ℤ) : ReachIn n n.natAbs := by
  rcases le_or_gt 0 n with h | h
  · refine ⟨List.replicate n.natAbs 1, ?_, ?_, ?_⟩
    · intro x hx
      rw [List.eq_of_mem_replicate hx]
      simp [stepMoves]
    · rw [List.sum_replicate]
      simp [Int.natAbs_of_nonneg h]
    · simp
  · refine ⟨List.replicate n.natAbs (-1), ?_, ?_, ?_⟩
    · intro x hx
      rw [List.eq_of_mem_replicate hx]
      simp [stepMoves]
    · rw [List.sum_replicate]
      simp only [nsmul_eq_mul, mul_neg, mul_one]
      omega
    · simp

theorem reach_nonempty (n : ℤ) : {k | ReachIn n k}.Nonempty := ⟨n.natAbs, reachIn_natAbs n⟩

theorem wordLen_le {n : ℤ} {k : ℕ} (h : ReachIn n k) : wordLen n ≤ k := Nat.sInf_le h

theorem reachIn_wordLen (n : ℤ) : ReachIn n (wordLen n) := Nat.sInf_mem (reach_nonempty n)

/-- **Upper bound.**  Using the big step, `n` is reached in at most
`n/13 + n%13` moves. -/
theorem wordLen_le_div_add_mod (n : ℕ) : wordLen n ≤ n / 13 + n % 13 := by
  refine wordLen_le ⟨List.replicate (n / 13) 13 ++ List.replicate (n % 13) 1, ?_, ?_, ?_⟩
  · intro x hx
    rcases List.mem_append.1 hx with hx | hx
    · rw [List.eq_of_mem_replicate hx]; simp [stepMoves]
    · rw [List.eq_of_mem_replicate hx]; simp [stepMoves]
  · rw [List.sum_append, List.sum_replicate, List.sum_replicate]
    simp only [nsmul_eq_mul, mul_one]
    have := Nat.div_add_mod n 13
    push_cast
    omega
  · simp [List.length_append]

/-- Every word of moves has a bounded sum. -/
theorem abs_sum_le (l : List ℤ) (h : ∀ x ∈ l, x ∈ stepMoves) : |l.sum| ≤ 13 * l.length := by
  induction l with
  | nil => simp
  | cons a t ih =>
      have ha : |a| ≤ 13 := abs_le_thirteen_of_mem (h a (List.mem_cons_self ..))
      have ht : |t.sum| ≤ 13 * t.length := ih fun x hx => h x (List.mem_cons_of_mem a hx)
      have : |a + t.sum| ≤ |a| + |t.sum| := abs_add_le _ _
      simp only [List.sum_cons, List.length_cons]
      push_cast
      linarith

/-- **Lower bound: no free lunch.**  Reaching `n` costs at least `|n|/13` moves. -/
theorem natAbs_le_thirteen_mul_wordLen (n : ℤ) : |n| ≤ 13 * (wordLen n : ℤ) := by
  obtain ⟨l, hmem, hsum, hlen⟩ := reachIn_wordLen n
  have := abs_sum_le l hmem
  rw [hsum, hlen] at this
  exact this

/-- **The shortcut.**  The hull-sized move costs one step, not thirteen. -/
theorem shortcut_thirteen : wordLen 13 = 1 := by
  have hle : wordLen 13 ≤ 1 := by
    refine wordLen_le ⟨[13], ?_, ?_, ?_⟩
    · intro x hx; simp at hx; simp [hx, stepMoves]
    · simp
    · simp
  have hne : wordLen 13 ≠ 0 := by
    intro h0
    obtain ⟨l, _, hsum, hlen⟩ := reachIn_wordLen (13 : ℤ)
    rw [h0, List.length_eq_zero_iff] at hlen
    rw [hlen] at hsum
    simp at hsum
  omega

/-- **The distortion theorem.**  For every target of size at least 14 the word
metric is strictly below the naive unit-step cost: the level structure really
does buy something, and `natAbs_le_thirteen_mul_wordLen` says how much. -/
theorem shortcut_distortion (n : ℕ) (h : 14 ≤ n) : wordLen n < n := by
  have h1 := wordLen_le_div_add_mod n
  have h2 : n / 13 + n % 13 < n := by omega
  omega

end GLM.StepCost
