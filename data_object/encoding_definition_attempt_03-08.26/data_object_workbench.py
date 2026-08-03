#!/usr/bin/env python3
"""Build and audit evidence-aware Data Objects from CSV, JSON, or JSONL.

This is the reusable workbench for subjects such as chemical elements, geometry,
or language.  It deliberately separates four things that are easy to conflate:

1. identity (what the subject is),
2. claims/observations (what a source says about it),
3. relations and state (how it is situated), and
4. optional encodings/views (ways to index or display the same information).

The script uses only Python's standard library.  Run ``python3
 data_object_workbench.py init EXAMPLE_DIR`` to create a small editable study,
then ``build`` and ``audit`` it.  The long comments are intentional: this file is
also the executable specification for the current Data Object method.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

# ---------------------------------------------------------------------------
# Stable protocol constants
# ---------------------------------------------------------------------------

PROTOCOL_NAME = "evidence-aware-data-object"
PROTOCOL_VERSION = "1.0.0"

# This is the same systematic extended binary Golay [24,12,8] convention used
# by the element experiments in this repository.  It is optional.  A subject
# does NOT become more real or more meaningful merely because it has a codeword:
# the codeword is an integrity/address representation of a declared integer ID.
GOLAY_B = (
    (0,1,1,1,1,1,1,1,1,1,1,1), (1,1,1,0,1,1,1,0,0,0,1,0),
    (1,1,0,1,1,1,0,0,0,1,0,1), (1,0,1,1,1,0,0,0,1,0,1,1),
    (1,1,1,1,0,0,0,1,0,1,1,0), (1,1,1,0,0,0,1,0,1,1,0,1),
    (1,1,0,0,0,1,0,1,1,0,1,1), (1,0,0,0,1,0,1,1,0,1,1,1),
    (1,0,0,1,0,1,1,0,1,1,1,0), (1,0,1,0,1,1,0,1,1,1,0,0),
    (1,1,0,1,1,0,1,1,1,0,0,0), (1,0,1,1,0,1,1,1,0,0,0,1),
)

# A fixed 4x6 Miracle Octad Generator coordinate convention.  Array position is
# the visible cell (row-major); value is the cyclic codeword coordinate stored
# there.  Changing this creates a new view version and must be recorded.
MOG_GRID_COORDINATES = (
    0,4,6,19,16,11,
    1,17,15,5,9,13,
    3,21,20,8,10,22,
    2,23,14,12,7,18,
)

# Adjacent MOG column pairs form three disjoint octads in this convention.  They
# partition the 24 coordinates and can be used for coarse summaries only when
# the datum genuinely has a declared 24-coordinate representation.
MOG_OCTAD_ZONES = (
    (0,4,1,17,3,21,2,23),
    (6,19,15,5,20,8,14,12),
    (16,11,9,13,10,22,7,18),
)

# Controlled statuses keep unknown data distinct from numerical zero.  Projects
# may extend this vocabulary in their manifest, but these meanings are stable.
BASE_STATUSES = {
    "observed", "measured", "calculated", "derived", "ontology_derived",
    "inferred", "imputed", "reported", "missing", "not_applicable",
}

# ---------------------------------------------------------------------------
# Canonicalization and exact integrity helpers
# ---------------------------------------------------------------------------

def canonical_json(value: Any) -> str:
    """Return deterministic JSON used for hashes and reproducible output.

    Sorting keys removes dictionary insertion-order accidents.  Compact
    separators avoid whitespace differences.  NaN and infinity are forbidden
    because they are not portable JSON data values and often hide bad inputs.
    """
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def sha256_json(value: Any) -> str:
    """Hash canonical JSON; this detects changes but does not prove truth."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def gray_encode(integer_id: int) -> int:
    """Reflected Gray encoding, useful when adjacent integer IDs are relevant."""
    return integer_id ^ (integer_id >> 1)


def bits_little_endian(number: int, width: int) -> list[int]:
    """Represent a nonnegative integer in the convention used by this project."""
    if number < 0 or number >= 2 ** width:
        raise ValueError(f"integer {number} does not fit in {width} bits")
    return [(number >> bit) & 1 for bit in range(width)]


def golay_encode(message: list[int]) -> list[int]:
    """Encode exactly twelve binary message bits as a 24-bit Golay word."""
    if len(message) != 12 or any(type(x) is not int or x not in (0, 1) for x in message):
        raise ValueError("Golay message must be exactly twelve binary integers")
    parity = [sum(message[i] * GOLAY_B[j][i] for i in range(12)) % 2
              for j in range(12)]
    return message + parity


def mog_cells(codeword: list[int]) -> list[dict[str, int]]:
    """Place a 24-bit word in the fixed MOG while retaining every coordinate."""
    if len(codeword) != 24:
        raise ValueError("a MOG codeword view requires exactly 24 values")
    return [
        {"row": cell // 6, "column": cell % 6, "coordinate": coordinate,
         "value": codeword[coordinate]}
        for cell, coordinate in enumerate(MOG_GRID_COORDINATES)
    ]

# ---------------------------------------------------------------------------
# Input handling and manifest model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Study:
    """Loaded study manifest plus its location for resolving relative paths."""
    manifest: dict[str, Any]
    path: Path

    @property
    def root(self) -> Path:
        return self.path.parent


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_study(path: Path) -> Study:
    """Load a manifest and fail early on structural mistakes."""
    raw = load_json(path)
    required = {"study_id", "object_type", "input", "identity", "claims"}
    missing = required - set(raw)
    if missing:
        raise ValueError(f"manifest missing required keys: {sorted(missing)}")
    if not isinstance(raw["claims"], list) or not raw["claims"]:
        raise ValueError("manifest claims must be a non-empty list")
    if len({c.get("predicate") for c in raw["claims"]}) != len(raw["claims"]):
        raise ValueError("each claim mapping needs a unique predicate")
    return Study(raw, path.resolve())


def read_records(path: Path, input_format: str | None = None) -> list[dict[str, Any]]:
    """Read CSV, JSON array, or JSONL without changing source values."""
    fmt = (input_format or path.suffix.lstrip(".")).lower()
    if fmt == "csv":
        with path.open(newline="", encoding="utf-8-sig") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    if fmt == "json":
        value = load_json(path)
        if not isinstance(value, list) or not all(isinstance(x, dict) for x in value):
            raise ValueError("JSON input must be an array of objects")
        return value
    if fmt in {"jsonl", "ndjson"}:
        records = []
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if line.strip():
                    value = json.loads(line)
                    if not isinstance(value, dict):
                        raise ValueError(f"JSONL line {line_number} is not an object")
                    records.append(value)
        return records
    raise ValueError(f"unsupported input format: {fmt}")


def get_path(record: dict[str, Any], dotted_path: str | None,
             default: Any = None) -> Any:
    """Read nested source fields such as ``source.page`` using dotted paths."""
    if dotted_path is None:
        return default
    current: Any = record
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current

# ---------------------------------------------------------------------------
# Typed values: preserve source text, parse only under explicit instructions
# ---------------------------------------------------------------------------

def parse_boolean(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"true", "yes", "1"}:
        return True
    if normalized in {"false", "no", "0"}:
        return False
    raise ValueError(f"cannot parse boolean value {value!r}")


def parse_typed(value: Any, value_type: str) -> Any:
    """Parse a source value according to the manifest's declared type.

    Missingness is handled before this function.  We preserve text as text,
    parse finite numbers only when requested, and never turn an empty value into
    zero.  Structured JSON values may already be objects/lists in JSON input.
    """
    if value_type == "string":
        return str(value)
    if value_type == "integer":
        if isinstance(value, bool):
            raise ValueError("boolean is not accepted as an integer")
        return int(value)
    if value_type == "number":
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("non-finite numbers are forbidden")
        return number
    if value_type == "boolean":
        return parse_boolean(value)
    if value_type == "json":
        return json.loads(value) if isinstance(value, str) else value
    if value_type == "rational_string":
        text = str(value).strip()
        if not re.fullmatch(r"[+-]?\d+(?:/[1-9]\d*)?", text):
            raise ValueError(f"invalid exact rational string: {text!r}")
        return text
    raise ValueError(f"unsupported value_type: {value_type}")


def is_missing(value: Any, missing_tokens: Iterable[Any]) -> bool:
    """Use a declared missing-token list; do not assume zero means missing."""
    if value is None:
        return True
    return any(value == token or str(value).strip() == str(token).strip()
               for token in missing_tokens)


def field_or_constant(record: dict[str, Any], mapping: dict[str, Any],
                      key: str, default: Any = None) -> Any:
    """Resolve either ``<key>_field`` or a literal ``<key>`` from a mapping."""
    field_name = mapping.get(f"{key}_field")
    return get_path(record, field_name, default) if field_name else mapping.get(key, default)

# ---------------------------------------------------------------------------
# Object construction
# ---------------------------------------------------------------------------

def build_claim(record: dict[str, Any], mapping: dict[str, Any],
                default_missing_tokens: list[Any]) -> dict[str, Any]:
    """Convert one source field into one evidence-bearing claim.

    The claim wraps the value with semantics and evidence metadata.  A value
    without a predicate, unit/scale, conditions, and provenance is often
    impossible to compare safely, so these slots always exist even when null.
    """
    predicate = mapping["predicate"]
    raw = get_path(record, mapping.get("field"))
    tokens = mapping.get("missing_tokens", default_missing_tokens)
    missing = is_missing(raw, tokens)
    value_type = mapping.get("value_type", "string")
    value = None if missing else parse_typed(raw, value_type)
    status = "missing" if missing else field_or_constant(record, mapping, "status", "reported")

    provenance = {
        "source_id": field_or_constant(record, mapping, "source_id"),
        "record_locator": field_or_constant(record, mapping, "record_locator"),
        "citation": field_or_constant(record, mapping, "citation"),
        "retrieved_at": field_or_constant(record, mapping, "retrieved_at"),
        "license": field_or_constant(record, mapping, "license"),
    }
    return {
        "predicate": predicate,
        "value": value,
        "value_type": value_type,
        "unit": field_or_constant(record, mapping, "unit"),
        "scale": field_or_constant(record, mapping, "scale"),
        "conditions": field_or_constant(record, mapping, "conditions"),
        "uncertainty": field_or_constant(record, mapping, "uncertainty"),
        "status": status,
        "provenance": provenance,
        # Preserve the exact source token for auditability.  This is especially
        # useful for rounded decimals, rational strings, and categorical labels.
        "source_value_text": None if raw is None else str(raw),
    }


def build_relations(record: dict[str, Any], mappings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build typed directed relations; direction and role remain explicit."""
    relations = []
    for mapping in mappings:
        target = get_path(record, mapping.get("target_field"))
        if target is None or str(target).strip() == "":
            continue
        relations.append({
            "predicate": mapping["predicate"],
            "target_canonical_id": str(target),
            "direction": mapping.get("direction", "outgoing"),
            "role": mapping.get("role"),
            "provenance": {"source_id": mapping.get("source_id")},
        })
    return relations


def make_identity_view(integer_id: int, use_gray: bool) -> dict[str, Any]:
    """Create an optional exact 12→24 integrity view for a bounded integer ID."""
    encoded = gray_encode(integer_id) if use_gray else integer_id
    message = bits_little_endian(encoded, 12)
    codeword = golay_encode(message)
    return {
        "view_type": "golay_mog_identity",
        "view_version": "extended-golay-systematic-v1/mog-cyclic-v1",
        "integer_id": integer_id,
        "message_transform": "reflected_gray" if use_gray else "binary",
        "message_bits_little_endian": message,
        "golay_codeword": codeword,
        "mog_cells": mog_cells(codeword),
        "octad_zones": [list(zone) for zone in MOG_OCTAD_ZONES],
        "interpretation": "Integrity/address view only; it does not add subject facts.",
    }


def make_channel_view(claims: list[dict[str, Any]], manifest: dict[str, Any]) -> dict[str, Any] | None:
    """Index up to 24 declared predicates in MOG cells without packing values.

    The actual typed values stay in ``claims``.  Cells contain references, so a
    floating-point measurement is never silently quantized to one bit and units
    are never discarded.  Predicate order is manifest order and therefore
    versionable and reproducible.
    """
    if not manifest.get("views", {}).get("claim_mog_index", False):
        return None
    if len(claims) > 24:
        raise ValueError("claim_mog_index supports at most 24 claims; use multiple named layers")
    cells = []
    for cell_index, claim in enumerate(claims):
        coordinate = MOG_GRID_COORDINATES[cell_index]
        cells.append({"row": cell_index // 6, "column": cell_index % 6,
                      "coordinate": coordinate,
                      "claim_ref": claim["predicate"],
                      "missing": claim["status"] == "missing"})
    return {
        "view_type": "mog_claim_index",
        "view_version": "manifest-order-v1/mog-cyclic-v1",
        "cells": cells,
        "interpretation": "Index of claim references, not a physical embedding.",
    }


def build_object(record: dict[str, Any], study: Study) -> dict[str, Any]:
    """Build one Data Object while preserving clear epistemic boundaries."""
    manifest = study.manifest
    identity = manifest["identity"]
    canonical_value = get_path(record, identity["field"])
    if canonical_value is None or str(canonical_value).strip() == "":
        raise ValueError(f"identity field {identity['field']!r} is missing")
    canonical_id = f"{identity.get('namespace', manifest['object_type'])}:{canonical_value}"
    label = get_path(record, identity.get("label_field"), str(canonical_value))

    claims = [build_claim(record, mapping, manifest.get("missing_tokens", ["", "NA", "null"]))
              for mapping in manifest["claims"]]
    relations = build_relations(record, manifest.get("relations", []))

    # Hash the stable subject payload, not build timestamps or output ordering.
    identity_payload = {"canonical_id": canonical_id,
                        "object_type": manifest["object_type"]}
    subject = {
        "canonical_id": canonical_id,
        "object_type": manifest["object_type"],
        "label": str(label),
        "aliases": get_path(record, identity.get("aliases_field"), []),
    }
    views: list[dict[str, Any]] = []
    identity_view = manifest.get("views", {}).get("golay_mog_identity")
    if identity_view:
        integer_id = int(get_path(record, identity_view.get("integer_field", identity["field"])))
        views.append(make_identity_view(integer_id, identity_view.get("gray", True)))
    channel_view = make_channel_view(claims, manifest)
    if channel_view:
        views.append(channel_view)

    return {
        "protocol": {"name": PROTOCOL_NAME, "version": PROTOCOL_VERSION},
        "study_id": manifest["study_id"],
        "schema_version": manifest.get("schema_version", 1),
        "subject": subject,
        "identity_integrity": {
            "canonical_payload_sha256": sha256_json(identity_payload),
            "hash_scope": "canonical_id and object_type only",
        },
        "claims": claims,
        "relations": relations,
        "state": get_path(record, manifest.get("state_field"), {}),
        "representations": views,
        "boundary": manifest.get("boundary", {
            "note": "This object describes only its declared subject and state; related events or contexts require linked objects."
        }),
    }


def build_study(manifest_path: Path, output_path: Path | None = None) -> tuple[Path, list[dict[str, Any]]]:
    """Build all records and reject duplicate canonical identities."""
    study = load_study(manifest_path)
    input_spec = study.manifest["input"]
    source_path = (study.root / input_spec["path"]).resolve()
    records = read_records(source_path, input_spec.get("format"))
    objects = [build_object(record, study) for record in records]
    ids = [obj["subject"]["canonical_id"] for obj in objects]
    if len(ids) != len(set(ids)):
        duplicates = sorted({item for item in ids if ids.count(item) > 1})
        raise ValueError(f"duplicate canonical identities: {duplicates}")

    target = output_path or (study.root / study.manifest.get("output", "objects.jsonl"))
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        for obj in objects:
            handle.write(canonical_json(obj) + "\n")
    return target, objects

# ---------------------------------------------------------------------------
# Auditing: structural checks are not empirical validation
# ---------------------------------------------------------------------------

def audit_objects(objects: list[dict[str, Any]]) -> dict[str, Any]:
    """Audit completeness and integrity without claiming scientific accuracy."""
    errors: list[str] = []
    warnings: list[str] = []
    ids: list[str] = []
    status_counts: dict[str, int] = {}
    predicate_counts: dict[str, int] = {}
    missing_count = 0

    for object_index, obj in enumerate(objects):
        prefix = f"object[{object_index}]"
        try:
            subject = obj["subject"]
            canonical_id = subject["canonical_id"]
            ids.append(canonical_id)
            expected_hash = sha256_json({"canonical_id": canonical_id,
                                         "object_type": subject["object_type"]})
            if obj["identity_integrity"]["canonical_payload_sha256"] != expected_hash:
                errors.append(f"{prefix}: identity hash mismatch")
        except (KeyError, TypeError) as exc:
            errors.append(f"{prefix}: malformed required structure ({exc})")
            continue

        seen_predicates: set[str] = set()
        for claim in obj.get("claims", []):
            predicate = claim.get("predicate")
            if not predicate:
                errors.append(f"{prefix}: claim lacks predicate")
                continue
            if predicate in seen_predicates:
                errors.append(f"{prefix}: duplicate predicate {predicate!r}")
            seen_predicates.add(predicate)
            predicate_counts[predicate] = predicate_counts.get(predicate, 0) + 1
            status = claim.get("status")
            status_counts[str(status)] = status_counts.get(str(status), 0) + 1
            if status not in BASE_STATUSES:
                warnings.append(f"{prefix}/{predicate}: unfamiliar status {status!r}")
            if status == "missing":
                missing_count += 1
                if claim.get("value") is not None:
                    errors.append(f"{prefix}/{predicate}: missing claim has non-null value")
            elif claim.get("value") is None:
                errors.append(f"{prefix}/{predicate}: non-missing claim has null value")
            provenance = claim.get("provenance", {})
            if status not in {"missing", "not_applicable"} and not provenance.get("source_id"):
                warnings.append(f"{prefix}/{predicate}: no source_id")

        for view in obj.get("representations", []):
            if view.get("view_type") == "golay_mog_identity":
                codeword = view.get("golay_codeword", [])
                if len(codeword) != 24 or any(bit not in (0, 1) for bit in codeword):
                    errors.append(f"{prefix}: invalid 24-bit Golay representation")
                if sorted(cell.get("coordinate") for cell in view.get("mog_cells", [])) != list(range(24)):
                    errors.append(f"{prefix}: MOG view is not a coordinate permutation")

    if len(ids) != len(set(ids)):
        errors.append("canonical identities are not unique")
    return {
        "protocol": {"name": PROTOCOL_NAME, "version": PROTOCOL_VERSION},
        "object_count": len(objects),
        "unique_identity_count": len(set(ids)),
        "claim_count": sum(predicate_counts.values()),
        "missing_claim_count": missing_count,
        "status_counts": dict(sorted(status_counts.items())),
        "predicate_counts": dict(sorted(predicate_counts.items())),
        "errors": errors,
        "warnings": warnings,
        "structurally_valid": not errors,
        "interpretation": (
            "Structural validity means the objects follow declared identity, typing, "
            "missingness, provenance, and encoding rules. It does not establish that "
            "source claims are true or that an optional geometry predicts reality."
        ),
    }


def read_objects(path: Path) -> list[dict[str, Any]]:
    return read_records(path, "jsonl")

# ---------------------------------------------------------------------------
# Example-study generator
# ---------------------------------------------------------------------------

def init_example(directory: Path) -> None:
    """Create a neutral geometry example that users can copy for any domain."""
    directory.mkdir(parents=True, exist_ok=True)
    records = [
        {"id": 1, "name": "unit square", "sides": 4, "area": "1/1",
         "definition": "four equal sides and four right angles", "source": "example:def:1"},
        {"id": 2, "name": "equilateral triangle", "sides": 3, "area": None,
         "definition": "three equal sides", "source": "example:def:2"},
    ]
    with (directory / "records.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(canonical_json(record) + "\n")
    manifest = {
        "study_id": "geometry-example-v1",
        "schema_version": 1,
        "object_type": "geometric_figure_definition",
        "input": {"path": "records.jsonl", "format": "jsonl"},
        "output": "objects.jsonl",
        "missing_tokens": ["", "NA", "null"],
        "identity": {"namespace": "figure", "field": "id", "label_field": "name"},
        "claims": [
            {"predicate": "side_count", "field": "sides", "value_type": "integer",
             "unit": "count", "status": "ontology_derived", "source_id_field": "source"},
            {"predicate": "area_in_unit_scale", "field": "area", "value_type": "rational_string",
             "unit": "unit^2", "conditions": {"normalization": "declared unit scale"},
             "status": "calculated", "source_id_field": "source"},
            {"predicate": "definition_text", "field": "definition", "value_type": "string",
             "status": "reported", "source_id_field": "source"},
        ],
        "views": {
            "golay_mog_identity": {"integer_field": "id", "gray": True},
            "claim_mog_index": True,
        },
        "boundary": {
            "note": "Definitions are distinct from a drawn instance, measurement, proof, or transformation event."
        },
    }
    (directory / "study.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (directory / "README.txt").write_text(
        "Edit study.json and records.jsonl, then run:\n"
        "python3 data_object_workbench.py build study.json\n"
        "python3 data_object_workbench.py audit objects.jsonl\n",
        encoding="utf-8",
    )

# ---------------------------------------------------------------------------
# Command-line interface
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    init_parser = commands.add_parser("init", help="create an editable example study")
    init_parser.add_argument("directory", type=Path)

    build_parser = commands.add_parser("build", help="build JSONL objects from a manifest")
    build_parser.add_argument("manifest", type=Path)
    build_parser.add_argument("--output", type=Path)
    build_parser.add_argument("--audit-output", type=Path)

    audit_parser = commands.add_parser("audit", help="audit an existing object JSONL file")
    audit_parser.add_argument("objects", type=Path)
    audit_parser.add_argument("--output", type=Path)

    args = parser.parse_args(argv)
    if args.command == "init":
        init_example(args.directory)
        print(f"Created example study in {args.directory}")
        return 0

    if args.command == "build":
        target, objects = build_study(args.manifest, args.output)
        report = audit_objects(objects)
        audit_target = args.audit_output or target.with_suffix(".audit.json")
        audit_target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"objects": str(target), "audit": str(audit_target),
                          "object_count": len(objects),
                          "structurally_valid": report["structurally_valid"]}, indent=2))
        return 0 if report["structurally_valid"] else 1

    objects = read_objects(args.objects)
    report = audit_objects(objects)
    if args.output:
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["structurally_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
