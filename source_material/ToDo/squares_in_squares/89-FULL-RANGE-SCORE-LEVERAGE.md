# 89 — The full row range, score leverage, and a constructed pocket net (run 130)

**Run 130, 2026-11-25.** Instruments `scripts/range_leverage.py` and
`scripts/construct_seam.py`; records `workspace/push/range_leverage130.json` and
`workspace/push/construct_seam130.json`. Doc 87 is untouched; `submission.csv` and root `WHITEBOARD.md`
are untouched.

**The question.** Runs 123–129 all attacked the same object: a delivered grid pose, squeezed. Doc 88 §7 said
what would move the number instead — an arrangement constructed at the target side, with exact contacts, so its
residual is zero before any relaxation — and asked for it to be tested on rows worth testing. This run
therefore does three things in order: (1) it measures the **whole** measured range, not the scored window, and
ranks every unbeaten row by what a unit of side is worth there; (2) it builds the one exact-contact family that
exists in closed form and measures it; (3) it records both against the guards.

---

## 1. The range, exactly

| source | rows | what it is |
| --- | ---: | --- |
| `workspace/submission/submission.csv` | **500,500 entries / 1,000 rows** | the scored table: `n = 1..1000`, one CSV line per square, header `id,n,square_id,x,y,angle` |
| `workspace/submission/table.json` | 1,000 | the same rows with the side as a 40-digit decimal string, a stored pose, and a provenance label |
| `json/extended_table_5000.json` | **4,000** | the measured extension: `n = 1001..5000`, fields `L, bound, grid, src` (a pose is stored for 33 rows only) |
| doc 08 / `beyond1000.py` | 4,794 designs | constructions to `n = 9900` (`k = 32..99`); **nothing above 9900 is measured anywhere** |

So the full measured range is `n = 1..5000` and the scored range is `n = 1..1000`. The distinction is not
cosmetic: `sqscore.guard()` **asserts** 1,000 rows, and a score is only computed over those.

**How the score is computed** (`scripts/sqscore.py`, the one scorer every instrument imports):

```
extent(state)   = max over axes of (max_i(x_i + e_i) - min_i(x_i - e_i)),  e_i = (|cos t_i| + |sin t_i|)/2
grid(n)         = ceil(sqrt n)                     exact, via isqrt
row_score(n, L) = L / sqrt(n) - 1                  lower is better
total           = sum over n = 1..1000 of row_score(n, L(n))      = 22.218056945
```

`extent` uses floats (the metric is defined on floats), the ratio is accumulated in `Decimal(30)`, and
`guard()` re-derives the delivered total from the CSV and raises rather than returning a wrong number. The
score is exactly **linear in each side with weight `1/sqrt n`** — `sqscore.marginal(n)` is that weight — which
is the whole basis of §2.

## 2. The unbeaten rows, in both ranges

An unbeaten row is one whose side is not below `ceil(sqrt n)` (the integer grid). Two sub-classes matter:

* **area-optimal**: `n = k^2` exactly. Then `L >= sqrt n = k` by area, so *no* arrangement can beat the row.
  These are not targets; they are theorems.
* **with room**: `n != k^2`, so `k/sqrt n - 1 > 0` is the score the row could still give.

| range | rows | beaten | unbeaten | area-optimal | with room | ceiling `Σ(k/√n-1)` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `n = 1..1000` (scored) | 1,000 | 553 | **447** | 31 | **416** | **7.195366** |
| `n = 1001..5000` (measured) | 4,000 | 805 | **3,195** | 39 | **3,156** | 25.719371 |
| total | 5,000 | 1,358 | 3,642 | 70 | 3,572 | 32.914737 |

The unscored range is where most of the unbeaten rows are — 3,195 of 4,000 (79.9 %) against 447 of 1,000
(44.7 %) — and it holds 3.6x the scored range's room. None of it can be scored: the metric stops at 1,000.

## 3. Leverage: what one unit of side buys, row by row

`d(row_score)/dL = -1/sqrt n`, so a unit of side reduction at row `n` is worth exactly `1/sqrt n` score. Ranked
by that weight the scored rows with room begin:

| n | k | L | `1/√n` | ceiling `k/√n-1` | band price `d(k)` | status |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 2 | 2 | 2 | **0.7071** | 0.4142 | – | **proved optimal `s(2)=2`** |
| 3 | 2 | 2 | 0.5774 | 0.1547 | – | **proved `s(3)=2`** |
| 6 | 3 | 3 | 0.4082 | 0.2247 | −0.672 | **proved `s(6)=3`** |
| 7 | 3 | 3 | 0.3780 | 0.1339 | −0.672 | **proved `s(7)=3`** |
| 8 | 3 | 3 | 0.3536 | 0.0607 | −0.672 | **proved `s(8)=3`** |
| 12 | 4 | 4 | 0.2887 | 0.1547 | +0.032 | open |
| 13 | 4 | 4 | 0.2774 | 0.1094 | +0.032 | open |
| 14 | 4 | 4 | 0.2673 | 0.0690 | +0.032 | **proved `s(14)=4`** |
| 15 | 4 | 4 | 0.2582 | 0.0328 | +0.032 | **proved `s(15)=4`** |
| 20 | 5 | 5 | 0.2236 | 0.1180 | **−0.131** | open |
| 21 | 5 | 5 | 0.2182 | 0.0911 | **−0.131** | open |
| 22 | 5 | 5 | 0.2132 | 0.0660 | **−0.131** | open |
| 23 | 5 | 5 | 0.2085 | 0.0426 | **−0.131** | open |
| 24 | 5 | 5 | 0.2041 | 0.0206 | **−0.131** | **proved `s(24)=5`** |
| 30 | 6 | 6 | 0.1826 | 0.0954 | +0.210 | open |
| 31 | 6 | 6 | 0.1796 | 0.0776 | +0.210 | open |

*(proved values: `optima.py`, Stromquist 2003 and Friedman DS7, compared exactly.)*

Two results that matter for budgeting:

* **Concentration.** The top 20 rows by leverage hold **2.013853 of the 416 rows' 7.195366** ceiling — 28.0 %
  of the scored room in 20 rows. Uniform spacing wastes 4.8 rows of budget for every row that can matter.
* **Leverage is anti-correlated with reachability at the top.** Nine of those 20 rows are **proved optimal**
  (`s(n)` published and equal to the delivered side), and they hold **1.124859 = 55.9 %** of the top-20's
  ceiling. The ranking's own top is therefore half closed by theorem: `n = 2, 3, 6, 7, 8, 14, 15, 24, 35` are
  not "hard", they are finished. A budget that sorts by `1/sqrt n` alone spends its first half on rows that
  cannot move.

## 4. Headroom: the band price, recomputed

`range_leverage.bands()` re-derives doc 75 §2's price from the rows themselves — frontier `m*` = the largest
beaten row of band `k`, `j* = k^2 - m*`, `V = L(m*)^2 - m*`, `d(k) = V - (j*-1)` — and reproduces the published
numbers: `k = 32` `V = 25.119`, `d = +0.119`; `k = 23` `V = 19.530`, `d = +0.530`; `k = 5` `d = -0.131`. So the
grid-frontier measurement is confirmed independently, in `Decimal`, from the table.

Cheapest next rows: `k = 3` (−0.672), `k = 5` (**−0.131**), `k = 7` (−0.021), `k = 9` (−0.004), `k = 10`
(−0.003), `k = 4` (+0.032). Dearest: `k = 29` (+0.922), `k = 11` (+0.929), `k = 26` (+0.985), `k = 14` (+0.988).

**The intersection is small and it is the budget answer.** High leverage *and* a band whose area is already
enough (`d < 0`) *and* not proved optimal leaves exactly:

> **`n = 20, 21, 22, 23`** (band `k = 5`, `d = -0.131`, leverage 0.209–0.224) and, one tier down,
> **`n = 12, 13`** (band `k = 4`, `d = +0.032`, leverage 0.277–0.289).

Everything cheaper is proved (`k = 3` → `n = 6,7,8`) or area-optimal (`n = 24`).

**Above 1000 the price is not merely negative, it is enormous** — because the extension's rows are constructed,
not squeezed: band `k = 33` frontier 1028 with `V = 31.9` against `j* - 1 = 60`, price **−28.08**; `k = 34`
−1.00; `k = 35` −1.06; `k = 36` −22.10. In the scored range the frontier spends 87–99.9 % of its void budget; in
the extension it spends a third of it. The rows above 1000 are waiting for better *constructions*, not for
area — which is exactly what §5 finds.

Also quantified: ext rows `1001..1024` (band 32) have **no beaten row at all** in the measured extension, so
they have no frontier above 1000 to price from; `sqscore`'s band 32 frontier (998) is the last one that costs
`+0.119`.

## 5. A constructed arrangement: the four-corner pocket net

Built in the exact field `Q(sqrt 2)` (`seam_wheels.Q2`), never in floats. An `a x a` upright block in each
corner, and one unit cell tilted 45° at the centre. The central cell's edge is at distance `1/2` from its
centre, so the corner blocks' inner corners lie **exactly** on it when

```
(L - 2a) / sqrt2 = 1/2        =>     L = 2a + sqrt2/2 ,      n = 4a^2 + 1 ,      grid k = 2a + 1
```

so the construction beats the grid by exactly `1 - sqrt2/2 = 0.292893` for **every** `a` — and the contacts are
exact, so `p = 0` before any relaxation. `construct_seam` gates it two ways: a cell-by-cell `exact_gate` (worst
penetration exactly `0`) and an O(1) exact argument (each block lies in `x + y <= 2a` while the central cell
needs `x + y >= 2a`, touching along one corner; the blocks are `sqrt2/2` apart; the central cell's left vertex
sits in the gap between the two left blocks).

**Control 1 — it reproduces a theorem.** At `a = 1` the construction gives `L = 2 + sqrt2/2 = 2.707106781187`,
which is `s(5)`, the *proved* optimum in `optima.py` (Stromquist). The arithmetic is not merely plausible; it
lands on a published exact value, and the delivered row 5 equals it to within `finalize`'s `1e-9` pad.

**Control 2 — it is rigid.** Replacing the central cell by a `p x p` tilted block, and allowing rectangular
corners `a x b`, gives `L = a + b + p/sqrt2` and `n = 4ab + p^2`. The exact constraint set is three inequalities:

* the diagonal pair of blocks forces **`a = b`** (with `2a <= a + b` on one diagonal and the mirror constraint on
  the other; unequal corners overlap the centre whatever `L` is);
* **containment** of the tilted block forces `p/sqrt2 <= a` (its bounding box is `p*sqrt2` square);
* the far diagonal is then free, because the bottom-right block has `x - y >= L - 2a = p/sqrt2` exactly.

Over the box `a, b <= 8, p <= 6` (**384 candidates**) the arithmetic beats the grid **12 times**, and the
constraint set admits **8**: all with `p = 1, a = b`, all at `n ≡ 1 (mod 4)`. With `a = b` and containment,
`L < k = 2a+1` requires `p < sqrt2`, i.e. `p = 1`. **The pocket net beats the grid at `n = 4a^2+1` and nowhere
else** — that is the family's exact reach, and it is 8 rows in `n <= 1000` (5, 17, 37, 65, 101, 145, 197, 257,
325, 401, 485, 577, 677, 785, 901 — 15 rows, `a = 1..15`) and 35 rows up to 5000.

**Why it cannot be pushed.** Its own density deficit is

```
(2a + sqrt2/2)^2 - (4a^2 + 1) = 2 sqrt2 a - 1/2  ≈  2.83 a  cells of area
```

— at `a = 15` (`k = 32`) it gives up **41.9 cells** of area to save **0.2929** of side. The row needs to *gain*
cells, not spend them. The family is a corner trick that pays at one count per band; it is not a density gain.

## 6. The family against both tables

35 rows `n = 4a^2+1 <= 5000` compared exactly (`Decimal` 45 digits against the stored 40-digit sides):

| verdict | rows | which |
| --- | ---: | --- |
| family better (smaller exact side) | **11** | 1157, 1601, 1937, 2305, 2501, 2705, 2917, 3365, 3845, 4097, 4625 |
| table better | **23** | 17, 37, 65, 101, 145, 197, 257, 325, 401, 485, 577, 677, 785, 901, 1025, 1297, 1445, 1765, 2117, 3137, 3601, 4357, 4901 |
| equal to the pad | 1 | 5 |

Two facts follow, and the second is the useful one:

* **In the scored range the family is never better.** All 15 of its rows are already beaten, and the delivered
  table beats the family on 14 of them by **0.032 to 0.186** (`n = 17`: 4.675530 vs 4.707107; `n = 901`:
  30.520815 vs 30.707107). The delivered constructions are smarter than the elementary net everywhere it
  applies.
* **In the extension the elementary net is better on 11 rows**, by **0.042 to 0.293** (median 0.234) — e.g.
  `n = 1157` 34.970563 → 34.707107, `n = 2305`, `2705`, `3845`: 49.0 / 53.0 / 63.0 → 48.707 / 52.707 / 62.707.
  Those 11 rows are unscored, so nothing is promoted from them; what they show is that the `n > 1000` table's
  side is not tight — consistent with the −28 void price of §4. The extension's unbeaten count is a statement
  about its constructions, not about the geometry.

## 7. The target measurement: constructed residual at the target side

For each leverage-ranked row, build the family arrangement that holds **exactly `n` cells** (the windmill plus
columns of `2a` upright cells beside it — wall-to-wall, so legal by construction) and measure its exact side
against the target `L_t = k - 1/8`. `p` is the residual penetration at that side, and the bar is run 129's
`gain/L` for that gain:

| n | k | family arrangement | L | `p` | bar | `p/bar` |
| ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 2, 3 | 2 | no windmill fits below `n` | – | – | 0.0667 | – |
| 6, 7 | 3 | windmill(1) + 1 column of 2 | 3.7071 | **0.8321** | 0.0435 | **19.1x** |
| 8 | 3 | windmill(1) + 2 columns of 2 | 4.7071 | 1.8321 | 0.0435 | 42.1x |
| 12, 13 | 4 | windmill(1) + 4 columns of 2 | 6.7071 | 2.8321 | 0.0323 | 87.8x |
| 14, 15 | 4 | windmill(1) + 5 columns of 2 | 7.7071 | 3.8321 | 0.0323 | 118.8x |
| 20, 21 | 5 | windmill(2) + 1 column of 4 | 5.7071 | 0.8321 | 0.0256 | 32.4x |
| 22 | 5 | windmill(2) + 2 columns of 4 | 6.7071 | 1.8321 | 0.0256 | 71.4x |
| 1001–1024 | 32 | windmill(15) + 4 columns of 30 | 34.7071 | 2.8321 | 0.0039 | **722.2x** |

`p` is exactly `sqrt2/2 + 1/8 + (columns - 1)`: the pocket's `0.7071` is a **constant**, not a rate, while the
bar `(1/8)/L_t` falls like `1/L`. So the constructed residual is 19x the bar at `k = 3` and **722x** at `k = 32`
— the *same construction*, the same constant, a bar 17x smaller. Constructed arrangements do not become
competitive as `n` grows; they get further away.

## 8. The exact anchor grammar: measured, not assumed

`anchor_chain.settle(n, L)` is the repo's exact constructive builder (walls, corners, two-contact closure, all
contacts at clearance `>= 0`, no relaxation at all). Run at the grid side and below it on the smallest
high-leverage row:

| n | L | placed | why | nodes | refusals | seconds |
| ---: | --- | ---: | --- | ---: | ---: | ---: |
| 6 | 3 | **6/6** | target reached | 17 | 85 | 8.9 |
| 6 | 2.99 | 5/6 | node cap 60 after 5 cells | 61 | 405 | 36.3 |
| 6 | 2.875 | 4/6 | node cap 60 after 4 cells | 61 | 400 | 32.5 |

It builds the grid, and it does not build the row *below* the grid within the cap. **`n = 10` at `L = 3` did not
close in 300 nodes / 120 s**, so the grammar cannot reach even the fourth row of the leverage ranking in budget.
This is recorded as a **limitation, not a proof**: a capped search that stops at 5 of 6 cells says nothing about
the row's geometry, only about the grammar's throughput. Where it does exhaust (a `node_cap` of `None`) it is
exact, which is why the repo's own forward tests are all `n <= 7`.

## 9. Verdict, and what it would take

**No candidate. Nothing promoted.** `submission.csv` and root `WHITEBOARD.md` are untouched, and no row's side
changed: the score is `22.218056945` with 553 beats and 447 unbeaten rows, exactly as delivered.

* **The scoring range is `n = 1..1000` and nothing above it is scored** (§1). The measured range is 1..5000,
  designs exist to 9900. Half the unbeaten rows on earth (3,195 of 5,000) are above the metric's last row.
* **Budget should follow `1/sqrt n` x headroom x reachability, not `1/sqrt n` alone**: the top 20 rows by
  leverage hold 28.0 % of the scored room, but 55.9 % of that sits behind published optima. The open,
  area-affordable, high-leverage rows are **`n = 20..23`** and then `n = 12, 13` (§3–§4).
* **A closed-form exact-contact construction exists and is rigid** (§5): it beats the grid by exactly
  `0.2929` at `n = 4a^2+1` and by nothing anywhere else, because its density deficit `2.83a` cells grows with
  the band while its side saving does not.
* **What would take the scored rows** is therefore an arrangement that is *full at the row's own count* with
  contacts in a field, which is what doc 88 §7 asked for and what §5 shows this family is not. The extension's
  `−28` void price at `k = 33` says the search for such arrangements is cheap *above* 1000 and expensive below
  it — a statement the scoring window makes academic.

## 10. Files, records, checks

* `scripts/range_leverage.py` (new, `Decimal`/`Fraction`/`isqrt` only — no float named): `k_of`, `lam`,
  `ceiling`, `load_scored`, `load_ext`, `status`, `bands`, `inventory`, `rank`, `headroom`, `show`, `selftest`,
  `main`.
* `scripts/construct_seam.py` (new, exact `Q(sqrt 2)` throughout — no float named): `to_dec`, `k_of`, `block`,
  `windmill`, `struct_gate`, `pen_at`, `family_gate`, `scan`, `hybrid`, `family_side`, `load_sides`, `compare`,
  `target_rows`, `anchor_probe`, `selftest`, `main`.
* `workspace/push/range_leverage130.json` — inventory, both band censuses, both rankings.
* `workspace/push/construct_seam130.json` — the 384-candidate scan (with the refused arithmetic winners), the
  35-row table comparison, the 18 target measurements, the three anchor probes.
* **Controls.** `range_leverage --selftest` **5 controls**: the delivered total re-derived from `table.json`'s
  L strings (`22.218056945`), the 553/447 split, `ceiling = 0` exactly at `n = 4, 100, 961`, strict
  monotonicity of `1/sqrt n`, and the band price reproducing doc 75 (`k = 32` `V = 25.119` `d = +0.119`).
  `construct_seam --selftest` **4 controls**: `windmill(1)` = `s(5)` with `exact_gate` worst penetration `0`, a
  refusal at `L - 1/100` with exact overflow `1/100`, the 8/384 rigidity, and row 5 equal to the delivered side
  to the pad.
* Guards green: `p_screen --selftest` **4**, `legal_slide --selftest` **8**, `structure --control` and
  `--check-solver`, `perturb`, `anchor_chain`, `void_insert`, `true_geom` selftests, `sqscore`
  **22.218056945** (553 / 447), `record_guard` OK, `glm_wheels --audit` **684 functions, 0 offenders**
  (unchanged: both new files are discovery instruments, not audited decision modules), `py_compile` OK.
