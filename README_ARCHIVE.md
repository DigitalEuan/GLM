# GLM overlay — archive

The archival half of [`README.md`](README.md): the change log, and the
write-up of each round as it was finished.

<!-- figures:history -->

*Everything in this file is an archive.  The counts in it were true when
the row was written and are deliberately left alone — for the package as it
is now, see [`README.md`](README.md) and [`FIGURES.md`](FIGURES.md), which is
regenerated from the code.*


## Change Log (Repository-Level)

| Version | Date | Change |
|---------|------|--------|
| 2.4 | 2026-08-06 | Initial structure with arc_agi_15/16 |
| 2.5 | 2026-08-07 | Added arc_agi_17 (substrate-native cognitive architecture). Updated: data flow, constants (Lean fix, TAX conservation, UBP scale, 2Δv), metrics (geometric work, hexcolour, 2Δv), driving styles (lattice perception, deliberative, imagination), ARC-AGI results. Marked integrated glm_machine modules. Added v37 features note. |
| 2.6 | 2026-08-10 | Added next_steps_from_7Aug26.md. Minor restructuring notes. |
| 2.7 | 2026-08-20 | Full repository catalog (CATALOG.md). Added glm_lean/ to tree and folder table. Updated ARC-AGI stats to v35 final (105/181, 217 runs, 4,015 edges, 66 hexcolour, 197 simplicial faces, 11 puzzle types). Verified all README cross-references. Fixed missing folder references. |
| 2.8 | 2026-08-21 | GLM 3+ (see below) - pulling the variosu parts of the GLM system into one clean operational directory 'glm_universal'
| 2.9 | 2026-08-21 | `glm_universal` operational hardening. Built the missing `GLM.py` CLI at the repo root (was 26 failing runtime tests, now zero failures). Added `glm_universal/data_objects/semantic_lexicon.py` with meaning-based encoding (10 semantic primitives + relations + has_physical_dim flag), 40 curated sample concepts, and a 39-test suite — replaces the legacy index-based lexicon as the register the runtime loads. Augmented the physics register from 660 → 701 concepts (+41) across nine previously-thin domains (acoustics +6, photometry +6, radiometry +6, base +4, geophysics +6, information +5, statistical mechanics +3, astronomy +3, signals and control +2). All 701 pass PhysicsCodec.check(). Total test count: 521 passed, 5577 subtests, zero regressions. See "GLM-3+ v0.5.0 — semantic lexicon + physics expansion" section near the bottom of this README. |
| 3.0 | 2026-08-21 | `glm_universal` dataset audit + growth. Ran dimensional audits on the physics register (found 4 real EXT10 exponent bugs and 1 ambiguous unit string — fixed; 7 remaining "mismatches" are the EXT10 design intent for solid angle, not bugs). Ran a lexicon audit (found 6 groups of concepts with identical primitive vectors — fixed all, zero collisions now). Redesigned the semantic lexicon with 1/8 gradations and explicit per-concept primitive values, growing the sample from 40 → 95 concepts across 11 topics. Added 19 more physics concepts (701 → 720, all unique names). Added two new analogy subspaces (`lexicon.primitives`, `lexicon.relations`) so cross-lexicon analogies resolve on meaning rather than spelling. Test count: 533 passed, 5854 subtests, zero regressions. See "GLM-3+ v0.5.1 — dataset audit + growth" section near the bottom of this README. |
| 3.1 | 2026-08-21 | `glm_universal` directive alignment + substantive tests. Reviewed `ubp_universal_1.txt` directive against the operational system. Found and fixed a regression introduced by v0.5.0/v0.5.1: 62 of 118 element symbols (`Li`, `Na`, `Be`, etc.) were colliding with physics symbol aliases, so `Li : Na :: Be : ?` resolved to `acoustic_intensity_level : avogadro_constant :: bejan_number : avogadro_number` instead of `Mg`. Fix: `_aliases_for()` in `runtime/parser.py` now suppresses short physics symbols that collide with element symbols (118-element table hard-coded). Also fixed `slow`'s `active_stative` primitive (was 1/8, should be 3/4) so `hot : cold :: fast : ?` now correctly resolves to `slow` (was `react`). Added 23 substantive end-to-end tests in `test_substantive.py` that check actual query answers, not just "the system returns a result". Test count: 556 passed, 5854 subtests, zero regressions. See "GLM-3+ v0.5.2 — directive alignment + substantive tests" section near the bottom of this README. |
| 3.2 | 2026-08-21 | `glm_universal` wiring of created-but-unused mechanisms. Surveyed the package and found four major reasoning modules that were implemented but never reached from any runtime query: `dimension_layers.escalate`, `product.griess_trilinear`, `coherence.nrci_breakdown`, and `analogy.nearest_lattice_point`. Wired all four as three new runtime query kinds (`project A B`, `trilinear A B C`, `coherence <concept>`) plus an augmentation to `describe` (now reports the lattice projection). Added 23 substantive tests (`test_wiring.py`) verifying each new query kind returns a useful answer. Inserted the directive's "layered projection" text near the top of this README. Test count: 579 passed, 5854 subtests, zero regressions. See "GLM-3+ v0.5.3 — wiring of created-but-unused mechanisms" section near the bottom of this README. |
| 4.0 | 2026-08-21 | `glm_universal` directive-mentioned mechanisms implemented. Wired the remaining lower-priority unwired functions (verifier_report, pair_census, theta_series, two_a_closure_report, signed_cosine_squared) as two new query kinds (`report <subject>`, `angle A B`). Implemented all five directive-mentioned mechanisms that had no code at all: Moonshine layer (graded dimensions V_0..V_10 + the j-function q-series + Leech-to-Moonshine bridge), Niemeier lattices (23 ADE root systems + deep-hole types), LLVQ (Leech Lattice Vector Quantization — codebook-free angular search over Leech shells), FWHT (Fast Walsh-Hadamard Transform — O(N log N) with exact arithmetic), Valorani's log-space SVD (Buckingham-Pi via rational nullspace, float-free). Added 31 substantive tests (`test_directive.py`). Test count: 610 passed, 5877 subtests, zero regressions. See "GLM-3+ v0.6.0 — directive-mentioned mechanisms implemented" section near the bottom of this README. |
| 4.1 | 2026-08-22 | `glm_universal` completion + the information-loss-at-boundaries study. Restored the missing `GLM.py` CLI (the shipped `glm_universal_v0.6.zip` did not contain it, so 30 CLI tests errored on import; the full 610-test suite now passes). Added `glm_universal/reasoning/information_loss.py` — the layered-projection thesis made measurable: indistinguishability, resolution, loss count, boundaries, refinement violations, congruence witnesses, capacity. Wired it as the `report information loss` subject with a verifying column-3 template. Added 42 tests (`test_information_loss.py`); test count 610 → **652 passed, 5877 subtests, zero regressions**. Audit finding: the substrate → integer step is **not** a refinement on real carriers (`refinement_chain_intact = False`). Added a machine-checked Lean 4 development in `RequestProject/GLM/` (`Constants`, `TaxConservation`, `Layers`, `Stack`, `GolayBoundary`) and the write-up `INFORMATION_LOSS_STUDY.md`. See "GLM-3+ v0.7.0" section at the bottom of this README. |
| 4.2 | 2026-08-22 | `glm_universal` completed to **v1.0.0**, and the README chain through every folder brought up to date. Implemented the reserved `glm_universal/benchmarks/` package: 5 suites, 2,390 scored tasks, every suite above its published baseline (overall 2,380/2,390), with 8 findings — including the negative ones — reported beside the scores; wired as `report benchmarks`. Added the public `GeometricSession.solve(query)` so an already-parsed query can be edited and re-run. Wired Valorani's Buckingham-Pi as the `pi_groups` query kind (the dimensionless groups of a set of quantities, from the exact rational nullspace of their EXT10 exponent matrix). Bumped `glm_universal.__version__` to 1.0.0 and exported the `migration` and `benchmarks` sub-packages from the package root. Test count 1,033 → **1,041 passed, 6,099 subtests, zero failures**. Corrected the v4.1 audit finding: the substrate → integer step **is** now a refinement (`refinement_chain_intact = True`), repaired by making the integer layer cumulative — see the correction appended to that section, and "GLM-3+ v1.0.0" at the bottom of this README. |
| 4.3 | 2026-08-22 | `glm_universal` **v1.1.0** — `semantics/`, and the version bump and README chain completed to match it. Added the seventh sub-package: the meaning space (a 24-coordinate carrier of *what a term denotes*, with an exact round trip, injectivity and a refusal at capacity), reference resolution (1,705 notations resolve; ambiguous terms are refused rather than decided by resolver order), relations derived from meanings, and the grounded graph — 357 meanings, 6,210 binary and 6,649 ternary edges, every one re-derived on demand. Audited the inherited ARC-era concept graph rather than describing it: **83 of its 4,282 concepts denote anything determinate, and 2 of its 4,015 edges state a re-derivable relation**; its `sha256`-of-a-spelling carriers put related pairs at mean Hamming 4547/376 ≈ 12.09 and unrelated pairs at 12077/1009 ≈ 11.97, either side of the 12 that two random 24-bit words average. Wired as the `meaning` query kind and the `report semantics` subject, both with verifying column-3 templates. Bumped `glm_universal.__version__` to 1.1.0, exported `semantics` from the package root, and pinned both in `test_wiring.py::TestPackageSurface` so the declared surface cannot drift from the code. Added the Lean files `RequestProject/GLM/Semantics/Meaning.lean` and `Grounding.lean` (11 → 13, still no `sorry`). Fixed two example scripts that resolved their data path from the wrong directory and one that formatted a `Fraction` with a float format spec; all six examples now run. Test count 1,041 → **1,094 passed, 6,331 subtests, zero failures**. See "GLM-3+ v1.1.0" at the bottom of this README. |
| 4.4 | 2026-08-23 | `glm_universal` **v1.2.0** — infinite values, irrational numbers, and a map of where the machine stops. Added `reasoning/exact_real.py`: a real held as a *process* (`x.at(k)` returns an exact `Fraction` within `2**-k`, for any `k`), roots of any degree, `pi`, `e` and `phi`, the dyadic tower of stand-ins and the level that exposes each, decided inequality and refused equality, and the delta-sigma modulator whose time average after `N` ticks is within `1/N` of any target — so a finite carrier that moves reaches every real. In 24 coordinates the modulator quantises to Golay codewords, which bounds it: the reachable set is the convex hull of the code, the all-½ target is held with deviation **0**, and the ramp target `i/24` is outside the hull with a separating functional verified against all 4,096 codewords (gap **13/5760**) proving no quantiser converges to it. Added `reasoning/real_expr.py`, written arithmetic over those processes (`(1+sqrt(5))/2`, `sqrt(2)+sqrt(3)`, `pi/4`, `root(3, 2)`; `0.1+0.2` is exactly `3/10`), with division refusing a divisor that has not moved away from zero by `2**-96` and naming the depth. Two new query kinds, `approximate <expr> to <n> places` and the comparison family, plus the `report infinite values` subject. Added the eighth sub-package `capabilities/`: 33 probes, each a question a user would ask, each answered by running the real code — **18 hold, 15 break, 0 errored, 0 surprises**, twelve of the breaks being theorems — wired as `report capabilities`. Bumped `glm_universal.__version__` to 1.2.0 and pinned the eight sub-packages in `test_wiring.py::TestPackageSurface`. Added the Lean files `DeltaSigma.lean`, `Irrational.lean`, `Reachable.lean` and `Computable.lean` (13 → 17, still no `sorry`). Test count 1,094 → **1,241 passed, 6,331 subtests, zero failures**. The write-up is `INFINITE_VALUES_STUDY.md`; see "GLM-3+ v1.2.0" at the bottom of this README. |
| 4.5 | 2026-08-24 | `glm_universal` v1.2.0, **extended**: the value grammar past the algebraic operations. Added `reasoning/transcendental.py` — `exp`, `log` (natural, or `log(base, x)`), `sin`, `cos`, `tan` and a non-integer exponent `x^y`, each a process with a stated error budget, all in exact rational arithmetic with **no float constructed anywhere**. `exp(1) = 2.71828182845904523536` agrees with `e` to `2**-78`, `sin^2 + cos^2 = 1` and `exp(log(7/2)) = 7/2` to `2**-55`, `2^(1/3)` equals `root(3, 2)`, and `log(2, 8)` is `3`. The two places the layer now stops are of different kinds and both are stated: `log` needs a **positivity witness** `x >= 2**-m` for exactly the reason `1/x` needs a nonzero one — `log(2)` goes through, `log(sqrt(2)-sqrt(2))` is refused with its depth named, and `x^y` inherits the refusal, so `2^pi` is computable and `0^pi` is not — while the inverse and hyperbolic family (`asin`, `acos`, `atan`, `sinh`, `cosh`, `tanh`, `erf`, `gamma`, `zeta`) is refused by an explicit list, `real_expr.UNBUILT_FUNCTIONS`, so the message names the missing function. This closes the work item the capability probes recorded as the largest gap in the value layer: the probe `real_transcendental_functions` now reports **holds** and checks the identities instead of the refusal, moving the totals to **33 probes, 19 hold, 14 break, 0 errored, 0 surprises**. Added `RequestProject/GLM/Transcendental.lean` (17 → 18 files, still no `sorry`, still only `propext`, `Classical.choice`, `Quot.sound`): the Lipschitz budgets `exp_error_le`, `sin_error_le`, `cos_error_le` and `log_error_le`, the positivity witness as an equivalence (`pos_iff_witness`), the range reduction `log_mul_two_pow`, and the power route `rpow_eq_exp_mul_log`. Added `tests/test_transcendental.py` (83 tests); test count 1,241 → **1,324 passed, 6,331 subtests, zero failures**. `INFINITE_VALUES_STUDY.md` §2.2 and §3.5 record the new boundary. |
| 4.6 | 2026-08-24 | Documentation reconciled against a full re-run, with no change to the code. The whole suite was collected and run here (**1,324 passed, 6,331 subtests, zero failures**), the eighteen Lean files were rebuilt with `lake build` and re-checked for `sorry` (none), the six example scripts were each run end to end, the 33 capability probes were re-run (**19 hold, 14 break, 0 errored, 0 surprises**), the semantic graph was rebuilt (357 meanings, 1,705 notations, 6,210 binary and 6,649 ternary edges) and `report semantics --verify-tct` returned `VERIFIED True`. Corrected the stale figures the last round left behind: the tests-README pointer and the reasoning README both quoted an earlier test count, and the Lean pointer here and in the repository README still said seventeen files. Added `Transcendental.lean` to the repository README's file list, and added the missing **Phase 4** section to `MASTER_PLAN.md` — the semantics work shipped as v1.1.0 was wired and tested but never entered the plan, including its two rows in the runtime-surface table. |
| 4.7 | 2026-08-25 | `glm_universal` v1.2.0, **extended**: ambiguity made a value the machine can carry. Added `substrate/superposition.py` — the nearest codewords of a received word kept together as one `Superposition`, bundled over F₂ and over Q, and collapsed only by a context. The finding is a contrast between the two bundles, and both halves are measured and proved: over 256 superpositions the F₂ (XOR) bundle takes exactly **one** value, `16777215` = all ones, so it distinguishes **1** of the 256 inputs and is information-free at this arity, while the rational bundle has coordinates only in `{1/6, 5/6}`, distinguishes **all 256**, and is inverted exactly by `recover_from_bundle`. `collapse` reports `collapsed` / `superposed` / `refuted` and never breaks a tie by member order. Added five Lean files (18 → **23**, still no `sorry`): `Golay/Code.lean` and `Golay/Sextet.lean` build the code from the parity block `substrate/mog.py` ships and settle its geometry — minimum distance 8, unique reading up to weight 3, covering radius exactly 4, and at a deep hole **exactly six** nearest codewords (`ties_card_eq_six`) whose supports partition the 24 coordinates into six tetrads (`sextet_partition`) — with the finite parts exhaustive over all 4,096 syndromes by `native_decide`, so those results additionally depend on `Lean.ofReduceBool` and `Lean.trustCompiler`; `Superposition.lean` proves `bundleF2_eq_one` and the injectivity of the rational bundle; `Wobble.lean` that a carrier cycling through the six readings is read back exactly as that bundle; `HullExpansion.lean` that a target separated from the hull of the available states by an explicit functional is unreachable under **any** schedule and reached in a 16-tick cycle once two Leech vectors are admitted (`alphabet_expansion_strictly_helps`). Wired as the nineteenth report subject, `report superposition` (aliases `ambiguity`, `tie`, `sextet`, `bundling`, `parallel hypotheses`, `list decoding`), with a column-3 template that returns `VERIFIED True`. Added `tests/test_superposition.py` (39 tests); test count 1,324 → **1,363 passed, 6,331 subtests, zero failures**. The write-up is `GEOMETRIC_AMBIGUITY_STUDY.md`, which also names what is not settled: the VOA state-field map, the Niemeier deep-hole census, and the self-organised-criticality reading of the mean coset weight. |
| 4.8 | 2026-08-25 | The coset census landed, and the dynamical half of the criticality question answered. `RequestProject/GLM/Golay/Census.lean` (mirrored into `glm_lean/`) counts the cosets — `1, 24, 276, 2024, 1771` — so **2,325** of the 4,096 are read uniquely and **1,771** are six-fold ties, and the mean distance to the code is exactly **`3433/1024`**, strictly between the packing radius 3 and the covering radius 4: the *average* word already sits past the radius of unique reading, so ambiguity is the typical case for this code rather than a corner case. `Golay/Dynamics.lean` turns the self-organised-criticality reading into a statement about a process and settles it: the uniform law is stationary and is the **only** stationary law (`step_unif`, `stationary_unique`), its mean distance is the census figure and it holds `3795/4096` at distance 3 or 4 — but every parity-check column has odd parity, so the chain is periodic and has **no** limiting law (`iterate_dirac_ne_unif`), the stationary law keeps `301/4096` below the packing radius so it does not concentrate, and a corrected one-bit error returns the same codeword (`perturb_correct_returns`), so a corrected carrier never drifts to the boundary at all. The claim survives only in its time-averaged form; the Cesàro convergence statement is recorded as open with its exact obstruction. Lean files 23 → **25**, still no `sorry`. In the package, `substrate/superposition.py` gained `coset_weight_distribution`, `mean_coset_weight`, `coset_census_report` and `coset_chain_report` — all exact `Fraction`/`int` arithmetic, no float, no sampling — and `report superposition` gained two more steps (four → **six**), still `VERIFIED True` from the column-3 template. `test_superposition.py` 39 → **61**; test count 1,363 → **1,385 passed, 6,331 subtests, zero failures**. |
| 4.9 | 2026-08-25 | `glm_universal` **v1.3.0** — the machine measured from outside, and a ninth sub-package to do it with. `capabilities/` asks the library where it stops and `benchmarks/` scores solver functions, but neither goes through `GLM.py`, so neither measures what a user gets. `evaluation/` does: **72 cases**, each starting the CLI in a **fresh interpreter** — one subprocess per question, no shared session, no warm caches — and scoring the `ANSWER` or `UNSOLVED` line the process prints. The question set covers **all 18 query kinds** and **all 19 report subjects**, and `test_evaluation.py` checks that coverage against the runtime's own tables so neither can be extended without a case. Scoring is deliberately asymmetric — `correct` and `refused_as_expected` score `+1`, an `unexpected_refusal` `0`, and a `wrong_answer` or a crash **`−1`** — because a refusal tells the user where the machine stops and a confident wrong answer does not; 11 of the 72 questions are ones the machine *should* refuse, each labelled `boundary` (a theorem or a deliberate commitment) or `gap` (missing implementation). Result: **67 of 72 passed** — 57 answered correctly, 10 refused as expected, **0 unexpected refusals**, 5 confidently wrong, 0 errored — with `report` at 20/20, `verify` 6/6, `describe` 6/6, `meaning` 6/6, `real` 5/5, `compare` 4/4, and **every failure in one kind**, `analogy` at 3/8. One gap was closed in the same run: `approximate 1/0 to 5 places` escaped as an uncaught `ZeroDivisionError` traceback (outcome `error`, weight `−1`) and now refuses, saying a quotient by an exact zero names no value (outcome `refused_as_expected`), moving the evaluation 66 → **67 of 72** and errored cases 1 → **0**. Re-ran the other two instruments here as well: **33 probes, 19 hold, 14 break, 0 errored, 0 surprises** and **2,380/2,390 benchmark tasks across 5 suites, every suite above baseline**. Bumped `glm_universal.__version__` to **1.3.0** and pinned the nine sub-packages in `test_wiring.py::TestPackageSurface`. Added `tests/test_evaluation.py` (19 tests); test count 1,385 → **1,405 passed, 6,331 subtests, zero failures**. The write-up is `CAPABILITY_ASSESSMENT.md`; see "GLM-3+ v1.3.0 — measuring the machine from outside" at the bottom of this README. |
| 5.0 | 2026-08-25 | The round that closed the evaluation set and bound the documentation to the code. **Analogy by named relation.** `reasoning/analogy_models.py` adds the layer the vector-offset solver was missing: four named models — `periodic_step`, `reciprocal_dimension`, `scale_shift`, `lexicon_relation` — each of which says what the relation between `A` and `B` *is*, in the register's own terms, or declines; a model that recognises the pair and finds nothing at the transported position **refuses and says where it looked** instead of falling back on the nearest point to a meaningless target. All five of the previous round's confidently wrong answers are closed (`He : Ne :: Ar : ?` → `Kr`, `B : Al :: C : ?` → `Si`, `length : wavenumber :: time : ?` → `frequency`, `solid : liquid :: liquid : ?` → `gas`, and `heat : temperature :: force : ?` now **refused** with both halves of the reason stated), and the three semantic-benchmark misses that survived it are closed too: `proton` now records `opposite_of electron` rather than the untransportable `related_to`, `accelerate` and `rotate` now share the parent `form_of move`, and the curated target of `cause : effect :: force : ?` was corrected from `motion` to `acceleration`, which is what the register's own triple `force causes acceleration` says. Wired as `report analogies`; the write-up is `ANALOGY_LAYER_STUDY.md`. **The molecules register** — `data_objects/molecules.py`, the sixth register: 51 molecules and ions, a formula grammar reading counts, nested brackets, hydrates and charges, and nothing stored per species but a name and a formula, with all 19 coordinates derived from the element register at load time. Held twice, as a faithful bundle of element carriers with multiplicities and as one composite summary carrier, with collisions *tested* rather than trusted: 0 of either kind. `report molecules`. **Chemistry coverage** — `reasoning/element_coverage.py` measures the sparsity (1,257 of 1,652 cells) and widens it three ways that each invent no measurement: derive (4 attributes, 344 new cells), estimate (one linear fit, covalent-radius coverage 12/59 → 99/118) and cross-check (14 comparable elements, 10 agreeing within 20 kJ/mol and 4 not — reported, not merged). Nothing is written back. `report chemistry coverage`. **The figures mechanism** — `glm_universal/figures.py` recomputes every count the documentation quotes into `FIGURES.md`, and `tests/test_figures.py` compares the committed file against a fresh computation *and* checks each README against the current numbers, so a stale figure is a test failure rather than something a reader discovers. **The inherited concept graph, decided** — `semantics.audit.retention_decision()` records **demoted to evidence**, with its grounds recomputed (4,282 concepts / 83 grounded, 4,015 edges / 2 derivable), and `tests/test_inherited_graph.py` enforces it by walking the imports of every module on the answering path. **Cesàro convergence proved** — `RequestProject/GLM/Golay/Cesaro.lean` closes the one item `Golay/Dynamics.lean` recorded as open: `|cesaro μ N f − 1/4096| ≤ 24/N` for every probability law, every syndrome and every `N ≥ 1`, by exact Fourier analysis over ℚ on the syndrome group, plus `cesaro_tendsto` for the same statement as a limit. **The VOA state–field map, at last, and honestly.** `RequestProject/GLM/VOA.lean` builds `Y(u, z) = Σₙ uₙ z⁻ⁿ⁻¹` on the three-dimensional 2A algebra: the Griess product is the single mode `u₁ v`, the field is truncated, `mode_skew` is the skew-symmetry axiom at this weight, and the invariant form is *forced* rather than chosen — invariance alone gives `⟨eᵢ, eⱼ⟩ = (1/8)⟨eᵢ, eᵢ⟩` — so the layer is a Frobenius algebra with self-adjoint modes and a vacuum `(4/5)(e₀+e₁+e₂)` of square length `12/5`. It then proves where that stops: `borcherds_commutator_fails` shows the commutator formula at `m = n = 1` would demand `u ⋆ (v ⋆ w) − v ⋆ (u ⋆ w) = (u ⋆ v) ⋆ w`, and on the axis triple the sides are `(−3/32) e₀ + (3/32) e₁` and `(−3/32) e₂`, so the discarded modes are load-bearing and the infinite-dimensional half of the bridge is necessary rather than traditional — and is not built. Lean files 25 → **27**, still no `sorry`. Measured after all of it: **83 of 83** CLI cases (73 answered, 10 refused as expected, 0 unexpected refusals, **0 confidently wrong**, 0 errored), **2,389 / 2,390** benchmark tasks with the three analogy suites now 12/12, 13/13 and 10/10, **33 probes, 20 hold, 13 break, 0 errored, 0 surprises**, and **1,669 tests across 37 test files, 8,818 subtests, zero failures**. Documentation reconciled against those figures throughout, and a single status document added at the repository root, `STATUS.md`. |
| 5.1 | 2026-08-25 | Two fixes from the last round recorded and pinned, and the figures regenerated against a full re-run. **The theta template.** `report theta` claims six coefficients — `theta_series(order=5)` returns `[1, 0, 196560, 16773120, 398034000, 4629381120]`, and the solver puts every one of them into `expected` — but the column-3 template hand-wrote the keys `coeff_0` .. `coeff_4`, so the last coefficient was stated in column 2 and never re-derived in a fresh interpreter; the parent's own comparison reported it as a missing key rather than a verified claim. The template now builds its `observed` map by enumerating whatever the series returns, so the check widens with the series instead of having to be widened by hand, and `report theta --verify-tct` returns `VERIFIED True` over all six. `test_runtime.py::TestReportThetaTemplate` (3 tests) pins it: that `expected` holds one key per returned coefficient, that the generated script enumerates rather than lists, and that a subprocess reproduces all six with no missing keys — all three fail against the old template, so the regression cannot come back silently. **The session docstring's quantity count, confirmed.** `runtime/session.py` described the registers it loads as `physics (660 quantities)`, the figure from before the register grew; it now reads 726, which is what `len(session.register("physics"))` returns and what `FIGURES.md` reports under *Registers*. The fix is now verified rather than asserted: `test_figures.py::TestModuleDocstringsQuoteCurrentFigures` (5 tests) reads the physics, chemistry and molecule counts out of that docstring and out of `data_objects/physics.py`'s, and compares each against the live register, and checks all six registers are named — the physics assertion fails if the docstring is put back to 660. **Figures and documentation.** `python -m glm_universal.figures --write` was re-run and `FIGURES.md` regenerated: every row is unchanged except the collected test count, 1,669 → **1,677**. The suite was run in full here — **1,677 passed, 8,851 subtests, zero failures** — and the counts quoted in `STATUS.md`, `MASTER_PLAN.md`, `CAPABILITY_ASSESSMENT.md`, this README and the package and tests READMEs were updated to match, with `1,669 tests` and `8,818 subtests` added to the superseded-phrase guard in `test_figures.py`. This README's version header, still reading 4.9 while the change log had reached 5.0, is corrected. No behaviour changed beyond the theta template. |
| 5.2 | 2026-08-28 | The round that tested the blueprint and put the wobble to work. **The unification blueprint as a live claim ledger** — `reasoning/blueprint.py` recomputes every testable sentence of `glm_unification_blueprint.md` against the package and gives each one of four verdicts, and the three subjects it needed to reach one are built beside it: `reasoning/engine.py` (Part III's carrier engine assembled from parts that already existed, so the claimed precision leap is measured against the three baselines it could mean rather than quoted), `reasoning/mantissa.py` (section 5.1's bit-spectrum tracker, with IEEE-754 binary64 modelled exactly in integers and `Fraction` so that **no float is ever constructed**) and `reasoning/reversible.py` (Part V: the Gray-code read channel, the Toffoli and Fredkin gates, the kink invariant). Wired as `report blueprint`, `report engine`, `report mantissa` and `report reversible`, pinned by `tests/test_blueprint.py` (77 tests), with `RequestProject/GLM/Mantissa.lean` and `Reversible.lean` as the machine-checked half — a float's dyadic orbit always collapses while the exact orbit of `1/p` never does, and Gray coding does **not** dissipate exactly half at any finite width, the sharp statement being `2·grayCycleFlips w = binaryCycleFlips w + 2`. **Noise as the computation** — `reasoning/noise_lab.py`, exact `Fraction` throughout and nothing random anywhere: a modulator driven by a two-tone signal tracks its running mean to 7/1152 against the bound 1/128; a periodic input closes its orbit exactly when its period sums to a whole number; a MASH 1-1 cascade's error is a second difference at every tick and, read through a triangular window, beats a single loop by a factor of 127 at M = 128; an exact Walsh spectrum reads the strength of each tone in a mix; and a subtractive-dither sweep trades the idle tone from 1/1 down to 33/128 for a bias it states. `RequestProject/GLM/Cascade.lean` proves what the module measures — `mAverage_error_le` (a signal, not a constant, tracked to `1/N`), `mState_periodic` (the closed orbit), `casOut_error` (the error is a second difference) and `casTriangular_error_lt` against `firstOrder_triangular_error_ge`, which is `O(1/M²)` against `O(1/M)`. Wired as `report noise` (aliases `wobble`, `wiggle`, `dither`, `cascade`), pinned by `tests/test_noise_lab.py` (40 tests); the write-up is `NOISE_EXPERIMENT_STUDY.md`. **The evaluation set** grew 83 → **89 cases** so that all 30 report subjects are exercised, and the previous round's single `gap` is closed: `nearest to PbCl2` now hands an operand no register enumerates to the formula parser and ranks the carrier it builds, guessing nothing. Closing it exposed where the gap label moves to — `coherence PbCl2`, which still resolves register names only — and the duplicate analogy case that had been standing in for a gap was removed. Measured after all of it: **89 of 89** CLI cases (79 answered, 10 refused as expected — 9 boundary, 1 gap — 0 unexpected refusals, **0 confidently wrong**, 0 errored) and **1,799 tests across 39 test files, 8,851 subtests, zero failures**; Lean files 27 → **30**, 7,388 lines, still no `sorry`. Documentation reconciled against those figures throughout. |
| 5.3 | 2026-08-28 | The round that tested the external study catalogue. **`glm_study_findings_catalog.md` as a live claim ledger** — `reasoning/catalog.py` restates every testable sentence of it as a claim, recomputes it against the package and gives it one of four verdicts: **57 claims, 32 confirmed, 14 refuted, 7 not reproduced, 4 not implemented**, wired as `report catalog` and pinned by `tests/test_catalog.py` (26 tests). The two instruments it needed were built beside it. **The spectral signature** — `reasoning/wobble.py` and `report signature` (33 tests) run the catalogue's ten-thousand-tick experiment and print the *law* beside every measured column, because `RequestProject/GLM/Sturmian.lean` proves the stream is the mechanical word of its target: `dsState_eq_fract`, `dsBit_eq_floor_diff`, `dsOnes_eq_floor`, the run-length bounds `1/t` and `1/(1−t)`, `dsTransitions_rate_tendsto`, `dsMeanRunLength_tendsto` and `ds_wobbleEntropy_tendsto`, with `ds_resonance_lock` putting the locked loop at entropy exactly zero — so running the loop tests nothing the target did not already fix, and the entropy dip at resonance is local rather than global. **Iteration drift** — `reasoning/drift.py` and `report drift` (26 tests) rerun the prime recurrence for 200 steps in exact rationals, in an exact binary64 model and in binary64 truncated to a fixed number of displayed digits, with **no float constructed anywhere**: the contractive rule stays inside every regime's ceiling and the accumulative rule reaches `7.49e+10` at `p = 3` in binary64 and `2.22e+22` at four digits. `RequestProject/GLM/Feedback.lean` landed in the same round: the vector modulator whose error returns through a rational matrix, with `efErr_abs_le_half`, `efAverage_error_le_identity` (`1/(2N)`, sharper than the scalar `1/N`), `halfFeedback_dead_zone` and `efOut_equivariant`. Measured after all of it: **92 of 92** CLI cases (82 answered, 10 refused as expected — 9 boundary, 1 gap — 0 confidently wrong, 0 errored), 33 report subjects, **1,884 tests across 42 test files, 8,864 subtests, zero failures**, and Lean files 30 → **32**, 8,157 lines, still no `sorry`. The write-up is `GLM_STUDY_CATALOG_AUDIT.md`. |
| 5.4 | 2026-08-28 | The round that finished the previous one and reconciled the chain. `RequestProject/GLM/Feedback.lean` and its Python counterpart, `reasoning/noise_lab.py`'s error-feedback section, were built but reached from nothing: `feedback_experiment` was not in `noise_report`, no test touched it, and the study still listed error feedback as not started. It is now the **sixth step of `report noise`** — the `1/(2N)` law in every coordinate, the dead zone at `A = 1/2` where the quantiser never fires, and equivariance under a permutation the matrix respects with a non-invariant matrix run beside it — re-derived by the column-3 script (`VERIFIED True`) and pinned by ten new tests in `tests/test_noise_lab.py` (40 → 50). Documentation: the Lean README gained the missing `Sturmian.lean` and `Feedback.lean` rows, `MASTER_PLAN.md` gained **Phase 9** (the catalogue ledger, the spectral signature, the drift study, error feedback) and eight missing runtime-surface rows, the reasoning and runtime READMEs gained `wobble.py` / `drift.py` / `catalog.py` and `report signature` / `report drift` / `report catalog`, `STATUS.md` and the repository README record the catalogue round and the document map now lists both audits, and `NOISE_EXPERIMENT_STUDY.md` gains §6 on error feedback. `tests/test_figures.py` now holds `STATUS.md` to the generated figures as well, so the status document cannot drift again. Re-verified here: `lake build` clean over 32 Lean files with no `sorry`, **1,894 tests across 42 test files, 8,896 subtests, zero failures**, 92/92 CLI cases, 2,389/2,390 benchmark tasks, 33 probes (20 hold, 13 break, 0 errored). |
| 5.5 | 2026-08-29 | `glm_universal` **v1.4.0** — the two companion preprints tested, and the last carrier gap closed. **Three containers, as an instrument.** `reasoning/containers.py` carries eight constants (`1/3`, `sqrt(2)`, the golden ratio, `pi` by Machin, `e` by its series, Liouville, Champernowne, an `Omega` surrogate) through the algorithmic, temporal and geometric containers of *The Generators and Containers of Real Processes*. Every generator is an exact `Fraction` recurrence; `precision_bits` is decided by integer comparison against a 200-bit reference, so no float is constructed anywhere in the module. `stream_period` *decides* the period from the target's denominator rather than searching a window, and `apparent_period` / `near_period_coincidence` are the counterweight: `sqrt(2)`'s stream matches its own 169-shift for 400 places and first disagrees at index 407. Hull verdicts are certificates — a separating direction for `outside`, the box `{|x|_1 <= 8, |x|_inf <= 4}` for `inside` — and anything neither settles is `undetermined`. Wired as `report containers`, pinned by `tests/test_containers.py` (52 tests). **The preprints as a claim ledger.** `reasoning/companion.py` restates both companion studies as testable claims and recomputes each one from `containers`, `drift`, `leech_construct`, `golay_decode`, `niemeier` and `wobble`: **49 claims — 26 confirmed, 17 refuted, 5 not reproduced, 1 not implemented**. Write-up in `GLM_COMPANION_STUDIES_AUDIT.md`; wired as `report companion`, pinned by `tests/test_companion.py` (27 tests). Both subjects return `VERIFIED True` under `--verify-tct`. **A carrier in every solver that takes one.** `coherence`, `spatial`, `angle` and `cluster` now fall through to the formula parser for an unregistered molecule, as `nearest` and `describe` already did, so `coherence PbCl2` answers instead of refusing — which removed the evaluation set's last `gap` case. 35 report subjects; 97 cases, 97 passed (88 answered, 9 boundary refusals, 0 gap); 1,991 tests across 44 test files, zero failures. |
| 5.6 | 2026-08-29 | `glm_universal` **v1.5.0** — above 24 dimensions, the Lean development given an address, and the standing rules turned into instruments. **The two rungs above the Leech lattice.** `substrate/lattice32.py` builds the 32-dimensional Barnes–Wall lattice by Construction D over `RM(1,5) ⊂ RM(3,5)`; its three levels are genuinely nested lattices of index `2^26` and `2^6` (product `2^32`, checked), so a 32-dimensional address has **three usable resolutions** where a Leech address has one, and truncating to the first *k* levels lands exactly on the nearest point of the *k*-th. `substrate/lattice48.py` builds a 48-dimensional extremal lattice from a self-dual ternary code and a neighbour step, at centre density exactly `(3/2)^24` — about **16,834 times** the Leech lattice's — and at the cost of the whole binary picture. `reasoning/higher_lattices.py` recomputes the ladder rather than quoting it (`report lattices`); `RequestProject/GLM/HigherLattices.lean` is the machine-checked half. **Delta–sigma against a shell.** `reasoning/shell_sigma.py` widens the alphabet to the 196,560 minimal vectors, so it no longer covers its own hull: a target inside is tracked to the `B/N` law of the matched rule, a target outside is certified unreachable by a separating functional, and the Gibbs-style rule is reached **without randomness** by greedy error feedback, inside the proved bound `(m−1)/N` at every temperature (`report shells`, `ShellSigma.lean`). Write-up: `HIGHER_LATTICE_STUDY.md`. **A Leech address for every Lean declaration.** `reasoning/lean_address.py` reduces each of the **849** declarations (35 files) to 24 integer counts of its statement, scales by 9 and decodes to the nearest Leech point. Read back exactly **849/849**, 0 coordinate errors out of 20,376, worst residual 3 against a covering radius of 4; 795 distinct addresses — exactly the number of distinct feature vectors, so the quantiser adds no conflation of its own; nearest-by-address shares a file **325/849 ≈ 38.3 %** against 27 for a SHA-256-of-the-name control, 20 for a seeded reshuffle of the same addresses, and a chance rate of `2005/59996 ≈ 3.34 %`. Scale 9 and not 8 because `8ℤ²⁴ ⊆ Λ` (`eightZ_mem_leech`), which would make the decoder an identity map; `readback_unique` makes the read-back well defined and `address_congr` says the address can carry no distinction the features have already discarded (`report lean`, `Address.lean`). Write-up: `LEAN_ADDRESS_STUDY.md`. **The standing rules, as instruments.** `PROJECT_DIRECTIVES.md` states eight rules and names the instrument for each; `reasoning/directives.py` parses that file and gives each instrument a live verdict (`report directives`), `reasoning/pipeline.py` reads the stage each piece of work has reached off the tree rather than from prose — **14 of 14 rows** through all six stages (`report pipeline`), `glm_universal/signoff/` plans a run against recorded dependency digests computed with `ast`, and `glm_universal/integrity.py` holds every SHA-256 use one module above the six core sub-packages so the purity audit enforces directive D3 by layout. `glm_universal/tools.py` is their command line. A new audit requires every `GLM.…` Lean name cited anywhere in the package to resolve to a real declaration; it found two stale citations, both corrected. The declaration reader was fixed twice: it was reading prose inside `/- … -/` as declarations and skipping declarations behind an attribute, which moved the corpus 804 → **849**. Measured after all of it: 40 report subjects; **102 of 102** CLI cases (93 answered, 9 boundary refusals, 0 gap, 0 confidently wrong, 0 errored); 33 probes (20 hold, 13 break, 0 errored); 2,389/2,390 benchmark tasks, every suite above baseline; **2,183 tests across 50 test files, 9,088 subtests, zero failures**; Lean files 34 → **35**, 9,213 lines, still no `sorry`. |
| 5.7 | 2026-08-29 | `glm_universal` **v1.6.0** — the sign-off ledger made sound, and every instrument put inside it. The previous round built `glm_universal/signoff/`: a test file is *signed off* when it has passed and nothing it depends on has changed since, the dependency set computed with `ast` rather than declared. **The hole.** That closure was imports only, so it did not contain the documents. `tests/test_figures.py` exists to catch a stale count in `STATUS.md`; with `STATUS.md` outside its digest the ledger would have gone on reporting that check as signed off while the document was being rewritten — a saving bought with a false statement. The closure now carries the documents and Lean sources a unit's modules *name*, found by parsing each module's string constants: a constant naming `MASTER_PLAN.md` pulls that document in, a constant naming a `.lean` file pulls in the whole development with `lakefile.toml`, `lean-toolchain` and `lake-manifest.json`, and a name that occurs more than once pulls in every copy. Over-hashing is the safe direction (**D4**). Measured: `test_figures.py`'s closure is 200 files and holds every document it checks; `test_substrate.py`'s holds none, so writing documents does not make the substrate tests stale. The schema is bumped 1 → 2, discarding every signature written under the old rule rather than trusting it. **The gap.** `signoff/checks.py` makes the other instruments units of the same ledger, with the same rule: `lean-build`, `lean-sorry-free`, `lean-copies-identical`, `capabilities`, `benchmarks`, `evaluation` and `figures`. Each has a command, a directory, a closure and the return codes that count as success (`grep` reports 1 when it finds nothing, which is what the sorry scan wants); the command is part of the digest. `figures.py --check` is new and prints a unified diff against a fresh computation. **The command line.** `--plan`, `--verify`, `--run`, `--run-checks`, `--run-everything`, `--run-all`, `--run-checks-all`, `--closure NAME` (a test file or an instrument), and `python -m glm_universal.tools signoff` for the read-only summary. Signatures are written after each unit, not at the end, so an interrupted session keeps what it has earned. Write-up: `MASTER_PLAN.md` Phase 12; the rule itself is directive **D4** in `PROJECT_DIRECTIVES.md`. |
| 5.8 | 2026-08-29 | `glm_universal` **v1.7.0** — a harmonic register, and the third of a claim it makes testable. The supplied study catalogue's §6.2 says chemical equilibria, musical harmony and market price discovery all map to Leech proximity, and `reasoning/catalog.py` had carried that sentence as **not implemented** for several rounds because there was nothing musical or economic to run it against. **The register.** `data_objects/harmonics.py` holds **28 intervals** as exact rational frequency ratios — 18 just, 5 septimal, 5 commas, prime limits 2/3/5/7 — with all 24 coordinates computed from the pair `(n, d)` rather than stored beside it, so the codec's round trip is exact and no float exists anywhere. It is the seventh register, `harmonics`, and the runtime loads it like the rest. **The study.** `reasoning/harmony.py` and `report harmony` test the sentence instead of repeating it. The nearest equal step is decided by comparing `r^24` against powers of two — integers, not logarithms — so the tempering error is the exact rational `(n/d)^12 / 2^k`: `1` at the unison and the octave and nowhere else, `531441/524288` at the fifth. No stack of fifths is a stack of octaves to `n = 200`. Tenney height and Euler's gradus agree at an exact Kendall tau of `313/378`. Then the claim itself: each interval is decoded to its nearest Leech point through its prime exponents — deliberately not through its carrier, which holds consonance outright and would make the claim true by construction — and swept over scales 1 to 32. At scale 1 the lattice puts fifteen of the 28 intervals on the unison's own point; from scale 4 every interval has its own point; from scale 8 distance from the unison orders them at tau `53/63`. **The verdict is `not reproduced`**, and the control is what decides it: the same distance taken *before* the decoder runs scores `53/63` too, and the decoder reorders **0** pairs, so what is measured is the prime-exponent vector rather than the geometry of the Leech lattice. **The ledger.** §6.2 is now two claims — the musical half reading its verdict off the harmony report at call time, the economic half still `not implemented` because there is no register of prices — so the catalogue ledger is **58 claims: 33 confirmed, 14 refuted, 7 not reproduced, 4 not implemented**. **The Lean.** `RequestProject/GLM/Harmony.lean`: `odd_prime_ratio_ne_two_zpow` — a ratio in lowest terms carrying any odd prime is not a step of *any* equal division of the octave, for every number of divisions at once — with `three_pow_ne_two_pow`, `fifth_never_closes`, three named corollaries and the two commas exact. Measured after all of it: **103 of 103** CLI cases (94 answered, 9 refused as expected — all boundary, **0 gap**), 41 report subjects, 7 registers holding 1,068 carriers, the pipeline board at **15 of 15** rows, **2,308 tests across 51 test files, 9,165 subtests, zero failures**, and Lean files 35 → **36**, 9,410 lines, still no `sorry`. The write-up is `HARMONY_STUDY.md`. |
| 5.9 | 2026-08-30 | The address study reconciled against the corpus it now measures, with no change to the package's behaviour. Adding `RequestProject/GLM/Harmony.lean` in the previous round widened the Lean development from 35 files to 36, so every figure in `LEAN_ADDRESS_STUDY.md` moved and nothing in the text said so. Re-measured here: **861** declarations across **36** files (557 theorems, 201 defs, 82 lemmas, 6 abbrevs, 5 each of inductive / instance / structure), read back **861/861** with **0** coordinate errors out of **20,664**, **806** distinct addresses for 861 declarations — exactly the number of distinct feature vectors, so the quantiser still adds no conflation of its own — in **47** collision classes covering 102 declarations. On the separation tests, nearest-by-address shares a file **330/861 (38.3 %)** against **26** for the SHA-256 control and **20** for the seeded reshuffle, with the chance rate recomputed from the file sizes at `288/8815 ≈ 3.27 %`; nearest is cited either way **72/861 (8.36 %)** against 10 and 5, chance `1123/185115 ≈ 0.61 %`. The study, `STATUS.md`, the package README and the overlay document index now state those numbers; the per-phase record in `MASTER_PLAN.md` is left at the figures measured when that phase closed, as a phase record should be. **The drift is now caught rather than noticed.** `test_lean_address.py::TestDocumentsQuoteTheCurrentCorpus` parses the development and requires the four documents that quote the corpus size to quote the size the parser finds, so the next Lean file added fails the suite instead of silently ageing the prose. Re-run after the edits: **2,309 tests across 51 test files, 9,170 subtests, zero failures**; **103 / 103** CLI cases (94 answered, 9 refused as expected — all boundary, 0 gap, 0 confidently wrong, 0 errored); `report lean`, `harmony`, `directives`, `pipeline`, `containers`, `companion`, `lattices`, `shells`, `semantics`, `noise`, `catalog`, `drift` and `signature` each `VERIFIED True` under `--verify-tct`; `lake build` clean over 36 Lean files, 9,410 lines, still no `sorry`; `FIGURES.md` regenerated. |
| 5.10 | 2026-08-30 | The layer chain made a real refinement on the shipped definitions, and the repository root tidied. **Part 1 — organisation.** The eleven study write-ups moved to `studies/` and the supplied material (archives, PDFs, `ToDo_01.txt`, the three supplied `.md` sources and `geometric_substrate_study.py`) to `source_material/`; `README.md`, `STATUS.md`, `MASTER_PLAN.md`, `CAPABILITY_ASSESSMENT.md` and `PROJECT_DIRECTIVES.md` stayed at the root, joined by a new one-line-per-document index `DOCUMENTS.md`. Every moved link was repointed, including the ones the code quotes: `reasoning/pipeline.py` and `reasoning/directives.py` now search `studies/` and `source_material/` as well as the two roots, eleven module and test docstrings name the new paths, and `tests/test_lean_address.py` holds `studies/LEAN_ADDRESS_STUDY.md`. Compiled bytecode was removed from version control and ignored. Two over-long documents were split at the `<!-- figures:history -->` marker: `README.md` 3,779 lines to 410 plus `README_ARCHIVE.md`, and `MASTER_PLAN.md` 1,375 lines to a header, a phase index and the open phase plus `MASTER_PLAN_ARCHIVE.md`. No module name, package structure, query surface or Lean file changed. **Part 2 — the refinement chain.** The audit finding that had been open for several rounds is closed. Both candidate fixes are now stated in `studies/INFORMATION_LOSS_STUDY.md` §3.1 — widen the integer layer's view, or narrow the substrate's — together with the reason the project's own account of a cumulative ascent commits it to widening, so that no information is lost at any stage. The report now says `refinement_chain_intact = True` on the real carriers, all four boundaries refine, and the rejected narrow reading is kept beside the stack as `LAYER_INTEGER_RAW` (resolves 4/7, loses 3, violates refinement on `(0,4)` and `(1,4)`) against the shipped `LAYER_INTEGER` (resolves 5/7, loses 2, no violations). `RequestProject/GLM/LayerChain.lean` states and proves the chain about the layers as they now are, on the real 24-coordinate carriers and with no `sorry`: `GLM.Info.glmChain_refines_of_le`, `GLM.Info.glmSi7Layer_not_refines_glmSubstrateLayer`, `GLM.Info.glmIntegerLayer_separates_unitOutside`, `GLM.Info.glmIntegerLayer_least` and ten more, and the study cites them by full name. A new `TestTheClosedRefinementDefect` class pins the chain and the vacuum / unit-on-coordinate-10 carrier pair that exposed the defect. Test count: 2,316 tests across 51 test files, 9,170 subtests, zero failures. |
| 5.11 | 2026-08-30 | The layer chain audited at register scale, and the resolution ceiling it exposes. The previous round closed the refinement chain on the seven carriers of `report information loss` — and each of those seven had been chosen *because* it exhibited a boundary, so the result was never a measurement of anything but the sample. `reasoning/escalation.py` re-runs the whole audit on **one carrier per named object of every register the package ships** — physics 726, chemistry 118, molecules 51, mathematics 22, harmonics 28, lexicon 95, **1,040** in all, nothing sampled. The naive audit is quadratic in the carriers and its congruence search quartic; both are avoided by grouping carriers under each layer's own **class key** — the parity bits at the substrate, the SI7 exponents beside them at the integer layer, the exact carrier at the three above — which is exactly that layer's zero-measure set, so one pass answers what a scan would. The shortcut is checked rather than trusted: `key_agreement()` re-derives every verdict from the layers' own `perceive` and `measure` over 918 pairs and finds no disagreement, and a test deliberately breaks a key to confirm the check would notice. **Measured:** resolution 415 → 544 → 757 → 757 → 757 of 1,040, boundary gains 5,883 / 5,475 / 0 / 0, **zero refinement violations, chain intact `True`** — the Phase 14 result survives a hundred and fifty times as many questions. **Found:** a **resolution ceiling** the sample could not show — 757 distinct carriers means 283 named entries share a carrier, in **104 collision classes, every one inside a single register** (275 physics, 8 mathematics), the largest being 78 dimensionless physics quantities; no layer sees anything but the carrier, so what is missing there is a coordinate for the name, not a finer layer. The rejected `LAYER_INTEGER_RAW` reading, which cost one pair on seven carriers, conflates **11,176** pairs the substrate separates. Wired as `report escalation` (aliases `scale`, `registers`, `ceiling`, `resolution`, `at scale`) with a column-3 script that returns `VERIFIED True`; 34 tests in `test_escalation.py`; a 104th evaluation case, the set now **104/104**; `RequestProject/GLM/Escalation.lean` (37 → 38 Lean files, still no `sorry`) proving the ceiling `entryResolution_le_distinct`, the order of the stack `entryResolution_mono`, addition descending on a lossless view, and the half-unit witness for why it does not descend below; write-up `studies/ESCALATION_STUDY.md`. |
| 5.12 | 2026-08-30 | Measure words as relative measures, and the documentation reconciled against a full re-run. **The register.** `data_objects/comparison_classes.py` holds **33 comparison classes over 8 quantities** (temperature 6, velocity 5, mass 5, length 5, density 4, force 3, pressure 3, frequency 2), each an exact bracket in the SI base unit of its quantity, and **8 measure scales carrying 47 degree words** at exact positions in `[0, 1]`; the unit, the dimension and the ten EXT10 exponents of a class carrier are read out of the physics register at load time, so nothing dimensional is typed twice, and a class naming a quantity the register does not hold fails to load. `lexicon_agreement()` reports `agrees: True` over the 9 words the scales share with the semantic lexicon, with `heavy` flagged as the one word whose polarity is the neutral `1/2`. **The widening, measured.** `reasoning/measure_view.py` reads a word against a class as an exact rational — *hot* in tea is **363 K**, *hot* for a stellar surface **44,000 K** — and audits three views over the **45 uses** the registers admit: the static concept carrier resolves 12/45; the measure view resolves **45/45**, refines the static reading and gains 82 pairs with **0 violations**; the reading-only view resolves 43/45 and **does** violate refinement, 3 times, so the rejected reading is kept beside the shipped one rather than described. The static view is checked against `dimension_layers`' rational layer over all 990 pairs. **The residue.** 15 of the 66 `related_to` triples are converted by the physics register alone — 3 `same_dimension_as`, 12 `differs_by` — and the remaining 51 are reported with the reason each was declined; an attribution that could be made in more than one way is refused rather than guessed. **The query.** `measure` is the nineteenth query kind (`measure hot in tea`, `measure hot`, `measure 300 in tea`), wired as `report measure` with five aliases, and it refuses at the boundary — `measure large in room`, `measure dark in room`, `measure hot in walking`, `measure expensive in market` — with `GLM.Info.boundary_empty_of_unmeasured` saying the refusal is forced by the registers rather than missing from the code. **The Lean.** `RequestProject/GLM/MeasureView.lean` (38 → **39** files, 40 declarations of its own, still no `sorry`): `GLM.Info.measureLayer_refines_staticLayer`, `measureLayer_least`, `boundary_measureLayer_staticLayer` with `hot_tea_star_mem_boundary` for non-emptiness, `measureReading_not_refines_staticLayer` for the rejected replacement, and `magnitude_strictMono` for the scale order. Write-ups: `studies/RELATIVE_MEASURE_PROPOSAL.md` and `studies/RELATIVE_MEASURE_STUDY.md`. **The reconciliation.** The address study was re-measured against the corpus `MeasureView.lean` widened: **966** declarations across **39** files (623 theorems, 233 defs, 84 lemmas, 8 abbrevs, 8 structures, 5 each of inductive / instance), read back **966/966** with **0** coordinate errors out of **23,184**, worst residual 3 at `GLM.CoherenceRegime`, **899** distinct addresses — exactly the number of distinct feature vectors, so the quantiser still adds no conflation of its own — in **57** collision classes (48 pairs, 8 triples, one class of four) covering 124 declarations; nearest-by-address shares a file **343/966 (35.5 %)** against **28** for the SHA-256 control and **21** for the seeded reshuffle, chance `1996/66585 ≈ 3.00 %`, and is cited either way **76/966 (7.87 %)** against 11 and 1, chance `2678/466095 ≈ 0.57 %`. `STATUS.md`, `CAPABILITY_ASSESSMENT.md`, the overlay README, the package README and the tests README now state the current test totals, the 112-case evaluation set and the 966-declaration corpus, and eleven phrases this round retired — `42 report subjects`, `38 Lean files`, `52 test files`, `104 cases`, `2,350 tests`, `9,232 subtests` among them — were added to the superseded-phrase guard in `tests/test_figures.py`, each naming the unit it counts so that the still-true `104 collision classes` is untouched. Measured after the edits: **2,424 tests across 54 test files, 10,782 subtests, zero failures**; **112 / 112** CLI cases (100 answered, 12 refused as expected — all boundary, 0 gap, 0 confidently wrong, 0 errored); `lake build` clean over the 39 Lean files with no `sorry`, and the repository and overlay copies of the sources identical; `FIGURES.md` matching a fresh computation. |
| 5.13 | 2026-08-31 | `glm_universal` **v1.8.0** — the economic third of the universality claim decided, the hexcolour layer audited and given a lookup, the infinite-dimensional half of the VOA bridge built, and the documentation reconciled against a full re-run. **The economic register.** `reasoning/economics.py` carries **21 quoted prices** over 7 instruments and 3 quarters as exact rationals; the lattice separates all 21 records at scale **1024**, and every record's nearest neighbour is another quarter of the same instrument — **21 of 21**, against a chance rate of `1/10`. The undecoded control does exactly as well, so catalogue claim 6.2's economic half is recorded as **not reproduced** rather than confirmed, which is the same answer the musical third reached by the same instrument; the ledger now tallies 33 confirmed, 14 refuted, 8 not reproduced, 3 not implemented. `report economics` is the forty-fourth report subject and the 113th evaluation case, the harmonic and economic registers are both describable from the CLI, and `studies/ECONOMICS_STUDY.md` is the write-up. `RequestProject/GLM/LogBucket.lean` proves the exact magnitude bucket well defined, unique, monotone and shifted by exactly `s` under scaling by `base^s`, which is what makes the control one set of numbers rather than a sweep. **The hexcolour audit.** A hexcolour address is the six-hex-digit rendering of a 24-bit carrier, one digit per four coordinates. Measured on the shipped data rather than asserted: **4,680** concepts carry an address, all **4,680** distinct, **0** fail to read back to their own mask, **0** disagree with the mask stored beside them, **0** fail to commute with the legacy-to-core relabelling, and the **15** legacy per-task addresses left by the supplied ARC pipeline are all Golay codewords and all round-trip. The audit is the sixth step of `report state migration` and re-derives itself in a fresh interpreter (`VERIFIED True`). The gap it exposed — nothing ever *looked anything up* by an address — is closed: the concept store now has lookup by address and every one of the 4,680 concepts is tested to round-trip through it. The legacy ARC-AGI block's "66 hexcolour addresses" is kept as the upstream run's own count with a correction beside it. Write-up: `studies/HEXCOLOUR_STUDY.md`. **The VOA bridge, infinite half.** `RequestProject/GLM/Heisenberg.lean` builds the Fock space with creation, annihilation and mode operators and proves the Heisenberg commutator relation, that every state is annihilated by all sufficiently high modes, that the space is infinite-dimensional, Borcherds' commutator formula on it, and a trace obstruction showing that **no** nonzero finite-dimensional rational vector space admits the relation at all — the precise sense in which the finite Griess layer cannot be the whole story. **The reconciliation.** The Lean address book was regenerated over the corpus as it now stands (**1,020** declarations across **41** files, 10,897 lines, digest `b1ea6697…`) and every measured figure of `studies/LEAN_ADDRESS_STUDY.md` re-measured with it; the per-file test table in `tests/README.md` was corrected against a `--collect-only` run and given the two rows it was missing (`test_derived.py`, `test_economics.py`), and the package status table's Tests column now partitions all 56 files; `STATUS.md`, `CAPABILITY_ASSESSMENT.md`, `README.md`, `DOCUMENTS.md`, `MASTER_PLAN.md` (Phase 17) and the package READMEs state the current 8 registers, 1,089 carriers, 46 reasoning modules, 113 evaluation cases, 44 report subjects and 41 Lean files, and eleven phrases retired this round — `7 registers`, `43 report subjects`, `112 cases`, `2,424 tests`, `10,782 subtests`, `39 Lean files`, `966 declarations` among them — were added to the superseded-phrase guard in `tests/test_figures.py`. Measured after the edits: **2,515 tests across 56 test files, 11,033 subtests, zero failures**; **113 / 113** CLI cases (101 answered, 12 refused as expected, 0 confidently wrong, 0 errored); 2,389 / 2,390 benchmark tasks with every suite above its baseline; 33 probes (20 hold, 13 break, 0 errored); `lake build` clean over the 41 Lean files with no `sorry`, the repository and overlay copies identical; `FIGURES.md` matching a fresh computation, and all 56 test files and all 7 instruments signed off in one `--release` run. |
| 5.14 | 2026-08-31 | `glm_universal` **v1.9.0** — the two items the measure-word round left open, closed, and the factor basis measured instead of asserted. **The comparison-class register grown.** `data_objects/comparison_classes.py` gained *volume*, *illuminance* and *luminous intensity*: 33 classes over 8 quantities → **45 over 11**, 8 scales carrying 47 degree words → **11 carrying 64**, and the words shared with the semantic lexicon 9 → **12**, still agreeing on quantity, polarity side and the six opposite-pole pairs. All **12** of the lexicon's adjectives are measurable now — `large`, `small` and `dark` among them — so the widening audit runs over **56 uses**: the static reading resolves 12, the widened one all 56, gaining **108 pairs** with **0** refinement violations, checked against the rational layer on all 1,540 pairs. That growth removed the shipped data's own refutation of the rejected *replacement* reading, so `replacement_witness()` keeps it a number rather than an assertion: over the 56 uses **plus one unmeasured use of each word** — 68 in all — the widening gains 164 pairs with 0 violations and the replacement gains the same 164 while **violating refinement on 66**. **The factor basis, swept.** `FACTOR_BASIS` carried a comment claiming a wider basis converts nothing and only adds ambiguity; `basis_sweep()` offers **every** quantity the physics register holds and measures what each would do — of **713** candidates, **571** change nothing, **125** would make an attribution ambiguous and are refused, and the **17** that strictly convert more occupy only **four dimensions**, two of which decide the same triple, so the data decides **three** factors. The basis is 13 → **16** and `related_to` conversion 15 → **27** of 66 (6 `same_dimension_as`, 21 `differs_by`), residue 51 → **39**, of which exactly one is declined for having no single basis factor. **The comparative.** *Hotter than* and *as hot as* are a relation between two **uses**, not two words, which is why no reading of the concepts alone can answer one. `comparative` is a query kind of its own, recognised structurally rather than by keyword, refusing across quantities, on an unmeasured use and on a word at the exact midpoint of its scale. Measured: of the 56 uses, **228 pairs** are comparable; within one class the word order decides **24 of 24** and across classes it gets **151 of 204** backwards — `is cold in stellar_surface hotter than hot in tea` is **yes**, 8000 K against 363 K. `RequestProject/GLM/Comparative.lean` is the machine-checked half: `hotterThan_trichotomy`, `hotterThan_iff_position_lt`, `comparative_not_determined_by_word_order`, `comparative_not_static`, `hotterThan_congr` and the two forced refusals. **The reconciliation.** `RELATIVE_MEASURE_STUDY.md`, `MASTER_PLAN.md` (Phases 16 and 18), `STATUS.md`, `CAPABILITY_ASSESSMENT.md`, `DOCUMENTS.md` and the package, data-objects, reasoning, runtime, tests and Lean READMEs were re-measured against the code rather than patched, and the suite totals were re-earned by a release run after the stale ones were discarded. Measured after the edits: **2,631 tests across 58 test files, 11,901 subtests, zero failures**; **123 / 123** CLI cases (108 answered, 15 refused as expected, every refusal a `boundary`, 0 gap); 2,389 / 2,390 benchmark tasks; 33 probes (20 hold, 13 break); `lake build` clean over **43** Lean files, 11,426 lines, no `sorry`, repository and overlay copies identical; `FIGURES.md` matching a fresh computation, and all 58 test files and all 7 instruments carrying a signature that still holds with the exhaustive cases run (`--verify-release`). **Named for the next round:** `STATUS.md` §3.4 and `MASTER_PLAN.md` Phase 19 — the `related_to` residue finished as a vocabulary decision, and the recipe every capability follows made into an object. |
| 5.15 | 2026-08-31 | `glm_universal` **v1.10.0** — the `related_to` residue finished as a vocabulary decision rather than a search. *"`motion` reaches no dimension the register holds"* reports a lookup, not a fact about the word. **The search, exhausted first.** `basis_sweep()` offers every one of the **713** quantities the physics register holds and the factor basis did not: **571** change nothing, **125** would make an attribution ambiguous and are refused, and the **17** that strictly convert more occupy four dimensions, two of which decide the same triple — so the data decides three factors and the automatic half is finished. **The decisions.** `data_objects/denotation.py` decides the residue's **36** undimensioned endpoints one name at a time, each with its written justification, under six verdicts: 1 `quantity`, 3 `ambiguous`, 4 `polymorphic`, 9 `carrier`, 11 `process`, 8 `abstraction`. Only `quantity` makes a name dimensional and it supplies **no coordinate** — *gravity* is the register's own `gravitational_field` under an ordinary-language spelling — and `denotation_audit()` refuses an entry that names a quantity the register does not hold, shadows one it does, or carries no justification. **What the decisions changed, measured.** `reasoning/denotation_view.py` is the second pass: of the 39 declined triples, **0** convert, 6 are repaired to `names_process_of` and 33 are declined by a reason that names what the endpoint *is*; coverage is exact both ways (36 needed, 36 decided, 0 undecided, 0 idle) and `closure()` reports **39 of 39 accounted for, 0 waiting on a lookup**. Zero conversions is the result rather than a disappointment: deciding what a word denotes is not a way of manufacturing relations. The repairs carry — of the **22** analogies the 27 converted triples license, **12** are answered against **1** for the unrepaired control. `RequestProject/GLM/Denotation.lean` states the part that is not a measurement: `reach_invents_nothing`, `secondPass_eq_firstPass_of_decided`, `secondPass_eq_firstPass_of_no_quantity_verdict`, `undecided_is_decided` and `repaired_not_converted`, with *gravity*, *motion* and *move* instantiated. `report denotations` and [`studies/DENOTATION_STUDY.md`](../studies/DENOTATION_STUDY.md) are how it is read; [`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 19 is how it was built. **Named for the next round:** the recipe every capability follows made into an object. |
| 5.16 | 2026-08-31 | `glm_universal` **v1.11.0** — the recipe every capability follows, made into an object, and the claim tested by subtraction rather than by addition. **The description.** `recipe/spec.py` is a `DomainSpec`: what a domain's objects *hold*, one derivation per coordinate, the keys the object is recovered from, the named readings that make up its layer chain, and the coordinates it must decline. Nothing else — no carrier method, no codec, no audit — and every value an `int` or a `Fraction`. A coordinate is written in composable **primitives** (25 of them, 23 used, `held` in all three domains, 7 shared by two or more), and a rule a domain has to state for itself is marked `judgement(...)`, so *"this domain is described, not coded"* is a measurement: of **72** coordinates, **66** are shared derivations and **6** are judgements — the musical conventions (`euler_gradus`, `tet_step`, `tet_error`, `harmonic_index`, `subharmonic_index`, `is_comma`), all in one domain, while the brackets and the prices need none. **The one generic path.** `recipe/build.py` takes a description and produces the carrier encoding, the read-back audit, the readings as `Layer`s, the widening audit and the query surface with its refusal boundary, knowing nothing about any domain: **3 descriptions, 94 objects**, all 24-coordinate, read-back **94 / 94** with no two objects sharing a carrier, and 3 named refusals refused per domain. The comparison chain is the one that gains: **42 → 43 → 45** classes, splitting `room_volume` from `household_lamp` and then `ship` from `ocean_depth`; harmonics and economics gain nothing, because a ratio and a price already separate every object those registers hold — reported, not asserted away. **The subtractive test.** Each domain is deleted and rebuilt from its description alone: **94 / 94 carriers identical**, the objects agree, and **9 figures** the reasoning modules measure come back unchanged (11 with the two exhaustive ones) — verdict `regenerated`, **3 of 3**. **The surface.** `derive <coordinate> of <object>` is one query kind answered off whichever description derives the coordinate (`derive span_ratio of tea` → `373/293`; `derive euler_gradus of perfect_fifth` → `4`, reported as a judgement), with two different refusals — a coordinate no description derives, and an object no register holds. **The part that is not a measurement.** `RequestProject/GLM/Recipe.lean` states the path itself: `Spec.readingOn` generates a reading as a `Layer`, `readingOn_mono` and `readingOn_append_least` that widening gives nothing up and adds nothing beyond keeping both, `boundary_readingOn_nonempty_iff` that what a widening gains is exactly a conflated pair a new coordinate splits, `lossless_readingOn_iff` / `encode_injective_of_keys` / `rebuild_encode` for the read-back, `answer_eq_none_iff` for the refusal boundary, and `encode_congr` / `indist_congr` / `answer_congr` — regeneration itself, stated formally — with `ratioSpec` instantiating all of it. `report recipe` and [`studies/RECIPE_STUDY.md`](../studies/RECIPE_STUDY.md) are how it is read; [`MASTER_PLAN.md`](../MASTER_PLAN.md) Phase 20 is how it was built. Whole suite 2,746 tests across 60 test files, 12,508 subtests, zero failures; 45 Lean files, `lake build` clean, no `sorry`; evaluation **129 / 129**. **Named for the next round:** the surface language driven off the descriptions. |
| 5.17 | 2026-08-31 | `glm_universal` **v1.12.0** — the question every capability answers, made into an object, and the report solvers split out of the session. `language/` is the eleventh sub-package: `question.py` (a `QuestionSpec` — an opening, named slots with roles, the literal phrasings that separate them, an optional tail and the named boundaries the shape must refuse at, every set of alternatives carrying the sentence that justifies treating it as one set), `descriptions.py` (three shapes and no code), `build.py` (one generic matcher, the generated corpus and the audits) and `report.py`, wired as `report language`. Described: `derive`, `measure` and `task` — 3 of the 20 answerable query kinds, in 6 slots and 44 surface forms at 6 judgements, with 14 openings and 5 named refusal boundaries, measured against the parser they restate rather than asserted. Beside it, every `report` subject moved out of `runtime/session.py` into one module per family under `runtime/reports/`, with tests that make the split a property of the tree rather than a tidy-up the next round undoes. |
| 5.18 | 2026-08-31 | `glm_universal` **v1.13.0** — the question shapes put in place of the branches, and a second shape family measured. The three hand-written branches for `derive`, `measure` and `task` are deleted and `parse_query` dispatches those kinds through their descriptions; a described **preamble** — the courtesies in a loop and at most one interrogative — is what let them go, and describing it is a narrowing measured by 15 witnesses. The deleted code is frozen verbatim in `language/legacy.py`, imported by the measurement and by nothing in the runtime. `language/infix.py` is the second family: an operator that cuts a *string*, describing `verify`, `analogy` and the relational half of `compare` in 8 operands and 34 surface forms at 9 judgements. Measured: 846/846 slot questions agree with the deleted branches and round-trip, 174/174 infix questions agree with the parser they had not yet replaced, and questions of other kinds are declined rather than misread. Coverage 6 of 20 across 2 families. What was not done was named rather than implied: `language.build.UNDESCRIBED_PARTS` listed the four parts still hand-written. |
| 5.19 | 2026-09-02 | `glm_universal` **v1.14.0** — the last four hand-written branches deleted, and the quantiser's search replaced by a lookup. **Part 1 — the four undescribed parts.** A **list** (a slot whose filling is a sequence, cut at described separators held in two ranks), a **modifier** (a word that directs how the operands are read without naming one, removed at the head and in the trailing frame and *nowhere else*), described **trailing options** and a **nested** shape (an operator whose sides are themselves a shape, tightened) are description language now, so the equation, the analogy operator, both comparison forms and the comparative lose their branches to `language/legacy.py`. `compare` needed no new family — given a list slot it is a fourth slot shape — so the picture is 4 slot shapes, 3 infix shapes and 1 nested shape: **7 of 20 answerable query kinds across 3 families**, every one read off its description by the runtime, at 15, 13 and 4 judgements, with 947/947, 201/201 and 480/628 agreement against the frozen branches, 20 narrowing witnesses, and one declared widening (148 comparatives written with `relative to`) accounted for with 0 left over. `RequestProject/GLM/QuestionNested.lean` proves the list cut, the modifier frame at the head and the tail but not in the middle, and the nested shape's round trip and its two refusals. **Part 2 — the `O(1)` LLVQ table**, the oldest item on the original brief. `reasoning/llvq_table.py` reads the Golay code off the MOG: the six GF(4) column labels form a hexacode word, the six column parities agree and the top row carries that parity — checked over all 4,096 codewords — so the code is 128 classes of 32, and `(label, parity, top bit)` fixes a column's pattern, which is the whole table at 16 entries. The class minimum is a six-term min-sum under one parity constraint and the bounded search is exact, both proved in `RequestProject/GLM/LLVQTable.lean` (`isLeast_cost_of_parity_eq`, `isLeast_cost_of_parity_ne`, `card_parity_class`, `isLeast_of_bounded_search`). `lean_address.quantise` decodes through the table and the scan stays in `analogy.py` as the thing to agree with: 1,270 corpus addresses decoded both ways, 0 changed, and 107 vectors agreeing point for point. The claim is stated as constant-bounded rather than constant — 96.8 codeword costs per call against the scan's 8,192, worst case the whole code. New: the `report llvq` subject (48 subjects), `tests/test_llvq_table.py`, an evaluation case (131 cases, 131/131) and `studies/LLVQ_TABLE_STUDY.md`. |
| 5.20 | 2026-09-03 | `glm_universal` **v1.15.0** — the supplied archive, read to the end. The parts of `source_material/GLM-main.zip` the brief named were gone through script by script and everything in them that could be stated as a theorem was retrieved as Lean: **25 files, 7,170 lines, 848 declarations**, building with no `sorry` and mirrored in `glm_lean/` — the MOG cube (`Cube/`: the surface identification and its weight enumerator, the hexacode tiling, the stabiliser test, the price list with covering radius exactly 4, the three-cube proposal), the lattice shortcut (`Shortcut/`, eight files: the Golay code, a complete decoder, the Gray layer's `O(1)` jump formula, the Leech octad step, the corrected pipeline and two audits of the published directory), the three generations of the paper's formal companion (`Foundations.lean`, `Gen2.lean`, `Gen3.lean`), the electromagnetic calibration (`Calibration.lean`, `AlignmentPoints.lean`), the first-principles sub-study (`FitCapacity.lean`, `Packing.lean`, `Triad.lean`), the projection sub-study (`SeedLayers.lean`), the graded cost model (`StepCost.lean`), spatial arithmetic (`SpatialArithmetic.lean`) and the ARC-era reasoning loop (`ReasoningLoop.lean`). **Nine of the twenty-five are negative results** — the calibration chain returns the `c` it was given, `3, 6, 9` is produced by any three-element set, the forced number is 23 rather than 24, the three-cube rules give a `[24,12,4]` code no relabelling repairs, the published directory's "even quantisation" is true by construction, `snap_to_codeword` is not a decoder, consecutive integers are never a "geodesic jump", the electron-mass point is off by 0.0090–0.0093 % rather than 0.007 %, and `FitCapacity.lean` prices such agreements at all. The Lean corpus went from 1,270 declarations across 48 files to **2,118 across 73**, so the address book was rebuilt and `studies/LEAN_ADDRESS_STUDY.md` re-measured: the separation signal rose to 13.2 times chance on the file test and 15.0 on the citation test. Nothing the system answers moved — **131 / 131** end to end with the same 16 boundary refusals. New: `tests/test_retrieved_lean.py` (**63 test files**) and `studies/RETRIEVED_LEAN_STUDY.md`. |
| 5.21 | 2026-09-04 | The work dropped from the delivered tree, restored, and the archive's second reading closed. The tree handed over at the end of the previous round was missing part of what that round had produced — Lean files, their test files and several study documents — and `dropped.zip` at the repository root is what came back. Everything in it has been put back and **re-verified from the substrate rather than trusted**: every figure its tests pin is recomputed, and every Lean file builds against the pinned Mathlib with no `sorry`. With them the development stands at **95 Lean files, 27,548 lines, 2,764 declarations** against 73 files and 2,118 declarations before, and the two copies of the tree are byte-identical. The second reading of the archive is the eight results of `studies/SOURCE_SALVAGE_SECOND_PASS.md` — the cube surface as the MOG grid, the read quantum as an operator, the Gray jump norm, the ARC grid metrics as interval bounds (`GridTension.lean`), the conditional lobe, the mode algebra, the free cube symmetries (`Cube/Stabiliser.lean`) and the parity count that caps them at 24 (`Golay/CubeMirror.lean`, the one Lean file written new rather than restored); the two questions the first reading left open are answered no in `studies/ARCHIVE_DEEP_DIVE_STUDY.md` (`TriadChance.lean`, `Relaxation.lean`), and the archive's search loop, its XOR combiner, the address stability radius and the nearest-point tie-break are `SearchLoop.lean`, `Combiner.lean`, `Stability.lean` and `TieBreak.lean`. Three study documents could not be restored and were written from the code instead: `studies/SOURCE_SALVAGE_AUDIT.md`, `studies/SOURCE_SALVAGE_SECOND_PASS.md` and `studies/ARCHIVE_DEEP_DIVE_STUDY.md`. The exactness clean-up is finished and enforced by a machine-checked inventory (`reasoning/exactness.py`, `tests/test_exactness.py`): every site where a float could be constructed and every digest taken is declared, and an undeclared site — or a declared one that has gone — fails the suite. `studies/GLM_Complete_Number_Theory_Evidence.md` is audited by a test that re-runs its generators and compares the paper's tables and transcript cell by cell. The address book was regenerated over the larger corpus and `studies/LEAN_ADDRESS_STUDY.md` re-measured rather than patched: **2,764 / 2,764 read back exactly, 0 coordinate errors**, 2,426 distinct addresses, nearest-by-address sharing a file **560 / 2,764** against 37 for the digest control and 23 for the seeded reshuffle, chance at `8878/636411`. New: nine test files (**72 test files**, 3,096 tests, 12,119 subtests), the `report searchloop` subject (**49 report subjects**) and its evaluation case (**132 CLI cases**, 132 / 132 with the same 16 boundary refusals); the reasoning package went from 49 modules to **57**. |
| 5.22 | 2026-09-04 | The address book made to do work, and the first loop. Two faculties the substrate had never been asked for, each measured against controls. **Retrieval** (`reasoning/retrieval.py`, `report retrieval`): the address book used as an index over the **2,826**-declaration Lean corpus, 202 stride-selected queries, chance in closed form. The address is a real index — hit@5 **51.5 %** against **6.9 %** chance, above the digest (3.5 %), the seeded reshuffle (6.9 %), the random ranking (5.9 %) and name search (34.2 %) — and is beaten decisively by a plain text control at **85.6 %** with 57.7 % precision@5. Two ablations locate the signal: the same features with no lattice score 51.0 %, and a lexical address 64.9 %, so the geometry transports the features faithfully and adds nothing to them. What it does earn is exactness: `RequestProject/GLM/Retrieval.lean` proves the completeness bound behind the shortlist, **144,075** measured pairs with **0** violations, and an empty shortlist is a proof of absence. **The loop** (`reasoning/controller.py`, `report controller`): propose–check–refuse over the ten EXT10 generators, with every returned plan re-verified end to end by `verifier.verify_expression_pair` — **100 %** under every scorer, by an instrument that did not build it. **127 of the register's 726** quantities are refused *with a proof* (`Controller.unreachable_of_invariant`) and no node expanded, and `Controller.beam_can_miss` is the decided witness that a width-one beam can miss a plan that exists. On the 24 reachable tasks the address scorer solves **18** against **8** unguided and **12** for a target-blind scorer — the substrate can steer — but the same distance without the lattice solves **17**, and at scale 1 the address scorer falls to exactly the no-guidance 8, as `Address.lean`'s read-back bound predicts. New: two Lean files (**97 Lean files**, 28,209 lines, 2,826 parsed declarations, no `sorry`), two test files (**74 test files**), two reasoning modules (**59 modules**), and the `report retrieval` and `report controller` subjects (**51 report subjects**) with their evaluation cases (**134 CLI cases**, 134 / 134 with the same 16 boundary refusals). Write-ups: `studies/ADDRESS_RETRIEVAL_STUDY.md` and `studies/CONTROLLER_STUDY.md`. |

============================================
GLM 3+ 21 August 2026
============================================

# GLM: Repository Audit and Unified Reasoner

Audit of the GLM project (`https://github.com/DigitalEuan/GLM.git`) and
construction of `glm_core`, a unified multi-domain reasoner with exact
arithmetic and full mathematical tracing.

## Status

**Step 1 complete** - repository audited, all six defects (D1-D6) empirically
confirmed by executing the repository's own code.

**Step 2 complete** - `glm_core` built and verified: 8 modules, 96/96
architectural checks passing, all four reasoning domains behind one Three
Column Thinking interface. See [Step 2](#step-2---the-unified-glm_core-engine)
below.

**Step 3 complete** - benchmarked across all four domains against external
ground truth. Physics 18/18 and 16/16, chemistry 13/13 reactions, 65/65 real
ARC tasks ingested, 19/19 symbolic checks, 9/9 TCT scripts executing and
matching. One hypothesis was **refuted**: geometric work does not predict bond
dissociation energy (r^2 = 0.0011). See
[Step 3](#step-3---multi-domain-benchmark) below.

**Step 5 complete** - three targeted enhancements built and re-benchmarked.
Bond-energy prediction went from r^2 = -0.19 to **0.813 under leave-one-out
cross-validation**; the legacy Golay coordinate permutation was derived and
verified, taking silent corruptions **65 -> 0**; the spatial hypothesis class
widened 8 -> 35 candidates but **did not improve the ARC score** - a negative
result, reported as such. 107 new tests pass, no regressions. See
[Step 5](#step-5---algorithmic-hardening) below.

**Step 4 complete** - every Step 3 boundary traced to its algebraic cause.
`glm_core/tracing.py` records exact derivations; four diagnoses came out of it,
including a positive control proving the chemistry failure is the encoding
rather than the task, and the discovery that the legacy and unified Golay
constructions are **different subspaces**. See
[Step 4](#step-4---mathematical-traces-and-failure-diagnostics) below.

## Running

`uv` is not on the default `PATH` in this session; it lives in `.uvbin/`.
This is why the previous iteration produced no results: the scripts were never
successfully executed.

```bash
cd /app/sandbox/session_20260820_113734_a0d8466bd805
export PATH="$PWD/.uvbin:$PATH"
uv run python workflow/00_static_scan.py          # AST/static census -> data/
uv run python workflow/01_subsystem_audit.py      # subsystem audit    -> results/
uv run python workflow/02_defect_verification.py  # defect probes      -> results/
```

Total runtime is roughly three minutes, dominated by subprocess-isolated
imports of repository modules that do substantial work at import time.

## Layout

| Path | Contents |
|---|---|
| `workflow/GLM/` | Cloned repository, commit `92b8bad` |
| `workflow/00_static_scan.py` | AST scan: syntax errors, imports, side effects |
| `workflow/01_subsystem_audit.py` | Five-subsystem audit and Golay reference code |
| `workflow/02_defect_verification.py` | Empirical probes for the six flagged defects |
| `workflow/probes/` | Generated probe scripts, one per defect (regenerated each run) |
| `data/static_scan.json` | Raw static scan output |
| `results/step1_subsystem_audit.{json,md}` | Subsystem audit |
| `results/step1_defect_verification.{json,md}` | Defect verification |
| `results/claims.json` | Claim ledger - every headline number with its source |
| `logs/` | Execution logs |

## Repository scope

549 Python files, 294,266 lines across ten subsystems. Three files fail to
parse. Representative modules import cleanly at rates from 1.00 (`glm_3.1`)
down to 0.083 (`arc_agi_17`), the latter because 33 files import `ubp_engine`,
a module present neither in the repository nor on PyPI.

## Architectural gap analysis

The repository is a sequence of architectural generations that were **added
alongside** one another rather than superseding one another. Nothing was
retired, so several generations of the same primitive coexist and are selected
by whichever directory happens to be on `sys.path`. This is the single
structural fact behind five of the six defects below.

| ID | Defect | Status | Key measurement |
|---|---|---|---|
| D1 | Two incompatible Buckingham-Pi solvers | confirmed | Pi group counts differ on 2 of 6 quantity sets |
| D2 | Golay decoding beyond the correction radius | confirmed, and refined | w=4 fails safe; **w=5 silently miscorrects** |
| D3 | Competing NRCI formulations | confirmed | 5 implementations, 3 distinct values, one input |
| D4 | Bond-energy scale incoherence | confirmed | unitless work, no conversion constant defined |
| D5 | Unseeded sampling in wall distance | confirmed | 3 distinct values from 12 identical calls |
| D6 | Knowledge-base ingestion contract broken | confirmed | `AttributeError` at module import |

Supporting census across the 549 files: **113** functions defining an
NRCI-named metric, **45** symmetry-TAX definitions, **15** Pi/nullspace
solvers, **142** Golay-related definitions, **241** bare `except:` handlers,
and **8** `random.*` call sites in modules that never set a seed.

### Where the review's framing was refined by measurement

Two findings differ from the review's description, in both directions:

**D2 is worse than described, and at a different error weight.** Review flagged
weight >= 4 as silent degradation. Measurement separates two distinct
behaviours. At weight 4 the decoder fails *safe*: the syndrome is never in the
weight-<=3 table, so the input is returned unchanged with `corrected=False` in
200/200 trials - loud, detectable, and the nearest codeword is genuinely
ambiguous there (mean 6.0 codewords tie, consistent with covering radius 4). At
weight 5 the decoder fails *silently*: the coset leader has weight <= 3, so the
lookup succeeds and a valid codeword is returned with `corrected=True` in
200/200 trials, but it is the wrong codeword in 200/200. Weight 5, not weight
4, is where corruption is reported to callers as success.

Separately, the repository has *already* addressed the weight-4 case: it
documents the limitation as its own audit item B8 and ships `nearest_codeword`
and `decode_complete`, which return a codeword in 200/200 weight-4 trials. The
remaining gap is that the legacy `snap_to_codeword` is still the routine the
rest of the codebase calls.

**D1's mechanism is not the one described.** Review attributed the divergence
to Gauss-Jordan rational nullspace versus Smith normal form. The measured cause
is the axis basis: `glm2` carries 11 exponent components (10 axes plus scale)
including a separate angle axis, while `glm` uses 7-axis SI. The two engines
share their vocabulary - 17 of 18 quantity names resolve in both - but assign
different dimensions to the same name. Torque and energy are distinct under
`glm2` and identical under `glm`, so `{torque, energy, angle}` yields 1 Pi group
versus 2, and `{action, angular_momentum}` yields 0 versus 1. The four sets
built only from mechanical L/M/T quantities agree. Whether an angle axis is
carried is a modelling choice, not a bug, but the two choices cannot both feed
one reasoner.

### The remaining four

**D3.** One fixed 24-bit vector of Hamming weight 12, pushed through every
loadable NRCI implementation, returns values spanning 0.211 to 0.748 - a spread
of 0.537 across 5 implementations, 3 of them distinct. Two of the five return
exact `Fraction` values with ~60-digit numerators; a third returns a float.
Neither the name nor the return type identifies which formulation was applied.

**D4.** `geometric_work()` returns pure counts (Hamming steps, NRCI-weighted
sums; `total_work: 12.0` on the seeded probe trajectory). The module mentions
kJ/mol but defines no Avogadro or joule conversion constant. The step to
physical energy is taken in a sibling module by
`predicted_bond_strength = and_nrci_val * bond_order_proxy * 1000`. The gap is
a missing dimensional conversion, not an arithmetic error.

**D5.** Twelve repeated calls to `_compute_wall_distance` on one fixed vector
returned `[5, 3, 3, 3, 7, 5, 5, 5, 5, 3, 7, 7]` - 3 distinct values. The method
samples 300 of 4,096 codewords (7.3% of the space) with unseeded `random`. The
exhaustive minimum distance for that vector is 3; the sampled call matched it
in 4 of 12 attempts. The metric is therefore both irreproducible and biased
upward, since sampling can only ever miss the true nearest codeword.

**D6.** `ubp_system_kb.json` stores 752 records as positional lists against a
declared 8-field schema (`_fields`), while `ubp_kb_loader.py` indexes them as
dicts. The module calls `load_kb()` at import, so it raises
`AttributeError: 'list' object has no attribute 'get'` before any consumer runs.
A working `kb_adapter.py` that handles the list schema is already present in the
same directory and imports cleanly - the remediation path exists.

## Corrections made to the audit itself

The audit's own reference Golay construction was wrong in the previous
iteration. A bordered quadratic-residue circulant was used, and it produced a
code with minimum weight **7**, i.e. not the Golay code. It has been replaced
by the extended cyclic [23,12] construction from the generator polynomial,
which is validated by exhaustive enumeration to `d = 8`. The reference now
recovers 200/200 at error weights 1-3, 25/200 at weight 4 and 0/200 at weight
5, matching the theoretical bounded-distance limit of `floor((8-1)/2) = 3`.
This is what makes the repository's own minimum weight of 8 a cross-validated
rather than a single-source claim.

## Evidence and limits

- Every figure in `results/` is **computed** in a single run (Tier 1), except
  the Golay minimum weight of 8, which is **cross-validated**: derived once by
  the repository's `GolayCodeEngine` and once by this audit's independent
  cyclic construction, which agree.
- The audit harness is seeded (`random.Random(20260820)`), so re-running
  reproduces the same trial draws. That is a property of the harness, not
  evidence that the audited code is deterministic - D5 shows it is not.
- The import smoke test covers up to 12 representative modules per subsystem,
  not all 549 files. Import success rates are estimates over that sample.
- D3 reports only implementations that could be **instantiated and called**; 5
  of the 113 NRCI definition sites cleared that bar. The true spread across all
  113 is unmeasured and is very unlikely to be smaller.
- D5 demonstrates non-determinism within one process. Cross-process variation
  was not separately measured.
- D4 executes `geometric_work()` and inspects constants; the end-to-end
  bond-energy pipeline was **not** run to completion, so no predicted energy in
  kJ/mol is reported here and the ~1e42 figure quoted in review is **not**
  confirmed by this audit.
- The census matches function names via AST; a function implementing one of
  these concepts under an unrelated name is not counted.
- Symmetry-TAX, Griess algebra, CRG, dual-warp classification and the Lean
  bindings were located and counted but **not** numerically validated.
- No repository defect has been fixed. This step characterises the codebase;
  remediation belongs to later steps.

---

# Step 2 - The unified `glm_core` engine

A standalone package that consolidates the four reasoning domains behind one
interface and remediates each Step 1 defect at the architectural level.

```bash
export PATH="$PWD/.uvbin:$PATH"
uv run python workflow/03_test_unified_core.py   # 96 checks, ~1 min
```

| Module | Role | Remediates |
|---|---|---|
| `glm_core/linear_algebra.py` | Exact RREF, nullspace, integer kernel, Smith normal form over Q and Z | D1 |
| `glm_core/dimensional.py` | Tagged dimensional bases (SI7 / EXT10), Buckingham Pi | D1 |
| `glm_core/golay.py` | [24,12,8] code, complete decoding, total coset table | D2, D5 |
| `glm_core/coherence.py` | One versioned NRCI and Symmetry TAX, exact | D3, D5 |
| `glm_core/chemistry.py` | 118-element ingestion, stoichiometry, labelled energy scale | D4, D6 |
| `glm_core/spatial.py` | Grids, D4 symmetry, simplicial faces, CRG | (drops `ubp_engine`) |
| `glm_core/tct.py` | Three Column Thinking across all four domains | - |

Package-level guarantees, checked by AST scan in the suite: **no `random`
import anywhere** (the audited tree had 8 unseeded call sites), **no
third-party import** (standard library only), and exact arithmetic
(`Fraction`/`int`) for every quantity that feeds a result - floats appear only
in `*_float` display fields.

## How each defect was closed

**D1 - divergent dimensional bases.** Rather than picking a winner, the basis
is now a required, explicit tag on every `Dimension` and every `PiResult`.
`Basis.SI7` treats angle as dimensionless (torque **is** energy);
`Basis.EXT10` carries angle, solid angle and information axes (torque is
**not** energy). Mixing bases raises. `DimensionalEngine.compare_bases()`
makes the Step 1 divergence a first-class diagnostic: for
`{torque, energy, angle}` it reports 2 groups under SI7 versus 1 under EXT10
and names the cause. Both answers are correct for their basis; what was wrong
before was that neither engine said which basis it used.

**D2 - Golay miscorrection.** The decoder is now complete (a total coset-leader
table over all 4096 syndromes) and returns a status rather than a boolean:
`CODEWORD`, `CORRECTED`, or `AMBIGUOUS_TIE`. Measured across error weights 0-7:
w<=3 always `CORRECTED` and always recovers the transmitted word; w=4 always
`AMBIGUOUS_TIE` with exactly 6 tied codewords, never silently resolved; and
**no success status ever returns a non-codeword** (0 occurrences).

One point of honesty, and it is the important one: the Step 2 brief asked for
`w>=5 -> UNCORRECTABLE`. **That is not achievable by any decoder for this
code, and this package does not pretend otherwise.** A weight-5 error produces
a received word bit-for-bit identical to one produced by a weight-3 error on a
different codeword; the two cases are information-theoretically
indistinguishable. The suite measures this directly - at w=5 the decoder
returns `CORRECTED` with the wrong codeword in 40 of 40 trials. What was fixed
is the *claim*: every result carries a `guarantee` string reading "correct if
at most 3 errors occurred", which is true, in place of the legacy
`corrected=True`, which was not.

**D3 - 113 competing NRCI definitions.** One definition, versioned
(`nrci-1.0.0`): `NRCI(v) = 1 - d(v, C) / 4`, exact `Fraction`, where d is the
distance to the Golay code and 4 is the covering radius. The normalisation is a
stated **convention**, not a derived result - the audited formulations were not
so much wrong as unlabelled, and the version constant is what fixes that.

**D5 - unseeded sampling.** The wall distance is an O(1) lookup in the complete
coset table, replacing the 300-of-4096 unseeded sample. 100 identical calls
return **1 distinct value**, variance exactly 0, and the value matches an
exhaustive minimum over all 4096 codewords. The audited version returned 3
distinct values in 12 calls.

**D6 - broken ingestion.** `KnowledgeBase` reads the `_fields` schema from the
file and zips it against each positional row, so the schema comes from the data
instead of being assumed. All **118** elements ingest, Z contiguous 1..118,
118 distinct 24-bit carriers. The 119th record is dropped for having no
parseable atomic number, and that drop is counted in the ingestion report
rather than passing silently.

**D4 - energy scale.** The dimensionless quantity and the physical one are now
separate and separately labelled. `geometric_work()` returns a dimensionless
count; `WORK_UNIT_KJ_PER_MOL = 190` is marked an empirical calibration anchor;
conversion is explicit and Avogadro's number is exact. Every estimate carries a
`basis` field recording that it rests on the fitted anchor.

## Two findings that the build surfaced

Both are reported rather than smoothed over, and both bear on later steps.

**No element carrier is a Golay codeword.** Of the 118 carriers, 0 are
codewords and 107 sit at the covering radius (NRCI = 0). Their Hamming weights
(8, 12, 16) coincide with Golay codeword weights, but the vectors themselves
are not in the code. The element encoding is therefore not Golay-aligned. This
is why the NRCI-weighted form of geometric work is degenerate for most pairs,
and why the energy conversion uses raw path length instead.

**The 190 kJ/mol anchor overshoots measured bond energies by 5.4x to 8.8x.**
Against CRC bond dissociation energies for 5 heteronuclear pairs, the mean
absolute error is 2745.6 kJ/mol. A further 4 homonuclear pairs (H-H, O-O, N-N,
C-C) are **undefined** under this work measure - identical carriers give a
zero-length trajectory - and return no energy rather than 0 kJ/mol, so a
non-result cannot be mistaken for a computed zero. The anchor is not fitted to
these data and this suite does not fit it; on the evidence, the carrier
encoding rather than the constant is the likely source of the discrepancy.

## Evidence and limits (Step 2)

- Every Step 2 number is **computed** in a single run (Tier 1), except the
  Golay minimum weight of 8, which is **cross-validated**: `glm_core/golay.py`
  builds the code from the cyclic generator polynomial and enumerates all 4096
  codewords, independently of the Step 1 reference in
  `workflow/01_subsystem_audit.py`, and the two agree.
- The Golay boundary table uses a deterministic enumeration - the first 40
  combinations of error positions per weight - not an exhaustive sweep of all
  error patterns at each weight.
- "0 silent miscorrections" is a statement about the module's **contract**, not
  a claim that weight-5 errors are detected. See D2 above.
- Element properties (Z, valence, tension, phase) are parsed from KB lexicon
  text by regular expression. They were checked for parseability; their
  chemical **correctness** was not verified against an external periodic table.
- The 24-bit carriers are taken from the knowledge base as given. Their format
  and distinctness are verified; that they encode any particular chemistry is
  not.
- No ARC-AGI task set was solved or scored. The spatial module's operations are
  verified against their own algebraic invariants only.
- `glm_core` does not import from the audited tree at runtime except to read
  the knowledge base JSON; no legacy module was modified, and the legacy call
  sites still using `snap_to_codeword` were **not** migrated.

---

# Step 3 - Multi-domain benchmark

```bash
export PATH="$PWD/.uvbin:$PATH"
uv run python workflow/04_multidomain_benchmark.py   # ~4 s
```

Full results in `results/step3_benchmark_results.json` and
`results/step3_benchmark_scorecard.md`. Each domain is scored against an
external or formal ground truth, not against the engine's own output.

| Domain | Metric | Result |
|---|---|---|
| Physics | Pi-group count vs textbook | **18/18** |
| Physics | Dimensional homogeneity (SI7) | **16/16** |
| Chemistry | Reaction balancing vs published coefficients | **13/13** |
| Chemistry | Work vs bond energy, r^2 | **0.0011** |
| Spatial | Real ARC tasks ingested | **65/65** |
| Spatial | ARC tasks solved (single-D4 class) | **1/65** |
| Symbolic | Exact-algebra checks | **19/19** |
| TCT | Column 3 executes and matches Column 2 | **9/9** |

## The headline result is a refutation

Step 2 reported that the 190 kJ/mol anchor overshoots measured bond energies
by 5-9x and suggested recalibrating it. Step 3 tested that suggestion properly,
against 24 tabulated bond dissociation energies, and it does not survive.

Least-squares refitting the scale factor drops the mean absolute error from
3019 to 110 kJ/mol - which looks like a fix until it is compared against the
right baseline. **Simply predicting the mean of the reference set gives an MAE
of 81 kJ/mol.** The refitted model is worse than a constant. The correlation
between dimensionless path length and bond energy is r = 0.033, r^2 = 0.0011.

So the anchor was never the problem. The dimensionless geometric work carries
essentially no information about bond dissociation energy, and **no choice of
calibration constant can rescue it**. This closes the question Step 2 left
open: the defect is in the carrier encoding, not in the constant. It is
consistent with the Step 2 finding that none of the 118 carriers is a Golay
codeword - the encoding is not capturing the chemistry it is supposed to.

Reported as a refutation rather than buried, because an in-sample refit
showing a 27x error reduction is exactly the kind of number that would look
like a success if the baseline were left out.

## A basis inconsistency the benchmark caught and fixed

Scoring dimensional homogeneity in EXT10 initially failed on `E = h f` while
`L = I omega` passed - an internal contradiction in the basis, not a fact
about physics. The cause was inconsistent angular bookkeeping: `frequency`
(cycles/s) carried no angle while `angular_velocity` (rad/s) did, though both
are angle per time.

Two corrections closed it, and both are now documented in
`glm_core/dimensional.py`:

- **A per-cycle convention.** Frequency carries `A=+1`; quantities defined per
  cycle - wavelength (metres per cycle), the Planck constant (joule-seconds
  per cycle) - carry `A=-1`.
- **Moment of inertia carries `A=-2`.** This is what makes `E = I omega^2` and
  `L = I omega = tau t` agree; assigning it `A=0` leaves the two definitions of
  angular momentum differing by `A^2`, the classic inconsistency of
  angle-as-a-dimension systems.

After the fix, all 16 laws are homogeneous in **both** bases, zero laws are
basis-sensitive, and EXT10 still separates torque from energy and angular
momentum from action while a negative control confirms it does **not**
over-separate cycle frequency from angular velocity. The visible cost is that
`f^2 L / g` is no longer dimensionless in EXT10, which is correct - the
pendulum relation holds for angular frequency.

## ARC-AGI: an honest floor

65 real training tasks from `arc_agi_17/data/training/` were ingested and the
spatial module was scored on whether it reproduces each held-out test output
exactly. Under a deliberately narrow hypothesis class - one global D4
operation, consistent across all training pairs - **1 of 65** tasks is solved,
at 1/1 precision within the class.

A synthetic control confirms the D4 detector itself finds all 8 operations, so
the low rate measures the hypothesis class, not a broken implementation. Most
ARC tasks need compositional reasoning far beyond a single rigid motion. This
is a floor for the spatial module, and it is reported rather than omitted.

## Evidence and limits (Step 3)

- All Step 3 numbers are **computed** in a single run (Tier 1), except the
  TCT Column 2 / Column 3 agreement, which is **cross-validated**: the value
  is computed once in-process and re-derived in a separate subprocess from the
  generated script.
- The refitted anchor is fitted on the same 16 pairs it is scored on. Its
  110 kJ/mol MAE is an optimistic **in-sample** figure with no held-out split;
  it is reported to bound what any constant could achieve, and it still loses
  to the baseline.
- Bond dissociation energies are standard tabulated **mean** values, not
  molecule-specific, so scatter against them is expected even for a good model.
- Physics ground truth is the textbook Pi-group count entered as a literal in
  the benchmark source. It encodes the standard result; it is not
  independently re-derived.
- The ARC figure is on 65 tasks from the repository's training directory. It
  is **not** the official ARC-AGI evaluation set and is not comparable to
  published ARC scores.
- Column 2 / Column 3 agreement requires the decisive value to appear in
  stdout. That is substantive but is not a full symbolic equivalence proof.
- Latency figures include interpreter startup per subprocess and do not
  measure engine speed.
- The legacy `snap_to_codeword` call sites were **not** migrated; no file under
  `workflow/GLM/` was modified in this step.

---

# Step 4 - Mathematical traces and failure diagnostics

```bash
export PATH="$PWD/.uvbin:$PATH"
uv run python workflow/05_mathematical_tracing.py   # ~10 s
```

`glm_core/tracing.py` adds four tracers that record intermediate algebra, not
just answers: `DimensionalTracer` (exponents, RREF, pivots, nullspace,
primitive kernel, with `A·k = 0` residuals recorded), `GolayTracer` (syndrome,
coset leaders, error bit positions, full distance profile to all 4096
codewords), `CoherenceTracer` (TAX term by term, NRCI with wall-distance
provenance) and `ConstructionATracer`. Full traces in
`results/step4_mathematical_traces.json`; the readable ledger is
`results/step4_failure_diagnostics.md`.

## The chemistry failure, finally pinned down

Step 3 refuted the bond-energy hypothesis but could not say whether the
encoding was at fault or the task was simply hard. Step 4 answers that with a
**positive control** - the same 22 bonds, regressed against standard chemical
descriptors:

| Predictor | r^2 | OLS in-sample MAE |
|---|---|---|
| Carrier path length | **0.0001** | 76.09 kJ/mol |
| Carrier Hamming distance | 0.0318 | 74.85 kJ/mol |
| Electronegativity difference | 0.5109 | 52.12 kJ/mol |
| Inverse bond length | 0.3303 | 55.45 kJ/mol |
| **Pauling's rule** | **0.8937** | **22.59 kJ/mol** |

Baseline (predict the mean): 76.18 kJ/mol. The carrier reaches 76.09 - it is
indistinguishable from a constant. Pauling's rule reaches r^2 = 0.89 on the
identical bonds. **The task is learnable; this encoding cannot learn it.**
Without this control, r^2 ~ 0 would have been ambiguous.

**And the encoding's structure is now exactly characterised.** The 118 carriers
have Hamming weights only on 8, 12 and 16 - precisely the Golay code's
non-trivial weights - so they were built to reproduce its weight enumerator.
They occupy just **64** distinct syndromes (vs ~116 expected under arbitrary
placement). Those 64 are **not** a linear subspace, but they **are a coset** of
one. The carrier set is a clean linear object uniformly displaced off the code.

Testing the obvious remediation shows it is insufficient: a single fixed XOR
offset takes 0 → 2 carriers into the code and mean wall distance 3.81 → 3.59.
One translation can send exactly one of the 64 syndrome classes to zero, so
only the carriers sharing that syndrome land in the code. Full alignment needs
a **redesign**, not a translation - and even a fully aligned encoding would not
help chemically, since XOR by a constant preserves every pairwise Hamming
distance and so cannot move any number in the table above.

## Legacy migration is a data migration, not a search-and-replace

279 legacy snap-style call sites remain, across 9 subsystems. Tracing the
legacy decoder against `glm_core` over a deterministic weight 0-7 sweep gives
**65 silent corruptions for the legacy decoder and 0 for the unified one**, and
locates the boundary precisely: weight 4 returns a non-codeword while flagging
`corrected=False` (detectable), weight 5 flags `corrected=True` and returns a
valid but wrong codeword (not detectable).

The more consequential finding is structural. The two implementations build
**different codes**:

| Property | Legacy | glm_core |
|---|---|---|
| Codewords | 4096 | 4096 |
| Weight distribution | identical | identical |
| Codewords in common | **8 of 4096** | |
| Same subspace | **No** | |

Both are valid [24,12,8] extended Golay codes with the same weight enumerator,
but they are different subspaces of GF(2)^24 - equivalent under a coordinate
permutation, not equal. So a call site **cannot** be migrated by swapping
`snap_to_codeword` for `decode_complete`: any 24-bit state persisted under the
legacy generator must also be mapped through the permutation relating the two
codes, or every stored vector silently changes meaning. This was invisible from
the call-site census alone and changes the shape of the migration task.

## A naming correction: Construction A is not the Leech lattice

The audited repository refers to "Leech lattice" coordinates while what is
directly constructible from the Golay code is Construction A,
`Lambda_A = { x in Z^24 : x mod 2 in C }`. These are not the same lattice:

| | Construction A | Leech |
|---|---|---|
| Minimum squared norm | 4 | 4 |
| Minimal vectors (kissing number) | **48** | **196560** |

Construction A admits the 48 vectors `(±2, 0, ..., 0)`, which the Leech lattice
excludes. Obtaining Leech requires Construction B plus a coordinate-sum
congruence that Construction A does not impose. Any invariant quoted as a Leech
property - the kissing number above all - does not follow from this
construction.

## ARC: all 65 tasks classified

Every task is now labelled with the narrowest transformation family a fixed
detector set can identify. 9 families; 1 single-D4 solvable, matching Step 3.

| Family | Tasks | | Family | Tasks |
|---|---|---|---|---|
| `same_shape_palette_subset` | 18 | | `inconsistent_across_pairs` | 6 |
| `same_shape_palette_extended` | 15 | | `same_shape_rearrangement` | 3 |
| `shape_expansion_other` | 9 | | `crop_subgrid` | 3 |
| `shape_reduction_other` | 9 | | `d4:flipud` | 1 |
| | | | `upscale_varying_parameter` | 1 |

The `*_other`, `*_subset`, `*_extended` and `inconsistent` labels are residual:
they record that **no detector matched**, so those 48 tasks are unexplained
rather than explained. That is the honest reading, and the table is the
work-list for widening the hypothesis class.

## Electromagnetic closure

Step 3's per-cycle convention was validated only on mechanics. Extending to 15
electromagnetic and electrodynamic relations (Faraday, capacitive and inductive
energy, `c^2 = 1/(eps mu)`, and others): **15/15 homogeneous in both bases, 0
basis-sensitive**. The EM quantities carry no angular exponent, so the
convention neither helps nor harms them - confirming it is correctly confined
to the rotational and wave sectors.

## Evidence and limits (Step 4)

- All values **computed** in a single run (Tier 1), except the carrier
  path-length r^2, which is **cross-validated**: re-derived here on 22 bonds
  against Step 3's 16, both giving r^2 ~ 0.
- Traced quantities are exact `Fraction`/`int`. The correlations in the
  chemistry section are computed in floating point because the reference
  chemical data are themselves decimal measurements.
- The regression fits are **in-sample** with no held-out split. They bound what
  each predictor could achieve; the comparison between them is the point, not
  the absolute numbers.
- Chemical reference values (electronegativity, covalent radii, bond energies)
  are standard tabulated means entered as literals, not re-derived. Mean BDEs
  are not molecule-specific.
- The ARC classifier reports the narrowest family its fixed detector set can
  find; residual labels mark absence of a match, not a positive finding.
- The CRG growth trace uses a lossy per-row parity projection - a structural
  probe, not evidence that grid rows are meaningful lattice vectors.
- The legacy sweep uses the first 30 error-position combinations per weight
  against one base codeword per code. Deterministic, but not exhaustive.
- The 196560 Leech kissing number is quoted from the literature; Construction
  A's 48 is derived here from the construction and the code's weight
  enumerator.
- **No file under `workflow/GLM/` was modified.** Legacy call sites are counted
  and characterised, not migrated.
- Step 2 (96/96) and Step 3 were re-run after these changes: no regressions.
  The Step 2 module-set assertion was updated for the new `tracing.py` module -
  it correctly caught the addition.

---

# Step 5 - Algorithmic hardening

```bash
export PATH="$PWD/.uvbin:$PATH"
uv run python workflow/06_remediation_benchmarks.py   # ~2 min
uv run pytest -q tests/test_step5_enhancements.py     # 107 tests
```

Three new modules act on Step 4's diagnoses: `glm_core/physical_carriers.py`,
`glm_core/isomorphism.py` and `glm_core/crg.py`, plus a hypothesis engine in
`glm_core/spatial.py` and legacy translation in `glm_core/golay.py`.

| Enhancement | Baseline | Enhanced |
|---|---|---|
| Bond energy, **LOOCV** r^2 | -0.193 | **0.813** |
| Bond energy, **LOOCV** MAE | 83.6 kJ/mol | **32.8 kJ/mol** |
| Carriers that are Golay codewords | 0 / 118 | **22 / 22** |
| Golay silent corruptions | 65 | **0** |
| Spatial hypothesis candidates | 8 | **35** (8 families) |
| ARC tasks solved | 1 / 65 | **1 / 65** |
| Physics Pi-group regression | 8/8 | 8/8 |

## Chemistry: the carrier redesign worked

Step 4 concluded the encoding had to be redesigned, not translated. Each
element is now four measured properties - Pauling electronegativity, covalent
radius, valence electrons, homonuclear bond energy - each quantised to 3 bits,
and the 12 resulting information bits are **Golay-encoded**. Two consequences
follow by construction: every carrier is a codeword (the alignment defect Step
4 found is closed), and a carrier corrupted by up to 3 bit flips still decodes
to the correct properties, which the legacy encoding could never do since its
vectors were not codewords at all.

Prediction is scored by **leave-one-out cross-validation** - a four-parameter
model on 22 bonds would otherwise flatter itself - and the regression is solved
exactly over Q with `Fraction`. LOOCV r^2 = **0.813**, MAE **32.8 kJ/mol**
against a predict-the-mean baseline of 76.2.

**What this does and does not show.** The gain comes from grounding the
encoding in measured chemistry. It is *not* lattice geometry discovering
chemistry and must not be read that way. The honest question answered is how
much predictive power survives quantisation to 24 bits, between two reference
points: the legacy carrier at r^2 ~ 0 below, and the continuous Pauling rule at
r^2 = 0.894 (Step 4) above. Most of it survives.

## Golay: the permutation was found, and it is the right kind of map

Step 4 showed the legacy and canonical codes share only 8 of 4096 codewords.
Step 5 derives the coordinate permutation relating them by searching the
Steiner system S(5,8,24) formed by each code's 759 octads, anchored on five
fixed points - legitimate because M24 is 5-transitive, so if any isomorphism
exists then one exists fixing five coordinates.

```
LEGACY_TO_CORE = (0,1,2,3,4,5,7,16,8,19,22,9,13,12,10,18,14,15,21,6,11,20,23,17)
```

Verified exhaustively over all 4096 codewords of each code: bijective,
round-trip identity, and **weight preserving**. That last property is the one
that matters. `glm_core/isomorphism.py` also builds a general linear
isomorphism, which maps the code onto the code but **scrambles Hamming
distance** and therefore cannot be wrapped around a decoder - it is retained
only for codeword translation, with that caveat attached in code. Only the
permutation commutes with decoding.

`decode_legacy()` uses it to route legacy words through the audited-correct
decoder: over the same weight 0-7 sweep, silent corruptions go from **65 to 0**.

## Spatial: a negative result

The hypothesis class was widened from 8 candidates (single global D4) to 35
across 8 families - colour permutation, D4 composed with colour permutation,
translation, bounding-box crop, integer upscaling, plain and alternating
tiling, component selection, compression, colour reduction, constant output.

**It did not improve the ARC score: 1/65 before, 1/65 after.** This misses the
Step 5 target of a measurable increase, and is reported without adjustment.

Synthetic capability controls confirm the engine really does solve the families
it added (6/6 controls, against 2/6 for the D4-only baseline), so the ceiling is
the corpus rather than the implementation. Step 4's classification is the
explanation: 33 of 65 tasks sit in the residual `palette_subset` /
`palette_extended` classes needing object-level compositional reasoning, and
none of the added families expresses that. Widening along the rigid-motion axis
was simply the wrong axis for this corpus - which is useful to know, and is
what the classification was for.

`glm_core/crg.py` does add real machinery here regardless: connected
components, component adjacency graphs, simplicial triangles, cycle rank, and
Euler characteristic as an exact hole count, all verified invariant under D4.

## Evidence and limits (Step 5)

- All values **computed** in a single run (Tier 1), except the Golay
  permutation's losslessness, which is **cross-validated**: derived by the
  Steiner search in `isomorphism.py` and independently re-verified in the
  benchmark against the legacy engine's own codeword set.
- Chemistry figures are **leave-one-out**, not in-sample. The quantisation
  edges and level midpoints were fixed before fitting and not tuned against the
  bond targets - but they were chosen by the same author as the model, so this
  is not a blind protocol.
- The 22 bonds carry tabulated **mean** dissociation energies, not
  molecule-specific values, so some residual scatter is irreducible.
- The corrupted-word sweep uses the first 30 error-position combinations per
  weight against one base codeword. Deterministic, not exhaustive.
- The spatial capability controls are synthetic tasks built by the same code
  paths the engine searches; they demonstrate wiring, not generalisation.
- The ARC corpus is 65 repository training tasks, not the official ARC-AGI
  evaluation set.
- **No file under `workflow/GLM/` was modified.** The 279 legacy call sites
  remain unmigrated; what Step 5 adds is the verified translation layer that
  would make migrating them correct.
- Two runs of the benchmark are byte-identical after stripping timestamps.

## Next steps

1. **Migrate the 279 legacy call sites** using `decode_legacy` and the verified
   permutation. The blocker Step 4 identified is now removed.
2. **Attack ARC along the right axis**: object-level and compositional rules
   for the 33 `palette_subset` / `palette_extended` tasks. Rigid motions are
   exhausted.
3. **Validate the carrier model out of family** - the current LOOCV is over 22
   bonds from one tabulation; a held-out set from a different source would test
   whether the quantisation generalises.
4. **Extend physical carriers to all 118 elements**; only 22 have the full
   property set tabulated here.

---
---

# GLM-3+ · Step 1 — `glm_universal` substrate and MOG-cube engine

A new plan begins here. The five steps above audited and remediated the
existing GLM repository; what follows is the **Universal MOG-Cube Geometric
Language Machine (`GLM-3+`)**, a clean re-founding in a self-contained package
`glm_universal/`. Step 1 builds the substrate: the algebraic, geometric and
Monster-group foundation everything else will be indexed by.

## What was built

```
glm_universal/
├── README.md              architecture, mathematical principles, provenance
├── __init__.py
├── substrate/
│   ├── README.md          per-module contracts and known limits
│   ├── linalg.py      203  exact integer / F_2 linear algebra
│   ├── mog.py         616  Golay code, hexacode, MOG trio, sextet, cubes
│   ├── leech2.py      621  Leech lattice, Λ/2Λ, Witt data, 2A axis detection
│   ├── digit_stack.py 621  10-plane 2-adic stack, facet attribution
│   └── __init__.py     80
├── data_objects/README.md  reserved — empty scaffold, contract only
├── reasoning/README.md     reserved — empty scaffold, contract only
├── benchmarks/README.md    reserved — empty scaffold, contract only
└── tests/test_substrate.py 735  73 test functions, 96 cases with parametrics
```

Dependency direction is strictly downward, `linalg → mog → leech2 →
digit_stack`, with no import cycle. The package imports **only** the Python
standard library and does not depend on `glm_core` or on anything under
`workflow/GLM/`.

## What the substrate computes

Every number below was produced by
`workflow/07_step1_substrate_verification.py` in this run and is readable back
from `results/step1_substrate_verification.json`.

| Fact | Computed | How |
|---|---|---|
| Golay codewords / octads | 4096 / 759 | enumerated from `G = [I₁₂ \| B]` |
| Weight enumerator | 1 + 759z⁸ + 2576z¹² + 759z¹⁶ + z²⁴ | enumerated |
| Hexacode alignment | 0 failures / 4096 codewords | exhaustive shadow check |
| MOG trio | 3 disjoint octads covering all 24 | validated at import |
| MOG sextet | 6 tetrads, all 15 pairs are octads | validated at import |
| Trios in the code | 3795 | exhaustive octad-pair search |
| Leech basis determinant | 2³⁶ = [Z²⁴ : Λ] | HNF of a checked generating set |
| Witt decomposition of Λ/2Λ | 12 planes, plus type | symplectic Gram-Schmidt |
| Singular classes | 8,390,656 = 2²³ + 2¹¹ | closed form from the Witt data |
| Theta series | 1, 0, 196560, 16773120, 398034000 | `E₄³ − 720Δ`, exact integers |
| Class census | 1 + 98,280 + 8,386,560 + 8,292,375 = 2²⁴ | closes exactly |
| **Type-2 (2A axis) classes** | **98,280** | all 196,560 minimal vectors reduced mod 2Λ |
| Co₀ pair census | {4: 2, 2: 9200, 1: 94208, 0: 93150} | 196,560 inner products |

The type-2 count is the one result that arrived by **two independent paths in
this session**: exhaustive enumeration of the minimal vectors (each class hit
exactly twice, asserted) and the theta coefficient `N(32)/2`. They agree.

## The three headline capabilities

**2A axis detection.** `is_2a_axis(point)` reduces a lattice point mod 2Λ and
looks the class up in the exhaustively enumerated 98,280-class table. Because
the enumeration is complete, a *negative* answer is as much a proof as a
positive one. Controls in this run: 2000/2000 minimal vectors detected as
axes, 200/200 doubled vectors correctly rejected, 200/200 verdicts unchanged
under adding 2·(a lattice point), the origin correctly rejected.

**MOG trio and sextet geometry.** One fixed labelling of the 24 coordinates as
a 4×6 frame makes the six columns a sextet and the three 4×2 bricks a trio of
octads. Bijective reshaping between the linear 24-vector and its 4×6 and 3×8
presentations round-trips for any payload — bits, integers, `Fraction`s,
strings — because it is a pure permutation of positions.

**Lossless 10-plane reconstruction.** `class_stack_rebuild(class_stack(v)) ==
v` held exactly across **366 round trips** in this run, over integer carriers,
rational carriers with mixed denominators, out-of-range rationals at derived
depths, and genuine Leech points in both the standard and Leech bases, each at
the default `(offset 512, depth 10)` pair and at two deeper admissible pairs.
Rational carriers are cleared by their least common denominator, which travels
in the stack and is reapplied on rebuild; no float is constructed at any step.

## Failing-facet attribution — new in this port

The reference implementation could say an equation failed. This one says
*where*. `verify_equation(lhs, rhs)` compares the two stacks plane by plane and
attributes each discrepancy to the MOG facets containing it — 31 named
subsets: 3 trio bricks, 6 sextet tetrads, 4 frame rows, 18 cube faces.

Worked example from this run: perturbing the single coordinate at cube address
`(brick 2, x 1, y 0, z 1)` by +1 produced

```
holds            : false
failing planes   : [0, 1]
difference mask  : 0x002000  (identical at both planes)
blamed facets    : brick2, col5, row1, cube2.x1, cube2.y0, cube2.z1
```

which is exactly the six facets that contain that coordinate, and no others.

## Why ten planes — Proposition D1

"Ten" is not a magic number, it is a measurement. If the offset `O ≥ max_abs`
and the depth `D` satisfies `2^D > O + max_abs`, then every shifted coordinate
lies in `[0, 2^D)` and reassembly is the identity. `derive_stack_parameters`
returns the least admissible pair for any range; `depth_report` confirmed in
this run that reconstruction is exact at every admissible pair tried, that
planes above the least admissible depth are identically zero, and that the
planes below it do not move. The defaults `2⁹`/10 are the least admissible pair
for `|c| ≤ 511`. The bound is two-sided and so conservative: `−512` encodes
fine, but a dataset reaching `|c| = 512` derives depth 11. That asymmetry is
asserted in a test so a later change to the formula cannot pass silently.

## Design invariants, enforced by tests rather than intended

| Invariant | Enforced by |
|---|---|
| Exact arithmetic only (`int`, `Fraction`) | `class_stack` raises `TypeError` on a float |
| No randomness anywhere in the package | AST scan of every substrate module for a `random` import |
| Standard library only | AST scan of every module's imports against an allow-list |
| Deterministic | reports compared for equality across repeated calls |

Test fixtures needing "arbitrary" vectors use an explicit seeded LCG written
out in the test file, so every input is a literal function of its seed.

## Corrections made during the port

* The reference audit checked the Leech basis for **unimodularity**, which is
  false in the ×√8 integer model. Corrected to the index `[Z²⁴ : Λ] = 2³⁶`,
  which is what the determinant actually equals and what the test now asserts.
* Type-2 detection no longer routes through the lattice decoder. Removing the
  decoder from the trusted base means an axis claim rests only on an
  exhaustive, self-validating enumeration.
* The digit stack is generalised from integer lattice points to arbitrary
  carriers over Q.

## Commands run

```bash
uv run pytest glm_universal/tests/test_substrate.py -q
uv run python workflow/07_step1_substrate_verification.py
```

## Output files

| Path | Contents |
|---|---|
| `glm_universal/` | the package (see tree above) |
| `workflow/07_step1_substrate_verification.py` | the verification driver |
| `results/step1_substrate_verification.json` | every recomputed fact, the reconstruction sweep, the depth report, the facet demonstration, the pytest summary, and the nine success-criteria booleans |
| `results/claims.json` | eight `glm3plus_substrate_*` claims merged in by id |

## Evidence and limits (GLM-3+ Step 1)

**Checked, and at which tier.**

- *Cross-validated (two independent paths in this session):* the 98,280
  type-2 class count — exhaustive reduction of all 196,560 minimal vectors
  versus the theta coefficient `N(32)/2` from `E₄³ − 720Δ`. Also the
  8,390,656 singular-class count — closed form from the Witt decomposition
  versus the theta-series census `1 + 98,280 + 8,292,375`.
- *Computed (single run, this session):* every other number in the tables
  above. All are readable back from
  `results/step1_substrate_verification.json`.
- *Checked against file:* the nine success-criteria booleans and the pytest
  summary line were re-read from the written JSON after the run.

**Not checked.**

- **The pipeline was not re-run end to end from a clean process to confirm
  byte-identical output.** Determinism is argued from the absence of any RNG
  import (AST-scanned) and from repeated-call equality of the report
  functions, not from a full replication.
- **`is_2a_axis` positive controls covered 2000 of the 196,560 minimal
  vectors**, not all of them; the 98,280-class table itself is exhaustive and
  self-validating, but the detection wrapper was spot-checked.
- **No Leech decoder is implemented.** Types 3 and 4 of an arbitrary class are
  not computed pointwise — only their counts appear, from the theta series.
  There is no `type_of_point`. A later step needing per-class type 3/4
  resolution must add one.
- **One alignment only.** `ALIGNED_BITS` fixes a single labelling of the 24
  coordinates, and every trio, sextet and facet name is relative to it. M₂₄ is
  not implemented, so there is no way yet to move between alignments, and no
  claim here is invariant-under-M₂₄.
- **Facet attribution is bit-level, not semantic.** It localises *where* two
  carriers differ in the MOG geometry; it says nothing about why.
- **`data_objects/`, `reasoning/` and `benchmarks/` are empty scaffolds.** They
  contain a README stating a contract and no code. Nothing in this step
  exercises them.
- The GPU on this instance was **not used and is not applicable**: the
  substrate is exact integer and `Fraction` arithmetic, where floating-point
  acceleration would forfeit the exactness the whole layer rests on. The full
  verification takes 30 seconds on one core.

## Next steps (after GLM-3+ Step 1)

1. **Step 2 — `data_objects/`**: typed carriers wrapping real data as
   substrate points, with round-trip tests as the acceptance criterion.
   *(Completed — see below.)*
2. **Add a Leech decoder** to `substrate/leech2.py` if per-class type 3/4
   resolution is needed; it is the one gap in the current type theory.
3. **Implement M₂₄** so that trio, sextet and facet statements can be made
   alignment-independent.
4. **Persist the 98,280-class table** to `data/` if a 5-second cold start per
   process becomes a bottleneck; it is currently rebuilt per process.

---

# GLM-3+ · Step 2 — `data_objects` universal multi-domain carrier engine

Four domains, one carrier shape. Every object is a point of **Q²⁴** with an
exact 2-adic digit stack fitted to it. Full submodule documentation lives in
`glm_universal/data_objects/README.md`; the numbers below were computed by
`workflow/08_step2_data_objects_verification.py` and are in
`results/step2_data_objects_verification.json`.

## The losslessness contract has two legs

A codec is lossless only if **both** hold:

| Leg | Statement | Whose property |
|---|---|---|
| substrate | `class_stack_rebuild(class_stack(v)) == v` | the digit stack |
| semantic | `decode(encode(x)) == x` | the codec |

The first can hold while the second fails — a codec that drops a field still
produces a perfectly faithful stack *of the truncated carrier*. Checking only
the substrate leg would make the losslessness claim vacuous, so both are
asserted separately for every object.

| Domain | Objects | Substrate leg | Semantic leg |
|---|---|---|---|
| physics | 660 | 660/660 | 660/660 |
| chemistry | 118 | 118/118 | 118/118 |
| mathematics | 22 | 22/22 | 22/22 |
| lexicon | 10 | 10/10 | 10/10 |

## Dynamic stack depth is load-bearing, not decorative

The module default `STACK_DEPTH = 10` is **not** used on the codec path and
would fail on every element. Depth is derived per carrier from its actual
coordinate range, with no ceiling:

| Carrier | Denominator | Depth |
|---|---|---|
| physics register (660 concepts) | ≤ 2 | 2–7 |
| element register (118 elements) | ≤ 25,000,000 | **24–41** |
| hydrogen (density drives it) | 25,000,000 | 39 |
| 10⁴⁰ in one coordinate | 1 | **134** |
| 10²⁵ and 10⁻²⁵ together | 10²⁵ | **168** |

Each depth was checked to be the *least* admissible: one plane fewer raises.

## Three results worth stating

**EXT10 resolves 3,018 concept pairs that SI7 cannot.** Over the 660-concept
register, SI7 leaves 14,245 dimensionally colliding pairs and EXT10 leaves
11,227. Sixty concepts carry a nonzero plane-angle, solid-angle or information
exponent — exactly the ones the SI projection loses. Torque (`L² M T⁻² A⁻¹`)
and energy (`L² M T⁻²`) are the canonical pair.

**The periodic table inherits an error-correcting separation.** Mapping *z* to
a Golay codeword gives 118 distinct addresses whose minimum pairwise Hamming
separation over all 6,903 pairs is **8** — exactly the `[24,12,8]` code's
minimum distance.

**395 missing element attributes were restored as `None`, not as zeros.** In
the source, covalent radius is present for 24/118 elements and homonuclear BDE
for 21/118. Each absent field is coordinate `0` *and* has its bit set in the
missingness mask, so a measured zero and an absent measurement stay
distinguishable. Nothing was imputed.

## Commands run

```bash
uv run python workflow/08a_ingest_registers.py               # freeze sources
uv run python -m pytest glm_universal/tests -q               # 177 passed
uv run python workflow/08_step2_data_objects_verification.py # 12/12 criteria
```

Tests: **81 tests / 5,110 subtests passed, 0 failed, 0 skipped** for
`test_data_objects.py`; **177 passed** for the full package, confirming no
Step 1 regression.

## Evidence and limits (GLM-3+ Step 2)

**Checked, and at which tier.** All round-trip counts, stack depths, collision
figures and the Golay separation are **Tier 1 (computed)** — produced by a
single run of `workflow/08_step2_data_objects_verification.py` in this session
and read back from
`results/step2_data_objects_verification.json`. The test-suite summary lines
are the harness's own capture of `pytest` output, so the pass counts are
Tier 2 with respect to the JSON report.

**Not checked.**

- **No independent re-derivation.** Nothing here is cross-validated: there is
  one implementation and one run. A second implementation of the codecs was
  not written, so a shared-assumption bug would not have been caught.
- **Source data was ingested, not audited.** The 660-concept register and the
  PubChem periodic table were converted to exact rationals faithfully — the
  conversion is exact and tested — but the underlying *physical values* were
  taken on trust from the in-repo sources. No value was checked against an
  external authority in this session.
- **Covalent radius (24/118) and homonuclear BDE (21/118) are sparse** because
  those are the only entries in the session's own tables. They were
  deliberately **not** topped up from recall; a fuller table must come with a
  citation.
- **The plan's dyadic offset does not exist for this data.** The plan asks for
  minimal *O* with 2ᴼ·v ∈ Z²⁴; denominators of 3, 12 and 2.5 × 10⁷ are not
  powers of two, so no such *O* exists. The codecs clear the general least
  common denominator instead — strictly more general, always defined — and
  `dyadic_exponent()` returns `None` in those cases rather than pretending.
  This is a documented departure from the plan text, not an oversight.
- **The lexicon is a 10-concept sample**, built to exercise the codec, not a
  corpus. Its carriers are unreadable without the `Vocabulary` that produced
  them.
- **Redundant coordinates are not independent evidence.** Physics coordinates
  10–16 and element coordinates 18–23 are functions of other coordinates; they
  are decode-time consistency checks, and a carrier that satisfies them has
  not thereby been validated against the world.
- The GPU was **not used and is not applicable**: exact `int`/`Fraction`
  arithmetic has no CUDA path, and reaching one would require the floats this
  step exists to exclude. The full sweep takes well under a minute on one core.

## Next steps (after GLM-3+ Step 2)

1. **Step 3 — `reasoning/`**: inference over stacks with facet-level failure
   attribution, using the 222 scalar and 71 tensor relations that accompany
   the 660-concept register as the first test corpus. **Done — see below.**
2. **Widen the chemistry sources** so covalent radius and BDE reach full
   coverage from a cited external table rather than staying at 24/118 and
   21/118.
3. **Cross-validate the codecs** with an independent second implementation, to
   move the round-trip claims off Tier 1.

# GLM-3+ Step 3 — Algebraic & Geometric Reasoning Kernel

`glm_universal/reasoning/` is implemented: four modules, a frozen relation
snapshot, 62 unit tests and a runnable audit. Package documentation lives in
`glm_universal/reasoning/README.md`; the results of this run are in
`results/step3_reasoning_kernel.json` and `results/step3_reasoning_kernel.md`.

## What was built

| file | contents |
| --- | --- |
| `glm_universal/reasoning/product.py` | Norton–Sakuma `2A` algebra over the 98,280 type-2 classes: `a·b = (1/8)(a + b − a_ab)`, the Griess form on axes, the 3-dimensional subalgebra with checked closure, exact Ising fusion spectrum, Miyamoto `τ` and `σ` |
| `glm_universal/reasoning/metric.py` | positive-definite Griess form on `Q^24`, exact squared distances, float-free angular comparison, triangle inequality by clearing the square root, exact single/complete linkage |
| `glm_universal/reasoning/analogy.py` | `D* = C + (B − A)` with projection onto candidates, the Golay code, or `Λ` by a provably optimal nearest-point decoder |
| `glm_universal/reasoning/verifier.py` | operator algebra, expression parser, and the multi-plane audit with 31-facet attribution |
| `glm_universal/reasoning/_data/physics_relations.json` | the 222 + 71 relation *statements* (frozen data, not an oracle) |
| `glm_universal/tests/test_reasoning.py` | 62 tests, including AST scans for float literals, `float()` calls, `random` and third-party imports |

## Results of this run

| check | result | source |
| --- | --- | --- |
| type-2 classes enumerated | 98,280 | `results/step3_reasoning_kernel.json` |
| `2A` pairs audited: closed, commutative, non-associative, Gram `1`/`1/8` | 8 / 8 | same |
| pair census against one axis (`1A`/`2A`/unmodelled/`2B`) | 2 / 9,200 / 94,208 / 93,150 | same |
| fusion spectrum dims at `1, 0, 1/4, 1/32` | 1, 1, 1, **0** | same |
| Griess form positive definite (2 independent proofs) | yes; Leech Gram determinant 1 | same |
| triangle inequality | 210 / 210 triples | same |
| physics analogies reaching the expected concept | 6 / 6 | same |
| element group/period analogies exactly and uniquely correct | 5 / 5 | same |
| perturbed Leech points decoded back to origin | 4 / 4 | same |
| scalar relations under scalar semantics | 222 / 222 | same |
| tensor relations under full semantics | 71 / 71 | same |
| scalar relations under full semantics | 186 / 222 | same |
| MOG facets carrying blame for the 36 strict failures | 12 of 31 | same |
| test suite | 62 passed (reasoning), 239 passed + 5,110 subtests (package) | pytest output |

Three results worth stating:

- **`τ_a` is the identity on the `2A` subalgebra, and that is derived rather
  than assumed.** The `1/32`-eigenspace of `ad_a` comes out empty when
  `(ad_a − λI)x = 0` is solved exactly over `Q^3`, and `τ` is by definition
  `−1` there. The axis swap people expect from `τ` actually belongs to `σ`
  (`−1` on the `1/4`-eigenspace), which the module checks is an automorphism
  and an isometry.
- **36 statements a units table gets right are wrong at full meaning.**
  `acceleration = speed / time` fails on rank and parity; the discrepancy lands
  in coordinates 18 and 19, and the verdict blames exactly the facets
  containing them (`brick2/col5/row3/cube2.*` and `brick1/col3/row0/cube1.*`).
  That is the facet attribution doing real work rather than decorating a
  boolean.
- **The additive analogy model has a visible boundary.**
  `time : frequency :: length : ?` is an inversion, not a translation, so the
  model answers acceleration rather than wavenumber. Recorded in the report as
  a boundary case, not quietly dropped.

## Commands run

```bash
uv run python workflow/09_extract_physics_relations.py   # freeze 222 + 71 + 40 aliases
uv run pytest glm_universal/tests/test_reasoning.py -q   # 62 passed
uv run pytest glm_universal/tests/ -q                    # 239 passed, 5110 subtests
uv run python workflow/10_reasoning_audit.py             # results + claim ledger
uv run python workflow/11_update_manifest.py             # provenance
```

## Evidence and limits (GLM-3+ Step 3)

**Checked, and at what tier.**

- Tier 1 (computed this run): every number in the table above is the return
  value of a function in `glm_universal.reasoning`, called by
  `workflow/10_reasoning_audit.py`, and re-read from
  `results/step3_reasoning_kernel.json`.
- Tier 3 (cross-validated by two independent paths): the relation tallies
  222 / 71 / 186. This kernel's own parser and operator algebra over
  `glm_universal`'s frozen 660-concept register produce those three numbers;
  the upstream `glm2_library.library_audit()`, a separate implementation over a
  separate copy of the register, produces the same three. The two paths share
  no code — only the statements, which are data.
- Positive definiteness is established twice within this run: by the diagonal
  of the form on the standard basis, and by Sylvester's criterion on all 24
  leading minors of the Leech Gram matrix in integer arithmetic.

**Not checked.**

- The `2A` audit covers **8 pairs** drawn deterministically from one seed
  class, not all 9,200 partners of that axis and not all 98,280 classes. The
  closure argument is uniform; the verification is a sample.
- The **pair-invariant-1 position is not modelled**. No Norton–Sakuma type is
  claimed for it and every product there raises. Whether it is 3A, 4A or
  another type is outside what this substrate decides.
- Identifying pair invariant 2 with the Norton–Sakuma `2A` position is an
  **operational definition** grounded in the substrate (it is the unique
  position where `u XOR v` is again type 2, hence the unique position where the
  Sakuma triple exists here). This run verifies the `2A` relations close there;
  it does not prove a correspondence with the Monster's `2A` conjugacy class.
- Analogy accuracy is reported on 6 physics and 5 chemistry items **chosen by
  hand** to probe specific structure. That is a demonstration, not a benchmark:
  no held-out set, no randomised sampling, and physics answers are usually tie
  classes (4–11 members) rather than single concepts.
- The nearest-lattice-point decoder is optimal **by construction**. This run
  checks that claim against explicit rivals on one query and on four perturbed
  minimal vectors; it is not an exhaustive proof by enumeration.
- Clustering ran on one hand-picked slice of 14 physical quantities, with no
  stability analysis over subsamples.
- The GPU was **not used and is not applicable**, for the same reason as
  Steps 1 and 2: exact `int`/`Fraction`/`F_2` arithmetic has no CUDA path, and
  reaching one would require the floats these steps exist to exclude. The whole
  audit takes about ten seconds on one core.

## Next steps (after GLM-3+ Step 3)

1. **Widen the `2A` audit** from 8 sampled pairs toward the full 9,200-partner
   orbit of one axis, which is affordable and would move the closure claim from
   a sample to a census.
2. **Decide the invariant-1 position** — identify which Norton–Sakuma type it
   carries, or establish that this substrate cannot see it.
3. **Benchmark the analogy solver** on a held-out item set rather than
   hand-chosen demonstrations, and report tie-class size as a first-class
   metric.
4. **Widen the chemistry sources** (carried over from Step 2): covalent radius
   and BDE remain at 24/118 and 21/118.


# GLM-3+ Step 1 (runtime) — Interactive Geometric Language Runtime and the Three Column Thinking Engine

The reasoning kernel of Step 3 can answer questions, but nothing could *ask*
it one. This step builds that layer: `glm_universal/runtime/` and the
top-level `GLM.py`, which together turn a typed or piped string into a
verified **Three Column Thinking** trace.

## What was built

| File | Lines | What it does |
|---|---|---|
| `glm_universal/runtime/parser.py` | ~640 | Deterministic semantic query parsing: a fixed grammar, a fixed keyword table, and six classification rules applied in a fixed priority order. No language model, no embedding, no sampling. |
| `glm_universal/runtime/session.py` | ~950 | `GeometricSession`: five lazily-loaded registers, the concept index over them, the active basis, the inference history, and one solver per query kind. |
| `glm_universal/runtime/tct_engine.py` | ~630 | The Three Column Thinking generator, the script renderer, the AST exactness check, and the subprocess verifier. |
| `GLM.py` | ~430 | CLI and API entry point: `--query`, `--domain`, `--interactive`, `--verify-tct`, `--export-trace`, plus `--format`, `--columns`, `--basis`, `--list-domains`. |
| `glm_universal/tests/test_runtime.py` | ~900 | 181 tests over the parser, the session, the TCT engine, the CLI, and package-wide exactness. |

## The three columns, and why the third one is not a printout

A trace states one solved query three times over. **Column 1** is the
reasoning chain in English. **Column 2** is the same chain as exact statements
over `Q`, `Z` and `F_2` — rational equations, digit-stack parameters, Griess
forms, Norton–Sakuma products, every rational as a canonical `"n/d"` string.
Both columns are read off the *same* `Step` objects, so entry *i* of each is
the same step; they cannot drift apart.

What they could still share is a bug in the solver. So **column 3** is a
generated, self-contained Python script that does not repeat the solver's
steps: it re-enters the package at its public API, in a fresh interpreter,
with column 2's values embedded as literals, and exits non-zero if anything
differs. Verification is then two independent comparisons — the script's own
exit code, and the parent process re-reading the script's JSON and comparing
key by key. A trace counts as verified only when both agree.

**This is a same-session cross-check between two code paths, not an
independent reproduction of the mathematics.** Both paths call the same
`glm_universal` functions, so a defect in those functions would be invisible
to it. What it does catch is the solver mis-transcribing, mis-rounding or
mis-labelling a result, and any dependence of an answer on interpreter state,
import order or a cached table — since the subprocess shares none of those.

## The spatial register

The plan called for a spatial/ARC domain. Rather than invent a dataset, the
`spatial` register is built from the MOG's own structures: the trio's three
octads, the sextet's six tetrads, the four rows of the `4 x 6` frame, and the
fifteen octads obtained as unions of tetrad pairs — 28
carriers, every one of them a presentation of the substrate. The octad
property of the bricks and of all fifteen tetrad-pair unions is *checked*
against the Golay code every time the register is built, so the sextet
property is verified rather than assumed.

## Results of this run

Registers loaded: physics 660, chemistry 118,
mathematics 22, lexicon 10, spatial
28 — 1481 distinct surface forms in the
concept index.

| Measure | Value |
|---|---|
| Battery queries | 20 |
| Parsed to the expected kind | 20/20 |
| Solved | 20/20 |
| Column 3 ran and matched column 2 | 20/20 |
| Solver kinds covered | 7 of 7 |
| Registers covered | 5 of 5 |
| Generated scripts float-free (AST) | True |
| Queries correctly refused | 6/6 |
| CLI invocations with the expected exit code | 7/7 |
| float literals in runtime sources | 0 |
| `float()` calls in runtime sources | 0 |
| RNG imports in runtime sources | 0 |
| Wall-clock imports in runtime sources | 0 |

### Negative controls

A verifier that always reported success would pass every positive check above,
so two deliberate falsifications were run:

- **A wrong exact value.** One claim in column 2 was replaced with `1/1`. The
  script exited 1 and the
  parent's comparison flagged exactly
  ['griess_norm2']. Caught:
  **True**.
- **A claim nothing recomputes.** A claim absent from every script template
  was added to column 2. It was reported as a missing key rather than passed
  over. Caught: **True**.

### One real defect this audit found

The first audit run failed on `check tensor force = mass * acceleration`. The
parser detected the semantics qualifier `tensor` and switched to `full`
semantics correctly, but left the word in the expression, so the left side
parsed as the unknown concept `tensor force`. Fixed in
`_strip_semantics_qualifier`, which removes a qualifier only in the two
positions where it is unambiguously a directive — leading, or in a trailing
`under <word> semantics` phrase — and leaves it alone mid-expression, where
deleting it would silently change the equation being audited. Four regression
tests cover the fix.

## Design invariants, enforced by tests rather than intended

- **No float anywhere**, in the runtime sources *or* in the scripts they
  generate. `script_is_exact` checks generated source by AST, so a `float` in
  a string or a comment is correctly ignored while a real one is caught.
- **No RNG and no wall clock.** A trace must be byte-identical between runs,
  which a test asserts by building the same trace from two fresh sessions and
  comparing the rendered Markdown.
- **XOR only where it is addition.** `sakuma_third_axis` combines two classes
  by `^` because on the `F_2` module `Lambda / 2 Lambda` that *is* vector
  addition, and both the language and the mathematics columns say so. Nowhere
  is `^` used as a stand-in for arithmetic on rationals.
- **Failures are results.** An unsolved query returns a `Solution` with
  `ok=False`, is recorded in the history, and still explains itself. Only a
  structurally malformed string raises.

## Commands run

```bash
uv run pytest glm_universal/tests/ -q                       # 420 passed, 5110 subtests
uv run python workflow/12_runtime_tct_audit.py              # AUDIT PASSED
uv run python GLM.py --list-domains
uv run python GLM.py -q "force = mass * acceleration" --verify-tct
printf 'describe carbon\n:quit\n' | uv run python GLM.py --interactive
```

## Output files

| Path | Contents |
|---|---|
| `glm_universal/runtime/{__init__,parser,session,tct_engine}.py` | The runtime package |
| `GLM.py` | CLI and API entry point |
| `glm_universal/tests/test_runtime.py` | 181 tests |
| `results/step1_runtime_tct.json` | Full machine-readable audit |
| `results/step1_runtime_tct.md` | Human-readable scorecard |
| `reports/tct_examples.md` | Three worked traces, all three columns |
| `workflow/12_runtime_tct_audit.py` | The audit script |

## Evidence and limits (GLM-3+ Step 1 runtime)

**Checked, and at which tier.**

- Every figure in the table above was computed by
  `workflow/12_runtime_tct_audit.py` in a single run and read back from
  `results/step1_runtime_tct.json` (Tier 1, computed; Tier 2 for the values
  restated here, which were re-read from that file).
- The 20/20 verification count is a
  Tier 3 cross-validation **in a narrow sense**: each value was derived twice,
  once by the in-process solver and once by a generated script in a separate
  interpreter. Named paths: `GeometricSession._solve_*` and the corresponding
  `tct_engine` template. Both call the same `glm_universal` functions, so this
  does not test those functions.
- The full suite reports 420 passed and 5,110 subtests passed, up from 239 and
  5,110 before this step; no previously passing test changed status.

**Not checked.**

- **Natural-language coverage.** The parser was exercised on 20 battery
  queries, 6 refusals and the parser tests. There is no held-out corpus of
  phrasings, so the rate at which a plausible user query is misclassified is
  unmeasured. The rules are transparent and the parse trace is always
  available, which bounds the cost of a misclassification but does not
  bound its frequency.
- **Solver correctness beyond the kernel's own tests.** The runtime is a
  routing and presentation layer; the mathematics it reports is Step 1–3's,
  under those steps' own limits.
- **Analogy quality.** The default subspaces
  (`physics.dimension`, `chemistry.position`) are inherited choices, not
  results of a tuning study, and no accuracy figure is claimed for the
  analogy solver here.
- **Performance.** Wall-clock figures are deliberately not recorded as data,
  so the artefacts stay byte-stable between runs; no throughput claim is made.
- **The `product` solver's pair selection** takes the first 2A partner in
  sorted class order. That is deterministic and checked, but it is one pair,
  not a census over the 9,200-partner orbit — the widening carried over from
  Step 3.

## Next steps (after GLM-3+ Step 1 runtime)

1. **A held-out query corpus** with per-rule precision, so parser
   misclassification becomes a measured quantity rather than an unmeasured
   one.
2. **Widen column 3's independence.** Today it re-enters the same API. A
   second template family that recomputes from the substrate primitives alone
   would turn the cross-check into something closer to a real reproduction.
3. **ARC-style spatial tasks.** The spatial register presents MOG structures;
   the next step is grid-to-grid transformation queries over it.
4. **A `benchmarks` suite** wiring the runtime to scored task sets, which is
   what `glm_universal/benchmarks` is reserved for.


============================================
GLM-3+ v0.5.0 — semantic lexicon + physics expansion (21 Aug 2026)
============================================

A working-session entry in the running record.  The work was: build the
missing CLI, replace the runtime's index-based lexicon with the meaning-based
one, and grow the physics register from 660 to 701 concepts.  Each change is
held to the same two-legged losslessness contract the rest of the package
enforces, and the full test suite stays green throughout.

## What was done

### 1. The missing `GLM.py` CLI at the repo root

The `glm_universal/tests/test_runtime.py` suite (181 tests) had been
failing since v2.8 because it expected a CLI entry script at
`/GLM.py` that had never been written.  Twenty-six tests errored on
import, four exactness tests errored on `Path.read_text()` of the
missing file.

`GLM.py` is now a ~480-line shell over `glm_universal.runtime` that
implements:

- **Batch mode**: `-q QUERY` (repeatable), `--query-file PATH`,
  `-c COLUMNS` (1=lang, 2=math, 3=script), `-f text|json|markdown`,
  `-d DOMAIN`, `--export-trace PATH`, `--verify-tct`,
  `--check-script-exactness`, `--list-domains`.
- **Interactive mode** (`--interactive`): a REPL over stdin or
  `--input PATH`, with meta-commands `:help`, `:domains`, `:basis`,
  `:columns`, `:verify on|off`, `:snapshot`, `:history`, `:export PATH`,
  `:quit`.  Unknown meta-commands report `unknown meta-command` rather
  than crashing.
- **Exit codes**: 0 success, 1 unsolved/malformed, 2 usage error.

The file imports only the standard library and `glm_universal`, so it
passes the AST exactness scan in `TestExactness`.

### 2. Semantic lexicon (replaces the runtime's lexicon register)

The legacy `glm_universal/data_objects/lexicon.py` encodes a word by
interning its spelling into vocabulary indices.  That makes the
encoding reversible but meaningless: two words that mean the same
thing but spell differently land far apart, and two words that spell
alike but mean different things land close.  It is a stable
identifier, not a measurement of meaning.

The new `glm_universal/data_objects/semantic_lexicon.py` takes the
other road.  A word is encoded by **what it means**:

```
0..9    semantic primitives  (ten Fractions in [0, 1])
                              abstract_concrete, animate_inanimate,
                              countable_mass, temporal_stable, spatial_local,
                              causal_passive, positive_negative,
                              singular_plural, active_stative,
                              definite_indefinite
10      pos_code              index 0..11 as a Fraction
11      arity                 number of relations
12..15  predicate indices     up to four relations
16..19  object indices       aligned with the predicates
20      has_physical_dim     1 if the word has EXT10 dimensions, else 0
21      primitive_count       n_set / 10
22      relation_count        n_rels / 4
23      checksum              (subject + sum(preds) + sum(objs)) mod 2^20
```

The curated sample lexicon is 40 concepts across physics (energy,
force, mass, velocity, acceleration, momentum, torque, power, work,
pressure), common matter (water, electron, atom, molecule, photon,
charge, gravity, light), thermal (heat, temperature, entropy,
enthalpy), verbs (accelerate, measure, attract, rotate, react),
adjectives (heavy, fast, slow, hot, cold), math (lattice, reflection,
monster, golay), and chemistry (bond, reaction, element, ion).

`SemanticConcept` is intentionally unhashable: its `__eq__` compares
the *encoded* form (primitives + relations + subject + pos), and the
encoded form does not carry `physical_dims` — only the `has_dims`
flag — so a hash on the encoded form would not match the hash of a
`SemanticConcept` whose `physical_dims` differs.  Callers use
`concept.subject` as a dict key.

`SemanticLexiconCodec.encode`/`decode`/`check` honour both legs of
the `Codec` contract:

- **substrate leg**: `class_stack_rebuild(class_stack(v)) == v`
- **semantic leg**: `decode(encode(x)) == x`

**Wiring.**  `runtime/session.py`'s `register("lexicon")` now loads
`do.semantic_lexicon_objects()` instead of `do.lexicon_objects()`.
`tct_engine.py`'s `_pool_snippet("lexicon")` likewise emits
`do.semantic_lexicon_objects()[0]` for column-3 scripts.  The legacy
module is still importable for comparison and is exercised by
`TestLexicon` in `test_data_objects.py` (10 concepts, unchanged).

**Resolution behaviour.**  Because `DOMAIN_PRIORITY` is
`(physics, chemistry, mathematics, spatial, lexicon)`, a word that
exists in physics (e.g. `energy`) still resolves to its physics
quantity when no domain hint is given.  Words unique to the lexicon
— `gravity`, `water`, `atom`, `electron`, `molecule`, `photon`,
`heat`, `temperature`, etc. — now resolve to the *semantic* concept
rather than the legacy interned-indices one.  The semantic concept of
`energy` is reachable as `describe energy -d lexicon` from the CLI or
`session.ask("describe energy", domain="lexicon")` from the API.

### 3. Physics register expansion: 660 → 701 concepts

Forty-one new physics concepts were added to
`glm_universal/data_objects/_data/physics_660.json` across nine
previously-thin domains:

| Domain | Added | Examples |
|---|---|---|
| acoustics | 6 | `acoustic_power_level`, `acoustic_intensity_level`, `acoustic_attenuation`, `loudness_level`, `acoustic_admittance`, `audio_frequency` |
| photometry | 6 | `color_temperature`, `chromaticity_x`, `chromaticity_y`, `tristimulus_X`, `tristimulus_Y`, `tristimulus_Z` |
| radiometry | 6 | `spectral_responsivity`, `spectral_power_density`, `spectral_absorptance`, `reflectivity`, `transmissivity`, `radiant_exitance` |
| base | 4 | `proton_mass`, `reduced_planck_constant`, `stefan_boltzmann_constant`, `avogadro_number` |
| geophysics | 6 | `s_wave_velocity`, `magnetic_inclination`, `magnetic_total_field`, `richter_magnitude`, `moment_magnitude`, `magnetic_anomaly` |
| information | 5 | `shannon_entropy`, `hartley_entropy`, `kl_divergence`, `fisher_information`, `self_information` |
| statistical mechanics | 3 | `gibbs_free_energy`, `equipartition_energy`, `degeneracy` |
| astronomy | 3 | `hubble_constant`, `hubble_distance`, `light_year` |
| signals and control | 2 | `transfer_function`, `nyquist_frequency` |

Each new concept has a unique snake_case name, a short symbol, the SI
coherent unit, a one-line gloss, ten exact rational EXT10 exponents
(as `"n/d"` strings), a decimal scale (usually `"0/1"`), tensor rank
(0/1/2), and P/T/C parities (0/1/-1).  All 701 concepts pass
`PhysicsCodec.check()` — both the substrate leg and the semantic leg.

## Test count

| Layer | Before | After |
|---|---|---|
| `test_substrate.py` | 96 | 96 |
| `test_data_objects.py` | 177 | 177 (sizes updated 660→701) |
| `test_reasoning.py` | 94 | 94 |
| `test_runtime.py` | 155 passed, 26 failed/errored | 181 |
| `test_semantic_lexicon.py` (new) | — | 39 |
| `test_physics_expansion.py` (new) | — | 9 |
| `test_semantic_lexicon_runtime.py` (new) | — | 21 |
| **Total** | **452 passed + 26 failed, 5110 subtests** | **521 passed, 5577 subtests, zero failures** |

## Known remaining gaps

These are deliberately *not* claimed as fixed:

1. **`physical_dims` is metadata on `SemanticConcept`.**  The carrier
   stores only the `has_dims` flag (coord 20), not the ten EXT10
   exponents themselves.  Two `SemanticConcept`s whose only difference
   is the value of `physical_dims` therefore compare equal.  Preserving
   the full EXT10 would require either dropping relation slots from
   four to fewer, or moving to a multi-carrier encoding.
2. **Carrier-space product still converges to "velocity"** for all
   word pairs (README roadmap item #3, untouched).
3. **Element encoding still doesn't reach 2A axes** for most elements
   (README roadmap item #2, untouched).
4. **NRCI shells 2 and 4 still use float (sqrt)** (README roadmap
   item #4, untouched).

## Files added or modified

| File | Status | Purpose |
|---|---|---|
| `GLM.py` | new | CLI entry point at the repo root |
| `glm_universal/data_objects/semantic_lexicon.py` | new | SemanticLexiconCodec + 40 sample concepts |
| `glm_universal/data_objects/__init__.py` | modified | exports the new module |
| `glm_universal/data_objects/_data/physics_660.json` | modified | 660 → 701 concepts |
| `glm_universal/data_objects/physics.py` | modified | docstrings 660 → 701 |
| `glm_universal/runtime/session.py` | modified | `register("lexicon")` now loads `semantic_lexicon_objects()`; describe solver shows primitives/arity for lexicon concepts |
| `glm_universal/runtime/tct_engine.py` | modified | `_pool_snippet("lexicon")` uses `semantic_lexicon_objects()[0]` |
| `glm_universal/tests/test_data_objects.py` | modified | three hardcoded 660 → 701 |
| `glm_universal/tests/test_runtime.py` | modified | two hardcoded 660 → 701 |
| `glm_universal/tests/test_semantic_lexicon.py` | new | 39 tests for the semantic codec |
| `glm_universal/tests/test_physics_expansion.py` | new | 9 tests for the augmented physics register |
| `glm_universal/tests/test_semantic_lexicon_runtime.py` | new | 21 tests for the runtime wiring |
| `glm_universal/README.md` | modified | see "GLM-3+ v0.5.0" section there |


============================================
GLM-3+ v0.5.1 — dataset audit + growth (21 Aug 2026)
============================================

A working-session entry in the running record.  The work was: audit the
physics and lexicon datasets for correctness, fix what was actually wrong,
grow both, and add the analogy-subspace plumbing that the v0.5.0 changelog
flagged as a near-term item.

## What was done

### 1. Physics dimensional audit + fixes

Wrote `audit_physics_dimensions.py` (kept under `/home/z/my-project/scripts/`,
not part of the package) that parses every concept's SI unit string and
computes the expected EXT10 exponents, then compares against what the
register claims.

The audit found 12 dimensional mismatches.  Analysis:

| Count | Diagnosis | Action |
|---|---|---|
| 7 | `luminous_*` concepts claim S=1 (solid angle) where the audit expected S=0. **EXT10 design intent** — the README's D1 explicitly keeps A and S separate even though SI treats them as dimensionless. Lumen = cd·sr, so S=1 is correct. | No change. Audit script will be updated in a future pass to honour the EXT10 convention. |
| 1 | `angstrom` had unit="A" which collides with ampere in the parser. Register's exponents are right (L=1); the unit string was wrong. | Fixed unit: `"A"` → `"angstrom"`. |
| 4 | Real bugs: `permeation_coefficient` (L=2 should be L=0), `proper_distance` (claimed all-zero, should be L=1), `proper_time` (claimed all-zero, should be T=1), `acoustic_admittance` (T=3 should be T=1, my v0.5.0 bug). | Fixed all four. |

The audit also flagged 23 unparseable units (mostly variants of `Ohm`,
`L` for litre, and fractional exponents like `Hz^(1/2)`).  These were not
changed — the parser is informational and the exponents in the register
are not in doubt for those entries.

After fixes, all 701 concepts still pass `PhysicsCodec.check()`.

### 2. Semantic lexicon audit + redesign

Wrote `audit_semantic_lexicon.py` (also under `scripts/`) that checks the
sample lexicon for codec round-trips, primitive range, subject uniqueness,
identical primitive vectors, POS distribution, antonym pair differences,
and within/cross-topic distances.

The v0.5.0 lexicon had **six groups of concepts with identical primitive
vectors** — pairs or triples of concepts that were indistinguishable in
the primitives subspace:

| Group | Why they collided |
|---|---|
| `velocity`/`fast`/`slow` | all set abstract_concrete=1/2, temporal_stable=1/4, and nothing else distinguishing |
| `acceleration`/`accelerate`/`rotate` | all had the same two primitives set |
| `torque`/`power` | both abstract_concrete=3/4 + causal_passive=1/4 |
| `atom`/`molecule`/`element` | all concrete+inanimate+stable+local |
| `reflection`/`monster`/`golay` | all abstract+inanimate+stable |
| `bond`/`ion` | both concrete+inanimate+stable+local |

The `fast`/`slow` antonym pair had **identical primitives** — they only
differed in their `opposite_of` relation target.  That's a real encoding
failure: the primitives subspace should be able to distinguish antonyms.

The v0.5.1 redesign:

1. Sets **every primitive on every concept** (no defaults — the curated
   sample no longer relies on `Fraction(1, 2)` as a fallback).
2. Uses **1/8 gradations** instead of 1/4 where finer resolution matters
   (especially `positive_negative`, `causal_passive`, `active_stative`,
   `definite_indefinite`).
3. Fixes `fast`/`slow` to differ on `positive_negative` (fast=1, slow=0)
   and `active_stative` (fast=1, slow=1/8) — so the antonym pair is now
   distinguishable on two primitive axes.
4. Distinguishes `atom`/`molecule`/`element` by `countable_mass` (atoms
   are countable, molecules are mass nouns, "element" is abstract).
5. Distinguishes `reflection`/`monster`/`golay` by their structural role:
   reflection acts on a vector (active_stative=1), monster contains
   involutions (causal_passive=1/4), golay shadows the hexacode
   (definite_indefinite=3/4).
6. Distinguishes `bond`/`ion` by `positive_negative` (bond=1/2 neutral,
   ion=1/4 — ions come in + and -).
7. Grew the sample from 40 → 95 concepts across 11 topics: physics (12),
   matter (10), thermal (5), waves (4), chemistry (6), math (8), verbs
   (12), adjectives (12), abstract (8), states of matter (5),
   electromagnetism (5), misc (8).

After redesign, **all 95 primitive vectors are unique** — zero collisions.
Within-topic d² is 0.150, cross-topic d² is 0.282 — a 1.88× ratio.  POS
distribution: 71 nouns / 12 verbs / 12 adjectives.

### 3. Physics register expansion: 701 → 720 concepts

Added 19 more physics concepts with unique names that avoid clashes with
existing entries.  Span: optics (3), quantum (3), materials (4),
electrochemistry (3), plasma (2), meteorology (2), biophysics (2).

Examples: `refractive_index_medium`, `abbe_dispersion_number`,
`diopter_power`, `expectation_value_position`,
`standard_deviation_position`, `compton_wavelength_electron`,
`yield_stress`, `fracture_stress`, `elastic_modulus`, `toughness_modulus`,
`standard_electrode_potential`, `exchange_current_per_area`, `nernst_slope`,
`debye_screening_length`, `ionization_fraction`, `dew_point_temperature`,
`saturation_vapor_pressure`, `resting_potential_cell`,
`action_potential_amplitude`.

All 720 pass `PhysicsCodec.check()`.

### 4. New analogy subspaces for the lexicon

Added two new entries to `reasoning.analogy.SUBSPACES`:

* `lexicon.primitives` — the ten semantic primitives alone.  Lets
  analogies over words resolve on meaning rather than spelling.
* `lexicon.relations` — the four predicate + four object slots.  Asks
  "what relations does this concept participate in?" without regard to
  its meaning.

Updated `runtime.session.DEFAULT_SUBSPACE["lexicon"]` from `None` to
`"lexicon.primitives"` so the runtime session uses the primitives subspace
by default for lexicon-domain analogies.

Cross-domain analogies (`heat : temperature :: force : ?`) still fail
because the analogy solver requires all three operands from the same
register — that's an existing limitation.  Within-lexicon analogies
(`hot : cold :: fast : ?`) now work end-to-end via the runtime:

```python
session.ask("hot : cold :: fast : ?")
# resolves on lexicon.primitives subspace
```

## Test count

| Layer | Before (v0.5.0) | After (v0.5.1) |
|---|---|---|
| `test_substrate.py` | 96 | 96 |
| `test_data_objects.py` | 177 | 177 (sizes updated 701→720) |
| `test_reasoning.py` | 94 | 94 |
| `test_runtime.py` | 181 | 181 (sizes updated 701→720) |
| `test_semantic_lexicon.py` | 39 | 39 (antonym tests updated) |
| `test_physics_expansion.py` | 9 | 9 (size updated 701→720) |
| `test_physics_expansion_v2.py` (new) | — | 5 |
| `test_semantic_lexicon_runtime.py` | 21 | 21 (size updated 40→95) |
| `test_lexicon_subspaces.py` (new) | — | 12 |
| **Total** | **521 passed, 5577 subtests** | **533 passed, 5854 subtests, zero failures** |

## Known remaining gaps

These are deliberately *not* claimed as fixed:

1. **Cross-domain analogies still fail.**  `heat : temperature :: force : ?`
   fails because `force` resolves to physics (DOMAIN_PRIORITY) while
   `heat`/`temperature` resolve to lexicon.  The analogy solver requires
   all three operands from the same register.  Fixing this needs either
   a multi-domain analogy mode or a domain-coercion step.
2. **`physical_dims` is metadata on `SemanticConcept`** (unchanged from
   v0.5.0).  The carrier stores only the `has_dims` flag.
3. **Audit script's unit parser** treats `sr` as dimensionless, so it
   reports the 7 `luminous_*` concepts as mismatches.  These are correct
   per EXT10 design — the parser should learn the EXT10 convention.
4. **23 unparseable units in the audit** (Ohm, L for litre, fractional
   exponents).  These are not bugs in the register, only limitations of
   the parser.
5. **Carrier-space product still converges to "velocity"** (README
   roadmap item #3, untouched).
6. **Element encoding still doesn't reach 2A axes** for most elements
   (README roadmap item #2, untouched).
7. **NRCI shells 2 and 4 still use float (sqrt)** (README roadmap item
   #4, untouched).

## Files added or modified (v0.5.1)

| File | Status | Purpose |
|---|---|---|
| `glm_universal/data_objects/semantic_lexicon.py` | modified | 40 → 95 concepts, every primitive set explicitly, 1/8 gradations |
| `glm_universal/data_objects/_data/physics_660.json` | modified | 701 → 720 concepts (+19 unique new); 5 dimensional fixes |
| `glm_universal/data_objects/physics.py` | modified | docstrings 701 → 720 |
| `glm_universal/reasoning/analogy.py` | modified | added `lexicon.primitives` + `lexicon.relations` subspaces |
| `glm_universal/runtime/session.py` | modified | `DEFAULT_SUBSPACE["lexicon"]` is now `"lexicon.primitives"` |
| `glm_universal/tests/test_data_objects.py` | modified | three hardcoded 701 → 720 |
| `glm_universal/tests/test_runtime.py` | modified | two hardcoded 701 → 720 |
| `glm_universal/tests/test_physics_expansion.py` | modified | size 701 → 720 |
| `glm_universal/tests/test_semantic_lexicon.py` | modified | antonym tests updated for new primitive values |
| `glm_universal/tests/test_semantic_lexicon_runtime.py` | modified | size 40 → 95 |
| `glm_universal/tests/test_physics_expansion_v2.py` | new | 5 tests for the 19 v0.5.1 physics concepts |
| `glm_universal/tests/test_lexicon_subspaces.py` | new | 12 tests for the two new analogy subspaces |
| `glm_universal/README.md` | modified | see "GLM-3+ v0.5.1" section there |







============================================
GLM-3+ v0.5.2 — directive alignment + substantive tests (21 Aug 2026)
============================================

A working-session entry in the running record.  The work was: review the
`ubp_universal_1.txt` directive against the operational system, find
where the previous growth broke things, fix them, and add tests that
actually check the answer is right (not just that the system returns one).

## The directive, in brief

`ubp_universal_1.txt` says the GLM is a layered projection system:

1. **Golay → Leech → Griess → Moonshine** is the unbroken mathematical
   pipeline.
2. **Each layer is true within its range** and hands off to the next when
   its range is exhausted.
3. **Exact arithmetic only, no floats, no random, no SHA256, no XOR where
   alternatives exist.**
4. **Simplifications and stubs are prohibited.** Learn from failures.
5. Words are projections of meaning — many words are projections of
   existing physics or math concepts.
6. The multi-MOG-cube (per `glm_lean/glm3/glm3_mog.py`) is not an
   add-on: a Leech point IS a stack of MOG frames.

## What was checked, and where we stand

### Multi-MOG-cube — present and operational

`glm_universal/substrate/digit_stack.py`'s `class_stack` IS the
multi-MOG-cube from `glm_lean/glm3/glm3_mog.py`.  Verified on a real
Leech basis vector:

* `plane 0` is constant (all 24 cells equal — the mod-2 parity frame)
* `plane 1` is a Golay codeword (a valid member of `GOLAY_SET`)
* the mod-8 sum condition holds (`sum(x) ≡ 4·(x_0 mod 2) mod 8`)

Every DataObject's `obj.stack()` produces this stack of MOG frames,
and `obj.plane_grids()` shows each plane as a 4×6 grid.  The substrate
side of the directive is honoured.

### The pipeline — Golay → Leech → Griess is wired

* **Golay** (`substrate/mog.py`): 4,096 codewords, 759 octads, verified
  MOG alignment with hexacode shadows.
* **Leech** (`substrate/leech2.py`): 196,560 minimal vectors, the 98,280
  type-2 classes, Λ/2Λ class census.
* **Griess** (`reasoning/product.py`, `reasoning/metric.py`): the
  Norton-Sakuma 2A algebra, the Griess form, the trilinear form
  `⟨u·v, w⟩ = T(x, y, z)`.
* **Moonshine** — not wired.  The graded dimensions `V_0, V_1, V_2, V_3, …`
  are not computed and the j-function is not used.  This is the
  explicit Step 4/Step 5 boundary the directive describes.

### The dimension-projection layers — implemented but not used by the runtime

`reasoning/dimension_layers.py` implements the five layers the
directive describes (substrate → integer → rational → Griess → universal),
each with a `perceive` and `measure` function and a `reach`/`failure_mode`
description.  An `escalate()` function walks up the layers.

**But the runtime session never calls `escalate()`.**  The session's
solvers each pick one layer and use it directly (the analogy solver uses
`SUBSPACES`, the verifier uses `digit_stack.verify_equation`, etc.).
The "hand off to the next layer when this one's range is exhausted"
mechanism is implemented but not wired into any user-facing query.

This is an honest gap, not a hidden one.  The layers exist, the
escalation function exists, but no query path uses it.

## What was found and fixed

### Regression: physics symbols colliding with element symbols

The v0.5.0 physics expansion added concepts whose symbols are short
strings that collide with element symbols:

| Physics concept | Symbol | Element it collided with |
|---|---|---|
| `acoustic_intensity_level` | `Li` | Lithium |
| `avogadro_constant` (existing) | `NA` → `na` | Sodium |
| `bejan_number` (existing) | `Be` | Beryllium |
| `magnetic_flux_density` (existing) | `B` | Boron |
| `force` (existing) | `F` | Fluorine |
| `momentum`, `power` (existing) | `P` | Phosphorus |
| `action` (existing) | `S` | Sulfur |
| `wavenumber` (existing) | `K` | Potassium |
| `capillary_number` (existing) | `Ca` | Calcium |
| ...62 of 118 element symbols total |

Because `DOMAIN_PRIORITY = (physics, chemistry, ...)` ranks physics
first, a query like `Li : Na :: Be : ?` resolved to
`acoustic_intensity_level : avogadro_constant :: bejan_number : avogadro_number`
— a syntactically valid but semantically broken answer.

**Fix:** `_aliases_for()` in `runtime/parser.py` now suppresses short
physics symbol aliases (length ≤ 2, normalised) when they appear in the
hard-coded 118-element symbol table.  The physics concept is still
reachable by its long name (`acoustic_intensity_level`) and by its
symbol under an explicit `-d physics` domain hint.

After the fix:

```
$ python3 GLM.py -q "Li : Na :: Be : ?"
Li : Na :: Be : Mg     ✓
```

### Bug: `slow`'s `active_stative` primitive was wrong

`hot : cold :: fast : ?` was returning `react` instead of `slow`.
The arithmetic:

* `cold - hot` flips `positive_negative` (1 → 0) and `active_stative`
  (1/4 → 0).
* Applied to `fast` (positive_negative=1, active_stative=1), the
  target is (positive_negative=0, active_stative=3/4).
* `slow` had active_stative=1/8 — wrong by 5/8.
* `react` had active_stative=3/4 — correct on that axis.

The `active_stative=1/8` for `slow` was a v0.5.1 encoding mistake.
Slow things are not "barely active" — they're process-like (active),
just slower.  Fixed `slow` to `active_stative=3/4`.

After the fix:

```
$ python3 GLM.py -q "hot : cold :: fast : ?"
hot : cold :: fast : slow     ✓
```

## Substantive tests added

`test_substantive.py` (23 tests) is a different kind of test suite.
The existing suites mostly check structural properties (codecs
round-trip, parser classifies correctly, scripts are float-free).
The new suite checks **actual query answers**:

* `Li : Na :: Be : ?` → `Mg` (not `avogadro_number`)
* `hot : cold :: fast : ?` → `slow` (not `react`)
* `velocity : acceleration :: momentum : ?` → tie class containing
  `force` (not `drag_force` alone)
* `force = mass * acceleration` → `holds = True`
* `describe energy` → `domain = physics` (DOMAIN_PRIORITY correct)
* `describe energy -d lexicon` → `domain = lexicon` (semantic concept
  reachable)
* `describe Li` → `domain = chemistry` (alias suppression works)
* `heat : temperature :: force : ?` → fails with "could not settle on
  a single domain" (cross-domain limitation, documented honestly)

These tests would have caught the v0.5.0 regression.  They are the
kind of check that matters to a user.

## Honest assessment: are the tests "achieving anything"?

The user asked the right question.  Categorising the 556 tests:

| Category | Count | What they check |
|---|---|---|
| **Structural** | ~480 | Codecs round-trip, parser classifies, scripts float-free, layouts have 24 coords, etc.  These catch implementation bugs but not semantic ones. |
| **Substrate-level** | ~96 | The Golay code, Leech lattice, MOG trio/sextet are mathematically correct.  These are real mathematical claims verified by computation. |
| **Semantic** | ~23 (new in v0.5.2) | Actual query answers: `Li:Na::Be:Mg`, `hot:cold::fast:slow`, etc. |
| **Demo** | 7 (TCT) | End-to-end TCT verification of pre-pinned queries. |

The structural tests are necessary but not sufficient.  The new
`test_substantive.py` is the kind of test that catches "I added 60
physics concepts and broke the chemistry analogy" — the kind of
regression that *did* slip through v0.5.0 and v0.5.1 because no test
was checking the actual answer.

## Known remaining gaps

1. **Cross-domain analogies.**  `heat : temperature :: force : ?`
   still fails.  The analogy solver requires all three operands from
   the same register.  This is the next thing to fix.
2. **The `escalate()` function is unused.**  The dimension-projection
   layers exist but no query path uses them.  The directive's
   "layered projection" is implemented but not operationally wired.
3. **The trilinear form `⟨u·v, w⟩` is implemented but not used for
   semantic similarity.**  The directive asks: "would you like to
   explore how to explicitly compute the ⟨u·v, w⟩ inner product to
   extract semantic similarity scores between your physics concepts?"
   The answer is yes, but it's not wired yet.
4. **`physical_dims` is metadata on `SemanticConcept`.**  The carrier
   stores only the `has_dims` flag, not the ten EXT10 exponents.
5. **Element encoding still doesn't reach 2A axes** for most elements.
6. **NRCI shells 2 and 4 still use float (sqrt).**

## Files added or modified (v0.5.2)

| File | Status | Purpose |
|---|---|---|
| `glm_universal/runtime/parser.py` | modified | `_aliases_for()` suppresses short physics symbols colliding with element symbols |
| `glm_universal/data_objects/semantic_lexicon.py` | modified | `slow.active_stative` 1/8 → 3/4 |
| `glm_universal/tests/test_substantive.py` | new | 23 substantive end-to-end tests |
| `glm_universal/README.md` | modified | see "GLM-3+ v0.5.2" section there |
| `README.md` (this file) | modified | v3.1 changelog + this section |


============================================
GLM-3+ v0.5.3 — wiring of created-but-unused mechanisms (21 Aug 2026)
============================================

A working-session entry in the running record.  The work was: survey the
`glm_universal` package for reasoning mechanisms that were implemented but
never reached from any runtime query, then wire them.  The directive's
"layered projection" framing (now quoted verbatim near the top of this
README) made the priority clear — `escalate()` was the headline gap.

## Survey findings

A package-wide survey (`Task ID: agent-1d0c3206` in the worklog) found:

* **Two entire reasoning modules were not imported by the runtime at all**:
  `reasoning/dimension_layers.py` and `reasoning/coherence.py`.  Their
  public API (`escalate`, `projection_report`, `LAYERS`, `RefinedNRCI`,
  `nrci_breakdown`, `coherence_regime`, the five-shell tax machinery)
  was reachable only from their own tests.
* **The Griess algebra's introspection layer was fully built but unused**:
  the trilinear form (`griess_trilinear`, `trilinear_on_axes`,
  `coherence_of_product`), the Ising fusion analysis (`fusion_spectrum`),
  and the Miyamoto involutions (`miyamoto_tau`, `miyamoto_sigma`) were
  exercised only by their own tests.
* **`analogy.nearest_lattice_point`** — provably optimal exact Leech
  decoding — was reached only from three example scripts.  The runtime
  never called it.
* **`coherence.RefinedNRCI` was doubly orphaned**: no runtime path, and
  no test path either.
* **All five directive-mentioned mechanisms are absent from the codebase**
  (Niemeier lattices, LLVQ, FWHT, Valorani SVD, Moonshine/j-function).
  These are future work, not created-but-unused.

## What was wired

Three new runtime query kinds plus an augmentation to a fourth.

### 1. `project A B` — the layered projection

Wires `reasoning/dimension_layers.py::escalate`.  Walks both carriers
through every layer (substrate → integer → rational → griess → universal),
reporting each layer's `perceive` of each operand and the `measure` of
their separation at that layer's resolution.  This is the directive's
"layered projection" made operational: a query that runs a branch of
operations at every layer and shows where each one's reach is exhausted.

Example:

```
$ python3 GLM.py -q "project carbon oxygen" -c 1
project C O: walked 5 layers, final = universal

  1. Projecting C and O through the dimension layers: each layer perceives
     the pair at its own resolution, and the layered projection walks from
     the substrate (binary) up to the universal (all layers at once).
  2. The substrate layer sees C as binary (HW=5, snap_distance=3, NRCI=1/4)
     and O as binary (HW=6, snap_distance=4, NRCI=0).  Its measure of
     their separation is 5.
  3. The integer layer sees C as SI7 exponents (6, 12, 2, 170, 76, 4, 348)
     and O as SI7 exponents (8, 15, 3, 152, 66, 6, 498).  Its measure of
     their separation is 186.
  ...
  7. The highest layer reached is universal (dimension -1).
```

### 2. `trilinear A B C` — the invariant form ⟨A·B, C⟩

Wires `reasoning/product.py::griess_trilinear`.  The directive asks:
"would you like to explore how to explicitly compute the ⟨u·v, w⟩ inner
product to extract semantic similarity scores between your physics
concepts?"  This solver answers that question operationally.

Each operand can be either a concept name or a bare integer axis label
(one of the 98,280 type-2 classes of Λ/2Λ).  Concepts are projected onto
their nearest Leech point and that point's type-2 class is taken as the
axis.  The trilinear form `T(A, B, C) = ⟨A·B, C⟩` is then computed
exactly.  Three pairwise bilinear forms and the coherence-of-product
block are reported alongside.

Example:

```
$ python3 GLM.py -q "trilinear 127 432 463" -c 1
trilinear 127 432 463: <A.B, C> = -3/32
```

The solver fails honestly when a triple has a pair in the
"invariant-1" position (which is not modelled — 94,208 of the 98,280
type-2 classes are in this position against any given axis).

### 3. `coherence <concept>` — the five-shell NRCI breakdown

Wires `reasoning/coherence.py::nrci_breakdown`.  The whole coherence
module was created in v0.4.0 but never reached from any runtime query.
NRCI is one of the GLM's headline metrics — the directive's constants
table puts TAX and NRCI front and centre.

Reports the combined NRCI, the regime (OnBit / Coherent / Transitional /
Subcoherent), and the five per-shell taxes (Golay, sign-parity,
sextet-balance, coset-type, sextet-signed).  Shells 2 and 4 are floats
(sqrt) — documented and unavoidable.

Example:

```
$ python3 GLM.py -q "coherence carbon" -c 1
coherence C: NRCI = 0.0000 (Subcoherent)
```

### 4. `describe <concept>` — augmented with lattice projection

Wires `reasoning/analogy.py::nearest_lattice_point`.  The describe solver
now reports three additional facts per carrier:

* `lattice_distance2` — squared distance from the carrier to its nearest
  point of the Leech lattice Λ
* `lattice_norm2` — the norm of that nearest lattice point
* `lattice_is_2a_axis` — whether that lattice point is a 2A axis of the
  Monster

These three facts are exactly what the directive's "Architectural
Pathway" describes — the bridge from the substrate (Golay/MOG) through
the geometry (Leech lattice) to the local action (Λ/2Λ type-2 classes,
which index the 98,280 axes of the Monster).

Example:

```
$ python3 GLM.py -q "describe carbon" -c 1
...
  5. The nearest point of the Leech lattice Lambda to this carrier is at
     squared distance 13472679/8000000; the lattice point has norm^2 =
     1098793024/1 and is NOT a 2A axis of the Monster.
```

## Parser changes

The parser (`runtime/parser.py`) was extended:

* `KINDS` now includes `"project"`, `"trilinear"`, `"coherence"`.
* `VERBS` adds: `project`, `escalate`, `layered view`,
  `dimension projection` → `project`; `trilinear`, `threefold` →
  `trilinear`; `coherence`, `nrci`, `tax` → `coherence`.
* `_build_keyword_query` handles the new kinds.  `project A B` and
  `trilinear A B C` accept whitespace-separated operands as well as
  comma/and-separated lists (the cluster query's convention).

## TCT engine changes

`tct_engine.py` was extended with three new templates
(`_body_project`, `_body_trilinear`, `_body_coherence`) and the
`_body_describe` template was extended to recompute the lattice projection
in column 3.  The script preamble now imports `coherence` and
`dimension_layers` alongside the existing reasoning imports.

## Test count

| Layer | Before (v0.5.2) | After (v0.5.3) |
|---|---|---|
| `test_substrate.py` | 96 | 96 |
| `test_data_objects.py` | 177 | 177 |
| `test_reasoning.py` | 94 | 94 |
| `test_runtime.py` | 181 | 181 |
| `test_semantic_lexicon.py` | 39 | 39 |
| `test_physics_expansion.py` | 9 | 9 |
| `test_physics_expansion_v2.py` | 5 | 5 |
| `test_semantic_lexicon_runtime.py` | 21 | 21 |
| `test_lexicon_subspaces.py` | 12 | 12 |
| `test_substantive.py` | 23 | 23 |
| `test_wiring.py` (new) | — | 23 |
| **Total** | **556 passed, 5854 subtests** | **579 passed, 5854 subtests, zero failures** |

## Known remaining gaps

These are deliberately *not* claimed as fixed:

1. **Cross-domain analogies still fail.**  `heat : temperature :: force : ?`
   still requires all three operands from the same register.
2. **`fusion_spectrum`, `miyamoto_tau/sigma`, `adjoint_matrix`** and the
   rest of the Griess algebra's introspection layer remain unwired.
   They are deep-algebraic queries that probably need a different
   surface than the current natural-language parser offers.
3. **`pair_census`, `theta_series`, `single_linkage`/`complete_linkage`
   as a `linkage=complete` option** remain unwired.  Lower priority.
4. **All five directive-mentioned mechanisms are still absent**:
   Niemeier lattices, LLVQ, FWHT, Valorani SVD, Moonshine/j-function.
5. **`physical_dims` is metadata on `SemanticConcept`** (unchanged).
6. **NRCI shells 2 and 4 still use float (sqrt)** (unchanged).

## Files added or modified (v0.5.3)

| File | Status | Purpose |
|---|---|---|
| `glm_universal/runtime/parser.py` | modified | `KINDS`, `VERBS`, and `_build_keyword_query` extended for the three new query kinds |
| `glm_universal/runtime/session.py` | modified | imports `coherence` + `dimension_layers`; three new solvers (`_solve_project`, `_solve_trilinear`, `_solve_coherence`); describe solver augmented with `lattice_projection` |
| `glm_universal/runtime/tct_engine.py` | modified | three new templates + extended `_body_describe`; preamble imports `co` and `dl` |
| `glm_universal/tests/test_wiring.py` | new | 23 substantive tests for the four wired mechanisms |
| `glm_universal/README.md` | modified | v0.5.3 status + the new query kinds documented |
| `README.md` (this file) | modified | v3.2 changelog + this section + the layered-projection directive text near the top |



============================================
GLM-3+ v0.6.0 — directive-mentioned mechanisms implemented (21 Aug 2026)
============================================

A working-session entry in the running record.  The work was: wire the
remaining lower-priority unwired mechanisms, then implement all five
directive-mentioned mechanisms that had no code at all.

## What was done

### 1. Remaining lower-priority unwired mechanisms (v0.5.4)

Two more query kinds wired into the runtime session:

**`report <subject>`** -- on-demand recomputation of facts, with four
subjects:
- `report relations` -- wires `ve.verifier_report`, the 222+71 relation
  audit.  Reports scalar/scalar (all 222 hold), scalar/full (186 of 222
  hold, 36 fail on rank/parity), and tensor/full (all 71 hold).
- `report leech distribution` -- wires `leech2.pair_census`, the
  4-position Leech distribution {4: 2, 2: 9200, 1: 94208, 0: 93150}.
- `report theta` -- wires `leech2.theta_series`, the Leech theta series
  E_4^3 - 720*Delta.
- `report subalgebra` -- wires `pr.two_a_closure_report`, the 2A
  subalgebra closure facts.

**`angle A B`** -- wires `me.signed_cosine_squared`, the exact rational
cosine comparison.  Reports sign(<A,B>) * cos^2(A,B) and the regime
(orthogonal / near-orthogonal / acute / obtuse / parallel / anti-parallel).

### 2. Five directive-mentioned mechanisms (v0.6.0)

All five mechanisms mentioned in `ubp_universal_1.txt` that had no code
at all are now implemented:

**Moonshine layer** (`reasoning/moonshine.py`) -- the graded dimensions
V_0, V_1, V_2, ..., V_10 of the Moonshine module V^natural, plus the
j-function q-series and the Leech-to-Moonshine bridge.  V_0 = 1 (the
vacuum), V_1 = 0 (the FLM theorem), V_2 = 196884 (the Griess algebra
that the substrate's leech2 module indexes via 98,280 type-2 classes).
The bridge explains: both the Leech theta series and j are modular forms
of weight 12 for SL(2, Z), built from E_4 and Delta; V_2 is the weight-2
piece, indexed by Lambda/2Lambda.

**Niemeier lattices** (`reasoning/niemeier.py`) -- the 23 ADE root
systems that classify the even unimodular 24-dimensional lattices
(Conway-Sloane).  The Leech is the unique one with no roots (rank 0);
the other 22 have rank-24 root systems (A_n, D_n, E_6/E_7/E_8 families).
The deep-hole-type function maps each root system to its deep-hole
description.  Future work: the actual Voronoi cell of the Leech lattice
(196,560 facets) for deep-hole finding.

**LLVQ** (`reasoning/llvq.py`) -- Leech Lattice Vector Quantization:
codebook-free angular search over Leech shells.  The first 6 shells are
catalogued (origin, 196,560 minimal vectors at norm 16, 16,773,120 at
norm 24, etc.).  The shell_of function classifies a 24-vector by which
shell it sits nearest to, in O(1) given the small shell table.  Future
work: the full O(1) lookup table indexed by the first few binary digits.

**FWHT** (`reasoning/fwht.py`) -- the Fast Walsh-Hadamard Transform:
O(N log N) instead of O(N^2) for group operations.  Verified:
fwht(fwht(v)) = N*v exactly.  Handles int and Fraction inputs.  The
incoherence_apply function implements the QuIP# pre-conditioning step
(Hadamard rotation before quantisation).  Future work: wire into the
substrate-level group actions (the 4096-codeword Golay code), where
the 12x speedup matters.

**Valorani's log-space SVD** (`reasoning/valorani.py`) -- Buckingham-Pi
via rational nullspace.  The directive says "use an SVD to find the
nullspace"; the rational nullspace is exact, faster, and float-free, so
we use it and document the SVD as the conceptual motivation.  The
buckingham_pi_groups function computes the Pi groups for any set of
physics quantities, e.g. {force, mass, acceleration, length, time}
yields 2 Pi groups.

## Lessons learned (recorded for future development)

These are the things the v0.5.x / v0.6.0 work has taught us about how
the GLM system is structured, how data_objects should be encoded, and
where the system can grow.  They are recorded here so future agents
inherit them.

### How the GLM is structured

The GLM is a **layered projection system** (the directive's framing,
now quoted verbatim near the top of this README).  Each layer is true
within its range and hands off to the next when its range is exhausted:

1. **substrate** (Golay/MOG binary) -- discrete encoding, error
   correction, the multi-MOG-cube.  True for binary carriers; cannot
   represent continuous quantities.
2. **integer** (SI7 exponents) -- integer-valued dimensional analysis.
   True for integer dimensions; cannot represent fractional exponents.
3. **rational** (EXT10 + Leech carrier) -- continuous dimensions,
   tensor rank, operator algebra.  True for linear operations; cannot
   multiply concepts.
4. **Griess** (V_2 algebra + Monster) -- the non-associative product,
   the trilinear form, the 2A axes.  True for V_2; the Moonshine
   module V^natural is the next layer.
5. **universal** (all layers at once) -- the explicit projection.

The `project A B` query kind walks all five layers and reports what
each sees.  This is the operationalisation of the directive's
"layered projection perspective".

### How data_objects should be encoded

The v0.5.0 → v0.5.2 work taught us:

1. **Every data_object has 24 coordinates, no padding.**  The carrier
   shape is fixed by the Leech lattice, not by the data.  If a domain
   needs more than 24 coordinates, it must split across multiple
   carriers (the multi-carrier encoding, future work).

2. **Missingness is data, not an inconvenience.**  The element register
   uses a missingness mask (coord 17) so "0 because no measurement" is
   distinguishable from "0 as a value".  Any new domain with sparse data
   should follow this pattern.

3. **Aliases must avoid cross-domain collisions.**  The v0.5.2 fix
   (suppress short physics symbols that collide with element symbols)
   is a hard lesson: adding 60 physics concepts broke the chemistry
   analogy because `Li` resolved to `acoustic_intensity_level` instead
   of lithium.  Any new domain with short symbol aliases must check
   against the existing alias table.

4. **Primitive vectors must be unique.**  The v0.5.1 lexicon audit
   found 6 groups of concepts with identical primitive vectors.  The
   fix was to set every primitive on every concept (no defaults) and
   use 1/8 gradations where 1/4 was too coarse.  Future lexicon growth
   should run the audit script before adding concepts.

5. **Words are projections of meaning.**  The directive says "many
   words may be just projections of existing physics or math concepts".
   The semantic lexicon encodes words with 10 primitives, but `hot` is
   not yet encoded as "temperature at high scale" — it is a standalone
   concept.  Future work: encode words as projections of physics
   concepts, with the primitives carrying the scale information.

### Where the system can grow

The system is a tree, with each folder's README wiring it together:

```
glm_universal/
├── substrate/      Step 1: the multi-MOG-cube (operational)
├── data_objects/   Step 2: typed carriers (5 domains, 953 concepts)
├── reasoning/       Step 3: algebra + geometry (12 modules, all wired)
├── runtime/         Step 4: query + TCT (13 query kinds)
├── examples/        demonstrations
├── tests/           610 tests
└── benchmarks/      reserved for scored task sets
```

Growth points:
- **data_objects**: add a molecules domain (no `molecules.py` yet,
  despite the README mentioning "82 molecules" elsewhere in the repo).
- **reasoning**: the Griess algebra introspection layer (fusion_spectrum,
  miyamoto_tau/sigma, adjoint_matrix) is built but unwired.  These need
  a different query surface than the natural-language parser.
- **runtime**: the cross-domain analogy mode (heat:temperature::force:?)
  is the next user-facing gap.
- **benchmarks**: reserved but empty.  Wiring the runtime to scored
  task sets (ARC-AGI, held-out query corpus) is the next major step.

### Pulling from the surrounding repository

The `glm_universal` package is a consolidation of the older GLM
implementations in the surrounding repository:

- `glm_lean/glm/` (GLM-1, 43 claims) → substrate layer
- `glm_lean/glm2/` (GLM-2, 58 claims) → data_objects layer
- `glm_lean/glm3/` (GLM-3, 64 claims) → reasoning layer
- `glm_machine/` (GLM v37) → runtime layer
- `GMHGL/` (UBP engine) → substrate layer
- `light/aristotle_01/` (Y constant, Lean4) → coherence layer

The `glm_universal` package does not delete or supersede these; it
*consolidates* them.  The older folders remain as the provenance record,
and `glm_universal` is the active runtime.

## Test count

| Layer | Before (v0.5.3) | After (v0.6.0) |
|---|---|---|
| `test_substrate.py` | 96 | 96 |
| `test_data_objects.py` | 177 | 177 |
| `test_reasoning.py` | 94 | 94 |
| `test_runtime.py` | 181 | 181 |
| `test_semantic_lexicon.py` | 39 | 39 |
| `test_physics_expansion.py` | 9 | 9 |
| `test_physics_expansion_v2.py` | 5 | 5 |
| `test_semantic_lexicon_runtime.py` | 21 | 21 |
| `test_lexicon_subspaces.py` | 12 | 12 |
| `test_substantive.py` | 23 | 23 |
| `test_wiring.py` | 23 | 23 |
| `test_directive.py` (new) | — | 31 |
| **Total** | **579 passed, 5854 subtests** | **610 passed, 5877 subtests, zero failures** |

## Files added or modified (v0.6.0)

| File | Status | Purpose |
|---|---|---|
| `glm_universal/runtime/parser.py` | modified | `KINDS`, `VERBS`, and `_build_keyword_query` extended for `report` and `angle` |
| `glm_universal/runtime/session.py` | modified | two new solvers (`_solve_report`, `_solve_angle`) + four report helpers |
| `glm_universal/runtime/tct_engine.py` | modified | five new templates (report_relations, report_leech, report_theta, report_subalgebra, angle) |
| `glm_universal/reasoning/moonshine.py` | new | Moonshine layer: graded dimensions + j-function + Leech-to-Moonshine bridge |
| `glm_universal/reasoning/niemeier.py` | new | 23 Niemeier lattices: ADE root systems + deep-hole types |
| `glm_universal/reasoning/llvq.py` | new | LLVQ: codebook-free angular search over Leech shells |
| `glm_universal/reasoning/fwht.py` | new | FWHT: O(N log N) Walsh-Hadamard transform |
| `glm_universal/reasoning/valorani.py` | new | Valorani's SVD: Buckingham-Pi via rational nullspace |
| `glm_universal/tests/test_directive.py` | new | 31 tests for the five directive modules |
| `glm_universal/README.md` | modified | v0.6.0 status + new modules documented |
| `glm_universal/substrate/README.md` | modified | notes on the multi-MOG-cube and theta_series |
| `glm_universal/data_objects/README.md` | modified | encoding lessons learned |
| `glm_universal/reasoning/README.md` | modified | new modules documented |
| `glm_universal/runtime/README.md` | new | the runtime query kinds (now 13) |
| `glm_universal/tests/README.md` | new | the test suite structure |
| `glm_universal/examples/README.md` | new | the example scripts |
| `README.md` (this file) | modified | v4.0 changelog + this section |


============================================
GLM-3+ v0.7.0 — completion + information loss at boundaries (22 Aug 2026)
============================================

Two pieces of work: finishing the shipped package so the whole suite
runs, and turning the layered-projection paragraph at the top of this
README into something measured and machine-checked.

### 1. The package now runs end to end

The distributed `glm_universal_v0.6.zip` did not contain `GLM.py`, even
though this README documents it and `test_runtime.py` imports it.  Thirty
CLI tests errored on collection.  `GLM.py` has been written against the
behaviour those tests specify:

* batch mode (`-q`, `--query-file`, stdin) and `--interactive`;
* `-d/--domain`, `-c/--columns`, `-f/--format` (`text`/`json`),
  `--list-domains`, `--export-trace`, `--check-script-exactness`,
  `--verify-tct`, `--no-banner`;
* meta-commands `:help :domains :basis :columns :verify :history
  :snapshot :export :quit`;
* exit codes 0 (all answered), 1 (a query failed), 2 (usage error).

With it in place: **610 passed, 5,877 subtests, zero failures** — the
count this README already claimed.

### 2. `reasoning/information_loss.py` — the thesis, measured

The README's layered-projection paragraph says each layer is *true from
its limited perspective and works to that degree of implementation then
becomes untrue when the next dimension layer is required to take over*.
`dimension_layers.py` asserts the five layers exist.  This module
measures where each one's range actually ends, from one relation:

> two carriers are **indistinguishable at a layer** when that layer's own
> `measure` reports distance 0 between their views.

Everything is derived from it, in exact `Fraction` arithmetic, with no
float constructed anywhere:

| Function | What it answers |
|---|---|
| `classes`, `resolution`, `loss_count` | how much a layer can tell apart, and how much it loses |
| `boundary(lower, higher, carriers)` | the pairs the lower layer conflates and the higher splits — the information lost, listed |
| `refinement_violations` | the pairs the *lower* layer splits and the *higher* conflates — holes in the ladder |
| `congruence_witness`, `is_congruent` | whether a law (by default, composing concepts by adding exponents) can be computed from what a layer sees |
| `capacity` | the pigeonhole bound — only the substrate is finite, at 2²⁴ |
| `information_loss_report` | all of the above, recomputed on demand, never quoted |

Views are memoised per layer and carrier, because the rational layer's
`perceive` runs a Leech nearest-point decode; the cache is an
optimisation only and is tested to be one.

### 3. The runtime subject: `report information loss`

```
$ python3 GLM.py -q "report information loss"
```

Answers with four steps (resolution, boundary, reach of the law,
refinement audit) and a column-3 script that recomputes the entire study
in a fresh interpreter and asserts it key by key.  Aliases: `report
loss`, `report boundaries`.

Measured on the fixed five-carrier set:

| Layer | resolves | loses | addition descends |
|---|---|---|---|
| substrate | 3 / 5 | 2 | no |
| integer | 3 / 5 | 2 | no |
| rational | 5 / 5 | 0 | **yes** |

| Boundary | pairs lost | is a refinement |
|---|---|---|
| substrate → integer | 2 | **no** |
| integer → rational | 3 | yes |

### 4. Audit finding: the substrate → integer step is not a refinement

`refinement_chain_intact` comes out **False**.  The substrate perceives a
24-bit parity view, so it separates a unit on coordinate 10 from the
vacuum.  The integer layer perceives only the seven SI7 exponents, so it
conflates them.  Escalating therefore destroys a distinction the layer
below already had — which is the one thing the layered-projection thesis
does *not* allow, since a higher perspective is supposed to see at least
as much as the one it supersedes.

Closing it means either widening the integer layer's view beyond the
seven SI exponents, or narrowing the substrate's parity view to the same
coordinates.  It is left open and reported rather than silently patched,
because which of the two is right is a design decision about what the
integer layer is *for*.

> **Correction (v4.2).**  The finding above is accurate as of v0.7.0 and is
> kept for the record, but it is **no longer the state of the system**.  The
> design decision it left open was taken: the first of the two options.
> `dimension_layers.LAYER_INTEGER` is now **cumulative** — escalating to it
> adds the seven SI7 exponents to everything the substrate could already tell
> apart, rather than replacing one view with the other — so it refines the
> layer below it by construction and `refinement_chain_intact` now comes out
> **`True`**.  The rejected non-cumulative reading is kept beside it as
> `LAYER_INTEGER_RAW`, outside `LAYERS` so nothing escalates through it, and
> `information_loss.non_cumulative_report()` measures exactly what it costs
> (resolution 4/7 instead of 5/7, two violating carrier pairs).  Keeping the
> rejected reading measurable is the point: the repair is checked against the
> alternative rather than asserted.  The Lean counterpart is
> `RequestProject/GLM/Cumulative.lean`.  The measured layer table on the
> current seven-carrier set is substrate 3/7, integer 5/7, rational 7/7,
> griess 7/7, universal 7/7, with addition descending from the rational layer
> up.  The five-carrier tables above are the v0.7.0 run and are superseded.

### 5. The Lean 4 development — `RequestProject/GLM/`

The same definitions, proved rather than measured.  Compiles with no
`sorry`; the key theorems depend only on `propext`, `Classical.choice`
and `Quot.sound`.

| File | Contents |
|---|---|
| `Constants.lean` | `Y = 1/(π + 2/π)` with `1/4 < Y < 1/2`, `Q = Y + 1/8`, TAX, NRCI, the four coherence regimes, and the proof that the NRCI bands are exactly the TAX bands 5/2, 10, 70/3 |
| `TaxConservation.lean` | `tax(a XOR b) + 2·tax(a AND b) = tax a + tax b` exactly on binary carriers; its failure on naturals; and that repairing it for `(1,2)` would require the false `Y = 1/2` |
| `Layers.lean` | the abstract theory: `Layer`, `Indist`, `Refines`, `Visible`, `Boundary`, `CongruentOn`, `capacity`, `resolution`, `lossCount`, `Stack`, `escalate` — with `boundary_nonempty_iff_new_visible` (loss = new expressive power), `descends_iff_congruent` (the exact content of `can_multiply`), `exists_indist_of_capacity_lt` (capacity forces loss), and `escalate` proved correct and minimal |
| `Tower.lean` | the "this continues" half: an unbounded dyadic tower of layers, cumulative (`dyadic_refines_of_le`), with a strict gain in expressive power at **every** step (`dyadic_boundary_nonempty`, `dyadic_new_visible`), no final layer (`dyadic_not_lossless`), and every distinction eventually made (`dyadic_separates`) |
| `Stack.lean` | the concrete substrate/integer/rational stack over ℚ: refinement chain, non-empty boundaries, the operational boundary where addition stops descending, resolutions 2/3/4 and loss counts 2/1/0, and worked escalations |
| `GolayBoundary.lean` | unique nearest codeword at Hamming distance ≤ 3 for any minimum-distance-8 code, two nearest codewords at distance 4, and that 3 is exactly the largest radius at which repair is a function |

The write-up tying the two halves together is `INFORMATION_LOSS_STUDY.md`
at the repository root.

### 6. Test count

| File | v0.6.0 | v0.7.0 |
|---|---|---|
| `test_substrate.py` | 96 | 96 |
| `test_data_objects.py` | 177 | 177 |
| `test_reasoning.py` | 94 | 94 |
| `test_runtime.py` | 181 | 181 |
| `test_semantic_lexicon.py` | 39 | 39 |
| `test_physics_expansion.py` | 9 | 9 |
| `test_physics_expansion_v2.py` | 5 | 5 |
| `test_semantic_lexicon_runtime.py` | 21 | 21 |
| `test_lexicon_subspaces.py` | 12 | 12 |
| `test_substantive.py` | 23 | 23 |
| `test_wiring.py` | 23 | 23 |
| `test_directive.py` | 31 | 31 |
| `test_information_loss.py` (new) | — | 42 |
| **Total** | **610** | **652 passed, 5,877 subtests, zero failures** |

### 7. Files added or modified (v0.7.0)

| File | Status | Purpose |
|---|---|---|
| `GLM.py` | new | the CLI the package was shipped without |
| `glm_universal/reasoning/information_loss.py` | new | loss at the layer boundaries, measured |
| `glm_universal/reasoning/__init__.py` | modified | exports the new module |
| `glm_universal/runtime/session.py` | modified | `_report_information_loss` + the new subject and its aliases |
| `glm_universal/runtime/tct_engine.py` | modified | the `report_information_loss` column-3 template |
| `glm_universal/tests/test_information_loss.py` | new | 42 tests |
| `RequestProject/GLM/*.lean` | new | the machine-checked development (`Constants`, `TaxConservation`, `Layers`, `Tower`, `Stack`, `GolayBoundary`) |
| `INFORMATION_LOSS_STUDY.md` | new | the study |
| `TopLevel_README.md` (this file) | modified | v4.1 changelog + this section |

---

============================================
GLM 3+ 22 August 2026
============================================

# GLM-3+ v0.8.0 → v1.0.0 — the `glm_universal` package completed

**Version 4.2 of this README.**  The four rounds of work below take
`glm_universal` from v0.7.0 to **v1.0.0**.  The theme is the same
throughout: *every mechanism the package contains should be reachable
from a query, every published number should be recomputed rather than
quoted, and every failure should be reported rather than hidden.*

Test count over the four rounds: 652 → **1,041 passed, 6,099 subtests,
zero failures**.  Per-file counts are in
`glm_universal/tests/README.md`.

---

## 1. v0.8.0 — the substrate finished, and three reasoning layers wired

### `substrate/golay_decode.py` — honest decoding

The legacy substrate *snapped*: scan the 4,096 codewords, keep the
nearest, break ties arbitrarily.  Fast, almost always right, and its two
failure modes were silent.  The replacement is a syndrome/coset
construction that makes both explicit:

* the full coset table — 4,096 cosets, 12,951 minimum-weight leaders,
  distributed `{0:1, 1:24, 2:276, 3:2024, 4:1771}`;
* **covering radius 4 > packing radius 3.**  Each of the 1,771 weight-4
  cosets has **six** leaders — the six tetrads of a sextet.  Decoding
  there is a choice, not a deduction, so `decode_complete` returns
  `ambiguous` and `decode_or_detect` refuses;
* **weight-5 miscorrection is a theorem, not a bug.**  By `S(5,8,24)`
  every 5-set lies in a unique octad, so a weight-5 error sits at
  distance 3 from the wrong codeword and 5 from the right one.  Every
  nearest-codeword rule is unique, confident and wrong there.  The
  remedy is a declared channel radius, which is what `guaranteed`
  exposes.

Reachable as `report golay decoding`.

### `substrate/leech_construct.py` — the A/B/C ladder

| Level | Conditions | min norm² | kissing |
|---|---|---|---|
| A | mod-2 Golay support | 16 | 48 |
| B | + mod-4 even parity | 32 | 98,256 |
| C | + the mod-8 sum condition and the odd glue coset | 32 | **196,560** |

`necessity_report()` drops each condition in turn and shows the packing
break it causes, so no condition is decoration.  The result agrees with
the independently built `leech2` module.  Reachable as `report leech
construction`.

### `substrate/isomorphism.py` — the legacy ↔ canonical bridge

The permutation is an **isometry** (so decoding commutes with the frame
change — proved in Lean as `decoding_commutes`) but is **not** a Golay
automorphism: 4,088 of the 4,096 canonical codewords leave the code
under it, and the two codes share exactly **8** codewords.  Reachable as
`report migration`.

### Three new reasoning layers

* `reasoning/facets.py` — the six-facet partition of the 24 coordinates:
  strictly linear, mutually orthogonal, none redundant.  `report facets`.
* `reasoning/monster_stack.py` — the ten-plane 2-adic stack; 5 planes
  compose strictly, 8 with pair repair.  `report monster stack`.
* `reasoning/multires.py` — the `F₂⁴ ↔ GF(4) × Z₄` fibration, column
  sub-lattices, cross-level inner and tensor products, and the
  scale-invariance boundary with its census collision.
  `report multiresolution`.

### The `task` query kind

`reasoning/tasks.py` runs three worked end-to-end tasks — `task grid`
(a grid transformation found, not guessed), `task physics` (a derivation
audited plane by plane), `task concepts` (a labelled walk through the
concept-relation graph).

---

## 2. The cumulative-layer repair

v0.7.0's audit finding was that the substrate → integer step was **not**
a refinement: escalating one step destroyed a distinction the layer
below already had.  Section 4 of the v0.7.0 write-up above left the fix
open as a design decision.  It has been taken.

`LAYER_INTEGER` is now **cumulative**: its view is the seven SI7
exponents *together with* everything the substrate could already tell
apart.  A cumulative layer refines the one below it by construction, so
`refinement_chain_intact` is now **`True`**.

The discarded reading is not deleted.  `LAYER_INTEGER_RAW` keeps the
exponents-only view, outside `LAYERS` so nothing escalates through it,
and `information_loss.non_cumulative_report()` measures what it costs:
resolution 4 of 7 instead of 5 of 7, and two violating carrier pairs.
The claim "cumulative layers repair the chain" is therefore *checked
against the alternative* rather than asserted.

`RequestProject/GLM/Cumulative.lean` proves the general statement:
`cumulative L M` refines both `L` and `M`, is the **coarsest** layer that
does, gains exactly what the new reading sees, and a tower built this way
is a refinement chain by construction.  It also proves both halves of the
concrete case — that the exponents-only reading has the hole, and that
the cumulative integer layer does not.

Measured now, on the fixed seven-carrier set:

| Layer | resolves | loses | addition descends |
|---|---|---|---|
| substrate | 3 / 7 | 4 | no |
| integer (cumulative) | 5 / 7 | 2 | no |
| rational | 7 / 7 | 0 | **yes** |
| griess | 7 / 7 | 0 | yes |
| universal | 7 / 7 | 0 | yes |

---

## 3. The literal state migration — `glm_universal/migration/`

The repository's *actual persisted state* — `arc_agi_17/results/glm_state.json`
and its companions — brought into the package exactly, with nothing
re-derived from a model and nothing invented.

`frames.py` settles by computation which frame and bit order the stored
data uses.  Two findings, both surprising and both load-bearing:

* the stored concept vectors are **already in the canonical frame**, so
  the shipped `LEGACY_TO_CORE` permutation must *not* be applied to them
  — applying it would have silently corrupted 4,282 records;
* the stored integer addresses **are** MSB-first and do need the bit
  reversal.  `RequestProject/GLM/Endianness.lean` proves that the two
  readings differ exactly by `Fin.revPerm`, so fixing the frame recovers
  the code without altering a stored bit.

`state.py` performs the migration: **4,282 concepts and 4,014 CRG edges**
in canonical form, plus **398 carriers minted deterministically** for
names the source referred to but never defined — labelled apart from the
records that were really there.  `verify_canonical` re-derives every
field from the masks alone.  Output: `arc_agi_17/results/glm_state_canonical.json`.

`store.py` is the consumer: labelled paths through the concept-relation
graph, Hamming neighbourhoods in the substrate, and the cross-links where
a CRG concept is also a register carrier — 4,680 concepts indexed, 857
asserted edges and 3,157 auto-proposed, 2,186 isolated.

A negative result is reported with the rest: **graph distance and Hamming
distance do not agree.**  Proximity in the substrate is not proximity in
the concept graph, and the store says so rather than implying otherwise.

Reachable as `report state migration`, `report concept store`, and
`task concepts`.

---

## 4. v1.0.0 — the last wiring gaps closed

### `glm_universal/benchmarks/` — the reserved package, implemented

The directory existed as a scaffold marked "RESERVED — not yet
implemented".  It now holds a harness that enforces, in code, the
contract it was reserved under:

* a suite **cannot report a score without a declared evidence tier**;
* a suite **cannot report a float** — every score is an exact `Fraction`;
* a suite **cannot report only its wins** — findings, including null and
  negative results, are part of the score object, not a footnote.

Five suites, 2,390 scored tasks, each against a published baseline:

| Suite | Score | Baseline |
|---|---|---|
| `physics_equations` | 29 / 30 | 20 / 30 |
| `golay_correction` | 2,325 / 2,325 | 1 / 2,325 |
| `analogy_chemistry` | 9 / 12 | 3 / 12 |
| `analogy_semantic` | 5 / 10 | 0 / 10 |
| `analogy_physics` | 12 / 13 | 0 / 13 |
| **overall** | **2,380 / 2,390** | |

Every suite beats its baseline.  Eight findings are reported beside the
numbers, and four of them are failures:

* **10,626 of 10,626 weight-4 patterns are ambiguous** — one past the
  packing radius the nearest codeword stops being unique.  The decoder
  returns all six rather than picking one.
* **42,504 of 42,504 weight-5 patterns decode to a unique, wrong
  codeword** — the `S(5,8,24)` theorem again.  A null result for
  correction beyond the radius, reported as one.
* **EXT10 refuses `angular_momentum = momentum * length`.**  This is the
  basis boundary, not an arithmetic error: EXT10 carries plane angle as a
  dimension, so angular momentum is `L² M T⁻¹ A⁻¹` while momentum times
  length is `L² M T⁻¹`.  The identity is *true in SI7 and false in
  EXT10* — exactly the layer handoff the information-loss study
  describes, showing up unbidden in a benchmark.
* **Reciprocal relations are outside the additive analogy model.**
  `length : wavenumber :: time : frequency` fails because the solver
  models an analogy as a fixed displacement, and length-to-wavenumber is
  an inversion.  No amount of tuning inside the model reaches it.

Results are written as data into `glm_universal/benchmarks/results/`.
Reachable as `report benchmarks`, and runnable directly:

```bash
PYTHONPATH=. python3 -m glm_universal.benchmarks --write
PYTHONPATH=. python3 GLM.py -q "report benchmarks" -c 1
```

### `GeometricSession.solve(query, raw=None)`

`ask()` used to be the only way in, so a parsed `Query` could not be
edited and re-run without rebuilding the surface string.  `solve` is now
public and `ask` parses and delegates to it.

### The `pi_groups` query kind

`valorani.buckingham_pi_groups` was implemented in v0.6.0 and reachable
from nothing.  It is now a query kind:

```
$ python3 GLM.py -q "pi groups force, mass, acceleration, length, time"
```

The dimensionless groups of a set of quantities, from the exact rational
nullspace of their EXT10 exponent matrix — rank 3, two Pi groups for that
input — with each group checked dimensionless in all ten axes and a
column-3 script that reproduces the computation.

### Package surface

`glm_universal.__version__` is now `"1.0.0"`, and `migration` and
`benchmarks` are exported from the package root alongside `substrate`,
`data_objects`, `reasoning` and `runtime`.  `benchmarks` resolves lazily,
because a suite imports the runtime and the runtime's `report benchmarks`
solver imports the suites.

---

## 5. Status

Every module in `glm_universal` is reachable from a runtime query.  Every
mechanism the directive names has an implementation.  The README chain
runs unbroken from this file to each sub-package.

What remains is mathematical extension rather than wiring, and is listed
in `glm_universal/README.md` under "What is left": deep-hole finding via
the Leech Voronoi cell, an O(1) LLVQ lookup table, FWHT inside the
substrate group actions, the VOA state-field map, multi-domain analogy,
words as projections of physics concepts, the `sr` unit-parser case, and
a general molecules domain.

Three known model boundaries are recorded rather than hidden: the
additive analogy model cannot express inversions; the coordinatewise
carrier-space product converges to "velocity" for all word pairs; and 36
of the 222 scalar relations that a units table gets right are wrong once
tensor rank and parity are included — which is a result, not a failure.

---

============================================
GLM-3+ v1.1.0 — semantics: meaning as the thing that gets encoded (22 Aug 2026)
============================================

The v1.0.0 package was feature complete in the sense that every mechanism it
named was implemented and reachable.  This round asks a different question:
when the system encodes `water`, what is it encoding?  The answer, for the
inherited ARC-era concept graph, turned out to be *the spelling* — and the
correction is the seventh sub-package, `glm_universal/semantics/`.

```bash
# from the repository root, where GLM.py lives
PYTHONPATH=. python3 GLM.py -q "meaning of water"
PYTHONPATH=. python3 GLM.py -q "relate energy torque"
PYTHONPATH=. python3 GLM.py -q "report semantics" --verify-tct
PYTHONPATH=. python3 glm_universal/examples/semantic_replacement.py --no-write
```

## 1. The finding, measured rather than asserted

`arc_agi_17/results/glm_state.json` holds 4,282 concepts and 4,015 edges.  The
carriers in it were made by hashing a name — `sha256(name)` truncated to 24
bits and snapped to a Golay codeword — and most of the edges were made by
measuring distances between those carriers.  `semantics/audit.py` measures what
that leaves:

| Measurement | Result |
|---|---|
| Concepts that denote anything determinate | **83 / 4,282** |
| Edges stating a re-derivable relation between two determinate referents | **2 / 4,015** |
| Edges that are carrier-proximity artefacts | 3,157 |
| Edges with at least one endpoint denoting nothing | 815 |
| Edges recording a pipeline event rather than a relation | 39 |
| Mean legacy Hamming distance, semantically related pairs | 4547/376 ≈ 12.09 |
| Mean legacy Hamming distance, unrelated pairs | 12077/1009 ≈ 11.97 |
| Two random 24-bit words | 12 |
| Notations for one subject, mean legacy Hamming between them | 359/30 ≈ 11.97 |
| The same pairs in the meaning space | **0** |

The related and unrelated means sit either side of the random-word expectation
of 12.  That is what "no signal" looks like when it is measured.  The
contingency table says the same thing without averaging: of 3,403 pairs of
grounded concepts, 376 are semantically related, 2 of those are adjacent under
the stored carriers, and 2 pairs are adjacent without being related.

## 2. What replaces it

| Module | What it is |
|---|---|
| `semantics/meaning.py` | the meaning space — six kinds of determinate content (`number`, `dimension`, `quantity`, `element`, `compound`, `operation`) encoded as 24 exact rationals, with an exact round trip and injectivity.  `encode` takes a meaning and nothing else, so no spelling can reach the carrier. |
| `semantics/reference.py` | nine resolvers, notation → meaning or an explicit refusal with a reason.  1,705 notations resolve.  A term two resolvers would answer differently is **ambiguous** and is refused: resolver order is not a tie-break. |
| `semantics/relations.py` | 15 binary and 4 ternary relations, each derived from the meanings and carrying the arithmetic that makes it true. |
| `semantics/graph.py` | the grounded graph: 357 meanings, 1,705 notations, 63 refused terms, 6,210 binary and 6,649 ternary edges — 12,859 in all, every one re-derived on demand (`all_verified = True`). |
| `semantics/audit.py` | the measurements in section 1, and the purge plan: 2 edges retained, 4,013 dumped, each with a stated reason. |
| `semantics/export.py` | the graph and the purge plan written out as documents beside the inherited state file, which is read and never written. |

## 3. Runtime surface added

| Query | Answers |
|---|---|
| `meaning of <term>` | what the notation denotes, its 24-coordinate meaning carrier, and the round trip.  A term with no determinate referent is refused **with its reason**. |
| `relate <a> <b>` | every relation derivable between the two meanings, each re-checked from the meanings alone. |
| `report semantics` (aliases `report meaning`, `report grounding`) | the whole audit above and the grounded graph that replaces it, with a column-3 script that recomputes it in a fresh interpreter. |

`meaning` is the fifteenth query kind and `semantics` the sixteenth report
subject.  Worked answers:

```
meaning of water        →  'water' denotes compound Z1_2 Z8
relate energy torque    →  si7_conflates: EXT10 separates them
                           (L² M T⁻² vs L² M T⁻² A⁻¹) and SI7 does not
report semantics        →  83 of 4282 inherited concepts denote anything
                           determinate; 2 of 4015 inherited edges survive;
                           the grounded graph has 357 meanings and 12,859
                           re-derived edges          [VERIFIED True]
```

## 4. The Lean development, extended

`RequestProject/GLM/Semantics/Meaning.lean` and `Grounding.lean` bring the
machine-checked companion from eleven files to thirteen, still with no `sorry`:

* `decode_coords` and `coords_injective` — the meaning carrier round-trips and
  separates distinct well-formed meanings, so the encoding loses nothing;
* `formula_capacity_collision` and `capacity_forces_refusal` — past five
  formula slots two distinct meanings share a carrier, so refusal is the only
  honest option, which is what the codec does;
* `semantic_iff_respects` and `spelling_not_semantic` — a map is a function of
  meaning exactly when it agrees on co-denoting notations, and a
  spelling-derived one is not, whatever it computes;
* `legacy_threshold_dichotomy` — **no** proximity radius on the legacy carriers
  recovers synonymy: every radius either splits a synonym pair or relates every
  notation to every other.  The audit's numbers are one instance of a theorem;
* `si7_conflates_energy_torque` with `exists_visible_dim_not_si7` — the
  EXT10 → SI7 step is a boundary in the sense of `Layers.lean`, and energy
  against torque is the witness.  The information-loss study and the semantics
  layer meet here.

## 5. Version bump and the README chain

* `glm_universal.__version__` is `1.1.0`; `semantics` is exported from the
  package root alongside the other six sub-packages.  Both are pinned by
  `test_wiring.py::TestPackageSurface`, so a future bump is not complete until
  the test agrees with `__init__.py`.
* `tests/README.md`, `examples/README.md` and this file now state the package
  as it is: 1,094 tests across 23 files, 15 query kinds, 16 report subjects,
  seven sub-packages, thirteen Lean files.
* Three defects in the example scripts were fixed rather than documented
  around: `encoding_poc.py` and `scaled_carriers.py` resolved
  `data_objects/_data/elements_118.json` from the `examples/` directory instead
  of the package root and could not start, and `scaled_carriers.py` formatted
  an exact `Fraction` with a float format spec, which raises on Python 3.11.
  It now renders through `coherence.decimal_str`, which never constructs a
  float.  All six example scripts run.

## 6. Test count

| | tests | subtests |
|---|---|---|
| v1.0.0 | 1,041 | 6,099 |
| v1.1.0 | **1,094** | **6,331** |

`test_semantics.py` adds 52 of the 53: the meaning space and its round trip,
notation invariance across numeral / word / Roman numeral / arithmetic /
formula / register name, refusal with a reason for the ungrounded and the
ambiguous, every derived relation re-verified, the grounded graph, the audit,
the written documents, and both runtime surfaces end to end with column-3
verification.  The remaining one is the version-surface test above.

---

============================================
GLM-3+ v1.2.0 — infinite values: a carrier is finite, a process is not (23 Aug 2026)
============================================

v1.1.0 asked what a term *denotes*. This round asks what happens when what it
denotes will not fit: `sqrt(2)`, `pi`, and every other value a 24-coordinate
rational carrier cannot hold. The answer is the value layer —
`glm_universal/reasoning/exact_real.py` and `real_expr.py` — and the map of
where it stops, `glm_universal/capabilities/`.

```bash
# from the repository root, where GLM.py lives
PYTHONPATH=. python3 GLM.py -q "approximate sqrt(2) to 20 places"
PYTHONPATH=. python3 GLM.py -q "approximate (1+sqrt(5))/2 to 12 places"
PYTHONPATH=. python3 GLM.py -q "is pi less than 355/113" -c 2
PYTHONPATH=. python3 GLM.py -q "report infinite values" -c 1
PYTHONPATH=. python3 GLM.py -q "report capabilities" -c 1
PYTHONPATH=. python3 -m glm_universal.capabilities
```

## 1. The claim, in one line

> A carrier is finite. A process is not. The GLM holds an irrational as the
> process, not as the carrier — and the process is a first-class object it can
> add, multiply, compare, print, refine and refuse.

Three things had to be true, and each is now proved or measured:

| Claim | Status |
|---|---|
| No finite carrier holds an irrational — the wall is real | **Proved** (`no_countable_layer_lossless`, a cardinality argument) |
| Every real *is* reached, as the limit of a finite carrier that moves | **Proved** (`dsAverage_error_le`, `dsAverage_tendsto`) and measured |
| The moving carrier is bounded by geometry in 24 dimensions | **Proved** (`avgVec_mem_hull`, `not_tendsto_avg_of_separating`) and certified in exact arithmetic |

## 2. Reals as processes

`reasoning/exact_real.py` holds a real as a rule: `x.at(k)` returns an exact
`Fraction` within `2**-k` of the value, for any `k`. No float is constructed
anywhere in the module, and there is no ceiling on `k` but time.

```
sqrt(2) = 1.41421356237309504880      root(3, 2) = 1.25992104989487316476
pi      = 3.14159265358979323846      e          = 2.71828182845904523536
phi     = 1.61803398874989484820
```

The dyadic tower's level `n` holds `floor(x*2^n)/2^n` — a *stand-in*,
indistinguishable from the target at that resolution and exposed by a higher
level. For `sqrt(2)`:

```
stand-ins:         1, 1, 5/4, 11/8, 11/8, 45/32, 45/32, 181/128
exposed at level:  0->2, 1->2, 2->3, 3->5
```

No stand-in squares to 2 at any level — and yet the tower *as a whole* is
faithful (`towerView_injective`). What is lost is lost at every single level
and at no level of the whole: exactly the layered-projection thesis at the top
of this README, now with a value rather than a claim in the place where the
handover happens.

## 3. Written arithmetic

`reasoning/real_expr.py` reads ordinary written expressions over those
processes — `+ - * /`, integer powers, brackets, `sqrt`, `cbrt`,
`root(degree, x)`, the constants `pi`, `e`, `phi`, and any rational or decimal
literal:

```
(1+sqrt(5))/2   = 1.61803398874989484820     (agrees with phi to 2**-58)
sqrt(2)+sqrt(3) = 3.14626436994197234232
pi/4            = 0.78539816339744830961
0.1+0.2         = 3/10, exactly
```

A decimal literal is read as the rational it names, so `0.1+0.2` is *exactly*
`3/10` and never `0.30000000000000004`.

Division is the interesting case: `1/x` is computable only from a bound
`|x| >= 2**-m`, and no algorithm produces that bound for an arbitrary process,
because doing so would decide whether the process is zero. So `divide` searches
for the witness to `WITNESS_DEPTH = 96` and refuses beyond it, naming the
depth. `1/(sqrt(3)-sqrt(2))` goes through and equals `sqrt(3)+sqrt(2)`;
`1/(sqrt(2)-sqrt(2))` is refused.

### 3a. Past the algebraic operations

`reasoning/transcendental.py` adds `exp`, `log` (natural, or `log(base, x)`),
`sin`, `cos`, `tan` and a non-integer exponent, on the same footing as the
rest — exact rational arithmetic throughout, no float constructed anywhere,
and a stated error budget for each:

```
exp(1)   = 2.71828182845904523536      log(2)  = 0.69314718055994530941
sin(1)   = 0.84147098480789650665      cos(1)  = 0.54030230586813971740
tan(1)   = 1.55740772465490223050      2^pi    = 8.82497782707628762385
2^(1/3)  = 1.25992104989487316476      log(2, 8) = 3.00000000000000000000
```

`2^(1/3)` and `root(3, 2)` agree, as they must. The budgets are the Lipschitz
bounds of `RequestProject/GLM/Transcendental.lean`: `exp` costs a factor
`exp(max x a)`, `sin` and `cos` cost one extra bit each, and `log` costs
`1/c` for a lower bound `c` on its argument — which is why it needs a
**positivity witness**, exactly as division needs a nonzero one.
`log(sqrt(2)-sqrt(2))` is refused with its depth named; `x^y` inherits the
refusal through `x^y = exp(y*log x)`, so `2^pi` is computable and `0^pi` is
not. The inverse and hyperbolic family (`asin`, `atan`, `sinh`, `erf`,
`gamma`, `zeta`, …) is refused by an explicit list, so the message names the
missing function rather than failing to parse.

## 4. The carrier that moves, and the hull that bounds it

The one-dimensional delta-sigma modulator chases the target with an exact error
accumulator: after `N` ticks its time average is a rational `k/N` within `1/N`
of the target — a theorem (`GLM.Info.dsAverage_error_le`), reproduced at
`N = 10, 100, 1000`. So a one-bit carrier reaches *every* real in the limit,
and `N` ticks carry `log2(N+1)` bits of resolution.

In 24 coordinates the loop quantises to Golay codewords, and that is what
bounds it:

| target | result |
|---|---|
| all-½ (inside the hull) | deviation **0**, using two codewords |
| `sqrt(2)-1` in all 24 coordinates | tracked to within `1/N` |
| the ramp, coordinate `i` holds `i/24` | deviation `19/300` after 200 ticks and not shrinking; accumulator excursion `311/24`, growing linearly |

The ramp is not a tuning failure. Every emitted state is a codeword, so every
reading is a convex combination of codewords (`avgVec_mem_hull`) and every
limit lies in their convex hull; the ramp target is outside it, and
`hull_certificate` returns a single linear functional that puts the target
strictly above all 4,096 codewords with gap **13/5760**. With
`not_tendsto_avg_of_separating` that turns into "no run of any quantiser rule
converges here". The complement, `avgVec_periodic`, says a carrier cycling
through `N` states reads back exactly the mean of its cycle — so the reachable
set is pinned from both sides: the hull, and nothing but the hull.

Only a larger emitted alphabet changes that. Nothing about the decoder does.

## 5. The runtime surface added

| Query | Answers |
|---|---|
| `approximate <expr> to <n> places` | the value to `n` places, with the plain statement that no carrier holds it |
| `is pi less than 355/113`, `compare sqrt(2) and 1.5`, `which is bigger e or pi` | the order, and the precision that settled it (`separated at 2**-32` for the first). Two sides that never separate come back "not distinguished at 2**-256": equality of two processes is not decidable, and the machine does not claim it |
| `report infinite values` | the whole value layer recomputed in a fresh interpreter and checked key by key |
| `report capabilities` | the 33 probes, run for real |

`real` and `compare` are the sixteenth and seventeenth query kinds;
`infinite values` and `capabilities` the seventeenth and eighteenth report
subjects.

## 6. The capability probes

`glm_universal/capabilities/` exists for one question: *where does it break?*
A probe states a capability in a user's words, declares beforehand whether it
is expected to hold, puts it to the real code, and reports the exact place the
capability stops.

**33 probes: 19 hold, 14 break, 0 errored, 0 surprises.**

A break is a success — the boundary has been located. Twelve of the fourteen
are theorems and will never move (the Golay repair radius of 3, the
undecidability of equality between processes, the convex hull above, the
non-associativity of the 2A product, the 25th coordinate). Two are work items:

* **the vocabulary is the registers** — 1,768 named terms, of which 66 are
  ambiguous and are refused rather than resolved by resolver order. There is no
  coordinate for 'justice', so widening the vocabulary means widening the
  registers, not the parser.
* **no arithmetic inside a description** — `what is energy` works,
  `what is energy divided by time` does not. Both halves of the machinery
  exist; no query kind joins them. *The largest single gap in the language
  layer, and a plumbing job rather than a mathematical one.*

A probe whose verdict differs from its declared expectation is reported as a
*surprise*, so a capability lost and a capability won are equally visible
instead of being buried in a diff. A third work item — *no transcendental
functions* — stood here until §3a was built; its probe now reports `holds` and
checks the identities rather than the refusal, which is the lifecycle a probe
is for.

## 7. The Lean development, extended

`RequestProject/GLM/DeltaSigma.lean`, `Irrational.lean`, `Reachable.lean`,
`Computable.lean` and `Transcendental.lean` take the machine-checked companion
from thirteen files to eighteen, still with no `sorry` and still depending on
nothing beyond `propext`, `Classical.choice` and `Quot.sound`:

* `dsAverage_error_le`, `dsAverage_tendsto` — the `1/N` law and its limit;
* `no_countable_layer_lossless`, `towerView_injective` — the wall, and the
  tower that is faithful although no level of it is;
* `avgVec_mem_hull`, `not_tendsto_avg_of_separating`, `avgVec_periodic` — the
  hull, the certificate, and exact reachability of a periodic carrier;
* `nonzero_iff_witness`, `inv_error_le`, `witness_depth_not_uniform`,
  `eq_of_forall_abs_sub_le` — what division needs, what it costs, why no fixed
  depth suffices, and why equality is refused while inequality is decided;
* `exp_error_le`, `sin_error_le`, `cos_error_le`, `log_error_le`,
  `pos_iff_witness`, `rpow_eq_exp_mul_log` — the error budget each
  transcendental function pays, the positivity witness as an equivalence, and
  the route a real power takes.

## 8. Test count

| | tests | subtests |
|---|---|---|
| v1.1.0 | 1,094 | 6,331 |
| v1.2.0 | **1,324** | **6,331** |

`test_exact_real.py` adds 90, `test_transcendental.py` 83 and
`test_capabilities.py` 56; the remaining one is the version-surface test. The
full write-up, including the work items with the exact line at which each
stops, is `INFINITE_VALUES_STUDY.md`.


============================================
GLM 3+ 25 August 2026
============================================

# GLM-3+ v1.2.0 — ambiguity as a value

```bash
# from the repository root, where GLM.py lives
PYTHONPATH=. python3 GLM.py -q "report superposition" -c 1
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_superposition.py -q
```

## 1. The question

`golay_decode` already reported a received word at distance 4 from the code as
`ambiguous` and stopped. That is honest, but it throws away a fact the geometry
knows: *how* it is ambiguous. This round builds the case out.

## 2. The shape of the tie

Proved in `Golay/Sextet.lean`, from exhaustive checks over all 4,096
syndromes: the code has minimum distance 8, a reading is unique up to error
weight 3, the covering radius is exactly 4, and a weight-4 coset has **exactly
six** nearest codewords, pairwise at distance 8, whose supports relative to the
received word partition the 24 coordinates into six tetrads. Every coset is
either uniquely readable or a six-fold tie — there is no third case.

## 3. Two bundles, and only one of them survives

| | F₂ bundle (XOR) | rational bundle (mean) |
|---|---|---|
| value on a six-fold tie | all ones, `16777215`, **always** | coordinates in `{1/6, 5/6}` |
| inputs distinguished (of 256) | **1** | **256** |
| invertible | no | yes, by `recover_from_bundle` |
| proved by | `bundleF2_eq_one`, `bundleF2_constant` | `bundleQ_eq`, `bundleQ_recover`, `bundleQ_injective` |

So the usual VSA bundling operation is exactly the wrong carrier for this kind
of ambiguity, and the reason is arithmetic, not implementation: six is even, and
each coordinate of a sextet tie is covered an even number of times.

## 4. Collapse, wobble, and the alphabet

`collapse(sup, context)` filters the members by a context predicate and reports
`collapsed` (one survivor), `superposed` (several) or `refuted` (none). It never
breaks a tie by member order, so it cannot present a guess as an answer.

`Wobble.lean` makes the same superposition a *moving* carrier: cycling through
the six readings, the time average is exactly the rational bundle
(`sextet_cycle_avgVec`) and still determines the tie. `HullExpansion.lean`
separates a target from the convex hull of the available states with the
functional `(7, −1, …, −1)` — value `7/2` at the target, `≤ 0` at every one of
the 4,096 scaled codewords — so no schedule reaches it, and then reaches it
exactly in a 16-tick cycle once two Leech vectors are admitted.

## 5. The runtime surface added

| Query | What it recomputes |
|---|---|
| `report superposition` | the sextet partition, both bundles, contextual collapse, and the alphabet-expansion certificate — four steps, column-3 verified |

## 6. The Lean development, extended

Eighteen files to twenty-three, still free of `sorry`: `Golay/Code.lean`,
`Golay/Sextet.lean`, `Superposition.lean`, `Wobble.lean`, `HullExpansion.lean`.
The exhaustive finite checks use `native_decide`, so they and their downstream
results depend on `Lean.ofReduceBool` and `Lean.trustCompiler` in addition to
`propext`, `Classical.choice` and `Quot.sound`.

## 7. Test count

| | tests | subtests |
|---|---|---|
| v1.2.0 | 1,324 | 6,331 |
| v1.2.0, extended | **1,363** | **6,331** |

`test_superposition.py` adds all 39. The full write-up is
`GEOMETRIC_AMBIGUITY_STUDY.md`.


---

# GLM-3+ v1.3.0 — the census, and what a perturbed carrier actually does

Everything in this section was recomputed here before it was written; the
recomputing functions are named beside each figure.

## 1. How often the tie happens

`substrate/superposition.py::coset_weight_distribution` builds the census from
the decoder's own coset table:

| distance to the code | 0 | 1 | 2 | 3 | 4 | total |
|---|---|---|---|---|---|---|
| cosets | 1 | 24 | 276 | 2,024 | **1,771** | 4,096 |

so **2,325** cosets are read uniquely and **1,771** are six-fold ties, and
`mean_coset_weight()` returns the exact `Fraction` **`3433/1024`**. The
packing radius is 3 and the covering radius is 4, so the *average* word is
already past the radius inside which the nearest-codeword reading is unique:
ambiguity is the typical case for this code, not a corner case. Machine-checked
in `RequestProject/GLM/Golay/Census.lean` (`coset_census`,
`unique_vs_ambiguous`, `mean_coset_weight`, `mean_coset_weight_gt_three`,
`mean_coset_weight_lt_four`); `coset_census_report()` checks the running figures
against the Lean ones and reports `census_agrees_with_lean` and
`mean_agrees_with_lean`.

## 2. Does a perturbed carrier settle there?  No

`coset_chain_report()` pushes the law over the 4,096 cosets forward exactly
(integer numerators over `24 ** n`; no float, no sampling), and
`RequestProject/GLM/Golay/Dynamics.lean` proves what it measures:

| finding | recomputed | proved |
|---|---|---|
| the uniform law is stationary, and is the only stationary law | `uniform_is_stationary` | `step_unif`, `stationary_unique` |
| its mean distance to the code is the census figure `3433/1024` | `stationary_mean_distance` | `expect_unif_cosetWt` |
| every parity-check column has odd parity | `columns_all_odd_parity` | `par_col` |
| so the chain is periodic — supports `24, 277, 2048, …`, parity class alternating — and is **never** uniform | `parity_alternates`, `law_never_uniform` | `iterate_dirac_ne_unif` |
| the stationary law keeps `301/4096` below the packing radius, so the weight does not lock on | — | `prob_unif_subcritical_pos` |
| the time average does settle: after 12 ticks the two-step average is `76017479/22674816`, within `5819/181398528` of `3433/1024` | `two_step_average_error` | (open — see below) |
| a corrected one-bit error returns the same codeword, so a corrected carrier stays *on* the code | `corrected_carrier_returns_to_code` | `perturb_correct_returns` |

The open point, stated exactly: Cesàro convergence of the time averages to the
uniform law is true but not proved here — it needs a quantitative mixing
argument (Doeblin minorisation for a power of the kernel, or Fourier analysis
on `(ZMod 2)¹²`) that Mathlib does not supply for a kernel of this shape. It is
recorded at the end of `Golay/Dynamics.lean`; nothing else depends on it.

## 3. Surface and counts

`report superposition` now has six steps (sextet, bundling, collapse, census,
chain, hull) and still returns `VERIFIED True` from its column-3 template.
Lean files 23 → **25**, still free of `sorry`. `test_superposition.py` 39 →
**61**; whole suite 1,363 → **1,385 passed, 6,331 subtests, zero failures**.


---

# GLM-3+ v1.3.0 — measuring the machine from outside

```bash
# from the repository root, where GLM.py lives
PYTHONPATH=. python3 -m glm_universal.evaluation --jobs 8
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_evaluation.py -q
```

## 1. Why a ninth sub-package

`capabilities/` asks the library where it stops. `benchmarks/` scores solver
functions. Neither goes through `GLM.py`, so neither measures what a user gets.
`evaluation/` does: **72 cases**, each starting the CLI in a **fresh
interpreter** — one subprocess per question, no shared session, no warm caches —
and scoring the `ANSWER` or `UNSOLVED` line the process prints. The question
set covers **all 18 query kinds** and **all 19 report subjects**, and a test
checks that coverage against the runtime's own tables, so a new kind or subject
cannot be added without a case.

## 2. The scoring is asymmetric

| outcome | weight | passes |
|---|---|---|
| `correct` | +1 | yes |
| `refused_as_expected` | +1 | yes |
| `unexpected_refusal` | 0 | no |
| `wrong_answer` | −1 | no |
| `error` | −1 | no |

A refusal tells the user where the machine stops; a confident wrong answer does
not. 11 of the 72 questions are ones the machine *should* refuse, each labelled
`boundary` (a theorem or a deliberate commitment) or `gap` (missing
implementation).

## 3. The result

**67 of 72 passed** — 57 answered correctly, 10 refused as expected, **0
unexpected refusals**, 5 confidently wrong, 0 errored. Every failure is in one
kind: `analogy`, 3/8. `report` is 20/20, `verify` 6/6, `describe` 6/6,
`meaning` 6/6, `real` 5/5, `compare` 4/4, and every other kind is at 100%.
The five analogy failures, each with the exact point at which it stops, and the
split of the expected refusals into 7 boundaries and 4 gaps, are written up in
`CAPABILITY_ASSESSMENT.md` together with the probe and benchmark totals
(33 probes: 19 hold, 14 break; 2,380/2,390 benchmark tasks across 5 suites).

## 4. A gap closed, before and after

`approximate 1/0 to 5 places` used to escape the CLI as an uncaught
`ZeroDivisionError` traceback — outcome `error`, weight −1. `_solve_real` and
`_solve_compare` now catch it and refuse, saying that a quotient by an exact
zero names no value — outcome `refused_as_expected`, weight +1. Evaluation
66 → **67 of 72**, errored cases 1 → **0**.

## 5. Surface and counts

`glm_universal.__version__` 1.2.0 → **1.3.0**, and `evaluation` is the ninth
sub-package, pinned in `test_wiring.py::TestPackageSurface`. Added
`tests/test_evaluation.py` (19 tests); whole suite 1,385 → **1,405 passed,
6,331 subtests, zero failures**.
