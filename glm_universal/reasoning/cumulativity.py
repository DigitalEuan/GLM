"""``glm_universal.reasoning.cumulativity`` -- the refinement check every layer
family must pass before it ships.

The rule this module is the instrument for
------------------------------------------
**A layer ships with its refinement check, or it does not ship.**

:mod:`~glm_universal.reasoning.information_loss` established what cumulativity
is worth: an operation ceases to be a function of what a layer sees exactly
when the layer stops refining the one below it, and the first run of that check
at scale caught a real design flaw -- the ``substrate -> integer`` step of the
shipped layer code, which read the seven SI7 exponents and discarded the
substrate's own view instead of adding to it.  That defect was reported rather
than quietly patched, and the rejected reading is still in the tree as
:data:`~glm_universal.reasoning.dimension_layers.LAYER_INTEGER_RAW` so that its
cost can be re-measured.

That precedent is the argument for making the check a standing obligation
rather than an intention.  This module turns it into one: every declared layer
family in the system registers here with its rungs, its declared refinement
edges and a probe set, and :func:`cumulativity_report` re-runs the check over
all of them.  A family that ships and violates an edge is a defect, and the
suite fails.

Two failure modes, deliberately kept apart
------------------------------------------
The check distinguishes two things that look alike and have different remedies.

**A refinement violation** is a pair of probes the *lower* rung tells apart and
the *higher* rung conflates.  It means the higher rung is not cumulative over
the lower one: escalating loses information the system already had.  The remedy
is a constraint on how the layer is built -- carry the lower rung's reading
alongside the new one.  This is what the rule above forbids.

**A conflation** is a pair of probes that a rung cannot tell apart at all,
though they are distinct.  It is not a failure of construction; it is the
rung's resolution, and no amount of refinement discipline repairs it.  The
deep-hole ladder has one that matters: read alone, the exact rational measure
of emission distances gives ``A_1^24`` and ``A_2^12`` the same single-atom
measure, and the pair is separated not by refining that rung but by **joining**
it to a reading that sees something else.  Cumulativity prevents a new rung
from re-inflicting a loss; only a join repairs a loss already there.

Because the two are distinct, a family's declared structure is a **directed
graph and not a chain**: an edge asserts refinement and is checked, and a
declared **non-edge** asserts that a rung does *not* refine another and is
checked too, by requiring a witness.  A ladder whose shape is asserted rather
than measured would hide exactly the conflation above.

Exactness
---------
Integers and :class:`~fractions.Fraction` throughout; every probe set is a
fixed declared list, and no digest, float or random source appears anywhere.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import (Callable, Dict, List, Optional, Sequence, Tuple)

__all__ = [
    "Rung", "Family", "FAMILIES", "family_by_key",
    "check_edge", "check_non_edge", "conflations", "check_family",
    "cumulativity_report", "shipped_defects", "rule_holds",
]


# ═════════════════════════════════════════════════════════════════════════
# 1.  WHAT A RUNG AND A FAMILY ARE
# ═════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Rung:
    """One reading in a family: what it can tell apart, and how far apart.

    ``same`` is the reading's own verdict that two probes are the same thing.
    ``metric`` is optional and is only used where two rungs' metrics are
    commensurable, in which case the stronger, constructive form of refinement
    -- ``d_higher >= d_lower`` on every probe pair -- is checked as well.
    """

    name: str
    title: str
    same: Callable[[object, object], bool]
    metric: Optional[Callable[[object, object], Fraction]] = None


@dataclass(frozen=True)
class Family:
    """A declared collection of readings, with the shape it claims to have."""

    key: str
    title: str
    rungs: Tuple[Rung, ...]
    probes: Callable[[], Sequence[object]]
    #: ``(lower, higher)``: the higher rung claims to see at least as much.
    edges: Tuple[Tuple[str, str], ...]
    #: ``(lower, higher)``: pairs where refinement is *denied*, and a witness
    #: is required to exist.  This is what keeps a ladder's shape measured.
    non_edges: Tuple[Tuple[str, str], ...] = ()
    #: Does the shipped system use this family?  A family kept only so that a
    #: rejected reading can still be priced is registered with ``False``.
    shipped: bool = True
    note: str = ""
    probe_names: Optional[Callable[[], Sequence[str]]] = None


def _rung(family: Family, name: str) -> Rung:
    for rung in family.rungs:
        if rung.name == name:
            return rung
    raise KeyError(f"{family.key}: no rung named {name!r}")


# ═════════════════════════════════════════════════════════════════════════
# 2.  THE CHECKS
# ═════════════════════════════════════════════════════════════════════════

def _names(family: Family, probes: Sequence[object]) -> Tuple[str, ...]:
    if family.probe_names is not None:
        return tuple(family.probe_names())
    return tuple(f"probe {index}" for index in range(len(probes)))


def check_edge(family: Family, lower: str, higher: str) -> Dict[str, object]:
    """Does ``higher`` see at least as much as ``lower`` on the probes?

    A violation is a probe pair the lower rung splits and the higher rung
    conflates.  Every violating pair is listed, not merely counted, because a
    violation is a design defect and the witness is what fixes it.
    """
    probes = list(family.probes())
    names = _names(family, probes)
    low = _rung(family, lower)
    high = _rung(family, higher)
    violations: List[Dict[str, object]] = []
    dominated = True
    comparable = low.metric is not None and high.metric is not None
    for i in range(len(probes)):
        for j in range(i + 1, len(probes)):
            same_low = low.same(probes[i], probes[j])
            same_high = high.same(probes[i], probes[j])
            if same_high and not same_low:
                violations.append({"left": names[i], "right": names[j]})
            if comparable:
                if (high.metric(probes[i], probes[j])       # type: ignore[misc]
                        < low.metric(probes[i], probes[j])):  # type: ignore[misc]
                    dominated = False
    return {
        "family": family.key, "lower": lower, "higher": higher,
        "pairs": len(probes) * (len(probes) - 1) // 2,
        "violations": tuple(violations),
        "refines": not violations,
        "metrics_comparable": comparable,
        "metric_dominates": dominated if comparable else None,
    }


def check_non_edge(family: Family, lower: str,
                   higher: str) -> Dict[str, object]:
    """A declared non-edge needs a witness, or the shape is an assertion.

    Returns the first probe pair the lower rung splits and the higher rung
    conflates.  ``witnessed`` false means the family claims a rung fails to
    refine another and the probe set does not show it -- which is a defect of
    the *declaration*, not of the layer.
    """
    probes = list(family.probes())
    names = _names(family, probes)
    low = _rung(family, lower)
    high = _rung(family, higher)
    for i in range(len(probes)):
        for j in range(i + 1, len(probes)):
            if high.same(probes[i], probes[j]) and not low.same(probes[i],
                                                                probes[j]):
                return {"family": family.key, "lower": lower,
                        "higher": higher, "witnessed": True,
                        "witness": (names[i], names[j])}
    return {"family": family.key, "lower": lower, "higher": higher,
            "witnessed": False, "witness": None}


def conflations(family: Family, rung: str) -> Dict[str, object]:
    """The probe pairs a rung cannot tell apart at all.

    Reported separately from a refinement violation and never counted as one:
    a conflation is the rung's resolution, and the remedy is a joint reading,
    not a refinement.
    """
    probes = list(family.probes())
    names = _names(family, probes)
    reading = _rung(family, rung)
    pairs: List[Dict[str, object]] = []
    for i in range(len(probes)):
        for j in range(i + 1, len(probes)):
            if reading.same(probes[i], probes[j]):
                pairs.append({"left": names[i], "right": names[j]})
    return {"family": family.key, "rung": rung, "pairs": tuple(pairs),
            "count": len(pairs),
            "remedy": ("a joint reading with a rung that sees something else; "
                       "refining this rung does not repair it")}


def check_family(family: Family) -> Dict[str, object]:
    """Every declared edge, every declared non-edge, and every rung's losses."""
    edges = tuple(check_edge(family, lower, higher)
                  for lower, higher in family.edges)
    non_edges = tuple(check_non_edge(family, lower, higher)
                      for lower, higher in family.non_edges)
    losses = tuple(conflations(family, rung.name) for rung in family.rungs)
    defects: List[str] = []
    for row in edges:
        if not row["refines"]:
            defects.append(
                f"{family.key}: {row['higher']} does not refine "
                f"{row['lower']} ({len(row['violations'])} violating pairs)")
        if row["metrics_comparable"] and row["metric_dominates"] is False:
            defects.append(
                f"{family.key}: {row['higher']}'s metric does not dominate "
                f"{row['lower']}'s")
    for row in non_edges:
        if not row["witnessed"]:
            defects.append(
                f"{family.key}: the declared non-edge {row['lower']} -> "
                f"{row['higher']} has no witness in the probe set")
    return {
        "key": family.key, "title": family.title, "shipped": family.shipped,
        "rungs": tuple(rung.name for rung in family.rungs),
        "probes": len(list(family.probes())),
        "edges": edges, "non_edges": non_edges, "conflations": losses,
        "defects": tuple(defects),
        "passes": not defects,
        "note": family.note,
    }


# ═════════════════════════════════════════════════════════════════════════
# 3.  THE DECLARED FAMILIES
# ═════════════════════════════════════════════════════════════════════════

def _dimension_probes() -> Sequence[object]:
    from . import information_loss as IL
    return IL.sample_carriers()


def _dimension_names() -> Sequence[str]:
    return ("the vacuum", "a half-unit on coordinate 0",
            "a unit on coordinate 0", "a two-unit on coordinate 0",
            "a unit on coordinate 10", "a 2A axis carrier",
            "the same axis, shifted by 1/7")


def _layer_rung(layer_name: str, title: str) -> Rung:
    from . import dimension_layers as DL
    from . import information_loss as IL
    layer = (DL.LAYER_INTEGER_RAW if layer_name == "integer_raw"
             else DL.LAYER_BY_NAME[layer_name])
    return Rung(name=layer_name, title=title,
                same=lambda a, b, _layer=layer: IL.indistinguishable(_layer,
                                                                     a, b))


def _dimension_family() -> Family:
    return Family(
        key="dimension-stack",
        title="the five-layer perspective stack the runtime reads carriers at",
        rungs=(
            _layer_rung("substrate", "24 parity bits"),
            _layer_rung("integer", "the SI7 exponents, carried with the bits"),
            _layer_rung("rational", "the exact carrier"),
            _layer_rung("griess", "the algebra, carried with the carrier"),
            _layer_rung("universal", "the whole reading"),
        ),
        probes=_dimension_probes,
        probe_names=_dimension_names,
        edges=(("substrate", "integer"), ("integer", "rational"),
               ("rational", "griess"), ("griess", "universal")),
        note=("The step that had to be repaired is the first one: the shipped "
              "integer layer carries the substrate's bits alongside the "
              "exponents precisely because reading the exponents alone does "
              "not refine the substrate."),
    )


def _rejected_family() -> Family:
    return Family(
        key="dimension-stack-rejected",
        title="the rejected integer reading, kept so its cost stays priced",
        rungs=(
            _layer_rung("substrate", "24 parity bits"),
            _layer_rung("integer_raw", "the SI7 exponents alone"),
        ),
        probes=_dimension_probes,
        probe_names=_dimension_names,
        edges=(),
        non_edges=(("substrate", "integer_raw"),),
        shipped=False,
        note=("This family is registered with no edges and one declared "
              "non-edge: the reading is not cumulative over the substrate, "
              "the check finds the witness, and the family does not ship.  It "
              "is the defect the first run of this check caught, kept on the "
              "record rather than deleted."),
    )


#: The declared probe records of the deep-hole ladder.  Each is a short
#: emission record -- ``(point, exact squared distance)`` pairs -- chosen so
#: that the ladder's declared shape is exercised: two of them share a distance
#: measure while differing in their arrivals, which is what makes the exact
#: rational rung a non-edge over the share rung rather than an edge.
def _point(index: int) -> Tuple[int, ...]:
    return tuple([index] + [0] * 23)


def _deep_hole_probes() -> Sequence[object]:
    four = Fraction(4)
    six = Fraction(6)
    return (
        # two arrivals in shares 2:1, no stray
        ((_point(1), four), (_point(1), four), (_point(2), four)),
        # three arrivals in equal shares, no stray: same measure as the first,
        # a different share profile
        ((_point(1), four), (_point(2), four), (_point(3), four)),
        # the 2:1 shares again, with one stray added
        ((_point(1), four), (_point(1), four), (_point(2), four),
         (_point(3), six)),
        # equal shares with one stray
        ((_point(1), four), (_point(2), four), (_point(3), four),
         (_point(4), six)),
        # a single arrival
        ((_point(1), four),),
    )


def _deep_hole_names() -> Sequence[str]:
    return ("shares 2:1, no stray", "shares 1:1:1, no stray",
            "shares 2:1 with a stray", "shares 1:1:1 with a stray",
            "one arrival")


def _ladder_rung(layer: str, title: str) -> Rung:
    from . import deep_hole_escalation as de

    def metric(a: object, b: object, _layer: str = layer) -> Fraction:
        return de.layer_distance(de.layer_profile(a, _layer),      # type: ignore[arg-type]
                                 de.layer_profile(b, _layer), _layer)

    return Rung(name=layer, title=title,
                same=lambda a, b: metric(a, b) == 0, metric=metric)


def _deep_hole_family() -> Family:
    return Family(
        key="deep-hole-ladder",
        title="the four readings of the deep-hole escalation ladder",
        rungs=(
            _ladder_rung("shares", "L1 - the arrival shares"),
            _ladder_rung("widened", "L2 - the shares and the stray spectrum"),
            _ladder_rung("rational", "L3 - the exact measure of distances"),
            _ladder_rung("joint", "L4 - L2 and L3 together"),
        ),
        probes=_deep_hole_probes,
        probe_names=_deep_hole_names,
        edges=(("shares", "widened"), ("widened", "joint"),
               ("rational", "joint")),
        non_edges=(("shares", "rational"),),
        note=("The ladder is a graph and not a chain, and this is where the "
              "two failure modes part company: L3 is not above L1, because a "
              "reading of distances alone cannot see which vertex a start "
              "arrived at.  The declared non-edge carries the witness for "
              "that -- two records with the same distance measure and "
              "different arrival shares -- and it is the same phenomenon that "
              "makes L3 conflate A_1^24 with A_2^12 in the measured round.  "
              "The remedy there is the join L4, not a refinement of L3."),
    )


def _families() -> Tuple[Family, ...]:
    return (_dimension_family(), _rejected_family(), _deep_hole_family())


#: Built on first use so that importing this module does not import the whole
#: layer stack; the tuple itself is fixed and declared.
FAMILIES: Tuple[Family, ...] = ()


def families() -> Tuple[Family, ...]:
    """Every declared layer family, built once."""
    global FAMILIES
    if not FAMILIES:
        FAMILIES = _families()
    return FAMILIES


def family_by_key(key: str) -> Family:
    """One family by its key."""
    for family in families():
        if family.key == key:
            return family
    raise KeyError(f"no layer family named {key!r}")


# ═════════════════════════════════════════════════════════════════════════
# 4.  THE REPORT, AND THE RULE
# ═════════════════════════════════════════════════════════════════════════

def cumulativity_report() -> Dict[str, object]:
    """Re-run the check over every declared family.  Nothing is quoted."""
    rows = tuple(check_family(family) for family in families())
    shipped = tuple(row for row in rows if row["shipped"])
    defects = tuple(defect for row in shipped
                    for defect in row["defects"])       # type: ignore[union-attr]
    return {
        "families": rows,
        "count": len(rows),
        "shipped": len(shipped),
        "edges_checked": sum(len(row["edges"]) for row in rows),  # type: ignore[arg-type]
        "non_edges_checked": sum(len(row["non_edges"])            # type: ignore[arg-type]
                                 for row in rows),
        "defects": defects,
        "holds": not defects,
        "rule": ("A layer family ships only if every declared refinement edge "
                 "holds on its probe set and every declared non-edge has a "
                 "witness.  A conflation is reported beside these and is not "
                 "a defect: it is the rung's resolution, and the remedy is a "
                 "joint reading rather than a refinement."),
    }


def shipped_defects() -> Tuple[str, ...]:
    """The defects of the families the system actually uses."""
    return tuple(cumulativity_report()["defects"])      # type: ignore[arg-type]


def rule_holds() -> bool:
    """Whether every shipped family passes its own check."""
    return not shipped_defects()


if __name__ == "__main__":                      # pragma: no cover
    report = cumulativity_report()
    print(f"families      {report['count']} "
          f"({report['shipped']} shipped)")
    print(f"edges         {report['edges_checked']} checked, "
          f"{report['non_edges_checked']} declared non-edges")
    for row in report["families"]:              # type: ignore[union-attr]
        state = "passes" if row["passes"] else "DEFECT"
        print(f"  {row['key']:<26} {state}")
        for defect in row["defects"]:
            print(f"    {defect}")
    print(f"rule holds    {report['holds']}")
