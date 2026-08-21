# `glm_universal/tests` — the test suite

**Parent:** `../README.md`

## Structure

| File | Tests | What it checks | Added in |
|---|---|---|---|
| `test_substrate.py` | 96 | Golay code, Leech lattice, MOG trio/sextet, digit stack (multi-MOG-cube) | v0.4.0 |
| `test_data_objects.py` | 177 | Codec round-trips, carrier invariants, register sizes (720/118/etc.) | v0.4.0 |
| `test_reasoning.py` | 94 | Griess product, trilinear form, metric, analogy, verifier, dimension layers | v0.4.0 |
| `test_runtime.py` | 181 | Parser, session, TCT engine, CLI | v0.4.0 |
| `test_semantic_lexicon.py` | 39 | SemanticConcept codec, primitive vectors, antonym distances | v0.5.0 |
| `test_physics_expansion.py` | 9 | The 41 v0.5.0 physics concepts | v0.5.0 |
| `test_physics_expansion_v2.py` | 5 | The 19 v0.5.1 physics concepts | v0.5.1 |
| `test_semantic_lexicon_runtime.py` | 21 | Runtime wiring of the semantic lexicon | v0.5.0 |
| `test_lexicon_subspaces.py` | 12 | The `lexicon.primitives` and `lexicon.relations` subspaces | v0.5.1 |
| `test_substantive.py` | 23 | Actual query answers (Li:Na::Be:Mg, hot:cold::fast:slow, etc.) | v0.5.2 |
| `test_wiring.py` | 23 | The v0.5.3 wiring (project, trilinear, coherence, lattice_projection) | v0.5.3 |
| `test_directive.py` | 31 | The five directive-mentioned modules (Moonshine, Niemeier, LLVQ, FWHT, Valorani) | v0.6.0 |

**Total: 610 tests, 5,877 subtests, zero failures.**

## Substantive vs structural tests

The test suite has two categories:

1. **Structural tests** (~550): check that codecs round-trip, the
   parser classifies correctly, scripts are float-free, layouts have
   24 coords, etc.  These catch implementation bugs but not semantic
   ones.

2. **Substantive tests** (~60, in `test_substantive.py`,
   `test_wiring.py`, `test_directive.py`): check actual query
   *answers* -- does `Li:Na::Be:?` return `Mg`?  Does
   `hot:cold::fast:?` return `slow`?  Does `trilinear 127 432 463`
   give `T = -3/32`?  These catch the kind of regression that
   adding 60 physics concepts can introduce.

## Running

```bash
cd /path/to/GLM                          # repo root, where GLM.py lives
PYTHONPATH=. python3 -m pytest glm_universal/tests/ -q
```

To run only the tests that don't need the CLI:

```bash
cd /path/to/glm_universal
PYTHONPATH=.. python3 -m pytest tests/ -q \
    --ignore=tests/test_runtime.py \
    --ignore=tests/test_semantic_lexicon_runtime.py
```
