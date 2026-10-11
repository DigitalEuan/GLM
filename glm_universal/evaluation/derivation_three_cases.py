"""``glm_universal.evaluation.derivation_three_cases`` -- the declared cases of
Phase 118: the limits of the second derivation study
(``studies/DERIVATION_TWO_STUDY.md`` §6) that are derivations.

Written and committed **before** any code of the round.  The scorer is
:mod:`glm_universal.runtime.derivation_three_report`.  Every expected value
below was worked out by hand from the statement, not from the machine; the
decimal values of the Robin eigenvalues were taken by a throw-away bisection
in floating point, written for this file and kept nowhere in the package.

Three operations move past the line Phase 107 drew:

* :data:`INEQUALITIES` -- ``prove information inequality: GIVENS |- CLAIM``,
  past the Shannon cone.  Where Phase 107's exact search finds neither a
  Shannon-type certificate nor a counterexample of linear functions of fair
  bits (``NOT_SHANNON``), the machine now tries two things more:

  - **a non-Shannon certificate**: the claim is a nonnegative combination of
    elemental inequalities, rational multiples of the givens and instances
    of the Zhang-Yeung inequality, each instance itself certified by the
    copy lemma (a fifth variable ``R``, a copy of one variable over two
    others, and a Shannon-type certificate over five variables).  Verdict
    ``proved_non_shannon``;
  - **an entropic counterexample**: a distribution with rational
    probabilities, not built from linear functions of fair bits, whose
    entropies -- sums of rational multiples of logarithms of primes -- meet
    every given and violate the claim, the sign decided exactly by comparing
    two integers.  Verdict ``NOT_VALID_ENTROPIC``.

  Otherwise the verdict stays ``NOT_SHANNON`` (undecided).
* :data:`RATE_DISTORTION` -- ``derive rate distortion function for SOURCE
  source with hamming distortion``, now on the whole range ``0 <= D <=
  D_max``.  Past the Shannon lower bound's tight range the optimal
  reproduction uses only the ``k`` most likely letters, and with
  ``P_k = p_1 + ... + p_k``, ``H_k = -sum_{i <= k} p_i log2 p_i`` and
  ``T = D - (1 - P_k)``,

      R(D) = H_k + (1 - D) log2(1 - D) + T log2(T/(k - 1)),

  on ``1 - P_k + (k - 1) p_{k+1} <= D <= 1 - P_k + (k - 1) p_k`` (letters
  sorted so that ``p_1 >= p_2 >= ...``).  ``k = m`` is the Shannon lower
  bound; ``k = 1`` is ``D_max = 1 - p_1``, where ``R = 0``.  The test
  channel and the dual (Lagrangian) point are rational, so both bounds meet
  exactly.  The pieces are declared as the breakpoints and the number of
  letters used on each piece, and a value at one point of each new piece as
  an expression in ``log2``.
* :data:`ROBIN` -- ``solve eigenvalue problem for y(x): d2(y)/dx2 +
  lambda*y = 0; BC; BC`` with one Robin end (``y'(e) + h y(e) = 0``, or
  ``a y(e) + b y'(e) = 0``) and a Dirichlet or Neumann end.  The eigenvalues
  are ``k_n^2`` for the roots of a transcendental equation, one in each
  declared interval, a negative eigenvalue exactly when the declared sign
  condition holds, and on a numeric interval each eigenvalue is enclosed by
  rational bounds (fixed-point series for ``sin``, ``cos``, ``sinh`` and
  ``cosh`` with the remainder bounded) to the printed digits.

Then:

* :data:`REFUSALS` -- texts that must still be refused, with the code.
* :data:`INEQUALITY_BATTERY`, :data:`RD_BATTERY`, :data:`ROBIN_BATTERY` --
  random batteries.
* :data:`PHASE_107_NARROWED` -- the one Phase 107 declared case this round
  supersedes, declared here before the code.
* :data:`LEAN_THEOREMS` and :data:`MARKS`.
"""

from __future__ import annotations

from typing import Optional, Tuple

__all__ = ["INEQUALITIES", "RATE_DISTORTION", "ROBIN", "REFUSALS",
           "INEQUALITY_BATTERY", "RD_BATTERY", "ROBIN_BATTERY",
           "PHASE_107_NARROWED", "LEAN_FILE", "LEAN_THEOREMS", "MARKS"]

ZY = ("prove information inequality: "
      "|- 2*I(C;D) <= I(A;B) + I(A;C,D) + 3*I(C;D|A) + I(C;D|B)")
INGLETON = ("prove information inequality: "
            "|- I(A;B) <= I(A;B|C) + I(A;B|D) + I(C;D)")

#: ``(id, question, verdict)``; verdict ``proved`` | ``proved_non_shannon``
#: | ``NOT_VALID`` | ``NOT_VALID_ENTROPIC`` | ``NOT_SHANNON``.
INEQUALITIES: Tuple[Tuple[str, str, str], ...] = (
    ("zhang-yeung", ZY, "proved_non_shannon"),
    ("zhang-yeung-renamed", "prove information inequality: "
     "|- 2*I(Z;W) <= I(X;Y) + I(X;Z,W) + 3*I(Z;W|X) + I(Z;W|Y)",
     "proved_non_shannon"),
    ("zhang-yeung-roles-swapped", "prove information inequality: "
     "|- 2*I(A;B) <= I(C;D) + I(C;A,B) + 3*I(A;B|C) + I(A;B|D)",
     "proved_non_shannon"),
    ("zhang-yeung-doubled", "prove information inequality: "
     "|- 4*I(C;D) <= 2*I(A;B) + 2*I(A;C,D) + 6*I(C;D|A) + 2*I(C;D|B)",
     "proved_non_shannon"),
    ("ingleton", INGLETON, "NOT_VALID_ENTROPIC"),
    ("ingleton-renamed", "prove information inequality: "
     "|- I(C;D) <= I(C;D|A) + I(C;D|B) + I(A;B)", "NOT_VALID_ENTROPIC"),
    # controls: Phase 107's verdicts below the new stages do not move
    ("shannon-control", "prove information inequality: "
     "|- H(X) + H(Y) >= H(X,Y)", "proved"),
    ("linear-control", "prove information inequality: "
     "|- I(X;Y|Z) <= I(X;Y)", "NOT_VALID"),
)

#: ``(id, question, breakpoints, letters used on each piece, samples)``.
#: ``breakpoints`` run from 0 to ``D_max``; piece ``i`` lies between
#: breakpoints ``i`` and ``i + 1`` and uses ``letters[i]`` reproduction
#: letters.  ``samples`` are ``(D, R(D) as an expression in log2)``.
RATE_DISTORTION: Tuple[Tuple[str, str, Tuple[str, ...], Tuple[int, ...],
                             Tuple[Tuple[str, str], ...]], ...] = (
    ("skewed-ternary", "derive rate distortion function for "
     "[1/2, 1/3, 1/6] source with hamming distortion",
     ("0", "1/3", "1/2"), (3, 2),
     (("5/12", "-(1/2)*log2(1/2) - (1/3)*log2(1/3) + (7/12)*log2(7/12) "
               "+ (1/4)*log2(1/4)"),)),
    ("four-letter-dyadic", "derive rate distortion function for "
     "[1/2, 1/4, 1/8, 1/8] source with hamming distortion",
     ("0", "3/8", "1/2"), (4, 2),
     (("7/16", "-(1/2)*log2(1/2) - (1/4)*log2(1/4) + (9/16)*log2(9/16) "
               "+ (3/16)*log2(3/16)"),)),
    ("four-letter-three-pieces", "derive rate distortion function for "
     "[2/5, 3/10, 1/5, 1/10] source with hamming distortion",
     ("0", "3/10", "1/2", "3/5"), (4, 3, 2),
     (("2/5", "-(2/5)*log2(2/5) - (3/10)*log2(3/10) - (1/5)*log2(1/5) "
              "+ (3/5)*log2(3/5) + (3/10)*log2(3/20)"),
      ("11/20", "-(2/5)*log2(2/5) - (3/10)*log2(3/10) + (9/20)*log2(9/20) "
                "+ (1/4)*log2(1/4)"))),
    # controls: the Shannon lower bound is tight on the whole range
    ("tight-ternary", "derive rate distortion function for "
     "[3/5, 1/5, 1/5] source with hamming distortion",
     ("0", "2/5"), (3,), ()),
    ("uniform-four", "derive rate distortion function for uniform(4) "
     "source with hamming distortion", ("0", "3/4"), (4,), ()),
)

#: ``(id, question, characteristic equation, interval of k_n with its index
#: range, negative eigenvalue: None for none or its value to six decimals,
#: the first three eigenvalues to six decimals or None on a symbolic
#: interval)``.
ROBIN: Tuple[Tuple[str, str, str, str, Optional[str],
                   Optional[Tuple[str, str, str]]], ...] = (
    ("phase-107-robin", "solve eigenvalue problem for y(x): d2(y)/dx2 + "
     "lambda*y = 0; y(0) = 0; y(L) + d(y)/dx(L) = 0",
     "tan(k*L) = -k", "((n - 1/2)*pi/L, n*pi/L), n = 1, 2, 3, ...",
     None, None),
    ("dirichlet-robin-1", "solve eigenvalue problem for y(x): d2(y)/dx2 + "
     "lambda*y = 0; y(0) = 0; d(y)/dx(1) + y(1) = 0",
     "tan(k) = -k", "((n - 1/2)*pi, n*pi), n = 1, 2, 3, ...",
     None, ("4.115858", "24.139342", "63.659107")),
    ("neumann-robin-1", "solve eigenvalue problem for y(x): d2(y)/dx2 + "
     "lambda*y = 0; d(y)/dx(0) = 0; d(y)/dx(1) + y(1) = 0",
     "k*tan(k) = 1", "((n - 1)*pi, (n - 1/2)*pi), n = 1, 2, 3, ...",
     None, ("0.740174", "11.734862", "41.438808")),
    ("dirichlet-robin-negative", "solve eigenvalue problem for y(x): "
     "d2(y)/dx2 + lambda*y = 0; y(0) = 0; d(y)/dx(1) - 2*y(1) = 0",
     "tan(k) = k/2", "(n*pi, (n + 1/2)*pi), n = 1, 2, 3, ...",
     "-3.667256", ("18.273763", "57.707511", "116.913905")),
    ("dirichlet-robin-weak", "solve eigenvalue problem for y(x): "
     "d2(y)/dx2 + lambda*y = 0; y(0) = 0; 2*d(y)/dx(1) - y(1) = 0",
     "tan(k) = 2*k", "(0, pi/2) for n = 1; ((n - 1)*pi, (n - 1/2)*pi), "
     "n = 2, 3, ...", None, ("1.358533", "21.198812", "60.682289")),
    ("neumann-robin-negative", "solve eigenvalue problem for y(x): "
     "d2(y)/dx2 + lambda*y = 0; d(y)/dx(0) = 0; d(y)/dx(1) - y(1) = 0",
     "k*tan(k) = -1", "((n - 1/2)*pi, n*pi), n = 1, 2, 3, ...",
     "-1.439229", ("7.830964", "37.469707", "86.822635")),
    ("robin-at-zero", "solve eigenvalue problem for y(x): d2(y)/dx2 + "
     "lambda*y = 0; d(y)/dx(0) - y(0) = 0; y(1) = 0",
     "tan(k) = -k", "((n - 1/2)*pi, n*pi), n = 1, 2, 3, ...",
     None, ("4.115858", "24.139342", "63.659107")),
    ("longer-interval", "solve eigenvalue problem for y(x): d2(y)/dx2 + "
     "lambda*y = 0; y(0) = 0; d(y)/dx(2) + 3*y(2) = 0",
     "tan(2*k) = -k/3", "((n - 1/2)*pi/2, n*pi/2), n = 1, 2, 3, ...",
     None, ("1.844788", "7.666872", "17.936474")),
)

#: ``(id, text, code)``: still refused after the round.
REFUSALS: Tuple[Tuple[str, str, str], ...] = (
    ("inequality-five-variables", "prove information inequality: "
     "|- H(A,B,C,D,E) <= H(A) + H(B) + H(C) + H(D) + H(E)",
     "TOO_MANY_VARIABLES"),
    ("rd-non-hamming", "derive rate distortion function for bernoulli(1/3) "
     "source with distortion [[0, 1], [2, 0]]", "UNSUPPORTED"),
    ("robin-both-ends", "solve eigenvalue problem for y(x): d2(y)/dx2 + "
     "lambda*y = 0; d(y)/dx(0) - y(0) = 0; d(y)/dx(1) + y(1) = 0",
     "TRANSCENDENTAL"),
    ("robin-variable-coefficient", "solve eigenvalue problem for y(x): "
     "d2(y)/dx2 + lambda*x*y = 0; y(0) = 0; d(y)/dx(1) + y(1) = 0",
     "UNSUPPORTED"),
    ("robin-symbolic-coefficient", "solve eigenvalue problem for y(x): "
     "d2(y)/dx2 + lambda*y = 0; y(0) = 0; d(y)/dx(1) + h*y(1) = 0",
     "UNSUPPORTED"),
)

#: ``(count, seed, coefficient bound)``: random four-variable claims built
#: from instances of the Zhang-Yeung and Ingleton inequalities and elemental
#: terms (``runtime.derivation_three_report.random_beyond_claim``).
INEQUALITY_BATTERY: Tuple[int, int, int] = (120, 11801, 2)

#: ``(count, seed, largest alphabet, denominator)``: random rational
#: sources.
RD_BATTERY: Tuple[int, int, int, int] = (150, 11802, 5, 24)

#: ``(count, seed)``: random rational ``h`` and ``L`` for the four
#: Dirichlet/Neumann-Robin families.
ROBIN_BATTERY: Tuple[int, int] = (60, 11803)

#: Phase 107's declared refusal this round answers instead:
#: ``derivation_two_cases.REFUSALS`` row ``eigen-robin`` (refused
#: ``TRANSCENDENTAL`` there) -- its mark Q7 is narrowed to accept the Phase
#: 118 reading of that text, which must give the equation ``tan(k*L) = -k``.
PHASE_107_NARROWED: Tuple[Tuple[str, str], ...] = (
    ("eigen-robin", "tan(k*L) = -k"),
)

LEAN_FILE = "RequestProject/GLM/NonShannon.lean"

#: The theorems mark N10 names, in :data:`LEAN_FILE`.
LEAN_THEOREMS: Tuple[str, ...] = (
    "zhang_yeung_of_copy",
    "zhang_yeung_not_shannon",
    "ingleton_violated",
    "rd_dual_lower_bound",
    "robin_root_exists",
    "robin_eigenfunction",
)

MARKS: Tuple[Tuple[str, str], ...] = (
    ("N1", "every INEQUALITIES case as declared: the verdict"),
    ("N2", "every RATE_DISTORTION case as declared: the breakpoints, the "
           "letters used on each piece, and R(D) at each sample point within "
           "1e-9 of the declared expression"),
    ("N3", "every ROBIN case as declared: the characteristic equation, the "
           "interval of k_n with its index range, the negative eigenvalue "
           "(present or absent, and its value to six decimals), and the first "
           "three eigenvalues to six decimals on a numeric interval"),
    ("N4", "every REFUSALS text refused with the declared code"),
    ("N5", "every answered reading of N1-N3 verifies by its column-3 "
           "script, which shares no code with the layer, and a mutated claim "
           "is rejected by the same script for every one of them"),
    ("N6", "the inequality battery: 0 unsound (every certificate re-checked "
           "exactly, and no claim proved that a distribution of the search "
           "pool violates), 0 inconsistent (no claim both certified and "
           "refuted), every reading one of the declared verdicts; the number "
           "left NOT_SHANNON is reported, not required"),
    ("N7", "the rate-distortion battery: on every random source the pieces "
           "tile [0, D_max], R(D) is continuous at every breakpoint, equals "
           "the Shannon lower bound on its tight range and lies on or above "
           "it elsewhere; at random rational D the test channel is a channel "
           "with distortion exactly D, the dual point is feasible exactly, "
           "the two bounds are the same sum of logarithms; and the "
           "Blahut-Arimoto algorithm, run independently, agrees within 1e-6"),
    ("N8", "the Robin battery: every enclosure re-checked by a sign change "
           "of the characteristic function at rational endpoints, each root "
           "in its declared interval, the negative eigenvalue present exactly "
           "when declared, and Newton's method in floating point, run "
           "independently, inside every enclosure widened by 1e-9"),
    ("N9", "nothing else moved: Phase 107's report meets 11 of 11 with "
           "PHASE_107_NARROWED applied, and no other outside question, Set B "
           "question or evaluation case changes verdict"),
    ("N10", "a Lean file proves what the layer rests on (LEAN_THEOREMS) with "
            "no sorry"),
)
