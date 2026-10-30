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
module is the executable instance; ``tests/test_constants.py`` (to be
written) checks that they agree on the values expressible in both.

*Created 30 October 2026 (Iteration 2 of the reorganisation).  This
module consolidates constants that were already in force; it does not
change any value.  The consolidation is the structural face of D6
("every figure a document quotes is generated") and D10 ("a document is
data") extended to constants: nothing fundamental is typed in two
places.*
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import (
    Any,
    Dict,
    FrozenSet,
    Mapping,
    Tuple,
)

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
    h = hashlib.sha256()
    h.update(f"CONSTANTS_SCHEMA={CONSTANTS_SCHEMA}\n".encode("utf-8"))
    # Substrate
    h.update(f"CARRIER_DIMENSION={CARRIER_DIMENSION}\n".encode("utf-8"))
    h.update(f"GOLAY_LENGTH={GOLAY_LENGTH}\n".encode("utf-8"))
    h.update(f"GOLAY_DIMENSION={GOLAY_DIMENSION}\n".encode("utf-8"))
    h.update(f"LEECH_DIMENSION={LEECH_DIMENSION}\n".encode("utf-8"))
    # Carrier regime
    h.update(f"CARRIER_Y={CARRIER_Y}\n".encode("utf-8"))
    h.update(f"CARRIER_Q={CARRIER_Q}\n".encode("utf-8"))
    h.update(f"CARRIER_BUDGET={CARRIER_BUDGET}\n".encode("utf-8"))
    h.update(f"CARRIER_TAX={CARRIER_TAX}\n".encode("utf-8"))
    h.update(f"CARRIER_NRCI={CARRIER_NRCI}\n".encode("utf-8"))
    # Signoff rule
    h.update(f"SIGNOFF_SCHEMA={SIGNOFF_SCHEMA}\n".encode("utf-8"))
    h.update(f"DOCUMENT_CHECKS={','.join(DOCUMENT_CHECKS)}\n".encode("utf-8"))
    h.update(f"RENDER_READERS={','.join(RENDER_READERS)}\n".encode("utf-8"))
    h.update(f"DIGEST_MODES={','.join(DIGEST_MODES)}\n".encode("utf-8"))
    h.update(f"CLOSURE_GROUPS={','.join(CLOSURE_GROUPS)}\n".encode("utf-8"))
    h.update(f"DOCUMENT_SUFFIXES={','.join(DOCUMENT_SUFFIXES)}\n".encode("utf-8"))
    h.update(f"YAML_SUFFIXES={','.join(YAML_SUFFIXES)}\n".encode("utf-8"))
    h.update(f"MAX_DOCUMENT_BYTES={MAX_DOCUMENT_BYTES}\n".encode("utf-8"))
    # Corpus
    h.update(f"TIER0_FIELD_LABELS={TIER0_FIELD_LABELS}\n".encode("utf-8"))
    h.update(f"TIER0_FOOTER={TIER0_FOOTER!r}\n".encode("utf-8"))
    h.update(f"NO_FUNCTION={NO_FUNCTION!r}\n".encode("utf-8"))
    h.update(f"SESSION_NOTES={','.join(sorted(SESSION_NOTES))}\n".encode("utf-8"))
    h.update(f"SKIP_DIRECTORIES={','.join(sorted(SKIP_DIRECTORIES))}\n".encode("utf-8"))
    # Figures
    h.update(f"SENTENCE_PATTERN_NAMES={','.join(SENTENCE_PATTERN_NAMES)}\n".encode("utf-8"))
    # Integrity
    h.update(f"NULL_MODEL_SEED={NULL_MODEL_SEED!r}\n".encode("utf-8"))
    return h.hexdigest()


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
#: from the Wobble subsystem (D17); the constant here is the certified
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

#: The four tier-0 field labels.  (Mirrors ``corpus/inventory.py`` line 170.)
TIER0_FIELD_LABELS: Mapping[str, str] = {
    "question": "Question.",
    "verdict": "Verdict.",
    "figure":   "Deciding figure.",
    "recomputed": "Recomputed by.",
}

#: The footer that closes a Tier-0 block.  (Mirrors
#: ``corpus/inventory.py`` line 283.)
TIER0_FOOTER: str = "*Tier 0 is a coarse read"

#: The marker a hand-written argument carries in the ``Recomputed by``
#: field, exempting it from the function-resolution check.  (Mirrors
#: ``corpus/inventory.py``.)
NO_FUNCTION: str = "(hand-written argument; nothing to recompute)"

#: The session working notes, never read by the corpus.  (Mirrors
#: ``corpus/inventory.py`` line 92.)
SESSION_NOTES: FrozenSet[str] = frozenset({"ARISTOTLE_SUMMARY.md"})

#: Directories never entered by the corpus walk.  (Mirrors
#: ``corpus/inventory.py`` line 84.)
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

#: The Lean development root: ``glm_lean/`` at the repository root.
LEAN_ROOT: Path = REPOSITORY_ROOT / "src" / "lean"

#: The Lean source directory (the ``srcDir`` of ``lakefile.toml``).
LEAN_SOURCE_DIR: Path = LEAN_ROOT
