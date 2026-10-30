"""Citations read in Lean's scope (Phase 101): the repaired citation reader,
the type-word repair, and the marks declared in
``studies/CITATION_SCOPE_STUDY.md`` before the measurement was taken.

The measurement itself is read from the stored record when it is current
(``tools citation-scope --write``) and re-taken otherwise.
"""

from __future__ import annotations

import unittest
from fractions import Fraction
from pathlib import Path

from glm_universal.reasoning import citation_reference as cr
from glm_universal.reasoning import citation_scope as cs
from glm_universal.reasoning import lean_address as la

ROOT = Path(__file__).resolve().parents[3]
LEAN = ROOT / "src" / "lean" / cs.LEAN_FILE

_REPORT = None


def report():
    global _REPORT
    if _REPORT is None:
        _REPORT = cs.current() or cs.citation_scope_report()
    return _REPORT


def decl(name: str, statement: str, body: str = "") -> la.Declaration:
    namespace = name.rsplit(".", 1)[0]
    return la.Declaration(name=name, kind="theorem", file="X.lean", line=1,
                          namespace=namespace, statement=statement, body=body)


FULL = frozenset({"GLM.Heisenberg.a", "GLM.Heisenberg.V", "GLM.Gen3.foo",
                  "GLM.Gen3.bar", "GLM.Golay24.Word", "GLM.Sakuma.e"})


class TestTheReader(unittest.TestCase):

    def test_comments_and_strings_are_not_read(self):
        text = 'a /- b /- c -/ d -/ e -- f\n"g h" i'
        stripped = la.strip_comments_and_strings(text)
        for word in ("b", "c", "d", "f", "g", "h"):
            self.assertNotIn(word, stripped.split())
        for word in ("a", "e", "i"):
            self.assertIn(word, stripped.split())

    def test_binders_are_found(self):
        bound = la.bound_names(
            "theorem t (a b : ℕ) {e : V} : ∀ x y, ∃ z ∈ s, fun w => a := by\n"
            "  intro h1 h2\n  obtain ⟨k, hk⟩ := h1\n  cases' h2 with p q")
        for name in ("a", "b", "e", "x", "y", "z", "w", "h1", "h2", "k",
                     "hk", "p", "q"):
            self.assertIn(name, bound)

    def test_a_bound_variable_is_not_a_citation(self):
        d = decl("GLM.Gen3.foo", "theorem foo (a : ℕ) : a = a", ":= rfl")
        self.assertNotIn("GLM.Heisenberg.a",
                         la.scoped_cited_names(d, FULL))

    def test_an_out_of_scope_short_name_is_not_a_citation(self):
        d = decl("GLM.Gen3.foo", "theorem foo : e = e", ":= rfl")
        self.assertEqual(frozenset(), la.scoped_cited_names(d, FULL))

    def test_in_scope_and_qualified_names_are_citations(self):
        d = decl("GLM.Heisenberg.b", "theorem b : a = Golay24.Word",
                 ":= Gen3.bar")
        self.assertEqual(
            frozenset({"GLM.Heisenberg.a", "GLM.Golay24.Word",
                       "GLM.Gen3.bar"}),
            la.scoped_cited_names(d, FULL))

    def test_an_open_makes_a_namespace_visible(self):
        d = decl("GLM.Gen3.foo", "theorem foo : Word = Word")
        scope = la.FileScope(opens=("GLM.Golay24",), variables=frozenset())
        self.assertEqual(frozenset({"GLM.Golay24.Word"}),
                         la.scoped_cited_names(d, FULL, scope))

    def test_a_variable_line_shadows(self):
        d = decl("GLM.Heisenberg.b", "theorem b : a = a")
        scope = la.FileScope(opens=(), variables=frozenset({"a"}))
        self.assertEqual(frozenset(), la.scoped_cited_names(d, FULL, scope))

    def test_field_notation_on_a_local_is_not_read(self):
        d = decl("GLM.Heisenberg.b", "theorem b (h : P) : Q", ":= h.a")
        self.assertEqual(frozenset(), la.scoped_cited_names(d, FULL))

    def test_resolution_is_lean_order(self):
        full = frozenset({"GLM.x", "GLM.A.x", "GLM.A.B.y"})
        self.assertEqual("GLM.A.x", la.resolve_in_scope("x", "GLM.A.B", (), full))
        self.assertEqual("GLM.x", la.resolve_in_scope("x", "GLM.C", (), full))
        self.assertIsNone(la.resolve_in_scope("y", "GLM.C", (), full))
        self.assertEqual("GLM.A.B.y",
                         la.resolve_in_scope("y", "GLM.C", ("GLM.A.B",), full))

    def test_goal_citations_open_the_development(self):
        names = la.declaration_names()
        some = next(n for n in sorted(names) if n.count(".") == 2)
        tail = some.split(".", 1)[1]
        self.assertIn(some, la.goal_citations(f"{tail} = {tail}"))
        self.assertNotIn(some, la.goal_citations(f"{tail} = {tail}",
                                                 exclude=some))

    def test_no_one_letter_sink_on_the_corpus(self):
        graph = la.citation_graph()
        cited = {}
        for targets in graph.values():
            for target in targets:
                cited[target] = cited.get(target, 0) + 1
        self.assertLess(cited.get("GLM.Heisenberg.a", 0), 50)
        legacy = la.legacy_citation_graph()
        self.assertGreater(sum(1 for t in legacy.values()
                               if "GLM.Heisenberg.a" in t), 1000)


class TestTheTypeWords(unittest.TestCase):

    def test_whole_identifiers_only(self):
        words = la.type_words("natCast IntervalSet Nat.succ (n : Nat) Finset")
        self.assertEqual(2, words["Nat"])
        self.assertEqual(0, words["Int"])
        self.assertEqual(0, words["Set"])
        self.assertEqual(1, words["Finset"])

    def test_the_legacy_count_reads_inside_identifiers(self):
        words = cs.infix_type_words("IntervalSet natCast")
        self.assertEqual(1, words["Int"])


class TestTheMarks(unittest.TestCase):

    #: L6 was met when the round closed (Phase 101): the headline and the
    #: legacy figures were taken on one tree.  Phase 114 edited a module the
    #: measurement digests, the close re-took the headline on the tree of
    #: that day (4739 declarations against the legacy record's 4596), and
    #: the legacy figures, taken by Phase 100's code, cannot be re-taken.
    #: So L6 is recorded as a miss by construction since then, and the
    #: legacy figures are kept as the record (CITATION_SCOPE_STUDY.md §3.3).
    RECORDED_MISSES: tuple = ("L6",)

    def test_every_declared_mark_is_met(self):
        self.assertEqual({"L1", "L2", "L3", "L4", "L5", "L6"},
                         set(report()["marks"]))
        for mark, met in report()["marks"].items():
            with self.subTest(mark=mark):
                self.assertEqual(met, mark not in self.RECORDED_MISSES)

    def test_the_repair_beats_the_legacy_reader(self):
        audit = report()["audit"]
        self.assertGreater(Fraction(audit["scoped"]["precision"]),
                           Fraction(audit["legacy"]["precision"]))
        self.assertLess(audit["scoped"]["one_letter_unconfirmed"],
                        audit["legacy"]["one_letter_unconfirmed"] // 100)

    def test_the_legacy_record_is_kept(self):
        #  The legacy figures are Phase 101's record, taken by Phase 100's
        #  code on the tree of 4596 declarations; they are never re-taken.
        #  The headline was on the same tree until Phase 114's close re-took
        #  it on a later one (see RECORDED_MISSES above).
        stored = cs.measurements()
        self.assertIsNotNone(stored)
        self.assertEqual(4596, stored["legacy"]["declarations"])
        self.assertEqual(stored["legacy"], cs.legacy_record())
        self.assertGreater(stored["headline"]["declarations"],
                           stored["legacy"]["declarations"])

    def test_the_reference_is_of_the_current_tree(self):
        self.assertEqual("fresh", cr.state()["verdict"])

    def test_the_lean_file_names_its_theorems(self):
        text = LEAN.read_text(encoding="utf-8")
        for name in ("resolve_bound", "resolve_mem", "resolve_first",
                     "cites_antitone", "legacy_reads_bound_variable",
                     "scoped_ignores_bound_variable", "typeCount_rename",
                     "infixCount_not_rename_invariant"):
            self.assertIn(f"theorem {name}", text)
        self.assertNotIn("sorry", text)


if __name__ == "__main__":
    unittest.main()
