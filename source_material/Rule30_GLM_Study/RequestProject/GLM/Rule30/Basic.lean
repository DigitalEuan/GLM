module

public import Mathlib

/-!
# Rule 30: basic definitions

We model an elementary cellular automaton on the integer line `ℤ` with cells in `Bool`
(`true` = black).  Rule 30 is the local rule `f(L, C, R) = L xor (C or R)`.

* `rule30 L C R`           — the local rule.
* `step x`                 — one synchronous update of the whole line.
* `evolve x n c`           — the cell at position `c` after `n` steps, starting from row `x`.
* `seed`                   — the single black cell at the origin (Wolfram's initial condition).
* `centerCol n`            — the centre column `a(n) = evolve seed n 0` (OEIS A051023).

Main facts proved here:
* `rule30_eq_truthTable` : the closed form agrees with Wolfram's numbering (30 = 0b00011110).
* `evolve_congr`         : *light-cone locality* — `evolve x n c` only depends on `x` on `[c-n, c+n]`.
* `evolve_shift`         : translation invariance.
* `evolve_seed_outside`  : for the seed, cells outside the light cone `|c| ≤ n` are white.
* `evolve_seed_left_edge`: for the seed, the left edge `c = -n` is always black.
-/

@[expose] public section

namespace GLM.Rule30

/-- The Rule 30 local rule: `L xor (C or R)`. -/
def rule30 (L C R : Bool) : Bool := xor L (C || R)

/-- Wolfram's numbering: output for pattern `4L + 2C + R` is bit `4L+2C+R` of `30`. -/
def truthTable (L C R : Bool) : Bool :=
  Nat.testBit 30 (4 * L.toNat + 2 * C.toNat + R.toNat)

theorem rule30_eq_truthTable (L C R : Bool) : rule30 L C R = truthTable L C R := by
  cases L <;> cases C <;> cases R <;> decide

/-- Over `GF(2)` the rule is the polynomial `L + C + R + C·R`. -/
theorem rule30_zmod (L C R : Bool) :
    ((rule30 L C R).toNat : ZMod 2) =
      (L.toNat : ZMod 2) + C.toNat + R.toNat + C.toNat * R.toNat := by
  cases L <;> cases C <;> cases R <;> decide

/-- A row of the automaton: a configuration of the whole integer line. -/
abbrev Config := ℤ → Bool

/-- One synchronous Rule 30 update. -/
def step (x : Config) : Config := fun c => rule30 (x (c - 1)) (x c) (x (c + 1))

/-- `evolve x n` is the row after `n` steps starting from `x`. -/
def evolve (x : Config) : ℕ → Config
  | 0 => x
  | n + 1 => step (evolve x n)

@[simp] theorem evolve_zero (x : Config) : evolve x 0 = x := rfl

theorem evolve_succ (x : Config) (n : ℕ) (c : ℤ) :
    evolve x (n + 1) c =
      rule30 (evolve x n (c - 1)) (evolve x n c) (evolve x n (c + 1)) := rfl

/-- Evolving `n` steps and then one more step. -/
theorem evolve_succ' (x : Config) (n : ℕ) : evolve x (n + 1) = evolve (step x) n := by
  induction n with
  | zero => rfl
  | succ n ih => exact congrArg step ih

/-- The single black cell at the origin. -/
def seed : Config := fun c => decide (c = 0)

/-- The centre column `a(n)` of Rule 30 started from a single black cell. -/
def centerCol (n : ℕ) : Bool := evolve seed n 0

/-! ## Light-cone locality -/

/-- **Light-cone locality.** If two rows agree on `[c - n, c + n]`, then the cells at
position `c` after `n` steps agree. -/
theorem evolve_congr (x y : Config) (n : ℕ) (c : ℤ)
    (h : ∀ j, c - n ≤ j → j ≤ c + n → x j = y j) : evolve x n c = evolve y n c := by
  induction n generalizing c with
  | zero => exact h c (by simp) (by simp)
  | succ n ih =>
    rw [evolve_succ, evolve_succ,
      ih (c - 1) (fun j h1 h2 => h j (by push_cast at *; omega) (by push_cast at *; omega)),
      ih c (fun j h1 h2 => h j (by push_cast at *; omega) (by push_cast at *; omega)),
      ih (c + 1) (fun j h1 h2 => h j (by push_cast at *; omega) (by push_cast at *; omega))]

/-- Translation invariance. -/
theorem evolve_shift (x : Config) (d : ℤ) (n : ℕ) (c : ℤ) :
    evolve (fun j => x (j + d)) n c = evolve x n (c + d) := by
  induction n generalizing c with
  | zero => rfl
  | succ n ih =>
    rw [evolve_succ, evolve_succ, ih, ih, ih]
    congr 2 <;> ring_nf

/-- The all-white row is a fixed point. -/
theorem evolve_false (n : ℕ) (c : ℤ) : evolve (fun _ => false) n c = false := by
  induction n generalizing c with
  | zero => rfl
  | succ n ih => simp [evolve_succ, ih, rule30]

/-! ## The seed: light cone and left edge -/

/-- More generally: if `x` is white on `(-∞, ℓ)` then after `n` steps the row is white on
`(-∞, ℓ - n)`. -/
theorem evolve_white_left (x : Config) (ℓ : ℤ) (hx : ∀ j, j < ℓ → x j = false) (n : ℕ) :
    ∀ c, c < ℓ - n → evolve x n c = false := by
  induction n with
  | zero => intro c hc; exact hx c (by simpa using hc)
  | succ n ih =>
    intro c hc
    rw [evolve_succ, ih (c - 1) (by push_cast at *; omega), ih c (by push_cast at *; omega),
      ih (c + 1) (by push_cast at *; omega)]
    rfl

/-- If `x` is white on `(-∞, ℓ)` and black at `ℓ`, then after `n` steps the cell `ℓ - n`
is black: the left edge of the pattern moves left at the speed of light. -/
theorem evolve_left_edge (x : Config) (ℓ : ℤ) (hx : ∀ j, j < ℓ → x j = false)
    (hℓ : x ℓ = true) (n : ℕ) : evolve x n (ℓ - n) = true := by
  induction n with
  | zero => simpa using hℓ
  | succ n ih =>
    rw [evolve_succ, evolve_white_left x ℓ hx n _ (by push_cast; omega),
      evolve_white_left x ℓ hx n _ (by push_cast; omega)]
    have : (ℓ - ((n + 1 : ℕ) : ℤ) + 1) = ℓ - n := by push_cast; ring
    rw [this, ih]; rfl

/-- If `x` is white on `(r, ∞)` then after `n` steps the row is white on `(r + n, ∞)`. -/
theorem evolve_white_right (x : Config) (r : ℤ) (hx : ∀ j, r < j → x j = false) (n : ℕ) :
    ∀ c, r + n < c → evolve x n c = false := by
  induction n with
  | zero => intro c hc; exact hx c (by simpa using hc)
  | succ n ih =>
    intro c hc
    rw [evolve_succ, ih (c - 1) (by push_cast at *; omega), ih c (by push_cast at *; omega),
      ih (c + 1) (by push_cast at *; omega)]
    rfl

theorem evolve_seed_outside (n : ℕ) (c : ℤ) (hc : (n : ℤ) < |c|) : evolve seed n c = false := by
  rcases lt_abs.mp hc with h | h
  · exact evolve_white_right seed 0 (fun j hj => by simp [seed]; omega) n c (by omega)
  · exact evolve_white_left seed 0 (fun j hj => by simp [seed]; omega) n c (by omega)

theorem evolve_seed_left_edge (n : ℕ) : evolve seed n (-n) = true := by
  have := evolve_left_edge seed 0 (fun j hj => by simp [seed]; omega) (by simp [seed]) n
  simpa using this

end GLM.Rule30
