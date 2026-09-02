"""``glm_universal.runtime.reports.language``
-- the subject :mod:`glm_universal.language` computes.

The question shapes, and the parser they are measured against.

Every method here is a solver for one ``report <subject>`` query.  They are
mixed into :class:`glm_universal.runtime.session.GeometricSession`,
which is where ``self`` comes from: the loaded registers, the concept index
and the shared helpers.  Splitting them out of the session keeps each family
beside a docstring that says which sub-package computes it, and keeps the
dispatcher readable as a dispatcher.
"""
from __future__ import annotations

from ... import language as lang

from ..payload import jsonable
from ..parser import Query
from ..solution import Solution, Step


class LanguageReports:
    """The subject :mod:`glm_universal.language` computes.

    A mixin of :class:`~glm_universal.runtime.session.GeometricSession`;
    it holds no state of its own.
    """

    # -- v1.12.0: the surface language, driven off descriptions -----------

    def _report_language(self, query: Query) -> Solution:
        """Wires lang.language_report -- the question shape made an object.

        `report recipe` made a *domain* declarative.  This subject does the
        same for the *question*: seven of the runtime's query kinds are
        written down as shapes -- an opening, named slots or operands, the
        words that separate them, and the boundaries they refuse at -- and
        three generic matchers read them, one per shape family.  What is
        reported is the comparison against the hand-written branches, now
        all deleted and frozen, question by question, over corpora
        generated from the registers rather than written by hand.
        """
        report = lang.language_report()
        described = report["surface"]
        agreed = report["agreement"]
        trips = report["round_trip"]
        refusals = report["refusals"]
        disjoint = report["disjoint"]
        narrowing = report["narrowing"]
        infix = report["infix"]
        infix_agreed = report["infix_agreement"]
        nested = report["nested"]
        nested_agreed = report["nested_agreement"]
        widening = report["widening"]
        coverage = report["coverage"]
        parts = report["undescribed_parts"]
        verdict = report["verdict"]

        steps = [
            Step("the question, written down",
                 f"A question shape is an opening, named slots, and the "
                 f"words that separate them.  Four of the runtime's query "
                 f"kinds are written that way -- "
                 f"{', '.join(described['kinds'])} -- and the roles a slot "
                 f"can carry are what let one matcher serve all of them: "
                 f"{', '.join(described['roles'])}.  What a question opens "
                 f"with before the opening -- the courtesies and the "
                 f"interrogatives -- is described too, as an ordered "
                 f"preamble that may be skipped, so that skipping is a "
                 f"described act rather than a loop in the parser.",
                 f"{verdict['kinds_described']} of {verdict['kinds_total']} "
                 f"answerable query kinds described by slots, "
                 f"one of them holding a list, "
                 f"{described['slots']} slots, "
                 f"{described['phrasings']} surface forms, "
                 f"{described['preamble_forms']} preamble forms"),
            Step("what does not generalise is counted",
                 f"Which phrasings count as the same question is a decision "
                 f"about English, and no description can derive one.  Each "
                 f"set of alternatives therefore carries its justification "
                 f"and is counted as a judgement, exactly as a domain "
                 f"description counts the coordinates it cannot derive.",
                 f"{described['judgements']} judgements across "
                 f"{verdict['kinds_described']} slot shapes, "
                 f"{verdict['infix_judgements']} across "
                 f"{verdict['kinds_infix']} infix shapes and "
                 f"{verdict['nested_judgements']} across "
                 f"{verdict['kinds_nested']} nested shape; "
                 + "; ".join(f"{shape['kind']} {shape['judgements']}"
                             for shape in described["shapes"])),
            Step("openings decide the shape",
                 f"No opening of one shape is a prefix of an opening of "
                 f"another, so at most one shape can be entered and the "
                 f"order they are tried in cannot change the answer.  That "
                 f"is `GLM.Question.matchPieces_not_both`, and it is what "
                 f"makes the descriptions a set rather than a priority "
                 f"list.",
                 f"{disjoint['openings']} openings, "
                 f"{len(disjoint['clashes'])} clashes, disjoint "
                 f"{disjoint['disjoint']}"),
            Step("written and read back",
                 f"Every question of the corpus is written back from the "
                 f"slots it filled and matched again, and comes back to the "
                 f"same filling.  Writing and matching are inverse on the "
                 f"questions a shape can write, which is "
                 f"`GLM.Question.matchPieces_rendered`.",
                 f"{trips['checked']} round trips, "
                 f"{len(trips['broken'])} broken"),
            Step("the branches are gone",
                 f"The seven hand-written branches that used to recognise "
                 f"these kinds are no longer in the parser: it now reads "
                 f"the descriptions.  The branches are kept frozen in "
                 f"`language.legacy`, imported by the measurement and by "
                 f"nothing in the runtime, so that the comparison still has "
                 f"something to compare against.  The corpus is generated "
                 f"from the registers the questions are about -- every "
                 f"opening crossed with every separator and every admitted "
                 f"decoration -- and agreement means the same kind and the "
                 f"same options, not merely the same kind.",
                 f"{verdict['kinds_read_off']} kinds read off the "
                 f"descriptions; {agreed['agreed']}/{agreed['corpus']} "
                 f"agreed with the deleted branches, "
                 f"{len(agreed['declined'])} declined, "
                 f"{len(agreed['disagreed'])} disagreed"),
            Step("and where it refuses",
                 f"A question of a kind the descriptions do not cover must "
                 f"be declined rather than misread: the {agreed['outside']} "
                 f"evaluation questions of the other kinds were all "
                 f"declined.  Every boundary a description names has a "
                 f"witness that reaches it, so a refusal is a measured "
                 f"limit and not a claim.  The narrowing is measured the "
                 f"same way: {narrowing['witnesses'] and len(narrowing['witnesses']) or 0} "
                 f"questions carrying a word the preamble does not describe "
                 f"are declined here and misread by the branches, which "
                 f"skipped them into a slot.",
                 f"{len(agreed['false_positives'])} "
                 f"false positives on {agreed['outside']} questions; "
                 f"{len(refusals['witnesses'])} boundary witnesses, "
                 f"{len(refusals['undescribed'])} undescribed; "
                 f"{narrowing['declined']} narrowing witnesses declined, "
                 f"{narrowing['misread_by_the_parser']} misread"),
            Step("a second shape family",
                 f"Not every question is an opening and runs of words.  "
                 f"{', '.join(infix['kinds'])} are recognised by an "
                 f"operator that cuts the question in two -- `=`, `::`, "
                 f"`greater than` -- with operands that are notations "
                 f"rather than word sequences.  A second description form "
                 f"and a second matcher cover them, and two things a shape "
                 f"can hold beside its operands are described here rather "
                 f"than scanned for: a *modifier*, a word that directs how "
                 f"the operands are compared without naming one of them, "
                 f"and a *trailing option*, a value written after them that "
                 f"narrows the answer.  The runtime reads all three kinds "
                 f"off these descriptions.",
                 f"{verdict['kinds_infix']} infix kinds, "
                 f"{infix['operands']} operands, "
                 f"{infix['phrasings']} surface forms; "
                 f"{infix_agreed['agreed']}/{infix_agreed['corpus']} agreed, "
                 f"{len(infix_agreed['disagreed'])} disagreed, "
                 f"{len(infix_agreed['false_positives'])} false positives on "
                 f"{infix_agreed['outside']} questions"),
            Step("a third family, whose operands are readings",
                 f"`is cold in stellar_surface hotter than hot in tea` is "
                 f"infix too, but its operands are not text: each side has "
                 f"to be a measured use, which is the "
                 f"{', '.join(nested['nests'])} shape itself.  So the "
                 f"nested description holds an operator and *the shape its "
                 f"sides nest*, tightened -- the opening dropped, the class "
                 f"made required, both slots narrowed to a single name -- "
                 f"and the tightening is what keeps an exact-real "
                 f"comparison out of it.  The operator is open rather than "
                 f"listed: any `-er than` word, or any word inside "
                 f"`as ... as`, because which degree words mean anything is "
                 f"the register's decision and not the shape's.  Reuse is "
                 f"the point, and it has a measured price: the nested shape "
                 f"admits every separator the measure shape admits, and the "
                 f"branch it replaces listed four of the five, so "
                 f"{verdict['nested_widened']} corpus questions written "
                 f"with `relative to` are read here and were unknown to the "
                 f"branch.  That widening is declared, and every widened "
                 f"question is accounted for by it.",
                 f"{verdict['kinds_nested']} nested kind nesting "
                 f"{', '.join(nested['nests'])}, "
                 f"{nested['options']} options carried; "
                 f"{nested_agreed['agreed']}/{nested_agreed['corpus']} "
                 f"agreed, {verdict['nested_widened']} widened "
                 f"({len(widening['unexplained'])} unexplained), "
                 f"{len(nested_agreed['disagreed'])} disagreed, "
                 f"{len(nested_agreed['false_positives'])} false positives "
                 f"on {nested_agreed['outside']} questions"),
            Step("what is recorded",
                 f"{verdict['because'][0].upper()}{verdict['because'][1:]}.  "
                 f"What the three families do not cover is named rather "
                 f"than left implicit: {len(parts)} limits are written "
                 f"down -- "
                 + "; ".join(part["part"] for part in parts)
                 + f" -- the first of them being the "
                 f"{len(coverage['undescribed_kinds'])} kinds that still "
                 f"have a branch apiece.",
                 f"verdict {verdict['verdict']} "
                 f"({verdict['kinds_covered']}/{verdict['kinds_total']} "
                 f"kinds described across "
                 f"{verdict['shape_families']} shape families, "
                 f"{verdict['kinds_read_off']} read off by the runtime)"),
        ]

        expected = {
            "kinds": ",".join(described["kinds"]),
            "judgements": str(described["judgements"]),
            "phrasings": str(described["phrasings"]),
            "slots": str(described["slots"]),
            "preamble_forms": str(described["preamble_forms"]),
            "corpus": str(agreed["corpus"]),
            "agreed": str(agreed["agreed"]),
            "disagreed": str(len(agreed["disagreed"])),
            "outside": str(agreed["outside"]),
            "false_positives": str(len(agreed["false_positives"])),
            "round_trips": str(trips["checked"]),
            "openings": str(disjoint["openings"]),
            "openings_disjoint": str(disjoint["disjoint"]),
            "witnesses": str(len(refusals["witnesses"])),
            "narrowing_witnesses": str(len(narrowing["witnesses"])),
            "narrowing_misread": str(narrowing["misread_by_the_parser"]),
            "infix_kinds": ",".join(infix["kinds"]),
            "infix_judgements": str(infix["judgements"]),
            "infix_corpus": str(infix_agreed["corpus"]),
            "infix_agreed": str(infix_agreed["agreed"]),
            "infix_disagreed": str(len(infix_agreed["disagreed"])),
            "nested_kinds": ",".join(nested["kinds"]),
            "nested_judgements": str(nested["judgements"]),
            "nested_corpus": str(nested_agreed["corpus"]),
            "nested_agreed": str(nested_agreed["agreed"]),
            "nested_widened": str(len(nested_agreed["widened"])),
            "nested_disagreed": str(len(nested_agreed["disagreed"])),
            "widenings": str(widening["witnesses"]),
            "widening_unexplained": str(len(widening["unexplained"])),
            "undescribed_kinds": str(len(coverage["undescribed_kinds"])),
            "undescribed_parts": str(len(parts)),
            "kinds_read_off": str(verdict["kinds_read_off"]),
            "kinds_covered": str(verdict["kinds_covered"]),
            "shape_families": str(verdict["shape_families"]),
            "verdict": str(verdict["verdict"]),
        }

        return Solution(
            query=query, kind="report",
            answer=f"report language: {verdict['kinds_covered']} of "
                   f"{verdict['kinds_total']} answerable query kinds -- "
                   f"{', '.join(described['kinds'])} by slot shape, "
                   f"{', '.join(infix['kinds'])} by infix shape and "
                   f"{', '.join(nested['kinds'])} by nested shape -- are "
                   f"described rather than hand-written, in "
                   f"{described['slots']} slots and {infix['operands']} "
                   f"operands over {described['phrasings']} and "
                   f"{infix['phrasings']} surface forms that cost "
                   f"{described['judgements']}, "
                   f"{verdict['infix_judgements']} and "
                   f"{verdict['nested_judgements']} decisions about "
                   f"English, all of them counted; every one of those "
                   f"kinds is now read off its description by the runtime "
                   f"with its hand-written branch deleted and frozen in "
                   f"`language.legacy`, and over corpora of "
                   f"{agreed['corpus']}, {infix_agreed['corpus']} and "
                   f"{nested_agreed['corpus']} questions generated from "
                   f"the registers that reading gives the same kind and "
                   f"the same options as the deleted branches "
                   f"{agreed['agreed']}, {infix_agreed['agreed']} and "
                   f"{nested_agreed['agreed']} times with "
                   f"{len(agreed['disagreed']) + len(infix_agreed['disagreed']) + len(nested_agreed['disagreed'])} "
                   f"disagreements, declines all {agreed['outside']} "
                   f"evaluation questions of the undescribed kinds and all "
                   f"{len(narrowing['witnesses'])} narrowing witnesses the "
                   f"branches misread, and round-trips every written "
                   f"question back to the slots it was written from; the "
                   f"{verdict['nested_widened']} questions the nested "
                   f"shape reads and its branch did not are the one "
                   f"declared widening, accounted for with "
                   f"{len(widening['unexplained'])} left over, so the "
                   f"round is recorded as {verdict['verdict']}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_language", "args": {}},
            payload={"report": jsonable({
                "kinds": ",".join(described["kinds"]),
                "infix_kinds": ",".join(infix["kinds"]),
                "nested_kinds": ",".join(nested["kinds"]),
                "corpus": agreed["corpus"],
                "agreed": agreed["agreed"],
                "infix_corpus": infix_agreed["corpus"],
                "infix_agreed": infix_agreed["agreed"],
                "nested_corpus": nested_agreed["corpus"],
                "nested_agreed": nested_agreed["agreed"],
                "nested_widened": len(nested_agreed["widened"]),
                "judgements": described["judgements"],
                "verdict": verdict["verdict"]})})
