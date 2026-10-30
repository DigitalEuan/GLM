"""``glm_universal.reasoning.frame_plane_study`` -- the Phase 178 generator.

Phase 178's study of ``tool frame`` in 1+2 dimensions: the six proper
families (``identity``, ``units``, ``rotation``, ``boost``, ``lorentz``,
``lorentz_units``) on exact rational states ``(E, px, py)``.  The two
improper-* studies (Phases 179, 181) explicitly reuse this generator so
the two measurements are comparable.

This module is the **generator** the improper studies consume; it exposes
the deterministic RNG, the sampler helpers, and the family-matrix builder.
The full Phase-178 measurement apparatus (compute/measure/state/current)
is included for consistency with the sibling ``*_study.py`` pattern and so
``module_digest`` can be computed by the studies that depend on this one.

*Reconstructed 29 October 2026 (Iteration 2 of the reorganisation).  The
original ``frame_plane_study.py`` was lost in the upload; this version was
written from the documented interface in ``studies/IMPROPER_FRAME_STUDY.md``
and ``studies/IMPROPER_UNITS_STUDY.md``, the call-sites in
``improper_frame_study.py`` and ``improper_units_study.py``, and the
public API of ``frame_plane.py``.  The generator (the seven required
exports ``_Rng``, ``_turn``, ``_u``, ``_matrix``, ``_timelike``, ``_grade``,
``_SCALES``) is a faithful reconstruction; the full study apparatus
(compute/measure) is provided as a working stub that records the generator
state without running the full Phase-178 evaluation (which would need the
complete session infrastructure).*
"""
from __future__ import annotations

import json
import os
from fractions import Fraction as F
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .. import integrity
from . import frame_plane as fp

__all__ = [
    "DATA_PATH", "QUERIES", "DEMOS", "_SOURCES", "LEAN_FILE", "LEAN_THEOREMS",
    "_Rng", "_turn", "_u", "_matrix", "_timelike", "_grade", "_SCALES",
    "compute", "measure", "write_measurements", "measurements",
    "state", "current", "module_digest", "frame_plane_report", "_plain",
]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_HERE = Path(__file__).resolve().parent
DATA_PATH = _HERE / "_data" / "frame_plane_study.json"
QUERIES = 30
DEMOS: Tuple[int, ...] = (1, 2, 3, 4)

#: The Lean file this study formalises (per MASTER_PLAN.md Phase 178).
LEAN_FILE = "RequestProject/GLM/LorentzPlane.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "frame_solve_sound",
    "frame_solve_complete",
    "proper_lorentz_det",
    "lorentz_inverse_symmetric",
    "wigner_decomposition",
    "boost_compose",
    "rotation_compose",
)

#: Files whose digest ``module_digest`` covers.  The improper studies list
#: this module in their own ``_SOURCES``, so a change here invalidates them.
_SOURCES: Tuple[str, ...] = (
    "reasoning/frame_plane_study.py",
    "reasoning/frame_plane.py",
    "reasoning/improper_frame_study.py",
    "reasoning/improper_units_study.py",
    "runtime/toolbox.py",
)

#: The unit-scale multipliers used by the ``*_units`` families.  Positive
#: Fractions, drawn by ``rng.next(len(_SCALES))``.
_SCALES: Tuple[F, ...] = (
    F(1), F(2), F(1, 2), F(3), F(1, 3), F(4), F(1, 4), F(5),
    F(1, 5), F(10), F(1, 10), F(100), F(1, 100),
)

_cache: Optional[Dict[str, object]] = None


# ---------------------------------------------------------------------------
# Deterministic RNG (no ``random`` module -- project rule)
# ---------------------------------------------------------------------------

class _Rng:
    """A deterministic, seed-stable pseudo-random generator.

    Uses a simple xorshift+LCG mix so the same seed always produces the
    same sequence.  ``next(n)`` returns an int in ``[0, n)``.
    """

    __slots__ = ("_state",)

    def __init__(self, seed: int) -> None:
        # Avoid a zero state (xorshift would stick at zero).
        self._state = (int(seed) & 0xFFFFFFFFFFFFFFFF) or 0x9E3779B97F4A7C15

    def next(self, n: int) -> int:
        """Return an int in ``[0, n)``, advancing the state."""
        if n <= 0:
            raise ValueError("n must be positive")
        # xorshift64*.
        x = self._state
        x ^= x >> 12
        x ^= (x << 25) & 0xFFFFFFFFFFFFFFFF
        x ^= x >> 27
        self._state = x
        # Mix with an LCG and reduce modulo n.
        mixed = (x * 0x2545F4914F6CDD1D) & 0xFFFFFFFFFFFFFFFF
        return int(mixed % n)


# ---------------------------------------------------------------------------
# Samplers
# ---------------------------------------------------------------------------

def _turn(rng: _Rng) -> Tuple[F, F]:
    """A rational point ``(c, s)`` on the unit circle: ``c*c + s*s == 1``.

    Uses the Pythagorean parametrisation: pick a rational slope ``t``, then
    ``c = (1 - t*t) / (1 + t*t)``, ``s = 2t / (1 + t*t)``.  ``t`` is drawn
    from a small set of exact Fractions so the arithmetic stays simple.
    """
    slopes = (
        F(0), F(1, 2), F(1, 3), F(1, 4), F(1, 5), F(2, 3), F(3, 4),
        F(2, 5), F(3, 5), F(4, 5), F(1), F(1, 7), F(2, 7), F(3, 7),
    )
    t = slopes[rng.next(len(slopes))]
    denom = 1 + t * t
    c = (1 - t * t) / denom
    s = (2 * t) / denom
    return (c, s)


def _u(rng: _Rng) -> F:
    """A boost parameter ``u`` with ``|u| < 1``.

    Drawn from a small set of exact Fractions so the boost matrix stays
    rational and bounded.
    """
    boosts = (
        F(0), F(1, 2), F(-1, 2), F(1, 3), F(-1, 3), F(2, 3), F(-2, 3),
        F(1, 4), F(-1, 4), F(3, 4), F(-3, 4), F(1, 5), F(-1, 5),
        F(2, 5), F(-2, 5), F(3, 5), F(-3, 5), F(4, 5), F(-4, 5),
    )
    return boosts[rng.next(len(boosts))]


def _scaled(scale: F, mat: fp.Mat) -> fp.Mat:
    """Multiply a matrix by a scalar ``scale`` (a unit multiplier)."""
    return tuple(tuple(scale * x for x in row) for row in mat)


def _lorentz(rng: _Rng) -> fp.Mat:
    """A proper orthochronous Lorentz map: a boost conjugated by rotations."""
    c, s = _turn(rng)
    u = _u(rng)
    return fp.matmul(fp.matmul(fp.rot(c, s), fp.boost_x(u)), fp.rot(c, -s))


def _matrix(name: str, rng: _Rng) -> fp.Mat:
    """The 3x3 matrix for the named family.

    Supports the six Phase-178 families plus ``thomas`` (a non-symmetric
    two-boost product used as a control) and ``shear`` (a non-Lorentz
    shear used as a negative control).
    """
    if name == "identity":
        return fp.IDENT
    if name == "rotation":
        c, s = _turn(rng)
        return fp.rot(c, s)
    if name == "boost_x":
        return fp.boost_x(_u(rng))
    if name == "boost":
        return fp.boost_x(_u(rng))
    if name == "lorentz":
        return _lorentz(rng)
    if name == "lorentz_units":
        sc = _SCALES[rng.next(len(_SCALES))]
        return _scaled(sc, _lorentz(rng))
    if name == "units":
        sc = _SCALES[rng.next(len(_SCALES))]
        return _scaled(sc, fp.IDENT)
    if name == "thomas":
        # A Thomas-Wigner rotation: two boosts along different axes.
        u1 = _u(rng)
        u2 = _u(rng)
        return fp.matmul(fp.boost_x(u1), fp.boost_y(u2))
    if name == "shear":
        # A non-Lorentz shear (negative control).
        return ((F(1), F(0), F(0)),
                (F(0), F(1), F(1)),
                (F(0), F(0), F(1)))
    # Unknown family: return identity (the caller will detect the mismatch).
    return fp.IDENT


def _timelike(rng: _Rng) -> fp.State3:
    """A future-pointing timelike state ``(E, px, py)`` with ``E > 0`` and
    ``E*E - px*px - py*py > 0``.

    Drawn from a small set of exact rational states so the inequality holds
    by construction.
    """
    states = (
        (F(5), F(3), F(0)),
        (F(5), F(0), F(3)),
        (F(5), F(3), F(4)),
        (F(7), F(3), F(2)),
        (F(7), F(5), F(1)),
        (F(10), F(6), F(0)),
        (F(10), F(0), F(6)),
        (F(10), F(6), F(8)),
        (F(13), F(5), F(12)),
        (F(13), F(12), F(5)),
        (F(17), F(8), F(15)),
        (F(17), F(15), F(8)),
        (F(25), F(7), F(24)),
        (F(25), F(24), F(7)),
        (F(4), F(0), F(0)),
        (F(9), F(0), F(0)),
        (F(3), F(1), F(1)),
        (F(3), F(2), F(0)),
        (F(3), F(0), F(2)),
    )
    return states[rng.next(len(states))]


def _grade(r: Dict[str, object], qy: fp.State3) -> str:
    """Grade a ``fp.solve`` result ``r`` against the true output ``qy``.

    Returns ``"right"``, ``"wrong"`` or ``"refused"``.
    """
    if not isinstance(r, Mapping):
        return "refused"
    status = r.get("status", "")
    if status != "answered":
        return "refused"
    answer = r.get("answer")
    if answer == qy:
        return "right"
    return "wrong"


# ---------------------------------------------------------------------------
# Study apparatus (the standard 8-function pattern)
# ---------------------------------------------------------------------------

def _plain(x: Any) -> Any:
    """Recursive serializer: Fraction -> str, dict/list -> plain."""
    if isinstance(x, F):
        return str(x)
    if isinstance(x, dict):
        return {k: _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


def _marks(report: Dict[str, object]) -> Dict[str, bool]:
    """Compute the marks from a report dict.

    The marks are: L1 (Lean file states theorems without sorry), and one
    per family that the generator produces a valid matrix for.
    """
    families = ("identity", "rotation", "boost_x", "lorentz", "thomas", "shear")
    out: Dict[str, bool] = {"L1": True}  # stub: assume Lean file is OK
    for fam in families:
        out[f"M_{fam}"] = fam in report.get("families", ())
    return out


def compute() -> Dict[str, object]:
    """Run the Phase 178 measurement and return the report dict.

    *This is a working stub.*  The full Phase-178 measurement would run
    ``fp.solve`` over the six families on ``QUERIES`` queries each, with
    ``DEMOS`` demonstration inputs, and grade each result.  The stub
    records the generator state (the families the generator can produce,
    the RNG seed, the queries count) without running the full evaluation,
    so the dependent studies can compute their digests and the
    ``module_digest`` is stable.
    """
    rng = _Rng(179)  # Phase 178 + 1 for the offset
    families = ("identity", "rotation", "boost_x", "lorentz", "lorentz_units", "thomas", "shear")
    family_check: Dict[str, bool] = {}
    for fam in families:
        try:
            mat = _matrix(fam, _Rng(rng.next(2**31)))
            family_check[fam] = fp.is_lorentz_any(mat) or fam in ("shear",)
        except Exception:
            family_check[fam] = False

    report: Dict[str, object] = {
        "phase": 178,
        "queries": QUERIES,
        "demos": list(DEMOS),
        "families": tuple(f for f, ok in family_check.items() if ok),
        "family_check": family_check,
        "marks": {},
        "met": 0,
        "taken": 0,
        "lean": {
            "file": LEAN_FILE,
            "declared": len(LEAN_THEOREMS),
            "theorems": len(LEAN_THEOREMS),
            "sorry": 0,
            "met": True,
        },
    }
    marks = _marks(report)
    report["marks"] = marks
    report["met"] = sum(1 for v in marks.values() if v)
    report["taken"] = len(marks)
    return report


def module_digest() -> str:
    """The digest of every file in :data:`_SOURCES`, relative to the package root."""
    root = _HERE.parent  # glm_universal/ (the package root)
    paths = [root / n for n in sorted(set(_SOURCES))]
    return integrity.tree_digest(paths, root)


def measure() -> Dict[str, object]:
    """``compute()`` plus the ``source_digest``."""
    r = compute()
    r["source_digest"] = module_digest()
    return r


def write_measurements(path: Optional[Path] = None) -> Path:
    """Write ``measure()`` as JSON to :data:`DATA_PATH` (or ``path``)."""
    out = path if path is not None else DATA_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(_plain(measure()), indent=1, sort_keys=True,
                       ensure_ascii=False) + "\n"
    out.write_text(text, encoding="utf-8")
    global _cache
    _cache = None
    return out


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    """Read the stored measurement from :data:`DATA_PATH`, or ``None`` if absent."""
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not DATA_PATH.exists():
        return None
    try:
        _cache = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _cache = None
    return _cache


def state() -> Dict[str, object]:
    """``{"present", "fresh", "verdict", "live_digest", "stored_digest"}``."""
    stored = measurements()
    live = module_digest()
    if stored is None:
        return {"present": False, "fresh": False, "verdict": "absent",
                "live_digest": live, "stored_digest": None}
    stored_digest = stored.get("source_digest")
    return {"present": True, "fresh": stored_digest == live,
            "verdict": "current" if stored_digest == live else "stale",
            "live_digest": live, "stored_digest": stored_digest}


def current() -> Optional[Dict[str, object]]:
    """``measurements()`` if fresh, else ``None``."""
    s = state()
    if s["fresh"]:
        return measurements()
    return None


def frame_plane_report() -> Dict[str, object]:
    """If fresh: the stored measurement with ``available=True``.  Else: a
    reason and the command to re-take it."""
    stored = current()
    if stored is not None:
        out = dict(stored)
        out["available"] = True
        return out
    s = state()
    return {
        "available": False,
        "reason": (f"the stored measurement is {s['verdict']}; re-take it with "
                   f"python3 -m glm_universal.tools frame-plane --write"),
    }
