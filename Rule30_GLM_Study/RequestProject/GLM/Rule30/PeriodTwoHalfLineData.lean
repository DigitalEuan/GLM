import RequestProject.GLM.Rule30.PeriodTwoHalfLine
import RequestProject.GLM.Rule30.RunBoundSearch

/-!
# Round 21: finite certificates for the one-sided period-2 target

The half-line machine of `PeriodTwoHalfLine.lean` needs no cells to the right of the column, so a
certificate for distance `d` enumerates only the `2^(d-1)` codes of the `d` cells between the edge
and the column.  The older certificates (`RunBoundSearch.lean`, `RunBoundEighteen.lean`) had to
search the cells to the right as well.

* `halfBound d` — the largest time at which some code of length `d` first fails the check
  (maximum over both phases), for `1 ≤ d ≤ 24`.
* `halfCheck_upTo_24` (`CERT`) — every code of length `d ≤ 24` fails by time `halfBound d`.
* `halfBound_sharp` (`CERT`) — for each `d`, some code survives up to `halfBound d - 1`: the values
  are exact **for the machine**.
* **`altRunBound_upTo_24`** (`CERT`) — in every left-white row, a column at distance `d ≤ 24` from
  the edge that alternates on `[0, L]` has `L ≤ halfBound d`.  This extends the certified range of
  the period-2 rung (for alternating runs) from `d ≤ 18` to `d ≤ 24`.
* `runBound_two_upTo_24` (`CERT`) — with the proved constant-run bound `3d + 5`, every period-2
  run (constant or alternating) at distance `d ≤ 24` has `L ≤ max (3d + 5) (halfBound d)`.
* `halfBound_le_linear` — all certified values satisfy `halfBound d ≤ 2d + 8`.
* `PeriodTwoHalfLineLinear` — the one-sided linear target (every code of length `d` fails by time
  `2d + 8`); `leftWhiteAperiodic_two_of_halfLineLinear` — it implies the period-2 rung.

Caution: the machine ignores the cells right of the column, so its bounds are **upper bounds**
for the real runs and are larger than the exact real values (e.g. `d = 11`: machine `30`, real
`13`).  In particular the machine does **not** satisfy `2d + 7` (`d = 11`), so the one-sided
linear target uses `2d + 8`.
-/

namespace GLM.Rule30

/-- The exact machine bounds for `d = 1, …, 24` (entry `0` is unused). -/
def halfBound (d : ℕ) : ℕ :=
  [0, 7, 6, 5, 6, 9, 10, 12, 17, 18, 17, 30, 29, 28, 32, 31, 30, 31, 33, 38, 37, 36, 41, 43,
    42].getD d 0

theorem halfCheck_upTo_twelve : ∀ d ≤ 12, 1 ≤ d → halfCheck d (halfBound d + 1) = true := by
  native_decide

theorem halfCheck_thirteen_to_eighteen :
    ∀ d ≤ 18, 13 ≤ d → halfCheck d (halfBound d + 1) = true := by
  native_decide

theorem halfCheck_nineteen_to_twentyone :
    ∀ d ≤ 21, 19 ≤ d → halfCheck d (halfBound d + 1) = true := by
  native_decide

theorem halfCheck_twentytwo : halfCheck 22 (halfBound 22 + 1) = true := by native_decide

theorem halfCheck_twentythree : halfCheck 23 (halfBound 23 + 1) = true := by native_decide

theorem halfCheck_twentyfour : halfCheck 24 (halfBound 24 + 1) = true := by native_decide

/-- **Every half-line code of length `d ≤ 24` fails the check by time `halfBound d`** (`CERT`). -/
theorem halfCheck_upTo_24 : ∀ d ≤ 24, 1 ≤ d → halfCheck d (halfBound d + 1) = true := by
  intro d hd h1
  rcases Nat.lt_or_ge d 13 with h | h
  · exact halfCheck_upTo_twelve d (by omega) h1
  rcases Nat.lt_or_ge d 19 with h' | h'
  · exact halfCheck_thirteen_to_eighteen d (by omega) h
  rcases Nat.lt_or_ge d 22 with h'' | h''
  · exact halfCheck_nineteen_to_twentyone d (by omega) h'
  interval_cases d
  · exact halfCheck_twentytwo
  · exact halfCheck_twentythree
  · exact halfCheck_twentyfour

/-- **The machine bounds are exact** (`CERT`): for each `1 ≤ d ≤ 24` some code has not failed
before time `halfBound d`. -/
theorem halfBound_sharp : ∀ d ≤ 24, 1 ≤ d → halfCheck d (halfBound d) = false := by
  native_decide

/-- **Alternating period-2 runs, `d ≤ 24`** (`CERT`). -/
theorem altRunBound_upTo_24 : AltRunBoundUpTo halfBound 24 :=
  altRunBoundUpTo_of_halfCheck halfCheck_upTo_24

/-- **All period-2 runs, `d ≤ 24`** (`CERT`): constant runs by the proved bound `3d + 5`,
alternating runs by the machine certificate. -/
theorem runBound_two_upTo_24 :
    RunBoundUpTo 2 (fun d => max (3 * d + 5) (halfBound d)) 24 := by
  intro x ℓ hw hb d L hd hrun
  by_cases hne : evolve x 1 (ℓ + d) ≠ evolve x 0 (ℓ + d)
  · exact le_trans (altRunBound_upTo_24 x ℓ hw hb d L hd hrun hne) (le_max_right _ _)
  · push_neg at hne
    refine le_trans (runBound_one x ℓ hw hb d L fun t ht => ?_) (le_max_left _ _)
    have hev : ∀ s, s ≤ L → evolve x s (ℓ + d) = evolve x 0 (ℓ + d) := by
      intro s
      induction s using Nat.strong_induction_on with
      | _ s ih =>
        intro hs
        match s, ih with
        | 0, _ => rfl
        | 1, _ => exact hne
        | s + 2, ih => rw [hrun s (by omega), ih s (by omega) (by omega)]
    rw [hev (t + 1) (by omega), hev t (by omega)]

/-- All certified machine bounds are at most `2d + 8`. -/
theorem halfBound_le_linear : ∀ d ≤ 24, 1 ≤ d → halfBound d ≤ 2 * d + 8 := by decide

/-! ## The one-sided linear target -/

/-- **One-sided linear target for period 2.** Every half-line code `S` whose top cell is at
position `d - 1` (i.e. `2^(d-1) ≤ S < 2^d`) fails the check by time `2d + 8`, in both phases. -/
def PeriodTwoHalfLineLinear : Prop :=
  ∀ d S : ℕ, 2 ^ (d - 1) ≤ S → S < 2 ^ d → 1 ≤ d → ∀ φ : ℕ, φ = 0 ∨ φ = 1 →
    halfDiesBy S φ (2 * d + 9) = true

theorem halfLineDies_of_halfLineLinear (h : PeriodTwoHalfLineLinear) : PeriodTwoHalfLineDies := by
  intro S hS φ hφ
  refine ⟨_, h (Nat.log 2 S + 1) S ?_ ?_ (by omega) φ hφ⟩
  · simpa using Nat.pow_log_le_self 2 hS.ne'
  · exact Nat.lt_pow_succ_log_self (by norm_num) S

/-- **The one-sided linear target implies the period-2 rung.** -/
theorem leftWhiteAperiodic_two_of_halfLineLinear (h : PeriodTwoHalfLineLinear) :
    LeftWhiteAperiodic 2 :=
  leftWhiteAperiodic_two_of_halfLineDies (halfLineDies_of_halfLineLinear h)

/-- The one-sided linear target holds for all `d ≤ 24` (`CERT`). -/
theorem halfLineLinear_upTo_24 : ∀ d S : ℕ, d ≤ 24 → 2 ^ (d - 1) ≤ S → S < 2 ^ d → 1 ≤ d →
    ∀ φ : ℕ, φ = 0 ∨ φ = 1 → halfDiesBy S φ (2 * d + 9) = true := by
  intro d S hd h1 h2 hd1 φ hφ
  exact halfDiesBy_mono (halfDiesBy_of_halfCheck (halfCheck_upTo_24 d hd hd1) hd1 h1 h2 φ hφ)
    (by have := halfBound_le_linear d hd hd1; omega)

end GLM.Rule30
