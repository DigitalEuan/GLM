# Development-required ledger — tct_squares

- lemmas total: 9
- proved (sorry-free): **6**
- `sorry` (development required): **3**
- axioms: **7**
- definitions: 2

## sorry lemmas

- `cascade_count_symbolic` : `∀ (m L : ℕ), m + (L + 1) + L = m + 2*L + 1`
  - gap: requires omega/ring (Mathlib) or manual algebra; the closure count is verified concretely at every cascade step in scripts/column3/05 (two-path: recursive vs. closed form)
- `verification_margin_soundness` : `∀ (x : ℚ), x * x < 0 → False`
  - gap: stand-in for the soundness certificate: proving that float64 SAT separation with a 1e-9 margin implies true non-overlap requires interval-arithmetic formalization (Mathlib) or exact algebraic predicates (exact predicates on rotated squares); our certificate is MEASURED with declared margin, not machine-checked
- `s11_optimal_value` : `∀ (L : ℚ), L = 38771/10000`
  - gap: DELIBERATE TARGET, EXPECTED UNPROVEN: no closed characterization of s(11) (or any non-trivial s(n)) is known; optimality proofs exist only for n in {1..8, 10, 14, 15, 24, 35} and square/adjacent families. This sorry marks the combinatorial-geometry wall of the competition

## axioms (assumed)

- `friedman_survey_data` : `Prop` — literature premise (Friedman, EJC DS#7 2009): best-known packings and bounds for s(n), n <= 100; Goebel/Cottingham/Stenlund/Cantrell pattern families
- `nagamochi_theorem` : `Prop` — theorem premise (Nagamochi 2005): s(k^2-2) = s(k^2-1) = k for all k - grid optimal for these n, no improvement possible
- `kearney_shiu_s6` : `Prop` — theorem premise (Kearney-Shiu 2002): s(6) = 3 - our engine's REFUSAL to pack 6 squares below 3 is consistent with this theorem
- `stromquist_s10` : `Prop` — theorem premise (Stromquist 2003): s(10) = 3 + 1/sqrt(2)
- `competition_metric` : `Prop` — rules premise: score = sum(L/sqrt(n) - 1); missing puzzle charged the grid ceiling; partial submissions allowed
- `engine_instrument` : `Prop` — instrument premise: the pressure-settling engine is a MEASURED search instrument (float64, deterministic LCG); certification margin 1e-9 declared
- `optimality_open` : `Prop` — conversational premise: for most n the optimal s(n) is unknown; found packings are upper bounds only

## To verify

```bash
cd lean/tct_squares && lake build
```
0 sorry = fully described; each sorry above is exactly what remains.
