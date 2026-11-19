# 47 — The lift, the exact carrier, and the seam production rules (Run 84)

Instruments `scripts/qsqrt2.py` (10 controls) and `scripts/mixed_field.py`
(14 controls); ledgers `workspace/push/uplift.json` (new, one record per mixed
row) and `workspace/push/mixed_field.json`. Read-only: **no row changed**, no
score claimed, `submission.csv` untouched.

**What this run answers.** Run `46` measured that 100 delivered rows are written
in the 0° and 45° words *up to a decimal* — the stored angles miss `π/4` by
4.5e-13 rad and the stored coordinates are 12-dp numbers, so the exact gate cannot
accept them as written. Three questions follow, and each one is a float-free
upgrade rather than a nicer approximation:

| # | upgrade | question | status |
|---|---|---|---|
| 1 | symbolic perception lifter | are those 100 rows *really* ℚ(√2) sentences, recoverable exactly? | **97 of 100 yes**, gate clearance exactly 0 |
| 2 | pure-algebraic ΔΣ carrier | can a rational carrier certify the irrational sentence? | **no** — closed form: legality is the sign of `r − √2` |
| 3 | seam production rules | what does an m-diamond strip cost and buy on a k-block core, in closed form? | **done** — 54/54 certified, gain positive only at m = 1 |

The rule of the run is unchanged: the exact gate is the only judge, and a
"no" is a result.

---

## 1. The symbolic perception lifter

### 1.1 The terminal object

`qsqrt2.lift_sentence(state, words)` takes a decimal sentence — centres as
`Fraction` decimals, words as 0° or 45° — and returns a state in ℚ(√2), or a
named reason why the decimals are not a sentence:

    {"status": "lifted" | "overlap" | "not-on-lattice" |
               "side-not-recovered" | "underdetermined" | "empty", ...}

The decimals are used only to choose the *topology* (which squares touch, on
which axis, with which sign). Every number in the returned state is exact, the
side is exact, and the verdict comes from `gate(state, words)` with no tolerance
anywhere.

### 1.2 How the reconstruction works

Four exact steps, in this order:

1. **The box.** `recover_side` searches the side as `a + b√2` by height-bounded
   rational basis recovery: `b` runs over `num/den` for `den <= 8`, `a` is the
   nearest multiple of `1/ad` to the remainder `side − b√2` (computed by the
   exact floor), and the comparison is exact. Three stages, cheapest first — the
   half grid (`2k + √2/2`), the small-denominator lattice, then the wide dyadic
   search. The stage order matters: one real row has side `3 + 4/3√2`, which no
   dyadic grid can see.
2. **The walls.** Every square that rests on a face of the box is placed exactly:
   `x = ex` on the left, `x = L − ex` on the right, likewise in `y`. This is what
   pins the boundary layer; a single gauge does not (measured in run 83).
3. **The peel.** Every other square from **two independent equations** to already
   placed squares — a contact on a SAT axis, with the sign the decimals have — by
   2×2 Cramer over ℚ(√2). One subtlety was a bug and is now a control: the link
   list must be *directed*, `links[i] += (j, q, −sgn, need)` and
   `links[j] += (i, q, +sgn, need)`. Reading both ends with one sign mirrors every
   placement it builds, and the gate then refuses a sentence that was built from
   its own contacts.
4. **The leftovers.** The squares the contact graph does not pin (a jammed
   interior cluster, where every neighbour is also unplaced) are recovered
   coordinate by coordinate by `recover_point`, using the row's own lattice
   denominator `D` derived from the recovered side and a height bound
   `HB = |a| + 2|b| + 4` from that side. Again exact; again the gate is the judge.

### 1.3 Measured on the table

100 mixed rows, n from 5 to 974:

| quantity | value |
|---|---|
| rows lifted | **97 / 100** |
| gate clearance on those rows | **exactly 0**, all 97 (no tolerance) |
| violations | 0 |
| exact contacts certified | **127,837** |
| squares covered | 37,260 (9,003 of them 45°) |
| centres placed by wall + peel | 26,024 |
| centres placed by height recovery | 5,618 |
| sides in ℚ(√2) \ ℚ | **97 / 97** |

The largest rows are the interesting ones, because the peel alone stalls on their
interiors and recovery fills the rest:

| n | 45° squares | exact side | side | contacts |
|---|---|---|---|---|
| 5 | 1 | `2 + 1/2√2` | 2.707107 | 4 |
| 19 | 8 | `3 + 4/3√2` | 4.885618 | 31 |
| 26 | 9 | `7/2 + 3/2√2` | 5.621320 | 52 |
| 40 | 16 | `4 + 2√2` | 6.828427 | 98 |
| 65 | 25 | `5 + 5/2√2` | 8.535534 | 172 |
| 325 | 95 | `15 + 5/2√2` | 18.535534 | 1,082 |
| 909 | 256 | `25 + 4√2` | 30.656854 | 3,259 |
| 962 | 289 | `39/2 + 17/2√2` | 31.520815 | 3,460 |
| 974 | 42 | `31 + 1/2√2` | 31.707107 | 3,523 |

That every side is irrational is not decoration: it is the run-83 obstruction
(no scale makes a 45° pose integral) restated on the real rows — 97 of the
delivered beating rows **cannot** be certified by any rational lattice predicate,
and now their field elements are known exactly.

### 1.4 The three that do not lift

| n | status | evidence |
|---|---|---|
| 51 | side not recovered | best candidate residual 2.74e-05 |
| 295 | side not recovered | best candidate residual 1.33e-05 |
| 126 | not on the lattice | 124 / 126 placed, 1 coordinate off-lattice, side `15/2 + 3√2` |

For 51 the residual keeps falling as the coefficient bound grows — 2.74e-05 at
`bmax = 8`, 1.81e-05 at 24, 1.13e-06 at 48 — the signature of an *approximation*
rather than of a value. For 295 it is flat at 1.33e-05 across the same three bounds,
so widening the search does not close that one either. In both cases no `a + b√2`
of small height sits at that side, and 1e-7 is far outside.

> **Corrected in run 85 (doc `48` §4.2).** Two of these three were a gap in this
> instrument, not a property of the table. `recover_side` allowed `b` denominator 3
> while forcing `a` onto 1/8 and 1/64 grids, and both rows have sides whose integer
> part shares denominator 3: n = 51 is exactly `16/3 + 5/3√2` and n = 295 is
> `22/3 + 22/3√2`. With `a` on the matching `4d` grid both lift at clearance 0, so
> the lift is **99/100** and the only remaining failure is n = 126, one 45° square
> whose coordinate is off every small-height lattice tested. The numbers above are
> kept as what run 84 measured; they are not what is true. Those two rows are float artefacts — decimal states whose contact topology
is not a ℚ(√2) sentence at all — and n = 126 is one coordinate away from being
one. This is the honest half of the census: the lift does not "succeed on
everything", it succeeds on 97 and *names* the 3 that are not sentences.

### 1.5 Controls

`qsqrt2.py --selftest` (10): field identities; 14,640 sign comparisons against
70-digit `Decimal`; the 3×3 grid at `L = 3` with 20 exact contacts; the 45° corner
glue tight at `2 + 1/2√2` and refused at `L − 1/1000`; **a 12-dp decimal copy of
that glue lifting back to `2 + 1/2√2` exactly** (10 equations, clearance 0); and a
3e-3 perturbation of the tilted square classified `not-on-lattice` rather than
lifted. `mixed_field.py --selftest` (14) adds the carrier, the Pell substitution,
the seam builder and the quantizer, and checks in the **bytecode** that none of
them calls `float` — a source grep would trip over the docstrings, so control 4
walks the code objects for the name.

## 2. What the 97 say about the table

Three statements, each exact:

1. **The decimal shadows are invertible.** The 100 rows' 12-dp coordinates are
   images of ℚ(√2) elements, and the height-bounded search returns them uniquely
   (candidate grids are 1/64 apart against a 1e-7 acceptance). The shadow loses
   the pair `(a, b)`; it does not lose the sentence.
2. **The lifted sides are a density ladder.** `n/L²` against the plain grid at the
   same `n`:

   | n | lifted `L` | `n/L²` | grid `n/⌈√n⌉²` |
   |---|---|---|---|
   | 5 | 2.707107 | 0.682275 | 0.555556 |
   | 19 | 4.885618 | 0.796003 | 0.760000 |
   | 40 | 6.828427 | 0.857864 | 0.816327 |
   | 101 | 10.535534 | 0.909931 | 0.834711 |
   | 325 | 18.535534 | 0.945961 | 0.900277 |
   | 974 | 31.707107 | 0.968826 | 0.951172 |

   The lifted rows are *better* than the odd grid at every size and their density
   climbs toward 1 — the grammar's own statement of why tilting pays.
3. **Nothing about the score.** No row changed. The lift certifies what the table
   already contains; it does not add to it.

## 3. The pure-algebraic carrier

### 3.1 The accumulator

`sigma_stream_exact(x, M, N)`: the error `e` is a **field element**, not a float.
Each cycle quantizes `z = x + e` to the nearest multiple of `1/M` by
`grid_round(z, M) = floor_q2(z·M + 1/2)/M`, where `floor_q2` bisects an exact
bracket `a − 2|b| − 1 <= z <= a + 2|b| + 1` using the sign rule of `46` §1, and
feeds back `e = z − q`. No `float()` call exists in the carrier, the state, the
Pell substitution, the seam builder or the quantizer (control 4, bytecode). The
gated object is therefore an exact rational state; the gate's answer is exact.

### 3.2 The ΔΣ ladder, M = 1000

| rung N | coordinate error | side excess | clearance | gate |
|---|---|---|---|---|
| 1 | 4.466e-04 | −1.068e-04 | −7.826e-04 | no |
| 2 | 5.339e-05 | −1.068e-04 | −7.551e-05 | no |
| 5 | 4.661e-05 | +9.322e-05 | +6.592e-05 | **yes** |
| 10 | 4.661e-05 | −6.781e-06 | −7.551e-05 | no |
| 20 | 3.391e-06 | −6.781e-06 | −4.795e-06 | no |
| 50 | 6.609e-06 | −6.781e-06 | −1.894e-05 | no |
| 100 | 3.391e-06 | +3.219e-06 | −4.795e-06 | no |
| 200 | 1.609e-06 | −1.781e-06 | −4.795e-06 | no |
| 500 | 6.094e-07 | −7.812e-07 | −1.967e-06 | no |
| 1,000 | 3.906e-07 | +2.188e-07 | −5.524e-07 | no |
| 2,000 | 1.094e-07 | +2.188e-07 | +1.547e-07 | **yes** |

2 of 11 rungs legal. The carrier converges (`1/(M N)` at the mean) and the
sentence does not: the legal rungs are legal at a side *above* the exact one, and
they are not the endpoints of a trend — the pattern is stroboscopic, because the
verdict is the sign of the bbox-defining coordinate's quantization error, and
first-order noise shaping does not control that sign.

### 3.3 The Pell ladder, in closed form

`pell_state` maps the whole sentence through `√2 ↦ p/q` (a ring map, so the state
stays a sentence of the same words). Then the side is computable in closed form:
the corner squares' centres are `1/2` and `3/2 + √2/2`, so under the map the box
is `2 + r/2` with `r = p/q`, i.e.

    side excess = (r − √2)/2      and      gate ⟺ r >= √2.

Measured, 12 convergents with `q <= 20000`:

| rung | coord error | side excess | clearance | gate |
|---|---|---|---|---|
| 1/1 | 1.036e-01 | −2.071e-01 | −1.464e-01 | no |
| 3/2 | 2.145e-02 | +4.289e-02 | +3.033e-02 | yes |
| 7/5 | 3.553e-03 | −7.106e-03 | −5.025e-03 | no |
| 17/12 | 6.133e-04 | +1.227e-03 | +8.673e-04 | yes |
| 41/29 | 1.048e-04 | −2.096e-04 | −1.487e-04 | no |
| 99/70 | 1.805e-05 | +3.608e-05 | +2.551e-05 | yes |
| 239/169 | 3.094e-06 | −6.185e-06 | −4.377e-06 | no |
| 577/408 | 5.309e-07 | +1.062e-06 | +7.509e-07 | yes |
| 1393/985 | 9.110e-08 | −1.822e-07 | −1.288e-07 | no |
| 3363/2378 | 1.561e-08 | +3.126e-08 | +2.210e-08 | yes |
| 8119/5741 | 2.681e-09 | −5.363e-09 | −3.793e-09 | no |
| 19601/13860 | 4.601e-10 | +9.202e-10 | +6.507e-10 | yes |

6 of 12, and the alternation is **exactly** the alternation of the convergents
around `√2`: the excess `(r − √2)/2` has the sign of `r − √2`, which alternates by
the theory of continued fractions. The clearance shrinks like the convergent
error and never reaches 0 at a rational `r`.

### 3.4 What the carrier certifies

**The carrier is a shadow with a measured sign, not an encoder.** Legality is a
half-line: `r >= √2` for the Pell map, and the sign of a coordinate error for the
ΔΣ stream. The exact sentence sits at the open/closed endpoint `clearance = 0`,
which is reached only by the pair `(a, b)`. So the answer to "can a rational
carrier certify the irrational sentence" is the same for both instruments:
**it converges to the answer and never returns it** — and now the gap is a closed
form, not a table of residuals.

## 4. The seam production rules

### 4.1 The rule

`S(k, m)`: four `k × k` axis-parallel blocks in the corners of the box, and an
`m`-diamond 45° strip along the anti-diagonal, diamond `j` centred at
`(L/2 + t, L/2 − t)` with `t = (2j − (m−1))/4`. `k = 1, m = 1` is exactly the
run-83 corner glue.

### 4.2 Closed forms

    side        L(k, m) = 2k + m√2/2
    count       N(k, m) = 4k² + m
    void        V(k, m) = L² − N = 2km√2 + m²/2 − m
    side cost   L(k, m) − 2k = m√2/2          (per square: √2/2)
    gain        ⌈√N⌉ − L = 1 − m√2/2         (the grid at N is 2k+1 whenever m >= 1)

The seam itself: consecutive diamonds differ by `(1/2, −1/2)`, a distance `1/√2`,
which is exactly the axis extent `ext = (|c|+|s|)/2 = √2/2` of a 45° square — so
every consecutive pair in the strip is a **contact**, and the strip's band has
width `√2` with zigzag amplitude `√2/2`. There is no slack parameter: the strip's
spacing *is* its width.

### 4.3 Verification, 54 / 54

For all `k = 2..10`, `m = 1..6`: the sentence gates **yes** at the closed-form side
and **no** at `L − 1e-9`. 54 of 54, no exceptions. The void is certified as a
field expression against the built sentence's own bbox in every case (control 7).

### 4.4 The economics: gain = 1 − m√2/2

`1 − m√2/2` changes sign at `m = √2`, so:

| m | gain | verdict |
|---|---|---|
| 1 | +0.292893 | strictly better than the odd grid at every k = 2..10 |
| 2 | −0.414214 | worse |
| 3 | −1.121320 | worse |
| 6 | −3.242641 | worse |

**A single diamond is a strict improvement over the plain `(2k+1)²` grid at
`4k²+1` squares, for every block size, by exact construction** — the corner glue
generalised. Two or more diamonds lose, and the reason is the strip's void
`2km√2`, which grows in `m` twice over (one factor of `m` from the strip's own
area, one from the `L` it forces).

### 4.5 Against the delivered table, no row changes

The `m = 1` family certifies `n = 4k²+1` at `2k + √2/2`. The delivered rows at
those `n` are already better, by 0.03–0.17 of side:

| n | delivered side | `S(k,1)` side | beats? |
|---|---|---|---|
| 17 | 4.675530 | 4.707107 | no |
| 37 | 6.625656 | 6.707107 | no |
| 65 | 8.535534 | 8.707107 | no |
| 101 | 10.535534 | 10.707107 | no |
| 325 | 18.535534 | 18.707107 | no |
| 401 | 20.535534 | 20.707107 | no |

So the production rule is a **proved grammar for a family the table already
dominates** — a construction result, not a score move. That is exactly what it was
asked to be: the general form of the corner glue, with the cost written in `(k, m)`
and the gate as the judge, instead of a patch glued onto one doomed `n`.

## 5. What is proved, what is measured, what is not claimed

**Proved.** The lift is exact and its verdicts are gates: 97 rows accepted at
clearance exactly 0 with 127,837 certified contacts, and a single coordinate
perturbation of 3e-3 is not liftable. The ΔΣ carrier contains no float and its
legality is the sign of its error. The Pell map's side excess is exactly
`(r − √2)/2`, so its legality is proved for every rational `r`, not just the 12
rungs tabulated. The seam rule's closed forms hold for all 54 `(k, m)` tested, and
`gain = 1 − m√2/2` is an exact sign statement.

**Measured.** The 5,618 coordinates that the contact graph did not pin (they are
recovered, and the gate certifies the reconstruction). The 2-of-11 and 6-of-12
legality counts. The three rows that are not sentences.

**Not claimed.** That `S(k, m)` is optimal in any class — it is a family, and its
side is proved minimal only within its own contact structure. That the three
non-liftable rows are *wrong* packings — they are verified packings that are not
ℚ(√2) sentences, which is a statement about the grammar, not about validity. Any
score movement: no row changed.

## 6. Next

1. **The 3 non-sentences.** Ask what field they *do* live in: n = 51 and 295 have
   sides that are not small-height ℚ(√2); a degree-4 extension or a rational-
   escalation test would say whether they are Pythagorean-word rows in disguise.
2. **The lift as a filter.** Run it over all 1000 rows with the 0°/90° word: it
   should certify the 447 grid rows at `⌈√n⌉` with clearance 0, which turns the
   "447 in ℚ" census line into a per-row exact certificate.
3. **`S(k, m)` at a band anchor.** The rule is proved but dominated; the open
   question of run `46` §8 still stands — a band anchor needs a pocket, and this
   rule gives the exact price of the only word that wins.

## Reproducing

    python3 scripts/qsqrt2.py --selftest            # 10 controls
    python3 scripts/mixed_field.py --selftest       # 14 controls
    python3 scripts/mixed_field.py                  # phases 1-3, seams, census
    python3 scripts/mixed_field.py --lift --budget 250   # repeat until remaining: 0

The lift is budgeted and cached in `workspace/push/uplift.json`; 100 rows take
about 12 minutes of exact arithmetic in total (the largest row, n = 974, is ~14 s).
