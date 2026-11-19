# 41 — Aimed at the band: fourteen constructions, no beats; and the exact side of every row (Run 78)

Instruments `scripts/band_construct.py` (4 controls) and `scripts/exact_sides.py`
(4 controls); ledgers `workspace/push/band_construct.json` and `exact_sides.json`,
the latter stamped into `row_census.json`. Read-only: **no row changed**, no score
claimed, `submission.csv` untouched.

Two questions, one negative and one completed. The negative is measured rather
than asserted: 14 constructions aimed at the band's hardest-to-ignore rows, all
refused by the exact gate, with the reason visible in the numbers. The completed
one is item 3's leftover — the exact algebraic side of every row, in exact
rational arithmetic, including the 449 rows where it cannot be expressed.

## 1. What the band is, measured

Above n = 324 the 247 open grid rows are **contiguous in the residue**
`m = n - k²`, one block per k, and each block starts exactly one past the last row
of that k that beats:

    k=18  beats m 1..20  open 21..35      k=25  beats m 1..30  open 31..49
    k=19  beats m 1..21  open 22..37      k=26  beats m 1..31  open 32..51
    k=20  beats m 1..23  open 24..39      k=27  beats m 1..32  open 33..53
    k=21  beats m 1..24  open 25..41      k=28  beats m 1..34  open 35..55
    k=22  beats m 1..25  open 26..43      k=29  beats m 1..35  open 36..57
    k=23  beats m 1..27  open 28..45      k=30  beats m 1..36  open 37..59
    k=24  beats m 1..28  open 29..47      k=31  beats m 1..37  open 38..39

Each block ends at `m = 2k-1` (the row `n = (k+1)² - 1` is closed by Karakuş) or
at the end of the table. So the band is not a geometric wall: it is **the edge of
the imported catalogue**, per k, and the rows past it sit at the grid because
nobody published a packing for them.

That fixes the target. A packing of n squares at side L is also a packing of n-1
squares at L (drop one), so within a block the band's first row is the easiest and
every larger m is at least as hard at the same side. Fourteen attempts, one per
block, decide what this run's construction family can do for all 247 rows.

**What is at stake.** The 403 beating rows above 324 gain a mean of **0.008808**
in score each. At that same quality, the 247 band rows would be worth **2.176** —
and **19** of them would cover the entire 0.163635 gap to the leader. The band is
the only place left in the table with that much score in it.

## 2. The construction aimed: extend the record by one square

For each k, take the delivered state of the row with `m = M(k)` — verified to beat
the grid, so its bounding box is already smaller than `k+1` — and put one more
unit square inside the largest box that still beats, `L = k+1 - 1e-6`. If any
placement is free, the row `n = k² + M(k) + 1` beats the grid outright at the
record's own side. Two tiers, both judged only by `declp.gate` at tol 0:

* **T1 rigid**: a 1/16 raster of centres at six orientations — 0, 45°, and four
  small Pythagorean tilts (arctan 3/4, 5/12, 7/24, 8/15), so that a placement on
  rational coordinates stays exactly rational.
* **T2 translate**: where T1 finds nothing, the best five placements go to
  `declp.solve` at `L = k+1 - 1e-6` with the new square and its 30 nearest
  neighbours free, then `packlib.finalize` and the gate.

    result: 0 of 14.  No free placement at any of six orientations.
    best placement still overlaps by 0.125, 0.125, 0.120, 0.132, 0.098, 0.142,
                              0.094, 0.094, 0.125, 0.134, 0.126, 0.125, 0.097, 0.139
    (mean 0.1196)  ·  70 local LPs: 0 feasible  ·  0 gate passes  ·  156 s

Two things in those numbers matter. First, **the free space is box-shaped, not
diamond-shaped**: all six orientations give the same margin to three decimals, so
a tilt gains nothing — the gap is a rectangle ~0.88 across, not a hole a rotated
square could slip into. Second, the margin is the *distance from fitting*: the
largest empty square in each record is `1 - margin`, i.e. **0.86 to 0.91 of a
unit**. The records are jammed: they carry their tilted boundary layer at
essentially full occupancy, and our family asks that layer for one square more.

**Verdict, stated with its scope.** No row of the 247 beats the grid by this
construction, and because the family is nested (its k-th member is that k's last
record plus inserts), the failure at one insert closes the family for the whole
block. This is **not** a proof that the rows are optimal or even unbeatable: a
tilted boundary layer built from scratch — rather than extended — is untouched,
and so is any global search. What it does establish is that the rows are not one
square away from the records the table already holds, which was the cheapest
possible way for them to fall.

**Why the family is structurally weak**, in one line: shrinking a 19-box grid by
any δ requires re-laying the boundary layer at a tilt, because deleting 16 squares
from the interior of a full grid does not move the extreme rows. The records do
that re-laying and carry `m` squares in the layer; the band wants `m+1` from the
same layer, and the layer is full by about a tenth of a unit.

## 3. Item 3's leftover: the exact algebraic side of every row

`exact_sides.py` computes, per row and with exact rational arithmetic throughout,
the element of a declared number field that the side lies in:

    every angle a multiple of pi/2      ex = 1/2                 L in Q
    every angle also a multiple of pi/4 ex = sqrt(2)/2           L in Q(sqrt 2)
    every angle Pythagorean (p,q,c)     ex = (|p|+|q|)/(2c)      L in Q

so `L = A + B·√2/2` with A built from the stored decimals exactly
(`Fraction(str(x))`) and B an integer. Maxima and minima over the four extremes are
decided by `q2_sign`, which compares `a + b√2/2` by squaring — never by a float.
`ideal` then searches A' (denominator ≤ 24) and B' (|B'| ≤ 12) for the
construction's own value, and `residual` is the distance between the two.

    axis        447   L in Q            (every one exactly ceil(sqrt n) + ~2e-9)
    45          100   L in Q(sqrt 2)
    pyth          4   L in Q
    generic     449   not expressible

Examples: n = 5 → `2 + √2/2`; n = 15 → `4`; n = 50 → `53/7` (which is the value
doc `19` decoded independently from the contact graph — the two agree); n = 290 →
`14 + 5√2/2`; n = 326 → `15 + 5√2/2`; n = 345 → `19`; n = 344 and n = 982 are
generic (117 and 440 irrational angles).

Checks: 0 disagreements between exact arithmetic and `sqscore.extent` over the 551
expressible rows (worst 1.03e-13), and once stamped into the row ledger, control 6
asserts that all 447 axis rows have ideal side exactly `⌈√n⌉`.

Two findings worth keeping:

* **B must be searched, not read off the state.** The state's own B counts only
  the 45° squares that touch a wall, so it is always 0, ±1 or ±2. n = 326 is the
  counter-example to reading it: its stored side is *rational* (B = 0) yet equals
  `15 + (5/2)√2` to 3.8e-9. The construction's algebraic value carries a
  coefficient the geometry of the walls does not show.
* **25 expressible rows have no ideal inside the declared box** (residual up to
  2.4e-4, against a median of 1.9e-9). They are recorded as such in the ledger
  rather than given a fitted expression.

**The honest limitation, said plainly.** A decimal angle is a *rational* number,
and cos of a non-zero rational is transcendental (Lindemann–Weierstrass), so for
any row containing a rotated square the side computed from the stored decimals is
not algebraic at all. What is algebraic is the **ideal** side — the construction
whose angles are exactly 0, π/4, arctan(p/q). For the 449 generic rows there is no
such construction in our hands: their angles are *polished*, not constructed, and
the instrument records "not expressible" with the count of generic squares instead
of inventing an expression. That is also why these rows cannot be certified the way
the 191 frozen-angle rows were: there is no exact angle multiset to certify.

## 4. Re-running

```bash
cd source_material/ToDo/squares_in_squares
python3 scripts/band_construct.py --selftest      # 4 controls (~2 s)
python3 scripts/band_construct.py                 # the 14 attempts (~156 s)
python3 scripts/exact_sides.py --selftest         # 4 controls (~7 s)
python3 scripts/exact_sides.py                    # every row (~10 s)
python3 scripts/row_census.py --selftest          # 6 controls
python3 scripts/row_census.py                     # the one ledger, now with sides
```

Ledgers: `workspace/push/band_construct.json` (per block: the anchor's side, the
box, every orientation's margin, every LP outcome, and the verdict),
`exact_sides.json` (per row: class mix, exact expression, ideal, residual), and
`row_census.json`, which now carries `side_class`, `L_exact`, `L_ideal`,
`exact_residual` and `exact_ok` beside the certificate stamp and the accounting.

## 5. What is next

The only item left with score in it is the one this run could not reach: **build
the tilted boundary layer from scratch** rather than extending a record. The
records show the layer can carry `m = M(k)` squares at side `k+1`; the question is
whether its parameterization admits `m+1`. That needs a construction with its own
geometry (seam, mask or staircase), not an insertion — and it is the same object
that `21`–`23`, `27` and `37` kept circling. Items 4 (an independent judge), 5
(the wall-pinned extent lemma) and 6 (how many constructions is the table) are
untouched by this run and unaffected by its negative.
