"""Tests for :mod:`glm_universal.reasoning.retrieval`.

Five things are pinned here.

* **The Lean file's promises hold of the running code.**  Every theorem of
  ``RequestProject/GLM/Retrieval.lean`` that is a statement about a ranking is
  checked against the real corpus rather than a toy: the ranking is
  independent of the order the corpus is read in (``ranked_eq_of_perm``),
  widening ``k`` only appends (``topk_prefix``, ``hit_mono``), nothing is
  returned that is not in the corpus (``mem_topk``), an empty radius shortlist
  really does certify absence
  (``filterRadius_eq_nil_certifies_absence``), and the completeness bound
  ``complete_shortlist`` is checked on more than a hundred thousand pairs.

* **The arithmetic is exact.**  Distances are ``int``, overlaps and rates are
  :class:`~fractions.Fraction`, and no float is constructed anywhere in the
  report.

* **The controls are controls.**  The digest scheme, the seeded reshuffle and
  the random ranking all sit at the chance rate, which is computed in closed
  form rather than simulated; a control that beat the address would mean the
  experiment was measuring something other than what it claims.

* **The verdict is the measurement.**  The report's boolean verdict is
  recomputed here from its own tables, so the summary cannot drift away from
  the numbers underneath it -- including the two findings that go against the
  substrate: the text control beats the address, and no address shortlist
  improves on the text control.

* **The query surface behaves.**  ``retrieve`` distinguishes a declaration
  query from a goal query, never returns the query itself, and returns at most
  ``k`` candidates from every scheme.
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.reasoning import lean_address as la
from glm_universal.reasoning import retrieval as rt


# ===========================================================================
# 1.  THE CORPUS AND ITS CACHES
# ===========================================================================

class TestTheIndexIsBuiltFromTheSources(unittest.TestCase):

    def test_the_address_book_is_fresh(self):
        self.assertEqual(la.cache_state()["verdict"], "fresh")

    def test_the_lexical_book_is_fresh(self):
        state = rt.lexical_cache_state()
        self.assertEqual(state["verdict"], "fresh")
        self.assertEqual(state["stored_digest"], la.tree_digest())

    def test_every_declaration_has_both_addresses(self):
        names = rt.corpus()
        self.assertGreater(len(names), 2000)
        self.assertEqual(set(names), set(la.addresses("feature")))
        self.assertEqual(set(names), set(rt.lexical_addresses()))

    def test_the_lexical_address_is_the_quantised_lexical_vector(self):
        # Recompute a handful from the sources rather than trusting the file.
        table = rt.lexical_table()
        stored = rt.lexical_addresses()
        for name in rt.corpus()[::400]:
            with self.subTest(name=name):
                self.assertEqual(stored[name], la.quantise(table[name]))

    def test_a_lexical_coordinate_counts_a_letter(self):
        vector = rt.lexical_vector("theorem alpha (beta : Nat) : alpha = beta")
        self.assertEqual(vector[0], 1)                 # alpha
        self.assertEqual(vector[1], 1)                 # beta
        self.assertEqual(vector[ord("n") - ord("a")], 1)   # nat
        self.assertEqual(vector[ord("t") - ord("a")], 1)   # theorem
        self.assertEqual(sum(vector), 4)


# ===========================================================================
# 2.  RELATIVES AND CHANCE
# ===========================================================================

class TestWhatCountsAsAHit(unittest.TestCase):

    def test_relatives_are_symmetric_and_exclude_the_query(self):
        for name in rt.corpus()[::500]:
            with self.subTest(name=name):
                self.assertNotIn(name, rt.relatives(name))
                for other in list(rt.relatives(name))[:5]:
                    self.assertIn(name, rt.relatives(other))

    def test_a_relative_is_a_file_mate_or_a_citation(self):
        files = rt.file_of()
        graph = la.citation_graph()
        for name in rt.corpus()[::700]:
            for other in list(rt.relatives(name))[:20]:
                with self.subTest(name=name, other=other):
                    self.assertTrue(
                        files[other] == files[name]
                        or other in graph.get(name, ())
                        or name in graph.get(other, ()))

    def test_chance_is_the_closed_form(self):
        # 1 - C(m-r, k)/C(m, k) on a case small enough to write out.
        self.assertEqual(rt.chance_hit_rate(1, 5, 1), Fraction(1, 4))
        self.assertEqual(rt.chance_hit_rate(2, 5, 2),
                         1 - Fraction(2 * 1, 4 * 3))
        self.assertEqual(rt.chance_hit_rate(0, 100, 5), Fraction(0))
        self.assertEqual(rt.chance_hit_rate(99, 100, 1), Fraction(1))

    def test_chance_is_monotone_in_k(self):
        previous = Fraction(-1)
        for k in rt.K_LADDER:
            value = rt.chance_hit_rate(40, 2802, k)
            self.assertGreater(value, previous)
            previous = value


# ===========================================================================
# 3.  THE LEAN PROMISES, CHECKED ON THE REAL CORPUS
# ===========================================================================

class TestTheLeanPromisesHold(unittest.TestCase):
    """Each test names the theorem of ``GLM/Retrieval.lean`` it exercises."""

    def test_ranked_eq_of_perm_the_reading_order_does_not_matter(self):
        table = la.addresses("feature")
        names = rt.corpus()
        query = names[7]
        forward = rt.rank_by_point(table, table[query], 12, query)
        backward = rt.rank_by_point(table, table[query], 12, query,
                                    candidates=tuple(reversed(names)))
        self.assertEqual([c.name for c in forward], [c.name for c in backward])

    def test_ties_are_broken_by_name_not_by_arrival(self):
        table = la.addresses("feature")
        query = rt.corpus()[11]
        found = rt.rank_by_point(table, table[query], 40, query)
        for first, second in zip(found, found[1:]):
            with self.subTest(pair=(first.name, second.name)):
                self.assertLessEqual(first.score, second.score)
                if first.score == second.score:
                    self.assertLess(first.name, second.name)

    def test_topk_prefix_and_hit_mono(self):
        table = la.addresses("feature")
        for query in rt.corpus()[::600]:
            small = rt.rank_by_point(table, table[query], 3, query)
            large = rt.rank_by_point(table, table[query], 9, query)
            with self.subTest(query=query):
                self.assertEqual([c.name for c in small],
                                 [c.name for c in large[:3]])

    def test_mem_topk_nothing_is_invented(self):
        names = set(rt.corpus())
        for scheme in rt.SCHEMES:
            with self.subTest(scheme=scheme):
                out = rt.retrieve("GLM.Address.address_congr", k=6,
                                  scheme=scheme)
                self.assertLessEqual(len(out["names"]), 6)
                for name in out["names"]:
                    self.assertIn(name, names)
                self.assertNotIn("GLM.Address.address_congr", out["names"])

    def test_complete_shortlist_the_bound_holds_on_the_corpus(self):
        report = rt.shortlist_report()
        self.assertGreater(report["pairs_checked"], 100_000)
        self.assertEqual(report["violations"], 0)
        self.assertTrue(report["bound_holds"])
        self.assertGreaterEqual(report["worst_slack"], 0)

    def test_the_shortlist_contains_every_feature_close_declaration(self):
        features = rt._point_table("features")
        addresses = rt._point_table("address")
        radius = 2
        bound = (la.SCALE * radius + 2 * rt.RHO) ** 2
        for query in rt.corpus()[::900]:
            close = [other for other in rt.corpus()
                     if other != query
                     and la.squared_distance(features[query],
                                             features[other]) <= radius ** 2]
            for other in close:
                with self.subTest(query=query, other=other):
                    self.assertLessEqual(
                        la.squared_distance(addresses[query],
                                            addresses[other]), bound)

    def test_an_empty_shortlist_certifies_absence(self):
        # `filterRadius_eq_nil_certifies_absence`: with a radius of -1 nothing
        # can be inside, and the certificate is that every entry is outside.
        table = la.addresses("feature")
        query = rt.corpus()[3]
        inside = [name for name in rt.corpus()
                  if la.squared_distance(table[query], table[name]) <= -1]
        self.assertEqual(inside, [])
        for name in rt.corpus()[::500]:
            self.assertGreater(la.squared_distance(table[query], table[name]),
                               -1)


# ===========================================================================
# 4.  EXACTNESS
# ===========================================================================

class TestNoFloatIsConstructed(unittest.TestCase):

    def test_the_scores_are_exact(self):
        for scheme in rt.SCHEMES:
            out = rt.retrieve("GLM.Address.address_congr", k=3, scheme=scheme)
            for candidate in out["candidates"]:
                with self.subTest(scheme=scheme, name=candidate["name"]):
                    self.assertNotIn(".", candidate["score"].replace("/", ""))

    def test_the_rates_are_fractions(self):
        report = rt.declaration_query_report()
        for scheme, rows in report["schemes"].items():
            for k, row in rows.items():
                with self.subTest(scheme=scheme, k=k):
                    self.assertIsInstance(row["hit_rate"], Fraction)
                    self.assertIsInstance(row["precision"], Fraction)
                    self.assertIsInstance(row["mrr"], Fraction)
        for k, value in report["chance"].items():
            self.assertIsInstance(value, Fraction)

    def test_the_distances_are_integers(self):
        table = la.addresses("feature")
        query = rt.corpus()[0]
        for candidate in rt.rank_by_point(table, table[query], 5, query):
            self.assertEqual(candidate.score.denominator, 1)


# ===========================================================================
# 5.  THE EXPERIMENT AND ITS CONTROLS
# ===========================================================================

class TestTheDeclarationQueryExperiment(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.report = rt.declaration_query_report()

    def test_the_sample_is_the_stated_stride(self):
        names = rt.corpus()
        stride = max(1, len(names) // rt.SAMPLE)
        expected = tuple(n for n in names[::stride] if rt.relatives(n))
        self.assertEqual(rt.query_sample(rt.SAMPLE), expected)
        self.assertEqual(self.report["queries"], len(expected))

    def test_hit_rates_are_monotone_in_k(self):
        for scheme, rows in self.report["schemes"].items():
            previous = Fraction(-1)
            for k in rt.K_LADDER:
                with self.subTest(scheme=scheme, k=k):
                    self.assertGreaterEqual(rows[k]["hit_rate"], previous)
                    previous = rows[k]["hit_rate"]

    def test_the_address_beats_every_control(self):
        k = rt.K_DEFAULT
        rows = self.report["schemes"]
        address = rows["address"][k]["hit_rate"]
        for control in ("digest", "shuffled", "random", "name"):
            with self.subTest(control=control):
                self.assertGreater(address, rows[control][k]["hit_rate"])
        self.assertGreater(address, self.report["chance"][k])

    def test_the_controls_sit_near_chance(self):
        k = rt.K_DEFAULT
        rows = self.report["schemes"]
        chance = self.report["chance"][k]
        for control in ("digest", "shuffled", "random"):
            with self.subTest(control=control):
                self.assertLess(abs(rows[control][k]["hit_rate"] - chance),
                                Fraction(1, 10))

    def test_the_text_control_beats_the_address(self):
        # The finding that goes against the substrate, pinned so that it
        # cannot quietly stop being reported.
        k = rt.K_DEFAULT
        rows = self.report["schemes"]
        self.assertGreater(rows["text"][k]["hit_rate"],
                           rows["address"][k]["hit_rate"])

    def test_the_lattice_neither_helps_nor_hurts_much(self):
        # `address` against `features`: the same information, quantised or
        # not.  The gap either way is small; a large one would mean the
        # quantiser was doing something the study does not describe.
        k = rt.K_DEFAULT
        rows = self.report["schemes"]
        gap = abs(rows["address"][k]["hit_rate"] - rows["features"][k]["hit_rate"])
        self.assertLess(gap, Fraction(1, 10))

    def test_the_lexical_address_is_the_better_address(self):
        k = rt.K_DEFAULT
        rows = self.report["schemes"]
        self.assertGreater(rows["lexical"][k]["hit_rate"],
                           rows["address"][k]["hit_rate"])
        self.assertLess(rows["lexical"][k]["hit_rate"],
                        rows["text"][k]["hit_rate"])


class TestTheGoalQueryExperiment(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.report = rt.goal_query_report()

    def test_a_goal_never_reproduces_the_stored_features(self):
        # Two coordinates are unknowable from a bare statement, so the goal
        # address is never the declaration's own address.  The cost of that is
        # what the table measures.
        self.assertEqual(self.report["features_reproduced"], 0)

    def test_the_goal_address_still_beats_its_controls(self):
        k = rt.K_DEFAULT
        rows = self.report["schemes"]
        self.assertGreater(rows["address"][k]["hit_rate"],
                           rows["digest"][k]["hit_rate"])
        self.assertGreater(rows["address"][k]["hit_rate"],
                           rows["random"][k]["hit_rate"])

    def test_the_goal_address_is_worse_than_the_declaration_address(self):
        k = rt.K_DEFAULT
        declaration = rt.declaration_query_report()["schemes"]["address"][k]
        self.assertLess(self.report["schemes"]["address"][k]["hit_rate"],
                        declaration["hit_rate"])


class TestTheHybrid(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.report = rt.hybrid_report()

    def test_no_shortlist_beats_the_text_control(self):
        self.assertFalse(self.report["any_shortlist_beats_text"])
        for row in self.report["rows"]:
            with self.subTest(shortlist=row["shortlist"]):
                self.assertLess(row["hit_rate"],
                                self.report["text_alone"]["hit_rate"])

    def test_a_larger_shortlist_recovers_more(self):
        previous = Fraction(-1)
        for row in self.report["rows"]:
            with self.subTest(shortlist=row["shortlist"]):
                self.assertGreaterEqual(row["hit_rate"], previous)
                previous = row["hit_rate"]


# ===========================================================================
# 6.  THE VERDICT IS THE MEASUREMENT
# ===========================================================================

class TestTheVerdict(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.report = rt.retrieval_report()

    def test_the_verdict_is_recomputed_from_the_tables(self):
        k = self.report["k"]
        rows = self.report["declaration_queries"]["schemes"]
        chance = self.report["declaration_queries"]["chance"][k]
        verdict = self.report["verdict"]
        address = rows["address"][k]["hit_rate"]
        self.assertEqual(verdict["address_beats_chance"], address > chance)
        self.assertEqual(verdict["address_beats_text"],
                         address > rows["text"][k]["hit_rate"])
        self.assertEqual(verdict["text_beats_address"],
                         rows["text"][k]["hit_rate"] > address)
        self.assertEqual(verdict["lexical_beats_structural"],
                         rows["lexical"][k]["hit_rate"] > address)

    def test_the_two_negative_findings_are_reported(self):
        verdict = self.report["verdict"]
        self.assertFalse(verdict["address_beats_text"])
        self.assertTrue(verdict["text_beats_address"])
        self.assertFalse(verdict["hybrid_beats_text"])

    def test_the_positive_findings_are_reported(self):
        verdict = self.report["verdict"]
        for key in ("address_beats_chance", "address_beats_digest",
                    "address_beats_shuffled", "address_beats_random",
                    "address_beats_name", "guarantee_holds"):
            with self.subTest(key=key):
                self.assertTrue(verdict[key])

    def test_the_address_is_many_times_chance(self):
        self.assertGreater(self.report["times_chance"], 5)

    def test_the_caches_are_fresh(self):
        self.assertTrue(self.report["cache"]["fresh"])
        self.assertTrue(self.report["lexical_cache"]["fresh"])


# ===========================================================================
# 7.  THE QUERY SURFACE
# ===========================================================================

class TestRetrieve(unittest.TestCase):

    def test_a_declaration_query_is_recognised(self):
        out = rt.retrieve("GLM.Address.address_congr", k=3)
        self.assertEqual(out["mode"], "declaration")
        self.assertEqual(out["point"],
                         la.addresses("feature")["GLM.Address.address_congr"])

    def test_a_goal_query_is_addressed_live(self):
        out = rt.retrieve("(n : Nat) : n + 0 = n", k=3)
        self.assertEqual(out["mode"], "goal")
        self.assertEqual(out["point"],
                         rt.goal_address("(n : Nat) : n + 0 = n"))

    def test_the_declaration_head_is_stripped_from_a_goal(self):
        stripped = rt.strip_declaration_head(
            "theorem Sample.name (n : Nat) : n = n")
        self.assertNotIn("Sample", stripped)
        self.assertIn("n = n", stripped)

    def test_every_scheme_answers(self):
        for scheme in rt.SCHEMES:
            with self.subTest(scheme=scheme):
                out = rt.retrieve("(n : Nat) : n + 0 = n", k=4, scheme=scheme)
                self.assertEqual(len(out["names"]), 4)
                self.assertEqual(len(set(out["names"])), 4)

    def test_an_unknown_scheme_is_refused(self):
        with self.assertRaises(ValueError):
            rt.rank("astrology", text="x", k=1)

    def test_the_text_search_finds_the_siblings_of_a_declaration(self):
        # The qualitative half of the finding: on a declaration whose file
        # mates share its vocabulary, the text control returns them and the
        # address does not.
        out = rt.retrieve("GLM.Address.address_congr", k=4, scheme="text")
        self.assertTrue(any(name.startswith("GLM.Address.")
                            for name in out["names"]))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
