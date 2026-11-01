module

public import RequestProject.GLM.Rule30.SidewaysView

/-!
# Round 33, To Do 29 (partly): the sideways reader for period 2, first columns in closed form

*Last altered 31 October 2026 (restored: this is the Round 33 file, claim C318, that the Rule 30
round built and checked but could not deliver; it is restored unchanged against the same
`SidewaysView.lean`).*

By `halfLineDies_two_iff` only the drive word `10` (`driveN 2 1`: black at even times) matters
for period 2, and by `halfLineDies_iff_sideways` the rung is a statement about the sideways
reconstruction `recon (driveN 2 1) u` for admissible first columns `u`.  Admissibility fixes
`u (2 s) = 1` and leaves one free bit `a s = u (2 s + 1)` per period.

This file computes the first columns of the reconstruction exactly in terms of the free bits
(the observer standing on the column and reading outwards):

| column | even time `2 s` | odd time `2 s + 1` |
|---|---|---|
| 1 (`u`) | `1` | `a s` |
| 2 | `¬ a s` | `¬ a s` |
| 3 | `a s` | `a (s + 1)` |
| 4 | `¬ a (s + 1)` | `a (s + 1) xor (a (s + 1) ∨ ¬ a s)` |
| 5 | `a s` | — |

So column 2 repeats each free bit twice (the sideways form of the half-speed reduction
`alt_left_determined`), column 3 is column 2 negated and read half a period later, and column 5
returns to the free bit at even times.  From column 4 on the columns are genuinely nonlinear in
the free bits (their algebraic degree grows, `scripts/sideways_period_two.py`, EMP).

**Consequence (FORMAL, `survivor_bits_period_two`).**  A code that survives the drive `10`
forever has bit `0` black, bit `2 = ¬` bit `1`, and bit `4 =` bit `2`: the first five cells next to
the column carry only two free bits.  (Consistent with the exact pre-edge count `survivors_card`.)
-/

@[expose] public section

namespace GLM.Rule30

namespace SidewaysTwo

/-- The drive `10`. -/
abbrev bd2 : ℕ → Bool := driveN 2 1

theorem bd2_even (s : ℕ) : bd2 (2 * s) = true := by
  simp [bd2, driveN, Nat.mul_mod_right]

theorem bd2_odd (s : ℕ) : bd2 (2 * s + 1) = false := by
  simp [bd2, driveN, Nat.add_mod, Nat.mul_mod_right]
  decide

variable {u : ℕ → Bool}

/-- Admissible first columns are black at even times. -/
theorem u_even (hu : Admissible bd2 u) (s : ℕ) : u (2 * s) = true := by
  have := hu (2 * s) (bd2_even s)
  rw [bd2_odd] at this
  simpa using this

/-- The free bit of the period `s`. -/
def a (u : ℕ → Bool) (s : ℕ) : Bool := u (2 * s + 1)

theorem col2_even (hu : Admissible bd2 u) (s : ℕ) : recon bd2 u 2 (2 * s) = !a u s := by
  show xor (u (2 * s + 1)) (u (2 * s) || bd2 (2 * s)) = _
  rw [u_even hu, bd2_even]; simp [a]

theorem col2_odd (hu : Admissible bd2 u) (s : ℕ) : recon bd2 u 2 (2 * s + 1) = !a u s := by
  show xor (u (2 * s + 1 + 1)) (u (2 * s + 1) || bd2 (2 * s + 1)) = _
  rw [show 2 * s + 1 + 1 = 2 * (s + 1) by ring, u_even hu, bd2_odd]; simp [a]

theorem col3_even (hu : Admissible bd2 u) (s : ℕ) : recon bd2 u 3 (2 * s) = a u s := by
  show xor (recon bd2 u 2 (2 * s + 1)) (recon bd2 u 2 (2 * s) || recon bd2 u 1 (2 * s)) = _
  rw [col2_odd hu, col2_even hu]
  show xor _ (_ || u (2 * s)) = _
  rw [u_even hu]; simp

theorem col3_odd (hu : Admissible bd2 u) (s : ℕ) : recon bd2 u 3 (2 * s + 1) = a u (s + 1) := by
  show xor (recon bd2 u 2 (2 * s + 1 + 1))
    (recon bd2 u 2 (2 * s + 1) || recon bd2 u 1 (2 * s + 1)) = _
  rw [show 2 * s + 1 + 1 = 2 * (s + 1) by ring, col2_even hu, col2_odd hu]
  show xor _ (_ || u (2 * s + 1)) = _
  cases a u (s + 1) <;> cases h : u (2 * s + 1) <;> simp [a, h]

theorem col4_even (hu : Admissible bd2 u) (s : ℕ) : recon bd2 u 4 (2 * s) = !a u (s + 1) := by
  show xor (recon bd2 u 3 (2 * s + 1)) (recon bd2 u 3 (2 * s) || recon bd2 u 2 (2 * s)) = _
  rw [col3_odd hu, col3_even hu, col2_even hu]
  cases a u s <;> simp

theorem col4_odd (hu : Admissible bd2 u) (s : ℕ) :
    recon bd2 u 4 (2 * s + 1) = xor (a u (s + 1)) (a u (s + 1) || !a u s) := by
  show xor (recon bd2 u 3 (2 * s + 1 + 1))
    (recon bd2 u 3 (2 * s + 1) || recon bd2 u 2 (2 * s + 1)) = _
  rw [show 2 * s + 1 + 1 = 2 * (s + 1) by ring, col3_even hu, col3_odd hu, col2_odd hu]

theorem col5_even (hu : Admissible bd2 u) (s : ℕ) : recon bd2 u 5 (2 * s) = a u s := by
  show xor (recon bd2 u 4 (2 * s + 1)) (recon bd2 u 4 (2 * s) || recon bd2 u 3 (2 * s)) = _
  rw [col4_odd hu, col4_even hu, col3_even hu]
  cases a u s <;> cases a u (s + 1) <;> rfl

/-- **The first five cells of a period-2 survivor.**  If the code `S` survives the drive `10`
forever, then bit `0` is black, bit `2` is the negation of bit `1`, and bit `4` equals bit `2`. -/
theorem survivor_bits_period_two {S : ℕ} (h : SurvivesForever bd2 S) :
    S.testBit 0 = true ∧ S.testBit 2 = !S.testBit 1 ∧ S.testBit 4 = S.testBit 2 := by
  obtain ⟨u, hu, hrow⟩ := (survives_iff_sideways bd2 S).1 h
  have h0 := hrow 0
  have h1 := hrow 1
  have h2 := hrow 2
  have h4 := hrow 4
  have e1 : recon bd2 u (0 + 1) 0 = true := by
    show u (2 * 0) = true; exact u_even hu 0
  have e2 : recon bd2 u (1 + 1) 0 = !a u 0 := col2_even hu 0
  have e3 : recon bd2 u (2 + 1) 0 = a u 0 := col3_even hu 0
  have e5 : recon bd2 u (4 + 1) 0 = a u 0 := col5_even hu 0
  rw [h0, h1, h2, h4, e1, e2, e3, e5]
  simp

end SidewaysTwo

end GLM.Rule30
