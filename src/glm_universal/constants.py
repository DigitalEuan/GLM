"""``glm_universal.constants`` -- the fundamental constants, in one place.

The GLM's fundamental constants were scattered across the tree before this
module: the carrier dimension ``N = 24`` lived in ``data_objects/base.py``;
the signoff schema version lived in ``signoff/rules.py``; the tier-0 field
labels lived in ``corpus/inventory.py``; the sentence patterns lived in
``figures.py``; the closure groups lived in ``signoff/rules.py``; the
null-model seed lived as a magic string in ``integrity.py``; the maximum
document size lived as a magic number in ``signoff/rules.py``.  There was
no single place to look up "what are the fundamental constants of this
project", and no single test that pinned them all.

This module is that place.  It owns the **meta-registry**: the constants
that the registries themselves depend on.  It does **not** own the
study-specific figures (those stay in ``corpus.render.FIGURES``) -- it
owns the constants that ``FIGURES``, ``BLOCKS``, ``SENTENCE_PATTERNS``,
``CHECKS``, and the signoff rule all read.

*Design principle.*  A constant lives here iff:

1. it is read by more than one sub-package (so a change ripples), or
2. it is a fundamental property of the substrate (so it must be findable),
   or
3. it is a magic number/string that the test suite should pin (so it
   cannot drift silently).

A constant that is local to one module stays in that module.

*Versioning.*  This module carries its own :data:`CONSTANTS_SCHEMA`, separate
from the signoff :data:`~signoff.rules.SCHEMA`.  A change to a constant
here bumps ``CONSTANTS_SCHEMA``; the signoff rule reads
:func:`constants_digest` and includes it in every closure, so a constants
change invalidates every signature (the same way a ``rules.py`` change
does).  The Lean formalisation (``Constants.lean``) is the spec; this
module is the executable instance; ``tests/test_constants.py`` checks
that they agree on the values expressible in both.

*Created 30 October 2026 (Iteration 2 of the reorganisation).  This
module consolidates constants that were already in force; it does not
change any value.  The consolidation is the structural face of D6
("every figure a document quotes is generated") and D10 ("a document is
data") extended to constants: nothing fundamental is typed in two
places.*

*Last altered 31 October 2026 (repository check): directive D21 (the owner's
instruction that this module is the single source of constants); the shared
paths of the reorganised tree (the Lean development and its holding folder,
the studies, ``source_material/ToDo`` and ``done``, the intake ledger, the
wheels package) and the helpers :func:`lean_file` and
:func:`source_material_item`; the digest is computed through
``glm_universal.integrity`` (same value as before); ``tests/test_constants.py``
written; :data:`LEAN_BUILD_EVIDENCE` and :data:`LEAN_BUILD_PINS`, the record of
the last passing Lean build that the intake's Lean-verified gate reads.*
"""
from __future__ import annotations

from pathlib import Path
from typing import (
    Any,
    Dict,
    FrozenSet,
    List,
    Mapping,
    Tuple,
)

from .integrity import sha256_hex

__all__ = [
    # Schema
    "CONSTANTS_SCHEMA",
    "constants_digest",
    # Substrate
    "CARRIER_DIMENSION",
    "GOLAY_LENGTH",
    "GOLAY_DIMENSION",
    "LEECH_DIMENSION",
    # Carrier regime (the Lean Constants.lean values)
    "CARRIER_Y",
    "CARRIER_Q",
    "CARRIER_BUDGET",
    "CARRIER_TAX",
    "CARRIER_NRCI",
    # Signoff rule
    "SIGNOFF_SCHEMA",
    "DOCUMENT_CHECKS",
    "RENDER_READERS",
    "DIGEST_MODES",
    "CLOSURE_GROUPS",
    "DOCUMENT_SUFFIXES",
    "YAML_SUFFIXES",
    "MAX_DOCUMENT_BYTES",
    # Corpus
    "TIER0_FIELD_LABELS",
    "TIER0_FOOTER",
    "NO_FUNCTION",
    "SESSION_NOTES",
    "SKIP_DIRECTORIES",
    # Figures
    "SENTENCE_PATTERN_NAMES",
    # Integrity
    "NULL_MODEL_SEED",
    # Paths
    "REPOSITORY_ROOT",
    "PACKAGE_ROOT",
    "LEAN_ROOT",
    "LEAN_SOURCE_DIR",
    "LEAN_LIBRARY",
    "LEAN_GLM_DIR",
    "LEAN_AUDIT_FILE",
    "LEAN_HOLDING_DIR",
    "LEAN_EXTERNAL_PREFIXES",
    "SCRIPTS_DIR",
    "LEAN_BUILD_EVIDENCE",
    "LEAN_BUILD_PINS",
    "STUDIES_DIR",
    "STUDY_SCHEMA_FILE",
    "LEAN_FILES_NEEDED",
    "SOURCE_MATERIAL_DIR",
    "SOURCE_TODO_DIR",
    "SOURCE_DONE_DIR",
    "INTAKE_LEDGER",
    "WHEELS_DIR",
    "lean_file",
    "LEAN_SUFFIX",
    "source_material_item",
]


# ---------------------------------------------------------------------------
# Schema and digest
# ---------------------------------------------------------------------------

#: The constants schema version.  Bump when the *meaning* of a constant
#: changes (not when a value moves -- a value move is itself the change).
#: The signoff rule reads :func:`constants_digest` and includes it in every
#: closure, so a bump here invalidates every signature.
CONSTANTS_SCHEMA: int = 1


def constants_digest() -> str:
    """A SHA-256 over the canonical serialisation of every constant in this
    module.

    The signoff rule includes this digest in every unit's closure, so a
    change to any constant here invalidates every signature -- the same
    effect as editing ``signoff/rules.py``.  This is the structural face
    of "a fundamental constant is in one place": there is no second copy
    to drift.
    """
    parts: List[str] = []
    parts.append(f"CONSTANTS_SCHEMA={CONSTANTS_SCHEMA}\n")
    # Substrate
    parts.append(f"CARRIER_DIMENSION={CARRIER_DIMENSION}\n")
    parts.append(f"GOLAY_LENGTH={GOLAY_LENGTH}\n")
    parts.append(f"GOLAY_DIMENSION={GOLAY_DIMENSION}\n")
    parts.append(f"LEECH_DIMENSION={LEECH_DIMENSION}\n")
    # Carrier regime
    parts.append(f"CARRIER_Y={CARRIER_Y}\n")
    parts.append(f"CARRIER_Q={CARRIER_Q}\n")
    parts.append(f"CARRIER_BUDGET={CARRIER_BUDGET}\n")
    parts.append(f"CARRIER_TAX={CARRIER_TAX}\n")
    parts.append(f"CARRIER_NRCI={CARRIER_NRCI}\n")
    # Signoff rule
    parts.append(f"SIGNOFF_SCHEMA={SIGNOFF_SCHEMA}\n")
    parts.append(f"DOCUMENT_CHECKS={','.join(DOCUMENT_CHECKS)}\n")
    parts.append(f"RENDER_READERS={','.join(RENDER_READERS)}\n")
    parts.append(f"DIGEST_MODES={','.join(DIGEST_MODES)}\n")
    parts.append(f"CLOSURE_GROUPS={','.join(CLOSURE_GROUPS)}\n")
    parts.append(f"DOCUMENT_SUFFIXES={','.join(DOCUMENT_SUFFIXES)}\n")
    parts.append(f"YAML_SUFFIXES={','.join(YAML_SUFFIXES)}\n")
    parts.append(f"MAX_DOCUMENT_BYTES={MAX_DOCUMENT_BYTES}\n")
    # Corpus
    parts.append(f"TIER0_FIELD_LABELS={TIER0_FIELD_LABELS}\n")
    parts.append(f"TIER0_FOOTER={TIER0_FOOTER!r}\n")
    parts.append(f"NO_FUNCTION={NO_FUNCTION!r}\n")
    parts.append(f"SESSION_NOTES={','.join(sorted(SESSION_NOTES))}\n")
    parts.append(f"SKIP_DIRECTORIES={','.join(sorted(SKIP_DIRECTORIES))}\n")
    # Figures
    parts.append(f"SENTENCE_PATTERN_NAMES={','.join(SENTENCE_PATTERN_NAMES)}\n")
    # Integrity
    parts.append(f"NULL_MODEL_SEED={NULL_MODEL_SEED!r}\n")
    return sha256_hex("".join(parts).encode("utf-8"))


# ---------------------------------------------------------------------------
# Substrate constants
# ---------------------------------------------------------------------------

#: The carrier dimension.  Fixed by the Leech lattice, not by convention.
#: (Mirrors ``data_objects/base.py`` line 70; formalised in
#: ``Constants.lean``.)
CARRIER_DIMENSION: int = 24

#: The length of a binary Golay codeword.
GOLAY_LENGTH: int = 24

#: The dimension of the binary Golay code (number of generator rows).
GOLAY_DIMENSION: int = 12

#: The dimension of the Leech lattice.
LEECH_DIMENSION: int = 24


# ---------------------------------------------------------------------------
# Carrier regime constants (the Lean Constants.lean values)
# ---------------------------------------------------------------------------

#: ``Y = 1/(pi + 2/pi)`` -- the carrier regime's reference value.
#: Formalised in ``Constants.lean`` as ``Y`` with theorems ``Y_pos``,
#: ``Y_lt_half``, ``Y_gt_quarter``.  The Python computes it on demand
#: from the Wobble subsystem (D18); the constant here is the certified
#: enclosure's lower bound (a Fraction).  *Placeholder until the Wobble
#: subsystem is wired (Phase R4 of the reorganisation plan); the value
#: below is a rational approximation, to be replaced by the wobble.*
from fractions import Fraction as _F
CARRIER_Y: _F = _F(1, 4)  # placeholder; the Lean value is irrational

#: ``Q = Y + 1/8`` -- the carrier regime's second reference value.
CARRIER_Q: _F = CARRIER_Y + _F(1, 8)

#: The carrier budget (``B = 10``).
CARRIER_BUDGET: int = 10

#: The carrier tax.  Formalised in ``Constants.lean``.
CARRIER_TAX: int = 8

#: The NRCI (non-residual carrier index).  Formalised in ``Constants.lean``.
CARRIER_NRCI: int = 4


# ---------------------------------------------------------------------------
# Signoff rule constants
# ---------------------------------------------------------------------------

#: The signoff ledger schema version.  Bumped when the *meaning* of a
#: digest changes.  (Mirrors ``signoff/rules.py`` line 86.)
SIGNOFF_SCHEMA: int = 6

#: The test files that read documents by walking the corpus (not by name).
#: Their closure includes every written document, and their digest mode
#: is ``"raw"``.  (Mirrors ``signoff/rules.py`` ``DOCUMENT_CHECKS``.)
DOCUMENT_CHECKS: Tuple[str, ...] = ("test_corpus.py", "test_figures.py")

#: The modules whose presence in a closure flips the digest mode to
#: ``"rendered"``.  (Mirrors ``signoff/rules.py`` ``RENDER_READERS``.)
RENDER_READERS: Tuple[str, ...] = (
    "corpus/render.py",
    "corpus/checks.py",
    "figures.py",
)

#: The three document digest modes.  (Mirrors ``signoff/rules.py``
#: ``DIGEST_MODES``.)
DIGEST_MODES: Tuple[str, ...] = ("written", "rendered", "raw")

#: The five closure groups, recorded with each signature to explain why a
#: unit is stale.  (Mirrors ``signoff/rules.py`` ``CLOSURE_GROUPS``.)
CLOSURE_GROUPS: Tuple[str, ...] = (
    "scaffolding", "data", "documents", "lean", "code",
)

#: The document suffixes walked by the corpus.  ``.yaml`` and ``.yml`` are
#: added by this iteration's YAML-aware protocol (see
#: ``SYSTEMS_TEST_AND_SIGNOFF_PROTOCOL.md``); they are not yet enforced
#: until the protocol is adopted and the signoff schema is bumped.
DOCUMENT_SUFFIXES: Tuple[str, ...] = (".md", ".txt")

#: The YAML suffixes, separate from :data:`DOCUMENT_SUFFIXES` until the
#: YAML-aware protocol is adopted (at which point they are merged in).
YAML_SUFFIXES: Tuple[str, ...] = (".yaml", ".yml")

#: The maximum document size read by the corpus and the reader (4 MB).
#: (Mirrors ``signoff/rules.py`` line 569.)
MAX_DOCUMENT_BYTES: int = 4 * 1024 * 1024


# ---------------------------------------------------------------------------
# Corpus constants
# ---------------------------------------------------------------------------

#: The four tier-0 field labels.  (Mirrors ``corpus/inventory.py`` ``_FIELD_LABELS``.)
TIER0_FIELD_LABELS: Mapping[str, str] = {
    "question": "Question.",
    "verdict": "Verdict.",
    "figure":   "Deciding figure.",
    "recomputed": "Recomputed by.",
}

#: The footer that closes a Tier-0 block.  (Mirrors
#: ``corpus/inventory.py``.)
TIER0_FOOTER: str = "*Tier 0 is a coarse read"

#: The marker a hand-written argument carries in the ``Recomputed by``
#: field, exempting it from the function-resolution check.  (Mirrors
#: ``corpus/inventory.py``.)
NO_FUNCTION: str = "(hand-written argument; nothing to recompute)"

#: The session working notes, never read by the corpus.  (Mirrors
#: ``corpus/inventory.py`` ``SESSION_NOTES``.)
SESSION_NOTES: FrozenSet[str] = frozenset({"ARISTOTLE_SUMMARY.md"})

#: Directories never entered by the corpus walk.  (Mirrors
#: ``corpus/inventory.py`` ``SKIP_DIRECTORIES``.)
SKIP_DIRECTORIES: FrozenSet[str] = frozenset({
    ".git",
    ".lake",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "_knowledge_cache",
})


# ---------------------------------------------------------------------------
# Figures constants
# ---------------------------------------------------------------------------

#: The names of the eight sentence patterns (the shapes a document's
#: quoted sentence must match).  The full ``(name, regex, description)``
#: tuples stay in ``figures.SENTENCE_PATTERNS`` (because the regexes are
#: part of the figures computation, not a constant); the names are here
#: so a test can pin the set.  (Mirrors ``figures.py`` line 498.)
SENTENCE_PATTERN_NAMES: Tuple[str, ...] = (
    "registers",
    "query_kinds",
    "report_subjects",
    "evaluation_cases",
    "test_files",
    "lean_files",
    "directives",
    "suite",
)


# ---------------------------------------------------------------------------
# Integrity constants
# ---------------------------------------------------------------------------

#: The null-model seed used by ``integrity.seeded_permutation``.  Was a
#: magic string in ``integrity.py`` line 110; now findable here.
NULL_MODEL_SEED: str = "glm-null-model"


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

#: This module's location: ``glm_universal/constants.py``.
_HERE = Path(__file__).resolve()

#: The package root: ``glm_universal/``.
PACKAGE_ROOT: Path = _HERE.parent

#: The repository root: the parent of the package.
REPOSITORY_ROOT: Path = PACKAGE_ROOT.parent.parent

#: The Lean development root: ``src/lean/`` (the ``srcDir`` of
#: ``lakefile.toml``; it was ``glm_lean/`` before the reorganisation).
LEAN_ROOT: Path = REPOSITORY_ROOT / "src" / "lean"

#: The Lean source directory (the ``srcDir`` of ``lakefile.toml``).
LEAN_SOURCE_DIR: Path = LEAN_ROOT

#: The Lean library name (``[[lean_lib]] name`` in ``lakefile.toml``) and the
#: top directory of its sources under :data:`LEAN_SOURCE_DIR`.
LEAN_LIBRARY: str = "RequestProject"

#: The GLM part of the Lean development: ``src/lean/RequestProject/GLM``.
LEAN_GLM_DIR: Path = LEAN_SOURCE_DIR / LEAN_LIBRARY / "GLM"

#: The whole-development axiom audit, which must import every Lean file.
LEAN_AUDIT_FILE: Path = LEAN_GLM_DIR / "AxiomAuditAll.lean"

#: The suffix of a Lean source file (see :func:`lean_file` for why it is
#: taken from a named file rather than spelled).
LEAN_SUFFIX: str = LEAN_AUDIT_FILE.suffix

#: Lean files held back from the build because a file they import is
#: missing (outside the ``RequestProject`` glob, so ``lake build`` never sees
#: them).  ``python3 -m glm_universal.lean_check`` lists what each waits for.
LEAN_HOLDING_DIR: Path = LEAN_ROOT / "awaiting_recovery"

#: Import prefixes that are not files of this development.
LEAN_EXTERNAL_PREFIXES: FrozenSet[str] = frozenset({
    "Mathlib", "Lean", "Std", "Init", "Aesop", "Batteries", "Qq",
    "Plausible", "ProofWidgets", "LeanSearchClient", "ImportGraph",
})

#: The repository's scripts directory (the Lean rebuild script lives here).
SCRIPTS_DIR: Path = REPOSITORY_ROOT / "scripts"

#: The record of the last passing Lean build, written by
#: ``scripts/rebuild_lean.sh`` only when the static check, ``lake build``
#: (whose ``AxiomAuditAll.lean`` fails on ``sorry`` or a non-standard axiom)
#: and the ``sorry`` scan all passed: the SHA-256 of every Lean file that was
#: built, the toolchain and the Mathlib pin.  The intake's ``Lean verified``
#: gate reads it (``glm_universal.lean_check.verification_problems``).
LEAN_BUILD_EVIDENCE: Path = SCRIPTS_DIR / "logs" / "lean_build_evidence.json"

#: The files outside the Lean sources whose change makes a build record stale.
LEAN_BUILD_PINS: Tuple[str, ...] = ("lean-toolchain", "lake-manifest.json", "lakefile.toml")

#: The studies: one ``*_STUDY.md`` + ``*_STUDY.yaml`` pair per question.
STUDIES_DIR: Path = REPOSITORY_ROOT / "studies"

#: The study manifest schema.
STUDY_SCHEMA_FILE: Path = STUDIES_DIR / "_schema" / "study.schema.yaml"

#: The registry of Lean files the reorganisation lost.
LEAN_FILES_NEEDED: Path = STUDIES_DIR / "_lean_files_needed.md"

#: The input folder: everything the owner supplies arrives here.
SOURCE_MATERIAL_DIR: Path = REPOSITORY_ROOT / "source_material"

#: Supplied items not yet taken through the intake pipeline.
SOURCE_TODO_DIR: Path = SOURCE_MATERIAL_DIR / "ToDo"

#: Supplied items whose intake is finished (absorbed, or closed with a
#: recorded reason).
SOURCE_DONE_DIR: Path = SOURCE_MATERIAL_DIR / "done"

#: The intake ledger: one record per supplied item, with its stage.
INTAKE_LEDGER: Path = SOURCE_MATERIAL_DIR / "INTAKE.yaml"

#: The one wheels folder (directive D5 and the intake rule): every wheel the
#: GLM uses lives in this package.
WHEELS_DIR: Path = PACKAGE_ROOT / "wheels"


# ---------------------------------------------------------------------------
# Path helpers (the two places a file may legitimately have moved to)
# ---------------------------------------------------------------------------

def lean_file(name: str) -> Path:
    """The path of a Lean file of the development, wherever it now lives.

    ``name`` is a file name (``"LeechShellCount.lean"``), a path relative to
    ``RequestProject/GLM`` (``"Rule30/Basic.lean"``) or a module name
    (``"RequestProject.GLM.LeechShellCount"``).  The file is looked for in the
    build tree first and then in :data:`LEAN_HOLDING_DIR`, where a file waits
    while a file it imports is missing; the build-tree path is returned when
    it is in neither, so a reader reports the absence itself.

    This helper opens no file.  The suffix is :data:`LEAN_SUFFIX`, taken from
    a file this module names rather than spelled as a bare string: under the
    sign-off closure rule (:func:`glm_universal.signoff.rules.referenced_documents`)
    a bare Lean suffix reads as a walk of the development, and since nearly
    every module imports this one, every test then depended on all of it.  A
    caller that reads the returned path spells its file name, which the rule
    resolves; the callers that pass module names are the manifest readers
    (``corpus/study_manifest.py`` and its importers), which hold the whole
    development through their own walk.  (31 October 2026, repository check.)
    """
    rel = name
    if not rel.endswith(LEAN_SUFFIX):
        rel = rel.replace(".", "/") + LEAN_SUFFIX
    if rel.startswith(LEAN_LIBRARY + "/"):
        rel_lib = Path(rel)
    else:
        rel_lib = Path(LEAN_LIBRARY) / "GLM" / rel
    for base in (LEAN_SOURCE_DIR, LEAN_HOLDING_DIR):
        candidate = base / rel_lib
        if candidate.is_file():
            return candidate
    return LEAN_SOURCE_DIR / rel_lib


def source_material_item(name: str) -> Path:
    """The path of a supplied item (a file or folder of ``source_material``).

    Items are filed under :data:`SOURCE_TODO_DIR` until their intake is
    finished and under :data:`SOURCE_DONE_DIR` afterwards; ``name`` is the
    item's path below that folder (``"GLM_Pipeline_Kit"`` or
    ``"GLM_Pipeline_Kit/GLMKit/AxiomAudit.lean"``).  The first existing
    location wins, then the legacy flat location; the ``done`` path is
    returned when the item is nowhere, so a reader reports the absence.
    """
    for base in (SOURCE_DONE_DIR, SOURCE_TODO_DIR, SOURCE_MATERIAL_DIR):
        candidate = base / name
        if candidate.exists():
            return candidate
    return SOURCE_DONE_DIR / name
