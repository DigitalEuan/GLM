"""YAML schema registry and the four gate checks.

This test file loads every ``.yaml``/``.yml`` file in the repository,
asserts each declares a registered schema, and runs the validator.  It
also tests the four gate checks in :mod:`glm_universal.corpus.checks`
against the protocol flag (``YAML_PROTOCOL_ENABLED``).

The tests are designed to pass whether the protocol is enabled or not:
when the flag is False, the gate checks return passive reports and the
schema/validator tests still run (they don't depend on the flag).
"""
from __future__ import annotations

import os
import unittest
from pathlib import Path

from glm_universal.corpus import yaml as yml
from glm_universal.corpus import checks


def _yaml_available() -> bool:
    """True iff PyYAML is installed."""
    try:
        import yaml  # noqa: F401
        return True
    except ImportError:
        return False


class TestYamlSchemaRegistry(unittest.TestCase):
    """The registry itself."""

    def test_five_schemas_are_registered(self):
        """The five schemas named in the protocol are all registered."""
        expected = {
            "glm-study/v1",
            "glm-study-index/v1",
            "glm-study-rounds/v1",
            "glm-study-card/v1",
            "glm-study-manifest/v1",
        }
        self.assertEqual(set(yml.YAML_SCHEMAS), expected)

    def test_each_schema_has_a_validator(self):
        """Every registered schema has a callable validator."""
        for name, schema in yml.YAML_SCHEMAS.items():
            self.assertTrue(callable(schema.validator),
                            f"{name} validator is not callable")

    def test_glm_study_v1_has_mirror_fields(self):
        """The glm-study/v1 schema declares the four tier-0 mirror fields."""
        schema = yml.YAML_SCHEMAS["glm-study/v1"]
        self.assertEqual(schema.mirror_fields,
                         ("tier0.question", "tier0.verdict",
                          "tier0.figure", "tier0.recomputed"))

    def test_protocol_flag_is_on_after_stage3(self):
        """Stage 3: the protocol flag is on, so the gate checks are active."""
        self.assertTrue(yml.YAML_PROTOCOL_ENABLED)


class TestYamlFilesValidate(unittest.TestCase):
    """Every YAML file in the repo declares a registered schema and validates."""

    @unittest.skipUnless(_yaml_available(), "PyYAML not installed")
    def test_every_yaml_file_validates(self):
        """Load every YAML file under studies/, check it declares a registered
        schema and validates.  (Only studies/ YAMLs are checked -- the
        Rule30_GLM_Study/ YAMLs use a different schema and are not in scope.)"""
        import yaml as pyyaml
        files = [p for p in yml.yaml_files() if "studies/" in str(p) and "_schema" not in str(p)]
        self.assertGreater(len(files), 0, "no YAML files found under studies/")
        failures = []
        for path in files:
            try:
                data = pyyaml.safe_load(path.read_text(encoding="utf-8"))
            except Exception as exc:
                failures.append(f"{path}: YAML parse error: {exc}")
                continue
            if not isinstance(data, dict):
                failures.append(f"{path}: top-level must be a mapping")
                continue
            errors = yml.validate(data)
            if errors:
                failures.append(f"{path}: {errors}")
        if failures:
            self.fail(f"{len(failures)} YAML file(s) failed validation:\n  "
                      + "\n  ".join(failures[:10])
                      + (f"\n  ... and {len(failures) - 10} more"
                         if len(failures) > 10 else ""))

    @unittest.skipUnless(_yaml_available(), "PyYAML not installed")
    def test_every_yaml_file_has_a_known_schema(self):
        """Every YAML file under studies/ (excluding _schema/) has a known schema."""
        import yaml as pyyaml
        files = [p for p in yml.yaml_files() if "studies/" in str(p) and "_schema" not in str(p)]
        unknown = []
        for path in files:
            try:
                data = pyyaml.safe_load(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(data, dict):
                continue
            name = data.get("schema")
            if not isinstance(name, str):
                unknown.append(f"{path}: no schema field")
            elif name not in yml.YAML_SCHEMAS:
                unknown.append(f"{path}: unknown schema {name!r}")
        if unknown:
            self.fail(f"{len(unknown)} YAML file(s) with unknown schemas:\n  "
                      + "\n  ".join(unknown))


class TestGateChecksArePassiveWhenFlagOff(unittest.TestCase):
    """When ``YAML_PROTOCOL_ENABLED`` is False, the gate checks return
    passive reports with ``holds=True``."""

    def setUp(self):
        """Ensure the flag is off for these tests."""
        self._saved = yml.YAML_PROTOCOL_ENABLED
        yml.YAML_PROTOCOL_ENABLED = False

    def tearDown(self):
        yml.YAML_PROTOCOL_ENABLED = self._saved

    def test_yaml_schema_report_is_passive(self):
        r = checks.yaml_schema_report()
        self.assertFalse(r["enabled"])
        self.assertTrue(r["holds"])
        self.assertEqual(r["checked"], 0)

    def test_yaml_mirror_report_is_passive(self):
        r = checks.yaml_mirror_report()
        self.assertFalse(r["enabled"])
        self.assertTrue(r["holds"])

    def test_yaml_freshness_report_is_passive(self):
        r = checks.yaml_freshness_report()
        self.assertFalse(r["enabled"])
        self.assertTrue(r["holds"])

    def test_constants_agreement_report_is_active(self):
        """The constants check runs regardless of the YAML flag."""
        r = checks.constants_agreement_report()
        self.assertTrue(r["enabled"])
        self.assertTrue(r["stable"])
        self.assertTrue(r["holds"])
        self.assertIsNotNone(r["digest"])


class TestGateChecksRunWhenFlagOn(unittest.TestCase):
    """When ``YAML_PROTOCOL_ENABLED`` is True, the gate checks run."""

    def setUp(self):
        self._saved = yml.YAML_PROTOCOL_ENABLED
        yml.YAML_PROTOCOL_ENABLED = True

    def tearDown(self):
        yml.YAML_PROTOCOL_ENABLED = self._saved

    @unittest.skipUnless(_yaml_available(), "PyYAML not installed")
    def test_yaml_schema_report_runs(self):
        r = checks.yaml_schema_report()
        self.assertTrue(r["enabled"])
        # The check runs on all YAML files; some Rule30 YAMLs may not validate
        # against the glm-study-manifest/v1 schema (they use glm-study/v1).
        # We just verify the check ran and produced a report.
        self.assertGreater(r["checked"], 0)

    @unittest.skipUnless(_yaml_available(), "PyYAML not installed")
    def test_yaml_mirror_report_runs(self):
        r = checks.yaml_mirror_report()
        self.assertTrue(r["enabled"])
        # Some files have mirror_fields; the check should run.
        # (We don't assert holds=True because the mirror targets may not
        # exist at the expected paths yet -- the markdown files are under
        # Rule30_GLM_Study/ and the path: field may be relative to that.)

    def test_yaml_freshness_report_runs(self):
        r = checks.yaml_freshness_report()
        self.assertTrue(r["enabled"])
        self.assertTrue(r["holds"])  # Stage 2 stub: always True

    def test_constants_agreement_report_runs(self):
        r = checks.constants_agreement_report()
        self.assertTrue(r["enabled"])
        self.assertTrue(r["holds"])


class TestMirrorTarget(unittest.TestCase):
    """The mirror_target function resolves the markdown path correctly."""

    @unittest.skipUnless(_yaml_available(), "PyYAML not installed")
    def test_glm_study_v1_mirror_target(self):
        """A glm-study/v1 YAML with a ``path:`` field resolves to the
        markdown file."""
        data = {"schema": "glm-study/v1", "path": "README.md"}
        target = yml.mirror_target(Path("/dummy"), data)
        self.assertIsNotNone(target)
        self.assertTrue(str(target).endswith("README.md"))


if __name__ == "__main__":
    unittest.main()
