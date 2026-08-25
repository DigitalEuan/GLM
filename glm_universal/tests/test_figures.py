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


def _current_state(path: str) -> str:
    """The part of a document that claims to describe the package now."""
    text = _read(path)
    return text.split(_HISTORY_MARKER, 1)[0]


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
                self.assertIn(f"## {title}", self.rendered)
                self.assertTrue(self.data[key],
                                f"section {key} computed nothing")


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
        """
        superseded = (
            "1,324 tests", "1,094 tests", "1,405 tests", "652 tests",
            "1,669 tests", "8,818 subtests",
            "seventeen Lean files", "thirteen Lean files",
            "eighteen Lean files", "16 report subjects",
            "15 query kinds", "five registers", "52 diatomics; a general",
        )
        documents = [
            "README.md", "MASTER_PLAN.md", "CAPABILITY_ASSESSMENT.md",
            "STATUS.md",
            "overlay/README.md", "overlay/glm_universal/README.md",
            "overlay/glm_universal/tests/README.md",
            "overlay/glm_universal/data_objects/README.md",
            "overlay/glm_universal/reasoning/README.md",
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
