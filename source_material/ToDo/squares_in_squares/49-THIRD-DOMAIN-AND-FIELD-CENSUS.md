# 49 — A third domain, the induction that failed, and a complete field census (Run 86)

Instruments: `scripts/lattice_shells.py` (new, third domain), `scripts/grammar_induction.py`
(new), `scripts/field_triage.py` (new), `scripts/glm_wheels.py` (extended: 17 controls).
Ledgers `workspace/push/glm_wheels.json`, `induction.json`, `field_triage.json`;
probe `workspace/push/probe_126_cage.py`. **No row changed, no score claimed,
`submission.csv` untouched.**

| item | result |
|---|---|
| 1. third domain (lattice shells) | **28 cells, 24 certified, 4 refused by law**; theta/kissing all exact |
| 2. induction from the atoms | **1/45 exact decompositions** — atoms are irreducible over the vocabulary, and the reason is measured |
| 3a. n = 126 | pose is off-lattice by 4.1e-3; the topology **is** Q(√2)-realisable (**173** placements) |
| 3b. field census | **all 1,000 rows classified**: 447 grid, 100 pose, 26 higher/side fields, 4 rational-t, 424 continuous |

---

## 1. Third domain: integer and quadratic lattice shells

`lattice_shells` shares no scalar arithmetic with the packing domain: no `Q2`, no
tolerance, no side length. Vectors live in the *doubled* lattice — a point of
(1/2)Z^d is a tuple of ints `y` meaning y/2 — so every norm is `sum(y*y)/4` and every
inner product an integer sum. The same six slots are registered with new meanings:

| slot | lattice meaning | law |
|---|---|---|
| `Tile` | one shell `L_m` | `r_L(m)` exact |
| `Frame` | minimal shell + kissing graph | `|L_min|`, degree set |
| `Strip` | the ball to radius √M (annuli) | `N(0..M) = Σ r(m)` |
| `Glue` | direct sum `L ⊕ M` | `θ(L⊕M) = θ(L)·θ(M)` |
| `SymmetryFold` | `v ↦ −v` | `r(m)` even, `r/2` pairs |
| `Atom` | the lattice itself | rank, `m_min`, kissing |

**The theta series are computed, not remembered** (pruned enumeration over
`Σ y² = 4m` with Legendre/Fermat feasibility prunes, exact ints):

| lattice | θ coefficients | kissing | root degree |
|---|---|---|---|
| Z² | 1, 4, 4, 0, 4, 8, 0 | 4 | — |
| Z³ | 1, 6, 12, 8, 6, 24, 24 | 6 | — |
| Z⁴ | 1, 8, 24, 32, 24, 48, 96 | 8 | — |
| D₄ | 1, 0, 24, 0, 24, 0, 96 | 24 | 8 |
| E₈ | 1, 0, 240, 0, 2160 | 240 | 56 |

The `Glue` law is the sharp one: for Z²⊕D₄ the *enumerated* shell sizes
(1, 4, 28, 96, 124) equal the convolution of the two theta series, at every m — the
witness recomputes the convolution independently from the two summands, so a wrong
direct sum cannot pass by agreeing with itself. The wheel spins **24 of 28 cells
certified**; the four refusals are all laws, not failures:

    D4 , m = 3        empty_shell   "even lattice, odd norm"
    E8 , m = 1        empty_shell   "even lattice, odd norm"
    Z2 (+) E8         rank_budget   rank 10 > 8
    Z4 (+) E8         rank_budget   rank 12 > 8

Control 17 also shows the topology witness *catching a liar*: claim Z⁴'s kissing
number as 24 (the true value is 8) and it is refused.

### 1.1 Friction — where the engine needed generalizing

The engine held, but four things were only *conventionally* domain-agnostic, and
they are worth naming rather than smoothing over:

1. **A real bug, now fixed.** Running `glm_wheels.py` as a script makes it
   `__main__`; a domain module doing `import glm_wheels` then gets a *second* module
   object with different `Claim`/`Refusal` classes, so `except Refusal` silently
   failed to catch. Fixed with one line (`sys.modules.setdefault`) rather than by
   duplicating the class. This is the kind of thing that only shows up when a second
   module participates in the type system.
2. **`Wheel.spin`'s row schema is packing-shaped.** It reads `claim.n`,
   `laws["extent"]`, and `meta["beats"]/["gain"]`. The lattice domain repurposes `n`
   as a cell count and leaves gain `None`; nothing broke, but the schema is by
   convention, not by type.
3. **`DecimalWitness` had to be re-implemented** (`DecimalLatticeWitness`) because
   `_dec` assumes a `Quad` scalar. The *protocol* (`applies`/`check`) generalized
   cleanly; the payload is duck-typed, so the witness cannot be shared.
4. **"Four witnesses per claim" becomes "every applicable witness".** The kissing
   witness scopes itself to `Frame`/`Atom`, so a `Glue` cell has three witnesses and
   three *kinds* of evidence. That is honest, but it means the four-witness slogan is
   per-family, and control 16 asserts 3 for the glue rather than pretending otherwise.

## 2. Inducing closed-form grammars from the lifted atoms

The induction is exact, not statistical: a template *occurs* in a state iff one of the
five isometries of the unit square (identity, the two axis reflections, the diagonal
reflection, a quarter turn) carries its centres **and its words** into the state under
a single translation; a cover is a set of disjoint occurrences; the induction
succeeds only when the cover is exact.

Scope: the three atoms (n = 5, 10, 40) plus every stripped lifted row small enough to
lift inside the budget — 45 states, 13 templates, 5 isometries, 225 pairings each.

**Result: 1 exact decomposition in 45 states.** The one is n = 5 via `Pocket1` — and
that is not news: `Pocket(1) = Strip(1,1)` is the closed form we already had, and
`Pocket1` is the same sentence as the atom. `Strip2,1` and `Glue1/2` occur in **zero**
states; `Pocket1`/`Fold1` occur only in n = 5 itself.

What the failure *is*, measured: in every state the best cover is `Tile1`, and it
covers exactly the axis squares —

| state | squares | tilted | Tile1 cover | fraction |
|---|---|---|---|---|
| n = 5 | 5 | 1 | 5 | 1.000 (exact) |
| n = 10 | 10 | 2 | 8 | 0.800 |
| n = 19 | 19 | 8 | 11 | 0.579 |
| n = 26 | 26 | 9 | 17 | 0.654 |
| n = 27 | 27 | 5 | 22 | 0.815 |
| n = 40 | 40 | 16 | 24 | 0.600 |

mean best coverage over all 45 states: **0.7324**. And n = 40 additionally contains
**four exact 2×2 `Tile2` blocks** (16 squares) inside its axis part — the only
sub-block structure the search found.

So the honest statement of item 2 is a **negative with a cause**: the atoms are not
compositions of the declared families. They decompose only over the *alphabet*
(axis Tile ⊕ single 45° diamond), where the count law is `N = a + d` with `d` the
tilted count — true by construction and therefore not an induction. What is missing
is a **diamond-placement primitive**: `Pocket` and `Strip` embed diamonds only in
their own fixed patterns, so a row that tiles an *irregular* set of diamonds (2 for
n = 10, 16 for n = 40, on a bent grid / a 45° checkerboard) has no family to belong
to. That is now a named, precise piece of deferred work rather than a vague wish.

## 3a. n = 126: the pose is off-lattice, the topology is not

The lift now places 124 squares by peeling, **recovers square 98 exactly by height
search** — `(5 − 2√2, 19/2)`, a value with height 2 that the earlier search missed
because the *neighbouring* coordinate needed a third-denominator component — and
leaves square 120.

**Square 120's structure is degenerate, and this is the key measurement.** It touches
exactly two squares, 98 and 109, and both contacts constrain the *same* SAT axis, so
the two linear equations are identical:

    (−√2/2)·x + (√2/2)·y = 5/2 + (11/4)√2      i.e.   y − x = 11/2 + (5/2)√2

Rank 1: the topology does **not** pin the square — it leaves a line. The stored pose
sits on that line to 1.54e-9. The exact feasible set on the line (70-digit Decimal,
all 124 partners, bisected) is

    x ∈ [1.3357864376269049512, 1.3713203435596425732],   width 0.0355339059

with the left end bound by partner 109 and the right end by partner 98; the stored
x = 1.347862817761 sits 0.0121 from the left end. So the cage is a real segment, not
a point — and the stored coordinate is *inside* it.

Then:

* **the cage at tolerance 1e-7 and 1e-4 is empty** — the stored x is not a small-height
  field element;
* **the cage at large tolerance is not empty**: enumerating Q(√2) placements with
  denominators ≤ 32 and heights ≤ 8 on the line inside the segment, **173** pass the
  full exact gate at clearance 0. The nearest is `x = 43/32` (exactly rational!), at
  L1 distance **8.2e-3** from the stored pose, i.e. 4.1e-3 in x.

Verdict, stated in the only honest form: **the stored pose of square 120 is
off-lattice — 1.347862817761 is 4.1e-3 from 43/32 and admits no field value at
height ≤ 8 on denominators ≤ 32 — but the row's contact structure is
Q(√2)-realisable.** So the ledger split is

| reading | count |
|---|---|
| poses exactly lifted into Q(√2) | **99 / 100** |
| rows whose contact topology has a Q(√2) realisation | **100 / 100** |

Both numbers are true; they are not the same claim, and the ledger must not merge
them. Run 84's "3 float artefacts" is now fully resolved: two were a side-search gap,
and the third is one square whose *stored* coordinate is transcendental while its
*topology* is not.

## 3b. Every row gets an exact field class

The triage classifies all 1,000 rows. Angles are read as exact Fractions (the table is
in radians); `cos`/`sin` are computed in 70-digit `Decimal` by Taylor series with
exact-precision range reduction (no float anywhere); a Pythagorean angle is detected as
a rational `t = tan(θ/2) = sin/(1+cos)` by continued fraction with a declared 1e-12
residual; the side test reuses `exact_field.recover_scalar`, whose comparison is exact
and whose lattice is deliberately small (denominators ≤ 8, height ≤ 4) so a row is not
credited to a field it only reaches by growing the search.

| class | rows | detail |
|---|---|---|
| `Q-grid` | **447** | all angles 0°; certified at clearance 0 by the census |
| `Q(sqrt2) pose` | **99** | 0°/45° sentence lifted exactly (four witnesses) |
| `Q(sqrt2) side` | **18** | container side in Q(√2) (includes n = 126: `15/2 + 3√2`) |
| `Q(sqrt7) side` | **5** | `7/2 + √7/2` (n=18), `13/2 + √7/2` (53), `23/2 + √7/2` (151), `29/2 + √7/2` (234), `53/2 + √7/2` (747) |
| `Q(sqrt5) side` | **3** | `99/8 + 23/8√5` (335), `107/8 + 23/8√5` (373), `123/8 + 23/8√5` (454) |
| `rational-t` | **4** | all angles Pythagorean: n = 50, 171, 198 with `t` denominators ≤ 3, n = 230 with ≤ 7 |
| `continuous` | **424** | neither: the side is not in a square-free field ≤ 21 at small height |

The 26 higher/side-field rows are the interesting residue: rows that no rotation
argument explains but whose *box* is exactly algebraic. n = 18 at `7/2 + √7/2` is the
smallest — a 5th-degree-of-freedom case the wheel has no cell for. And the four
`rational-t` rows confirm the t-basis story quantitatively: Pythagorean packings are
rare (4 of 1,000) and always small-denominator (≤ 7).

---

## 4. What is proved, measured, and not claimed

**Proved.** The theta coefficients, kissing numbers and root degrees above are exact
enumerations (the prunes are necessary conditions only, so they cannot change the
answer). `θ(L⊕M) = θ(L)·θ(M)` holds cell by cell for both glue cells. The lattice
domain names no `float` — 175 decision functions across four modules, audited in
bytecode. n = 126's rank-1 contact algebra is exact, and its feasible segment is a
70-digit Decimal measurement whose ends are identified partners.

**Measured.** 24/28 lattice cells certified; 1/45 exact decompositions with mean best
coverage 0.7324; 173 field placements in n = 126's cage and the 8.2e-3 nearest;
the 1,000-row field tally.

**Not claimed.** That the atoms have no closed form — only that they are irreducible
over the *declared* vocabulary, under translation and reflection, by exhaustive
search. That n = 126's stored pose lifts: it does not, and the doc says 99/100 for
poses. That `continuous` means non-algebraic: it means "not in a square-free
Q(√d), d ≤ 21, at denominators ≤ 8 and height ≤ 4" — a bounded, declared test, and
growing it could only reclassify rows *into* fields, never out.

## 5. Deferred, and named

1. **A diamond-placement primitive.** §2 says exactly what is missing and what it must
   cover: 2 diamonds on a bent grid (n = 10), 16 on a 45° checkerboard (n = 40), 8 at
   n = 19. A `DiamondField(spec)` combinator taking an exact placement set is the next
   step, and the induction search is now the acceptance test for any proposed rule.
2. **The 26 side-field rows.** They have an exact box and no exact grammar. n = 18 at
   `7/2 + √7/2` is the smallest; a Q(√7) wheel (same engine, different `d`) is now a
   one-parameter change.
3. **A fourth domain** would test the claim harder; the friction list in §1.1 is the
   map of what to expect (payload duck-typing, per-family witnesses, packing-shaped
   row schema).

## Reproducing

    python3 scripts/glm_wheels.py --selftest        # 17 controls
    python3 scripts/glm_wheels.py                  # three wheels, 175-function audit
    python3 scripts/glm_wheels.py --audit           # 4 modules, 0 offenders
    python3 scripts/grammar_induction.py --selftest # 2 controls
    python3 scripts/grammar_induction.py            # 45 states, exact covers
    python3 scripts/field_triage.py --selftest      # 4 controls
    python3 scripts/field_triage.py                 # 1,000-row class ledger
    python3 workspace/push/probe_126_cage.py        # the 173-placement cage
