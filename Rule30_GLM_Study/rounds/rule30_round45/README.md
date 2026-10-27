# Round 45 — Hypothesis Engine v17: the gate loop, made to work

This folder is self-contained: pure Python 3, standard library only, exact integer and `Fraction`
arithmetic only.

    python3 hypothesis_engine_v17.py            # full run, about 35 s -> out/engine_v17.{json,md}
    python3 hypothesis_engine_v17.py --quick    # smaller ranges, about 25 s
    python3 hypothesis_engine_v17.py --no-ledger    # ablation: no Lean provisions
    python3 run_round45.py [--quick]            # v15, v16, v17 side by side, scored -> out/round45_results*.md
    python3 test_round45.py                     # 28 checks (unit tests + one quick engine run)

| File | What it is |
|---|---|
| `hypothesis_engine_v17.py` | **Engine v17**: the TCT gate cascade after every stage (claim class → recompute → refutation audit → escalation → implication → Lean ledger), typed fixpoint rollback, the arrow (read trajectory), and the trajectory dialogue with its consistency check |
| `glm_layers.py` | Portable layered verdicts: `LayerProfile` (verdict rule per kind of claim, shape check, arrow), and the identity / explained-away / coincidence / exclusivity / escalation reads with real scales |
| `run_round45.py` | Runs v15, v16 and v17 (with and without the ledger, with automatic claim classes), and scores them against the Round 44 ground truth |
| `test_round45.py` | Tests |
| `V17_REPORT.md` | The report: the 12 defects found in v15/v16, what v17 does, results, caveats, Master Equation correspondence, hand-off notes |
| `out/` | Results of the runs: engine reports (statuses, layer profiles, arrows, gate log, dialogue) and score tables |
| `hypothesis_engine_v14.py`, `glm_guards.py`, `tax_guards.py` | Copied unchanged from `../rule30_round42/` so that v15–v17 run from this folder |
| `hypothesis_engine_v15.py`, `hypothesis_engine_v16.py` | The owner's uploads, copied unchanged |
| `glm_needs.py`, `needs_rule30.py` | Copied unchanged from `../rule30_round44/`: exact tools (centre column, Berlekamp–Massey, left diagonals) and the ground-truth table |

The Lean side is in `RequestProject/GLM/HypothesisEngine/` of the Lean project:

* `GateLoop.lean` — the contract of the gate loop: layered reads, escalate before assert and
  the arrow, typed rollback, and the soundness of the cascade. FORMAL.
* `GateLoopData.lean` — certifies v17's full-range H16 (no eventual period `p ≤ 64` with
  preperiod `≤ 30000`). CERT.

## Headline

Scored against the 24 statements whose answer was fixed in Round 44, before v17 existed:

| engine | right | wrong | overclaim | abstain |
|---|---|---|---|---|
| v16 (and v15) | 4 | 5 | 15 | 0 |
| v17 without the Lean ledger | 20 | 0 | 0 | 4 |
| v17 | 24 | 0 | 0 | 0 |

* v17's own gates find three of v16's wrong answers without any Lean input:
  * H19 is refuted by escalation (n = 11101);
  * H39 by widening the seed set (seed 111);
  * H36 by recomputation (the comparison was printed the wrong way round).
* They also stop all 15 overclaims.
* The Lean ledger then settles the four questions that need a proof: H16, H32, H33 and H44.

The caveats are in `V17_REPORT.md` §3. The ledger and the ground truth share sources, and the
claim classes were written by reading these same statements, so this is not a held-out test.
