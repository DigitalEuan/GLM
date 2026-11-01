"""Tests for the counted corpus (Phase 154, ``studies/CORPUS_KNOWLEDGE_STUDY.md``):
the reader's rules (:mod:`glm_universal.knowledge.reader`), the readings
(:mod:`~glm_universal.knowledge.answer`), the ``corpus`` query kind and its
brute-force recheck (:mod:`~glm_universal.knowledge.ask`) and the study's
compute helpers (:mod:`~glm_universal.knowledge.study`).

Fast and synthetic: a corpus of a few dozen invented Markdown documents is
read with :func:`glm_universal.knowledge.reader.read_bytes` and counted with
:func:`glm_universal.knowledge.model.build`, so the real corpus is never
loaded, no measurement is re-taken and nothing is written.  Where
:func:`~glm_universal.knowledge.ask.recheck` loads the corpus itself,
``model.load`` is replaced for the test by the synthetic corpus.

*Created 31 October 2026 (repository check).*

*Reconstructed 31 October 2026 (repository check): the original
tests/test_corpus_knowledge.py (named by MASTER_PLAN.md Phase 154 and
studies/CORPUS_KNOWLEDGE_STUDY.md §6) was lost in the October 2026
reorganisation; rebuilt from studies/CORPUS_KNOWLEDGE_STUDY.md (§§1, 3, 3a,
5, 7), studies/CORPUS_DEFINITIONS_STUDY.md (§§2.1, 2.3) and the
reconstructed modules.*
"""
from __future__ import annotations

import re
import unittest
from fractions import Fraction

from glm_universal import constants
from glm_universal.knowledge import answer as ans
from glm_universal.knowledge import ask as kask
from glm_universal.knowledge import model as mdl
from glm_universal.knowledge import reader as rd
from glm_universal.knowledge import study as cks


# ---------------------------------------------------------------------------
#  A synthetic corpus
# ---------------------------------------------------------------------------

NUMBERS = tuple("one two three four five six seven eight nine ten eleven twelve".split())
TREES = tuple("oak pine elm ash birch maple cedar larch rowan alder hazel willow".split())


def _md(path: str, paragraphs) -> rd.Document:
    doc = rd.read_bytes(path, "\n\n".join(paragraphs).encode("utf-8"))
    assert doc is not None, path
    return doc


def _documents():
    docs = []
    for tree in TREES:
        lines = [f"There are {n} gears in the {tree} box." for n in NUMBERS]
        lines.append(f"A digest addresses integrity never meaning in the {tree} archive.")
        lines.append(f"The {tree} ledger lists every gear by number.")
        docs.append(_md(f"notes/trees/{tree}.md", lines))
    docs.append(_md("notes/glossary.md", [
        "# Glossary",
        "The widget frame is a rigid steel box that holds the gears.",
        "Sprocket wheel: a toothed steel wheel that drives the chain.",
        "Sprocket wheel: notes/sprockets.md",
        "Every sprocket wheel turns slowly.",
        "Flywheel, a heavy wheel that stores energy.",
        "The gear ratio is a number.",
        "Blue tie red.",
        "Blue tie green.",
    ]))
    docs.append(_md("notes/gearing.md", [
        "Each gear ratio counts the teeth of the driven and the driving gear.",
        "A high gear ratio puts more teeth on the driven gear than on the driving gear.",
    ]))
    docs.append(_md("archive/old/glossary.md", [
        "The widget frame is a rigid steel box that holds the gears.",
        "A widget frame is steel.",
        "The gear ratio is the teeth of the driven gear over the teeth of the driving gear.",
    ]))
    return tuple(docs)


DOCS = _documents()
KNOWLEDGE = mdl.build(DOCS, digest="synthetic-corpus-knowledge")


class _SyntheticLoad:
    """``model.load`` replaced by the synthetic corpus for one test."""

    def __enter__(self):
        self._saved = mdl.load
        mdl.load = lambda rebuild=False: KNOWLEDGE
        return KNOWLEDGE

    def __exit__(self, *exc):
        mdl.load = self._saved
        return False


# ---------------------------------------------------------------------------
#  The Lean file (studies/CORPUS_KNOWLEDGE_STUDY.md §2)
# ---------------------------------------------------------------------------

class TestLeanFile(unittest.TestCase):

    def test_theorems_and_no_sorry(self):
        path = constants.lean_file("CorpusKnowledge.lean")
        if not path.is_file():
            self.skipTest(f"{path.name} is not in the tree")
        text = path.read_text(encoding="utf-8")
        for name in ("train_append", "train_perm", "predict_eq_none_of_tie",
                     "sqcos_nonneg", "sqcos_le_one", "sqcos_eq_one_iff"):
            self.assertRegex(text, rf"\btheorem {name}\b", name)
        self.assertIsNone(re.search(r"\bsorry\b", text))


# ---------------------------------------------------------------------------
#  reader.py
# ---------------------------------------------------------------------------

class TestReader(unittest.TestCase):

    def test_tokens_are_words(self):
        # words only: digits kept, an inner apostrophe kept, punctuation never a token
        self.assertEqual(rd._tokenise("The corpus's 21.5% rule, x_y; don't-stop."),
                         ("the", "corpus's", "21", "5", "rule", "x_y", "don't", "stop"))
        self.assertEqual(rd._tokenise("-- : | ! ?"), ())

    def test_sentence_ends_need_space(self):
        self.assertEqual(
            rd._split_sentences("See glm_universal.knowledge for 21.5% of it. Next one! "
                                "Is it? Last part"),
            ["See glm_universal.knowledge for 21.5% of it.", "Next one!", "Is it?",
             "Last part"])
        self.assertEqual(rd._split_sentences('He said "stop." Then (we left.) Done'),
                         ['He said "stop."', "Then (we left.)", "Done"])

    def test_python_docstrings_and_comments(self):
        source = (
            '"""The module docstring says the widget turns. It has two sentences."""\n'
            'X = "a plain string literal that is not any docstring at all"\n'
            '# A comment line is prose too.\n'
            'class Gear:\n'
            '    """The class docstring names the gear."""\n'
            '    def turn(self):\n'
            '        """The method docstring is read too."""\n'
            '        return "another literal string with many words in it"\n'
            'async def spin():\n'
            '    """An async docstring is read as well."""\n')
        doc = rd.read_bytes("pkg/mod.py", source.encode("utf-8"))
        texts = [s.text for s in doc.sentences]
        for wanted in ("The module docstring says the widget turns.",
                       "It has two sentences.", "The class docstring names the gear.",
                       "The method docstring is read too.",
                       "An async docstring is read as well.",
                       "A comment line is prose too."):
            self.assertIn(wanted, texts)
        self.assertFalse(any("literal" in t for t in texts))

    def test_json_prose_rule(self):
        self.assertTrue(rd._is_prose("this sentence has enough words to count"))
        self.assertFalse(rd._is_prose("too short here"))           # fewer than five words
        self.assertFalse(rd._is_prose("1 2 3 4 5 6 seven eight"))  # more numbers than words
        doc = rd.read_bytes("data/x.json", (
            b'{"a": "this sentence has enough words to count as prose",'
            b' "b": "1 2 3 4 5 6 seven", "c": "too short",'
            b' "d": ["the list item also holds plenty of words here"], "e": 12}'))
        self.assertEqual([s.text for s in doc.sentences],
                         ["this sentence has enough words to count as prose",
                          "the list item also holds plenty of words here"])

    def test_table_row_is_one_sentence(self):
        doc = rd.read_bytes("notes/t.md", (
            b"Intro paragraph is here.\n"
            b"| term | meaning | note |\n|---|---|---|\n"
            b"| gear | a toothed wheel | common |\n"
            b"After the table comes prose. And a second sentence!\n"))
        paragraphs = [[s.text for s in p.sentences] for p in doc.paragraphs]
        self.assertEqual(paragraphs, [
            ["Intro paragraph is here."],
            ["| term | meaning | note |", "| gear | a toothed wheel | common |"],
            ["After the table comes prose.", "And a second sentence!"]])

    def test_address_and_heading(self):
        doc = DOCS[len(TREES)]
        self.assertEqual(doc.sentences[0].text, "Glossary")      # a heading is a sentence
        self.assertEqual(doc.sentences[1].address, "notes/glossary.md#p1.s0")
        self.assertEqual(rd.top_folder("archive/old/glossary.md"), "archive")


# ---------------------------------------------------------------------------
#  answer.py: helpers
# ---------------------------------------------------------------------------

class TestHelpers(unittest.TestCase):

    def test_runs(self):
        toks = ("a", "b", "a", "b", "c")
        self.assertEqual(ans.find_run(toks, ("a", "b")), 0)
        self.assertEqual(ans.find_run(toks, ("a", "b"), 1), 2)
        self.assertEqual(ans.runs(toks, ("a", "b")), [0, 2])
        self.assertEqual(ans.find_run(toks, ()), -1)
        self.assertEqual(ans.find_run(toks, ("c", "d")), -1)

    def test_fold_and_content(self):
        self.assertEqual(ans.fold("gears"), "gear")
        self.assertEqual(ans.fold("bus"), "bus")    # three letters: kept
        self.assertEqual(ans.content_set(("the", "gears", "of", "a", "box"), ("box",)),
                         frozenset({"gear"}))

    def test_sqcos(self):
        a, b = frozenset("xyz"), frozenset("yzw")
        self.assertEqual(ans.sqcos(a, b), Fraction(4, 9))
        self.assertEqual(ans.sqcos(a, a), 1)
        self.assertEqual(ans.sqcos(a, frozenset()), 0)
        self.assertEqual(ans.sqcos(a, b), ans.sqcos(b, a))
        self.assertIsInstance(ans.sqcos(a, b), Fraction)

    def test_grade_of(self):
        self.assertEqual(ans.grade_of(2, 2), "strong")
        self.assertEqual(ans.grade_of(3, 5), "weak")
        self.assertEqual(ans.grade_of(0, 1), "weak")

    def test_source_rank(self):
        def sentence(path, tier0=False):
            return rd.Sentence(tokens=("x",), address=f"{path}#p0.s0", tier0=tier0,
                               folder="", text="x", document=path)
        self.assertEqual(ans.source_of(sentence("STATUS.md", tier0=True)), (0, "tier-0"))
        self.assertEqual(ans.source_of(sentence("studies/A.md"))[1], "state document")
        self.assertEqual(ans.source_of(sentence("glm_lean/A.lean"))[1], "Lean doc comment")
        self.assertEqual(ans.source_of(sentence("src/a.py"))[1], "docstring")
        self.assertEqual(ans.source_of(sentence("source_material/x.md"))[1],
                         "archive or supplied")
        self.assertEqual(ans.source_of(sentence("data/x.json"))[1], "data file")


# ---------------------------------------------------------------------------
#  answer.py: define and its patterns
# ---------------------------------------------------------------------------

def _sentence(text: str) -> rd.Sentence:
    return rd.Sentence(tokens=rd._tokenise(text), address="t.md#p0.s0", tier0=False,
                       folder="", text=text, document="t.md")


class TestPatterns(unittest.TestCase):

    def test_declared_patterns(self):
        run = ("widget", "frame")
        self.assertEqual(ans.match_pattern(_sentence("Widget frame: a box."), run),
                         ("gloss::", 0))
        self.assertEqual(ans.match_pattern(_sentence("Widget frame — a box."), run),
                         ("gloss:—", 0))
        self.assertEqual(ans.match_pattern(_sentence("Widget frame is a box."), run),
                         ("copula:is", 1))
        self.assertEqual(ans.match_pattern(_sentence("The widget frame refers to a box."),
                                           run), ("copula:refers to", 2))
        self.assertEqual(ans.match_pattern(_sentence("Widget frame, the box of gears."),
                                           run), ("gloss:,", 3))
        self.assertEqual(ans.match_pattern(_sentence("3. Widget frame is a box."), run),
                         ("copula:is", 1))   # a leading list number is passed over

    def test_not_a_definition(self):
        run = ("widget", "frame")
        for text in ("Every widget frame is a box.",          # the term does not open it
                     "Widget frame: notes/frames.md",          # the label rule: a path
                     "Widget frame: frames.py",                # the label rule: a file name
                     "Widget frame:",                          # nothing after the colon
                     "Widget frame, which holds gears.",       # a comma only before the/a/an
                     "| Widget frame: a box | b | c |",        # a table row
                     "Widget frames are boxes."):              # not the term's run
            self.assertIsNone(ans.match_pattern(_sentence(text), run), text)

    def test_define_context_ranking(self):
        got = ans.define("widget frame", KNOWLEDGE)
        self.assertTrue(got["ok"])
        self.assertEqual(got["address"], "notes/glossary.md#p1.s0")
        self.assertEqual(got["pattern"], "copula:is")
        self.assertEqual(got["source"], "state document")
        self.assertEqual(got["mentions"], 3)
        self.assertEqual(got["documents"], 2)
        # the archive copy of the same sentence is kept at its best-ranked copy
        self.assertEqual(got["candidates"], ["notes/glossary.md#p1.s0",
                                             "archive/old/glossary.md#p1.s0"])
        self.assertEqual(got["witness"][0], got["address"])

    def test_context_ranking_against_pattern_ranking(self):
        by_context = ans.define("gear ratio", KNOWLEDGE)
        by_pattern = ans.define("gear ratio", KNOWLEDGE, ranking="pattern")
        self.assertEqual(by_pattern["address"], "notes/glossary.md#p6.s0")
        self.assertEqual(by_context["address"], "archive/old/glossary.md#p2.s0")
        self.assertGreater(by_context["support"], by_pattern["support"])
        self.assertEqual(by_context["strength"], "strong")
        self.assertEqual(sorted(r["address"] for r in by_context["answers"]),
                         sorted(r["address"] for r in by_pattern["answers"]))

    def test_label_is_passed_over(self):
        got = ans.define("sprocket wheel", KNOWLEDGE)
        self.assertEqual(got["address"], "notes/glossary.md#p2.s0")
        self.assertEqual(got["pattern"], "gloss::")
        self.assertEqual(len(got["answers"]), 1)

    def test_refusals(self):
        unmentioned = ans.define("zyxwv", KNOWLEDGE)
        self.assertFalse(unmentioned["ok"])
        self.assertIn("no sentence of the corpus mentions", unmentioned["refusal"])
        undefined = ans.define("gears", KNOWLEDGE)
        self.assertFalse(undefined["ok"])
        self.assertIn("no sentence defines it", undefined["refusal"])
        self.assertEqual(undefined["documents"], 14)
        self.assertFalse(ans.define("  !! ", KNOWLEDGE)["ok"])


# ---------------------------------------------------------------------------
#  answer.py: predict, continue, company, spread, context
# ---------------------------------------------------------------------------

class TestReadings(unittest.TestCase):

    def test_predict_is_none_at_a_tie(self):
        tie = ans.predict("blue tie", KNOWLEDGE)
        self.assertFalse(tie["ok"])
        self.assertEqual(tie["tie"], ["green", "red"])
        unique = ans.predict("a digest", KNOWLEDGE)
        self.assertTrue(unique["ok"])
        self.assertEqual((unique["word"], unique["count"], unique["total"]),
                         ("addresses", 12, 12))
        self.assertFalse(ans.predict("zyxwv qqq", KNOWLEDGE)["ok"])

    def test_continue_stops_at_a_tie(self):
        got = ans.continue_text("a digest addresses", KNOWLEDGE)
        self.assertTrue(got["ok"])
        self.assertEqual(got["text"], "integrity never meaning in the")
        self.assertEqual(got["stop"], "tie")
        self.assertEqual([(s["count"], s["total"]) for s in got["steps"]], [(12, 12)] * 5)
        self.assertTrue(all(w == "notes/trees/oak.md#p12.s0" for w in got["witness"]))
        refused = ans.continue_text("blue tie", KNOWLEDGE)
        self.assertFalse(refused["ok"])
        self.assertIn("a tie between green, red", refused["refusal"])

    def test_continue_limit(self):
        got = ans.continue_text("a digest addresses", KNOWLEDGE, max_tokens=2)
        self.assertEqual((got["text"], got["stop"]), ("integrity never", "limit"))

    def test_similar_and_related(self):
        got = ans.similar("seven", KNOWLEDGE)
        self.assertTrue(got["ok"])
        # the other eleven number words fill the same slot; the first ten by
        # squared cosine, then count, then spelling
        self.assertEqual(len(got["neighbours"]), ans.NEIGHBOURS)
        self.assertTrue(set(got["neighbours"]) <= set(NUMBERS) - {"seven"})
        self.assertTrue(all(isinstance(s, Fraction) for s in got["scores"]))
        rel = ans.related("gears", KNOWLEDGE)
        self.assertTrue(rel["ok"])
        self.assertEqual(rel["neighbours"][0], "box")
        self.assertFalse(ans.similar("widget frame", KNOWLEDGE)["ok"])   # one word only
        self.assertFalse(ans.similar("zyxwv", KNOWLEDGE)["ok"])

    def test_spread(self):
        got = ans.spread("widget frame", KNOWLEDGE)
        self.assertEqual((got["occurrences"], got["sentences"], got["paragraphs"],
                          got["documents"]), (3, 3, 3, 2))
        self.assertEqual(got["folders"], ["archive", "notes"])
        self.assertEqual(got["by_source"], {"state document": 1, "archive or supplied": 2})

    def test_context(self):
        got = ans.context("gears", KNOWLEDGE)
        self.assertEqual(got["words"][0], "box")
        self.assertEqual(got["mentions"], 146)
        doc = ans.context("seven", KNOWLEDGE, "document")
        self.assertEqual(doc["mentions"], 12)
        self.assertIn("ledger", doc["words"])
        self.assertFalse(ans.context("gears", KNOWLEDGE, "chapter")["ok"])


# ---------------------------------------------------------------------------
#  ask.py: the grammar, the answers and the brute-force recheck
# ---------------------------------------------------------------------------

class TestAsk(unittest.TestCase):

    def test_grammar(self):
        cases = {
            "corpus define golay code": ("define", "golay code", "sentence"),
            "What is a syndrome?": ("define", "syndrome", "sentence"),
            "corpus context of gears at document scale": ("context", "gears", "document"),
            "corpus words like seven": ("similar", "seven", "sentence"),
            "related to gears": ("related", "gears", "sentence"),
            "corpus continue a digest addresses": ("continue", "a digest addresses",
                                                   "sentence"),
            "corpus spread of golay": ("spread", "golay", "sentence"),
            "corpus predict blue tie": ("predict", "blue tie", "sentence"),
            "corpus address of seven": ("address", "seven", "sentence"),
        }
        for request, (reading, subject, scale) in cases.items():
            self.assertEqual(kask.parse(request),
                             {"reading": reading, "subject": subject, "scale": scale},
                             request)
        self.assertIsNone(kask.parse("corpus hello"))
        self.assertIsNone(kask.parse("corpus"))

    def test_answers_carry_expected(self):
        for request in ("corpus define widget frame", "corpus continue a digest addresses",
                        "corpus address of seven", "corpus words like seven",
                        "corpus related to gears", "corpus spread of widget frame",
                        "corpus context of gears", "corpus predict a digest"):
            got = kask.ask(request, KNOWLEDGE)
            self.assertTrue(got["ok"], request)
            self.assertTrue(got["expected"], request)
            self.assertTrue(all(isinstance(k, str) and isinstance(v, str)
                                for k, v in got["expected"].items()), request)
            self.assertEqual(len(got["answer"].splitlines()), 1, request)
            self.assertTrue(got["witness"], request)

    def test_define_answer_shape(self):
        got = kask.ask("corpus define widget frame", KNOWLEDGE)
        self.assertTrue(got["answer"].startswith("The corpus says: The widget frame is"))
        self.assertIn("[notes/glossary.md#p1.s0]", got["answer"])
        self.assertEqual(got["expected"]["head"], "notes/glossary.md#p1.s0")
        self.assertEqual(got["quality"]["grade"], "strong")

    def test_address_answer(self):
        got = kask.ask("corpus address of seven", KNOWLEDGE)
        self.assertIn("sits at the Leech point", got["answer"])
        self.assertIn("read back exactly: True", got["answer"])
        self.assertEqual(got["expected"]["readback"], "True")
        self.assertEqual(len(got["expected"]["coordinates"].split(",")), 24)
        self.assertEqual(len(got["expected"]["address"].split(",")), 24)

    def test_refusals(self):
        for request, words in (("corpus define zyxwv", "mentions"),
                               ("corpus address of widget frame", "one word"),
                               ("corpus continue blue tie", "tie"),
                               ("corpus hello", "grammar")):
            got = kask.ask(request, KNOWLEDGE)
            self.assertFalse(got["ok"], request)
            self.assertIn(words, got["refusal"], request)
            self.assertEqual(got["expected"], {}, request)

    def test_answer_request_raises(self):
        with _SyntheticLoad():
            self.assertTrue(kask.answer_request("corpus define widget frame")["ok"])
            with self.assertRaises(kask.CorpusRefusal):
                kask.answer_request("corpus define zyxwv")

    def test_recheck_equals_expected(self):
        requests = ("corpus define widget frame", "corpus define sprocket wheel",
                    "corpus define gear ratio",
                    "corpus continue a digest addresses", "corpus address of seven",
                    "corpus words like seven", "corpus related to gears",
                    "corpus spread of widget frame", "corpus context of gears",
                    "corpus context of seven at document scale",
                    "corpus context of widget frame at paragraph scale",
                    "corpus predict a digest")
        with _SyntheticLoad():
            for request in requests:
                got = kask.ask(request)
                self.assertTrue(got["ok"], request)
                self.assertEqual(kask.recheck(request), got["expected"], request)

    def test_recheck_refusals(self):
        with _SyntheticLoad():
            self.assertEqual(kask.recheck("corpus define zyxwv")["ok"], "False")
            self.assertEqual(kask.recheck("corpus address of widget frame")["ok"], "False")
            self.assertEqual(kask.recheck("corpus hello")["ok"], "False")


# ---------------------------------------------------------------------------
#  study.py: the Phase 154 compute helpers and the honest report
# ---------------------------------------------------------------------------

class TestStudy(unittest.TestCase):

    def test_number_words(self):
        self.assertEqual(cks.NUMBER_WORDS, NUMBERS)

    def test_heldout_split(self):
        train, held = cks.heldout_split(DOCS)
        ordered = sorted(d.path for d in DOCS)
        self.assertEqual([d.path for d in held], ordered[4::5])
        self.assertEqual(len(train) + len(held), len(DOCS))

    def test_distinct_and_novel(self):
        doc = _md("x/y.md", ["Same words here.", "Same words here.", "Other words."])
        self.assertEqual(cks.distinct_sentences([doc]),
                         [("same", "words", "here"), ("other", "words")])
        twin = _md("x/z.md", ["Same words here.", "New words."])
        novel, count = cks.novel_sentences([doc], [twin])
        self.assertEqual((novel, count), ([("new", "words")], 2))

    def test_prediction_stats(self):
        model = mdl.train(DOCS[:3])
        sentence = rd._tokenise("A digest addresses integrity never meaning in the oak archive.")
        stats = cks.prediction_stats(model, [sentence])
        self.assertEqual(stats["positions"], len(sentence) + 1)
        self.assertLessEqual(stats["guarded_right"], stats["guarded_answered"])
        self.assertLessEqual(stats["majority_answered"], stats["guarded_answered"])
        # after "the" the three training trees tie, so "oak" is not guarded
        self.assertGreater(stats["right"], 0)

    def test_additivity(self):
        got = cks.additivity(list(DOCS))
        self.assertTrue(got["sum_of_halves_equal"])
        self.assertTrue(got["reverse_order_equal"])

    def test_plural_pairs_and_backwards(self):
        self.assertEqual(cks.backwards("golay"), "yalog")
        pairs = cks.plural_pairs(KNOWLEDGE)
        self.assertTrue(all(p == w + "s" for w, p in pairs))

    def test_define_rate(self):
        got = cks.define_rate(KNOWLEDGE, ["widget frame", "gears"])
        self.assertEqual((got["terms"], got["answered"], got["nonsense_refused"]), (2, 1, 2))

    def test_report_is_honest(self):
        report = cks.corpus_knowledge_report()
        state = cks.state()
        if report.get("available"):
            self.assertTrue(state["fresh"])
        else:
            self.assertIn(state["verdict"], ("absent", "stale"))
            self.assertIn(state["verdict"], report["reason"])
            self.assertIn("--write", report["reason"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
