"""Writes r6_reasoning_suite.json: paired claims for a GLM reasoning test (feedback #1 Track C,
feedback #3 section 4).  Each item asks for: verdict -> missing hypothesis -> counterexample or
proof reference -> next admissible test.  Items marked "held_out": true use phrasings and
examples that do not appear in the package's error record; use them for evaluation only."""
import json
from pathlib import Path

L = "RequestProject/GLM/Rule30/"
items = [
 # ---- measure vs seed --------------------------------------------------------------
 dict(id="M1", claim="For almost every initial row, the centre column has frequency 1/2.",
      verdict="ACCEPT", missing_hypothesis=None,
      reference=L+"Ergodic.lean (Problems 1 and 2 hold for almost every row)", next_test=None),
 dict(id="M1x", claim="Hence the centre column of the single-cell seed has frequency 1/2.",
      verdict="REJECT", missing_hypothesis="the seed is a measure-zero row; 'almost every' says nothing about it",
      reference=L+"ColumnInverse.lean: bernoulliRow_seed_null, exists_row_with_biased_column",
      next_test="a seed-specific argument using the seed's initial data"),
 # ---- map vs value -----------------------------------------------------------------
 dict(id="A1", claim="The map x -> a(n)(0) has ANF degree 2n-1 for 2 <= n <= 20.",
      verdict="ACCEPT", missing_hypothesis=None,
      reference=L+"ParityReductionData.lean: anfDegree_eq_upto20 (computation, native_decide)", next_test=None),
 dict(id="A1x", claim="Therefore the single bit a(n)(0) is hard to compute.",
      verdict="REJECT", missing_hypothesis="degree is a property of the map on all rows, not of its value on the seed",
      reference=L+"Prizes.lean: map_properties_cannot_decide_periodicity, degree_facts_compatible_with_periodicity",
      next_test="a uniform machine model with a lower bound (Problem3 in MachineModel.lean)"),
 dict(id="A2x", held_out=True,
      claim="The seed value a(n)(0) equals the linear ANF coefficient, so the parity of whiteDiagonalCount (the top coefficient) tracks the seed.",
      verdict="REJECT", missing_hypothesis="the linear and the top coefficient are different coefficients; the first equals the seed value by definition, the second is a map property",
      reference=L+"SeedBoundary.lean: seed_value_eq_linear_coeff; ANF.lean: anfCoeff_topMonomial_eq_count",
      next_test="state a seed-specific recurrence for the linear coefficient and test it"),
 # ---- finite prefix vs asymptotics ---------------------------------------------------
 dict(id="F1", claim="The first 10^6 centre bits have wobble |D(n)| <= 2*sqrt(n) except at listed times.",
      verdict="ACCEPT", missing_hypothesis=None, reference=L+"WobbleCertificate.lean (exact certificate)", next_test=None),
 dict(id="F1x", claim="So the infinite centre column has frequency 1/2.",
      verdict="REJECT", missing_hypothesis="finite-prefix data alone cannot decide an asymptotic property; a finite certificate needs a structural theorem behind it",
      reference=L+"WobbleCertificate.lean: no finite certificate decides Problems 1 or 2",
      next_test="a structural argument (e.g. a proof that the total echo is o(N^2))"),
 dict(id="F2x", held_out=True,
      claim="A sequence that passes a 24-bit block-uniformity test on 10^6 bits is normal; one that fails is not.",
      verdict="REJECT", missing_hypothesis="normality is asymptotic; the binary Champernowne sequence (normal) fails this test at 10^6 bits",
      reference="rule30_round6/r6_golay_census.json (Champernowne chi2 = 47 on 41666 blocks)",
      next_test="state the asymptotic property and look for a proof"),
 # ---- frequency vs normality ---------------------------------------------------------
 dict(id="N1x", claim="Problem 2 asks whether the centre column is a normal sequence.",
      verdict="REJECT", missing_hypothesis="Problem 2 asks only for frequency 1/2 of each colour (balance); normality needs every k-block with frequency 2^-k",
      reference=L+"Wobble.lean: HasFrequencyHalf; Prizes.lean: Problem2", next_test=None),
 # ---- diagonals ---------------------------------------------------------------------------
 dict(id="D1", claim="Every right diagonal of the seed pattern is periodic, with period dividing 2^D and least period > ceil(D/2).",
      verdict="ACCEPT", missing_hypothesis=None, reference=L+"Diagonals.lean", next_test=None),
 dict(id="D1x", claim="So the diagonal read-out a(t) = rdiag(t, t) is aperiodic.",
      verdict="REJECT", missing_hypothesis="unbounded diagonal periods hold for every right-white row, including rows with periodic centre columns",
      reference=L+"DiagonalCoupling.lean: diagonal_coupling_does_not_decide_problem1",
      next_test="use the seed's initial diagonal data (only diagonal 0 black at time 0)"),
 dict(id="D2x", held_out=True,
      claim="The seed's right edge is white, so the first inner diagonal is driven only by the left edge.",
      verdict="REJECT", missing_hypothesis="the right edge a(t)(t) is always black, and the right-diagonal system is autonomous (diagonal D depends only on D-1, D-2)",
      reference=L+"SeedBoundary.lean: evolve_seed_right_edge, rdiag_one_eq; Diagonals.lean: rdiag_succ", next_test=None),
 dict(id="D3x", held_out=True,
      claim="The centre column is the output of a fixed nonlinear shift register driven by the periodic edge stripes, so its pseudo-randomness follows from filter-generator theory.",
      verdict="REJECT", missing_hypothesis="a finite-state machine driven by an eventually periodic input has an eventually periodic output; the model needs an unbounded register (the diagonal read-out)",
      reference=L+"SeedBoundary.lean: Transducer.output_eventuallyPeriodic, problem1_no_finite_driven_register",
      next_test="work with the unbounded diagonal system and the seed's initial data"),
 # ---- spectral ----------------------------------------------------------------------------
 dict(id="S1", claim="D(N)^2 = N + 2 * (sum of the lag-k echoes of the +-1 wave, 1 <= k < N).",
      verdict="ACCEPT", missing_hypothesis=None, reference=L+"Spectral.lean: wobble_sq_eq_echo", next_test=None),
 dict(id="S1x", held_out=True,
      claim="Showing the wave has no spectral atom (no resonance) is an easier route to Problem 2 that bypasses the combinatorics.",
      verdict="REJECT", missing_hypothesis="'no atom at frequency 0' in the Cesaro sense is equivalent to Problem 2, so it is a restatement, not a shortcut",
      reference=L+"Spectral.lean: problem2_iff_totalEcho",
      next_test="a seed-specific bound on the total echo"),
 dict(id="S2", claim="If the centre column were eventually periodic with period p, its normalised lag-p echo would tend to 1.",
      verdict="ACCEPT", missing_hypothesis=None, reference=L+"Spectral.lean: echo_resonance, problem1_of_no_resonance", next_test=None),
 # ---- predictors / observers ---------------------------------------------------------
 dict(id="O1", claim="No causal predictor beats chance on a typical (random) row.",
      verdict="ACCEPT", missing_hypothesis=None, reference=L+"Unpredictability.lean: ae_predictor_hits_half", next_test=None),
 dict(id="O1x", claim="So no predictor beats chance on the seed's centre column.",
      verdict="REJECT", missing_hypothesis="the centre column is computable; the Rule 30 rule itself predicts it perfectly. Unpredictability is only meaningful relative to a declared rule space",
      reference=L+"RuleSpace.lean: not_escapes_allRules, centerCol_captured; Unpredictability.lean: no_row_typical_for_all_predictors",
      next_test="fix a rule space (lag, finite-state) and prove escape or typicality for it"),
 dict(id="O2", held_out=True,
      claim="Problem 1 is equivalent to the centre column escaping all lag rules 'bit t repeats bit t-p', and also to escaping all finite-state rules.",
      verdict="ACCEPT", missing_hypothesis=None,
      reference=L+"RuleSpace.lean: problem1_iff_escapes_lag, problem1_iff_escapes_fs, escapes_lag_iff_escapes_fs", next_test=None),
 dict(id="O3x", held_out=True,
      claim="Rule 30 with a right-white initial row always produces an aperiodic centre column, because the dynamics is chaotic.",
      verdict="REJECT", missing_hypothesis="some right-white rows have centre column 1,0,1,0,... (captured by a lag-2 rule)",
      reference=L+"RuleSpace.lean: exists_rightWhite_row_captured_by_lag; ColumnInverse.lean: exists_row_with_periodic_column", next_test=None),
 # ---- parity count ---------------------------------------------------------------------
 dict(id="P1", claim="whiteDiagonalCount(n) equals the number of zeros of a Boolean function of n-1 variables.",
      verdict="ACCEPT", missing_hypothesis=None, reference=L+"ParityReduction.lean: whiteDiagonalCount_eq_reduced", next_test=None),
 dict(id="P1x", held_out=True,
      claim="whiteDiagonalCount(n) is odd for n <= 36, so the top-monomial conjecture is proved.",
      verdict="REJECT", missing_hypothesis="exhaustive checks cover finitely many n (Lean proves 2 <= n <= 20; n <= 36 is outside-Lean evidence)",
      reference=L+"ParityReductionData.lean; rule30_round6/r6_parity_reduction_output.txt",
      next_test="a recurrence or involution for the reduced function valid for all n"),
 # ---- geometry --------------------------------------------------------------------------
 dict(id="G1x", held_out=True,
      claim="Lifting a tied Leech-lattice address into a Lorentzian space resolves the tie and therefore adds evidence about Rule 30.",
      verdict="REJECT", missing_hypothesis="a symmetry-preserving lift introduces no new evidence and can preserve the tie",
      reference="feedback #3 section 5 (retraction by the reviewer)",
      next_test="compare the lattice encoding against a direct encoding on a retrieval task"),
]
out = {"format": "verdict -> missing_hypothesis -> reference -> next_test",
       "scoring": "an answer scores 1 if its verdict matches; full credit also requires naming the missing hypothesis for REJECT items",
       "items": items}
Path(__file__).with_name("r6_reasoning_suite.json").write_text(json.dumps(out, indent=1))
print(len(items), "items;", sum(1 for i in items if i.get("held_out")), "held out")
