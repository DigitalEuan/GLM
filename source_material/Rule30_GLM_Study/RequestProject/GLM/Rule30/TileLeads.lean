module

public import RequestProject.GLM.Rule30.ShortcutNetwork
public import RequestProject.GLM.Rule30.SeedBoundary

/-!
# Round 15: leads from aperiodic-tiling theory

Three ideas taken from the theory of aperiodic monotiles, each turned into exact statements about
Rule 30.

## 1. Rigidity of the whole diagram (the "period of the whole tile collection")

In tiling theory a period is a translation that maps the *whole* collection of tiles to itself.
Here the collection is the space-time diagram of the seed.

* `seed_spacetime_period_trivial` : if shifting by `a` steps in time and `b` cells in space maps
  the seed's diagram to itself from some time on, then `a = 0` and `b = 0`.
* `seed_no_mirror_symmetry` : no time shift combined with a reflection of space maps the diagram to
  itself from some time on.

So the eventual symmetry group of the diagram, inside time shifts and isometries of the line, is
trivial. This follows the pattern of the "finite linear image" argument for tilings: translations
are trivial, so a symmetry is fixed by its linear part, and here the only non-trivial linear part
(the mirror) is excluded too. Problem 1 asks for the same rigidity for **one column**, a single
projection of the diagram. That is the hard part.

## 2. The period-2 forcing lemma (the first missing link of Problem 1)

If a column alternates `1010…` from time `N`, the local rule forces structure on its left.
`AltFrom x c N` says that column `c` of the run from `x` alternates from time `N`.

* `alt_forces_left_one` : whenever column `c` is black, column `c - 1` is black too.
* `alt_pair_constant` : column `c - 2` repeats each value it has at a black time of column `c`.
* `alt_shift_complement` : column `c - 3` is the complement of column `c - 2` shifted by one step.
* `alt_left_determined` : **everything on the left of column `c` is determined by the single
  sequence "column `c - 2`"** (from time `N + 1` on).

So the period-2 case reduces from "three unknown columns" to one unknown sequence that runs at
half speed. Problem 1's first open rung becomes: *no half-speed sequence `u` generates a
left-white world.*

## 3. The recognizability bridge (from marked to unmarked tilings)

Aperiodicity proofs for tiles often go through *marked* tiles. The step that removes the markings
needs the marking to be **recognizable** from the bare shape. In Rule 30 the pair of adjacent
columns is the "marked" object: it is proved aperiodic. The bare centre column is the unmarked
object.

* `problem1_of_neighbour_recognizable` : if a neighbouring column (`+1` or `-1`) can be read
  off from the centre column by a finite sliding window (any rule, any delay), then Problem 1
  holds.
-/

@[expose] public section

namespace GLM.Rule30

/-! ## 1. Rigidity of the seed's space-time diagram -/

/-- The second cell from the left edge is black at every time `t ≥ 1`. -/
theorem evolve_seed_left_edge_two (t : ℕ) (ht : 1 ≤ t) :
    evolve seed t (-(t : ℤ) + 1) = true := by
  obtain ⟨n, rfl⟩ : ∃ n, t = n + 1 := ⟨t - 1, by omega⟩
  rw [evolve_succ, show -((n + 1 : ℕ) : ℤ) + 1 - 1 = -((n + 1 : ℕ) : ℤ) by ring,
    show -((n + 1 : ℕ) : ℤ) + 1 = -(n : ℤ) by push_cast; ring,
    evolve_seed_outside n _ (by rw [abs_neg]; push_cast; rw [abs_of_nonneg (by positivity)]; omega),
    evolve_seed_left_edge]
  rfl

/-- The seed's right edge at distance one is white at even times. -/
theorem evolve_seed_right_edge_two_even (k : ℕ) :
    evolve seed (2 * k) ((2 * k : ℕ) - 1 : ℤ) = false := by
  have := rdiag_one_eq (2 * k)
  simp only [rdiag] at this
  rw [this]
  simp

/-- **Translation rigidity.** If the seed's diagram is invariant under the space-time shift
`(t, i) ↦ (t + a, i + b)` from time `N` on, then the shift is trivial. -/
theorem seed_spacetime_period_trivial {a : ℕ} {b : ℤ} {N : ℕ}
    (h : ∀ t ≥ N, ∀ i : ℤ, evolve seed (t + a) (i + b) = evolve seed t i) :
    a = 0 ∧ b = 0 := by
  have hR := h N le_rfl (((N + a : ℕ) : ℤ) - b)
  rw [show ((N + a : ℕ) : ℤ) - b + b = ((N + a : ℕ) : ℤ) by ring, evolve_seed_right_edge] at hR
  have hL := h N le_rfl (-((N + a : ℕ) : ℤ) - b)
  rw [show -((N + a : ℕ) : ℤ) - b + b = -((N + a : ℕ) : ℤ) by ring, evolve_seed_left_edge] at hL
  have bR : |((N + a : ℕ) : ℤ) - b| ≤ N := by
    by_contra hc; push_neg at hc; rw [evolve_seed_outside N _ hc] at hR; exact absurd hR (by simp)
  have bL : |-((N + a : ℕ) : ℤ) - b| ≤ N := by
    by_contra hc; push_neg at hc; rw [evolve_seed_outside N _ hc] at hL; exact absurd hL (by simp)
  rw [abs_le] at bR bL
  push_cast at bR bL
  omega

/-- **No mirror symmetry.** No time shift composed with a reflection `i ↦ b - i` of space maps the
seed's diagram to itself from some time on. -/
theorem seed_no_mirror_symmetry {a : ℕ} {b : ℤ} {N : ℕ} :
    ¬ ∀ t ≥ N, ∀ i : ℤ, evolve seed (t + a) (b - i) = evolve seed t i := by
  intro h
  have hR := h N le_rfl (b - ((N + a : ℕ) : ℤ))
  rw [show b - (b - ((N + a : ℕ) : ℤ)) = ((N + a : ℕ) : ℤ) by ring, evolve_seed_right_edge] at hR
  have hL := h N le_rfl (b + ((N + a : ℕ) : ℤ))
  rw [show b - (b + ((N + a : ℕ) : ℤ)) = -((N + a : ℕ) : ℤ) by ring, evolve_seed_left_edge] at hL
  have bR : |b - ((N + a : ℕ) : ℤ)| ≤ N := by
    by_contra hc; push_neg at hc; rw [evolve_seed_outside N _ hc] at hR; exact absurd hR (by simp)
  have bL : |b + ((N + a : ℕ) : ℤ)| ≤ N := by
    by_contra hc; push_neg at hc; rw [evolve_seed_outside N _ hc] at hL; exact absurd hL (by simp)
  rw [abs_le] at bR bL
  push_cast at bR bL
  have ha : a = 0 := by omega
  have hb : b = 0 := by omega
  subst ha hb
  have key := h (2 * (N + 1)) (by omega) (((2 * (N + 1) : ℕ) : ℤ) - 1)
  rw [show (0 : ℤ) - (((2 * (N + 1) : ℕ) : ℤ) - 1) = -((2 * (N + 1) : ℕ) : ℤ) + 1 by ring,
    Nat.add_zero, evolve_seed_left_edge_two _ (by omega), evolve_seed_right_edge_two_even] at key
  exact absurd key (by simp)

/-! ## 2. The period-2 forcing lemma -/

/-- Rule 30 can be solved for the left input: the left cell is the new centre cell XOR
(centre OR right). -/
theorem left_solve (x : Config) (t : ℕ) (i : ℤ) :
    evolve x t (i - 1) = xor (evolve x (t + 1) i) (evolve x t i || evolve x t (i + 1)) := by
  rw [evolve_succ]
  cases evolve x t (i - 1) <;> cases evolve x t i <;> cases evolve x t (i + 1) <;> rfl

/-- **Leftward determination.** Two runs that agree on two adjacent columns from time `M` on agree
on every column to their left from time `M` on. -/
theorem columns_left_determined (x y : Config) (c : ℤ) (M : ℕ)
    (h0 : ∀ t ≥ M, evolve x t c = evolve y t c)
    (h1 : ∀ t ≥ M, evolve x t (c + 1) = evolve y t (c + 1)) :
    ∀ k : ℕ, ∀ t ≥ M, evolve x t (c - k) = evolve y t (c - k) := by
  intro k
  suffices H : ∀ t ≥ M, evolve x t (c - k) = evolve y t (c - k) ∧
      evolve x t (c + 1 - k) = evolve y t (c + 1 - k) from fun t ht => (H t ht).1
  induction k with
  | zero => intro t ht; simpa using And.intro (h0 t ht) (h1 t ht)
  | succ k ih =>
    intro t ht
    refine ⟨?_, by simpa [show c + 1 - ((k + 1 : ℕ) : ℤ) = c - k by push_cast; ring] using (ih t ht).1⟩
    have e : c - ((k + 1 : ℕ) : ℤ) = (c - k) - 1 := by push_cast; ring
    rw [e, left_solve x, left_solve y, (ih (t + 1) (by omega)).1, (ih t ht).1,
      show c - (k : ℤ) + 1 = c + 1 - k by ring, (ih t ht).2]

/-- Column `c` of the run from `x` alternates from time `N` on. -/
def AltFrom (x : Config) (c : ℤ) (N : ℕ) : Prop :=
  ∀ t ≥ N, evolve x (t + 1) c = !evolve x t c

/-- **Key forcing.** At a black time of column `c`, the cell to its left is the complement of the
next value of column `c`. (True for every run, with no periodicity assumption.) -/
theorem key_forcing (x : Config) (c : ℤ) (t : ℕ) (h : evolve x t c = true) :
    evolve x t (c - 1) = !evolve x (t + 1) c := by
  have e := evolve_succ x t c
  rw [h] at e
  rw [e]
  cases evolve x t (c - 1) <;> rfl

/-- If column `c` alternates, the cell to its left is black whenever column `c` is black. -/
theorem alt_forces_left_one {x : Config} {c : ℤ} {N : ℕ} (h : AltFrom x c N) {t : ℕ} (ht : N ≤ t)
    (hc : evolve x t c = true) : evolve x t (c - 1) = true := by
  rw [key_forcing x c t hc, h t ht, hc]; rfl

/-- One step after a black time of column `c`, column `c - 1` is the complement of column
`c - 2`. -/
theorem alt_next_left {x : Config} {c : ℤ} {N : ℕ} (h : AltFrom x c N) {t : ℕ} (ht : N ≤ t)
    (hc : evolve x t c = true) : evolve x (t + 1) (c - 1) = !evolve x t (c - 2) := by
  rw [evolve_succ, show c - 1 - 1 = c - 2 by ring, show c - 1 + 1 = c by ring,
    alt_forces_left_one h ht hc]
  cases evolve x t (c - 2) <;> rfl

/-- **Pair constancy.** If column `c` alternates, column `c - 2` keeps its value for one step
after each black time of column `c`. -/
theorem alt_pair_constant {x : Config} {c : ℤ} {N : ℕ} (h : AltFrom x c N) {t : ℕ} (ht : N ≤ t)
    (hc : evolve x t c = true) : evolve x (t + 1) (c - 2) = evolve x t (c - 2) := by
  have h1 : evolve x (t + 1) c = false := by rw [h t ht, hc]; rfl
  have h2 : evolve x (t + 2) c = true := by rw [h (t + 1) (by omega), h1]; rfl
  have l2 := alt_forces_left_one h (t := t + 2) (by omega) h2
  have e := evolve_succ x (t + 1) (c - 1)
  rw [show c - 1 - 1 = c - 2 by ring, show c - 1 + 1 = c by ring, h1, alt_next_left h ht hc] at e
  rw [show t + 1 + 1 = t + 2 by ring, l2] at e
  revert e
  cases evolve x (t + 1) (c - 2) <;> cases evolve x t (c - 2) <;> simp [rule30]

/-- From time `N + 1` on, at least one of columns `c - 2`, `c - 1` is black. -/
theorem alt_left_or {x : Config} {c : ℤ} {N : ℕ} (h : AltFrom x c N) {t : ℕ} (ht : N + 1 ≤ t) :
    (evolve x t (c - 2) || evolve x t (c - 1)) = true := by
  cases hc : evolve x t c
  · obtain ⟨s, rfl⟩ : ∃ s, t = s + 1 := ⟨t - 1, by omega⟩
    have hs : evolve x s c = true := by
      have := h s (by omega); rw [hc] at this
      revert this; cases evolve x s c <;> simp
    rw [alt_pair_constant h (by omega) hs, alt_next_left h (by omega) hs]
    cases evolve x s (c - 2) <;> rfl
  · rw [alt_forces_left_one h (by omega) hc]; simp

/-- **Shifted complement.** If column `c` alternates from time `N`, then from time `N + 1` on,
column `c - 3` is the complement of column `c - 2` one step later. -/
theorem alt_shift_complement {x : Config} {c : ℤ} {N : ℕ} (h : AltFrom x c N) {t : ℕ}
    (ht : N + 1 ≤ t) : evolve x t (c - 3) = !evolve x (t + 1) (c - 2) := by
  rw [show c - 3 = (c - 2) - 1 by ring, left_solve, show c - 2 + 1 = c - 1 by ring,
    alt_left_or h ht]
  cases evolve x (t + 1) (c - 2) <;> rfl

/-- **One-parameter reduction of the period-2 case.** Two runs whose column `c` alternates from
time `N` in the same phase, and whose columns `c - 2` agree from time `N` on, agree on every
column `j ≤ c` from time `N + 1` on. -/
theorem alt_left_determined {x y : Config} {c : ℤ} {N : ℕ} (hx : AltFrom x c N)
    (hy : AltFrom y c N) (hN : evolve x N c = evolve y N c)
    (hu : ∀ t ≥ N, evolve x t (c - 2) = evolve y t (c - 2)) :
    ∀ j ≤ c, ∀ t ≥ N + 1, evolve x t j = evolve y t j := by
  have hc : ∀ t ≥ N, evolve x t c = evolve y t c := by
    intro t ht
    induction t, ht using Nat.le_induction with
    | base => exact hN
    | succ t ht ih => rw [hx t ht, hy t ht, ih]
  have hc1 : ∀ t ≥ N + 1, evolve x t (c - 1) = evolve y t (c - 1) := by
    intro t ht
    cases hxt : evolve x t c
    · obtain ⟨s, rfl⟩ : ∃ s, t = s + 1 := ⟨t - 1, by omega⟩
      have hs : evolve x s c = true := by
        have := hx s (by omega); rw [hxt] at this
        revert this; cases evolve x s c <;> simp
      have hs' : evolve y s c = true := by rw [← hc s (by omega)]; exact hs
      rw [alt_next_left hx (by omega) hs, alt_next_left hy (by omega) hs', hu s (by omega)]
    · have hyt : evolve y t c = true := by rw [← hc t (by omega)]; exact hxt
      rw [alt_forces_left_one hx (by omega) hxt, alt_forces_left_one hy (by omega) hyt]
  have hdet := columns_left_determined x y (c - 2) (N + 1) (fun t ht => hu t (by omega))
    (fun t ht => by rw [show c - 2 + 1 = c - 1 by ring]; exact hc1 t ht)
  intro j hj t ht
  rcases (show j = c ∨ j = c - 1 ∨ j ≤ c - 2 by omega) with rfl | rfl | hj2
  · exact hc t (by omega)
  · exact hc1 t ht
  · have := hdet (c - 2 - j).toNat t ht
    rwa [show c - 2 - (((c - 2 - j).toNat : ℕ) : ℤ) = j by omega] at this

/-! ## 3. The recognizability bridge -/

/-- Column `c` of the seed's run. -/
def seedCol (c : ℤ) (t : ℕ) : Bool := evolve seed t c

/-- **Recognizability implies Problem 1.** Suppose that from some time on, a neighbouring column
(`+1` or `-1`) of the seed's run can be read off from a window of `k` cells of the centre column,
by a fixed rule `F` and with a fixed delay `s`. Then the centre column is not eventually
periodic. -/
theorem problem1_of_neighbour_recognizable {k : ℕ} (F : (Fin k → Bool) → Bool) (s N : ℕ)
    (e : ℤ) (he : e = 1 ∨ e = -1)
    (h : ∀ t ≥ N, seedCol e (t + s) = lensWalk F 1 centerCol t) : Problem1 := by
  intro hp
  obtain ⟨p, hp0, M, hM⟩ := evPeriodic_lensWalk F 1 hp
  have hcol : EventuallyPeriodic (seedCol e) := by
    refine ⟨p, hp0, max N M + s, fun n hn => ?_⟩
    obtain ⟨t, rfl⟩ : ∃ t, n = t + s := ⟨n - s, by omega⟩
    rw [show t + s + p = (t + p) + s by ring, h (t + p) (by omega), h t (by omega),
      hM t (by omega)]
  rcases he with rfl | rfl
  · exact seed_not_both_adjacent_columns_periodic 0 ⟨hp, by simpa [seedCol] using hcol⟩
  · exact seed_not_both_adjacent_columns_periodic (-1) ⟨hcol, by simpa using hp⟩

end GLM.Rule30
