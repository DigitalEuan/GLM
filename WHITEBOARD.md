# Whiteboard — the round in progress

## Tier 0 — the coarse read

**Question.** If this session stopped now, what would the next one need to
know to carry the round on?

**Verdict.** No round is in flight: Phase 127 (norm 256 and the hex colour:
the empty norm-256 rung filled by the first-hex-digit reading, the rotated
Leech rung retired, the hex shortcut held on every point checked, and the
ladder found answering 8 of 568 held-out queries wrongly; 7 of 8 marks) and
Phase 126 (inert variables, 7 of 7 marks) are closed and recorded in
`MASTER_PLAN.md`. The next round starts from the To-Do list, `STATUS.md` §2.1.

**Deciding figure.** 0 steps outstanding.

**Recomputed by.** (hand-written argument; nothing to recompute)

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict
and the figure above are grounded in the body below, and
`glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## How to use this file

**Write it while the round runs, not after it.** If a session ends here, this
is what the next one reads first: what is done, what is half-done, and the
exact command that resumes it. A step finished is a line changed here, before
the next step starts — not a note to write up later.

When the round closes, its content moves into [`STATUS.md`](STATUS.md) (the
present tense) and [`MASTER_PLAN.md`](MASTER_PLAN.md) (the past tense), and
this file goes back to the shape below. That is the same rule the rest of the
repository keeps: the state document holds what *is*, the plan holds what
*happened*, and this holds only what is *in flight*.

Two habits earn their keep, and both were learned by losing work to their
absence:

* **Record the command, not the intention.** "Re-take the escalation cache" is
  not resumable; `python3 -m glm_universal.tools queryesc --write` is.
* **Record what a step will invalidate.** A release signs the tree it ran on;
  editing a document afterwards makes the units that read it stale again, so
  the order is documents first, refresh, then release.

## Status

**No round is in flight.** Phase 127 is closed (norm 256 and the hex colour,
taken from `STATUS.md` §2.1 item 1 with the owner's note): the
pre-registration and `RequestProject/GLM/HexRung.lean` first, then
`reasoning/norm256_hex.py`; the measurement is `tools norm256-hex` (cache
re-taken with `--write`). The study is
[`studies/NORM_256_HEX_STUDY.md`](studies/NORM_256_HEX_STUDY.md), 7 of 8
marks. The record is [`MASTER_PLAN.md`](MASTER_PLAN.md), "Phase 127". The
next round starts from the To-Do list, `STATUS.md` §2.1; 0 steps of Phase 127
are outstanding.
