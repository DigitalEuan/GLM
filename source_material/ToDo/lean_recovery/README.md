# Rebuilt Lean files: `LeechShells`, `LorentzPlane`, `AdversarialDialogue`

*Phase 190, 15 November 2026. Proposed replacements for three files the Lean
build needs and does not have — see `studies/_lean_files_needed.md`.*

## Why these three, and why they are reconstructions

`git log -S` on the declarations shows all three existed only as six-line
placeholders (added `794eb56`, deleted at `7eea8f8`) and were never written out,
so nothing was lost that could be recovered: there is no earlier text to restore.
What survived is their **consumers**: six files held in
`src/lean/awaiting_recovery/RequestProject/GLM/` are written against their exact
API, and three Python modules record the semantics and the theorem names.

So each file here is rebuilt from two things, and only those two:

| file | semantics from | API pinned by | theorems from |
|---|---|---|---|
| `LeechShells.lean` | `reasoning/leech_shells.py` | `LeechShellCount.lean`, `GolayDeepHole.lean` | `leech_shells.LEAN_THEOREMS` |
| `LorentzPlane.lean` | `reasoning/frame_plane.py` | `LorentzImproper.lean`, `LorentzUnits.lean` | `frame_plane.LEAN_THEOREMS` |
| `AdversarialDialogue.lean` | `reasoning/adversarial_dialogue_study.py` | `ResumedDialogue.lean`, `StackedDialogue.lean` | `adversarial_dialogue_study.LEAN_THEOREMS` |

`[DecidableEq β]`-free `after`, the exact `HeadSet c q S` argument order used by
`ResumedDialogue.resumed_least`, the two-parity shape of `IsLeech` that
`LeechShellCount` destructures, and `normSq` as an integral sum are all taken
from how the held files call them — not invented here.

## Status of each file — read this before adding them to the build

**`LorentzPlane.lean`** — complete: `eta`, `IsLorentz`, `minkowski`, `rest`,
`boostX`/`boostY`/`rot`, `boostTo`, and all thirteen theorems of
`frame_plane.LEAN_THEOREMS` (`boostX_lorentz`, `boostY_lorentz`, `rot_lorentz`,
`lorentz_mul`, `minkowski_preserved`, `boostTo_symm`, `boostTo_rest`,
`boostTo_lorentz`, `thomas_eq`, `thomas_lorentz`, `thomas_not_symm`,
`thomas_wigner`, `thomas_rotation_ne_one`), with the Thomas–Wigner numbers of the
study (`(5/3, −4/3, −4/3)·rot(15/17, −8/17)` in the `u = 1/2` case) as the
worked instance.

**`AdversarialDialogue.lean`** — complete: `HeadSet`, `after`, `Contradictory`
and the nine theorems (`adversary_live_subset`, `adversary_least`,
`adversary_resolved_mem`, `contradicted_iff_inconsistent`,
`conflicting_replies_contradict`, `repeat_reply_idem`, `consistent_lie_live`,
`consistent_lie_resolves`, `consistent_lie_confirmed`).

**`LeechShells.lean`** — **partial, and deliberately so.** Present and proved:
`normSq`, `IsLeech` (exactly the API the held files use), `support`,
`minimal_even_support`, `minimal_odd_pattern`. Owed: `minimal_shape`,
`shellCount_eq`, `shells_from_census`. The last two are the study's counting
procedure (per-coordinate generating functions over squared length and value
mod 8, summed over the code's five weights); it has to agree with
`LeechShellCount.lean`'s `patternGF`/`patternArr`, a 550-line specification that
cannot be checked without a build. `minimal_shape` is the case split over the two
lemmas that are here, plus "two coordinates of size 4". Asserting either would be
guessing, and a `sorry` fails this repository's own `lean_check` and
`AxiomAuditAll` — so they are recorded as owed instead.

## How to add them to the build

1. Copy the three files into `src/lean/RequestProject/GLM/` (they import
   `RequestProject.GLM.GolayWeightEnum`, so they belong in that namespace's
   directory, not in `awaiting_recovery/`).
2. `PYTHONPATH=src python3 -m glm_universal.lean_check --write-audit`
3. `scripts/rebuild_lean.sh` — static check, `lake build`, axiom audit, `sorry`
   scan, citation re-take and the build record. It exits 0 only on a full pass.
4. When it passes, move the dependent held files back out of `awaiting_recovery/`
   in this order, since each is written against the file above it:
   `LeechShells` → `LeechShellCount.lean`, `GolayDeepHole.lean`;
   `LorentzPlane` → `LorentzImproper.lean` → `LorentzUnits.lean`;
   `AdversarialDialogue` → `ResumedDialogue.lean` → `StackedDialogue.lean`.
   Then `studies/_lean_files_needed.md` goes from 13 missing to 10.

Expect elaboration errors on the first build: none of these has been compiled,
and they were written without a toolchain. `LorentzPlane` is the most likely to
build; `LeechShells`'s `minimal_odd_pattern` is the most likely not to (the
`±5` exclusion and the `24 + 8k` sum are the fiddly steps). Report the log at
`scripts/logs/lean_build_latest.log` and the next round repairs against it.
