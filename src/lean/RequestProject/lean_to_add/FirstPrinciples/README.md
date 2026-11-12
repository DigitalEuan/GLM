# A First-Principles Sub-Study of the UBP System

This directory is a self-contained sub-study of the UBP constants project.  It
does something different from the parent audit.

* The parent audit (`../UBP/`, verdicts in `../docs/VERDICTS.md`) takes the
  framework's claims one at a time and asks **"is this true?"**
* This sub-study starts from the framework's own logical beginning — *there is a
  binary distinction and it can be toggled* — and asks, at each step,
  **"what is forced, what is chosen, and what had to be brought in from
  outside?"**

The result is a single ordered chain of 37 findings plus 2 bridges and 3 open
items, all machine-checked.  **The list is in
[`FINDINGS.md`](FINDINGS.md)** — that is the document to read.

---

## The short answer

The chain divides cleanly into three parts.

**Part 1 (Stages 0–2) is genuinely first-principles and genuinely works.**  From
"there is a distinction" you get, with no further input: the two-element field,
the state space `(ZMod 2)ⁿ`, the toggle group, the Hamming metric, the
`2t+1` criterion for unique decoding, the sphere-packing bound, and — the
sharpest result in the sub-study — the fact that a *perfect* three-error
correcting binary code can exist only at lengths 7 and 23 (verified exhaustively
for all lengths up to 2000).  This is the honest core of the UBP architecture.
Note what it forces: **23**.  The 24 of the "24-bit OffBit" is the parity
extension — proved here in general to raise an odd minimum distance by exactly
one, so 7 becomes 8 — which by FP-11/FP-12 adds detection but no correction; it
is chosen for self-duality, not derived.

**Part 2 (Stage 3) is where the framework stops being first-principles.**  Every
quantity produced by Part 1 is an integer.  Each of `π`, `φ`, `e` is irrational.
Therefore no seed is obtainable from the substrate by any rational expression in
its counts (FP-19): the seeds are an **input**, not an output, of the binary
principle.  Each seed *is* forced by the rôle it is given — `φ` by
self-similarity, `π` by rotational closure, `e` by unit growth rate (FP-20 –
FP-22) — but the step that multiplies them into `ℳ = πφe` and reads off the
integer 13 is a free choice: `⌊πe/φ⌋ = 5`, `⌊πφ²e⌋ = 22` and `⌊πφe²⌋ = 37` are
equally available (FP-24).

**Part 3 (Stage 4) measures the evidence.**  A formula of the shape "integer
plus a multiple of a small constant" is an arithmetic progression, and a
progression of spacing `s` lands within `s/2` of *any* target (FP-25).  Applying
this to the three headline fits:

| fit | generic guarantee | achieved | ratio |
|---|---|---|---|
| `α⁻¹ = 137 + L` | `2.3×10⁻⁴` for **any** target `≥ 137` | `1.96×10⁻⁴` | `< 1.2×` |
| `m_μ/m_e = 169/w` | `2.97×10⁻³` for **any** target `≥ 206` | `2.94×10⁻⁴` | `≈ 10×` |
| `m_p/m_e = 1836 + 2Lσ` | `1.5×10⁻⁶` for **any** target `≥ 1836` | `3.74×10⁻⁷` | `≈ 4×` |

So the fine-structure agreement is essentially not evidence at all; the muon fit
is worth about one decimal digit of surprise; the proton fit about a factor of
four.  The general statement — a family of `N` candidate formulas can match a
target set of measure at most `2Nδ` — is FP-30.

**Stage 5** disposes of the decorative arithmetic: `3, 6, 9` is one number
counted three ways and is true of any three-element set, and 24 has eight
divisors and half a dozen equally simple decompositions.

---

## Layout

```
FirstPrinciples/
├── README.md          ← this file
├── FINDINGS.md        ← THE ORDERED LIST OF FINDINGS (start here)
├── Distinction.lean   Stage 0  FP-1 … FP-7    distinction, toggle, ZMod 2, (ZMod 2)ⁿ
├── Distance.lean      Stage 1  FP-8 … FP-12   Hamming metric, unique decoding, even-distance ambiguity
├── Packing.lean       Stage 2  FP-13 … FP-18  ball counting, sphere-packing bound, lengths 7 and 23
├── Seeds.lean         Stage 3  FP-19 … FP-24  the seeds as input; φ, π, e characterised; hull alternatives
├── FitCapacity.lean   Stage 4  FP-25 … FP-31  what a numerical agreement can prove
├── Triad.lean         Stage 5  FP-32 … FP-35  3-6-9 and 24 as generic arithmetic
└── Findings.lean      assembly, the two bridges to the parent audit, and the axiom audit
```

Dependencies flow strictly downwards; `Seeds.lean` and `FitCapacity.lean` import
the parent study's enclosure arithmetic and verified constants
(`../UBP/Enclosure.lean`, `../UBP/Seeds.lean`, `../UBP/Alpha.lean`,
`../UBP/Masses.lean`) rather than duplicating them.

## Reproducing

From the repository root:

```bash
lake exe cache get      # optional, fetches prebuilt Mathlib
lake build FirstPrinciples.Findings
```

`Findings.lean` ends with a `#print axioms` block covering every headline
theorem.  Each reports only `propext`, `Classical.choice`, `Quot.sound` — Lean's
three standard axioms — so nothing here rests on an added assumption, and the
directory contains no `sorry`.

## Method notes

* **The substrate is modelled as `Bits n = Fin n → ZMod 2`.**  FP-5 justifies
  this: any two-element ring is `ZMod 2`, so nothing is assumed by working with
  the field rather than with `Bool`.
* **Exhaustive searches are kernel-checked.**  FP-15's search over all lengths
  `4 ≤ n ≤ 2000` runs inside `decide`, i.e. inside the Lean kernel, using the
  closed form `Σ_{i≤3} C(n,i) = (n³+5n+6)/6` (itself proved, `ball3_closed_form`)
  and the divisibility test `S ∣ 2⁴⁵`, which for `S ≤ 2⁴⁵` is exactly "S is a
  power of two".  No `native_decide` is used anywhere.
* **All real-number bounds are verified interval arithmetic.**  The enclosures
  of `π, φ, e, ℳ, w, L` come from the parent study's `Enc` layer, where every
  endpoint computation happens in `ℚ`.
* **Statements are kept as general as the proof allows.**  The guarantees in
  Stage 4 are stated for *all* targets above a threshold, not just for the
  measured value, because that is what makes them evidential statements rather
  than numerical coincidences.

## What this sub-study does *not* claim

It does not refute UBP.  Stages 0–2 show that a real and rather elegant piece of
mathematics sits underneath the framework's coding-theoretic layer.  What it
does establish is where the framework's own "zero free parameters, everything
flows from the seeds" narrative breaks: the seeds are an input (FP-19), the
monomial that produces 13 is a choice (FP-24), and two of the three headline
numerical agreements are within an order of magnitude of what an arbitrary
target would have received (FP-26, FP-29).
