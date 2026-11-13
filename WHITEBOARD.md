# Whiteboard — the round in progress

## Tier 0 — the coarse read

**Question.** If this session stopped now, what would the next one need to
know to carry the round on?

**Verdict.** The platform round of 13 November 2026 is in flight: the repair,
the filing and the corpus gates are done, and the remainder below is the Lean
and intake work that is open.

**Deciding figure.** `intake check` reports one error and `lean_check`
thirty-six, and each names its own remainder.

**Recomputed by.** (hand-written argument; nothing to recompute)

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict
and the figure above are grounded in the body below, and
`glm_universal.corpus.checks.tier_report` fails if they stop being.*

*Last altered 13 November 2026 (platform round: the round in flight, what is done, and the command that resumes each open step).*

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

## Status

**Round in flight: the platform round of 13 November 2026** (the plan is
[`STATUS.md`](STATUS.md) §2.1 item 0a). Working branch
`freebuff/7d3bfafca6d92bfcfbf83364`, kept local until the session's end by the
owner's instruction.

**Done, and committed or ready to commit:**

* **P0, the repair** (`cb64b00`). `main` carried unresolved `git stash pop`
  conflicts from `8a7ddca` in six files; the five Python modules are restored
  to their pre-conflict content (byte-identical to `4c8e107`) and compile, and
  `GLM_REPOSITORY_MAP.md` is the current document rather than half a merge.
* **P1, the filing.** Twenty-seven root copies byte-identical to `done/` and
  thirteen duplicate folders discarded; the root `Rule30_GLM_Study` confirmed
  already in the build tree; the newer root `cent_compiler_v12` filed as
  `cent_compiler_v12_update`; `leechlean`, `cent_compiler_v12_2` and
  `lean_to_add` registered in the intake ledger; the 79 Lean files and 31
  documents of `lean_to_add` moved out of `src/lean` to
  `source_material/ToDo/lean_to_add`; the stray `archive/ARISTOTLE_SUMMARY.md`
  (a byte copy of the renamed Phase 183 note) removed.
* **P1, the caches.** The study manifests are synced (205 of 205, current),
  the corpus is refreshed (tier contract holds, 251 of 251 state documents,
  address books fresh, 589 of 589 inline figures), and the coverage claim's one
  defect is cleared.

**Green on 13 November 2026:** `corpus --check` (tier contract, coverage
claim, study manifests, address books, every generated block and figure), the
seven-phase plan in [`STATUS.md`](STATUS.md) §2.1 item 0a, and the smoke query.

**Two gates remain open**, each naming its own remainder under its section
below.

1. **One intake error.** `iter10_lorentzian` cites
   `RequestProject.GLM.GolayDeepHole`, which is a placeholder: it clears when
   the thirteen placeholder Lean files are restored
   (`studies/_lean_files_needed.md`), which is P2's first task. The four stale
   `cent_compiler_v12` `staged/` copies were removed (they duplicate the
   installed provisional wheels).
2. **Thirty-six Lean errors.** Thirteen placeholders in `GLM/`, six files held
   in `awaiting_recovery/` — `LorentzUnits.lean` waits on `LorentzImproper`,
   which waits on the `LorentzPlane` placeholder, so the chain returns together
   — and the declaration warnings.
3. **P2, the Lean toolchain.** Install elan + Lean 4.28 + Mathlib here (about
   6–8 GB and hours on two cores) and run `scripts/rebuild_lean.sh` in the
   background; the owner-machine build record stays the fallback.

**Standing hazards — read before running anything:** [`ITERATE.md`](ITERATE.md)
§0.1, and §0.5 for this workspace's own rules (venv and pytest, the 233 MB
knowledge cache, `--jobs 2`, logs outside the tree, no supplied material under
`src/`). The two that cost the most: don't edit documents while
`corpus --refresh` runs, and re-take `queryesc`, `budget-guard-frozen` and
`ties-ladder-frozen` first after editing `evaluation/cases.py`, then the rest,
then refresh the corpus last.
