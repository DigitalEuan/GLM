"""``glm_universal.reasoning.hole_reports_l5`` -- the configuration reading
``L5`` asked each earlier deep-hole round's question (Phase 149).

``studies/HOLE_REPORTS_L5_STUDY.md`` gives each of the three deep-hole reports
that still named a hole only with their own rounds' readings -- ``report hole
classifier``, ``report hole ladder`` and ``report hole failures`` -- a
**clause**: the round's answer is kept verbatim (a record is not rewritten),
and the clause says what ``L5`` answers to the question that round asked.

The three readings
------------------
* :func:`classifier_reading` -- the first round's question was whether the
  arrivals name the hole, and its stopping rule the sanity query (the same
  hole under a bare seed change).  ``L5``'s answer: the ten seed queries
  through the answer rule of :mod:`configuration_classifier`, and all 44
  queries.
* :func:`ladder_reading` -- the escalation gate is that every reference
  recognises itself under a seed change.  ``L5``'s answer: the gate at every
  ensemble size the configuration reading was measured at
  (:func:`configuration_reading.cell` on the stored ensembles), the smallest
  size that passes, and the sizes where it passes with ``rho >= 1`` (the
  global criterion is sufficient, not necessary --
  ``GLM.HoleReportsL5.criterion_not_necessary``).
* :func:`failures_reading` -- each of the joint reading's four failures
  through the answer rule at the same cell (1920 starts), and ``L5``'s own
  per-type criterion there.

Nothing here decodes a lattice point: the readings use the stores that already
exist (:mod:`configuration_queries`, :mod:`share_ensemble`,
:mod:`deep_hole_escalation`), so all three take well under a second.  When a
store is absent or stale the reading says so (``available`` False) rather
than give a figure taken from code that has moved (D4).

:func:`classifier_clause`, :func:`ladder_clause` and :func:`failures_clause`
are the clause texts of §7.2, and :func:`classifier_expected`,
:func:`ladder_expected` and :func:`failures_expected` the ``l5_*`` keys a
report states beside its own, for its column-3 template to recompute.

Exactness
---------
Integers and :class:`fractions.Fraction` only; ``rho`` is rendered by
:func:`deep_hole_failures.rounded` (integer rounding).

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from
``studies/HOLE_REPORTS_L5_STUDY.md`` (§§0-7, the clause texts of §7.2),
``MASTER_PLAN.md`` Phase 149, the CLI handler ``tools hole-reports-l5``, and
the public APIs of ``configuration_classifier``, ``configuration_queries``,
``configuration_reading``, ``share_ensemble`` and ``deep_hole_escalation``.*

Created 31 October 2026.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional

__all__ = [
    "LEAN_FILE", "LEAN_THEOREMS", "JOINT_FAILURES", "FAILURE_STARTS",
    "classifier_reading", "ladder_reading", "failures_reading", "readings",
    "classifier_clause", "ladder_clause", "failures_clause",
    "classifier_expected", "ladder_expected", "failures_expected",
    "clauses",
]

#: The Lean file of the round (namespace ``GLM.HoleReportsL5``).
LEAN_FILE: str = "RequestProject/GLM/HoleReportsL5.lean"
LEAN_THEOREMS = ("rule_fires_of_resolvesAt", "rule_sound", "gate_of_rule",
                 "criterion_not_necessary")

#: The joint reading's failures as the failure round recorded them
#: (``studies/DEEP_HOLE_FAILURE_STUDY.md``); the reading re-derives them
#: from the stored query rows and reports the names it found.
JOINT_FAILURES = ("hole 5 · translation", "hole 7 · translation",
                  "hole 9 · negation", "hole 9 · permutation")

#: The cell the failure round read at, and where L5's criterion is asked.
FAILURE_STARTS: int = 1920


def _unavailable(reason: str) -> Dict[str, object]:
    return {"available": False, "reason": reason}


def _classified() -> Optional[Dict[str, object]]:
    """The 44 queries through the answer rule against the ten references at
    1920 starts, or ``None`` when the stored profiles are not current."""
    from . import configuration_classifier as cc
    from . import configuration_queries as cq
    data = cq.current()
    if data is None:
        return None
    table = cc.reference_table(data)
    if not table:
        return None
    return cc.classify_queries(table, data)


# ═════════════════════════════════════════════════════════════════════════
# 1.  THE THREE READINGS
# ═════════════════════════════════════════════════════════════════════════

def classifier_reading() -> Dict[str, object]:
    """The first round's question at ``L5``: the sanity query (the ten seed
    queries named as themselves) and the 44 queries."""
    from . import configuration_queries as cq
    run = _classified()
    if run is None:
        return _unavailable("the query profiles (configuration_queries) are "
                            "absent or stale")
    rows = list(run["rows"])
    seed = [r for r in rows if r["kind"] == "seed"]
    seed_correct = sum(1 for r in seed if r["verdict"] == "correct")
    within = [r for r in rows if r["within_own_radius"]]
    return {
        "available": True, "starts": cq.STARTS,
        "seed_queries": len(seed), "seed_correct": seed_correct,
        "sanity_holds": bool(seed) and seed_correct == len(seed),
        "queries": run["queries"], "answered": run["answered"],
        "correct": run["correct"], "wrong": run["wrong"],
        "refused": run["refused"],
        "within_radius": len(within),
        "within_answered": sum(1 for r in within
                               if r["answer"] is not None),
        "false_absences": run["false_absences"],
        "absences": run["absences"],
    }


def ladder_reading() -> Dict[str, object]:
    """The escalation gate at ``L5`` at every stored ensemble size."""
    from . import configuration_reading as cr
    from . import deep_hole_escalation as de
    from . import share_ensemble as se
    data = se.current()
    if data is None:
        return _unavailable("the share ensembles (share_ensemble) are absent "
                            "or stale")
    cells = [cr.cell(data, int(n)) for n in data["sizes"]]
    passing = [c for c in cells if c["q0"] == c["gate"]]
    joint_first: Optional[int] = None
    esc = de.current()
    if esc is not None:
        best = esc.get("decision", {}).get("best") or {}
        if best.get("q0") == esc.get("decision", {}).get("gate"):
            joint_first = int(best["starts"])
    return {
        "available": True,
        "sizes": len(cells),
        "starts": [c["starts"] for c in cells],
        "passing": len(passing),
        "smallest_passing": (min(c["starts"] for c in passing)
                             if passing else None),
        "passes_without_criterion": [c["starts"] for c in passing
                                     if not c["ratio_below_one"]],
        "joint_first_passing": joint_first,
        "cells": [{"starts": c["starts"], "q0": c["q0"], "gate": c["gate"],
                   "ratio": c["ratio"],
                   "ratio_below_one": c["ratio_below_one"],
                   "locally_certified": c["locally_certified"]}
                  for c in cells],
    }


def failures_reading() -> Dict[str, object]:
    """The joint reading's failures through ``L5``'s answer rule, and
    ``L5``'s per-type criterion at the failure round's cell."""
    from . import configuration_reading as cr
    from . import share_ensemble as se
    run = _classified()
    if run is None:
        return _unavailable("the query profiles (configuration_queries) are "
                            "absent or stale")
    data = se.current()
    if data is None:
        return _unavailable("the share ensembles (share_ensemble) are absent "
                            "or stale")
    failed = [r for r in run["rows"] if not r["joint_correct"]]
    cell = cr.cell(data, FAILURE_STARTS)
    return {
        "available": True, "starts": FAILURE_STARTS,
        "joint_failures": len(failed),
        "names": [r["query"] for r in failed],
        "names_as_recorded": sorted(r["query"] for r in failed)
                             == sorted(JOINT_FAILURES),
        "l5_correct": sum(1 for r in failed if r["verdict"] == "correct"),
        "l5_wrong": sum(1 for r in failed if r["verdict"] == "wrong"),
        "l5_refused": sum(1 for r in failed if r["verdict"] == "refused"),
        "types": cell["gate"],
        "locally_certified": cell["locally_certified"],
        "rho": cell["ratio"],
        "rho_below_one": bool(cell["ratio_below_one"]),
    }


def readings() -> Dict[str, Dict[str, object]]:
    """All three readings."""
    return {"classifier": classifier_reading(), "ladder": ladder_reading(),
            "failures": failures_reading()}


# ═════════════════════════════════════════════════════════════════════════
# 2.  THE CLAUSES AND THE KEYS THEY STATE
# ═════════════════════════════════════════════════════════════════════════

def _rho(value: Optional[Fraction]) -> str:
    from . import deep_hole_failures as dhf
    return "n/a" if value is None else dhf.rounded(value, 4)


def classifier_clause(r: Dict[str, object]) -> Optional[str]:
    """The clause ``report hole classifier`` ends with (§7.2)."""
    if not r.get("available"):
        return None
    holds = "holds" if r["sanity_holds"] else "does not hold"
    return (f"read at L5 (the configuration reading, {r['starts']} starts) "
            f"under its answer rule the sanity query {holds} -- "
            f"{r['seed_correct']} of {r['seed_queries']} seed queries named "
            f"as themselves -- and the {r['queries']} queries are answered "
            f"{r['correct']} correctly, {r['wrong']} wrongly and "
            f"{r['refused']} refused")


def ladder_clause(r: Dict[str, object]) -> Optional[str]:
    """The clause ``report hole ladder`` ends with (§7.2)."""
    if not r.get("available"):
        return None
    if r["smallest_passing"] is None:
        return (f"read at L5 the gate passes at 0 of {r['sizes']} ensemble "
                f"sizes")
    text = (f"read at L5 the gate passes at {r['passing']} of {r['sizes']} "
            f"ensemble sizes, first at {r['smallest_passing']} starts")
    if r.get("joint_first_passing") is not None:
        text += (f" where the joint reading needed "
                 f"{r['joint_first_passing']}")
    loose = list(r["passes_without_criterion"])
    if loose:
        sizes = ", ".join(str(n) for n in loose)
        text += (f", and at {sizes} starts it passes with rho at or above "
                 f"one, so the global criterion is sufficient, not necessary")
    return text


def failures_clause(r: Dict[str, object]) -> Optional[str]:
    """The clause ``report hole failures`` ends with (§7.2)."""
    if not r.get("available"):
        return None
    return (f"read at L5 under its answer rule the {r['joint_failures']} "
            f"failures are answered {r['l5_correct']} correctly, "
            f"{r['l5_wrong']} wrongly and {r['l5_refused']} refused, and at "
            f"{r['starts']} starts L5 meets the criterion for "
            f"{r['locally_certified']} of {r['types']} types "
            f"(rho = {_rho(r['rho'])})")


def classifier_expected(r: Dict[str, object]) -> Dict[str, str]:
    """The ``l5_*`` keys ``report hole classifier`` states."""
    if not r.get("available"):
        return {"l5": "unavailable"}
    return {"l5_seed_correct": str(r["seed_correct"]),
            "l5_seed_queries": str(r["seed_queries"]),
            "l5_correct": str(r["correct"]), "l5_wrong": str(r["wrong"]),
            "l5_refused": str(r["refused"])}


def ladder_expected(r: Dict[str, object]) -> Dict[str, str]:
    """The ``l5_*`` keys ``report hole ladder`` states."""
    if not r.get("available"):
        return {"l5": "unavailable"}
    return {"l5_sizes": str(r["sizes"]), "l5_passing": str(r["passing"]),
            "l5_smallest_passing": str(r["smallest_passing"]),
            "l5_passes_without_criterion":
                ",".join(str(n) for n in r["passes_without_criterion"])}


def failures_expected(r: Dict[str, object]) -> Dict[str, str]:
    """The ``l5_*`` keys ``report hole failures`` states."""
    if not r.get("available"):
        return {"l5": "unavailable"}
    return {"l5_failures_correct": str(r["l5_correct"]),
            "l5_joint_failures": str(r["joint_failures"]),
            "l5_certified_types": str(r["locally_certified"]),
            "l5_types": str(r["types"]), "l5_rho": _rho(r["rho"])}


def clauses() -> List[Optional[str]]:
    """The three clause texts, in report order."""
    r = readings()
    return [classifier_clause(r["classifier"]), ladder_clause(r["ladder"]),
            failures_clause(r["failures"])]
