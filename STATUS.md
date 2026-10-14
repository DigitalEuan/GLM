# Status


## Tier 0 — the coarse read

**Question.** What is still to do, where does the work stand in one screen, and how is a run closed?

**Verdict.** This is the To-Do list: what is open, sharpest first, with the closed record moved out to the archive and the standing description of the system moved to `SYSTEM.md`.

**Deciding figure.** Every instrument in the table at the head of the document reports its own result on demand.

**Recomputed by.** `glm_universal.signoff.ledger.suite_totals`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

> **Positioning.** Before starting a round, read the Positioning section of
> [`PROJECT_DIRECTIVES.md`](PROJECT_DIRECTIVES.md): what is claimed, what is
> not, and why an absence at one layer is not a refutation. It is stated once,
> there, and every document in this repository is written under it.

## How to work in this repository

**Commit after each completed step, not once at the end** (directive D1). A
step is anything that leaves the tree working — one document reconciled, one
test added, one lemma proved.

This is the To-Do list: what is open, sharpest first, with the closed record moved out to the archive and the standing description of the system moved to `SYSTEM.md`.

**This document is the To-Do list, and only that.** It holds what is open
(§2), the instrument table in one screen (§1) and the close (§3). It does not
hold the record:

* what the system **is** — the standing description, the full instrument
  table and the re-verification commands — is [`SYSTEM.md`](SYSTEM.md);
* what each round **did** is [`MASTER_PLAN.md`](MASTER_PLAN.md) (and
  [`archive/MASTER_PLAN_ARCHIVE.md`](archive/MASTER_PLAN_ARCHIVE.md));
* the running account this document used to carry, round by round up to
  Phase 110, and the candidate list as it was named, are in
  [`archive/STATUS_ROUNDS_ARCHIVE.md`](archive/STATUS_ROUNDS_ARCHIVE.md);
* how to run a round is [`ITERATE.md`](ITERATE.md).

**Keeping it short.** When a round closes, *delete* the To-Do line it took
(its record goes to `MASTER_PLAN.md` and its study), add the lines the round
left as new To-Do lines, and replace the "Just closed" paragraph below. Never
stack a second "round before" paragraph here: that stack is what made this
document three thousand lines long.

**Every run updates the paper.**
[`GLM_ACADEMIC_PAPER.md`](studies/GLM_ACADEMIC_PAPER.md) is the record of the
GLM as a whole and is kept up to date in every development run (the owner's
standing instruction; it is a row of the close checklist, `ITERATE.md` §4.1).

**Starting a new round? Read [`ITERATE.md`](ITERATE.md) §0, then §2 below.**

**Just closed: Phase 138** (the record is [`MASTER_PLAN.md`](MASTER_PLAN.md),
"Phase 138"; the study is
[`TOOL_VERDICTS_STUDY.md`](studies/TOOL_VERDICTS_STUDY.md), 6 of 6 marks),
the three next steps §2.2 listed after Phase 137. A tool's yes/no answer is
now a planner step (*is 0xff reachable from 0x0* is `False`, with the gate
tool's proved reason); *if A, B, otherwise C* builds only the branch its test
selects; *the first convergent of pi whose denominator is above 1000* is
unrolled into checked steps with no iteration cap, admitted because a proved
measure ends it (`search_terminates`). The classical closest-fraction theorem
is proved (`RequestProject/GLM/NearestFraction.lean`:
`nearest_fraction_candidates`), so `best approximation` checks a Farey
certificate for every bound and the 20,000 bound (and the 10^12 one) is gone.
Fresh held-out rewordings: 12 of 16 read, 12 right, 0 wrong; Phase 137's two
misses now read. Verdict questions: 14 of 14.
**Before it, Phase 137** (8 of 8 marks): tool values.

---

## 1. Where the work stands, in one screen

| instrument | command | result |
|---|---|---|
| test suite | `python3 -m pytest glm_universal/tests -q` | **<!--figure:suite-->5,397 tests across 181 of the 183 test files, 18,972 subtests, outside the document checks<!--/figure-->**, zero failures |
| end-to-end CLI evaluation | `python3 -m glm_universal.evaluation --jobs 8` | **<!--figure:evaluation-case-count-->188<!--/figure-->** cases — 0 confidently wrong, every refusal a `boundary` |
| benchmark suites | `python3 -m glm_universal.benchmarks` | **2,389 / 2,390** across 5 suites |
| capability probes | `python3 -m glm_universal.capabilities` | 33 probes — 20 hold, 13 break, 0 surprises |
| Lean development | `lake build` (repository root) | <!--figure:lean-files-->210 Lean files<!--/figure-->, **0 `sorry`** |
| corpus | `python3 -m glm_universal.corpus --check` | the tier contract, the coverage claim of `ENTRY.md`, every generated block and every derived cache |

The package holds **<!--figure:registers-->8 registers<!--/figure-->** beside a 45-class comparison register,
**<!--figure:query-kinds-->25 query kinds<!--/figure-->** one of which
dispatches **<!--figure:report-subjects-->67 report subjects<!--/figure-->**, and 3 tasks. The Lean development is
addressed declaration by declaration: `reasoning/lean_address.py` gives each of
the <!--figure:lean-declarations-->5,167<!--/figure--> declarations a deterministic Leech address computed from 24 structural
counts of its statement. Read back exactly <!--figure:lean-declarations-->5,167<!--/figure-->/<!--figure:lean-declarations-->5,167<!--/figure--> with 0 coordinate errors
(`report lean`). The other forty-odd instruments, each with its command and its
current figure, are the table in [`SYSTEM.md`](SYSTEM.md) §1.

---

## 2. To Do

Sharpest first within each group. Each line names the study section that
states the item in full; the bracketed names (`lattice item 6`, `track M`, …)
are the names earlier records use, kept so that a reference in a study or a
module docstring still finds its line. When a line is taken, delete it here and
record the round in `MASTER_PLAN.md`.

### 2.1 The next round — take one of these

1. **The placement guard in the answering path** (left by Phase 129). The
   answering path reads the ladder unguarded, and the unguarded ladder
   answers 8, 1 and 2 queries wrongly on three held-out perturbation sets;
   the placement guard removed all of them on four sets at a cost of 5 to 9
   per cent of the correct answers. Putting it in changes answers the
   evaluation pins, so it needs a frozen-path comparison, and the per-cell
   radius table must be kept beside the digest of the carriers it came from.
   [`PLACEMENT_GUARD_STUDY.md`](studies/PLACEMENT_GUARD_STUDY.md) §7.4.
   *Correction (Phase 130):* no module a query loads imports the ladder the
   guard protects (`ladder_escalation`, `cell_guard` and `placement_guard`
   are reached only from `tools.py` and other measurement modules), so the
   first step of this item is a query kind that reads a carrier by its
   address; only then is there an answering path to guard
   ([`COUNTER_LASSO_STUDY.md`](studies/COUNTER_LASSO_STUDY.md) §0).
   Phase 134's `carrier` kind reads a 24-bit Golay word, not a ladder
   carrier, so this first step still stands; the carrier read is the pattern
   it can follow ([`PROTECTED_TAG_STUDY.md`](studies/PROTECTED_TAG_STUDY.md)
   §7.5).
2. **The budget rule in the walk and the answering path** (left by Phase
   124). The walk's own reading (patience 40) certified 225 of 256 held-out
   deep holes, and `classify_carrier` still defaults to a patience of 60;
   replace both with the budget rule (no barren stop, 1056 starts) under a
   frozen-path comparison, since it changes answers the evaluation pins.
   [`PROBE_BUDGET_STUDY.md`](studies/PROBE_BUDGET_STUDY.md) §7.4.
3. **`L5` in the other deep-hole reports** (left by Phase 123). Only
   `report hole configuration` answers by `L5`; `report hole classifier`,
   `hole ladder` and `hole failures` still name a hole with the ladder's
   readings. Each would move under a frozen-path comparison like B5's.
   [`LATTICE_COMPLETION_STUDY.md`](studies/LATTICE_COMPLETION_STUDY.md) §7.6.

4. **The operations ladder in the planner and the session** (left by Phase
   125). The ladder and GLM-BAT are reached only through `tool ladder` and
   `tool machine`; giving the planner's plans or the session's default
   domains the ladder's vocabulary (a plan step as a GLM-BAT line, drift and
   rollback as planner checks) changes answers the evaluation pins, so it
   needs a frozen-path comparison.
   [`OPERATIONS_LADDER_STUDY.md`](studies/OPERATIONS_LADDER_STUDY.md) §7.4.

### 2.2 Smaller follow-ups left by closed studies

Each is a section a closed study ends on; any of them can be folded into a
round from §2.1 or taken as a short round of its own.

* **The connected machine, the rest** (left by Phases 136, 137 and 138).
  Since Phase 138 a tool's verdict is a planner step, but only from the two
  tools with a boolean figure (`gates`, `wiring`) and from any tool value by
  equality; the ladder's relations and a law's fate are not yet verdicts. The
  search reads one shape (the first convergent past a denominator bound,
  whose measure is proved); a search without a proved measure — *the first
  term of the continued fraction of X above 100* — waits for a proof, since
  no cap is to be added. Four of the sixteen fresh rewordings are unread
  (*the fraction closest to e with …*, *the kissing number of the
  24-dimensional leech lattice*, *the number of norm 6 vectors in the leech
  lattice*, *the minimum number of gate moves to go from …*); reading them
  now would be a post-hoc fit, so a fresh held-out set comes first. The
  primality step keeps a ceiling of 10^12. `tool wiring` names the 20
  modules no question reaches, and the two ladder guards among them wait on
  item 1 of §2.1.
  [`TOOL_VERDICTS_STUDY.md`](studies/TOOL_VERDICTS_STUDY.md) §7,
  [`CONNECTED_MACHINE_TWO_STUDY.md`](studies/CONNECTED_MACHINE_TWO_STUDY.md)
  §7.3.

* **The designed substrate, the rest** (left by Phases 133, 134 and 135). The
  `carrier` kind reads the stages and the protected tag, but the soft
  certificate is reached only through a supplied soft reading: its acceptance
  rate on a soft reading the GLM produces itself is not measured, because the
  GLM produces none yet. The carrier read carries no guard of its own beyond
  the stages' assumptions: a fifteen-bit tag with three or more flipped bits
  can mislead radius 2 (`tag15_three_flips_mislead`; 26,681 of 680,064 tied
  reads with three consecutive flips, post hoc), and reading it at radius 1 instead never misleads on three
  flips but corrects only one. Since Phase 135 the tag lengths are bounded:
  the seven-bit tag is the shortest possible and the protected tags are the
  shortest built on seven bits; a tag of another shape with 9–10 bits (one
  flip) or 11–14 bits (two) is neither found nor excluded, and the search's
  control never reached 15 bits, so a stronger search comes first
  ([`SHORTEST_TAG_STUDY.md`](studies/SHORTEST_TAG_STUDY.md) §7.5). The substrate study's other results (the four-label
  mirror, the 86–128-value Golay tag, the Delsarte bound) are cited, not
  re-proved.
  [`PROTECTED_TAG_STUDY.md`](studies/PROTECTED_TAG_STUDY.md) §7.5,
  [`DESIGNED_SUBSTRATE_STUDY.md`](studies/DESIGNED_SUBSTRATE_STUDY.md) §7.5,
  [`SHORTEST_TAG_STUDY.md`](studies/SHORTEST_TAG_STUDY.md) §7.5.

* **Norm 256 and the hex colour, the rest** (left by Phase 127). `H16` is
  measured beside the ladder only; putting it into the answering path needs a
  frozen-path comparison. The 4096-colour subspace that decides membership of
  the rotated Leech rung has no use yet, because that rung was retired; other
  rotations of the Leech lattice were deliberately not compared on the 568
  queries. [`NORM_256_HEX_STUDY.md`](studies/NORM_256_HEX_STUDY.md) §7.5.
* **GLM-BAT, the rest** (left by Phases 125, 126, 130, 131 and 132). Stream
  merging (`2>&1`), `SORT` options, `FOR /F`, `SETLOCAL`/`ENDLOCAL` and
  delayed expansion are refused. The counter-lasso reading refuses growth that
  is not a translation (L12, N5, N6: quadratic or geometric; L12 never
  halts) — since Phase 132 it *diagnoses* them, and the closed forms are
  proved (`const_second_diff_closed_form`, `const_ratio_closed_form`), so the
  next step is a jump over a pass whose comparison is quadratic in the pass
  number; a jump whose output would pass 1,000,000 lines (P6); an `ECHO`
  with redirection or inside a chain or test body on a pass (P10); a constant
  read through `ERRORLEVEL`; and comparisons of text. The run encoder takes
  the block covering the most lines even when it has only two copies, so
  P8's printed text opens with two 16-line blocks; asking for three copies
  would state it as the hand computation expected.
  [`AFFINE_OUTPUT_STUDY.md`](studies/AFFINE_OUTPUT_STUDY.md) §7.5,
  [`CONSTANT_BOUND_STUDY.md`](studies/CONSTANT_BOUND_STUDY.md) §7.4,
  [`COUNTER_LASSO_STUDY.md`](studies/COUNTER_LASSO_STUDY.md) §7.4,
  [`OPERATIONS_LADDER_STUDY.md`](studies/OPERATIONS_LADDER_STUDY.md) §7.4.
* **Radicals, the rest** (left by Phases 114, 115 and 116). Compositions whose
  outer polynomial has degree below 5, with the obstruction in the inner
  polynomial, and imprimitive groups that are not compositions over the
  rationals, are still silent
  ([`COMPOSED_RADICAL_STUDY.md`](studies/COMPOSED_RADICAL_STUDY.md) §4); so
  are primitive groups of prime-power degree with no element whose power is
  a transposition or a 3-cycle (`PSL(2, 7)` on eight points), and primitive
  groups with no `(n - 1, 1)` element (`S5` on the ten pairs of five points)
  ([`PRIMITIVE_DEGREE_STUDY.md`](studies/PRIMITIVE_DEGREE_STUDY.md) §4). A positive statement of solvability
  (the resolvent sextic for quintics). Dedekind's theorem in Lean, which
  would close the gap between the factorisation and the group element. The
  16-modular-factor cap (lattice reduction past it).
  [`PRIMITIVE_RADICAL_STUDY.md`](studies/PRIMITIVE_RADICAL_STUDY.md) §4.
* **The router's reach into the Lean tree** (left by Phase 115). Every unit
  that reaches the router takes the whole Lean development through
  `reasoning/lean_address.py`'s tree walker, and the median cost of one Lean
  edit now stands one unit above half the units that name any Lean file;
  split the walker out of the module the answering path reads.
  [`ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md) §5k.
* **Derivations, the rest** (left by Phase 119). Six or more variables
  (`TOO_MANY_VARIABLES`); claims that neither Zhang–Yeung nor chains of two
  copies decide (8 of the 40 five-variable battery claims and Phase 118's 3
  undecided claims stay `NOT_SHANNON`); rate distortion with a symbolic
  source, and continuous sources; Robin at both ends with coefficients of
  opposite sign (the number of negative eigenvalues then depends on `a`, `b`
  and `L` together), a symbolic coefficient at the near end, and variable
  coefficients.
  [`DERIVATION_FOUR_STUDY.md`](studies/DERIVATION_FOUR_STUDY.md) §6.
* **Meta questions, the rest** (track M; left by Phase 117). Recognition of
  rewordings: p92a goes to the earlier `deep_hole_tie` frame and h92 ("coset
  weight is 4") is read by no frame. A meta question on a topic outside the
  declared eighteen is not read.
  [`META_QUESTIONS_STUDY.md`](studies/META_QUESTIONS_STUDY.md) §5.
* **Explanations, the rest** (track E; left by Phase 120). Recognition of
  rewordings: 30 of the 35 held-out rewordings are read by no frame (none is
  misread). A *why* question outside the declared 35 is not read, and the
  explanations themselves are still refused. The nuclide register holds ground
  states only — no excited states (the Hoyle state is quoted), isomers or
  abundances.
  [`EXPLANATION_ANCHOR_STUDY.md`](studies/EXPLANATION_ANCHOR_STUDY.md) §5.
* **The studies the router holds** (left by Phase 117). The meta frames read
  six studies, so editing the paper, the integer-decision study or the
  symbolic-parameters study now makes 48 units stale where it made two or
  three; a stored, digest-checked copy of the quoted sentences would take
  that back out.
  [`META_QUESTIONS_STUDY.md`](studies/META_QUESTIONS_STUDY.md) §6.
* **Lattice, measured but not settled.** Whether larger ensembles make
  `A_1^24` or `A_2^12` emit a stray (not measured;
  [`STRAY_BLIND_STUDY.md`](studies/STRAY_BLIND_STUDY.md)). A margin other
  than twice the nearest distance for the adopted guard, which refuses 137
  queries it used to answer (lattice item 8;
  [`SECOND_READING_STUDY.md`](studies/SECOND_READING_STUDY.md) §9).
* **The planner's utility gate** (item 9). Reading one of the loop's
  questions from English — the next measurable step before the supplied
  planner could earn promotion out of the sandbox under D14.
  [`PLANNER_LOOP_STUDY.md`](studies/PLANNER_LOOP_STUDY.md).
* **Frames and folds.** Cross-table comparison, differences between
  molecules, a frame over the nuclide register (which now exists, Phase 120,
  but is read only by the explanation anchors), one-sided ranges, the top `k`
  under a hole. [`DECLARED_FRAMES_STUDY.md`](studies/DECLARED_FRAMES_STUDY.md) §6.
* **Discourse.** The column handed to the planner's folds, a present-rows
  column, further phrasings, the plan store for the new shapes, an outside
  multi-turn set. [`DISCOURSE_STATE_STUDY.md`](studies/DISCOURSE_STATE_STUDY.md) §7.
* **The register against the world.** Sources for electron affinity and the
  melting and boiling points; isotope masses for the 34 world-silent weights;
  a held-out check of the narrowing.
  [`REGISTER_WORLD_STUDY.md`](studies/REGISTER_WORLD_STUDY.md) §6.
* **Temperature scales.** A register in degrees Fahrenheit (the declaration
  `GLM.MeasurandKinds.fahrenheit_kelvin` already states), an answer stated in
  degrees Celsius, the ITS-90 vapour-pressure ranges as interval values.
  [`CELSIUS_REGISTER_STUDY.md`](studies/CELSIUS_REGISTER_STUDY.md) §7;
  the measurand register's own remainder,
  [`MEASURAND_REGISTER_STUDY.md`](studies/MEASURAND_REGISTER_STUDY.md) §6.
* **Typed operators.** Polar phasors, three-phase power and power-factor
  correction, the verifier's rank algebra joined to the typed values.
  [`TYPED_OPERATORS_STUDY.md`](studies/TYPED_OPERATORS_STUDY.md) §6.
* **The Python dialect and the reverse grammar.** Unicode case and
  whitespace tables as a register, booleans as a term, sets and
  comprehensions ([`THIRD_SORT_STUDY.md`](studies/THIRD_SORT_STUDY.md) §6);
  `break`, closures, the truth of sequences, a trace inside calls, a program
  with state handed to the planner as a sentence
  ([`IMPERATIVE_GRAMMAR_STUDY.md`](studies/IMPERATIVE_GRAMMAR_STUDY.md) §6);
  keywords and defaults, starred displays, unpacking in the imperative grammar
  ([`UNPACKING_RESCORE_STUDY.md`](studies/UNPACKING_RESCORE_STUDY.md) §6);
  the relay reading the integer certificate kinds and an `INDEPENDENT`
  verdict's witness handed on as a follow-up
  ([`REVERSE_TCT_STUDY.md`](studies/REVERSE_TCT_STUDY.md) §12).
* **Second readings.** Framing an existing register by default; a soft
  channel whose reliabilities come from outside the views.
  [`SECOND_VIEW_STUDY.md`](studies/SECOND_VIEW_STUDY.md) §6.
* **Substrate-native cognition.** Semantic judgements as annotated
  provenance (E4); deeper PCGS proofs (E7).
  [`SUBSTRATE_NATIVE_COGNITION_STUDY.md`](studies/SUBSTRATE_NATIVE_COGNITION_STUDY.md) §8.
* **Supplied material not yet read in** (candidate G and Phase 49). The
  language half of `mog_cube_1` (about thirty files) and the unported part of
  `ObserverY.lean` (Appendix C.3 of
  [`GLM_ACADEMIC_PAPER.md`](studies/GLM_ACADEMIC_PAPER.md)); the vision
  experiments script `glm_vision_experiments_v14.py`; the v4 query-loop
  reading (no control yet) and the v4 higher-lattice escalation (argued, never
  run) of [`NOW_RECEIPT_STUDY.md`](studies/NOW_RECEIPT_STUDY.md).
* **The soft floor's breaks at rate 1/5**, which remain under every contract
  variant. [`CONTRACT_MATRIX_STUDY.md`](studies/CONTRACT_MATRIX_STUDY.md),
  [`RATE_POSTERIOR_STUDY.md`](studies/RATE_POSTERIOR_STUDY.md) §4.

### 2.3 Waiting on the owner

* **Outside material:** a register that arrives anonymous on its own (item 4)
  — goals from a second Lean development, or from a generator, scored against
  the anonymous-register controls.
  [`ANONYMOUS_REGISTER_STUDY.md`](studies/ANONYMOUS_REGISTER_STUDY.md).
* **Decisions:** whether any discrepancy found against the outside sources is
  ever written back into a register
  ([`REGISTER_WORLD_STUDY.md`](studies/REGISTER_WORLD_STUDY.md) §6); the
  element register's aluminium melting point, 933.437 K against ITS-90's
  933.473 K ([`CELSIUS_REGISTER_STUDY.md`](studies/CELSIUS_REGISTER_STUDY.md)
  §7); the planner's DC `power` asked an alternating question
  ([`TYPED_OPERATORS_STUDY.md`](studies/TYPED_OPERATORS_STUDY.md) §6).
* **Proposed for retirement:** candidate P's 42 PIPELINE laws, which could be
  re-read only through UBP pipelines the GLM does not implement
  ([`LAW_TRIAGE_STUDY.md`](studies/LAW_TRIAGE_STUDY.md) §3); candidate H's
  concept 6, which waits on a trilinear object in the runtime.

### 2.4 Parked, and ongoing

* **Parked at the owner's direction (Phase 106):** the rest of the retrieval
  line — N5 (a native word ranking with the part letter words first), the AST
  index study's §8, the citation-scope study's §6 and the document-tree
  study's §6. Kept as the record; every operation it built stays in the
  system.
* **Ongoing rather than finishable:** the lexicon's vague `related_to`
  triples and the sparse chemistry cells — see [`SYSTEM.md`](SYSTEM.md) §3.2.

**The discipline any item is taken under**, unchanged: describe or measure,
never assert; count what does not generalise; freeze the path being replaced
so the new one has something to agree with; and the end-to-end evaluation must
return the same answers and the same refusals.

---

## 3. Closing a run

The close is one exact sequence, written out with its measured cost in
[`ITERATE.md`](ITERATE.md) §4. In short: finish the work and write it down
(study, `MASTER_PLAN.md` phase, this list), then from `overlay/` run
`corpus --refresh`, `corpus --check` and `signoff --close --jobs 8` once,
touch no document afterwards, and commit. The test-suite row above is the
sign-off ledger's own count, recorded by the close.

---

## 4. The document map

There is no hand-kept index any more, because a hand-kept index is a stored
table and this project's rule is that a table may be kept only beside the
digest of what it came from.

* [`ENTRY.md`](ENTRY.md) states the reading order and the coverage claim:
  these documents describe the system as it is, everything else is a record of
  a round.  The claim is tested — `glm_universal.corpus.checks` fails if a
  current-state document is unreachable from it or an archived one is missing
  from its list.
* [`DIGEST.md`](DIGEST.md) is that list at tier 0, one row per document —
  question, verdict, deciding figure, and the function that recomputes it.  It
  is **generated** from the documents' own tier-0 blocks by
  `python3 -m glm_universal.corpus --write`, so it cannot drift from them.
