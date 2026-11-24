# 88 — Screening the combinatorial moves against `p < gain / L` (run 129)

Doc 87 (run 128) reduced the local route to one inequality: the squeeze banks `gain` and the cheapest local
legalisation pays `p · L`, so a candidate is convertible only if the projection leaves

```
p  <  gain / L          (6.5e-4 at n = 33 … 1.3e-4 at n = 942)
```

That was measured on six rows with the plain squeeze. Run 129 asks the combinatorial question the earlier runs
had not answered: **does changing which cell sits where — before the squeeze — move `p` under the bar?** It
samples three move families and a control on **ten unbeaten rows × three seeds**, and it screens: a candidate
already `10×` above its bar is recorded and not converted, so the budget goes to the candidates that could pay.

**Result: 128 candidates, none under the bar.** The closest is `2.58×` over, on the smallest row. The four
candidates worth pricing were converted exactly, and every one lost `4.3e-3 … 5.5e-3` of side.

No row, table entry or score changed. `submission.csv` and `WHITEBOARD.md` are untouched; the score is still
`22.218056945` (553 beats, 447 grid). **Doc 87's numbers are not altered here** — its record is read as a
control (§2), never rewritten.

## 1. The screen

| piece | definition |
|---|---|
| candidate | `structure.attempt(n, kind, seconds, seed)` — squeeze at `L0 − 4e-3` and project, unchanged from run 126 (8 s per draw here) |
| measurement | `legal_slide.check_pose` on the projected pose: the deepest violating pair `p`, at 40 digits in `Decimal`, over the `REACH`-complete pair list |
| bar | `gain / L0`, with `gain = L0 − L_squeeze` **of that draw** — its own bar, not a nominal one; `gain` ranged `2.0e-3 … 3.97e-3`, so the bar ranged `1.31e-4 … 6.55e-4` across the ten rows |
| decision | `p < bar` → convert now; `p < 10 · bar` → price it on request and give the row two extra seeds; anything further out → record and stop (`should_convert`, tested in §2) |
| families | plain squeeze (control, `kind 0`), displaced cell (`kind 1`, its fallback branch), 2×2 block rotation (`kind 2`), and a **legal void swap** (`kind 3`, §3) |
| rows | `33, 75, 160, 250, 350, 439, 560, 662, 770, 883` — ten evenly spaced unbeaten rows |

The early stop is the point of the screen: `check_pose` costs one exact sweep, while the conversion costs a
bisected minimal legalisation plus the move set. 124 of the 128 candidates were screened without being converted.

## 2. Controls (`python3 scripts/p_screen.py --selftest`)

| control | what it shows | result |
|---|---|---|
| **1** bar arithmetic, against doc 87's own record | `gain`, `bar`, `p` and `p/bar` recomputed from `legal_relaxed128.json` must reproduce the documented row | n = 33: `gain 3.9266e-3`, **`bar 6.5443e-4`** (doc 87: `6.544e-4`), `p 3.5893e-3`, **5.5×** over — and `payback ÷ (p·L0) = 0.83`, the small-`n` coefficient of the law |
| **2** the decision function, five cases | under the bar converts, inside the margin is priced, outside is screened, and `p = bar` exactly is **not** a pass | `0 → convert`, `0.9 bar → convert`, `9 bar → convert`, `11 bar → screen`, `1.0 bar → priced but not under`; and `no gain → no conversion` |
| **3** non-vacuity | a pass is reachable, so "fail" is not the function's only output | a legal 4×4 at side 4 has `p = 0`; with a `2e-3` gain its bar is `5e-4` and it **passes** |
| **4** a real rejection, not a hypothetical one | a measured failed draw is screened | run 128's worst row (n = 942): `p 5.215e-2` vs bar `1.281e-4` = **407×**, `convert = False` |

## 3. The void-swap family, and why it needed its own implementation

`structure.attempt`'s `kind 1` is *meant* to be the void move: it samples a free-space point with `1.02`
clearance from every cell. **On these poses no such point exists** — 0 of 32 draws found one, so every kind-1
candidate was the fallback branch (a small displacement) and the "teleport into a void" family was never
instantiated at all. That is the same fact doc 75 recorded from the other side (every void in a frontier pose is
a squashed unit cell) and doc 87 measured on relaxed poses (no free unit seat).

The void move that *is* available is run 127's: a wall cell is moved to an exact unit-lattice seat inside the
pose, legal at the destination at 40 digits, and the rearranged pose is then squeezed. `p_screen.void_swap`
implements exactly that, tries two cells on each of the four walls, and rejects a swap that is illegal or grows
the side. Availability is the finding: **29 of 32 draws found no seat at all**, and no row above n = 33 had one.
A narrower first version (one seeded cell per wall) found a seat in 1 of 31 draws; widening it to eight wall
cells is what makes the availability number a measurement rather than an artefact of the search order.

## 4. The screen: 128 candidates, none under the bar

`python3 scripts/p_screen.py --rows 33,75,160,250,350,439,560,662,770,883 --seeds 3,4,5 --seconds 8`
(record `workspace/push/p_screen129.json`; per-row adaptive extension added 2 seeds to n = 33, giving 32 draws per
family). Each cell is the **median `p` over seeds with the `[min–max]` spread**; small rows are the only ones near
the bar, and the spread is 2–4× of the median at n = 33 but under 1.2× at n = 75.

| n | bar | plain (control) | displace one cell | void swap | rotate 2×2 | best family | min p/bar |
|---|---|---|---|---|---|---|---|
| 33 | 6.546e−4 | **3.369e−3** [1.7e−3–7.1e−3] | **3.942e−3** [1.7e−3–6.9e−3] | 4.994e−3 (3 draws) | **4.319e−3** [2.1e−3–7.4e−3] | plain | **2.6×** |
| 75 | 4.366e−4 | **4.778e−3** [4.4e−3–4.8e−3] | **6.642e−3** [6.3e−3–6.8e−3] | no seat (3) | **1.346e−2** [8.0e−3–2.1e−2] | plain | 10.2× |
| 160 | 3.040e−4 | **1.118e−2** [9.7e−3–1.7e−2] | **6.990e−3** [6.3e−3–1.2e−2] | no seat (3) | **6.703e−2** [6.4e−2–7.3e−2] | displace | 20.7× |
| 250 | 2.429e−4 | **3.446e−2** [2.5e−2–1.5e−1] | **2.774e−2** [2.3e−2–3.8e−2] | no seat (3) | **2.161e−2** [1.3e−2–5.0e−2] | rotate | 52.6× |
| 350 | 2.064e−4 | **2.876e−2** [1.8e−2–4.1e−2] | **2.945e−2** [2.0e−2–6.5e−2] | no seat (3) | **9.269e−2** [8.9e−2–1.5e−1] | plain | 84.8× |
| 439 | 1.873e−4 | **3.937e−2** [1.7e−2–5.0e−2] | **3.863e−2** [2.6e−2–6.6e−2] | no seat (3) | **1.217e−1** [1.2e−1–1.3e−1] | displace | 91.0× |
| 560 | 8.319e−5 | **4.901e−2** [2.4e−2–5.2e−2] | **3.757e−2** [3.2e−2–3.8e−2] | no seat (3) | **4.210e−2** [2.8e−2–1.4e−1] | displace | 174.5× |
| 662 | 1.509e−4 | **4.051e−2** [3.8e−2–7.9e−2] | **5.585e−2** [5.5e−2–6.4e−2] | no seat (3) | **4.906e−2** [4.8e−2–7.7e−2] | plain | 252.3× |
| 770 | 1.077e−4 | **5.907e−2** [5.0e−2–9.3e−2] | **6.846e−2** [4.4e−2–1.0e−1] | no seat (3) | **6.597e−2** [5.6e−2–7.4e−2] | plain | 699.6× |
| 883 | 1.310e−4 | **9.624e−2** [8.1e−2–1.0e−1] | **5.897e−2** [5.0e−2–8.4e−2] | no seat (3) | **5.396e−2** [3.8e−2–1.6e−1] | rotate | 578.9× |

**0 of 128 candidates pass; 99 are over the bar and 29 have no candidate at all** (the void swap's missing
seats). The bar itself is per-draw, which is why n = 560's is `8.3e-5` — that draw's squeeze banked only
`2.0e-3`, so it had less to spend and a tighter bar.

## 5. Attribution: the family does not matter, the row does

| family | draws | no seat | min `p/bar` | median `p/bar` | median `p` |
|---|---|---|---|---|---|
| plain squeeze (control) | 32 | 0 | **2.58×** | 141.9× | 3.161e−2 |
| displace one cell | 32 | 0 | **2.62×** | 141.0× | 3.086e−2 |
| void swap | 32 | **29** | **2.61×** | 7.7× (3 draws only) | 4.994e−3 |
| rotate a 2×2 block | 32 | 0 | 3.14× | **293.3×** | 5.174e−2 |

* **No family gets near the bar.** The best single draw anywhere is `2.58×` and it is the *control*, not a
  combinatorial move. The three families that run are separated by less than their own seed spread on the rows
  where they are comparable (n = 33: 2.58 / 2.62 / 2.61 / 3.14).
* **Block rotation is the worst family**, at twice the median ratio of the other two (293× against 141–142×),
  and it is systematically worst on the large rows (n = 439: 658×; n = 350: 447×). A 90° rotation of a 2×2 block
  in a jammed pose is a large local disturbance that the projection then has to repair, and it repairs it to a
  bigger residual.
* **The void swap is mostly unavailable**, and where available (n = 33 only) it lands at `2.61×` — the same
  place as everything else. Its median is small (7.7×) because it only has three draws and all three are on the
  smallest row; that number must not be read as "the void swap is 18× better".
* **The ordering of the families changes with the row** (best-by-median is plain at 33, 75, 350, 662, 770;
  displace at 160, 439, 560; rotate at 250 and 883), and the same family's median moves by 1.6–2.6× between
  the best and worst row. So the attribution is: *the depth is set by the row's scale, not by which cell moved.*

## 6. The four confirmations at 20 s: the screen's prediction, measured

The best draw of each family (n = 33) was re-run at 20 s — 2.5× the screen's budget — with the full exact
conversion (`legal_scale`, then the legal move set) so the prediction is checked against a dL rather than
assumed. Record `workspace/push/p_screen129_confirm.json`.

| family | `p` | `p/bar` | `f*` | payback | dL | moves | certified |
|---|---|---|---|---|---|---|---|
| plain (control) | 1.707e−3 | **2.58×** | 1.001710 | +8.542e−3 | **−4.573e−3** | 0 + 3 | side 6.00457258, **0 violations** |
| displace one cell | 1.662e−3 | **2.51×** | 1.001665 | +8.316e−3 | **−4.348e−3** | 0 + 3 | side 6.00434759, **0 violations** |
| rotate a 2×2 block | 1.894e−3 | **2.86×** | 1.001897 | +9.478e−3 | **−5.507e−3** | 0 + 3 | side 6.00550734, **0 violations** |
| void swap | 1.844e−3 | 2.79× | 1.001848 | +9.231e−3 | **−5.267e−3** | 0 + 3 | side 6.00526692, **0 violations** |

Every conversion lost side, by `4.3e-3 … 5.5e-3`, which is `payback − gain` as doc 87's law predicts
(`8.3e-3 − 3.9e-3 = 4.4e-3`). **The screen is not a budget artefact**: at 2.5× the budget the same draws give
`p` within 9 % of their 8 s values (three improved, one worsened), and the ranking is unchanged.

## 7. What it would take

For these rows the law is `dL ≈ gain − 0.83 · p · L`, so the crossing is

```
p* = gain / (0.83 · L)  ≈  7.8e-4  at n = 33      (the bar p < gain/L is the conservative form)
```

and the best draw on the only row within reach sits at `1.66e-3 … 1.71e-3`, i.e. **2.1× to 2.6× above the
crossing**. At n = 770 and n = 883 the same requirement is `700×` and `580×` away. Since

* the three available families move `p` by less than 10 % against the control on comparable rows,
* the seed spread is 2–4× at n = 33 and under 1.2× at n = 75, and
* the void swap is unavailable on 9 of the 10 rows,

the combinatorial moves tested here cannot supply the factor. A random single-cell move changes *where* the
overlap is, not *how deep*. What would move the number is a rearrangement whose projection residual is
structurally smaller — an exact-contact or lattice-seam arrangement measured at the target side *before* any
relaxation — which is the same conclusion doc 87 reached from the continuous side, now with ten rows and 128
draws behind it.

## 8. Files, records, checks

* `scripts/p_screen.py` — new driver (discovery, outside the float audit by the same rule as `structure.py`: it
  hands a float pose to the relaxer and names `float` in doing so). Functions: `family_of`, `bar_of`,
  `should_convert`, `measure`, `convert`, `squeeze_from`, `void_swap`, `screen`, `row_list`, `median`,
  `summarise`, `selftest`.
* `workspace/push/p_screen129.json` — 128 candidates: per candidate `n`, `kind`, `family`, `seed`, `moved`,
  `L0`, `squeeze_side`, `gain`, `p`, `violations`, `worst_pair`, `bar`, `ratio`, `passes_bar`,
  `sweeps_completed`/`sweeps_aborted`, `patches_solved`, `screened`, `screen_reason`, `cells_tried` (void swap).
* `workspace/push/p_screen129_confirm.json` — the four 20 s confirmations, each with `f*`, `payback`,
  `side_final`, `dL`, the move counts and the 40-digit certificate.
* Guards green: `legal_slide --selftest` **8 controls** (P, N, N2, N3, V, E, F, S), `p_screen --selftest`
  **4 controls**, `structure --control` (A 100.0 %, B absorbed at 4.0030358954), `structure --check-solver`
  (same objective, faster), `perturb`, `anchor_chain`, `void_insert`, `true_geom` selftests, `sqscore`
  **22.218056945** (553 beats, 447 grid), `record_guard` OK, `glm_wheels --audit` **684 functions, 0 offenders**
  (unchanged: `p_screen` is a discovery driver, not an audited decision module), `py_compile` OK.
  `submission.csv` and root `WHITEBOARD.md` untouched; doc 87 unedited.
