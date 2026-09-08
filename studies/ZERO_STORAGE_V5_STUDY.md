# Generate, don't store — and say what generating costs

*The zero-storage substrate reached v4 with one stored table left in it: a
4096-word set of Golay codewords, consulted on every membership decision. v5
removes it — the code is self-dual, so its twelve generator rows are also a
parity-check matrix, and membership is twelve AND-popcount-parity operations
against 36 bytes — and then does the thing that makes the removal an honest
trade rather than a slogan: every generated answer now carries an exact
integer **ledger** of what it cost. A third piece, **NRCI**, is given one
written-down definition here and reported for three streams the substrate
already emits, beside the bound that is proved for one of them.*

Code: [`glm_zero_storage_substrate_v5.py`](../glm_zero_storage_substrate_v5.py)
(standalone, standard library only; v4 is kept unchanged at
[`glm_zero_storage_substrate_v4.py`](../glm_zero_storage_substrate_v4.py) so
the two can be run side by side).
Formal development:
[`RequestProject/GLM/ZeroStorageV5.lean`](../RequestProject/GLM/ZeroStorageV5.lean),
building on [`ZeroStorage.lean`](../RequestProject/GLM/ZeroStorage.lean).
Run: `python3 glm_zero_storage_substrate_v5.py --test` (about six seconds,
exits 0), `--ledger`, `--demo`, `--report`, and `--test --full` for the
sixteen-million-word sweep.

---

## 1. What was still stored, and what replaced it

v4's `is_leech` decided the Golay condition with `mask in self.word_set`: a
frozenset of 4096 24-bit words, roughly 12 KB held for the life of the
process. Everything else in the file was generated; this was the exception,
and it was the exception in the one place the substrate is used most.

The extended binary Golay code is **self-dual**: `G = G⊥`. So the same twelve
generator rows that *produce* the code also *check* it, and

```
syndrome(mask) = ( popcount(mask & row_0) mod 2, …, popcount(mask & row_11) mod 2 )
mask ∈ G₂₄  ⟺  syndrome(mask) = 0
```

Twelve word operations against 36 bytes of generator, no allocation, no
lookup. And when the word is *not* a codeword the same twelve operations
return its 12-bit syndrome rather than a bare `False` — which is the language
the Lean decoder machinery (`GLM.Golay.Census`, `GLM.Cube.Tax`) is already
written in, so the script and the proofs now say the same thing.

**Proved.** `GLM.ZeroStorageV5.syndromeZero_iff_isGolay` — for every
`c < 2²⁴`, zero syndrome is equivalent to membership of the code. The proof
is the systematic-encoder argument: `check_xor` makes the checks 𝔽₂-linear,
`rows_orthogonal` (a 144-case kernel decision) makes every row pass every
check, so every codeword has zero syndrome; conversely, subtract the codeword
carried by the low twelve bits and what remains has no information bits and
zero syndrome, and `high_injective` (a 4096-case kernel decision) says such a
word is zero. `syndromeSieve_iff_isLeech` then carries it up to the whole
membership test: parity read off coordinate 0, twelve parity checks, one
mod-8 sum — no table anywhere — decides exactly `IsLeech`.

**Checked before anything was removed**, in
`check_syndrome_against_lookup()`, three ways:

| comparison | result |
|---|---|
| every codeword the generator produces has syndrome 0 | 4096 / 4096 |
| the set of zero-syndrome words in the whole 2²⁴ space, by exact null-space elimination | 4096 words, **equal to the code as a set** |
| all 16,777,216 words swept one at a time (`--test --full`) | 4096 accepted, agrees |
| the 196,560 minimal vectors of Λ₂₄, syndrome route against the v4 lookup route | **196,560 compared, 0 disagreements** |
| 1,536 deliberate non-codewords (a codeword with one bit flipped) | 1,536 compared, 0 disagreements |
| the same, on the generator rows the **Lean** development uses | verified |

The last row matters: the script builds the code from the quadratic residues
mod 11 and the Lean development uses a different, permutation-equivalent
generator. The syndrome route is checked against both, so the equivalence
proved in Lean is a statement about a generator this file also runs.

The null-space check deserves a sentence. Sweeping 2²⁴ words is the check a
sceptic asks for and it is offered (`--full`), but it is not the check that
settles the question: the parity map is linear, so its kernel is the span of a
null-space basis, and computing that basis exactly and comparing it with the
code as a *set* settles it in milliseconds.

---

## 2. The cost ledger: what an answer costs, in exact integers

Every routine that does work now takes an optional `Ledger` and posts the
exact count of primitives it spent. Thirteen items are counted and each is
documented in the file (`LEDGER_ITEMS`): parity checks, popcounts, word XORs
(Gray-code steps), coordinate passes, coset trials, cosets pruned, ±4 repairs,
table lookups, integer square roots, series terms, big-integer divisions,
Δ-Σ ticks, rational operations.

Two disciplines make the numbers worth quoting:

* **Exact integers, never wall-clock.** A second run of the same call
  reproduces the ledger byte for byte. Nothing in this file records a time.
* **Posted from known trip counts**, not incremented inside hot loops, so the
  ledger does not depend on how a loop was written.

Headline costs, as `--ledger` prints them:

| operation | ledger | held bytes |
|---|---|---|
| one Golay membership decision, syndrome route | `parity_check: 12` | 36 (the generator) |
| one Golay membership decision, cached route | `table_lookup: 1` | 36 + **12,288** (the cache) |
| one Leech membership decision | `coordinate_pass: 24, parity_check: 12` | 36 |
| one nearest-point decode, pruned | `coset_trial: 9, coset_pruned: 8,185, coordinate_pass: 34,303, pm4_repair: 4, word_xor: 8,192, parity_check: 12` — total **50,705** | 36 |
| the same decode, exhaustive | `coset_trial: 8,194, coordinate_pass: 196,776, pm4_repair: 4,098, word_xor: 8,192` — total **217,272** | 36 |
| π to 64 bits | `series_term: 31, big_div: 64` — total 95 | — |
| √2 to 64 bits | `int_sqrt: 1, big_div: 1` — total 2 | — |
| γ to 64 bits | `series_term: 543, big_div: 569` — total 1,112 | — |

The storage audit is now three columns rather than two — bytes stored, bytes
of generator, **and the tax to recover one item**:

| object | stored | generator | tax per item |
|---|---|---|---|
| the 4096 codewords | 12,288 B | 36 B | `word_xor 4095/4096` (one XOR each) |
| a membership decision | 12,288 B | 36 B | `parity_check 12` |
| the 759 octads | 2,277 B | 36 B | `word_xor 1365/253` |
| the 196,560 minimal vectors | 4,717,440 B | 36 B | `coordinate_pass 24, word_xor 1/24` |
| one nearest-point decode | 4,717,440 B | 36 B | ≈ 50,700 primitives |
| **total** | **9,461,733 B** | **180 B** | — |

That is the honest form of the comparison the earlier drafts were making. The
ratio 52,565 : 1 is real, and so is the tax: recovering *one* codeword costs
about one XOR, recovering *one* membership decision costs twelve parity
checks — both far cheaper than the table they replace — while recovering the
nearest lattice point to a target costs about fifty thousand primitives, which
is where a cache could genuinely be argued for. The ledger is what turns that
from an opinion into a number.

**The cache, if it is wanted, is a cache.** `GolayCode(rows, cache=True)`
materialises the 4096 words, records the SHA-256 digest of *what the rows
generate*, and `cache_is_what_the_rows_generate()` regenerates and compares —
the digest-and-regenerate discipline the rest of the system uses. The audit
prices both paths side by side so the trade is visible rather than assumed.

**The zero-storage alternative was measured first.** The coset search is now
pruned by a running bound: coordinates are visited in decreasing order of how
much the choice costs, a coset is abandoned as soon as its partial cost plus
the cheapest possible completion reaches the best cost so far, and a seed
codeword (the systematic encoding of the cheaper residue choice on the twelve
information positions) gives the bound something to work with immediately.
This stores nothing. On the deterministic probe set it evaluates **3 to 9** of
the 8,192 cosets and prunes the rest, for a mean work ratio of **0.218**
against the exhaustive search — and `decoder_cost_report()` checks that the
pruned search returns the *same point at the same distance* as the exhaustive
one on every probe.

---

## 3. NRCI, defined here

The older GLM material uses "NRCI" with more than one formula behind it. In
this file it has exactly one, and it is a measurement rather than a slogan:

> For a residual sequence `r` measured against a reference sequence `x` of the
> same length with `Σxᵢ² > 0`,
>
>   **NRCI(r ; x) = 1 − √( Σ rᵢ² / Σ xᵢ² )**

It is 1 when the residual vanishes, 0 when the residual is as large as the
reference, negative when it is larger. Two exact forms are reported and
neither uses a float:

* `nrci_squared(r, x)` — the exact rational `1 − Σr²/Σx²`, which needs no
  root at all;
* `nrci(r, x, bits)` — a dyadic **enclosure** `[lo, hi]` of the definition
  above with `hi − lo ≤ 2⁻ᵇⁱᵗˢ`, computed with `math.isqrt`, so the two
  endpoints provably bracket the value and a second run reproduces them.

Every reported figure names the stream it was measured on. The three the
script emits, at 2⁻³²:

| stream | what the residual is | NRCI |
|---|---|---|
| Δ-Σ running average | `rₙ = (1/n)Σbᵢ − (1/n)Σtᵢ` for `n = 1…N`, against the running mean target | 0.914890755 (N = 512, target 2/7) |
| a decode | `rᵢ = pointᵢ − targetᵢ` over the 24 coordinates, against the target | 0.694065270 |
| the dyadic tower | `rₙ = q − πₙ(q)` for `n = 0…12`, against `q` | 0.594904260 |

Where a bound is *proved*, the figure and the bound are printed side by side:
for the Δ-Σ stream the read-out bound `|rₙ| < 1/n` is checked at **every** `n`
of the window, not only at the end, and reported beside the NRCI. That is the
intended use — NRCI is comparable across runs and streams, and it is never
asked to do the work a proof does.

---

## 4. Continuous retargeting: the register as a tracker

v4's `retarget()` zeroed the accumulator, which threw the window away: a
register retargeted every tick never held more than one tick of evidence. In
v5 retargeting keeps the accumulator by default, and the bound survives,
because the accumulator stays in `[0,1)` whatever the target does:

```
Σ bits = Σ targets − accumulator,   0 ≤ accumulator < 1
```

so `|average − mean target| < 1/N` for a *moving* target, and against a fixed
target `s` the error is that plus exactly the mean deviation of the trajectory
from `s`.

**Proved.** `dsAcc_mem_Ico` (the accumulator invariant), `dsAcc_eq` (the count
identity), `ds_track_bound` (`|average − mean target| < 1/N`) and
`ds_track_moving_target` (`|average − s| ≤ 1/N + (1/N)Σ|tₙ − s|`), all over ℚ
with a per-tick target schedule — the formal image of continuous retargeting.

**Measured**, on a deterministic ramp with a step in the middle (256 ticks,
256 writes, no RNG):

| | measured |
|---|---|
| `|average − mean target|` | 7/2048, against the bound 1/256 — holds |
| `|average − final target|` | 81/256, against `1/N + drift = 649/2048` — holds |
| accumulator stayed in `[0,1)` | yes |
| the v4 zeroing register, same trajectory | **1 tick of evidence** at the end |

---

## 5. Higher-order noise shaping: measured, not assumed

Orders 1, 2 and 3 are implemented as exact-rational error-feedback loops with
the binomial coefficients `(1)`, `(2,−1)`, `(3,−3,1)`, so that
`bₙ − xₙ = −Δᵖe` exactly. The literature's promise — faster error decay for
higher `p` — is *not* assumed here, for the reason the v3 audit exists: it is a
promise conditional on the loop staying bounded, and 1-bit high-order loops
need not.

What the file reports for each order and window length is: the plain read-out
error and `N·error`; the error through a triangular (Bartlett) read-out window
and `N²·error`; the worst state excursion `max|e|` observed; and a
**guaranteed** bound on the filtered error, `max|e| · Σ|Δᵖw| / Σw`, computed
from that excursion and the window itself by summation by parts. The bound is
a bound, not a fit.

On the stated five-target set (1/3, 2/7, 5/8, 12345/32768, 7/11):

| order | N | N·(plain err) | N²·(filtered err) | max\|e\| | guaranteed filtered bound |
|---|---|---|---|---|---|
| 1 | 64 | 0.3333 | 7.13 | 0.500 | 3.03 × 10⁻² |
| 1 | 256 | 0.4453 | 2.87 | 0.500 | 7.75 × 10⁻³ |
| 1 | 1024 | 0.4286 | 3.56 | 0.500 | 1.95 × 10⁻³ |
| 2 | 64 | 0.3333 | 2.77 | 0.791 | 3.00 × 10⁻³ |
| 2 | 256 | 0.4453 | 1.44 | 0.884 | 2.14 × 10⁻⁴ |
| 2 | 1024 | 0.4286 | 5.08 | 0.884 | 1.35 × 10⁻⁵ |
| 3 | 64 | 12.0 | 610 | 1,431 | 8.13 |
| 3 | 256 | 38.1 | 11,308 | 111,463 | 40.5 |
| 3 | 1024 | 163 | 234,993 | 14,023,949 | 320 |

Read honestly, that says three things.

1. **The plain time average does not improve with order.** `N·error` stays
   about the same for orders 1 and 2. That is expected: plain averaging is a
   rectangular window, and the summation-by-parts constant for it is `2`
   whatever the order.
2. **The filtered read-out is where order pays, and only while the loop is
   stable.** The *guaranteed* bound falls by more than two orders of magnitude
   from order 1 to order 2 at N = 1024 (1.95 × 10⁻³ → 1.35 × 10⁻⁵), because
   the triangular window's second difference has constant mass while its mass
   grows like `N²/4`. The measured error is well inside that.
3. **Order 3 with these coefficients is unstable, and the file says so.** The
   state grows without bound (`max|e|` reaching 1.4 × 10⁷ at N = 1024), the
   guaranteed bound becomes vacuous, and no decay claim is made. Near the rail
   (target 1/1000) even order 2 runs away — `max|e| = 468.5` at N = 1024 —
   which is exactly the stability caveat the literature attaches to 1-bit
   high-order modulators, measured here rather than assumed away.

So the honest verdict is: order 2 delivers a genuinely better *guaranteed*
filtered read-out on targets away from the rails; order 3, at these
coefficients, does not deliver anything, and the measurement is what says so.

---

## 6. Demand-driven precision

`ExactReal` gains composition — `er_add`, `er_sub`, `er_mul` — with the
requested precision propagated **backwards**, in the spirit of iRRAM and AERN
but with no dependency added: for `x·y` with `|x| ≤ 2^Bx` and `|y| ≤ 2^By`,
`x` is asked for `k + By + 2` bits and `y` for `k + Bx + 2`, which is the least
that still guarantees `2⁻ᵏ` at the top, and the product is rounded at `k+3`.

Measured on `(π + e)·√2` at `k = 64`: demand-driven costs a ledger total of
**152** primitives against **188** for the habit it replaces (every leaf asked
for `k + 32`), a ratio of **0.809** — and both answers are checked against the
reference product for the `2⁻⁶⁴` contract. The saving is modest because the
leaves here are cheap; the point is that the ledger can now *say* what the
discipline is worth instead of asserting that it is worth something.

---

## 7. The decoder is exact, and now proved

v4 argued the exactness of the coset decoder in its docstring and checked it
empirically (no nearer point among the 196,560 neighbours, on every probe).
v5 keeps the empirical check and adds the mathematical core of the argument to
the Lean development:

* `quad_step_bound` — with the residual at most half the class spacing, no
  nonzero multiple of 4 beats the corresponding single ±4 step;
* `quad_zero_bound` — staying put is optimal coordinate by coordinate;
* `coset_cost_ge` — when the mod-8 sum forces an **odd** number of ±4 moves,
  no such move set costs less than the per-coordinate optimum plus the
  smallest single-move penalty;
* `coset_repair_attained` — and a single ±4 move attains that bound.

Together they are the statement the implementation relies on: *inside a coset,
the cheapest single ±4 repair is the minimum*.

The surrounding claim — that the 8,192 cosets exhaust the lattice, so the
winner over them is the *global* nearest point — was the piece left measured
rather than proved. It is now proved too, for a rational target and integer
lattice points:

* `coset_min_cost` — for any point `x` of a Construction-C coset,
  `dist2 y x` is at least `dist2 y n` plus, when the mod-8 sum forces an odd
  repair, the smallest single-move penalty; `n` is any per-coordinate nearest
  member of the coset's residue classes, which is exactly what the script's
  `_tables` builds;
* `coset_min_attained` — a point of the coset achieves that value, so the
  bound is the coset minimum and not merely a lower bound;
* `leech_in_coset` — every Leech point lies in the coset named by its own
  parity and mod-4 mask, so the 8,192 cosets exhaust `Λ₂₄`;
* `lattice_dist_ge` — hence a bound established on every coset is a bound on
  the whole lattice, which is the decoder's minimisation.

`allTwos_inCoset` records that the hypotheses are satisfiable on a coset that
really occurs, so none of the four is vacuous. What remains outside Lean is
the transcription itself: that the Python `_tables`/`nearest` computes the `n`
and the repair these theorems describe, which the self-test checks against an
unpruned exhaustive search on every probe.

---

## 8. What is proved, and what is only measured

| Lean name | what it says |
|---|---|
| `syndromeZero_iff_isGolay` | twelve parity checks decide the Golay code |
| `syndromeSieve_iff_isLeech` | the whole v5 membership test decides `Λ₂₄` |
| `dsAcc_mem_Ico`, `dsAcc_eq` | the accumulator invariant and the count identity |
| `ds_track_bound` | `|average − mean target| < 1/N`, moving target |
| `ds_track_moving_target` | `|average − s| ≤ 1/N + mean deviation` |
| `quad_step_bound`, `quad_zero_bound` | per-coordinate optimality |
| `coset_cost_ge`, `coset_repair_attained` | the cheapest ±4 repair is the minimum |
| `quadQ_step_bound`, `quadQ_zero_bound` | the same, for a rational target |
| `coset_min_cost`, `coset_min_attained` | the decoder's point is the nearest point of its coset |
| `leech_in_coset` | the 8,192 cosets exhaust `Λ₂₄` |
| `lattice_dist_ge` | so the minimum over cosets is the minimum over the lattice |
| `allTwos_inCoset` | those hypotheses are satisfiable, on a coset that occurs |

All are `sorry`-free and depend only on `propext`, `Classical.choice` and
`Quot.sound`.

Everything else in this document is a measurement of *this* script at *this*
commit: 4096 zero-syndrome words equal to the code, 196,560 shell vectors
agreeing on both routes, ledger totals 12 / 50,705 / 217,272, the work ratio
0.218, the NRCI figures, the noise-shaping table, and the audit's
9,461,733 : 180 bytes. They are reproduced by

```bash
python3 glm_zero_storage_substrate_v5.py --test        # the whole self-check
python3 glm_zero_storage_substrate_v5.py --test --full # + the 2²⁴ sweep
python3 glm_zero_storage_substrate_v5.py --ledger      # the cost of each answer
python3 glm_zero_storage_substrate_v5.py --report      # everything, as JSON
lake build RequestProject.GLM.ZeroStorageV5            # the proofs
```

---

## 9. What this licenses, and what it does not

**It licenses** saying that the substrate stores no table: the Golay code, the
octads, the minimal shell, the membership decision, the nearest-point decode
and every constant are generated from 36 bytes of generator rows and the code
in this file, with the membership equivalence *proved* rather than sampled and
the shell comparison run in full before the old route was removed. It licenses
quoting a cost for any of them, because the cost is an exact integer that a
re-run reproduces.

It also licenses calling the decode *optimal*: the coset minimum and the
exhaustion of `Λ₂₄` by the 8,192 cosets are both theorems now (§7), so the
figure the decoder returns is the distance to the nearest lattice point and
not merely the best of a search.

**It does not license** calling the higher-order register better: on the plain
average it is not, and at order 3 it is unstable at these coefficients. It
does not license treating the Lean statements as a proof *about the Python*:
they are about the mathematics the Python transcribes, and the transcription
is checked by the self-test, not proved. And it
does not license reading NRCI as anything but what §3 defines: a normalised
residual, on a named stream, with a proof printed beside it wherever one
exists.

---

## 10. What Mathlib already has — checked, not assumed

The suggestion that `syndromeSieve_iff_isLeech` "belongs in Mathlib" is only
worth entertaining after looking, so the tree was searched rather than
guessed at. The search is over the 7,648 `.lean` files of the Mathlib pinned
by this project's `lake-manifest.json` (rev `8f9d9cff`, toolchain
`leanprover/lean4:v4.28.0`), counting *files* that mention each term
case-insensitively:

| searched for | files |
|---|---|
| `Leech` | 0 |
| `Golay` | 0 |
| `Niemeier` | 0 |
| `sphere packing` / `SpherePacking` / `packingDensity` | 0 |
| `linear code` / `LinearCode` / `binary code` | 0 |
| `sigma-delta` | 0 |
| `Hamming` | 1 (`Mathlib/InformationTheory/Hamming.lean`) |
| `ZLattice` | 14 |
| `covolume` | 8 |
| `QuadraticForm` | 38 |
| `RootSystem` | 26 |
| `ModularForm` | 30 |

So: the ambient theory this development would sit on — `ℤ`-lattices and their
covolume, quadratic forms, root systems, modular forms — is present and
mature. The specific objects are not there at all: no Golay code, no Leech
lattice, no Niemeier classification, no coding-theory layer beyond the Hamming
metric, and nothing on sphere packing or on quantisation. That is the honest
state of the check as of this commit; it is a statement about what a search of
this pinned copy turns up, not a claim about Mathlib in general or about work
in flight elsewhere.

Two consequences for this project. First, nothing here can be phrased by
reusing an existing Golay/Leech definition — `IsGolay`, `IsLeech`, the sieve
and the syndrome all had to be defined in the repository, which is what
`RequestProject/GLM/ZeroStorage*.lean` does. Second, if any of it were ever
offered upstream, the missing prerequisite is not the sieve equivalence but
the layer beneath it: a definition of a binary linear code with a
parity-check/dual pair, on which "self-dual ⇒ generator rows check
membership" is the natural general lemma, and of which the Golay case would
be an instance. The equivalence proved here is the instance, not the theory,
and it is stated against the repository's own definitions.
