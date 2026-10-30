"""``glm_universal.evaluation.symbolic_cases`` -- the declared cases of
Phase 98, symbolic parameters (boundary class S of
``studies/QUESTION_SET_B_STUDY.md`` §8, item 1).

Written and committed **before** any code of the round.  The scorer is
:mod:`glm_universal.runtime.symbolic_report`.

Three kinds of declaration:

* :data:`SYSTEMS` -- systems of equations in letters put to the new
  ``solve symbolically for ...:`` operation, each with the answer derived by
  hand.  An expected value is compared as an identity of rational functions
  (never as text); a quantity the machine can only give through a root is
  declared by its square in :data:`SYSTEMS_SQUARED`.
* :data:`REFUSALS` -- systems the operation must refuse, with the code.
* :data:`OUTSIDE_S` -- the 13 outside questions of class S, each with the
  hand-derived answer a correct reading must contain (as a fragment of the
  printed answer), or ``None`` where the round does not expect to answer.
  :data:`OUTSIDE_T` is the one transcendental question (class T).
* :data:`VARIANTS` -- for each outside question the round expects to answer,
  re-worded questions with one given changed, and the answer that change
  must produce (a frame that looked its answer up by question would fail
  these).

:data:`MARKS` is the ladder.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

__all__ = ["SYSTEMS", "SYSTEMS_SQUARED", "REFUSALS", "OUTSIDE_S",
           "OUTSIDE_T", "VARIANTS", "MARKS"]

#: ``(id, question, {target: expected expression})``.
SYSTEMS: Tuple[Tuple[str, str, Dict[str, str]], ...] = (
    ("sum-difference",
     "solve symbolically for x, y: x + y = s; x - y = d",
     {"x": "(s + d)/2", "y": "(s - d)/2"}),
    ("rolling-cylinder",
     "solve symbolically for a, f in terms of M, g, theta, R: "
     "M*a = M*g*sin(theta) - f; f*R = I*alpha; I = (1/2)*M*R^2; "
     "a = alpha*R",
     {"a": "(2/3)*g*sin(theta)", "f": "(1/3)*M*g*sin(theta)"}),
    ("rolling-hollow-sphere",
     "solve symbolically for a in terms of M, g, theta, R: "
     "M*a = M*g*sin(theta) - f; f*R = I*alpha; I = (2/3)*M*R^2; "
     "a = alpha*R",
     {"a": "(3/5)*g*sin(theta)"}),
    ("atwood",
     "solve symbolically for a, T in terms of m1, m2, g: "
     "m1*a = m1*g - T; m2*a = T - m2*g",
     {"a": "g*(m1 - m2)/(m1 + m2)", "T": "2*m1*m2*g/(m1 + m2)"}),
    ("divider",
     "solve symbolically for I, V2 in terms of V, R1, R2: "
     "V = I*(R1 + R2); V2 = I*R2",
     {"I": "V/(R1 + R2)", "V2": "V*R2/(R1 + R2)"}),
    ("parallel",
     "solve symbolically for R in terms of R1, R2: 1/R = 1/R1 + 1/R2",
     {"R": "R1*R2/(R1 + R2)"}),
    ("thin-lens",
     "solve symbolically for v in terms of u, f: 1/f = 1/u + 1/v",
     {"v": "u*f/(u - f)"}),
    ("block-diagram",
     "solve symbolically for Y in terms of Gc, Gv, Gp, Gm, Gd, D: "
     "E = -Gm*Y; U = Gc*E; Y = Gp*(Gv*U + Gd*D)",
     {"Y": "Gp*Gd*D/(1 + Gc*Gv*Gp*Gm)"}),
    ("rise-time",
     "solve symbolically for t in terms of v0, g: 0 = v0 - g*t",
     {"t": "v0/g"}),
    ("elastic-pair",
     "solve symbolically for v1, v2 in terms of m1, m2, u: "
     "m1*u = m1*v1 + m2*v2; v2 - v1 = u",
     {"v1": "u*(m1 - m2)/(m1 + m2)", "v2": "2*m1*u/(m1 + m2)"}),
    ("two-loop",
     "solve symbolically for I1, I2, I3 in terms of V, R1, R2, R3: "
     "I1 = I2 + I3; V = I1*R1 + I2*R2; I2*R2 = I3*R3",
     {"I1": "V*(R2 + R3)/(R1*R2 + R1*R3 + R2*R3)",
      "I2": "V*R3/(R1*R2 + R1*R3 + R2*R3)",
      "I3": "V*R2/(R1*R2 + R1*R3 + R2*R3)"}),
    ("cramer",
     "solve symbolically for x, y: a*x + b*y = e; c*x + d*y = f",
     {"x": "(e*d - b*f)/(a*d - b*c)", "y": "(a*f - c*e)/(a*d - b*c)"}),
    ("incline-friction",
     "solve symbolically for a in terms of m, g, theta, mu: "
     "m*a = m*g*sin(theta) - mu*N; N = m*g*cos(theta)",
     {"a": "g*(sin(theta) - mu*cos(theta))"}),
    ("series-capacitors",
     "solve symbolically for C in terms of C1, C2: 1/C = 1/C1 + 1/C2",
     {"C": "C1*C2/(C1 + C2)"}),
    ("ideal-gas",
     "solve symbolically for T in terms of p, V, n, R: p*V = n*R*T",
     {"T": "p*V/(n*R)"}),
)

#: ``(id, question, {target: expected square})`` -- answers through a root.
SYSTEMS_SQUARED: Tuple[Tuple[str, str, Dict[str, str]], ...] = (
    ("kinetic-speed",
     "solve symbolically for v in terms of m, E: E = (1/2)*m*v^2",
     {"v": "2*E/m"}),
    ("pendulum-period",
     "solve symbolically for T in terms of L, g: T^2 = 4*pi^2*L/g",
     {"T": "4*pi^2*L/g"}),
    ("invariant-mass",
     "solve symbolically for M in terms of m0, gamma, c: "
     "E = gamma*m0*c^2 + m0*c^2; p = gamma*m0*v; "
     "v^2 = c^2*(1 - 1/gamma^2); M^2*c^4 = E^2 - p^2*c^2",
     {"M": "2*m0^2*(1 + gamma)"}),
)

#: ``(id, question, refusal code)``.
REFUSALS: Tuple[Tuple[str, str, str], ...] = (
    ("one-equation-two-unknowns",
     "solve symbolically for x, y: x + y = 1", "UNDERDETERMINED"),
    ("contradiction",
     "solve symbolically for x: x + 1 = x + 2", "INCONSISTENT"),
    ("quadratic",
     "solve symbolically for x: x^2 + x = c", "NONLINEAR"),
    ("unreadable",
     "solve symbolically for x: x + = 2", "UNREADABLE"),
    ("target-absent",
     "solve symbolically for z: x = 1", "NOT_IN_SYSTEM"),
    ("dependent",
     "solve symbolically for x, y: x + y = 1; 2*x + 2*y = 2",
     "UNDERDETERMINED"),
    ("vacuous",
     "solve symbolically for x: 0*x = 0", "UNDERDETERMINED"),
    ("product-of-unknowns",
     "solve symbolically for x, y: x*y = 1; x + y = 3", "NONLINEAR"),
)

#: The 13 class-S outside questions (index into the outside set) and the
#: fragment a correct printed answer must contain; ``None`` = not expected.
OUTSIDE_S: Dict[int, Optional[str]] = {
    7: "gamma*(sqrt(2*phi_F + V_SB) - sqrt(2*phi_F))",
    8: "tan(theta1)/tan(theta2) = epsilon1/epsilon2",
    10: "a = (2/3)*g*sin(theta)",
    11: "W = (3/2)*R*T0*(1 - 2^(-2/3))",
    12: "E = lambda/(2*pi*epsilon0*r)",
    14: "M = m0*sqrt(2*(gamma + 1))",
    16: "U = N*epsilon/(e^(epsilon/(k*T)) + 1)",
    17: "Q = pi^2*a^4*alpha*B0^2/(2*R)",
    26: "C_V,m = R",
    27: "CFSE = -(12/5)*Delta_o + 2*P",
    33: "Y/D = Gd*Gp/(1 + Gc*Gv*Gp*Gm)",
    45: "omega0 = 2*pi*k0/N",
    47: "R_yy[m] = a^|m|/(1 - a^2)",
}

#: The transcendental question (class T): the reading must bracket the root
#: of 0.5*omega + arctan(omega) = pi to within 1/10000, with exact bounds.
OUTSIDE_T: Dict[int, str] = {35: "omega_co"}

#: Per answered outside question: ``(variant text, fragment)``.
VARIANTS: Dict[int, List[Tuple[str, str]]] = {
    8: [("Advanced Magnetostatics: At a planar interface separating two "
         "linear, isotropic media with permeabilities μ₁ and μ₂ and no "
         "surface current, a static magnetic field $\\mathbf{H}_1$ hits the "
         "boundary at an angle θ₁ relative to the surface normal. Prove the "
         "boundary condition relationship $\\frac{\\tan\\theta_1}"
         "{\\tan\\theta_2} = \\frac{\\mu_1}{\\mu_2}$ by invoking Maxwell's "
         "boundary equations for tangential $\\mathbf{H}$ and normal "
         "$\\mathbf{B}$ fields.",
         "tan(theta1)/tan(theta2) = mu1/mu2")],
    10: [("Classical Mechanics: A uniform solid sphere of mass M and radius "
          "R rolls without slipping down an inclined plane making an angle θ "
          "with the horizontal. Find the linear acceleration of the sphere's "
          "center of mass and the minimum coefficient of static friction "
          "required to prevent slipping.", "a = (5/7)*g*sin(theta)"),
         ("Classical Mechanics: A thin hoop of mass M and radius R rolls "
          "without slipping down an inclined plane making an angle θ with "
          "the horizontal. Find the linear acceleration of the hoop's center "
          "of mass and the minimum coefficient of static friction required "
          "to prevent slipping.", "a = (1/2)*g*sin(theta)")],
    11: [("Thermodynamics: One mole of an ideal monatomic gas undergoes an "
          "adiabatic expansion from an initial volume V₀ to a final volume "
          "3V₀. Calculate the total work done by the gas during this process "
          "and express your answer in terms of the initial temperature T₀ "
          "and the universal gas constant R.",
          "W = (3/2)*R*T0*(1 - 3^(-2/3))"),
         ("Thermodynamics: One mole of an ideal diatomic gas undergoes an "
          "adiabatic expansion from an initial volume V₀ to a final volume "
          "2V₀. Calculate the total work done by the gas during this process "
          "and express your answer in terms of the initial temperature T₀ "
          "and the universal gas constant R.",
          "W = (5/2)*R*T0*(1 - 2^(-2/5))")],
    12: [("Electromagnetism: An infinitely long, straight wire carries a "
          "uniform line charge density λ. Surrounding this wire is a "
          "coaxial conducting cylindrical shell with inner radius a and "
          "outer radius b that carries a net line charge density μ. Use "
          "Gauss's Law to find the electric field in all three regions: "
          "inside the shell, within the conducting material, and outside "
          "the shell.", "E = (lambda + mu)/(2*pi*epsilon0*r)")],
    14: [("Special Relativity: A particle of rest mass m₀ moving at a "
          "relativistic speed v collides head-on with a particle of rest "
          "mass 2m₀ at rest. The two particles fuse together to form a "
          "single composite particle. Calculate the rest mass M of the "
          "resulting composite particle in terms of m₀ and the Lorentz "
          "factor γ.", "M = m0*sqrt(4*gamma + 5)")],
    16: [("Statistical Mechanics: Consider a system of N non-interacting, "
          "distinguishable particles, where each particle can occupy one of "
          "three energy levels: 0, ε or 2ε. Derive the canonical partition "
          "function for this system and find the expression for the total "
          "internal energy as a function of temperature T.",
          "Z = (1 + e^(-epsilon/(k*T)) + e^(-2*epsilon/(k*T)))^N")],
    17: [("Electrodynamics: A square loop of wire with side a and "
          "resistance R lies flat in the xy-plane. A time-dependent, "
          "spatially uniform magnetic field is applied perpendicular to the "
          "loop, given by $\\mathbf{B}(t) = B_0 e^{-\\alpha t} "
          "\\hat{\\mathbf{z}}$. Derive the expression for the total "
          "electrical energy dissipated as heat in the loop from t = 0 to "
          "t → ∞.", "Q = a^4*alpha*B0^2/(2*R)")],
    26: [("Statistical Thermodynamics: For a nonlinear polyatomic molecule "
          "modeled as a rigid rotor, write down the expression for the "
          "rotational partition function ($q_{\\text{rot}}$) at high "
          "temperatures. Use it to derive an expression for the rotational "
          "contribution to the molar constant-volume heat capacity "
          "($C_{V,m}$) and explain why this value changes at cryogenic "
          "temperatures.", "C_V,m = (3/2)*R")],
    27: [("Coordination Chemistry: Using Crystal Field Theory (CFT), sketch "
          "the d-orbital splitting diagram for a high-spin d⁵ octahedral "
          "complex versus a tetrahedral complex of the same metal ion. "
          "Calculate the Crystal Field Stabilization Energy (CFSE) for both "
          "configurations in terms of $\\Delta_o$ or $\\Delta_t$ and "
          "pairing energy (P).", "octahedral: CFSE = 0")],
    33: [("Block Diagram Algebra: Consider a standard negative feedback "
          "loop with a process $G_p(s)$, an actuator $G_v(s)$, a "
          "sensor/transmitter $G_m(s)$, and a controller $G_c(s)$. If a load "
          "disturbance $d(t)$ enters the loop through a disturbance transfer "
          "function $G_d(s)$ at the process output, derive the closed-loop "
          "transfer function relating the controlled variable $Y(s)$ to the "
          "disturbance $D(s)$ when the setpoint change is zero "
          "($Y_{sp} = 0$).", "Y/D = Gd/(1 + Gc*Gv*Gp*Gm)")],
    47: [("Stochastic Signals & LTI Systems: Wide-Sense Stationary (WSS) "
          "white noise $w[n]$ with zero mean and variance σ² = 4 is passed "
          "through a first-order stable filter with impulse response "
          "$h[n] = a^n u[n]$ where |a| < 1. Derive the Autocorrelation "
          "Function $R_{yy}[m]$ and the Power Spectral Density "
          "$S_{yy}(e^{j\\omega})$ of the output signal $y[n]$.",
          "R_yy[m] = 4*a^|m|/(1 - a^2)")],
}

#: The ladder, declared before any code.
MARKS: Tuple[Tuple[str, str], ...] = (
    ("S1", "at least 10 of the 13 class-S outside questions answered through "
           "the router with a gate-verified reading containing the declared "
           "fragment; 0 answered without it (0 confidently wrong)"),
    ("S2", "every declared variant answered with its own fragment, gate "
           "verified (the answer moves with the given)"),
    ("S3", "every system of SYSTEMS answered, each target equal to the "
           "declared expression as a rational-function identity; every "
           "system of SYSTEMS_SQUARED answered with the declared square"),
    ("S4", "every system of REFUSALS refused with the declared code"),
    ("S5", "every answered reading's column-3 script verifies, and rejects "
           "the same script with the answer altered (S1, S2, S3)"),
    ("S6", "no regression: the 27 framed outside answers and the 14 Set B "
           "verdicts of Phase 89 unchanged; no earlier declared question is "
           "read by the new operation"),
    ("S7", "the class-T question (index 35) answered with the root bracketed "
           "to 1/10000 by exact bounds, gate verified"),
    ("S8", "a Lean file proves the identities the frames rest on (the "
           "rolling body for every moment-of-inertia factor, the invariant "
           "mass, the loop with a disturbance, the boundary-condition "
           "ratio, the output autocorrelation as a geometric series) with "
           "no sorry"),
)
