# Study Session: an evidence-aware Data Object method

**Session status:** current synthesis and reusable working method  
**Companion program:** `data_object_workbench.py`  
**Scope:** chemical elements, geometry, language, and other subject domains

## 1. Quick orientation

The most developed system in this repository is not a claim that a 24-bit Golay word *contains all facts* about a subject. It is a layered Data Object:

1. **Canonical identity** says what the subject is.
2. **Typed claims** say what is known, reported, measured, calculated, or missing.
3. **Evidence metadata** records units, scale, conditions, uncertainty, status, and provenance.
4. **State and relations** distinguish the subject from a particular condition, interaction, or event.
5. **Integrity and spatial views** may add Gray, Golay, MOG, or exact 24-dimensional addresses without replacing the underlying facts.
6. **Audits and held-out studies** test whether a representation is internally correct and whether it has empirical value. These are different questions.

This is the closest alignment with reality currently supported by the work: preserve distinctions made by the source, make uncertainty and absence visible, avoid lossy packing, and test any proposed geometric meaning against unseen data and ordinary controls.

The reusable script applies this architecture to CSV, JSON, or JSONL records. A small study manifest maps source fields to identities and claims. The script emits deterministic JSONL objects and an audit report. Optional Golay/MOG views are deliberately labelled as integrity or indexing views, not physical laws.

## 2. The central model

A Data Object is best understood as a **versioned evidence graph node**, not a flat feature vector.

### 2.1 Identity

A canonical identifier should be stable, unique within a namespace, and based on the domain's actual identity rule:

- element: atomic number (with isotope/ion/state kept separate);
- geometric figure definition: a controlled definition identifier;
- lexical item: language + lemma + sense identifier, not merely spelling;
- text occurrence: document + span identifier;
- interaction: a separate event identifier linked to all participants.

A hash detects accidental changes to a declared payload. It does not prove that the identifier corresponds to reality.

### 2.2 Claims rather than naked values

Every value is wrapped as a claim with:

- `predicate`: the meaning of the value;
- `value` and `value_type`;
- `unit` or a non-physical `scale` where applicable;
- `conditions`;
- `uncertainty`;
- epistemic `status` such as measured, calculated, derived, reported, or missing;
- `provenance`, including source identity and record locator;
- exact `source_value_text` for audit and round-trip inspection.

Unknown is represented by null plus an explicit missing status. It is never silently replaced by zero. A rational string can remain exact until a declared conversion is needed.

### 2.3 State, relation, and event boundaries

An element is not the same object as an isotope, ion, excited state, material sample, molecule, or reaction event. A word sense is not the same object as a spelling, token occurrence, translation, speaker intent, or conversation. A geometric definition is not the same object as one drawing or one measured specimen.

The method therefore keeps:

- **state** for the declared state of this object;
- **relations** for typed, directed links;
- **separate event objects** for interactions, transformations, observations, or utterances when those have their own participants and conditions.

This boundary prevents facts measured in one context from being attached universally to the subject.

### 2.4 Representations and views

Gray code, Golay code, MOG cells, Leech coordinates, a plot, an embedding, and a feature vector are representations of information. They are not automatically new information.

A representation must declare:

- its input and transform;
- coordinate convention and version;
- whether it is lossless, error-protecting, indexing, or visual;
- an inverse or reconstruction rule if one exists;
- dimensionality and known information loss;
- the permitted interpretation.

The companion script includes two optional views:

- a bounded integer identity can become 12 little-endian bits, optionally through reflected Gray code, then a systematic extended binary Golay `[24,12,8]` word in the project's fixed 4×6 MOG;
- up to 24 typed claims can be **referenced** from MOG cells. Values remain in the claim records, so a measurement is not quantized into one bit and its unit is not lost.

## 3. Current system information

### 3.1 Exact discrete core

The repository has established and tested:

- unique element identities and round trips;
- reflected Gray adjacency for consecutive atomic numbers at the message layer;
- systematic extended Golay encoding and the expected codeword properties;
- a fixed 4×6 MOG coordinate permutation;
- three disjoint adjacent-column-pair Golay octads that partition all 24 coordinates;
- exact Leech minimal-vector inventories in shape classes A, B, and C;
- explicit symmetric pair operators and exact interaction identities;
- a typed 118-element object collection with nine MOG layers.

These are mathematical or software-integrity results. They establish that the encodings are coherent, not that they are privileged chemistry.

### 3.2 Data architecture reached for elements

The most developed element object separates:

- atomic-number identity;
- Gray/Golay integrity representation;
- neutral ground-state electronic occupancy;
- typed observed channels;
- exact Leech addresses;
- explicit MOG display layers;
- a boundary excluding isotope, ion, excited-state, phase-sample, molecule, and event objects.

A later KB companion table improved metrological honesty by retaining exact strings and making unit, condition, uncertainty, source, and status explicit. Where the source lacks metadata, the fields say so rather than inventing it.

### 3.3 Geometry status

The MOG is an exact 4×6 arrangement of 24 coordinates. The Leech lattice is genuinely 24-dimensional. A declared rank-three projection was audited and showed severe local information loss on the fixed address set:

- mean relative distance error about 65.31%;
- maximum relative distance error 100%;
- directed nearest-neighbour recall about 8.88%;
- 15 projected-point collisions.

Therefore exact calculations stay in the exact space. Three-dimensional forms are views with declared projection and distortion, not replacements for 24-dimensional geometry. Typed physical channels may control colour, size, or panels in a visualization, but are not silently promoted to geometric axes.

### 3.4 Empirical status

Across the completed studies, fixed Golay/MOG/Leech arrangements have not demonstrated a universal predictive advantage over ordinary baselines or matched random layouts.

Key examples:

- For seven held-out atomic-property endpoints, the cubic atomic-number baseline had the best overall normalized held-out error.
- Gray coding provided exact input locality, but did not improve those predictions.
- Searching 129 MOG layouts using training data did not produce reusable held-out geometric advantage for tested pair relationships.
- Exact A/B/C Leech address spaces were coherent, but fixed addresses behaved similarly to random-address controls in relationship tests.
- On 52 neutral gas-phase diatomic dissociation records, fixed Class A slightly improved over raw properties but remained inside the random-Class-A range; other fixed classes did not improve the baseline.
- The operational UBP MOG/Hexacode descriptor was worse than raw measured properties on that endpoint and remained within the random-layout range.
- A Y-twin representation was information-redundant by construction and did not improve the KB interaction result.

The safe conclusion is constructive: the geometry is a reproducible hypothesis space and indexing system, while physical meaning must be earned by prospective or leakage-safe held-out performance.

## 4. Studies completed and what not to repeat blindly

### Study A — first periodic-table benchmark

**Question:** Do fixed MOG and 3D arrangements improve prediction of atomic properties?  
**Design:** seven endpoints; leave-period-out and leave-group-out tests; atomic-number, message-bit, Golay-bit, fixed geometry, random layout, and shuffled-target controls.  
**Result:** no universal optimal MOG geometry; atomic-number polynomial was best overall.  
**Do not repeat unchanged:** another broad arrangement sweep on the same targets without a new preregistered hypothesis or new external data.

### Study B — Gray identity and exact addresses

**Question:** Can consecutive element identities be made local while retaining error protection and typed observations?  
**Result:** yes at the 12-bit Gray-message layer; Golay intentionally expands adjacent distance. Twenty-four fixed Leech addresses were distinct, equal-norm, and full rank.  
**Lesson:** measure locality at the layer where it is claimed. Do not confuse error-code distance with semantic distance.

### Study C — spatial transitions and selected layouts

**Question:** Do blast radius, traversal time, pair proximity, or training-selected MOG layouts reveal reusable structure?  
**Result:** the tested re-encoding operation gave burst sizes 8 or 12, not the proposed `7–11 / 7 / 1 / 1`; Gray traversal gave a deterministic one-bit message clock; selected MOG layouts stayed near chance on tested relationships.  
**Lesson:** define the update operation and clock before measuring. Traversal properties inherited from construction are not independent physical discoveries.

### Study D — complete Leech minimal-vector classes

**Question:** Do exact Classes A, B, and C provide privileged addresses for measured channels?  
**Result:** exact inventory and norms were validated, but fixed-address relationship performance did not beat raw measurements and resembled random controls.  
**Lesson:** a rich symmetry space is valid mathematics but does not choose a domain mapping by itself.

### Study E — genuine interaction endpoint

**Question:** Do fixed class-based pair operators predict neutral gas-phase diatomic dissociation energy under complete-element holdout?  
**Result:** fixed Class A was competitive but inside the random control range; B, C, and combined classes did not establish an advantage.  
**Lesson:** interaction objects need species, participants, charge, electronic state, phase, temperature convention, uncertainty, and provenance. Complete participant holdout is essential.

### Study F — UBP ontology operationalization

**Question:** Do TAX/NRCI, fixed MOG, Hexacode, and XOR trajectory improve the same interaction endpoint?  
**Result:** Hexacode validity followed from codeword construction and was not selective. On binary states, TAX reduced to Hamming weight times a constant and NRCI was monotone in weight. All 118 identities passed the proposed 0.500 horizon. Predictive results did not establish fixed-layout value.  
**Lesson:** derive algebraic dependencies before treating scores as independent dimensions.

### Study G — KB and fundamental-first audit

**Question:** Can the supplied KB tensor and formula tables be used as evidence-ready data?  
**Result:** five element channels aligned safely, but units, conditions, uncertainty, and per-value provenance were absent. Several positional categories had schema-length mismatches and were refused. Particle formula agreements were reproduction, not held-out prediction.  
**Lesson:** decode positional arrays only when every observed length equals the declared parameter count. Never infer shifted labels after a mismatch.

### Study H — typed KB, octads, and 3D projection

**Question:** Can the five safe channels be made operational and the geometry boundaries made explicit?  
**Result:** a 590-row typed companion retained exact values and exposed unresolved metadata; three exact octad zones were published; the 24→3 view was found too lossy for computational replacement; a future particle protocol was frozen as protocol-only.  
**Lesson:** do not relabel already inspected data as prospective. Freeze the rule before target access.

## 5. The reusable study workflow

### Phase 0 — formulate the claim

Write one sentence naming:

- subject type;
- target claim or endpoint;
- conditions and population;
- what would count as success;
- what is merely a view or hypothesis.

If this cannot be stated, do not encode yet.

### Phase 1 — freeze ontology and boundaries

1. Choose a canonical identity and namespace.
2. Decide which states require separate objects.
3. Decide which interactions require event objects.
4. Define typed relation predicates and direction.
5. Version this decision before feature experiments.

### Phase 2 — acquire and preserve sources

1. Save immutable source snapshots when permitted.
2. Record citation, retrieval date, record locator, and license field.
3. Keep source tokens unchanged.
4. Never merge disagreeing sources silently. Store separate claims with separate provenance.
5. Use explicit null for absence; reserve zero for a real zero.

### Phase 3 — map claims

For each field, declare:

- predicate;
- source field;
- value type;
- unit or scale;
- conditions;
- uncertainty;
- status;
- provenance mapping;
- declared missing tokens.

A field with unknown unit can still be retained, but must be marked unresolved and excluded from incompatible calculations.

### Phase 4 — build base objects before geometry

Generate identity, claims, state, relations, and boundary first. Audit uniqueness, type parsing, missingness, and provenance. This base object is the truth-preserving layer.

### Phase 5 — add representations without overwriting facts

Add Gray/Golay/MOG only when there is a declared reason:

- integrity/error separation;
- fixed indexing;
- controlled visualization;
- a preregistered empirical hypothesis.

Keep transform versions. Preserve the base claim and use references from cells. For an embedding, publish its complete transform and distortion audit.

### Phase 6 — validate at four distinct levels

1. **Structural:** schema, types, unique IDs, missingness.
2. **Exact mathematical:** round trips, permutations, code properties, invariants.
3. **Source fidelity:** sampled or full comparisons to source records and citations.
4. **Empirical:** held-out prediction with baselines and controls.

Passing one level does not imply another.

### Phase 7 — lock empirical tests

Before evaluation:

- freeze data splits and target manifest;
- hold out complete subjects or participant families when leakage can cross records;
- fit preprocessing only on training data;
- include simple domain baselines, raw-feature baselines, random-layout controls, and negative controls;
- perform model/layout selection only inside training data;
- report all predeclared endpoints, uncertainty, and failures;
- label exploratory reuse honestly.

### Phase 8 — version and promote

Promote a change only if it improves at least one declared property without damaging source fidelity. Version separately:

- ontology/schema;
- source snapshot;
- mapping manifest;
- representation transform;
- experiment protocol;
- generated objects and audit.

## 6. Using `data_object_workbench.py`

The script is standard-library-only and intentionally generic.

### 6.1 Create an example

```bash
python3 data_object_workbench.py init examples/geometry_study
python3 data_object_workbench.py build examples/geometry_study/study.json
python3 data_object_workbench.py audit examples/geometry_study/objects.jsonl
```

The generated `study.json` is the main configuration. It maps input fields into a canonical identity and typed claims. Copy it rather than editing the Python core for each subject.

### 6.2 Input formats

Supported input:

- CSV with headers;
- JSON containing an array of objects;
- JSONL/NDJSON containing one object per line.

Nested JSON fields can be addressed using dotted paths such as `source.record_id`.

### 6.3 Minimal manifest pattern

```json
{
  "study_id": "language-senses-v1",
  "schema_version": 1,
  "object_type": "lexical_sense",
  "input": {"path": "senses.csv", "format": "csv"},
  "output": "sense_objects.jsonl",
  "missing_tokens": ["", "NA", "null"],
  "identity": {
    "namespace": "sense",
    "field": "sense_id",
    "label_field": "lemma"
  },
  "claims": [
    {
      "predicate": "definition",
      "field": "definition",
      "value_type": "string",
      "status": "reported",
      "source_id_field": "dictionary_id",
      "record_locator_field": "entry_url"
    }
  ]
}
```

Language should normally identify senses rather than treating one spelling as one universal object. Add language, register, attestation, speaker/context, and translation as typed claims or linked objects according to the study question.

### 6.4 Claim mapping keys

Each claim mapping requires `predicate` and normally `field`. It may declare:

- `value_type`: `string`, `integer`, `number`, `boolean`, `json`, or `rational_string`;
- literal `unit`, `scale`, `conditions`, `uncertainty`, `status`, and provenance values;
- or field-backed variants such as `unit_field`, `conditions_field`, `status_field`, `source_id_field`, `record_locator_field`, `citation_field`, `retrieved_at_field`, and `license_field`;
- per-claim `missing_tokens`.

If both a literal and field-backed form are possible, the field-backed form is used when configured.

### 6.5 Optional MOG views

```json
"views": {
  "golay_mog_identity": {"integer_field": "numeric_id", "gray": true},
  "claim_mog_index": true
}
```

The integer must fit in 12 bits. The claim index supports up to 24 claims; larger systems should use several explicitly named semantic layers rather than silently truncating or forcing an unrelated positional tensor into 24 cells.

### 6.6 Audit interpretation

The audit checks identity hashes, uniqueness, status/value consistency, provenance presence, and exact coordinate coverage of optional MOG views. Warnings such as a missing source identifier do not rewrite data. Errors produce a nonzero exit status.

A clean audit means **structurally valid under the manifest**. It does not mean every source statement is true, every unit is comparable, or the geometry predicts an external endpoint.

## 7. Domain adaptations

### 7.1 Geometry

Separate:

- abstract definition;
- theorem/proof claim;
- parameterized instance;
- coordinate realization and frame;
- measured physical specimen;
- transformation event.

Exact quantities can use rational strings or symbolic source text. Approximate measurements need units and uncertainty. Coordinate embeddings should specify frame, orientation, scale, handedness, and invariance requirements.

A MOG layer could index up to 24 named features or constraints, but Euclidean meaning should come from the geometric definition—not from MOG cell proximity unless separately tested.

### 7.2 Language

Separate:

- orthographic form;
- lemma;
- lexical sense;
- token occurrence;
- utterance/event;
- speaker and context;
- translation relation.

Language is relational and contextual. Frequency requires corpus, date range, sampling, tokenization, and normalization. Meaning labels require annotator/source and uncertainty or disagreement where available. Embeddings are lossy learned views and should retain model/version and evaluation context.

### 7.3 Chemistry and materials

Retain the element architecture, but create distinct linked objects for isotope, ion, electronic state, phase/sample, molecule, and reaction. Every interaction endpoint needs participant roles, stoichiometry, charge, state, conditions, uncertainty, and provenance. Do not infer molecule behaviour solely from an element identity XOR or distance.

## 8. Decision rules for future development

Adopt these as non-negotiable gates:

1. **No hidden coercion:** type conversions must be declared.
2. **No unknown-as-zero:** null and status carry missingness.
3. **No geometry-as-fact:** a representation is labelled as a view until externally supported.
4. **No positional decoding after mismatch:** lengths must agree exactly with the declared schema.
5. **No source collapse:** disagreements remain separate evidence claims.
6. **No test-set tuning:** select transforms and parameters inside training data only.
7. **No retroactive prospectivity:** inspected targets remain exploratory/in-sample.
8. **No 3D replacement of exact 24D work:** publish projection and distortion.
9. **No universal subject object:** state and event boundaries are domain-specific and explicit.
10. **No success by complexity alone:** compare against simple and random controls.

## 9. Recommended next studies

The reusable workbench should now be exercised on two deliberately different subjects:

### Geometry pilot

Build 50–200 objects containing definitions, exact invariants, parameterized coordinate instances, and known equivalence relations. Test round trips and transformation invariance. Use a MOG claim index only as navigation. If proposing a spatial arrangement, predict a withheld relation not used to create it.

### Language pilot

Build sense-level objects from one well-provenanced lexicon plus attested token events from one declared corpus. Preserve language, sense, register, source, time, and context. Compare any Golay/MOG or spatial view against ordinary sparse and embedding baselines under lemma-family or document holdout.

### Cross-domain refinement

After both pilots, change the common script only for abstractions genuinely shared by chemistry, geometry, and language. Keep domain ontologies in manifests or separate adapters. This avoids forcing every subject into the element schema while retaining one versioned construction and audit engine.

## 10. Session conclusion

The strongest current method is conservative in the useful sense: it stores more context, discards less information, marks what is unknown, and prevents mathematical encoding from masquerading as empirical discovery. Golay/MOG remains valuable for exact integrity, indexing, controlled arrangements, and hypothesis generation. Its role in predicting elemental, geometric, or linguistic behaviour must be demonstrated separately with locked data and matched controls.

Use the companion script as the stable core, manifests as versioned domain mappings, and separate experiment programs for endpoint-specific tests. This gives one evolving Data Object system without turning one subject's ontology into every subject's ontology.
