# Past the second derivation study: non-Shannon inequalities, rate distortion on the whole range, Robin spectra

## Tier 0 — the coarse read

**Question.** Can the GLM move past three of the limits the second derivation study drew (its §6) — a four-variable information inequality left `NOT_SHANNON`, rate distortion refused `NOT_TIGHT` past the Shannon lower bound's range, and eigenvalue problems with a Robin condition refused `TRANSCENDENTAL` — and answer them with a derivation a stand-alone script re-decides, while what it still cannot do stays refused by name?

**Verdict.** Yes, within the three declared operations: every declared case came out as declared, every answer verifies by its own script and every mutated claim is rejected by it, the three batteries are sound, the one Phase 107 refusal this round answers was narrowed as declared, nothing else the machine answers moved, and the Lean file proves what the operations rest on. 10 of 10 marks met.

**Deciding figure.** Information inequalities 8 of 8, rate-distortion sources 5 of 5, Robin problems 8 of 8, refusals 5 of 5; 21 of 21 scripts verify and 21 of 21 mutants rejected; 120 random inequalities (64 proved, 12 proved past Shannon, 41 not valid, 3 left undecided), 0 unsound, 0 inconsistent; 150 random sources (146 past the bound), 0 failures; 60 random Robin problems, 0 failures; Phase 107 11 of 11, 0 of 304 other texts moved; marks N1–N10 met.

**Recomputed by.** `glm_universal.runtime.derivation_three_report.derivation_three_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Phase 118. [`DERIVATION_TWO_STUDY.md`](DERIVATION_TWO_STUDY.md) §6 listed
what track P still could not do. Three of its items are derivations with a
checkable end, and the owner's direction — more reasoning, more scope — asks
for exactly that kind of step:

* **Information inequalities.** A four-variable claim with neither a
  Shannon-type certificate nor a counterexample of linear functions of fair
  bits was left `NOT_SHANNON`: "the machine knows no non-Shannon inequality
  to try". The Zhang–Yeung inequality is the first such inequality, and the
  Ingleton inequality the first that holds for linear (representable)
  distributions but not for all.
* **Rate distortion.** Hamming distortion was answered only where the
  Shannon lower bound is tight; past it the operation refused `NOT_TIGHT`.
* **Spectra.** A Robin condition `y'(e) + h·y(e) = 0` makes the eigenvalues
  roots of a transcendental equation, refused `TRANSCENDENTAL`.

The other items of that §6 — the three questions that ask for accounts (29,
39, 96), five or more variables, non-Hamming distortion, variable
coefficients — were left where they are, and five of them are declared
refusals of this round (mark N4).

## 1. Declarations — committed before any code

The cases, the expected values (worked by hand; the decimal Robin values by a
throw-away bisection kept nowhere in the package) and the marks are in
`overlay/glm_universal/evaluation/derivation_three_cases.py`, committed as the
round's first commit:

* **INEQUALITIES** (8): Zhang–Yeung and three renamings/rescalings
  (`proved_non_shannon`), Ingleton and a renaming (`NOT_VALID_ENTROPIC`),
  and two controls whose Phase 107 verdicts must not move (`proved`,
  `NOT_VALID`).
* **RATE_DISTORTION** (5): three sources past the bound — `[1/2, 1/3, 1/6]`,
  `[1/2, 1/4, 1/8, 1/8]` and `[2/5, 3/10, 1/5, 1/10]` (three pieces) — each
  with its breakpoints, the letters used on each piece and `R(D)` at a point
  of each new piece written in `log2`; two controls where the bound is tight
  throughout.
* **ROBIN** (8): Phase 107's own refused text (symbolic `L`), Dirichlet- and
  Neumann-Robin with positive, negative and weak `h`, Robin at the left end,
  and a longer interval — each with its characteristic equation, the
  interval holding `k_n`, the negative eigenvalue (absent, or its value) and
  the first three eigenvalues to six decimals.
* **REFUSALS** (5): five variables (`TOO_MANY_VARIABLES`), non-Hamming
  distortion (`UNSUPPORTED`), Robin at both ends (`TRANSCENDENTAL`), a
  variable coefficient and a symbolic `h` (`UNSUPPORTED`).
* Three batteries (120 claims, 150 sources, 60 problems, fixed seeds), the
  one Phase 107 case superseded (`eigen-robin`, which must now read
  `tan(k*L) = -k`), the Lean theorems, and marks N1–N10.

## 2. What was added

* `reasoning/non_shannon.py` — past the Shannon cone. A claim Phase 107
  leaves `NOT_SHANNON` is tried two ways more. **A certificate**: a linear
  program over the elemental inequalities, the givens and all 12 distinct instances
  of Zhang–Yeung on the four names; each instance used is itself certified
  by the copy lemma (a fifth variable `R`, a copy of one variable over two
  others, and an exact Shannon certificate over five variables). **An
  entropic counterexample**: a pool of distributions with rational
  probabilities on few atoms (37,941 laws), screened in
  integer fixed point and then decided exactly — every entropy is a rational
  combination of `log2` of primes, and the sign of such a combination is
  settled by comparing two integers. Neither found: `NOT_SHANNON` stays.
* `reasoning/hamming_rd.py` — the Erokhin form of `R(D)` on the whole range:
  past the bound the optimal reproduction uses the `k` most likely letters,
  `R(D) = H_k + (1 − D)·log2(1 − D) + T·log2(T/(k − 1))` with
  `T = D − (1 − P_k)`, on the piece between `1 − P_k + (k − 1)p_{k+1}` and
  `1 − P_k + (k − 1)p_k`. At a rational `D` the backward test channel and
  the dual (Lagrangian) point are rational, so the upper and lower bounds
  are the same sum of logarithms — an exact proof of the value. A
  Blahut–Arimoto iteration is run only as an independent cross-check, by
  the marks.
* `reasoning/robin.py` — the six Dirichlet/Neumann-Robin cases (positive,
  negative and weak `h`, either end): the characteristic equation, the
  interval of each `k_n`, the negative eigenvalue `−μ²` when present, and
  rational enclosures of each root by sign changes of the characteristic
  function, computed with fixed-point series for `sin`, `cos`, `sinh`,
  `cosh` and `π` with their remainders bounded.
* `runtime/derivation_three_scripts.py` (the column-3 scripts, importing
  nothing of the package), `runtime/derivation_three_frames.py` (the
  readings, handed over from Phase 107's operations at three points, with an
  `ENABLED` switch), `runtime/derivation_three_marks.py` (the marks that stay
  below the frames), `runtime/derivation_three_report.py` (N5 and N9) and
  the `derivation-three` subcommand of `glm_universal.tools`.
* Phase 107's mark Q7 narrowed by `PHASE_107_NARROWED`: its `eigen-robin`
  refusal is now accepted when answered with `tan(k*L) = -k`.

## 3. Results

```
N1  8/8 information inequalities as declared
N2  5/5 rate-distortion sources as declared
N3  8/8 Robin problems as declared
N4  5/5 refusals as declared at the layer, 5/5 through the frames
N5  21/21 scripts verify, 21/21 mutants rejected
N6  120 random claims: proved 64, proved_non_shannon 12, NOT_VALID 41, NOT_SHANNON 3; unsound 0, inconsistent 0, script failures 0
N7  150 random sources (146 past the bound): tiling 0, discontinuities 0, SLB mismatches 0, below the bound 0, script failures 0, Blahut-Arimoto failures 0
N8  60 random Robin problems: script failures 0, Newton outside 0, negative eigenvalue wrong 0, interval failures 0
N9  Phase 107: 11 of 11 marks; 0 of 304 other texts moved
N10 Lean: file present, no theorem missing, no sorry
10 of 10 marks met
```

In one line: Yes, within the three declared operations: every declared case came out as declared, every answer verifies by its own script and every mutated claim is rejected by it, the three batteries are sound, the one Phase 107 refusal this round answers was narrowed as declared, nothing else the machine answers moved, and the Lean file proves what the operations rest on. 10 of 10 marks met.

Information inequalities 8 of 8, rate-distortion sources 5 of 5, Robin
problems 8 of 8, refusals 5 of 5, at the layer and through the frames. On
the inequality battery 12 of the 120 random claims were proved only with
Zhang–Yeung instances, and 3 were left undecided (`NOT_SHANNON`) — the mark
reports that number rather than requiring it to be zero, since Zhang–Yeung
is one of infinitely many non-Shannon inequalities and the counterexample
pool is finite. On the rate-distortion battery 146 of the 150 sources had a
range past the bound; the worst Blahut–Arimoto disagreement was about
2·10⁻⁸ bits. On the Robin battery the cases drawn were 22 Dirichlet with
positive `h`, 16 Neumann with positive `h`, 12 Neumann with negative `h`, 8
Dirichlet with a negative eigenvalue and 2 weak Dirichlet. The 304 texts
that did not move are the other outside questions, Set B and the evaluation
cases; 11 of them are read by both the old and the new layer and give the
same answer.

## 4. Notes on the way

* **Ingleton is refuted by an entropic law, not a linear one.** The
  Ingleton inequality holds for every distribution of linear functions of
  fair bits, so Phase 107's GF(2) search can never refute it. The law on
  four atoms `(0,0,0,0)`, `(1,1,1,1)`, `(1,0,1,0)`, `(1,0,0,1)` with
  probabilities `1/3, 1/3, 1/6, 1/6` violates it by exactly
  `2·log 3 − 3·log 2` (nats) — positive because `9 > 8`. The machine finds
  that law in its pool and prints the exact difference; the Lean file
  proves it.
* **"Not Shannon" is not "false".** Zhang–Yeung has a polymatroid witness
  (Phase 107 printed it) and still holds for every distribution. The
  verdict `proved_non_shannon` keeps the two facts apart: the reading cites
  both the copy-lemma certificate and the fact that no Shannon certificate
  exists.
* **The Robin control case moved Phase 107.** `eigen-robin` was a declared
  refusal there. Rather than let a later round silently change an earlier
  round's declared verdict, the change was declared in this round's case
  file before the code, and Phase 107's mark narrowed to it (N9).

* **No float, even in the cross-checks.** The first full close failed the
  package's no-float rule (directive D7): the pool screen, the
  Blahut–Arimoto iteration and Newton's method had been written in floating
  point. All three now run in integer fixed point (a base-2 logarithm read
  bit by bit by squaring, `e^(−s)` from its series in exact rationals, sine
  and cosine from their series), the floating-point helpers left the
  reasoning package, and the full measurement was re-taken: every figure
  above came out the same.

## 5. What is proved

`overlay/glm_lean/RequestProject/GLM/NonShannon.lean`, with no sorry and only
the standard axioms (`propext`, `Classical.choice`, `Quot.sound`):

* `zhang_yeung_of_copy` — for any set function on five variables meeting the
  Shannon inequalities, the copy conditions (the fifth variable a copy of
  the third over the first and fourth — equal entropies on the four named
  marginals — and conditionally independent of the second and third given
  the first and fourth) give the Zhang–Yeung inequality on the first four: the copy-lemma certificate the operation
  emits is sound.
* `zhang_yeung_not_shannon` — a polymatroid (integer, checked by `decide`)
  meets every Shannon inequality and violates Zhang–Yeung: no Shannon-type
  proof of it exists.
* `ingleton_violated` — under the four-atom law above,
  `I(A;B) − (I(A;B|C) + I(A;B|D) + I(C;D)) = 2·log 3 − 3·log 2 > 0`.
* `rd_dual_lower_bound` — for a slope `s ≥ 0` and positive weights `μ` with
  `Σₓ p(x)μ(x)e^(−s·d(x,y)) ≤ 1` for every `y`, every channel with
  distortion at most `D` has mutual information at least
  `Σₓ p(x) log μ(x) − sD`: the lower half of the exact rate-distortion
  value.
* `robin_root_exists` — for `h, L > 0` and every `n ≥ 1` the characteristic
  equation `k·cos(kL) + h·sin(kL) = 0` has a root in
  `((n − 1/2)π/L, nπ/L)`.
* `robin_eigenfunction` — at any root `k` of that equation, `sin(kx)`
  solves `y'' + k²y = 0`, vanishes at 0 and meets `y'(L) + h·y(L) = 0`.

## 6. Limits

* **The copy lemma itself is not in Lean.** `zhang_yeung_of_copy` proves
  the inequality *given* a fifth variable with the copy conditions; that
  such a variable exists for every distribution is the textbook
  construction, not formalised here.
* **Non-Shannon inequalities stop at Zhang–Yeung.** Claims needing other
  non-Shannon inequalities (Dougherty–Freiling–Zeger, Matúš) or a larger
  pool stay `NOT_SHANNON`; 3 of 120 battery claims did. Five or more
  variables are still `TOO_MANY_VARIABLES`.
* **Rate distortion** is still Hamming distortion only.
* **Robin spectra** need a Dirichlet or Neumann condition at the other end
  and a numeric `h`: Robin at both ends (`TRANSCENDENTAL`), a symbolic `h`
  and variable coefficients (`UNSUPPORTED`) stay refused. With a symbolic
  `L` the interval of each root is given but not the decimals.
* **The questions that ask for accounts** (29, 39, 96) are where Phase 107
  left them.

## 7. What the round moved

Under directive D15 the round moves **derivation** past three lines the last
round drew. Two of the three operations now return an exact proof where
there was a refusal (a copy-lemma certificate, a matched pair of rational
primal and dual points), and the third returns certified enclosures of
transcendental roots. It also moves **refusal**: `NOT_SHANNON` now means
"neither Shannon, nor Zhang–Yeung, nor a pool law decides it", a narrower
claim than before.

## 8. Re-running

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools derivation-three          # all marks
PYTHONPATH=. python3 -m glm_universal.tools derivation-three --quick  # batteries of 30, no outside comparison
PYTHONPATH=. python3 -m unittest glm_universal.tests.test_derivation_three
lake build RequestProject.GLM.NonShannon                             # from the project root
```
