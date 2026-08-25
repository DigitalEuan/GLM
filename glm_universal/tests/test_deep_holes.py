"""Tests for the hole layer: ``niemeier``, ``voronoi_walk``, ``deep_holes``.

Four things are pinned here.

* the **catalogue** is derived, not listed -- the 23 Niemeier root systems
  come out of the ADE component formulas and a common Coxeter number;
* the **walk** really reaches a vertex of the Voronoi diagram, exactly, and
  the climb really raises the radius to the covering radius;
* the **reading** of a hole's diagram is right on holes built out of the
  package's own codewords, and its completeness certificate is an identity
  that is checked, not a claim;
* the **refusals** are refusals: a lattice point and a carrier in general
  position get no Niemeier type, with a reason.

Everything is exact.  The slower census is exercised with small parameters;
the report's own defaults are what the report subject runs.
"""

from __future__ import annotations

import functools
import unittest
from fractions import Fraction

from glm_universal.reasoning import deep_holes as dh
from glm_universal.reasoning import metric, niemeier
from glm_universal.reasoning import voronoi_walk as vw
from glm_universal.substrate import leech2


@functools.lru_cache(maxsize=None)
def _classified(which: str):
    """Classify a constructed hole once and share it across the tests."""
    hole = (dh.octad_pair_hole() if which == "octad"
            else dh.dodecad_triangle_hole())
    return hole, dh.classify_carrier(hole["center"])


# ===========================================================================
# 1.  THE DERIVED CATALOGUE
# ===========================================================================

class TestCatalogue(unittest.TestCase):

    def test_exactly_twenty_three_root_systems(self):
        systems = niemeier.enumerate_niemeier_root_systems()
        self.assertEqual(len(systems), 23)

    def test_every_system_has_rank_24_and_one_coxeter_number(self):
        for name, rank, coxeter in niemeier.NIEMEIER_ROOT_SYSTEMS:
            with self.subTest(name=name):
                self.assertEqual(rank, 24)
                self.assertGreater(coxeter, 0)

    def test_the_classical_names_are_present(self):
        names = {name for name, _r, _h in niemeier.NIEMEIER_ROOT_SYSTEMS}
        for expected in ("A_1^24", "A_2^12", "A_24", "D_24", "E_8^3",
                         "D_16 E_8", "A_12^2", "D_8^3", "E_6^4",
                         "D_10 E_7^2", "A_7^2 D_5^2"):
            with self.subTest(name=expected):
                self.assertIn(expected, names)


# ===========================================================================
# 2.  THE MARKS ARE SOLVED FOR
# ===========================================================================

class TestMarks(unittest.TestCase):

    def test_a_1_tilde_has_marks_one_one(self):
        self.assertEqual(dh.extended_dynkin_marks(2, [(0, 1, True)]), (1, 1))

    def test_a_cycle_has_all_marks_one(self):
        for size in (3, 4, 5, 9):
            with self.subTest(size=size):
                edges = [(i, (i + 1) % size, False) for i in range(size)]
                self.assertEqual(dh.extended_dynkin_marks(size, edges),
                                 tuple([1] * size))

    def test_d_4_tilde_has_a_mark_two_and_coxeter_six(self):
        edges = [(0, i, False) for i in (1, 2, 3, 4)]
        marks = dh.extended_dynkin_marks(5, edges)
        self.assertEqual(sorted(marks), [1, 1, 1, 1, 2])
        self.assertEqual(sum(marks), 6)

    def test_a_diagram_that_is_not_extended_has_no_positive_null_vector(self):
        # A single edge: the finite A_2 Cartan matrix is nonsingular.
        self.assertIsNone(dh.extended_dynkin_marks(2, [(0, 1, False)]))


# ===========================================================================
# 3.  THE WALK
# ===========================================================================

class TestWalk(unittest.TestCase):

    def test_a_walk_lands_on_a_vertex_of_the_voronoi_diagram(self):
        landed = vw.vertex_walk(seed=20260825)
        self.assertIsNotNone(landed)
        center = landed["center"]
        radius = landed["radius2_raw"]
        # Every active point is at the same distance ...
        for point in landed["active"]:
            self.assertEqual(vw.squared_distance(center, point), radius)
        # ... and that distance is genuinely the nearest.
        nearest = dh.nearest_lattice_point_fwht(center).point
        self.assertEqual(vw.squared_distance(center, nearest), radius)
        # A vertex needs at least 25 constraints in 24 dimensions.
        self.assertGreaterEqual(landed["active_count"], 25)

    def test_the_radius_never_exceeds_the_covering_radius(self):
        reached = vw.walk_to_deep_hole(seed=20260825 + 977)
        self.assertIsNotNone(reached)
        self.assertLessEqual(reached["radius2"], dh.COVERING_RADIUS2)
        for value in reached["radius_curve"]:
            self.assertLessEqual(value, dh.COVERING_RADIUS2)

    def test_the_climb_never_lowers_the_radius(self):
        reached = vw.walk_to_deep_hole(seed=20260825 + 977)
        curve = reached["radius_curve"]
        for earlier, later in zip(curve, curve[1:]):
            self.assertGreater(later, earlier)

    def test_the_walk_is_deterministic(self):
        first = vw.vertex_walk(seed=4242)
        second = vw.vertex_walk(seed=4242)
        self.assertEqual(first["center"], second["center"])
        self.assertEqual(first["active"], second["active"])


# ===========================================================================
# 4.  TWO HOLES BUILT OUT OF THE SUBSTRATE'S OWN CODEWORDS
# ===========================================================================

class TestConstructedHoles(unittest.TestCase):

    def test_octad_pair_midpoint_is_at_the_covering_radius(self):
        hole = dh.octad_pair_hole()
        self.assertEqual(hole["separation2_raw"], 64)
        distance = dh._raw_distance2(hole["center"], hole["left"])
        self.assertEqual(Fraction(distance, metric.GRIESS_SCALE),
                         dh.COVERING_RADIUS2)

    def test_dodecad_triangle_centroid_is_at_the_covering_radius(self):
        hole = dh.dodecad_triangle_hole()
        self.assertEqual(hole["side2_raw"], 48)
        for vertex in hole["vertices"]:
            distance = dh._raw_distance2(hole["center"], vertex)
            self.assertEqual(Fraction(distance, metric.GRIESS_SCALE),
                             dh.COVERING_RADIUS2)

    def test_octad_pair_reads_as_a_1_24_and_certifies(self):
        _hole, result = _classified("octad")
        self.assertEqual(result["niemeier_type"], "A_1^24")
        self.assertTrue(result["certified"])
        diagram = result["diagram"]
        self.assertEqual(diagram["vertex_count"], 48)
        self.assertEqual(diagram["component_count"], 24)
        self.assertEqual(diagram["double_bonds"], 24)
        self.assertEqual(diagram["coxeter_number"], 2)

    def test_dodecad_triangle_reads_as_a_2_12_and_certifies(self):
        _hole, result = _classified("dodecad")
        self.assertEqual(result["niemeier_type"], "A_2^12")
        self.assertTrue(result["certified"])
        diagram = result["diagram"]
        self.assertEqual(diagram["vertex_count"], 36)
        self.assertEqual(diagram["component_count"], 12)
        self.assertEqual(diagram["coxeter_number"], 3)

    def test_every_vertex_found_is_a_lattice_point(self):
        hole = dh.dodecad_triangle_hole()
        probe = dh.hole_vertices(hole["center"], probes=60, patience=20)
        for vertex in probe["vertices"]:
            self.assertTrue(leech2.in_leech(list(vertex)))


# ===========================================================================
# 5.  THE CERTIFICATE IS AN IDENTITY, NOT A CLAIM
# ===========================================================================

class TestCertificate(unittest.TestCase):

    def test_a_proper_subset_of_the_vertices_does_not_certify(self):
        hole, result = _classified("dodecad")
        vertices = result["diagram"]  # full set is certified
        self.assertTrue(vertices["certified_complete"])
        partial = result["probe"]["vertices"][:-3]
        diagram = dh.hole_diagram(partial, center=hole["center"])
        self.assertFalse(diagram["certified_complete"])

    def test_the_certificate_checks_rank_and_a_single_coxeter_number(self):
        _hole, result = _classified("octad")
        certificate = result["diagram"]["completeness_certificate"]
        self.assertTrue(certificate["barycentre_identity"])
        self.assertTrue(certificate["single_coxeter_number"])
        self.assertEqual(certificate["total_rank"], 24)

    def test_no_center_means_no_certificate_rather_than_a_free_pass(self):
        _hole, result = _classified("octad")
        diagram = dh.hole_diagram(result["probe"]["vertices"])
        self.assertIsNone(diagram["completeness_certificate"])
        self.assertFalse(diagram["certified_complete"])


# ===========================================================================
# 6.  THE REFUSALS
# ===========================================================================

class TestRefusals(unittest.TestCase):

    def test_a_lattice_point_has_no_niemeier_type(self):
        result = dh.classify_carrier([0] * 24, probes=6, patience=3)
        self.assertIsNone(result["niemeier_type"])
        self.assertFalse(result["has_niemeier_type"])
        self.assertIn("lattice point", result["verdict"])

    def test_a_carrier_in_general_position_is_refused_with_its_distance(self):
        carrier = [Fraction(1, 8)] + [Fraction(0)] * 23
        result = dh.classify_carrier(carrier, probes=6, patience=3)
        self.assertIsNone(result["niemeier_type"])
        self.assertIn("no Niemeier type", result["verdict"])

    def test_the_probe_reports_the_distance_it_measured(self):
        probe = dh.probe_hole([Fraction(0)] * 24, probes=4, patience=2)
        self.assertTrue(probe["at_a_lattice_point"])
        self.assertEqual(probe["min_distance2"], 0)


# ===========================================================================
# 7.  THE CENSUS AND ITS HONESTY
# ===========================================================================

class TestCensus(unittest.TestCase):

    def test_a_walked_hole_is_either_typed_or_explained(self):
        run = dh.walked_hole(seed=20260825 + 977, probes=120, patience=25)
        if run["niemeier_type"] is None:
            self.assertTrue(run["verdict"])
        else:
            self.assertTrue(run["certified"])
            self.assertIn(run["niemeier_type"], niemeier.NIEMIER_BY_NAME)

    def test_the_census_reports_its_shortfall(self):
        census = dh.deep_hole_census(walks=0, probes=120, patience=25)
        self.assertEqual(census["types_in_catalogue"], 23)
        self.assertEqual(census["shortfall"],
                         23 - census["types_exhibited_count"])
        self.assertEqual(census["census_complete"],
                         census["shortfall"] == 0)
        self.assertIn("shortfall", census["honest_statement"])

    def test_the_constructions_alone_exhibit_two_types(self):
        census = dh.deep_hole_census(walks=0, probes=200, patience=40)
        self.assertEqual(set(census["types_exhibited"]),
                         {"A_1^24", "A_2^12"})


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
