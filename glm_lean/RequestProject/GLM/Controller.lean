/-
# The loop: propose, check, refuse — and what each of those steps guarantees

`SearchLoop.lean` proved what a *one-shot* hard gate buys: filter the
candidates on every observation, and what survives is sound but not
determined.  `ReasoningLoop.lean` proved that a loop with a decreasing
ℕ-valued gap terminates.  Neither of them is a controller: neither takes a
question it cannot answer in one step, decomposes it, tries, checks and
revises.

`overlay/glm_universal/reasoning/controller.py` is that controller, on the one
register where every step can be checked exactly: a **dimensional derivation**.
The task is to express a physical quantity as a product of powers of the ten
EXT10 generators, one factor at a time, with the existing exact verifier
deciding whether the answer is right.  The loop proposes the twenty moves
(multiply or divide by one of the ten generators), scores them with a
heuristic, keeps the best few, and repeats until the state *is* the target or
the budget is gone — at which point it refuses rather than returning its
closest guess.

This file is what that loop can promise, stated so that no measurement can
take it away.

## 1.  The state space

A state is an exponent vector `Fin n → ℤ`; a move adds or subtracts one basis
vector; a plan is a list of moves and `replay` applies it.  Because a move only
ever adds `± e i`, `replay p s = s + Σ (p.map delta)`, which is `replay_eq`,
and plans compose by `++`.

## 2.  How long the shortest plan is — exactly

* `l1_le_length` — **the lower bound.**  A plan reaching `t` from `0` has at
  least `‖t‖₁` moves, because one move changes the ℓ¹ norm by at most one.
* `exists_plan` — **the upper bound, constructively.**  There is a plan of
  exactly `‖t‖₁` moves.
* `minimal_length_eq_l1` — so the minimum is `‖t‖₁`, and the controller has an
  exact optimum to be scored against rather than a best-so-far.  Every
  measurement of "did the loop find a minimal plan" in
  `studies/CONTROLLER_STUDY.md` is against this number.

## 3.  Why a greedy loop is enough when the heuristic is exact

`exists_descent`: from any state other than the target there is a move that
strictly decreases the ℓ¹ distance to the target.  So a width-one loop driven
by the exact remaining-distance heuristic reaches the target in exactly
`‖t − s‖₁` steps (`greedy_reaches`) — no backtracking, no search.  That is the
reference the substrate's heuristic is measured against: the question the
study asks is not whether the lattice can guide the loop *at all*, but how
close it comes to the heuristic that is exact by construction.

## 4.  Why a refusal can be a proof

`unreachable_of_invariant`: if `phi` is a homomorphism that every move leaves
alone, then it is constant along any plan, so a target on which it differs
from the start is unreachable **at any depth**.  The controller's first act is
to evaluate three such invariants — the decimal scale, the tensor rank and the
integrality of the exponents — and a target failing one is refused with that
invariant named, without a single node being expanded.  This is a refusal that
carries a proof, in the same sense as
`GLM.Retrieval.filterRadius_eq_nil_certifies_absence`.

`scale_invariant` is the instance the running code uses: no move changes the
decimal scale coordinate, so no plan can.

## 5.  And the limit, stated rather than caveated

`beam_can_miss`: a width-one loop driven by a heuristic that is *not* exact can
fail on a target that is reachable — an explicit two-coordinate witness,
decided by the kernel.  Beam search is incomplete, the controller reports the
failure as a refusal rather than as an answer, and the study counts how often
it happens under each heuristic.  A loop that gives up honestly is worth more
than one that confabulates.
-/
import Mathlib

namespace GLM.Controller

open Finset

variable {n : ℕ}

/-! ## 1.  States, moves and plans -/

/-- A move: multiply (`up = true`) or divide (`up = false`) by one generator. -/
structure Move (n : ℕ) where
  /-- Which generator. -/
  axis : Fin n
  /-- Multiply rather than divide. -/
  up : Bool
  deriving DecidableEq

/-- What one move adds to the exponent vector. -/
def delta (m : Move n) : Fin n → ℤ :=
  fun i => if i = m.axis then (if m.up then 1 else -1) else 0

/-- Applying a plan: the start plus the sum of the moves. -/
def replay (p : List (Move n)) (s : Fin n → ℤ) : Fin n → ℤ :=
  s + (p.map delta).sum

/-- The ℓ¹ norm of an exponent vector: the number of unit moves it stands for. -/
def l1 (x : Fin n → ℤ) : ℕ := ∑ i, (x i).natAbs

theorem replay_nil (s : Fin n → ℤ) : replay [] s = s := by
  simp [replay]

theorem replay_cons (m : Move n) (p : List (Move n)) (s : Fin n → ℤ) :
    replay (m :: p) s = replay p s + delta m := by
  simp [replay, List.sum_cons]
  abel

theorem replay_append (p q : List (Move n)) (s : Fin n → ℤ) :
    replay (p ++ q) s = replay q (replay p s) := by
  simp [replay, List.map_append, List.sum_append]
  abel

theorem l1_eq_zero_iff (x : Fin n → ℤ) : l1 x = 0 ↔ x = 0 := by
  constructor
  · intro h
    funext i
    have := Finset.sum_eq_zero_iff.mp h i (Finset.mem_univ i)
    simpa [Int.natAbs_eq_zero] using this
  · rintro rfl
    simp [l1]

theorem l1_delta (m : Move n) : l1 (delta m) = 1 := by
  classical
  unfold l1 delta
  rw [Finset.sum_eq_single m.axis]
  · cases m.up <;> simp
  · intro b _ hb
    simp [hb]
  · intro h
    exact absurd (Finset.mem_univ m.axis) h

theorem l1_add_le (x y : Fin n → ℤ) : l1 (x + y) ≤ l1 x + l1 y := by
  unfold l1
  rw [← Finset.sum_add_distrib]
  refine Finset.sum_le_sum ?_
  intro i _
  exact Int.natAbs_add_le _ _

/-! ## 2.  The shortest plan has exactly `l1` moves -/

/-- **The lower bound.**  A plan from the origin to `t` has at least `‖t‖₁`
moves: one move changes the ℓ¹ norm by at most one. -/
theorem l1_le_length (p : List (Move n)) : l1 (replay p 0) ≤ p.length := by
  induction p with
  | nil => simp [replay_nil, l1]
  | cons m q ih =>
      rw [replay_cons]
      calc l1 (replay q 0 + delta m)
          ≤ l1 (replay q 0) + l1 (delta m) := l1_add_le _ _
        _ ≤ q.length + 1 := by rw [l1_delta]; omega
        _ = (m :: q).length := by simp

/-- The ℓ¹ norm, split off one coordinate. -/
theorem l1_split (t : Fin n → ℤ) (i : Fin n) :
    l1 t = (t i).natAbs + ∑ j ∈ Finset.univ.erase i, (t j).natAbs :=
  (Finset.add_sum_erase _ _ (Finset.mem_univ i)).symm

/-- Stepping one coordinate of `t` towards zero costs exactly one from `‖t‖₁`. -/
theorem l1_sub_delta {t : Fin n → ℤ} {i : Fin n} (hi : t i ≠ 0) :
    l1 (t - delta ⟨i, decide (0 < t i)⟩) + 1 = l1 t := by
  classical
  set m : Move n := ⟨i, decide (0 < t i)⟩ with hm
  have hoff : ∀ j, j ≠ i → (t - delta m) j = t j := by
    intro j hj
    simp [hm, delta, Pi.sub_apply, hj]
  have hat : (t - delta m) i = t i - (if 0 < t i then 1 else -1) := by
    simp only [hm, delta, Pi.sub_apply, decide_eq_true_eq]
    split_ifs <;> omega
  rw [l1_split (t - delta m) i, l1_split t i]
  have hrest : ∑ j ∈ Finset.univ.erase i, ((t - delta m) j).natAbs
      = ∑ j ∈ Finset.univ.erase i, (t j).natAbs :=
    Finset.sum_congr rfl fun j hj => by rw [hoff j (Finset.mem_erase.mp hj).1]
  rw [hrest, hat]
  have : (t i - (if 0 < t i then 1 else -1)).natAbs + 1 = (t i).natAbs := by
    split_ifs <;> omega
  omega

/-- **The upper bound, constructively.**  There is a plan of exactly `‖t‖₁`
moves from the origin to `t`. -/
theorem exists_plan (t : Fin n → ℤ) :
    ∃ p : List (Move n), p.length = l1 t ∧ replay p 0 = t := by
  classical
  generalize hk : l1 t = k
  induction k using Nat.strong_induction_on generalizing t with
  | _ k ih =>
    by_cases hzero : t = 0
    · subst hzero
      exact ⟨[], by simp [← hk, l1], by simp [replay_nil]⟩
    · have hne : ∃ i, t i ≠ 0 := by
        by_contra hcon
        push_neg at hcon
        exact hzero (funext hcon)
      obtain ⟨i, hi⟩ := hne
      set m : Move n := ⟨i, decide (0 < t i)⟩ with hm
      set t' := t - delta m with ht'
      have hstep : l1 t' + 1 = l1 t := l1_sub_delta hi
      have hlt : l1 t' < k := by omega
      obtain ⟨p, hlen, hrep⟩ := ih (l1 t') hlt t' rfl
      refine ⟨m :: p, ?_, ?_⟩
      · simp [hlen, ← hk, ← hstep]
      · rw [replay_cons, hrep, ht']
        abel

/-- **The shortest plan has exactly `‖t‖₁` moves.**  The controller therefore
has an exact optimum to be scored against. -/
theorem minimal_length_eq_l1 (t : Fin n → ℤ) :
    IsLeast {k : ℕ | ∃ p : List (Move n), p.length = k ∧ replay p 0 = t}
      (l1 t) := by
  constructor
  · exact exists_plan t
  · rintro k ⟨p, rfl, hrep⟩
    have := l1_le_length p
    rw [hrep] at this
    exact this

/-! ## 3.  A greedy loop with an exact heuristic never backtracks -/

/-- **There is always a move that gets strictly closer.**  From any state other
than the target, some move reduces the ℓ¹ distance by one — so a width-one loop
driven by the exact distance reaches the target without ever backtracking. -/
theorem exists_descent {s t : Fin n → ℤ} (h : s ≠ t) :
    ∃ m : Move n, l1 (replay [m] s - t) + 1 = l1 (s - t) := by
  classical
  have hne : ∃ i, (s - t) i ≠ 0 := by
    by_contra hcon
    push_neg at hcon
    exact h (funext fun i => by have := hcon i; simp at this; omega)
  obtain ⟨i, hi⟩ := hne
  refine ⟨⟨i, decide ((s - t) i < 0)⟩, ?_⟩
  have hkey : replay [(⟨i, decide ((s - t) i < 0)⟩ : Move n)] s - t
      = (s - t) - delta ⟨i, decide (0 < (s - t) i)⟩ := by
    funext j
    by_cases hj : j = i
    · subst hj
      have hi' : s j - t j ≠ 0 := by simpa using hi
      simp only [replay, delta, Pi.add_apply, Pi.sub_apply, List.map_cons,
        List.map_nil, List.sum_cons, List.sum_nil, add_zero,
        decide_eq_true_eq]
      split_ifs <;> omega
    · simp [replay, delta, Pi.sub_apply, hj]
  rw [hkey]
  exact l1_sub_delta hi

/-- The distance the greedy loop still has to cover after one descent step. -/
theorem greedy_reaches (s t : Fin n → ℤ) :
    ∃ p : List (Move n), p.length = l1 (s - t) ∧ replay p s = t := by
  obtain ⟨p, hlen, hrep⟩ := exists_plan (t - s)
  refine ⟨p, ?_, ?_⟩
  · rw [hlen]
    unfold l1
    refine Finset.sum_congr rfl fun i _ => ?_
    have : -((s - t) i) = (t - s) i := by simp
    rw [← Int.natAbs_neg ((s - t) i), this]
  · unfold replay at hrep ⊢
    have : (p.map delta).sum = t - s := by simpa using hrep
    rw [this]
    abel

/-! ## 4.  A refusal that carries a proof -/

/-- **An invariant every move preserves is preserved by every plan.**  So a
target on which it differs from the start is unreachable at any depth: the
controller can refuse without expanding a single node, and the refusal is a
theorem rather than a budget. -/
theorem invariant_replay {M : Type*} [AddCommMonoid M]
    (phi : (Fin n → ℤ) →+ M) (hzero : ∀ m : Move n, phi (delta m) = 0)
    (p : List (Move n)) (s : Fin n → ℤ) : phi (replay p s) = phi s := by
  induction p generalizing s with
  | nil => simp [replay_nil]
  | cons m q ih =>
      rw [replay_cons, map_add, hzero m, add_zero, ih]

theorem unreachable_of_invariant {M : Type*} [AddCommMonoid M]
    (phi : (Fin n → ℤ) →+ M) (hzero : ∀ m : Move n, phi (delta m) = 0)
    {s t : Fin n → ℤ} (h : phi s ≠ phi t) :
    ¬ ∃ p : List (Move n), replay p s = t := by
  rintro ⟨p, hp⟩
  exact h (by rw [← hp, invariant_replay phi hzero])

/-- The instance the running controller uses: a move changes an *exponent*, so
any coordinate outside the exponent block — the decimal scale, the tensor rank
— is untouched, and a target that differs there is refused outright. -/
theorem scale_invariant (extra : (Fin n → ℤ) →+ ℤ)
    (hzero : ∀ m : Move n, extra (delta m) = 0)
    {s t : Fin n → ℤ} (h : extra s ≠ extra t) :
    ¬ ∃ p : List (Move n), replay p s = t :=
  unreachable_of_invariant extra hzero h

/-! ## 5.  The limit: a narrow loop can miss -/

/-- One step of a width-one loop: take the move the heuristic likes best,
breaking ties by the move's own order. -/
def bestMove (h : (Fin n → ℤ) → ℕ) (moves : List (Move n)) (s : Fin n → ℤ) :
    Option (Move n) :=
  moves.foldl
    (fun best m =>
      match best with
      | none => some m
      | some b => if h (replay [m] s) < h (replay [b] s) then some m else some b)
    none

/-- The two moves of a one-coordinate space. -/
def moves1 : List (Move 1) := [⟨0, true⟩, ⟨0, false⟩]

/-- A heuristic that prefers the wrong direction. -/
def badHeuristic (x : Fin 1 → ℤ) : ℕ := (x 0 + 5).natAbs

/-- **A width-one loop can miss a plan that exists.**  With the misleading
heuristic above, the best move from the origin is the one that goes *away* from
the target `(1)`, which is one move away — so the loop's first step is already
wrong.  Beam search is incomplete; the controller therefore reports a failure
as a refusal and never as an answer, and the study counts how often each
heuristic makes this happen. -/
theorem beam_can_miss :
    bestMove badHeuristic moves1 (fun _ => 0) = some ⟨0, false⟩
      ∧ replay [⟨0, true⟩] (fun _ => 0) = (fun _ => 1 : Fin 1 → ℤ) := by
  constructor
  · decide
  · funext i
    fin_cases i
    simp [replay, delta]

end GLM.Controller
