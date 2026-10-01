"""The 106 unresolved laws triaged, pinned.

``glm_universal.reasoning.law_triage`` is the computational half of
``studies/LAW_TRIAGE_STUDY.md`` (Phase 83): one fate per law under the
service rule (a law comes in only if it does measurable work), the declared
checks computed exactly from the substrate.
"""

from __future__ import annotations

import pathlib
import unittest
import zipfile
from fractions import Fraction

from glm_universal.reasoning import law_triage as lt


class TestOneFatePerLaw(unittest.TestCase):

    def test_the_106_and_their_fates(self):
        ids = [r["id"] for r in lt.load()["laws"]]
        self.assertEqual(len(ids), 106)
        self.assertEqual(set(ids), set(lt.FATE))

    def test_counts(self):
        r = lt.law_triage_report()
        self.assertEqual(r["counts"], {"absorbed": 0, "already served": 3,
                                       "refuted": 3, "retired": 100})
        self.assertEqual(sum(r["reasons"].values()), 100)
        self.assertEqual(r["reasons"]["PIPELINE"], 42)
        self.assertEqual(r["reasons"]["WORLD"], 31)
        self.assertEqual(r["met"], r["of"])

    def test_retired_iff_reason(self):
        for fate, reason, note in lt.FATE.values():
            self.assertEqual(fate == "retired", reason is not None)
            self.assertTrue(note)


class TestTheChecks(unittest.TestCase):

    def test_every_check_as_declared(self):
        for law in lt.CHECKS:
            self.assertTrue(lt.check(law)["as_declared"], law)

    def test_hemispheric(self):
        c = lt.check("LAW_HEMISPHERIC_COHERENCE_001")
        self.assertGreater(c["right"]["1/20"], Fraction(97, 100))
        self.assertEqual(c["first_rate_below_51_percent"], Fraction(3, 20))

    def test_particles_are_codewords_eight_apart(self):
        c = lt.check("LAW_PARTICLE_6D")
        self.assertTrue(c["carriers_are_codewords"])
        self.assertEqual(c["electron_positron"], 8)
        self.assertEqual(c["lepton_quark"], [8, 12, 16])

    def test_leech_has_no_norm_two(self):
        self.assertEqual(lt.check("LAW_LEPTON_004")["least_norm"], 4)

    def test_parity(self):
        c = lt.check("LAW_COSMO_003")
        self.assertEqual(c["even_fraction_words"], Fraction(1, 2))
        self.assertEqual(c["even_fraction_code"], 1)

    def test_squeeze_is_fifteen_bits(self):
        c = lt.check("LAW_SQUEEZE_001")
        self.assertEqual(c["bits"], 15)
        self.assertEqual(c["fraction_of_states"], Fraction(1, 512))


class TestServedAndSource(unittest.TestCase):

    def test_served_callables_run(self):
        for law, row in lt.served().items():
            self.assertTrue(row["ok"], law)

    def test_source(self):
        archive = pathlib.Path(__file__).resolve().parents[3] / lt.ZIP_PATH
        if not archive.exists():
            self.skipTest("the archive is not present")
        raw = zipfile.ZipFile(archive).read(lt.KB_MEMBER)
        s = lt.source_check(raw)
        self.assertTrue(s["passed"])
        self.assertEqual(s["texts_equal"], 106)
        self.assertEqual(lt.law_triage_report(raw)["marks"]["B5"], True)


if __name__ == "__main__":
    unittest.main()
