# 17 — The combinatorial address: tilt pattern + contact graph

**Run 47, 2026-11-18.** Instrument `scripts/leech_comb.py`; ledger
`workspace/push/leech_comb.json`. Read-only.

`16-LEECH-MAP.md` closed the metric address: the Λ₂₄ legality predicate is an
integrality condition, and over 255 rows every tilted packing was illegal at every
scale while every untilted one was legal somewhere. The one bit the design can see
is the tilt bit; the graph is the rest. This run builds that address, tests it,
and reports an honest negative with three useful byproducts.

---

## 1. Review of `leech_map.py`, and what was cut

Read with fresh eyes, the file had five pieces of dead weight. None changed a
number, which is why the cleanup was safe — the rerun reproduces the run-45
results exactly (196 560/196 560 accepted, crosstab 0/87/168/0, round-trip bound
1.92e-03).

| cut | why |
| --- | --- |
| `import numpy as np` | nothing used it after the gap-vector rewrite |
| `store.get(n) if hasattr(store, "get") else store[n]` | `read_csv` always returns a dict; one branch was unreachable |
| `snap_distance` and its column | a **second** Golay predicate duplicating `in_leech24`; the Hamming distance was 0 for every legal row and 3–4 for every illegal one, i.e. no information the predicate did not already carry |
| `minimal_vectors` as a list of 196 560 vectors | streamed as a generator; the validator only counts and tests |
| `GEN_TOL`, `e = [0]*24`, the `(st, L, L0)` third field | unused |

One real bug fixed: `--validate` alone used to **overwrite** the ledger and wipe
the probe section (hit during run 45). The ledger is now merged, and the
`--validate`-only run is verified to keep `probe` intact.

## 2. The address

For a packing of n unit squares:

```
tilt_i ∈ {0,1}        one bit per square
G                     nodes = squares; edge iff the pair has a SEGMENT contact
address = ( WL-signature( G coloured by tilt ), |E(G)| )
```

Three design decisions, each defended by a test:

* **Segment contact, not point contact.** `packlib.verify` on a pair reports
  penetration 0 for a *corner* touch, so a naive reading makes the 2×2 grid
  complete (K₄). A corner contact carries no rigidity constraint, so the edge
  rule is: touching on one axis (`|min pen| ≤ tol`) *and* strictly overlapping on
  the other (`max pen > tol`). Validated: the 2×2 grid is now a 4-cycle (4 edges,
  all degrees 2), the 3×3 grid has 12 edges with degrees 4×2, 4×3, 1×4 — the
  grid graph, as it must be.
* **The pair view agrees with the gate.** `axis_penetrations` exposes the four
  SAT values the gate minimises; a test checks `min(...) == verify(pair)["worst_pen"]`
  on 200 random pairs (to 1e-12), so it is a refinement of the gate, not a second
  implementation of it.
* **Canonical under symmetry.** The address is invariant under relabelling the
  squares (checked) and under the 8 symmetries of the bounding box (checked), and
  it is discrete — no scale parameter, unlike every metric attempt.

## 3. Selftest — 7/7

| check | result |
| --- | --- |
| address invariant under relabelling | ok |
| canonical form invariant under D₄ | ok |
| pair axes equal the gate's penetration | ok (200 pairs, 1e-12) |
| 2×2 grid is a 4-cycle | ok |
| 3×3 grid degrees / 12 edges | ok |
| different shapes get different addresses | ok |
| n = 5 delivered row | tilt bits (1,0,0,0,0), degrees (4,1,1,1,1), 4 edges |

That last row is a clean structural statement: **s(5) = 2 + √2/2 is a star
K₁,₄** — the 45° diamond in face contact with all four corner squares — and it
carries exactly one tilt bit. The Göbel optimum has a name in this language.

**Stability** (the property the metric address lacked): a 1e-7 perturbation left
the address unchanged in **50/50** trials at n = 5 and **9/9** on the ensemble
sample.

## 4. Does it predict slack, conditional on n and r?

Conditioning on n subsumes r (`r = n − (k−1)²` with `k = ⌈√n⌉`), and in the
delivered table there is exactly one row per n, so **conditional on n there is no
variance left to explain**. The test therefore needs an ensemble; two generators
were used — sub-packings (delete one square from a bigger delivered row, which
stays in the tight regime) and random sequential placement in a loose box —
88 packings at n = 5..10, scored with `sqscore.row_score`.

| statistic | observed | permutation null | verdict |
| --- | ---: | --- | --- |
| R² address, baseline n | **+0.978** | mean 0.500, max 0.701, 0/300 ≥ | significant |
| R² tilt only | +0.662 | — | |
| R² edge count only | +0.920 | — | |
| R² multi-member classes only | +0.965 | mean 0.337, max 0.542, 0/300 ≥ | significant |
| **R² stratified on (n, source)** | **+0.728** | mean 0.535, max **0.758**, 12/300 ≥ | **not significant** |

The stratified line is the one that matters, and it kills the result. Sub-packings
of one delivered row share that row's side length, so part of the unstratified R²
is the *source*, not the address. Once the source is controlled, the address does
not beat the null (12/300 ≈ 0.04, and three statistics were examined).

**The address does not determine the side length either.** Within a single
address class the L spread is mean **0.071**, max **0.420** — two packings with
the same tilt pattern and the same WL signature of the same contact graph can
differ in side by 0.42, which is ~0.15 of score at n = 8.

## 5. Verdict

The combinatorial address is **real, exact, discrete and stable** — everything the
metric address was not — and it is **not a predictor of slack**. Its information
is redundancy: the contact graph is mostly determined by the density that also
determines L, and the residual information (which graph, at which n) is not
worth a score.

What it does buy, and should be kept:

1. **A canonical, scale-free descriptor** for any packing (`address`,
   `canonical_set`, `tilt_bits`, `contacts`, `degree_sequence`), invariant under
   relabelling and D₄, stable to 1e-7. That is a legitimate GLM module for
   comparing, deduplicating and classifying packings.
2. **A correct contact graph** — segment contacts, validated against both grids
   and against the gate. The project did not have this before, and it is the
   input any rigidity argument needs.
3. **A structural name for the controls**: s(5) is K₁,₄ plus one tilt.

And it points at what looked predictive: L fixed not by the contact *graph* but by
the **rigid** contact structure — the Maxwell/Laman count of the contact graph
(2n − 3 independent constraints; corner contacts contribute nothing), i.e. the
packing's **rigidity class**, not its isomorphism class. That hypothesis was
stated here and **tested in run 48 (`18-RIGIDITY.md`): it is false.** The 0.42
spread is carried entirely by address classes with |E| = 0, i.e. packings whose
squares never touch, where no graph statistic can apply; where contacts do exist
the Laman class collapses to `(2n − 3 − |E|, 0)` because no packing in the
ensemble has a redundant contact. The grids also show the object was
mis-specified: a 2×2 grid's contact graph is a 4-cycle — a mechanism — and only
the container pins it.

## 6. Limits

* 88 packings, n ≤ 10, two generators; RSA rows are loose (slack 0.3–0.5).
* WL is not a complete isomorphism invariant; two packings with the same address
  may have different graphs, which only makes the negative stronger, not weaker.
* The stratified null is borderline (0.04); the honest reading is "indistinguishable
  from noise", not "proven zero".
* No score claimed, no row changed, nothing committed.

## 7. Files

* `scripts/leech_comb.py` — address, canonical form, contacts, statistics,
  selftest, ensemble and report. `python3 scripts/leech_comb.py [--quick] [--draws N]`.
* `scripts/leech_map.py` — cleaned metric codec (run 46); same numbers as run 45.
* `workspace/push/leech_comb.json`, `workspace/push/leech_map.json` — ledgers.
