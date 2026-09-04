"""The D7/D9 inventories: no float is written, and every unusual operation
is declared.

``glm_universal.reasoning.exactness`` parses every module of the package and
reports the sites where a float could be constructed, where a cryptographic
digest is taken, and -- through
:func:`glm_universal.reasoning.combiner.xor_inventory` -- where XOR is used.
These tests are what turns the three inventories into a rule: they fail when
the tree acquires a site nobody declared, and equally when a declared site
stops existing, because a stale inventory is as misleading as an incomplete
one.
"""

from __future__ import annotations

import ast
import pathlib
import unittest
from fractions import Fraction

from glm_universal.reasoning import exactness as EX
from glm_universal.reasoning.combiner import xor_inventory
from glm_universal.evaluation import harness as EH
from glm_universal.signoff.__main__ import _percent, _seconds


class TestTheFloatInventory(unittest.TestCase):
    """No module writes a float without saying why."""

    def setUp(self) -> None:
        self.inventory = EX.exactness_inventory()

    def test_every_float_site_is_declared(self):
        self.assertEqual(self.inventory["unclassified_modules"], ())

    def test_no_declared_site_has_gone_away(self):
        self.assertEqual(self.inventory["stale_declarations"], ())

    def test_a_declared_site_declares_the_right_kinds(self):
        self.assertEqual(self.inventory["mismatched_kinds"], ())

    def test_the_inventory_is_complete(self):
        self.assertTrue(self.inventory["inventory_is_complete"])

    def test_the_only_float_site_is_the_rejection_probe(self):
        """The one warranted site: floats fed in to be refused.

        ``carrier_rejects_floats`` hands ``0.5`` and ``2.0`` to four entry
        points of the substrate and requires each to raise, so the floats are
        the adversarial input and the probe's result is that none of them was
        accepted.  Every other module of the package is float-free.
        """
        self.assertEqual(set(self.inventory["sites"]),
                         {"capabilities/probes.py"})
        self.assertEqual(self.inventory["by_kind"]["float-call"], 0)
        self.assertEqual(self.inventory["by_kind"]["float-clock"], 0)
        self.assertEqual(self.inventory["by_kind"]["inexact-library"], 0)

    def test_the_scan_covers_the_whole_package(self):
        scanned = int(self.inventory["modules_scanned"])
        root = pathlib.Path(EX.__file__).resolve().parent.parent
        actual = sum(1 for path in root.rglob("*.py")
                     if "__pycache__" not in path.as_posix()
                     and not path.relative_to(root).as_posix()
                     .startswith("tests/"))
        self.assertEqual(scanned, actual)

    def test_no_integer_division_makes_a_float(self):
        self.assertEqual(EX.certain_float_divisions(), ())


class TestTheScannerItself(unittest.TestCase):
    """A scanner nobody has tested is not an instrument."""

    def _sites(self, source: str) -> dict:
        path = pathlib.Path(self._write(source))
        return EX.module_float_sites(path)

    def _write(self, source: str) -> str:
        import tempfile
        handle = tempfile.NamedTemporaryFile(
            "w", suffix=".py", delete=False, encoding="utf-8")
        handle.write(source)
        handle.close()
        return handle.name

    def test_it_finds_a_float_literal(self):
        self.assertEqual(self._sites("x = 0.5\n"), {"float-literal": 1})

    def test_it_finds_an_exponent_literal(self):
        self.assertEqual(self._sites("x = 1e-9\n"), {"float-literal": 1})

    def test_it_finds_the_float_builtin(self):
        self.assertEqual(self._sites("x = float(1)\n"), {"float-call": 1})

    def test_it_finds_a_float_clock(self):
        self.assertEqual(self._sites("import time\nx = time.monotonic()\n"),
                         {"float-clock": 1})

    def test_the_integer_clock_is_not_a_float_site(self):
        self.assertEqual(self._sites("import time\nx = time.monotonic_ns()\n"),
                         {})

    def test_exact_math_is_not_an_inexact_library(self):
        self.assertEqual(self._sites("import math\nx = math.isqrt(9)\n"), {})

    def test_inexact_math_is(self):
        self.assertEqual(self._sites("import math\nx = math.sqrt(9)\n"),
                         {"inexact-library": 1})

    def test_the_word_float_in_a_docstring_is_not_a_float(self):
        self.assertEqual(self._sites('"""No float here."""\nfloats = 1\n'), {})

    def test_an_integer_is_not_a_float(self):
        self.assertEqual(self._sites("x = 1\ny = True\n"), {})

    def test_certain_integer_division_is_recognised(self):
        tree = ast.parse("x = len(a) / 2\n")
        node = tree.body[0].value
        self.assertTrue(EX._certainly_integer(node.left))
        self.assertTrue(EX._certainly_integer(node.right))

    def test_a_fraction_division_is_not_convicted(self):
        tree = ast.parse("x = Fraction(1, 2) / 2\n")
        node = tree.body[0].value
        self.assertFalse(EX._certainly_integer(node.left))


class TestTheDigestInventory(unittest.TestCase):
    """Three modules hash, and all three hash for integrity (D3)."""

    def setUp(self) -> None:
        self.inventory = EX.digest_inventory()

    def test_every_digest_site_is_declared(self):
        self.assertEqual(self.inventory["unclassified_modules"], ())

    def test_no_declared_digest_site_has_gone_away(self):
        self.assertEqual(self.inventory["stale_declarations"], ())

    def test_every_use_is_an_integrity_use(self):
        self.assertTrue(self.inventory["every_use_is_integrity"])

    def test_the_reasoning_kernel_does_not_hash(self):
        """No module of the reasoning kernel or the substrate takes a digest.

        This is D3 read the strict way: a digest may decide whether a stored
        result is still valid, and may never stand in for what a thing means.
        """
        hashing = {module for module, _ in EX.DIGEST_SITES}
        self.assertFalse({m for m in hashing
                          if m.startswith(("reasoning/", "substrate/",
                                           "semantics/", "data_objects/",
                                           "runtime/"))})


class TestTheThreeInventoriesTogether(unittest.TestCase):
    """D9: an operation that is not the substrate's own is declared."""

    def test_all_three_hold(self):
        report = EX.warranted_operations_report()
        self.assertTrue(report["holds"])
        self.assertEqual(report["complete"], report["inventories"])

    def test_the_xor_inventory_is_the_one_the_combiner_keeps(self):
        report = EX.warranted_operations_report()
        self.assertEqual(report["xor"], xor_inventory())


class TestTimingIsIntegerArithmetic(unittest.TestCase):
    """The timing layers measure in integer nanoseconds, and format exactly."""

    def test_elapsed_time_renders_without_a_float(self):
        self.assertEqual(EH._seconds_text(0), "0.0")
        self.assertEqual(EH._seconds_text(1234), "1.2")
        self.assertEqual(EH._seconds_text(1250), "1.3")
        self.assertEqual(EH._seconds_text(96), "0.1")
        self.assertEqual(EH._seconds_text(60_000), "60.0")

    def test_the_signoff_formats_an_exact_rational(self):
        self.assertEqual(_seconds(Fraction(1234, 1000)), "1.2s")
        self.assertEqual(_seconds(Fraction(0)), "0.0s")
        self.assertEqual(_percent(Fraction(1, 3)), "33")
        self.assertEqual(_percent(Fraction(1)), "100")

    def test_a_case_result_records_whole_milliseconds(self):
        result = EH.CaseResult(
            id="x", kind="report", question="q", expect="answer",
            classification="", outcome="correct", returncode=0, answer="a",
            refused=False, stopped_at="", milliseconds=17)
        self.assertIsInstance(result.milliseconds, int)
        self.assertEqual(result.as_dict()["milliseconds"], 17)


if __name__ == "__main__":                      # pragma: no cover
    unittest.main()
