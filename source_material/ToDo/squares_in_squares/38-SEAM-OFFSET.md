# 38 — W1 started: the multi-lattice seam, with the offset free (Run 75)

Instrument `scripts/seam_offset.py` (3 controls), ledger `workspace/push/seam_offset.json`.
Read-only: no row changed, no score claimed, `submission.csv` untouched.

Run 74 left a list (`WHITEBOARD.md`, "Squares in Squares"). Its W4 — the n = 11
near-miss — is spent in `37` §9 and is a dead end as a construction. This run
starts W1, the family the project censused (`22` §3, `23` §3) but never closed:
two 45° lattices meeting at an **irrational** offset. The question changes from
"what is the offset of this row" to "what does the offset cost".

## 1. What was declared, and what is solved

The atom is the n = 290 row, the only delivered row whose tilted part is not one
lattice. It is read as integers plus one free scalar:

| part | representation | status |
| --- | --- | --- |
| upright, 240 squares | wall anchor `(m, i)` per axis, coordinate `a + b·L` | exact, `seam_wheels.posfunc` |
| tilted, 2 × 25 squares | delivered centres, grouped into frames by the 45° residue | exact after one `Q(√2)` snap |
| frame B | translated by `s` along `(1,−1)/√2`, i.e. `(s/2, −s/2)` | **the free parameter** |
| side `L` | bisected, then snapped to `Q(√2)` | solved |

A frame is a *label*, not a reconstruction: nothing is re-fitted, and the exact
gate is asked about the state that results. Grouping uses the fact that two
tilted centres share a 45° lattice iff `2(x±y)/√2` have the same fractional part
mod 1. The `% 1` fold has to be a **circular distance**, not a one-sided test: a
residue that arrives as exactly `1 − 1e-9` survives `f > 1 − 1e-9` and splits one
frame into two, which is `23` §3's bug in a new place. It fired here first —
n = 226 came back as 20 + 5 sites — and control 1 is what caught it.

## 2. The measured offset, and a correction to `22`

The two frames differ **only along the seam**: `Δ(x+y) = 0` exactly, and

    Δ(x−y) = 18 − (25/2)·√2 = 0.322330472 …

with `18 − 12.5√2` recovered by `seam_wheels.snap` (height ≤ 220, no fitting). In
the rotated frame's own units — where adjacent diagonal rows are ½ apart — the
offset is `−25 + 18√2 = 0.455844`, i.e. **0.4558 of a lattice step**: an
algebraic fraction of the step, not a half-integer and not a grid point.

**`22` §3's number does not survive this measurement.** It reports the offset as
`0.2721·√2 = 0.384808`. What `0.2721` actually is, is the residue of `2(x−y)/√2`
for one frame; the frame's `(x−y)` grid residue is half of that, `0.192384`, and
`0.384808` is *twice the residue*, not the distance between the frames. The gap
to the true value is `0.384808 − 0.322330 = 0.062478`. Nothing in `22`/`23`
depends on the value — the two-frame split and its exact certificate (pen 0,
rebuild 1.7e-9) both stand, and this instrument reproduces the row with rebuild
error 0.0 — but the number attached to the offset is mis-scaled, and `23` §3
inherits it. Recorded here rather than edited there, because the certificate in
`23` is the part that was load-bearing.

## 3. The census: a shift costs exactly the shift

The declared set is `s = 0` and `s = j·√2/8`, `|j| ≤ 8` — 17 surd shifts, all
exact in `Q(√2)`, so a positive answer cannot be blamed on a float. For each `s`
the side is bracketed by bisection (nomination, `1e-9` tolerance = the CSV's own
pad), then the nominated state is snapped to `Q(√2)`, shifted exactly, and
replayed through `seam_wheels.exact_gate` (no floats). `n = 290`, delivered side
`17.535533908`:

| shift `s` | min side | vs delivered | certified |
| --- | ---: | ---: | --- |
| `0` | 17.535533906 | −1.9e−9 (the pad) | yes |
| `±√2/8` | 17.712310600 | **+1.767767e−1** | yes |
| `±2√2/8` | 17.889087295 | **+3.535534e−1** | yes |
| `±3√2/8` … `±8·√2/8` | — | — | **inadmissible** |

Two facts, both exact:

* **the penalty is the shift, one for one** — `+1.767767e−1` against the nominal
  `√2/8 = 0.176776695`, and `+3.535534e−1` against `2√2/8 = 0.353553391`; the
  remaining 4e−9 is the finalizer's pad, paid twice. The seam has no slack in this direction:
  sliding one lattice by `s` forces the side up by `s`, because the other lattice
  and the wall-anchored fill cannot absorb it.
* **past `2√2/8` the atom does not pack at all** inside `L0 + 4` (the walk-up
  bound), in either direction. The offset is not a knob with a wide admissible
  range; it is a narrow pocket around a determined value.

**0 certified gains.** So at the one row where the project has a genuine
multi-lattice atom, the irrational offset is *determined*, and the family's first
degree of freedom is priced at 1:1. The seam is tight — which is the honest
opposite of the hope that a surd offset is a hidden free parameter.

## 4. What this does and does not close

It closes the *offset* question at n = 290, and it prices the direction that
would have been cheap to try. It does **not** close W1, and the reason is
structural rather than a matter of more compute: this atom's frame count, block
sizes and fill are all inherited from a delivered row, so the census can only
say what shifting *that* arrangement costs. The family question — can a
multi-lattice seam be *built* with a smaller seam constant than the single-lattice
`0.535534` / `0.520815` of `21` — needs a builder that chooses the two blocks and
the fill at a target count, i.e. the `23` wheel with the seam left free. That is
W2-adjacent work (a word and an arrangement generated, not verified), and this
run does not start it.

What the measurement does supply is a constraint for that builder: at the one
atom of this kind in the table, the seam is *at* its optimum and pays 1:1 for a
shift, so a multi-lattice construction cannot buy its gain by sliding one lattice
against another. Any gain has to come from the block sizes, the masks, or the
fill — not from the offset.

## 5. Controls

1. **Degradation, one frame** — n = 226 groups to `[25]`, one frame, and its
   bracketed side is `15.535533906` against the delivered `15.535533908`
   (−1.5e−9, the finalizer's pad). This is also the check that the split is not
   simply always returning two frames.
2. **Degradation, two frames** — n = 290 at `s = 0` rebuilds the delivered atom
   with error **0.0**, and lands on `17.535533906` (−1.5e−9).
3. **The gate is the judge** — the delivered n = 290 atom gates at
   `17.535533908`; a copy with one square moved 25% toward another is refused
   with penetration `0.250000`.

Two instrument defects were found by these controls and by nothing in the printed
census, and both are recorded because they are the kind that produce a *false
gain*:

* `packlib.finalize` cannot be the bisection predicate. It **scales** the state
  (by up to `3e-5` on its later tries), so "finalize succeeds" means "feasible at
  a side above the one being asked about" — measured as a phantom `2.4e−6` gain
  on control 1. The predicate is now a float gate at `1e-9` and is labelled
  nomination-only; the exact gate is the judge.
* snapping the *shifted* coordinate fails outright (`13.886485388` has no
  `Q(√2)` snap of height ≤ 220 once `√2/8` is added). The base is snapped once
  and the shift added exactly, which is both correct and faster (`census` 23 s).

## 6. Re-running

```bash
cd source_material/ToDo/squares_in_squares
python3 scripts/seam_offset.py --selftest    # 3 controls (~2 s)
python3 scripts/seam_offset.py               # the 17-shift census (~23 s)
```

Ledger: `workspace/push/seam_offset.json` — every shift with its bracket, its
certified side, and its nudge.
