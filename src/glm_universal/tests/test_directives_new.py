"""Tests for the three new directive subsystems: Wobble (D17),
Reversibility (D18), and Generate-don't-store (D19).
"""
from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.reasoning import wobble_registry as wobble, reversibility, generate_not_store


class TestWobble(unittest.TestCase):
    """The Wobble registry (D17)."""

    def test_registry_has_builtin_sources(self):
        """pi, e, and sqrt(2) are registered."""
        qs = wobble.quantities()
        self.assertIn("pi", qs)
        self.assertIn("e", qs)
        self.assertIn("sqrt(2)", qs)

    def test_wobble_returns_enclosure(self):
        """wobble() returns a (lower, upper) pair of Fractions."""
        lower, upper = wobble.wobble("pi", Fraction(1, 1000))
        self.assertIsInstance(lower, Fraction)
        self.assertIsInstance(upper, Fraction)
        self.assertLess(lower, upper)

    def test_wobble_raises_on_unknown(self):
        with self.assertRaises(KeyError):
            wobble.wobble("unknown_quantity", Fraction(1, 100))

    def test_consumers_of(self):
        """pi has consumers."""
        consumers = wobble.consumers_of("pi")
        self.assertGreater(len(consumers), 0)

    def test_wobble_report(self):
        r = wobble.wobble_report()
        self.assertGreater(r["count"], 0)
        self.assertTrue(r["holds"])
        self.assertIn("pi", r["quantities"])


class TestReversibility(unittest.TestCase):
    """The Reversibility ledger (D18)."""

    def test_ledger_has_builtin_operations(self):
        """golay.encode, corpus.ask, combiner.xor are registered."""
        ops = reversibility.all_operations()
        names = [op.name for op in ops]
        self.assertIn("golay.encode", names)
        self.assertIn("corpus.ask", names)
        self.assertIn("combiner.xor", names)

    def test_bijective_has_inverse(self):
        """golay.encode is bijective with inverse golay.decode."""
        self.assertEqual(reversibility.class_of("golay.encode"), "bijective")
        self.assertEqual(reversibility.inverse_of("golay.encode"), "golay.decode")

    def test_forward_only_has_no_inverse(self):
        """corpus.ask is forward_only with empty inverse."""
        self.assertEqual(reversibility.class_of("corpus.ask"), "forward_only")
        self.assertEqual(reversibility.inverse_of("corpus.ask"), "")

    def test_declared_lossy_has_witness(self):
        """combiner.xor is declared_lossy with a witness."""
        self.assertEqual(reversibility.class_of("combiner.xor"), "declared_lossy")
        self.assertGreater(len(reversibility.loss_witness_of("combiner.xor")), 0)

    def test_reversibility_report(self):
        r = reversibility.reversibility_report()
        self.assertGreater(r["count"], 0)
        self.assertTrue(r["holds"])
        self.assertIn("bijective", r["by_class"])
        self.assertIn("forward_only", r["by_class"])
        self.assertIn("declared_lossy", r["by_class"])

    def test_four_classes_represented(self):
        """All four reversibility classes are represented."""
        r = reversibility.reversibility_report()
        for cls in ("bijective", "has_inverse", "forward_only", "declared_lossy"):
            self.assertIn(cls, r["by_class"], f"class {cls} not represented")


class TestGenerateNotStore(unittest.TestCase):
    """The Generate-don't-store registry (D19)."""

    def test_registry_has_builtin_regenerators(self):
        """FIGURES.md and DIGEST.md are registered."""
        paths = generate_not_store.stored_files()
        self.assertIn("FIGURES.md", paths)
        self.assertIn("DIGEST.md", paths)

    def test_regenerator_of(self):
        """regenerator_of returns the regenerator for a path."""
        regen = generate_not_store.regenerator_of("FIGURES.md")
        self.assertIsNotNone(regen)
        self.assertIn("figures", regen.description.lower())

    def test_audit_returns_report(self):
        """audit() returns a report with the expected keys."""
        r = generate_not_store.audit()
        self.assertIn("registered", r)
        self.assertIn("present", r)
        self.assertIn("absent", r)
        self.assertIn("matches", r)
        self.assertIn("mismatches", r)
        self.assertIn("holds", r)

    def test_generate_not_store_report(self):
        r = generate_not_store.generate_not_store_report()
        self.assertGreater(r["registered"], 0)


class TestStudyLedger(unittest.TestCase):
    """The rebuilt study ledger."""

    def test_ledger_loads(self):
        """The ledger loads the YAML manifests."""
        from glm_universal.corpus import study_ledger
        led = study_ledger.ledger()
        self.assertGreater(led["counts"]["studies"], 100)

    def test_ledger_has_predecessors(self):
        """The ledger has predecessor edges."""
        from glm_universal.corpus import study_ledger
        led = study_ledger.ledger()
        self.assertGreater(led["counts"]["edges"], 50)

    def test_ledger_is_acyclic(self):
        """The predecessor graph is acyclic (strict-phase filter)."""
        from glm_universal.corpus import study_ledger
        led = study_ledger.ledger()
        self.assertTrue(led["acyclic"], f"cycle found: {led['cycle']}")

    def test_ledger_report(self):
        from glm_universal.corpus import study_ledger
        r = study_ledger.study_ledger_report()
        self.assertIn("summary", r)
        self.assertIn("edges", r["summary"])
        self.assertIn("acyclic", r["summary"])
        self.assertTrue(r["holds"])


if __name__ == "__main__":
    unittest.main()
