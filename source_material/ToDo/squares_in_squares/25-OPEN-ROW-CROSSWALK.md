# 25 — open-row literature crosswalk, and the n = 11 check (run 57)

Instrument `scripts/crosswalk.py`, ledger `workspace/push/crosswalk.json`.
Read-only: no row changed, no score moved.

Answers the run-57 review's two asks: re-rank after excluding the proved rows,
then crosswalk every open row against the published record and check n = 11.

## 1. The method, and the one rule that matters

For each open row:

| column | source |
| --- | --- |
| delivered side | `sqscore.extent` on the canonical CSV |
| best published construction | Friedman DS7 (2009) **Table 1**, with author and figure; exact closed form where the table gives one |
| published lower bound | DS7 **Table 2**, with author; plus Stromquist Thm 2 for s(11) |
| status | `at_published` / `beats_published` / `above_published` |
| forward value | the suffix of that residue column, priced with the canonical scorer, **if** a base existed exactly at the published side |

The rule the review asked for is applied literally: **only a row where a
published construction is strictly smaller than the delivered side is a target.**
A gap between the published best and the published lower bound is *not* a target —
run 56 showed a general bound missing the true optimum at n = 10 by 0.5145, so
that gap is unresolved mathematics, not available score.

## 2. The crosswalk

| n | r | delivered | best published | Δ (ours − pub) | status | pub − LB | forward value |
| ---: | ---: | ---: | --- | ---: | --- | ---: | ---: |
| 11 | 2 | 3.877083592 | 3.8771 Trump | −8.5e-9 | at | 0.0882 | 0.000000 |
| 12 | 3 | 4.000000002 | 4 grid | +1.5e-9 | at | 0.2111 | 0.000000 |
| 17 | 1 | 4.675530095 | 4.6756 Bidwell (3 angles) | −7.0e-5 | at | 0.2304 | 0.000000 |
| 18 | 2 | 4.822875657 | `7/2 + √7/2` Hämäläinen | +1.6e-9 | at | 0.3777 | 0.000000 |
| 19 | 3 | 4.885618085 | `3 + 4√2/3` Wainwright | +1.6e-9 | at | 0.4003 | 0.000000 |
| 20 | 4 | 5.000000002 | 5 grid | +1.6e-9 | at | 0.5147 | 0.000000 |
| 26 | 1 | 5.621320345 | `7/2 + 3√2/2` Friedman | +1.6e-9 | at | 0.2295 | 0.000000 |
| 27 | 2 | 5.707106783 | `5 + 1/√2` Göbel | +1.7e-9 | at | 0.3153 | 0.000000 |
| 28 | 3 | 5.824444618 | `3 + 2√2` Göbel | **−3.98e-3** | **beats** | 0.3167 | 0.000000 |
| 29 | 4 | 5.933833464 | 5.9344 Gensane/Ryckelynck (6 angles) | **−5.67e-4** | **beats** | 0.4227 | 0.000000 |
| 30 | 5 | 6.000000002 | 6 grid | +1.7e-9 | at | 0.4883 | 0.000000 |
| 31 | 6 | 6.000000002 | 6 grid | +1.7e-9 | at | 0.3585 | 0.000000 |

**Tally: 10 `at_published`, 2 `beats_published`, 0 `above_published`.**

Six of the ten "at" rows match the published closed form to 1e-9 or better, which
is the exact-gate level: the table is not merely close to Hämäläinen's,
Wainwright's, Friedman's and Göbel's constructions — it **is** them, to the pad.
The two `beats` rows are the interesting ones for provenance: at n = 28 the
delivered side is 0.00398 below Göbel's `3+2√2` as printed in the 2009 survey, and
at n = 29 it is 5.7e-4 below the Gensane–Ryckelynck value. In other words the
table already carries *post-2009* improvements on those rows (the current register
gives 5.824445 for n = 28, which matches us).

**There is no import target.** And the forward column says something stronger:
even if a construction existed exactly at the published side of any of these rows,
it would pay **0.000000** over that column's suffix — because the table is already
at or below it. So "import a published construction" is not a route to score on
any row checked here, independently of how good the construction is.

## 3. The n = 11 check

n = 11 is the review's priority-2 case: unproved, best known ≈3.8771 (Trump
1979), proved lower bound `2 + 4/√5 = 3.788854` (Stromquist, Thm 2).

| check | result |
| --- | --- |
| delivered vs Trump | 3.877083592 vs 3.8771 → **at**, Δ = −8.5e-9 |
| tilt angles in the row | **49.8181°** (only non-axis angle) |
| Trump's middle squares | "about **40.182°**"; orientation is mod 90°, and 90 − 49.8181 = **40.1819°** |
| 0°/45°-restricted optimum (Stromquist) | `2 + 2√(8/9) = 3.885618` |
| delivered vs that restricted optimum | 3.877084 < 3.885618 ✓ so the row *must* use a non-45° angle |
| unresolved (pub − LB) | 0.088229 in side |

So the delivered n = 11 row **is Trump's construction**, identified two
independent ways: the side agrees to 8.5e-9, and the single non-axis angle is
40.1819°, which is Trump's 40.182° to the fourth decimal. The row also sits below
the 0°/45°-restricted optimum, which is the property Stromquist's paper isolates
(the first case where an optimal packing needs a non-45° angle). The positive
control the review asked for therefore passes — and, because it passes, n = 11 is
a **benchmark, not a target**: nothing published is smaller, and the 0.0882 of
bound gap is exactly the kind of number run 56 warned not to read as room.

The word class of that row is `other` in the `20` sense (not `axis`, not `pi/4`,
and its tangent is not a small rational in the declared table): it is the first
row in the table that the ℚ(√2) alphabet cannot express, which is why the exact
gate cannot certify it and only `packlib`'s float gate can.

## 4. What the rerank now says

The review asked for the best *remaining* start rather than the best bound in
isolation. Three filters have now been applied in sequence, and each removes a
class:

1. **Proved rows are out** — 42/42 at their exact optimum (run 56), including
   n = 10, which was the top of the earlier optimistic ranking.
2. **Importing is out** — 0 of 12 open rows has a published construction smaller
   than the delivered side, and the forward value at the published side is 0.000000
   everywhere (§2).
3. **Bound gaps cannot rank what is left** — after (1) and (2), every remaining
   candidate is a row where a construction *better than the published record*
   would be needed. Its value cannot be estimated from a lower bound (run 56's
   n = 10 lesson), so the ranking has to be by **constructibility**, not by
   bound slack.

That is a real narrowing: the next score gain, if any, requires a construction
strictly below the published record on an open row — not a better arrangement of
one we already have (runs 53–55: every boundary move costs ≥ 0.5 of side), and
not an import (this run). The two routes left are the two the review names:
extend a family to a row the catalogue does not cover, or invent a multi-angle
motif. Neither can be ranked by a bound; both need a wheel with an exact builder.

## 5. What this does not show

* **12 rows, not all open rows.** The crosswalk covers n = 11, 12, 17–20, 26–31 —
  the rows for which DS7 Table 1 and Table 2 both give values and which sit in the
  low-r columns. Rows 37+ and the large-n strips are not checked.
* **Float publishes stay floats.** Where Table 1 gives 4-dp values (n = 11, 17, 29)
  the comparison is at 1e-4, not exact; only the closed forms in ℚ(√2) are exact.
  n = 18's `7/2 + √7/2` is exact but not in ℚ(√2), so it is compared at 1e-9 as a
  float.
* **The forward column is the declared (r, δ) invariant**, not a built packing. It
  says what a base at the published side would pay if the family extended; it does
  not construct the extension.
* **`beats_published` at n = 28 and 29 is a statement about the 2009 survey**, not
  about the current frontier. Both rows already match the current register.

## 6. Files

* `scripts/crosswalk.py` — per-row `PUB`/`LB` tables with formula, value, author
  and figure; three-way status; forward-only suffix value.
* `workspace/push/crosswalk.json` — 12 rows, the tally, the n = 11 angles.
* follows `24-N10-OPTIMAL.md`; completes the crosswalk that document listed as
  the next instrument.
