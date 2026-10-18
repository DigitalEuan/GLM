# The machine reads what it carries — the registers as files, the typed planner and the field reads through GLM-BAT

## Tier 0 — the coarse read

**Question.** Can the batch machine check the values a chain carries by reading the session's registers and the question itself, and can the typed planner's computations and the session's field answers be run and gated by the same machine, without moving any answer?

**Verdict.** Yes. The machine is given its own copy of the registers (8,408 entries in 11 tables) and the question's numbers, and of the 2,314 steps Phase 151 carried as data it now reads 2,189 and computes 33 more, with 92 still carried; every answered chain is still admitted. A lie at a register read is found at its own step every time, a lie at a given whenever it is not another number of the same question, and a lie at a newly computed step every time. The typed planner's 42 exact computations and 7,716 field answers of the session's default domains run through the same machine, every honest one admitted and every altered one refused, and no answer moved. No mark was missed.

**Deciding figure.** 13 of 13 marks; 174/174 chains admitted with 2,087 register reads, 102 question reads, 213 computed and 92 carried steps; lies found at their step 121/121 (register), 54/54 (question, 3 more are other numbers of the question), 42/42 (computed); typed plans 42/42 admitted and 42/42 lies refused; field reads 7,716/7,716 admitted and 7,716/7,716 lies refused; 697/697 texts unchanged.

**Recomputed by.** `glm_universal.reasoning.carried_read_study.carried_read_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration** for Phase 153 (§§0–6, committed before the stored
measurement; §7 is what came out), item 2 of [`STATUS.md`](../STATUS.md)
§2.1 (*the operations ladder beyond the stepwise planner*, left by Phases 125
and 151, [`PLANNER_LADDER_STUDY.md`](PLANNER_LADDER_STUDY.md) §7.4). The owner
asked for this round to run more of the system through the batch machine —
the session's default domains and the typed planner — *and* to have the
machine check carried values itself, with Three Column Thinking in mind. Item
1 of §2.1 (the question at the three remaining ties) is postponed at the
owner's request until more such ties accumulate or a higher mechanism for
them is found; it stays on the To-Do list.

**What Phase 151 left.** Every chain of the stepwise planner was a GLM-BAT
program, but 2,314 of its 2,494 steps were *carried*: written into the
program as data. A lie in a carried step was invisible at its own step and
caught downstream in only 87 of 168 cases.

**What this round builds.**

* **The registers as machine files** (`reasoning/register_files.py`). Every
  declared register table — the `element` and `molecule` source tables, the
  ITS-90 fixed points, and the carrier attributes of the session's eight
  default domains — is written as `reg/<table>.txt`, one line
  `@<row>.<field>=<value>;` per scalar entry whose key and value avoid the
  delimiters and GLM-BAT's special characters. The element table is written
  from the frozen snapshot by the module's own reader, not from the loaded
  register, and compared with it entry for entry.
* **Reads instead of carries** (`reasoning/carried_read.py`, the reading
  mode of `planner_ladder.check_chain`). A `lookup` step's file is written
  only when `FIND "@row.field=value;" < reg/<table>.txt` succeeds; a `given`,
  `measured` or `literal` step's only when its value is among the question's
  own numbers in `q.txt`. `gcd`, `lcm`, `parity`, `prime` (up to `10^8`, by
  trial division in a loop), `larger`, `comparative` and the folds `even`,
  `odd`, `max`, `min` are computed. The stepwise gate (`stepwise.READ`) runs
  in this mode.
* **Number words as junctions.** The question reader identifies a declared
  list of number words with their numbers (`twice`, `double`, `half`,
  `halve`, `negate` — the stepwise grammar's own — and `triple`, `a dozen`,
  `a score`, `a quarter`, …), by the junction rule (two names are one only
  where a declared junction identifies them). Widening it is adding a row.
* **The typed planner through the machine** (`reasoning/typed_ladder.py`).
  An answered `arith`, `gcd`, `lcm`, `prime` or `convert` plan is said as a
  chain — the numbers read from the question, the operation computed — and
  refused as `MACHINE_DRIFT` if the machine disagrees.
* **The session's field answers through the machine.** A `field` answer
  whose value is a scalar of a register table is one read; the session
  refuses it if the machine does not find it.

**Three Column Thinking.** Column 3 here is GLM-BAT's second interpreter,
given the same seed files: it re-runs every program and asserts the claim.
Building the round found one disagreement between the two interpreters: a
line with two redirections (`FIND "…" < reg/x.txt > r.txt`) is read by the
machine and not by column 3's reader. The reads therefore send the found
line to the output stream — which becomes the run's read log — rather than
to a file.

**What was known before this was written.** The marks were run while the
code was built. The first run of C1 refused one chain (*…then halve it*:
the literal 2 is not written as a digit), which is why the number-word
junctions exist; the first run of T2 missed one lie (*is 1000003 prime?*,
above the first bound of `10^6`), which is why the bound is `10^8` and why
T2 counts only plans whose last step the machine computes. The baseline of
the frozen path (`reasoning/_data/carried_read_baseline.json`, 697 texts)
was taken with the round's two switches off, which restores the answering
path as Phase 152 left it. **The stored measurement had not been taken when
this was committed.**

## 1. What is proved before any code

`RequestProject/GLM/CarriedRead.lean` (namespace `GLM.CarriedRead`); no
`sorry`, standard axioms only.

* `sep_cancel` — a separator absent from both left parts splits two lists
  at the same place.
* `line_infix_iff` — with keys and values free of `@`, `=`, `;`, the needle
  `@k=v;` occurs in the line `@k'=v';` exactly when `k = k'` and `v = v'`.
* `find_iff_mem` — `FIND` finds `@k=v;` in a register file exactly when the
  register holds `(k, v)`; `find_iff_eq` — with unique keys, exactly when
  `v` is the register's value at `k`.
* `machine_honest_below`, `honest_no_drift`, `first_lie_drifts` — over a
  chain of computed steps, checked reads and unchecked carried steps: an
  honest chain never drifts, and the first lie drifts at its own step
  whether it is computed or read, with nothing before it drifting.
* `no_drift_iff` — when every step the machine does not compute is an exact
  read, no drift holds exactly when the chain is honest.

## 2. The questions

* The register tables as the session holds them.
* The 174 chains the stepwise planner answers among its 283 recorded texts
  (Phase 151's baseline).
* The corpus: those 283 texts (through the router), the typed planner's six
  sets (through `ask_planned`) and the evaluation's cases (through `ask`) —
  697 texts.
* Every written register entry asked as `field <field> of <row>`.

## 3. The marks, declared before the measurement

| mark | claim |
|---|---|
| **L1** | `CarriedRead.lean` builds with the full `lake build`, no `sorry`, standard axioms only |
| **R1** | every register table written with unique keys; the snapshot reading agrees with the loaded element register on every scalar entry |
| **R2** | per table, a GLM-BAT program finds every entry with `FIND` (exit 0), and a program with every value altered finds none |
| **C1** | every answered chain, said with reads: halts with exit 0, no drift, the gated pipeline promotes |
| **C2** | the last register read of every chain that has one, raised by one: the first drift is that step, the pipeline does not promote, the seed files are restored |
| **C3** | the same at the last question read: caught at its step whenever the altered value is not another number of the question |
| **C4** | the same at the last step the round newly computes (a verdict flipped, a row swapped, a number raised) |
| **C5** | both column-3 scripts of every chain, given the seed files, verify; the run claim with its last file altered and the pipeline claim with its promotion flipped are rejected |
| **T1** | every answered typed plan of the said kinds over the corpus is admitted |
| **T2** | every such plan whose last step the machine computes, with its claim altered, is refused |
| **S1** | every written entry asked as a field: answered; every answer from that table read by the machine and admitted |
| **S2** | each of those with its value altered is refused |
| **F1** | every baseline text asked again with the switches on: the same status and the same answer text |

## 4. What would count against

C1, T1 or S1 failing on honest data would mean a read does not read what the
planner reads (or the reader is wrong). C2, C4 or T2 failing would mean a
lie the proof says is seen is not. F1 failing would mean the gates moved an
answer.

## 5. What is not claimed

* A question read is **membership**: a lie that is another number of the
  same question is not seen (`find_iff_mem`, not `find_iff_eq`).
* What stays carried — tool answers, planner computations, the folds the
  machine does not compute (rank, median, quartiles, the k-th largest, top),
  and the steps whose inputs are verdicts — is still trusted, and counted.
* A field value that is a tuple, a mapping, or holds a special character is
  not read; the `lean`, `python` and `function` tables are not registers and
  are not given to the machine.
* The register files are the register as loaded (and, for the element
  table, as the snapshot holds it); the machine checks the planner against
  the data, not the data against the world.

## 6. Files

* `RequestProject/GLM/CarriedRead.lean` — L1.
* `glm_universal/reasoning/register_files.py`, `carried_read.py`,
  `typed_ladder.py`; the reading mode of `planner_ladder.py`; the gates in
  `runtime/stepwise.py`, `runtime/semantic_plan.py`, `runtime/session.py`.
* `glm_universal/reasoning/carried_read_study.py` — the marks;
  `python3 -m glm_universal.tools carried-read [--write] [--baseline]`.
* `glm_universal/tests/test_carried_read.py`.

## 7. What came out

`python3 -m glm_universal.tools carried-read` (stored in
`reasoning/_data/carried_read_study.json`, digest-guarded).

In short: the machine now reads almost everything the stepwise planner used
to hand it as data, and the typed planner and the session's field answers
pass through the same machine; every honest answer is admitted, every
declared lie is found where the proof says it is, and no answer moved.

### 7.1 The marks

| mark | result | met |
|---|---|---|
| **L1** | `CarriedRead.lean` builds with the full `lake build`, no `sorry`; `#print axioms` shows at most `propext`, `Classical.choice`, `Quot.sound` | yes |
| **R1** | 8,408 entries written in 11 tables (2,438 not sayable: tuples, mappings, special characters), 0 duplicated keys; the snapshot reading agrees with the loaded element register on 1,965 of 1,965 entries | yes |
| **R2** | every entry found by `FIND` and no altered entry found, in each of the 10 tables that hold an entry (`carrier:economics` holds no scalar) | yes |
| **C1** | 174 of 174 chains admitted: 2,087 register reads, 102 question reads, 213 computed steps, 92 carried (16,125 lines, 16,835 machine steps) | yes |
| **C2** | 121 of 121 lies at the last register read: the first drift is the lie, not promoted, the seed restored | yes |
| **C3** | 54 of 54 lies at the last question read caught at their step; in 3 more chains the altered value is another number of the same question, and those 3 are not seen (as declared) | yes |
| **C4** | 42 of 42 lies at the last newly computed step found at that step | yes |
| **C5** | 174 of 174 run scripts and 174 of 174 pipeline scripts verify with the seed files; 348 of 348 mutants rejected | yes |
| **T1** | of the 171 answered typed plans, 42 are of the said kinds (arith 10, convert 13, gcd 7, lcm 1, prime 11): 42 of 42 admitted | yes |
| **T2** | 42 of 42 altered claims refused (none has a carried last step) | yes |
| **S1** | 8,408 entries asked as fields, 8,408 answered; 7,716 answered from the table asked (the rest by a table of higher priority holding the same row and field), 7,716 of 7,716 read and admitted | yes |
| **S2** | 7,716 of 7,716 altered values refused | yes |
| **F1** | 697 of 697 texts — the 283 stepwise texts, the typed planner's six sets (197) and the 217 evaluation cases — the same status and the same answer text | yes |

*Re-taken at Phase 154* (the `corpus` query kind and its evaluation cases):
12 of 12 marks again. F1 now reads 697 of 697 with the same status and 661
of 697 with the same text; every one of the 36 moved texts is a declared
move — the 28 outside the evaluation set are exactly the old text with
`'corpus'` added to the refusal's list of query kinds, and the 8 evaluation
cases are moves `ties_ladder_frozen` declares (the reports the tree measures
of itself, and the same refusal list). F1 was amended at that
re-take from *the same text* to *the same text or a declared move*.

### 7.2 What is still carried

The 92 carried steps are 48 folds the machine does not compute (rank,
median, quartiles, the k-th largest, top, and the bounded folds), 31
planner computations (tool answers and one conversion), 7 axiom steps whose
inputs the machine does not hold as numbers, and 3 each of `choose` and
`first` whose inputs are verdicts. A lie at the last numeric carried step
(37 chains) is never found at its step; 5 are found downstream and 32 are
not seen.

### 7.3 What this answers

The two halves of the owner's item are done. **The machine checks carried
values itself**: a register value is no longer data the planner hands it
but an entry it finds in its own copy of the register, so a lie there is
found at its own step (`first_lie_drifts`), which Phase 151 could not do.
**More of the system runs through the machine**: the typed planner's exact
computations and every scalar field answer of the session's default domains
are now GLM-BAT programs gated by the machine, with column 3 as the second
interpreter (Three Column Thinking's check, applied to the machine's own
reads). Faculty: **refusal** — the gates add the power to withhold an answer
whose data or arithmetic disagrees with the machine; over the recorded
questions they withhold nothing, because nothing disagrees.

### 7.4 What is left

* The 92 carried steps: the remaining folds (rank, median, quartiles, top,
  the k-th largest) need a sort in GLM-BAT; tool answers need the tool's
  own computation said as GLM-BAT.
* A question read is membership; reading a given at its position in the
  question would make it exact.
* The number-word junctions are a short declared list; a junction table
  shared by the planner and the machine (so a word the planner reads is
  always a word the machine reads) would close the gap by construction.
* The plan search and the typed planner's other plan kinds (ordering,
  extremum, linear, Bezout, factorise, substrate facts) are not yet said as
  GLM-BAT.
