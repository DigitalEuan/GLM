# 46 — The mixed-field grammar: ℚ | ℚ(√2), exactly (Run 83)

Instruments `scripts/qsqrt2.py` (7 controls) and `scripts/mixed_field.py`
(13 controls); ledger `workspace/push/mixed_field.json`. Read-only:
**no row changed**, no score claimed, `submission.csv` untouched.

**The sentence this run is about.**

> Because √2 is irrational, no scale and no discrete symmetry label can make an
> irrational pose satisfy an integer lattice predicate.

That is a theorem about the *predicate*, and it is the object of study rather than
a stopping condition. What it forbids is reading a 45° packing as a lattice point.
What it leaves open is the move the ladder has been pointing at since `28`: lift
the verification alphabet one step, to the field the geometry actually lives in,
where the 0° word and the 45° word are equally first-class and their seam is
measurable in the same arithmetic. Doc `19` §5 no longer frames this as an
anti-pattern; the rung is recorded there as an interface measurement plus its
constructive lift.

**The program, as recorded.** Four phases, each with the status this run leaves it
in:

| Phase | Question | Status |
|---|---|---|
| 1 | lift the alphabet to ℚ(√2) and gate mixed sentences exactly | **done** — `qsqrt2.py`, §1–§2 |
| 2 | measure the seam: what a 45° block costs against a 0° core, and what the bridge word is | **done for the corner-glue family** — the seam law, §3 |
| 3 | carry the irrational across a rational interface with ΔΣ and ask the gate what it certified | **measured** — §4 |
| 4 | algebraic extension vs rational escalation, exactly | **done** — the swap table, §5 |

Still open, and named: Phase 2 at a *band anchor* (an exact pocket replacement,
which needs a construction rather than a float LP), and run 82's orientation-aware
empty-square bound.

---

## 1. The arithmetic, and what "exact" buys

`Q2` is `a + b√2` with `a, b` in `Fraction`. Addition, subtraction, multiplication
and division are field operations; there is no float anywhere, and `Q2` refuses to
be constructed from one. The sign — the only decision the gate needs — is exact:

    sign(a + b√2) = sign(a)             if b = 0
                  = sign(b)             if a = 0
                  = +1 / -1             if a, b have the same sign
                  = sign(a² - 2b²)      if a > 0 > b
                  = -sign(a² - 2b²)     if a < 0 < b

The middle cases are decided by comparing rationals, and `a² = 2b²` has no nonzero
rational solution, so no case is ever a tie. **A contact is exactly zero, and a
1e-300 overlap is an overlap.**

The gate is the SAT predicate `packlib.verify` implements in floats, written over
the field: for a pair with centre difference `d` and any axis `q` of either square,
the pair is separated iff

    |d·q| >= 1/2 + ext_other(q),

where `ext(c, s, q) = (|u·q| + |v·q|)/2` for the square's own edge frame
`u = (c, s)`, `v = (-s, c)`. The container side is
`max(max(x + ex) - min(x - ex), same in y)` with `ex = (|c| + |s|)/2`, also a field
element, so "does this beat the grid" is a field comparison, not a float one.

Controls (`qsqrt2.py --selftest`): field identities, including `(1+√2)(1-√2) = -1`
and `(√2/2)² = 1/2`; **14,640** mixed elements whose sign agrees with a 70-digit
`Decimal`; a 3×3 rigid grid at `L = 3` with 20 exact contacts (12 edge + 8 corner)
and clearance exactly 0; the 45° corner glue tight at `2 + √2/2` and refused at
`L - 1/1000`; **274** random rational-word states on which the exact gate and
`packlib.verify` agree, each at least 1e-3 from contact; and two overlaps refused
with exactly `-1` and `-1/2`.

## 2. The sentences, certified

Seven mixed sentences, each at the tight side of its own family: shrinking the
binding contact by 1e-3 is refused in all seven.

| sentence | N | exact side | side | gate | contacts | grid | beats |
|---|---|---|---|---|---|---|---|
| pair, 45° | 2 | `1 + 3/4√2` | 2.060660 | yes | 1 | 2 | no |
| pair, t=1/2 | 2 | `72/35` | 2.057143 | yes | 1 | 2 | no |
| pair, t=1/5 | 2 | `450/221` | 2.036199 | yes | 1 | 2 | no |
| **corner glue, 45°** | 5 | **`2 + 1/2√2`** | **2.707107** | yes | 4 | 3 | **yes** |
| corner glue, t=1/2 | 5 | `19/7` | 2.714286 | yes | 4 | 3 | yes |
| corner glue, t=1/3 | 5 | `19/7` | 2.714286 | yes | 4 | 3 | yes |
| ring nine, 45° | 9 | `2 + √2` | 3.414214 | yes | 4 | 3 | no |

The pair's binding axis is *not* the axis square's own x axis — on that axis the
slack is strictly negative at the tight side. It is the tilted square's edge axis:
the 0° square's corner sits exactly on the 45° edge. That is why the pair's side is
`(1+cos+sin)²/(2(cos+sin))` and not the obvious `1+cos+sin`.

The corner glue is the interesting one: four 0° squares in the corners and **one**
tilted square in the middle, at `2 + 1/(cos+sin)`, with **four exact contacts**.
Five squares in `2.707107` against the grid's 3 — a gain of **0.292893** of side,
and an exact density

    n/L² = 5 / (9/2 + 2√2) = (90 - 40√2)/49 = 0.682275.

## 3. The seam law

For the corner-glue family the side is exactly

    L(θ) = 2 + 1/(cos θ + sin θ),

and `(cos θ + sin θ)² = 1 + sin 2θ <= 2`, with equality only at `θ = 45°`. So

    L(θ) >= 2 + 1/√2,

and the 45° word is the unique minimum of the family. The excess is the
**field-transition tax** of a word, and it is exact:

| word | cos + sin | L | tax against 45° |
|---|---|---|---|
| 45° | √2 | `2 + 1/2√2` = 2.707107 | 0 |
| t=1/2 (53.13°) | 7/5 | `19/7` = 2.714286 | `5/7 - 1/2√2` = 0.007179 |
| t=1/3 (36.87°) | 7/5 | `19/7` = 2.714286 | `5/7 - 1/2√2` = 0.007179 |
| t=1/5 (22.62°) | 17/13 | `47/17` = 2.764706 | `13/17 - 1/2√2` = 0.057599 |
| t=1/7 (16.26°) | 31/25 | `87/31` = 2.806452 | `25/31 - 1/2√2` = 0.099345 |

This is the answer to the seam question in its cheapest form. **The minimal glue
word is one tilted square, and it couples four 0° squares at once.** There is no
sawtooth strip to pay for, because the four 0° squares are in the corners and the
tilted square's four edges are the four seams: the interface is a diagonal line of
four contacts, each exactly tight.

The honest negative is next to it: a diamond can *bridge* a seam but it cannot
*replace* a square. Put the same nine squares around a diamond — corner and edge
squares pushed to the walls of a 3×3 ring — and the side is `2 + √2 = 3.414214`
against the plain grid's 3.000000. The diamond costs 0.414 of side, which is the
run-79 finding ("one diamond nets `k² - 2`") obtained here by exact arithmetic
rather than by a float build.

## 4. The modulator across the seam

Take the exact five-square sentence and feed each irrational coordinate to a
first-order ΔΣ modulator with rational step `1/1000`. The stream is generated
against the double image of the field element (an error of 1e-16, four orders below
the quantum); the object that is then gated is the exact rational state, so the
verdict is exact.

| N | max coord error | side − L | side | gate | clearance |
|---|---|---|---|---|---|
| 1 | 4.47e-4 | −1.07e-4 | 2.707000 | no | −7.55e-5 |
| 10 | 4.66e-5 | −6.78e-6 | 2.707100 | no | −4.80e-6 |
| 100 | 3.39e-6 | +3.22e-6 | 2.707110 | no | −4.80e-6 |
| 1,000 | 3.91e-7 | +2.19e-7 | 2.707107 | no | −5.52e-7 |
| 10,000 | 1.88e-8 | +1.88e-8 | 2.707107 | **yes** | +1.3e-8 |

The running average converges like `1/(M N)`; the *sentence* does not. One of the
five rungs is legal, and it is legal at a side larger by 1.9e-8 — a different,
worse packing. Every refused rung is an overlap at the exact side or below it.
So the modulator carries the geometry as a **bounded process**: it never returns
the same sentence, it returns either an overlap at the exact side or a legal
packing at a worse one. What makes the irrational object exist exactly in a
discrete machine is not the stream but the pair `(a, b)`; the stream is its shadow,
with a bound that is now measured.

> **Superseded in part by `47` §3 (run 84).** The stream above is generated against
the double image and is only *judged* exactly — a double shortcut. Run 84 replaces
it with a carrier whose accumulator is a field element and whose quantizer is the
exact floor, with no `float()` call in the carrier, the state or the substitution
(checked in the bytecode). The qualitative conclusion survives and sharpens: for
the whole-sentence Pell map the side excess is exactly `(r − √2)/2`, so legality is
the sign of `r − √2` — proved for every rational `r`, not tabulated. The rungs
quoted here are historical; `47` §3.3 carries the exact ones.

## 5. Algebraic extension vs rational escalation

Both families computed exactly, at `N = 2` and `N = 5`:

| word | in ℚ? | N=2 side | N=5 side |
|---|---|---|---|
| 45° | no | `1 + 3/4√2` = 2.060660 | `2 + 1/2√2` = 2.707107 |
| t=1/2 | yes | `72/35` = 2.057143 | `19/7` = 2.714286 |
| t=1/3 | yes | `72/35` = 2.057143 | `19/7` = 2.714286 |
| t=1/5 | yes | `450/221` = 2.036199 | `47/17` = 2.764706 |
| t=1/7 | yes | `1568/775` = 2.023226 | `87/31` = 2.806452 |

**The two fields swap order between N=2 and N=5, and the swap is an exact
inequality, not a measurement.** At N=2 the shallowest tilt tested wins among the
words (`1568/775`), with the 45° pair `3/4√2 - 793/775 = +0.037434` behind it; but
every word loses to the plain axis pair at side 2, and the words' sides approach 2
from above as θ → 0, so N=2 is an axis win and not a gain. At N=5 the 45° glue wins,
with t=1/2 behind it by exactly `5/7 - 1/2√2`. The shallow tilt is cheap in the pair
and expensive in the glue; the algebraic word is the other way round.

**Integrality, said exactly.** The rational words have a finite integral model:
scale the `t = 1/2` and `t = 1/3` sentences by 70, `t = 1/5` by 442, `t = 1/7` by
1550, and every coordinate and the side are integers — an integer lattice
predicate can see them. The 45° word has none: `s(1 + √2)` is rational only if
`√2` is, for every rational `s ≠ 0`. So the ladder's third rung is a statement
about the *predicate*, and the escape is not a scale but a second coordinate: the
pair `(a, b)` **is** the integral model of ℚ(√2), with `b` the label the scale
cannot supply.

## 6. The census: how much of the table is even writable here

| class | rows |
|---|---|
| exactly the 0° word (stored angle `0.0`) | **447** |
| within 1e-9° of 45°, i.e. a decimal shadow (deficit 4.5e-13 rad) | 100 |
| mixing words at 1e-3° | 2 |
| no word at all | **451** |

The 447 are exactly the rows whose sides run 78 recorded as lying in ℚ. The 100 are
the 45° rows, stored as 12-dp decimals that miss `π/4` by 4.5e-13 rad — close
enough for any float instrument and not equal, so the exact gate cannot accept them
as written. The 451 remaining rows use no word at all. **A lifted grammar cannot
retrofit a decimal table; it has to build.** That is the honest reason the mixed
work is construction work, and also the reason it is well-posed: 447 rows are
already sentences of it.

> **Extended by `47` §1–§2 (run 84).** It turns out the 100 *can* be retrofitted:
the symbolic lifter recovers each row's exact ℚ(√2) state from its decimals and
certifies it with the gate at clearance exactly 0 — **97 of 100**, with 127,837
exact contacts over 37,260 squares. The other 3 (n = 51, 126, 295) are not
small-height ℚ(√2) sentences at all, so the census line above is now a measured
split: 97 decimal shadows of exact sentences, 3 float artefacts. Every one of the
97 sides is irrational, which is this section's obstruction stated on the rows
themselves.

## 7. What is proved, and what is not

**Proved here.** The arithmetic is exact and the sign decision is total (14,640
comparisons against 70-digit decimals). The gate agrees with `packlib` on every
state tested where a float verdict is unambiguous. Seven mixed sentences are
accepted at their quoted sides with exact contacts, and refused 1e-3 below them.
`L(θ) = 2 + 1/(cos+sin) >= 2 + 1/√2` with equality only at 45° — so the 45° word is
the cheapest bridge in this family, and every rational escalation pays an exact
tax. The diamond in a 3×3 ring needs `2 + √2`. The escalation comparisons are exact
rational inequalities in ℚ(√2). No scale makes a 45° pose integral (field
argument). The modulator's bound is measured, not assumed.

**Not proved, and not claimed.** That any of these families is optimal *over all
packings* — each side is proved minimal only within its own contact structure.
Nothing about the band rows: no exact mixed pocket has been built at a band anchor,
so no claim is made there, and no float LP result is reported as one. Nothing about
the score: no row changed.

## 8. Next

1. **Phase 2 at a band anchor.** Build, not search: take the `k = 18` anchor
   (`n = 345`) and write an exact ℚ(√2) pocket (corner glue scaled into the
   boundary layer) that the gate can accept or refuse. The float LP is the wrong
   instrument here precisely because its output is not a sentence.
2. **The orientation-aware bound** run 82 left open: prove the maximal empty square
   is at 0° with an interval version of `s(p, θ)` in ℚ(√2).
3. **A glue search that respects exactness.** Generate candidates in the field
   (lattice offsets in ℤ + ℤ√2), gate them exactly, and never snap a float state —
   the census shows why snapping cannot work.
