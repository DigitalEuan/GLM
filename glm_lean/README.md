https://aristotle.harmonic.fun/dashboard/requests/705777e9-a185-4ffc-878a-16582e92092f

This project was edited by [Aristotle](https://aristotle.harmonic.fun).

To cite Aristotle:
- Tag @Aristotle-Harmonic on GitHub PRs/issues
- Add as co-author to commits:
```
Co-authored-by: Aristotle (Harmonic) <aristotle-harmonic@harmonic.fun>
```

# The Geometric Language Machine

Three generations of the same idea — exact, composable meaning on a lattice
carrier — each an academic-paper-style script that verifies its own claims,
each with a companion implementation that shows the method at work.

All three share one architectural rule: **the meaning is the state and the
carrier is a derived view of it**. A concept is its exact integer (GLM-1) or
rational (GLM-2, GLM-3) exponent vector; the bit pattern or lattice point is
`encode(meaning)`, computed on demand, cached, never settable and never an
input. Nothing in any of the three systems reduces an exponent modulo 2 to
reach a verdict — the mod-2 ceiling is measured in a clearly marked appendix, as
the negative result that justifies the architecture.

| | what it is | run it |
|---|---|---|
| [`glm/`](glm) | **GLM-1**: the consolidated first-generation paper and companion reasoner (seven integer dimension exponents; a derived Golay/MOG carrier; 43 verified claims). | `cd glm && python3 glm_paper.py` |
| [`glm2/`](glm2) | **GLM-2**: the second generation, pushed much further — ten *rational* exponents plus scale, tensor rank and three parities; a Leech-lattice carrier with nearest-point repair; `Co₀` constructed rather than quoted; an operator algebra (`grad`, `div`, `curl`, `d/dt`, integrals) and a verified commutative non-associative axial-algebra layer; 58 verified claims. | `cd glm2 && python3 glm2_paper.py` |
| [`glm3/`](glm3) | **GLM-3**: the third generation, which actually *uses* the Monster. Λ/2Λ built as an F₂ quadratic space of plus type; the extraspecial group `2^(1+24)` constructed from that form with an explicit cocycle and its 4096-dimensional representation; the **whole Griess algebra**, 98,580 + 98,304 = 196,884-dimensional and exact, with the structure constants of both halves derived rather than quoted and the classical 2A eigenvalue ledger 1 / 96,256 / 4,371 / 96,256 computed; a canonical coherent axis-sign convention; the **multi-MOG-cube** as a faithful stack of Monster addresses per concept, at a depth derived from the data; an honest **metric** on meanings with nearest neighbours and clustering; relation words, Norton–Sakuma triangles and facet-level equation checking over the 660-concept register; and a four-part **benchmark** (217,470 pairs, 64 physical laws, 224 corrupted mutants, 40 dimensionless groups). 64 verified claims. | `cd glm3 && python3 glm3_paper.py` |
| [`RequestProject/`](RequestProject) | The Lean 4 + Mathlib companions: `GLM.lean`, `GLM2.lean` and `GLM3.lean`, one per generation. All `sorry`-free. | `lake build` |

Everything is standard library only on the Python side, and every script must
be run from inside its own directory.

Each generation also ships its companion implementation and test suite:

```bash
cd glm  && python3 glm_reasoner.py  && python3 test_glm.py
cd glm2 && python3 glm2_reasoner.py && python3 test_glm2.py
cd glm3 && python3 glm3_reasoner.py && python3 test_glm3.py && python3 glm3_bench.py
```

---

This project was edited by [Aristotle](https://aristotle.harmonic.fun).

To cite Aristotle:
- Tag @Aristotle-Harmonic on GitHub PRs/issues
- Add as co-author to commits:
```
Co-authored-by: Aristotle (Harmonic) <aristotle-harmonic@harmonic.fun>
```
