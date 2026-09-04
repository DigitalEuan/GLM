# The Geometric Language Machine: A Unified Substrate for Exact Computation, Physical Calibration, and Semantic Reasoning

## A Technical Documentation Paper

**Author:** Euan R. A. Craig (DigitalEuan), Auckland, New Zealand  
**Date:** 02 September 2026  
**Repository:** https://github.com/DigitalEuan/GLM  
**Status:** Working Paper — synthesised from 20+ sub-studies, 1,139 source files, and 1,310 machine-checked theorems

---

## Abstract

This paper documents the Geometric Language Machine (GLM), a cognitive architecture built on the Universal Binary Principle (UBP) — a 24-dimensional computational arrangement constructed from the extended binary Golay code and the Leech lattice. The system rejects floating-point arithmetic entirely, operating instead with exact rational arithmetic over ℚ²⁴, and achieves deterministic, reproducible, and formally verifiable computation.

The complete chain of reasoning from first principles: how a single binary distinction forces the existence of the Golay code at length 23, how the parity extension to 24 dimensions yields the Leech lattice through a three-tiered construction ladder, and how this geometric substrate supports a layered architecture of increasing resolution — from binary parity through integer, rational, Griess algebra, and universal perspectives. Each layer boundary is a theorem, not a design choice: information lost at a boundary is exactly equivalent to new expressive power gained above it.

The system's dynamic value layer represents irrational and transcendental numbers not as static approximations but as infinite processes — deterministic Delta-Sigma feedback loops that converge on the Leech lattice. A family of thermodynamic carrier engines optimises these processes, achieving up to 60-bit precision on exotic constants while maintaining exact arithmetic throughout.

Physical calibration studies anchor the substrate to measured reality: the electromagnetic scale function maps photon wavelengths to substrate units through a linear, Hamming-weight-dependent relationship; a refractive index law emerges from the substrate's symmetry tax without empirical parameters; and dimensionless ratios connecting substrate constants to particle mass ratios achieve precisions of 0.001% to 0.03%.

Application studies demonstrate that encoding chemical elements as 24-bit data objects in the Leech lattice produces element-property correlations exceeding r = 0.90 for electronegativity and boiling point, and that spatial arithmetic operations on these encodings predict bond energies and bond orders with measurable accuracy. A machine-checked semantics on the MOG cube surface builds a complete micro-language — words with physical dimension, true sentences, connectives with measured meanings, and conversation with memory — verified by 1,310 Lean theorems with zero `sorry` placeholders.

Throughout, we distinguish carefully between what is proved, what is calibrated, and what remains open. The paper serves as both a technical reference and an honest accounting of a research programme that spans pure mathematics, computational physics, and artificial intelligence.

---

## Table of Contents

1. [Introduction and Scope](#1-introduction-and-scope)
2. [The Universal Binary Principle: From Distinction to Substrate](#2-the-universal-binary-principle-from-distinction-to-substrate)
3. [The Golay Code and Leech Lattice: The 24-Dimensional Foundation](#3-the-golay-code-and-leech-lattice-the-24-dimensional-foundation)
4. [The Layer Stack: Resolution, Boundaries, and Escalation](#4-the-layer-stack-resolution-boundaries-and-escalation)
5. [Dynamic Value Carriers: Irrationals as Processes](#5-dynamic-value-carriers-irrationals-as-processes)
6. [The Thermodynamic Carrier Engine Series](#6-the-thermodynamic-carrier-engine-series)
7. [Bit Dynamics and Reversible Computing](#7-bit-dynamics-and-reversible-computing)
8. [Higher Lattices: Beyond 24 Dimensions](#8-higher-lattices-beyond-24-dimensions)
9. [Physical Calibration: The Electromagnetic Scale](#9-physical-calibration-the-electromagnetic-scale)
10. [The Speed-of-Light Calibration Study](#10-the-speed-of-light-calibration-study)
11. [Chemistry Applications: Spatial Arithmetic on Elements](#11-chemistry-applications-spatial-arithmetic-on-elements)
12. [The MOG Cube: Encoding and Semantics](#12-the-mog-cube-encoding-and-semantics)
13. [The Leech Lattice Shortcut](#13-the-leech-lattice-shortcut)
14. [Formal Verification: The Lean Development](#14-formal-verification-the-lean-development)
15. [First-Principles Analysis](#15-first-principles-analysis)
16. [The Projection Sub-Seed: Where Seeds Enter](#16-the-projection-sub-study-where-seeds-enter)
17. [Synthesis: What Is Proved, What Is Calibrated, What Is Open](#17-synthesis-what-is-proved-what-is-calibrated-what-is-open)
18. [Conclusion and Open Questions](#18-conclusion-and-open-questions)

---

## 1. Introduction and Scope

### 1.1 What This Document Is

This paper synthesises GLM development research into a single coherent narrative. The source material comprises:

- **20+ sub-studies** in the `studies/` and `source_material/` directories, each addressing a specific aspect of the GLM system
- **Physical calibration studies** in `light/`, covering electromagnetic scale calibration and speed-of-light analysis
- **Encoding experiments** in `data_object/`, testing whether 24-bit Golay/Leech encodings can represent chemical elements and predict their interactions
- **Formal verification** in `RequestProject/` directories across the repository, comprising Lean 4 / Mathlib developments with zero `sorry` placeholders
- **First-principles analysis** in `data_object/FirstPrinciples/` and `data_object/Projection/`, examining what the framework forces, what it chooses, and what must be brought in from outside

The paper is not a copy-paste compilation. Each source document is read, its core claims extracted, and the connections between studies made explicit. Where studies contradict or correct each other, the correction is recorded. Where claims are later audited and found wanting, the audit verdict is given.

### 1.2 The Central Question

The GLM project asks: **Can a computational system built entirely on exact arithmetic over a 24-dimensional geometric substrate reason about physical reality, predict measurable quantities, and support formal verification — without ever resorting to floating-point approximation?**

The answer, as documented across the studies assembled here, is nuanced. The substrate's mathematical structure is genuine and deep. Its layer architecture is formally verified. Its physical calibrations achieve measurable precision. But the gap between calibration and derivation — between fitting constants and predicting them from first principles — remains the central open problem.

### 1.3 Reading Guide

Sections 2–4 establish the mathematical foundations: the binary substrate, the Golay/Leech construction, and the layer architecture. Sections 5–7 describe the dynamic machinery: how continuous values are handled, how computation is optimised, and how bit-level operations preserve information. Sections 8–12 present the applications: higher-dimensional lattices, physical calibration, chemistry, and language. Sections 13–16 document the formal verification and first-principles analysis. Section 17 synthesises the findings into a single proven/calibrated/open ledger.

---

## 2. The Universal Binary Principle: From Distinction to Substrate

### 2.1 The Starting Point

The Universal Binary Principle (UBP) begins from a single axiom: **there exists a binary distinction, and it can be toggled.** Everything else is derived.

This is not a metaphor. The first-principles sub-study (`data_object/FirstPrinciples/FINDINGS.md`) traces the logical chain rigorously:

- **FP-1 to FP-7 (Stage 0):** From "there is a distinction" → the two-element field 𝔽₂ → the state space (ℤ/2ℤ)ⁿ → the toggle group → the Hamming metric. No choices are made; these are forced by the algebra of a two-element ring.

- **FP-8 to FP-12 (Stage 1):** The Hamming metric yields the `2t+1` criterion for unique decoding, the sphere-packing bound, and — the sharpest result — the fact that a *perfect* three-error-correcting binary code can exist only at lengths 7 and 23. This is verified exhaustively for all lengths up to 2,000 inside the Lean kernel.

- **FP-13 to FP-18 (Stage 2):** Ball counting yields the sphere-packing bound. The numbers 7 and 23 are forced, not chosen. The 24 of the "24-bit OffBit" is the parity extension, proved to raise an odd minimum distance by exactly one (7 becomes 8), added for self-duality rather than derived.

### 2.2 The Architectural Commitments

The UBP enforces a strict discipline on all code that operates within it:

| Commitment | Operational Ban |
|---|---|
| No floats (`fractions.Fraction` only) | No SHA-256 hashes |
| Exact arithmetic only | No XOR (except over 𝔽₂) |
| Standard library only | No random seeds |
| Re-derived (falsifiable) facts | |

These are not preferences but structural requirements. The iteration drift study (`source_material/GLM_Iteration_Study.pdf`) demonstrates why: under the accumulative recurrence X_{n+1} = (p+1)/p · X_n − 1/p, a standard IEEE-754 float64 loses all semantic information by step 200 for p = 3 (absolute error ≈ 7.5 × 10¹⁰), while display-truncated floats — simulating AI tool loops — explode to 6.0 × 10¹⁹. The drift is deterministic, not statistical: floating-point "hallucinations" in iterative systems are a hardware consequence, not a model failure.

### 2.3 Three Column Thinking (TCT)

Every runtime solution in the GLM is returned as a synchronised, three-column payload:

1. **Column 1 (Language):** The chain of conceptual reasoning in plain English
2. **Column 2 (Mathematics):** The identical logical steps as exact equations over ℚ, ℤ, or 𝔽₂
3. **Column 3 (Re-Derivation Script):** A dynamically generated Python script that re-executes Column 2 in an isolated subprocess with no shared state

A solution is reported as **VERIFIED True** if and only if the independent re-derivation matches perfectly. This is not testing — it is proof-carrying computation.

---

## 3. The Golay Code and Leech Lattice: The 24-Dimensional Foundation

### 3.1 The Extended Binary Golay Code

The extended binary Golay code is a [24, 12, 8] linear code over 𝔽₂. It has 4,096 codewords, minimum Hamming distance 8, and forms a Steiner system S(5, 8, 24) — meaning any 5 coordinates are contained in exactly one codeword of weight 8 (an *octad*). There are 759 octads.

The code is self-dual: it equals its own dual under the standard inner product. This property, combined with the Steiner structure, makes it one of the most symmetric objects in combinatorics, with automorphism group the Mathieu group M₂₄ of order 244,823,040.

### 3.2 The Leech Lattice via Construction A → B → C

The Leech lattice Λ₂₄ is the unique even unimodular lattice in 24 dimensions with no roots (no vectors of norm 2). It has 196,560 minimal vectors of norm √32, and its kissing number — the number of non-overlapping unit spheres that touch a central sphere — is 196,560.

The GLM constructs Λ₂₄ from the Golay code through a three-tiered congruence ladder over ℤ²⁴ scaled by √8:

**Construction A:** Coordinates are congruent mod 2 to a Golay codeword (x ≡ c mod 2). This yields a lattice of minimal norm 16 with kissing number 48 (the shape (±4, 0²³)).

**Construction B:** Adds the mod-4 even-parity condition (Σxᵢ ≡ 0 mod 4), eliminating the (±4, 0²³) short vectors. Minimum norm rises to 32, kissing number to 98,256 (shapes (±4², 0²²) and (±2⁸) on octads).

**Construction C:** Enforces the mod-8 sum condition (Σxᵢ ≡ 4·(x₀ mod 2) mod 8) and adjoins the odd glue coset (∓3, ±1²³), reaching the complete rootless kissing number of 196,560.

Each condition is proved strictly necessary: removing any one allows short vectors to slip below the minimal norm. The construction is implemented in `substrate/leech_construct.py` and verified in `RequestProject/GLM/HigherLattices.lean`.

### 3.3 The Code-to-Lattice Correspondence

The iteration study maps the broader landscape of error-correcting codes lifted to sphere packings:

| Dimension | Code | Lattice | Kissing | Method |
|---|---|---|---|---|
| 4 | Parity [4,3,2] | D₄ | 24 | Construction A |
| 8 | Ext. Hamming [8,4,4] | E₈ (Gosset) | 240 | Construction A |
| 12 | Ternary Golay [12,6,6] | K₁₂ (Coxeter-Todd) | 756 | Construction A over 𝔽₃ |
| 16 | Reed-Muller RM(1,4) | BW₁₆ (Barnes-Wall) | 4,320 | Construction A |
| **24** | **Ext. Binary Golay [24,12,8]** | **Λ₂₄ (Leech)** | **196,560** | **A → B → C** |
| 32 | Extremal QR [32,16,8] | Q₃₂ (Quebbemann) | 146,880 | Construction A |

The Leech lattice sits at the apex of this ladder in the dimensions that matter for the GLM.

### 3.4 Complete Syndrome Decoding

The GLM replaces legacy brute-force "snapping" with complete syndrome/coset decoding over the 4,096 Golay codewords:

- **Within the packing radius (d ≤ 3):** Unique nearest-codeword recovery with absolute certainty. Proved in `GolayBoundary.lean`: `snap_unique_of_le_three`.
- **At the deep-hole boundary (d = 4):** Exactly six equidistant nearest codewords (the six tetrads of a MOG sextet). The decoder refuses arbitrary choice, marking status as `AMBIGUOUS`. Proved: `snap_ambiguous_at_four`.
- **Beyond the covering radius (d ≥ 5):** By the Steiner system S(5,8,24), a weight-5 error lies at distance 3 from the *wrong* codeword. Silence is a theorem. Status: `UNCORRECTABLE`.

The boundary is a single integer: at weight 3 the substrate's repair is truth; at weight 4 it returns incompatible answers and the question must be escalated.

The Lean proofs in `GolayBoundary.lean` are stated for **any** code of minimum distance 8, not just the Golay code. The combined theorem `snap_boundary_at_three` packages both results: for any two codewords at distance 8, (1) every pattern within distance 3 of a codeword has a unique nearest codeword, and (2) there exists a pattern at distance 4 from both. The witness construction uses `flipOn` (flipping coordinates in a subset of the difference set) with a subset of size exactly 4.

---

## 4. The Layer Stack: Resolution, Boundaries, and Escalation

### 4.1 The Abstract Theory of Layers

The information loss study (`studies/INFORMATION_LOSS_STUDY.md`) formalises the thesis that a system is true up to a point, and past that point a different system takes over. The key insight is that a **layer** is a *resolution* — a function from carriers to views:

```
structure Layer (C : Type u) where
    View     : Type v
    perceive : C → View
```

Everything else derives from `perceive`:

| Notion | Definition | Reading |
|---|---|---|
| `Indist L a b` | `L.perceive a = L.perceive b` | the layer's verdict that two carriers are the same |
| `Refines L' L` | `∀ a b, L'.Indist a b → L.Indist a b` | L' distinguishes at least as much as L |
| `Visible L P` | `∀ a b, L.Indist a b → (P a ↔ P b)` | P is a proposition the layer can state |
| `Boundary L' L` | `{(a,b) | L.Indist a b ∧ ¬ L'.Indist a b}` | what the lower layer loses |
| `capacity L` | `Fintype.card L.View` | how much the layer can hold |

### 4.2 The Three Fundamental Theorems

**Part 1 — A layer is genuinely true within its reach.** `Layer.CongruentOn.mono`: if an operation is computable at a layer's resolution on a region T, it is computable on every subregion S ⊆ T. A law's reach shrinks, never grows; inside its reach it is exactly true.

The precise content of "a law holds at a layer" is the `CongruentOn` predicate: an operation `op` is *congruent* for a layer `L` on a region `S` when replacing operands by carriers the layer cannot tell apart does not change what the layer sees of the result. The theorem `descends_iff_congruent` proves that this is *equivalent* to the existence of a function on views that computes the operation entirely in the layer's own view space. This is the formal content of the GLM's `can_multiply` flag: a layer that cannot multiply is one for which the product is not a function of what the layer sees.

**Part 2 — Loss and gain are the same event.** `Layer.boundary_nonempty_iff_new_visible`: for L' refining L,

```
(Boundary L' L).Nonempty ↔ ∃ P, Visible L' P ∧ ¬ Visible L P
```

Information lost at a boundary is exactly new expressive power. There is no loss without a gain, and no gain without a loss. The proof constructs the witnessing property explicitly: `P(a) := L'.Indist a₀ a` for a boundary pair `(a₀, a₁)` — the property "indistinguishable from a₀ at the higher layer" is visible at L' but not at L.

**Part 3 — The ascent is forced.** `Layer.exists_indist_of_capacity_lt`: a layer whose capacity is smaller than the carrier space *must* conflate two distinct carriers. Loss is not a design defect; it is forced by the dimension count. The converse is also proved: a lossless layer has capacity at least the size of the carrier space (`card_le_capacity_of_lossless`).

**The cumulative guarantee.** `Visible.mono`: every proposition visible at a coarse layer stays visible at every finer layer that refines it. Nothing true below becomes false above, so long as it was expressible below. This is the precise sense in which the tower is cumulative rather than a sequence of revolutions. Combined with the refinement chain, this means any statement the substrate can make remains statable all the way up to the universal layer.

### 4.3 The GLM's Five-Layer Stack

The shipped system implements five perspectives over ℚ²⁴:

| Layer | Perceive | Sees | Capacity |
|---|---|---|---|
| Substrate | 24 parity bits (mod 2) | one bit of parity per coordinate | 2²⁴ = 16,777,216 |
| Integer | 7 SI exponents + substrate parity | integer part + structural bits | unbounded |
| Rational | the exact carrier q ∈ ℚ²⁴ | everything | unbounded |
| Griess | carrier + Griess algebra element | algebraic structure | 196,884 dimensions |
| Universal | carrier + Griess + integer | everything available | unbounded |

Resolution rises monotonically. The rational layer's view *is* the carrier, so nothing above it can gain further resolution. The chain is proved a refinement in `LayerChain.lean`: `GLM.Info.glmChain_refines_of_le`. The specific refinement theorems for each step are:
- `glmIntegerLayer_refines_glmSubstrateLayer` — integer refines substrate
- `glmRationalLayer_refines_glmIntegerLayer` — rational refines integer
- `glmGriessLayer_refines_glmRationalLayer` — Griess refines rational
- `glmUniversalLayer_refines_glmGriessLayer` — universal refines Griess

The rational layer is proved lossless (`glmRationalLayer_lossless`), and the Griess and universal layers inherit losslessness via `cumulative_lossless_left`. The cumulative construction (`Cumulative.lean`) ensures that the integer layer is the **coarsest** reading that keeps both the substrate parity and the SI7 exponents (`glmIntegerLayer_least`): widening adds no resolution beyond what the two views already had.

### 4.4 The Refinement Defect and Its Repair

An earlier version of the integer layer read only the seven SI exponents, discarding the substrate's parity view. This created a refinement hole: the substrate separated a unit-on-coordinate-10 from the vacuum, but the integer layer conflated them. Escalating from substrate to integer *destroyed* a distinction the lower layer already had.

The fix was to **widen** the integer layer rather than narrow the substrate — the choice the project's own account of a cumulative ascent commits to. The shipped `LAYER_INTEGER` carries `substrate_bits` and `hamming_weight` beside the seven `exponents_SI7`. The rejected narrow reading is retained as `LAYER_INTEGER_RAW` to measure the cost: at register scale, the narrow reading conflates 11,176 pairs the substrate already separates.

The defect and its repair are proved as theorems on the real 24-coordinate carriers in `LayerChain.lean`:
- `si7_conflates_unitOutside` — the raw SI7 reading conflates the vacuum and a unit on coordinate 10
- `glmSi7Layer_not_refines_glmSubstrateLayer` — the defect, as a theorem: the raw reading does not refine the substrate
- `glmIntegerLayer_separates_unitOutside` — the repair: the cumulative integer layer separates the same pair
- `boundary_glmIntegerLayer_glmSubstrateLayer_nonempty` — the repair is genuine: the boundary still exists after widening

### 4.5 Escalation at Register Scale

The escalation study (`studies/ESCALATION_STUDY.md`) tests the layer stack on the machine's own data — one carrier per named object of every shipped register:

| Register | Entries |
|---|---|
| Physics | 726 |
| Chemistry | 118 |
| Molecules | 51 |
| Mathematics | 22 |
| Harmonics | 28 |
| Lexicon | 95 |
| **Total** | **1,040** |

Results:

| Layer | Resolves | Loses | Largest Class |
|---|---|---|---|
| Substrate | 415 / 1,040 | 625 | 142 |
| Integer | 544 / 1,040 | 496 | 118 |
| Rational | 757 / 1,040 | 283 | 78 |
| Griess | 757 / 1,040 | 283 | 78 |
| Universal | 757 / 1,040 | 283 | 78 |

The ceiling is 757 distinct carriers under 1,040 named entries. The 283 unreachable entries are almost entirely in physics — 78 are dimensionless ratios (albedo, absorptance, etc.) that share identical 24-coordinate encodings because the register carries no coordinate for *provenance*. The escalation mechanism has nothing left to offer here; a seventh coordinate, not a sixth layer, is what would help.

### 4.6 The Dyadic Tower: An Infinite Ladder

The information loss study exhibits an explicit infinite tower: the *dyadic layers*, where layer n perceives a rational q as ⌊q · 2ⁿ⌋ — resolution 2⁻ⁿ. Three theorems establish its properties:

- **Cumulative:** Every layer refines every layer below it (`dyadic_refines_succ`)
- **Strictly increasing:** Every step has a non-empty boundary (`dyadic_boundary_nonempty`)
- **Exhaustive:** Any two distinct carriers are told apart at some finite level (`dyadic_separates`)

The witness pair at each level n is explicitly constructed in `Tower.lean`: 0 and (2^(n+1))⁻¹ are conflated at level n and separated at level n+1 (`dyadic_witness`). The theorem `dyadic_not_lossless` proves no layer of the tower is lossless.

The concrete three-layer stack (`Stack.lean`) demonstrates escalation on explicit examples:
- `escalate_zero_one`: 0 and 1 are separated at the substrate layer (parity differs)
- `escalate_zero_two`: 0 and 2 require the integer layer (same parity, different integer part)
- `escalate_zero_half`: 0 and 1/2 require the rational layer (both lower layers blind to the fractional part)

The GLM's digit stack (multi-MOG-cube) is the operational form of this tower: plane k is the k-th binary digit, which is the layer that perceives q as ⌊q · 2ᵏ⌋. The stack has no ceiling.

### 4.7 Operational Boundaries: Where Laws Stop Being True

The layer stack's most powerful property is not just that layers see less, but that *laws* stop being computable at certain layers.

**Addition on integer carriers.** On the region of integer-valued carriers `{q | ∃ k : ℤ, q = k}`, addition descends to both the substrate and integer layers (`substrate_congruent_on_integerCarriers`, `integer_congruent_on_integerCarriers`). Within its reach, the substrate is exactly right about addition.

**Addition on all rationals.** Once fractional carriers appear, the same law fails. The witness is a half: `⌊1/2⌋ + ⌊1/2⌋ = 0` but `⌊1/2 + 1/2⌋ = 1`. The substrate and integer layers take the integer part first, and integer-part does not commute with addition. Theorem `substrate_not_congruent_on_univ`: addition does not descend to the substrate on all of ℚ. Theorem `integer_addition_does_not_descend`: no function on integer views can reproduce addition of rational carriers — it is not merely inaccurate but *ill-defined*.

**The rational layer takes over.** `rational_congruent_on_univ`: at the rational layer, addition descends everywhere. `rational_addition_descends`: an explicit function on views exists. The same law, `a + b`, is exactly true at the substrate on integer carriers, ill-defined at the substrate on rational carriers, and exactly true again one layer up. The truth did not change; the domain of definition did.

**The concrete measurement.** On the region `{0, 1/2, 1, 2}` — four carriers chosen to exercise each handoff — the three lowest layers resolve 2, 3, and 4 classes respectively:

| Layer | Resolves | Loses | Boundary witness |
|---|---|---|---|
| Substrate | 2 (even/odd) | 2 | 0 and 2: same parity, different integer part |
| Integer | 3 (integer parts 0,1,2) | 1 | 0 and 1/2: same integer part |
| Rational | 4 (all distinct) | 0 | nothing left to lose |

The escalation examples from `Stack.lean` make this concrete:
- `escalate_zero_one`: 0 and 1 are separated at the substrate layer (parity differs) — no escalation needed
- `escalate_zero_two`: 0 and 2 require the integer layer (same parity, different integer part)
- `escalate_zero_half`: 0 and 1/2 require the rational layer (both lower layers blind to the fractional part)

### 4.8 The TAX Conservation Law

On binary carriers, the symmetry tax satisfies an exact conservation law:

```
TAX(a ⊕ b) + 2 · TAX(a ∧ b) = TAX(a) + TAX(b)
```

where TAX(v) = HW(v) · Y + ‖v‖²/8, with Y = 1/(π + 2/π) ≈ 0.2647.

This is proved from |s Δ t| + 2|s ∩ t| = |s| + |t| on supports (`card_symmDiff_add_two_mul_card_inter` in `TaxConservation.lean`). The support identities `support_bxor` (symmetric difference) and `support_band` (intersection) connect the bitwise operations to set operations. On binary carriers, TAX simplifies to `(#(support a) : ℝ) × Q` where Q = Y + 1/8 (`tax_ofBits`), so the conservation law reduces to the set-theoretic identity.

Raise the carriers from bits to naturals, keeping bitwise XOR and AND, and it fails irreparably. The witness: `w1 = (1)` and `w2 = (2)`, where `1 XOR 2 = 3` and `1 AND 2 = 0`. The left side gives `TAX(3) = Y + 9/8`; the right side gives `TAX(1) + TAX(2) - 2·TAX(0) = Y + 1/8 + Y + 4/8 = 2Y + 5/8`. These are equal iff `Y = 1/2`. Theorem `tax_conservation_at_integer_layer_iff`: conservation for this single pair holds *iff* Y = 1/2 — which is false, since `Y_lt_half` gives Y = 1/(π + 2/π) < 1/2. The boundary is sharp, not gradual: the only value of the GLM's own constant that would save the law is one the constant does not have.

The four coherence regimes are established in `Constants.lean` with exact tax boundaries:

| Regime | NRCI Bound | TAX Bound (proved) |
|---|---|---|
| OnBit | ≥ 0.8 | TAX ≤ 5/2 |
| Coherent | ≥ 0.5 | 5/2 < TAX ≤ 10 |
| Transitional | ≥ 0.3 | 10 < TAX ≤ 70/3 |
| Subcoherent | < 0.3 | TAX > 70/3 |

The vacuum is proved to be OnBit (`regime_zero`). Additional proved properties: Y > 1/4 (`Y_gt_quarter`), Q < 1 (`Q_lt_one`), NRCI is strictly decreasing in TAX (`nrci_lt_nrci_of_tax_lt`), perfect coherence is exactly the vacuum (`nrci_eq_one_iff`), and the zero carrier is the unique carrier of zero tax (`tax_eq_zero_iff`).
# Part II: Dynamic Values, Carrier Engines, and Bit Dynamics

## 5. Dynamic Value Carriers: Irrationals as Processes

### 5.1 The Problem of Continuous Values

A GLM carrier is a 24-tuple of exact rationals (q₀, q₁, ..., q₂₃) ∈ ℚ²⁴. This is a finite point-set carrying finite information. The cardinal geometry study (`source_material/cardinal_geometry_synthesis.md`) proves the wall: **no finite carrier can hold an irrational value.** Natural number addition is disjoint union of point-sets; multiplication is Cartesian product; signed integers emerge via the Grothendieck construction. But √2 cannot be reached by any finite construction of this kind.

The UBP's answer is not to approximate but to **represent irrationals as infinite processes** — limit-converging trajectories that participate in infinite structures without ever being stored statically.

### 5.2 The Delta-Sigma Modulator

The dynamic carrier wiggles around a target x* ∈ [0, 1] using a deterministic error feedback loop:

1. At step n, the error accumulator integrates: e[n] = e[n-1] + (x* − y[n-1])
2. The quantiser (the Golay snap function) forces the value back to the nearest discrete lattice state: y[n] = snap(e[n])
3. The running average (1/N)Σy[n] converges to the target at rate O(1/N), recovering exactly log₂(N+1) bits of precision

This is not an approximation scheme — it is a *representation*. The number is defined by its converging process, not by any finite truncation.

### 5.3 The Wobble as Computation: Beyond Representation

The noise experiment (`studies/NOISE_EXPERIMENT_STUDY.md`) demonstrates that the Delta-Sigma trajectory can do more than represent values — it can *compute*. The key results, all proved in `Cascade.lean` and `Feedback.lean`:

**A loop can chase a signal, not just a constant.** The three core theorems (`mState_mem_Ico`, `mSum_eq`, `mAverage_error_le`) hold for an arbitrary input sequence `u : ℕ → ℝ`, not just a fixed target. The accumulator stays in [0, 1) for *every* input, and the bits track the input's running mean to 1/N. Measured on `square(4, 1/8) + triangle(6, 1/6)` about 1/2 — two tones of different periods beating with period 12 — after 128 ticks: error = 7/1152 ≤ 1/128. The homeostasis does not depend on the target standing still.

**Closed orbits are decidable.** If the input is P-periodic and its sum over one period is a whole number, the accumulator is empty at the end of every period, so state and bits are exactly P-periodic (`mState_periodic`). Whether a wobble settles is a decidable question about the input, answered by deciding rather than by running and looking.

**Cascaded loops buy an order.** The cascade (MASH 1-1) feeds stage one's error into a second loop and recombines the outputs. The identity `casOut_error` shows the instantaneous error becomes a *second* difference of a bounded sequence. Each stage buys one order of convergence.

**Error feedback through a matrix.** `Feedback.lean` generalises the loop to a rational matrix, proving that the state stays bounded and the output tracks the input's running mean at rate ρ/N where ρ depends on the matrix's spectral radius.

### 5.4 The Three Containers of a Constant

Under the GLM, a number is not defined by its rounded decimal digits but by three active containers:

**The Algorithmic Container:** The rational generator and its exact step-complexity cost. Algebraic irrationals (Babylonian/Heron's method) converge quadratically — √2 reaches 50 bits in exactly 5 steps. Transcendental constants converge geometrically — π (Machin's arctangent series) reaches 50 bits in 9 steps at ≈ 2.32 bits/step. Exotic constants like Liouville's number reach 50 bits in 3 steps, while algorithmically random constants (Chaitin Ω surrogate) reveal exactly 1 bit per step and fail to reach 50 bits within 30 steps.

**The Temporal Container (Wobble Signature):** Running each target through a 10,000-step first-order Delta-Sigma modulator produces a unique "vibrational signature":

| Constant | Fractional Target | Wobble Entropy | Autocorrelation (lag 1) | Mean Run Length |
|---|---|---|---|---|
| Ω Surrogate | 0.567143 | 0.980 | −0.671 | 1.20 |
| √2 − 1 | 0.414214 | 0.979 | −0.657 | 1.21 |
| φ − 1 | 0.618034 | 0.959 | −0.528 | 1.31 |
| 1/3 Baseline | 0.333333 | 0.918 | −0.333 | 1.50 |
| e − 2 | 0.718282 | 0.858 | −0.127 | 1.77 |
| π − 3 | 0.141593 | 0.588 | +0.434 | 3.53 |
| Liouville | 0.110001 | 0.500 | +0.560 | 4.55 |
| α (fine-structure) | 0.007297 | 0.062 | −0.007 | 68.49 |
| e^π − π | 0.999100 | 0.011 | −0.001 | 500.00 |

Algebraic irrationals produce highly structured Sturmian word sequences with strong negative autocorrelation at lag 1, indicating rapid quasiperiodic alternation. The fine-structure constant's fractional part produces near-maximum run lengths (137), a signature of extreme structural regularity.

**The Geometric Container (Hull Certificate):** Projecting each constant into a 24-dimensional target vector and testing containment against 150 Leech minimal vectors reveals a sharp boundary. Leech minimal vectors have fixed norm √32 ≈ 5.66. Only Liouville's constant sits inside the hull (norm 0.56, margin −5.38). All other constants scale far beyond the packing boundary (√2: norm 7.16; π: norm 15.92; e: norm 13.77). The system generates an exact separating linear functional — a mathematical proof that no quantiser rule can ever converge to these targets on the substrate from within the hull.

### 5.5 The Digit Stack as the Dyadic Tower

The GLM's multi-MOG-cube (digit stack) is the operational form of the information loss study's dyadic tower. Each plane k is the k-th binary digit — the layer that perceives q as ⌊q · 2ᵏ⌋. The full stack of planes represents the exact rational value. The stack is infinite in principle: any rational can be stacked to arbitrary depth, and the mechanism has no ceiling.

### 5.6 How the GLM Works with Infinite Values

The cardinal geometry study proves that bare point-sets in ℝ³ can only hold non-negative, finite information. Natural number addition is disjoint union; multiplication is Cartesian product; signed integers emerge via the Grothendieck construction (a pair (P, Q) of non-negative point-sets, value = |P| − |Q|, sign emerging from which stockpile survives annihilation). But irrational numbers cannot be reached by any finite construction of this kind.

The GLM's carriers are not bare point-sets — they are *anchored* to infinite structures:

| Structure | Finite or Infinite? | What the Carrier's Participation Gives |
|---|---|---|
| Leech lattice Λ₂₄ | Infinite | Nearest lattice point, class, norm², is_2a_axis — one of 98,280 type-2 classes |
| Golay code [24,12,8] | Finite (4,096 words) | Plane-0 mask, Golay alignment, facet signature, Steiner system S(5,8,24) |
| Griess algebra V₂ | Finite (196,884 dims) | Projection onto a 2A axis, Griess norm, product with other carriers |
| Moonshine module V^♮ | Infinite | Grade (which Vₙ it lives in) — j-function coefficient |
| Dyadic tower (digit stack) | Infinite | Resolution at each depth — each plane is one layer of the tower |

**Irrationals as limits of the dyadic tower.** √2 cannot be any finite plane stack. But the *sequence* of plane stacks converges to it:

```
depth 1: ⌊√2 · 2¹⌋ = 2      → carrier ≈ 1.0
depth 2: ⌊√2 · 2²⌋ = 5      → carrier ≈ 1.25
depth 3: ⌊√2 · 2³⌋ = 11     → carrier ≈ 1.375
depth 4: ⌊√2 · 2⁴⌋ = 22     → carrier ≈ 1.375
depth 5: ⌊√2 · 2⁵⌋ = 45     → carrier ≈ 1.40625
```

The GLM doesn't store the limit; it stores the *process* (the stack mechanism). Each depth is a finite carrier; the sequence of depths IS the irrational.

**The Griess product as a non-associative tower.** The Griess algebra's non-associativity — (a·b)·c ≠ a·(b·c) — generates an infinite tower of higher products:
- Level 1: the bilinear product a·b (the Sakuma relation)
- Level 2: the trilinear form ⟨u·v, w⟩ (operational since v0.5.3)
- Level 3: the quadrilinear form ⟨(u·v)·w, x⟩ (not yet computed)
- Level ∞: the vertex operator Y(u, z) = Σ uₙz⁻ⁿ⁻¹ (the VOA state-field map)

Each level is a *new operation* that the previous level cannot express — the information loss study's "boundary = new expressive power" in action.

**The Moonshine module as an infinite q-series.** V^♮ = V₀ ⊕ V₁ ⊕ V₂ ⊕ ... with graded dimensions 1, 0, 196884, 21493760, .... Each Vₙ is finite, but the series is infinite. The GLM has the first 11 coefficients (v0.6.0). The infinite lives in the fact that the series never terminates.

The cardinal geometry synthesis states this precisely: "The carrier (outside) is finite. The relationships (inside) are infinite." The carrier is a finite projection of an infinite structure. The digit stack is the bridge between them.

---

## 6. The Thermodynamic Carrier Engine Series

### 6.1 The Thermo-Dynamic Carrier Engine (TDCE)

To optimise the execution of Delta-Sigma loops, the GLM models computation as a physical, thermodynamic system. The baseline TDCE routes continuous targets through a four-stage mechanical analogue:

1. **Stage 1 — Delta-Sigma Accumulator:** An exact rational integrator capturing residual error displacement
2. **Stage 2 — Modular Escapements:** A 5-bit structural parity filter (residues at mod 2, 4, 8, 144, 256) representing the physical rings of the MOG, the Construction ladder, and the digit stack byte
3. **Stage 3 — Leech Lattice Snap:** Projects the coordinate vector to Λ₂₄, calculating local thermodynamic strain as TAX = d²/32
4. **Stage 4 — Escalation Trip-Lever:** Lifts the processing plane to a higher dimension when local strain overflows capacity

The TDCE achieves full 60-bit precision on exotic constants (Champernowne, Ω surrogate) where the naive baseline stalls at 21–22 bits — a 2.7× improvement. However, it is approximately 22× more expensive in integer arithmetic operations.

### 6.2 The Optimisation Stack

Three advanced stages resolve the TDCE's computational overhead:

**Radiator (Cooling):** A periodic heat-sink that bleeds off accumulated TAX strain every N steps, preventing premature escalation events. This reduces the TAX on a π run by 15,000×.

**Multi-Fuel (Parallel Generators):** Runs two distinct generators in parallel (e.g., Newton's method and continued fractions for √2) and dynamically swaps to the faster-converging path at each tick, utilising cached trajectories.

**Turbocharger (Adaptive Snapping):** Adapts the snapping strategy on the fly based on current strain:
- *Tight snap* (|e| < 1): evaluates the local space
- *Relaxed snap* (1 ≤ |e| < 4): evaluates a coarser grid
- *Skip snap* (|e| ≥ 4): bypasses search entirely, preserving CPU cycles

### 6.3 The Optimal Engine and Gearbox

The culmination integrates all six stages under a runtime **Gearbox Classifier** that identifies the incoming target's class (Rational, Algebraic, Transcendental, or Exotic) and shifts configurations dynamically. The Optimal Engine achieves **100% TCT verification** — all 15 complex workloads (including π + e and √2 × φ) pass independent re-derivation in a fresh subprocess, with 10 of 15 reaching full 60-bit precision.

### 6.4 The Refractive-Index Law

The engine series produces a concrete physical prediction. A region whose states carry TAX T needs 24 + T ticks per cell, yielding:

```
v(T) = 27c / (24 + T)       n(T) = (24 + T) / 27
```

Causality forces the vacuum TAX to be the minimum of the tax spectrum. On the Golay layer, the octads uniquely minimise the codeword tax at 8Y + 1 = 3.1174, giving the "24 bits + 3 TAX = 27 ticks" structure.

The law is falsifiable: if TAX is bounded by 24, then n ≤ 16/9 = 1.778. Water (T = 11.99), glass (T = 17.0), and sapphire (T = 23.7) satisfy this; diamond (T = 41.3) does not. This is the concrete experimental content of the idea.

---

## 7. Bit Dynamics and Reversible Computing

### 7.1 Standard Binary vs. Gray Code

Standard binary counting creates high-amplitude "transition cliffs" where multiple bits roll over simultaneously (e.g., 011 → 100). This generates massive local noise. The bit reversibility study compares standard binary against Binary Reflected Gray Code (BRGC) over 10,000 steps:

| Metric | Standard Binary | BRGC (Gray) | Ratio |
|---|---|---|---|
| Mean transitions per step | 1.9946 bits | 1.0000 bit | 1.99× reduction |
| Max transition cliff | 11 bits | 1 bit | 11× reduction |
| Transition Shannon Entropy | 1.9939 bits/symbol | 0.0000 bits/symbol | Complete collapse |
| Cumulative Symmetry TAX | 7,791.56 units | 3,896.75 units | ≈ 2:1 |

BRGC guarantees exactly one bit flip per step (`gray_step`: consecutive Gray codes differ by a power of two, proved in `Reversible.lean`), and zero transition entropy. **Correction:** The claim that Gray "dissipates exactly half" is **false at every finite width**. The sharp statement, proved as `gray_two_mul_eq`, is `2 * grayCycleFlips w = binaryCycleFlips w + 2`: Gray costs one step more than half, and exactly half only in the limit. The theorem `gray_not_exactly_half` confirms this for all finite w. It remains the mathematically optimal read channel.

### 7.2 Logically Reversible Gates

Classical logic gates (AND, XOR) are lossy, permanently erasing state information and dissipating a minimum of kT ln 2 of heat under Landauer's Principle. The GLM enforces reversibility by partitioning the 24-coordinate MOG frame into eight vertical 3-bit sub-registers and running bijective, self-inverse gates:

- **Toffoli Gate (CCNOT):** [c₁, c₂, c₃] ↦ [c₁, c₂, c₃ ⊕ (c₁ ∧ c₂)] — proved involutive (`toffoli_involutive`, verified by `decide`) and bijective (`toffoli_bijective`)
- **Fredkin Gate (CSWAP):** [c₁, c₂, c₃] ↦ [c₁, c₃, c₂] if c₁ = 1 — proved involutive (`fredkin_involutive`) and bijective (`fredkin_bijective`)

**Important detail from the Lean proofs:** The composition `round = fredkin ∘ toffoli` is **not** an involution (`round_not_involutive`). Instead, it has order 3: `round³ = id` (`round_cubed`). This means a run of rounds must be undone by the inverse round (`roundInv = toffoli ∘ fredkin`), not by repeating itself. The inverse satisfies `roundInv ∘ round = id` and `round ∘ roundInv = id` (both proved). The 100-operation test runs forward rounds then inverse rounds, returning a final Hamming distance of **exactly 0** — byte-identical starting state. The Refined NRCI and Golay syndrome weight are perfectly conserved throughout.

### 7.3 Topological Defect (Soliton) Storage

Information can be encoded as topological defects — solitons or phase kinks — propagating along 1D cyclic lattice strings rather than as static coordinates:

- **Kink definition:** A boundary where adjacent coordinates differ (vᵢ ≠ vᵢ₊₁, with cyclic wrap)
- **Conservation:** Across 20 random vectors, the kink count is perfectly conserved (20/20 PASS) under 9 cyclic rotations (shifts of 1, 3, 5, 7, 11, 13, 17, 19, and 23 coordinates)
- **Soliton injection:** A single coordinate bit flip moves the kink count by an even amount in `{-2, 0, +2}`. **Correction:** The claim of "exactly ±2" is too strong. The Lean theorem `kinks_flip_le` proves `kinks(flipAt v j) ≤ kinks(v) + 2`, and `le_kinks_flip` proves the reverse bound. The theorem `kinks_flip_unchanged` exhibits a concrete case (on `0001`, flipping coordinate 0) where a flip changes nothing at all — it destroys one kink and creates another. The theorem `kinks_flip_drops_two` exhibits the case where the count drops by 2. The kink count is always even (`kinks_even`), so the change is always even, but it can be zero.

This makes the represented meaning immune to coordinate-level rotational noise — the kink count is a topological invariant under rotation (`kinks_rotate`), and it is always even.

### 7.4 Persistent Homology of Perturbations

Mapping birth/death times of topological features (loops, voids, cavities) around lattice perturbations on persistence diagrams clusters 100 random carriers (50 physics, 50 chemistry) into their correct semantic domains with **100% classification accuracy**. The topological signature of a carrier is sufficient to determine its domain without reading its raw coordinates.

---

## 8. Higher Lattices: Beyond 24 Dimensions

### 8.1 The Question

Everything spatial in the GLM lives in 24 dimensions. The higher-lattice study (`studies/HIGHER_LATTICE_STUDY.md`) asks: what is above it, and is anything up there useful?

### 8.2 The 32-Dimensional Barnes-Wall Lattice

Construction A over a binary code always contains 2eᵢ (norm 2), so a single-level binary lift can never have minimum 4 in 32 dimensions. The fix is a *two-level* lift — Construction D — over a nested pair of Reed-Muller codes RM(1,5) ⊂ RM(3,5):

```
x = 4a + 2b + c     c ∈ RM(1,5),  b ∈ RM(3,5),  a ∈ ℤ³²
```

The minimum is 16 (extremal for dimension 32), the kissing number is 146,880, and the lattice is unimodular.

**What 32 dimensions buy:** A Leech address is flat — the mod-2/mod-4/mod-8 sieve is a membership test that cannot be decomposed into usable resolutions. Construction D is different: its three levels are genuinely nested lattices, each an honest quotient of the next:

```
4ℤ³²  <  4ℤ³² + 2·RM(3,5)  <  4ℤ³² + 2·RM(3,5) + RM(1,5)
```

Truncating to the first k levels gives exactly the nearest point of the k-th nested lattice. This provides **three usable resolutions** where Λ₂₄ provides one — a coarse address that is usable on its own and refinable later.

### 8.3 The 48-Dimensional Ternary Lattice

Binary runs out at 48 dimensions. The fix: move to 𝔽₃. The Pless symmetry code C(23), generated by [I₂₄ | S] with S the bordered Jacobsthal matrix of the prime 23, is self-dual and doubly even with minimum distance 15.

A four-step ladder produces an even unimodular lattice with minimum 6 (extremal for dimension 48) and centre density exactly (3/2)²⁴ — approximately **16,834 times** more dense per unit cell than the Leech lattice. This number is the whole motivation for the climb, and it is an exact rational.

The cost: no Golay code, no MOG, no octads — an 𝔽₃ code and a neighbour step instead. The binary picture is abandoned entirely.

### 8.4 Delta-Sigma Against a Shell

The Delta-Sigma machinery always emits from a small alphabet. What happens when the alphabet is 196,560 points on a sphere?

**Rule 1 — Nearest, over the whole lattice:** With a quantiser of covering radius ρ, the running mean tracks any target at ρ/N. The Leech lattice covers, so nothing is out of reach. Measured: error |mean − t|² = 1/9 ≤ bound 1/9.

**Rule 2 — Matched, over one shell:** Emit the shell point the accumulator points at hardest (the argmax of the support function). The replacement for a covering radius is a *margin* μ: the support function beats the target by μ‖s‖ in every direction. Then the accumulator never leaves the ball of radius D²/(2μ) + D, and the error falls as B/N. Measured: error falls as 1/N, accumulator is bounded while N grows.

**The wall:** For a target outside the hull (5e₀), the support function h(e₀) = 4 < ⟨e₀, t⟩ = 5. This is a one-line exact separating certificate that no rule emitting from the shell can ever reach the target. The accumulator grows linearly at exactly the predicted rate of 1 per tick.

**Temperature without randomness:** The hard snap is replaced with a temperature-weighted Gibbs ensemble among candidates, realised not by sampling but by the same error-feedback accumulator. The trajectory *is* the distribution: visit frequencies converge to Gibbs weights at rate (m−1)/N. At t = 1 the frequencies are exactly uniform; as t rises the ensemble concentrates on the nearest candidate.
# Part III: Physical Calibration, Chemistry, and Applications

## 9. Physical Calibration: The Electromagnetic Scale

### 9.1 The Scale Function

The UBP substrate does not have a single scale number — it has a scale **function** that maps each photon's wavelength (continuous) through its Hamming weight class (discrete) to a substrate-unit-to-meters conversion. The EM calibration study (`light/EM_calibration_1/`) establishes:

```
S(λ, HW) = λ / [HW × (Y + 1/8)]

where Y = 1/(π + 2/π) ≈ 0.2647

  HW=8:   S = λ / 3.1174   (gamma/X-ray/EUV regime)
  HW=12:  S = λ / 4.6761   (optical/IR/microwave regime)
  HW=16:  S = λ / 6.2348   (radio/ELF regime)
```

This is not curve-fit. It is derived from the substrate's definition: the symmetry tax of a Golay codeword of weight w is TAX = w × (Y + 1/8), and the scale factor converts substrate units to real meters through this tax.

### 9.2 Five Confirmation Tests

**Test 1 — Linearity (EXACT):** Within each HW class, S = k × λ is confirmed to machine precision. S/λ = 1/TAX_HW is exactly constant for all photons in each class. This is a mathematical identity.

**Test 2 — Scale constants derived:**
- HW=8: k = 0.3208 (1 substrate unit = λ/3.12 meters)
- HW=12: k = 0.2139 (1 substrate unit = λ/4.68 meters)
- HW=16: k = 0.1604 (1 substrate unit = λ/6.23 meters)

**Test 3 — Invertibility:** The scale is invertible for HW=16 (radio/ELF), where codeword_index correlates with log₂(f) at r = −0.71. For HW=8 and HW=12, the encoding saturates and the scale is not invertible from substrate alone.

**Test 4 — Continuous within HW=16:** The radio/ELF regime has a continuous scale within the HW class — 7 of 8 photons have distinct codewords, and the codeword index tracks log₂(f). This means for radio frequencies, the substrate has a continuous (not just discrete) scale.

**Test 5 — Anchor validation:** The 190 kJ/mol anchor matches three visible-light photons (HeNe at 188.98 kJ/mol, Na D2 at 203.08, H-alpha at 182.28) — all in the regime where visible photon energy (~200 kJ/mol) matches chemical bond energies, explaining why visible light drives photochemistry.

### 9.3 What the GLM Can Do with EM Data

For any encoded EM photon, the GLM can:
1. Determine HW class → regime (gamma / optical / radio)
2. Look up the scale constant k = 1/TAX_HW
3. Compute the scale S = k × λ → meters per substrate unit
4. For HW=16 (radio): use codeword_index to estimate λ from substrate alone
5. For HW=8, 12: the scale is discrete (3 levels) but linear within each level

---

## 10. The Speed-of-Light Calibration Study

### 10.1 The Chain

The lightspeed study (`light/aristotle_01/`) constructs a chain from chemistry data through quantum mechanics to a cell length:

1. **Work energy:** E₁(κ) = κ/N_A, where κ = 190 kJ/mol (fitted from 114 element pairs)
2. **Tick:** τ(κ) = h/E₁(κ) = h·N_A/κ — the Planck-Einstein period of a quantum of energy E₁
3. **Tick budget:** ν(T) = 24 + T (24 bit-shifts plus T ticks of TAX overhead)
4. **Cell duration:** T_cell = ν(T)·τ
5. **Cell length:** ℓ_cell = c · T_cell = (24+T)·c·h·N_A/κ

At κ = 190 kJ/mol, the one-work-unit photon is red visible light (λ₁ = 629.6 nm), and the cell is 27 of its wavelengths: ℓ_cell = 17.0 μm.

### 10.2 What Is Proved and What Is Not

The study's headline claim — "the speed of light is not an input constant, it's an output" — is **false**. Theorem 2 (circularity): ℓ_cell/T_cell = c identically, for every κ and every tick budget. A quantity returned unchanged whatever the inputs were is not being predicted.

Theorem 3 (dimensional no-go): there are no integers a, b with a·(1,2,−1) + b·(1,2,−2) = (0,1,−1). An action and an energy determine a time, not a speed. The chain would become a genuine derivation of c if and only if the substrate predicted ℓ_cell independently of c. It does not.

**What survives:** The refractive-index law n(T) = (24+T)/27 contains no κ, no h, no N_A, no c — it is purely a statement about the substrate's tick accounting, and it is falsifiable. Causality forces T₀ to be the minimum TAX (Theorem 6), and on the Golay layer the octads uniquely minimise the codeword tax at 8Y + 1 = 3.1174 (Theorem 8).

### 10.3 The Alignment Points

Re-measured with exact rational arithmetic and machine-checked in Lean:

| Point | Formula | Value | Target | Relative Error |
|---|---|---|---|---|
| P2 | 169/WOBBLE | 206.708 | 206.768 | 0.02938% |
| P7 | 220 − 83 + L | 137.063 | 137.036 | 0.01962% |
| P8 | 1836 + 2L_s | 1836.152 | 1836.153 | 0.0000374% |
| P4 | Y²·WOBBLE·24⁴·29⁴·hΔν_Cs/c² | 9.109×10⁻³¹ kg | 9.109×10⁻³¹ | 0.00919% |

**Corrections to the original synthesis:**
- P4's residual is 0.00919%, not 0.007% as originally quoted
- P6 (MONAD/13 = 1 + L) is a tautology — it is the definition of L rewritten
- P5 holds on the Golay layer only; among Leech minimal vectors, class A (∓4², 0²²) has lower tax than octads

### 10.4 The Honest Statement

The substrate supplies dimensionless numbers; the SI supplies the dimensions. Every alignment point has the form: measured quantity ≈ (dimensionless substrate number) × (SI-defined unit). The lightspeed chain is a *calibration*, not a derivation, and it is only as good as the 190 kJ/mol fit.

---

## 11. Chemistry Applications: Spatial Arithmetic on Elements

### 11.1 The Encoding

The encoding experiment (`data_object/encoding_definition_attempt_04.08.26/`) tests whether 118 chemical elements can be encoded as 24-bit data objects in the Leech lattice, and whether spatial arithmetic operations on these encodings predict real chemistry.

Each element is encoded using four properties mapped to the MOG grid:
- Electronegativity (EN × 10)
- Boiling Point (BP ÷ 40)
- Melting Point (MP ÷ 40)
- Density (Rho × 10)

### 11.2 Element Property Prediction

The encoding preserves element identity with high fidelity:

| Property | Correlation (r) | Verdict |
|---|---|---|
| Electronegativity | 0.92 | Excellent |
| Boiling Point | 0.95 | Excellent |
| Melting Point | 0.87 | Strong |
| Density | 0.82 | Strong |

### 11.3 Bond Energy Prediction

The core problem: element Data Objects are fixed per element. O=O and O-O produce identical codewords because the encoding captures element identity, not bond context. The solution is **bond order warping** — modifying the codeword based on bond order using Golay column permutations, creating distinct spatial sectors in the 24D lattice for single, double, and triple bonds.

**The warping mechanism:**
- Bond Order 1 (single): codeword unchanged
- Bond Order 2 (double): swap MOG columns 2↔3 in each row
- Bond Order 3 (triple): swap MOG columns 2↔3 AND 4↔5 in each row

This ensures that O-O (single) and O=O (double) land on different sectors of the 24D lattice, while preserving Golay structure (column swaps are valid MOG operations).

**The flip_activation strategy** (flipping bits 12-17, the Activation row, for multi-bond pairs) proved most effective. The Activation row encodes melting point (MP); flipping these bits for double/triple bonds creates a distinct geometric signature because higher bond orders correlate with different melting point patterns.

Testing 114 element pairs with 5-fold cross-validation:

| Method | Bond Energy r | Bond Order Accuracy | Notes |
|---|---|---|---|
| Linear (no features) | 0.01 | — | No signal |
| Linear (with BO feature) | 0.74 | — | BO as feature works |
| Random Forest (identity) | 0.10 | 81.6% | Baseline |
| Random Forest (column swap) | 0.31 | 83.3% | Warping helps |
| Random Forest (flip activation) | 0.44 | 86.8% | Best single warp |
| **rotate_3 + flip** | **0.55** | **86.8%** | **Best combined warp** |

### 11.4 The Activation Row as Bond Formation Layer

The strongest single feature in the entire experiment is `diff_A` (Activation row difference) at r = 0.50. The Activation row encodes melting point — elements with different melting points form stronger bonds. This is not a statistical artefact; it is a structural property of how the MOG grid encodes physical processes.

**The snap energy signal** is a key finding. The snap process — where a mid-point between two element codewords resolves to the nearest Golay codeword — behaves differently for different bond types:

| Bond Order | Mean Snap Energy | Interpretation |
|---|---|---|
| 1 (single) | −0.171 | **Releases** energy |
| 2 (double) | +0.117 | **Absorbs** energy |
| 3 (triple) | +0.234 | **Absorbs** more energy |

Single bonds release energy when snapped; triple bonds absorb it. This is a real, monotonic signal. The snap process is part of the interaction mechanism, not just post-processing.

Additional features carry independent signal:
- **Tortuosity** (path winding through Leech space): r = 0.36, partial r = 0.33 independent of mass
- **Geometric work** (path integral of settlement dynamics): r = 0.35
- **overlap_A** (Activation row overlap): r = −0.35 for bond energy
- **cross_strength** (element interaction strength): r = −0.22

**The three-column diagnostic** (`geometric_work.py --diagnose SYM_A SYM_B BO`) outputs aligned Language/Math/Script columns for any bond:
```
Step 1: PERCEPTION — element codewords and properties
Step 2: WARPING — graduated Activation flip based on BO
Step 3: INTERACTION — AND/XOR metrics with warped codeword
Step 4: SETTLEMENT — geometric work (path integral)
Step 5: PREDICTION — calibrated to kJ/mol
```

### 11.5 The 190 kJ/mol Scale Factor: Status, Limits, and Open Issues

The constant κ = 190 kJ/mol is the **only empirical number** in the entire calibration chain. Every downstream quantity — the tick duration (τ = h·N\_A/κ), the cell length (ℓ\_cell = 27·c·h·N\_A/κ), and the EM scale constants — is exactly proportional to 1/κ. This makes κ the single most load-bearing assumption in the physical calibration, and its status deserves careful, unsentimental statement.

**What κ is.** Fitted from 114 chemical element pairs against tabulated bond dissociation data. The fit assigns one unit of "geometric work" (the path integral through Leech space during bond settlement) to approximately 190 kJ/mol of real bond energy. The supporting dataset is not in this repository, so the fit itself could not be independently re-run, and — critically — the thermodynamic convention used for the 114 pairs (0 K dissociation energy D₀, 298 K enthalpy ΔH₂₉₈, or a mixture) has not been stated.

**The 190-vs-193 question is a convention issue, not a residual.** The commonly quoted Br₂ bond dissociation enthalpy at 298 K is ΔH₂₉₈ ≈ 192.8 kJ/mol. The bond dissociation energy at 0 K is D₀ ≈ 190.2 kJ/mol. The two differ by the thermal correction, ≈ 2.6 kJ/mol — which is exactly the discrepancy previously reported as a "1.6% miss." If the 114-pair fit was performed against D₀ values, then κ = 190 coincides with the 0 K Br–Br dissociation energy to within rounding, and the original claim of near-exact agreement was closer to correct than the softening suggested. If the fit used 298 K enthalpies throughout, then every comparison in this section is off by a small but systematic thermal offset. Either way, the fix is the same: state which convention the dataset uses and compare like with like. Until that is done, no percentage agreement quoted against a single tabulated number is meaningful.

**The reference data are not homogeneous.** O=O (498 kJ/mol) and N≡N (946 kJ/mol) are genuine diatomic dissociation energies: well-defined, directly measurable quantities. C–C (347 kJ/mol) and C=O (799 kJ/mol) are *mean bond enthalpies* — model-dependent bookkeeping averages over many molecular environments. The actual C–C dissociation enthalpy in ethane is ≈ 377 kJ/mol, and C=O ranges from ≈ 532 kJ/mol per bond in CO₂ to ≈ 1072 kJ/mol in carbon monoxide. Fitting a single multiplicative constant across both diatomic dissociation energies and mean bond enthalpies mixes a measurement with an averaging convention, introducing a systematic of order 5–10% — larger than the ±5% uncertainty the calibration chain worries about. The 114-pair dataset should state, for each entry, which kind of number it is.

**What is not known, and what the downstream numbers actually are.** The fit uncertainty on κ has not been published. Because every downstream quantity is proportional to 1/κ, a ±5% uncertainty on κ propagates as ±5% on τ, ℓ\_cell, and the EM scale constants. But the deeper point is that τ and ℓ\_cell contain no information beyond κ and the integer 27. Numerically: κ = 190 kJ/mol is 1.969 eV per particle, corresponding to a photon wavelength of ≈ 630 nm. Then τ = h·N\_A/κ = 2.10 fs and ℓ\_cell = 27·c·τ = 27 × 630 nm ≈ 17.0 μm. These are the calibration energy re-expressed in time and length units; they are not independent physical predictions. Nothing can be tested by τ or ℓ\_cell that is not already a test of κ. Switching to κ = 193 kJ/mol moves ℓ\_cell from 17.0 μm to 16.7 μm — a 1.6% shift with no new content. Publishing the fit methodology, the full 114-pair dataset with thermodynamic conventions, and a residual-scatter confidence interval on κ would strengthen the entire chain.

**What does not depend on κ.** The refractive-index law n(T) = (24+T)/27 contains no κ, no h, no N\_A, no c. It is a statement about the substrate's tick accounting and is κ-free by construction. However, being κ-free also makes it a definitional accounting statement rather than a calibration claim; its empirical content rests entirely on whether the refractive indices it predicts match measurement, and that comparison should be stated and assessed separately. The EM scale's *linearity* (S = k × λ within each HW class) is exact by construction and independent of κ. The bond-order warping results (r = 0.55, 86.8% accuracy) depend on the encoding structure, not on the absolute energy scale, and survive revision of κ. Two caveats apply to the bond-order numbers: they require a sample size n, a confidence interval, and a stated base rate before "86.8% accuracy" is interpretable; and a label-shuffle control — the same null comparison used elsewhere in this project — would settle cheaply whether the accuracy exceeds chance.

**The productive framing, with a necessary split.** The energy scale is genuinely molecular and optical: κ ≈ 2 eV per particle, visible-light photon energies, the range of chemical bond strengths. That part of the "molecular scale" characterisation is fair and is the reason the substrate maps well to structural chemistry. The derived *length* scale is not molecular: ℓ\_cell = 17 μm sits in the mid-infrared, roughly five orders of magnitude above a typical bond length (~0.1 nm). Saying "the substrate operates at the molecular scale" is supported for the energy and contradicted for the length; the two should not be conflated. The 190 kJ/mol calibration is best understood not as a prediction of bond energies from first principles, but as an **empirical conversion factor** between the substrate's geometric work metric and real thermodynamic quantities. Whether the geometric work carries genuine signal about relative bond strengths is the open question; the absolute calibration is, by construction, empirical.

### 11.6 The Combined Picture

No single method fully explains everything, but they all point to the same physical picture: bond formation is a geometric process in the Activation row of the MOG grid, and the structural changes during settlement (geometric work) predict bond strength. The data flow is:

```
Element properties → 24-bit Data Objects → Warped encodings →
AND/XOR interaction metrics → Geometric work (path integral) →
Calibrated predictions (kJ/mol)
```

Note, XOR is not generally considered a suitable function in the UBP or GLM systems as it destroys rather than carries information.

---

## 12. The MOG Cube: Encoding and Semantics

### 12.1 The Cube Surface as MOG

The MOG cube study (`data_object/mog_cube_1/`) establishes that the surface of a cube — 6 faces × 4 cells = 24 cells — is a natural physical realisation of the MOG (Miracle Octad Generator) grid. The key results, all proved in Lean:

- **24 surface cells = 6 faces × 4 quadrants = the MOG grid** (`CubeMOG.IsMog`)
- **Three-layer factorisation:** 2²⁴ → 2¹⁸ → 2¹² (`fibre_card`, `hexpass_card`, `mog_card`)
- **Weight distribution:** 1, 759, 2576, 759, 1 (`CubeMOG.mog_weight_enumerator`)
- **Minimum distance:** 8 (`CubeMOG.mog_min_weight`)
- **One erased face:** always repaired (`CubeMOG.face_erasure_correctable`)
- **Any two erased faces:** always ambiguous (`CubeMOG.two_face_ambiguous`)
- **Repair cost:** at most 4·Q, and 4·Q is attained (`CubeTax.tax_le_four_Q`, `covering_radius_le_four`, `covering_radius_ge_four`)
- **Free cube symmetries:** 12 of 48 (the tetrahedral group) for canonical placement; all 24 rotations for a better placement

### 12.2 The Precision Wall and How It Was Breached

The parity (XOR) cube accepts 1,758 sentences of which only 356 are true — **20% precision**. The reason is proved: `MeasuredWords.xor_encoding_is_mod_two` — any encoding whose composition is XOR sees exponents only mod 2, so `E = mc⁴` is accepted because 4 ≡ 2 (mod 2). No rearrangement of the code fixes this.

The fix is **keeping the integer content**. The integer cube uses a ripple-carry adder wired across each face (`IntegerCube.addG`), achieving **precision 1.00**: the accepted set is *the same list* as the true set, not merely the same length (`IntegerCube.integer_accepts_eq_equations`). XOR is this adder with the carry wire cut (`IntegerCube.xor_is_add_without_carry`); the carry is exactly the information XOR was throwing away.

The cost: an integer record is essentially never a codeword (`IntegerCube.phrase_codeword_count = 0`), though it is still at most 4·Q from one. The honest architecture is two-layer: **integers for meaning, the code for protection and transport**, with a proved exchange rate between them.

### 12.3 Language on the Cube

Given a micro-world of three things (water, stone, lamp) with a temperature and mass each — 512 possible worlds — the system:

- **Holds measurable content on the cube.** A word's physical dimension (exponents of L, M, T, I, Θ, N) is carried on the 24 cells, one dimension per face.
- **Composes by arithmetic, not by hashing.** Multiplying two quantities is adding their cubes, cell by cell.
- **Judges equations exactly.** Over 156 phrases and every ordered pair, it accepts exactly the 356 that are dimensionally true, and no others.
- **Says true things about a world**, answers questions — *is it…? why…? which is hotter…? what if we heat it?* — and refuses false premises.
- **Joins clauses with `and`, `but`, `so`**, where the choice is a measured property of the remaining possible worlds, not a decoration.
- **Holds a conversation** that remembers its topic and commitments, and can never contradict something it has already said.
- **Says what to do**: given a goal it returns a shortest action sequence, and narrates what changed at each step.

A ten-turn transcript, produced by the Lean definitions themselves:
```
> tell me about the water       the water is frozen
> tell me more                  and it is not heavy
> tell me more                  and it is not hotter than the stone
> is it warm?                   the water is not warm
> why is it warm?               as I said, the water is not warm because the water is frozen
> tell me about the stone       the stone is not frozen
> tell me more                  but it is not hotter than the lamp
> tell me more                  but it is heavier than the lamp
> is it hotter than the water?  the stone is hotter than the water
> tell me more                  and it is not boiling
```

Every reply is true in every state, utterance and world (`Dialogue.reply_true`). A conversation never contradicts itself (`Dialogue.run_no_contradiction`).

### 12.4 The Verified Connectives

Each connective has a proved semantic meaning:
- **`and` is news** (`and_is_informative`): it adds information the listener didn't already have
- **`but` is contrastive** (`but_is_contrastive`): it signals a reversal of expectation
- **`so` is a deduction** (`so_is_a_deduction`): it follows logically from what came before

The corpus: 1,536 paragraphs, 9,216 clauses (4,824 `and`, 1,512 `but`, 2,880 `so`), every one valid (`Discourse.corpus_facts`). Paragraphs that change subject: 512 paragraphs, 3,072 clauses, 2,524 subject changes, 330 cross-subject deductions (`WideDiscourse.wcorpus_facts`).

### 12.5 Thought on the Cube

Stage 4 made the cube *think*, not just store:
- **Inference is addition on the surface:** the conclusion record is the premise record plus a fixed law word (`CubeThought.apply_law`)
- **Denial is one universal translation**, the same word for all 48 literals (`negation_is_a_translation`)
- **An inference survives three damaged cells** (`inference_survives_damage`)
- **78 entailing pairs, 27 distinct law words** (`laws_are_sound_on_the_surface`, `law_words_counted`)
- **Clauses, links and dimensions stored as records on one surface:** 4,096 records, 1,024 per role, any two differing in at least 8 cells (`ClauseStore.role_capacity`, `rec_min_distance`)

### 12.6 Stage 5: Learning and Scaling

The capstone development closes four of five open items:

- **Learning:** The 78-entry law table is *fitted*, not written. Version-space elimination over 2,256 hypotheses. Recall is 1 at every corpus size (`laws_are_never_missed`). Twelve chosen worlds suffice (`teaching_set_learns_the_table`); no corpus of three or fewer can ever do it (`teaching_lower_bound`). From the complete corpus the learner returns exactly the same 78 pairs the package used to write by hand.
- **Scaling:** `3n + 3n²` contentful atoms, `6n + 6n²` contingent literals, every one of the 18ⁿ worlds described by exactly `3n + 3n²` facts, for all n (`Scaling.lean`).
- **Continuous quantities:** Integer degrees and kilograms, graded comparatives that recover the exact difference, substrate window proved sharp at [−8, 7] on one face and [−128, 127] on two (`Continuous.lean`).
- **Relative clauses:** Conservativity, monotonicity, duality, exactly 12 law schemas valid at every world size (`Relative.lean`).
- **Golay enumerator:** 759 octads and the weight enumerator 1, 759, 2576, 759, 1 proved for every code with the four defining properties. Uniqueness up to equivalence is still quoted, not proved.

**The capstone** (`Capstone.lean`): 78 English conditionals learned from twelve observed worlds, each passing the system's own test for a law, no law of the lexicon left unsaid, and the *why*-answers licensed by the same learning. The half-trained failure is recorded beside it — after sixteen worlds 1,099 sentences stand, of which 1,021 are false.

### 12.7 The Theorem Index

The Lean development comprises 43 files with 1,310 top-level declarations (574 definitions, 736 theorems), zero `sorry`, and no added axioms. Every headline theorem depends only on Lean's three standard axioms (propext, Classical.choice, Quot.sound). `Package.lean` re-checks the axioms behind every headline result in one place, including all of Stage 5. 103 of the finite searches are discharged by `native_decide`, so those additionally trust Lean's compiler rather than the kernel alone; the axiom audit makes that boundary visible.

---

## 13. The Leech Lattice Shortcut

### 13.1 The O(1) Formula

The Leech lattice shortcut (`leech_lattice/`) provides a metric shortcut — not an arithmetic one. The most direct utility is the ability to calculate the 24-dimensional distance between any two integers using just three machine instructions:

```
d² = popcount(gray(a XOR b))
```

This allows instant metric evaluation without walking the interval between integers or enumerating lattice octads.

### 13.2 Structural Integrity

The corrected method guarantees that every transition, when doubled (2Δv), is a genuine Leech lattice vector. For researchers studying the geometric distribution of integers or primes, this provides a mathematically rigorous coordinate system where d² = 8 steps are guaranteed minimal (kissing-sphere) hops in 24D space.

### 13.3 Advanced Scoring: TGIC 3-6-9

The system provides a framework for evaluating the "stability" of integers through node metrics:
- **NRCI (Non-Random Coherence Index):** Measures structural coherence against random expectation
- **TGIC stability:** Evaluates symmetry tax and neighbour pressure within the 24D manifold

### 13.4 The Observer/Read Quantum Study

The "I am Y" study (`light/aristotle_01/Y_STUDY_CLEAN_RESTATEMENT.md`) examines the cost of observation in the substrate. The vacuum is the zero state; the activation quantum is the minimum nonzero tax (8Y + 1 = 3.1174). The loop-as-syndrome interpretation connects the Delta-Sigma feedback loop to error-correction syndrome decoding, and the regime bands (tight/relaxed/skip) correspond to the turbocharger's adaptive snapping strategy.
# Part IV: Formal Verification, First Principles, and Synthesis

## 14. Formal Verification: The Lean Development

### 14.1 Scope

The GLM's formal verification is spread across multiple Lean 4 / Mathlib developments in `RequestProject/` directories throughout the repository. The key developments are:

| Development | Location | Declarations | Content |
|---|---|---|---|
| Core GLM | `glm_lean/RequestProject/GLM/` | 1,310 | Layers, escalation, constants, Golay, Leech, delta-sigma, language |
| Lightspeed | `light/aristotle_01/RequestProject/` | — | Speed-of-light chain, substrate constants, refractive index |
| First Principles | `data_object/FirstPrinciples/` | — | Distinction → Golay, sphere-packing, seeds, fit capacity |
| Projection | `data_object/Projection/` | — | Layer theorem, seed placement, fibre analysis, cost model |
| Higher Lattices | `glm_lean/RequestProject/GLM/HigherLattices.lean` | — | Barnes-Wall 32D, ternary 48D, shell sigma |

Every development builds with `lake build`, contains zero `sorry` placeholders, and every headline theorem depends only on Lean's three standard axioms: `propext`, `Classical.choice`, `Quot.sound`.

### 14.2 The Verification Discipline

The GLM enforces a strict separation between what is proved, what is recomputed, and what is recorded:

**Proved in Lean:** Theorems that hold under the standard axioms. Examples: `GLM.Info.glmChain_refines_of_le` (the layer chain is a refinement), `UBPLightspeed.substrate_c_is_circular` (c is recovered identically), `UBPProjection.transcendental_not_trace_of_finite_order` (no finite symmetry produces a transcendental number).

**Recomputed exactly, every call:** Numerical results regenerated by Python scripts with exact rational arithmetic. Examples: the code's self-duality, weight divisibility, determinant certificates, kissing number censuses.

**Recomputed only when asked (exhaustive):** Results requiring brute-force enumeration (e.g., ternary minimum distance 15 by exhausting an information set, full-weight census by 2²³ Gray-code steps). The default report flags these as `exhaustive: false`.

**Not computed at all:** Results not attempted here (e.g., the kissing number in 48 dimensions, reported as `null` with `kissing_source: "not computed here"` rather than quoting a literature value).

### 14.3 Key Machine-Checked Results

A selection of the most significant theorems, grouped by domain:

**Layer Architecture:**
- `GLM.Info.glmChain_refines_of_le` — the five-layer chain is a refinement (nothing true below becomes false above)
- `GLM.Info.entryResolution_mono` — resolution rises with the layer, for any register
- `GLM.Info.entryResolution_le_distinct` — no layer resolves more entries than there are distinct carriers
- `GLM.Info.substrate_addition_not_congruent` — addition does not descend below the rational layer

**Tax Conservation:**
- `tax_conservation` — TAX(a ⊕ b) + 2·TAX(a ∧ b) = TAX(a) + TAX(b) on binary carriers
- `tax_conservation_fails_at_integer_layer` — the law fails irreparably above binary
- `Y_lt_half` — Y = 1/(π + 2/π) < 1/2, so no repair is possible

**Golay Boundary:**
- `snap_unique_of_le_three` — unique repair at distance ≤ 3
- `snap_ambiguous_at_four` — ambiguity at distance exactly 4
- `snap_boundary_at_three` — 3 is exactly the largest radius for uniqueness

**Speed of Light:**
- `speed_not_from_action_and_energy` — no integers a, b give (0,1,−1) from (1,2,−1) and (1,2,−2)
- `cellLength_div_cellDuration` — ℓ_cell/T_cell = c identically (circularity)
- `octad_min_tax` — octads uniquely minimise the codeword tax
- `refIndex_strictMono` — n(T) is strictly increasing in T

**First Principles:**
- `perfect_code_iff_seven_or_twentythree` — a perfect 3-error-correcting binary code exists only at lengths 7 and 23
- `ball3_closed_form` — Σ_{i≤3} C(n,i) = (n³ + 5n + 6)/6
- `quadratic_pisot_ge_phi` — no quadratic Pisot number is smaller than φ

**Projection:**
- `transcendental_not_trace_of_finite_order` — no finite symmetry produces a transcendental invariant
- `lattice_character_ne_pi` — unconditionally, no lattice symmetry has π as a character value
- `phi_is_trace_of_order_ten` — φ is literally the trace of a rotation of order 10
- `hull_map_not_injective` — the floor function over 13 cannot be inverted

### 14.4 The Axiom Audit

Every headline theorem is audited by a `#print axioms` block that must report exactly `[propext, Classical.choice, Quot.sound]`. No theorem in any development rests on an added assumption. Hypotheses (such as "π is transcendental") are arguments to theorems, never `axiom` declarations.

---

## 15. First-Principles Analysis

### 15.1 What Is Forced, What Is Chosen

The first-principles sub-study (`data_object/FirstPrinciples/`) starts from the framework's own logical beginning — "there is a binary distinction and it can be toggled" — and asks at each step: what is forced, what is chosen, and what had to be brought in from outside?

The chain divides into three parts:

**Part 1 (Stages 0–2) is genuinely first-principles and genuinely works.** From "there is a distinction" you get, with no further input: the two-element field, the state space (ℤ/2ℤ)ⁿ, the toggle group, the Hamming metric, the 2t+1 criterion for unique decoding, the sphere-packing bound, and the fact that a perfect three-error-correcting binary code can exist only at lengths 7 and 23. This is the honest core of the UBP architecture.

**Part 2 (Stage 3) is where the framework stops being first-principles.** Every quantity produced by Part 1 is an integer. Each of π, φ, e is irrational. Therefore no seed is obtainable from the substrate by any rational expression in its counts (FP-19): the seeds are an **input**, not an output, of the binary principle. Each seed is forced by the rôle it is given — φ by self-similarity, π by rotational closure, e by unit growth rate — but the step that multiplies them into ℳ = πφe and reads off the integer 13 is a free choice.

**Part 3 (Stage 4) measures the evidence.** A formula of the shape "integer plus a multiple of a small constant" is an arithmetic progression, and a progression of spacing s lands within s/2 of *any* target. Applying this to the three headline fits:

| Fit | Generic Guarantee | Achieved | Ratio |
|---|---|---|---|
| α⁻¹ = 137 + L | 2.3×10⁻⁴ for any target ≥ 137 | 1.96×10⁻⁴ | < 1.2× |
| m_μ/m_e = 169/w | 2.97×10⁻³ for any target ≥ 206 | 2.94×10⁻⁴ | ≈ 10× |
| m_p/m_e = 1836 + 2Lσ | 1.5×10⁻⁶ for any target ≥ 1836 | 3.74×10⁻⁷ | ≈ 4× |

The fine-structure agreement is essentially not evidence at all. The muon fit is worth about one decimal digit of surprise. The proton fit about a factor of four.

### 15.2 The Bit-Score Ledger

The projection sub-study converts these findings into a ranked development queue:

| Fit | Bits of Evidence | Verdict |
|---|---|---|
| α⁻¹ = 137 + L | < 1 bit | Not evidence — pursue other targets |
| m_p/m_e = 1836 + 2Lσ | 2–3 bits | Worth pursuing |
| m_μ/m_e = 169/w | 3–4 bits | Most promising single fit |

Doubling the number of candidate formulas costs exactly one bit. The general statement — a family of N candidate formulas can match a target set of measure at most 2Nδ — is FP-30.

---

## 16. The Projection Sub-Seed: Where Seeds Enter

### 16.1 The Layer Theorem

The projection sub-study (`data_object/Projection/`) proves a fundamental constraint on where each seed can enter the framework:

**Theorem (L-5):** No finite symmetry produces a transcendental number — in any dimension, over ℂ. A linear map of finite order has only roots of unity as eigenvalues, so character values are sums of roots of unity, hence algebraic.

**Theorem (L-7):** Unconditionally (using only irrationality, not transcendence): no lattice symmetry has π or e as a character value. Lattice symmetries are integer matrices; their character values are integers.

This forces a clean separation:

| Layer | What It Produces | Which Seed Lives There |
|---|---|---|
| 0 — Counting | Naturals, rational ratios | None (proved) |
| 1 — Finite symmetry | Algebraic numbers in cyclotomic fields | φ |
| 2 — Flows | Period and flow-time constants | π, e |

### 16.2 φ Is Native to Layer 1

φ is literally the trace of a rotation of order 10: φ = ζ + ζ⁻¹ for a primitive 10th root of unity, lying in a cyclotomic field. But φ is **not** an eigenvalue of any finite-order map (eigenvalues have modulus 1, and φ > 1). It enters as a *character value*, never as a scaling.

**Correction:** The framework's "φ shears" is wrong. The Fibonacci matrix is a *stretch* (hyperbolic, eigenvalue φ > 1), not a shear (parabolic, eigenvalue 1). Exponential beats linear: this is proved.

### 16.3 What Projection Destroys

The trace map on SL(2,ℤ) has infinite fibres: two matrices with the same trace, determinant, and characteristic polynomial are not conjugate over ℤ. The floor function ⌊·⌋ over 13 has a fibre of measure 1, and three different seed monomials land in it: πφe = 13.817..., πφ³ = 13.308..., π⁴/e² = 13.182.... "Run 13 backwards to the seeds" is impossible, and that is a theorem.

### 16.4 Q Is a Gauge, Not an Observable

Once the coherence budget is calibrated to the quantum, the NRCI ladder is 8/(8+n) whatever Q is. No statement about coherence can depend on the value of Q. This is proved: `nrci_gauge_independent`.

### 16.5 What Is Out of Reach

The study is explicit about what it cannot prove:
- Algebraic independence of π and e (open problem)
- Necessity of the modelling choices (sufficiency is provable, necessity never)
- The icosian construction of the Leech lattice in full
- "Meaning", "Time", "resonance" as physics (not mathematics)

---

## 17. Synthesis: What Is Proved, What Is Calibrated, What Is Open

### 17.1 The Proven Core

The following are established mathematical facts, machine-checked in Lean:

1. **The binary substrate is forced.** From "there is a distinction" → 𝔽₂ → (ℤ/2ℤ)ⁿ → Hamming metric → perfect codes exist only at lengths 7 and 23 → parity extension to 24 → Golay code → Leech lattice via A → B → C. No choices are made in this chain until the parity extension, which is chosen for self-duality.

2. **The layer architecture is formally verified.** The five-layer stack is a refinement chain. Information lost at a boundary is exactly new expressive power gained. The ascent is forced by capacity constraints. The dyadic tower is infinite, strictly increasing, cumulative, and exhaustive.

3. **TAX conservation is exact on binary carriers and irreparably broken above.** The boundary is a single constant (Y = 1/(π + 2/π) ≠ 1/2), proved.

4. **The Golay snap radius is sharp.** Unique repair at distance ≤ 3, ambiguity at 4, uncorrectable at ≥ 5. The boundary is a single integer.

5. **No finite symmetry produces a transcendental number.** φ enters as a character value; π and e must come from flows.

6. **The floor function is not invertible.** Three different seed monomials produce hull 13. Seed recovery is impossible.

7. **The refractive-index law is falsifiable.** n(T) = (24+T)/27 with no empirical parameters. Diamond falsifies it (T > 24).

8. **Gray code is the optimal read channel.** Exactly one bit flip per step (`gray_step`), zero transition entropy. **Correction:** "Exactly half" is false at every finite width; the sharp statement is `2·gray = binary + 2` (`gray_two_mul_eq`).

9. **Reversible gates perfectly conserve state.** Toffoli and Fredkin are involutions and bijections. The composition has order 3 (`round_cubed`), not order 2. Inverse rounds undo forward rounds exactly. Kink count is rotation-invariant (`kinks_rotate`) and always even (`kinks_even`); single flips move it by {-2, 0, +2}, not exactly ±2.

10. **The MOG cube supports a complete verified language.** 1,310 Lean declarations, zero sorry, words with dimension, true sentences, connectives, conversation.

### 17.2 The Calibrated Results

The following are empirical calibrations, internally consistent but not derived from first principles:

1. **The EM scale function** S(λ, HW) = λ/[HW × (Y + 1/8)] is validated against 48 EM references. It is derived from the substrate's definition, not curve-fit, but the substrate's definition itself contains the empirically fitted constant Y.

2. **The mass scale** is internally consistent: m_e formula (0.00919% error), m_μ/m_e ratio (0.02938% error), cross-check m_e × ratio → m_μ (0.039% error). The WOBBLE cancels in the cross-check.

3. **The proton-to-electron mass ratio** m_p/m_e = 1836 + 2L_s achieves 0.0000374% error — the most precise alignment point, worth 2–3 bits of evidence.

4. **The 190 kJ/mol scale factor** matches real bond energies and places the substrate at the molecular scale.

5. **Element property encoding** achieves r > 0.90 for electronegativity and boiling point from 24-bit Golay/Leech encodings.

6. **Bond energy prediction** reaches r = 0.55 with warping strategies, and bond order classification reaches 86.8% accuracy.

### 17.3 The Open Problems

1. **The mass residual (0.00919%).** The single most important open problem. If the residual is α² × (geometric factor), it would connect the UBP mass scale to QED. The corrected value (9.19×10⁻⁵, not 7.2×10⁻⁵) makes the α² hypothesis less clean (1.726α², not 1.35α²).

2. **Null model uniqueness.** 33 out of 50,000 random transcendental combinations match m_e within 0.01%. The formula is motivated (structural integers, precision-stable) but not proven unique.

3. **The missing length.** The substrate cannot derive c (Buckingham's Π theorem). It would need a predicted absorption or scattering length independent of c. Absent that, the correct claim is "the substrate calibrates to a 17 μm cell", not "the substrate derives c".

4. **The TAX spectrum.** Integer TAX (n ≤ 1.778) and codeword TAX (n ≤ 1.235) give different ceilings. The model must commit before it can be tested.

5. **Provenance.** The 275 unreachable physics entries need a coordinate for "of" — what a quantity is a measure *of* — not a new layer.

6. **The VOA state-field map Y(u, z).** The Moonshine module has graded dimensions but not the operator. The first step: mode operators uₙ for n = −1, 0, 1 on the 2A subalgebra.

7. **Algebraic independence of π and e.** Open problem. The transcendence degree of ℚ(π,e) over ℚ is 1 or 2; both branches are formalised conditionally.

8. **The κ fit uncertainty.** Every downstream number is proportional to 1/κ. A ±5% fit uncertainty is a ±5% uncertainty on the cell length.

---

## 18. Conclusion and Open Questions

### 18.1 What the GLM Is

The GLM is a mathematically rigorous 24-dimensional substrate with exact rational arithmetic, where:
- The charge scale is exact (vertex count → e/12)
- The velocity scale is exact (MONAD/13 → v/c = 0.339, but this is a definition, not a prediction)
- The mass scale is internally consistent (0.009% error, cross-checks pass)
- The photon as minimum-Tax octad is a mathematical fact on the Golay layer
- The layer architecture is formally verified with 1,310+ Lean theorems
- The encoding system predicts element properties at r > 0.90

### 18.2 What the GLM Is Not

The GLM is **not** a theory that derives physical constants from first principles. The first-principles analysis proved this conclusively: the seeds (π, φ, e) are inputs, not outputs; the monomial producing 13 is a choice; and two of the three headline numerical agreements are within an order of magnitude of what an arbitrary target would have received.

### 18.3 The Productive Reframing

**Old:** "Can the substrate derive physical constants?" → No, by Buckingham's Π.

**New:** "Can substrate ratios + SI-defined anchors predict measured constants?" → Partially yes. The substrate supplies dimensionless numbers; the SI supplies the dimensions. This is calibration, not derivation, and it is only as good as the empirical anchors.

### 18.4 The Path Forward

The most productive direction is not to chase exact derivations of constants the SI already defines. It is to build the **computational engine** — use the calibrated substrate as a geometric stability evaluator where TAX minimisation and NRCI maximisation serve as solver logic. The MOG cube language, the chemistry encoding, and the Leech lattice shortcut are all steps in this direction.

### 18.5 The Honest Summary

The UBP has genuine mathematical structure that deserves honest acknowledgment. The dimensionless ratios pass null-model tests. The mass scale is internally consistent. The layer architecture is formally verified. The encoding system predicts real chemistry. These are real findings, not numerology.

But the gap between "the substrate has structure that correlates with physical reality" and "the substrate derives physical reality from first principles" remains the central tension of the programme. The studies assembled here map that gap precisely, and the formal verification ensures that nothing is claimed that cannot be checked.

---

## Appendix A: Source Document Index

### Studies Directory (`studies/`)
| Document | Core Subject |
|---|---|
| ANALOGY_LAYER_STUDY.md | A : B :: C : D query resolution |
| DENOTATION_STUDY.md | What undimensioned names denote |
| ECONOMICS_STUDY.md | The economic register |
| ESCALATION_STUDY.md | Layer stack on 1,040 carriers |
| GEOMETRIC_AMBIGUITY_STUDY.md | Six-fold Golay tie as computation |
| GLM_COMPANION_STUDIES_AUDIT.md | Testing companion preprints |
| GLM_STUDY_CATALOG_AUDIT.md | Testing empirical findings |
| GLM_UNIFICATION_BLUEPRINT_AUDIT.md | Testing the specification |
| HARMONY_STUDY.md | The harmonic register |
| HEXCOLOUR_STUDY.md | Hexcolour address layer |
| HIGHER_LATTICE_STUDY.md | 32D and 48D lattices |
| INFINITE_VALUES_STUDY.md | Irrationals in the GLM |
| INFORMATION_LOSS_STUDY.md | Layer boundaries and refinement |
| LANGUAGE_STUDY.md | Question shapes as objects |
| LEAN_ADDRESS_STUDY.md | Leech addresses for Lean declarations |
| LLVQ_TABLE_STUDY.md | O(1) Leech quantiser lookup |
| NAME_COORDINATE_STUDY.md | Resolution ceiling for names |
| NOISE_EXPERIMENT_STUDY.md | Wobble as computation |
| RECIPE_STUDY.md | Recipes as objects |
| RELATIVE_MEASURE_PROPOSAL.md | Measure words as relative measures (proposal) |
| RELATIVE_MEASURE_STUDY.md | Measure words as relative measures (measured) |

### Source Material (`source_material/`)
| Document | Core Subject |
|---|---|
| glm_unification_blueprint.md | Master specification for GLM-3+ |
| glm_study_findings_catalog.md | Empirical findings catalogue |
| cardinal_geometry_synthesis.md | Geometry, information loss, and infinite values |
| DYNAMIC_CARRIER_STUDY.md | Dynamic carrier processes |
| geometric_substrate_study.py | Geometric substrate experiments |

### Light Studies (`light/`)
| Directory | Core Subject |
|---|---|
| aristotle_01/ | EM scale calibration, Leech shortcut, lightspeed study, observer Y study |
| EM_calibration_1/ | Speed of light calibration (11 versions) |
| reports/ | 20-phase audit reports |

### Data Object Studies (`data_object/`)
| Directory | Core Subject |
|---|---|
| encoding_definition_attempt_03-08.26/ | Spatial arithmetic experiments |
| encoding_definition_attempt_04.08.26/ | 24-bit Golay/Leech encoding + MOG spatial chemistry |
| mog_cube_1/ | MOG cube encoding system and semantics |
| FirstPrinciples/ | First-principles sub-study (37 findings) |
| Projection/ | Projection sub-study (seed placement) |

### Formal Verification (`RequestProject/` directories)
| Location | Content |
|---|---|
| glm_lean/RequestProject/GLM/ | 43 files, 1,310 declarations, core GLM verification |
| light/aristotle_01/RequestProject/ | Lightspeed, substrate constants, lattice shortcut |
| data_object/FirstPrinciples/ | Distinction, distance, packing, seeds, fit capacity |
| data_object/Projection/ | Layers, one-parameter, fibre, cheapest, cost, surprisal |

---

## Appendix B: Key Constants

| Symbol | Definition | Value | Source |
|---|---|---|---|
| Y | 1/(π + 2/π) | 0.264675430405 | Substrate definition |
| MONAD | π · φ · e | 13.817580227176 | Seed product |
| WOBBLE | MONAD − ⌊MONAD⌋ | 0.817580227176 | Fractional part |
| L | WOBBLE / 13 | 0.062890786706 | Derived |
| Q | Y + 1/8 | 0.389675430405 | Coherence quantum |
| σ | 29/24 | 1.208333333333 | Scaling factor |
| κ | Empirical fit | 190 kJ/mol | Chemistry anchor |
| τ | h·N_A/κ | 2.100165 fs | Tick duration |
| ℓ_cell | 27·c·τ | 16.9996 μm | Cell length |
| TAX(octad) | 8Y + 1 | 3.117403 | Minimum codeword tax |

---

## Appendix C: Glossary

- **Carrier:** A 24-tuple of exact rationals (q₀, ..., q₂₃) ∈ ℚ²⁴ — the fundamental data unit
- **MOG:** Miracle Octad Generator — the 6×4 grid encoding the Golay code's structure
- **NRCI:** Non-Random Coherence Index — measures structural coherence against random expectation
- **TAX:** Symmetry tax — the cost of a state, defined as HW·Y + ‖v‖²/8
- **TGIC:** The 3-6-9 structure — a scoring framework for integer stability in 24D
- **TCT:** Three Column Thinking — the verification protocol (Language / Mathematics / Script)
- **UBP:** Universal Binary Principle — the foundational framework
- **GLM:** Geometric Language Machine — the cognitive architecture built on UBP
- **Delta-Sigma:** The deterministic error-feedback loop used to represent continuous values
- **Golay code:** The [24, 12, 8] extended binary error-correcting code
- **Leech lattice:** Λ₂₄ — the unique even unimodular rootless lattice in 24 dimensions
- **Griess algebra:** The 196,884-dimensional non-associative algebra supporting the Monster group
- **Construction A/B/C:** The three-tiered congruence ladder from Golay code to Leech lattice
- **Hull certificate:** An exact separating linear functional proving a target is unreachable
- **Wobble signature:** The entropy/autocorrelation profile of a Delta-Sigma stream
- **Escalation:** The process of moving to a higher layer when the current one is insufficient
- **Refinement:** L' refines L if L' distinguishes at least as much as L
- **Deep hole:** A point at maximum distance from the nearest lattice point
