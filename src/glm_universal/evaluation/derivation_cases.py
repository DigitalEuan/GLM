"""``glm_universal.evaluation.derivation_cases`` -- the declared cases of
Phase 106: derivations and proofs (track P of
``studies/QUESTION_SET_B_STUDY.md`` §8).

Written and committed **before** any code of the round.  The scorer is
:mod:`glm_universal.runtime.derivation_report`.  Every expected value below
was worked out by hand from the statement, not from the machine.

Four operations, each a derivation no register holds:

* :data:`PROOFS` -- ``prove: PREMISES |- GOAL`` in propositional logic.
  The verdict is ``intuitionistic`` (a proof found that uses no classical
  rule), ``classical`` (a tautology with no intuitionistic proof: the proof
  given uses excluded middle once, and the absence of an intuitionistic proof
  is decided by a terminating complete search), or ``NOT_VALID`` (refused,
  with a falsifying valuation; the valuation is declared where it is unique).
* :data:`MOTION` -- ``derive equations of motion for Q1, Q2[, small
  oscillations]: L = ...``: the Euler-Lagrange equations of a Lagrangian, and
  for small oscillations the linearisation about the origin and the squared
  normal-mode frequencies.  An equation matches when it is a nonzero multiple
  of the declared one by a factor free of every coordinate, velocity and
  acceleration; the frequency set must be equal as a set of expressions.
* :data:`TRANSFER` -- ``derive transfer functions from U1, U2 to Y: EQ; ...``:
  a dynamic model linearised about its steady state (``X_s`` the steady
  value of ``X``), in deviation variables, Laplace-transformed, and solved
  for each output over each input.  Each declared transfer function must be
  equal as a rational function in ``s`` and the parameters.
* :data:`PROFILES` -- ``solve boundary value problem for Y(X): d/dX(P*d(Y)/dX)
  = G; BC; BC``: the flux form with ``P`` a monomial in ``X`` and ``G`` a
  polynomial in ``X``, solved by two quadratures, the constants fixed by the
  boundary conditions (a value, a derivative, or ``bounded at 0``).  The
  declared profile must be equal identically.
* :data:`REFUSALS` -- texts of the four operations that must be refused, with
  the code.
* :data:`OUTSIDE_P` -- the class-P questions of the outside set this round
  declares it will answer, with a fragment the answer must contain; every
  other outside question's verdict must not change.
* :data:`MARKS` -- the ladder.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

__all__ = ["PROOFS", "MOTION", "TRANSFER", "PROFILES", "REFUSALS",
           "OUTSIDE_P", "PROVER_BATTERY", "MARKS"]

#: ``(id, question, verdict, falsifying valuation or None)``.
PROOFS: Tuple[Tuple[str, str, str, Optional[Dict[str, bool]]], ...] = (
    ("curry", "prove: C <-> (C -> F) |- F", "intuitionistic", None),
    ("liar", "prove: L <-> ~L |- false", "intuitionistic", None),
    ("chain", "prove: p -> q, q -> r |- p -> r", "intuitionistic", None),
    ("contraposition", "prove: p -> q |- ~q -> ~p", "intuitionistic", None),
    ("curry-uncurry", "prove: p -> (q -> r) |- (p & q) -> r",
     "intuitionistic", None),
    ("disjunctive-syllogism", "prove: p | q, ~p |- q", "intuitionistic",
     None),
    ("de-morgan-or", "prove: |- ~(p | q) <-> (~p & ~q)", "intuitionistic",
     None),
    ("not-not-lem", "prove: |- ~~(p | ~p)", "intuitionistic", None),
    ("excluded-middle", "prove: |- p | ~p", "classical", None),
    ("peirce", "prove: |- ((p -> q) -> p) -> p", "classical", None),
    ("double-negation", "prove: |- ~~p -> p", "classical", None),
    ("de-morgan-and", "prove: |- ~(p & q) -> (~p | ~q)", "classical", None),
    ("dummett", "prove: |- (p -> q) | (q -> p)", "classical", None),
    ("material-implication", "prove: |- (p -> q) -> (~p | q)", "classical",
     None),
    ("affirming-consequent", "prove: p -> q, q |- p", "NOT_VALID",
     {"p": False, "q": True}),
    ("conjunction-intro-wrong", "prove: |- p -> (p & q)", "NOT_VALID",
     {"p": True, "q": False}),
)

#: ``(id, question, [declared equation = 0, ...], linearised equations or
#: None, squared frequencies or None)``.  Velocities are ``q_dot``,
#: accelerations ``q_ddot``.
MOTION: Tuple[Tuple[str, str, List[str], Optional[List[str]],
                    Optional[List[str]]], ...] = (
    ("simple-pendulum",
     "derive equations of motion for th, small oscillations: "
     "L = (1/2)*m*l^2*th_dot^2 + m*g*l*cos(th)",
     ["l*th_ddot + g*sin(th)"], ["l*th_ddot + g*th"], ["g/l"]),
    ("spring-mass",
     "derive equations of motion for x, small oscillations: "
     "L = (1/2)*m*x_dot^2 - (1/2)*k*x^2",
     ["m*x_ddot + k*x"], ["m*x_ddot + k*x"], ["k/m"]),
    ("double-pendulum",
     "derive equations of motion for th1, th2, small oscillations: "
     "L = m*l^2*th1_dot^2 + (1/2)*m*l^2*th2_dot^2 "
     "+ m*l^2*th1_dot*th2_dot*cos(th1 - th2) + 2*m*g*l*cos(th1) "
     "+ m*g*l*cos(th2)",
     ["2*l*th1_ddot + l*th2_ddot*cos(th1 - th2) "
      "+ l*th2_dot^2*sin(th1 - th2) + 2*g*sin(th1)",
      "l*th1_ddot*cos(th1 - th2) + l*th2_ddot "
      "- l*th1_dot^2*sin(th1 - th2) + g*sin(th2)"],
     ["2*l*th1_ddot + l*th2_ddot + 2*g*th1",
      "l*th1_ddot + l*th2_ddot + g*th2"],
     ["(2 - sqrt(2))*g/l", "(2 + sqrt(2))*g/l"]),
    ("atwood",
     "derive equations of motion for x: "
     "L = (1/2)*(m1 + m2)*x_dot^2 + (m1 - m2)*g*x",
     ["(m1 + m2)*x_ddot - (m1 - m2)*g"], None, None),
    ("bead-on-hoop",
     "derive equations of motion for th, small oscillations: "
     "L = (1/2)*m*R^2*(th_dot^2 + w^2*sin(th)^2) + m*g*R*cos(th)",
     ["R*th_ddot - R*w^2*sin(th)*cos(th) + g*sin(th)"],
     ["R*th_ddot + (g - R*w^2)*th"], ["g/R - w^2"]),
    ("central-force",
     "derive equations of motion for r, ph: "
     "L = (1/2)*m*(r_dot^2 + r^2*ph_dot^2) + k/r",
     ["m*r_ddot - m*r*ph_dot^2 + k/r^2",
      "r*ph_ddot + 2*r_dot*ph_dot"], None, None),
    ("pendulum-on-cart",
     "derive equations of motion for x, th, small oscillations: "
     "L = (1/2)*(M + m)*x_dot^2 + m*l*x_dot*th_dot*cos(th) "
     "+ (1/2)*m*l^2*th_dot^2 + m*g*l*cos(th)",
     ["(M + m)*x_ddot + m*l*th_ddot*cos(th) - m*l*th_dot^2*sin(th)",
      "x_ddot*cos(th) + l*th_ddot + g*sin(th)"],
     ["(M + m)*x_ddot + m*l*th_ddot", "x_ddot + l*th_ddot + g*th"],
     ["0", "(M + m)*g/(M*l)"]),
    ("two-masses-three-springs",
     "derive equations of motion for x1, x2, small oscillations: "
     "L = (1/2)*m*(x1_dot^2 + x2_dot^2) "
     "- (1/2)*k*(x1^2 + (x2 - x1)^2 + x2^2)",
     ["m*x1_ddot + 2*k*x1 - k*x2", "m*x2_ddot + 2*k*x2 - k*x1"],
     ["m*x1_ddot + 2*k*x1 - k*x2", "m*x2_ddot + 2*k*x2 - k*x1"],
     ["k/m", "3*k/m"]),
)

#: ``(id, question, {(output, input): declared transfer function})``.
TRANSFER: Tuple[Tuple[str, str, Dict[Tuple[str, str], str]], ...] = (
    ("heating-tank",
     "derive transfer functions from Ti, Q to T: "
     "rho*V*Cp*d(T)/dt = rho*F*Cp*(Ti - T) + Q",
     {("T", "Ti"): "1/((V/F)*s + 1)",
      ("T", "Q"): "(1/(rho*F*Cp))/((V/F)*s + 1)"}),
    ("level-tank",
     "derive transfer functions from qi to h: A*d(h)/dt = qi - h/R",
     {("h", "qi"): "R/(A*R*s + 1)"}),
    ("two-tanks-in-series",
     "derive transfer functions from qi to h2: "
     "A1*d(h1)/dt = qi - h1/R1; A2*d(h2)/dt = h1/R1 - h2/R2",
     {("h2", "qi"): "R2/((A1*R1*s + 1)*(A2*R2*s + 1))"}),
    ("mass-spring-damper",
     "derive transfer functions from f to x: "
     "m*d2(x)/dt2 + c*d(x)/dt + k*x = f",
     {("x", "f"): "1/(m*s^2 + c*s + k)"}),
    ("draining-tank",
     "derive transfer functions from qi to h: A*d(h)/dt = qi - k*sqrt(h)",
     {("h", "qi"): "(2*sqrt(h_s)/k)/((2*A*sqrt(h_s)/k)*s + 1)"}),
    ("isothermal-cstr",
     "derive transfer functions from CAi, F to CA: "
     "V*d(CA)/dt = F*(CAi - CA) - V*k*CA",
     {("CA", "CAi"): "F_s/(V*s + F_s + V*k)",
      ("CA", "F"): "(CAi_s - CA_s)/(V*s + F_s + V*k)"}),
)

#: ``(id, question, declared profile)``.
PROFILES: Tuple[Tuple[str, str, str], ...] = (
    ("slab",
     "solve boundary value problem for T(x): d/dx(d(T)/dx) = 0; "
     "T(0) = T1; T(L) = T2",
     "T1 + (T2 - T1)*x/L"),
    ("cylinder-shell",
     "solve boundary value problem for T(r): d/dr(r*d(T)/dr) = 0; "
     "T(R1) = T1; T(R2) = T2",
     "T1 + (T2 - T1)*(ln(r) - ln(R1))/(ln(R2) - ln(R1))"),
    ("sphere-shell",
     "solve boundary value problem for C(r): d/dr(r^2*d(C)/dr) = 0; "
     "C(R1) = C1; C(R2) = C2",
     "(C2*R2 - C1*R1)/(R2 - R1) + (C1 - C2)*R1*R2/((R2 - R1)*r)"),
    ("slab-with-source",
     "solve boundary value problem for T(x): d/dx(k*d(T)/dx) = -q; "
     "d(T)/dx(0) = 0; T(L) = Ts",
     "Ts + q*(L^2 - x^2)/(2*k)"),
    ("wire-with-source",
     "solve boundary value problem for T(r): d/dr(r*d(T)/dr) = -q*r/k; "
     "T bounded at 0; T(R) = Ts",
     "Ts + q*(R^2 - r^2)/(4*k)"),
    ("sphere-with-source",
     "solve boundary value problem for T(r): d/dr(r^2*d(T)/dr) = -q*r^2/k; "
     "T bounded at 0; T(R) = Ts",
     "Ts + q*(R^2 - r^2)/(6*k)"),
)

#: ``(id, text, code)``.
REFUSALS: Tuple[Tuple[str, str, str], ...] = (
    ("prove-unreadable", "prove: p -> |- q", "UNREADABLE"),
    ("motion-absent-coordinate",
     "derive equations of motion for y: L = (1/2)*m*x_dot^2",
     "NOT_IN_LAGRANGIAN"),
    ("motion-not-equilibrium",
     "derive equations of motion for th, small oscillations: "
     "L = (1/2)*m*l^2*th_dot^2 - m*g*l*sin(th)",
     "NOT_EQUILIBRIUM"),
    ("transfer-absent-output",
     "derive transfer functions from qi to h2: A*d(h)/dt = qi - h/R",
     "NOT_IN_SYSTEM"),
    ("transfer-underdetermined",
     "derive transfer functions from qi to h2: "
     "A1*d(h1)/dt = qi - h1/R1 - h2/R2",
     "UNDERDETERMINED"),
    ("profile-one-condition",
     "solve boundary value problem for T(x): d/dx(d(T)/dx) = 0; T(0) = T1",
     "UNDERDETERMINED"),
    ("profile-inconsistent",
     "solve boundary value problem for y(x): d/dx(d(y)/dx) = 0; "
     "d(y)/dx(0) = 1; d(y)/dx(1) = 2",
     "INCONSISTENT"),
    ("profile-non-monomial",
     "solve boundary value problem for y(x): d/dx((1 + x)*d(y)/dx) = 0; "
     "y(0) = 0; y(1) = 1",
     "UNSUPPORTED"),
)

#: ``(outside index, fragment the answer must contain)``: the class-P
#: questions of ``Outside_Question_Set_B_candidate_O1.txt`` this round
#: declares it will answer.  The others stay refused.
OUTSIDE_P: Tuple[Tuple[int, str], ...] = (
    (18, "2*l*th1_ddot + l*th2_ddot + 2*g*th1 = 0"),
    (24, "(C1 - C2)*R1*R2"),
    (30, "1/(rho*F*Cp)"),
    (85, "F follows"),
)

#: Random formulas for the prover's soundness battery: ``(count, seed,
#: atoms, depth)``.
PROVER_BATTERY: Tuple[int, int, int, int] = (2000, 10601, 3, 4)

MARKS: Tuple[Tuple[str, str], ...] = (
    ("R1", "every PROOFS case as declared: the verdict, and for NOT_VALID "
           "the declared falsifying valuation"),
    ("R2", "every MOTION case as declared: each Euler-Lagrange equation, each "
           "linearised equation and the set of squared frequencies"),
    ("R3", "every TRANSFER case as declared: each transfer function"),
    ("R4", "every PROFILES case as declared: the profile"),
    ("R5", "every REFUSALS text refused with the declared code"),
    ("R6", "every answered reading of R1-R4 verifies by its column-3 "
           "script, which shares no code with the layer, and a mutated "
           "claim is rejected by the same script for every one of them"),
    ("R7", "the prover battery: every emitted proof re-checked rule by rule "
           "by an independent checker and every proved formula a "
           "tautology by truth table (0 unsound); every NOT_VALID carries a "
           "valuation that falsifies it; every tautology answered (0 gaps)"),
    ("R8", "the outside set: every OUTSIDE_P question answered with its "
           "fragment and its gate verified; no other outside or Set B "
           "question changes verdict; the 177 evaluation cases unchanged"),
    ("R9", "a Lean file proves what the layer rests on (the soundness of the "
           "prover's sequent rules for every valuation, Curry's derivation, "
           "the three shell profiles satisfy their equations and boundary "
           "values, the double pendulum's frequencies are roots of its "
           "characteristic polynomial) with no sorry"),
)
