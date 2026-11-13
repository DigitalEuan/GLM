# GLM Lean review: what is relevant to the cent compiler

Source-level review of the adjacent GLM tree
(`glm-study/src/lean/RequestProject`, 434 `.lean` files: 433 under `GLM/` and
one `Main.lean`). The tree was triaged by directory and keyword; the wheel,
Golay, `Shortcut/`, `IntakeChecks/` and relevant root headers were read, and
the direct candidates were inspected in detail.

**No Lean build was run.** The GLM repository's own `STATUS.md` says its Lean
files have not been built in the session that created them; the build belongs
to the owner's `scripts/rebuild_lean.sh`. Everything below is a source claim,
not a verified build or an import into `cent_compiler_v12`.

## Bottom line

Only a small part of the GLM tree targets the cent compiler. The genuinely
direct files are:

| File | What it contains | Why it matters here |
|---|---|---|
| `Wheels/CentWheels.lean` | 1,696 lines covering the 31 supplied cent formula wheels: absorbed W16–W25, W28, W29, W32–W34, the W4/W6 additions, W11–W15, and the supplied axioms that fail on their own tables. It defines the eight-axis dimension map, proves `axioms_balanced`, and carries explicit derivability and refusal certificates. | The formal counterpart of the cent wheel relation vectors, dimension tables and study verdicts. It is the closest thing in the tree to a proof spec for the main compiler's wheel layer. |
| `IntakeChecks/Derivability.lean` | A generic proof of the two certificates: `derivable_of_combination` (an explicit rational combination) and `not_derivable_of_functional` (a separating functional). Includes force-from-mass-acceleration and energy-not-from-speed examples. | Matches the exact span-membership/refusal logic behind `axiom_graph.derive_from` and its `missing_bridges`; the formal statement is independent of `CentWheels`. |
| `ConnectedMachine.lean` | Wheel unions, soundness of splitting shared names, the W5/W10 `E = mc²` refusal, and the W5/W6 hydraulic junction licensing. | The closest formal treatment of the junction/non-identity semantics used by the main axiom graph, including why a naive union can over-derive. |
| `EngineeringWheels.lean` | Formula wheels as rational span membership; Ohm-wheel positive and negative controls; translation carrying derivations across an analogy; Smith chart and delta-sigma facts. | Conceptual match to the main wheel/derivation layer and to the delta-sigma route, not a copy of the cent tables. |
| `DomainWheels.lean` | W11–W15: oscillator conflation under a naive union, refusal after splitting `angular_frequency`, and swept-volume licensing at declared junctions. | Directly relevant to the graph's split-name and junction rules; again conceptual, not cent data. |

`AxiomAuditAll.lean` imports many of these files, but it is an aggregate
whole-development audit, not a cent formalization. It also contains entries for
placeholder modules, so it is not evidence that the tree builds.

## Leech/Golay branch

These are relevant to the Leech audit and lattice bridge, not to the physical
compiler's wheel tables:

| File | Result |
|---|---|
| `Shortcut/Leech.lean` | `IsLeech` in the integral `×√8` scaling; every nonzero Leech vector has norm² at least 32; doubled Golay differences are Leech vectors; the minimal case is exactly the octad step. |
| `Shortcut/GolayWeights.lean` | Exhaustive weight enumerator `1 + 759x⁸ + 2576x¹² + 759x¹⁶ + x²⁴`, double-evenness, minimum distance 8, constant-time codeword recognition. |
| `Golay/Code.lean` | The concrete `[24,12,8]` code via syndromes; syndrome additivity and the statement that equal syndromes differ by a codeword. This formalizes cosets, not the separate `Λ/2Λ ≅ F₂²⁴` claim. |
| `Golay/Sextet.lean`, `Census.lean`, `Dynamics.lean` | The six-way covering-radius tie, the coset census (1,771 of 4,096 syndromes at weight four), and the perturb/correct dynamics. Useful for Leech/Golay claims; not cent compilation. |
| `ZeroStorage.lean` | A negative audit: the proposed mod-4 sieve is sound but keeps only 1,152 of the 196,560 minimal vectors; an explicit octad vector is rejected. This is valuable as a warning against an invalid lattice-generation shortcut. |
| `DimensionCarrier.lean` | Proves XOR is blind to even shifts and that a 24-bit word is a derived carrier, not a primary one. This supports the provenance warning around the 24-bit class isomorphism; it is not a new proof of that isomorphism. |
| `NativeWords.lean` | Golay names preserve token Jaccard overlap; a shared Golay class is a near letter set. Relevant to token naming/addressing, not to the compiler's formulas. |

`LayerChain.lean` is **not** the cent compiler's five fidelity layers. It
formalizes the GLM's five information readings over 24 rational coordinates
(substrate, integer, rational, Griess, universal). The names overlap, but the
carrier and the refinement relation are different. `IntegerWheel.lean` and
`SporadicOrders.lean` formalize GLM provisions wheels (OEIS sequences and the 26
sporadic group orders), not the cent formula wheels.

The remaining bulk is not directly relevant: 139 files under `Rule30/`, the
`HypothesisEngine`, and the general semantics/ARC material.

## Verification status and caveats

- `CentWheels.lean` says `tests/test_cent_wheels.py` re-checks every vector,
  table, certificate and verdict against the Python. **No such test file is
  present in this workspace.** That cross-check cannot be run here, and the
  Lean file itself has not been built.
- `AxiomAuditAll.lean` names placeholder modules such as `FoldMachine.lean`,
  `LeechMachine.lean`, `LeechShells.lean`, `LorentzPlane.lean` and
  `ToolMachine.lean`. It is not a clean build target.
- `Shortcut/Leech.lean` and the Golay files prove lattice/code facts in their
  own scaling and definitions. They do not establish the study's move-level
  address scheme, the 24-bit class isomorphism, or a heat kernel.
- None of this tree is imported by `cent_compiler_v12`, and no file in it was
  modified during this review.

## Useful next step

If Lean integration is pursued, the first useful comparison is
`CentWheels` + `Derivability` against the main compiler's declared wheel
vectors and certificates, followed by `ConnectedMachine` against the
junction/split-name rules in `axiom_graph`. That is a proof-integration task,
not a data import; it should not be marked complete until the owner's Lean
build and the missing cross-check test actually pass.

## Application audit

[`GLM_CENT_APPLICATION_AUDIT.md`](GLM_CENT_APPLICATION_AUDIT.md) records the
usage-level gap map and scalar cent application probes. It does not import the
Lean tree or claim a proof result.
