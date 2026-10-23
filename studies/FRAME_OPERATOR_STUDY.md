# Frame operators — Lorentz boosts in exact arithmetic, operators inferred layer by layer, and the anchor κ = 190 kJ/mol

## Tier 0 — the coarse read

**Question.** Taking the owner's `Lorentz boosts.pdf` further: can the GLM carry out rational Lorentz boosts exactly, infer an unknown frame operator from example pairs by reading the invariant layer first and fitting in the light-cone layer, and never confuse a change of frame with a change of units; and what does the work-energy anchor κ = 190 kJ/mol actually do, how fine is it, and what is it for?

**Verdict.** Yes, within the declared families. The boost arithmetic held on every one of 78,161 exact checks, and 26 theorems in `RationalBoost.lean` prove it in general. `tool frame` answered 703 of 1,620 in-vocabulary queries outright and every one of the rest after a single asked example, with 0 wrong answers; outside the vocabulary it refused all 360, but only after an evidence guard was added between the first and second take. Light along one ray cannot tell a frame from a unit change, so all 270 such queries were refused; light along both rays can, which broke one declared mark (F4). κ is a unit: no dimensionless output depends on it. It is the bromine dissociation energy to within the register's ±0.3 kJ/mol, and its digits are the smallest of the four precision knobs.

**Deciding figure.** 17 of 18 marks (F4 missed); integrity failures 0 of 78,161; in-vocabulary wrong answers 0 of 1,620 (first-fit control 376); after one ask 1,620 of 1,620 right; outside-vocabulary wrong 207 at the first take, 0 at the second; κ shifts 0.105 %, 0.158 %, 0.435 %, 1.55 %.

**Recomputed by.** `glm_universal.reasoning.frame_operator_study.frame_operator_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 21 October 2026 (measured the same day, in one session). The marks
were written into `reasoning/frame_operator_study.py` and committed before the
first measurement (commit "Phase 177 (pre-registration)"). After the first take
the mechanism gained one rule, the evidence guard; §7.2 says why and gives both
takes. No mark was changed.*

## 0. What this document is

A study for Phase 177, taken at the owner's request of 21 October 2026. The
owner's document
[`source_material/Lorentz boosts.pdf`](../source_material/Lorentz%20boosts.pdf)
extends the pipeline kit
([`PIPELINE_KIT_STUDY.md`](PIPELINE_KIT_STUDY.md)) towards dimension
projection, layered stacking and operational use for ARC-style puzzles and
general reasoning: like the formula wheels, but a method for working things
out rather than a table of laws. The document has three parts:

1. a reading of a Lorentz boost as a puzzle "move" whose invariant core is the
   rest mass, with `c` as the calibration dial and `c = 1` as natural units;
2. a section placing the anchor `κ = 190 kJ/mol` beside `c` as the microscopic
   dial, with an uncompiled Lean sketch of a "relativity calibration wheel";
3. a review recommending two studies: **A**, exact transformation integrity
   (rational boosts checked for invariance, inverse, composition, branch and
   unit consistency), and **B**, operator inference (learn `B(u)` from pairs
   without being told `u`; then a mixed benchmark of rotations, boosts,
   permutations and unit conversions where the machine must infer which
   structure applies). It also asks that the physical claims be kept separate.

This round does A and B, and answers the owner's three questions about `κ`:
how it works for calibration, how much more refined it could be, and what use
it has for the GLM.

## 1. Corrections to the source, carried into the work

The review's corrections are taken as given, and the work is built so that each
one is enforced rather than just stated:

* **A boost changes the frame; it does not accelerate anything.** `tool frame`
  calls it a change of frame, and the families are coordinate maps.
* **`E = m` holds only in the rest frame.** The tool reports `E² − p²` of the
  answer against the query, never `E`.
* **Setting `c = 1` changes units; it does not derive `c`.**
  `Calibration.substrate_c_is_circular` already proves the chain returns the
  `c` it was given. `KappaAnchor.cellLength_ratio_kappa_free` proves the same
  for `κ`: setting the dial moves no dimensionless output.
* **The Leech lattice is Euclidean; spacetime is not.** `int_boost_trivial`
  shows more: an *integer* lattice with the form `E² − p²` carries no
  non-trivial boost at all (`a² − b² = 1` over `ℤ` forces `b = 0`). Boosts
  therefore run on `ℚ`, with denominators that grow (§7.6), and no map onto
  the Leech lattice is attempted. That third version of the review's Study B
  is left out, for this stated reason.
* **The minimum tax is `8Q = 3.117…`, not `3`.** The repository's `refIndex`
  already takes `T₀` as a parameter. §6 measures how much rounding `27` from
  `27.117…` moves things against `κ`.
* **The Lean sketch was unchecked.** It is replaced by `RationalBoost.lean`,
  which compiles. The sketch's `RationalBoost` structure required `γ²(1 − β²)
  = 1` with a rational `γ`; `rational_boost_param` shows the `u`-family below
  is exactly the set of such boosts.

## 2. What is proved

**`overlay/glm_lean/RequestProject/GLM/RationalBoost.lean`** (namespace
`GLM.RationalBoost`; 26 theorems, 0 `sorry`). For rational `u` with `u² ≠ 1`,
`a(u) = (1+u²)/(1−u²)` and `b(u) = 2u/(1−u²)`, and `B(u)` is the boost with
entries `a`, `−b`, `−b`, `a`:

* `ca_sq_sub_sb_sq` (`a² − b² = 1`), `boost_inv` (`E² − p²` kept),
  `boost_zero`, `boost_neg_boost` (inverse), `boost_boost` and
  `compose_abs_lt_one` (`B(u)B(v) = B((u+v)/(1+uv))`, which stays in
  `(−1, 1)`), `sb_div_ca` and `abs_beta_lt_one` (`β = 2u/(1+u²)`, `|β| < 1`),
  `boost_future` (future timelike stays future timelike);
* **the light-cone layer:** `inv_eq_plus_mul_minus`, `boost_plus`,
  `boost_minus` (a boost divides `E + p` by the Doppler factor
  `k = (1+u)/(1−u)` and multiplies `E − p` by it), `doppler_compose`
  (composition multiplies Doppler factors);
* `rational_boost_param`: every boost with rational entries is `B(b/(a+1))`.
  `int_boost_trivial`: no integer boost other than `±1`;
* **frame against units:** `scale_inv` (a change of units multiplies the
  invariant by `s²`), `scale_boost_comm`, `null_confound` and
  `null_confound_example` (on the light ray `(e, e)` a boost *is* the
  rescaling by `1/k`; `B(1/2)` and the rescaling by `1/3` agree on `(1, 1)`),
  `null_confound_opposite` and `null_rays_separate` (on the other ray it is
  the rescaling by `k`, so light from both directions separates the two;
  proved after the first take, §7.3), `timelike_separates` (one state with
  `E² − p² ≠ 0` fixes the scale and the boost together), `boost_determined`;
* **the invariant as a classifier:** `rot_euclid` (a rotation keeps
  `E² + p²`), `boost_not_euclid`, `rot_not_inv` (neither family keeps the
  other's form unless it is trivial).

**`overlay/glm_lean/RequestProject/GLM/KappaAnchor.lean`** (namespace
`GLM.KappaAnchor`; 11 theorems, 0 `sorry`), on top of `Calibration.lean`:
`cellLength_ratio_kappa_free`, `ratio_free_of_c`, `tick_scale_inv`,
`tick_relative_change`, `kappa_within_br2_d0`, `kappa_tick_ratio_d0`
(`950/951`), `kappa_tick_ratio_bde` (`190/193`), `quantity_choice_dominates`,
`kappa_relative_uncertainty_lt`, `tax_rounding_dominates_kappa`,
`kappa_eV_bounds` (`1.9692 eV`).

`lake build` succeeds. Both files are imported by `AxiomAuditAll.lean`, whose
guard now covers 9,722 theorems, all on the standard axioms.

## 3. The mechanism

`overlay/glm_universal/reasoning/frame_operators.py`, reached as `tool frame
E,p -> E',p' ; … ? E,p` (exact rationals). It works in three stacked layers;
this is the part meant to carry over to other domains (§8):

1. **The invariant layer (classify).** Read off which quadratic form each pair
   keeps (`E² − p²`, `E² + p²`), or whether one ratio scales both. Each family
   has a necessary signature, and a family whose signature fails is not fitted.
2. **The diagonal layer (fit).** Fit each family in the coordinates where it
   acts by scaling: light-cone `(E+p, E−p)` for boosts, unit changes and their
   products, the complex number `E + ip` for rotations and their products.
   Parameters are exact ratios. A parameter that no pair reaches stays free.
3. **The gate (answer, refuse, ask).** Answer only when every fitting family
   gives the query one output **and** at least one of them is *checked*: it has
   fewer parameters than the independent equations the pairs supply (two per
   dimension of the span of the inputs). Otherwise refuse, say which families
   disagree, and name an input to ask about, preferring a massive state.

Families: `identity`, `swap`, `parity` (no parameter); `units`, `boost`,
`rotation` (one); `boost_units`, `rotation_units` (two).

`overlay/glm_universal/reasoning/kappa_anchor.py`, reached as `tool kappa
[VALUE in kJ/mol]`: the chain at an anchor (work energy, eV per particle,
tick, cell, wavelength), the κ-free sweep, the anchor's source in the GLM's
registers, and the refinement budget.

Measured by `reasoning/frame_operator_study.py`
(`python3 -m glm_universal.tools frame-operators`, a few seconds).

## 4. What is measured, and the marks

Exactly as declared in the module before the first measurement.

**A. Exact integrity.** Every `u = m/n` with `1 ≤ n ≤ 12`, `|m| < n` (91
parameters) on every integer state with `|E|, |p| ≤ 6` (169 states):

* **E1** `E² − p²` kept; **E2** `B(−u)B(u) = id`; **E3**
  `B(u)B(v) = B((u+v)/(1+uv))` (`n ≤ 6` for both); **E4** future timelike
  kept; **E5** light-cone path equals the matrix path; **E6** unit
  consistency: boosting in joules then converting to work units of `κ/N_A`
  equals converting first; **E7** every rational boost built from an
  independent parameter `r` (`a = (r + 1/r)/2`, `b = (r − 1/r)/2`) is
  `B(b/(a+1))`. Each must have 0 failures.

**B. Operator inference.** Eleven task families: eight in the declared
families, one composite that belongs to them (`boost_chain3`, three boosts in
turn), and two that do not (`boost_then_rotate`, `shear`). Thirty queries each
at one, two and three demonstrations, with timelike demonstrations or with
light-like ones all on the ray `E = p`: 1,980 queries, 1,620 of them in
vocabulary. Parameters and states come from a fixed integer recurrence.
Solvers: **shipped**; **no filter**; **occam** (fewest parameters first, gate
within a tier); **first fit** (the first fitting family answers, a free
parameter guessed); **linear** (a general 2×2 matrix fitted from two
independent inputs, the review's "direct representation" baseline).

* **F1** shipped: 0 wrong on in-vocabulary families, every condition;
* **F2** at two timelike demonstrations, at least 95 % of in-vocabulary
  queries right;
* **F3** after at most two asks, at least 90 % of shipped in-vocabulary
  refusals right, 0 wrong;
* **F4** the light-like confound: on one-ray light-like demonstrations, 0
  queries of `boost`, `units`, `boost_units` answered; the first ask a massive
  state in every one; **0 light-like pool inputs separate the fitted boost from
  the fitted change of units**;
* **F5** `boost_chain3` at two or more timelike demonstrations right every
  time, with the fitted Doppler factor the product of the three;
* **F6** outside the vocabulary: 0 wrong at two or more demonstrations;
* **F7** the invariant filter changes no status or answer, and fewer fits are
  tried with it;
* **F8** the first-fit control gives at least one wrong in-vocabulary answer;
* **K** `κ = 190` lies in the register's `D0(Br2)` interval, every cell ratio
  over the anchor sweep is `(24+T)/27`, and the four refinement knobs order
  as Lean says;
* **L** both Lean files state their theorems with no `sorry`;
* **T** `tool frame` refuses one boost demonstration and names a massive
  state, answers two, and `tool kappa` answers.

## 5. Faculties

Under [`BLOCKERS_STUDY.md`](BLOCKERS_STUDY.md) §1: **derive** and **refuse**.
Every answer `tool frame` gives is computed from the example pairs. No register
holds it. Each wrong answer a control gives and the shipped gate does not is a
refusal, and its cost is counted. `tool kappa` derives its figures from the
SI constants and the registers. Nothing here is addressing.

## 6. The anchor κ: the owner's three questions

**How it works for calibration.** `κ` enters the chain once, as an energy per
mole: the tick is `τ = h N_A / κ`, the cell `(24+T)τ`, and the length
`c (24+T) τ`. Every dimensionful output is therefore proportional to `1/κ`
(`tick_scale_inv`), and every dimensionless output is free of it: the ratio of
two cells is `(24+T)/(24+T₀)` whatever `κ` is
(`cellLength_ratio_kappa_free`), and the measured sweep over 24 anchor and tax
pairs confirms it. Setting `κ = 1` gives the substrate's natural units in
exactly the sense that `c = 1` gives relativity's: it changes the units and
nothing that can be tested. In `tool frame` this is the `units` family: an
operator that multiplies every component by one scale, is identified from a
single example, multiplies the invariant by `s²`, and commutes with every
boost. The calibration dial is an operator that can be inferred, and it is
told apart from a change of frame exactly when a massive state, or light from
both directions, is seen (§7.3).

**Where it comes from, and how much more refined it could be.** The GLM's own
diatomic register holds `D0(Br2) = 951/5 = 190.2 kJ/mol ± 0.3`. `κ = 190` is
inside that interval (`kappa_within_br2_d0`), and Br₂ is the nearest of the
register's 52 species (the next, NaH, is 7.60 kJ/mol away). The element
register's homonuclear bond energy for bromine is 193 kJ/mol, the 298 K value.
A relative error in `κ` becomes a relative error of the same size in every
output (`tick_relative_change`). The four knobs that limit the chain's
precision, as relative shifts of every dimensionful output:

| knob | shift | proved by |
|---|---|---|
| third significant figure (`190 → 190.2`) | 0.105 % (`1/951`) | `kappa_tick_ratio_d0` |
| the register's uncertainty (half-width) | 0.158 % (`1/634`) | `kappa_relative_uncertainty_lt` |
| tick budget `24 + 8Q` rounded to `27` | 0.435 % | `tax_rounding_dominates_kappa` |
| which quantity: `D0` against the 298 K bond energy | 1.55 % (`3/193`) | `kappa_tick_ratio_bde`, `quantity_choice_dominates` |

So adding digits to `κ` is the least useful refinement. The useful ones, in
order, are (i) deciding which tabulated quantity the anchor names (`D0` at
0 K, or the 298 K bond enthalpy), which is fifteen times the digit effect; and
(ii) using the exact tick budget `24 + 8Q` instead of `27`. Both are decisions
about the definition, not measurements. Once they are made, the precision
floor is the register's ±0.3 kJ/mol.

**What use it has for the GLM.** Three uses, and one non-use:

1. **A declared unit.** `tool kappa` gives the conversions (work units, J,
   eV per particle `1.9692`, nm `629.6`). As the `units` family in `tool
   frame` it is an operator the GLM can infer and keep apart from a frame
   change.
2. **A guard.** A claim whose truth changes when `κ` changes is a claim about
   units. `cellLength_ratio_kappa_free` is the test: only the dimensionless
   part of a chain can carry a substrate claim.
3. **An anchor for a falsifiable prediction.** The only testable output of
   the chain is the dimensionless refractive-index law. `κ` does not enter it,
   so testing that law needs no better `κ`. It needs the independent material
   data the review lists (how TAX is computed from a material, which index,
   held-out materials).
4. **Not a predictor.** The archive's own Step 3 measured `r² = 0.0011`
   between its dimensionless geometric work and 24 bond energies, and a
   refitted scale did worse than predicting the mean. That figure is quoted
   from the archive README and was not re-measured here. No choice of `κ`
   rescues a measure that carries no signal.

## 7. What came out

### 7.1 Summary

Yes, within the declared families. The boost arithmetic held on every one of
78,161 exact checks, and 26 theorems in `RationalBoost.lean` prove it in
general. `tool frame` answered 703 of 1,620 in-vocabulary queries outright and
every one of the rest after a single asked example, with 0 wrong answers;
outside the vocabulary it refused all 360, but only after an evidence guard was
added between the first and second take. Light along one ray cannot tell a
frame from a unit change, so all 270 such queries were refused; light along
both rays can, which broke one declared mark (F4). κ is a unit: no
dimensionless output depends on it. It is the bromine dissociation energy to
within the register's ±0.3 kJ/mol, and its digits are the smallest of the four
precision knobs.

**17 of 18 marks** (E1–E7, F1, F2, F3, F5, F6, F7, F8, K, L, T met; F4 missed).

### 7.2 The two takes, and the evidence guard

**First take** (the mechanism as committed with the marks): in vocabulary 813
right, 0 wrong, 807 refused; **outside the vocabulary 1 right, 207 wrong, 152
refused**. F6 was missed, and so was F4 (§7.3): 16 of 18. The wrong answers all
had one cause. When every demonstration input lies on one line (all on the
light ray `E = p`, or two parallel timelike inputs), the two-parameter family
`rotation_units` (multiplication by a Gaussian rational) fits *any* operator
exactly: two equations, two unknowns. If nothing else fit, the gate answered
from a fit that had been solved for but never tested. All 180 `boost_then_rotate`
and `shear` queries on light-like data, plus 27 on timelike data (23 of them
at one demonstration), were answered that way.

**The revision.** A family counts as evidence only if it is *checked*: it has
fewer parameters than the independent equations the pairs give (two per
dimension of the span of the inputs). If every fitting family agrees but none
is checked, the status is `untested`, and the ask names an input off the line.
This is the GLM's version of the kit's rule that a fitted mask needs two
distinct demonstrations.

**Second take** (shipped): in vocabulary **703 right, 0 wrong, 917 refused**;
outside **0 right, 0 wrong, 360 refused**. The guard costs 110 in-vocabulary
answers. All of them were right: 90 `rotation_units` queries on light-like data
and 20 at one or two timelike demonstrations, where the truth happened to be
the untested family. All 110 come back after one ask. After at most two asks: **1,620 of 1,620 right, 0 wrong**, using
917 asks, exactly one per refusal. The guard was added after seeing the first
take's wrong answers, so F6's pass at the second take is a pass of a revised
mechanism, not a prediction.

### 7.3 F4: the confound is a one-ray effect, and the prediction was wrong

The first two parts of F4 held: of the 270 queries of `boost`, `units` and
`boost_units` on one-ray light-like demonstrations, **0 were answered**, and
the first ask was a massive state **in all 270**. The third part, that no
light-like input separates the fitted boost from the fitted unit change,
failed: **268** separations, every one on the *opposite* ray `(1, −1)`, and 0
on the same ray. The prediction confused the theorem with a broader claim.
`null_confound` is a statement about one ray. On the other ray the same boost
is the *reciprocal* rescaling (`null_confound_opposite`), so light from both
directions separates a frame change from a unit change (`null_rays_separate`,
proved after this take). The review's caution, "a single null example does
not constrain a general linear operator in the same way", is right. The
sharper statement: light-like data confounds frame and units **only when it all
lies on one ray**. A frame change shifts the two rays by reciprocal Doppler
factors; a change of units shifts both equally. The mark stays missed.

### 7.4 Study A

| check | failures / checks |
|---|---|
| E1 invariant | 0 / 15,379 |
| E2 inverse | 0 / 15,379 |
| E3 composition | 0 / 13,225 |
| E4 branch | 0 / 3,276 |
| E5 light-cone path = matrix path | 0 / 15,379 |
| E6 unit consistency (joules ↔ work units of `κ/N_A`) | 0 / 15,379 |
| E7 every rational boost is `B(b/(a+1))` | 0 / 144 |

78,161 checks, 0 failures. These are instances of theorems proved in §2. They
confirm that the Python arithmetic the tool runs agrees with the Lean
statement, which is the review's requirement `Dec(B̂(Enc q)) = B(u)q`, with
the light-cone layer as `Enc`/`Dec`.

### 7.5 The controls

| solver | in vocabulary: right / wrong / refused | outside: right / wrong / refused |
|---|---|---|
| shipped | 703 / 0 / 917 | 0 / 0 / 360 |
| shipped after ≤ 2 asks | 1,620 / 0 / 0 | 0 / 0 / 360 |
| first take (no evidence guard) | 813 / 0 / 807 | 1 / 207 / 152 |
| occam (fewest parameters first) | 920 / 3 / 697 | 0 / 0 / 360 |
| first fit | 1,244 / 376 / 0 | 1 / 245 / 114 |
| linear 2×2 | 530 / 0 / 1,090 | 114 / 0 / 246 |

* **F8:** the first-fit control's 376 wrong answers are what the gate
  prevents.
* **Occam** answers more but gives **3 wrong** (rotation truths at one or two
  timelike demonstrations, where a parameter-free family happened to fit;
  any vector can be rotated onto its own swap). Reading the families as a
  union is what makes F1 hold.
* **Linear** is never wrong, because every family here is linear, but it needs
  two independent inputs. It answers none of the 540 one-demonstration
  queries and none of the 810 one-ray light-like ones (the two sets overlap in 270). It names no family,
  and it cannot tell a boost from a unit change. On the two operators outside
  the vocabulary it answers 114 right, where the shipped gate refuses: a larger
  hypothesis space buys coverage at the price of saying nothing about
  structure. The structured tool's advantage is that it **names** the operator
  (`boost B(u) with u = 1/2, k = 3, β = 4/5`) and the invariant, and that one
  timelike example plus one ask suffices, not that it gets more right.
* **F7:** the invariant filter tried 7,907 fits against 15,840 without it
  (−50 %), with 0 changes of status or answer.
* **F5:** the `boost_chain3` family at two or more timelike demonstrations,
  60 of 60 right, the fitted Doppler factor equal to the product of the three
  in all 60 (`doppler_compose`). Longer compositions do not enlarge the
  hypothesis space.
* **F2:** at two timelike demonstrations, 261 of 270 right (96.7 %).

### 7.6 Exact arithmetic is not free

The bit length of the largest numerator or denominator of `B(1/2)ⁿ(2, 1)`, for
`n = 1 … 16`: 2, 4, 7, 11, 14, 17, 20, 23, 26, 30, 33, 36, 39, 42, 45, 49,
about 3 bits per boost. That is linear, as `doppler_compose` predicts: the
Doppler factor multiplies by `k = 3` each time, and the light-cone layer
carries it as one rational per ray. `int_boost_trivial` says the growth cannot
be avoided by moving to integers.

### 7.7 The tool, as used

```
tool frame 1,0 -> 5/3,-4/3 ? 3,1
  refused -- boost gives 11/3,-7/3; boost_units gives 11/3,-7/3;
  rotation_units gives 19/3,-7/3 ... to settle it, give the output for 2,1
  (a massive state: one fixes frame and units together)
tool frame 1,0 -> 5/3,-4/3 ; 2,1 -> 2,-1 ? 3,1
  11/3,-7/3 ... boost B(u) with u = 1/2 (Doppler factor k = 3, velocity ratio
  beta = 4/5) ... E^2-p^2 of the answer is 8 against 8 for the query
tool frame 1,1 -> 1/3,1/3 ; 2,2 -> 2/3,2/3 ? 3,1
  refused -- units gives 1,1/3; boost gives 11/3,-7/3 ... every demonstration
  input is light-like, so a change of frame and a change of units look alike
```

## 8. What carries over: the method for puzzles and other domains

The owner's guess was that the method would transfer to domains where things
get "worked out". Here is what transfers, stated so that each step corresponds
to something already in the GLM or a To-Do line:

| step | frame operators (this study) | 0/1 grids (`tool induce`) | other domains |
|---|---|---|---|
| classify by what is kept | `E² − p²`, `E² + p²`, a common ratio | Hamming weight (`wt_comp_perm`), the `4×` Leech layer | conserved quantities: charge, mass balance, a count, a sum |
| fit where the operator is diagonal | light-cone `(E+p, E−p)`, complex `E + ip` | cell permutations, a fitted mask | eigen-coordinates, log scale for products, the wheel's monomial exponents |
| answer only when tested and agreed | the gate plus the evidence guard | the gate plus "a mask needs two pairs" | the formula wheels' junction refusals |
| ask for the separating example | a massive state, or light from the other ray | `tool induce`'s `ask` | "what would you measure next" |
| say what is not seen at this layer | one ray confounds frame and units | weight-preserving rules look alike at the weight layer | an absence at one layer is not a refutation (Positioning) |

Two findings go beyond this domain:

* **The evidence guard is general.** Any family with as many parameters as the
  data have independent equations fits anything. A gate that counts only
  agreement will answer from such a fit. The kit's mask rule is one instance;
  the frame tool's `untested` status is another. The count to use is
  equations from the *span* of the inputs, not the number of examples.
* **"Which layer confounds what" is something to measure.** The confound of
  §7.3 is exact (`null_confound`), it lives on one ray, and the tool reports it
  in the refusal. This puts the Positioning section's "check from several
  layers before calling it absent" into practice.

## 9. What is not claimed

* Nothing here derives `c`, `κ`, or any physical constant. `κ` is a measured
  bond energy put in by hand. Its agreement with `D0(Br2)` is its provenance,
  not evidence of anything about the substrate.
* No map from the Leech lattice to Lorentzian spacetime is given, and
  `int_boost_trivial` is the reason none is attempted on an integer carrier.
* The TAX refractive-index proposal was not tested. It needs material data
  fixed independently of the indices, as the review says.
* The tool's families are a declared vocabulary. Its soundness
  (`GLM.PipelineInduction.solve_sound`) holds when the truth is among them.
  Outside them, the evidence guard and the gate refused every measured query
  at the second take, but the first take shows what happens without the guard.
* The marks were declared before measuring. The evidence guard was not: it
  was added after the first take's wrong answers.
