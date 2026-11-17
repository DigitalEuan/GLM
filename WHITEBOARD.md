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

**#2 in flight (17 November 2026).** `wheels/quantity_graph.py` holds the
absorbed item's 43 junctions and 15 non-identities, audits them (one bad
junction, `W36 pair_energy -> W4 energy`, and one vacuous guard, `W37
relaxation_time`), and contracts the sound edges into identity classes; four
vacuous guards are repaired with the other-wheel name read out of their
reason (`W39 magnetomotive_force` against `W1 current`, `W41
temperature_difference` against `W8 temperature`, `W42
moment_of_inertia_of_section` against `W4 moment_of_inertia`, `W36
pair_energy` against `W5 energy`).

`wheels/cent_union.py` feeds those classes to `domains.split_system` over all
39 wheels. The third junction table **duplicates most of Phase 66's and the
domain table's** entries; the merge keeps each pair once (15 pairs), and the
graph's 28 sound edges pass as explicit pairings, so differently named
quantities join (`pair_penetration`/`stress`, `magnetic_flux`/`flux`). The
rational engine reads the cent wheels' fractional powers.

**Energy family measured (8 pre-registered questions):** the 39-wheel naive
union is ill-posed on all 8 (merging six `energy` copies makes the exponents
non-unique); the six energy wheels alone derive 7; the licensed union answers
3 and refuses 5, of which **4 are the capacitor `1/2 C V^2` against the
delivered `C V^2` factor-1/2 conflict** (`charge`/`voltage`,
`capacitance`/`voltage`, `power`/`time`, `energy`/`time`). The refusal names
both formulas rather than choosing one.
