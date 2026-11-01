"""Tests for :mod:`glm_universal.constants` -- directive D21, one source of constants.

*Created 31 October 2026 (repository check).  ``constants.py`` promised this
file ("``tests/test_constants.py`` (to be written) checks that they agree on
the values expressible in both"); D21 names it as its instrument.*

What is checked:

* the values the Lean file ``Constants.lean`` and the Python module both
  express agree (the budget ``B = 10``, the quanta ``1/4 < Y < 1/2`` and
  ``Q = Y + 1/8``), the irrational ``Y`` being read through its Wobble
  enclosure (D18), never through a typed-in decimal;
* every older copy of a constant that the consolidation has not yet removed
  (``data_objects.base.N``, ``substrate.leech2.DIM``, ``signoff.rules.SCHEMA``
  ...) still agrees with ``constants`` -- a mirror that drifts fails here;
* every shared path ``constants`` declares exists, and the two path helpers
  find files where the October 2026 reorganisation put them;
* :func:`constants_digest` is deterministic and moves when a constant moves;
* no non-test module builds the path of the Lean tree, the studies folder or
  the input folder by hand, outside the sites recorded below (the ratchet: the
  list may only shrink);
* every Lean file held in ``src/lean/awaiting_recovery/`` waits only for files
  ``studies/_lean_files_needed.md`` records as missing, or for another held
  file (added 31 October 2026, the rule that registry states).
"""

from __future__ import annotations

import ast
import re
import unittest
from fractions import Fraction
from pathlib import Path

from glm_universal import constants as C


class TestValuesAgreeWithLean(unittest.TestCase):
    """``Constants.lean`` is the specification (D8); the Python is its instance."""

    @classmethod
    def setUpClass(cls):
        cls.lean = C.lean_file("Constants.lean").read_text(encoding="utf-8")

    def test_the_lean_file_is_where_the_constants_say(self):
        self.assertTrue(C.lean_file("Constants.lean").is_file())

    def test_budget(self):
        m = re.search(r"def budget : ℝ := (\d+)", self.lean)
        self.assertIsNotNone(m)
        self.assertEqual(int(m.group(1)), C.CARRIER_BUDGET)

    def test_the_lean_file_proves_the_bounds_the_python_relies_on(self):
        for theorem in ("Y_pos", "Y_lt_half", "Y_gt_quarter", "Q_pos",
                        "Q_lt_one"):
            self.assertIn(f"theorem {theorem}", self.lean, theorem)
        self.assertIn("noncomputable def Q : ℝ := Y + 1 / 8", self.lean)

    def test_y_is_read_through_its_wobble_enclosure(self):
        # Y = 1/(pi + 2/pi) is decreasing in pi for pi > sqrt(2), so the
        # enclosure [lo, hi] of pi gives [1/(hi + 2/hi), 1/(lo + 2/lo)].
        from glm_universal.reasoning import wobble_registry as W
        lo, hi = W.wobble("pi", Fraction(1, 10 ** 6))
        self.assertIsInstance(lo, Fraction)
        self.assertLess(lo, hi)
        y_lo = 1 / (hi + 2 / hi)
        y_hi = 1 / (lo + 2 / lo)
        # The Lean theorems Y_gt_quarter and Y_lt_half, seen in the enclosure.
        self.assertLess(Fraction(1, 4), y_lo)
        self.assertLess(y_hi, Fraction(1, 2))
        # The stored value is a certified lower bound, never above Y.
        self.assertLessEqual(C.CARRIER_Y, y_lo)
        self.assertIsInstance(C.CARRIER_Y, Fraction)

    def test_q_is_y_plus_an_eighth(self):
        self.assertEqual(C.CARRIER_Q, C.CARRIER_Y + Fraction(1, 8))
        self.assertLess(C.CARRIER_Q, 1)


class TestMirrorsAgree(unittest.TestCase):
    """Older copies the consolidation has not yet removed must not drift."""

    def test_carrier_dimension(self):
        from glm_universal.data_objects import base
        from glm_universal.substrate import golay_decode, leech2
        self.assertEqual(base.N, C.CARRIER_DIMENSION)
        self.assertEqual(leech2.DIM, C.LEECH_DIMENSION)
        self.assertEqual(golay_decode.N, C.GOLAY_LENGTH)
        self.assertEqual(C.CARRIER_DIMENSION, C.LEECH_DIMENSION)
        self.assertEqual(C.GOLAY_LENGTH, 2 * C.GOLAY_DIMENSION)

    def test_signoff_schema(self):
        from glm_universal.signoff import rules
        self.assertEqual(rules.SCHEMA, C.SIGNOFF_SCHEMA)

    def test_null_model_seed(self):
        from glm_universal import integrity
        import inspect
        default = inspect.signature(
            integrity.seeded_permutation).parameters["seed"].default
        self.assertEqual(default, C.NULL_MODEL_SEED)


class TestPaths(unittest.TestCase):

    def test_every_declared_directory_exists(self):
        for name in ("REPOSITORY_ROOT", "PACKAGE_ROOT", "LEAN_ROOT",
                     "LEAN_SOURCE_DIR", "LEAN_GLM_DIR", "SCRIPTS_DIR",
                     "STUDIES_DIR", "SOURCE_MATERIAL_DIR", "WHEELS_DIR"):
            self.assertTrue(getattr(C, name).is_dir(), name)

    def test_every_declared_file_exists(self):
        for name in ("LEAN_AUDIT_FILE", "STUDY_SCHEMA_FILE",
                     "LEAN_FILES_NEEDED"):
            self.assertTrue(getattr(C, name).is_file(), name)

    def test_the_package_is_inside_the_repository(self):
        self.assertEqual(C.PACKAGE_ROOT, C.REPOSITORY_ROOT / "src" / "glm_universal")
        self.assertEqual(C.LEAN_GLM_DIR.relative_to(C.REPOSITORY_ROOT).parts,
                         ("src", "lean", C.LEAN_LIBRARY, "GLM"))

    def test_lean_file_accepts_names_paths_and_modules(self):
        by_name = C.lean_file("Constants.lean")
        self.assertEqual(C.lean_file("Constants"), by_name)
        self.assertEqual(C.lean_file(f"{C.LEAN_LIBRARY}.GLM.Constants"), by_name)
        self.assertEqual(C.lean_file("Rule30/Basic.lean").name, "Basic.lean")

    def test_lean_file_finds_a_held_file(self):
        held = sorted(C.LEAN_HOLDING_DIR.rglob("*.lean"))
        if not held:
            self.skipTest("nothing is held awaiting recovery")
        found = C.lean_file(held[0].name)
        self.assertEqual(found, held[0])

    def test_an_absent_lean_file_is_reported_at_its_build_path(self):
        path = C.lean_file("NoSuchFileEver.lean")
        self.assertFalse(path.exists())
        self.assertEqual(path.parent, C.LEAN_GLM_DIR)

    def test_an_absent_item_is_reported_in_done(self):
        path = C.source_material_item("no_such_item_ever")
        self.assertFalse(path.exists())
        self.assertEqual(path.parent, C.SOURCE_DONE_DIR)

    def test_every_name_in_all_is_defined(self):
        for name in C.__all__:
            self.assertTrue(hasattr(C, name), name)


class TestTheHoldingRegistry(unittest.TestCase):
    """The rule ``studies/_lean_files_needed.md`` states: a file held in
    ``src/lean/awaiting_recovery/`` may wait only for files that registry
    records as missing, or for another file held in the same state
    (``glm_universal.lean_check.audited_or_held``)."""

    def test_every_held_file_waits_only_for_recorded_files(self):
        from glm_universal import lean_check
        held = lean_check.held_files()
        if not held:
            self.skipTest("nothing is held awaiting recovery")
        registry = C.LEAN_FILES_NEEDED.read_text(encoding="utf-8")
        for entry in held:
            with self.subTest(held=entry["module"]):
                self.assertTrue(entry["lacks"], f"{entry['module']} waits for nothing")
                self.assertTrue(lean_check.audited_or_held(entry["module"]),
                                f"{entry['module']} waits for {entry['lacks']}")
                for wait in entry["lacks"]:
                    name = wait.split(" ")[0]
                    if "(itself held)" not in wait:
                        self.assertIn(f"`{name.split('.')[-1]}.lean`", registry)

    def test_a_held_file_waiting_for_an_unrecorded_file_or_for_nothing_is_refused(self):
        from unittest import mock
        from glm_universal import lean_check
        held = lean_check.held_files()
        if not held:
            self.skipTest("nothing is held awaiting recovery")
        module = held[0]["module"]
        for lacks in (["RequestProject.GLM.NoSuchRecordedFileEver"], []):
            with self.subTest(lacks=lacks), mock.patch.object(
                    lean_check, "held_files", lambda: [{"module": module, "lacks": lacks}]):
                self.assertFalse(lean_check.audited_or_held(module))


class TestDigest(unittest.TestCase):

    def test_the_digest_is_deterministic(self):
        self.assertEqual(C.constants_digest(), C.constants_digest())
        self.assertRegex(C.constants_digest(), r"^[0-9a-f]{64}$")

    def test_the_digest_moves_when_a_constant_moves(self):
        before = C.constants_digest()
        saved = C.CARRIER_BUDGET
        try:
            C.CARRIER_BUDGET = saved + 1
            self.assertNotEqual(C.constants_digest(), before)
        finally:
            C.CARRIER_BUDGET = saved
        self.assertEqual(C.constants_digest(), before)


#: Non-test modules that still build a shared path by hand, recorded on
#: 31 October 2026.  The list may only shrink: a module that is moved to the
#: constants comes off it, and a new hand-built path fails the test below.
#: Each entry is a path relative to ``src/glm_universal``.
LEGACY_PATH_SITES = frozenset({
    "evaluation/connected_two_cases.py",
    "evaluation/elliptic_certificate_cases.py",
    "evaluation/pocklington_certificate_cases.py",
    "evaluation/primality_certificate_cases.py",
    "evaluation/tool_values_cases.py",
    "evaluation/tool_verdicts_cases.py",
    "reasoning/agree_channel_marks.py",
    "reasoning/blueprint.py",
    "reasoning/carrier_read.py",
    "reasoning/citation_reference.py",
    "reasoning/confidence_floor_marks.py",
    "reasoning/decoder_confidence_marks.py",
    "reasoning/designed_substrate.py",
    "reasoning/directives.py",
    "reasoning/evidence_in_use_study.py",
    "reasoning/frame_operator_study.py",
    "reasoning/held_precision.py",
    "reasoning/law_absorption.py",
    "reasoning/lean_address.py",
    "reasoning/meta_evidence.py",
    "reasoning/ops_ladder.py",
    "reasoning/pi_machine_study.py",
    "reasoning/pipeline.py",
    "reasoning/pipeline_ask_study.py",
    "reasoning/pipeline_kit_study.py",
    "reasoning/rate_posterior_marks.py",
    "reasoning/review_sweep.py",
    "reasoning/shortest_tag.py",
    "runtime/composed_radical_report.py",
    "runtime/cubic_radical_report.py",
    "runtime/cubic_trig_report.py",
    "runtime/derivation_four_marks.py",
    "runtime/derivation_report.py",
    "runtime/derivation_three_marks.py",
    "runtime/derivation_two_report.py",
    "runtime/explanation_report.py",
    "runtime/frobenius_radical_report.py",
    "runtime/meta_report.py",
    "runtime/nonlinear_report.py",
    "runtime/primitive_degree_report.py",
    "runtime/primitive_radical_report.py",
    "runtime/quintic_radical_report.py",
    "runtime/symbolic_report.py",
    "signoff/rules.py",
})


def _hand_built_path_sites():
    """Modules outside ``constants.py`` and the tests that spell a shared
    folder name (``"lean"``, ``"studies"``, ``"source_material"``,
    ``"glm_lean"``) as a string literal joined onto a path."""
    shared = {"lean", "glm_lean", "studies", "source_material", "scripts"}
    sites = set()
    for path in sorted(C.PACKAGE_ROOT.rglob("*.py")):
        rel = path.relative_to(C.PACKAGE_ROOT).as_posix()
        if rel == "constants.py" or rel.startswith("tests/"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)
                    and isinstance(node.right, ast.Constant)
                    and isinstance(node.right.value, str)
                    and node.right.value.strip("/").split("/")[0] in shared):
                sites.add(rel)
    return sites


class TestSingleSource(unittest.TestCase):

    def test_no_new_hand_built_shared_paths(self):
        new = sorted(_hand_built_path_sites() - LEGACY_PATH_SITES)
        self.assertEqual(new, [], "use glm_universal.constants for these paths")

    def test_the_legacy_list_only_records_real_sites(self):
        stale = sorted(LEGACY_PATH_SITES - _hand_built_path_sites())
        self.assertEqual(stale, [], "remove these from LEGACY_PATH_SITES")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
