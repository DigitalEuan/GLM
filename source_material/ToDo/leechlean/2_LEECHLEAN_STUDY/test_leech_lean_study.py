"""``tests/test_leech_lean_study.py`` -- the measurement behind
``studies/LEECHLEAN_STUDY.md``, recomputed: the 15 questions, the baseline,
the controls and the mechanism.

*Created 11 November 2026 (the intake of ``source_material/ToDo/leechlean``,
directive D22).  The criterion is the study's §8: at least 12 of 15 right
and 0 wrong through the tool surface, 0 of 15 without it, every control
refused or left alone, and the move model at least 3 points above the part
model on the pre-registered sample.*
"""
import unittest

from glm_universal.reasoning import leech_lean_study as S


def _no_float(value) -> None:
    if isinstance(value, float):
        raise AssertionError(f"a float reached the figures: {value!r}")
    if isinstance(value, dict):
        for v in value.values():
            _no_float(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            _no_float(v)


class TestMeasurement(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.report = S.leech_lean_report()

    def test_figures_are_exact(self):
        _no_float(self.report)

    def test_the_criterion(self):
        r = self.report
        self.assertGreaterEqual(r["right"], 12, r["grades"])
        self.assertEqual(r["wrong"], 0)
        self.assertEqual(r["baseline_right"], 0)
        for name, held in r["checks"].items():
            self.assertTrue(held, name)
        self.assertTrue(r["all_checks_hold"])

    def test_the_15_grades(self):
        grades = self.report["grades"]
        self.assertEqual(len(grades), 15)
        for qid, grade in grades.items():
            self.assertIn(grade, ("right", "refused"), (qid, grade))
        self.assertEqual(sum(1 for g in grades.values() if g == "right"),
                         self.report["right"])

    def test_the_controls(self):
        controls = self.report["controls"]
        self.assertEqual(len(controls), 6)
        for cid, outcome in controls.items():
            self.assertIn(outcome, ("refused", "flagged"), (cid, outcome))

    def test_the_mechanism(self):
        loo = self.report["loo"]
        self.assertEqual(loo["files"], S.LOO_FILES)
        self.assertGreater(loo["move_hits"] * max(loo["part_total"], 1),
                           loo["part_hits"] * max(loo["move_total"], 1))
        self.assertGreaterEqual(self.report["margin_points_pm"], 30)

    def test_the_deciding_figure(self):
        fig = self.report["deciding_figure"]
        self.assertIn("of 15 questions answered right", fig)
        self.assertIn("0 wrong", fig)
        self.assertIn("of 6 negative controls", fig)
        self.assertIn("move model", fig)


if __name__ == "__main__":
    unittest.main()
