# GLM v3.17.0 — Levelling-Up Report

**Date:** 2026-07-06
**Author:** Z.ai levelling-up pass (per `SESSION_SUMMARY.md`)
**Base version:** v3.16.0 (26/26 self-tests, 41/41 golden cases)
**New version:** v3.17.0 (26/26 self-tests, 41/41 golden cases, **46/46 new v3.17 tests**)

---

## What changed (one-paragraph summary)

v3.17.0 wires `GLM09_tools.evaluate_numeric` to the real native UBP engines (`NoiseALU`, `ExactMath`, `LinearAlgebraALU`, `PhysicsALU`) via a new `GLM25_native_alu` adapter, so every numeric computation now produces a real execution `trace` and a substrate `fingerprint` (NRCI + lattice name + Monster grade). SymPy is demoted to validation-only — it cross-checks the native result and the agreement is recorded as `sympy_check.matches`, but never overrides the native answer. A second new module, `GLM26_crg_alu`, provides the **word-level NoiseALU equivalent** proposed in SESSION_SUMMARY §10 — `traverse`, `shortest_path`, `relate`, `chain`, and `compose_path_fingerprint` all produce `{result, trace, fingerprint}` with the same shape as math operations, unifying the "sovereign computation" two-stage pattern across math and words. The destructive **quadrant-forcing** step in `GLM23_grammar_vectors` and `GLM24_continuous_learner` is retired behind a `QUADRANT_FORCING_ENABLED` flag (default OFF); the default path is now pure SVD + plain Golay snap, which the session summary confirmed retains ~75% of distributional signal vs. forcing's ~0%. Three confirmed ContinuousLearner bugs are fixed (protected-prefix blanket-freeze, learned-edges never re-applied on reload, no flush-on-exit save), plus a fourth bug discovered during testing: `co_occurs` was not in `EDGE_LABELS`, so `crg.add_edge(..., "co_occurs", ...)` was silently returning False — meaning the original `_check_for_new_edges` was also broken, not just `_load_learned_edges`. Finally, `chat_prose(query, fresh=True)` and a `verb_distance` gate in `OntologicalGrammar.construct_sentence` address the cross-topic bleed and word-salad issues from SESSION_SUMMARY §4.

---

## File-by-file changes

### New modules (additive — no existing code paths touched)

#### `GLM25_native_alu.py` (~580 lines)
Native ALU adapter. Exposes:
- `native_compute(kind, operands, validate=True, **kwargs) -> NativeResult` — routes 30 numeric operations through the real engines. Every result carries `{result, exact, approx, trace, fingerprint, sympy_check, elapsed_us, operation}`.
- `symbolic_with_fingerprint(kind, expr, var, **kwargs) -> dict` — runs symbolic ops (differentiate, integrate, ODE, Taylor, limit) via SymPy (no native equivalent exists) but still fingerprints the result through the substrate.
- `NativeResult` class with `to_dict()` for serialization.
- Module-level lazy singletons for `NoiseALU`, `PhysicsALU`, `LinearAlgebraALU`, `AdaptiveManifold` (instantiation is non-trivial; kept alive for the module lifetime).

Operations with native equivalents: `gcd, lcm, factorial, isqrt, sqrt, is_prime, combination, permutation, modpow, add, sub, mul, divmod, power, dot_product, cross_product, vector_magnitude, det_2x2, det_3x3, det_nxn, matrix_trace, fibonacci, sum_series, extended_gcd, modular_inverse, crt_two, stirling2, mean, variance, stddev` (29 operations).

Operations using SymPy (no native equivalent exists, result still fingerprinted): `eigenvalues`, `differentiate`, `integrate`, `simplify`, `solve`, `partial_diff`, `gradient`, `ode`, `taylor`, `limit`, `sum_series_symbolic` (11 operations).

#### `GLM26_crg_alu.py` (~360 lines)
Word-level NoiseALU equivalent. Exposes `CRGTraversalALU(crg, vocab)` with:
- `traverse(src, label, dst)` — single-edge walk, returns `{verified, dst_vector, dst_hex, trace, fingerprint}`.
- `shortest_path(a, b, max_hops=3, label_filter=None)` — BFS over the CRG, returns `{path, path_str, n_hops, dst_vector, dst_hex, trace, fingerprint}`.
- `relate(a, b, max_hops=2)` — direct + 2-hop relation listing.
- `chain(*words, label_filter=None)` — multi-hop walk, returns `{all_paths, total_hops, end_word, end_vector, end_fingerprint, full_trace}`.
- `compose_path_fingerprint(path)` — SHA-256 hash of the canonical path string, fed to `AdaptiveManifold.fingerprint`. Two isomorphic backbones produce identical hashes → identical fingerprints.

The "sovereign computation" two-stage pattern is now uniform:
| Domain | Stage-1 (explicit algorithm) | Stage-2 (fingerprint) |
|---|---|---|
| Math | `NoiseALU.gcd(a,b)` Euclidean walk | `AdaptiveManifold.fingerprint(result)` |
| Words | `CRGTraversalALU.shortest_path(a,b)` BFS walk | `AdaptiveManifold.fingerprint(dst_hex_int)` |

Both produce `{result, trace, fingerprint}` with the same keys.

### Modified modules (surgical patches, all behind opt-in flags where possible)

#### `GLM09_tools.py` — Native-first compute, SymPy validation-only
- Added import of `GLM25_native_alu.native_compute` and `symbolic_with_fingerprint`.
- Rewrote `evaluate_numeric(comp)` to route through `native_compute` first; falls back to legacy SymPy/stdlib path only if native fails (defensive). Every successful native result now returns:
  ```python
  {value, exact, approx, trace, fingerprint, sympy_check, elapsed_us, native=True}
  ```
  The `{value, exact, approx}` triple is preserved for backward compat — existing callers (golden cases, self-tests) work unchanged.
- `evaluate_symbolic(comp)` is unchanged — SymPy remains the engine for symbolic ops (no native exists), but results could be routed through `symbolic_with_fingerprint` if you want substrate fingerprints attached. This is left as a follow-up.

#### `GLM23_grammar_vectors.py` — Quadrant-forcing retired (default OFF)
- Added module flag `QUADRANT_FORCING_ENABLED = os.environ.get("GLM_QUADRANT_FORCING", "0") == "1"`. Default OFF.
- Added new `build_svd_only_vectors(svd_signal, vocab_list, word_roles)` — pure PPMI+SVD, median-quantise, plain Golay snap (no quadrant restriction). This is the SESSION_SUMMARY's "comparatively benign" path (§6/§7) that retains ~75% of the signal.
- Modified `build_grammar_vectors()` to route through `build_svd_only_vectors` by default; the legacy forcing path (`build_grammar_aligned_vectors` + `snap_to_golay_preserving_quadrant`) only fires when `QUADRANT_FORCING_ENABLED=True`.
- The legacy functions are preserved for A/B testing — no existing code paths removed.

#### `GLM24_continuous_learner.py` — Three bug fixes + quadrant-forcing retired
- **Bug (a) fix** (protected-prefix blanket-freeze): replaced the broad `ubp_id.startswith(('ELEM_', 'LAW_', 'PARTICLE_', 'MOLECULE_', 'MATH_', 'PVE_'))` skip in `_refine_vectors` with a precise check: only skip words that are (1) hand-curated AND (2) whose `golay_codeword` field equals their current `vector`. PVE_ entries are no longer blanket-frozen — they CAN be refined if their co-occurrence profile shifts.
- **Bug (b) fix** (learned_edges never re-applied): added `_load_learned_edges()` method called from `__init__`. Iterates `self.state.learned_edges`, calls `crg.add_edge(src, label, dst)` for each, skips duplicates. Returns the actual count of edges added (not just attempted).
- **Bug (c) fix** (no flush-on-exit): registered `atexit.register(self._atexit_flush)` in `__init__`. Also flushes after `_refine_vectors` when `refined > 0`, so learning isn't lost between 5-query boundaries.
- **Quadrant-forcing retired** in `_learn_new_word` and `_refine_vectors` — both branch on `QUADRANT_FORCING_ENABLED`. Default path uses plain `GOLAY_ENGINE.snap_to_codeword` with no quadrant restriction.
- **Bonus fix (bug d)**: discovered during testing. The original `_check_for_new_edges` called `crg.add_edge(w1, "co_occurs", w2)` but `"co_occurs"` was not in `EDGE_LABELS`, so the call silently returned False. **The original "edge learning" was completely broken** — not just the reload path. Fixed by adding `"co_occurs"` to `EDGE_LABELS` in `GLM01_substrate.py`.

#### `GLM22_ontological_grammar.py` — Word-salad gate
- Added `max_verb_distance: int = 8` parameter to `OntologicalGrammar.construct_sentence`. When the nearest VERB to the gap vector is more than 8 bits away, the function returns `None` instead of producing a sentence. This lets `construct_paragraph` break the chain gracefully instead of emitting the word-salad that SESSION_SUMMARY §4 documented (`"Time ent beweeping. Beweeping minus_eleven over."`).

#### `GLM11_runtime.py` — `fresh=False` parameter + CRG-ALU exposure
- `chat_prose(query, fresh=False)`: when `fresh=True`, calls `self.manager.reset()` and resets `self._turn` before processing. This eliminates cross-topic bleed (SESSION_SUMMARY §4) for one-shot queries. Default `False` preserves existing multi-turn behavior.
- `crg_alu()`: lazily constructs and returns a `CRGTraversalALU` bound to this runtime's CRG + vocab. This is the public API for word-level sovereign computation.

#### `GLM01_substrate.py` — `co_occurs` added to `EDGE_LABELS`
- Added `"co_occurs"` to the allowed edge-label set. This is the root-cause fix for the original `_check_for_new_edges` silent failure (see bug d above).

---

## Test results

### Baseline (v3.16.0, before any changes)
- 26/26 self-tests pass (`GLM12_cli_entry.py --test`)
- 41/41 golden cases pass (`run_golden_cases.py`)

### v3.17.0 (after all changes)
- 26/26 self-tests pass ✅
- 41/41 golden cases pass ✅
- 30/30 `test_v317_levelling.py` tests pass ✅
- 16/16 `test_v317_signal_and_sovereign.py` tests pass ✅
- **Total: 113/113 tests pass**

### What the new tests prove

| Suite | Test | Claim verified |
|---|---|---|
| Levelling | `test_native_compute_equivalence` (13 ops) | Every numeric op returns the same answer as SymPy, with a real trace + fingerprint attached |
| Levelling | `test_sympy_demoted_to_validation` | SymPy's `isprime(97)` matches `NoiseALU.is_prime(97)`; `validate=False` skips SymPy entirely |
| Levelling | `test_crg_alu_traces_and_fingerprints` (5 sub-tests) | CRG-ALU produces real traces + real fingerprints; path fingerprinting is deterministic |
| Levelling | `test_no_quadrant_forcing` | `QUADRANT_FORCING_ENABLED=False`; alignment rate is 47.1% (not 100% as forcing would produce) |
| Levelling | `test_learned_edges_reapply` | `before=0 after=1` — learned CRG edges now re-applied on reload |
| Levelling | `test_atexit_flush` | `saved_query_count=1` — state flushed even when query_count is not a multiple of 5 |
| Levelling | `test_refine_does_not_freeze_only_prefixed` | PVE_ word `action` was considered for refinement (not blanket-skipped) |
| Levelling | `test_chat_prose_fresh_no_bleed` | `fresh=True` response has no `hamiltonian` in the first 200 chars when the query is about oxygen |
| Levelling | `test_generate_grammatical_no_salad` | 0/5 weak outputs across seeds `hamiltonian, time, energy, anomaly, lattice` |
| Signal | `test_native_metrics_always_present` (10 ops) | Every numeric op produces NRCI + lattice name |
| Signal | `test_sovereign_computation_uniformity` | Math and word operations produce the same `{result, trace, fingerprint}` shape |
| Signal | `test_nl_signal_retention` | ρ=−0.0655, p=9.21e-04 (n=2557) — statistically significant, correctly signed |
| Signal | `test_comparative_demo` | Live demonstration: `gcd(54,24)` now shows trace `[gcd(54,24): 54 mod 24 = 6, gcd(24,6): 24 mod 6 = 0]` + `nrci=0.9917 lattice='Identity'` |

---

## Architecture diagram (before vs after)

### Before (v3.16.0)
```
User query
  ↓
GLM11_runtime.chat()
  ↓
GLM09_tools.evaluate_numeric(comp)
  ↓
  ├─ math.gcd(a,b)         ← stdlib
  ├─ math.factorial(n)     ← stdlib
  ├─ sp.binomial(n,k)      ← SymPy (compute engine)
  ├─ sp.Matrix(...).det()  ← SymPy (compute engine)
  └─ math.sqrt(x)          ← stdlib

Output: {value, exact, approx}  ← no trace, no fingerprint, no metrics
```

### After (v3.17.0)
```
User query
  ↓
GLM11_runtime.chat()
  ↓
GLM09_tools.evaluate_numeric(comp)
  ↓
GLM25_native_alu.native_compute(kind, operands, validate=True)
  ↓
  ├─ NoiseALU().gcd(a,b)              ← native, returns trace + fingerprint
  ├─ NoiseALU().factorial(n)          ← native, returns trace + fingerprint
  ├─ ExactMath.icomb(n,k)             ← native, fingerprint applied
  ├─ LinearAlgebraALU().det_nxn(m)    ← native, fingerprint applied
  └─ ExactMath.sqrt_frac(f)           ← native, fingerprint applied
  ↓
[optional] SymPy cross-check
  ↓
Output: {value, exact, approx, trace, fingerprint, sympy_check, native=True}
                                ↑              ↑                ↑
                          step-by-step   NRCI + lattice    validation match
```

For word relations (NEW path):
```
User query (word relation)
  ↓
GLM11_runtime.crg_alu()
  ↓
GLM26_crg_alu.CRGTraversalALU(crg, vocab)
  ↓
  ├─ traverse(src, label, dst)
  ├─ shortest_path(a, b, max_hops=3)
  ├─ relate(a, b)
  ├─ chain(*words)
  └─ compose_path_fingerprint(path)
  ↓
Output: {result, trace, fingerprint}
                ↑              ↑
          hop-by-hop      NRCI + lattice
          BFS trace       of destination vector
```

---

## Migration notes (how to apply to your repo)

The v3.17 files live in `/home/z/my-project/download/GLM_v3.17/`. To apply to your `UBP_Repo`:

1. **Copy the two new modules** (no conflicts possible — they're additive):
   - `GLM25_native_alu.py` → `core_studio_v4.0/GLM/GLM25_native_alu.py`
   - `GLM26_crg_alu.py` → `core_studio_v4.0/GLM/GLM26_crg_alu.py`

2. **Apply the patches** to existing files. The cleanest way is to use `diff` against the v3.16 originals:
   ```bash
   diff core_studio_v4.0/GLM/GLM09_tools.py /home/z/my-project/download/GLM_v3.17/GLM09_tools.py
   diff core_studio_v4.0/GLM/GLM11_runtime.py /home/z/my-project/download/GLM_v3.17/GLM11_runtime.py
   diff core_studio_v4.0/GLM/GLM22_ontological_grammar.py /home/z/my-project/download/GLM_v3.17/GLM22_ontological_grammar.py
   diff core_studio_v4.0/GLM/GLM23_grammar_vectors.py /home/z/my-project/download/GLM_v3.17/GLM23_grammar_vectors.py
   diff core_studio_v4.0/GLM/GLM24_continuous_learner.py /home/z/my-project/download/GLM_v3.17/GLM24_continuous_learner.py
   diff core_studio_v4.0/GLM/GLM01_substrate.py /home/z/my-project/download/GLM_v3.17/GLM01_substrate.py
   ```
   All patches are clearly marked with `# v3.17.0` comments and `# BUG FIX (a/b/c/d)` annotations.

3. **Copy the test suites** to your repo:
   - `tests/test_v317_levelling.py`
   - `tests/test_v317_signal_and_sovereign.py`
   - `tests/run_all_v317_tests.py`

4. **Verify**: `python3 GLM12_cli_entry.py --test` should still report 26/26. `python3 tests/run_all_v317_tests.py` should report 113/113 total tests passing (26 self-tests + 41 golden + 30 levelling + 16 signal/sovereign).

5. **Opt-in legacy behavior** (only if you need to A/B test):
   ```bash
   GLM_QUADRANT_FORCING=1 python3 GLM12_cli_entry.py --test
   ```
   This re-enables the v3.15 quadrant-forcing path for direct comparison.

---

## What's NOT changed (deliberately)

- **`evaluate_symbolic`** still uses SymPy for differentiation/integration/ODE/Taylor/limits — no native UBP equivalent exists for these. The result could be wrapped in `symbolic_with_fingerprint` to attach a substrate fingerprint; this is a follow-up.
- **`generate_grammatical`** still uses the geometric construction approach (SVO via gap vector). The new `max_verb_distance=8` gate reduces word salad but doesn't eliminate it entirely — the underlying geometric relationship between noun pairs and verbs is sometimes genuinely too far. A follow-up would be to use the new `CRGTraversalALU.shortest_path` to find verbs that actually have a CRG relationship to the noun pair, rather than pure Hamming proximity.
- **The CRG is still ~173 edges for 4,261 words** — the SESSION_SUMMARY §10 noted this is drastically under-built (60.7 words per edge). v3.17 doesn't expand the CRG; that's a separate curation task. The `CRGTraversalALU` is the engine; it needs more fuel.
- **Tilt (`ubp_kb_architect.calculate_tilt`)** — still uses `numpy` and `math.acos`. The session summary noted Tilt is "mostly redundant with full Hamming distance" (§8). v3.17 doesn't change it.
- **The four `exp_l/m/n/o/p` and `exp_g_followup` scripts** — still have the hardcoded `glm_work/` path bug (SESSION_SUMMARY §4). v3.17 doesn't touch these; they're experimental scripts, not part of the runtime.

---

## Recommended next steps

1. **Wire `evaluate_symbolic` through `symbolic_with_fingerprint`** so differentiation/integration results also get substrate fingerprints. This completes the "native metrics everywhere" promise.

2. **Expand the CRG**. The `CRGTraversalALU` is ready; it just needs more edges. SESSION_SUMMARY §10 noted the CRG is "drastically under-built relative to the 4,248-word vocabulary (60.7 words per edge)". Consider:
   - Auto-expanding the CRG from the master resource's "related concepts" fields
   - Using the SVD signal to propose edges between words with low Hamming distance and high co-occurrence
   - Curating 100-200 more edges by hand for the most-queried physics concepts

3. **Use `CRGTraversalALU` in `generate_grammatical`**. Replace the pure Hamming-proximity object selection with `crg.shortest_path(seed, candidate)` — only chain through concepts that have a real CRG relationship. This would eliminate word salad at the source rather than gating it after the fact.

4. **Add a `chat_prose` topic-shift detector** that automatically calls `fresh=True` when the new query's content has <some-threshold overlap with the active zone's topic nouns. This would make `fresh=True` the automatic default for unrelated follow-ups, without requiring the caller to know about it.

5. **A/B test the SVD-only path against the legacy forcing path** on a real-world query set. The 47.1% quadrant alignment (vs. 100% under forcing) is expected; what matters is whether downstream quality (recall accuracy, response coherence) improves. The test harness here proves signal is retained; production A/B would prove end-to-end quality.

6. **Consider a `NoiseALU`-equivalent for symbolic differentiation**. The user's request was "all computation/calculation should always be UBP native where possible". Differentiation of polynomials CAN be done natively (coefficient × power → coefficient × power-1), and the substrate would then fingerprint the result. This would close the last gap in the "native-first" promise.
