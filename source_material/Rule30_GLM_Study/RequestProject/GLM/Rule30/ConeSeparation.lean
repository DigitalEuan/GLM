module

public import RequestProject.GLM.Rule30.Basic

/-!
# Cone separation (Target 1) and the chirality of Rule 30

This file proves, for **every** starting row (not only the single-cell seed) and every `n`:

* `evolve_flip_left_edge` / `booleanDerivative_left_edge` (**cone separation**):
  flipping the leftmost cell `x_{c-n}` of the light cone always flips the cell `(n, c)`,
  i.e. `∂ a(n)(c) / ∂ x_{c-n} = 1` identically.
* `cone_separation_decomposition`: `a(n)(c) = x_{c-n} xor g(x)` where `g` does not
  depend on `x_{c-n}` at all.
* `booleanDerivative_right_edge` (**right-edge derivative formula**, new):
  `∂ a(n)(c) / ∂ x_{c+n} = ∏_{k<n} ¬ a(k)(c+n-1-k)`: the rightmost variable matters exactly
  when the diagonal just inside the right edge of the light cone is entirely white.
* `columns_determine_left`: two adjacent columns determine every column to their left
  (the "reading direction" of Rule 30).
* `left_wall_stationary`, `right_side_not_recoverable`: the converse fails — information
  from the right can be completely hidden from all columns to its left.
* `rule30_left_permutive`, `rule30_not_right_permutive`, `rule30_ne_mirror`: the local rule
  is chiral (its mirror image is Rule 86).
-/

@[expose] public section

namespace GLM.Rule30

/-! ## Local chirality of the rule -/

/-- Rule 30 is *left-permutive*: flipping the left input always flips the output. -/
theorem rule30_left_permutive (L C R : Bool) : rule30 (!L) C R = !rule30 L C R := by
  cases L <;> cases C <;> cases R <;> rfl

/-- Rule 30 is *not* right-permutive: with `C = 1` the right input is invisible. -/
theorem rule30_not_right_permutive : ∃ L C R : Bool, rule30 L C (!R) = rule30 L C R :=
  ⟨false, true, false, rfl⟩

/-- The left input can always be recovered from the output and the other two inputs. -/
theorem rule30_solve_left (L C R : Bool) : L = xor (rule30 L C R) (C || R) := by
  cases L <;> cases C <;> cases R <;> rfl

/-- The mirror image of Rule 30 (`L ↔ R`) is Rule 86, a different rule. -/
theorem rule30_mirror_eq_rule86 (L C R : Bool) :
    rule30 R C L = Nat.testBit 86 (4 * L.toNat + 2 * C.toNat + R.toNat) := by
  cases L <;> cases C <;> cases R <;> decide

theorem rule30_ne_mirror : ∃ L C R : Bool, rule30 L C R ≠ rule30 R C L :=
  ⟨true, true, false, by decide⟩

/-! ## Boolean derivatives -/

/-- The Boolean derivative of `f` with respect to the variable `x_i`:
`(∂f/∂x_i)(x) = f(x with x_i := 1) xor f(x with x_i := 0)`. -/
def booleanDerivative (f : Config → Bool) (i : ℤ) : Config → Bool :=
  fun x => xor (f (Function.update x i true)) (f (Function.update x i false))

/-- Flip a single cell. -/
def flipAt (x : Config) (i : ℤ) : Config := Function.update x i (!x i)

/-! ## Cone separation -/

/-- **Cone separation (left-permutivity of the `n`-step map).** Flipping the leftmost cell
`x_{c-n}` of the light cone of `(n, c)` flips the cell `(n, c)`, for every row `x`. -/
theorem evolve_flip_left_edge (x : Config) (n : ℕ) (c : ℤ) :
    evolve (flipAt x (c - n)) n c = !evolve x n c := by
  induction n generalizing c with
  | zero => simp [flipAt]
  | succ n ih =>
    rw [evolve_succ, evolve_succ]
    have h1 : flipAt x (c - ↑(n + 1)) = flipAt x (c - 1 - n) := by push_cast; ring_nf
    rw [h1, ih (c - 1)]
    have hC : evolve (flipAt x (c - 1 - n)) n c = evolve x n c :=
      evolve_congr _ _ _ _ (fun j hj _ => by
        simp only [flipAt]; rw [Function.update_of_ne (by omega)])
    have hR : evolve (flipAt x (c - 1 - n)) n (c + 1) = evolve x n (c + 1) :=
      evolve_congr _ _ _ _ (fun j hj _ => by
        simp only [flipAt]; rw [Function.update_of_ne (by omega)])
    rw [hC, hR, rule30_left_permutive]

/-- **Cone separation, derivative form.** `∂ a(n)(c) / ∂ x_{c-n} = 1` identically. -/
theorem booleanDerivative_left_edge (n : ℕ) (c : ℤ) :
    booleanDerivative (fun x => evolve x n c) (c - n) = fun _ => true := by
  funext x
  simp only [booleanDerivative]
  have h := evolve_flip_left_edge (Function.update x (c - n) false) n c
  have : flipAt (Function.update x (c - ↑n) false) (c - ↑n) = Function.update x (c - n) true := by
    simp [flipAt]
  rw [this] at h
  rw [h]; cases evolve (Function.update x (c - ↑n) false) n c <;> rfl

/-- **Cone separation, decomposition form.** `a(n)(c) = x_{c-n} xor g(x)`, where
`g(x) = a(n)(c)` evaluated with `x_{c-n}` set to `0`; `g` does not depend on `x_{c-n}`. -/
theorem cone_separation_decomposition (x : Config) (n : ℕ) (c : ℤ) :
    evolve x n c = xor (x (c - n)) (evolve (Function.update x (c - n) false) n c) := by
  cases hx : x (c - n)
  · simp only [Bool.false_xor]
    congr 1; funext j
    by_cases hj : j = c - n
    · subst hj; simp [hx]
    · simp [Function.update_of_ne hj]
  · have h := evolve_flip_left_edge (Function.update x (c - n) false) n c
    have : flipAt (Function.update x (c - ↑n) false) (c - ↑n) = x := by
      funext j
      by_cases hj : j = c - n
      · subst hj; simp [flipAt, hx]
      · simp [flipAt, Function.update_of_ne hj]
    rw [this] at h
    rw [h]; cases evolve (Function.update x (c - ↑n) false) n c <;> rfl

/-! ## The right-edge derivative formula -/

/-- **Right-edge derivative formula.** For every row `x`,
`∂ a(n)(c) / ∂ x_{c+n} (x) = 1` iff the cells `(k, c+n-1-k)`, `k < n` (the diagonal just
inside the right edge of the light cone) are all white. -/
theorem booleanDerivative_right_edge (n : ℕ) (c : ℤ) (x : Config) :
    booleanDerivative (fun x => evolve x n c) (c + n) x =
      decide (∀ k < n, evolve x k (c + n - 1 - k) = false) := by
  induction n generalizing c with
  | zero => simp [booleanDerivative]
  | succ n ih =>
    simp only [booleanDerivative] at ih ⊢
    rw [evolve_succ, evolve_succ]
    -- the left and centre parents do not see `x_{c+n+1}`
    have hL : ∀ b, evolve (Function.update x (c + ↑(n + 1)) b) n (c - 1) = evolve x n (c - 1) :=
      fun b => evolve_congr _ _ _ _ (fun j _ hj => by
        rw [Function.update_of_ne (by push_cast at *; omega)])
    have hC : ∀ b, evolve (Function.update x (c + ↑(n + 1)) b) n c = evolve x n c :=
      fun b => evolve_congr _ _ _ _ (fun j _ hj => by
        rw [Function.update_of_ne (by push_cast at *; omega)])
    rw [hL, hL, hC, hC]
    have hidx : c + ↑(n + 1) = (c + 1) + n := by push_cast; ring
    have ih' := ih (c + 1)
    -- the inner diagonal cells do not see `x_{c+n+1}` either
    have key : (∀ k < n + 1, evolve x k (c + ↑(n + 1) - 1 - ↑k) = false) ↔
        (evolve x n c = false ∧ ∀ k < n, evolve x k (c + 1 + ↑n - 1 - ↑k) = false) := by
      constructor
      · intro h
        refine ⟨?_, fun k hk => ?_⟩
        · have := h n (by omega); rwa [show c + ↑(n + 1) - 1 - ↑n = c by push_cast; ring] at this
        · have := h k (by omega)
          rwa [show c + ↑(n + 1) - 1 - ↑k = c + 1 + ↑n - 1 - ↑k by push_cast; ring] at this
      · rintro ⟨h1, h2⟩ k hk
        rcases Nat.lt_succ_iff_lt_or_eq.mp hk with hk | hk
        · rw [show c + ↑(n + 1) - 1 - ↑k = c + 1 + ↑n - 1 - ↑k by push_cast; ring]; exact h2 k hk
        · subst hk; rwa [show c + ↑(k + 1) - 1 - ↑k = c by push_cast; ring]
    rw [decide_eq_decide.mpr key, Bool.decide_and, hidx, ← ih']
    cases evolve x n (c - 1) <;> cases evolve x n c <;>
      cases evolve (Function.update x (c + 1 + ↑n) true) n (c + 1) <;>
      cases evolve (Function.update x (c + 1 + ↑n) false) n (c + 1) <;> rfl

/-! ## Reading direction: columns determine everything to their left -/

/-- The left-solving identity at the level of space-time:
`a(t)(c-1) = a(t+1)(c) xor (a(t)(c) or a(t)(c+1))`. -/
theorem evolve_solve_left (x : Config) (t : ℕ) (c : ℤ) :
    evolve x t (c - 1) = xor (evolve x (t + 1) c) (evolve x t c || evolve x t (c + 1)) := by
  rw [evolve_succ]; exact rule30_solve_left _ _ _

/-- **Two adjacent columns determine every column to their left.** If the space-time
diagrams of `x` and `y` agree on the columns `c` and `c+1` at all times, they agree on
every column `j ≤ c + 1` at all times. -/
theorem columns_determine_left (x y : Config) (c : ℤ)
    (h0 : ∀ t, evolve x t c = evolve y t c) (h1 : ∀ t, evolve x t (c + 1) = evolve y t (c + 1)) :
    ∀ j ≤ c + 1, ∀ t, evolve x t j = evolve y t j := by
  have key : ∀ k : ℕ, ∀ t, evolve x t (c - k) = evolve y t (c - k) ∧
      evolve x t (c + 1 - k) = evolve y t (c + 1 - k) := by
    intro k
    induction k with
    | zero => intro t; simp [h0, h1]
    | succ k ih =>
      intro t
      refine ⟨?_, ?_⟩
      · have e : c - ↑(k + 1) = (c - k) - 1 := by push_cast; ring
        rw [e, evolve_solve_left, evolve_solve_left, (ih (t + 1)).1, (ih t).1,
          show c - ↑k + 1 = c + 1 - k by ring, (ih t).2]
      · rw [show c + 1 - ↑(k + 1) = c - k by push_cast; ring]; exact (ih t).1
  intro j hj t
  obtain ⟨k, hk⟩ : ∃ k : ℕ, j = c + 1 - k := ⟨(c + 1 - j).toNat, by omega⟩
  rw [hk]; exact (key k t).2

/-! ## ... but not to their right: the left wall -/

/-- The half-row `…0101` ending in a black cell at position `1`. -/
def leftWall (z : Config) : Config := fun c => if c ≤ 1 then decide (c % 2 = 1) else z c

/-- **The left wall is stationary.** Whatever lies to the right of position `1`, all cells at
positions `≤ 1` never change. -/
theorem left_wall_stationary (z : Config) (n : ℕ) (c : ℤ) (hc : c ≤ 1) :
    evolve (leftWall z) n c = decide (c % 2 = 1) := by
  induction n generalizing c with
  | zero => simp [leftWall, hc]
  | succ n ih =>
    rw [evolve_succ, ih (c - 1) (by omega), ih c hc]
    rcases lt_or_eq_of_le hc with hc' | rfl
    · rw [ih (c + 1) (by omega)]
      rcases Int.emod_two_eq_zero_or_one c with h | h
      · have h1 : (c - 1) % 2 = 1 := by omega
        have h2 : (c + 1) % 2 = 1 := by omega
        simp [h, h1, h2, rule30]
      · have h1 : (c - 1) % 2 = 0 := by omega
        simp [h, h1, rule30]
    · simp [rule30]

/-- **Information from the right can be invisible on the left.** There are two rows that
differ at position `2` but whose space-time diagrams agree on every column `≤ 1` forever.
So, unlike the leftward direction (`columns_determine_left`), columns never determine what
lies to their right: Rule 30 has a built-in reading direction. -/
theorem right_side_not_recoverable :
    ∃ x y : Config, x 2 ≠ y 2 ∧ ∀ n, ∀ c ≤ 1, evolve x n c = evolve y n c := by
  refine ⟨leftWall (fun _ => false), leftWall (fun _ => true), by simp [leftWall], ?_⟩
  intro n c hc
  rw [left_wall_stationary _ n c hc, left_wall_stationary _ n c hc]

end GLM.Rule30
