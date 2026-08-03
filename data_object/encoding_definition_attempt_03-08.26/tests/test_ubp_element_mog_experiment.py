import json
import math
import unittest

import golay_mog_experiments as base
import ubp_element_mog_experiment as experiment
import ubp_unified_v5 as ubp


class UBPElementMOGExperimentTests(unittest.TestCase):
    def test_all_element_words_have_valid_hexacode_shadows(self):
        hexacode = set(ubp.GolayCodeEngine.build_hexacode())
        for z in range(1, 119):
            word = experiment.element_codeword(z)
            self.assertEqual(len(word), 24)
            self.assertIn(ubp.GOLAY_ENGINE.mog_decompose(word)[0], hexacode)

    def test_descriptors_are_symmetric_and_finite(self):
        fixed = tuple(base.MOG_GRID_BITS)
        for left, right in ((1, 8), (6, 6), (17, 35)):
            forward = experiment.pair_ubp_descriptor(left, right, fixed)
            backward = experiment.pair_ubp_descriptor(right, left, fixed)
            self.assertEqual(forward, backward)
            self.assertTrue(all(math.isfinite(value) for value in forward))

    def test_tax_nrci_reduce_to_weight_on_binary_words(self):
        for z in range(1, 119):
            word = experiment.element_codeword(z)
            tax, nrci = experiment.tax_nrci(word)
            expected_tax = float(sum(word) * (experiment.Y + experiment.Fraction(1, 8)))
            self.assertAlmostEqual(tax, expected_tax)
            self.assertAlmostEqual(nrci, 10 / (10 + expected_tax))

    def test_complete_element_holdout_and_generated_summary(self):
        experiment.write_outputs()
        summary = json.loads(experiment.SUMMARY.read_text())
        self.assertEqual(summary["exact_audits"]["invalid_hexacode_shadows"], 0)
        self.assertEqual(summary["exact_audits"]["binary_tax_identity_failures"], 0)
        self.assertEqual(summary["exact_audits"]["element_identity_nrci_above_0_5"], 118)
        self.assertEqual(len(summary["fixed_results"]), 5)
        self.assertTrue(all(math.isfinite(row["macro_element_mae_kJ_mol"])
                            for row in summary["fixed_results"]))


if __name__ == "__main__":
    unittest.main()
