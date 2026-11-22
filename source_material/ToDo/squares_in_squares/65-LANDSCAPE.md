# 65 — The relaxed rung: coverage, and what exact lifting can reach (run 102)

Run 101 closed the certificate boundary. This run turns that instrument on the part of the table
that has never had an exact sentence: the **424 relaxed rows**. The question is not "can the
verifier check a sentence" but "which of the 424 can a sentence be built for, and would any of them
be *smaller* than the row the table already publishes".

**Short version.** Of the 1,000 rows, 546 carry a certified exact sentence, 30 have an algebraic
*side* but no lifted pose, and 424 are relaxed. Every one of the 424 carries at least one
transcendental angle, so none can be lifted as it stands. On 14 targeted rows (the three notches,
the continuous rows that bracket them, and small/medium rows with the most slack) **3 lift and
certify at clearance 0** — and they are precisely the three notches, which were already exact. The
other **11 refuse for two structural reasons**, measured below. **No row achieves a materially
smaller exact side**: the three exact sides sit 3.84–3.85 × 10⁻⁹ *below* the delivered side, which
is the table's polish overshoot, not a gain. No row moved, and no score is claimed.

## 1. Coverage of the 1,000 rows

| label | rows | what it means |
|---|---|---|
| **certified** | **546** | an exact sentence exists at clearance 0: 447 pure-Q grid rows (run 84's census) and 99 Q(√2) pose lifts (runs 84–85) |
| **side-only** | **30** | the container side lies in Q(√2) (18), Q(√7) (5), Q(√5) (3) or a rational-t lattice (4), but the *pose* was never lifted — the unlifted one is n = 126 |
| **relaxed** | **424** | the run-86 class `continuous`: neither the side nor the pose has an exact class we search |

Source: the run-86 `field_triage.json` classes, crossed with the run-85 `uplift.json` statuses; this
run only re-derives the angle census and the side (70-digit Decimal), it does not re-classify.

The carrier census is new. A **carrier** is a square whose stored angle has no exact word in
Q, Q(√2), Q(√5) or Q(√7) at the declared heights (rational t-basis up to denominator 64; 0°, 45° and
the Pythagorean words are the exact candidates). 453 rows carry at least one carrier:

| carriers per row | rows |
|---|---|
| none | 547 |
| 1–10 | 14 |
| 11–100 | 123 |
| > 100 | 316 |

**All 424 relaxed rows carry at least one carrier** — none is 0°/45°-only — and in **361 of them a
carrier sits on the bounding box** (its rotated extent sets a face of the container), while in 63
the carriers are strictly interior. That split turns out to predict nothing about liftability, for
the reason in §5.

## 2. Why the relaxed rung is relaxed

Two independent obstructions, and the census separates them:

* **the angle.** A stored angle whose 70-digit cos/sin is not one of our exact words has no exact
  rotation matrix in any field we use. A sentence containing it is not a sentence of our alphabet —
  at *any* side. That is a statement about the declared alphabet and the declared heights, and it
  is a refusal, not a search gap.
* **the side.** The container side of a relaxed row is, in 7 of the 14 targets, not within 1e-7 of
  any `a + b√2` with denominators ≤ 16 and `|b| ≤ 16` — the declared lattice of
  `qsqrt2.recover_side`. The box itself is not a number we can write.

The four targets whose sides *are* rational are the interesting ones: **n = 680, 733, 788, 845 have
sides 186/7, 193/7, 200/7, 207/7** — the `2k + 4/7` lattice, one rung of the same rational-t
family run 90 built at `2k + 5/7`. Their angles are still transcendental, but their *sides* are
cheap, and that is why the lifting test gets further on them (§4).

## 3. The target set

Fourteen rows, chosen before any lift was run:

| group | rows | why |
|---|---|---|
| the notches | 677, 785, 901 | the three delivered rows the block-45 family almost explains; all three are `Q(√2) pose` rows and lift — they are the **reference**, not the target |
| edge band | 680, 689, 733, 788, 845, 904 | the continuous rows that bracket each notch (677 → 680, 785 → 788, 901 → 904), i.e. the nearest rung in both count and side |
| small/medium slack | 11, 17, 39, 68, 86 | the relaxed rows with the largest slack `L − √N` (0.516–0.566), where a tightened L has the most room to show up |

## 4. Method

`scripts/landscape65.py` (new, six controls of its own; `--audit` now includes it):

1. **Re-derive the angle census.** Each stored angle gets an exact word if the 70-digit Decimal
   cos/sin matches Q's axis word, the 45° word, or a rational t-basis word within 1e-11. The
   t-basis is recovered as a *fraction* (run 86's `pyth_angle` returned only the denominator, which
   cannot rebuild the word) by continued fraction with its residual declared at 1e-12.
2. **Drop the carriers, lift the core.** `qsqrt2.lift_sentence` places wall cells exactly, peels the
   rest from contact equations by 2×2 Cramer, recovers leftovers by height-bounded search, and the
   exact gate judges the result.
3. **Certify.** Every lifted sentence is written as a `galois-certificate/1` object (tag `Quad(2)`,
   exact rotations and centres as `(a, b)` pairs, tight `L`, origin 0) and checked by
   `verify_certificates.verify_certificate` — the same verifier run 101 shipped.
4. **Completion probe.** For a carrier, its contacts in the delivered pose (largest of the four SAT
   slacks zero, found in 70-digit Decimal) give exact contact equations on the *core cell's* axes;
   each word of the certified families (axis, 45°, t = 1/2, 1/3, 3, 2, 1/4, 1/5) turns each pair
   into a 2×2 solve, and a candidate is accepted only if every pair with the core clears through the
   exact per-pair predicate and the **full gate** accepts the completed sentence.
5. The two tolerances are declared and only choose topology: 1e-7 for a lift's acceptance, 1e-9 for
   reading the delivered pose, 1e-6 for contact detection in the probe. No verdict is a comparison
   against a decimal.

## 5. Results

| n | N | carriers | core | side (exact) | vs delivered | certificate |
|---|---|---|---|---|---|---|
| 677 | 677 | 0 | **lifted** | `29/2 + 17/2√2` | **−3.845e−9** | verified, 2375 contacts |
| 785 | 785 | 0 | **lifted** | `33/2 + 17/2√2` | **−3.851e−9** | verified, 2785 contacts |
| 901 | 901 | 0 | **lifted** | `37/2 + 17/2√2` | **−3.855e−9** | verified, 3227 contacts |
| 680 | 680 | 90 | 590 | not-on-lattice | — | — |
| 689 | 689 | 455 | 234 | side-not-recovered | — | — |
| 733 | 733 | 96 | 637 | not-on-lattice | — | — |
| 788 | 788 | 99 | 689 | not-on-lattice | — | — |
| 845 | 845 | 110 | 735 | not-on-lattice | — | — |
| 904 | 904 | 108 | 796 | side-not-recovered | — | — |
| 11 | 11 | 5 | 6 | side-not-recovered | — | — |
| 17 | 17 | 7 | 10 | side-not-recovered | — | — |
| 39 | 39 | 15 | 24 | side-not-recovered | — | — |
| 68 | 68 | 34 | 34 | side-not-recovered | — | — |
| 86 | 86 | 21 | 65 | side-not-recovered | — | — |

**Hits: 3 of 14** — the three notches, at clearance 0, each with a certificate the shipped verifier
accepts, and the same contact counts the run-85 lift recorded (2375 / 2785 / 3227). They are the
reference: the delivered 677/785/901 rows *are* exact sentences, and the run confirms it with the
certificate format rather than with the older ledger.

**Does any candidate beat the delivered row?** Strictly, yes — and it is not a gain. The exact sides
are 3.844692085…e−9, 3.850692085…e−9 and 3.854692085…e−9 below the sides recorded in
`submission.csv`. The table's decimals are written *above* the exact side by that margin (the
polish/shim scale every earlier run measured at 1–4e−9), so a lift always lands a few nanometres
under the published number. No row is tighter by a distance that would change a score digit, and
none of the 14 improves on what is already published.

**Misses: 11 of 14, in two groups.**

* *`not-on-lattice`* (680, 733, 788, 845 — exactly the four `2k + 4/7` rows). The side is
  recovered; the geometry is not. With the carriers removed the contact graph no longer pins every
  remaining square, and the per-coordinate height-bounded recovery refuses — the habit of these
  rows is that the carriers are **structural ties**, not decoration: they are what closes the
  corner regions of the 45° block, and removing 90–110 of them (out of 680–845) leaves free
  squares whose positions are under-determined by the equations that survive.
* *`side-not-recovered`* (689, 904, 11, 17, 39, 68, 86). The lift stops before the geometry: the
  core's own span is not within 1e-7 of the declared Q(√2) lattice, so there is no `L` to place
  cells in. These are the rows whose side is genuinely outside the fields we write.

**Completion: the machinery is tested, the relaxed rows cannot use it yet.** The probe ran a
positive control — remove one cell from the certified n = 677 sentence and ask the alphabet to put
one back — and it succeeds: the axis word at `(14 + 17/2√2, 14 + 17/2√2)`, clearance 0, 2375
contacts (control 6 in `landscape65.py --selftest`, recorded in the ledger). No relaxed row could be
probed, because the probe needs a lifted core and none of the 11 has one; so the honest count for
the relaxed rung is **0 carriers replaced out of 0 attempted**, with the theorem-of-the-day being
that the obstruction is upstream of the completion.

## 6. What this says about the frontier

The relaxed rung is not "almost exact" in the way the polished poses suggest. Its two obstructions
are independent and both fatal to a lift:

1. **the angle is not in the alphabet**, so no exact rotation exists for the carrier — and the
   carriers are spread through the row (316 rows have more than 100 of them), not confined to a
   seam;
2. **the side is not in a field we write** in 7 of the 14 targets, so even a perfect core would have
   no container.

Where the side *is* rational (`2k + 4/7`), the carriers are structural ties, so the natural next
production is not a lift but a **construction**: build a sentence at side `2k + 4/7` from rational-t
words only (t = p/7 family, denominators small), at the counts 680/733/788/845 and their
neighbourhoods, and let the gate decide. That family is exactly the one run 90 built at
`2k + 5/7`; the missing rung is the word whose seam law gives `4/7`. If it gates, four relaxed rows
acquire exact sentences *at their own published side* — no gain, but the first exact certificates on
the relaxed rung; if it gates at a smaller side, that is a real score candidate and the falsifier is
the gate at 1e-9 below.

The notches remain the template: 677/785/901 show that a relaxed-looking pose can be an exact
Q(√2) sentence when its 289 tilted squares are all at the 45° word. The relaxed 424 are the rows
where that is **not** the case, and the census now says so row by row.

## 7. State

`landscape65.py --selftest` **6 controls**, 32 s (the angle census; the 45° word; the t-basis
refusal at π/8; n = 677 lifting at clearance 0 with 2375 contacts and a verified certificate; n = 680
carrying 90 transcendental squares; and the completion control on 677). `--audit` **366 functions,
0 naming `float`** (24 of them in `landscape65`), with `landscape65` added to the audited modules. `--selftest` (glm_wheels) 32
controls, `verify_certificates --selftest` 11 mutations, bare run exit 0, `record_guard.py` OK,
README/STATUS footers byte-identical. Ledger: `workspace/push/landscape65.json`.

**No row changed, no score claimed, `submission.csv` and root `WHITEBOARD.md` untouched.** The 424
relaxed rows still carry no exact sentence; this run says which obstruction each one meets and what
a construction at the rational side would have to do.
