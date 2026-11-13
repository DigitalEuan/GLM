# 'data_object/mog_cube_1' - MOG Cube — Encoding System

**Version:** 1.0.0  (13 August 2026)
**Author:** Euan R. A. Craig (DigitalEuan), Auckland, New Zealand   
**Parent:** `data_object/README.md`

## UPDATE THIS README - if changes are made in this folder or systems in sub-folders need rewiring within the repository and effect this README file's structure

- How to encode any subject (element, molecule, word, number, shape) as a 24-bit Data Object in the Leech lattice.  

---

This project was edited by [Aristotle](https://aristotle.harmonic.fun).

To cite Aristotle:
- Tag @Aristotle-Harmonic on GitHub PRs/issues
- Add as co-author to commits:
```
Co-authored-by: Aristotle (Harmonic) <aristotle-harmonic@harmonic.fun>
```

# GLM semantics on the MOG cube — machine-checked package

A Lean 4 / Mathlib development that puts measurable meaning on the 24-cell
MOG/Golay data object and builds a small language on top of it: words with
physical dimension, sentences that are true, connectives (`and`, `but`, `so`)
with measured meanings, a conversation that remembers, and plans that say what
to do. Everything claimed is a theorem: the build has **no `sorry` and no added
axioms**.

**Start here: [`FINAL_REPORT.md`](FINAL_REPORT.md)** — the results, the
failures, and what is not machine-checked + 'STAGE5_REPORT.md'.

## Documents

| file | what it is |
|---|---|
| `FINAL_REPORT.md` | the summary of stages 1–4: headline results, honest limits, next steps |
| `STAGE5_REPORT.md` | stage 5 — learning, relative clauses, scaling, continuous quantities, the Golay weight enumerator, and the capstone |
| `CUBE_MOG_REPORT.md` | stage 1 working notes — the cube surface as the MOG, the price list, the 20% precision wall |
| `CUBE_MOG_REPORT_2.md` | stage 2 — the integer cube, precision 1.00, the micro-world and its question answerer |
| `CUBE_MOG_REPORT_3.md` | stage 3 — connectives, dialogue, Zipf's law, planning and narration |
| `THEOREM_INDEX.md` | every top-level declaration, with a one-line summary (generated) |
| `ARISTOTLE_SUMMARY.md` | the session-by-session log of what was added when |
| `MOG_semantics_1.txt` | the original brief |
| `glm_clean/` | the exploratory Python that guided the work, including `exp7_cube_surface.py` |

## The Lean development (`RequestProject/`)

43 files, 1310 top-level declarations (574 definitions, 736 theorems), no `sorry`.

*Substrate — the code and the cube*

| file | contents |
|---|---|
| `GolaySemantics.lean` | the `[24,12,8]` Golay code as the GLM's substrate: `d = 8`, syndromes, unique repair below the boundary |
| `GolayHexTiles.lean` | GF(4), the `[6,3,4]` hexacode, and its decoding |
| `CubeSurfaceMOG.lean` | cube surface = MOG grid; the `2^24 → 2^18 → 2^12` factorisation; face erasure |
| `CubeStabiliser.lean` | which of the 48 cube symmetries the code gives away free |
| `CubeTax.lean` | syndrome, coset leaders, covering radius, the sharp `4·Q` repair price |
| `ThreeCube.lean` | the three-cube (Turyn) construction of the same code |

*Symmetry — what no placement can achieve*

| file | contents |
|---|---|
| `GolayCode.lean` | Golay codes abstractly: self-duality, and exactly `2^(12-k)` codewords on any prescribed pattern of `k ≤ 7` cells |
| `GolaySteiner.lean` | the octads form a Steiner system `S(5,8,24)`, by moment counting |
| `GolayInvolution.lean` | a diagonal mirror kills invariance: no Golay code on the surface is `T_d`- or `O_h`-invariant |
| `GolayTh.lean` | the other side: explicit Golay codes on the surface preserved by the rotations `O` and by the pyritohedral group `T_h`, each group being exactly the stabiliser of its code |

*Meaning — measurable content*

| file | contents |
|---|---|
| `MeasuredWords.lean` | physical dimension on the cube; the characteristic-2 ceiling, proved unavoidable for XOR |
| `MeasuredSentences.lean` | the parity cube's measured precision: 356 true, 1758 accepted |
| `IntegerCube.lean` | integers inside the cube, a ripple-carry adder per face, precision 1.00 |
| `WideInteger.lean` | integers on a pair of records: the window widens from 16 to 256 |
| `Grounding.lean` | tying the micro-world's atoms to dimensions, and what each layer cannot do |
| `SentenceCode.lean` | storing clauses as codewords, with three-cell repair |
| `ClauseStore.lean` | clauses, links and dimensions as records on one surface: 4096 records, 1024 per role |
| `CubeThought.lean` | inference as addition on the surface — a law word per entailment, and denial as one universal translation |

*Language — the narrow world*

| file | contents |
|---|---|
| `Semantics.lean` | the 512-world micro-world, its literals, laws, and true sentences |
| `Chat.lean` | question answering: *is it…? why…? which…? what if…?* |
| `Discourse.lean` | `and` / `but` / `so`, and a corpus of 1536 checked paragraphs |
| `WideDiscourse.lean` | paragraphs that change subject, and cross-subject deductions |
| `Dialogue.lean` | conversation with topic and commitments; no contradictions |
| `Conversation.lean` | pronouns and "the former"/"the latter"; a repeated question escalates to a reason, then a priced plan |
| `Paragraph.lean` | paragraphs whose length is content, not fuel: they stop when the stock of facts is exhausted |
| `Zipf.lean` | the frequency test (negative) and a Huffman code that pays (positive) |

*Language — the wide world*

| file | contents |
|---|---|
| `WideWorld.lean` | 24 things: 1872 words, 3744 literals, 3600 contingent, laws proved for every size |
| `Abstract.lean` | kinship — an abstract vocabulary the measurements provably cannot define |
| `WideChat.lean` | chat over the wide world: every answer true, every reason a ground |
| `WideZipf.lean` | Zipf re-measured after widening: 37 of 39 ranks fit, but the head still crosses the law |
| `Quantified.lean` | *every* and *some* over the things of the world: duality, instantiation, witnesses, and a proof that quantification is not sugar over the lexicon |

*Time, cause, and action*

| file | contents |
|---|---|
| `Causation.lean` | `because` with a direction of time; the entailment version proved cyclic |
| `Narrative.lean` | shortest plans within a three-action horizon, and narration of change |
| `PlanCost.lean` | priced plans, proved cheapest by induction, and the argument for a plan |
| `ReachPlan.lean` | planning with no horizon: a reachability table over all 512 worlds |

*Stage 5 — learning, grammar, scale, the continuum*

| file | contents |
|---|---|
| `Learning.lean` | the law table fitted from a corpus of worlds: recall 1 at every size, the learning curve, a 12-world teaching set, a proved lower bound of 4 |
| `Relative.lean` | relative clauses: conservativity, monotonicity, 12 law schemas for every world size, and the accidental generalisations measured |
| `Scaling.lean` | the counts as polynomials in `n`: `3n + 3n²` contentful atoms, `6n + 6n²` literals, and every world described by exactly `3n + 3n²` facts |
| `Continuous.lean` | integer temperatures and masses, graded comparatives that recover the exact difference, and the substrate window proved sharp |
| `GolayEnumerator.lean` | 759 octads and the weight enumerator `1, 759, 2576, 759, 1` for every code with the four defining properties |
| `Capstone.lean` | learn → utter → check: 78 English conditionals learned from 12 worlds, sound, complete, and licensing the system's explanations |

*Root*

| file | contents |
|---|---|
| `Package.lean` | imports everything and audits the axioms of 179 headline results |
| `Main.lean` | project-wide option settings |

## Building and running

```bash
lake build                         # whole development
lake build RequestProject.Package  # + the axiom audit
python3 glm_chat2.py               # stage 1–2 Python mirror (no dependencies)
python3 glm_discourse.py           # stage 3 Python mirror (no dependencies)
python3 make_theorem_index.py      # regenerate THEOREM_INDEX.md
python3 glm_clean/exp7_invariance_check.py   # the old invariance search, now superseded by proof
```

The two Python mirrors recompute every number in the reports and print the Lean
value beside their own, so you can poke at the system directly. The Lean side
is the authority.

---

This project was edited by [Aristotle](https://aristotle.harmonic.fun).

To cite Aristotle:
- Tag @Aristotle-Harmonic on GitHub PRs/issues
- Add as co-author to commits:
```
Co-authored-by: Aristotle (Harmonic) <aristotle-harmonic@harmonic.fun>
```
