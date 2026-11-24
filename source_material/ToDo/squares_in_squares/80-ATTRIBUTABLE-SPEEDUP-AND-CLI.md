# 80 — Attributable speedup, dead code, an unbeaten row, and a CLI (run 121)

Four things: the run-120 speedup is re-measured so it is attributable (and the attribution changes), the dead
code is gone, the settler is pointed at a real unbeaten row, and the instruments get one command line.
Read-only: no row changed, no score moved, `submission.csv` and root `WHITEBOARD.md` untouched.

## 1. The speedup, made attributable

Run 120 compared 248 nodes / 140.8 s against 69 nodes / 30.6 s while three things changed together (generator,
width, ordering). The old generator is kept as `mode="sweep"` and re-run at the same width and ordering:

| generator | width | order | settled | nodes | time |
|---|---|---|---|---|---|
| sweep (run 119 settings) | none | none | 5/5 | 248 | 140.8 s |
| **sweep** (control) | 8 | contact-first | 5/5 | **60** | **25.8 s** |
| intersection (run 120) | 8 | contact-first | 5/5 | 69 | 31.2 s |

**The speedup is the width limit plus the contact-first ordering** (4.1x fewer nodes, 5.5x less time at the
same generator), and **the intersection generator is slightly slower** than the sweep it replaced (69 vs 60
nodes; 75 353 vs 53 364 raw candidates). What it buys is *derivation instead of guessing*: no lattice step can
miss a determined anchor, and no sweep parameters remain. The prefilter and memo hit rates in doc 79 §2 stand
as measured; their isolated share of the time is **not** isolated and is not claimed.

## 2. Dead code removed

* `_offset_cache` / `_OFFSETS` (the 2-D field-lattice enumerator abandoned in run 119) — deleted; it returned
  an empty list since the solves landed.
* the unused `lattice=` parameter of `lattice_candidates` — deleted.
* `determined_candidates` is kept, but only as `mode="frontier"`: its closure is evidence, not dead weight.

The suite audit is now **655 decision functions, 0 offenders**, with `anchor_chain` at **42**: the trim
removed the abandoned enumerator and added the `sweep_candidates` control, so the count went up by one.

## 3. An unbeaten grid row

`sq_cli.py row N` points the settler at a table row, with the target side equal to that row's grid side
`k = ceil(sqrt n)`, and then **classifies the stall** by asking the generator for anchors at the deepest state.

| row | k | delivered | status | settled | nodes | stop | anchors still available |
|---|---|---|---|---|---|---|---|
| **n = 12** | 4 | 4.0000000015 | **unbeaten** | **8/12** | 21 | node cap 20 | **73** |
| n = 23 | 5 | — | unbeaten | — | — | > 900 s wall clock | not reached |

**Verdict for n = 12:** the stall is a **budget/order limit**, *not* exhaustion and *not* a missing command —
73 determined anchors are still available at the deepest state, so the grammar can extend it; the search simply
did not get there inside 20 nodes. That is the honest classification the three-way question asks for.

**Verdict for n = 23:** no result within the wall clock; the honest label is **throughput-limited**, not
exhaustion (the state space was nowhere near closed) and not a missing command (candidates were still being
produced). The cost per node grows with the placed count — each node constructs and tests thousands of exact
`Fraction`/`Quad` candidates — and that, not the grammar, is now the binding constraint on rows of 16+ cells.

## 4. A CLI

`scripts/sq_cli.py` is the pipeline entry point, and it is thin: it drives the instruments that already exist.

```
python3 scripts/sq_cli.py settle 5 2+1/2r2 --width 8      # forward settler at an exact side
python3 scripts/sq_cli.py row 12 --cap 20                 # a table row, with the stall classified
python3 scripts/sq_cli.py verify 10                       # a certified row as an admitted anchor chain
python3 scripts/sq_cli.py audit                           # bytecode float audit
```

Sides are typed exactly (`3`, `2+1/2r2`, `7/2+1/2r7`) and parsed into the field with `Fraction` arithmetic;
`row` writes `workspace/push/gridrow120.json`; `verify` prints the chain with each anchor's gate verdict.

## 5. Checks

| check | result |
|---|---|
| `anchor_chain.py --selftest` | both exact rows, 28/28 anchors, refusal at exact slack `-1/4` |
| `sq_cli.py verify 10` | side `3 + 1/2 sqrt2`, 10 anchors, 0 overlaps |
| `sq_cli.py row 12 --cap 20` | 8/12, 73 anchors available at the stop — budget, not exhaustion |
| `sq_cli.py audit` | 106 functions over `anchor_chain` + `exact_field`, 0 offenders |
| `glm_wheels.py --audit` | **655 functions, 0 offenders**; `anchor_chain` 42, none naming float |
| `sqscore.py`, `record_guard.py`, `void_insert.py --selftest` | green |
| `submission.csv`, `WHITEBOARD.md` | untouched |
