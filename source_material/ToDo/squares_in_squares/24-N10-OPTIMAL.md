# 24 — n = 10 is a proved optimum, and the table is exact on every proved row (run 56)

Instrument `scripts/optima.py`, ledger `workspace/push/optima.json`. Read-only:
no row changed, no score moved. **This document retracts a run-55 claim.**

## 1. The correction

Run 55 said the seed wheel left "0.51 of theoretically admissible side" untouched
at n = 10. That was wrong, and the review is right about why:

> **s(10) = 3 + 1/√2 = 3.707106781186…** is **proved optimal**, not best known.
> W. Stromquist, *Packing 10 or 11 Unit Squares in a Square*, Electron. J.
> Combin. **10** (2003) #R8, doi:10.37236/1701, Theorem 1. Restated in Friedman's
> survey (DS7, §1): "In 2003, Stromquist proved s(10) = 3+1/√2". The same paper's
> opening paragraph also states s(1)=1, s(2)=s(3)=s(4)=2, s(5)=2+√2/2,
> s(6)=…=s(9)=3.

So the Karakuş floor `s(10) ≥ 3.192582404` is **0.514524 below** the true optimum.
That number is **looseness in a general bound**, not unclaimed packing space, and
no construction can sit in it. Two things follow immediately:

* a general lower bound with a large numeric gap is not evidence of room. It was
  used correctly in `21` as a *prune* and incorrectly here as a *target*;
* n = 10 is an **optimality control**, not a place to look for a smaller side.

## 2. The control, checked rather than asserted

All of it is exact arithmetic on the delivered row, not a float comparison:

| check | result |
| --- | --- |
| `snap(L_del − 3)` | **`1/2·√2`** — exactly the algebraic value |
| delivered `L(10)` | 3.707106782648 = `3 + ½√2` + 1.5e-9 (the finalizer pad) |
| exact gate at `L = 3 + ½√2` | **ok, worst penetration 0** |
| certified wheel cells below optimum − 4e-8 | **0 of 80** |
| best wheel cell | `centred/edge`, offset (−1+½, −1+½), 3.707106791 = optimum + 9.8e-9 |

The last two lines are the point: the best cell in the seed wheel **is** the
delivered row's construction, certifying at the proved optimum, and nothing in
the 436-cell grammar certifies below it. So run 55's negative was a **forced
negative**: the grammar could not have produced a gain at n = 10 because no
packing better than `3+½√2` exists. What it actually did was **recover a known
optimal construction exactly** — a positive control for the builder, the gate and
the mask representation, and the right kind of result for a benchmark row.

The construction is Göbel's (1979) diagonal strip: two tilted squares at 45° in a
strip with eight upright squares (Friedman's survey and the Kingbird catalogue
both attribute the n = 10 optimum to Göbel, tilt angles 0° and 45°). The catalogue
also lists an **alternative** n = 10 packing "with minimal rotated squares" that
adds an L-shape to s(5). That alternative is a distinct production and is **not**
in my grammar; adding it is a coverage test, not a route to a better side.

## 3. The battery: every proved row at once

If one row is at its optimum, the natural question is how many others are. `optima.py`
compares the delivered table against **every exactly-known s(n)**, and classifies
each row as `at` (a control), `above` (a real target — a proved smaller side
exists) or `below` (impossible; would indict the table):

    42 proved rows checked:   at = 42   above = 0   below = 0

The 42 are the squares `1²…31²` (s(n)=√n) together with n = 1, 2, 3, 5, 6, 7, 8,
9, 10, 14, 15, 24, 35 (Stromquist's opening paragraph; Friedman DS7 §1 for
`14, 15, 24, 35` and the square case). Every one sits exactly on its proved
value to within the 1e-6 tolerance that the stored 2e-9 pad requires.

Two consequences, both sharper than "the table is good":

1. **No score is available on any proved row.** There is no packing to find
   there — the value is already optimal, and any apparent gain would mean the
   gate, the scorer or the table is wrong, which is why `below` is treated as a
   defect and makes the script exit non-zero.
2. **The only two proved rows that beat the grid are n = 5 and n = 10**, and both
   are exactly optimal (`2+½√2` and `3+½√2`). So the entire remaining 0.1637 of
   aggregate gap lives in rows whose optimum **nobody knows** — the open rows.
   That is where a new construction can matter, and nowhere else.

It also settles a question from `20`: the construction grammar reproduces **both**
proved non-trivial optima exactly (n = 5 through the diamond, n = 10 through the
two-tilt seed). The grammar is adequate for the published constructions at the
sizes where they are proved; what is missing is a construction for the rows that
are *not* proved, which is a different problem from representing the ones that are.

## 4. What this changes about the target

The review's instruction is accepted without reservation: **do not enlarge the
n = 10 fill search hoping to beat 3.7071.** n = 10 stays in the instrument as a
control, and its grammar may still be extended for coverage (the Göbel
alternative), but it cannot produce score.

For score, the filter is now two-staged, and both stages are decided:

1. **Proved rows are out** (42/42 at optimum, this run).
2. Among unproved rows, the forward-only ranking of `22` §6 says no delivered
   column gains by re-placing its own base (`now` = 0 for every column, because
   slack falls with k), so a gain requires a *better* base than the column
   already contains. The optimistic per-start bounds put the largest single
   upper bound at the shallow end (r = 1 at n = 10, which is optimal and closed)
   and the base-less window at 0.058535 for all of 38–60.

So the honest next target is **not** a shallow proved row and **not** the deep
base-less columns: it is an **unproved row in an open column**, where a new
construction could be certified exactly and where the corrected ranking says the
payoff is real. Catalogues (Friedman, Kingbird, Gensane–Ryckelynck) can *nominate*
such rows and their constructions; their floats are nominations, never
certificates, and nothing enters the table without passing the exact gate.

## 5. What this does not show

* No new construction and no score change. This run fixes a claim and adds a
  control battery.
* The catalogue's best-known values for **unproved** rows are compared in run 57
  (`25-OPEN-ROW-CROSSWALK.md`): 10 at the published construction, 2 below it,
  0 above, so there is no import target among the 12 rows checked. Floats are
  compared at their printed precision and labelled as such.
* The Göbel "minimal rotated squares" alternative for n = 10 is not implemented.
* `at` means "the table equals the proved optimum", not "my grammar proves it".
  The optimality is Stromquist's theorem; the grammar only reproduces the
  arrangement.

## 6. Files

* `scripts/optima.py` — `proved()` (exact Q2 values, sourced) and the three-way
  classification; exits non-zero if any row is below a proved optimum.
* `workspace/push/optima.json` — 42 rows with `at`/`above`/`below` and deltas.
* retracts `23` §2's "0.51 of theoretically admissible side"; the n = 10 control
  is also recorded in `23`'s ledger cell for the winning grammar production.
