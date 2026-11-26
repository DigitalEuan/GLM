# 109 — The composite family, and the beat counts prose could still hide (Run 153)

**Two closures.** The record: `RECONCILIATION.md` still said **553/1000** under its own
"## Canonical state" heading, and the guard could not see it because R3's claim test knew only
table rows, currency sentences and lines naming the score. R3 now also covers any line inside a
**current-state section** (canonical / current / delivered / results / status / frontier / state),
skips fenced code, and reads the *paragraph* — not the line — for a superseded score when deciding
what is history. It flagged exactly one line, `RECONCILIATION.md:10`; that line is fixed and the
guard is clean.

The audit: the 550 trusted bases now seed a fourth family — **a base plus an exact motif in its
leftover** — and the whole audit is re-run. **93,431 candidates over all 900 rows of 101..1000, 0
strict beats.** Family D alone contributes 57,388 candidates over 784 rows, and its closest
candidate is not a near-miss but a **grid tie**: the family is *provably* bounded by the area
bound, so it cannot exceed grid density at all.

---

## 1. What R3 could still miss, and what it catches now

Run 152's R3 required a line to *look* like a claim: a markdown table row, a currency sentence, or a
line naming the current score. `RECONCILIATION.md`'s canonical-state block is none of those —

```
## Canonical state
The latest state represented by the surviving run records is **Run 52** ...
- score: **22.217428576** (rounded: **22.217429**);
- rows beating the grid: **553/1000**;
```

— the score sits on one line, the count on the next, and neither line is a table. Three additions
close it:

1. **sections** — a line under a heading that declares the current state (`canonical`, `current`,
   `delivered`, `results`, `status`, `frontier`, `state`) is a claim on its own, whatever its shape;
2. **paragraphs** — history is decided per paragraph, not per line, so a run-log entry that ends a
   line with a superseded score and starts the next with its beat count stays history;
3. **fences** — fenced code is not prose and is skipped (the `REPRODUCE.md` transcript's
   "454/1000 beat grid (the run-13 frontier)" is not a claim).

The scan examines 19 beat counts on claim lines and flagged exactly one of them:

```
RECONCILIATION.md:10: 553/1000  [R3 beat count]
    - rows beating the grid: **553/1000**;
```

fixed to `**554/1000** (553 before the run-140 promotion of row 90)`. Two lines that a naive prose
rule *would* have flagged are now correctly exempt, and both are worth naming because they are the
shapes a future sweep will meet: `04-RUN-LOG.md:116` (`454/1000 beat grid`, a Run-14 entry whose
score is at the end of the previous line) and `09-CASCADE.md:21` / `NEXT_STEPS.md:44` (tables that
quote "22.218056945, 553/1000" — a superseded score *on* the line). Every count of something else
(`929/1000` verified rows, `540/1000` tilt-support rows, `875/1000` title counts) is untouched,
because R3 still requires the beat vocabulary.

## 2. Family D: a base and a motif in its leftover

A base is a rigid pose with a **square** bbox `[0, L]²`. A motif is any other rigid pose with a square
bbox — the twelve C poses (3 words × `b = 2..5`, block plus exact fill) and the smallest bases
themselves (`L ≤ 6`), because a base is the densest tile this project owns. Place:

```
base   [0, L]^2            motif's bbox   [L, L+S]^2        frame   [0, L+S]^2
```

The two bboxes meet only along lines, so **validity is structural** (no search, no gate needed to be
valid); the free area is exactly the two strips `[L, L+S]×[0, L]` and `[0, L]×[L, L+S]`, of area
`2 L S`, and each is filled to the integer lattice:

```
nx = floor(L+S) - ceil(L)          cells across the strip
ny = floor(L)                      cells along it
n  = n_base + m + 2 nx ny          L_total = L + S, exactly
```

`nx`/`ny` are exact: floors and ceilings in the base's field, no sampling. Trims `r = 0, 1, 2` give
three counts per `(base, motif)` at the same side, so the family covers `784` distinct rows rather
than 300.

**The bound.** A packing of `n` unit squares in side `L` has `n ≤ L²` — the squares are disjoint and
inside the frame. Likewise `m ≤ S²`, and the strips hold at most `2 L S`. Therefore

```
n_D = n + m + 2 nx ny  ≤  L² + S² + 2 L S  =  (L + S)²
```

so **every composite satisfies `L_total ≥ √n_D`**: family D can never be denser than a perfect tiling
of its own frame, i.e. it can tie the grid and never beat it. That is not a sampling result; it holds
for every base, every motif and every trim, and the audit's numbers are consistent with it exactly:

| | |
| --- | --- |
| candidates | **57,388** |
| rows reached | 784 of 900 |
| strict beats | **0** |
| closest candidate | **−1.448e-9** — row 111, `base36` in `base25`, a **grid tie** (11.000000003 vs 11.000000002) |
| second closest | **−0.0032** — row 110 |
| more than `1e-2` above | 436 of the 900 rows |

The gap between "closest" and "second closest" is the point: the only composites that come near a
delivered side are the ones that *are* the grid. Everything else is at least `3.2e-3` above.

## 3. The re-run, all four families

```
exact bases: 550 of 1000  words {'axis': 446, 'mixed': 104}  fields {'Q': 450, 'Q(sqrt 2)': 100}
scale_motifs: 93431 candidates over n = 101..1000, 900 rows reached, 0 strict beat(s)
  A-product      31577 candidates, 900 rows, 0 beats, best margin -1.498e-9  (row 133)
  B-inflate       4348 candidates, 554 rows, 0 beats, best margin +1.936e-9   (row 962)
  C-rot-block      118 candidates,  91 rows, 0 beats, best margin -0.177    (row 106)
  D-composite    57388 candidates, 784 rows, 0 beats, best margin -1.448e-9  (row 111, a tie)
```

Family D is now the best candidate at **70 rows** of the 900 — including `n = 272`, where it improves
the best-known candidate from `18.000000` (run 151/152) to **`17.742641`** — still `0.777` above the
delivered `16.965586`. At `n = 500` the product family still holds the best candidate (`23.414214`).

**Why the whole audit is negative, in one sentence each.** (A) multiplies a packing by `k²` in side
`kL`, so it *preserves* density and can only reproduce the table's own slack. (B) raises it toward 1
by adding a unit ring, and its ceiling is the grid — which is why its best margins are `±2e-9` and why
it is the family that *reproduces* the table. (C) is a rotated block in its own bbox, and a rotated
block can use at most `b²/(bw)²` of it (0.66 realised for 45°), so it is far *below* grid density.
(D) is bounded by `(L+S)²` and so can never exceed grid density. **A composition of rigid tiles cannot
beat a row that is denser than the grid — and 554 of the delivered rows are.**

## 4. Controls

`python3 scripts/scale_motifs.py --selftest` — **15/15**, 31 decision functions, 0 naming `float`.
Run 152's controls are unchanged (the CSV read exactly, the gate, the product and border laws, the
planted duplicate, both words with their spare area, the margin rule, row 50 as a rational-word base,
the `atan(1/2)` grid in Q(√5) at exactly `9/√5`, the mixed-radical refusal, the census). Two new ones:

* **13** — the composite law: row 20 + the 45° 3×3 motif gives **60 cells at `L = 9.242640689`**,
  which is exactly `L_base + S_motif`; the exact strip counts are `nx = 3`, `ny = 5`, so the strips
  add `30`, and the *built pose* (cell by cell) gates with 96 contacts.
* **14** — the composite frontier is nowhere near the table: over rows 20/50/120 the best composite
  is `n = 266` at `−0.177`.

`python3 scripts/exact_words.py --selftest` — 8/8 (unchanged). `python3 scripts/record_guard.py` —
clean, with R3's section rule in place.

## 5. Reproduce

```
python3 scripts/scale_motifs.py --selftest    # 15 controls, ~40 s
python3 scripts/scale_motifs.py --promote     # ~3.5 min; 93,431 candidates, 0 beats
python3 scripts/record_guard.py               # R1, R2, R3
```

Ledger `workspace/push/scale_motifs.json`: `summary` gains `D-composite`, and its per-row `rows` list
records `motif`, `m` (the base), `drop` and the exact side at 18 decimals.

## 6. What this closes, and what it leaves

**Closed.** (i) The prose beat count: R3 now reads current-state *sections*, so `RECONCILIATION.md`'s
canonical block is checked rather than skipped, and the sweep found no other stale count outside the
shapes declared historical. (ii) The composite question: with the bound `n ≤ (L+S)²`, family D is
shown — not just measured — to be incapable of beating the grid, and the audit confirms it with 57,388
candidates whose best is a tie. (iii) The audit's negative now rests on an argument that covers every
rigid-tile composition, with the four families as its instances.

**Left, declared.** (i) The composites keep the two bboxes in opposite corners; placing them anywhere
else cannot raise the area bound, but it *can* change the integrality of the strips, so a variant that
slides the motif along the frame is not audited here. (ii) Bases in two different radicals would make
a composite live in a degree-4 tower; **zero** such bases exist, so nothing is skipped in practice.
(iii) `record_guard`'s R3 is still a text rule: a document that states neither a score, nor a beat
label, nor a current-state heading cannot be checked by it — the honest limit of a scanner, recorded
here rather than papered over.
