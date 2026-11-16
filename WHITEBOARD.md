# Whiteboard — the round in progress

## Tier 0 — the coarse read

**Question.** If this session stopped now, what would the next one need to
know to carry the round on?

**Verdict.** The platform round of 13 November 2026 is in flight: the repair,
the filing, the corpus gates, the Lean registry, the chat surface and the
iteration lane are done, and what remain open are P2, the Lean toolchain and the
owner's build record, and P5's third line, *carriers the evaluation's questions
name*.

**Deciding figure.** `intake check` reports 0 errors, `lean_check` is **OK**,
and the chat surface's study reports 4 of 4 marks.

**Recomputed by.** (hand-written argument; nothing to recompute)

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict
and the figure above are grounded in the body below, and
`glm_universal.corpus.checks.tier_report` fails if they stop being.*

*Last altered 15 November 2026 (Phase 189: the two received Lean deliveries censused and triaged — `lean_to_add` and `leechlean` are at *triaged*, 0 of 163 item-local imports resolving, the port and the build owed to the owner's machine).*

*Last altered 15 November 2026 (the Squares in Squares probe: filed and measured — 22.218057 working against 22.642387 documented, the public merge and the tighter clearance both null; and `--jobs 8` in the hazards line, which still said 2).*

*Last altered 14 November 2026 (Phase 188: the iteration lane — the machine's
eight CPUs, the evaluation's own default worker count, the cheap lane and the
close in one order; and the surface's second refusal hint).*

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
[`STATUS.md`](STATUS.md) §2.1 item 0a), with **Phase 187** taken on 14 November
2026. Working branch `freebuff/42d4bc4f5e39502a40d110e9`.

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
* **P1, the caches.** The study manifests are synced (206 of 206 with this
  round's study), the corpus is refreshed, and `corpus --check` is current.
* **P2, the registry.** The 36 Lean errors were one defect — the build tree
  contradicting `studies/_lean_files_needed.md` — and are cleared: the twelve
  placeholder stubs, the six byte-identical held copies and `Scratch.lean`
  removed from the build, `AxiomAuditAll.lean` regenerated, and `lean_check`
  **OK** (0 errors, no duplicate Lean file). No Lean toolchain: **no build**.
* **P3, the workflow (14 November 2026), measured here.** A venv with pytest
  at `~/glm/venv` (`python3 -m venv ~/glm/venv && ~/glm/venv/bin/pip install
  pytest`); the knowledge cache warmed once with
  `PYTHONPATH=src python3 -c "from glm_universal.knowledge import model;
  model.load()"` (84 s, 167 MB, git-ignored) — without it every CLI case spends
  about 106 s counting the corpus; `--jobs 2`; logs outside the tree in
  `~/glm/`. **Background jobs do not survive a tool call in this workspace:**
  anything longer than five minutes runs in the right-side terminal
  (`PYTHONPATH=src python3 -m glm_universal.evaluation --jobs 2`).
* **P3, the workflow, corrected (14 November 2026; Phase 188,
  [`studies/ITERATION_LANE_STUDY.md`](studies/ITERATION_LANE_STUDY.md), 4 of 4
  marks).** The workspace offers **8 CPUs**, not 2: `evaluation.harness.default_jobs()`
  now answers with them (capped at 8) and is the default of the evaluation and
  the replay gate, so `--jobs` is only needed to lower it. Measured: 8 cases
  64.4 s at `--jobs 1` against 8.9 s at `--jobs 8`; the whole evaluation 237 of
  237 in 248 s. `ITERATE.md` §0.5 now carries the measured machine, the cheap
  lane (`corpus --check`, touched tests, `--only KIND`, `--case`), the
  censuses-last close order, the empty sign-off ledger and the one-off that
  would fill it, and the four units that already fail on the inherited tree.
* **P5, the chat surface (14 November 2026; Phase 187,
  [`studies/CHAT_SURFACE_STUDY.md`](studies/CHAT_SURFACE_STUDY.md), 4 of 4
  marks).** The interactive surface echoes a query once (the answer path's
  echo is the only one), `:kinds` lists the parser's own table (30 declared
  readings, `unknown` apart), and a question with no declared reading says so
  and points at `:kinds` — in the interactive surface only, so the `UNSOLVED`
  line the evaluation pins is unchanged; the evaluation answers 237 of 237 with
  no answer moved. Commands:
  `printf ':kinds\nwhat colour is the sky\n:quit\n' | PYTHONPATH=src python3
  src/GLM.py --interactive --no-banner`.

**Measured since the last round (15 November 2026): the owner's Squares in
Squares project.** It is filed as `source_material/ToDo/squares_in_squares`
(commit `6d41e27`, its own `packlib` gate passes here) and it answers where the
score stands, which its own documents had behind: the working submission is
**22.218057**, the quoted 22.642387 is `submission.run36.csv`. A merge with the
strongest public file and a re-opening of the 2e-9 contact clearance were both
measured null (22.218056852 and a 1.8e-8 move), so what is left to the leader
(22.0544) is 0.1637 of packings, not of precision. It is not a GLM claim and
touches no answer; the item's record carries the numbers.

* **P4, the Lean intake triage (15 November 2026; Phase 189,
  [`studies/LEAN_DELIVERIES_CENSUS_STUDY.md`](studies/LEAN_DELIVERIES_CENSUS_STUDY.md)).**
  The two items filed on 13 November at `received` are now *triaged*, on a
  measured census: `lean_to_add` (79 supplied files, 1,999 declarations) and
  `leechlean` (8 files of Lean beside a Python package). 6 of the 87 supplied
  files are byte-identical to tree files, 8 are byte-identical to each other,
  and 0 of the 163 item-local imports resolves — the deliveries are rooted at
  flat `RequestProject.*`/`FirstPrinciples.*`/`Projection.*` while the tree's
  modules are all `RequestProject.GLM.*`.  So absorption is a re-rooting port
  and its only check is `lake build`: no file was moved into `src/lean`.
  `intake check` 0 errors; `leechlean`'s codec demo runs here (1,686 of 1,686
  ticks on the lattice, byte-exact round trip `True`); `LeechLeanCodec.lean`
  imports the misspelled `LechLeanGolay` and cannot build as supplied.
  **Owed:** the port (per item `next_step`), and none of the thirteen missing
  Lean files is in either delivery.

**Two gates remain open**, each naming its own remainder under its section
below.

1. **P2, the Lean toolchain and the owner's build record.** Install elan +
  Lean 4.28 + Mathlib here (about 6–8 GB and hours on two cores) and run
  `scripts/rebuild_lean.sh`, or take the owner-machine build record as the
  fallback. Every item absorbed ahead of it then clears with
  `python3 -m glm_universal.intake confirm-build <id>`; the 13 files of
  [`studies/_lean_files_needed.md`](studies/_lean_files_needed.md) stay owed;
  three of them (`LeechShells`, `LorentzPlane`, `AdversarialDialogue`) now have
  proposed rebuilds in `source_material/ToDo/lean_recovery/`, so the build has
  something to compile before the rest is written.
2. **P5's third line, *carriers the evaluation's questions name*.** A question
   naming a carrier no register holds (`what is the address of iron`) is
   refused; reading it is a change to an answer, and [`STATUS.md`](STATUS.md)
   §2.2 (*the connected machine, the rest*) says a fresh held-out set comes
   first.

**Standing hazards — read before running anything:** [`ITERATE.md`](ITERATE.md)
§0.1, and §0.5 for this workspace's own rules (venv and pytest, the counted
knowledge cache, `--jobs 8` (the machine's own count), logs outside the tree, no supplied material under
`src/`, background jobs do not survive a tool call). The two that cost the
most: don't edit documents while `corpus --refresh` runs, and re-take
`queryesc`, `budget-guard-frozen` and `ties-ladder-frozen` first after editing
`evaluation/cases.py`, then the rest, then refresh the corpus last.
