# The answer censuses guarded by what their answers quote, and the replay gate as a step of the close

## Tier 0 — the coarse read

**Question.** Can a measurement that records the system's answers stop calling itself current after a stored measurement those answers quote has been re-taken, and can the evaluation's replay gate become a step of the close rather than a flag to remember?

**Verdict.** Yes, both. The evidence census and the result census now record, while they run, every stored measurement their answers open, and their digests cover those files: alter any one of them and the census turns stale. The close re-takes the two censuses last, in order, so a re-take earlier in the same stage cannot leave them stale. The replay gate is the sign-off instrument `replay`, re-run when what it reads has moved and signed like the others.

**Deciding figure.** 5 of 5 marks; 110 of 110 and 111 of 111 quoted measurements move their census's digest when altered; the replay instrument signed passed (171 of 171 answered cases verified by column 3).

**Recomputed by.** `glm_universal.reasoning.quoted_measurements_study.quoted_measurements_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 20 October 2026 (pre-registered and measured 20 October 2026, in one session; the marks were written with the measuring module before its first run, and none was restated).*

## 0. What this document is

A study for Phase 174. It takes two lines of To-Do item 7 of
[`STATUS.md`](../STATUS.md) §2.1, *the evidence model, in use, the rest*, left
by Phases 169 and 171
([`EVIDENCE_IN_USE_STUDY.md`](EVIDENCE_IN_USE_STUDY.md) §7.5):

* *The census's digest does not cover the stored measurements its answers
  quote, so it can hold a stale answer and call itself current; the same holds
  for any measurement that records answers* — hazard 4 of
  [`ITERATE.md`](../ITERATE.md) §0.1.
* *The gate is a flag of the evaluation, not yet a step of `signoff --close`.*

Neither changes an answer. Both change whether the repository can be trusted
to say when an answer it has stored is out of date, which is what every later
round of reasoning work stands on.

## 1. The mechanism

**What a census quoted.** `glm_universal/quoted_measurements.py` records,
inside a `with recording()` block, every file opened for reading under a
`_data` directory of the package — the stored measurements. It wraps `open`
(and `io.open`, through which `Path.read_text` and `Path.read_bytes` read) for
the block and restores them after; it interprets nothing. The evidence census
(`reasoning/evidence_model_study.py`, Phase 169) and the result census
(`reasoning/evidence_in_use_study.py`, Phase 171) run each evaluation question
inside such a block, store the union as `quoted`, and add those files to their
digest (`module_digest(quoted)`). A census never counts its own file, and the
evidence census never counts the result census's, which digests it: either
would be a cycle in which re-taking one stales the other for ever.

**The order of the close.** Stage 0 of `signoff --close` re-takes every stale
measurement cache. Since this round it re-takes the two censuses last, the
evidence census before the result census (`signoff.CENSUS_LAST`), and takes
them again in its second pass if an earlier re-take staled them.

**The replay instrument.** `python3 -m glm_universal.evaluation --replay-only`
runs the replay gate of Phase 171 without the evaluation; the sign-off
instrument `replay` (`signoff/checks.py`) is that command, with the gate and
the command line in its closure. `signoff --close` therefore runs it when, and
only when, what it reads has moved, and `--verify-release` counts it.

## 2. The marks

Written with the measuring module, before its first run; none was restated.

| mark | met when |
|---|---|
| **Q1** | both censuses record at least one stored measurement their answers quote |
| **Q2** | every quoted file, altered by one byte in a copy of the tree, moves the digest of the census that quotes it (n of n), and the unaltered copy reproduces the live digest |
| **Q3** | neither census quotes its own file; the evidence census does not quote the result census |
| **Q4** | stage 0 re-takes the censuses last, the evidence census before the result census, whatever order the stale caches arrive in |
| **Q5** | the `replay` instrument is declared, its closure holds `evaluation/replay.py` and `GLM.py`, and its last run is signed passed at the current digest |

## 3. What is not claimed

A file read before the recording began — at the import of a module imported
earlier — is not seen; the censuses start the recording before their own
imports, and Q1 counts what was seen, not what could have been. The recorder
sees stored measurements under `_data` only: a register or a document an
answer reads is guarded, as before, by the sources the census lists. The
replay instrument's closure is drawn the way the evaluation instrument's is
(the import closure of its entry points, plus `GLM.py` named outright), so a
change reached only through `GLM.py`'s own imports is seen by the evaluation
instrument's rule, not more finely. The release sign-off of the test files is
still owed (pytest is not installed here).

## 4. What came out

`PYTHONPATH=. python3 -m glm_universal.tools quoted-measurements` (computed
when asked, nothing stored).

| Mark | What | Result |
|---|---|---|
| Q1 | both censuses record what their answers quote | evidence census 110 stored measurements, result census 111 — **met** |
| Q2 | every quoted file, altered by one byte in a copy, moves the digest | 110 of 110 and 111 of 111; the unaltered copy reproduces the live digest — **met** |
| Q3 | no cycle | neither census quotes its own file; the evidence census does not quote the result census — **met** |
| Q4 | stage 0 re-takes the censuses last, in order | order ends `evidence_model_study`, `evidence_in_use_study` — **met** |
| Q5 | `replay` declared, closure holds `evaluation/replay.py` and `GLM.py`, signed at the current digest | declared, both in the closure, signed passed: 177 cases, 171 replayable, 171 verified, 6 without a column 3, failed none — **met** |

5 of 5 marks. With the censuses re-taken under the new digests, the evidence census
is 9 of 9 and the result census 7 of 7 (evaluation 223 of 223; 223 agree with
the Phase 169 census, 0 differ).

## In one paragraph

Yes, both. The evidence census and the result census now record, while they run, every stored measurement their answers open, and their digests cover those files: alter any one of them and the census turns stale. The close re-takes the two censuses last, in order, so a re-take earlier in the same stage cannot leave them stale. The replay gate is the sign-off instrument `replay`, re-run when what it reads has moved and signed like the others.

The figures: 5 of 5 marks; 110 of 110 and 111 of 111 quoted measurements move their census's digest when altered; the replay instrument signed passed (171 of 171 answered cases verified by column 3).
