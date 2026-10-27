# Round 40 study folder — the open bit at the white diagonals (To Do 45, 46)

Everything here is **EMP** (computations, not machine-checked).  The Lean side of Round 40 is
`RequestProject/GLM/Rule30/Transients.lean` (FORMAL) and `TransientsData.lean` (CERT).
Integer and bit operations only.

## Programs

| File | What it does |
|---|---|
| `bandfast.c` | Bit-packed left band of Rule 30 (distances `0..W-1` from the left edge; a closed system). Runs until `row(t) = row(t-64)`, which is an exact certificate that every diagonal `< W` is 64-periodic from then on. Prints the white diagonals, the outer period and parity, and the bit after each white. |
| `patdump.c` | Same, prints the eventual patterns (phase `t mod 64`) of chosen diagonals. |
| `transient.c`, `syncfront.c`, `syncfront2.py`, `probe.c`, `probe_white.py` | Exact transients (settling times), synchronisation of two rows, the last black cell of a white diagonal. |
| `fscan.c` | Iterates the proved eventual-pattern law `F` (`WhiteDiagonals.lean`) between white diagonals. |
| `localband.c` | A stretch of diagonals driven at its outer edge by known eventual patterns, started from any filling (the run-up experiment). |
| `seeds_scan.py`, `branch_scan.py` | Hypotheses H1–H4 over random rows. Outputs `r40_seed_scan.json`, `r40_branch_scan.json`. |
| `runup_validate.py` | Hypothesis H9 against the full automaton. Output `r40_runup_validation.json`. |
| `recur.c` | Hypothesis H7 (the certified-reset recursion), refuted. |
| `predict_bit.sh` | The prediction for the open bit at `1420878968`. Output `r40_bit_prediction.txt`. |

## Hypotheses and outcomes

| # | Hypothesis (stated before the run) | Outcome |
|---|---|---|
| H1 | Every row with a left edge has the white diagonals of the seed up to the first even white diagonal (prediction of the Round 40 theorem). | Confirmed on 399 random rows; then **proved** for every row through `53207` (`left_edge_rows_agree_up_to_shift`). |
| H2 | At an even white diagonal the two branches are taken by about half of the rows. | **Refuted.** All 301 random rows (width 2–40), and 20 rows with fully random bands of width 100 to 99 999, take the seed's branch at `53207` and at `58286`: white list `2, 7, 28, 399, 53207, 58286, 87866` with parities o, o, o, o, e, e, o. |
| H3 | Settling times grow about linearly with slope ≈ 1. | Slope ≈ 1.33: the band of width `W` settles at `1.3308 W … 1.3331 W` for every row tried (`W = 100 000`). The proved bound is `1 + D·Q` (`ldiag_perFrom_linear`). |
| H4 | The branch depends on simple features of the seed. | Moot (H2: no row deviates). |
| H7 | The settling times follow the "certified reset" recursion, and the bit is the reset value. | **Refuted**: the recursion settles with slope ≈ 2 and predicts a white at 72575 instead of 58286. |
| H8 | Two rows synchronise deep inside the transient. | **Refuted**: with the best shift, agreement starts only about where the diagonals settle. |
| H9 | **Run-up universality.** A stretch driven at its outer edge by the true eventual patterns, from any filling, reproduces the true pattern after an even white diagonal once the run-up `c` before the white is long enough. | Validated against the automaton: at `53207` and `58286`, `c ≥ 1000` gives 8/8 fillings correct (`c ≤ 300`: mixed). At **odd** white diagonals the phase is not reproduced (2/8–6/8). This matches the symmetry: there the two choices differ only by a time shift (`odd_white_complement_is_shift`), and the driven stretch commutes with that shift. |

## The prediction (To Do 46)

At the even white diagonal `w = 1420878968` all 24 runs (run-ups `c = 3000, 10000, 30000,
100000`, six random fillings each) give the post-white pattern `6cbda353`, which is Round 39's
"bit 1" branch.  Iterating the proved law from it gives the next white diagonal at
**`2107985254`** with outer pattern `ed91e45c` of **odd** parity, so **period 64 from diagonal
`2107985255`**.  By the Round 40 theorem the open bit at that odd white diagonal does not matter,
so the next white after it is fixed by the pattern law alone. Iterated at period 64, the law finds
**no white diagonal in `2107985255 … 32107985254`** (3·10¹⁰ diagonals, `fscan_q64.txt`).

Status: **EMP** (prediction).  It rests on proved laws plus H9, which is validated at two even
white diagonals but not proved.

## Reproduce

```
gcc -O3 -o bandfast bandfast.c && ./bandfast 100000 1      # white list to 100000, exact
python3 branch_scan.py 100000 300                          # H1, H2, H4
python3 runup_validate.py                                  # H9
./predict_bit.sh                                           # the prediction
```
