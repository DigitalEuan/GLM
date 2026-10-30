"""The measured result: the described shapes against the shipped parser.

:func:`language_report` runs the whole generic path over every description in
:mod:`glm_universal.language.descriptions` and reports what it finds: how many
surface forms the shapes recognise and how many decisions about English that
took; whether the openings are disjoint, so that the order the shapes are
tried in cannot matter; whether a question written from a shape matches back
to the slots it was written from; whether every boundary a description names
has a witness that reaches it; and -- the number the phase is about --
whether the described shapes and the hand-written parser make the same query
out of the same question, over a corpus generated from the registers rather
than written by hand.

:func:`ask` is the query surface.  It reads a question with no hand-written
phrase in the path: the shape is matched off the description, the slots
become the options, and where the described kind has an answerer that takes
those options, it is called.  A question the descriptions do not cover is
declined with the boundary named, which is a stated limit rather than a gap.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from . import build
from .descriptions import (DESCRIBED_KINDS, INFIX_KINDS, INFIX_QUESTIONS,
                          NESTED_KINDS, NESTED_QUESTIONS, QUESTIONS)
from .question import QuestionSpec

__all__ = ["ask", "shape_summary", "surface", "language_report",
           "infix_surface", "nested_surface", "described_share"]


# ===========================================================================
# 1.  THE QUERY SURFACE
# ===========================================================================

def ask(question: str,
        specs: Sequence[QuestionSpec] = QUESTIONS) -> Dict[str, Any]:
    """Read a question off the descriptions, and answer it where they decide.

    The parse is the description's; the answer, where there is one, is the
    same module the runtime calls with the same options, so this is a
    different *surface* over the same machine and not a second implementation
    of it.
    """
    outcome = build.parse(question, specs)
    if not isinstance(outcome, build.Match):
        return {"question": question, "matched": False,
                "boundary": outcome.boundary, "reason": outcome.reason,
                "kind": outcome.kind, "answered": False}
    options = build.options_of(outcome)
    row: Dict[str, Any] = {
        "question": question, "matched": True, "kind": outcome.kind,
        "options": options, "surfaces": outcome.surfaces,
        "trace": outcome.trace, "answered": False,
    }
    if outcome.kind == "derive":
        from ..recipe import ask as derive_ask
        answer = derive_ask(options["coordinate"], options["object"],
                            options["domain"] or None)
        row["answered"] = bool(answer.get("answered"))
        row["answer"] = answer
    elif outcome.kind == "measure":
        from ..reasoning import measure_view as mv
        if not options["class"]:
            row["reason"] = ("a measure word is read against a comparison "
                             "class, and none was named")
        else:
            try:
                reading = mv.read(options["subject"], options["class"])
            except (KeyError, ValueError) as exc:
                row["reason"] = str(exc)
            else:
                row["answered"] = True
                row["answer"] = reading
    else:
        row["reason"] = (f"the {outcome.kind} shape parses here; running it "
                         f"is the session's job")
    return row


# ===========================================================================
# 2.  ONE SHAPE, MEASURED
# ===========================================================================

def shape_summary(spec: QuestionSpec) -> Dict[str, Any]:
    """What one description says, and what it recognises."""
    return {
        "kind": spec.kind,
        "gloss": spec.gloss,
        "shape": spec.render(),
        "slots": tuple(slot_.name for slot_ in spec.slots),
        "roles": spec.roles(),
        "optional": tuple(slot_.name for slot_ in spec.slots
                          if slot_.optional),
        "judgements": spec.judgements,
        "phrasings": spec.phrasing_count(),
        "openings": len(spec.opening.alternatives),
        "refusals": tuple(refusal.name for refusal in spec.refusals),
        "why": tuple(piece.why for piece in spec.phrasings),
    }


def surface(specs: Sequence[QuestionSpec] = QUESTIONS) -> Dict[str, Any]:
    """The whole described surface, before any question is matched."""
    shapes = tuple(shape_summary(spec) for spec in specs)
    return {
        "kinds": tuple(spec.kind for spec in specs),
        "shapes": shapes,
        "judgements": sum(shape["judgements"] for shape in shapes),
        "phrasings": sum(shape["phrasings"] for shape in shapes),
        "slots": sum(len(shape["slots"]) for shape in shapes),
        "roles": tuple(sorted({role for shape in shapes
                               for role in shape["roles"]})),
        "refusals": sum(len(shape["refusals"]) for shape in shapes),
        "preamble": tuple(sorted({
            spec.preamble.render() for spec in specs
            if spec.preamble is not None})),
        "preamble_forms": sum(len(spec.preamble.forms())
                              for spec in specs
                              if spec.preamble is not None),
    }


def infix_shape_summary(spec: Any) -> Dict[str, Any]:
    """What one infix description says."""
    return {
        "kind": spec.kind,
        "gloss": spec.gloss,
        "shape": spec.render(),
        "operands": tuple(operand.name for operand in spec.operands),
        "carried": spec.carried,
        "roles": spec.roles(),
        "judgements": spec.judgements,
        "phrasings": spec.phrasing_count(),
        "meanings": dict(spec.meanings),
        "refusals": tuple(refusal.name for refusal in spec.refusals),
        "why": tuple(piece.why for piece in spec.phrasings),
    }


def infix_surface(specs: Sequence[Any] = INFIX_QUESTIONS) -> Dict[str, Any]:
    """The whole described *infix* surface, before any question is matched."""
    shapes = tuple(infix_shape_summary(spec) for spec in specs)
    return {
        "kinds": tuple(spec.kind for spec in specs),
        "shapes": shapes,
        "judgements": sum(shape["judgements"] for shape in shapes),
        "phrasings": sum(shape["phrasings"] for shape in shapes),
        "operands": sum(len(shape["operands"]) for shape in shapes),
        "roles": tuple(sorted({role for shape in shapes
                               for role in shape["roles"]})),
        "refusals": sum(len(shape["refusals"]) for shape in shapes),
    }


def nested_shape_summary(spec: Any) -> Dict[str, Any]:
    """What one nested description says."""
    return {
        "kind": spec.kind,
        "gloss": spec.gloss,
        "shape": spec.render(),
        "nests": spec.side.shape.kind,
        "options": spec.options,
        "judgements": spec.judgements,
        "separators": spec.separators,
        "refusals": tuple(refusal.name for refusal in spec.refusals),
        "why": (spec.operator.why, spec.side.why),
    }


def nested_surface(specs: Sequence[Any] = NESTED_QUESTIONS) -> Dict[str, Any]:
    """The whole described *nested* surface.

    A nested shape holds no slots of its own: what it describes is an
    operator and which described shape each of its two sides must match, so
    what is counted here is the reuse -- which shape is nested, and how many
    options come back out of it.
    """
    shapes = tuple(nested_shape_summary(spec) for spec in specs)
    return {
        "kinds": tuple(spec.kind for spec in specs),
        "shapes": shapes,
        "judgements": sum(shape["judgements"] for shape in shapes),
        "nests": tuple(sorted({shape["nests"] for shape in shapes})),
        "options": sum(len(shape["options"]) for shape in shapes),
        "refusals": sum(len(shape["refusals"]) for shape in shapes),
    }


# ===========================================================================
# 3.  THE WHOLE THING
# ===========================================================================

def language_report(specs: Sequence[QuestionSpec] = QUESTIONS
                    ) -> Dict[str, Any]:
    """Every described shape, matched, measured against the shipped parser."""
    described = surface(specs)
    disjoint = build.openings_disjoint(specs)
    trips = build.round_trip(specs)
    refusals = build.refusal_audit(specs)
    agreed = build.agreement(specs)
    narrowed = build.narrowing(specs)
    infix = infix_surface()
    infix_agreed = build.infix_agreement()
    nested = nested_surface()
    nested_agreed = build.nested_agreement()
    widened = build.widening()
    covered = build.coverage()

    examples: List[Dict[str, Any]] = [
        ask("derive span_ratio of tea", specs),
        ask("what derives numerator of perfect_fifth in harmonics", specs),
        ask("how much hot in tea", specs),
        ask("task grid", specs),
        ask("report language", specs),
        ask("derive span_ratio", specs),
    ]

    exact = (disjoint["disjoint"] and trips["exact"] and refusals["exact"]
             and agreed["exact"] and narrowed["exact"]
             and infix_agreed["exact"] and nested_agreed["exact"]
             and widened["holds"])
    verdict = {
        "kinds_described": len(described["shapes"]),
        "kinds_read_off": covered["described"],
        "kinds_infix": len(infix["shapes"]),
        "kinds_nested": len(nested["shapes"]),
        "kinds_covered": covered["described"],
        "kinds_total": covered["kinds"],
        "shape_families": covered["families"],
        "judgements": described["judgements"],
        "infix_judgements": infix["judgements"],
        "nested_judgements": nested["judgements"],
        "phrasings": described["phrasings"],
        "corpus": agreed["corpus"],
        "agreed": agreed["agreed"],
        "declined": len(agreed["declined"]),
        "disagreed": len(agreed["disagreed"]),
        "outside": agreed["outside"],
        "false_positives": len(agreed["false_positives"]),
        "round_trips": trips["checked"],
        "openings_disjoint": disjoint["disjoint"],
        "narrowing_witnesses": len(narrowed["witnesses"]),
        "infix_corpus": infix_agreed["corpus"],
        "infix_agreed": infix_agreed["agreed"],
        "infix_disagreed": len(infix_agreed["disagreed"]),
        "infix_outside": infix_agreed["outside"],
        "infix_false_positives": len(infix_agreed["false_positives"]),
        "nested_corpus": nested_agreed["corpus"],
        "nested_agreed": nested_agreed["agreed"],
        "nested_widened": len(nested_agreed["widened"]),
        "nested_disagreed": len(nested_agreed["disagreed"]),
        "nested_outside": nested_agreed["outside"],
        "nested_false_positives": len(nested_agreed["false_positives"]),
        "widenings": widened["witnesses"],
        "widening_holds": widened["holds"],
        "undescribed_parts": len(build.UNDESCRIBED_PARTS),
        "verdict": "described" if exact else "not described",
        "because": (
            "every kind any of the three families describes is read off "
            "its description by the runtime itself, with no branch left "
            "for any of them, and over the generated corpora that reading "
            "is the one the deleted branches gave; every question written "
            "from a shape matches back to the slots it was written from, "
            "every named boundary has a witness that reaches it, no "
            "question of an undescribed kind is matched, and the one place "
            "a description reads more than its branch did is declared, "
            "measured and accounted for question by question"
            if exact else
            "the described shapes and the deleted branches did not agree "
            "on every question of the generated corpora"),
    }
    return {
        "surface": described,
        "disjoint": disjoint,
        "round_trip": trips,
        "refusals": refusals,
        "agreement": agreed,
        "narrowing": narrowed,
        "infix": infix,
        "infix_agreement": infix_agreed,
        "nested": nested,
        "nested_agreement": nested_agreed,
        "widening": widened,
        "coverage": covered,
        "undescribed_parts": build.undescribed_parts(),
        "examples": tuple(examples),
        "verdict": verdict,
    }


def _runtime_kinds() -> Sequence[str]:
    from ..runtime.parser import KINDS
    return tuple(kind for kind in KINDS if kind != "unknown")


def described_share() -> Dict[str, Any]:
    """Which of the runtime's kinds are described, and which are not.

    Four answers, not one: which kinds each of the three shape families
    describes -- ``compare`` is in two of them, because its list form and
    its relational form are different shapes asking the same question --
    and the rest, which are still a branch apiece.  Every described kind is
    now also *read off* its description by the runtime.
    """
    kinds = _runtime_kinds()
    covered = set(DESCRIBED_KINDS) | set(INFIX_KINDS) | set(NESTED_KINDS)
    return {
        "described": tuple(kind for kind in kinds if kind in DESCRIBED_KINDS),
        "infix": tuple(kind for kind in kinds if kind in INFIX_KINDS),
        "nested": tuple(kind for kind in kinds if kind in NESTED_KINDS),
        "covered": tuple(kind for kind in kinds if kind in covered),
        "undescribed": tuple(kind for kind in kinds if kind not in covered),
        "kinds": len(kinds),
    }
