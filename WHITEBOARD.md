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

*Last altered 17 November 2026 (the item's own tables checked: the stale
43-entry per-wheel junction copy replaced by the operative 59-pair
`index.json` table, 50 sound edges, and the four declared analogies refused).*

*Last altered 17 November 2026 (the packing language list: PL-1 and PL-2 in
flight in `source_material/ToDo/squares_in_squares` — the graded objective and
the collective stir — with PL-3 to PL-9 listed below and their resume
commands).*

*Last altered 18 November 2026 (the squares branch, runs 71–74: the branch space
at frozen angles closed negatively — the relaxation is empty, 87,767 structures
solved, 0 improvements — the dimension theorem scoped to the axis-parallel
class, `declp3.py --milp` retired. The way-forward list is at the foot of this
file, with its resume commands).*

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

---

## Follow-ups (brainstorm, 17 Nov 2026)

Most valuable next items, ranked by leverage, for the optional-static-Lean /
GLM-systems focus:

1. **Serve the router's two Lean lookups (`feature_table`, `declaration_names`)
   from the stored book** — *taken this round.* `lean_address.feature_table()`
   and `lean_address.declaration_names()` now read from `lean_book` (features +
   declaration rows) instead of walking the development; both fall back to the
   tree when no book is present. Recomputed values match byte-for-byte.
2. **Fix the lean-tree split's dependency tracking.** — *taken this round.*
   Builders (`corpus/measurements`, `citation_reference`, `retrieval`,
   `native_parity`, `native_words`, `corpus_resample`, `stack`, `tie_break`,
   `citation_scope`, `operation_escalation`, `corpus/render`) now import
   `lean_tree` directly, so the sign-off ledger flags their tree dependency;
   answering paths keep the `lean_address` importlib shim. lean_blast_radius:
   264 units, 228 taking the whole development (up from 224 — builders now
   correctly attributed).
3. **Extend disk caching to the other expensive memoized derivations** —
   *taken this round (partial).* `citation_graph` and `separation_report` are
   now `DerivedStore`-backed (`lean_citation_graph`, `lean_separation_report`),
   with sorted-list / `_freeze`+`_thaw` round-trips; verified equal to the
   recomputed versions. `feature_table` is book-served. `legacy_citation_graph`
   (now `lean_legacy_citation_graph`) and `tiebreak_report` (now
   `stack_tiebreak_report`) are now `DerivedStore`-backed too, both fresh on
   the current tree; closes the caching follow-up.
4. **Investigate the pre-existing `lean_address` duplicate-name failures** —
   *investigated this round.* Root cause is not the parser: 128 duplicate
   full names arise because multiple Lean files share a namespace (e.g.
   `Cube/Stabiliser.lean` and `CubeStabiliser.lean` both `namespace GLM.CubeStab`),
   so `declarations()` yields 9604 entries for 9476 unique names. Consolidating
   these held copies would change the tree digest and require a rebuild (owner's
   Lean toolchain), so left untouched; recorded rather than hidden.
5. **Refresh the iteration-cost study's blast-radius table** — *blocked.*
   The table rows can be updated to the current 264-unit tree, but
   `test_the_ledger_is_selective` still fails: median_single_file (231) is far
   above `units_naming_lean // 2 + RECORDED_MEDIAN_EXCESS` (149). The excess
   is structural (signoff/rules.py's glob is in every unit's closure), not a
   stale-baseline issue; bumping the recorded excess would hide it. Needs a
   deeper cut than doc refresh.
6. **Tighten the relay cache key** — *deferred.* The current key (lean files
   plus every source document) is the tightest file-based key DerivedStore
   supports; keying on digest strings would need a synthetic input file or a
   non-file store. Left as-is (correct, if chatty).
7. **Chat-surface *carriers* reading change** — blocked on a fresh held-out set.
8. **Lean-optional verification** — *verified this round.* Grep of
   `src/glm_universal` finds no `lake` invocation in Python; only docstring
   mentions. `lean_check` is a static text check and intake's Lean-verified
   stage requires the owner's build record. Stance holds.

1. **P2, the Lean toolchain and the owner's build record.** Install elan +
  Lean 4.28 + Mathlib here (about 6–8 GB and hours on two cores) and run
  `scripts/rebuild_lean.sh`, or take the owner-machine build record as the
  fallback. Every item absorbed ahead of it then clears with
  `python3 -m glm_universal.intake confirm-build <id>`; the 13 files of
  [`studies/_lean_files_needed.md`](studies/_lean_files_needed.md) stay owed;
  three of them (`LeechShells`, `LorentzPlane`, `AdversarialDialogue`) now have
  proposed rebuilds in `source_material/ToDo/lean_recovery/`, so the build has
  something to compile before the rest is written, and since Phase 191 an item
  whose Lean is written and statically checked is not stopped by the missing
  toolchain: `intake defer-lean` carries it past *Lean verified* as
  `lean_owed` for `measured` and `absorbed`, and `confirm-build` ends the flag
  when `scripts/rebuild_lean.sh` passes.
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

## Packing language — the open list (17 November 2026)

Squares in Squares run 39 (`source_material/ToDo/squares_in_squares/06-CRAM-RELAX.md`)
measured four mechanisms from arXiv:2611.17309v1 and left one transfer (the
learned relation cost ranks seeds: AUC 1.000 / 0.794, Spearman 0.37–0.74) and
two refusals (the calibrated threshold is degenerate at tau = 0; focused
relaxation loses at n = 240 *with* 6× the per-body moves). The reading, and
the reason for this list: **the packing energy is a gate, not a landscape** —
E = 0 *is* feasibility, so every feasible packing is a global minimum and E
cannot prefer the deeper arrangement. What separates a grid from a record is
which *relations* it uses, and that is graded.

`[new]` = raised this round. Nothing here is a GLM claim, and no row of the
table is touched by any of them.

| # | item | status | resume |
|---|---|---|---|
| **PL-1** | **Graded objective.** Descend `F = E + lam * cbar` (mean learned relation cost of the near pairs) instead of E. `graded` applies lam throughout; `tail` only in the improving-only tail — feasibility first, then the language. lam = 0 is a control that must reproduce run 39's `full` column to 1e-12. | **closed — negative** (§2–3 of `07-LANGUAGE-OBJECTIVE.md`) | `--check` passes: lam = 0 reproduces run 39's `full` to 1e-12. The result is the *slope* finding below |
| **PL-2** | **The stir.** A collective move: a body plus its k nearest neighbours moved rigidly (rotation about the patch centroid with p = 0.3). The move a focused Gibbs step cannot make, and the one run 39's n = 240 negative names. k = 4, equal move budget — the arm gets 4× the body displacements, so a loss is strong and a win is provisional. | **measured at matched budget — a narrow positive** | the mid-corruption wins **survive at moves/4**: n = 110, amp 0.04 → 0.64×; n = 240, amp 0.01 → 0.31× (identical at both budgets, i.e. converged). Still loses at heavy corruption (1.18×, 1.22×) |
| **PL-3** | **The seam symbol.** The alphabet lacks its one non-lattice word: at n = 344 the record's 16.7 units² of free area is a thin seam across 51 orientations, not a +1-voided grid (first insertion overlaps +0.257). Add a seam relation; aim at 356/395/355 (0.0111 / 0.0107 / 0.0104 each). | listed | build on `seam_census.py` |
| **PL-4** | **The patch fixed point as the lock.** The one-body stop rule never fired (0 of 96 runs, 4 sweeps). "No k-body re-lay lowers F" is the analogue with content, and it is what makes "locked in place" a certificate rather than a hope. | listed | `--patch` plus the sweep |
| **PL-5** | **The score question on the graded objective.** Run 39's push table was E-descent only: 0 of 24 runs below the record. Repeat it descending the language cost, against the **295 open rows** rather than the 16 recovery cells. | listed | a `--push` arm |
| **PL-6** | **Fit the table on the frontier, weighted by depth.** The dialect correction: on the record class φ anti-correlates with depth (−0.61) and the deepest class sits near the vacuum (φ 0.015), so fitting on all 1000 rows learns the shallow dialect. Refit on the 553 sub-grid rows, depth-weighted. | listed | `fit_relation_costs` variant |
| **PL-7** | **Second-order relations.** A pairwise cost cannot see a seam: a seam is a *configuration* of three or four relations. Add triple/patch features and re-measure A's AUC and Spearman on the same two controls. | listed | feature block in `cram_language.py` |
| **PL-8** | **GLM intake.** The transferable object is the learned pairwise potential over an **exact finite alphabet** (18 cells; rational t-basis angles), not the descent and not the threshold. It enters only by the intake (study → test → Lean → measured) and needs the owner's build; two gates fail pre-existing (`corpus --check` → `KeyError: 'GLM.AdversarialDialogue.HeadSet'`; six drifted manifests). | blocked | owner's Lean build |
| **PL-9** | **Coarse-to-fine as the default.** Run 39's D was never much worse and sometimes 1.6× better (n = 240, amp 0.01). Free: settle positions before tilts in every schedule. | listed | one-line schedule change |
| **PL-10** | **A C¹ relation potential.** The fitted table was a *step function* whose jumps (~1e-2) do not shrink with displacement, so it had no derivative and no weight at which it acted as a gradient. Kernel density over the 21,602 contacts (360×240 grid, σ = half a bin), `U = −log p`, bilinear. | **closed — positive, with a condition** | **10 of 16 cells improve after the polish**, best 5.9×; language cost falls with the energy (no trade). Cells: n = 20 amp 0.04 → **0.18×**, amp 0.08 → **0.23×**; n = 60 amp 0.04 → **0.50×**; n = 240 amp 0.01 → **0.31×**. Gentle corruption is inert (1.00–1.03×) — the records sit at the density maximum, gradient ~0 — and a wrong λ there costs up to 17.8×. **The condition is PL-11** |
| **PL-11** | **Schedule λ by corruption.** `lam = (excess/e0)^2`, excess = `cbar_smooth(seed) − cbar_smooth(record)`; one parameter `e0`, fitted on a **disjoint** grid (n = 30/80/150/300 × amp 0.02/0.06), never on the 16 test cells. | **closed — honest, and 3× smaller than the biased number** | e0 = 0.3162 (train mean \|log ratio\| 0.075). **16 cells, one λ each: geometric mean 0.898, median 0.977, 5 cells ≥5% better, 1 worse, best 0.417** (n = 20 amp 0.08). Best-of-seven read as 0.674 → the selection was worth **0.75× of the honest figure** (§10). Cause of the undershoot: flat training plateaus, mean-log-ratio fit lands mid-plateau, λ = 0.001–4.3 against optima of 100–1000 ⇒ **PL-13** |
| **PL-13** | **Min-max refit of the rule.** Same form, same disjoint grid, fit `e0` by **min-max regret** (regret = log distance from each cell's own best λ — the §10 criterion was degenerate, it rewarded λ→0), training grid extended to λ = 10⁴/10⁵, then re-test the 16 and the below-record targets once. | **closed — negative, and it locates the real defect** | Fit saturates legitimately: `e0` = 1e-4 → λ = 10⁴ on all 8 training cells (training minima at λ ≥ 10⁴ for most). 16 cells: **geo 1.143** (14% worse), median 0.981, 8 better / 7 worse, best 0.255, worst **10.60**. Regime split: amp 0.005 → 3.57× worse, 0.01 → 1.47× worse, **0.04 → 0.49×**, **0.08 → 0.67×**. Cause: the training grid (excess 0.045–0.35) contains **no gentle cell**, so nothing paid for the regime where a strong language term hurts — **PL-14** |
| **PL-14** | **Train on solved examples *and* cover the deployment range.** The min-max failure is grid coverage, not the criterion: a maximally engaged language term is the best objective this project has at amp ≥ 0.04 (2.0×, 1.5×) and destroys gentle seeds. Rebuild the grid as the proven-optimal rows × amps {0.002, 0.005, 0.01, 0.02, 0.06} — solved examples (the CRAM reading of a training set) *and* the gentle regime — lift the 1e4 clamp, then fit min-max regret and test the 16 once. | **closed — the first honest rule that beats control** | Grid: 8 proven rows (n = 13, 32, 45, 60, 76, 96, 120, 143, all in `proven_floors`) × 5 amps × 8 λ (0 … 1e8), 1 seed, clamp lifted to 1e12. Fit is **interior**: e0 = 0.008577, and λ follows the measured ladder 0.10 / 1.2 / 6.5 / 48 / 1600 across amps 0.002→0.06. **16 cells: geo 0.975** (2.5% better than switching the term off), median 0.954, 8 better / 2 worse, best 0.246. By amp: 0.005 → **1.016** (the 3.58× gentle damage is gone), 0.01 → 2.677, **0.04 → 0.507**, **0.08 → 0.656**. Push: **0/8 gated, 0/8 below the record** again (geo 1.069) | `python3 scripts/cram_language.py --fit-proven --rule-proven --push-proven --write` (~22 min) |
| **PL-15** | **The amp-0.01 band.** Both §12 failures sat at amp 0.01 (6.23×, 9.06×) at λ = 2–8 while the training cells there measured 0.89–1.31×. | **closed — both halves answered, and they differ** | Six seeds per cell at amp 0.01. **(a) The damage was λ, not the band:** the full-set λ there is 0.1–0.5 and the same cells return **1.02× and 1.02×**. **(b) The residual wobble is bistability:** n=240 gives 0.30 0.34 1.00 1.00 0.26 1.06 — modes ~3.4× apart, not a spread; 2 seeds said 0.316, 6 seeds say 0.551 | `--probe-amp01 --write` (~5 min) |
| **PL-17** | **The training grid should be all 156 proved rows.** Same amp ladder, same λ ladder, same lifted clamp, same min-max criterion, one seed — only the rows change from 8 to 156. | **closed — the best result in the project, and no bad cells** | 780 cells (10.6 h serial, 27.5 min on 8 workers, checkpointed). Fit: **e0 = 0.036869**, λ by amp **0.009 / 0.068 / 0.367 / 2.42 / 77.1**, mean regret 0.0882, max regret 1.463. **16 cells: geo 0.782**, median 0.946, 8 better, **0 worse**, best 0.32, **worst 1.028**; by amp 1.011 / 0.885 / 0.592 / 0.705. Push: **0/8 gated, 0/8 below** (geo 1.049). Mechanism: the cells' own λ* is **flat in n** (amp 0.06 → 1000/1000/1000), so the gentler rule is min-max buying uniformity across 156 heterogeneous rows, not an n-effect | `bash scripts/_run_proven_all.sh` then `--rule-proven-all --push-proven-all --probe-amp01 --write` |
| **PL-18** | **Hand the push wall to the ⅀Δ classifier.** Four weightings all give 0/8 at d = 1%/2%. Is that jam rigid (crystalline contact order → abandon the target) or liquid (one-parameter family → retry rotation-rich)? | **closed — the wall is LIQUID, and "mechanical" was wrong** | `--dump-jam-states` then `delta_sigma_push.py --from-states`: **4/16 RIGID_WALL, 12/16 ONE_PARAM_JAM**, 2 degenerate. **Every state at n ≥ 110 is liquid** (ρ = −0.04 … +0.32, contacts 89–98% of n). Rigid only at n = 60 seed 0 (**60/60 contacts, ρ = 1.000**) and at n = 20 where ρ is undefined. Verdict flips with seed at fixed n — §13's bistability, in contact order. Fixed a silent bug: `rho=nan` used to fall through to "liquid" unlabelled; now it falls back to contact fraction and flags `degenerate` | `python3 scripts/cram_language.py --dump-jam-states --write` then `python3 scripts/delta_sigma_push.py --from-states workspace/push/jam_states.json` (~2 min) |
| **PL-19** | **Rotate-rich retry at the liquid jam.** 12/16 states are one-parameter jams; the classifier's prescription is `rotate_frac = 0.5`. Is the missing freedom angular? | **closed — negative, and it refutes the classifier's prescription** | `relax_graded` gained `rotate_frac`/`rot_amp` (defaults bit-exact); treatment = 0.5 frac, ±0.05 rad (**33× the polish step**). Four arms, 8 cells: **0/8 gated in every arm**, and **rot_rule geo 1.459 (46% worse)**, rot_only 1.011 (neutral). Rotation makes states **more crystalline**: rigid 4/16 → **7/16**, all-in-contact 2/16 → **7/16** (n=20: 20/20 at both seeds). The wall survives its fifth distinct attack | `--push-rotation --write` (154 s), then `delta_sigma_push.py --from-states workspace/push/jam_states_rot.json` |
| **PL-20** | **Measure the wall instead of attacking it.** Five attempts (four weightings, then angular freedom) all give 0/8. Replace "does it break" with "how far is it": bisect `d` between 0 and 1% for the smallest depth that ever gates, and run the **collective** patch move (`relax_patch`, k = 4 bodies) at the same targets — a different freedom from single-body rotation | **[new] next** | `--push-rotation` with a `--depths` ladder (0.0005 … 0.01) and a `rot → patch` arm |
| **PL-21** | **Open the empty residue columns.** 23 of 60 residues have no base at all (r = 38…60), and they hold most of the 7.195 score sitting at grid. Target the **first row** of each column, n = k₀²+r with the smallest k₀ ≥ ⌈r/2⌉, and search for *any* packing with slack δ < 1 — one base opens the whole column. | **[new] next** | `cascade_predict.py` gives the ranked column weights; residue 38 banks **0.257** at δ=0.5, **0.103** at δ=0.8 (the run-35 import gained 0.0036) |
| **PL-22** | **Shrink base slack where a base exists.** For the 37 covered residues each 0.01 of δ buys 0.01·W(r); r=1 is worth 0.005 per 0.01. | **[new]** | sensitivity table in `09-CASCADE.md` §5 |
| **PL-23** | **One source of truth for the table.** `table.json` is **stale**: 22.645991 with 543 beats against the CSV's 22.218056945 with 553; **357 rows disagree**. Any script that reads it under-reports by 0.43 and any that writes it back regresses the submission. | **[new] next — integrity** | regenerate from `submission.csv`, or make the CSV canonical and read-only |
| **PL-24** | **Verify the >1000 rows that have no state.** `extended_table_5000.json` holds 4,000 rows (n = 1001…5000), **805 non-grid**, but only **33 with a stored state** — the other **772** are arithmetic, not gated packings. | **[new]** | gate a sample with `packlib`, then either store states or mark the rows unverified |
| **PL-16** | **Widen the window past 1000 (owner's call).** Keep the submission at n ≤ 1000, but stop treating the 1,000-row window as the landscape. Build the easy rows above it exactly and count what is there. | **closed — 53% of the window is trivially constructible** | `scripts/beyond1000.py`: **4,794 rows, 4,794 distinct n, n ∈ [1020, 9900]**, 0 invalid, **53.27%** of the 9,000-row window; 340 of them **provably optimal** (depth 0.0000–0.0005); `k^2+j` upper bounds (4,454 rows, median depth 0.0103). Gate sample 24 rows, all_match, drift 0. Documented in `08-BEYOND-1000.md` | `python3 scripts/beyond1000.py --census --gate --write` (~40 s) |

| **PL-25** | **Leech addresses: 24 pockets as a language.** 24 = 6 angle sectors × 4 radial shells, thresholded to a 24-bit word and snapped to the nearest extended Golay codeword (4096 words, min weight 8, verified) — the repo's own construction (`LeechResidue.lean`), the same pattern as the 39,992-token `leechbridge` codebook. | **closed — refuted for global histograms** | 1000 rows → **50 distinct addresses**, entropy **2.811 of 12 bits**; snap distance median 4; MI(address; beats grid) **0.1930** vs permutation null **0.0431** (real but ~0.15 bits); MI(address; residue r) **0.9198**, MI(address; band k) **0.5626** — mostly encoding `n`, not the packing. **82% of squares in sector 0**, one pocket holds 46%, emptiest 0.07%. Stability: every distinct address is **≥8 bits away** (the code's min distance), so a 2e-3 and a 4.6e-1 energy perturbation are equally far — no metric left | `python3 scripts/leech_address.py --json` (~20 s) |
| **PL-26** | **Leech as a quantiser, per square.** Λ₂₄ is the best 24-dim quantiser (G = 0.0658 vs cubic 0.0833, 21% less error; covering 4× better). Keep real-valued counts per square in the 24 pockets, take the nearest lattice point, and use the **residual vector** as the language — graded, bounded by the covering radius, unlike the snapped codeword. Falsifier: residual norm must correlate with ΔE, and residual direction must repeat across the PL-15 bistable seeds | **[new] next** | extend `leech_address.py` with `nearest_leech()` and report Spearman(residual norm, ΔE) |
| **PL-12** | **The contact word is never recovered.** Jaccard with the record's contact set is **0.018–0.054** in every probe, at every energy (6 of 285 contacts; 36 of 669). Positions do approach the record at large n (1.8×, 2.5× closer) and the bbox moves toward `L`, so the language is a shape prior, not a decoder. Raises the real question: is the target `L` = the record at all, or should the push be aimed *below* it — the score question — since no descent visits the record's arrangement. | **null confirmed with the term engaged** | **run twice.** Mean-\|log\| rule (λ = 0.008–0.04, term effectively off): 0 of 8 gated. Min-max rule (**λ = 10⁴ everywhere, term fully engaged**): **0 of 8 gated, 0 of 8 below the record** — ratios 1.08/1.12, 0.82/0.89, 1.34/1.22, 0.76/0.93 at d = 1%/2%. The wall is mechanical, not a weighting choice *(superseded by PL-18: the jam classifies **liquid** in 12/16 states — the missing freedom is rotational, not a theorem)* |

| **PL-27** | **Snapping as measurement, not action.** Statistic of the snap rather than the codeword: hard distance, Euclidean distance to the code, centred ρ₁, decisiveness gap ρ₁−ρ₂. | **positive, controlled** | Hard distance is **graded** `{1:5, 2:27, 3:296, 4:672}` (variance 0.316) — part 7's "median 4, max 4" hid this. Grid: MI(hard d) 0.0831, MI(euclid) 0.1722, MI(ρ₁) 0.1239, **MI(gap) 0.2955** vs null 0.0019–0.0046. Controls: I(band;beats) 0.0163, I(residue;beats) 0.4438, **I(gap;beats\|band) 0.3619** (rises), **I(gap;beats\|residue) 0.1356**; within-residue permutation 300 reps → null 0.0549±0.0082, **z = +9.87**, excess **≈0.081 bits**. First 24-pocket statistic to survive controls. Negative: does **not** track energy (Spearman −0.061/−0.132/+0.108, pooled −0.124) | `python3 scripts/leech_measure.py --json`; `python3 scripts/leech_snap_controls.py` |
| **PL-28** | **Sign and use of the decisiveness gap.** Direction unmeasured: are beating rows more decisively legal or less? Then use it as a prior to rank rows *inside* a base-less residue column, to feed PL-21's base search | **[new]** | report MI + mean gap by beat class; test the ranking on one column |


| **PL-29** | **Rotation control on the snap prior — closes PL-27/28.** Any address statistic must beat the trivial rotation flag, since beating grid requires rotated squares. | **closed — negative, prior retracted** | Beating rows are more decisive (AUC 0.7540, null 0.4999±0.0189, z=+13.48; per-column median AUC 0.716) **but** grid rows have gap median 0.0000 and 63.4% exactly 0 — gap 0 means the pocket vector sits *on* a codeword, which is what an axis-aligned grid does. **AUC(rotation→beats) 0.8193 ≥ AUC(gap) 0.7540; AUC(gap) among rotated rows only 0.3495** (below chance). MI(rot;beats) 0.3312, MI(gap;beats) 0.2276, **MI(gap;beats\|rot) 0.0304** — 87% is rotation. Spearman(gap,δ) among rotated beating rows +0.166 (wrong direction). Part 8’s "survives controls" retracted | `python3 scripts/leech_prior.py --json`; `python3 scripts/leech_rotation_control.py` |
| **PL-30** | **Correct the base population: 39 columns, not 23.** Measured from the delivered table, not the cascade model | **corrected** | **21 residues contain a beating row; 39 do not** (r = 0, 22, 24–60). `09-CASCADE.md` §5’s "37 of 60 with a base" came from the planner’s model; the delivered packings give 21. PL-21’s target population and its ceiling are therefore larger than the lever table showed | `python3 scripts/leech_prior.py --json` (field `base_less`) |
**Measured this round** (ledger `workspace/push/cram_language.json`, record

| **PL-33** | **Instrument audit: two errors, every Leech number re-measured.** (a) parts 7-10 scored `10/L` where the repository scores `sum(L/sqrt(n)-1)`; (b) every Leech instrument inflated the bbox (`max(ex)` on both sides), reclassifying 253 of 553 beating rows as grid. `leech_audit_fix.py` reproduces the delivered table to 1.3e-10 and 553 beats, cross-checked against `packlib.verify` | **corrected; two claims withdrawn** | Corrected: AUC(rotation→beats) **1.0000**, AUC(gap→beats) 0.9861, MI(rot;beats) 0.9919, **MI(gap;beats\|rot) 0.0000** — rotation predicts beating grid **perfectly** and the snap statistic adds exactly nothing. **Part 8's "0.081 bits genuine" withdrawn** (artefact of the mislabelled target). **PL-30 withdrawn**: corrected target gives 37 residues with a beating row and 24 without — the record's original 37/24 was right. Area ceiling rebuilt: base-less 0.8068 (0.0046/row) vs open columns 6.3886 (0.0237/row); **slack is worth 52.38 per unit — 0.01 = 0.5238** | `python3 scripts/leech_audit_fix.py --json` |


| **PL-34** | **The scorer guard.** One shared scorer `scripts/sqscore.py` with an assertion that submission.csv gives exactly 22.218056945 and 553 beats (447 grid); all leech/area/cascade instruments import it, none keeps a private box or score scale | **done** | 8 instruments wired: leech_address, leech_measure, leech_prior, leech_snap_controls, leech_rotation_control, area_ceiling, cascade_predict, leech_audit_fix. Grep for `ex = 0.5`, `max(ex)`, `10 / dsqrt`, `10.0 / L`, `ceil(sqrt(n)) - 1e-12` returns nothing. Re-run once each, all agree: MI 0.5856, AUC 0.9861, AUC(rot) 1.0000, MI(gap\|rot) 0.0000, z=+47.50, area_ceiling 22.218056945 (it had still been printing 27.979 — the exact bug class the guard catches) | `python3 scripts/sqscore.py` |
| **PL-32** | **Tighten the r=1 base below slack 0.520815** | **attempted — no base found** | relax+coordinate_polish returns the delivered state **unchanged** (k=8: 8.535534 in, 8.535534 out, target 8.5155): the packings are fixed points. sa_push.anneal fails the gate on every seed. `cram_relax.project` dropped (docstring: *measured to hurt*); `soft_relax.hop_search` unimportable — `cent_discovery` is missing from this tree. Carrier validated instead: bands from n=5 (29), n=65 (23), n=626 (6), **0 gate failures**, **measured score change 0.000000000** — the table beats its own chains. Needs a construction, or `cent_discovery` restored | `python3 scripts/pl32_base.py`; `12-GUARD-AND-PL32.md` |
| **PL-31** | **Area ceiling: where the remaining score can be.** Gain at a row is bounded by `10/sqrt(n) - 10/(k+1)` (zero-waste limit); column slack is set by the base and inherited by every row | **plan revised** | Total headroom under 24.7311. The 39 base-less columns hold **1.7598 over 429 rows (0.0041/row)**, the 21 open columns hold **14.0163 over 271 rows (0.0517/row)** — **13x per row better**. **PL-21 deprioritised.** Marginal value of slack over the 21 columns: **41.6828 per unit, 0.4168 per 0.01**; r=1 alone 6.3277 (30/31 rows beating). Ceiling concentrated in small r: r=1 5.8677, r=2 3.8517, r=3 2.4747. Gaining 1.0 needs slack down ~0.02 uniformly — construction, not search | `python3 scripts/area_ceiling.py --json` |

| **PL-35** | **Restore the soft-relaxation engine.** `cent_discovery`, `engine_variants` and `oracle_basin` are imported by 8 scripts and are in neither the tree nor the git history | **reconstructed; hop_search unvalidated** | `git log --all` on the name returns nothing; only references exist (commits db74f9e/41489c7). Rebuilt to contract: cent_discovery.rsa_seed/attempt, oracle_basin.settle_to/ramp_settle, engine_variants.finalize_gate/lattice_seed/transduce. Imports: soft_relax/boundary_demo/boundary_scan/p1p_insert31/p2_seed_polish OK; fine_probe still needs `lm_exactify`, root_probe+lattice_scan still need `pressure_settle` (both absent). settle_to VALIDATED (delivered n=5 -> E=0, L=2.707107); rsa_seed clean at n=5/11, ~5e-2 overlap at n=65/626; **hop_search NOT validated** (n=5 control 0/8 hard hops; cold-settle plateaus at E=2.8e-2). PL-32 sweep: k=8 (78s), k=9 (97s) -> 0 gated finds; k=10..25 skipped on budget, so the question is open, not answered | `python3 scripts/cent_discovery.py`; `13-CENT-RESTORATION.md` |
| **PL-32** | **Tighten the r = 1 base.** δ = 0.5208 is inherited by all 31 rows of the largest column; search for a base packing with smaller slack, then let the cascade carry it | **[new] next** | report new δ and the measured score delta; reject any claim above the area ceiling for that column |

| **PL-36** | **Vectorise the O(n^2) penalty; fix the cold settle.** `sa_push.total_pen` looped n Python calls; the settle used L-BFGS-B on it | **vectorised (verified exact); settle improved; control STILL FAILS** | `pair_pen_matrix` delegates to `cram_relax.margin_matrix`; total_pen is one matmul, **identical to the loop** (48.360341919152 both), **0.15 ms** at n=40, and hop_search at n=5 goes 67s -> 17s with hard hops 0/8 -> 1/4. Two own defects caught: a hand-rolled matrix that disagreed (48.36 vs 27.90) and a triu rewrite that halved the penalty (the loop summed ordered pairs). settle_to now uses cram_relax.relax + coordinate_polish. **Control: best 3.080452 vs known 2.7071068**; shrink-and-repair 2.870-2.906. Cause: the optimum is the 4-around-1 rotated-45 pattern; single-body moves and fixed-side SA cannot restructure a random seed into it. **k=8..25 sweep deliberately NOT run** — unvalidated engine numbers are meaningless | `python3 scripts/cent_discovery.py` |
`07-LANGUAGE-OBJECTIVE.md`, notes `notes/run40_NOTES.md`). Recovery test first:
lam = 0 reproduces run 39's `full` medians exactly (2.333e-03 at n = 20,
amp 0.01; 9.208e-02 at n = 110, amp 0.04), so every difference below is a
difference of objective.

* **The learned cost has no derivative.** Perturbing one body by up to `eps`
moves `cbar` by a median 9.5e-02 at n = 60 and 1.8e-02 at n = 240 — **the same
at eps = 1e-3 as at eps = 1e-1**. It is a step function with jumps of order
1e-2, not a smooth potential. Consequence, measured directly: at n = 110,
amp 0.04, `lam` = 0.1, 1.0, 1e3 and 1e6 return **identical** states — the term
is lexicographic from 0.1 onward, and there is no weight between "off" and
"decides everything". The hinge energy beside it moves by ~1e-5 per move at a
polish endpoint: three decades apart.
* **PL-1: negative.** `graded` wins on polished E in 6/16 cells by 5–6% and
loses by 3.7× to **125×** (n = 20, amp 0.005: 6.28e-05 → 7.88e-03); `cbar`
falls by at most 5% anywhere. `tail` is neutral at n = 110/240 (0.97–1.00×)
and 13–154× worse at n = 20/60. One real cell (n = 240, amp 0.01: 3.12e-03
against 4.42e-03 at 3% lower `cbar`) — not a mechanism.
* **PL-2: a narrow positive.** At equal *move* budget (4× the displacements,
handicapped in its favour) the patch arm beats `full` in 2/16 cells —
n = 110, amp 0.04 (0.64×) and n = 240, amp 0.01 (0.31×) — within ±25% in 13,
worse in 1. Both wins are mid-corruption large-n, the same corner where run
39's D won. First proposal-grammar change here to beat one-body descent
anywhere; it does not beat it generally.
* **No packing found.** 0 runs at E ≤ 1e-6 in every arm; the score and
`submission.csv` are untouched. Two seeds, medians, no error bars — only the
>25% differences are called out.
* **PL-10 built and it works, conditionally.** Kernel-density potential
(360×240, σ = half a bin, `U = −log p`, bilinear), fit in 0.4 s. **10 of 16
cells improve after the polish**, best **5.9×**, and the language cost falls
with the energy instead of being traded against it: n = 20 amp 0.04 → 0.18×,
amp 0.08 → 0.23×; n = 60 amp 0.04 → 0.50×; n = 240 amp 0.01 → 0.31×. Gentle
corruption is inert (records sit at the density maximum, gradient ~0) and a
wrong λ there costs up to 17.8× — so the weight must be **scheduled by
corruption**, which is PL-11.
* **PL-2's caveat closed.** At `moves/4` (matched displacement) the mid-
corruption wins are unchanged — n = 110, amp 0.04 → 0.64×; n = 240, amp 0.01 →
0.31×, identical at both budgets. Not bought with budget. Heavy corruption
still loses (1.18×, 1.22×).
* **PL-11: the rule, honestly.** `lam = (excess/e0)^2`, `e0` fitted on a
**disjoint** grid. One λ per cell, 16 cells: geometric mean **0.898**, median
0.977, 5 cells ≥5% better, 1 worse, best **0.417**. Against §7's best-of-seven
0.674, the selection bias was worth **0.75× of the honest figure** — the 33%
of §7 is a 10% in fact. The rule picks λ = 0.001–4.3 where the cells wanted
100–1000: flat training plateaus, mean-log-ratio fit lands mid-plateau (PL-13).
* **PL-14: the first honest rule that beats switching the term off.** Grid =
8 proven-optimal rows × amps {0.002, 0.005, 0.01, 0.02, 0.06} × λ ∈ {0, 1,
10, 100, 1e3, 1e4, 1e6, 1e8}, clamp lifted. The fit is **interior** for the
first time: e0 = 0.008577, λ = 0.10 / 1.2 / 6.5 / 48 / 1600 across the five
amps — it reproduces the measured ladder rather than pinning to a bound.
**16 cells: geo 0.975** (median 0.954, 8 better / 2 worse, best 0.246).
By amp: **0.005 → 1.016** (the clamped rule's 3.58× gentle damage is gone),
0.01 → 2.677, **0.04 → 0.507**, **0.08 → 0.656**. The heavy-corruption gains
survived the honest fit; only the gentle wreckage was priced out.
* **What the interior fit fixed, and what it did not.** Remaining μ-damage is
confined to **amp 0.01**: n=20 (λ=8.03) 6.23×, n=110 (λ=2.06) 9.06×, while
n=60 0.92× and n=240 0.98× at the same amp are fine. The training cells at
amp 0.01 all measured 0.89–1.31× at λ=10, so the grid did not see it either:
same λ, per-n flips between 0.9× and 9×, on sub-milli energies (1.3e-4 →
8.3e-4). That is bimodality, not a weighting error — PL-15.
* **The push is unchanged by any weighting.** With the interior rule engaged
(λ = 11–55 at excess ≈ 0.03): **0 of 8 gated `L`, 0 of 8 below the record**,
geo 1.069, best 0.906. Three different rules — off, saturated, interior —
and the same wall. The wall is mechanical (PL-12).
* **PL-17: all 156 proved rows is the first rule with no bad cells.** Same
grid, same criterion, only the rows change. Fit **e0 = 0.036869** with λ =
0.009 / 0.068 / 0.367 / 2.42 / 77.1 across the amps. **16 cells: geo 0.782**
(22% better than switching the term off), 8 better, **0 worse**, worst cell
**1.028** — inside the noise floor. §11's 3.58× gentle failure and §12's two
6–9× failures are all gone, at the cost of a little heavy-corruption gain
(0.507 → 0.592, 0.656 → 0.705).
* **Why the full set is gentler — and it is not n.** The cells' own optimum λ
is flat across n bands (amp 0.06: **1000 / 1000 / 1000**). The full set is
gentler because 156 heterogeneous rows make min-max buy uniformity instead of
sitting on anyone's optimum: **max regret got worse (0.554 → 1.463) while mean
regret got better (0.106 → 0.088)**. The rule that generalises best is the one
that deliberately sits between cells.
* **PL-15 settled, in two halves.** The 6.23× / 9.06× failures were **λ, not the
band**: they ran at λ = 2–8 from the eight-row fit, and at the full-set λ
(0.1–0.5) the same cells return **1.02× / 1.02×** over six seeds. What remains
is **bistability**: n=240 gives 0.30 0.34 1.00 1.00 0.26 1.06 — modes 3.4×
apart, 2 seeds said 0.316 and 6 seeds say 0.551. A single chain cannot report
the value of λ.
* **The push is unchanged at the fourth weighting.** λ = 0.6–3.0, engaged:
still **0 of 8 gated, 0 of 8 below the record** (geo 1.049, best 0.929).
Off, saturated, interior-8, interior-156 — one answer. That is a jam, and
PL-18 has now classified it.
* **PL-18: the jam is liquid in 12 of 16 states, so "mechanical" was wrong.**
`--dump-jam-states` + `delta_sigma_push.py --from-states` (the script's own
contact-bitstream ρ classifier): **4/16 RIGID_WALL, 12/16 ONE_PARAM_JAM**.
**Every state at n ≥ 110 is liquid** (ρ = −0.04 … +0.32; contacts 89–98% of
n). Rigid only at n = 60 seed 0 — **60/60 squares in contact, ρ = 1.000** —
and at n = 20, where 19/20 touching leaves ρ undefined. So the 0/8 is a
search-freedom problem, and the specific missing freedom is **rotation**
(PL-19). §11–§13's "the wall is mechanical" is corrected.
* **The classifier had a silent-wrong-answer bug, now fixed.** `rho = nan`
(one lag slice constant) fell through `rho > 0.5` as False and was reported
as a liquid jam **without comment**. `classify` now falls back to the contact
fraction (≥ 0.9 = crystalline), keeps ρ = nan, and writes
`degenerate: true`. Same failure class as the dead `--dither`, one level down.
* **Flag surface audited.** Removed `--dither` (no body) and the superseded
8-row path (`--fit-proven`, `--rule-proven`, `--push-proven`, serial
`train_grid`, `PROVEN_TRAIN_ROWS`). Added **`audit_flags`**: every action flag
is mapped to the section it must produce, and a flag that leaves `res`
untouched exits **2** with the flag named. Verified both ways — stub with only
`check` set returns `['--check']`; a satisfied flag returns `[]`; `--dither`
is now an argparse error.
* **PL-19: the liquid jam does not break, and rotation makes it more
crystalline.** `relax_graded` gained `rotate_frac`/`rot_amp` (defaults
bit-exact — recovery test still matching, rule arm reproduces the stored push
exactly at 1.0486). Treatment: 0.5 fraction, ±0.05 rad, i.e. **33× the polish
angular step**. Four arms, 8 cells, d = 1%/2%: **0/8 gated in every arm**;
**rot_rule geo 1.459 (46% worse)**, rot_only 1.011 (neutral). Contact order
gets *more* crystalline: rigid **4/16 → 7/16**, all-in-contact **2/16 →
7/16** (n=20 gives 20/20 at both seeds and depths). The classifier's
equation "liquid ⇒ retry rotation-rich" is from another campaign and does not
transfer; `ONE_PARAM_JAM` means "not crystalline", not "rotation-limited".
The wall has now survived five distinct attacks: four weightings and angular
freedom.
* **PL-16: the window above 1000 is half constructible, and it is all
lattice.** `beyond1000.py` builds **4,794 rows over 4,794 distinct n**
(n ∈ [1020, 9900]) in closed form — **53.27%** of the 9,000-row window, 0
invalid, 24-row gate sample all_match with zero drift. 340 are **provably
optimal** (k² and k²−1..4, depth 0.0000–0.0005); 4,454 are `k^2+j` upper
bounds at median depth 0.0103. The uncovered 47% is n = k²+j with j > k — the
upper half of every band, where `L = k+1` stops being plausible. The corollary
matters: **every easy row above 1000 is lattice**, so widening by easy rows
widens the vacuum, not the vocabulary. See `08-BEYOND-1000.md`.
* **Historical defect, found and fixed in the same pass.** §10's criterion
(mean |log ratio|) is degenerate — at λ → 0 every ratio → 1.0, so it rewards
switching the term off; measured, mean |log ratio| is 0.282 at the fit and
0.072 at e0 = 10. The 0.898 figure came from a rule fitted to do nothing.
* **PL-12's null is confirmed with the term engaged.** Below-record targets,
d = 1%/2%: with λ = 10⁴ (fully engaged) still **0 of 8 cells reached a gated
`L` and 0 of 8 went below the record**. The wall is mechanical.
* **"Optimal packings up to 10,000" is not available here, and would be the
vacuum anyway.** The table stops at n = 1000. The 156 proven-optimal rows
(n ∈ [1, 961], 193,742 contacts) sit **99.99%** in the two lattice relation
cells — 96.07% for all rows n ≤ 120 — and at an un-corrupted optimal packing
the excess is 0, so the rule's own form gives λ = 0 there. Solved examples are
the right *seeds*; they are not the right *coverage*, which is PL-14.
* **The ceiling is now visible.** Jaccard with the record's contact set is
**0.018–0.054** at every energy — no chain has ever reproduced a record's
contact word. Positions do approach it at large n (1.8×, 2.5× closer) and the
bbox moves toward `L`, so the language behaves as a shape prior, not a
decoder. That is PL-12, and it is the question worth answering next.

## Plan — cent wheels Python-only work (this environment)

**Context.** `cent_compiler_v12` is absorbed ahead of the build (provisional);
`test_cent_bridge` and `test_cent_router` pass; `test_cent_wheels` is 25/36
with 11 failures, all tracing to `parse_monomial_q` in
`wheels/cent_wheels.py` not handling function-call syntax such as
`sign_of(applied_load - critical_load)` in supplied axioms.

**Steps (Python only, no `lake`):**

1. **Extend `parse_monomial_q`** to accept `sign_of(...)` (and comparable
   sign-bearing factors) as a ±1 factor contributing no prime exponents.
   Unblocks all 11 failing marks.
2. Re-run `test_cent_wheels.py`; regenerate `cent_wheels_report(lean=True)`.
3. Re-run the intake's staged tests (`item:cent test`) so the provisional
   pass is current.
4. Wire source labels into `derive_query.py` for cent-wheel answers.
5. Leave Lean build confirmation to the owner
   (`confirm-build cent_compiler_v12` after `rebuild_lean.sh`).

**Step 1 done:** extended parse_monomial_q for sign_of (commit aa80585).
**Step 3 done:** retest cent_compiler_v12 recorded (4 of 5 pass;
  test_cent_wheels still 4 pre-existing failures).
**Step 4 done:** source label wired into derive_text figures.
**Step 2 done:** re-ran test_cent_wheels (32/36) and regenerated
  cent_wheels_report(lean=True) — e1 met, 0 disagreements; d1 has 5 failing_si7
  and 1 unknown (pre-existing data-drift in absorbed transcription, not parser).
  The 4 remaining test failures are data-fidelity checks (transcription vs.
  supplied item / Lean file), not parser issues.

**Current state (17 November 2026):** the drift is fixed and the family is
  **24 wheels** — W16–W29, W32–W34 and W36–W42 absorbed; W35 remains in
  `NOT_ABSORBED`. `CENT_WHEEL_IDS` and `provisional.json` carry the 24; the
  supplied item has 101 axioms (5 failing at SI7) and 33 controls;
  `test_cent_wheels` is **37/37**, `cent_wheels_report(lean=True)` has d1
  axioms=101 / failing=5, s2 controls=33 supplied and 22 absorbed, absorption
  met; the Lean file is regenerated (220 theorems, agreement OK);
  `lean_check` OK and `intake check` 0 errors. `hidden_relations` now reports
  only genuine combinations (two dimensionless laws on a shared quantity),
  not a disjoint conjunction of independent laws. The owner's Lean build is
  still the open item (follow-ups in `studies/_cent_wheels_follow_ups.md`).

## Ranked next steps — cent wheels (17 November 2026)

Value order, newest ideas marked **[new]** and earlier ones **[raised]**. Nothing
below is started except #2, which is in flight.

1. **[raised] Owner Lean build** — the only unverified claim: 220 theorems,
   the `sign_of` path and the nine new wheels have never been type-checked.
2. **[new] Junction-aware cross-wheel licensing** — *in flight.* The engine
   ignores the supplied `junctions`/`non_identities`; naive union already
   licenses 4 measured wrong answers through the `energy` conflation. Build
   the typed quantity graph, then join only along declared edges.
3. **[new] Dimensionless-function layer** (`log`, `exp`, `sign`, `abs`, plus a
   gradient) — recovers W35 (Nernst, Fick), makes W42's `sign_of` honest, and
   reaches past monomials.
4. **[new] Battery for the new domains** — `MEASURE_BATTERY` stops at W35; W26,
   W27 and W36–W42 have no independent questions. Cheapest way to show the new
   absorption buys something.
5. **[new] Coefficient-level correctness mark** — the relation vector already
   carries the coefficient's prime exponents; test the wrong-coefficient
   not-a-laws (e.g. `1/2 C V^2` against `C V^2`).
6. **[new] Automated rule-R correction search** — propose the minimal table or
   exponent edit that balances a failing axiom; humans approve.
7. **[new] Negative-control generation and perturbation fuzzing** — perturb an
   exponent or coefficient per case and assert refusal; finds over-licensing.
8. **[new] Derivation distance / near-miss metric** — use the separating
   functional to quantify how far a refused formula is from the span.
9. **[new] Per-wheel health table** — D1/S2/S5, absorption, cases and Lean
   status, one row per wheel, for triage and regressions.
10. **[new] Evaluate the item's 22 application proposals** against the absorbed
    wheels — which are now sound, which rest on corrected axioms.
11. **[new] Redundant-axiom, duplicate-law and consistency marks** — is an
    axiom in the span of the others; does a wheel imply `2 = 1`.
12. **[new] Table inference** for wheels that ship no `dimensions` (W21 arrived
    without one and was hand-corrected).
13. **[raised] Port the compiler pipeline** (pound → cent → delta, five
    fidelity layers, SPICE output) — the item's purpose beyond the wheels.
14. **[new] General soundness theorem in Lean** — one structural result
    replacing 220 per-case theorems.
15. **[new] Sum / term homogeneity support** — the other half of the
    non-monomial gap after #3.
16. **[new] Second independent engine** for differential testing of span
    membership where the integer engine cannot read.

**#2 in flight (17 November 2026; the item's own tables checked).**
`wheels/quantity_graph.py` now follows the absorbed item's **operative**
junction table, `wheels/index.json`: **59 distinct pairs**. The item carries a
second, stale copy in the per-wheel `W*.json` `junctions` blocks — 43
directional entries, 29 distinct pairs — and that is the copy transcribed
first; it omits all thirty W20–W35 registry edges. `test_the_per_wheel_junction_copy_is_stale`
pins the 29 < 59 relation. The graph audits the table (seven junctions name a
quantity the wheel lacks, `W36 pair_energy -> W4 energy` among them; one
vacuous guard, `W37 relaxation_time`) and contracts the sound edges into
identity classes; four vacuous guards are repaired with the other-wheel name
read out of their reason (`W39 magnetomotive_force` against `W1 current`,
`W41 temperature_difference` against `W8 temperature`, `W42
moment_of_inertia_of_section` against `W4 moment_of_inertia`, `W36
pair_energy` against `W5 energy`). A declared junction is not a licence to
identify: four pairs have unequal SI7 vectors and are refused as declared
analogies (`W1 voltage`/`W20 stress`, `W12 area`/`W34 pipe_radius`, and the
two W36 `pair_penetration`/`stress` edges), leaving **50 sound edges**.

`wheels/cent_union.py` feeds those classes to `domains.split_system` over all
39 wheels. The third junction table **duplicates most of Phase 66's and the
domain table's** entries; the merge keeps each pair once (15 pairs), and the
graph's 50 sound edges pass as explicit pairings, so differently named
quantities join (`magnetic_flux`/`flux`, `heat_rate`/`power`). The rational
engine reads the cent wheels' fractional powers. Completing the table did not
move the measured family numbers below: it widened the licensing without
altering what the five families answer.

**Energy family measured (8 pre-registered questions):** the 39-wheel naive
union is ill-posed on all 8 (merging six `energy` copies makes the exponents
non-unique); the six energy wheels alone derive 7; the licensed union answers
3 and refuses 5, of which **4 are the capacitor `1/2 C V^2` against the
delivered `C V^2` factor-1/2 conflict** (`charge`/`voltage`,
`capacitance`/`voltage`, `power`/`time`, `energy`/`time`). The refusal names
both formulas rather than choosing one.

The two records the table cannot use are now **classified rather than left as
generic unknowns**: the `W36 pair_energy -> W4 energy` junction is dropped
(W4 holds no energy), and the `W37 relaxation_time` guard is vacuous (W4
holds no timescale, and the record gives no other name). A cross-name answer
now renders the name the question asked.

**The other non-identity families measured (17 November 2026).** Same
method: the naive union over the family's own wheels against the licensed
39-wheel union.

| family | questions | family-naive | licensed answered | refused | conflations |
|---|---|---|---|---|---|
| energy | 8 | 7 | 3 | 5 | 4 (the factor-½ capacitor/delivered pair) |
| mass | 2 | 2 | 0 | 2 | 2: `E = 2 m c²`, `m = E/(2c²)` |
| time | 3 | 3 | 1 | 2 | 2: `v = L P / E`, `t = E / P` |
| angle | 2 | 2 | 0 | 2 | 2: `angular_velocity = angular_frequency` (both ways) |
| stress | 2 | 1 | 1 | 1 | 0; the gap and the repair below |

The 39-wheel naive union is ill-posed on **all** of the mass, time and angle
questions (merging the shared name makes the exponents non-unique); the
family-size naive derives them. The licensed union refuses every conflation,
so the non-identity table is doing its job across all four families, not
just energy.

**Stress repair.** The supplied table joins `stress` across W20/W21/W37/W40
only through W36's **dimensionless** `pair_penetration`, a dimension gap, and
that left W40's stress disconnected from W37's, so the W37+W40 dissipation
question could never connect. `dimension_gaps()` reports exactly the two W36
edges (and, with the full table, `W1 voltage`/`W20 stress` and `W12
area`/`W34 pipe_radius`, which are analogies rather than stress); two
same-name `BRIDGES` (W20/W21 and W20/W37) join the four dimensioned copies
directly. Now `dissipated_power` from `force, area,
strain_rate` derives `force * strain_rate / area`, and `pair_energy` from
`stress` is refused at the gap instead of printing a dimensionally false
`stress^2`.

**What the item already has (checked 17 November 2026).** The absorbed
pipeline is not a blank slate; several of its modules overlap this round.

| module | what it is | relation to this round |
|---|---|---|
| `axiom_graph.py` | 40 wheels, 101 axioms, 59 junctions; wheel/axiom/quantity/dimension nodes; union-find identities, non-identity barriers, exact `derive_from` with **direct and bounded substitution** and proof steps | the upstream ancestor of `quantity_graph.py` + `cent_union.py`; ours adds the SI7 dimension filter it lacks and now reads its 59-pair table |
| `leech_class.py` | class word `c mod 2` from a declared row-HNF basis, XOR composition, F2 rank; tested on 80,361 moves (63,257 classes, rank 24) | the existing **Leech addressing**: a class index, not a lattice, metric or Griess product; the quotient verdict stands |
| `typed_graph.py` | route/component graph: primitive nodes, wire bindings, component lowerings | unrelated to the quantity graph (ports and wires, not measurands); no reuse |
| `wheel_mapping.py` | declared typed bridge with an SI residual (W24 log-domain sqrt) | the pattern for an **analogy** edge; the dimension filter is the same test |
| `isomorphism_gate.py` | 3-tier gate and 7 transducer analogies (W1↔W7, W4↔W5, W3↔W14, ...) | method-level analogies, not quantity identities; keep them out of the identity graph |
| `port_contracts.py` | 0/1-junction **circuit** port contracts | a different sense of "junction"; no reuse |

The capability still to port is the substitution search: the item's
`derive_from` chains declared axioms through intermediate quantities, while
`derive_across` enumerates direct linear combinations only. That is the one
existing capability the licensed union does not yet have.

---

## Squares in Squares — the way forward (18 November 2026)

Runs 71–74 settled the *search* question and left the *construction* question
open. This is the list, in the order the measurements say to spend on it, with
the command that resumes each. Nothing here moves a row by itself.

**The one-line diagnosis.** The score is exactly rotation: 447 aligned rows, all
at `⌈√n⌉`; 553 beats, none aligned; 447 + 553 = 1000. A row therefore moves only
if its **angle multiset** moves, and the 0.163635 to the leader sits in rows that
need a word this project has not written down. It is a construction gap, not a
search gap — runs 65–74 spent nine runs proving that from three directions.

| # | target | why it is next | status | resume |
|---|---|---|---|---|
| **W1** | **Multi-lattice seams at irrational offsets.** Two lattices meeting along a seam, offset by a surd (the 0.384808 of `22`, the exclusion list of `23`). | The only structure that can beat a single-word row *without inventing a new word*, and it is the one family the project censused but never closed. A seam is a configuration, not a relation (PL-7). | listed | `python3 scripts/seam_wheels.py` |
| **W2** | **The angle word as generator, not verifier.** `31` and `28` hold the word algebra (rational t-basis angles); the packers are verifiers. Generate a word, build the packing exactly, gate it. | This is the only lever the score has ever responded to, and run 73's corollary says so by theorem. | listed | word algebra in `31`; build on `cert_extend.py` |
| **W3** | **The 675 rows above n = 324.** 0 of them can be proved from the present catalogue. | The largest single block by score, and it is a *source* problem: the frontier stops at 324. | blocked | needs an above-324 catalogue |
| **W4** | **The depth-2 margin at n = 11: +4.48e−3.** A competing declared-branch structure needs 3.881566 against the record's 3.877084. | The tightest neighbourhood measured anywhere in the table. A targeted search there is aimed at four milli-units, not at a structure — the cheapest remaining near-miss to understand. | measured, unspent | `python3 scripts/bb2d.py --flips 2 11` then the `where` field in `bb2d_flips2.json` |
| **W5** | **Base-less residue columns.** Corrected census (PL-33): 37 residues with a beating row, 24 without; the base-less ceiling is 0.8068. | Real but small: ~0.0046 per row. Only after W1/W2. | listed, low value | `python3 scripts/leech_audit_fix.py --json`; `area_ceiling.py` |

**Doors that are closed — do not spend on them again.**

* **Aligned rows by rearrangement.** Theorem (`36` §2, `36` §3): axis-parallel
  squares cannot beat `⌈√n⌉`. 447 rows, 0 exceptions.
* **Branch changes at frozen angles.** `bb2d.py --flips 2`: 87,767 structures
  within two changes, 0 improvements, and only 9,179 of them differ at all —
  of the 1,543 single flips only 322 change the optimum. Run 71's 6,684 flips
  were a ranked depth-1 sample of this space; this run solves all of it at
  five rows.
* **3D cubes.** `L_d(n) = ⌈n^{1/d}⌉` in the axis-parallel class, every n
  (`36`). Note the class: in 2D n = 5 already beats it by rotation, so the
  theorem is not a statement about rotated solids.
* **`declp3.py --milp`.** Retired in run 74 (`37` §5): subsumed by the counting
  argument, and its relaxation is the construction measured empty in 2D.
* **Dropping the global disjunction into a black-box MILP.** Root bound = the
  largest square's own extent (1.0 / √2), i.e. no bound at all (`37` §2).

**The one number to keep in view.** `22.218056945`, 553 beats, guarded by
`sqscore.guard()`. Anything that would move it must first pass the exact gate,
and the 12-dp round trip means an "improvement" smaller than 1e−9 is not one.

---

## The squares branch, run 96 (20 November 2026) — the honest score, the window above 1000, and the 7-rung read

**What the round asked.** Three questions left open by run 95's closure of the census's 151 row:
does *any* exact sentence beat a delivered row at the same count; what do the families emit above
`n = 1000`, where the table and the float tables stop; and where does all of it sit on the 7-rung
perception-and-escalation ladder. Written up in
[`59-ESCALATION-LADDER-BRIDGE.md`](source_material/ToDo/squares_in_squares/59-ESCALATION-LADDER-BRIDGE.md)
and, for the chord check, `58-THE-STAIRCASE.md` §7.2. **No row moved; `submission.csv` untouched.**

**The honest score: 0 of 364.** `family_spin.py --calibrate` spins Ridge, Strip, Diamond,
Ring and Staircase over Q(√2), Q(√5), Q(√7) and three rational-t words — 364 members that share a
count with a delivered row. **0 beat the table; 6 are at parity** (the atoms `n = 5, 10, 18, 19, 40`,
agreeing with the delivered pose to 1.3–1.7e−9 — the table's own polish, not a win); **358 are
behind**, and the shortfall grows with `N` (closest: the Seventh at `n = 5`, by `0.001391`; the 45°
rung at `N = 901` is `30.70711` against the table's `30.52082`, and splicing it in would *raise* the
total by `0.0062`). The algebra is the reason: every family is single-word, `L = 2k + w` with
`w = m·min(1/(c+s), c+s) ≥ ½√2` (minimum at `x = c+s = 1`, the 45° word), while the delivered rows
at `N = 4k²+1` sit at `2k + O(1/k)`. **The table is not reproducible by this alphabet.** It explains
the *sides* of 576 of the 1000 rows (447 grid, 99 Q(√2)-pose, 18 Q(√2)-side, 5 Q(√7)-side, 3
Q(√5)-side, 4 rational-t) and constructs 6 of them as sentences; the other **424 rows have no field
class at all**.

**Above 1000, exactly.** The ridge is zero-drift at `N = 1025` (`L = 32 + ½√2`,
void `−½ + 32√2` = 44.754834, **3724 contacts**, 0.293 inside the grid's 33) and at `N = 1937`
(`L = 44 + ½√2`, **7228 contacts**), with the seven words at `N = 1025` ordered exactly as
`min(x, 1/x)` predicts — 45° best (`32.707107`), `t = 1/5` worst (`32.764706`). **The staircase does
not scale**: from `k = 6` the brick wall is longer than the seam it fills, so the sentence collides
(38 violations at `k = 6`, 56 at `k = 7`, 297 at `k = 21` where the bbox is `62.71` against the law's
`44.82`) and **no gauge** among 25 slides at `k = 6` gates. Its side law is `k = 5` only — it is a
reading of one row, not a family. The ring refuses at `k = 2, 3` (`ring_chain_adrift`).

**The chord check, repaired and then made uniform.** Run 95 read the largest *single block's* free
`v`-chord (`0.558490`), which does not cover a pair whose two `u` values fall in different blocks —
and the table's rotation has a `5/4`-wide `v`-window, so that case is real. The instrument now
decides on the **union** of the closed blocks' free sets: `0.624681 < 1`, the sound quantity, and
control 27 asserts the union exceeds the largest block's chord. `--chord-spin` then runs the same two
instruments over the census word and **all 66 rotation classes** (the 78 field-compatible words):
**66 of 66 place one square, 66 of 66 place no pair**, free spans `0.428760–0.780198` (`u`) and
`0.440099–0.822876` (`v`). 2 m 02 s as its own run, deliberately outside the suite.

**The ladder, candidly.** Rung 1 (Golay substrate): we hold the 24-pocket leech address, and after
the run-33 audit its only signal *is* the rotation flag. Rung 2 (integer): 447 axis rows exactly at
`⌈√n⌉`, and it cannot see the 553 beating rows at all. Rung 3 (rational/algebraic): home — the gate,
the cage, the chord union, 1169 certificates, and the lossless ceiling. Rung 4 (scan): the delivered
table itself, whose 2e-9 pose is why the table's own 151 overlaps our exact 149 by `−2.365e-9`.
Rung 5 (topology): classifies our contact graphs, cannot propose one. **Rung 6 (Griess/Conway):
empty** — a Golay shadow is not a Co₀ label on an exact carrier. Rung 7 (certificate): our strongest,
and its refusals keep the `climb_principled` discipline.

**Where we are blind, with the numbers.** (i) The table's escape word `19211307153/31250000000` rad
is in no `Q(√d)` at height ≤ 4096 and is not Pythagorean — so "151 is impossible" is a statement
about `Q(√7) ∪ Q_Pyth` plus a measured `−2.365e-9` overlap, **not** about squares. (ii) One word per
family is why `w ≥ ½√2` and why `2k + O(1/k)` is unreachable. (iii) 424 of 1000 delivered rows are
outside any field — that is the size of the blindness, in rows.

**The next move — one production, not a search (PL-37).** A **second word in the same sentence**,
declared by a *mixed* tangency (tilted₁ against tilted₂ along tilted₁'s own axis), so the closure is a
polynomial identity in both words. The ring is the template: its pinwheel offset
`2·p5·v + 2 = 5/4 − (4k−1)/4·√7` cannot be cancelled by one word, and a second word can. First target:
keep the 45° blocks at `k = 16` (`N = 1025`, `L = 32 + ½√2`, 3724 contacts) and put the bar at `θ₂`
in the seam, then a square at `θ₁` in the void. Falsifier: if no word pair closes below `2k + w` for
every `k ≤ 8` over `Q(√2) ∪ Q(√5) ∪ Q(√7) ∪ Q_Pyth`, the single-word ceiling is a theorem of the
family's topology and the next move is the *relaxed* rung (the table), not grammar. `staircase_cage`
and `staircase_chords` already answer feasibility for any word pair in one field, so the work is the
builder, not a new engine.

**Resume.**

```
cd source_material/ToDo/squares_in_squares
python3 scripts/glm_wheels.py --selftest        # 27 controls, ~1 m 49 s
python3 scripts/glm_wheels.py --audit           # 243 functions, 0 offenders
python3 scripts/glm_wheels.py --chord-spin      # 66/66 no-pair, 2 m 02 s
python3 scripts/family_spin.py --calibrate      # 364 members: 0 beat, 6 parity, 358 behind
python3 scripts/family_spin.py --beyond strip   # N = 1025..1027, 1937..1939, zero drift
python3 scripts/record_guard.py                 # OK
```

**In flight.** Nothing half-written. The two-word builder of §6 is named and unbuilt; the 424
continuous rows are measured and unclaimed.
