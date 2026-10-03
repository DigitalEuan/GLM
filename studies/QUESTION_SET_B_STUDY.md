# The outside question sets — Set B, Outside O1, and the Capability Failure Matrix

## Tier 0 — the coarse read

**Question.** What do the two outside question sets the owner supplied in Phase 89 find, and how far can declared question frames, each answer checked by its own column-3 script, carry the machine into them?

**Verdict.** Before this round the router read none of the 126 questions; with declared question frames, every Set B item and 27 outside questions are read and answered or correctly refused, each checked by its column-3 script, with no confidently wrong answer.

**Deciding figure.** Set B: 14 of 14 by audit (protocol +10: 11 right, 1 disputed answer); Outside O1: 27 of 112 framed and correct, 0 wrong, 85 located boundaries in six classes; 41 framed questions, 0 verdicts changed by the contract variant; 177 of 177 contract questions identical through the routed `-q`.

**Recomputed by.** `glm_universal.evaluation.question_set_b.report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

The owner's Phase 89 request: two outside question sets, now in
`source_material/` —
`Improved_Question_Set_B_Benchmark_Suite.txt` ("Set B": 14 JSON items
`O1-001`..`O1-014`, each with an expected status, a refusal code and three
columns) and `Outside_Question_Set_B_candidate_O1.txt` ("Outside O1": 112
questions — nine subject sections of ten at Medium/Hard/Very Hard, ten
questions written against the GLM benchmark, and twelve critical engineering
questions). Set B is expected to be within reach; Outside O1 is written to
find boundaries, and a refusal there is a located boundary (directive D15),
to be logged in a **Capability Failure Matrix** and built on. The same
request settled K1 — route `-q` through the multi-surface router (Option A),
with the typed planner set aside or tried as a quick validation check — and
asked for candidate P's two contract changes to be run as a 4-way matrix
([`CONTRACT_MATRIX_STUDY.md`](CONTRACT_MATRIX_STUDY.md)).

## 1. The baseline — before any frame

Every question was given to the router as written. Set B: 0 of 14 read by
any surface but the planner, and all 14 refused generically (`parse_query`,
`unsolved: resolve`, "not recognised"). Outside O1: 0 of 112 meaningful
answers — 110 generic refusals and 2 vacuous answers ("… denotes nothing
determinate", questions 71 and 82). The machine had the *mathematics* for most
of Set B (the agree-channel census, the complete decoder, the rate posterior,
the stepwise planner, the integer procedure, the dialect loop) but no reader
for the *English* the questions are written in.

## 2. What was built

**Declared question frames** —
`glm_universal/runtime/question_frames.py` (13 frames for the Set B kinds)
and `glm_universal/runtime/outside_frames.py` (26 frames for the kinds Outside
O1 located). A frame is a recogniser that pulls the givens out of the text
and an answerer that computes from those givens — through the machine's own
modules wherever one exists (`agree_channel_marks.agree_cell`,
`carried_fork.carry`, `law_absorption.confidence`,
`confidence_floor.floor_check`, `rate_posterior.decode_soft`,
`engineering.union.derive_across`, the stepwise planner, the integer
procedure, the dialect's planner bridge) and through the exact algebras of
`glm_universal/reasoning/exact_forms.py` elsewhere: surds `a + b√c`,
logarithm forms `r + Σ c_p log₂ p` (every entropy of a distribution with
rational masses is exactly one), and Sturm root isolation. Every decimal
printed is a truncation of an exact process (`real_expr`), never a float.
Nothing is looked up by question: `tests/test_question_frames.py` changes
the givens of ten frames and checks the answers move with them.

**The column-3 gate.** Each reading carries a stand-alone script that
recomputes its answer by an **independent** route — it rebuilds the 4096
Golay codewords from twelve generators instead of calling the decoder,
raises a log identity to an integer power instead of summing a series,
checks a Routh range at its ends and its marginal root, re-samples an
aliased signal — and must end `VERIFIED True`. The script runs under
`python3 -I` with a 5-second budget **before** the reading is output; a
script that fails turns the reading into the refusal `SCRIPT_GATE_FAILED`
(the test `test_a_reading_the_gate_rejects_is_refused` builds one). On the 41
framed questions every script passed.

**The router's `frames` surface**, tried after the Python surface and before
engineering (order `toolbox, reverse, python, frames, engineering,
planner`). Non-interference, as `ConnectedMachine.lean`'s `route_cons_none`
makes it a count: the frames read **0** of the 382 declared questions of the
contract, engineering, cognition and Python sets, and 0 of the 1,584
declared strings in every evaluation module; a frame never reads text
beginning *given …* (the planner's phrasing) and hands its own rewrites to
the router *below* itself.

## 3. Set B — 14 of 14 by audit

| id | reader | verdict | file expects | protocol | audited |
|---|---|---|---|---|---|
| O1-001 | `agree_operating` | retention 0.979633…, residual 4.6120e-5 | VERIFIED_TRUE | +1 | +1 |
| O1-002 | `octad_pair` | REFUSED AMBIGUOUS (2 survive) | AMBIGUOUS | +1 | +1 |
| O1-003 | `error_weight` | REFUSED UNCORRECTABLE | UNCORRECTABLE | +1 | +1 |
| O1-004 | `declared_rate_floor` | REFUSED BELOW_FLOOR (posterior 150094635296999121/193036414974201856) | BELOW_FLOOR | +1 | +1 |
| O1-005 | `floor_range` | REFUSED FLOOR_OUT_OF_RANGE | FLOOR_OUT_OF_RANGE | +1 | +1 |
| O1-006 | `rate_grid` | REFUSED RATE_GRID_EXCEEDED | RATE_OUT_OF_RANGE | 0 | +1 |
| O1-007 | `across_wheels_values` | power = 500 W | VERIFIED_TRUE | +1 | +1 |
| O1-008 | `energy_light` | REFUSED NO_LICENSED_JUNCTION | DERIVATIONS_DISAGREE | 0 | +1 |
| O1-009 | `heat_level` | REFUSED LEVEL_AS_DIFFERENCE | LEVEL_AS_DIFFERENCE | +1 | +1 |
| O1-010 | `stepwise_givens` | REFUSED INCONSISTENT_GIVENS | INCONSISTENT_GIVENS | +1 | +1 |
| O1-011 | `integer_entails` | ENTAILS over ℤ (INDEPENDENT over ℚ) | VERIFIED_TRUE | +1 | +1 |
| O1-012 | `loop_least` | r = 13 ohm | VERIFIED_TRUE | +1 | +1 |
| O1-013 | `integer_system` | decided: x = 2, y = -1 | INTEGER_UNDECIDED | −1 | +1 |
| O1-014 | `rate_grid` | REFUSED RATE_GRID_EXCEEDED | RATE_GRID_EXCEEDED | +1 | +1 |

**Protocol +10** (the file's own scoring: 11 right, 2 refusals under another
code, 1 answer where the file expects a refusal). **Audited +14.** The audit
(`question_set_b_cases.SET_B_AUDIT`, written from the file and the machine's
modules before the frames ran) differs from the file on three items and
qualifies three:

* **O1-013** — the file expects `INTEGER_UNDECIDED` because "the splinter
  search depth exceeds configured limits". For `3x + 5y = 1` it does not:
  `gcd(3, 5) = 1`, the integer procedure decides the system, and
  `x = 2, y = -1` is a witness (`QuestionSetB.lean`:
  `int_linear_solvable_iff`, `three_five_witness`). Refusing would be a false
  refusal; the machine answers, and the reading records the disputed
  premise.
* **O1-006** — the machine's code for a guard-peaked rate posterior is
  `RATE_GRID_EXCEEDED` (which the file itself uses in O1-014);
  `RATE_OUT_OF_RANGE` is not a machine code.
* **O1-008** — the machine refuses because no declared junction licenses
  W5 = W10 (the naive union would give `2·m·c²`); `DERIVATIONS_DISAGREE` is
  the stepwise planner's code for two derivations of one target with
  different values, which is not what happens. The new code
  `NO_LICENSED_JUNCTION` names the machine's reason.
* Qualified: **O1-001**'s `Fraction(2449, 2500)` and `Fraction(461,
  10000000)` are roundings of the exact retention and residual (the machine
  prints the exact fractions in column 2); **O1-002**'s "6 survive" is wrong
  for two distinct tetrads of one octad — exactly 2 survive (the sent word
  and the octad), 6 only when both reads carry the same tetrad; **O1-004**'s
  `6561/8437` is not the posterior — the exact value is
  `150094635296999121/193036414974201856 ≈ 0.777545`, below the floor
  either way. **O1-003**: the refusal rests on the *declared* weight —
  without it the decoder would answer, wrongly, at distance 3
  (`weight_five_miscorrects`).

## 4. Outside O1 — the Capability Failure Matrix

27 of 112 are read by a frame and answered (or, for the Nyquist question,
correctly refused) exactly, each value audited by hand against an
independent derivation and checked by its gated script; **0 are confidently
wrong**. The other 85 are located boundaries. Classes
(`question_set_b_cases.BOUNDARY_CLASSES`):

| class | meaning | count |
|---|---|---|
| F | framed: answered or correctly refused exactly | 27 |
| E | explanation: a conceptual or causal account with no single checkable value | 32 |
| P | proof or general derivation (calculus, Lagrangians, PDEs, information inequalities) | 18 |
| M | meta: about the GLM's own engineering (scoring, sandboxing, Lean templates) | 18 |
| S | symbolic parameters: the answer is a formula in letters | 13 |
| D | design or diagram: a circuit, block diagram, sketch, controller design | 3 |
| T | transcendental equation needing a function the exact layer lacks (arctan) | 1 |

By section (F = framed):

| section | F | E | P | S | M | D | T |
|---|---|---|---|---|---|---|---|
| Electrical engineering | 5 | 2 | 0 | 2 | 0 | 1 | 0 |
| Physics | 2 | 0 | 2 | 6 | 0 | 0 | 0 |
| Chemistry and chemical | 4 | 1 | 3 | 2 | 0 | 0 | 0 |
| Process control and dynamics | 3 | 1 | 2 | 1 | 0 | 2 | 1 |
| Signal processing | 6 | 1 | 1 | 2 | 0 | 0 | 0 |
| Information Theory | 5 | 0 | 5 | 0 | 0 | 0 | 0 |
| The Elements | 0 | 10 | 0 | 0 | 0 | 0 | 0 |
| Nuclear Physics & Isotopes | 0 | 10 | 0 | 0 | 0 | 0 | 0 |
| Logic | 0 | 7 | 3 | 0 | 0 | 0 | 0 |
| Questions designed to match the GLM benchmark | 1 | 0 | 2 | 0 | 7 | 0 | 0 |
| 12 critical engineering questions | 1 | 0 | 0 | 0 | 11 | 0 | 0 |

**What the 27 answers are** (hand audit): Routh ranges `0 < K < 48` with
`ω = 2√2`, and `−1/4 < K_c < 5/2` (`0 < K_c < 5/2` for a positive gain) with
`ω = 1`, `P_u = 2π`; per-unit `1/5` p.u.; ROC `−1 < Re(s) < 3`, non-causal;
`Γ_L = −1/5 − j2/5`, `|Γ| = √5/5`, VSWR `(3 + √5)/2 ≈ 2.618034`; Nyquist
`Z = N + P = −2` refused as inconsistent; fringe `m₁ = 3` (with `m₂ = 4`);
well probability `1/4`; Arrhenius `T₂ ≈ 311.024 K`; Nernst `E ≈ 1.04816 V`;
`ΔS = 3R ln(3/2) ≈ 10.1136 J/K`; SO₃ equilibrium `x ≈ 0.461223 atm`
(isolated to width 1e-12); FOPDT `y(2) = 0`, `y(7) = 3(1 − e⁻¹) ≈ 1.896361`,
`y(∞) = 3`; Kalman: controllable and observable (both ranks 2); aliasing to
`{200, 300}` Hz with the 800 Hz sine folded to `−3 sin(2π·200t)`;
`X(z)` with ROC `1/2 < |z| < 3`, DTFT exists; convolutions `[1, 1, 1, −3]`
and `[−2, 1, 1]`; bilinear `H(z) = (1 + z⁻¹)/(6 − 2z⁻¹)`, `Ω = ∞ → z = −1`;
decimation: no aliasing (the copies just touch at ±π); Wiener
`h₀ = 86/161`, `h₁ = 40/161`; `H(X,Y) = 3/2`, `H(X) = H(Y) = 2 − (3/4)log₂3`,
`H(Y|X) = (3/4)log₂3 − 1/2`, `I = 5/2 − (3/2)log₂3`; Huffman `L = 7/4`,
efficiency `≈ 0.995850`; BSC `C = 1 − H(0.11) ≈ 0.500084`, uniform input;
alternating channel `1/2` bit per use; water-filling `(6, 4, 0)` W,
`C = log₂7 − (1/2)log₂3`; Golay `[23,12,7]` perfect, `[24,12,8]`
quasi-perfect with 1771 weight-4 cosets of 6 tetrads each; the coset-weight-4
tie: no tie-break from the read alone beats 1 time in 6, so the machine
refuses AMBIGUOUS and carries the fork.

**Two vacuous answers** (71, 82): the planner's denotation frame "answers"
that the question's text denotes nothing determinate. Not a wrong value, but
an answer where a refusal is due — a located defect of the planner, recorded
for the next round.

### 4.1 Every question
| # | set | diff | n | class | reader | verdict (first words) |
|---|---|---|---|---|---|---|
| 0 | EE | M | 1 | E | planner | refused (generic) |
| 1 | EE | M | 2 | F | frame `routh_cubic` | stable for 0 < K < 48; marginal K = 48, sustained oscillation at omega = 2*sqrt(2) rad/s,  |
| 2 | EE | M | 3 | F | frame `per_unit_base` | 1/5 p.u. (= 0.2000) |
| 3 | EE | M | 4 | D | planner | refused (generic) |
| 4 | EE | H | 1 | E | planner | refused (generic) |
| 5 | EE | H | 2 | F | frame `roc` | ROC: -1 < Re(s) < 3; the system is non-causal (two-sided: the right-half-plane pole makes  |
| 6 | EE | H | 3 | F | frame `reflection` | Gamma_L = -1/5 - j2/5, /Gamma_L/ = 1/5*sqrt(5) (= 0.447213...), VSWR = 3/2 + 1/2*sqrt(5) ( |
| 7 | EE | H | 4 | S | planner | refused (generic) |
| 8 | EE | VH | 1 | S | planner | refused (generic) |
| 9 | EE | VH | 2 | F | frame `nyquist` | refused INCONSISTENT_GIVENS: Z = N + P = -2 + 0 = -2: a number of closed-loop right-half- |
| 10 | Ph | M | 1 | S | planner | refused (generic) |
| 11 | Ph | M | 2 | S | planner | refused (generic) |
| 12 | Ph | M | 3 | S | planner | refused (generic) |
| 13 | Ph | M | 4 | F | frame `fringe_coincidence` | m1 = 3 (it coincides with order m2 = 4 of the other wavelength, at path difference 1800 nm |
| 14 | Ph | H | 1 | S | planner | refused (generic) |
| 15 | Ph | H | 2 | F | frame `infinite_well` | P = 1/4 |
| 16 | Ph | H | 3 | S | planner | refused (generic) |
| 17 | Ph | H | 4 | S | planner | refused (generic) |
| 18 | Ph | VH | 1 | P | planner | refused (generic) |
| 19 | Ph | VH | 2 | P | planner | refused (generic) |
| 20 | Ch | M | 1 | F | frame `arrhenius` | T2 = 1/(1/298 - R ln 3/65000) = 311.024... K |
| 21 | Ch | M | 2 | F | frame `nernst` | E = 11/10 - (RT/2F) ln(170/3) = 1.04816... V |
| 22 | Ch | M | 3 | F | frame `gas_entropy` | Delta S = 3*R*ln(3/2) = 3*R*(-ln(2) + ln(3)) = 10.1136... J/K (R = 8.31446261815324 J/(mol |
| 23 | Ch | M | 4 | E | planner | refused (generic) |
| 24 | Ch | H | 1 | P | planner | refused (generic) |
| 25 | Ch | H | 2 | F | frame `equilibrium` | x = 0.461223... atm: P(SO3) = 1.0775, P(SO2) = 0.9224, P(O2) = 0.4612 atm (x isolated in a |
| 26 | Ch | H | 3 | S | planner | refused (generic) |
| 27 | Ch | H | 4 | S | planner | refused (generic) |
| 28 | Ch | VH | 1 | P | planner | refused (generic) |
| 29 | Ch | VH | 2 | P | planner | refused (generic) |
| 30 | PC | M | 1 | P | planner | refused (generic) |
| 31 | PC | M | 2 | F | frame `fopdt_step` | y(0) = 0; y(2) = 0; y(7) = 3(1 - e^-1) = 1.896361...; y(infinity) = 3 |
| 32 | PC | M | 3 | E | planner | refused (generic) |
| 33 | PC | M | 4 | S | planner | refused (generic) |
| 34 | PC | H | 1 | F | frame `routh_cubic` | stable for -1/4 < K_c < 5/2 (with a positive gain, 0 < K_c < 5/2); marginal K_c = 5/2, sus |
| 35 | PC | H | 2 | T | planner | refused (generic) |
| 36 | PC | H | 3 | D | planner | refused (generic) |
| 37 | PC | H | 4 | D | planner | refused (generic) |
| 38 | PC | VH | 1 | F | frame `kalman_rank` | controllability matrix [1 -1; 1 -3] has rank 2/2: completely controllable; observability m |
| 39 | PC | VH | 2 | P | planner | refused (generic) |
| 40 | SP | M | 1 | F | frame `aliasing` | components at 200, 300 Hz: reconstructed x_r(t) = 5cos(2 pi 300 t) - 3sin(2 pi 200 t) |
| 41 | SP | M | 2 | F | frame `z_transform` | X(z) = 1/(1 - 1/2 z^-1) + 1/(1 - (-3) z^-1) = (2 + 5/2 z^-1)/((1 - 1/2 z^-1)(1 - (-3) z^-1 |
| 42 | SP | M | 3 | F | frame `convolution` | linear y_L = [1, 1, 1, -3]; 3-point circular y_C = [-2, 1, 1]: y_C[n] = sum_k y_L[n + k3]  |
| 43 | SP | M | 4 | E | planner | refused (generic) |
| 44 | SP | H | 1 | F | frame `bilinear` | H(z) = (1 + z^-1)/(6 - 2 z^-1) = 1/6(1 + z^-1)/(1 - 1/3 z^-1); Omega = infinity maps to z  |
| 45 | SP | H | 2 | S | planner | refused (generic) |
| 46 | SP | H | 3 | F | frame `decimation` | Y(e^jw) = (1/3) sum_(k=0)^2 X(e^(j(w - 2 pi k)/3)); the band edge 1/3pi stretches to 1pi,  |
| 47 | SP | H | 4 | S | planner | refused (generic) |
| 48 | SP | VH | 1 | F | frame `wiener` | h0 = 86/161 (= 0.534161...), h1 = 40/161 (= 0.248447...); minimum MSE = 43/161 |
| 49 | SP | VH | 2 | P | planner | refused (generic) |
| 50 | IT | M | 1 | F | frame `joint_entropy` | H(X) = 2 - 3/4*log2(3) (= 0.811278...), H(Y) = 2 - 3/4*log2(3) (= 0.811278...), H(X,Y) = 3 |
| 51 | IT | M | 2 | F | frame `huffman` | code A=0, B=10, C=110, D=111; L = 7/4 bits/symbol; H(X) = 7/5 - 3/20*log2(3) + 1/4*log2(5) |
| 52 | IT | M | 3 | P | planner | refused (generic) |
| 53 | IT | M | 4 | F | frame `bsc_capacity` | C = 1 - H(11/100) = -1 - 2*log2(5) + 11/100*log2(11) + 89/100*log2(89) (= 0.500084...) bit |
| 54 | IT | H | 1 | P | planner | refused (generic) |
| 55 | IT | H | 2 | P | planner | refused (generic) |
| 56 | IT | H | 3 | P | planner | refused (generic) |
| 57 | IT | H | 4 | F | frame `memory_channel` | 1/2 bits per channel use on average (identity steps carry 1 bit, BSC(1/2) steps carry 0) |
| 58 | IT | VH | 1 | F | frame `water_filling` | P = (6, 4, 0) W (water level nu = 7); C = -1/2*log2(3) + log2(7) (= 2.014873...) bits per  |
| 59 | IT | VH | 2 | P | planner | refused (generic) |
| 60 | El | M | 1 | E | planner | refused (generic) |
| 61 | El | M | 2 | E | planner | refused (generic) |
| 62 | El | M | 3 | E | planner | refused (generic) |
| 63 | El | M | 4 | E | planner | refused (generic) |
| 64 | El | H | 1 | E | planner | refused (generic) |
| 65 | El | H | 2 | E | planner | refused (generic) |
| 66 | El | H | 3 | E | planner | refused (generic) |
| 67 | El | H | 4 | E | planner | refused (generic) |
| 68 | El | VH | 1 | E | planner | refused (generic) |
| 69 | El | VH | 2 | E | planner | refused (generic) |
| 70 | Nu | M | 1 | E | planner | refused (generic) |
| 71 | Nu | M | 2 | E | planner | vacuous answer ("denotes nothing determinate") |
| 72 | Nu | M | 3 | E | planner | refused (generic) |
| 73 | Nu | M | 4 | E | planner | refused (generic) |
| 74 | Nu | H | 1 | E | planner | refused (generic) |
| 75 | Nu | H | 2 | E | planner | refused (generic) |
| 76 | Nu | H | 3 | E | planner | refused (generic) |
| 77 | Nu | H | 4 | E | planner | refused (generic) |
| 78 | Nu | VH | 1 | E | planner | refused (generic) |
| 79 | Nu | VH | 2 | E | planner | refused (generic) |
| 80 | Lo | M | 1 | E | planner | refused (generic) |
| 81 | Lo | M | 2 | P | planner | refused (generic) |
| 82 | Lo | M | 3 | E | planner | vacuous answer ("denotes nothing determinate") |
| 83 | Lo | M | 4 | E | planner | refused (generic) |
| 84 | Lo | H | 1 | E | planner | refused (generic) |
| 85 | Lo | H | 2 | P | planner | refused (generic) |
| 86 | Lo | H | 3 | P | planner | refused (generic) |
| 87 | Lo | H | 4 | E | planner | refused (generic) |
| 88 | Lo | VH | 1 | E | planner | refused (generic) |
| 89 | Lo | VH | 2 | E | planner | refused (generic) |
| 90 | GB | M | 1 | F | frame `golay_perfect` | [23,12,7] is perfect: 2^12 * (1+23+253+1771) = 2^12 * 2048 = 2^23, radius-3 spheres tile F |
| 91 | GB | M | 2 | M | planner | refused (generic) |
| 92 | GB | M | 3 | M | planner | refused (generic) |
| 93 | GB | M | 4 | M | planner | refused (generic) |
| 94 | GB | H | 1 | M | planner | refused (generic) |
| 95 | GB | H | 2 | P | planner | refused (generic) |
| 96 | GB | H | 3 | P | planner | refused (generic) |
| 97 | GB | H | 4 | M | planner | refused (generic) |
| 98 | GB | VH | 1 | M | planner | refused (generic) |
| 99 | GB | VH | 2 | M | planner | refused (generic) |
| 100 | CE | T1 | 1 | M | planner | refused (generic) |
| 101 | CE | T1 | 2 | M | planner | refused (generic) |
| 102 | CE | T1 | 3 | M | planner | refused (generic) |
| 103 | CE | T2 | 1 | F | frame `deep_hole_tie` | no tie-break chosen from the read alone can be better than guessing: the 6 nearest codewor |
| 104 | CE | T2 | 2 | M | planner | refused (generic) |
| 105 | CE | T2 | 3 | M | planner | refused (generic) |
| 106 | CE | T3 | 1 | M | planner | refused (generic) |
| 107 | CE | T3 | 2 | M | planner | refused (generic) |
| 108 | CE | T3 | 3 | M | planner | refused (generic) |
| 109 | CE | T4 | 1 | M | planner | refused (generic) |
| 110 | CE | T4 | 2 | M | planner | refused (generic) |
| 111 | CE | T4 | 3 | M | planner | refused (generic) |

Sets: EE electrical, Ph physics, Ch chemistry, PC process control, SP signal
processing, IT information theory, El the elements, Nu nuclear, Lo logic, GB
written against the GLM benchmark, CE the twelve critical engineering
questions. `#` is the 0-based position in the file.

## 5. K1 — `-q` through the router

`GLM.py -q` now goes through the multi-surface router (Option A): a question
the planner reads is answered exactly as before, with its trace kept for
`--export-trace` and the stepwise planner consulted only on a refusal; any
other surface prints as `--ask` prints it (the `frames` surface with its
three columns and the gate's line). `--plan` keeps the pre-Phase-89 typed
planner path; `--grammar`, `--domain` and `--eng` keep theirs.

**The contract set through the command line**, as K1 asked: all 177
questions of `evaluation.cases.CASES` give byte-identical output and exit
codes through the routed `-q` and through `--plan` (177 of 177; 151
answered, 26 refused on both paths) — the router changes no contract
verdict.

**The typed planner as a validation check.** `--cross-check` asks the typed
planner the same text after a routed answer from another surface. On the 41
framed questions it answers **0**: as a validator of the outside sets'
answers it has nothing to say, so it stays set aside. The validation check
that does carry weight is the column-3 gate of §2, which re-derives every
framed answer independently before output; the typed planner should be
tried again as a cross-check once it reads frames of its own.

## 6. Candidate P on the question sets

`question_set_b.variant_run` re-reads every framed question (41: 14 Set B and
27 Outside) under each of the four contract variants of
[`CONTRACT_MATRIX_STUDY.md`](CONTRACT_MATRIX_STUDY.md), with a fresh session
of frame reads per variant. A, B, C and D each answer 31 and refuse 10 with
the same codes; **0 verdicts differ** from the control. The question sets
fix the rate wherever a confidence is asked for (O1-001 and O1-004 declare
`p = 1/10`), and the two rate-estimate items (O1-006, O1-014) are guard
refusals under every rule — so they do not discriminate between the
variants; the decision rests on the exhaustive census of the matrix study.

## 7. What is proved

`RequestProject/GLM/QuestionSetB.lean` (built, no `sorry`, standard axioms
only):

* `int_linear_solvable_iff` — `a x + b y = c` has an integer solution iff
  `gcd a b ∣ c` (the `integer_system` frame's rule); `three_five_witness`.
* `int_entails_ceil`, `rat_not_entails` — `2x ≥ 5` entails `x ≥ 3` over ℤ
  and not over ℚ.
* `weight_five_miscorrects` — a five-point error inside an octad leaves the
  read 3 from a different codeword (with `GLM.Golay24.unique_octad`
  supplying the octad).
* `routh_marginal_root` — at the marginal gain, `s = iω` with
  `ω² = a₁/a₃` is a root of the cubic.
* `nyquist_inconsistent` — `N + P < 0` admits no closed loop.
* `upper_rule_safe` — the production contract's upper-credible rule never
  overstates the confidence when the true rate is within the credible set.
* The audit's exact values: `golay23_perfect`, `golay24_not_perfect`,
  `deep_hole_cosets`, `fringe_least`, `wiener_taps`, `per_unit_rebase`,
  `reflection_coefficient`, `vswr_value`.

`RequestProject/GLM/QuestionSetBAnswers.lean` (begun in this round, completed
and first built in Phase 90; no `sorry`, standard axioms only) proves the
framed answers themselves from each question's givens, where the mathematics
is in reach. It has 40 theorems:

* Control: the Routh ranges `0 < K < 48` and `-1/4 < K_c < 5/2` and their
  marginal roots, the two Kalman ranks and the FOPDT step response.
* Signals: aliasing at the samples, convolution, the bilinear map, the
  z-transform's region of convergence and value, and the Wiener error.
* Physics: the infinite well's `1/4`.
* Information: the joint and mutual information, Huffman's length and its
  optimality, the binary symmetric channel's capacity at `p = 0.11`, the
  memory channel and water-filling, with its level, allocation, optimality
  and capacity.

## 8. The boundaries, as the next tracks

Ordered by how many questions each would move and how far the machine
already is from it:

1. **S, symbolic parameters (13).** Every one is a closed formula in
   letters (`a = (2/3) g sin θ`, `M = m₀ √(2(1 + γ))`, `U = Nε/(e^{ε/kT}+1)`,
   `R_yy[m] = a^{|m|}/(1 − a²)`). The exact layer computes with numbers;
   a small polynomial/rational-function algebra over named parameters, with
   the gate checking the formula at random rational points, would take most
   of this class.
2. **P, derivations and proofs (18).** Half are standard derivations whose
   *result* is checkable (`I(X;Y) ≥ 0` with equality iff independent,
   Kraft–McMillan, `R(D) = H(p) − H(D)`, the Gaussian's differential
   entropy); the frames can state and gate the result, and the Lean side can
   carry the proof where Mathlib has it.
3. **M, meta (18).** These ask about the GLM's own engineering — the
   scoring rule, the `python3 -I` sandbox, Lean templates, overflow in exact
   arithmetic, the splinter cap. The answers exist in the studies; a frame
   that answers from the project's own documents (the address book and the
   corpus) is the route.
4. **E, explanations (32).** The Elements, nuclear physics and logic
   sections ask *why*. No exact frame answers them; the honest reading is the
   current refusal. The periodic-table and nuclide registers could anchor
   the factual parts (Z, N, magic numbers, binding energies), leaving the
   explanation as a refusal.
5. **D (3), T (1).** Designs and diagrams stay refusals; arctan would close
   the one transcendental equation (`ω_co` of `e^{−0.5s}/(s+1)` solves
   `0.5ω + arctan ω = π`), and is a small addition to `transcendental.py`.
6. **The two vacuous answers** — the planner's denotation frame should refuse
   a text that is a question rather than a term.

## 9. Re-running

`PYTHONPATH=. python3 -m glm_universal.tools question-set-b` from `overlay/`
(about a minute and a half; `--json` for the rows, `--no-variants` to skip
§6). `GLM.py -q '<question>' -c 1,2,3` for one question with its three
columns and gate line. Tests: `glm_universal/tests/test_question_frames.py`.
