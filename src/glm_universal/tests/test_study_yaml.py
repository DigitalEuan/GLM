"""Tests for the study YAML manifests (the .yaml + .md pairs).

Validates that:
  * Every study .md with a tier-0 block has a paired .yaml.
  * Every .yaml declares the correct schema (glm-study-manifest/v1).
  * Every .yaml has the required fields (id, question, verdict, file_refs).
  * The .yaml's id matches its filename.
  * The .yaml's file_refs.prose points to the paired .md.
  * The tier-0 fields (question, verdict) are non-empty.
"""
from __future__ import annotations

import unittest
from pathlib import Path

try:
    import yaml as _yaml
except ImportError:
    _yaml = None


def _studies_dir() -> Path:
    """The studies/ directory."""
    from glm_universal.constants import REPOSITORY_ROOT
    return REPOSITORY_ROOT / "studies"


def _yaml_available() -> bool:
    return _yaml is not None


class TestStudyYamlPairs(unittest.TestCase):
    """Every study .md with a tier-0 block has a paired .yaml."""

    def setUp(self):
        self.studies = _studies_dir()

    def test_studies_directory_exists(self):
        self.assertTrue(self.studies.is_dir(), f"{self.studies} is not a directory")

    def test_schema_file_exists(self):
        schema = self.studies / "_schema" / "study.schema.yaml"
        self.assertTrue(schema.exists(), f"schema file {schema} does not exist")

    @unittest.skipUnless(_yaml_available(), "PyYAML not installed")
    def test_every_md_with_tier0_has_yaml(self):
        """Every .md with a tier-0 block has a paired .yaml."""
        TIER0_FOOTER = "*Tier 0 is a coarse read"
        missing = []
        for md in sorted(self.studies.glob("*.md")):
            text = md.read_text(encoding="utf-8")
            if "## Tier 0" not in text:
                continue  # no tier-0 block, skip
            yaml_path = md.with_suffix(".yaml")
            if not yaml_path.exists():
                missing.append(md.name)
        if missing:
            self.fail(f"{len(missing)} .md files with tier-0 blocks have no .yaml:\n  "
                      + "\n  ".join(missing[:10])
                      + (f"\n  ... and {len(missing) - 10} more" if len(missing) > 10 else ""))

    @unittest.skipUnless(_yaml_available(), "PyYAML not installed")
    def test_every_yaml_declares_correct_schema(self):
        """Every .yaml declares schema: glm-study-manifest/v1."""
        bad = []
        for yaml_path in sorted(self.studies.glob("*.yaml")):
            data = _yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                bad.append(f"{yaml_path.name}: not a mapping")
                continue
            schema = data.get("schema")
            if schema != "glm-study-manifest/v1":
                bad.append(f"{yaml_path.name}: schema is {schema!r}")
        if bad:
            self.fail(f"{len(bad)} .yaml files with wrong schema:\n  "
                      + "\n  ".join(bad[:10]))


class TestStudyYamlFields(unittest.TestCase):
    """The required fields are present and correct."""

    def setUp(self):
        self.studies = _studies_dir()

    @unittest.skipUnless(_yaml_available(), "PyYAML not installed")
    def test_required_fields_present(self):
        """Every .yaml has id, question, verdict, file_refs."""
        missing = []
        for yaml_path in sorted(self.studies.glob("*.yaml")):
            data = _yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                continue
            for field in ("schema", "id", "question", "verdict", "file_refs"):
                if field not in data:
                    missing.append(f"{yaml_path.name}: missing {field}")
        if missing:
            self.fail(f"{len(missing)} .yaml files missing required fields:\n  "
                      + "\n  ".join(missing[:10]))

    @unittest.skipUnless(_yaml_available(), "PyYAML not installed")
    def test_id_matches_filename(self):
        """The .yaml's id matches its filename (without extension)."""
        bad = []
        for yaml_path in sorted(self.studies.glob("*.yaml")):
            data = _yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                continue
            expected_id = yaml_path.stem
            if data.get("id") != expected_id:
                bad.append(f"{yaml_path.name}: id is {data.get('id')!r}, expected {expected_id!r}")
        if bad:
            self.fail(f"{len(bad)} .yaml files with mismatched id:\n  "
                      + "\n  ".join(bad[:10]))

    @unittest.skipUnless(_yaml_available(), "PyYAML not installed")
    def test_file_refs_prose_points_to_paired_md(self):
        """The file_refs.prose field points to the paired .md."""
        bad = []
        for yaml_path in sorted(self.studies.glob("*.yaml")):
            data = _yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                continue
            fr = data.get("file_refs", {})
            prose = fr.get("prose", "")
            expected = yaml_path.stem + ".md"
            if prose != expected:
                bad.append(f"{yaml_path.name}: prose is {prose!r}, expected {expected!r}")
        if bad:
            self.fail(f"{len(bad)} .yaml files with wrong prose ref:\n  "
                      + "\n  ".join(bad[:10]))

    @unittest.skipUnless(_yaml_available(), "PyYAML not installed")
    def test_tier0_fields_non_empty(self):
        """The question and verdict fields are non-empty."""
        empty = []
        for yaml_path in sorted(self.studies.glob("*.yaml")):
            data = _yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                continue
            if not data.get("question"):
                empty.append(f"{yaml_path.name}: empty question")
            if not data.get("verdict"):
                empty.append(f"{yaml_path.name}: empty verdict")
        if empty:
            self.fail(f"{len(empty)} .yaml files with empty tier-0 fields:\n  "
                      + "\n  ".join(empty[:10]))


class TestStudyYamlDrift(unittest.TestCase):
    """The .yaml has not drifted from its .md."""

    def setUp(self):
        self.studies = _studies_dir()

    @unittest.skipUnless(_yaml_available(), "PyYAML not installed")
    def test_yaml_not_older_than_md(self):
        """The .yaml was generated after the .md was last modified.

        (This catches the case where the .md was edited but the .yaml
        was not regenerated.)
        """
        stale = []
        for md in sorted(self.studies.glob("*.md")):
            yaml_path = md.with_suffix(".yaml")
            if not yaml_path.exists():
                continue  # missing yaml is caught by TestStudyYamlPairs
            if yaml_path.stat().st_mtime < md.stat().st_mtime - 1:
                stale.append(md.name)
        if stale:
            self.fail(f"{len(stale)} .yaml files are older than their .md "
                      f"(run 05_studies_to_yaml.py --write):\n  "
                      + "\n  ".join(stale[:10]))


if __name__ == "__main__":
    unittest.main()
