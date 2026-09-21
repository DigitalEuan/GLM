"""Tests for :mod:`glm_universal.corpus` -- the documents held as data.

What is pinned here is the *contract the prose is under*, so that a document
which drifts fails a run rather than misleading a reader.

* **The tier contract.**  Every current-state document carries a tier-0 block;
  every tier-0 verdict is quoted from, or says nothing beyond, the body below
  it; every number a deciding figure quotes appears in that body; and every
  function named as recomputing a figure resolves.

* **The archive rule.**  Membership of the archive is decided by the path and
  nothing else, and the two halves partition the corpus -- the executable form
  of ``GLM.Corpus.card_state_add_card_archive``.

* **The coverage claim.**  Every current-state document is reachable from
  ``ENTRY.md`` through current-state documents, every archived document is
  listed there, and no link in the repository points at a file that does not
  exist.

* **Generation.**  ``DIGEST.md`` and every ``<!-- generated: ... -->`` block
  match a fresh rendering, and rendering is idempotent -- writing twice changes
  nothing the second time.

* **The address book.**  It is fresh against the corpus digest, every unit has
  both addresses, the quantiser adds no conflation of its own, every feature
  vector reads back exactly, and the completeness bound of
  ``GLM.Retrieval.complete_shortlist`` holds on every pair checked -- so an
  empty shortlist really is the proof of absence
  ``GLM.Corpus.absent_of_shortlist_empty`` says it is.

* **Exactness.**  No float is constructed anywhere in the corpus report: every
  rate is a :class:`~fractions.Fraction` and every distance an ``int``.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.corpus import address as ad
from glm_universal.corpus import caches as ca
from glm_universal.corpus import checks as ck
from glm_universal.corpus import cost as ct
from glm_universal.corpus import gate as gt
from glm_universal.corpus import inventory as inv
from glm_universal.corpus import render as rd
from glm_universal.corpus import report as rp


# ===========================================================================
# 1.  THE INVENTORY
# ===========================================================================

class TestTheCorpusIsEnumeratedByRule(unittest.TestCase):

    def test_the_repository_root_is_the_one_holding_the_overlay(self):
        self.assertTrue((inv.REPOSITORY_ROOT / "overlay").is_dir())
        self.assertTrue((inv.REPOSITORY_ROOT / "ENTRY.md").is_file())

    def test_source_material_is_not_part_of_the_written_corpus(self):
        self.assertIn("source_material", inv.SKIP_DIRECTORIES)
        for path in inv.document_paths():
            self.assertFalse(path.startswith("source_material/"))

    def test_the_archive_rule_is_decided_by_the_path(self):
        self.assertTrue(inv.is_archive_path("MASTER_PLAN_ARCHIVE.md"))
        self.assertTrue(inv.is_archive_path("ARISTOTLE_SUMMARY.md"))
        self.assertTrue(inv.is_archive_path("studies/archive/OLD.md"))
        self.assertFalse(inv.is_archive_path("STATUS.md"))
        self.assertFalse(inv.is_archive_path("studies/HARMONY_STUDY.md"))

    def test_state_and_archive_partition_the_corpus(self):
        docs = inv.documents()
        state = inv.state_documents()
        archive = inv.archive_documents()
        self.assertEqual(len(state) + len(archive), len(docs))
        self.assertEqual(set(), {d.path for d in state} & {d.path for d in archive})

    def test_a_generated_document_is_one_a_generator_writes(self):
        for path in inv.generated_paths():
            self.assertTrue(inv.is_generated(path))
            document = inv.document(path)
            if document is not None:
                self.assertTrue(document.generated)
        self.assertIn("DIGEST.md", inv.generated_paths())

    def test_generated_documents_are_not_part_of_the_digest_inputs(self):
        sources = {d.path for d in inv.source_documents()}
        for path in inv.generated_paths():
            self.assertNotIn(path, sources)

    def test_the_corpus_digest_ignores_generated_block_bodies(self):
        before = inv.corpus_digest()
        self.assertEqual(before, inv.corpus_digest())
        self.assertEqual(64, len(before))

    def test_every_document_is_split_into_sections(self):
        for document in inv.documents():
            for section in document.sections:
                self.assertTrue(section.unit.startswith(document.path))
                self.assertGreater(section.end, section.start)


# ===========================================================================
# 2.  THE TIER CONTRACT
# ===========================================================================

class TestTheTierContract(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.report = ck.tier_report()

    def test_every_current_state_document_carries_a_tier_zero(self):
        self.assertEqual(self.report["with_tier0"],
                         self.report["state_documents"])

    def test_every_verdict_is_grounded_in_its_document(self):
        self.assertEqual(self.report["verdict_grounded"],
                         self.report["with_tier0"])

    def test_some_verdicts_are_literal_quotations(self):
        #  The weaker test is the one enforced; this records that most
        #  verdicts meet the stronger one as well.
        self.assertGreater(self.report["verdict_verbatim"],
                           self.report["with_tier0"] // 2)

    def test_every_deciding_figure_quotes_only_numbers_the_body_carries(self):
        self.assertEqual(self.report["figure_grounded"],
                         self.report["with_tier0"])

    def test_every_named_function_resolves(self):
        self.assertEqual(self.report["functions_resolve"],
                         self.report["with_function"])
        self.assertGreater(self.report["with_function"], 30)

    def test_the_contract_holds_with_no_failures(self):
        self.assertEqual((), self.report["failures"])
        self.assertTrue(self.report["holds"])

    def test_a_verdict_the_document_does_not_support_is_caught(self):
        body = "the address is complete up to a stated radius"
        self.assertEqual([], [w for w in ck._verdict_words("A stated radius.")
                              if w not in body])
        self.assertIn("kangaroo",
                      [w for w in ck._verdict_words("A kangaroo radius.")
                       if w not in body])


# ===========================================================================
# 3.  THE COVERAGE CLAIM
# ===========================================================================

class TestTheCoverageClaim(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.report = ck.reachability_report()

    def test_the_entry_document_is_present(self):
        self.assertTrue(self.report["entry_present"])
        self.assertEqual("ENTRY.md", self.report["entry_document"])

    def test_every_current_state_document_is_reachable(self):
        self.assertEqual((), self.report["unreachable"])
        self.assertEqual(self.report["reachable"], self.report["state_documents"])

    def test_every_archive_document_is_listed(self):
        self.assertEqual((), self.report["unlisted_archive"])
        self.assertEqual(self.report["archive_listed"],
                         self.report["archive_documents"])

    def test_no_link_points_at_a_file_that_does_not_exist(self):
        self.assertEqual((), self.report["broken_links"])

    def test_the_claim_holds(self):
        self.assertTrue(self.report["holds"])


# ===========================================================================
# 4.  WHAT IS GENERATED
# ===========================================================================

class TestGeneration(unittest.TestCase):

    def test_every_generated_document_matches_a_fresh_rendering(self):
        for path, renderer in sorted(rd.GENERATORS.items()):
            target = inv.REPOSITORY_ROOT / path
            self.assertTrue(target.is_file(), path)
            self.assertEqual(target.read_text(encoding="utf-8"), renderer(),
                             f"{path} is stale; run "
                             f"python3 -m glm_universal.corpus --write")

    def test_the_digest_holds_one_row_per_document(self):
        digest = rd.render_digest()
        for document in inv.source_documents():
            self.assertIn(f"[`{document.path}`]({document.path})", digest)

    def test_every_block_names_a_registered_renderer(self):
        for document in inv.source_documents():
            for name, _body in rd.block_spans(document.text):
                self.assertIn(name, rd.BLOCKS, f"{document.path}: {name}")

    @pytest.mark.exhaustive
    def test_every_generated_block_matches_a_fresh_rendering(self):
        outcome = rd.refresh(write=False)
        self.assertEqual((), outcome["blocks_changed"])
        self.assertEqual((), outcome["documents_written"])
        self.assertTrue(outcome["current"])

    def test_the_shape_of_the_generated_part_is_reported(self):
        shape = rd.generation_shape()
        self.assertEqual(len(rd.GENERATED), shape["generated_documents"])
        self.assertEqual(len(rd.GENERATORS), shape["rendered_here"])
        self.assertGreaterEqual(shape["blocks"], 8)


# ===========================================================================
# 5.  THE DOCUMENT ADDRESS BOOK
# ===========================================================================

class TestTheAddressBook(unittest.TestCase):

    def test_the_book_is_fresh_against_the_corpus_digest(self):
        state = ad.cache_state()
        self.assertEqual("fresh", state["verdict"],
                         "run python3 -m glm_universal.corpus --write")
        self.assertEqual(state["stored_digest"], inv.corpus_digest())

    def test_every_unit_has_both_addresses(self):
        names = {unit.name for unit in ad.units()}
        self.assertGreater(len(names), 400)
        for scheme in ("lexical", "structural"):
            self.assertEqual(names, set(ad.addresses(scheme)))

    def test_addresses_are_integer_points_of_the_lattice(self):
        for name, point in list(ad.addresses("lexical").items())[:20]:
            self.assertEqual(24, len(point), name)
            for coordinate in point:
                self.assertIsInstance(coordinate, int)

    def test_the_quantiser_adds_no_conflation_of_its_own(self):
        result = ad.injectivity("lexical")
        self.assertTrue(result["quantisation_adds_no_conflation"])
        self.assertEqual(result["distinct_addresses"], result["distinct_vectors"])

    def test_every_feature_vector_reads_back_exactly(self):
        trip = ad.round_trip("lexical")
        self.assertEqual(trip["checked"], trip["exact"])
        self.assertEqual(0, trip["coordinate_errors"])

    def test_a_distinctive_word_is_one_the_corpus_does_not_use_everywhere(self):
        frequency = ad.document_frequency()
        limit = max(1, len(ad.units()) // ad.DF_DENOMINATOR)
        for word in ad.distinctive_words("the leech lattice quantiser"):
            self.assertLessEqual(frequency.get(word, 0), limit)


class TestTheCertifiedShortlist(unittest.TestCase):

    def test_the_shortlist_is_complete_up_to_the_radius(self):
        answer = ad.shortlist("golay code covering radius sextet", 2)
        self.assertTrue(answer["answered"])
        self.assertTrue(answer["complete"])
        self.assertEqual(ad.address_radius_squared(2),
                         answer["address_radius_squared"])
        for found in answer["units"]:
            self.assertLessEqual(found.squared_distance,
                                 answer["address_radius_squared"])

    def test_an_empty_shortlist_is_reported_as_a_proof_of_absence(self):
        answer = ad.shortlist("zzzz qqqq xxxx unheard of vocabulary", 0)
        self.assertTrue(answer["answered"])
        if not answer["units"]:
            self.assertTrue(answer["proof_of_absence"])

    def test_the_guarantee_names_the_theorem_it_instantiates(self):
        answer = ad.shortlist("the tier contract", 1)
        self.assertEqual("GLM.Retrieval.complete_shortlist", answer["guarantee"])

    def test_retrieve_ranks_lexically_inside_the_guarantee(self):
        answer = ad.retrieve("what does the archive rule do?", k=5)
        self.assertEqual("text", answer["ranking_scheme"])
        self.assertEqual("lexical", answer["shortlist_scheme"])
        self.assertLessEqual(len(answer["ranked"]), 5)

    @pytest.mark.exhaustive
    def test_the_completeness_bound_holds_on_the_corpus(self):
        bound = ad.bound_report()
        self.assertGreater(bound["pairs_checked"], 10_000)
        self.assertEqual(0, bound["violations"])
        self.assertTrue(bound["bound_holds"])


class TestTheRetrievalMeasurement(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.report = ad.retrieval_report()

    def test_the_lexical_address_beats_chance_and_both_null_models(self):
        self.assertTrue(self.report["lexical_beats_chance"])
        self.assertTrue(self.report["lexical_beats_digest"])
        self.assertTrue(self.report["lexical_beats_shuffled"])

    def test_the_text_control_is_reported_even_though_it_wins(self):
        #  The honest finding, pinned so it cannot quietly disappear.
        self.assertTrue(self.report["text_beats_lexical"])
        self.assertEqual("text", self.report["best_scheme"])

    def test_every_rate_is_an_exact_fraction(self):
        self.assertIsInstance(self.report["chance"], Fraction)
        for scheme in ad.SCHEMES:
            score = self.report["schemes"][scheme]
            self.assertIsInstance(score["hit_rate"], Fraction)
            self.assertIsInstance(score["precision"], Fraction)

    def test_relevance_is_the_rest_of_the_document(self):
        table = ad.relative_table()
        for unit in ad.units()[:50]:
            for other in table[unit.name]:
                self.assertEqual(unit.document, other.split("#", 1)[0])
                self.assertNotEqual(unit.name, other)


# ===========================================================================
# 6.  THE WHOLE REPORT
# ===========================================================================

class TestInlineFigures(unittest.TestCase):
    """A number inside a sentence, emitted rather than typed.

    A generated block covers a section; the figures cover the phrase.  What is
    pinned here is the contract a marker carries: it names a figure something
    emits, its text is what that figure now says, it never sits inside a
    record of a past round, and its value is not part of what the corpus
    digest is taken over -- otherwise a sentence saying how large the corpus
    is would change what the corpus is.
    """

    def test_every_marker_names_a_registered_figure(self):
        for document in inv.source_documents():
            for name, _body in rd.figure_spans(document.text):
                self.assertIn(name, rd.FIGURES, f"{document.path}: {name}")

    def test_every_marker_holds_what_the_figure_says(self):
        report = rd.figure_report()
        self.assertEqual((), report["stale"],
                         "an inline figure has drifted; run "
                         "python3 -m glm_universal.corpus --refresh")
        self.assertTrue(report["holds"])
        self.assertGreater(report["fresh"], 0)

    def test_no_live_figure_sits_in_a_record_of_a_past_round(self):
        self.assertEqual((), rd.figure_report()["in_history"])

    def test_a_figure_is_rewritten_where_a_history_marker_does_not_protect_it(self):
        text = ("the suite is <!--figure:test-files-->1 test file"
                "<!--/figure--> today\n")
        fresh = rd.refresh_text(text)
        self.assertIn(rd._render_figure("test-files"), fresh)
        self.assertEqual(fresh, rd.refresh_text(fresh))

    def test_a_record_of_a_past_round_keeps_the_figure_it_was_written_with(self):
        text = ("<!-- figures:history -->\n"
                "that round counted <!--figure:test-files-->1 test file"
                "<!--/figure-->\n")
        self.assertEqual(text, rd.refresh_text(text))

    def test_an_unregistered_marker_is_left_alone_and_reported(self):
        text = "<!--figure:no-such-figure-->7<!--/figure-->"
        self.assertEqual(text, rd.refresh_text(text))

    def test_the_value_of_a_figure_is_outside_the_corpus_digest(self):
        document = next(d for d in inv.source_documents()
                        if rd.figure_spans(d.text))
        written = inv.written_text(document)
        self.assertTrue(rd.figure_spans(written))
        for _name, body in rd.figure_spans(written):
            self.assertEqual("", body)

    def test_every_figure_renders_a_non_empty_string(self):
        for name in rd.FIGURES:
            value = rd._render_figure(name)
            self.assertIsInstance(value, str)
            self.assertTrue(value.strip(), name)
            self.assertNotIn("\n", value, name)


class TestTheIterationCost(unittest.TestCase):
    """The cost report counts work avoided, in integers, and never times it."""

    def test_a_settled_tree_decodes_nothing(self):
        report = ct.cost_report()
        self.assertEqual(0, report["addresses"]["decodes_now"],
                         "nothing changed, so no address needed decoding; "
                         "run python3 -m glm_universal.corpus --refresh")
        self.assertGreater(report["addresses"]["decodes_from_nothing"], 0)
        self.assertTrue(report["settled"])

    def test_the_planner_report_is_taken_once_and_not_once_per_block(self):
        planner = ct.planner_cost()
        self.assertEqual(len(ct.PLANNER_BLOCKS),
                         planner["reports_per_check_before"])
        self.assertLessEqual(planner["reports_per_check_now"], 1)
        for name in ct.PLANNER_BLOCKS:
            self.assertIn(name, rd.BLOCKS)

    def test_the_figures_counted_are_the_figures_in_the_corpus(self):
        counted = ct.figure_cost()
        report = rd.figure_report()
        self.assertEqual(report["figures"], counted["in_the_corpus"])
        self.assertEqual(report["documents_with_figures"],
                         counted["documents"])
        self.assertEqual(len(rd.FIGURES), counted["registered"])

    def test_the_blast_radius_is_what_the_study_states(self):
        """The study's table of what one Lean edit costs, recomputed.

        ``lean_blast_radius`` is kept out of ``cost_report`` because it walks
        every unit's closure and ``cost_report`` is rendered into documents on
        every check.  This is where it is held to the prose instead.
        """
        radius = ct.lean_blast_radius()
        study = (Path(ct.__file__).resolve().parents[3]
                 / "studies" / "ITERATION_COST_STUDY.md")
        text = study.read_text(encoding="utf-8")
        for row, value in (
                ("test units in the suite", radius["units"]),
                ("Lean files", radius["lean_files"]),
                ("units an edit to *any* Lean file used to make stale",
                 radius["units_naming_lean"]),
                ("units one Lean file makes stale now, median",
                 radius["median_single_file"]),
                ("units the worst single Lean file makes stale",
                 radius["worst_single_file"]),
                ("units that read the tree with a glob, so are stale "
                 "whenever it moves",
                 radius["units_taking_the_whole_development"])):
            with self.subTest(row=row):
                self.assertIn(f"| {row} | {value} |", text)

    def test_the_ledger_is_selective_about_the_lean_development(self):
        """The property the study's table is evidence for.

        A unit that does not read the whole development must not depend on
        the whole development: that single rule is what made the ledger
        report every unit stale after any Lean edit.
        """
        radius = ct.lean_blast_radius()
        self.assertLess(radius["units_taking_the_whole_development"],
                        radius["units_naming_lean"])
        self.assertLessEqual(radius["median_single_file"],
                             radius["units_naming_lean"] // 2)

    def test_no_module_on_the_answering_path_reads_the_development(self):
        """The §5e rule, pinned at the modules that have broken it.

        The field surface broke it once by parsing the development on the
        runtime's import path, and the probe oracle broke it again by reading
        one declaration's file name off the tree rather than off the stored
        book -- which took the median cost of a Lean edit from 26 units back
        to 81, because nearly every unit reaches the probe.  Each of these
        modules is on the path a query takes, so none of them may carry the
        whole development; each reads the generated book instead, and the
        book is data, so a unit that reads it is still stale when it moves.
        """
        from glm_universal.signoff import rules as R
        development = {path for path in R.lean_sources()
                       if path.suffix == ".lean"}
        self.assertGreater(len(development), 100)
        reasoning = Path(R.__file__).resolve().parents[1] / "reasoning"
        for module in ("field_surface.py", "probe_oracle.py",
                       "coordinate_order.py", "lean_book.py"):
            with self.subTest(module=module):
                closure = set(R.unit_closure(reasoning / module))
                carried = development & closure
                self.assertLess(len(carried), len(development),
                                f"{module} carries the whole development")

    def test_no_reading_of_the_cost_is_a_float(self):
        def walk(value):
            self.assertNotIsInstance(value, float)
            if isinstance(value, dict):
                for item in value.values():
                    walk(item)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    walk(item)
        walk(ct.cost_report())


class TestTheCorpusReport(unittest.TestCase):

    def test_the_checks_hold(self):
        report = rp.corpus_report()
        self.assertTrue(report["holds"])

    def test_reading_at_tier_zero_costs_a_fraction_of_reading_in_full(self):
        cost = rp.reading_cost()
        self.assertLess(cost["tier0_fraction_of_state"], Fraction(1, 10))
        self.assertGreater(cost["words_tier0"], 0)

    def test_nothing_in_the_report_is_a_float(self):
        def walk(value):
            self.assertNotIsInstance(value, float)
            if isinstance(value, dict):
                for item in value.values():
                    walk(item)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    walk(item)
        walk(rp.corpus_report())


# ===========================================================================
# 8b.  THE GATE THAT SKIPS AN UNCHANGED CHECK
# ===========================================================================

class TestTheDocumentsGateRecord(unittest.TestCase):
    """``--check`` may skip only a question whose inputs have not moved.

    The documents check renders every generated block of every document and
    costs about three quarters of a minute; a session runs it on picking the
    round up, when nothing at all has changed since the last round closed.
    The record lets it answer that case in a second.  What is pinned here is
    the part that could be wrong: what the digest covers, that only a *pass*
    is skippable, and that a moved input is not.
    """

    def test_the_digest_covers_the_documents_the_code_and_the_development(self):
        closure = {path.name for path in gt._closure()}
        for named in ("STATUS.md", "ENTRY.md", "render.py", "inventory.py",
                      "__main__.py"):
            self.assertIn(named, closure)
        self.assertTrue(any(name.endswith(".lean") for name in closure))

    def test_the_digest_is_a_function_of_the_tree_alone(self):
        self.assertEqual(gt.inputs_digest(), gt.inputs_digest())
        self.assertEqual(64, len(gt.inputs_digest()))

    def test_a_pass_is_skippable_and_a_failure_is_not(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "gate.json"
            original = gt.GATE_PATH
            gt.GATE_PATH = path
            try:
                self.assertIsNone(gt.unchanged_since_pass())
                gt.record(True)
                self.assertIsNotNone(gt.unchanged_since_pass())
                gt.record(False)
                self.assertIsNone(gt.unchanged_since_pass())
                #  A pass recorded against another tree is not this tree's.
                gt.record(True, digest="0" * 64)
                self.assertIsNone(gt.unchanged_since_pass())
                gt.forget()
                self.assertIsNone(gt.stored())
            finally:
                gt.GATE_PATH = original

    def test_a_record_of_another_schema_is_ignored_rather_than_trusted(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "gate.json"
            original = gt.GATE_PATH
            gt.GATE_PATH = path
            try:
                path.write_text(json.dumps({
                    "schema": gt.SCHEMA + 1, "verdict": "current",
                    "digest": gt.inputs_digest(), "at": "then"}),
                    encoding="utf-8")
                self.assertIsNone(gt.stored())
                self.assertIsNone(gt.unchanged_since_pass())
            finally:
                gt.GATE_PATH = original


# ===========================================================================
# 9.  THE MEASUREMENT CACHES
# ===========================================================================

class TestEveryStoredMeasurementIsAccountedFor(unittest.TestCase):
    """The census of study caches: total, cheap, and reachable.

    Each of these caches is a set of figures too expensive to take while
    rendering, kept beside the digest of the sources it was taken from. The
    discipline is sound on its own -- a stale cache refuses rather than
    answers -- but until the census existed a stale one was found by whatever
    happened to read it, which in the worst case was a release run twenty
    minutes in. What is pinned here is that the census *finds* them all and
    that each one names the command that re-takes it.
    """

    def test_a_cache_is_recognised_by_its_shape_not_by_a_list(self):
        found = set(ca.cached_modules())
        self.assertIn("query_escalation", found)
        self.assertIn("blockers", found)
        for name in found:
            source = (ca.REASONING / f"{name}.py").read_text(encoding="utf-8")
            self.assertIn("def module_digest(", source)
            self.assertIn("def current(", source)

    def test_every_cache_names_the_command_that_re_takes_it(self):
        census = ca.cache_census()
        self.assertEqual((), census["without_a_command"])
        commands = ca.commands_by_module()
        for name in ca.cached_modules():
            self.assertIn(name, commands)

    def test_the_commands_are_sub_commands_the_tool_actually_has(self):
        from glm_universal import tools

        parser = tools._parser()
        actions = [action for action in parser._actions
                   if hasattr(action, "choices") and action.choices]
        available = set()
        for action in actions:
            available.update(action.choices)
        for command in ca.commands_by_module().values():
            self.assertIn(command, available)

    def test_the_census_adds_up(self):
        census = ca.cache_census()
        self.assertEqual(census["caches"], len(ca.cached_modules()))
        self.assertEqual(census["caches"],
                         census["fresh"] + len(census["stale"]))
        self.assertEqual(census["holds"],
                         not census["stale"] and not census["without_a_command"])

    def test_a_stale_cache_is_described_with_its_command(self):
        rows = ({"module": "example", "fresh": False, "command": "example",
                 "retake": "PYTHONPATH=. python3 -m glm_universal.tools "
                           "example --write"},)
        lines = ca.describe({"rows": rows, "without_a_command": ()})
        self.assertEqual(1, len(lines))
        self.assertIn("example is stale", lines[0])
        self.assertIn("--write", lines[0])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
