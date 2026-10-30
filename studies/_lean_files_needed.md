# Missing Lean files registry

*Updated 29 October 2026 (Iteration 18).*

## Status

| status | count | description |
| --- | --- | --- |
| **placeholder** | 12 | referenced by AxiomAuditAll.lean; placeholders created, need real content |
| **recovered** | 1 | AxiomAuditAll.lean — recovered from owner, placed in src/lean/ |
| **source_material** | 14 | in source_material/ (already evaluated, not to be absorbed) |
| **archived** | 7 | in archive/lean_drafts/ (superseded) |

## Placeholder Lean files (need real content from owner)

These 12 files are referenced by `AxiomAuditAll.lean` (the whole-development
axiom audit) but were not in the upload. Placeholder files have been created
so the import list resolves; each needs to be replaced with the real Lean
content from the owner's development environment.

| file | Python pair | study | what it proves |
| --- | --- | --- | --- |
| `AdversarialDialogue.lean` | `reasoning/adversarial_dialogue_study.py` | ADVERSARIAL_DIALOGUE_STUDY | 9 theorems of Phase 167 |
| `ColourInduction.lean` | — | — | colour induction theorems |
| `ContextFrames.lean` | `runtime/context_frames.py` | CONTEXT_FRAMES_STUDY | context-frames theorems |
| `FoldMachine.lean` | `reasoning/fold_machine_study.py` | FOLD_MACHINE_STUDY | fold machine theorems |
| `LeechKissing.lean` | `reasoning/leech_shells.py` | LEECH_KISSING_STUDY | minimal shell bijection |
| `LeechMachine.lean` | `reasoning/leech_shells.py` | — | Leech machine theorems |
| `LeechShells.lean` | `reasoning/leech_shells.py` | LEECH_SHELLS_STUDY | Leech shell theorems |
| `LorentzPlane.lean` | `reasoning/frame_plane.py` | IMPROPER_FRAME_STUDY | Lorentz plane theorems |
| `SourceTiers.lean` | `knowledge/source_tiers.py` | SOURCE_TIERS_STUDY | source tier theorems |
| `StudyLedger.lean` | `corpus/study_ledger.py` | STUDY_LEDGER_STUDY | study ledger acyclicity |
| `ThermoFriction.lean` | `knowledge/thermo_friction_study.py` | THERMO_FRICTION_STUDY | thermo friction theorems |
| `ToolMachine.lean` | `reasoning/tool_machine.py` | TOOL_MACHINE_STUDY | tool machine theorems |

## Recovered files

| file | source | status |
| --- | --- | --- |
| `AxiomAuditAll.lean` | Owner upload | **placed** in src/lean/RequestProject/GLM/ — imports every Lean file and fails the build if any theorem depends on an axiom outside the standard set |
| `LeechShellCount.lean` | Owner upload | **already present** (confirmed identical) |
| `LorentzImproper.lean` | Owner upload | **already present** (confirmed identical) |
| `leech_shells.py` | Owner upload | **replaced** the existing Python module |
| `cases.py` | Owner upload | **already present** (confirmed identical) |
