"""``glm_universal.reasoning.deep_hole_failures`` -- the four failures, exactly,
and the spread that keeps the certificate out of reach.

The question
------------
The escalation round
(:mod:`glm_universal.reasoning.deep_hole_escalation`,
``studies/DEEP_HOLE_ESCALATION_STUDY.md``) reached its gate at the joint
reading with 1920 starts: every reference hole recognises itself, and **40 of
44** queries are named correctly.  Two things were left on the record there:

* the **four** queries that are not named correctly, which were counted and
  never examined; and
* the ratio ``rho = 2W/B``, which improves along the ladder from 3.90 to
  **2.59** and stops there, so the classifier that names 40 of 44 still cannot
  *certify* a single absence.

Both are governed by the worst-case within-type spread ``W``, which is why this
round takes them as one item rather than two.  It is **descriptive first**: for
each of the four it reports the exact distance to *every* reference and the
rank of the correct answer, because "second by a hair" and "absent from the
shortlist" are opposite diagnoses and the ranks tell them apart.

What is *not* done here
-----------------------
No new rung, no new reading, no new ensemble size.  Every number below is taken
at exactly one cell -- ``(joint, 1920)``, the cell the escalation round landed
on, named in the pre-registration before this module was written.  A round that
went looking for a cell where the four failures disappear would be the
unbounded search the escalation round was disciplined against; this one is
allowed no search at all on that axis.  The only enumeration it performs is
declared and reported in full: the 10 leave-one-out and 45 leave-two-out
reference subsets of §8, every one of which is printed whatever it says.

Exactness
---------
Integers and :class:`~fractions.Fraction` throughout.  No float, no RNG, and
no digest except the cache guard.
"""

from __future__ import annotations

import json
from fractions import Fraction
from functools import lru_cache
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .. import integrity
from . import deep_hole_classifier as dhc
from . import deep_hole_escalation as de
from . import wobble as wbl

__all__ = [
    "CELL_LAYER", "CELL_STARTS", "HALF", "EXPECTED_CORRECT", "EXPECTED_QUERIES",
    "SHORTLIST_DEPTH", "CLOSE_PAIR_RANK", "SUBSETS_TRIED",
    "plan", "record_for", "reference_table", "query_rows", "failures",
    "diagnoses", "spread", "leave_out", "reproduction",
    "per_type_criterion", "half_control", "faithfulness",
    "deep_hole_failure_report",
    "module_digest", "measure", "write_measurements", "measurements",
    "state", "current", "DATA_PATH", "rounded",
]


# ═════════════════════════════════════════════════════════════════════════
# 1.  THE PRE-REGISTERED CONSTANTS
# ═════════════════════════════════════════════════════════════════════════

#: The one cell this round reads at: the escalation round's passing cell.
CELL_LAYER: str = "joint"
CELL_STARTS: int = 1920

#: The declared split of the ensemble for the bimodality diagnosis: the first
#: 960 starts against the second 960.  The first half is exactly the 960-start
#: rung of the ladder, so the split is a rung boundary and not a new object.
HALF: int = CELL_STARTS // 2

#: What the escalation round reported at this cell.  A stopping rule: if this
#: round does not reproduce it, nothing else here is read.
EXPECTED_CORRECT: int = 40
EXPECTED_QUERIES: int = 44

#: "Absent from the shortlist" means the correct answer is not in the first
#: three ranks.  Fixed here, before the ranks are known.
SHORTLIST_DEPTH: int = 3

#: "The references were the closest pair" means the (truth, winner) pair is
#: among the five closest of the 45 reference pairs.  Fixed here too.
CLOSE_PAIR_RANK: int = 5

#: The declared enumeration of §8, reported in full: every one-type and every
#: two-type deletion of the reference set.
SUBSETS_TRIED: int = 10 + 45


# ═════════════════════════════════════════════════════════════════════════
# 2.  THE PLAN -- the escalation round's references and queries, unchanged
# ═════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=None)
def plan() -> Dict[str, object]:
    """The references and the query set, as centres and seeds.

    Exactly :func:`deep_hole_escalation.query_set`'s construction, re-derived
    here so that the ensembles can be enumerated before any of them is run.
    Nothing about the geometry, the transforms or the certification is
    changed: this is a plan of the same measurement, not a new one.
    """
    entries, siblings = de.reference_entries()
    references = tuple((str(entry["type"]),
                        tuple(Fraction(x) for x in entry["center"]))
                       for entry in entries)
    queries: List[Dict[str, object]] = []
    for index, entry in enumerate(entries):
        for transform in dhc.transforms():
            kind = str(transform["kind"])
            centre = tuple(Fraction(x)
                           for x in dhc._apply(kind, entry["center"]))
            moved = tuple(sorted(dhc._apply_point(kind, vertex)
                                 for vertex in entry["vertices"]))
            check = dhc._certify_at(centre, moved)
            name = f"hole {index} · {transform['key']}"
            if not check["certified"] or check["type"] != entry["type"]:
                queries.append({
                    "name": name, "truth": str(entry["type"]), "used": False,
                    "kind": str(transform["key"]),
                    "reason": (f"the transform did not re-certify as "
                               f"{entry['type']}, so it is dropped"),
                })
                continue
            queries.append({
                "name": name, "truth": str(entry["type"]), "used": True,
                "kind": str(transform["key"]),
                "seed": int(transform["seed"]), "centre": centre,
                "reason": "",
            })
    for sibling in siblings:
        queries.append({
            "name": f"{sibling['name']} · sibling centre",
            "truth": str(sibling["type"]), "used": True, "kind": "sibling",
            "seed": dhc.QUERY_SEEDS["sibling"],
            "centre": tuple(Fraction(x) for x in sibling["center"]),
            "reason": "",
        })
    return {"references": references, "queries": tuple(queries)}


def ensemble_keys() -> Tuple[Tuple[Tuple[Fraction, ...], int], ...]:
    """Every ``(centre, seed)`` this round needs, without duplicates."""
    layout = plan()
    keys: List[Tuple[Tuple[Fraction, ...], int]] = []
    seen = set()

    def add(centre: Tuple[Fraction, ...], seed: int) -> None:
        key = (centre, seed)
        if key not in seen:
            seen.add(key)
            keys.append(key)

    for _label, centre in layout["references"]:      # type: ignore[misc]
        add(centre, de.REFERENCE_SEED)
        add(centre, de.SANITY_SEED)
    for query in layout["queries"]:                  # type: ignore[union-attr]
        if query.get("used"):
            add(query["centre"], int(query["seed"]))  # type: ignore[arg-type]
    return tuple(keys)


#: Records filled by the writer, so that the ensembles can be run in parallel.
#: A hit here and a call to :func:`deep_hole_escalation.emissions` compute the
#: same thing -- the ensemble is deterministic -- so the cache changes only how
#: long the measurement takes.
_RECORDS: Dict[Tuple[Tuple[Fraction, ...], int],
               Tuple[Tuple[Tuple[int, ...], Fraction], ...]] = {}


def record_for(centre: Tuple[Fraction, ...], seed: int
               ) -> Tuple[Tuple[Tuple[int, ...], Fraction], ...]:
    """The declared ensemble at a centre and seed, to the top rung."""
    key = (tuple(centre), int(seed))
    hit = _RECORDS.get(key)
    if hit is not None:
        return hit
    return de.emissions(key[0], key[1], CELL_STARTS)


def emit(item: Tuple[Tuple[Fraction, ...], int, int]
         ) -> Tuple[Tuple[Tuple[int, ...], Fraction], ...]:
    """One ensemble, as a worker sees it.  Top level, so it is picklable.

    The ensemble size travels with the work item rather than being read from
    the module, so that a worker computes the same ensemble the caller asked
    for even when the caller is a test running a smaller cell.
    """
    centre, seed, starts = item
    return de.emissions(tuple(centre), int(seed), int(starts))


def fill(parallel: bool = True) -> int:
    """Run every ensemble this round needs, in parallel where possible."""
    keys = [key for key in ensemble_keys() if key not in _RECORDS]
    if not keys:
        return 0
    items = [(centre, seed, CELL_STARTS) for centre, seed in keys]
    if parallel:
        try:
            from concurrent.futures import ProcessPoolExecutor
            with ProcessPoolExecutor() as pool:
                for key, record in zip(keys, pool.map(emit, items)):
                    _RECORDS[key] = record
            return len(keys)
        except Exception:                      # pragma: no cover - fall back
            pass
    for key, item in zip(keys, items):
        _RECORDS[key] = emit(item)
    return len(keys)


# ═════════════════════════════════════════════════════════════════════════
# 3.  THE READING AT THE ONE DECLARED CELL
# ═════════════════════════════════════════════════════════════════════════

def _profile(record: Sequence[Tuple[Tuple[int, ...], Fraction]]) -> object:
    return de.layer_profile(record, CELL_LAYER)


def _distance(left: object, right: object) -> Fraction:
    return de.layer_distance(left, right, CELL_LAYER)


@lru_cache(maxsize=None)
def reference_table() -> Tuple[Tuple[str, object], ...]:
    """The reference profile of each type at the declared cell."""
    layout = plan()
    return tuple((label, _profile(record_for(centre, de.REFERENCE_SEED)))
                 for label, centre in layout["references"])  # type: ignore[misc]


@lru_cache(maxsize=None)
def half_tables() -> Tuple[Tuple[Tuple[str, object], ...],
                           Tuple[Tuple[str, object], ...]]:
    """The reference profiles read on each declared half of the ensemble."""
    layout = plan()
    first: List[Tuple[str, object]] = []
    second: List[Tuple[str, object]] = []
    for label, centre in layout["references"]:       # type: ignore[misc]
        record = record_for(centre, de.REFERENCE_SEED)
        first.append((label, _profile(record[:HALF])))
        second.append((label, _profile(record[HALF:])))
    return tuple(first), tuple(second)


def _ranked(profile: object, table: Sequence[Tuple[str, object]]
            ) -> Tuple[Tuple[str, Fraction], ...]:
    return tuple(sorted(((label, _distance(profile, reference))
                         for label, reference in table),
                        key=lambda row: (row[1], row[0])))


@lru_cache(maxsize=None)
def query_rows() -> Tuple[Dict[str, object], ...]:
    """Every used query, with its exact distance to *every* reference.

    This is the descriptive object the round exists to produce: the escalation
    round kept only the winner and the rank, and the four diagnoses of the
    pre-registration are distinguishable only from the whole row.
    """
    layout = plan()
    table = reference_table()
    first_table, second_table = half_tables()
    rows: List[Dict[str, object]] = []
    for query in layout["queries"]:                  # type: ignore[union-attr]
        if not query.get("used"):
            continue
        centre = query["centre"]
        seed = int(query["seed"])                    # type: ignore[arg-type]
        record = record_for(centre, seed)            # type: ignore[arg-type]
        ranked = _ranked(_profile(record), table)
        best_distance = ranked[0][1]
        winners = [label for label, distance in ranked
                   if distance == best_distance]
        truth = str(query["truth"])
        own = next(distance for label, distance in ranked if label == truth)
        order = [label for label, _distance in ranked]
        first_named = _ranked(_profile(record[:HALF]), first_table)[0][0]
        second_named = _ranked(_profile(record[HALF:]), second_table)[0][0]
        rows.append({
            "query": str(query["name"]),
            "kind": str(query["kind"]),
            "truth": truth,
            "verdict": "named" if len(winners) == 1 else "ambiguous",
            "label": winners[0] if len(winners) == 1 else None,
            "correct": len(winners) == 1 and winners[0] == truth,
            "own_distance": own,
            "best_distance": best_distance,
            "margin": own - best_distance,
            "own_rank": order.index(truth) + 1,
            "ranked": ranked,
            "first_half_named": first_named,
            "second_half_named": second_named,
            "halves_agree": first_named == second_named,
            "half_gap": _distance(_profile(record[:HALF]),
                                  _profile(record[HALF:])),
        })
    return tuple(rows)


def failures() -> Tuple[Dict[str, object], ...]:
    """The queries the escalated reading does not name correctly."""
    return tuple(row for row in query_rows() if not row["correct"])


# ═════════════════════════════════════════════════════════════════════════
# 4.  THE REFERENCE PAIRS
# ═════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=None)
def reference_pairs() -> Tuple[Dict[str, object], ...]:
    """Every pair of references with its exact distance, closest first."""
    table = reference_table()
    rows: List[Dict[str, object]] = []
    for (left, left_profile), (right, right_profile) in combinations(table, 2):
        rows.append({"left": left, "right": right,
                     "distance": _distance(left_profile, right_profile)})
    rows.sort(key=lambda row: (row["distance"], row["left"], row["right"]))
    for index, row in enumerate(rows):
        row["rank"] = index + 1
    return tuple(rows)


def pair_rank(left: str, right: str) -> Optional[Dict[str, object]]:
    """Where a pair of type names sits in the closest-pair ordering."""
    for row in reference_pairs():
        if {row["left"], row["right"]} == {left, right}:
            return row
    return None


# ═════════════════════════════════════════════════════════════════════════
# 5.  THE FOUR DIAGNOSES, EACH WITH ITS RULE FIXED IN THE PRE-REGISTRATION
# ═════════════════════════════════════════════════════════════════════════

def diagnoses() -> Tuple[Dict[str, object], ...]:
    """For each failure, which of the four pre-registered readings holds.

    The four are *not* exclusive by construction, and the round does not force
    them to be: a row may satisfy none of them, in which case the round says
    so, which is the outcome that would refute all four at once.
    """
    pairs = reference_pairs()
    separation = pairs[0]["distance"] if pairs else Fraction(0)
    out: List[Dict[str, object]] = []
    for row in failures():
        truth = str(row["truth"])
        winner = row["label"]
        pair = (pair_rank(truth, str(winner)) if winner is not None else None)
        close = (pair is not None
                 and int(pair["rank"]) <= CLOSE_PAIR_RANK)
        tie = (row["verdict"] == "ambiguous"
               or row["margin"] == 0)
        bimodal = not row["halves_agree"]
        absent = int(row["own_rank"]) > SHORTLIST_DEPTH
        near_miss = (int(row["own_rank"]) == 2
                     and separation > 0
                     and Fraction(row["margin"]) < separation / 10)
        out.append({
            "query": row["query"],
            "truth": truth,
            "named": winner,
            "own_rank": row["own_rank"],
            "margin": row["margin"],
            "margin_over_separation": (None if separation == 0
                                       else Fraction(row["margin"]) / separation),
            "pair_rank": (None if pair is None else pair["rank"]),
            "pair_distance": (None if pair is None else pair["distance"]),
            "a_closest_pair": close,
            "b_bimodal": bimodal,
            "c_tie": tie,
            "d_absent_from_shortlist": absent,
            "near_miss": near_miss,
            "first_half_named": row["first_half_named"],
            "second_half_named": row["second_half_named"],
            "half_gap": row["half_gap"],
            "none_of_the_four": not (close or bimodal or tie or absent),
        })
    return tuple(out)


# ═════════════════════════════════════════════════════════════════════════
# 6.  THE SPREAD, TYPE BY TYPE
# ═════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=None)
def spread() -> Dict[str, object]:
    """``W`` and ``B`` opened up: which type, and which pair, set the ratio.

    ``W_seed`` is the escalation round's spread -- the sanity ensemble only --
    and reproducing its ratio is the stopping rule of §3 of the study.
    ``W_all`` is the spread over every perturbation the query set contains,
    which is the quantity the *classifier* actually has to survive.
    """
    layout = plan()
    table = dict(reference_table())
    rows: List[Dict[str, object]] = []
    for label, centre in layout["references"]:       # type: ignore[misc]
        reference = table[label]
        sanity = _distance(_profile(record_for(centre, de.SANITY_SEED)),
                           reference)
        widest = sanity
        widest_by = "the sanity seed"
        for row in query_rows():
            if str(row["truth"]) != label:
                continue
            if Fraction(row["own_distance"]) > widest:
                widest = Fraction(row["own_distance"])
                widest_by = str(row["query"])
        gap = min((_distance(reference, other)
                   for name, other in table.items() if name != label),
                  default=Fraction(0))
        nearest = min(((name, _distance(reference, other))
                       for name, other in table.items() if name != label),
                      key=lambda item: (item[1], item[0]), default=(None, None))
        rows.append({
            "type": label,
            "seed_spread": sanity,
            "spread": widest,
            "widest_by": widest_by,
            "gap": gap,
            "nearest_reference": nearest[0],
            "ratio_seed": (None if gap == 0 else Fraction(2) * sanity / gap),
            "ratio": (None if gap == 0 else Fraction(2) * widest / gap),
        })
    rows.sort(key=lambda row: (-row["spread"], row["type"]))
    pairs = reference_pairs()
    separation = pairs[0]["distance"] if pairs else Fraction(0)
    worst_seed = max((row["seed_spread"] for row in rows), default=Fraction(0))
    worst_all = max((row["spread"] for row in rows), default=Fraction(0))
    return {
        "rows": tuple(rows),
        "separation": separation,
        "closest_pair": (None if not pairs
                         else (pairs[0]["left"], pairs[0]["right"])),
        "worst_seed_spread": worst_seed,
        "worst_spread": worst_all,
        "worst_seed_type": next((row["type"] for row in rows
                                 if row["seed_spread"] == worst_seed), None),
        "worst_type": next((row["type"] for row in rows
                            if row["spread"] == worst_all), None),
        "rho_seed": (None if separation == 0
                     else Fraction(2) * worst_seed / separation),
        "rho_all": (None if separation == 0
                    else Fraction(2) * worst_all / separation),
    }


# ═════════════════════════════════════════════════════════════════════════
# 7.  THE DECLARED DELETION SWEEP
# ═════════════════════════════════════════════════════════════════════════

def _ratio_over(labels: Sequence[str]) -> Dict[str, object]:
    """``rho`` computed over a sub-collection of the reference types."""
    kept = set(labels)
    table = [(label, profile) for label, profile in reference_table()
             if label in kept]
    if len(table) < 2:
        return {"kept": tuple(sorted(kept)), "separation": None,
                "spread": None, "ratio": None, "below_one": False}
    separation = min(_distance(left, right)
                     for (_l, left), (_r, right) in combinations(table, 2))
    by_type = {row["type"]: row for row in spread()["rows"]}  # type: ignore[index]
    widest = max(Fraction(by_type[label]["spread"]) for label in kept
                 if label in by_type)
    ratio = None if separation == 0 else Fraction(2) * widest / separation
    return {"kept": tuple(sorted(kept)), "separation": separation,
            "spread": widest, "ratio": ratio,
            "below_one": ratio is not None and ratio < 1}


@lru_cache(maxsize=None)
def leave_out() -> Dict[str, object]:
    """Every one-type and two-type deletion, reported whatever it says.

    A deletion that takes ``rho`` below 1 certifies **only over the reference
    set that remains**, and the study says so wherever this table is read: a
    classifier that cannot be asked about a type it has deleted has not earned
    a certificate about that type.
    """
    labels = [label for label, _profile in reference_table()]
    ones: List[Dict[str, object]] = []
    for dropped in labels:
        row = _ratio_over([label for label in labels if label != dropped])
        row = dict(row)
        row["dropped"] = (dropped,)
        ones.append(row)
    ones.sort(key=lambda row: (row["ratio"] is None,
                               row["ratio"] if row["ratio"] is not None else 0))
    twos: List[Dict[str, object]] = []
    for first, second in combinations(labels, 2):
        row = dict(_ratio_over([label for label in labels
                                if label not in {first, second}]))
        row["dropped"] = (first, second)
        twos.append(row)
    twos.sort(key=lambda row: (row["ratio"] is None,
                               row["ratio"] if row["ratio"] is not None else 0))
    best_one = ones[0] if ones else None
    best_two = twos[0] if twos else None
    return {
        "full": _ratio_over(labels),
        "one": tuple(ones),
        "two": tuple(twos),
        "best_one": best_one,
        "best_two": best_two,
        "any_below_one": any(row["below_one"] for row in ones + twos),
        "subsets_tried": len(ones) + len(twos),
    }


# ═════════════════════════════════════════════════════════════════════════
# 8.  THE STOPPING RULE
# ═════════════════════════════════════════════════════════════════════════

def reproduction() -> Dict[str, object]:
    """This round must reproduce the escalation round before it is read."""
    rows = query_rows()
    correct = sum(1 for row in rows if row["correct"])
    return {
        "queries": len(rows),
        "correct": correct,
        "failures": len(rows) - correct,
        "expected_queries": EXPECTED_QUERIES,
        "expected_correct": EXPECTED_CORRECT,
        "reproduces": (len(rows) == EXPECTED_QUERIES
                       and correct == EXPECTED_CORRECT),
    }


# ═════════════════════════════════════════════════════════════════════════
# 9.  FAITHFULNESS -- the certificate the round is really about
# ═════════════════════════════════════════════════════════════════════════

def per_type_criterion() -> Dict[str, object]:
    """The types whose own criterion ``2W_T < B_T`` holds, and what it earns.

    The global ratio is a worst case over all ten types, so it says nothing
    about a type that is well separated from its own neighbours.  Where
    ``rho_T < 1`` the per-type criterion holds, and
    ``GLM.DeepHoleFailure.per_type_correct`` turns it into a
    certificate: every query of that type lying within ``W_T`` of ``f_T`` is
    named correctly, whatever the other types do.
    """
    rows = spread()["rows"]
    certified = tuple(str(row["type"]) for row in rows      # type: ignore[union-attr]
                      if row["ratio"] is not None
                      and Fraction(row["ratio"]) < 1)
    return {
        "certified": certified,
        "count": len(certified),
        "total": len(tuple(rows)),                          # type: ignore[arg-type]
        "reading": ("For these types the criterion holds at the type level, "
                    "so naming them is certified rather than heuristic; for "
                    "the rest it does not, and naming them remains a "
                    "faculty without a certificate."),
    }


def half_control() -> Dict[str, object]:
    """The bimodality rule, applied to the queries that were named correctly.

    A control, and one added after the four diagnoses had been read: rule B
    fires when the two halves of an ensemble name different types, and that
    would fire for *any* query whose margin is smaller than the noise at half
    the budget.  Applying the same rule to the correct queries is what says
    whether it discriminates.  It is reported as a control and is not part of
    the pre-registered four.
    """
    rows = query_rows()
    correct = [row for row in rows if row["correct"]]
    wrong = [row for row in rows if not row["correct"]]
    disagreeing = sum(1 for row in correct if not row["halves_agree"])
    return {
        "correct": len(correct),
        "correct_halves_disagree": disagreeing,
        "failures": len(wrong),
        "failures_halves_disagree": sum(1 for row in wrong
                                        if not row["halves_agree"]),
    }


def faithfulness() -> Dict[str, object]:
    """The radius a query needs against the radius separation allows.

    ``r*`` is ``B/2``: inside it a nearest-reference answer is certified, and
    an absence is a proof.  ``faithfulness`` is the largest distance any query
    of a type sits from its own reference.  While ``faithfulness >= r*`` the
    two are incompatible and ``GLM.DeepHole.absent_certifies`` cannot be
    instantiated, which is exactly the state the escalation round left.
    """
    measured = spread()
    separation = Fraction(measured["separation"])   # type: ignore[arg-type]
    radius = separation / 2
    needed = max((Fraction(row["own_distance"]) for row in query_rows()),
                 default=Fraction(0))
    return {"faithfulness": needed, "certified_radius": radius,
            "compatible": needed < radius,
            "shortfall": needed - radius}


# ═════════════════════════════════════════════════════════════════════════
# 10.  THE REPORT
# ═════════════════════════════════════════════════════════════════════════

def deep_hole_failure_report() -> Dict[str, object]:
    """Everything this round knows, recomputed on call."""
    check = reproduction()
    measured = spread()
    sweep = leave_out()
    rows = diagnoses()
    counts = {
        "a_closest_pair": sum(1 for row in rows if row["a_closest_pair"]),
        "b_bimodal": sum(1 for row in rows if row["b_bimodal"]),
        "c_tie": sum(1 for row in rows if row["c_tie"]),
        "d_absent_from_shortlist": sum(
            1 for row in rows if row["d_absent_from_shortlist"]),
        "near_miss": sum(1 for row in rows if row["near_miss"]),
        "none_of_the_four": sum(1 for row in rows if row["none_of_the_four"]),
    }
    worst = str(measured["worst_type"])
    failing_types = sorted({str(row["truth"]) for row in rows})
    return {
        "cell": {"layer": CELL_LAYER, "starts": CELL_STARTS,
                 "layer_name": de.LAYER_NAMES[CELL_LAYER]},
        "reproduction": check,
        "queries": query_rows(),
        "failures": rows,
        "counts": counts,
        "spread": measured,
        "per_type": per_type_criterion(),
        "half_control": half_control(),
        "faithfulness": faithfulness(),
        "leave_out": sweep,
        "pairs": reference_pairs(),
        "same_mechanism": worst in failing_types,
        "worst_spread_type": worst,
        "failing_types": tuple(failing_types),
        "subsets_tried": SUBSETS_TRIED,
        "original_negative": {
            "rho_at_the_passing_cell": measured["rho_seed"],
            "criterion": "rho < 1",
            "stands": (measured["rho_seed"] is None
                       or Fraction(measured["rho_seed"]) >= 1),
            "reading": (
                "The escalation round's negative is kept on the record beside "
                "whatever this round returns: at the passing cell the ratio is "
                "2.59 against a criterion of 1, no absence is certified, and "
                "nothing below repairs that."),
        },
        "method": (
            "One cell, declared in advance and not searched over: the joint "
            "reading at 1920 starts, which is the cell the escalation round "
            "landed on.  Every used query is re-read there and its exact "
            "distance to all ten references is kept, so that the four "
            "failures can be diagnosed by rank and margin rather than by "
            "hypothesis.  The spread is then opened up type by type, and the "
            "declared deletion sweep asks whether one type's spread is what "
            "holds the ratio above 1."),
        "limits": (
            "A deletion that takes the ratio below 1 certifies only over the "
            "types that remain.  The four diagnoses are readings of the same "
            "44 queries and are not independent tests.  Nothing here is a new "
            "rung: no cell other than (joint, 1920) is measured, and no claim "
            "is made about one."),
    }


# ═════════════════════════════════════════════════════════════════════════
# 11.  THE CACHE, GUARDED BY A DIGEST
# ═════════════════════════════════════════════════════════════════════════

DATA_PATH = (Path(__file__).resolve().parent / "_data"
             / "deep_hole_failures.json")

_SOURCES: Tuple[str, ...] = (
    "reasoning/deep_hole_failures.py",
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


def measure(parallel: bool = True) -> Dict[str, object]:
    """The report, with the digest of what it was taken from beside it."""
    fill(parallel=parallel)
    payload = dict(deep_hole_failure_report())
    payload["source_digest"] = module_digest()
    return payload


def write_measurements(path: Optional[Path] = None,
                       parallel: bool = True) -> Path:
    """Take the measurements and store them beside their digest."""
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(de._freeze(measure(parallel=parallel)), indent=1,
                   sort_keys=True, ensure_ascii=False) + "\n",
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
    loaded = de._thaw(json.loads(DATA_PATH.read_text(encoding="utf-8")))
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


def rounded(value: object, places: int = 4) -> str:
    """An exact rational rendered at a stated precision, by integers."""
    return wbl.round_str(Fraction(value), places)


if __name__ == "__main__":                      # pragma: no cover
    print(f"wrote {write_measurements()}")
    print(f"digest {module_digest()}")
