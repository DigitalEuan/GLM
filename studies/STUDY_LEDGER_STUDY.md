# The study ledger — every study as one machine-readable row, and the files the documents name

## Tier 0 — the coarse read

**Question.** Can every study be read into one machine-readable row — phase, predecessors, marks, amendments, frozen path, digests, status, follow-ups — from the files alone, with nothing typed in, and can that ledger check where its sources disagree and which of the files the documents name are missing?

**Verdict.** Yes. The studies are one ledger read from the documents, the plan, the To-Do list and the stored measurements, with nothing typed in, and the ledger is also a check: it lists where those sources disagree and which file names do not resolve.

**Deciding figure.** 8 of 10 marks, 1 of 2 amended (S4′ missed); 155 studies, all with tier 0, a phase for 144; 185 predecessor edges, none later than its study; stored mark counts agreeing with their figure 7 of 10; tamper control 7 of 7; file names 4,254 in 195 documents, 142 missing at the first reading and 0 after the amended reading and the corrections.

**Recomputed by.** (hand-written argument; nothing to recompute)

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 31 October 2026. Reconstructed 31 October 2026 from the round records; the original was lost in the October 2026 reorganisation.* The original was written and measured in the Phase 161 session; its pre-registration (§§0–6) was written before the measurement, and two amendments (S4′, S10′, §3.1) were declared after the first measurement and before the second.

> **How this reconstruction was made.** From the Phase 161 record of
> [`MASTER_PLAN.md`](../MASTER_PLAN.md), the "study ledger" row of
> [`SYSTEM.md`](../SYSTEM.md), §20.35 and the study table of
> [`GLM_ACADEMIC_PAPER.md`](GLM_ACADEMIC_PAPER.md), the item *the study
> ledger, the rest* of [`STATUS.md`](../STATUS.md) §2.2, the row of
> `tests/README.md` for `test_study_ledger.py` and the handler `_study_ledger`
> of `tools.py`. The records give the count of marks met, the two amendments
> and what the round measured, but not the wording of S1–S10 nor which two of
> them were missed; §5 and §7.1 say so mark by mark. No figure appears that the
> records do not give.

## 0. What this document is

A study for Phase 161, taken from the owner's plan of 19 October 2026
(`source_material/GLM_19OCT26_1.md`, Part II.6, *create a machine-readable
study ledger*), with the owner's request of this session folded in: *check all
documents and files have actually been put into the repository*.

With 155 studies, what each one measured, which phase it belongs to, what it
built on and what it left had become readable only by reading. This round
reads all of it into one ledger, with nothing typed in: each study's own file
gives its tier 0, its phase, its links, its mark counts and missed and amended
marks; the plan gives the phases that link it; the To-Do list gives its status
and follow-ups, each section reference looked up; and the measurement cache of
its recomputing module gives the stored counts and digests.

## 1. What was built

* **`RequestProject/GLM/StudyLedger.lean`** (no `sorry`, no axioms): the
  ledger's predecessor relation — a link to a study of strictly earlier phase —
  has no cycle whatever the links are (`no_cycle`, `no_cycle_of_phase_lt`),
  and every chase back through predecessors stops (`ledgerPred_wellFounded`).
* **`glm_universal/corpus/study_ledger.py`**: `ledger()` (one row per study:
  title, tier 0, phase and its source, plan phases, predecessors, successors,
  related studies, mark counts, missed and amended marks, declared marks,
  frozen path, dates, status, follow-ups with each section reference looked
  up, the stored measurement's counts, digests and currency, the code digest),
  `ledger_json()`, `ledger_issues()`, `missing_files()`, `untracked_files()`
  and `study_ledger_report()`.
* **`tools study-ledger [--json] [--issues] [--files]`**. Nothing is stored;
  the ledger is re-read each time, so it is never stale.

## 2. The control

A **tamper control**: predecessor edges reversed in a copy of the ledger must
each be seen. Beside it, the reader's own agreement checks: the study's own
phase against the plan's, a deciding figure's mark count against the stored
measurement it names, and every follow-up reference looked up.

## 3. What is not claimed

The ledger reads; it does not judge a study's argument. A mark count in a
deciding figure is compared with the stored file, not re-measured. The
answering path cannot reach the ledger, so no answer of the GLM moves (S9).

### 3.1 The amendments (S4′, S10′)

Declared after the first measurement and before the second.

* **S4′** — a rule to explain the differences between a deciding figure's mark
  count and the stored measurement it names (a declared mark the stored file
  does not hold counts as an explained difference).
* **S10′** — an amended reading of the file names the documents give. At the
  first reading 142 names were reported missing; the amended reading, with the
  corrections of §7.3, reported 0.

## 4. Faculties

None of derivation, addressing or refusal moved for the GLM's answers (S9: the
answering path cannot reach the ledger). For the corpus the round added a check
that refuses a file name that does not resolve.

## 5. The marks

The wording of S1–S10 is lost. What the records attach to a mark is given;
where they attach nothing, the row says so.

| mark | what the records attach to it |
|---|---|
| **L1** | `StudyLedger.lean` builds with no `sorry` and no axioms |
| **S1**–**S3** | not recorded |
| **S4** | the deciding figures' mark counts against the stored measurements (the subject of its amendment S4′) |
| **S5**–**S8** | not recorded |
| **S9** | the answering path cannot reach the ledger |
| **S10** | the file names the documents give (the subject of its amendment S10′) |
| **S4′** | every difference between a figure's count and its stored file explained by the declared rule (amended) |
| **S10′** | the file names read again by the amended reading (amended) |

## 6. How it is measured

`python3 -m glm_universal.tools study-ledger` prints the ledger's summary, the
kinds of disagreement, the tamper control, the file check and the marks;
`--json` prints the ledger, `--issues` the disagreements, `--files` the names
that do not resolve. What the round measured: studies and their tier 0; phases
and their source; the study's own phase against the plan's; stored
measurements with counts against their figures; the tamper control; follow-up
references; predecessor edges; the file names. Tests:
`tests/test_study_ledger.py` (7), run by hand: 7 of 7 passed (pytest was not
installed).

## 7. What came out

### 7.1 The marks

| mark | recorded result | outcome |
|---|---|---|
| **L1** | built with no `sorry`, no axioms | met |
| **S1**–**S3** | — | not recorded one by one |
| **S4** | 10 stored measurements with counts: 7 agree with their figure, 2 differ by the Lean mark the stored file does not hold, 1 (`COORDINATE_JUNCTION_STUDY.md`) is not explained by the reader | not recorded one by one |
| **S5**–**S8** | — | not recorded one by one |
| **S9** | the answering path cannot reach the ledger | met |
| **S10** | file names: 4,254 in 195 documents; 142 reported missing at the first reading | not recorded one by one |
| **S4′** | the deciding figures count their marks in more than one way, so the rule does not explain them | missed |
| **S10′** | 0 missing after the amended reading and the corrections | met |

**8 of 10 marks, 1 of 2 amended.** The records give the number of marks met
among S1 to S10 (eight) but do not name the two that were not. That the amendments were
declared for S4 and S10, and that their first readings were the unexplained
disagreement and the 142 missing names, suggests that the two marks not met
were S4 and S10; this is an inference, not a record.

The other measured quantities: 155 studies, all with tier 0; a phase for 144,
the study's own phase and the plan agreeing on 28 of 29; the tamper control
seen 7 of 7; 30 of 30 follow-up references resolve; 185 predecessor edges,
none later than its study.

The paper's account (§20.35) of the count comparison reads "7 of 10 agree, and
the three that do not count a mark (the Lean build) that the stored file does
not hold"; the plan's record, quoted in the table, explains two of the three
that way and leaves one unexplained.

### 7.2 What this answers

Yes. The studies are one ledger read from the documents, the plan, the To-Do list and the stored measurements, with nothing typed in, and the ledger is also a check: it lists where those sources disagree and which file names do not resolve.

A study's predecessors are the linked studies of a strictly earlier phase, so
the relation has no cycle whatever the links are (`GLM.StudyLedger.no_cycle`,
`ledgerPred_wellFounded`).

### 7.3 The files (the owner's request)

No file of this repository's own work was missing; 11 names in 7 documents did
not resolve, and stale or misleading names were corrected:
[`HIGHER_LATTICE_STUDY.md`](HIGHER_LATTICE_STUDY.md) named three test files
since merged into `test_lattice_high.py`; the paper named the iteration study
PDF without its ` (1)`; the `data_objects` and `reasoning` package READMEs
named four upstream workflow files as if they were here; three documents named
a former location, a removed module and a program's output file as files.
Phase 160's `test_fold_machine.py` ([`FOLD_MACHINE_STUDY.md`](FOLD_MACHINE_STUDY.md))
had no row in the tests README; it got one. Three files are on disk but outside
version control — `source_material/GLM-main.zip` and the two supplied PDFs,
kept out by `.gitignore` (`*.zip`, `*.pdf`) — so a clone of the repository
lacks them although many documents cite them.

**What it invalidated.** Nothing the ledger stores (it stores nothing). The new
Lean file added one query to the Lean-address sets, so the two evaluation cases
that pin exact counts (`report-relay`: 683 → 687 of 851, the gate on 58 of
1702; `report-anonymous`: 683 → 54 and 153 → 152 of 851) were re-pinned, their
claims unchanged, and the measurements that digest the case file were re-taken,
every mark as before. `nearest-question` read 7 of 8 when it was first re-taken
in parallel with `ties-ladder-frozen`, whose stored frozen path its F1 reads;
taken after it, 8 of 8. The evaluation then ran 222 of 222. The test-file
sign-off was still owed (pytest not installable).

### 7.4 What is left

* One convention for counting marks in a deciding figure, so that S4′ can be
  met: the figures count their marks in more than one way (the Lean mark with
  the measured marks, beside them, or not at all); one declared convention, or
  the stored file recording the marks taken outside it, would let S4′ be met.
* Declared marks written as lists: older studies declare marks in lists the
  reader does not see.
* Phases for 11 studies, and one disagreement (96 against 97).
* Declared dates: since D17 every file a round creates or alters is dated, and
  the ledger could read the stamps as its pre-registration and measurement
  dates.
* The file check in `corpus --check`.
* The supplied binaries in or out of history — settled by the owner on 18
  October 2026: `GLM-main.zip` and the two PDFs stay outside version control,
  as supplied ([`SOURCE_TIERS_STUDY.md`](SOURCE_TIERS_STUDY.md) §7.4).

### 7.5 State of the files at this reconstruction (31 October 2026)

The Phase 161 module was lost in the October 2026 reorganisation.
`corpus/study_ledger.py` was rebuilt on 29 October 2026 to read the study
manifests (`studies/*.yaml`) instead of the documents, and altered on 31
October 2026 to read them through the shared loader of
`corpus/study_manifest.py`, which derives each manifest from its document and
the tree (`python3 -m glm_universal.corpus.study_manifest --check` fails when a
manifest has drifted). The rebuilt `study_ledger_report()` reads today's tree,
not the round's, and checks four marks of its own (L1–L4: the ledger loads,
the graph is acyclic, every edge points to an earlier phase, the tamper
control is caught), which are not the round's S1–S10; that is why the tier-0 block above names no
recomputing function. `StudyLedger.lean` is not in the tree (recorded missing
in [`_lean_files_needed.md`](_lean_files_needed.md)); the original
`tests/test_study_ledger.py` was lost, and the test of that name now in the
tree (`src/glm_universal/tests/test_study_ledger.py`) tests the rebuilt
module.

## In one paragraph

Phase 161 reads every study into one ledger row with nothing typed in: its own
file for tier 0, phase, links and marks; the plan for the phases that link it;
the To-Do list for status and follow-ups; the stored measurement for counts and
digests. Predecessors are linked studies of a strictly earlier phase, so the
relation has no cycle (`no_cycle`). 155 studies, a phase for 144, 185 edges,
the tamper control 7 of 7, 30 of 30 follow-ups resolving. At the owner's
request the ledger looked up 4,254 file names in 195 documents: no lost file
of the repository's own work, 11 stale names corrected, and three supplied
files outside version control. A figure's mark count is still quoted, not
checked, because the figures count their marks in more than one way (S4′
missed). 8 of 10 marks, 1 of 2 amended.
