"""Layered resolution: turn a structured failure into an explicit outcome.

The exact core never substitutes a value for an error.  When an attempt fails
it raises :class:`~cent_compiler.exact.CentError`; this controller records the
failure and moves on to the next candidate or the next fidelity layer.  Nothing
is caught silently: every failure is preserved in the returned trace.

The five layer names mirror the fidelity cascade used by the v2 compiler
(``ideal -> parasitic -> thermal -> quantum -> fabricated``), but this module is
deliberately independent of :mod:`cent_compiler.hypothesis_bridge`: a caller
supplies the layer parameters and the runner, so the controller can be used for
an evaluator program, a port network or a cost model alike.

Outcome vocabulary
------------------
``converged``   every layer accepted the selected candidate
``diverging``   no candidate survived some layer (the arrow diverges)
``refused``     the first failure was on the first layer and ``strict`` was set
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping, Sequence

from .exact import CentError, ErrorCode

DEFAULT_LAYER_NAMES: tuple[str, ...] = (
    "ideal",
    "parasitic",
    "thermal",
    "quantum",
    "fabricated",
)


@dataclass(frozen=True)
class Layer:
    """A fidelity layer: a name plus the parameters it imposes on an attempt."""

    name: str
    overrides: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "overrides", dict(self.overrides))

    def as_dict(self) -> dict[str, Any]:
        return {"layer": self.name, "overrides": dict(self.overrides)}


@dataclass(frozen=True)
class Candidate:
    """A named implementation tried by the controller."""

    name: str
    payload: Any = None

    def as_dict(self) -> dict[str, Any]:
        return {"candidate": self.name}


@dataclass(frozen=True)
class Attempt:
    """One (candidate, layer) attempt."""

    candidate: str
    layer: str
    status: str  # "converged" | "raised"
    value: Any = None
    error: Mapping[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "candidate": self.candidate,
            "layer": self.layer,
            "status": self.status,
        }
        if self.error is not None:
            out["error"] = dict(self.error)
        return out


@dataclass(frozen=True)
class Resolution:
    """The result of a layered resolution."""

    status: str
    value: Any
    candidate: str | None
    attempts: tuple[Attempt, ...]

    @property
    def converged(self) -> bool:
        return self.status == "converged"

    @property
    def failures(self) -> tuple[Attempt, ...]:
        return tuple(a for a in self.attempts if a.status == "raised")

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "candidate": self.candidate,
            "attempts": [a.as_dict() for a in self.attempts],
        }


def default_layers() -> tuple[Layer, ...]:
    return tuple(Layer(name) for name in DEFAULT_LAYER_NAMES)


def resolve(
    candidates: Sequence[Candidate | str],
    run: Callable[[Any, Layer], Any],
    layers: Iterable[Layer] | None = None,
    *,
    strict: bool = False,
) -> Resolution:
    """Try each candidate through each layer, keeping the full failure trace.

    ``run(candidate_payload, layer)`` performs one attempt and must raise
    :class:`CentError` on failure.  At each layer the first candidate that
    converges is selected; if every candidate fails the resolution stops with
    status ``diverging``.  With ``strict`` a failure of the first candidate on
    the first layer returns ``refused`` immediately.
    """
    cands = tuple(Candidate(c, c) if isinstance(c, str) else c for c in candidates)
    if not cands:
        raise CentError(ErrorCode.INVALID_INPUT, "resolution needs at least one candidate")
    layer_seq = tuple(default_layers() if layers is None else layers)
    if not layer_seq:
        raise CentError(ErrorCode.INVALID_INPUT, "resolution needs at least one layer")

    attempts: list[Attempt] = []
    selected: Candidate | None = None
    value: Any = None

    for layer_index, layer in enumerate(layer_seq):
        converged_here = False
        for cand in cands:
            try:
                produced = run(cand.payload, layer)
            except CentError as exc:
                attempts.append(
                    Attempt(cand.name, layer.name, "raised", error=exc.as_dict())
                )
                if strict and layer_index == 0 and cand is cands[0]:
                    return Resolution("refused", None, None, tuple(attempts))
                continue
            attempts.append(Attempt(cand.name, layer.name, "converged", value=produced))
            selected, value, converged_here = cand, produced, True
            break
        if not converged_here:
            return Resolution("diverging", None, None, tuple(attempts))

    return Resolution("converged", value, selected.name if selected else None, tuple(attempts))


def require_converged(resolution: Resolution, where: str | None = None) -> Any:
    """Return the value of a converged resolution or raise a structured error."""
    if resolution.converged:
        return resolution.value
    last = resolution.failures[-1] if resolution.failures else None
    raise CentError(
        ErrorCode.APPROXIMATION_UNPROVED,
        f"resolution {resolution.status}: no candidate survived the fidelity cascade",
        where,
        detail=resolution.as_dict() if last is None else {"trace": resolution.as_dict()},
    )
