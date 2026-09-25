# GLM Improvement Investigation and Prioritized Roadmap

**Audit date:** 24 September 2026  
**Repository baseline:** `DigitalEuan/GLM`, commit `7ba4f97`  
**Scope:** improve practical success, accuracy, coverage, derivation, and reliability without weakening the refusal contract.

## Executive conclusion

The GLM is already strong at **exact, closed-world computation over structured registers**. Its best evidence is not the size of the codebase but the combination of exact arithmetic, explicit refusals, machine-checked Lean statements, complete Golay correction census, and independent re-derivation of answered showcase probes. The current evaluation reports **177/177 cases passed**, including **149 correct answers and 28 expected refusals**, with no unexpected refusals, confident wrong answers, or errors. The benchmark suites report **2,389/2,390** tasks passed, and the exhaustive Golay suite covers every tested pattern rather than a sample. These are substantial results.

The principal limitation is not the geometric substrate. It is the **interface between open language and the typed operations the system already possesses**. The preregistered language probe scores **2 correct, 1 wrong, and 17 refused out of 20**, below its pass mark of 10 correct. An oracle decomposition shows why: approximately **4 questions are parser-limited, 10 are held by existing tables or functions but exposed by no query surface, and 4 are genuinely absent**. Adding vocabulary alone already failed as an intervention; widening the lexicon to 57 of the probe’s 69 content words moved the score by nothing. The next high-value investment is therefore a typed semantic parsing and planning layer that maps paraphrases into existing GLM operations, not another round of carrier or lexicon expansion.

A second limitation is that the current evaluation is highly successful but **closed-world**. It enumerates the runtime’s 24 query kinds and 65 report subjects, so it is excellent at regression detection but weak evidence for open-ended language competence. A future release should report two separate scores: the existing contract suite and a held-out, independently authored generalization suite. Otherwise, a perfect score can coexist with the language probe’s 2/20 result.

A third limitation is **derivation depth**. The blockers ledger classifies most measured gains as table lookup or geometric addressing; only two measured results are explicitly derived rather than retrieved. The system can verify dimensional equations and perform exact folds, but it rarely synthesizes a new answer from multiple facts under a typed plan. Improving this faculty should be the second major track after parsing.

## Current capability profile

| Area | Current evidence | Interpretation |
|---|---:|---|
| End-to-end runtime | 177/177 evaluation cases; 149 correct, 28 expected refusals | Excellent on the authored, closed query surface; not evidence of open-language coverage |
| Benchmark suites | 2,389/2,390 across five suites | Strong structured performance; one physics-equation case is a stated tensor-semantics boundary |
| Capability probes | 20 holds, 13 breaks, 0 surprises | The boundary map is internally consistent and unusually explicit |
| Exactness and safety | Integers, `Fraction`, no floats in core; 0 confident wrong answers in CLI evaluation | A major asset; must be preserved as new coverage is added |
| Natural-language probe | 2 correct, 1 wrong, 17 refused of 20 | The most important practical weakness |
| Query surface | 24 query kinds and 65 report subjects | Broad internally, but surface forms remain finite and hand-described |
| Structured knowledge | 8 registers, 1,143 carriers, 45 comparison classes | Useful foundation, but correctness is mostly checked against the registers themselves |
| Conversation | 8/15 follow-ups bound, 7/15 refused; 0/15 without memory | A valid initial episodic layer, limited to three follow-up shapes |
| Scale conversion | 7/12 declared questions answered; 6 of 7,750 numeric-scale pairs bridged | Safe and conservative, but intentionally narrow |
| Role binding | 6/12 declared bindings recovered by name; 424/1,143 carriers uniquely nameable | The algebraic reading is exact; the name-recovery fibre is the limitation |
| Program-text operation | 503/576 correct, 13 wrong, 60 refused at one reading | Unsafe without a second-reading guard; current guard trades coverage for zero wrong answers |
| Formal layer | 126 Lean files claimed by current documents, no `sorry` | Strong proof discipline; build reproducibility must be made routine |
| Data completeness | 1,257/1,652 chemistry cells measured; 210 remain explicitly unresolved after widening | Do not silently fill missing data; prioritize provenance and independent validation |

The exact structured core should be treated as the project’s competitive advantage. It provides a safe execution substrate for a higher-level planner because every answer can carry a typed operation, exact payload, provenance, and refusal reason. The improvement strategy should make more user questions reach that core without turning unsupported interpretations into answers.

## The highest-value bottlenecks

### 1. Typed semantic parsing is the primary bottleneck

The parser currently recognises a finite grammar with described shapes, start-only directives, named slots, and a few controlled paraphrases. This is well engineered for determinism, but it is not an open-language interface. The probe shows that most failures are not missing mathematical or chemical capability. They are failures to map ordinary wording to a known operation.

The best next component is a **typed intermediate representation (IR)** between text and the existing session API. It should represent at least:

- intent: describe, field, compare, ordering, extremum, derive, verify, report, task, or conversation follow-up;
- entities: register, row, field, quantity, unit, operation, relation, and conversation variable;
- constraints: expected type, scale, table, missingness policy, and allowed conversion;
- answer policy: answer, ask for clarification, or refuse with a typed reason;
- provenance: which tokens and grounding rules licensed each slot.

The parser should not directly generate an answer. It should generate one or more typed plans. The planner should reject plans whose types, scales, or fields do not line up, then execute only a plan licensed by the existing solver. This preserves the current refusal semantics while widening the language surface.

The existing lexicon admission machinery should be used as a grounding source, not treated as the parser itself. The previous vocabulary experiment is decisive: adding 54 words did not improve the probe score. The next experiment should therefore hold the registers constant and compare three parsers: current grammar, typed rule parser, and typed parser plus controlled paraphrase expansion.

**Pilot success criteria:** use the existing 20 canonical probe questions plus at least three independently written paraphrases per question. The pilot should reach at least **10/20 canonical correct**, at most **1/20 wrong**, and no confident wrong answer on the paraphrase set. Every answer must include the selected plan and the exact refusal reason when it declines. A parser that raises coverage but produces untyped guesses is a regression, not an improvement.

### 2. Compositional derivation is the second bottleneck

The system currently proves that it can derive in limited settings: it checks equations over recovered exponent vectors, composes some register values, folds declared columns, and handles exact conversions. However, the blockers ledger reports only **two measured derived results** in the relevant round. Most successful outputs remain retrieval or addressing of labels already present in a register.

The next derivation layer should be deliberately narrow. It should implement a **typed derivation planner** over existing operations rather than attempt general theorem proving. A plan could combine field reads, unit conversion, arithmetic, comparison, and a final rendering step. Examples include:

- derive molar mass from a chemical formula and element masses;
- derive a missing physical quantity when a declared law and enough operands are present;
- compute an extremum over a complete, converted, multi-table column;
- answer a follow-up that requires more than one turn’s result;
- produce a refusal when a derivation depends on a hole, an unlicensed conversion, or an underdetermined variable.

Every derivation should be represented as a small typed graph. The graph should distinguish **retrieved premises**, **converted premises**, **computed intermediates**, and **final claims**. This makes the current “reasoning” claim more precise and makes independent re-derivation straightforward.

**Pilot success criteria:** pre-register 30 derivation tasks, balanced among solvable, underdetermined, missing-data, wrong-unit, and wrong-law controls. Require at least **90% exact correctness on solvable tasks**, **0 confident wrong answers**, and a refusal reason that identifies the first unsatisfied precondition on every negative control. The derivation benchmark must include tasks whose answers are not present as named register entries.

### 3. Evaluation needs an independent generalization layer

The current 177-case evaluation is valuable because it is exhaustive over the runtime’s declared kinds and subjects. Its limitation is structural: the cases are generated from the same system tables and query surface that define the runtime. It cannot measure whether a new user phrase, an unseen composition, or a fact outside the registers is handled correctly.

Create three distinct evaluation sets:

1. **Contract regression set.** Keep the existing 177 cases unchanged. This protects known behavior and refusal boundaries.
2. **Held-out language set.** Author new questions without reusing the parser’s literal templates. Use paraphrases, indirect wording, reordered clauses, spelling variations, and multi-sentence context. Keep the answer key external to the runtime tables where possible.
3. **Adversarial safety set.** Include ambiguous names, cross-scale comparisons, missing fields, misleading near matches, underdetermined equations, and questions whose natural-language answer is not represented by the registers.

The held-out and adversarial sets should be versioned independently and evaluated in fresh interpreters. Their labels should not be generated by the same code path that produces answers. The release dashboard should report answer accuracy, unexpected refusal rate, confident-wrong rate, calibration of refusal reasons, and paraphrase stability separately.

A useful primary metric is **safe coverage**:

> safe coverage = correct answers / (correct answers + expected refusals + confident wrong answers), with confident wrong answers counted negatively in a secondary score.

Do not collapse correctness and coverage into one number. A model that answers twice as many questions by guessing is worse than the current system.

### 4. Independent data truth is missing for many claims

The current checks establish that the runtime is consistent with its registers. They do not establish that the registers are correct about the external world. The reasoning showcase states this limitation explicitly for dimensional records, migrated concept graphs, and Hamming assignments. This is scientifically honest, but it limits the meaning of “accuracy.”

Add a small **external-ground-truth validation layer** for facts that have authoritative definitions or stable reference values. Separate these from internal regression tests. Candidate domains are SI definitions, element identities and standard atomic weights, chemical formula parsing, and a small set of physics identities with semantic distinctions. Each record should carry source, retrieval date, unit, uncertainty or exactness status, and whether it is a definition, measurement, or derived value.

The validation should never overwrite the project’s exact register automatically. It should produce a discrepancy report. This allows the GLM to distinguish:

- internally consistent but externally unvalidated;
- externally supported and internally consistent;
- internally inconsistent;
- externally disputed or source-dependent.

This track improves trust more than adding another geometric register.

### 5. Conversation should become typed state, not surface-pattern accumulation

The current conversation layer is a good proof of concept: licensing beats naive recency on 3 of 10 control rows, and it binds 8 of 15 declared follow-ups while refusing 7. Its current limitation is that it recognises only three shapes: pronoun, subject substitution, and end-flip.

The next improvement should not be a fourth collection of regular expressions. It should store a **typed discourse state**: recent entities, query intent, answer set, selected fields, comparison scale, unresolved ambiguity, and refusal reason. Follow-ups such as “the one before that,” “both of them,” and “why?” can then be interpreted as operations over discourse state. A response should carry the antecedent candidates and the licensing result so that ambiguity is inspectable.

The most valuable conversation pilot is the tie-forward case. Instead of forcing one antecedent after a fourteen-row tie, the system can preserve a set-valued referent and route it to a set-capable operation such as `describe-many`, `field-of-each`, or `extremum-over-present`. This directly converts a current refusal into compositional derivation without weakening ambiguity handling.

**Success criteria:** pre-register at least 30 multi-turn dialogues, including distractor turns, tied answers, conflicting scales, clarification requests, and refusal carry-forward. Require zero confident wrong antecedents and explicit reasons for every unresolved reference.

### 6. Program-text geometry should remain a sandbox until semantics improve

The program-text experiment is interesting, but it demonstrates locality rather than understanding. One reading gets **503/576 correct with 13 wrong**, and the second-reading guard removes wrong answers at the cost of many refusals. The failure is expected because syntax-count vectors do not directly encode file identity or semantic role.

Do not promote this into the main reasoning path yet. First add a real program-text register with structured facts: module, definition name, imports, type signature, theorem dependencies, syntax tree features, and source span. Then compare lexical, structural, and dependency-based addressing against the current syntax-only geometry. The current geometry can remain one faculty in an ensemble, but it must not be allowed to make file-level claims without corroborating source metadata.

**Promotion criteria:** on a held-out set of definitions, require zero confident wrong file claims, an independently measured improvement over lexical search, and a refusal when structural and source-index evidence disagree.

## Recommended implementation sequence

| Priority | Work package | Why now | Exit gate |
|---|---|---|---|
| P0 | Reproducible release and evaluation hygiene | The repository’s documents instruct commands under `overlay/`, while the checked-out layout is flattened; tracked bytecode also conflicts with the stated ignore policy | One clean checkout runs the documented commands in a pinned environment; CI records exact toolchain and dependency versions |
| P1 | Typed semantic IR and planner | Directly attacks the 17/20 language-probe refusals without changing the substrate | ≥10/20 canonical probe correct, ≤1 wrong, zero confident wrong; paraphrase set reported separately |
| P2 | Held-out and adversarial evaluation | Prevents closed-world overfitting and makes improvements comparable | Independent labels, fresh-process execution, coverage/safety/calibration dashboard |
| P3 | Typed compositional derivation | Increases the scarce faculty: producing answers not stored as labels | 30 preregistered tasks, ≥90% solvable exact accuracy, zero confident wrong |
| P4 | Typed multi-turn state and set-valued references | Extends an already successful conversation mechanism into genuine composition | 30-dialogue suite, zero confident wrong antecedents, explicit ambiguity/refusal reasons |
| P5 | External-ground-truth validation | Separates register consistency from world accuracy | Discrepancy report for SI, chemistry, and selected physics facts; no silent overwrites |
| P6 | Program-text register | Converts an unsafe geometric experiment into a checkable source-navigation faculty | Held-out source-location accuracy with zero confident wrong claims |
| P7 | Sparse chemistry completion | Useful for coverage, but less valuable than parsing and derivation | Only add values with provenance and out-of-sample validation; preserve unresolved reasons |

P0 should be completed before P1 because the current repository is difficult to reproduce exactly. The documents describe an `overlay/` working directory, but the repository checkout used for this audit has the package at the root. The repository also contains tracked `__pycache__` and `.pyc` files even though the documentation says compiled files should remain untracked. Finally, the corpus check in this sandbox resolves an external `/opt/.manus/webdev/templates/...` path outside the repository and fails before evaluating the corpus. These are operational defects, not evidence of a GLM reasoning failure, but they make every future measurement less trustworthy.

## What should not be prioritized yet

The project should not respond to the language-probe failure by adding large numbers of vocabulary entries. That intervention was already measured and produced no score improvement. It should not expand the lattice dimension before demonstrating that current structured information cannot support the target operation. The 24-dimensional limit is a real substrate boundary, but most current user-facing misses occur earlier at parsing, plan selection, and missing query surfaces.

It should not treat a higher benchmark score on internally generated cases as sufficient evidence of success. The current system can obtain perfect scores on its closed evaluation while refusing most ordinary-language questions. New capabilities should therefore be judged against held-out language and adversarial safety sets, not only against generated cases.

It should not weaken ambiguity or missingness refusals to increase answer counts. The project’s strongest design property is that it distinguishes an answer from a plausible label. In particular, the Golay repair boundary, cross-scale ordering, holes in columns, ambiguous role-binding fibres, and set-valued conversation references should remain explicit refusal or set-valued outcomes unless a new theorem or declared data source licenses a stronger result.

## A concrete first round

The most defensible next round is **“typed question plans over the existing GLM surface.”** It should be small enough to finish and large enough to move the target.

First, freeze the current 20-question blocker probe and create a separate 60-question paraphrase set. Second, define a typed IR for intent, entities, fields, units, operations, and refusal policies. Third, implement a deterministic parser that emits candidate plans with provenance rather than answers. Fourth, execute candidates through the existing session operations, accepting only a uniquely licensed plan. Fifth, add a plan-level trace showing why each candidate was accepted or rejected. Sixth, re-run the original probe, paraphrases, current 177-case contract set, and adversarial safety cases.

The round should be considered successful only if it improves safe coverage while preserving the old contract set and eliminating confident wrong answers. Its primary figures should be: canonical probe correct/wrong/refused; held-out paraphrase correct/wrong/refused; number of parser candidates; number of plans rejected by type or scale checks; unexpected refusal rate; and confident-wrong rate. The study should explicitly classify each gained answer as **table**, **addressed**, or **derived**, because increased coverage alone is not the same as increased reasoning.

## Bottom line

The GLM does not need a larger mathematical substrate first. It needs a better **typed bridge from language to the substrate and its existing operations**, followed by a planner that composes those operations into new, checkable results. The recommended order is therefore:

1. make the repository and evaluation reproducible;
2. build typed semantic parsing and plan selection;
3. add independent held-out and adversarial evaluation;
4. expand compositional derivation;
5. extend conversation into typed, set-valued state;
6. validate register facts against external ground truth;
7. only then promote program-text and sparse-data expansions.

This route is the most likely to improve **success and coverage without sacrificing accuracy**, because it attacks the measured bottleneck, preserves the refusal contract, and makes every new answer traceable to a licensed operation rather than to a more permissive guess.

## References

[1]: https://github.com/DigitalEuan/GLM/blob/main/STATUS.md "GLM current status and measured release table"

[2]: https://github.com/DigitalEuan/GLM/blob/main/CAPABILITY_ASSESSMENT.md "GLM measured capability assessment"

[3]: https://github.com/DigitalEuan/GLM/blob/main/studies/BLOCKERS_STUDY.md "GLM blocker study and preregistered language probe"

[4]: https://github.com/DigitalEuan/GLM/blob/main/studies/PROBE_ORACLE_STUDY.md "GLM probe oracle and coverage decomposition"

[5]: https://github.com/DigitalEuan/GLM/blob/main/studies/OPERATION_ESCALATION_STUDY.md "GLM operation escalation study"

[6]: https://github.com/DigitalEuan/GLM/blob/main/studies/SECOND_READING_STUDY.md "GLM second-reading safety study"

[7]: https://github.com/DigitalEuan/GLM/blob/main/studies/CONVERSATION_STUDY.md "GLM conversation and licensing study"

[8]: https://github.com/DigitalEuan/GLM/blob/main/studies/SCALE_CONVERSION_STUDY.md "GLM scale conversion study"

[9]: https://github.com/DigitalEuan/GLM/blob/main/studies/SUPPLIED_PORTS_STUDY.md "GLM supplied ports, role binding, and plan store study"

[10]: https://github.com/DigitalEuan/GLM/blob/main/PROJECT_DIRECTIVES.md "GLM project positioning and standing directives"

[11]: https://github.com/DigitalEuan/GLM/blob/main/MASTER_PLAN.md "GLM master plan and phase history"
