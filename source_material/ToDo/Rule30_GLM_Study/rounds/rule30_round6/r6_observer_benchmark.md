# Round 6 observer benchmark (frozen predictors, disjoint test segments)

Evidence class of every number below: **EMP** (finite computation outside Lean).
A high accuracy is a *captured pattern*; an accuracy near 1/2 is only *no pattern found at this budget*, never a proof of escape.

| sequence | N | best predictor (test 2) | acc | best lag | acc | const-1 acc | golay-24 acc | wobble-arrow acc | proof status |
|---|---|---|---|---|---|---|---|---|---|
| rule30-centre | 131072 | lag-28 | 0.505829 | lag-28 | 0.505829 | 0.494568 | 0.501709 | 0.501678 | OPEN: P1 and P2 unproved. Lean proves only finite facts (no eventual period p <= 1000 starting <= 1000; exact wobble values to 10^6) and the equivalences P1 <=> escape from lag rules <=> escape from finite-state rules. |
| periodic-7 | 131072 | lag-7 | 1.0 | lag-7 | 1.0 | 0.571442 | 0.285736 | 0.428558 | FORMAL (trivial): eventually periodic, captured by lag-7. |
| biased-1/3 | 131072 | lag-3 | 1.0 | lag-3 | 1.0 | 0.333344 | 0.0 | 0.333344 | FORMAL: frequency 1/3 (Lean `exists_row_with_biased_column` uses this column). |
| champernowne | 131072 | lag-14 | 0.856964 | lag-14 | 0.856964 | 0.459229 | 0.496948 | 0.540771 | Known theorem (not in this package): normal in base 2. |
| sha256-counter | 131072 | lag-37 | 0.506683 | lag-37 | 0.506683 | 0.501587 | 0.494812 | 0.498413 | A fixed rule (hash in counter mode); nothing proved here. |
| rightwhite-row-periodic | 4096 | lag-2 | 1.0 | lag-2 | 1.0 | 0.5 | 0.0 | 1.0 | FORMAL: a right-white Rule 30 row with centre column 1,0,1,0,... (`exists_row_with_periodic_column`); captured by lag-2. |
| rightwhite-row-biased | 4096 | lag-3 | 1.0 | lag-3 | 1.0 | 0.333984 | 0.0 | 0.333984 | FORMAL: a right-white Rule 30 row with centre column of frequency 1/3 (`exists_row_with_biased_column`). |
| rule30-centre-4096 | 4096 | ctx-11 | 0.532227 | lag-62 | 0.530273 | 0.500977 | 0.520508 | 0.500977 | OPEN: P1 and P2 unproved. Lean proves only finite facts (no eventual period p <= 1000 starting <= 1000; exact wobble values to 10^6) and the equivalences P1 <=> escape from lag rules <=> escape from finite-state rules. |

Right-white rows built by column inversion have black-cell density 0.505 (periodic column) and 0.516 (biased column): the rows look like noise while their centre columns are captured by tiny rules.

Budgets: lag p <= 64, context order k <= 16. Run time 17.7 s.
