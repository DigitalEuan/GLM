# GLM Pipeline Kit

This folder holds the parts of the 9-iteration GLM pipeline study that **work and have been
checked**, packaged on their own so you can copy this one folder into the Geometric Language
Machine (GLM) system. It replaces the roughly 90 study files: scripts, data, PDFs and plots.

It has two parts, and each one runs without the other:

| Part | What it is | Requirements | How to check it |
|---|---|---|---|
| `GLMKit/` (Lean 4) | Machine-checked proofs of the study's exact claims, plus corrections where a claim was wrong | Lean 4.28.0 + Mathlib `v4.28.0` | `lake exe cache get && lake build` |
| `python/glm_kit/` | Working pipeline code that mirrors the Lean definitions one-to-one | Python ≥ 3.9, **standard library only** | `cd python && python3 -m unittest discover -s tests -v` |

`FINDINGS.md` goes through the study one iteration at a time. For each claim it says whether
it was **verified**, **corrected**, **explained as an artifact**, or **not reproducible
here**, and which theorem or test backs that up.

---

## 1. What the kit gives the GLM

The corrected pipeline (`python/glm_kit/pipeline.py`):

```
grid ──encode──▶ 24-bit word ──measure──▶ Golay syndrome / nearest codeword / parity
                     │
                     ├──layer───▶ exact rule: the 4× embedding fails ⇔ odd popcount   (no learned head needed)
                     ├──embed───▶ 8× embedding: ALWAYS a Leech point                   (no Λ32/Λ48 escalation needed)
                     ├──junction▶ exact Λ/2Λ class of 4b = (Golay syndrome, popcount mod 4)
                     └──operate─▶ hypotheses kept in superposition:
                                   • XOR displacement (toggle, any XOR-mask rule)
                                   • geometric cell permutations (reflect, shifts, …) = permute_op
                                 answer only when every surviving hypothesis agrees on the query
```

Result of `python3 run_pipeline_demo.py`: 50 queries per family, 4 demonstrations each,
5 families = 250 queries in total.

| task | odd/even | 4× wall | 8× in Λ24 | solved | wrong |
|---|---|---|---|---|---|
| toggle | 24/26 | 24 | 50/50 | 50 | 0 |
| translate | 0/50 | 0 | 50/50 | 49 | 0 (1 flagged *ambiguous*) |
| reflect_v | 24/26 | 24 | 50/50 | 50 | 0 |
| flood_fill | 0/50 | 0 | 50/50 | 0 (unsolved, open) | 0 |
| bfs_shortest | 0/50 | 0 | 50/50 | 0 (unsolved, open) | 0 |

Toggle analogy `A:¬A::C:?`: the iteration-8 threshold decode gets **0/30** exact; the
parity-decode fix gets **30/30**.

These numbers come from running the Python code. The Lean files prove the mechanisms behind
them, for example *why* the threshold decode fails and *why* the parity decode is always
exact. They do not prove the individual counts.

## 2. Lean library `GLMKit` (all proofs complete: no `sorry`, no added axioms)

| File | Main results |
|---|---|
| `Golay.lean` | `golayCode_length` (4096), `golay_weight_enumerator` (1, 759, 2576, 759, 1), `golay_doubly_even`, `golay_self_orthogonal`, `golay_xor_closed` (linear), `golay_min_distance` (8), `allOnes_mem_golay`, `octads_length` (759), `steiner_5_8_24`, `golay23_sphere_packing` |
| `Leech.lean` | `parity_wall`, `parity_wall_glue`, **`eight_mul_mem`**, **`junction_iff`**, `junction_same_parity`, `leech24_parity_wall`, `leech24_eight_mul`, `leech_theta_coefficients` (E₄³ − 720Δ = 1 + 0q + 196560q² + 16773120q³ + 398034000q⁴), `leech_min_vectors_count`, `leech_class_census` |
| `Lattices.lean` | `bw_four_mul_mem` (Λ32), `constrA_p_mul_mem` / `constrA_three_mul_binary` (Λ48, Λ96), `constrA_spin_artifact`, `constrA_analogy_mem`, **`snap_analogy_noop`** |
| `Pless.lean` | `plessS_mul_transpose` (S·Sᵀ = −I over F₃), `plessS_skew`, `pless_generator_self_orthogonal`, `plessS_isUnit_det`, `plessS_ker_trivial`, `plessS_transpose_ker_trivial` |
| `Fields.lean` | `f2_two_eq_zero`, `f3_two_eq_neg_one`, `f3_orderOf_two`, `f5_orderOf_two`, `f7_orderOf_two`, `f7_orderOf_three`, `zmod6_not_isDomain`, **`no_field_of_card_six`**, `char_two_puncture`, `f9_alpha_order_four`, `f9_units_cyclic_order_eight`, `f4_units_order_three`, `f8_units_order_seven` |
| `Analogy.lean` | `xor_analogy_exact_iff`, `xor_analogy_toggle`, **`threshold_analogy_toggle_iff`**, `parity_decode_eq_xor`, `parity_analogy_toggle`, **`binary_mem_convexHull_iff`**, `const_mem_convexHull` |
| `Permutation.lean` | `wt_comp_perm`, `leech_layer_perm`, `wt_not`, `leech_layer_toggle`, `reflectV_involutive` |
| `AxiomAudit.lean` | `#print axioms` for the headline results |

**Scope of the Lean model.** The lattice theorems are stated for an *arbitrary* binary code
`C` that contains `0`, in the standard √8-scaled integer model of the Leech lattice. So they
also apply to the GLM substrate's own Golay code, whatever coordinate order it uses.

The concrete instance uses the cyclic Golay code with generator polynomial `0xC75` plus a
parity bit. This code is equivalent to the GLM's MOG-ordered code up to a permutation of
coordinates. However, it is **not** the same bitmask table, so do not swap one for the other
bit-for-bit.

**How finite facts are checked.** Finite facts (counts, matrix identities, the Steiner check)
are evaluated with `native_decide`. This means the results rely on the Lean compiler, which
shows up as the `Lean.ofReduceBool` and `Lean.trustCompiler` axioms. Everything else uses only
the standard axioms.

**Build time.** About 2 minutes for `Golay.lean` and well under a minute for the rest, once
Mathlib is cached.

## 3. Python package `glm_kit` (stdlib only)

| Module | Contents |
|---|---|
| `golay.py` | the G24 code, syndrome, coset-leader decoder (4096 cosets), octads |
| `leech.py` | `in_leech` (and `in_leech_like` for any code), `embed4`, `embed4_glue`, **`embed8`**, `hits_parity_wall`, **`junction_label`**, `same_class` |
| `lattices.py` | Pless `S`, `[I\|S]`, Construction-A membership, `in_lambda48` |
| `fields.py` | puncture/spin table for F₂…F₉ (correct F₉ orders), ℤ/6 zero divisors |
| `analogy.py` | `xor_analogy`, `parity_analogy` (fix), `threshold_analogy` (the old decode, kept for reference), **`permute_op`**, permutation library, `consistent_permutations` |
| `tasks.py` | the 5 synthetic task families with verified traces (Note 2 / TraceViT style) |
| `pipeline.py` | `measure(word)`, `solve(demos, query)` |
| `glm_bridge.py` | `check_substrate(leech2)`: tests the GLM's own `leech2.in_leech` / `class_of` against the theorems |
| `tests/test_kit.py` | 14 tests that cross-check every Lean-verified fact numerically |

Bit convention: coordinate `i` is bit `i`, the same as in Lean.
`tasks.grid_to_word(g, msb_first=True)` reproduces the study scripts' grid convention, where
the first cell is bit 23.

## 4. Bringing it into the GLM

1. Copy this folder into the GLM repository, for example as `glm_pipeline_kit/`.
2. Run `python3 -m unittest discover -s python/tests`. All 14 tests should pass.
3. Inside the GLM environment, run
   `from glm_universal.substrate import leech2; from glm_kit import glm_bridge; print(glm_bridge.check_substrate(leech2))`.
   Every failure counter should be 0. *This bridge was not run in the verification session,
   because the GLM repository was not available there.*
4. Replace in the GLM:
   - the learned lattice-selection head → `leech.hits_parity_wall`;
   - `4×` + Λ32/Λ48 escalation → `leech.embed8`;
   - Leech-class junction coordinates → `leech.junction_label`;
   - the Λ48 dual-snap threshold decode → `analogy.parity_analogy` / `xor_analogy`;
   - the coordinatewise-only `combiner.apply_op` for permutation tasks → `analogy.permute_op`
     together with `consistent_permutations`.
5. Optionally, build `GLMKit` with Lean to re-check the proofs.

## 5. What is *not* in the kit, and why

- The neural learners and Experiment B (iterations 1, 5, 6, 7 and 9) need `numpy`, `torch` and
  the GLM substrate. None of these were available, so the learners were not re-run and their
  accuracy figures are **not verified**. Their main target, the lattice layer, turns out to be
  an exact function of parity (`parity_wall`), so the kit replaces it with an exact rule.
- The delta-sigma "wobble" statistics, cost atlas and Leech wobble (iteration 2) depend on
  `glm_universal.reasoning`, so they were not re-run.
- The PDFs, plots and report generators are presentation only.
- `flood_fill` and `bfs_shortest` are not solved by any verified operator yet. They are open
  items, not failures of the kit.
