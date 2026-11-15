# VERIFICATION REPORT

Tier 1 (Python) and Tier 2 (Lean) status for the Squares-in-Squares study.
Method: TCT (Geometric Language Machine), UBP discipline (exact tiers)
with declared measured tier (engine/certificates, margins stated).

## Tier 1 — Python pipeline, end to end

| Module | Key checked | Expected | Result |
|---|---|---|---|
| 01 `01_grid_baseline.py` | `PERFECT_SQUARES` | `31` | VERIFIED |
| 02 `02_known_results.py` | `GOEBEL_MATCH` | `1` | VERIFIED |
| 03 `03_pack_engine.py` | base 5@2.8 | found, E≈0 | VERIFIED (measured) |
| 04 `04_verify_packing.py` | `CERTIFIED` | all packings | 30/30 certified |
| 05 `05_cent_patterns.py` | `TWO_PATH_COUNTS_OK` | `1` | VERIFIED |
| 06 `06_scorecard.py` | δ identity | < 1e-9 | VERIFIED |

Notable exact results:
- grid ceiling total: **28.9376699165…** (isqrt bounds, width < 2e-15)
- Göbel strip formula verified against all 7 published values (exact √2)
- 31 perfect squares (grid-optimal proven), 60 Nagamochi no-win puzzles,
  33 best-knowns beating grid (n ≤ 100)
- base: 5 squares in L = 2.8; cascade: 29 packings (k²+1 at k+0.8)
- improvement: **−0.587631** (30 puzzles); rows: 500,500
- impossibility cross-check: engine refuses 6@2.9 = theorem s(6)=3

### Defect log (7 build defects, all re-derived)

SAT-axis push; angle-after-wall infeasibility; infinite shrink loop; floor
edge case (exact-integer branch); script path depth; write race; proven-table
encoding. Each caught by asserts or runtime; each fixed from computed values.

## Tier 2 — Lean (`lean/tct_squares/`, scaffolded from `lean/spec.json`)

- Proved (sorry-free): **6** — `sqrt2_witness`, `cascade_step1..3`,
  `improvement_5`, `nagamochi_sample`
- `sorry` (development required): **3**
  - `cascade_count_symbolic` — gap: `omega`/`ring` (Mathlib)
  - `verification_margin_soundness` — gap: interval arithmetic / exact
    predicates (Mathlib); 1e-9 certificate is measured, not machine-checked
  - `s11_optimal_value` — **deliberate, expected unproven**: the
    combinatorial-geometry wall (optimality of s(11) open)
- Axioms (named premises): **7**
- `lake build`: **not run** — `lake` not on PATH here; project ready:
  `cd lean/tct_squares && lake build`.

## Optimization loop (docs/07)

- ¢ cost: 10 → 7 (iteration 1 accepted; iteration 2 rejected — `spatial`
  is the L witness).
- Cross-checks: 14 written / 14 live after defect fixes.

## How to re-verify

```bash
cd squares-in-squares-tct
python3 scripts/column3/01_grid_baseline.py
python3 scripts/column3/02_known_results.py
python3 scripts/run_search.py            # re-derives found.json (deterministic LCG)
python3 scripts/column3/05_cent_patterns.py
python3 scripts/column3/04_verify_packing.py
python3 scripts/column3/06_scorecard.py
python3 scripts/lean_ledger.py lean/tct_squares --build
```

Note: engine runs are deterministic (declared LCG seeds) — exact
reproduction of `found.json` expected; wall-clock varies.

---

## FINAL VERIFICATION (survey-integrated submission, score 23.284687)

Scope: all 1000 packings in `submission/submission.csv` (500,500 rows).

1. **Source certification.** 235 survey SVGs parsed with the survey's
   `parse_svg_packing.py` (Decimal, 20–100 digits, angle normalization to
   (-π/2, π/2]); each packing verified: pairwise SAT non-overlap and
   bbox containment in the declared side s (parse-time bbox ≤ s + 1e-6).
2. **Removal windows.** Realizations via beam-search greedy removal
   (beam 4, candidates restricted to bbox-edge squares); every result
   re-verified before storage.
3. **Cascade chains.** Band-cell construction is geometry-complete: the
   free region at container L+1 is three disjoint rectangles (right band,
   top band, corner), counted exactly as nx·⌊h⌋ + ny·⌊w⌋ + nx·ny; any
   prefix of the deterministic cell order is a valid packing (cells
   mutually disjoint, touching the base only at the bbox boundary).
4. **Clearance policy.** Every stored state scaled by (1+2e-9/L) about
   its bbox corner before 12-dp rounding, so contacts open ~2e-9 gaps;
   CSV round-trip re-verified zero overlaps (worst penetration ≤ 0) and
   zero container drift (|L_csv − L_table| ≤ 1e-9 for all 1000).
5. **Round-trip.** Final CSV read back from disk: id continuity 0..500499
   confirmed, per-n square counts confirmed, score recomputed
   independently: **23.284687** (grid ceiling 28.937670; improvement
   −5.652983; 399/1000 beat grid).
6. **Cross-checks.** Triangular-table authoritative list: 214/214 exact
   match for n ≤ 324 (0 misses, 0 spurious). Aux-page box scan: 0 missing
   records (same-s variants only). Göbel-square family enumeration under
   its constraint a−1 < ½b√2 < a+1: no new coverage of grid-tied n.
   Chain-reach limits per grid block: computed exactly; the 601 grid-tied
   puzzles are open problems (state of the art matched, not exceeded).

Arithmetic: all scores computed in Python (float64, sums over 1000 terms);
grid ceiling re-derived twice (scripts/column3/01, packlib scorecard).
