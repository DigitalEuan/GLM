# 42 — The tilted boundary layer, built from scratch, and its capacity (Run 79)

Instrument `scripts/layer_construct.py` (4 controls); ledger
`workspace/push/layer_construct.json`. Read-only: **no row changed**, no score
claimed, `submission.csv` untouched.

`41` §5 named the one construction left with score in it: not extending a record
but *building* the tilted boundary layer. This run builds it, lets the exact gate
decide, and reports its capacity. The layer does not reach the band: **0 of 14**
block-first rows, and its capacity is `m ≤ 0` at every k.

## 1. What the layer is, read off the table exactly

n = 326 is the one band-adjacent row whose construction is fully exact in our
hands (angles only 0 and 45°, side `15 + (5/2)√2`). Its cell map:

    276 axis-aligned squares + 50 at 45° = 326,  side 18.535533906
    a (k+1)-grid with two opposite corners cut away in a 45° diamond
    (85 cells out) and two 5x5 blocks of 45° squares on the rotated unit
    lattice laid in the cuts (50 in):  net -35 squares for -0.4645 of side.

Two facts about that shape drive everything:

* the cuts are **diamonds**, because a 45° block on the rotated unit lattice has
  bounding box `√2 j` and holds `j²` squares;
* a unit square's width is **≥ 1 in every direction**, so a seam band of
  fractional width holds nothing at all. The tilt cannot be a thin strip; it has
  to be a whole block traded against grid cells.

## 2. The generator, and the exact gate as the only judge

`build(k, j, delta, sx, sy)`: the axis grid (every cell whose unit square fits
`[0, L]²`, `L = k+1−delta`), plus two `j×j` blocks of 45° squares at opposite
corners at offsets `(sx, sy)`, minus every axis cell that collides with a rotated
square. Nothing is copied from the delivered states: the coordinates come from
`(j, delta, sx, sy)`. Collision uses the four-axis SAT constant
`0.5 + 0.5(|cos Δ| + |sin Δ|)`, which is the same on all four axes because on any
owner's axis the owner contributes its own half and the other square its support.

Certification is the project's own path — `packlib.finalize` (which buys ~1e-9 of
clearance by scaling) then `declp.gate` at tol 0 — because a clean lattice build
touches exactly and can round the wrong way by 1e-13. A build counts only if the
gate passes **and** `L < k+1 − 1e-9`.

Sweep: `j = 0..8`, twelve deltas, a 5x5 offset grid, truncated at 24 gate calls
per row (declared; candidates are tried in descending count, so the truncation
never hides a *higher* count that passed).

## 3. Result: 0 of 14, and capacity `m ≤ 0`

    k    need n  need m   best gated n   m_cap   L        layer-only
    18     345     21        324          0     18.000    n 322 (m -2)
    19     383     22        361          0     19.000    n 359 (m -2)
    ...    ...    ...        ...         ...     ...        ...
    31     999     38        961          0     31.000    n 959 (m -2)

    overall capacity m_cap = 0          (the best gated build is the plain k x k grid at side k)
    with one diamond or more  m_cap = -2  (the layer *costs* two squares at every k)
    band requirement          m >= 21 .. 38

So the layer's capacity, as a function of (k, m), is `m ≤ 0`: it never adds a
square to `k²`, and with any diamond at all it loses two. The band needs 21 to 38.
**No row of the 247 is reachable by this construction**, and that is measured, not
inferred.

**Why it loses, with the number.** At the n=326 record's own side the clean build
carries **290** squares where the plain 18×18 grid carries **324** and the polished
record carries **326**: a j=5 diamond's `√2·5 = 7.07` bounding box displaces about
84 unit cells and puts back 50, a net −34. Diamond trade is negative on an integer
grid, by area, at every j — `2j²` in, `≈ 2j²` out or worse.

**Why the table still has 54 clean records at m ≤ 13.** Those are *polished*: their
axis cells are shifted fractionally (n=326's cells sit at 18.03, not 18), which is
exactly why their sides are `A + B√2/2` with a non-integer rational A — `15 + 5√2/2`,
`13 + 4√2`, `k + √2/2`, `467/17 − 11√2/2`. The menu of those families, read off the
403 rows that beat above 324, is the empirical capacity curve: **the largest m any
clean family reaches is 13, at any k.** The band starts at 21.

**Scope, stated.** A corner placement is one declared placement; the record's
interior/anti-diagonal placement and fractional shifts (polishing) are not swept
here, and the sweep is truncated at a declared budget. What is established is that
the *clean* two-diamond layer — the only version we can build exactly from
coordinates — cannot carry a single square past `k²` at any k, so it cannot attack
the band; and that the polished records which do carry m = 1..13 stop well short of
where the band begins.

## 4. Controls

1. `j = 0, delta = 0` reproduces the plain (k+1)-square grid and gates at `k+1`;
2. the gate bites: two coincident blocks are refused (penetration 0.7071);
3. the builder is run at the table's own clean side (18.535533906) and its count is
   reported against the record's 326 — the measurement in §3;
4. bookkeeping: the count is always kept-axis cells plus `2j²`.

## 5. Re-running

```bash
cd source_material/ToDo/squares_in_squares
python3 scripts/layer_construct.py --selftest   # 4 controls (~10 s)
python3 scripts/layer_construct.py              # the fourteen rows (~2 min)
```

## 6. What this settles, and what it does not

It settles the question `41` left open in the negative: the from-scratch layer, as
a clean construction, does not beat the grid on any band row — its capacity is
`m ≤ 0` against a requirement of `m ≥ 21`, and it loses squares rather than adding
them because the diamond trade is negative by area. Combined with run 78 (no band
row is one square from the records we hold), both cheap routes into the 247 are now
measured and closed.

It does **not** settle the rows themselves. A *polished* construction — the kind
that produced the 54 clean records, and the 349 generic ones — remains open, and so
do items 4 (an independent judge), 5 (the wall-pinned extent lemma) and 6 (how many
constructions is the table). The band is still the only part of the table with
enough score in it: at the mean gain of its neighbours, 19 of the 247 rows would
close the entire 0.163635 gap.
