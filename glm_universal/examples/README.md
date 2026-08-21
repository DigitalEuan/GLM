# `glm_universal/examples` — demonstration scripts

**Parent:** `../README.md`

## Scripts

| Script | What it demonstrates |
|---|---|
| `demo_tct.py` | Three Column Thinking demo (7 queries, all verified). The headline demonstration that the runtime works end-to-end. |
| `encoding_poc.py` | Element + word encoding proof of concept. Shows the approach that `data_objects/semantic_lexicon.py` formalised in v0.5.0. |
| `integrated_nrci.py` | NRCI + Griess metric integrated test. Exercises the coherence module's five-shell NRCI alongside the Griess distance. |
| `scaled_carriers.py` | Scaled carriers + carrier-space product. Known limitation: the coordinatewise product converges to "velocity" for all word pairs. |

## Running

```bash
cd /path/to/GLM
PYTHONPATH=. python3 glm_universal/examples/demo_tct.py
```

The TCT demo runs 7 queries through the runtime session, builds a
Three Column Thinking trace for each, verifies column 3 in a fresh
interpreter, and reports `ALL DEMOS VERIFIED` if all 7 match.
