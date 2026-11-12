# Fixed GLM/cent question corpus

The fixed corpus is
[`tests/fixtures/glm_cent_questions.json`](../tests/fixtures/glm_cent_questions.json),
run by [`tests/test_question_corpus.py`](../tests/test_question_corpus.py).
Each entry invokes one stable `cent` CLI command with `--json` and pins its exit
code, selected JSON fields, list lengths or refusal diagnostics.

This is an evidence and reproducibility corpus. It is **not** a GLM benchmark,
does not call a language model and does not claim a Rule30 or ARC-AGI score.

## Questions

| ID | Question | Stable command | Pinned outcome |
|---|---|---|---|
| `compile-kcl-sum` | What proposal and template does `y = x + z` produce? | `cent compile "y = x + z" --json` | `cent-compile/1`, `kcl_summer`, `proposal_effect=none`, not fabricated |
| `discover-sqrt` | How many declared compute methods exist for a square root? | `cent discover "compute a square root" --json` | 5 compute methods across 4 domain labels |
| `discover-carry` | What carries an irrational value as a physical signal? | `cent discover "carry an irrational value as a physical signal" --json` | one `carry` method: delta-sigma; not a compute algorithm |
| `matrix-mult` | What evidence exists for multiplying two signals? | `cent matrix --operation mult --json` | 6 rows: 1 structural template, 5 inherited candidates, 0 exact routes |
| `assemble-sum` | What is `1/2 + 1/3` on the KCL route? | `cent assemble sum-kcl --input 1/2 --input-b 1/3 --json` | exact `5/6`, simulation passed |
| `assemble-difference` | What is `1/2 - 1/3` on the KCL route? | `cent assemble sum-kcl --input 1/2 --input-b 1/3 --operation difference --json` | exact `1/6`, simulation passed |
| `derive-thermal` | Derive thermal energy from mass, heat capacity and temperature. | `cent derive W8.energy W8.mass W8.specific_heat_capacity W8.temperature --json` | `W8.mass * W8.specific_heat_capacity * W8.temperature`, coefficient `1` |
| `derive-disjoint-gap` | What happens when thermal inputs cannot reach wavelength? | `cent derive W9.wavelength W8.energy W8.temperature --json` | `gap`: disjoint declared-axiom components |
| `axiom-counts` | What are the global axiom-graph counts? | `cent axioms --json` | 39 wheels, 98 axioms, 230 quantities, 65 dimensions, 54/57 junctions |
| `physical-reference-gap` | Is the log-domain route fabrication-ready? | `cent physical sqrt-log --range 1/2:1 --json` | `reference topology; not fabrication-ready`; gaps remain |
| `discover-unmatched-gap` | What happens for an undeclared quantum-gravity request? | `cent discover "compute a quantum gravity bridge" --json` | unmatched; one suggestion and an explicit gap |
| `refuse-unknown-function` | Is an unsupported function refused? | `cent compile "y = notafunction(x)" --json` | exit `2`; no guessed method |
| `refuse-invalid-operation` | Is an undeclared matrix operation refused? | `cent matrix --operation not-an-operation --json` | exit `2`; declared vocabulary only |

The two refusal entries intentionally produce **no JSON**. The three gap
entries return a structured JSON payload whose certificate status is `gap` or
whose outcome is explicitly partial. None is converted into a pass.

## Corpus schema

```json
{
  "schema": "cent-question-corpus/1",
  "questions": [
    {
      "id": "stable-id",
      "question": "human-readable question",
      "argv": ["cent-subcommand", "...", "--json"],
      "expect": {
        "exit": 0,
        "json": true,
        "fields": {"schema": "cent-.../1"},
        "length_eq": {"methods": 5},
        "length_gte": {"gaps": 1},
        "stderr_contains": ["diagnostic"]
      }
    }
  ]
}
```

`argv` excludes the Python interpreter and the `cent` path; the runner supplies
both. Field paths use dot notation and integer list indexes. The runner accepts
only the declared `cent` subcommands and a fixed expectation vocabulary.

## Run it

```bash
python3 tests/test_question_corpus.py   # 16/16 checks
python3 tests/run_all.py                # 17 suites, 824/824 checks
```

The corpus suite currently contains **13 questions** and **16 checks**: 13
question executions plus three corpus-integrity checks. It is part of the
canonical gate, so an intentional CLI/schema change must update the corpus and
its pinned answers together.

## Explicit limits

- No GLM model is invoked; the corpus tests the declared cent evidence surface.
- No Rule30 or ARC-AGI adapter, input dataset or scoring rule is declared, so no
  benchmark result is claimed.
- Commands requiring caller-declared external files (for example
  `cent leech-class`) are not included; D5 and D10b–D10e remain blocked.
- Proposal generation, reference netlists and fabrication geometry are not
  fabricated-device evidence. The corpus preserves their explicit boundaries.
