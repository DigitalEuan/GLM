"""Tests for :mod:`glm_universal.reasoning.stability`.

Four things are pinned here:

* the **arithmetic is exact** -- every radius, residual and perturbation is a
  :class:`~fractions.Fraction` or an ``int``, and the two certificates are the
  hypotheses of ``RequestProject/GLM/Stability.lean`` transcribed, so a change
  in either has to be a deliberate one;
* the **radius is the radius** -- for a declaration whose radius the shell
  test certifies as exact, a perturbation strictly inside it leaves the
  address alone and the perturbation the theorem constructs just outside it
  does not, decoded by the quantiser rather than argued about;
* the **census is honest** -- an address at radius zero really is equidistant
  from two lattice points, and the histogram accounts for every declaration
  it measured;
* the **read-back outlives the address** -- stepping a feature by one whole
  unit moves the read-back in exactly the coordinate that was stepped.
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.reasoning import lean_address as la
from glm_universal.reasoning import stability as st
from glm_universal.substrate import leech2


# ===========================================================================
# 1.  THE CERTIFICATES ARE THE LEAN HYPOTHESES
# ===========================================================================

class TestTheCertificates(unittest.TestCase):

    def test_the_packing_certificate_is_the_lean_inequality(self):
        # `isNearest_of_sq_data`: 4D + 4E <= m^2 and 64 D E <= (m^2-4D-4E)^2.
        for D in (Fraction(0), Fraction(1, 4), Fraction(1), Fraction(3)):
            for E in (Fraction(0), Fraction(1), Fraction(4), Fraction(8),
                      Fraction(11)):
                with self.subTest(D=D, E=E):
                    slack = Fraction(st.MIN_NORM2) - 4 * D - 4 * E
                    wanted = slack >= 0 and 64 * D * E <= slack ** 2
                    self.assertEqual(st.certified_safe(D, E), wanted)

    def test_the_packing_certificate_is_silent_outside_the_ball(self):
        # A residual at or past the squared packing radius leaves nothing to
        # certify: the bound needs 4E < m^2 before any perturbation fits.
        self.assertFalse(st.certified_safe(Fraction(1, 64), Fraction(8)))
        self.assertTrue(st.certified_safe(Fraction(1), Fraction(1)))

    def test_the_shell_certificate_is_the_lean_inequality(self):
        for A in (Fraction(0), Fraction(1, 8), Fraction(1, 2), Fraction(9, 8)):
            for E in (Fraction(5), Fraction(8), Fraction(11), Fraction(16)):
                with self.subTest(A=A, E=E):
                    limit = Fraction(st.NEXT_SHELL_NORM2, 4)
                    slack = limit - A - E
                    wanted = slack >= 0 and 4 * A * E <= slack ** 2
                    self.assertEqual(st.shell_certified(A, E), wanted)

    def test_no_float_is_constructed(self):
        record = st.stability_radius("GLM.Address.Quantiser")
        self.assertIsInstance(record["radius2"], Fraction)
        self.assertIsInstance(record["residual2"], Fraction)
        self.assertIsInstance(record["crossing"], Fraction)
        for coordinate in record["address"]:
            self.assertIsInstance(coordinate, int)


# ===========================================================================
# 2.  THE RADIUS IS THE NEAREST BISECTOR
# ===========================================================================

class TestTheRadius(unittest.TestCase):

    def test_the_best_competitor_is_a_minimal_vector(self):
        record = st.stability_radius("GLM.Address.Quantiser")
        vector = list(record["competitor"])
        self.assertEqual(leech2.norm2(vector), st.MIN_NORM2)
        self.assertTrue(leech2.in_leech(vector))

    def test_the_radius_is_the_distance_to_that_bisector(self):
        # radius = (|v|^2 - 2<d,v>) / (2|v|); squared, it is what is reported.
        name = "GLM.Address.Quantiser"
        features = la.feature_table()[name]
        vector = st.scaled_input(features)
        point, _ = st.decode(vector)
        offset = st.residual(vector, point)
        competitor = st.best_competitor(offset)
        inner = sum(a * b for a, b in zip(offset, competitor["vector"]))
        gap = Fraction(st.MIN_NORM2) - 2 * inner
        self.assertEqual(competitor["radius2"],
                         gap ** 2 / (4 * st.MIN_NORM2))
        self.assertEqual(competitor["crossing"], gap / (2 * st.MIN_NORM2))

    def test_a_zero_radius_really_is_a_tie(self):
        # An address at radius zero is equidistant from two lattice points.
        for name in st.corpus_names(24):
            record = st.stability_radius(name)
            if not record["on_a_bisector"]:
                continue
            with self.subTest(name=name):
                point = record["address"]
                rival = tuple(a + b for a, b in
                              zip(point, record["competitor"]))
                vector = st.scaled_input(record["features"])
                here = sum((Fraction(a) - b) ** 2
                           for a, b in zip(vector, point))
                there = sum((Fraction(a) - b) ** 2
                            for a, b in zip(vector, rival))
                self.assertEqual(here, there)
                self.assertEqual(here, record["residual2"])
            break

    def test_the_witness_holds_inside_and_moves_outside(self):
        checked = 0
        for name in st.corpus_names(8):
            witness = st.crossing_witness(name)
            with self.subTest(name=name):
                self.assertTrue(witness["outside_moves"])
                if witness["strict_inside"]:
                    self.assertTrue(witness["inside_holds"])
                    checked += 1
        self.assertGreater(checked, 0)

    def test_the_flip_lands_on_the_competitor(self):
        witness = st.crossing_witness("GLM.Address.Quantiser")
        self.assertTrue(witness["outside_is_the_competitor"])


# ===========================================================================
# 3.  THE CENSUS AND THE SWEEP
# ===========================================================================

class TestTheCensus(unittest.TestCase):

    def test_the_histogram_accounts_for_every_declaration(self):
        census = st.radius_census(limit=8)
        self.assertEqual(sum(census["radius2_histogram"].values()),
                         census["declarations"])
        self.assertEqual(census["radius2_histogram"].get("0", 0),
                         census["on_a_bisector"])

    def test_the_residuals_sit_where_the_study_says(self):
        census = st.radius_census(limit=8)
        self.assertGreaterEqual(census["residual2_min"], 0)
        self.assertLessEqual(census["residual2_max"],
                             Fraction(st.MIN_NORM2, 2))

    def test_nothing_certified_ever_moved(self):
        sweep = st.perturbation_sweep(limit=4)
        self.assertEqual(sweep["certificate_violations"], 0)
        self.assertEqual(sweep["radius_violations"], 0)

    def test_the_sweep_declares_its_perturbations_exactly(self):
        sweep = st.perturbation_sweep(limit=2, steps=(Fraction(1, 8),),
                                      directions=("uniform",))
        row = sweep["rows"][0]
        # 24 coordinates each moved by 1/8: squared norm 24/64 = 3/8.
        self.assertEqual(row["size2"], Fraction(3, 8))
        self.assertLessEqual(row["address_kept"], row["declarations"])

    def test_a_whole_feature_unit_changes_everything(self):
        sweep = st.perturbation_sweep(limit=2, steps=(Fraction(st.SCALE),),
                                      directions=("uniform",))
        row = sweep["rows"][0]
        self.assertEqual(row["address_kept"], 0)
        self.assertEqual(row["reading_kept"], 0)

    def test_the_certificate_probe_is_exercised_and_sound(self):
        probe = st.certificate_probe(points=4, offsets=2)
        self.assertTrue(probe["available"])
        self.assertGreater(probe["checked"], 0)
        self.assertEqual(probe["violations"], 0)


# ===========================================================================
# 4.  THE READ-BACK
# ===========================================================================

class TestTheReadBack(unittest.TestCase):

    def test_the_read_back_follows_a_feature_step(self):
        report = st.feature_step_report(limit=4, steps=2)
        self.assertGreater(report["steps"], 0)
        self.assertEqual(report["read_back_tracks_the_step"],
                         report["steps"])

    def test_the_report_assembles_and_agrees_with_itself(self):
        report = st.stability_report(limit=4, witnesses=1)
        self.assertTrue(report["witnesses_agree"])
        self.assertEqual(report["min_norm2"], leech2.MIN_NORM2)
        self.assertEqual(report["scale"], la.SCALE)
        self.assertEqual(report["census"]["declarations"], 4)
        self.assertEqual(report["sweep"]["radius_violations"], 0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
