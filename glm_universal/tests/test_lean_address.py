"""Tests for :mod:`glm_universal.reasoning.lean_address`.

The module gives every declaration of the Lean development a deterministic
Leech address.  These tests pin the four things that make the scheme a claim
rather than a decoration:

* the parser finds declarations and nothing that is not one;
* the feature map depends on the *statement* and not on the name, so renaming
  a declaration cannot move it and rewriting one must;
* the address is a lattice point, is lossless, and its conflation classes come
  from the feature map rather than from the quantiser;
* the digest guard reports a stale address book rather than answering from it.

Nothing here recomputes the whole book -- one nearest-point decode costs about
a tenth of a second and there are hundreds of declarations.  The stored book is
spot-checked by re-deriving a handful of addresses from scratch, which is what
makes it a cache rather than data.
"""

from __future__ import annotations

import json
import re
import unittest
from fractions import Fraction
from pathlib import Path

from glm_universal.reasoning import lean_address as la


class TestParser(unittest.TestCase):

    def test_the_development_is_found(self):
        self.assertIsNotNone(la.lean_root())
        self.assertGreater(len(la.lean_files()), 30)

    def test_declarations_are_found_in_every_file(self):
        files = {d.file for d in la.declarations()}
        self.assertEqual(len(files), len(la.lean_files()))

    def test_names_are_fully_qualified_and_unique(self):
        names = [d.name for d in la.declarations()]
        self.assertEqual(len(names), len(set(names)))
        self.assertTrue(all(n.startswith("GLM") for n in names))

    def test_a_known_theorem_is_parsed_with_its_kind_and_file(self):
        decl = la.declaration("GLM.HigherLattices.BarnesWall.norm_dvd_eight")
        self.assertIsNotNone(decl)
        self.assertEqual(decl.kind, "theorem")
        self.assertEqual(decl.file, "HigherLattices.lean")
        self.assertIn("nrm (mk a b c)", decl.statement)

    def test_the_statement_stops_at_the_first_top_level_assignment(self):
        decl = la.declaration("GLM.HigherLattices.BarnesWall.mk")
        self.assertNotIn("fun i =>", decl.statement)
        self.assertIn("fun i =>", decl.body)

    def test_short_names_resolve_when_unambiguous(self):
        self.assertIsNotNone(la.declaration("eightZ_mem_leech"))

    def test_no_duplicate_names(self):
        self.assertEqual(la.parser_agreement()["duplicates"], ())

    def test_parser_agreement_against_a_supplied_reference(self):
        names = [d.name for d in la.declarations()][:5]
        report = la.parser_agreement(names + ["GLM.NotARealDeclaration"])
        self.assertTrue(report["reference_supplied"])
        self.assertEqual(report["agreed"], 5)
        self.assertEqual(report["missed"], ("GLM.NotARealDeclaration",))


class TestFeatures(unittest.TestCase):

    def setUp(self):
        self.table = la.feature_table()

    def test_every_declaration_has_twenty_four_capped_coordinates(self):
        for name, vector in self.table.items():
            self.assertEqual(len(vector), 24, name)
            self.assertTrue(all(0 <= v <= la.CAP for v in vector), name)

    def test_feature_names_match_the_vector_length(self):
        self.assertEqual(len(la.FEATURE_NAMES), 24)
        self.assertEqual(len(set(la.FEATURE_NAMES)), 24)

    def test_a_universally_quantified_theorem_counts_its_quantifier(self):
        decl = la.declaration("GLM.HigherLattices.Ternary.even_norm_ge_eighteen")
        vector = dict(zip(la.FEATURE_NAMES, la.features_of(decl)))
        self.assertGreaterEqual(vector["order"], 1)
        self.assertEqual(vector["kind"], 1)

    def test_the_name_is_not_a_feature(self):
        """Renaming a declaration must not move it."""
        decl = la.declaration("GLM.Address.readback_unique")
        renamed = la.Declaration(
            name="GLM.Address.some_other_name", kind=decl.kind,
            file=decl.file, line=decl.line, namespace=decl.namespace,
            statement=decl.statement, body=decl.body)
        self.assertEqual(la.features_of(decl), la.features_of(renamed))

    def test_the_statement_is_a_feature(self):
        """Rewriting the statement must move it."""
        decl = la.declaration("GLM.Address.readback_unique")
        altered = la.Declaration(
            name=decl.name, kind=decl.kind, file=decl.file, line=decl.line,
            namespace=decl.namespace,
            statement=decl.statement + " ∀ x, ∃ y, x = y",
            body=decl.body)
        self.assertNotEqual(la.features_of(decl), la.features_of(altered))

    def test_the_proof_is_not_a_feature(self):
        """Two proofs of one statement must address the same point."""
        decl = la.declaration("GLM.Address.readback_unique")
        reproved = la.Declaration(
            name=decl.name, kind=decl.kind, file=decl.file, line=decl.line,
            namespace=decl.namespace, statement=decl.statement,
            body="by\n  simpa using something_else")
        self.assertEqual(la.features_of(decl), la.features_of(reproved))

    def test_citation_graph_is_directed_and_excludes_self(self):
        graph = la.citation_graph()
        for name, targets in graph.items():
            self.assertNotIn(name, targets)

    def test_a_citation_is_found(self):
        graph = la.citation_graph()
        cited = graph["GLM.HigherLattices.BarnesWall.norm_dvd_eight"]
        self.assertIn("GLM.HigherLattices.BarnesWall.sum_binary", cited)


class TestQuantisation(unittest.TestCase):

    def test_the_scale_is_at_least_twice_the_covering_radius(self):
        self.assertGreaterEqual(la.SCALE, 2 * la.COVERING_RADIUS)

    def test_the_scale_is_not_a_multiple_of_eight(self):
        """8 Z^24 lies inside the lattice, so scale 8 would be an identity."""
        self.assertNotEqual(la.SCALE % 8, 0)

    def test_a_computed_address_is_a_lattice_point(self):
        from glm_universal.substrate import leech_construct as lc
        decl = la.declarations()[0]
        point = la.quantise(la.feature_table()[decl.name])
        self.assertIsNotNone(lc.level_of(point))

    def test_read_back_recovers_the_features(self):
        table = la.feature_table()
        for name in list(table)[:3]:
            point = la.quantise(table[name])
            self.assertEqual(la.describe_address(point)["recovered"],
                             table[name], name)

    def test_read_back_handles_negative_coordinates(self):
        reading = la.describe_address([-la.SCALE] * 24)
        self.assertEqual(reading["recovered"], tuple([-1] * 24))
        self.assertEqual(reading["max_residual"], 0)

    def test_squared_distance_is_an_integer_and_symmetric(self):
        a = (1,) * 24
        b = (0,) * 24
        self.assertIsInstance(la.squared_distance(a, b), int)
        self.assertEqual(la.squared_distance(a, b), la.squared_distance(b, a))
        self.assertEqual(la.squared_distance(a, b), 24)

    def test_the_sentence_names_the_kind(self):
        features = [0] * 24
        features[la.FEATURE_NAMES.index("kind")] = 1
        self.assertIn("theorem", la.sentence(features))
        features[la.FEATURE_NAMES.index("kind")] = 2
        self.assertIn("definition", la.sentence(features))


class TestAddressBook(unittest.TestCase):

    def test_the_book_is_present_and_fresh(self):
        state = la.cache_state()
        self.assertTrue(state["present"])
        self.assertEqual(
            state["verdict"], "fresh",
            "the Lean sources changed since the address book was written; run "
            "`python -m glm_universal.tools lean-address --write`")

    def test_a_stale_digest_is_reported_rather_than_used(self):
        book = dict(la.address_book())
        book["tree_digest"] = "0" * 64
        original = la._book_cache
        try:
            la._book_cache = book
            state = la.cache_state()
            self.assertFalse(state["fresh"])
            self.assertEqual(state["verdict"], "stale")
        finally:
            la._book_cache = original

    def test_the_book_covers_every_declaration(self):
        book = la.address_book()
        self.assertEqual(len(book["order"]), len(la.declarations()))
        self.assertEqual(set(book["order"]), {d.name for d in la.declarations()})

    def test_stored_features_match_a_fresh_computation(self):
        book = la.address_book()
        table = la.feature_table()
        for name in book["order"]:
            self.assertEqual(tuple(book["features"][name]), table[name], name)

    def test_stored_addresses_recompute_exactly(self):
        """The book is a cache, so a sample of it is re-derived from scratch."""
        book = la.address_book()
        for name in book["order"][:3]:
            self.assertEqual(tuple(book["addresses"]["feature"][name]),
                             la.quantise(tuple(book["features"][name])), name)

    def test_the_book_holds_no_floats(self):
        text = Path(la.DATA_PATH).read_text(encoding="utf-8")
        for token in json.loads(text)["addresses"]["feature"].values():
            self.assertTrue(all(isinstance(v, int) for v in token))


class TestSchemes(unittest.TestCase):

    def test_three_schemes_are_available_over_the_same_declarations(self):
        sizes = {scheme: len(la.addresses(scheme)) for scheme in la.SCHEMES}
        self.assertEqual(len(set(sizes.values())), 1)

    def test_an_unknown_scheme_is_refused(self):
        with self.assertRaises(ValueError):
            la.addresses("astrology")

    def test_the_shuffle_is_a_permutation_of_the_feature_addresses(self):
        feature = sorted(la.addresses("feature").values())
        shuffled = sorted(la.addresses("shuffled").values())
        self.assertEqual(feature, shuffled)

    def test_the_shuffle_is_deterministic(self):
        self.assertEqual(la.addresses("shuffled"), la.addresses("shuffled"))

    def test_the_shuffle_actually_moves_things(self):
        feature = la.addresses("feature")
        shuffled = la.addresses("shuffled")
        moved = sum(1 for name in feature if feature[name] != shuffled[name])
        self.assertGreater(moved, len(feature) // 2)

    def test_the_seeded_permutation_is_a_permutation(self):
        for n in (1, 2, 5, 40, 805):
            order = la._seeded_permutation(n)
            self.assertEqual(sorted(order), list(range(n)))

    def test_the_hash_control_is_deterministic_and_name_dependent(self):
        first = la.name_hash_vector("GLM.Address.readback_unique")
        self.assertEqual(first, la.name_hash_vector("GLM.Address.readback_unique"))
        self.assertNotEqual(first, la.name_hash_vector("GLM.Address.other"))


class TestMeasurements(unittest.TestCase):

    def test_the_encoding_is_lossless_over_the_whole_corpus(self):
        trip = la.round_trip_report("feature")
        self.assertEqual(trip["exact"], trip["checked"])
        self.assertEqual(trip["coordinate_errors"], 0)
        self.assertEqual(trip["exact_rate"], Fraction(1))

    def test_the_covering_bound_is_respected(self):
        guarantee = la.readback_guarantee()
        self.assertTrue(guarantee["bound_respected"])
        self.assertTrue(guarantee["lossless"])
        self.assertLessEqual(guarantee["worst_observed_residual"],
                             la.COVERING_RADIUS)

    def test_the_decoder_is_not_idle(self):
        """At this scale every point is genuinely quantised."""
        guarantee = la.readback_guarantee()
        self.assertEqual(guarantee["moved_by_the_decoder"],
                         guarantee["declarations"])

    def test_quantisation_adds_no_conflation(self):
        inj = la.injectivity("feature")
        self.assertEqual(inj["distinct_addresses"],
                         inj["distinct_feature_vectors"])
        self.assertTrue(inj["quantisation_adds_no_conflation"])

    def test_the_hash_control_is_injective(self):
        """A digest separates everything -- and means nothing."""
        self.assertTrue(la.injectivity("hash_control")["injective"])

    def test_the_structural_scheme_beats_both_controls(self):
        report = la.separation_report()
        verdict = report["verdict"]
        self.assertTrue(verdict["feature_beats_hash_control"])
        self.assertTrue(verdict["feature_beats_shuffle"])
        self.assertTrue(verdict["feature_beats_chance"])
        self.assertTrue(verdict["linked_beats_chance"])

    def test_the_hash_control_scores_near_chance(self):
        report = la.separation_report()
        control = report["separation"]["hash_control"]["neighbours"] \
            if "separation" in report else report["hash_control"]["neighbours"]
        self.assertLess(abs(control["same_file_rate"]
                            - control["same_file_chance"]),
                        Fraction(1, 20))

    def test_the_lift_over_chance_is_large(self):
        neighbours = la.separation_report()["feature"]["neighbours"]
        self.assertGreater(neighbours["same_file_rate"],
                           5 * neighbours["same_file_chance"])

    def test_rates_are_exact_fractions(self):
        neighbours = la.separation_report()["feature"]["neighbours"]
        for key in ("same_file_rate", "same_file_chance", "linked_rate",
                    "linked_chance"):
            self.assertIsInstance(neighbours[key], Fraction)


class TestSpeaking(unittest.TestCase):

    def test_an_unknown_name_is_refused_rather_than_guessed(self):
        self.assertFalse(la.speak("GLM.NotAThing")["found"])

    def test_speaking_a_known_theorem(self):
        spoken = la.speak("GLM.Address.readback_unique", neighbours=2)
        self.assertTrue(spoken["found"])
        self.assertTrue(spoken["addressed"])
        self.assertTrue(spoken["read_back_exact"])
        self.assertEqual(len(spoken["address"]), 24)
        self.assertEqual(len(spoken["neighbours"]), 2)
        self.assertIn("theorem", spoken["sentence"])

    def test_neighbours_are_ordered_by_distance(self):
        spoken = la.speak("GLM.Address.readback_unique", neighbours=5)
        distances = [n["squared_distance"] for n in spoken["neighbours"]]
        self.assertEqual(distances, sorted(distances))

    def test_the_report_is_complete(self):
        report = la.lean_address_report()
        self.assertTrue(report["available"])
        for key in ("cache", "corpus", "features", "round_trip", "guarantee",
                    "separation", "spoken"):
            self.assertIn(key, report)
        self.assertEqual(report["cache"]["verdict"], "fresh")


class TestEveryCitedTheoremExists(unittest.TestCase):
    """Directive D8: where a Lean file and a Python module disagree, the Lean
    file is the specification -- so a module citing ``GLM.Foo.bar`` must be
    citing something that is actually there.

    The declaration index makes that checkable for the first time: every
    ``GLM....`` name written anywhere in the package is looked up, and a name
    that is neither a declaration nor a namespace prefix of one is a stale
    citation.  Two were found when this test was written, one of them a
    theorem cited under a namespace it does not live in.
    """

    #: ``GLM.py`` is the command line script, not a Lean name.
    IGNORED = {"GLM.py"}

    #: This file deliberately cites names that do not exist, to check that
    #: they are refused, and is therefore excluded from its own audit.
    SELF = "test_lean_address.py"

    CITATION = re.compile(r"\bGLM(?:\.[A-Za-z_][A-Za-z0-9_']*)+")

    @classmethod
    def setUpClass(cls):
        cls.names = {d.name for d in la.declarations()}
        cls.namespaces = set()
        for name in cls.names:
            parts = name.split(".")
            for i in range(1, len(parts)):
                cls.namespaces.add(".".join(parts[:i]))

    def known(self, name):
        return name in self.names or name in self.namespaces

    def test_every_lean_name_cited_in_the_package_resolves(self):
        root = Path(la.__file__).resolve().parent.parent
        stale = {}
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in str(path) or path.name == self.SELF:
                continue
            for cited in self.CITATION.findall(path.read_text(encoding="utf-8")):
                if cited in self.IGNORED or self.known(cited):
                    continue
                stale.setdefault(cited, set()).add(path.name)
        self.assertEqual(
            stale, {},
            "stale Lean citations: " + ", ".join(
                f"{k} in {sorted(v)}" for k, v in sorted(stale.items())))

    def test_the_audit_would_notice_a_stale_citation(self):
        self.assertFalse(self.known("GLM.Address.no_such_theorem"))
        self.assertTrue(self.known("GLM.Address.readback_unique"))

    def test_a_namespace_prefix_counts_as_known(self):
        self.assertTrue(self.known("GLM.Address"))
        self.assertTrue(self.known("GLM.Shell"))

    def test_declarations_carrying_an_attribute_are_parsed(self):
        # ``@[simp] lemma dsBit_zero_eq_zero`` sits at column zero behind its
        # attribute; the reader has to see past it.
        self.assertIn("GLM.Info.dsBit_zero_eq_zero", self.names)


class TestDocumentsQuoteTheCurrentCorpus(unittest.TestCase):
    """The corpus size moves whenever a Lean file is added.

    Every count in the write-up and in the READMEs is then out of date at
    once, and nothing in the text says so.  This holds the four documents
    that state the corpus size to the size the parser actually finds; the
    per-phase record in ``MASTER_PLAN.md`` is left out on purpose, because a
    phase record states what was measured at the time.
    """

    @classmethod
    def setUpClass(cls):
        cls.count = len(la.declarations())
        # overlay/glm_universal/tests -> the repository root.
        cls.repo = Path(__file__).resolve().parents[3]

    def claims(self):
        n = self.count
        return [
            ("STATUS.md", f"the {n} declarations"),
            ("STATUS.md", f"Read back exactly {n}/{n}"),
            ("overlay/README.md", f"for each of the {n}"),
            ("overlay/glm_universal/README.md", f"**{n}/{n}**"),
            ("studies/LEAN_ADDRESS_STUDY.md", f"| declarations checked | {n} |"),
        ]

    def test_the_documents_state_the_corpus_as_it_is_parsed(self):
        for relative, phrase in self.claims():
            with self.subTest(document=relative):
                path = self.repo / relative
                self.assertTrue(path.is_file(), f"{relative} is missing")
                self.assertIn(
                    phrase, path.read_text(encoding="utf-8"),
                    f"{relative} does not state the current corpus size: "
                    f"expected the phrase {phrase!r}")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
