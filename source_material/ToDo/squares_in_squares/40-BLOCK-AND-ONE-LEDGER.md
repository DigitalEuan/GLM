# 40 — The catalogue block is certified, and the rows get one ledger (Run 77)

Instruments `scripts/frozen_opt.py` (`--min-n`, cumulative slices; 3 controls) and
`scripts/row_census.py` (now 5 controls: the certificate stamp, the closed-row
`head`, and the gap accounting). Ledgers `workspace/push/frozen_opt.json` (union
of two slices) and `workspace/push/row_census.json` (1000 rows, stamped).
Read-only: no row changed, no score claimed, `submission.csv` untouched.

This run finishes item 2 of `39` §1, probes a question I expected to go the other
way, and closes item 3's second half as a negative rather than leaving it as an
aspiration.

## 1. Item 2 finished — and the slice was the whole block

`39` §3 priced the completion as `--top 300 --max-n 324`, about five minutes, and
called it "the catalogue block", expecting a partial run. The eligible set is
**150**: only 150 of the 553 beating rows lie at or below n = 324, and 403 lie
above it. So `--top 300` is the *entire* block, and the result is unconditional on
it, not a declared slice of it:

    150 of 150 certified, 0 candidates, 147 s
    (n <= 100: 36 rows, 1.9 s | 101-200: 51 rows, 22.4 s | 201-324: 63 rows, 122.7 s)
    slowest single row 4.75 s at n = 303

The statement, at each of those rows: with every square free and the delivered
state's own axis declaration, `solve(xy, th, L0 - 1e-6, free=all)` has no feasible
point — no translation of those angles fits below the delivered side. The cost is
~`n^2`, which is why 63 rows above n = 200 cost 122.7 s while 87 rows below cost
24.3 s.

**Scope, unchanged and load-bearing.** This is a statement about the *declaration*
(the argmin axis per tight pair, as delivered), not about the branch space: run 74
closed the whole declaration space at five rows only. What it rules out at n ≤ 324
is rearrangement at fixed angles; what it leaves standing is a different angle
multiset — which is W2's job description, now stated per row rather than as a mood.

## 2. The frontier is free too — not what I expected

The reason to spend 228 s above the catalogue's stopping point: the 41 beating rows
in 325 ≤ n ≤ 400 sit in the residue band `m ≥ 21`, where the grid is 0.02–0.05 above
the area bound, so the delivered sides there are close to the zero-waste ceiling and
were the most plausible place in the whole table for slack to hide. The guess was
that the certificate would break at the first row past the frontier.

    band 325-400: 41 of 41 certified, 0 candidates, 228 s (4.4-7.1 s per row)
    union across both slices: 191 of 191 certified

So the certificate is not a small-`n` artefact: at **every beating row with
n ≤ 400** the delivered side is the frozen-angle optimum of its own declaration.
The ledger accumulates slices by design (`frozen_opt.json` now carries
`min_n`/`max_n`/`top` per slice and a union summary), precisely so that a probe
above the frontier cannot erase the block below it — a partial-run hazard that
`39`'s single-slice ledger had.

Honest caveats, both of which belong next to the number: "certified" is not
"optimal" — the model fixes the axis declaration, and it is *our* declaration, so
the leader is not bound by it; and 362 beating rows above 400 remain unattempted.
By the measured `n^2` curve (7 s at n = 400, ~45 s at n = 1000) the complete 553-row
certificate is a **1.5–2 h** job, priced from measurements rather than guessed.

## 3. Item 3: one ledger — and the attribution is measured to be impossible

`row_census.py` now ingests `frozen_opt.json` and stamps every row with one status
word, so the table question ("what can still move, and what cannot") is answered in
one file:

    closed          60   a published bound forbids any gain
    opt@declared   191   delivered side = optimum of its own declaration, frozen angles
    beat-open      362   beats the grid, no certificate
    grid-open      387   does not beat the grid, no published bound closes it

**A defect found while stamping.** At a row closed by a published bound the old
`head` formula `(grid - floor)/sqrt(n) - gain` returns `(L - grid)/sqrt(n)` — a
*positive* "opportunity" on a row where no gain is possible at all. The artefact is
tiny (largest 5.0e−10, at n = 4), so no total printed in run 76 was corrupted, but
the definition was wrong: `head` is now exactly 0 at a closed row, and control 4
asserts it for all 60 and asserts that none of them is ever certified.

**The attribution, measured.** The recorded gap to the leader is 0.163635. Every
bound this project holds, summed at its most generous (zero-waste: `grid/sqrt(n) - 1`,
which no packing attains), gives:

    zero-waste ceiling over the 387 open grid rows   7.005752
    same over the 553 beats (ceiling minus gain)    15.022691
    conceivable total                              22.028443   = 135x the gap
    the same restricted to head                    21.005091   = 128x the gap

So no bound held here attributes the gap row by row, and none ever could: the
floors are 128× too weak. Control 5 asserts this inequality, so the negative stays
visible instead of quietly turning into a "result". Attribution of 0.163635 needs
the leader's per-row sides — which this project has never had — or a measurement per
row that the floors cannot supply. That is a data problem (item 7's neighbourhood),
not an instrument problem.

**What item 3 therefore is.** The ledger's remaining job is bookkeeping — which
rows are still in play, and under which scope — not prioritisation. Its second half,
"attribute the 0.163635", is dead with bounds, and is recorded as dead.

## 4. What this changes

* **The table's opportunity now has a status, not a story.** 191 beating rows are
  closed to frozen-angle rearrangement, 60 grid rows are closed outright, and the
  remaining 749 rows split 362 + 387. Score can only *appear* on the 387 open grid
  rows (247 of them above 324, in one residue band); the 362 beat-open rows can only
  improve, and at frozen angles they cannot.
* **W2 is the only lever at n ≤ 400, stated per row.** Any further gain on those 191
  rows must come from a different angle multiset; a search that only retranslates
  the delivered angles is now known to be aimed at a row that cannot move.
* **Items 2 and 3 are now settled enough to stop.** Item 2's extension above 400 is
  a compute purchase (1.5–2 h) with no new idea in it; item 3's accounting half is
  impossible with the bounds we hold. The live target list is items 1 (247 residue
  rows need a construction), 4 (an independent judge), 5 (the wall-pinned extent
  lemma) and 6 (how many constructions is the table).
* **Item 1 is untouched by this run** and remains the only item that can add score:
  247 open grid rows above 324, all `m ≥ 21`, where beating the grid needs a packing
  within 0.02–0.05 of the area bound.

## 5. Re-running

```bash
cd source_material/ToDo/squares_in_squares
python3 scripts/row_census.py --selftest                 # 5 controls (~2 s)
python3 scripts/frozen_opt.py --selftest                 # 3 controls (~6 s)
python3 scripts/row_census.py                            # census + stamping (~2 s)
python3 scripts/frozen_opt.py --top 300 --max-n 324      # the block, 150 rows (~2.5 min)
python3 scripts/frozen_opt.py --min-n 325 --max-n 400    # the band above (~4 min)
```

Ledgers: `workspace/push/frozen_opt.json` (slices + union; `eps` 1e−6, every row's
`self_feasible`/`certified`/`seconds`, so a partial run cannot be quoted as a
table-wide result), `workspace/push/row_census.json` (1000 rows with `status`,
`head`, `floor`, `certified_frozen`, and the accounting block).
