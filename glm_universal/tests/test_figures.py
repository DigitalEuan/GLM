"""``FIGURES.md`` must agree with a fresh computation.

The documentation quotes a lot of counts, and a count in a Markdown file is
inert: nothing stops it from describing the code as it was three changes ago.
:mod:`glm_universal.figures` recomputes the whole set, and this file is what
makes the recomputation binding -- if the generated table and the committed
one disagree, the suite fails and names the rows that moved.

The remedy when it fails is never to edit the Markdown.  It is::

    python -m glm_universal.figures --write

Beyond the equality check, the individual figures are checked against the
modules that produce them, so that a *wrong* generator is caught as well as a
stale file, and the READMEs that quote the headline counts are checked to
quote the current ones.
"""

from __future__ import annotations

import os
import re
import unittest

from glm_universal import figures as fg


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as handle:
        return handle.read()


#: ``overlay/`` -- the directory holding ``glm_universal/``.
_OVERLAY = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

#: The repository root, one level above the overlay.
_REPO = os.path.dirname(_OVERLAY)


def _repo_file(relative: str) -> str:
    """A repository-relative path, as an absolute one."""
    return os.path.normpath(os.path.join(_REPO, relative))


#: Everything after this marker in a document is an archive of what was true
#: at some earlier round -- a change-log row, or a write-up of a finished
#: step.  Those counts are *supposed* to be out of date: rewriting them would
#: falsify the record.  Only the text before the marker states the package as
#: it is now, so only that text is held to the current figures.
_HISTORY_MARKER = "<!-- figures:history -->"

#: A document whose archive sits *inside* it -- a change-log section with
#: current-state prose on both sides -- closes the archive again with this
#: marker.  An unclosed `figures:history` still runs to the end of the file,
#: which is what the documents split into a header and an archive rely on.
_CURRENT_MARKER = "<!-- figures:current -->"


def _current_state(path: str) -> str:
    """The part of a document that claims to describe the package now."""
    head, *rest = _read(path).split(_HISTORY_MARKER)
    kept = [head]
    for chunk in rest:
        if _CURRENT_MARKER in chunk:
            kept.append(chunk.split(_CURRENT_MARKER, 1)[1])
    return "".join(kept)


# ===========================================================================
# 1.  THE GENERATED FILE IS CURRENT
# ===========================================================================

class TestGeneratedFile(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.data = fg.figures(with_tests=True)
        cls.rendered = fg.render_markdown(cls.data)

    def test_figures_md_exists_beside_the_package(self):
        self.assertTrue(os.path.isfile(fg.figures_path()),
                        f"{fg.figures_path()} is missing; run "
                        f"`python -m glm_universal.figures --write`")

    def test_figures_md_matches_a_fresh_computation(self):
        committed = _read(fg.figures_path()).splitlines()
        fresh = self.rendered.splitlines()
        if committed == fresh:
            return
        drifted = [(a, b) for a, b in zip(committed, fresh) if a != b]
        self.fail(
            f"FIGURES.md is stale in {len(drifted)} row(s) "
            f"(and {abs(len(committed) - len(fresh))} row(s) added or "
            f"removed).  First difference:\n"
            f"  committed: {drifted[0][0] if drifted else '<length>'}\n"
            f"  fresh:     {drifted[0][1] if drifted else '<length>'}\n"
            f"Run `python -m glm_universal.figures --write`.")

    def test_every_section_is_rendered(self):
        for key, title in fg._SECTION_TITLES:
            with self.subTest(section=key):
                if key in _MEASURED_BY_A_RUN and not self.data[key]:
                    # honest emptiness: no complete run has recorded totals
                    # yet, and a zero would be a claim rather than a figure
                    continue
                self.assertIn(f"## {title}", self.rendered)
                self.assertTrue(self.data[key],
                                f"section {key} computed nothing")

    def test_the_sentences_section_is_rendered(self):
        generated = fg.sentences(self.data)
        self.assertIn("## Sentences", self.rendered)
        for name, sentence in generated.items():
            with self.subTest(name=name):
                self.assertIn(sentence, self.rendered)


#: Sections whose figures are a property of a *run* rather than of the
#: sources.  They are empty until a complete run has recorded them, and an
#: empty section is rendered as nothing rather than as a row of zeroes.
_MEASURED_BY_A_RUN = frozenset({"suite"})


# ===========================================================================
# 2.  THE GENERATOR AGREES WITH THE MODULES
# ===========================================================================

class TestGeneratorIsRight(unittest.TestCase):

    def test_the_package_surface_is_the_declared_one(self):
        import glm_universal
        from glm_universal.runtime.parser import KINDS
        from glm_universal.runtime.session import (DOMAINS, REPORT_SUBJECTS,
                                                   TASKS)
        figures = fg.package_figures()
        self.assertEqual(figures["version"], glm_universal.__version__)
        self.assertEqual(figures["query_kinds"], KINDS)
        self.assertEqual(figures["report_subjects"], REPORT_SUBJECTS)
        self.assertEqual(figures["domains"], DOMAINS)
        self.assertEqual(figures["tasks"], TASKS)

    def test_every_declared_subpackage_imports(self):
        import importlib
        for name in fg.package_figures()["subpackages"]:
            with self.subTest(subpackage=name):
                importlib.import_module(f"glm_universal.{name}")

    def test_the_register_counts_are_the_registers(self):
        from glm_universal.runtime.session import GeometricSession
        session = GeometricSession()
        counts = fg.register_figures()["by_domain"]
        for domain, count in counts.items():
            with self.subTest(domain=domain):
                self.assertEqual(count, len(session.register(domain)))
        self.assertEqual(fg.register_figures()["total_carriers"],
                         sum(counts.values()))

    def test_the_chemistry_figures_are_the_coverage_report(self):
        from glm_universal.reasoning import element_coverage as ec
        report = ec.element_coverage_report()
        figures = fg.chemistry_figures()
        self.assertEqual(figures["filled_cells"],
                         report["coverage"]["filled_cells"])
        self.assertEqual(figures["covalent_radius_estimated"],
                         report["estimates"]["estimate_count"])
        self.assertEqual(
            figures["covalent_radius_measured"]
            + figures["covalent_radius_estimated"]
            + figures["covalent_radius_absent"],
            figures["elements"])

    def test_the_molecule_figures_are_the_molecules_report(self):
        from glm_universal.data_objects import molecules as mol
        report = mol.molecules_report()
        figures = fg.molecule_figures()
        self.assertEqual(figures["molecules"], report["molecules"])
        self.assertEqual(figures["coordinates"], 24)
        self.assertTrue(figures["bundle_is_faithful"])

    def test_the_capability_figures_add_up(self):
        figures = fg.capability_figures()
        self.assertEqual(figures["holds"] + figures["breaks"]
                         + figures["errors"], figures["probes"])
        self.assertEqual(len(figures["breaking_probes"]), figures["breaks"])

    def test_the_evaluation_figures_add_up(self):
        figures = fg.evaluation_figures()
        self.assertEqual(figures["expected_answers"]
                         + figures["expected_refusals"], figures["cases"])
        self.assertEqual(figures["refusals_boundary"]
                         + figures["refusals_gap"],
                         figures["expected_refusals"])

    def test_the_lean_development_is_free_of_holes(self):
        figures = fg.lean_figures()
        self.assertTrue(figures, "the Lean tree was not found")
        self.assertEqual(figures["sorries"], 0)
        self.assertGreater(figures["files"], 0)

    def test_the_test_file_list_is_the_directory(self):
        figures = fg.test_figures()
        here = os.path.dirname(os.path.abspath(__file__))
        on_disk = sorted(name for name in os.listdir(here)
                         if name.startswith("test_") and name.endswith(".py"))
        self.assertEqual(list(figures["file_names"]), on_disk)
        self.assertEqual(figures["test_files"], len(on_disk))

    def test_the_tests_readme_has_a_row_for_every_test_file(self):
        """A new test file must reach the table, not just the total.

        The header count is generated and therefore cannot age, but the
        per-file table under it is written by hand, and a file added without a
        row went unnoticed for a round.  One row per file, and no row for a
        file that no longer exists.
        """
        here = os.path.dirname(os.path.abspath(__file__))
        on_disk = sorted(name for name in os.listdir(here)
                         if name.startswith("test_") and name.endswith(".py"))
        text = _read(os.path.join(here, "README.md"))
        rows = re.findall(r"^\| `(test_\w+\.py)` \|", text, re.MULTILINE)
        self.assertEqual(sorted(rows), on_disk,
                         "glm_universal/tests/README.md must carry exactly "
                         "one row per test file")
        self.assertEqual(len(rows), len(set(rows)),
                         "a test file is listed twice")


# ===========================================================================
# 3.  THE READMES QUOTE THE CURRENT FIGURES
# ===========================================================================

def _headline_claims():
    """``(path, what, phrase)`` -- phrases the documentation must contain.

    Each phrase is built from a recomputed figure, so the assertion is not
    "this README mentions a number" but "this README states the number the
    code currently produces".  Only the headline counts are pinned: the ones
    a reader would act on.
    """
    package = fg.package_figures()
    modules = package["modules_by_subpackage"]
    registers = fg.register_figures()["by_domain"]
    chemistry = fg.chemistry_figures()
    molecules = fg.molecule_figures()
    semantics = fg.semantics_figures()
    capabilities = fg.capability_figures()
    evaluation = fg.evaluation_figures()
    tests = fg.test_figures()
    lean = fg.lean_figures()

    counts = (
        ("query kinds", f"{package['query_kind_count']} query kinds"),
        ("report subjects",
         f"{package['report_subject_count']} report subjects"),
        ("registers", f"{package['domain_count']} registers"),
        ("molecules", f"{molecules['molecules']} molecules"),
        ("elements", f"{chemistry['elements']} elements"),
        ("meanings", f"{semantics['meanings']} meanings"),
        ("probes", f"{capabilities['probes']} probes"),
        ("evaluation cases", f"{evaluation['cases']} cases"),
        ("test files", f"{tests['test_files']} test files"),
        ("Lean files", f"{lean['files']} Lean files"),
    )
    subjects = f"{package['report_subject_count']} report subjects"
    kinds = f"{package['query_kind_count']} query kinds"
    domains = f"{package['domain_count']} registers"
    lean_files = f"{lean['files']} Lean files"
    probes = f"{capabilities['probes']} probes"

    out = [("overlay/FIGURES.md", what, phrase) for what, phrase in counts]
    out += [
        ("README.md", "registers", domains),
        ("README.md", "report subjects", subjects),
        ("README.md", "query kinds", kinds),
        ("README.md", "Lean files", lean_files),
        ("MASTER_PLAN.md", "registers", domains),
        ("MASTER_PLAN.md", "report subjects", subjects),
        ("STATUS.md", "registers", domains),
        ("STATUS.md", "report subjects", subjects),
        ("STATUS.md", "query kinds", kinds),
        ("STATUS.md", "Lean files", lean_files),
        ("STATUS.md", "probes", probes),
        ("STATUS.md", "test files", f"{tests['test_files']} test files"),
        ("CAPABILITY_ASSESSMENT.md", "probes", probes),
        ("CAPABILITY_ASSESSMENT.md", "Lean files", lean_files),
        ("CAPABILITY_ASSESSMENT.md", "evaluation cases",
         f"{evaluation['cases']} cases"),
        ("overlay/README.md", "registers", domains),
        ("overlay/README.md", "report subjects", subjects),
        ("overlay/README.md", "query kinds", kinds),
        ("overlay/README.md", "Lean files", lean_files),
        ("overlay/README.md", "test files",
         f"{tests['test_files']} test files"),
        ("overlay/glm_universal/README.md", "physics register",
         f"{registers['physics']} quantities"),
        ("overlay/glm_universal/README.md", "molecules register",
         f"{molecules['molecules']} molecules"),
        ("overlay/glm_universal/README.md", "report subjects", subjects),
        ("overlay/glm_universal/README.md", "query kinds", kinds),
        ("overlay/glm_universal/data_objects/README.md", "molecules",
         f"{molecules['molecules']} molecules"),
        ("overlay/glm_universal/reasoning/README.md", "reasoning modules",
         f"{modules['reasoning']} modules"),
        ("overlay/glm_universal/runtime/README.md", "report subjects",
         subjects),
        ("overlay/glm_universal/runtime/README.md", "query kinds", kinds),
        ("overlay/glm_universal/runtime/README.md", "registers", domains),
        ("overlay/glm_universal/capabilities/README.md", "probes", probes),
        ("overlay/glm_universal/evaluation/README.md", "evaluation cases",
         f"{evaluation['cases']} cases"),
        ("overlay/glm_universal/tests/README.md", "test files",
         f"{tests['test_files']} test files"),
        ("overlay/glm_lean/RequestProject/GLM/README.md", "Lean files",
         lean_files),
    ]
    return tuple(out)


class TestDocumentationQuotesCurrentFigures(unittest.TestCase):

    def test_the_headline_counts_are_stated_as_they_are_computed(self):
        for path, what, phrase in _headline_claims():
            with self.subTest(path=path, figure=what):
                full = _repo_file(path)
                self.assertTrue(os.path.isfile(full), f"{path} is missing")
                self.assertIn(
                    phrase, _current_state(full),
                    f"{path} does not state the current {what}: "
                    f"expected the phrase {phrase!r}")

    def test_no_document_still_claims_a_superseded_count(self):
        """Counts that were true in an earlier round and must not survive.

        Finding one of these means that document was not updated with the
        rest, which is exactly the failure this file exists to catch.

        A *per-phase* total in ``MASTER_PLAN.md`` is a historical record, not
        a claim about the present, so bare test totals of the form
        ``N tests across M test files`` are deliberately not listed here for
        the phases that carry their own measured-result table.
        """
        superseded = (
            "1,324 tests", "1,094 tests", "1,405 tests", "652 tests",
            "1,669 tests", "8,818 subtests", "1,677 tests",
            "1,884 tests", "1,885 tests",
            "seventeen Lean files", "thirteen Lean files",
            "eighteen Lean files", "16 report subjects",
            "33 report subjects", "35 reasoning modules", "92-case",
            "15 query kinds", "five registers", "52 diatomics; a general",
            "37 report subjects",
            "46 test files", "34 Lean files", "99 cases", "99-case",
            "37 reasoning modules", "71 modules",
            "40 report subjects", "35 Lean files", "6 registers",
            "2,205 tests", "2,183 collected tests",
            "2,309 tests", "2,309 collected tests",
            "41 report subjects", "37 Lean files", "51 test files",
            "103 cases", "103-case", "2,316 tests",
            # Retired in v5.12.  "104 collision classes" is a different
            # figure and is still true, so every phrase here names the unit
            # it counts rather than the bare number.
            "42 report subjects", "38 Lean files", "52 test files",
            "104 cases", "104 CLI cases", "104-case",
            "2,350 tests", "2,350 collected tests",
            "9,088 subtests", "9,165 subtests", "9,170 subtests",
            "9,232 subtests",
            # Retired in v5.13, when the economic register became the eighth
            # and its report the forty-fifth evaluation case.
            "7 registers", "45 reasoning modules", "43 report subjects",
            "112 cases", "112 CLI cases", "112-case",
            "2,424 tests", "2,424 collected tests", "10,782 subtests",
            "39 Lean files", "966 declarations",
            # Retired in v5.14, when the comparison-class register grew and
            # the comparative became a query kind of its own.
            "113 cases", "113 CLI cases", "113-case",
            "2,515 tests", "2,515 collected tests", "11,033 subtests",
            "41 Lean files", "1,020 declarations", "56 test files",
            # Retired in v5.15, when the denotation register closed the
            # `related_to` residue and earned a pipeline row and a case.
            "123 cases", "123 CLI cases", "123-case",
            "2,631 tests", "2,631 collected tests", "11,901 subtests",
            "58 test files", "43 Lean files", "1,072 declarations",
            "44 report subjects", "47 reasoning modules",
            # Retired in v5.16, when the recipe became an object of its own:
            # a tenth sub-package, a forty-sixth report subject, a
            # twenty-first query kind and the sixtieth test file.
            "45 report subjects", "20 query kinds",
            "nine sub-packages", "88 modules",
            "59 test files", "2,656 tests", "2,656 collected tests",
            "12,074 subtests",
            # Retired in v5.17, when the question shape became an object:
            # an eleventh sub-package, a forty-seventh report subject and
            # the sixty-first test file.
            "46 report subjects", "ten sub-packages", "92 modules",
            "45 Lean files", "129 cases", "129 CLI cases", "129-case",
            "60 test files", "2,746 tests", "2,746 collected tests",
            "12,508 subtests",
            # Retired in v5.19, when the lattice quantiser's search became a
            # lookup table: a forty-eighth report subject, a forty-ninth
            # reasoning module and the sixty-second test file.  The two Lean
            # files added since v5.17 retire their counts with it.
            "47 report subjects", "61 test files",
            "46 Lean files", "47 Lean files",
            "130 cases", "130 CLI cases", "130-case",
            "2,847 tests", "2,847 collected tests", "10,985 subtests",
            "96 modules", "48 reasoning modules",
        )
        documents = [
            "README.md", "MASTER_PLAN.md", "CAPABILITY_ASSESSMENT.md",
            "STATUS.md",
            "overlay/README.md", "overlay/glm_universal/README.md",
            "overlay/glm_universal/tests/README.md",
            "overlay/glm_universal/data_objects/README.md",
            "overlay/glm_universal/reasoning/README.md",
            "overlay/glm_universal/substrate/README.md",
            "overlay/glm_universal/semantics/README.md",
            "overlay/glm_universal/runtime/README.md",
            "overlay/glm_universal/capabilities/README.md",
            "overlay/glm_universal/evaluation/README.md",
            "overlay/glm_lean/RequestProject/GLM/README.md",
        ]
        for path in documents:
            full = _repo_file(path)
            if not os.path.isfile(full):
                continue
            text = _current_state(full)
            for phrase in superseded:
                with self.subTest(path=path, phrase=phrase):
                    self.assertNotIn(phrase, text)


# ===========================================================================
# 3a.  THE GENERATED SENTENCES, CHECKED BY SHAPE
# ===========================================================================
#
#  The list of superseded phrases above does real work, but it is a
#  hand-maintained artefact that grows every round -- which is the failure
#  mode it exists to prevent, one level up.  This check is the structural
#  version of it.  ``glm_universal.figures`` emits each sentence together
#  with a pattern that matches *any* sentence of that shape; here, every
#  match found in a document must be the sentence the generator produced.
#  Nothing has to be told which old number to look for.

#: Documents held to the generated sentences.  ``MASTER_PLAN.md`` is not one
#: of them: its phase records state what each phase measured at the time,
#: and rewriting those would falsify the record rather than correct it.
_SENTENCE_DOCUMENTS = (
    "README.md",
    "STATUS.md",
    "CAPABILITY_ASSESSMENT.md",
    "overlay/README.md",
    "overlay/FIGURES.md",
    "overlay/glm_universal/README.md",
    "overlay/glm_universal/tests/README.md",
    "overlay/glm_universal/data_objects/README.md",
    "overlay/glm_universal/reasoning/README.md",
    "overlay/glm_universal/substrate/README.md",
    "overlay/glm_universal/semantics/README.md",
    "overlay/glm_universal/runtime/README.md",
    "overlay/glm_universal/capabilities/README.md",
    "overlay/glm_universal/evaluation/README.md",
    "overlay/glm_lean/RequestProject/GLM/README.md",
)


class TestGeneratedSentencesAreTheOnesQuoted(unittest.TestCase):
    """Any phrase of a generated shape must be the generated phrase."""

    @classmethod
    def setUpClass(cls):
        cls.sentences = fg.sentences()
        cls.patterns = {name: pattern
                        for name, pattern, _ in fg.SENTENCE_PATTERNS}

    def test_every_pattern_matches_its_own_sentence(self):
        """A pattern that did not match its own sentence would check nothing."""
        for name, sentence in self.sentences.items():
            with self.subTest(name=name):
                pattern = self.patterns.get(name)
                self.assertIsNotNone(pattern,
                                     f"{name} has no shape to guard it")
                self.assertRegex(sentence, pattern)

    def test_every_sentence_shape_in_a_document_is_the_current_sentence(self):
        for path in _SENTENCE_DOCUMENTS:
            full = _repo_file(path)
            if not os.path.isfile(full):
                continue
            text = _current_state(full)
            for name, sentence in self.sentences.items():
                pattern = self.patterns[name]
                for found in re.findall(pattern, text):
                    with self.subTest(path=path, name=name, found=found):
                        self.assertEqual(
                            found, sentence,
                            f"{path} states {found!r} where the code now "
                            f"produces {sentence!r}; the generated sentence "
                            f"is in overlay/FIGURES.md under `{name}`")

    def test_the_suite_totals_are_a_generated_sentence(self):
        """The figure that went stale unnoticed is now one of these."""
        if "suite" not in self.sentences:
            self.skipTest("no complete run has recorded the suite totals")
        self.assertRegex(self.sentences["suite"],
                         r"^[\d,]+ tests across \d+ of the \d+ test files, "
                         r"[\d,]+ subtests, outside the document check$")

    def test_the_suite_sentence_states_the_whole_suite_it_was_taken_from(self):
        """The two file counts must agree rather than compete.

        The suite row counts one file fewer than the ``test_files`` row, so a
        sentence saying only ``N test files`` would state a number that is
        true of the measurement and false of the suite -- and the
        ``test_files`` shape, which reads any ``N test files`` it finds, would
        object to it.  The sentence therefore names both: the files measured,
        and the suite they were measured out of.  That second number is the
        ``test_files`` figure, so the two rows say the same thing.
        """
        if "suite" not in self.sentences:
            self.skipTest("no complete run has recorded the suite totals")
        self.assertIn(self.sentences["test_files"], self.sentences["suite"])

    def test_the_totals_leave_this_file_out_of_the_count(self):
        """The subtraction that makes a documentation round converge once.

        This file checks the documents, and the documents quote the suite
        totals, so counting this file made the totals depend on what the
        documents say.  The ledger now measures them over the suite minus
        this file -- every unit still runs and still has to pass -- and the
        sentence says so.  The check here is that the exclusion is real: the
        counted units are the suite without this file, and one fewer.
        """
        from glm_universal.signoff import ledger as sl
        suite = [path.name for path in sl.test_units()]
        counted = [path.name for path in sl.counted_units()]
        self.assertIn("test_figures.py", suite)
        self.assertNotIn("test_figures.py", counted)
        self.assertEqual(len(counted) + 1, len(suite))


# ===========================================================================
# 4.  THE MODULE DOCSTRINGS QUOTE THE CURRENT REGISTERS
# ===========================================================================

class TestModuleDocstringsQuoteCurrentFigures(unittest.TestCase):
    """A count in a docstring goes stale exactly as a count in a README does.

    :mod:`glm_universal.runtime.session` describes the registers it loads and
    states their sizes.  That paragraph said ``physics (660 quantities)`` long
    after the register had grown to its present size -- a reader of the module
    was told a number the code had not produced for several rounds.  The
    figure is now read out of the live registers here, so the paragraph cannot
    drift from them again.
    """

    @classmethod
    def setUpClass(cls):
        from glm_universal.runtime import session as se
        cls.session_doc = se.__doc__ or ""
        cls.session = se.GeometricSession()

    def _quoted(self, pattern: str) -> int:
        found = re.search(pattern, self.session_doc)
        self.assertIsNotNone(
            found,
            f"the session docstring no longer states {pattern!r}")
        return int(found.group(1))

    def test_the_session_docstring_states_the_physics_register_size(self):
        self.assertEqual(self._quoted(r"``physics`` \((\d+) quantities\)"),
                         len(self.session.register("physics")))

    def test_the_session_docstring_states_the_chemistry_register_size(self):
        self.assertEqual(self._quoted(r"``chemistry`` \((\d+) elements\)"),
                         len(self.session.register("chemistry")))

    def test_the_session_docstring_states_the_molecule_register_size(self):
        self.assertEqual(self._quoted(r"``molecules`` \((\d+) molecules"),
                         len(self.session.register("molecules")))

    def test_the_session_docstring_names_every_register(self):
        from glm_universal.runtime.session import DOMAINS
        for domain in DOMAINS:
            with self.subTest(domain=domain):
                self.assertIn(f"``{domain}``", self.session_doc)

    def test_the_package_docstring_states_the_physics_register_size(self):
        import glm_universal
        found = re.search(r"points: (\d+) physical quantities",
                          glm_universal.__doc__ or "")
        self.assertIsNotNone(
            found,
            "the package docstring no longer states the register size")
        self.assertEqual(int(found.group(1)),
                         len(self.session.register("physics")))

    def test_the_package_docstring_names_every_sub_package(self):
        import glm_universal
        doc = glm_universal.__doc__ or ""
        for name in ("substrate", "data_objects", "reasoning", "semantics",
                     "runtime", "migration", "benchmarks", "capabilities",
                     "evaluation", "signoff"):
            with self.subTest(name=name):
                self.assertIn(f"``glm_universal.{name}``", doc)

    def test_the_physics_module_docstring_states_the_register_size(self):
        from glm_universal.data_objects import physics as ph
        quoted = set(re.findall(r"(\d+)[ -](?:quantities|concept|named)",
                                ph.__doc__ or ""))
        self.assertTrue(quoted, "the physics docstring quotes no count")
        for count in quoted:
            with self.subTest(count=count):
                self.assertEqual(int(count),
                                 len(self.session.register("physics")))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
