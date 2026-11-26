# 103 — The beat probe: the block-bedded carrier cannot beat any of the 110 two-class rows — it only ties 19 (Run 146)

**Run 146, 2026-11-26.** Instrument `scripts/beat_probe.py` (new), ledger
`workspace/push/beat_probe.json`; `scripts/block_bed.py` repaired (doc 102 §8).

Doc 102 closed run 145 with a question and a price: the entry gate would authorise a sweep, and the
sweep's question was *can this family reach a row's count at a side below the delivered one?* — i.e.
can it **beat**, or only **tie**? Run 146 puts that question to the family **directly**, without a
sweep, and finds the answer is **no**: over every side in the window `[√n, L_delivered)`, every grid
size `K`, every block shape with `p·q ≤ 330` that fits the box, and **every split**, the family never
even reaches a delivered row's count — **0 count matches in 949,243 trials**, so there is nothing for
the gate to refuse. **0 beats.** The family explains the table's symmetric third and nothing below it.

**The one thing that changed the answer before it started: run 145's 48 was a counting defect.** The
probe could not be built on a counter that was wrong, and checking the counter found it (two defects
in `split_counts`, doc 102 §8). With the counter fixed the entry test is **19/110 — a FAIL by one
row** — and every hit is a *symmetric* declaration. The probe's null result is therefore about a
family whose reach was already one row short, and the null is measured, not inherited: the same search
re-finds all **19** ties at exactly their delivered side when the delivered side is allowed (§4).

**Nothing promoted, and C1–C4 was not entered — there is no candidate.** `submission.csv` and root
`WHITEBOARD.md` are untouched; the delivered total stands at **22.217428576** (554 beats, 446 ties).

## 1. What was asked

Run 145's next step, in the user's words: *"Run the cheap probe block_bed's passed entry test
authorises: for the 48 reproduced rows and the 110 two-class rows, search the same family for a side
strictly below the delivered one, so we learn whether it can ever beat a row rather than only tie it.
If a beat shows up, gate it and take it through C1–C4; if not, say plainly that the family only
explains the table."*

The 48 became 19 when the counter was repaired (§4); the probe covers the 110, which contains them.

## 2. Why the question is small: two exact bounds

1. **Area.** Every cell has area 1 (axis cells are `1 × 1`, block cells are 45° squares of side 1), so
   a legal pose of `n` cells needs `L*L >= n`. A beat can therefore only sit in

       sqrt n  <=  L  <  L_delivered,

   a window whose width is `L_del·(1/√fill_del − 1)` — for the delivered fills (0.90–0.97) that is
   **0.1 to 1.3 units**, i.e. **14–16** group sides `a + (s/2)√2` per row (the group is dense: ~30
   sides per unit of length, because every `s` contributes one).
2. **The count law.** `n = K*K − D + p*q` with `D >= 0` forces `K*K >= n − p*q`, and the family needs
   `L > K`; with `p*q <= 330` this pins `K` to `sqrt n ± 4`. For a row near its delivered side the
   *required* block correction `p*q − D = n − K*K` is a small number (the "waste": block cells that do
   not replace a carrier cell), which is exactly the quantity that does not move when `L` moves.

So the sweep is a **visit**: 15 sides × ≤ 7 grid sizes × the shapes that fit, per row.

## 3. The instrument

- **`probe_table(a, s, K, p, q)`** — the bed count of *every* split `(kx, ky)` in one `O(K²)` pass.
  All the geometry is `(A + B√2)/4` with `A, B` integers, and the comparisons are **exact integer
  comparisons**: `_bisect_exact` uses a rounded key to find the boundary and `_sgn` walks it to the
  exact index. Exactness is not decoration: the windows very often end *exactly* on a lattice point
  (the block touches a cell corner), and a rounded comparison then answers one cell out — which is how
  the first version of this table drifted by 3–4 cells and was rejected by its own control.
- **Coverage**: every `(side, K, shape)` with `pq <= 330`, the block's bbox `√2(p+q)/2 <= L`, and
  **every split** `1 <= kx, ky <= K−1`. The count is from the table; a split whose count equals
  `K*K + pq − n` is rebuilt by `block_bed.check` and judged by `qsqrt2.gate`, and a hit counts only
  when `r["n"] == n`.
- **Controls** (`--selftest`, 4): the table equals `bed_count` on **every** split of six declarations
  (1805 splits); an oversized block is refused; the table reproduces the recorded drop counts of the
  recorded declarations; **and the sensitivity control** — the identical search, with the delivered
  side allowed, re-finds all 19 ties at exactly their delivered side (and never below).

## 4. The result

`python3 scripts/beat_probe.py` — 110 rows, **1379 s (23 min)**, one background process:

| measure | value |
|---|---|
| rows probed | **110** (82 whose side is in the group, 28 outside it) |
| (row, side) windows searched | **910** |
| (side, K, shape) trials, each over every split | **949,243** |
| **count matches** (`K*K − D + p*q == n`, exact) | **0** |
| gate refusals | **0** |
| **beats** (a gated pose at `L < L_del`, count `n`) | **0** |
| sensitivity control | **19 / 19** ties re-found at exactly the delivered side |

**Not one declaration of the family reaches a delivered count at a side below the delivered side.**
That is stronger than "the gate refused them": the count equation is never satisfied, so the family's
*arithmetic* — `K*K` minus the bed plus a block of at most 330 cells, at a side in `[√n, L_del)` — is
outside every one of the 110 counts. The 19 ties of doc 102 are the whole of the family's contact with
the delivered table: **19 of 110 rows tied, 0 beaten**, and 63 in-group rows that are not even tied.

The 28 rows outside the group are untouched by the probe: the family's side law cannot express their
sides at all, so they can be neither tied nor beaten by it (they are listed in doc 102 §4).

## 5. What it means

- **The family only explains the table**, and only its symmetric part: the 19 ties are the centred
  `K = 2k`, `kx = ky = k`, square-block poses — the delivered poses' own symmetry. The free split,
  the block's aspect ratio and the seam gap add no reach at all.
- **The binding constraint is the count, not the gate.** Run 144's obstruction was geometric
  (carrier–carrier overlap); run 145 removed it and found the entry test short by one; run 146 shows
  the next wall is arithmetic — the family cannot place `n` cells at a lower side, whatever the gate
  would say.
- **No promotion, and no C1–C4.** C1 (a legal candidate that beats a row), C2/C3/C4 all presuppose a
  candidate. There is none, so the gate is not entered and `submission.csv` / `WHITEBOARD.md` stay
  untouched.

## 6. What this redirects

1. **More translates per axis is the cheapest untried degree of freedom.** The family has four
   translates plane-wide (two runs per axis); the delivered axis classes have 4–54 (doc 100 §7). `r`
   runs per axis with `r − 1` positive gaps keeps the disjointness law and the bed rule *unchanged*
   and multiplies the count surface by `r²`; the probe of this doc is the instrument that can price it
   (the same `[√n, L_del)` window, the same count equation, a bigger `K`-space).
2. **The 28 out-of-group rows need a finer side law**, not a new carrier: `a + b√2` with rational `b`
   (doc 100's "any rational `b`") covers sides like `7.5714` and `8.8810` that halves cannot.
3. **Do not sweep this family.** Its reach is 19 ties, every one at the delivered side; there is no
   parameter left in it that moves a side down.

## 7. Checks

Run this visit, each exit 0 unless marked: `beat_probe --selftest` **4 controls**; `beat_probe`
**110 rows, 0 beats** (doc 102's family, ledger written); `beat_probe --control` **19/19** ties
re-found; `block_bed --selftest` **10 controls** (control 9 now compares the split table with the
counter on every split); `block_bed` entry test **19/110** (FAIL, threshold 20); `py_compile` on
`block_bed`, `beat_probe`, `qsqrt2`; `glm_wheels --audit` **684 functions, 0 offenders** (its list is
fixed and does not include this run's two modules, so `exact_field.audit_module` was also run on them
directly: `beat_probe` **14** functions / `block_bed` **22** functions, **0 naming float**); `sqscore`
**22.217428576** (554/446); `record_guard` OK.

No row changed.
