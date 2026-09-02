# The unification blueprint, tested

**What this document is.** `glm_unification_blueprint.md` is a specification: it
states, in prose, what the GLM-3+ substrate is and what it does. A
specification that is only read can drift away from the code without anybody
noticing. This study turns it into a **live claim ledger**: every testable
sentence of the blueprint is restated as a claim, recomputed against the
package as it stands, and given a verdict.

Nothing below is quoted from the document. Every figure is produced by the call
that settles it, on demand, by `glm_universal.reasoning.blueprint`. Ask the
running system for it:

```
python GLM.py -q "report blueprint" --verify-tct
```

The ledger's own numbers are re-derived in a fresh interpreter by column 3 of
the Three Column Thinking payload, so the audit is falsifiable in exactly the
way the blueprint asks the rest of the system to be.

---

## The four verdicts

| verdict | meaning |
|---|---|
| **confirmed** | the package reproduces the blueprint's figure exactly |
| **refuted** | the package reproduces a *different* figure; the ledger records what is true instead |
| **not reproduced** | the claim is well posed, but the measurement it names does not show what it says |
| **not implemented** | the claim describes a subsystem the package does not have, so it cannot be tested at all |

## The result

**39 testable claims. 26 confirmed, 9 refuted, 4 not reproduced, 0 not
implemented.**

At the start of this work the count of *not implemented* claims was 2: the
whole thermo-dynamic engine family of Part III existed only as prose. It has
since been built (`glm_universal.reasoning.engine`) and its claims are now
measured rather than deferred, which is why that column is empty.

---

## Section 1 — the Universal Binary Principle

The blueprint states the UBP as a commitment. The ledger tests it as a property
of the source tree: every module of the package is parsed, and the three things
the UBP bans in computation — a float literal, a `float(...)` construction, and
an import of a random, hashing or floating-point library — are counted per
sub-package. A `float` that appears only as the second argument of `isinstance`
is the discipline being *enforced* rather than broken, and is not counted.

* **Confirmed.** All 64 modules of the six sub-packages the discipline is
  claimed for — `substrate`, `data_objects`, `reasoning`, `semantics`,
  `runtime`, `migration` — construct no float and import none of `random`,
  `secrets`, `hashlib`, `numpy`, `scipy`, `decimal`, `statistics`.
* **Refuted, as a claim about the whole package.** 16 modules outside that core
  do construct floats: `capabilities/probes.py` and much of the test suite feed
  floats in precisely to check that they are refused; `evaluation/harness.py`
  times in seconds; `benchmarks/harness.py` fingerprints a run with SHA-256;
  `examples/scaled_carriers.py` is the legacy demonstration that exists to show
  the damage. None of them sits on a computation path — but the ban does not
  reach them, and the ledger says so rather than restricting the scan until the
  claim comes out true.

## Section 2 — the substrate core and the isometric bridge (all confirmed)

| § | claim | figure |
|---|---|---|
| 2.1 | 4,096 cosets, 12,951 minimum-weight leaders | exactly that, leader weights 0–4 |
| 2.1 | unique below radius 4, a sextet at radius 4 | cosets by leader weight `{0: 1, 1: 24, 2: 276, 3: 2024, 4: 1771}` |
| 2.2 | the shipped `LEGACY_TO_CORE` is the document's σ | identical, coordinate for coordinate |
| 2.2 | an isometry, not an automorphism; 8 codewords shared | 8 of 4,096 stay, 4,088 leave |
| 2.2 | stored carriers are canonical; do not permute them | `safe_for_engine_frame_data = False` |
| 2.3 | Construction A: norm 16, kissing 48 | shape `(±4, 0²³)`, 48 vectors |
| 2.3 | Construction B: norm 32, kissing 98,256 | `(±4², 0²²)` 1,104 and `(±2⁸)` 97,152 |
| 2.3 | Construction C reaches 196,560 | plus the odd glue coset `(∓3, ±1²³)` 98,304 |

## Section 3 — the dynamic value layer

* **Confirmed.** The running average of the modulator's trajectory stays inside
  the `1/N` envelope on every one of 20 target/step pairs measured; the worst
  case is `71/226` at `N = 1024`, error `79/115712` against the bound `1/1024`.
* **Not reproduced.** "Recovering exactly `log₂(N+1)` bits" is not an identity.
  The bits actually cleared depend on the target's denominator, and every target
  measured clears strictly *more* than `⌊log₂(N+1)⌋`. `log₂(N+1)` is a floor.

## Section 4 — the thermo-dynamic carrier engine

This is where the work of this round went. The engine family is now assembled
in `glm_universal.reasoning.engine` — seven stages plus the gearbox, all in
exact arithmetic — and reachable as `report engine`.

* **Confirmed.** The baseline engine routes a target through accumulator,
  escapements, snap and trip-lever. On `1/3` over 64 ticks: error `1/192`, drum
  period 2,304 (the least common multiple of 2, 4, 8, 144, 256), 57 escalations.
* **Confirmed.** The radiator works. Four bleeds leave the strain at 0 against
  60 uncooled, and 36 escalations against 57.
* **Confirmed.** Multi-fuel works, and is worth something exact: Heron's
  iteration clears 40 bits at tick 5, the continued-fraction convergents at tick
  16, and the switching strategy at tick 5 — **a 16/5 speed-up over the slower
  fuel**, with one swap. The comparison between fuels is exact, because the
  residual `|x² − r|` is rational and the root itself is never needed.
* **Confirmed.** The turbocharger works: once the strain is over capacity it
  skips 6 of the run's 8 snaps, saving 150 integer operations under the cost
  model the module states in the open.
* **Confirmed.** The gearbox classifies `1/3` as rational (snap skipped),
  `√2` as algebraic (relaxed snap, radiator every 8 ticks) and `π` as
  transcendental (relaxed snap, radiator every 4).
* **Not reproduced: the "2.7× precision leap".** A ratio of precisions means
  nothing until both of its terms are named, and the blueprint names neither.
  Three baselines were measured and all three are reported: against bitwise
  truncation of the target the modulator **loses**, at 7/64; against a one-shot
  hold it wins by 7×; against half its own tick budget it gains between 1 and
  7/6. None of them is 27/10. The figure as written names no measurement.

A second finding of the assembly, worth recording on its own: **the two snap
strengths measure different quantities.** The exact search measures the
distance to the Leech lattice; the certificate path measures the distance to the
nearest Golay-aligned sign pattern. On the same sign carrier the first reads
TAX 0 and the second reads TAX 8. The fast path is a *different reading*, not a
cheaper version of the slow one, and `report engine` says so on its face.

## Section 5 — metrology, coherence and escalation

### 5.1 The PTB/AOO mantissa question

* **Not reproduced.** "10 full bits of mantissa are lost on the very first
  operation." Modelling IEEE-754 binary64 exactly in integers, the stored double
  keeps at least **53** bits of relative precision on every odd prime tested,
  and its significand differs from the exact expansion in at most 3 of 53 bits.
  Nothing near ten bits goes anywhere at step 0.
* **Confirmed.** The period of the expansion of `1/p` is the multiplicative
  order of 2 mod p, exactly computable: 2, 4, 3, 10, 12, 8, 18, 11, 28, 5 for
  the first ten odd primes.
* **Confirmed — and this is where the loss really is.** A double is a dyadic
  rational, so under the doubling map its orbit runs out of bits and dies
  (p = 3 at step 54 of a bound of 54), while the exact orbit has period 2 and
  never terminates. The hallucination origin is the *structure* of the stored
  number, not the size of the first rounding error.
* **Refuted.** "Substrate-faithful for p = 3, substrate-inverted for p = 5."
  While the double still holds information the projections agree to within
  Hamming 23. After the collapse the distance is the exact orbit's own
  projection weight: for p = 3 that is (24, 24), inverted at *every* phase, and
  for p = 5 it is (0, 0, 0, 24), faithful at three phases of four. Both readings
  occur — but they belong to the phase rather than to the prime, and the two
  primes are the other way round.

### 5.2 and 5.3 (confirmed)

The refined NRCI carries all five shells, and on a probe carrier with signs,
unequal tetrads and a non-zero syndrome all five are non-zero. The cumulative
layer stack resolves 3 / 5 / 7 / 7 / 7 of the seven carriers and loses
4 / 2 / 0 / 0 / 0, exactly as the table has it, with
`refinement_chain_intact = True`.

## Section 6 — reversible computing and bit dynamics

* **Confirmed.** BRGC changes exactly one bit per step; the step-size variance
  is 0, so the transition distribution is a point mass and its entropy is
  exactly zero.
* **Refuted: "exactly half the TAX".** Over a full cycle binary counting flips
  `2^(w+1) − 2` bits and Gray counting flips `2^w`, so twice the Gray cost
  exceeds the binary cost by exactly 2 at *every* width. At w = 8: 256 flips
  against 510, ratio 128/255. Half is the limit, never the value. This one is
  proved, not just measured: `GLM.Reversible.gray_two_mul_eq` and
  `gray_not_exactly_half`.
* **Confirmed.** Toffoli and Fredkin are self-inverse and bijective on all eight
  inputs, and 1,600 gate applications forward and back return the carrier at
  Hamming distance 0.
* **Refuted: the syndrome is not conserved.** During the same reversible run the
  Golay syndrome weight takes the values [4, 7]. Reversibility is a property of
  the map, not of the code: a bijection may leave the code and come back.
* **Confirmed.** The kink count is invariant under every rotation
  (`GLM.Reversible.kinks_rotate`) and always even (`kinks_even`).
* **Refuted: not exactly ±2.** Over all 256 circular 8-bit words a single flip
  moves the kink count by `{−2: 512, 0: 1024, +2: 512}` — it leaves the count
  unchanged in exactly half of all cases. Proved as
  `kinks_flip_le` / `le_kinks_flip` together with the explicit unchanged
  witness `kinks_flip_unchanged`.
* **Refuted: the MOG columns.** The MOG frame the substrate carries is 4 rows by
  6 columns, so a column is 4 coordinates and there are 6 of them — not eight
  vertical 3-bit sub-registers. The gate layer is well defined on any partition
  of the 24 coordinates into triples, and the module runs it on both the
  consecutive blocks and a MOG-derived partition.

## Section 7 — the roadmap

* **7.1 closed.** `nearest` now falls back to the molecule formula parser when
  the operand is not one of the register's enumerated names;
  `nearest PbCl2` answers under TCT verification.
* **7.2 confirmed, and proved.** The Griess truncation is not a convention:
  `GLM.VOA.borcherds_commutator_fails` exhibits the axis triple on which the
  truncated commutator formula fails, and `GLM.VOA.form_invariant` records what
  the finite layer genuinely does carry.
* **7.3 refuted as stated.** A constant-time path exists — `fwht_decode`'s
  certificate. It hard-decides the 24 signs, reads the Golay coset leader out of
  the syndrome table, and either proves optimality from the code's minimum
  distance or declines and hands over to the exact route. A table indexed by
  coordinate *prefixes* alone cannot see reliability magnitudes, which is why
  the fast path was given a certificate instead of more stored digits.
* **The headline figures are stale.** "1,324 tests, 6,331 subtests, 27 Lean
  files" is a snapshot. The live counts are generated into `overlay/FIGURES.md`
  by `glm_universal.figures`, which is the only place in the project a test
  count is allowed to be stated; the Lean tree now holds 29 files.

---

## What was built as a result

| what | where | reachable as |
|---|---|---|
| the claim ledger | `overlay/glm_universal/reasoning/blueprint.py` | `report blueprint` |
| the reversible bit-dynamics audit | `overlay/glm_universal/reasoning/reversible.py` | `report reversible` |
| the PTB/AOO mantissa metrology | `overlay/glm_universal/reasoning/mantissa.py` | `report mantissa` |
| the thermo-dynamic carrier engine | `overlay/glm_universal/reasoning/engine.py` | `report engine` |
| the Part V statements, machine-checked | `RequestProject/GLM/Reversible.lean` | `lake build` |
| the §5.1 statements, machine-checked | `RequestProject/GLM/Mantissa.lean` | `lake build` |
| the unregistered-molecule path | `runtime/session.py`, `data_objects/molecules.py` | `nearest PbCl2` |

Bound by `overlay/glm_universal/tests/test_blueprint.py`, which fails if a
verdict changes without the ledger changing with it.
