"""Auditing the inherited concept graph, and saying exactly what it contains.

The question
------------
The repository's persistent state -- ``arc_agi_17/results/glm_state.json``,
grown over 217 pipeline runs -- holds 4,282 concepts and 4,015 CRG edges.  Is
any of it information *about the subjects*?

This module answers by measurement, not by opinion.  Every number below is
recomputed from the shipped state file and the frozen registers each time the
report runs; nothing is quoted from a previous run.

The four measurements
---------------------
1. :func:`concept_grounding` -- how many of the 4,282 concept names denote
   something determinate, by sense.  A name that denotes nothing cannot have
   a carrier that measures anything, whatever the carrier looks like.
2. :func:`edge_grounding` -- every one of the 4,015 edges, classified: does
   its label state a relation about the subjects at all; are both endpoints
   grounded; and, when they are, is the relation re-derivable from the two
   meanings?
3. :func:`carrier_information` -- the decisive one.  Over the pairs of
   grounded concepts, does the stored carrier distance know anything about
   whether the two subjects are related?  The comparison is exact: mean
   Hamming distance between semantically related pairs against unrelated
   pairs, as rationals, plus the 2x2 table of CRG adjacency against semantic
   relatedness.
4. :func:`notational_variants` -- the groups of stored names that denote the
   *same* meaning, with the Hamming distance the stored carriers put between
   them.  A carrier derived from spelling separates synonyms; a carrier
   derived from meaning cannot.  This is the empirical face of the theorem
   ``GLM.Semantics.spelling_not_semantic``.

What follows from it
--------------------
:func:`purge_plan` turns the classification into an action: which edges to
keep, which to dump, and why -- each with its reason recorded, so nothing
disappears silently.  :func:`audit_report` runs the lot and sets it beside
the grounded graph :mod:`.graph` builds from the registers, which is what the
purged edges are being replaced *by*.
"""

from __future__ import annotations

from fractions import Fraction
from functools import lru_cache
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from ..derived import memo
from ..migration.state import load_state
from . import relations as rel
from .graph import build_graph, graph_report
from .meaning import Meaning
from .reference import resolve

__all__ = [
    "PIPELINE_LABELS", "PROXIMITY_LABELS",
    "ANSWERING_MODULES", "EVIDENCE_ONLY_SUBJECTS",
    "legacy_concepts", "legacy_edges",
    "concept_grounding", "edge_grounding", "carrier_information",
    "notational_variants", "purge_plan", "retention_decision",
    "audit_report",
]

#: Labels that record something about the *pipeline*, not about the subjects:
#: which run touched a concept, which solve happened to succeed.  Whatever
#: their value as provenance, they state no relation between two subjects.
PIPELINE_LABELS = ("learned_success", "glm_learned", "run", "session")

#: Labels attached by carrier proximity rather than by any claim.  The
#: generator computed the Hamming distance between two SHA-256-derived
#: carriers and added an edge when it fell below a radius; the label is a
#: constant, so the edge asserts nothing that could be true or false of the
#: two subjects.
PROXIMITY_LABELS = ("auto_proposed",)


# ===========================================================================
# 1.  THE INHERITED STATE
# ===========================================================================

@lru_cache(maxsize=1)
def _state() -> Optional[Mapping[str, object]]:
    return load_state()


def legacy_concepts() -> Dict[str, Tuple[int, ...]]:
    """``name -> 24-bit stored vector`` for every inherited concept."""
    state = _state()
    if state is None:
        return {}
    concepts = state.get("concepts", {})
    if not isinstance(concepts, dict):
        raise ValueError("audit: 'concepts' is not an object")
    out: Dict[str, Tuple[int, ...]] = {}
    for name, record in concepts.items():
        vector = record.get("vector") if isinstance(record, dict) else None
        if isinstance(vector, list) and len(vector) == 24:
            out[str(name)] = tuple(int(bit) for bit in vector)
    return out


def legacy_edges() -> Tuple[Tuple[str, str, str], ...]:
    """``(src, label, dst)`` for every inherited CRG edge, in stored order."""
    state = _state()
    if state is None:
        return ()
    edges = state.get("crg_edges", [])
    if not isinstance(edges, list):
        raise ValueError("audit: 'crg_edges' is not a list")
    return tuple((str(e["src"]), str(e["label"]), str(e["dst"]))
                 for e in edges if isinstance(e, dict))


def _hamming(a: Sequence[int], b: Sequence[int]) -> int:
    return sum(1 for x, y in zip(a, b) if x != y)


@lru_cache(maxsize=1)
def _grounded_concepts() -> Dict[str, Meaning]:
    """The inherited names that denote something, and what they denote."""
    out: Dict[str, Meaning] = {}
    for name in sorted(legacy_concepts()):
        answer = resolve(name)
        if answer.meaning is not None:
            out[name] = answer.meaning
    return out


# ===========================================================================
# 2.  MEASUREMENT 1 -- THE CONCEPTS
# ===========================================================================

def concept_grounding() -> Dict[str, object]:
    """How much of the inherited concept mass denotes anything determinate."""
    concepts = legacy_concepts()
    by_sense: Dict[str, int] = {}
    refusal_reasons: Dict[str, int] = {}
    grounded: List[str] = []
    for name in sorted(concepts):
        answer = resolve(name)
        if answer.meaning is not None:
            grounded.append(name)
            by_sense[answer.sense] = by_sense.get(answer.sense, 0) + 1
        else:
            head = answer.reason.split(":")[0]
            refusal_reasons[head] = refusal_reasons.get(head, 0) + 1
    return {
        "concepts": len(concepts),
        "grounded": len(grounded),
        "ungrounded": len(concepts) - len(grounded),
        "grounded_fraction": (f"{len(grounded)}/{len(concepts)}"
                              if concepts else "0/0"),
        "by_sense": dict(sorted(by_sense.items())),
        "refusal_reasons": dict(sorted(refusal_reasons.items())),
        "grounded_names": tuple(grounded),
    }


# ===========================================================================
# 3.  MEASUREMENT 2 -- THE EDGES
# ===========================================================================

def edge_grounding() -> Dict[str, object]:
    """Every inherited edge, classified by what it states and what checks out.

    The classes are exclusive and exhaustive:

    ``proximity_artefact``
        the label is a carrier-proximity marker: no relation is stated
    ``about_the_pipeline``
        the label records a run, not a relation between the subjects
    ``endpoint_ungrounded``
        a relation is stated, but at least one endpoint denotes nothing, so
        there is nothing for it to be a relation between
    ``not_derivable``
        both endpoints denote something and no relation between those two
        meanings can be derived -- the edge may still be true, but the
        repository cannot check it
    ``derivable``
        both endpoints denote something and a relation between the two
        meanings is derivable, with a witness
    """
    edges = legacy_edges()
    grounded = _grounded_concepts()
    classes: Dict[str, int] = {}
    by_label: Dict[str, Dict[str, int]] = {}
    derivable: List[Dict[str, object]] = []
    for src, label, dst in edges:
        if label in PROXIMITY_LABELS:
            verdict = "proximity_artefact"
        elif label in PIPELINE_LABELS:
            verdict = "about_the_pipeline"
        elif src not in grounded or dst not in grounded:
            verdict = "endpoint_ungrounded"
        else:
            claims = rel.derive(grounded[src], grounded[dst])
            claims += rel.derive(grounded[dst], grounded[src])
            if claims:
                verdict = "derivable"
                derivable.append({
                    "src": src, "label": label, "dst": dst,
                    "derived": [c.relation for c in claims],
                    "witness": claims[0].witness,
                })
            else:
                verdict = "not_derivable"
        classes[verdict] = classes.get(verdict, 0) + 1
        by_label.setdefault(label, {})
        by_label[label][verdict] = by_label[label].get(verdict, 0) + 1
    return {
        "edges": len(edges),
        "classes": dict(sorted(classes.items())),
        "distinct_labels": len(by_label),
        "by_label": {label: dict(sorted(counts.items()))
                     for label, counts in sorted(by_label.items())},
        "derivable_edges": tuple(derivable),
    }


# ===========================================================================
# 4.  MEASUREMENT 3 -- DOES THE STORED CARRIER KNOW ANYTHING?
# ===========================================================================

def _mean(values: Sequence[int]) -> Optional[Fraction]:
    if not values:
        return None
    return Fraction(sum(values), len(values))


def carrier_information() -> Dict[str, object]:
    """Whether stored carrier distance tracks semantic relatedness at all.

    Over every pair of inherited concepts that both denote something, the
    pair is *related* when some relation between the two meanings is
    derivable.  If the stored carriers measured the subjects, related pairs
    would sit closer than unrelated ones.  The two mean Hamming distances are
    computed exactly, as rationals, and reported side by side with the 2x2
    table of CRG adjacency against semantic relatedness.

    The stored carriers are 24-bit words, so a Hamming distance of 12 is what
    two independent random words average.
    """
    vectors = legacy_concepts()
    grounded = _grounded_concepts()
    names = tuple(sorted(grounded))
    adjacency = set()
    for src, label, dst in legacy_edges():
        if label in PIPELINE_LABELS:
            continue
        adjacency.add((src, dst))
        adjacency.add((dst, src))
    related_d: List[int] = []
    unrelated_d: List[int] = []
    table = {"related_and_adjacent": 0, "related_not_adjacent": 0,
             "adjacent_not_related": 0, "neither": 0}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            claims = rel.derive(grounded[a], grounded[b])
            claims += rel.derive(grounded[b], grounded[a])
            related = bool(claims)
            distance = _hamming(vectors[a], vectors[b])
            (related_d if related else unrelated_d).append(distance)
            adjacent = (a, b) in adjacency
            if related and adjacent:
                table["related_and_adjacent"] += 1
            elif related:
                table["related_not_adjacent"] += 1
            elif adjacent:
                table["adjacent_not_related"] += 1
            else:
                table["neither"] += 1
    mean_related = _mean(related_d)
    mean_unrelated = _mean(unrelated_d)
    gap = (mean_related - mean_unrelated
           if mean_related is not None and mean_unrelated is not None
           else None)
    return {
        "grounded_concepts": len(names),
        "pairs": len(related_d) + len(unrelated_d),
        "semantically_related_pairs": len(related_d),
        "unrelated_pairs": len(unrelated_d),
        "mean_hamming_related": (str(mean_related) if mean_related is not None
                                 else None),
        "mean_hamming_unrelated": (str(mean_unrelated)
                                   if mean_unrelated is not None else None),
        "mean_hamming_gap": str(gap) if gap is not None else None,
        "random_word_expectation": "12",
        "contingency": table,
        "reading": (
            "a carrier that measured the subjects would put related pairs "
            "closer than unrelated ones; the gap here is the whole of the "
            "semantic signal the stored carriers carry"),
    }


# ===========================================================================
# 5.  MEASUREMENT 4 -- SYNONYMS UNDER A SPELLING-DERIVED CARRIER
# ===========================================================================

def notational_variants() -> Dict[str, object]:
    """Stored names that denote the same thing, and how far apart they sit.

    Two notations for one subject must land on one carrier if the carrier is
    a function of the subject.  Under the inherited encoding they land as far
    apart as unrelated words, which is what it means for the encoding to be a
    function of the spelling instead.
    """
    vectors = legacy_concepts()
    grounded = _grounded_concepts()
    groups: Dict[Meaning, List[str]] = {}
    for name, meaning in grounded.items():
        groups.setdefault(meaning, []).append(name)
    reported: List[Dict[str, object]] = []
    distances: List[int] = []
    for meaning, names in sorted(groups.items(),
                                 key=lambda kv: sorted(kv[1])):
        if len(names) < 2:
            continue
        names = sorted(names)
        pairs = [(a, b, _hamming(vectors[a], vectors[b]))
                 for i, a in enumerate(names) for b in names[i + 1:]]
        distances.extend(d for _, _, d in pairs)
        reported.append({
            "meaning": meaning.describe(),
            "notations": names,
            "legacy_hamming": [{"a": a, "b": b, "distance": d}
                               for a, b, d in pairs],
        })
    mean = _mean(distances)
    return {
        "synonym_groups": len(reported),
        "synonym_pairs": len(distances),
        "mean_legacy_hamming_between_synonyms": (str(mean) if mean is not None
                                                 else None),
        "semantic_hamming_between_synonyms": 0,
        "groups": tuple(reported),
        "reading": (
            "in the meaning space every one of these pairs is at distance 0 "
            "by construction: they are one node with several notations"),
    }


# ===========================================================================
# 6.  WHAT TO DUMP
# ===========================================================================

def purge_plan() -> Dict[str, object]:
    """Which inherited edges survive an audit, and why the rest do not.

    Survival requires all three: the label states a relation about the
    subjects; both endpoints denote something determinate; and a relation
    between those two meanings is re-derivable now.  Everything else is
    listed with its reason -- dumped, not deleted quietly.
    """
    classification = edge_grounding()
    classes = classification["classes"]         # type: ignore[index]
    assert isinstance(classes, dict)
    keep = classes.get("derivable", 0)
    total = classification["edges"]             # type: ignore[index]
    assert isinstance(total, int)
    dumped = {name: count for name, count in sorted(classes.items())
              if name != "derivable"}
    return {
        "edges": total,
        "retained": keep,
        "dumped": total - keep,
        "dumped_by_reason": dumped,
        "retained_edges": classification["derivable_edges"],
        "reasons": {
            "proximity_artefact":
                "the label is a carrier-proximity marker, so the edge states "
                "no relation that could be true or false of the subjects",
            "about_the_pipeline":
                "the label records a pipeline event, not a relation between "
                "the subjects",
            "endpoint_ungrounded":
                "at least one endpoint denotes nothing determinate, so there "
                "is nothing for the relation to hold between",
            "not_derivable":
                "both endpoints denote something, but no relation between "
                "those meanings can be derived and checked here",
        },
    }


# ===========================================================================
# 6b.  WHAT WAS DECIDED ABOUT THE INHERITED GRAPH
# ===========================================================================
#
# The audit left one question open: refine the inherited graph until it earns
# its place, or drop it.  :func:`retention_decision` records the answer, and
# recomputes the evidence for it rather than restating a remembered figure.
#
# Neither branch was taken whole.  Refining it is not possible in the sense
# that matters: an edge earns its place by being re-derivable from what its
# endpoints mean, and 4,013 of the 4,015 cannot be, not because the
# derivation is missing but because the endpoints denote nothing to derive
# from.  Deleting it is not possible either without deleting the evidence for
# that very claim.  So it is *demoted*: kept as an input the audit reads, and
# removed from the answering path entirely.
# ---------------------------------------------------------------------------

#: The modules that answer a question about meaning.  None of them may read
#: the inherited state: that is what "demoted to evidence" means, and
#: ``tests/test_inherited_graph.py`` checks it by walking their imports.
ANSWERING_MODULES: Tuple[str, ...] = (
    "glm_universal.semantics.meaning",
    "glm_universal.semantics.reference",
    "glm_universal.semantics.relations",
    "glm_universal.semantics.graph",
    "glm_universal.reasoning.analogy",
    "glm_universal.reasoning.analogy_models",
    "glm_universal.data_objects.semantic_lexicon",
)

#: The report subjects that are *allowed* to read the inherited state,
#: because each is a report about that file rather than an answer drawn from
#: it: what it contains, what it migrates to, and what the audit makes of it.
EVIDENCE_ONLY_SUBJECTS: Tuple[str, ...] = (
    "concept store", "migration", "state migration", "semantics",
)


@memo
def retention_decision() -> Dict[str, object]:
    """Keep the inherited concept graph, and on what terms -- with evidence.

    Every figure here is recomputed from the state file and the registers.
    The decision itself is a sentence, but the grounds for it are numbers,
    and if the numbers ever moved the sentence would have to be rewritten --
    which is why they are returned beside it.
    """
    concepts = concept_grounding()
    edges = edge_grounding()
    carriers = carrier_information()
    plan = purge_plan()
    grounded = graph_report(build_graph())
    return {
        "decision": "demoted to evidence",
        "kept": True,
        "consulted_for_answers": False,
        "grounds": {
            "concepts": concepts["concepts"],
            "concepts_grounded": concepts["grounded"],
            "edges": edges["edges"],
            "edges_derivable": plan["retained"],
            "edges_dumped": plan["dumped"],
            "mean_hamming_related": carriers["mean_hamming_related"],
            "mean_hamming_unrelated": carriers["mean_hamming_unrelated"],
            "mean_hamming_gap": carriers["mean_hamming_gap"],
            "replacement_meanings": grounded["meanings"],
            "replacement_edges": (grounded["binary_edges"]
                                  + grounded["ternary_edges"]),
        },
        "terms": (
            "the file stays in the repository and is read by nothing that "
            "answers a question: it is the input this audit measures, and "
            "the evidence for the grounded graph replacing it",
            "no module on the answering path imports it -- see "
            "ANSWERING_MODULES, which the suite checks by walking imports",
            "the report subjects that do read it are reports *about* it: "
            + ", ".join(EVIDENCE_ONLY_SUBJECTS),
        ),
        "rejected": {
            "refine": "an edge earns its place by being re-derivable from "
                      "what its endpoints mean; for all but the derivable "
                      "ones at least one endpoint denotes nothing "
                      "determinate, so there is nothing to refine towards",
            "delete": "deleting the file would delete the evidence for the "
                      "claim that it carries no information about the "
                      "subjects, and that claim is a measurement, not an "
                      "opinion",
        },
    }


# ===========================================================================
# 7.  THE WHOLE AUDIT
# ===========================================================================

@memo
def audit_report() -> Dict[str, object]:
    """Every measurement, with the replacement graph beside it."""
    concepts = concept_grounding()
    edges = edge_grounding()
    carriers = carrier_information()
    variants = notational_variants()
    plan = purge_plan()
    grounded = graph_report(build_graph())
    return {
        "state_present": bool(legacy_concepts()),
        "concept_grounding": {k: v for k, v in concepts.items()
                              if k != "grounded_names"},
        "edge_grounding": {k: v for k, v in edges.items()
                           if k != "derivable_edges"},
        "carrier_information": carriers,
        "notational_variants": {k: v for k, v in variants.items()
                                if k != "groups"},
        "purge_plan": {k: v for k, v in plan.items()
                       if k != "retained_edges"},
        "retention_decision": retention_decision()["decision"],
        "replacement": {
            "meanings": grounded["meanings"],
            "notations": grounded["notations"],
            "binary_edges": grounded["binary_edges"],
            "ternary_edges": grounded["ternary_edges"],
            "all_edges_reverified": grounded["verification"]["all_verified"],
        },
    }
