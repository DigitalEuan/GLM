"""``glm_universal.engineering.oscillator_junction`` -- the W09/W13 junction.

Phase 158's measurement of the W09 (wave kinematics) / W13 (mass-spring
oscillator) junction.  Four variants were tried under one declared rule;
variant B (``rate_only``: join ``frequency`` only, split ``angle``) was
chosen and ships.

The variant definitions live in
:mod:`glm_universal.wheels.junctions.oscillator`; this module is the
study/measurement surface that :mod:`glm_universal.tools`' ``oscjunction``
subcommand and the tier-0 contract for
``studies/OSCILLATOR_JUNCTION_STUDY.md`` expect.

*Created 29 October 2026 (Iteration 6, Phase R2).  The variant
definitions are faithful to ``studies/OSCILLATOR_JUNCTION_STUDY.md``.
The ``report`` and ``measure`` functions are working stubs that return
the report dict shape with all marks ``False``; the stored measurement
JSON does not exist.  When the full session infrastructure is restored,
run ``tools oscjunction --write`` to take the four censuses.*
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

from ..wheels.junctions.oscillator import (
    VARIANTS, VARIANT_READINGS, SHIPPED, LEAN_FILE, LEAN_THEOREMS,
)

__all__ = [
    "VARIANTS", "VARIANT_READINGS", "SHIPPED", "LEAN_FILE", "LEAN_THEOREMS",
    "measure", "write", "report",
]


_HERE = Path(__file__).resolve().parent
_DATA_PATH = _HERE / "_data" / "oscillator_junction.json"


def measure(variant: str) -> Dict[str, Any]:
    """Measure one variant's census.

    *Stub:* returns the measurement shape with zero counts and marks
    ``False``.
    """
    if variant not in VARIANTS:
        raise KeyError(f"unknown variant {variant!r}")
    marks = {m: False for m in ("O1", "O2", "O3")}
    return {
        "variant": variant,
        "battery": {"answered": 0, "refused": 0, "wrong": 0},
        "lost": 0,
        "not_entailed": 0,
        "entailed_labelled": 0,
        "entailed_other": 0,
        "preservation_questions": 0,
        "shipped_answers": 0,
        **marks,
    }


def write(measurements: Dict[str, Dict[str, Any]]) -> str:
    """Write the four variant measurements to ``_data/oscillator_junction.json``."""
    _DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "variants": {v: measurements[v] for v in VARIANTS if v in measurements},
        "chosen": SHIPPED,
        "lean": {"file": LEAN_FILE, "theorems": list(LEAN_THEOREMS)},
    }
    text = json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    _DATA_PATH.write_text(text, encoding="utf-8")
    return str(_DATA_PATH)


def report() -> Dict[str, Any]:
    """The oscillator-junction report.

    Reads the stored measurement (if present) and returns the report dict
    shape that :mod:`glm_universal.tools`'s ``_oscjunction`` handler
    reads.  If no stored measurement exists, returns ``{"measured": False}``.
    """
    stored = _read()
    if stored is None:
        return {"measured": False, "chosen": SHIPPED}
    marks: Dict[str, Dict[str, Any]] = {}
    for v in VARIANTS:
        if v in stored.get("variants", {}):
            marks[v] = stored["variants"][v]
        else:
            marks[v] = measure(v)
    return {
        "measured": True,
        "fresh": True,
        "chosen": stored.get("chosen", SHIPPED),
        "preservation_questions": marks.get(SHIPPED, {}).get("preservation_questions", 0),
        "shipped_answers": marks.get(SHIPPED, {}).get("shipped_answers", 0),
        "marks": marks,
    }


def _read() -> Dict[str, Any] | None:
    """Read the stored measurement, or ``None`` if absent."""
    if not _DATA_PATH.exists():
        return None
    try:
        return json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
