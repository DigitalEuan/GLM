"""Tests for ``tools/glm_study_yaml.py``.  Run from the project root:

    python3 -m unittest tools/test_glm_study_yaml.py

Self-contained: every Markdown and YAML sample is synthetic.  The PyYAML cross-checks
run when PyYAML is importable and are skipped otherwise.
"""

import itertools
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import glm_study_yaml as g  # noqa: E402

try:
    import yaml  # type: ignore
except ImportError:          # pragma: no cover - PyYAML is optional
    yaml = None

TOOL = os.path.join(HERE, "glm_study_yaml.py")
TEMPLATE = os.path.join(HERE, "templates", "STUDY_TEMPLATE.yaml")
TEMPLATE_ARGS = ["new", "--id", "example", "--title", "Example — a new GLM study"]
FOOTER = g.TIER0_FOOTER_LINE

STUDY = """# Escalation — how far the carry climbs

## Tier 0 — the coarse read

**Question.** How far does a carry climb before it is absorbed?

**Verdict.** Every carry is absorbed within three steps on the tested range.

**Deciding figure.** 3 steps over 4096 seeds.

**Recomputed by.** `glm_universal.escalation.measure.max_climb`

""" + FOOTER + """

*Last altered 20 October 2026 (Round 49: tables refreshed).*

This study measures the carry climb of Rule 30 seeds
and records where the bound is proved.

## 1. The question this answers

See [the inventory](../glm_universal/corpus/inventory.py), [status](../STATUS.md#open),
[a section](#2-what-is-machine-checked) and [the web](https://example.org/x.md).

| seeds | max climb | note |
|------:|----------:|------|
| 1024  | 3         | a \\| b |
| 4096  | 3         | `x` |

```bash
python3 -m glm_universal.escalation.measure --seeds 4096
lake build RequestProject.Escalation
```

```text
## not a heading
```

### 1.1 Method

Seeds are enumerated in order.

## 2. What is machine-checked

The bound is `RequestProject.Escalation.climb_le_three` in `RequestProject/Escalation.lean`.

## 2. What is machine-checked

A duplicate heading gets a suffixed anchor.

## 3. What this leaves open

Trailing spaces here.   
\tA tab-indented line.
"""

EDGE_CASES = {
    "empty": "",
    "newline only": "\n",
    "blank lines": "\n\n\n",
    "title only, no newline": "# Title",
    "no sections": "# T\n\nJust prose.\n",
    "no trailing newline": "# T\n\n## A\n\nbody",
    "heading at end, no newline": "# T\n\n## A",
    "heading at end": "# T\n\n## A\n",
    "crlf": "# T\r\n\r\n## A\r\n\r\nbody\r\n\r\n## B\r\nx\r\n",
    "crlf, no final newline": "# T\r\n\r\n## A\r\n\r\nbody",
    "mixed line ends": "# T\r\n\n## A\rbody\r\n",
    "lone cr": "a\rb\r",
    "trailing spaces and tabs": "# T  \n\n## A \t\n\nx  \n\t\ty\t\n",
    "## inside fences": "# T\n\n```\n## not\n```\n\n## Real\n\n```md\n## not either\n```\n",
    "unclosed fence": "# T\n\n## A\n\n```\n## hidden\n",
    "consecutive headings": "## A\n## B\n\n\n## C\n\n\n\nx\n\n\n",
    "headings without blank lines": "# T\n## A\nx\n## B\ny",
    "heading with closing hashes": "## A ##\n\nx\n",
    "heading variants": "##  Two spaces  \n\n##\tTab\n\n##NoSpace\n\n### Sub\n",
    "duplicate headings": "## X\n\n## X\n\n## X\n",
    "bom": "\ufeff# T\n\n## A\n",
    "unicode": "# Été — 😀\n\n## Ünïcode\n\n\u2028 sep \u0085 nel\n",
    "control characters": "# T\n\n## A\n\nbell \x07 esc \x1b del \x7f\n",
    "tier 0 then intro": ("# T\n\n## Tier 0\n\n**Question.** q?\n\n**Verdict.** v.\n\n"
                          "**Deciding figure.** 1.\n\n**Recomputed by.** " + g.NO_FUNCTION
                          + "\n\n" + FOOTER + "\n\nIntro paragraph.\n\nAnother.\n\n## 1. Next\n\nx\n"),
    "leading blank lines in body": "## A\n\n\n\n  indented\n",
    "literal-block hostile": "## A\n\n \n  \n\t\nend  \n\n\n",
    "only a heading line": "##",
    "glm study": STUDY,
}

ADVERSARIAL = [
    "", " ", "  ", "\t", "\n", "\n\n", "a\n", "a\n\n", "a\n\n\n", "\na", " a\nb", "\ta\nb",
    "a \nb", "a\nb ", "a\n \n", "a\t\n", "null", "Null", "NULL", "~", "true", "False", "yes",
    "No", "on", "OFF", "y", "n", "0", "-0", "+1", "012", "0x1F", "0b101", "1_000", "1:30",
    "1e3", "1.5", ".5", "-.inf", ".NaN", "2026-10-27", "2026-10-27 10:00", "=", "<<", "- a",
    "-", "--", "---", "--- a", "...", "? a", "?", ": a", ":", "a:", "a: b", "a:b", "a #b",
    "a#b", "#a", "&a", "*a", "!a", "!!str", "|", ">", "%a", "@a", "`a", "'a'", '"a"', "[a]",
    "{a: b}", "a, b", "a,b", "\x00", "\x07", "\x08", "\x0b", "\x0c", "\x1b", "\x7f", "\x80",
    "\x85", "\xa0", "\u2028", "\u2029", "\ufeff", "a\ufeffb", "\ud7ff", "\ue000", "\ufffd",
    "\ufffe", "é", "😀", "\U0010ffff", "a\r\nb", "\r", "a\rb", "line\n  indented\n",
    "\n\nlead", "  \n", "a\\b", "\\", '"', "'", "tab\there", "x" * 300, "word " * 60,
    "# Title\n\n## Section\n", "```\n## x\n```\n", "**Question.** q?", "a  ", " a",
]


def roundtrip(text, path="studies/X_STUDY.md"):
    """md -> YAML text -> own parser -> md."""
    study = g.md_to_study(text, path)
    emitted = g.dump_yaml(study)
    back = g.load_yaml(emitted)
    return study, emitted, back, g.study_to_md(back)


def run_cli(*args, cwd=None):
    proc = subprocess.run([sys.executable, TOOL] + list(args), cwd=cwd,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")


class EmitterTest(unittest.TestCase):

    def test_plain_and_quoted(self):
        self.assertEqual(g.dump_yaml({"a": "plain text"}), "a: plain text\n")
        for s in ("", " x", "x ", "yes", "null", "~", "123", "1.5", "2026-10-27", "a: b",
                  "a #b", "- x", "#x", "x:", "'q'", "---", "@x", "tab\tin"):
            self.assertTrue(g.dump_yaml({"a": s}).startswith('a: "'), s)

    def test_literal_blocks_and_chomping(self):
        self.assertEqual(g.dump_yaml({"a": "x\ny"}), "a: |-\n  x\n  y\n")
        self.assertEqual(g.dump_yaml({"a": "x\ny\n"}), "a: |\n  x\n  y\n")
        self.assertEqual(g.dump_yaml({"a": "x\n\n", "b": 1}), "a: |+\n  x\n\nb: 1\n")
        self.assertEqual(g.dump_yaml({"a": " x\ny\n"}), "a: |2\n   x\n  y\n")
        self.assertEqual(g.dump_yaml({"a": "\n\tx\n"}), "a: |2\n\n  \tx\n")
        # a document must end with exactly one newline: no |+ at its very end
        self.assertEqual(g.dump_yaml({"a": "x\n\n"}), 'a: "x\\n\\n"\n')

    def test_escapes(self):
        self.assertEqual(g.dump_yaml({"a": "x\r\ny"}), 'a: "x\\r\\ny"\n')
        self.assertEqual(g.dump_yaml(["\x00\x07\x1b\x7f\ufeff\U0001F600"]),
                         '- "\\u0000\\u0007\\u001b\\u007f\\ufeff\U0001F600"\n')
        self.assertEqual(g.dump_yaml("\U000F0000"), "\U000F0000\n")
        self.assertEqual(g.dump_yaml("\ufffe"), '"\\ufffe"\n')

    def test_types_and_layout(self):
        doc = {"s": "x", "i": -3, "t": True, "f": False, "n": None, "l": [], "d": {},
               "nested": [{"k": [1, [2, {}]]}, [], "z"]}
        text = g.dump_yaml(doc)
        self.assertFalse(text.startswith("---"))
        self.assertTrue(text.endswith("\n") and not text.endswith("\n\n"))
        self.assertEqual(g.load_yaml(text), doc)
        self.assertEqual(list(g.load_yaml(g.dump_yaml({"z": 1, "a": 2}))), ["z", "a"])
        self.assertEqual(g.dump_yaml([]), "[]\n")
        self.assertEqual(g.dump_yaml(None), "null\n")

    def test_refuses_inexact_values(self):
        for bad in (1.5, {1: "x"}, object()):
            self.assertRaises(TypeError, g.dump_yaml, {"a": bad} if bad != {1: "x"} else bad)


class ParserTest(unittest.TestCase):

    def test_own_parser_reads_own_output(self):
        for s in ADVERSARIAL:
            for obj in ({"k": s}, [s, {"x": [s]}], {s: s}, s):
                self.assertEqual(g.load_yaml(g.dump_yaml(obj)), obj, repr(obj))

    def test_generated_strings(self):
        alphabet = ["a", " ", "\n", "\t", "#", ":", "-", '"', "'", "\\", "0", "é", "\r", "|"]
        for n in range(4):
            for t in itertools.product(alphabet, repeat=n):
                obj = {"k": "".join(t), "l": ["".join(t)]}
                self.assertEqual(g.load_yaml(g.dump_yaml(obj)), obj, repr(obj))

    def test_hand_written_yaml(self):
        text = ("# comment\nschema: glm-study/v1   # trailing comment\nn: ~\nm: null\nt: yes\n"
                "i: 42\nneg: -7\nflo: 1.5\nsq: 'it''s'\ndq: \"tab\\there \\u00e9\"\n"
                "flow: [a, 'b c', \"d\", 3]\nempty_l: []\nempty_d: {}\n"
                "lit: |\n  line one\n    indented\n\n  after blank\nkeep: |+\n  x\n\n"
                "strip: >-\n  folded\n  text\n\n  para\nind: |2-\n    two extra\n  base\n"
                "plain: a long plain\n  scalar on two lines\nseq:\n- a\n- b: 1\n  c: 2\n"
                "-   - nested\n    - list\nkey with spaces: value with colon:inside? no\n")
        got = g.load_yaml(text)
        self.assertEqual(got["n"], None)
        self.assertEqual(got["t"], True)
        self.assertEqual(got["i"], 42)
        self.assertEqual(got["flo"], "1.5")            # exact: floats stay strings
        self.assertEqual(got["sq"], "it's")
        self.assertEqual(got["dq"], "tab\there é")
        self.assertEqual(got["flow"], ["a", "b c", "d", 3])
        self.assertEqual(got["lit"], "line one\n  indented\n\nafter blank\n")
        self.assertEqual(got["keep"], "x\n\n")
        self.assertEqual(got["strip"], "folded text\npara")
        self.assertEqual(got["ind"], "  two extra\nbase")
        self.assertEqual(got["plain"], "a long plain scalar on two lines")
        self.assertEqual(got["seq"], ["a", {"b": 1, "c": 2}, ["nested", "list"]])
        if yaml is not None:
            got.pop("flo")
            want = yaml.safe_load(text)
            want.pop("flo")
            self.assertEqual(got, want)

    def test_multi_line_quoted(self):
        text = ('a: "one\n  two\n\n  three \\\n  four"\nb: \'x\n\n  y\'\'s\'\n')
        self.assertEqual(g.load_yaml(text), {"a": "one two\nthree four", "b": "x\ny's"})

    def test_refusals(self):
        for text in ("a: &x 1\n", "a: *x\n", "a: !!str 1\n", "a:\n\tb: 1\n", "a: 1\na: 2\n",
                     "a: 1\n b: 2\n", "a: [1, 2\n", 'a: "open\n', "a: b: c\n",
                     "--- 1\n--- 2\n"):
            self.assertRaises(g.YAMLError, g.load_yaml, text)

    def test_documents_markers_and_crlf(self):
        self.assertEqual(g.load_yaml("---\na: 1\n...\n"), {"a": 1})
        self.assertEqual(g.load_yaml("a: |\r\n  x\r\n"), {"a": "x\n"})
        self.assertEqual(g.load_yaml(""), None)

    @unittest.skipIf(yaml is None, "PyYAML is not importable")
    def test_agrees_with_pyyaml_on_adversarial_strings(self):
        for s in ADVERSARIAL:
            for obj in ({"k": s, "z": 1}, [s, {"x": [s]}], {s: [s]}, s):
                text = g.dump_yaml(obj)
                self.assertEqual(yaml.safe_load(text), obj, repr(text))
                self.assertEqual(g.load_yaml(text), yaml.safe_load(text), repr(text))

    @unittest.skipIf(yaml is None, "PyYAML is not importable")
    def test_agrees_with_pyyaml_on_generated_strings(self):
        alphabet = ["a", " ", "\n", "\t", "#", ":", "-", '"', "'", "\\", "\x85", "\u2028", "~"]
        for n in range(4):
            for t in itertools.product(alphabet, repeat=n):
                text = g.dump_yaml({"k": "".join(t)})
                self.assertEqual(g.load_yaml(text), yaml.safe_load(text), repr(text))

    @unittest.skipIf(yaml is None, "PyYAML is not importable")
    def test_agrees_with_pyyaml_on_every_study_yaml(self):
        for name, text in sorted(EDGE_CASES.items()):
            emitted = g.dump_yaml(g.md_to_study(text, "studies/X_STUDY.md"))
            self.assertEqual(g.load_yaml(emitted), yaml.safe_load(emitted), name)
        index = g.dump_yaml(g.build_index([HERE], with_bodies=True))
        self.assertEqual(g.load_yaml(index), yaml.safe_load(index))

    @unittest.skipIf(yaml is None, "PyYAML is not importable")
    def test_reads_what_pyyaml_writes(self):
        study = g.md_to_study(STUDY, "studies/ESCALATION_STUDY.md")
        for width in (40, 80, 10 ** 6):
            text = yaml.safe_dump(study, sort_keys=False, allow_unicode=True, width=width)
            self.assertEqual(g.load_yaml(text), study, width)
        self.assertEqual(g.load_yaml(yaml.safe_dump(study, sort_keys=False)), study)

    @unittest.skipIf(yaml is None, "PyYAML is not importable")
    def test_prefer_pyyaml(self):
        self.assertEqual(g.load_yaml("a: 1.5\n", prefer_pyyaml=True), {"a": 1.5})
        self.assertEqual(g.load_yaml("a: 1.5\n"), {"a": "1.5"})


class MarkdownModelTest(unittest.TestCase):

    def setUp(self):
        self.study = g.md_to_study(STUDY, "studies/ESCALATION_STUDY.md")

    def test_top_level(self):
        s = self.study
        self.assertEqual(list(s), list(g.KEY_ORDER))
        self.assertEqual((s["schema"], s["id"], s["path"], s["kind"], s["archive"]),
                         ("glm-study/v1", "escalation", "studies/ESCALATION_STUDY.md", "study",
                          False))
        self.assertEqual(s["title"], "Escalation — how far the carry climbs")
        self.assertEqual(s["tier0"], {
            "question": "How far does a carry climb before it is absorbed?",
            "verdict": "Every carry is absorbed within three steps on the tested range.",
            "figure": "3 steps over 4096 seeds.",
            "recomputed": "`glm_universal.escalation.measure.max_climb`"})
        self.assertEqual(s["last_altered"], "20 October 2026 (Round 49: tables refreshed)")
        self.assertEqual(s["summary"], "This study measures the carry climb of Rule 30 seeds "
                                       "and records where the bound is proved.")
        self.assertEqual(s["tags"], [])
        self.assertEqual(s["source"], {"head": "# Escalation — how far the carry climbs\n\n",
                                       "trailing_newline": True, "newline": "lf"})

    def test_sections(self):
        secs = self.study["sections"]
        self.assertEqual([x["heading"] for x in secs], [
            "Tier 0 — the coarse read", "1. The question this answers",
            "2. What is machine-checked", "2. What is machine-checked", "3. What this leaves open"])
        self.assertEqual([x["anchor"] for x in secs], [
            "tier-0-the-coarse-read", "1-the-question-this-answers", "2-what-is-machine-checked",
            "2-what-is-machine-checked-1", "3-what-this-leaves-open"])
        self.assertEqual([x.get("role") for x in secs], ["tier0", None, None, None, None])
        one = secs[1]
        self.assertIn("## not a heading", one["body"])
        self.assertEqual(one["subsections"], ["1.1 Method"])
        self.assertEqual(one["tables"], [{"header": ["seeds", "max climb", "note"],
                                          "rows": [["1024", "3", "a \\| b"],
                                                   ["4096", "3", "`x`"]]}])
        self.assertEqual(one["links"], ["STATUS.md", "glm_universal/corpus/inventory.py"])
        self.assertEqual(one["code_blocks"], 2)
        self.assertTrue(secs[4]["body"].endswith("here.   \n\tA tab-indented line.\n"))

    def test_derived(self):
        d = self.study["derived"]
        self.assertEqual(d["links"], ["STATUS.md", "glm_universal/corpus/inventory.py"])
        self.assertEqual(d["lean_files"], ["RequestProject/Escalation.lean"])
        self.assertEqual(d["lean_modules"], ["RequestProject.Escalation",
                                             "RequestProject.Escalation.climb_le_three"])
        self.assertIn("glm_universal.escalation.measure.max_climb", d["python_modules"])
        self.assertIn("glm_universal.corpus.checks.tier_report", d["python_modules"])
        self.assertEqual(d["commands"], [
            "python3 -m glm_universal.escalation.measure --seeds 4096",
            "lake build RequestProject.Escalation"])
        self.assertEqual(d["line_count"], STUDY.count("\n"))
        self.assertEqual(d["word_count"], len(STUDY.split()))

    def test_anchor_rule(self):
        self.assertEqual(g.anchor("3. What is `machine-checked` (Lean)"),
                         "3-what-is-machine-checked-lean")
        self.assertEqual(g.anchor("Tier 0 — the coarse read"), "tier-0-the-coarse-read")
        self.assertEqual(g.anchor("— ✓ —"), "section")
        self.assertEqual(g.anchor("[Link](x) **bold** _it_"), "linkx-bold-it")

    def test_names_kinds_archive(self):
        cases = {"studies/ESCALATION_STUDY.md": ("escalation", "study", False),
                 "audits/CORPUS_AUDIT.md": ("corpus_audit", "audit", False),
                 "NEW_IDEA_PROPOSAL.md": ("new_idea_proposal", "proposal", False),
                 "OLD_ARCHIVE.md": ("old_archive", "archive", True),
                 "archive/NOTES.md": ("notes", "document", True),
                 "x/Archive/y/README.md": ("readme", "readme", True),
                 "ARISTOTLE_SUMMARY.md": ("aristotle_summary", "document", True),
                 "MASTER_PLAN.md": ("master_plan", "document", False)}
        for path, want in cases.items():
            s = g.md_to_study("# T\n", path)
            self.assertEqual((s["id"], s["kind"], s["archive"]), want, path)
        self.assertEqual(g.md_to_study("no heading\n", "dir/FILE.md")["title"], "FILE.md")

    def test_partial_tier0_is_null(self):
        s = g.md_to_study("# T\n\n## Tier 0\n\n**Question.** q\n\n## 1. A\n", "X_STUDY.md")
        self.assertIsNone(s["tier0"])
        self.assertEqual(s["sections"][0]["role"], "tier0")
        self.assertIn("a study needs a complete tier0", " ".join(g.validate_study(s)[0]))

    def test_last_altered_variants(self):
        s = g.md_to_study("# T\n\n*Created 1 May 2026. Last altered 2 May 2026 (x).*\n", "a.md")
        self.assertEqual(s["last_altered"], "2 May 2026 (x)")
        self.assertIsNone(g.md_to_study("# T\n\n```\n*Last altered 1 May.*\n```\n",
                                        "a.md")["last_altered"])


class RoundTripTest(unittest.TestCase):

    def test_edge_cases_are_exact(self):
        for name, text in sorted(EDGE_CASES.items()):
            study, emitted, back, md = roundtrip(text)
            self.assertEqual(back, study, name)
            self.assertEqual(md, text, name)
            self.assertEqual(g.study_to_md(back, sync_tier0=True), text, name)
            self.assertEqual(g.dump_yaml(back), emitted, name)

    def test_derived_fields_are_ignored_when_rendering(self):
        study = g.md_to_study(STUDY, "studies/ESCALATION_STUDY.md")
        study["derived"] = {"word_count": 0}
        study["sections"][1]["tables"] = []
        study["summary"] = "edited"
        self.assertEqual(g.study_to_md(study), STUDY)

    def test_crlf_layer(self):
        study = g.md_to_study(EDGE_CASES["crlf"], "a.md")
        self.assertEqual(study["source"]["newline"], "crlf")
        self.assertNotIn("\r", g.dump_yaml(study).replace("\\r", ""))
        mixed = g.md_to_study(EDGE_CASES["mixed line ends"], "a.md")
        self.assertEqual(mixed["source"]["newline"], "lf")

    def test_roundtrip_file_and_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            good, bad = os.path.join(tmp, "A.md"), os.path.join(tmp, "B.md")
            with open(good, "wb") as handle:
                handle.write(STUDY.encode("utf-8"))
            with open(bad, "wb") as handle:
                handle.write(b"# caf\xe9\n")
            self.assertEqual(g.roundtrip_file(good, "A.md", yaml), [])
            self.assertEqual(g.roundtrip_file(bad, "B.md"), ["not valid UTF-8 (refused)"])


class RenderTest(unittest.TestCase):

    def test_canonical_layout(self):
        study = g.new_study("demo", "Demo", "Q?", "V.", "F 1.", g.NO_FUNCTION)
        self.assertNotIn("source", study)
        md = g.study_to_md(study)
        self.assertEqual(md.split("\n\n## 1.")[0], (
            "# Demo\n\n## Tier 0 — the coarse read\n\n**Question.** Q?\n\n**Verdict.** V.\n\n"
            "**Deciding figure.** F 1.\n\n**Recomputed by.** " + g.NO_FUNCTION + "\n\n"
            + FOOTER))
        again = g.md_to_study(md, study["path"])
        self.assertEqual(again["tier0"], study["tier0"])
        self.assertEqual([(s["heading"], s["body"]) for s in again["sections"]],
                         [(s["heading"], s["body"]) for s in study["sections"]])
        self.assertEqual([s["heading"] for s in study["sections"][1:]],
                         [h for h, _ in g.DEFAULT_SECTIONS])

    def test_canonical_render_regenerates_tier0(self):
        study = g.new_study("demo", "Demo")
        study["tier0"]["verdict"] = "Edited verdict."
        study["last_altered"] = "27 October 2026"
        md = g.study_to_md(study)
        again = g.md_to_study(md, study["path"])
        self.assertEqual(again["tier0"]["verdict"], "Edited verdict.")
        self.assertEqual(again["last_altered"], "27 October 2026")
        self.assertEqual(md.count("**Verdict.**"), 1)

    def test_hand_written_canonical_yaml(self):
        text = ("schema: glm-study/v1\nid: tiny\npath: studies/TINY_STUDY.md\ntitle: Tiny\n"
                "kind: study\narchive: false\ntier0:\n  question: Q?\n  verdict: V.\n"
                "  figure: '7'\n  recomputed: " + g.NO_FUNCTION + "\nsections:\n"
                "  - heading: 1. Body\n    anchor: 1-body\n    body: |\n      Seven is 7.\n")
        study = g.load_yaml(text)
        self.assertEqual(g.validate_study(study)[0], [])
        md = g.study_to_md(study)
        self.assertTrue(md.startswith("# Tiny\n\n## Tier 0 — the coarse read\n\n**Question.** Q?"))
        self.assertTrue(md.endswith("## 1. Body\n\nSeven is 7.\n"))

    def test_sync_tier0(self):
        study = g.md_to_study(STUDY, "studies/ESCALATION_STUDY.md")
        study["tier0"]["verdict"] = "Every carry is absorbed within four steps."
        errors = g.validate_study(study)[0]
        self.assertTrue(any("tier0.verdict disagrees" in e for e in errors), errors)
        plain = g.study_to_md(study)
        self.assertEqual(plain, STUDY)
        synced = g.study_to_md(study, sync_tier0=True)
        self.assertEqual(synced, STUDY.replace(
            "within three steps on the tested range.", "within four steps."))
        self.assertEqual(g.md_to_study(synced, study["path"])["tier0"], study["tier0"])

    def test_sync_tier0_inserts_section(self):
        study = g.md_to_study("# T\n\n## 1. A\n\nx\n", "studies/T_STUDY.md")
        study["tier0"] = {"question": "Q?", "verdict": "V.", "figure": "1", "recomputed": "R"}
        synced = g.study_to_md(study, sync_tier0=True)
        self.assertTrue(synced.startswith("# T\n\n## Tier 0 — the coarse read\n\n**Question.** Q?"))
        self.assertEqual(g.md_to_study(synced, study["path"])["tier0"], study["tier0"])

    def test_sync_tier0_adds_missing_field(self):
        text = "# T\n\n## Tier 0\n\n**Question.** Q?\n\n" + FOOTER + "\n\n## 1. A\n\nx\n"
        study = g.md_to_study(text, "studies/T_STUDY.md")
        study["tier0"] = {"question": "Q?", "verdict": "V.", "figure": "1", "recomputed": "R"}
        synced = g.md_to_study(g.study_to_md(study, sync_tier0=True), study["path"])
        self.assertEqual(synced["tier0"], study["tier0"])
        self.assertEqual(synced["sections"][1]["body"], "x\n")


class ValidateTest(unittest.TestCase):

    def test_converted_and_new_studies_are_valid(self):
        self.assertEqual(g.validate_study(g.md_to_study(STUDY, "studies/ESCALATION_STUDY.md")),
                         ([], []))
        errors, warnings = g.validate_study(g.new_study("x", "X"))
        self.assertEqual(errors, [])
        self.assertTrue(any("TODO placeholders remain" in w for w in warnings), warnings)

    def test_errors(self):
        base = g.md_to_study(STUDY, "studies/ESCALATION_STUDY.md")
        cases = [
            (lambda s: s.update(schema="glm-study/v0"), "schema must be"),
            (lambda s: s.pop("title"), "missing required key 'title'"),
            (lambda s: s.update(kind="essay"), "kind must be one of"),
            (lambda s: s.update(id="Not Snake"), "id must be a lower_snake string"),
            (lambda s: s["sections"][1].update(anchor="wrong"), "does not match heading"),
            (lambda s: s["sections"][3].update(anchor="2-what-is-machine-checked"),
             "duplicate anchors"),
            (lambda s: s.update(tier0=None), "a study needs a complete tier0"),
            (lambda s: s["tier0"].update(figure=""), "tier0.figure must be"),
            (lambda s: s["sections"][2].update(body="x\n\n## smuggled\n"), "do not survive"),
        ]
        for edit, message in cases:
            study = g.load_yaml(g.dump_yaml(base))
            edit(study)
            errors = g.validate_study(study)[0]
            self.assertTrue(any(message in e for e in errors), (message, errors))
        self.assertEqual(g.validate_study([1])[0], ["the YAML document is not a mapping"])

    def test_warnings(self):
        study = g.md_to_study(STUDY, "studies/ESCALATION_STUDY.md")
        study["extra"] = 1
        study["sections"][1]["body"] += "More words.\n"
        errors, warnings = g.validate_study(study)
        self.assertEqual(errors, [])
        self.assertTrue(any("unknown key 'extra'" in w for w in warnings))
        self.assertTrue(any("derived fields are stale" in w for w in warnings))
        canonical = g.new_study("x", "X", "Q?", "V.", "F.", g.NO_FUNCTION)
        canonical["tier0"]["verdict"] = "Other."
        errors, warnings = g.validate_study(canonical)
        self.assertEqual(errors, [])
        self.assertTrue(any("tier0.verdict disagrees" in w for w in warnings))


class IndexQueryTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = self.tmp.name
        os.makedirs(os.path.join(root, "studies"))
        os.makedirs(os.path.join(root, "archive"))
        with open(os.path.join(root, "studies", "ESCALATION_STUDY.md"), "w") as handle:
            handle.write(STUDY)
        with open(os.path.join(root, "archive", "OLD.md"), "w") as handle:
            handle.write("# Old notes\n\n## Log\n\nNothing about carries.\n")
        new = g.new_study("fresh", "Fresh study", "Why?", "Because.", "1.", g.NO_FUNCTION)
        with open(os.path.join(root, "studies", "FRESH_STUDY.yaml"), "w") as handle:
            handle.write(g.dump_yaml(new))
        self.root = root

    def tearDown(self):
        self.tmp.cleanup()

    def test_index(self):
        index = g.build_index([self.root])
        self.assertEqual(index["schema"], g.INDEX_SCHEMA)
        self.assertEqual([e["path"] for e in index["entries"]],
                         ["archive/OLD.md", "studies/ESCALATION_STUDY.md",
                          "studies/FRESH_STUDY.md"])
        esc = index["entries"][1]
        self.assertEqual(list(esc), ["id", "path", "yaml", "title", "kind", "archive", "tier0",
                                     "last_altered", "summary", "tags", "sections", "links",
                                     "lean_files", "lean_modules", "python_modules",
                                     "word_count"])
        self.assertIsNone(esc["yaml"])
        self.assertTrue(index["entries"][2]["yaml"].endswith("studies/FRESH_STUDY.yaml"))
        self.assertTrue(index["entries"][0]["archive"])
        self.assertNotIn("body", esc["sections"][0])
        self.assertEqual(g.dump_yaml(index), g.dump_yaml(g.build_index([self.root])))

    def test_query(self):
        index = g.build_index([self.root])
        q = lambda **kw: g.query_index(index, **kw)  # noqa: E731
        self.assertEqual(q(text="ABSORBED"), [("studies/ESCALATION_STUDY.md#tier-0-the-coarse-read",
                                               "Tier 0 — the coarse read")])
        self.assertEqual(q(text="seeds enumerated"), [])          # bodies not indexed
        self.assertEqual(q(lean="climb_le_three"),
                         [("studies/ESCALATION_STUDY.md#2-what-is-machine-checked",
                           "2. What is machine-checked")])
        self.assertEqual(q(link="STATUS.md"),
                         [("studies/ESCALATION_STUDY.md#1-the-question-this-answers",
                           "1. The question this answers")])
        self.assertEqual([u for u, _ in q(kind="document")], ["archive/OLD.md"])
        self.assertEqual(q(fields=["tier0.verdict=because"]), [("studies/FRESH_STUDY.md",
                                                                "Fresh study")])
        self.assertEqual(q(fields=["archive=true"]), [("archive/OLD.md", "Old notes")])
        full = g.build_index([self.root], with_bodies=True)
        self.assertEqual(g.query_index(full, text="seeds enumerated"),
                         [("studies/ESCALATION_STUDY.md#1-the-question-this-answers",
                           "1. The question this answers")])


class CommandLineTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name
        os.makedirs(os.path.join(self.dir, "studies"))
        self.md = os.path.join(self.dir, "studies", "ESCALATION_STUDY.md")
        with open(self.md, "w", encoding="utf-8") as handle:
            handle.write(STUDY)

    def tearDown(self):
        self.tmp.cleanup()

    def test_import_has_no_side_effects(self):
        proc = subprocess.run([sys.executable, "-c", "import glm_study_yaml"], cwd=HERE,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual((proc.returncode, proc.stdout, proc.stderr), (0, b"", b""))

    def test_md2yaml_yaml2md_validate_get(self):
        code, out, _ = run_cli("md2yaml", "studies/ESCALATION_STUDY.md", "-o", "e.yaml",
                               cwd=self.dir)
        self.assertEqual(code, 0)
        with open(os.path.join(self.dir, "e.yaml"), encoding="utf-8") as handle:
            study = g.load_yaml(handle.read())
        self.assertEqual(study["path"], "studies/ESCALATION_STUDY.md")
        code, out, _ = run_cli("yaml2md", "e.yaml", cwd=self.dir)
        self.assertEqual((code, out), (0, STUDY))
        code, out, _ = run_cli("render", "e.yaml", "--sync-tier0", "-o", "back.md", cwd=self.dir)
        with open(os.path.join(self.dir, "back.md"), encoding="utf-8") as handle:
            self.assertEqual(handle.read(), STUDY)
        code, out, _ = run_cli("validate", "e.yaml", cwd=self.dir)
        self.assertEqual((code, out), (0, "validate: 1 files, 0 errors, 0 warnings\n"))
        self.assertEqual(run_cli("get", "e.yaml", "--tier0", cwd=self.dir)[1],
                         g.tier0_block(study["tier0"]))
        self.assertEqual(run_cli("get", "e.yaml", "--field", "tier0.figure", cwd=self.dir)[1],
                         "3 steps over 4096 seeds.\n")
        code, out, _ = run_cli("get", "e.yaml", "--section", "3-what-this-leaves-open",
                               cwd=self.dir)
        self.assertTrue(out.startswith("## 3. What this leaves open\n\nTrailing spaces"))
        code, _, err = run_cli("get", "e.yaml", "--section", "nope", cwd=self.dir)
        self.assertEqual(code, 1)
        self.assertIn("no section", err)

    def test_validate_reports_errors(self):
        study = g.md_to_study(STUDY, "studies/ESCALATION_STUDY.md")
        study["tier0"]["figure"] = "5 steps"
        with open(os.path.join(self.dir, "bad.yaml"), "w", encoding="utf-8") as handle:
            handle.write(g.dump_yaml(study))
        code, out, _ = run_cli("validate", "bad.yaml", cwd=self.dir)
        self.assertEqual(code, 1)
        self.assertIn("bad.yaml: ERROR: tier0.figure disagrees", out)
        code, out, _ = run_cli("render", "bad.yaml", "--sync-tier0", "-o", "s.md", cwd=self.dir)
        code, out, _ = run_cli("md2yaml", "s.md", "-o", "s.yaml", cwd=self.dir)
        code, out, _ = run_cli("validate", "s.yaml", cwd=self.dir)
        self.assertIn("0 errors", out)

    def test_dir_conversion_roundtrip_index_query(self):
        with open(os.path.join(self.dir, "README.md"), "w", encoding="utf-8") as handle:
            handle.write("# Read me\r\n\r\nThe [study](studies/ESCALATION_STUDY.md).")
        code, _, err = run_cli("md2yaml", "--dir", ".", "--out", "yaml", cwd=self.dir)
        self.assertEqual(code, 0)
        self.assertTrue(os.path.isfile(os.path.join(self.dir, "yaml", "studies",
                                                    "ESCALATION_STUDY.yaml")))
        self.assertTrue(os.path.isfile(os.path.join(self.dir, "yaml", "README.yaml")))
        code, out, _ = run_cli("roundtrip", ".", cwd=self.dir)
        self.assertEqual(code, 0)
        self.assertIn("roundtrip: 2 files, 2 exact, 0 failed", out)
        code, out, _ = run_cli("index", "yaml", "-o", "INDEX.yaml", "--with-bodies", cwd=self.dir)
        self.assertEqual(code, 0)
        code, out, _ = run_cli("query", "INDEX.yaml", "--text", "tab-indented", cwd=self.dir)
        self.assertEqual((code, out), (0, "studies/ESCALATION_STUDY.md#3-what-this-leaves-open"
                                          "  3. What this leaves open\n"))
        code, out, _ = run_cli("query", "INDEX.yaml", "--link", "studies/ESCALATION_STUDY.md",
                               cwd=self.dir)
        self.assertEqual(out, "README.md  Read me\n")
        self.assertEqual(run_cli("query", "INDEX.yaml", "--text", "absent words",
                                 cwd=self.dir)[0], 1)
        with open(os.path.join(self.dir, "BAD.md"), "wb") as handle:
            handle.write(b"\xff\xfe")
        code, out, _ = run_cli("roundtrip", ".", cwd=self.dir)
        self.assertEqual(code, 1)
        self.assertIn("FAIL", out)

    def test_new_matches_template(self):
        code, out, _ = run_cli(*TEMPLATE_ARGS)
        self.assertEqual(code, 0)
        with open(TEMPLATE, encoding="utf-8") as handle:
            self.assertEqual(handle.read(), out)
        study = g.load_yaml(out)
        self.assertNotIn("source", study)
        self.assertEqual(study["id"], "example")
        self.assertEqual(g.validate_study(study)[0], [])
        code, out, _ = run_cli("new", "--id", "x", "--title", "X", "--question", "Q?",
                               "--verdict", "V.", "--figure", "F.", "--recomputed",
                               g.NO_FUNCTION, "-o", "x.yaml", cwd=self.dir)
        code, out, _ = run_cli("yaml2md", "x.yaml", cwd=self.dir)
        self.assertTrue(out.startswith("# X\n\n## Tier 0 — the coarse read\n\n**Question.** Q?"))


if __name__ == "__main__":
    unittest.main()
