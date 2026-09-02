"""The measured result: three domains deleted and regenerated from their
descriptions, and one query surface driven off the descriptions themselves.

:func:`recipe_report` runs the whole generic path over every description in
:mod:`glm_universal.recipe.descriptions` and reports what it finds: how much of
each domain is shared primitives and how much is a judgement the domain had to
state; whether the layer chain the description declares is a refinement chain;
what each widening gains; whether the carriers the description generates are
the carriers the hand-written register ships, coordinate by coordinate; and
whether the figures the reasoning modules measure are unchanged when the
regenerated register is put in the shipped one's place.

:func:`ask` is the query surface.  It takes a coordinate and an object and
answers from whichever description derives it -- and refuses, with the reason,
where none does.  The refusal is not a gap: ``GLM.Recipe.Spec.answer_eq_none_iff``
says the answerable coordinates are exactly the described ones, so a query the
descriptions cannot decide has to be declined rather than guessed.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from . import build
from .descriptions import DESCRIPTIONS, description_by_name
from .spec import PRIMITIVES, DomainSpec

__all__ = ["ask", "domain_summary", "shared_surface", "recipe_report"]


# ===========================================================================
# 1.  THE QUERY SURFACE
# ===========================================================================

def ask(coordinate: str, object_name: str,
        domain: Optional[str] = None) -> Dict[str, Any]:
    """Answer a coordinate of one object from the descriptions, or refuse.

    With no domain named, every description that derives the coordinate is
    tried, and the one that also holds the object answers.  A coordinate no
    description derives, or an object no register holds, is refused with the
    reason -- which is the refusal boundary, not a missing feature.
    """
    specs = ([description_by_name(domain)] if domain is not None
             else list(DESCRIPTIONS))
    attempts: List[Dict[str, Any]] = []
    for spec in specs:
        result = build.answer(spec, coordinate, object_name)
        if result["answered"]:
            return result
        attempts.append(result)
    holders = tuple(spec.name for spec in specs if spec.derives(coordinate))
    if holders:
        reason = (f"the {' and '.join(holders)} description derives "
                  f"{coordinate!r}, but no register holds an object named "
                  f"{object_name!r}")
    else:
        reason = (f"no description derives {coordinate!r}; the described "
                  f"domains are "
                  f"{', '.join(spec.name for spec in DESCRIPTIONS)}")
    return {"answered": False, "coordinate": coordinate,
            "object": object_name, "reason": reason,
            "attempts": tuple(attempts)}


# ===========================================================================
# 2.  ONE DOMAIN, MEASURED
# ===========================================================================

def domain_summary(spec: DomainSpec, with_figures: bool = True,
                   exhaustive: bool = False) -> Dict[str, Any]:
    """What the generic path makes of one description."""
    audit = build.widening_audit(spec)
    refusals = build.refusal_audit(spec)
    regenerated = build.regeneration(spec, with_figures=with_figures,
                                     exhaustive=exhaustive)
    judgements = spec.judgements
    return {
        "domain": spec.name,
        "gloss": spec.gloss,
        "objects": len(spec.facts()),
        "coordinates": len(spec.coordinates),
        "derivations": len(spec.coordinates) - len(judgements),
        "judgements": judgements,
        "judgement_count": len(judgements),
        "primitives": spec.primitives_used,
        "keys": spec.keys,
        "labels": spec.labels,
        "readings": audit["readings"],
        "steps": audit["steps"],
        "chain_intact": audit["chain_intact"],
        "lossless": audit["lossless"],
        "distinct_carriers": audit["read_back"]["distinct_carriers"],
        "refused": tuple(r["coordinate"] for r in refusals["refused"]),
        "all_absent_refused": refusals["all_absent_refused"],
        "all_derived_answered": refusals["all_derived_answered"],
        "carriers_compared": regenerated["carriers_compared"],
        "carriers_identical": regenerated["carriers_identical"],
        "objects_agree": regenerated["objects_agree"],
        "figures": tuple(f["figure"] for f in regenerated["figures"]),
        "figures_unchanged": regenerated["figures_unchanged"],
        "regenerated": regenerated["regenerated"],
    }


# ===========================================================================
# 3.  WHAT THE DESCRIPTIONS SHARE
# ===========================================================================

def shared_surface() -> Dict[str, Any]:
    """How much of the three domains is one vocabulary, and how much is not."""
    used: Dict[str, List[str]] = {}
    for spec in DESCRIPTIONS:
        for primitive in spec.primitives_used:
            used.setdefault(primitive, []).append(spec.name)
    coordinates = sum(len(spec.coordinates) for spec in DESCRIPTIONS)
    judgements = sum(len(spec.judgements) for spec in DESCRIPTIONS)
    return {
        "domains": tuple(spec.name for spec in DESCRIPTIONS),
        "primitives_available": len(PRIMITIVES),
        "primitives_used": tuple(sorted(used)),
        "primitives_in_every_domain": tuple(
            sorted(p for p, names in used.items()
                   if len(names) == len(DESCRIPTIONS))),
        "primitives_in_two_or_more": tuple(
            sorted(p for p, names in used.items() if len(names) >= 2)),
        "primitives_in_one_domain": tuple(
            sorted(p for p, names in used.items() if len(names) == 1)),
        "coordinates": coordinates,
        "derivations": coordinates - judgements,
        "judgements": judgements,
        "judgements_by_domain": {spec.name: len(spec.judgements)
                                 for spec in DESCRIPTIONS},
    }


# ===========================================================================
# 4.  THE WHOLE THING
# ===========================================================================

def recipe_report(with_figures: bool = True,
                  exhaustive: bool = False) -> Dict[str, Any]:
    """Every description, run through the one generic path."""
    domains = tuple(domain_summary(spec, with_figures=with_figures,
                                   exhaustive=exhaustive)
                    for spec in DESCRIPTIONS)
    shared = shared_surface()

    answered = ask("span_ratio", "tea")
    answered_derived = ask("product_complexity", "perfect_fifth")
    refused_coordinate = ask("cents", "perfect_fifth")
    refused_object = ask("span_ratio", "cup_of_coffee")

    regenerated = tuple(d["domain"] for d in domains if d["regenerated"])
    verdict = {
        "domains_described": len(domains),
        "domains_regenerated": len(regenerated),
        "carriers_compared": sum(d["carriers_compared"] for d in domains),
        "carriers_identical": sum(d["carriers_identical"] for d in domains),
        "chains_intact": all(d["chain_intact"] for d in domains),
        "all_lossless": all(d["lossless"] for d in domains),
        "figures_unchanged": all(d["figures_unchanged"] for d in domains),
        "verdict": ("regenerated" if len(regenerated) == len(domains)
                    else "not regenerated"),
        "because": (
            "each domain's carriers, objects and measured figures came back "
            "identical from its description alone"
            if len(regenerated) == len(domains) else
            "at least one domain did not come back identical from its "
            "description"),
    }

    return {
        "domains": domains,
        "shared": shared,
        "queries": {
            "answered": answered,
            "answered_derived": answered_derived,
            "refused_coordinate": refused_coordinate,
            "refused_object": refused_object,
        },
        "verdict": verdict,
    }
