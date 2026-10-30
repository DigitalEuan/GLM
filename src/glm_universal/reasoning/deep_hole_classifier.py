"""``glm_universal.reasoning.deep_hole_classifier`` -- a hole named by its
arrival distribution, against the baseline that already names some of them.

The question
------------
:mod:`glm_universal.reasoning.deep_holes` *reads* a deep hole of the Leech
lattice: it collects the hole's vertices, measures the pairwise distances,
matches the components against the extended Dynkin shapes and certifies the
reading with the marked-barycentre identity.  That is the classification
theorem applied to a geometric object, and it is exact.

This module asks a different question, pre-registered in
``studies/DEEP_HOLE_STUDY.md`` before the module existed: is the
**distribution of trajectories that arrive at a hole** enough to name it?
The classifier here never looks at a distance between two vertices.  It sees
only how often each vertex was arrived at, over a declared deterministic
ensemble of modulator starts, and it names the hole by comparing that
profile with a reference table.

Why it is not obviously worth anything
--------------------------------------
A deep hole has ``24 + k`` vertices, ``k`` its number of components, so the
**plain vertex count** already names several of the 23 types by itself.  A
trajectory statistic that merely reproduces the vertex count has measured
nothing at all.  The cheap baseline is therefore the competitor that matters
and it was fixed in the study before any measurement: the method has to beat
the vertex count, not merely a hash.

What is measured
----------------
1. **The holes.**  Two built from the substrate's own codewords -- the
   octad-pair midpoint and the dodecad-triangle centroid -- then twelve
   walks at declared seeds.  Whatever distinct certified types that budget
   reaches is the attempted set; what it does not reach is reported as not
   reached.
2. **The ensemble.**  For a centre ``c`` and a declared seed, 240 starts,
   one tick each, quantised by the exact nearest-Leech-point decoder.  Every
   emission is recorded.  Emissions at the minimum distance are *vertex
   arrivals*; anything further is a *stray*, counted and excluded.
3. **The statistic.**  The arrival shares ``a(v)/A`` as exact rationals,
   sorted descending and zero-padded to 48 -- the largest vertex count there
   is.  Distance is the L1 metric on ``Q^48``.
4. **The queries.**  Each reference hole is transformed by a symmetry the
   walk is allowed -- a seed change, a lattice translation, negation, a
   Golay-automorphism coordinate permutation -- and re-certified at the new
   centre before it is used, so a transform that fails to preserve the type
   is dropped with a stated reason rather than quietly used.
5. **The controls.**  A digest control (D3), a seeded reshuffle, the
   vertex-count baseline, and a uniform-profile ablation that is the baseline
   expressed inside the method's own metric.

Everything is exact: integers and :class:`~fractions.Fraction`, no float
anywhere.  The one thing that is not enumerated is the ensemble of start
offsets -- there are ``2001**24`` of them -- and the study declares the exact
finite deterministic ensemble used instead, up front.
"""

from __future__ import annotations

import json
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .. import integrity
from ..substrate import isomorphism as iso, leech2
from . import deep_holes as dh
from . import niemeier
from . import wobble as wbl
from . import wobble_landscape as wls
from .fwht_decode import _Sweep, nearest_lattice_point_fwht

__all__ = [
    "STARTS", "STABILITY_STARTS", "DITHER", "OFFSET_SPAN", "PROFILE_LENGTH",
    "REFERENCE_SEED", "QUERY_SEEDS", "WALK_SEEDS", "OPERATING_RADIUS",
    "STATISTICS_TRIED", "GATE_BITS",
    "offsets", "arrival_counts", "share_profile", "uniform_profile",
    "l1", "linf", "digest_profile",
    "golay_permutation", "transforms",
    "reference_holes", "reference_table", "query_set",
    "classify", "certified_radius", "separation", "per_type",
    "tail_probability",
    "score_run", "gate_decision", "deep_hole_classifier_report",
    "module_digest", "measure", "write_measurements", "measurements",
    "state", "current", "DATA_PATH",
]


# ═════════════════════════════════════════════════════════════════════════
# 1.  THE PRE-REGISTERED CONSTANTS
# ═════════════════════════════════════════════════════════════════════════

#: Starts in one ensemble.  Not a sample size: the ensemble *is* these 240
#: declared starts, and a different seed is a different declared ensemble.
STARTS: int = 240

#: The declared stability re-measurement, which is the 120-start prefix of
#: the same sweep and therefore costs nothing extra.
STABILITY_STARTS: int = 120

#: Start offsets are ``(sweep.below(OFFSET_SPAN) - 1000) / DITHER``.
DITHER: int = 4000
OFFSET_SPAN: int = 2001

#: Profiles are padded to the largest vertex count a deep hole can have,
#: which is the 48 of the ``A_1^24`` hole.
PROFILE_LENGTH: int = 48

#: The reference ensemble's seed, and one seed per query family.
REFERENCE_SEED: int = 20260825
QUERY_SEEDS: Dict[str, int] = {
    "seed": 20260826,
    "translation": 20260827,
    "negation": 20260828,
    "permutation": 20260829,
    "sibling": 20260830,
}

#: The declared walk budget, in the declared order.
WALK_SEEDS: Tuple[int, ...] = tuple(20260825 + 977 * i for i in range(12))

#: The operating radius of the classifier, fixed before the measurement.
OPERATING_RADIUS: Fraction = Fraction(1, 2)

#: The multiplicity correction: how many statistics this study tried.
STATISTICS_TRIED: int = 4

#: The gate, in bits.
GATE_BITS: int = 3

#: Probing parameters handed to the frozen path when it certifies a hole.
WALK_PROBES: int = 200
WALK_PATIENCE: int = 40


# ═════════════════════════════════════════════════════════════════════════
# 2.  THE ENSEMBLE
# ═════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=None)
def offsets(seed: int, starts: int = STARTS) -> Tuple[Tuple[Fraction, ...], ...]:
    """The declared start offsets: start 0 is the zero accumulator.

    Exactly the offsets :func:`deep_holes.probe_hole` uses, so the ensemble
    here is the frozen path's ensemble with the arrival counts kept.
    """
    sweep = _Sweep(seed)
    out: List[Tuple[Fraction, ...]] = []
    for index in range(starts):
        if index == 0:
            out.append(tuple([Fraction(0)] * 24))
        else:
            out.append(tuple(Fraction(sweep.below(OFFSET_SPAN) - 1000, DITHER)
                             for _ in range(24)))
    return tuple(out)


def _raw_distance2(a: Sequence, b: Sequence) -> Fraction:
    return sum((Fraction(a[i]) - Fraction(b[i])) ** 2 for i in range(24))


@lru_cache(maxsize=None)
def arrival_counts(center: Tuple[Fraction, ...], seed: int,
                   starts: int = STARTS) -> Dict[str, object]:
    """Run the declared ensemble at ``center`` and keep the arrival tally.

    One tick per start, no patience rule and no early stop, so every start
    contributes exactly one emission and the counts are commensurable across
    holes and across ensembles.
    """
    point = [Fraction(x) for x in center]
    emissions: List[Tuple[Tuple[int, ...], Fraction]] = []
    best: Optional[Fraction] = None
    for offset in offsets(seed, starts):
        driven = [offset[i] + point[i] for i in range(24)]
        emitted = nearest_lattice_point_fwht(driven).point
        distance = _raw_distance2(point, emitted)
        emissions.append((emitted, distance))
        best = distance if best is None else min(best, distance)
    counts: Dict[Tuple[int, ...], int] = {}
    strays: Dict[Fraction, int] = {}
    for emitted, distance in emissions:
        if distance == best:
            counts[emitted] = counts.get(emitted, 0) + 1
        else:
            strays[distance] = strays.get(distance, 0) + 1
    arrivals = sum(counts.values())
    return {
        "seed": seed,
        "starts": starts,
        "min_distance2_raw": best,
        "counts": dict(sorted(counts.items())),
        "support": tuple(sorted(counts)),
        "vertex_count": len(counts),
        "arrivals": arrivals,
        "strays": sum(strays.values()),
        "stray_spectrum": dict(sorted(strays.items())),
    }


def share_profile(counts: Dict[Tuple[int, ...], int]
                  ) -> Tuple[Fraction, ...]:
    """The arrival shares, sorted descending and padded to 48."""
    total = sum(counts.values())
    if total <= 0:
        return tuple([Fraction(0)] * PROFILE_LENGTH)
    shares = sorted((Fraction(value, total) for value in counts.values()),
                    reverse=True)
    shares = shares[:PROFILE_LENGTH]
    return tuple(shares + [Fraction(0)] * (PROFILE_LENGTH - len(shares)))


def uniform_profile(support: int) -> Tuple[Fraction, ...]:
    """The ablation: the same support size, every share equal."""
    if support <= 0:
        return tuple([Fraction(0)] * PROFILE_LENGTH)
    support = min(support, PROFILE_LENGTH)
    return tuple([Fraction(1, support)] * support
                 + [Fraction(0)] * (PROFILE_LENGTH - support))


def digest_profile(name: str) -> Tuple[Fraction, ...]:
    """A profile derived from a name by digest: geometry-free, by design.

    D3 says a digest addresses integrity and never meaning, so a classifier
    that uses this must score at chance.  That is the point of it, and the
    bytes come from :func:`glm_universal.integrity.byte_vector` so that the
    hashing stays in the one module the project allows it in.
    """
    values = [value + 1 for value
              in integrity.byte_vector(name, PROFILE_LENGTH, 256)]
    total = sum(values)
    return tuple(sorted((Fraction(v, total) for v in values), reverse=True))


def l1(a: Sequence[Fraction], b: Sequence[Fraction]) -> Fraction:
    """The L1 distance between two profiles, exactly."""
    return sum(abs(Fraction(a[i]) - Fraction(b[i]))
               for i in range(PROFILE_LENGTH))


def linf(a: Sequence[Fraction], b: Sequence[Fraction]) -> Fraction:
    """The L-infinity distance between two profiles, exactly."""
    return max(abs(Fraction(a[i]) - Fraction(b[i]))
               for i in range(PROFILE_LENGTH))


# ═════════════════════════════════════════════════════════════════════════
# 3.  THE TRANSFORMS -- the symmetries the walk is allowed
# ═════════════════════════════════════════════════════════════════════════

def _permutation_family() -> List[Tuple[str, Tuple[int, ...]]]:
    """The declared finite family Q3 searches, in the declared order."""
    family: List[Tuple[str, Tuple[int, ...]]] = []
    for k in range(24):
        family.append((f"cyclic rotation by {k}",
                       tuple((i + k) % 24 for i in range(24))))
    residues = sorted({(x * x) % 23 for x in range(1, 23)})
    for a in residues:
        for b in range(23):
            perm = [0] * 24
            perm[23] = 23
            for i in range(23):
                perm[i] = (a * i + b) % 23
            family.append((f"x -> {a}x + {b} mod 23", tuple(perm)))
    return family


@lru_cache(maxsize=None)
def golay_permutation() -> Dict[str, object]:
    """The first non-identity member of the family that is an automorphism.

    Reported with its verdict rather than assumed: if the family holds none,
    or the one it holds fails to carry lattice points to lattice points, Q3
    is dropped and the report says so.
    """
    identity = tuple(range(24))
    checked = 0
    for name, perm in _permutation_family():
        checked += 1
        if perm == identity:
            continue
        if not iso.is_golay_automorphism(perm)["is_automorphism"]:
            continue
        sample = [list(v) for v in dh._trio_vectors()]
        sample += [list(v) for v in dh._dodecad_vectors(limit=8)]
        preserved = all(leech2.in_leech(list(iso.permute_vector(v, perm)))
                        for v in sample)
        return {
            "found": bool(preserved),
            "name": name,
            "permutation": perm,
            "members_checked": checked,
            "lattice_sample": len(sample),
            "lattice_preserved": preserved,
            "reason": ("the first non-identity automorphism of the declared "
                       "family, checked to carry the sampled lattice points "
                       "back into the lattice"
                       if preserved else
                       "an automorphism of the code that moved a lattice "
                       "point out of the lattice, so Q3 is dropped"),
        }
    return {"found": False, "name": None, "permutation": None,
            "members_checked": checked, "lattice_sample": 0,
            "lattice_preserved": False,
            "reason": "no non-identity member of the declared family is an "
                      "automorphism of the code, so Q3 is dropped"}


@lru_cache(maxsize=None)
def _translation() -> Tuple[int, ...]:
    """Q1's lattice vector: the first vector of the MOG trio."""
    return dh._trio_vectors()[0]


def transforms() -> Tuple[Dict[str, object], ...]:
    """The declared query transforms, in order, each with its seed."""
    out: List[Dict[str, object]] = [
        {"key": "seed", "name": "the same centre, a different ensemble seed",
         "seed": QUERY_SEEDS["seed"], "kind": "identity"},
        {"key": "translation", "name": "translation by a lattice vector",
         "seed": QUERY_SEEDS["translation"], "kind": "translation"},
        {"key": "negation", "name": "negation about the origin",
         "seed": QUERY_SEEDS["negation"], "kind": "negation"},
    ]
    permutation = golay_permutation()
    if permutation["found"]:
        out.append({"key": "permutation",
                    "name": f"the coordinate permutation "
                            f"'{permutation['name']}'",
                    "seed": QUERY_SEEDS["permutation"], "kind": "permutation"})
    return tuple(out)


def _apply(kind: str, vector: Sequence) -> Tuple:
    if kind == "identity":
        return tuple(vector)
    if kind == "translation":
        shift = _translation()
        return tuple(Fraction(vector[i]) + shift[i] for i in range(24))
    if kind == "negation":
        return tuple(-Fraction(vector[i]) for i in range(24))
    if kind == "permutation":
        perm = golay_permutation()["permutation"]
        return tuple(iso.permute_vector(list(vector), perm))
    raise ValueError(f"_apply: unknown transform {kind!r}")


def _apply_point(kind: str, point: Sequence[int]) -> Tuple[int, ...]:
    moved = _apply(kind, point)
    return tuple(int(x) for x in moved)


# ═════════════════════════════════════════════════════════════════════════
# 4.  THE HOLES, IN THE DECLARED ORDER
# ═════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=None)
def reference_holes(walks: int = len(WALK_SEEDS)) -> Tuple[Dict[str, object], ...]:
    """Every hole the declared budget reaches, certified by the frozen path.

    The two constructions first, then the walks in index order.  Nothing is
    looked up: each centre is produced by a construction out of the
    substrate's own codewords or by a walk, and each type is the certified
    reading of :func:`deep_holes.hole_diagram`.
    """
    found: List[Dict[str, object]] = []

    def record(name: str, construction: str, center: Sequence,
               classification: Dict[str, object]) -> None:
        found.append({
            "name": name,
            "construction": construction,
            "center": tuple(Fraction(x) for x in center),
            "type": classification.get("niemeier_type"),
            "certified": bool(classification.get("certified")),
            "vertices": tuple(classification["probe"]["vertices"]),
            "vertex_count": classification["probe"]["vertex_count"],
            "verdict": classification["verdict"],
        })

    pair = dh.octad_pair_hole()
    record("octad-pair midpoint", pair["construction"], pair["center"],
           dh.classify_carrier(pair["center"], probes=400,
                               seed=REFERENCE_SEED, patience=60))
    triangle = dh.dodecad_triangle_hole()
    record("dodecad-triangle centroid", triangle["construction"],
           triangle["center"],
           dh.classify_carrier(triangle["center"], probes=400,
                               seed=REFERENCE_SEED, patience=60))

    for index, seed in enumerate(WALK_SEEDS[:max(0, walks)]):
        run = dh.walked_hole(seed=seed, probes=WALK_PROBES,
                             patience=WALK_PATIENCE)
        if not run.get("reached_deep_hole") or not run.get("certified"):
            found.append({
                "name": f"walk {index}",
                "construction": "walk + climb",
                "center": None,
                "type": None,
                "certified": False,
                "vertices": (),
                "vertex_count": 0,
                "verdict": run.get("verdict", "the walk reached no hole"),
            })
            continue
        record(f"walk {index}", "walk + climb", run["center"],
               run["classification"])
    return tuple(found)


@lru_cache(maxsize=None)
def _certify_at(center: Tuple[Fraction, ...],
                vertices: Tuple[Tuple[int, ...], ...]) -> Dict[str, object]:
    """The frozen reader, applied to a transported vertex set."""
    diagram = dh.hole_diagram(vertices, center=center)
    return {
        "type": diagram["root_system"],
        "certified": bool(diagram["certified_complete"]),
        "in_catalogue": bool(diagram["in_niemeier_catalogue"]),
        "vertex_count": diagram["vertex_count"],
    }


# ═════════════════════════════════════════════════════════════════════════
# 5.  THE REFERENCE TABLE AND THE QUERY SET
# ═════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=None)
def reference_table(walks: int = len(WALK_SEEDS), starts: int = STARTS
                    ) -> Dict[str, object]:
    """The first certified centre of each type, with its reference profile."""
    holes = reference_holes(walks)
    entries: List[Dict[str, object]] = []
    siblings: List[Dict[str, object]] = []
    seen: Dict[str, int] = {}
    for hole in holes:
        label = hole["type"]
        if not hole["certified"] or not label:
            continue
        if label in seen:
            siblings.append(hole)
            continue
        seen[label] = len(entries)
        ensemble = arrival_counts(hole["center"], REFERENCE_SEED, starts)
        profile = share_profile(ensemble["counts"])
        entries.append({
            "label": label,
            "hole": hole["name"],
            "construction": hole["construction"],
            "center": hole["center"],
            "vertices": hole["vertices"],
            "certified_vertex_count": hole["vertex_count"],
            "profile": profile,
            "support": ensemble["vertex_count"],
            "arrivals": ensemble["arrivals"],
            "strays": ensemble["strays"],
            "counts": ensemble["counts"],
            "reached_of_certified": sum(
                1 for v in hole["vertices"] if v in ensemble["counts"]),
            "support_within_certified": all(
                v in set(hole["vertices"]) for v in ensemble["support"]),
        })
    return {
        "entries": tuple(entries),
        "labels": tuple(entry["label"] for entry in entries),
        "size": len(entries),
        "siblings": tuple(siblings),
        "catalogue_size": len(niemeier.NIEMEIER_ROOT_SYSTEMS),
        "missing_types": tuple(
            name for name, _r, _h in niemeier.NIEMEIER_ROOT_SYSTEMS
            if name not in seen),
        "holes": holes,
    }


@lru_cache(maxsize=None)
def query_set(walks: int = len(WALK_SEEDS), starts: int = STARTS
              ) -> Tuple[Dict[str, object], ...]:
    """Every query, with its ground truth re-certified at its own centre."""
    table = reference_table(walks, starts)
    queries: List[Dict[str, object]] = []
    for index, entry in enumerate(table["entries"]):
        for transform in transforms():
            kind = str(transform["kind"])
            center = tuple(Fraction(x) for x in _apply(kind, entry["center"]))
            moved = tuple(sorted(_apply_point(kind, v)
                                 for v in entry["vertices"]))
            check = _certify_at(center, moved)
            name = f"hole {index} · {transform['key']}"
            if not check["certified"] or check["type"] != entry["label"]:
                queries.append({
                    "name": name,
                    "transform": transform["key"],
                    "truth": entry["label"],
                    "used": False,
                    "reason": (f"the transform did not re-certify as "
                               f"{entry['label']} (read {check['type']}, "
                               f"certified {check['certified']}), so it is "
                               f"dropped"),
                })
                continue
            ensemble = arrival_counts(center, int(transform["seed"]), starts)
            queries.append({
                "name": name,
                "transform": transform["key"],
                "truth": entry["label"],
                "used": True,
                "seed": int(transform["seed"]),
                "profile": share_profile(ensemble["counts"]),
                "support": ensemble["vertex_count"],
                "arrivals": ensemble["arrivals"],
                "strays": ensemble["strays"],
                "reason": "",
            })
    for sibling in table["siblings"]:
        ensemble = arrival_counts(sibling["center"], QUERY_SEEDS["sibling"],
                                  starts)
        queries.append({
            "name": f"{sibling['name']} · sibling centre",
            "transform": "sibling",
            "truth": sibling["type"],
            "used": True,
            "seed": QUERY_SEEDS["sibling"],
            "profile": share_profile(ensemble["counts"]),
            "support": ensemble["vertex_count"],
            "arrivals": ensemble["arrivals"],
            "strays": ensemble["strays"],
            "reason": "",
        })
    return tuple(queries)


# ═════════════════════════════════════════════════════════════════════════
# 6.  THE CLASSIFIER, WITH A STATED REFUSAL
# ═════════════════════════════════════════════════════════════════════════

def classify(profile: Sequence[Fraction],
             table: Sequence[Tuple[str, Sequence[Fraction]]],
             radius: Fraction = OPERATING_RADIUS) -> Dict[str, object]:
    """Nearest reference within ``radius``, or a refusal that says which.

    Three verdicts, and no fourth: ``named`` when one reference is strictly
    nearest and within the radius, ``ambiguous`` when the minimum is attained
    more than once inside it, ``absent`` when nothing is inside it.  This is
    ``GLM.DeepHole.classify`` in the Lean file, and the totality and
    single-valuedness are proved there.
    """
    distances = [(label, l1(profile, reference)) for label, reference in table]
    if not distances:
        return {"verdict": "absent", "label": None, "distance": None,
                "runner_up": None, "margin": None, "distances": ()}
    best = min(distance for _label, distance in distances)
    winners = [label for label, distance in distances if distance == best]
    ordered = tuple(sorted(((str(label), distance)
                            for label, distance in distances),
                           key=lambda row: (row[1], row[0])))
    runner_up = ordered[1][1] if len(ordered) > 1 else None
    if best > radius:
        return {"verdict": "absent", "label": None, "distance": best,
                "runner_up": runner_up,
                "margin": None if runner_up is None else runner_up - best,
                "distances": ordered}
    if len(winners) > 1:
        return {"verdict": "ambiguous", "label": None, "distance": best,
                "runner_up": runner_up, "margin": Fraction(0),
                "distances": ordered}
    return {"verdict": "named", "label": winners[0], "distance": best,
            "runner_up": runner_up,
            "margin": None if runner_up is None else runner_up - best,
            "distances": ordered}


def separation(table: Sequence[Tuple[str, Sequence[Fraction]]]
               ) -> Dict[str, object]:
    """The pairwise L1 separations of the reference profiles."""
    pairs: List[Tuple[str, str, Fraction]] = []
    for i in range(len(table)):
        for j in range(i + 1, len(table)):
            pairs.append((str(table[i][0]), str(table[j][0]),
                          l1(table[i][1], table[j][1])))
    smallest = min((row[2] for row in pairs), default=None)
    closest = min(pairs, key=lambda row: row[2]) if pairs else None
    return {"pairs": tuple(sorted(pairs, key=lambda row: row[2])),
            "pair_count": len(pairs),
            "minimum": smallest,
            "closest_pair": closest}


def certified_radius(table: Sequence[Tuple[str, Sequence[Fraction]]]
                     ) -> Optional[Fraction]:
    """``r* = half the smallest pairwise separation`` -- measured, not chosen.

    Under ``r*`` at most one reference can be within range of any profile, so
    a ``named`` verdict is provably unique and an ``absent`` verdict is a
    certified absence.  That implication is ``GLM.DeepHole`` in Lean.
    """
    smallest = separation(table)["minimum"]
    return None if smallest is None else Fraction(smallest, 2)


# ═════════════════════════════════════════════════════════════════════════
# 7.  THE RUN, THE CONTROLS AND THE SCORE
# ═════════════════════════════════════════════════════════════════════════

def _binomial(n: int, k: int) -> int:
    if k < 0 or k > n:
        return 0
    out = 1
    for i in range(k):
        out = out * (n - i) // (i + 1)
    return out


def tail_probability(correct: int, queries: int, labels: int) -> Fraction:
    """Exactly the chance a uniform labeller does at least this well."""
    if queries <= 0 or labels <= 0:
        return Fraction(1)
    p = Fraction(1, labels)
    total = Fraction(0)
    for j in range(correct, queries + 1):
        total += _binomial(queries, j) * p ** j * (1 - p) ** (queries - j)
    return total


def _run(name: str, queries: Sequence[Dict[str, object]],
         table: Sequence[Tuple[str, Sequence[Fraction]]],
         profile_of, radius: Fraction = OPERATING_RADIUS) -> Dict[str, object]:
    """One classifier over the whole query set, method or control alike."""
    rows: List[Dict[str, object]] = []
    correct = 0
    refused = 0
    wrong = 0
    for query in queries:
        if not query.get("used"):
            continue
        outcome = classify(profile_of(query), table, radius)
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
            "query": query["name"],
            "truth": query["truth"],
            "verdict": outcome["verdict"],
            "label": outcome["label"],
            "distance": outcome["distance"],
            "margin": outcome["margin"],
            "own_distance": own,
            "own_rank": (ranked.index(str(query["truth"])) + 1
                         if str(query["truth"]) in ranked else None),
            "correct": hit,
        })
    total = len(rows)
    labels = max(1, len(table))
    tail = tail_probability(correct, total, labels)
    return {
        "name": name,
        "rows": tuple(rows),
        "queries": total,
        "correct": correct,
        "wrong": wrong,
        "refused": refused,
        "accuracy": Fraction(correct, total) if total else Fraction(0),
        "chance": Fraction(1, labels),
        "tail": tail,
        "score": wls.bit_score(tail, STATISTICS_TRIED),
    }


def _reshuffled(labels: Sequence[str], seed: int = REFERENCE_SEED
                ) -> Tuple[str, ...]:
    """A declared seeded permutation of the labels, never the identity."""
    order = list(labels)
    if len(order) < 2:
        return tuple(order)
    sweep = _Sweep(seed)
    for index in range(len(order) - 1, 0, -1):
        swap = sweep.below(index + 1)
        order[index], order[swap] = order[swap], order[index]
    if tuple(order) == tuple(labels):
        order[0], order[1] = order[1], order[0]
    return tuple(order)


def score_run(walks: int = len(WALK_SEEDS), starts: int = STARTS
              ) -> Dict[str, object]:
    """The method and every control, over the same query set."""
    table = reference_table(walks, starts)
    entries = table["entries"]
    queries = query_set(walks, starts)
    method_table = tuple((entry["label"], entry["profile"])
                         for entry in entries)

    method = _run("the arrival-share profile", queries, method_table,
                  lambda query: query["profile"])

    digest_table = tuple((entry["label"], digest_profile(entry["label"]))
                         for entry in entries)
    digest = _run("digest control (D3)", queries, digest_table,
                  lambda query: digest_profile(query["name"]),
                  radius=Fraction(2))

    shuffled = _reshuffled([entry["label"] for entry in entries])
    reshuffle_table = tuple((shuffled[i], entries[i]["profile"])
                            for i in range(len(entries)))
    reshuffle = _run("seeded reshuffle of the pairing", queries,
                     reshuffle_table, lambda query: query["profile"])

    count_table = tuple((entry["label"], uniform_profile(entry["support"]))
                        for entry in entries)
    baseline = _run("the plain vertex count", queries, count_table,
                    lambda query: uniform_profile(query["support"]),
                    radius=Fraction(0))
    ablation = _run("uniform-profile ablation", queries, count_table,
                    lambda query: uniform_profile(query["support"]))

    radius_star = certified_radius(method_table)
    certified = _run("the method at the certified radius r*", queries,
                     method_table, lambda query: query["profile"],
                     radius=radius_star if radius_star is not None
                     else Fraction(0))
    own = [row["own_distance"] for row in method["rows"]
           if row["own_distance"] is not None]
    faithfulness = max(own) if own else None
    compatible = (faithfulness is not None and radius_star is not None
                  and faithfulness <= radius_star)

    return {
        "method": method,
        "certified": certified,
        "faithfulness_radius": faithfulness,
        "faithfulness_compatible": compatible,
        # Every query is a hole that *is* present and *is* tabulated, so an
        # `absent` verdict at r* is a false absence, and counting them is how
        # the certified-absence theorem is held to account.
        "absent_at_r_star": sum(1 for row in certified["rows"]
                                if row["verdict"] == "absent"),
        "own_rank_first": sum(1 for row in method["rows"]
                              if row["own_rank"] == 1),
        "controls": (digest, reshuffle, baseline, ablation),
        "digest": digest,
        "reshuffle": reshuffle,
        "baseline": baseline,
        "ablation": ablation,
        "reshuffled_labels": shuffled,
        "separation": separation(method_table),
        "certified_radius": certified_radius(method_table),
        "operating_radius": OPERATING_RADIUS,
        "beats_every_control": all(
            method["accuracy"] > control["accuracy"]
            for control in (digest, reshuffle, baseline, ablation)),
        "beats_baseline": method["accuracy"] > baseline["accuracy"],
    }


def per_type(run: Dict[str, object], labels: Sequence[str]
             ) -> Tuple[Dict[str, object], ...]:
    """How each type fared, query by query, for the study's table."""
    out: List[Dict[str, object]] = []
    for label in labels:
        rows = [row for row in run["rows"] if row["truth"] == label]
        out.append({
            "label": label,
            "queries": len(rows),
            "correct": sum(1 for row in rows if row["correct"]),
            "recovered": bool(rows) and all(row["correct"] for row in rows),
            "own_rank_first": sum(1 for row in rows if row["own_rank"] == 1),
        })
    return tuple(out)


def _recovered(run: Dict[str, object], labels: Sequence[str]
               ) -> Tuple[str, ...]:
    """The types every one of whose queries this run named correctly."""
    out: List[str] = []
    for label in labels:
        rows = [row for row in run["rows"] if row["truth"] == label]
        if rows and all(row["correct"] for row in rows):
            out.append(str(label))
    return tuple(out)


def gate_decision(walks: int = len(WALK_SEEDS), starts: int = STARTS
                  ) -> Dict[str, object]:
    """The pre-registered decision tree, applied to the numbers."""
    run = score_run(walks, starts)
    table = reference_table(walks, starts)
    labels = [entry["label"] for entry in table["entries"]]
    method = run["method"]
    baseline = run["baseline"]

    sanity = [row for row in method["rows"]
              if row["query"].endswith("· seed")]
    sanity_holds = bool(sanity) and all(row["correct"] for row in sanity)

    method_types = _recovered(method, labels)
    baseline_types = _recovered(baseline, labels)
    beyond = tuple(t for t in method_types if t not in baseline_types)
    score = Fraction(method["score"]["corrected"])
    passes_bits = score >= GATE_BITS

    if not sanity_holds:
        verdict = "stopped at the sanity query"
        reading = ("the statistic does not survive a seed change at a fixed "
                   "centre, so the ensemble is measuring the sweep and not "
                   "the hole")
    elif not run["beats_baseline"]:
        verdict = "no better than the vertex count"
        reading = ("the trajectory distribution adds nothing over the static "
                   "vertex count, so no classification faculty is claimed")
    elif not passes_bits:
        verdict = "weak"
        reading = ("the method beats the vertex count but scores below the "
                   "gate of 3 bits, so it ships as a measurement and no "
                   "faculty is claimed")
    elif len(beyond) < 2:
        verdict = "a coincidence"
        reading = ("the method beats the vertex count and the gate, but it "
                   "recovers at most one type the vertex count cannot, which "
                   "the study fixed in advance as a coincidence rather than a "
                   "method")
    else:
        verdict = "a method"
        reading = ("the method beats the vertex count and the gate and "
                   "recovers more than one type the vertex count cannot, so "
                   "the classification faculty is claimed and the "
                   "certified-absence theorem is instantiated at r*")
    return {
        "verdict": verdict,
        "reading": reading,
        "sanity_holds": sanity_holds,
        "sanity_queries": len(sanity),
        "beats_baseline": run["beats_baseline"],
        "beats_every_control": run["beats_every_control"],
        "score": score,
        "score_rounded": method["score"]["corrected_rounded"],
        "gate_bits": GATE_BITS,
        "passes_bits": passes_bits,
        "recovered": method_types,
        "recovered_count": len(method_types),
        "baseline_recovered": baseline_types,
        "beyond_baseline": beyond,
        "per_type": per_type(method, labels),
        "per_type_baseline": per_type(baseline, labels),
        "claims_faculty": verdict == "a method",
    }


# ═════════════════════════════════════════════════════════════════════════
# 8.  THE REPORT
# ═════════════════════════════════════════════════════════════════════════

def _stability(walks: int, starts: int) -> Dict[str, object]:
    """The declared secondary: the same classification at 120 starts."""
    if starts <= STABILITY_STARTS:
        return {"run": False, "starts": starts}
    short = score_run(walks, STABILITY_STARTS)
    full = score_run(walks, starts)
    return {
        "run": True,
        "starts": STABILITY_STARTS,
        "accuracy": short["method"]["accuracy"],
        "full_accuracy": full["method"]["accuracy"],
        "agrees": short["method"]["accuracy"] == full["method"]["accuracy"],
        "beats_baseline": short["beats_baseline"],
    }


@lru_cache(maxsize=None)
def deep_hole_classifier_report(walks: int = len(WALK_SEEDS),
                                starts: int = STARTS) -> Dict[str, object]:
    """Everything this module knows, recomputed on call."""
    table = reference_table(walks, starts)
    run = score_run(walks, starts)
    gate = gate_decision(walks, starts)
    return {
        "starts": starts,
        "stability": _stability(walks, starts),
        "walk_budget": len(WALK_SEEDS[:walks]),
        "reference_seed": REFERENCE_SEED,
        "permutation": golay_permutation(),
        "table": table,
        "run": run,
        "gate": gate,
        "statistics_tried": STATISTICS_TRIED,
        "catalogue_size": len(niemeier.NIEMEIER_ROOT_SYSTEMS),
        "method": (
            "A hole is named by how often the modulator's trajectory arrives "
            "at each of its vertices, never by a distance between two of "
            "them.  For a centre and a declared seed the ensemble runs 240 "
            "starts of one tick each through the exact nearest-Leech-point "
            "decoder; the arrival shares, sorted and padded to 48, are the "
            "statistic; the label is the nearest reference profile within "
            "the operating radius, with a stated refusal when nothing is "
            "near enough or two references tie."),
        "controls": (
            "Four, all on the same query set.  A digest control, because a "
            "hash of a name carries no geometry and must score at chance; a "
            "seeded reshuffle of the pairing; the plain vertex count, which "
            "is the competitor that matters because a deep hole has 24 + k "
            "vertices and that already names some types; and a "
            "uniform-profile ablation, which is the vertex count expressed "
            "inside the method's own metric, so the gap between it and the "
            "method is exactly what the shape of the arrival distribution "
            "is worth."),
        "limits": (
            "Three.  The ensemble of start offsets is not enumerable -- "
            "there are 2001**24 of them -- so the study declares the exact "
            "finite deterministic ensemble it uses instead, and a different "
            "seed is a different declared ensemble rather than a re-run.  "
            "The walk budget reaches the types it reaches and the rest are "
            "reported as not reached, because reaching a named type on "
            "demand would need its centre, which is the stored table the "
            "exercise avoids.  And the classifier is a classifier of holes: "
            "a carrier that is not at the covering radius has no type and "
            "is refused."),
    }


# ═════════════════════════════════════════════════════════════════════════
# 9.  THE CACHE, GUARDED BY A DIGEST
# ═════════════════════════════════════════════════════════════════════════

DATA_PATH = (Path(__file__).resolve().parent / "_data"
             / "deep_hole_classifier.json")

#: A change to any of these makes the cache stale, which is D4.
_SOURCES: Tuple[str, ...] = (
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


def measure() -> Dict[str, object]:
    """The report, with the digest of what it was taken from beside it."""
    payload = dict(deep_hole_classifier_report())
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
