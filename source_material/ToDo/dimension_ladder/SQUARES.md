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

## 3. The one restriction it does explain — and it is the whole answer

The squares problem is the axis-aligned section **by construction**: fixing orientation kills the
offset `m·(1,1,0)` that produces the hexagonal gain, and that offset is precisely what is not in
`L`. So the gap between this table's geometry and the plane optimum is exactly **2/√3 in linear
scale**, and it is not recoverable by better search — it is the price of the orientation
restriction. That is the sentence worth keeping from the whole side-quest:

> The squares-in-squares table lives on the (001) slice; the plane optimum is the (111) slice; the
> ratio between them is 4/3 in the square, and it is created by a stacking offset the problem
> forbids.

The project has already *measured* the shadow of this without naming it: `16-LEECH-MAP.md` reports
the integral-section test separating tilted rows **87/87 illegal** from untilted **168/168 legal**,
and `29-SAT-PROBE-AND-RESOLUTION.md` §B.2 reports that √2 is not a lattice point at any resolution.
The bridge supplies the mechanism: a section is integral iff its plane's coordinates stay in a ring —
ℚ for the axis-aligned lattice, ℚ(√2) for 45°. That makes the existing `leech_map.py` mapping
(number field → laminated-tower level, 87 % exact) the **section-class** ladder, and the bridge is
its geometry, not a replacement for it.

## 4. If effort is to be spent, the two real options

**(a) Cubes in cubes — the only place the dimension ladder touches this project.** The bridge's
exact statement becomes a question: is the 3D optimum the *extrusion* of the 2D one? Extrusion is
always feasible (extend every square's `(x,y)` to a cube and leave `z` free), so `s₃(n) ≥ s₂(n)`
for free; equality is lamination, and the first row where extrusion fails is where a genuine density
ladder starts. Cost: a 3D analogue of `declp` (box in box, `6n` walls, `3n+1` variables) plus a gate
and a `verify` — one instrument, one run. Payoff: a fact about *packing*, not about this table's
score, which stays 22.218056945 either way.

**(b) A per-row section-class label.** Cost: small — `split_lattices` and `lattice_coords` already
exist. Payoff: small, because `22` and `23` already do most of it and the label does not move the
score.

Recommendation: **(a) only if the ladder itself is the goal**, and nothing at all if the goal is the
score. Neither improves the delivered table, and the bridge should not be imported into
`squares_in_squares` as machinery — the honest use is §3's sentence, which is a *diagnosis* of why
"grid" is the right family and hex cannot be.

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
