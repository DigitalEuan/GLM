"""``glm_universal.evaluation.derivation_four_cases`` -- the declared cases of
Phase 119: the limits the third derivation study drew
(``studies/DERIVATION_THREE_STUDY.md`` §6).

Written and committed **before** the reasoning code of the round (the Lean
files ``CopyLemma.lean`` and ``RobinBoth.lean`` came first, as Phase 117's
did).  The scorer is :mod:`glm_universal.runtime.derivation_four_report`.
The expected verdicts were worked out by hand; the decimal values were taken
by throw-away floating-point computations (a Blahut-Arimoto iteration with a
bisection on the slope for the rate-distortion values, a bisection on the
characteristic function for the Robin values), written for this file and
kept nowhere in the package.  The two-copy derivation of the Matus case was
located by a throw-away exhaustive search over pairs of copy steps before
this file was written; the declaration is that the machine finds *a*
two-copy certificate, not which one.

Four lines move:

* **The copy lemma in Lean.**  Not a case: mark P10 requires
  ``GLM.CopyLemma.copy_lemma`` and ``zhang_yeung_entropic`` (the Zhang-Yeung
  inequality for every finite distribution, with nothing left unproved).
* :data:`INEQUALITIES` -- ``prove information inequality``:

  - **past Zhang-Yeung**: a four-variable claim that neither the Shannon
    cone, nor the twelve Zhang-Yeung instances, nor the pool of rational laws
    decides is tried against *chains of copies*: ``R1`` a copy of one
    variable over a set of others, and ``R2`` a copy of the same variable over
    that set together with ``R1`` (Matus's construction), with an exact
    Shannon-type certificate over the six variables.  Verdict
    ``proved_by_copies``;
  - **five variables**: the Shannon-type search, the GF(2) counterexamples,
    the Zhang-Yeung instances on every four of the five, and the rational
    laws lifted to five variables (the fifth constant, or a copy of one of the
    four), with the same verdicts as for four.
* :data:`RATE_DISTORTION` -- ``derive rate distortion function for SOURCE
  source with distortion [[...]]`` (optionally ``at D = q``): ``D_min``,
  ``D_max``, and ``R(D)`` at the three quarter points of ``[D_min, D_max]``
  (and at ``q``) to six decimals, each from a rigorous enclosure: a channel of
  distortion at most ``D`` for the upper bound, a dual point with every
  exponential a power of a rational for the lower bound.
* :data:`ROBIN` -- Robin conditions at both ends (positive coefficients),
  a symbolic coefficient ``h`` (the spectrum given case by case in the sign
  and size of ``h`` or ``h*L``), a negative ``h`` on a symbolic interval
  (case by case in ``L``), and on a symbolic interval with ``h > 0`` a
  closed-form enclosure of each root.

Then :data:`REFUSALS`, the batteries, :data:`PHASE_118_NARROWED`,
:data:`LEAN_THEOREMS` and :data:`MARKS`.
"""

from __future__ import annotations

from typing import Optional, Tuple

__all__ = ["INEQUALITIES", "RATE_DISTORTION", "ROBIN", "ROBIN_SYMBOLIC",
           "ROBIN_BOUNDS", "REFUSALS", "INEQUALITY_BATTERY", "RD_BATTERY",
           "ROBIN_BATTERY", "PHASE_118_NARROWED", "LEAN_FILES",
           "LEAN_THEOREMS", "MARKS"]

P = "prove information inequality: "

MATUS_2 = (P + "|- 2*(I(A;B|C) + I(A;B|D) + I(C;D) - I(A;B)) + I(B;C|A) + "
           "3*I(A;C|B) + 3*I(A;B|C) >= 0")

#: ``(id, question, verdict)``; verdict ``proved`` | ``proved_non_shannon``
#: | ``proved_by_copies`` | ``NOT_VALID`` | ``NOT_VALID_ENTROPIC`` |
#: ``NOT_SHANNON``.
INEQUALITIES: Tuple[Tuple[str, str, str], ...] = (
    ("matus-2", MATUS_2, "proved_by_copies"),
    ("matus-2-renamed", P + "|- 2*(I(X;Y|Z) + I(X;Y|W) + I(Z;W) - I(X;Y)) + "
     "I(Y;Z|X) + 3*I(X;Z|Y) + 3*I(X;Y|Z) >= 0", "proved_by_copies"),
    # five variables
    ("five-subadditivity", P + "|- H(A,B,C,D,E) <= H(A) + H(B) + H(C) + "
     "H(D) + H(E)", "proved"),
    ("five-markov-chain", P + "I(A;C|B) = 0, I(A,B;D|C) = 0, "
     "I(A,B,C;E|D) = 0 |- I(A;E) <= I(B;D)", "proved"),
    ("five-conditioning-false", P + "|- I(A;B|C,D) <= I(A;B|C,D,E)",
     "NOT_VALID"),
    ("five-zhang-yeung", P + "|- 2*I(C;D) <= I(A;B) + I(A;C,D) + "
     "3*I(C;D|A) + I(C;D|B) + I(C;E|D)", "proved_non_shannon"),
    ("five-ingleton", P + "|- I(A;B) <= I(A;B|C) + I(A;B|D) + I(C;D) + "
     "I(A;E|B,C,D)", "NOT_VALID_ENTROPIC"),
    # controls: Phase 118's verdicts do not move
    ("zhang-yeung-control", P + "|- 2*I(C;D) <= I(A;B) + I(A;C,D) + "
     "3*I(C;D|A) + I(C;D|B)", "proved_non_shannon"),
    ("ingleton-control", P + "|- I(A;B) <= I(A;B|C) + I(A;B|D) + I(C;D)",
     "NOT_VALID_ENTROPIC"),
)

RD = "derive rate distortion function for "

#: ``(id, question, D_min, D_max, ((D, R(D) to six decimals), ...))``.
#: The points are the quarter points of ``[D_min, D_max]`` (and the asked
#: ``D``); ``R(D) = 0`` from ``D_max`` on.
RATE_DISTORTION: Tuple[Tuple[str, str, str, str,
                             Tuple[Tuple[str, str], ...]], ...] = (
    ("rd-asymmetric-binary", RD + "bernoulli(1/3) source with distortion "
     "[[0, 1], [2, 0]]", "0", "2/3",
     (("1/6", "0.408007"), ("1/3", "0.168063"), ("1/2", "0.040519"))),
    ("rd-absolute-ternary", RD + "uniform(3) source with distortion "
     "[[0, 1, 2], [1, 0, 1], [2, 1, 0]]", "0", "2/3",
     (("1/6", "0.851114"), ("1/3", "0.459148"), ("1/2", "0.192996"))),
    ("rd-squared-ternary", RD + "[1/2, 1/3, 1/6] source with distortion "
     "[[0, 1, 4], [1, 0, 1], [4, 1, 0]]", "0", "2/3",
     (("1/6", "0.741165"), ("1/3", "0.378785"), ("1/2", "0.129884"))),
    ("rd-positive-floor", RD + "bernoulli(1/2) source with distortion "
     "[[1, 2], [3, 1]]", "1", "3/2",
     (("9/8", "0.532288"), ("5/4", "0.280991"), ("11/8", "0.111676"))),
    ("rd-at-a-point", RD + "bernoulli(1/3) source with distortion "
     "[[0, 1], [2, 0]] at D = 1/4", "0", "2/3",
     (("1/6", "0.408007"), ("1/4", "0.270915"), ("1/3", "0.168063"),
      ("1/2", "0.040519"))),
    # control: Hamming written as a matrix -- h(1/4) - h(D) exactly
    ("rd-hamming-as-matrix", RD + "bernoulli(1/4) source with distortion "
     "[[0, 1], [1, 0]]", "0", "1/4",
     (("1/16", "0.473988"), ("1/8", "0.267714"), ("3/16", "0.115066"))),
)

E = "solve eigenvalue problem for y(x): d2(y)/dx2 + lambda*y = 0; "

#: Robin at both ends: ``(id, question, characteristic equation, interval
#: of k_n, first three eigenvalues to six decimals or None)``; no eigenvalue
#: ``<= 0`` (both coefficients positive).
ROBIN: Tuple[Tuple[str, str, str, str, Optional[Tuple[str, str, str]]],
             ...] = (
    ("robin-both-ends", E + "d(y)/dx(0) - y(0) = 0; d(y)/dx(1) + y(1) = 0",
     "(1 - k^2)*sin(k) + 2*k*cos(k) = 0",
     "((n - 1)*pi, n*pi), n = 1, 2, 3, ...",
     ("1.707053", "13.492357", "43.357221")),
    ("robin-both-asymmetric", E + "d(y)/dx(0) - 2*y(0) = 0; "
     "2*d(y)/dx(1) + y(1) = 0",
     "(1 - k^2)*sin(k) + 5/2*k*cos(k) = 0",
     "((n - 1)*pi, n*pi), n = 1, 2, 3, ...",
     ("1.791596", "14.154998", "44.227282")),
    ("robin-both-longer", E + "d(y)/dx(0) - y(0) = 0; "
     "d(y)/dx(2) + 3*y(2) = 0",
     "(3 - k^2)*sin(2*k) + 4*k*cos(2*k) = 0",
     "((n - 1)*pi/2, n*pi/2), n = 1, 2, 3, ...",
     ("1.024785", "5.038149", "13.119898")),
    ("robin-both-symbolic-length", E + "d(y)/dx(0) - y(0) = 0; "
     "d(y)/dx(L) + y(L) = 0",
     "(1 - k^2)*sin(k*L) + 2*k*cos(k*L) = 0",
     "((n - 1)*pi/L, n*pi/L), n = 1, 2, 3, ...", None),
)

#: A symbolic coefficient, or a sign class that depends on a symbolic
#: length: ``(id, question, equation, ((condition, interval of k_n, what is
#: <= 0: "none" | "zero" | "negative"), ...))``.
ROBIN_SYMBOLIC: Tuple[Tuple[str, str, str,
                            Tuple[Tuple[str, str, str], ...]], ...] = (
    ("robin-symbolic-h", E + "y(0) = 0; d(y)/dx(1) + h*y(1) = 0",
     "tan(k) = -k/h", (
         ("h > 0", "((n - 1/2)*pi, n*pi), n = 1, 2, 3, ...", "none"),
         ("h = 0", "k_n = (n - 1/2)*pi, n = 1, 2, 3, ...", "none"),
         ("-1 < h < 0", "(0, pi/2) for n = 1; ((n - 1)*pi, (n - 1/2)*pi), "
          "n = 2, 3, ...", "none"),
         ("h = -1", "(n*pi, (n + 1/2)*pi), n = 1, 2, 3, ...", "zero"),
         ("h < -1", "(n*pi, (n + 1/2)*pi), n = 1, 2, 3, ...", "negative"))),
    ("robin-symbolic-h-neumann", E + "d(y)/dx(0) = 0; d(y)/dx(1) + h*y(1) "
     "= 0", "k*tan(k) = h", (
         ("h > 0", "((n - 1)*pi, (n - 1/2)*pi), n = 1, 2, 3, ...", "none"),
         ("h = 0", "k_n = (n - 1)*pi, n = 2, 3, ...", "zero"),
         ("h < 0", "((n - 1/2)*pi, n*pi), n = 1, 2, 3, ...", "negative"))),
    ("robin-symbolic-h-and-length", E + "y(0) = 0; d(y)/dx(L) + h*y(L) = 0",
     "tan(k*L) = -k/h", (
         ("h > 0", "((n - 1/2)*pi/L, n*pi/L), n = 1, 2, 3, ...", "none"),
         ("h = 0", "k_n = (n - 1/2)*pi/L, n = 1, 2, 3, ...", "none"),
         ("-1 < h*L < 0", "(0, pi/(2*L)) for n = 1; ((n - 1)*pi/L, "
          "(n - 1/2)*pi/L), n = 2, 3, ...", "none"),
         ("h*L = -1", "(n*pi/L, (n + 1/2)*pi/L), n = 1, 2, 3, ...", "zero"),
         ("h*L < -1", "(n*pi/L, (n + 1/2)*pi/L), n = 1, 2, 3, ...",
          "negative"))),
    ("robin-negative-h-symbolic-length", E + "y(0) = 0; "
     "d(y)/dx(L) - 2*y(L) = 0", "tan(k*L) = k/2", (
         ("L < 1/2", "(0, pi/(2*L)) for n = 1; ((n - 1)*pi/L, "
          "(n - 1/2)*pi/L), n = 2, 3, ...", "none"),
         ("L = 1/2", "(n*pi/L, (n + 1/2)*pi/L), n = 1, 2, 3, ...", "zero"),
         ("L > 1/2", "(n*pi/L, (n + 1/2)*pi/L), n = 1, 2, 3, ...",
          "negative"))),
)

#: A symbolic interval with ``h > 0``: ``(id, question, lower and upper
#: bound of k_n*L as printed)``.
ROBIN_BOUNDS: Tuple[Tuple[str, str, str, str], ...] = (
    ("robin-symbolic-length-bounds", E + "y(0) = 0; y(L) + d(y)/dx(L) = 0",
     "(n - 1/2)*pi + arctan(L/(n*pi))",
     "(n - 1/2)*pi + arctan(L/((n - 1/2)*pi))"),
    ("robin-symbolic-length-bounds-3", E + "y(0) = 0; "
     "d(y)/dx(L) + 3*y(L) = 0",
     "(n - 1/2)*pi + arctan(3*L/(n*pi))",
     "(n - 1/2)*pi + arctan(3*L/((n - 1/2)*pi))"),
)

#: ``(id, text, code)``: still refused after the round.
REFUSALS: Tuple[Tuple[str, str, str], ...] = (
    ("inequality-six-variables", P + "|- H(A,B,C,D,E,F) <= H(A) + H(B) + "
     "H(C) + H(D) + H(E) + H(F)", "TOO_MANY_VARIABLES"),
    ("rd-symbolic-source", RD + "bernoulli(p) source with distortion "
     "[[0, 1], [2, 0]]", "UNSUPPORTED"),
    ("rd-negative-distortion", RD + "bernoulli(1/3) source with distortion "
     "[[0, -1], [1, 0]]", "UNREADABLE"),
    ("rd-below-floor", RD + "bernoulli(1/2) source with distortion "
     "[[1, 2], [3, 1]] at D = 1/2", "INFEASIBLE"),
    ("robin-both-ends-mixed-sign", E + "d(y)/dx(0) + y(0) = 0; "
     "d(y)/dx(1) + y(1) = 0", "UNSUPPORTED"),
    ("robin-variable-coefficient", "solve eigenvalue problem for y(x): "
     "d2(y)/dx2 + lambda*x*y = 0; y(0) = 0; d(y)/dx(1) + y(1) = 0",
     "UNSUPPORTED"),
)

#: ``(count, seed)``: random five-variable claims
#: (``runtime.derivation_four_marks.random_five_claim``), plus Phase 118's
#: own battery re-run past Zhang-Yeung.
INEQUALITY_BATTERY: Tuple[int, int] = (40, 11901)

#: ``(count, seed, largest alphabet, largest distortion)``: random sources
#: and integer distortion matrices.
RD_BATTERY: Tuple[int, int, int, int] = (60, 11902, 4, 3)

#: ``(count, seed)``: random positive ``a, b, L`` for Robin at both ends, and
#: random ``h`` in every sign class of the symbolic cases.
ROBIN_BATTERY: Tuple[int, int] = (40, 11903)

#: Phase 118's declared refusals this round answers instead
#: (``derivation_three_cases.REFUSALS``): its mark N4 (through the frames) is
#: narrowed to accept the Phase 119 reading of these texts, which must carry
#: the fragment given.
PHASE_118_NARROWED: Tuple[Tuple[str, str], ...] = (
    ("inequality-five-variables", "holds"),
    ("rd-non-hamming", "D_max = 2/3"),
    ("robin-both-ends", "(1 - k^2)*sin(k) + 2*k*cos(k) = 0"),
    ("robin-symbolic-coefficient", "tan(k) = -k/h"),
)

LEAN_FILES: Tuple[str, ...] = ("RequestProject/GLM/CopyLemma.lean",
                               "RequestProject/GLM/RobinBoth.lean")

#: The theorems mark P10 names, ``(file index, name)``.
LEAN_THEOREMS: Tuple[Tuple[int, str], ...] = (
    (0, "condMI_nonneg"),
    (0, "entropicFn_shannon"),
    (0, "copy_lemma"),
    (0, "zhang_yeung_entropic"),
    (1, "robin_both_root_exists"),
    (1, "robin_both_eigenfunction"),
    (1, "robin_root_arctan"),
    (1, "robin_root_bounds"),
)

MARKS: Tuple[Tuple[str, str], ...] = (
    ("P1", "every INEQUALITIES case as declared: the verdict"),
    ("P2", "every RATE_DISTORTION case as declared: D_min, D_max, and R(D) "
           "at every point to six decimals, from an enclosure of width below "
           "1e-6 that contains the declared value to within 5e-7"),
    ("P3", "every ROBIN, ROBIN_SYMBOLIC and ROBIN_BOUNDS case as declared: "
           "the equation, the interval of k_n (per case), what is <= 0 (per "
           "case), the eigenvalues to six decimals on a numeric interval, and "
           "the printed bounds"),
    ("P4", "every REFUSALS text refused with the declared code, at the layer "
           "and through the frames"),
    ("P5", "every answered reading of P1-P3 verifies by its column-3 script, "
           "which shares no code with the layer, and a mutated claim is "
           "rejected by the same script for every one of them"),
    ("P6", "the inequality battery: 0 unsound (every certificate re-checked "
           "exactly, no claim proved that a lifted pool law violates), 0 "
           "inconsistent, every reading one of the declared verdicts; and "
           "Phase 118's battery re-run with the copy chains: the number of "
           "its 3 NOT_SHANNON claims now decided is reported, not required, "
           "and none of its other verdicts moves"),
    ("P7", "the rate-distortion battery: every enclosure verified by its "
           "script, of width below 1e-6, the channel within the distortion "
           "exactly and the dual point feasible exactly; R non-increasing and "
           "convex across the quarter points (checked on the rigorous ends); "
           "every Hamming matrix within the enclosure of Phase 118's exact "
           "value"),
    ("P8", "the Robin battery: every two-ended root enclosure re-checked by "
           "a certified sign change inside its interval, a Newton iteration "
           "in fixed point inside every enclosure widened by 1e-9; for the "
           "symbolic cases, at random h (and L) in every sign class, a "
           "certified sign change in each of the first three intervals and "
           "the zero or negative eigenvalue present exactly when declared; "
           "for the bounds, every root of a random numeric instance inside "
           "them"),
    ("P9", "nothing else moved: Phase 118's report meets its marks with "
           "PHASE_118_NARROWED applied, and no outside question, Set B "
           "question or evaluation case changes verdict with the Phase 119 "
           "readings on and off"),
    ("P10", "the Lean files prove what the layer rests on (LEAN_THEOREMS) "
            "with no sorry: Shannon's inequalities and the copy lemma for "
            "every finite distribution, Zhang-Yeung with nothing left "
            "unproved, the two-ended Robin roots and eigenfunctions, and the "
            "closed-form enclosure"),
)
