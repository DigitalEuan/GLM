module

public import RequestProject.GLM.Rule30.ConeSeparation
public import RequestProject.GLM.Rule30.Wobble

/-!
# Perspective: the wobble as the observer's arrow, and the mirror observer

This file makes precise the suggestion that the wobble defines a *perspective* — a
direction from which the observer reads and towards which a run is converging.

## 1. The wobble arrow (time direction)

At time `n` the observer "stands" at deviation `f(n) − 1/2 = D(n)/(2n)`.  Define
* `observerArrow a n = −sign D(n) ∈ {−1, 0, 1}` — the direction pointing towards balance;
* `stepDir a n = +1` if `a n = true`, `−1` otherwise — the direction of the next step.

`deviation_decreases_iff` proves, for every sequence and every `n ≥ 1`:

  the next bit brings the frequency strictly closer to `1/2`
  **iff** the arrow is non-zero and the step follows the arrow.

So `observerArrow` is exactly the "arrow" that tells which way the run is currently
converging: the run converges at a step precisely when it moves along the arrow.

## 2. Reading direction (time reversal)

`wobble_reverse`: reading a window of length `N` backwards (from the far end), the
accumulator is `D_rev(k) = D(N) − D(N − k)`: the two observers agree on the total, and their
paths are related by a point reflection.

## 3. The mirror observer (space direction)

An observer looking at the automaton from the other side sees the mirror rule
`rule86 L C R = rule30 R C L` (Rule 86).  `evolve86_mirror` shows the mirror observer sees
the mirrored space-time diagram; in particular both observers see **the same centre
column** (`centerCol86_eq`), but the permutive side flips: Rule 86 is right-permutive and
not left-permutive (`rule86_right_permutive`, `rule86_not_left_permutive`).  So the
centre-column problems are perspective-independent, while the cone-separation arrow
(`columns_determine_left`) is a property of the chosen side.
-/

@[expose] public section

namespace GLM.Rule30

/-! ## 1. The wobble arrow -/

/-- The observer's arrow at time `n`: the direction (`±1`) pointing back towards balance,
or `0` when exactly balanced. -/
def observerArrow (a : ℕ → Bool) (n : ℕ) : ℤ := -Int.sign (wobble a n)

/-- The direction of the step taken at time `n`. -/
def stepDir (a : ℕ → Bool) (n : ℕ) : ℤ := if a n then 1 else -1

/-- Integer core of the arrow theorem. -/
theorem int_arrow (W s n : ℤ) (hn : 1 ≤ n) (hW : |W| ≤ n) (hs : s = 1 ∨ s = -1) :
    |W + s| * n < |W| * (n + 1) ↔ (-Int.sign W ≠ 0 ∧ s = -Int.sign W) := by
  rcases lt_trichotomy W 0 with h | rfl | h
  · rw [Int.sign_eq_neg_one_of_neg h]
    rw [abs_of_neg h] at hW ⊢
    rcases hs with rfl | rfl
    · rcases eq_or_lt_of_le (show W + 1 ≤ 0 by omega) with h' | h'
      · rw [h', abs_zero]; simp; nlinarith
      · rw [abs_of_neg h']; simp; nlinarith
    · rw [abs_of_neg (by omega : W + -1 < 0)]; simp; nlinarith
  · rcases hs with rfl | rfl <;> simp <;> omega
  · rw [Int.sign_eq_one_of_pos h]
    rw [abs_of_pos h] at hW ⊢
    rcases hs with rfl | rfl
    · rw [abs_of_pos (by omega : 0 < W + 1)]; simp; nlinarith
    · rcases eq_or_lt_of_le (show 0 ≤ W + -1 by omega) with h' | h'
      · rw [← h', abs_zero]; simp; nlinarith
      · rw [abs_of_pos h']; simp; nlinarith

/-- **The wobble arrow theorem.** For `n ≥ 1`, the bit `a n` moves the empirical frequency
strictly closer to `1/2` iff the observer's arrow is non-zero and the step follows it. -/
theorem deviation_decreases_iff (a : ℕ → Bool) {n : ℕ} (hn : 1 ≤ n) :
    |freq a (n + 1) - 1 / 2| < |freq a n - 1 / 2| ↔
      (observerArrow a n ≠ 0 ∧ stepDir a n = observerArrow a n) := by
  rw [freq_sub_half a (by omega), freq_sub_half a hn, abs_div, abs_div,
    abs_of_pos (by positivity : (0:ℝ) < 2 * ((n + 1 : ℕ) : ℝ)),
    abs_of_pos (by positivity : (0:ℝ) < 2 * (n : ℝ)),
    div_lt_div_iff₀ (by positivity) (by positivity)]
  have hs : stepDir a n = 1 ∨ stepDir a n = -1 := by
    unfold stepDir; split_ifs <;> simp
  have hW' : wobble a (n + 1) = wobble a n + stepDir a n := by
    rw [wobble_succ]; rfl
  rw [hW', observerArrow]
  rw [← int_arrow (wobble a n) (stepDir a n) n (by exact_mod_cast hn)
    (abs_wobble_le a n) hs]
  constructor
  · intro h
    have : ((|wobble a n + stepDir a n| * n : ℤ) : ℝ) < ((|wobble a n| * (n + 1) : ℤ) : ℝ) := by
      push_cast at h ⊢; nlinarith
    exact_mod_cast this
  · intro h
    have h' : ((|wobble a n + stepDir a n| * n : ℤ) : ℝ) < ((|wobble a n| * (n + 1) : ℤ) : ℝ) := by
      exact_mod_cast h
    push_cast at h' ⊢; nlinarith

/-- **The ideal delta-sigma modulator always follows the arrow.** Its feedback loop *is* the
observer's arrow; Rule 30, by contrast, is "open loop" (see `arrow_stats_10000`, where it
follows the arrow on 4968 of the 9964 steps with a non-zero arrow below `10⁴`). -/
theorem deltaSigma_follows_arrow (n : ℕ) (h : observerArrow deltaSigma n ≠ 0) :
    stepDir deltaSigma n = observerArrow deltaSigma n := by
  obtain ⟨h1, h2⟩ := deltaSigma_wobble n
  unfold observerArrow at h ⊢
  rw [h1] at h ⊢
  rcases h2 with h2 | h2
  · simp [h2] at h
  · simp [stepDir, deltaSigma, h2]

/-! ## 2. Reading direction -/

/-- Read the window `a 0, …, a (N-1)` backwards. -/
def readBackwards (N : ℕ) (a : ℕ → Bool) : ℕ → Bool := fun i => a (N - 1 - i)

theorem ones_readBackwards (N : ℕ) (a : ℕ → Bool) :
    ∀ k ≤ N, ones (readBackwards N a) k + ones a (N - k) = ones a N := by
  intro k
  induction k with
  | zero => intro _; simp
  | succ k ih =>
    intro hk
    have := ih (by omega)
    rw [ones_succ]
    have e : N - k = (N - (k + 1)) + 1 := by omega
    rw [e, ones_succ] at this
    simp only [readBackwards, show N - 1 - k = N - (k + 1) by omega]
    split_ifs at this ⊢ <;> omega

/-- **Reversed reading.** The backwards observer's accumulator is `D(N) − D(N − k)`. -/
theorem wobble_reverse (N : ℕ) (a : ℕ → Bool) (k : ℕ) (hk : k ≤ N) :
    wobble (readBackwards N a) k = wobble a N - wobble a (N - k) := by
  have := ones_readBackwards N a k hk
  unfold wobble
  have h : ((N - k : ℕ) : ℤ) = N - k := by omega
  rw [h]; omega

/-! ## 3. The mirror observer -/

/-- Rule 86: Rule 30 seen in a mirror. -/
def rule86 (L C R : Bool) : Bool := rule30 R C L

theorem rule86_truthTable (L C R : Bool) :
    rule86 L C R = Nat.testBit 86 (4 * L.toNat + 2 * C.toNat + R.toNat) :=
  rule30_mirror_eq_rule86 L C R

/-- The space-time evolution under Rule 86. -/
def evolve86 (x : Config) : ℕ → Config
  | 0 => x
  | n + 1 => fun c => rule86 (evolve86 x n (c - 1)) (evolve86 x n c) (evolve86 x n (c + 1))

/-- **The mirror observer sees the mirrored diagram.** -/
theorem evolve86_mirror (x : Config) (n : ℕ) (c : ℤ) :
    evolve86 (fun j => x (-j)) n c = evolve x n (-c) := by
  induction n generalizing c with
  | zero => rfl
  | succ n ih =>
    simp only [evolve86, ih, evolve_succ, rule86]
    congr 1 <;> [congr 1; skip] <;> ring_nf

/-- Both observers see the same centre column. -/
theorem centerCol86_eq (n : ℕ) : evolve86 seed n 0 = centerCol n := by
  have h : (fun j : ℤ => seed (-j)) = seed := by funext j; simp [seed]
  have := evolve86_mirror seed n 0
  rw [h] at this; simpa [centerCol] using this

theorem rule86_right_permutive (L C R : Bool) : rule86 L C (!R) = !rule86 L C R :=
  rule30_left_permutive R C L

theorem rule86_not_left_permutive : ∃ L C R : Bool, rule86 (!L) C R = rule86 L C R :=
  ⟨false, true, false, rfl⟩

end GLM.Rule30
