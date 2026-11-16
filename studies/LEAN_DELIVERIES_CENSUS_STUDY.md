# The two received Lean deliveries: what the tree already holds, and what absorbing them would take

## Tier 0 — the coarse read

**Question.** Of the two Lean deliveries registered on 13 November 2026 (`lean_to_add`, `leechlean`), which part does the build tree already hold, which part is new, and what would absorbing the rest take on a workspace with no Lean toolchain?

**Verdict.** Six of the 87 supplied files are byte-identical to files the tree already has, and none of the rest can be copied in: 0 of the delivery's 163 item-local imports resolves in the tree, because the five `lean_to_add` developments are rooted at flat `RequestProject.*`, `FirstPrinciples.*` and `Projection.*` while every tree module lives under `RequestProject.GLM.*`. Absorbing them is a re-rooting port whose only check is `lake build`, so both items stay at *triaged* here and the port is owed to the owner's machine, with the thirteen missing Lean files still missing: neither delivery contains one of them.

**Deciding figure.** 0 of 163 item-local imports resolve as written; 6 of 87 files byte-identical to the tree; 8 supplied files byte-identical to each other; 0 `sorry` in all 87.

**Recomputed by.** `glm_universal.corpus.lean_deliveries.census_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

*Created 15 November 2026 (platform round, P4 intake: the two items filed on 13 November were at `received` with no kind, offers or next step). No marks are declared and none is claimed: this is a census taken before any absorption was proposed, not a hypothesis test. It changes no answer the GLM gives.*

---

## 0. What this document is

`source_material/ToDo/lean_to_add` and `source_material/ToDo/leechlean` were
moved out of the build tree on 13 November 2026 and registered at `received`
(STATUS.md §2.1, P1 and P4). The owner's rule for the first of them is that it
is absorbed *only if the main Lean folder does not already hold it*, and a file
name cannot answer that: the 12 November upload placed files beside files that
differ, and placed some byte-identical ones beside their own copies.

This is the measurement behind the triage. It reads text only — no Lean
toolchain is involved and none is claimed — and it uses
`glm_universal.lean_check.parse_file`, the parser the tree checker itself uses,
so the census and `lean_check` cannot disagree about what a file declares.

## 1. The census

The build tree at the time of measurement: 419 Lean files under
`src/lean/RequestProject`, 9,344 distinct declaration names.

| item / sub-project | files | declarations | names the tree lacks | byte-identical to the tree | same name, different content | imports |
| --- | --- | --- | --- | --- | --- | --- |
| `lean_to_add/FirstPrinciples` | 7 | 82 | 82 | 0 | 4 | `FirstPrinciples`, `Mathlib` |
| `lean_to_add/Projection` | 8 | 133 | 133 | 0 | 1 | `Projection`, `FirstPrinciples`, `Mathlib` |
| `lean_to_add/aristotle_01` | 12 | 321 | 321 | 0 | 10 | `RequestProject`, `Mathlib` |
| `lean_to_add/leech_lattice` | 9 | 126 | 126 | 0 | 9 | `RequestProject`, `Mathlib` |
| `lean_to_add/mog_cube_1` | 43 | 1,337 | 1,328 | 1 | 4 | `RequestProject`, `Mathlib` |
| `leechlean/2_LEECHLEAN_STUDY` | 6 | 98 | 42 | 4 | 0 | `RequestProject`, `Mathlib` |
| `leechlean/demo` | 2 | 41 | 2 | 1 | 0 | `Mathlib` |

`lean_to_add` is 79 files and 1,999 declarations; `leechlean` is 8 files and 139
declarations. All 87 files parse, none contains `sorry` or a hand-written
`axiom`, and no file in either delivery is empty.

**The two halves are not the same kind of thing.** `lean_to_add` is Lean: five
separate developments, each with its own reports, Python mirrors and
`lakefile.toml` in the case of `aristotle_01`. `leechlean` is a Python package
that addresses the parts of Lean files on the Leech lattice, with six Lean files
of its own in `2_LEECHLEAN_STUDY`.

## 2. What the tree already holds

Six files, by SHA-256:

| supplied file | the tree's copy |
| --- | --- |
| `lean_to_add/mog_cube_1/RequestProject/Main.lean` | `src/lean/RequestProject/Main.lean` |
| `leechlean/2_LEECHLEAN_STUDY/Derivability.lean` | `src/lean/RequestProject/GLM/IntakeChecks/Derivability.lean` |
| `leechlean/2_LEECHLEAN_STUDY/NextTerm.lean` | `src/lean/RequestProject/GLM/IntakeChecks/NextTerm.lean` |
| `leechlean/2_LEECHLEAN_STUDY/RuleThirtyBits.lean` | `src/lean/RequestProject/GLM/IntakeChecks/RuleThirtyBits.lean` |
| `leechlean/2_LEECHLEAN_STUDY/SporadicOrderCheck.lean` | `src/lean/RequestProject/GLM/IntakeChecks/SporadicOrderCheck.lean` |
| `leechlean/demo/sample_Golay_Code.lean` | `src/lean/RequestProject/GLM/Golay/Code.lean` |

The four `IntakeChecks` files were built on their own in the standalone check of
1 November 2026 and are the tree's own copies of `leechlean`'s study Lean. Of
`leechlean`'s six study files, then, four are already held and two are new:
`LeechLeanCodec.lean` and `LeechLeanGolay.lean`, 42 declaration names the tree
does not declare.

Eight files are byte-identical to each other *inside* the delivery: the eight
that `aristotle_01` and `leech_lattice` both carry (`Decoder`, `FactorMap`,
`Golay`, `GolayWeights`, `GrayCode`, `Leech`, `Shortcut`, `Substrate`).
`aristotle_01` adds four files of its own (`Lightspeed`, `Main`, `ObserverY`,
`SubstrateConstants`). Absorbing both copies would be worse than absorbing one.

## 3. What is not held, and why it cannot be copied in

**No item-local import resolves.** Of the 163 imports that name the delivery's
own modules — as opposed to `Mathlib` — 0 resolve against the tree's module
names. The reason is the root, not the content: the deliveries are lake projects
of their own, rooted at `RequestProject` (`first` `FirstPrinciples`, then
`Projection`), while the tree's modules are all under `RequestProject.GLM`.

| supplied import root | files | tree modules under that root |
| --- | --- | --- |
| `RequestProject.*` (flat) | 64 | 0 — the tree has `RequestProject.Main` and `RequestProject.GLM.*` |
| `FirstPrinciples.*` | 7 | 0 |
| `Projection.*` | 8 | 0 |

So the work of absorbing `mog_cube_1` is a re-rooting of 43 files: every
`import RequestProject.X` becomes `import RequestProject.GLM.<Place>.X`, and
`AxiomAuditAll.lean` is regenerated. The interesting cases are the ones where a
tree module already exists with the same content or the same name:

* **Same name, different content (28 files).** Four `FirstPrinciples` files
  (`Distinction`, `FitCapacity`, `Packing`, `Triad`) and `Projection/Layers`
  share a name with a module the tree already holds under `GLM/`; so do the
  eight `aristotle_01`/`leech_lattice` files (`Shortcut/*`, `PipelineKit/*`).
  This census cannot say which copy is newer or better — that is a reading of
  the two files, and it must be done before a port, not after.
* **Same content, different place.** The tree carries flat copies of two
  `mog_cube_1` files, `GLM/CubeStabiliser.lean` and `GLM/CubeSurface.lean`,
  beside their re-homed versions `GLM/Cube/Stabiliser.lean` and
  `GLM/Cube/Surface.lean`. `lean_check` prints one warning for every
  declaration that stands in both — the evidence that a copy-in has been tried
  once already and left two homes for one development. A port should *move*,
  never add a third copy.

**One defect before any build.** `leechlean/2_LEECHLEAN_STUDY/LeechLeanCodec.lean`
imports `RequestProject.GLM.IntakeChecks.LechLeanGolay`, a misspelled module
that exists nowhere — not in the tree, not in the delivery. That file cannot
build even in the delivery it came from, so it is a one-line repair before it is
anything else, and its companion `LeechLeanGolay.lean` is the module it means.

## 4. `leechlean`'s Python half does run here

The item is not all Lean. Its own codec demo runs on this workspace with
`numpy` alone and the bundled codebook, and it reproduces its README's claim:

```
$ python3 demo/demo_encode_decode.py
tokens (ticks): 1686
addresses on the Leech lattice: 1686 / 1686
byte-exact round trip: True
total energy: 42200 lattice units (10550 bits of surprisal)
work integral ends at lattice point W = [...] (on lattice: True)
```

That is a measurement of the supplied item, not of the GLM: it says the demo
runs, not that the GLM gains anything from it. Whether the part-level addressing
it offers improves an answer, an address or a refusal is the *measured* stage of
the intake, and it has not been attempted.

## 5. What is owed, in the order it can be paid

**A. The tree's own Lean (P2).** Nothing in either delivery is one of the
thirteen missing files of [`_lean_files_needed.md`](_lean_files_needed.md) —
searched by name across both items and both demo copies. So the registry stays
at 13 missing, 6 held, and the work order the navigator gives still stands:
`LeechShells.lean` first (two held files wait on it alone: `LeechShellCount`,
`GolayDeepHole`), then `LorentzPlane.lean` (unblocks `LorentzImproper` and
`LorentzUnits`), then `AdversarialDialogue.lean` (unblocks `ResumedDialogue`
and `StackedDialogue`). A recovered file goes to
`src/lean/RequestProject/GLM/`, its held files move back beside it, then
`lean_check --write-audit`, then the build.

**B. The owner's build record.** Every item absorbed ahead of the build
(`glm_wheels_bundle`, `Rule30_GLM_Study`, `cent_compiler_v12`) is confirmed by
one thing: a passing run of the script that is already the owner's step.

```
scripts/rebuild_lean.sh            # static check, toolchain, cache get, lake build, sorry scan, citation re-take, build record
```

It writes `scripts/logs/lean_build_latest.log` and
`scripts/logs/lean_build_evidence.json`, exits 1 if any required step fails, and
its record is the only evidence the intake's *Lean verified* gate accepts. The
toolchain is pinned in the repository (`leanprover/lean4:v4.28.0`, Mathlib
`v4.28.0`), and the working notes put the cost of installing it and building at
about 6–8 GB and hours on two cores. After it passes:

```
PYTHONPATH=src python3 -m glm_universal.intake confirm-build glm_wheels_bundle
PYTHONPATH=src python3 -m glm_universal.intake confirm-build Rule30_GLM_Study
PYTHONPATH=src python3 -m glm_universal.intake confirm-build cent_compiler_v12
```

**C. The port of the two deliveries.** A port is one sub-project at a time, in
this order, each ending in `lean_check --write-audit` and a build:

1. `FirstPrinciples` (7 files) and `Projection` (8): self-contained — their only
   local imports are each other, and five of the files name modules the tree
   already holds, so diff those five first and decide same-or-new.
2. `mog_cube_1` (43 files): re-root to `RequestProject.GLM.Cube/` — the tree's
   `GLM/Cube/Stabiliser.lean` and `GLM/Cube/Surface.lean` are the re-homed copies
   of two of its files, so the flat `CubeStabiliser`/`CubeSurface` copies go
   rather than gain a sibling.
3. `aristotle_01`/`leech_lattice`: one port of 12 files (`leech_lattice`'s 9 are
   its subset), re-rooted to `RequestProject.GLM.Shortcut/`, whose copy the tree
   already carries in a different form.
4. `leechlean`'s two new Lean files: repair the `LechLeanGolay` import, then
   place beside the four `IntakeChecks` files that are already there.

None of these ports can be checked on this workspace, and a port that is not
built is not evidence: that is why neither item moves past *triaged* here.

## 6. Not claimed

* Nothing here says a supplied development is correct, better or worse than the
  tree's — only which files the tree already holds and what a port must touch.
* The declaring-name overlap is a name comparison, not a semantics comparison:
  a file whose declarations differ only by namespace is counted as new names.
  That is why §3 names the five same-name pairs that a reader must actually
  diff.
* No answer the GLM gives changed; no Lean file was added, moved or edited; no
  supplied file was edited.
* `leechlean`'s demo running is not a measurement of help.

## 7. How to take the measurement again

```bash
PYTHONPATH=src python3 -m glm_universal.corpus.lean_deliveries            # the tables above
PYTHONPATH=src python3 -m glm_universal.corpus.lean_deliveries --json      # per-file rows
PYTHONPATH=src python3 studies/scripts/lean_to_add_census.py               # the same, from the study side
```

Both read `source_material/` and `src/lean/` and write nothing. The test is
`src/glm_universal/tests/test_lean_deliveries.py`.

## In one paragraph

Six of the 87 supplied files are byte-identical to files the tree already has,
and none of the rest can be copied in: 0 of the delivery's 163 item-local
imports resolves in the tree, because the five `lean_to_add` developments are
rooted at flat `RequestProject.*`, `FirstPrinciples.*` and `Projection.*` while
every tree module lives under `RequestProject.GLM.*`. Absorbing them is a
re-rooting port whose only check is `lake build`, so both items stay at *triaged*
here and the port is owed to the owner's machine, with the thirteen missing Lean
files still missing: neither delivery contains one of them.
