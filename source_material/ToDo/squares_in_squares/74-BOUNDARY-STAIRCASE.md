# 74 — The boundary staircase, certified: an interval verifier, a corner-nesting packer, and two laws that close the fringe route

Run 112 built packings from scratch and every family lost; doc 73 §5 named the three things worth trying
and this run does all three. It adds `scripts/interval_verifier.py` — a strictly float-free rational
interval verifier, now inside the float audit — replaces the shelf with a **corner-nesting** packer, and
builds **family E**, an upright core with tilted cells seated along a wall at the quarter word and at
rational slopes `t = 1/q` with an expanding denominator.

**Verdict: nothing beats `L_delivered`, so `submission.csv` and the root `WHITEBOARD.md` are untouched.**
But this run can say *why* in a way run 112 could not, because two of its results are statements rather
than measurements:

* **T1 — the lattice ceiling.** A pose whose cells all sit on the integer lattice has side at least
  `ceil(sqrt n)`. All nine target rows are in the 553 that beat the grid, i.e. `L_delivered < ceil(sqrt
  n)`, so **no lattice construction can pass C2 on any of them** — not for want of a better packer, but
  arithmetically.
* **T2 — fringe domination.** A one-cell tilted fringe has along-wall pitch `1/max(|c|, |s|) >= 1` and
  outward protrusion `|c| + |s| >= 1`, both minimised at the axis. So a tilted fringe cell is never
  denser than the axis column it replaces, and family E's maximum at side `L` is exactly `floor(L)^2`.

Together they close the wall-fringe route, and they locate the only remaining one: the delivered table's
tilt is **interior** (a 56-cell band at `3-4-5` and `1/3` in the `2k + 4/7` rows), not a wall fringe.

## 1. The interval verifier: C1's second judge

`true_geom.py` measures a pose at 40 decimal digits — correct to the digits used, but a measurement. Doc
72 §5 C1 refuses to promote a pose with no exact sentence, and doc 73 §5 named the consequence: the open
rows (680, 733, 845, 904, 971) carry no algebraic word at all, so a construction there has no judge.
`interval_verifier.py` is that judge, and it is `Fraction` from top to bottom:

* every **direction** is enclosed in a rational interval — the axis word exactly, the quarter word by
  `isqrt` bounds on `sqrt 2` (`lo = isqrt(2·2^160)/2^80 <= sqrt 2 < (lo+1)/2^80`), and a rational slope
  `(q, p)/sqrt(p^2 + q^2)` exactly when `p^2 + q^2` is a square (`4/5, 3/5` for `3-4-5`), by the same
  `isqrt` bracket otherwise;
* every **centre** is an exact rational, so the displacement of a pair is exact and only the extents and
  the axes carry enclosure width;
* all **4N wall bounds** are checked as `x - h >= 0`, `x + h <= L`, and the same in `y`, against a
  declared rational side;
* every pair is checked for a separating axis with a **strictly positive rational lower bound** on the
  slack, testing the two axis-aligned directions first (SAT holds on *any* axis, so disjoint bounding
  boxes already certify a pair) and the four cell axes only for the pairs that survive that prune;
* the side is reported as an interval `[L_lo, L_hi]`, with `L_hi` a rational upper bound.

It is a *strict* judge, and it says so: an **exact contact** (slack exactly 0) cannot be certified by an
enclosure, because the interval straddles zero. That is why every construction here carries a `1e-9`
hairline, and why the verifier refuses the exact-contact poses the algebraic gate accepts. An overlap is
certified when the best axis' slack *upper* bound is negative; anything else is reported `inconclusive`,
never as a pass. `--selftest` has **7 controls**, including both refusals: an exact contact is
`inconclusive` (control 3) and a half-unit overlap is a proven violation (control 5).

The verifier is **in the float audit**: `glm_wheels --audit` now checks **613** decision functions with
**0** naming `float` (596 before, 17 new). `interval_verifier.py --check` replays the nine stored family-E
recipes end to end in **19 s**, the 961-cell `n = 971` pose (461,280 pairs) and all.

## 2. The corner-nesting packer: what moved, and what did not

Run 112's shelf could only stack rows, so a residue strip always paid a whole extra row under the
near-square block. `nest_pack` keeps every free corner of every placed box as a candidate and takes the
lowest-leftmost fit, splitting the boxes by the same `1e-9` hairline — overlap-freedom stays structural.
`best_layout` now runs both packers over the same width scan and keeps the better.

| n | A run 112 | **A run 113** | B run 112 | **B run 113** | C 112 | **C 113** | D 113 |
|---|---|---|---|---|---|---|---|
| 29 | 7.828427 | **7.828427** | 6.656854 | **6.414214** | 8.538462 | **8.538462** | **6.000000** |
| 41 | 8.828427 | **7.828427** | 7.414214 | **7.414214** | 9.846154 | **9.846154** | **7.000000** |
| 53 | 9.828427 | **8.828427** | 8.656854 | **8.000000** | 11.153846 | **11.153846** | **8.000000** |
| 55 | 9.828427 | **8.828427** | 8.414214 | **8.000000** | 11.769231 | **11.769231** | **8.000000** |
| 680 | 28.828427 | **27.828427** | 27.656854 | **27.000000** | 39.230769 | **39.230769** | **27.000000** |
| 733 | 29.828427 | **28.828427** | 28.656854 | **28.000000** | 39.230769 | **39.230769** | **28.000000** |
| 845 | 31.828427 | **30.828427** | 30.656854 | **30.000000** | 43.230769 | **43.230769** | **30.000000** |
| 904 | 32.828427 | **31.828427** | 31.656854 | **31.000000** | 44.461538 | **44.461538** | **31.000000** |
| 971 | 33.828427 | **32.828427** | 33.000000 | **32.121320** | 45.769231 | **45.769231** | **32.000000** |

The packer does what it was asked to do: **A gains `1.0` of side on eight of nine rows** and **B gains
`0.24`–`0.88`**, and B now **ties the upright reference D on six rows** (53, 55, 680, 733, 845, 904) —
its tilted decoration nests for free there. Family C is unchanged because a Pythagorean *square* lattice
has nothing to nest; its shelf was already its own tiling. All 36 seeds are zero-overlap at 40 digits.

**But no deficit against `L_delivered` closed, and doc 73 §4's attribution needs a correction.** Run 112
read D's residual `1.0–2.3 %` as "shelf non-nesting (49–57 void units)". It is not: for upright blocks the
boxes *tile*, so `sum bbox = n` exactly and `L^2 - sum bbox = L^2 - n` is the container's own leftover,
which this run measures at 49, 51, 55, 57 and 53 units on 680…971 — unchanged by the packer, because it
is `ceil(sqrt n)^2 - n` plus a hairline. The shelf was never the cause; T1 is.

## 3. Family E: the seating law, then the seats

Family E is an `a`-by-`b` upright core with one-cell tilted cells seated along one or two walls inside
`[0, L]^2`. The seats are not scanned: `seat_law(p, q)` derives them, and every candidate is then still
clearance-checked (a seat a corner or the other wall's fringe refuses is skipped, not asserted).

Two cells of the same direction, at the same outward coordinate, `Δ` apart along the wall, have SAT axes
`u = (c, s)`, `v = (-s, c)` and the two wall directions, so their best slack is
`max(Δ, Δ|c|, Δ|s|) - (|c| + |s|)` against an axis cell and `max(Δ, Δ|c|, Δ|s|) - 1` against its own kind;
the binding terms give **`pitch = 1/max(|c|, |s|)`**. The first outward position that clears a solid axis
wall column is `0.5 + h` from its centres, so the fringe's outer edge lands **`|c| + |s|` past the wall**.
Both numbers are `>= 1` and equality holds only at the axis limit:

| t | 1/1 | 3/4 | 5/12 | 8/15 | 1/3 | 1/13 | 1/1000 | axis |
|---|---|---|---|---|---|---|---|---|
| half-extent `h` | 0.707107 | 0.700000 | 0.653846 | 0.676471 | 0.632456 | 0.536875 | 0.500500 | 0.500000 |
| pitch `1/max(c,s)` | 1.414214 | 1.250000 | 1.083333 | 1.133333 | 1.054093 | 1.002954 | 1.000000 | 1.000000 |
| protrusion `2h` | 1.414214 | 1.400000 | 1.307692 | 1.352941 | 1.264911 | 1.073750 | 1.001000 | 1.000000 |

That is **T2**, and it is a control, not a remark: `pattern_seeds --selftest` control 10 asserts
`pitch >= 1` and `protrusion >= 1` for all sixteen slopes in the alphabet and equality at the axis.

## 4. Results: E never seats a fringe cell below `ceil(sqrt n)`

Best family E fill of each row **at the delivered side** (so the question is "can E reach `n` without
growing the box?", the only question C2 asks):

| n | delivered | grid `ceil(sqrt n)` | E core | fringe seats | cells | shortfall | certified side `[L_lo, L_hi]` |
|---|---|---|---|---|---|---|---|
| 29 | 5.933833 | 6 | 5×5 | **0** | 25 | **+4** | `[5.000000004, 5.000000004]` |
| 41 | 6.926693 | 7 | 6×6 | **0** | 36 | **+5** | `[6.000000005, 6.000000005]` |
| 53 | 7.822876 | 8 | 7×7 | **0** | 49 | **+4** | `[7.000000006, 7.000000006]` |
| 55 | 7.945771 | 8 | 7×7 | **0** | 49 | **+6** | `[7.000000006, 7.000000006]` |
| 680 | 26.571429 | 27 | 26×26 | **0** | 676 | **+4** | `[26.000000025, 26.000000025]` |
| 733 | 27.571429 | 28 | 27×27 | **0** | 729 | **+4** | `[27.000000026, 27.000000026]` |
| 845 | 29.571429 | 30 | 29×29 | **0** | 841 | **+4** | `[29.000000028, 29.000000028]` |
| 904 | 30.563626 | 31 | 30×30 | **0** | 900 | **+4** | `[30.000000029, 30.000000029]` |
| 971 | 31.678780 | 32 | 31×31 | **0** | 961 | **+10** | `[31.000000030, 31.000000030]` |

**Not one fringe cell fits inside the delivered side on any row**, because the smallest protrusion any
fringe can have is `1`, which is exactly the lattice step — so the strip is never wide enough
(`L_delivered - floor(L)` is 0.93, 0.93, 0.82, 0.95, 0.57, 0.57, 0.57, 0.56, 0.68). The shortfall is
therefore exactly `n - floor(L)^2`: **4, 5, 4, 6, 4, 4, 4, 4, 10 cells** — 0.5 % to 1.0 % of the row,
which is the same number T1 predicts from the other side of the argument. Every fill is certified by the
interval verifier at its own side, and every certificate lands strictly **below** `L_delivered`, so the
losses are *proved*, not merely measured: 3,844 wall bounds and 461,280 pairs on n = 971, 0 violations,
0 inconclusive, tightest certified slack `1.0e-9` (the hairline by construction).

**The expanding denominator, measured.** To see the tilt itself rather than the ceiling, fix a core with
one column of room (`30 × 31` at n = 971, `L = 31.678780`) and sweep `t = 1/q`:

| q | 1 | 2 | 3 | 4 | 5 | 7 | 13 | 30 | 100 | 1000 |
|---|---|---|---|---|---|---|---|---|---|---|
| `h` | 0.707107 | 0.670820 | 0.632456 | 0.606339 | 0.588348 | 0.565685 | 0.536875 | 0.516380 | 0.504975 | 0.500500 |
| pitch | 1.414214 | 1.118034 | 1.054093 | 1.030776 | 1.019804 | 1.010153 | 1.002954 | 1.000555 | 1.000050 | 1.000000 |
| cells | **952** | 958 | 959 | 960 | 960 | **961** | 961 | 961 | 961 | 961 |
| tilted | 22 | 28 | 29 | 30 | 30 | 31 | 31 | 31 | 31 | 31 |
| shortfall | **+19** | +13 | +12 | +11 | +11 | **+10** | +10 | +10 | +10 | +10 |
| void at `L` | 51.5 | 45.5 | 44.5 | 43.5 | 43.5 | **42.5** | 42.5 | 42.5 | 42.5 | 42.5 |

The void falls **monotonically** with the denominator and saturates exactly where the tilt has vanished:
at `q = 7` the fringe *is* the 31st axis column, `961 = 31^2`, and the shortfall is the ceiling's 10 with
nothing left for the slope to give. The whole of tilt's boundary value is the 9 cells between `q = 1` and
`q = infinity` — and all nine of them are recovered by **removing** the tilt. That is T2 as a measurement:
the 45-degree staircase costs 9 cells, the axis limit costs none, and there is no intermediate rung that
pays. The delivered row's own void is 32.5, so even the limit (`42.5`) is 10 behind: the gap is the
`floor(L)^2` ceiling, not the fringe.

## 5. Against doc 72 §5

| criterion | result |
|---|---|
| **C1** certifiable pose | **now met**: `interval_verifier.py` is a second judge for arbitrary rational poses and is in the float audit; 9 family-E poses certified, 7 refusal/pass controls |
| **C2** strictly smaller 40-digit side, zero overlap | **fails on all nine rows.** Best family deficit `-0.32 … -0.44` absolute (`D`/`B` at `ceil(sqrt n)`); family E is `n - floor(L)^2` cells **short** of `n`, so it cannot even be built at the delivered side |
| **C3** gain above `epsilon` and rendering noise | not reached |
| **C4** the metric moves | not reached |

What the run *does* establish, and what it refuses:

1. **T1** closes every integer-lattice construction on 553 of the 1000 rows — the nine targets included —
   by arithmetic. Run 112's uniform loss was not a packer failure; it was `ceil(sqrt n)`.
2. **T2** closes the one-cell wall fringe: a tilted fringe cell's pitch and protrusion are both `>= 1`,
   with equality only at the axis, so family E can never exceed `floor(L)^2` and its tilt is strictly
   dominated by the axis column it replaces (measured: 9 cells at 45°, 0 at the limit).
3. **The corner-nesting packer is real** — A `-1.0`, B `-0.24…-0.88` of side, B tied with D on six rows —
   and its limit is the ceiling, not the packing.
4. **The next route is interior tilt.** The delivered rows beat `ceil(sqrt n)` and carry 56 tilted cells
   each at `3-4-5` and `1/3` in a *band*, not at a wall. A wall fringe cannot do that (T2); a seam between
   two upright blocks can, because both sides of a seam can be sheared by a rational offset without
   paying a per-cell pitch. That is the mechanism run 114 would have to name, and T1/T2 are the falsifiers
   it has to respect.

## 6. Controls and audit

`interval_verifier --selftest`: **7 controls** (axis word exact side 1 and 4 walls; quarter word bracketed
around `sqrt 2`; exact contact refused as inconclusive; `1e-9` hairline certified with slack `> 5e-10`;
half-unit overlap a proven violation; Pythagorean direction exact at `4/5, 3/5` with half-extent `7/10`,
`5-12-13` at `17/26`, `1/1000` approaching `1/2`; side law exact on axis cells and a 45-degree cell
refused in a box of side 1). `pattern_seeds --selftest`: **10 controls** (run 112's five, the ceiling, the
corner packer's three cases, the staircase's count and wall, the domination law over all sixteen slopes,
and the recipe certified end to end). `glm_wheels --audit`: **613 functions, 0 naming `float`**
(`interval_verifier` 17 of them; `pattern_seeds` stays discovery-side and outside, like `relax_angles`).
Every other selftest green, 7 shipped certificates re-verified, `sqscore` still 22.218056945 with 553
beats, `record_guard.py` refuses a stale total presented as current.

Ledgers: `workspace/push/pattern_seeds.json` (families A–D with both packers),
`workspace/push/staircase.json` (family E, with recipes), `workspace/push/staircase_denominators.json`
(the sweep), `workspace/push/interval_checks.json` (the 9 recipes `interval_verifier --check` replays).
