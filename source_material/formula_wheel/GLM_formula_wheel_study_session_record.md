# GLM Formula-Wheel Study Session Record

**Record date:** 24 September 2026  
**Scope:** Work beginning with the introduction of `glm_formula_wheel_study.py`, followed by its audit, the corrected formula study, Smith Chart work, RF refinements, delta–sigma audio investigation, and multidomain evidence aggregation.  
**Status:** Standalone studies completed and tested. Direct integration with the full `glm_universal` Golay–Leech substrate remains future work.

---

## 1. Executive Summary

The initial `glm_formula_wheel_study.py` attempted to verify, derive, discover, and analogize physical formulas using GLM. Review showed that it primarily checked dimensional signatures while reporting broader physical verification. It also modified package data during evaluation, defined seven rather than ten claimed wheels, used unsound string-pattern derivation, incorrectly scored some controls, and made unsupported claims about angle and GLM uniqueness.

A standalone correction, `glm_formula_wheel_study_v2.py`, was created. It separates parsing and grounding, dimensional homogeneity, exact monomial derivability from declared axioms, and preregistered physical status. It contains ten domains and 41 positive and negative cases. Both SI and explicit-angle policies achieved 41/41 expected dimensional outcomes, 41/41 derivability outcomes, and zero execution errors. These figures measure agreement with the preregistered protocol—not discovery or empirical verification of 41 physical laws.

The Smith Chart was then evaluated as a complementary system. It belongs after dimensional normalization rather than inside the formula wheel: `Z` and `Z0` must share dimensions, after which `z=Z/Z0` is a dimensionless complex quantity mapped by a Möbius transformation. `glm_smith_chart_study.py` passes 16/16 exact transformation and geometry checks. `glm_smith_chart_extensions.py` adds frequency traces, VNA CSV input, lossless-line rotation, VSWR/Q contours, matching-network search, local refinement, tolerance corners, plots, and ranking baselines.

For the deterministic synthetic RF example, 3,370 finite candidates were evaluated. The refined solution used a series 8.12184 pF capacitor and shunt 14.2802 nH inductor. Worst `|Gamma|` improved from 0.304865 to 0.246138 and worst VSWR from 1.87714 to 1.65301. Independent ±5% component corners raised worst `|Gamma|` to 0.269106 and VSWR to 1.73638. These are idealized simulation results, not a fabrication-ready network.

A separate delta–sigma audio study tested oversampling, noise shaping, limit cycles, deterministic TPDF dither, rational DC, finite-precision `sqrt(2)` incommensurate inputs, reconstruction, SNR, THD+N, and spectral error. All six preregistered checks passed. Coherent-tone SNR was approximately 42.89 dB for the first-order loop, 70.07 dB for the second-order loop, and 12.29 dB for the memoryless one-bit baseline. Rational DC produced a 16-sample cycle; dither broke that short period. The incommensurate case avoided the same short period but did not improve SNR. Thus an “irrational” stimulus is a stress condition, not a general accuracy mechanism.

The resulting architecture is a set of separate evidence producers joined through versioned evidence documents. Their scores are deliberately not pooled into one scientific-validity percentage.

---

## 2. Study Questions and Architecture

The session addressed:

1. What does `glm_formula_wheel_study.py` actually establish?
2. Can a scientifically defensible formula-wheel study be produced?
3. Does the Smith Chart provide a useful GLM representation?
4. Can Smith geometry support a practical RF workflow?
5. Can delta–sigma audio and incommensurate inputs add a useful capability?
6. How should heterogeneous modules cooperate without confusing their evidence?

The final architecture is:

```text
EquationClaim
  -> FormulaWheelEvidence

ImpedanceClaim + DimensionCheck(Z, Z0)
  -> dimensionless z = Z/Z0
  -> SmithChartEvidence
  -> RFMatchingEvidence

AudioStimulus + ModulatorDefinition
  -> DeltaSigmaAudioEvidence

All evidence documents
  -> GLM comparison/evaluation layer
```

Modules communicate through typed evidence, not through a universal `verified` flag.

---

## 3. Audit of `glm_formula_wheel_study.py`

### 3.1 Execution status

The original script passed syntax compilation. Full execution failed because `glm_universal` was not present in the supplied workspace:

```text
ModuleNotFoundError: No module named 'glm_universal'
```

Runtime claims about the full package could therefore not be validated. Findings about that script came from complete static inspection.

### 3.2 Principal defects

| Finding | Consequence |
|---|---|
| Dimensional homogeneity was reported as verification | Dimensionally valid but false or incomplete equations could pass |
| `ensure_physics_relations()` changed installed data before evaluation | The experiment was not read-only and became circular |
| Only `W1`, `W2`, `W4`, `W5`, `W7`, `W9`, and `W10` existed | Claimed ten-wheel coverage was false |
| 44 expressions were generated, not 12 per wheel | Report and implementation disagreed |
| Cross-substitution used string patterns | Valid Watt formulas could be missed and invalid formulas invented |
| Scalar and tensor relation tables were identical | Different semantic types were collapsed |
| Broad `except Exception` converted defects into negative results | Parser, name, and execution errors could be hidden |
| Kirchhoff scoring counted only `True` | Correct negative controls were treated as failures |
| Analogy/discovery counted any answer as success | No gold target, abstention rule, or correctness criterion existed |
| `round(float(x))` occurred on an allegedly exact path | The exact-arithmetic invariant was violated |
| W2 AC power omitted phase/conjugation distinctions | Real, reactive, apparent, and complex power were conflated |
| “GLM corrected a textbook error” cited no textbook | The code supplied the wrong equation itself |
| “No LLM can do this” and “unique to GLM” lacked evidence | Conclusions exceeded the experiment |

Examples the original derivation could construct included:

```text
power = torque^2 / angular_acceleration
acoustic_intensity = acoustic_pressure^2 / particle_velocity
```

Neither follows from the declared physical axioms.

### 3.3 Angle conclusion

The independent `A` axis is a GLM modelling convention. Current SI treats plane angle as a quantity with the unit one while encouraging explicit units when useful. Moreover, `torque = moment_of_inertia * angular_velocity` already fails through time: torque contains `T^-2`, whereas `moment_of_inertia * angular_velocity` contains `T^-1`. A separate angle axis is unnecessary for that rejection.

Defensible conclusion:

> An explicit angle axis can expose some angle-related modelling ambiguities, but rejection of `τ = Iω` is not unique to that axis, and dimensional inconsistency alone does not identify or correct a real textbook source.

---

## 4. Corrected Formula-Wheel Study

### 4.1 Implementation

`glm_formula_wheel_study_v2.py` was created as a read-only reference using the Python standard library and exact `Fraction` arithmetic. It provides:

- ten declared domains, `W1`–`W10`;
- 41 preregistered cases;
- restricted AST parsing;
- exact dimension vectors;
- coefficient-aware monomial relations;
- rational row-span derivability from declared axioms;
- typed results;
- SI and experimental explicit-angle policies;
- assumptions, sources, notes, and protocol hash;
- strict mode, self-tests, and JSON export;
- no package-data mutation.

Outcome vocabulary includes:

```text
dimensionally_consistent
dimensionally_inconsistent
algebraically_derived
not_algebraically_derived
physically_supported
physically_underspecified
model_convention
negative_control
unresolved
execution_error
```

`physically_supported` is curated metadata under explicit assumptions and a source. It is not inferred from dimensions alone.

### 4.2 Domains

| ID | Domain |
|---|---|
| W1 | DC Ohm and power |
| W2 | Sinusoidal AC impedance and power |
| W3 | Electrostatics and capacitors |
| W4 | Rotational mechanics |
| W5 | Linear dynamics and work-energy |
| W6 | Fluid statics and flow |
| W7 | Linear plane-wave acoustics |
| W8 | Thermal physics and heat transfer |
| W9 | Wave kinematics |
| W10 | Photon energy and momentum |

### 4.3 Results

| Policy | Dimensional expectations | Derivability expectations | Execution errors |
|---|---:|---:|---:|
| SI angle convention | 41/41 | 41/41 | 0 |
| Explicit `A` convention | 41/41 | 41/41 | 0 |

Policy-dependent expectations were explicit. For example, `angular_velocity = frequency` is dimensionally compatible under SI but incompatible under an independent `A` convention; neither dimensional result supplies the numerical factor in `omega = 2*pi*f`.

### 4.4 Interpretation limit

The 41/41 scores mean that implementation outputs matched preregistered expectations. They do not mean the full GLM substrate was benchmarked, that 41 laws were empirically verified, or that tensor contractions, phase, causality, and uncertainty were solved.

---

## 5. Supplied `glm_formula_wheel_study_v2.1.py`

The later supplied file was a mixed development draft rather than an executable study:

```text
SyntaxError at line 1535: ====
```

It contained pasted separators, duplicate cases, duplicate scorecards, and code appended after a completed `main()` block. It also described `Sense` subtraction as algebraic derivation. Signature equality can establish dimensional/type compatibility, but cannot prove that a target follows from declared axioms.

The file was preserved unchanged as an historical artifact.

---

## 6. Smith Chart Capability

### 6.1 Placement in the system

The Smith Chart complements GLM after dimensional grounding:

```text
z = Z_load / Z0
Gamma = (z - 1) / (z + 1)
z = (1 + Gamma) / (1 - Gamma)
```

`EXT10` can establish that `Z/Z0` is dimensionless. The Smith module then preserves resistance, reactance, phase, passivity, and transmission-line geometry—information that dimensional vectors alone discard.

### 6.2 Exact core study

`glm_smith_chart_study.py` implements rational-complex arithmetic and tests:

- matched and short-circuit points;
- normalized real and complex impedance transforms;
- inverse transforms;
- impedance/admittance duality;
- passive/active unit-circle behaviour;
- reflected power;
- constant-resistance and constant-reactance circles;
- exact `z -> Gamma -> z` round trips.

| Measure | Result |
|---|---:|
| Expected outcomes | 16/16 |
| Execution errors | 0 |

This validates the transformations and invariants, not a Golay–Leech advantage.

---

## 7. RF/Smith Chart Extensions

### 7.1 Features

`glm_smith_chart_extensions.py` adds:

1. frequency-indexed `S11` traces;
2. CSV ingestion for real/imaginary `S11`, magnitude/phase, dB/phase, or `R+jX`;
3. deterministic series-RLC demonstration data;
4. lossless reference-plane rotation;
5. impedance, VSWR, and load-Q contours;
6. series-reactance and shunt-susceptance operations;
7. physically frequency-scaled `L` and `C` candidates;
8. bypass, one-element, and two-element candidates;
9. coarse-grid and local coarse-to-fine search;
10. independent component-tolerance corners;
11. raw-impedance, Smith, physical-objective, and optional external GLM rankings;
12. PNG, JSON, and CSV export.

A bypass candidate ensures that an unsuitable search grid cannot force a network worse than no network.

### 7.2 Default synthetic protocol

| Parameter | Value |
|---|---:|
| Model | Ideal deterministic series RLC |
| Frequency range | 0.8–1.2 GHz |
| Points | 101 |
| Reference impedance | 50 ohm |
| Line length | 0 m |
| Velocity factor | 1 |
| Objective | Minimize worst `|Gamma|` |
| Coarse grid | 41 × 41 per topology |
| Refinement passes | 3 |
| Finite candidates | 3,370 |
| Tolerance | Independent ±5% corners |

### 7.3 Result

Selected candidate:

```text
Candidate: REF-00064
Topology: series_then_shunt
Series C: 8.1218416795 pF
Shunt L: 14.2801611948 nH
```

| Quantity | Before | After |
|---|---:|---:|
| Mean `|Gamma|` | 0.265443 | 0.166741 |
| Worst `|Gamma|` | 0.304865 | 0.246138 |
| Worst VSWR | 1.87714 | 1.65301 |
| Mean reflected-power fraction | 0.070666 | 0.029583 |

| Tolerance measure | Value |
|---|---:|
| Nominal worst `|Gamma|` | 0.246138 |
| ±5% corner worst `|Gamma|` | 0.269106 |
| ±5% corner worst VSWR | 1.73638 |
| Worst series scale | 0.95 |
| Worst shunt scale | 1.05 |

### 7.4 Ranking baselines

| Method | Candidate | Worst `|Gamma|` | Regret | Spearman rho |
|---|---|---:|---:|---:|
| Raw normalized-impedance distance | `LNET-00927` | 0.318772 | 0.072634 | 0.3396 |
| Smith mean-reflection distance | `LNET-00755` | 0.273502 | 0.027364 | 0.9687 |
| Physical worst-reflection objective | `REF-00064` | 0.246138 | 0 | 1.0000 |

No external GLM ranking was supplied, so no Golay–Leech advantage was inferred. The candidate CSV permits a future blind test using `candidate_id,glm_score` over the same candidate set.

### 7.5 Limitations

The RF model uses ideal lumped components and a lossless line. It does not yet include component Q/ESR, self-resonance, layout parasitics, de-embedding uncertainty, transmission loss/dispersion, statistical Monte Carlo tolerances, stability, thermal limits, power handling, or measured post-build validation.

---

## 8. Delta–Sigma Audio Study

### 8.1 Scientific rationale

Delta–sigma modulation supplies a separate sampled nonlinear feedback capability. The proposed “irrational” idea was constrained carefully:

- rational low-level inputs can generate short periodic bitstreams;
- finite-precision `sqrt(2)` cases are incommensurate stress inputs, not exact general irrationals;
- avoiding a short period does not imply reduced noise;
- dither is the controlled cycle-breaking intervention and carries a noise cost.

### 8.2 Protocol

| Parameter | Value |
|---|---:|
| Audio rate | 48 kHz |
| Oversampling ratio | 64 |
| Modulator rate | 3.072 MHz |
| Duration | 0.2 s |
| Analysis band | 20 Hz–20 kHz |
| Dither | Deterministic PCG64 TPDF |
| Reconstruction | Polyphase low-pass decimation |
| Tone analysis | Arbitrary-frequency least-squares fitting |

Arbitrary-frequency fitting prevents FFT-bin leakage from unfairly penalizing the incommensurate tone.

### 8.3 Results

| Case | SNR (dB) | THD+N (dB) | Period | In-band error (dBFS) |
|---|---:|---:|---:|---:|
| `DS-DC-RATIONAL` | — | — | 16 | -336.44 |
| `DS-DC-INCOMM` | — | — | None | -72.55 |
| `DS-DC-DITHER` | — | — | None | -59.58 |
| `DS-TONE-COHERENT-1` | 42.89 | -42.84 | 3,072 | -56.47 |
| `DS-TONE-INCOMM-1` | 42.61 | -42.47 | None | -56.43 |
| `DS-TONE-COHERENT-2` | 70.07 | -70.07 | None | -84.36 |
| `DS-TONE-INCOMM-2` | 69.41 | -69.41 | None | -84.04 |
| `DS-TONE-DITHER-2` | 69.59 | -69.59 | None | -84.16 |
| `BASE-1BIT` | 12.29 | -6.77 | None | -2.25 |

### 8.4 Preregistered checks

| Check | Result |
|---|---|
| Rational DC produces a short period | Pass |
| TPDF dither breaks that detected period | Pass |
| Incommensurate DC avoids the same short period | Pass |
| Second-order improves coherent-tone SNR over first order | Pass |
| Noise shaping beats the memoryless one-bit baseline | Pass |
| All tested states remain bounded | Pass |

Total: 6/6.

### 8.5 Interpretation

For these explicit simulations, the primary accuracy gain came from second-order noise shaping. The incommensurate input changed periodicity but not SNR materially. Dither broke periodicity with added noise. The study does not represent all delta–sigma architectures and omits analog noise, clock jitter, DAC mismatch, hardware nonlinearities, and physical reconstruction circuitry.

---

## 9. Combined Evidence Architecture

`glm_formula_wheel_suite.py` combines the formula and exact Smith studies. `glm_multidomain_evidence_suite.py` aggregates formula, Smith, and delta–sigma evidence while retaining separate scores.

| Capability | Result |
|---|---:|
| Formula dimensional outcomes | 41/41 |
| Formula derivability outcomes | 41/41 |
| Smith Chart outcomes | 16/16 |
| Delta–sigma checks | 6/6 |

A recommended evidence envelope contains:

```text
claim_id
capability
input_hash
protocol_hash
outcome_type
observations
expected_outcome
assumptions
provenance
uncertainty_or_limitations
execution_status
```

---

## 10. Files and Status

| File | Role | State |
|---|---|---|
| `glm_formula_wheel_study.py` | Original study | Reviewed; unchanged; requires absent `glm_universal` |
| `glm_formula_wheel_study_v2.py` | Corrected formula protocol | Executable and validated |
| `glm_formula_wheel_study_v2.1.py` | Mixed user draft | Preserved; syntax-invalid |
| `glm_formula_wheel_results.json` | Formula evidence | Validated |
| `glm_smith_chart_study.py` | Exact Smith capability | Executable and validated |
| `glm_smith_chart_results.json` | Smith evidence | Validated |
| `glm_formula_wheel_suite.py` | Formula/Smith runner | Executable and validated |
| `glm_formula_wheel_suite_results.json` | Formula/Smith evidence | Validated |
| `glm_smith_chart_extensions.py` | RF workflow | Executable and validated |
| `glm_smith_extensions.png` | RF plot | Generated and inspected |
| `glm_smith_extensions_results.json` | RF evidence | Validated |
| `glm_smith_matching_candidates.csv` | RF candidate table | 3,370 latest rows |
| `glm_delta_sigma_audio_study.py` | Audio study | Executable and validated |
| `glm_delta_sigma_audio.png` | Audio spectra/waveform | Generated and inspected |
| `glm_delta_sigma_audio_results.json` | Audio evidence | Validated |
| `glm_delta_sigma_audio_results.csv` | Audio table | 9 cases |
| `glm_multidomain_evidence_suite.py` | Multidomain aggregator | Executable and validated |
| `glm_multidomain_evidence_results.json` | Aggregated evidence | Validated |

---

## 11. Reproducibility and Integrity

### 11.1 Protocol hashes

| Evidence | Schema | Protocol hash |
|---|---|---|
| Formula | `glm.formula-wheel-study.v2` | `eb51121248cb63d1b8c8b083370e0f2b3385e34f9796204bc829e1a0d860afc1` |
| Smith core | `glm.smith-chart-study.v1` | `15f6b21280de4e8d1e2f4ded196c74f027456cbc4caf6a78dfb0b1f34b74165b` |
| Formula/Smith suite | `glm.formula-wheel-suite.v1` | `4d1a67a06ae87bbd08c7275aedf3f44ca852d89d6aece711640067e5de3f6de4` |
| Smith extensions | `glm.smith-chart-extensions.v1` | `6bfc88efa6cae0a347687ee64796d47c0aa21673f01fc3664ec33463b9e3057e` |
| Delta–sigma | `glm.delta-sigma-audio-study.v1` | `5efba468227de6b334992671edf7bf941317e4ce6933f5405a747ab77ca0b489` |
| Multidomain suite | `glm.multidomain-engineering-evidence.v1` | `cf3a900f0afb62a6c18e1ccb0fa52327f288fb69cd5afd7b4016b075670ca59f` |

### 11.2 Script SHA-256 snapshots

| File | SHA-256 |
|---|---|
| `glm_formula_wheel_study.py` | `f1e14b0ea6f02f42ed929fa926e49b9a6ac79f6f99a8684b3d4ec3f81bb5fddb` |
| `glm_formula_wheel_study_v2.py` | `c6dfbd098f29163afeecd0ea6f0abc7bb5e1dc92ed3698bd75be37ce37e5d201` |
| `glm_formula_wheel_study_v2.1.py` | `88be1b770d8f3faae2ff2189677e51e959d7769699d14791ab9914ab2a8400ca` |
| `glm_smith_chart_study.py` | `a7a301073e3081d0e27a73bd062c2a96942cae40db6e82b44d926c08b3cb0a79` |
| `glm_formula_wheel_suite.py` | `b842f5c30e56eb36e533fce1b3a662cb40448dd3b32ece4e7dadeaa7c3478233` |
| `glm_smith_chart_extensions.py` | `04ed4455f33e5a1cad96db2a63453eb28412cec0f8219e8395f948ef4b408733` |
| `glm_delta_sigma_audio_study.py` | `69b08537b81450f437e7ebed6b7cc54b6dfb17255ae9c645f560b4df2ad4afb4` |
| `glm_multidomain_evidence_suite.py` | `0a65f4d8fa8b165865246156d6be2c013b6217b84bf6d7b1ef1dfebe5552714f` |

Hashes are snapshots and change after file edits.

### 11.3 Commands

```bash
python glm_formula_wheel_study_v2.py --self-test
python glm_formula_wheel_study_v2.py --strict
python glm_formula_wheel_study_v2.py --angle-policy explicit --strict
python glm_smith_chart_study.py --self-test
python glm_smith_chart_study.py --strict
python glm_smith_chart_extensions.py --self-test
python glm_smith_chart_extensions.py --strict
python glm_delta_sigma_audio_study.py --self-test
python glm_delta_sigma_audio_study.py --strict
python glm_multidomain_evidence_suite.py --strict
```

---

## 12. Claim Boundaries

Supported:

- the reference formula implementation matches 41 preregistered dimensional and derivability expectations under each policy;
- the Smith core satisfies 16 preregistered transformations and invariants;
- the RF optimizer improves the stated synthetic objective under its ideal model and reports ±5% corner sensitivity;
- the implemented second-order delta–sigma loop outperforms the implemented first-order and memoryless baselines;
- rational, incommensurate, and dithered cases differ in detected periodicity.

Not established:

- that full GLM outperforms conventional dimensional analysis;
- that Golay–Leech encoding improves RF matching or audio conversion;
- that dimensional homogeneity proves physical truth;
- that signature mismatch proves equations involving unmodelled tensor contractions false;
- that irrational numbers generally improve accuracy;
- that the RF network is fabrication-ready;
- that simulated delta–sigma results predict a particular device;
- that non-GLM systems cannot perform these calculations.

---

## 13. Recommended Next Work

### Priority 1: integrate the real GLM substrate

Run identical held-out cases through:

1. the exact standalone reference;
2. raw `EXT10`;
3. `EXT10` plus rank/P/T/C;
4. full Golay–Leech representation;
5. conventional symbolic/numerical baselines.

Use identical labels, splits, abstention rules, and metrics. The adapter must be read-only.

### Priority 2: measured RF validation

Use calibrated VNA `S11(f)` data and add de-embedding, uncertainty, component Q/ESR, self-resonance, layout parasitics, standard values, Monte Carlo tolerances, held-out frequencies, and post-build measurements. Let GLM rank the complete candidate table blindly and measure regret.

### Priority 3: stronger delta–sigma protocol

Add amplitude/DC sweeps, multiple OSRs and orders, several deterministic seeds with intervals, explicit NTF/STF measurement, intermodulation, multitone tests, overload recovery, state bounds, and trusted-toolbox or hardware comparisons.

### Priority 4: stable evidence schema

Add JSON Schema validation, semantic versioning, immutable input hashes, code/data revisions, uncertainty fields, environment metadata, and strict separation of observations, expectations, interpretations, and claims.

### Priority 5: explicit physical operators

Introduce typed dot products, cross products, tensor contractions, conjugation, real/imaginary projections, complex magnitude/phase, and frame/orientation assumptions. Ordinary multiplication must not stand for every physical operator.

---

## 14. Sources Consulted

| Material | Identifier/URL | Use and access |
|---|---|---|
| Supplied `glm_formula_wheel_study.py` | Complete workspace file | Primary audit object |
| Supplied `glm_formula_wheel_study_v2.1.py` | Complete workspace file | Structural review and compilation test |
| BIPM, *The International System of Units (SI)*, 9th edition | DOI 10.59161/AUEZ1291; https://www.bipm.org/documents/20126/41483022/SI-Brochure-9-EN.pdf | Full-text extraction; angle/unit-one interpretation |
| BIPM, “The BIPM has published a new version of the SI Brochure” | https://www.bipm.org/en/-/2024-09-11-si-brochure-301 | 2024 angle clarification |
| ScienceDirect Topics, “Smith Chart” | https://www.sciencedirect.com/topics/engineering/smith-chart | User-named source; direct retrieval returned HTTP 403 |
| CERN/JUAS, “RF Engineering Introduction to the Smith Chart” | https://indico.cern.ch/event/1088623/contributions/4632092/attachments/2391935/4095965/RFeng22_SmithChart_withQuiz.pdf | Search metadata; PDF extraction failed |
| Rohde & Schwarz, “Understanding the Smith chart” | https://www.rohde-schwarz.com/us/products/test-and-measurement/essentials-test-equipment/spectrum-analyzers/understanding-the-smith-chart_257989.html | Normalized one-port interpretation |
| Microwaves101, “Smith Chart Basics” | https://www.microwaves101.com/encyclopedias/smith-chart-basics | Extracted page; normalization, admittance, rotation, and matching |
| Analog Devices, “Sigma-Delta ADCs Tutorial” | https://www.analog.com/en/resources/technical-articles/sigmadelta-adcs-tutorial.html | Search metadata; direct fetch timed out |
| Analog Devices, “MT-022: ADC Architectures III, Sigma-Delta ADC Basics” | https://www.analog.com/mt-022 | Oversampling and noise-shaping context |
| Analog Devices, “MT-023: ADC Architectures IV” | https://www.analog.com/mt-023 | Idle tones and advanced concepts |
| Perez Gonzalez and Reiss, “Idle Tone Behavior in Sigma Delta Modulation” | AES Convention Paper 7108 | Bibliographic/search metadata |
| Reiss, “Understanding sigma delta modulation: the solved and unsolved issues” | *Journal of the Audio Engineering Society* 56, 49–64 (2008) | Bibliographic/search metadata |
| “A New Type of Wireless Transmission Based on Digital Direct Modulation for Use in Partially Implantable Hearing Aids.” | PMID 33923716; DOI 10.3390/s21082809 | PubMed abstract |
| “A 90.9 dB SNDR 95.3 dB DR Audio Delta-Sigma Modulator with FIA-Assisted OTA.” | PMID 38474986; DOI 10.3390/s24051449 | PubMed abstract |

Web material was retrieved on 24 September 2026. Access limitations are stated rather than presenting snippets as full-text review.

---

## 15. Final Position

The formula-wheel concept is valuable as typed dimensional grounding plus exact derivability from explicit axioms. The Smith Chart supplies the appropriate complex-domain representation for normalized RF immittance. Delta–sigma supplies a sampled nonlinear feedback domain for periodicity, noise shaping, dither, and multiscale spectral evidence.

GLM’s opportunity is to coordinate these capabilities while preserving each domain’s semantics, assumptions, uncertainty, and baselines. A credible Golay–Leech contribution must be demonstrated through blinded held-out comparisons against raw `EXT10`, conventional complex-plane, symbolic, and signal-processing methods—not inferred merely from assembling the modules.
