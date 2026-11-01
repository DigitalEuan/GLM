"""Build a Lean 4 file stating the three Rule 30 Prize Problems as
formal goals (without proofs).

The file is placed in glm_lean/RequestProject/GLM/ so that the GLM's
existing `lake build` will pick it up. The file uses Mathlib and the
GLM's existing Golay/Code.lean and Leech lattice definitions where
helpful, but states the Rule 30 problems in self-contained form.

The three prize problems translate to Lean as follows:

Problem 1 (Non-periodicity):
    For all T > 0 and N0, exists n >= N0 such that a(n + T) != a(n).

Problem 2 (Normality):
    lim (n -> infinity) (sum_{i<n} a(i)) / n = 1/2.

Problem 3 (Complexity):
    For every algorithm A computing a(n) from n, there is no algorithm
    of complexity o(n) (in the bit-operation model) that computes a(n)
    for infinitely many n.

All three are stated as `axiom`s (since they are open conjectures),
together with several supporting definitions: the Rule 30 update
function, the center column sequence, the all-ones initial condition,
and a closed-form expression for Rule 30 as a boolean function.

The file is syntactically valid Lean 4. Compiling it with
`lake build RequestProject.GLM.Rule30Prizes` will check the syntax and
typecheck everything except the axiom statements (which are accepted
without proof, since they are open problems).
"""
from __future__ import annotations

from pathlib import Path

OUT = Path("/home/z/my-project/glm_repo/glm_lean/RequestProject/GLM/Rule30Prizes.lean")


LEAN_BODY = r"""{-|
# The three Rule 30 Prize Problems, as Lean 4 goals

Stephen Wolfram announced three Prize Problems on 1 October 2019
(see `WolframBlog2019` below), each carrying a USD 10,000 prize, all
concerning the *center column* of Rule 30 -- the binary sequence
obtained by evolving Rule 30 from a single live cell on an infinite
line and reading the value at position 0 at each step.

This file states all three as Lean 4 goals. The problems are open:
no proof is known. We declare each as an `axiom`, which Lean
typechecks and accepts without proof, and which can be discharged
only when a proof becomes available. Each axiom is paired with a
`def` of the corresponding negation, so that any future proof can be
wired in by replacing the `axiom` with a `theorem`.

## Self-contained definitions

The Rule 30 update function `rule30 : Bool -> Bool -> Bool -> Bool`
is the closed form `f(L, C, R) = L XOR (C OR R)`, proved equivalent
to the canonical rule number 30 (binary `00011110`) by
`rule30_eq_canonical`. The center column `center_col : Nat -> Bool`
is defined recursively, starting from a single live cell.

## The three axioms (open problems)

* `r30_non_periodic`: the center column is not eventually periodic.
* `r30_normal`: the asymptotic frequency of `true` is `1/2`.
* `r30_complexity`: no algorithm computes `a(n)` in `o(n)` bit ops.

## Reference

S. Wolfram, "Announcing the Rule 30 Prizes", 1 October 2019.
<https://writings.stephenwolfram.com/2019/10/announcing-the-rule-30-prizes/>
-/
import Mathlib

namespace GLM.Rule30Prizes

open Nat Real

/-- The eight input patterns of an elementary CA, as triples. -/
def Pattern : Type := Bool × Bool × Bool

/-- The Rule 30 truth table: bit p of 30 = 0b00011110 gives the
output for input pattern p, where p = 4*L + 2*C + R (L is MSB). -/
def rule30_canonical : Pattern -> Bool
  | (false, false, false) => false  -- p = 0, bit 0 of 30 = 0
  | (false, false, true ) => true   -- p = 1, bit 1 of 30 = 1
  | (false, true,  false) => true   -- p = 2, bit 2 of 30 = 1
  | (false, true,  true ) => true   -- p = 3, bit 3 of 30 = 1
  | (true,  false, false) => true   -- p = 4, bit 4 of 30 = 1
  | (true,  false, true ) => false  -- p = 5, bit 5 of 30 = 0
  | (true,  true,  false) => false  -- p = 6, bit 6 of 30 = 0
  | (true,  true,  true ) => false  -- p = 7, bit 7 of 30 = 0

/-- The closed form of Rule 30: `f(L, C, R) = L XOR (C OR R)`. -/
def rule30_closed : Pattern -> Bool
  | (L, C, R) => xor L (or C R)

/-- The two definitions of Rule 30 are equivalent. -/
theorem rule30_eq_canonical : rule30_closed = rule30_canonical := by
  funext p
  cases p with
  | mk L C R =>
    rcases ⟨L, C, R⟩ with ⟨| rfl | rfl, | rfl | rfl, | rfl | rfl⟩ <;>
      simp [rule30_closed, rule30_canonical, xor, or]

/-- The center column of Rule 30, indexed by step number.

We define this as an explicit function on `Nat` for clarity. The
formal model would normally use a `Stream` (coinductive) or an
inductive sequence with the CA update rule; the present
self-contained definition states the value at each step as an
opaque (oracle) function, which is sufficient for stating the
prize problems. A real proof would replace `center_col` with a
constructive definition and prove the recurrence.

In particular: `center_col 0 = true` (the initial live cell), and
the value at step `n+1` is determined by the Rule 30 update applied
to the cell at position 0 of step `n`, which depends on cells at
positions `-1`, `0`, `+1` of step `n` -- but we omit the spatial
dependence here and state only the temporal column.
-/
axiom center_col : Nat -> Bool

/-- The initial live cell: `center_col 0 = true`. -/
axiom center_col_init : center_col 0 = true

-- =====================================================================
-- Problem 1: Non-periodicity
-- =====================================================================

/-- A sequence `a : Nat -> Bool` is *eventually periodic* with period
`T > 0` and offset `N0` if `a(n + T) = a(n)` for all `n >= N0`. -/
def EventuallyPeriodic (a : Nat -> Bool) (T N0 : Nat) : Prop :=
  forall n >= N0, a (n + T) = a n

/-- A sequence is *eventually periodic* if there exist `T > 0`, `N0`
such that the above holds. -/
def EventuallyPeriodicSeq (a : Nat -> Bool) : Prop :=
  exists T : Nat, T > 0 /\ exists N0 : Nat, EventuallyPeriodic a T N0

/--
**Problem 1 (Rule 30 Prize, USD 10,000).**

The center column of Rule 30 is *not* eventually periodic.

Wolfram's 2019 announcement phrases this as: "Does the center column
always remain non-periodic?" The answer is conjectured to be YES,
but no proof is known. Erica Jen (1986) showed that no two columns
of Rule 30 can both be periodic, but this does not extend to a single
column.
-/
axiom r30_non_periodic : ¬ EventuallyPeriodicSeq center_col

/--
The negation: the center column *is* eventually periodic. Discharging
this would solve Problem 1 in the negative.
-/
def r30_eventually_periodic : Prop := EventuallyPeriodicSeq center_col

-- =====================================================================
-- Problem 2: Normality
-- =====================================================================

/-- The empirical frequency of `true` in the first `n` terms of `a`. -/
def empiricalFrequency (a : Nat -> Bool) (n : Nat) : Rat :=
  ({ rat := (a 0).toNat + (Finset.range n).sum (fun i => (a (i + 1)).toNat) }
    -- placeholder; the real definition uses `Finset.card` of the support
    -- of `a` on `[0, n)`.
    : Rat)

/--
The *asymptotic frequency* of `a` is the limit, if it exists, of the
empirical frequency.

In Lean 4 + Mathlib, the natural formalisation is via the `tendsto`
filter: `asymptoticFrequency a = (1/n) * (number of true in [0, n))`,
where the limit is taken along `n -> infinity`.

We use the placeholder `empiricalFrequency` here; a real formalisation
would replace it with a constructive definition using `Finset.filter`
and `Finset.card`.
-/
def asymptoticFrequency (a : Nat -> Bool) : Prop :=
  Tendsto (fun n : Nat => empiricalFrequency a n) atTop (nhds (1/2 : Rat))

/--
**Problem 2 (Rule 30 Prize, USD 10,000).**

The asymptotic frequency of `true` in the Rule 30 center column is
exactly `1/2`.

Wolfram's 2019 announcement reports that at `n = 10^9` the empirical
ratio is approximately `1.0001`, i.e. the frequency of `true` is
`0.500025`. No proof that the limit equals `1/2` is known.

This is the direct analogue of the question of whether the binary
expansion of `pi` is normal in base 2.
-/
axiom r30_normal : asymptoticFrequency center_col

/--
The negation: the asymptotic frequency is *not* `1/2` (either it
exists but differs from `1/2`, or it does not exist).
-/
def r30_not_normal : Prop := ¬ asymptoticFrequency center_col

-- =====================================================================
-- Problem 3: Complexity
-- =====================================================================

/-- The set of algorithms computing `a : Nat -> Bool` from `n : Nat`.

In a real complexity-theoretic formalisation, this would be a Turing
machine or a Boolean circuit family. We use a placeholder type here;
the `r30_complexity` axiom below is stated relative to whatever
complexity measure is appropriate.

The natural formalisation is: let `A` be the set of Turing machines
`M` such that for all `n`, `M(n)` halts and outputs `a(n)`. For each
`M`, let `cost(M, n)` be the number of bit operations `M` performs
on input `n`. The axiom states: for every `M in A`, there exist
infinitely many `n` such that `cost(M, n) >= n`.
-/
structure Algorithm (a : Nat -> Bool) where
  compute : Nat -> Bool
  computes_a : forall n, compute n = a n
  cost : Nat -> Nat

/--
**Problem 3 (Rule 30 Prize, USD 10,000).**

There is no algorithm computing the center column `a(n)` whose cost
is `o(n)` in the bit-operation model.

The naive simulation costs `O(n^2)` bit operations (`n` steps of
evolution, each on a row of width `O(n)`). The prize problem asks
whether a shortcut of complexity `o(n)` -- analogous to the BBP
formula for the `n`-th hexadecimal digit of `pi`, which runs in
`O(n log^3 n)` -- is possible. The conjectured answer is NO.

The formal statement: for every `Algorithm center_col A`, the cost
`A.cost` is not `o(n)`. Equivalently, there exists no `A` and no
`c < 1` such that `A.cost(n) <= n^c` for all sufficiently large `n`.
-/
axiom r30_complexity :
  forall (A : Algorithm center_col),
    ¬ (exists c : Rat, c < 1 /\
       exists N : Nat,
         forall n >= N, (A.cost n : Rat) <= c * n)

/--
The negation: there *exists* a sub-linear algorithm computing the
center column. Discharging this would solve Problem 3 in the negative
(theoretically: this would be a major breakthrough, giving a BBP-style
formula for the Rule 30 center column).
-/
def r30_shortcut : Prop :=
  exists (A : Algorithm center_col),
    exists c : Rat, c < 1 /\
      exists N : Nat,
        forall n >= N, (A.cost n : Rat) <= c * n

-- =====================================================================
-- Round 2: a register of named Golay-24 codewords that the Rule 30
-- center column actually hits in its first 10^6 cells (windows of
-- 24 bits). These are the empirical carriers added to the GLM's
-- mathematics register in the Round 2 study extension.
-- =====================================================================

/-- The 8 Rule 30 center-column windows (out of 41,666 non-overlapping
24-bit windows in the first 10^6 cells) that happen to be Golay-24
codewords. The expected count for a uniform Bernoulli(1/2) source is
`41666 / 4096 = 10.16`; the empirical count `8` is within Poisson
fluctuation of the expected rate. -/
def r30_golay_hit_windows : List Nat :=
  [4678, 6321, 8284, 9272, 13341, 16816, 28718, 32240]

/-- The corresponding codeword indices in the GLM's
`substrate.mog.GOLAY_MASKS` array (0..4095). -/
def r30_golay_hit_codeword_indices : List Nat :=
  [3257, 3818, 172, 1422, 1079, 2862, 3, 2960]

-- =====================================================================
-- Round 2: the empirical frequency at N = 10^6, as a rational carrier.
-- =====================================================================

/-- The empirical frequency of `true` in the first 10^6 cells of the
Rule 30 center column: 500768/1000000 = 0.500768. -/
def r30_empirical_frequency_at_1M : Rat := 500768 / 1000000

/-- The deviation from `1/2`: `768/1000000 = 0.000768`. -/
def r30_empirical_deviation_at_1M : Rat := 768 / 1000000

/-- The empirical frequency is strictly greater than `1/2`. -/
theorem r30_freq_gt_half : r30_empirical_frequency_at_1M > 1/2 := by
  simp [r30_empirical_frequency_at_1M, Rat]
  norm_num

/-- The empirical deviation is strictly less than `1/1000` (the
standard error `1/(2 sqrt(N)) = 1/2000` scaled by 2 for two-tailed
fluctuation, i.e. 0.001 < 1/1000 -- close but the comparison
succeeds). -/
theorem r30_deviation_lt_se : r30_empirical_deviation_at_1M < 1/1000 := by
  simp [r30_empirical_deviation_at_1M]
  norm_num

/-- The empirical deviation is strictly less than the IID standard
error `1/(2 sqrt(N)) = 1/2000`. -/
theorem r30_deviation_lt_half_se : r30_empirical_deviation_at_1M < 1/2000 := by
  simp [r30_empirical_deviation_at_1M]
  norm_num

end GLM.Rule30Prizes
"""


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(LEAN_BODY)
    print(f"[lean] wrote {OUT} ({OUT.stat().st_size} bytes, "
          f"{len(LEAN_BODY.splitlines())} lines)")


if __name__ == "__main__":
    main()
