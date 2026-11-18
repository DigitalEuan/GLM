# Write-offs — routes we have paid for and will not pay for again

A write-off here is a **measured** negative with its ledger attached, not an
opinion. An entry is retired only if the evidence behind it is re-read and the
verdict is false; the register is rebuilt from the ledgers by
`python3 scripts/motif_wheels.py --writeoffs`, which re-reads the campaign and
recomputes the counts rather than trusting this page.

Register (machine-readable): `workspace/push/writeoffs.json`.

---

## W-01 — compiled physics-analogy search moves as packing attacks

**Verdict: written off (0 finds in the entire campaign).**

**What was built.** `scripts/cent_engines.py` (Run 6) compiled four cent
isomorphisms into four search engines on one shared, exact substrate (the same
vectorised SAT penalty `packlib.verify` certifies with):

| engine | compiled law | move |
|---|---|---|
| P-04 flywheel | `omega = (2E/I)^(1/2)` | rotate a contact cluster as one rigid body |
| P-05 optical PLL | `lambda = c/f` | phase-lock each tilt to a reference set |
| P-11 piezo | `stress = E * strain` | Hookean push proportional to penetration |
| P-12 Griffith | `K = sigma * sqrt(pi a)` | open a random crack plane, then relax |

**What it cost and returned.** 236 campaign cells completed — P-04 60,
P-05 60, P-11 58, P-12 58 — across the small-n head `{6, 12, 13, 20, 21, 22,
30..33}` and the roomy mid-band set, at two depths (grid − 0.002 and
grid − 0.02). **Finds: 0.** `cent_campaign.json["finds"] == []` and
`cent_findings.json == []`.

**Why it is closed.** A move cannot add an arrangement the geometry does not
have. Every one of these engines re-arranges an existing configuration; none of
them changes *which* configurations are expressible. The score in this problem
is set by base geometry, and the two escapes that have actually been measured
are geometric, not analogous to a physical law:

- at n = 5, 300 single-body 45-degree rotation kicks from the E = 0.034082
  attractor produced **0** feasible states, while re-slotting the most strained
  bodies into the widest free gap produced **25/150** (see
  `oracle_basin.collective_kick`);
- the r = 1 column rows are locally rigid: pushed 0.02 below their side, the
  settle returns L bit-identical (8.535533908), so no amount of polishing
  finds a new row.

The only constructive route with measured score is the motif one: the exact
band step (`M-cascade`), Friedman's L-extension (`M-l-extension`), and the
n = 5 cross (`M-cross-grid`, Göbel 1979).

**Reopens only if** a new engine is shown, on a gated control, to reach a side
that no local settle reaches — i.e. its control cell passes `packlib` at a side
the current engines cannot reach, and that is demonstrated before any campaign
run.

**Pointers.** `workspace/push/cent_campaign.json`,
`workspace/push/cent_findings.json`, `scripts/cent_engines.py`,
`scripts/motif_wheels.py` (the replacement: declared motif families, one gate,
one scorer).

---

## Measured, not yet registered

These are negative results from the motif work that are not formal write-offs
because they are properties of a *move*, not of a whole route — but they should
be read before paying for the same idea again:

- **Rigid-row compression.** Pushing an r = 1 row below its side returns L
  bit-identical; the row is jammed, so "better settle" is not a source of
  score. (`workspace/push/pl32_sweep.json`.)
- **Pure in-place rotation kicks.** 0/300 from the n = 5 attractor; the kick
  needs a re-slot component to escape the 3-in-a-line trap.
- **Uniform re-slot inside a dense packing.** Destroys the state and the Gibbs
  settle cannot repair it; the re-slot radius is now scaled to 1.2 mean body
  spacings for that reason (`oracle_basin.collective_kick`).

## Register schema

```json
{"schema": "cent-writeoff-register/1",
 "written": "YYYY-MM-DD HH:MM:SS",
 "entries": [{"id": "W-01", "route": "...", "source": "...",
              "evidence": "236 campaign cells, 0 finds",
              "cells": 236, "per_engine": {"p04_flywheel": 60, "...": 0},
              "finds": 0, "verdict": "written off",
              "reason": "...", "do_not_retry_unless": "...",
              "pointers": ["..."]}]}
```
