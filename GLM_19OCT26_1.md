# Next GLM Development Plan

## Overall direction

The next development work should extend the GLM from a system that mainly detects friction and refuses unsafe readings into a system that can use measured friction as a signal for recovery.

The previous Friction studies established that:

- recursive two-token valleys can dominate continuation;
- full contact weighting can dilute a strong local signal;
- wear does not remove a valley that is carved by the continuation row itself;
- margins can remove flip-flops but can also suppress informative changes;
- typo recovery can be improved safely when spelling is given priority over corpus use;
- rare technical vocabulary can remain invisible to a corpus-only respeller.

The next stage should turn those observations into active mechanisms while also strengthening the wider reasoning architecture.

## Part I — Thermomechanical Friction extension

The Friction method should now be extended through a thermomechanical model. The mechanical analogy is:

- **Heat:** local uncertainty, score concentration, score variance, recursive dominance, and disagreement between prompt and generated context.
- **Actuation:** a controlled change to the machine’s tolerance, weighting, or vocabulary boundary.
- **Thermal expansion:** forcing a continuation out of a recursive valley.
- **Thermoelectric generation:** using a prompt/generated-context gradient to recover lost signal.
- **Sintering:** temporarily opening a restricted register vocabulary when corpus friction blocks a valid technical term.

The analogy should be used to design measurable mechanisms, not as a claim that the GLM has literal thermodynamic energy.

### Experiment A — Bimetallic strip / thermal expansion governor

Target the self-made valley created by the two-token row.

Measure the thermal state of the current continuation row using an exact concentration measure, such as the top candidate’s score relative to the top five candidates. Combine this with detection of repeated bigrams in the most recent generated tokens.

When the row becomes sufficiently “hot,” dynamically increase a taboo penalty for continuations that repeat recent generated bigrams. The purpose is to create a controlled escape from recursive phrases such as “the same way.” When the row is “cold”—low dominance or high ambiguity—the mechanism should leave the ordinary continuation unchanged.

Compare:

- the standard two-token continuation;
- the existing contact continuation;
- the static-taboo control;
- the thermally actuated governor.

Measure:

- reduction in the most frequent recursive continuation;
- held-out overlap with the correct text;
- precision and coverage;
- number and quality of distinct continuations;
- whether the mechanism terminates or refuses cleanly when no safe continuation remains.

The key question is whether the governor reduces recursive dominance without simply replacing a repetitive but correct answer with a diverse but incorrect one.

### Experiment B — Thermoelectric prompt-anchor recovery

Target signal dilution and the accuracy cost of the stick-slip margin.

Treat the original prompt as the cold side and the generated context as the hot side. Measure the thermal gradient as the difference between their folder or directory evidence. Possible exact measures include the variance, range, or score difference between prompt words and generated words.

When the gradient is high, the generated context may be running on its own “exhaust.” Use that signal to activate a temporary prompt-anchor override that gives the original prompt greater weight for the next reading. When the gradient is low, keep the normal reader active.

Compare:

- the frictionless reader;
- the fixed one-quarter margin reader;
- the noise-sensitive reader;
- the thermoelectric prompt-anchor reader.

Measure:

- final directory accuracy in high-gradient cases;
- whether the override reduces noise-induced switches and returns;
- whether it preserves informative changes of mind;
- whether it remains inactive when prompt and generated evidence agree;
- whether a mismatched or shuffled generated context produces the expected weaker result.

The key question is whether a thermal gradient can distinguish signal dilution from a legitimate change in subject.

### Experiment C — Friction sintering / register-vocabulary phase transition

Target vocabulary blind spots such as `millisecond`, where a technically valid word is too rare in the corpus to be recognized by the normal respeller.

Keep the existing corpus-based respeller as the solid state. When it refuses and the token has the shape of a valid technical word or unit, allow a bounded fallback to a curated register lexicon. The fallback should be treated as a temporary liquid state: it consults the register vocabulary, selects a structural match, and then returns to the normal state.

The register lexicon should contain domain-specific carrier names, structural words, and units that the parser or registers require but the corpus barely uses.

Measure:

- recovery of unknown but structurally valid technical words;
- preservation of ordinary misspelling behavior such as `waht`;
- whether the mechanism changes already successful answers;
- whether register terms and units are recovered without broadening correction recklessly.

Hexadecimal literals, arbitrary identifiers, formulas, and code-like strings should remain a separate protected class rather than being treated as ordinary misspellings. The sintering mechanism should be aimed at valid technical vocabulary, not arbitrary low-frequency tokens.

### Thermomechanical study results

The three experiments should be assessed independently. The study should make clear:

- which friction signals are useful sensors;
- whether the thermal governor actually escapes recursive valleys;
- whether prompt anchoring recovers signal without suppressing information;
- whether register sintering fills vocabulary gaps safely;
- which mechanisms should be adopted and which should remain experimental;
- what each unsuccessful mechanism teaches about the structure of the GLM.

## Part II — Broader development priorities

### 1. Create a unified evidence and result model

Bring the planner, corpus, domain, lattice, certificate, and conversation systems toward a common result representation.

A result should be able to expose:

- the answer or candidate set;
- the type of evidence used;
- the source data and witness;
- the formal theorem or checker involved;
- the confidence or certification boundary;
- the budget used;
- any ambiguity or unresolved tie;
- the refusal reason;
- the conversation or reply history;
- whether the result was independently replayed.

This would make the distinctions already present in the studies visible throughout the system rather than only in individual reports.

### 2. Close the remaining carried-value gaps

The planner ladder now checks computed values and the carried-read work makes many register values machine-readable, but some values remain carried rather than independently reconstructed.

Extend the machine vocabulary to cover:

- rank;
- median;
- quartiles;
- top and k-th largest values;
- bounded folds;
- tool answers;
- verdict-dependent steps;
- exact position-specific reads from questions.

The goal is to reduce the amount of the planner that is trusted as data and increase the amount that is recomputed or read through an independent machine path.

### 3. Add contextual domain frames

The domain-wheel work showed that individually valid formulas can overgenerate when junctions are globally combined. The next development should let the question specify context such as:

- which object is being measured;
- which body drives a wave;
- whether an oscillator is coupled to a rotating body;
- whether energy is stored or delivered;
- which physical interpretation of a shared name is intended.

This should allow the solver to recover useful relationships without globally identifying quantities that are only conditionally related.

### 4. Develop an explicit corpus confidence curve

The corpus can predict local text and expose word use, but its guarded predictor currently faces a precision/coverage trade-off and its definition readings are not reliably graded.

Develop declared operating modes such as:

- a high-confidence, low-coverage mode;
- a balanced mode;
- a high-coverage candidate mode.

For definitions, return witnessed text together with a quality description rather than treating every pattern match as a definition. Continue testing context ranking against held-out glosses and first-mention controls.

The corpus should remain evidence for retrieval, explanation, and candidate generation rather than an unqualified source of truth.

### 5. Expand adversarial interactive testing

The nearest-question work successfully keeps replies inside the measured ranking head. Extend this approach to more realistic conversations:

- false replies at every turn;
- contradictory replies;
- unanswered questions;
- stale replies to an earlier turn;
- intended carriers outside the candidate head;
- ambiguous or malformed replies;
- users who choose a response that is semantically close to more than one option.

The central principle should remain that dialogue may resolve uncertainty inside an evidence-backed candidate set, but should not promote a candidate that the underlying measurement excluded.

### 6. Create a machine-readable study ledger

The number of studies is now large enough to justify a structured research index. The ledger should connect:

- phase and study name;
- predecessor and related studies;
- preregistration date;
- measurement date;
- stored-data digest;
- code digest;
- marks passed and missed;
- amendments;
- frozen-path effects;
- current status;
- open follow-up questions.

This would keep the academic paper, status documents, reports, tests, and implementation modules aligned as the project grows.

### 7. Separate corpus source tiers more clearly

Repeat important corpus experiments with source tiers reported separately, for example:

- core system documentation;
- implementation code and comments;
- formal Lean material;
- studies and generated reports;
- archived or supplied material.

This will show whether a result comes from the underlying system and source material or mainly from the project’s own explanatory prose and repeated reports.

## Overall intended outcome

The next development stage should move GLM toward a more coherent evidence-sensitive reasoning system.

The thermomechanical Friction work should make failure signals actionable. The broader work should make the resulting actions explainable, provenance-aware, context-sensitive, and safe under ambiguity.

The desired outcome is not that every experiment passes. The desired outcome is a clear map of:

- where friction indicates a recoverable failure;
- where friction indicates genuine uncertainty;
- which recovery actions improve correctness;
- which actions merely increase diversity or coverage;
- which domain relationships require context;
- which corpus readings are useful evidence;
- which values still need independent computation;
- and where the system should continue to refuse.
