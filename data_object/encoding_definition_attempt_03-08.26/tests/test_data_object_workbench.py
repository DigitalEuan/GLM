import json
import tempfile
import unittest
from pathlib import Path

import data_object_workbench as workbench


class DataObjectWorkbenchTests(unittest.TestCase):
    def test_golay_mog_view_is_exact_and_complete(self):
        view = workbench.make_identity_view(37, use_gray=True)
        self.assertEqual(len(view["message_bits_little_endian"]), 12)
        self.assertEqual(len(view["golay_codeword"]), 24)
        self.assertEqual(sorted(cell["coordinate"] for cell in view["mog_cells"]), list(range(24)))
        self.assertEqual(set().union(*map(set, workbench.MOG_OCTAD_ZONES)), set(range(24)))
        self.assertEqual(sum(map(len, workbench.MOG_OCTAD_ZONES)), 24)

    def test_example_build_is_deterministic_and_auditable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workbench.init_example(root)
            first_path, first_objects = workbench.build_study(root / "study.json")
            first_bytes = first_path.read_bytes()
            second_path, second_objects = workbench.build_study(root / "study.json")
            self.assertEqual(first_bytes, second_path.read_bytes())
            self.assertEqual(first_objects, second_objects)
            audit = workbench.audit_objects(second_objects)
            self.assertTrue(audit["structurally_valid"])
            self.assertEqual(audit["object_count"], 2)
            self.assertEqual(audit["missing_claim_count"], 1)
            self.assertEqual(second_objects[1]["claims"][1]["value"], None)
            self.assertEqual(second_objects[1]["claims"][1]["status"], "missing")

    def test_duplicate_identity_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workbench.init_example(root)
            records_path = root / "records.jsonl"
            lines = records_path.read_text(encoding="utf-8").splitlines()
            records_path.write_text("\n".join([lines[0], lines[0]]) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate canonical identities"):
                workbench.build_study(root / "study.json")

    def test_source_text_and_typed_value_are_both_retained(self):
        mapping = {
            "predicate": "length",
            "field": "length_text",
            "value_type": "number",
            "unit": "m",
            "uncertainty_field": "uncertainty",
            "status": "measured",
            "source_id_field": "source",
        }
        claim = workbench.build_claim(
            {"length_text": "1.2300", "uncertainty": "0.005", "source": "lab:7"},
            mapping,
            [""],
        )
        self.assertEqual(claim["value"], 1.23)
        self.assertEqual(claim["source_value_text"], "1.2300")
        self.assertEqual(claim["uncertainty"], "0.005")
        self.assertEqual(claim["provenance"]["source_id"], "lab:7")

    def test_audit_detects_identity_tampering(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workbench.init_example(root)
            _, objects = workbench.build_study(root / "study.json")
            objects[0]["subject"]["canonical_id"] = "figure:tampered"
            audit = workbench.audit_objects(objects)
            self.assertFalse(audit["structurally_valid"])
            self.assertTrue(any("hash mismatch" in error for error in audit["errors"]))

    def test_nonfinite_number_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "non-finite"):
            workbench.parse_typed("NaN", "number")


if __name__ == "__main__":
    unittest.main()
