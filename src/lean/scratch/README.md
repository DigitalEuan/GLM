# `src/lean/scratch/` — Lean kept out of the build

## Tier 0 — the coarse read

**Question.** Why is there Lean outside `src/lean/RequestProject/`, and is any of it part of the development?

**Verdict.** None of it is part of the development: files here are kept, not deleted, but `lake build` does not build them and the axiom audit does not import them.

**Deciding figure.** One file, `Scratch.lean`.

**Recomputed by.** (hand-written argument; nothing to recompute)

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 31 October 2026 (repository check).*

None of it is part of the development: files here are kept, not deleted, but `lake build` does
not build them and the axiom audit does not import them. They sit outside `RequestProject/`, so
the `RequestProject.+` glob of `lakefile.toml` does not reach them and `AxiomAuditAll.lean` does
not list them. There is one file, `Scratch.lean`:

| file | what it is | why it is here |
| --- | --- | --- |
| `Scratch.lean` | a working copy of the Ingleton computation (`entropyOf`, `ingleton_violated`) in the root namespace | it was in the build tree as `RequestProject/GLM/Scratch.lean`, declaring names outside `GLM`; the cited theorem is `GLM.NonShannon.ingleton_violated` in `RequestProject/GLM/NonShannon.lean`, which proves the same statement inside the development |
