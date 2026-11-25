# 99 — The tilt price across the table: 508 of 554 beats carry a grain the inequality prices out (Run 142)

**Run 142, 2026-11-25.** Instruments `scripts/tilt_audit.py` (new) and ledger
`workspace/push/tilt_audit.json`. Doc 98 priced a single near-square grain in an
axis substrate and concluded that a two-grain interface cannot pay for itself;
this run applies that inequality to every delivered pose, class by class, and
asks whether the rows that beat the grid are the rows that escape it.

**Answer: they are not.** The inequality never separates the two populations. All
446 grid ties are single-class axis poses with **zero** tilted cells, so the price
has nothing to reject; and 508 of the 554 beat rows carry at least one class the
same inequality prices out — 43,144 of the 125,490 tilted cells in beating rows
sit in a class that cannot pay for its own bbox. The measured reason is that the
bbox is not the grain's own: the other lattice is inside it.

**Nothing promoted.** No candidate pose was built, so `submission.csv` and root
`WHITEBOARD.md` are untouched and the delivered total stands at
**22.217428576** / 554 beats / 446 grid ties. This run changes no side; it changes
what the standing card says the next constructor should be.

## 1. What was asked, and what was measured

The request was threefold: (a) apply doc 98's exact tilt price across the
delivered table and its orientation-class / grain-size data, extending doc 97's
`crystal_domains` analysis from 14 target rows to all 1,000; (b) compare the 554
grid-beating rows (and especially the 51 verified-room rows) with the 446
grid-tying rows; (c) decide the next constructor from that evidence and record
the decision. No row was to move without a C1-C4 pass, and none was attempted.

## 2. The instrument: what is exact, and what is only enclosed

`tilt_audit.py` reads `workspace/submission/submission.csv` as **decimal text**
(`Decimal`, exact for what the CSV says — 49,325 distinct angle strings over
500,500 cells, cached) and computes, per row:

| quantity | how it is decided |
| --- | --- |
| container side and the beat/tie flag | bbox from `ex = (|cos|+|sin|)/2` per cell; `beat` iff `side < ceil(sqrt n)`, `ceil` by `isqrt`; agrees with `sqscore` on 554/446 |
| orientation classes | angle mod `pi/2` (a square is symmetric under 90°), clustered by a gap rule at `TAU = 1e-6` rad; re-run at `TAU/100` and `TAU*100` |
| class cell count `m` | integer |
| `x = |sin 2theta|` | enclosure: `pi` bracketed by the **Machin series in exact rationals** (16 atan(1/5) − 4 atan(1/239), alternating-series tail bounds; width 2.1e-90), angle reduced mod `pi/2`, Taylor tails bounded, half-width `EPS = 1e-45` |
| doc-98 verbatim verdict | `sqrt(m(1+x)) − sqrt(m) < 1` ⇔ `(m x − 1)^2 < 4m` (`mx > 1`), evaluated on rational interval endpoints |
| measured-bbox verdict | the same test with the class's own bbox area `A` in place of `m(1+x)` |
| bbox sharing | cells of other classes whose centres lie strictly inside a class's bbox |

The inequality is decided by exact rational comparisons on the enclosure:
`d = A − m − 1`, so `d ≤ 0` pays, `d² < 4m` pays, `d² ≥ 4m` is priced out. A
decision is reported `ambiguous` only when the interval straddles `d = 2√m`; there
are **0** ambiguous decisions, and the closest doc-98 decision in the whole table
sits **7.169e-4** from its threshold — 10^41 times the enclosure width. The
Decimal/`Fraction` core names no `float`: `exact_field.audit_module` reports
**20 decision functions, 0 offenders**.

**Flagged, not hidden.** The angles and coordinates are decimal CSV values, so
`sin 2theta` is transcendental: every `x`, `ex` and bbox area is an *enclosure*,
not a rational identity, and the class partition is a tolerance statement. §4
therefore reports the partition at three tolerances, and the two-class structure
it leans on is identical at all three on all 110 rows.

## 3. Controls (8, all exact)

1. the Machin enclosure is 2.14e-90 wide and agrees with an independent 55-digit
   value to 1e-54 (no constant is trusted);
2. the `sin`/`cos` enclosures contain the exact rational Taylor values of seven
   angles through the quadrant map, and `c² + s² = 1` to 1e-44;
3. the spinor thresholds reproduce doc 98's table exactly — 6, 6, 10, 8, 17 cells
   for `1/2, 1/3, 2/3, 1/4, 3/4`;
4. `A − m − 1 < 2√m` decides 522 rational cases (9 counts × 58 areas); 49 cells at
   `x = 0.96` is priced out, 6 cells is not;
5. angle mod `pi/2` is invariant under ±90° and ±180° to 1e-50;
6. the gap rule merges 1e-9 noise and keeps a 4e-10 design gap inside one class;
7. the delivered table is 554 beats / 446 ties and five sides agree with
   `sqscore.extent` to 1e-8;
8. the module is float-free by bytecode.

## 4. The cross-table numbers

| | grid ties | grid beats |
| --- | --- | --- |
| rows | 446 | 554 |
| orientation classes (τ = 1e-6) | **1 in all 446** | 2 in 110, ≥3 in 444 (median **45**, quartiles 4 / 104, max 589; 147 rows carry > 100 classes) |
| cells | 205,192 | 295,308 |
| tilted cells | **0** | 125,490 (42.5 %) |
| largest `|sin 2θ|` in the row | **1e-45** (axis, to the enclosure) | ≥ 0.70 in 507 rows, 0.30-0.70 in 47 |
| rows with a doc-98 priced-out class | 0 (no class to price) | **508 / 554** |
| cells in priced-out classes | 0 | **43,144** (34.4 % of all tilted cells) |

Class-level detail is stored for the 192 beat rows whose partition has ≤ 12
classes (655 classes): **249 classes are priced out** (13,278 cells), the tilted
classes have median size **8 cells**, class `x` quartiles are **0.000 / 0.861 /
0.995** (so the poses are 45°-dominant), and of the **147 tilted classes with
`m ≥ 20`, 144 are priced out** — the inequality bites exactly where a grain is
large, and large tilted grains are everywhere in the beating rows.

**Tolerance.** 362 rows change class count between `TAU/100` and `TAU*100` (the
relaxed poses carry per-cell angle jitter), which is why the claim is stated at
`TAU` and re-measured at both neighbours: at `TAU*100` the priced-out population
grows to **518 rows / 52,104 cells** (merging classes makes them larger, and the
price scales with `m`), so "508" is the conservative reading of a stable
direction. The 110 two-class rows have the **same** partition at all three
tolerances.

## 5. The answer to question (b): the price is not the separator

Read as a classifier, the tilt price has no discriminating power here:

- it cannot explain a **tie**, because every tie is a pure axis pose (one class,
  no tilted cell at all) — there is no grain to price;
- it does not explain a **beat**, because 92 % of beating rows carry a class it
  prices out.

So the delivered table does **not** "systematically evade" the inequality; it
**violates its model**, which is a different and more useful statement. Doc 98's
inequality is about a grain that owns its bounding box and can buy back one cell
row at a seam. The delivered beats are not that object.

## 6. Why the inequality does not bite: the bbox is shared

For every row, the instrument measures how much of one class's bbox is occupied
by *all* cells (its own plus the other classes'):

| | two-class beats (110 rows) |
| --- | --- |
| bbox fill of the probed (tilted) class | min 0.444, **median 0.879**, max 0.998 |
| fill ÷ the row's own box density `n/L²` | min 0.611, **median 0.937**, max 1.062 |
| rows at ≥ 0.8 / ≥ 0.9 of their box density | 96 / 75 |
| score gain over the grid | min 0.0053, median 0.0193, max 0.1310 |

A class whose bbox is filled to the container's own density is not costing the
container an inflated box: the area the inequality charges it for is being used
by the other lattice. That is the mechanism — **two lattices sharing one
bounding box**, not a grain embedded in a substrate. Doc 98's §8(3) named this
("the interface must be worth more than one row … cells of each owning area on
both sides"); the audit says the delivered rows had it all along, in its
strongest form: the two lattices interlock over the *whole* box, and 105 of the
110 two-class rows are exactly the ones the isolated-grain inequality rejects.

## 7. The 51 verified-room rows

Joining the room ledger (`crystal_domains`, room total `1.09584` over 51 rows at
`n ≤ 100`) to the audit:

- **30 of 51** carry a doc-98 priced-out class; **18** are two-class poses, 17 are
  one-class (room there comes from a published lower bound below the grid, not
  from a beat);
- 651 of their 2,937 cells are tilted, and **534 (82 %)** of those sit in priced-out
  classes — a much higher share than the 34 % over all beats, which is what a
  high-room row looks like when the mechanism is area sharing;
- their bbox-sharing ratio has median **0.937**, the same as the two-class family.

So the answer does not change in the high-room population; it sharpens.

## 8. What this does to doc 98

Doc 98's §6 result stands as a statement about its **own constructor**: an axis
substrate plus a grain whose bbox is *added* to the substrate's extent, with
collisions resolved by deleting cells from one side. Both of its yield rules
delete, so neither can produce a shared bbox.

Its closing sentence — *"two grains cannot do it at these counts either"* — is
**too broad** and is corrected here: it is true for butted grains and for
deletion-based interleaving on a one-row seam; it is false for area-sharing
two-lattice poses, of which the delivered table already contains **110**, spanning
`n = 5 … 974` and beating the grid by 0.0053-0.1310 of score. The correct
statement is that *a grain that must be given its own box* cannot pay, and the
delivered beats never give it one.

## 9. The decision: the next prototype is an area-sharing two-lattice constructor

**Direction: `shared_box.py` — two whole lattices, one shared box, no deletions.**

Why this and not the alternatives:

- **Not a many-grain polycrystal constructor.** The polycrystal reading rests on
  the class partition, which is tolerance-dependent on 362 rows; the two-class
  structure is stable at three tolerances in 110/110 rows, and it already wins.
  A many-grain search would add a much larger space around a mechanism the audit
  locates more precisely at two classes. Polycrystals are the *consequence*
  (444 rows have ≥3 classes), not the cheapest first object.
- **Not a contact-network / topology edit.** Doc 97 measured the room rows as
  floppy (edge contacts 0.43-0.62 of `3m − 3`), so rigidity is not the lever, and
  runs 132-134 measured every tightening family null on the delivered poses
  (contraction, single-axis band slide, squeeze-and-legalise, void swap). The win
  is in the *area partition*, which is exactly what a shared-box constructor
  changes.
- **Not the run-141 interleave.** Its two yield rules both delete cells, so its
  best pose at every tested row was the degenerate `1/1` grid. Area sharing is
  the one thing it provably cannot express.

Why it is area-feasible where it is needed: two disjoint lattices in a box of side
`L` need `n ≤ L²`, so a beat needs `n > (k−1)² = k² − 2k + 1`, i.e. only the top
`2k − 1` counts of a band are reachable, and the void budget is `< j`. In the
scored bands the frontier is `m* = k² − j*` with `j* = 18…26 ≤ 2k − 1` for
`k ≥ 21`, so the family's area window covers the frontier rows — the same rows the
delivered table's high-room population lives on.

**Entry criterion for the next run (falsifiable, no sweep before it passes).** The
constructor must reproduce the delivered `(n, side)` pair of **at least 20 of the
110 two-class rows** from a count rule and a contact/box equation, with 0 overlaps
under `import_n090`'s exact SAT. If it cannot reproduce poses the table already
has, it will not beat the 446 ties, and the run records the refusal instead of a
sweep.

## 10. What was not built, and why

No constructor was written this run. The evidence supports a concrete,
non-redundant mechanism — which is why the direction is stated with a spec and an
entry test rather than a gesture — but a shared-box constructor needs its own
count law, its own exact gate path and its own controls, which is a run of its
own (run 141 spent its whole budget on the smaller interleaving family). A
half-verified constructor would have been worse than none. **Refused: nothing;
promoted: nothing; `submission.csv` untouched.**

## 11. Guards, and what is not claimed

Checked this run, each exit 0: `tilt_audit --selftest` **8** · `interleaved_boundary
--selftest` 9 · `twin_boundary` 5 · `notch136` · `glm_plan` 5 · `pure_slide` ·
`beaten_leverage` · `band5` · `ext_census` · `range_leverage` · `construct_seam` ·
`p_screen` · `legal_slide` · `structure --control` and `--check-solver` ·
`perturb` · `anchor_chain` · `void_insert` · `true_geom` · `row_census` ·
`motif_wheels` 13 · `crystal_domains` 4 · `import_n090` 5 · `pub_bounds_check` 4 ·
`witt_octad` 5 · `leech_audit_fix` · `verify_certificates` · `sqscore`
**22.217428576** (554/446) · `record_guard` OK · `glm_wheels --audit` 0
offenders · `py_compile`.

**Not claimed.** The audit measures the *delivered* poses only; it says nothing
about whether a constructor can reach the 446 ties. The class partition is a
tolerance statement (reported at three tolerances, stable for the two-class
family, unstable for 362 relaxed rows). The bbox-sharing figure counts cells by
centre inside a bbox, so it is a density measurement, not a tiling proof. And the
two-class rows are not all `45° + axis`: 47 of 554 beats have their largest tilt
below `x = 0.70`, and the class `x` quartiles show a real spread.
