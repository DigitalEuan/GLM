# 36 — The cube grid is optimal for every n, and the score is exactly rotation (Run 73)

*(Title read precisely: optimal for every n **in the axis-parallel class** — see §2.1, added run 74.)*

Run 72 left n = 9 open in `(2, 3]`: the declared-axis LP gave constructions, and the only bound it
could certify stopped at n = 4. This run was meant to settle that one row. It settles **every** row,
by an argument, and the argument turns out to explain the whole 1000-row score.

No row of the table changed. The delivered total is still `22.218056945` *(historical: at that time)*, 553 beats, and
`sqscore.guard()` holds.

## 1. The answer to the question as asked

**L(9) = 3 exactly.** It is not in `(2, 3]`; it is 3, and the 3×3×1 grid attains it.

## 2. The theorem (and it is not about n = 9)

For axis-parallel unit cubes in a cube of side `L`, in `d` dimensions:

* cube `i` occupies `[c_i − ½, c_i + ½]`, so `c_i ∈ [½, L − ½]`: **all centres lie in a box of side
  `L − 1`**;
* two such cubes are disjoint **iff** `‖c_i − c_j‖_∞ ≥ 1`;
* if `L − 1 < m` for an integer `m`, split that box into `m^d` sub-boxes of side `(L−1)/m < 1`. Two
  centres in one sub-box differ by less than 1 in *every* coordinate, so they are not separated, so
  **each sub-box holds at most one centre**. Hence `n ≤ m^d`.

Take `m = ⌊L − 1⌋ + 1`, the smallest integer with `L − 1 < m`. Then `n ≤ (⌊L−1⌋ + 1)^d`, and
contrapositively `n > k^d ⇒ L ≥ k + 1`. The grid `k × … × k` gives `L ≤ k + 1`. Therefore

    L_d(n) = ⌈n^(1/d)⌉  exactly, for every n, in every dimension d.

In 3D: **L(n) = ⌈n^{1/3}⌉ for every n**, so `L(9) = 3` (not 2.08–3), `L(28) = 4`, and so on. The
declared-axis LP, the descent, the extrusion question, and any future search over cube arrangements
are all answered at once: the grid is not merely good, it is optimal in this class, always, and
there is nothing above it to find.

### 2.1 The scope, stated once (added run 74)

Every word above is about **axis-parallel** cubes. It is not a theorem about rotated solids, and
the restriction is not vacuous. The same argument in two dimensions says *axis-parallel unit
squares* satisfy `L(n) = ⌈√n⌉`, and the delivered table's own n = 5 row is `2.707107 < 3 = ⌈√5⌉`
because one square is at π/4. So read the theorem as

    L_d(n) = ⌈n^{1/d}⌉  is the optimum IN THE AXIS-PARALLEL CLASS, for every n and every d.

That is exactly what §3's corollary turns on: it bounds the 447 aligned rows (they are all at
`⌈√n⌉`, so they are optimal within their class) and it says nothing at all about the 553 rows that
contain a rotated square. It also says nothing about rotated cubes — a question this project has
not asked and has no instrument for. The dimension step is free of information here; the rotation
step is not.

Consequences worth having on the record:

* the run-72 table's "strictly better" verdicts at n = 5–8 are the theorem's sharp cases
  (`L(5..8) = 2`, `L(9..26) = 3`), not a search artefact;
* n = 9 was never going to be beaten, and no amount of extra search power was going to show it —
  the MILP below could not, and did not need to;
* `desc(extr) = L2` in run 72 (the extrusion's rigidity) is a *local* statement; the theorem is the
  global one.

## 3. The 2D corollary, which is the interesting part

The same argument in two dimensions: **axis-parallel unit squares in a square satisfy
`L(n) = ⌈√n⌉` exactly.** Ninety-nine words, and it closes a question the project has been circling
for seventy runs from the other side: *if every square is axis-parallel, the grid cannot be beaten.*
So every one of the 553 beats in the delivered table must contain **at least one rotated square** —
not as a tendency, but as a necessity.

That is checkable on the table, and it holds exactly:

| claim | measurement |
|---|---|
| axis-aligned rows | **447** of 1000 |
| those not at `⌈√n⌉` (would falsify the theorem) | **0** |
| rows that beat the grid | **553** |
| beats containing zero rotated squares | **0** |
| 447 + 553 | **1000** — the two classes are exactly complementary |

So in the delivered table **containing a rotated square is equivalent to beating the grid**, on all
1000 rows. The score is not a packing-score at all in the density sense: it is a *rotation* score.
The angles say the same thing — among the 553 beats the populated words are π/2 (66,445 squares),
π/4 (11,731), −π/2 (952), then 0.715135 and −0.420631, with 0 appearing 3,899 times as the *unrotated
members of rotated rows*, never as a row.

Precisely what this does and does not prove: the 447 aligned rows are optimal **within the
axis-parallel class** (a different and weaker statement than the 152 rows proved optimal outright,
which remain the stronger claim). Nothing here says a rotated row is optimal, or that any particular
`L` cannot be improved — it says the only lever that has ever moved this score is an angle. The n =
5 row is the witness that the class restriction is real rather than pedantic: `2.707107` against
`⌈√5⌉ = 3`, one square at π/4.

**One correction to run 72's headline (added run 74).** "The extrusion of the delivered row" is a
cube state only when the row is axis-aligned; a square at π/4 is not a unit cube, and
`declp3.json` records `extrude_ok = False` at n = 5 and n = 10. At those two rows the `extr` column
(`2.7071`, `3.7071`) is the extent of a set of **overlapping** cubes, and `desc(extr) = L2` is not
rigidity — the trace shows the LP proposing `3.0` and `4.0` and the descent refusing, because the
starting state is not legal. So "3D strictly better" at n = 5 and n = 10 is true but vacuous (there
is no extruded packing to beat), and `35` §3's "the extrusion is rigid on every row" holds at the
other ten rows only. The values themselves are untouched: `L(5..8) = 2`, `L(9) = 3`.

## 4. The instrument that could not do it, and why that is worth recording

The natural way to settle n = 9 is a big-M disjunctive MILP over all `6^C(n,2)` declared structures
at once — exact in principle, no branch enumeration. It is implemented (`declp3.py --milp`) and it
works where the problem is small: **n = 4 and n = 5 close in ~9 s each**, both returning the grid
side and both *infeasible* at `t ≤ L − 1e−3`, i.e. grid-optimal to the stated margin.

At n = 9 it has 216 binaries and 36 tight equality constraints, and it did not close: the 60 s solver
budget expired and the 300 s command cap killed it outright. An LP-guided branch-and-bound of our own
(using `declp3.solve` per node) is the obvious remedy, and it is now **unnecessary for this problem** —
recorded so that nobody spends the afternoon on it. The lesson is the project's own: a solver's
silence is not a theorem, and a two-line counting argument beat both the LP and the MILP.

## 5. Code housekeeping (as asked)

> **Run 74: `--milp` is retired.** The disjunctive MILP described in §4 is redundant against §2's
> counting argument, never closed the row it was built for, and its relaxation is the same big-M
> construction that run 74 measured to be *empty* in two dimensions (root bound = the largest
> square's own extent; `37` §2). `_disjunction`, `milp_min_side`, `feasible_below`, `milp_report`
> and the `--milp` flag are removed from `declp3.py` (kept in `git show fd22941`). `--exhaustive`
> and `--selftest` are unchanged. The paragraph below is the run-73 record.

* **`--exhaustive` is now opt-in.** A default `python3 scripts/declp3.py` runs the 12-row table in
  seconds; the 46,656-branch `n = 4` enumeration (65 s of run 72's 71 s) only runs with
  `--exhaustive` (all rows) or `--exhaustive N [LIMIT]` (one row).
* **`--selftest` is an alias for `--control`**, so the instrument answers to the project's convention
  as well as its own name.
* `--milp N …` is the new disjunctive mode, with a 60 s per-instance budget and its own ledger
  (`workspace/push/declp3_milp.json`).

## 6. What this means for the project, and the way forward

Three things follow, and they are not opinions — they are the corollary in §3 plus the record.

1. **The search space that has been searched is the wrong one.** Runs 65–71 spent four runs closing
   branch-flip and free-set cells, and run 71's exhaustive refusal is now *explained*: on an aligned
   row no rearrangement of axis-parallel positions can ever gain, by theorem. The only cells that can
   pay are ones that change an **angle**.
2. **So the angle word is the object, not the position.** The project already has the vocabulary
   (`axis`, `p8 = √2−1`, `atan2`, `atan3`, `atan4`, plus the crams) and 1169 algebraic certificates.
   The theorem says a row moves iff its angle multiset changes, which makes the word algebra of `31`
   and `28` the right engine and the packer a verifier.
3. **The remaining honest targets**, in the order I would spend on them:
   (a) the 675 rows above n = 324 — a *source* problem, unchanged, and still the largest single block;
   (b) **multi-lattice seams at irrational offsets** (`22-DIAMOND-MASK.md`'s two lattices at 0.384808,
   `23-SEED-WHEELS.md`): a two-angle family is the only structure that can beat a single-word row
   without inventing a new word, and it is the one family the project censused but never closed;
   (c) a **2D branch-space MILP at frozen angles** — the same disjunction as in §4, one dimension
   down, which would *certify* a row optimal for its angle multiset instead of failing to improve it.
   This is the strongest available replacement for the flip searches, and §4 is the warning attached:
   at n = 18 it is 612 binaries, so it needs the LP-guided B&B, not a black-box solver.

What I would **not** do: build a 3D ladder. §2 says there is nothing there — the cube grid is optimal
in every dimension, for every n, by a nine-line proof. The project's ladder is 2D rotation, and its
rungs are angle words.

## 7. Re-running

```bash
cd source_material/ToDo/squares_in_squares
python3 scripts/declp3.py                 # 12 rows, seconds (no enumeration)
python3 scripts/declp3.py --selftest      # the same three controls as --control
python3 scripts/declp3.py --exhaustive    # the 46,656-branch n = 4 bound (65 s)
# --milp was retired in run 74 (see §5); its code is at git show fd22941
```

The table checks in §3:

```bash
python3 - <<'EOF'
import csv, math, sys; from collections import defaultdict
sys.path.insert(0, 'scripts'); from sqscore import extent
by = defaultdict(list)
for d in csv.DictReader(open('workspace/submission/submission.csv')):
    by[int(d['n'])].append((float(d['x']), float(d['y']), float(d['angle'])))
L = {n: extent(v) for n, v in by.items()}
al = {n: all(abs(s[2]) < 1e-12 for s in by[n]) for n in by}
beat = {n: L[n] < math.ceil(math.sqrt(n)) - 1e-9 for n in by}
print(sum(al.values()), sum(beat.values()),
      sum(1 for n in by if al[n] and abs(L[n]-math.ceil(math.sqrt(n))) > 1e-6),
      sum(1 for n in by if beat[n] and al[n]))
EOF
```
