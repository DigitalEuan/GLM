"""``glm_universal.runtime.reports.migration``
-- the subjects about moving the legacy data onto the core.

Reports about migration: the machinery, and the data it moved.

``report migration`` is about the permutation between two Golay frames;
``report state migration`` and ``report concept store`` are about the data
-- what the migrated state contains and what can be asked of it.

Every method here is a solver for one ``report <subject>`` query.  They are
mixed into :class:`glm_universal.runtime.session.GeometricSession`,
which is where ``self`` comes from: the loaded registers, the concept index
and the shared helpers.  Splitting them out of the session keeps each family
beside a docstring that says which sub-package computes it, and keeps the
dispatcher readable as a dispatcher.
"""
from __future__ import annotations

from ...migration import state as stm
from ...migration import store as sto
from ...substrate import isomorphism as iso

from ..parser import Query
from ..solution import Solution, Step


class MigrationReports:
    """The subjects about moving the legacy data onto the core.

    A mixin of :class:`~glm_universal.runtime.session.GeometricSession`;
    it holds no state of its own.
    """

    def _report_migration(self, query: Query) -> Solution:
        """Wires iso.migration_report -- the legacy-to-core bridge."""
        report = iso.migration_report()
        codes = report["codes"]
        isometry = codes["isometry"]
        automorphism = codes["automorphism"]
        decoder = report["decoder"]
        dataset = report["dataset"]

        steps = [
            Step("two frames, one bridge",
                 f"The legacy Golay frame and this package's canonical one "
                 f"share only {codes['shared_codewords']} of their "
                 f"{codes['core_codewords']} codewords, so legacy data read "
                 f"in canonical coordinates is a different codeword, not a "
                 f"relabelled one.  The derived permutation fixes "
                 f"{len(report['fixed_points'])} coordinates and moves the "
                 f"rest.",
                 f"permutation = {report['permutation']}, "
                 f"shared codewords = {codes['shared_codewords']}"),
            Step("it is an isomorphism, not an automorphism",
                 f"Under the permutation "
                 f"{automorphism['codewords_leaving_the_code']} of the "
                 f"{automorphism['codewords']} canonical codewords leave the "
                 f"canonical code -- as they must, since the two codes are "
                 f"different -- while the weight distributions agree "
                 f"exactly, so the image is an equivalent [24, 12, 8] code.",
                 f"is_automorphism = {automorphism['is_automorphism']}, "
                 f"weight distributions agree = "
                 f"{codes['weight_distributions_agree']}"),
            Step("why a permutation and not any linear isomorphism",
                 f"A coordinate permutation preserves Hamming weight and "
                 f"distance, checked here on all "
                 f"{isometry['codewords_checked']} codewords and "
                 f"{isometry['pairs_checked']} pairs, so it commutes with "
                 f"nearest-codeword decoding and may be wrapped around the "
                 f"decoder.  A general linear isomorphism between the two "
                 f"codes scrambles distance and may not.",
                 f"weight preserving = {isometry['weight_preserving']}, "
                 f"distance preserving = "
                 f"{isometry['distance_preserving']}"),
            Step("decoding legacy data",
                 f"Routing legacy words through the canonical frame and the "
                 f"complete decoder recovers the truth on every sampled "
                 f"pattern within the packing radius, and turns all "
                 f"{decoder['snap_silent_ties_total']} silently broken ties "
                 f"into explicit ambiguities.  Weight-5 miscorrection "
                 f"survives in both columns, because it is a theorem about "
                 f"the code.",
                 f"silent ties = {decoder['snap_silent_ties_total']}, "
                 f"now flagged = {decoder['routed_flagged_total']}"),
            Step("bulk migration",
                 f"Concepts, CRG edges and hexcolour addresses migrate "
                 f"through one call.  On the exercise dataset "
                 f"({dataset['concepts']} concepts, {dataset['edges']} "
                 f"edges, {dataset['hexcolours']} addresses) the migration "
                 f"round-trips, preserves weights, keeps masks distinct and "
                 f"leaves no dangling edge.",
                 f"round trip = {dataset['round_trip']}, "
                 f"referentially intact = "
                 f"{dataset['referentially_intact']}"),
        ]
        expected = {
            "is_permutation": str(report["is_permutation"]),
            "fixed_points": str(list(report["fixed_points"])),
            "shared_codewords": str(codes["shared_codewords"]),
            "legacy_is_distinct": str(codes["legacy_is_distinct"]),
            "weight_distributions_agree":
                str(codes["weight_distributions_agree"]),
            "minimum_distance": str(codes["minimum_distance"]),
            "is_automorphism": str(automorphism["is_automorphism"]),
            "weight_preserving": str(isometry["weight_preserving"]),
            "distance_preserving": str(isometry["distance_preserving"]),
            "snap_silent_ties_total":
                str(decoder["snap_silent_ties_total"]),
            "routed_flagged_total": str(decoder["routed_flagged_total"]),
            "every_silent_tie_is_now_flagged":
                str(decoder["every_silent_tie_is_now_flagged"]),
            "guaranteed_below_packing_radius":
                str(decoder["guaranteed_below_packing_radius"]),
            "dataset_round_trip": str(dataset["round_trip"]),
            "dataset_weights_preserved": str(dataset["weights_preserved"]),
            "dataset_referentially_intact":
                str(dataset["referentially_intact"]),
        }
        return Solution(
            query=query, kind="report",
            answer=f"report migration: the legacy and canonical codes share "
                   f"{codes['shared_codewords']} of "
                   f"{codes['core_codewords']} codewords; the bridge is a "
                   f"weight- and distance-preserving permutation, so legacy "
                   f"data can be decoded through the audited decoder, and "
                   f"all {decoder['snap_silent_ties_total']} silent ties "
                   f"become explicit",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_migration", "args": {}},
            payload={"report": report})

    # ------------------------------------------------------------------
    # 3l.  the migrated repository data
    # ------------------------------------------------------------------
    # ``report migration`` above is about the *machinery* -- a permutation
    # between two Golay frames.  These two are about the *data*: which
    # frame the repository actually writes in, what the migrated state
    # contains, and what can be asked of it once migrated.
    # ------------------------------------------------------------------

    def _report_state_migration(self, query: Query) -> Solution:
        """Wires stm.state_migration_report -- the literal data migration."""
        report = stm.state_migration_report()
        if not report.get("available"):
            return Solution(
                query=query, kind="report",
                answer="report state migration: no stored GLM state is "
                       "present in this checkout",
                ok=False, error="state migration: no data",
                steps=(Step("no data",
                            "Neither the migrated state nor the source "
                            "state was found under arc_agi_17/results.",
                            "glm_state_canonical.json absent"),),
                payload={"report": report})

        checks = report["checks"]
        frame = report["frame"]
        verification = report["verification"]
        hexcolours = report["hexcolours"]
        addresses = frame["addresses"] or {}

        steps = [
            Step("which frame the data is in",
                 f"The repository's own Golay engine and this package's "
                 f"canonical code are the same "
                 f"{frame['shared_codewords']} words under the same "
                 f"coordinate numbering, so concept vectors migrate by the "
                 f"identity.  The legacy-to-core permutation would move "
                 f"{frame['permutation_damage']} codewords off the code, so "
                 f"it must not be applied to them.",
                 f"frames coincide = {frame['frames_coincide']}, "
                 f"bridge = {frame['correct_bridge']}"),
            Step("the one real coordinate correction",
                 f"Stored integer addresses put coordinate i at bit 23-i.  "
                 f"Read with the bit reversal, "
                 f"{addresses.get('codewords_read_msb_first', 0)} of "
                 f"{addresses.get('addresses', 0)} are Golay codewords; read "
                 f"without it, "
                 f"{addresses.get('codewords_read_lsb_first', 0)} are.  The "
                 f"data decides the convention.",
                 f"bit reversal required = "
                 f"{addresses.get('bit_reversal_required')}"),
            Step("what came across",
                 f"{checks['concepts_imported']} concepts and "
                 f"{checks['edges_migrated']} edges, with "
                 f"{checks['concepts_minted']} carriers minted for edge "
                 f"endpoints the state never gave one and "
                 f"{checks['edges_dropped']} edge dropped for a nameless "
                 f"endpoint.  Roles and quadrant weights are recomputed from "
                 f"the carriers, and agree with the stored values in all "
                 f"{checks['roles_agree']} cases.",
                 f"concepts = {checks['concepts_total']}, "
                 f"referentially intact = "
                 f"{checks['referentially_intact']}"),
            Step("how much of it is anchored",
                 f"A concept vector is a received word, not a codeword: "
                 f"{checks['carriers_that_are_codewords']} of "
                 f"{checks['concepts_total']} are codewords, "
                 f"{checks['decode_corrected']} decode to a unique nearest "
                 f"codeword, and {checks['decode_ambiguous']} are genuinely "
                 f"ambiguous -- six equally near codewords and no answer.  "
                 f"Those are recorded as ambiguous rather than snapped.",
                 f"guaranteed = {checks['decode_guaranteed']}, "
                 f"ambiguous = {checks['decode_ambiguous']}"),
            Step("exactness",
                 f"NRCI is rewritten as an exact rational from the package's "
                 f"Y; the stored float is kept beside it as the rational it "
                 f"really is, and the two differ by at most "
                 f"{checks['worst_nrci_gap'][0]}/"
                 f"{checks['worst_nrci_gap'][1]}.  The written payload "
                 f"contains {verification['floats_in_payload']} floats.",
                 f"fields recomputed and agreeing = "
                 f"{verification['fields_recomputed_and_agreeing']}"),
            Step("the hexcolour addresses",
                 f"Every migrated concept carries a hexcolour -- the "
                 f"six-hex-digit rendering of its 24-bit carrier, one digit "
                 f"per four coordinates.  All "
                 f"{hexcolours['concepts']} of them are distinct, so the "
                 f"rendering separates the concepts it addresses; "
                 f"{hexcolours['round_trip_failures']} fail to read back to "
                 f"their own mask, {hexcolours['recomputed_disagreements']} "
                 f"disagree with the mask they are stored beside, and "
                 f"{hexcolours['migration_mismatches']} fail to commute with "
                 f"the legacy-to-core relabelling.  The "
                 f"{hexcolours['legacy_addresses']} per-task addresses the "
                 f"supplied ARC pipeline left behind are all Golay codewords "
                 f"({hexcolours['legacy_codewords']} of "
                 f"{hexcolours['legacy_addresses']}) and all round-trip.",
                 f"faithful = {hexcolours['faithful']}"),
        ]

        expected = {
            "frames_coincide": str(frame["frames_coincide"]),
            "shared_codewords": str(frame["shared_codewords"]),
            "permutation_damage": str(frame["permutation_damage"]),
            "bit_reversal_required":
                str(addresses.get("bit_reversal_required")),
            "concepts_imported": str(checks["concepts_imported"]),
            "concepts_minted": str(checks["concepts_minted"]),
            "edges_migrated": str(checks["edges_migrated"]),
            "edges_dropped": str(checks["edges_dropped"]),
            "referentially_intact": str(checks["referentially_intact"]),
            "roles_agree": str(checks["roles_agree"]),
            "carriers_that_are_codewords":
                str(checks["carriers_that_are_codewords"]),
            "decode_ambiguous": str(checks["decode_ambiguous"]),
            "decode_guaranteed": str(checks["decode_guaranteed"]),
            "worst_nrci_gap": str(list(checks["worst_nrci_gap"])),
            "fields_recomputed_and_agreeing":
                str(verification["fields_recomputed_and_agreeing"]),
            "floats_in_payload": str(verification["floats_in_payload"]),
            "hexcolour_concepts": str(hexcolours["concepts"]),
            "hexcolour_distinct": str(hexcolours["distinct"]),
            "hexcolour_round_trip_failures":
                str(hexcolours["round_trip_failures"]),
            "hexcolour_recomputed_disagreements":
                str(hexcolours["recomputed_disagreements"]),
            "hexcolour_migration_mismatches":
                str(hexcolours["migration_mismatches"]),
            "legacy_hexcolours": str(hexcolours["legacy_addresses"]),
            "legacy_hexcolour_codewords": str(hexcolours["legacy_codewords"]),
            "legacy_hexcolour_round_trip_failures":
                str(hexcolours["legacy_round_trip_failures"]),
            "hexcolours_faithful": str(hexcolours["faithful"]),
        }
        return Solution(
            query=query, kind="report",
            answer=f"report state migration: {checks['concepts_imported']} "
                   f"concepts and {checks['edges_migrated']} edges migrated "
                   f"in the canonical frame, "
                   f"{checks['concepts_minted']} carriers minted, "
                   f"{checks['decode_ambiguous']} carriers ambiguous under "
                   f"complete decoding, no float written",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_state_migration", "args": {}},
            payload={"report": report})

    def _report_concept_store(self, query: Query) -> Solution:
        """Wires sto.store_report -- what the migrated data supports."""
        report = sto.store_report()
        if not report.get("available"):
            return Solution(
                query=query, kind="report",
                answer="report concept store: the migrated state has not "
                       "been written",
                ok=False, error="concept store: no data",
                steps=(Step("no data",
                            "Run the state migration first.",
                            "glm_state_canonical.json absent"),),
                payload={"report": report})

        steps = [
            Step("the graph",
                 f"{report['concepts']} concepts, {report['edges']} edges "
                 f"and {report['labels']} distinct relation labels.  The "
                 f"busiest concept is {report['max_degree_concept']} with "
                 f"{report['max_degree']} edges.",
                 f"concepts = {report['concepts']}, "
                 f"edges = {report['edges']}"),
            Step("how much of it is asserted",
                 f"{report['asserted_edges']} edges carry a real relation "
                 f"label; {report['auto_proposed_edges']} are "
                 f"'auto_proposed', proposals the growth loop made and "
                 f"nothing confirmed.  A walk that excludes them is a walk "
                 f"over asserted knowledge only, and it gives different "
                 f"answers.",
                 f"asserted = {report['asserted_edges']}, "
                 f"auto-proposed = {report['auto_proposed_edges']}"),
            Step("how much of it is reachable",
                 f"{report['isolated_concepts']} of the concepts have no "
                 f"edge at all, so they can be described but not reasoned "
                 f"about relationally; {report['minted_concepts']} carriers "
                 f"were minted by the migration and are marked as such.",
                 f"isolated = {report['isolated_concepts']}, "
                 f"minted = {report['minted_concepts']}"),
            Step("two kinds of nearness",
                 f"On {report['samples_checked']} sampled concepts, the "
                 f"graph neighbourhood and the five nearest carriers in "
                 f"Hamming distance share a name in "
                 f"{report['samples_where_graph_and_substrate_agree']} "
                 f"cases.  The carriers were assigned by digest, not by "
                 f"meaning, so substrate distance between concepts is not a "
                 f"semantic distance and must not be read as one.",
                 f"agreements = "
                 f"{report['samples_where_graph_and_substrate_agree']}"
                 f"/{report['samples_checked']}"),
        ]
        expected = {
            "concepts": str(report["concepts"]),
            "edges": str(report["edges"]),
            "labels": str(report["labels"]),
            "asserted_edges": str(report["asserted_edges"]),
            "auto_proposed_edges": str(report["auto_proposed_edges"]),
            "isolated_concepts": str(report["isolated_concepts"]),
            "minted_concepts": str(report["minted_concepts"]),
            "max_degree": str(report["max_degree"]),
            "max_degree_concept": str(report["max_degree_concept"]),
            "samples_checked": str(report["samples_checked"]),
            "samples_where_graph_and_substrate_agree":
                str(report["samples_where_graph_and_substrate_agree"]),
        }
        return Solution(
            query=query, kind="report",
            answer=f"report concept store: {report['concepts']} concepts, "
                   f"{report['edges']} edges "
                   f"({report['asserted_edges']} asserted, "
                   f"{report['auto_proposed_edges']} auto-proposed), "
                   f"{report['isolated_concepts']} isolated",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_concept_store", "args": {}},
            payload={"report": report})
