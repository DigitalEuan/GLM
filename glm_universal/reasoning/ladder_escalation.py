"""``glm_universal.reasoning.ladder_escalation`` -- reading the substrate at
every rung of the construction ladder, starting in the middle.

The question
------------
This system reads a carrier by quantising it: the 24 exact coordinates are
snapped to the nearest point of a lattice, and the point is the address.  Which
lattice?  Until now the answer was fixed -- Construction A in the old scripts,
the Leech lattice since the sieve was completed -- and a fixed answer is a
*partial system*, because the rungs of
:mod:`glm_universal.substrate.construction_ladder` trade two things against
each other and no single rung wins both:

* a **coarse** rung (``B``, ``C``) has few points and a large minimum distance,
  so a perturbed query still lands on the right point -- but distinct carriers
  collide on it, and a collision cannot be resolved by reading harder;
* a **fine** rung (``D``, ``Z``) separates everything -- and a perturbation of
  half a unit already moves the address.

``studies/CONSTRUCTION_LADDER_STUDY.md`` pre-registers the experiment this
module runs: hold a register of carriers, perturb a query off one of them, and
ask which carrier the reading names.  A rung answers **correctly**, **wrongly**
or not at all; a wrong answer is the expensive outcome and is counted
separately, never folded into an accuracy.

Escalation, out from the middle
-------------------------------
The ladder's rungs in coarse-to-fine order are ``B, C, A, D, Z``, and its
middle is ``A`` -- which is exactly where this system used to read.  Three
orders of visiting them are run against each other, with the same stopping
rule:

``middle_out``
    ``A, D, C, Z, B`` -- start where the system already reads, then one step
    finer, one step coarser, and outwards.  This is the walk
    :func:`glm_universal.substrate.construction_ladder.middle_out_order`
    generates and ``GLM.ConstructionLadder`` proves visits every rung once.
``coarse_to_fine``
    ``B, C, A, D, Z`` -- the note's ladder, climbed from the bottom.
``fine_to_coarse``
    ``Z, D, A, C, B`` -- the same ladder from the top.

The stopping rule is the only one available to a reader that does not know the
answer: **stop at the first rung whose cell is occupied by exactly one
carrier**.  Occupancy is a property of the index, built once from the clean
carriers; nothing about the query's true identity is used.

What is measured
----------------
For every order and every fixed rung: correct answers, wrong answers,
refusals, and the exact work done -- the number of rung quantisations, and the
roundings, codeword evaluations and repairs inside them, all counted by the
quantisers themselves rather than modelled.

Exactness
---------
:class:`~fractions.Fraction` and integers throughout.  The perturbations are
deterministic: the support and the signs of the offset applied to carrier ``i``
are read off Golay codeword ``i mod 4096``, so the sweep is a function of the
index and no random source is imported.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .. import integrity
from ..substrate import construction_ladder as CL
from ..substrate import mog
from . import metric
from .analogy import _round_to_residue
from .fwht_decode import message_of_codeword, support_sums_fwht

__all__ = [
    "Quantisation", "quantise", "reading",
    "SAMPLE_PER_REGISTER", "PERTURBATIONS", "ORDERS",
    "sample_carriers", "perturb", "rung_index", "occupancy",
    "answer_with_order", "answer_at_rung", "order_facts",
    "run_orders", "run_fixed_rungs", "ladder_escalation_report",
    "module_digest", "measure", "write_measurements", "measurements",
    "state", "current", "DATA_PATH",
]

DIM = 24


# ═════════════════════════════════════════════════════════════════════════
# 1.  THE QUANTISERS, ONE PER RUNG, EACH COUNTING ITS OWN WORK
# ═════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Quantisation:
    """The nearest point of one rung, and what finding it cost.

    ``work`` counts what the quantiser actually did: ``roundings`` is the
    number of coordinate roundings, ``codewords`` the number of Golay
    codewords whose cost was evaluated, ``repairs`` the number of single
    coordinate moves made to satisfy a congruence.  ``cost`` is their sum, so
    a rung cannot buy accuracy quietly.
    """

    rung: str
    point: Tuple[int, ...]
    distance2: Fraction
    work: Dict[str, int] = field(default_factory=dict)

    @property
    def cost(self) -> int:
        return sum(self.work.values())


def _round_nearest(value: Fraction) -> Tuple[int, Fraction, Fraction]:
    """Nearest integer to ``value``, its cost, and the penalty of the next one.

    Ties go to the smaller integer, which is the tie-break the rest of the
    package uses (see ``reasoning.analogy._round_to_residue``).
    """
    floor = value.numerator // value.denominator
    best, best_cost = None, None
    for candidate in (floor, floor + 1):
        cost = (value - candidate) ** 2
        if best_cost is None or cost < best_cost or (cost == best_cost
                                                     and candidate < best):
            best, best_cost = candidate, cost
    assert best is not None and best_cost is not None
    alt = min((value - (best + 1)) ** 2, (value - (best - 1)) ** 2)
    return best, best_cost, alt - best_cost


def _quantise_z(values: Sequence[Fraction]) -> Quantisation:
    rounded = [_round_nearest(value) for value in values]
    point = tuple(entry[0] for entry in rounded)
    cost = sum((entry[1] for entry in rounded), Fraction(0))
    return Quantisation("Z", point, cost, {"roundings": DIM})


def _quantise_d(values: Sequence[Fraction]) -> Quantisation:
    rounded = [_round_nearest(value) for value in values]
    point = [entry[0] for entry in rounded]
    cost = sum((entry[1] for entry in rounded), Fraction(0))
    work = {"roundings": DIM, "repairs": 0}
    if sum(point) % 2 != 0:
        penalty, index = min((entry[2], i) for i, entry in enumerate(rounded))
        base = point[index]
        up, down = (values[index] - (base + 1)) ** 2, (values[index]
                                                       - (base - 1)) ** 2
        point[index] = base + 1 if up <= down else base - 1
        cost += penalty
        work["repairs"] = 1
    return Quantisation("D", tuple(point), cost, work)


def _decode_even(values: Sequence[Fraction], rung: str,
                 enforce_sum: bool) -> Quantisation:
    """Nearest point of rung ``A`` (``enforce_sum`` false) or ``B`` (true).

    The search is the even half of the package's Leech decoder: round every
    coordinate to the two residues ``0`` and ``2`` mod 4, turn the difference
    into 4,096 codeword costs with one Walsh-Hadamard transform, and -- for
    ``B`` -- repair the coordinate sum with the single cheapest ``+-4`` move.
    """
    base = [_round_to_residue(value, 0) for value in values]
    alt = [_round_to_residue(value, 2) for value in values]
    base_cost = sum((entry[1] for entry in base), Fraction(0))
    delta = [alt[i][1] - base[i][1] for i in range(DIM)]
    sums = support_sums_fwht(delta)
    work = {"roundings": 2 * DIM, "codewords": len(mog.GOLAY_MASKS),
            "repairs": 0}
    best_point: Optional[List[int]] = None
    best_cost: Optional[Fraction] = None
    repairs = 0
    for word in mog.GOLAY_MASKS:
        cost = base_cost + sums[message_of_codeword(word)]
        if best_cost is not None and cost > best_cost:
            continue
        point = [alt[i][0] if (word >> i) & 1 else base[i][0]
                 for i in range(DIM)]
        if enforce_sum and sum(point) % 8 != 0:
            penalties = [(alt[i][2] if (word >> i) & 1 else base[i][2], i)
                         for i in range(DIM)]
            penalty, index = min(penalties)
            cost += penalty
            current = point[index]
            up = (values[index] - (current + 4)) ** 2
            down = (values[index] - (current - 4)) ** 2
            point[index] = current + 4 if up <= down else current - 4
            repairs += 1
        if best_cost is None or cost < best_cost or (
                cost == best_cost and best_point is not None
                and point < best_point):
            best_cost, best_point = cost, point
    assert best_point is not None and best_cost is not None
    work["repairs"] = repairs
    return Quantisation(rung, tuple(best_point), best_cost, work)


def _quantise_c(values: Sequence[Fraction]) -> Quantisation:
    from .fwht_decode import nearest_lattice_point_fwht
    result = nearest_lattice_point_fwht(values)
    work = {"roundings": 4 * DIM, "codewords": 2 * len(mog.GOLAY_MASKS),
            "repairs": 0}
    return Quantisation("C", tuple(result.point),
                        result.distance2 * metric.GRIESS_SCALE, work)


#: Quantisations already computed, keyed by the exact vector and the rung.  A
#: run asks for the same carrier at the same rung once per order, and the
#: answer is a pure function of the two, so it is computed once.  The work
#: counts a cached call reports are the ones the computation actually did.
_QUANTISE_CACHE: Dict[Tuple[Tuple[Fraction, ...], str], Quantisation] = {}


def quantise(vector: Sequence, rung: str) -> Quantisation:
    """The nearest point of the named rung, exactly, with its work counted."""
    values = metric.as_exact_vector(vector)
    key = (tuple(values), rung)
    cached = _QUANTISE_CACHE.get(key)
    if cached is not None:
        return cached
    computed = _quantise_uncached(values, rung)
    _QUANTISE_CACHE[key] = computed
    return computed


def _quantise_uncached(values: Sequence[Fraction], rung: str) -> Quantisation:
    base, exponent = CL.scale_of(rung)
    if exponent != 0:
        return _quantise_scaled(values, rung, base, exponent)
    if rung == "Z":
        return _quantise_z(values)
    if rung == "D":
        return _quantise_d(values)
    if rung == "A":
        return _decode_even(values, "A", enforce_sum=False)
    if rung == "B":
        return _decode_even(values, "B", enforce_sum=True)
    if rung == "C":
        return _quantise_c(values)
    raise KeyError(f"ladder_escalation: no quantiser for rung {rung!r}")


def _quantise_scaled(values: Sequence[Fraction], rung: str, base: str,
                     exponent: int) -> Quantisation:
    """The nearest point of ``2^k L``, from the quantiser of ``L``.

    Scaling is an exact similarity: the nearest point of ``2^k L`` to ``v`` is
    ``2^k`` times the nearest point of ``L`` to ``v / 2^k``, and the squared
    distance is ``4^k`` times the distance the base quantiser measured.  No
    new search is written, and the work the base quantiser counted is carried
    across unchanged plus the ``24`` scalings each way.
    """
    factor = Fraction(2) ** exponent
    shrunk = tuple(value / factor for value in values)
    inner = _quantise_uncached(shrunk, base)
    scaled = [coordinate * factor for coordinate in inner.point]
    for coordinate in scaled:
        if coordinate.denominator != 1:         # pragma: no cover - defensive
            raise ValueError(
                f"ladder_escalation: rung {rung!r} is not integral")
    point = tuple(int(coordinate) for coordinate in scaled)
    work = dict(inner.work)
    work["scalings"] = work.get("scalings", 0) + 2 * DIM
    return Quantisation(rung, point, inner.distance2 * factor * factor, work)


def reading(vector: Sequence,
            rungs: Sequence[str] = CL.RUNG_ORDER) -> Dict[str, Quantisation]:
    """The vector read at each named rung."""
    return {rung: quantise(vector, rung) for rung in rungs}


# ═════════════════════════════════════════════════════════════════════════
# 2.  THE DECLARED EXPERIMENT
# ═════════════════════════════════════════════════════════════════════════

#: How many named objects of each register the declared run uses, taken in the
#: register's own order -- not chosen, and not sampled at random.
SAMPLE_PER_REGISTER: int = 24

#: ``(label, support, magnitude)``.  The query is the carrier with ``magnitude``
#: added to, or subtracted from, ``support`` of its coordinates; which
#: coordinates and which signs is decided by a Golay codeword, so the sweep is
#: a function of the carrier's index alone.
#: The four magnitudes are chosen against the rungs' packing radii -- a rung of
#: minimum norm ``m`` returns the right point for any offset of squared length
#: below ``m/4`` -- so that the sweep crosses every rung's tolerance in turn:
#: ``1/8`` is inside ``Z``'s radius, ``1/2`` is past it, ``2`` is past ``D``'s
#: and inside ``A``'s, and ``9/2`` is past ``A``'s and inside ``C``'s.
PERTURBATIONS: Tuple[Tuple[str, int, Fraction], ...] = (
    ("8 coordinates by 1/8", 8, Fraction(1, 8)),
    ("8 coordinates by 1/4", 8, Fraction(1, 4)),
    ("8 coordinates by 1/2", 8, Fraction(1, 2)),
    ("8 coordinates by 3/4", 8, Fraction(3, 4)),
)

def orders_for(rungs: Sequence[str]) -> Dict[str, Tuple[str, ...]]:
    """The three visiting orders of a ladder, all with the same stopping rule."""
    keys = tuple(rungs)
    return {
        "middle_out": CL.middle_out_order(keys),
        "coarse_to_fine": keys,
        "fine_to_coarse": tuple(reversed(keys)),
    }


#: The orders the rungs of the declared ladder are visited in.
ORDERS: Dict[str, Tuple[str, ...]] = orders_for(CL.RUNG_ORDER)

#: The ladder lengths the sweep measures.  Five is the note's own ladder and
#: the recorded "before"; eleven is the ladder this module now declares; the
#: longer ones are measured to find where the escalation stops being safe.
LADDER_LENGTHS: Tuple[int, ...] = (5, 7, 9, 11, 13, 15)


def sample_carriers() -> Tuple[Tuple[str, str, Tuple[Fraction, ...]], ...]:
    """``(register, name, carrier)`` for the declared sample."""
    from . import escalation as ESC
    out: List[Tuple[str, str, Tuple[Fraction, ...]]] = []
    seen: Dict[str, int] = {}
    for entry in ESC.register_carriers():
        taken = seen.get(entry.register, 0)
        if taken >= SAMPLE_PER_REGISTER:
            continue
        seen[entry.register] = taken + 1
        out.append((entry.register, entry.name, entry.carrier))
    return tuple(out)


def perturb(carrier: Sequence[Fraction], index: int,
            support: int, magnitude: Fraction) -> Tuple[Fraction, ...]:
    """The declared deterministic offset applied to one carrier.

    Codeword ``index mod 4096`` chooses the coordinates -- its support,
    truncated to ``support`` entries in increasing order -- and the parity of
    the coordinate's position inside that support chooses the sign.
    """
    word = mog.GOLAY_MASKS[index % len(mog.GOLAY_MASKS)]
    chosen = [i for i in range(DIM) if (word >> i) & 1][:support]
    if len(chosen) < support:                   # short codeword: wrap around
        extra = [i for i in range(DIM) if i not in chosen]
        chosen = chosen + extra[:support - len(chosen)]
    values = list(Fraction(x) for x in carrier)
    for rank, coordinate in enumerate(chosen):
        sign = 1 if rank % 2 == 0 else -1
        values[coordinate] += sign * magnitude
    return tuple(values)


# ═════════════════════════════════════════════════════════════════════════
# 3.  THE INDEX, AND THE READING THAT USES IT
# ═════════════════════════════════════════════════════════════════════════

def rung_index(rung: str,
               carriers: Sequence[Tuple[str, str, Tuple[Fraction, ...]]]
               ) -> Dict[Tuple[int, ...], Tuple[int, ...]]:
    """``lattice point -> the carriers that quantise to it`` at one rung."""
    table: Dict[Tuple[int, ...], List[int]] = {}
    for i, (_, _, carrier) in enumerate(carriers):
        point = quantise(carrier, rung).point
        table.setdefault(point, []).append(i)
    return {point: tuple(members) for point, members in table.items()}


def occupancy(indices: Dict[str, Dict[Tuple[int, ...], Tuple[int, ...]]],
              rungs: Optional[Sequence[str]] = None
              ) -> Tuple[Dict[str, object], ...]:
    """How many carriers each rung separates, and how many it conflates."""
    out: List[Dict[str, object]] = []
    for rung in (rungs if rungs is not None else CL.RUNG_ORDER):
        table = indices[rung]
        singletons = sum(1 for members in table.values() if len(members) == 1)
        conflated = sum(len(members) for members in table.values()
                        if len(members) > 1)
        out.append({
            "rung": rung,
            "cells": len(table),
            "separated": singletons,
            "conflated": conflated,
            "largest_cell": max((len(m) for m in table.values()), default=0),
        })
    return tuple(out)


def answer_at_rung(query: Sequence[Fraction], rung: str,
                   indices: Dict[str, Dict[Tuple[int, ...], Tuple[int, ...]]]
                   ) -> Tuple[Optional[int], int]:
    """The carrier a single rung names, and the work it cost.

    ``None`` means the rung's cell is empty or holds more than one carrier --
    in either case the rung has not named anything.
    """
    quantised = quantise(query, rung)
    members = indices[rung].get(quantised.point, ())
    return (members[0] if len(members) == 1 else None), quantised.cost


def answer_with_order(query: Sequence[Fraction], order: Sequence[str],
                      indices: Dict[str, Dict[Tuple[int, ...], Tuple[int, ...]]]
                      ) -> Dict[str, object]:
    """Walk the rungs in this order, stopping at the first one that names one
    carrier."""
    cost = 0
    visited: List[str] = []
    for rung in order:
        visited.append(rung)
        named, rung_cost = answer_at_rung(query, rung, indices)
        cost += rung_cost
        if named is not None:
            return {"named": named, "rung": rung, "visited": tuple(visited),
                    "cost": cost}
    return {"named": None, "rung": None, "visited": tuple(visited),
            "cost": cost}


def order_facts() -> Dict[str, object]:
    """The middle-out walk, checked here as well as proved in Lean."""
    walk = CL.middle_out_order()
    return {
        "ladder": CL.RUNG_ORDER,
        "middle": CL.MIDDLE,
        "middle_out": walk,
        "visits_every_rung_once": sorted(walk) == sorted(CL.RUNG_ORDER),
        "starts_in_the_middle": walk[0] == CL.MIDDLE,
        "lean": "GLM.ConstructionLadder.middleOut_nodup, "
                "GLM.ConstructionLadder.middleOut_length, "
                "GLM.ConstructionLadder.middleOut_head",
    }


# ═════════════════════════════════════════════════════════════════════════
# 4.  THE RUN
# ═════════════════════════════════════════════════════════════════════════

def _score(rows: Sequence[Dict[str, object]]) -> Dict[str, object]:
    correct = sum(1 for row in rows if row["verdict"] == "correct")
    wrong = sum(1 for row in rows if row["verdict"] == "wrong")
    refused = sum(1 for row in rows if row["verdict"] == "refused")
    return {
        "queries": len(rows),
        "correct": correct,
        "wrong": wrong,
        "refused": refused,
        "cost": sum(int(row["cost"]) for row in rows),
        "rungs_visited": sum(int(row["visits"]) for row in rows),
    }


def _verdict(named: Optional[int], truth: int) -> str:
    if named is None:
        return "refused"
    return "correct" if named == truth else "wrong"


def run_orders(carriers=None, perturbations=PERTURBATIONS,
               rungs: Optional[Sequence[str]] = None
               ) -> Dict[str, object]:
    """Every order, over every declared perturbation of every sample carrier."""
    carriers = carriers if carriers is not None else sample_carriers()
    ladder = tuple(rungs) if rungs is not None else CL.RUNG_ORDER
    orders = orders_for(ladder)
    indices = {rung: rung_index(rung, carriers) for rung in ladder}
    results: Dict[str, object] = {}
    per_setting: List[Dict[str, object]] = []
    for label, support, magnitude in perturbations:
        setting_rows: Dict[str, List[Dict[str, object]]] = {
            name: [] for name in orders}
        for i, (_, _, carrier) in enumerate(carriers):
            query = perturb(carrier, i, support, magnitude)
            for name, order in orders.items():
                found = answer_with_order(query, order, indices)
                setting_rows[name].append({
                    "carrier": i,
                    "verdict": _verdict(found["named"], i),   # type: ignore[arg-type]
                    "rung": found["rung"],
                    "cost": found["cost"],
                    "visits": len(found["visited"]),          # type: ignore[arg-type]
                })
        per_setting.append({
            "perturbation": label,
            "support": support,
            "magnitude": str(magnitude),
            "orders": {name: _score(rows)
                       for name, rows in setting_rows.items()},
            "resolving_rung": {
                name: _rung_histogram(rows)
                for name, rows in setting_rows.items()},
        })
    results["settings"] = tuple(per_setting)
    results["rungs"] = ladder
    results["occupancy"] = occupancy(indices, ladder)
    results["totals"] = {
        name: {
            "correct": sum(int(setting["orders"][name]["correct"])      # type: ignore[index]
                           for setting in per_setting),
            "wrong": sum(int(setting["orders"][name]["wrong"])          # type: ignore[index]
                         for setting in per_setting),
            "refused": sum(int(setting["orders"][name]["refused"])      # type: ignore[index]
                           for setting in per_setting),
            "cost": sum(int(setting["orders"][name]["cost"])            # type: ignore[index]
                        for setting in per_setting),
            "rungs_visited": sum(int(setting["orders"][name]["rungs_visited"])  # type: ignore[index]
                                 for setting in per_setting),
        }
        for name in orders
    }
    return results


def _rung_histogram(rows: Sequence[Dict[str, object]]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for row in rows:
        key = str(row["rung"]) if row["rung"] else "none"
        out[key] = out.get(key, 0) + 1
    return dict(sorted(out.items()))


def run_fixed_rungs(carriers=None, perturbations=PERTURBATIONS,
                    rungs: Optional[Sequence[str]] = None
                    ) -> Dict[str, object]:
    """The controls: each rung read alone, which is what a partial system does."""
    carriers = carriers if carriers is not None else sample_carriers()
    ladder = tuple(rungs) if rungs is not None else CL.RUNG_ORDER
    indices = {rung: rung_index(rung, carriers) for rung in ladder}
    per_setting: List[Dict[str, object]] = []
    for label, support, magnitude in perturbations:
        rung_rows: Dict[str, List[Dict[str, object]]] = {
            rung: [] for rung in ladder}
        for i, (_, _, carrier) in enumerate(carriers):
            query = perturb(carrier, i, support, magnitude)
            for rung in ladder:
                named, cost = answer_at_rung(query, rung, indices)
                rung_rows[rung].append({
                    "carrier": i, "verdict": _verdict(named, i),
                    "named": named,
                    "cost": cost, "visits": 1, "rung": rung})
        oracle = sum(
            1 for i in range(len(carriers))
            if any(rung_rows[rung][i]["verdict"] == "correct"
                   for rung in ladder))
        scores = {rung: _score(rows) for rung, rows in rung_rows.items()}
        best = max(scores.items(),
                   key=lambda item: (item[1]["correct"], -item[1]["wrong"]))
        named_by_two = 0
        disagreements = 0
        for i in range(len(carriers)):
            names = {rung_rows[rung][i]["named"] for rung in ladder}
            names.discard(None)
            if len(names) >= 1:
                named_by_two += 1
            if len(names) > 1:
                disagreements += 1
        per_setting.append({
            "perturbation": label,
            "rungs": scores,
            "best_rung": best[0],
            "best_correct": best[1]["correct"],
            "oracle": oracle,
            "queries_named_by_some_rung": named_by_two,
            "rungs_disagree": disagreements,
        })
    totals = {
        rung: {
            "correct": sum(int(setting["rungs"][rung]["correct"])       # type: ignore[index]
                           for setting in per_setting),
            "wrong": sum(int(setting["rungs"][rung]["wrong"])           # type: ignore[index]
                         for setting in per_setting),
            "refused": sum(int(setting["rungs"][rung]["refused"])       # type: ignore[index]
                           for setting in per_setting),
            "cost": sum(int(setting["rungs"][rung]["cost"])             # type: ignore[index]
                        for setting in per_setting),
        }
        for rung in ladder
    }
    totals["oracle"] = {"correct": sum(int(setting["oracle"])            # type: ignore[arg-type]
                                       for setting in per_setting)}
    return {
        "settings": tuple(per_setting),
        "totals": totals,
        "agreement": {
            "queries_named_by_some_rung": sum(
                int(setting["queries_named_by_some_rung"])               # type: ignore[arg-type]
                for setting in per_setting),
            "rungs_disagree": sum(int(setting["rungs_disagree"])         # type: ignore[arg-type]
                                  for setting in per_setting),
            "why_it_matters": (
                "when the rungs that name a carrier all name the same one, "
                "every visiting order returns the same answer, whatever the "
                "stopping rule -- which is "
                "GLM.ConstructionLadder.firstNamed_order_independent"),
        },
    }


def ladder_escalation_report(rungs: Optional[Sequence[str]] = None
                             ) -> Dict[str, object]:
    """Everything this round knows, recomputed on call."""
    carriers = sample_carriers()
    ladder = tuple(rungs) if rungs is not None else CL.RUNG_ORDER
    orders = run_orders(carriers, rungs=ladder)
    fixed = run_fixed_rungs(carriers, rungs=ladder)
    best_fixed = max(((rung, scores) for rung, scores
                      in fixed["totals"].items() if rung != "oracle"),   # type: ignore[union-attr]
                     key=lambda item: (item[1]["correct"], -item[1]["wrong"]))
    ladder_scores = orders["totals"]["middle_out"]                       # type: ignore[index]
    return {
        "carriers": len(carriers),
        "ladder": ladder,
        "ladder_length": len(ladder),
        "registers": sorted({register for register, _, _ in carriers}),
        "perturbations": tuple({"label": label, "support": support,
                                "magnitude": str(magnitude)}
                               for label, support, magnitude in PERTURBATIONS),
        "order_facts": order_facts(),
        "orders": orders,
        "fixed_rungs": fixed,
        "best_fixed_rung": {"rung": best_fixed[0], **best_fixed[1]},
        "best_rung_per_setting": tuple(
            {"perturbation": setting["perturbation"],                    # type: ignore[index]
             "best_rung": setting["best_rung"],                          # type: ignore[index]
             "best_correct": setting["best_correct"],                    # type: ignore[index]
             "oracle": setting["oracle"]}                                # type: ignore[index]
            for setting in fixed["settings"]),                           # type: ignore[union-attr]
        "oracle": int(fixed["totals"]["oracle"]["correct"]),             # type: ignore[index]
        "agreement": fixed["agreement"],                                 # type: ignore[index]
        "order_cost": {
            name: int(scores["cost"])                                    # type: ignore[index]
            for name, scores in orders["totals"].items()},               # type: ignore[union-attr]
        "cheapest_order": min(
            orders["totals"].items(),                                    # type: ignore[union-attr]
            key=lambda item: int(item[1]["cost"]))[0],
        "ladder_over_best_fixed": {
            "correct": int(ladder_scores["correct"])
            - int(best_fixed[1]["correct"]),
            "wrong": int(ladder_scores["wrong"]) - int(best_fixed[1]["wrong"]),
        },
        "method": (
            f"Every carrier of the declared sample is indexed at all "
            f"{len(ladder)} rungs; a query is the carrier with a "
            f"deterministic offset added; a rung answers only when its cell "
            f"holds exactly one carrier; the three orders differ only in "
            f"which rung is tried first."),
        "limits": (
            "The sample is the first 24 named objects of each of six "
            "registers, and the perturbations are four declared settings, so "
            "the figures are about this sample and this sweep. A wrong answer "
            "is reported separately from a refusal and is never folded into "
            "an accuracy."),
    }


def length_sweep(carriers=None,
                 lengths: Sequence[int] = LADDER_LENGTHS
                 ) -> Dict[str, object]:
    """The same experiment at several ladder lengths -- how long is too long?

    Thickening the ladder can only help while the rungs keep agreeing: the
    order-independence theorem
    (``GLM.ConstructionLadder.firstNamed_order_independent``) needs every rung
    that names a carrier to name the same one, and a rung coarse enough to put
    two carriers in one cell *and* to be the first rung asked can break that.
    This sweep measures where it breaks rather than assuming it does not.
    """
    carriers = carriers if carriers is not None else sample_carriers()
    rows: List[Dict[str, object]] = []
    for length in lengths:
        ladder = CL.ladder_of_length(length)
        orders = run_orders(carriers, rungs=ladder)
        fixed = run_fixed_rungs(carriers, rungs=ladder)
        totals = orders["totals"]                                        # type: ignore[index]
        correct = {name: int(scores["correct"])
                   for name, scores in totals.items()}                   # type: ignore[union-attr]
        wrong = {name: int(scores["wrong"])
                 for name, scores in totals.items()}                     # type: ignore[union-attr]
        refused = {name: int(scores["refused"])
                   for name, scores in totals.items()}                   # type: ignore[union-attr]
        rows.append({
            "length": length,
            "ladder": ladder,
            "middle": ladder[len(ladder) // 2],
            "correct": correct,
            "wrong": wrong,
            "refused": refused,
            "order_independent": len(set(correct.values())) == 1
            and len(set(wrong.values())) == 1,
            "rungs_disagree": int(fixed["agreement"]["rungs_disagree"]),    # type: ignore[index]
            "oracle": int(fixed["totals"]["oracle"]["correct"]),            # type: ignore[index]
            "matches_oracle": correct["middle_out"]
            == int(fixed["totals"]["oracle"]["correct"]),                   # type: ignore[index]
            "cost": {name: int(scores["cost"])
                     for name, scores in totals.items()},                # type: ignore[union-attr]
        })
    safe = [row for row in rows
            if max(row["wrong"].values()) == 0                           # type: ignore[union-attr]
            and row["order_independent"] and row["rungs_disagree"] == 0]
    broken = [row for row in rows if row not in safe]
    best = (max(safe, key=lambda row: int(row["correct"]["middle_out"]))  # type: ignore[index]
            if safe else None)
    return {
        "rows": tuple(rows),
        "lengths": tuple(lengths),
        "longest_safe": (int(best["length"]) if best else None),         # type: ignore[arg-type]
        "best_correct": (int(best["correct"]["middle_out"])              # type: ignore[index]
                         if best else None),
        "first_broken": (int(broken[0]["length"]) if broken else None),  # type: ignore[arg-type]
        "why_it_breaks": (
            "a rung coarse enough to hold two carriers in one cell can still "
            "hold exactly one -- the wrong one -- in the cell a perturbed "
            "query lands in, and then the rungs disagree and the answer "
            "depends on which rung was asked first"),
    }


# ═════════════════════════════════════════════════════════════════════════
# 5.  THE CACHE, GUARDED BY A DIGEST
# ═════════════════════════════════════════════════════════════════════════

DATA_PATH = (Path(__file__).resolve().parent / "_data"
             / "ladder_escalation.json")

_SOURCES: Tuple[str, ...] = (
    "reasoning/ladder_escalation.py",
    "substrate/construction_ladder.py",
    "substrate/golay_paley.py",
    "substrate/leech_construct.py",
    "reasoning/fwht_decode.py",
)


def module_digest() -> str:
    """One digest over the sources this measurement is taken from."""
    root = Path(__file__).resolve().parent.parent
    return integrity.tree_digest([root / name for name in _SOURCES], root)


def _freeze(value: object) -> object:
    if isinstance(value, Fraction):
        return {"__fraction__": f"{value.numerator}/{value.denominator}"}
    if isinstance(value, dict):
        return {str(key): _freeze(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_freeze(item) for item in value]
    return value


def measure() -> Dict[str, object]:
    """The report, with the digest of what it was taken from beside it.

    The headline is the declared eleven-rung ladder; the five-rung ladder the
    round started from is measured beside it and kept as the recorded
    "before", and the sweep records what every length in between does.
    """
    carriers = sample_carriers()
    payload = dict(ladder_escalation_report())
    payload["before"] = ladder_escalation_report(CL.BASE_ORDER)
    payload["length_sweep"] = length_sweep(carriers)
    payload["source_digest"] = module_digest()
    return payload


def write_measurements(path: Optional[Path] = None) -> Path:
    """Take the measurements and store them beside their digest."""
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(_freeze(measure()), indent=1, sort_keys=True,
                   ensure_ascii=False) + "\n", encoding="utf-8")
    return target


_cache: Optional[Dict[str, object]] = None


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    """What is stored, whether or not it is still current."""
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not DATA_PATH.exists():
        return None
    loaded = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    _cache = loaded if isinstance(loaded, dict) else None
    return _cache


def state() -> Dict[str, object]:
    """Present, and taken from the sources as they stand?"""
    stored = measurements()
    live = module_digest()
    if stored is None:
        return {"present": False, "fresh": False, "live_digest": live,
                "stored_digest": None, "verdict": "absent"}
    same = stored.get("source_digest") == live
    return {"present": True, "fresh": same, "live_digest": live,
            "stored_digest": stored.get("source_digest"),
            "verdict": "fresh" if same else "stale"}


def current() -> Optional[Dict[str, object]]:
    """The measurements if they still describe the sources, else ``None``."""
    stored = measurements()
    if stored is None or stored.get("source_digest") != module_digest():
        return None
    return stored


if __name__ == "__main__":                      # pragma: no cover
    print(f"wrote {write_measurements()}")
    print(f"digest {module_digest()}")
