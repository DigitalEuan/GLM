"""``glm_universal.reasoning.economics`` -- the economic register, measured.

The supplied study catalogue makes one universality claim in three parts:
chemical equilibria, musical harmony and **market price discovery** all map to
proximity in the Leech lattice.  :mod:`glm_universal.reasoning.harmony`
settled the musical part against the harmonic register.  This module does the
same job for the economic part against
:mod:`glm_universal.data_objects.economics_register`, so the claim stops being
*not implemented* and acquires a verdict with the statistic that decides it
printed beside it.

What is computed, and all of it exactly
---------------------------------------
1. **A price vector.**  Each of the 21 records becomes a 24-vector built only
   from things the register holds exactly: the base-2 and base-10 magnitude
   buckets, the *mantissa* in each base (``price / base**bucket``, a rational
   in ``[1, base)``), the ten EXT10 exponents of the physical quantity the
   price is quoted per, and a currency-pair flag.  No logarithm is evaluated
   and no float is constructed -- the buckets come from
   :func:`~glm_universal.data_objects.economics_register.compute_exact_log_bucket`,
   which decides ``base**k <= x < base**(k+1)`` by multiplying integers.

2. **Separation.**  Scaled and decoded to the nearest Leech point by the same
   exact decoder the rest of the package uses: at which scale does the lattice
   stop conflating distinct records?

3. **Ordering.**  Does distance from the origin order the records by
   magnitude?  Reported as an exact Kendall tau against the base-2 bucket.

4. **Co-movement.**  The register carries three consecutive quarters per
   instrument, so the sharpest question the claim admits can actually be
   asked: is a record's nearest neighbour in the lattice another quarter of
   *the same instrument*?  Two of the twenty other records are, so the chance
   rate is ``2/20``; anything near ``21/21`` is a real signal and anything
   near ``2/20`` is not.

5. **The control.**  Every one of the above is computed a second time on the
   undecoded vectors.  Scaling cannot reorder distances, so the control is one
   set of numbers for the whole sweep, and it is what the lattice has to beat.
   Without it, "maps to proximity in the Leech lattice" cannot be told apart
   from "maps to proximity in ``Q^24``, and was afterwards decoded".

Nothing here is sampled and no float is constructed.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Mapping, Sequence, Tuple

from ..data_objects import economics_register as er
from ..derived import memo
from . import analogy
from .harmony import kendall_tau

__all__ = [
    "CLAIM",
    "SCALES",
    "CHANCE_SAME_INSTRUMENT",
    "price_vector",
    "magnitude_table",
    "lattice_separation",
    "comovement",
    "decoded_points",
    "economics_report",
]

#: The catalogue sentence this module exists to settle.
CLAIM = "market price discovery maps to proximity in the Leech lattice"

#: The scales the price vectors are swept over before being decoded.  The
#: ladder :mod:`.harmony` uses, continued upward: the harmonic register is
#: separated by scale 9, and the economic one is not separated until 1024,
#: because the closest pair in it -- the euro in 2024-Q1 at ``109/100`` and in
#: 2024-Q3 at ``273/250``, a fifth of a percent apart -- has to be pushed past
#: the covering radius before the decoder stops rounding both to the same
#: point.  The plateau at 20 of 21 across 256 and 512 is that pair and
#: nothing else.
SCALES: Tuple[int, ...] = (1, 2, 4, 8, 9, 16, 32, 64, 128, 256, 512, 1024)

#: Of the twenty records that are not a given one, two are another quarter of
#: the same instrument.  A nearest-neighbour rate at this level is chance.
CHANCE_SAME_INSTRUMENT = Fraction(2, 20)


# ===========================================================================
# 1.  THE PRICE VECTOR
# ===========================================================================

def _mantissa(price: Fraction, base: int) -> Fraction:
    """``price / base**bucket``: the exact rational in ``[1, base)``.

    The part of a magnitude a bucket throws away, kept exactly rather than
    rounded.  It is what separates two quarters that share a bucket -- gold
    sits in base-2 bucket 11 in all three windows -- so without it the lattice
    could not tell one quarter of an instrument from another at all.
    """
    k = er.compute_exact_log_bucket(price, base)
    return price / Fraction(base) ** k


def price_vector(record: "er.PriceRecord", scale: int = 1
                 ) -> Tuple[Fraction, ...]:
    """The 24-coordinate vector of one record, at a given integer scale.

    Fifteen coordinates carry content and nine are zero.  Every one is exact:
    the buckets are integers, the mantissas are rationals in ``[1, base)``,
    and the EXT10 exponents come straight from the physics register.
    """
    head: List[Fraction] = [
        Fraction(scale * record.log_bucket(2)),
        Fraction(scale) * _mantissa(record.price, 2),
        Fraction(scale * record.log_bucket(10)),
        Fraction(scale) * _mantissa(record.price, 10),
    ]
    head.extend(Fraction(scale) * e for e in record.exponents)
    head.append(Fraction(scale if record.is_dimensionless_currency else 0))
    return tuple(head + [Fraction(0)] * (24 - len(head)))


def magnitude_table() -> Tuple[Dict[str, object], ...]:
    """Every record with its two buckets and two mantissas, exactly.

    This is the register's own arithmetic laid out for inspection: the row for
    gold in ``2024-Q1`` says bucket 11 because ``2**11 = 2048 <= 2070``, and
    the row for ``2024-Q3`` says 11 because ``2478 < 4096``.
    """
    rows: List[Dict[str, object]] = []
    for record in er.load_price_register():
        rows.append({
            "key": record.key,
            "identifier": record.identifier,
            "window": record.observation_window,
            "price": record.price,
            "bucket_2": record.log_bucket(2),
            "mantissa_2": _mantissa(record.price, 2),
            "bucket_10": record.log_bucket(10),
            "mantissa_10": _mantissa(record.price, 10),
            "bounds_hold": (er.bucket_bounds_hold(record.price, 2)
                            and er.bucket_bounds_hold(record.price, 10)),
        })
    return tuple(rows)


# ===========================================================================
# 2.  THE GEOMETRY
# ===========================================================================

def _distance2(left: Sequence, right: Sequence) -> Fraction:
    return sum((Fraction(a) - Fraction(b)) ** 2
               for a, b in zip(left, right))


def _points_cache_inputs() -> Tuple[object, ...]:
    """Everything the decoded points are a function of.

    The register itself, this module, the two modules that turn a rational
    vector into a lattice point, and the physics snapshot the EXT10 exponents
    come from.  If any of them moves the artefact is stale and the decoding
    happens again.
    """
    from pathlib import Path

    package = Path(__file__).resolve().parent.parent
    return (
        Path(__file__).resolve(),
        package / "data_objects" / "economics_register.py",
        package / "data_objects" / "_data" / "economics_register.csv",
        package / "data_objects" / "_data" / "physics_660.json",
        package / "reasoning" / "analogy.py",
        package / "reasoning" / "metric.py",
        package / "substrate" / "leech2.py",
    )


def _points_store():
    """The digest-keyed artefact holding the decoded points, by scale."""
    from ..derived import DerivedStore

    return DerivedStore("economics_lattice_points", _points_cache_inputs,
                        schema=1)


def decoded_points(scale: int) -> Tuple[Tuple[int, ...], ...]:
    """The 21 records as Leech points at one scale, decoded once ever.

    Exact decoding of a 24-vector is the expensive step in this module -- a
    twelve-scale sweep is 252 of them -- and the answer is a pure function of
    frozen inputs.  It is therefore stored the way the Lean address book is:
    beside the SHA-256 digest of the sources it came from, read back only
    while that digest holds, recomputed the moment it moves.  A stale artefact
    is never answered from.
    """
    store = _points_store()
    stored = store.read_fresh()
    table: Dict[str, object] = dict(stored) if isinstance(stored, dict) else {}
    key = str(int(scale))
    records = er.load_price_register()
    found = table.get(key)
    if (isinstance(found, list) and len(found) == len(records)
            and all(isinstance(row, list) and len(row) == 24
                    for row in found)):
        return tuple(tuple(int(c) for c in row) for row in found)
    points = tuple(
        tuple(int(c) for c in
              analogy.nearest_lattice_point(price_vector(record, scale)).point)
        for record in records)
    table[key] = [list(p) for p in points]
    try:
        store.write(table)
    except OSError:  # pragma: no cover - a read-only checkout still works
        pass
    return points


def _nearest_same_instrument(points: Sequence[Sequence],
                             records: Sequence["er.PriceRecord"]
                             ) -> Dict[str, object]:
    """How often a record's nearest neighbour is the same instrument.

    Ties are counted against the claim: a record whose nearest distance is
    shared by another instrument does not count as a hit, because a tie is not
    a discovery.
    """
    hits: List[str] = []
    ties: List[str] = []
    for i, record in enumerate(records):
        best: Fraction = None            # type: ignore[assignment]
        winners: List[int] = []
        for j in range(len(records)):
            if j == i:
                continue
            d = _distance2(points[i], points[j])
            if best is None or d < best:
                best, winners = d, [j]
            elif d == best:
                winners.append(j)
        same = [j for j in winners
                if records[j].identifier == record.identifier]
        if len(winners) > 1 and len(same) != len(winners):
            ties.append(record.key)
        elif same:
            hits.append(record.key)
    return {
        "hits": len(hits),
        "of": len(records),
        "rate": Fraction(len(hits), len(records)) if records else Fraction(0),
        "tied": tuple(ties),
        "missed": tuple(r.key for r in records
                        if r.key not in hits and r.key not in ties),
    }


def _statistics(points: Sequence[Sequence],
                records: Sequence["er.PriceRecord"]) -> Dict[str, object]:
    """Separation, ordering and co-movement for one set of points."""
    origin = tuple(Fraction(0) for _ in range(24))
    distances = tuple(_distance2(p, origin) for p in points)
    buckets = tuple(r.log_bucket(2) for r in records)
    return {
        "distinct_points": len({tuple(p) for p in points}),
        "max_distance2": max(distances),
        "tau_magnitude": kendall_tau(distances, buckets),
        "comovement": _nearest_same_instrument(points, records),
    }


def lattice_separation(scales: Sequence[int] = SCALES) -> Dict[str, object]:
    """Decode every price vector at each scale, and count what survives.

    The control is the same vectors *before* the decoder.  Multiplying every
    coordinate by one positive factor cannot change the order of the
    distances, so the control is a single set of numbers rather than a sweep.
    """
    records = er.load_price_register()
    control = _statistics([price_vector(r, 1) for r in records], records)
    rows: List[Dict[str, object]] = []
    for scale in scales:
        row = dict(_statistics(decoded_points(scale), records))
        row["scale"] = scale
        rows.append(row)
    best = max(rows, key=lambda r: (r["distinct_points"],
                                    r["comovement"]["hits"],
                                    r["tau_magnitude"]))
    return {
        "scales": tuple(scales),
        "rows": tuple(rows),
        "record_count": len(records),
        "best_scale": best["scale"],
        "best_distinct": best["distinct_points"],
        "best_tau_magnitude": best["tau_magnitude"],
        "best_comovement": best["comovement"],
        "control": control,
        "fully_separated": tuple(r["scale"] for r in rows
                                 if r["distinct_points"] == len(records)),
        "beats_control": (
            best["tau_magnitude"] > control["tau_magnitude"]
            or best["comovement"]["hits"] > control["comovement"]["hits"]),
    }


def comovement(scale: int = 8) -> Dict[str, object]:
    """The co-movement question on its own, at one scale.

    Named separately because it is the question the register was widened to
    make askable: three consecutive quarters per instrument is what turns
    "prices are points" into something that can be wrong.
    """
    records = er.load_price_register()
    result = dict(_nearest_same_instrument(decoded_points(scale), records))
    result["scale"] = scale
    result["chance"] = CHANCE_SAME_INSTRUMENT
    result["beats_chance"] = result["rate"] > CHANCE_SAME_INSTRUMENT
    return result


# ===========================================================================
# 3.  THE VERDICT
# ===========================================================================

def _verdict(separation: Mapping[str, object]) -> Dict[str, object]:
    """The claim's verdict, from the statistic rather than from taste.

    Three conditions, and the third is the one that decides it.

    * the lattice must **separate** the records -- each at its own point;
    * proximity must **track the market**: a nearest neighbour that is another
      quarter of the same instrument, at better than the ``2/20`` chance rate;
    * and it must do so **better than the control**, which is the same
      distance taken before the decoder is applied.

    The first two can hold for a reason that has nothing to do with the Leech
    lattice: two quarters of one instrument have nearly equal prices, so their
    vectors are near each other in ``Q^24`` before any lattice is involved.
    Only the third condition separates the sentence being tested from that.
    Where the decoder adds nothing, the claim is recorded as *not reproduced*:
    what was measured is real, and it is not what the sentence says.
    """
    separated = bool(separation["fully_separated"])
    tau = separation["best_tau_magnitude"]
    best_co = separation["best_comovement"]
    control = separation["control"]
    control_co = control["comovement"]
    tracks = best_co["rate"] > CHANCE_SAME_INSTRUMENT
    beats_control = bool(separation["beats_control"])
    if separated and tracks and beats_control:
        verdict = "confirmed"
        because = ("the lattice separates every record, its nearest "
                   "neighbours are other quarters of the same instrument "
                   "well above the chance rate, and it does better than the "
                   "same distance taken before the decoder")
    elif separated and tracks:
        verdict = "not reproduced"
        because = (f"proximity does track the market -- {best_co['hits']} of "
                   f"{best_co['of']} nearest neighbours are another quarter "
                   f"of the same instrument, against a chance rate of "
                   f"{CHANCE_SAME_INSTRUMENT} -- but the undecoded control "
                   f"does exactly as well ({control_co['hits']} of "
                   f"{control_co['of']}) with no lattice at all, so what is "
                   f"measured is the price vector rather than the geometry "
                   f"of the Leech lattice")
    elif separated:
        verdict = "refuted"
        because = (f"the lattice separates the records but its nearest "
                   f"neighbours are not the same instrument's other quarters "
                   f"any more often than chance: {best_co['hits']} of "
                   f"{best_co['of']}")
    else:
        verdict = "refuted"
        because = ("no scale in the sweep gives every record its own lattice "
                   "point, so proximity cannot be discovering anything about "
                   "prices it conflates")
    return {
        "claim": CLAIM,
        "separated": separated,
        "tracks_the_market": tracks,
        "best_tau_magnitude": tau,
        "best_comovement_rate": best_co["rate"],
        "control_comovement_rate": control_co["rate"],
        "chance_rate": CHANCE_SAME_INSTRUMENT,
        "beats_control": beats_control,
        "verdict": verdict,
        "because": because,
    }


# ===========================================================================
# 4.  THE REPORT
# ===========================================================================

@memo
def economics_report() -> Dict[str, object]:
    """Everything above, in one exact dictionary."""
    separation = lattice_separation()
    return {
        "register": dict(er.register_summary()),
        "magnitudes": magnitude_table(),
        "lattice": separation,
        "verdict": _verdict(separation),
    }
