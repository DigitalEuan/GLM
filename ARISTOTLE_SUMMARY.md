# Summary of changes for run c52d76f0-fe22-4188-b7c2-12ec941d3e83
I ran one round of experiments (Phase 156), using your friction analogy to choose them. Each mechanism got success criteria and a control, committed before any measurement: 12 original criteria, 9 amended ones fixed after the first run, and 4 for the fixes. Write-up: `studies/FRICTION_STUDY.md`.

**1. Moving the questions — what holds.** I took all 222 evaluation questions and moved each one a little in seven declared ways: add `?`, capitalise, double the spaces, prefix *please*, prefix *can you tell me*, transpose two letters, drop a *the*. Each run was scored *hold* (still right), *stick* (refuses) or *slip* (answers wrongly), 1,291 runs in all.
- **Surface changes hold:** 625 of 650 runs.
- **Wording changes mostly stick rather than slip.** Under motion the machine refuses rather than guesses.
- **Of the 26 slips, 19 were refusals the evaluation harness can't read** (a `REFUSED` line from the stepwise planner). The other 7 were real wrong answers, all from *can you tell me*: six read the "me" as the dimension M, e.g. *"can you tell me meaning of water" → 'me' denotes dimension M*.
- **Fix:** `GLM.py` now has `settle_question`. It collapses runs of spaces, and treats a leading *tell me* as politeness unless *about*, *whether* or *if* follows.
- **After the fix, 1,136 of 1,291 moved questions hold and none slips.** Doubled spaces and *can you tell me* now hold on all 222.
- **Every evaluation question passes before and after the fix, and every outcome is the same.** One answer line still differs: a lattice distance in `corpus address of seven` changed because the corpus is the project's own text and grew between runs. That criterion asked for identical lines, so it is recorded as missed.

**2. Contact over the whole prompt.** The text model picks the next word from the last two words only (a contact patch of two asperities). I tried weighting each candidate by how many of the prompt's words it is associated with (real contact area). Test: 1,000 held-out sentences.
- **At full weight it does worse:** 4,201 correct next words against 4,312.
- **The signal is real but small:** each variant beats the same rule driven by an unrelated sentence's words.
- **Kept under the two-word count, it gains 203 correct words but loses precision.**
- **Continuations escape the corpus's deepest rut** (*"… the same way"*), but then fall into new ruts of their own.

**3. Stick-slip — a reading that holds until clearly beaten.** I read sentences word by word and guessed which of the project's 138 directories each came from, with and without a "hold your guess" margin.
- **The holding reader never changes its mind more often.** This is proved in Lean for any margin.
- **It almost eliminates flip-flops** (returns to an earlier guess: 15 down to 1).
- **But it ends correct less often** (232 against 272). Most of the reader's changes of mind carry information. Holding a guess only helps where the swings are noise.

**Lean.** `overlay/glm_lean/RequestProject/GLM/Friction.lean` has no `sorry` and uses only the standard axioms. It proves:
- the holding reader switches no more often than the leader (`held_switches_le`, `stick_switches_le`);
- the held reading always stays within the margin of the leader (`held_within_margin`);
- the contact weighting never overturns a large lead, and with no prompt words it ranks exactly like the two-word count (`contact_keeps_large_lead`, `contact_empty_prompt`).

The full `lake build` passed earlier in this session, and the new module was rebuilt after the last edit.

**Score:** 5 of 12 original criteria, 5 of 9 amended, 3 of 4 fix criteria. The misses are kept as misses.

**Status of checks:**
- The new tests (`tests/test_friction.py`, 17 of 17) pass, run by hand because pytest can't be installed here.
- The document check (`corpus --check`) is current, and the full evaluation passes 222 of 222.
- `signoff --close` still needs pytest and is still outstanding.
- Running some existing test files by hand turned up older failures, recorded in `STATUS.md`:
  - `runtime/session.py` is 4,716 lines, over its test's 4,500 limit.
  - `test_figures` fails on the stored suite sentence (*183 test files*), which only a pytest sign-off re-takes.
  - Four test files had no row in the tests README; I added them.

**Other updates:** `tools friction`, `MASTER_PLAN.md`, `STATUS.md`, `SYSTEM.md`, `WHITEBOARD.md`, the paper (§20.30) and the package READMEs. Everything is committed and pushed.

**Next steps** (`STATUS.md` §2.1, item 4):
- **Typos are the main remaining weak spot:** 155 of 196 transposed-letter questions are refused. A "did you mean" that reads a word by spelling and by usage is the candidate; it changes refusals the evaluation pins, so it needs a before/after comparison.
- Let the harness read `REFUSED` lines.
- Add "wear" so continuations stop reinforcing themselves.
- Try a holding margin set from how noisy the leader is.