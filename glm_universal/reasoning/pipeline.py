"""``glm_universal.reasoning.pipeline`` -- study to test to implemented, measured.

The problem this solves
-----------------------
A study document is easy to write and easy to leave behind.  Three rounds of
this project ended with a document describing something the code did not do, or
with code nothing could reach: an error-feedback loop no report exposed, a
catalogue audit the master plan did not know about, a pair of higher-dimensional
lattice modules whose study document had not been written.  In each case the
work existed and the *account* of it did not, and the next session spent its
first hour auditing instead of building.

So the pipeline is made explicit, and the stage each piece of work has reached
is **computed from the tree** rather than claimed in prose.  Directive D5 of
``PROJECT_DIRECTIVES.md`` states the rule; this module is its instrument.

The six stages
--------------
======  ==============  ==================================================
stage   means           detected by
======  ==============  ==================================================
1       studied         the document exists and is not a stub
2       implemented     every module of the row exists
3       wired           the report subject is in ``REPORT_SUBJECTS``
4       tested          some test file imports one of the modules
5       formalised      every named Lean file exists
6       verified        a column-3 template exists for the subject
======  ==============  ==================================================

Stage 6 is the presence of the template, not a run of it: running
``--verify-tct`` spawns a fresh interpreter per subject and takes minutes,
which is a full check rather than a status board.  :func:`verify_commands`
prints the commands that do run it, and ``STATUS.md`` lists them.

What is declared and what is measured
-------------------------------------
Only the *registry* below is declared -- which document, modules, subject, test
hint and Lean files belong to one piece of work.  That association cannot be
derived from the tree, because it is what the work *is*.  Everything else --
whether each of those exists, whether the subject dispatches, which test file
covers it, how many tests that is -- is read off the tree at call time, so a
row cannot claim a stage it has not reached.

A row may declare ``lean_expected=False`` when a Lean counterpart is not
meaningful (the directives table, this module).  Those rows are counted
separately rather than silently excused.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

_HERE = Path(__file__).resolve()
PACKAGE_ROOT = _HERE.parent.parent
PROJECT_ROOT = PACKAGE_ROOT.parent
REPO_ROOT = PROJECT_ROOT.parent
TESTS_DIR = PACKAGE_ROOT / "tests"

#: Where documents are looked for, in order.  Study write-ups live in
#: ``studies/`` and supplied material in ``source_material/`` (see
#: ``DOCUMENTS.md`` at the repository root); the registry below still names
#: them by their bare file name and the search covers both folders.
_DOC_ROOTS = (REPO_ROOT, REPO_ROOT / "studies", REPO_ROOT / "source_material",
              PROJECT_ROOT)

#: Where the Lean development is looked for, in order.
_LEAN_ROOTS = (PROJECT_ROOT / "glm_lean" / "RequestProject" / "GLM",
               REPO_ROOT / "RequestProject" / "GLM")

#: A document shorter than this is a stub, not a study.
STUB_BYTES = 2000

STAGES: Tuple[str, ...] = (
    "studied", "implemented", "wired", "tested", "formalised", "verified",
)


@dataclass(frozen=True)
class Row:
    """One piece of work, and where to look for each of its stages."""

    key: str
    title: str
    document: str
    modules: Tuple[str, ...]
    subject: Optional[str]
    lean: Tuple[str, ...] = ()
    lean_expected: bool = True


#: The registry.  Association only -- every stage is measured, never declared.
REGISTRY: Tuple[Row, ...] = (
    Row("information-loss", "what a layer boundary costs",
        "INFORMATION_LOSS_STUDY.md",
        ("reasoning/information_loss.py", "reasoning/dimension_layers.py"),
        "information loss",
        ("Layers.lean", "Tower.lean", "GolayBoundary.lean",
         "TaxConservation.lean")),
    Row("infinite-values", "reals as processes, and where the value layer stops",
        "INFINITE_VALUES_STUDY.md",
        ("reasoning/exact_real.py", "reasoning/transcendental.py"),
        "infinite values",
        ("Irrational.lean", "Transcendental.lean", "Constants.lean")),
    Row("geometric-ambiguity", "the six-fold Golay tie and its dynamics",
        "GEOMETRIC_AMBIGUITY_STUDY.md",
        ("substrate/superposition.py", "reasoning/facets.py"),
        "superposition",
        ("Superposition.lean", "Facets.lean", "Wobble.lean",
         "HullExpansion.lean")),
    Row("noise-experiment", "noise as the computation",
        "NOISE_EXPERIMENT_STUDY.md",
        ("reasoning/noise_lab.py",),
        "noise",
        ("DeltaSigma.lean", "Cascade.lean", "Feedback.lean")),
    Row("analogy-layer", "analogy by named relation",
        "ANALOGY_LAYER_STUDY.md",
        ("reasoning/analogy_models.py",),
        "analogies",
        ("Semantics/Meaning.lean",)),
    Row("study-catalog", "the findings catalogue as a claim ledger",
        "GLM_STUDY_CATALOG_AUDIT.md",
        ("reasoning/catalog.py", "reasoning/wobble.py", "reasoning/drift.py"),
        "catalog",
        ("Sturmian.lean",)),
    Row("unification-blueprint", "the blueprint as a claim ledger",
        "GLM_UNIFICATION_BLUEPRINT_AUDIT.md",
        ("reasoning/blueprint.py",),
        "blueprint",
        ("Reversible.lean", "Mantissa.lean")),
    Row("companion-studies", "the two companion preprints, claim by claim",
        "GLM_COMPANION_STUDIES_AUDIT.md",
        ("reasoning/companion.py", "reasoning/containers.py"),
        "companion",
        ("Constants.lean",)),
    Row("higher-lattices", "past 24: the 32- and 48-dimensional rungs",
        "HIGHER_LATTICE_STUDY.md",
        ("substrate/lattice32.py", "substrate/lattice48.py",
         "reasoning/higher_lattices.py"),
        "lattices",
        ("HigherLattices.lean",)),
    Row("shell-sigma", "the delta-sigma loop run against the Leech shell",
        "HIGHER_LATTICE_STUDY.md",
        ("reasoning/shell_sigma.py",),
        "shells",
        ("ShellSigma.lean",)),
    Row("lean-address", "deterministic Leech addresses for Lean declarations",
        "LEAN_ADDRESS_STUDY.md",
        ("reasoning/lean_address.py",),
        "lean",
        ("Address.lean",)),
    Row("harmony", "the musical third of the universality claim",
        "HARMONY_STUDY.md",
        ("data_objects/harmonics.py", "reasoning/harmony.py"),
        "harmony",
        ("Harmony.lean",)),
    Row("economics", "the economic third of the universality claim",
        "ECONOMICS_STUDY.md",
        ("data_objects/economics_register.py", "reasoning/economics.py"),
        "economics",
        ("LogBucket.lean",)),
    Row("escalation", "the layer stack audited at register scale",
        "ESCALATION_STUDY.md",
        ("reasoning/escalation.py",),
        "escalation",
        ("Escalation.lean",)),
    Row("relative-measure", "a measure word read as a measurement",
        "RELATIVE_MEASURE_STUDY.md",
        ("data_objects/comparison_classes.py", "reasoning/measure_view.py"),
        "measure",
        ("MeasureView.lean",)),
    Row("denotation", "what the undimensioned names denote",
        "DENOTATION_STUDY.md",
        ("data_objects/denotation.py", "reasoning/denotation_view.py"),
        "measure",
        ("Denotation.lean",)),
    Row("name-coordinate", "the resolution ceiling, attacked where it lives",
        "NAME_COORDINATE_STUDY.md",
        ("reasoning/name_coordinate.py",),
        "names",
        ("NameCoordinate.lean",)),
    Row("hexcolour", "the address layer, audited on the shipped data",
        "HEXCOLOUR_STUDY.md",
        ("migration/state.py", "substrate/isomorphism.py"),
        "state migration",
        ("Endianness.lean",)),
    Row("semantics", "meaning, not spelling",
        "MASTER_PLAN.md",
        ("semantics/meaning.py", "semantics/graph.py", "semantics/audit.py"),
        "semantics",
        ("Semantics/Meaning.lean", "Semantics/Grounding.lean")),
    Row("directives", "the standing rules, and their instruments",
        "PROJECT_DIRECTIVES.md",
        ("reasoning/directives.py",),
        "directives",
        (), lean_expected=False),
    Row("pipeline", "study to test to implemented, measured",
        "PROJECT_DIRECTIVES.md",
        ("reasoning/pipeline.py",),
        "pipeline",
        (), lean_expected=False),
)


# ===========================================================================
#  Locating things
# ===========================================================================

def document_path(name: str) -> Optional[Path]:
    for root in _DOC_ROOTS:
        candidate = root / name
        if candidate.is_file():
            return candidate
    return None


def module_path(relative: str) -> Optional[Path]:
    candidate = PACKAGE_ROOT / relative
    return candidate if candidate.is_file() else None


def lean_path(name: str) -> Optional[Path]:
    for root in _LEAN_ROOTS:
        candidate = root / name
        if candidate.is_file():
            return candidate
    return None


def _report_subjects() -> Tuple[str, ...]:
    from ..runtime.session import REPORT_SUBJECTS
    return tuple(REPORT_SUBJECTS)


def _templates() -> Tuple[str, ...]:
    from ..runtime.tct_engine import TEMPLATES
    return tuple(sorted(TEMPLATES))


def _dotted(relative: str) -> str:
    return "glm_universal." + relative[:-3].replace("/", ".")


_test_index_cache: Optional[Dict[str, Tuple[str, ...]]] = None


def test_index() -> Dict[str, Tuple[str, ...]]:
    """Which test files import which package modules.

    Read with :mod:`ast` from the test sources, so nothing is imported and no
    test is run to find out.
    """
    global _test_index_cache
    if _test_index_cache is not None:
        return _test_index_cache
    index: Dict[str, List[str]] = {}
    for path in sorted(TESTS_DIR.glob("test_*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError):  # pragma: no cover - defensive
            continue
        for node in ast.walk(tree):
            names: List[str] = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names
                         if a.name.startswith("glm_universal")]
            elif isinstance(node, ast.ImportFrom) and node.module:
                base = node.module
                if not base.startswith("glm_universal"):
                    continue
                names = [base] + [f"{base}.{a.name}" for a in node.names]
            for name in names:
                index.setdefault(name, []).append(path.name)
    _test_index_cache = {key: tuple(sorted(set(value)))
                         for key, value in index.items()}
    return _test_index_cache


def tests_covering(relative: str) -> Tuple[str, ...]:
    """Test files that import a module, by its package-relative path."""
    dotted = _dotted(relative)
    index = test_index()
    hits = set(index.get(dotted, ()))
    # ``from glm_universal.reasoning import lean_address`` indexes as the
    # sub-package plus the attribute
    for key, files in index.items():
        if key == dotted or key.startswith(dotted + "."):
            hits.update(files)
    return tuple(sorted(hits))


def count_tests(filename: str) -> int:
    """How many test methods a test file defines -- counted, not run."""
    path = TESTS_DIR / filename
    if not path.is_file():
        return 0
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError):  # pragma: no cover - defensive
        return 0
    total = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                and node.name.startswith("test_"):
            total += 1
    return total


# ===========================================================================
#  Stages
# ===========================================================================

def stage_report(row: Row) -> Dict[str, object]:
    """Every stage of one row, each with the evidence that decided it."""
    doc = document_path(row.document)
    doc_bytes = doc.stat().st_size if doc else 0
    modules = {name: module_path(name) is not None for name in row.modules}
    subjects = _report_subjects()
    templates = _templates()
    covering: Dict[str, Tuple[str, ...]] = {
        name: tests_covering(name) for name in row.modules}
    all_covering = sorted({f for files in covering.values() for f in files})
    lean = {name: lean_path(name) is not None for name in row.lean}
    template_name = ("report_" + row.subject.replace(" ", "_")
                     if row.subject else None)

    stages = {
        "studied": bool(doc) and doc_bytes >= STUB_BYTES,
        "implemented": bool(modules) and all(modules.values()),
        "wired": bool(row.subject) and row.subject in subjects,
        "tested": bool(all_covering),
        "formalised": (all(lean.values()) and bool(lean))
                      if row.lean_expected else True,
        "verified": bool(template_name) and template_name in templates,
    }
    missing = [name for name in STAGES if not stages[name]]
    return {
        "key": row.key,
        "title": row.title,
        "document": row.document,
        "document_bytes": doc_bytes,
        "modules": dict(sorted(modules.items())),
        "subject": row.subject,
        "template": template_name,
        "tests": tuple(all_covering),
        "test_count": sum(count_tests(name) for name in all_covering),
        "lean": dict(sorted(lean.items())),
        "lean_expected": row.lean_expected,
        "stages": stages,
        "stages_reached": sum(1 for name in STAGES if stages[name]),
        "complete": not missing,
        "first_missing": missing[0] if missing else None,
    }


def verify_commands() -> Tuple[str, ...]:
    """The commands that actually run column 3 for every wired subject."""
    rows = [stage_report(row) for row in REGISTRY]
    return tuple(
        f'PYTHONPATH=. python3 GLM.py -q "report {r["subject"]}" --verify-tct'
        for r in rows if r["stages"]["wired"])


def pipeline_report() -> Dict[str, object]:
    """Every row, its stage, and what the whole board looks like."""
    rows = tuple(stage_report(row) for row in REGISTRY)
    complete = [r for r in rows if r["complete"]]
    by_stage = {name: sum(1 for r in rows if r["stages"][name])
                for name in STAGES}
    blocked: Dict[str, List[str]] = {}
    for r in rows:
        if r["first_missing"]:
            blocked.setdefault(r["first_missing"], []).append(r["key"])
    return {
        "rows": rows,
        "count": len(rows),
        "complete": len(complete),
        "complete_rate": Fraction(len(complete), len(rows)) if rows else Fraction(0),
        "by_stage": by_stage,
        "stages": STAGES,
        "blocked_at": {k: tuple(v) for k, v in sorted(blocked.items())},
        "incomplete": tuple(r["key"] for r in rows if not r["complete"]),
        "total_tests": sum(r["test_count"] for r in rows),
        "lean_not_expected": tuple(r["key"] for r in rows
                                   if not r["lean_expected"]),
        "verify_commands": verify_commands(),
    }


def _main(argv: Sequence[str]) -> int:
    report = pipeline_report()
    width = max(len(r["key"]) for r in report["rows"])
    print(f"{'row':<{width}}  " + "  ".join(s[:4] for s in STAGES) + "   next")
    for r in report["rows"]:
        marks = "  ".join(" ok " if r["stages"][s] else " -- " for s in STAGES)
        print(f"{r['key']:<{width}}  {marks}   {r['first_missing'] or ''}")
    print()
    print(f"{report['complete']} of {report['count']} rows complete")
    for stage, keys in report["blocked_at"].items():
        print(f"blocked at {stage}: {', '.join(keys)}")
    return 0
