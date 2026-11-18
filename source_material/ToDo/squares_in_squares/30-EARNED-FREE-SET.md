# 30 — The §11.5 probe with an earned free set: no k changes the answer (run 67)

The run-65 refusal in `29` Part A was **built in**: the free set was "the k squares
that touch walls", chosen so the frozen remainder still spanned the side. This run
chooses the free set the way the geometry does and raises k until the core stops
spanning, so the refusal is earned.

**Headline:** the core does stop spanning — at k = 161, 184, 267, 298 for the four
rows — and the LP then **still refuses at every one of those k, and at every larger
ring, up to and including k = n.** There is no smallest k that changes the answer,
because none does. At k = n the refusal is the strongest form available: the
delivered side is the **exact optimum** of the declared-axis, fixed-orientation LP.

---

## 1. Why the old free set was circular

`19` §11.5 frees k squares and asks for a certificate. If the k are chosen by wall
contact, the remaining n−k still reach both walls, so the side cannot drop for a
reason that has nothing to do with the neighbourhood: the *definition* of the free
set guarantees the refusal. `29` Part A reported that as a finding ("the walls pin
the packing"). It was a tautology dressed as a measurement.

## 2. The earned rule

`scripts/extreme_probe.py` (ledger `extremeprobe/1`):

1. **Seeds** — the squares that actually achieve the four extremes at the delivered
   state: `argmin(x−h)`, `argmax(x+h)`, `argmin(y−h)`, `argmax(y+h)` (2–4 distinct,
   since one square often holds two).
2. **Growth** — adjoin the tight-pair partners (pen ≤ 1e−9) of every free square,
   one ring at a time. Freeing a square means freeing what it *pushes on*.
3. **Gate** — at each ring compute the frozen core's span; the core blocks if
   `max(span_x, span_y) ≥ L − 1e−6`.
4. **Price** — at every ring where the core does not block, solve the declared-axis
   LP at `L − ε`, ε ∈ {1e−6, 1e−4, 1e−2}, then certify with `packlib.verify` and
   score with the canonical scorer.

## 3. Result — the rings, and where the core stops spanning

| n | L₀ | seed k | rings (k) | k where core stops spanning | core span there | feasible cells |
| --: | --: | --: | --- | --: | --- | --: |
| 294 | 17.656854 | 3 | 3, 12, 27, 46, 63, 78, 89, 102, 119, 138, **161**, 186, 209, 228, 239, 258, 273, 284, 291, 294 | **161** (55%) | 16.9602 / 16.9602 | **0** |
| 295 | 17.704233 | 3 | 3, 12, 27, 47, 71, 93, 120, 150, **184**, 213, 242, 262, 274 | **184** (62%) | 17.0445 / 11.8995 | **0** |
| 299 | 17.801004 | 4 | 4, 10, 16, 22, 31, 44, 63, 85, 109, 135, 162, 192, 222, 238, 253, 261, 265, 267 | **267** (89%) | 15.7923 / 14.8008 | **0** |
| 298 | 17.778175 | 2 | 2, 8, 18, 32, 50, 68, 92, 122, 156, 194, 230, 254, 272, 286, 296, **298** | **298** (100%) | 0 / 0 | **0** |

Two things are measured here, and the second is the answer to the question asked:

* **The core is global, not local.** Reaching the point where a shrink is even
  *arithmetically* possible needs **55–100%** of the squares free. The extreme
  achievers and their tight partners occupy a *spanning chain*: each ring adds
  squares the walls need, and the chain runs across the whole cell. There is no k
  small enough to be a search neighbourhood and large enough to permit a shrink.
* **Even then the answer does not change.** At every priced ring — every ring from
  the first unspanning one to k = n — the LP is infeasible at all three ε. **0
  feasible cells, 0 gains, for every k.**

n = 298 is the sharpest instance: the core keeps spanning until *every single
square is free*, and only then is the LP attempted — and it refuses at ε = 1e−6.

## 4. What k = n certifies

With all translations free, θ frozen and each pair pinned to the axis that separated
it at the delivered state, `L₀ − 1e−6` is infeasible and `L₀` is feasible (the
delivered state is a witness). So:

> **The delivered side is the exact optimum of the declared-axis, fixed-orientation
> LP.** No rearrangement of positions at fixed angles can improve any of these four
> rows by even 1e−6.

That is a real certificate, of exactly the scope `lp_seam` has for a single seam
extended to all n squares simultaneously. Its limit is the same: *within the
declared axis assignment and the delivered orientations*. A pair that changes which
axis separates it, or a square that rotates, is outside the declaration and is not
covered. `L4`–`L6` and the `disj_census` (0.76% of pairs tight, ≥2 branches each)
say how far outside: the branch space, not a residual neighbourhood.

## 5. Errata — the LP was wrong twice before it was right

This run's first answers were **invalid**, and so was `29` Part A's LP reasoning.
Three defects in `sat_probe.solve_lp`, each caught by a different check:

| defect | how it showed | fix |
| --- | --- | --- |
| global translation written into pair rows (run 65) | every cell infeasible for one reason | global cancels; dropped |
| pair rows had `i`/`j` coefficients in the wrong order, and were appended as `≤` when the condition is `≥` | delivered state infeasible **at its own L₀** | signs from `t = (c_j−c_i)·q`, rows negated |
| required separation used `h_i + h_j` (each square's own half-extent) | infeasible at L₀ with 76 violated pairs, e.g. `|t₀| = 1.000` vs required 1.414 | correct constant is `0.5 + Eu[owner, other]`, exactly as `packlib` |

The check that catches all of them is now permanent and cheap:

    python3 scripts/sat_probe.py --selftest      # 6/6

It asserts the mandatory invariant — **the delivered state is feasible at its own
side**, for a small free set and for the full free set, at n = 10, 83, 294. Any LP
that fails this is not measuring the packing. This should have existed before run
65; it is the one thing in this whole line that a five-line test would have saved.

**What survives from run 65:** the 18 cells refused for `rigid core spans`, which is
computed *outside* the LP, so those refusals are still true — but they are the
tautology of §1, not a statement about neighbourhoods. The LP-based reading of that
refusal is withdrawn and superseded by this record.

## 6. Scope

* **Establishes:** for n ∈ {294, 295, 298, 299}, no fixed-axis, fixed-orientation
  translation of any subset — including all — lowers the side. The strongest is
  k = n at ε = 1e−6.
* **Does not establish:** that these rows cannot be improved at all. That needs the
  branch space (which pair is tight on which axis) and/or rotation, which is the
  same wall every other instrument has hit: `L4` (elementary moves close), `L5`
  (rotation is elementary), `L6` (assignment is the asymmetry), `L1` (E ≡ 0, so
  nothing ranks the branches).
* **Not claimed:** anything about rows other than these four. The run is bounded by
  construction, and four rows is what it priced.

---

# Files

* `scripts/extreme_probe.py` — earned free set: extremes → tight rings → gate → LP → verify.
* `scripts/sat_probe.py` — `solve_lp` rebuilt (three defects fixed), `--selftest` added;
  the builder is now `declp.solve` (consolidation after run 70), so `solve_lp` is its
  signature-only shim.
* `workspace/push/extreme_probe.json` — every ring, with core spans and priced cells.
* `workspace/push/sat_probe.json` — run 65's cells, now annotated by the fixed LP's scope.
* supersedes the LP reasoning of `29` Part A; `19` §11.5 points here.
