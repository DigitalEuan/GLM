"""``glm_universal.corpus.yaml`` -- the YAML schema registry and validators.

The GLM repository carries YAML manifests that mirror markdown documents
(the ``glm-study/v1`` schema in ``Rule30_GLM_Study/study/docs/``), catalogue
them (``glm-study-index/v1``), list rounds (``glm-study-rounds/v1``), and
identify the study card (``glm-study-card/v1``).  The reorganisation plan
proposes a fifth schema (``glm-study-manifest/v1``) for the semantic study
manifests of Phase R3.

This module is the **registry**: it maps each ``schema: <name>`` declaration
to a :class:`YamlSchema` instance carrying:

* a ``validator`` -- returns ``[]`` if the YAML is valid, a list of error
  strings otherwise;
* four field-path tuples -- ``written_fields``, ``generated_fields``,
  ``run_measured_fields``, ``mirror_fields`` -- that define the three
  digest modes (``written``/``rendered``/``raw``) and the mirror check.

The registry is the structural foundation for the four YAML gate checks
(see :mod:`glm_universal.corpus.checks`): schema conformance, YAML-MD
drift, YAML freshness, and constants agreement.  Until the YAML protocol
is adopted (Stage 3 of the protocol adoption, when the signoff schema
bumps to 6), the checks are gated off behind
:data:`YAML_PROTOCOL_ENABLED = False`.

*Created 29 October 2026 (Iteration 3 of the reorganisation, Stage 2 of
the protocol adoption).  This module is the passive registry; the gate
checks in ``corpus/checks.py`` read it but do not run until the flag is
flipped.*
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    FrozenSet,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
)

__all__ = [
    "YamlSchema",
    "YAML_SCHEMAS",
    "YAML_PROTOCOL_ENABLED",
    "schema_of",
    "validate",
    "yaml_files",
    "mirror_target",
    "field_paths",
]


# ---------------------------------------------------------------------------
# The protocol flag
# ---------------------------------------------------------------------------

#: Whether the YAML protocol is enabled.  ``True`` as of Stage 3 of the
#: protocol adoption (Iteration 10).  The gate checks in ``corpus/checks.py``
#: now run against every YAML file, and the corpus walk includes YAML suffixes.
YAML_PROTOCOL_ENABLED: bool = True


# ---------------------------------------------------------------------------
# The YamlSchema dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class YamlSchema:
    """A registered YAML schema.

    Attributes
    ----------
    name
        The schema identifier, as declared in the YAML's ``schema:`` field
        (e.g. ``"glm-study/v1"``).
    validator
        A callable that takes a parsed YAML mapping and returns a list of
        error strings (empty if valid).
    written_fields
        Field paths that are hand-authored (stable across re-renders).
        These are preserved in every digest mode.
    generated_fields
        Field paths that are emitted by a converter from the markdown or
        the code.  These are blanked in ``"written"`` digest mode.
    run_measured_fields
        The subset of ``generated_fields`` that quote a recomputed number
        (e.g. a figure, a word count).  These are blanked in both
        ``"written"`` and ``"rendered"`` digest modes.
    mirror_fields
        Field paths that must agree with the markdown mirror's tier-0
        block.  Used by the ``yaml_mirror_report()`` gate check.
    """

    name: str
    validator: Callable[[Mapping[str, Any]], List[str]]
    written_fields: Tuple[str, ...] = ()
    generated_fields: Tuple[str, ...] = ()
    run_measured_fields: Tuple[str, ...] = ()
    mirror_fields: Tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

def _require(data: Any, path: str, types: Tuple[type, ...],
             errors: List[str]) -> None:
    """Check that ``data`` at ``path`` is one of ``types``; append an error
    if not.  ``path`` uses dot notation (e.g. ``"tier0.question"``)."""
    obj: Any = data
    for part in path.split("."):
        if not isinstance(obj, Mapping) or part not in obj:
            errors.append(f"missing field: {path}")
            return
        obj = obj[part]
    if not isinstance(obj, types):
        errors.append(
            f"field {path} must be {types}, got {type(obj).__name__}"
        )


def _require_list_of_str(data: Any, path: str,
                          errors: List[str]) -> None:
    """Check that ``data`` at ``path`` is a list of strings."""
    obj: Any = data
    for part in path.split("."):
        if not isinstance(obj, Mapping) or part not in obj:
            errors.append(f"missing field: {path}")
            return
        obj = obj[part]
    if not isinstance(obj, list):
        errors.append(f"field {path} must be a list, got {type(obj).__name__}")
        return
    for i, item in enumerate(obj):
        if not isinstance(item, str):
            errors.append(f"field {path}[{i}] must be a string")


def _validate_glm_study_v1(data: Mapping[str, Any]) -> List[str]:
    """Validator for ``glm-study/v1`` -- the per-document manifest."""
    errors: List[str] = []
    if data.get("schema") != "glm-study/v1":
        errors.append(f"schema must be 'glm-study/v1', got {data.get('schema')!r}")
    _require(data, "id", (str,), errors)
    _require(data, "path", (str,), errors)
    _require(data, "title", (str,), errors)
    _require(data, "kind", (str,), errors)
    _require(data, "archive", (bool,), errors)
    _require(data, "tier0.question", (str,), errors)
    _require(data, "tier0.verdict", (str,), errors)
    _require(data, "tier0.figure", (str,), errors)
    _require(data, "tier0.recomputed", (str,), errors)
    # source is generated; present in real manifests but absent in templates.
    # Validate its shape IF present, but don't require it.
    source = data.get("source")
    if isinstance(source, Mapping):
        if "head" not in source:
            errors.append("field source.head missing when source is present")
        if "trailing_newline" not in source:
            errors.append("field source.trailing_newline missing when source is present")
        if "newline" not in source:
            errors.append("field source.newline missing when source is present")
    # sections is a list of dicts (present in real manifests, may be empty
    # in templates).
    sections = data.get("sections")
    if sections is not None:
        if not isinstance(sections, list):
            errors.append("field sections must be a list")
        else:
            for i, sec in enumerate(sections):
                if not isinstance(sec, Mapping):
                    errors.append(f"sections[{i}] must be a dict")
                    continue
                if "heading" not in sec:
                    errors.append(f"sections[{i}] missing 'heading'")
                if "anchor" not in sec:
                    errors.append(f"sections[{i}] missing 'anchor'")
    # derived is generated; validate its shape IF present.
    derived = data.get("derived")
    if isinstance(derived, Mapping):
        if "word_count" in derived and not isinstance(derived["word_count"], int):
            errors.append("field derived.word_count must be an int")
        if "line_count" in derived and not isinstance(derived["line_count"], int):
            errors.append("field derived.line_count must be an int")
    return errors


def _validate_glm_study_index_v1(data: Mapping[str, Any]) -> List[str]:
    """Validator for ``glm-study-index/v1`` -- the catalogue."""
    errors: List[str] = []
    if data.get("schema") != "glm-study-index/v1":
        errors.append(
            f"schema must be 'glm-study-index/v1', got {data.get('schema')!r}"
        )
    _require(data, "documents", (int,), errors)
    _require(data, "sections", (int,), errors)
    entries = data.get("entries")
    if not isinstance(entries, list):
        errors.append("field entries must be a list")
    else:
        for i, entry in enumerate(entries):
            if not isinstance(entry, Mapping):
                errors.append(f"entries[{i}] must be a dict")
                continue
            if "id" not in entry:
                errors.append(f"entries[{i}] missing 'id'")
            if "path" not in entry:
                errors.append(f"entries[{i}] missing 'path'")
            if "yaml" not in entry:
                errors.append(f"entries[{i}] missing 'yaml'")
    return errors


def _validate_glm_study_rounds_v1(data: Mapping[str, Any]) -> List[str]:
    """Validator for ``glm-study-rounds/v1`` -- the round listing."""
    errors: List[str] = []
    if data.get("schema") != "glm-study-rounds/v1":
        errors.append(
            f"schema must be 'glm-study-rounds/v1', got {data.get('schema')!r}"
        )
    _require_list_of_str(data, "sources", errors)
    rounds = data.get("rounds")
    if not isinstance(rounds, list):
        errors.append("field rounds must be a list")
    else:
        for i, rnd in enumerate(rounds):
            if not isinstance(rnd, Mapping):
                errors.append(f"rounds[{i}] must be a dict")
                continue
            if "round" not in rnd:
                errors.append(f"rounds[{i}] missing 'round'")
            if "phase" not in rnd:
                errors.append(f"rounds[{i}] missing 'phase'")
    return errors


def _validate_glm_study_card_v1(data: Mapping[str, Any]) -> List[str]:
    """Validator for ``glm-study-card/v1`` -- the study card."""
    errors: List[str] = []
    if data.get("schema") != "glm-study-card/v1":
        errors.append(
            f"schema must be 'glm-study-card/v1', got {data.get('schema')!r}"
        )
    _require(data, "id", (str,), errors)
    _require(data, "title", (str,), errors)
    _require(data, "question", (str,), errors)
    _require(data, "owner", (str,), errors)
    return errors


def _validate_glm_study_manifest_v1(data: Mapping[str, Any]) -> List[str]:
    """Validator for ``glm-study-manifest/v1`` -- the semantic manifest.

    Validates the required fields from the JSON Schema in
    ``REORGANIZATION_PLAN.md`` §5.6.1, but leniently: the id pattern is
    not enforced (studies use uppercase names like ``PI_MACHINE_STUDY``,
    not the proposed ``NNNN_Name``), phase 0 is allowed (not all studies
    have phases extracted), and faculty ``unknown`` is allowed.
    """
    errors: List[str] = []
    if data.get("schema") != "glm-study-manifest/v1":
        errors.append(
            f"schema must be 'glm-study-manifest/v1', got {data.get('schema')!r}"
        )
    # Required top-level fields.
    for f in ("id", "question", "verdict"):
        if f not in data:
            errors.append(f"missing required field: {f}")
    # phase must be a non-negative int (0 = unknown).
    if "phase" in data:
        if not isinstance(data["phase"], int) or data["phase"] < 0:
            errors.append(f"phase must be a non-negative int, got {data['phase']!r}")
    # status enum (unknown allowed).
    if "status" in data and data["status"] not in (
        "open", "measured", "closed", "archived", "negative", "unknown"
    ):
        errors.append(f"status must be one of the enums, got {data['status']!r}")
    # faculty enum (unknown allowed).
    if "faculty" in data and data["faculty"] not in (
        "derivation", "addressing", "refusal", "maintenance", "unknown"
    ):
        errors.append(f"faculty must be one of the enums, got {data['faculty']!r}")
    # file_refs.prose is required.
    fr = data.get("file_refs")
    if not isinstance(fr, Mapping) or "prose" not in fr:
        errors.append("file_refs.prose is required")
    return errors


# ---------------------------------------------------------------------------
# The registry
# ---------------------------------------------------------------------------

YAML_SCHEMAS: Dict[str, YamlSchema] = {
    "glm-study/v1": YamlSchema(
        name="glm-study/v1",
        validator=_validate_glm_study_v1,
        written_fields=(
            "schema", "id", "path", "title", "kind", "archive",
            "tier0.question", "tier0.verdict", "tier0.recomputed",
            "last_altered", "summary", "tags",
        ),
        generated_fields=(
            "source.head", "source.trailing_newline", "source.newline",
            "sections",
            "derived.links", "derived.lean_files",
            "derived.lean_modules", "derived.python_modules",
            "derived.commands", "derived.word_count", "derived.line_count",
        ),
        run_measured_fields=(
            "tier0.figure",
            "derived.word_count",
            "derived.line_count",
        ),
        mirror_fields=(
            "tier0.question", "tier0.verdict",
            "tier0.figure", "tier0.recomputed",
        ),
    ),
    "glm-study-index/v1": YamlSchema(
        name="glm-study-index/v1",
        validator=_validate_glm_study_index_v1,
        written_fields=("schema",),
        generated_fields=("with_bodies", "documents", "sections", "entries"),
        run_measured_fields=("documents", "sections"),
        mirror_fields=(),
    ),
    "glm-study-rounds/v1": YamlSchema(
        name="glm-study-rounds/v1",
        validator=_validate_glm_study_rounds_v1,
        written_fields=("schema", "sources", "before_lean"),
        generated_fields=("rounds",),
        run_measured_fields=(),
        mirror_fields=(),
    ),
    "glm-study-card/v1": YamlSchema(
        name="glm-study-card/v1",
        validator=_validate_glm_study_card_v1,
        written_fields=(
            "schema", "id", "title", "question", "owner", "contributors",
            "status", "problems", "package", "documents",
            "machine_readable", "tools",
        ),
        generated_fields=(),
        run_measured_fields=("package.unfinished_proofs",),
        mirror_fields=(),
    ),
    "glm-study-manifest/v1": YamlSchema(
        name="glm-study-manifest/v1",
        validator=_validate_glm_study_manifest_v1,
        written_fields=(
            "schema", "id", "phase", "status", "question", "verdict",
            "deciding_figure", "recomputed_by",
            "marks.declared",
            "controls", "perturbations",
            "layer.primary", "layer.resolutions_tried",
            "layer.non_edges", "layer.refinement_of",
            "predecessors", "supersedes",
            "junctions", "directives", "wobble_deps",
            "reversibility.class", "reversibility.inverse_of",
            "reversibility.inverse_lean",
            "reversibility.loss_witness", "reversibility.loss_lean",
            "faculty", "evidence", "file_refs", "follow_ups",
        ),
        generated_fields=("successors", "superseded_by"),
        run_measured_fields=(
            "deciding_figure",
            "marks.met", "marks.missed", "marks.amended",
        ),
        mirror_fields=(
            "question", "verdict", "deciding_figure", "recomputed_by",
        ),
    ),
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def schema_of(data: Mapping[str, Any]) -> Optional[YamlSchema]:
    """Look up the :class:`YamlSchema` for a parsed YAML mapping's
    ``schema:`` field, or ``None`` if unregistered."""
    name = data.get("schema")
    if not isinstance(name, str):
        return None
    return YAML_SCHEMAS.get(name)


def validate(data: Mapping[str, Any]) -> List[str]:
    """Validate a parsed YAML mapping against its declared schema.

    Returns a list of error strings (empty if valid).  If the schema is
    not declared or not registered, returns a single-element list naming
    the problem.
    """
    name = data.get("schema")
    if not isinstance(name, str):
        return ["no 'schema:' field declared"]
    schema = YAML_SCHEMAS.get(name)
    if schema is None:
        return [f"schema {name!r} is not registered"]
    return schema.validator(data)


def yaml_files(root: Optional[Path] = None) -> List[Path]:
    """Every ``.yaml``/``.yml`` file under ``root`` (default: the
    repository root), excluding ``.git``, ``.lake``, ``__pycache__``,
    ``source_material``, and the knowledge cache.

    Returns paths in sorted order for deterministic iteration.
    """
    from ..constants import REPOSITORY_ROOT
    if root is None:
        root = REPOSITORY_ROOT
    skip = {".git", ".lake", "__pycache__", ".pytest_cache",
            "source_material", "_knowledge_cache", "node_modules"}
    out: List[Path] = []
    for dirpath, dirnames, filenames in Path(root).walk():  # type: ignore[union-attr]
        dirnames[:] = [d for d in dirnames if d not in skip]
        for name in filenames:
            if name.endswith(".yaml") or name.endswith(".yml"):
                out.append(Path(dirpath) / name)
    return sorted(out)


def mirror_target(yaml_path: Path, data: Mapping[str, Any]) -> Optional[Path]:
    """The markdown file this YAML manifest mirrors, or ``None``.

    For ``glm-study/v1``, the mirror target is the ``path:`` field (a
    repo-relative markdown path).  For other schemas, returns ``None``
    (they do not mirror a single markdown file).
    """
    schema_name = data.get("schema")
    if schema_name == "glm-study/v1":
        md_path = data.get("path")
        if isinstance(md_path, str):
            from ..constants import REPOSITORY_ROOT
            # The path is relative to the Rule30_GLM_Study/ package root.
            # Try both the repo root and the Rule30_GLM_Study/ subdirectory.
            root = REPOSITORY_ROOT
            for base in (root / "Rule30_GLM_Study", root):
                candidate = base / md_path
                if candidate.exists():
                    return candidate
            # Return the expected path even if it doesn't exist (the
            # mirror check will report it as a broken link).
            return root / "Rule30_GLM_Study" / md_path
    elif schema_name == "glm-study-manifest/v1":
        fr = data.get("file_refs")
        if isinstance(fr, Mapping):
            prose = fr.get("prose")
            if isinstance(prose, str):
                from ..constants import REPOSITORY_ROOT
                return REPOSITORY_ROOT / prose
    return None


def field_paths(data: Any, prefix: str = "") -> List[str]:
    """Recursively collect every field path in a parsed YAML mapping,
    using dot notation for nested keys and ``[*]`` for list indices.

    Used by the freshness check to walk the generated fields and verify
    each is current.
    """
    out: List[str] = []
    if isinstance(data, Mapping):
        for key, value in data.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            out.append(path)
            out.extend(field_paths(value, path))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            path = f"{prefix}[{i}]"
            out.extend(field_paths(item, path))
    return out
