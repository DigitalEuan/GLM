"""Tests for ``glm_universal.semantics`` -- meaning as the encoded thing.

The suite is organised around the claim the package makes, which is not a
claim about coverage but about *what is encoded*:

1. **The meaning space.**  Exactness, the round trip, injectivity, and a
   decoder that notices corruption.  A codec that never refuses anything is
   not checking anything, so the negative controls are here too.
2. **Reference.**  The property that gives the package its point: notations
   that denote the same subject get the *same* carrier, across spelling,
   numeral, Roman numeral, arithmetic, chemical formula and register name.
   And the other half of it -- a term with no determinate referent is refused
   with a reason, rather than given a carrier it has not earned.
3. **Relations.**  Every derived claim is re-derivable from the meanings
   alone, and the expected relations between concrete subjects do hold.
4. **The graph.**  Nodes are meanings, notations collapse onto them, and
   every edge re-verifies.
5. **The audit.**  The measurements over the inherited concept graph are
   internally consistent, and they do show what the package says they show:
   the legacy carrier separates synonyms and carries no relatedness signal.
6. **The documents.**  The graph and the purge plan write out exactly, and
   the inherited state file is read and never written.
7. **The runtime.**  ``meaning of ...``, ``relate ... ...`` and ``report
   semantics`` are wired end to end, including Three Column Thinking
   verification of a generated script in a fresh interpreter.
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from glm_universal.semantics import audit as sau            # noqa: E402
from glm_universal.semantics import export as sex           # noqa: E402
from glm_universal.semantics import graph as sgr            # noqa: E402
from glm_universal.semantics import meaning as sme          # noqa: E402
from glm_universal.semantics import reference as sre        # noqa: E402
from glm_universal.semantics import relations as srl        # noqa: E402
from glm_universal.runtime import parser as PA              # noqa: E402
from glm_universal.runtime import session as SE             # noqa: E402
from glm_universal.runtime import tct_engine as TE          # noqa: E402


def _sample_meanings():
    """A spread over all six kinds, built without touching any notation."""
    out = [sme.Meaning.number(Fraction(0)),
           sme.Meaning.number(Fraction(2)),
           sme.Meaning.number(Fraction(-7, 3)),
           sme.Meaning.dimension([0] * 10),
           sme.Meaning.dimension([2, 1, -2, 0, 0, 0, 0, 0, 0, 0]),
           sme.Meaning.dimension([2, 1, -2, 0, 0, 0, 0, -1, 0, 0]),
           sme.Meaning.quantity([1, 0, -1, 0, 0, 0, 0, 0, 0, 0], 299792458),
           sme.Meaning.quantity([0] * 10, Fraction(1, 3)),
           sme.Meaning.compound([(1, 2), (8, 1)]),
           sme.Meaning.compound([(6, 1), (1, 4)]),
           sme.Meaning.compound([(1, 1), (6, 1), (7, 1), (8, 1), (16, 1)])]
    out.extend(sme.Meaning.element(z) for z in range(1, sme.MAX_Z + 1))
    out.extend(sme.Meaning.op(name) for name in sme.OPERATIONS)
    return out


# ===========================================================================
# 1.  THE MEANING SPACE
# ===========================================================================

class TestMeaningSpace(unittest.TestCase):
    """Exactness, the round trip, injectivity, and refusal."""

    def test_layout_is_twenty_four(self):
        self.assertEqual(len(sme.MEANING_LAYOUT), 24)
        for m in _sample_meanings():
            self.assertEqual(len(sme.encode(m)), 24)

    def test_carrier_is_exact(self):
        for m in _sample_meanings():
            for coordinate in sme.encode(m):
                self.assertIsInstance(coordinate, (int, Fraction))
                self.assertNotIsInstance(coordinate, (bool, float))

    def test_round_trip(self):
        for m in _sample_meanings():
            with self.subTest(meaning=m.describe()):
                self.assertEqual(sme.decode(sme.encode(m)), m)

    def test_carriers_are_injective(self):
        carriers = {}
        for m in _sample_meanings():
            key = tuple(sme.encode(m))
            self.assertNotIn(key, carriers,
                             f"{m.describe()} collides with "
                             f"{carriers.get(key)}")
            carriers[key] = m.describe()

    def test_checksum_catches_perturbation(self):
        carrier = list(sme.encode(sme.Meaning.element(8)))
        carrier[12] = carrier[12] + 1          # oxygen -> fluorine, silently?
        with self.assertRaises(sme.DecodeError):
            sme.decode(carrier)

    def test_wrong_length_is_refused(self):
        with self.assertRaises(sme.DecodeError):
            sme.decode([Fraction(0)] * 23)

    def test_encode_has_no_notation_parameter(self):
        """The claim 'the carrier cannot depend on the spelling', by type."""
        import inspect
        signature = inspect.signature(sme.encode)
        self.assertEqual(list(signature.parameters), ["meaning"])

    def test_over_capacity_formula_is_refused(self):
        """Six distinct elements do not fit five slots, so they are refused."""
        with self.assertRaises(ValueError):
            sme.Meaning.compound([(z, 1) for z in range(1, 7)])

    def test_impossible_formula_is_refused(self):
        with self.assertRaises(ValueError):
            sme.Meaning.compound([(0, 1)])
        with self.assertRaises(ValueError):
            sme.Meaning.compound([(1, 0)])
        with self.assertRaises(ValueError):
            sme.Meaning.element(sme.MAX_Z + 1)

    def test_codec_contract(self):
        for m in (sme.Meaning.element(6), sme.Meaning.number(Fraction(5, 2))):
            obj = sme.meaning_object(m)
            self.assertEqual(obj.domain, "semantics")
            self.assertEqual(sme.MeaningCodec().decode(obj), m)


# ===========================================================================
# 2.  REFERENCE: ONE SUBJECT, ONE CARRIER
# ===========================================================================

#: Groups of notations that denote the same subject, by construction of the
#: subject rather than of the string: a numeral, a word, a Roman numeral and
#: two arithmetic expressions are the same number; a name and a formula are
#: the same species; register synonyms are the same dimension.
SYNONYM_GROUPS = (
    ("2", "two", "4/2", "1+1", "6/3"),
    ("12", "twelve", "XII", "3*4", "144/12"),
    ("water", "H2O", "dihydrogen monoxide"),
    ("methane", "CH4"),
    ("hydrogen", "H"),
    ("add", "addition", "plus", "sum"),
)


class TestReference(unittest.TestCase):
    """Notation invariance, and refusal with a reason."""

    def test_synonyms_share_one_meaning(self):
        for group in SYNONYM_GROUPS:
            meanings = {term: sre.resolve(term) for term in group}
            for term, answer in meanings.items():
                with self.subTest(term=term):
                    self.assertTrue(answer.grounded,
                                    f"{term!r} refused: {answer.reason}")
            first = meanings[group[0]].meaning
            for term in group[1:]:
                with self.subTest(pair=(group[0], term)):
                    self.assertEqual(meanings[term].meaning, first)

    def test_synonyms_share_one_carrier(self):
        for group in SYNONYM_GROUPS:
            carriers = {tuple(sme.encode(sre.meaning_of(term)))
                        for term in group}
            self.assertEqual(len(carriers), 1, f"{group} split into "
                                               f"{len(carriers)} carriers")

    def test_case_and_spacing_do_not_matter(self):
        for a, b in (("Water", "water"), ("  water ", "water"),
                     ("SPEED OF LIGHT", "speed_of_light"),
                     ("speed of light", "speed_of_light")):
            with self.subTest(pair=(a, b)):
                self.assertEqual(sre.resolve(a).meaning,
                                 sre.resolve(b).meaning)

    def test_undeterminate_terms_are_refused(self):
        for term in ("beautiful", "ago", "abb", "justice", "the",
                     "qwertyuiop"):
            answer = sre.resolve(term)
            with self.subTest(term=term):
                self.assertFalse(answer.grounded)
                self.assertTrue(answer.reason.strip(),
                                "a refusal must state its reason")

    def test_resolution_is_deterministic(self):
        for term in ("water", "energy", "two", "beautiful", "Fe", "H2O"):
            with self.subTest(term=term):
                self.assertEqual(sre.resolve(term), sre.resolve(term))

    def test_every_reference_term_resolves_and_round_trips(self):
        terms = sre.reference_terms()
        self.assertGreater(len(terms), 1000)
        for term in terms:
            answer = sre.resolve(term)
            if answer.meaning is None:
                continue                       # ambiguous terms are refused
            self.assertEqual(sme.decode(sme.encode(answer.meaning)),
                             answer.meaning)

    def test_ambiguous_terms_are_refused_not_guessed(self):
        report = sre.ambiguity_report()
        self.assertGreater(report["ambiguous_terms"], 0)
        for entry in list(report["ambiguous"])[:20]:
            with self.subTest(term=entry["term"]):
                self.assertFalse(sre.resolve(str(entry["term"])).grounded)

    def test_a_notation_with_two_readings_is_refused(self):
        """``II`` is the Roman numeral two and the formula for two iodine
        atoms.  Two determinate referents is not one, so it is refused."""
        answer = sre.resolve("II")
        self.assertFalse(answer.grounded)
        self.assertIn("ambiguous", answer.reason)

    def test_known_referents(self):
        self.assertEqual(sre.meaning_of("water"),
                         sme.Meaning.compound([(1, 2), (8, 1)]))
        self.assertEqual(sre.meaning_of("carbon"), sme.Meaning.element(6))
        self.assertEqual(sre.meaning_of("two"), sme.Meaning.number(2))
        self.assertEqual(sre.meaning_of("speed").exponents,
                         sre.meaning_of("velocity").exponents)


# ===========================================================================
# 3.  RELATIONS
# ===========================================================================

class TestRelations(unittest.TestCase):
    """Derived claims, and the arithmetic that re-checks them."""

    def test_expected_relations_hold(self):
        cases = (
            ("water", "hydrogen", "contains_element"),
            ("water", "oxygen", "contains_element"),
            ("hydrogen", "helium", "next_element"),
            ("energy", "torque", "si7_conflates"),
            ("speed", "velocity", "same_meaning"),
            ("speed_of_light", "speed", "same_dimension"),
            ("speed_of_light", "speed", "magnitude_of"),
            ("two", "three", "successor"),
            ("two", "four", "divides"),
        )
        for a, b, relation in cases:
            with self.subTest(pair=(a, b), relation=relation):
                claims = srl.derive(sre.meaning_of(a), sre.meaning_of(b))
                self.assertIn(relation, {c.relation for c in claims})

    def test_every_derived_claim_reverifies(self):
        terms = ("water", "hydrogen", "oxygen", "carbon", "methane", "helium",
                 "energy", "torque", "speed", "frequency", "two", "three",
                 "four", "twelve")
        meanings = [sre.meaning_of(t) for t in terms]
        checked = 0
        for a in meanings:
            for b in meanings:
                for claim in srl.derive(a, b):
                    self.assertTrue(srl.verify(claim),
                                    f"{claim.relation} failed to re-verify")
                    checked += 1
        self.assertGreater(checked, 0)

    def test_ternary_dimension_algebra(self):
        energy = sre.meaning_of("energy")
        force = sre.meaning_of("force")
        length = sre.meaning_of("length")
        claims = srl.derive_ternary(energy, force, length)
        self.assertIn("product_of", {c.relation for c in claims})
        for claim in claims:
            self.assertTrue(srl.verify(claim))

    def test_relations_do_not_hold_between_unrelated_meanings(self):
        """A relation table that says yes to everything says nothing."""
        claims = srl.derive(sre.meaning_of("carbon"),
                            sre.meaning_of("energy"))
        self.assertEqual(claims, ())

    def test_witnesses_are_nonempty(self):
        for claim in srl.derive(sre.meaning_of("water"),
                                sre.meaning_of("oxygen")):
            self.assertTrue(claim.witness.strip())


# ===========================================================================
# 4.  THE GROUNDED GRAPH
# ===========================================================================

class TestGraph(unittest.TestCase):
    """Nodes are meanings; notations collapse onto them; edges re-verify."""

    @classmethod
    def setUpClass(cls):
        cls.graph = sgr.build_graph()
        cls.report = sgr.graph_report(cls.graph)

    def test_nodes_are_meanings_not_names(self):
        self.assertLess(self.report["meanings"], self.report["notations"])
        self.assertEqual(len(set(self.graph.meanings)),
                         len(self.graph.meanings))

    def test_synonyms_are_one_node(self):
        for group in SYNONYM_GROUPS:
            nodes = {self.graph.meaning_of(term) for term in group
                     if self.graph.meaning_of(term) is not None}
            with self.subTest(group=group):
                self.assertLessEqual(len(nodes), 1)

    def test_every_edge_reverifies(self):
        verdict = self.graph.verify()
        self.assertTrue(verdict["all_verified"], verdict)

    def test_edges_exist(self):
        self.assertGreater(self.report["binary_edges"], 0)
        self.assertGreater(self.report["ternary_edges"], 0)

    def test_refused_terms_carry_reasons(self):
        for resolution in self.graph.refused:
            self.assertTrue(resolution.reason.strip())

    def test_paths_are_relation_chains(self):
        water = sre.meaning_of("water")
        helium = sre.meaning_of("helium")
        path = self.graph.path(water, helium)
        if path is not None:
            for source, relation, target in path:
                claims = {c.relation for c in srl.derive(source, target)}
                self.assertIn(relation, claims)

    def test_build_is_deterministic(self):
        again = sgr.build_graph(("water", "H2O", "hydrogen", "oxygen",
                                 "helium", "two", "four"))
        twice = sgr.build_graph(("water", "H2O", "hydrogen", "oxygen",
                                 "helium", "two", "four"))
        self.assertEqual(again.meanings, twice.meanings)
        self.assertEqual([c.as_dict() for c in again.binary],
                         [c.as_dict() for c in twice.binary])


# ===========================================================================
# 5.  THE AUDIT OF THE INHERITED GRAPH
# ===========================================================================

class TestAudit(unittest.TestCase):
    """What the inherited concept graph turns out to contain."""

    @classmethod
    def setUpClass(cls):
        cls.report = sau.audit_report()

    def test_state_file_is_present(self):
        self.assertTrue(self.report["state_present"],
                        "the audit needs the shipped legacy state file")

    def test_concept_counts_are_consistent(self):
        concepts = self.report["concept_grounding"]
        self.assertEqual(concepts["grounded"] + concepts["ungrounded"],
                         concepts["concepts"])
        self.assertLess(concepts["grounded"], concepts["concepts"] // 10)

    def test_edge_classes_partition_the_edges(self):
        edges = self.report["edge_grounding"]
        self.assertEqual(sum(edges["classes"].values()), edges["edges"])

    def test_purge_plan_accounts_for_every_edge(self):
        plan = self.report["purge_plan"]
        self.assertEqual(plan["retained"] + plan["dumped"], plan["edges"])
        for reason in plan["dumped_by_reason"]:
            self.assertIn(reason, plan["reasons"])

    def test_legacy_carrier_carries_no_relatedness_signal(self):
        """Related pairs are not closer than unrelated ones, in the legacy
        carrier.  If they were, the carrier would be measuring the subjects."""
        carriers = self.report["carrier_information"]
        related = Fraction(str(carriers["mean_hamming_related"]))
        unrelated = Fraction(str(carriers["mean_hamming_unrelated"]))
        self.assertGreaterEqual(related, unrelated - Fraction(1, 2))
        self.assertLess(abs(related - 12), Fraction(1))

    def test_legacy_carrier_separates_synonyms(self):
        variants = self.report["notational_variants"]
        self.assertGreater(variants["synonym_pairs"], 0)
        legacy = Fraction(str(variants["mean_legacy_hamming_between_synonyms"]))
        self.assertGreater(legacy, 0)

    def test_replacement_graph_is_fully_verified(self):
        replacement = self.report["replacement"]
        self.assertTrue(replacement["all_edges_reverified"])
        self.assertGreater(replacement["binary_edges"],
                           self.report["purge_plan"]["retained"])


# ===========================================================================
# 6.  THE DOCUMENTS
# ===========================================================================

class TestExport(unittest.TestCase):
    """Writing the replacement out, and leaving the inherited state alone."""

    @classmethod
    def setUpClass(cls):
        cls.graph = sgr.build_graph(("water", "H2O", "hydrogen", "H",
                                     "oxygen", "helium", "two", "four",
                                     "energy", "torque", "beautiful"))

    def test_graph_document_is_json_and_float_free(self):
        document = sex.graph_document(self.graph)
        json.dumps(document)                    # must serialise at all

        def walk(node, path=""):
            if isinstance(node, float):
                self.fail(f"float at {path}")
            if isinstance(node, dict):
                for key, value in node.items():
                    walk(value, f"{path}.{key}")
            elif isinstance(node, (list, tuple)):
                for i, value in enumerate(node):
                    walk(value, f"{path}[{i}]")

        walk(document)
        self.assertEqual(document["counts"]["meanings"],
                         len(self.graph.meanings))

    def test_carrier_strings_round_trip(self):
        for meaning in self.graph.meanings:
            coordinates = [Fraction(s) for s in sex.carrier_strings(meaning)]
            self.assertEqual(sme.decode(coordinates), meaning)

    def test_refused_terms_are_recorded_not_dropped(self):
        document = sex.graph_document(self.graph)
        refused = {entry["term"] for entry in document["refused"]}
        self.assertIn("beautiful", refused)
        for entry in document["refused"]:
            self.assertTrue(str(entry["reason"]).strip())

    def test_write_documents_leaves_the_inherited_state_untouched(self):
        legacy = sex.DEFAULT_RESULTS / "glm_state.json"
        before = (hashlib.sha256(legacy.read_bytes()).hexdigest()
                  if legacy.exists() else None)
        with tempfile.TemporaryDirectory() as tmp:
            paths = sex.write_documents(Path(tmp), graph=self.graph)
            for path in paths.values():
                self.assertTrue(path.exists())
                json.loads(path.read_text(encoding="utf-8"))
        after = (hashlib.sha256(legacy.read_bytes()).hexdigest()
                 if legacy.exists() else None)
        self.assertEqual(before, after)

    def test_purge_document_states_a_reason_for_every_dump(self):
        document = sex.purge_document()
        plan = document["plan"]
        self.assertEqual(plan["retained"] + plan["dumped"], plan["edges"])
        for reason in plan["dumped_by_reason"]:
            self.assertIn(reason, plan["reasons"])


# ===========================================================================
# 7.  THE RUNTIME
# ===========================================================================

class TestRuntimeMeaning(unittest.TestCase):
    """``meaning of ...``, ``relate ... ...`` and ``report semantics``."""

    @classmethod
    def setUpClass(cls):
        cls.session = SE.GeometricSession()

    def test_parser_classifies_meaning_queries(self):
        for text in ("meaning of water", "relate energy torque",
                     "same meaning two 2", "denotation of H2O"):
            with self.subTest(text=text):
                self.assertEqual(PA.parse_query(text).kind, "meaning")

    def test_parser_passes_terms_verbatim(self):
        query = PA.parse_query("meaning of qwertyuiop")
        self.assertEqual(tuple(query.options["terms"]), ("qwertyuiop",))

    def test_meaning_of_water(self):
        solution = self.session.ask("meaning of water")
        self.assertTrue(solution.ok)
        self.assertIn("Z1_2 Z8", solution.answer)
        self.assertEqual(solution.expected["all_round_trips_hold"], "True")

    def test_relate_reports_derived_relations(self):
        solution = self.session.ask("relate energy torque")
        self.assertTrue(solution.ok)
        self.assertIn("si7_conflates", solution.expected["relations"])
        self.assertEqual(solution.expected["all_claims_reverify"], "True")

    def test_relate_synonyms_gives_distance_zero(self):
        solution = self.session.ask("relate two 2")
        self.assertEqual(solution.expected["same_meaning"], "True")

    def test_ungrounded_term_is_refused_with_a_reason(self):
        solution = self.session.ask("meaning of beautiful")
        self.assertEqual(solution.expected["grounded_beautiful"], "False")
        self.assertIn("nothing determinate", solution.answer)

    def test_report_semantics(self):
        solution = self.session.ask("report semantics")
        self.assertTrue(solution.ok)
        self.assertIn("legacy_concepts", solution.expected)

    def test_two_sessions_answer_identically(self):
        other = SE.GeometricSession()
        for text in ("meaning of water", "relate hydrogen helium"):
            with self.subTest(text=text):
                self.assertEqual(self.session.ask(text).expected,
                                 other.ask(text).expected)


class TestRuntimeMeaningSubprocess(unittest.TestCase):
    """Three Column Thinking: column 3 must reproduce column 2."""

    @classmethod
    def setUpClass(cls):
        cls.session = SE.GeometricSession()

    def test_generated_scripts_verify(self):
        for text in ("meaning of water", "relate energy torque"):
            with self.subTest(text=text):
                trace = TE.verify_trace(TE.build_trace(self.session.ask(text)),
                                        timeout=900)
                self.assertTrue(trace.verdict.executed, trace.verdict)
                self.assertTrue(trace.verdict.matches_column2, trace.verdict)


if __name__ == "__main__":
    unittest.main()
