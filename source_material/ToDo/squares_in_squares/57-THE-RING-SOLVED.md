# Run 94 — the ring, solved from its own tangencies

Run 93 read the 10 + 4 + 4 counts correctly and then built the wrong sentence: four corner
modules, scanned against a tangent set, refusing at every tried `(k, word)` under
`ring_unresolved`. This run throws that ansatz away and solves **the census's own sentence**:
a C2 perimeter of 10 axis squares, 4 gap squares wedged across the four wall gaps, and 4
pinwheel squares, each one the unique solution of two declared tangencies in Q(√7). The
result certifies at `N = 18`, `L = 7/2 + ½√7`, clearance exactly 0 — and it is the delivered
n = 18 pose.

It also corrects run 93's reading of the pose. The row is **not** "a polished decimal packing
carrying 0.03–0.07 of slack between module and frame": every centre of the constructed
sentence reproduces the delivered row to **1.8e-9**, which is the size of the 1e-9 shims the
CSV itself writes. The pose was always an exact contact sentence; run 93 was reading the
wrong sentence's gaps.

## 1. The topology, extracted

The 18 squares of n = 18 are, by their exact contact graph:

| role | count | what it is |
|---|---|---|
| perimeter | 10 | 4 corner squares at `(±a, ±a)`; a 3-square run **up** the left wall from the bottom corner; a 3-square run **down** the right wall from the top corner; one square inward on the bottom wall; one inward on the top wall |
| gap | 4 | one square wedged across each wall gap, contacting **both** squares that flank the gap on its own two axes |
| pinwheel | 4 | the four inner squares: two `v`-steps up from each gap square, closing on the **opposite** gap square |

with `a = k + c` and the side `L = 2a + 1 = 2k + 3/2 + (c + s)` (`ring_side`). The gaps this
leaves are not chosen: a vertical wall covers `2k + 2` of its `L`, so its gap is `2c − 1`
(0.8229 at k = 1); a horizontal wall covers 3, so its gap is `2c + 2k − 2` (1.8229 at k = 1).

**Wall faces.** Every perimeter square is flush on at least one face, and the flush faces are
exactly `4k + 10` = **14** — two per corner square (8), one per run square (4), one each for
the bottom-wall and top-wall squares (2). The gate's container is that flushness, so the side
is derived and the wall is not a free parameter.

**Declared tangencies (22).** With `u = (c, s)`, `v = (−s, c)` the word's own axes, a tilted
square at `p` and an axis square at `q` are tangent on the tilted square's axis iff

```
|(q − p)·u| = 1/2 + (|c| + |s|)/2 =: need          (its own face 1/2, the axis square's reach (|c|+|s|)/2)
```

and two tilted squares are tangent along `v` or `u` iff `|(q − p)·v| = 1`, i.e. `q = p + v`.

| group | contact | count |
|---|---|---|
| frame | `bl–l1`, `l1–l2`, `tr–r1`, `r1–r2`, `bl–b`, `l1–b`, `tr–t`, `r1–t` | 8 |
| wedge | `p5–r2`, `p5–br` (right gap), `−p5–l2`, `−p5–tl` (left gap, by C2) | 4 |
| chain | `p5–p6`, `p6–p7`, `p7–p8` and their C2 images | 6 |
| pin | `p7–(−p5)`, `p8–(−p5)`, `−p7–p5`, `−p8–p5` | 4 |

Every one of them is checked as an exact contact (`max_axis slack == 0`, the gate's own
reading) before the gate itself is consulted, so a declaration that has drifted is a refusal
and not a silent pass.

## 2. The solve

Each module is a 2×2 solve — one equation per independent axis, hence a point — in Q(√7):

```
p5 = { p·u = (a, a−2k)·u − need ,  p·v = (a, −a)·v + need }        the right-gap wedge
p6 = p5 + v                                                        one edge-to-edge step
p7 = { p·u = −p5·u + 1 ,  p·v = p6·v + 1 }                          chain step + pinwheel
p8 = { p·u = −p5·u + 1 ,  p·v = p7·v + 1 }
```

and the other four tilted squares are the images under `p → −p`. The solutions, exactly
(denominators 16):

| square | x | y |
|---|---|---|
| `p5` | `9/16 + 3/16·√7` | `−19/16 + 1/16·√7` |
| `p6` | `13/16 − 1/16·√7` | `−15/16 + 5/16·√7` |
| `p7` | `21/16 − 7/16·√7` | `−1/16 + 5/16·√7` |
| `p8` | `25/16 − 11/16·√7` | `3/16 + 9/16·√7` |

No scan, no tolerance, no float: `need` is a field element, the dot products are field dot
products, and the two equations are on the orthogonal pair `u, v` (so the solve is
`p = (p·u)u + (p·v)v`).

## 3. The certificate

`ring_field` → `p_ring(1)`, and the exact gate:

```
ok = True        L = 7/2 + ½√7 (= ring_side(cls, c, s, 1))
clearance = 0    contacts = 26    violations = 0
```

The 26 contacts are the 22 declared ones plus 4 that follow by consequence: the bottom and
top wall squares against the opposite chain end (`b–(−p7)`, `t–p7`) and the two inner
diagonals (`p6–(−p7)`, `(−p6)–p7`). A further 12 pairs share a zero slack on one axis while
another axis still holds them apart — 38 zero-slack axis coincidences, 26 contacts — which is
why the declaration is tested against the strict reading.

The `Ring k=1` cell is registered on the spatial wheel: the wheel is **47/47 certified, 0
refused**, and this cell passes all four witnesses (exact gate at clearance 0, a connected
contact graph with every square touching, `N + V = L²` with `V = 7/2·√7 − 4` (5.260), and the
independent 70-digit Decimal recomputation).

## 4. The census row *is* this sentence

Every one of the 18 constructed centres matches a delivered centre of n = 18 to **1.8e-9**
— the scale of the 1e-9 clearance shims the CSV carries (`0.500000000333`). Control 24
asserts it (< 1e-4, and the measured value is printed), so "n = 18 is constructed from
grammar" is now a checked statement, not a hope. Run 93's slack reading was an artifact of
reading the corner-module sentence's distances instead of this one's.

## 5. Does the grammar generalise? No — and exactly where it stops

The pinwheel's closure contact is `p7–(−p5)` and `p8–(−p5)`: their `u`-separation is exactly
1 by construction, at every `k`, so the question is whether their `v`-offset stays inside a
unit. It does not:

```
2·p5·v + 2 = 5/4 − (4k − 1)/4·√7
```

| k | `2p5·v + 2` | closure pair | verdict |
|---|---|---|---|
| 1 | −0.734313 | `|·| = 0.734 < 1` | **contact** — the pinwheel closes |
| 2 | −3.380065 | adrift by 1.380065 | refuses `ring_chain_adrift` |
| 3 | −6.025816 | adrift by 4.025816 | refuses `ring_chain_adrift` |
| 5 | −11.317319 | adrift by 9.317319 | refuses `ring_chain_adrift` |

The exact closure slack is `−13/4 + (4k − 1)/4·√7` at `k = 2, 3, 5`, positive and growing by
√7 per `k`. So `k ≥ 2` is a **declared law, not a collision**: the sentence is built, its
declared tangency is measured, and the family refuses because the tangency is not one. (At
`k = 2` the drifted chain also happens to overlap the perimeter; the declared law fires
first, and the collision is recorded as a consequence rather than as the reason.)

**And the census's own k = 5 row is not this family's member even in count.** The ring at
`k = 5` would have `N = 4k + 14 = 34` squares at `L = 23/2 + ½√7` — the *same side* the
census records — while n = 151 is a **151-square staircase**: 125 axis squares in **21
staggered columns** (at `±(j + c)` and `±(j + 1/2 − s)` for `j = 0..4`, with 37.5% of them
stacked 12-deep on the outer walls) plus 26 tilted squares, 24 of them at the census word.
Its fill is 151 against `L² = 134 + 23/2·√7 ≈ 164.4`; the ring's is 34 against the same
`L²`. So the Q(√7) family's side law generalises — `2k + 3/2 + (c + s)` is one law for all
five rows — but the **sentence splits**: k = 1 is the ring; k = 5 is a dense multi-layer
staircase, and the ring's single-layer grammar is not what carries it.

## 6. Verification

* `glm_wheels.py --selftest` — **24 controls**, exit 0 (control 24 is the ring: the 22
  declared tangencies, the 26 contacts, the 14 wall faces, the 1.8e-9 census agreement, and
  the `k = 2, 3, 5` refusals with their exact slack; control 5 exercises
  `ring_chain_adrift` on a constructed cell; control 23 now points at control 24).
* `glm_wheels.py` — spin: spatial **47/47 certified**, 0 refused, with the `Ring k=1` row
  (`N = 18`, `L = 7/2 + ½√7`, 4 witnesses); sequences 6/7; lattice 24/28.
* `glm_wheels.py --audit` — **207 decision functions, 0 offenders** (bytecode).
* `grammar_induction.py --selftest` (3/3), `qsqrt2.py --selftest` (11/11),
  `field_triage.py --selftest` (4/4), `scripts/record_guard.py` — all OK.

Nothing here touches `submission.csv` or `WHITEBOARD.md`; no row changed, and no score is
claimed. The ring is a construction result, not a table move: at n = 18 it reproduces the row
we already had.
