# Classification ledger (TCT §14)

Identity: `n = p + s + a + r` → **22 = 13 + 3 + 7 + 1**

## Proved (13) — Python VERIFIED

1. grid baseline score exact via isqrt bounds: 28.9376699165… (01)
2. 31 perfect squares: grid proven optimal (area bound tight) (01)
3. Göbel count formula ⌊a²+a+3+(a−1)√2⌋ matches all published values (02)
4. all 7 Göbel-family packings beat grid (exact side bounds) (02)
5. proven values table satisfies √n ≤ s(n) ≤ ⌈√n⌉ (02)
6. Nagamochi class: 60 puzzles admit no grid improvement (02)
7. 33 best-known bounds beat grid for n ≤ 100 (02)
8. engine base: 5 squares in L = 2.8 < grid 3 (found.json)
9. L-extension closure exact: m + ⌊L+1⌋ + ⌊L⌋ in L+1 (two-path counts) (05)
10. 29 cascade packings generated and verified (05)
11. 30 puzzles improved; −0.587631 (two-path accounting) (06)
12. 30/30 certified: SAT + containment, 1e-9 margin, 2 scan paths (04)
13. submission complete: 500,500 rows, sample format (06)

Lean proved (6): `sqrt2_witness`, `cascade_step1`, `cascade_step2`,
`cascade_step3`, `improvement_5`, `nagamochi_sample`.

## Sorry (3) — named gaps, development required

- `cascade_count_symbolic` — needs `omega`/`ring` (Mathlib); closure count
  verified concretely at every cascade step.
- `verification_margin_soundness` — needs interval-arithmetic formalization
  or exact algebraic predicates (Mathlib); our 1e-9 certificate is measured,
  declared, double-scanned — but not machine-checked.
- `s11_optimal_value` — **deliberate, expected unproven**: closed
  characterization of s(11). The combinatorial-geometry wall; optimality
  known only for n ∈ {1..8, 10, 14, 15, 24, 35} and families.

## Axioms (7) — named premises

- `friedman_survey_data` — best-known packings/bounds (literature).
- `nagamochi_theorem` — s(k²−2) = s(k²−1) = k.
- `kearney_shiu_s6` — s(6) = 3 (engine's refusal consistent).
- `stromquist_s10` — s(10) = 3+1/√2.
- `competition_metric` — scoring rules.
- `engine_instrument` — measured-search status (float64, LCG, margins).
- `optimality_open` — most s(n) unknown; found packings are upper bounds.

## Refused (1)

- "our packings are optimal / beat best-known bounds" — **`WOULD_BE_GUESS`**.
  Upper bounds only. The verified claim is exactly: improved over the grid
  ceiling on 30 puzzles, certified. Optimality = the open problem itself.

## Cross-check register (14 written; 7 defects fixed; 14 live)

| Module | Cross-check pairs (disjoint paths) |
|---|---|
| 01 | per-n isqrt intervals vs. algebraic identity; count vs. combinatorics |
| 02 | formula floor via bounds vs. published values; side bounds vs. grid; table vs. bounds |
| 03 | engine restarts agree on success/failure verdicts |
| 04 | full-pair SAT vs. AABB-near SAT (must agree) |
| 05 | recursive closure counts vs. closed form (every step) |
| 06 | per-puzzle δ sum vs. totals difference (< 1e-9) |

Defect log (docs/07): 7 build defects — SAT-axis push, angle-after-wall,
infinite shrink loop, floor edge case, path depth, write race, table
encoding — all caught and re-derived from computed values. `c − t = 14 ≥ 2`. ✓
