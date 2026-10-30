# The rest of track P: information, codes, spectra and the diagonal argument

## Tier 0 — the coarse read

**Question.** Can the GLM take the rest of track P — the eleven class-P outside questions Phase 106 left refused that are derivations (information inequalities, Kraft–McMillan, rate–distortion, maximum entropy, eigenvalue problems, transmission through a barrier, the radix-2 FFT, a rate posterior, compactness, Tarski) — and answer them with a derivation that a stand-alone script re-decides, while the three that are not derivations stay refused?

**Verdict.** Yes, within the eight declared operations: every declared case came out as declared, every answer verifies by its own script and every mutated claim is rejected by it, both batteries are sound with nothing left undecided, eleven outside questions that were refused are now answered, questions 29, 39 and 96 stay refused, and nothing else the machine answers moved. 11 of 11 marks met.

**Deciding figure.** Information inequalities 16 of 16, codes 11 of 11, rate distortion 5 of 5, maximum entropy 4 of 4, eigenvalue problems 6 of 6, transmission, FFT and posterior 13 of 13, refusals 14 of 14; 55 of 55 scripts verify and 55 of 55 mutants rejected; 400 random inequalities (293 not valid, 107 proved), 0 unsound, 0 undecided; 600 random codes (256 uniquely decodable), 0 disagreements, 0 Kraft violations; outside 11 of 11 answered, 0 of 292 other texts moved; marks Q1–Q11 met.

**Recomputed by.** `glm_universal.runtime.derivation_two_report.derivation_two_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Phase 107. [`DERIVATION_STUDY.md`](DERIVATION_STUDY.md) §6 left the rest of
track P refused: outside questions 19, 28, 29, 39, 49, 52, 54, 55, 56, 59,
81, 86, 95 and 96. The owner asked for the rest of track P this round. Read
one by one, eleven of the fourteen are derivations the machine could own;
three are not:

* **29** (a non-isothermal CSTR) asks to *explain* multiplicity and
  stability of steady states — an account of a phase portrait, not a
  derivation with a checkable end;
* **39** (model predictive control) asks how MPC *handles* constraints
  differently from PID — a comparison of practices;
* **96** (Tarski–Seidenberg over ℚ and ℤ) asks *why* a verification query
  becomes undecidable — an account that would rest on Matiyasevich's
  theorem, which nothing in the machine or its Lean development carries.

These three were declared to stay refused before any code was written, and
mark Q10 checks that they do.

## 1. Declarations — committed before any code

The cases, the expected values (worked by hand) and the marks are in
`glm_universal/evaluation/derivation_two_cases.py`, committed as the
first commit of the round, before any operation existed. Nothing in it was
changed after code was written.

| Set | Count | What is declared |
|---|---|---|
| `INEQUALITIES` | 16 | verdict: `proved` (ten, from non-negativity of mutual information to a four-variable chain), `NOT_VALID` (four), `NOT_SHANNON` (Zhang–Yeung and Ingleton) |
| `CODES` | 8 | unique decodability, prefix-freeness, Kraft sum, the shortest ambiguous string |
| `PREFIX_CONSTRUCTIONS` | 3 | the canonical prefix code for given lengths |
| `RATE_DISTORTION` | 5 | `R(D)` on the tight range, the range, the zero point, and where the bound is not tight |
| `MAXENT` | 4 | the density and its entropy |
| `EIGEN` | 6 | eigenvalues, index range, normalised eigenfunctions (Dirichlet, Neumann, mixed both ways, periodic twice) |
| `SCATTERING` | 5 | `T` and `R` for delta barrier, delta well, step above and below, step plus delta |
| `FFT` | 4 | stages, butterflies, nontrivial twiddles, output order |
| `POSTERIOR` | 4 | density, mode, the reading on the machine's rate grid |
| `REFUSALS` | 14 | the refusal code |
| `OUTSIDE_P2` | 11 | outside questions 19, 28, 49, 52, 54, 55, 56, 59, 81, 86, 95 and a fragment each answer must contain |
| `STAYS_REFUSED` | 3 | questions 29, 39 and 96 |
| `INEQUALITY_BATTERY` | — | 400 random inequalities on three variables, seed 10701 |
| `CODE_BATTERY` | — | 600 random binary codes, seed 10702 |

The marks:

* **Q1** every inequality case as declared; **Q2** every code and prefix
  construction; **Q3** every rate-distortion case; **Q4** every
  maximum-entropy case; **Q5** every eigenvalue problem; **Q6** every
  transmission, FFT and posterior case; **Q7** every refusal with its code.
* **Q8** every answered reading of Q1–Q6 verifies by its column-3 script,
  which shares no code with the layer, and the same script rejects a mutated
  claim.
* **Q9** the batteries: every Shannon certificate re-checked exactly and
  every `NOT_VALID` distribution recomputed to violate the claim (0 unsound),
  no three-variable inequality left `NOT_SHANNON` (0 undecided); the
  Sardinas–Patterson verdict agrees with a brute-force search for two
  parsings on every random code, every uniquely decodable code has Kraft sum
  at most 1, and every constructed code is prefix-free with the requested
  lengths.
* **Q10** the eleven outside questions answered with fragment and gate;
  29, 39 and 96 still refused; no other outside or Set B question changes
  verdict; the 177 evaluation cases unchanged.
* **Q11** a Lean file proves what the layer rests on, with no sorry.

## 2. What was added

Eight operations, each a question frame with three columns (answer,
derivation, stand-alone script):

* **`prove information inequality: GIVENS |- CLAIM`** —
  `reasoning/info_inequality.py`. A claim linear in entropies, conditional
  entropies and (conditional) mutual informations of up to four variables is
  written in joint entropies and decided three ways. *Proved*: an exact
  rational simplex finds non-negative multipliers of the elemental
  inequalities (plus any multiple of the givens) whose sum is the claim — a
  Shannon-type certificate, printed as `claim = Σ λ·(elemental)`.
  *`NOT_VALID`*: a distribution made of linear functions of fair bits
  (over GF(2)), whose entropies are ranks, violates the claim and meets the
  givens. *`NOT_SHANNON`*: no certificate exists — Farkas gives a
  polymatroid meeting every elemental inequality and violating the claim —
  and no linear distribution violates it; the reading says plainly that a
  non-Shannon inequality would be needed. Zhang–Yeung and Ingleton both land
  there, as declared.
* **`decide unique decodability: W1, W2, …`** and **`construct prefix code
  with lengths …`** — `reasoning/coding_theory.py`. Sardinas–Patterson with
  the dangling-suffix layers shown, the shortest ambiguous string with its
  two parsings (`010 = 01.0 = 0.10`), the Kraft sum, and the canonical
  prefix code (refused `KRAFT_VIOLATED` when the sum exceeds 1).
* **`derive rate distortion function for SOURCE source with hamming
  distortion`** — the Shannon lower bound `H(X) − H(D) − D·log(m−1)` together
  with the backward test channel that meets it. Where the test channel would
  need a negative probability the bound is not tight, and the reading prints
  the function only where it is: for the source `[1/2, 1/3, 1/6]` it gives
  `R(D)` on `[0, 1/3]`, `0` from `1/2`, and refuses `NOT_TIGHT` between.
* **`derive rate posterior for k = K errors in n = N bits [on the machine's
  grid]`** — the Beta posterior, its mode, and the reading on the six rates
  the machine's rate hunt uses; where the posterior peaks at the guard rate
  the reading says so and names the refusal `RATE_GRID_EXCEEDED`.
* **`derive maximum entropy density on SUPPORT [with CONSTRAINTS]`** —
  `reasoning/maxent.py`. Gaussian, exponential, uniform and the
  second-moment case, each with its entropy; an unbounded support without a
  moment is refused `UNBOUNDED`, an interval with a mean `TRANSCENDENTAL`.
* **`solve eigenvalue problem for Y(X): d2(Y)/dX2 + lambda*Y = 0; BC; BC`**
  — `reasoning/spectral.py`. The three sign cases of `λ` are settled by the
  determinant of the boundary rows, so `λ = 0` is admitted for Neumann and
  periodic and not for Dirichlet; the eigenfunctions are normalised. A Robin
  condition is refused `TRANSCENDENTAL` (its eigenvalues solve
  `tan(kL) = …`).
* **`derive transmission coefficient for V(x) = …`** — a delta, a step, or
  both at `x = 0`, solved from the matching conditions by complex Cramer's
  rule; `T = 1/(1 + g²/(4k²))` for the delta and `4k₁k₂/(k₁ + k₂)²` above a
  step.
* **`derive decimation-in-frequency fft for N = …`** (or `-time`) —
  `reasoning/fft_derivation.py`: the split of the DFT into two half-length
  DFTs, the butterflies stage by stage and the bit-reversed output order.

Around them: `runtime/derivation_two_scripts.py` writes the column-3 scripts
(exact rational arithmetic, importing nothing of the package),
`runtime/derivation_two_frames.py` the frames and the eleven outside frames,
`runtime/derivation_two_report.py` the scorer, `tools derivation-two` the
command and `tests/test_derivation_two.py` the tests. The dispatch is behind
the flag `DERIVATIONS_TWO` in `runtime/question_frames.py`; with it off, the
frame layer is exactly as Phase 106 left it.

Each outside frame recognises the situation and writes it in an operation's
terms: the ring's Hamiltonian becomes `psi'' + lambda*psi = 0` with periodic
conditions on `[0, 2*pi]`; the delta barrier a potential at one point; the
Markov chain the given `I(X;Z|Y) = 0`. Where a question also asks for an
account (*explain the physical significance*) the computed part is answered
and the rest is named, inside the reading, as the refusal `EXPLANATION`.

## 3. Results

```
Q1  16/16 information inequalities as declared
Q2  11/11 codes as declared
Q3  5/5 rate-distortion questions as declared
Q4  4/4 maximum-entropy laws as declared
Q5  6/6 eigenvalue problems as declared
Q6  13/13 transmission, FFT and posterior questions as declared
Q7  14/14 refusals as declared
Q8  55/55 scripts verify, 55/55 mutants rejected
Q9  400 random inequalities: NOT_VALID 293, proved 107; unsound 0, undecided 0, script failures 0
    600 random codes: 256 uniquely decodable; disagreements 0, Kraft violations 0, construction failures 0
Q10 outside: 11/11 answered with fragment and gate; 29, 39, 96 still refused; 0 of 292 other texts moved
Q11 Lean: file present, no theorem missing, no sorry
11 of 11 marks met
```

In one line: Yes, within the eight declared operations: every declared case came out as declared, every answer verifies by its own script and every mutated claim is rejected by it, both batteries are sound with nothing left undecided, eleven outside questions that were refused are now answered, questions 29, 39 and 96 stay refused, and nothing else the machine answers moved. 11 of 11 marks met.

Information inequalities 16 of 16, codes 11 of 11, rate distortion 5 of 5,
maximum entropy 4 of 4, eigenvalue problems 6 of 6, transmission, FFT and
posterior 13 of 13, refusals 14 of 14. On the inequality battery every
three-variable claim was decided — either a certificate or a GF(2)
counterexample — so `NOT_SHANNON` was never needed below four variables,
which is what the theory says (every three-variable entropy inequality is
Shannon-type, and every invalid one here was refuted by a distribution of
linear functions of fair bits). On the code battery the Sardinas–Patterson
verdict agreed with brute force on all 600 codes, and none of the 256
uniquely decodable codes had a Kraft sum above 1 — McMillan's theorem
holding on the sample, as it must. The 292 texts that did not move are the
other outside questions, Set B and the 177 evaluation cases.

The eleven outside questions now answered, each with its declared fragment:
19 (the delta barrier, `T = 1/(1 + m*alpha^2/(2*hbar^2*E))`), 28 (the
particle on a ring, `E_m = m^2*hbar^2/(2*I)`), 49 (the radix-2 DIF split,
`(x[n] - x[n + N/2])*W_N^n`), 52 (mutual information as a divergence,
`D(p(x,y) || p(x)*p(y))`), 54 (data processing, with the certificate
`I(X;Y) - I(X;Z) = I(X;Y|Z)` …), 55 (the Gaussian as maximum entropy,
`h = (1/2)*ln(2*pi*e*sigma^2)`), 56 (Kraft–McMillan,
`sum_i D^(-l_i) <= 1`), 59 (the binary source, `R(D) = H(p) - H(D)`), 81
(compactness, `has an infinite model`), 86 (Tarski, `is not definable`) and
95 (the rate posterior, `p^k*(1 - p)^(n - k)`).

**What three of them rest on.** For 56, 81 and 86 what the machine
*computes* is narrower than the general statement, and the readings say so.
For 56 it computes a worked code and its counting bound; for 86 it proves
the propositional core — `D <-> ~TD, TD <-> D |- false` — with the Phase 106
G4ip prover; for 81 it writes the compactness argument. The general
statements are carried by theorems of
`RequestProject/GLM/DerivationsTwo.lean` (§5), which the readings cite by
name. These three answers are *Lean-anchored*: their generality is a proved
theorem, not something the frame derived.

## 4. Notes on the way

* **The rate-distortion bound is not always the function.** The Shannon
  lower bound `H(X) − H(D) − D·log(m−1)` is easy to print on the whole range
  `0 ≤ D ≤ D_max`, but for a non-uniform source over three letters it is met
  only while the backward test channel is a channel; past that the true
  `R(D)` lies strictly above it. The operation checks the test channel's
  probabilities and refuses `NOT_TIGHT` on the gap rather than print a bound
  as the function; the case `skewed-ternary` was declared to need exactly
  that, and it does.
* **`NOT_SHANNON` is a verdict, not a failure.** A claim with no Shannon
  certificate and no linear counterexample is not "unproved" in the sense of
  a search that ran out: Farkas' lemma gives a polymatroid witness that no
  Shannon-type proof exists. The reading prints the witness, so the claim
  "no proof of this kind exists" is checkable — the same standard Phase 106
  set with Kripke countermodels for classical verdicts.

## 5. What is proved

`glm_lean/RequestProject/GLM/DerivationsTwo.lean`, with no sorry and
only the standard axioms (`propext`, `Classical.choice`, `Quot.sound`;
`lawvere_fixed_point` uses none):

* `gibbs_inequality` — `D(p ‖ q) ≥ 0`, with equality only at `p = q`;
  `mutual_information_nonneg` — `I(X;Y) ≥ 0`, zero only for independence.
* `shannon_certificate_sound` — a certificate `c = Σ λᵢEᵢ + Σ μⱼGⱼ` with
  `λ ≥ 0` proves `c · h ≥ 0` for every `h` meeting the elemental
  inequalities and the givens: what the inequality prover emits is sound.
* `data_processing` — for any set function meeting the Shannon
  inequalities, `I(X;Z|Y) = 0` gives `I(X;Y) ≥ I(X;Z)`.
* `kraft_mcmillan` — every uniquely decodable code over `D ≥ 2` symbols has
  `Σ D^(−lᵢ) ≤ 1` (the counting argument: the `n`-th power of the Kraft sum
  is at most `n·Σlᵢ + 1`).
* `dif_even`, `dif_odd` — the radix-2 decimation-in-frequency split, over
  any commutative ring.
* `posterior_increasing` — `p^a (1−p)^b` increases strictly up to its mode.
* `rd_test_channel` — the backward test channel of the binary source is a
  channel, reproduces the source, and the binary entropy is increasing on
  `[0, 1/2]`.
* `delta_transmission`, `delta_transmission_energy` — the matching
  conditions at a delta barrier, `|t|² = 1/(1 + g²/(4k²))`,
  `|r|² + |t|² = 1`, and the energy form.
* `ring_eigenfunction`, `dirichlet_eigenfunction` — the eigenfunctions
  solve their equations, meet their conditions and are normalised.
* `lawvere_fixed_point` and `tarski_undefinability` — the diagonal argument:
  in any interpretation with diagonal sentences and negation, no formula
  defines truth.
* `infinite_model_of_large_finite_models` — a first-order theory with
  arbitrarily large finite models has an infinite model (from Mathlib's
  compactness theorem).

## 6. Limits

*Phase 118 took the second, third and fourth items below past these limits
(a non-Shannon inequality, rate distortion on the whole range, one Robin
end); see [`DERIVATION_THREE_STUDY.md`](DERIVATION_THREE_STUDY.md).*

* **Three questions stay refused** — 29, 39 and 96, for the reasons in §0.
  They ask for accounts, not derivations.
* **Information inequalities stop at four variables** (`TOO_MANY_VARIABLES`),
  and a `NOT_SHANNON` claim is left undecided: the machine knows no
  non-Shannon inequality to try.
* **Rate distortion** is Hamming distortion only (`UNSUPPORTED` otherwise),
  and only where the Shannon lower bound is tight.
* **Spectra** are constant-coefficient second-order problems with
  separated or periodic conditions; Robin conditions and variable
  coefficients are refused.
* **The general form of 56, 81 and 86** is the Lean theorem, not the
  frame's own derivation (§3).

## 7. What the round moved

Under directive D15 the round moves **derivation** again: eight more
operations produce a derivation with an independent script, and two of them
(the inequality prover and the code decider) return a *witness* on the
negative side as well as a proof on the positive — a GF(2) distribution, a
polymatroid, an ambiguous string. It also moves **refusal**: `NOT_TIGHT`,
`NOT_SHANNON` and `EXPLANATION` name precisely what the machine will not
claim.

## 8. Re-running

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools derivation-two          # all marks (under a minute)
PYTHONPATH=. python3 -m glm_universal.tools derivation-two --quick  # batteries of 100
PYTHONPATH=. python3 -m unittest glm_universal.tests.test_derivation_two
lake build RequestProject.GLM.DerivationsTwo                       # from the project root
```
