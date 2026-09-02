"""``glm_universal.runtime.reports.recipe``
-- the subject :mod:`glm_universal.recipe` computes.

The domain descriptions and the one generic path that builds them.

Every method here is a solver for one ``report <subject>`` query.  They are
mixed into :class:`glm_universal.runtime.session.GeometricSession`,
which is where ``self`` comes from: the loaded registers, the concept index
and the shared helpers.  Splitting them out of the session keeps each family
beside a docstring that says which sub-package computes it, and keeps the
dispatcher readable as a dispatcher.
"""
from __future__ import annotations

from fractions import Fraction

from ... import recipe as rcp

from ..payload import jsonable
from ..parser import Query
from ..solution import Solution, Step, q


class RecipeReports:
    """The subject :mod:`glm_universal.recipe` computes.

    A mixin of :class:`~glm_universal.runtime.session.GeometricSession`;
    it holds no state of its own.
    """

    def _report_recipe(self, query: Query) -> Solution:
        """Wires rcp.recipe_report -- the recipe made into an object.

        Every capability here was built by hand from one recipe.  This subject
        runs the recipe's *input* instead: three domains built in earlier
        rounds, each written down as a description, each rebuilt from its
        description alone by one generic path, and each compared against the
        register the hand-written module ships -- carrier by carrier, object
        by object, and figure by figure.
        """
        report = rcp.recipe_report()
        shared = report["shared"]
        verdict = report["verdict"]
        domains = report["domains"]
        refused = report["queries"]["refused_coordinate"]
        answered = report["queries"]["answered"]

        steps = [
            Step("the recipe, written down",
                 f"A description says what a domain's objects are, which "
                 f"held quantity each coordinate derives from, which "
                 f"coordinates recover the object, what a reading of one "
                 f"object is, and what must be refused.  Three domains built "
                 f"by hand in earlier rounds now have one: "
                 f"{', '.join(shared['domains'])}.",
                 f"{verdict['domains_described']} descriptions, "
                 f"{shared['coordinates']} coordinates, "
                 f"{len(shared['primitives_used'])} of "
                 f"{shared['primitives_available']} shared primitives used"),
            Step("what generalises, and what does not",
                 f"A coordinate is either a shared primitive -- the same rule "
                 f"serving a frequency ratio, a quoted price and a "
                 f"comparison bracket -- or a judgement the domain has to "
                 f"state for itself.  The judgements are not eliminated: "
                 f"they are counted, and they are exactly the musical "
                 f"conventions.  The comparison and economic registers need "
                 f"none at all.",
                 f"{shared['derivations']} derivations, "
                 f"{shared['judgements']} judgements "
                 f"({', '.join(f'{k} {v}' for k, v in shared['judgements_by_domain'].items())})"),
            Step("one path from a description",
                 f"The carrier encoding, the layer chain, the widening "
                 f"audit, the query surface and the refusal boundary are all "
                 f"computed from the description by "
                 f"`glm_universal.recipe.build`, which knows nothing about "
                 f"any domain.  Every chain came back a refinement chain, "
                 f"and every register lossless against its own read-back.",
                 "; ".join(f"{d['domain']}: {len(d['readings'])} readings, "
                           f"chain {d['chain_intact']}, lossless "
                           f"{d['lossless']}" for d in domains)),
            Step("the test: delete a domain and rebuild it",
                 f"Each domain goes description -> carrier -> read-back -> "
                 f"its own object, and the result is compared against what "
                 f"the hand-written module ships: "
                 f"{verdict['carriers_identical']} of "
                 f"{verdict['carriers_compared']} carriers identical "
                 f"coordinate by coordinate, every object equal, and the "
                 f"figures the reasoning modules measure unchanged with the "
                 f"regenerated register in the shipped one's place.",
                 "; ".join(f"{d['domain']}: {d['carriers_identical']}/"
                           f"{d['carriers_compared']} carriers, figures "
                           f"{d['figures_unchanged']}" for d in domains)),
            Step("the query surface, and where it refuses",
                 f"`derive <coordinate> of <object>` is answered off the "
                 f"descriptions rather than off a hand-written phrase, so a "
                 f"new description costs no new parsing rule.  A coordinate "
                 f"no description derives is refused with the reason, which "
                 f"is `GLM.Recipe.Spec.answer_eq_none_iff`.",
                 f"answered: {answered['coordinate']} of "
                 f"{answered['object']} = "
                 f"{q(answered['value']) if isinstance(answered['value'], Fraction) else answered['value']}; "
                 f"refused: {refused['reason']}"),
            Step("what is recorded",
                 f"{verdict['because'][0].upper()}{verdict['because'][1:]}.  "
                 f"What the descriptions do not remove is the judgements, "
                 f"and what they do not yet cover is the rest of the "
                 f"registers: three domains are described, not all of them.",
                 f"verdict {verdict['verdict']} "
                 f"({verdict['domains_regenerated']}/"
                 f"{verdict['domains_described']} domains)"),
        ]

        expected = {
            "domains": ",".join(shared["domains"]),
            "coordinates": str(shared["coordinates"]),
            "derivations": str(shared["derivations"]),
            "judgements": str(shared["judgements"]),
            "primitives_used": str(len(shared["primitives_used"])),
            "carriers_compared": str(verdict["carriers_compared"]),
            "carriers_identical": str(verdict["carriers_identical"]),
            "domains_regenerated": str(verdict["domains_regenerated"]),
            "chains_intact": str(verdict["chains_intact"]),
            "all_lossless": str(verdict["all_lossless"]),
            "figures_unchanged": str(verdict["figures_unchanged"]),
            "verdict": str(verdict["verdict"]),
        }
        for entry in domains:
            expected[f"{entry['domain']}_judgements"] = \
                str(entry["judgement_count"])
            expected[f"{entry['domain']}_carriers"] = \
                str(entry["carriers_identical"])

        return Solution(
            query=query, kind="report",
            answer=f"report recipe: {verdict['domains_described']} domains "
                   f"described -- {', '.join(shared['domains'])} -- in "
                   f"{shared['coordinates']} coordinates, of which "
                   f"{shared['derivations']} are shared primitives and "
                   f"{shared['judgements']} are judgements the domain states "
                   f"for itself (all six of them musical); one generic path "
                   f"builds the carriers, the layer chain, the widening "
                   f"audit and the query surface from each description, and "
                   f"regenerating the three registers from their "
                   f"descriptions alone reproduces "
                   f"{verdict['carriers_identical']} of "
                   f"{verdict['carriers_compared']} carriers exactly, with "
                   f"every measured figure unchanged, so the round is "
                   f"recorded as {verdict['verdict']}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_recipe", "args": {}},
            payload={"report": jsonable({
                "domains": ",".join(shared["domains"]),
                "coordinates": shared["coordinates"],
                "judgements": shared["judgements"],
                "verdict": verdict["verdict"]})})
