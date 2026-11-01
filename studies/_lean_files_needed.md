# Missing Lean files registry

## Tier 0 — the coarse read

**Question.** Which Lean files were lost in the reorganisation, which complete files wait for them, and what does recovering one take?

**Verdict.** 13 files are missing and recorded here rather than imitated by a placeholder; 6 complete files that import a missing file are held in `src/lean/awaiting_recovery/`, out of `lake build`, until it returns.

**Deciding figure.** 13 missing, 6 held, 1 restored (`Rule30/SidewaysPeriodTwo.lean`).

**Recomputed by.** `glm_universal.lean_check.check_tree`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Last altered 31 October 2026 (repository check: the twelve placeholder files were removed from
the build tree and recorded here; `LorentzianMajority.lean` added; six files that import a
missing file moved to `src/lean/awaiting_recovery/`; `Scratch.lean` moved out of the build to
`src/lean/scratch/`; later the same day the check that enforces the holding rule named correctly
— `lean_check.audited_or_held`, pinned in `tests/test_constants.py`).*

The reorganisation of October 2026 lost some Lean files. The owner does not have the originals
(answer of 30 October 2026), so each is recorded here as missing rather than imitated by a
placeholder. A placeholder that contains only a comment builds, but it lets
`AxiomAuditAll.lean` appear to audit a file that proves nothing; that is why the twelve
placeholders are gone.

`python3 -m glm_universal.lean_check` lists the held files and what each waits for. A file held
back from the build must wait only for files named in the first table below (or for another held
file): `glm_universal.lean_check.audited_or_held` accepts a held file only then, and
`src/glm_universal/tests/test_constants.py` (`TestTheHoldingRegistry`) fails otherwise, as do the
tests of the held files' own studies (for example `test_leech_shell_count.py`).

## Status

| status | count | where |
| --- | --- | --- |
| **missing** | 13 | not in the repository; the original is needed, or a new proof written by a later round |
| **held** | 6 | `src/lean/awaiting_recovery/RequestProject/GLM/` — complete files that import a missing file, kept out of `lake build` until it returns |
| **restored** | 1 | `Rule30/SidewaysPeriodTwo.lean` (Round 33 of the Rule 30 study, claim C318), back in the build |

## Missing files

| file | Python pair | study | what it proved | needed by |
| --- | --- | --- | --- | --- |
| `AdversarialDialogue.lean` | `reasoning/adversarial_dialogue_study.py` | `ADVERSARIAL_DIALOGUE_STUDY.md` (Phase 167) | the 9 theorems of the adversarial dialogue | `ResumedDialogue.lean` (held) |
| `ColourInduction.lean` | `reasoning/colour_induction.py` | `COLOUR_INDUCTION_STUDY.md` part A (Phase 178) | colour induction (12 theorems: `count_perm`, `fit_iff_functional`, `gate_sound`, `untested_never_answers`, `unread_fitted_refuses`) | — |
| `ContextFrames.lean` | `engineering/context_frames_study.py` | `CONTEXT_FRAMES_STUDY.md` (Phase 170) | context-frame theorems | — |
| `FoldMachine.lean` | `reasoning/fold_machine_study.py` | `FOLD_MACHINE_STUDY.md` (Phase 160) | the counting rule for a position in a sorted column | — |
| `LeechKissing.lean` | `reasoning/leech_shells.py` | `LEECH_KISSING_STUDY.md` (Phase 165) | the minimal shell both ways; 196,560 | — |
| `LeechMachine.lean` | `reasoning/leech_shells.py` | — | Leech machine theorems | — |
| `LeechShells.lean` | `reasoning/leech_shells.py` | `LEECH_SHELLS_STUDY.md` (Phase 164) | the Leech shapes | `LeechShellCount.lean`, `GolayDeepHole.lean` (held) |
| `LorentzianMajority.lean` | `reasoning/lorentzian_majority.py` | `LORENTZIAN_MAJORITY_STUDY.md` (Phase 184) | the declared majority rule: uniqueness, soundness, tightness | — |
| `LorentzPlane.lean` | `reasoning/frame_plane.py` | `COLOUR_INDUCTION_STUDY.md` part B (Phase 178) | the Lorentz plane (13 theorems: boosts and rotations are Lorentz, `thomas_wigner`) | `LorentzImproper.lean` (held) |
| `SourceTiers.lean` | `knowledge/source_tiers.py` | `SOURCE_TIERS_STUDY.md` (Phase 162) | source tier theorems | — |
| `StudyLedger.lean` | `corpus/study_ledger.py` | `STUDY_LEDGER_STUDY.md` (Phase 161) | study ledger acyclicity | — |
| `ThermoFriction.lean` | `knowledge/thermo_friction_study.py` | `THERMO_FRICTION_STUDY.md` (Phase 159) | thermomechanical friction theorems | — |
| `ToolMachine.lean` | `reasoning/tool_machine.py` | `TOOL_MACHINE_STUDY.md` (Phase 163) | tool machine theorems | — |

A study whose Lean file is missing reports its Lean mark as not met; the mark returns when the
file does. Recovering a file means: put it at `src/lean/RequestProject/GLM/<file>`, move every
held file that waited for it back beside it, run
`python3 -m glm_universal.lean_check --write-audit`, then `scripts/rebuild_lean.sh`.

## Held files

| file | waits for |
| --- | --- |
| `GolayDeepHole.lean` | `LeechShells.lean` |
| `LeechShellCount.lean` | `LeechShells.lean` |
| `LorentzImproper.lean` | `LorentzPlane.lean` |
| `LorentzUnits.lean` | `LorentzImproper.lean` (held) |
| `ResumedDialogue.lean` | `AdversarialDialogue.lean` |
| `StackedDialogue.lean` | `ResumedDialogue.lean` (held) |

The Python readers find a held file through `glm_universal.constants.lean_file`, so a study that
reads a theorem statement from it still reads it; its "audited" mark is not met while it is held.

## Earlier recoveries

| file | source | status |
| --- | --- | --- |
| `AxiomAuditAll.lean` | owner upload | in the build tree; its import list is regenerated with `lean_check --write-audit` |
| `LeechShellCount.lean` | owner upload | held (see above) |
| `LorentzImproper.lean` | owner upload | held (see above) |
| `Rule30/SidewaysPeriodTwo.lean` | the Rule 30 round's own copy | restored 31 October 2026 |
| `Scratch.lean` | owner upload | moved out of the build to `src/lean/scratch/` on 31 October 2026: a root-namespace working copy of `GLM.NonShannon.ingleton_violated` (`NonShannon.lean`), which the studies cite |
