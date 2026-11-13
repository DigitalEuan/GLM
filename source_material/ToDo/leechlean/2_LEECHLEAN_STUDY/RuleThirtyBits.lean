module

public import Mathlib

/-!
# Rule 30 on a row of bits: the step the hypothesis engine computes

*Created 1 November 2026 (Phase 186: the intake of `source_material/ToDo/Rule30_GLM_Study`,
directive D22; a standalone check, written for the absorption ahead of the owner's build).*

The hypothesis engine (`glm_universal.reasoning.hypothesis_engine`) keeps a row of Rule 30 as the
bits of one natural number and advances it with `new = (x << 1) ^ (x | (x >> 1))`. This file proves
that this one line is Rule 30:

* `rule30_wolfram` — the local rule `l xor (c or r)` is the rule numbered 30 (bit `4l + 2c + r` of
  the number 30), checked on all eight neighbourhoods;
* `testBit_step_zero`, `testBit_step_succ` — bit `i + 1` of `step x` is the local rule applied to
  bits `i`, `i + 1`, `i + 2` of `x` (so bit `j` holds the cell in column `j - W` and its left
  neighbour is bit `j - 1`, the engine's convention);
* `centreBits_64` — the first 64 cells of the centre column from one black cell, the list the
  engine's `centre_bits(64)` returns (`tests/test_hypothesis_engine.py` compares the two);
* `centreBits_64_ones` — 35 of those 64 cells are black.

Everything is formal (`decide`, `simp`; no `native_decide`).
-/

@[expose] public section

namespace GLM.IntakeChecks.RuleThirtyBits

/-- The local rule of Rule 30: the new cell is `left xor (centre or right)`. -/
def rule30 (l c r : Bool) : Bool := l ^^ (c || r)

/-- The local rule is Wolfram's rule 30: the new cell is bit `4l + 2c + r` of `30`. -/
theorem rule30_wolfram (l c r : Bool) :
    rule30 l c r = Nat.testBit 30 (4 * l.toNat + 2 * c.toNat + r.toNat) := by
  cases l <;> cases c <;> cases r <;> decide

/-- One Rule 30 step on a row kept as the bits of a natural number (the engine's
`rule30_step`). -/
def step (x : ℕ) : ℕ := (x <<< 1) ^^^ (x ||| (x >>> 1))

/-- Bit `0` of a step: nothing lies to its left. -/
theorem testBit_step_zero (x : ℕ) : (step x).testBit 0 = (x.testBit 0 || x.testBit 1) := by
  rw [step, Nat.testBit_xor, Nat.testBit_or, Nat.testBit_shiftRight, Nat.testBit_shiftLeft]
  simp

/-- Bit `i + 1` of a step is Rule 30 applied to bits `i` (left), `i + 1` (centre) and `i + 2`
(right) of the row. -/
theorem testBit_step_succ (x i : ℕ) :
    (step x).testBit (i + 1) = rule30 (x.testBit i) (x.testBit (i + 1)) (x.testBit (i + 2)) := by
  rw [step, Nat.testBit_xor, Nat.testBit_or, Nat.testBit_shiftRight, Nat.testBit_shiftLeft,
    show 1 + (i + 1) = i + 2 by omega]
  simp [rule30]

/-- `t` steps from the row `x`. -/
def evolve (x : ℕ) : ℕ → ℕ
  | 0 => x
  | t + 1 => step (evolve x t)

/-- The first `n` cells of the centre column from one black cell, read at bit `n + 2` of a row
started as `1 <<< (n + 2)` (the engine's `centre_bits(n)`: the margin keeps the spreading pattern
clear of bit `0` for the `n` steps read). -/
def centreBits (n : ℕ) : List Bool :=
  (List.range n).map fun t => (evolve (1 <<< (n + 2)) t).testBit (n + 2)

/-- The first 64 cells of Rule 30's centre column. -/
theorem centreBits_64 : centreBits 64 =
    [true, true, false, true, true, true, false, false, true, true, false, false, false, true,
     false, true, true, false, false, true, false, false, true, true, true, false, true, false,
     true, true, true, false, false, true, true, true, false, true, false, true, false, true,
     true, false, false, false, false, true, true, false, false, true, false, true, false, true,
     true, false, true, false, true, false, true, true] := by
  decide

/-- 35 of the first 64 centre cells are black. -/
theorem centreBits_64_ones : (centreBits 64).count true = 35 := by
  rw [centreBits_64]; decide

end GLM.IntakeChecks.RuleThirtyBits
