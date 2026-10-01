# Folds with a hole: the median, the ends and the rank of a column, bounded where the register is silent, and the present-rows question asked as its own

## Tier 0 — the coarse read

**Question.** What can the stepwise planner say about the median, the ends and the rank of a column when some readings are missing — and can it answer the present-rows question as its own question — without answering anything wrongly?

**Verdict.** Yes: the stepwise planner now reads the median, the largest and the smallest value and the rank of a row over every element or a declared class, answers a median or a rank over a column with holes as the exact interval every completion of the holes lands in — one value when the interval closes — refuses `COLUMN_HOLE` where the holes leave a side open, and answers the present-rows question asked as its own with the missing rows named, with every declared case as declared and 0 wrong.

**Deciding figure.** 34 of 34 declared questions (11 order, 8 bounded, 8 rank, 7 present-rows) and 2 of 2 follow-ups as declared, 0 wrong, where round three's reader answers 0 of the 34 and the whole machine answered 0 of them before the round and 25 after; 9 of 9 bounded answers hold over every one of 200 completions with both ends attained; 26 of 26 chain scripts verified (843 of 843 steps aligned) and every mutation rejected, 15 of 15 hole lies included; 8 of 8 marks met.

**Recomputed by.** `glm_universal.runtime.stepwise_four.stepwise_four_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Two rounds left the same question named. The extremum round
([`COLUMN_EXTREMUM_STUDY.md`](COLUMN_EXTREMUM_STUDY.md) §7) folded a column to
its maximum and refused every column with a hole, and said: *a rank, a median
or a top-k over the same column would each need their own statement of what a
hole does to them, and none is built*; and *of the rows that are filled in,
which is the largest?* is a different, answerable question that would have to
be asked as one. Round three of the stepwise planner
([`STEPWISE_THREE_STUDY.md`](STEPWISE_THREE_STUDY.md) §6, Phase 84) folded
sums, means and parity counts over a declared class, refused `COLUMN_HOLE`
with the missing rows named, and left *the present-rows mean asked as its own
question*. They are candidate 2 and the last item of candidate O7 of
[`STATUS.md`](../STATUS.md) §3.4, and this round takes both.

The point of the round is a difference between folds that the earlier
refusals treated alike. A hole moves a mean anywhere: one missing reading can
be anything, and so can the mean (Phase 84 proved it). A hole does **not**
move an order statistic anywhere. With `h` readings missing from a column of
`n`, the `k`-th smallest of the whole column lies between the `(k − h)`-th
and the `k`-th smallest of the rows that are present — whatever the missing
readings are — and both ends are reached by some completion. So a median can
be answered as an exact interval, a rank as a range of ranks, and sometimes
the interval closes to one value, which is then the answer the holes cannot
change. Where it does not close on one side (the largest value, with any
hole; a median with more holes than rows on one side of it), the refusal
stays, and now says why in terms of that bound.

## 1. The objects

Exact throughout (D7); no digest decides a meaning (D3); every reading rests
on a declaration, and the declared sets and columns are round three's own
([`runtime/declared_frames.py`](../overlay/glm_universal/runtime/declared_frames.py)).

* **Order folds over a declared set.** *The median (largest, highest,
  maximum, smallest, lowest, minimum) X of S* and *the median of the Xs of
  S*. The median of an even count is the mean of the two middle values (the
  declared convention); the largest and smallest are the ends of the column.
  On a column with no missing reading each is one exact value.
* **The rule for a hole** — the statement this round adds. Let the set have
  `n` rows of which `h` have no reading, and let `p₁ ≤ … ≤ p_{n−h}` be the
  readings that are present. The `k`-th smallest of the completed column
  (1-based) is at least `p_{k−h}` when `k > h` and at most `p_k` when
  `k ≤ n − h`; filling every hole below every reading attains the first and
  filling every hole above attains the second. So:
  * the **median** is answered `between A and B`, where `A` and `B` are the
    medians of those two extreme completions (for an even count, the mean of
    the two middle bounds); when `A = B` the answer is that single value;
    when either bound does not exist the median is refused `COLUMN_HOLE`,
    naming the missing rows and the side left open;
  * the **largest** is refused `COLUMN_HOLE` whenever a reading is missing
    (the upper bound never exists: `k = n > n − h`), and so is the
    **smallest** — the extremum round's refusal, now with its reason stated
    as the open side.
* **The rank of a row.** *The rank of R by X among S*: largest first, ties
  sharing the better rank, so the rank is one more than the number of
  members whose reading is strictly larger. With `h` holes the rank is
  answered `between r and r + h`, where `r` counts only the present
  readings — the holes filled below R's reading give `r`, filled above give
  `r + h` — and is one value when `h = 0`. R must be a member of S
  (`NOT_A_MEMBER` otherwise) and must hold a reading (`VALUE_MISSING`).
* **The present-rows question, asked as that question.** A declared set
  followed by *that have one*, *that have a recorded X* or *with a recorded
  X* names the members that hold a reading of the fold's column. Every fold
  of rounds three and four (sum, mean, parity counts, median, largest,
  smallest, rank) is then taken over those rows exactly, and the answer step
  **names the missing rows** — its column 1 lists them. It is a different
  question from the column's, with a true answer; nothing in it is claimed of
  the rows that are missing. A present-rows question over a set in which no
  member holds a reading is refused `COLUMN_EMPTY`.
* **Three columns.** Every new fold is a `fold` step: one looked-up step per
  input, then the fold, with a declared column-1 template and column-2
  equation that the chain's column-3 script reads back with its own readers.
  For a present-rows or bounded fold the script re-derives from the register
  both the members of the set and which of them are missing, requires the
  inputs to be exactly the present members' readings in the register's order
  and the recorded missing rows to be exactly the missing members, and
  recomputes the fold — for a bounded fold, both bounds by the rule above.

## 2. Declarations — written before any code of the round

The corpus is
[`evaluation/stepwise_four_cases.py`](../overlay/glm_universal/evaluation/stepwise_four_cases.py),
committed with this section and before any code: 11 order questions (8 to be
answered, 3 refused by name), 8 bounded questions (6 answered — two of them
closing to one value — and 2 refused), 8 rank questions (5 answered, 3
refused), 7 present-rows questions (6 answered, 1 refused) and 2 follow-ups.

| mark | claim | measured by |
|---|---|---|
| **H1** | every order case gets its declared verdict; 0 wrong. Control: round three's reader (round four switched off) answers 0 of the 11 | `orders` |
| **H2** | every bounded case gets its declared verdict; 0 wrong; round three's reader answers 0 of them | `bounded` |
| **H3** | every rank case gets its declared verdict; 0 wrong; round three's reader answers 0 of them | `ranks` |
| **H4** | every present-rows case gets its declared verdict; 0 wrong; every answered present-rows chain names in its fold step exactly the members the register records as missing; round three's reader answers 0 of the 7 | `present` |
| **H5** | the rule is sound and sharp on the register: for every answered bounded median or rank, each of 200 completions of its holes (the two extreme completions and 198 seeded fills drawn from a range wider than the present readings) gives a value inside the interval, and the two extreme completions give its two ends; for every `COLUMN_HOLE` order refusal of this corpus, the two extreme completions (holes a million below the smallest reading, then a million above the largest) move the value by at least a million | `completions` |
| **H6** | every answered chain's column-3 script prints `VERIFIED True` in a fresh `python3 -I`, with one `ALIGNED` line per step; rounds one to three's eight mutation kinds are all rejected, and so is one more: `hole-lie` (a present-rows or bounded fold's recorded missing rows short of one, re-rendered to agree) | `scripts` |
| **H7** | non-interference: round three's corpus keeps every verdict (marks V1–V5 as measured without scripts), rounds one and two's likewise through it, and on the router's declared sets no answered verdict changes and no declared refusal becomes an answer | `interference` |
| **H8** | `RequestProject/GLM/HoleBounds.lean` builds with no `sorry` and standard axioms, and proves: the `k`-th smallest of a list is at most `v` exactly when more than `k` of its readings are at most `v`; with the holes appended, the `k`-th smallest lies between the `(k − h)`-th and the `k`-th smallest of the present readings, and each bound is attained by the completion that fills every hole below (above) it; with `k < h`, or `k` past the present readings, a completion puts the `k`-th smallest at any value below (above) every reading, which is why an open side is refused; the rank of a row with `h` holes lies between its present rank and that plus `h`, both attained | Lean |

The measurement is `glm_universal.runtime.stepwise_four.stepwise_four_report`.

## 3. What was built

* [`runtime/stepwise.py`](../overlay/glm_universal/runtime/stepwise.py) —
  behind `ROUND_FOUR` (read only while rounds two and three are on): the
  order words (`_ORDER_WORDS`: *median*, *largest*, *highest*, *maximum*,
  *greatest*, *smallest*, *lowest*, *minimum*), the present-rows phrases
  (`_present_split`: *that have one*, *that have a reading*, *that have a
  recorded X*, *with a recorded X*; a recorded column other than the fold's
  is refused, not guessed), the rank frame, and the step builder
  `_build_fold4`, with the two new refusals `NOT_A_MEMBER` and
  `COLUMN_EMPTY` in the precedence list beside `COLUMN_HOLE`.
* [`reasoning/stepwise_script.py`](../overlay/glm_universal/reasoning/stepwise_script.py)
  — `fold_value`, the rule of §1 over the present readings and a count of
  holes; the column-1 and column-2 forms of the new folds (the missing rows
  in column 1 for a present-rows or bounded fold, the ranked row, the holes
  in column 2); the readers of both columns, in the module and in the
  generated script; the script's own `order_fold`, which re-derives the
  class, the missing members and the present inputs from the register before
  it recomputes; and the mutation `hole-lie`.
* [`runtime/stepwise_four.py`](../overlay/glm_universal/runtime/stepwise_four.py)
  — the measurement (`stepwise_four_report`), round three's reader as the
  control, and the completions census of H5; `tools stepwise-four`;
  `tests/test_stepwise_four.py`.
* **Wiring.** Nothing new on the question path: the router already hands a
  planner refusal to the stepwise planner, so every new question is
  reachable from `GLM.py --ask` and `GLM.py --steps`. The planner's surface
  in `runtime/toolbox.py` now cites the new Lean file.
* [`RequestProject/GLM/HoleBounds.lean`](../overlay/glm_lean/RequestProject/GLM/HoleBounds.lean)
  — §5.

## 4. Results

Measured by `tools stepwise-four` at the close of the round.

**Can it?** Yes: every declared case as declared, 0 wrong; a median or a rank over a column with holes is answered as the exact interval every completion of the holes lands in, one value when the interval closes; every bounded answer inside every completion with both ends attained, every script verified and every mutation rejected.

| mark | result | figure |
|---|---|---|
| **H1** | met | 11 of 11 order cases as declared: 8 answered (the median, the largest, the highest, the lowest and a follow-on *then is it even*), 3 refused by the declared name (`COLUMN_HOLE` twice — the smallest boiling point of the noble gases, oganesson's missing; the largest density of the transition metals, nine superheavy rows missing — and `SET_UNDECLARED`); 0 wrong. Round three's reader answers 0 of the 34 questions of the corpus |
| **H2** | met | 8 of 8 bounded cases: 6 answered — the median density of the halogens `between 1556607/1000000 and 201/50`, of melting point over all the elements `between 1091 and 266133/200`, of electronegativity over the lanthanides `between 57/50 and 123/100`, of valence electrons over the post-transition metals `between 3 and 4`, and two that close: the median valence electrons of the transition metals is `2` with four readings missing, and of all the elements `2` with ten missing — and 2 refused `COLUMN_HOLE` (five of seven noble-gas electronegativities missing; eight of fifteen actinide boiling points); 0 wrong |
| **H3** | met | 8 of 8 rank cases: 5 answered (iron 33rd by atomic weight among the transition metals, xenon 3rd by atomic number among the noble gases, gold `between 6 and 15` by density among the transition metals, osmium `between 1 and 23` by density among all the elements, iron `between 17 and 26` by electronegativity), 3 refused (`NOT_A_MEMBER`, `VALUE_MISSING`, `UNKNOWN_STEP`); 0 wrong |
| **H4** | met | 7 of 7 present-rows cases: 6 answered, 1 refused `COLUMN_EMPTY` (no alkaline earth metal holds an electron affinity in the register); 0 wrong; every one of the 6 answered chains names in its fold step exactly the members the register records as missing |
| **H5** | met | 9 of 9 bounded answers (6 medians, 3 ranks) inside the interval on every one of 200 completions, the low and the high extreme completion giving exactly its two ends; 4 of 4 `COLUMN_HOLE` order refusals move by at least a million between their extreme completions (the two ends by exactly a million, the two medians by 10,000,002/5 and 2,002,777) |
| **H6** | met | 26 of 26 answered chains verified in a fresh `python3 -I`, 843 of 843 steps `ALIGNED`; value lie, column 1 alone, reordering, answer, read lie and member lie each 26 of 26 rejected, hole lie 15 of 15 |
| **H7** | met | round three's corpus through the round-four module: 18 of 18 comparative, 6 of 6 count-noun, 6 of 6 prefix and 17 of 17 fold cases and 2 of 2 follow-ups as declared, its controls still met; rounds one and two held; on the router's 273 declared questions the stepwise layer still reads 11 and turns none into an answer |
| **H8** | met | §5 |

**In all.** 34 of 34 declared questions and 2 of 2 follow-ups as declared,
with 0 wrong answers. One thing was not met on the first run, and it was in
the reader, not the corpus: four present-rows questions came back unread,
because the planner writes the number word *one* as `1` before any frame
reads it, so *the noble gases that have one* reached round four as *… that
have 1*. The reader now accepts both; no declared case was changed. As in
rounds one to three, the corpus and the module share an author, so this is
the reach of the declared set, not an independent test (§6).

**What the whole machine gained.** Through `GLM.py --ask` the machine
answered none of the 34 before this round; after it, it answers 25 and
refuses the other 9 by name, every answer through the stepwise planner and
equal to the stepwise planner's own.

**What the rule says that the refusal did not.** Round three refused every
fold over a column with a hole. For a sum or a mean that stays right — a hole
can move them anywhere — but for an order statistic it withheld something the
register does determine. *The median number of valence electrons of the
transition metals* is `2` whatever palladium, darmstadtium, roentgenium and
copernicium turn out to hold; *osmium's rank by density among all the
elements* is somewhere from first to twenty-third, and no completion of the
22 missing densities puts it lower. Where the rule leaves a side open it says
which: the largest density of the transition metals is refused as open
above, because nothing in the register bounds the nine superheavy rows it
does not hold.

**Faculty (D15).** Derive: every answered fold computes a value no register
row holds, and every bounded one an interval over all the completions of its
holes, with one looked-up step per present reading and every step re-checked
in all three columns. Refuse: `COLUMN_HOLE` now names the side a hole leaves
open, `NOT_A_MEMBER` refuses a rank a row does not have, and `COLUMN_EMPTY` a
present-rows question with no present rows.

### 4.1 Beyond the declaration — not counted

Ten further questions, written after the module worked and so **not** a
held-out test, were run once through `GLM.py --ask`'s router. Nine were
answered and each was checked against the register by hand: 0 wrong (*the
rank of gold by atomic weight among all the elements* = 40, the 39 elements
after gold all being heavier; *the rank of fluorine by electronegativity among
all the elements* = `between 1 and 24`, fluorine holding the largest of the
95 recorded readings; *the smallest electronegativity of the elements that
have one* = 7/10; *the median density of the noble gases* = `between
17837/10000000 and 3733/1000000`; *the median year discovered of the
lanthanides* = 1879, no reading missing). One was refused: *the lowest
melting point of the transition metals*, `COLUMN_HOLE`, open below.

## 5. Lean

`RequestProject/GLM/HoleBounds.lean` builds with no `sorry` and the standard
axioms only (`propext`, `Classical.choice`, `Quot.sound`). A column is the
list of present readings with the missing ones appended; only the number of
missing readings is a fact about the register.

* `kth_le_iff` — counting: the `k`-th smallest reading is at most `v` exactly
  when more than `k` readings are at most `v`; `kth_mem` — it is one of the
  readings.
* `kth_append_le`, `le_kth_append` — the two bounds: whatever the missing
  readings are, the `k`-th smallest of the whole column lies between the
  `(k − h)`-th and the `k`-th smallest present reading.
* `kth_append_eq_low`, `kth_append_eq_high`, `kth_fill_below` — both bounds
  are attained, and one completion (every hole below every present reading)
  attains every lower bound at once: the interval answered is the smallest
  that is right for every completion.
* `kth_fill_const_low`, `kth_fill_const_high` — an open side: with `k < h`,
  or `k` past the present readings, a completion puts the `k`-th smallest at
  any value below (above) every reading, so no bound on that side holds for
  every completion — the largest value of a column with a hole is always of
  the second kind.
* `rank_append_bounds`, `rank_append_eq_low`, `rank_append_eq_high` — the rank
  of a reading, largest first, lies between its present rank and that plus
  `h`, and both ends are attained.
* `mid_bounds` — for an even count, the mean of the two middle values is
  bounded by the means of their bounds.

## 6. What this leaves

* **A held-out set nobody on the project wrote** — candidate O's sharpest
  item, and still not something the project can write for itself.
* **Top-*k* and quantiles other than the median.** The rule covers every
  order statistic, so *the three densest transition metals* (a row is surely
  in the top *k* when its present rank plus the holes is at most *k*, surely
  out when its present rank exceeds *k*) and quartiles are the same
  statement read differently; neither has a declared frame yet.
* **A mean with a declared range.** A mean has no bound under a hole because
  a reading can be anything. A declared physical range for a column (a
  density is positive; an electronegativity on the Pauling scale lies in a
  stated interval) would bound it, and would have to be argued for rather
  than looked up — the same kind of declaration as candidate 1's measurands.
* **Present-rows parity counts** (*how many of the halogens that have one
  have an odd …*) read the same fold and are not given a frame.
