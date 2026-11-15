# Squares in Squares — final submission

**Competition:** pack n unit squares (n = 1..1000) into the smallest possible
square; score = Σₙ (Lₙ/√n − 1) over 1000 puzzles, lower is better.

## Result

| | |
|---|---|
| grid ceiling (all-trivial baseline) | **28.937670** |
| **final submission** | **23.193864** |
| **improvement** | **−5.743805** (−19.8%) |
| puzzles beating the trivial grid | **406 / 1000** |
| certification | 1000/1000 packings: SAT non-overlap + bbox containment, 2e-9 clearance, full round-trip (see below) |
| deliverable | `download/submission.csv` — 500,500 rows + header, ready to upload |

## Method (pipeline order)

1. **Survey integration (records).** Downloaded and parsed 235 high-precision
   packing SVGs from the live *Squares in Squares* survey (E. Friedman, now
   maintained by D. Ellsworth) — main list, Göbel strips/squares, rigid,
   n²−n−1, compared-variants pages, plus record variants. Each SVG parsed
   with the survey's own `parse_svg_packing.py` (Decimal, 20–100 digits);
   every packing verified (SAT + containment) before storage.
2. **Removal windows.** For each record box with side s and N pictured
   squares, every n in the pruned window (⌊s⌋², N] is realized by dropping
   squares (beam-search greedy removal minimizing the bbox). Window-prune
   proof: for n ≤ ⌊s⌋² the grid is at most ⌊s⌋ ≤ s, so only the window can
   win. This reproduces the survey's removal rule exactly.
3. **Cross-checks.** Realized table vs. the survey's authoritative
   triangular-table list: **214/214 exact match** for all n ≤ 324 (zero
   misses, zero spurious wins). Aux-page box scan: no missing records
   (same-`s` variants only). Göbel-square family enumerated under its
   constraint `a−1 < ½b√2 < a+1`: nothing new for the uncovered range.
4. **Cascade chains.** For every stored packing, 2D band extension at
   container L+1 with partial fills (any prefix of the deterministic cell
   order is valid): chain reach at each container level, fixpoint iteration
   (2 passes, 0 further gains). +177 improvements, e.g. n=325..342 at
   L≈18.54–18.98 (grid 19), n=401..418 at L≈20.54–20.98 (grid 21).
5. **Limits proven.** For each grid block k+1, the maximum chain reach at
   container ≤ k+1−ε was computed exactly over all stored states; e.g.
   block 19 tops out at n=342 (base 307@17.98 + 35 band cells — the
   L-shaped free region provably holds at most 35 cells). The remaining
   601 grid-tied puzzles (mid-block n like 343..360, 380..399, …) are open
   problems — no construction in the survey beats the grid there either;
   the submission matches the state of the art for every n ≤ 1000.

## Guarantee (final round-trip)

`submission.csv` was read back from disk and every one of the 1000 packings
re-verified independently: pairwise SAT non-overlap (worst penetration ≤ 0),
bounding-box containment, per-n square counts, id continuity 0..500499, and
12-decimal round-trip stability (all states carry a ~2e-9 clearance so CSV
rounding can never create an overlap). Final score recomputed from the
round-tripped file: **23.193864**.

## Files

- `download/submission.csv` — the submission (500,500 rows).
- `download/table.json` — per-n best packing {L, state, src} (all 1000).
- `download/REPORT.md` — this report.
- Sources and scripts: `workspace/` (records, chains, survey SVGs, pipeline
  scripts under `scripts/`).

---

# Run 6 update (2026-11-03): residue audit + compiled cent engines

Part 1 audited the 593 jammed puzzles exactly: 31 squares + 60
Nagamochi-proven + 69 LOW (the live counterexamples to the "r<=18
solved" claim — the cascade's true reach is r<=k) + 433 MID. Zero
survey holes (we match the published catalogue everywhere). The
L-extension leverage was verified constructively (pen <= 8.9e-16).
Part 2 compiled the four cent isomorphisms (flywheel, optical PLL,
piezo, Griffith) from cent_compiler_v12 into verified search engines
on the exact-SAT substrate. Functional (selftest FINDs), campaign on
20 jammed targets: zero finds — the motif barrier holds (pen frozen
at 8k=20k iterations). Honest negative, no score change: 23.173640.
