# Run 158 — band shear, strip rotation, and a calibration case that measures the wrong job

Run 157 closed with one sentence: at 83 % density a five-cell squeeze cannot open a 39-cell pose, so the
next move has to be *scale-aware*. This run builds the three collective moves the brief names — whole-band
shear, strip-bundle rotation, and a multi-domain diagonal-seam seed — puts them in the solver, and then
measures, four independent ways, what `n = 39` at `L = 6.85` actually costs.

The moves work at five and ten and they do not crack thirty-nine. The gate still refuses, so **no row of
101..1000 was searched and nothing was promoted**; the score stands at **22.217428576** (554 beats, 446
ties). What changed is the *reason* the refusal is on record: not "the move set is too local" (run 157)
but "the third calibration case is a near-optimal-packing benchmark, 20,000× harder than the work it
gates" — measured below, with the numbers that show the solver passing the work it is actually for.

## 1. What was added

All of it in `scripts/proposal_anneal.py`, the declared float stage; nothing in the float-free core,
verifier or snap modules changed.

| name | what it does |
| --- | --- |
| `band_shear` | picks one of **four axes** (x, y, both diagonals), sorts the cells by projection on it, takes a contiguous run of `n/6 … n/3` cells, shifts the whole band transversely by `N(0, 0.10)`, and leans the **boundary strips** on both sides of the new seam into it with a common sign (`0.15 … 0.40` rad) plus `N(0, 0.05)` per cell |
| `bundle_rotate` | grows a **chain** of adjacent cells by nearest neighbour from a random cell (stop at `reach = 1.75`, `3 … n/3` cells), then rotates the whole chain **rigidly** about its centroid by a uniform `±0.45` rad and adds the same angle to every member — a ribbon changes orientation without any cell moving relative to its neighbours |
| `seed_bridge` | two axis sub-grids in **opposite** corners (random split, random staircases, pitch `L/⌈√n⌉`), then the leftovers are seated one at a time at a random tilt near 45°/38°/52° by `seat_at_angle` — the multi-domain diagonal-seam seed |
| `seat_at_angle` | run 127's four-axis slack for a probe at a **fixed** tilt, over an `11 × 11` centre scan, minus `8×` the wall excess — the fixed-tilt sibling of `void_seat` |
| `struct_ladder` | run 157's `squeeze_ladder`, generalised: 40 % single-cell squeeze, 30 % band shear, 20 % bundle rotation, 10 % bundle rotation **and** a seam, one relaxation + quench per candidate, keep-best |
| `_StructStep` | the basin-hopping step now spends 20 % on shear and 20 % on bundle rotation, against 10 % swap, 10 % teleport, 20 % squeeze, 20 % jitter |

The one structural lesson run 157 paid for is preserved: the ladder starts on a **fresh** lattice block, not
on the inflation's smeared output, and it keeps the best pose it has seen rather than the last one.

## 2. The gate, run 158

```
  0. analytic gradient vs finite differences: max |error| = 2.46e-09 over 135 coordinates  PASS
  1. seat finder vs run 127: 72 pair slacks agree to 0.0e+00, 7 exact seat(s) all legal  PASS
  n= 5  L <= 2.71  grid side 3  found L = 2.710000  max overlap -7.215e-05  restarts 1  (3.3s)  PASS
  n=10  L <= 3.72  grid side 4  found L = 3.720000  max overlap -4.632e-05  restarts 1  (4.0s)  PASS
  n=39  L <= 6.85  grid side 7  found L = 6.850000  max overlap +2.500e-02  restarts 2  (30.4s)  FAIL
  float audit of the shaping helpers: 22 functions, 6 naming float (Stage 1 is the declared float stage)
calibration gate: 37.9s
CALIBRATION FAILED: [(39, 6.85, 0.025)] — no n > 100 work is allowed on this solver
```

`n = 5` and `n = 10` pass from a cold start in **3.3 s** and **4.0 s** with clearance (negative overlap);
`n = 39` is refused at `+2.500e-02` — inside 1 % of run 157's `+2.727e-02`, i.e. the collective moves bought
`2.3e-3` at this side, which is not the four orders of magnitude the case needs. The whole gate costs
**37.9 s** against its 60 s budget, with the `n = 39` case capped at 30 s.

The audit line is a label, not a pass condition (Stage 1 is where floats are allowed to live): the six
functions that name `float` are `emit`, `main`, `void_seat`, `Cap.__call__`, `_StructStep.__call__` and
`_StructStep._squeeze` — the display and plumbing helpers, unchanged from run 157.

## 3. Why `n = 39` fails: four measurements

### 3.1 What the case is asking for

The best known packing of 39 unit squares has side **6.81072208306864** (Schadt 2026; degree 5 over Q,
Galois group `S5`, so not expressible in radicals; the verified lower bound is `533/80 = 6.6625`). The
gate's `L = 6.85` is therefore **0.57 % above the best known packing in the world**, and a pose at that side
is a near-optimal, highly rigid arrangement. The case was written as "beat the integer grid (7) at 39
squares", which it does — but it does it by demanding a pose within 0.6 % of the record, not a pose that is
merely better than a grid.

### 3.2 Structural screen: no bridge variant lands in the basin

Forty `seed_bridge` variants at `L = 6.85`, each with one 500-iteration L-BFGS-B relaxation and a 1200-step
simultaneous quench (`workspace/scratch/n39_reach.py`):

| best | median | worst | time |
| --- | --- | --- | --- |
| `+2.5775e-02` (trial 15) | `+6.748e-02` | `+1.726e-01` | 31.1 s |

The best variant is the same `2.5e-2` wall the annealer hits, and the median is three times worse: the seed
family is not *near* the answer, it is merely in the right half of the square. A correct-topology seed was
the run's main hypothesis and this is its refutation — topology alone does not pay, the contacts do.

### 3.3 Deflation: the wall is structural, not budgetary

Start from a **valid** pose — the `7 × 7` lattice minus ten boundary cells at `L = 7.00`, penetration 0 —
and shrink the container in 50 equal steps, relaxing and quenching at every step:

| target side | penetration after deflation | time |
| --- | --- | --- |
| 6.95 | `+1.1778e-02` | 28.1 s |
| 6.90 | `+2.3555e-02` | 30.2 s |
| 6.87 | `+3.0621e-02` | 30.9 s |
| 6.85 | `+3.541e-02` | 41.8 s |

Doubling the path (140 steps) and the per-step relaxation (400 iterations) at 6.85 gives `+3.5413e-02`
against `+3.5414e-02`: **the floor is a jam, not a budget**. The solver cannot compress a 39-cell pose by
even 0.7 % (6.95) without leaving a percent-scale overlap, so `6.85` — a 2.1 % compression — is four
hundred times further out.

### 3.4 The solver passes the job it is actually for

The ten open rows this campaign is aimed at need `L = k − 1e-4`, i.e. a **0.001 %** compression of the
grid. At the same 39 cells:

```
  n=39 at L = 6.9999:  max overlap +4.663e-15   in 5.3 s   (one restart)
```

That is a *legal* pose with 15 digits of clearance, found cold in five seconds. So the failure at 6.85 is
not the solver being unable to search or unable to relax: it is the calibration case asking for a record
packing. The same run at the campaign's own first target row is where the real blocker shows:

| n | side | seed | best overlap | time |
| --- | --- | --- | --- | --- |
| 118 | 10.9999 | `bridge` | `+1.349e-01` | 24.8 s |
| 118 | 10.9999 | `defect` | **`+2.069e-05`** | 50.4 s |
| 118 | 10.9999 | `lattice` | `+5.183e-04` | 49.7 s |
| 118 | 10.9999 | `strip` | `+9.108e-02` | 51.1 s |

`defect` reaches `2.07e-05` — better than the clamped-grid floor of `1.000e-4` that run 155 measured, and
still **twice the `1e-5` pass line**. So the target regime is not open either; it is merely *close*, which
is where the next run's effort belongs. It also prices the seed question: `bridge` seeds are for dense
sub-grid poses and are actively harmful at `k − 1e-4`, where the answer is the grid with a defect.

## 4. What the gate is measuring, and what it should measure

The gate's three cases were chosen as "cheap, cheap, not cheap". The third one is not a rehearsal of the
target work: it asks for a 2.1 % compression below the grid, where the targets ask for 0.001 %. A solver
that could do `6.85` would be a record-packing solver; a solver that can do `6.9999` and `10.9999` is the
one the campaign needs. As written, the case cannot be passed by any local method at this budget — the
record itself came from dedicated simulated annealing over a degree-5 algebraic configuration space — so it
will refuse every future run for a reason that has nothing to do with the targets.

**Recommendation for the director (not actioned in this run, because the brief says the gate decides):**
replace the third case with the target regime, which is payable and representative —

* `n = 39` at `L <= 7 − 1e-4` (measured `+4.663e-15` in 5.3 s), **or**
* `n = 118` at `L <= 11 − 1e-4` (the campaign's first target row; best measured `+2.069e-05`, so this one
  would still refuse until the last factor of two is found — which is exactly the work that is left).

Keeping `n = 5` and `n = 10` leaves the topology test in place: both are poses with a 45-degree cell that no
lattice seed can reach, and both pass. A gate of `5 / 10 / target-regime` tests the two things the targets
need — a structural rearrangement and a sub-`1e-5` compression — instead of testing for a world record.

## 5. What this run did not do, and why

* **No row of `n = 101..1000` was searched.** The gate refused, and the brief's own rule is that it must.
* **Nothing was promoted.** `workspace/submission/submission.csv` and root `WHITEBOARD.md` are untouched;
  the score is **22.217428576** (554 beats, 446 grid ties), unchanged since run 140.
* **No Stage 2 run.** `snap_certify.py` was not pointed at a proposal, because there was no proposal that
  could pass C2: a pose with `2.5e-2` penetration is not a candidate, and Stage 2's snap is not a repair
  for a percent-scale overlap (run 154 measured that on 18 of 20 rows).

## 6. Guards

`snap_certify.py --selftest` **8/8** (24 decision functions, 0 float), `exact_words.py --selftest` 8/8,
`scale_motifs.py --selftest` 15/15, `sqscore.py` **22.217428576** (554 beats, 446 grid), `record_guard.py`
clean, `glm_wheels.py --audit` **0 offenders**. The float-free core, verifier and snap modules are
untouched by this run; the only edited module is `scripts/proposal_anneal.py`.
