# 13 — cent_discovery: never in git, reconstructed; and what that means for PL-32

## 1. The search result, stated first

`cent_discovery.py` **does not exist in this tree and never existed in the
repository's git history.** `git log --all -- '*cent_discovery*'` returns nothing;
grepping every commit's tree finds only *references* to it, in commits `db74f9e`
and `41489c7`, inside `REPRODUCE.md`, `boundary_demo.py`, `boundary_scan.py`,
`fine_probe.py`, `root_probe.py`, `run19_docs.py`, `soft_relax.py` and two JSON
ledgers. **There was nothing to restore.**

`hop_search` needs two more modules that are **also absent from tree and
history**: `engine_variants` (`finalize_gate`, `lattice_seed`, `transduce`) and
`oracle_basin` (`settle_to`, `ramp_settle`). The whole soft-relaxation engine was
broken, not one import.

## 2. What was done instead

Three modules rebuilt to the contract their call sites use, each marked
RECONSTRUCTION in its docstring:

* `scripts/cent_discovery.py` — `rsa_seed(n, L, rng)` (two-phase: honest RSA,
  then a jittered lattice that cannot overlap), `attempt(...)`, and a `__main__`
  running the control rediscovery the callers' docstrings prescribe.
* `scripts/oracle_basin.py` — `settle_to(q, L, iters)` (L-BFGS-B, ftol 1e-14, on
  the project's own `sa_push.total_pen`), `ramp_settle`.
* `scripts/engine_variants.py` — `finalize_gate` (thin wrapper over
  `packlib.verify`, so the gate stays the only authority), `lattice_seed`,
  `transduce`.

Import status of the eight affected scripts after the work:

| script | imports |
| --- | --- |
| `soft_relax.py` | **OK** |
| `boundary_demo.py` | **OK** |
| `boundary_scan.py` | **OK** |
| `p1p_insert31.py` | **OK** |
| `p2_seed_polish.py` | **OK** |
| `fine_probe.py` | still fails — missing `lm_exactify` |
| `root_probe.py` | still fails — missing `pressure_settle` |
| `lattice_scan.py` | still fails — missing `pressure_settle` |

Two further modules absent from the tree (`lm_exactify`, `pressure_settle`) are
outside what `hop_search` needs, so they are recorded, not reconstructed.

## 3. What validated, and what did not

| piece | evidence |
| --- | --- |
| `settle_to` | **validated**: from the delivered n=5 record it reaches E=0, gate ok, **L = 2.707107** — the documented control optimum |
| `rsa_seed` | **validated for feasibility**: seeds gate clean at n=5 (pen −8.3e-3) and n=11 (−1.4e-2); n=65/626 still overlap ~5e-2 (jitter plus tilt at cell ≈ 1.08) |
| `hop_search` | **NOT validated**: at n=5, target 2.7081, it returns 0/8 hard hops, where `soft_relax`'s own docstring records this as a control it passes |

Cause of the hop failure, measured: from a random seed `settle_to` plateaus at
E = 2.8e-2 and L-BFGS-B exits — 250, 1000 and 4000 iterations all return the same
state (L = 2.902716) — so the cold settle sticks in a local minimum and the SA
hops do not recover a hard state in the move budget.

Two of my own defects were found and fixed on the way, both measured: the SAT
projection radius used `hw` instead of the half-side 0.5 (up to 41%
over-conservative), and the seed fallback placed squares without checking the
ones already down (worst_pen 0.46 at n=5, 1.03 at n=65). Fixing them took seeds
from overlapping to clean at n=5 and n=11, but did not fix `hop_search`.

## 4. PL-32 with hop_search — not answered

The sweep over k = 8..25 was started and is **incomplete**:

| k | n | target slack | hard hops | result | time |
| ---: | ---: | ---: | ---: | --- | ---: |
| 8 | 65 | 0.5158 | 0/1 | no gated find | 78 s |
| 9 | 82 | 0.5158 | 0/1 | no gated find | 97 s |
| 10..25 | — | — | — | **skipped: time budget** | — |

At 2 hops × 6000 moves one seed costs 78–97 s, so 18 values of k do not fit in a
single pass here — and the engine is unvalidated anyway. **No base below 0.520815
was found, and the search is explicitly incomplete: this is not evidence about
the geometry.** Ledger: `workspace/push/pl32_hopsearch.json` (checkpointed per k,
so a resumed run appends rather than restarts).

## 5. area_ceiling.py is gone

`scripts/area_ceiling.py` is **deleted**. `scripts/leech_audit_fix.py` is now the
only scorer of that quantity and prints the same figures under the same guard:
base-less 0.806788 over 177 rows, open columns 6.388578 over 270 rows, total grid
ceiling 7.195366, beating-row headroom 15.022691. `11-AREA-CEILING.md` and
`12-GUARD-AND-PL32.md` now point at `leech_audit_fix.py`; their stale references
to the deleted file were retargeted rather than left dangling.

---

## 6. Vectorising the penalty, fixing the cold settle (run 50)

### Vectorisation: done, and verified identical

`sa_push.total_pen` used a Python loop of `n` calls to `pair_pen_k`, each of
which built its own boolean mask and recomputed `cos/sin` for the whole array --
O(n²) with ~n Python-level calls. It is now one matrix product:

```
P = pair_pen_matrix(X, Y, TH, HW)      # delegates to cram_relax.margin_matrix
total_pen = P.ravel().P.ravel() * weight + OUTW * out_pen.out_pen
```

Verification, not assertion: on a random n=40 state the pair part is
**48.360341919152** by the old loop and **48.360341919152** by the new one, equal
to all printed digits. `total_pen` at n=40 now costs **0.15 ms**.

Two of my own defects were caught by that check and fixed:

* a hand-rolled version of the matrix disagreed with the loop (48.36 vs 27.90);
  delegation to `cram_relax.margin_matrix` replaced it;
* switching to `np.triu_indices` silently halved the penalty, because the old
  loop summed over **ordered** pairs (k over all, j ≠ k). Kept the ordered scale.

Effect on the engine: `hop_search` at n=5 went from **67 s** (0/8 hard hops) to
**17 s** with hard hops appearing (**1/4**).

### The cold settle: better, still failing its control

`oracle_basin.settle_to` no longer uses L-BFGS-B on the Python penalty (which
exited at E = 2.8e-2 from every seed). It now runs the project's own vectorised
`cram_relax.relax` (single-body Gibbs on the exact per-body strain) followed by
`coordinate_polish`, reporting `cram_relax.energy`.

Measured on the control the engine's own docstring names:

| attempt | n=5, target 2.7081 | known 2.7071068 |
| --- | --- | --- |
| old settle (L-BFGS-B, Python penalty), 8 hops | 0/8 hard hops | fails |
| new settle, 8 hops × 20k moves | 1/4 hard, best **3.080452** | **still fails** |
| new settle + shrink-and-repair (6 rounds, 3 seeds) | L = 2.870-2.906, E ≈ 4e-2 | **still fails** |

Diagnosis: the optimum is the 4-around-1 arrangement with the centre square
rotated 45°. Single-body descent and SA at a fixed infeasible side cannot
*restructure* a random seed into it -- every body's own strain is lowered by
staying where it is. Passing the control needs a rotation-aware collective move
(a swap/rotate kick that moves several bodies at once) or a family seed; neither
exists in the reconstruction.

### Consequence: the k = 8..25 sweep is NOT run

The control still fails, so any numbers from a k = 8..25 sweep would be
uninterpretable -- which is the point you made, and it holds. Nothing is claimed
from this round about the geometry. What this round does establish is that the
penalty is now fast and provably unchanged, and that the remaining defect is in
the *move set* of the settle, not in its cost.
