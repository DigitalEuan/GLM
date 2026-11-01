"""``glm_universal.engineering.domains_reread`` -- the post-hoc reading of
the census of the union (``studies/DOMAIN_WHEELS_STUDY.md`` §7.3; not a
mark).

Two places where the census code is narrower than the declaration's words:
*in-wheel* is declared as "some single wheel derives it", but the census asks
only wheels holding all three names; and the labels are declared to match
"any target" of a relation, but the census compares up to a *positive*
multiple, which a rearrangement with the other side as target negates.
:func:`reread` reads a census's gained rows with both words literally: a
gained answer the union gives from one wheel alone moves to in-wheel, and a
label matches up to any non-zero multiple.  Phase 158
(``OSCILLATOR_JUNCTION_STUDY.md`` §2.2) grades every variant's census in this
reading.

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from studies/DOMAIN_WHEELS_STUDY.md
§7.3 and studies/OSCILLATOR_JUNCTION_STUDY.md §2.2.  The census itself
(:func:`glm_universal.engineering.domains.census`) carries the same reading
as its ``post_hoc`` entry.*
"""
from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Sequence

from . import domains as dmn

__all__ = ["reread", "stored_reread"]


def reread(census: Mapping[str, Any],
           labels: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """The post-hoc reading of a census that carries its gained ``rows``
    (``labels`` default: ``DOMAIN_LABELS`` of ``evaluation/domain_cases.py``;
    without them ``right`` is ``None``)."""
    if labels is None:
        labels = dmn._labels()
    rows = list(census.get("rows", []))
    kept = [r for r in rows if not r.get("one_wheel")]
    right = None
    wrong_rows = None
    if labels is not None:
        def ok(r):
            return any(dmn.same_relation_any(f"{r['t']} = {r['formula']}", lab)
                       for lab in labels)
        right = sum(1 for r in kept if ok(r))
        wrong_rows = sorted({(r["t"], r["formula"], "+".join(r["wheels"]))
                             for r in kept if not ok(r)})
    return {"gained": len(rows), "one_wheel": len(rows) - len(kept),
            "reread_gained": len(kept), "right": right,
            "labelled": labels is not None,
            "not_right": None if wrong_rows is None else [list(w) for w in wrong_rows]}


def stored_reread() -> Optional[Dict[str, Any]]:
    """The post-hoc reading of the stored census
    (``engineering/_data/domains.json``), or ``None`` when none is stored or
    it does not carry its rows."""
    stored = dmn._read_census()
    if not stored or "rows" not in stored.get("census", {}):
        return None
    out = reread(stored["census"])
    out["fresh"] = dmn.census_state()["fresh"]
    return out
