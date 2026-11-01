"""Tests for ``glm_universal.corpus.study_ledger`` -- the predecessor graph
of the studies, read through the shared manifest loader.

*Created 31 October 2026 (repository check of the YAML study system).  The
Phase 161 test file of this name (7 tests) was lost in the October 2026
reorganisation; these tests are written for the rebuilt ledger.*
"""
from __future__ import annotations

import unittest
from unittest import mock

try:
    import yaml as _yaml
except ImportError:  # pragma: no cover
    _yaml = None

from glm_universal import constants as C
from glm_universal.corpus import study_ledger as sl
from glm_universal.corpus import study_manifest as sm


def _graph(edges, phases):
    return {sid: {"id": sid, "schema": sm.SCHEMA_NAME, "phase": phases[sid],
                  "predecessors": list(edges.get(sid, ())),
                  "file_refs": {"prose": sid + ".md"}}
            for sid in phases}


class TestGraphChecks(unittest.TestCase):

    def test_cycle_found_and_reported(self):
        graph = _graph({"A": ["B"], "B": ["C"], "C": ["A"]},
                       {"A": 3, "B": 2, "C": 1})
        acyclic, cycle = sl._check_acyclic(graph)
        self.assertFalse(acyclic)
        self.assertEqual(cycle[0], cycle[-1])
        self.assertEqual(set(cycle), {"A", "B", "C"})

    def test_long_chain_is_not_recursive(self):
        n = 5000
        phases = {f"S{i}": i + 1 for i in range(n)}
        edges = {f"S{i}": [f"S{i - 1}"] for i in range(1, n)}
        self.assertEqual(sl._check_acyclic(_graph(edges, phases)), (True, []))

    def test_ledger_reads_the_shared_loader(self):
        graph = _graph({"B": ["A"], "C": ["A", "B", "GONE"]},
                       {"A": 1, "B": 2, "C": 0})
        with mock.patch.object(sm, "load_manifests", return_value=graph):
            led = sl.ledger()
            issues = sl.ledger_issues(led)
            tamper = sl.tamper_control()
        self.assertEqual(led["counts"]["studies"], 3)
        self.assertEqual(led["edges"], 4)
        self.assertEqual(led["studies"][0]["successors"], ["B", "C"])
        kinds = sorted({kind for _s, kind, _d in issues})
        self.assertEqual(kinds, ["missing predecessor", "no phase",
                                 "predecessor not earlier"])
        self.assertEqual(tamper, {"tampered": 3, "caught": 3})


@unittest.skipUnless(_yaml is not None, "PyYAML not installed")
class TestTheRepository(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.led = sl.ledger()
        cls.report = sl.study_ledger_report()

    def test_loads_every_manifest(self):
        self.assertEqual(self.led["counts"]["studies"],
                         len(list(C.STUDIES_DIR.glob("*.yaml"))))
        self.assertEqual(sl.STUDIES_DIR, C.STUDIES_DIR)

    def test_acyclic_with_edges(self):
        self.assertTrue(self.led["acyclic"], self.led["cycle"])
        self.assertGreater(self.led["edges"], 100)

    def test_every_edge_is_to_an_earlier_phase(self):
        kinds = {kind for _s, kind, _d in sl.ledger_issues(self.led)}
        self.assertNotIn("predecessor not earlier", kinds)
        self.assertNotIn("missing predecessor", kinds)
        self.assertNotIn("cycle", kinds)

    def test_tamper_control_sees_every_reversal(self):
        self.assertEqual(self.report["tampered"], sl.TAMPER_EDGES)
        self.assertEqual(self.report["tamper_caught"], sl.TAMPER_EDGES)
        self.assertTrue(self.report["holds"])
        self.assertEqual(self.report["met"], self.report["taken"])

    def test_missing_files_names_the_recorded_gaps(self):
        report = sl.missing_files()
        lean_missing = {(s, ref) for s, kind, ref in report["missing"]
                        if kind == "lean"}
        for sid, data in sm.load_manifests().items():
            for ref in data["file_refs"].get("lean_missing", []):
                self.assertIn((sid, ref), lean_missing)
        self.assertFalse(sl.untracked_files()["measured"])


if __name__ == "__main__":
    unittest.main()
