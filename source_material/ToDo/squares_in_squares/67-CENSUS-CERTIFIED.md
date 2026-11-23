# 67 — the census certified, the 45 degree repair, and the coupled move (run 106)

Run 105 certified five rows, one at a time and by hand. This run asks whether that was a
property of five rows or of the table: it is the table's census. **552 of the 553 rows whose
snapped words are exact now carry a verified `galois-certificate/1`** — 547 of them for the
first time — the two asked rows still stay blocked with exact reasons, and the two-cell trade
that doc 66 §7 named cannot exist at depth one: in the two certified sentences tested, every
neighbour of every bounding-box cell has *zero* room in all eight directions.

The instrument is `scripts/cand106.py` (25 decision functions, float-free, 5 controls); the
ledger is `workspace/push/cand106.json`; the representative certificates are
`workspace/push/cand106_samples.json`.

## 1. The screen, the slide, the count

**The census (exact, over all 1000 rows, 10.5 s).** A row is in the census when every one of
its angles snaps to a unit word of `rat47`'s alphabet at `<= 1e-9`. That is **553 rows**. The
worst row in the table is n = 743, whose nearest word is 1.27 away — it is not a sentence and
no certificate is possible for it, so it is out of scope by measurement rather than by choice.

**The per-row procedure**, in this order:

1. `survey` — one exact `Q(sqrt 2)` SAT pass that returns, together, the overlapping pairs and
   the tightest separated pair's smallest slack (a `Fraction` fast path when every word of the
   row is rational; `survey_rat` is 3-6x faster and is identical on those rows by the selftest's
   control 2).
2. Overlaps present -> the row is not clean; record it and stop. (No census row took this branch
   after the repair of section 2: 0 of 553.)
3. `slide_best` — slide the tightest pair's second cell by the smallest exact step that closes
   **every** positive axis of that pair, over all eight signed directions.
4. `certify_state` — the exact gate at clearance 0 plus a certificate, written and verified.

**The tally** (batch of 2441 s):

| category | rows | note |
|---|---|---|
| census | 553 | snapped words within `1e-9` |
| **certified** | **552** | clearance exactly 0, verified certificate |
| already tight, no pair | 1 | n = 1: a single square has no pair to contact |
| not clean | 0 | — |
| other | 0 | — |

Of the 552, **550 are closed by a slide**: 549 by a single-axis slide, and one by an all-axis
(diagonal) slide. The diagonal one is the case that shows why "close every axis" is the right
rule rather than "close one": **n = 634**'s tightest pair has *both* separations at
`1 + 77/10^12`, so closing y alone leaves x open by `77/10^12` and the pair is still separated
(its SAT slack is the max over axes, so the sentence would have had no contact). The move that
works is `t = 77/10^12 * sqrt2` along `(1,1)/sqrt2`, and it certifies at `L =
6426776695777/250000000000 = 25.707106783080` with **2 contacts**.

**The two rows that were not clean are closed by the repair of section 2**, not by a slide:
n = 678 and n = 679 each carry exactly one overlapping pair at their exact words (slack
`-1 + 1414213561901/2*10^12*sqrt2`), one diagonal step of that same exact size fixes it, and
both certify at `L = 1326776695393/50000000000 = 26.535533907860` with 1 contact.

**How many are new.** Run 105's five rows (325, 329, 331, 66, 67) are inside the 552 and carry
the same sides, digit for digit (`741421356313/40000000000`, `2332106781659/125000000000`,
`467677669577/25000000000`, `4328427125631/500000000000`, `2176776695739/250000000000`), so the
newly certified count is **552 - 5 = 547**. The shipped document held seven cells, none of them
from these rows.

**Representative re-verification (independent of the producer).** Three certificates spanning
the census — first, middle and last certified row — were written out as a document and checked
by the standalone verifier, which shares no code with the gate:

```
$ python3 scripts/verify_certificates.py workspace/push/cand106_samples.json
  verified cand105_n2_d2: Quad(2), N = 2, L = 2, contacts = 1, clearance = 0, void = 2
  verified cand105_n427_d2: Quad(2), N = 427, L = 1312500000119/62500000000,
      contacts = 1, clearance = 0, void = 54687500312375000014161/3906250000000000000000
  verified cand105_n1000_d2: Quad(2), N = 1000, L = 16000000000969/500000000000,
      contacts = 1, clearance = 0, void = 6000000031008000000938961/250000000000000000000000
  3 verified, 0 failed
```

The certificates are the census's *own* poses: no cell's word is changed and the slide is the
table's own polish shim (the steps run `1e-12` to `1e-9`). This is a change of *status*, not of
the table: 547 rows stop being "a pose with a tolerance" and become a sentence with a witness.

**One side does move, by exactly the shim.** 551 of the 552 certified sides are identical to the
delivered side; the exception is **n = 2, certified at `L = 2`, which is exactly `1/10^9` below
the delivered `2 + 1/10^9`** — its slide moved the cell that defines the bbox, and the bbox came
in by the whole shim. It is not a gain: two unit squares need a span of 2 in some direction, so 2
is the row's own floor and the 2 x 1 grid's side as well, and a side of exactly 2 is not *below*
that grid — the guard's 553/1000 count does not move.

## 2. The 45 degree repair, generalised and run on n = 330 and n = 332

Run 104's positional repair moved one cell of an offending pair along a SAT axis of that pair,
with a **rational** step, because every row it touched was worded in `Q`. The 45 degree rows are
not: their axes are `(1,1)/sqrt2 = Q2(0, 1/2)` and `(-1,1)/sqrt2 = Q2(0, -1/2)` — field elements
with a zero rational part, so the generalised step is

```
t = (sign(proj) * need - proj) / k,      k = +d.q  if the second cell moves,  -d.q  if the first does
```

with `d` one of the eight signed unit directions (`x`, `y`, `(1,1)/sqrt2`, `(-1,1)/sqrt2` and
their negatives) and the smallest `|t|` that lowers the overlap count chosen; the exact gate, not
the arithmetic, is the arbiter. The steps are exact `Q(sqrt 2)` values end to end (`Decimal`
never enters — the first draft's `Decimal(1).sqrt()` was removed as inexact before any verdict).

| n | start overlaps | after the repair | moves | verdict | certified side |
|---|---|---|---|---|---|
| 330 | 6 | **3** | 4 | refused: the next move does not lower the count | — |
| 332 | 159 | **159** | 1 | refused: the first move does not lower the count | — |
| 678 | 1 | **0** | 1 | **certified**, 1 contact | `1326776695393/50000000000` |
| 679 | 1 | **0** | 1 | **certified**, 1 contact | `1326776695393/50000000000` |

**n = 330 is half-solved, exactly and visibly.** Four moves each lower the count by one:

| move | pair | cell | direction | exact step | overlaps after |
|---|---|---|---|---|---|
| 1 | 14, 32 | 14 | `-x` | `212180669517/101000000000000` | 5 |
| 2 | 28, 32 | 28 | `-y` | `1422316677/789062500000` | 4 |
| 3 | 80, 101 | 80 | `-x` | `58927632333/845*10^11` | 3 |
| 4 | 195, 216 | 195 | diagonal | `-1 + 1414025346279/2*10^12*sqrt2` | 3 |

The fourth move is the 45 degree case working as designed — a diagonal step on a 45 degree pair
— and after it the loop stops because the fifth move (pair 216, 233) leaves the count at 3. The
three survivors, (216, 233), (224, 247) and the clearance `-1/2 + 352353905641/10^12*sqrt2` that
binds them all, are mutually coupled: each is fixed by moving a cell that the next pair needs.
This is the same contact-blocking shape run 105 found at n = 333, now on a 45 degree row and at
three simultaneous pairs.

**n = 332 does not start.** Its 159 overlaps are dense enough that the first move (pair 22, 191,
cell 22, `+y`, `41204100433/10^12`) leaves 159: the pair separates, another pair closes in the
same direction, and the count is unchanged, so the loop stops after one step. Neither row
closes into a certificate, and neither is claimed to.

## 3. The two-cell coupled move: no depth-one instance exists

Doc 66 §7 named the trade: move an interior cell onto a *new* contact to free slack, then spend
that slack by pulling the bbox-defining wall cell inward. The prototype tests it on two
certified rows (n = 66 and n = 325) by exhaustive enumeration rather than by search heuristics:

- **walls** — every cell touching one of the four bbox faces (their outer face *is* the wall);
- **partners** — every cell bbox-adjacent to a wall cell (the cells that could free its room);
- **directions** — all eight signed unit directions for the partner's first move;
- for each combination: the largest first move of the partner that stays legal (`tau_p`, exact
  by the pair's own slack), the room the wall cell then has inward, and whether the wall can
  move in by a strictly positive `tau`.

| n | wall cells | partner slots | combinations | legal first move with `tau > 0` | verdict |
|---|---|---|---|---|---|
| 66 | 30 | 152 | 1216 | **0** | no-combination |
| 325 | 72 | 360 | 2880 | **0** | no-combination |

Every combination in both rows has `tau = 0` — not "small", not "below rounding", but exactly
zero, and no combination failed a gate (so the zeros are not turndowns of an illegal move: the
moves do not exist). The reading is that these two sentences are **jammed at depth one**: every
neighbour of every bbox cell is already in contact along a narrowing axis in every one of the
eight directions, so there is no interior slack to spend and no two-cell trade to make. The
obstruction is not the search budget — it is that the free space is exactly zero.

That the mechanism itself is sound is a control, not an assumption: selftest control 5 builds a
4 x 3 sentence in which the same enumeration finds the interior move that frees room and the
wall move that spends it, shrinking the box from 4 to **3**. So the refusal above is a property
of the certified rows, not of the instrument.

A first run of the prototype tested four directions instead of eight and reported the same
verdict; it was wrong to trust — a *widening* axis can free room in the four-direction run's
blind spot. The eight-direction enumeration doubles the combination count, and every added
direction is also exactly zero, so the verdict survives the correction; the correction is
recorded here because the first number was not the honest one.

## 4. What is and is not claimed

**Established.** 553 census rows (exact screen, `1e-9`); **552 certified** at clearance exactly 0
with verified certificates, **547 of them for the first time**, the other 5 being run 105's; the
three exceptions named exactly (n = 1 has no pair; 678 and 679 had one overlap each and are
certified by the 45 degree repair); three representative certificates re-verified by
`verify_certificates.py` alone; the 45 degree repair works as a move (n = 678 and 679 close, n =
330 goes 6 -> 3) and does not close n = 330 or n = 332, with the exact steps and the exact
clearance that blocks them; the coupled two-cell trade has **no instance at depth one** on
n = 66 (1216 combinations) or n = 325 (2880), with the mechanism proven live by a control that
shrinks a box 4 -> 3.

**Not claimed.** Any improvement: no certified side is below its delivered side by more than the
table's own shim (551 are identical, and n = 2 is `1e-9` lower at its own floor of 2); that the census is the whole table (447 rows are not
sentences at `1e-9`, and 1 row — n = 743 — is off by 1.27); that depth-two chains are impossible
(the prototype tests depth one, no more); that n = 330's three survivors are unresolvable (they
are *coupled* under a single-cell move, which is a statement about the move, not about the row).
`submission.csv` and the root `WHITEBOARD.md` are untouched, and no score is claimed.

**Next.** The coupled move's honest successor is depth two on the same two rows: a *pair* of
interior cells whose joint free space pays for one wall move, which is the first case this
enumeration cannot see. n = 330's three coupled overlaps are the natural target for the 45
degree version of the same chain, since section 2 leaves them at one exact clearance.
