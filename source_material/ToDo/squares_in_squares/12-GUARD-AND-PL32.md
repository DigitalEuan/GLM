# 12 — The scorer guard, and PL-32 (no base found)

Instruments: `scripts/sqscore.py` (the one scorer), `scripts/pl32_base.py`
(search + cascade carrier). Ledgers: `workspace/push/pl32.json`,
`workspace/push/pl32_carry.json`.

---

## 1. The guard

`scripts/sqscore.py` is now the only scorer in the project's instruments:

```
extent(state)  = max over axes of (max_i(x_i+ex_i) - min_i(x_i-ex_i))   [per square]
grid(n)        = ceil(sqrt(n))   exact, via isqrt
row_score(n,L) = L/sqrt(n) - 1
row_gain(n,L)  = (grid(n) - L)/sqrt(n)
marginal(n)    = 1/sqrt(n)
```

`guard()` recomputes `workspace/submission/submission.csv` and **raises** unless
the result is exactly **22.218056945 with 553 beats over 1000 rows (447 grid)**.
It is an assertion, not a warning: a script that calls it cannot print a score on
a wrong scale or against a mis-classified target.

Every affected instrument imports it and calls it at start-up:

| script | calls `SQ.guard()` | uses `SQ.extent` / `SQ.is_beat` |
| --- | --- | --- |
| `leech_address.py` | yes | yes |
| `leech_measure.py` | yes | yes |
| `leech_prior.py` | yes | yes |
| `leech_snap_controls.py` | yes | yes |
| `leech_rotation_control.py` | yes | yes |
| ~~`area_ceiling.py`~~ | **deleted** — folded into `leech_audit_fix.py` | — |
| `cascade_predict.py` | yes | yes |
| `leech_audit_fix.py` | yes | delegates to `SQ` |

A grep across those files for the old private computations (`ex = 0.5`,
`max(ex)`, `10 / dsqrt`, `10.0 / L`, `math.ceil(math.sqrt(n)) - 1e-12`)
returns **nothing**.

### Re-run once, all agreeing

| script | result under the guard |
| --- | --- |
| `leech_address.py` | guard OK; MI(address; beats) **0.5856 bits**, H(beats) 0.992, null 0.0466 |
| `leech_measure.py` | guard OK; AUC(gap→beats) **0.9861** |
| `leech_prior.py` | guard OK; per-column AUC median **1.000** over 37 columns |
| `leech_rotation_control.py` | guard OK; AUC(rotation→beats) **1.0000**, MI(rot; beats) **0.9919**, MI(gap; beats \| rotation) **0.0000** |
| `leech_snap_controls.py` | guard OK; I(gap; beats \| residue) 0.5740, z = +47.50 |
| `leech_audit_fix.py` (absorbs area_ceiling) | guard OK; **score 22.218056945, 553 beating, 447 grid**; ceiling base-less 0.806788 / open 6.388578 |
| `cascade_predict.py` | guard OK; reads the stale `table.json`: 22.645990613, 543 beats (expected — it scores a different file) |
| `leech_audit_fix.py` | guard OK; reproduces the delivered table to 1.3e-10 |

Note on `auc(gap → beats)` restricted to rotated rows: it is **undefined**, not
zero — all 553 rotated rows beat grid, so there is no negative class left. The
earlier `nan` was the same fact.

---

## 2. PL-32 — no base found

Target: a packing of `n = k²+1` with slack below the column's best **0.520815**
(attained at k = 25..31; k = 8..24 sit at 0.535534; k = 2 at 0.707107).

Two search paths, both gated with `packlib`:

* **`cram_relax.relax` + `coordinate_polish` from the delivered state** — returns
  the state **unchanged**. For every k tried (8, 10, 12, 16, 20, 25) the gated L
  equals the delivered L to six decimals (k=8: 8.535534 in, 8.535534 out, target
  8.5155). The delivered packings are **fixed points** of the project's own
  descend-to-fixed-point relaxation: it cannot tighten anything.
* **`sa_push.anneal` from compressed grid seeds** — 2 seeds, 20k–75k moves per
  target: every resulting state **fails the gate** (overlaps at the target side).

Two tooling facts found on the way, both recorded rather than worked around:

* `cram_relax.project` was removed from the chain — its own docstring records it
  as *measured to hurt* ("greedy SAT pushes … raised E 8.3e-4 → 2.4e-3").
* `soft_relax.hop_search` **cannot be imported at all**: it needs
  `cent_discovery`, which is imported by `boundary_demo.py`, `boundary_scan.py`
  and `fine_probe.py` but **does not exist in this tree**.

**Result: no base below 0.520815 was found. Nothing is claimed.** This is a
failed search with the available tooling, not a proof that the column cannot be
tightened.

---

## 3. The carrier, validated

The band step must work whether or not a better base is found, so it was run from
every existing base and **each band gated by `packlib`**:

| base | slack | bands carried | gate failures | rows improved | score change |
| --- | ---: | ---: | ---: | ---: | ---: |
| n=5 (k=2) | 0.707107 | 29 | **0** | 0 | +0.000000000 |
| n=65 (k=8) | 0.535534 | 23 | **0** | 0 | +0.000000000 |
| n=626 (k=25) | 0.520815 | 6 | **0** | 1 | −0.000000000 (1e-9) |

Geometry: from a packing of `k²+1` squares in `[0, k+δ]²`, add the `k+1` squares
`(i+½, top+½)` and the `k` squares `(top+½, j+½)`, `top = k+δ`, giving
`(k+1)²+1` squares in a box of side `k+1+δ`.

Two defects were found and fixed while building it, both **measured**:

1. the delivered states are **not corner-anchored**, so the first strips cut the
   old packing and the gate rejected every band from n=5 and n=65 — the state is
   now translated to (0,0) before banding;
2. successive bands **touch the previous strip exactly**, which `packlib` rejects
   at `tol=0` — the gap now accumulates 1e-9 off the real top of the state.

**Measured score change from carrying every existing base to the end of its
column: 0.000000000.**

That is the correct answer, not a disappointment: the delivered packings are at
or below the slack of their own bases. A chain from n=5 would give `k+0.707107`
(worse than the table's 0.5355 above k=8), and a chain from n=626 reproduces the
table exactly. **The table is not chain-limited — it beats its own chains.**

---

## 4. What PL-32 would need

A base below 0.520815 needs a **construction** this tree does not have, not more
search plumbing: the relaxer is a fixed point of the current packings, the
annealer cannot reach the target, and `hop_search` is unavailable because its
module is missing. The honest options are to restore `cent_discovery` from the
commit that had it, or to write the r=1 family construction directly.
