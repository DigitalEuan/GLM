# The address read — a ladder carrier read by its address, under the placement guard

## Tier 0 — the coarse read

**Question.** Can the GLM answer a question by reading a carrier off the construction ladder by its address — a point in, a named carrier out — with every answer certified by the placement guard from a stored table kept beside the digest of the carriers it came from, without changing any answer the evaluation already pins?

**Verdict.** Yes. A new query kind, `locate`, reads a carrier off the construction ladder by its address and answers only under the placement guard, from a stored table that refuses to load when any of its three digests fails. On the four sets of Phase 129 it answers exactly what the measurement-only read answered, query by query (445, 402, 393 and 402 correct, 0 wrong); on a fifth set generated after the pre-registration it answers 402 and refuses 166 with 0 wrong, where the unguarded ladder answers 4 wrongly; every one of its 2,169 answers is the strictly nearest carrier by a full scan, with its margin honest and its origin certified; all twelve tamperings of the table are refused; and the evaluation's earlier cases keep their verdicts.

**Deciding figure.** 10 of 10 marks (L1, A1, A2, A3, A4, O1, C1, T1, Q1, W1); correct/wrong 445/0, 402/0, 393/0, 402/0 on the four sets and 402/0 on the fifth (unguarded ladder 433/4); clean set 125 answered, 0 wrong, 17 refused, 15 of them exact duplicate carriers; 12 of 12 tamperings refused; 0 of 195 evaluation cases read as `locate` other than the 7 new ones.

**Recomputed by.** `glm_universal.reasoning.address_read_study.address_read_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration** for Phase 143, committed with its Lean file and before
the module that takes the measurement exists. §§0–6 are as they were
committed; §7 is what came out.

It takes item 1 of [`STATUS.md`](../STATUS.md) §2.1, *the placement guard in
the answering path* (left by Phase 129,
[`PLACEMENT_GUARD_STUDY.md`](PLACEMENT_GUARD_STUDY.md) §7.4), at the step the
item's own correction names first. Phase 130 found that no module a query
loads imports the ladder the guard protects
([`COUNTER_LASSO_STUDY.md`](COUNTER_LASSO_STUDY.md) §0): `ladder_escalation`,
`cell_guard` and `placement_guard` are reached only from `tools.py` and other
measurement modules, so there was no answering path to put the guard into.
Phase 134's `carrier` kind reads a 24-bit Golay word and is the pattern to
follow ([`PROTECTED_TAG_STUDY.md`](PROTECTED_TAG_STUDY.md) §7.5). This round
builds that answering path — a query kind, `locate`, that reads a carrier by
its address — and builds it **guarded from the first line**: there is no
unguarded reading of the ladder for a question to reach, so nothing pinned
moves, and the frozen-path comparison the item asks for is the evaluation's
own (mark F1).

It is a wiring round in the sense the owner asked for: the ladder, the cell
guard and the placement guard stop being measurement-only and become a
faculty a question reaches, and the census of unreached modules
(`tool wiring`) says so (mark W1).

**Order of work, stated plainly.**

1. *What was known before this was written.* Everything in
   [`PLACEMENT_GUARD_STUDY.md`](PLACEMENT_GUARD_STUDY.md) §7, in particular
   the placement-guarded ladder's 445, 402, 393 and 402 correct and 0 wrong on
   the four sets, middle-out order. The stored indices take about 45 s to
   compute (31 s for the eleven rungs' cells, 13 s for the radii, measured
   while planning this round), so a query cannot compute them and a stored
   table is required. The 142 carriers' names hold two collisions, `water`
   (molecules, lexicon) and `acceleration` (physics, lexicon), seen while
   writing the grammar. While reading the wiring census for W1, it was
   found to fail **before this round**: Phase 142's `quadratic_lasso` is
   neither reached nor declared. That is fixed in this round (§2.5) and
   recorded here rather than folded in silently.
2. *The Lean file before this was committed.*
   `RequestProject/GLM/AddressRead.lean` was written and built first (§1).
3. **No code of the read existed, no query of the fifth set (§4) had been
   generated, and no question of the battery (§3.2) had been read when this
   was committed.**

## 1. What is proved before any code

`RequestProject/GLM/AddressRead.lean`, no `sorry`, standard axioms only, on
top of `RequestProject/GLM/PlacementGuard.lean`. It states the read the query
kind performs — a stored table giving each rung and point at most one entry
(a cell centre, the one carrier the cell holds, a radius), walked in a list,
answering at the first rung whose guard holds:

* `read_strict_nearest` — on a sound table (every stored radius at most the
  distance from the centre to every other carrier), an answer is the strictly
  nearest carrier;
* `read_agrees_with_scan` — it is the carrier a full scan finds, whenever the
  scan finds a strictly nearest one;
* `read_order_independent` — two visiting orders that both answer agree;
* `entry_unique_in_ball`, `read_unique_in_ball` — the **certificate an answer
  carries**: with `D = ρ − |q − p|`, the answer is within `D` of the query and
  *no other carrier is*;
* `read_origin` — if the query is a carrier `c_t` moved by at most `δ`, and
  `δ + |q − p| < ρ` at the answering rung, the answer is `t`: a stated bound
  on the move turns a certified-nearest answer into a certified-correct one;
* `margin_lower` — the rational lower bound reported for `D` never overstates
  it;
* `read_none_iff` — the read refuses exactly when no rung's guard holds.

As in Phases 128 and 129 the theorems do not say an answer is the carrier a
query was *made from*; they say it is the nearest one, and — `read_origin` —
when the move is short enough, that the two coincide.

## 2. The rule

### 2.1 The stored table

For the ladder Phase 123 left (`8C 8A 4C 2C 2A C A 2D A/2 D12^2 Z`, the
ladder of [`PLACEMENT_GUARD_STUDY.md`](PLACEMENT_GUARD_STUDY.md)) and the 142
carriers of `ladder_escalation.sample_carriers`, store for every rung every
occupied cell: a cell holding one carrier `i` with `ρ²_p` exactly as Phase 129
defined it, a cell holding several carriers with their indices. The table is
written to `reasoning/_data/address_table.json` with three digests: of the
carriers (names and exact coordinates), of the sources the cells depend on
(the quantisers and the module), and of the table's own content. A read uses
the table only when all three hold against what is live; otherwise it refuses
`stale-table` and names the command that re-takes it
(`tools address-table --write`). This is the second half of the item: the
per-cell radius table kept beside the digest of the carriers it came from
(D4).

### 2.2 The read

A query point `q` (24 exact rationals) is quantised at each rung in the
middle-out order; at the first rung whose cell holds exactly one carrier `i`
and whose placement guard holds — `|q − c_i| + |q − p| < ρ_p`, decided
exactly by `sqrt_add_lt_sqrt_iff` — the read answers `i`. Otherwise it refuses
`no-certified-rung`, listing for every rung whether the cell was empty, shared
or failed the guard, and naming the carrier the unguarded ladder would have
named, marked *uncertified*.

An answer reports the rung, the margin `D` as an exact rational lower bound
(`margin_lower`, three decimal places), and — when the request states how far
the point was moved — whether `read_origin` certifies the origin.

### 2.3 The question

`locate` is a start-only keyword (like `carrier`, an ordinary noun elsewhere):

```
locate <ref>                                   the carrier itself
locate <ref> moved <s> by <m> [word <k>]        Phase 127's declared move
locate <c1>, <c2>, ..., <c24> [within <d>]      a point, and a bound on its move
<ref> := <name> | <register>:<name>
```

`moved s by m word k` applies `ladder_escalation.perturb` (codeword `k`,
default the carrier's index among the 142) and makes the move's length known
exactly, `δ² = s·m²`; `within d` states `δ = d`. A name that two registers
share is refused `ambiguous-name` with both readings; a name outside the 142
`unknown-name`; a point of the wrong length `dimension`; anything unread
`malformed`.

### 2.4 Column 3

The script does not use the table or the ladder: it rebuilds the point from
the request, measures it against all 142 carriers, and requires the answered
carrier to be strictly nearest, inside the reported margin, and every other
carrier outside it.

### 2.5 The census

`placement_guard` and `cell_guard` leave the census's measurement-only list,
since a question now reaches them; so does `norm256_hex`, which the guard
imports for its quantisers. `quadratic_lasso` (Phase 142) is declared, with
the reason its siblings carry, and so is this round's own measurement module,
`address_read_study`.

## 3. The sets and the questions, declared here

### 3.1 The fifth query set

The same 142 carriers; four perturbations used by no earlier round, applied
with `ladder_escalation.perturb` to carrier `i` with codeword index `i + 512`:

| support | magnitude | squared length |
|---|---|---|
| 16 coordinates | 1/4 | 1 |
| 6 coordinates | 1 | 6 |
| 24 coordinates | 1/2 | 6 |
| 3 coordinates | 3/2 | 27/4 |

568 queries, generated and read once, after this document is committed. The
**clean set** is the 142 carriers themselves.

### 3.2 The question battery

Seventeen questions, counted: seven whose outcome the rule fixes and ten
reads.

| # | question | declared |
|---|---|---|
| R1 | `locate water` | refused `ambiguous-name`, naming molecules and lexicon |
| R2 | `locate Fe` | refused `unknown-name` (iron is not among the 142) |
| R3 | `locate xyz:C` | refused `unknown-name` |
| R4 | `locate 1, 2, 3` | refused `dimension` |
| R5 | `locate C moved 30 by 1/2` | refused `malformed` (support past 24) |
| R6 | `locate C moved 8 by x` | refused `malformed` |
| R7 | `locate C please` | refused `malformed` |
| B1 | `locate C` | answered, `C`, predicted |
| B2 | `locate molecules:water` | answered, `water` (molecules), predicted |
| B3 | `locate lexicon:water` | answered, `water` (lexicon), predicted |
| B4 | `locate C moved 8 by 1/2` | read; outcome not predicted |
| B5 | `locate energy moved 24 by 1/4` | answered, `energy`, predicted |
| B6 | `locate perfect_fifth moved 2 by 2` | read; outcome not predicted |
| B7 | `locate physics:acceleration moved 8 by 1/4 word 7` | answered, `acceleration` (physics), predicted |
| B8 | `locate golay_codeword_1 moved 4 by 3/2` | read; outcome not predicted |
| B9 | `locate` with 24 zeros | read; outcome not predicted |
| B10 | `locate 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 within 1/2` (the carrier `golay_codeword_1`) | answered, `golay_codeword_1`, origin certified, predicted |

## 4. The marks, declared before the code

| mark | statement |
|---|---|
| **L1** | `RequestProject/GLM/AddressRead.lean` builds with no `sorry` and the standard axioms only, with the theorems of §1. |
| **A1** | *The answering path is the measurement.* On the four sets of Phase 129 (2,272 queries), the read the query kind calls names, query by query, exactly the carrier the placement-guarded ladder of `placement_guard.read_set` names in the middle-out order — so 445, 402, 393 and 402 correct and 0 wrong. |
| **A2** | *Certified nearest, by scan.* On the four sets, the fifth set and the clean set, every answer is the strictly nearest carrier by a full scan, and no other carrier lies within the reported margin. |
| **A3** | *Blind.* On the fifth set (§3.1), the read answers 0 queries with a carrier other than the one the query was made from. |
| **A4** | *Order.* On every set read, the middle-out, coarse-to-fine and fine-to-coarse reads agree query by query. |
| **O1** | *Origin.* On every set read, every answer whose known move `δ` satisfies `δ + |q − p| < ρ` names the carrier the query was made from. |
| **C1** | *Clean.* On the clean set, no carrier is read as another. |
| **T1** | *The table and its digest.* Each of twelve declared tamperings — a radius raised, a radius lowered, a single carrier swapped for another, a cell centre moved, a single-carrier entry deleted, an entry added, a carrier's coordinate moved in the live register, the source digest altered, the carrier digest altered, the ladder reordered, the file truncated, the file absent — makes the read refuse `stale-table`; none is answered. |
| **Q1** | *The questions.* Through the session, R1–R7 come out as declared (7 of 7); every one of B1–B10 either answers the scan's strictly nearest carrier or refuses, and B1, B2, B3, B5, B7 and B10 come out as predicted (6 of 6); every answered question's column-3 script verifies, and changing the answered carrier or overstating the margin in its expectation is rejected. |
| **W1** | *Wiring and the frozen path.* The census passes (no undeclared module, no stale declaration) with `placement_guard`, `cell_guard` and `norm256_hex` reached; no case of the evaluation is read as `locate`; and the end-to-end evaluation passes with the earlier cases' verdicts unchanged. |

**Predictions.** L1, A1, A2, A4, C1 and T1 are predicted to hold (A2, A4 and
C1 by theorem, A1 by construction, T1 by the digest). A3 is uncertain: the
guard is certified-nearest, not certified-correct, and the fifth set's moves of
squared length 6 and 27/4 are of the order of the longest earlier ones (8 and
9 in the third and fourth sets). O1 holds by
theorem; how many answers it covers is not predicted. Q1's predicted reads
are predicted with moderate confidence (the clean carriers are predicted to
pass their own guard at some rung). W1 is predicted to hold.

## 5. What this round does not do

* It does not route any existing question through the ladder: the
  escalation reports, the `nearest` kind and the evaluation's pinned cases
  read what they read before. Those are the *ladder's readings in the
  answering path* Phase 129 named, and with this kind in place the remaining
  step of item 1 is to give them the guarded read under a frozen-path
  comparison.
* It does not grow the register: the table covers the 142 carriers of the
  declared sample, and a register that grows must re-take it.
* It does not choose a ladder: the read uses the ladder Phase 129 measured.

## 6. Files

| file | what |
|---|---|
| `RequestProject/GLM/AddressRead.lean` | §1 |
| `glm_universal/reasoning/address_read.py` | the table, its digests, the read, the request grammar; `tools address-table --write` re-takes the table |
| `glm_universal/reasoning/address_read_study.py` | the fifth set, the tamperings, the battery, the marks, `address_read_report` |
| `glm_universal/runtime/session.py`, `runtime/parser.py` | the `locate` kind |
| `glm_universal/runtime/tct_engine.py` | the `locate` template of column 3 |
| `glm_universal/runtime/toolbox.py` | the census's declarations (§2.5) |
| `glm_universal/tests/test_address_read.py` | the marks |
| `python3 -m glm_universal.tools address-read` | the measurement; `--write` re-takes it |

## 7. What came out

Measured by `python3 -m glm_universal.tools address-read --write` after §§0–6
were committed, and stored in `reasoning/_data/address_read_study.json` beside
the digest of every module it depends on. Nothing in §§0–6 was changed after
the measurement.

### 7.1 The four sets of Phase 129 (A1)

| set | queries | correct | wrong | refused | disagreements with `read_set` |
|---|---|---|---|---|---|
| standard | 568 | 445 | 0 | 123 | 0 |
| held_out | 568 | 402 | 0 | 166 | 0 |
| third | 568 | 393 | 0 | 175 | 0 |
| fourth | 568 | 402 | 0 | 166 | 0 |

The answering path is the measurement: query by query it names the carrier the
placement-guarded ladder of Phase 129 names, so 445, 402, 393 and 402 correct
and 0 wrong. **A1 met.**

### 7.2 The fifth set (A3) and the clean set (C1)

The fifth set (§3.1, offset 512) was generated after the pre-registration and
read once. The read answers 402, refuses 166 and answers 0 wrongly. **A3
met** — the uncertain mark. Read post hoc, beside it: the unguarded ladder
answers 433 correctly and 4 wrongly; nearest-carrier-alone, with no guard,
answers 492 correctly, 16 wrongly and meets 60 ties; the cell guard of Phase
127 with its packing radius answers 14, all correct. The placement guard is
what turns the fifth set's four wrong answers into refusals at a cost of 31
correct ones.

On the clean set — the 142 carriers themselves — the read answers 125, 0
wrongly, and refuses 17. **C1 met.** The refusals are the finding of the round
that was not predicted (§4 predicted every clean carrier would pass its own
guard at some rung): 15 of the 17 are carriers whose exact coordinates are
another carrier's — `filled_*` (eight of them), `acoustic_absorption`,
`intensity_level` and `power_level`, `absorptance` and `albedo`, and
`golay_codeword_0` and `hexacode_word_0` — so their radius is 0 at every rung
and no read can name one of them over the other. The other 2,
`high_denominator_2x3` and `rational_root_thirds`, are distinct carriers that
share a cell at all eleven rungs. Refusing them is the guard doing what the
Lean file says it does; it is a property of the registers, not of the read,
and is recorded as a To-Do for the registers.

### 7.3 Certified nearest, order and origin (A2, A4, O1)

Over all six sets (3,550 queries, 2,169 answers): 0 answers that are not the
strictly nearest carrier by full scan, 0 margin violations, 0 queries on which
the middle-out, coarse-to-fine and fine-to-coarse orders disagree, and 0
origin violations, with the origin certified on all 2,169 answers. **A2, A4 and
O1 met**, as the theorems `read_strict_nearest`, `read_order_independent` and
`read_origin` say they must.

*Correction (Phase 148): the six sets hold 2,982 queries (142 + 5 × 568), as
the stored measurement counts them; "3,550" above was a mis-sum. The 2,169
answers and every zero are unchanged
([`NEAREST_ADDRESS_STUDY.md`](NEAREST_ADDRESS_STUDY.md) §7.2).*

### 7.4 The table and its digest (T1)

All 12 declared tamperings make the read refuse `stale-table`; none is
answered, and the intact table loads. **T1 met** (12 of 12).

### 7.5 The questions (Q1)

R1–R7 come out as declared, 7 of 7. B1, B2, B3, B5, B7 and B10 come out as
predicted, 6 of 6. Of the four reads whose outcome was not predicted, B4
(`locate C moved 8 by 1/2`) is answered `C` at the second rung, and B6, B8 and
B9 are refused because no rung certifies them; all ten reads are sound (the
scan's strictly nearest carrier or a refusal), 10 of 10. All 7 answered
questions' column-3 scripts verify, and all 14 mutants (the answered carrier
changed, the margin overstated) are rejected. **Q1 met.**

### 7.6 Wiring and the frozen path (W1)

The tool census passes: 165 of 184 tools reached, 0 undeclared, 0 stale, with
`placement_guard`, `cell_guard` and `norm256_hex` now reached from the
answering path and removed from the measurement-only list. No earlier case of
the evaluation is diverted to `locate`. The evaluation passes 195 of 195; the
frozen-path comparison finds all 178 baseline cases present with the same
status, and the texts that moved are the declared ones (the language report's
count of answerable kinds rises from 24 to 25; the query-escalation report
counts the new cases). **W1 met.**

Taking W1 found a defect of this round before it was recorded: the first
version of `reasoning/address_table.py` imported `hashlib` directly, which the
blueprint audit's reading of the Universal Binary Principle counts against the
core, and the blueprint report moved from 26 to 25 confirmed claims. The
digests are now taken through `integrity.sha256_hex` — the same SHA-256, so
the stored table is unchanged apart from its source digest — and the
blueprint report is back to its baseline text.

### 7.7 Verdict

L1 holds: `RequestProject/GLM/AddressRead.lean` builds with no `sorry` and the
standard axioms only. With the nine measured marks, 10 of 10 marks are met.

Yes. A new query kind, `locate`, reads a carrier off the construction ladder by its address and answers only under the placement guard, from a stored table that refuses to load when any of its three digests fails. On the four sets of Phase 129 it answers exactly what the measurement-only read answered, query by query (445, 402, 393 and 402 correct, 0 wrong); on a fifth set generated after the pre-registration it answers 402 and refuses 166 with 0 wrong, where the unguarded ladder answers 4 wrongly; every one of its 2,169 answers is the strictly nearest carrier by a full scan, with its margin honest and its origin certified; all twelve tamperings of the table are refused; and the evaluation's earlier cases keep their verdicts.

What remains of item 1 of `STATUS.md` §2.1 is §5's first bullet: the
escalation reports, the `nearest` kind and the evaluation's pinned cases still
read what they read before, and giving them the guarded read under a
frozen-path comparison is the next step.
