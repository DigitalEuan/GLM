# The chat surface: one echo, the declared readings, and what a refusal means

## Tier 0 — the coarse read

**Question.** When the GLM is used as a conversation from the command line rather than as a batch of questions, does the surface say what it is doing — the question once, the readings it has, and why a question was not read?

**Verdict.** Yes, for the three defects the platform round of 13 November 2026 named under *use*. The interactive surface echoed every query twice, one echo its own and one the answer path's; it now echoes each query once, from the answer path alone. It had no way to say which readings a question may have; `:kinds` now lists the parser's own table — 30 declared readings, with `unknown` named apart — and nothing is typed twice. A question that matched no declared reading was refused with the bare word `unrecognised query`, while the machine's own reading of that refusal (the sentence matched no classification rule) was discarded; the interactive surface now says so and points at `:kinds`, and the batch line the evaluation pins is unchanged.

**Deciding figure.** 4 of 4 marks; the interactive surface echoes 2 of 2 queries once, `:kinds` prints 30 of 30 declared readings once each from the parser's table, a refusal says why in the interactive surface and not in the batch one, and the evaluation answers 237 of 237 with no answer moved.

**Recomputed by.** `glm_universal.evaluation.harness.evaluation_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

*Created 14 November 2026 (platform round, pre-registered and measured 14 November 2026, in one session; the marks were written before the last of them was run, and none was restated).*

---

## 0. What this document is

A study for the platform round's **P5, *use*** — the third of the seven phases
of [`STATUS.md`](../STATUS.md) §2.1 item 0a — taken with the Lean phase (P2)
set aside by the owner's instruction of 14 November 2026: *focus on developing
the system aside from Lean here*. P2 waits on a Lean toolchain this workspace
does not have; P5 does not.

The phase's line names three things: *carriers the evaluation's questions
name, the doubled query echo, refusal wording*. This round takes the two that
are defects of the surface rather than of the reading:

* **the doubled query echo** — the interactive surface printed `QUERY` twice
  for every question, once itself and once from the answer path;
* **refusal wording** — a question with no declared reading was refused with
  `unrecognised query` alone, while the machine's own answer (which names what
  was tried) was thrown away, and there was no way to ask what the readings
  are.

*Carriers the evaluation's questions name* is a reading change — a question
that names a carrier no register holds (`what is the address of iron`) would
have to be answered, or refused differently — and the To-Do list settles that
class of change in the opposite direction: reading a fresh rewordings now would
be a post-hoc fit, so a fresh held-out set comes first
([`STATUS.md`](../STATUS.md) §2.2, *the connected machine, the rest*). It is
left, and named in §3 below.

Nothing here changes an answer: every change is in what the interactive surface
prints around an answer, and the evaluation drives `GLM.py` in batch mode.

## 1. The mechanism

**One echo.** `_interactive` printed `QUERY   asked` itself and then called
`_batch_query`, which prints the query on every branch it has — `_render_text`
prints `trace.query` for an answer, and each refusal branch prints it before
the refusal. The echo in `_interactive` is removed, so the answer path is the
one place a question is echoed, and it echoes it as solved (the reply rewrite
of Phase 146 included).

**`:kinds`.** `_meta_kinds` reads `glm_universal.runtime.KINDS`, the parser's
one table — the table `test_evaluation.py` already holds to the runtime's own
kinds, and the one the state documents' figure for the query kinds is counted
from. It prints the declared readings four to a row, and names `unknown` apart
because `unknown` is where a question with no declared reading lands rather
than a reading of its own. No list is typed a second time: adding a kind to
`KINDS` adds it to `:kinds`.

**The refusal's meaning.** `Session._solve` returns, for an unrecognised
question, an `answer` saying the query was not recognised as any of the
declared kinds and an `error` of `unrecognised query`; the CLI printed only the
error. `_print_refusal_hint` reads the solution the session kept
(`session.last_solution`) and, when its kind is `unknown`, prints one line: the
sentence matched no declared reading, and `:kinds` lists all 30. It is called
from `_interactive` only — never from `_batch_query` — so the `UNSOLVED` line
the evaluation scores is exactly what it was.

## 2. The marks

Written before the last of them was run; none was restated.

| mark | met when |
|---|---|
| **C1** | in the interactive surface one query prints one `QUERY` line, for an answered question and for a refused one |
| **C2** | `:kinds` prints the parser's table: 30 declared readings, each once, with `unknown` named apart |
| **C3** | a question with no declared reading says so in the interactive surface, and the batch surface prints exactly what it printed before |
| **C4** | the evaluation answers every case it answered before, with no answer moved by the change |

## 3. What is not claimed

*Carriers the evaluation's questions name* is not taken here (§0). The
interactive surface still has no way to list the carriers a register holds or
to say which register a name nearly matched beyond the suggestion `resolve`
already attaches; `:domains` gives the registers and their sizes, and that is
all. The refusal hint is given for the kind `unknown` only: a question that
parsed to a real kind and then failed to resolve (`what is the address of
iron`) gets the resolver's own message, which already names the domain, and no
hint was added to it in this round. Phase 188 adds one for that second case —
the registers are where to look, and `:domains` lists them with what each
holds ([`ITERATION_LANE_STUDY.md`](ITERATION_LANE_STUDY.md) §5). It is a
surface line in the interactive mode only, and no answer moves.

The batch surface is deliberately untouched, so a user in batch mode gets no
`:kinds` pointer; the evaluation pins that line and a surface change there is a
change to every stored answer census.

## 4. What came out

The first three marks are the interactive tests of
`src/glm_universal/tests/test_runtime.py`; the fourth is the evaluation.

| Mark | What | Result |
|---|---|---|
| C1 | one `QUERY` line per query, answered and refused | 2 of 2 queries echoed once (`test_interactive_echoes_a_query_once`) — **met** |
| C2 | `:kinds` from the parser's table | 30 of 30 declared readings printed once each, `unknown` named apart (`test_interactive_lists_the_declared_readings`) — **met** |
| C3 | refusal says why, batch unchanged | the interactive surface prints the hint, the batch surface does not (`test_interactive_says_why_an_unread_question_was_refused`) — **met** |
| C4 | no answer moved | the evaluation answers 237 of 237 as before: 187 answered, 50 refused as expected, 0 confidently wrong — **met** |

4 of 4 marks.

## In one paragraph

Yes, for the three defects the platform round of 13 November 2026 named under *use*. The interactive surface echoed every query twice, one echo its own and one the answer path's; it now echoes each query once, from the answer path alone. It had no way to say which readings a question may have; `:kinds` now lists the parser's own table — 30 declared readings, with `unknown` named apart — and nothing is typed twice. A question that matched no declared reading was refused with the bare word `unrecognised query`, while the machine's own reading of that refusal (the sentence matched no classification rule) was discarded; the interactive surface now says so and points at `:kinds`, and the batch line the evaluation pins is unchanged.

The figures: 4 of 4 marks; the interactive surface echoes 2 of 2 queries once, `:kinds` prints 30 of 30 declared readings once each from the parser's table, a refusal says why in the interactive surface and not in the batch one, and the evaluation answers 237 of 237 with no answer moved.
