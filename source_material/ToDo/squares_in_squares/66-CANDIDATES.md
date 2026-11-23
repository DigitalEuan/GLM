# 66 — the candidate search (run 105)

Run 104 closed the `2k + 4/7` rung's last pair and measured the 28 + 28 band, but every
side it touched stayed at the delivered value. This run leaves row-polishing behind and
attacks the only question that can move a row: **is there a candidate whose exact side is
strictly smaller than the delivered row's?** The instrument is new (`scripts/cand105.py`),
the verdicts are exact, and the answer is recorded whether it is a hit or a refusal.

The standing rule holds: `submission.csv` and the root `WHITEBOARD.md` are untouched,
because nothing here passes the exact gate at clearance 0 with a strictly smaller side.

## 1. The lever, and why the obvious one is dead

**A homothety cannot help.** A delivered row's container *is* the bounding box of its own
squares, so scaling the positions by `lambda < 1` pushes the wall-touching squares out of
the box: `lambda* = 1` identically, with a wall as the binding constraint (control 5 of
the selftest). No similarity transform of a row can lower it.

**What can: a change of extent.** A unit square's bbox half-extent is `(|c| + |s|)/2`,
which is `1/2` at the axis words, `sqrt2/2 = 0.707107` at 45 degrees, `(1 + sqrt3)/4 =
0.683013` at 60 and `(cos72 + sin72)/2 = 0.630037` at 72. Re-labelling a cell's word
therefore *changes the container*, and the whole search is whether some relabelling leaves
a clean packing at a smaller side.

**And the relabelling space has an exact floor.** Every extent is `>= 1/2`, with equality
exactly at the axis words, so re-labelling **every** cell axis simultaneously minimises both
spans. That gives a bound over the *entire* space of word assignments, not just the ones
enumerated:

> **Axis bound.** For a fixed pose, `L_axis` (the bbox with every word axis) is
> `<= L'` for every word assignment. If `L_axis` equals the delivered bbox, **no
> relabelling of any subset of cells can lower this row's side.**

Each candidate is gated with the exact `Q(sqrt 2)` gate at clearance 0, and a win has to
produce a `galois-certificate/1` that the standalone verifier accepts -- two independent
witnesses, as before.

## 2. The candidate rows

The rows were chosen by one declared rule -- the largest relative void `(L^2 - n)/n` in
each range, six above the frontier and four below it -- so "high-leverage" means "the most
area to win", not a hand-picked list:

| n | range | void `(L^2-n)/n` | delivered side | note |
|---|---|---|---|---|
| 330 | band > 324 | 5.880% | 18.692388157318 | snapped pose overlaps 6 times |
| 333 | band > 324 | 5.842% | 18.773753412888 | overlaps 115 times |
| 329 | band > 324 | 5.799% | 18.656854253272 | snapped pose is a packing, 1e-13 words |
| 332 | band > 324 | 5.784% | 18.740417291325 | overlaps 159 times |
| 331 | band > 324 | 5.727% | 18.707106783080 | packing, 1e-13 words |
| 325 | band > 324 | 5.713% | 18.535533907825 | packing, 1e-13 words |
| 68 | small | 13.851% | 8.798795238991 | overlaps 52 times |
| 66 | small | 13.547% | 8.656854251262 | packing, 1e-13 words |
| 67 | small | 13.155% | 8.707106782956 | packing, 1e-13 words |
| 69 | small | 12.927% | 8.827194657504 | overlaps 24 times |

## 3. The hit/miss ledger

**No candidate beats its row: 0 of 10.** The table is the exact result, `Delta L` measured
against the delivered row's own snapped bbox:

| n | closest candidate | `Delta L` (exact) | gate at clearance 0 | verdict |
|---|---|---|---|---|
| 325 | 45 deg -> axis (all) | 0 | refuse, 182 overlaps | no beat |
| 329 | 45 deg -> axis (all) | 0 | refuse, 231 | no beat |
| 330 | motif -> axis (all) | 0 | refuse, 6 | no beat |
| 331 | motif -> axis (all) | 0 | **pass, 0 overlaps** | no beat (same side) |
| 332 | 45 deg -> axis (all) | 0 | refuse, 205 | no beat |
| 333 | motif -> axis (all) | **-9.2835e-4** | refuse, 116 (from 115) | no beat: contact-breaking |
| 66 | motif -> axis (all) | 0 | **pass, 0 overlaps** | no beat (same side) |
| 67 | 45 deg -> axis (all) | 0 | refuse, 14 | no beat |
| 68 | cell 64, axis -> 45 | 0 | refuse, 56 | no beat |
| 69 | t = 1/4 -> axis (all) | 0 | refuse, 34 | no beat |

Two entries are worth reading twice. For **n = 331 and n = 66** the axis relabelling is
itself a *clean packing* at the same side (0 overlaps): a second exact pose for the row,
not a smaller one -- the motif was not load-bearing there. For **n = 333** the relabelling
does lower the bbox by exactly `9.2835e-4`, and the gate refuses it with 116 overlaps
against the delivered pose's 115: the shrink is real and unreachable at the same time.

## 4. Five rows gain a first exact sentence

Five of the ten rows carried exactly-worded angles (worst snap `<= 3.2e-13`) and a clean
gate, but their pose had the table's `1e-9` polish shim, so the clearance was positive and
the certificate schema -- which requires a contact, not a tolerance -- refused them. One
**exact slide** to the nearest contact closes each: the tightest separated pair's own axis
is a unit vector, so moving the cell by exactly its slack along that axis lands the pair at
`|proj| = need`. All five then verify, with clearance exactly 0 and one contact:

| n | certified side `L` (exact) | delivered side | slide | cert |
|---|---|---|---|---|
| 325 | `741421356313/40000000000` = 18.535533907825 | 18.535533907825 | cell 12, along `(1,1)/sqrt2`, `1/sqrt2 - 353553390631/5*10^11` | **verified** |
| 329 | `2332106781659/125000000000` = 18.656854253272 | 18.656854253272 | cell 311, `-y`, `107/10^12` | **verified** |
| 331 | `467677669577/25000000000` = 18.70710678308 | 18.707106783080 | cell 8, `-x`, `53/5*10^11` | **verified** |
| 66 | `4328427125631/500000000000` = 8.656854251262 | 8.656854251262 | cell 51, along `(1,1)/sqrt2`, `1/sqrt2 - 1414213562699/2*10^12` | **verified** |
| 67 | `2176776695739/250000000000` = 8.707106782956 | 8.707106782956 | cell 1, `-x`, `229/10^12` | **verified** |

The certified side equals the delivered side at every digit the table prints -- the slides
are `2e-10` to `1e-10`, the same shim scale run 102 measured -- so these are **not**
improvements: they are the first *tight, certified* sentences for those rows. The shipped
certificate document held seven cells (tile2, ring18, staircase149/150, block45_5_4,
block45half_17_14, slope21) and none of these rows, so each is a first for its row.

## 5. The obstacles, named exactly

1. **Wall-pinning (9 of 10 rows).** For nine rows the axis bound equals the delivered bbox
   *exactly*. By the bound of section 1 that is a proof, not a failed search: the bbox is
   set by minimal-extent (axis) cells, so no word assignment of any subset of cells can
   lower the side. The remaining degree of freedom is position, and doc 80 already showed
   the wall ring cannot come in at `1e-7` on 553 rows.
2. **Contact-breaking (n = 333).** The one row whose relabelling would lower `L` pays for
   it in contacts: 116 overlaps against 115. The shrink and the packing are incompatible at
   these positions.
3. **Overlap at the snapped angles (5 rows).** n = 330, 333, 332, 68 and 69 are not packings
   at their snapped words (6, 115, 159, 52 and 24 overlaps). For the three rational-word
   rows (333, 68, 69) run 104's positional repair was tried and refused (113, 52 and 24
   overlaps left); for 330 and 332 the row carries the 45 degree word and that repair is
   rational-only, so it was not attempted. The obstacle is geometric overlap, not field
   mismatch -- the field test below is clean for all of them.

## 6. The off-axis motifs, refused or certified exactly

The task's own suggestions were checked as algebra rather than sampled.

**The strip penalty.** A lone tilted square adds `|c| + |s| - 1` to a wall:

| word | penalty |
|---|---|
| axis | 0 |
| 60 deg (hexagonal) | `(sqrt3 - 1)/2 = 0.366025` |
| 45 deg | `sqrt2 - 1 = 0.414214` |
| 72 deg (golden) | `cos72 + sin72 - 1 = 0.260074` |

**Hexagonal is expressible -- in a field the alphabet did not have.** `sin60 = sqrt3/2` is
refused by `Q(sqrt 2)`, `Q(sqrt 5)` and `Q(sqrt 7)` (exactly: for `sqrt(r) = a + b sqrt d`,
`a b = 0`, so `r` and `r/d` would both have to be non-squares -- they are). It needs
`Q(sqrt 3)`, and this run builds that field's first certified sentence: two squares
touching at one corner, `N = 2`, side `3/2 + (1/2)sqrt3 = 2.366025`, one contact,
certificate **verified**. Its 45 degree analogue is `1 + sqrt2 = 2.414214`, and the axis
pair is `2`. So at `N = 2` the hexagonal tilt *beats* the 45 degree one by `0.0482` and
still loses to the axis row by exactly the strip penalty `0.366025`.

**Golden is not expressible at all.** `cos72 = (sqrt5 - 1)/4` is in `Q(sqrt 5)`, but
`sin72 = a + b sqrt5` would force `256 a^4 - 160 a^2 + 5 = 0`, whose discriminant
`20480 = 64^2 * 5` is not a square: the word is a degree-4 object, so *no* `Q(sqrt 5)` rung
can carry a 72 degree square. That is a field mismatch, not a spacing problem.

## 7. What is and is not claimed

Established: 0 of 10 candidates beat their row; the axis bound is a global floor over word
relabellings, so nine rows are *provably* closed to relabelling; n = 333's `-9.2835e-4` is
contact-blocked; five rows gain their first tight certified sentence (at the delivered
side, `2e-10`-scale slides); the first certified `Q(sqrt 3)` sentence and the two field
refusals. `submission.csv` and `WHITEBOARD.md` are untouched, and no score is claimed.

Not claimed: any improvement; that relabelling exhausts *pose* changes (it does not -- doc
80's wall-ring test is the instrument for those); a general law beyond these ten rows.

Next constructive idea, now that the extent lever is closed: the only trade left is
extent *for* contacts. Take a certified row (section 4 gives five with a full contact
graph), move one interior cell inward onto a new contact, and spend the freed shim by
sliding the wall cell that sets the bbox -- a two-cell move, which is exactly the
neighbourhood the one-cell and whole-motif searches could not reach.
