import csv
import json
import math
import unittest
from fractions import Fraction

import ubp_fundamental_kb_experiment as experiment


class UBPDependenceAndKBAuditTests(unittest.TestCase):
    def test_standardized_elements_are_complete_and_ordered(self):
        rows, audit = experiment.load_standardized_elements()
        self.assertEqual(len(rows), 118)
        self.assertEqual([r["id_atomic_number"] for r in rows], list(range(1, 119)))
        self.assertTrue(all(isinstance(r["atomic_mass"], Fraction) for r in rows))
        self.assertIn("M_Charge", audit["positionally_unsafe_categories"])
        self.assertIn("I_Complexity", audit["positionally_unsafe_categories"])
        self.assertTrue(all(audit["core_channel_completeness"][k]["observed"] == 118
                            for k in experiment.CORE_CHANNELS))

    def test_y_twin_is_declared_deterministic_map(self):
        left, right = [1.0, -2.0], [3.0, 5.0]
        descriptor = experiment._twin_pair_descriptor(left, right)
        self.assertEqual(len(descriptor), 12)
        self.assertTrue(all(math.isfinite(x) for x in descriptor))
        self.assertEqual(descriptor, experiment._twin_pair_descriptor(right, left))

    def test_peer_coherence_reports_absolute_and_relative_rules(self):
        rows, _ = experiment.load_standardized_elements()
        result = experiment.peer_coherence(rows)
        self.assertEqual(result["absolute_threshold"], 0.7)
        self.assertEqual(result["absolute_pass_elements"], 49)
        for grouping in (result["period_groups"], result["chemical_class_groups"]):
            self.assertEqual(sum(x["elements"] for x in grouping), 118)
            self.assertTrue(all(x["relative_pass_0_7_of_peer_median"] == x["elements"]
                                for x in grouping))

    def test_particle_audit_is_reproduction_not_holdout(self):
        rows, summary = experiment.particle_formula_audit()
        self.assertEqual(len(rows), 30)
        self.assertTrue(all(r["validation_status"] == "formula reproduction; not held-out" for r in rows))
        self.assertEqual(summary["canonical_formulae"], 9)
        self.assertEqual(summary["canonical_at_or_above_100_percent"], 3)
        self.assertTrue(any("anchor" in note.lower() for note in summary["independence_audit"]))

    def test_all_generated_outputs_and_holdout_folds(self):
        experiment.write_outputs()
        summary = json.loads(experiment.SUMMARY_OUT.read_text())
        self.assertEqual(summary["kb_schema_audit"]["element_entries"], 118)
        self.assertEqual(summary["coherence"]["absolute_pass_elements"], 49)
        with experiment.HOLDOUT_OUT.open(newline="", encoding="utf-8") as handle:
            metrics = list(csv.DictReader(handle))
        self.assertEqual(len(metrics), 19 * 3)
        self.assertEqual(set(r["configuration"] for r in metrics),
                         {"mean_only", "kb_math_standardized_ABC", "kb_math_Y_twin_ABC"})


if __name__ == "__main__":
    unittest.main()
