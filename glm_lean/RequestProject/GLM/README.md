# `RequestProject/GLM/` — machine-checked companion to the GLM package

**27 Lean files**, all building against Mathlib at `v4.28.0` — the
toolchain already pinned by `glm_lean/lean-toolchain` — and all free of `sorry`.
Every theorem below has been checked with `#print axioms`; none depends on
anything beyond `propext`, `Classical.choice` and `Quot.sound`, except the
finite exhaustive checks in `Golay/Sextet.lean` (and the results downstream of
them), which are discharged by `native_decide` and so additionally use
`Lean.ofReduceBool` and `Lean.trustCompiler`.

These files are *additive*. They live in a new `RequestProject/GLM/`
directory alongside the existing `RequestProject/GLM.lean`, `GLM2.lean` and
`GLM3.lean`, which they neither import nor modify. The existing lakefile
glob `RequestProject.+` already picks them up, so nothing needs configuring:

```bash
cd glm_lean
lake build
```

## What is proved, and why it is here

| file | subject | why the package cares |
|---|---|---|
| `Constants.lean` | `Y = 1/(π + 2/π)`, `Q = Y + 1/8`, `B = 10`; `TAX(v) = HW(v)·Y + ‖v‖²/8`; `NRCI(v) = B/(B + TAX(v))` | `nrci_eq_one_iff`: NRCI is in `(0, 1]` and equals `1` **exactly** at the zero carrier — perfect coherence is exactly the vacuum. Each coherence regime is shown to be equivalently a band of TAX. |
| `TaxConservation.lean` | `TAX(a ⊕ b) = TAX(a) + TAX(b) − 2·TAX(a ∧ b)` | Holds *exactly* for binary carriers, and `tax_conservation_fails_at_integer_layer` shows it fails one layer up. The first concrete instance of a law with a boundary. |
| `GolayBoundary.lean` | nearest-codeword reading in a minimum-distance-8 code | `snap_boundary_at_three`: unique for error weight ≤ 3, and at weight 4 there are patterns equidistant from two codewords. This is the boundary `snap_to_codeword` runs into, and the one the runtime reports as `ambiguous`. |
| `Permutation.lean` | coordinate permutations | A permutation is an isometry, so nearest-codeword decoding commutes with it. This is why a legacy→canonical *permutation* may be wrapped around a decoder while a general linear isomorphism may not. |
| `Endianness.lean` | bit order | `bitsMSB_eq_bitReverse_bitsLSB`: the MSB-first and LSB-first readings of a stored integer differ exactly by `Fin.revPerm`. Hence `endianness_is_a_frame_choice`: fixing the frame recovers the code without altering a stored bit, and no decoder guarantee is lost. This is the audit finding behind the literal data migration. |
| `Facets.lean` | the six facets | The facet projections are linear, idempotent, mutually orthogonal and complete, so `pythagoras` splits squared distance exactly across facets. This is what makes the runtime's facet attribution exact rather than heuristic. |
| `Sakuma.lean` | the 2A Sakuma product | `sakuma_not_associative`: the two bracketings of a pairwise-2A triple are `−3/32·e₂` and `−3/32·e₀`. The XOR label shortcut it replaced *is* associative, so the replacement was not cosmetic. |
| `Layers.lean` | the general theory | A layer is a `perceive` map. Refinement, visibility, boundary and congruence are derived from it. `boundary_nonempty_iff_new_visible`: information lost at a boundary is *precisely* new expressive power. `descends_iff_congruent` is the exact content of the `can_multiply` flag. |
| `Stack.lean` | the concrete GLM stack | substrate → integer → rational, with worked escalations and a measured loss count on a four-carrier region. |
| `Cumulative.lean` | how a stack is *made* a refinement chain | `cumulative L M` is the layer that keeps `L`'s reading and adds `M`'s. It refines both and is the coarsest layer that does (`refines_cumulative_iff`), what it gains is exactly what the new reading sees (`boundary_cumulative_left`), and a tower built this way is a refinement chain by construction (`cumulativeTower_refines_of_le`). The concrete model is the GLM's own case: `si7Model_not_refines_substrateModel` proves the hole the exponents-only reading has, and `integerModel_refines_substrateModel` that the cumulative integer layer — the one the package now ships — does not. |
| `Semantics/Meaning.lean` | the meaning space | `decode_coords` and `coords_injective`: the 24-coordinate meaning carrier round-trips and separates distinct well-formed meanings, so `semantics/meaning.py`'s encoding loses nothing. `encode_indep_of_notation`: an encoding that is a function of the meaning gives equal carriers to two notations of one subject — the property the spelling-hashed legacy carriers do not have. `formula_capacity_collision` and `capacity_forces_refusal`: past five formula slots two distinct meanings share a carrier, which is why the encoder refuses instead of truncating. |
| `Semantics/Grounding.lean` | meaning versus spelling, and the EXT10 → SI7 boundary | `semantic_iff_respects` and `spelling_not_semantic`: a map is a function of meaning exactly when it agrees on co-denoting notations, and a spelling-derived one is not, whatever it computes. `legacy_threshold_dichotomy`: no proximity radius on the legacy carriers recovers synonymy — every radius is either not semantic or trivially true of every pair. `si7_conflates_energy_torque` with `exists_visible_dim_not_si7`: the EXT10 → SI7 step is a boundary in the sense of `Layers.lean`, and energy and torque are the witness. |
| `DeltaSigma.lean` | the moving carrier | `dsAverage_error_le`: after `N` ticks the one-bit modulator's time average is within `1/N` of its target, and `dsAverage_tendsto` takes that to the limit — so a finite carrier that is allowed to move reaches *every* real, irrational included. This is the `1/N` law `reasoning/exact_real.py` reproduces at `N = 10, 100, 1000`. |
| `Irrational.lean` | the wall, and the tower that gets round it | `no_countable_layer_lossless`: a layer whose views form a countable set conflates two distinct reals, so no carrier holds an irrational — a cardinality argument, not an engineering limit. `towerView_injective`: what is lost at every single level is not lost by the tower as a whole. This is why a real is held as a process and its level-`n` stand-in `⌊x·2ⁿ⌋/2ⁿ` is only ever a stand-in. |
| `Reachable.lean` | what the 24-D carrier can hold | `avgVec_mem_hull`: every reading of the dynamic carrier is a convex combination of codewords, so the reachable set is inside the convex hull of the code. `not_tendsto_avg_of_separating`: a single linear functional separating a target from every codeword rules out convergence under *any* quantiser rule — the certificate the package computes for the ramp target. `avgVec_periodic` pins the set from the other side: a carrier cycling through `N` states reads back exactly the mean of its cycle. |
| `Computable.lean` | what is computable about an approximated value | `nonzero_iff_witness`: a real is nonzero **iff** a bound `|x| ≥ 2⁻ᵐ` exists, so that witness is precisely the information division needs; `inv_error_le` is the cost the implementation pays for it; `witness_depth_not_uniform` shows no fixed search depth works for every divisor, which is why `real_expr.divide` refuses by naming its depth. `eq_of_forall_abs_sub_le`: processes never separated are equal — but "never" quantifies over all precisions at once, which is why equality is refused and inequality is decided. |
| `Transcendental.lean` | the error budgets of `exp`, `log`, `sin`, `cos` and `x ^ y` | `exp_error_le`, `sin_error_le`, `cos_error_le` and `log_error_le` are the Lipschitz-style bounds `reasoning/transcendental.py` divides its precision among: the exponential's constant is `exp (max x a)`, the two trigonometric functions cost one extra bit, and the logarithm's constant is `1/c` for a lower bound `c` — which is why it needs a positivity witness. `pos_iff_witness` says such a witness is exactly what positivity is, the same shape as `nonzero_iff_witness` for division. `rpow_eq_exp_mul_log` is the power route, and `rpow_natCast_eq_pow` says the split between an integer power and a real one is a choice of algorithm, not of meaning. |
| `Tower.lean` | "does this continue?" | Yes: `dyadicLayer` is an explicit infinite tower that is cumulative, strictly gains expressive power at *every* step, has no lossless top, and still separates any two distinct carriers. Contrast `boundary_above_rational_empty`: whether a particular tower terminates is a property of the carrier space, not of the idea of layering. |
| `Golay/Code.lean` | the concrete extended binary Golay code | The code is built from the same parity block the package ships in `substrate/mog.py`: a word is a `Finset (Fin 24)` and `syn` is its 12-bit syndrome. `syn_symmDiff` makes the syndrome additive over symmetric difference, and `syn_eq_iff_isCodeword_symmDiff` says two words share a syndrome exactly when they differ by a codeword — the coset algebra everything else runs on. |
| `Golay/Sextet.lean` | the covering radius and the six-fold tie | Five exhaustive finite checks over all 4096 syndromes give `golay_min_weight` and hence `golay_min_distance_eight`; from them `unique_nearest_of_le_three` (reading is unambiguous up to weight 3), `covering_radius_eq_four`, and the shape of the ambiguity at weight 4: `ties_card_eq_six` — a deep hole has **exactly six** nearest codewords, no more and no fewer — with `sextet_partition` showing the six tie words partition the 24 coordinates into six tetrads, and `ties_pairwise_hdist_eight` that they are pairwise as far apart as the code allows. `coset_dichotomy` says every coset is either uniquely readable or a six-fold tie. |
| `Golay/Census.lean` | how often the tie happens, and where the average word sits | `coset_census` counts the 4,096 cosets by distance to the code — `1, 24, 276, 2024, 1771` — so `unique_vs_ambiguous` splits them into 2,325 uniquely readable and 1,771 six-fold ties, and `mean_coset_weight` computes the exact average distance `3433/1024`. `mean_coset_weight_gt_three` and `mean_coset_weight_lt_four` place it strictly between the packing radius 3 and the covering radius 4: the *average* word is already past the radius inside which the reading is unique, so ambiguity is the typical case for this code rather than a corner case. `cosetWt_eq_dist` identifies the coset weight with the distance to the nearest codeword. This is what `substrate/superposition.py`'s `coset_census_report` recomputes. |
| `Golay/Dynamics.lean` | the dynamical half of the criticality question | The census is about a distribution; this is about a process. One tick adds a parity-check column to the carrier's syndrome, so repeated one-bit perturbation is a random walk on the 4,096 cosets. `step_unif` and `stationary_unique`: the uniform law is stationary and is the *only* stationary law, so the long-run average distance to the code is the census figure `3433/1024` (`expect_unif_cosetWt`), with `3795/4096` of the mass at distance 3 or 4. But `par_col` and `iterate_dirac_ne_unif`: every column has odd parity, so the law alternates between the two parity classes and is **never** uniform — the chain has no limiting law; `prob_unif_subcritical_pos`: the stationary law keeps `301/4096` below the packing radius, so the weight does not lock on; and `perturb_correct_returns`: a corrected one-bit error returns the same codeword, so a corrected carrier stays *on* the code. The self-organised-criticality claim is therefore true only in its time-averaged form. The Cesàro statement the file leaves open is proved next door. |
| `Golay/Cesaro.lean` | the positive half of the same question | The perturb-only chain never converges, so the honest dynamical claim is about **time averages**, and this file proves it with an explicit rate: for every probability law `μ`, every syndrome `f` and every `N ≥ 1`, `cesaro_converges` gives `|cesaro μ N f − 1/4096| ≤ 24/N`, and `cesaro_tendsto` reads that back as an ordinary `Tendsto` for anyone who wants it in that form. The proof diagonalises the chain by the characters of `Syn = (ZMod 2)^12` — which take values `±1` and so live in `ℚ`, keeping the whole argument in exact rational arithmetic with no analysis. It turns on four facts about the eigenvalue `lam s`: `lam_zero` (`= 1`, which is why the limit is `1/4096` and not `0`), `lam_le` (`≤ 11/12` for `s ≠ 0`, quantitative irreducibility, because the columns span every syndrome), `abs_lam_le_one` (attained at `−1` on the all-ones syndrome — the periodicity itself), and `abs_geom_sum_le` (the partial sums are bounded by `24`, which is the `24` in the headline bound). The orthogonality relation `sum_chi` is proved here rather than imported. |
| `Superposition.lean` | holding all six readings at once | `bundleF2_eq_one`: bundling the six tie words by XOR gives the all-ones vector *whatever the tie is*, so the F2 bundle of a superposition carries no information about it — `bundleF2_constant`. Over the rationals the same bundle is faithful: `bundleQ_eq` computes the mean coordinatewise as `(1 + 4·vᵢ)/6`, `bundleQ_recover` reads the tie back out of it and `bundleQ_injective` says distinct superpositions have distinct bundles. This is the exact sense in which the ambiguity survives in a rational carrier and dies in a binary one. |
| `Wobble.lean` | ambiguity as a moving carrier | `sextet_cycle_avgVec`: a carrier that cycles through the six tied readings is read back exactly as their rational bundle, `sextet_cycle_determines` that this reading still determines the tie, and `sextet_cycle_tendsto` takes it to the limit. Wobble between the candidates is therefore a lossless way to hold them, not noise. |
| `HullExpansion.lean` | when a wider alphabet is genuinely needed | `cycle_avgVec_eq` reads a cycle back as its mean; `concTarget_not_mem_hull_scaled` exhibits a linear certificate separating a target from the hull of the available states, so `concTarget_unreachable_scaled` rules it out under any schedule — and `concTarget_reached_by_leech` hits it exactly in 16 ticks once two more states are admitted. `alphabet_expansion_strictly_helps` is the two together: the gain is in the alphabet, not in the schedule. |
| `VOA.lean` | the state–field map `Y(u, z)` on the 2A algebra, and where the finite layer stops | The Griess product of `Sakuma.lean` is one mode of a vertex operator algebra's state–field map, `Y(u, z) = ∑ₙ uₙ z^{-n-1}`, and this file builds that map at the layer the finite algebra carries: `mode u 1 v = u ⋆ v` and nothing else, so `mode_truncated` makes the field a genuine formal Laurent series. What the layer *does* carry is real vertex-algebra structure: `mode_skew` is the skew-symmetry axiom at this weight, and the invariant form is not chosen but forced — `form_forced_off_diagonal` derives `⟨eᵢ, eⱼ⟩ = (1/8)⟨eᵢ, eᵢ⟩` from invariance alone — giving `form_invariant`, `mode_self_adjoint` and `form_nondegenerate`, so the layer is a Frobenius algebra with vacuum `vac = (4/5)(e₀+e₁+e₂)` (`vac_mul`, `form_vac = 12/5`). What it does not carry is stated just as exactly: `borcherds_commutator_fails` shows the commutator formula at `m = n = 1` would demand `u ⋆ (v ⋆ w) − v ⋆ (u ⋆ w) = (u ⋆ v) ⋆ w`, and on the axis triple the two sides are `(−3/32) e₀ + (3/32) e₁` and `(−3/32) e₂`. The discarded modes are load-bearing; the infinite-dimensional half of the Moonshine bridge is not built here, and nothing claims it is. |

## Relationship to the Python package

Nothing here imports or executes Python, and nothing in the package imports
Lean. The correspondence is by statement:

* `Constants.lean` states the constants table of the top-level README;
* `GolayBoundary.lean` states what `substrate/golay_decode.py` reports as
  `corrected` / `ambiguous`;
* `Permutation.lean` and `Endianness.lean` state the frame facts that
  `glm_universal/migration/frames.py` audits numerically;
* `Facets.lean` states the decomposition `reasoning/facets.py` computes;
* `Layers.lean`, `Stack.lean` and `Tower.lean` state the theory that
  `reasoning/information_loss.py` and `reasoning/dimension_layers.py`
  instantiate;
* `Semantics/Meaning.lean` and `Semantics/Grounding.lean` state what
  `glm_universal/semantics/` implements — the round trip and injectivity of
  `meaning.encode`, the capacity refusal, the sense in which the inherited
  `sha256`-of-a-spelling carriers cannot be a measurement of meaning (which
  `semantics/audit.py` measures numerically), and the `si7_conflates` relation
  the grounded graph records;
* `DeltaSigma.lean`, `Irrational.lean`, `Reachable.lean` and `Computable.lean`
  state what `reasoning/exact_real.py` and `reasoning/real_expr.py` implement —
  the `1/N` law of the modulator, the cardinality wall and the faithful tower
  of stand-ins, the convex hull that bounds the 24-D carrier together with the
  separating certificate, and the exact sense in which comparison, division and
  equality are and are not computable;
* `Transcendental.lean` states the error budgets `reasoning/transcendental.py`
  pays — the argument precision each of `exp`, `log`, `sin`, `cos` and a real
  power demands, and the positivity witness `log` refuses without;
* `Cumulative.lean` states the property `dimension_layers.LAYERS` was made to
  have — `LAYER_INTEGER` keeps `substrate_bits`, the Griess and universal
  measures keep the carrier term — and the failure of the reading kept beside
  it as `LAYER_INTEGER_RAW`, which
  `information_loss_report()["non_cumulative"]` measures;
* `Golay/Code.lean`, `Golay/Sextet.lean`, `Golay/Census.lean`,
  `Golay/Dynamics.lean`, `Golay/Cesaro.lean`, `Superposition.lean`,
  `Wobble.lean`
  and `HullExpansion.lean` state what `substrate/superposition.py` implements —
  the six-fold tie at a deep hole and its sextet partition, the XOR bundle that
  collapses to the all-ones vector against the rational bundle that does not,
  contextual collapse back to a single reading, the wobble cycle whose time
  average is that rational bundle, the coset census and the exact mean coset
  weight `3433/1024` that `coset_census_report` recomputes, the perturbation
  chain that `coset_chain_report` pushes forward exactly, and the separating
  certificate behind the alphabet-expansion report.

Where the two disagree, the Lean file is the specification and the Python is
the implementation under test.
