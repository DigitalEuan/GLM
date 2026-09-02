# The harmonic register, and the third of a claim it makes testable

*What `data_objects/harmonics.py`, `reasoning/harmony.py`,
`RequestProject/GLM/Harmony.lean` and `report harmony` are for, and what they
measured.*

Every figure below is recomputed by the code that reports it. Run

```bash
cd overlay
PYTHONPATH=. python3 GLM.py -q "report harmony" --verify-tct
```

and the third column re-derives the whole study in a fresh interpreter and
checks it key by key (`VERIFIED True`).

---

## 1. Why there is a musical register at all

`glm_study_findings_catalog.md` §6.2 makes a universality claim:

> the mathematics of homeostasis is universal — chemical equilibria, musical
> harmony and market price discovery all map to Leech proximity.

`reasoning/catalog.py` had carried that sentence as **not implemented** for
several rounds, and the reason was honest: there was nothing musical in the
package to run it against, and a claim nothing can be run against is not a
finding. Of the three domains it names, music is the cheapest to supply and
the only one that needs no measurement at all. An interval *is* a ratio of two
positive integers — `3/2`, `5/4`, `81/80` — so a harmonic register is
arithmetic rather than data: nothing is calibrated, nothing is sampled, and no
float is constructed anywhere in what follows.

## 2. The register

`data_objects/harmonics.py` holds **28 intervals**: 18 just, 5 septimal and 5
commas, over prime limits 2, 3, 5 and 7. All 24 coordinates of
`HARMONIC_LAYOUT` are computed from the pair `(n, d)` in lowest terms — the
exponents over 2, 3, 5 and 7, Tenney height `n · d`, Euler's *gradus
suavitatis*, the nearest equal-tempered step and the exact rational by which
that step misses — and only `n` and `d` are needed to read the interval back,
which is why `IntervalCodec`'s round trip is exact and why corrupting a derived
coordinate cannot change what is decoded.

## 3. Equal temperament, decided by integer comparison

The nearest 12-tone step of a ratio `r` is found by comparing `r^24` against
powers of two — integers, not logarithms — and the miss is the exact rational
`(n/d)^12 / 2^k`.

| interval | the exact miss |
|---|---|
| unison, octave | `1` — exact, and the only two that are |
| perfect fifth | `531441/524288`, the Pythagorean comma |
| perfect fourth | `524288/531441` — the same comma, the other way |
| just major third | `244140625/268435456` |
| septimal third | `282429536481/221460595216`, the worst missed |

## 4. No tuning ever closes — counted here, proved in Lean

`(3/2)^n` is `3^n / 2^n` in lowest terms and `3^n` is odd, so no stack of
fifths is ever a stack of octaves. The Python side searches to `n = 200` and
finds nothing; `RequestProject/GLM/Harmony.lean` closes it for every `n`:

* `three_pow_ne_two_pow` — the kernel: `3^n = 2^m` forces `n = 0`;
* `fifth_never_closes` — `(3/2)^n ≠ 2^m` for every `n > 0` and every integer
  `m`, so the circle of fifths is not a circle;
* `odd_prime_ratio_ne_two_zpow` — the general obstruction, and the one the
  register needs: a ratio in lowest terms carrying **any** odd prime is not a
  step of *any* equal division of the octave, for every number of divisions at
  once. This is why the table above can read `1` at the unison and the octave
  and nowhere else — not by measurement, but necessarily;
* `fifth_not_tempered`, `major_third_not_tempered`,
  `harmonic_seventh_not_tempered` — one named corollary per prime limit;
* `pythagorean_comma_eq`, `syntonic_comma_eq`, `fifth_tet_error` — the exact
  residues the report quotes, checked rather than trusted.

Twelve fifths overshoot seven octaves by `531441/524288`; four fifths overshoot
the just major third by `81/80`, the syntonic comma. Both are exact.

## 5. Two orderings of consonance

Tenney height (`n · d`, taken before anyone applies a logarithm) and Euler's
gradus suavitatis are compared by an **exact** Kendall tau-a — a rational,
counted over all 378 pairs, not estimated. They agree at `313/378`: the same
five simplest intervals in the same order (unison, octave, perfect fifth,
perfect fourth, major sixth) and disagreement further out. The lattice test
below is therefore run against both rather than against a favourite.

## 6. The claim itself, and the control it has to beat

Each interval is sent to its nearest Leech point by the package's exact
decoder, through a **tuning vector**: its exponents over 2, 3, 5 and 7, scaled,
and zero in the other twenty coordinates. Deliberately *not* its register
carrier — the carrier holds `n · d` and the gradus outright, so a distance
computed from it would measure consonance by construction and the claim would
be true by definition rather than by geometry.

Two questions are then asked of the geometry, and both are counted:

| scale | distinct points | on the unison | τ vs Tenney | τ vs gradus | pairs the decoder reorders |
|---|---|---|---|---|---|
| 1 | 7 | 15 | 107/189 | 185/378 | 148 |
| 2 | 19 | 5 | 136/189 | 235/378 | 68 |
| 4 | 28 | 1 | 277/378 | 79/126 | 45 |
| 8 | 28 | 1 | **53/63** | 29/42 | **0** |
| 9 | 28 | 1 | 53/63 | 29/42 | 0 |
| 16 | 28 | 1 | 53/63 | 29/42 | 0 |
| 32 | 28 | 1 | 53/63 | 29/42 | 0 |

Below scale 4 the lattice is a *destroyer* of distinctions: at scale 1 fifteen
of the 28 intervals land on the unison's own point. From scale 4 upwards every
interval has its own point, and distance from the unison orders the intervals
by consonance at τ = 53/63, comfortably above the 1/2 the verdict rule asks
for.

**The control is the same distance taken before the decoder runs**, on the raw
tuning vectors. It scores **53/63 against Tenney and 29/42 against gradus —
exactly the same** — and from scale 8 upwards the decoder reorders **no pair at
all**.

## 7. The verdict: `not reproduced`

`reasoning/harmony._verdict` decides between three conditions, and the third is
the one that settles it: the lattice must separate the intervals (it does), the
distance must order them (it does), and it must do so **better than the
control** (it does not).

> Proximity does order the intervals — τ 53/63 against consonance — but the
> undecoded control orders them just as well with no lattice at all, and the
> decoder reorders 0 pairs, so what is measured is the prime-exponent vector
> rather than the geometry of the Leech lattice.

That is a real finding, and it is not the sentence the catalogue wrote. A
finding that survives its control is a finding; one that does not is a change
of coordinates. The confirming branch of the verdict is reachable — a test
exhibits an input that takes it — so the outcome is a measurement rather than a
foregone conclusion.

## 8. What this did to the claim ledger

`reasoning/catalog.py` §6.2 named three domains under one verdict. Two of them
can now be measured and one still cannot, so a single verdict would have to be
either a pass the markets have not earned or a gap the music does not deserve.
The sentence is therefore carried as **two claims**:

| claim | verdict | why |
|---|---|---|
| musical harmony maps to Leech proximity | **not reproduced** | read off the harmony study above — the control is not beaten |
| market price discovery maps to Leech proximity | **not implemented** | there is no economic register, and the semantics layer refuses a term it has no coordinate for rather than inventing one |

The ledger is now **58 claims: 33 confirmed, 14 refuted, 7 not reproduced, 4
not implemented**, and the musical verdict is derived from the harmony report
at call time rather than written down, so it cannot drift from what the code
measures.

## 9. Where it is reachable

| surface | what it gives |
|---|---|
| `report harmony` (aliases `harmonics`, `music`, `intervals`, `tuning`, `temperament`, `consonance`) | the whole study in three columns, the third re-deriving it in a fresh interpreter |
| the `harmonics` register | 28 interval carriers, reachable from every solver that takes a carrier |
| `report catalog` | the two §6.2 claims, the musical one carrying this verdict |
| `tests/test_harmonics.py` | 99 tests over the register, the arithmetic, the codec, the temperament table, the closure search, the two consonance orderings, the lattice sweep, the verdict and the runtime wiring |
| `RequestProject/GLM/Harmony.lean` | why no tempering error can be zero |

## 10. What is still open

Market price discovery. Supplying it would mean a register of prices, and a
price is a measurement rather than an arithmetic object — which is exactly the
difference that made music cheap and makes markets expensive. It is recorded
as an open gap in the ledger rather than passed over.
