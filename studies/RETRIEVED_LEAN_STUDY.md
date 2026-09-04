# What was left behind in the archive, and what of it is a theorem

*The supplied archive (`source_material/GLM-main.zip`) holds a decade of GLM
experiments as loose scripts, notes and half-finished Lean files. This round
went through the parts the brief named — the `glm_machine` scripts, the two
light/EM calibration rounds, the Leech-lattice shortcut, the spatial-arithmetic
and MOG-cube encoding attempts, the first-principles and projection sub-studies,
`GMHGL`, the earlier `glm_lean` iterations and the ARC experiments — and asked
one question of each: **is there a claim here that can be stated as a theorem
and checked?** Where the answer was yes, the claim was retrieved into the
development as Lean that builds against the current Mathlib, with no `sorry`.
Where the claim turned out to be false, the refutation was retrieved instead.*

Lean: 25 files, 7,230 lines, 854 declarations, all under
[`RequestProject/GLM/`](../RequestProject/GLM/) and mirrored in
`overlay/glm_lean/`.
Checked by: `lake build`, the sorry scan, the two-copy diff and
`overlay/glm_universal/tests/test_retrieved_lean.py`.
Addressed by: `report lean` — the corpus these files joined is measured in
[`LEAN_ADDRESS_STUDY.md`](LEAN_ADDRESS_STUDY.md).

---

## 1. The discipline this round was held to

The archive is not short of assertions, and the temptation with retrieved
material is to carry the assertion across and let the Lean file's existence
stand in for a check. Four rules were applied instead, and every file below
obeys all four.

1. **A claim is retrieved as a statement, not as a conclusion.** Where the
   source says "the speed of light is an output of the substrate", the Lean
   file states the chain and proves what the chain actually determines.
2. **A refutation counts as a retrieval.** Nine of the twenty-five files are
   negative results (§3), and a false claim is more useful proved false than
   quietly dropped.
3. **Nothing is assumed about the GLM that the development does not already
   carry.** Where a retrieved file needs the Golay code, the minimum weight or
   the tax function, it uses `Golay/Code.lean`, `Golay24.golay_min_weight` and
   `Constants.lean` rather than restating them, so a retrieved theorem cannot
   agree with the substrate by being about a different substrate.
4. **Classical facts stay hypotheses.** Transcendence statements the retrieved
   material needs (that `π` and `e` are transcendental, say) are carried as
   explicit hypotheses of the theorems that use them, never as axioms.

---

## 2. What came back, file by file

| file | lines | decls | what the archive claimed | what is now proved |
|---|---|---|---|---|
| `Calibration.lean` | 462 | 71 | `light/`, both rounds: *"c is not an input, it is an output of the substrate's 24-bit cycle"* | **False, and structurally so.** `substrate_c_is_circular`: dividing the derived cell length by the derived cell duration returns `c` for *every* anchor and *every* tick budget. `speed_not_from_action_and_energy`: an action and an energy generate only `Mᵃ⁺ᵇ L²ᵃ⁺²ᵇ T⁻ᵃ⁻²ᵇ`, which never contains `L T⁻¹`. What survives is the dimensionless part: the propagation law `n(T) = (24+T)/(24+T₀)`, causality forcing `T₀` to be the minimum admissible tax, and `octad_min_tax` identifying that minimum with the octads at `8Q` |
| `AlignmentPoints.lean` | 176 | 17 | eight "alignment points" between substrate numbers and measured constants | the two that are not fits are audited: `gammaS_eq` verifies `γ = ℳ/13` and `FitCapacity.derived_layer_is_definitional` shows it is the definition of the leak rewritten, so nothing is predicted; `electronMass_error` proves the relative error of the electron-mass point lies in `[0.0090 %, 0.0093 %]` against a claimed `0.007 %` — a correction to the source table |
| `FitCapacity.lean` | 428 | 54 | `α⁻¹ = 137 + L`, `m_μ/m_e = 169/w`, `m_p/m_e = 1836 + 2Lσ` as evidence | the instrument that prices such evidence. `fit_capacity`: `N` candidate predictions matching within `δ` cover a target set of measure at most `2Nδ`. The ledger scores the three fits at **< 1 bit**, 3–4 bits and 2–3 bits over the guarantee that holds for any target of that size |
| `Packing.lean` | 341 | 32 | 24 is structurally forced | **23 is forced; 24 is not.** `perfect_triple_length`: for `4 ≤ n ≤ 2000` a perfect three-error-correcting binary code needs `n ∈ {7, 23}`. At 24 the sphere-packing bound is missed by 7,254,016 words, and `even_distance_ambiguity` shows the 24th coordinate buys detection, never correction. Self-duality selects it, and that is a symmetry preference |
| `Triad.lean` | 106 | 9 | `tgic_v3.py`, `tgic_audit.py`, `ubp_tgic_engine.py`: the triple `3, 6, 9` | `tgic_counts_generic`: *any* three-element set produces `3, 6, 9`, so exhibiting them distinguishes nothing; `interaction_counts_differ`: which of 3, 6 and 9 is "the interactions" is a naming choice; `twentyfour_decompositions`: 24 is decomposition-rich, so matching a structure to a decomposition of it is close to costless |
| `SeedLayers.lean` | 431 | 41 | the projection sub-study: where `π`, `φ`, `e` may enter | `transcendental_not_trace_of_finite_order`: no finite group acting linearly has a transcendental character value, and on a *lattice* `lattice_character_ne_pi` excludes `π` by integrality alone. `φ` is a character value (`phi_is_trace_of_order_ten`) but not an eigenvalue of any finite-order map, and `fibMat_eigenvector` places it where it belongs: an infinite-order lattice automorphism, a stretch and not a shear |
| `StepCost.lean` | 233 | 28 | the cost model of the archive's engines | `nrci_gauge_independent`: calibrated to `B = 8Q` the coherence ladder `1, 1/2, 2/5, 1/3, 1/4` is free of `Q`, so no statement about it can depend on the read quantum; `total_const`: a constant rate is not a clock; `shortcut_distortion`: with steps of size 1 and 13, every target of size ≥ 14 is strictly cheaper than the naive path — the precise form of "levels give shortcuts" |
| `SpatialArithmetic.lean` | 290 | 22 | `GMHGL/spatial_arithmetic.py`, `spatial_totient_kinetics.py` | the polygon codec is lossless (`nodeCount_roundtrip`, `nodeCount_injective`) with the sign in the parity of the vertex count; `dist_ge_clearance` proves in an arbitrary metric space why operator clearance keeps a unit-edge detector from joining two operands; and the script's "proven theorem" `C(N) = ⌊N/2⌋ − φ(N)/2` is proved, in the two halves `jump_orbit_card` and `coprime_half_count` |
| `ReasoningLoop.lean` | 147 | 12 | the ARC experiments' *perceive → goal → gap → propose → inspect* cycle | `solve_sound`: the verification gate holds, whatever the proposer offers; `solve_eq_none_iff`: a refusal is exactly the absence of a passing candidate, so it is informative; `gate_not_sufficient`: two candidates can pass every training pair and disagree on the test — the limit stated as a theorem, and the qualitative form of `FitCapacity.fit_capacity` |
| `Foundations.lean` | 343 | 41 | the first `glm_lean` iteration, GLM-1 | the mod-2 ceiling (an XOR-composing encoder cannot separate `E = mc²` from `E = mc⁴`, and is not injective at all), the derived carrier (`9⁷ < 2²⁴`), the 16-state column codec, winding integrality and the extraspecial commutation relations |
| `Gen2.lean` | 491 | 69 | GLM-2 | the meaning module's 2-torsion, so no injective homomorphism into `ℤ²⁴` exists; the rational strengthening of the ceiling — over `ℚ¹⁰` *every* additive map into a group of exponent 2 is identically zero; unique decoding inside the packing radius; the `Λ/2Λ` census and the Griess ledger |
| `Gen3.lean` | 793 | 98 | GLM-3 | the plus-type count `(4ⁿ + 2ⁿ)/2` for `n` hyperbolic planes, giving `2²³ + 2¹¹` at `n = 12`; the extraspecial group `2^(1+24)` built from its cocycle rather than quoted; the faithfulness of the 2-adic stack; and §6, the arithmetic behind the cube refutation — the even-weight code on eight cells has 128 words and `RM(1,3)` has 16, so the archive's identification cannot hold |
| `Cube/Surface.lean` | 547 | 82 | `mog_cube_1`: the cube's surface is the MOG | proved, and made exact: `mog_card` 4096 codewords, weight enumerator `1, 759, 2576, 759, 1`, minimum weight 8, the three-layer factorisation `2¹⁸ = 64·2¹²`, and the erasure boundary — one bad face heals, two are genuinely ambiguous |
| `Cube/HexTiles.lean` | 187 | 22 | the cube as a hexacode tile | `hexacode_mds`: three incoming faces determine the tile; `update_matrix_order_three`: the propagation matrix has order three; `determined_by_boundary`: a legal assembly of the octant is fixed by its boundary, so the hexacode layer's entropy is a surface entropy |
| `Cube/Stabiliser.lean` | 308 | 48 | the cube's symmetries are free moves | under the MOG identification only **12 of 48** are (`stabiliser_card`), exactly the tetrahedral rotations (`preserves_iff_tetrahedral`) — but the identification is a choice, and §3 exhibits a different `[24,12,8]` placement on the same cells preserved by **all 24** rotations and by no improper symmetry |
| `Cube/Tax.lean` | 287 | 32 | the cube's instruction set is free / priced / repairable | the price list proved: `covering_radius_le_four` and `covering_radius_ge_four` make the repair tax exactly `4Q` in the worst case; `repair_unique_of_le_three` and `repair_ambiguous_at_four` place the boundary; `and_is_priced` exhibits two codewords whose AND is not one |
| `Cube/Three.lean` | 347 | 48 | `test_8_three_cube.py`: three parallel 3-cubes with rules A, B, C give the Golay code | **no.** Rule A is `RM(1,3)`, 16 words, not the `RM(2,3)` the script names; Rule B rejects nothing Rule A accepts; the Rule-A/B code is `[24,12,4]`, and `ruleA_code_is_not_golay` shows no relabelling repairs it. Turyn's glue on the same three cubes does give the Golay code, and that is proved beside the refutation |
| `Shortcut/Golay.lean` | 146 | 19 | the shortcut method's Golay layer | the `[24,12,8]` code from the substrate's own generator matrix, its `GF(2)`-linearity and Hamming arithmetic |
| `Shortcut/GolayWeights.lean` | 96 | 11 | — | all 4096 codewords enumerated: the weight enumerator, double evenness, minimum distance 8, and codeword recognition as an `O(1)` test |
| `Shortcut/Decoder.lean` | 150 | 17 | `snap_to_codeword` is a decoder | it is not: it corrects weight ≤ 3 and otherwise returns its input. `golay_covering_radius` (every word is within 4), `decode_isGolay`, `decode_dist_le_four` supply the complete decoder, and `substrate_snap_fails` names a word the shipped engine leaves outside the code |
| `Shortcut/Substrate.lean` | 111 | 8 | the published directory's *"`d² ∈ 2ℤ`, 100 %"* is an empirical lattice law | it is neither empirical nor about the walks: the code is doubly even, so weight parity is constant on a coset, the failing cosets have even leader weight, and `legacySnap_even_weight` makes every output even by construction |
| `Shortcut/GrayCode.lean` | 234 | 27 | the 24-bit Gray layer, and "geodesic jumps" between consecutive integers | `d2_eq_pop_gray_xor` — the jump norm is `pop(gray(a XOR b))`, an `O(1)` formula — and `d2_succ`: adjacent integers are always at `d² = 1`, so the directory's larger values for consecutive integers come from the factor encoder and the snap, not from Gray adjacency |
| `Shortcut/Leech.lean` | 284 | 16 | the "geodesic octad step" | `leech_min_norm` (32 in the integral scaling), `golay_step_isLeech`, and `golay_step_minimal_iff`: a doubled Golay difference is a kissing vector exactly when the codewords are at Hamming distance 8 |
| `Shortcut/Shortcut.lean` | 176 | 22 | the published pipeline and its directory | the corrected pipeline lands in `Λ₂₄` (`corrected_step_isLeech`), its norm is quantised by 4 and not by 2 (`corrected_quantized`), and the audit theorems evaluate it on the published catalogues |
| `Shortcut/FactorMap.lean` | 116 | 8 | the directory's "Deep Interfacial Sequence" | the generator's *factor* encoder is reconstructed, the factorisations are certified, and the published jump norms are reproduced exactly — which is what makes the audit's point precise rather than rhetorical |

---

## 3. What the retrieval is worth, counted rather than asserted

**Nine of the twenty-five files are negative results.** `Calibration.lean`,
`Triad.lean`, `Packing.lean`, `Cube/Three.lean`, `Shortcut/Substrate.lean`,
`Shortcut/Decoder.lean`, `Shortcut/GrayCode.lean` and `AlignmentPoints.lean`
each show that something the archive reported as a discovery is either a
tautology, a naming choice, or numerically different from what was quoted; and
`FitCapacity.lean` is the instrument that says how much a numerical agreement
could have been worth in the first place. That is the majority of the
retrieval's value, and it is the part that would have been lost had the
material simply been left in the archive: a refuted claim in a script is
indistinguishable from an unexamined one.

**Five of them are load-bearing for the current system.** `Cube/Surface.lean`
supplies the identification the MOG cube encoding rests on; `Shortcut/Leech.lean`
and `Shortcut/Golay.lean` are the lattice and code arithmetic the shortcut
method needs; `Cube/Tax.lean` proves the price list the cube's instruction set
is described by; and `ReasoningLoop.lean` states what the ARC-era cognitive
cycle's verification gate does and does not buy — the property the current
evaluation harness scores by.

**None of them changed an answer.** The end-to-end evaluation returns the same
131 / 131 with the same 16 boundary refusals it returned before the retrieval,
and the benchmark suites and capability probes are unmoved. The retrieval is
additive: it enlarges what is *proved* about the system without altering what
the system answers.

**What it did move** is the address book, and by exactly the amount a growth of
this size should move it: the Lean corpus went from 1,270 declarations across
48 files to **2,118 across 73**, and `LEAN_ADDRESS_STUDY.md` was re-measured
rather than patched. The interesting part of that re-measurement is that the
separation signal *improved* — nearest-by-address shares a file 13.2 times
chance where it was 12.3 times before, and the citation test 15.0 times chance
where it was 9.6 — on a corpus two thirds larger and from files the encoding
had never seen. Those two ratios are the measurement taken at the close of
this round; both have been re-measured since and are quoted at their current
values in `LEAN_ADDRESS_STUDY.md`.

**Where the tree stands now.** The table above is re-measured against the tree
on every suite run, so its rows are current rather than of-their-time: two of
the files retrieved here have been extended since — `Calibration.lean` by the
lightspeed work and `Triad.lean` by the triad audit — which is why the totals
read 7,230 lines and 854 declarations rather than the 7,170 and 848 the round
closed on. The corpus as a whole has moved further still: the restoration
round that followed brought the development to **2,764 declarations across 95
files**, so the 854 retrieved here are now a little under a third of it. The
round-time figure of 1,270-before / 2,118-after in the paragraph above is left
as written, because it records what the retrieval itself moved.

---

## 4. What was examined and not retrieved

The brief named more than was retrieved, and the omissions are deliberate.

* **`ubp_unified_v5.py`, `ldp_nrci.py`, `refined_nrci.py`, `value_geometry.py`,
  `geometry.py`, `ubp_genesis_boot.py`.** Their content is already in the
  development, in `Constants.lean` (the tax and coherence definitions),
  `Facets.lean` and `Layers.lean`. `Shortcut/Substrate.lean` retrieves the one
  thing `ubp_unified_v5.py` supplies that was not already there — its
  `snap_to_codeword`, as the object of a refutation.
* **`ubp_electromagnetic_analog_compute_engine.py`,
  `ubp_eml_alu_sovereign.py`.** Simulation harnesses: they compute, but state
  nothing that survives being separated from the simulation.
* **`ldp_complete_mapping.md`, `tgic_verification.py`.** Tabulations. The
  claims they tabulate are the ones `Triad.lean` audits.
* **The price section of the archive's hexacode file.** Already in the
  development twice over, in `StepCost.lean` and `SeedLayers.lean`, and the
  retrieved `Cube/HexTiles.lean` says so in its header rather than duplicating
  it.
* **`arc_agi_15`.** The architectural claim was retrieved as
  `ReasoningLoop.lean`; the grid heuristics were not, because they are
  ARC-specific and the loop's guarantees are not.

---

## 5. Reproducing this

```bash
# the Lean, from the repository root
lake build
grep -rInw -e sorry -e admit RequestProject/GLM     # no matches
diff -r -x README.md RequestProject/GLM overlay/glm_lean/RequestProject/GLM

# the retrieval's own test
cd overlay
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_retrieved_lean.py -q

# the corpus these files joined
PYTHONPATH=. python3 -m glm_universal.tools lean-address
PYTHONPATH=. python3 GLM.py -q "report lean" --no-banner
```

Every declaration counted above is counted by the address book's parser, so the
per-file numbers in §2 and the corpus figures in `LEAN_ADDRESS_STUDY.md` cannot
disagree: `test_retrieved_lean.py` fails if a file listed here is missing from
the tree, missing from the mirror, or contributes a different number of
declarations than the table states.
