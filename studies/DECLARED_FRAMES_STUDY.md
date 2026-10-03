# Frames from a declaration: the stepwise planner's folds generated from one table, and the widenings written as entries in it

## Tier 0 — the coarse read

**Question.** Can the stepwise planner's fold frames be generated from a declaration rather than written by hand, and can the widenings the last two rounds left be added as entries in that declaration without answering anything wrongly?

**Verdict.** Yes: the stepwise planner's fold frames are now generated from one declaration and read every text of rounds one to five and of the router's declared sets exactly as the hand-written readers did, and the widenings rounds three and four left — further order statistics, superlatives and the top k, bounds through a declared physical range, the present-rows parity count, the metals and the rare earths, the remaining exact SI prefixes and the comparatives over the molecule table — are entries in that declaration, with every declared case as declared and 0 wrong.

**Deciding figure.** 638 of 638 texts read alike by the generated and the hand-written readers; 54 of 54 declared questions (12 order, 12 superlative, 12 bound, 6 class, 6 prefix, 6 molecule) and 2 of 2 follow-ups as declared, 0 wrong, where round four's reader answers 0 of the 54 and the whole machine answered 5 of them before the round and 41 after; 10 of 10 bounded answers hold over every one of 200 completions with both ends attained; 41 of 41 chain scripts verified (858 of 858 steps aligned) and every mutation rejected; 3 of 3 declared moves; 9 of 9 marks met.

**Recomputed by.** `glm_universal.runtime.stepwise_five.stepwise_five_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Round 4 of the order of work ([`STATUS.md`](../STATUS.md) §3.4,
[`ROADMAP_STUDY.md`](ROADMAP_STUDY.md)) is the planner widenings: H's E6
first — *frames generated from a declaration rather than written by hand*
([`SUBSTRATE_NATIVE_COGNITION_STUDY.md`](SUBSTRATE_NATIVE_COGNITION_STUDY.md)
§8) — then what O7 and candidate 2 left
([`STEPWISE_THREE_STUDY.md`](STEPWISE_THREE_STUDY.md) §6,
[`HOLE_FOLDS_STUDY.md`](HOLE_FOLDS_STUDY.md) §6). The roadmap's reason for
the order is that every widening of Phases 73–85 was a hand-written frame;
generating the frames from a declaration first turns the remaining
widenings into declarations rather than code.

## 1. The objects

Exact throughout (D7); no digest decides a meaning (D3).

* **The frame declaration.** One table of frame entries. Each entry names
  the round that declared it, a surface template with typed slots (the fold
  word, the column, the set, a row, an ordinal or a count), the words its
  fold slot accepts and the fold each word means, which scopes it may be
  read over (the whole set, the present rows), and the tree it builds. The
  reader is generated from the table: each template is compiled with its
  slots filled from the declared vocabularies, and entries are tried in the
  declared order. The hand-written readers of rounds three and four are
  kept, unused by the live path, as the control the generated reader is
  measured against.
* **Further order statistics** (entries, not code paths): the `k`-th largest
  and `k`-th smallest value of a column over a declared set, and the lower
  and upper quartile under one declared convention — the median of the
  lower (upper) half, the middle value left out of both halves when the
  count is odd. Each is an average of order statistics at positions fixed
  by the count, so round four's rule bounds it under a hole: with `h`
  missing, the order statistic at 0-based position `k` of the completed
  column lies between the present readings at `k − h` and `k`, both
  attained. `ORDER_OUT_OF_RANGE` when `k` exceeds the set.
* **Superlatives and the top `k`.** The superlative of each declared
  comparative (*heaviest*, *lightest*, *densest*, *oldest*, *newest*) names
  the row, or the `k` rows, of a declared set first by the comparative's
  column and direction, in that order. The `k`-th and `(k + 1)`-th rows
  tying is refused `TOP_K_TIE`. Under a hole the top `k` is refused
  `COLUMN_HOLE` — a missing reading can always be filled into it — and is
  answered over the present rows when the question asks for them.
* **Bounds.** *What are the bounds on* a sum, a mean or a parity count over
  a declared set. A parity count with `h` holes in an integer column lies
  between the present count `c` and `c + h`, both attained. A sum or a mean
  with `h` holes is bounded only through a **declared physical range**
  `[L, U]` of its column: the sum lies between `S + hL` and `S + hU` (the
  mean, those over the count), both attained by filling every hole at `L`
  (`U`). A column with no declared range is refused `RANGE_UNDECLARED`. Two
  ranges are declared, each argued: the Pauling electronegativity in
  `[0, 3.98]` (the scale is positive, and fluorine's 3.98 is its largest
  value), and the first ionization energy in `[0, 24.587]` eV (an ionization
  energy is positive, and helium's is the largest of any element). Every
  present reading is checked to lie in its declared range.
* **The present-rows parity count**: *how many of S that have one have an
  odd X*, over the present rows with the missing rows named.
* **Classes the register does not hold as one value**: *the metals* — the
  union of the register's alkali, alkaline earth, transition and
  post-transition metal, lanthanide and actinide classes (the metalloids are
  not metals under this declaration) — and *the rare earths* (*rare earth
  elements*) — the lanthanides with scandium and yttrium, the IUPAC
  definition.
* **The remaining exact SI prefixes**: peta, exa, zetta, yotta, ronna and
  quetta; femto, atto, zepto, yocto, ronto and quecto — exact by the SI
  prefix definitions.
* **The declared comparatives over the molecule table**: *heavier* and
  *lighter* compare the molar mass there; a comparative with no molecule
  column (*denser*) is refused `COMPARATIVE_UNDECLARED`; one row of each
  table is refused `TABLE_MISMATCH`.

## 2. Declarations — written before any code of the round

The corpus is
[`evaluation/stepwise_five_cases.py`](../overlay/glm_universal/evaluation/stepwise_five_cases.py),
committed with this section and before any code: 12 order questions (10 to
be answered, 2 refused), 12 superlative questions (8 answered, 4 refused),
12 bound and present-count questions (9 answered, 3 refused), 6 class
questions (4 answered, 2 refused), 6 prefix questions (5 answered, 1
refused), 6 molecule questions (4 answered, 2 refused) and 2 follow-ups.
Three earlier declared verdicts are declared to move (`MOVED`): round
three's `f09` and round four's `o10` (*the metals*, refused
`SET_UNDECLARED`) and round three's `p05` (*exavolts*, refused
`UNKNOWN_UNIT`), each a refusal naming exactly a declaration this round
adds.

| mark | claim | measured by |
|---|---|---|
| **D1** | the generated reader, restricted to the entries of rounds three and four, returns exactly the readings of the hand-written readers — the same trees in the same order, or the same refusal name — on every text of the corpora of rounds one to five and of the router's declared question sets. Control: with the declaration emptied, the generated reader reads none of the fold questions of rounds three to five | `generated` |
| **D2** | every order case gets its declared verdict; 0 wrong; round four's reader (round five switched off) answers 0 of the 12 | `orders` |
| **D3** | every superlative case gets its declared verdict; 0 wrong; round four's reader answers 0 of them | `superlatives` |
| **D4** | every bound and present-count case gets its declared verdict; 0 wrong; round four's reader answers 0 of them | `bounds` |
| **D5** | every class, prefix and molecule case gets its declared verdict; 0 wrong; round four's reader answers 0 of them; and each of D2–D5's widenings is a declaration entry: with the round-five entries removed from the declaration (and nothing else switched off), every case of D2–D5 gets round four's verdict | `widenings` |
| **D6** | every bounded answer of the corpus is sound and sharp on the register: each of 200 completions of its holes (both extreme completions and 198 seeded fills — inside the declared range for a ranged sum or mean) gives a value inside the interval, and the two extreme completions give its two ends | `completions` |
| **D7** | every answered chain's column-3 script prints `VERIFIED True` in a fresh `python3 -I`, with one `ALIGNED` line per step; every mutation kind of rounds one to four is rejected | `scripts` |
| **D8** | non-interference: the corpora of rounds one to four keep every declared verdict except the three of `MOVED`, each of which gets its declared new verdict and gets its earlier one back with round five switched off; on the router's declared sets no answered verdict changes and no declared refusal becomes an answer | `interference` |
| **D9** | `RequestProject/GLM/DeclaredFrames.lean` builds with no `sorry` and standard axioms, and proves: a parity count with `h` holes lies between the present count and that plus `h`, both attained; a sum with `h` holes each in `[L, U]` lies between `S + hL` and `S + hU`, both attained, and the mean likewise over the count; the quartile positions lie inside the column and the order-statistic bound of `GLM.HoleBounds` applies at each; with a hole and no bound on it, some completion puts the hole first, which is why the top `k` under a hole is refused | Lean |

The measurement is `glm_universal.runtime.stepwise_five.stepwise_five_report`.

## 3. What was built

* [`runtime/frame_declarations.py`](../overlay/glm_universal/runtime/frame_declarations.py)
  — the declaration and the reader generated from it. `VOCABULARIES` (the
  fold words and the fold each means, by round), `FRAMES` (10 entries: 3 of
  round three, 3 of round four, 4 of round five, each a template with typed
  slots, its scopes and the builder it hands to), `SUPERLATIVES` (5),
  `RANGES` (2, each with its argument), 18 ordinals and 10 count words.
  `read(text, rounds, level)` compiles each template with its slots filled
  from the vocabularies of the rounds switched on and tries the entries in
  the declared order. The flags `GENERATED` (the live path reads through the
  generated reader; the hand-written readers of rounds three and four stay as
  the control) and `ROUND_FIVE`/`DECLARE_ROUND_FIVE` (the round-five entries
  and widenings), `emptied()` (the control of D1) and `declared_verdict()`
  (an earlier corpus's verdict, moved where `MOVED` says).
* [`runtime/declared_frames.py`](../overlay/glm_universal/runtime/declared_frames.py)
  — the sets the register does not hold as one value (`UNION_SETS`: *the
  metals*, *the rare earths*, *rare earth elements*) and the comparatives
  declared per table (`TABLE_COMPARATIVES`: over the molecule table, *heavier*
  and *lighter* by molar mass).
* [`runtime/quantity_units.py`](../overlay/glm_universal/runtime/quantity_units.py)
  — `FIFTH_PREFIXES`, the twelve remaining exact SI prefixes, read only while
  round five is on.
* [`runtime/stepwise.py`](../overlay/glm_universal/runtime/stepwise.py) —
  the generated reader hooked into the function and segment readings; the
  builders `_build_top` (superlatives and the top `k`) and `_build_bounds`;
  the comparative builder dispatching by table; and the refusals
  `ORDER_OUT_OF_RANGE`, `TOP_K_TIE`, `RANGE_UNDECLARED`, `TABLE_MISMATCH` and
  `COMPARATIVE_UNDECLARED` in the precedence list.
* [`reasoning/stepwise_script.py`](../overlay/glm_universal/reasoning/stepwise_script.py)
  — `order_positions` (the positions an order fold averages, `None` when
  the set is too small), `top_rows`, the range-aware `fold_value`, the column
  1 and 2 forms of the new folds and their readers, and in the generated
  script its own `positions`, `top_of`, set membership through the declared
  unions and the table-aware comparative, so a script re-derives every new
  answer from the register without the planner.
* [`runtime/stepwise_five.py`](../overlay/glm_universal/runtime/stepwise_five.py)
  — the measurement (`stepwise_five_report`), round four's reader and the
  hand-written readers as the controls, the completions census of D6;
  `tools stepwise-five`; `tests/test_stepwise_five.py`. The reports of rounds
  three and four read their declared verdicts through `declared_verdict`, so
  the three moved cases are measured against their new verdicts there too.
* **Wiring.** Nothing new on the question path: every new question reaches
  the stepwise planner through `GLM.py --ask` and `GLM.py --steps` as before.
  The planner's surface in `runtime/toolbox.py` now cites the new Lean file.
* [`RequestProject/GLM/DeclaredFrames.lean`](../overlay/glm_lean/RequestProject/GLM/DeclaredFrames.lean)
  — §5.

## 4. Results

Measured by `tools stepwise-five` at the close of the round.

**Can it?** Yes: the generated reader reads every text exactly as the hand-written readers did, every declared case is as declared with 0 wrong, every bounded answer lies inside every completion with both ends attained, every script is verified and every mutation rejected.

| mark | result | figure |
|---|---|---|
| **D1** | met | 638 of 638 texts (the corpora of rounds one to five and the router's declared sets) read alike by the generated reader, restricted to rounds three and four, and the hand-written readers — the same trees in the same order or the same refusal; 49 of them carry a fold. With the declaration emptied the generated reader reads 0 of the fold questions |
| **D2** | met | 12 of 12 order cases: 10 answered, among them the second largest atomic weight of the noble gases `11100879/50000`, the third smallest atomic number of the halogens `35`, the lower quartile atomic number of the noble gases `10`, and three bounded: the second largest density of the halogens `between 493/100 and 7`, the lower quartile melting point of all the elements `between 30159/100 and 577`, the lower quartile electronegativity of the transition metals `between 61/50 and 33/20` — and 2 refused (`COLUMN_HOLE`, `ORDER_OUT_OF_RANGE` for the ninth largest of six halogens); 0 wrong |
| **D3** | met | 12 of 12 superlative cases: 8 answered (among them the heaviest noble gas oganesson, the oldest helium, the three heaviest alkali metals francium, cesium, rubidium, the two densest transition metals with a recorded density osmium, iridium, the heaviest of the metals livermorium), 4 refused (`COLUMN_HOLE` for the two densest transition metals with nine densities missing, `TOP_K_TIE`, `COMPARATIVE_UNDECLARED`, `ORDER_OUT_OF_RANGE`); 0 wrong |
| **D4** | met | 12 of 12 bound and present-count cases: 9 answered, among them the mean electronegativity of the noble gases `between 4/5 and 51/14`, the total ionization energy of the actinides `between 86353/1000 and 5547/50` eV, how many of the elements have an odd year discovered `between 51 and 64`, the average atomic number of the halogens `158/3` (no hole: the bound closes) and two present-rows parity counts — and 3 refused (`COLUMN_EMPTY`, `RANGE_UNDECLARED` for density, `NOT_AN_INTEGER`); 0 wrong |
| **D5** | met | 6 of 6 class, 6 of 6 prefix and 6 of 6 molecule cases, 0 wrong: the average atomic number of the rare earths `60`, how many of the metals have an odd atomic number `47`, 12 exavolts across 4 ohms `36000000000000000000000000000000000000` watts, *which is heavier, water or ammonia* water; refused `COLUMN_HOLE`, `SET_UNDECLARED` (*the semimetals*), `UNKNOWN_UNIT` (*bigavolts*), `COMPARATIVE_UNDECLARED` (*denser* over molecules) and `TABLE_MISMATCH`. Round four's reader answers 0 of the 54 questions of D2–D5; with the round-five entries removed from the declaration and nothing else switched off, 54 of 54 get round four's verdict |
| **D6** | met | 10 of 10 bounded answers (four order statistics, two means, two sums, two parity counts) inside the interval on every one of 200 completions, the two extreme completions giving exactly its two ends |
| **D7** | met | 41 of 41 answered chains verified in a fresh `python3 -I`, 858 of 858 steps `ALIGNED`; value lie, column 1 alone, reordering, answer and read lie each 41 of 41 rejected, member lie 32 of 32, hole lie 13 of 13, unit lie 5 of 5, word lie 4 of 4 |
| **D8** | met | rounds one to four held, round four's 11 order, 8 bounded, 8 rank, 7 present-rows cases and 2 follow-ups among them; the 3 of 3 declared moves get their new verdicts (round three's `f09` `6023/91`, round four's `o10` `68`, round three's `p05` the exavolt power) and their old refusals back with round five off; on the router's 273 declared questions the stepwise layer reads 11 before and after, no row changes and no declared refusal becomes an answer |
| **D9** | met | §5 |

**In all.** 54 of 54 declared questions and 2 of 2 follow-ups as declared,
with 0 wrong answers. Two things were not met on the first full run, and both
were in the measurement, not the planner: the census helper `completed`
did not accept the bare words *max* and *min* (only `max:k`), and round
three's stitched check re-asked the moved case `p05`, whose stitched form
reads `current` exactly as the volts version does. No declared case was
changed. As in rounds one to four, the corpus and the module share an author,
so this is the reach of the declared set, not an independent test (§6).

**What the whole machine gained.** Through `GLM.py --ask` the machine
answered 5 of the 54 before this round — the five molecule comparisons, by the
ordering surface — and 41 after: every new answer through the stepwise
planner and equal to its own. One of the 41 is a declared planner refusal:
*which is heavier, water or iron* is refused `TABLE_MISMATCH` by the planner
and answered by the ordering surface, as it was before the round, through its
own declared conversions (molar mass and atomic weight both in `u`). That
answer is not wrong — both readings are in unified atomic mass units — and
the two surfaces disagreeing on whether to compare across tables is recorded
in §6 rather than changed here.

**What the declaration changed.** Every widening of rounds one to four was a
hand-written frame. This round's widenings are 4 frame entries, 94
vocabulary words, 5 superlatives, 2 ranges and 12 prefixes, with two step
builders (`_build_top`, `_build_bounds`) the only new code paths; removing the
entries returns every case to round four's verdict (D5). A range is a
declaration that has to be argued: the electronegativity and ionization
energy ranges bound a mean round four had to refuse, and density, which has
no declared upper bound, is still refused by name.

**Faculty (D15).** Derive: a bound under holes is now answered for sums,
means and parity counts where a range or integrality closes it, and every
bounded answer is the smallest interval right for every completion. Refuse:
`RANGE_UNDECLARED`, `TOP_K_TIE`, `ORDER_OUT_OF_RANGE`, `TABLE_MISMATCH` and
`COMPARATIVE_UNDECLARED` each name the declaration that is missing.

## 5. Lean

`RequestProject/GLM/DeclaredFrames.lean` builds with no `sorry` and the
standard axioms only, on top of `GLM.HoleBounds`. A column is again the list
of present readings with the missing ones appended.

* `countP_append_bounds`, `countP_fill_low`, `countP_fill_high` — a count of
  readings with a property lies between the present count and that plus
  `h`, and both ends are attained; `oddCount_fill_even`,
  `oddCount_fill_odd`, `oddCount_append_bounds` — the same for integer
  readings and oddness, the fills being `0` and `1`.
* `sum_append_bounds`, `sum_fill_const` — with every missing reading in
  `[L, U]`, the sum lies between `S + hL` and `S + hU`, attained by the
  constant fills; `mean_append_bounds` — the mean likewise over the count.
* `quartilePositions_lt`, `quartile_halves`, `kthLargest_pos_lt` — the
  positions the quartiles and the `k`-th largest read lie inside the column
  (for `ORDER_OUT_OF_RANGE`, exactly when `k` does not exceed the count);
  `orderStat_bounds` — round four's bound applies at each of them.
* `top_open`, `top_drops` — a hole filled above a present reading gives it a
  larger rank than a hole filled at or below it, and a row ranked `k` drops
  out of the top `k` when one hole is filled above it: why the top `k` under
  a hole is refused.
* The noble gases' mean electronegativity: both ends of the answered
  interval are computed from the register's readings.

## 6. What this leaves

* **A held-out set nobody on the project wrote** — still candidate O's
  sharpest item.
* **Cross-table comparison.** The planner refuses one row of each table
  `TABLE_MISMATCH`; the ordering surface compares them through declared
  conversions. Which is right is a declaration to make (a molecule's molar
  mass and an element's atomic weight are in the same unit), not code.
* **Differences between molecules** (*how much heavier is water than
  ammonia*): the molecule table now has comparatives but no difference frame.
* **A nuclide register** (neutrons, isotopes): the element table holds no
  neutron column, so every such question is still refused by name.
* **One-sided ranges.** A mean is bounded only through a two-sided range; a
  density is positive but has no declared upper bound, so it stays
  `RANGE_UNDECLARED`. A one-sided range would bound one side.
* **The top `k` under a hole.** Refused whole; a row surely in (present rank
  plus holes at most `k`) could be named with the others left open.
* **The remaining named items** of the substrate study's E4 and E7 — the
  declaration makes them entries, but none is declared yet.
