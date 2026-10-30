# Round 44 — the needs wheel, and the escalation sketch corrected

Pure Python 3, standard library only. Run everything with:

    python3 run_round44.py            # about 20 s; writes out/round44_results.{json,md}
    python3 run_round44.py --no-real-arc

| File | What it is |
|---|---|
| `glm_needs.py` | Portable needs-wheel protocol: `Need`, `Provision`, `Wheel`, `answer` (first provision that speaks wins, as in Lean `NeedsWheel.answer`), `score` (right / wrong / overclaim / abstain), `run_conditions` (base, guard only, requested, requested + guard, all, random same-size controls) |
| `needs_rule30.py` | The 40 statements of `../glm_wheel.json` plus held-out ones. Each has a ground truth fixed in advance (a Lean name, an exact computation, or OPEN). The engine states its needs, and the provisions are exact recomputation, the Lean ledger, and checked implications |
| `needs_arc.py` | A small ARC-style solver (programs of depth ≤ 2, answers only if every consistent program agrees), a need diagnosis from the demonstrations alone, synthetic puzzle families (development and held-out), and the provisions |
| `run_round44.py` | Runs Rule 30, synthetic ARC, and real ARC (the 50 tasks inside `../glm_repo.zip`), with a leave-one-out ablation |
| `out/round44_results.md`, `.json` | The results |
| `V16_WHEEL_REVIEW.md` | Review of `hypothesis_engine_v16.py`, `glm_wheel.py`, `glm_wheel.json`, and what the measurements show |

The corrected edition of `GLM_Escalation_Boundaries_Exploration.md` is
`RequestProject/GLM/Escalation/GLM_Escalation_Boundaries_Exploration_CORRECTED.md` in the Lean project, inside the
Lean package next to the theorems it cites.

Headline results (details in `V16_WHEEL_REVIEW.md`):

* **Rule 30 wheel.**
  * The base engine scores 8 right, 12 wrong and 15 overclaims out of 40.
  * With the provisions it asked for plus an honesty guard, it scores 40 right and 0 wrong. The
    Lean ledger carries most of the gain (without it: 30 right). The ledger and the ground truth
    share sources, so this measures routing to checked sources, not discovery.
* **Synthetic ARC, held-out families.**
  * Base: 19/120.
  * Provisions requested from development needs: 72/120, against 55–73 for random sets of the
    same size.
  * Per-puzzle stated needs: 108/120, never wrong.
* **Real ARC.** 2 of 53 tests solved, with no wrong answers. Most needs are "unknown", so the need
  vocabulary is the bottleneck.
* **Wheel entries.**
  * Refuted by Lean certificates: H19, and the linear-complexity clause of ledger C160.
  * H36's comparison is inverted.
  * The "language wheel" entries L-H01, L-H04 and L-H06 are refuted by the Lean ledger.
