# 95 — Proved-optimal refusal, the verified bounds table, and the octad test (Run 138)

**Run 138, 2026-11-25.** Instruments `scripts/pub_bounds_check.py` (new),
`scripts/witt_octad.py` (new), `scripts/glm_plan.py` (extended with rule **R5**);
ledgers `workspace/push/pub_bounds_check.json`, `workspace/push/witt_octad.json`,
`workspace/push/glm_plan.json`; the saved source of record
`workspace/push/pub_frontier_20261020.html`.
**No row changed, no score claimed, `submission.csv` and root `WHITEBOARD.md` untouched.**

Doc 94 left three things as prose or hand-work: it *noted* in text that row 6 is a proved
optimum, it *quoted* a room computed from a hand-transcribed bounds table, and it *specified* an
octad test it did not run. This run turns all three into instruments, and every one of them
changed a number.

---

## 1. R5 — proved-optimal refusal, in the engine

`glm_plan.decide` now has a fifth rule. **R5 (proved-optimal target):** if the claim's row `n + 1`
is marked *proved optimal* in the published frontier, refuse — because no search is needed either
way: if the proved optimum is at or above the frontier side the claim is **impossible**, and if it
is below, a packing attaining it **already exists**. The set is not a literal any more: it is read
from the source's `aria-label="optimal"` badges by `pub_bounds_check.py` (49 rows in `1..100`).

| band | target | verdict |
| --- | --- | --- |
| `k = 3` | row 6, `s(6) = 3` proved (Kearney–Shiu) | **refuse R5** — "target row 6 is proved optimal (s = 3.0)" |
| `k = 4` | row 12, `4` vs LB `3.9716` | schedule — **world-record claim** |
| `k = 5` | row 20, `5` vs LB `4.9125` | schedule — **world-record claim** |
| `k = 7` | row 42, `7` vs LB `6.8475` | schedule — **world-record claim** |
| other 26 | — | refused R1–R4 (doc 94 §2) |

**3 scheduled / 27 refused; scheduled prize `0.07237`** (it was 4 and `0.19194` in doc 94, because
`k = 3`'s `0.1196` was a ceiling). Every scheduled claim now carries
`requires_world_record: true`: the frontier side at `k = 4, 5, 7` is below the published best-known
side of its target row, so collecting any of them is a new world record, not a fit. That is a
feasibility statement about those three, and it is the honest one.

`glm_plan --selftest` **control 5** asserts exactly this: band `k = 3` is refused with an `R5`
reason, it is absent from `scheduled`, the scheduled list is `[4, 5, 7]`, and all three are flagged
world-record claims.

## 2. The bounds table, machine-checked: 17 diffs, room `1.14087` → `1.09647`

**Method.** `pub_bounds_check.py` re-reads the same project's machine-readable frontier table
(`https://jlevy.github.io/squares/frontier.html`, saved verbatim with its fetch date), parses every
`n = 1..324` row out of the HTML (`data-value` attributes), and diffs it against `glm_plan.PUB` in
`Decimal` at tolerance `5e-5`. It is not a second opinion: it is the same source, read by machine
instead of by eye. Its own selftest plants a false lower bound at `n = 12` and requires the diff to
be caught.

**Result: 17 of 200 numbers were wrong — and one of them matters in a way nobody expected.**

| n | field | transcribed (PDF text) | source (live table) | delta |
| --- | --- | --- | --- | --- |
| 12 | lb | 3.9715 | 3.9716 | -0.0001 |
| 19 | lb | 4.825 | 4.8275 | -0.0025 |
| 20 | lb | 4.905 | 4.9125 | -0.0075 |
| 26 | lb | 5.545 | 5.555 | -0.010 |
| 27 | lb | 5.6435 | 5.655 | -0.0115 |
| 28 | lb | 5.735 | 5.7425 | -0.0075 |
| 29 | lb | 5.81 | 5.82 | -0.010 |
| 30 | lb | 5.8835 | 5.8925 | -0.0090 |
| 31 | lb | 5.9525 | 5.9775 | -0.0250 |
| 37 | lb | 6.44 | 6.4975 | -0.0575 |
| 39 | lb | 6.65 | 6.6625 | -0.0125 |
| 44 | lb | 6.9725 | 7 | -0.0275 |
| 76 | lb | 8.965 | 9 | -0.0350 |
| 94 | lb | 9.95 | 9.972 | -0.0220 |
| 95 | lb | 9.965 | 10 | -0.0350 |
| 96 | lb | 9.97 | 10 | -0.0300 |
| **90** | **ub** | **10** | **9.9940387665828706** | **+0.00596** |

Two different failures, both worth recording:

* **Sixteen are lower bounds I took from the PDF's rounded rendering** (`≥ 4.905` where the table
  holds `4.9125`). Every one makes the true room *smaller* than the figure I quoted. The verified
  room is **`1.09647` over 51 rows**, not `1.14087` over 55 — a 4 % overstatement, and the 55→51
  drop is four rows (44, 76, 95, 96) whose bounds are now *equal to their upper bounds*, i.e. they
  have since been proved optimal.
* **One is an upper bound where the world moved**: the live table has a packing at
  `s(90) ≤ 9.9940387665828706` (jazivxt 2026) where the PDF still said `10`. Our row 90 is
  `10.0000000019`, so **we are behind by `5.96e-3` of side at row 90, worth `6.28e-4` of score** —
  the first and only row in `1..100` where a published packing beats the delivered table.

The ranking that doc 94 derived is unchanged by the correction (86, 68, 89, 51, 84, 55, 83, 85 stay
the top eight, and `n = 86` is still `0.03424`), which is the reassuring part: the *conclusion* was
robust to the transcription even though the *number* was not. The proved-optimal set grew from 45
(PDF) to 49 (live): rows 44, 76, 95, 96 have been proved optimal since the PDF was drawn, which is
also why four room rows disappeared.

## 3. The octad test — FAIL, structurally, and it found something better

**The tester first.** `witt_octad.py` builds the design it is looking for out of the Golay code
(`leech24_design.golay_words`, the 759 weight-8 words) and requires: every 5-subset of 24 in
**exactly one** octad (`42504 = C(24,5)`, multiplicities all 1). It then deletes one octad and
requires coverage to drop by exactly `C(8,5) = 56`. It also checks an injected `K8` is found as
exactly one 8-clique. A test that cannot fail is worthless, so these were run before the data.

**Then the data.** The vocabulary is the 79 direction classes used by the 596 structured rows
(`<= 4` classes, i.e. the rows with an exact word vocabulary rather than jitter). Three graphs,
one canonical 24-point set each (the 24 most frequent classes), `WINDOW = 256` cells:

| graph | \|V\| | \|E\| | clique number ω | 8-cliques in top-24 | 5-subset multiplicities |
| --- | --- | --- | --- | --- | --- |
| exact contact (`\|sep\| <= 1e-9`) | 64 | **0** | **1** | 0 | 0/42504 |
| near contact (`tau = 0.02`) | 64 | 13 | 3 | 0 | 0/42504 |
| co-occurrence (structured rows) | 79 | 138 | 4 | 0 | 0/42504 |
| co-occurrence, all 1000 rows | 24 | — | — | — | 15/42504 covered, multiplicity 1..12 |

**Verdict: no `S(5,8,24)` acts on any of them.** ω ≤ 4 everywhere, so a block of 8 does not exist and
the axiom is not merely false — it is untestable at this block size. Even the permissive all-rows
co-occurrence view covers 15 of the 42,504 required 5-subsets, with multiplicities from 1 to 12:
under-covered and over-covered at once, which is the opposite of a design.

**The finding worth keeping is the first row of that table: exact contacts between *different*
direction classes number zero.** Every exact contact in the structured poses is same-class — rows
10, 11 and 17 have 7, 8 and 13 exact contacts respectively and not one of them crosses a class.
That is doc 75's "sliver" picture, now measured graph-theoretically: different orientations in this
table never touch at tangency, they are separated by the compression gap. And it is asserted as a
control (`selftest` 4), so if a future pose ever does have a cross-class tangency the instrument
will say so. (Row 5 is looser still: all five cells are `>= 0.207` apart even at its proved-optimal
side — no contact at all.)

So doc 94 §6's last opening is now closed the same way the others were: by measurement. The 24D
/Golay framing retains the exact codec and the descriptive class-transition data; it has no
predictive grip on the score, and the octad route was the last place one could have hidden.

## 4. What this corrects in doc 94

| doc 94 said | verified |
| --- | --- |
| certified room `1.14087` over 55 rows | **`1.09647` over 51 rows** |
| 0 rows behind the published frontier | **1 row behind: `n = 90`, `6.28e-4`** |
| `k = 3`'s prize is a ceiling "noted in prose" | **refused by the instrument (R5)** |
| scheduled `0.19194` | **`0.07237`** (`k = 4, 5, 7`), all world-record claims |
| the octad test is "specified, not run" | **run: FAIL, structurally, with zero cross-class exact contacts** |

## 5. Next, in order

1. **Fetch and certify the `n = 90` packing** (`s(90) ≤ 9.9940387665828706`, jazivxt 2026) and put it
   through C1–C4. It is the only import on the table, it is worth `6.28e-4` — seven times the two
   notches together — and it needs a transcription and a certificate, not a search. **Not attempted
   in this run**: the coordinates still have to be read from the case record and gated exactly.
2. The three scheduled bands are world-record claims (`0.0724`); attack by row gap, not by band.
3. Nothing else on the table until a claim passes R1–R5.

**Checks.** `pub_bounds_check --selftest` **3** (parser spot values, planted-error detection,
proved-set size 49 and row 6 in it); `witt_octad --selftest` **5** (the design itself, the
deleted-octad failure, the clique machinery, the cross-class-contact control, the coverage measure
on the design); `glm_plan --selftest` **5** (R5 refusal of band `k = 3`, the three world-record
claims, the verified room `1.09647`, one row behind at `n = 90`, and the earlier controls).
`sqscore` **22.218056945** (553/447); `record_guard` OK; `glm_wheels --audit` **684 functions,
0 offenders**; the full guard set green (§ user list); `py_compile` OK.
