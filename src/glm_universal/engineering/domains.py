"""``glm_universal.engineering.domains`` -- the domain wheels W11-W15.

Phase 157's domain wheels: W11 (uniform motion), W12 (density, volume,
amount), W13 (mass-spring oscillator), W14 (inductors, LC circuit),
W15 (charge and energy over time).  The five wheels, their ten declared
junctions with W01-W10, the four non-identities, and the demand census.

The wheel definitions and junction tables live in
:mod:`glm_universal.wheels`; this module is the study/measurement surface
that :mod:`glm_universal.tools`' ``domains`` subcommand and the tier-0
contract for ``studies/DOMAIN_WHEELS_STUDY.md`` expect.

*Created 29 October 2026 (Iteration 6, Phase R2).  The wheel definitions
and junction tables are faithful to ``studies/DOMAIN_WHEELS_STUDY.md``
§2.2-2.3.  The ``domains_report`` function is a working stub that returns
the report dict shape with all marks ``False``; the stored census JSON
does not exist, so the census is reported as stale.  When the full
session infrastructure is restored, run ``tools domains --write`` to
take the census.*
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from ..wheels import DOMAIN_WHEELS, JUNCTIONS, NON_IDENTITIES, ALIASES

__all__ = [
    "DOMAIN_WHEELS", "DOMAIN_JUNCTIONS", "DOMAIN_NON_IDENTITIES", "ALIASES",
    "domains_report", "write_census", "census_state",
]


_HERE = Path(__file__).resolve().parent
_CENSUS_PATH = _HERE / "_data" / "domains.json"


#: The ten Phase-157 domain junctions (W01-W15), as a dict keyed by
#: ``"W5/W11"``-style strings (the format the CLI handler reads).
#: Transcribed from :mod:`glm_universal.wheels.junctions.domain`.
def _format_junctions() -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for (a, b), names in JUNCTIONS.items():
        # Only include junctions that involve at least one domain wheel (W11+).
        if a >= "W11" or b >= "W11":
            key = f"{a}/{b}"
            out[key] = {"names": list(names)}
    return out


DOMAIN_JUNCTIONS: Dict[str, Dict[str, Any]] = _format_junctions()


#: The domain non-identities, in the same ``"W13/W14"`` format.
def _format_non_identities() -> Dict[str, str]:
    out: Dict[str, str] = {}
    for (a, b), reason in NON_IDENTITIES.items():
        if a >= "W11" or b >= "W11":
            key = f"{a}/{b}"
            out[key] = reason
    return out


DOMAIN_NON_IDENTITIES: Dict[str, str] = _format_non_identities()


def _wheel_dicts() -> List[Dict[str, Any]]:
    """The five domain wheels as serialisable dicts."""
    return [
        {"id": w.id, "title": w.title, "axioms": list(w.axioms)}
        for w in DOMAIN_WHEELS
    ]


def _battery_tally() -> Dict[str, int]:
    """The battery tally: 23 answered, 9 refused, 0 wrong (declared).

    *Stub:* returns the declared shape with zeros.
    """
    return {"answered": 0, "refused": 0, "wrong": 0, "questions": 0}


def domains_report(census: bool = False) -> Dict[str, Any]:
    """The domain-wheels report.

    * ``census=False`` (default): reads the stored census (if fresh) and
      returns the report with the marks.  If no stored census exists,
      returns the report with marks ``False``.
    * ``census=True``: takes the census afresh (the full union census
      over the 222 evaluation cases).  *Stub:* returns the same shape
      with zero counts.

    The report dict shape matches what :mod:`glm_universal.tools`'s
    ``_domains`` handler reads.
    """
    marks: Dict[str, bool] = {m: False for m in ("D1", "D2", "D3", "D4", "D5")}
    report: Dict[str, Any] = {
        "wheels": _wheel_dicts(),
        "junctions": DOMAIN_JUNCTIONS,
        "battery": {"tally": _battery_tally()},
        "marks": marks,
        "met": sum(1 for v in marks.values() if v),
        "taken": len(marks),
    }
    if census:
        report["census"] = {
            "gained": 0, "gained_right": 0,
            "naive_new": 0, "naive_refused": 0,
        }
        report["census_fresh"] = False
    else:
        stored = _read_census()
        if stored is not None:
            report["census"] = stored.get("census", {
                "gained": 0, "gained_right": 0,
                "naive_new": 0, "naive_refused": 0,
            })
            report["census_fresh"] = True
            report["marks"] = stored.get("marks", marks)
            report["met"] = sum(1 for v in report["marks"].values() if v)
            report["taken"] = len(report["marks"])
        else:
            report["census_fresh"] = False
    return report


def write_census() -> str:
    """Take the census afresh and write it to ``_data/domains.json``.

    *Stub:* writes a minimal census with zero counts.
    """
    _CENSUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "wheels": _wheel_dicts(),
        "junctions": DOMAIN_JUNCTIONS,
        "battery": {"tally": _battery_tally()},
        "census": {
            "gained": 0, "gained_right": 0,
            "naive_new": 0, "naive_refused": 0,
        },
        "marks": {m: False for m in ("D1", "D2", "D3", "D4", "D5")},
    }
    text = json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    _CENSUS_PATH.write_text(text, encoding="utf-8")
    return str(_CENSUS_PATH)


def census_state() -> Dict[str, Any]:
    """``{"present", "fresh", "verdict"}`` for the stored census."""
    if not _CENSUS_PATH.exists():
        return {"present": False, "fresh": False, "verdict": "absent"}
    return {"present": True, "fresh": True, "verdict": "current"}


def _read_census() -> Dict[str, Any] | None:
    """Read the stored census, or ``None`` if absent."""
    if not _CENSUS_PATH.exists():
        return None
    try:
        return json.loads(_CENSUS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
