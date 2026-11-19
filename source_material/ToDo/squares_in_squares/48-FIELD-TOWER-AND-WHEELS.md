# 48 — The field tower, the wheel engine, and two domains (Run 85)

Instruments `scripts/exact_field.py` (7 controls), `scripts/glm_wheels.py`
(12 controls), `scripts/qsqrt2.py` (10, unchanged), `scripts/mixed_field.py`
(14, unchanged) — **43 controls**. Ledgers
`workspace/push/glm_wheels.json`, `workspace/push/q_census.json`,
`workspace/push/outlier_probe.json`. Read-only: **no row changed**, no score
claimed, `submission.csv` untouched.

**What this run is.** Run 84 left three things domain-specific that should not be:
the ring logic lived inside ℚ(√2), the declared-law wheel pattern lived inside
packing (`motif_wheels.py`), and the reconstruction's fallback was a per-coordinate
height search. This run extracts the first two and replaces the third, then uses
them: a second domain that is not geometry, and a census of the table that is
finally complete.

| piece | deliverable | status |
|---|---|---|
| 1 | `exact_field.py` — Z, Q, Q(√d), rational t-points, exact order/floor/ceil, bytecode audit | **done**, 49 functions audited |
| 2 | `glm_wheels.py` — alphabet/syntax/witness engine, four-witness verification | **done**, two domains |
| 3 | spatial + Sturmian coverage, 447-row census, outlier probe, 2D cage | **done**, one row open (n = 126) |

---

## 1. The tower

`exact_field` holds four scalar kinds and nothing about squares:

| rung | type | exact decisions |
|---|---|---|
| Z | `Z` (integral subclass of Q; arithmetic returns Q) | sign, order, floor, ceil |
| Q | `Q` (a `Fraction` with `sign`, `floor`, `ceil`) | all of them |
| Q(√d) | `Quad`, `d` square-free, one subclass per field (`class Q2(Quad): d = 2`) | sign, order, floor, ceil |
| t-basis | `tword(p, q)` on the unit circle, `t = tan(θ/2) = p/q` | exact, `cos² + sin² = 1` |

Every decision is derived from `sign()` through one mixin, so no field can
disagree with itself about ordering: comparisons are the sign of a difference,
`floor` is a bisection on sign tests inside an exact bracket
`a − |b|(⌊√d⌋+1) − 1 ≤ z ≤ a + |b|(⌊√d⌋+1) + 1`, and `ceil = −floor(−z)`. The
sign rule is the same case analysis for every `d`: same-sign coefficients are
immediate, and the mixed cases compare `a²` with `d b²`, which has no nonzero
rational solution because `d` is square-free — so no case is a tie.

**Controls.** 1,400 signs across `d = 2, 3, 5, 6, 7, 10, 13` agree with 70-digit
`Decimal`; 600 floors satisfy `k ≤ z < k+1` exactly; every nonzero element inverts
in its own field; `Q8` is refused (not square-free); six t-points lie on the circle
exactly, with `t = 1/2, 3/4` giving the 3-4-5 and 7-24-25 triples; and
`recover_scalar` returns `7/2 − 3/4√3` from its 12-dp decimal in ℚ(√3) while
refusing a non-lattice value.

**The audit is the deliverable, not a claim.** `no_float_calls` walks **code
objects** — not source, so docstrings cannot fake a pass — and `audit_module`
reports counts. It is self-tested with a planted `float(z) > 0` (caught) and
exempts exactly three things, each named in `DISPLAY_ONLY`/`TEST_ONLY`/`WITNESS_ONLY`:
`__float__`/`decimal` (display), `selftest` (it plants the offender), and
`float_state` (it feeds `packlib`'s float verifier as an independent witness).
Current audit of the run-85 instruments:

    exact_field   49 decision functions, 0 naming float
    qsqrt2        20 decision functions, 0 naming float
    glm_wheels    76 decision functions, 0 naming float
    total        145, 0 offenders

**`qsqrt2` now sits on the tower.** `Q2` is `Quad` with `d = 2`; the sign, order,
arithmetic, float refusal and `floor` all moved out, and `floor_q2` is a one-line
delegation. The API is unchanged, which is checkable: all 10 `qsqrt2` controls and
all 14 `mixed_field` controls still pass, and every sampled lift verdict is
identical (`n = 5, 19, 126, 295, 362, 974` reproduce their recorded status, side,
contacts and recovery counts).

## 2. The engine

A **domain** registers an `Alphabet` (atomic words with exact measure and
extent), a registry of `Syntax` combinators, and its `Witness` suite. A
**combinator** returns a `Claim` — the built sentence, its closed-form laws, and
its payload. A **wheel** is a declared parameter grid of cells; `Wheel.spin` can
only enumerate, take a `Refusal` with a named law, run every witness, and record
the verdict. `Engine` holds domains and wheels and contains no geometry.

The five combinator slots are filled by both domains:

| slot | spatial geometry | Sturmian sequences |
|---|---|---|
| `Tile` | k×k grid | mechanical word of slope α |
| `Pocket` | four k-blocks + one 45° diamond | — (not in the sequence alphabet) |
| `Strip` | S(k, m): four k-blocks + m-diamond strip | a window of the same orbit |
| `Glue` | rational-t corner glue (five squares) | two consecutive windows joined |
| `SymmetryFold` | diagonal reflection | reversal of the word |

### 2.1 Multi-witness verification

A claim is certified only if **all four** witnesses pass, and each one is a
different kind of evidence:

| witness | spatial geometry | Sturmian sequences |
|---|---|---|
| `exact_gate` | the SAT gate, clearance exactly 0 | the mechanical-word realisation |
| `topology` | contact graph: spanning, min degree ≥ 1 | factor complexity `p(m) = m + 1` |
| `conservation` | `N + V = L²` and `L² ≥ N`, exactly | weight sum and the coboundary law |
| `decimal_cross` | 70-digit `Decimal` bbox and per-pair verdicts | 70-digit weight sum |

The Decimal witness is not decoration: it recomputes the *side* and, pair by pair,
the gate's own decision, and requires `dec_ok == exact_ok` and `|L_dec − L| ≤ 1e-40`.
Control 10 shows it accepts the exact side of the corner pocket and **rejects a
claim whose side is off by 1e-9**.

### 2.2 The spin

Spatial wheel, 28 declared cells: **25 certified, 3 refused** — the refusals are
`Strip(k, 0)` for k = 2, 3, 4, refused by `strip_needs_diamond` ("no diamond, so it
is the plain 2k grid: no seam"). Sample of the laws:

| family | cell | N | L exact | gain vs grid | verdict |
|---|---|---|---|---|---|
| Tile | k=3 | 9 | 3 | 0 | certified |
| Pocket | k=1 | 5 | `2 + 1/2√2` | `1 − 1/2√2` = 0.292893 | certified |
| Pocket | k=3 | 37 | `6 + 1/2√2` | `1 − 1/2√2` | certified |
| Strip | k=2, m=2 | 18 | `4 + √2` | `1 − √2` = −0.414214 | certified |
| Strip | k=3, m=1 | 37 | `6 + 1/2√2` | `1 − 1/2√2` | certified |
| Glue | t=1/2 | 5 | `19/7` | 2/7 | certified |
| Glue | t=1/5 | 5 | `47/17` | 4/17 | certified |
| SymmetryFold | k=2 | 17 | `4 + 1/2√2` | `1 − 1/2√2` | certified |
| Atom | n=5 | 5 | `2 + 1/2√2` | `1 − 1/2√2` | certified |
| Atom | n=10 | 10 | `3 + 1/2√2` | `1 − 1/2√2` | certified |
| Atom | n=40 | 40 | `4 + 2√2` | `3 − 2√2` = 0.171573 | certified |

The `Atom` family is the honest half of "generalising n = 5, 10, 40": those three
delivered sentences are lifted exactly and certified with all four witnesses, but
**n = 10 and n = 40 are not instances of the closed-form families** — n = 10 is
8 axis squares plus 2 diamonds at `3 + 1/2√2`, n = 40 carries 16 tilted squares at
`4 + 2√2`, and neither is `4k² + m`. They are registered as atoms with measured
law bundles, and a closed-form ladder covering them is named as deferred work
(§6) rather than invented. n = 5 *is* the closed form: `Pocket(1) = Strip(1,1)`.

Sequence wheel, 7 cells: **6 certified, 1 refused**. The refusal is the point:
slope `1/2` is refused by `not_sturmian` with its numbers — `p(2) = 2 ≠ 3` — because
a rational slope's word is periodic, and periodicity is exactly the failure of
`p(m) = m + 1`. The certified cells use slope `√2 − 1` (irrational, so genuinely
Sturmian) and carry `√2` in their weight laws:

| family | cell | letters | ones | law |
|---|---|---|---|---|
| Tile | α = √2−1 | 21 | 8 | weight `18 − 5√2` |
| Frame | α = √2−1, ρ = 1/2 | 21 | 9 | weight `15 − 3√2` |
| Frame | α = √2−1, ρ = 1/3 | 21 | 9 | weight `15 − 3√2` |
| Strip | α = √2−1, shift 3 | 21 | 8 | same orbit, same weight |
| Glue | α = √2−1, ρ = 1/2 | 21 | 9 | `∂(uv) = ∂u ⊕ (u₋₁ ⊕ v₀) ⊕ ∂v` |
| SymmetryFold | α = √2−1 | 21 | 8 | reversal law, weight preserved |

The coboundary law needed fixing during the run, and the fix is a result: the
naive identity `∂(uv) = ∂u ⊕ ∂v` is **false**, and the correct law carries the
seam term `u₋₁ ⊕ v₀`. A witness that "passes" a false law is worse than no witness.

## 3. Cross-domain generality, stated precisely

The engine's `spin` never mentions squares, angles, or letters; it calls
`domain.build`, catches `Refusal`, and runs witnesses polymorphically. The proof
is that a second domain was registered **without touching the engine** and produced
certified claims with laws in the same exact field — including a refusal that is a
theorem (periodic ⟹ not Sturmian) rather than a failed search. Two domains, one
pipeline, 14 combinator slots, 35 cells, 31 certified.

## 4. The census, and a correction to run 84

### 4.1 All 447 pure-Q rows

Every delivered row written only in the 0° word is certified at **clearance
exactly 0**, with side exactly `⌈√n⌉`:

| quantity | value |
|---|---|
| rows certified | **447 / 447** |
| side = `⌈√n⌉` | 447 / 447 |
| clearance | 0 (n = 1 has no pairs, so no clearance exists) |
| exact contacts certified | **419,281** |
| squares covered | 205,282 |
| certified by the exact gate | 136 rows (all rows with n ≤ 250) |
| certified by the lattice lemma | 311 rows (n > 250, where the gate is O(n²)) |

The lattice lemma is a theorem, not a shortcut: for unit axis-parallel squares with
**distinct half-integer centres** inside an integer box, two centres differ by an
integer on some axis, so they differ by at least 1 there — which is exactly the SAT
condition for this word — and they touch when it is exactly 1, which is why clearance
is 0. The certificate checks half-integrality, box membership and distinctness in
exact arithmetic (`floor_q2` for the rounding), and the exact gate is run
independently on every row small enough to afford it. Both paths agree on all 136
overlapping rows.

### 4.2 The three outliers were a search bug (run 84's §1.4 corrected)

Run 84 reported n = 51 and n = 295 as "not small-height ℚ(√2) sentences". **That was
wrong**, and this run finds why: `recover_side` allowed `b` to have denominator 3
while forcing `a` onto 1/8 or 1/64 grids, so a side whose integer part also has
denominator 3 could never be seen. Probing the stored sides against every
square-free `d ≤ 21` (exact `recover_scalar`, tolerance 1e-7, twice at different
height bounds) gives:

| n | stored side (exact rational) | field | exact side |
|---|---|---|---|
| 51 | 7.690355939008 | ℚ(√2) | `16/3 + 5/3√2` |
| 126 | 11.742640688949 | ℚ(√2) | `15/2 + 3√2` |
| 295 | 17.704232794224 | ℚ(√2) | `22/3 + 22/3√2` |

and **no other field** among `d ≤ 21` witnesses any of them. With the search fixed
(`a` on the matching `4d` grid), the mixed-row lift is:

| quantity | run 84 | run 85 |
|---|---|---|
| rows lifted | 97 / 100 | **99 / 100** |
| exact contacts | 127,837 | **128,895** |
| squares covered | 37,260 | 37,606 |
| peeled / recovered centres | 26,024 / 5,618 | 26,016 / 5,795 |
| clearance | 0 | 0 (all 99), violations 0 |
| sides irrational | 97 / 97 | 99 / 99 |

The one remaining failure is n = 126, and it is now a *single square*: 125 of 126
centres lie in the field and its side is `15/2 + 3√2`, but square 120
(a 45° square at x = 1.347862817846) has no small-height value on any denominator
≤ 16 with `|b| ≤ 24`, and the 2D cage refuses to invent one. So the census's final
honest split is **99 exact sentences + 1 row with one off-lattice square**, and the
"3 float artefacts" of run 84 becomes "1 off-lattice square in 1 row".

### 4.3 The exact 2D feasible cage

The old fallback recovered each coordinate independently by height search; the
cage replaces it:

* the cage walls are the lattice points within 1e-7 of the stored coordinate on
  each axis (`_lattice_candidates`, exact rounding by `floor`);
* the filter is the box plus the **exact SAT predicate against every placed
  square** — the joint 2D condition, not two independent 1D ones;
* the returned point is canonical: nearest the stored coordinate, ties broken
  lexicographically, so it does not depend on search order;
* a point that fails the 2D predicate is never returned, and an empty cage returns
  nothing (both directions are control 12).

It recovered the freed square of `S(2,1)` exactly at `(1/2, 1/2)`, and it is what
refuses n = 126's square 120 instead of proposing a value that would fail the gate.

## 5. What is proved, measured, and not claimed

**Proved.** The tower's sign/order/floor are total for every square-free `d`
(the mixed cases reduce to `a²` vs `d b²`, and no nonzero rational solution
exists). 145 decision functions in the three instruments name no `float` — and the
audit is itself tested against a planted offender. The 447 Q rows' sentences are
exact, at clearance 0, with side `⌈√n⌉`. The lattice lemma is a proof, and the gate
agrees with it on the 136 rows where both run. The two domains run on one engine
without engine-side special cases. The coboundary law is the seam-aware identity
(and the naive one is false).

**Measured.** The 99/100 lift, its contact and recovery counts, the 0.292893 gain
of every `m = 1` strip, the atoms' law bundles, the 6-of-7 sequence certification.

**Corrected.** Run 84's "3 float artefacts" (§1.4) — two of the three were a gap in
the side search, now fixed and re-measured. `47-LIFT-CARRIER-SEAM.md` keeps its
numbers as run-84 history and carries a note pointing here.

**Not claimed.** That the spatial grammar is *complete*: the wheel covers grids,
pockets, strips, rational glues, folds and three atoms, and its coverage is only as
wide as its declared families. That n = 10 or n = 40 are closed-form cells (they are
atoms). Any score movement: no row changed.

## 6. Deferred, and named

1. **A closed-form ladder covering n = 10 and n = 40.** Their lifted states are the
   data: n = 10 is a sheared ladder (columns at `1/2, 3/2, 3/2+√2/2, 5/2+√2/2` with
   two diamonds filling the diagonal gaps), n = 40 has 16 diamonds at `4 + 2√2`.
   Deriving the parametric rule from these two states, rather than fitting a count
   law to them, is the next construction question — and the wheel now has the
   machinery to check a proposed rule against both atoms.
2. **n = 126's single square.** One coordinate off every small-height lattice tested;
   either it is off-field (a float placement) or its height is larger than 24.
   A wider probe with a targeted denominator, or a proof that no small-height value
   exists, would settle which.
3. **A third domain.** The engine's slots are ready for one more registration (a
   lattice-shell domain in ℚ(√d), or the parity-coboundary complex as its own
   domain rather than a witness), which would test the "domain-agnostic" claim
   harder than two domains can.

## Reproducing

    python3 scripts/exact_field.py --selftest          # 7 controls
    python3 scripts/glm_wheels.py --selftest           # 12 controls
    python3 scripts/qsqrt2.py --selftest               # 10 controls (unchanged)
    python3 scripts/mixed_field.py --selftest          # 14 controls (unchanged)
    python3 scripts/glm_wheels.py                      # spin both wheels, ledger
    python3 scripts/glm_wheels.py --census --budget 240    # 447 Q rows, resumable
    python3 scripts/glm_wheels.py --probe --budget 240     # the 3 outliers
    python3 scripts/exact_field.py --audit             # the bytecode audit
    python3 scripts/glm_wheels.py --audit              # all three modules
