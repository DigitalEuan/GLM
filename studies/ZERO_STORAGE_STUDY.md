# Generated, not stored — how far the idea goes, and where it has to be checked


## Tier 0 — the coarse read

**Question.** How far does generate-rather-than-store go, and where does it have to be checked?

**Verdict.** The idea is right, and it is measurable.

**Deciding figure.** The proposed Leech sieve is sound and 99.4 % incomplete, with the one-line repair stated.

**Recomputed by.** `glm_universal.reasoning.generative.zero_storage_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

**Instrument:** `overlay/glm_universal/reasoning/generative.py`.
**Report subject:** `report generated` (column‑3 verified in a fresh interpreter).
**Tests:** `overlay/glm_universal/tests/test_generative.py` (16 cases), and the end-to-end case `report-generated` in `overlay/glm_universal/evaluation/cases.py`.
**Lean:** `RequestProject/GLM/ZeroStorage.lean` (sorry‑free).
**Subject of the study:** the proposal in `glm_zero_storage_substrate_v3.txt` —
stop storing the substrate's tables and regenerate them instead.

Every figure below is printed by `report generated`; nothing here is quoted
from prose.

---

## 1. The idea is right, and it is measurable

Membership of Λ₂₄ is three congruences on 24 integers. The 196,560 minimal
vectors are therefore a *consequence*, not data, and holding them is a choice.
The audit puts the two costs side by side and — this is the part that makes the
row worth anything — **checks the regenerated object against the stored one
before emitting the row**.

| object | stored | generator | verified identical |
| --- | ---: | ---: | :---: |
| Golay code, all 4096 codewords | 12,288 B | 36 B (12 rows) | yes |
| 759 octads | 2,277 B | 36 B | yes |
| 196,560 minimal vectors of Λ | 4,717,440 B | 12,288 B (the code) | yes |
| Leech membership decision | 4,717,440 B | 12,288 B | yes |
| **total** | **9,449,445 B** | **24,648 B** | **all verified** |

Ratio **3,149,815 : 8,216**, about **383 to one**. Regeneration is cheap at the
scale that matters: the whole code comes back from its 12 generator rows by
XOR closure, and one membership decision is a pass over 24 coordinates and one
set lookup — no table is consulted at all. No wall‑clock figure is recorded
anywhere in the instrument: the report is emitted through the runtime, whose
traces are required to be byte‑identical between runs, so every quantity in
the table is one a second run reproduces exactly.

**The same question, asked of this repository.** Of the **7,316,334 bytes** the
overlay keeps on disk, **7,296,569** are caches of things it can recompute —
the two Lean address books from the Lean tree, the controller addresses from
the register, the 98,280‑class type‑2 table from the lattice — each stored
beside the digest of the inputs it came from, and only **19,765 bytes** are
primary data the package was given. **99.7 %** of what looks like storage here
is already generation with a cache in front of it.

So the perspective does not need arguing for. What it needs is the discipline
the rest of the project applies to everything else: *a generator is a claim,
and a claim is measured against what it replaces.* The remaining sections are
that measurement, and three of the four proposed generators fail it.

---

## 2. The proposed Leech sieve is sound and 99.4 % incomplete

The script's `is_leech_point` keeps a vector when

* the mod‑2 word is a Golay codeword ("Construction A"),
* **all 24 coordinates agree mod 4** ("Construction B"),
* `Σx ≡ 4m (mod 8)` and an odd‑glue branch ("Construction C").

Run against the kissing shell:

| shape | minimal vectors | kept by the sieve |
| --- | ---: | ---: |
| `(±4², 0²²)` | 1,104 | 1,104 |
| `(∓3, ±1²³)` | 98,304 | 48 |
| `(±2⁸, 0¹⁶)` | 97,152 | **0** |
| total | 196,560 | **1,152** |

* **Sound:** `0` of the vectors it keeps are outside Λ. Proved in general, not
  sampled: `GLM.ZeroStorage.v3Sieve_sound`.
* **Incomplete:** recall `1152/196560 = 8/1365`, about **0.586 %**. A "kissing
  number" of 1152 against 196,560.
* **Exactly why:** the mod‑4 condition of the real Construction C is not "all
  coordinates agree" but *"the coordinates that disagree form a Golay
  codeword"*. The sieve has kept only the two degenerate codewords, the empty
  word and the all‑ones word. That is the content of
  `GLM.ZeroStorage.v3Sieve_iff`: `V3Sieve x ↔ IsLeech x ∧ UniformMod4 x`.
* The survivors are closed under addition and negation
  (`v3Sieve_add`, `v3Sieve_neg`), so the sieve does generate *a* lattice — a
  genuine sublattice of Λ₂₄ — just not Λ₂₄. This is the same failure mode the
  construction ladder already documents at the other rungs: Construction A
  alone is a 48‑kissing packing and a perfectly good lattice.
* A witness, decided by the kernel: `octadVec`, twice the indicator of the
  octad `{0,1,2,3,4,17,21,23}`, has norm² 32, is in Λ (`octadVec_isLeech`) and
  is rejected by the sieve (`octadVec_not_v3Sieve`).

**The repair is one line.** Replace `uniform_mod4` by the codeword test:
`corrected_sieve` in the instrument. It was compared with the package's own
`leech2.in_leech` on **196,656** vectors — the whole shell, plus probe vectors
in general position, **96** of which are outside the lattice — and agreed
**every time**. Same cost: one pass and one lookup.

---

## 3. The snap built on the sieve does not snap

The script's `snap` rounds the target, probes ±1 and then ±2 on one coordinate
at a time, and if nothing survives the sieve, falls back to "round every
coordinate to the nearest even integer" — which it describes as trivially a
Leech point. It is not: `(2,2,0²²)` is even in every coordinate and outside Λ,
because the Golay code has no word of weight 22
(`GLM.ZeroStorage.fallbackVec_not_isLeech`).

Beside it the instrument puts an exact coset decoder: for each of the 4096
codewords and each parity, the nearest point of that coset is computed exactly
(the coordinates are independent inside a coset, and the mod‑8 sum is fixed by
the cheapest single ±4 move), so the winner is the true nearest lattice point.

| probes (4) | script's snap | exact decoder |
| --- | --- | --- |
| general position | **4 of 4 outside Λ**, all via the even fallback; squared distance up to **138** beyond nearest | inside Λ 4/4, squared distance `187/16, 111/8, 207/16, 101/8` |
| half a step from a minimal vector | **3 of 4 outside Λ**; one found at `1/2`, the right answer | inside Λ 4/4, squared distance `1/2` every time |

The decoder's own check is that every answer is inside Λ *and* within the
squared covering radius **16** of its target — the property that separates a
nearest‑point decoder from a merely nearby one. It holds on every probe.

---

## 4. A generated number is only as good as its cost bound

The script's closed‑form constants, measured against the package's certified
`ExactReal` processes at 200 bits (and, for γ, against the published value):

| generator, at the settings the script's own suite uses | bits correct | its own claim | holds |
| --- | ---: | --- | :---: |
| π, Machin, 20 terms | 96 | geometric, no bit count | — |
| e, Taylor, 20 terms | 61 | geometric, no bit count | — |
| √2, Babylonian, 10 steps | 202 | "≈ 2^k bits after k steps" (1024) | no |
| ln 2, alternating, precision = 64 | **9** | "1 bit per term" (256 terms) | no |
| γ, `H_n − ln2·bit_length(n)` | **3** | precision 8 | no |

**0 of the 3 stated accuracy claims hold.** π and e are exactly what they look
like; the other three are not, and γ is not a slow generator but a wrong one —
it approximates `ln n` by `ln 2 · bit_length(n)`, which rounds the logarithm to
an integer and leaves an error of order 0.1 at every precision.

The cost side matters as much. The Babylonian iterate's denominator, in bits,
runs `2, 4, 9, 19, 40, 80, 162, 325, 650, 1301, 2603, 5207` — it doubles every
step, so the module's own default of **64** iterations asks for a denominator
of about 2⁶⁴ bits and cannot be run at all. "Hold the process, not the number"
only works when the process is *parameterised by the precision it is asked
for*, which is precisely the contract of `ExactReal.at(k)`: an answer within
`2⁻ᵏ`, and only as much work as that needs.

The dyadic tower is the same contract in the layer vocabulary, and the Lean
file states it: `dyadic_surrogate_error` — level `n` pins a rational to a
half‑open window of width `2⁻ⁿ`; `dyadic_exact_iff_den_pow_two` — the ladder
terminates exactly on the dyadic rationals and is genuinely infinite for every
other one. One claim of the script does not survive contact:
`dyadic_value_not_strictMono` shows the *readings* are not strictly increasing
(at `q = 1/3` levels 0 and 1 both read 0); what is strictly increasing is the
resolution, which is `GLM.Info.dyadic_boundary_nonempty`, already in
`Tower.lean`.

---

## 5. The "Niemeier portal" is a real invariant with a constant label

At each of the **200** weight‑4 words checked (of 10,626) there are exactly six
codewords at Hamming distance 4 and none closer, and their pairwise distances
are all 8: the sextet is genuine, and the script detects it correctly. What it
does not do is identify a Niemeier lattice — the detector's output takes
**1** distinct value over those words, and a constant separates nothing, so the
printed label `A₁²⁴` is decoration rather than a reading. The instrument that
does read a hole's diagram, from the lattice rather than the code, is
`reasoning/deep_holes.py`, with its extended‑Dynkin marks and completeness
certificate.

---

## 6. What this perspective brings to the GLM

1. **A rule, not a slogan.** *Generate what is a consequence; store only what is
   primary; check the generator against what it replaces, every time.* The
   overlay already lives this way for 99.7 % of its bytes — with digests, so a
   stale cache is reported rather than believed. The audit adds the missing
   half: the check.
2. **The lattice needs no table.** 4.7 MB of minimal vectors is a consequence of
   12,288 bytes of code and three congruences, verified identical. Any part of
   the system that today reaches for a shell can decide membership instead.
3. **A correct generative snap.** `exact_snap` is now in the tree as the
   reference nearest‑point decoder — exact, always inside Λ, always within the
   covering radius — so a "snap" anywhere in the system can be scored against
   it rather than trusted.
4. **A boundary for generated reals.** A process is a number only when its
   error is a function of the work; ungoverned iteration is not zero‑storage,
   it is unbounded storage deferred to run time.
5. **Four theorems where there were four docstrings.** Soundness, the exact
   characterisation of what the sieve generates, the lost minimal vector and
   the unsound fallback are now proved rather than asserted, and the dyadic
   read‑out bound says what a generated number costs to read.

## 7. Follow-up: the refined substrate script

The findings above are now carried by a standalone successor,
[`scripts/glm_zero_storage_substrate_v4.py`](scripts/glm_zero_storage_substrate_v4.py), beside this study — standard library
only, no dependency on the overlay, exact arithmetic throughout. It keeps the
working parts and repairs the rest:

| v3 part | verdict above | in v4 |
| --- | --- | --- |
| Construction A→B→C sieve | sound, 99.4 % incomplete | repaired: the mod-4 word must be a **codeword** (`is_leech`) |
| snap | 3–4 of 4 answers outside Λ | exact coset decoder (`LeechDecoder.nearest`) |
| dyadic tower | correct, one false claim | kept; readings non-decreasing, resolution strictly improving |
| closed-form constants | 0 of 3 accuracy claims hold | `ExactReal.at(k)`: within `2⁻ᵏ`, denominators `k + O(1)` bits |
| Niemeier portal | real invariant, constant label | the **sextet** itself (`sextet_of_tetrad`), label reported as constant |
| Δ-Σ state memory | untested here | rebuilt standalone with its `1/N` read-out bound |

The script generates the Golay code from the quadratic residues mod 11 (36
bytes of generator rows) and stores nothing else. `--test` checks all of it in
about five seconds: the weight distribution 1 / 759 / 2576 / 759 / 1; the
196,560 minimal vectors streamed and all of norm² 32 and accepted; the decoder
inside Λ and within ρ² = 16 on every probe, with **no nearer point among the
196,560 neighbours**, and a half-step target decoding at exactly `1/2`; π, e,
√2, φ, ln 2 and γ meeting their `2⁻ᵏ` contract at k = 8, 32, 96; all 10,626
tetrads giving six-part partitions whose pairwise unions are octads, 1,771
sextets in all; and the storage audit reproducing 9,449,445 → 24,648 bytes.

On the Lean side `GLM.ZeroStorage.refinedSieve_iff_isLeech` proves that the
deterministic form the script computes — parity read off coordinate 0, no
existential, no search — decides exactly `Λ₂₄`.

The v3 draft is kept for the record at
`source_material/glm_zero_storage_substrate_v3.txt`.

## Reproducing

```
python3 studies/scripts/glm_zero_storage_substrate_v4.py --test
python3 studies/scripts/glm_zero_storage_substrate_v4.py --demo
```

```
cd overlay
python3 -c "from glm_universal.reasoning import generative as g; print(g.zero_storage_report(4)['verdict'])"
python3 -m unittest glm_universal.tests.test_generative
python3 -c "from glm_universal.runtime.session import GeometricSession as S; print(S().ask('report generated').answer)"
```

```
lake build RequestProject.GLM.ZeroStorage
```
