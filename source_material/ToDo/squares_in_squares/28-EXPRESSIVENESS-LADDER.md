# 28 — The expressiveness ladder (G-3), and what it buys (run 63)

**Track B. A theory result that costs no score and changes how proposals are
judged.** Six boundary claims, one shape each:

> representation *R* **cannot distinguish** two packings that differ in score.

Each rung names its witness, its ledger, and whether this run recomputed it or is
quoting it. `scripts/ladder.py` reads the ledgers and asserts them; the ledger is
`workspace/push/ladder.json` (`ladder/1`). **4 of 6 rungs recompute and pass; 2
are quoted and are not counted as checks.** That split is the point of the
document, not a footnote.

## 1. The ladder

| # | representation | what it cannot see | witness | status |
| ---: | --- | --- | --- | --- |
| 1 | **float / scan layer** | anything below ~2.5e-13 | corrected to `\|Δscan\| ≤ 1` (`01`) | quoted |
| 2 | **24-pocket address** (6 sectors × 4 shells) | anything but rotation | AUC(rot→beats) **1.0000** vs AUC(gap→beats) **0.9861**; MI(gap; beats \| rot) = **0.0000** | recomputed ✓ |
| 3 | **Λ₂₄ integrality predicate** | the field ℚ(√2) | tilted ∧ legal **0**, tilted ∧ illegal **87**, untilted ∧ legal **168**, untilted ∧ illegal **0** | recomputed ✓ |
| 4 | **contact graph + Laman count** | any mechanism beyond \|E\| | R² = \|E\| (0.391 both); 0/220 rows with a redundant contact; cluster headroom 0, −1, −1, −2 | quoted |
| 5 | **WL signature** of the tilt-coloured contact graph | geometry itself | beats its null only on a contact-bearing ensemble (R² 0.624 vs null 0.545, 0/200) | recomputed ✓ |
| 6 | **the published catalogue** | everything above n = 324 | **325** rows determined, **675** undetermined; witness family `s(k²+1) = k + 0.5355339` | recomputed ✓ |

## 2. Why one document, and why these six

Each of the six was measured in a different campaign, for a different reason, and
recorded as a failure of a *route* (runs 11–18, 50, 58–61). Read together they are
one theorem-shaped statement about **what a packing's score can be addressed by**:

* rung 1 says a numerical comparison cannot see the last 13 digits, so a gate at
  that scale is noise;
* rungs 2, 3 and 5 say the three natural *discrete* codes each collapse on exactly
  the coordinate that carries the score — pockets see rotation, Λ₂₄ sees
  integrality, WL sees combinatorics;
* rung 4 says the mechanism notion adds nothing to a count that is already
  available;
* rung 6 says the *literature itself* stops at a line, and that the line is not
  where the mathematics stops — it is where the catalogue's coverage stops.

The shape is the same in every case: **a representation is blind in a specific,
provable direction, and the blind direction is where the score lives.**

## 3. The positive companion (rung 7, constructive)

The ladder has a converse, and it is the reason the project still has a route:

> **the exact layer loses nothing that is written in a field.** 929/1000 rows are
> exact on one of two tracks (853 field-certificate + 76 `Fraction` replay, drift
> ≤ 1.9e-9), and every import replays exactly.

So the ladder is not "representations are useless"; it is "a representation must
be chosen for what it can *express*, and here the expressible thing is an
algebraic word". That is the same conclusion §5 of `19` reached from the score
side. `21`/`22` then demonstrated it constructively: both r = 1 atoms were rebuilt
from integers in ℚ(√2) and their seams solved exactly.

## 4. What the ladder buys

Three concrete uses, all available now:

1. **It forbids classes of proposal before they are built.** Any route that maps a
   packing to a lattice point (rung 3), to a pocket code (rung 2), to a graph
   invariant (rungs 4–5), or to a float comparison (rung 1) is dead on arrival for
   the *score*, however exact the map.
2. **It prices a citation.** Rung 6 is the reason the crosswalk reports 325 rows
   rather than 1000: a source's completeness boundary is a boundary result, and
   using the trivial grid past it would have manufactured comparisons.
3. **It explains the pattern of the whole project.** Every scoring result here
   added a *word* (a tilted family, an atom, a seam); every non-scoring result
   added a *code*. That is the ladder, read as history.

## 5. What this document does not do

* **Rungs 1 and 4 are quoted, not recomputed.** Their witnesses live in `01`,
  `17`, `18` and ledgers this script does not replay; `ladder.py` marks them
  `quoted` and does not count them. Closing that gap is real work (re-deriving the
  scan tolerance and the 220-row redundancy census), not documentation.
* **No Lean.** The tower and the codec still live in Python and prose (`19` §4.2).
* **It does not rank proposals by value.** The ladder says what *cannot* work; it
  says nothing about which of the surviving routes is cheapest. For that the
  register in `19` §6 and the pricing in `21`/`22` remain the instruments.
* **Rung 6 is a statement about one catalogue**, not about the literature: another
  source with above-324 coverage would dissolve it, which is exactly what §6 of
  `26` asks for.

## 6. Re-run

    python3 scripts/ladder.py      # 4/6 recomputed and checked, 2 quoted
    python3 scripts/frontier.py    # supplies rung 6's 325/675

## 7. Files

* `scripts/ladder.py` — the six rungs, ledger-backed, `ladder/1`.
* `workspace/push/ladder.json` — the rungs with their witnesses and check status.
* sources: `01-LAYERS.md`, `17-COMB-ADDRESS.md`, `18-RIGIDITY.md`,
  `workspace/push/{leech_audit_fix,leech_map,leech_comb,frontier}.json`.
