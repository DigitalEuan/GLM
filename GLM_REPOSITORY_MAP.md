# GLM Repository Map

*Last altered 30 October 2026 (reorganisation: src/ layout, YAML pairs, 19 directives, 427 Lean files).*

## Layout

```
GLM/
├── README.md, ENTRY.md, SYSTEM.md, STATUS.md, ITERATE.md,    (state documents)
│   PROJECT_DIRECTIVES.md (19 directives), MASTER_PLAN.md,
│   DIGEST.md, FIGURES.md, WHITEBOARD.md, LICENSE,
│   REASONING_CAPABILITY.md, CAPABILITY_ASSESSMENT.md,
│   GLM_REPOSITORY_MAP.md (this file)
│
├── lakefile.toml                    (srcDir = "src/lean")
├── lean-toolchain, lake-manifest.json
├── conftest.py                      (adds src/ to sys.path)
├── .gitignore, .glm_*.json
│
├── src/                             (all executable code)
│   ├── GLM.py                       (the CLI)
│   ├── glm_universal/               (the Python package)
│   │   ├── constants.py             (single source of truth for fundamentals)
│   │   ├── figures.py, integrity.py
│   │   ├── corpus/                  (document-as-data engine)
│   │   │   ├── study_ledger.py      (the study graph, 153 edges, acyclic)
│   │   │   ├── yaml.py              (YAML schema registry, 5 schemas)
│   │   │   ├── checks.py            (4 YAML gate checks + tier-0 contract)
│   │   │   └── ...
│   │   ├── knowledge/               (corpus query surface + studies)
│   │   │   ├── answer.py            (7 readings: define/context/similar/...)
│   │   │   ├── ask.py               (request grammar + dispatch)
│   │   │   ├── glossary.py          (27 held-out glossary entries)
│   │   │   ├── friction.py          (hold-out model, 4 predictors, 2 readers)
│   │   │   ├── friction_two.py      (worn contact, noise-set reader)
│   │   │   ├── model.py, reader.py  (corpus model, 210K sentences, 3.7M tokens)
│   │   │   └── ...
│   │   ├── reasoning/               (substrate-native reasoning)
│   │   │   ├── wobble_registry.py   (D17: wobble sources)
│   │   │   ├── reversibility.py     (D18: reversibility ledger)
│   │   │   ├── generate_not_store.py (D19: generate-don't-store)
│   │   │   ├── ast_index.py         (structural expression index)
│   │   │   └── ...
│   │   ├── wheels/                  (15 wheels, centralized)
│   │   │   ├── w11.py-w15.py        (5 domain wheels)
│   │   │   └── junctions/           (phase66 + domain + oscillator)
│   │   ├── engineering/             (10 formula wheels + domains + oscillator)
│   │   ├── runtime/                 (session, parser, router, evidence)
│   │   ├── sandbox/                 (attention_simulator, aggregation_bench)
│   │   ├── tests/                   (5,915 tests)
│   │   └── ...
│   └── lean/                        (427 Lean files, 0 sorry)
│       └── RequestProject/GLM/
│           ├── AxiomAuditAll.lean   (whole-development axiom audit)
│           ├── LeechShellCount.lean (every Leech shell, proved)
│           ├── Rule30/              (156 Rule 30 study files)
│           ├── HypothesisEngine/    (10 hypothesis engine files)
│           ├── Escalation/          (6 escalation submodules)
│           └── ...
│
├── studies/                         (194 .md + 191 .yaml = 385 study files)
│   ├── _schema/study.schema.yaml    (glm-study-manifest/v1)
│   ├── _lean_files_needed.md        (registry of missing Lean files)
│   ├── ATTENTION_SIMULATOR_STUDY.md (+ .yaml)  (absorbed from source_material)
│   ├── AGGREGATION_BENCH_STUDY.md   (+ .yaml)  (absorbed from source_material)
│   └── ... (189 more studies, each a .md + .yaml pair)
│
├── source_material/                 (owner-supplied, kept as supplied)
│   ├── source_material/Rule30_GLM_Study/            (the Rule 30 study)
│   ├── source_material/arc_agi_17/                  (ARC AGI evaluation)
│   ├── attention/                   (attention simulator code)
│   ├── GLM_Pipeline_Kit/            (10 Lean files, already absorbed)
│   └── ...
│
└── archive/                         (records of earlier rounds)
    ├── ARISTOTLE_SUMMARY.md
    └── ...

```

## Key figures

| figure | value |
| --- | --- |
| Lean files | 427 |
| Python modules | 218+ |
| Studies (.md) | 194 |
| Study YAML manifests | 191 |
| Test files | 217 |
| Tests collected | 5,915 |
| Directives | 19 (D1-D19) |
| Wheels | 15 (W01-W15) |
| Corpus sentences | 210,591 |
| Corpus tokens | 3,756,126 |
| Predecessor edges | 153 (acyclic) |
