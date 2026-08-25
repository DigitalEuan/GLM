"""The capability-probe harness.

A *system test* asks whether a mechanism still does what it did yesterday.  A
**capability probe** asks a different question: *can the machine do this at
all, and if not, exactly where does it stop?*  The answer to the second
question is the useful one, because a located boundary is a work item and a
passing system test is not.

Every probe therefore declares, before it runs:

``question``
    the capability in one sentence, in the language of someone using the
    machine rather than of someone maintaining it;
``expectation``
    ``"holds"`` or ``"breaks"`` -- what is believed *now*.  A probe that
    breaks where it was expected to hold is a regression; a probe that holds
    where it was expected to break is a capability that has been won, and both
    are surfaced as ``surprises`` rather than buried in a diff.

and returns, after it runs:

``verdict``
    ``"holds"``, ``"breaks"`` or ``"error"``.  ``"breaks"`` is a *successful*
    probe: the limit was found and located.  ``"error"`` means the probe
    itself fell over and its evidence cannot be trusted.
``boundary``
    where the capability stops, stated exactly -- a weight, a level, a
    denominator, a certificate.
``evidence``
    the exact quantities behind the verdict, as strings, so the report can be
    compared key by key across runs.

Nothing here scores anything.  A capability that breaks is not a failure to be
hidden; it is the map of what to build next.
"""

from __future__ import annotations

import time
import traceback
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple

__all__ = [
    "Outcome", "Probe", "holds", "breaks", "register", "probe",
    "probe_names", "get_probe", "run_probe", "run_all", "capability_report",
    "AREAS",
]

#: The parts of the machine a probe can be about.  A probe must name one, so
#: the report can say which areas are solid and which are thin.
AREAS: Tuple[str, ...] = (
    "reals", "dynamic carrier", "substrate", "carriers", "layers",
    "algebra", "runtime", "semantics", "scale",
)


@dataclass(frozen=True)
class Outcome:
    """What a probe found."""

    verdict: str
    boundary: str
    evidence: Mapping[str, str] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, object]:
        return {"verdict": self.verdict, "boundary": self.boundary,
                "evidence": dict(self.evidence)}


def holds(boundary: str, **evidence: object) -> Outcome:
    """The capability is there.  ``boundary`` says how far it was pushed."""
    return Outcome("holds", boundary,
                   {key: str(value) for key, value in evidence.items()})


def breaks(boundary: str, **evidence: object) -> Outcome:
    """The capability stops.  ``boundary`` says exactly where."""
    return Outcome("breaks", boundary,
                   {key: str(value) for key, value in evidence.items()})


@dataclass(frozen=True)
class Probe:
    """A declared capability and the code that puts it to the test."""

    name: str
    area: str
    question: str
    expectation: str
    run: Callable[[], Outcome]

    def __post_init__(self) -> None:
        if self.area not in AREAS:
            raise ValueError(f"Probe {self.name}: unknown area {self.area!r}")
        if self.expectation not in ("holds", "breaks"):
            raise ValueError(
                f"Probe {self.name}: expectation must be 'holds' or 'breaks'")


_REGISTRY: Dict[str, Probe] = {}


def register(item: Probe) -> Probe:
    if item.name in _REGISTRY:
        raise ValueError(f"register: duplicate probe {item.name!r}")
    _REGISTRY[item.name] = item
    return item


def probe(name: str, area: str, question: str, expectation: str
          ) -> Callable[[Callable[[], Outcome]], Callable[[], Outcome]]:
    """Decorator form of :func:`register`."""

    def decorate(function: Callable[[], Outcome]) -> Callable[[], Outcome]:
        register(Probe(name, area, question, expectation, function))
        return function

    return decorate


def probe_names() -> Tuple[str, ...]:
    return tuple(sorted(_REGISTRY))


def get_probe(name: str) -> Probe:
    if name not in _REGISTRY:
        raise KeyError(f"get_probe: unknown probe {name!r}; known probes are "
                       f"{', '.join(probe_names())}")
    return _REGISTRY[name]


def run_probe(name: str) -> Dict[str, object]:
    """Run one probe.  A probe that raises is reported, never propagated."""
    item = get_probe(name)
    started = time.monotonic()
    try:
        outcome = item.run()
    except Exception as error:                      # noqa: BLE001 - reported
        outcome = Outcome("error", f"{type(error).__name__}: {error}",
                          {"traceback": traceback.format_exc(limit=3)})
    elapsed = time.monotonic() - started
    return {
        "name": item.name,
        "area": item.area,
        "question": item.question,
        "expectation": item.expectation,
        "seconds": round(elapsed, 3),
        "surprise": outcome.verdict != item.expectation,
        **outcome.as_dict(),
    }


def run_all(names: Optional[Sequence[str]] = None) -> Tuple[Dict[str, object], ...]:
    chosen = tuple(names) if names is not None else probe_names()
    return tuple(run_probe(name) for name in chosen)


def capability_report(names: Optional[Sequence[str]] = None) -> Dict[str, object]:
    """Run the probes and lay out what the machine can and cannot do.

    The report is deliberately shaped around the *boundaries*: the capability
    that holds is one line, the capability that stops gets the place where it
    stops.
    """
    results = run_all(names)
    by_area: Dict[str, Dict[str, int]] = {}
    for result in results:
        bucket = by_area.setdefault(
            str(result["area"]), {"holds": 0, "breaks": 0, "error": 0})
        bucket[str(result["verdict"])] += 1

    boundaries: List[Dict[str, str]] = [
        {"name": str(r["name"]), "area": str(r["area"]),
         "question": str(r["question"]), "boundary": str(r["boundary"])}
        for r in results if r["verdict"] == "breaks"
    ]
    surprises = [str(r["name"]) for r in results if r["surprise"]]
    errors = [str(r["name"]) for r in results if r["verdict"] == "error"]

    return {
        "probes": len(results),
        "holds": sum(1 for r in results if r["verdict"] == "holds"),
        "breaks": len(boundaries),
        "errors": len(errors),
        "error_names": tuple(errors),
        "surprises": tuple(surprises),
        "by_area": {area: dict(counts) for area, counts in sorted(by_area.items())},
        "boundaries": tuple(boundaries),
        "results": results,
    }
