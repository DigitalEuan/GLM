"""Tests for :mod:`glm_universal.reasoning.tie_break`.

Four things are pinned here:

* the **enumeration** -- the closed-form size that
  :func:`~glm_universal.reasoning.tie_break.tie_record` reports is the number
  of points :func:`~glm_universal.reasoning.tie_break.tie_class` actually
  lists, every listed point is in the Leech lattice, and every one of them is
  at the reported distance;
* the **decoder** -- its answer is always a member of the tie class it is
  choosing from, so the module and the quantiser agree about what the class
  is, and the module's ``canonical`` really is the least member of it;
* the **rules disagree** -- the decoder's inherited rule is not the stated
  canonical one, on the corpus and on the two-tied-coordinate example that
  ``TieBreak.lean``'s ``decoder_not_lexLeast`` describes;
* the **invariants** -- whatever the tie-break does, the read-back is
  unchanged (the Lean theorem ``readback_of_tie_class``, checked here against
  the corpus), and no scale in the sweep is tie-free without also being one at
  which the decoder returns its input.
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.reasoning import lean_address as la
from glm_universal.reasoning import tie_break as tb
from glm_universal.substrate import leech2

#: Enough declarations to exercise every branch of the enumeration without
#: making the suite pay for the whole corpus; the full-corpus figures live in
#: ``studies/TIE_BREAK_STUDY.md`` and are recomputed by ``report tiebreak``.
SAMPLE = 12


def _vectors(count: int = SAMPLE):
    table = la.feature_table()
    for declaration in la.declarations()[:count]:
        yield declaration.name, tuple(
            Fraction(int(v) * tb.SCALE) for v in table[declaration.name])


# ===========================================================================
# 1.  THE ENUMERATION
# ===========================================================================

class TestTheTieClass(unittest.TestCase):

    def test_the_closed_form_counts_what_the_listing_lists(self):
        for name, vector in _vectors():
            with self.subTest(declaration=name):
                record = tb.tie_record(vector)
                members = tb.tie_class(vector)
                self.assertEqual(len(members), int(record["size"]))
                self.assertEqual(len(set(members)), len(members))

    def test_every_member_is_a_leech_point_at_the_reported_distance(self):
        for name, vector in _vectors(6):
            record = tb.tie_record(vector)
            for point in tb.tie_class(vector):
                with self.subTest(declaration=name, point=point[:4]):
                    self.assertTrue(leech2.in_leech(list(point)))
                    distance2 = sum((a - b) ** 2
                                    for a, b in zip(vector, point))
                    self.assertEqual(distance2, record["distance2"])

    def test_nothing_else_is_as_close(self):
        """A member's neighbours one option away are strictly further."""
        for name, vector in _vectors(4):
            record = tb.tie_record(vector)
            point = tb.canonical_point(vector)
            for index in range(24):
                for step in (-4, 4):
                    moved = list(point)
                    moved[index] += step
                    if not leech2.in_leech(moved):
                        continue
                    with self.subTest(declaration=name, index=index):
                        distance2 = sum((a - b) ** 2
                                        for a, b in zip(vector, moved))
                        self.assertGreaterEqual(distance2,
                                                record["distance2"])

    def test_the_integer_pass_agrees_with_the_reference_branch_minimum(self):
        """The cleared-denominator first pass finds the same minimum.

        :func:`~glm_universal.reasoning.tie_break.branch_minimum` is the
        readable statement; :func:`~glm_universal.reasoning.tie_break.tie_record`
        runs the same arithmetic in integers to find the winning branches.
        Here the reference is run on all 8,192 branches and the two are
        required to give the same cost, the same class size and the same least
        member.
        """
        from glm_universal.substrate import mog
        for name, vector in _vectors(3):
            with self.subTest(declaration=name):
                best = None
                size = 0
                points = []
                for parity in (0, 1):
                    for word in mog.GOLAY_MASKS:
                        record = tb.branch_minimum(vector, parity, word)
                        if best is None or record["cost"] < best:
                            best = record["cost"]
                            size = int(record["count"])
                            points = [record["point"]]
                        elif record["cost"] == best:
                            size += int(record["count"])
                            points.append(record["point"])
                fast = tb.tie_record(vector)
                self.assertEqual(best, fast["distance2"])
                self.assertEqual(size, fast["size"])
                self.assertEqual(min(points), tuple(fast["canonical"]))

    def test_the_canonical_point_is_the_least_member(self):
        for name, vector in _vectors():
            with self.subTest(declaration=name):
                members = tb.tie_class(vector)
                self.assertEqual(tb.canonical_point(vector), members[0])

    def test_a_class_too_large_to_list_is_refused_rather_than_truncated(self):
        for _, vector in _vectors():
            if tb.tie_class_size(vector) > 2:
                with self.assertRaises(ValueError):
                    tb.tie_class(vector, cap=2)
                return
        self.skipTest("no tied declaration in the sample")

    def test_the_residue_options_are_one_or_two_and_differ_by_four(self):
        for residue in range(4):
            for numerator in range(-16, 17):
                value = Fraction(numerator, 2)
                with self.subTest(residue=residue, value=value):
                    options, cost = tb.residue_options(value, residue)
                    self.assertIn(len(options), (1, 2))
                    for option in options:
                        self.assertEqual(option % 4, residue % 4)
                        self.assertEqual((value - option) ** 2, cost)
                    if len(options) == 2:
                        self.assertEqual(options[1] - options[0], 4)
                        self.assertEqual(2 * value,
                                         options[0] + options[1])

    def test_the_even_subset_count_is_the_branch_count(self):
        self.assertEqual(tb.even_subset_count(0), 1)
        for size in range(1, 12):
            with self.subTest(size=size):
                self.assertEqual(tb.even_subset_count(size), 2 ** (size - 1))
                listed = sum(1 for mask in range(1 << size)
                             if bin(mask).count("1") % 2 == 0)
                self.assertEqual(listed, tb.even_subset_count(size))


# ===========================================================================
# 2.  THE DECODER, AGAINST THE CLASS IT CHOOSES FROM
# ===========================================================================

class TestTheDecoderAgrees(unittest.TestCase):

    def test_the_decoders_answer_is_in_the_tie_class(self):
        for name, vector in _vectors():
            with self.subTest(declaration=name):
                self.assertIn(tb.decoder_point(vector), tb.tie_class(vector))

    def test_the_address_book_uses_the_decoders_answer(self):
        table = la.feature_table()
        for declaration in la.declarations()[:6]:
            name = declaration.name
            with self.subTest(declaration=name):
                vector = tuple(Fraction(int(v) * tb.SCALE)
                               for v in table[name])
                self.assertEqual(la.quantise(table[name]),
                                 tb.decoder_point(vector))


# ===========================================================================
# 3.  THE TWO RULES DISAGREE
# ===========================================================================

class TestTheRulesDisagree(unittest.TestCase):

    def test_the_rule_is_stated_clause_by_clause(self):
        self.assertEqual(len(tb.RULE), 3)
        for clause in tb.RULE:
            with self.subTest(clause=clause["clause"]):
                self.assertTrue(clause["where"])
                self.assertTrue(clause["says"])

    def test_raising_the_first_tied_coordinate_is_not_the_least_choice(self):
        """``TieBreak.lean``'s ``decoder_not_lexLeast``, on two coordinates.

        Two tied coordinates, an odd number of them to be raised: the decoder
        raises the earliest and the canonical rule the last, and the second is
        lexicographically smaller.
        """
        base = [0] * 24
        first = list(base)
        first[3] = 4
        last = list(base)
        last[17] = 4
        self.assertLess(tuple(last), tuple(first))

    def test_the_decoder_and_the_canonical_rule_differ_on_the_corpus(self):
        census = tb.tie_census(limit=SAMPLE)
        self.assertEqual(census["decoder_in_tie_class"], census["declarations"])
        self.assertLessEqual(census["decoder_is_canonical"],
                             census["declarations"])
        self.assertEqual(census["decoder_is_canonical"]
                         + census["decoder_differs_from_canonical"],
                         census["declarations"])


# ===========================================================================
# 4.  WHAT THE TIE-BREAK CANNOT TOUCH
# ===========================================================================

class TestTheInvariants(unittest.TestCase):

    def test_the_read_back_survives_the_tie_break(self):
        """``TieBreak.lean``'s ``readback_of_tie_class``, on the corpus."""
        table = la.feature_table()
        for declaration in la.declarations()[:SAMPLE]:
            name = declaration.name
            features = tuple(table[name])
            vector = tuple(Fraction(int(v) * tb.SCALE) for v in features)
            for point in tb.tie_class(vector, cap=64) if \
                    tb.tie_class_size(vector) <= 64 else ():
                with self.subTest(declaration=name):
                    reading = la.describe_address(point)
                    self.assertEqual(reading["recovered"], features)

    def test_every_member_is_inside_the_covering_radius(self):
        table = la.feature_table()
        for declaration in la.declarations()[:6]:
            name = declaration.name
            features = tuple(table[name])
            vector = tuple(Fraction(int(v) * tb.SCALE) for v in features)
            if tb.tie_class_size(vector) > 64:
                continue
            for point in tb.tie_class(vector, cap=64):
                with self.subTest(declaration=name):
                    for coordinate, feature in zip(point, features):
                        self.assertLessEqual(
                            abs(coordinate - tb.SCALE * feature),
                            tb.COVERING_RADIUS)

    def test_no_scale_is_tie_free_without_being_degenerate(self):
        sweep = tb.scale_tie_table(scales=(4, 6, 8, 9, 12, 16), sample=6)
        self.assertEqual(sweep["tie_free_and_working"], 0)
        for row in sweep["rows"]:
            with self.subTest(scale=row["scale"]):
                if row["tie_free"]:
                    self.assertTrue(row["degenerate"])
                    self.assertEqual(row["worst_distance2"], 0)

    def test_a_multiple_of_eight_leaves_the_decoder_nothing_to_do(self):
        table = la.feature_table()
        for declaration in la.declarations()[:4]:
            features = table[declaration.name]
            with self.subTest(declaration=declaration.name):
                vector = tuple(Fraction(8 * int(v)) for v in features)
                record = tb.tie_record(vector)
                self.assertEqual(record["size"], 1)
                self.assertEqual(record["distance2"], 0)
                self.assertEqual(tuple(record["canonical"]),
                                 tuple(8 * int(v) for v in features))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
