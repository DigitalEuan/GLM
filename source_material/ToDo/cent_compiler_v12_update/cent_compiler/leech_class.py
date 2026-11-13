"""Exact class-word audit for a declared Leech basis and move corpus.

The audit implements the computable fragment of the 24-bit class isomorphism:
for a declared row-HNF basis ``B`` of a lattice, a lattice vector ``x`` has
unique coordinates ``c`` with ``x = c B``; the class word is the parity vector
``(c_0 mod 2, ..., c_{n-1} mod 2)``.  Class words compose by XOR.

This module does not construct the Leech lattice, its metric or quadratic form,
a Griess product, a Monster action, a Lean certificate or a codebook optimizer.
The basis and moves are caller-declared evidence.  The audit is deliberately
separate from the operation matrix: a class word is an index, not a compute or
carry method.
"""
from __future__ import annotations

import json
import random
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA = "cent-leech-class/1"
MAX_DIMENSION = 24


class LeechClassError(ValueError):
    """The declared basis, vector or corpus is malformed or inconsistent."""


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise LeechClassError(f"{label} must be an integer")
    return value


def validate_basis(basis: Sequence[Sequence[int]]) -> tuple[tuple[int, ...], ...]:
    """Validate a square row-HNF basis with positive pivots and zero right tails."""
    if not isinstance(basis, Sequence) or isinstance(basis, (str, bytes)):
        raise LeechClassError("basis must be a list of rows")
    rows = []
    for index, raw_row in enumerate(basis):
        if not isinstance(raw_row, Sequence) or isinstance(raw_row, (str, bytes)):
            raise LeechClassError(f"basis row {index} must be a list")
        rows.append(tuple(_integer(value, f"basis[{index}]") for value in raw_row))
    dimension = len(rows)
    if not 1 <= dimension <= MAX_DIMENSION:
        raise LeechClassError(
            f"basis dimension must be between 1 and {MAX_DIMENSION}, got {dimension}"
        )
    if any(len(row) != dimension for row in rows):
        raise LeechClassError("basis must be square")
    for index, row in enumerate(rows):
        if row[index] <= 0:
            raise LeechClassError(
                f"basis row {index} must have a positive pivot at column {index}"
            )
        if any(row[column] != 0 for column in range(index + 1, dimension)):
            raise LeechClassError(
                f"basis row {index} must have zeros to the right of its pivot"
            )
    return tuple(rows)


def _coords(vector: Sequence[int], basis: tuple[tuple[int, ...], ...]) -> tuple[int, ...]:
    dimension = len(basis)
    if len(vector) != dimension:
        raise LeechClassError(
            f"vector dimension {len(vector)} does not match basis dimension {dimension}"
        )
    values = tuple(_integer(value, "vector coordinate") for value in vector)
    coordinates = [0] * dimension
    for index in range(dimension - 1, -1, -1):
        remainder = values[index] - sum(
            coordinates[column] * basis[column][index]
            for column in range(index + 1, dimension)
        )
        pivot = basis[index][index]
        if remainder % pivot:
            raise LeechClassError(
                f"vector is not in the declared lattice: coordinate {index} "
                f"has remainder {remainder % pivot} modulo {pivot}"
            )
        coordinates[index] = remainder // pivot
    for column in range(dimension):
        reconstructed = sum(
            coordinates[row] * basis[row][column] for row in range(dimension)
        )
        if reconstructed != values[column]:
            raise LeechClassError("basis solve did not reconstruct the vector")
    return tuple(coordinates)


def basis_coords(vector: Sequence[int], basis: Sequence[Sequence[int]]) -> tuple[int, ...]:
    """Return the unique integer coordinates of ``vector`` in a row-HNF basis."""
    return _coords(vector, validate_basis(basis))


def _class_word(vector: Sequence[int], basis: tuple[tuple[int, ...], ...]) -> int:
    coordinates = _coords(vector, basis)
    return sum((coordinate & 1) << index for index, coordinate in enumerate(coordinates))


def class_word(vector: Sequence[int], basis: Sequence[Sequence[int]]) -> int:
    """Return the parity class word of a lattice vector."""
    return _class_word(vector, validate_basis(basis))


def xor_compose(left: int, right: int) -> int:
    """Compose two class words by coordinate-wise XOR."""
    return _integer(left, "left class word") ^ _integer(right, "right class word")


def f2_rank(words: Sequence[int]) -> int:
    """Return the rank of the class words over F2."""
    pivots: dict[int, int] = {}
    for raw_word in words:
        word = _integer(raw_word, "class word")
        while word:
            pivot = word.bit_length() - 1
            if pivot in pivots:
                word ^= pivots[pivot]
            else:
                pivots[pivot] = word
                break
    return len(pivots)


def _fraction_text(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def load_basis(path: str | Path) -> tuple[tuple[int, ...], ...]:
    """Load a basis from a JSON list or an object with a ``basis`` key."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise LeechClassError(f"cannot read basis {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise LeechClassError(f"basis is not valid JSON: {exc}") from exc
    if isinstance(data, Mapping):
        data = data.get("basis")
    if not isinstance(data, list):
        raise LeechClassError("basis JSON must be a list of rows or an object with 'basis'")
    return validate_basis(data)


def audit(
    basis: Sequence[Sequence[int]],
    moves: Mapping[str, Any],
    *,
    composition_samples: int = 5000,
    seed: int = 0,
    provenance: str = "",
) -> dict[str, Any]:
    """Audit class words for a declared basis and move mapping.

    ``moves`` maps move ids to either a vector or an object with a ``vector``
    key.  Composition is checked on a deterministic sample of move pairs; the
    report says so rather than claiming an exhaustive check.
    """
    validated = validate_basis(basis)
    dimension = len(validated)
    if not isinstance(moves, Mapping) or not moves:
        raise LeechClassError("moves must be a non-empty object keyed by move id")
    if composition_samples < 0:
        raise LeechClassError("composition_samples must be non-negative")
    vectors: list[tuple[int, ...]] = []
    for move_id, raw in moves.items():
        vector = raw.get("vector") if isinstance(raw, Mapping) else raw
        if vector is None:
            raise LeechClassError(f"move {move_id!r} has no vector")
        if not isinstance(vector, Sequence) or isinstance(vector, (str, bytes)):
            raise LeechClassError(f"move {move_id!r} vector must be a list")
        if len(vector) != dimension:
            raise LeechClassError(
                f"move {move_id!r} vector dimension {len(vector)} "
                f"does not match basis dimension {dimension}"
            )
        vectors.append(tuple(_integer(value, f"move {move_id!r}") for value in vector))

    words = [_class_word(vector, validated) for vector in vectors]
    distinct_words = len(set(words))
    rank = f2_rank(words)
    zero_class_moves = sum(1 for word in words if word == 0)
    sample_size = min(int(composition_samples), len(vectors) * len(vectors))
    rng = random.Random(seed)
    passed = 0
    for _ in range(sample_size):
        left = vectors[rng.randrange(len(vectors))]
        right = vectors[rng.randrange(len(vectors))]
        total = tuple(a + b for a, b in zip(left, right))
        if _class_word(total, validated) == (
            _class_word(left, validated) ^ _class_word(right, validated)
        ):
            passed += 1

    determinant = 1
    for index, row in enumerate(validated):
        determinant *= row[index]
    class_space = 1 << dimension
    composition_ok = sample_size > 0 and passed == sample_size
    checks = [
        {
            "name": "row-HNF basis",
            "status": "pass",
            "detail": f"{dimension}x{dimension}, determinant {determinant}",
        },
        {
            "name": "class words",
            "status": "pass",
            "detail": f"{len(vectors)} moves, {distinct_words} distinct class words",
        },
        {
            "name": "F2 rank",
            "status": "pass",
            "detail": f"rank {rank} over F2",
        },
        {
            "name": "XOR composition",
            "status": "pass" if composition_ok else "gap",
            "detail": f"{passed}/{sample_size} sampled move pairs",
        },
    ]
    gaps = [
        "class-index only; no lattice metric/q-form, Griess product or Monster action",
        "basis and moves are caller-declared; this audit does not construct the Leech lattice",
    ]
    if sample_size == 0:
        gaps.append("no composition sample was requested")
    return {
        "schema": SCHEMA,
        "status": "ok" if composition_ok else "gap",
        "provenance": str(provenance or ""),
        "dimension": dimension,
        "basis_determinant": determinant,
        "moves_decoded": len(vectors),
        "distinct_moves": len(set(vectors)),
        "distinct_class_words": distinct_words,
        "class_space_size": class_space,
        "observed_class_fraction": _fraction_text(
            Fraction(distinct_words, class_space)
        ),
        "f2_rank": rank,
        "zero_class_moves": zero_class_moves,
        "composition": {
            "sample_size": sample_size,
            "passed": passed,
            "rule": "phi(x+y) = phi(x) XOR phi(y)",
            "detail": "deterministic sample of move pairs; not exhaustive",
        },
        "checks": checks,
        "gaps": gaps,
        "claim": (
            "exact class-word audit over a declared row-HNF basis; it is not a "
            "Griess product, Monster action, Lean certificate or codebook optimizer"
        ),
    }


def render_text(report: Mapping[str, Any]) -> str:
    """Render a class-word audit for the terminal."""
    lines = [
        "LEECH CLASS-WORD AUDIT",
        "=" * 72,
        f"schema: {report.get('schema')}",
        f"status: {report.get('status')}",
        (
            f"basis: {report.get('dimension')}x{report.get('dimension')} "
            f"determinant={report.get('basis_determinant')}"
        ),
        (
            f"moves: {report.get('moves_decoded')} decoded, "
            f"{report.get('distinct_moves')} distinct"
        ),
        (
            f"class words: {report.get('distinct_class_words')} distinct of "
            f"{report.get('class_space_size')} "
            f"({report.get('observed_class_fraction')})"
        ),
        f"F2 rank: {report.get('f2_rank')}",
        f"zero-class moves: {report.get('zero_class_moves')}",
    ]
    composition = report.get("composition") or {}
    lines.append(
        "composition: {}/{} sampled pairs ({})".format(
            composition.get("passed"),
            composition.get("sample_size"),
            composition.get("rule"),
        )
    )
    for gap in report.get("gaps") or []:
        lines.append(f"gap: {gap}")
    if report.get("provenance"):
        lines.append(f"provenance: {report['provenance']}")
    lines.append(f"claim: {report.get('claim')}")
    return "\n".join(lines)


__all__ = [
    "LeechClassError",
    "MAX_DIMENSION",
    "SCHEMA",
    "audit",
    "basis_coords",
    "class_word",
    "f2_rank",
    "load_basis",
    "render_text",
    "validate_basis",
    "xor_compose",
]
