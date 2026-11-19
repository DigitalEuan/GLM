# 43 — No row has slack; the table is sixty slacks (Run 80)

Instrument `scripts/refine_cascade.py` (5 controls); ledgers
`workspace/push/refine_cascade.json`, `refine_cascade_profile.json`,
`refine_cascade_chain.json`. Read-only: **no row changed**, no score claimed,
`submission.csv` untouched.

**The question.** Can any solve we already hold be refined even slightly further
— not the ones already proven optimal — and can a cascade family planner
propagate such a refinement?

**The answer, in two parts.**

1. **No.** All 553 beating rows refuse a local shrink even at 1e-7, with the
   entire wall ring free. Every beating row is locally rigid at frozen angles.
2. **The cascade is not a lever we can pull, because it has already been pulled
   everywhere.** 969 of 969 non-square rows sit *exactly* at their residue
   class's causal chain value. The table is not 1000 solves; it is **60 slacks**.

---

## 1. The candidate set, and why it is only now testable

Run 77 certified 191 beating rows as the frozen-angle optimum of their own
declaration. That certificate is a refusal at `eps = 1e-6`, so it says nothing
about refinements smaller than a micro-unit — and the 362 beating rows above
n = 400 were never tested at all, because `declp.solve`'s LP is global and dense:
500k constraint rows at n = 1000.

So the untested population is 362 rows, and the 191 "certified" rows still owe an
answer below 1e-6. This run scans **all 553**.

## 2. The instrument

`local_solve` is `declp.solve`'s formulation verbatim — the delivered branch per
pair (`argmin` of the four SAT axes), the separation constant `0.5 + e_other`, the
sign from the delivered projection, the containment `|x + t + D| + h <= L/2` — but
the pair set is truncated to a radius where it can still bind. With `span = 0.05`
per square and `move = 0.5` global, a pair whose centres are 2.6 apart cannot come
into contact (max relative motion 0.2; binding needs < 1.2071), so the truncation
loses nothing.

The free set is the **wall ring**: every square defining one of the four extreme
edges, plus every square within 1.3 of one of them, capped at 50 by default (200
in the run reported here, where the cap was never hit). Everything else is held.

Demand ladder, descending: `1e-2 ... 1e-7`. The first feasible rung is finalized
(2e-9) and put through the exact gate; a round that gates at a strictly smaller
side is accepted and the next round starts from the new state, up to twelve
rounds. A refusal is a **local** statement and is labelled one.

Controls (all pass):

1. on n = 10, 50, 100 the local LP agrees with `declp.solve` on feasibility at
   `L0`, `L0 - 1e-6`, `L0 - 1e-3` with every square free;
2. a rigid 5×5 grid at L = 5 is refused at every rung — no hallucinated slack;
3. a wall loosened by +0.02 is found and put back to the delivered side
   (3.727107 → 3.707107) in two rounds;
4. the gate, not the LP, is the judge: a raw LP state is refused (pen 7.6e-13)
   and the finalized one is accepted;
5. the cascade arithmetic reproduces a hand sum (n = 50, r = 1, 25 members,
   W = 1.571665).

## 3. Every beating row is wall-pinned

    scanned           553 of 553 beating rows
    refined           0
    free-set cap hit  0 row-rounds   (fmax = 200)
    row gain          0.000e+00

Not one of them could give back 1e-7 at frozen angles, let alone 1e-2. The wall
squares of every delivered beat are in contact with their neighbours and with
each other, so the classic "slide the boundary inward" refinement has nothing to
grab: the constructions are locally jammed.

**Scope.** Angles are frozen (the LP cannot rotate a square), and a local refusal
is not a proof. What is excluded is the whole family of refinements that keep the
rotations and move the boundary — the cheapest and historically most productive
kind (runs 16, 25, 35). Rotation-enabled refinement is the one axis still open,
and it is a nonlinear search, not this instrument.

## 4. The table is 60 slacks, not 1000 solves

Write n = k² + r and δ(n) = L(n) − k. The cascade of `09-CASCADE.md` carries a
base's slack upward: a base k₀² + r at slack δ packs every row k² + r, k ≥ k₀, at
container k + δ. Measuring δ against the **causal** leader (the best slack in the
class at strictly smaller k — a larger row cannot serve a smaller one):

| | |
| --- | ---: |
| residue classes | 60 |
| non-square rows | 969 |
| rows exactly at their causal chain value | **969** |
| cascade-open rows, tolerance 1e-8 | **0** |
| open at tolerance 1e-9 | 25, every one of them 1.89e-9 |

The 25 rows that look open at 1e-9 *are* `finalize`'s own 2e-9 global scale: the
class leaders were finalized and the rows above them were not, so a 1.9e-9 "gap"
appears that is margin, not slack. At 1e-8 the channel is empty — the same
conclusion run 42 reached from the stale table, now exact and with the causal
condition enforced.

**What this means structurally.** The whole delivered table is a
60-parameter object:

    total = sum_r sum_{k: k^2 + r <= 1000} (k + delta*(r)) / sqrt(k^2 + r) - 1000

so

    d(total)/d(delta*(r)) = W(r) = sum_{k^2 + r <= 1000} 1/sqrt(k^2 + r),

with `W(1) = 3.6453` over 31 rows, `W(2) = 3.4437`, `W(5) = 2.3745`. A refinement
of **one** row is therefore not worth one row: if a class leader's slack drops by
Δ, the same Δ is available to all of its rows by the chain translation, and the
planner's payoff is Δ·W(r) — a factor of ~30 of leverage per class, which is
exactly why the user's hypothesis was worth testing.

Two things follow, and they are the run's real content:

* **The propagation channel is pre-applied, not missing.** Because every row
  already sits at its leader's slack, there is no un-propagated gain anywhere in
  the table. The 415 rows where construction beats the chain (run 42) are simply
  rows whose *own* construction improved the class, and the improvement was
  carried up. A cascade planner has nothing left to carry inside n ≤ 1000.
* **Only 60 rows can matter.** Since every class is one parameter, the rows worth
  attacking are the 60 class leaders, and among them only the classes whose
  leader is not already at grid: 37 classes beat, **23 classes sit at δ = 1**
  (at grid) — and those 23 are precisely the band's residue classes from runs
  78–79. The grid mass of the table is 23 unfilled slacks, one per residue, not
  447 independent row problems.

## 5. What this closes, and the one axis it leaves

Closed: boundary-slide refinement of every solve we hold (0 of 553 at frozen
angles, down to 1e-7); and the hypothesis that the cascade could magnify an
improvement we had not noticed (the channel is saturated to within `finalize`'s
own 2e-9 scale).

Left open, named:

* **rotation-enabled refinement** — the LP cannot turn a square, and a turning
  square is the one move that changes a contact's axis. A nonlinear solver over
  one square's angle is the next instrument, not this one.
* **margin mining** — re-finalizing at a smaller gap than 2e-9 would shave ~2e-9
  off each of 553 sides, worth ~1e-7 in total, at the cost of the contact margin
  that protects the delivery from 12-dp rounding. Available, measured, and not
  taken: it is bookkeeping, not geometry.
* **the 23 unfilled slacks** — the band, where runs 78–79 showed the two cheap
  constructions give 0 of 14 and capacity m ≤ 0.

## 6. Re-running

```bash
cd source_material/ToDo/squares_in_squares
python3 scripts/refine_cascade.py --selftest                 # 5 controls
python3 scripts/refine_cascade.py --n-min 1 --fmax 200       # 553 rows, ~3.5 min
python3 scripts/refine_cascade.py --profile                  # the 60 slacks
python3 scripts/refine_cascade.py --chain                    # build + gate the chain
```
