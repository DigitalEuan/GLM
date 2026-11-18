# 31 — The algebraic-word framing, audited (run 68)

A framing was proposed for this project: a packing is a **sentence over an exact
relation alphabet** (its "algebraic words"), score moves when the alphabet moves
and not when a search runs longer, the pile-of-angle-words route is already
closed, and what remains is discrete non-block multi-angle rotation at a few
named rows. This document exists because that framing was offered as a direction
to work in, and **every number in it has to be checked against the delivered
table before it directs a run** — the standing rule of this collection: a
catalogued or asserted geometry is a nomination until an exact builder and the
canonical scorer certify it (`19` §10.1).

The framing holds on its three closures. It does not hold on four of its
figures, and one of its recommended rows cannot be priced at all from here. All
of that is below.

---

## 1. The tower, and what this project actually holds at each rung

| field | angle | where it lives here | status |
|---|---|---|---|
| ℚ | 0°, 90° (axis) | the 447 grid rows; alphabet `{axis}` | scored, no beat |
| ℚ(√2) | 45° | 128 of the 553 beats carry a 45° square; 54 design rows `gobel2/gobelS/gobel3` (`05-MECHANICS.md`, design-quadratic row); 45° **kink-minimum** of `s(θ)` proven by sweep (`theta_family.py:19`, `GLM_INVESTIGATION.md` 206–207) | certified |
| ℚ(√5) | arctan(1/2) = 26.565° | run 5 family, `galois_certs.py` | certified, 0 conversions |
| ℚ(√10) | arctan(1/3) = 18.435° | run 5 family | certified, 0 conversions |
| ℚ(√3) | 30° | run 5 family; `json/theta30_new_members.json` | certified, 0 conversions |
| ℚ(√2,√3) | 15° (V4) | run 5 family | certified, 0 conversions |
| ℚ(√(2+√2)) | 22.5° (C4, nested quartic) | run 5 phase B (38 of the 280 certificates), `22.5°` re-sweep | certified, 0 conversions |

None of these rungs needs a special representation. For rational
`t = tan(θ/2)` the cosine and sine are rational, so **any** of these angles is
exactly buildable and exactly gated (`21` §8, and the erratum recorded in
`04-RUN-LOG.md` run 54: the earlier claim that a non-ℚ(√2) seam could not be
certified exactly was wrong). The tower is
therefore a statement about *which words are cheap to certify*, not about which
are representable.

## 2. The three closures, checked line by line

**2.1 Run 5 — the rotated-block family is closed.** `scripts/theta225_push.py`
sweeps all 7 special angles (45°, 36.870°, 30°, 26.565°, 22.5°, 18.435°, 15°) as
a `p×p` block plus corner staircases: phase A/B over `n ≤ 1050`, phase D over
`1001 ≤ n ≤ 5000` against `json/extended_table_5000.json`. The deliverable is the
certificate collection, **280 certificates** from `scripts/galois_certs.py`
(7 angle families × full `(a,p)` sweeps plus survey records; 54 carry a static
entry in `json/galois_certificates.json`, 9 of them value-match the live table,
`05-MECHANICS.md`, certificate table). **Conversions: 0.** The cause is structural and proven by the
same sweep: `s(θ)` has a kink-minimum at exactly 45° for every `(a,p)`, so
tilting a rigid block away from 45° buys bounding-box waste, not density.

**2.2 Run 52 — the score step is an arrangement, not a word.**
`scripts/r1_atoms.py` (`workspace/push/r1_atoms.json`, record `20-R1-ATOMS.md`).
Both bands (`k = 8..24` and `k = 25..31`) use the **same alphabet**
`{axis, π/4}`, so the 0.520815 step is carried by a 17×17 diamond that is
half-full at `k = 24` (145/289) and full from `k = 25` (289/289, side 17√2). The
falsifier fired: no new word was needed to explain the step.

**2.3 Run 55 — the two-tilt grammar at n = 10 buys nothing.**
`scripts/seed_wheels.py` (selftest 7/7, record `23-SEED-WHEELS.md`). 400
wall-anchored cells + 36 centred cells = **436 cells, 80 certified, 0 gains**;
the best exact side is 4.000000 (grid) and the centred fill reaches
3.707106791 = delivered + pad. The Karakuş floor is 3.192582, so 0.51 of
admissible side is untouched — and the binding component is the **fill**, not
the tilt pair.

So the framing's central negative is right, and it is right **by our own
instruments**: a wider vocabulary of angle words thrown at rigid templates does
not convert a row. That is not a bound; it is a closed scope, and the scope is
declared in each record.

## 3. The framing's figures against ours

| framing's claim | what the ledgers say | verdict |
|---|---|---|
| ℚ(√2) 45° "carries **70%** of all score improvements" | 128 of 553 beats contain a 45° square (**23.2 %** of the beat rows); those rows carry **43.2 %** of the 6.719613 total gain. All 553 beats carry at least one tilt; 0 beats exist on the axis alphabet alone | **overstated**; the two measured shares are the usable numbers |
| 280 machine-verified certificates | 280 (`galois_certs.py`); 54 static entries, 9 value-matched | ✓ |
| swept for `1 ≤ n ≤ 5000` | phase A/B `n ≤ 1050`, phase D `1001–5000` | ✓ |
| converted **0** unresolved numerical puzzles | 0 | ✓ |
| score step 0.520815 explained by the 17×17 diamond | ✓ (145/289 → 289/289) | ✓ |
| run 55: 436 cells, 80 certified, 0 gains | ✓ (Karakuş floor 3.192582) | ✓ |
| **Khalili–Gharabaghi**: `s(k²−5) = k` for all `k ≥ 7` | real and current: registered 2026-11-13 as **T-298** in the Squares Project, reported at **V0/C1** (reported lower bound; full replay and Lean build held by that project's owner). It is **not** verified in this record. Our table touches the family at 25 rows, `n = 44…956`, `k = 7…31`: **all 25 sit at the grid, 0 beats**, so nothing here contradicts it | **external, reported — call it a nomination performed correctly**, not "formally proved" in our voice |
| "linear density wall `r*(k) ≈ 0.67k + 4`" | no such quantity exists in any ledger. Our exact statements are the `s(k²−2)=s(k²−1)=k` family, Daniel's `k²−3`, `k²−4`, Karakuş's bound as a pre-gate prune (`20`, `21`: 29/29 `k²−1` rows at grid, 20/20 `s(k²−k)` beat), and the catalogue witness `s(k²+1) = k + 0.5355339` | **unsupported here**; do not quote it |
| "the three thinnest wall-margin points: n = 656 (0.00029), n = 184 (0.00040), n = 819 (0.00130)" | those rows in the delivered table: `k = 26/14/29`, `r = k²−n = 20/12/22`, `L = k` to 2e-9, **gain exactly 0.000000**, `L − √n = 0.387503 / 0.435340 / 0.381824`. No ledger quantity reproduces 0.00029/0.00040/0.00130. And 447 rows share gain 0, so zero gain cannot select three of them | **not reproducible → unearned**; see §4 |
| Trump's 11-square packing ≈ 40.18° with 8 tilt angles; Gensane–Ryckelynck's 29-square with 6 | external; **our catalogue ends at n = 324** (215 cells, no `square-<n>.svg` above), so rows 656 and 819 fall inside the 675 undetermined rows where we have no source at all (`26` §9) | **quoted, not rechecked** |

## 4. What the three named rows actually are

`n = 656`, `184`, `819` are **at the wall**, not near a thin margin of room.
`L = k` for each of them (to the table's 2e-9 fuzz), the gain `(k − L)/√n` is
0.000000, and a row at `L = k` has to cross an **entire integer step** before it
beats anything — the widest possible ask, not the smallest. If "margin" was meant
as "distance pressed against the integer wall", the reading is at least
qualitative (they are pressed), but:

* 447 of 1000 rows are pressed in exactly the same way, so the three are not
  distinguished by it;
* the quoted non-zero figures are not the difference to the wall under any
  measure in `sqscore.py` (`gain`, `slack = L − isqrt(n)`, `L − √n`, `score`);
* two of the three (`656`, `819`) lie above `n = 324`, where our best-known
  comparison is unsourced (`26` §9: 675 rows with `best_known = null`), so their
  "margin" cannot be checked from here even in principle;

A nomination that cannot be priced is not room. Under this collection's rules it
is recorded here and not acted on (`19` §10.1 rule 1: a bound or a number with a
big gap is not room).

## 5. What survives, and the one route the framing leaves open

* **Alphabet-first is the correct reading of the delivered table.** Every beat
  uses a tilt; none exists on the axis alphabet alone. Score is entirely a
  property of which words a row's construction uses.
* **The pile is closed for rigid templates** — run 5 (280 certificates, 0
  conversions), run 52 (same alphabet across the step), run 55 (436 cells, 0
  gains). Three independent instruments, three refusals, each with a declared
  scope.
* **The one unexhausted route is non-block, multi-angle, non-rigid** — the
  Trump / Gensane–Ryckelynck kind of configuration. It is not excluded by
  anything here. But every piece of evidence for it in the framing sits **above
  n = 324**, in the 675-row region where the catalogue is unsourced, so a sweep
  there cannot be scored against a best-known: it would produce certificates with
  nothing to compare them to.
* **The live object is therefore the one already named at the end of run 67**
  (`19` §12.4, `30` §6): branch assignment plus rotation at a **single**
  well-sourced row, with the exact gate as the only judge — not a wider LP, not a
  finer lattice, not a broad multi-angle sweep.

## 6. What this document does not do

* It does not certify any non-block multi-angle construction. None has been
  built here; the above-324 examples are quoted, not reimplemented.
* It does not adopt `0.67k + 4`, and it does not repeat the three margins as if
  they were measured.
* It does not upgrade T-298: the report is recorded as reported, and the only
  claim made in our voice is the 25-row contact check in §3 (all at grid).
* It changes no row. The canonical scorer is untouched; total **22.218056945**,
  **553** beats, **447** at grid, 1000 rows.

## 7. Re-run

```bash
cd source_material/ToDo/squares_in_squares
python3 scripts/sqscore.py                 # 22.218056945, 553 beats, 1000 rows
python3 - <<'PY'
import sys, math; sys.path.insert(0,'scripts'); import sqscore
per = sqscore.load()
B=[n for n in range(1,1001) if sqscore.is_beat(n, sqscore.extent(per[n]))]
g45=[n for n in B if any(abs(a-math.pi/4)<1e-6 for (_,_,a) in per[n])]
gain=lambda n:(math.ceil(math.sqrt(n))-sqscore.extent(per[n]))/math.sqrt(n)
print(len(B), len(g45), round(sum(map(gain,g45))/sum(map(gain,B)),4))
print(all(not sqscore.is_beat(n, sqscore.extent(per[n])) for n in (k*k-5 for k in range(7,32))))
PY
```

Recorded in `04-RUN-LOG.md` as run 68; indexed in `19-COLLECTION-AND-REVIEW.md` §9.
