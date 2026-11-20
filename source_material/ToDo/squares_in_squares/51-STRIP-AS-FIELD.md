# Run 88 — the strip as a field, and cells from run parameters

Two items were left in doc 50's "does not claim" list: `strip_needs_diamond` still firing
for `S(k,0)`, and n = 19 / n = 40 declaring their axis cells as literal lists. Both are
now closed, and closing them turned out to be the same job: once a field's carrier is a
*product of two 1-D skeletons*, a strip is a field too, and an atom's cell set stops
being data.

Nothing in the table moved. `submission.csv` and the root whiteboard are untouched.

## 1. The strip is a field of (k, m)

The old `p_strip(k, m)` refused at `m = 0` with

```
strip_needs_diamond: S(k, 0) has no diamond, so it is the plain 2k grid: no seam
```

That refusal was honest but it described a *missing implementation*, not a mathematical
dead end. The strip is a declared field:

```python
strip_field(k, m):
    seam = m * sqrt2 / 2
    X = {1/2, ..., k - 1/2}  u  {1/2 + k + seam, ..., 2k - 1/2 + seam}      (same for Y)
    slots[i] = (k + (2i+1) sqrt2/4, k + (2(m-1-i)+1) sqrt2/4),  i = 0..m-1
```

i.e. four k-blocks separated by a seam of width `m√2/2`, with the m diamonds sitting on
the anti-diagonal inside that seam. Both halves are arithmetic in `i`, so the whole
declaration is *generated from (k, m)* — no rows, no literals.

At `m = 0` the seam has width 0, the slot list is empty, the carrier is exactly the
`2k × 2k` axis grid, and the insertion rule has nothing to drop. The claim certifies:

| cell | N | L | gain | verdict |
|---|---|---|---|---|
| `S(2,0)` | 16 | 4 | 0 | certified |
| `S(3,0)` | 36 | 6 | 0 | certified |
| `S(4,0)` | 64 | 8 | 0 | certified |

**The spatial wheel is now 31/31 certified, 0 refused.** The last three refusals of the
packing domain are gone — not by deleting them, but by implementing the thing they said
was missing.

Two guards make that safe rather than convenient:

- **control 19** asserts `S(k,0)` is *identical* to `p_grid(2k)` — same N, same L, same
  cell set, gain 0 — for k = 1..4, so the new certificate cannot drift away from the
  object it claims to be; and asserts `S(k,m)` reproduces the run-84 sentence for
  m ∈ {1,2,3} at three k (same state set, same L, N = 4k² + m).
- **control 5** had to change, and the change is a finding, not a loosening. It used to
  assert "the wheel must have at least one refused cell". It now asserts the opposite —
  no spatial cell refuses — and then exercises *every* refusal law on a constructed
  cell (`degenerate_cell`, `negative_seam`, `unknown_field`, `no_diamond`,
  `declaration_overlaps`), plus checks that the other two wheels still refuse by law
  (`not_sturmian`, `empty_shell`, `rank_budget`). The refusal mechanism is tested harder
  than before; it is no longer tested through a cell that exists only to fail.

## 2. Cells from run parameters

Run 87 declared n19's 11 and n40's 24 axis cells as explicit lists, with the honest note
that "their axis sets are not product grids". That note was wrong, and the product test
says so. Given each field's slot list, both carriers are exactly a product minus the
cells the slots collide with:

| field | X skeleton | Y skeleton | carrier | dropped | cells |
|---|---|---|---|---|---|
| n10 | `{1/2,3/2} ∪ {3/2+√2/2, 5/2+√2/2}` | same | 16 | 8 | 8 |
| n19 | `{1/2,3/2} ∪ {1/2+a,3/2+a,5/2+a}` | `{1/2,3/2,5/2} ∪ {3/2+a,5/2+a}` | 25 | 14 | 11 |
| n40 | `{1/2,3/2,5/2} ∪ {3/2+2√2,5/2+2√2,7/2+2√2}` | same | 36 | 12 | 24 |

with `a = 4/3√2`. The algebra is one type:

```python
_skeleton(runs)        # union of arithmetic runs (start, step, count), exact Q(sqrt2)
_product_cells(X, Y)   # the carrier
```

A run has three parameters, so a field is now two short run lists plus its slots. n10's
run-87 "bent grid" is the two-run case; the seam families are the union case. The
insertion rule is unchanged and still does all the deriving — L, void, gain, contacts,
and the `declaration_overlaps` refusal.

**The counts changed, in the honest direction.** n19's dropped cell count was 0 in run 87
because its carrier was a pre-trimmed 11-cell list; it is 14 now, because the carrier is
the full 25-cell product and the rule does the trimming. n40: 0 → 12. n10: 8 → 8. The
atoms' N, L, void and contacts are *identical* to run 87 — control 18 compares the
generated cell sets against the run-87 census cell by cell (8/11/24 cells), and the
induction acceptance test still reports 10/10, 19/19, 40/40 exact with
`identical_to_atom` and `L_matches_atom` true in all three cases.

Control 18 also refuses to pass if a declared field ever needs more than two runs per
axis — the compactness assumption is itself checked, so a future field that quietly
degenerates back into a list is caught.

## 3. Verification

| check | result |
|---|---|
| `glm_wheels --selftest` | **19/19** (was 17) |
| `glm_wheels` spin | spatial **31/31**, sequences 6/7, lattice 24/28 |
| `glm_wheels --audit` | **177 functions, 0 offenders** (was 174) |
| `grammar_induction --selftest` | 3/3, acceptance exact on n = 10, 19, 40 |
| `qsqrt2 --selftest` | 11/11 (cage unchanged) |
| `field_triage --selftest` | 4/4 |
| `record_guard.py` | OK |

## 4. What this run does not claim

- **`S(k,0)`'s certificate is a tautology, deliberately.** It says the empty-seam field
  is the grid and that the grid buys nothing (gain 0). It is worth having because it
  closes the family rather than special-casing it, and because control 19 pins it to
  `p_grid(2k)`; it is not a new packing.
- **The seam's diamonds never touch an axis cell.** For m ≥ 1 the strip's slots collide
  with nothing (verified: carrier 16/36/64 = axis count, dropped 0), so the strip's
  insertion rule is vacuous — the seam is empty space by construction. That is why the
  m = 0 case degenerates cleanly, and it also means the strip exercises the *carrier*
  algebra rather than the collision rule. The three atoms exercise the collision rule.
- **Pocket is still `S(k,1)` from run 84's builder**, not from `strip_field`; the two
  agree on the state set for every k tested (control 19 covers k = 2, 3, 4), but the
  pocket's own path was left alone rather than rewritten without need.
- **177 functions audited, still 0 naming float.** The new code is `Q(sqrt2)` and
  `Fraction` throughout; `_skeleton` multiplies by `Q2(i)` so even the index is exact.

Entries `51-STRIP-AS-FIELD.md`; records `31`–`51`.
