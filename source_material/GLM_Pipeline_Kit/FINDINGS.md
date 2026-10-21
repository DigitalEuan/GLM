# Audit of the 9-iteration GLM pipeline study

Every claim in this document carries one of these labels:

- ✅ **Verified**: proved in Lean (`GLMKit`) and/or checked by the kit's tests.
- 🔧 **Corrected / fixed**: the claim or code was wrong or incomplete. A corrected version is
  proved and implemented.
- ⚠️ **Artifact**: the reported number is right, but the stated reason for it is not. The
  actual reason is proved.
- ⛔ **Not reproduced here**: this needs the GLM substrate, `numpy` or `torch`, none of which
  were available. These claims were not checked and are not in the kit.

Environment note: the study scripts import `glm_universal` from `/home/z/my-project/glm_repo`
and use `numpy` and `torch`. None of these were available in the verification session, so no
study script could be executed as written. All 40 scripts were syntax-checked and they all
compile. The exact mathematical content was re-implemented from scratch: in Lean (proved) and
in standard-library Python (tested).

---

## Iteration 1: Note 4 audit, Experiment A + C, Experiment B

| Claim | Status | Evidence |
|---|---|---|
| G24 has 4096 codewords with weight enumerator 1 + 759y⁸ + 2576y¹² + 759y¹⁶ + y²⁴, is doubly even, has d = 8, and has 759 octads | ✅ | `golayCode_length`, `golay_weight_enumerator`, `golay_doubly_even`, `golay_min_distance`, `octads_length` |
| G24 is linear and self-orthogonal | ✅ | `golay_xor_closed`, `golay_self_orthogonal` |
| Steiner system S(5,8,24) | ✅ | `steiner_5_8_24` (all 42504 five-sets checked) |
| G23 is perfect: 2¹²·(1+23+253+1771) = 2²³ | ✅ | `golay23_sphere_packing` |
| Leech theta series = E₄³ − 720Δ, with 196560 minimal vectors | ✅ (coefficients) | `leech_theta_coefficients`: 1, 0, 196560, 16773120, 398034000 |
| Minimal-vector shapes 759·2⁷ + 24·2¹² + C(24,2)·4 = 196560; class census sums to 2²⁴ | ✅ (arithmetic only) | `leech_min_vectors_count`, `leech_class_census`; spot checks of all three shapes being in Λ24 |
| Enumeration of the 196560 vectors, the 98280 classes, the Co₀ pair census, and [ℤ²⁴:Λ] = 2³⁶ | ⛔ | needs the substrate's enumerations |
| Golay-coset solver scores 0 % on toggle | ⚠️ explained | `allOnes_mem_golay`: the toggle displacement 𝟙 is a codeword, so its syndrome is 0 and the decoder returns the zero leader |
| Raw XOR scores 100 % on toggle and fails on the other tasks | ✅ | `xor_analogy_toggle`; `xor_analogy_exact_iff` (exact iff the displacement x ⊕ f(x) is the same for every input) |
| Golay-coset = random-linear in 249/250 trials | ⛔ | statistical, not re-run |
| Experiment B: trace supervision improves IMR | ⛔ | neural; not re-run. The trace generators are kept (`tasks.py`, with `verify_trace`) |

## Iteration 2: cost atlas, wobble, hull certificate, Leech wobble

| Claim | Status | Evidence |
|---|---|---|
| All binary task targets lie outside the convex hull of the 4096 codewords ("provably unreachable") | ⚠️ | `binary_mem_convexHull_iff`: a 0/1 target is in the hull of 0/1 vectors **iff it is one of them**. "100 % separation" only means no target was a codeword. It says nothing about higher layers. |
| Constant targets c·𝟙 lie inside the hull, and the wobble visits 2 codewords | ✅ explained | `const_mem_convexHull` together with `zero_mem_golay` and `allOnes_mem_golay`: c·𝟙 lies on the segment from 0 to 𝟙 |
| Cost-atlas percentages and wobble / Leech-wobble trajectories | ⛔ | need `glm_universal.reasoning` |

## Iteration 3: step rules and the parity wall

| Claim | Status | Evidence |
|---|---|---|
| Parity wall: 4·b ∈ Λ24 iff popcount(b) is even, and the odd-coset glue (−3, 1²³) does not help | ✅ | `parity_wall`, `parity_wall_glue` (any code), `leech24_parity_wall`. The study's data agrees exactly: the wall count equals the odd count for every task (toggle 21/21, reflect_v 19/19, 0 for the others) |
| The reason given ("sum(glue) ≡ 4 mod 8 always") | 🔧 | the actual reason is simply that Σ 4bᵢ = 4·wt(b), which is ≡ 0 (mod 8) iff wt(b) is even |
| Rule-invocation table: sum_mod_8 and in_leech are invoked 2× per sample | 🔧 bug | `iter3_01_step_rules.py` only counts names that appear in `STEP_RULES`. `sum_mod_8` and `in_leech` are not in that dict, so the data file shows **0**, not the 2× stated in the worklog |
| translate / flood_fill / bfs_shortest are "structurally even" | ✅ | the inputs have 4 + 6 = 10 cells (block plus floor), 2h + 2w − 4 cells (rectangle boundary) and 2 cells respectively |

## Iteration 4: Λ32, Λ48 and the pair-census escalation

| Claim | Status | Evidence |
|---|---|---|
| Λ32 and Λ48 resolve 100 % of wall hits | ⚠️ | `bw_four_mul_mem` (4ℤⁿ ⊆ 4ℤⁿ + 2C₂ + C₁) and `constrA_p_mul_mem` (3ℤⁿ ⊆ every Construction-A lattice). Both succeed by trivial scaling. |
| The Λ48 "spin / multiplication puncture" mechanism | 🔧 | the embedding works because **3 ≡ 0 in F₃**, which is deletion, not a unit (the script's own docstring says this). It has nothing to do with 2 = −1. |
| An escalation beyond Λ24 is needed | 🔧 | `eight_mul_mem`: **8ℤ²⁴ ⊆ Λ24**, so the 8× embedding places every binary target inside Λ24 itself. Fix: `leech.embed8`. |
| pair_census is never invoked | ✅ explained | follows from the two points above |

## Iteration 5: rule learner and field punctures

| Claim | Status | Evidence |
|---|---|---|
| Learner accuracies (67–87 % in-distribution, and so on) | ⛔ | neural, not re-run |
| The lattice label the learner predicts | 🔧 | by `parity_wall` the label **is** popcount mod 2. The learner was being asked to learn parity from raw bits, which explains the "majority-class default". Exact replacement: `leech.hits_parity_wall` |
| F₂: 2 = 0. F₃: 2 = −1 with order 2. F₅: ord(2) = 4. F₇: ord(2) = 3 | ✅ | `f2_two_eq_zero`, `f3_two_eq_neg_one`, `f3_orderOf_two`, `f5_orderOf_two`, `f7_orderOf_two` |
| F₇ docstring says "spin of order 6" | 🔧 | ord(2) = 3 (as the script's table says). Order 6 belongs to 3: `f7_orderOf_three` |
| F₆ is not a field | ✅ | `no_field_of_card_six` (no field has 6 elements), `zmod6_not_isDomain` |
| Characteristic-2 extensions keep the puncture | ✅ | `char_two_puncture`; `f4_units_order_three`, `f8_units_order_seven` |
| F₉: spin order 4 in the table, but the report text says "order 8 (richest spin)" | 🔧 | `f9_alpha_order_four`: α with α² = −1 has order **4**. `f9_units_cyclic_order_eight`: F₉ˣ ≅ C₈ does contain elements of order 8, but α is not one of them. "Doubling 2 → 4" is true for α; the full group has order 8 = 4 × 2. |

## Iteration 6: fixed learner and Λ96

| Claim | Status | Evidence |
|---|---|---|
| Learner gains from parity feature, balanced loss and deeper encoder | ⛔ | neural, not re-run. The "parity feature" is the label itself, see iteration 5 |
| Λ96 snaps 100 % | ⚠️ | `constrA_p_mul_mem` (3× embedding) |
| Every target has a 3-element spin superposition | ⚠️ artifact | `constrA_spin_artifact`: every permutation and every rescaling of a 3×-embedded target stays in the lattice. The count equals the number of operations tested, whatever the target |

## Iteration 7: substrate superpose, full F₉ lattice, lattice analogy

| Claim | Status | Evidence |
|---|---|---|
| superpose() features raise learner accuracy to 0.969 | ⛔ | needs the substrate and torch |
| The full F₉ lattice exposes an 8-element spin superposition | ⚠️ artifact | same reason as iteration 6 (`constrA_spin_artifact`) |
| The α-embedding needs target ∈ ker Sᵀ | ✅ | `plessS_transpose_ker_trivial`: ker Sᵀ = 0, so only the zero target qualifies |
| lattice_analogy at Λ24 gives 0 % exact | ⛔ (consistent) | not re-run. The analogy fix is under iteration 8 |

## Iteration 8: junctions, dual snap, F₂ combiner, ker S

| Claim | Status | Evidence |
|---|---|---|
| Junctions are 100 % same-parity | ✅ (now a theorem) | `junction_same_parity`. Stronger: `junction_iff` says 4b ≡ 4b′ (mod 2Λ) ⇔ b ⊕ b′ ∈ G24 ∧ wt b ≡ wt b′ (mod 4). Exact label: `leech.junction_label`. Caveats on the script: it only inspected the first 10 of 17 junctions, and odd targets used raw bits as coordinates |
| Dual snap: toggle 0 % | 🔧 explained + fixed | `threshold_analogy_toggle_iff`: the threshold decode is exact **iff A = C**. Fix: decode by parity (`parity_decode_eq_xor`, `parity_analogy_toggle`) → 30/30 in the demo |
| Dual snap: translate 47 %, reflect_v 3 % | 🔧 fixed | an additive analogy cannot express position-dependent rules. Fix: `permute_op` plus the permutation hypothesis library → translate 49/50 and reflect_v 50/50, with 0 wrong answers (demo) |
| The combiner cannot express permutations (DI1/DI3) | 🔧 fixed | `analogy.permute_op`. `wt_comp_perm` and `leech_layer_perm` show that permutations keep the lattice layer |
| S·Sᵀ = 2I = −I (mod 3), rank 24, ker S = 0 | ✅ | `plessS_mul_transpose`, `plessS_isUnit_det`, `plessS_ker_trivial`. Also `plessS_skew` and `pless_generator_self_orthogonal` (C(23) is self-dual) |

## Iteration 9: junction learner, richer snap, unified summary

| Claim | Status | Evidence |
|---|---|---|
| A junction head with 147 classes overfits (DI6) | 🔧 resolved | no learning is needed: the junction is computed exactly by `junction_label` (`junction_iff`). The coarse label "parity" is exact as well (`junction_same_parity`) |
| The richer Λ48 snap equals the trivial snap (DI7) | ✅ (in general) | `snap_analogy_noop`: for a **linear** code, D* = C + (B − A) of lattice points is a lattice point, so **any** snap that fixes lattice points returns it unchanged |
| DI7 fix: "use a non-trivial embedding where D* mod 3 ≠ 0" | 🔧 | this cannot work while A, B, C are lattice points (`constrA_analogy_mem`). The analogy has to be changed (XOR / permutation), not the embedding |

## Open items (carried forward)

- `flood_fill` and `bfs_shortest` have no verified operator yet: they are neither XOR rules
  nor permutations. Natural next operators: region fill (closure of a boundary) and a
  shortest-path writer.
- Re-run the neural learners inside the GLM, now using the exact labels (parity, junction
  label) as inputs or targets.
- Run `glm_bridge.check_substrate(leech2)` inside the GLM to confirm that the substrate
  satisfies the proved theorems.
