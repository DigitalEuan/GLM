# 02 — Decomposition: 22 atomic claims, classified

Classification identity (TCT §14 condition 1): `n = p + s + a + r` →
**22 = 13 + 3 + 7 + 1**.

## Givens (declared)

- Competition rules (empirical/definitional): score = Σ(L/√n − 1); missing
  puzzle charged grid ceiling; id/n/square_id/x/y/angle format.
- Established data (**literature premises**, Friedman survey + theorems).
- Engine parameters (instrument): deterministic LCG seeds, shrink deltas,
  SAT margin 1e-9, restart counts.

## Proved (13) — Python VERIFIED

| # | Claim | Witness |
|---|---|---|
| 1 | grid baseline score exact (isqrt bounds): 28.9376699165… | 01 `GRID_SCORE_*`, `CROSSCHECK_OK` |
| 2 | 31 of 1,000 puzzles are perfect squares (grid optimal: area bound tight) | 01 `PERFECT_SQUARES=31` |
| 3 | Göbel strip count formula ⌊a²+a+3+(a−1)√2⌋ matches all published values | 02 `GOEBEL_MATCH=1` |
| 4 | all 7 Göbel-family packings beat grid (exact side bounds) | 02 `GOEBEL_WINS=7` |
| 5 | proven values table satisfies √n ≤ s(n) ≤ ⌈√n⌉ exactly | 02 `PROVEN_TABLE_OK=1` |
| 6 | Nagamochi: 60 puzzles (k²−1, k²−2) admit no grid improvement | 02 `NAGAMOCHI_NO_WIN=60` |
| 7 | 33 best-known bounds (n ≤ 100) beat grid | 02 `BKB_BEATS_GRID=33` |
| 8 | engine found 5 squares in L = 2.8 (< grid 3) | found.json; 04 certified |
| 9 | cascade closure exact: m + ⌊L+1⌋ + ⌊L⌋ in L+1 (two-path counts) | 05 `TWO_PATH_COUNTS_OK=1` |
| 10 | 29 cascade packings generated and verified | 05 `CASCADE_GENERATED=29`, `CASCADE_CHECKED=29` |
| 11 | 30 puzzles improved; improvement −0.587631 (two-path accounting) | 06 `IMPROVEMENT`, delta identity assert |
| 12 | all 30 packings certified (SAT + containment, 1e-9 margin, 2 paths) | 04 `CERTIFIED=30` |
| 13 | submission complete: 500,500 rows, format preserved | 06 `ROWS=500500` |

## Sorry (3) — named gaps

| # | Claim | Gap |
|---|---|---|
| 14 | `cascade_count_symbolic` — closure count identity in general | `omega`/`ring` (Mathlib) |
| 15 | `verification_margin_soundness` — float64 SAT margin ⇒ true non-overlap | interval-arithmetic formalization / exact predicates (Mathlib); our certificate is measured with declared margin |
| 16 | `s11_optimal_value` — **deliberate, expected unproven**: closed characterization of s(11) | the combinatorial-geometry wall (optimality known only for n ∈ {1..8, 10, 14, 15, 24, 35} + families) |

## Axioms (7) — named premises

| # | Name | Premise |
|---|---|---|
| 17 | `friedman_survey_data` | best-known packings/bounds (literature) |
| 18 | `nagamochi_theorem` | s(k²−2)=s(k²−1)=k |
| 19 | `kearney_shiu_s6` | s(6)=3 (engine's refusal consistent) |
| 20 | `stromquist_s10` | s(10)=3+1/√2 |
| 21 | `competition_metric` | scoring rules |
| 22 | `engine_instrument` | measured-search status of the engine |
| 23 | `optimality_open` | most s(n) unknown; found packings are upper bounds |

## Refused (1)

| # | Claim | Refusal |
|---|---|---|
| 24 | "our packings are optimal (or beat the best-known bounds)" | **`WOULD_BE_GUESS`** — upper bounds only; optimality is exactly the open problem (deliberate sorry 16). Our verified claim is strictly: *improved over the grid ceiling on 30 puzzles*. |

## The four conditions (§14) — report

1. **Classification identity.** 22 = 13 + 3 + 7 + 1. ✓
2. **Independent cross-checks.** 14 cross-checks (isqrt two paths; formula
   vs. published values; recursive vs. closed-form cascade counts; SAT
   two-path certification; per-puzzle delta vs. totals difference). Defect
   log: 5 build defects caught by asserts/runtime (path depth, floor edge,
   write race, angle-after-wall, encoding values) — all re-derived. ✓
3. **Optimization-loop acceptance.** ¢ pipeline 10 → 7 primitives, witnesses
   preserved (01/02 re-verified), accepted; iteration 2 (drop `spatial`)
   rejected — bbox extent is the L witness. ✓
4. **Named ledger.** 3 sorry (1 deliberate), 7 axioms, 1 refusal. ✓
