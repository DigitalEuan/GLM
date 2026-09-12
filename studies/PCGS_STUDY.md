# Generate, don't store — with a proof attached: the PCGS concept tested here

## Tier 0 — the coarse read

**Question.** How far does "generate, don't store" go once every generated answer has to carry correctness evidence and a cost, and how much of it does the GLM already have?

**Verdict.** Six systems are admitted; three rest on theorems proved here, one on a checked transcription, two on tests.

**Deciding figure.** 6 systems against the 6 admission criteria: 3 proved, 1 a checked transcription, 2 tested.

**Recomputed by.** `glm_universal.reasoning.pcgs.pcgs_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

Code: [`glm_universal/reasoning/pcgs.py`](../overlay/glm_universal/reasoning/pcgs.py),
tests [`glm_universal/tests/test_pcgs.py`](../overlay/glm_universal/tests/test_pcgs.py).
Formal development: [`RequestProject/GLM/PCGS.lean`](../RequestProject/GLM/PCGS.lean).
Sources: [`source_material/pcgs_wider_landscape_v4.txt`](../source_material/pcgs_wider_landscape_v4.txt),
[`source_material/pcgs_wider_landscape.py`](../source_material/pcgs_wider_landscape.py),
[`source_material/pcgs_glm_integration.py`](../source_material/pcgs_glm_integration.py).
Run: `PYTHONPATH=. python3 -c "from glm_universal.reasoning import pcgs; print(pcgs.pcgs_report())"`
from the overlay root, or `python3 -m pytest glm_universal/tests/test_pcgs.py`
(about a second).

---

## 1. What the concept adds to what was already here

The substrate already generates rather than stores. `ZERO_STORAGE_STUDY.md`
removed the Leech tables and `ZERO_STORAGE_V5_STUDY.md` removed the last one —
the 4,096-word Golay set — by deciding membership with twelve parity checks
against 36 bytes, proved equivalent in `GLM.ZeroStorageV5.syndromeZero_iff_isGolay`.
What the supplied scripts propose on top of that is a *contract*:

```
compact description → (answer, correctness evidence, resource evidence)
```

Three things, not one. The answer alone is procedural generation, which the
project already does. The addition is that the answer arrives with something a
reader can check, and with an exact statement of what producing it cost.

Under that contract a system is admitted only if it can say six things:

1. a description materially smaller than the extensional object,
2. a useful direct query that avoids reconstructing the object,
3. a semantic specification independent of the implementation,
4. a proof, a compact certificate, or an explicitly labelled test,
5. a multidimensional resource report,
6. an honest account of when caching wins instead.

Criterion 4 is the one that does the work, and it is the one this study insists
on stating truthfully: *proved*, *checked transcription*, or *tested* — never a
claim of proof for a property that was only sampled.

## 2. The two scripts could not be run, and what was done instead

Neither script runs as supplied. Both import a package `pcgs` from
`/tmp/pcgs_recommended/pcgs_v6_starter`, which is not in the repository, and
`pcgs_glm_integration.py` additionally sets `GLM_ROOT = "/home/z/my-project/GLM"`
and calls `os.chdir` into the missing tree. So "could this be properly tested
here?" has a precondition: the part of them that is mathematics had to be
rewritten against this project's own substrate.

`glm_universal/reasoning/pcgs.py` is that rewrite — standard library only,
`int` and `Fraction` throughout, no RNG, no third-party import — and it is
wired to the Lean development rather than to a printed transcript. The
originals are kept unchanged in `source_material/` as the record of what was
proposed.

## 3. The systems, and the evidence each actually has

| system | compact description | direct query | evidence | kind |
| --- | --- | --- | --- | --- |
| Reed–Muller `RM(1,m)` | one integer `m` | weight and minimum distance without a codeword table | `GLM.PCGS.rmWeight_of_ne_zero`, `rmWeight_of_zero`, `rm_min_distance` | **proved** |
| Golay `[24,12,8]` | twelve rows, 36 bytes | membership as twelve parity checks | `GLM.ZeroStorageV5.syndromeZero_iff_isGolay`, plus the census here | **proved** |
| Cost algebra and physical layer | seven counters, four constants | the energy floor of a measured ledger | `GLM.PCGS.Cost.*`, `bitsErased_reversible`, `landauerEnergy_mono`, `landauerEnergy_le_of_le_log_two`, `ln2Fast_le_log_two` | **proved** |
| Number-theoretic transform | two integers `(p, g)` | `w_k` in `O(log k)`; convolution without a matrix | `GLM.PCGS.ntt_intt` for the definition; the radix-2 algorithm is checked against it | **checked transcription** |
| Sparse stencil operator | the stencil and the dimension | matrix–vector product without the matrix | agreement with the dense matrix on exact rational inputs | tested |
| Finite-state transducer | transition and output functions | the output stream for one input stream | agreement with recomputation at every prefix | tested |

Six systems are admitted; three rest on theorems proved here, one on a checked
transcription, two on tests — 6 systems against the 6 admission criteria: 3
proved, 1 a checked transcription, 2 tested, each labelled with the kind of
evidence it actually has.

### 3.1 Reed–Muller: the weight is forced, so no table is needed

A codeword of `RM(1,m)` is an affine functional `x ↦ c + ⟪a, x⟫` on `𝔽₂^m`. If
`a ≠ 0`, pick a coordinate `i₀` with `a i₀ = 1`; flipping that coordinate is an
involution of `𝔽₂^m` that turns the value of the codeword over, so it matches
the points where the word is `1` with the points where it is `0` one for one.
The two sets cover `𝔽₂^m`, so each has `2^(m-1)` points. That is
`GLM.PCGS.rmWeight_of_ne_zero`; `rmWeight_of_zero` handles the zero word and the
all-ones word, and `rm_min_distance` reads off the minimum distance `2^(m-1)`
for the difference of two distinct codewords.

So the generated code's weight distribution is a theorem rather than a census.
The module enumerates anyway — `code_report` — and the two agree at `m = 2, 3, 4`:
`{0:1, 2:6, 4:1}`, `{0:1, 4:14, 8:1}`, `{0:1, 8:30, 16:1}`. At `m = 4` the
description is **80 bits** against **512 bits** for the codeword table.

**One claim of the source script is false.** It states that `RM(1,m)` is
self-dual "iff `m` is odd". Self-duality needs `k = n/2`, that is
`m + 1 = 2^(m-1)`, which holds only at `m = 3` — the extended Hamming code
`[8,4,4]`. At `m = 5` the code is `[32,6,16]`, dimension 6 against 16, and is
not self-dual. `ReedMullerCode.is_self_dual` decides it rather than asserting
it, and the test pins both directions.

### 3.2 The transform: proved for the definition, checked for the algorithm

`GLM.PCGS.ntt_intt` proves that for a primitive `n`-th root of unity `w` in a
field where `n` is invertible, `intt w (ntt w a) = a` — the transform pair may be
generated from `(p, g)` and never stored. The proof is the orthogonality
relation `GLM.PCGS.root_orthogonality`: `w^j (w⁻¹)^k` is an `n`-th root of unity,
it equals `1` exactly when `j = k` because a primitive root is injective on
exponents below `n`, and a root of unity other than `1` sums to zero over a full
period.

The theorem is about the *definition* `A_i = Σ_j a_j w^{ij}`. What the script
ships, and what this module ships, is the iterative radix-2 algorithm, which is
a different program. That gap is named rather than papered over:
`NumberTheoreticTransform.forward_direct` is the definition,
`NumberTheoreticTransform.forward` is the algorithm, and every input the report
and the tests run goes through both and must agree. The evidence kind is
*checked transcription* — exactly the status the summary already records for the
zero-storage scripts.

Prices, from the same run: mod 17 at length 4 the description is **7 bits**
against **20** for a twiddle table; mod 97 at length 8 it is **10 bits** against
**56**. The measured operation counts equal the declared formula
`(n/2) log n` butterflies at 2 multiplications, 1 addition and 1 subtraction
each — forward `mul 8, add 4, sub 4`; inverse the same plus `n` multiplications
and 2 inversions — which is criterion 5 met by measurement rather than by
assertion.

### 3.3 The cost algebra: why the ledger may be assembled in any order

`Cost` is the script's `CostVector`: six operation counters and one information
counter, replacing "CPU cycles" and "RAM bytes", neither of which is a property
of the computation. Sequential composition is addition, `k`-fold repetition is
scaling, and `GLM.PCGS.Cost.plus_comm`, `plus_assoc`, `zero_plus`,
`algebraicTotal_plus` and `algebraicTotal_scale` are what make a report
assembled stage by stage name the same cost as one assembled in any other order.

The information axis is `bitsFor n = ⌈log₂ n⌉`. `GLM.PCGS.bitsFor_spec` says the
bound is achievable and `bitsFor_min` says nothing smaller is, so `bitsFor_le_iff`
makes it the description bound rather than an estimate. The source script's
`of_vector` fell back to `math.log2` — a float — above 65,536 symbols;
`bits_for_vector` here is exact at every size, and the test checks it at
100,000 symbols.

### 3.4 The physical layer: a better constant, and one comment withdrawn

Landauer's floor is `kT ln 2` per bit erased and the CMOS switching cost is
`½CV²` per gate transition. Three claims are proved here:
`bitsErased_reversible` (a step that loses no information erases nothing, so its
Landauer cost is exactly zero), `landauerEnergy_mono` (monotone in bits erased),
and `landauerEnergy_le_of_le_log_two` — replacing `ln 2` by a rational lower
bound keeps the reported energy a lower bound, which is what licences the
exact-`Fraction` arithmetic in the first place.

The script's rational lower bound is the alternating harmonic partial sum. It is
a valid lower bound, and `GLM.PCGS.ln2Lower_100_le_log_two` checks the constant
it uses — but at a hundred terms it is **0.68817**, wrong in the third decimal
place against `ln 2 = 0.69315`, and *being* a lower bound is a separate fact at
each length. The module replaces it with `ln 2 = Σ 1/(k·2^k)`, whose terms are
all positive, so every partial sum is a lower bound **at once**:
`GLM.PCGS.ln2Fast_le_log_two`, proved for all lengths. At 64 terms the residual
is below `10⁻²¹`, and that is the constant `landauer_per_bit` now uses.

Two further corrections. `thermodynamic_efficiency` in the script returned
`Fraction(0)` both when the ratio is genuinely zero and when there are no
operations at all and it is undefined; here the undefined case returns `None`.
And the comment that an efficiency above 1 "would violate the second law" does
not follow from the model: the CMOS figure is a per-operation engineering
constant of a chosen process, not a physical bound, so a ratio above 1 would
mean the two axes had been measured against incomparable units. The report says
that instead.

At the constants chosen (300 K, 0.7 V, 1 fF) the floor is
`2.85 × 10⁻²¹ J` per bit and the switching cost `2.45 × 10⁻¹⁶ J` per operation:
a ratio of **85,954**, which is the script's "about 10⁵" read exactly.

### 3.5 Caching, priced rather than deprecated

Criterion 6 is the one a "generate, don't store" document is most likely to
skip. `GLM.PCGS.breakeven_iff` states the trade exactly and
`breakevenQueries_spec` proves that `⌈store / (generate − lookup)⌉` is precisely
the query count at which materialising starts to pay. Measured on this module's
own objects:

| object | stored | generate | lookup | break-even |
| --- | ---: | ---: | ---: | ---: |
| `RM(1,4) [16,5,8]` | 512 bits | 5 | 1 | 128 queries |
| NTT twiddles mod 17 | 20 bits | 2 | 1 | 20 queries |
| Golay `[24,12,8]` codeword table | 98,304 bits | 12 | 1 | 8,937 queries |

Read the last row the way the substrate is actually used: a process that decides
membership more than about nine thousand times would, on this accounting, be
better off with the table — which is why `ZeroStorageV5`'s twelve-parity test
matters. It is not a cheaper table, it is a *different query*, at 12 word
operations and no table at all.

## 4. What the GLM already had, and what is new

Already here, and reused rather than rebuilt: the Golay code and its census
(`substrate/mog.py`), Leech membership and the coset decoder
(`substrate/leech2.py`, `reasoning/fwht_decode.py`), the generated-not-stored
audit with its storage ledger (`reasoning/generative.py`), exact real processes
with certified error bounds (`reasoning/exact_real.py` — the script's "exact
constants on demand", already carried further here), and the Delta-Sigma
machinery with its proved tracking bound (`GLM.ZeroStorageV5.ds_track_bound`).
The cross-check in `golay_cross_check` regenerates the code from the twelve rows
and confirms it is the stored one: 4,096 codewords, weight enumerator
`{0:1, 8:759, 12:2576, 16:759, 24:1}`, minimum distance 8, 288 bits of
description against 98,304 of extension.

New with this study: the cost algebra with its proved laws, the information
bound with its proved tightness, Reed–Muller generated with its weight
distribution proved, the transform pair with its inversion proved, the physical
layer with the three claims above, and the break-even theorem.

## 5. What this does *not* establish

* The radix-2 algorithm is not proved — it is checked against the definition
  that is. Proving it would mean formalising bit-reversal and the butterfly
  recursion, and is a candidate for a later round.
* The sparse operator and the transducer are tested, not proved. Both are
  plausible targets: the stencil operator's agreement with its dense matrix is a
  finite identity for each dimension, and the running-mean transducer's
  correctness is an induction on the prefix.
* Nothing here says the concept is *free*. §3.5 is the price list, and two of
  the three rows favour a table at high enough query counts.
* The physical layer prices a *model*. The Boltzmann constant is exact by the SI
  definition, but the temperature, the supply voltage and the gate capacitance
  are stated choices, and the CMOS figure is an engineering constant, not a
  bound.
