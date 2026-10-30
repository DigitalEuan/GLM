# Summary of changes for run b869a397-9a30-48dd-bb82-f415f59a5505
This round (Phase 183, "the Lorentzian evidence space") takes the Lorentzian lift beyond puzzle solving. It treats the lift as a general way to weigh evidence: a set of cues is combined into one lifted point. That point's position gives the agreed answer, and its distance from the light cone measures how much the cues disagree.

**Lean** (`glm_lean/RequestProject/GLM/LorentzianEvidence.lean`): builds with no `sorry` and only the standard axioms. It is included in `AxiomAuditAll.lean`, which reports 10038 theorems on standard axioms only. The file proves, in any dimension:
- **Decomposition (`evidence_decomp`):** a weighted sum of lifted cues equals the lift of their consensus plus the Weyl vector times their disagreement (a weighted spread about the consensus).
- **Norm (`evid_norm`, `evid_null_iff`):** the Lorentzian norm of the evidence is exactly minus the disagreement, so it is null exactly when every cue agrees.
- **Guard (`dispersion_guard_sound`):** the dispersion guard is sound.
- **Analogy (`analogy_evidence`):** "a is to b as c is to ?" is evidence with weights \(1, -1, 1\).
- **Settling a tie (`separates_iff`, `card_ge_of_separates`):** a question that tells apart a Golay sextet tie needs at least five revealed positions, and the exact condition is given.

**Python:**
- New `reasoning/lorentzian_evidence.py`, exposed as a new `tool evidence`. It refuses examples that do not all state one relation.
- `tool lorentz` gains a certificate guard and a five-bit settling question, which you answer with `@POS=BIT`.
- New `tools lorentzian-evidence` measurement: 13 of 15 pre-declared marks met. The two missed marks are explained in the study.
- New test file `tests/test_lorentzian_evidence.py`. Its 9 tests pass when run by hand.

**Measured results** (all exact fractions):
- **Golay decoy:** the certificate guard cuts wrong answers from 61 to 27 and loses no right answer. The 27 that remain look identical to honest readings.
- **Settling question:** five bits resolve 600 of 600 tied readings (five random positions resolve 391).
- **Dispersion guard:** proved sound, but it never fired on this data.
- **Physics relations:** the guarded rule gives no wrong answers anywhere, but simple voting does better on one decoy set (155 right against 0).
- **Name analogies:** the existing analogy method got 10 of 13 names wrong. The new class certificate contains the expected name in 12 of 13.
- **Semantic relations:** gains are small (5.5% → 6.2% right per query).

So the clearest use for general reasoning is this: the lift can tell when a question is still open and name the smallest question that settles it, rather than having to guess.

**Documents:** the write-up is `studies/LORENTZIAN_EVIDENCE_STUDY.md`. STATUS, MASTER_PLAN, SYSTEM, WHITEBOARD, the academic paper (§20.55–20.56) and `tests/README.md` are updated and stamped 23 October 2026.

**Checks:** I re-took the stale stored measurements, including the two answer censuses. The figures did not change, except for counts that grew with the corpus. After `corpus --refresh`, `corpus --check` reports current. The test-file sign-off (`signoff --close`) is still owed because pytest cannot be installed here. All work is committed and pushed, and the Properties table lists the six proved theorems and three definitions.