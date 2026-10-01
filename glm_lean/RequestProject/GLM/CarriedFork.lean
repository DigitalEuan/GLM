module

public import Mathlib

/-!
# The carried fork: six candidates carried until a later decision resolves them

The formal half of `studies/CARRIED_FORK_STUDY.md`. The Python module
`glm_universal/reasoning/carried_fork.py` keeps the six equidistant Golay
candidates of a deep-hole read as a live set, and lets later stages remove
candidates, each with a reason. This file proves the rules that make an answer
from such a fork trustworthy, in the generality the module uses them.

* `live_subset`, `live_append`, `live_comm` — carrying a fork through more
  stages only shrinks it, and the order in which later decisions arrive does
  not matter.
* `ledger_partition` — the live candidates and the eliminated ones always
  partition the candidates.
* `truth_survives`, `resolved_eq_truth` — if every stage is true of the
  truth and the truth was a candidate, a fork left with one candidate holds
  the truth. With the stage "is a declared case" this is the closed-world
  resolution of `classify`; with "is a candidate of the second read" it is
  the second reading.
* `at_most_one_fits`, `unsure_resolves` — pairwise disjoint tetrads cannot
  both fit inside an unsure set of fewer than eight coordinates, so the
  unsure-set stage always resolves, and to the truth.
* `soft_cost_coord`, `soft_cost_sum` — on a soft reading, the extra squared
  distance a candidate pays over the hard decision is the total reliability
  `|2 s_j − 1|` of the coordinates where it differs from the hard word.
* `even_lift_dist`, `odd_lift_dist` — the lower bounds behind the Leech
  lift: an even-type point whose mod-4 pattern differs from the hard word in
  `d` coordinates is at squared distance at least `4 d` from `2 y`, and an
  odd-type point is at least `24` away.
-/

@[expose] public section

namespace GLM.CarriedFork

open Finset

variable {α : Type*}

/-- The candidates still live after a list of stages, each a predicate that a
candidate must satisfy to stay. -/
def live (cands : Finset α) (stages : List (α → Bool)) : Finset α :=
  cands.filter (fun c => stages.all (fun p => p c))

theorem live_subset (cands : Finset α) (stages : List (α → Bool)) :
    live cands stages ⊆ cands :=
  filter_subset _ _

/-- A further stage can only remove candidates. -/
theorem live_append (cands : Finset α) (s t : List (α → Bool)) :
    live cands (s ++ t) ⊆ live cands s := by
  intro c hc
  simp only [live, mem_filter, List.all_append, Bool.and_eq_true] at hc ⊢
  exact ⟨hc.1, hc.2.1⟩

/-- The order in which the later decisions arrive does not matter. -/
theorem live_comm (cands : Finset α) (s t : List (α → Bool)) :
    live cands (s ++ t) = live cands (t ++ s) := by
  ext c
  simp only [live, mem_filter, List.all_append, Bool.and_comm]

/-- The ledger: live and eliminated candidates partition the candidates. -/
theorem ledger_partition [DecidableEq α] (cands : Finset α) (stages : List (α → Bool)) :
    live cands stages ∪ (cands \ live cands stages) = cands ∧
      Disjoint (live cands stages) (cands \ live cands stages) :=
  ⟨union_sdiff_of_subset (live_subset _ _), disjoint_sdiff⟩

/-- A stage that is true of the truth never removes it. -/
theorem truth_survives {cands : Finset α} {stages : List (α → Bool)} {truth : α}
    (h : truth ∈ cands) (hs : ∀ p ∈ stages, p truth = true) :
    truth ∈ live cands stages := by
  simp only [live, mem_filter, List.all_eq_true]
  exact ⟨h, hs⟩

/-- **A resolved fork holds the truth**: if the truth was a candidate, every
stage is true of it, and exactly one candidate is left, that candidate is the
truth. No order-based choice is involved. -/
theorem resolved_eq_truth {cands : Finset α} {stages : List (α → Bool)}
    {truth : α} (h : truth ∈ cands) (hs : ∀ p ∈ stages, p truth = true)
    (h1 : (live cands stages).card = 1) : live cands stages = {truth} := by
  obtain ⟨a, ha⟩ := card_eq_one.mp h1
  have := truth_survives h hs
  rw [ha, mem_singleton] at this
  rw [ha, this]

/-- A fork with no live candidate refutes an assumption: some stage is false
of the truth, or the truth was never a candidate. -/
theorem contradicted_refutes {cands : Finset α} {stages : List (α → Bool)}
    {truth : α} (h0 : live cands stages = ∅) :
    truth ∉ cands ∨ ∃ p ∈ stages, p truth = false := by
  by_contra hc
  push_neg at hc
  have := truth_survives hc.1 (fun p hp => by
    have := hc.2 p hp
    cases hpt : p truth <;> simp_all)
  rw [h0] at this
  simp at this

/-- **Two disjoint tetrads cannot share a small unsure set.** For pairwise
disjoint error patterns, each of size at least `k`, at most one of them fits
inside a set of fewer than `2 k` coordinates. -/
theorem at_most_one_fits {ι β : Type*} [Fintype ι] [DecidableEq ι]
    [DecidableEq β] (T : ι → Finset β) (k : ℕ) (hT : ∀ i, k ≤ (T i).card)
    (hdisj : Pairwise (fun i j => Disjoint (T i) (T j))) (U : Finset β)
    (hU : U.card < 2 * k) :
    (univ.filter (fun i => T i ⊆ U)).card ≤ 1 := by
  rw [card_le_one]
  intro i hi j hj
  simp only [mem_filter, mem_univ, true_and] at hi hj
  by_contra hne
  have hsub : T i ∪ T j ⊆ U := union_subset hi hj
  have hcard := card_le_card hsub
  rw [card_union_of_disjoint (hdisj hne)] at hcard
  have := hT i
  have := hT j
  omega

/-- **The unsure-set stage resolves, to the truth.** If the true error
pattern lies inside the unsure set and the set has fewer than `2 k`
coordinates, the only pattern that fits is the true one. -/
theorem unsure_resolves {ι β : Type*} [Fintype ι] [DecidableEq ι]
    [DecidableEq β] (T : ι → Finset β) (k : ℕ) (hT : ∀ i, k ≤ (T i).card)
    (hdisj : Pairwise (fun i j => Disjoint (T i) (T j))) (U : Finset β)
    (hU : U.card < 2 * k) (t : ι) (ht : T t ⊆ U) :
    univ.filter (fun i => T i ⊆ U) = {t} := by
  have hle := at_most_one_fits T k hT hdisj U hU
  have hmem : t ∈ univ.filter (fun i => T i ⊆ U) := by simp [ht]
  rw [eq_singleton_iff_unique_mem]
  exact ⟨hmem, fun x hx => card_le_one.mp hle x hx t hmem⟩

/-- The hard decision of a soft level: `1` from one half up. -/
def hard (x : ℚ) : ℚ := if 1 / 2 ≤ x then 1 else 0

/-- **The price of disagreeing with the hard decision, one coordinate.** For a
bit `b ∈ {0, 1}`, the extra squared distance it pays over the hard decision is
zero where it agrees, and the reliability `|2 x − 1|` where it does not. -/
theorem soft_cost_coord (x b : ℚ) (hb : b = 0 ∨ b = 1) :
    (x - b) ^ 2 - (x - hard x) ^ 2 = if b = hard x then 0 else |2 * x - 1| := by
  unfold hard
  by_cases h : (1 : ℚ) / 2 ≤ x
  · rw [if_pos h, abs_of_nonneg (by linarith)]
    rcases hb with rfl | rfl
    · rw [if_neg (by norm_num)]; ring
    · rw [if_pos rfl]; ring
  · rw [if_neg h, abs_of_neg (by linarith)]
    rcases hb with rfl | rfl
    · rw [if_pos rfl]; ring
    · rw [if_neg (by norm_num)]; ring

/-- **The price of a candidate, summed.** The extra squared distance from a
soft reading to a 0/1 candidate over the hard word is the total reliability of
the coordinates where the candidate differs from the hard word — for a
deep-hole candidate, the reliability of its tetrad. -/
theorem soft_cost_sum {n : ℕ} (s c : Fin n → ℚ) (hc : ∀ j, c j = 0 ∨ c j = 1) :
    ∑ j, (s j - c j) ^ 2 - ∑ j, (s j - hard (s j)) ^ 2 =
      ∑ j ∈ univ.filter (fun j => c j ≠ hard (s j)), |2 * s j - 1| := by
  rw [← sum_sub_distrib, sum_filter]
  refine sum_congr rfl (fun j _ => ?_)
  rw [soft_cost_coord (s j) (c j) (hc j)]
  split_ifs <;> simp_all

/-- One coordinate of an even-type lift: if the mod-4 pattern of an even
integer `x` differs from the bit `y`, then `x` is at squared distance at least
`4` from `2 y`. -/
theorem even_lift_coord (x : ℤ) (y : Bool) (hx : Even x)
    (hne : (x % 4 = 2) ≠ (y = true)) : 4 ≤ (x - 2 * (if y then 1 else 0)) ^ 2 := by
  have key : ∀ z : ℤ, z % 4 = 2 → 4 ≤ z ^ 2 := by
    intro z hz
    have : (2 : ℤ) ≤ |z| := by
      rcases abs_cases z with ⟨h1, _⟩ | ⟨h1, _⟩ <;> omega
    nlinarith [sq_abs z, abs_nonneg z]
  have hx2 := Int.even_iff.mp hx
  cases y
  · simp only [Bool.false_eq_true, if_false, mul_zero, sub_zero] at hne ⊢
    exact key x (by simpa using hne)
  · simp only [if_true, mul_one] at hne ⊢
    exact key (x - 2) (by
      have : ¬ x % 4 = 2 := by simpa using hne
      omega)

/-- **Even-type lifts.** An even-type point whose mod-4 pattern differs from
the hard word `y` in `d` coordinates is at squared distance at least `4 d`
from `2 y`. At coset weight 4 every pattern that is a codeword differs in at
least 4 coordinates, so the lifted word is at least 16 from every even-type
Leech point. -/
theorem even_lift_dist {n : ℕ} (x : Fin n → ℤ) (y : Fin n → Bool)
    (hx : ∀ j, Even (x j)) :
    4 * ((univ.filter (fun j => (x j % 4 = 2) ≠ (y j = true))).card : ℤ) ≤
      ∑ j, (x j - 2 * (if y j then 1 else 0)) ^ 2 := by
  calc 4 * ((univ.filter (fun j => (x j % 4 = 2) ≠ (y j = true))).card : ℤ)
      = ∑ _j ∈ univ.filter (fun j => (x j % 4 = 2) ≠ (y j = true)), (4 : ℤ) := by
        rw [sum_const, nsmul_eq_mul]; ring
    _ ≤ ∑ j ∈ univ.filter (fun j => (x j % 4 = 2) ≠ (y j = true)),
          (x j - 2 * (if y j then 1 else 0)) ^ 2 := by
        refine sum_le_sum (fun j hj => ?_)
        simp only [mem_filter, mem_univ, true_and] at hj
        exact even_lift_coord (x j) (y j) (hx j) hj
    _ ≤ ∑ j, (x j - 2 * (if y j then 1 else 0)) ^ 2 :=
        sum_le_sum_of_subset_of_nonneg (filter_subset _ _)
          (fun j _ _ => sq_nonneg _)

/-- **Odd-type lifts.** Every coordinate of an odd-type point is an odd
integer, at distance at least 1 from the even integer `2 y_j`, so the point is
at squared distance at least `n` (24 for the Leech lattice) from `2 y`. -/
theorem odd_lift_dist {n : ℕ} (x : Fin n → ℤ) (y : Fin n → Bool)
    (hx : ∀ j, Odd (x j)) :
    (n : ℤ) ≤ ∑ j, (x j - 2 * (if y j then 1 else 0)) ^ 2 := by
  have : ∀ j, (1 : ℤ) ≤ (x j - 2 * (if y j then 1 else 0)) ^ 2 := by
    intro j
    obtain ⟨r, hr⟩ := hx j
    have hne : x j - 2 * (if y j then 1 else 0) ≠ 0 := by
      split_ifs <;> omega
    have : (1:ℤ) ≤ |x j - 2 * (if y j then 1 else 0)| := Int.one_le_abs hne
    nlinarith [sq_abs (x j - 2 * (if y j then 1 else 0))]
  calc (n : ℤ) = ∑ _j : Fin n, (1 : ℤ) := by simp
    _ ≤ _ := sum_le_sum (fun j _ => this j)

end GLM.CarriedFork
