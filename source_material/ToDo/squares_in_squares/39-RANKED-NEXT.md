# 39 — What next: eight ranked targets, and the first two begun (Run 76)

Instruments `scripts/row_census.py` (3 controls) and `scripts/frozen_opt.py`
(3 controls); ledgers `workspace/push/row_census.json` and `frozen_opt.json`.
Read-only: no row changed, no score claimed, `submission.csv` untouched.

W4 is spent and dead (`37` §9), W1 has its first measurement (`38`): the seam
offset at the table's only two-lattice row is determined and a shift costs the
shift. This run writes down the ranked list that replaces those two, and starts
the two cheapest entries. One of them has already changed the plan, and one of
my own premises did not survive the measurement.

## 1. The eight targets, noted

Ranked by reachable score × probability × 1/cost. Status is where this run left
each one.

| # | target | why | status |
| --- | --- | --- | --- |
| 1 | **Prove vs improve on the 675 rows above n = 324** — a row needs a *construction*, not a source, to score | the largest block by count; the grid is only provably stuck at `n = k²` and `n = k²−1` | **begun, §2**; a construction aimed at the band is measured and refused in `41` |
| 2 | **Frozen-angle optimality row by row** — the `k = n` free-set LP on every beat | turns run 74's five-row negative into a table-wide one, and names the rows where slack exists | **begun, §3**; the block and the band above it certified in `40` |
| 3 | **One row-keyed ledger + attribution of the 0.163635** | forty per-run ledgers, no table question answered | begin (the ledger exists in part) |
| 4 | **A second, independent judge** — a checker sharing no code with `packlib.verify`, plus an independent score | every instrument in nine runs funnels into one unexamined judge | not started |
| 5 | **The wall-pinned extent lemma** — unify run 67's free-set refusals, `37` §9's extent-bound flip and `38` §3's 1:1 seam cost | one lemma explains every negative of runs 65–75 and predicts the exempt rows | not started |
| 6 | **How many constructions is the table?** — canonicalise the contact graph of all 553 beats and count isomorphism classes | `18` predicts side length from the graph, nobody has counted the templates | not started |
| 7 | **Import the literature's bounds, not only its records** | a better bound proves a row optimal or proves we are leaving score on it | not started |
| 8 | **Price the `GAIN_MIN = 4e-8` bar** — rows whose true optimum is below the stored side by less than the bar | a policy, never priced; run 75 showed inherited gates deserve scrutiny | not started |

## 2. Item 1 begun: the row census, and it reframes the 675

`row_census.py` computes, per row and with no search: the delivered side, the
grid, the gain, the strongest proved floor (`max(area, Karakus)`), the head still
reachable, whether the row is aligned, and its residue `n − ⌊√n⌋²`. Controls: the
table reproduces (`22.218056945`, 553, 447); **no delivered row violates its
floor** (including all 553 beats — a violation would convict the bound, not the
row); and both endpoints bite (`n = 15` closed by Karakus at exactly 4, `n = 11`
open with head 0.152204).

The partition of the 447 grid rows is the first thing nobody had computed:

    n = k^2     31 rows } 60 rows cannot beat the grid by a published bound
    n = k^2 - 1 30 rows } alone, with no catalogue and no search
    open        387 rows, of which 247 are above n = 324

The 60 are worth a sentence on their own: `area` gives `L ≥ k` at a square, and
`Karakus` is exact at `k²−1`, so those rows are settled by arithmetic. Of the 60,
**26 are above n = 324** — i.e. the block the record files under "0 of them can be
proved" contains 26 rows that *are* proved, and the proof needs no source at all.
(W3's claim is about the catalogue; it should say so.)

The 387 open rows are not spread evenly. Above n = 324 the failure is purely a
**residue band**:

* every row above 324 with residue `m ≤ 20` beats the grid;
* all **247** open grid rows above 324 have `m ≥ 21` (they run to `m = 59`, i.e.
  rows just below the next square, where `⌈√n⌉` is only 0.001–0.02 above the side
  the area bound allows).

Below 324 the open rows cover every residue, so the two blocks have different
causes: below the frontier we fail on rows a catalogue says nothing about, above
it we fail on one residue band, systematically.

**My own premise did not survive.** I proposed ranking rows by head as the target
list. Head sums to **6.295** over the 387 open rows — forty times the 0.163635 gap
— so it cannot discriminate; and worse, all **553** beats have head ≥ 0.01
(sum 14.71), because the area/Karakus floors are weak everywhere. The head ranking
is informative only *inside* the grid block, and even there it points at `n ≤ 72`,
where nothing is unknown. The usable output of item 1 is therefore the residue
split and the 60/26 closed rows, not a head ranking. That is an honest correction
to my own proposal, recorded rather than quietly dropped.

## 3. Item 2 begun: the delivered side is the frozen-angle optimum, 87 rows so far

`frozen_opt.py` asks the `k = n` question of run 67 for one row at a time: with
every square free and the delivered state's own branch per pair, does anything fit
`L0 − 1e−6`? A refusal is a certificate for that declaration; a feasible point
would be a score candidate. Controls: the delivered state is feasible at its own
side for `n = 5, 11, 15, 294`; a demand 0.5 below the side is refused at `n = 5`;
and run 67's published refusal reproduces at `n = 294` (`17.656854251`, 2.8 s).

    slice: the 87 beating rows with n <= 200 (all of them)
    result: 87 of 87 certified, 27 s total (~0.3 s per row)

So on every beating row up to n = 200 the delivered side is the exact optimum of
the declared-axis, fixed-orientation model: no translation of those angles, with
that declaration, improves it. The scope is the *declaration*, not the branch
space — run 74 closed the whole declaration space at five rows only — and the
cost scales like `n²`, so the natural completion is `--top 300 --max-n 324`
(the whole catalogue block, ~5 min), which this run did not take.

## 4. What this changes

* **The 675 is not one block.** It is 26 rows proved optimal by a published bound,
  305+ rows that already beat, and **247 open grid rows in a residue band**. Only
  the last group is a target, and it is 247 rows, not 675 — and it needs a
  construction, not a source.
* **Item 3 is now easy to the point of being overdue**: the census already is the
  row-keyed ledger; what it lacks is the instrument that produced each row and the
  exact algebraic side.
* **Item 2 is cheaper than I priced it** and should be finished before any search
  is aimed at a row: a row certified here cannot be moved by a frozen-angle
  rearrangement, so every remaining gain at `n ≤ 324` must come from a different
  angle multiset — which is W2's job description, stated per row.
* **Items 1 and 2 do not interact as I expected**: head does not select the rows
  item 2 should certify, because it is uninformative on beats. Item 2's slice is
  better chosen by *row size* (cheap) than by head.

## 5. Re-running

```bash
cd source_material/ToDo/squares_in_squares
python3 scripts/row_census.py --selftest     # 3 controls (~1 s)
python3 scripts/row_census.py                # the census (~1 s)
python3 scripts/frozen_opt.py --selftest     # 3 controls (~6 s)
python3 scripts/frozen_opt.py --top 87 --max-n 200    # the slice above (~27 s)
python3 scripts/frozen_opt.py --top 300 --max-n 324   # the whole block (run 77: 150/150)
python3 scripts/frozen_opt.py --min-n 325 --max-n 400 # the band above (run 77: 41/41)
```

Ledgers: `workspace/push/row_census.json` (1000 rows), `frozen_opt.json` (the
declared slice, with its `eps` and its row list, so a partial run cannot be quoted
as a table-wide result).
