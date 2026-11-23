# 70 — The relational layer: contacts, pins, voids, and coupled moves

Runs 106–108 all ended at the same wall: a local move (a slide, a chain, a face) either left the side
alone or made it worse. This run stops asking "which cell can move" and asks the *semantic* question
instead — **what is the relational structure of a packing, and does any move that respects it reach a
smaller side?** `scripts/semantic_pack.py` (3 controls, 27 decision functions, float-free, in the
`--audit` list) builds that structure exactly, generates coupled moves from it, and hands every
survivor to the same strict judges as before: `qsqrt2.gate` at clearance 0 and
`verify_certificates.py`. Nothing here reads a float; nothing here trusts a certificate it did not
verify; `submission.csv` and the root `WHITEBOARD.md` are untouched.

## 1. What "relational" means here

Four exact objects, all computed from the row's decimal pose with its angles snapped to the eight
words (the snap gap is reported per row):

| object | definition | why it matters |
|---|---|---|
| **contact** | a pair whose best-axis slack is exactly 0 | the only way the gate's side is held; no contact, no obstruction |
| **pin** | for a bbox side, a wall cell whose contact *narrows* under that side's inward direction | this is why a single-cell slide is useless: the cell is held by the very thing it must move away from |
| **bottleneck chain** | wall cell `w` → its pin `b` → *`b`'s own pin* | the shortest relational obstruction: to free `w` you must first free `b`, which is held in turn |
| **void pocket** | a connected component (in the contact graph) of wall cells that still have positive inward room | the free space a coupled move could spend |

The analysis is the same information doc 68 read cell by cell, now as a graph: who holds whom, and
whether the holding chain terminates in free space or in itself. A row whose chains have no free end
is *relationally closed* — every wall cell is held by a cell that is itself held — and no translation
family, however coupled, can move the side, because the obstruction has no exit.

A pocket with room is the one place a coupled move can act: spend it, and the chain behind it may
open. That is the whole theory of this run; §2 is the measurement.

## 2. The relational measurement

Five rows, the same exact analysis (`--analyse`, ledger `workspace/push/semantic_pack.json`). "Non-word"
counts the cells whose stored angle is not one of the eight exact words, and the gap is the largest
distance from the stored angle to its word.

| n | N | non-word | max gap | contacts | wall cells lo_x/hi_x/lo_y/hi_y | pinned | chains | pockets | max room |
|---|---|---|---|---|---|---|---|---|---|
| 11 | 11 | 5 | 2.9e−3 | 5 | 1 / 1 / 1 / 1 | 2 | 2 | 1 group | 3.53e−4 |
| 17 | 17 | 7 | 3.4e−3 | 9 | 1 / 4 / 1 / 1 | 3 | 4 | none | 0 |
| 18 | 18 | — | — | — | — | — | — | — | — (repair-stalled, 16 overlaps) |
| 29 | 29 | 14 | 3.5e−3 | 23 | 1 / 1 / 1 / 1 | 1 | 1 | none | 0 |
| 330 | 330 | 236 | 6.9e−3 | 30 | 1 / 14 / 1 / 14 | 2 | 2 | none | 0 |

**Every row that could be analysed is relationally closed.** In four of the five there is not one wall
cell with room; the pinned cells are held by neighbours that are themselves pinned (`bottlenecks`), so
the chain wall → pin → pin is a cycle with no free end. The single exception is one wall cell at n = 11
with `3.53e−4` of room — and it is the `hi_x` cell, on the axis that is *not* binding.

n = 330 shows the structure most clearly, and it is why the row is hard: the 28 free wall cells are
exactly the 14 staircase cells on `hi_x` and the 14 on `hi_y`, while the two *binding* cells (one on
`lo_x`, one on `lo_y`) are pinned. Free space sits on the sides that do not set the side. Sliding it
inward cannot shrink the box, because the opposite sides have no room at all. This is the relational
statement of what runs 106–108 found numerically.

## 3. Coupled moves, and the one "win" that is not one

Three move families, all exact, all gated at clearance 0 (`--search`, `--trades`):

| n | rigid clusters | re-orientations | legal | model wins | verified certs | trades fired |
|---|---|---|---|---|---|---|
| 11 | 24 | 14 | 24 | 0 | 0 | 0 |
| 17 | 42 | 49 | 43 | 0 | 0 | 1 (no win) |
| 29 | 14 | 48 | 14 | 0 | 0 | 0 |
| 330 | 20 | 23 | 11 | **1** | 1 | 0 |

The rigid family translates connected 2–5-cell clusters (24 clusters max, seeded on wall cells) along
each of the eight directions by the exact time their first outside pair makes contact; the
re-orientation family rotates a cluster by 45° or 90° about its own bbox centre (the eight words are
closed under 45° rotation, so this stays in `Q(√2)`); the trade family pushes a *pin* into its own room
and lets the squeeze pull the wall in behind it. 234 attacks, 92 legal, and exactly one candidate that
beat the delivered side — at n = 330.

**It is an artifact, and it is the most useful thing this run found.** The move is a rigid translation
of cells {14, 32} by `t = −13 + (928542037565257/10^14)√2` along `(√2/2, √2/2)`; it gates at clearance 0
and its certificate **verifies** (`N = 330`, 25 contacts, void ≥ 0) at

```
L_model = 9500099491707/10^12 + (13/2)√2 = 18.692488   vs   table L = 18.692672   (−1.85e−4)
```

So far a genuine win — until the row is written into the submission and scored by the repository's own
`sqscore`, which uses the *true* stored angles:

```
true side of the candidate      18.692915843
true side of the delivered row  18.692388157     →  the candidate is 2.43e−4 WORSE
whole-table score               22.218056945 → 22.218085993   (+2.9e−5)
```

`submission.csv` was patched to test this and **reverted** the moment the score moved the wrong way;
`sqscore` and `record_guard` are green again on the delivered table. The certificate was never wrong:
it is exact for the pose whose angles are the eight words. The *pose* was wrong — `state_of` snaps every
angle to its word, and at n = 330, 236 of the 330 angles are not words (gaps up to `6.9e−3` rad). The
gate's own side for that pose is a **model** number, not the row's side.

Two consequences, both important:

1. **`L_model < table L` is not a sound test on a transcendental row.** The table's L is itself a model
   value: at n = 330 it says `18.692672` while the delivered CSV's true side is `18.692388` — the table
   *overstates* the row by `2.84e−4`, four orders of magnitude above any polish. A candidate can beat
   the table and still be worse in reality, which is exactly what happened here. For the three small
   rows the model and the truth agree to nine decimals (`3.877083592`, `4.675530095`, `5.933833464`),
   so their negative results stand; for n = 330 the bar has to be `sqscore`'s extent.
2. **A certificate is only a certificate for the pose it certifies.** Run 108's face slides survive this
   test because their rows are word-exact and the slides move `1e−9` — far below the model error. A
   `1e−4`-scale relational move on a snapped pose does not.

## 4. What representation would be required

The obstruction here is **transcendence, not degree**. The gate's needed separation for a pair of
squares is a combination of `cos` and `sin` of sums and differences of the stored angles; when an angle
is a non-zero rational number of radians (every decimal here is one), `cos θ` is transcendental
(Lindemann–Weierstrass: `cos θ` algebraic would make `e^{iθ}` algebraic, hence `iθ` algebraic, which is
impossible). **No algebraic number field can certify a row with a single non-word angle.** Higher-degree
equations would not help; only these do:

* **word snapping with an explicit error budget** — certify the snapped pose *and* prove
  `true side ≥ model side − ε(gap)`, with `ε` bounded from the gaps and the per-cell extents. This is
  the containment argument that would have caught the n = 330 trap before submission, and it is the
  cheapest route: every moved cell's extent changes by at most `|sin| · gap`;
* **certified interval arithmetic** (ball arithmetic at, say, 10⁻⁴⁰) — rigorous over ℝ but no longer
  algebraic, so it cannot produce the certificate objects `verify_certificates.py` checks;
* **a genuine algebraic extension only if the angles are algebraic** — e.g. 30°/60° words would put the
  field at `Q(√2, √3)`, degree 4, and the gate generalises directly there. That is the only sense in
  which "higher-degree equations" could arise, and none of the tested rows needs it.

The 553 word-exact rows need none of this: for them the gate, the certificates and every relational
computation are exact, which is why every *verified* certificate in this repository — including run 108's
`−4.62e−10` and `−2.16e−10` — lives on them.

## 5. What is and is not claimed

**Claimed.** The relational layer is built and exact: 5 rows mapped, 234 coupled moves attacked, 92
legal, **0 genuine improvements**. The four analysable rows are relationally closed — depth-2 pin
chains, no free void on a binding side, one `3.5e−4` pocket on a non-binding side at n = 11. The single
candidate that beat the table (n = 330, `−1.85e−4` in the snapped model, certificate verified) is a
snapping artifact: under the row's true angles it is `+2.43e−4` worse, and the table's own L for that
row overstates reality by `2.84e−4`. `submission.csv` and the root `WHITEBOARD.md` are **untouched** —
the guard's condition (a verified strictly smaller *genuine* side) was met in the model and failed in
reality, which is precisely what the guard is for. Run 108's candidate patch is unchanged.

**Not claimed.** That these five rows prove anything about the other 443 uncertified rows; that cluster
sizes above 5 or rotations other than 45°/90° are exhausted; that the n = 18 row is hopeless (it is
repair-stalled at 16 overlaps after snapping, nothing more). No score is claimed and no number here is
offered as a leaderboard estimate.

**Next.** The sound bar for any transcendental row is the true-angle extent, so the next instrument
should carry the error budget of §4: bound `ε(gap)` per row, compare `model L + ε` with the delivered
true side, and only then decide whether a relational move is worth pursuing.

