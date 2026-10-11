"""Phase 116 -- roots with no expression in radicals in a degree that is not
a prime power, from one Frobenius element.

``studies/PRIMITIVE_DEGREE_STUDY.md`` measures the branch layer against marks
D1-D8 (:mod:`glm_universal.evaluation.primitive_degree_cases`).  These tests
hold the facts the round rests on; the full measurement, which reads every
declared question through the frames the CLI uses, is
``python3 -m glm_universal.tools primitive-degree``.

The tests stay below the frames on purpose: everything that reaches the
router takes the whole Lean development into its closure
(``ITERATION_COST_STUDY.md`` §5k), so the layer's wiring is checked here at
the branch layer itself (:func:`symbolic_nonlinear.solve_nonlinear`), which
the frame calls.
"""

from __future__ import annotations

import re
import unittest
from fractions import Fraction as F
from pathlib import Path

from glm_universal.evaluation import primitive_degree_cases as C
from glm_universal.reasoning import primitive_degree_groups as G
from glm_universal.reasoning import symbolic as S
from glm_universal.reasoning import symbolic_factor as Z
from glm_universal.reasoning import symbolic_nonlinear as N

LEAN_FILE = (Path(__file__).resolve().parents[2] / "glm_lean" /
             "RequestProject" / "GLM" / "PrimitiveDegree.lean")


def _q(ints):
    return [F(c) for c in ints]


def _poly(ints):
    x = S.Poly.var("x")
    p = S.Poly.const(0)
    for i, c in enumerate(ints):
        t = S.Poly.const(c)
        for _ in range(i):
            t = t * x
        p = p + t
    return p


def _branch_text(ints) -> str:
    b = N.solve_nonlinear([(S.RF(_poly(ints)), S.RF(S.Poly.const(0)))],
                          ["x"], ["x"])
    return repr(b)


class TestPrimePower(unittest.TestCase):

    def test_small_values(self):
        powers = [n for n in range(1, 30) if Z.is_prime_power(n)]
        self.assertEqual(powers, [2, 3, 4, 5, 7, 8, 9, 11, 13, 16, 17, 19,
                                  23, 25, 27, 29])

    def test_against_trial_division(self):
        for n in C.PRIME_POWER_RANGE:
            self.assertEqual(Z.is_prime_power(n),
                             G.prime_power_by_division(n), n)


class TestCayleySextic(unittest.TestCase):

    def test_scaled_declared_cases_are_integral(self):
        for _, (a, b), s in C.DEGREE:
            f = C.cayley_sextic(a, b)
            for i, c in enumerate(f):
                self.assertEqual(c % s ** (6 - i), 0)
            self.assertEqual(G.scaled_sextic(a, b, s)[-1], 1)

    def test_frobenius_quintic_has_a_rational_root(self):
        # x^5 + 15x + 12 has the Frobenius group of order 20: theta = 180
        f = C.cayley_sextic(15, 12)
        self.assertEqual(sum(c * 180 ** i for i, c in enumerate(f)), 0)
        self.assertFalse(G.irreducible(f))

    def test_declared_sextics_irreducible(self):
        for _, (a, b), s in C.DEGREE:
            self.assertTrue(G.irreducible(G.scaled_sextic(a, b, s)))


class TestGroups(unittest.TestCase):
    """Mark D3's group half: why Phase 114 could never reach these sextics."""

    def test_orders_and_transitivity(self):
        for special, order in ((False, 120), (True, 60)):
            g = G.projective_group(special)
            self.assertEqual(len(g), order)
            self.assertEqual({s[0] for s in g}, set(range(6)))

    def test_a_long_cycle_and_no_jordan_element(self):
        for special in (False, True):
            types = {tuple(G.cycle_degrees(s))
                     for s in G.projective_group(special)}
            self.assertIn((1, 5), types)
            self.assertEqual([t for t in types
                              if Z.jordan_power(list(t)) is not None], [])


class TestCertificate(unittest.TestCase):

    def test_fires_on_every_declared_sextic(self):
        for _, (a, b), s in C.DEGREE:
            f = _q(G.scaled_sextic(a, b, s))
            text = Z.radical_free_degree(f)
            self.assertIsNotNone(text)
            self.assertIn(Z.DEGREE_LEAN, text)
            self.assertIn("which is not a prime power", text)
            self.assertIn("degrees 1, 5", text)
            # Phase 114's two-element test is silent: no Jordan element
            self.assertIsNone(Z.radical_free_primitive(f))
            self.assertEqual(Z.radical_free_galois(f), text)

    def test_the_branch_layer_carries_it(self):
        _, (a, b), s = C.DEGREE[0]
        self.assertIn(Z.DEGREE_LEAN, _branch_text(G.scaled_sextic(a, b, s)))

    def test_the_branch_layer_is_silent_on_a_solvable_sextic(self):
        text = _branch_text([-2, 0, 0, 0, 0, 0, 1])          # x^6 - 2
        self.assertNotIn("no root of it is expressible in radicals", text)

    def test_silent_in_prime_power_degree(self):
        # x^8 - x - 1 has S_8; degree 8 is a prime power, so the new test
        # stays out and Phase 114's wording is kept
        f = _q([-1, -1, 0, 0, 0, 0, 0, 0, 1])
        self.assertIsNone(Z.radical_free_degree(f))
        self.assertIn(Z.PRIMITIVE_LEAN, Z.radical_free_galois(f))

    def test_phase_114_wording_kept_where_it_applies(self):
        f = _q([-1, -1, 0, 0, 0, 0, 1])           # x^6 - x - 1
        self.assertIn(Z.PRIMITIVE_LEAN, Z.radical_free_galois(f))

    def test_silent_on_solvable_sextics(self):
        for f in ([-2, 0, 0, 0, 0, 0, 1], [1, 0, 0, 1, 0, 0, 1],
                  [-1, 0, -1, 0, 0, 0, 1]):
            self.assertIsNone(Z.radical_free_degree(_q(f)))

    def test_silent_when_reducible(self):
        self.assertIsNone(Z.radical_free_degree(
            _q(C.cayley_sextic(15, 12)), irreducible=False))

    def test_reach_sample(self):
        # the first ten of the reach battery: every one certified by the new
        # statement and none by Phase 114's
        for ab, f in G.reach_polys()[:10]:
            text = Z.radical_free_galois(_q(f)) or ""
            self.assertIn(Z.DEGREE_LEAN, text, ab)
            self.assertNotIn(Z.PRIMITIVE_LEAN, text, ab)


class TestLean(unittest.TestCase):

    def test_every_named_theorem_and_no_sorry(self):
        src = LEAN_FILE.read_text(encoding="utf-8")
        code = re.sub(r"/-.*?-/", "", src, flags=re.S)
        code = re.sub(r"--[^\n]*", "", code)
        self.assertNotRegex(code, r"\bsorry\b")
        for name in ("isPrimePow_card_of_isPreprimitive_of_isSolvable",
                     "no_radical_root_of_long_cycle_of_not_isPrimePow"):
            self.assertRegex(code, rf"theorem\s+{name}\b")
        self.assertIn(Z.DEGREE_LEAN.rsplit(".", 1)[1], code)


if __name__ == "__main__":
    unittest.main()
