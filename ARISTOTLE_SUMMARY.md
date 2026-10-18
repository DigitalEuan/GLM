# Summary of changes for run 51e503fe-59af-43ef-b67c-1cbdd5148103
I checked every file the Phase 158 summary names. Nothing is missing. Both studies and all the Lean files are in the repository.

**What I found**
- `studies/FRICTION_STUDY.md` is there, including the §8 note on using analogy as a method. `studies/OSCILLATOR_JUNCTION_STUDY.md` is there too.
- **The Lean files are not at the repository root.** They live under `overlay/glm_lean/RequestProject/`, which `lakefile.toml` names as the source folder. The last summary wrote the new file as `RequestProject/GLM/OscillatorJunction.lean`. That path leaves off the `overlay/glm_lean/` part, so it looks missing if you search from the root. The real file is `overlay/glm_lean/RequestProject/GLM/OscillatorJunction.lean`.
- **Count:** there are 232 Lean files, 231 under `GLM/` plus `Main.lean`. That matches the 231 that `STATUS.md` reports, since its count covers only `GLM/`. Every Lean module named in an `import` line exists.
- **Build:** I rebuilt the whole library with `lake build`. It succeeded with no errors, no `sorry` and no added axioms. The Phase 158 theorems use only the standard axioms.
- I also checked every `.md`, `.lean` and `.py` path mentioned in the main documents and studies. The few that don't resolve are intentional. They name files inside `source_material/GLM-main.zip`, files folded into others in earlier rounds (e.g. `CubeStabiliser.lean`, now `Cube/Stabiliser.lean`), or example file names used in the text.

**What was actually wrong, and the fixes**
1. **Properties table:** 261 of the 599 entries still pointed at the old path `RequestProject/GLM/…`. That is probably why the Lean files looked absent from your side. I pointed each one at `overlay/glm_lean/RequestProject/GLM/…`. No status changed (530 proved, 69 in progress), and every entry's file now exists and contains the named declaration.
2. **Visibility:** I published the study documents, the Lean files and the main project documents, so they should now show up for you.
3. **`STATUS.md`:** I added a short "Where the files are" paragraph. It says where the Lean files live, how to read a bare `RequestProject/…` path in older records, and what this check found. Editing `STATUS.md` made three generated blocks in other study files go stale, so I ran the document-update step: the address book and a block in `studies/CORPUS_ADDRESS_STUDY.md` were refreshed. `python3 -m glm_universal.corpus --check` now reports `current`. The end-to-end evaluation still reports no failures, with all 46 expected refusals at `boundary`.

Everything is committed and pushed. This run was the file check only: no new development round was taken, so the To-Do list in `STATUS.md` §2 is unchanged and Phase 159 is still open.