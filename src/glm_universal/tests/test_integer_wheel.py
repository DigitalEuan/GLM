"""The Integer Wheel (``glm_universal.wheels.integer_wheel``), pinned.

*Created 31 October 2026 (intake of glm_wheels_bundle; directive D22;
``studies/INTEGER_WHEEL_STUDY.md``).*

Ported from the supplied ``test_integer_wheel.py`` of ``glm_wheels_bundle``
(its five groups: sanity, Rule 30, soundness, non-repetition, merge/turn), in
unittest style, against the *absorbed* wheel -- the supplied entries the
independent reference reproduces (:mod:`glm_universal.wheels.oeis_reference`).
Where the supplied test asserted an identification the audit holds out, the
port asserts what is true instead: the supplied wheel says it, the absorbed
wheel does not, and the reason is pinned.  Added: the provision contract of
``Wheels/IntegerWheel.lean`` checked clause by clause on the real data
(``speak`` exactly as the Lean defines it), the eight ``termsAxxxxxx`` lists of
the Lean file against the Python entries, the audit, the query surface
:mod:`glm_universal.wheels.sequence_query` and the study's measurement
:mod:`glm_universal.wheels.integer_wheel_study`.

*Last altered 31 October 2026 (repository check): the wheels are installed
provisionally (the owner's decision, until the Lean build confirms
``Wheels/IntegerWheel.lean`` and ``Wheels/SporadicOrders.lean``); S2 is put to
the command line without the wheels, and the wired command line answers with
the provisional note.*

*Last altered 1 November 2026 (Phase 186): the wheels absorbed ahead of the
owner's build; S2's wired command line answers with the register's note in
either state.*
"""

from __future__ import annotations

import math
import subprocess
import sys
import unittest

from glm_universal import constants as C
from glm_universal.wheels import PROVISION_WHEELS, provision_wheel, ALL_WHEELS
from glm_universal.wheels import integer_wheel_study as S
from glm_universal.wheels import lean_wheel_data as L
from glm_universal.wheels import oeis_reference as R
from glm_universal.wheels.integer_wheel import (
    IntegerWheel, OEISEntry, default_wheel, supplied_wheel, supplied_entries,
)
from glm_universal.wheels.monster_wheel import default_monster_wheel
from glm_universal.wheels.sequence_query import (
    ANSWERED, NOT_MINE, UNANSWERED, answer_sequence_query, parse_order,
    resolve_query, sequence_terms,
)

_IW = None
_SW = None
_MW = None


def iw() -> IntegerWheel:
    global _IW
    if _IW is None:
        _IW = default_wheel()
    return _IW


def sw() -> IntegerWheel:
    global _SW
    if _SW is None:
        _SW = supplied_wheel()
    return _SW


def mw():
    global _MW
    if _MW is None:
        _MW = default_monster_wheel()
    return _MW


# ---------------------------------------------------------------------------
# The Lean definitions of Wheels/IntegerWheel.lean, transliterated
# ---------------------------------------------------------------------------

def lean_is_prefix(c, terms) -> bool:
    """``c <+: terms``."""
    return len(c) <= len(terms) and tuple(terms[:len(c)]) == tuple(c)


def lean_provision(entry, c):
    """``provision e c = if c ≠ [] ∧ c <+: e.terms then some e.id else none``."""
    return entry.oeis_id if (len(c) > 0 and lean_is_prefix(c, entry.terms)) else None


def lean_least(ids):
    """``least``: ``none`` on ``[]``, else the minimum."""
    out = None
    for i in ids:
        out = i if out is None else min(out, i)
    return out


def lean_speak(entries, c):
    """``speak w c = if c = [] then none else least ((chosen w c).map Entry.id)``
    with ``chosen`` the exact matches if any, else the prefix matches."""
    c = tuple(c)
    if not c:
        return None
    exact = [e for e in entries if tuple(e.terms) == c]
    prefix = [e for e in entries if lean_is_prefix(c, e.terms)]
    chosen = prefix if not exact else exact
    return lean_least(e.oeis_id for e in chosen)


def load_supplied(name: str):
    """The supplied file ``glm_wheels_bundle/<name>`` as a module (from
    ``ToDo/`` or ``done/``), or ``None`` when the item is not in the
    checkout.  Its folder is on ``sys.path`` only while it loads."""
    import importlib.util
    path = C.source_material_item(f"glm_wheels_bundle/{name}")
    if not path.is_file():
        return None
    folder = str(path.parent)
    sys.path.insert(0, folder)
    no_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True          # leave the supplied folder as it is
    try:
        spec = importlib.util.spec_from_file_location(f"_supplied_{path.stem}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = no_bytecode
        sys.path.remove(folder)
        sys.modules.pop("factorint_compat", None)
    return module


def supplied_rows(rows):
    """Seed rows with their terms as lists, for comparing a port with the
    supplied file."""
    return [(r[0], r[1], list(r[2])) + tuple(r[3:]) for r in rows]


def rule30_centre(n: int):
    """Rule 30 from a single black cell, the centre cell at steps 0..n-1."""
    width = 2 * n + 3
    row = [0] * width
    row[width // 2] = 1
    out = []
    for _ in range(n):
        out.append(row[width // 2])
        row = [0] + [(30 >> (row[i - 1] * 4 + row[i] * 2 + row[i + 1])) & 1
                     for i in range(1, width - 1)] + [0]
    return out


# ---------------------------------------------------------------------------
# Group 1 (ported): sanity
# ---------------------------------------------------------------------------

#: The supplied test's 53 sanity cases (name, terms, the id it expected).
SANITY_CASES = (
    ("Fibonacci numbers", [0, 1, 1, 2, 3, 5, 8, 13, 21, 34], "A000045"),
    ("Lucas numbers", [2, 1, 3, 4, 7, 11, 18, 29, 47, 76], "A000032"),
    ("Prime numbers", [2, 3, 5, 7, 11, 13, 17, 19, 23, 29], "A000040"),
    ("Composite numbers", [4, 6, 8, 9, 10, 12, 14, 15, 16, 18], "A002808"),
    ("Powers of 2", [1, 2, 4, 8, 16, 32, 64, 128, 256, 512], "A000079"),
    ("Powers of 3", [1, 3, 9, 27, 81, 243, 729, 2187, 6561], "A000244"),
    ("Factorials", [1, 1, 2, 6, 24, 120, 720, 5040, 40320], "A000142"),
    ("Squares", [0, 1, 4, 9, 16, 25, 36, 49, 64, 81], "A000290"),
    ("Cubes", [0, 1, 8, 27, 64, 125, 216, 343, 512], "A000578"),
    ("Triangular", [0, 1, 3, 6, 10, 15, 21, 28, 36, 45], "A000217"),
    ("Tetrahedral", [0, 1, 4, 10, 20, 35, 56, 84, 120, 165], "A000292"),
    ("Catalan", [1, 1, 2, 5, 14, 42, 132, 429, 1430], "A000108"),
    ("Bell", [1, 1, 2, 5, 15, 52, 203, 877, 4140], "A000110"),
    ("Motzkin", [1, 1, 2, 4, 9, 21, 51, 127, 323, 835], "A001006"),
    ("Padovan", [1, 0, 0, 1, 0, 1, 1, 1, 2, 2], "A000931"),
    ("Narayana cows", [1, 1, 1, 2, 3, 4, 6, 9, 13, 19], "A000930"),
    ("Tribonacci", [0, 0, 1, 1, 2, 4, 7, 13, 24, 44], "A000073"),
    ("Jacobsthal", [0, 1, 1, 3, 5, 11, 21, 43, 85, 171], "A001045"),
    ("Perrin", [3, 0, 2, 3, 2, 5, 5, 7, 10, 12], "A001608"),
    ("Derangements", [1, 0, 1, 2, 9, 44, 265, 1854], "A000166"),
    ("Involutions", [1, 1, 2, 4, 10, 26, 76, 232], "A000085"),
    ("Mersenne numbers (2^n-1)", [0, 1, 3, 7, 15, 31, 63, 127, 255, 511], "A000225"),
    ("Primorial", [1, 2, 6, 30, 210, 2310, 30030], "A002110"),
    ("Highly composite", [1, 2, 4, 6, 12, 24, 36, 48, 60, 120], "A002182"),
    ("Ulam numbers", [1, 2, 3, 4, 6, 8, 11, 13, 16, 18], "A002858"),
    ("LCM 1..n", [1, 1, 2, 6, 12, 60, 60, 420, 840], "A003418"),
    ("Recaman", [0, 1, 3, 6, 2, 7, 13, 20, 12, 21], "A005132"),
    ("Odd numbers", [1, 3, 5, 7, 9, 11, 13, 15, 17, 19], "A005408"),
    ("Even numbers", [0, 2, 4, 6, 8, 10, 12, 14, 16, 18], "A005843"),
    ("Thue-Morse", [0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0], "A010060"),
    ("Evil numbers", [0, 3, 5, 6, 9, 10, 12, 15, 17, 18], "A001969"),
    ("Odious numbers", [1, 2, 4, 7, 8, 11, 13, 14, 16, 19], "A000069"),
    ("Hamming weight", [0, 1, 1, 2, 1, 2, 2, 3, 1, 2], "A000120"),
    ("Pascal flattened", [1, 1, 1, 1, 2, 1, 1, 3, 3, 1], "A007318"),
    ("e digits", [2, 7, 1, 8, 2, 8, 1, 8, 2, 8, 4, 5, 9, 0, 4, 5], "A001113"),
    ("pi digits", [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8, 9, 7, 9, 3], "A000796"),
    ("sqrt(2) digits", [1, 4, 1, 4, 2, 1, 3, 5, 6, 2, 3, 7, 3, 0, 9, 5], "A010505"),
    ("golden ratio digits", [1, 6, 1, 8, 0, 3, 3, 9, 8, 8, 7, 4, 9, 8, 9, 4], "A001622"),
    ("ln(2) digits", [6, 9, 3, 1, 4, 7, 1, 8, 0, 5, 5, 9, 9, 4, 5, 3], "A002162"),
    ("Pell numbers", [0, 1, 2, 5, 12, 29, 70, 169, 408, 985], "A000129"),
    ("Stern's diatomic", [0, 1, 1, 2, 1, 3, 2, 3, 1, 4], "A002487"),
    ("Woodall numbers", [1, 7, 23, 63, 159, 383, 895, 2047, 4607], "A003261"),
    ("Look-and-say lengths", [1, 2, 2, 4, 6, 6, 8, 10, 14, 20], "A001155"),
    ("Pentagonal numbers", [0, 1, 5, 12, 22, 35, 51, 70, 92, 117], "A000326"),
    ("Hexagonal numbers", [1, 6, 15, 28, 45, 66, 91, 120, 153], "A000384"),
    ("Double factorial (odd)", [1, 1, 3, 15, 105, 945, 10395, 135135], "A001147"),
    ("Generalized pentagonal", [0, 1, 2, 5, 7, 12, 15, 22, 26, 35], "A001318"),
    ("Number of divisors", [1, 2, 2, 3, 2, 4, 2, 4, 3, 4], "A000005"),
    ("Euler totient", [1, 1, 2, 2, 4, 2, 6, 4, 6, 4], "A000010"),
    ("Prime counting pi(n)", [0, 0, 1, 2, 2, 3, 3, 4, 4, 4], "A000720"),
    ("All-1s", [1, 1, 1, 1, 1, 1, 1, 1, 1, 1], "A000012"),
    ("Zero sequence", [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], "A000004"),
    ("All-0s characteristic", [1, 0, 0, 0, 0, 0, 0, 0, 0, 0], "A000007"),
)

#: The three supplied identifications the audit holds out, and why.  The
#: OEIS has the digits of sqrt 2 as A002193 and the look-and-say lengths as
#: A005341; A000720 (pi(n)) has offset 1, while the stored list starts with
#: pi(0) = 0.
HELD_OUT_CASES = {
    "A010505": R.NOT_RECOMPUTED,
    "A001155": R.NOT_RECOMPUTED,
    "A000720": R.DISAGREES,
}


class TestSanityPorted(unittest.TestCase):
    """Group 1 of the supplied test, on the absorbed wheel."""

    def test_the_supplied_cases(self):
        self.assertEqual(len(SANITY_CASES), 53)
        for name, seq, expected in SANITY_CASES:
            with self.subTest(name=name):
                if expected in HELD_OUT_CASES:
                    self.assertEqual(sw().speak(seq), expected)
                    self.assertIsNone(iw().speak(seq))
                    self.assertNotIn(expected, iw())
                else:
                    self.assertEqual(iw().speak(seq), expected)

    def test_why_three_are_held_out(self):
        for oid, verdict in HELD_OUT_CASES.items():
            with self.subTest(oid=oid):
                entry = sw().get(oid)
                self.assertEqual(R.audit_entry(oid, entry.terms)["verdict"], verdict)

    def test_no_match_stays_silent(self):
        self.assertIsNone(iw().speak([4, 8, 15, 16, 23, 42, 999, 1234, 5678, 90123]))
        self.assertIsNone(iw().speak([42, 71, 9, 333, 90210, 8675309]))
        self.assertIsNone(iw().speak([7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
                                      53, 59, 61, 67, 71, 73, 79, 83]))


# ---------------------------------------------------------------------------
# Group 2 (ported): Rule 30
# ---------------------------------------------------------------------------

class TestRule30Ported(unittest.TestCase):
    """Group 2 of the supplied test.  The supplied centre column is not the
    Rule 30 centre column: it differs from the rule, run here, at term 5, so
    the absorbed wheel does not hold it (the supplied wheel speaks A051023
    on it, as the supplied test expected)."""

    ITEM_CC = [1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1]

    def test_the_rule_itself(self):
        cc = rule30_centre(20)
        self.assertEqual(cc[:5], self.ITEM_CC[:5])
        self.assertNotEqual(cc[5], self.ITEM_CC[5])
        self.assertEqual(tuple(cc), R.reference_terms("A051023", 20))

    def test_the_supplied_column_is_held_out(self):
        self.assertEqual(sw().speak(self.ITEM_CC), "A051023")
        self.assertEqual(sw().speak(self.ITEM_CC[:10]), "A051023")
        self.assertIsNone(iw().speak(self.ITEM_CC))
        self.assertNotIn("A051023", iw())
        self.assertEqual(R.audit_entry("A051023", sw().get("A051023").terms)["verdict"],
                         R.DISAGREES)

    def test_the_other_rule30_lists(self):
        self.assertIsNone(iw().speak([0, 3, 8, 29, 400, 87867]))
        self.assertEqual(iw().speak([1, 2, 4, 8, 16, 32]), "A000079")
        white = [2, 7, 28]
        spoken = iw().speak(white)
        if spoken is not None:
            self.assertTrue(iw().soundness_check(white, spoken))
        self.assertIsNone(iw().speak([100, 99, 99, 98, 96, 92, 84]))
        self.assertIsNone(iw().speak([3200, 81, 441, 8]))


# ---------------------------------------------------------------------------
# Group 3 (ported): soundness
# ---------------------------------------------------------------------------

class TestSoundnessPorted(unittest.TestCase):

    def test_audit_soundness(self):
        for wheel in (iw(), sw()):
            report = wheel.audit_soundness()
            self.assertEqual(report["unsound"], 0)
            self.assertEqual(report["entries"],
                             report["sound"] + report["silent"] + report["unsound"])

    def test_spot_checks(self):
        claims = [
            [0, 1, 1, 2, 3, 5, 8, 13, 21, 34],
            [2, 3, 5, 7, 11, 13, 17, 19, 23, 29],
            [1, 2, 4, 8, 16, 32, 64, 128, 256, 512],
            [1, 1, 2, 5, 14, 42, 132, 429, 1430, 4862],
            [1, 1, 2, 3, 5, 7, 11, 15, 22, 30],
            [0, 1, 3, 6, 2, 7, 13, 20, 12, 21],
            [1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1],
            [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8, 9, 7, 9, 3],
            [2, 7, 1, 8, 2, 8, 1, 8, 2, 8, 4, 5, 9, 0, 4, 5],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ]
        for c in claims:
            spoken = iw().speak(c)
            if spoken is None:
                continue
            self.assertTrue(iw().soundness_check(c, spoken))
            self.assertEqual(iw().get(spoken).matches(tuple(c)), len(c))


# ---------------------------------------------------------------------------
# Group 4 (ported): non-repetition
# ---------------------------------------------------------------------------

class TestNonRepetitionPorted(unittest.TestCase):

    def test_provision_signature(self):
        prov = iw().needs_wheel_provision()
        self.assertEqual(prov([0, 1, 1, 2, 3, 5]), "A000045")
        self.assertIsNone(prov([4, 8, 15, 16, 23, 42]))

    def test_sample_ids(self):
        for oid in ("A000045", "A000040", "A000079", "A001113", "A000796",
                    "A000108", "A000110", "A010060", "A005132"):
            self.assertIn(oid, iw())
        self.assertNotIn("A051023", iw())         # held out (see Group 2)

    def test_spoken_output_is_an_oeis_id(self):
        spoken = iw().speak([0, 1, 1, 2, 3, 5, 8, 13, 21, 34])
        self.assertIsInstance(spoken, str)
        self.assertTrue(spoken.startswith("A"))

    def test_a_separate_family_from_the_fifteen(self):
        self.assertEqual(len(ALL_WHEELS), 15)
        self.assertEqual(tuple(p.id for p in PROVISION_WHEELS), ("IW", "MW"))
        self.assertEqual(set(provision_wheel("IW").build().ids()), set(iw().ids()))
        with self.assertRaises(KeyError):
            provision_wheel("W1")


# ---------------------------------------------------------------------------
# Group 5 (ported): merge / turn
# ---------------------------------------------------------------------------

class TestMergeTurnPorted(unittest.TestCase):

    def setUp(self):
        self.new = OEISEntry("A999999", "(test entry) squares of odd numbers",
                             tuple((2 * i + 1) ** 2 for i in range(10)),
                             frozenset({"test"}), "(2n+1)^2", 0)

    def test_merge_keeps_and_adds(self):
        merged = iw().merge(IntegerWheel([self.new]))
        self.assertEqual(len(merged), len(iw()) + 1)
        self.assertIn("A999999", merged)
        self.assertEqual(merged.speak([1, 9, 25, 49, 81]), "A999999")
        self.assertEqual(merged.speak([0, 1, 1, 2, 3, 5, 8, 13, 21, 34]), "A000045")
        self.assertEqual(merged.audit_soundness()["unsound"], 0)
        for e in iw().entries():                  # merge_keeps
            self.assertEqual(merged.get(e.oeis_id), e)

    def test_merge_self(self):
        self.assertEqual(set(iw().merge(iw()).ids()), set(iw().ids()))
        self.assertEqual(len(iw().merge(iw())), len(iw()))

    def test_turn_does_not_mutate(self):
        before = len(iw())
        turned = iw().turn([self.new])
        self.assertEqual(len(iw()), before)
        self.assertIn("A999999", turned)


# ---------------------------------------------------------------------------
# The provision contract of Wheels/IntegerWheel.lean, on the real data
# ---------------------------------------------------------------------------

def _claims():
    """Every nonempty prefix of every entry of the absorbed Monster Wheel,
    the empty claim, each prefix with its last term changed, and S1's
    held-out battery."""
    out = [()]
    for e in mw().entries():
        for n in range(1, len(e.terms) + 1):
            out.append(e.terms[:n])
            out.append(e.terms[:n - 1] + (e.terms[n - 1] + 1,))
    out.extend(claim for _label, claim in S.held_out_battery())
    return out


class TestLeanSpeakSemantics(unittest.TestCase):
    """``speak`` behaves as ``Wheels/IntegerWheel.lean`` defines it: silent on
    the empty claim and when nothing starts with the claim, the exact tier
    first, the least identifier of the chosen tier."""

    @classmethod
    def setUpClass(cls):
        cls.claims = _claims()

    def test_python_speak_is_lean_speak(self):
        for wheel in (iw(), mw()):
            entries = wheel.entries()
            mismatches = [c for c in self.claims
                          if wheel.speak(c) != lean_speak(entries, c)]
            self.assertEqual(mismatches, [])

    def test_the_clauses(self):
        w = mw()
        entries = w.entries()
        for c in self.claims:
            spoken = w.speak(c)
            if not c:
                self.assertIsNone(spoken)                          # speak_eq_none
                continue
            matching = [e for e in entries if lean_is_prefix(c, e.terms)]
            if not matching:
                self.assertIsNone(spoken)                          # speak_eq_none
                continue
            self.assertIsNotNone(spoken)                           # speak_isSome
            entry = w.get(spoken)
            self.assertTrue(lean_is_prefix(c, entry.terms))       # speak_sound
            exact = [e for e in entries if tuple(e.terms) == tuple(c)]
            if exact:
                self.assertEqual(tuple(entry.terms), tuple(c))     # speak_exact
                self.assertEqual(spoken, min(e.oeis_id for e in exact))
            else:
                self.assertEqual(spoken, min(e.oeis_id for e in matching))  # speak_least

    def test_provision_sound_and_complete(self):
        for e in iw().entries()[:40]:
            p = e.provision()
            self.assertIsNone(p(()))
            for n in range(1, len(e.terms) + 1):
                self.assertEqual(p(e.terms[:n]), e.oeis_id)        # provision_complete
                self.assertEqual(p(e.terms[:n]), lean_provision(e, e.terms[:n]))
            self.assertIsNone(p(e.terms + (0,)))                   # provision_sound
            bumped = e.terms[:-1] + (e.terms[-1] + 1,)
            self.assertIsNone(p(bumped))

    def test_a_single_order_speaks_its_group_not_the_sorted_list(self):
        # The exact tier first: [7920] is M11's whole stored list and only a
        # prefix of the sorted orders.
        self.assertEqual(mw().speak([7920]), "M11")
        self.assertEqual(lean_speak(mw().entries(), [7920]), "M11")

    def test_locate_is_sound(self):
        for claim in ((1, 2, 3, 5, 8, 13), (3, 5, 7, 9, 11), (5, 9, 2, 6, 5, 3)):
            oid, k = iw().locate(claim)
            self.assertEqual(iw().get(oid).terms[k:k + len(claim)], claim)
            self.assertGreaterEqual(k, 1)
        self.assertIsNone(iw().locate((4, 8, 15, 16, 23, 42)))
        self.assertIsNone(iw().locate(()))


# ---------------------------------------------------------------------------
# The Lean file's eight closed-form entries against the Python data
# ---------------------------------------------------------------------------

class TestLeanAgreement(unittest.TestCase):
    """``Wheels/IntegerWheel.lean`` read back, against the Python entries."""

    @classmethod
    def setUpClass(cls):
        cls.path = C.lean_file(L.INTEGER_WHEEL_LEAN)
        cls.lists = L.integer_wheel_terms()

    def test_the_file_is_in_the_build_tree_and_audited(self):
        from glm_universal import lean_check
        self.assertTrue(self.path.is_file())
        self.assertTrue(lean_check.audited_or_held(L.INTEGER_WHEEL_LEAN))

    def test_the_eight_lists_are_read(self):
        self.assertEqual(sorted(self.lists), sorted(
            ["A000045", "A000032", "A000142", "A000108", "A000040", "A000079",
             "A000290", "A000217"]))

    def test_each_list_is_a_prefix_of_the_python_entry(self):
        for oid, terms in self.lists.items():
            with self.subTest(oid=oid):
                self.assertGreater(len(terms), 0)
                for wheel in (iw(), sw(), mw()):
                    self.assertEqual(wheel.get(oid).terms[:len(terms)], terms)

    def test_each_list_is_its_closed_form(self):
        # The Lean file proves these equal to the closed forms; recomputed
        # here, so a misread list fails rather than agreeing by accident.
        def fib(n):
            a, b = 0, 1
            for _ in range(n):
                a, b = b, a + b
            return a

        def lucas(n):
            a, b = 2, 1
            for _ in range(n):
                a, b = b, a + b
            return a

        def prime(k):
            return k > 1 and all(k % d for d in range(2, math.isqrt(k) + 1))

        forms = {
            "A000045": [fib(n) for n in range(25)],
            "A000032": [lucas(n) for n in range(25)],
            "A000142": [math.factorial(n) for n in range(20)],
            "A000108": [math.comb(2 * n, n) // (n + 1) for n in range(20)],
            "A000040": [k for k in range(100) if prime(k)],
            "A000079": [2 ** n for n in range(25)],
            "A000290": [n * n for n in range(25)],
            "A000217": [n * (n + 1) // 2 for n in range(25)],
        }
        for oid, terms in self.lists.items():
            self.assertEqual(list(terms), forms[oid], oid)

    def test_the_contract_theorems_are_stated(self):
        text = L.lean_text(L.INTEGER_WHEEL_LEAN)
        for name in S.LEAN_THEOREMS[L.INTEGER_WHEEL_LEAN]:
            self.assertRegex(text, rf"(?m)^theorem\s+{name}\b")
        self.assertIn("namespace GLM.IntegerWheel", text)


# ---------------------------------------------------------------------------
# The audit (mark A)
# ---------------------------------------------------------------------------

class TestSuppliedSeed(unittest.TestCase):
    """``glm_universal.wheels.oeis_seed``: the supplied data, as supplied."""

    def test_the_seed(self):
        from glm_universal.wheels.oeis_seed import CURATED_OEIS
        self.assertEqual(len(CURATED_OEIS), 183)
        ids = [row[0] for row in CURATED_OEIS]
        self.assertEqual(len(set(ids)), 183)
        for row in CURATED_OEIS:
            self.assertRegex(row[0], r"^A\d{6}$")
            self.assertTrue(row[2], row[0])
            self.assertTrue(all(type(t) is int for t in row[2]), row[0])

    def test_the_wheels_read_it_unchanged(self):
        from glm_universal.wheels.oeis_seed import CURATED_OEIS
        for row in CURATED_OEIS:
            self.assertEqual(sw().get(row[0]).terms, tuple(row[2]))

    def test_the_port_is_the_supplied_data(self):
        from glm_universal.wheels.oeis_seed import CURATED_OEIS
        supplied = load_supplied("oeis_seed.py")
        if supplied is None:
            self.skipTest("the supplied item is not in this checkout")
        self.assertEqual(supplied_rows(CURATED_OEIS), supplied_rows(supplied.CURATED_OEIS))


class TestAudit(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.audit = R.audit_supplied()

    def test_the_frozen_list_is_the_live_audit(self):
        self.assertEqual(self.audit["admitted_integer"], R.ADMITTED_IDS)
        self.assertEqual(self.audit["admitted_group_theory"], R.ADMITTED_GROUP_THEORY_IDS)

    def test_the_counts_the_study_quotes(self):
        self.assertEqual(self.audit["counts"], {R.VERIFIED: 109, R.DISAGREES: 33,
                                                R.NOT_RECOMPUTED: 45, R.SHORT: 1})
        self.assertEqual(len(supplied_entries()), 183)
        self.assertEqual(len(iw()), 107)
        self.assertEqual(len(R.ADMITTED_IDS), 107)

    def test_the_absorbed_wheel_holds_exactly_the_verified(self):
        self.assertEqual(set(iw().ids()), set(R.ADMITTED_IDS))
        for e in iw().entries():
            self.assertEqual(R.audit_entry(e.oeis_id, e.terms)["verdict"], R.VERIFIED)
            self.assertEqual(e, sw().get(e.oeis_id))   # nothing rewritten

    def test_an_entry_that_is_not_a_run_disagrees(self):
        self.assertEqual(R.audit_entry("A000045", (0, 1, 1, 2, 3, 5, 9))["verdict"],
                         R.DISAGREES)
        self.assertEqual(R.audit_entry("A000045", (1, 1, 2, 3, 5, 8))["verdict"],
                         R.VERIFIED)
        self.assertEqual(R.audit_entry("A999998", (1, 2, 3))["verdict"],
                         R.NOT_RECOMPUTED)


# ---------------------------------------------------------------------------
# The query surface (glm_universal.wheels.sequence_query)
# ---------------------------------------------------------------------------

class TestSequenceQuery(unittest.TestCase):
    """``answer_sequence_query``: 0 answered, 1 nothing answers, 2 not mine."""

    def test_the_examples_of_the_brief(self):
        code, reply = answer_sequence_query("what sequence is 1, 1, 2, 3, 5, 8")
        self.assertEqual(code, ANSWERED)
        self.assertTrue(reply.startswith("A000045"))
        self.assertIn("position 1", reply)
        code, reply = answer_sequence_query("identify the sequence 2 3 5 7 11")
        self.assertEqual((code, reply[:7]), (ANSWERED, "A000040"))
        code, reply = answer_sequence_query("which sporadic group has order 7920")
        self.assertEqual(code, ANSWERED)
        self.assertTrue(reply.startswith("M11"))

    def test_refusals_and_others(self):
        self.assertEqual(answer_sequence_query("what sequence is 4, 8, 15, 16, 23, 42")[0],
                         UNANSWERED)
        self.assertEqual(answer_sequence_query("what sequence is 1, 2")[0], UNANSWERED)
        for text in ("what is the capital of France", "what is 2 + 3",
                     "what sequence of events led to the war",
                     "what sequence of 3 events led to the war",
                     "identify the speaker", "what is the order of operations",
                     "what is the order of the B-tree", "what is the order of CO2 emissions",
                     "what is the order of the monster in the film", ""):
            with self.subTest(text=text):
                self.assertEqual(answer_sequence_query(text), (NOT_MINE, ""))

    def test_reading_the_question(self):
        self.assertEqual(sequence_terms("what sequence is 1, -2, 3"), (1, -2, 3))
        self.assertEqual(parse_order("2^4 * 3^2 * 5 * 11"), 7920)
        self.assertEqual(parse_order("7,920"), 7920)
        self.assertEqual(parse_order("2**4·3**2·5·11"), 7920)
        self.assertIsNone(parse_order("seven"))

    def test_every_answer_is_a_run_of_the_named_entry(self):
        for text in ("what sequence is 1, 1, 2, 3, 5, 8", "what sequence is 3, 5, 7, 9",
                     "what sequence is 1, 4, 9, 16, 25"):
            r = resolve_query(text)
            self.assertEqual(r.code, ANSWERED)
            for oid in r.ids:
                terms = mw().get(oid).terms
                self.assertEqual(terms[r.position:r.position + len(r.claim)], r.claim)

    def test_no_network_and_no_float(self):
        from glm_universal.reasoning.exactness import module_float_sites
        for module in S.NEW_MODULES:
            self.assertEqual(module_float_sites(C.PACKAGE_ROOT / module), {}, module)
        probe = ("import sys; import glm_universal.wheels.sequence_query as q; "
                 "q.answer_sequence_query('what sequence is 1, 2, 4, 8'); "
                 "print(sorted(m for m in sys.modules if m.startswith('urllib')"
                 " or m in ('socket', 'http.client')))")
        out = subprocess.run([sys.executable, "-c", probe], capture_output=True,
                             text=True, env={"PYTHONPATH": str(C.PACKAGE_ROOT.parent)},
                             timeout=120)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertNotIn("urllib.request", out.stdout)
        self.assertNotIn("http.client", out.stdout)


# ---------------------------------------------------------------------------
# The study's measurement (glm_universal.wheels.integer_wheel_study)
# ---------------------------------------------------------------------------

class TestStudyMeasurement(unittest.TestCase):
    """The marks of ``studies/INTEGER_WHEEL_STUDY.md`` that need no command
    line, re-taken; the figures the study quotes are pinned."""

    def test_the_question_set(self):
        self.assertEqual(len(S.SEQUENCE_QUESTIONS), 70)
        self.assertEqual(len(S.ORDER_QUESTIONS), 32)
        self.assertEqual(len(S.S3_QUESTIONS), 102)
        self.assertEqual(len(S.S4_QUESTIONS), 28)
        self.assertEqual(len({q[0] for q in S.S3_QUESTIONS + S.S4_QUESTIONS}), 130)
        self.assertEqual((S.S2_BAR_MAX_RIGHT, S.S3_BAR_MIN_RIGHT), (10, 85))

    def test_classify(self):
        ids = S._ids("A000045")
        self.assertEqual(S.classify(ids, 0, ("A000045",), None), S.RIGHT)
        self.assertEqual(S.classify(ids, 0, ("A000046",), None), S.WRONG)
        self.assertEqual(S.classify(ids, 1, (), None), S.REFUSED)
        self.assertEqual(S.classify(("order", 7), 0, ("X",), 7), S.RIGHT)
        self.assertEqual(S.classify(S.REFUSE, 0, ("X",), None), S.WRONG)
        self.assertEqual(S.classify(S.NOT_A_QUESTION, 2, (), None), S.LEFT)
        self.assertEqual(S.classify_cli(ids, 1, "UNSOLVED nothing"), S.REFUSED)
        self.assertEqual(S.classify_cli(ids, 0, "QUERY A000045\nANSWER Fibonacci"), S.OTHER)
        self.assertEqual(S.classify_cli(ids, 0, "ANSWER A000045"), S.RIGHT)
        self.assertEqual(S.classify_cli(("order", 7920), 0, "ANSWER 7,920"), S.RIGHT)

    def test_s2_puts_the_questions_to_the_command_line_without_the_wheels(self):
        # Since the measurement the command line answers from the wheels (the
        # sequence lookup kind, installed provisionally); S2 still measures
        # the GLM without them.
        text = "what sequence is 1, 1, 2, 3, 5, 8"
        code, out = S.ask_cli(text)
        self.assertEqual(code, 1, out)
        self.assertEqual(S.classify_cli(S._ids("A000045"), code, out), S.REFUSED)
        code, out = S.ask_cli(text, with_wheels=True)
        self.assertEqual(code, 0, out)
        self.assertEqual(S.classify_cli(S._ids("A000045"), code, out), S.RIGHT)
        # The note the register gives: "provisional: ..." while installed
        # provisionally, "absorbed ahead of the build: ..." once absorbed
        # ahead of the owner's build (1 November 2026, Phase 186).
        self.assertTrue("[provisional:" in out or "[absorbed ahead of the build:" in out, out)

    def test_s3_and_s4(self):
        s3 = S.mark_s3()
        self.assertEqual((s3["right"], s3["wrong"], s3["refused"]), (89, 0, 13))
        self.assertTrue(set(S.EXPECTED_REFUSALS) <= set(s3["refused_qids"]))
        self.assertTrue(s3["met"])
        s4 = S.mark_s4()
        self.assertEqual((s4["perturbed_refused"], s4["nonsporadic_refused"],
                          s4["other_left_alone"], s4["wrong"]), (12, 10, 6, 0))
        self.assertTrue(s4["met"])

    def test_the_control_answers_wrongly(self):
        c = S.mark_c()
        self.assertEqual((c["s3_right"], c["s3_wrong"]), (91, 6))
        self.assertGreater(c["held_out_false"], 0)

    def test_s1(self):
        s1 = S.mark_s1()
        self.assertTrue(s1["met"])
        self.assertEqual((s1["prefixes"], s1["surface_questions"], s1["held_out"]),
                         (3652, 3382, 1483))

    def test_r_reports_no_help(self):
        r = S.mark_r()
        self.assertTrue(r["no_help"])
        self.assertEqual(r["absorbed"]["additional"], 0)
        self.assertEqual(r["supplied"]["additional"], 0)
        self.assertEqual(r["absorbed"]["sporadic_orders"], ())
        self.assertEqual(r["surface_false"], 0)

    def test_l_and_a(self):
        self.assertTrue(S.mark_l()["met"])
        self.assertTrue(S.mark_a()["met"])

    def test_t_without_tests_is_not_met(self):
        t = S.mark_t(run_tests=False)
        self.assertFalse(t["met"])
        self.assertTrue(t["registry_unchanged"])
        self.assertTrue(t["provision_wheels"])
        self.assertEqual(t["float_modules"], ())

    def test_the_figure_is_a_sentence_of_integers(self):
        fig = S.deciding_figure(
            {"prefixes": 1, "surface_questions": 2, "held_out": 3, "surface_false": 0,
             "held_out_false": 0, "speak_false": 0},
            {"right": 0, "questions": 102},
            {"right": 89, "wrong": 0, "questions": 102},
            {"perturbed_refused": 12, "nonsporadic_refused": 10,
             "other_left_alone": 6, "questions": 28})
        self.assertIn("89 of 102", fig)
        self.assertIn("0 of 102", fig)
        self.assertIn("28 of 28", fig)
        self.assertIn("in 6 soundness checks", fig)


if __name__ == "__main__":
    unittest.main()
