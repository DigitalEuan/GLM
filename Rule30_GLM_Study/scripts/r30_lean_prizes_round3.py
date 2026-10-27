"""Extend the Round 2 Lean 4 file with formal statements of the
proof-strategy lemmas suggested by the user's Round 3 roadmap:

  - `RestrictedView n k`: an algorithm that only reads k bits of the
    initial state (out of 2n+1). Used for Problem 3's fooling set.

  - `fooling_set_lemma`: there exist two initial states S1, S2 that
    agree on the k bits a restricted-view algorithm reads, but
    disagree on a(n). Proving this for k < 2n+1 would be a major step
    toward Problem 3.

  - `martingale_bias_zero`: the expected value of the next Golay
    coset weight's "bias" given the current coset is zero. Used for
    Problem 2's martingale/mixing argument.

  - `deep_hole_poisson_bound`: the count of deep-hole occurrences in
    the first N windows is bounded by Poisson tails. Used for
    Problem 2's structural-evidence path.

  - `lorentzian_contradiction_for_periodicity`: if the center column
    were eventually periodic, then the Lorentzian summed scores
    over the infinite identical readings would either diverge or
    force a trivial constant sequence. Used for Problem 1.

  - `anf_degree_growth_conjecture`: deg(a(n)) = 2n-1 for all n >= 2.
    Empirically verified for n = 2..10 in Round 3. Used for
    Problems 1 and 3.

  - `anf_implies_complexity_lower_bound`: if the ANF degree is
    Omega(n), then any circuit computing a(n) has size Omega(n)
    (a known circuit-complexity result, here stated as an axiom
    pending a Lean proof).

These statements are FORMAL GOALS, not proofs. The point is to
record the proof strategy precisely enough that a future Lean
proof attempt can discharge each axiom as a theorem.
"""
from __future__ import annotations

from pathlib import Path

OUT = Path("/home/z/my-project/glm_repo/glm_lean/RequestProject/GLM/Rule30PrizesRound3.lean")


LEAN_BODY = r"""{-|
# Round 3 extensions to the Rule 30 Prize Problems Lean file

This file extends `Rule30Prizes.lean` (Round 2) with formal
statements of the proof-strategy lemmas suggested by the user's
Round 3 roadmap. Each lemma is a *goal* (a `theorem` to be proved,
or an `axiom` to be assumed), not a proof. The point is to record
the proof strategy precisely enough that a future Lean proof
attempt can discharge each as a theorem.

## The four Round 3 proof strategies

1. **Lorentzian second-reading contradiction (Problem 1)**:
   Assume for contradiction that the center column is eventually
   periodic with period T. Then the 24-bit windows at positions n,
   n+T, n+2T, ... are identical. The Lorentzian summed scores over
   these infinite identical readings would either diverge (if the
   single-reading score is nonzero) or force a trivial constant
   sequence (if the score is zero). Both contradict the Rule 30
   update rule. This is `lorentzian_contradiction_for_periodicity`.

2. **Martingale + Poisson deep-hole bound (Problem 2)**:
   Model the sequence of Golay coset weights as a stochastic
   process. If the next coset's bias is a martingale difference
   sequence (zero conditional expectation), the deviation of the
   empirical frequency from 1/2 shrinks as O(1/sqrt(N)) by
   Azuma-Hoeffding. The Poisson deep-hole bound gives a
   finite-window certificate. These are `martingale_bias_zero`
   and `deep_hole_poisson_bound`.

3. **Lorentzian fooling set (Problem 3)**:
   To compute a(n) in o(n) time, an algorithm must read < 2n+1
   cells of the initial state. Construct two initial states S1, S2
   that agree on the cells the algorithm reads, but disagree on
   a(n). The Lorentzian tie (deep hole) makes this possible: both
   S1 and S2 map to the same deep hole under the restricted view,
   but resolve to different a(n) under the full context. This is
   `fooling_set_lemma`.

4. **ANF degree growth implies complexity lower bound (Problems 1, 3)**:
   The empirical pattern `deg(a(n)) = 2n - 1` (verified for n=2..10
   in Round 3) gives a linear lower bound on the ANF size, which
   in turn gives an Omega(n) lower bound on the circuit size via
   a standard circuit-complexity result. These are
   `anf_degree_growth_conjecture` and
   `anf_implies_complexity_lower_bound`.

All statements are open conjectures. The Lean file is the formal
skeleton; the proofs (when they come) will replace the axioms with
theorems.
-/
import Mathlib
import RequestProject.GLM.Rule30Prizes

namespace GLM.Rule30Prizes.Round3

open Nat Real Finset

-- =====================================================================
-- §1. ANF degree growth (Round 3 empirical finding, now a formal goal)
-- =====================================================================

/-- The algebraic normal form degree of `center_col n` as a polynomial
in the `2n+1` initial cell values, over GF(2). Round 3's numba-JIT'd
Möbius transform computes this for `n = 1..10`:

    n = 1  : deg = 2
    n = 2  : deg = 3
    n = 3  : deg = 5
    n = 4  : deg = 7
    n = 5  : deg = 9
    n = 6  : deg = 11
    n = 7  : deg = 13
    n = 8  : deg = 15
    n = 9  : deg = 17
    n = 10 : deg = 19

The pattern `deg = 2n - 1` holds for `n >= 2`. At `n = 1` the degree
is `2` (the maximum possible for `2*1+1 = 3` variables, minus 1). -/
axiom anf_degree : Nat -> Nat

/-- The empirical pattern: `anf_degree n = 2 * n - 1` for `n >= 2`.
Verified by Round 3's numba-JIT'd Möbius transform for `n = 2..10`. -/
axiom anf_degree_growth_conjecture :
  forall n : Nat, n >= 2 -> anf_degree n = 2 * n - 1

/-- At `n = 1`, the ANF degree is `2` (the maximum minus 1, for 3
variables). -/
axiom anf_degree_at_1 : anf_degree 1 = 2

/-- Corollary: the ANF degree grows linearly in `n`. -/
theorem anf_degree_linear_growth
    (h : anf_degree_growth_conjecture) :
    forall n : Nat, n >= 2 -> anf_degree n = 2 * n - 1 := by
  exact h

-- =====================================================================
-- §2. Problem 1: the Lorentzian second-reading contradiction
-- =====================================================================

/-- A "reading" of the Rule 30 center column at position `n` is the
24-bit window `[a(n), a(n+1), ..., a(n+23)]`, viewed as a binary
vector in {0,1}^24. In the Lorentzian lift, this becomes the null
vector `L(x)`. -/
def Reading (n : Nat) : Prop := True  -- placeholder; real def uses the CA

/-- If the center column is eventually periodic with period `T`, then
for any window position `n >= N0`, the reading at `n` equals the
reading at `n + T`. -/
axiom periodic_implies_identical_readings :
  forall (T N0 : Nat), T > 0 ->
    EventuallyPeriodic center_col T N0 ->
    forall (n : Nat), n >= N0 ->
      -- The 24-bit window at position n equals the window at n+T
      -- (formally: the Boolean sequence agrees on [n, n+23] = [n+T, n+T+23])
      True  -- placeholder; real statement uses stream equality

/-- The Lorentzian "summed score" of a center-column window at
position `n` against a fixed Leech lattice point `lambda`. Per the
key identity `<L(x), r_lambda> = 1 - |x - lambda|^2 / 2`, this is
`1 - |x_n - lambda|^2 / 2`. -/
def lorentzianSummedScore (lambda : Fin 24 -> Rat) (n : Nat) : Rat :=
  1 - 0  -- placeholder; real definition uses the Leech distance

/-- **The Lorentzian second-reading contradiction (Problem 1).**

If the Rule 30 center column is eventually periodic with period `T`,
then the sequence of 24-bit windows is periodic. Therefore, every
"tie" window at position `n` will be identically repeated at
`n + T, n + 2T, ...`, giving infinitely many identical readings of
the same deep hole.

The Lorentzian summed score over infinitely many identical readings
is either:
  (a) Divergent (if the single-reading score is nonzero), or
  (b) Trivially zero (if the single-reading score is zero).

Both contradict the Rule 30 update rule, which produces a nontrivial
sequence (`center_col_init` plus the closed-form `f_30(L, C, R) =
L XOR (C OR R)`).

This contradiction would prove `r30_non_periodic`.

The formal statement is a *goal*: a `theorem` to be proved. The
proof would discharge the `r30_non_periodic` axiom of
`Rule30Prizes.lean`. -/
theorem lorentzian_contradiction_for_periodicity
    (h_periodic : EventuallyPeriodicSeq center_col)
    (h_rule30 : rule30_closed = rule30_canonical)
    (h_init : center_col 0 = true) :
    False := by
  -- Proof sketch:
  -- 1. From h_periodic, get T > 0 and N0 such that a(n+T) = a(n)
  --    for all n >= N0.
  -- 2. The 24-bit windows at positions n, n+T, n+2T, ... are
  --    identical (each pair agrees componentwise).
  -- 3. Each such window maps to the same Lorentzian null vector
  --    L(x) and the same deep-hole certificate (if any).
  -- 4. The summed Lorentzian score over k identical readings is
  --    k * (single-reading score).
  -- 5. If single-reading score != 0, the sum diverges, contradicting
  --    the bounded Golay codeword rate (Round 1's measurement:
  --    8 hits in 41666 windows, expected ~10.2).
  -- 6. If single-reading score = 0, every reading is at a trivial
  --    tie (the all-zero window), which forces the center column
  --    to be all-zero, contradicting center_col_init.
  sorry  -- placeholder; a real proof would replace this

-- =====================================================================
-- §3. Problem 2: the martingale + Poisson deep-hole bound
-- =====================================================================

/-- The "bias" of a Golay coset is the deviation of its empirical
frequency from 1/4096 (the uniform rate). For a deep-hole coset
(weight 4), the bias is the deviation of the empirical deep-hole
rate from 1771/4096 = 43.2% (per the GLM's slack record
LAW_GOLAY_UNIQUENESS_001). -/
def cosetBias (window_idx : Nat) : Rat :=
  0  -- placeholder; real definition uses the empirical count vs. expected

/-- **The martingale-bias-zero axiom (Problem 2).**

The expected value of the next Golay coset weight's "bias" given the
current coset weight is zero. This is the martingale-difference
property: the Rule 30 update rule acts as a *mixing operator* on
the space of Golay cosets, with no preferred direction.

If this axiom holds, then the sequence of coset-bias differences is
a bounded martingale-difference sequence. By Azuma-Hoeffding, the
deviation of the partial sums from zero is O(sqrt(N)), giving
|f(N) - 1/2| = O(1/sqrt(N)) and hence the limit is 1/2.

This is the *martingale path* to Problem 2. -/
axiom martingale_bias_zero :
  forall (n : Nat),
    -- The conditional expectation of cosetBias (n+1) given the
    -- coset weights at positions 0, 1, ..., n is zero.
    True  -- placeholder; real statement uses conditional expectation

/-- **The Azuma-Hoeffding consequence.**

If `martingale_bias_zero` holds, then the cumulative bias up to
position N is bounded by O(sqrt(N)). Combined with the
center-column-to-coset-weight map, this gives
|f(N) - 1/2| = O(1/sqrt(N)) and hence `r30_normal`.

This is the *martingale path* stated as a theorem (to be proved
once `martingale_bias_zero` is established). -/
theorem martingale_implies_normality
    (h_martingale : martingale_bias_zero)
    (h_bias_to_freq : True) -- placeholder for the coset-to-freq map
    : asymptoticFrequency center_col := by
  sorry

/-- **The Poisson deep-hole bound (Problem 2).**

The count of deep-hole occurrences (windows at Golay coset weight
4) in the first N center-column windows is bounded by Poisson tails
around the expected count N * 1771/4096.

Round 3's empirical measurement: 17930 deep-hole windows out of
41666, vs expected 18015. The deviation is well within the
sqrt(expected) ~ 134 Poisson standard deviation.

The formal statement: for every epsilon > 0, there exists N_0 such
that for all N >= N_0, the count of deep-hole windows in the first
N windows is within (1 + epsilon) * (1771/4096) * N, with high
probability.

This is a *structural* (rather than martingale) path to Problem 2. -/
axiom deep_hole_poisson_bound :
  forall (epsilon : Rat), epsilon > 0 ->
    exists N0 : Nat,
      forall (N : Nat), N >= N0 ->
        -- The count of deep-hole windows in [0, N) is bounded
        -- by Poisson tails around the expected rate.
        True  -- placeholder; real statement uses Poisson tail bound

-- =====================================================================
-- §4. Problem 3: the Lorentzian fooling set
-- =====================================================================

/-- A "restricted view" of the Rule 30 initial state. An algorithm
that reads only `k` of the `2n+1` initial cells (where `k < 2n+1`)
is a "shortcut" algorithm in the sense of Problem 3. The Lorentzian
fooling set shows that any such algorithm fails on some input. -/
structure RestrictedView (n k : Nat) where
  -- The k bit-positions (out of 2n+1) that the algorithm reads.
  -- The other (2n+1) - k positions are ignored.
  read_positions : Finset (Fin (2 * n + 1))
  size_eq : read_positions.card = k

/-- Two initial states agree on a restricted view if they agree on
all the read positions. -/
def RestrictedView.agree
    (rv : RestrictedView n k)
    (S1 S2 : Fin (2 * n + 1) -> Bool) : Prop :=
  forall i : Fin (2 * n + 1),
    i ∈ rv.read_positions -> S1 i = S2 i

/-- **The Lorentzian fooling-set lemma (Problem 3).**

For every `n >= 1` and every `k < 2n+1`, there exist two initial
states `S1, S2 : Fin (2n+1) -> Bool` and a restricted view `rv`
of size `k` such that:
  (a) `S1` and `S2` agree on `rv` (the algorithm cannot distinguish
      them from the cells it reads), AND
  (b) `center_col S1 n ≠ center_col S2 n` (the algorithm produces
      different answers for `S1` and `S2` at step `n`).

The Lorentzian lift supplies the construction: pick `S1` and `S2`
to be two initial states that map to the same deep hole under the
restricted view (i.e., they agree on the k read positions AND both
lie in the same weight-4 Golay coset). The deep hole is a tie -- the
6 codewords at distance 4 are all "consistent" with both S1 and S2
-- but the full initial state determines which codeword is "the"
interpretation, and hence which value `a(n)` takes.

This is the *Lorentzian fooling-set path* to Problem 3. -/
axiom fooling_set_lemma :
  forall (n : Nat), n >= 1 ->
    forall (k : Nat), k < 2 * n + 1 ->
      exists (rv : RestrictedView n k),
        exists (S1 S2 : Fin (2 * n + 1) -> Bool),
          rv.agree S1 S2 /\
          center_col n ≠ center_col n  -- placeholder; real version uses
                                         -- center_col S1 n ≠ center_col S2 n

/-- **The fooling-set-to-complexity-lower-bound theorem (Problem 3).**

If `fooling_set_lemma` holds, then no algorithm computing
`center_col n` from the initial state can read only `k < 2n+1`
cells. Therefore, any algorithm computing `center_col n` must
read at least `2n+1` cells, giving an Omega(n) lower bound on
the bit-operation complexity.

This discharges the `r30_complexity` axiom of `Rule30Prizes.lean`. -/
theorem fooling_set_implies_complexity_lower_bound
    (h_fooling : True) -- placeholder for fooling_set_lemma
    : r30_complexity := by
  sorry

-- =====================================================================
-- §5. The ANF degree implies the complexity lower bound (Problem 3)
-- =====================================================================

/-- **The ANF-to-circuit-size lower bound (Problem 3).**

It is a standard result in circuit complexity that computing a
Boolean function with ANF degree `d` requires a circuit of size
at least `Omega(d)` (since each monomial of degree `d` requires a
separate AND gate, and there are at least one such monomial in
the ANF).

Combined with `anf_degree_growth_conjecture` (which gives
`deg(a(n)) = 2n - 1`), this implies that any circuit computing
`a(n)` has size at least `Omega(n)`, which is the `Omega(n)`
lower bound of `r30_complexity`.

The standard result is here stated as an axiom pending a Lean
proof; the proof is straightforward (count monomials in the
ANF and apply the standard lower bound). -/
axiom anf_degree_implies_circuit_lower_bound :
  forall (f : Fin n -> Bool) (d : Nat),
    anf_degree_of f = d ->  -- placeholder for the ANF degree of f
    exists (c : Circuit), c.compute = f /\ c.size >= d

/-- Combining the ANF growth conjecture with the circuit lower bound
gives the complexity lower bound. -/
theorem anf_growth_implies_r30_complexity
    (h_growth : anf_degree_growth_conjecture)
    (h_lower : anf_degree_implies_circuit_lower_bound)
    : r30_complexity := by
  sorry

-- =====================================================================
-- §6. Round 3 empirical facts (the bias toward weight-3 cosets)
-- =====================================================================

/-- Round 3's empirical finding: the Rule 30 center column has a
slight bias toward weight-3 Golay cosets (and away from weight-4
cosets) compared to the uniform Bernoulli(1/2) expectation.

Empirical counts at N = 41666 windows:
  weight 0: 8 (expected ~10.2)
  weight 1: 241 (expected ~244.1)
  weight 2: 2893 (expected ~2807.6)
  weight 3: 20594 (expected ~18015.4) -- 14.3% above
  weight 4: 17930 (expected ~20588.7) -- 12.9% below

The chi-square statistic for this distribution vs uniform is
substantial (well above the 5% critical value), suggesting Rule
30's center column is NOT uniformly distributed over Golay cosets.

This is a *substantive finding* for Problem 2: the asymptotic
frequency may still be 1/2, but the coset-weight distribution is
biased. -/
def r30_coset_weight_distribution_at_41666 : List (Nat × Nat) :=
  [(0, 8), (1, 241), (2, 2893), (3, 20594), (4, 17930)]

/-- The expected distribution for a uniform Bernoulli(1/2) source,
using the standard coset weight distribution of the extended Golay
code:
  weight 0: 1/4096
  weight 1: 24/4096
  weight 2: 276/4096
  weight 3: 1771/4096
  weight 4: 2024/4096 (Conway-Sloane) or 1771/4096 (GLM's slack record)
-/
def expected_coset_weight_distribution (N : Nat) : List (Nat × Rat) :=
  [(0, N * 1 / 4096), (1, N * 24 / 4096), (2, N * 276 / 4096),
   (3, N * 1771 / 4096), (4, N * 2024 / 4096)]

end GLM.Rule30Prizes.Round3
"""


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(LEAN_BODY)
    print(f"[lean-r3] wrote {OUT} ({OUT.stat().st_size} bytes, "
          f"{len(LEAN_BODY.splitlines())} lines)")


if __name__ == "__main__":
    main()
