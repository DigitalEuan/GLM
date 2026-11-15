# 05-MECHANICS.md — the clear picture (Run 37, 2026-11-08)

*What is actually happening inside this system, measured on the
delivered frontier (Run 36/37: score 22.642386651, 543/1000 beat grid).
Companion measurements live in `workspace/push/layer_settle37.json`,
`exact_replay37.json`, `leech_map.json` (run 37 refresh) and the
regenerated exact chain (`leech_core` 28/28, `octad_moves` 14/14,
280 Galois certificates).*

---

## 1. The one-sentence picture

The system is a **provenance pipeline, not a solver**: every row of
the table is an *imported or derived exact-rational object* that
passes a float64 SAT gate on entry, is stored at 12 decimals, and —
for 133 of the 217 import rows and by construction for 581 more —
**replays exactly in `Fraction` arithmetic**; the tower of perception
layers (Substrate → Integer → Rational → Scan → Certificate) is what
keeps that statement lawful, and the Golay/Leech substrate is the
verified logic layer at its base. The score is the sanity check; the
mechanics is the deliverable.

## 2. Where the 1000 rows actually settle (the run-37 census)

Measured by **provenance** — what exact material exists locally for
each row — not by fitting the stored floats (the run-5-era field-fit
census degenerates on today's table; see §5):

| settle class | rows | improvement share | what it means |
|---|---:|---:|---|
| **cert-rational** | 674 | 1.1380 (18.1%) | an exact rational side exists locally: grid 457 (integer side, lattice states), mishapolk 207, register 10 |
| **design-quadratic** | 134 | 2.825 (44.9%) | exact design side from a construction family: gobel2/gobelS/gobel3 54 (Q(√2) at 45°), survey exact 77 + aux 3 |
| **derived** | 124 | 1.447 (23.0%) | exact arithmetic on a parent: chain3 88 (L = L(parent) + integer), closure/removal 36 (envelope minima) |
| **float-only** | 68 | 0.886 (14.1%) | run18-frontier: 12-dp optimize states, no exact material anywhere |

Facts that follow (all script-computed, this run):

- **The import frontier is exactly rational.** All 217 import rows
  (mishapolk 207 + register 10) carry exact rational *sides* from
  their sources (`verified.bound` / cert headers); 133 of them also
  have their full **geometry** as local exact certificates, and all
  133 replay in pure `Fraction` with **0 failures**
  (`exact_replay37.py`; pairwise SAT on both squares' edge normals,
  container fit, corner touch allowed).
- The 84 remaining mishapolk rows are *side-only* (exact rational
  bound; finalize-float geometry) — the honest exactness boundary of
  the import frontier.
- The stored-vs-exact drift over the 133 replayed rows is
  1.83e-9 … 1.35e-8: precisely the finalize clearance (the deliberate
  +2e-9 scale before the 12-dp round). Nothing else drifts.
- **chain3 inheritance is exact integer arithmetic**: L(334) =
  L(299) + 1 + 2e-9, L(371) = L(334) + 1.000000000 — the whole 88-row
  chain3 class inherits the exactness of its single T-263 parent
  (an exact rational), so "derived" is not a weaker class; it is the
  same exactness propagated.

## 3. The angle vocabulary in the t-basis (where the layer tower is
   sharpest)

Every import certificate is written in the **t-basis**: rotation as
t = tan(θ/2) with (c, s) = ((1−t²)/(1+t²), 2t/(1+t²)) — so the
*geometry* is rational whenever t is rational, regardless of θ being
transcendental. Measured over the 133 verified geometries:

- **all 133 packings contain axis-aligned squares** (t = 0 present);
- 31 hit the 45° bucket — and the exact t of the largest signature
  (20 rows) is the rational **225058681/543339720 = √2 − 1 + O(1e-10)**:
  the import frontier's "45°" rows are *rational near-45°* angles.
  The 12-dp storage layer and the 1e-9 SAT gate both read them as
  exactly 45°; the `Fraction` replay sees the truth (a rational
  tilt, ~1e-10 off the classic construction angle);
- 22 hit the arctan(1/2) bucket (26.565°, the 2:1 rational-slope
  family); the rest are scattered rational angles — the records are
  hand-polished, not family constructions (consistent with run 31's
  asymmetry census: every record class is asymmetric).

This is the concrete answer to "where can ill-defined mechanics blur
the perspective — literally": **the blur lives between the Scan layer
(12-dp) and the exact t-basis**, and it is bounded at ~1e-10 for the
45° family and 1.35e-8 for sides. Both are far below every decision
threshold in the pipeline (1e-7 import gain, 1e-9 SAT margin), which
is why the layers stay lawful.

## 4. The exact environment: what is float-free, and where the lossy
   operations live

**Float-free by construction (verified this run):**

| component | arithmetic | check |
|---|---|---|
| Golay code + Leech lattice (leech_core) | bitmasks, big integers | 28/28 assertions |
| octad calculus (octad_moves) | integers | 14/14 assertions |
| import certificates (sides) | `Fraction` | 217/217 exact rationals |
| import geometries (133 replayed) | `Fraction` | 133/133 verified, 0 failures |
| grid rows | integer side + lattice states | by construction (5 spot-checked) |
| construction design sides | exact formulae (Q(√2) family, Q(√7) survey forms) | galois_certs: 280 certificates, 9 value-matched on the live table |
| chain3 / closure / removal | exact arithmetic on parents | envelope laws (root_audit: monotone 999/999, shell 937/937) |

**The three lossy operations, named and bounded:**

1. **The SAT gate** (packlib.verify) is float64 with a declared 1e-9
   margin. It is the *entry gate*, not the record: for the 133
   geometry-bearing imports the same rows now also pass the `Fraction`
   replay, so the gate's yes/no is backed by exact arithmetic wherever
   exact material exists. (The 84 side-only rows and 68 float-only
   rows rely on the gate alone — recorded as the boundary, §2.)
2. **The finalize clearance** (+2e-9 scale, then 12-dp round) is
   *deliberate*: it guarantees the rounded state never overlaps. Its
   measured effect is the 1.83e-9…1.35e-8 drift (§2) — three orders
   below the 1e-7 import-gain threshold, so it cannot churn the table
   (the MIN_GAIN rule).
3. **The 12-dp storage** is the Scan layer of the tower: it is what
   the field-fit censuses see, and it is why the run-5-era tier
   mapping degenerates on today's table (§5). The exact material
   behind it is local and re-derivable — the tower's whole point.

## 5. The 24D-lattice question, answered honestly

The verified part (integer-exact, this run and before):

- The Golay/Leech substrate's **logic** is real and closed: Steiner
  ladder 253/77/21/5/1, octad calculus 30/448/280, distance-8 graph
  759-regular of diameter 3, covering radius exactly 4 — and the
  **projection law**: every coordinate projection of Λ24 is the same
  lattice (checkerboard + diagonal), with the only defect locus
  *exactly* the 759 octads.
- The **perception-layer tower** (01-LAYERS.md) is formalized and its
  boundary theorems hold: Substrate is blind to 0-vs-2, Integer sees
  it but is blind to 0-vs-½, Rational sees both, Scan (12-dp) is
  blind below 2.5e-13.

The empirical part, re-measured this run — and this is the correction
the current frontier forces:

- The run-5-era mapping (container value → number field → Λ-window)
  reported 87% coverage and Spearman(level, improvement) = +0.79,
  with Q(√2) carrying 70% of the improvement. **That was a property
  of the construction-era table** (score 23.17, 407/1000). On the
  current frontier, `leech_map.py` gives: coverage 70.7% *fits*, but
  the strict noise floor is 879/1000 random values — and the level
  series is **constant** (991/1000 at level 0 under the certified
  standard), so both Spearman correlations are **UNDEFINED**. The
  instrument now says so instead of crashing (run-37 patch).
- What actually happened is instructive: the frontier changed *class*
  — from constructions (Q(√2) at 45°, the Λ8 window) to **imports**
  (exact rationals in the t-basis) — and the tower, correctly read by
  provenance (§2), shows it. The 45° signature itself persists inside
  the imports as the rational √2−1 + O(1e-10) (§3): the same
  geometry, now carried exactly.
- So the honest statement of the "big clue": **the lattice does not
  predict the score anymore; it enforces the language the packings
  are written in.** Every object the system trusts is either an exact
  rational (t-basis), an exact quadratic surd (45° family), or exact
  arithmetic on one of those — and the Golay/Leech layer is the
  verified rule system that keeps the lower layers (parity, integers)
  from blurring the upper ones (exactness). The projection law's
  defect-locus-is-the-octads result remains the deepest structural
  fact in the repository; no isomorphism between Λ24 and the packing
  problem is claimed, and none is needed for the exact environment to
  hold.

## 6. What this buys (the score as sanity check)

- Score unchanged this run: **22.642386651** (543/1000; gap 0.587965).
  The mechanics run made no table change — by design: its products are
  the census, the replays, and the corrected instruments.
- The exact-replay result (133/133) is now the strongest certification
  statement available for the import frontier: stronger than the SAT
  gate (it is `Fraction`-exact), weaker than Lean (no proof script) —
  recorded in `02-EXACT-VERIFICATION.md`'s tradition, at the run-36/37
  frontier.
- Standing follow-ups: (a) 84 side-only mishapolk rows — geometry
  certs worth requesting upstream; (b) 68 float-only rows — the only
  class with no exact material (the natural target for any future
  *construction* push, as opposed to imports); (c) re-run
  `exact_snap.py` (~40 min) if a whole-table certificate-field census
  is wanted — not run this turn.

## 7. Reproduction (REPRODUCE.md §A27 carries the commands)

```bash
python3 scripts/leech_core.py        # 28/28
python3 scripts/octad_moves.py       # 14/14
python3 scripts/galois_certs.py      # 280 certificates
python3 scripts/level_audit.py       # staged field fits (table-only note)
python3 scripts/leech_map.py         # tower map + UNDEFINED Spearman
python3 scripts/layer_settle37.py    # the provenance census
python3 scripts/exact_replay37.py    # the Fraction replays (133/133)
```
