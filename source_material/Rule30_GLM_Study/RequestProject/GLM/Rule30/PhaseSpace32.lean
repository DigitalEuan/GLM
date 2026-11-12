import RequestProject.GLM.Rule30.ANF
import RequestProject.GLM.Rule30.ElementaryCA

/-!
# The 32-state causal phase space (5-cell window)

(This file is deliberately not a `module`: some finite checks use `native_decide`.)

Two Rule 30 steps map a 5-cell window `x_{c−2}, …, x_{c+2}` to the cell `a(2)(c)`.
The window has `2^5 = 32` states.  This file formalises that phase space and checks
everything about it exhaustively, then records exactly what such a local check can and
cannot establish about the global degree growth.

## What is proved

* `evolve_two_eq_local` : `a(2)(c) = r30_local_update (window x c)` for every row — the
  32-state map *is* the two-step map.
* `local_anf` (all 32 states): the ANF of the local update is
  `x₋₂ + x₁ + x₋₁x₁ + x₀x₁ + x₂ + x₋₁x₂ + x₀x₂ + x₁x₂ + x₋₁x₁x₂ + x₀x₁x₂`,
  so its degree is `3 = 2·2 − 1`, with **two** top monomials `x₋₁x₁x₂` and `x₀x₁x₂`.
* `localCoeff_eq_anfCoeff` : these local coefficients are the global ANF coefficients of
  `a(2)(0)` from `ANF.lean` (the window loses nothing).
* `local_left_permutive`, `local_right_derivative`, `local_depends_both_edges` : the
  32-state versions of cone separation and of the right-edge derivative formula.
* `depends_exactly_on_cone` (all `n`): `a(n)(c)` depends on both `x_{c−n}` and `x_{c+n}`;
  the support grows by exactly one cell on each side at every step.

## What a 5-cell check cannot do (the "bridge lemma" audited)

`phaseSpace_does_not_determine_growth`: Rule 30 and Rule 180 (`L xor (C and not R)`) have
the *same* 32-state profile — both are left-permutive, both two-step maps have degree `3`
and depend on both edge cells — but after three steps Rule 30 has degree `5` and Rule 180
only degree `4`.  So no property read off the 32-state phase space alone can force
`deg = 2n − 1`; the global growth depends on how the window maps compose, which is the
`TopMonomialConjecture`.
-/

namespace GLM.Rule30

open Finset

/-! ## The phase space and the local update -/

/-- The 32-state causal phase space: a 5-cell window `x_{c−2}, …, x_{c+2}` (index `i` is the
cell `c + i − 2`).  (An `abbrev`, so that finiteness and decidability are inferred.) -/
abbrev LocalPhaseSpace := Fin 5 → Bool

/-- Rule 30 applied twice inside the window: the cell `a(2)(c)` as a function of the
32 window states.  Over `GF(2)` each step is `f(L, C, R) = L + C + R + C·R`. -/
def r30_local_update (s : LocalPhaseSpace) : Bool :=
  rule30 (rule30 (s 0) (s 1) (s 2)) (rule30 (s 1) (s 2) (s 3)) (rule30 (s 2) (s 3) (s 4))

/-- The window of the row `x` around the cell `c`. -/
def window (x : Config) (c : ℤ) : LocalPhaseSpace := fun i => x (c + (i : ℤ) - 2)

/-- **The 32-state map is the two-step map.** -/
theorem evolve_two_eq_local (x : Config) (c : ℤ) :
    evolve x 2 c = r30_local_update (window x c) := by
  simp only [evolve_succ, evolve_zero, r30_local_update, window]
  norm_num
  ring_nf

/-! ## Exhaustive algebra on the 32 states -/

/-- The indicator state of a set of window cells. -/
def localInd (T : Finset (Fin 5)) : LocalPhaseSpace := fun i => decide (i ∈ T)

/-- ANF coefficient on the 32-state space (Möbius transform), as an element of `GF(2)`. -/
def localCoeff (f : LocalPhaseSpace → Bool) (S : Finset (Fin 5)) : ZMod 2 :=
  ∑ T ∈ S.powerset, bz (f (localInd T))

/-- The monomials of the local update (window indices; `i` ↔ `x_{i−2}`). -/
def localMonomials : Finset (Finset (Fin 5)) :=
  {{0}, {3}, {1, 3}, {2, 3}, {4}, {1, 4}, {2, 4}, {3, 4}, {1, 3, 4}, {2, 3, 4}}

/-- **ANF of the 32-state map** (exhaustive over all 32 monomials):
`x₋₂ + x₁ + x₋₁x₁ + x₀x₁ + x₂ + x₋₁x₂ + x₀x₂ + x₁x₂ + x₋₁x₁x₂ + x₀x₁x₂`. -/
theorem local_anf (S : Finset (Fin 5)) :
    localCoeff r30_local_update S = if S ∈ localMonomials then 1 else 0 := by
  revert S; native_decide

/-- **Degree 3 on the 32-state space**, with exactly two top monomials. -/
theorem local_degree :
    (∀ S : Finset (Fin 5), 3 < S.card → localCoeff r30_local_update S = 0) ∧
      (univ.filter (fun S : Finset (Fin 5) =>
          S.card = 3 ∧ localCoeff r30_local_update S = 1)) = {{1, 3, 4}, {2, 3, 4}} := by
  native_decide

/-- Flip one window cell. -/
def localFlip (s : LocalPhaseSpace) (i : Fin 5) : LocalPhaseSpace := Function.update s i (!s i)

/-- **Cone separation on the 32 states**: flipping `x_{c−2}` always flips `a(2)(c)`. -/
theorem local_left_permutive (s : LocalPhaseSpace) :
    r30_local_update (localFlip s 0) = !r30_local_update s := by
  revert s; decide

/-- **Right-edge derivative on the 32 states**: flipping `x_{c+2}` flips `a(2)(c)` exactly
when `x_{c+1}` and `a(1)(c)` are both white (the `n = 2` case of
`booleanDerivative_right_edge`). -/
theorem local_right_derivative (s : LocalPhaseSpace) :
    xor (r30_local_update (localFlip s 4)) (r30_local_update s) =
      (!s 3 && !rule30 (s 1) (s 2) (s 3)) := by
  revert s; decide

/-- The two-step map really depends on both edge cells of its window. -/
theorem local_depends_both_edges :
    (∃ s, r30_local_update (localFlip s 0) ≠ r30_local_update s) ∧
      (∃ s, r30_local_update (localFlip s 4) ≠ r30_local_update s) := by
  decide

/-! ## The local coefficients are the global ones -/

/-- Window index `i` ↦ cell `i − 2`. -/
def windowEmb : Fin 5 ↪ ℤ := ⟨fun i => (i : ℤ) - 2, fun i j h => by
  simp only [sub_left_inj, Nat.cast_inj] at h; exact Fin.ext h⟩

theorem window_ind_map (T : Finset (Fin 5)) : window (ind (T.map windowEmb)) 0 = localInd T := by
  funext i
  simp only [window, ind, localInd, mem_map, windowEmb, Function.Embedding.coeFn_mk, zero_add]
  apply decide_eq_decide.mpr
  constructor
  · rintro ⟨j, hj, hji⟩
    have : j = i := Fin.ext (by omega)
    exact this ▸ hj
  · intro hi; exact ⟨i, hi, rfl⟩

/-- **The 32-state ANF is the global ANF of `a(2)(0)`.** -/
theorem localCoeff_eq_anfCoeff (S : Finset (Fin 5)) :
    localCoeff r30_local_update S = anfCoeff (fun x => evolve x 2 0) (S.map windowEmb) := by
  rw [anfCoeff, coeffZ, localCoeff]
  refine sum_bij (fun T _ => T.map windowEmb) ?_ ?_ ?_ ?_
  · intro T hT; exact mem_powerset.mpr (map_subset_map.mpr (mem_powerset.mp hT))
  · intro T₁ _ T₂ _ h; exact map_inj.mp h
  · intro U hU
    obtain ⟨u, hu, rfl⟩ := subset_map_iff.mp (mem_powerset.mp hU)
    exact ⟨u, mem_powerset.mpr hu, rfl⟩
  · intro T _
    rw [evolve_two_eq_local, window_ind_map]

/-! ## Global support growth: one cell on each side per step (all `n`) -/

/-- **The dependence window of `a(n)(c)` is exactly `[c − n, c + n]`**: it depends on
`x_{c−n}` (cone separation) and on `x_{c+n}` (at the all-white row, by the right-edge
derivative formula).  This is the true "+1 left, +1 right" growth — of the support, not
of the degree. -/
theorem depends_exactly_on_cone (n : ℕ) (c : ℤ) :
    (∃ x : Config, evolve (flipAt x (c - n)) n c ≠ evolve x n c) ∧
      (∃ x : Config, evolve (flipAt x (c + n)) n c ≠ evolve x n c) := by
  refine ⟨⟨fun _ => false, by rw [evolve_flip_left_edge]; simp⟩, ⟨fun _ => false, ?_⟩⟩
  have hd := booleanDerivative_right_edge n c (fun _ => false)
  simp only [booleanDerivative, evolve_false, implies_true, decide_true] at hd
  intro h
  have hw : Function.update (fun _ : ℤ => false) (c + n) false = fun _ => false := by
    funext j; by_cases hj : j = c + n
    · subst hj; simp
    · simp [Function.update_of_ne hj]
  rw [hw, evolve_false] at hd
  simp only [flipAt, Bool.not_false, evolve_false] at h
  rw [h] at hd; simp at hd

/-! ## Generic elementary CA on a finite window (for the audit) -/

-- `ecaRule` (Wolfram's numbering) and `ecaRule_30` now live in `ElementaryCA.lean` (Round 9),
-- where the whole elementary family is developed.

/-- Rule 180 is `L xor (C and not R)`, i.e. `L + C + C·R` over `GF(2)`. -/
theorem ecaRule_180 (L C R : Bool) : ecaRule 180 L C R = xor L (C && !R) := by
  cases L <;> cases C <;> cases R <;> rfl

/-- One step on a finite list of cells (the list shrinks by two). -/
def stepList (f : Bool → Bool → Bool → Bool) : List Bool → List Bool
  | a :: b :: c :: rest => f a b c :: stepList f (b :: c :: rest)
  | _ => []

/-- The centre cell after `n` steps, from the `2n + 1` cells encoded by the mask `m`. -/
def runCenter (f : Bool → Bool → Bool → Bool) (n m : ℕ) : Bool :=
  ((stepList f)^[n] ((List.range (2 * n + 1)).map m.testBit)).headD false

/-- ANF coefficient (Möbius transform over submasks) of the `n`-step centre map. -/
def windowCoeff (f : Bool → Bool → Bool → Bool) (n S : ℕ) : Bool :=
  ((List.range (2 ^ (2 * n + 1))).filter (fun T => T &&& S == T && runCenter f n T)).length
    % 2 == 1

/-- Number of cells in a mask. -/
def maskCard (k S : ℕ) : ℕ := ((List.range k).filter S.testBit).length

/-- ANF degree of the `n`-step centre map. -/
def windowDegree (f : Bool → Bool → Bool → Bool) (n : ℕ) : ℕ :=
  (((List.range (2 ^ (2 * n + 1))).filter (windowCoeff f n)).map (maskCard (2 * n + 1))).foldr
    max 0

/-- The 32-state profile used by the bridge-lemma argument: degrees after one and two
steps, left-permutivity of the two-step map, and dependence on both edge cells. -/
def profile32 (f : Bool → Bool → Bool → Bool) : ℕ × ℕ × Bool × Bool × Bool :=
  (windowDegree f 1, windowDegree f 2,
    (List.range 32).all (fun m => runCenter f 2 (m ^^^ 1) == !runCenter f 2 m),
    (List.range 32).any (fun m => runCenter f 2 (m ^^^ 1) != runCenter f 2 m),
    (List.range 32).any (fun m => runCenter f 2 (m ^^^ 16) != runCenter f 2 m))

/-- Sanity check against the global theorems: the generic evaluator gives Rule 30 the
degrees `2, 3, 5, 7, 9` for `n = 1, …, 5` (cf. `anfDegree_one`, `anfDegree_eq_upto14`). -/
theorem windowDegree_rule30 :
    (List.range' 1 5).map (windowDegree (ecaRule 30)) = [2, 3, 5, 7, 9] := by native_decide

/-- Rule 180 grows by only one per step: `2, 3, 4, 5, 6`. -/
theorem windowDegree_rule180 :
    (List.range' 1 5).map (windowDegree (ecaRule 180)) = [2, 3, 4, 5, 6] := by native_decide

/-- **The 32-state phase space does not determine degree growth.** Rule 30 and Rule 180
have identical 32-state profiles (degree `2` then `3`, left-permutive, both edges
essential), yet their three-step degrees are `5` and `4`. -/
theorem phaseSpace_does_not_determine_growth :
    profile32 (ecaRule 30) = profile32 (ecaRule 180) ∧ profile32 (ecaRule 30) = (2, 3, true, true, true) ∧
      windowDegree (ecaRule 30) 3 = 5 ∧ windowDegree (ecaRule 180) 3 = 4 := by
  native_decide

end GLM.Rule30
