"""``glm_universal.evaluation.derivation_two_cases`` -- the declared cases of
Phase 107: the rest of track P (derivations and proofs) of
``studies/QUESTION_SET_B_STUDY.md`` §8, after Phase 106 took four of its
eighteen questions.

Written and committed **before** any code of the round.  The scorer is
:mod:`glm_universal.runtime.derivation_two_report`.  Every expected value
below was worked out by hand from the statement, not from the machine.

Eight operations, each a derivation no register holds:

* :data:`INEQUALITIES` -- ``prove information inequality: GIVENS |- CLAIM``
  over the entropies of up to four random variables.  The verdict is
  ``proved`` (a Shannon-type certificate: the claim is a nonnegative
  rational combination of elemental inequalities plus rational multiples of
  the givens), ``NOT_VALID`` (refused, with a distribution -- each variable
  a GF(2)-linear function of independent fair bits -- whose exact entropies
  satisfy every given and violate the claim), or ``NOT_SHANNON`` (refused:
  no Shannon-type certificate exists and no linear distribution violates
  it; the inequality is left undecided).  For three variables or fewer the
  middle verdict is complete: every extreme ray of the Shannon cone is the
  entropy vector of such a distribution.
* :data:`CODES` -- ``decide unique decodability: W1, W2, ...`` by the
  Sardinas-Patterson procedure, with the Kraft sum and, for a uniquely
  decodable code, a prefix code with the same lengths; for a code that is
  not, an ambiguous string with two parsings.  ``construct prefix code with
  lengths L1, L2, ... [over D symbols]`` builds the canonical prefix code
  or refuses ``KRAFT_VIOLATED``.
* :data:`RATE_DISTORTION` -- ``derive rate distortion function for SOURCE
  source with hamming distortion``: the Shannon lower bound with the
  backward test channel, the range of distortion where the channel exists
  (the bound is the function there), ``R(D) = 0`` from the largest useful
  distortion on, and a stated gap (refused ``NOT_TIGHT``) between.
* :data:`MAXENT` -- ``derive maximum entropy density on SUPPORT with
  CONSTRAINTS``: the exponential-family density, its multipliers and its
  differential entropy, the maximum shown by ``h(f) = h(f*) - D(f||f*)``.
* :data:`EIGEN` -- ``solve eigenvalue problem for Y(X): d2(Y)/dX2 +
  lambda*Y = 0; BC; BC`` on an interval with Dirichlet or Neumann ends, or
  periodic: the eigenvalues, the normalised eigenfunctions, and the sign
  analysis that rules out the other values of ``lambda``.
* :data:`SCATTERING` -- ``derive transmission coefficient for V(x) = ...``
  for a potential concentrated at ``x = 0`` (a delta, a step, or both): the
  matching conditions solved as a linear system with complex coefficients.
* :data:`FFT` -- ``derive decimation-in-frequency fft for N = ...`` (or
  ``decimation-in-time``): the radix-2 split, the butterflies stage by
  stage with their twiddle factors, the counts and the output order.
* :data:`POSTERIOR` -- ``derive rate posterior for k = K errors in n = N
  bits [on the machine's grid]``: the Beta posterior, its normalising
  constant, its mode and monotonicity, and on the machine's declared rate
  grid the exact grid posterior and whether its peak is the guard point.

Then:

* :data:`REFUSALS` -- texts that must be refused, with the code.
* :data:`OUTSIDE_P2` -- the class-P questions of the outside set this round
  declares it will answer, with a fragment the answer must contain; every
  other outside question's verdict must not change (questions 29, 39 and 96
  stay refused, as declared here).
* :data:`INEQUALITY_BATTERY`, :data:`CODE_BATTERY` -- random batteries.
* :data:`MARKS` -- the ladder.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

__all__ = ["INEQUALITIES", "CODES", "PREFIX_CONSTRUCTIONS", "RATE_DISTORTION",
           "MAXENT", "EIGEN", "SCATTERING", "FFT", "POSTERIOR", "REFUSALS",
           "OUTSIDE_P2", "STAYS_REFUSED", "INEQUALITY_BATTERY",
           "CODE_BATTERY", "LEAN_THEOREMS", "MARKS"]

#: ``(id, question, verdict)``; verdict ``proved`` | ``NOT_VALID`` |
#: ``NOT_SHANNON``.
INEQUALITIES: Tuple[Tuple[str, str, str], ...] = (
    ("mi-nonneg", "prove information inequality: |- I(X;Y) >= 0", "proved"),
    ("cmi-nonneg", "prove information inequality: |- I(X;Y|Z) >= 0",
     "proved"),
    ("subadditivity",
     "prove information inequality: |- H(X) + H(Y) >= H(X,Y)", "proved"),
    ("conditioning-reduces",
     "prove information inequality: |- H(X) >= H(X|Y)", "proved"),
    ("chain-rule", "prove information inequality: "
     "|- H(X,Y,Z) = H(X) + H(Y|X) + H(Z|X,Y)", "proved"),
    ("han-three", "prove information inequality: "
     "|- H(X,Y) + H(Y,Z) + H(X,Z) >= 2*H(X,Y,Z)", "proved"),
    ("data-processing", "prove information inequality: "
     "I(X;Z|Y) = 0 |- I(X;Y) >= I(X;Z)", "proved"),
    ("data-processing-other-end", "prove information inequality: "
     "I(X;Z|Y) = 0 |- I(Y;Z) >= I(X;Z)", "proved"),
    ("function-of", "prove information inequality: "
     "H(Y|X) = 0 |- H(X) >= H(Y)", "proved"),
    ("four-chain", "prove information inequality: "
     "I(A;C|B) = 0, I(A,B;D|C) = 0 |- I(A;B) >= I(A;D)", "proved"),
    ("independence-not-conditional", "prove information inequality: "
     "I(X;Y) = 0 |- I(X;Y|Z) = 0", "NOT_VALID"),
    ("conditioning-can-increase-mi", "prove information inequality: "
     "|- I(X;Y|Z) <= I(X;Y)", "NOT_VALID"),
    ("joint-below-marginal", "prove information inequality: "
     "|- H(X) >= H(X,Y)", "NOT_VALID"),
    ("reverse-data-processing", "prove information inequality: "
     "I(X;Z|Y) = 0 |- I(X;Z) >= I(X;Y)", "NOT_VALID"),
    ("zhang-yeung", "prove information inequality: "
     "|- 2*I(C;D) <= I(A;B) + I(A;C,D) + 3*I(C;D|A) + I(C;D|B)",
     "NOT_SHANNON"),
    ("ingleton", "prove information inequality: "
     "|- I(A;B) <= I(A;B|C) + I(A;B|D) + I(C;D)", "NOT_SHANNON"),
)

#: ``(id, question, uniquely decodable, prefix-free, Kraft sum,
#: ambiguous string or None)``.  The ambiguous string is declared where it
#: is the shortest one; any string with two parsings is accepted.
CODES: Tuple[Tuple[str, str, bool, bool, str, Optional[str]], ...] = (
    ("complete-prefix", "decide unique decodability: 0, 10, 110, 111",
     True, True, "1", None),
    ("suffix-code", "decide unique decodability: 0, 01, 011",
     True, False, "7/8", None),
    ("reversed-prefix", "decide unique decodability: 1, 10, 100",
     True, False, "7/8", None),
    ("ud-not-prefix-complete", "decide unique decodability: 0, 01, 11",
     True, False, "1", None),
    ("ternary-prefix", "decide unique decodability: 0, 1, 20, 21, 22",
     True, True, "1", None),
    ("ambiguous-010", "decide unique decodability: 0, 01, 10",
     False, False, "1", "010"),
    ("ambiguous-0110", "decide unique decodability: 01, 10, 0110",
     False, False, "9/16", "0110"),
    ("kraft-exceeded", "decide unique decodability: 00, 01, 10, 11, 0",
     False, False, "3/2", "00"),
)

#: ``(id, question, codewords)`` -- the canonical prefix code.
PREFIX_CONSTRUCTIONS: Tuple[Tuple[str, str, List[str]], ...] = (
    ("lengths-1233", "construct prefix code with lengths 1, 2, 3, 3",
     ["0", "10", "110", "111"]),
    ("lengths-222", "construct prefix code with lengths 2, 2, 2",
     ["00", "01", "10"]),
    ("ternary-1122", "construct prefix code with lengths 1, 1, 2, 2 over 3 "
     "symbols", ["0", "1", "20", "21"]),
)

#: ``(id, question, R(D) on the tight range, upper end of the tight range,
#: distortion from which R(D) = 0, gap refused)``.  ``H(a)`` is the binary
#: entropy, ``H(a,b,c)`` the entropy of a distribution, logarithms base 2.
RATE_DISTORTION: Tuple[Tuple[str, str, str, str, str, bool], ...] = (
    ("bernoulli-p", "derive rate distortion function for bernoulli(p) "
     "source with hamming distortion", "H(p) - H(D)", "p", "p", False),
    ("bernoulli-quarter", "derive rate distortion function for "
     "bernoulli(1/4) source with hamming distortion", "H(1/4) - H(D)",
     "1/4", "1/4", False),
    ("bernoulli-three-quarters", "derive rate distortion function for "
     "bernoulli(3/4) source with hamming distortion", "H(1/4) - H(D)",
     "1/4", "1/4", False),
    ("uniform-ternary", "derive rate distortion function for uniform(3) "
     "source with hamming distortion", "log2(3) - H(D) - D", "2/3", "2/3",
     False),
    ("skewed-ternary", "derive rate distortion function for "
     "[1/2, 1/3, 1/6] source with hamming distortion",
     "H(1/2, 1/3, 1/6) - H(D) - D", "1/3", "1/2", True),
)

#: ``(id, question, density, differential entropy in nats)``.
MAXENT: Tuple[Tuple[str, str, str, str], ...] = (
    ("gaussian", "derive maximum entropy density on (-inf, inf) with mean "
     "mu and variance sigma^2",
     "exp(-(x - mu)^2/(2*sigma^2))/sqrt(2*pi*sigma^2)",
     "(1/2)*ln(2*pi*e*sigma^2)"),
    ("second-moment", "derive maximum entropy density on (-inf, inf) with "
     "second moment s", "exp(-x^2/(2*s))/sqrt(2*pi*s)",
     "(1/2)*ln(2*pi*e*s)"),
    ("exponential", "derive maximum entropy density on [0, inf) with mean "
     "mu", "exp(-x/mu)/mu", "1 + ln(mu)"),
    ("uniform", "derive maximum entropy density on [a, b]", "1/(b - a)",
     "ln(b - a)"),
)

#: ``(id, question, eigenvalue formula, index range, eigenfunction)``.
EIGEN: Tuple[Tuple[str, str, str, str, str], ...] = (
    ("dirichlet", "solve eigenvalue problem for y(x): d2(y)/dx2 + "
     "lambda*y = 0; y(0) = 0; y(L) = 0", "(n*pi/L)^2", "n = 1, 2, 3, ...",
     "sqrt(2/L)*sin(n*pi*x/L)"),
    ("neumann", "solve eigenvalue problem for y(x): d2(y)/dx2 + lambda*y = "
     "0; d(y)/dx(0) = 0; d(y)/dx(L) = 0", "(n*pi/L)^2", "n = 0, 1, 2, ...",
     "1/sqrt(L) for n = 0; sqrt(2/L)*cos(n*pi*x/L)"),
    ("dirichlet-neumann", "solve eigenvalue problem for y(x): d2(y)/dx2 + "
     "lambda*y = 0; y(0) = 0; d(y)/dx(L) = 0", "((2*n - 1)*pi/(2*L))^2",
     "n = 1, 2, 3, ...", "sqrt(2/L)*sin((2*n - 1)*pi*x/(2*L))"),
    ("neumann-dirichlet", "solve eigenvalue problem for y(x): d2(y)/dx2 + "
     "lambda*y = 0; d(y)/dx(0) = 0; y(L) = 0", "((2*n - 1)*pi/(2*L))^2",
     "n = 1, 2, 3, ...", "sqrt(2/L)*cos((2*n - 1)*pi*x/(2*L))"),
    ("periodic-ring", "solve eigenvalue problem for y(x): d2(y)/dx2 + "
     "lambda*y = 0; y(0) = y(2*pi); d(y)/dx(0) = d(y)/dx(2*pi)", "m^2",
     "m = 0, +-1, +-2, ...", "exp(i*m*x)/sqrt(2*pi)"),
    ("periodic-L", "solve eigenvalue problem for y(x): d2(y)/dx2 + "
     "lambda*y = 0; y(0) = y(L); d(y)/dx(0) = d(y)/dx(L)", "(2*pi*m/L)^2",
     "m = 0, +-1, +-2, ...", "exp(2*pi*i*m*x/L)/sqrt(L)"),
)

#: ``(id, question, transmission coefficient)``.  ``k1 = sqrt(2*m*E)/hbar``,
#: ``k2 = sqrt(2*m*(E - V0))/hbar``.
SCATTERING: Tuple[Tuple[str, str, str], ...] = (
    ("delta-barrier", "derive transmission coefficient for V(x) = "
     "alpha*delta(x)", "1/(1 + m*alpha^2/(2*hbar^2*E))"),
    ("delta-well", "derive transmission coefficient for V(x) = "
     "-beta*delta(x)", "1/(1 + m*beta^2/(2*hbar^2*E))"),
    ("step-above", "derive transmission coefficient for V(x) = "
     "V0*step(x), E > V0", "4*k1*k2/(k1 + k2)^2"),
    ("step-below", "derive transmission coefficient for V(x) = "
     "V0*step(x), E < V0", "0"),
    ("step-and-delta", "derive transmission coefficient for V(x) = "
     "V0*step(x) + alpha*delta(x), E > V0",
     "4*k1*k2/((k1 + k2)^2 + (2*m*alpha/hbar^2)^2)"),
)

#: ``(id, question, stages, butterflies, twiddle multiplications other than
#: W^0, output order or None, input order or None)``.
FFT: Tuple[Tuple[str, str, int, int, int, Optional[List[int]],
                 Optional[List[int]]], ...] = (
    ("dif-8", "derive decimation-in-frequency fft for N = 8", 3, 12, 5,
     [0, 4, 2, 6, 1, 5, 3, 7], None),
    ("dit-8", "derive decimation-in-time fft for N = 8", 3, 12, 5,
     None, [0, 4, 2, 6, 1, 5, 3, 7]),
    ("dif-16", "derive decimation-in-frequency fft for N = 16", 4, 32, 17,
     [0, 8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15], None),
    ("dif-2", "derive decimation-in-frequency fft for N = 2", 1, 1, 0,
     [0, 1], None),
)

#: ``(id, question, normalising constant or formula, mode, grid peak or
#: None, peak is the guard)``.  The machine's grid is
#: ``reasoning.rate_posterior.GRID`` (guard 1/5).
POSTERIOR: Tuple[Tuple[str, str, str, str, Optional[str], bool], ...] = (
    ("letters", "derive rate posterior for k errors in n bits",
     "(n + 1)!/(k!*(n - k)!)", "k/n", None, False),
    ("three-in-twenty", "derive rate posterior for k = 3 errors in n = 20 "
     "bits on the machine's grid", "23940", "3/20", "1/5", True),
    ("one-in-hundred", "derive rate posterior for k = 1 errors in n = 100 "
     "bits on the machine's grid", "10100", "1/100", "1/100", False),
    ("none-in-ten", "derive rate posterior for k = 0 errors in n = 10 "
     "bits on the machine's grid", "11", "0", "1/1000", False),
)

#: ``(id, text, code)``.
REFUSALS: Tuple[Tuple[str, str, str], ...] = (
    ("inequality-unreadable", "prove information inequality: |- I(X;Y >= 0",
     "UNREADABLE"),
    ("inequality-five-variables", "prove information inequality: "
     "|- H(A,B,C,D,E) <= H(A) + H(B) + H(C) + H(D) + H(E)",
     "TOO_MANY_VARIABLES"),
    ("prefix-kraft-violated", "construct prefix code with lengths 1, 1, 2",
     "KRAFT_VIOLATED"),
    ("code-empty-word", "decide unique decodability: 0, , 1", "UNREADABLE"),
    ("rd-non-hamming", "derive rate distortion function for bernoulli(1/3) "
     "source with distortion [[0, 1], [2, 0]]", "UNSUPPORTED"),
    ("maxent-unbounded", "derive maximum entropy density on (-inf, inf) "
     "with mean mu", "UNBOUNDED"),
    ("maxent-truncated-gaussian", "derive maximum entropy density on "
     "[0, inf) with mean mu and variance sigma^2", "UNSUPPORTED"),
    ("maxent-interval-mean", "derive maximum entropy density on [a, b] "
     "with mean mu", "TRANSCENDENTAL"),
    ("eigen-robin", "solve eigenvalue problem for y(x): d2(y)/dx2 + "
     "lambda*y = 0; y(0) = 0; y(L) + d(y)/dx(L) = 0", "TRANSCENDENTAL"),
    ("eigen-one-condition", "solve eigenvalue problem for y(x): d2(y)/dx2 "
     "+ lambda*y = 0; y(0) = 0", "UNDERDETERMINED"),
    ("eigen-variable-coefficient", "solve eigenvalue problem for y(x): "
     "d2(y)/dx2 + lambda*x*y = 0; y(0) = 0; y(L) = 0", "UNSUPPORTED"),
    ("scattering-two-points", "derive transmission coefficient for V(x) = "
     "alpha*delta(x) + alpha*delta(x - a)", "UNSUPPORTED"),
    ("fft-not-power-of-two", "derive decimation-in-frequency fft for N = 12",
     "NOT_POWER_OF_TWO"),
    ("posterior-inconsistent", "derive rate posterior for k = 5 errors in "
     "n = 3 bits", "INCONSISTENT"),
)

#: ``(outside index, fragment the answer must contain)``.
OUTSIDE_P2: Tuple[Tuple[int, str], ...] = (
    (19, "T = 1/(1 + m*alpha^2/(2*hbar^2*E))"),
    (28, "E_m = m^2*hbar^2/(2*I)"),
    (49, "(x[n] - x[n + N/2])*W_N^n"),
    (52, "D(p(x,y) || p(x)*p(y))"),
    (54, "I(X;Y) - I(X;Z) = I(X;Y|Z)"),
    (55, "h = (1/2)*ln(2*pi*e*sigma^2)"),
    (56, "sum_i D^(-l_i) <= 1"),
    (59, "R(D) = H(p) - H(D)"),
    (81, "has an infinite model"),
    (86, "is not definable"),
    (95, "p^k*(1 - p)^(n - k)"),
)

#: The class-P questions this round declares it leaves refused.
STAYS_REFUSED: Tuple[int, ...] = (29, 39, 96)

#: ``(count, seed, variables, coefficient bound)``: random linear
#: inequalities in the joint entropies of three variables.
INEQUALITY_BATTERY: Tuple[int, int, int, int] = (400, 10701, 3, 2)

#: ``(count, seed, largest code size, longest word)``: random binary codes.
CODE_BATTERY: Tuple[int, int, int, int] = (600, 10702, 5, 4)

#: The theorems mark Q11 names, in
#: ``RequestProject/GLM/DerivationsTwo.lean``.
LEAN_THEOREMS: Tuple[str, ...] = (
    "gibbs_inequality", "mutual_information_nonneg",
    "shannon_certificate_sound", "data_processing", "kraft_mcmillan",
    "dif_even", "dif_odd", "posterior_increasing", "rd_test_channel",
    "delta_transmission", "ring_eigenfunction", "dirichlet_eigenfunction",
    "lawvere_fixed_point", "tarski_undefinability",
    "infinite_model_of_large_finite_models",
)

MARKS: Tuple[Tuple[str, str], ...] = (
    ("Q1", "every INEQUALITIES case as declared: the verdict"),
    ("Q2", "every CODES case as declared (unique decodability, prefix-free, "
           "Kraft sum, and the shortest ambiguous string where declared) and "
           "every PREFIX_CONSTRUCTIONS case gives the declared code"),
    ("Q3", "every RATE_DISTORTION case as declared: the function on the "
           "tight range, the range, the zero point, and the gap refused "
           "exactly where declared"),
    ("Q4", "every MAXENT case as declared: the density and the entropy"),
    ("Q5", "every EIGEN case as declared: the eigenvalues, the index range "
           "and the normalised eigenfunctions"),
    ("Q6", "every SCATTERING, FFT and POSTERIOR case as declared"),
    ("Q7", "every REFUSALS text refused with the declared code"),
    ("Q8", "every answered reading of Q1-Q6 verifies by its column-3 "
           "script, which shares no code with the layer, and a mutated "
           "claim is rejected by the same script for every one of them"),
    ("Q9", "the batteries: every Shannon certificate re-checked exactly and "
           "every NOT_VALID distribution re-computed to violate the claim "
           "(0 unsound), no three-variable inequality left NOT_SHANNON "
           "(0 undecided); the Sardinas-Patterson verdict agrees with a "
           "brute-force search for two parsings on every random code, every "
           "uniquely decodable code has Kraft sum at most 1, and every "
           "constructed code is prefix-free with the requested lengths"),
    ("Q10", "the outside set: every OUTSIDE_P2 question answered with its "
            "fragment and its gate verified; questions 29, 39 and 96 still "
            "refused; no other outside or Set B question changes verdict; "
            "the 177 evaluation cases unchanged"),
    ("Q11", "a Lean file proves what the layer rests on (LEAN_THEOREMS) "
            "with no sorry"),
)
