# Direct GLM questions: method search and tests

This audit asks five direct questions of the GLM-adjacent surface:

1. can ties in Leech lattice calculations be resolved?
2. can lattice paths be travelled efficiently?
3. can XOR be computed in a 24D lattice?
4. can an optimal 2D square packing for `n` squares be found?
5. can any Rule 30 question be answered directly?

Four queries still return no declared method. **Packing now returns a declared
candidate**, discovered by decomposing the problem into overlap energy,
stress/relaxation and container constraints before searching the wheel material.
That candidate is the **Pressure Settling Engine** from W36/W37. It is a
fixed-container feasibility heuristic, not an optimality proof.

## Results

| Question | `cent discover` | Working facility | Test result | Verdict |
|---|---|---|---|---|
| Resolve Leech ties | gap | `move_corpus` lexical move-id tie-break | `a → {b,c}` tie predicts `b`; accuracy `1/2` | bigram tie only, not a Leech tie resolver |
| Travel lattice paths efficiently | gap | `move_corpus` net-displacement accounting | 24D path `e0,e1,e0` has net `[2,1,0…]`, squared norm `5` | accounting only; no shortest/optimal path planner |
| XOR in a 24D lattice | gap | `leech_class` exact class-word XOR | class words `1 ⊕ 2 = 3`; F2 rank `2`; audit `4/4` | working class-index utility, not an operation row |
| Optimal 2D square packing | **method** | W36 squared penetration/wall energy + W37 relaxation | exact fixed-container probe: initial energy `1` → final `0`; `optimal=false` | pressure-settling candidate; global optimality remains a gap |
| Answer Rule 30 directly | gap | none | no Rule 30 adapter, data or score | explicit gap |

The 24D tests use a synthetic diagonal basis with determinant `2^24`, not the
Leech lattice basis. They test parity coordinates and XOR mechanics, not Leech
geometry, a metric, a q-form or a shortest-path metric. The tie fixture is a
synthetic move corpus, not a lattice nearest-neighbour calculation.

Packing uses axis-aligned unit squares in a fixed square container. Its exact
probe resolves overlap and wall violation for the declared initial state. It
does **not** search all configurations, prove a lower bound, handle rotation or
arbitrary square sizes, or produce a physical device. `optimal=false` and the
first gap says “no global optimality certificate or exhaustive configuration
search.”

## What the compiler found

`cent matrix` now has 32 rows across 12 operations. Packing appears as a
`declared-analogy` row, separate from exact routes, structural templates,
declared bridges and text-only wheel candidates. `cent discover` returns the
Pressure Settling Engine for the packing query. The method records a **39-wheel
scan**: W36/W37 are selected, while W5/W6/W21/W32/W34/W40 remain adjacent
candidates because they do not declare both the objective and relaxation laws.

The four remaining direct queries are still boundaries, not hidden methods:

- the Leech modules audit caller-declared bases, moves and bigrams;
- the class-word map is an index utility outside the operation matrix;
- no geometric tie-break or path planner is declared;
- no Rule 30 adapter, input data or scoring rule is declared.

## Why the narrow utilities are not promoted

- **Tie:** the only implemented tie-break is the lexicographically smallest move
  ID in a bigram table. A Leech tie needs declared distance, candidate set and
  geometric rule; none is present.
- **Path:** net displacement is descriptive accounting. Efficient travel needs a
  declared graph, edge cost, start/goal and optimality criterion.
- **XOR:** class-word XOR is exact, but it is a class-index computation, not a
  physical compute or carry method. It does not supply the missing metric.
- **Packing:** W36/W37 supply the objective and relaxation laws, but not a
  global search or optimality certificate. The engine is deliberately labelled
  a heuristic.
- **Rule 30:** the Hypothesis Engine material describes Rule 30 work elsewhere,
  but no adapter or scoring rule is imported into cent.

## Reproduction

```bash
python3 tests/test_glm_direct_questions.py   # 12/12 checks
python3 cent packing --n 2 --side 3 --iterations 12
python3 cent discover "find an optimal 2D square packing for n squares" --json
python3 tests/run_all.py                     # 17 suites, 824/824 checks
```

The audit does not construct a Leech lattice, run a path search, prove a
packing optimum, execute a Rule 30 question, run a GLM or run Lean. It preserves
the distinction between a working narrow utility and a compiler method.

## Next development targets

- Define a Leech tie contract with a declared candidate set and resolution rule.
- Define a lattice-path contract with an edge cost and optimality criterion.
- Decide whether the 24D class-word XOR should be exposed as an index operation
  outside the physical operation matrix.
- Add an exhaustive or branch-and-bound packing proof for small declared `n`,
  then compare it with the pressure-settling heuristic.
- Add a Rule 30 adapter only with declared input, answer key and scoring rule.
