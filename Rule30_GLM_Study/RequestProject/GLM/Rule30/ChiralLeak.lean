import RequestProject.GLM.Rule30.Observer
import RequestProject.GLM.Rule30.OnePeriodicColumn
import RequestProject.GLM.Rule30.Compute
import RequestProject.GLM.Rule30.Diagonals

/-!
# The off-centre observer: where chirality enters the wobble

Round 11, track B.  The centre observer cannot tell wheel 30 from its mirror image, wheel 86
(`centre_column_class`).  An observer at column `c` sees, by the mirror symmetry, what an observer
of wheel 86 sees at column `−c`.  So the difference that chirality makes to the wobble at column
`c` is measured **inside Rule 30 alone** by

  `chiralGap c N = D_c(N) − D_{−c}(N)`,

the wobble at column `c` minus the wobble at the mirror column.

* `wobble_mirror_column` : the wobble of wheel 86 at column `c` equals the wobble of wheel 30 at
  column `−c`; so `chiralGap c N` is also "wheel 30 minus wheel 86, both read at column `c`"
  (`chiralGap_eq_thirty_sub_eightySix`).
* `chiralGap_centre`, `chiralGap_neg` : the gap vanishes identically at the centre and is odd in
  `c`.
* `chiralGap_first` : **chirality enters the wobble at once off-centre**: for `c = 1, …, 5` the
  gap is zero up to `N = 2, 5, 4, 8, 6` and non-zero at `N = 3, 6, 5, 9, 7` respectively.
* `rdiag_moving_frame` : the observer riding the right edge (depth coordinates) sees wheel `86`,
  the mirror image of 30, with its frame moving one cell per step.
* `offCentre_pair_problem1` : the strongest Problem-1 statement available for observers: of the
  two observers at columns `0` and `c ≠ 0`, at least one sees a column that is not eventually
  periodic (`seed_at_most_one_periodic_column`).  Problem 1 asks for this at the centre.

`EMP` (outside Lean, `rule30_round11/r11_offcentre_wobble.c`): to `N = 10⁶` the gaps behave like
the difference of two random walks.  `max |chiralGap c N|` over `N ≤ 10⁶` is
`886, 1170, 1754, 1924, 2918` for `c = 1, …, 5`, with no drift.  The leak of chirality into the
wobble is immediate and of the same `√N` order as the wobble itself; it does not grow linearly.
-/

namespace GLM.Rule30

/-- The chirality signal in the wobble at column `c`: the wobble at `c` minus the wobble at the
mirror column `−c`, both for Rule 30 from the impulse. -/
def chiralGap (c : ℤ) (N : ℕ) : ℤ :=
  wobble (ecaColumn 30 seed c) N - wobble (ecaColumn 30 seed (-c)) N

/-- The mirror image's wobble at column `c` is Rule 30's wobble at column `−c`. -/
theorem wobble_mirror_column (c : ℤ) (N : ℕ) :
    wobble (ecaColumn 86 seed c) N = wobble (ecaColumn 30 seed (-c)) N := by
  have := ecaColumn_mirror 30 seed (-c)
  rw [seed_mirror, mirrorNum_thirty, neg_neg] at this
  rw [this]

/-- The gap is "wheel 30 minus its mirror image wheel 86", both observed at column `c`. -/
theorem chiralGap_eq_thirty_sub_eightySix (c : ℤ) (N : ℕ) :
    chiralGap c N = wobble (ecaColumn 30 seed c) N - wobble (ecaColumn 86 seed c) N := by
  rw [chiralGap, wobble_mirror_column]

/-- At the centre the gap vanishes identically: the centre is blind to chirality. -/
theorem chiralGap_centre (N : ℕ) : chiralGap 0 N = 0 := by
  simp [chiralGap]

/-- The gap is odd in the column. -/
theorem chiralGap_neg (c : ℤ) (N : ℕ) : chiralGap (-c) N = - chiralGap c N := by
  simp [chiralGap]

/-- The wobble of the first `N` values of a column, read off the window computation. -/
theorem wobble_eq_window (r : ℕ) (x : Config) (c : ℤ) (N : ℕ) :
    wobble (ecaColumn r x c) N = 2 * ((windowColumn r x c N).count true : ℤ) - N := by
  rw [wobble, ones_eq_count, windowColumn_eq]

/-- The chirality gap, computed on finite windows. -/
theorem chiralGap_eq_window (c : ℤ) (N : ℕ) :
    chiralGap c N = 2 * ((windowColumn 30 seed c N).count true : ℤ)
      - 2 * ((windowColumn 30 seed (-c) N).count true : ℤ) := by
  rw [chiralGap, wobble_eq_window, wobble_eq_window]; ring

private theorem gap_check :
    (List.map (fun N => chiralGap 1 N) (List.range 4) = [0, 0, 0, -2]) ∧
    (List.map (fun N => chiralGap 2 N) (List.range 7) = [0, 0, 0, 0, 0, 0, -2]) ∧
    (List.map (fun N => chiralGap 3 N) (List.range 6) = [0, 0, 0, 0, 0, -2]) ∧
    (List.map (fun N => chiralGap 4 N) (List.range 10) = [0, 0, 0, 0, 0, 0, 0, 0, 0, -2]) ∧
    (List.map (fun N => chiralGap 5 N) (List.range 8) = [0, 0, 0, 0, 0, 0, 0, -2]) := by
  simp only [chiralGap_eq_window]
  decide +kernel

/-- **Chirality enters the wobble immediately off-centre.**  For `c = 1, …, 5` the gap
`D_c(N) − D_{−c}(N)` is zero for `N < N_c` and non-zero at `N_c`, where
`N_c = 3, 6, 5, 9, 7`. -/
theorem chiralGap_first :
    (∀ N < 3, chiralGap 1 N = 0) ∧ chiralGap 1 3 ≠ 0 ∧
    (∀ N < 6, chiralGap 2 N = 0) ∧ chiralGap 2 6 ≠ 0 ∧
    (∀ N < 5, chiralGap 3 N = 0) ∧ chiralGap 3 5 ≠ 0 ∧
    (∀ N < 9, chiralGap 4 N = 0) ∧ chiralGap 4 9 ≠ 0 ∧
    (∀ N < 7, chiralGap 5 N = 0) ∧ chiralGap 5 7 ≠ 0 := by
  obtain ⟨h1, h2, h3, h4, h5⟩ := gap_check
  have get : ∀ (c : ℤ) (K : ℕ) (l : List ℤ), List.map (fun N => chiralGap c N) (List.range K) = l →
      ∀ N < K, chiralGap c N = l.getD N 0 := by
    intro c K l h N hN
    rw [← h, List.getD_eq_getElem _ _ (by simpa using hN)]
    simp
  refine ⟨fun N hN => ?_, ?_, fun N hN => ?_, ?_, fun N hN => ?_, ?_, fun N hN => ?_, ?_,
    fun N hN => ?_, ?_⟩
  · rw [get 1 4 _ h1 N (by omega)]; interval_cases N <;> rfl
  · rw [get 1 4 _ h1 3 (by omega)]; decide
  · rw [get 2 7 _ h2 N (by omega)]; interval_cases N <;> rfl
  · rw [get 2 7 _ h2 6 (by omega)]; decide
  · rw [get 3 6 _ h3 N (by omega)]; interval_cases N <;> rfl
  · rw [get 3 6 _ h3 5 (by omega)]; decide
  · rw [get 4 10 _ h4 N (by omega)]; interval_cases N <;> rfl
  · rw [get 4 10 _ h4 9 (by omega)]; decide
  · rw [get 5 8 _ h5 N (by omega)]; interval_cases N <;> rfl
  · rw [get 5 8 _ h5 7 (by omega)]; decide

/-- **The off-centre pair always sees aperiodicity.** For every column `c ≠ 0`, at least one of
the two observers at columns `0` and `c` reads a sequence that is not eventually periodic.
Problem 1 is the statement that the centre observer is always such an observer. -/
theorem offCentre_pair_problem1 {c : ℤ} (hc : c ≠ 0) :
    ¬ EventuallyPeriodic centerCol ∨ ¬ EventuallyPeriodic (fun t => evolve seed t c) := by
  by_contra h
  push_neg at h
  exact hc (seed_at_most_one_periodic_column h.2 h.1)

/-! ## The observer riding the right edge sees the mirror wheel, moving -/

/-- **The right-edge frame.**  Read in the frame that rides the right edge of the light cone
(cell `t − D` at time `t`, indexed by the depth `D`), Rule 30 is wheel `86`, its mirror image,
with the frame moving by one cell per step: the new value at depth `D` is wheel 86 applied to the
depths `(D − 2, D − 1, D)`.  So the perspective of the observer changes both the wheel it sees
(30 ↦ 86) and its velocity. -/
theorem rdiag_moving_frame (D : ℤ) (t : ℕ) :
    rdiag D (t + 1) = ecaRule 86 (rdiag (D - 2) t) (rdiag (D - 1) t) (rdiag D t) := by
  rw [← mirrorNum_thirty, ecaRule_mirrorNum, ecaRule_30, rdiag_succ]
  simp only [rule30]

end GLM.Rule30
