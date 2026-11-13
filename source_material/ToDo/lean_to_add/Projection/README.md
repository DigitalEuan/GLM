# The projection sub-study — where each seed is allowed to enter

A self-contained, machine-checked sub-study of the UBP constants framework,
built around one question:

> A number is a *projection* of a structure with motion in it.  Which structures
> can produce `π`, `φ` and `e`, and what does the projection destroy?

Everything in this directory builds with `lake build`, contains no `sorry`, adds
no axiom, and every headline theorem depends only on Lean's three standard
axioms — audited by the `#print axioms` block in
[`All.lean`](All.lean).

The ordered list of results is **[`FINDINGS.md`](FINDINGS.md)**.  This file is
the guide: the short answer, the layout, the cost model used to choose what to
build, and the limits.

---

## Short answer

**1. There is a hard constraint on where each seed can enter, and it is now a
theorem.**  A linear map of finite order has only roots of unity as eigenvalues,
so a finite symmetry group's character values are sums of roots of unity, hence
algebraic.  No finite group acting linearly — on any module, in any dimension —
can produce a transcendental invariant.  When the module is a *lattice* (which is
the case for Golay, Leech, `M₂₄`, `Co₀`) the statement is unconditional and much
stronger: characters are integers, so `π` and `e` are excluded by irrationality
alone.

So the framework's "chain of levels" is a proved constraint, not an analogy:

| layer | what it produces | which seed lives there |
|---|---|---|
| 0 — counting | naturals, and rational ratios | none (proved in `FirstPrinciples/`) |
| 1 — finite symmetry | algebraic numbers in cyclotomic (abelian) fields | `φ` |
| 2 — flows | period and flow-time constants | `π`, `e` |

**2. `φ` is native to Layer 1, but not in the way the framework assumes.**  `φ`
is not merely algebraic: it is literally the trace of a rotation of order 10,
and `φ = ζ + ζ⁻¹` for a primitive 10th root of unity — so it lies in a
cyclotomic field.  But `φ` is **not** an eigenvalue of any finite-order map
(eigenvalues of finite-order maps have modulus 1, and `φ > 1`).  It enters a
finite symmetry group as a *character value*, never as a scaling.  It *is* an
eigenvalue of an infinite-order lattice automorphism — the Fibonacci matrix.

**3. `φ` shears is wrong; `φ` stretches.**  A shear (parabolic) has eigenvalue
`1` and moves vectors linearly; the Fibonacci matrix (hyperbolic) has eigenvalue
`φ > 1` and moves them exponentially.  Both statements are proved, and so is the
separation (exponential beats linear).

**4. The two projections the framework relies on are provably lossy.**  On
`SL(2,ℤ)` the trace has infinite fibres, and two integral shears with the same
trace, determinant and characteristic polynomial are *not* conjugate over `ℤ`.
The hull `⌊·⌋` over `13` has a fibre of measure 1, and three different monomials
in the seeds land in it: `πφe = 13.817…`, `πφ³ = 13.308…`, `π⁴/e² = 13.182…`.
"Run 13 backwards to the seeds" is impossible, and that is a theorem.

**5. "`φ` is the cheapest self-similarity" needs two corrections.**  `φ` is the
smallest *quadratic* Pisot number (proved here by a short integer case
analysis) — but the plastic number `ρ ≈ 1.3247`, the real root of `x³ = x+1`, is
a smaller Pisot number of degree 3 (also proved: its two conjugates have modulus
`√(ρ²−1) < 1`).  And the property that actually makes `φ` appear in packing and
stability arguments is not self-similarity but *worst approximability*:
`|φ − p/q| ≥ 1/(3q²)` for every rational.

**6. `Q` is a gauge, not an observable.**  Once the coherence budget is
calibrated to the quantum, the NRCI ladder is `8/(8+n)` whatever `Q` is.  No
statement about coherence can depend on the value of `Q`.

**7. The numerical fits now carry a number, in bits.**  `α⁻¹`: under one bit —
not evidence.  Proton: between two and three bits.  Muon: between three and four
bits.  That is a ranked development queue rather than an argument.

---

## The graded cost model used to plan the study

Each candidate module was scored before it was built: *cost* is formalisation
effort, *value* is how much of the framework's own architecture the result
settles, and the ratio decides the order.  This is the same shape as the cost
model formalised in [`Cost.lean`](Cost.lean) — a cost per step and a preference
for the cheapest path to a fixed target.

| # | module | cost | value | ratio | status |
|---|---|---|---|---|---|
| 1 | `Layers.lean` | medium | **highest** — turns the chain of levels into a constraint | best | **done** |
| 2 | `OneParameter.lean` | easy–medium | high — gives `π`, `φ`, `e` each a positive characterisation | high | **done** |
| 3 | `Fibre.lean` | medium | high — makes "information lost by projection" a theorem | high | **done** |
| 4 | `Cheapest.lean` | medium | medium — corrects a claim the framework leans on | medium | **done** |
| 5 | `Cost.lean` | easy | medium — removes a spurious parameter (`Q`) | high | **done** |
| 6 | `Surprisal.lean` | easy | medium — converts "coincidence" into a ranked queue | high | **done** |
| 7 | `Independence.lean` (appendix) | easy | medium — records what each branch of the open question does to the framework | high | **done** |
| — | algebraic independence of `π`, `e` itself | unbounded | would settle minimality | — | **out of reach** (open problem) |
| — | necessity of the modelling choices | impossible | — | — | **out of reach** (sufficiency provable, necessity never) |
| — | icosian construction of the Leech lattice | very high | would make `ℤ[φ]` action explicit | low | **not attempted**; the `ℤ[φ]`-module property can be carried as a hypothesis |
| — | "meaning", "Time", "resonance" as physics | n/a | — | — | **not mathematics** |

Everything in the top block is proved.  Everything in the bottom block is stated
here as out of reach, up front, rather than left implicit.

---

## Layout

```
Projection/
├── Layers.lean         module 1 — the layer theorem (headline)
├── OneParameter.lean   module 2 — rotation / shear / stretch, and the flow
├── Fibre.lean          module 3 — projection and fibre; the hull is not invertible
├── Cheapest.lean       module 4 — quadratic Pisot minimality, plastic number, approximability
├── Cost.lean           module 5 — gauge-independence, graded cost, shortcut/distortion
├── Surprisal.lean      module 6 — the bit-score ledger
├── Independence.lean   appendix — the two branches of the trdeg ℚ(π,e) question
├── All.lean            imports everything; axiom audit
├── FINDINGS.md         the ordered list of findings, with verdict tags
└── README.md           this file
```

Dependencies: modules 1 and 2–4 build on the parent study's seed definitions and
verified enclosures (`UBP/Seeds.lean`, `UBP/SeedClasses.lean`,
`UBP/Enclosure.lean`); module 6 builds on the capacity bounds proved in
`FirstPrinciples/FitCapacity.lean`.  Nothing in the parent study was modified.

## Build

```bash
lake exe cache get     # optional: prebuilt Mathlib
lake build             # builds everything, including this directory
lake build Projection  # this directory only
```

The axiom audit is the `#print axioms` block at the end of `All.lean`; it prints
one line per headline theorem, and every line must read
`[propext, Classical.choice, Quot.sound]`.

## Method notes

* **Transcendence is carried as a hypothesis.**  The pinned Mathlib does not
  contain the Lindemann–Weierstrass theorem, so statements that need "π is
  transcendental" or "e is transcendental" take them as explicit hypotheses, as
  the parent study does.  Where a result can be obtained from *irrationality*
  alone — which Mathlib does have — it is stated unconditionally, and that is
  why the lattice version of the layer theorem is the strongest one here.
* **No axioms are added.**  Hypotheses are arguments to theorems, never
  `axiom` declarations.
* **Numerical claims use verified interval arithmetic.**  Every decimal in this
  directory comes from the parent study's `Enc` enclosures, so a claim such as
  `⌊π⁴/e²⌋ = 13` is a kernel-checked consequence of rational bounds on `π` and
  `e`, not a floating-point evaluation.
* **Definitions are minimal.**  `IsQuadPisotPair` is Vieta's relations plus two
  inequalities, so the minimality theorem needs no algebraic number theory;
  `ReachIn`/`wordLen` are the word metric written out, so the distortion theorem
  needs no geometric group theory.
