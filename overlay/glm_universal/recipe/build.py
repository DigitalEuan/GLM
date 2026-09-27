"""The one generic path: from a description to a register, a reading, an
audit, a query surface and a refusal boundary.

Nothing in this module knows what a domain is about.  Everything it produces is
a function of the :class:`~glm_universal.recipe.spec.DomainSpec` handed to it,
which is what makes the claim testable: a domain built by hand can be deleted
and regenerated from its description, and every figure measured off it stays
where it was.  :func:`regeneration` is that test, run rather than asserted.

The five steps, in the order the recipe used to be applied by hand:

1. :func:`carrier` / :func:`register` -- the carrier encoding.  One coordinate
   per description entry, every one derived from a held quantity, and 24 of
   them because the substrate's dimension is fixed by the Leech lattice.
2. :func:`view` / :func:`classes` -- the readings the description declares, as
   layers in the sense of ``RequestProject/GLM/Layers.lean``.
3. :func:`widening_audit` -- for each step of the chain: does it refine the one
   below (it always does -- ``Spec.readingOn_mono``), what does it gain
   (``Spec.boundary_readingOn_nonempty_iff``), and is the top of the chain
   lossless (``Spec.lossless_full_of_keys``)?
4. :func:`answer` -- the query surface: the value of a coordinate the
   description derives.
5. :func:`answer` again -- the refusal boundary: ``None`` with a stated reason
   for a coordinate it does not, which is ``Spec.answer_eq_none_iff``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from ..data_objects.base import N, DataObject
from .spec import DomainSpec, Facts

__all__ = [
    "carrier", "carriers", "register", "describe",
    "read_back", "read_back_audit",
    "view", "classes", "resolution", "refines", "boundary",
    "widening_audit", "answer", "refusal_audit",
    "regenerate", "regeneration", "domain_report",
]


# ===========================================================================
# 1.  THE CARRIER ENCODING
# ===========================================================================

def carrier(spec: DomainSpec, facts: Facts) -> Tuple[Any, ...]:
    """One object's carrier: every coordinate the description derives."""
    return tuple(coordinate.of(facts) for coordinate in spec.coordinates)


def carriers(spec: DomainSpec) -> Tuple[Tuple[Any, ...], ...]:
    """The whole register, generated from the description."""
    return tuple(carrier(spec, facts) for facts in spec.facts())


def register(spec: DomainSpec) -> Tuple[DataObject, ...]:
    """The register as carriers, tagged and laid out from the description."""
    out: List[DataObject] = []
    for facts in spec.facts():
        values = carrier(spec, facts)
        if len(values) != N:
            raise ValueError(f"{spec.name}: a carrier has {len(values)} "
                             f"coordinates, not {N}")
        out.append(DataObject(
            name=str(facts["name"]), domain=spec.name, carrier=values,
            attributes={k: v for k, v in facts.items() if k != "name"},
            layout=spec.layout,
            provenance={
                "source": f"the {spec.name} description",
                "derivation": "every coordinate computed from a held "
                              "quantity by the recipe's own primitives",
            }))
    return tuple(out)


def describe(spec: DomainSpec) -> Tuple[Dict[str, str], ...]:
    """The description itself, coordinate by coordinate, for a report."""
    return tuple({
        "coordinate": c.name,
        "kind": c.kind,
        "rule": c.rule.render(),
        "source": c.source,
    } for c in spec.coordinates)


# ===========================================================================
# 2.  THE READ-BACK
# ===========================================================================

def read_back(spec: DomainSpec, values: Sequence[Any],
              labels: Optional[Mapping[str, Any]] = None) -> Facts:
    """Recover an object's held facts from its carrier, through the keys.

    ``labels`` are the held facts the carrier does not hold -- the object's
    name, and any prose beside it.  They are carried rather than derived, and
    :func:`read_back_audit` reports how many there are: a register's names are
    not recoverable from its carriers, which is the missing coordinate
    ``NameCoordinate.lean`` is about.
    """
    layout = spec.layout
    keyed = {key: values[layout.index(key)] for key in spec.keys}
    return spec.rebuild(keyed, dict(labels or {}))


def read_back_audit(spec: DomainSpec) -> Dict[str, Any]:
    """Whether every object of the register is recovered from its carrier.

    A description whose keys determine its objects gives a lossless encoding
    -- ``GLM.Recipe.Spec.lossless_full_of_keys`` -- so this audit is the
    theorem's hypothesis, checked on the register the description generates.
    """
    failures: List[str] = []
    for facts in spec.facts():
        values = carrier(spec, facts)
        recovered = read_back(spec, values, _labels(spec, facts))
        if carrier(spec, recovered) != values:
            failures.append(str(facts["name"]))
    seen: Dict[Tuple[Any, ...], str] = {}
    collisions: List[Tuple[str, str]] = []
    for facts in spec.facts():
        values = carrier(spec, facts)
        if values in seen:
            collisions.append((seen[values], str(facts["name"])))
        else:
            seen[values] = str(facts["name"])
    return {
        "objects": len(spec.facts()),
        "recovered": len(spec.facts()) - len(failures),
        "failures": tuple(failures),
        "labels": spec.labels,
        "distinct_carriers": len(seen),
        "collisions": tuple(collisions),
        "lossless": not failures and not collisions,
    }


# ===========================================================================
# 3.  THE READINGS, AND THE AUDIT OVER THEM
# ===========================================================================

def view(spec: DomainSpec, reading: str, facts: Facts) -> Tuple[Any, ...]:
    """What one reading of the description sees of one object."""
    selected = _reading(spec, reading).coordinates
    return tuple(spec.coordinate(name).of(facts) for name in selected)


def _labels(spec: DomainSpec, facts: Facts) -> Dict[str, Any]:
    """The held facts a description carries beside the carrier."""
    return {label: facts[label] for label in spec.labels if label in facts}


def _reading(spec: DomainSpec, name: str):
    for reading in spec.readings:
        if reading.name == name:
            return reading
    raise KeyError(f"{spec.name}: no reading {name!r}")


def classes(spec: DomainSpec, reading: str) -> Tuple[Tuple[str, ...], ...]:
    """The register's objects grouped by what a reading can tell apart."""
    buckets: Dict[Tuple[Any, ...], List[str]] = {}
    for facts in spec.facts():
        buckets.setdefault(view(spec, reading, facts),
                           []).append(str(facts["name"]))
    return tuple(tuple(names) for names in buckets.values())


def resolution(spec: DomainSpec, reading: str) -> int:
    """How many objects a reading can tell apart."""
    return len(classes(spec, reading))


def refines(spec: DomainSpec, finer: str, coarser: str) -> bool:
    """Whether one reading distinguishes at least as much as another."""
    entries = spec.facts()
    for i, left in enumerate(entries):
        for right in entries[i + 1:]:
            same_finer = (view(spec, finer, left) == view(spec, finer, right))
            same_coarser = (view(spec, coarser, left)
                            == view(spec, coarser, right))
            if same_finer and not same_coarser:
                return False
    return True


def boundary(spec: DomainSpec, finer: str,
             coarser: str) -> Tuple[Tuple[str, str], ...]:
    """The pairs the coarser reading conflates and the finer one splits.

    This set *is* what the widening gains --
    ``GLM.Recipe.Spec.boundary_readingOn_nonempty_iff``.
    """
    entries = spec.facts()
    out: List[Tuple[str, str]] = []
    for i, left in enumerate(entries):
        for right in entries[i + 1:]:
            if (view(spec, coarser, left) == view(spec, coarser, right)
                    and view(spec, finer, left) != view(spec, finer, right)):
                out.append((str(left["name"]), str(right["name"])))
    return tuple(out)


def widening_audit(spec: DomainSpec) -> Dict[str, Any]:
    """Run the whole layer chain the description declares.

    For each step: it must refine the step below -- appending coordinates can
    only widen, which is ``Spec.readingOn_mono`` -- and what it gains is
    reported as the pairs it splits.  The top of the chain is checked for
    losslessness against the read-back.
    """
    steps: List[Dict[str, Any]] = []
    names = [reading.name for reading in spec.readings]
    for lower, higher in zip(names, names[1:]):
        gained = boundary(spec, higher, lower)
        steps.append({
            "from": lower,
            "to": higher,
            "refines": refines(spec, higher, lower),
            "classes_below": resolution(spec, lower),
            "classes_above": resolution(spec, higher),
            "gained_pairs": len(gained),
            "example": gained[0] if gained else None,
        })
    read_back = read_back_audit(spec)
    return {
        "domain": spec.name,
        "readings": tuple(names),
        "steps": tuple(steps),
        "chain_intact": all(step["refines"] for step in steps),
        "top_resolution": resolution(spec, names[-1]) if names else 0,
        "objects": len(spec.facts()),
        "lossless": read_back["lossless"],
        "read_back": read_back,
    }


# ===========================================================================
# 4.  THE QUERY SURFACE AND ITS REFUSAL BOUNDARY
# ===========================================================================

def answer(spec: DomainSpec, coordinate: str,
           object_name: str) -> Dict[str, Any]:
    """Answer a coordinate of one object, or refuse with the reason.

    Answered exactly when the description derives the coordinate; refused
    exactly when it does not, which is ``GLM.Recipe.Spec.answer_eq_none_iff``.
    A name the register does not hold is refused the same way -- the query
    surface never invents an object either.
    """
    if not spec.derives(coordinate):
        return {
            "answered": False,
            "domain": spec.name,
            "coordinate": coordinate,
            "object": object_name,
            "reason": (f"the {spec.name} description does not derive "
                       f"{coordinate!r}; it holds "
                       f"{len(spec.coordinates)} coordinates and this is not "
                       f"one of them"),
        }
    for facts in spec.facts():
        if str(facts["name"]) == object_name:
            entry = spec.coordinate(coordinate)
            return {
                "answered": True,
                "domain": spec.name,
                "coordinate": coordinate,
                "object": object_name,
                "value": entry.of(facts),
                "rule": entry.rule.render(),
                "source": entry.source,
                "kind": entry.kind,
            }
    return {
        "answered": False,
        "domain": spec.name,
        "coordinate": coordinate,
        "object": object_name,
        "reason": (f"the {spec.name} register holds no object named "
                   f"{object_name!r}"),
    }


def refusal_audit(spec: DomainSpec) -> Dict[str, Any]:
    """Exercise the refusal boundary on the coordinates the domain lacks."""
    first = str(spec.facts()[0]["name"])
    refused = []
    for name in spec.refuses:
        result = answer(spec, name, first)
        refused.append({"coordinate": name,
                        "answered": result["answered"],
                        "reason": result.get("reason", "")})
    answered = [answer(spec, name, first)["answered"] for name in spec.layout]
    return {
        "domain": spec.name,
        "object": first,
        "derived": len(spec.layout),
        "answered": sum(1 for ok in answered if ok),
        "refused": tuple(refused),
        "all_derived_answered": all(answered),
        "all_absent_refused": all(not r["answered"] for r in refused),
    }


# ===========================================================================
# 5.  REGENERATION -- THE TEST OF THE WHOLE THING
# ===========================================================================

def regenerate(spec: DomainSpec) -> Tuple[Any, ...]:
    """The domain's own objects, rebuilt from the description alone.

    Each object goes description -> carrier -> read-back -> native object, so
    nothing of the hand-written register survives the trip except the held
    facts the description says it needs.
    """
    if spec.native is None:
        raise ValueError(f"{spec.name}: the description names no native "
                         f"constructor, so it cannot be regenerated")
    out = []
    for facts in spec.facts():
        recovered = read_back(spec, carrier(spec, facts),
                              _labels(spec, facts))
        out.append(spec.native(recovered))
    return tuple(out)


def regeneration(spec: DomainSpec, with_figures: bool = True,
                 exhaustive: bool = False) -> Dict[str, Any]:
    """Delete the domain and rebuild it from its description.

    Three things are compared, in increasing strength:

    * the **carriers** the description generates against the carriers the
      hand-written module ships -- coordinate by coordinate;
    * the **objects** rebuilt through the read-back against the register's
      own, by equality of the domain's value type;
    * the **figures** the reasoning modules measure, recomputed with the
      regenerated register installed in place of the shipped one.

    A domain passes when all three agree exactly.
    """
    generated = carriers(spec)
    shipped = tuple(spec.shipped()) if spec.shipped is not None else ()
    mismatches: List[Dict[str, Any]] = []
    if shipped:
        for facts, mine, theirs in zip(spec.facts(), generated, shipped):
            if tuple(mine) != tuple(theirs):
                differing = [spec.layout[i] for i in range(len(mine))
                             if i < len(theirs) and mine[i] != theirs[i]]
                mismatches.append({"object": str(facts["name"]),
                                   "coordinates": tuple(differing)})

    rebuilt: Tuple[Any, ...] = ()
    objects_agree: Optional[bool] = None
    disagreeing: Tuple[str, ...] = ()
    if spec.native is not None:
        rebuilt = regenerate(spec)
        if spec.natives is not None:
            theirs = tuple(spec.natives())
            differing = [str(facts["name"])
                         for facts, mine, other
                         in zip(spec.facts(), rebuilt, theirs)
                         if mine != other]
            disagreeing = tuple(differing)
            objects_agree = (len(rebuilt) == len(theirs) and not differing)

    figures: List[Dict[str, Any]] = []
    declared = spec.figures + (spec.figures_exhaustive if exhaustive else ())
    if with_figures and declared and spec.install is not None:
        for name, function in declared:
            before = function()
            with spec.install(rebuilt):
                after = function()
            figures.append({"figure": name, "unchanged": before == after})

    return {
        "domain": spec.name,
        "objects": len(generated),
        "coordinates": len(spec.layout),
        "carriers_compared": len(shipped),
        "carriers_identical": len(shipped) - len(mismatches) if shipped else 0,
        "mismatches": tuple(mismatches),
        "objects_rebuilt": len(rebuilt),
        "objects_agree": objects_agree,
        "objects_disagreeing": disagreeing,
        "figures": tuple(figures),
        "figures_unchanged": all(f["unchanged"] for f in figures),
        "regenerated": (not mismatches
                        and (objects_agree is not False)
                        and all(f["unchanged"] for f in figures)),
    }


def domain_report(spec: DomainSpec, with_figures: bool = True,
                  exhaustive: bool = False) -> Dict[str, Any]:
    """Everything the generic path produces for one description."""
    return {
        "domain": spec.name,
        "gloss": spec.gloss,
        "coordinates": len(spec.coordinates),
        "judgements": spec.judgements,
        "primitives": spec.primitives_used,
        "keys": spec.keys,
        "objects": len(spec.facts()),
        "description": describe(spec),
        "audit": widening_audit(spec),
        "refusals": refusal_audit(spec),
        "regeneration": regeneration(spec, with_figures=with_figures,
                                     exhaustive=exhaustive),
    }
