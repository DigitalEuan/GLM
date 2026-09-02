# `glm_universal.evaluation` — the end-to-end CLI evaluation

The other measuring instruments in this package look at the machine from the
inside. `capabilities/` asks the library where it stops; `benchmarks/` scores
solver functions on curated and exhaustive task sets. Neither of them goes
through `GLM.py`, so neither of them measures what a user actually gets.

This sub-package does. Every case starts **`GLM.py` in a fresh interpreter** —
one subprocess per question, no shared session, no warm caches, nothing the
evaluation itself can prime — and scores exactly what a user would see: the
process's exit code and the `ANSWER` or `UNSOLVED` line it printed.

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.evaluation                     # all 131 cases
PYTHONPATH=. python3 -m glm_universal.evaluation --jobs 8            # in parallel
PYTHONPATH=. python3 -m glm_universal.evaluation --only analogy      # one query kind
PYTHONPATH=. python3 -m glm_universal.evaluation --case report-superposition
PYTHONPATH=. python3 -m glm_universal.evaluation --list              # the question set
PYTHONPATH=. python3 -m glm_universal.evaluation --json results.json
```

The exit code is 0 when every case passes and 1 when any case fails, so the
harness can be used as a gate.

## The question set

`cases.py` holds **131 cases**. Between them they cover **all 21 query kinds**
the runtime recognises (including `unknown`, the kind a question gets when
nothing else claims it) and **all 48 report subjects**. Coverage is not
asserted in prose: `test_evaluation.py` compares `KINDS_COVERED` and
`SUBJECTS_COVERED` against the runtime's own tables and fails when a kind or a
subject is added without a case.

Of the 130, **114 expect an answer and 16 expect a refusal** — all 16
classified `boundary`, and **no `gap` case left**.

A case declares what the honest outcome is:

* `expect="answer"` — with `contains`, the ground truth the answer must state,
  and optionally `forbids`, text that would mean the machine answered a
  different question.
* `expect="refusal"` — with `classification`, either

  * `"boundary"` — the machine *should* refuse, because answering would require
    crossing a limit that is a theorem or a deliberate design commitment
    (equality of two real processes is not decidable; the vocabulary is exactly
    the registers; a quotient by an exact zero names no value), or
  * `"gap"` — the machine *should* refuse today because the implementation is
    missing, and closing the gap would turn the case into an `answer` case.

## Where the run stands

The whole set runs **97 of 97**, with no wrong answers and no unexpected
refusals: every case either answers with the ground truth or refuses exactly
where it declared it would.

**No `gap` case is left.** The last one was `coherence PbCl2`: the formula
parser read `PbCl2` and the molecule codec would encode it — every coordinate
derived from the element register, so no new datum was needed — but each
solver resolved its operand against the names a register enumerates and
stopped there. Every solver that takes a carrier and nothing else now hands an
operand no register enumerates to the formula parser before refusing, which
is what `coherence-unregistered-molecule` and the `spatial`, `angle` and
`cluster` cases beside it check. Nothing is guessed: an unparseable formula
still refuses. The nine refusals that remain are all `boundary` — a theorem
or a stated commitment, not a missing implementation.

## The scoring is asymmetric on purpose

A refusal tells the user where the machine stops. A confident wrong answer does
not, so it is scored worse:

| outcome | meaning | weight | counts as a pass |
|---|---|---|---|
| `correct` | answered, and the answer contains the ground truth | +1 | yes |
| `refused_as_expected` | the honest answer was a refusal, and it refused | +1 | yes |
| `unexpected_refusal` | refused a question it should have answered — a gap | 0 | no |
| `wrong_answer` | answered where it should have refused, or contradicted the ground truth | −1 | no |
| `error` | crashed, timed out, or printed neither an answer nor a refusal | −1 | no |

`accuracy` is passes / cases. `score` is the weighted total / cases, so a run
that is right about everything scores `1` and a run that is confidently wrong
about everything scores `−1`. `test_evaluation.py` pins the asymmetry directly:
a synthetic run of one wrong answer scores strictly below a synthetic run of one
unexpected refusal.

## What comes back

`evaluation_report()` returns a plain dictionary — totals, per-kind breakdown,
the classification split of the expected refusals, and one record per case with
its outcome and, for a failure, the exact point at which it stops (`stops_at`).
`format_report()` renders it; `write_json()` writes it.

## Files

| file | what it holds |
|---|---|
| `cases.py` | the 131 cases, `cases_by_kind`, `KINDS_COVERED`, `SUBJECTS_COVERED` |
| `harness.py` | `run_case`, `run_all`, `evaluation_report`, `format_report`, `write_json` |
| `__main__.py` | the command line above |

The write-up of the current run — totals, per-kind accuracy, every failure, and
the split between boundaries and gaps — is
[`CAPABILITY_ASSESSMENT.md`](../../../CAPABILITY_ASSESSMENT.md) at the top of
the repository.
