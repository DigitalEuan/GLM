# Round 44 results: the needs wheel

## Rule 30 (40 statements)

| condition | right | wrong | overclaim | abstain |
|---|---|---|---|---|
| base (no wheel) | 8 | 12 | 15 | 5 |
| guard only | 18 | 0 | 0 | 22 |
| requested provisions | 28 | 0 | 12 | 0 |
| requested + guard | 40 | 0 | 0 | 0 |
| all provisions + guard | 40 | 0 | 0 | 0 |
| random same-size + guard #1 | 40 | 0 | 0 | 0 |
| random same-size + guard #2 | 40 | 0 | 0 | 0 |
| random same-size + guard #3 | 40 | 0 | 0 | 0 |
| random same-size + guard #4 | 40 | 0 | 0 | 0 |
| random same-size + guard #5 | 40 | 0 | 0 | 0 |

Leave-one-out (all other provisions + guard):

| removed | right | wrong | overclaim | abstain |
|---|---|---|---|---|
| without RANGE-CENTRE | 39 | 0 | 0 | 1 |
| without TOOL-BM | 40 | 0 | 0 | 0 |
| without RANGE-LDIAG | 40 | 0 | 0 | 0 |
| without RANGE-SEEDS | 39 | 0 | 0 | 1 |
| without RECOMPUTE | 40 | 0 | 0 | 0 |
| without LEDGER | 30 | 0 | 0 | 10 |
| without IMPLICATIONS | 37 | 0 | 0 | 3 |

Requested provisions: RANGE-CENTRE, TOOL-BM, RANGE-LDIAG, RANGE-SEEDS, RECOMPUTE, LEDGER, IMPLICATIONS

Needs no provision could meet: range:ldiag:predicted, test:APP.conversation.reset, test:APP.deephole.ladder, test:APP.evidence.prediction, test:APP.lattice.addressing, test:APP.rcalculus.model, test:APP.retrieval.uniformity, test:GAP.centre.diagonal.connection, test:GAP.chain.explanation, test:GAP.ratio.growing

## Synthetic ARC

development 44 puzzles, held-out 120 (held-out families are different from the development families)

| condition | right | wrong | refused |
|---|---|---|---|
| base (no wheel) | 19 | 0 | 101 |
| requested (from development needs) | 72 | 0 | 48 |
| all provisions | 106 | 0 | 14 |
| random same-size #1 | 66 | 0 | 54 |
| random same-size #2 | 67 | 0 | 53 |
| random same-size #3 | 55 | 2 | 63 |
| random same-size #4 | 61 | 0 | 59 |
| random same-size #5 | 73 | 2 | 45 |
| on-demand (per-puzzle needs) | 108 | 0 | 12 |

Requested from development needs: gravity_down, fill_enclosed, scale, crop_largest, draw_lines, denoise, mirror_h

Diagnosis on held-out refusals: {"refused_by_base": 101, "need_stated": 89, "unknown": 12, "need_served_and_solved": 89}

## Real ARC (tasks shipped in glm_repo.zip)

53 test grids

* base: {'refused': 53}
* on-demand, provisions V1: {'right': 2, 'wrong': 0, 'refused': 51}
* on-demand, provisions V2 (+ recolour_by_feature): {'right': 2, 'wrong': 0, 'refused': 51}
* stated needs: {'primitive:unknown': 37, 'primitive:recolour-objectwise': 12, 'primitive:gravity-down': 2, 'primitive:fill-enclosed': 1, 'primitive:crop': 1, 'primitive:gravity-left': 1, 'primitive:gravity-right': 1, 'primitive:gravity-up': 1, 'primitive:scale': 1}
