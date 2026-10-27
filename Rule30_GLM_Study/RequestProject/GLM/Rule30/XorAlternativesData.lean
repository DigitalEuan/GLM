import RequestProject.GLM.Rule30.RunCountGeneral
import RequestProject.GLM.Rule30.HankelKronecker

/-!
# Round 24: finite checks for the XOR alternatives

(Not a `module`: the checks use `native_decide`.)  All statements here are `CERT`.

* `runCountW_thirty_edge`, `outer_law_fails`, `outer_runCount_law_iff`, `outer_and_breaks_law`,
  `outer_or_breaks_law` : the counting law fails for every non-left-permutive gate in place of
  the XOR (see `RunCountGeneral.lean`).
* A sound window simulator for every wheel on the impulse row (`winStep_window`, `colGo_spec`,
  `centreList_spec`) and the check **`orType_no_small_period`** : for the four OR-type wheels
  `L xor h(C, R)` (30, 45, 75, 135), whose centre-column questions are open, the centre column has
  no eventual period `p ≤ 500` starting at or before time `500`.  This is the same kind of finite
  evidence as `no_small_eventual_period` for Rule 30, now for the whole OR-type class: the four
  wheels that `inner_alternative_periodic` cannot settle all look aperiodic.
* `frontier_round24` collects the round (including Kronecker's converse from
  `HankelKronecker.lean`).
-/

namespace GLM.Rule30

/-- Rule 30 at the edge: `20 ≠ 16`. -/
theorem runCountW_thirty_edge : RunCountW 30 2 3 3 = 20 := by native_decide

/-! ## Replacing the XOR breaks the law -/

/-- For the 16 gates `g` in `g(L, C or R)`, a finite check: if the wheel is not left-permutive,
the period-2 law already fails at `d = 3, T = 2` or at `d = 4, T = 3`. -/
theorem outer_law_fails (g : BinGate) (hg : ¬ IsLeftPermutive (outerRule g)) :
    RunCountW (outerRule g) 2 3 2 ≠ 2 ^ 4 ∨ RunCountW (outerRule g) 2 4 3 ≠ 2 ^ 5 := by
  rw [gate_eq_gateOf g] at hg ⊢
  generalize g false false = b0 at hg ⊢
  generalize g false true = b1 at hg ⊢
  generalize g true false = b2 at hg ⊢
  generalize g true true = b3 at hg ⊢
  revert b0 b1 b2 b3
  native_decide

/-- **Among the 16 ways to replace the XOR, the counting law holds exactly for the
left-permutive ones** (`xor`, `xnor`, `L`, `not L`; `outerRule_leftPermutive_iff`). -/
theorem outer_runCount_law_iff (g : BinGate) :
    (∀ d T, 1 ≤ T → T < d → RunCountW (outerRule g) 2 d T = 2 ^ (d + 1)) ↔
      IsLeftPermutive (outerRule g) := by
  constructor
  · intro h
    by_contra hg
    rcases outer_law_fails g hg with h1 | h1
    · exact h1 (h 3 2 (by norm_num) (by norm_num))
    · exact h1 (h 4 3 (by norm_num) (by norm_num))
  · intro hr d T hT hTd
    exact runCountW_law hr 2 d T (by norm_num) (by omega) hTd

/-- AND in place of XOR (wheel 224): `21` contexts instead of `16`. -/
theorem outer_and_breaks_law : RunCountW 224 2 3 2 = 21 := by native_decide

/-- OR in place of XOR (wheel 254): `17` contexts instead of `16`. -/
theorem outer_or_breaks_law : RunCountW 254 2 3 2 = 17 := by native_decide

/-! ## A sound window simulator -/

/-- One step on a window: the cells `x a, …, x (a + len - 1)` give `x' (a + 1), …,
x' (a + len - 2)`. -/
def winStep (r : ℕ) : List Bool → List Bool
  | a :: b :: c :: rest => ecaRule r a b c :: winStep r (b :: c :: rest)
  | _ => []

theorem winStep_map (r : ℕ) : ∀ (m : ℕ) (f : ℕ → Bool), winStep r ((List.range (m + 2)).map f) =
      (List.range m).map fun i => ecaRule r (f i) (f (i + 1)) (f (i + 2)) := by
  intro m
  induction m with
  | zero => intro f; simp [List.range_succ, winStep]
  | succ m ih =>
    intro f
    have h := ih (fun i => f (i + 1))
    rw [List.range_succ_eq_map, List.map_cons, List.map_map] at h ⊢
    rw [List.range_succ_eq_map, List.map_cons, List.map_map]
    rw [List.range_succ_eq_map, List.map_cons, List.map_map] at h
    rw [List.range_succ_eq_map, List.map_cons, List.map_map]
    simp only [winStep, Function.comp_def] at h ⊢
    rw [h, List.map_cons, List.map_map]
    rfl

/-- Read the middle cell, step the window, repeat: the centre column. -/
def colGo (r : ℕ) : ℕ → ℕ → List Bool → List Bool
  | 0, i, l => [l.getD i false]
  | k + 1, i, l => l.getD i false :: colGo r k (i - 1) (winStep r l)

theorem colGo_spec (r : ℕ) (x : Config) : ∀ (k m i : ℕ), k ≤ i →
    colGo r k i ((List.range (2 * i + 1)).map fun j : ℕ => ecaEvolve r x m (-(i : ℤ) + (j : ℤ))) =
      (List.range (k + 1)).map fun j => ecaEvolve r x (m + j) 0 := by
  intro k
  induction k with
  | zero =>
    intro m i _
    simp [colGo, List.getD_eq_getElem?_getD, List.getElem?_range (show i < 2 * i + 1 by omega)]
  | succ k ih =>
    intro m i hk
    obtain ⟨i, rfl⟩ : ∃ i', i = i' + 1 := ⟨i - 1, by omega⟩
    have hw := winStep_map r (2 * i + 1)
      (fun j : ℕ => ecaEvolve r x m (-((i + 1 : ℕ) : ℤ) + (j : ℤ)))
    rw [show 2 * i + 1 + 2 = 2 * (i + 1) + 1 by ring] at hw
    simp only [colGo]
    rw [hw, show i + 1 - 1 = i by omega]
    have : (List.range (2 * i + 1)).map (fun j : ℕ =>
        ecaRule r (ecaEvolve r x m (-((i + 1 : ℕ) : ℤ) + (j : ℤ)))
          (ecaEvolve r x m (-((i + 1 : ℕ) : ℤ) + ((j + 1 : ℕ) : ℤ)))
          (ecaEvolve r x m (-((i + 1 : ℕ) : ℤ) + ((j + 2 : ℕ) : ℤ)))) =
        (List.range (2 * i + 1)).map fun j : ℕ => ecaEvolve r x (m + 1) (-(i : ℤ) + (j : ℤ)) := by
      apply List.map_congr_left
      intro j _
      rw [ecaEvolve_succ]
      congr 1 <;> [congr 1; congr 1; skip] <;> push_cast <;> ring_nf
    rw [this, ih (m + 1) i (by omega), List.range_succ_eq_map (n := k + 1), List.map_cons,
      List.map_map]
    congr 1
    · simp [List.getD_eq_getElem?_getD]; congr 1; ring
    · apply List.map_congr_left; intro j _; simp; ring_nf

/-- The first `N + 1` centre-column values of wheel `r` on the impulse row, by the window
simulator. -/
def centreList (r N : ℕ) : List Bool :=
  colGo r N N ((List.range (2 * N + 1)).map fun j : ℕ => seed (-(N : ℤ) + (j : ℤ)))

/-- **Soundness of the simulator.** -/
theorem centreList_spec (r N : ℕ) :
    centreList r N = (List.range (N + 1)).map (ecaColumn r seed 0) := by
  have := colGo_spec r seed N 0 N le_rfl
  simpa [centreList, ecaColumn] using this

theorem centreList_getD (r N i : ℕ) (hi : i ≤ N) :
    (centreList r N).toArray.getD i false = ecaColumn r seed 0 i := by
  rw [centreList_spec]
  simp [Array.getD, List.getElem_range, show i < N + 1 by omega]

/-- The finite test: every `p ∈ [1, P]` is broken at some time `n ∈ [N, N + M)`. -/
def noPeriodCheck (l : Array Bool) (P N M : ℕ) : Bool :=
  (List.range' 1 P).all fun p => (List.range' N M).any fun n =>
    l.getD (n + p) false != l.getD n false

/-- The four OR-type wheels pass the test with `P = N = M = 500` on the first 1501 values. -/
theorem orType_check :
    ∀ r ∈ [30, 45, 75, 135], noPeriodCheck (centreList r 1500).toArray 500 500 500 = true := by
  native_decide

/-- **Finite evidence for the OR-type class.** For each of the four wheels `L xor h(C, R)` with
`h` of OR type (30, 45, 75, 135), the centre column on the impulse row has no eventual period
`p ≤ 500` that starts at or before time `500`. -/
theorem orType_no_small_period (h : BinGate) (hh : IsOrType h) (p N : ℕ) (hp : 1 ≤ p)
    (hp' : p ≤ 500) (hN : N ≤ 500) :
    ¬ ∀ n ≥ N, ecaColumn (innerRule h) seed 0 (n + p) = ecaColumn (innerRule h) seed 0 n := by
  have hr := (innerRule_orType h).1 hh
  have hr' : innerRule h ∈ [30, 45, 75, 135] := by
    simp only [Finset.mem_insert, Finset.mem_singleton] at hr
    simp only [List.mem_cons, List.not_mem_nil, or_false]
    exact hr
  have hc := orType_check _ hr'
  simp only [noPeriodCheck, List.all_eq_true, List.any_eq_true] at hc
  obtain ⟨n, hn, hne⟩ := hc p (List.mem_range'_1.mpr ⟨hp, by omega⟩)
  obtain ⟨hn1, hn2⟩ := List.mem_range'_1.mp hn
  intro hper
  rw [centreList_getD _ _ _ (by omega), centreList_getD _ _ _ (by omega)] at hne
  simp [hper n (by omega)] at hne

/-! ## Round 24 collected -/

/-- **Round 24 frontier.** (1) Every gate other than XOR in `g(L, C or R)` gives an eventually
periodic centre column. (2) Every non-OR-type gate in `L xor h(C, R)` does too. (3) The exact
counting law holds for every `L xor h(C, R)`. (4) It holds for all times for Rule 86, the mirror
of Rule 30, (5) but not for Rule 30 at the edge. (6) The four OR-type wheels have no eventual
period `p ≤ 500` from time `≤ 500`. (7) The Hankel form of Problem 1 is exact. -/
theorem frontier_round24 :
    (∀ g : BinGate, g ≠ (fun a b => xor a b) →
      EventuallyPeriodic (ecaColumn (outerRule g) seed 0)) ∧
    (∀ h : BinGate, ¬ IsOrType h → EventuallyPeriodic (ecaColumn (innerRule h) seed 0)) ∧
    (∀ (h : BinGate) (p d T : ℕ), 1 ≤ p → p ≤ T + 1 → T < d →
      RunCountW (innerRule h) p d T = 2 ^ (d + p - 1)) ∧
    (∀ d T : ℕ, 1 ≤ T → RunCountW 86 2 d T = 2 ^ (d + 1)) ∧
    RunCountW 30 2 3 3 = 20 ∧
    (∀ h : BinGate, IsOrType h → ∀ p N : ℕ, 1 ≤ p → p ≤ 500 → N ≤ 500 →
      ¬ ∀ n ≥ N, ecaColumn (innerRule h) seed 0 (n + p) = ecaColumn (innerRule h) seed 0 n) ∧
    Problem1IffHankelInfinitelyOften :=
  ⟨outer_alternative_periodic, inner_alternative_periodic,
    fun h p d T hp hpT hTd => innerRule_runCount_law h p d T hp hpT hTd,
    runCountW_eightySix, runCountW_thirty_edge,
    fun h hh p N hp hp' hN => orType_no_small_period h hh p N hp hp' hN,
    problem1IffHankelInfinitelyOften⟩

end GLM.Rule30
