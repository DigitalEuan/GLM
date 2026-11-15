# 01 — Overview: Squares in Squares through the GLM

## The competition

Pack n unit squares into the smallest axis-aligned square, for 1,000 puzzles
(n = 1…1,000). Score = Σ (L/√n − 1), lower better; a missing puzzle is
charged the trivial grid ceiling. This is a classic **open problem in
combinatorial geometry**: for most n, the optimal packing s(n) is unknown,
and the best-known packings are decades of collective human work. The brief:
run the established systems first, then devise original methods (cent
compiler), and see how far we can get.

## The layered answer (what we did)

**Layer 1 — Established systems (expected, all encoded and verified):**
the trivial grid (⌈√n⌉); Friedman's survey of best-known packings
(EJC DS#7, 2009) with Göbel's diagonal-strip and central-square families
(verified: count(a) = ⌊a²+a+3+(a−1)√2⌋ matches all published values, exact
√2 bounds); the proven values (s(2)=s(3)=2, s(5)=2+1/√2, s(6)=s(7)=s(8)=3,
s(10)=3+1/√2, s(14)=s(15)=4, s(24)=5, s(35)=6, Nagamochi's s(k²−2)=s(k²−1)=k);
and the L-extension closure ("put an L of squares around a packing").

**Layer 2 — Original methods (cent-engineered):**
- a **pressure-settling engine** (position-based relaxation with SAT-axis
  separation, frozen-angle settling, adaptive shrink continuation, declared
  deterministic LCG) — a cent pipeline over primitives `state_space`,
  `sat`, `hysteresis`, `rate`;
- a **residue-family cascade planner**: systematic application of the
  L-extension closure from selected base packings — one base at n = k₀²+r
  opens the *entire* family k²+r for all k (exact two-path accounting);
- the pipeline's measured/exact split: search is measured (float64, declared
  margins); certification is rigorous (SAT non-overlap + containment at
  1e-9 margin, two disjoint check paths).

## What we achieved (verified)

| Result | Value |
|---|---|
| base packing found | **5 squares in L = 2.8** (engine, 2 s) |
| cascade generated | **29 packings** (k²+1 family: 10, 17, 26, …, 962) |
| improved puzzles | **30** (each L = k+0.8 < grid k+1) |
| grid baseline score | 28.937670 (exact: 28.9376699165…) |
| our score | 28.350038 |
| **improvement** | **−0.587631** |
| certified | 30/30 (SAT + containment, margin 1e-9) |
| submission | `submission/submission.csv` (all 500,500 rows) |

And one satisfying consistency result: the engine **refused** to pack 6
squares below L = 3 — exactly matching the proven theorem s(6) = 3
(Kearney–Shiu 2002). A jammed search that respects known impossibility
results is evidence the instrument is honest.

## The frontier (documented, not hidden)

Deep targets (5@2.72, 10@3.72, 11@3.9, 17@4.75 …) jammed just below
feasibility — the relaxation reaches its frontier at ~0.02–0.05 under grid
without stronger moves. Wave-3 rescue runs are logged; every failure is a
measured energy, not a shrug. The famous best-known packings (Göbel strips,
Trump's 11, Cantrell's improvements) require *structured* tilted families —
rediscovering those numerically is the next methodological step (docs/05).

## Repository layout

README.md · docs/ (established map, original methods, engine design,
boundaries) · scripts/ (TCT bundled + 6 column3 modules + 3 search drivers)
· lean/ (Lake project) · cent/ (optimization loop) · ledgers/ ·
verification/ · submission/ (found.json, cascade.json, submission.csv).
