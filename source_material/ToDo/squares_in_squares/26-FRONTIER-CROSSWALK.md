# 26 — full-range frontier crosswalk (run 58)

> **SUPERSEDED — §1, §2 and §3 below are WRONG and are kept only as the record of
> what run 58 got wrong.** Two defects: (a) §1 states the catalogue rule as "n ≤ 324
> unpictured → trivial `ceil(√n)`", but the catalogue's rule is *the closest packing
> shown to the right of n*; (b) §2 and §3 report a 287-row coverage and a 56-row
> `beats` count from that wrong rule. The corrected rule and the validity
> evidence are in **§8**; the strictly correct coverage is in **§9** — 325 rows exact, 675
> not resolvable from this source, 0 targets. §4–§8.5 stand except where §9 amends them.

Instrument `scripts/frontier.py`, ledger `workspace/push/frontier.json`.
Read-only: no row changed, no score moved.

Replaces run 57's 12-row sample with a crosswalk attempted over **all 1000 rows**. The coverage actually
achievable is **325 rows** — see §9, which is the current statement.

## 1. Sources, and the coverage map — **SUPERSEDED, wrong rule (§8.1)**

The catalogue states its own completeness boundary, which is what makes a
full-range crosswalk possible at all:

> **Kingbird catalogue** (Ellsworth's high-precision revision of Friedman's
> gallery): "For the n ≤ 324 not pictured, the trivial packing (with no tilted
> squares) is the best known packing."

So for n ≤ 324 the record is *complete*: pictured rows take the pictured value,
every other row takes the trivial side `ceil(√n)`. Above 324 the catalogue only
pictures record-setting packings, and it only pictures **n = 626** inside
324 < n ≤ 1000 — which tells us nothing rigorous about the rest, so nothing is
claimed there.

| basis | rows | what it means |
| --- | ---: | --- |
| `catalogue_2026` | 146 | pictured value, current catalogue |
| `trivial_rule` | 135 | n ≤ 324 unpictured → best known = `ceil(√n)` |
| `ds7_2009` | 6 | 2026 value not extracted; 2009 value used (an upper bound on the current record) |
| `pictured_value_not_extracted` | 38 | pictured, but the value sat after a truncation on the page |
| `unresolved_above_324` | 675 | n > 324, unpictured: the completeness statement does not reach here |

**Resolved: 287 rows. Unresolved: 713 (675 by the source's boundary, 38 by the
fetch).** That coverage split is the honest headline of this run.

## 2. The answer to the question asked — **SUPERSEDED, wrong counts (§8.2)**

    resolved rows: 287       at = 231      beats = 56      ABOVE = 0

**There are no import targets.** On every row where the record is complete, the
delivered side is at or below the best known construction — there is no row where
a catalogued packing is strictly better than what the table already has. This
extends run 57's 12-row result to 287 rows and confirms it.

Sample at the current records (all `at`, deltas are the finalizer pad):

| n | delivered | catalogue | status |
| ---: | ---: | ---: | --- |
| 50 | 7.571428573 | `7 + 4/7` = 7.571428571 | at |
| 55 | 7.945771009 | 7.945771008 | at |
| 71 | 8.944071559 | 8.944071558 | at |
| 83 | 9.634757650 | 9.634757649 | at |
| 87 | 9.838815272 | 9.838815270 | at |
| 205 | 14.824451148 | 14.824451146 | at |
| 626 | 25.520815282 | `13.5 + 8.5√2` = 25.520815280 | at |

Seven records from 2025–26 — including Schadt's rational `7+4/7` at n = 50 and
the 672-degree Hajba/Chang record at n = 83 — are already in the table.

## 3. The 56 `beats` rows — **PARTLY SUPERSEDED (§8.3): 80 under the correct rule**

On 56 resolved rows the delivered side is strictly **below** the extracted
catalogue value, sometimes substantially:

| n | delivered | catalogue | margin |
| ---: | ---: | ---: | ---: |
| 51 | 7.690355939 | 7.700799235 | −1.04e-2 |
| 102 | 10.605828698 | 10.611387941 | −5.56e-3 |
| 105 | 10.789303786 | 10.807619333 | −1.83e-2 |
| 123 | 11.591378147 | 11.601399794 | −1.00e-2 |
| 126 | 11.742640689 | 11.774735132 | −3.21e-2 |
| 303 | 17.901811279 | 17.931255096 | −2.94e-2 |
| 183 | 13.999580181 | 14 (`trivial_rule`) | −4.20e-4 |

The tempting reading is that the table holds 56 published-record improvements.
**I do not make that claim**, for two reasons that are both mechanical:

1. the label→value mapping was extracted from a page the fetch **truncated inside
   several entries**, so an offset error would shift values between neighbouring
   rows and manufacture exactly this pattern;
2. the margins at n = 51…306 are far larger than the ~1e-2 separations that
   record-setting constructions usually have, which is the signature of a
   mismatched comparison rather than of 30 world records.

What can be said without that risk: on all 287 resolved rows the delivered side is
**at or below** the extracted value. Whether 56 of them are genuinely below the
current record is a question for the machine-readable table, not for this page.

## 4. Why this run cannot resolve the remaining 713 — **SUPERSEDED by §9**

The catalogue's completeness statement covers n ≤ 324 only. For 325 ≤ n ≤ 1000 it
pictures exactly one packing (n = 626), so "no picture" there is not evidence of
anything — unlike the n ≤ 324 case, where it is a stated fact. The 38 pictured
rows whose values were truncated are a fetch problem, not a source problem.

The fix is the catalogue's **triangular table view** (linked from the same page),
which presents n and s compactly, plus `parse_svg_packing.py` for exact
coordinates. That is the first action of the next run, and it would close all 713
rows without new mathematics.

## 5. What the ranking now says

With 0 import targets over 287 resolved rows, and run 57's 12-row sample agreeing,
the reviewed decision holds and can be stated as a result rather than a
hypothesis:

* **importing is closed** as a route to score, on every row where the record is
  complete — regardless of how large the published bound gap is, because the
  table already sits at or below the best known construction;
* **a new score requires a construction below the published record** on some open
  row, which cannot be selected by bound slack (run 56) or by import gap (this
  run);
* the only remaining ranking signal is **constructibility** — which family can be
  built exactly and extended over a residue column — and that is a grammar
  question, not a crosswalk question.

Two rows deserve a note on that last point: n = 183 and n = 655 sit *just* below
the grid (13.999580181 vs 14, 25.999711088 vs 26) on rows the catalogue does not
picture. They are the kind of near-grid, thin-margin rows where a small structural
gain propagates cheaply, and 655 is in the unresolved band.

## 6. What this does not show — **SUPERSEDED in substance by §9**

* **713 of 1000 rows unresolved**, by the reasons in §4. This is not a full-range
  crosswalk in the strict sense; it is a complete one over 287 rows plus a
  catalogue-wide search for record-setting packings above 324.
* **The 56 `beats` are unconfirmed** (§3) and must not be read as records.
* Catalogue values are **nominations**, as in every run since 53. Nothing here
  enters `submission.csv`; no construction was built.
* No claim about proved optimality beyond run 56's 42 rows.

## 7. Files

* `scripts/frontier.py` — `PICT` (pictured values, catalogue decimals),
  `WEAK` (2009 fallbacks and truncated rows), `best_known` (with basis),
  `fwd_gain` (forward-only suffix value), three-way status plus `unresolved`.
* `workspace/push/frontier.json` — 1000 rows with basis, status and deltas.
* follows `25-OPEN-ROW-CROSSWALK.md`; supersedes its 12-row coverage.

---

# §8 — Correction (run 59): the rule was wrong, the mapping was not

Follow-up after fetching the catalogue's **Triangular Table View**, which states
its rule outright and attaches every value to its own row number:

> "For the n not shown, the closest packing shown to the right of it is the best
> known packing (to have the appropriate number of arbitrarily chosen squares
> removed)."

## 8.1 What run 58 got wrong

§1 used *"n ≤ 324 unpictured → trivial `ceil(√n)`"*. That is not the catalogue's
rule. The catalogue's best known for an unpictured row is the value of the
**next shown row to its right** — i.e. a bigger packing with squares removed —
which is `≤` the trivial side. So run 58 **understated** `best_known` on ~100 rows.

That error can only hide an import target, never invent one: a *smaller*
`best_known` makes the delivered side look better, not worse. The zero-target
result therefore survives the correction — and is now measured against a value
that is `≥` the true one, i.e. against the weakest standard the catalogue allows.

## 8.2 The label-mapping worry is resolved

§3 suspected the 56 `beats` were an offset artifact of a truncated fetch. The
triangular table removes that doubt: each value is written against its own `n`
(`51. … $s = 7.70079923541701$`), inline, with no separate label list to misalign.
Re-checking against those per-row values:

| | rows |
|---|---:|
| resolved (n ≤ 324) | **316** — at 236, beats 80, **above 0** |
| blocked: left of a truncated anchor | 9 |
| outside the extracted band (n > 324) | 675 |

**Still zero import targets, now over 316 rows** instead of 287, under the correct
rule and unambiguous values.

## 8.3 But `beats` ≠ records, for a different reason

80 rows sit below the catalogue's `best_known`. Most are rows **left of an anchor**
(n = 84 anchored at 90, n = 143 anchored at 148, …): there the catalogue's value is
inherited from a larger packing, so it is a loose upper bound and the comparison
says nothing about records.

Only **same-n** comparisons are meaningful, and there are **61** of them — e.g.
n = 51 (7.690355939 vs 7.700799235), n = 126 (11.742640689 vs 11.774735132),
n = 303 (17.901811279 vs 17.931255096). Those are the rows worth a human look; the
delivered packing is genuinely narrower than the catalogue's value for the same n.

## 8.4 Are those packings real? Yes — and my first check of that was broken

The "45 below the record" reading was implausible enough to test. Two checks:

* **Square counts**: every one of the 1000 rows contains exactly `n` squares
  (`len(per[n]) == n` for all n; 0 exceptions). `packlib.score_detail` skips
  mismatched rows anyway, so the score never rested on a short row.
* **Validity**: `packlib.verify` on 51 sampled rows, including every large-margin
  one — all `ok: True`, `worst_pen` between −1.3e-10 and −2.6e-10, `w == h == L`.
  These are valid packings of exactly `n` unit squares in a square of side `L`.

**Retraction**: this run also contained an ad-hoc float verifier that reported
penetrations of `+2.9e-1` on rows that match the catalogue to 2e-9. It was wrong —
it misused `seam_wheels.EXT`/`AXES_OF` as if `EXT` were indexed by axis label. Its
numbers are void and are not used anywhere. `packlib.verify` is the check that
counts, and it is the project's own documented SAT validator.

So: the 61 same-n rows are not a mapping artifact and not invalid geometry. Whether
they are *record claims* is a decision for the owner, not something this record
asserts — an unpublished table being below a published value is a fact about the
two tables, not a claim that the catalogue is wrong.

## 8.5 What is still not covered

675 rows above n = 324 and 9 rows left of a truncated anchor. The triangular page
continues past 324, but the fetch truncated at n = 324 both times. Resolving the
rest needs the page fetched in chunks (or the per-row `.svg` metadata), not new
mathematics.

---

# §9 — Corrected coverage (run 61): 325 rows exact, 675 not resolvable here

> Supersedes the "1000/1000 resolved" claim this file briefly carried, and the
> tallies in §8.2 / §8.5. The §1–§3 markers at the top still apply.

## 9.1 The page, and its scope

Fetched with `curl` (the in-app reader truncates near n = 324 at 50 k characters):
230,852 bytes, complete file, **215 entry cells**, and **zero** `square-<n>.svg`
links above n = 324. So the triangular table covers n ≤ 324 only — precisely the
band the catalogue's completeness statement governs. `scripts/parse_tt.py` parses
it into `workspace/push/tt.json` (0 unparseable values, 0 cells with an ambiguous
double value).

## 9.2 What is exact

For n ≤ 324: `best_known(n) = min(trivial(n), value at the nearest shown n' ≥ n)` —
the minimum over every construction the catalogue lists for that row, i.e. the
strictest admissible reading. It can only make the delivered side look worse, so
it can only *add* targets.

| | rows |
|---|---:|
| **resolved (n ≤ 324)** | **325** |
| at | 246 |
| beats | 79 |
| **above (import targets)** | **0** |

Basis: `catalogue_2026 146, no_source_above_324 675, triangular_table 74, trivial_rule 105`.

Of the 79 beats, **79** are same-n comparisons against a value the
catalogue attaches to that row, and **0** are inherited from a larger
shown row. Largest same-n margin: -0.032094.

The nine rows whose own values the earlier fetch delivered as "..." are now exact:

| n | catalogue | delivered | status |
|---:|---:|---:|---|
| 146 | 12.600907779 | 12.583782192 | beats |
| 154 | 12.931667130 | 12.921100943 | beats |
| 171 | 13.571428571 | 13.571428573 | at |
| 180 | 13.935087053 | 13.916993524 | beats |
| 228 | 15.609022821 | 15.604601478 | beats |
| 235 | 15.826605633 | 15.826605635 | at |
| 291 | 17.535533906 | 17.535533908 | at |
| 292 | 17.602571412 | 17.591378147 | beats |
| 293 | 17.634146341 | 17.623065214 | beats |

## 9.3 Why the 675 rows above 324 cannot be resolved — and why the trivial grid is not a stand-in

A draft of this section assigned the trivial grid to every unpictured n > 324 and
reported 1000/1000. That is wrong, and the catalogue's own numbers refute it:

* within its scope the catalogue carries the **s(k²+1) family at a constant
  offset**: 145 = 12²+1 → 12.5355339, 170 = 13²+1 → 13.5355339, 197 = 14²+1 →
  14.5355339, 226 = 15²+1 → 15.5355339, 290 = 17²+1 → 17.5355339;
* nothing in the source marks k = 17 as the end of the family; applied at
  325 = 18²+1 it gives 18.5355, where the trivial grid gives 19;
* so "trivial" is provably not the catalogue's best known above 324. The catalogue
  makes no completeness claim there and pictures only selected records — our parse
  finds exactly one in 325..1000 (n = 626).

The giveaway was a margin: n = 677 = 26²+1 comes out 0.479 below the trivial 27,
which is an ordinary member of that family, not a record. Using the trivial grid as
the record would have labelled 402 such rows "improvements on the record".

Assigning a value there converts 675 open rows into confident-looking comparisons
in the one direction that hides targets. They stay open:
`basis = no_source_above_324`, `best_known = null`.

## 9.4 What this means for the reviewed question

On every row the source determines — **325** of them — there is no import target:
the delivered side is at or below the best known construction. Two hundred of
those rows are the ones the catalogue's completeness statement actually covers
outright, and the rest are inherited from it. Above 324 the question is *open, not
answered*: settling it needs a source with above-324 coverage (a maintained flat
grid, or the record list behind the five known records), which this catalogue does
not provide. No amount of re-reading this page will produce it.

## 9.5 Reproduce

    curl -sS -o workspace/raw/triangular_table.html \
      https://kingbird.myphotos.cc/packing/squares_in_squares__triangular_table.html
    python3 scripts/parse_tt.py     # -> workspace/push/tt.json (215 rows)
    python3 scripts/frontier.py     # -> workspace/push/frontier.json (1000 rows)
