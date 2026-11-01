# Build and check logs

## Tier 0 — the coarse read

**Question.** Where do the logs of a Lean build or a repository check made on the owner's machine go, and why are they kept?

**Verdict.** `scripts/rebuild_lean.sh` and `scripts/check_repository.sh` write their logs here, and the logs are kept in version control on purpose: they are how a build made on the owner's machine reaches the next round, which cannot run `lake build` itself.

**Deciding figure.** Two scripts, two latest logs: `lean_build_latest.log` and `repository_check_latest.log`.

**Recomputed by.** (hand-written argument; nothing to recompute)

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 31 October 2026 (repository check).  Last altered 31 October 2026 (the repository
check script and this tier-0 block added).*

Two scripts write their logs here, each as a time-stamped file and a copy named `*_latest.log`:

| script | what it runs | latest log |
| --- | --- | --- |
| `scripts/rebuild_lean.sh` | the static Lean check, `lake exe cache get`, `lake build` (which includes `AxiomAuditAll.lean`), and a `sorry`/`admit` scan | `lean_build_latest.log` |
| `scripts/check_repository.sh` | the Python gates: `lean_check`, the directives, the date stamps, the intake ledger, `corpus --check`, a smoke query, `pytest`, the evaluation | `repository_check_latest.log` |

These logs are kept in version control on purpose: they are how a build made on the owner's
machine reaches the next round, which cannot run `lake build` itself. Send the two latest logs
back with the next upload; the next round fixes whatever they report.
