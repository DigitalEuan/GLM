# One evidence and result model — every answer and refusal of the evaluation read into the same ten fields

## Tier 0 — the coarse read

**Question.** Can the answers of the planner, the grammar, the toolbox, the lattice reads, the corpus and the conversation be read into one result representation that exposes, for each, its answer or candidate set, its kind of evidence, its witness, the theorem behind it, its certification boundary, its cost, its open tie, its refusal reason, its reply history and whether it was replayed — truthfully, over the whole evaluation?

**Verdict.** Yes, after two repairs the census itself found. All 223 evaluation questions read into the ten fields; the model's status agrees with the evaluation on all of them, where the surfaces' own solved flag alone disagrees on two; every refusal names its reason. The first take missed two marks: 26 cited theorem names did not resolve, all of them a Python repr's closing quote read as a prime (an extractor artefact, amended), and two answers' own column 3 did not reproduce them — the trilinear template could not replay a triple of axis labels and the language report's column 3 had drifted behind its report. Both were real defects of the replay, fixed; on the re-take every one of the 171 replayable answers verifies. Re-taken on 31 October 2026 on the reconstructed model, with the Lean declaration lookup restored so that every cited name is checked against the declarations of the build tree, over the 227 questions the evaluation now holds: 9 of 9 marks again (§7.6).

**Deciding figure.** Phase 169 record (20 October 2026): 9 of 9 marks on the re-take (7 of 9 on the first: R5 and R6 missed); 171 of 171 column-3 replays verified (169 of 171 first); 50 cited theorem names, all declared; status: 172 answered, 5 open, 3 contradicted, 43 refused; boundary: 171 certified, 5 checkable, 46 refused, 1 uncertified. Re-taken 31 October 2026 on the reconstructed model (§7.6): 9 of 9 marks; 173 of 173 replays verified; 21 cited names, none undeclared among the 9,341 declarations of the build tree; status: 174 answered, 5 open, 3 contradicted, 45 refused; boundary: 173 certified, 5 checkable, 48 refused, 1 uncertified.

**Recomputed by.** `glm_universal.reasoning.evidence_model_study.evidence_model_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 20 October 2026 (pre-registered 20 October 2026: §§0–6 were committed before the census of §7 was taken; measured 20 October 2026).*

*Last altered 1 November 2026 (Phase 186: re-taken over the 237 evaluation cases, noted in §7.6). Earlier, 31 October 2026 (repository check: 1 link repointed to where the file now lives after the October 2026 reorganisation — supplied items under `source_material/done/` or `source_material/ToDo/`; the text is unchanged; its run commands now start from the repository root (`PYTHONPATH=src`); §7.3 records that the two replay repairs were lost with the upload and restored; later the same day §7.6 added — the re-take on the reconstructed model with the Lean declaration lookup restored — and the tier-0 block and the closing figures now give that re-take beside the Phase 169 record.)*

## 0. What this document is

A pre-registration for Phase 169. It takes Part II.1 of the owner's plan of
19 October 2026 ([`source_material/GLM_19OCT26_1.md`](../source_material/done/GLM_19OCT26_1.md),
*create a unified evidence and result model*): bring the planner, corpus,
domain, lattice, certificate and conversation systems toward a common result
representation exposing ten things — the answer or candidate set; the type of
evidence used; the source data and witness; the formal theorem or checker
involved; the confidence or certification boundary; the budget used; any
ambiguity or unresolved tie; the refusal reason; the conversation or reply
history; and whether the result was independently replayed.

**What was known when this was written.** While the adapter was written, the
223 evaluation questions were routed once to see which surfaces and query
kinds answer them (222 by the planner and grammar across 29 kinds, 1 by the
toolbox), and that run showed two questions whose solution is marked solved
while its answer is a refusal in words (`meaning of justice`, *denotes nothing
determinate*; `is 0.1 + 0.2 equal to 0.3`, *are not distinguished*); the
evaluation counts both as refusals by its declared markers. No field of the
model, no replay and no mark had been computed.

## 1. The model

`glm_universal/runtime/evidence.py`: a frozen `Result` with the ten
fields (`FIELDS`), and four adapters that read a surface's own object without
changing what it answered — `from_routed` (any verdict of the command line's
router), `from_solution` (a solution of the planner or the grammar),
`from_define` (a corpus definition, carrying the quality description of
Phase 168), `from_turn` (a conversation turn, carrying its reply history and
the tie it leaves). The declared rules are in the module's docstring:
**status** (`answered`, `refused`, `open`, `contradicted`; a refusal in words
by the evaluation's markers is `refused`), **evidence** by query kind
(`lattice`, `register`, `computation`, `certificate`, `corpus`,
`self-report`, `tool`, and `dialogue` when replies were read), **theorems**
as the `GLM.`-qualified names cited and those the Lean development declares,
**boundary** (`certified` when column 3 replays and verifies, `checkable`
when there are column-3 claims, `refused`, `uncertified`), **budget** (steps),
**replayed** (`True`/`False` when column 3 was run, `None` when there is no
column 3).

## 2. The census

Every question of the end-to-end evaluation, routed as the command line routes
it (`runtime.router.route`), read by `from_routed` with column 3 replayed in
a fresh interpreter. Beside it: five corpus terms through `from_define`
(`golay code`, `leech lattice`, `tier 0`, `register`, and the nonsense term
`yalog`), and a two-turn conversation through `from_turn` (`nearest to albedo
moved 4 by 1/4`, then the reply `no`).

## 3. Faculties

None moves: the model is a reading, it adds no answer and removes none. What
it changes is what can be *seen* of every answer at once.

## 4. The marks

| mark | met when |
|---|---|
| **R1** | every evaluation question gives a `Result`, without an exception |
| **R2** | the `Result`'s status agrees with the evaluation on every case: answered or open exactly when an answer is expected |
| **R3** | every refused `Result` names its reason |
| **R4** | every answered `Result` has a kind of evidence other than `unclassified` |
| **R5** | every `GLM.`-qualified name a `Result` cites is a declaration of the Lean development |
| **R6** | every answered `Result` that has a column 3 replays, and every replay verifies |
| **R7** | every open tie carries its candidates and its ambiguity, and every `Result` read from a question with `given` replies carries one history entry per reply |
| **R8** | the four corpus terms answer with a witness address and a `corpus:` boundary, the nonsense term is refused with its reason; the conversation's first turn is open with candidates inside the head, and its second carries one reply in its history and candidates inside the head |
| **R9** | every `Result` exposes all ten fields |

## 5. What would count against

R2 missed would mean the model's status says something the evaluation does
not — an answer the evaluation counts as a refusal, or the reverse. R5 missed
would mean an answer cites a theorem the Lean development does not hold. R6
missed would mean an answer's own column 3 does not reproduce it.

## 6. What is not claimed

The model is an adapter layer: the surfaces still return their own objects,
and the command line still prints them its own way. The evidence kind is
declared by query kind, not inferred from the computation. A `Result` read
from a toolbox, frames, reverse or Python surface has no column 3 here, and
its theorems are only those its text names.

## 7. What came out

`PYTHONPATH=src python3 -m glm_universal.tools evidence-model` (stored in
`reasoning/_data/evidence_model_study.json`, digest-guarded over the model,
the router, the session, the conversation, the Three Column Thinking engine
and the evaluation -- and, since 31 October 2026, over the Lean tree R5 reads
and its parser; `--write` re-takes it in about nine minutes with eight
processes).

§7.1–§7.5 are the Phase 169 record of 20 October 2026, kept as it was taken
over the 223 questions of that day. The stored file holds the re-take of 31
October 2026 on the reconstructed model, which §7.6 reports.

### 7.1 The census (Phase 169 record)

| field | what the 223 questions show |
|---|---|
| surface | planner and grammar 222, toolbox 1 |
| status | answered 172, open 5, contradicted 3, refused 43 |
| evidence | register 78, self-report 69, lattice 44, computation 26, corpus 5, tool 1 |
| boundary | certified 171, checkable 5, refused 46, uncertified 1 |
| candidates | 20 results carry a candidate set |
| theorems | 29 results cite a `GLM.` name; 50 distinct names, all declared |
| witness | 179 results carry witness values |
| budget | 843 solution steps in all |

The six answered results without a replay are the four `describe` answers,
the numeral-arithmetic description and the toolbox's Leech-norm answer, none
of which has a column 3; five of them are `checkable` (their column-2 claims
exist) and the toolbox answer is `uncertified`.

### 7.2 The marks (Phase 169 record)

| mark | first take | re-take | met |
|---|---|---|---|
| **R1** | 223 results, no exception | same | met |
| **R2** | status agrees with the evaluation on all 223; the surfaces' solved flag alone disagrees on 2 (`meaning of justice`, `is 0.1 + 0.2 equal to 0.3`: solved, answered by a refusal in words) | same | met |
| **R3** | 46 of 46 refused or contradicted results name a reason | same | met |
| **R4** | 0 of 177 answered results unclassified | same | met |
| **R5** | 51 names cited, **26 undeclared** | 50 cited, 0 undeclared (amendment R5′) | **missed**, then met as R5′ |
| **R6** | 171 replayable, **169 verified**: `trilinear 127 432 463` and `report language` failed | 171 of 171 verified | **missed**, then met after the two repairs |
| **R7** | 5 of 5 open ties carry candidates and ambiguity; 8 of 8 questions with `given` replies carry one history entry per reply | same | met |
| **R8** | `golay code`, `leech lattice`, `tier 0`, `register` answered, each with a witness address and boundary `corpus:strong`; `yalog` refused with its reason; the tie opens on `physics:absorptance` and `physics:albedo`, the reply `no` leaves `physics:albedo` with one history entry | same | met |
| **R9** | 223 of 223 expose all ten fields | same | met |

### 7.3 The two misses, and what they were

**R5 — an artefact of reading, amended.** All 26 undeclared names ended in
`'`, and for every one the name without it is declared: the names were read
out of a Python `repr` of the payload, whose closing quote the name pattern
(which allows Lean's prime) swallowed. The amendment, written after the first
take and named here as such: a trailing `'` is dropped when the name without
it is declared and the name with it is not. A genuinely primed Lean name that
is declared is kept as it is. R5 as pre-registered is reported **missed**; R5′
is met. Nothing was wrong with any answer.

**R6 — two real defects of the replay, repaired.**

* `trilinear 127 432 463`: the solver reads a bare integer operand as an axis
  label of the 2A class table, but the column-3 template looked every operand
  up by name in a domain's objects, so a triple of labels could never be
  replayed (`KeyError: '127'`). The template now writes a bare integer as the
  label itself, as the solver reads it, and keeps the lattice projection for
  concept names. The answer did not change: T = −3/32.
* `report language`: the report's column 3 had fallen behind its report in
  three ways — it consulted only the first of the two frozen parsers (the
  report itself consults both since `compare` was described), it took the
  parser's dispatch of `compare` to its two described matchers for a
  hand-written branch, and it did not recompute nine figures the report has
  claimed since (the nested family, the widenings, the undescribed kinds).
  All three are repaired; the report's figures did not change.

*Added 31 October 2026 (repository check):* the October 2026 upload carried
both templates from before these repairs, so both replays failed again; the
repairs are restored in `runtime/tct_engine.py` as described above, and the
replay gate passes (173 of 173 replayable answers verified).

Neither defect was visible to the evaluation, which checks the answer and
not its replay; both were visible to the model the first time every answer
was read with its replay beside it — which is what Part II.1 asked the model
to make possible.

### 7.4 What this does not show

The model is a reading over the evaluation's 223 questions; a question
outside them may reach a surface or kind whose adapter fields are thinner
(the toolbox, frames, reverse and Python surfaces have no column 3 here). The
evidence kind is declared by query kind. The surfaces still return and print
their own objects: the model is offered beside them, not yet in place of them.

### 7.5 What is left

* The command line and the conversation still print their own objects; a
  `--json` reading of every answer through `Result` is the natural next use,
  and it changes no answer.
* The frames, reverse, Python and engineering surfaces have no column 3 to
  replay, and their theorems are only those their text names.
* The evaluation checks answers, not replays: the two defects of §7.3 would
  have gone on unseen. Replaying column 3 for every answered case belongs in
  the evaluation's gate (it costs about nine minutes on eight processes).
* The evidence kind is declared by query kind; inferring it from the
  computation the answer actually ran is open.

### 7.6 Re-taken on 31 October 2026

*Added 31 October 2026 (repository check).* `runtime/evidence.py` was lost in
the October 2026 reorganisation and reconstructed from §1 of this study. Until
this re-take the reconstruction did not look the cited names up at all: it
copied every cited name into the list of declared ones, so R5 could not fail
whatever an answer cited. The lookup is now restored. `declared_names` reads
every full name the Lean development declares -- the build tree
`src/lean/RequestProject/GLM` as `reasoning/lean_address.py` parses it, 9,341
declarations when this was taken; the files held in `src/lean/awaiting_recovery/`
are not part of the development -- and `cited_theorems` reads the cited names
with the name pattern allowing Lean's prime and applies amendment R5′ against
those declarations, so a cited name the development does not declare is
counted against R5. `tests/test_evidence_model.py` checks this through the
adapter: an invented name is cited and not declared, a declared name read out
of a `repr` loses the closing quote, a declared primed name keeps its prime,
and an undeclared citation fails R5.

The census, over the 227 questions the evaluation holds now (four more than
on 20 October), with column 3 replayed:

| field | the re-take |
|---|---|
| surface | planner and grammar 226, toolbox 1 |
| status | answered 174, open 5, contradicted 3, refused 45 |
| evidence | register 78, self-report 69, lattice 44, computation 28, corpus 7, tool 1 |
| boundary | certified 173, checkable 5, refused 48, uncertified 1 |
| candidates | 23 results carry a candidate set |
| theorems | 24 results cite a `GLM.` name (10 `locate`, 7 `nearest`, 3 `hole`, 2 `carrier`, 1 `field`, 1 `ordering`); 21 distinct names, none undeclared |
| witness | 178 results carry witness values |
| budget | 848 solution steps in all |

| mark | the re-take | met |
|---|---|---|
| **R1** | 227 results, no exception | met |
| **R2** | status agrees with the evaluation on all 227; the solved flag alone disagrees on 2 (`meaning-open-vocabulary`, `compare-equality`) | met |
| **R3** | 48 of 48 refused or contradicted results name a reason | met |
| **R4** | 0 of 179 answered or open results unclassified | met |
| **R5** | 21 names cited, 0 undeclared among the 9,341 declarations (R5′ applied in the adapter) | met |
| **R6** | 173 replayable, 173 of 173 verified | met |
| **R7** | 5 of 5 open ties carry candidates and ambiguity; 8 of 8 questions with `given` replies carry one history entry per reply | met |
| **R8** | `golay code`, `tier 0` and `register` answered with boundary `corpus:strong`, `leech lattice` with `corpus:weak`, each with a witness address; `yalog` refused with its reason; the tie opens on `physics:absorptance` and `physics:albedo`, and the reply `no` leaves `physics:albedo` with one history entry | met |
| **R9** | 227 of 227 expose all ten fields | met |

**9 of 9 marks.** The re-take cites fewer names than the record (21 against
50, in 24 results against 29). The record's list of names is not in the
upload, so which citations went cannot be said name by name; the answers that
cite Lean names now are the `locate`, `nearest`, `hole`, `carrier`, `field`
and `ordering` answers counted above, several of them from modules rebuilt
after the reorganisation. The six answered results without a replay are the
four `describe` answers, the numeral-arithmetic description and the toolbox's
Leech-norm answer, as in the record.

*Re-taken 1 November 2026 (Phase 186), over the 237 questions the evaluation
holds since the intake items were absorbed (ten more).* 237 results, no
exception. Surface: planner and grammar 229, toolbox 8 (1 before). Status:
answered 182, contradicted 3, open 5, refused 47. Evidence: register 78,
self-report 69, lattice 44, computation 31, corpus 7, tool 8. Boundary:
certified 174, checkable 5, refused 50, uncertified 8 (1 before). Column 3
replayed 174 of the 187 answers, all 174 verified. 23 names cited, none
undeclared among the 9,400 declarations; the solved flag alone still disagrees
with the evaluation on 2. **9 of 9 marks**, as before.

## In one paragraph

Yes, after two repairs the census itself found. All 223 evaluation questions read into the ten fields; the model's status agrees with the evaluation on all of them, where the surfaces' own solved flag alone disagrees on two; every refusal names its reason. The first take missed two marks: 26 cited theorem names did not resolve, all of them a Python repr's closing quote read as a prime (an extractor artefact, amended), and two answers' own column 3 did not reproduce them — the trilinear template could not replay a triple of axis labels and the language report's column 3 had drifted behind its report. Both were real defects of the replay, fixed; on the re-take every one of the 171 replayable answers verifies. Re-taken on 31 October 2026 on the reconstructed model, with the Lean declaration lookup restored so that every cited name is checked against the declarations of the build tree, over the 227 questions the evaluation now holds: 9 of 9 marks again (§7.6).

The figures: Phase 169 record (20 October 2026): 9 of 9 marks on the re-take (7 of 9 on the first: R5 and R6 missed); 171 of 171 column-3 replays verified (169 of 171 first); 50 cited theorem names, all declared; status: 172 answered, 5 open, 3 contradicted, 43 refused; boundary: 171 certified, 5 checkable, 46 refused, 1 uncertified. Re-taken 31 October 2026 on the reconstructed model (§7.6): 9 of 9 marks; 173 of 173 replays verified; 21 cited names, none undeclared among the 9,341 declarations of the build tree; status: 174 answered, 5 open, 3 contradicted, 45 refused; boundary: 173 certified, 5 checkable, 48 refused, 1 uncertified.
