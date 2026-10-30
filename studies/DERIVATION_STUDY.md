# Derivations and proofs: the machine produces a derivation

## Tier 0 — the coarse read

**Question.** Can the GLM derive, rather than look up: prove or refute a propositional sequent with a checkable proof or countermodel, derive the equations of motion of a Lagrangian with its small oscillations, derive the transfer functions of a dynamic model, and solve a boundary value problem in flux form — each answer re-decided by a stand-alone script that shares no code with the layer?

**Verdict.** Yes, within the four declared operations: every declared case came out as declared, every answer verifies by its own script and every mutated claim is rejected by it, the prover is sound and complete on the random battery, four questions of the outside set that were refused are now answered, and nothing else the machine answers moved. 9 of 9 marks met.

**Deciding figure.** Proofs 16 of 16, equations of motion 8 of 8, transfer models 6 of 6, profiles 6 of 6, refusals 8 of 8; 36 of 36 scripts verify and 36 of 36 mutants rejected; 2000 random formulas (1769 not valid, 149 intuitionistic, 82 classical, each classical one with a Kripke countermodel), 0 unsound, 0 gaps; outside class P 4 of 4 answered, 0 of 299 other texts moved; marks R1–R9 met.

**Recomputed by.** `glm_universal.runtime.derivation_report.derivation_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Phase 106. The owner judged that the retrieval round 9 items still open —
the AST index follow-ups ([`AST_INDEX_STUDY.md`](AST_INDEX_STUDY.md) §8) and
the citation-scope follow-ups
([`CITATION_SCOPE_STUDY.md`](CITATION_SCOPE_STUDY.md) §6) — were not
producing strong results, and asked for work that moves the machine's
reasoning instead. Both studies now carry a *Disposition (Phase 106)*
section: their working operations stay, their follow-ups are parked.

The round taken instead is track **P, derivations and proofs**, the second
boundary named in [`QUESTION_SET_B_STUDY.md`](QUESTION_SET_B_STUDY.md) §8:
18 outside questions ask for a proof or a general derivation (calculus,
Lagrangians, PDEs, information inequalities), and the machine refused all of
them because no register holds a derivation. Of the three things a round can move under directive D15 — derivation,
addressing, refusal — derivation had the least behind it.

## 1. Declarations — committed before any code

The cases, the expected values (worked by hand) and the marks are in
`glm_universal/evaluation/derivation_cases.py`, committed as the
first commit of the round, before the prover or the derivation layer
existed. Nothing in it was changed after code was written.

| Set | Count | What is declared |
|---|---|---|
| `PROOFS` | 16 | sequent, verdict (`intuitionistic`, `classical`, `NOT_VALID`), falsifying valuation where unique |
| `MOTION` | 8 | each Euler–Lagrange equation up to a coordinate-free factor; linearisation and squared frequencies for small oscillations |
| `TRANSFER` | 6 | each transfer function as a rational function in `s` |
| `PROFILES` | 6 | the profile, identically |
| `REFUSALS` | 8 | the refusal code |
| `OUTSIDE_P` | 4 | outside questions 18, 24, 30, 85 and a fragment each answer must contain |
| `PROVER_BATTERY` | — | 2000 random formulas, seed 10601, 3 atoms, depth 4 |

The marks:

* **R1** every proof case as declared; **R2** every motion case; **R3** every
  transfer case; **R4** every profile; **R5** every refusal with its code.
* **R6** every answered reading of R1–R4 verifies by its column-3 script, and
  the same script rejects a mutated claim.
* **R7** the prover battery: every emitted proof re-checked rule by rule by an
  independent checker and every proved formula a tautology by truth table
  (0 unsound); every `NOT_VALID` carries a falsifying valuation; every
  tautology answered (0 gaps).
* **R8** the four outside questions answered with fragment and gate; no other
  outside or Set B question changes verdict; the 177 evaluation cases
  unchanged.
* **R9** a Lean file proves what the layer rests on, with no sorry.

## 2. What was added

Four operations, each a question frame with three columns (answer,
derivation, stand-alone script):

* **`prove: PREMISES |- GOAL`** — `reasoning/proof_search.py`. A G4ip
  sequent prover (Dyckhoff's contraction-free calculus, so the search
  terminates and is complete for intuitionistic propositional logic). If no
  intuitionistic proof exists the formula is decided by truth table; a
  tautology is then proved from the fewest instances of excluded middle, and
  a Kripke countermodel of at most four worlds is searched to show *why*
  there is no constructive proof. A non-tautology is refused with a
  falsifying valuation. Curry's paradox
  (`C <-> (C -> F) |- F`) gets a 9-step constructive proof; Peirce's law
  gets a proof from excluded middle on `p` and a two-world countermodel.
* **`derive equations of motion for Q1, Q2[, small oscillations]: L = …`** —
  `reasoning/derivation.py`. Euler–Lagrange by exact symbolic
  differentiation (the time derivative by the chain rule `q → q_dot →
  q_ddot`), each equation divided by the factor free of the dynamics and
  stated nonzero; for small oscillations, the linearisation about the
  origin (refused `NOT_EQUILIBRIUM` when the origin is not one), the mass
  and stiffness matrices and the squared frequencies from
  `det(K − w²M) = 0` through the nonlinear layer. The double pendulum gives
  `w² = (2 ± sqrt(2))*g/l`.
* **`derive transfer functions from U… to Y: EQ; …`** — the model is
  linearised about its steady state in deviation variables,
  Laplace-transformed and solved; each output over each input is a rational
  function in `s`.
* **`solve boundary value problem for Y(X): d/dX(P*d(Y)/dX) = G; BC; BC`** —
  flux form with `P` a monomial and `G` a polynomial, two quadratures, the
  constants fixed by value, derivative or `bounded at 0` conditions.

Around them: `runtime/derivation_scripts.py` writes the column-3 scripts
(exact rational arithmetic, importing nothing of the package),
`runtime/derivation_frames.py` the frames and four outside frames (an
`n`-link chain pendulum, Curry's paradox in words, the spherical film with
a stagnant-gas second track, the heated tank), `runtime/derivation_report.py`
the scorer, `tools derivation` the command and `tests/test_derivation.py`
the tests. The dispatch is behind the flag `DERIVATIONS` in
`runtime/question_frames.py`.

## 3. Results

```
R1  16/16 proofs as declared
R2  8/8 equations of motion as declared
R3  6/6 transfer models as declared
R4  6/6 profiles as declared
R5  8/8 refusals as declared
R6  36/36 scripts verify, 36/36 mutants rejected
R7  2000 random formulas: NOT_VALID 1769, intuitionistic 149, classical 82;
    unsound 0, gaps 0, script failures 0; classical with a Kripke countermodel 82
R8  outside class P: 4/4 answered with fragment and gate; 0 of 299 other texts moved
R9  Lean: file present, no theorem missing, no sorry
9 of 9 marks met
```

In one line: Yes, within the four declared operations: every declared case came out as declared, every answer verifies by its own script and every mutated claim is rejected by it, the prover is sound and complete on the random battery, four questions of the outside set that were refused are now answered, and nothing else the machine answers moved. 9 of 9 marks met. Every mark is met, R1–R9. Proofs 16 of 16, equations of motion 8 of 8,
transfer models 6 of 6, profiles 6 of 6, refusals 8 of 8. The battery
emitted 82 classical verdicts and every one of them came with a Kripke
countermodel, so the claim "no constructive proof exists" is witnessed and
not just the output of a failed search. The 299 texts that did not move are
the other outside questions, Set B and the 177 evaluation cases: nothing
else the machine answers changed verdict.

The four outside questions now answered: 18 (the double pendulum's
equations and modes — the answer contains
`2*l*th1_ddot + l*th2_ddot + 2*g*th1 = 0`), 24 (two tanks — a transfer
function containing `(C1 - C2)*R1*R2`), 30 (the heated tank,
`1/(rho*F*Cp)`) and 85 (Curry's paradox — `F follows`).

## 4. Defects found on the way

* **A crash in the nonlinear layer.** On the triple pendulum the
  characteristic cubic is in *casus irreducibilis*: its three real roots
  have no expression in real radicals. `_cardano` in
  `reasoning/symbolic_nonlinear.py` received `None` from the real square
  root and failed with a `TypeError`. It now refuses with
  `SymbolicError NONLINEAR`, which the frame reports as a refusal of the
  modes while still answering the equations of motion.
* **A divisor the script did not know.** The central-force angular equation
  is the Euler–Lagrange expression divided by `m*r`, a factor containing a
  coordinate. The first script assumed a constant ratio between the claim
  and the Euler–Lagrange expression and so would have rejected a correct
  answer. The answer now states its divisor (`m != 0 and r != 0`), and the
  script checks that the divisor times the claim *is* the Euler–Lagrange
  expression and that the divisor is nonzero at every point it uses.

## 5. What is proved

`glm_lean/RequestProject/GLM/Derivations.lean`, with no sorry and
only the standard axioms:

* `g4ip_sound` — every G4ip derivation is sound for every Boolean
  valuation: the sequent rules the prover uses cannot prove a non-tautology.
* `curry_derivation` — from `C ↔ (C → F)`, `F`.
* `slab_profile`, `cylinder_profile`, `sphere_profile` — the three shell
  profiles satisfy their equations and boundary values.
* `double_pendulum_modes` — `(2 ± √2) g/l` are the roots of the double
  pendulum's characteristic polynomial.

## 6. Limits

* **The rest of track P.** Questions 19, 28, 29, 39, 49, 52, 54, 55, 56,
  59, 81, 86, 95 and 96 stay refused: information inequalities,
  Kraft–McMillan, rate–distortion, PDE derivations beyond flux-form ODEs,
  and proofs that are not propositional.
* **Modes in letters from a cubic.** When the characteristic polynomial is
  a cubic in casus irreducibilis the squared frequencies have no real radical
  form; the machine refuses them. A trigonometric form, or a numeric track
  with exact bounds, is the open item.
* **Propositional only.** The prover has no quantifiers; first-order and
  arithmetic proofs are outside it.

## 7. What the round moved

Under directive D15 the round moves **derivation**. Before it, a derivation
could be checked if it was written out, but not produced; the four
operations produce one — a proof or countermodel, a symbolic derivation —
with an independent script. It also moves **refusal** in one place: the
casus irreducibilis crash is now a named refusal.

## 8. Re-running

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools derivation            # all marks (a few minutes)
PYTHONPATH=. python3 -m glm_universal.tools derivation --quick    # a battery of 200
PYTHONPATH=. python3 -m unittest glm_universal.tests.test_derivation
```
