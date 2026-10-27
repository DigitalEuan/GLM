# Summary of changes for run 97fcfeda-6b2b-40a0-b51a-2bce86c24d7e
This round is **Phase 184, the declared majority rule**. It takes the first line of To-Do item 11 in `STATUS.md` §2.1: a majority rule for conflicting examples, with its own soundness condition. It also fixes a slowdown that was making the end-to-end evaluation time out. Nothing else from the To-Do list was taken.

**Lean** (`overlay/glm_lean/RequestProject/GLM/LorentzianMajority.lean`, added to `AxiomAuditAll.lean`). It builds with no `sorry`, and the whole-development audit reports 10069 theorems on the standard axioms only. The rule splits the examples into groups that state the same target. It answers the target whose group holds more than half the total weight, and refuses if none does. Proved, for any finite set of examples, any rational weights and targets of any type:
- At most one target can hold more than half the weight (`majority_unique`), and the rule answers exactly that target (`majorityRule_eq_some_iff`).
- **Soundness condition** (`majority_never_wrong`, `majority_sound`): if the examples stating the true target hold at least half the weight, the rule never answers anything else. If they hold more than half, it answers correctly.
- **The condition is tight** (`majority_misled`): below half, wrong examples that agree with each other decide the answer. No rule that reads only the answers can check the condition; the caller has to supply it.
- **A wrong answer needs many wrong examples** (`majority_wrong_needs_decoys`): if an answer is backed by \(g\) of \(k\) examples, at least \(g\) of them must be wrong for it to be wrong.
- Each agreeing group has zero spread in the evidence space (`group_disp_zero`, `group_evid_null`), and wherever Phase 183's dispersion guard answers, the rule gives the same answer (`majority_extends_guard`).

**Python:**
- `reasoning/lorentzian_majority.py`, exposed as a new **`tool majority A : B, … :: C`**. It names the examples it outvoted and states with each answer how many examples would have to be wrong for the answer to be wrong. `tool evidence` is unchanged.
- A new measurement, `tools lorentzian-majority`, whose marks were committed before the first run: **8 of 8 met**. Physics relations, 300 queries per condition:
  - two good examples and one decoy: 155 right, 0 wrong, where the guard answers none (this reproduces Phase 183's figure);
  - three good and two decoys: 161 right, 0 wrong;
  - one good example and two decoys that agree: 148 wrong, exactly the cases `majority_misled` predicts;
  - one good, two agreeing decoys and two other decoys: the rule refuses all 300, where a simple plurality vote is wrong 150 times.
- **The cost:** with two good examples against two decoys that disagree with each other, a plurality vote gets 149 right and the majority rule refuses all of them. This is in the study.
- New tests in `tests/test_lorentzian_majority.py`.
- New write-up: `studies/LORENTZIAN_MAJORITY_STUDY.md`.

**The evaluation fix.** With 6,224 Lean declarations, `report lean` took about 199 seconds, and the 8-process evaluation timed out on it and on `report relay` (221 of 223 passed). I changed the nearest-neighbour search in `lean_address.nearest_points` to sort points along an integer principal axis and stop scanning using an exact bound. `report lean` now takes about 56 seconds and every figure is unchanged; the test comparing the search with brute force passes. `report relay` is still about 230 seconds when run alone and is now a To-Do line in `STATUS.md` §2.2.

**Checks run:**
- End-to-end evaluation: 223 of 223 on 8 processes.
- `corpus --check`: current.
- `tools dates`: 0 defects.
- Every measurement made stale by the code changes was re-taken. Their marks are unchanged, except `native_words` W2, which moved from not met to met; that mark had not been re-taken for several corpus updates, so the change reflects the larger corpus.
- `test_lorentzian_majority`, `test_lorentzian_evidence`, `test_axiom_guard`, `test_connected_machine` and the fast-search tests all pass when run by hand. pytest can't be installed here, so the full test-suite sign-off is still owed, as in earlier rounds.

**Records updated:** `STATUS.md` (the "Just closed" paragraph, item 11, a new §2.2 line), `MASTER_PLAN.md` (Phase 184), `SYSTEM.md`, the academic paper (§20.57 and result 48), `WHITEBOARD.md` and `tests/README.md`. The proved theorems and the rule's definition are registered in the Properties table. All work is committed and pushed.