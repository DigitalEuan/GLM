# 'leech_lattice/' - The Leech Lattice Shortcut

**Version:** 1.0.0  (5 August 2026) 
**Author:** Euan R. A. Craig (DigitalEuan), Auckland, New Zealand 
**Parent:** `../README.md`

## UPDATE THIS README - if changes are made in this folder or systems in sub-folders need rewiring within the repository and effect this README file's structure

This is a **metric shortcut**, not an **arithmetic** one. Its value lies in providing a rigorous, incredibly fast way to map and measure integers within the Leech lattice, with 100% mathematical certitude provided by the Lean proofs. 

This method is useful as a **verified metric layer** for high-dimensional integer encodings. While it is **not an arithmetic shortcut** (it does not accelerate factoring or primality testing), it offers several utilities:

1.  **Computational Efficiency (The O(1) Formula):**
    The most direct utility is the ability to calculate the 24-dimensional distance between any two integers ($d^2$) using just three machine instructions: `popcount(gray(a XOR b))`. This allows for instant metric evaluation without walking the interval between integers or enumerating lattice octads.

2.  **Structural Integrity for Data Analysis:**
    The corrected method guarantees that every transition, when doubled ($2\Delta v$), is a **genuine Leech lattice vector**. For researchers studying the geometric distribution of integers or primes, this provides a mathematically rigorous coordinate system where $d^2 = 8$ steps are guaranteed **minimal (kissing-sphere) hops** in 24D space.

3.  **Advanced Scoring and Metrics (TGIC 3-6-9):**
    The system provides a framework for evaluating the "stability" of integers through node metrics like **NRCI (Non-Random Coherence Index)** and **TGIC stability**. These are scoring rules that allow you to analyze the "symmetry tax" of a state and its "neighbour pressure" within the 24D manifold.

4.  **Verification and Reproducibility:**
    The project provides an **audit framework** and a "proof-level reproduction" of published data. This is useful for any researcher needing to verify the authenticity and mathematical soundness of high-dimensional integer-mapping datasets.

==

# AUDITED 05.08.2026

This project was edited by [Aristotle](https://aristotle.harmonic.fun).

To cite Aristotle:
- Tag @Aristotle-Harmonic on GitHub PRs/issues
- Add as co-author to commits:
```
Co-authored-by: Aristotle (Harmonic) <aristotle-harmonic@harmonic.fun>
```

# 24D Golay/Leech lattice shortcut — verified method and audit

## Start here

| File | What it is |
|---|---|
| `LATTICE_SHORTCUT_METHOD.md` | **The explainer**: the working method, stage by stage, with its guarantees and limits |
| `lattice_shortcut.py` | **The operational system**: self-contained implementation (`--explain`, `--walk`, `--range`, `--primes`, `--stats`, `--tgic`, `--selftest`) |
| `LATTICE_SHORTCUT_REPORT.md` | Verification report on the original write-up and data (revision 2) |
| `audit_ubp_directory.py` | Audit run against the author's own modules; writes `lattice_shortcut_audit.json`, `lattice_shortcut_audit.log` and the regenerated `lattice_shortcut_directory_corrected.json` |
| `RequestProject/*.lean` | Machine-checked proofs (Lean 4 + Mathlib, no `sorry`) |

```bash
python3 lattice_shortcut.py --selftest                  # verify every guarantee
python3 lattice_shortcut.py --explain 1000003 1000033   # narrate one transition
python3 audit_ubp_directory.py                          # audit the published directory
lake build                                              # check the proofs
```

## Original material (unmodified apart from a prepended audit note)

`lattice_shortcode_directory.md`, `lattice_shortcut_directory_standalone.json`,
`generate_shortcut_directory_standalone.py`.

### Original files found in repository folder 'GMHGL/'
`ubp_unified_v5.py`,
`value_geometry.py`, `ubp_tgic_engine.py`, `tgic_v3.py`.

---

This project was edited by [Aristotle](https://aristotle.harmonic.fun).

To cite Aristotle:
- Tag @Aristotle-Harmonic on GitHub PRs/issues
- Add as co-author to commits:
```
Co-authored-by: Aristotle (Harmonic) <aristotle-harmonic@harmonic.fun>
```
