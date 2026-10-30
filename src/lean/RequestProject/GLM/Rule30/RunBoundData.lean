import RequestProject.GLM.Rule30.LeftWhiteLift
import RequestProject.GLM.Rule30.Compute

/-!
# Round 13: the period-2 run bound, checked for small distances

`LeftWhiteLift.lean` reduces Problem 1 to run bounds for left-white rows.  Period 1 is proved for
all distances.  Period 2 is the first open case.  This file checks it **exhaustively** for every
left-white row and every distance `d ≤ 7` from the edge.

* `runCheck p d L` — a computable test: no left-white row has its column at distance `d`
  `p`-periodic on the time window `[0, L]`.  `runCheck_sound` proves that the test means this, for
  **every** left-white row (the column only depends on `d + L + 1` cells right of the edge).
* `runBound_two_upTo_seven` (`CERT`) — for every left-white row and every `d ≤ 7`, a column at
  distance `d` stays 2-periodic for at most `B₂ d` steps, with `B₂ = 1, 7, 6, 5, 5, 8, 9, 9`.
* `runBound_two_sharp` (`CERT`) — each of these bounds is attained by some left-white row.
* `runBound_one_sharp_upTo_seven` (`CERT`) — for period 1 the exact bound is `d + 1` for `d ≤ 7`
  (the proved general bound is `3d + 5`).
* `runBound_small_periods` (`CERT`) — exact run bounds for periods `3, …, 6` at distances
  `d ≤ 4`.

These checks are about all left-white rows, not about the seed alone.  For the seed they only cover
the first eight rows of the stack, so they are evidence for the period-2 run bound, not a proof.
-/

namespace GLM.Rule30

/-- The cells `x ℓ, …, x (ℓ + K - 1)` as the bits of a natural number. -/
def encodeWin (x : Config) (ℓ : ℤ) : ℕ → ℕ
  | 0 => 0
  | K + 1 => encodeWin x ℓ K ||| ((x (ℓ + K)).toNat <<< K)

theorem testBit_encodeWin (x : Config) (ℓ : ℤ) (K k : ℕ) :
    (encodeWin x ℓ K).testBit k = (decide (k < K) && x (ℓ + k)) := by
  induction K with
  | zero => simp [encodeWin]
  | succ K ih =>
    simp only [encodeWin, Nat.testBit_or, ih, Nat.testBit_shiftLeft]
    rcases lt_trichotomy k K with h | h | h
    · simp [h, show k < K + 1 by omega, show ¬ K ≤ k by omega]
    · subst h; cases x (ℓ + k) <;> simp
    · simp only [show ¬ k < K by omega, show ¬ k < K + 1 by omega, decide_false,
        Bool.false_and, Bool.false_or, Bool.and_eq_false_imp, decide_eq_true_eq]
      intro _
      obtain ⟨j, hj⟩ : ∃ j, k - K = j + 1 := ⟨k - K - 1, by omega⟩
      rw [hj]; cases x (ℓ + K) <;> simp [Nat.testBit_succ]

theorem encodeWin_lt (x : Config) (ℓ : ℤ) (K : ℕ) : encodeWin x ℓ K < 2 ^ K :=
  Nat.lt_pow_two_of_testBit _ fun i hi => by simp [testBit_encodeWin]; omega

/-- Near the column, a left-white row agrees with its encoded window. -/
theorem evolve_eq_encodeWin (x : Config) (ℓ : ℤ) (hw : ∀ j, j < ℓ → x j = false)
    (K t d : ℕ) (h : d + t < K) :
    evolve x t (ℓ + d) = evolve (maskConfig 0 (encodeWin x ℓ K)) t d := by
  rw [show ℓ + (d : ℤ) = (d : ℤ) + ℓ by ring, ← evolve_shift]
  apply evolve_congr
  intro j h1 h2
  simp only [maskConfig, CharP.cast_eq_zero, add_zero]
  by_cases hj : 0 ≤ j
  · rw [if_pos hj, testBit_encodeWin, decide_eq_true (by omega), Bool.true_and]
    congr 1; omega
  · rw [if_neg hj]; exact hw _ (by omega)

theorem evolve_maskConfig_fast (m t d : ℕ) :
    evolve (maskConfig 0 m) t d = (rowStep^[t] m).testBit (d + t) := by
  rw [testBit_rowStep_iterate 0 m t (d + t)]
  congr 1; push_cast; ring

/-- Computable test: for every encoded left-white window (bit `0` set), the column at distance
`d` is **not** `p`-periodic on `[0, L]`. -/
def runCheck (p d L : ℕ) : Bool :=
  (List.range (2 ^ (d + L + 1))).all fun m =>
    !(m.testBit 0) ||
      !((List.range (L + 1 - p)).all fun t =>
        (rowStep^[t + p] m).testBit (d + t + p) == (rowStep^[t] m).testBit (d + t))

/-- **Soundness of the test**, for every left-white row. -/
theorem runCheck_sound {p d L : ℕ} (hc : runCheck p d L = true) (x : Config) (ℓ : ℤ)
    (hw : ∀ j, j < ℓ → x j = false) (hb : x ℓ = true) :
    ¬ ∀ t, t + p ≤ L → evolve x (t + p) (ℓ + d) = evolve x t (ℓ + d) := by
  intro hrun
  set m := encodeWin x ℓ (d + L + 1)
  have hm : m < 2 ^ (d + L + 1) := encodeWin_lt x ℓ _
  have h0 : m.testBit 0 = true := by
    simp only [m, testBit_encodeWin]; simpa using hb
  have := List.all_eq_true.mp hc m (List.mem_range.mpr hm)
  rw [h0] at this
  simp only [Bool.not_true, Bool.false_or, Bool.not_eq_eq_eq_not, List.all_eq_false,
    List.mem_range] at this
  obtain ⟨t, ht, hne⟩ := this
  apply hne
  have e1 := evolve_eq_encodeWin x ℓ hw (d + L + 1) (t + p) d (by omega)
  have e2 := evolve_eq_encodeWin x ℓ hw (d + L + 1) t d (by omega)
  rw [evolve_maskConfig_fast] at e1 e2
  rw [show d + t + p = d + (t + p) by ring, ← e1, ← e2]
  exact beq_iff_eq.mpr (hrun t (by omega))

/-- A failed test produces a left-white row with a `p`-periodic run of length `L`. -/
theorem exists_run_of_runCheck_false {p d L : ℕ} (hc : runCheck p d L = false) :
    ∃ x : Config, (∀ j, j < 0 → x j = false) ∧ x 0 = true ∧
      ∀ t, t + p ≤ L → evolve x (t + p) (0 + d) = evolve x t (0 + d) := by
  unfold runCheck at hc
  rw [List.all_eq_false] at hc
  obtain ⟨m, -, hm⟩ := hc
  rw [Bool.not_eq_true, Bool.or_eq_false_iff, Bool.not_eq_false', Bool.not_eq_false',
    List.all_eq_true] at hm
  obtain ⟨h0, hall'⟩ := hm
  have hall : ∀ t, t < L + 1 - p →
      (rowStep^[t + p] m).testBit (d + t + p) = (rowStep^[t] m).testBit (d + t) :=
    fun t ht => beq_iff_eq.mp (hall' t (List.mem_range.mpr ht))
  refine ⟨maskConfig 0 m, maskConfig_white 0 m, by simpa [maskConfig] using h0, fun t ht => ?_⟩
  rw [zero_add, evolve_maskConfig_fast, evolve_maskConfig_fast,
    show d + (t + p) = d + t + p by ring]
  exact hall t (by omega)

/-- Run bounds for the distances `d ≤ D` only. -/
def RunBoundUpTo (p : ℕ) (B : ℕ → ℕ) (D : ℕ) : Prop :=
  ∀ (x : Config) (ℓ : ℤ), (∀ j, j < ℓ → x j = false) → x ℓ = true →
    ∀ d L : ℕ, d ≤ D → (∀ t, t + p ≤ L → evolve x (t + p) (ℓ + d) = evolve x t (ℓ + d)) → L ≤ B d

theorem runBoundUpTo_of_checks {p D : ℕ} {B : ℕ → ℕ}
    (hc : ∀ d ≤ D, runCheck p d (B d + 1) = true) : RunBoundUpTo p B D := by
  intro x ℓ hw hb d L hd hrun
  by_contra hL
  exact runCheck_sound (hc d hd) x ℓ hw hb fun t ht => hrun t (by omega)

/-- The exact period-2 run bounds for `d = 0, …, 7`. -/
def runBoundTwo (d : ℕ) : ℕ := [1, 7, 6, 5, 5, 8, 9, 9].getD d 0

theorem runCheck_two_upTo_seven : ∀ d ≤ 7, runCheck 2 d (runBoundTwo d + 1) = true := by
  native_decide

/-- **Period-2 run bound for `d ≤ 7` (`CERT`).** In every left-white row, the column at distance
`d ≤ 7` from the edge stays 2-periodic for at most `runBoundTwo d` steps. -/
theorem runBound_two_upTo_seven : RunBoundUpTo 2 runBoundTwo 7 :=
  runBoundUpTo_of_checks runCheck_two_upTo_seven

theorem runCheck_two_sharp : ∀ d ≤ 7, runCheck 2 d (runBoundTwo d) = false := by
  native_decide

/-- **The period-2 bounds are exact (`CERT`):** for each `d ≤ 7` some left-white row has a
2-periodic run of length `runBoundTwo d` at distance `d`. -/
theorem runBound_two_sharp (d : ℕ) (hd : d ≤ 7) :
    ∃ x : Config, (∀ j, j < 0 → x j = false) ∧ x 0 = true ∧
      ∀ t, t + 2 ≤ runBoundTwo d → evolve x (t + 2) (0 + d) = evolve x t (0 + d) :=
  exists_run_of_runCheck_false (runCheck_two_sharp d hd)

theorem runCheck_one_upTo_seven : ∀ d ≤ 7, runCheck 1 d (d + 2) = true ∧ runCheck 1 d (d + 1) = false := by
  native_decide

/-- **Period 1, exact for `d ≤ 7` (`CERT`):** a column at distance `d` is constant for at most
`d + 1` steps, and this is attained. -/
theorem runBound_one_sharp_upTo_seven :
    RunBoundUpTo 1 (fun d => d + 1) 7 ∧
      ∀ d : ℕ, d ≤ 7 → ∃ x : Config, (∀ j, j < 0 → x j = false) ∧ x 0 = true ∧
        ∀ t, t + 1 ≤ d + 1 → evolve x (t + 1) (0 + (d : ℤ)) = evolve x t (0 + (d : ℤ)) :=
  ⟨runBoundUpTo_of_checks fun d hd => (runCheck_one_upTo_seven d hd).1,
    fun d hd => exists_run_of_runCheck_false (runCheck_one_upTo_seven d hd).2⟩

/-- Exact run bounds for periods `3, …, 6` and distances `d ≤ 4` (computed outside Lean, checked
below). -/
def runBoundSmall (p d : ℕ) : ℕ :=
  ([[4, 7, 9, 8, 8], [7, 7, 9, 9, 10], [5, 10, 9, 9, 10], [6, 14, 13, 13, 12]].getD (p - 3) []).getD d 0

theorem runCheck_small_periods :
    ∀ p ∈ [3, 4, 5, 6], ∀ d ≤ 4, runCheck p d (runBoundSmall p d + 1) = true := by
  native_decide

/-- **Run bounds for periods `3, …, 6` at distances `d ≤ 4` (`CERT`).** -/
theorem runBound_small_periods (p : ℕ) (hp : p ∈ [3, 4, 5, 6]) :
    RunBoundUpTo p (runBoundSmall p) 4 :=
  runBoundUpTo_of_checks fun d hd => runCheck_small_periods p hp d hd

end GLM.Rule30
