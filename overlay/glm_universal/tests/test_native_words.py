"""Native words (Phase 71): word overlap computed on Golay words of the tokens,
against the marks declared in ``studies/NATIVE_WORDS_STUDY.md`` before the
module existed.

The census-sized figures are read from the stored measurements when they are
current (``tools native-words --write``), and re-taken otherwise.
"""

from __future__ import annotations

import unittest
from fractions import Fraction
from pathlib import Path

from glm_universal.reasoning import lean_address as la
from glm_universal.reasoning import native_words as nw
from glm_universal.reasoning import retrieval as rt
from glm_universal.runtime import toolbox
from glm_universal.substrate import golay_decode as gd

ROOT = Path(__file__).resolve().parents[3]

_REPORT = None


def report():
    global _REPORT
    if _REPORT is None:
        _REPORT = nw.current() or nw.native_words_report()
    return _REPORT


def hits(entry, k):
    table = entry["hits"]
    return table.get(k, table.get(str(k)))


class TestTheObjects(unittest.TestCase):

    def test_a_letter_word_reads_the_letter_buckets(self):
        self.assertEqual(nw.letter_word("le"), nw.letter_word("el"))
        self.assertEqual((1 << 11) | (1 << 4), nw.letter_word("le"))
        # y and z fold onto a and b, as in the lexical book.
        self.assertEqual(nw.letter_word("a"), nw.letter_word("y"))
        self.assertEqual(nw.letter_word("b"), nw.letter_word("z"))
        self.assertEqual(0, nw.letter_word("_0'"))

    def test_parts_split_at_underscores_dots_primes_and_digits(self):
        self.assertEqual(("succ", "le", "iff"), nw.token_parts("succ_le_iff"))
        self.assertEqual(("nat", "add"), nw.token_parts("Nat.add'"))
        self.assertEqual(("x", "y"), nw.token_parts("x2y"))

    def test_a_class_is_every_nearest_codeword(self):
        for word in (nw.letter_word("lattice"), nw.letter_word("golay"), 0):
            decoded = gd.decode_complete(word)
            cls = nw.golay_class(word)
            self.assertEqual(set(decoded.candidates), set(cls))
            self.assertIn(len(cls), (1, 6))

    def test_the_name_book_is_injective_and_keeps_new_tokens_apart(self):
        book = nw.NameBook(["le", "el", "golay"])
        self.assertNotEqual(book.name("le"), book.name("el"))
        self.assertEqual(book.name("el")[0], book.name("le")[0])
        first, second = book.name("lee"), book.name("eel")
        self.assertNotEqual(first, second)
        self.assertTrue(book.injective())

    def test_jaccard_is_exact_and_zero_on_empty_sets(self):
        self.assertEqual(Fraction(1, 3), nw.jaccard(frozenset("ab"),
                                                    frozenset("bc")))
        self.assertEqual(Fraction(0), nw.jaccard(frozenset(), frozenset()))


class TestTheRankings(unittest.TestCase):

    def test_the_text_ranking_here_is_the_shipped_one(self):
        decls = {d.name: d for d in la.declarations()}
        for name in rt.query_sample(rt.SAMPLE)[:8]:
            text = rt.strip_declaration_head(decls[name].statement)
            with self.subTest(query=name):
                shipped = [c.name for c in rt.rank_by_text(text, 10, name)]
                here = [c.name for c in nw.rank_lean(text, 10, "text", name)]
                self.assertEqual(shipped, here)

    def test_the_native_ranking_carries_the_token_overlap_first(self):
        decls = {d.name: d for d in la.declarations()}
        for name in rt.query_sample(rt.SAMPLE)[:8]:
            text = rt.strip_declaration_head(decls[name].statement)
            with self.subTest(query=name):
                a = [c.score for c in nw.rank_lean(text, 10, "text", name)]
                b = [c.score for c in nw.rank_lean(text, 10, "words_native",
                                                   name)]
                self.assertEqual(a, b)

    def test_retrieval_accepts_the_word_schemes(self):
        for scheme in rt.WORD_SCHEMES:
            with self.subTest(scheme=scheme):
                got = rt.retrieve("GLM.Address.readback_unique", k=3,
                                  scheme=scheme)
                self.assertEqual("declaration", got["mode"])
                self.assertEqual(3, len(got["names"]))
                self.assertNotIn("GLM.Address.readback_unique", got["names"])

    def test_the_live_document_ranking_is_the_native_one(self):
        from glm_universal.corpus import address as ad
        answer = ad.retrieve("what does the archive rule do?", k=5)
        self.assertEqual("words_native", answer["ranking_scheme"])
        self.assertLessEqual(len(answer["ranked"]), 5)


class TestTheMarks(unittest.TestCase):

    def test_every_mark_is_measured(self):
        self.assertEqual({"W1", "W2", "W3", "W4", "W5", "W6"},
                         set(report()["marks"]))

    def test_w1_the_names_are_exact(self):
        r = report()
        self.assertTrue(r["marks"]["W1"])
        self.assertTrue(r["lean"]["injective"])
        self.assertTrue(r["documents"]["injective"])

    def test_w2_and_w3_the_native_ranking_at_least_matches_the_standard(self):
        r = report()
        self.assertTrue(r["marks"]["W2"])
        self.assertTrue(r["marks"]["W3"])
        for label in ("declarations", "goals"):
            schemes = r["lean"][label]["schemes"]
            for k in rt.K_LADDER:
                self.assertGreaterEqual(hits(schemes["words_native"], k),
                                        hits(schemes["text"], k))

    def test_w5_and_the_leech_tie_break_marks_are_measured(self):
        # W4 and W6 are not pinned: both compare rankings that differ only
        # inside ties of the standard's overlap, by one or a few queries, and
        # they flip with the corpus -- at Phase 71's close W4 was met and W6
        # missed; after Phase 72's Lean file moved the stride sample, W4 is
        # missed by one query at k = 5 and W6 met (NATIVE_WORDS_STUDY.md §3.4).
        r = report()
        self.assertTrue(r["marks"]["W5"])
        self.assertIsInstance(r["marks"]["W4"], bool)
        self.assertIsInstance(r["marks"]["W6"], bool)

    def test_the_wiring_follows_the_marks(self):
        # W2 and W3 met: the live document ranking is words_native (declared).
        r = report()
        self.assertTrue(r["marks"]["W2"] and r["marks"]["W3"])
        self.assertIn("words_native", rt.WORD_SCHEMES)


class TestTheToolAndTheLeanFile(unittest.TestCase):

    def test_the_tool_reads_tokens_as_golay_words(self):
        got = toolbox.run_tool("tool native words succ_le_iff")
        self.assertTrue(got.ok, got.text)
        self.assertIn("succ", got.text)

    def test_the_lean_file_states_what_the_module_relies_on(self):
        text = (ROOT / nw.LEAN_FILE).read_text(encoding="utf-8")
        for name in ("jaccard_image_of_injOn", "jaccard_names",
                     "index_separates", "take_map_overlap_eq",
                     "shared_class_near", "letterWord_congr"):
            self.assertIn(f"theorem {name}", text)
        self.assertNotIn("sorry", text)
