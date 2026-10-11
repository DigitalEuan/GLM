# Past the third derivation study: the copy lemma in Lean, chained copies, five variables, any distortion matrix, Robin at both ends

## Tier 0 — the coarse read

**Question.** Can the GLM close the four lines the third derivation study left (its §6) — the copy lemma itself in Lean, information inequalities that need more than Zhang–Yeung or have five variables, rate distortion for distortions other than Hamming, and Robin problems at both ends, with a symbolic coefficient or with no decimals on a symbolic interval — with a derivation a stand-alone script re-decides, while what it still cannot do stays refused by name?

**Verdict.** Yes, within the declared operations: the copy lemma and Zhang–Yeung are proved in Lean for every finite distribution, every declared case came out as declared, every answer verifies by its own script and every mutated claim is rejected by it, the three batteries are sound, the four Phase 118 refusals this round answers were narrowed as declared, nothing else the machine answers moved, and none of Phase 118's three undecided battery claims is decided by two copies. 10 of 10 marks met.

**Deciding figure.** Information inequalities 9 of 9, rate-distortion sources 6 of 6, Robin problems 10 of 10, refusals 6 of 6; 25 of 25 scripts verify and 25 of 25 mutants rejected; 40 random five-variable claims (8 proved, 11 proved past Shannon, 12 not valid, 1 refuted by an entropic law, 8 left undecided), 0 unsound, 0 inconsistent; 60 random sources (12 with D_min = D_max, 13 Hamming), 0 failures; 40 random Robin problems, 0 failures; Phase 118 10 of 10, 0 of 304 other texts moved; marks P1–P10 met.

**Recomputed by.** `glm_universal.runtime.derivation_four_report.derivation_four_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Phase 119. [`DERIVATION_THREE_STUDY.md`](DERIVATION_THREE_STUDY.md) §6 listed
four lines, and the owner asked for exactly those to be cleaned up before the
next round's items:

* **The copy lemma itself was not in Lean.** `zhang_yeung_of_copy` proved
  Zhang–Yeung *given* a fifth variable with the copy conditions, not that one
  always exists.
* **Inequalities past Zhang–Yeung, and five or more variables.** Claims
  needing other non-Shannon inequalities stayed `NOT_SHANNON` (3 of Phase
  118's 120 battery claims); five variables were `TOO_MANY_VARIABLES`.
* **Rate distortion** was Hamming distortion only.
* **Robin spectra** needed a Dirichlet or Neumann condition at the other end
  and a numeric `h`; on a symbolic interval no number bounded a root.

The owner also asked that [`GLM_ACADEMIC_PAPER.md`](GLM_ACADEMIC_PAPER.md) be
kept up to date in every development run, as the record of the GLM as a
whole; it stood at Phase 101 and was brought to Phase 119 in this round (its
§19.15–§19.17, §20.6, §21.5 and §24.2), and the instruction is now a row of
the close checklist ([`ITERATE.md`](../ITERATE.md) §4.1).

## 1. Declarations — committed before the reasoning code

The Lean files came first (as Phase 117's did), then
`overlay/glm_universal/evaluation/derivation_four_cases.py`, committed before
any reasoning code of the round. The expected verdicts were worked by hand;
the decimal values were taken by throw-away floating-point computations (a
Blahut–Arimoto iteration with a bisection on the slope, a bisection on the
characteristic function) kept nowhere in the package; the two-copy derivation
of Matúš's case was located by a throw-away search over pairs of copy steps,
and the declaration is that the machine finds *a* two-copy certificate, not
which one.

* **INEQUALITIES** (9): Matúš's two-copy inequality and a renaming
  (`proved_by_copies`); five variables — subadditivity and a Markov chain
  (`proved`), conditioning that can increase (`NOT_VALID`), Zhang–Yeung with
  a fifth-variable term (`proved_non_shannon`), Ingleton with one
  (`NOT_VALID_ENTROPIC`); and the two Phase 118 controls.
* **RATE_DISTORTION** (6): an asymmetric binary distortion, the absolute and
  the squared error on three letters, a matrix with a positive floor
  (`D_min = 1`), a value at an asked point, and Hamming written as a matrix
  (the control: `h(1/4) − h(D)` exactly) — each with `D_min`, `D_max` and
  `R(D)` at the quarter points to six decimals.
* **ROBIN** (4), **ROBIN_SYMBOLIC** (4), **ROBIN_BOUNDS** (2): Robin at both
  ends (three numeric, one symbolic length), a symbolic `h` with a Dirichlet
  and with a Neumann end and with a symbolic length, a negative `h` on a
  symbolic length (cases in `L`), and the arctangent bounds for `h = 1` and
  `h = 3`.
* **REFUSALS** (6): six variables (`TOO_MANY_VARIABLES`), a symbolic source
  (`UNSUPPORTED`), a negative distortion (`UNREADABLE`), an asked `D` below
  `D_min` (`INFEASIBLE`), Robin at both ends with coefficients of opposite
  sign and a variable coefficient (`UNSUPPORTED`).
* Three batteries (fixed seeds), the four Phase 118 refusals this round
  answers instead (`PHASE_118_NARROWED`, with the fragment each answer must
  carry), the Lean theorems, and marks P1–P10.

## 2. What was added

* `RequestProject/GLM/CopyLemma.lean` — entropy of a variable on a finite
  probability space, conditional mutual information, Shannon's inequalities
  for every entropy function (`condMI_nonneg`, `entropicFn_shannon`), the
  copy law `p(ω₁)·p(ω₂)·[b(ω₁) = b(ω₂)] / P(b = b(ω₁))` with both marginals
  equal to the original law (`copy_fst`, `copy_snd`) and the copy
  conditionally independent of the original given `b` (`copy_condMI_zero`),
  packaged as `copy_lemma`; and `zhang_yeung_entropic`: Zhang–Yeung for the
  entropy function of every four variables, by building the copy and applying
  `GLM.NonShannon.zhang_yeung_of_copy`.
* `RequestProject/GLM/RobinBoth.lean` — the two-ended characteristic function
  `charBoth a b L k = (ab − k²)·sin(kL) + k(a + b)·cos(kL)`, a root in every
  `(nπ/L, (n + 1)π/L)` for `a, b, L > 0` (`robin_both_root_exists`), the
  eigenfunction `k·cos(kx) + a·sin(kx)` (`robin_both_eigenfunction`), and for
  one Robin end `kL − (n − ½)π = arctan(hL/(kL))` (`robin_root_arctan`) and
  the closed-form bounds (`robin_root_bounds`).
* `reasoning/copy_chain.py` — chained copies: single copies first, then two
  copies of the same variable over the same base, the second also over the
  first; every copy condition (`H(R, T) = H(x, T)` for each `T` in the base,
  `I(R; rest | base) = 0`) enters the exact simplex as an equality. The
  five-variable layer: Phase 107's search, the 60 Zhang–Yeung instances on
  every four of the five, and Phase 118's rational laws lifted (the fifth
  variable constant or equal to one of the others), every candidate decided
  exactly on the five-variable claim. `reasoning/info_inequality.py` gained a
  `max_variables` argument.
* `reasoning/general_rd.py` — any finite distortion matrix: `D_min`, `D_max`,
  and at the quarter points (and an asked `D`) an enclosure of `R(D)`: a
  bisection on a dyadic slope `t`, the Blahut–Arimoto iteration in integer
  fixed point choosing the reproduction law, the time-sharing mixture of the
  two end channels for the upper bound (its distortion checked to be at most
  `D` exactly), the dual point `μ(x) = 1/(c_max·Z(x))` for the lower bound
  (its feasibility checked exactly, every exponential a power of `t`), and
  every logarithm bracketed bit by bit. An enclosure whose ends round apart at
  six decimals is narrowed a thousandfold.
* `reasoning/robin_two.py` — Robin at both ends (`a, b > 0`; any other sign
  `UNSUPPORTED`), a symbolic coefficient (Phase 118's six cases read as a case
  split on the sign class of `h` or `hL`, with `h = 0` in closed form), a
  negative coefficient on a symbolic interval (the same split read in `L`),
  and the arctangent bounds.
* `runtime/derivation_four_scripts.py` (column-3 scripts: the copy conditions
  rebuilt from the steps' descriptions, the rate-distortion bounds recomputed
  with the script's own logarithms, Robin signs from the script's own series
  and `π`), `runtime/derivation_four_frames.py` (the readings, handed over at
  four points, with an `ENABLED` switch), `runtime/derivation_four_marks.py`,
  `runtime/derivation_four_report.py` and the `derivation-four` subcommand.
* Phase 118's mark N4 (through the frames) narrowed by `PHASE_118_NARROWED`.
  Two of those four texts are also, word for word, Phase 107 refusals
  (`inequality-five-variables`, `rd-non-hamming`); Phase 107's mark Q7 applies
  the same narrowing to those identical texts. That second application was
  decided after the case file was committed, and is recorded here as such.

## 3. Results

```
P1  9/9 information inequalities as declared
P2  6/6 rate-distortion sources as declared
P3  10/10 Robin problems as declared
P4  6/6 refusals as declared at the layer, 6/6 through the frames
P5  25/25 scripts verify, 25/25 mutants rejected
P6  40 random five-variable claims: proved 8, proved_non_shannon 11, NOT_VALID 12, NOT_VALID_ENTROPIC 1, NOT_SHANNON 8; unsound 0, inconsistent 0, script failures 0; Phase 118's battery: 0 of its 3 NOT_SHANNON claims decided by copies
P7  60 random sources (12 with D_min = D_max, 13 Hamming): script 0, width 0, monotone 0, convex 0, hamming 0, channel 0 failures
P8  40 random Robin problems: script 0, newton 0, interval 0, cases 0, bounds 0 failures
P9  Phase 118: 10 of 10 marks; 0 of 304 other texts moved (11 read both ways)
P10 Lean: both files present, no theorem missing, no sorry
10 of 10 marks met
```

In one line: Yes, within the declared operations: the copy lemma and Zhang–Yeung are proved in Lean for every finite distribution, every declared case came out as declared, every answer verifies by its own script and every mutated claim is rejected by it, the three batteries are sound, the four Phase 118 refusals this round answers were narrowed as declared, nothing else the machine answers moved, and none of Phase 118's three undecided battery claims is decided by two copies. 10 of 10 marks met.

Information inequalities 9 of 9, rate-distortion sources 6 of 6, Robin
problems 10 of 10, refusals 6 of 6, at the layer and through the frames. Both
Matúš cases were proved by a chain of two copies, as declared (each reading,
with its mutant, takes about a minute: the Shannon search, the Zhang–Yeung
instances, the pool and then the chains are tried in that order). On the
five-variable battery 11 of the 40 random claims were proved only with
Zhang–Yeung instances on four of the five, one was refuted by a lifted
rational law, and 8 were left undecided (`NOT_SHANNON`); the mark reports that
number rather than requiring it to be zero. Phase 118's battery was re-run
past Zhang–Yeung: chains are tried only on its three `NOT_SHANNON` claims, so
nothing else can move, and none of the three is decided by chains of up to two
copies — the mark reports that count, as declared, rather than requiring it.
On the rate-distortion battery 12 of the 60 sources have `D_min = D_max` (a
column of the matrix is cheapest for every letter) and have nothing to
enclose; every other enclosure verified by its script, was narrower than
`10⁻⁶`, and agreed with Phase 118's exact value on the 13 Hamming matrices.
The 304 texts that did not move are the other outside questions, Set B and the
evaluation cases; 11 of them are read both with the Phase 119 readings on and
off and give the same answer. Phase 118's report, with `PHASE_118_NARROWED`
applied, met all 10 of its marks, its own Phase 107 comparison included.

## 4. Notes on the way

* **A straight piece of `R(D)` defeated the first enclosure.** On a Hamming
  source with two equally likely letters, `R(D)` is straight where both
  letters leave the reproduction together. The bisection on the slope then
  converges to the one slope of that piece, and the longer iteration at the
  lower end pushed the channel's distortion past `D`, leaving no channel below
  it (`NO_ENCLOSURE` on one battery source). The bisection's own channel at
  that end, whose distortion was checked, is now kept beside the refined one;
  the upper bound is the time-shared chord, which is exact on a straight
  piece.
* **Six decimals need a narrower enclosure near a rounding boundary.** One
  battery value sat within `10⁻⁸` of a boundary at the sixth decimal; the two
  ends of its enclosure rounded apart and the script, rightly, refused the
  printed value. Such an enclosure is now narrowed a thousandfold before the
  value is printed.
* **The column-3 scripts recompute, they do not trust.** The rate-distortion
  script uses its own logarithm (squaring with outward rounding) and checks
  that its own enclosure is narrower than `10⁻⁶` and rounds to the printed
  value; the chain script rebuilds the copy conditions from the steps rather
  than reading them; the Robin scripts carry their own Taylor series and their
  own enclosure of `π` from Machin's formula.

## 5. What is proved

`overlay/glm_lean/RequestProject/GLM/CopyLemma.lean` and
`RobinBoth.lean`, with no sorry and only the standard axioms (`propext`,
`Classical.choice`, `Quot.sound`):

* `condMI_nonneg`, `entropicFn_shannon` — every conditional mutual
  information of finitely many finite random variables is `≥ 0`.
* `copy_lemma` — for every finite distribution and every variable `b` there is
  a finite space with two maps into the original whose law keeps every
  entropy through either map, on whose support `b` agrees through both, and
  under which the copy is conditionally independent of the original given `b`.
* `zhang_yeung_entropic` — Zhang–Yeung for every four variables, nothing
  assumed.
* `robin_both_root_exists`, `robin_both_eigenfunction` — the two-ended roots
  and eigenfunctions.
* `robin_root_arctan`, `robin_root_bounds` — the closed-form enclosure of each
  root on a symbolic interval.

Not in Lean: that a chain of two copies exists (it is the copy lemma applied
twice — the second time to the law the first produced — and the certificate
over six variables is checked exactly by its script, not by Lean); the
uniqueness of the root in each two-ended interval (argued in
`reasoning/robin_two.py`'s docstring, checked by sign changes in the
battery); the rate-distortion enclosures (each is checked exactly by its
script against `GLM.NonShannon.rd_dual_lower_bound` and the channel bound).

## 6. Limits

* **Six or more variables** stay `TOO_MANY_VARIABLES`. Claims that neither
  Zhang–Yeung nor chains of two copies decide stay `NOT_SHANNON` (8 of the 40 five-variable battery claims, and all 3 of Phase 118's undecided claims).
* **Rate distortion** needs a numeric source: a symbolic source is
  `UNSUPPORTED`; continuous sources are not read.
* **Robin at both ends** needs both coefficients positive; with a coefficient
  of the other sign the number of negative eigenvalues depends on `a`, `b`
  and `L` together and the problem is refused `UNSUPPORTED`. A symbolic
  coefficient is read at the far end only. Variable coefficients stay
  refused.
* **The questions that ask for accounts** (29, 39, 96) are where Phase 107
  left them; they are track E.

## 7. What the round moved

Under directive D15 the round moves **derivation** past the four lines the
last round drew: four refusals (`TOO_MANY_VARIABLES` for five variables,
`UNSUPPORTED` for a distortion matrix and for a symbolic `h`,
`TRANSCENDENTAL` for Robin at both ends) are now answers with scripts, and a
claim Zhang–Yeung does not decide can now be proved by two copies. It also
moves **refusal**: `NOT_SHANNON` is narrower again, and a refused Robin problem
now names why (a coefficient of the other sign). And the copy lemma, which
Phase 118 used without proof, is now a theorem.

## 8. Re-running

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools derivation-four          # all marks
PYTHONPATH=. python3 -m glm_universal.tools derivation-four --quick  # batteries of 10, no outside comparison
PYTHONPATH=. python3 -m unittest glm_universal.tests.test_derivation_four
lake build RequestProject.GLM.CopyLemma RequestProject.GLM.RobinBoth  # from the project root
```
