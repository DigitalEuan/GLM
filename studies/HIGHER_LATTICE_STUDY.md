# Past 24: the higher-lattice study

*What the machine gains by climbing above the Leech lattice, and what it has to
give up to get there. The 32-dimensional Barnes–Wall rung and its
three-resolution address; the 48-dimensional ternary rung and its factor of
16,834 in density; and the delta–sigma loop run against a Leech shell, where
the alphabet is a sphere rather than a ball.*

Code:
[`overlay/glm_universal/substrate/lattice32.py`](../overlay/glm_universal/substrate/lattice32.py),
[`overlay/glm_universal/substrate/lattice48.py`](../overlay/glm_universal/substrate/lattice48.py),
[`overlay/glm_universal/reasoning/higher_lattices.py`](../overlay/glm_universal/reasoning/higher_lattices.py),
[`overlay/glm_universal/reasoning/shell_sigma.py`](../overlay/glm_universal/reasoning/shell_sigma.py).
Queries: `report lattices`, `report shells`.
Formal development:
[`RequestProject/GLM/HigherLattices.lean`](../RequestProject/GLM/HigherLattices.lean),
[`RequestProject/GLM/ShellSigma.lean`](../RequestProject/GLM/ShellSigma.lean).
Tests: `overlay/glm_universal/tests/test_lattice32.py`,
`test_lattice48.py`, `test_higher_lattices.py`, `test_shell_sigma.py`.

---

## 1. The question

Everything spatial in this system lives in 24 dimensions: the Golay code, the
MOG, the Leech lattice Λ₂₄, its 196,560 minimal vectors, the hull census that
decides which targets a 24-dimensional carrier can hold. That is a stopping
point, not an end point, and the to-do list asked the obvious next question:
*what is above it, and is anything up there useful to this machine rather than
merely true?*

Two separate things were wanted, and they are the two halves of this document.

1. **Climb the ladder.** The even unimodular lattices whose minimum is as large
   as the dimension allows — the *extremal* ones — exist in dimensions 8, 16,
   24, 32, 40, 48, …. Build the two rungs above the Leech lattice, from
   scratch, and see what each construction buys.
2. **Use a shell as an alphabet.** The delta–sigma machinery of
   [`NOISE_EXPERIMENT_STUDY.md`](NOISE_EXPERIMENT_STUDY.md) always emits from a
   *small* alphabet, and `HullExpansion.lean` records the price: a loop can
   only track targets inside the convex hull of what it may emit. What happens
   when the alphabet is 196,560 points on a sphere?

Both halves keep the discipline of the rest of the repository: no float is
constructed anywhere, no random number is drawn, every count is recomputed
rather than quoted, and each claim that can be a theorem is one.

---

## 2. The ladder, recomputed

`ladder_report()` does not store the table below; it recomputes each centre
density from `δ = (minimum/4)^(n/2)`, which is valid because all four lattices
are unimodular, and takes the kissing numbers from the modules that build the
lattices.

| dim | minimum | centre density | kissing | source of the kissing number |
|---|---|---|---|---|
| 8 | 2 | `1/16` | 240 | classical |
| 16 | 2 | `1/256` | 480 | classical |
| 24 | 4 | `1` | 196,560 | `substrate.leech2.minimal_vectors` |
| 32 | 4 | `1` | 146,880 | `substrate.lattice32` |
| 48 | 6 | `282429536481/16777216` | — | not computed here |

Every row is extremal for its dimension (`all_extremal: true`). The last
centre density is exactly `(3/2)^24`, so the 48-dimensional rung packs about
**16,834 times** more densely per unit cell than the Leech lattice. That
number is the whole motivation for the climb, and it is an exact rational, not
a rounded one.

The 24- and 32-dimensional rows have the *same* centre density, 1. They are
not the same lattice and the 32-dimensional one is not a waste of a rung: what
32 dimensions buy is not density but **address structure**, which is §3.

---

## 3. Thirty-two dimensions: an address with three resolutions

### The obstacle

Construction A over a binary code always contains `2 eᵢ`. In the `|x|²/2`
normalisation that vector has norm 2, so a single-level binary lift can never
have minimum 4 in 32 dimensions, no matter which code is used.

### The fix

A *two-level* lift — Construction D — over a nested pair of Reed–Muller codes
`RM(1,5) ⊂ RM(3,5)`. A point is

```
x = 4a + 2b + c        c ∈ RM(1,5),  b ∈ RM(3,5),  a ∈ Z^32
```

and `lattice32.py` recomputes every input to that construction:

| quantity | value |
|---|---|
| outer code `RM(1,5)` | length 32, dimension 6, 64 words, weights {0, 16, 32} |
| words of weight 16 | 62 |
| inner code `RM(3,5)` | length 32, dimension 26, minimum weight 4 |
| words of weight 4 | 1,240 |
| nested, and a dual pair | `RM(1,5) ⊂ RM(3,5)`, dimensions sum to 32, mutually orthogonal |

The minimum is the three-case argument, and each case is decided by a
*different* level of the address:

| case | why the norm is large | code input | bound on `|x|²` |
|---|---|---|---|
| `c ≠ 0` | a coordinate with `cᵢ = 1` is odd, so contributes ≥ 1 | outer minimum weight 16 | 16 |
| `c = 0, b ≠ 0` | a coordinate with `bᵢ = 1` is 2 mod 4, so contributes ≥ 4 | inner minimum weight 4 | 16 |
| `c = 0, b = 0, a ≠ 0` | a nonzero coordinate is a nonzero multiple of 4 | none | 16 |

All three bottom out at exactly 16, which is minimum 4 in the `|x|²/2` model —
extremal for dimension 32. That is
`GLM.HigherLattices.BarnesWall.norm_ge_of_ne_zero`, proved in Lean for a
general `n` and a general pair of binary vectors, with the code hypotheses as
explicit assumptions. Evenness is
`BarnesWall.norm_dvd_eight`, and it comes from the duality of the two codes:
the cross term `2·⟨b, c⟩` is even exactly because `b ⟂ c`.

The determinant certificate is computed rather than cited: the basis
determinant is `2^32 = 4,294,967,296`, the Gram determinant is `2^64`, the
scaled determinant is 1 — unimodular — and the Gram matrix is even.

The kissing number is a census of the three shapes:

```
(±1^16, 0^16)   126,976
(±2^4,  0^28)    19,840
(±4^1,  0^31)        64
                -------
                146,880   distinct: 146,880
```

### What the address buys

This is the part that feeds back into the rest of the system. A Leech address
is **flat**. The mod-2 / mod-4 / mod-8 sieve of `substrate.leech_construct` is
a membership *test*: it tells you whether a vector is in Λ₂₄, but you cannot
hand someone the coarse part of a Leech vector and have them reconstruct
anything at that resolution alone.

Construction D is different, because its three levels are genuinely nested
lattices, each an honest quotient of the next:

```
4Z^32  <  4Z^32 + 2·RM(3,5)  <  4Z^32 + 2·RM(3,5) + RM(1,5)
```

| | |
|---|---|
| index of the first step | `2^26 = 67,108,864` |
| index of the second step | `2^6 = 64` |
| total index | `2^32 = 4,294,967,296` (the product, checked) |
| usable resolutions | **3**, against 1 for a Leech address |

`address_round_trip()` takes sample points apart and puts them back together,
and checks the property that makes the address multi-resolution rather than
merely a decomposition: truncating to the first *k* levels gives exactly the
nearest point of the *k*-th nested lattice. Every sample round-trips, every
truncation is itself a lattice point, and the levels nest
(`all_round_trip`, `all_levels_usable`: true). Uniqueness of the decomposition
is `BarnesWall.mk_injective`.

So the answer to "what does dimension 32 buy?" is: a coarse address that is
usable on its own and refinable later — precisely what a single Leech address
is not.

---

## 4. Forty-eight dimensions: where binary runs out

### The obstacle, stated honestly

There is a beautiful binary code of the right size — the extended quadratic
residue code `QR(47)`, a self-dual doubly even `[48, 24, 12]` code, built here
from the quadratic residues mod 47 and verified self-dual and doubly even. It
is not enough. Construction A over *any* binary code contains `2 eᵢ`, of norm
2, so the binary route stops at minimum 2, four short of extremal, and no glue
over that code repairs it.

### The fix: move to `F_3`

Over `F_3`, Construction A has shortest trivial vectors `3 eᵢ`, of norm 3 in
the `|x|²/3` model. The code is the **Pless symmetry code `C(23)`**, generated
by `[I₂₄ | S]` with `S` the bordered Jacobsthal matrix of the prime 23.
`ternary_code_report()` recomputes `S Sᵀ = −I` over `F_3` (hence self-dual),
`Sᵀ = −S` (hence both halves are information sets), and divisibility of all
weights by 3. Its minimum distance is 15.

Then a four-step ladder, each step exact:

| lattice | definition | determinant | minimum |
|---|---|---|---|
| `A` | `{x ∈ Z^48 : x mod 3 ∈ C}`, form `|x|²/3` | 1 | 3 (odd lattice) |
| `L₀` | `{x ∈ A : Σx even}` | 4 | **6** |
| `N₁` | `L₀ + Z·h`, `h = (3/2)·1` | 1 | 4 |
| `N₂` | `L₀ + Z·h′`, `h′ = 3e₀ + h` | 1 | **6** |

`L₀` reaching 6 is the machine-checked step:
`GLM.HigherLattices.Ternary.even_norm_ge_eighteen` says a nonzero vector of an
even lattice built over a ternary code of minimum weight 15 has `|x|² ≥ 18`.
The two supporting lemmas are `Ternary.norm_ge_card_support` (a coordinate
outside `3Z` contributes at least 1) and `Ternary.norm_dvd_nine` (if every
coordinate is divisible by 3 the norm is divisible by 9) — the two halves of
the case split.

`N₁` and `N₂` are the two even unimodular *neighbours* of `L₀`. They differ
only in which coset is glued on, and the difference between minimum 4 and
minimum 6 comes down to a parity census. Every vector of the glued coset has
all 48 coordinates half-odd-integers, so its norm is at least 4, with equality
iff every coordinate is `±1/2`; translating that back through `x = y − h`
turns the equality case into a statement about the code. The norm-4 vectors of
`N₁` are exactly the full-weight codewords with an **even** number of
2-coordinates, and those of `N₂` the ones with an **odd** number.

`full_weight_census()` settles it by enumeration:

```
full-weight codewords          96
   even number of 2s           96
   odd  number of 2s            0
```

All 96 land in `N₁`, which therefore has minimum 4; **none** land in `N₂`, so
`N₂` is the extremal one. The count is cross-checked independently by solving
for the extremal ternary weight enumerator in the Gleason basis
`φ₄ = x⁴ + 8xy³`, `φ₁₂ = y³(x³ − y³)³` from `A₀ = 1`,
`A₃ = A₆ = A₉ = A₁₂ = 0`, and reading off `A₄₈ = 96`. Two independent routes,
same number.

### What is certified and what is recorded

Directive **D8** says the Lean file is the specification, and the corollary is
that a document must be clear about which claims are which. In this section:

* **Proved in Lean**: `L₀` has minimum 6, given a ternary code of minimum
  weight 15.
* **Recomputed exactly, every call**: the code's self-duality, symmetry, weight
  divisibility, the four determinants, the neighbour construction, the Gleason
  cross-check `A₄₈ = 96`.
* **Recomputed only when asked** (`exhaustive=True`, a few seconds each): the
  ternary minimum distance 15 by exhausting an information set, the
  full-weight census by `2^23` Gray-code steps, and the binary minimum distance
  12 by `2^24` steps. The default report flags these as `exhaustive: false`
  and says so in the payload — a recorded result is labelled a recorded result.
* **Not computed at all**: the kissing number in 48 dimensions, which the
  ladder reports as `null` with `kissing_source: "not computed here"` rather
  than quoting a literature value.

---

## 5. The other half: delta–sigma against a shell

### Why a shell is hard

The delta–sigma results of the noise study all rest on one hypothesis: the
quantiser has a **covering radius** — every point of the space is within `ρ` of
something the loop may emit. Then the accumulator never leaves the ball of
radius `ρ`, and the running mean tracks any target at `ρ/N`.

A shell is a *sphere*. It is finite and it covers nothing, so that hypothesis
is simply unavailable, and with it the whole argument. `ShellSigma.lean`
therefore proves two different laws for two different rules.

### Rule 1 — nearest, over the whole lattice

`GLM.Shell.sAverage_error_le`: with a quantiser of covering radius `ρ`, the
running mean tracks *any* target at `ρ/N`. The Leech lattice covers, so
nothing is out of reach; this is exactly the wall of `HullExpansion.lean`
coming down, at the cost of an alphabet that is no longer finite. Measured,
with the exact Leech decoder as the quantiser, 12 ticks:

```
covering radius²      16
max |state|²          16      (inside the ball, as the theorem says)
error |mean − t|²     1/9   ≤ bound 1/9
emissions             all in Λ₂₄
```

The hypothesis of the theorem — that a covering radius exists at all — is a
long way outside this development for Λ₂₄, so it enters the Lean file as an
explicit hypothesis `hq`, and `roundQuant_covering` (rounding on `ℝ` covers at
`1/2`) shows the hypothesis is satisfiable rather than vacuous. That is the
honest shape for a theorem whose hypothesis the code checks numerically.

### Rule 2 — matched, over one shell

Emit the shell point the accumulator points at hardest: the `argmax` that
computes the alphabet's **support function**. The replacement for a covering
radius is a **margin** `μ`: the support function beats the target by `μ‖s‖` in
every direction, which says exactly that the target sits at distance `μ` inside
the convex hull of the shell. Then

* `GLM.Shell.shState_norm_le` — the accumulator never leaves the ball of radius
  `D²/(2μ) + D`, where `D` bounds `‖t − v‖` over the alphabet;
* `GLM.Shell.shAverage_error_le` — hence the `B/N` law for a finite,
  non-covering alphabet.

Measured, on a target built as an explicit convex combination of shell points,
24 ticks:

```
target |t|²             128/81
error  |mean − t|²      5/324     (and 5/81 at half the ticks: it falls as 1/N)
max |state|²            2048/81   — flat, not growing
observed margin²        2209/162
min slack over the run  0         (the margin hypothesis held at every
                                   direction the run actually visited)
emissions               5 distinct points, all on the shell
```

The accumulator is *bounded* while `N` grows, which is the whole content of the
theorem, and the error accordingly falls like `1/N`.

### The wall is still there, and it is exhibited

`outside_run()` takes the target `5e₀`. In the direction `e₀` the shell's
support function is 4 while the target is 5:

```
h(e₀) = 4  <  ⟨e₀, t⟩ = 5      gap 1
```

That is a one-line exact separating certificate that **no** rule emitting from
the shell can ever reach the target, and the run shows the accumulator growing
linearly at exactly the predicted rate of 1 per tick (`|state|² = 144` after 12
ticks, i.e. `|state| = 12`). The relevant theorem is
`GLM.Info.not_tendsto_avg_of_separating`. Inside the hull: `1/N`. Outside:
divergence, with the rate known in advance.

`certified_inner_ball()` gives a *sufficient* condition needing no search: from
the first shape alone, `h(x) ≥ 4·max|xᵢ| ≥ 4‖x‖/√24`, so every target with
`3‖t‖² < 2` has a certified margin. Exact, and deliberately not tight.

### The support function, and the one shortcut in this study

The matched rule needs `h(x) = max{⟨x, v⟩ : |v|² = 32}` **exactly**, at every
tick. Enumerating 196,560 vectors per tick is possible; `shell_support`
instead maximises over each of the three shapes in closed form —
`(±4², 0²²)` from the two largest coordinates; `(±2⁸)` over the 759 octads;
`(∓3, ±1²³)` over the 4,096 Golay codewords with the coset sums supplied by the
Walsh–Hadamard transform of `reasoning.fwht_decode`.

Directive **D2** says to prefer the raw computation to fighting for a shortcut.
This is the case where the shortcut earns its keep, and the reason is worth
recording, because it is the general rule rather than an exception:

| | per call |
|---|---|
| closed form (`shell_support`) | ≈ 65 ms |
| enumerating all 196,560 minimal vectors | ≈ 10.4 s |

The shortcut is about 160× faster — but what makes it *usable* is
`support_agreement()`, which checks the closed form against the full sweep and
found `all_agree: true` on every probe tried. The raw computation is not the
thing the shortcut replaces; it is the thing that licenses it. A shortcut with
no raw computation behind it is an assumption wearing a faster coat.

### Temperature without randomness

The last section of `ShellSigma.lean` replaces the hard snap — always the
nearest point — with a temperature-weighted choice among candidates:

```
gibbsWeight E t i = t^(Emax − Eᵢ) / Σⱼ t^(Emax − Eⱼ)
```

in exact rational arithmetic, with three proved properties:
`gibbsWeight_uniform` (at `t = 1` every candidate has weight `1/m`: infinite
temperature is the uniform ensemble), `gibbsWeight_le_inv` (a candidate that is
not of least energy has weight at most `1/t`: as the temperature falls the rule
collapses onto the hard snap, at an explicit rate) and `gibbsWeight_mono`
(lower energy never has lower weight).

A machine that constructs no floats and draws no samples cannot realise an
ensemble by sampling it. So it does not: `gibbsCount` is the same greedy
error-feedback accumulator the modulators use, and `gibbsFreq_error_le` proves
its visit frequencies converge to the Gibbs weights at rate `(m−1)/N`. **The
trajectory is the distribution.**

Measured on a real instance — the query point `(3,2,1,0,…)`, its six nearest
shell candidates, energies the exact squared distances `6, 14, 22, 22, 22, 22`
scaled by 8 to `0, 1, 2, 2, 2, 2` — over 60 ticks:

| `t` | weights | max frequency error | proved bound `(m−1)/N` |
|---|---|---|---|
| 1 | `1/6` each | `0` | `1/12` |
| 3 | `9/16, 3/16, 1/16, …` | `1/80` | `1/12` |
| 12 | `9/10, 3/40, 1/160, …` | `1/96` | `1/12` |

At `t = 1` the frequencies are exactly uniform; as `t` rises the ensemble
concentrates on the nearest candidate, and the deterministic trajectory stays
inside the proved bound at every temperature.

---

## 6. What this changes for the system

* **The Leech lattice is not the only address space in the package.** For
  anything that wants a coarse-then-fine address, the 32-dimensional
  Construction D lattice provides three usable resolutions where Λ₂₄ provides
  one. `LEAN_ADDRESS_STUDY.md` uses the flat Leech address, and §3 is the
  measurement of what that costs.
* **Density has a price and it is legible.** 48 dimensions buy a factor of
  16,834 in centre density and cost the binary picture entirely: no Golay code,
  no MOG, no octads — an `F_3` code and a neighbour step instead.
* **A finite non-covering alphabet is workable, with a margin.** The `B/N` law
  for the matched rule means the delta–sigma machinery is not restricted to
  covering alphabets, provided the target is certifiably inside the hull; and
  when it is not, the separating certificate says so in one line.
* **Temperature is available without randomness.** Anything in the system that
  would have reached for a sampler can use the error-feedback realisation and
  keep both determinism and an error bound.

---

## 7. Reproducing every number here

```bash
cd overlay
PYTHONPATH=. python3 GLM.py -q "report lattices" --no-banner
PYTHONPATH=. python3 GLM.py -q "report shells"   --no-banner

# with column-3 verification (slower: a fresh interpreter per subject)
PYTHONPATH=. python3 GLM.py -q "report lattices" --verify-tct --no-banner
PYTHONPATH=. python3 GLM.py -q "report shells"   --verify-tct --no-banner

# the exhaustive certificates, opt-in
PYTHONPATH=. python3 -c "from glm_universal.substrate import lattice48 as l; \
    print(l.lattice48_report(exhaustive=True)['full_weight_census'])"

# the tests
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_lattice32.py \
    glm_universal/tests/test_lattice48.py \
    glm_universal/tests/test_higher_lattices.py \
    glm_universal/tests/test_shell_sigma.py -q
```

The Lean side:

```bash
lake build
```

`HigherLattices.lean` and `ShellSigma.lean` are `sorry`-free, and every theorem
named above depends only on the standard axioms (`propext`,
`Classical.choice`, `Quot.sound`).
