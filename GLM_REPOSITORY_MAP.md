# GLM Repository Map

## Tier 0 — the coarse read

**Question.** Where is everything in this repository, and which folder does each kind of file belong in?

**Verdict.** The executable code is under `src/` (the package, the CLI and the Lean development), the studies are under `studies/` as Markdown with a YAML manifest each, the owner's supplied material is under `source_material/` in `ToDo/` and `done/`, and the state documents are at the root.

**Deciding figure.** Four top-level folders of content — `src/`, `studies/`, `source_material/`, `archive/` — plus `scripts/` for the two owner-run checks.

**Recomputed by.** (hand-written argument; nothing to recompute)

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Last altered 31 October 2026 (repository check: tier-0 block; 22 directives; `source_material/` in `ToDo/` and `done/` with the intake ledger; the one wheels folder, the new wheels in it marked provisional until the Lean build (earlier the same day staged in their intake items); `src/lean/awaiting_recovery/`; `scripts/`). Earlier: 30 October 2026 (reorganisation: src/ layout, YAML pairs).*

The executable code is under `src/` (the package, the CLI and the Lean development), the
studies are under `studies/` as Markdown with a YAML manifest each, the owner's supplied
material is under `source_material/` in `ToDo/` and `done/`, and the state documents are at the
root. There are four top-level folders of content — `src/`, `studies/`, `source_material/`,
`archive/` — plus `scripts/` for the two owner-run checks. Every command is run from the
repository root with `PYTHONPATH=src`.

## Layout

```
GLM/
├── README.md, ENTRY.md, SYSTEM.md, STATUS.md, ITERATE.md,    (state documents)
│   PROJECT_DIRECTIVES.md (22 directives, D1–D22), MASTER_PLAN.md,
│   DIGEST.md, FIGURES.md (both generated), WHITEBOARD.md, LICENSE,
│   REASONING_CAPABILITY.md, CAPABILITY_ASSESSMENT.md,
│   GLM_REPOSITORY_MAP.md (this file)
│
├── lakefile.toml                    (srcDir = "src/lean"; the Lean library RequestProject)
├── lean-toolchain, lake-manifest.json
├── conftest.py                      (adds src/ to sys.path for pytest)
├── .gitignore, .glm_*.json          (sign-off ledger, corpus gate)
│
├── scripts/                         (run on the owner's machine)
│   ├── rebuild_lean.sh              (rebuild .lake: cache get, lake build, axiom audit, sorry scan)
│   ├── check_repository.sh          (every Python gate, one log)
│   ├── apply_reorganisation.sh      (applies this round's file moves to an older checkout)
│   └── logs/                        (the latest logs, read by the next round)
│
├── src/                             (all executable code)
│   ├── GLM.py                       (the CLI: python3 src/GLM.py -q "…")
│   ├── glm_universal/               (the Python package)
│   │   ├── constants.py             (D21: the single source of constants, shared paths, pinned values)
│   │   ├── figures.py, integrity.py, lean_check.py, tools.py
│   │   ├── intake/                  (D22: the intake of supplied material; python3 -m glm_universal.intake)
│   │   ├── corpus/                  (documents as data: tier contract, generated blocks, gate)
│   │   │   ├── study_manifest.py    (the studies' YAML manifests: --check, --sync)
│   │   │   ├── study_index.py       (the `study` query kind, answered from the manifests)
│   │   │   ├── study_links.py       (every relative link resolves, or is recorded absent)
│   │   │   ├── study_ledger.py      (the study graph, acyclic)
│   │   │   ├── dates.py             (D17: the date stamps)
│   │   │   └── yaml.py, checks.py, …
│   │   ├── wheels/                  (the one wheels folder)
│   │   │   ├── __init__.py          (all 15 wheels W01–W15 in one place; W01–W10, the engineering
│   │   │   │                         formula wheels, re-exported from engineering/wheels.py)
│   │   │   ├── w11.py–w15.py        (the domain wheels W11–W15)
│   │   │   ├── integer_wheel.py, monster_wheel.py, sequence_query.py, cent_wheels.py, …
│   │   │   │                        (the provision wheels IW and MW and the cent wheels
│   │   │   │                         W16–W34, PROVISIONAL until the owner's Lean build
│   │   │   │                         confirms them: listed in _data/provisional.json)
│   │   │   └── junctions/           (phase66, domain, oscillator)
│   │   ├── runtime/                 (session, parser, router, TCT engine, reports/)
│   │   ├── reasoning/               (substrate-native reasoning and the study instruments)
│   │   ├── knowledge/               (the corpus as what the GLM knows)
│   │   ├── engineering/             (formula wheels, domains, oscillator junction)
│   │   ├── substrate/, data_objects/, semantics/, migration/, language/, recipe/
│   │   ├── evaluation/, benchmarks/, capabilities/, sandbox/, signoff/, examples/
│   │   └── tests/                   (one test file per module or study; tests/README.md)
│   └── lean/
│       ├── RequestProject/GLM/      (the Lean development, built by lake build)
│       │   ├── AxiomAuditAll.lean   (imports every built file; the whole-development axiom audit)
│       │   ├── Rule30/, HypothesisEngine/, Escalation/, Golay/, Cube/, Semantics/,
│       │   │   PipelineKit/, Shortcut/
│       │   ├── Wheels/              (IntegerWheel.lean, SporadicOrders.lean)
│       │   └── …
│       ├── awaiting_recovery/       (files that import a lost file; out of the build)
│       └── tools/
│
├── studies/                         (one .md + one .yaml per study)
│   ├── _schema/study.schema.yaml    (glm-study-manifest/v1)
│   ├── _lean_files_needed.md        (the Lean files the repository no longer has)
│   └── …
│
├── source_material/                 (the owner's material; kept as supplied)
│   ├── README.md                    (how to supply new material)
│   ├── INTAKE.yaml                  (the ledger: every item, its stage and evidence)
│   ├── ToDo/                        (still being taken in; an item's staged/, when it has
│   │                                 one, holds code waiting for absorption)
│   └── done/                        (absorbed or closed)
│
└── archive/                         (records of earlier rounds)
```

## Where a new file goes

| a new … | goes in | and is recorded by |
| --- | --- | --- |
| piece of supplied material | `source_material/ToDo/` | `python3 -m glm_universal.intake register <path>` |
| study | `studies/<NAME>_STUDY.md` with its `.yaml` | `python3 -m glm_universal.corpus.study_manifest --sync` |
| module | `src/glm_universal/<sub-package>/` | a test file in `src/glm_universal/tests/` and a row in its README |
| wheel | `src/glm_universal/wheels/` (only after the intake's Lean and measured stages) | the intake ledger's `absorbed_into` |
| Lean file | `src/lean/RequestProject/GLM/` | a line in `AxiomAuditAll.lean` (`lean_check --write-audit`) |
| constant, shared path or pinned value | `src/glm_universal/constants.py` | `test_constants.py` |

## Key figures

The counts that move are generated, not typed: see [`FIGURES.md`](FIGURES.md) (Lean files,
query kinds, report subjects, registers, the test suite) and
[`DIGEST.md`](DIGEST.md) (every document at tier 0). The directives are counted live by
`python3 -m glm_universal.tools directives`, the studies by
`python3 -m glm_universal.corpus.study_manifest --check`, and the supplied items by
`python3 -m glm_universal.intake status`.
