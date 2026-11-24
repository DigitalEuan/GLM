# 79 — Constraint intersection, two speedups, and n = 6, 7 (run 120)

Three things, all measured: the two-parent command now **solves** its candidate instead of sweeping for it,
two exact speedups pay for themselves with hit-rate numbers, and the settler is run on n = 6 and n = 7 at
their best known sides. Read-only: no row changed, no score moved, `submission.csv` and root `WHITEBOARD.md`
untouched. Instrument: `scripts/anchor_chain.py --forward`; record `workspace/push/anchor_forward118.json`.

## 1. Candidate generation: intersection, not sweeping

Every anchor is now the **intersection of two exact loci**, and each locus is linear in the centre:

| command | closure | how the candidate is obtained |
|---|---|---|
| `ANCHOR_CORNER` | wall + wall | one placement per corner per direction — no solve needed |
| `PROPAGATE_SLIDE` | wall + contact | wall pins one coordinate; the tangency equation is linear in the other — **one division** |
| `STACK_BLOCK` | contact + contact | two tangency equations, two unknowns — a **2x2 exact solve** in Q(sqrt d) |

The lattice sweep is gone from the closure path: `wall_contact_candidates` evaluates
`c_other = p_other + (sR - q_a(c_pinned - p_pinned))/q_b` directly, and `two_contact_candidates` inverts
the 2x2 system over the axis pairs of both parents **and of the candidate** (the 45 degree cell touches two
axis cells along *its* axis). The old frontier-slide generator survives only as `mode="frontier"`, kept
because its state space closes and that closure is itself evidence.

## 2. The two speedups, with hit rates

**(a) Bounds prefilter.** Every cell gets a conservative rational bounding box using an **integer-only**
bracket of sqrt(d) (`isqrt(d * 10^24)`, no float anywhere); two boxes that do not touch cannot produce an
overlap, so the four-axis SAT test is skipped. Measured skip rate over the runs:

| run | pairs tested | skipped by bounds | skip rate |
|---|---|---|---|
| n = 4 at L = 2 | 47 | 47 | 100 % |
| n = 5 at `2 + 1/2 sqrt2` | 12 096 | 11 894 | **98.3 %** |
| n = 6 at L = 3 | 4 584 | 4 556 | **99.4 %** |
| n = 7 at L = 3 | 48 768 | 48 477 | **99.4 %** |

**(b) Failure-pair memo.** A tested pair is remembered by its state key, so a pair refused in one branch is
not re-tested in the next:

| run | memo hits | misses | hit rate |
|---|---|---|---|
| n = 5 | 174 | 28 | **86.1 %** |
| n = 6 | 19 | 9 | 67.9 % |
| n = 7 | 256 | 35 | **88.0 %** |

**Effect on the one run that is comparable before and after** (n = 5 at the proved optimum, both with a
contact-first order): **248 nodes / 140.8 s -> 69 nodes / 30.6 s**, i.e. **3.6x fewer nodes and 4.6x less
time**. On n = 4 the same node count (5) drops from 1.0 s to 0.31 s.

**Caveat kept honest.** The 5/6/7 runs use a contact-first order with a width of 8 candidates per node. That
is a *heuristic*, so a **success** under it is a real settlement, while a **failure** under it would only
have been a search-order limit. Every failure reported below is labelled with which of the three it is.

## 3. n = 6 and n = 7 at their best known sides

Both best known sides here are **proved optima**: `s(6) = s(7) = 3` (Stromquist 2003, quoted in doc 24 —
`s(6) = ... = s(9) = 3`), realised by the plain 3x3 axis grid, whose cells are all corner- or contact-closed.

| target | L | settled | exact span | nodes | states | refusals | time |
|---|---|---|---|---|---|---|---|
| n = 4 | `2` | **4/4** | `2` | 5 | 14 | 17 | 0.31 s |
| n = 5, frontier, no caps | `2 + 1/2 sqrt2` | 4/5 | — | 69 | 68 | 0 | 6.84 s |
| n = 5, closure | `2 + 1/2 sqrt2` | **5/5** | `2 + 1/2 sqrt2` | 69 | 87 | 454 | 30.64 s |
| **n = 6** | `3` | **6/6** | `3` | 17 | 43 | 85 | **8.75 s** |
| **n = 7** | `3` | **7/7** | `3` | 128 | 159 | 821 | **102.6 s** |

**There is no stall on n = 6 or n = 7.** Both reach the target at a span exactly equal to the proved optimum,
so the honest verdict for these two is *neither exhaustion, nor a missing command, nor a budget limit* —
the grammar settles them. The only stall in the table is the frontier-mode n = 5 run, and that one **is**
genuine state-space exhaustion (69 nodes expand to 68 distinct states and the stack empties).

**The honest limit of these two results.** A settlement at `L = 3` for 6 or 7 cells is *not* evidence of a
new packing: the 3x3 grid achieves it, and every cell of that grid is corner- or contact-closed, which is
exactly the class the grammar enumerates. So n = 6 and n = 7 confirm that the constructor is **sound and
complete on the grid regime** — they do not test it where the grid fails. That test remains n = 212
(budget-limited probe) and the unbeaten rows (no attempt yet).

## 4. Checks

| check | result |
|---|---|
| `anchor_chain.py --selftest` | n=10 side `3 + 1/2 sqrt2`, n=18 side `7/2 + 1/2 sqrt7`, 28/28 anchors, refusal at exact slack `-1/4` |
| `anchor_chain.py --forward` | the five runs above, JSON written |
| `glm_wheels.py --audit` | **654 decision functions, 0 offenders**; `anchor_chain` 41, none naming float |
| `sqscore.py`, `record_guard.py`, `void_insert.py --selftest` | green |
| `submission.csv`, `WHITEBOARD.md` | untouched |
