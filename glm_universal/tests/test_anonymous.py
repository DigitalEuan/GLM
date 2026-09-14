"""Tests for :mod:`glm_universal.reasoning.anonymous` -- the anonymous register.

Five things are pinned here.

* **The anonymiser is what it says it is.**  It replaces every identifier
  outside the declared vocabulary, leaves the declared vocabulary and every
  symbol alone, is a function of the text and of nothing else, and is
  idempotent on a text it has already renamed.

* **The Lean file's promises hold of the running code.**  The structural
  reading of a statement survives the renaming
  (``GLM.Anonymous.features_anonymise``), the identifier overlap with the
  corpus is destroyed by it (``overlap_anonymise_eq_zero``), and with
  confidence zero the stack's relay is the interleave
  (``relay_hands_over``) -- each checked against the shipped mechanism rather
  than restated.

* **The idealisation is audited rather than assumed.**  The shipped feature
  map counts the type vocabulary *wherever it occurs*, including inside an
  identifier, so a renaming can move one of those six coordinates.  The test
  pins both halves: no other syntax coordinate ever moves, and the queries
  where one of the six does are counted rather than waved away.

* **The measured claim is recomputed from the report's own tables**, so the
  answer the runtime prints cannot drift from the measurement behind it.

* **The arithmetic is exact** -- rates and overlaps are
  :class:`~fractions.Fraction`, no float anywhere (directive D7).
"""

from __future__ import annotations

import pathlib
import unittest
from fractions import Fraction

from glm_universal.reasoning import anonymous as an
from glm_universal.reasoning import exactness as ex
from glm_universal.reasoning import lean_address as la
from glm_universal.reasoning import pipeline as ppl
from glm_universal.reasoning import retrieval as rt
from glm_universal.reasoning import stack as sk
from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import GeometricSession, REPORT_SUBJECTS


SAMPLE = "theorem foo (n : Nat) : bar n = baz n"


# ===========================================================================
# 1.  THE ANONYMISER
# ===========================================================================

class TestTheAnonymiser(unittest.TestCase):

    def test_it_replaces_everything_outside_the_declared_vocabulary(self):
        out = an.anonymise(SAMPLE)
        for token in ("foo", "bar", "baz", "n"):
            with self.subTest(token=token):
                self.assertNotIn(token, an.renaming(SAMPLE).values())
                self.assertNotIn(f" {token} ", f" {out} ")

    def test_it_keeps_the_declared_vocabulary(self):
        out = an.anonymise(SAMPLE)
        self.assertIn("theorem", out)
        self.assertIn("Nat", out)

    def test_it_keeps_every_symbol_and_the_token_count(self):
        out = an.anonymise(SAMPLE)
        self.assertEqual(out.count("("), SAMPLE.count("("))
        self.assertEqual(out.count("="), SAMPLE.count("="))
        self.assertEqual(out.count(":"), SAMPLE.count(":"))
        self.assertEqual(len(out.split()), len(SAMPLE.split()))

    def test_it_is_a_function_of_the_text_alone(self):
        self.assertEqual(an.anonymise(SAMPLE), an.anonymise(SAMPLE))
        self.assertEqual(an.renaming(SAMPLE), an.renaming(SAMPLE))

    def test_the_placeholders_are_positional(self):
        table = an.renaming(SAMPLE)
        self.assertEqual(table["foo"], "anonvar0")
        self.assertEqual(sorted(table.values()),
                         sorted(an.PLACEHOLDER.format(i)
                                for i in range(len(table))))

    def test_renaming_twice_changes_nothing_further(self):
        once = an.anonymise(SAMPLE)
        self.assertEqual(an.anonymise(once), once)

    def test_the_placeholders_are_fresh_against_the_corpus(self):
        #  The hypothesis of GLM.Anonymous.overlap_anonymise_eq_zero, checked
        #  against the corpus rather than assumed.  A Lean file that spelled a
        #  placeholder would break it, and this test is what would notice.
        self.assertTrue(an.placeholders_are_fresh())


# ===========================================================================
# 2.  WHAT THE RENAMING DOES TO EACH FACULTY
# ===========================================================================

class TestTheLeanPromisesHoldOfTheCode(unittest.TestCase):

    def test_the_structural_reading_survives_a_renaming(self):
        #  GLM.Anonymous.features_anonymise, on the shipped feature map.
        for row in an.anonymous_records()[:40]:
            with self.subTest(name=row.name):
                self.assertTrue(
                    all(i in an.TYPE_COORDINATES for i in row.moved))

    def test_no_coordinate_outside_the_type_vocabulary_ever_moves(self):
        report = an.anonymous_report()
        self.assertEqual(
            report["queries_moved_outside_the_type_vocabulary"], ())

    def test_the_type_vocabulary_can_move_and_that_is_reported(self):
        #  The audit finding: the shipped map reads the type words inside
        #  identifiers too, so a declaration whose name spells one loses the
        #  count.  It is measured, not hidden.
        report = an.anonymous_report()
        self.assertLess(report["invariant_queries"], report["queries"])
        self.assertGreater(report["invariant_queries"],
                           report["queries"] * 9 // 10)

    def test_an_anonymised_query_shares_no_identifier_with_the_corpus(self):
        #  GLM.Anonymous.overlap_anonymise_eq_zero: the text faculty's
        #  confidence is zero by construction.
        vocabulary = an.corpus_vocabulary()
        for name in an.queries()[:40]:
            decl = la.declaration(name)
            text = rt.strip_declaration_head(decl.statement if decl else "")
            with self.subTest(name=name):
                fresh = set(an.renaming(text).values())
                self.assertTrue(all(token.lower() not in vocabulary
                                    for token in fresh))

    def test_the_relay_hands_the_register_over(self):
        #  GLM.Anonymous.relay_hands_over: confidence below the gate, so the
        #  relay is the interleave of the plan.
        for row in an.anonymous_records()[:40]:
            answers = row.anonymous
            if answers["text"].confidence >= sk.GATE:
                continue
            expected = sk.interleave(
                [answers[name].names for name, _ in sk.QUOTAS],
                [quota for _, quota in sk.QUOTAS])
            with self.subTest(name=row.name):
                self.assertEqual(sk.relay(answers), expected)


# ===========================================================================
# 3.  THE MEASUREMENT
# ===========================================================================

class TestTheRegisterAsMeasured(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.report = an.anonymous_report()

    def hits(self, reading: str, faculty: str) -> int:
        return self.report[reading][faculty]["hits"][self.report["k"]]

    def test_the_text_layer_leads_while_the_names_are_there(self):
        self.assertGreater(self.hits("plain", "text"),
                           self.hits("plain", "address"))

    def test_the_text_layer_collapses_without_them(self):
        self.assertLess(self.hits("anonymous", "text") * 5,
                        self.hits("plain", "text"))

    def test_the_identifier_address_book_collapses_with_it(self):
        self.assertLess(self.hits("anonymous", "lexical") * 5,
                        self.hits("plain", "lexical"))

    def test_the_structural_address_holds(self):
        self.assertGreaterEqual(self.hits("anonymous", "address") * 2,
                                self.hits("plain", "address"))

    def test_the_structural_address_leads_every_other_faculty_there(self):
        for faculty in an.SCORED:
            if faculty == "address":
                continue
            with self.subTest(faculty=faculty):
                self.assertGreater(self.hits("anonymous", "address"),
                                   self.hits("anonymous", faculty))

    def test_the_controls_are_at_chance_in_both_readings(self):
        queries = self.report["queries"]
        chance = self.report["chance_at_5"] * queries
        for faculty in ("digest", "random"):
            with self.subTest(faculty=faculty):
                self.assertLess(self.hits("anonymous", faculty), 2 * chance)

    def test_the_gate_fires_on_most_of_the_register(self):
        fired = self.report["relay_anonymous"]["fired"]
        self.assertGreaterEqual(Fraction(fired, self.report["queries"]),
                                Fraction(1, 2))
        self.assertLess(self.report["relay_plain"]["fired"], fired)

    def test_the_relay_lifts_the_leader_in_the_register(self):
        relay = self.report["relay_anonymous"]
        k = self.report["k"]
        self.assertGreater(relay["relay"]["hits"][k],
                           relay["leader"]["hits"][k])

    def test_every_declared_verdict_holds(self):
        for key, value in self.report["verdict"].items():
            with self.subTest(claim=key):
                self.assertTrue(value)

    def test_the_rates_are_exact(self):
        for reading in ("plain", "anonymous"):
            for faculty in an.SCORED:
                rate = self.report[reading][faculty]["hit_rate"][5]
                with self.subTest(reading=reading, faculty=faculty):
                    self.assertIsInstance(rate, Fraction)
        self.assertIsInstance(self.report["chance_at_5"], Fraction)

    def test_the_module_constructs_no_float(self):
        path = (pathlib.Path(an.__file__).resolve())
        self.assertEqual(ex.module_float_sites(path), {})


# ===========================================================================
# 4.  THE RUNTIME, AND THE RECORD
# ===========================================================================

class TestTheSubjectAndThePipelineRow(unittest.TestCase):

    def test_the_subject_is_declared_and_dispatches(self):
        self.assertIn("anonymous", REPORT_SUBJECTS)
        solution = GeometricSession().ask("report anonymous")
        self.assertEqual(solution.kind, "report")
        self.assertIn("anonymous", solution.answer.lower())

    def test_the_answer_states_the_measured_figures(self):
        report = an.anonymous_report()
        solution = GeometricSession().ask("report anonymous register")
        self.assertEqual(solution.expected["queries"],
                         str(report["queries"]))
        self.assertEqual(solution.expected["anonymous_address_hits"],
                         str(report["anonymous"]["address"]["hits"][5]))
        self.assertEqual(solution.expected["fired"],
                         str(report["relay_anonymous"]["fired"]))

    def test_column_three_renders_for_the_subject(self):
        script = tct.render_script(GeometricSession().ask("report anonymous"))
        self.assertIn("anonymous", script)

    def test_the_pipeline_row_names_the_study_the_subject_and_the_lean_file(self):
        row = next(r for r in ppl.REGISTRY if r.key == "anonymous-register")
        self.assertEqual(row.document, "ANONYMOUS_REGISTER_STUDY.md")
        self.assertEqual(row.subject, "anonymous")
        self.assertIn("Anonymous.lean", row.lean)


if __name__ == "__main__":
    unittest.main()
