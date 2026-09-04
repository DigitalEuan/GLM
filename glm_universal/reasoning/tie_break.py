"""``glm_universal.reasoning.tie_break`` -- the part of an address geometry
does not decide.

What this module is
-------------------
Most of this development's Leech addresses are **not unique**: the scaled
feature vector sits exactly equidistant from several lattice points, and which
of them becomes the address is settled by the decoder's tie-break -- three
unremarked lines of :mod:`~glm_universal.reasoning.analogy`.  This module makes
the tie an object:

``tie_record`` / ``tie_class_size`` / ``tie_class`` / ``canonical_point``
    the tie class of a rational 24-vector, counted in **closed form** and
    listed on request.  The count never enumerates: inside one congruence
    branch the coordinates decouple except for the sum-mod-8 condition, a tied
    coordinate has exactly two options differing by 4
    (``nearest_in_residue_class_differ_by_four``), raising one flips the sum
    condition (``sum_raise_mod_eight``), and the two parities of subset are
    equinumerous (``card_odd_subsets``), so ``k`` tied coordinates give
    ``2 ** (k - 1)`` minimisers;
``RULE`` / ``decoder_point``
    what the shipped decoder actually does, stated clause by clause, against
    the canonical alternative -- take the least member of the class -- which is
    well defined for the reason clause 3 is not (``isLexLeast_unique``);
``tie_census`` / ``canonical_separation`` / ``scale_tie_table``
    the measurement: how many addresses are decided by the tie-break, what
    changes if the canonical rule is used instead, and why avoiding the ties by
    choosing another scale is not available -- a tie-free scale is a
    *degenerate* scale, one at which the decoder returns its input.

The formal development is ``RequestProject/GLM/TieBreak.lean`` and by D8 it is
the specification.  Everything here is exact ``int`` / ``Fraction``; no float
is constructed anywhere.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from ..substrate import mog
from . import lean_address as la
from . import llvq_table

__all__ = [
    "SCALE", "COVERING_RADIUS", "RULE",
    "residue_options", "even_subset_count", "branch_minimum",
    "tie_record", "tie_class_size", "tie_class", "canonical_point",
    "decoder_point", "tie_census", "canonical_separation",
    "scale_tie_table", "tie_break_report",
]

#: The address book's scale factor.
SCALE = la.SCALE

#: The covering radius of the Leech lattice in this integer model.
COVERING_RADIUS = la.COVERING_RADIUS

#: The decoder's rule, transcribed clause by clause from
#: :func:`glm_universal.reasoning.analogy.nearest_lattice_point`.  Each clause
#: is a *choice*: the objective is already attained by every option it
#: discards.
RULE: Tuple[Dict[str, str], ...] = (
    {"clause": "round half down",
     "where": "analogy._round_to_residue",
     "says": "of the two nearest integers in a residue class mod 4, take the "
             "smaller"},
    {"clause": "repair the sum at the earliest free coordinate",
     "where": "analogy.nearest_lattice_point, the sum-mod-8 repair",
     "says": "move one coordinate by +-4: the least penalty, the earliest of "
             "those, upwards on a tie -- and a coordinate that was itself "
             "tied has penalty 0, so the repair lands on the earliest tied "
             "coordinate"},
    {"clause": "lexicographically least across cosets",
     "where": "analogy.nearest_lattice_point, the incumbent comparison",
     "says": "among the 2 x 4,096 coset representatives of equal cost, keep "
             "the lexicographically least -- which ranges over the "
             "representatives clauses 1 and 2 produced, not over the tie "
             "class"},
)


# ---------------------------------------------------------------------------
# 1.  One coordinate
# ---------------------------------------------------------------------------
def residue_options(value: Fraction, residue: int
                    ) -> Tuple[Tuple[int, ...], Fraction]:
    """The integers congruent to ``residue`` mod 4 nearest to ``value``.

    One of them, or two when ``value`` is exactly halfway between two such
    integers -- and then they differ by exactly 4
    (``TieBreak.nearest_in_residue_class_differ_by_four``).  The second return
    value is the squared distance, which is the same for both.
    """
    value = Fraction(value)
    shifted = (value - residue) / 4
    floor_k = shifted.numerator // shifted.denominator
    best: List[int] = []
    best_cost: Optional[Fraction] = None
    for k in (floor_k, floor_k + 1):
        x = residue + 4 * k
        cost = (value - x) ** 2
        if best_cost is None or cost < best_cost:
            best_cost, best = cost, [x]
        elif cost == best_cost and x not in best:
            best.append(x)
    assert best_cost is not None
    return tuple(sorted(best)), best_cost


def _penalty(value: Fraction, options: Sequence[int], cost: Fraction
             ) -> Fraction:
    """The extra cost of the cheapest ``+-4`` move away from the optimum."""
    candidates = [(value - (x + step)) ** 2
                  for x in options for step in (4, -4)
                  if (x + step) not in options]
    return min(candidates) - cost


def even_subset_count(size: int) -> int:
    """How many subsets of a ``size``-element set have a given parity.

    ``1`` when the set is empty -- only the empty subset -- and ``2 ** (n-1)``
    otherwise, which is ``TieBreak.card_even_subsets``.
    """
    if size < 0:
        raise ValueError("even_subset_count: size must be non-negative")
    return 1 if size == 0 else 1 << (size - 1)


# ---------------------------------------------------------------------------
# 2.  One congruence branch
# ---------------------------------------------------------------------------
def _coordinate_table(vector: Sequence, parity: int
                      ) -> Tuple[Tuple[Tuple[int, ...], Fraction, Fraction], ...]:
    """For each coordinate and each of the branch's two residues, the options,
    their shared cost, and the penalty of stepping outside them."""
    rows = []
    for value in vector:
        value = Fraction(value)
        row = []
        for residue in (parity % 4, (parity + 2) % 4):
            options, cost = residue_options(value, residue)
            row.append((options, cost, _penalty(value, options, cost)))
        rows.append(tuple(row))
    return tuple(rows)


def branch_minimum(vector: Sequence, parity: int, word: int
                   ) -> Dict[str, object]:
    """The minimum of one congruence branch, its size, and its least member.

    The branch is the parity ``m`` together with the Golay word ``w`` saying
    which coordinates sit in the *other* residue class.  This is the readable
    statement of section 2 of ``studies/TIE_BREAK_STUDY.md``; :func:`tie_record`
    runs the same arithmetic over all 8,192 branches at once.
    """
    values = [Fraction(v) for v in vector]
    cost = Fraction(0)
    options: List[Tuple[int, ...]] = []
    penalties: List[Fraction] = []
    for index, value in enumerate(values):
        residue = ((parity + 2) if (word >> index) & 1 else parity) % 4
        opts, c = residue_options(value, residue)
        cost += c
        options.append(opts)
        penalties.append(_penalty(value, opts, c))
    tied = [i for i, opts in enumerate(options) if len(opts) == 2]
    low = [opts[0] for opts in options]
    wanted = (4 * parity) % 8
    if tied:
        point = list(low)
        if sum(point) % 8 != wanted:
            # raise the *last* tied coordinate: the least admissible choice
            # (TieBreak.lexLeast_of_odd)
            point[tied[-1]] = options[tied[-1]][1]
        return {
            "cost": cost,
            "count": even_subset_count(len(tied)),
            "point": tuple(point),
            "tied": tuple(tied),
            "repaired": False,
        }
    if sum(low) % 8 == wanted:
        return {"cost": cost, "count": 1, "point": tuple(low),
                "tied": (), "repaired": False}
    # no free coordinate: pay the cheapest +-4 repair, and count every
    # (coordinate, direction) that attains it
    best = min(penalties)
    winners: List[Tuple[int, ...]] = []
    for index, value in enumerate(values):
        if penalties[index] != best:
            continue
        x = low[index]
        for step in (4, -4):
            if (value - (x + step)) ** 2 - (value - x) ** 2 != best:
                continue
            moved = list(low)
            moved[index] = x + step
            winners.append(tuple(moved))
    winners.sort()
    return {
        "cost": cost + best,
        "count": len(winners),
        "point": winners[0],
        "tied": (),
        "repaired": True,
    }


# ---------------------------------------------------------------------------
# 3.  The tie class
# ---------------------------------------------------------------------------
def tie_record(vector: Sequence) -> Dict[str, object]:
    """The tie class of ``vector``: its distance, its size, its least member.

    The size is the closed form -- nothing is enumerated to obtain it.
    """
    values = [Fraction(v) for v in vector]
    best_cost: Optional[Fraction] = None
    size = 0
    canonical: Optional[Tuple[int, ...]] = None
    branches: List[Tuple[int, int]] = []
    for parity in (0, 1):
        table = _coordinate_table(values, parity)
        base_cost = sum(row[0][1] for row in table)
        delta = [row[1][1] - row[0][1] for row in table]
        for word in mog.GOLAY_MASKS:
            cost = base_cost
            for index in range(24):
                if (word >> index) & 1:
                    cost += delta[index]
            if best_cost is not None and cost > best_cost:
                continue        # even a free sum condition cannot win
            record = branch_minimum(values, parity, word)
            if best_cost is None or record["cost"] < best_cost:
                best_cost = Fraction(record["cost"])          # type: ignore[arg-type]
                size = int(record["count"])                   # type: ignore[arg-type]
                canonical = record["point"]                   # type: ignore[assignment]
                branches = [(parity, word)]
            elif record["cost"] == best_cost:
                size += int(record["count"])                  # type: ignore[arg-type]
                if canonical is None or record["point"] < canonical:
                    canonical = record["point"]               # type: ignore[assignment]
                branches.append((parity, word))
    assert best_cost is not None and canonical is not None
    return {
        "distance2": best_cost,
        "size": size,
        "canonical": canonical,
        "branches": tuple(branches),
        "lean": "GLM.TieBreak.Nearest, GLM.TieBreak.card_even_subsets",
    }


def tie_class_size(vector: Sequence) -> int:
    """How many lattice points are equally near -- without listing them."""
    return int(tie_record(vector)["size"])          # type: ignore[arg-type]


def _branch_members(vector: Sequence, parity: int, word: int
                    ) -> List[Tuple[int, ...]]:
    """Every minimiser of one branch, listed."""
    record = branch_minimum(vector, parity, word)
    values = [Fraction(v) for v in vector]
    options: List[Tuple[int, ...]] = []
    for index, value in enumerate(values):
        residue = ((parity + 2) if (word >> index) & 1 else parity) % 4
        options.append(residue_options(value, residue)[0])
    tied = list(record["tied"])                     # type: ignore[arg-type]
    if not tied:
        if not record["repaired"]:
            return [record["point"]]                # type: ignore[list-item]
        low = [opts[0] for opts in options]
        best = min(_penalty(values[i], options[i],
                            (values[i] - low[i]) ** 2) for i in range(24))
        members: List[Tuple[int, ...]] = []
        for index, value in enumerate(values):
            x = low[index]
            for step in (4, -4):
                if (value - (x + step)) ** 2 - (value - x) ** 2 != best:
                    continue
                moved = list(low)
                moved[index] = x + step
                members.append(tuple(moved))
        return sorted(set(members))
    low = [opts[0] for opts in options]
    wanted = (4 * parity) % 8
    members = []
    for mask in range(1 << len(tied)):
        point = list(low)
        for slot, index in enumerate(tied):
            if (mask >> slot) & 1:
                point[index] = options[index][1]
        if sum(point) % 8 == wanted:
            members.append(tuple(point))
    return members


def tie_class(vector: Sequence, cap: int = 4096) -> List[Tuple[int, ...]]:
    """Every member of the tie class, sorted, least first.

    Refused rather than truncated when the class is larger than ``cap``: a
    truncated tie class is a wrong answer, not a partial one.
    """
    record = tie_record(vector)
    size = int(record["size"])                      # type: ignore[arg-type]
    if size > cap:
        raise ValueError(
            f"tie_class: the class has {size} members, above the cap {cap}; "
            f"raise the cap or use tie_class_size")
    members: List[Tuple[int, ...]] = []
    for parity, word in record["branches"]:         # type: ignore[union-attr]
        members.extend(_branch_members(vector, parity, word))
    members = sorted(set(members))
    assert len(members) == size, (
        f"tie_class: listed {len(members)} members, closed form says {size}")
    return members


def canonical_point(vector: Sequence) -> Tuple[int, ...]:
    """The stated rule: the lexicographically least member of the tie class."""
    return tuple(tie_record(vector)["canonical"])   # type: ignore[arg-type]


def decoder_point(vector: Sequence) -> Tuple[int, ...]:
    """What the shipped decoder returns -- the address as it stands."""
    result = llvq_table.nearest_lattice_point_table(
        [Fraction(v) for v in vector])
    return tuple(int(c) for c in result.point)


# ---------------------------------------------------------------------------
# 4.  The census
# ---------------------------------------------------------------------------
def _scaled(features: Sequence[int], scale: int = SCALE) -> Tuple[Fraction, ...]:
    return tuple(Fraction(int(v) * scale) for v in features)


def tie_census(limit: Optional[int] = None) -> Dict[str, object]:
    """How much of the address book is decided by the tie-break."""
    table = la.feature_table()
    names = list(table)[:limit] if limit is not None else list(table)
    sizes: Dict[int, int] = {}
    decided = in_class = canonical_hits = differs = read_back_agrees = 0
    worst_distance2 = Fraction(0)
    largest = 0
    largest_at = ""
    for name in names:
        vector = _scaled(table[name])
        record = tie_record(vector)
        size = int(record["size"])                  # type: ignore[arg-type]
        sizes[size] = sizes.get(size, 0) + 1
        decided += size > 1
        if size > largest:
            largest, largest_at = size, name
        worst_distance2 = max(worst_distance2,
                              Fraction(record["distance2"]))  # type: ignore[arg-type]
        decoder = decoder_point(vector)
        canonical = tuple(record["canonical"])      # type: ignore[arg-type]
        if size <= 4096:
            in_class += decoder in tie_class(vector)
        else:                                       # pragma: no cover
            in_class += 1
        if decoder == canonical:
            canonical_hits += 1
        else:
            differs += 1
        read_back_agrees += (la.describe_address(decoder)["recovered"]
                             == la.describe_address(canonical)["recovered"])
    return {
        "declarations": len(names),
        "decided_by_geometry": len(names) - decided,
        "decided_by_the_tie_break": decided,
        "class_size_histogram": dict(sorted(sizes.items())),
        "decoder_in_tie_class": in_class,
        "decoder_is_canonical": canonical_hits,
        "decoder_differs_from_canonical": differs,
        "read_back_agrees": read_back_agrees,
        "largest_class": largest,
        "largest_class_at": largest_at,
        "worst_distance2": worst_distance2,
        "lean": "GLM.TieBreak.mem_nearest, GLM.TieBreak.readback_of_tie_class",
    }


def _addresses(rule: str, limit: Optional[int] = None
               ) -> Dict[str, Tuple[int, ...]]:
    table = la.feature_table()
    names = list(table)[:limit] if limit is not None else list(table)
    out: Dict[str, Tuple[int, ...]] = {}
    for name in names:
        vector = _scaled(table[name])
        out[name] = (canonical_point(vector) if rule == "canonical"
                     else decoder_point(vector))
    return out


def _separation(table: Dict[str, Tuple[int, ...]]) -> Dict[str, object]:
    """The address study's separation figures, for a given address table."""
    book = la.address_book()
    names = [n for n in table]
    files = ({n: book["declarations"][n]["file"] for n in names}
             if book else {n: "" for n in names})
    graph = la.citation_graph()
    linked = {n: set(graph.get(n, ())) for n in names}
    for source, targets in graph.items():
        for target in targets:
            if target in linked:
                linked[target].add(source)
    same_total = same_count = cross_total = cross_count = 0
    for i, a in enumerate(names):
        pa = table[a]
        for b in names[i + 1:]:
            distance = la.squared_distance(pa, table[b])
            if files[b] == files[a]:
                same_total += distance
                same_count += 1
            else:
                cross_total += distance
                cross_count += 1
    same_file = cited = 0
    for a in names:
        pa = table[a]
        best = None
        winners: List[str] = []
        for b in names:
            if b == a:
                continue
            distance = la.squared_distance(pa, table[b])
            if best is None or distance < best:
                best, winners = distance, [b]
            elif distance == best:
                winners.append(b)
        if winners and all(files[w] == files[a] for w in winners):
            same_file += 1
        if winners and all(w in linked[a] for w in winners):
            cited += 1
    return {
        "declarations": len(names),
        "distinct_addresses": len(set(table.values())),
        "nearest_shares_a_file": same_file,
        "nearest_is_cited": cited,
        "same_file_mean_squared_distance":
            Fraction(same_total, same_count) if same_count else Fraction(0),
        "cross_file_mean_squared_distance":
            Fraction(cross_total, cross_count) if cross_count else Fraction(0),
    }


def canonical_separation(limit: Optional[int] = None) -> Dict[str, object]:
    """Both address books, figure by figure: what the tie-break moves."""
    decoder = _addresses("decoder", limit)
    canonical = _addresses("canonical", limit)
    moved = sum(1 for name in decoder if decoder[name] != canonical[name])
    return {
        "declarations": len(decoder),
        "addresses_that_move": moved,
        "decoder": _separation(decoder),
        "canonical": _separation(canonical),
    }


def scale_tie_table(scales: Sequence[int] = tuple(range(1, 25)),
                    sample: int = 40) -> Dict[str, object]:
    """Is there a scale with no ties?  Only a degenerate one.

    ``eightZ_mem_leech`` says ``8Z^24`` is inside the lattice, so at a multiple
    of eight the input is already a lattice point and the decoder returns it
    unchanged -- the ties vanish because nothing is being decided.
    """
    table = la.feature_table()
    names = list(table)[:sample]
    rows: List[Dict[str, object]] = []
    tie_free_and_working = 0
    for scale in scales:
        tied = moved = 0
        largest = 1
        worst = Fraction(0)
        for name in names:
            vector = _scaled(table[name], scale)
            record = tie_record(vector)
            size = int(record["size"])              # type: ignore[arg-type]
            tied += size > 1
            largest = max(largest, size)
            worst = max(worst, Fraction(record["distance2"]))  # type: ignore[arg-type]
            moved += Fraction(record["distance2"]) != 0        # type: ignore[arg-type]
        row = {
            "scale": scale,
            "declarations": len(names),
            "tied": tied,
            "moved_by_the_decoder": moved,
            "largest_class": largest,
            "worst_distance2": worst,
            "tie_free": tied == 0,
            "degenerate": moved == 0,
        }
        tie_free_and_working += bool(row["tie_free"]) and not row["degenerate"]
        rows.append(row)
    return {
        "rows": rows,
        "sample": len(names),
        "tie_free_and_working": tie_free_and_working,
        "lean": "GLM.Address.eightZ_mem_leech",
    }


def tie_break_report(limit: Optional[int] = 40) -> Dict[str, object]:
    """The study in one call, at a size a report can afford."""
    return {
        "rule": list(RULE),
        "census": tie_census(limit=limit),
        "scales": scale_tie_table(scales=(4, 6, 8, 9, 12, 16),
                                  sample=min(limit or 40, 40)),
        "covering_radius": COVERING_RADIUS,
        "scale": SCALE,
        "study": "studies/TIE_BREAK_STUDY.md",
        "lean_file": "RequestProject/GLM/TieBreak.lean",
    }
