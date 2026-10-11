"""``glm_universal.reasoning.lattice_completion`` -- the lattice round's
readings and marks (Phase 123): part A's configuration reading over all 23
Niemeier types, and the marks of all three parts.

``studies/LATTICE_COMPLETION_STUDY.md`` pre-registered three parts and their
marks.  The measurements are stored by three modules, each beside the digest
of its sources: :mod:`hole_census` (the 23 references and the ensembles of
the thirteen new ones), :mod:`configuration_queries` (the 44 queries' ``L5``
profiles) and :mod:`empty_rungs` (the candidates and the filling), and the frozen-path
comparison by :mod:`frozen_path` (B5).  This
module only reads them:

* :func:`hole_census_report` -- part A: the stages, the control (A2), and the
  ``L5`` cell over all 23 references at every size (A3, A4);
* :func:`lattice_completion_report` -- every mark of §3, with the classifier
  of :mod:`configuration_classifier` (B) and the filling of
  :mod:`empty_rungs` (C).

Exactness
---------
Integers and :class:`~fractions.Fraction` only; nothing here decodes.
"""

from __future__ import annotations

from collections import Counter
from fractions import Fraction
from typing import Dict, List, Optional, Tuple

from . import configuration_classifier as cc
from . import configuration_reading as cr
from . import empty_rungs as er
from . import frozen_path as fp
from . import hole_census as hc
from . import patience_census as pc
from . import share_ensemble as se

__all__ = [
    "LEAN_MODULE", "STATISTICS_TRIED", "all_records", "cell", "control_rows",
    "merged", "hole_census_report", "lattice_completion_report",
]

#: The Lean file of the round (mark L1).
LEAN_MODULE: str = "RequestProject/GLM/LatticeCompletion.lean"

#: Phase 122's 44 statistics, plus six ``L5`` cells (A), two classifier
#: readings (B) and five candidate audits (C).
STATISTICS_TRIED: int = cr.STATISTICS_TRIED + len(hc.SIZES) + 2 + len(er.CANDIDATES)


# ═════════════════════════════════════════════════════════════════════════
# 1.  PART A -- L5 OVER ALL 23
# ═════════════════════════════════════════════════════════════════════════

def all_records(data: Dict[str, object], starts: int
                ) -> Tuple[Tuple[str, Tuple, Tuple], ...]:
    """Per type, in the catalogue's order, both seeds' multisets at
    ``starts``: the ten from :mod:`share_ensemble`, the rest from here."""
    old = se.current()
    rows: Dict[str, Tuple[Tuple, Tuple]] = {}
    if old is not None:
        for hole in old["holes"]:
            rows[str(hole["label"])] = (se.multiset(hole["reference"], starts),
                                        se.multiset(hole["sanity"], starts))
    for hole in data["holes"]:
        rows[str(hole["label"])] = (se.multiset(hole["reference"], starts),
                                    se.multiset(hole["sanity"], starts))
    return tuple((label, rows[label][0], rows[label][1])
                 for label in cr.NIEMEIER_TYPES if label in rows)


def cell(data: Dict[str, object], starts: int) -> Dict[str, object]:
    """``Q0``, ``W``, ``B``, ``rho`` and the per-hole criterion for ``L5``
    over every reference at ``starts``, as :func:`configuration_reading.cell`
    computes them for the ten."""
    table = all_records(data, starts)
    refs = [(label, cr.configuration_profile(ref)) for label, ref, _ in table]
    sanity = [(label, cr.configuration_profile(san)) for label, _, san in table]
    passes = 0
    worst: Optional[Fraction] = None
    worst_label = None
    rows: List[Dict[str, object]] = []
    for index, (label, profile) in enumerate(sanity):
        distances = [(name, cr.configuration_distance(profile, reference))
                     for name, reference in refs]
        own = distances[index][1]
        best = min(d for _n, d in distances)
        winners = [n for n, d in distances if d == best]
        correct = len(winners) == 1 and winners[0] == label
        passes += int(correct)
        if worst is None or own > worst:
            worst, worst_label = own, label
        nearest_other = min(cr.configuration_distance(refs[index][1], other)
                            for name, other in refs if name != label)
        local = None if nearest_other == 0 else 2 * own / nearest_other
        rows.append({"label": label, "own_distance": own,
                     "nearest_other_reference": nearest_other,
                     "local_ratio": local,
                     "locally_certified": local is not None and local < 1,
                     "correct": correct})
    separation: Optional[Fraction] = None
    closest = None
    for i in range(len(refs)):
        for j in range(i + 1, len(refs)):
            d = cr.configuration_distance(refs[i][1], refs[j][1])
            if separation is None or d < separation:
                separation, closest = d, (refs[i][0], refs[j][0])
    ratio = (None if not separation or worst is None
             else 2 * worst / separation)
    return {"starts": starts, "q0": passes, "gate": len(table),
            "spread": worst, "spread_label": worst_label,
            "separation": separation, "closest_pair": closest,
            "ratio": ratio, "ratio_below_one": ratio is not None and ratio < 1,
            "locally_certified": sum(1 for r in rows if r["locally_certified"]),
            "rows": tuple(rows)}


def control_rows(data: Dict[str, object]) -> Tuple[Dict[str, object], ...]:
    """A2: at the top size, per new hole and seed, the arrival set is the
    certified vertex set and its diagram has the label's keys."""
    declared = {str(e["type"]): set(tuple(v) for v in e["vertices"])
                for e in data["census"]["entries"]}
    rows = []
    for hole in data["holes"]:
        label = str(hole["label"])
        for role in ("reference", "sanity"):
            record = se.multiset(hole[role], hc.TOP)
            shares, r2 = cr.arrivals(record)
            points = sorted(shares)
            keys = Counter(cr.vertex_keys(points, r2)) if r2 is not None \
                else Counter()
            same_set = set(points) == declared[label]
            same_diagram = keys == cr.expected_keys(label)
            rows.append({"label": label, "seed": role,
                         "arrivals": len(points),
                         "declared": len(declared[label]),
                         "vertex_set": same_set, "diagram": same_diagram,
                         "holds": same_set and same_diagram})
    return tuple(rows)


def merged(data: Dict[str, object]) -> Optional[Dict[str, object]]:
    """The census with the post-hoc centres of :mod:`patience_census` in
    place of the entries it left uncertified, or ``None`` if the follow-up
    is absent or stale."""
    extra = pc.current()
    if extra is None:
        return None
    kept = [e for e in extra["entries"] if e["certified"]]
    entries = [e for e in data["census"]["entries"] if e["certified"]] + kept
    census = dict(data["census"])
    census["entries"] = tuple(entries)
    return {"census": census,
            "holes": tuple(data["holes"]) + tuple(extra["holes"])}


def _post_hoc(data: Dict[str, object]) -> Dict[str, object]:
    """The cells over the census and the follow-up together (post hoc)."""
    both = merged(data)
    if both is None:
        return {"available": False, "reason": (
            "the post-hoc follow-up is absent or stale; re-take it with "
            "python3 -m glm_universal.tools patience-census --write")}
    extra = pc.current()
    cells = tuple(cell(both, n) for n in hc.SIZES)
    top = cells[-1]
    control = control_rows(both)
    reached = len(both["census"]["old"]) + len(both["census"]["entries"])
    return {"available": True, "probes": extra["probes"],
            "patience": extra["patience"], "entries": extra["entries"],
            "types_reached": reached, "cells": cells, "control": control,
            "control_holds": sum(1 for r in control if r["holds"]),
            "marks": {"A1": reached == len(cr.NIEMEIER_TYPES),
                      "A2": bool(control) and all(r["holds"] for r in control),
                      "A3": top["q0"] == top["gate"] == len(cr.NIEMEIER_TYPES)
                            and bool(top["ratio_below_one"]),
                      "A4": top["locally_certified"] == top["gate"]
                            == len(cr.NIEMEIER_TYPES)}}


def hole_census_report() -> Dict[str, object]:
    """The census, the control and every ``L5`` cell over all 23."""
    data = hc.current()
    if data is None:
        return {"available": False, "reason": (
            "the hole census is absent or stale; re-take it with python3 -m "
            "glm_universal.tools hole-census --write")}
    entries = data["census"]["entries"]
    cells = tuple(cell(data, n) for n in hc.SIZES)
    top = cells[-1]
    control = control_rows(data)
    certified = [e for e in entries if e["certified"]]
    reached = len(data["census"]["old"]) + len(certified)
    by_stage: Dict[str, int] = {}
    for e in certified:
        by_stage[str(e["stage"])] = by_stage.get(str(e["stage"]), 0) + 1
    return {
        "available": True, "sizes": hc.SIZES, "top": hc.TOP,
        "types_reached": reached, "catalogue": len(cr.NIEMEIER_TYPES),
        "by_stage": by_stage, "entries": entries,
        "walks_run": data["census"]["walks_run"],
        "pilot_walks_run": data["census"]["pilot_walks_run"],
        "unreached": data["census"]["unreached"],
        "control": control,
        "control_holds": sum(1 for r in control if r["holds"]),
        "cells": cells,
        "marks": {"A1": reached == len(cr.NIEMEIER_TYPES),
                  "A2": bool(control) and all(r["holds"] for r in control),
                  "A3": top["q0"] == top["gate"] == len(cr.NIEMEIER_TYPES)
                        and bool(top["ratio_below_one"]),
                  "A4": top["locally_certified"] == top["gate"]
                        == len(cr.NIEMEIER_TYPES)},
        "post_hoc": _post_hoc(data),
    }


# ═════════════════════════════════════════════════════════════════════════
# 2.  EVERY MARK
# ═════════════════════════════════════════════════════════════════════════

def lattice_completion_report() -> Dict[str, object]:
    """The marks of all three parts, from the three stores."""
    census = hole_census_report()
    classifier = cc.configuration_classifier_report()
    rungs = er.current()
    marks: Dict[str, Optional[bool]] = {"L1": True}   # the build; pinned by tests
    for key in ("A1", "A2", "A3", "A4"):
        marks[key] = census["marks"][key] if census["available"] else None
    for key in ("B1", "B2", "B3", "B4"):
        marks[key] = (classifier["marks"][key] if classifier["available"]
                      else None)
    frozen = fp.frozen_path_report()
    marks["B5"] = frozen["holds"] if frozen["available"] else None
    marks["B6"] = (classifier["marks"]["B6"] if classifier["available"]
                   else None)
    for key in ("C1", "C2", "C3"):
        marks[key] = rungs["marks"][key] if rungs is not None else None
    return {"lean": LEAN_MODULE, "census": census, "classifier": classifier,
            "rungs": rungs, "frozen_path": frozen, "marks": marks,
            "marks_met": sum(1 for v in marks.values() if v),
            "marks_scored": sum(1 for v in marks.values() if v is not None),
            "statistics_tried": STATISTICS_TRIED}
