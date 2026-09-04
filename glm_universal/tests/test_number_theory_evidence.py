"""``studies/GLM_Complete_Number_Theory_Evidence.md``, audited against the code.

The paper quotes three exact tables, a worked example that walks one number
down every layer of the pipeline, an index of the Lean theorems behind each
section, and a count of the Lean development.  All five are things the tree can
be asked about, so none of them is taken on trust here:

* the tables of §1.3, §2.4 and §9.2 are compared, cell by cell, against a fresh
  run of the generator the paper names (`studies/scripts/number_theory_tables.py`);
* the §14 transcript is compared against a fresh run of
  `glm_universal.examples.number_pipeline`, line for line;
* every theorem named in Appendix A is required to exist, in the file the
  appendix says it is in;
* the Lean file count the paper quotes is required to be the tree's;
* the paper's claim to construct no float is checked against the D7 scan of the
  modules it is computed from.

This is the instrument behind directive D6 for one particular document: if the
code moves, the paper fails the suite rather than ageing quietly.
"""

from __future__ import annotations

import io
import contextlib
import pathlib
import re
import runpy
import unittest
from typing import Dict, List, Tuple

from glm_universal.examples import number_pipeline
from glm_universal.reasoning import exactness as EX

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJECT_ROOT = PACKAGE_ROOT.parent
REPO_ROOT = PROJECT_ROOT.parent
PAPER = REPO_ROOT / "studies" / "GLM_Complete_Number_Theory_Evidence.md"
GENERATOR = REPO_ROOT / "studies" / "scripts" / "number_theory_tables.py"
LEAN_ROOT = REPO_ROOT / "RequestProject" / "GLM"

_ROW = re.compile(r"^\|(.+)\|\s*$")


def _cells(line: str) -> List[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _tables(text: str) -> List[List[List[str]]]:
    """Every markdown table in the text, as a list of rows of cells."""
    tables: List[List[List[str]]] = []
    current: List[List[str]] = []
    for line in text.splitlines():
        if _ROW.match(line):
            cells = _cells(line)
            if all(set(cell) <= set("-: ") for cell in cells):
                continue                      # the header rule
            current.append(cells)
        elif current:
            tables.append(current)
            current = []
    if current:
        tables.append(current)
    return tables


def _norm(cell: str) -> str:
    """A document cell as the generator would have printed it."""
    return cell.replace("**", "").replace("✓", "yes").replace("✗", "no").strip()


def _generator_tables() -> Dict[str, List[List[str]]]:
    """The three tables the paper's generator prints, keyed by first header."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        runpy.run_path(str(GENERATOR), run_name="__main__")
    out: Dict[str, List[List[str]]] = {}
    for table in _tables(buffer.getvalue()):
        out[" | ".join(table[0])] = table[1:]
    return out


def _paper_tables() -> Dict[str, List[List[str]]]:
    out: Dict[str, List[List[str]]] = {}
    for table in _tables(PAPER.read_text(encoding="utf-8")):
        key = " | ".join(_norm(cell).lower() for cell in table[0])
        out[key] = [[_norm(cell) for cell in row] for row in table[1:]]
    return out


def _paper_table(headers: Tuple[str, ...]) -> List[List[str]]:
    key = " | ".join(h.lower() for h in headers)
    tables = _paper_tables()
    assert key in tables, f"no table with headers {headers} in the paper"
    return tables[key]


class TestTheExactTables(unittest.TestCase):
    """§1.3, §2.4 and §9.2 against a fresh run of the generator."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.generated = _generator_tables()

    def test_the_coherence_table_is_the_generated_one(self):
        rows = _paper_table(("Hamming weight", "TAX", "NRCI", "Regime"))
        fresh = self.generated["weight | TAX | NRCI | regime"]
        self.assertEqual(len(rows), len(fresh))
        for paper_row, fresh_row in zip(rows, fresh):
            # "0 (vacuum)" and "8 (octad)" name the weight they carry
            self.assertEqual(paper_row[0].split()[0], fresh_row[0])
            self.assertEqual(paper_row[1:3], fresh_row[1:3])
            self.assertEqual(paper_row[3].lower(), fresh_row[3].lower())

    def test_the_sturmian_census_is_the_generated_one(self):
        rows = _paper_table(
            ("p", "⌊500/p⌋ (Lean prediction)", "measured 1s", "match",
             "longest 0-run", "longest the bound permits"))
        fresh = self.generated[
            "p | floor(500/p) | measured ones | match | longest 0-run | "
            "longest run the bound permits"]
        self.assertEqual(len(rows), len(fresh))
        for paper_row, fresh_row in zip(rows, fresh):
            self.assertEqual(paper_row, fresh_row)

    def test_the_census_covers_the_twenty_four_odd_primes(self):
        rows = _paper_table(
            ("p", "⌊500/p⌋ (Lean prediction)", "measured 1s", "match",
             "longest 0-run", "longest the bound permits"))
        self.assertEqual(len(rows), 24)
        self.assertIn("**24/24 exact matches**", PAPER.read_text(encoding="utf-8"))

    def test_the_binary_period_table_is_the_generated_one(self):
        rows = _paper_table(("p", "ord_p(2)", "full reptend", "H(1/p)"))
        fresh = self.generated["p | ord_p(2) | full reptend | H(1/p)"]
        self.assertEqual(rows, fresh)

    def test_twelve_of_the_twenty_four_are_full_reptend(self):
        rows = _paper_table(("p", "ord_p(2)", "full reptend", "H(1/p)"))
        self.assertEqual(sum(1 for row in rows if row[2] == "yes"), 12)


class TestTheWorkedExample(unittest.TestCase):
    """§14: the transcript is the program's output, not a quotation of it."""

    def test_the_transcript_matches_a_fresh_run(self):
        text = PAPER.read_text(encoding="utf-8")
        start = text.index("## 14. Worked example")
        # the first fenced block is the command; the second is the transcript
        block = text[start:].split("```")[3]
        quoted = [line.rstrip() for line in block.strip("\n").splitlines()]
        fresh = [line.rstrip() for line in number_pipeline.render().splitlines()]
        self.assertEqual(quoted, fresh)

    def test_the_example_is_the_one_the_paper_describes(self):
        fresh = number_pipeline.render()
        # the readings §14 draws out of the transcript, each checked
        self.assertIn("t = 1/7", fresh)
        self.assertIn("ones in 24 ticks   3", fresh)
        self.assertIn("longest 0-run      6", fresh)
        self.assertIn("coset weight       3", fresh)
        self.assertIn("nearest codeword   0x000000", fresh)
        self.assertIn("regime onBit", fresh)
        self.assertIn("binary period 3", fresh)
        self.assertIn("4/27 shares the", fresh)


class TestTheLeanIndex(unittest.TestCase):
    """Appendix A: every theorem named is in the file it is named under."""

    @staticmethod
    def _index() -> List[Tuple[str, List[str]]]:
        text = PAPER.read_text(encoding="utf-8")
        appendix = text[text.index("## Appendix A"):text.index("## Appendix B")]
        rows: List[Tuple[str, List[str]]] = []
        for line in appendix.splitlines():
            if not line.startswith("| `"):
                continue
            cells = _cells(line)
            if len(cells) != 3:
                continue
            files = re.findall(r"`([^`]+\.lean)`", cells[0])
            names = [n for n in re.findall(r"`([^`]+)`", cells[1])
                     if "*" not in n]
            if files:
                rows.append((files[0], names))
        return rows

    def test_the_index_is_not_empty(self):
        self.assertGreaterEqual(len(self._index()), 15)

    def test_every_named_file_exists(self):
        for filename, _ in self._index():
            self.assertTrue((LEAN_ROOT / filename).is_file(), filename)

    def test_every_named_theorem_is_in_its_file(self):
        pattern = "|".join(("theorem", "lemma", "def", "abbrev"))
        for filename, names in self._index():
            source = (LEAN_ROOT / filename).read_text(encoding="utf-8")
            declared = set(re.findall(
                rf"^(?:private\s+|protected\s+|noncomputable\s+)*"
                rf"(?:{pattern})\s+([A-Za-z_][A-Za-z0-9_'.]*)",
                source, re.MULTILINE))
            for name in names:
                self.assertIn(name, declared, f"{filename}: {name}")


class TestTheQuotedCounts(unittest.TestCase):
    """The paper's own figures about the tree."""

    @staticmethod
    def _lean_files() -> int:
        return sum(1 for path in LEAN_ROOT.rglob("*.lean"))

    def test_the_lean_file_count_is_current(self):
        text = PAPER.read_text(encoding="utf-8")
        quoted = set(int(n) for n in re.findall(
            r"(\d+) files under `RequestProject/GLM/`", text))
        quoted |= set(int(n) for n in re.findall(
            r"`RequestProject/GLM/` \((\d+) files\)", text))
        self.assertTrue(quoted, "the paper no longer states a file count")
        self.assertEqual(quoted, {self._lean_files()})

    def test_the_named_scripts_exist(self):
        text = PAPER.read_text(encoding="utf-8")
        for relative in re.findall(r"`(studies/scripts/[^`]+\.py)`", text):
            self.assertTrue((REPO_ROOT / relative).is_file(), relative)

    def test_the_named_modules_exist(self):
        text = PAPER.read_text(encoding="utf-8")
        for relative in re.findall(
                r"`overlay/(glm_universal/[^`]+\.py)`", text):
            self.assertTrue((PACKAGE_ROOT.parent / relative).is_file(),
                            relative)


class TestTheExactnessClaim(unittest.TestCase):
    """The paper claims its own arithmetic constructs no float (D7)."""

    def test_the_modules_it_computes_from_are_float_free(self):
        inventory = EX.exactness_inventory()
        sites = inventory["sites"]
        for module in ("reasoning/coherence.py", "reasoning/wobble.py",
                       "substrate/mog.py", "substrate/golay_decode.py",
                       "examples/number_pipeline.py"):
            self.assertNotIn(module, sites)

    def test_the_generator_itself_constructs_no_float(self):
        found = EX.module_float_sites(GENERATOR)
        # the sieve's ``limit ** 0.5`` would be a float; it is not there
        self.assertEqual(found, {})


if __name__ == "__main__":                      # pragma: no cover
    unittest.main()
