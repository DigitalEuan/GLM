module

public import RequestProject.GLM.Rule30.Prizes
public import RequestProject.GLM.Rule30.RunBoundSearch

/-!
# Round 21 (DRAFT): the power-series ladder

**STATUS: DRAFT - NOT COMPILED.** This file was written outside the Lean toolchain
(Round 21 was produced in a compute-only environment). Aristotle must typecheck it
against Mathlib `v4.28.0` before import, fix any naming drift, and only then wire it
into `RequestProject/GLM/Rule30.lean`. No proof below is claimed; every target is a
`Prop` in the package style. Nothing here claims progress on the open problems.

Round 21 added the empirical layer (all `EMP`, outside Lean, artefacts in
`rule30_round21/data/`): maximal 2-kernel growth to depth 16; LC(2^22) = 2^22/2
exactly; random-like leading Hankel determinants with H_1536 nonzero; AP scan
strides 2-96 with no resonance; arcsine-typical excursion statistics; p(n) = 2^n
for n <= 17; the exact counting law C(d,T) = 2^(d+1) for 2 <= T <= d (d <= 12);
sparse witness rows. This file states the corresponding theorem TARGETS.

## The ladder

Over GF(2), with A(z) = sum a(n) z^n the generating function of the centre column:

  rational (eventually periodic; linear recurrence; bounded LC; finite Hankel rank)
    < algebraic (2-automatic; finite 2-kernel - Christol)
      < transcendental

`Problem1` sits at the first step: P1 iff A(z) is irrational. The kernel criterion
(Allouche-Shallit-Yassawi 2021, Theorem 1) gives the proof strategy for the second:
if the members a(2^k n + r_k) can be chosen all distinct, the sequence is not
2-automatic.
-/

@[expose] public section

namespace GLM.Rule30

/-! ## The 2-kernel and automaticity -/

/-- The 2-kernel of a sequence: all subsequences `a(2^k n + r)`. -/
def TwoKernel (a : ℕ → Bool) : Set (ℕ → Bool) :=
  { f | ∃ k r, r < 2 ^ k ∧ f = fun n => a (2 ^ k * n + r) }

/-- `a` is 2-automatic iff its 2-kernel is finite (Allouche-Shallit). -/
def IsTwoAutomatic (a : ℕ → Bool) : Prop := (TwoKernel a).Finite

/-- **New sufficient target for P1 (Round 21).** The centre column is not
2-automatic. Eventual periodicity implies automaticity in every base, so this
implies `Problem1`; by Christol it is implied by transcendence of A(z) over
GF(2)(z); it is necessary for `Problem3` (automatic sequences are computable from
`n` in `O(log n)`). It is seed-specific (passes E2), infinite in character (E6),
and a property of the column alone (survives the mirror). EMP: kernel grows
maximally to depth 16, so an automaton would need at least 65,536 states. -/
def CentreNotTwoAutomatic : Prop := ¬ IsTwoAutomatic centerCol

/-- **P1 from the new rung (proof target).** Automatic sequences include the
eventually periodic ones, so not-automatic rules out eventual periodicity.
Proof: an eventually periodic `a` has bounded 2-kernel (decimations of a periodic
tail plus finitely many transient shifts). -/
def NotAutomaticImpliesProblem1 : Prop := CentreNotTwoAutomatic → Problem1

/-- The Allouche-Shallit kernel criterion, as a Lean target: if for every depth
`k` there is a phase `r_k` such that the chosen members are pairwise distinct,
then `a` is not 2-automatic. This is the shape a transcendence proof of the
`CentreNotTwoAutomatic` rung would take. -/
def KernelCriterionPath (a : ℕ → Bool) : Prop :=
  ∃ r : ℕ → ℕ, (∀ k, r k < 2 ^ k) ∧
    ∀ k₁ k₂, k₁ ≠ k₂ → (fun n => a (2 ^ k₁ * n + r k₁)) ≠ (fun n => a (2 ^ k₂ * n + r k₂))

def KernelCriterionSound : Prop := ∀ a : ℕ → Bool, KernelCriterionPath a → ¬ IsTwoAutomatic a

/-! ## Linear complexity restatement and certificate -/

/-- Minimal LFSR length generating the first `m` terms of `a` from the start
(Berlekamp-Massey). To be implemented as a verified function on `List Bool`
(wire to the `Compute.lean` primitives; the Round 21 C implementation is the
specification reference, validated on four calibration families). -/
def lcProfile (a : ℕ → Bool) (m : ℕ) : ℕ := lcProfileImpl a m

/-- **P1 restatement (power-series form, target).** `Problem1` iff the linear
complexity profile of the centre column is unbounded. Direction 1: eventual
periodicity with pre-period `tau` and period `p` admits a from-start recurrence
of order `tau + p`, so `lcProfile` is eventually constant. Direction 2: an
unbounded profile satisfies no recurrence, so no eventual periodicity. -/
def LCUnbounded (a : ℕ → Bool) : Prop := ∀ N, ∃ m ≥ N, N ≤ lcProfile a m

def Problem1IffLCUnbounded : Prop := Problem1 ↔ LCUnbounded centerCol

/-- **The one-shot certificate (CERT target).** `LC(2^22) = 2,097,152` implies:
no eventual periodicity with `tau + p < 2,097,152`. To be checked by
`native_decide` on a verified Berlekamp-Massey, mirroring `runSearch`'s use in
`RunBoundSearch.lean`. Extends ledger row C160 by a factor of 200 in `n`. -/
def NoSmallPeriodicity (bound : ℕ) : Prop :=
  ¬ ∃ tau p, tau + p < bound ∧ EventuallyPeriodicFrom centerCol tau p

def LCImpliesNoSmallPeriodicity : Prop :=
  lcProfile centerCol (2 ^ 22) = 2 ^ 21 → NoSmallPeriodicity (2 ^ 21)

/-! ## Hankel restatement -/

/-- The leading Hankel determinant over GF(2): det [a(i+j)] for i, j < N. -/
def hankelDet (a : ℕ → Bool) (N : ℕ) : Bool := detGF2 (fun i j => a (i + j))

/-- **P1 restatement (Hankel form, target).** `Problem1` iff Hankel determinants
are nonzero for infinitely many `N`. Also the rank certificate: `hankelDet ≠ 0`
at `N` forces Hankel rank `≥ N`, hence `tau + 2p ≥ N` for any eventual
periodicity (calibrated: m-sequence peaks exactly at its register order). -/
def Problem1IffHankelInfinitelyOften : Prop :=
  Problem1 ↔ (∀ N, ∃ M ≥ N, hankelDet centerCol M)

/-! ## Morse-Hedlund restatement -/

/-- Number of distinct blocks of length `n` in the first `m` terms. -/
def blockComplexity (a : ℕ → Bool) (n m : ℕ) : ℕ := blockComplexityImpl a n m

/-- **P1 restatement (complexity form, target).** Morse-Hedlund: eventually
periodotic iff `p(n) ≤ n` for some `n`. So P1 iff `p(n) ≥ n + 1` for all `n`.
EMP: `p(n) = 2^n` exactly for `n ≤ 17` on 2^22 bits. -/
def Problem1IffComplexity : Prop :=
  Problem1 ↔ ∀ n, n + 1 ≤ blockComplexity centerCol n (2 ^ 22)

/-! ## The period-2 counting law -/

/-- The number of left-white contexts (free cells `x_1 .. x_{d+T}`, black edge
fixed) keeping the column at distance `d` `p`-periodic through time `T`. To be
defined by counting `witnessCheck`-style masks over `Finset.range (2 ^ (d + T))`,
mirroring `witnessCheck` / `runBoundTwoWitness` in `RunBoundSearch.lean`. -/
def RunCount (p d T : ℕ) : ℕ := RunCountImpl p d T

/-- **The counting law conjecture (Round 21's proposed new rung).** For every
left-white distance `d` and `2 ≤ T ≤ d`: exactly `2^(d+1)` contexts sustain
2-periodicity through time `T`. EMP-verified for `d ≤ 12` (each step adds one
free bit and one constraint, and exactly half the extended contexts survive -
the independence regime). Looks provable by induction along the diagonals. -/
def RunCountTwoLaw : Prop := ∀ d T, 2 ≤ T → T ≤ d → RunCount 2 d T = 2 ^ (d + 1)

/-- **Barrier entropy form (target).** After `T = d` the deficit
`H(d,T) = d + T - log2 C(d,T)` is strictly increasing in `T`. Together with
`RunCountTwoLaw` this would bound `B(d)` by a linear function of `d` - the
`PeriodTwoLinearBound` rung, via `C(d,T) ≥ 1` forcing `H(d,T) ≤ d + T`. -/
def DeficitIncreasingAfterD : Prop :=
  ∀ d T, d < T → (RunCount 2 d (T + 1) ≠ 0 →
    2 ^ (d + T + 1) / RunCount 2 d (T + 1) > 2 ^ (d + T) / RunCount 2 d T)

end GLM.Rule30
