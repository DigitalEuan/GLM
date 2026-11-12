module

public import RequestProject.GLM.Rule30.MachineModel

/-!
# Problem 3: the quantifiers made explicit

Round 6 ledger reconciliation (feedback #3, section 1).  `Problem3` (in `MachineModel.lean`) says
that no Turing machine computing the centre column has running time `o(n)`.  "Not `o(n)`" only
says the running time is at least `ε · n` **infinitely often** (along some subsequence of inputs);
it is weaker than an eventual lower bound.

* `Problem3Eventual` : every such machine has running time `Ω(n)` **eventually**, i.e.
  `n = O(time(n))`.  This is the reading closest to "computing `a(n)` needs at least order `n` work".
* `problem3_of_eventual` : the eventual form implies `Problem3` (proved).

Both are open.  Both ask for a lower bound that is exponential in the input length (`≈ log₂ n`
bits), which is beyond current lower-bound techniques for any explicit function.
-/

@[expose] public section

namespace GLM.Rule30

open Asymptotics Filter

/-- **Problem 3, eventual form** (open): every Turing machine computing the centre column needs
running time at least a constant times `n`, for all large `n`. -/
def Problem3Eventual : Prop :=
  ∀ M : Turing.TM2ComputableInTime Computability.finEncodingNatBool
      Computability.finEncodingBoolBool centerCol,
    (fun n : ℕ => (n : ℝ)) =O[atTop]
      (fun n : ℕ => (M.time (Computability.finEncodingNatBool.encode n).length : ℝ))

/-- The eventual form implies `Problem3`. -/
theorem problem3_of_eventual (h : Problem3Eventual) : Problem3 := by
  intro M ho
  have hself : (fun n : ℕ => (n : ℝ)) =o[atTop] (fun n : ℕ => (n : ℝ)) := (h M).trans_isLittleO ho
  refine isLittleO_irrefl ?_ hself
  refine (eventually_gt_atTop 0).frequently.mono (fun n hn => ?_)
  simp only [ne_eq, Nat.cast_eq_zero]
  omega

end GLM.Rule30
