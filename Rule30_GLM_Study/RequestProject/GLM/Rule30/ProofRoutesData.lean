import RequestProject.GLM.Rule30.ProofRoutes
import RequestProject.GLM.Rule30.ConjectureLoopData

/-!
# Round 27 certificates: witnesses, refuted progress measures, refuted width steps

(Not a `module`: the checks use `native_decide`.)  Everything here is about the period-2 drive
word `10` (`driveN 2 1`, black at even times), which by `halfLineDies_two_iff` is the whole
period-2 rung.  The searches that produced the tables are `scripts/post_edge_witnesses.py` and
`scripts/progress_measures.py` (EMP); this file checks their output.

## 1. The longest survivors (Experiment A), `d ≤ 32`

`lmaxTwo` lists, for every code length `d ≤ 32`, the exact longest life `Lmax d` (first failure
time) and one code achieving it.  `lmaxTwo_spec`: every code of length `d` fails at some time
`≤ Lmax d`, and the listed code first fails exactly at `Lmax d`.  The sequence is not monotone
(`Lmax 11 = 30 > Lmax 12 = 16`), and its jumps are irregular (`Lmax 30 = 52`, `Lmax 31 = 66`).

## 2. Declared progress measures (Experiment B): all refuted

`rankPot i` for `i < 8` is the declared family: width, number of black cells, number of
adjacent changes, trailing black run at the column, first adjacent white pair, number of white
cells, black cells in the original-width window, length of the alternating block at the column.
**`no_declared_ranking`**: none of them is a ranking for any window `1 ≤ c ≤ 20` and any initial
bound `f`.  Each refutation is one surviving post-edge window across which the measure does not
drop (`rankWitness`, smallest counterexamples in the search order of the script).

## 3. Width steps (Experiment C, width-induction route)

**`not_widthStep_two`**: `WidthStep (driveN 2 1) b` is false for every `b ≤ 17`.  Every code of
length 29 fails by time 48, but a code of length 31 survives to time 66.

## 4. A shared inner survivor (the sound form of width reduction, observed)

**`shared_inner_survivor`**: the longest survivors of lengths 11 (code `1493`) and 19 (code
`382293`) both carry, from time 6 to time 19, an inner column that alternates (black at odd
times), at depth 6 and 14 respectively, and the cells beyond it are the **same** inner code
`1601` in both.  That inner code, driven by the word `01`, first fails at time 13
(`inner_alternation_bound` explains why the inner columns can follow the drive that long and no
longer).

`witnesses_merge`: the two longest survivors of length 11 (`1493`, `1507`) have the same state
from time 2 on.  Longest survivors often coincide as trajectories (the driven step is not
injective), so a list of witnesses can contain fewer mechanisms than codes.

## 5. The surviving candidate and the open statement

`frontier_round27` collects the round.  Of the four routes, the population route is the only one
with a surviving uniform candidate: **`Round27Open := AmortizedHalving 2 4 1`**, which implies
the period-2 rung (`halfLineDies_of_amortized`).  It is **OPEN**; it is certified for every
`d ≤ 12` (`amortizedHalvingUpTo_2_4_1`), so the smallest unresolved case is `d = 13`.
-/

namespace GLM.Rule30

/-! ## 1. Longest survivors -/

/-- `(d, Lmax d, witness)` for the drive word `10`, `d = 1 … 32` (from `scripts/`). -/
def lmaxTwo : List (ℕ × ℕ × ℕ) :=
  [(1, 2, 1), (2, 6, 3), (3, 4, 5), (4, 6, 11), (5, 8, 29), (6, 10, 43), (7, 12, 67), (8, 10, 253), (9, 18, 331), (10, 14, 853), (11, 30, 1493), (12, 16, 2379), (13, 28, 6581), (14, 32, 11165), (15, 26, 25853), (16, 30, 52149), (17, 30, 84821), (18, 30, 218453), (19, 38, 382293), (20, 30, 607133), (21, 36, 1684821), (22, 40, 2858293), (23, 40, 4463957), (24, 42, 15780693), (25, 44, 17445931), (26, 44, 60061981), (27, 48, 133420373), (28, 48, 164963797), (29, 48, 319789493), (30, 52, 725829429), (31, 66, 1314727381), (32, 54, 3527253301)]

/-- The check of one row: the witness has length `d`, first fails exactly at `L`, and the prefix
search shows every code of length `d` fails before `L + 1`. -/
def lmaxEntryCheck (d L S : ℕ) : Bool :=
  decide (1 ≤ d) && decide (2 ^ (d - 1) ≤ S) && decide (S < 2 ^ d) &&
    !dDiesBy (driveN 2 1) S L && dDiesBy (driveN 2 1) S (L + 1) &&
    prefixSearch (driveN 2 1) (L + 1) (d - 1) 0 0

theorem lmaxTwo_check : lmaxTwo.all (fun e => lmaxEntryCheck e.1 e.2.1 e.2.2) = true := by
  native_decide

/-- **Exact longest life for every `d ≤ 32`.** -/
theorem lmaxTwo_spec : ∀ e ∈ lmaxTwo,
    (∀ S, 2 ^ (e.1 - 1) ≤ S → S < 2 ^ e.1 → dDiesBy (driveN 2 1) S (e.2.1 + 1) = true) ∧
    (2 ^ (e.1 - 1) ≤ e.2.2 ∧ e.2.2 < 2 ^ e.1 ∧ dDiesBy (driveN 2 1) e.2.2 e.2.1 = false ∧
      dDiesBy (driveN 2 1) e.2.2 (e.2.1 + 1) = true) := by
  intro e he
  have h := List.all_eq_true.1 lmaxTwo_check e he
  simp only [lmaxEntryCheck, Bool.and_eq_true, decide_eq_true_eq, Bool.not_eq_true'] at h
  obtain ⟨⟨⟨⟨⟨hd, h1⟩, h2⟩, hL⟩, hL1⟩, hP⟩ := h
  exact ⟨fun S a b => dDiesBy_of_prefixSearch hd hP a b, h1, h2, hL, hL1⟩

/-- Survival is inherited by earlier horizons. -/
theorem dDiesBy_false_of_le {bd : ℕ → Bool} {S T T' : ℕ} (h : dDiesBy bd S T = false)
    (hT : T' ≤ T) : dDiesBy bd S T' = false := by
  cases h' : dDiesBy bd S T'
  · rfl
  · rw [dDiesBy_mono h' hT] at h; exact h

/-! ## 2. Declared progress measures -/

/-- Number of cells of a state (`0` for the empty state). -/
def bitLen (X : ℕ) : ℕ := if X = 0 then 0 else Nat.log2 X + 1

/-- Number of black cells. -/
def popcount (X : ℕ) : ℕ := ((List.range (bitLen X)).filter (X.testBit ·)).length

/-- First index `< n` satisfying `p` (or `n`). -/
def firstIdx (p : ℕ → Bool) (n : ℕ) : ℕ := (List.range n).findIdx p

/-- **The declared family of progress measures** (state `X`, time `t`):
`0` width, `1` black cells, `2` adjacent changes, `3` black run at the column,
`4` first adjacent white pair, `5` white cells, `6` black cells in the original-width window,
`7` (and above) length of the alternating block at the column. -/
def rankPot : ℕ → ℕ → ℕ → ℕ
  | 0, X, _ => bitLen X
  | 1, X, _ => popcount X
  | 2, X, _ => popcount (X ^^^ (X >>> 1))
  | 3, X, _ => firstIdx (fun i => !X.testBit i) (bitLen X + 1)
  | 4, X, _ => firstIdx (fun i => !X.testBit i && !X.testBit (i + 1)) (bitLen X + 1)
  | 5, X, _ => bitLen X - popcount X
  | 6, X, t => popcount (X % 2 ^ (bitLen X - t))
  | _, X, _ => firstIdx (fun n => decide (1 ≤ n) && X.testBit n == X.testBit (n - 1)) (bitLen X + 2)

/-- One refuting window: a code of length `d`, alive through `t + c` with `t` after the edge,
across which `P` does not drop. -/
def rankWindowCheck (P : ℕ → ℕ → ℕ) (c d S t : ℕ) : Bool :=
  decide (1 ≤ d) && decide (2 ^ (d - 1) ≤ S) && decide (S < 2 ^ d) && decide (d - 1 ≤ t) &&
    !dDiesBy (driveN 2 1) S (t + c) &&
    decide (P (halfStateD (driveN 2 1) S t) t ≤ P (halfStateD (driveN 2 1) S (t + c)) (t + c))

theorem not_ranking_of_check {P : ℕ → ℕ → ℕ} {c d S t : ℕ} (h : rankWindowCheck P c d S t = true)
    (f : ℕ → ℕ) : ¬ Ranking (driveN 2 1) P c f := by
  simp only [rankWindowCheck, Bool.and_eq_true, decide_eq_true_eq, Bool.not_eq_true'] at h
  obtain ⟨⟨⟨⟨⟨hd, h1⟩, h2⟩, ht⟩, hs⟩, hP⟩ := h
  exact not_ranking_of_window f hd h1 h2 ht hs hP

/-- The smallest counterexamples `(i, c, d, S, t)` found by `scripts/progress_measures.py`. -/
def rankWitness : List (ℕ × ℕ × ℕ × ℕ × ℕ) :=
  [(0, 1, 1, 1, 0),
   (0, 2, 1, 1, 0),
   (0, 3, 2, 3, 1),
   (0, 4, 2, 3, 1),
   (0, 5, 2, 3, 1),
   (0, 6, 7, 67, 6),
   (0, 7, 9, 285, 8),
   (0, 8, 9, 285, 8),
   (0, 9, 9, 331, 8),
   (0, 10, 9, 331, 8),
   (0, 11, 11, 1493, 10),
   (0, 12, 11, 1493, 10),
   (0, 13, 11, 1493, 10),
   (0, 14, 11, 1493, 10),
   (0, 15, 11, 1493, 10),
   (0, 16, 11, 1493, 10),
   (0, 17, 11, 1493, 10),
   (0, 18, 11, 1493, 10),
   (0, 19, 11, 1493, 10),
   (0, 20, 11, 1493, 10),
   (1, 1, 1, 1, 0),
   (1, 2, 1, 1, 0),
   (1, 3, 2, 3, 1),
   (1, 4, 2, 3, 1),
   (1, 5, 2, 3, 1),
   (1, 6, 7, 67, 6),
   (1, 7, 9, 285, 8),
   (1, 8, 9, 285, 8),
   (1, 9, 9, 331, 8),
   (1, 10, 9, 331, 8),
   (1, 11, 11, 1493, 10),
   (1, 12, 11, 1493, 10),
   (1, 13, 11, 1493, 10),
   (1, 14, 11, 1493, 10),
   (1, 15, 11, 1493, 10),
   (1, 16, 11, 1493, 10),
   (1, 17, 11, 1493, 10),
   (1, 18, 11, 1493, 10),
   (1, 19, 11, 1493, 10),
   (1, 20, 11, 1493, 10),
   (2, 1, 1, 1, 0),
   (2, 2, 1, 1, 0),
   (2, 3, 2, 3, 1),
   (2, 4, 2, 3, 1),
   (2, 5, 2, 3, 1),
   (2, 6, 7, 67, 6),
   (2, 7, 9, 285, 8),
   (2, 8, 9, 285, 8),
   (2, 9, 9, 331, 8),
   (2, 10, 9, 331, 8),
   (2, 11, 11, 1493, 10),
   (2, 12, 11, 1493, 10),
   (2, 13, 11, 1493, 10),
   (2, 14, 11, 1493, 10),
   (2, 15, 11, 1493, 10),
   (2, 16, 11, 1493, 10),
   (2, 17, 11, 1493, 10),
   (2, 18, 11, 1493, 10),
   (2, 19, 11, 1493, 10),
   (2, 20, 11, 1493, 10),
   (3, 1, 1, 1, 0),
   (3, 2, 2, 3, 1),
   (3, 3, 2, 3, 1),
   (3, 4, 2, 3, 1),
   (3, 5, 2, 3, 1),
   (3, 6, 9, 285, 8),
   (3, 7, 9, 285, 8),
   (3, 8, 9, 331, 8),
   (3, 9, 9, 331, 9),
   (3, 10, 11, 1493, 11),
   (3, 11, 11, 1493, 11),
   (3, 12, 11, 1493, 10),
   (3, 13, 11, 1493, 11),
   (3, 14, 11, 1493, 11),
   (3, 15, 11, 1493, 11),
   (3, 16, 11, 1493, 10),
   (3, 17, 11, 1493, 11),
   (3, 18, 11, 1493, 10),
   (3, 19, 11, 1493, 11),
   (3, 20, 27, 133420373, 26),
   (4, 1, 1, 1, 0),
   (4, 2, 1, 1, 0),
   (4, 3, 2, 3, 1),
   (4, 4, 2, 3, 2),
   (4, 5, 2, 3, 1),
   (4, 6, 7, 67, 6),
   (4, 7, 9, 285, 8),
   (4, 8, 9, 331, 10),
   (4, 9, 9, 331, 9),
   (4, 10, 9, 331, 8),
   (4, 11, 11, 1493, 12),
   (4, 12, 11, 1493, 12),
   (4, 13, 11, 1493, 11),
   (4, 14, 11, 1493, 10),
   (4, 15, 11, 1493, 12),
   (4, 16, 11, 1493, 10),
   (4, 17, 11, 1493, 13),
   (4, 18, 11, 1493, 12),
   (4, 19, 14, 11083, 13),
   (4, 20, 11, 1493, 10),
   (5, 1, 1, 1, 0),
   (5, 2, 1, 1, 0),
   (5, 3, 2, 3, 1),
   (5, 4, 2, 3, 1),
   (5, 5, 2, 3, 1),
   (5, 6, 7, 67, 6),
   (5, 7, 9, 285, 9),
   (5, 8, 9, 285, 8),
   (5, 9, 9, 331, 8),
   (5, 10, 9, 331, 8),
   (5, 11, 11, 1493, 10),
   (5, 12, 11, 1493, 10),
   (5, 13, 11, 1493, 10),
   (5, 14, 11, 1493, 10),
   (5, 15, 11, 1493, 10),
   (5, 16, 11, 1493, 10),
   (5, 17, 11, 1493, 10),
   (5, 18, 11, 1493, 10),
   (5, 19, 11, 1493, 10),
   (5, 20, 11, 1493, 10),
   (6, 1, 1, 1, 0),
   (6, 2, 2, 3, 1),
   (6, 3, 2, 3, 1),
   (6, 4, 2, 3, 2),
   (6, 5, 2, 3, 1),
   (6, 6, 7, 67, 6),
   (6, 7, 9, 285, 8),
   (6, 8, 9, 331, 10),
   (6, 9, 9, 331, 9),
   (6, 10, 9, 331, 8),
   (6, 11, 11, 1493, 12),
   (6, 12, 11, 1493, 10),
   (6, 13, 11, 1493, 10),
   (6, 14, 11, 1493, 10),
   (6, 15, 11, 1493, 11),
   (6, 16, 11, 1493, 10),
   (6, 17, 11, 1493, 12),
   (6, 18, 11, 1493, 12),
   (6, 19, 11, 1493, 10),
   (6, 20, 11, 1493, 10),
   (7, 1, 1, 1, 1),
   (7, 2, 1, 1, 0),
   (7, 3, 2, 3, 3),
   (7, 4, 5, 29, 4),
   (7, 5, 2, 3, 1),
   (7, 6, 7, 67, 6),
   (7, 7, 9, 331, 8),
   (7, 8, 9, 331, 8),
   (7, 9, 9, 331, 8),
   (7, 10, 9, 331, 8),
   (7, 11, 11, 1493, 10),
   (7, 12, 11, 1493, 10),
   (7, 13, 11, 1493, 10),
   (7, 14, 11, 1493, 10),
   (7, 15, 11, 1493, 10),
   (7, 16, 11, 1493, 10),
   (7, 17, 11, 1493, 10),
   (7, 18, 11, 1493, 10),
   (7, 19, 11, 1493, 10),
   (7, 20, 11, 1493, 10)]

/-- Every measure `i < 8` and every window `1 ≤ c ≤ 20` has a checked refuting window. -/
def rankTableCheck : Bool :=
  (List.range 8).all fun i => (List.range 20).all fun c' =>
    rankWitness.any fun w =>
      w.1 == i && w.2.1 == c' + 1 && rankWindowCheck (rankPot i) (c' + 1) w.2.2.1 w.2.2.2.1 w.2.2.2.2

theorem rankTableCheck_eq : rankTableCheck = true := by native_decide

/-- **No declared progress measure is a ranking**, for any window `1 ≤ c ≤ 20` and any bound. -/
theorem no_declared_ranking : ∀ i < 8, ∀ c, 1 ≤ c → c ≤ 20 → ∀ f : ℕ → ℕ,
    ¬ Ranking (driveN 2 1) (rankPot i) c f := by
  intro i hi c hc1 hc2 f
  have h := List.all_eq_true.1 rankTableCheck_eq i (List.mem_range.2 hi)
  have h' := List.all_eq_true.1 h (c - 1) (List.mem_range.2 (by omega))
  obtain ⟨w, -, hw⟩ := List.any_eq_true.1 h'
  simp only [Bool.and_eq_true, beq_iff_eq] at hw
  obtain ⟨⟨-, hc⟩, hw⟩ := hw
  rw [show c - 1 + 1 = c by omega] at hw
  exact not_ranking_of_check hw f

/-! ## 3. Width steps -/

/-- **No width step of size `≤ 17`.** All codes of length 29 fail by time 48; the code
`1314727381` of length 31 survives to time 66. -/
theorem not_widthStep_two {b : ℕ} (hb : b ≤ 17) : ¬ WidthStep (driveN 2 1) b := by
  have h29 : ∀ S, 2 ^ (29 - 1) ≤ S → S < 2 ^ 29 → dDiesBy (driveN 2 1) S (48 + 1) = true :=
    (lmaxTwo_spec (29, 48, 319789493) (by simp [lmaxTwo])).1
  have h31 : dDiesBy (driveN 2 1) 1314727381 66 = false :=
    (lmaxTwo_spec (31, 66, 1314727381) (by simp [lmaxTwo])).2.2.2.1
  exact not_widthStep_of_witness (d := 29) (T := 49) (by norm_num) h29 (by norm_num)
    (by norm_num) (dDiesBy_false_of_le h31 (by omega))

/-! ## 4. A shared inner survivor -/

/-- **The longest survivors of lengths 11 and 19 share an inner survivor.** -/
theorem shared_inner_survivor :
    halfStateD (driveN 2 1) 1493 6 >>> 6 = 1601 ∧
    halfStateD (driveN 2 1) 382293 6 >>> 14 = 1601 ∧
    (∀ u ≤ 13, innerCol (driveN 2 1) 1493 6 (u + 6) = driveN 2 2 u) ∧
    (∀ u ≤ 13, innerCol (driveN 2 1) 382293 14 (u + 6) = driveN 2 2 u) ∧
    innerCol (driveN 2 1) 1493 6 20 ≠ driveN 2 2 14 ∧
    innerCol (driveN 2 1) 382293 14 20 ≠ driveN 2 2 14 ∧
    dDiesBy (driveN 2 2) 1601 13 = false ∧ dDiesBy (driveN 2 2) 1601 14 = true := by
  native_decide

/-- **Two longest survivors of length 11 are one trajectory from time 2 on.** -/
theorem witnesses_merge :
    (1493 : ℕ) ≠ 1507 ∧ halfStateD (driveN 2 1) 1493 2 = halfStateD (driveN 2 1) 1507 2 := by
  native_decide

/-! ## 5. The open statement and the round's frontier -/

/-- **OPEN (Round 27).** The surviving uniform candidate: amortised halving with `c = 4`,
`e = 1` for period 2.  Smallest unresolved case: `d = 13`. -/
def Round27Open : Prop := AmortizedHalving 2 4 1

/-- **Round 27 frontier.** -/
theorem frontier_round27 :
    -- the transition specification: no state repeats, no fixed window is closed
    (∀ (bd : ℕ → Bool) S, 0 < S → StrictMono (halfStateD bd S)) ∧
    (∀ (b : Bool) w, 1 ≤ w → halfStep b 0 % 2 ^ w ≠ halfStep b (2 ^ w) % 2 ^ w) ∧
    -- inner columns: the inner machine driven by its own column never fails
    (∀ (bd : ℕ → Bool) S k T, 1 ≤ k → dDiesBy (innerCol bd S k) (S >>> k) T = false) ∧
    -- ranking route: no declared measure works for windows up to 20
    (∀ i < 8, ∀ c, 1 ≤ c → c ≤ 20 → ∀ f, ¬ Ranking (driveN 2 1) (rankPot i) c f) ∧
    -- width-induction route: no width step of size at most 17
    (∀ b ≤ 17, ¬ WidthStep (driveN 2 1) b) ∧
    -- population route: the surviving candidate implies the rung, certified to d = 12
    (Round27Open → HalfLineDies 2) ∧ AmortizedHalvingUpTo 2 4 1 12 :=
  ⟨fun bd _ hS => halfStateD_strictMono bd hS,
   fun b _ hw => (window_not_closed b hw).2,
   fun bd S _ T hk => inner_never_fails bd S hk T,
   no_declared_ranking,
   fun _ hb => not_widthStep_two hb,
   fun h => halfLineDies_of_amortized (by norm_num) h,
   amortizedHalvingUpTo_2_4_1⟩

end GLM.Rule30
