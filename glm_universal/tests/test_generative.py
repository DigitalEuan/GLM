"""Tests for the generate-vs-store audit: ``reasoning/generative.py``.

Four things are pinned here.

* the **sieve** proposed by the zero-storage script is sound and incomplete,
  and the numbers are the ones the study quotes: 1152 of the 196,560 minimal
  vectors kept, none of them outside the lattice;
* the **repair** is exact -- the one-line fix agrees with the package's own
  membership test on every vector tested, in and out of the lattice;
* the **snap** built on the sieve returns points that are not lattice points,
  while the exact coset decoder beside it is always inside the lattice and
  always within the covering radius, which is what says it is the nearest
  point and not merely a near one;
* the **generators** are measured against certified processes, so a stated
  accuracy that is not delivered is a failing row rather than a docstring.

Everything is exact, and the report subject is exercised end to end.
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.reasoning import generative as gen
from glm_universal.substrate import leech2
from glm_universal.substrate.mog import GOLAY_MASKS


class SieveTests(unittest.TestCase):
    """What the script's Construction A -> B -> C sieve actually generates."""

    def test_sieve_is_sound_and_incomplete(self) -> None:
        report = gen.sieve_shell_report()
        self.assertEqual(report["minimal_vectors"], 196560)
        self.assertEqual(report["unsound"], 0)
        self.assertEqual(report["kept"], 1152)
        self.assertEqual(report["recall"], Fraction(1152, 196560))

    def test_the_octad_vectors_are_the_loss(self) -> None:
        shape = gen.sieve_shell_report()["by_shape"]
        self.assertEqual(shape["2^8 0^16"]["minimal"], 97152)
        self.assertEqual(shape["2^8 0^16"]["kept"], 0)
        self.assertEqual(shape["4^2 0^22"]["kept"], 1104)
        self.assertEqual(shape["3^1 1^23"]["kept"], 48)

    def test_an_octad_vector_is_in_the_lattice_and_rejected(self) -> None:
        octad = next(mask for mask in GOLAY_MASKS
                     if bin(mask).count("1") == 8)
        vector = tuple(2 if (octad >> i) & 1 else 0 for i in range(24))
        self.assertTrue(leech2.in_leech(vector))
        self.assertEqual(sum(v * v for v in vector), 32)
        self.assertFalse(gen.v3_sieve(vector))
        self.assertTrue(gen.corrected_sieve(vector))

    def test_the_repair_is_exact(self) -> None:
        report = gen.sieve_fix_report()
        self.assertTrue(report["exact"])
        self.assertEqual(report["agree"], report["checked"])
        self.assertEqual(report["disagreements"], [])
        # The probe population is not trivially outside-free either way.
        self.assertGreater(report["probe_vectors_outside_lattice"], 0)


class SnapTests(unittest.TestCase):
    """The generated snap against an exact decoder."""

    def test_rounding_to_even_is_not_a_snap(self) -> None:
        vector = tuple([2, 2] + [0] * 22)
        self.assertFalse(leech2.in_leech(vector))

    def test_exact_decoder_is_inside_and_within_the_covering_radius(self) -> None:
        report = gen.snap_report(4)
        self.assertTrue(report["exact_all_in_lattice"])
        self.assertTrue(report["exact_within_covering_radius"])
        for row in report["rows"]:
            self.assertLessEqual(Fraction(row["exact_dist2"]),
                                 gen.COVERING_RADIUS2)

    def test_the_script_snap_leaves_the_lattice(self) -> None:
        report = gen.snap_report(4)
        self.assertEqual(report["v3_outside_lattice"], report["probes"])
        self.assertEqual(report["branches"], {"fallback_even": 4})

    def test_a_target_beside_a_lattice_point_is_recovered_exactly(self) -> None:
        for target in gen.near_lattice_targets(3):
            answer = gen.exact_snap(target)
            self.assertTrue(answer["in_lattice"])
            self.assertEqual(answer["dist2"], Fraction(1, 2))


class StorageTests(unittest.TestCase):
    """What a generator costs, and what the package already generates."""

    def test_every_regenerated_object_matches_the_stored_one(self) -> None:
        report = gen.storage_report()
        self.assertTrue(report["all_verified"])
        self.assertGreater(report["ratio"], 100)
        for row in report["rows"]:
            self.assertTrue(row["verified"], row["object"])
            self.assertNotIn("regenerate_us", row)

    def test_the_storage_report_reads_no_clock(self) -> None:
        """It is emitted through the runtime, whose traces must reproduce."""
        self.assertEqual(gen.storage_report.__wrapped__(),
                         gen.storage_report.__wrapped__())

    def test_the_overlay_mostly_stores_caches(self) -> None:
        report = gen.repo_storage_report()
        self.assertTrue(report["all_present"])
        self.assertGreater(report["generated_fraction"], Fraction(99, 100))
        self.assertGreater(report["primary_bytes"], 0)


class GeneratorAccuracyTests(unittest.TestCase):
    """A process is a number only when its error is a function of the work."""

    def test_machin_and_taylor_deliver(self) -> None:
        rows = {row["constant"]: row
                for row in gen.exact_real_report()["rows"]}
        self.assertGreater(rows["pi (Machin, 20 terms)"]["bits_correct"], 64)
        self.assertGreater(rows["e (Taylor, 20 terms)"]["bits_correct"], 32)

    def test_the_stated_accuracies_that_fail(self) -> None:
        report = gen.exact_real_report()
        rows = {row["constant"]: row for row in report["rows"]}
        self.assertLess(rows["ln2 (alternating, precision=64)"]
                        ["bits_correct"], 16)
        self.assertLess(rows["gamma (H_n - ln2*bit_length, precision=8)"]
                        ["bits_correct"], 8)
        self.assertEqual(report["claims_met"], 0)
        self.assertEqual(report["claims_made"], 3)

    def test_the_babylonian_iterate_doubles_in_length(self) -> None:
        report = gen.exact_real_report()
        self.assertTrue(report["babylonian_doubles"])
        growth = report["babylonian_denominator_bits"]
        self.assertGreater(growth[-1], 1000)


class SextetTests(unittest.TestCase):
    """The deep-hole tie is real; the label put on it is constant."""

    def test_the_sextet_is_there_and_the_label_is_not(self) -> None:
        report = gen.sextet_label_report()
        self.assertEqual(report["sextet_confirmed"],
                         report["weight4_words_checked"])
        self.assertEqual(report["pairwise_distance_8"],
                         report["weight4_words_checked"])
        self.assertTrue(report["label_is_constant"])


class ReportSubjectTests(unittest.TestCase):
    """The subject dispatches, and says what the study says."""

    def test_report_generated(self) -> None:
        from glm_universal.runtime.session import (REPORT_SUBJECTS,
                                                   GeometricSession)
        self.assertIn("generated", REPORT_SUBJECTS)
        solution = GeometricSession().ask("report generated")
        self.assertEqual(solution.kind, "report")
        self.assertEqual(solution.expected["sieve_kept"], "1152")
        self.assertEqual(solution.expected["sieve_unsound"], "0")
        self.assertEqual(solution.expected["fix_exact"], "True")
        self.assertEqual(solution.expected["verdict_sieve_sound"], "True")
        self.assertEqual(solution.expected["verdict_sieve_complete"], "False")
        self.assertEqual(solution.script_spec["template"], "report_generated")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
