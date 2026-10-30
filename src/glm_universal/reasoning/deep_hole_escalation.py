"""``glm_universal.reasoning.deep_hole_escalation`` -- the ladder that escalates
the reading until the law descends, or marks the boundary where it does not.

The question
------------
The first deep-hole round
(:mod:`glm_universal.reasoning.deep_hole_classifier`, ``studies/DEEP_HOLE_STUDY.md``)
stopped at its own sanity check: the arrival-share profile of a hole moved
further when the *ensemble seed* changed than the profiles of different hole
types are apart, so 3 of 10 holes kept their label and the pre-registered
decision tree stopped the round.

``studies/DEEP_HOLE_ESCALATION_STUDY.md`` asks whether that is a property of
the geometry or of the **layer the geometry was read at**, which is the
distinction ``studies/INFORMATION_LOSS_STUDY.md`` and ``GLM/Layers.lean``
exist to make.  Two things were done to the first statistic that a cumulative
reading would not do: the *strays* were excluded from the profile, and the
budget was fixed at 240 starts.  This module escalates on both axes along a
ladder fixed in the pre-registration, and reports the cheapest cell at which
the criterion holds -- or, if none does, the boundary with a number on it.

The ladder
----------
Four readings, three sizes, twelve cells:

``L1`` shares
    the first round's statistic, unchanged: arrival shares sorted descending,
    padded to 48, L1 metric.
``L2`` widened
    ``L1`` carried alongside the stray spectrum -- the shares, over *all*
    emissions, of the distinct raw squared distances above the minimum.  The
    distance is the sum of the two L1 distances, so it is cumulative over
    ``L1`` by construction.
``L3`` rational
    the exact measure on the rationals that puts mass ``1/N`` at each
    emission's raw squared distance from the centre, compared by the exact
    1-Wasserstein distance on the line.  This is the reading that uses the
    distance *values* and not merely their ordering.
``L4`` joint
    ``L2`` and ``L3`` added: the top of the ladder.

Sizes ``N`` in ``(240, 480, 960)``.  The declared sweep emits starts in a
fixed order, so the 240-start ensemble is a **prefix** of the 960-start one:
escalating ``N`` adds information and never replaces it, and one 960-start run
per ``(centre, seed)`` supplies every cell.

The gate
--------
The primary statistic is ``Q0``: how many of the ``K`` reference holes have
their *own* reference strictly nearest under the cell's metric when only the
ensemble seed is changed.  The gate is ``Q0 = K`` -- every hole recognises
itself.  Alongside it, every cell reports the scale-free ratio
``rho = 2W / B`` with ``W`` the worst seed shift and ``B`` the reference
separation; ``rho < 1`` is sufficient for the gate, and that implication is
``GLM.DeepHoleLadder.nearest_correct`` in Lean rather than an assumption here.

Exactness
---------
Integers and :class:`~fractions.Fraction` throughout -- offsets, distances,
shares, Wasserstein integrals, radii, ratios and tails.  The one declared
digest is the D3 control, which must carry no meaning for the control to be a
control (D9, D11).  The one non-enumerable step is the set of start offsets,
declared in the study.
"""

from __future__ import annotations

import json
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .. import integrity
from . import deep_hole_classifier as dhc
from . import niemeier
from . import wobble as wbl
from . import wobble_landscape as wls
from .fwht_decode import nearest_lattice_point_fwht

__all__ = [
    "STARTS_LADDER", "MAX_STARTS", "LAYER_KEYS", "CELLS",
    "STATISTICS_TRIED", "GATE_BITS", "REFERENCE_SEED", "SANITY_SEED",
    "emissions", "share_profile", "stray_profile", "rational_profile",
    "layer_profile", "layer_distance", "wasserstein1",
    "reference_entries", "cell", "ladder", "decision",
    "full_run", "deep_hole_escalation_report",
    "module_digest", "measure", "write_measurements", "measurements",
    "state", "current", "DATA_PATH", "rounded",
]


# ═════════════════════════════════════════════════════════════════════════
# 1.  THE PRE-REGISTERED CONSTANTS
# ═════════════════════════════════════════════════════════════════════════

#: The ladder of ensemble sizes, in the declared order.  Nested prefixes.
#: The first three were pre-registered; 1920 is the **extension rung**, added
#: after the twelve declared cells were measured and the sanity count was seen
#: to be climbing, and it is flagged as such in every table so that a rung
#: decided after the trend is never read as one decided before it.
DECLARED_STARTS: Tuple[int, ...] = (240, 480, 960)
EXTENSION_STARTS: Tuple[int, ...] = (1920,)
STARTS_LADDER: Tuple[int, ...] = DECLARED_STARTS + EXTENSION_STARTS

#: The largest rung, and therefore the only ensemble actually run.
MAX_STARTS: int = STARTS_LADDER[-1]

#: The ladder of readings, in the declared order of escalation.
LAYER_KEYS: Tuple[str, ...] = ("shares", "widened", "rational", "joint")

#: The twelve cells, layer first and then size, which is the order the
#: decision tree means by "the cheapest cell that passes".
CELLS: Tuple[Tuple[str, int], ...] = tuple(
    (layer, starts) for layer in LAYER_KEYS for starts in STARTS_LADDER)

#: The reference ensemble, and the sanity ensemble that only changes the seed.
REFERENCE_SEED: int = dhc.REFERENCE_SEED
SANITY_SEED: int = dhc.QUERY_SEEDS["seed"]

#: The multiplicity correction: 4 statistics in the first round, 12 declared
#: cells here, and the 4 cells of the extension rung -- counted whatever they
#: say, which is the point of correcting for them.
STATISTICS_TRIED: int = 20

#: The gate on a bit score, unchanged from the first round.
GATE_BITS: int = 3

#: How long a profile is padded to: the 48 vertices of the ``A_1^24`` hole.
PROFILE_LENGTH: int = dhc.PROFILE_LENGTH

#: The bottom rung must reproduce the first round, which named 3 of 10 holes
#: correctly under a bare seed change.  A stopping rule, not a target.
REPRODUCTION_EXPECTED: int = 3


# ═════════════════════════════════════════════════════════════════════════
# 2.  THE ENSEMBLE -- run once at the top rung, sliced for the others
# ═════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=None)
def emissions(center: Tuple[Fraction, ...], seed: int,
              starts: int = MAX_STARTS) -> Tuple[Tuple[Tuple[int, ...],
                                                       Fraction], ...]:
    """Every emission of the declared ensemble, in start order.

    One tick per start through the exact nearest-Leech-point decoder, and the
    emitted point kept with its exact raw squared distance to ``center``.
    Nothing is discarded here: which emissions count as strays is a decision
    of the *reading*, not of the ensemble, which is the repair of the narrow
    view the pre-registration describes.
    """
    point = [Fraction(x) for x in center]
    offsets = dhc.offsets(seed, starts)
    out: List[Tuple[Tuple[int, ...], Fraction]] = []
    for offset in offsets:
        driven = [offset[i] + point[i] for i in range(24)]
        emitted = nearest_lattice_point_fwht(driven).point
        distance = sum((point[i] - Fraction(emitted[i])) ** 2
                       for i in range(24))
        out.append((tuple(int(x) for x in emitted), distance))
    return tuple(out)


def prefix(record: Sequence[Tuple[Tuple[int, ...], Fraction]], starts: int
           ) -> Tuple[Tuple[Tuple[int, ...], Fraction], ...]:
    """The ``starts``-start ensemble, which is a prefix of a longer one."""
    return tuple(record[:starts])


# ═════════════════════════════════════════════════════════════════════════
# 3.  THE READINGS
# ═════════════════════════════════════════════════════════════════════════

def _sorted_padded(values: Sequence[Fraction]) -> Tuple[Fraction, ...]:
    shares = sorted(values, reverse=True)[:PROFILE_LENGTH]
    return tuple(list(shares) + [Fraction(0)] * (PROFILE_LENGTH - len(shares)))


def share_profile(record: Sequence[Tuple[Tuple[int, ...], Fraction]]
                  ) -> Tuple[Fraction, ...]:
    """``L1``: the arrival shares, sorted descending and padded to 48.

    An arrival is an emission at the minimum distance seen; anything further
    is a stray and is not in this profile.  This is the first round's
    statistic, reproduced rather than quoted.
    """
    if not record:
        return tuple([Fraction(0)] * PROFILE_LENGTH)
    best = min(distance for _point, distance in record)
    counts: Dict[Tuple[int, ...], int] = {}
    for point, distance in record:
        if distance == best:
            counts[point] = counts.get(point, 0) + 1
    total = sum(counts.values())
    if total <= 0:
        return tuple([Fraction(0)] * PROFILE_LENGTH)
    return _sorted_padded([Fraction(value, total) for value in counts.values()])


def stray_profile(record: Sequence[Tuple[Tuple[int, ...], Fraction]]
                  ) -> Tuple[Fraction, ...]:
    """The reading the first round discarded: the stray spectrum.

    The shares -- over *all* emissions, so that the stray fraction itself is
    retained rather than normalised away -- of the distinct raw squared
    distances above the minimum, sorted descending and padded to 48.
    """
    if not record:
        return tuple([Fraction(0)] * PROFILE_LENGTH)
    best = min(distance for _point, distance in record)
    spectrum: Dict[Fraction, int] = {}
    for _point, distance in record:
        if distance != best:
            spectrum[distance] = spectrum.get(distance, 0) + 1
    total = len(record)
    return _sorted_padded([Fraction(value, total)
                           for value in spectrum.values()])


def rational_profile(record: Sequence[Tuple[Tuple[int, ...], Fraction]]
                     ) -> Tuple[Tuple[Fraction, Fraction], ...]:
    """``L3``: the exact measure on the rationals of emission distances.

    Mass ``1/N`` at each emission's raw squared distance from the centre,
    returned as ``(value, share)`` pairs sorted by value.  Unlike the share
    layers this reading uses the distance *values*, so a shift of the
    ensemble that moves which vertex a start lands on but not how far it
    lands moves this profile not at all.
    """
    if not record:
        return ()
    total = len(record)
    weights: Dict[Fraction, int] = {}
    for _point, distance in record:
        weights[distance] = weights.get(distance, 0) + 1
    return tuple(sorted((value, Fraction(count, total))
                        for value, count in weights.items()))


def l1(left: Sequence[Fraction], right: Sequence[Fraction]) -> Fraction:
    """The L1 distance between two padded profiles, exactly."""
    return sum(abs(Fraction(left[i]) - Fraction(right[i]))
               for i in range(PROFILE_LENGTH))


def wasserstein1(left: Sequence[Tuple[Fraction, Fraction]],
                 right: Sequence[Tuple[Fraction, Fraction]]) -> Fraction:
    """The exact 1-Wasserstein distance between two measures on the line.

    ``int |F_left - F_right|`` as a finite sum of :class:`~fractions.Fraction`
    over the union of the two supports -- no float, no quadrature, and no
    tolerance.
    """
    support = sorted({value for value, _share in left}
                     | {value for value, _share in right})
    if len(support) < 2:
        return Fraction(0)
    left_map = {value: share for value, share in left}
    right_map = {value: share for value, share in right}
    total = Fraction(0)
    cumulative_left = Fraction(0)
    cumulative_right = Fraction(0)
    for index in range(len(support) - 1):
        value = support[index]
        cumulative_left += left_map.get(value, Fraction(0))
        cumulative_right += right_map.get(value, Fraction(0))
        width = support[index + 1] - value
        total += abs(cumulative_left - cumulative_right) * width
    return total


def layer_profile(record: Sequence[Tuple[Tuple[int, ...], Fraction]],
                  layer: str) -> object:
    """The reading of one rung, applied to an ensemble record."""
    if layer == "shares":
        return share_profile(record)
    if layer == "widened":
        return (share_profile(record), stray_profile(record))
    if layer == "rational":
        return rational_profile(record)
    if layer == "joint":
        return (share_profile(record), stray_profile(record),
                rational_profile(record))
    raise ValueError(f"layer_profile: unknown layer {layer!r}")


def layer_distance(left: object, right: object, layer: str) -> Fraction:
    """The rung's metric.  Each obeys the triangle inequality, which is what
    ``GLM.DeepHoleLadder.Reading`` requires of a rung."""
    if layer == "shares":
        return l1(left, right)                      # type: ignore[arg-type]
    if layer == "widened":
        return (l1(left[0], right[0])               # type: ignore[index]
                + l1(left[1], right[1]))            # type: ignore[index]
    if layer == "rational":
        return wasserstein1(left, right)            # type: ignore[arg-type]
    if layer == "joint":
        return (l1(left[0], right[0])               # type: ignore[index]
                + l1(left[1], right[1])             # type: ignore[index]
                + wasserstein1(left[2], right[2]))  # type: ignore[index]
    raise ValueError(f"layer_distance: unknown layer {layer!r}")


LAYER_NAMES: Dict[str, str] = {
    "shares": "L1 - arrival shares (the first round's statistic)",
    "widened": "L2 - arrival shares widened by the stray spectrum",
    "rational": "L3 - the exact rational measure of emission distances",
    "joint": "L4 - the joint reading, L2 and L3 together",
}


# ═════════════════════════════════════════════════════════════════════════
# 4.  THE REFERENCE HOLES -- the first round's, unchanged
# ═════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=None)
def reference_entries() -> Tuple[Tuple[Dict[str, object], ...],
                                 Tuple[Dict[str, object], ...]]:
    """The first certified centre of each type, and the sibling centres.

    Exactly the first round's rule, over exactly the first round's holes:
    nothing about the geometry is re-derived here, only the reading of it.
    """
    holes = dhc.reference_holes()
    entries: List[Dict[str, object]] = []
    siblings: List[Dict[str, object]] = []
    seen: Dict[str, int] = {}
    for hole in holes:
        label = hole["type"]
        if not hole["certified"] or not label:
            continue
        if label in seen:
            siblings.append(dict(hole))
            continue
        seen[str(label)] = len(entries)
        entries.append(dict(hole))
    return tuple(entries), tuple(siblings)


# ═════════════════════════════════════════════════════════════════════════
# 5.  ONE CELL OF THE LADDER
# ═════════════════════════════════════════════════════════════════════════

def _pairwise_minimum(profiles: Sequence[Tuple[str, object]], layer: str
                      ) -> Tuple[Optional[Fraction], Optional[Tuple[str, str]]]:
    best: Optional[Fraction] = None
    which: Optional[Tuple[str, str]] = None
    for i in range(len(profiles)):
        for j in range(i + 1, len(profiles)):
            distance = layer_distance(profiles[i][1], profiles[j][1], layer)
            if best is None or distance < best:
                best = distance
                which = (profiles[i][0], profiles[j][0])
    return best, which


@lru_cache(maxsize=None)
def cell(layer: str, starts: int) -> Dict[str, object]:
    """One cell of the ladder: the sanity count, the spread and the ratio.

    ``Q0`` is the number of reference holes whose own reference is *strictly*
    nearest under this rung's metric when only the ensemble seed is changed.
    ``rho = 2W/B`` is the scale-free criterion; ``rho < 1`` implies
    ``Q0 = K``, by ``GLM.DeepHoleLadder.nearest_correct``.
    """
    entries, _siblings = reference_entries()
    references: List[Tuple[str, object]] = []
    sanity: List[Tuple[str, object]] = []
    for entry in entries:
        centre = tuple(Fraction(x) for x in entry["center"])
        reference = prefix(emissions(centre, REFERENCE_SEED), starts)
        shifted = prefix(emissions(centre, SANITY_SEED), starts)
        references.append((str(entry["type"]), layer_profile(reference, layer)))
        sanity.append((str(entry["type"]), layer_profile(shifted, layer)))

    rows: List[Dict[str, object]] = []
    passes = 0
    worst: Optional[Fraction] = None
    for index, (label, profile) in enumerate(sanity):
        distances = [(name, layer_distance(profile, reference, layer))
                     for name, reference in references]
        own = distances[index][1]
        best = min(distance for _name, distance in distances)
        winners = [name for name, distance in distances if distance == best]
        correct = len(winners) == 1 and winners[0] == label
        if correct:
            passes += 1
        worst = own if worst is None else max(worst, own)
        ordered = sorted(distances, key=lambda row: (row[1], row[0]))
        rows.append({
            "label": label,
            "own_distance": own,
            "nearest": winners[0] if len(winners) == 1 else None,
            "nearest_distance": best,
            "own_rank": [name for name, _d in ordered].index(label) + 1,
            "correct": correct,
        })

    separation, closest = _pairwise_minimum(references, layer)
    ratio = (None if separation is None or separation == 0
             else Fraction(2) * worst / separation
             if worst is not None else None)
    return {
        "layer": layer,
        "layer_name": LAYER_NAMES[layer],
        "starts": starts,
        "declared": starts in DECLARED_STARTS,
        "holes": len(entries),
        "q0": passes,
        "gate": len(entries),
        "passes": passes == len(entries) and len(entries) > 0,
        "spread": worst,
        "separation": separation,
        "closest_pair": closest,
        "ratio": ratio,
        "ratio_below_one": ratio is not None and ratio < 1,
        "rows": tuple(rows),
    }


@lru_cache(maxsize=None)
def ladder() -> Tuple[Dict[str, object], ...]:
    """Every cell, in the declared order of escalation."""
    return tuple(cell(layer, starts) for layer, starts in CELLS)


# ═════════════════════════════════════════════════════════════════════════
# 6.  THE FULL QUERY SET AT A CELL
# ═════════════════════════════════════════════════════════════════════════

def _digest_pair(name: str, layer: str) -> object:
    """A geometry-free profile of the right shape for this rung (D3).

    This is the one declared digest of the round: a control has to carry no
    meaning at all, so it is built from a hash of the *name* and nothing
    else.  D11 -- the experiment needs an operation the project otherwise
    avoids, so the operation is declared instead of the round being dropped.
    """
    shares = dhc.digest_profile(name)
    strays = dhc.digest_profile(name + " · strays")
    measure_support = tuple(
        (Fraction(2) + Fraction(index, 8), share)
        for index, share in enumerate(dhc.digest_profile(name + " · measure")))
    if layer == "shares":
        return shares
    if layer == "widened":
        return (shares, strays)
    if layer == "rational":
        return measure_support
    return (shares, strays, measure_support)


def _uniform_pair(support: int, layer: str) -> object:
    """The ablation: the same support size, every share equal, no strays."""
    shares = dhc.uniform_profile(support)
    empty = tuple([Fraction(0)] * PROFILE_LENGTH)
    if layer == "shares":
        return shares
    if layer == "widened":
        return (shares, empty)
    if layer == "rational":
        return ((Fraction(2), Fraction(1)),)
    return (shares, empty, ((Fraction(2), Fraction(1)),))


def _support_of(record: Sequence[Tuple[Tuple[int, ...], Fraction]]) -> int:
    if not record:
        return 0
    best = min(distance for _point, distance in record)
    return len({point for point, distance in record if distance == best})


@lru_cache(maxsize=None)
def query_set(starts: int) -> Tuple[Dict[str, object], ...]:
    """The first round's query set, re-certified, with the full record kept."""
    entries, siblings = reference_entries()
    queries: List[Dict[str, object]] = []
    for index, entry in enumerate(entries):
        for transform in dhc.transforms():
            kind = str(transform["kind"])
            centre = tuple(Fraction(x)
                           for x in dhc._apply(kind, entry["center"]))
            moved = tuple(sorted(dhc._apply_point(kind, v)
                                 for v in entry["vertices"]))
            check = dhc._certify_at(centre, moved)
            name = f"hole {index} · {transform['key']}"
            if not check["certified"] or check["type"] != entry["type"]:
                queries.append({
                    "name": name, "truth": entry["type"], "used": False,
                    "reason": (f"the transform did not re-certify as "
                               f"{entry['type']}, so it is dropped"),
                })
                continue
            record = prefix(emissions(centre, int(transform["seed"])), starts)
            queries.append({
                "name": name, "truth": entry["type"], "used": True,
                "seed": int(transform["seed"]), "record": record,
                "support": _support_of(record), "reason": "",
            })
    for sibling in siblings:
        centre = tuple(Fraction(x) for x in sibling["center"])
        record = prefix(emissions(centre, dhc.QUERY_SEEDS["sibling"]), starts)
        queries.append({
            "name": f"{sibling['name']} · sibling centre",
            "truth": sibling["type"], "used": True,
            "seed": dhc.QUERY_SEEDS["sibling"], "record": record,
            "support": _support_of(record), "reason": "",
        })
    return tuple(queries)


def _nearest(profile: object, table: Sequence[Tuple[str, object]],
             layer: str) -> Dict[str, object]:
    """The nearest-reference rule of the pre-registration's §4.

    No radius: the rung's metrics are not commensurable, so the rule that is
    escalated is the one the primary statistic is defined by -- strictly
    nearest names, a tie refuses.  The radius questions are the secondaries.
    """
    distances = [(label, layer_distance(profile, reference, layer))
                 for label, reference in table]
    if not distances:
        return {"verdict": "absent", "label": None, "distance": None,
                "distances": ()}
    best = min(distance for _label, distance in distances)
    winners = [label for label, distance in distances if distance == best]
    ordered = tuple(sorted(distances, key=lambda row: (row[1], row[0])))
    if len(winners) > 1:
        return {"verdict": "ambiguous", "label": None, "distance": best,
                "distances": ordered}
    return {"verdict": "named", "label": winners[0], "distance": best,
            "distances": ordered}


def _run(name: str, queries: Sequence[Dict[str, object]],
         table: Sequence[Tuple[str, object]], layer: str,
         profile_of: Callable[[Dict[str, object]], object]) -> Dict[str, object]:
    """One classifier over the whole query set, method or control alike."""
    rows: List[Dict[str, object]] = []
    correct = 0
    refused = 0
    wrong = 0
    for query in queries:
        if not query.get("used"):
            continue
        outcome = _nearest(profile_of(query), table, layer)
        ranked = [label for label, _distance in outcome["distances"]]
        own = next((distance for label, distance in outcome["distances"]
                    if label == query["truth"]), None)
        hit = (outcome["verdict"] == "named"
               and outcome["label"] == query["truth"])
        if hit:
            correct += 1
        elif outcome["verdict"] == "named":
            wrong += 1
        else:
            refused += 1
        rows.append({
            "query": query["name"], "truth": query["truth"],
            "verdict": outcome["verdict"], "label": outcome["label"],
            "distance": outcome["distance"], "own_distance": own,
            "own_rank": (ranked.index(str(query["truth"])) + 1
                         if str(query["truth"]) in ranked else None),
            "correct": hit,
        })
    total = len(rows)
    labels = max(1, len(table))
    tail = dhc.tail_probability(correct, total, labels)
    return {
        "name": name, "rows": tuple(rows), "queries": total,
        "correct": correct, "wrong": wrong, "refused": refused,
        "accuracy": Fraction(correct, total) if total else Fraction(0),
        "chance": Fraction(1, labels), "tail": tail,
        "score": wls.bit_score(tail, STATISTICS_TRIED),
    }


@lru_cache(maxsize=None)
def full_run(layer: str, starts: int) -> Dict[str, object]:
    """The method and every control at one cell, over the full query set."""
    entries, _siblings = reference_entries()
    queries = query_set(starts)
    table: List[Tuple[str, object]] = []
    for entry in entries:
        centre = tuple(Fraction(x) for x in entry["center"])
        record = prefix(emissions(centre, REFERENCE_SEED), starts)
        table.append((str(entry["type"]), layer_profile(record, layer)))

    method = _run("the escalated reading", queries, tuple(table), layer,
                  lambda query: layer_profile(query["record"], layer))

    digest_table = tuple((label, _digest_pair(label, layer))
                         for label, _profile in table)
    digest = _run("digest control (D3)", queries, digest_table, layer,
                  lambda query: _digest_pair(str(query["name"]), layer))

    shuffled = dhc._reshuffled([label for label, _p in table])
    reshuffle_table = tuple((shuffled[i], table[i][1])
                            for i in range(len(table)))
    reshuffle = _run("seeded reshuffle of the pairing", queries,
                     reshuffle_table, layer,
                     lambda query: layer_profile(query["record"], layer))

    count_table = tuple(
        (label, _uniform_pair(_support_of(prefix(
            emissions(tuple(Fraction(x) for x in entry["center"]),
                      REFERENCE_SEED), starts)), layer))
        for (label, _profile), entry in zip(table, entries))
    ablation = _run("uniform-profile ablation", queries, count_table, layer,
                    lambda query: _uniform_pair(int(query["support"]), layer))

    baseline_rows = []
    baseline_correct = 0
    baseline_refused = 0
    supports: Dict[int, List[str]] = {}
    for (label, _profile), entry in zip(table, entries):
        centre = tuple(Fraction(x) for x in entry["center"])
        support = _support_of(prefix(emissions(centre, REFERENCE_SEED), starts))
        supports.setdefault(support, []).append(label)
    for query in queries:
        if not query.get("used"):
            continue
        candidates = supports.get(int(query["support"]), [])
        named = candidates[0] if len(candidates) == 1 else None
        hit = named == query["truth"]
        if hit:
            baseline_correct += 1
        if named is None:
            baseline_refused += 1
        baseline_rows.append({"query": query["name"], "truth": query["truth"],
                              "verdict": "named" if named else "ambiguous",
                              "label": named, "correct": hit})
    total = len(baseline_rows)
    baseline_tail = dhc.tail_probability(baseline_correct, total, len(table))
    baseline = {
        "name": "the plain vertex count", "rows": tuple(baseline_rows),
        "queries": total, "correct": baseline_correct, "wrong": 0,
        "refused": baseline_refused,
        "accuracy": Fraction(baseline_correct, total) if total else Fraction(0),
        "chance": Fraction(1, max(1, len(table))), "tail": baseline_tail,
        "score": wls.bit_score(baseline_tail, STATISTICS_TRIED),
    }

    own = [row["own_distance"] for row in method["rows"]
           if row["own_distance"] is not None]
    faithfulness = max(own) if own else None
    separation, closest = _pairwise_minimum(tuple(table), layer)
    certified = None if separation is None else Fraction(separation) / 2
    return {
        "layer": layer, "layer_name": LAYER_NAMES[layer], "starts": starts,
        "method": method, "controls": (digest, reshuffle, baseline, ablation),
        "digest": digest, "reshuffle": reshuffle, "baseline": baseline,
        "ablation": ablation,
        "faithfulness_radius": faithfulness,
        "separation": separation, "closest_pair": closest,
        "certified_radius": certified,
        "faithfulness_compatible": (faithfulness is not None
                                    and certified is not None
                                    and faithfulness <= certified),
        "own_rank_first": sum(1 for row in method["rows"]
                              if row["own_rank"] == 1),
        "mean_own_rank": (Fraction(sum(row["own_rank"]
                                       for row in method["rows"]
                                       if row["own_rank"] is not None),
                                   max(1, len(method["rows"])))),
        "beats_baseline": method["accuracy"] > baseline["accuracy"],
        "beats_every_control": all(method["accuracy"] > control["accuracy"]
                                   for control in (digest, reshuffle,
                                                   baseline, ablation)),
    }


# ═════════════════════════════════════════════════════════════════════════
# 7.  THE DECISION TREE, AS PRE-REGISTERED
# ═════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=None)
def decision() -> Dict[str, object]:
    """The pre-registered tree of §7 of the study, applied to the cells."""
    cells = ladder()
    declared = tuple(row for row in cells if row["declared"])
    extension = tuple(row for row in cells if not row["declared"])
    bottom = next(row for row in cells
                  if row["layer"] == "shares" and row["starts"] == 240)
    reproduces = bottom["q0"] == REPRODUCTION_EXPECTED

    def _rank(row: Dict[str, object]):
        return (row["q0"], -(row["ratio"] if row["ratio"] is not None
                             else Fraction(10 ** 9)))

    winner = next((row for row in cells if row["passes"]), None)
    declared_winner = next((row for row in declared if row["passes"]), None)
    best = max(cells, key=_rank)
    declared_best = max(declared, key=_rank)
    rises = best["q0"] > bottom["q0"]
    if not reproduces:
        verdict = "stopped: the bottom rung does not reproduce the first round"
        reading = ("The ladder's bottom rung is the first round's cell, and it "
                   "must return the first round's number before anything above "
                   "it is read.  It does not, so nothing above it is read.")
    elif winner is not None:
        verdict = "the law descends"
        reading = (f"The gate is reached at {winner['layer_name']} with "
                   f"{winner['starts']} starts, which is the cheapest cell in "
                   f"the declared order that reaches it"
                   + (" -- and it is a cell of the extension rung, decided "
                      "after the twelve pre-registered cells were measured, "
                      "so it is reported as an extension and not as the "
                      "pre-registered result."
                      if not winner["declared"] else
                      ", and it is one of the twelve pre-registered cells."))
    elif rises:
        verdict = "a boundary, with the ladder still climbing"
        reading = ("No cell reaches the gate, and the sanity count does rise "
                   "along the ladder, so the reading is climbing towards the "
                   "boundary and this budget does not reach it.  The "
                   "extrapolation is refused: nothing is claimed about a cell "
                   "that was not run.")
    else:
        verdict = "a boundary, and the escalation thesis refuted here"
        reading = ("No cell reaches the gate and the sanity count does not "
                   "rise along the ladder.  Widening and enlarging the reading "
                   "do not help with this question, so the obstruction is not "
                   "resolution -- which is a negative result against this "
                   "project's own framework and is recorded as one.")
    return {
        "verdict": verdict,
        "reading": reading,
        "reproduces": reproduces,
        "bottom": bottom,
        "expected": REPRODUCTION_EXPECTED,
        "winner": winner,
        "best": best,
        "declared_winner": declared_winner,
        "declared_best": declared_best,
        "declared_cells": len(declared),
        "extension_cells": len(extension),
        "winner_is_extension": winner is not None and not winner["declared"],
        "best_is_extension": not best["declared"],
        "rises": rises,
        "gate": bottom["gate"],
        "run_full_query_set": winner is not None,
    }


def _cost() -> Dict[str, object]:
    """What the round cost, in the only unit that is exact: decoder calls."""
    entries, siblings = reference_entries()
    ensembles = 2 * len(entries)
    return {
        "ensembles": ensembles,
        "starts_each": MAX_STARTS,
        "decoder_calls": ensembles * MAX_STARTS,
        "cells": len(CELLS),
        "note": (f"One ensemble per centre and seed at the top rung, sliced "
                 f"for the rungs below it, so the {len(CELLS)} cells cost one "
                 f"run each of {MAX_STARTS} starts rather than {len(CELLS)}."),
        "sibling_centres": len(siblings),
    }


# ═════════════════════════════════════════════════════════════════════════
# 8.  THE REPORT
# ═════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=None)
def deep_hole_escalation_report() -> Dict[str, object]:
    """Everything this module knows, recomputed on call."""
    cells = ladder()
    tree = decision()
    entries, siblings = reference_entries()
    run = (full_run(str(tree["winner"]["layer"]), int(tree["winner"]["starts"]))
           if tree["winner"] is not None else None)
    return {
        "cells": cells,
        "decision": tree,
        "run": run,
        "holes": len(entries),
        "siblings": len(siblings),
        "labels": tuple(str(entry["type"]) for entry in entries),
        "starts_ladder": STARTS_LADDER,
        "layers": LAYER_KEYS,
        "layer_names": LAYER_NAMES,
        "statistics_tried": STATISTICS_TRIED,
        "gate_bits": GATE_BITS,
        "reference_seed": REFERENCE_SEED,
        "sanity_seed": SANITY_SEED,
        "catalogue_size": len(niemeier.NIEMEIER_ROOT_SYSTEMS),
        "cost": _cost(),
        "method": (
            "The first deep-hole round stopped because its statistic could "
            "not recognise a hole as itself under a changed ensemble seed.  "
            "This round asks whether that was the geometry or the layer it "
            "was read at, by escalating the reading along a declared ladder: "
            "four readings, from the first round's arrival shares up to the "
            "shares widened by the discarded strays and joined to the exact "
            "rational measure of emission distances, each at 240, 480 and "
            "960 starts.  The gate is that every reference hole recognises "
            "itself, and the cheapest cell that reaches it is the answer."),
        "limits": (
            "The hole set is the first round's and is not enlarged, so the "
            "13 unreached Niemeier types stay unreached.  No pairwise vertex "
            "distance, diagram shape or component-size vector is read at any "
            "rung, because those are the label source.  And nothing is "
            "extrapolated past the top rung: if 960 starts and the joint "
            "reading do not pass, the study says what the ratio was and "
            "refuses to say what a larger ensemble would do."),
    }


# ═════════════════════════════════════════════════════════════════════════
# 9.  THE CACHE, GUARDED BY A DIGEST
# ═════════════════════════════════════════════════════════════════════════

DATA_PATH = (Path(__file__).resolve().parent / "_data"
             / "deep_hole_escalation.json")

#: A change to any of these makes the cache stale, which is D4.
_SOURCES: Tuple[str, ...] = (
    "reasoning/deep_hole_escalation.py",
    "reasoning/deep_hole_classifier.py",
    "reasoning/deep_holes.py",
    "reasoning/voronoi_walk.py",
    "reasoning/fwht_decode.py",
    "reasoning/niemeier.py",
    "substrate/isomorphism.py",
    "substrate/leech2.py",
)


def module_digest() -> str:
    """One digest over the sources this measurement is taken from."""
    root = Path(__file__).resolve().parent.parent
    return integrity.tree_digest([root / name for name in _SOURCES], root)


def _freeze(value: object) -> object:
    if isinstance(value, Fraction):
        return {"__fraction__": f"{value.numerator}/{value.denominator}"}
    if isinstance(value, dict):
        return {"__items__": [[_freeze(key), _freeze(item)]
                              for key, item in value.items()]} \
            if any(not isinstance(key, str) for key in value) \
            else {str(key): _freeze(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_freeze(item) for item in value]
    return value


def _thaw(value: object) -> object:
    if isinstance(value, dict):
        text = value.get("__fraction__")
        if isinstance(text, str) and len(value) == 1:
            return Fraction(text)
        items = value.get("__items__")
        if isinstance(items, list) and len(value) == 1:
            return {_hashable(_thaw(key)): _thaw(item) for key, item in items}
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_thaw(item) for item in value]
    return value


def _hashable(value: object) -> object:
    if isinstance(value, list):
        return tuple(_hashable(item) for item in value)
    return value


def _without_records(payload: Dict[str, object]) -> Dict[str, object]:
    """The report without the raw ensembles, which are large and derivable."""
    out = dict(payload)
    run = out.get("run")
    if isinstance(run, dict):
        out["run"] = {key: value for key, value in run.items()}
    return out


def measure() -> Dict[str, object]:
    """The report, with the digest of what it was taken from beside it."""
    payload = _without_records(dict(deep_hole_escalation_report()))
    payload["source_digest"] = module_digest()
    return payload


def write_measurements(path: Optional[Path] = None) -> Path:
    """Take the measurements and store them beside their digest."""
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(_freeze(measure()), indent=1, sort_keys=True,
                   ensure_ascii=False) + "\n",
        encoding="utf-8")
    return target


_cache: Optional[Dict[str, object]] = None


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    """What is stored, whether or not it is still current."""
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not DATA_PATH.exists():
        return None
    loaded = _thaw(json.loads(DATA_PATH.read_text(encoding="utf-8")))
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


def rounded(value: object, places: int = 3) -> str:
    """An exact rational rendered at a stated precision, by integers."""
    return wbl.round_str(Fraction(value), places)
