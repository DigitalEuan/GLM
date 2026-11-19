# Can the bridge be used for squares-in-squares?

Short answer: **not as an engine, yes as a diagnosis.** The bridge optimises a bulk centre density
of a translation-invariant point set with free rotation. Squares-in-squares has a wall, a fixed
orientation, and a quantity whose ceiling is *attained*. So nothing in the bridge can produce or
bound an `L`. What it can do is name, exactly, why this project is one rung below the plane optimum
and why that gap is structural rather than a tuning failure.

## 1. The objective has no ladder here

| n | L | density `n/L²` | defect `1 − n/L²` | score `L/√n − 1` |
|---:|---:|---:|---:|---:|
| 2 | 2 | 0.5000 | 5.00e−1 | +0.4142 |
| 4 | 2 | **1.0000** | 1.0e−9 | 0 |
| 25 | 5 | **1.0000** | 6.4e−10 | 0 |
| 100 | 10 | **1.0000** | 3.6e−10 | 0 |
| 961 | 31 | **1.0000** | 3.0e−10 | 0 |
| 1000 | 32 | 0.9766 | 2.34e−2 | +0.0119 |

(the zeros are the delivered coordinates' own rounding, ≤ 1e−9 in `extent`; summing `L/√n − 1` over
all 1000 rows reproduces **22.218056945**, so this is the delivered table, not a copy)

31 rows are perfect squares (n = 1, 4, …, 961) and on every one of them the density is exactly 1:
the ceiling is *attained, 31 times*. In the plane-lattice problem the ceiling is never attained
(δ = 1/√12 ≈ 0.2887 of area, approached only in the limit), which is what makes "which lattice is
denser" a question with an infinite ladder of answers. Here it is a question with a trivial answer
on 31 rows, and on the rest the content is the **boundary defect**, which decays with n instead of
converging to a bulk constant. A density ladder has no rungs to climb.

The discrete level this project actually climbs is `k = ⌈√n⌉` — a *count*, not a dimension. Above
1000 the ladder is even closed by construction (`08-BEYOND-1000.md`: 100 % of the easy rows are
axis-aligned `k`-lattices, and the `k²−i` rows are proved optimal).

## 2. The bridge's objects are absent, and the census shows it

| row | variables `2n` | binding contacts | binding walls | wall is |
|---:|---:|---:|---:|---|
| 18 | 36 | 26 | 14 | **needed** (26 < 36) |
| 20 | 40 | 55 | 18 | not needed |
| 60 | 120 | 195 | 27 | not needed |
| 100 | 200 | 342 | 40 | not needed |

(from `workspace/push/flipgrow_census.json`, run 71)

In a lattice, the "wall" is the Voronoi cell and its size *is* the determinant — every constraint is
the same constraint repeated by symmetry. In this table the wall binds only 14 of 72 wall
inequalities at n = 18 and 40 of 400 at n = 100, while the contacts alone over-determine every row
at n ≥ 20. So the over-determination that run 71 measured is a **contact** phenomenon, not a
container-lattice one, and the determinant/Gram bookkeeping of `bridge.py` has nothing to attach to.

## 3. What the bridge does say — and what the 2/√3 is *not*

The squares problem is the axis-aligned section of this lattice family, by construction. Two
statements follow, and they must be kept apart:

**(i) A ratio between two sphere relaxations, which is not a cost to squares.** The (001) section
induces the square lattice, `δ² = 1/16`; the (111) section induces A₂, `δ² = 1/12`. The linear ratio
is `2/√3 ≈ 1.155`, and it is **a comparison between two disc packings**. Squares are not discs: the
square lattice tiles the plane at density **1**, and so does the hexagonal one, in every section. So
`2/√3` is not a gap this table has to close, not a penalty it pays for fixing orientation, and not a
bound on any `L`. Rotating gains nothing, because nothing is being lost — a tiling of the plane is
already full. An earlier draft of this note called it "the price of the orientation restriction";
that was wrong, and the number constrains only a problem whose objects are discs.

**(ii) The section and its ring, which is the transferable part.** What the bridge genuinely supplies
is vocabulary: a table row is a *section*, and a section is addressable in integers only if its
plane's coordinates stay in a ring — ℚ for the axis-aligned lattice, ℚ(√2) at 45°. The project has
already measured the shadow of this: `16-LEECH-MAP.md` reports the integral-section test separating
tilted rows **87/87 illegal** from untilted **168/168 legal**, and
`29-SAT-PROBE-AND-RESOLUTION.md` §B.2 reports that √2 is not a lattice point at any resolution. That
makes the existing `leech_map.py` mapping (number field → laminated-tower level, 87 % exact) the
**section-class** ladder, and the bridge is its geometry, not a replacement for it. The restriction
this exposes is real, but it is a restriction on *addressability*, not on density — and it says
nothing about whether a given `L` can be beaten.

## 4. If effort is to be spent, the two real options

**(a) Cubes in cubes — built and run.** `squares_in_squares/35-CUBES-IN-A-CUBE.md` with
`declp3.py`: the declared-axis LP one dimension up, judged by an exact gate that reads the recorded
coordinates as `Fraction`s. The question was whether the 3D optimum is the *extrusion* of the
delivered 2D row. Answer: **yes at n = 2, 3, 4 and 9, and no at 6, 7, 8, 12, 16, 20.** Two cubes in a
box of side `L < 2` must intersect, so `L(n) ≥ 2` for `n ≥ 2`, and the 2×2×2 grid gives 2 for
`n ≤ 8` — the 3D optimum is exactly 2 there, against 2.7071 (n = 5) and 3 (n = 6, 7, 8) for the row.
The cube grid also beats the row at n = 10, 12, 16, 20. The score is untouched (22.218056945).

**One correction to that answer (run 74).** At n = 5 and n = 10 there is no extrusion to compare:
a square at π/4 is not a unit cube, so the "extruded" state is a set of overlapping cubes and
`declp3.json`'s own `extrude_ok` is `False`. The comparison there is between the 3D grid and the 2D
*problem*, not between two packings, and the "extrusion is rigid" reading of `desc(extr) = L2`
fails at exactly those two rows (the LP proposes a larger side and the descent refuses an illegal
start). The conclusion is unchanged — 3D needs 2 where 2D needs 2.7071 — but the object is the
problem, not the extruded state.

**And then the question closed completely — for axis-parallel cubes.** Run 73
(`36-CUBE-GRID-IS-OPTIMAL.md`) proves `L(n) = ⌈n^{1/3}⌉` for *every* n, in every dimension, by
counting centres in `m^d` sub-boxes: all centres sit in a box of side `L − 1`, a sub-box of side
`< 1` holds at most one, so `n > k^d ⇒ L ≥ k + 1`, which the `k`-grid attains. So `L(9) = 3`,
nothing beats the cube grid at any `n`, and the 3D question has no ladder at all.

**The scope matters, and run 74 wrote it down where it belongs.** The proof never rotates anything:
it is a theorem about axis-parallel cubes, and in 2D about axis-parallel squares. That restriction
is not pedantic — it is exactly the restriction this project lives inside. The delivered table's
n = 5 row is `2.707107 < 3 = ⌈√5⌉` because one square sits at π/4, so in 2D the axis-parallel
bound is *true and immediately beaten outside its class*. So `L_d(n) = ⌈n^{1/d}⌉` is the optimum of
the axis-parallel class, nothing more; a rotated cube is outside it and is an open problem this
project has no instrument for. Read `BRIDGE.md`'s "the dimension step is free of information" in
that light: it is free because rotation was removed, and rotation is the whole score down here.

**What that means for this note — and it is the real finding.** The same argument in two dimensions
says *axis-parallel* squares can never beat `⌈√n⌉` — and since it applies only to that class, the
n = 5 row (`2+1/√2 ≈ 2.7071` against 3) shows the class boundary is the whole game. So every beat in
the 1000-row table must contain a rotated square — and it does: **447 rows are axis-aligned and all
sit exactly at `⌈√n⌉`; 553 rows beat, and none of them is axis-aligned; 447 + 553 = 1000.** Rotation
is not a feature of the score, it *is* the score. Contrast that with `BRIDGE.md`, where the lattice carries the plane optimum as a
section and the dimension step is free of information: here the dimension step is free of information
too, but the rotation step is everything. The bridge and the table are two different ladders — section
class versus orientation — and only the second one has rungs this project can climb.

**(b) A per-row section-class label.** Cost: small — `split_lattices` and `lattice_coords` already
exist. Payoff: small, because `22` and `23` already do most of it and the label does not move the
score.

Recommendation: (a) is done and answered; (b) is score-neutral. Nothing in this note improves the
delivered table, and the bridge should not be imported into `squares_in_squares` as machinery — its
honest use is §3: the section vocabulary, and the reason the plane result transfers to the table's
*addressing* and not to its `L`.

## 5. Re-running the numbers in this note

```bash
cd source_material/ToDo/squares_in_squares
python3 - <<'EOF'
import csv, math, sys
from collections import defaultdict
sys.path.insert(0, 'scripts'); from sqscore import extent
by = defaultdict(list)
for d in csv.DictReader(open('workspace/submission/submission.csv')):
    by[int(d['n'])].append((float(d['x']), float(d['y']), float(d['angle'])))
L = {n: extent(v) for n, v in by.items()}
print(sum(L[n]/math.sqrt(n) - 1 for n in L))          # 22.218056945
print(sum(1 for n in L if math.isqrt(n)**2 == n))     # 31
EOF
```
