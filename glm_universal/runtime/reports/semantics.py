"""``glm_universal.runtime.reports.semantics``
-- the subject :mod:`glm_universal.semantics` computes.

The grounding audit read off :mod:`glm_universal.semantics`.

Every method here is a solver for one ``report <subject>`` query.  They are
mixed into :class:`glm_universal.runtime.session.GeometricSession`,
which is where ``self`` comes from: the loaded registers, the concept index
and the shared helpers.  Splitting them out of the session keeps each family
beside a docstring that says which sub-package computes it, and keeps the
dispatcher readable as a dispatcher.
"""
from __future__ import annotations

from ...semantics import audit as sau

from ..parser import Query
from ..solution import Solution, Step


class SemanticsReports:
    """The subject :mod:`glm_universal.semantics` computes.

    A mixin of :class:`~glm_universal.runtime.session.GeometricSession`;
    it holds no state of its own.
    """

    def _report_semantics(self, query: Query) -> Solution:
        """Wires sau.audit_report -- what the inherited graph contains.

        Four measurements over the shipped state file, and the grounded
        graph that replaces what they condemn.  Every number is recomputed
        here; none is quoted.
        """
        report = sau.audit_report()
        concepts = report["concept_grounding"]
        edges = report["edge_grounding"]
        carriers = report["carrier_information"]
        variants = report["notational_variants"]
        plan = report["purge_plan"]
        replacement = report["replacement"]
        classes = edges["classes"]              # type: ignore[index]

        steps = [
            Step("concepts",
                 f"Of the {concepts['concepts']} inherited concepts, "     # type: ignore[index]
                 f"{concepts['grounded']} denote something determinate.",  # type: ignore[index]
                 f"grounded = {concepts['grounded_fraction']}\n"           # type: ignore[index]
                 f"by sense = {concepts['by_sense']}"),                    # type: ignore[index]
            Step("edges",
                 f"Of the {edges['edges']} inherited edges, "              # type: ignore[index]
                 f"{classes.get('derivable', 0)} state a relation between "
                 f"two determinate referents that can be re-derived now.",
                 f"classes = {classes}"),
            Step("carriers",
                 "Stored carrier distance against semantic relatedness: a "
                 "carrier that measured the subjects would put related "
                 "pairs closer.",
                 f"mean Hamming, related = "
                 f"{carriers['mean_hamming_related']}\n"                   # type: ignore[index]
                 f"mean Hamming, unrelated = "
                 f"{carriers['mean_hamming_unrelated']}\n"                 # type: ignore[index]
                 f"two random 24-bit words average 12"),
            Step("synonyms",
                 "Stored names that denote the same thing, and the distance "
                 "the inherited carrier puts between them.",
                 f"synonym pairs = {variants['synonym_pairs']}\n"          # type: ignore[index]
                 f"mean legacy Hamming = "
                 f"{variants['mean_legacy_hamming_between_synonyms']}\n"   # type: ignore[index]
                 f"distance in the meaning space = 0"),
            Step("replacement",
                 f"The grounded graph built from the registers: "
                 f"{replacement['meanings']} meanings carrying "           # type: ignore[index]
                 f"{replacement['notations']} notations, and every edge "   # type: ignore[index]
                 f"re-derived from the meanings it joins.",
                 f"binary edges = {replacement['binary_edges']}\n"         # type: ignore[index]
                 f"ternary edges = {replacement['ternary_edges']}\n"       # type: ignore[index]
                 f"all re-verified = "
                 f"{replacement['all_edges_reverified']}"),                # type: ignore[index]
        ]

        expected = {
            "legacy_concepts": str(concepts["concepts"]),          # type: ignore[index]
            "legacy_concepts_grounded": str(concepts["grounded"]),  # type: ignore[index]
            "legacy_edges": str(edges["edges"]),                    # type: ignore[index]
            "edges_proximity_artefact": str(
                classes.get("proximity_artefact", 0)),
            "edges_endpoint_ungrounded": str(
                classes.get("endpoint_ungrounded", 0)),
            "edges_derivable": str(classes.get("derivable", 0)),
            "edges_retained": str(plan["retained"]),                # type: ignore[index]
            "edges_dumped": str(plan["dumped"]),                    # type: ignore[index]
            "mean_hamming_related": str(
                carriers["mean_hamming_related"]),                  # type: ignore[index]
            "mean_hamming_unrelated": str(
                carriers["mean_hamming_unrelated"]),                # type: ignore[index]
            "synonym_pairs": str(variants["synonym_pairs"]),        # type: ignore[index]
            "mean_legacy_hamming_between_synonyms": str(
                variants["mean_legacy_hamming_between_synonyms"]),   # type: ignore[index]
            "grounded_meanings": str(replacement["meanings"]),      # type: ignore[index]
            "grounded_notations": str(replacement["notations"]),    # type: ignore[index]
            "grounded_binary_edges": str(
                replacement["binary_edges"]),                       # type: ignore[index]
            "grounded_ternary_edges": str(
                replacement["ternary_edges"]),                      # type: ignore[index]
            "all_edges_reverified": str(
                replacement["all_edges_reverified"]),               # type: ignore[index]
        }

        derived_edges = (int(replacement["binary_edges"])       # type: ignore[index]
                         + int(replacement["ternary_edges"]))   # type: ignore[index]
        return Solution(
            query=query, kind="report",
            answer=(f"report semantics: {concepts['grounded']} of "          # type: ignore[index]
                    f"{concepts['concepts']} inherited concepts denote "     # type: ignore[index]
                    f"anything determinate; {plan['retained']} of "          # type: ignore[index]
                    f"{plan['edges']} inherited edges survive the audit; "   # type: ignore[index]
                    f"the grounded graph has {replacement['meanings']} "     # type: ignore[index]
                    f"meanings and {derived_edges} re-derived edges"),
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_semantics", "args": {}},
            payload={"report": report})
