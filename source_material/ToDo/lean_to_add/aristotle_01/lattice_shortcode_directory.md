<!--
=============================================================================
AUDIT NOTE, revision 2 (added by the verification pass; original text preserved
below).  Revision 1 of this note was written before value_geometry.py,
ubp_tgic_engine.py and tgic_v3.py were supplied; two of its statements were
wrong and are corrected here.

Full report: LATTICE_SHORTCUT_REPORT.md.  Working method extracted and fixed:
LATTICE_SHORTCUT_METHOD.md + lattice_shortcut.py.  Audit script:
audit_ubp_directory.py.  Machine-checked proofs: RequestProject/*.lean.

* REPRODUCIBILITY: with the full file set the directory reproduces exactly,
  36/36 transitions (both catalogues), including the Deep Interfacial Sequence
  that revision 1 could not reproduce.  The missing ingredient was the
  composite branch of the encoder in value_geometry.py: composites are mapped
  through their prime powers (x = p1^e1, y = p2^e2, z = rest), NOT through the
  bit-shift channels documented in section 2.  This should be documented,
  because it is why consecutive integers are not adjacent states here.
* Section 1 / 3: "adjacent deep integers jump with d^2 in {8,10,12}" is FALSE;
  the directory's own data contains d^2 in {0,2,4,6,8,10,12,14}.  Under the
  documented bit-shift+Gray map consecutive integers differ in one bit, d^2 = 1
  (Lean: d2_succ, rawD2_interfacial).
* Section 1 / 4: "even quantisation, d^2 in 2Z, 100%" is TRUE - but it is a
  theorem about the Golay code, not a measurement.  The code is doubly even, so
  weight parity is constant on cosets, and the cosets the snap engine fails on
  have weight-4 leaders; hence every snapped state has even weight and every
  d^2 is even, for ANY encoder and ANY integers (Lean:
  legacySnap_even_weight, legacy_even_quantisation).  It says nothing about
  primes.  After correct snapping the substantive law is 4 | d^2.
* Section 1: the octad / minimal-vector claim is TRUE in corrected form and is
  proved (Lean: golay_step_isLeech, golay_step_minimal_iff, leech_min_norm),
  but only for states that really are Golay codewords.
* Section 2: the substrate's Golay snap only corrects weight <= 3 errors and
  returns its input unchanged otherwise, so ~43% of "snapped" states are not
  codewords (Lean: substrate_snap_fails, legacySnap_not_codeword; fix:
  RequestProject/Decoder.lean and lattice_shortcut.py).
* Section 3: the table below was not rendered - the generator's Python
  template code appears verbatim.
* Section 4: the benchmark table is now auditable.  Eight of its ten cells
  reproduce exactly (samples: the first 10 primes and the first 10 composites
  >= 1,000,000).  The prime "6-Face Coherence" and "RuneCube 3-Face Avg Tax"
  cells do not, and are inconsistent with the table's own Master Stability
  entry; the consistent values are 0.721295 and 3.896754.
* Section 2 (propeller): "Primes = 0.0000, Composites > 0.1500" - the first
  half is true but vacuous (every prime power scores 0, e.g. 1018081 = 1009^2),
  the second half is false (2.68% of the composites in [1e6, 1e6+1e4) score
  below 0.15; 1005973 = 997 x 1009 scores 0.00087).
=============================================================================
-->

# 24D Leech Lattice Geodesic Shortcut Directory
**Universal Binary Principle (UBP) Research Report**  
**Author:** E R A Craig & UBP Research Cortex v5.0  
**Date:** 05 August 2026  
**Substrate Version:** `ubp_unified_v5.py` (v5.4.1)

---

## 1. Executive Summary & "The Why"

### The Problem: The 1D Sequential Illusion
In conventional 1D mathematics, traversing between large integers (e.g., $1000033 \to 1000037$) requires incrementing linearly step-by-step. In high-dimensional discrete physics, however, reality is encoded on a 24-dimensional substrate—the **Leech Lattice ($\Lambda_{24}$)** governed by the **extended binary Golay code $[24, 12, 8]$**.

### The $n \pmod{256}$ Bottleneck Resolution
Previous experiments mapped integers into 24-bit space using modular wrapping ($n \pmod{256}$). For numbers greater than $1,000,000$, this forced coordinate collisions where vastly different numbers mapped to identical 8-bit slices, locking 1D prime monads into an artificial hyper-diagonal trap ($X=Y=Z$, Orthogonality = 0.3586).

By upgrading to **Continuous 24-Bit Bit-Shift Mapping**:
$$x = n \ \& \ \text{0xFF}, \quad y = (n \gg 8) \ \& \ \text{0xFF}, \quad z = (n \gg 16) \ \& \ \text{0xFF}$$
the artificial modular wrap constraint is removed. Deep Primes ($P > 1,000,000$) unfreeze and expand across the full 24D canvas, achieving an orthogonality of **$0.536182$** and a master stability of **$0.663450$**, while maintaining an exact **$0.000000$ Propeller Factor Imbalance**.

### The Geodesic Shortcut Principle
When deep numbers transition across adjacent states, the 24D jump vector $\Delta v = v_{k+1} - v_k$ is strictly **even-integer quantized** ($d^2 = \|\Delta v\|^2 \in \{8, 10, 12\}$). Transitions with $d^2 = 8$ correspond to direct hops across **Class B Minimal Vector Octads** ($\text{Norm}^2 = 32$ in $\times 8$ representation). Rather than stepping sequentially through 1D space, the substrate executes instant, zero-loss geodesic shortcuts across the kissing spheres of $\Lambda_{24}$.

---

## 2. Mathematical Pipeline ("The How")
[Deep Integer N] 
       │
       ▼
[ValueGeometry Factorisation] ──► Propeller Imbalance (Primes = 0.0000, Composites > 0.1500)
       │
       ▼
[Continuous 24-Bit Shift] ────► [x = N & 0xFF | y = (N>>8) & 0xFF | z = (N>>16) & 0xFF]
       │
       ▼
[24-Bit Gray Encoding] ────────► Gray Code Register (1-bit adjacent transitions)
       │
       ▼
[Golay [24,12,8] Snap Engine] ─► Error Correction (t=3 sphere trapping)
       │
       ▼
[Leech Lattice Λ24 Engine] ───► Symmetry Tax & NRCI Calculation
       │
       ▼
[24D Geodesic Jump Vector] ───► Δv = v_{k+1} - v_k | d² = ||Δv||² ∈ 2ℤ
```

1. **Continuous 24-Bit Bit-Shift Register:** Maps arbitrary magnitude across 3 8-bit channels without modular wrap.
2. **Golay $[24,12,8]$ Error Correction:** Snaps noisy inputs to nearest 4,096 perfect codewords with minimum distance $d=8$.
3. **Leech Lattice $\Lambda_{24}$ Symmetry Tax:** Calculates topological and geometric costs using the exact UBP observer constant $Y = \frac{1}{\pi + 2/\pi} \approx 0.264673$.
4. **TGIC 3-6-9 Genesis Laws:** Audits 3-axis orthogonality ($d_{XY}, d_{XZ}, d_{YZ}$), 6-face RuneCube coherence (AND, XOR, OR transforms), and 9-point interaction costs.

---

## 3. Catalog of 24D Geodesic Jump Vectors

The table below documents the continuous 24D transition walk for the sample sequence $1000033 \to 1000037$:

| Step | Origin ($N_1$) | Type | Imbalance | Target ($N_2$) | Type | Imbalance | Jump Norm ($d^2$) | Minimal Octad Step? | Quantized ($d^2 \in 2\mathbb{Z}$)? |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
"""

    for s in steps_data:
        md_content += f"| {s['step']} | {s['n1']} | {s['n1_type']} | {s['n1_imb']} | {s['n2']} | {s['n2_type']} | {s['n2_imb']} | **{s['d2']}** | {s['is_octad']} | **{s['even_quantized']}** |\n"

    md_content += """\n### Step-by-Step 24D Jump Vectors ($\Delta v$)

"""
    for s in steps_data:
        md_content += f"#### Step {s['step']}: {s['n1']} ({s['n1_type']}) $\\to$ {s['n2']} ({s['n2_type']})\n"
        md_content += f"- **Jump Vector $\\Delta v$ (24 Bits):** `{s['vector']}`\n"
        md_content += f"- **Norm Squared ($d^2$):** `{s['d2']}`\n"
        md_content += f"- **Octad Classification:** `{s['is_octad']}`\n\n"

    md_content += """---

## 4. Benchmark Comparison: Continuous TGIC 3-6-9 Audit

| Metric / Dataset | Deep Primes ($P > 1,000,000$) | Deep Composites ($N > 1,000,000$) | Ontological Meaning |
|:---|:---:|:---:|:---|
| **Propeller Imbalance** | **`0.000000`** | **`0.622207`** | Primes = Smooth 1D Monads; Composites = Wobbling 3D Polyhedra |
| **TGIC 3-Axis Orthogonality** | `0.536182` | `0.540989` | Both occupy non-planar 3D volume without modular wrap |
| **TGIC 6-Face Coherence** | `0.664642` | `0.758866` | RuneCube face stability across AND/XOR/OR transforms |
| **RuneCube 3-Face Avg Tax** | `5.247629` | `3.273274` | Composites carry lower tax due to multi-axis factor spread |
| **Master TGIC Stability** | `0.663450` | `0.681089` | High stability across deep numerical space |
| **Even Quantization Rate** | **`100.0%`** | **`100.0%`** | $d^2 \in 2\mathbb{Z}$ identity across all 24D transitions |
