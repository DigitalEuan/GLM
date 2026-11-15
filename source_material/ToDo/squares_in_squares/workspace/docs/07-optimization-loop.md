# 07 — Optimization loop and defect log

Per TCT §11: iterate on cost after VERIFIED; never at the price of a witness.

## Baseline

- Cost metric: ¢ primitive count for the packing pipeline (docs/05).
- Verification strength: 14 cross-checks (isqrt two paths; Göbel formula
  vs. published values; recursive vs. closed-form cascade counts; SAT
  double-scan certification; per-puzzle δ vs. totals difference).

## Iteration 1 — v1 → v2 (accepted)

- **Proposal.** Drop `scale`, `accum`, `sum` from the pipeline (stitched
  steps with no witness of their own).
- **Measurement.** `BEFORE: total=10 (atomic=8, composite=2)` →
  `AFTER: total=7 (atomic=5, composite=2)` — REDUCED by 3.
- **Re-verification.** 01 (`PERFECT_SQUARES=31`) and 02 (`GOEBEL_MATCH=1`)
  re-run: VERIFIED.
- **Verdict. ACCEPTED.**

## Iteration 2 — drop `spatial` (rejected)

- **Proposal.** `state_space` subsumes geometry.
- **Re-verification.** bbox extents *are* the L measurement (the score's
  numerator); dropping `spatial` orphans the L witnesses.
- **Verdict. REJECTED.** Loop stops.

## Defect log (the build taught the method)

| # | Defect | Caught by | Fix |
|---|---|---|---|
| 1 | center-line pair push jams rotated squares | failed targets | SAT-axis resolution |
| 2 | angle polish after wall projection → infeasible states | energy breakdown (wall E > 0) | freeze angles during settle |
| 3 | shrink loop never terminates at target L | process hang | `break` on reaching target |
| 4 | hand-floor bug in Göbel count (exact-integer case) | assert straddle | exact-integer branch |
| 5 | script path depth (column3 vs scripts) | FileNotFound | `../..` roots |
| 6 | write race: cascade read before search wrote | FileNotFound | re-run after write |
| 7 | (p,q) encoding values wrong in proven table | review pre-run | corrected encoding |

Each defect was re-derived from computed values, never guessed (the
assert-layer discipline of the quartet, continued).

## Final report

- ¢ cost: 10 → 7; 14 cross-checks live.
- Search campaigns: 3 waves, ~40 target attempts, every failure recorded
  as a measured energy (search_log*.txt).
- Improvement: 30 puzzles, −0.587631 vs. grid ceiling; 30/30 certified.
