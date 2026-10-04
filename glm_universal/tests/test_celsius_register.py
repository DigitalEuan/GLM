"""The Celsius register -- the ITS-90 fixed points held in degrees Celsius,
the scale table's offset row, and the planner reading a Celsius register value
as a level, pinned.

``glm_universal.data_objects.fixed_points`` is the register
(``studies/CELSIUS_REGISTER_STUDY.md``, Phase 99);
``glm_universal.runtime.celsius_register_report`` measures the declared corpus
of ``glm_universal.evaluation.celsius_register_cases``.  The facts the round
rests on are theorems of ``RequestProject/GLM/CelsiusRegister.lean`` (C8).
Everything is exact.
"""

from __future__ import annotations

import unittest
from fractions import Fraction
from pathlib import Path

from glm_universal.data_objects import fixed_points as fp
from glm_universal.evaluation import celsius_register_cases as C
from glm_universal.reasoning import scale_conversion as sc
from glm_universal.runtime import celsius_register_report as cr
from glm_universal.runtime import measurand_register as mreg
from glm_universal.runtime import quantity_units as qu
from glm_universal.runtime import stepwise as sw
from glm_universal.runtime.session import GeometricSession

LEAN = (Path(__file__).resolve().parents[3] / "overlay" / "glm_lean"
        / "RequestProject" / "GLM" / "CelsiusRegister.lean")

_SESSION = []


def session():
    if not _SESSION:
        _SESSION.append(GeometricSession())
    return _SESSION[0]


class TestTheRegister(unittest.TestCase):

    def test_c1_the_register_and_its_offset_row(self):
        got = cr.register_report()
        self.assertTrue(got["met"], got)
        self.assertEqual(got["carried_match"], 14)

    def test_the_register_holds_celsius_only(self):
        for row in fp.load_fixed_point_register():
            fields = row.fields()
            self.assertIn("temperature_C", fields)
            self.assertFalse(any(k.endswith("_K") for k in fields))
            self.assertIsInstance(row.temperature_C, Fraction)

    def test_no_row_answers_to_an_element_name(self):
        surface = session().field_surface
        table = surface.table_by_name("fixed_point")
        for alias in ("zinc", "Zn", "water", "mercury"):
            self.assertNotIn(alias, table.aliases())

    def test_the_offset_row_is_the_si_definition(self):
        row = sc.declared("fixed_point:temperature_C")
        self.assertEqual((row.factor, row.offset), (1, Fraction(27315, 100)))
        self.assertEqual(sum(1 for r in sc.CONVERSIONS if r.offset != 0), 1)

    def test_a_factor_alone_refuses_the_offset_row(self):
        with self.assertRaises(qu.UnitRefused) as caught:
            qu.scale_into_si("fixed_point:temperature_C")
        self.assertEqual(caught.exception.name, "OFFSET_UNIT")
        factor, offset, _dim, quantity = qu.scale_into_si_affine(
            "fixed_point:temperature_C")
        self.assertEqual((factor, offset, quantity),
                         (1, Fraction(27315, 100), "temperature"))

    def test_the_offset_switch_restores(self):
        with cr.switched(OFFSETS=False):
            self.assertEqual(sc.apply(sc.declared(
                "fixed_point:temperature_C"), Fraction(1, 100)),
                Fraction(1, 100))
        self.assertTrue(sc.OFFSETS)

    def test_the_measurand_row_is_a_level_by_name(self):
        row = mreg.measurand_of("fixed_point:temperature_C")
        self.assertEqual((row.by_name, row.kind, row.offset),
                         ("temperature", "thermodynamic temperature",
                          Fraction(27315, 100)))


class TestTheDeclaredCases(unittest.TestCase):

    def test_c2_ordering(self):
        got = cr.order_report(session())
        self.assertEqual((got["met"], got["wrong"]), (got["cases"], 0), got)

    def test_c3_columns(self):
        got = cr.column_report(session())
        self.assertEqual(got["met"], got["cases"], got)

    def test_c4_planner(self):
        for cid, q, want in C.PLANNER_CASES:
            with self.subTest(case=cid):
                got = sw._verdict_of(sw.answer(session(), q))
                self.assertEqual(tuple(got[:len(want)]), want)

    def test_an_offset_conversion_is_named_with_its_carried_values(self):
        row = next(r for r in cr.order_report(session())["rows"]
                   if r["id"] == "o03")
        self.assertIn("+ 5463/20", row["sentence"])
        self.assertIn("6829/25 (= 273.16)", row["sentence"])


class TestTheControls(unittest.TestCase):

    def test_c5_offset_dropped(self):
        order = cr.order_report(session())
        by_id = {r["id"]: r for r in order["rows"]}
        for cid in C.NAIVE_FLIPS:
            self.assertNotEqual(by_id[cid]["naive"], by_id[cid]["got"])
        for cid, q, want in C.PLANNER_CASES:
            if cid not in C.NAIVE_PLANNER_WRONG:
                continue
            with self.subTest(case=cid), cr.switched(OFFSETS=False):
                naive = sw._verdict_of(sw.answer(session(), q))
                self.assertEqual(naive[0], "ANSWER")
                self.assertNotEqual(tuple(naive[:2]), want)

    def test_c5_register_absent(self):
        with cr.switched(ACTIVE=False):
            before = GeometricSession()
            names = [t.name for t in before.field_surface.tables()]
            self.assertNotIn("fixed_point", names)
            q = C.PLANNER_CASES[0][1]
            self.assertNotEqual(sw._verdict_of(sw.answer(before, q))[0],
                                "ANSWER")
        self.assertTrue(fp.ACTIVE)


class TestTheScripts(unittest.TestCase):

    def test_c7_scripts_and_the_offset_lie(self):
        got = cr.scripts_report(session(), limit=2)
        self.assertEqual(got["verified"], got["chains"], got)
        self.assertEqual(got["escaped"], [])
        self.assertEqual(got["offset_lies_caught"], got["offset_lies"])
        self.assertEqual(got["offset_lies"], 2)


class TestTheLeanFile(unittest.TestCase):

    def test_c8_the_lean_file_names_the_facts(self):
        text = LEAN.read_text(encoding="utf-8")
        self.assertNotIn("sorry", text)
        for name in ("register_carries_to_its90_kelvin",
                     "register_above_absolute_zero",
                     "register_strictly_increasing",
                     "celsius_row_keeps_verdicts",
                     "dropping_the_offset_flips_a_verdict",
                     "naive_level_wrong", "planner_answers",
                     "aluminium_gap"):
            self.assertIn(f"theorem {name}", text)


if __name__ == "__main__":                       # pragma: no cover
    unittest.main()
