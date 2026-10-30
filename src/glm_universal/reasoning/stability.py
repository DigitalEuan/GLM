"""``glm_universal.reasoning.stability`` -- how far may an input move?

What this module is
-------------------
:mod:`~glm_universal.reasoning.lean_address` gives every Lean declaration an
address: its 24 structural counts, scaled by :data:`~.lean_address.SCALE`, sent
to the nearest point of the Leech lattice.  An address is only worth quoting if
it is *stable* -- if a small change in the declaration does not move it -- and
until this module there was no measurement of how small "small" has to be.

That is what is measured here, and the statements it instantiates are proved,
for an arbitrary candidate set in an arbitrary metric or inner product space,
in ``RequestProject/GLM/Stability.lean``:

``certified_safe``
    the **certificate**: ``isNearest_of_sq_data`` in squared quantities alone,
    ``64 D E <= (m^2 - 4D - 4E)^2``, so it can be checked in exact rational
    arithmetic with no square root anywhere.  Sufficient, never sharp;
``shell_certified``
    the sharper certificate of ``le_competitorRadius_of_shell``, which uses the
    next shell of the lattice rather than only its minimum distance;
``best_competitor`` / ``stability_radius``
    the **sharp** answer of ``isNearest_perturbed_iff``: the exact radius is
    the least distance to a bisector, minimised over the rivals, and past it
    ``exists_perturbation_flip`` *builds* a perturbation that moves the
    address rather than merely asserting that one exists;
``crossing_witness``
    that construction, run: a perturbation strictly inside the radius that
    leaves the address alone, and the one just outside it that does not,
    decoded by the quantiser rather than argued about;
``radius_census`` / ``perturbation_sweep`` / ``feature_step_report``
    the measurement over the corpus: how the radii are distributed, what a
    declared perturbation actually costs, and the fact that a whole feature
    unit always moves both the address and its read-back.

Everything is exact: every radius, residual and perturbation is an ``int`` or a
:class:`~fractions.Fraction`, and no float is constructed anywhere (D7).
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from ..substrate import leech2
from . import lean_address as la
from . import llvq_table

__all__ = [
    "MIN_NORM2", "NEXT_SHELL_NORM2", "SCALE", "COVERING_NORM2",
    "certified_safe", "shell_certified",
    "corpus_names", "scaled_input", "decode", "residual", "best_competitor",
    "stability_radius", "crossing_witness", "radius_census",
    "perturbation_sweep", "feature_step_report", "certificate_probe",
    "stability_report",
]

#: The minimum squared norm of the Leech lattice in the integral model of
#: ``substrate/leech2.py``.
MIN_NORM2 = leech2.MIN_NORM2

#: The squared norm of the second shell in the same model.
NEXT_SHELL_NORM2 = 48

#: The squared covering radius in the same model -- half the minimum norm.
COVERING_NORM2 = Fraction(MIN_NORM2, 2)

#: The address book's scale factor.
SCALE = la.SCALE

_MINIMAL: Optional[Tuple[Tuple[int, ...], ...]] = None
_COMPETITOR_CACHE: Dict[Tuple[Fraction, ...], Dict[str, object]] = {}
_RADIUS_CACHE: Dict[str, Dict[str, object]] = {}


def _minimal_vectors() -> Tuple[Tuple[int, ...], ...]:
    """All 196,560 minimal vectors, enumerated once and kept."""
    global _MINIMAL
    if _MINIMAL is None:
        _MINIMAL = tuple(tuple(v) for v in leech2.minimal_vectors())
    return _MINIMAL


# ---------------------------------------------------------------------------
# 1.  The two certificates, transcribed from the Lean hypotheses
# ---------------------------------------------------------------------------
def certified_safe(perturbation2: Fraction, residual2: Fraction) -> bool:
    """``isNearest_of_sq_data`` with ``m^2 = MIN_NORM2``.

    ``D`` is the squared size of the perturbation and ``E`` the squared
    distance from the input to its address.  Sufficient for the address to be
    unchanged; it is not sharp, and :func:`stability_radius` is.
    """
    slack = Fraction(MIN_NORM2) - 4 * Fraction(perturbation2) - 4 * Fraction(residual2)
    if slack < 0:
        return False
    return 64 * Fraction(perturbation2) * Fraction(residual2) <= slack ** 2


def shell_certified(perturbation2: Fraction, residual2: Fraction) -> bool:
    """``le_competitorRadius_of_shell``: the same test against the next shell.

    Rivals on the second shell are further away, so the admissible
    perturbation is larger; the limit is a quarter of the shell's squared norm.
    """
    limit = Fraction(NEXT_SHELL_NORM2, 4)
    slack = limit - Fraction(perturbation2) - Fraction(residual2)
    if slack < 0:
        return False
    return 4 * Fraction(perturbation2) * Fraction(residual2) <= slack ** 2


# ---------------------------------------------------------------------------
# 2.  The corpus, and one declaration's radius
# ---------------------------------------------------------------------------
def corpus_names(limit: Optional[int] = None) -> Tuple[str, ...]:
    """Declaration names, in the address book's own order."""
    names = tuple(la.feature_table())
    return names if limit is None else names[:limit]


def scaled_input(features: Sequence[int]) -> Tuple[int, ...]:
    """``SCALE`` times a feature vector -- the point the quantiser is given."""
    return tuple(int(v) * SCALE for v in features)


def decode(vector: Sequence) -> Tuple[Tuple[int, ...], object]:
    """The nearest Leech point to ``vector``, and the decoder's own result."""
    result = llvq_table.nearest_lattice_point_table(
        [Fraction(v) for v in vector])
    return tuple(int(c) for c in result.point), result


def residual(vector: Sequence, point: Sequence) -> Tuple[Fraction, ...]:
    """``x - p``: the offset of the input from its address."""
    return tuple(Fraction(a) - Fraction(b) for a, b in zip(vector, point))


def best_competitor(offset: Sequence[Fraction]) -> Dict[str, object]:
    """The rival that comes closest to winning, and how close it comes.

    A rival is ``p + v`` for a minimal vector ``v``; the distance from ``x`` to
    the bisector of ``p`` and ``p + v`` is ``(|v|^2 - 2<d,v>) / (2|v|)`` with
    ``d = x - p``, so the least such distance is attained at the ``v`` that
    maximises ``<d, v>``.  Everything is reported squared, or as the
    coefficient ``t`` with ``delta = t v``, so that no square root is needed.
    """
    key = tuple(Fraction(c) for c in offset)
    cached = _COMPETITOR_CACHE.get(key)
    if cached is not None:
        return cached
    d = list(key)
    best_inner: Optional[Fraction] = None
    best_vector: Tuple[int, ...] = ()
    for v in _minimal_vectors():
        inner = sum(a * b for a, b in zip(d, v))
        if best_inner is None or inner > best_inner:
            best_inner, best_vector = inner, v
    assert best_inner is not None
    gap = Fraction(MIN_NORM2) - 2 * best_inner
    answer = {
        "vector": best_vector,
        "inner": best_inner,
        "gap": gap,
        "radius2": gap ** 2 / (4 * MIN_NORM2),
        "crossing": gap / (2 * MIN_NORM2),
    }
    _COMPETITOR_CACHE[key] = answer
    return answer


def stability_radius(name: str) -> Dict[str, object]:
    """Everything about one declaration's address and how far it may move."""
    cached = _RADIUS_CACHE.get(name)
    if cached is not None:
        return cached
    features = la.feature_table()[name]
    vector = scaled_input(features)
    point, _ = decode(vector)
    offset = residual(vector, point)
    competitor = best_competitor(offset)
    residual2 = sum(c * c for c in offset)
    record: Dict[str, object] = {
        "name": name,
        "features": tuple(int(v) for v in features),
        "address": point,
        "competitor": competitor["vector"],
        "residual2": Fraction(residual2),
        "radius2": Fraction(competitor["radius2"]),
        "crossing": Fraction(competitor["crossing"]),
        "on_a_bisector": Fraction(competitor["radius2"]) == 0,
        "certified": certified_safe(Fraction(competitor["radius2"]),
                                    Fraction(residual2)),
        "lean": "GLM.Stability.isNearest_perturbed_iff",
    }
    _RADIUS_CACHE[name] = record
    return record


# ---------------------------------------------------------------------------
# 3.  The witness the theorem constructs
# ---------------------------------------------------------------------------
def crossing_witness(name: str,
                     overshoot: Fraction = Fraction(1, 1000)) -> Dict[str, object]:
    """Run ``exists_perturbation_flip``: inside holds, outside moves.

    The perturbation is ``t v`` for the closest competitor ``v``, which is the
    direction the theorem picks.  ``t = crossing`` is exactly the bisector, so
    ``t`` a little below it must keep the address and ``t`` a little above it
    must lose it.
    """
    record = stability_radius(name)
    features, point = record["features"], record["address"]
    vector = scaled_input(features)                       # type: ignore[arg-type]
    v = record["competitor"]
    crossing = Fraction(record["crossing"])               # type: ignore[arg-type]
    inside_t = crossing / 2
    outside_t = crossing + overshoot
    inside = [Fraction(a) + inside_t * b for a, b in zip(vector, v)]
    outside = [Fraction(a) + outside_t * b for a, b in zip(vector, v)]
    inside_point, _ = decode(inside)
    outside_point, _ = decode(outside)
    rival = tuple(int(a) + int(b) for a, b in zip(point, v))
    return {
        "name": name,
        "crossing": crossing,
        "strict_inside": crossing > 0,
        "inside_size2": inside_t ** 2 * MIN_NORM2,
        "outside_size2": outside_t ** 2 * MIN_NORM2,
        "inside_holds": inside_point == point,
        "outside_moves": outside_point != point,
        "outside_is_the_competitor": outside_point == rival,
        "lean": "GLM.Stability.exists_perturbation_flip",
    }


# ---------------------------------------------------------------------------
# 4.  The census over the corpus
# ---------------------------------------------------------------------------
def radius_census(limit: Optional[int] = None) -> Dict[str, object]:
    """How the radii and residuals are distributed over the corpus."""
    histogram: Dict[str, int] = {}
    residuals: List[Fraction] = []
    radii: List[Fraction] = []
    bisectors = 0
    names = corpus_names(limit)
    for name in names:
        record = stability_radius(name)
        key = str(record["radius2"])
        histogram[key] = histogram.get(key, 0) + 1
        residuals.append(Fraction(record["residual2"]))   # type: ignore[arg-type]
        radii.append(Fraction(record["radius2"]))         # type: ignore[arg-type]
        bisectors += bool(record["on_a_bisector"])
    return {
        "declarations": len(names),
        "radius2_histogram": histogram,
        "on_a_bisector": bisectors,
        "radius2_min": min(radii) if radii else Fraction(0),
        "radius2_max": max(radii) if radii else Fraction(0),
        "residual2_min": min(residuals) if residuals else Fraction(0),
        "residual2_max": max(residuals) if residuals else Fraction(0),
        "covering_bound": COVERING_NORM2,
    }


def _direction(kind: str, index: int) -> Tuple[int, ...]:
    """A declared perturbation direction, as 24 integer coefficients."""
    if kind == "uniform":
        return tuple(1 for _ in range(24))
    if kind == "alternating":
        return tuple(1 if i % 2 == 0 else -1 for i in range(24))
    if kind == "single":
        return tuple(1 if i == index % 24 else 0 for i in range(24))
    raise ValueError(f"_direction: unknown direction {kind!r}")


def perturbation_sweep(limit: Optional[int] = None,
                       steps: Sequence[Fraction] = (Fraction(1, 8),
                                                    Fraction(1, 2),
                                                    Fraction(2)),
                       directions: Sequence[str] = ("uniform", "alternating"),
                       ) -> Dict[str, object]:
    """Move every address by each declared perturbation and see what survives.

    ``certificate_violations`` counts the cases the certificate called safe and
    which moved anyway; ``radius_violations`` counts the ones strictly inside
    the sharp radius that moved. Both are theorems, so both must be zero.
    """
    names = corpus_names(limit)
    rows: List[Dict[str, object]] = []
    certificate_violations = radius_violations = 0
    for kind in directions:
        for step in steps:
            step = Fraction(step)
            kept = reading_kept = 0
            size2 = Fraction(0)
            for index, name in enumerate(names):
                record = stability_radius(name)
                offsets = _direction(kind, index)
                delta = [step * c for c in offsets]
                size2 = sum(c * c for c in delta)
                vector = scaled_input(record["features"])  # type: ignore[arg-type]
                moved = [Fraction(a) + b for a, b in zip(vector, delta)]
                point, _ = decode(moved)
                same = point == record["address"]
                kept += same
                before = la.describe_address(record["address"])["recovered"]  # type: ignore[arg-type]
                after = la.describe_address(point)["recovered"]
                reading_kept += after == before
                if not same:
                    if certified_safe(Fraction(size2),
                                      Fraction(record["residual2"])):  # type: ignore[arg-type]
                        certificate_violations += 1
                    if Fraction(size2) < Fraction(record["radius2"]):  # type: ignore[arg-type]
                        radius_violations += 1
            rows.append({
                "direction": kind,
                "step": step,
                "size2": Fraction(size2),
                "declarations": len(names),
                "address_kept": kept,
                "reading_kept": reading_kept,
            })
    return {
        "rows": rows,
        "declarations": len(names),
        "certificate_violations": certificate_violations,
        "radius_violations": radius_violations,
        "lean": "GLM.Stability.isNearest_of_sq_data",
    }


# ---------------------------------------------------------------------------
# 5.  The read-back outlives the address
# ---------------------------------------------------------------------------
def feature_step_report(limit: Optional[int] = None, steps: int = 4
                        ) -> Dict[str, object]:
    """Step a feature by one whole unit; the read-back must follow it there.

    The address is a lattice point and the read-back divides by ``SCALE``, so a
    change of one whole feature unit has to appear in the read-back in exactly
    the coordinate that was changed -- and in no other.
    """
    names = corpus_names(limit)
    total = tracked = 0
    for name in names:
        features = list(la.feature_table()[name])
        base_point, _ = decode(scaled_input(features))
        base_read = la.describe_address(base_point)["recovered"]
        for index in range(min(steps, len(features))):
            stepped = list(features)
            direction = -1 if stepped[index] >= la.CAP else 1
            stepped[index] += direction
            point, _ = decode(scaled_input(stepped))
            read = la.describe_address(point)["recovered"]
            total += 1
            expected = list(base_read)                    # type: ignore[arg-type]
            expected[index] += direction
            tracked += tuple(read) == tuple(expected)     # type: ignore[arg-type]
    return {
        "declarations": len(names),
        "steps": total,
        "read_back_tracks_the_step": tracked,
        "scale": SCALE,
    }


# ---------------------------------------------------------------------------
# 6.  The certificate, exercised on lattice points directly
# ---------------------------------------------------------------------------
def certificate_probe(points: int = 8, offsets: int = 4) -> Dict[str, object]:
    """Check the certificate away from the corpus, on the lattice itself.

    Take a few lattice points, offset each by a declared fraction of a minimal
    vector, and wherever the certificate says the address cannot move, decode
    and confirm that it did not.
    """
    minimal = _minimal_vectors()
    if not minimal:  # pragma: no cover
        return {"available": False, "checked": 0, "violations": 0}
    checked = violations = 0
    for i in range(points):
        base = minimal[(i * 977) % len(minimal)]
        for j in range(1, offsets + 1):
            direction = minimal[(i * 31 + j * 1013) % len(minimal)]
            scale = Fraction(1, 4 * (j + 1))
            offset = [scale * c for c in direction]
            residual2 = sum(c * c for c in offset)
            vector = [Fraction(a) + b for a, b in zip(base, offset)]
            point, _ = decode(vector)
            for k in (1, 2):
                delta_scale = Fraction(1, 16 * k)
                delta = [delta_scale * c for c in
                         minimal[(i * 7 + j * 11 + k) % len(minimal)]]
                size2 = sum(c * c for c in delta)
                if not certified_safe(Fraction(size2), Fraction(residual2)):
                    continue
                moved, _ = decode([a + b for a, b in zip(vector, delta)])
                checked += 1
                violations += moved != point
    return {
        "available": True,
        "checked": checked,
        "violations": violations,
        "lean": "GLM.Stability.isNearest_of_sq_data",
    }


# ---------------------------------------------------------------------------
# 7.  One call for the whole measurement
# ---------------------------------------------------------------------------
def stability_report(limit: Optional[int] = 16, witnesses: int = 2
                     ) -> Dict[str, object]:
    """The census, the sweep and the witnesses, in one object."""
    census = radius_census(limit)
    sweep = perturbation_sweep(limit)
    checked = [crossing_witness(name) for name in corpus_names(witnesses)]
    agree = all(w["outside_moves"] and (w["inside_holds"] or not w["strict_inside"])
                for w in checked)
    return {
        "min_norm2": MIN_NORM2,
        "next_shell_norm2": NEXT_SHELL_NORM2,
        "scale": SCALE,
        "census": census,
        "sweep": sweep,
        "witnesses": checked,
        "witnesses_agree": agree,
        "study": "studies/LEAN_ADDRESS_STUDY.md",
        "lean_file": "RequestProject/GLM/Stability.lean",
    }
