"""``glm_universal.reasoning.hole_reading`` -- the budget rule in the answering
path (Phase 147).

``studies/BUDGET_READING_STUDY.md`` took item 2 of ``STATUS.md`` §2.1, left by
Phase 124 (``studies/PROBE_BUDGET_STUDY.md`` §7.4): the certifying reading of
a deep hole stops on its completeness certificate or on a budget fixed in
advance, never after a run of barren starts.

The rule
--------
**At the covering radius:** no barren stop, and a budget of :data:`BUDGET`
starts (``GLM.ProbeBudget.budget_serves_every_type``).  ``GLM.BudgetReading``
proves what replacing the patience by the rule can change: wherever the
patience reading was certified, the rule is certified with the same vertex
set and so the same type (``budget_agrees``); the rule is uncertified only if
no start inside its budget carries the certificate
(``budget_refuses_only_without_cert``); and an answer can move only from a
refusal to a certified type (``patience_may_refuse``).

**Below the covering radius:** start 0 is the undithered modulator, whose
emitted point is the exact nearest lattice point, so whether a carrier is a
deep hole is decided by start 0 alone, and a carrier below the covering
radius has no Niemeier type however long it is read.  There the stop decides
only how many nearest lattice points the reading reports, and the frozen
convention (:data:`SHALLOW_PROBES` starts, a patience of
:data:`SHALLOW_PATIENCE`) is kept and named as a lower bound.

Where the rule is used
----------------------
* :func:`read_centre` -- one carrier, read under the rule;
* :func:`walked` -- a declared walk (``hole walk <n>``) read under the rule;
* :func:`census_report` -- ``report deep holes``, whose walks and
  constructions are read under the rule;
* :func:`answer` -- the ``hole`` query kind.

The frozen parameters of the measurement modules
(``deep_hole_classifier.WALK_PROBES``/``WALK_PATIENCE`` and the census
convention of ``probe_budget``) are records of earlier rounds and are left as
they were; this module is the answering path's reader.

Exactness
---------
Integers and :class:`fractions.Fraction` only.
"""

from __future__ import annotations

import re
from fractions import Fraction
from typing import Dict, Optional, Sequence, Tuple

from . import deep_holes as dh
from . import metric
from .fwht_decode import nearest_lattice_point_fwht

__all__ = [
    "BUDGET", "SHALLOW_PROBES", "SHALLOW_PATIENCE", "REFERENCE_SEED",
    "WALK_BASE", "WALK_STRIDE", "LEAN_FILE", "LEAN_THEOREMS", "HoleError",
    "walk_seed", "depth", "read_centre", "walked", "census_report",
    "parse_request", "answer",
]

#: The budget, proved enough for every type by ``GLM.ProbeBudget`` and equal
#: to ``probe_budget.BUDGET`` (a test holds the two together).
BUDGET: int = 1056
#: The frozen convention below the covering radius, where no type can come.
SHALLOW_PROBES: int = 400
SHALLOW_PATIENCE: int = 60
#: The sweep seed of a reading not made by a walk (the census's).
REFERENCE_SEED: int = 20260825
#: The declared walk seeds: walk ``n`` is seeded ``WALK_BASE + WALK_STRIDE n``.
WALK_BASE: int = 20260825
WALK_STRIDE: int = 977
#: The Lean file of the round and its theorems.
LEAN_FILE: str = "RequestProject/GLM/BudgetReading.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "certified_mono", "budget_agrees", "budget_refuses_only_without_cert",
    "patience_may_refuse")


class HoleError(ValueError):
    """A ``hole`` request the reader refuses, with its reason tag."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


def walk_seed(index: int) -> int:
    """The declared seed of walk ``index``."""
    return WALK_BASE + WALK_STRIDE * index


def depth(centre: Sequence) -> Dict[str, object]:
    """Start 0 alone: the exact nearest lattice point and the squared
    distance to it, normalised as ``deep_holes`` normalises it."""
    point = [Fraction(x) for x in centre]
    nearest = nearest_lattice_point_fwht(point).point
    raw = sum((point[i] - nearest[i]) ** 2 for i in range(24))
    normalised = raw / metric.GRIESS_SCALE
    return {"distance2": normalised, "deep": normalised == dh.COVERING_RADIUS2,
            "lattice_point": raw == 0}


def read_centre(centre: Sequence, seed: int = REFERENCE_SEED,
                known: Sequence = ()) -> Dict[str, object]:
    """One carrier read under the rule; the classification of
    :func:`deep_holes.classify_carrier` with the rule's parameters, and the
    parameters it was read with."""
    point = tuple(Fraction(x) for x in centre)
    if depth(point)["deep"]:
        probes, patience, rule = BUDGET, BUDGET, "budget"
    else:
        probes, patience, rule = SHALLOW_PROBES, SHALLOW_PATIENCE, "shallow"
    reading = dh.classify_carrier(point, probes=probes, seed=seed,
                                  patience=patience, known=known)
    reading = dict(reading)
    reading["rule"] = rule
    reading["probes"] = probes
    reading["patience"] = patience
    starts = int(reading["probe"].get("starts_run") or 0)
    reading["budget_reached"] = rule == "budget" and starts >= BUDGET
    return reading


def walked(index: int) -> Dict[str, object]:
    """Walk ``index`` of the declared seeds, its hole read under the rule
    (:func:`deep_holes.walked_hole` with the budget as both the start count
    and the patience, so no barren start ends it)."""
    return dh.walked_hole(seed=walk_seed(index), probes=BUDGET,
                          patience=BUDGET)


def census_report(walks: int = 3) -> Dict[str, object]:
    """``report deep holes`` under the rule: the census of
    :func:`deep_holes.deep_holes_report` with every reading at the covering
    radius given the budget and no barren stop."""
    return dh.deep_holes_report(walks=walks, probes=BUDGET, patience=BUDGET)


# ═════════════════════════════════════════════════════════════════════════
# THE REQUEST
# ═════════════════════════════════════════════════════════════════════════

_WALK = re.compile(r"^(?:at\s+|of\s+)?(?:the\s+)?walk\s+(?:number\s+)?"
                   r"(?P<n>\S+)$", re.I)
_OCTAD = re.compile(r"^(?:at\s+|of\s+)?(?:the\s+)?octad[- ]pair"
                    r"(?:\s+midpoint)?$", re.I)
_DODECAD = re.compile(r"^(?:at\s+|of\s+)?(?:the\s+)?dodecad[- ]triangle"
                      r"(?:\s+centroid)?$", re.I)
#: The largest declared walk index a request may name.
MAX_WALK: int = 99999


def _fraction(token: str) -> Fraction:
    try:
        return Fraction(token)
    except (ValueError, ZeroDivisionError):
        raise HoleError("malformed", f"{token!r} is not an exact "
                                     f"coordinate") from None


def parse_request(text: str) -> Dict[str, object]:
    """Read a ``hole`` request: ``walk <n>``, ``octad pair``,
    ``dodecad triangle`` or 24 exact coordinates.

    Returns ``label``, ``centre`` (``None`` for a walk, whose centre the walk
    finds), ``walk`` (the index, or ``None``) and ``construction``.
    """
    text = text.strip().rstrip("?.").strip()
    if not text:
        raise HoleError("malformed", "no walk, construction or point to read")
    walk = _WALK.match(text)
    if walk:
        token = walk.group("n")
        if not re.fullmatch(r"\d+", token):
            raise HoleError("malformed", f"a walk is named by its index, a "
                                         f"whole number, not {token!r}")
        index = int(token)
        if index > MAX_WALK:
            raise HoleError("malformed", f"walk indices run from 0 to "
                                         f"{MAX_WALK}")
        return {"label": f"walk {index} (seed {walk_seed(index)})",
                "centre": None, "walk": index, "construction": "walk + climb"}
    if _OCTAD.match(text):
        pair = dh.octad_pair_hole()
        return {"label": "the octad-pair midpoint", "walk": None,
                "centre": tuple(Fraction(x) for x in pair["center"]),
                "construction": pair["construction"]}
    if _DODECAD.match(text):
        tri = dh.dodecad_triangle_hole()
        return {"label": "the dodecad-triangle centroid", "walk": None,
                "centre": tuple(Fraction(x) for x in tri["center"]),
                "construction": tri["construction"]}
    if "," in text or re.match(r"^(?:at\s+|of\s+)?[-+]?\d", text):
        body = re.sub(r"^(?:at|of)\s+", "", text, flags=re.I)
        tokens = [t for t in re.split(r"[,\s]+", body) if t]
        point = tuple(_fraction(t) for t in tokens)
        if len(point) != 24:
            raise HoleError("dimension", f"a point has 24 coordinates; the "
                                         f"request gives {len(point)}")
        return {"label": "the given point", "centre": point, "walk": None,
                "construction": "a point given in the request"}
    raise HoleError("malformed", f"{text!r}: a hole request is `hole walk "
                                 f"<n>`, `hole octad pair`, `hole dodecad "
                                 f"triangle` or `hole <24 coordinates>`")


def answer(text: str) -> Dict[str, object]:
    """Read a ``hole`` request under the rule.

    Returns ``status`` (``"certified"``, ``"uncertified"``, ``"shallow"``,
    ``"lattice-point"`` or ``"stalled"``), the type when certified, the
    vertex set, the starts run and the parameters of the reading.
    """
    parts = parse_request(text)
    out: Dict[str, object] = {"label": parts["label"], "walk": parts["walk"],
                              "construction": parts["construction"],
                              "budget": BUDGET}
    if parts["walk"] is not None:
        run = walked(int(parts["walk"]))
        if not run.get("reached_deep_hole"):
            out.update(status="stalled", type=None, centre=run.get("center"),
                       verdict=run.get("verdict"),
                       radius2=run.get("radius2"))
            return out
        reading = dict(run["classification"])
        reading["rule"] = "budget"
        starts = int(reading["probe"].get("starts_run") or 0)
        reading["budget_reached"] = starts >= BUDGET
        centre = tuple(Fraction(x) for x in run["center"])
        seed = walk_seed(int(parts["walk"]))
    else:
        centre = parts["centre"]
        seed = REFERENCE_SEED
        reading = read_centre(centre, seed=seed)
    probe = reading["probe"]
    out.update(centre=centre, seed=seed, rule=reading["rule"],
               starts=int(probe.get("starts_run") or 0),
               vertex_count=int(probe["vertex_count"]),
               vertices=tuple(tuple(int(x) for x in v)
                              for v in probe["vertices"]),
               distance2=probe["min_distance2"],
               budget_reached=bool(reading.get("budget_reached")),
               verdict=reading["verdict"])
    if probe["at_a_lattice_point"]:
        out.update(status="lattice-point", type=None)
    elif not probe["is_deep_hole"]:
        out.update(status="shallow", type=None)
    elif reading["certified"]:
        out.update(status="certified", type=reading["niemeier_type"],
                   coxeter=reading["diagram"]["coxeter_number"])
    else:
        out.update(status="uncertified", type=None)
    return out
