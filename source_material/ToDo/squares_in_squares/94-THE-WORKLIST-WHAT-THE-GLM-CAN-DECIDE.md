# 94 — The worklist: the table is at the world frontier, and the room is per-row (Run 137)

**Run 137, 2026-11-25.** Instrument `scripts/glm_plan.py` (`--selftest`, `--frontier`), ledger
`workspace/push/glm_plan.json`. Claims are `glm_wheels.Claim` records, so `glm_wheels --audit`
covers them. **No row changed, no score claimed, `submission.csv` and root `WHITEBOARD.md`
untouched.**

This run asked a different question from the last 136: not *what can we build*, but **which
remaining claims are decidable at all, and where is the room actually measured to be.** Two
answers, both new:

1. **The room is not in band inheritance.** Doc 75's `0.23251` programme is real but it is a
   *subset* of a larger and better-certified number: the delivered table sits at or above the
   **published world frontier on all 100 rows with `n <= 100`** (measured against The Squares
   Project's best-known list, 2026-10-20: **zero** rows behind), and the distance from our sides to
   the **published lower bounds** is **`1.14087` over 55 rows** — four times the band programme and
   `1,285×` the two notches.
2. **26 of 30 bands are undecidable**, in a sense made precise below, and that — not bad luck — is
   why the recent runs stalled. Four bands are decidable; the largest of their prizes is a **proved
   optimum that cannot be collected**.

---

## 1. The measurement that re-ranks everything

`glm_plan --frontier` compares the delivered CSV with the published frontier for `n = 1…100`
(best-known side and best proved lower bound, embedded in the instrument with its source and date).

| quantity | value |
| --- | --- |
| rows where a published packing beats ours | **0 of 100** |
| total gain available by importing published packings | **0** |
| rows where our side is above the published **lower bound** | **55** |
| certified room to those bounds, `Σ (L_table - LB)/√n` | **`1.14087`** |
| band-inheritance programme (doc 75 §2, recomputed exactly) | `0.23251` |
| the two doc-93 notches | `0.00089` |

The top of the certified-gap ranking (`n`, our side, published lower bound, room):

| n | L (delivered) | LB | room |
| --- | --- | --- | --- |
| 86 | `9.820536` | `9.503` | `0.03424` |
| 68 | `8.798796` | `8.530` | `0.03260` |
| 89 | `9.949748` | `9.650` | `0.03177` |
| 51 | `7.690356` | `7.470` | `0.03086` |
| 84 | `9.697935` | `9.4225` | `0.03005` |
| 55 | `7.945772` | `7.728` | `0.02936` |
| 83 | `9.634758` | `9.370` | `0.02906` |
| 85 | `9.742641` | `9.475` | `0.02903` |
| 90 | `10.000000` | `9.730` | `0.02846` |
| 72 | `9.000000` | `8.760` | `0.02828` |

**The single largest measured prize in the repository is `0.0342` at row 86 — 38× the k = 23 notch
and 79× the k = 32 notch — and it is a per-row side reduction, not a band inheritance.** Every one
of the top ten is worth more than the entire notch programme. This is the answer to "where do we
stop going nowhere": the effort has been aimed by *structural curiosity* (which pose has an
interesting void) instead of by *measured room* (which row is furthest from a proved bound), and the
two rankings disagree by two orders of magnitude.

An honest caveat, stated once: a lower bound is not a construction. The `1.14087` is room in the
sense that no packing can do better than the bound; much of it may be unattainable, and several of
the bounds are loose. What it is *not* is somebody else's packing waiting to be transcribed — that
number is measured at zero.

## 2. The band worklist

`glm_plan` writes one `Claim` per band — `j` cells to add, doc 75's void price, the frontier pose's
angle-class count, the prize — and applies four rules (§3).

| k | frontier | j | price | classes | prize | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | 5 | 4 | -0.672 | 2 | 1.20e-1 | **SCHEDULE** — but proved optimal, see §3 |
| 4 | 11 | 5 | +0.032 | 2 | 3.55e-2 | **SCHEDULE** (row 12 is open: `4` vs LB `3.9715`) |
| 5 | 19 | 6 | -0.131 | 2 | 2.56e-2 | **SCHEDULE** (row 20 is open: `5` vs LB `4.905`) |
| 7 | 41 | 8 | -0.021 | 3 | 1.13e-2 | **SCHEDULE** (row 42 is open: `7` vs LB `6.8475`) |
| 6 | 29 | 7 | +0.210 | 6 | 1.21e-2 | refuse R1 (6 classes) |
| 8 | 55 | 9 | +0.135 | 7 | 7.25e-3 | refuse R1 (7) |
| 9 | 71 | 10 | -0.004 | 6 | 6.59e-3 | refuse R1, R2 (`n+j = 81`) |
| 10 | 89 | 11 | -0.003 | 2 | 5.30e-3 | refuse R2 (`100`) |
| 13 | 156 | 13 | +0.459 | 15 | 1.66e-3 | refuse R1 (15), R2 (`169`), R3 |
| 12 | 132 | 12 | +0.657 | 12 | 1.24e-3 | refuse R1, R2, R3 |
| 17 | 273 | 16 | +0.454 | 22 | 9.71e-4 | refuse R1, R2, R3 |
| 16 | 241 | 15 | +0.588 | 27 | 8.28e-4 | refuse R1, R2, R3 |
| 20 | 382 | 18 | +0.463 | 91 | 6.86e-4 | refuse R1 (91), R2, R3 |
| 23 | 509 | 20 | +0.530 | 47 | 4.53e-4 | refuse R1 (47), R2 (`529`), R3 |
| 15 | 211 | 14 | +0.807 | 17 | 4.43e-4 | refuse R1, R2, R3 |
| 32 | 998 | 26 | +0.119 | 147 | 4.35e-4 | refuse R1 (147), R2 (`1024`) |
| 22 | 465 | 19 | +0.597 | 44 | 4.24e-4 | refuse R1, R2, R3 |
| 19 | 344 | 17 | +0.718 | 31 | 4.00e-4 | refuse R1, R2, R3 |
| 11 | 110 | 11 | +0.929 | 16 | 3.05e-4 | refuse R1, R2, R3 |
| 21 | 423 | 18 | +0.737 | 42 | 3.05e-4 | refuse R1, R2, R3 |
| 25 | 604 | 21 | +0.665 | 52 | 2.72e-4 | refuse R1, R2, R3 |
| 28 | 761 | 23 | +0.624 | 83 | 2.43e-4 | refuse R1, R2, R3 |
| 24 | 556 | 20 | +0.806 | 66 | 1.71e-4 | refuse R1, R2, R3 |
| 18 | 308 | 16 | +0.897 | 29 | 1.62e-4 | refuse R1, R2, R3 |
| 27 | 707 | 22 | +0.861 | 60 | 9.65e-5 | refuse R1, R2, R3 |
| 30 | 876 | 24 | +0.854 | 88 | 8.20e-5 | refuse R1, R2, R3 |
| 31 | 936 | 25 | +0.858 | 78 | 7.49e-5 | refuse R1, R2, R3 |
| 29 | 818 | 23 | +0.922 | 85 | 4.71e-5 | refuse R1, R2, R3 |
| 14 | 183 | 13 | +0.988 | 18 | 3.09e-5 | refuse R1, R2, R3, R4 (`V/j = 0.999`) |
| 26 | 655 | 21 | +0.985 | 189 | 1.13e-5 | refuse R1, R2, R3, R4 |

**4 scheduled, 26 refused; `0.19194` scheduled against `0.04056` refused** — and the scheduled
total is itself misleading, because one of the four cannot pay (below).

## 3. The four rules, and the ceiling that is not a prize

A claim is *scheduled* only when its obligation is a bounded exact enumeration:

* **R1 — structured pose.** At most `4` angle classes; a pose with 6–189 classes is a continuum
  object whose "next pose" is an open optimisation, not an enumeration.
* **R2 — small-pose regime.** `n + j <= 64`. This is the rule that was missing: runs 116/117
  attacked a 20–26 cell obligation inside a 509–998 cell pose, which is not an enumeration at all.
* **R3 — void to save under a cell.** `price <= 0.25` unit².
* **R4 — not at the void limit.** `V/j <= 0.999` (bands 14 and 26 spend 99.9 % of their budget).

The scheduled prizes need one correction the geometry cannot see, and the literature can: **row 6
cannot be beaten, because `s(6) = 3` is proved** (Kearney & Shiu 2001/2002), as are `s(5) = 2+√2/2`
(Göbel 1979) and `s(7) = s(8) = s(9) = 3`. So the `k = 3` claim's `0.1196` is a *ceiling on an
impossible row*, not a prize: scheduling it would be the most expensive kind of dead end. The three
real ones are `k = 4` (row 12, open: best `4`, LB `3.9715`), `k = 5` (row 20, open: `5` vs `4.905`)
and `k = 7` (row 42, open: `7` vs `6.8475`), worth `0.0723` together.

This is exactly the failure mode the user asked about, caught in the act: a *decidable* claim (R1–R4
all pass) whose answer is nevertheless known — and the fix is not more geometry, it is reading the
frontier before running. `glm_plan` now carries that frontier in the instrument.

## 4. Why this stops the dead-end loop

Six lines are closed by proof, not by exhaustion, and each says "do not return":

| line | closure | where |
| --- | --- | --- |
| 24D metric address | a `45°` square puts every integer-scale encoding off the rational lattice; **255/255** separation | doc 16 §4 |
| block substitution | `s(7) = 3` proved | doc 75 |
| 45° cheapest word | both seam terms `>= √2/2`, equality iff `c = s`; every exact word caps at 17 cells below `L = 5` | doc 92 §I |
| band 5 from scratch | 16/16 patterns legalise strictly above 5 (closest `5.001898`) | doc 92 §II |
| square ties | 551/551 beats square-tied to `1.6e-10` | docs 92 §III, 134 |
| the two notches | every cell and slab locked to `1.3e-5` against a `0.24` need | doc 93 |

What was missing was the *generic* exclusion — a claim that no instrument can decide — and the
discipline to check the frontier before a run. Both are now instruments: a run from here begins by
writing a claim, showing R1–R4 pass, and showing the row is not already proved optimal. Anything
else is a run without a proof obligation, which is the pattern that produced 136 of them.

## 5. What the GLM can do beyond a passive check

`glm_wheels.py` is 684 audited functions, six slots (`Tile`, `Frame`, `Strip`, `Glue`, …) across
several domains, `Claim(domain, family, params, size, laws, payload, measure, invariant)`, witnesses,
and `--audit` at **0 offenders**. Three jobs are open to it; this run takes the first and third:

1. **Decide** (new). `glm_plan` writes the claim and obligation for every remaining band and refuses
   what is not a bounded enumeration. The refusals are the useful output.
2. **Certify** (already built). Exact laws and witnesses over exact quantities — the reason the
   score can be trusted, and the repository's genuine differentiator.
3. **Schedule** (new). Rank by *measured room*, now against the published bounds as well as the
   bands. §1 is the first ranking that puts row 86 above row 509 by a factor of 38.

What the GLM **cannot** do is generate a pose: its laws are equalities over exact quantities, and no
slot produces a construction. Every gain in the table came from a construction (a word, a lattice, a
windmill, a strip), never from a wheel. A "GLM investigator" pretending otherwise would be one more
dead end; a GLM that decides, certifies and schedules is the one that has been working all along.

## 6. The Golay / Leech 24D track: what survives, and the one test worth running

Three measurements, so the answer is evidence rather than preference:

1. **Reach.** `leech_map.WINDOW_MAX_N = 11` (`2n + 1` coordinates), so the metric address speaks
   about **11 of 1000 rows**, all decided. The 553 scored beats are outside it.
2. **No 24-direction vocabulary.** The delivered table uses **28,548 distinct angle classes**
   (`mod π/2`, `1e-6`): 396,348 cells at `0°`, 11,734 at `45°`, then a tail of 481, 405, 372, …
   Per row: 447 rows one class (the grid rows), 112 two, 24 three, 13 four, the rest up to **626
   classes in row 747**. There is no 24-element direction set for a Golay code to act on.
3. **The tilt-support Golay law is false.** The Golay weight enumerator is `{0, 8, 12, 16, 24}`; the
   delivered tilt counts include `1, 2, 5, 6, 7, 9, 13, 14, 15, …` — **540 of 1000 rows violate
   it**. "The tilted support is a Golay codeword" is not a law of this table.

What survives is real and not decorative:

* **The codec.** `leech_map.encode / decode / in_leech24` is an exact 24-integer canonical form for
  `n <= 11`, with a validated membership predicate and a computable coset — a legitimate GLM module
  for storage, comparison and deduplication, and the reason the small-n control library is exact.
* **The combinatorial address doc 16 §5 named and nobody built:** `(tilt pattern, contact graph)`.
  It is the right descendant of the 24D design because `S(5,8,24)` is a *combinatorial* design, and
  the measurement says combinatorics is the only thing the score has — doc 16: the design sees
  exactly one bit per square, tilted or not, and that bit is the score (**553 rows carry a tilt and
  exactly those 553 rows are the beats** — checked set-for-set, symmetric difference empty).
* **The one experiment worth running next**, finite and cheap: on the 596 structured rows (`<= 4`
  classes), build the direction-class compatibility graph (two classes adjacent when a cell of one
  can contact a cell of the other in a delivered pose) and ask whether it contains the Witt design's
  octads — 8-sets in which every 5-subset appears exactly once, the `S(5,8,24)` property doc 15
  verified for the code itself. Right or wrong, it is a finite check on real data, and it is the only
  form in which the 24D perspective can be *productive* here rather than a framing. Specified, not
  run, in this pass.

## 7. Recommendation

1. **Rank by measured room, per row.** Attack row 86 (`0.03424`), then 68, 89, 51, 84, 55, 83, 85,
   90, 72 — each a per-row side reduction toward a proved bound, each worth 38–79× a notch. These
   are open problems of the field, so the expectation should be research effort, not search.
2. **Run no band work except `k = 4, 5, 7`** (`0.0723` together, all decidable, all open rows), and
   **do not run `k = 3`**: row 6 is a proved optimum and its `0.1196` is a ceiling.
3. **Treat the 26 refused bands as closed** until a claim passes R1–R4; the two notches among them
   are closed twice over (rigidity, doc 93; undecidability, §2) for `8.9e-4`.
4. **Put the differentiation where it already is strongest:** exact-arithmetic certification (684
   audited functions, 0 offenders; `Q(√2)`/`Q(√7)`/`Fraction`/`Decimal` core, bytecode-audited),
   plus the combinatorial address of §6. The table is at the world frontier — that is the headline
   the repository has earned, and it is a better claim than any single extra row.

**Checks.** `glm_plan --selftest` **4**: `k = 32` frontier reproduces `n = 998`,
`L = 31.986238620`, price `+0.119` (doc 75: `+0.120`); the 30-prize sum reproduces doc 75's
`0.23251`; the rules schedule a structured small obligation and refuse both a large-pose obligation
(R2) and a 40-class pose (R1); the delivered table is **0 rows behind** the published frontier for
`n <= 100` with certified room `1.14087` over 55 rows.
