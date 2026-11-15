# 03 — The three-column contract

The three columns describe the **identical logical steps**. Domain: ℤ/ℚ for
accounting (isqrt bounds for √n); float64 + declared 1e-9 margins for the
geometric search/certificate (measured tier, UBP §2 exception applied and
declared). **UBP.** Exact arithmetic wherever exactness is claimable.

**Givens.** Competition rules; Friedman-survey data; engine instrument
parameters (LCG seeds, shrink schedules, margins).

| Step | Plain English | Mathematics | Python (this step) | Lean |
|---|---|---|---|---|
| 1 | the grid ceiling per puzzle | L = ⌈√n⌉, score = ⌈√n⌉/√n − 1 | 01: isqrt bounds | — |
| 2 | the exact grid total | Σ = 28.9376699165… (width < 2e-15) | 01: `GRID_SCORE_DIGITS=28937669` | — |
| 3 | perfect squares are grid-optimal | n = k² ⇒ s(n) = k (area bound tight) | 01: `PERFECT_SQUARES=31` | — |
| 4 | the Göbel strip count formula | count = ⌊a²+a+3+(a−1)√2⌋ | 02: exact √2 bounds | `sqrt2_witness` (proved) |
| 5 | formula vs. published values | 5, 10, 27, 38, 52, 67, 84 match | 02: `GOEBEL_MATCH=1` | — |
| 6 | proven values in bounds | √n ≤ s(n) ≤ ⌈√n⌉ (12 cases) | 02: `PROVEN_TABLE_OK=1` | — |
| 7 | Nagamochi's no-win class | s(k²−1) = s(k²−2) = k | 02: `NAGAMOCHI_NO_WIN=60` | `nagamochi_sample` (proved) |
| 8 | the engine's search object | positions + angles; L continuation | 03: PBD + adaptive shrink | `engine_instrument` (axiom) |
| 9 | the found base | 5 squares in L = 2.8 < 3 | found.json | `improvement_5` (proved) |
| 10 | the L-extension closure | m → m + ⌊L+1⌋ + ⌊L⌋ in L+1 | 05: `extend()` | `cascade_step1..3` (proved) |
| 11 | cascade counts, two paths | recursive ≡ closed form | 05: `TWO_PATH_COUNTS_OK=1` | `cascade_count_symbolic` (sorry) |
| 12 | the generated family | 29 packings: k²+1 at k+0.8 | 05: `CASCADE_GENERATED=29` | — |
| 13 | the certificate | SAT penetration ≤ 1e-9 + containment, 2 paths | 04: `CERTIFIED=30` | `verification_margin_soundness` (sorry) |
| 14 | the score accounting | per-puzzle δ ≡ totals difference | 06: assert < 1e-9 | — |
| 15 | the result | 28.937670 → 28.350038 (−0.587631) | 06: `IMPROVEMENT` | — |
| 16 | the submission | 500,500 rows, sample format preserved | 06: `ROWS=500500` | `competition_metric` (axiom) |
| 17 | the impossibility cross-check | engine refuses 6@2.9 = s(6)=3 | search logs | `kearney_shiu_s6` (axiom) |
| 18 | the optimality boundary | upper bounds only; s(n) open | — | `s11_optimal_value` (sorry: deliberate) |

**UBP compliance.** Exact ℤ/ℚ + isqrt bounds for all score claims; the
geometric tier is float64 with a **declared 1e-9 certificate margin**
(measured, not exact — recorded in `engine_instrument` and the soundness
sorry). No randomness: deterministic LCG with declared seeds.

**Decomposition.** 22 atomic claims: 13 proved, 3 sorry, 7 axioms, 1 refused
(docs/02).

**Verification.** Python: 6/6 modules exercised end-to-end (grid baseline,
known results, engine, verifier, cascade, scorecard); certificate run:
30/30 certified. **Lean:** 6 proved, 3 sorry (`cascade_count_symbolic`,
`verification_margin_soundness`, `s11_optimal_value` [deliberate]),
7 axioms. `lake build`: not run here; ready at `lean/tct_squares/`.
