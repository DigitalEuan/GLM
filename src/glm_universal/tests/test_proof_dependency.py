"""What a Lean result rests on (Phase 101): the dependency operation over the
elaborator's citation graph, against the marks declared in
``studies/CITATION_SCOPE_STUDY.md`` §2.1 before its code existed.
"""

from __future__ import annotations

import unittest

from glm_universal.reasoning import proof_dependency as pd
from glm_universal.runtime import dependency_frames as df
from glm_universal.runtime import dependency_report as dr
from glm_universal.runtime import question_frames as qf

_REPORT = None


def report():
    global _REPORT
    if _REPORT is None:
        _REPORT = dr.dependency_report()
    return _REPORT


class TestThePhrasings(unittest.TestCase):

    def test_three_phrasings_are_read(self):
        self.assertEqual("rests_on",
                         df.match_raw("does A.b rest on C.d?")["kind"])
        self.assertEqual("rests_on",
                         df.match_raw("Does x depend on y")["kind"])
        self.assertEqual("closure",
                         df.match_raw("what does A.b rest on")["kind"])
        self.assertEqual("dependents",
                         df.match_raw("what rests on A.b?")["kind"])
        self.assertEqual("dependents",
                         df.match_raw("which declarations rest on A")["kind"])
        self.assertIsNone(df.match_raw("what is the mass of iron"))

    def test_the_frame_layer_reads_them(self):
        got = qf.frame_of("does GLM.CitationScope.cites_mem rest on "
                          "GLM.CitationScope.resolve_mem")
        self.assertIsNotNone(got)
        self.assertEqual("proof_dependency", got[0].name)


class TestTheSearch(unittest.TestCase):

    def test_a_path_is_made_of_edges(self):
        g = pd.graph()
        path = pd.shortest_path("GLM.CitationScope.cites_antitone",
                                "GLM.CitationScope.prefixes")
        self.assertIsNotNone(path)
        for a, b in zip(path, path[1:]):
            self.assertIn(b, g[a])

    def test_closure_and_dependents_are_inverse(self):
        name = "GLM.CitationScope.prefixes"
        for user in pd.dependents(name).members:
            self.assertIn(name, pd.closure(user))

    def test_an_ambiguous_name_is_read_in_the_other_names_scope(self):
        ans = pd.rests_on("resolve_first", "candidates")
        self.assertEqual("GLM.CitationScope.candidates", ans.target)
        with self.assertRaises(pd.DependencyError) as caught:
            pd.lookup("candidates")
        self.assertEqual("AMBIGUOUS_NAME", caught.exception.code)


class TestTheMarks(unittest.TestCase):

    def test_d1_as_declared_and_after_the_repair(self):
        first = report()["as_declared"]
        self.assertEqual((7, 0, 5), (first["right"], first["wrong"],
                                     first["refused"]))
        self.assertEqual(["AMBIGUOUS_NAME"], first["codes"])
        self.assertFalse(report()["marks"]["D1"])
        self.assertTrue(report()["marks"]["D1_after_repair"])
        self.assertEqual(0, report()["wrong"])

    def test_d2_gates_and_mutations(self):
        self.assertTrue(report()["marks"]["D2"])

    def test_d3_refusals(self):
        self.assertTrue(report()["marks"]["D3"])


if __name__ == "__main__":
    unittest.main()
