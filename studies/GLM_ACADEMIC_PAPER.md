# The Geometric Language Machine: A Unified Substrate for Exact Computation, Physical Calibration, and Semantic Reasoning


## Tier 0 — the coarse read

**Question.** What is the GLM, stated as a paper rather than as a repository?

**Verdict.** The system rejects floating-point arithmetic entirely, operating instead with exact rational arithmetic.

**Deciding figure.** A working paper over the whole system — the substrate studies of the supplied archive and the machine built on them, <!--figure:registers-->8 registers<!--/figure--> reached through <!--figure:query-kinds-->24 query kinds<!--/figure--> and checked by <!--figure:lean-files-->133 Lean files<!--/figure--> — kept beside the studies it draws on.

**Recomputed by.** (hand-written argument; nothing to recompute)

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

## A Technical Documentation Paper

**Author:** Euan R. A. Craig (DigitalEuan), Auckland, New Zealand  
**Date:** 02 September 2026; revised 24 September 2026 (Phases 60 and 61)  
**Repository:** https://github.com/DigitalEuan/GLM  
**Status:** Working Paper — the whole system in one place: the substrate studies of the supplied archive (Parts I–IV) and the machine built on them through Phase 59 (Parts V–VI), with one ledger of what is proved, calibrated, measured, refuted and open (Part VII). Phase 61 brought the last small bodies of archive Lean under this repository's own build (`Distinction.lean`, `SeedRoles.lean`, `GolayMOG.lean`) and extended the supplied-material ledger of Appendix C to every part of the archive.

> **Positioning.** This paper is written under the Positioning section of
> [`PROJECT_DIRECTIVES.md`](../PROJECT_DIRECTIVES.md), which is the one place
> it is stated: the claim is not that the lattice generates the universe, but
> that there is an exact substrate — the Golay code, the Leech lattice and the
> arithmetic on them — and that reality maps onto it with a fidelity that is
> measured against a control wherever it is asserted.

**How the figures in this paper are kept.** A figure written between
`<!--figure:…-->` markers is emitted by the code that measures it and is
rewritten by `python3 -m glm_universal.corpus --refresh`; `corpus --check`
fails if one goes stale, so those numbers cannot age. Every other number in
Parts V–VII is quoted from the study named beside it, where it is recomputed;
the figures of Parts I–IV are those of the archive studies they summarise,
and where this repository has re-measured one the re-measurement is the one
given.

---

## Abstract

This paper documents the Geometric Language Machine (GLM), a cognitive architecture built on the Universal Binary Principle (UBP) — a 24-dimensional computational arrangement constructed from the extended binary Golay code and the Leech lattice. The system rejects floating-point arithmetic entirely, operating instead with exact rational arithmetic over ℚ²⁴, and achieves deterministic, reproducible, and formally verifiable computation.

The complete chain of reasoning from first principles: how a single binary distinction forces the existence of the Golay code at length 23, how the parity extension to 24 dimensions yields the Leech lattice through a three-tiered construction ladder, and how this geometric substrate supports a layered architecture of increasing resolution — from binary parity through integer, rational, Griess algebra, and universal perspectives. Each layer boundary is a theorem, not a design choice: information lost at a boundary is exactly equivalent to new expressive power gained above it.

The system's dynamic value layer represents irrational and transcendental numbers not as static approximations but as infinite processes — deterministic Delta-Sigma feedback loops that converge on the Leech lattice. A family of thermodynamic carrier engines optimises these processes, achieving up to 60-bit precision on exotic constants while maintaining exact arithmetic throughout.

Physical calibration studies anchor the substrate to measured reality: the electromagnetic scale function maps photon wavelengths to substrate units through a linear, Hamming-weight-dependent relationship; a refractive index law emerges from the substrate's symmetry tax without empirical parameters; and dimensionless ratios connecting substrate constants to particle mass ratios achieve precisions of 0.001% to 0.03% — agreements whose evidential worth the first-principles study prices, in bits, against what an arbitrary target would have received.

Application studies demonstrate that encoding chemical elements as 24-bit data objects in the Leech lattice produces element-property correlations exceeding r = 0.90 for electronegativity and boiling point, and that spatial arithmetic operations on these encodings predict bond energies and bond orders with measurable accuracy. A machine-checked semantics on the MOG cube surface builds a complete micro-language — words with physical dimension, true sentences, connectives with measured meanings, and conversation with memory — proved in the supplied archive's own Lean development.

On that substrate this repository has built and measured the machine itself: a pure-standard-library Python package holding <!--figure:registers-->8 registers<!--/figure--> of exact carriers, answering <!--figure:query-kinds-->24 query kinds<!--/figure--> (one of which dispatches <!--figure:report-subjects-->65 report subjects<!--/figure-->) as three-column answers whose third column re-derives the second in a fresh interpreter, and refusing — with a named reason — wherever an answer would have been a guess. Its faculties are measured rather than described: an end-to-end evaluation of <!--figure:evaluation-cases-->177 CLI cases<!--/figure--> with no confidently wrong answer, 33 capability probes of which 13 locate a boundary, five benchmark suites, pre-registered probes for language, conversation, ordering, extremum, scale conversion, typed question plans and engineering languages, and escalation ladders read over the construction ladder and the norm family. The formal layer is a Lean 4 / Mathlib development of <!--figure:lean-files-->133 Lean files<!--/figure--> and <!--figure:lean-declarations-->3,766<!--/figure--> declarations with no `sorry`, and the repository is kept by <!--figure:directive-count-->16<!--/figure--> standing rules, each enforced by an instrument.

Throughout, we distinguish carefully between what is proved, what is calibrated, what is measured, what is refuted, and what remains open. The paper serves as both a technical reference and an honest accounting of a research programme that spans pure mathematics, computational physics, and artificial intelligence.

---

## Table of Contents

**Part I — Foundations**
1. [Introduction and Scope](#1-introduction-and-scope)
2. [The Universal Binary Principle: From Distinction to Substrate](#2-the-universal-binary-principle-from-distinction-to-substrate)
3. [The Golay Code and Leech Lattice: The 24-Dimensional Foundation](#3-the-golay-code-and-leech-lattice-the-24-dimensional-foundation)
4. [The Layer Stack: Resolution, Boundaries, and Escalation](#4-the-layer-stack-resolution-boundaries-and-escalation)

**Part II — Dynamic Values, Carrier Engines, and Bit Dynamics**
5. [Dynamic Value Carriers: Irrationals as Processes](#5-dynamic-value-carriers-irrationals-as-processes)
6. [The Thermodynamic Carrier Engine Series](#6-the-thermodynamic-carrier-engine-series)
7. [Bit Dynamics and Reversible Computing](#7-bit-dynamics-and-reversible-computing)
8. [Higher Lattices: Beyond 24 Dimensions](#8-higher-lattices-beyond-24-dimensions)

**Part III — Physical Calibration, Chemistry, and Applications**
9. [Physical Calibration: The Electromagnetic Scale](#9-physical-calibration-the-electromagnetic-scale)
10. [The Speed-of-Light Calibration Study](#10-the-speed-of-light-calibration-study)
11. [Chemistry Applications: Spatial Arithmetic on Elements](#11-chemistry-applications-spatial-arithmetic-on-elements)
12. [The MOG Cube: Encoding and Semantics](#12-the-mog-cube-encoding-and-semantics)
13. [The Leech Lattice Shortcut](#13-the-leech-lattice-shortcut)

**Part IV — Formal Verification and First Principles**
14. [Formal Verification: The Lean Development](#14-formal-verification-the-lean-development)
15. [First-Principles Analysis](#15-first-principles-analysis)
16. [The Projection Sub-Study: Where Seeds Enter](#16-the-projection-sub-study-where-seeds-enter)

**Part V — The Machine**
17. [Architecture: One Carrier, Three Columns, Named Refusals](#17-architecture-one-carrier-three-columns-named-refusals)
18. [Registers and Meaning](#18-registers-and-meaning)
19. [The Answer Surface: From a Row to a Plan](#19-the-answer-surface-from-a-row-to-a-plan)
20. [Escalation and Ladders](#20-escalation-and-ladders)
21. [Addressing: The Geometry as an Index](#21-addressing-the-geometry-as-an-index)
22. [Measured Capability](#22-measured-capability)
23. [The Negative Results](#23-the-negative-results)

**Part VI — Method**
24. [How the Repository Keeps Itself Honest](#24-how-the-repository-keeps-itself-honest)

**Part VII — Synthesis**
25. [Synthesis: Proved, Calibrated, Measured, Refuted, Open](#25-synthesis-proved-calibrated-measured-refuted-open)
26. [Conclusion](#26-conclusion)

**Appendices** — [A: every study](#appendix-a-every-study) · [B: the Lean development by theme](#appendix-b-the-lean-development-by-theme) · [C: the supplied material, and what is still left in it](#appendix-c-the-supplied-material-and-what-is-still-left-in-it) · [D: key constants](#appendix-d-key-constants) · [E: glossary](#appendix-e-glossary)

---

## 1. Introduction and Scope

### 1.1 What This Document Is

This paper synthesises GLM development research into a single coherent narrative, and since its revision in Phase 60 it is the document that keeps track of the GLM as a *whole*. The source material comprises:

- **The supplied archive** (`source_material/GLM-main.zip`): the physical calibration studies in `light/`, the encoding experiments and the MOG cube in `data_object/`, the first-principles and projection sub-studies, the `GMHGL` scripts, the Leech-lattice shortcut, the early `glm_lean` and `glm_machine` iterations and the ARC-era loop — together with the other supplied documents in `source_material/`. Parts I–IV summarise these, and Appendix C says, item by item, where each went.
- **The machine built in this repository**: the package under `overlay/glm_universal/`, its registers, operations, instruments and tests. Part V describes it and Part VI describes the discipline it is kept under.
- **The studies** in `studies/`, each of which measures one thing against a control and records the result, positive or negative. Appendix A lists every one.
- **The formal verification** in `RequestProject/GLM/`: a single Lean 4 / Mathlib development that builds with `lake build`, has no `sorry`, and is mirrored byte-for-byte in `overlay/glm_lean/`. §14 and Appendix B describe it.

The paper is not a copy-paste compilation. Each source document is read, its core claims extracted, and the connections between studies made explicit. Where studies contradict or correct each other, the correction is recorded. Where claims are later audited and found wanting, the audit verdict is given.

### 1.2 The Central Question

The GLM project asks: **Can a computational system built entirely on exact arithmetic over a 24-dimensional geometric substrate reason about physical reality, predict measurable quantities, and support formal verification — without ever resorting to floating-point approximation?**

The Positioning section of the directives breaks that into four questions that can each be answered by running something: can language, mathematics and program text be mapped onto the Leech lattice; can the GLM *reason* with what the mapping gives it; can it be *generative*; and can it produce results that are real, accurate and checkable. §22 gives the current measured answers.

The answer, as documented across the studies assembled here, is nuanced. The substrate's mathematical structure is genuine and deep. Its layer architecture is formally verified. Its physical calibrations achieve measurable precision. The machine answers a bounded but real range of questions exactly and refuses the rest with a reason. But the gap between calibration and derivation — between fitting constants and predicting them from first principles — remains the central open problem of the physics, and the gap between *addressing* an answer and *deriving* one remains the central open problem of the machine.

### 1.3 Reading Guide

Sections 2–4 establish the mathematical foundations: the binary substrate, the Golay/Leech construction, and the layer architecture. Sections 5–8 describe the dynamic machinery: how continuous values are handled, how computation is optimised, how bit-level operations preserve information, and what lies above 24 dimensions. Sections 9–13 present the applications from the archive: physical calibration, chemistry, the MOG cube language, and the Leech shortcut. Sections 14–16 document the formal verification and the first-principles analysis. Sections 17–23 describe the machine this repository built on the substrate — its architecture, registers, operations, escalation ladders, addressing, measured capability and negative results — and §24 the method that keeps it honest. Section 25 is the single ledger; §26 concludes.

A reader who wants the coarse picture and nothing else can read the tier-0 table in [`DIGEST.md`](../DIGEST.md), which states every document's verdict in one line; this paper is the long form of that table.

---

## 2. The Universal Binary Principle: From Distinction to Substrate

### 2.1 The Starting Point

The Universal Binary Principle (UBP) begins from a single axiom: **there exists a binary distinction, and it can be toggled.** Everything else is derived.

This is not a metaphor. The first-principles sub-study (`data_object/FirstPrinciples/FINDINGS.md`) traces the logical chain rigorously:

- **FP-1 to FP-7 (Stage 0):** From "there is a distinction" → the two-element field 𝔽₂ → the state space (ℤ/2ℤ)ⁿ → the toggle group → the Hamming metric. No choices are made; these are forced by the algebra of a two-element ring. Since Phase 61 this stage is machine-checked here too (`Distinction.lean`): the toggle is the only non-trivial reversible operation on a cell (`GLM.Distinction.perm_bool_eq`), every ring with two elements is `ZMod 2` (`GLM.Distinction.two_element_ring_is_zmod_two`), and a group in which every element is its own inverse is abelian, so commutativity is derived rather than assumed (`GLM.Distinction.self_inverse_forces_comm`).

- **FP-8 to FP-12 (Stage 1):** The Hamming metric yields the `2t+1` criterion for unique decoding, the sphere-packing bound, and — the sharpest result — the fact that a *perfect* three-error-correcting binary code can exist only at lengths 7 and 23. This is verified exhaustively for all lengths from 4 to 2,000 inside the Lean kernel (`perfect_triple_length`, `Packing.lean`; the arithmetic is set out in §15 of [`GLM_Complete_Number_Theory_Evidence.md`](GLM_Complete_Number_Theory_Evidence.md)).

- **FP-13 to FP-18 (Stage 2):** Ball counting yields the sphere-packing bound. The numbers 7 and 23 are forced, not chosen. The 24 of the "24-bit OffBit" is the parity extension, proved to raise an odd minimum distance by exactly one (7 becomes 8), added for self-duality rather than derived.

### 2.2 The Architectural Commitments

The UBP enforces a strict discipline on all code that operates within it:

| Commitment | Operational Ban |
|---|---|
| No floats (`fractions.Fraction` only) | No SHA-256 hashes |
| Exact arithmetic only | No XOR (except over 𝔽₂) |
| Standard library only | No random seeds |
| Re-derived (falsifiable) facts | |

In the shipped package each of these is a standing rule with an instrument
rather than a preference (§24): no floats is directive D7, checked by parsing
every module; exclusive-or and every other operation that is not the
substrate's own are allowed only at declared sites (D9, D11); and SHA-256 is
confined to one module, `glm_universal/integrity.py`, one level above the six
core sub-packages, where it addresses integrity and never meaning (D3).

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
| Griess | carrier + an axis of the partial Norton–Sakuma 2A algebra | algebraic structure on axes | the 2A product on axes; the 196,884-dimensional Griess algebra itself is not held |
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
| Lexicon | 149 |
| **Total** | **1,094** |

Results:

| Layer | Resolves | Loses | Largest Class |
|---|---|---|---|
| Substrate | 469 / 1,094 | 625 | 142 |
| Integer | 598 / 1,094 | 496 | 118 |
| Rational | 811 / 1,094 | 283 | 78 |
| Griess | 811 / 1,094 | 283 | 78 |
| Universal | 811 / 1,094 | 283 | 78 |

The audit covers six of the eight registers (the spatial and economics registers are not in it). The ceiling is 811 distinct carriers under 1,094 named entries. The 283 unreachable entries are almost entirely in physics — 78 are dimensionless ratios (albedo, absorptance, etc.) that share identical 24-coordinate encodings because the register carries no coordinate for *provenance*. The escalation mechanism has nothing left to offer here; a seventh coordinate, not a sixth layer, is what would help.

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

**The Griess product as a non-associative tower.** *(A caution, from Phase 63, item E2: the runtime holds a partial Norton–Sakuma 2A axial algebra, meaning the product on axes, and not the Griess algebra. So the tower below describes the Griess algebra, not anything the runtime can climb yet.)* The Griess algebra's non-associativity — (a·b)·c ≠ a·(b·c) — generates an infinite tower of higher products:
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

### 10.5 The Archive's Twenty-Phase Audit

Before the Lean audit above, the archive's own twenty-phase audit
(`light/reports/`, with its floating-point scripts in `light/scripts/` and its
synthesis in `light/reports/LIGHTSPEED_STUDY_SYNTHESIS.md`) had already closed
four routes, and they are recorded here so that nobody reopens them. The
figures are the archive's and are not re-run here.

- **The direct c-formula is numerology.** Its false-positive rate against random integers was 39 %: random targets were matched about as well as `c`.
- **The dimensional anchors carry no substrate structure.** The caesium frequency Δν_Cs = 9,192,631,770 Hz has the prime factor 44,351, which no substrate count produces, and the gravitational constant fails the null model.
- **The gravitational coupling fit has the signature of numerology.** The formula for α_G works with the archive's approximate π and fails with the true π: the approximation error was cancelling the formula's error.
- **The muon pattern does not generalise.** `169/WOBBLE` for m_μ/m_e has no analogue for m_τ/m_e.

What the audit kept — the charge anchor, the octad as the minimum-tax photon, the two mass formulas and their shared scale — is the calibrated core of §10.3 and §25.2, re-measured here with exact arithmetic.

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

### 11.7 The Discrete Layer, Machine-Checked

The one Lean file of the spatial-arithmetic experiments
(`data_object/encoding_definition_attempt_03-08.26/`) was retrieved in Phase 61
as `GolayMOG.lean`. It does not touch the correlations above; it proves what
is true of the encoding whatever the chemistry says, and five of its results
are negative:

| result | what it says | kind |
|---|---|---|
| `GLM.GolayMOG.identityAddress_injective` | the 12-bit Gray identity addresses of the 118 elements decode back to the atomic number, so no two collide | positive |
| `GLM.GolayMOG.consecutive_identity_oneBitApart` | consecutive atomic numbers are one bit apart: the Gray layer makes the table's order local | positive |
| `GLM.GolayMOG.mogCoordinate_bijective`, `GLM.GolayMOG.octadZoneCoordinate_bijective` | the fixed MOG cell assignment loses no coordinate, and its three column-pair regions partition the 24 | positive |
| `GLM.GolayMOG.leechAddress_sqNorm`, `GLM.GolayMOG.leechMinimalClass_counts` | the 24 stored Leech addresses are minimal vectors, and the three shape families count 1104 + 97152 + 98304 = 196560 | positive |
| `GLM.GolayMOG.binaryTax_mono` | on a binary vector TAX is a monotone function of Hamming weight alone, so it orders nothing the weight does not | negative |
| `GLM.GolayMOG.binaryNRCI_above_half` | below weight 16 an NRCI above one half is automatic whenever Y < 3/16, so that threshold selects nothing | negative |
| `GLM.GolayMOG.element_relativeCoherent_seventy_percent` | under the observed score bounds the "retain 70 % of a peer's score" rule is passed by every element | negative |
| `GLM.GolayMOG.yTwin_injective` | the "virtual Y twin" is injective only because it keeps the original coordinates; it adds no information | negative |
| `GLM.GolayMOG.projection24to3Q_not_injective` | the published 24-to-3 Walsh view is lossy: two coordinate basis vectors share an image | negative |

The archive's own training benchmarks for the same data objects
(`data_object/BENCHMARKS.md`, iteration 11) point the same way and are recorded
for that reason: three-body NRCI passes, but element-pair geometry correlates
at r = +0.05 and molecule geometry at r = 0.00 under the baseline
specification. Those are the archive's figures, not re-run here.

---

## 12. The MOG Cube: Encoding and Semantics

### 12.1 The Cube Surface as MOG

The MOG cube study (`data_object/mog_cube_1/` in the supplied archive) establishes that the surface of a cube — 6 faces × 4 cells = 24 cells — is a natural physical realisation of the MOG (Miracle Octad Generator) grid. It is also the largest Lean development in the archive: 43 files. **Where each result below is checked matters, and it is stated per subsection.** The geometric half (§12.1) was retrieved into this repository's development as `Cube/Surface.lean`, `Cube/Tax.lean`, `Cube/Stabiliser.lean`, `Cube/Three.lean`, `Cube/HexTiles.lean` and `Golay/CubeMirror.lean`, and is rebuilt by every `lake build`. The language half (§12.2–§12.6) — the integer cube, the measured words, the dialogue, the discourse corpus, cube thought and the capstone — was **not** retrieved: it is proved in the archive's own development and is quoted here from it, and Appendix C lists it as the largest body of verified material still left in the archive. The key geometric results, proved in the development:

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

The archive's MOG-cube development comprises 43 files with 1,310 top-level declarations (574 definitions, 736 theorems), zero `sorry`, and no added axioms; `Package.lean` there re-checks the axioms behind every headline result in one place, including all of Stage 5, and 103 of its finite searches are discharged by `native_decide`, so those additionally trust Lean's compiler rather than the kernel alone. These figures are the archive's own and describe that development, not this repository's: of its 43 files, the six named in §12.1 were retrieved and are rebuilt here, and the rest are not (Appendix C). This repository's development is described in §14.

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
# Part IV: Formal Verification and First Principles

## 14. Formal Verification: The Lean Development

### 14.1 Scope

There is one Lean development in this repository: `RequestProject/GLM/`, built from the repository root by `lake build` against Mathlib for Lean 4.28.0. It holds <!--figure:lean-files-->133 Lean files<!--/figure--> and <!--figure:lean-declarations-->3,766<!--/figure--> top-level declarations, contains no `sorry` and no `admit`, declares no axiom, and is mirrored byte-for-byte in `overlay/glm_lean/RequestProject/GLM/` so that the package's figures and its Lean citations read the same tree (`diff -r -x README.md RequestProject/GLM overlay/glm_lean/RequestProject/GLM` is empty; Phase 60 found and repaired the one time it was not).

The development grew in three ways, and Appendix B lists every file under the theme it belongs to:

| origin | what it contributed | where it is recorded |
|---|---|---|
| **the early `glm_lean`** of the archive (`GLM.lean`, `GLM2.lean`, `GLM3.lean`) | the foundations, the second and third generations of the core — ported whole | `Foundations.lean`, `Gen2.lean`, `Gen3.lean` |
| **retrieval from the archive** | the Leech shortcut, the lightspeed chain, the first-principles packing and fit-capacity results, the projection cost and seed layers, the geometric half of the MOG cube, the Golay weight enumerator and Steiner system, the GMHGL scripts' surviving claims; and, in Phase 61, the Stage 0 distinction chain, the seeds' roles, the hull and trace fibres, the φ-cheapest results and the spatial-arithmetic data object's discrete layer (`Distinction.lean`, `SeedRoles.lean`, `GolayMOG.lean`) | [`RETRIEVED_LEAN_STUDY.md`](RETRIEVED_LEAN_STUDY.md), [`SOURCE_SALVAGE_AUDIT.md`](SOURCE_SALVAGE_AUDIT.md), [`SOURCE_SALVAGE_SECOND_PASS.md`](SOURCE_SALVAGE_SECOND_PASS.md) |
| **written in this repository** | one file per mechanism the machine relies on — the layer chain, the escalation loop, the operations and their refusals, the conversation layer, the planner, the engineering surface | the study of the round that built it (Appendix A) |

One body of the archive's Lean is proved there and not rebuilt here: the language half of the MOG cube (§12), about thirty files. The two first-principles files and three projection files that the Phase 60 revision listed as left, and the spatial-arithmetic study's `GolayMOG.lean`, were retrieved in Phase 61; the archive modules they imported are not in the supplied archive, so their numerical bounds were re-derived from `FitCapacity.lean`, and the irrationality of `e`, which they assumed, is now proved (`GLM.SeedRoles.eSeed_irrational`). Where this paper quotes a theorem that is not rebuilt it says so, and Appendix C lists what remains.

### 14.2 The Verification Discipline

The GLM enforces a strict separation between what is proved, what is recomputed, and what is recorded:

**Proved in Lean:** Theorems that hold under the standard axioms. Examples: `GLM.Info.glmChain_refines_of_le` (the layer chain is a refinement), `GLM.Lightspeed.substrate_c_is_circular` (c is recovered identically, so the chain cannot predict it), `GLM.SeedLayers.transcendental_not_trace_of_finite_order` (no finite symmetry produces a transcendental number).

**Recomputed exactly, every call:** Numerical results regenerated by Python with exact rational arithmetic. Examples: the code's self-duality, weight divisibility, determinant certificates, kissing number censuses.

**Recomputed only when asked (exhaustive):** Results requiring brute-force enumeration (e.g., ternary minimum distance 15 by exhausting an information set, full-weight census by 2²³ Gray-code steps). The default report flags these as `exhaustive: false`, and the sign-off release runs them.

**Not computed at all:** Results not attempted here (e.g., the kissing number in 48 dimensions, reported as `null` with `kissing_source: "not computed here"` rather than quoting a literature value).

**Where Lean and Python disagree, Lean is the specification** (directive D8). Every `GLM.…` name written anywhere in the package is looked up against the development's declaration index by `tests/test_lean_address.py`, so a module cannot cite a theorem that is not there.

### 14.3 Key Machine-Checked Results

A selection, grouped by domain; every name is a declaration in `RequestProject/GLM/`.

**Layer architecture** (`Layers.lean`, `LayerChain.lean`, `Cumulative.lean`, `Tower.lean`, `Stack.lean`):
- `GLM.Info.glmChain_refines_of_le` — the five-layer chain is a refinement (nothing true below becomes false above)
- `GLM.Info.entryResolution_mono` — resolution rises with the layer, for any register
- `GLM.Info.entryResolution_le_distinct` — no layer resolves more entries than there are distinct carriers
- `GLM.Info.substrate_addition_not_congruent` — addition does not descend below the rational layer

**Tax conservation** (`TaxConservation.lean`, `Constants.lean`):
- `tax_conservation` — TAX(a ⊕ b) + 2·TAX(a ∧ b) = TAX(a) + TAX(b) on binary carriers
- `tax_conservation_fails_at_integer_layer` — the law fails irreparably above binary
- `Y_lt_half` — Y = 1/(π + 2/π) < 1/2, so no repair is possible

**Golay boundary and code** (`GolayBoundary.lean`, `Golay/Sextet.lean`, `GolayWeightEnum.lean`, `Steiner.lean`):
- `snap_unique_of_le_three`, `snap_ambiguous_at_four`, `snap_boundary_at_three` — 3 is exactly the largest radius for uniqueness
- `ties_card_eq_six` — the tie at distance four is exactly six
- `golay_weight_enumerator`, `unique_octad`, `card_octads_through_four` — the enumerator 1, 759, 2576, 759, 1, the Steiner system S(5, 8, 24), and λ₄ = 5

**Speed of light and calibration** (`Lightspeed.lean`, `Calibration.lean`):
- `speed_not_from_action_and_energy` — no integers a, b give (0,1,−1) from (1,2,−1) and (1,2,−2)
- `cellLength_div_cellDuration` — ℓ_cell/T_cell = c identically (circularity)
- `octad_min_tax` — octads minimise the codeword tax (on the code layer)
- `refIndex_strictMono` — n(T) is strictly increasing in T

**First principles** (`Packing.lean`, `FitCapacity.lean`):
- `perfect_triple_length` — for 4 ≤ n ≤ 2000, a perfect three-error-correcting binary code has length 7 or 23
- `ball3_closed_form` — Σ_{i≤3} C(n,i) = (n³ + 5n + 6)/6
- `parityExt_min_distance` — the parity extension raises an odd minimum distance by one
- `fit_capacity` — N candidate formulas match a target set of measure at most 2Nδ
- `GLM.Distinction.two_element_ring_is_zmod_two`, `GLM.Distinction.perm_bool_eq` — the arithmetic and the toggle are forced by a two-state carrier

**Projection** (`SeedLayers.lean`, `StepCost.lean`):
- `transcendental_not_trace_of_finite_order` — no finite symmetry produces a transcendental invariant
- `lattice_character_ne_pi` — unconditionally, no lattice symmetry has π as a character value
- `phi_is_trace_of_order_ten` — φ is literally the trace of a rotation of order 10
- `nrci_gauge_independent` — the coherence ladder does not depend on the value of Q

**The seeds** (`SeedRoles.lean`, Phase 61):
- `GLM.SeedRoles.eSeed_irrational` — e is irrational (Fourier's argument), so `GLM.SeedRoles.lattice_character_ne_eSeed_unconditional` holds with no hypothesis
- `GLM.SeedRoles.seeds_not_ratio_of_counts` — no seed is a ratio of integers, so the seeds are an input to the binary principle
- `GLM.SeedRoles.phi_unique_positive_root`, `GLM.SeedRoles.pi_least_positive_zero`, `GLM.SeedRoles.e_unique_unit_growth_base` — each seed is forced by its role
- `GLM.SeedRoles.hull_alternatives`, `GLM.SeedRoles.three_monomials_give_thirteen`, `GLM.SeedRoles.thirteen_not_invertible` — the combining rule is free and 13 cannot be run backwards
- `GLM.SeedRoles.quadratic_pisot_ge_phi`, `GLM.SeedRoles.plastic_lt_phi`, `GLM.SeedRoles.phi_badly_approximable` — φ is the least quadratic Pisot number, not the least Pisot number, and is badly approximable
- `GLM.SeedRoles.pi_mul_e_dichotomy`, `GLM.SeedRoles.monad_irrational_of_pi_mul_e_transcendental` — the two branches of the π·e question, neither asserted

**The machine's own guarantees** (one file per mechanism; §19–§21 give the context):
- `GLM.Conversation.resolve_bound_licensed`, `tie_is_refused`, `most_recent_mention_is_not_the_antecedent` — a bound antecedent is always a licensed one, a tie between licensed candidates is refused, and recency alone would have chosen wrongly
- `GLM.CoordinateOrder.naive_order_is_not_scale_free`, `order_scale_invariant` — why two readings on different scales are refused
- `GLM.ColumnExtremum.extremum_over_present_is_not_the_extremum` — why a column with a hole has no extremum
- `GLM.ScaleConversion.orderWith_conservative` — a declared conversion adds answers only where the table speaks
- the files `RoleBinding.lean` and `PlanStore.lean` — the parity binding inverts unconditionally, and a stored plan replays what it stored
- `GLM.SemanticPlan.accept_perm`, `disagreement_is_ambiguous`, `planned_conservative`, `first_licensed_order_dependent` — the planner's answering rule does not depend on the order plans are tried, refuses whenever two licensed plans disagree, only adds to what the grammar answers, and the obvious alternative (take the first plan that works) does depend on order
- `GLM.Engineering.ohm_power_derivable`, `smith_round_trip`, `ds_rational_period_iff` — wheel derivability, the Smith map, and the least period of a delta–sigma stream
- `GLM.Anonymous.overlap_anonymise_eq_zero` and the file `Relay.lean` — the anonymous register shares no identifier with the corpus, and what the relay's gate guarantees

**Proved in the archive and not rebuilt here** (quoted in §12): the MOG-cube language results (`Dialogue.reply_true`, `IntegerCube.integer_accepts_eq_equations`, `laws_are_never_missed`). The floor and Pisot results this paragraph listed before Phase 61 are now rebuilt, under `GLM.SeedRoles`. Earlier drafts of this paper cited one of these under a name no development contains; the name used for the perfect-code result is now the one in `Packing.lean`.

### 14.4 The Axiom Audit

Every headline theorem is audited with `#print axioms`. The kernel-checked theorems depend only on `propext`, `Classical.choice` and `Quot.sound`; the finite searches discharged by `native_decide` additionally depend on `Lean.ofReduceBool` and `Lean.trustCompiler`, which is the compiler-trust boundary the audit makes visible rather than hides. No theorem rests on an added `axiom` declaration: hypotheses such as "π is transcendental" are arguments to theorems, never axioms. "e is irrational" was one such hypothesis, because the pinned Mathlib does not carry it, until Phase 61 proved it (`GLM.SeedRoles.eSeed_irrational`). The per-file audit is recorded in [`overlay/glm_lean/RequestProject/GLM/README.md`](../overlay/glm_lean/RequestProject/GLM/README.md).

---

## 15. First-Principles Analysis

### 15.1 What Is Forced, What Is Chosen

The first-principles sub-study (`data_object/FirstPrinciples/`) starts from the framework's own logical beginning — "there is a binary distinction and it can be toggled" — and asks at each step: what is forced, what is chosen, and what had to be brought in from outside?

The chain divides into three parts:

**Part 1 (Stages 0–2) is genuinely first-principles and genuinely works.** From "there is a distinction" you get, with no further input: the two-element field, the state space (ℤ/2ℤ)ⁿ, the toggle group, the Hamming metric, the 2t+1 criterion for unique decoding, the sphere-packing bound, and the fact that a perfect three-error-correcting binary code can exist only at lengths 7 and 23. This is the honest core of the UBP architecture.

**Part 2 (Stage 3) is where the framework stops being first-principles.** Every quantity produced by Part 1 is an integer. Each of π, φ, e is irrational. Therefore no seed is obtainable from the substrate by any rational expression in its counts (FP-19): the seeds are an **input**, not an output, of the binary principle. Each seed is forced by the rôle it is given — φ by self-similarity, π by rotational closure, e by unit growth rate — but the step that multiplies them into ℳ = πφe and reads off the integer 13 is a free choice. All of this is now under this repository's build: `GLM.SeedRoles.seeds_not_ratio_of_counts`; `GLM.SeedRoles.phi_unique_positive_root`, `GLM.SeedRoles.pi_least_positive_zero` and `GLM.SeedRoles.e_unique_unit_growth_base` for the three roles; and `GLM.SeedRoles.hull_alternatives` for the free choice — ⌊πe/φ⌋ = 5, ⌊πφ²e⌋ = 22 and ⌊πφe²⌋ = 37 are exactly as simple as ⌊πφe⌋ = 13.

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

## 16. The Projection Sub-Study: Where Seeds Enter

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

The trace map on SL(2,ℤ) has infinite fibres: two matrices with the same trace, determinant, and characteristic polynomial are not conjugate over ℤ. The floor function ⌊·⌋ over 13 has a fibre of measure 1, and three different seed monomials land in it: πφe = 13.817..., πφ³ = 13.308..., π⁴/e² = 13.182.... "Run 13 backwards to the seeds" is impossible, and that is a theorem (`GLM.SeedRoles.trace_fibre_infinite`, `GLM.SeedRoles.same_trace_not_conjugate`, `GLM.SeedRoles.floor_fibre_measure`, `GLM.SeedRoles.three_monomials_give_thirteen`, `GLM.SeedRoles.thirteen_not_invertible`). Every seed's number forgets something in the same way: 2π forgets the winding number (`GLM.SeedRoles.period_fibre_infinite`), and e, the time-one value of the flow f′ = f (`GLM.SeedRoles.flow_time_one`), forgets the clock (`GLM.SeedRoles.e_flow_fibre`). Which kind of motion a number comes from is decided by the trace alone (`GLM.SeedRoles.sl2_trichotomy`): elliptic for π, parabolic for the shear, hyperbolic for φ.

### 16.4 Q Is a Gauge, Not an Observable

Once the coherence budget is calibrated to the quantum, the NRCI ladder is 8/(8+n) whatever Q is. No statement about coherence can depend on the value of Q. This is proved: `nrci_gauge_independent`.

### 16.5 What Is Out of Reach

The study is explicit about what it cannot prove:
- Algebraic independence of π and e (open problem)
- Necessity of the modelling choices (sufficiency is provable, necessity never)
- The icosian construction of the Leech lattice in full
- "Meaning", "Time", "resonance" as physics (not mathematics)

### 16.6 In What Sense φ Is Cheapest

The framework calls φ "the cheapest self-similarity an integer lattice
supports". That is right in two dimensions and wrong in general. φ is a
quadratic Pisot number (`GLM.SeedRoles.phi_isQuadPisot`), and no quadratic Pisot
number is smaller (`GLM.SeedRoles.quadratic_pisot_ge_phi`, by a two-line integer
case analysis). The plastic number ρ ≈ 1.3247, the real root of x³ = x + 1, is
smaller (`GLM.SeedRoles.plastic_lt_phi`), and it is a Pisot number: its two
complex conjugates lie strictly inside the unit disc
(`GLM.SeedRoles.plastic_conjugates_inside_disc`). The property that actually
makes φ extremal in packing and stability arguments is a different one: φ is
badly approximable, |φ − p/q| ≥ 1/(3q²) for every rational p/q
(`GLM.SeedRoles.phi_badly_approximable`; the sharp constant is 1/√5), and so it
is not a Liouville number (`GLM.SeedRoles.phi_not_liouville`).

### 16.7 The Two Branches of the Independence Question

Whether π·e is transcendental is open, and the framework's claim that no seed
is derivable from the others depends on it. What is not open is that there
are exactly two branches (`GLM.SeedRoles.pi_mul_e_dichotomy`). If π·e is
transcendental, the monad, the wobble and the leak are all irrational
(`GLM.SeedRoles.monad_irrational_of_pi_mul_e_transcendental`,
`GLM.SeedRoles.wobble_irrational_of_pi_mul_e_transcendental`). If π·e is
algebraic, a rational monad would *force* that, which is an algebraic relation
between π and e (`GLM.SeedRoles.pi_mul_e_isAlgebraic_of_monad_rat`). Both are
stated with the transcendence status as a hypothesis; neither is asserted.

---

# Part V: The Machine

Parts I–IV are the substrate and what can be proved or calibrated about it.
This part is the machine built on it in this repository — the package
`overlay/glm_universal/`, reached through `overlay/GLM.py` — and what it has
been measured to do. It is written in the present tense: what the machine *is*
now, with the study that measured each part named beside it. What each round
*did* is the phase record in [`MASTER_PLAN.md`](../MASTER_PLAN.md); where the
work stands is [`STATUS.md`](../STATUS.md).

## 17. Architecture: One Carrier, Three Columns, Named Refusals

### 17.1 The package

`glm_universal` is pure Python standard library with exact arithmetic and no
randomness anywhere a result is computed. Its eleven sub-packages are layered
strictly — `substrate`, `data_objects`, `reasoning`, `semantics`, `recipe`,
`language`, `runtime`, `migration`, `benchmarks`, `capabilities`,
`evaluation` — with the Phase 59 `engineering` surface beside them as an
opt-in package, the `sandbox` holding what is not yet relied on, `signoff` and
`corpus` holding the repository's own instruments, and `integrity.py` holding
every SHA-256 use one level above the core. The reasoning kernel alone is
<!--figure:reasoning-modules-->93<!--/figure--> modules.

### 17.2 The carrier

Every object the machine holds — a physical quantity, an element, a molecule, a
musical interval, a price, a word, a Lean declaration — is one shape: a
24-tuple of exact rationals, the **carrier** of §4.3, read at the resolution of
whichever layer is asking. The 24-bit word, the syndrome, the MOG cell, the
Leech point and the shell are projections of it at stated resolutions, and the
layer chain of §4 is what licenses reading it at more than one.

### 17.3 The substrate, as shipped

Complete syndrome decoding with no silent tie-break (§3.4); the full Leech
lattice in place of Construction A (kissing number 196,560); the exact 2A
Sakuma product in place of the XOR shortcut, proved non-associative in
`Sakuma.lean`; the six-facet orthogonal decomposition (`Facets.lean`); and a
quantiser that decodes through the LLVQ class table — a 16-entry column table, the
64 hexacode words, 128 classes of 32 — rather than by scanning the code, which is
exact and is what makes a whole-corpus measurement affordable
([`LLVQ_TABLE_STUDY.md`](LLVQ_TABLE_STUDY.md)). No substrate table is stored:
the last one was replaced by twelve parity checks against 36 bytes, proved
equivalent ([`ZERO_STORAGE_V5_STUDY.md`](ZERO_STORAGE_V5_STUDY.md)).

### 17.4 The query, and the three columns

A question enters as one of <!--figure:query-kinds-->24 query kinds<!--/figure-->
— `verify`, `analogy`, `describe`, `nearest`, `product`, `cluster`, `spatial`,
`project`, `trilinear`, `coherence`, `report`, `angle`, `task`, `pi_groups`,
`meaning`, `real`, `compare`, `measure`, `comparative`, `derive`, `field`,
`ordering`, `extremum`, and `unknown` for what matches none — and `report`
dispatches <!--figure:report-subjects-->65 report subjects<!--/figure-->, each a
study that recomputes itself on demand. Every answer is the three-column
payload of §2.3: the reasoning in language, the same steps as exact equations,
and a generated script that re-derives the second column in a fresh
interpreter. An answer is reported verified only when the re-derivation
agrees.

### 17.5 Refusal is an answer

When the machine cannot answer it says so, and it says *why*: a named reason
from a declared set (an unknown row, a field the register records as missing,
two readings on different scales, a column with a hole in it, two licensed
readings that disagree). The evaluation scores this asymmetrically — an honest
refusal `+1`, a confidently wrong answer `−1` — so the machine is built to
prefer the first. Much of Part V is the story of refusals becoming answers one
declared case at a time, and of refusals that were kept because the answer
would have been a guess.

## 18. Registers and Meaning

### 18.1 The registers

<!--figure:registers-->8 registers<!--/figure-->, holding
<!--figure:binding-carriers-->1,143<!--/figure--> carriers between them:

| register | carriers | what a row is |
|---|---|---|
| physics | 726 | a quantity, with EXT10 exponents and a unit string cross-checked against each other |
| chemistry | 118 | an element, with its sparse measured fields and their provenance |
| molecules | 51 | a species or ion, every coordinate derived from the element register at load time |
| mathematics | 22 | a mathematical object |
| lexicon | 149 | a concept, with ten semantic primitives and explicit relation triples |
| spatial | 28 | a spatial configuration |
| harmonics | 28 | a musical interval as an exact rational frequency ratio |
| economics | 21 | a quoted price as an exact rational |

Beside them sits a 45-class comparison register for measure words
([`RELATIVE_MEASURE_STUDY.md`](RELATIVE_MEASURE_STUDY.md)) and a declared
energy-conjugate table for cross-register analogy
([`CONJUGATE_STUDY.md`](CONJUGATE_STUDY.md)).

### 18.2 A register is not allowed to invent

Sparse chemistry is decided rather than left blank: 9 fields take a rule that
beat the field's own mean out of sample, 185 cells are filled by labelled
estimate, and every cell still empty carries one of three stated reasons
([`ELEMENT_COMPLETION_STUDY.md`](ELEMENT_COMPLETION_STUDY.md)). A new name is
admitted only when a stated route gives it coordinates computed from a register
the machine already checks ([`ADMISSION_STUDY.md`](ADMISSION_STUDY.md)); what an
undimensioned name denotes is a vocabulary decision, recorded as one
([`DENOTATION_STUDY.md`](DENOTATION_STUDY.md)); and a vague `related_to` triple
is routed through four declared routes of which only the last asks a person
([`VAGUENESS_STUDY.md`](VAGUENESS_STUDY.md)). A register can be regenerated
from its description with every measured figure unchanged
([`RECIPE_STUDY.md`](RECIPE_STUDY.md)).

### 18.3 Meaning, not spelling

The grounded graph holds 357 meanings, 1,705 notations and 12,859 edges, every
one re-derived on demand. The inherited ARC-era concept graph, which hashed a
spelling and snapped it near a codeword, was audited and demoted to evidence: a
hash of a spelling identifies a string and measures nothing about what the
string means (directive D3), and `tests/test_inherited_graph.py` walks the
imports of every module that answers a question to keep it out
([`Semantics/Meaning.lean`](../RequestProject/GLM/Semantics/Meaning.lean),
[`Semantics/Grounding.lean`](../RequestProject/GLM/Semantics/Grounding.lean)).
Torque and energy are the same in SI7 and different in EXT10, which adds plane
angle, solid angle and information; the projection between them is lossy
exactly where those exponents are nonzero, and the machine says which.

## 19. The Answer Surface: From a Row to a Plan

The surface grew outward from a single register row, one declared operation at
a time, each measured on questions written before the code. Each step says of
itself whether it is `table`, `address` or `derive` (§22.3).

| operation | what it does | measured on its declared set | study |
|---|---|---|---|
| **field surface** | one named field of one named row, over <!--figure:fieldsurface-tables-->13<!--/figure--> tables, <!--figure:fieldsurface-rows-->9,248<!--/figure--> rows and <!--figure:fieldsurface-pairs-->55,173<!--/figure--> addressable pairs | answers <!--figure:fieldsurface-moved-->9<!--/figure--> of the <!--figure:fieldsurface-held-->10<!--/figure--> held-but-unreachable probe questions, exactly the <!--figure:fieldsurface-predicted-->9<!--/figure--> declared reachable | [`FIELD_SURFACE_STUDY.md`](FIELD_SURFACE_STUDY.md) |
| **ordering** | one coordinate off two rows, ordered exactly, refused across scales | answers <!--figure:ordering-answered-->4<!--/figure--> and refuses <!--figure:ordering-refused-->3<!--/figure--> of <!--figure:ordering-declared-count-->7<!--/figure-->, every one as declared | [`ORDERING_STUDY.md`](ORDERING_STUDY.md) |
| **extremum** | one coordinate over every row of a table, folded or refused | folds <!--figure:extremum-answered-->4<!--/figure--> and refuses <!--figure:extremum-refused-->4<!--/figure--> of <!--figure:extremum-declared-count-->8<!--/figure--> columns, every one as declared | [`COLUMN_EXTREMUM_STUDY.md`](COLUMN_EXTREMUM_STUDY.md) |
| **scale conversion** | a declared table of <!--figure:scales-rows-->9<!--/figure--> scales over <!--figure:scales-quantities-->4<!--/figure--> quantities | answers <!--figure:scales-answered-->7<!--/figure--> and refuses <!--figure:scales-refused-->5<!--/figure--> of <!--figure:scales-declared-->12<!--/figure-->; relates <!--figure:scales-bridged-->6<!--/figure--> of <!--figure:scales-pairs-->7,750<!--/figure--> scale pairs and refuses the rest | [`SCALE_CONVERSION_STUDY.md`](SCALE_CONVERSION_STUDY.md) |
| **conversation** | a follow-up bound to an earlier turn by licensing, not recency | binds <!--figure:conversation-answered-->8<!--/figure--> and refuses <!--figure:conversation-refused-->7<!--/figure--> of <!--figure:conversation-declared-count-->15<!--/figure--> follow-ups; a session with no memory answers <!--figure:conversation-alone-->0<!--/figure--> | [`CONVERSATION_STUDY.md`](CONVERSATION_STUDY.md) |
| **role binding and plan store** | a typed relation as one 24-bit word; a resolved follow-up kept under a digest of the whole conversation | the filler's name recovered for <!--figure:binding-recovered-->6<!--/figure--> of <!--figure:binding-declared-count-->12<!--/figure--> bindings and refused for <!--figure:binding-refused-->6<!--/figure-->; all <!--figure:planstore-replayed-->15<!--/figure--> follow-ups replay unchanged, licensing trials <!--figure:planstore-trials-first-->27<!--/figure--> → <!--figure:planstore-trials-replayed-->0<!--/figure--> | [`SUPPLIED_PORTS_STUDY.md`](SUPPLIED_PORTS_STUDY.md) |
| **typed question plans** | <!--figure:plans-frames-->18<!--/figure--> frames read an English question into typed plans over the operations above; answered only when every licensed plan agrees | the frozen language probe <!--figure:plans-probe-correct-->19<!--/figure--> correct, <!--figure:plans-probe-wrong-->0<!--/figure--> wrong, <!--figure:plans-probe-refused-->1<!--/figure--> refused; held-out <!--figure:plans-held-correct-->86<!--/figure--> correct and <!--figure:plans-held-correct-refusal-->22<!--/figure--> correct refusals of <!--figure:plans-held-total-->110<!--/figure-->, <!--figure:plans-held-wrong-->1<!--/figure--> wrong | [`SEMANTIC_PLAN_STUDY.md`](SEMANTIC_PLAN_STUDY.md) |
| **engineering languages** | formula wheels as exact exponent-vector relations, the Smith chart over the Gaussian rationals, mechanical–electrical analogy, delta–sigma modulators | 63 pre-registered questions: 53 correct, 10 correct refusals, 0 wrong, where both earlier paths answered none; wheels 41 / 41, Smith chart 16 / 16, force–voltage analogy 9 / 9 each way | [`ENGINEERING_LANGUAGE_STUDY.md`](ENGINEERING_LANGUAGE_STUDY.md) |

Three things about this table are worth stating outright.

* **Every refusal it lists was declared before the run**, and most are
  *proved* to be the right answer: `naive_order_is_not_scale_free` exhibits a
  rescaling that flips a comparison of raw numbers;
  `extremum_over_present_is_not_the_extremum` exhibits a column whose extremum
  over its filled rows is a different value at a different row; the
  conversation layer refuses the fourteen-way tie at the top of the lexicon's
  `abstract_concrete` column rather than choose a referent.
* **The planner and the engineering surface are opt-in** (`GLM.py --plan`,
  `GLM.py --eng`), because the command line renders every answer as a
  three-column trace and a computed plan has no trace kind yet. Making the
  planner the default is the first named candidate for a later round.
* **Their wrong answers are named.** The planner's one held-out error is the
  element register holding iron's atomic weight as `55.84` where the answer key
  uses `55.845`: a precision fault in a register, not in the planner. The
  engineering stress set's first run is frozen at 27 correct, 1 wrong and 10
  correct refusals, and its one "wrong" answer is a formatting mismatch of the
  same value.

## 20. Escalation and Ladders

§4 proves that loss at a layer boundary is exactly gain above it. The machine
uses that as an operating rule: when a reading at one layer cannot decide, it
escalates to a finer one, declared before it is taken and costed (directive
D13).

### 20.1 The construction ladder and the norm family

The ladder from ℤ²⁴ through D₂₄ and Constructions A, B and C, generated from
their conditions with the scalings that fill the gaps, is eleven rungs; an
escalated reading over it names **462** of 568 declared queries correctly with
**0** wrong, against **327** for the five rungs the supplied note proposed and
**283** for the best single rung
([`CONSTRUCTION_LADDER_STUDY.md`](CONSTRUCTION_LADDER_STUDY.md)). Indexed by
minimum squared norm it becomes a family of
<!--figure:normfamily-rung-count-->25<!--/figure--> rungs over
<!--figure:normfamily-norms-->12<!--/figure--> norms; the complete family is
*not* safe — it answers <!--figure:normesc-family-wrong-->1<!--/figure--> query
wrongly — so the declared retirement rule removes the rung at fault, and the
repaired <!--figure:normesc-rungs-->10<!--/figure-->-rung ladder names
<!--figure:normesc-correct-->467<!--/figure--> of
<!--figure:normesc-queries-->568<!--/figure--> with
<!--figure:normesc-wrong-->0<!--/figure--> wrong
([`NORM_FAMILY_STUDY.md`](NORM_FAMILY_STUDY.md), `NormFamily.lean`).

### 20.2 Operations other than retrieval, and the second reading

<!--figure:opesc-count-->7<!--/figure--> operations other than retrieval were
escalated under the same discipline against substrate-removed controls; every
one gains, and one — program text — answered
<!--figure:opesc-program-wrong-->13<!--/figure--> of
<!--figure:opesc-program-queries-->576<!--/figure--> queries wrongly and was
reported unsafe ([`OPERATION_ESCALATION_STUDY.md`](OPERATION_ESCALATION_STUDY.md)).
Requiring a second reading at another layer to agree removes all thirteen:
`<!--figure:secondread-shipped-->strict+margin<!--/figure-->`, the
<!--figure:secondread-adopted-->1<!--/figure--> of
<!--figure:secondread-configurations-->6<!--/figure--> declared configurations
that met all four pre-registered marks, answers
<!--figure:secondread-program-correct-->366<!--/figure--> correctly and
<!--figure:secondread-program-wrong-->0<!--/figure--> wrongly, at a counted
cost of <!--figure:secondread-given-up-->150<!--/figure--> answers given up
([`SECOND_READING_STUDY.md`](SECOND_READING_STUDY.md), `SecondReading.lean`).

### 20.3 Escalation inside the query loop

Escalation is a step of the ordinary query loop, not a separate tool: over the
whole evaluation set no answer moves and no principled refusal is converted,
while four of the declared probes are resolved above the first rung
([`QUERY_ESCALATION_STUDY.md`](QUERY_ESCALATION_STUDY.md), `EscalationLoop.lean`).
Stalled results are registered and ranked before the next re-reading rather
than after it ([`REVIEW_SWEEP_STUDY.md`](REVIEW_SWEEP_STUDY.md)), and a layer
family ships only with its refinement check — declared edges verified,
declared non-edges witnessed (directive D12,
[`CUMULATIVITY_STUDY.md`](CUMULATIVITY_STUDY.md)).

### 20.4 The deep holes

The Niemeier deep holes of the Leech lattice were classified from the
trajectories of a walk, pre-registered against controls including a
vertex-count baseline fixed in advance: the trajectory statistic beat every
control (15 of 44 against 11 for the vertex count), and the round stopped
itself because its sanity check kept only 3 of 10 labels under a bare seed
change ([`DEEP_HOLE_STUDY.md`](DEEP_HOLE_STUDY.md)). Read one layer up and
escalated over layer × budget cells, the same question passes the sanity check
10 of 10 and names 40 of 44 at the joint reading
([`DEEP_HOLE_ESCALATION_STUDY.md`](DEEP_HOLE_ESCALATION_STUDY.md)); the four
remaining failures are near misses at rank 2 and share one mechanism with the
unmet separation criterion
([`DEEP_HOLE_FAILURE_STUDY.md`](DEEP_HOLE_FAILURE_STUDY.md)). The census of the
23 root systems is searched for rather than tabulated (`Niemeier.lean`).

## 21. Addressing: The Geometry as an Index

The second of the Positioning's four questions — can language, mathematics and
program text be mapped onto the lattice — is asked most sharply of the Lean
development itself, because it is a corpus whose ground truth is known.

* **The Lean address book.** Each of the
  <!--figure:lean-declarations-->3,766<!--/figure--> declarations gets a
  deterministic Leech address computed from 24 structural counts of its
  statement, read back exactly, with nearest-by-address sharing a source file
  far more often than a SHA-256 control or a seeded reshuffle does
  ([`LEAN_ADDRESS_STUDY.md`](LEAN_ADDRESS_STUDY.md)). Determinism: yes. Meaning:
  partly — and the two are not the same thing.
* **Against plain text it loses, and the loss is recorded.** Where the names
  are available, retrieval by address is a real index and is beaten decisively
  by text search ([`ADDRESS_RETRIEVAL_STUDY.md`](ADDRESS_RETRIEVAL_STUDY.md));
  the same holds for the documents of this repository, where the address
  contributes a shortlist complete up to a stated radius rather than a better
  ranking ([`CORPUS_ADDRESS_STUDY.md`](CORPUS_ADDRESS_STUDY.md)). Most Leech
  addresses in the development are not unique, and the tie class is enumerated
  exactly ([`TIE_BREAK_STUDY.md`](TIE_BREAK_STUDY.md)).
* **Where the names are taken away, it holds.** In the anonymous register — a
  goal written in another formalisation's vocabulary, modelled by renaming
  everything outside a declared vocabulary, and proved to share no identifier
  with the corpus (`overlap_anonymise_eq_zero`) — text search and the
  identifier address book fall to the hit rate chance gives while the
  structural address keeps most of what it had
  ([`ANONYMOUS_REGISTER_STUDY.md`](ANONYMOUS_REGISTER_STUDY.md)).
* **As a stack, it helps the leader.** Given a stated confidence gate and only
  the queries the leading text faculty cannot read, the geometry carries more
  queries than it loses (13 against 0 over 1,658 queries), where a
  digest-and-reshuffle relay under the same gate carries 2. The gain is
  strict on all three query sets on the current corpus — but that standing
  moves with the corpus: when Phase 59 added one Lean file the goal set fell
  level, and when Phase 61 added three it rose again, and the study records
  each move rather than the best figure
  ([`STACK_RELAY_STUDY.md`](STACK_RELAY_STUDY.md), `Relay.lean`).
* **Procedures are retrievable the way numbers are**: a search loop's hard gate
  admits exactly what it can check, and the ranking's limits are measured as a
  census ([`SEARCH_LOOP_STUDY.md`](SEARCH_LOOP_STUDY.md)); the propose–check–
  refuse loop re-verifies every returned plan and carries a proof with each
  refusal ([`CONTROLLER_STUDY.md`](CONTROLLER_STUDY.md)).

## 22. Measured Capability

### 22.1 The four instruments

| instrument | what it measures | result |
|---|---|---|
| end-to-end CLI evaluation | the command line in a fresh interpreter per question, scored asymmetrically | <!--figure:evaluation-case-count-->177<!--/figure--> cases: 149 answered correctly, 28 refused as expected, **0 confidently wrong** |
| capability probes | where the library stops, asked as user questions | 33 probes: 20 hold, 13 break — each break a located boundary, not a failure |
| benchmark suites | solver functions against curated and exhaustive task sets | 2,389 / 2,390 across 5 suites, every suite above its declared baseline |
| test suite | the package's own regression net | <!--figure:suite-->4,267 tests across 108 of the 109 test files, 16,276 subtests, outside the document check<!--/figure--> |

The thirteen probe breaks are the machine's measured edges, spread over nine
areas (algebra, carriers, dynamic carriers, layers, reals, scale, semantics,
substrate; every runtime probe holds). The four that matter most for a user,
in the probes' own terms: the repair radius is exactly 3 — at weight 4 six
codewords are equally near and at weight 5 the answer is unique, confident and
wrong, because the octads form `S(5,8,24)`; the Norton–Sakuma product is not
associative; the TAX law is exact on binary carriers and fails over the
naturals; and the vocabulary is exactly the registers
([`CAPABILITY_ASSESSMENT.md`](../CAPABILITY_ASSESSMENT.md) §3). Each is the
machine reporting a theorem of Parts I–IV back as behaviour.

### 22.2 The pre-registered language probe

The sharpest single measurement of what blocks fuller reasoning is a probe of
<!--figure:probe-questions-->20<!--/figure--> English questions with a declared
pass mark of <!--figure:probe-pass-mark-->10<!--/figure-->. Asked through the
default path it scores <!--figure:probe-correct-->2<!--/figure--> correct,
<!--figure:probe-wrong-->1<!--/figure--> wrong and
<!--figure:probe-refused-->17<!--/figure--> refused — a declared failure, kept
as one ([`BLOCKERS_STUDY.md`](BLOCKERS_STUDY.md)). Widening the lexicon to
<!--figure:probe-lexicon-held-->57<!--/figure--> of the probe's
<!--figure:probe-lexicon-words-->69<!--/figure--> content words moved nothing;
translating each question into the query grammar by hand showed the refusals
are three different failures — <!--figure:oracle-parsed-->6<!--/figure-->
parsed, <!--figure:oracle-surface-->10<!--/figure--> held by a register but
unreachable, <!--figure:oracle-absent-->4<!--/figure--> absent
([`PROBE_ORACLE_STUDY.md`](PROBE_ORACLE_STUDY.md)). The field surface, the
ordering operation and the typed planner of §19 were built against exactly
that diagnosis, and through the planner the same frozen probe now passes its
mark at <!--figure:plans-probe-correct-->19<!--/figure--> correct.

### 22.3 Which faculty moved

The standing target of the project is narrow: a round moves it when the system
**derives** (produces an answer no register holds), **addresses** (recovers an
answer from the geometry when the query is not the stored key) or **refuses**
(withholds an answer that would have been wrong) better than before, under a
perturbation declared in advance. [`BLOCKERS_STUDY.md`](BLOCKERS_STUDY.md) §1
separates the three mechanically, and on its own count only
<!--figure:probe-derived-->2<!--/figure--> measured results were derivation
rather than lookup or addressing when it was taken. Across the
<!--figure:plans-questions-->197<!--/figure--> questions asked both through the
grammar and through the typed planner, the
<!--figure:plans-gained-->147<!--/figure--> answers the planner gains sort into <!--figure:plans-gains-derive-->70<!--/figure-->
derived, <!--figure:plans-gains-table-->76<!--/figure--> looked up and
<!--figure:plans-gains-address-->1<!--/figure--> addressed
([`SEMANTIC_PLAN_STUDY.md`](SEMANTIC_PLAN_STUDY.md) §7). Derivation is the
scarce faculty and stays the one most worth a round.

### 22.4 The four questions, answered as measurements

1. **Mapping.** Yes for the registers (every carrier re-derived from its
   source on load) and for the Lean development (every declaration read back
   exactly from its address). For open English, only through declared frames
   (§19); for program text, the address is a real index that loses to text
   search when names are present and holds when they are not (§21).
2. **Reasoning.** Addressing and refusal are strong and measured; derivation
   is real but narrow — Buckingham-Pi from an exact nullspace, wheel
   derivations over declared axioms, exact arithmetic and conversion inside
   typed plans — and the probe of §22.2 is the measure of how narrow.
3. **Generation.** The machine works with what it holds rather than only
   recalling it wherever a declared operation composes rows (ordering,
   extremum, conversion, plans, wheels); it does not yet compose across a union
   of declared relations, and says so (the first candidate in `STATUS.md`
   §3.4).
4. **Real, accurate, checkable.** Every answer carries its own re-derivation;
   the evaluation has no confidently wrong answer; the known wrong value in a
   register is named rather than hidden.

## 23. The Negative Results

The Positioning calls a refuted claim a result, because it is the cheapest
thing the project produces and the most easily lost. These are the ones that
bear on the system as a whole; each is the verdict of the study named.

| claim tested | verdict | study |
|---|---|---|
| the harmonic register's intervals are distinctive on the lattice | not reproduced against an undecoded control | [`HARMONY_STUDY.md`](HARMONY_STUDY.md) |
| the economic register's prices are distinctive on the lattice | not reproduced; the control is not beaten | [`ECONOMICS_STUDY.md`](ECONOMICS_STUDY.md) |
| the fine-structure constant's wobble signature is structurally distinctive | too weak to spend on (B = 1.79 bits, below the pre-registered gate), so the landscape was not enumerated | [`WOBBLE_LANDSCAPE_STUDY.md`](WOBBLE_LANDSCAPE_STUDY.md) |
| a Leech address retrieves better than reading the words | no — beaten decisively by plain text; for documents, a complete shortlist but no better ranking | [`ADDRESS_RETRIEVAL_STUDY.md`](ADDRESS_RETRIEVAL_STUDY.md), [`CORPUS_ADDRESS_STUDY.md`](CORPUS_ADDRESS_STUDY.md) |
| the proposed zero-storage Leech sieve is complete | sound and 99.4 % incomplete, with the one-line repair stated | [`ZERO_STORAGE_STUDY.md`](ZERO_STORAGE_STUDY.md) |
| the supplied reverse-call planner earns promotion | safety gate holds, utility gate fails on the project's own evaluation set; not promoted | [`REVERSE_CALL_PLANNER_STUDY.md`](REVERSE_CALL_PLANNER_STUDY.md) |
| the elementwise product binding inverts | refuted: <!--figure:binding-product-zero-->1,133<!--/figure--> of the carriers read zero somewhere | [`SUPPLIED_PORTS_STUDY.md`](SUPPLIED_PORTS_STUDY.md) |
| the supplied conversational GLM's higher-order analogy adds a constraint | does not survive being re-run | [`CONVERSATION_STUDY.md`](CONVERSATION_STUDY.md) |
| the accumulator is a receipt of the history | the identity holds and the reading does not: it records the integral mod 1 and nothing else | [`NOW_RECEIPT_STUDY.md`](NOW_RECEIPT_STUDY.md) |
| the full norm family is a safe ladder | no — one wrong answer; the rung at fault is retired | [`NORM_FAMILY_STUDY.md`](NORM_FAMILY_STUDY.md) |
| program-text escalation is safe | no — 13 wrong answers, repaired only by a second reading | [`OPERATION_ESCALATION_STUDY.md`](OPERATION_ESCALATION_STUDY.md) |
| the deep-hole classifier is stable under a seed change | no at the first layer (3 of 10); yes one layer up (10 of 10) | [`DEEP_HOLE_STUDY.md`](DEEP_HOLE_STUDY.md) |
| nine claims in the archive's scripts | false, and proved false in the retrieved Lean | [`RETRIEVED_LEAN_STUDY.md`](RETRIEVED_LEAN_STUDY.md) |
| two questions the archive's deep dive asked | both negative, and both more useful than a positive | [`ARCHIVE_DEEP_DIVE_STUDY.md`](ARCHIVE_DEEP_DIVE_STUDY.md) |
| the pre-registered language probe passes on the default path | no — 2 / 1 / 17 against a mark of 10; passes only through the planner | [`BLOCKERS_STUDY.md`](BLOCKERS_STUDY.md) |
| the Golay/Leech encoding helps the engineering surface | no advantage found, and none claimed | [`ENGINEERING_LANGUAGE_STUDY.md`](ENGINEERING_LANGUAGE_STUDY.md) |
| the relay's gain is a stable property of the mechanism | no — it is a measurement of the current corpus: Phase 59's added file made it tie text on the goal set (2 carried, 2 lost) with the strict band ending at 1/5, and Phase 61's three files restored a strict gain on every set (13 carried, 0 lost) | [`STACK_RELAY_STUDY.md`](STACK_RELAY_STUDY.md) |

Parts I–IV carry their own negatives, which §25.4 collects: the fine-structure
fit worth less than one bit, the substrate unable to derive c, "φ shears"
wrong, the archive's "d² always even" and "exactly half" refuted, and the
floor over 13 not invertible.

---

# Part VI: Method

## 24. How the Repository Keeps Itself Honest

A research programme that spans this much fails most often not by being wrong
but by *ageing*: a figure typed into a document that the code has since moved,
a finding written nowhere, a round re-run in full because nothing recorded what
it depended on. The repository is built against that failure.

**Standing rules with instruments.** [`PROJECT_DIRECTIVES.md`](../PROJECT_DIRECTIVES.md)
states <!--figure:directives-->16 standing rules<!--/figure-->, each naming the
instrument that enforces it, and `report directives` prints each instrument's
live verdict. Among them: no floats (D7), checked by parsing every module; an
operation that is not the substrate's own used only at declared sites (D9,
D11); where Lean and Python disagree, Lean is the specification (D8); a layer
ships with its refinement check (D12); an escalated re-reading is declared
before it is taken (D13); something not yet relied on lives in the sandbox with
a computed promotion checklist (D14); every round says which of derivation,
addressing and refusal it moved, or that it moved none (D15).

**Every figure generated.** Directive D6: every figure a document quotes is
generated by the code that reports it. `glm_universal/figures.py` writes
`overlay/FIGURES.md`, inline figure markers carry the live value into the prose
(as throughout this paper), generated blocks carry whole tables, and
`tests/test_figures.py` fails when a document and the code disagree.
[`GLM_Complete_Number_Theory_Evidence.md`](GLM_Complete_Number_Theory_Evidence.md)
goes further: its own test re-runs its generator and compares every table cell
by cell.

**A document is data.** Directive D10: every document is classified by rule,
carries a tier-0 block (question, verdict, deciding figure, the function that
recomputes it), is addressed, and is checked — the verdict must be grounded in
the document's own words, every link must resolve, and every current-state
document must be reachable from [`ENTRY.md`](../ENTRY.md). The corpus holds
<!--figure:corpus-documents-->98<!--/figure--> documents, of which
<!--figure:corpus-state-documents-->94<!--/figure--> describe the system as it
is and <!--figure:corpus-archive-documents-->4<!--/figure--> are records of a
round, and [`DIGEST.md`](../DIGEST.md) is their tier-0 reading, generated.

**Sign off only what moved.** Directive D16 and `glm_universal/signoff`: every
test file and instrument is signed against a digest of everything it depended
on — its import closure computed with `ast` — so a change re-runs what it
touched and nothing else, and a release runs everything with the exhaustive
cases on. The cost of that loop is itself measured
([`ITERATION_COST_STUDY.md`](ITERATION_COST_STUDY.md)).

**The round.** Orient from the whiteboard and the status document, take a
named candidate, declare the measurement before taking it, work against the
cheapest gate that could fail, write the finding where it belongs — the study,
the status document, the phase record, the Lean — and close with refresh,
check and release ([`ITERATE.md`](../ITERATE.md)). Fifty-nine phases are
recorded in [`MASTER_PLAN.md`](../MASTER_PLAN.md) and its archive, and the
discipline above was assembled over them rather than present from the start.

---

# Part VII: Synthesis

## 25. Synthesis: Proved, Calibrated, Measured, Refuted, Open

### 25.1 The Proven Core

The following are established mathematical facts, machine-checked in Lean in this repository's development unless marked otherwise:

1. **The binary substrate is forced up to one choice.** From "there is a distinction" → 𝔽₂ → (ℤ/2ℤ)ⁿ → Hamming metric → perfect three-error-correcting codes exist only at lengths 7 and 23 (for n ≤ 2000, `perfect_triple_length`) → parity extension to 24 (`parityExt_min_distance`) → Golay code → Leech lattice via A → B → C. No choices are made in this chain until the parity extension, which is chosen for self-duality.

2. **The layer architecture is formally verified.** The five-layer stack is a refinement chain. Information lost at a boundary is exactly new expressive power gained. The ascent is forced by capacity constraints. The dyadic tower is infinite, strictly increasing, cumulative, and exhaustive.

3. **TAX conservation is exact on binary carriers and irreparably broken above.** The boundary is a single constant (Y = 1/(π + 2/π) ≠ 1/2), proved.

4. **The Golay snap radius is sharp.** Unique repair at distance ≤ 3, a six-fold tie at 4, uncorrectable at ≥ 5. The boundary is a single integer. The code's own numbers — the weight enumerator, `S(5,8,24)`, `λ₄ = 5` — are theorems about the development's code, not quotations.

5. **No finite symmetry produces a transcendental number.** φ enters as a character value; π and e must come from flows. For a lattice symmetry the statement needs only irrationality, and it now holds unconditionally for e as well as π, because e is proved irrational (`GLM.SeedRoles.lattice_character_ne_eSeed_unconditional`).

6. **The floor function is not invertible.** Three different seed monomials produce hull 13, so seed recovery is impossible (`GLM.SeedRoles.three_monomials_give_thirteen`, `GLM.SeedRoles.thirteen_not_invertible`; retrieved from the archive's projection development in Phase 61).

7. **The refractive-index law is falsifiable.** n(T) = (24+T)/27 with no empirical parameters. Diamond falsifies it (T > 24).

8. **Gray code is the optimal read channel.** Exactly one bit flip per step (`gray_single_bit`), and the jump between two states is `pop(gray(a XOR b))` (`d2_eq_pop_gray_xor`). **Correction:** "exactly half" is false at every finite width; the sharp statement is `2·gray = binary + 2` (`gray_two_mul_eq`).

9. **Reversible gates perfectly conserve state.** Toffoli and Fredkin are involutions and bijections. The composition has order 3 (`round_cubed`), not order 2. Inverse rounds undo forward rounds exactly. Kink count is rotation-invariant (`kinks_rotate`) and always even (`kinks_even`); single flips move it by {-2, 0, +2}, not exactly ±2.

10. **The delta–sigma stream is exactly characterised.** Its average converges at O(1/N) (`dsAverage_error_le`); its ones count is a floor (`dsOnes_eq_floor`); its least period is the denominator of a rational input and an irrational input never repeats (`ds_rational_period_iff`, `ds_irrational_aperiodic`); its accumulator records the integral mod 1 and nothing else (`acc_eq_iff_fract_eq`).

11. **The machine's refusals are theorems.** A comparison across scales is refused because a rescaling can flip it (`naive_order_is_not_scale_free`); a column with a hole has no extremum (`extremum_over_present_is_not_the_extremum`); the planner refuses when two licensed plans disagree and its rule is order-independent (`disagreement_is_ambiguous`, `accept_perm`); a conversation tie is refused (`tie_is_refused`).

12. **The MOG cube supports a complete verified micro-language** — words with dimension, true sentences, connectives, conversation, learning — proved in the archive's 43-file development; its geometric half is rebuilt here, its language half is not (§12, Appendix C).

13. **The seeds are forced by their roles and by nothing below them.** No seed is a ratio of counts (`seeds_not_ratio_of_counts`); φ, π and e are each the unique number playing its role (`phi_unique_positive_root`, `pi_least_positive_zero`, `e_unique_unit_growth_base`); φ is the least quadratic Pisot number but not the least Pisot number (`quadratic_pisot_ge_phi`, `plastic_lt_phi`).

### 25.2 The Calibrated Results

The following are empirical calibrations, internally consistent but not derived from first principles:

1. **The EM scale function** S(λ, HW) = λ/[HW × (Y + 1/8)] is validated against 48 EM references. It is derived from the substrate's definition, not curve-fit, but the substrate's definition itself contains a chosen constant, Y = 1/(π + 2/π), whose form is not derived.

2. **The mass scale** is internally consistent: m_e formula (0.00919% error), m_μ/m_e ratio (0.02938% error), cross-check m_e × ratio → m_μ (0.039% error). The WOBBLE cancels in the cross-check.

3. **The proton-to-electron mass ratio** m_p/m_e = 1836 + 2L_s achieves 0.0000374% error — the most precise alignment point, worth 2–3 bits of evidence.

4. **The 190 kJ/mol scale factor** is an empirical conversion between geometric work and bond energy, fitted over 114 element pairs whose thermodynamic convention is not stated (§11.5). It places the substrate's *energy* scale in the molecular and optical range; its derived *length*, 17 μm, is not molecular.

5. **Element property encoding** achieves r > 0.90 for electronegativity and boiling point from 24-bit Golay/Leech encodings.

6. **Bond energy prediction** reaches r = 0.55 with warping strategies, and bond order classification reaches 86.8% accuracy.

### 25.3 The Measured Machine

The following are measurements of the machine, each against a control or a declared set, each recomputed by the instrument named in Part V:

1. **No confidently wrong answer** in <!--figure:evaluation-cases-->177 CLI cases<!--/figure-->, 28 of them refusals the machine was expected to make.
2. **The language probe passes through the planner** (<!--figure:plans-probe-correct-->19<!--/figure--> of <!--figure:probe-questions-->20<!--/figure-->) and fails on the default path (<!--figure:probe-correct-->2<!--/figure-->), which is why making the planner the default is the first open item of the machine.
3. **Every declared operation behaves as declared**: field surface, ordering, extremum, scale conversion and conversation each answer and refuse exactly the cases declared before the run.
4. **Escalation is safe where it is shipped**: 462 of 568 on the construction ladder and <!--figure:normesc-correct-->467<!--/figure--> on the repaired norm ladder, both with 0 wrong; the program-text operation made safe by a second reading at a counted cost.
5. **The engineering surface** answers 53 of 63 pre-registered questions and correctly refuses the other 10, with 0 wrong.
6. **Addressing** is deterministic and exact on the Lean corpus, loses to text search when names are present, and holds when they are not.

### 25.4 The Refuted Claims

Kept because a refuted claim is a result: the fine-structure fit is worth less than one bit of evidence; the substrate cannot derive c (it is recovered identically, `substrate_c_is_circular`); "φ shears" is wrong (the Fibonacci matrix is a stretch); the archive's "d² is always even" (`exists_odd_d2`) and "Gray flips exactly half" (`gray_two_mul_eq`) are false; the accumulator is not a receipt of its history (`receipt_collision`); walking a polygon is Euler's totient, not a new primality test (`subCycles_eq_zero_iff_prime`); the product binding does not invert; the harmony and economics correspondences are not reproduced against their controls; the fine-structure constant's wobble signature is too weak to spend on; the address does not beat plain text; nine claims of the archive's scripts are proved false (§23).

### 25.5 The Open Problems

**Of the substrate and its physics:**

1. **The mass residual (0.00919%).** The single most important open problem of the physics. If the residual is α² × (geometric factor), it would connect the UBP mass scale to QED. The corrected value (9.19×10⁻⁵, not 7.2×10⁻⁵) makes the α² hypothesis less clean (1.726α², not 1.35α²).

2. **Null model uniqueness.** 33 out of 50,000 random transcendental combinations match m_e within 0.01%. The formula is motivated (structural integers, precision-stable) but not proven unique.

3. **The missing length.** The substrate cannot derive c (Buckingham's Π theorem). It would need a predicted absorption or scattering length independent of c. Absent that, the correct claim is "the substrate calibrates to a 17 μm cell", not "the substrate derives c".

4. **The TAX spectrum.** Integer TAX (n ≤ 1.778) and codeword TAX (n ≤ 1.235) give different ceilings. The model must commit before it can be tested.

5. **Provenance.** The 275 unreachable physics entries of §4.5 need a coordinate for "of" — what a quantity is a measure *of* — not a new layer.

6. **The VOA beyond the Griess layer.** The state–field map Y(u, z) is now built on the 2A Sakuma algebra (`VOA.lean`), and Borcherds' commutator formula is proved to fail once the discarded modes are dropped; the rank-one Heisenberg vertex algebra is built over the exact rationals (`Heisenberg.lean`). What remains open is the Moonshine module itself: the operator on the 196,884-dimensional Griess algebra, of which these are the finite and the free-boson halves.

7. **Algebraic independence of π and e.** Open problem. The transcendence degree of ℚ(π,e) over ℚ is 1 or 2; both branches of its scalar shadow, whether π·e is transcendental, are formalised conditionally in `SeedRoles.lean` (§16.7).

8. **The κ fit uncertainty.** Every downstream number is proportional to 1/κ. A ±5% fit uncertainty is a ±5% uncertainty on the cell length.

**Of the machine** (the candidates named in [`STATUS.md`](../STATUS.md) §3.4, sharpest first):

9. **Derivation across a declared union of relations.** The engineering surface derives inside one formula wheel at a time and so refuses hydraulic power from pressure and volume flow rate, which follows across two wheels.
10. **Typed physical operators.** Monomial wheels cannot separate real, reactive and apparent power, nor dot from cross product.
11. **The planner as the default path**, which needs a trace kind for the planner's own computations.
12. **A held-out set nobody on the project wrote**, with labels from outside the registers — the test that separates reach from anticipation.
13. **The register against the world**: a discrepancy report of register values against cited standard values (the iron atomic weight is the first row), never overwriting the register.
14. **Typed discourse state** — *the one before that*, *both of them*, and a tie carried forward as a column rather than refused.
15. **The Lean still in the archive.** The MOG cube's language half (about thirty files) is proved in the archive and not rebuilt here, and so are the unported parts of the observer-Y file (Appendix C). The five first-principles and projection files named here before Phase 61 are now rebuilt. Retrieving the language half would put the results quoted in §12 under this repository's own `lake build`.

---

## 26. Conclusion

### 26.1 What the GLM Is

The GLM is a mathematically rigorous 24-dimensional substrate with exact rational arithmetic, and a machine built on it, where:
- The charge scale is exact (vertex count → e/12)
- The velocity scale is exact (MONAD/13 → v/c = 0.339, but this is a definition, not a prediction)
- The mass scale is internally consistent (0.009% error, cross-checks pass)
- The photon as minimum-Tax octad is a mathematical fact on the Golay layer (`octad_min_tax`)
- The layer architecture, the code's arithmetic and the machine's refusals are formally verified in a development of <!--figure:lean-files-->133 Lean files<!--/figure--> with no `sorry`
- The encoding system predicts element properties at r > 0.90
- The machine answers <!--figure:query-kinds-->24 query kinds<!--/figure--> over <!--figure:registers-->8 registers<!--/figure-->, re-derives every answer it gives, and refuses with a named reason where an answer would be a guess

### 26.2 What the GLM Is Not

The GLM is **not** a theory that derives physical constants from first principles. The first-principles analysis proved this conclusively: the seeds (π, φ, e) are inputs, not outputs; the monomial producing 13 is a choice; and two of the three headline numerical agreements are within an order of magnitude of what an arbitrary target would have received.

Nor is it, yet, a general reasoner. It derives narrowly, addresses well where names are absent and poorly where they are present, and answers open English only through declared frames. Those limits are measured, and the measurements are in §22.

### 26.3 The Productive Reframing

**Old:** "Can the substrate derive physical constants?" → No, by Buckingham's Π.

**New:** "Can substrate ratios + SI-defined anchors predict measured constants?" → Partially yes. The substrate supplies dimensionless numbers; the SI supplies the dimensions. This is calibration, not derivation, and it is only as good as the empirical anchors.

**And for the machine:** "Can an exact substrate carry a reasoner?" → It carries one that is never confidently wrong on what it has been asked, whose every answer is re-derivable, and whose every refusal names its reason — which is a narrower thing than a general reasoner and a rarer one.

### 26.4 The Path Forward

The most productive direction is not to chase exact derivations of constants the SI already defines. It is to keep building the **computational engine** — the calibrated substrate as a geometric stability evaluator, and the machine on it widened one declared, measured operation at a time. Derivation is the scarce faculty, and §25.5 items 9–14 are the next steps toward it; item 15 brings the rest of the archive's verified material under this repository's own build.

### 26.5 The Honest Summary

The UBP has genuine mathematical structure that deserves honest acknowledgment. The dimensionless ratios pass null-model tests. The mass scale is internally consistent. The layer architecture is formally verified. The encoding system predicts real chemistry. The machine built on it is exact, checkable and conservative. These are real findings, not numerology.

But the gap between "the substrate has structure that correlates with physical reality" and "the substrate derives physical reality from first principles" remains the central tension of the programme, and the gap between addressing an answer and deriving one remains the central tension of the machine. The studies assembled here map both gaps precisely, and the formal verification ensures that nothing is claimed that cannot be checked.

---

## Appendix A: Every Study

Every document in `studies/`, grouped by the part of this paper it feeds. The
verdict of each, in one line, is in [`DIGEST.md`](../DIGEST.md); this table
says what each is *about* and where this paper uses it.

**The substrate, the layers and the values** (Parts I–II)

| study | subject | used in |
|---|---|---|
| [`INFORMATION_LOSS_STUDY.md`](INFORMATION_LOSS_STUDY.md) | what each layer boundary loses, pair by pair, and the theorems that loss is gain | §4 |
| [`ESCALATION_STUDY.md`](ESCALATION_STUDY.md) | the layer stack on the registers' own carriers, and the resolution ceiling | §4.5 |
| [`CUMULATIVITY_STUDY.md`](CUMULATIVITY_STUDY.md) | three layer families checked for refinement; declared non-edges witnessed | §20.3 |
| [`COMBINER_STUDY.md`](COMBINER_STUDY.md) | why XOR is the only coordinatewise combiner on the substrate, and what a wider output buys | §2.2, §24 |
| [`GEOMETRIC_AMBIGUITY_STUDY.md`](GEOMETRIC_AMBIGUITY_STUDY.md) | the six-fold Golay tie as a sextet, and collapse as a measurement | §3.4 |
| [`TIE_BREAK_STUDY.md`](TIE_BREAK_STUDY.md) | Leech addresses that are not unique, and what a tie-break cannot touch | §21 |
| [`INFINITE_VALUES_STUDY.md`](INFINITE_VALUES_STUDY.md) | irrationals as processes, and what the machine provably cannot do with them | §5 |
| [`NOISE_EXPERIMENT_STUDY.md`](NOISE_EXPERIMENT_STUDY.md) | the wobble as computation: cascades, closed orbits, dither, error feedback | §5.3 |
| [`NOW_RECEIPT_STUDY.md`](NOW_RECEIPT_STUDY.md) | the accumulator as the integral mod 1, and why it is not a receipt of history | §23, §25.1 |
| [`WOBBLE_LANDSCAPE_STUDY.md`](WOBBLE_LANDSCAPE_STUDY.md) | is the fine-structure constant structurally distinctive? pre-registered; too weak | §23 |
| [`HIGHER_LATTICE_STUDY.md`](HIGHER_LATTICE_STUDY.md) | the 32-dimensional Barnes–Wall and 48-dimensional ternary rungs | §8 |
| [`CONSTRUCTION_LADDER_STUDY.md`](CONSTRUCTION_LADDER_STUDY.md) | the eleven-rung ladder from ℤ²⁴ to Λ₂₄, escalated | §20.1 |
| [`NORM_FAMILY_STUDY.md`](NORM_FAMILY_STUDY.md) | the ladder indexed by minimum norm, the unsafe rung retired | §20.1 |
| [`LLVQ_TABLE_STUDY.md`](LLVQ_TABLE_STUDY.md) | the quantiser's scan replaced by a class-table lookup | §17.3 |
| [`ZERO_STORAGE_STUDY.md`](ZERO_STORAGE_STUDY.md) | generating the substrate's tables instead of storing them; the sieve's incompleteness | §23 |
| [`ZERO_STORAGE_V5_STUDY.md`](ZERO_STORAGE_V5_STUDY.md) | the last stored table removed; Golay membership as twelve parity checks | §17.3 |
| [`HEXCOLOUR_STUDY.md`](HEXCOLOUR_STUDY.md) | a hexcolour as a rendering of a carrier, and an address as not a measurement | §21 |

**The audits of supplied material** (Parts III–IV)

| study | subject | used in |
|---|---|---|
| [`GLM_UNIFICATION_BLUEPRINT_AUDIT.md`](GLM_UNIFICATION_BLUEPRINT_AUDIT.md) | every testable sentence of the blueprint given a verdict | Appendix C |
| [`GLM_STUDY_CATALOG_AUDIT.md`](GLM_STUDY_CATALOG_AUDIT.md) | the external findings catalogue as a live claim ledger | Appendix C |
| [`GLM_COMPANION_STUDIES_AUDIT.md`](GLM_COMPANION_STUDIES_AUDIT.md) | the two companion preprints, claim by claim | Appendix C |
| [`SOURCE_SALVAGE_AUDIT.md`](SOURCE_SALVAGE_AUDIT.md) | eleven retrieved Lean files, every number recomputed | §14.1 |
| [`SOURCE_SALVAGE_SECOND_PASS.md`](SOURCE_SALVAGE_SECOND_PASS.md) | eight more results retrieved | §14.1 |
| [`RETRIEVED_LEAN_STUDY.md`](RETRIEVED_LEAN_STUDY.md) | 25 files of Lean from the archive; nine claims found false | §14.1, §23 |
| [`ARCHIVE_DEEP_DIVE_STUDY.md`](ARCHIVE_DEEP_DIVE_STUDY.md) | two questions asked of the archive; both negative | §23 |
| [`PCGS_STUDY.md`](PCGS_STUDY.md) | six systems admitted against six criteria | Appendix C |
| [`GLM_Complete_Number_Theory_Evidence.md`](GLM_Complete_Number_Theory_Evidence.md) | the number-theoretic substrate: every table generated and tested | §2.1, §24 |

**Registers and meaning** (§18)

| study | subject | used in |
|---|---|---|
| [`ELEMENT_COMPLETION_STUDY.md`](ELEMENT_COMPLETION_STUDY.md) | sparse chemistry decided cell by cell | §18.2 |
| [`ADMISSION_STUDY.md`](ADMISSION_STUDY.md) | the door a new name comes in by | §18.2 |
| [`DENOTATION_STUDY.md`](DENOTATION_STUDY.md) | what the undimensioned names denote | §18.2 |
| [`VAGUENESS_STUDY.md`](VAGUENESS_STUDY.md) | a router for vague `related_to` triples | §18.2 |
| [`NAME_COORDINATE_STUDY.md`](NAME_COORDINATE_STUDY.md) | a coordinate for the name, and the control that decides what does the work | §18 |
| [`RELATIVE_MEASURE_PROPOSAL.md`](RELATIVE_MEASURE_PROPOSAL.md) | measure words as relative measures (the proposal) | §18.1 |
| [`RELATIVE_MEASURE_STUDY.md`](RELATIVE_MEASURE_STUDY.md) | the comparison-class register, measured | §18.1 |
| [`CONJUGATE_STUDY.md`](CONJUGATE_STUDY.md) | cross-register analogy through an energy-conjugate table | §18.1 |
| [`ANALOGY_LAYER_STUDY.md`](ANALOGY_LAYER_STUDY.md) | A : B :: C : D, and why a relation is not always a displacement | §22.1 |
| [`HARMONY_STUDY.md`](HARMONY_STUDY.md) | the harmonic register; universality not reproduced | §23 |
| [`ECONOMICS_STUDY.md`](ECONOMICS_STUDY.md) | the economic register; not reproduced | §23 |
| [`RECIPE_STUDY.md`](RECIPE_STUDY.md) | a register regenerated from its description | §18.2 |
| [`LANGUAGE_STUDY.md`](LANGUAGE_STUDY.md) | the question's shape as an object; parser branches deleted | §19 |

**The answer surface and the conversation** (§19)

| study | subject | used in |
|---|---|---|
| [`BLOCKERS_STUDY.md`](BLOCKERS_STUDY.md) | what blocks fuller reasoning; the pre-registered language probe | §22.2 |
| [`PROBE_ORACLE_STUDY.md`](PROBE_ORACLE_STUDY.md) | what a refusal is evidence of | §22.2 |
| [`FIELD_SURFACE_STUDY.md`](FIELD_SURFACE_STUDY.md) | one field of one row, over every declared table | §19 |
| [`ORDERING_STUDY.md`](ORDERING_STUDY.md) | two readings ordered, or refused across scales | §19 |
| [`COLUMN_EXTREMUM_STUDY.md`](COLUMN_EXTREMUM_STUDY.md) | a column folded, or refused for a hole or a second scale | §19 |
| [`SCALE_CONVERSION_STUDY.md`](SCALE_CONVERSION_STUDY.md) | the declared table of conversions | §19 |
| [`CONVERSATION_STUDY.md`](CONVERSATION_STUDY.md) | the turn that refers back, licensed rather than guessed | §19 |
| [`SUPPLIED_PORTS_STUDY.md`](SUPPLIED_PORTS_STUDY.md) | role binding and the plan store shipped; the product binding refuted | §19, §23 |
| [`SEMANTIC_PLAN_STUDY.md`](SEMANTIC_PLAN_STUDY.md) | typed question plans, pre-registered held-out sets | §19, §22 |
| [`ENGINEERING_LANGUAGE_STUDY.md`](ENGINEERING_LANGUAGE_STUDY.md) | formula wheels, the Smith chart, analogy, delta–sigma | §19 |

**Escalation, addressing and the loop** (§20–§21)

| study | subject | used in |
|---|---|---|
| [`OPERATION_ESCALATION_STUDY.md`](OPERATION_ESCALATION_STUDY.md) | seven operations escalated; program text unsafe | §20.2 |
| [`SECOND_READING_STUDY.md`](SECOND_READING_STUDY.md) | the second reading that makes program text safe | §20.2 |
| [`QUERY_ESCALATION_STUDY.md`](QUERY_ESCALATION_STUDY.md) | escalation as a step of the query loop | §20.3 |
| [`REVIEW_SWEEP_STUDY.md`](REVIEW_SWEEP_STUDY.md) | stalled results ranked before the next re-reading | §20.3 |
| [`DEEP_HOLE_STUDY.md`](DEEP_HOLE_STUDY.md) | Niemeier deep holes classified from trajectories | §20.4 |
| [`DEEP_HOLE_ESCALATION_STUDY.md`](DEEP_HOLE_ESCALATION_STUDY.md) | the same question read one layer up | §20.4 |
| [`DEEP_HOLE_FAILURE_STUDY.md`](DEEP_HOLE_FAILURE_STUDY.md) | the four remaining failures, one mechanism | §20.4 |
| [`LEAN_ADDRESS_STUDY.md`](LEAN_ADDRESS_STUDY.md) | Leech addresses for the Lean declarations | §21 |
| [`ADDRESS_RETRIEVAL_STUDY.md`](ADDRESS_RETRIEVAL_STUDY.md) | retrieval by address, beaten by plain text | §21, §23 |
| [`ANONYMOUS_REGISTER_STUDY.md`](ANONYMOUS_REGISTER_STUDY.md) | take the names away and the structural address holds | §21 |
| [`STACK_RELAY_STUDY.md`](STACK_RELAY_STUDY.md) | the faculties as a stack with a stated gate | §21 |
| [`CORPUS_ADDRESS_STUDY.md`](CORPUS_ADDRESS_STUDY.md) | the repository's own documents, addressed | §21 |
| [`SEARCH_LOOP_STUDY.md`](SEARCH_LOOP_STUDY.md) | a procedure retrieved the way a number is | §21 |
| [`CONTROLLER_STUDY.md`](CONTROLLER_STUDY.md) | propose, check, refuse — six heuristics on 24 tasks | §21 |
| [`REVERSE_CALL_PLANNER_STUDY.md`](REVERSE_CALL_PLANNER_STUDY.md) | the supplied planner, sandboxed and not promoted | §23 |
| [`ITERATION_COST_STUDY.md`](ITERATION_COST_STUDY.md) | what a round costs, and the cache that stops it repeating work | §24 |
| [`GLM_ACADEMIC_PAPER.md`](GLM_ACADEMIC_PAPER.md) | this paper | — |

---

## Appendix B: The Lean Development by Theme

Every file of `RequestProject/GLM/`, grouped by what it is about. The
statements are in the files; §14.3 names the headline theorems.

| theme | files |
|---|---|
| foundations and the core's generations | `Foundations`, `Gen2`, `Gen3`, `Computable`, `Permutation`, `Reachable` |
| constants, calibration, physics | `Constants`, `Calibration`, `Lightspeed`, `AlignmentPoints`, `ReadQuantum`, `StepCost`, `Stability`, `TaxConservation`, `DimensionCarrier`, `MeasureView`, `Comparative`, `Denotation` |
| layers and escalation | `Layers`, `LayerChain`, `Cumulative`, `CumulativityRule`, `Tower`, `Stack`, `Escalation`, `EscalationLoop`, `Irrational`, `ConstructionLadder`, `ScaledLadder`, `NormFamily`, `HullExpansion`, `SecondReading` |
| the Golay code and its decoding | `GolayMOG`, `Golay/Code`, `Golay/Census`, `Golay/Cesaro`, `Golay/Dynamics`, `Golay/Sextet`, `Golay/CubeMirror`, `GolayBoundary`, `GolayWeightEnum`, `Steiner`, `LDP`, `Relaxation`, `Endianness`, `TieBreak`, `Combiner`, `Facets`, `ZeroStorage`, `ZeroStorageV5`, `LLVQTable` |
| the Leech lattice, higher lattices and the algebra above | `Shortcut/Substrate`, `Shortcut/Golay`, `Shortcut/GolayWeights`, `Shortcut/GrayCode`, `Shortcut/Leech`, `Shortcut/Decoder`, `Shortcut/FactorMap`, `Shortcut/Shortcut`, `GrayJump`, `HigherLattices`, `ShellSigma`, `Niemeier`, `DeepHoleClassifier`, `DeepHoleEscalation`, `DeepHoleFailure`, `Extraspecial`, `Sakuma`, `VOA`, `Heisenberg`, `Superposition`, `ModeAlgebra` |
| the MOG cube (geometric half) | `Cube/Surface`, `Cube/Tax`, `Cube/Stabiliser`, `Cube/Three`, `Cube/HexTiles` |
| values, streams and number theory | `DeltaSigma`, `Sturmian`, `Mantissa`, `Wobble`, `WobbleLandscape`, `Feedback`, `Cascade`, `NowReceipt`, `Transcendental`, `Reversible`, `LogBucket`, `Harmony`, `Totient`, `SpatialArithmetic`, `GridTension` |
| first principles and projection | `Distinction`, `Packing`, `FitCapacity`, `SeedLayers`, `SeedRoles`, `Triad`, `TriadCensus`, `TriadChance`, `Platonic`, `PCGS` |
| semantics and language | `Semantics/Grounding`, `Semantics/Meaning`, `Question`, `QuestionNested`, `Recipe`, `Admission`, `Completion`, `Conjugate`, `Vagueness`, `NameCoordinate`, `Corpus` |
| the loop, search and addressing | `ReasoningLoop`, `SearchLoop`, `Controller`, `ConditionalInduction`, `Address`, `Retrieval`, `Relay`, `Anonymous` |
| the answer surface and the conversation | `FieldSurface`, `ProbeOracle`, `CoordinateOrder`, `ColumnExtremum`, `ScaleConversion`, `Conversation`, `RoleBinding`, `PlanStore`, `SemanticPlan`, `EngineeringWheels` |

---

## Appendix C: The Supplied Material, and What Is Still Left in It

This appendix is the answer to *has anything useful been left behind?* For each
part of the supplied archive and each other supplied document it says where the
material went. "Retrieved" means its content is in the package or the Lean
development and is rebuilt and tested here; "audited" means its claims were
restated and given verdicts; "left" means it has not been brought in, with the
reason where one was recorded.

### C.1 The archive, `source_material/GLM-main.zip`

| part | what it is | status | where |
|---|---|---|---|
| `glm_lean/` | the first Lean-backed GLM (`GLM.lean`, `GLM2.lean`, `GLM3.lean`) | retrieved whole | `Foundations.lean`, `Gen2.lean`, `Gen3.lean` |
| `GLM.py`, `README.md` (archive root) | the archive's entry point and overview | superseded by `overlay/GLM.py` and the repository's own documents | [`README.md`](../README.md) |
| `glm_machine/`, `glm_3.1/`, `glm_universal/` | the earlier machine scripts (`glm_machine` is GLM v37) and the earlier package | folded into the package in the early phases — `glm_machine` into the runtime layer — with the frame bridge and state migration in `overlay/glm_universal/migration/` | [`archive/PACKAGE_README_ARCHIVE.md`](../archive/PACKAGE_README_ARCHIVE.md), [`archive/MASTER_PLAN_ARCHIVE.md`](../archive/MASTER_PLAN_ARCHIVE.md) |
| `light/aristotle_01/` | EM scale calibration, the lightspeed chain, the observer-Y study, the shortcut | retrieved: `Lightspeed.lean`, the `Shortcut/` files, `ReadQuantum.lean`, and the constants and mass-scale bounds of `SubstrateConstants.lean` in `AlignmentPoints.lean` and `FitCapacity.lean`; **left in part**: `ObserverY.lean` — its tax, NRCI and regime results are rebuilt under other names in `Constants.lean` and `ReadQuantum.lean`, but its minimal-vector tax classes (classes A and B coherent, class C transitional), its loop-closure and history-additivity lemmas and its calibrated regime separation are not | §9–§10, §13.4, [`SOURCE_SALVAGE_AUDIT.md`](SOURCE_SALVAGE_AUDIT.md) |
| `light/reports/`, `light/scripts/`, `light/source_documents/`, `light/worklogs/` | the twenty-phase floating-point audit of the lightspeed claims, its synthesis and PDF report, and the working notes behind it | summarised: its structural closures are §10.5, its calibrated core §10.3 and §25.2, its open problems §25.5 items 1–3; the scripts are floating-point and are not re-run, and the source documents are working notes rather than claims | §10, §25 |
| `light/EM_calibration_1/` | the speed-of-light calibration, eleven versions | audited; its surviving arithmetic is in `Calibration.lean` | §10, [`SOURCE_SALVAGE_AUDIT.md`](SOURCE_SALVAGE_AUDIT.md) |
| `leech_lattice/` | the Leech lattice shortcut | retrieved whole | `Shortcut/`, `GrayJump.lean`, §13 |
| `data_object/encoding_definition_attempt_03-08.26/` | spatial arithmetic experiments | summarised (§11) from the archive's own reports; its one Lean file retrieved whole in Phase 61 as `GolayMOG.lean` — lossless Gray identity addresses, the MOG and Leech address tables, and five negative results | §11.7 |
| `data_object/encoding_definition_attempt_04.08.26/` | the 24-bit Golay/Leech chemistry encoding and MOG spatial arithmetic | summarised in §11 from the archive's own reports; its correlations are the archive's figures and are not re-run here | §11 |
| `data_object/FirstPrinciples/` | the first-principles sub-study | retrieved: `Packing.lean` (with `Distance.lean`), `FitCapacity.lean`, `Triad.lean`, and in Phase 61 `Distinction.lean` (as `Distinction.lean`) and `Seeds.lean` (into `SeedRoles.lean`, with the irrationality of e proved rather than assumed); not taken: `Findings.lean`, an index whose two bridge lemmas restate results already rebuilt | §2.1, §15 |
| `data_object/Projection/` | the projection sub-study | retrieved: `StepCost.lean` (cost), `SeedLayers.lean` (layers and most of the one-parameter file), the surprisal ledger in `FitCapacity.lean`; and in Phase 61 `Fibre.lean`, `Cheapest.lean`, `Independence.lean` and the rest of `OneParameter.lean` (the SL(2,ℝ) trichotomy, the period and flow fibres) into `SeedRoles.lean` | §16 |
| `data_object/` (top level) | the encoding specification, the element and molecule notes, the test ledger and calibration log of the training iterations, the training benchmarks, a MOG experiment note, a 256-dimensional Barnes–Wall note, and the scripts and JSON results behind them | summarised: the benchmarks' negative figures are recorded in §11.7; the specification and ledgers are the provenance of §11; **not taken**: the Barnes–Wall note, whose central claim — that a SHA-256 fingerprint is a physical coordinate — is the reading of a hash as meaning that directive D3 forbids | §11 |
| `data_object/mog_cube_1/` | the MOG cube: encoding and a verified micro-language, 43 Lean files | retrieved: the geometric half (`Cube/*`, `Golay/CubeMirror.lean`, `GolayWeightEnum.lean`, `Steiner.lean`); **left**: the language half — the integer cube and measured words, sentences, paragraphs, discourse and dialogue, cube thought, relative clauses and quantifiers, causation, continuous quantities, learning, scaling, Zipf and the capstone — about thirty files, the largest body of verified material not rebuilt here | §12, §25.5 item 15 |
| `GMHGL/` | `ubp_unified_v5.py`, `spatial_arithmetic.py`, `geometry.py`, `ldp_complete_mapping.md`, `ldp_nrci.py`, `refined_nrci.py`, `spatial_totient_kinetics.py`, the `tgic_*` scripts, the EM analog engine, the EML ALU, the genesis boot, `value_geometry.py` | retrieved where a claim survives separation from its script: `LDP.lean`, `Totient.lean`, `SpatialArithmetic.lean`, `Triad.lean`, `Shortcut/Substrate.lean`; the simulation harnesses and tabulations deliberately not, with the reasons recorded | [`RETRIEVED_LEAN_STUDY.md`](RETRIEVED_LEAN_STUDY.md) §4 |
| `arc_agi_15/` (and 16, 17) | the ARC-era loop and grid heuristics | the architectural claim retrieved as `ReasoningLoop.lean`, the grid metrics as `GridTension.lean`, the conditional lobe as `ConditionalInduction.lean`; the ARC-specific heuristics deliberately not | [`SEARCH_LOOP_STUDY.md`](SEARCH_LOOP_STUDY.md), [`RETRIEVED_LEAN_STUDY.md`](RETRIEVED_LEAN_STUDY.md) §4 |
| `long_term_memory/` | a knowledge note, training data and two large knowledge bases in JSON | **left**: no study reads it; as unverified text it could at most seed a register through the admission door of §18.2, never be quoted as fact | — |

### C.2 The other supplied documents, `source_material/`

| document | status | where |
|---|---|---|
| `glm_unification_blueprint.md` | audited sentence by sentence | [`GLM_UNIFICATION_BLUEPRINT_AUDIT.md`](GLM_UNIFICATION_BLUEPRINT_AUDIT.md) |
| `glm_study_findings_catalog.md` | audited as a live claim ledger | [`GLM_STUDY_CATALOG_AUDIT.md`](GLM_STUDY_CATALOG_AUDIT.md) |
| `cardinal_geometry_synthesis.md`, `DYNAMIC_CARRIER_STUDY.md`, `geometric_substrate_study.py` | built into the value layer and the dynamic carriers | §4–§5, [`INFINITE_VALUES_STUDY.md`](INFINITE_VALUES_STUDY.md) |
| `GLM_Iteration_Study (1).pdf`, `GLM_Generators_Containers (2).pdf` | the two companion preprints — the float-drift demonstration and the code-to-lattice survey; the three containers of a constant — audited claim by claim | §2.2, §3.3, §5.4, [`GLM_COMPANION_STUDIES_AUDIT.md`](GLM_COMPANION_STUDIES_AUDIT.md) |
| `Golay codes and Hadamard matrices.txt` | the constructions the ladder is generated from | [`CONSTRUCTION_LADDER_STUDY.md`](CONSTRUCTION_LADDER_STUDY.md) |
| `glm_zero_storage_substrate_v3.txt` | generated rather than stored tables | [`ZERO_STORAGE_STUDY.md`](ZERO_STORAGE_STUDY.md), [`ZERO_STORAGE_V5_STUDY.md`](ZERO_STORAGE_V5_STUDY.md) |
| `pcgs_glm_integration.py`, `pcgs_wider_landscape.py`, `pcgs_wider_landscape_v4.txt` | six systems admitted | [`PCGS_STUDY.md`](PCGS_STUDY.md) |
| `glm_vision_experiments_v14.py` | the consolidated "self-inspecting agent" of fourteen vision experiments (filter, understand, cross-domain) | **left**: filed in Phase 43 and not yet run against the package or given a study | — |
| `glm_reverse_call_planner_v2.py`, `REVERSE_CALL_PLANNER_README.md` | sandboxed, measured, not promoted | [`REVERSE_CALL_PLANNER_STUDY.md`](REVERSE_CALL_PLANNER_STUDY.md) |
| `HISTORY_RECORDED_NOW_*.md`, `history_recorded_now.py` | the claim decided: the identity holds, the reading does not | [`NOW_RECEIPT_STUDY.md`](NOW_RECEIPT_STUDY.md) |
| `conversation_experiment/` | eight scripts run unmodified; two claims refuted; four pieces taken | [`CONVERSATION_STUDY.md`](CONVERSATION_STUDY.md), [`SUPPLIED_PORTS_STUDY.md`](SUPPLIED_PORTS_STUDY.md) |
| `GLM_IMPROVEMENT_ROADMAP.md` | P1 and P2 taken (typed plans, held-out evaluation); P3–P7 stand as candidates | [`SEMANTIC_PLAN_STUDY.md`](SEMANTIC_PLAN_STUDY.md), §25.5 |
| `formula_wheel/` | the engineering-language session record | [`ENGINEERING_LANGUAGE_STUDY.md`](ENGINEERING_LANGUAGE_STUDY.md) |
| `ToDo_01.txt` | the owner's working list; its items are carried in the phase record | [`MASTER_PLAN.md`](../MASTER_PLAN.md) |

### C.3 What is still worth bringing in

Phase 61 retrieved the small bodies of verified material the Phase 60 ledger
named: the first-principles and projection files and the archive's
`GolayMOG.lean` are now under this repository's build (§14.1). Read against
the whole of C.1 and C.2, what remains that would add to the system rather
than duplicate it is:

1. **The MOG cube's language half** — about thirty files, a verified
   micro-language whose dialogue never contradicts itself and whose law table
   is *learned* rather than written. It is the nearest thing in the archive to
   the typed discourse state that §25.5 item 14 asks for, and it is already
   proved; it is the one large body of archive Lean still outside this build.
2. **The rest of `ObserverY.lean`** — the tax classes of the Leech minimal
   vectors and the calibrated regime separation. Small, and it would complete
   §13.4.
3. **The vision experiments' self-inspection loop** — not yet run against the
   package; small enough for one round, and it would say whether the loop's
   filter–understand–check trinity adds anything the controller of §21 does not
   already do.
4. **The improvement roadmap's P3–P7** — typed compositional derivation,
   typed multi-turn state, external-truth validation, a program-text register,
   and provenance-first sparse chemistry — which line up with §25.5 items 9–14.

Everything else in the archive is either retrieved, summarised with its
figures attributed, or deliberately not taken with the reason in the row that
names it.

---

## Appendix D: Key Constants

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

The package carries Y as an exact 15-digit rational, never a float; the
decimals above are renderings of it.

---

## Appendix E: Glossary

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
- **Register:** A declared table of carriers of one kind (physics, chemistry, molecules, mathematics, lexicon, spatial, harmonics, economics)
- **Query kind:** One of the declared shapes a question can take; `report` dispatches the report subjects
- **Licensing:** Admitting a candidate reading only when the query it produces solves; used by the conversation layer and the planner
- **Named refusal:** A refusal that states which of a declared set of reasons applies
- **Faculty:** One of derivation, addressing and refusal — the three things a round can move
- **Tier 0:** The question, verdict and deciding figure every current-state document opens with; checked against the document's own body
- **Inline figure:** A number written between figure markers, emitted by the code that measures it
- **Sign-off ledger:** The record of which tests and instruments are signed against a digest of everything they depend on
- **Sandbox:** Where a component not yet relied on lives, with a computed promotion checklist
