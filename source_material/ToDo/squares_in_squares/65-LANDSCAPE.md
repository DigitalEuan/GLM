# 65 — The relaxed rung: coverage, and what exact lifting can reach (run 102)

Run 101 closed the certificate boundary. This run turns that instrument on the part of the table
that has never had an exact sentence: the **424 relaxed rows**. The question is not "can the
verifier check a sentence" but "which of the 424 can a sentence be built for, and would any of them
be *smaller* than the row the table already publishes".

**Short version.** Of the 1,000 rows, 546 carry a certified exact sentence, 30 have an algebraic
*side* but no lifted pose, and 424 are relaxed. Every one of the 424 carries at least one
transcendental angle, so none can be lifted as it stands. On 14 targeted rows (the three notches,
the continuous rows that bracket them, and small/medium rows with the most slack) **3 lift and
certify at clearance 0** — and they are precisely the three notches, which were already exact. The
other **11 refuse for two structural reasons**, measured below. **No row achieves a materially
smaller exact side**: the three exact sides sit 3.84–3.85 × 10⁻⁹ *below* the delivered side, which
is the table's polish overshoot, not a gain. No row moved, and no score is claimed.

## 1. Coverage of the 1,000 rows

| label | rows | what it means |
|---|---|---|
| **certified** | **546** | an exact sentence exists at clearance 0: 447 pure-Q grid rows (run 84's census) and 99 Q(√2) pose lifts (runs 84–85) |
| **side-only** | **30** | the container side lies in Q(√2) (18), Q(√7) (5), Q(√5) (3) or a rational-t lattice (4), but the *pose* was never lifted — the unlifted one is n = 126 |
| **relaxed** | **424** | the run-86 class `continuous`: neither the side nor the pose has an exact class we search |

Source: the run-86 `field_triage.json` classes, crossed with the run-85 `uplift.json` statuses; this
run only re-derives the angle census and the side (70-digit Decimal), it does not re-classify.

The carrier census is new. A **carrier** is a square whose stored angle has no exact word in
Q, Q(√2), Q(√5) or Q(√7) at the declared heights (rational t-basis up to denominator 64; 0°, 45° and
the Pythagorean words are the exact candidates). 453 rows carry at least one carrier:

| carriers per row | rows |
|---|---|
| none | 547 |
| 1–10 | 14 |
| 11–100 | 123 |
| > 100 | 316 |

**All 424 relaxed rows carry at least one carrier** — none is 0°/45°-only — and in **361 of them a
carrier sits on the bounding box** (its rotated extent sets a face of the container), while in 63
the carriers are strictly interior. That split turns out to predict nothing about liftability, for
the reason in §5.

## 2. Why the relaxed rung is relaxed

Two independent obstructions, and the census separates them:

* **the angle.** A stored angle whose 70-digit cos/sin is not one of our exact words has no exact
  rotation matrix in any field we use. A sentence containing it is not a sentence of our alphabet —
  at *any* side. That is a statement about the declared alphabet and the declared heights, and it
  is a refusal, not a search gap.
* **the side.** The container side of a relaxed row is, in 7 of the 14 targets, not within 1e-7 of
  any `a + b√2` with denominators ≤ 16 and `|b| ≤ 16` — the declared lattice of
  `qsqrt2.recover_side`. The box itself is not a number we can write.

The four targets whose sides *are* rational are the interesting ones: **n = 680, 733, 788, 845 have
sides 186/7, 193/7, 200/7, 207/7** — the `2k + 4/7` lattice, one rung of the same rational-t
family run 90 built at `2k + 5/7`. Their angles are still transcendental, but their *sides* are
cheap, and that is why the lifting test gets further on them (§4).

## 3. The target set

Fourteen rows, chosen before any lift was run:

| group | rows | why |
|---|---|---|
| the notches | 677, 785, 901 | the three delivered rows the block-45 family almost explains; all three are `Q(√2) pose` rows and lift — they are the **reference**, not the target |
| edge band | 680, 689, 733, 788, 845, 904 | the continuous rows that bracket each notch (677 → 680, 785 → 788, 901 → 904), i.e. the nearest rung in both count and side |
| small/medium slack | 11, 17, 39, 68, 86 | the relaxed rows with the largest slack `L − √N` (0.516–0.566), where a tightened L has the most room to show up |

## 4. Method

`scripts/landscape65.py` (new, six controls of its own; `--audit` now includes it):

1. **Re-derive the angle census.** Each stored angle gets an exact word if the 70-digit Decimal
   cos/sin matches Q's axis word, the 45° word, or a rational t-basis word within 1e-11. The
   t-basis is recovered as a *fraction* (run 86's `pyth_angle` returned only the denominator, which
   cannot rebuild the word) by continued fraction with its residual declared at 1e-12.
2. **Drop the carriers, lift the core.** `qsqrt2.lift_sentence` places wall cells exactly, peels the
   rest from contact equations by 2×2 Cramer, recovers leftovers by height-bounded search, and the
   exact gate judges the result.
3. **Certify.** Every lifted sentence is written as a `galois-certificate/1` object (tag `Quad(2)`,
   exact rotations and centres as `(a, b)` pairs, tight `L`, origin 0) and checked by
   `verify_certificates.verify_certificate` — the same verifier run 101 shipped.
4. **Completion probe.** For a carrier, its contacts in the delivered pose (largest of the four SAT
   slacks zero, found in 70-digit Decimal) give exact contact equations on the *core cell's* axes;
   each word of the certified families (axis, 45°, t = 1/2, 1/3, 3, 2, 1/4, 1/5) turns each pair
   into a 2×2 solve, and a candidate is accepted only if every pair with the core clears through the
   exact per-pair predicate and the **full gate** accepts the completed sentence.
5. The two tolerances are declared and only choose topology: 1e-7 for a lift's acceptance, 1e-9 for
   reading the delivered pose, 1e-6 for contact detection in the probe. No verdict is a comparison
   against a decimal.

## 5. Results

| n | N | carriers | core | side (exact) | vs delivered | certificate |
|---|---|---|---|---|---|---|
| 677 | 677 | 0 | **lifted** | `29/2 + 17/2√2` | **−3.845e−9** | verified, 2375 contacts |
| 785 | 785 | 0 | **lifted** | `33/2 + 17/2√2` | **−3.851e−9** | verified, 2785 contacts |
| 901 | 901 | 0 | **lifted** | `37/2 + 17/2√2` | **−3.855e−9** | verified, 3227 contacts |
| 680 | 680 | 90 | 590 | not-on-lattice | — | — |
| 689 | 689 | 455 | 234 | side-not-recovered | — | — |
| 733 | 733 | 96 | 637 | not-on-lattice | — | — |
| 788 | 788 | 99 | 689 | not-on-lattice | — | — |
| 845 | 845 | 110 | 735 | not-on-lattice | — | — |
| 904 | 904 | 108 | 796 | side-not-recovered | — | — |
| 11 | 11 | 5 | 6 | side-not-recovered | — | — |
| 17 | 17 | 7 | 10 | side-not-recovered | — | — |
| 39 | 39 | 15 | 24 | side-not-recovered | — | — |
| 68 | 68 | 34 | 34 | side-not-recovered | — | — |
| 86 | 86 | 21 | 65 | side-not-recovered | — | — |

**Hits: 3 of 14** — the three notches, at clearance 0, each with a certificate the shipped verifier
accepts, and the same contact counts the run-85 lift recorded (2375 / 2785 / 3227). They are the
reference: the delivered 677/785/901 rows *are* exact sentences, and the run confirms it with the
certificate format rather than with the older ledger.

**Does any candidate beat the delivered row?** Strictly, yes — and it is not a gain. The exact sides
are 3.844692085…e−9, 3.850692085…e−9 and 3.854692085…e−9 below the sides recorded in
`submission.csv`. The table's decimals are written *above* the exact side by that margin (the
polish/shim scale every earlier run measured at 1–4e−9), so a lift always lands a few nanometres
under the published number. No row is tighter by a distance that would change a score digit, and
none of the 14 improves on what is already published.

**Misses: 11 of 14, in two groups.**

* *`not-on-lattice`* (680, 733, 788, 845 — exactly the four `2k + 4/7` rows). The side is
  recovered; the geometry is not. With the carriers removed the contact graph no longer pins every
  remaining square, and the per-coordinate height-bounded recovery refuses — the habit of these
  rows is that the carriers are **structural ties**, not decoration: they are what closes the
  corner regions of the 45° block, and removing 90–110 of them (out of 680–845) leaves free
  squares whose positions are under-determined by the equations that survive.
* *`side-not-recovered`* (689, 904, 11, 17, 39, 68, 86). The lift stops before the geometry: the
  core's own span is not within 1e-7 of the declared Q(√2) lattice, so there is no `L` to place
  cells in. These are the rows whose side is genuinely outside the fields we write.

**Completion: the machinery is tested, the relaxed rows cannot use it yet.** The probe ran a
positive control — remove one cell from the certified n = 677 sentence and ask the alphabet to put
one back — and it succeeds: the axis word at `(14 + 17/2√2, 14 + 17/2√2)`, clearance 0, 2375
contacts (control 6 in `landscape65.py --selftest`, recorded in the ledger). No relaxed row could be
probed, because the probe needs a lifted core and none of the 11 has one; so the honest count for
the relaxed rung is **0 carriers replaced out of 0 attempted**, with the theorem-of-the-day being
that the obstruction is upstream of the completion.

## 6. What this says about the frontier

The relaxed rung is not "almost exact" in the way the polished poses suggest. Its two obstructions
are independent and both fatal to a lift:

1. **the angle is not in the alphabet**, so no exact rotation exists for the carrier — and the
   carriers are spread through the row (316 rows have more than 100 of them), not confined to a
   seam;
2. **the side is not in a field we write** in 7 of the 14 targets, so even a perfect core would have
   no container.

Where the side *is* rational (`2k + 4/7`), the carriers are structural ties, so the natural next
production is not a lift but a **construction**: build a sentence at side `2k + 4/7` from rational-t
words only (t = p/7 family, denominators small), at the counts 680/733/788/845 and their
neighbourhoods, and let the gate decide. That family is exactly the one run 90 built at
`2k + 5/7`; the missing rung is the word whose seam law gives `4/7`. If it gates, four relaxed rows
acquire exact sentences *at their own published side* — no gain, but the first exact certificates on
the relaxed rung; if it gates at a smaller side, that is a real score candidate and the falsifier is
the gate at 1e-9 below.

The notches remain the template: 677/785/901 show that a relaxed-looking pose can be an exact
Q(√2) sentence when its 289 tilted squares are all at the 45° word. The relaxed 424 are the rows
where that is **not** the case, and the census now says so row by row.

## 7. State

`landscape65.py --selftest` **6 controls**, 32 s (the angle census; the 45° word; the t-basis
refusal at π/8; n = 677 lifting at clearance 0 with 2375 contacts and a verified certificate; n = 680
carrying 90 transcendental squares; and the completion control on 677). `--audit` **382 functions,
0 naming `float`** (25 in `landscape65`, 15 in `rat47`), with both added to the audited modules. `--selftest` (glm_wheels) 32
controls, `verify_certificates --selftest` 11 mutations, bare run exit 0, `record_guard.py` OK,
README/STATUS footers byte-identical. Ledger: `workspace/push/landscape65.json`.

**No row changed, no score claimed, `submission.csv` and root `WHITEBOARD.md` untouched.** The 424
relaxed rows still carry no exact sentence; this run says which obstruction each one meets and what
a construction at the rational side would have to do.

## 8. Run 103 — cleanup, a bounded core lift, and the `2k + 4/7` rung

### 8.1 What changed in the instrument

`landscape65.py` lost the debris of the debug rounds: the unused `gcd` import, a dead branch in
`word_kind` (both arms returned `"pyth"`), a recomputed extent in `probe_carrier` (the value was
already in `e`), and a stale "five controls" docstring. The carrier-drop semantics are now one
function instead of a list comprehension repeated in three places:

```python
keep, dropped = drop_carriers(words)   # carriers are removed, never snapped
```

with the policy stated where it lives: a carrier is removed, never re-read as an axis word (a
sentence that gates because an angle was rounded is not a sentence of this alphabet); the kept cells
keep their delivered order and their own words; the dropped indices come back so completion can
address a carrier by its **delivered** index, with no reuse or compaction.

### 8.2 The core lift is now bounded in work, not in wall-clock

The cost of the five refuse-every-round cores was the leftover search: for a core whose side is
`~2k`, `height_bound` is `~31`, `lattice_den` is `~14`, and one `recover_point` call scans ~6000
exact candidates; a 700-square core asked for that twice per unpinned square per density round.

`qsqrt2.recover_leftovers` now takes an optional `budget` in those work units and returns
`(miss, exhausted)`; `lift_sentence` threads it and reports `budget_exhausted` on a refusal.
`None` is the old unbounded search, so every earlier caller — including the verifier's own lift
path — is unchanged. `landscape65` declares `RECOVER_BUDGET = 120`.

Measured on the same fourteen rows (per-row seconds are in the ledger):

| row group | before (run 102) | after (run 103) |
|---|---|---|
| notch lifts 677/785/901 | ~40 s each | **10.6 / 13.2 / 16.2 s** |
| `not-on-lattice` 680/733/788/845 | 3–9 min each | **33.9 / 60.4 / 58.0 / 67.7 s** |
| `side-not-recovered` (7 rows) | seconds | 1.3–1.5 s each |
| the whole 14-row run | ~45 min | **306 s** (269.6 s of it lifting) |

**Every verdict is unchanged, row by row**: 3 `lifted` (same sides `29/2 + 17/2√2`,
`33/2 + 17/2√2`, `37/2 + 17/2√2`, same 2375/2785/3227 contacts, certificates verified), 4
`not-on-lattice`, 7 `side-not-recovered`, the same coverage tally (546/30/424) and the same carrier
bands. The refusals now also record `unrecovered` and `budget_exhausted: true` — the budget cut the
search short, and run 102's unbounded search refused in the same way, which is what lets the label
stand.

### 8.3 The `2k + 4/7` rung, started (`scripts/rat47.py`)

**The strip lemma (exact, exhaustive over the alphabet).** Over all 82 rational-t words with
`q <= 16` plus the 45° word, the bounding-box width `|cos| + |sin|` has minimum **exactly 1**, and
the minimum is attained only by `t = 0` and `t = 1` — the two axis orientations. Since `4/7 < 1`,
**no unit square can sit in a `4/7` margin**: the rung's extra `4/7` cannot be a seam width, so the
four rows are not block-plus-margin packings. (The overhang of a *rotated* square can be small; its
bbox cannot.)

**The skeleton (measured).** All four rows are `N = m² + 4` with `m = 26, 27, 28, 29`, and their
delivered sides are exactly `2k + 4/7` to 1e−6 (`26.571428…`, `27.571428…`, `28.571428…`,
`29.571428…`). Replacing every angle by its nearest rational-t word gives the same shape in all four:

| n | axis (`t=0` / `t=1`) | `t=1/2` (3-4-5) | `t=1/3` | worst snap | snapped-gate violations |
|---|---|---|---|---|---|
| 680 | 172 / 452 = 624 | **28** | **28** | 1.57e−3 | **1** (−3.07e−5) |
| 733 | 192 / 485 = 677 | **28** | **28** | 2.85e−3 | **2** (−6.9e−4, −3.7e−4) |
| 788 | 162 / 570 = 732 | **28** | **28** | 3.57e−3 | **1** (−2e−11) |
| 845 | 476 / 313 = 789 | **28** | **28** | 1.56e−3 | **2** (−1.6e−3, −2e−4) |

The **28 + 28 constant** is the rung's signature: in every row, exactly 28 squares at the 3-4-5 word
and exactly 28 at `t = 1/3`, the rest axis-aligned. And the delivered pose, with those words, misses
being an exact sentence by **one or two pairs** — 788 by `2e−11`, i.e. at rounding scale.

**The repair (exact).** Re-choosing words cannot close those pairs. A discrete search over the four
(and then pairwise, 6×6) nearest words per cell, scored by the exact per-pair clearance, swaps
**nothing** in all four rows: the violations stay at 1, 2, 1, 2. The defect is **positional, not
angular** — the pose is a numerically polished arrangement, not a sentence whose angles were
mis-labelled.

**The lift from scratch.** Lifting the snapped pose exactly, the contact graph pins only 142 (680),
19 (733), 302 (788) and 19 (845) of 590–813 squares, and the bounded leftover recovery refuses:
`not-on-lattice`, `budget_exhausted`. So the rung cannot be reached by re-labelling the delivered
pose either.

**Certificates: 0 of 4.** The rung is started, its arithmetic is confirmed, its structure is named
(axis block + 28 + 28), and its obstruction is located to one or two pairs — but no exact sentence
at `2k + 4/7` exists yet.

### 8.4 The next experiment

Two candidates, in order of cheapness:

1. **788 first**, because its single violation is `2e−11`: a positional repair — translate one cell
   of the offending pair by an exact rational amount and re-gate its incident edges — may close it
   without touching the other 787 squares. The certificate format carries any `Q(√2)` coordinate, so
   a repair at that scale is legal arithmetic, not a tolerance.
2. **The 28 + 28 band, built from the two words directly.** Both counts are constant across four
   different `m`, so the band is a fixed module: 28 squares at the 3-4-5 word and 28 at `t = 1/3`
   arranged around an `m × m` axis block. Deriving its contact law (as doc 53 derived the ridge's
   `w* = min(1/(c+s), c+s)`) is the way to build it at clearance 0 instead of repairing a polished
   pose.

Neither is claimed here. What run 103 establishes is the arithmetic (`2k + 4/7`, `m² + 4`), the
invariant (`28 + 28` tilted squares), the lemma (no `4/7` seam), and the measurement (the pose is one
or two pairs away) — plus a 14-row run that costs 306 s instead of 45 minutes with identical verdicts.

## 9. Run 104 — the rung's last pair closes (above it), and what the 28 + 28 band is

### 9.1 The positional repair (`scripts/rat47pos.py`)

Run 103 showed that re-choosing words cannot close the rung's one or two offending pairs, so run 104
moves *positions*: one cell of each offending pair is translated along a SAT axis of that pair, every
orientation untouched. The method is small and exact:

* for a move `t·d` of a cell, each pair's constraint is `|s0 + t·(d·q)| >= need` on **some one** of its
  eight axes — a union of two rational rays per axis, intersected over the pairs and with the container
  box (so the side can never grow). The feasible set is an exact interval union in `Q`; no tolerance
  decides anything and no float appears in any decision.
* the witness is the **first** feasible move away from the delivered pose: the boundary at which the
  offending pair's own constraint turns non-negative, so that pair is in exact contact and the
  sentence's clearance is exactly 0.
* a row with two pairs is repaired one pair at a time; a move is accepted when the exact gate's overlap
  count strictly drops, and the gate — not the interval arithmetic — is the arbiter.

| n | offending pair(s) | delivered slack | move | gate | certificate | side | excess over `m + 4/7` |
|---|---|---|---|---|---|---|---|
| 680 | 244–268 (`t=1`, `t=1`) | −3.0743e−5 | cell 244, −x, `6148681/200000000000` | ok, clearance 0, 1 contact | **verified** | 26.571428573356 | 1.92742857e−9 |
| 733 | 255–280, 471–496 | −6.9151e−4, −3.6617e−4 | cell 280, +x, `691512899/10^12` (2 → 1), then cell 471, −x, `183083837/5·10^11` | ok, clearance 0, 2 contacts | **verified** | 27.571428573356 | 1.92742857e−9 |
| 788 | 195–217 (`t=0`, `t=0`) | **−2e−11** | cell 195, −x, `1/5·10^10` | ok, clearance 0, 1 contact | **verified** | 28.571428573359 | 1.93042857e−9 |
| 845 | 254–278, 763–790 | −1.5524e−4, −1.9999e−4 | cell 254, −x, `77620519/5·10^11` (2 → 1), then cell 763, −y, `129093267/2·10^11` | ok, clearance 0, 2 contacts | **verified** | 29.571428573361 | 1.93242857e−9 |

**The pair closes, and the answer to "at `200/7`?" is no.** Each repaired sentence is an exact
zero-clearance sentence — a contact, not a tolerance — and `verify_certificates` accepts a
`galois-certificate/1` for all four. But the side they close at is the delivered side, and that side is
**above** the rung by 1.93e−9:

* exact, not measured: `28571428573359/10^12 − 200/7 = 13513/(7·10^12)` for 788, and the same
  arithmetic gives `3373/1750000000000` (680, 733) and `13527/7000000000000` (845).
* the excess is a **wall** problem, not a pair problem: the cell realising the wide direction has
  7.0e−11 (788), 7.3e−11 (733), 7.5e−11 (680) and 6.8e−11 (845) of inward room before it touches its
  neighbour — 26–28× **less** than the excess — so no single-cell move, and no whole-wall move, reaches
  the rung.
* the pose lives on a `1/10^12` coordinate grid while the rung's side is `m + 4/7`, denominator 7, and 7
  does not divide `10^12`. A sentence at the rung needs coordinates off that grid, so rounding the
  delivered pose can only make it tight *at its own side*.

Tally: `closed-above-rung` ×4. **The rung is closable as an exact zero-clearance sentence one lattice
step above itself, and not at itself.** The 2e−11 gap run 103 measured was the visible part of a
1.93e−9 wall offset; closing the pair was never going to move the wall.

### 9.2 The 28 + 28 band's law (`scripts/rat47law.py`)

**The census (exact).** Every row carries `m² − 52` axis cells — 624, 677, 732, 789 — with exactly 28
at the 3-4-5 word and 28 at `t = 1/3`, so `N = (m² − 52) + 56 = m² + 4` is a decomposition, not a
coincidence.

**The module (measured, exact where it can be).** Each band is a strip anchored to the bbox corner, and
the other band is its transpose:

| key | 680 | 733 | 788 | 845 | spread |
|---|---|---|---|---|---|
| `t=1/2` `x0` | 1.545714285793 | 1.545714285790 | 1.545714285788 | 1.545714285785 | **8e−12** |
| `t=1/2` width | 7.480000000564 | 7.480000000542 | 7.480000000523 | 7.480000000506 | **5.8e−11** |
| `t=1/2` `y0` | 12.434689648 | 12.433414229 | 12.434640726 | 12.436319694 | 2.9e−3 |
| `t=1/2` height | 12.701318869 | 12.704928117 | 12.704280179 | 12.703017386 | 3.6e−3 |

The `t = 1/3` band has the same four numbers transposed (`y0 = 1.5457142858` to 8e−12, height 7.48 to
5.8e−11, width and `x0` free). So the band is a **7.48-thick strip whose thickness is the same in four
independently polished rows to 5.8e−11** (each row sits 5.1–5.6e−10 above the rational `187/25` — the
shim scale run 102 found), **pinned to the wall it touches to 8e−12, and free along its own length,
which wanders by 3.6e−3**.

**The contact graph (the law).** Inside each band the contact types are the same in all four rows:

| type (words, frame axis, sign) | 680 | 733 | 788 | 845 |
|---|---|---|---|---|
| `t=1/2`–`t=1/2`, `u`, + | 16 | 16 | 16 | 16 |
| `t=1/2`–`t=1/2`, `u`, − | 4 | 4 | 4 | 4 |
| `t=1/2`–`t=1/2`, `v`, − | 8 | 8 | 8 | **9** |
| `t=1/3`–`t=1/3`, `u`, + | 20 | 20 | 20 | 20 |
| `t=1/3`–`t=1/3`, `v`, − | **9** | 8 | 8 | 8 |

Five types, four identical in every row, exactly one contact flipping between rows. The classification
is safe over a wide threshold band: the smallest non-contact slack among the band's close pairs is
1.4e−4 … 1.9e−4, so any threshold in `[1e−10, 1.4e−4]` returns the same graph.

**And the graph is why the length moves.** 28 cells carry only 28–29 exact intra-band contacts: an
assembly that under-constrained is not rigid (rigidity wants ~81), and its free direction is exactly the
one that varies. What fixes the *thickness* to 5.8e−11 is not the band but its two interfaces.

**The interface is not a law.** The contacts from the band to the axis mosaic are 32, 31, 28, 31 in 11,
12, 12, 13 types — no fixed graph. That is the honest split: the band is *internally* lawful and
*externally* loose, which is what a strip wedged between two mosaics with 1e−3 fillers should look like.

**The `4/7` is a lattice shift, not a seam.** Classifying every cell's bbox corner by the nearer of `Z²`
and `(Z + 4/7)²`, the axis cells' column gaps include **18 gaps of exactly 3/7 in every row** (closest
measured 2.9e−10 … 3.2e−6) — the `4/7` / `3/7` alternation of two interpenetrating lattices. The
per-lattice cell *counts* flip with the corner's own gauge (680: 560 shifted / 120 unit; 733: 121 / 612),
so they are reported as gauged, while the 18 is not gauged at all. This is what the strip lemma
predicted: a `4/7` margin holds no square, so the rung's extra `4/7` has to be a *relative shift* of the
mosaic, and it is.

### 9.3 Above 1000

**Arithmetic (exact).** With `axis = m² − 52` and `band = 56` measured in all four rows, the law extends
to every `m >= 26` as arithmetic:

| m | N = m² + 4 | axis | band | side = m + 4/7 |
|---|---|---|---|---|
| 32 | 1028 | 972 | 56 | 228/7 |
| 40 | 1604 | 1548 | 56 | 284/7 |
| 45 | 2029 | 1973 | 56 | 319/7 |

**Growth (translation only, so no drift is possible).** Copying the outer 3-wide band outward — every
added cell an *exact translate* of a cell already in the row, no coordinate re-derived — takes 845 to 965
cells at side 32.571428573361. The excess over the new rung is `13527/7000000000000` = 1.93242857e−9,
**digit for digit the source row's excess**: the rung's offset is carried, not compounded. So the *side*
extends past 1000 without drift.

**The count does not extend this way**, and that is the finding: the growth adds 120 cells where
`N = m² + 4` asks for 183, because the outer band is not periodic — 58 cells in the last 3 units against
87 in the one before it. Two consequences, stated rather than smoothed over: the four rows are **not
translations of one another** (they share a count law, not a shape), and an exact `N > 1000` row needs a
fresh construction, not a copy. The grown sentence also inherits the source row's two violating pairs,
which §9.1's repair closes the same way.

### 9.4 What is and is not claimed

Established: four exact zero-clearance sentences with verified certificates at the delivered sides (0 of
4 at the rung itself); the wall is 1.93e−9 wide and 27× tighter than the excess needs; the 28 + 28
module's thickness `187/25` to 5.8e−11, its five intra-band contact types, and its loose interface; the
rung's `4/7` as a two-lattice shift with 18 exact `3/7` gaps; and drift-free side extension past 1000
with a named count failure.

Not claimed: an exact sentence at `2k + 4/7`; a rigid module (the band is a chain, not a body); a fixed
band-to-axis interface; an `N > 1000` row. The next production is a construction at the rung side itself
— the wall offset says the pair repair was the wrong scale, and the lattice law says where the `4/7`
enters — with the count law's constructive form as its second target.
