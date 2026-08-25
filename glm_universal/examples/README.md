# `glm_universal/examples` — demonstration scripts

**Parent:** [`../README.md`](../README.md) · **Repository root:**
[`../../README.md`](../../README.md)

Six runnable scripts and one generated transcript. Each script has a `main`
and runs standalone; each is also importable, so the test suite can exercise
it rather than let it rot. Every one of them was run from a clean checkout at
the version this README describes, and the results quoted below are what they
printed.

## Scripts

| Script | What it demonstrates | Ends with |
|---|---|---|
| `demo_tct.py` | Three Column Thinking end to end: 7 questions (distance, analogy over physics, analogy over elements, Griess product, coherence, dimension projection, nearest element to a word), each answered in language, in exact mathematics, and by a generated script re-run in a fresh interpreter. The headline demonstration that the runtime works. | `ALL DEMOS VERIFIED` |
| `reasoning_showcase.py` | Can the GLM reason? 29 probes across seven themes — dimensional reasoning, the TAX / NRCI constants, retrieval and analogy, layered reasoning and where a truth stops holding, the migrated state, puzzle solving, and the limits stated as refusals. Nothing is narrated by hand: every line is read off the solution objects, and the last theme is made of questions the system *cannot* answer, so the capability claim is bounded from both sides. | `probes run: 29, as expected: 29, unexpected: 0` |
| `semantic_replacement.py` | What the inherited ARC-era concept graph contained, measured; what its stored carriers turn out to be a measurement of; and the grounded graph that replaces it — 1,705 notations, 357 meanings, 6,210 binary and 6,649 ternary edges, every edge re-derived from the meanings it joins. | `all edges re-derived from the meanings they join : True` |
| `encoding_poc.py` | Element + word encoding proof of concept, with exact `Fraction` distances throughout. Shows the approach that `data_objects/semantic_lexicon.py` formalised in v0.5.0. | `DONE — All distances computed with exact Fraction arithmetic.` |
| `integrated_nrci.py` | The coherence module's five-shell NRCI alongside the Griess metric, with the roots in shells 2 and 4 taken at a declared rational resolution rather than approximated silently. | `DONE — All values exact rationals …` |
| `scaled_carriers.py` | Scaled carriers and the carrier-space product, plain against coherence-weighted distance. | `SUMMARY` |

| Generated file | How to regenerate |
|---|---|
| `reasoning_showcase_transcript.md` | `PYTHONPATH=. python3 glm_universal/examples/reasoning_showcase.py --markdown > glm_universal/examples/reasoning_showcase_transcript.md` — do not edit by hand. `tests/test_reasoning_showcase.py` (14 tests) checks that the showcase still reproduces. |

## Running

```bash
cd /path/to/GLM                       # repo root, where GLM.py lives
PYTHONPATH=. python3 glm_universal/examples/demo_tct.py
PYTHONPATH=. python3 glm_universal/examples/reasoning_showcase.py
PYTHONPATH=. python3 glm_universal/examples/semantic_replacement.py
```

Options:

| Script | Flag | Effect |
|---|---|---|
| `reasoning_showcase.py` | `--no-verify` | skip column 3 — much faster, no subprocesses |
| | `--markdown` | emit GitHub-flavoured Markdown instead of plain text |
| | `--only <n>` | run one theme |
| | `--timeout <s>` | per-verification subprocess timeout (default 180) |
| `semantic_replacement.py` | `--no-write` | print the summary only |

`semantic_replacement.py` is the only script that writes anything: with no
flag it writes `semantic_graph.json` and `semantic_purge_plan.json` beside the
inherited state file, which it **reads and never writes**.

## Known limitations, stated rather than hidden

* `scaled_carriers.py` quantises to an integer scale by rounding through
  `float`, and prints one distance through `float` as well. It is kept as a
  proof of concept for that reason: the package proper is float-free, and this
  script is not part of it.
* `scaled_carriers.py`'s coordinatewise carrier product converges to
  "velocity" for all word pairs — a real limitation of that product, left in
  view rather than removed.
* `demo_tct.py` and `reasoning_showcase.py` spawn one subprocess per verified
  claim, so a full run of either takes minutes. `--no-verify` on the showcase
  removes the subprocesses.
