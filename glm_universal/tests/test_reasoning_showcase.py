"""Tests for the reasoning showcase.

The showcase in ``glm_universal/examples/reasoning_showcase.py`` is the
evidence behind ``REASONING_CAPABILITY.md``.  It is therefore held to the
same standard as any other claim in the package: it is a test, not a demo.

What is pinned here:

* every probe expected to be answered *is* answered, and every probe expected
  to be refused *is* refused (a refusal silently becoming an answer is as
  much a regression as the reverse);
* every answered probe carries a reasoning chain with both columns filled and
  at least one falsifiable claim;
* every answered probe renders a column-3 script that is float-free;
* a representative sample of probes actually verifies end to end in a fresh
  interpreter.

The full end-to-end verification of all probes is deliberately *not* run
here -- it spawns one subprocess per probe and takes minutes.  Run the script
itself for that.
"""

from __future__ import annotations

import io
import unittest

from glm_universal.examples import reasoning_showcase as SHOW
from glm_universal.runtime import tct_engine as TE
from glm_universal.runtime.session import GeometricSession

#: One probe from each section, verified end to end.  Kept short on purpose.
SAMPLED = (
    "verify energy = mass * speed_of_light^2",
    "coherence of planck_constant",
    "force : energy :: pressure : ?",
    "project energy torque",
    "task concepts",
    "task grid",
)


def all_probes():
    for section in SHOW.SECTIONS:
        for probe in section.probes:
            yield section, probe


class TestShowcaseStructure(unittest.TestCase):

    def test_sections_are_non_empty(self):
        self.assertTrue(SHOW.SECTIONS)
        for section in SHOW.SECTIONS:
            with self.subTest(section=section.title):
                self.assertTrue(section.probes)
                self.assertTrue(section.blurb)

    def test_every_probe_says_why_it_is_asked(self):
        for _, probe in all_probes():
            with self.subTest(query=probe.query):
                self.assertTrue(probe.why.strip())

    def test_queries_are_unique(self):
        queries = [p.query for _, p in all_probes()]
        self.assertEqual(len(queries), len(set(queries)))

    def test_there_is_a_section_of_refusals(self):
        refused = [p for _, p in all_probes() if p.expect_unsolved]
        self.assertGreaterEqual(len(refused), 3)


class TestEveryProbeBehaves(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.session = GeometricSession()
        cls.solutions = {p.query: cls.session.ask(p.query)
                         for _, p in all_probes()}

    def test_answered_probes_are_answered(self):
        for _, probe in all_probes():
            if probe.expect_unsolved:
                continue
            with self.subTest(query=probe.query):
                sol = self.solutions[probe.query]
                self.assertTrue(sol.ok, sol.answer)
                self.assertTrue(sol.answer.strip())

    def test_refused_probes_are_refused(self):
        for _, probe in all_probes():
            if not probe.expect_unsolved:
                continue
            with self.subTest(query=probe.query):
                sol = self.solutions[probe.query]
                self.assertFalse(sol.ok, sol.answer)

    def test_a_refusal_explains_itself(self):
        for _, probe in all_probes():
            if not probe.expect_unsolved:
                continue
            with self.subTest(query=probe.query):
                # Either it names the offending token, or it lists the query
                # kinds it does support.  Never a bare failure.
                answer = self.solutions[probe.query].answer
                self.assertTrue(len(answer) > 20, answer)

    def test_answered_probes_have_both_columns(self):
        for _, probe in all_probes():
            if probe.expect_unsolved:
                continue
            with self.subTest(query=probe.query):
                sol = self.solutions[probe.query]
                self.assertTrue(sol.steps)
                for step in sol.steps:
                    self.assertTrue(step.language.strip())
                    self.assertTrue(step.mathematics.strip())

    def test_answered_probes_commit_to_claims(self):
        for _, probe in all_probes():
            if probe.expect_unsolved:
                continue
            with self.subTest(query=probe.query):
                self.assertTrue(self.solutions[probe.query].expected)

    def test_every_generated_script_is_float_free(self):
        for _, probe in all_probes():
            if probe.expect_unsolved:
                continue
            with self.subTest(query=probe.query):
                sol = self.solutions[probe.query]
                script = TE.render_script(sol)
                ok, offenders = TE.script_is_exact(script)
                self.assertTrue(ok, f"{probe.query}: {offenders}")


class TestSampledProbesVerify(unittest.TestCase):
    """Column 3 actually agrees with column 2, for a sample."""

    @classmethod
    def setUpClass(cls):
        cls.session = GeometricSession()

    def test_sampled_probes_verify_end_to_end(self):
        known = {p.query for _, p in all_probes()}
        for query in SAMPLED:
            with self.subTest(query=query):
                self.assertIn(query, known)
                sol = self.session.ask(query)
                trace = TE.verify_trace(TE.build_trace(sol), timeout=180)
                self.assertTrue(trace.verdict.executed,
                                trace.verdict.stderr_tail)
                self.assertEqual(trace.verdict.mismatches, ())
                self.assertEqual(trace.verdict.missing_keys, ())
                self.assertTrue(trace.verified)


class TestShowcaseRuns(unittest.TestCase):
    """The driver itself, in its fast mode, reports no surprises."""

    def test_run_without_verification_reports_zero_unexpected(self):
        buffer = io.StringIO()
        failures = SHOW.run(verify=False, stream=buffer)
        self.assertEqual(failures, 0, buffer.getvalue()[-2000:])

    def test_markdown_mode_produces_markdown(self):
        buffer = io.StringIO()
        SHOW.run(markdown=True, verify=False, only="1.", stream=buffer)
        text = buffer.getvalue()
        self.assertIn("# GLM reasoning showcase", text)
        self.assertIn("### `verify energy = mass * speed_of_light^2`", text)

    def test_only_filter_restricts_the_run(self):
        buffer = io.StringIO()
        SHOW.run(verify=False, only="no such section", stream=buffer)
        self.assertIn("probes run     : 0", buffer.getvalue())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
