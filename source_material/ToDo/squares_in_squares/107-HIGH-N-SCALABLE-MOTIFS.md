# 107 — The scalable motifs on n = 101..1000, decided exactly (Run 151)

**Headline.** Run 151 asked whether our delivered rows in 101..1000 have actually *exploited* the
scalable constructions of the literature — recursive grid products, Friedman's unit-border inflation, and
the parametric strip / 45° / rational-rotation motifs — and answered it with an exact audit rather than
an opinion. From **519 rows rebuilt exactly in Q(√2)** (446 all-axis, 73 with 45° cells, from the CSV's
own decimal text) the three families produce **33,074 candidates over all 900 rows** of the window, and
**not one is a strict beat**: the best candidate at any row is either the delivered side itself, within
the 1e-8 noise floor, or above it.

| family | candidates | rows reached | strict beats | best margin vs delivered |
| --- | --- | --- | --- | --- |
| A — k×k products with cell trims (`k = 2, 3`) | 28,904 | 900 | **0** | **−1.5e-9** (row 133) |
| B — Friedman unit-border inflation, iterated | 4,052 | 547 | **0** | **+1.9e-9** (row 962) |
| C — rational-word block + exact corner fill | 118 | 91 | **0** | −0.177 (row 106) |

A negative margin means the candidate is *above* the delivered side; a positive one below it. The two
near-zero margins are the point: they are the same construction on both sides of the comparison, and
they agree to within the 12-decimal rendering noise of the CSV (row 5's side, for instance, is 1.3e-9
away from its exact `2 + √2/2`). Nothing was promoted; `submission.csv` and root `WHITEBOARD.md` are
untouched and the total stands at **22.217428576** (554 beats, 446 grid ties).

---

## 1. What the brief asked, and what "already exploited" means

Three families were named: **(a)** recursive grid-product tiling — 2×2 copies at `n = 4m` and their trims
`4m−1..3`, 3×3 copies at `n = 9m` and `9m−1..8`; **(b)** Friedman's L-border inflation, `n → n + 2⌊L⌋ + 1`
at `L + 1`, propagated iteratively from every verified beating row; **(c)** the DS#7 parametric formulas
(diagonal strip, Göbel's 45° strip, centred/off-centre `b×b` 45° blocks, Cleemann's rational 8-15-17
spinor at `n = 272`).

"Already exploited" can be answered in exactly one way: build each family from its own law, in exact
arithmetic, and compare its side with the delivered side at every row. That is what
`scripts/scale_motifs.py` does. It is **float-free**: the delivered sides are 45-digit `Decimal`s
computed with `true_geom`'s Decimal series from the CSV's decimal text, the candidate sides are elements
of `Q(√2)` read off exact poses, and the comparison is `L + 1e-8 ≤ delivered(n)` with `1e-8` an exact
`Fraction`. The bytecode audit names 24 decision functions, 0 of which touch a float.

## 2. The three families, as laws

**Bases.** A family needs something to grow from. A delivered row is rebuilt exactly when every cell's
angle is the 0° word or the 45° word: the centres are the CSV's decimal text (exact rationals), the words
are exact (`AXIS`, `word_45()`), so the pose is a `Q(√2)` sentence. **519 of the 1000 rows qualify.** The
rest carry arbitrary angles and are refused — replaying their decimals would make the audit approximate
in the one place it must not be. Each base is passed through the exact SAT gate before use.

**(A) k×k products.** From `m` squares in side `L`, `k²` translated copies give `k²m` in side `kL`; and
dropping any `r` of those cells gives `k²m − r` in the *same* side, for `0 ≤ r ≤ m−1`. Dropping cannot
create an overlap and cannot grow the box, so validity is structural — and every candidate that had been
a strict beat would still have gone through the gate. Written once, this is the whole family: **every n
in `[k²m − m + 1, k²m]` at side `kL`**, for `k = 2, 3`.

**(B) Friedman's unit-border inflation.** Put the base in the corner of an `(L+1)`-square and fill the two
unit strips with axis-aligned cells: `⌊L+1⌋` up one side, `⌊L+1⌋` along the other, the corner shared —

```
n' = n + 2⌊L+1⌋ − 1 = n + 2⌊L⌋ + 1,      L' = L + 1,
```

with `⌊·⌋` the exact floor in `Q(√2)`. Iterated up to 12 times from every base. The border cells are unit
squares at integer positions, so the side stays in the base's field and every step is exact.

**(C) The parametric motifs.** A `b×b` block of unit squares at a rational word — the 45° word, or the
8-15-17 word `(cos, sin) = (8/17, 15/17)`, or 3-4-5 as a control — corner-anchored, with every
axis-aligned unit square that fits *exactly* in the remainder added by a greedy exact fill (each cell
adjudicated pair by pair with the SAT predicate, bucketed by integer cell so the fill is fast). The count
and the side are read off the pose; no remembered formula is trusted. `b ≤ 20`, and the fill box is
widened by 0..2 units as a declared parameter.

## 3. The numbers, row by row

The audit reaches **900 of the 900 rows** in 101..1000 with at least one candidate. What the margins look
like across the window:

| best candidate's margin at a row | rows |
| --- | --- |
| within `1e-6` of the delivered side (the families *reproduce* the table) | **425** |
| between `1e-6` and `1e-2` above | 17 |
| more than `1e-2` above | 458 |

The first line is the real answer to the brief: on nearly half the window the table's own side **is**
these constructions. Row 962 is the cleanest witness — twelve different bases inflate into it, and the
exact cascade from row 901 lands at `31.520815300` against the rendered `31.520815284`, i.e. `1.9e-9`
*below* the delivered side: the table's row 962 **is** its own cascade, and the 1.9e-9 is the CSV's
12-decimal rendering, not a win. The same story at row 133, where a 2×2 product of row 34's pose gives
`12.000000003` against a delivered `12.000000002` (`−1.5e-9`).

The four rows the brief names explicitly:

| n | delivered | best candidate | margin |
| --- | --- | --- | --- |
| 101 | 10.535534 | B, `L = 10.535534` | 0 (the delivered row **is** the cascade) |
| 120 | 11.000000 | B, `L = 11.000000` | 0 (a grid tie, reproduced) |
| 272 | **16.965586** | A (2× row 68) `L = 18.000000` | **−1.034** |
| 1000 | 32.000000 | B, `L = 32.000000` | 0 (area-exact, reproduced) |

## 4. Why — the arithmetic, not the sampling

**(A) and (B) are the table's own constructions**, so their reachable rows are already at or below their
side; a family cannot beat the table that was built from it. The audit makes that concrete rather than
rhetorical: 425 rows reproduce to `1e-6`, and the two closest rows disagree only by rendering noise.

**(C) has an area ceiling and cannot reach it.** A `b×b` block at a word with `w = |cos| + |sin|` has
bbox side `bw`, so the spare area inside that bbox is `(w² − 1)b²`; the family's absolute ceiling is the
area bound `n = w²b², L = bw`, which is unreachable because a grid fill can never tile the two corner
triangles. What the exact fill actually reaches, and what the table has at those counts:

| word | `b` | cells | `L` | `L/√n` | delivered at that `n` |
| --- | --- | --- | --- | --- | --- |
| 45° | 10 | 166 | 14.142 | **1.098** (9.8 % above the floor) | 166 ties at **13.000** (0.9 %) |
| 8-15-17 | 10 | 147 | 13.529 | **1.116** (11.6 %) | 147 at **12.657** (4.4 %) |
| 8-15-17 | 13 | 289 | 18.000 | 1.059 | 289 ties at **17.000** (0 %) |
| 45° | 7 | 106 | 11.000 | 1.068 | 106 at **10.823** (2.3 %) |

So the parametric family is between one and two units above the table wherever it lands, and its best
members are *grid ties* (a rotated block plus an integer fill tends to land exactly on an integer side).
That is not a search failure: it is the shape of the family. It also explains `n = 272`: the rational-
block family does not produce that count at any `b ≤ 20`, `extra ≤ 2` — its neighbours are 259
(`17.588` against a delivered `16.591`), 289 (`18.000` against `17.000`) and 293 (`18.941` against
`17.623`), i.e. 1.0–1.3 above. Row 272's own pose is *not* an exact base either (it is not a 0/45° word
sentence), so the delivered `16.965586` there comes from a construction that is neither of these.

## 5. Controls

`python3 scripts/scale_motifs.py --selftest` — **9/9**:

1. the CSV is read exactly (1000 rows; side(5) against the exact `2 + √2/2`, gap `1.3e-9` — the 12-dp
   rendering, below the margin);
2. the exact gate on a 3×3 grid: `L = 3` exactly, 20 contacts;
3. row 20 rebuilds in Q(√2) from the CSV's own decimals and gates;
4. the product law: `4 × 20 = 80` at exactly `2L`, and `4 × 20 − 3 = 77` at the same side, both gated;
5. the border law: three inflations give `20 → 31 → 44 → 59` cells (the solver's own count law
   `2⌊L+1⌋ − 1`: +11, +13, +15) at `L + 3` exactly, gated with 129 contacts;
6. a duplicated cell is refused with a negative clearance, so the fill control is not vacuous;
7. the two named words at `b = 6`: 51 cells at 8.485 (45°) and 52 at 8.118 (8-15-17), with the spare area
   `S² − b²` printed — the family's ceiling in one number;
8. the comparison is against the *delivered* side (row 120 is a tie at `11.0000000018`: `11` is not a
   beat at margin `+1.8e-9`, `11 − 1e-6` is);
9. bytecode audit: 24 decision functions, 0 naming `float`.

## 6. Reproduce

```
python3 scripts/scale_motifs.py --selftest   # 9 controls
python3 scripts/scale_motifs.py              # the audit, ~2.5 min, ledger written
python3 scripts/scale_motifs.py --promote    # C1 on every strict beat (none to run)
```

Ledger `workspace/push/scale_motifs.json`: the base census, each family's candidate/row/beat counts and
best margin, every strict beat (none), and the best candidate at every row of the window with its family,
its exact side at 18 decimals and its margin.

## 7. What this closes, and what it leaves

**Closed.** (i) The question "have we exploited the scalable motifs above 100?" has an exact answer: on
all 900 rows of 101..1000, the three families together never beat the delivered side; on 425 of them they
*are* the delivered side. (ii) The parametric family's ceiling is arithmetic, not a matter of parameters:
its realised slack is 5.9–11.6 % above `√n` where the table sits at 0–4.4 %, and its best members are
grid ties. (iii) The `n ≤ 100` block is frozen (run 150): nothing in this run touched a row at or below
100, and both of the two larger audit families were propagated *from* those rows, not into them.

**Left, honestly declared.** (i) **519 of the 1000 rows are exact bases**; the other 481 carry arbitrary
angles, so families (A) and (B) cannot be grown from them exactly — a float replay would be needed, which
this project does not do for a proof. Rows above 100 whose pose is not a 0/45° sentence are therefore
outside the audit's reach *as bases*, though they are still reached as *targets*. (ii) The notch/strip
variants of the motifs (a strip that follows the carrier's seam, an asymmetric notch) are not in these
families — they are docs 105/106's subject and were decided there. (iii) The rational-block family uses a
greedy fill; a *purposeful* corner module (exact contact, not grid-aligned) is a different family and is
not audited here. (iv) Nothing here is a proof about *all* constructions: it is a decision about these
families' declared boxes, and the boxes are spelled out in §2 and in the ledger rather than summarised.
