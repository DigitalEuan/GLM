# 05 — Original methods: the cent pipeline

The brief: after the established systems, *devise original methods*. Two
were engineered here, both decomposable into the ¢ vocabulary.

## Method 1 — pressure-settling engine (cent primitives)

The packing problem compiled to primitives:

| Primitive | Role in the engine |
|---|---|
| `state_space` | the configuration space: (x, y, θ) per square |
| `sat` | SAT penetration resolution — the contact law (push along the min-penetration axis) |
| `hysteresis` | angle freezing during settling; Metropolis rescue only at jams; retreat-on-jam memory |
| `rate` | the shrink schedule (continuation delta, adaptive halving) |
| `eq` | feasibility predicate: zero penetration ∧ containment |
| `mult` | energy accumulation (pen² terms) |
| `spatial` | bbox extents: half-width = (|cosθ|+|sinθ|)/2 |

Design lessons (each won by a failed build, docs/07):
1. **Resolve along the SAT axis**, not the center-line (v1's center-line
   pushes jammed rotated squares).
2. **Freeze angles while settling**; angle moves after wall projection
   create infeasible states (v2's bug).
3. **Continuation, not direct attack**: shrink from a feasible grid
   (Gensane–Ryckelynck family), with adaptive delta halving and re-heating
   at jams.
4. **Deterministic LCG** — the search is reproducible; "no randomness" is
   satisfied in the UBP sense (no unseeded entropy).

The engine found 5@2.8 in 2 s and *refused* 6@2.9 — matching proven
s(6) = 3 (the instrument respects impossibility).

## Method 2 — residue-family cascade planner (original)

Friedman's L-extension closure is known; the **planner** is ours: treat
closures as a *generating function over puzzles*.

- A base packing at (m, L) with L < ⌈√m⌉ generates the chain
  m, m+⌊L+1⌋+⌊L⌋, … at L+1, L+2, … — and since ⌈√(m_{j+1})⌉ − (L+j+1)
  stays positive, **every chain member beats grid**.
- Chain arithmetic (two-path verified): from 5@2.8: 10, 17, 26, 37, 50,
  65, 82, 101, …, 962 = k²+1 at k+0.8 — 30 puzzles from ONE base.
- Residue classes: a base at k₀²+r opens family k²+r for all k. So the
  strategic targets are *marginal bases* at small n (11 → k²+2, 12 → k²+3,
  13 → k²+4, …), not deep records. This re-frames the search problem: we
  do not need Trump's 11@3.877 — we need **11@3.98** to open 30 more
  puzzles. (Wave-2/3 runs target exactly these; frontier report below.)

## The frontier, honestly

| Target | Status | E at best attempt |
|---|---|---|
| 5@2.8 | **FOUND** (base) | 0 |
| 5@2.72/2.75 | jammed | 0.054 / 0.030 |
| 10@3.85 | jammed | 0.038 |
| 11@3.97/3.98 | jammed (closest miss) | 0.026 / **0.0129** (wave-3) |
| 17@4.95 | jammed | 0.021 |
| 18@4.97/4.98 | jammed | 0.044 / 0.049 (wave-3) |
| 6@anything < 3 | **impossible** (s(6)=3) | refusal = theorem agreement |

Jams land at |E| ~ 1e-2: the relaxation needs *structured tilted motifs*
(45° strips, 40° pairs) to proceed — the historical packings' signature.
Seeding with such motifs (Göbel-strip parameterized seeds) is the next
engineering step; the parameters of the strip families are all in docs/04.

## Method 3 (proposed, not yet run) — motif-seeded search

Parameterize the Göbel/Cantrell/Trump motif families analytically (strip
width w, tilt θ, offset δ), seed the engine inside each family, and let
relaxation polish — a hybrid of exact family geometry and numeric settling.
Expected yield: match-or-beat best-knowns on the 33 encoded n (docs/02 #7),
and the n > 100 range where literature packings are sparse.

## Frontier resolution (final update)

Method 3 was never needed as a *search* method: the tilted motifs it sought
are exactly what the maintained survey (Friedman/Ellsworth) publishes as
high-precision SVGs. Integrating that source (235 SVGs parsed with the
survey's own tool), completing it with removal windows (⌊s⌋² < n ≤ N_pic)
and partial-fill cascade chains, reproduced the survey's authoritative
table exactly (214/214 cross-check for n ≤ 324) and carried the same
state of the art to all n ≤ 1000: **score 23.284687** (grid ceiling
28.937670), 399/1000 puzzles beating the grid.

The jam table above is now historical: e.g. 11@3.877 is *in* the records
(Trump 1979, 8th-degree root); 17@4.6755 (Bidwell 1998) likewise. The
remaining 601 grid-tied puzzles (mid-block n like 343..360, 380..399) are
open problems: per-block chain-reach limits were proven (max reach at
container ≤ k+1−ε over all stored states; e.g. block 19: 342 = 307@17.98
+ 35 band cells), the Göbel-square family was enumerated under its
constraint (nothing new), and the survey itself lists no record beating
the grid there. Motif-seeded search *beyond* the survey remains the open
frontier — with the bar now set at matching published records first, then
beating them by the same pipeline.
