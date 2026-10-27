# Round 15: can we supply what a proof needs? And leads from aperiodic tilings

**Where the prize stands.** All three Rule 30 problems are still open. This round does two things:

1. It takes Round 14's list of what a proof would need and asks, for each item, whether we can
   supply it.
2. It takes what is useful from the attached tiling research, recorded with its citation in
   `TILE_RESEARCH_NOTES.md`.

The Lean work is `RequestProject/GLM/Rule30/TileLeads.lean`, imported by the package root
`RequestProject/GLM/Rule30.lean`. It is described in rows C163–C169 of `claims.csv` and in the
"Round 15" section of the package README. Everything builds with no `sorry` and no added axioms.

Labels: `FORMAL` = Lean proof; `EMP` = computed outside Lean, not a theorem; `OPEN` = not settled.

---

## 1. "What a proof would take": can we provide it?

| Round 14 requirement | Can we supply it? | What this round adds |
|---|---|---|
| **P1, first link:** the centre column does not eventually alternate (period 2). Needs "a quantity that alternation would cap but that the seed's evolution drives up without bound". | **Partly.** The quantity is still missing. The problem it must solve is now much smaller. | **Period-2 forcing lemma** (`FORMAL`). An alternating column forces its left side, and everything on the left is determined by **one half-speed sequence** `u` (column `c - 2`). |
| **P1, all periods:** one argument uniform in `p`. | No. | `key_forcing` (`FORMAL`) gives the part valid for every period: at each black time of a periodic column, the cell to its left is fixed. |
| **P1, other routes:** turn the proved "two adjacent columns are never both periodic" into a one-column statement. | A valid bridge, but the data do not support its hypothesis. | **Recognizability bridge** (`FORMAL`): if a neighbour column can be read from a finite window of the centre column, P1 follows. Measured (`EMP`): about 0.3 bits stay uncertain. |
| **P2:** a balance theorem for the seed. | No. | Nothing new. Tiling theory has no frequency tools. |
| **P3:** a lower bound for every algorithm. | No. | Nothing new. |

### 1a. The period-2 forcing lemma (`FORMAL`)

Suppose column `c` alternates `1010…` from time `N` (`AltFrom x c N`). This works for **any**
starting row, not only the seed. Then:

* `alt_forces_left_one`: whenever column `c` is black, column `c - 1` is black.
* `alt_pair_constant`: column `c - 2` holds each value for two steps (`u(k)` at times `2k` and
  `2k + 1`).
* `alt_shift_complement`: column `c - 3` is the complement of column `c - 2` one step later.
* `alt_left_determined`: from time `N + 1`, **every cell at or left of column `c` is determined by
  the phase and the single sequence `u`**.

In Round 14 the period-2 case had three unknown columns. Now it has one unknown sequence with one
free bit per two steps. The open statement becomes:

> **No half-speed sequence `u` generates a left-white world.** Solving Rule 30 leftwards from the
> columns forced by `u` must eventually contradict "white beyond a moving black edge".

This is the form in which a "capped quantity" argument should be sought. For the seed, the edge
is at distance `t` at time `t`, and cell `(t, -j)` is a fixed Boolean function of `u` on roughly
`[t/2, (t+j)/2]`.

**What we tried and could not close.** We looked for a second level of forcing, which would
make the structure self-similar like a tiling hierarchy. Column `c - 4` is already a *nonlinear*
function of `u` (`r15_alt_reduction_output.txt`), so the clean recursion stops at `c - 3`.

### 1b. The recognizability bridge (`FORMAL` + `EMP`)

`problem1_of_neighbour_recognizable` says the following. Suppose that from some time on, column
`+1` or `-1` of the seed's run equals `F(c(t), …, c(t + k − 1))`, for some fixed rule `F` and a
fixed delay. Then the centre column is not eventually periodic. The reason is that a periodic
centre column would then make an adjacent pair periodic, which is already proved impossible.

Test (`r15_recognizability.c`, 4,194,304 steps, with a delayed-column control to estimate bias):

| window (centre bits) | 1 | 3 | 5 | 7 | 9 | 11 | 13 | 15 |
|---|---|---|---|---|---|---|---|---|
| uncertainty of column −1 (bits) | 1.00 | 0.41 | 0.37 | 0.34 | 0.33 | 0.31 | 0.31 | 0.30 |
| uncertainty of column +1 (bits) | 1.00 | 0.81 | 0.75 | 0.68 | 0.66 | 0.62 | 0.61 | 0.59 |

Larger windows are not reliable at this sample size. Part of the drop is explained by
`key_forcing`: column −1 is fixed at the centre's black times. The rest decreases only slowly,
so the data give no support to exact recognizability. This is an observation, not a theorem.

### 1c. Rigidity of the whole diagram (`FORMAL`)

* `seed_spacetime_period_trivial`: no non-trivial space-time shift maps the seed's diagram to
  itself, even from some time on.
* `seed_no_mirror_symmetry`: no shift combined with a reflection does either.

Both come from the two edges of the light cone. They show that **the whole diagram is rigid, and
Problem 1 asks for the rigidity of one projection of it**. The gap between these two statements
is exactly what makes the problem hard.

---

## 2. The tiling research: what we took

See `TILE_RESEARCH_NOTES.md` for the citation and a full table. In short:

* We took four ideas: periods of the whole collection, the "finite linear image" argument for
  symmetries, boundary keys with local forcing, and the marked→unmarked (recognizability) bridge.
  Each became a Lean theorem above.
* We did not take any results. The attached Lean file depends on a module that was not supplied,
  and the manuscript reports its own final verification as pending. Nothing here depends on it.
* The PDFs and the `.lean.txt` file are not part of the package and can be removed from the
  workspace. The citation is kept in the notes.
* The decisive tool of tiling proofs, a forced self-similar hierarchy, has no known Rule 30
  counterpart. The period-2 forcing lemma is the closest we found.

## What the GLM should say

* "P1, period 2: an alternating column leaves one half-speed free sequence `u`. The open question
  is whether some `u` is compatible with a white left edge."
* "A neighbour column readable from a finite window of the centre column would prove P1. The data
  do not support this."
* "The seed's whole diagram has no symmetry. The problem is the symmetry of one column."

## Files

| File | Purpose |
|---|---|
| `TILE_RESEARCH_NOTES.md` | what was taken from the tiling research, with citation |
| `r15_columns.c` | bit-packed Rule 30 from one black cell; writes columns −1, 0, +1 (`./r15_columns 4194304 > big.bin`, about 1 minute) |
| `r15_recognizability.c`, `r15_recognizability_output.txt` | uncertainty of the neighbour columns given centre-column windows (reads `big.bin`) |
| `r15_alt_reduction.py`, `r15_alt_reduction_output.txt` | illustration of the period-2 forcing: columns left of an alternating column built from a random `u` |
