This project was edited by [Aristotle](https://aristotle.harmonic.fun).

To cite Aristotle:
- Tag @Aristotle-Harmonic on GitHub PRs/issues
- Add as co-author to commits:
```
Co-authored-by: Aristotle (Harmonic) <aristotle-harmonic@harmonic.fun>
```

# Designed Dimensions × GLM: is the Golay–Leech substrate optimal, and can a better one be designed?

A study of the substrate used by the Geometric Language Machine
([DigitalEuan/GLM](https://github.com/DigitalEuan/GLM)): the extended binary Golay code
\(G_{24}\) with its Leech-lattice and "negative space" (sextet mirror) layers. The study asks
whether that substrate is optimal, whether a better one can be designed, and where the
boundaries are.

## Start here

**`glm_package/README.md` is the consolidated record of the study, ready to take into the GLM.**
It covers the findings, the boundaries, the recommended protocol and the open problems.
`glm_package/THEOREMS.md` indexes every machine-checked result. `glm_package/glm_substrate.py` is a
reference implementation of the recommended protocol, with a self-test.

The phase reports below are the detailed history. Where they differ from the package, the
package is current.

| Read | For |
|---|---|
| `glm_package/` | **The integration package** (record, theorem index, reference implementation) |
| `reports/05-hpskl-free-space-and-open-items.md` | **Phase 5:** the HPSKL concept tested exactly (what is scientific, what is falsified, what the GLM can use); free resolution of the ambiguous space with proved gates; the open mirror items (Golay-extension family closed; why the general cases resist) |
| `reports/04-triggered-mirror-and-open-items.md` | **Phase 4:** the triggered (on-demand) mirror and how to use the ambiguous space; open items revisited (sender tags need 8 labels for any design, now proved) |
| `reports/03-cheaper-mirror-study.md` | **Phase 3:** a mirror with fewer than six labels. A certified five-label substrate, what it costs, partial mirrors on Golay |
| `reports/DesignSpec_v1-section4-corrected.md` | Corrected text for §4 of `DesignSpec_v1.pdf` (order of \(M_{24}\)) |
| `reports/02-designed-substrate-study.md` | **Phase 2:** trying to design a better substrate. Experiments, new theorems, limits, recommendations |
| `reports/01-golay-optimality-report.md` | Phase 1: Golay optimality theorem, negative-space floor, mirror cost |
| `reports/SOURCE-MATERIAL-AUDIT.md` | What the uploaded material contains, what reproduces, what was missing (with phase-2 addendum) |
| `reports/REORGANISATION-LOG.md` | Every file move and edit made while organising the repository |
| `experiments/README.md` | Index of exploratory computations and their logs |

## Layout

```
glm_package/             consolidated record + reference implementation (start here)
RequestProject/GLM/      Lean 4 / Mathlib proofs (no sorry)
  Bounds.lean            universal limits for any code and decoder (BSC bound, volume bounds)
  Golay.lean             the Golay code G24, syndrome decoder, finite facts
  GolayOptimal.lean      Golay is optimal; negative-space floor; one-sixth ceiling
  Mirror.lean            sextets, mirror (clarification) cost 6 vs universal floor 4, trade-off
  Tag.lean               sender-side tags: Golay needs >= 86 labels, 7 bits suffice; on-demand protocol
  Steiner.lean           octads form S(5,8,24); punctured code G23 is perfect
  Leech.lean             Leech lattice on the Golay carrier, minimal norm, subgroup
  LeechKissing.lean      exact classification of minimal vectors; kissing number 196,560
  CheapMirror.lean       any mirror with <= 5 labels forces ambiguity below 4 bit flips
  Mirror5.lean           an explicit substrate whose mirror needs exactly 5 labels
  MirrorConsult.lean     exact (rational) probability of consulting the mirror; Golay vs five-label code
  GolayPartialMirror.lean  K labels on Golay resolve exactly K/6 of the 4-bit corruptions
  GolaySymmetry.lean     the cyclic shift of DesignSpec section 4 maps G24 onto itself
  TriggeredMirror.lean   trigger for the mirror; on-demand K-label lists of size ceil(6/K); batching; reliabilities
  Delsarte.lean          Delsarte LP bound, certified: A(24,9) <= 551, any sender tag needs >= 8 labels
  HPSKLLeech.lean        HPSKL codebook: Leech overlaps {0,1/4,1/2}; GLM phase states; complement blind spot
  QuantumDiscrimination.lean  any-POVM discrimination bound, depolarizing noise, tight frames, contact-graph invariance
  HPSKLVerdict.lean      five-qubit verdicts: a GLM symbol in one 5-qubit state is read with prob <= 1/128
  SoftResolve.lean       free use of the ambiguous space: soft certificate (radius 8, sharp), posterior gate
  GolayExtWitness.lean, GolayExtMirror.lean  all 4096 one-bit extensions of the [23,12,7] code need 6 mirror labels
reports/                 study reports
experiments/             exploratory scripts and logs (not formally verified)
source_material/         the Designed-Dimensions material (design track, paper, archive, HPSKL.txt)
```

## Building

```
lake build
```

builds every Lean file (the `native_decide` checks over the 4096 codewords take a few
minutes). The reference implementation is tested with
`cd glm_package && python3 test_glm_substrate.py` (standard library only). Axioms used: `propext`, `Classical.choice`, `Quot.sound`, plus
`Lean.ofReduceBool` / `Lean.trustCompiler` from `native_decide`.

---

This project was edited by [Aristotle](https://aristotle.harmonic.fun).

To cite Aristotle:
- Tag @Aristotle-Harmonic on GitHub PRs/issues
- Add as co-author to commits:
```
Co-authored-by: Aristotle (Harmonic) <aristotle-harmonic@harmonic.fun>
```
