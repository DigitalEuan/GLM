"""The Monster Wheel (``glm_universal.wheels.monster_wheel``), pinned.

*Created 31 October 2026 (intake of glm_wheels_bundle; directive D22;
``studies/INTEGER_WHEEL_STUDY.md``).*

Ported from the supplied ``test_monster_wheel.py`` of ``glm_wheels_bundle``
(its five groups: sanity by order, factorisation, soundness, absorption,
non-repetition), in unittest style, against the absorbed wheel.  Added: the
26 sporadic groups of ``Wheels/SporadicOrders.lean`` read back and compared
with the Python data (names, orders, every ``order_<name>`` factorisation and
the exponent vectors), ``find_by_order`` against the Lean ``findByOrder``,
the factorisation helper :mod:`glm_universal.wheels.factorint`, and the
sporadic-order questions of the query surface.
"""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from glm_universal import constants as C
from glm_universal.wheels import lean_wheel_data as L
from glm_universal.wheels.cfsg_seed import (
    CFSG_GROUPS, GROUP_THEORY_OEIS, SPORADIC_ORDERS_SORTED, exponent_vector,
    factorize, order_from_factors,
)
from glm_universal.wheels.factorint import factorint, is_probable_prime, smallest_prime_factor
from glm_universal.wheels.integer_wheel import OEISEntry, default_wheel
from glm_universal.wheels.cfsg_import import extend_from_cfsg_directory
from glm_universal.wheels.monster_wheel import (
    PRIMES_TO_73, SORTED_ORDERS_ID, MonsterWheel, default_monster_wheel,
    supplied_monster_wheel,
)
from glm_universal.wheels.sequence_query import ANSWERED, UNANSWERED, NOT_MINE, answer_sequence_query

MONSTER_ORDER = 808017424794512875886459904961710757005754368000000000


def lean_find_by_order(orders, n):
    """``findByOrder n = (sporadicOrders.find? (fun g => g.2 = n)).map Prod.fst``."""
    for name, order in orders:
        if order == n:
            return name
    return None


def parse_python_factorisation(text):
    """``'2^4 · 3^2 · 5 · 11'`` -> ``((2, 4), (3, 2), (5, 1), (11, 1))``."""
    out = []
    for part in text.split("·"):
        m = re.fullmatch(r"\s*(\d+)(?:\^(\d+))?\s*", part)
        out.append((int(m.group(1)), int(m.group(2)) if m.group(2) else 1))
    return tuple(out)


class TestSanityPorted(unittest.TestCase):
    """Group 1 of the supplied test: each group by its order; non-orders
    silent."""

    @classmethod
    def setUpClass(cls):
        cls.w = default_monster_wheel()

    def test_each_group_by_its_order(self):
        self.assertEqual(len(CFSG_GROUPS), 26)
        for gid, _name, order, *_rest in CFSG_GROUPS:
            self.assertEqual(self.w.find_by_order(order), gid)

    def test_non_orders_stay_silent(self):
        for n in (7, 60, 168, 660, 1234567890, 1, 0, 7919, 7921, MONSTER_ORDER + 1):
            self.assertIsNone(self.w.find_by_order(n), n)

    def test_only_the_groups_are_single_term_entries(self):
        single = sorted(e.oeis_id for e in self.w.entries() if len(e.terms) == 1
                        and not e.oeis_id.endswith("-EXPVEC"))
        self.assertEqual(single, sorted(g[0] for g in CFSG_GROUPS))


class TestFactorisationPorted(unittest.TestCase):
    """Group 2 of the supplied test."""

    @classmethod
    def setUpClass(cls):
        cls.w = default_monster_wheel()

    def test_find_by_factorization(self):
        for gid, _name, order, *_rest in CFSG_GROUPS:
            f = factorize(order)
            self.assertEqual(self.w.find_by_factorization([p for p, _ in f],
                                                          [e for _, e in f]), gid)
            self.assertEqual(order_from_factors(f), order)

    def test_find_by_exponent_vector(self):
        for gid, _name, order, *_rest in CFSG_GROUPS:
            ev = list(exponent_vector(order, max_prime=73))
            while ev and ev[-1] == 0:
                ev.pop()
            self.assertEqual(self.w.find_by_exponent_vector(ev), gid)
        self.assertEqual(self.w.find_by_exponent_vector([4, 2, 1, 0, 1]), "M11")
        self.assertIsNone(self.w.find_by_exponent_vector([0] * 21))
        self.assertIsNone(self.w.find_by_factorization([2, 3], [4]))

    def test_the_factoriser(self):
        self.assertEqual(factorint(7920), {2: 4, 3: 2, 5: 1, 11: 1})
        self.assertEqual(factorint(1), {})
        self.assertEqual(factorint(97), {97: 1})
        self.assertEqual(smallest_prime_factor(91), 7)
        self.assertTrue(is_probable_prime(2 ** 61 - 1))
        self.assertFalse(is_probable_prime(2 ** 61 + 1))
        n = (2 ** 61 - 1) * (2 ** 31 - 1) * 1009 ** 2
        self.assertEqual(factorint(n), {2 ** 61 - 1: 1, 2 ** 31 - 1: 1, 1009: 2})
        f = factorint(MONSTER_ORDER)
        product = 1
        for p, e in f.items():
            self.assertTrue(is_probable_prime(p))
            product *= p ** e
        self.assertEqual(product, MONSTER_ORDER)


class TestSoundnessPorted(unittest.TestCase):
    """Group 3 of the supplied test."""

    def test_audit_soundness(self):
        for w in (default_monster_wheel(), supplied_monster_wheel()):
            report = w.audit_soundness()
            self.assertEqual(report["unsound"], 0)
            self.assertEqual(report["entries"],
                             report["sound"] + report["silent"] + report["unsound"])

    def test_spot_checks(self):
        w = default_monster_wheel()
        for _gid, _name, order, *_rest in CFSG_GROUPS:
            spoken = w.find_by_order(order)
            self.assertIsNotNone(spoken)
            self.assertTrue(w.soundness_check([order], spoken))


_SYNTH_LEAN = """module

/-! Synthetic CFSG-style Lean file for testing the parser. -/

namespace CFSG.Sporadic.Synth

/-- The order of the synthetic test group T1. -/
theorem card_T1 : card T1 = 1234567890 := by
  sorry

/-- The order of the synthetic test group T2. -/
theorem card_T2 : card T2 = 9876543210 := by
  sorry

/-- A have declaration. -/
have h_card_T3 : card T3 = 1024 := by
  sorry

end CFSG.Sporadic.Synth
"""


class TestAbsorptionPorted(unittest.TestCase):
    """Group 4 of the supplied test (the parser reads only the files it is
    given; nothing here touches the repository's Lean tree)."""

    def setUp(self):
        self.w = default_monster_wheel()

    def test_the_parser(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Synth.lean"
            path.write_text(_SYNTH_LEAN, encoding="utf-8")
            entries = self.w.parse_cfsg_lean_file(path)
        self.assertEqual(sorted((e.oeis_id, e.terms) for e in entries),
                         [("T1", (1234567890,)), ("T2", (9876543210,)), ("T3", (1024,))])

    def test_register_and_speak(self):
        self.w.register(OEISEntry("TITANS", "(synthetic) Titan groups T_n",
                                  (1000, 2000, 3000, 4000, 5000)))
        self.assertIn("TITANS", self.w)
        self.assertEqual(self.w.speak([1000, 2000, 3000, 4000, 5000]), "TITANS")

    def test_extend_from_a_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Group1.lean").write_text(
                "theorem card_G1 : card G1 = 100 := by sorry\n"
                "theorem card_G2 : card G2 = 200 := by sorry\n", encoding="utf-8")
            (root / "Group2.lean").write_text(
                "theorem card_H1 : card H1 = 300 := by sorry\n"
                "theorem card_M11 : card M11 = 1 := by sorry\n", encoding="utf-8")
            added, failed = extend_from_cfsg_directory(self.w, root)
        self.assertEqual((added, failed), (3, 0))
        for gid in ("G1", "G2", "H1"):
            self.assertIn(gid, self.w)
        self.assertEqual(self.w.get("M11").terms, (7920,))   # never overwritten

    def test_merge_keeps(self):
        fresh = default_monster_wheel()
        self.w.register(OEISEntry("TITANS", "t", (1000, 2000)))
        merged = self.w.merge(fresh)
        self.assertEqual(len(merged), len(self.w))
        self.assertEqual(merged.audit_soundness()["unsound"], 0)


class TestNonRepetitionPorted(unittest.TestCase):
    """Group 5 of the supplied test."""

    @classmethod
    def setUpClass(cls):
        cls.w = default_monster_wheel()
        cls.iw = default_wheel()

    def test_the_order_provision(self):
        prov = self.w.needs_wheel_provision()
        self.assertEqual(prov(7920), "M11")
        self.assertIsNone(prov(60))
        self.assertEqual(self.iw.speak([0, 1, 1, 2, 3, 5, 8, 13, 21, 34]), "A000045")

    def test_the_monster_speaks_m(self):
        spoken = self.w.find_by_order(MONSTER_ORDER)
        self.assertEqual(spoken, "M")
        self.assertFalse(spoken.startswith("A"))

    def test_all_26_and_a_superset_of_the_integer_wheel(self):
        self.assertEqual(set(self.w.group_ids()), {g[0] for g in CFSG_GROUPS})
        for e in self.iw.entries():                  # merge_keeps
            self.assertEqual(self.w.get(e.oeis_id).terms, e.terms)

    def test_the_port_is_the_supplied_data(self):
        from glm_universal.tests.test_integer_wheel import load_supplied, supplied_rows
        supplied = load_supplied("cfsg_seed.py")
        if supplied is None:
            self.skipTest("the supplied item is not in this checkout")
        self.assertEqual([tuple(g) for g in CFSG_GROUPS],
                         [tuple(g) for g in supplied.CFSG_GROUPS])
        self.assertEqual(supplied_rows(GROUP_THEORY_OEIS),
                         supplied_rows(supplied.GROUP_THEORY_OEIS))
        self.assertEqual(list(SPORADIC_ORDERS_SORTED), list(supplied.SPORADIC_ORDERS_SORTED))

    def test_the_absorbed_inventory(self):
        self.assertEqual(len(self.w), 161)
        self.assertEqual(len(supplied_monster_wheel()), 240)
        self.assertIn(SORTED_ORDERS_ID, self.w)
        self.assertEqual(self.w.get(SORTED_ORDERS_ID).terms, tuple(SPORADIC_ORDERS_SORTED))
        self.assertNotIn("A001034", self.w)          # another sequence's id
        self.assertEqual(len(GROUP_THEORY_OEIS), 5)


class TestLeanAgreement(unittest.TestCase):
    """``Wheels/SporadicOrders.lean`` read back, against the Python data."""

    @classmethod
    def setUpClass(cls):
        cls.path = C.lean_file(L.SPORADIC_ORDERS_LEAN)
        cls.orders = L.sporadic_orders()
        cls.facts = L.sporadic_factorisations()

    def test_the_file_is_in_the_build_tree_and_audited(self):
        from glm_universal import lean_check
        self.assertTrue(self.path.is_file())
        self.assertTrue(lean_check.audited_or_held(L.SPORADIC_ORDERS_LEAN))
        text = L.lean_text(L.SPORADIC_ORDERS_LEAN)
        self.assertIn("namespace GLM.SporadicOrders", text)
        for name in ("sporadicOrders_length", "sporadicOrders_nodup",
                     "sporadicNames_nodup", "findByOrder_sound", "findByOrder_complete"):
            self.assertRegex(text, rf"(?m)^theorem\s+{name}\b")
        self.assertNotIn("native_decide", re.sub(r"/-.*?-/", "", text, flags=re.DOTALL))

    def test_names_and_orders(self):
        self.assertEqual(len(self.orders), 26)
        self.assertEqual(self.orders, tuple((g[0], g[2]) for g in CFSG_GROUPS))
        self.assertEqual(len({n for n, _ in self.orders}), 26)
        self.assertEqual(len({o for _, o in self.orders}), 26)
        self.assertEqual(tuple(sorted(o for _, o in self.orders)),
                         tuple(SPORADIC_ORDERS_SORTED))

    def test_every_order_theorem(self):
        self.assertEqual(sorted(self.facts), sorted(g[0] for g in CFSG_GROUPS))
        for gid, _name, order, fact, *_rest in CFSG_GROUPS:
            with self.subTest(gid=gid):
                stated, factors = self.facts[gid]
                self.assertEqual(stated, order)
                product = 1
                for p, e in factors:
                    product *= p ** e
                self.assertEqual(product, order)
                self.assertEqual(factors, parse_python_factorisation(fact))
                self.assertEqual(tuple(factorize(order)), factors)
                vector = [dict(factors).get(p, 0) for p in PRIMES_TO_73]
                self.assertEqual(list(exponent_vector(order, max_prime=73)), vector)
                self.assertEqual(default_monster_wheel().get(gid + "-EXPVEC").terms,
                                 tuple(vector))

    def test_find_by_order_is_lean_find_by_order(self):
        w = default_monster_wheel()
        probes = [o for _, o in self.orders] + [o + 1 for _, o in self.orders] + [
            0, 1, 7, 60, 168, 20160, 7919, 7921]
        for n in probes:
            self.assertEqual(w.find_by_order(n), lean_find_by_order(self.orders, n), n)


class TestOrderQuestions(unittest.TestCase):
    """The sporadic-order questions of ``answer_sequence_query``."""

    def test_forward(self):
        for gid, name, order, *_rest in CFSG_GROUPS:
            code, reply = answer_sequence_query(f"which sporadic group has order {order}")
            self.assertEqual(code, ANSWERED)
            self.assertTrue(reply.startswith(f"{gid} — "), reply)
        code, reply = answer_sequence_query("which sporadic group has order 2^4 * 3^2 * 5 * 11")
        self.assertEqual((code, reply[:3]), (ANSWERED, "M11"))
        code, reply = answer_sequence_query("which sporadic group has order 7,920?")
        self.assertEqual((code, reply[:3]), (ANSWERED, "M11"))

    def test_reverse(self):
        code, reply = answer_sequence_query("what is the order of the Monster group")
        self.assertEqual(code, ANSWERED)
        self.assertIn(str(MONSTER_ORDER), reply)
        code, reply = answer_sequence_query("what is the order of the sporadic group M24")
        self.assertEqual(code, ANSWERED)
        self.assertIn("244823040", reply)
        code, reply = answer_sequence_query("what is the order of the sporadic group He")
        self.assertIn("4030387200", reply)

    def test_refused(self):
        for text in ("which sporadic group has order 60",
                     "which sporadic group has order 2^4 * 3^2 * 5 * 13",
                     "what is the order of the sporadic group M13",
                     "which sporadic group has order 2^99999999"):
            with self.subTest(text=text):
                self.assertEqual(answer_sequence_query(text)[0], UNANSWERED)
        for text in ("what is the order of the group S5", "what is the order of the B-tree",
                     "what is the order of the group held by the army"):
            with self.subTest(text=text):
                self.assertEqual(answer_sequence_query(text)[0], NOT_MINE)


if __name__ == "__main__":
    unittest.main()
