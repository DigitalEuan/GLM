"""``glm_universal.figures`` -- every number the documentation quotes.

Why this module exists
----------------------
The documentation quotes a great many counts: how many quantities are in the
physics register, how many of the 118 elements carry a covalent radius, how
many meanings the grounded graph holds, how many capability probes hold and
how many break.  Every one of them is a fact about the code, and every one of
them goes stale the moment the code moves.

Rather than re-deriving them by hand on each iteration, this module
recomputes the whole set in one call and renders it as the Markdown table
that ships as ``FIGURES.md``.  Three things follow:

* **one command refreshes the documentation's numbers** --
  ``python -m glm_universal.figures --write`` rewrites ``FIGURES.md``;
* **drift is a test failure, not a discovery** --
  ``tests/test_figures.py`` compares the file on disk against a fresh
  computation and fails if they differ, so a stale figure cannot be pushed;
* **the READMEs have somewhere to point.**  A README that quotes a count
  cites the row here that produces it, so a reader can see what recomputes
  it.

What is *not* here
------------------
Two figures cannot be computed from inside the package and are recorded
rather than derived: the number of tests the suite collects (that needs
``pytest`` to walk the suite -- pass ``--with-tests`` to fill it in) and the
Lean development's file and line counts (those need the repository, not the
package -- pass ``--lean-root``).  Both are labelled as measured externally
wherever they appear.

The one figure that used to be a fixed point
--------------------------------------------
One row is different in kind from the rest, and it is worth knowing what was
done about it.  The ``suite`` row -- *N tests across M test files, K
subtests* -- is measured by running the suite, and the suite includes
``tests/test_figures.py``, which checks the documents that quote that row.
Measured over the whole suite the figure was **self-referential**: it counted
a test file whose own size depended on what the documents said.

Two different things got called "drift", and only one of them was expensive.
A documented figure changing **value** -- ``2,745`` becomes ``2,746`` --
rewrote digits inside sentences that already existed, which did not change
how many checks the document check performs, so one complete run converged.
The **set** of documented sentences changing -- a document added, a quoted
phrase appearing or disappearing, a test that used to skip now running --
moved ``test_figures.py``'s own subtest count, which moved the suite totals,
which were themselves quoted: that round needed **two** complete runs, the
first to learn the new shape and the second to certify the numbers written
from it.  Nothing about it was unsound; it was just an expensive way to be
right, repeated every documentation round.

As of v1.12.0 the loop is gone rather than managed.  The totals are measured
over ``signoff.ledger.counted_units()`` -- the suite **minus** the
document-checking file.  Every unit is still run, and every one still has to
pass before any total is recorded; the one file whose size the documentation
can move is simply not counted.  So nothing a document says can move a number
a document quotes, and a documentation round converges in one pass by
construction.  The generated sentence -- *N tests across M of the T test
files, K subtests, outside the document check* -- states the subtraction
where the figure is read rather than hiding it in the ledger, and names the
whole suite ``T`` as well as the measured part ``M`` so that this row and the
``test_files`` row agree instead of appearing to contradict each other.

Everything else is exact and deterministic: no float is constructed, nothing
is sampled, and two runs on the same tree give the same table.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import subprocess
import sys
from fractions import Fraction
from typing import Dict, List, Mapping, Optional, Tuple

__all__ = [
    "package_figures",
    "register_figures",
    "chemistry_figures",
    "molecule_figures",
    "semantics_figures",
    "capability_figures",
    "evaluation_figures",
    "benchmark_figures",
    "lean_figures",
    "test_figures",
    "suite_figures",
    "figures",
    "sentences",
    "SENTENCE_PATTERNS",
    "render_markdown",
    "figures_path",
    "main",
]


# ===========================================================================
# 1.  THE PACKAGE SURFACE
# ===========================================================================

def package_figures() -> Dict[str, object]:
    """Version, sub-packages, query kinds, report subjects, tasks."""
    import glm_universal
    from .runtime.parser import KINDS
    from .runtime.session import DOMAINS, REPORT_SUBJECTS, TASKS

    subpackages = tuple(name for name in glm_universal.__all__
                        if name != "__version__")
    here = os.path.dirname(os.path.abspath(__file__))
    modules = {}
    for name in subpackages:
        folder = os.path.join(here, name)
        modules[name] = sum(
            1 for entry in os.listdir(folder)
            if entry.endswith(".py") and not entry.startswith("_"))
    return {
        "version": glm_universal.__version__,
        "subpackages": subpackages,
        "subpackage_count": len(subpackages),
        "modules_by_subpackage": modules,
        "module_count": sum(modules.values()),
        "query_kinds": KINDS,
        "query_kind_count": len(KINDS),
        "report_subjects": REPORT_SUBJECTS,
        "report_subject_count": len(REPORT_SUBJECTS),
        "domains": DOMAINS,
        "domain_count": len(DOMAINS),
        "tasks": TASKS,
        "task_count": len(TASKS),
    }


def register_figures() -> Dict[str, object]:
    """How many carriers each register holds, and the total."""
    from .runtime.session import DOMAINS, GeometricSession

    session = GeometricSession()
    counts = {domain: len(session.register(domain)) for domain in DOMAINS}
    return {
        "by_domain": counts,
        "total_carriers": sum(counts.values()),
    }


# ===========================================================================
# 2.  CHEMISTRY -- THE ELEMENT REGISTER AND HOW SPARSE IT IS
# ===========================================================================

def chemistry_figures() -> Dict[str, object]:
    """The element register, and the three honest widenings of it."""
    from .data_objects import elements as el
    from .reasoning import element_coverage as ec

    report = ec.element_coverage_report()
    coverage = report["coverage"]
    derived = report["derived"]
    estimates = report["estimates"]
    model = estimates["model"]
    cross = report["cross_check"]
    return {
        "elements": coverage["elements"],
        "diatomics": len(el.load_diatomic_register()),
        "measured_fields": len(coverage["counts"]),
        "total_cells": coverage["total_cells"],
        "filled_cells": coverage["filled_cells"],
        "complete_fields": coverage["complete_fields"],
        "sparse_fields": coverage["sparse_fields"],
        "sparsest_field": coverage["sparsest"],
        "sparsest_count": coverage["counts"][coverage["sparsest"]],
        "covalent_radius_measured": estimates["measured_count"],
        "covalent_radius_estimated": estimates["estimate_count"],
        "covalent_radius_absent": len(estimates["still_absent"]),
        "covalent_coverage_before": str(estimates["coverage_before"]),
        "covalent_coverage_after": str(estimates["coverage_after"]),
        "fit_slope": str(model["slope"]),
        "fit_intercept_pm": str(model["intercept_pm"]),
        "fit_mean_absolute_residual_pm":
            str(model["mean_absolute_residual_pm"]),
        "fit_worst_element": model["worst_element"],
        "fit_max_absolute_residual_pm":
            str(model["max_absolute_residual_pm"]),
        "derived_attributes": derived["attribute_count"],
        "derived_new_cells": derived["new_cells"],
        "cross_check_compared": cross["compared"],
        "cross_check_agree_within_20": cross["agree_within_20_count"],
        "cross_check_disagree": cross["disagree_beyond_20"],
        "cross_check_largest_difference_element":
            cross["largest_difference"]["element"],
        "cross_check_largest_difference":
            str(cross["largest_difference"]["difference"]),
    }


def molecule_figures() -> Dict[str, object]:
    """The molecules register: what it holds and what its summary loses."""
    from .data_objects import molecules as mol

    report = mol.molecules_report()
    collisions = report["collisions"]
    return {
        "molecules": report["molecules"],
        "ions": len(report["charged"]),
        "distinct_elements_used": report["distinct_elements_used"],
        "coordinates": report["coordinates"],
        "derived_fields": report["derived_fields"],
        "missing_by_field": dict(report["missing_by_field"]),
        "bundle_is_faithful": collisions["bundle_is_faithful"],
        "distinct_bundles": collisions["distinct_bundles"],
        "bundle_collisions": collisions["bundle_collision_count"],
        "distinct_composites": collisions["distinct_composites"],
        "composite_collisions": collisions["composite_collision_count"],
        "largest_by_mass": report["largest_by_mass"][0],
        "largest_by_mass_u": str(report["largest_by_mass"][1]),
        "largest_by_atom_count": report["largest_by_atom_count"][0],
        "largest_atom_count": report["largest_by_atom_count"][1],
    }


# ===========================================================================
# 3.  MEANING
# ===========================================================================

def semantics_figures() -> Dict[str, object]:
    """The grounded graph, and the audit of the inherited concept graph."""
    from .semantics import audit as sau

    report = sau.audit_report()
    grounding = report["concept_grounding"]
    edges = report["edge_grounding"]
    carrier = report["carrier_information"]
    replacement = report["replacement"]
    graph = sau.graph_report()
    return {
        "meanings": replacement["meanings"],
        "notations": replacement["notations"],
        "binary_edges": replacement["binary_edges"],
        "ternary_edges": replacement["ternary_edges"],
        "all_edges_reverified": replacement["all_edges_reverified"],
        "refused_terms": graph["refused_terms"],
        "nodes_by_kind": dict(graph["nodes_by_kind"]),
        "isolated_meanings": graph["isolated_meanings"],
        "collapsed_meanings": graph["collapsed_meanings"],
        "inherited_concepts": grounding["concepts"],
        "inherited_grounded": grounding["grounded"],
        "inherited_edges": edges["edges"],
        "inherited_derivable_edges": edges["classes"].get("derivable", 0),
        "inherited_edge_classes": dict(edges["classes"]),
        "mean_hamming_related": carrier["mean_hamming_related"],
        "mean_hamming_unrelated": carrier["mean_hamming_unrelated"],
    }


# ===========================================================================
# 4.  WHAT IT CAN AND CANNOT DO
# ===========================================================================

def capability_figures() -> Dict[str, object]:
    """The probe verdicts, by area."""
    from .capabilities import harness as ch

    report = ch.capability_report()
    by_area = {area: dict(counts)
               for area, counts in sorted(report["by_area"].items())}
    return {
        "probes": report["probes"],
        "holds": report["holds"],
        "breaks": report["breaks"],
        "errors": report["errors"],
        "surprises": report["surprises"],
        "areas": len(by_area),
        "by_area": by_area,
        "breaking_probes": tuple(
            result["name"] for result in report["results"]
            if result["verdict"] == "breaks"),
    }


def evaluation_figures() -> Dict[str, object]:
    """The end-to-end question set: how many cases, of what kind."""
    from .evaluation import cases as ec

    by_kind = {kind: len(group)
               for kind, group in sorted(ec.cases_by_kind().items())}
    refusals = [case for case in ec.CASES if case.expect == "refusal"]
    return {
        "cases": len(ec.CASES),
        "kinds_covered": len(by_kind),
        "by_kind": by_kind,
        "expected_answers": sum(1 for c in ec.CASES if c.expect == "answer"),
        "expected_refusals": len(refusals),
        "refusals_boundary": sum(1 for c in refusals
                                 if c.classification == "boundary"),
        "refusals_gap": sum(1 for c in refusals
                            if c.classification == "gap"),
        "gap_cases": tuple(c.id for c in refusals
                           if c.classification == "gap"),
        "report_subjects_exercised": len(ec.SUBJECTS_COVERED),
    }


def benchmark_figures() -> Dict[str, object]:
    """The benchmark suites and their scores."""
    from .benchmarks import harness as bh

    report = bh.benchmark_report()
    return {
        "suites": report["suite_count"],
        "tasks": report["task_count"],
        "passed": report["passed_count"],
        "overall_score": str(report["overall_score"]),
        "null_results": len(report["null_results"]),
        "by_suite": {claim["suite"]: claim["claim"]
                     for claim in report["claims"]},
    }


# ===========================================================================
# 5.  MEASURED OUTSIDE THE PACKAGE
# ===========================================================================

#: A proof hole, as a whole word.  Matching the substring would count the
#: word "admitted" in a docstring as an unproven theorem.
_HOLE = re.compile(r"\b(sorry|admit)\b")



def lean_figures(root: Optional[str] = None) -> Dict[str, object]:
    """The Lean development: files, lines and remaining ``sorry``s.

    ``root`` is the directory holding ``RequestProject/``.  Returns an empty
    mapping when it cannot be found, rather than guessing.
    """
    if root is None:
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates = [os.path.join(here, "glm_lean"),
                      os.path.dirname(here)]
    else:
        candidates = [root]
    for candidate in candidates:
        tree = os.path.join(candidate, "RequestProject", "GLM")
        if not os.path.isdir(tree):
            continue
        files: List[str] = []
        lines = 0
        sorries = 0
        for dirpath, _dirnames, filenames in os.walk(tree):
            for filename in sorted(filenames):
                if not filename.endswith(".lean"):
                    continue
                path = os.path.join(dirpath, filename)
                files.append(os.path.relpath(path, candidate))
                with open(path, encoding="utf-8") as handle:
                    for line in handle:
                        lines += 1
                        # Whole words only: "admitted" and "admits" occur in
                        # the prose of several docstrings and are not holes.
                        if _HOLE.search(line):
                            sorries += 1
        return {
            "root": os.path.relpath(candidate,
                                    os.path.dirname(os.path.dirname(
                                        os.path.abspath(__file__)))),
            "files": len(files),
            "lines": lines,
            "sorries": sorries,
            "file_names": tuple(sorted(files)),
        }
    return {}


def test_figures(run: bool = False) -> Dict[str, object]:
    """How many tests the suite collects.

    Collected with ``pytest --collect-only`` in a subprocess, because the
    count is a property of the suite rather than of the package.  Returns the
    file list unconditionally and the count only when ``run`` is true.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    tests = os.path.join(here, "tests")
    names = tuple(sorted(name for name in os.listdir(tests)
                         if name.startswith("test_")
                         and name.endswith(".py")))
    out: Dict[str, object] = {"test_files": len(names), "file_names": names}
    if not run:
        return out
    process = subprocess.run(
        [sys.executable, "-m", "pytest", tests, "--collect-only", "-q"],
        cwd=os.path.dirname(here), capture_output=True, text=True)
    collected = None
    for line in process.stdout.splitlines():
        if "test" in line and "collected" in line:
            collected = int(line.split()[0])
    out["collected"] = collected
    return out


def suite_figures() -> Dict[str, object]:
    """How many tests and subtests the last complete run counted.

    A test total and a subtest total are properties of a *run*: no amount of
    reading the sources produces them.  The sign-off ledger records them, and
    only a release run -- every unit passing with the exhaustive cases on --
    is allowed to write them, so this is the figure a complete run produced
    rather than a partial count.  Empty until such a run has happened, which
    is the honest answer and not a zero.

    This is the row that was missing: the subtest total appeared in five
    documents and in nothing that checked it, so it aged quietly for two
    rounds.  Quoting it here brings it under the same one check as the rest.

    The counts are measured over the suite *minus* the document-checking file
    (``signoff.ledger.counted_units``), which is what makes them reachable in
    one pass; ``excludes`` names the file, ``of_test_files`` is the whole
    suite it was taken out of, and the generated sentence states both, so a
    reader is never left to wonder why this row's file count is one below the
    ``test_files`` row's.
    """
    from .signoff import ledger as sl

    totals = sl.suite_totals()
    if not totals:
        return {}
    excludes = tuple(totals.get("excludes") or ())
    counted = totals.get("test_files")
    return {
        "test_files": counted,
        "of_test_files": (counted + len(excludes)
                          if counted is not None else None),
        "tests": totals.get("tests"),
        "subtests": totals.get("subtests"),
        "excludes": ", ".join(excludes) or "(nothing)",
        "measured_by": "the sign-off ledger, at the last complete run",
        "python": totals.get("python"),
    }


# ===========================================================================
# 6.  THE WHOLE TABLE
# ===========================================================================

def figures(with_tests: bool = False,
            lean_root: Optional[str] = None) -> Dict[str, object]:
    """Every documented figure, recomputed."""
    return {
        "package": package_figures(),
        "registers": register_figures(),
        "chemistry": chemistry_figures(),
        "molecules": molecule_figures(),
        "semantics": semantics_figures(),
        "capabilities": capability_figures(),
        "evaluation": evaluation_figures(),
        "benchmarks": benchmark_figures(),
        "lean": lean_figures(lean_root),
        "tests": test_figures(run=with_tests),
        "suite": suite_figures(),
    }


# ===========================================================================
# 6a.  GENERATED PROSE
# ===========================================================================
#
#  A README does not quote a table row, it quotes a sentence.  Every round
#  that changed a count therefore had to find the sentences again by hand,
#  and the guard against the *old* sentence was a list that grew every time.
#  A list of forbidden phrases is a hand-maintained artefact, which is the
#  same failure mode one level up.
#
#  So the generator emits the sentences too.  Each one has a pattern that
#  matches *any* sentence of its shape, current or superseded, and
#  ``tests/test_figures.py`` requires that every match in a document is the
#  sentence generated here.  That check is total: it does not have to be told
#  which old number to look for, because it objects to any number but the
#  present one.

#: name -> (pattern matching any sentence of this shape, what it counts).
#: The pattern is deliberately loose about the number and strict about the
#: unit, so ``104 collision classes`` is never confused with ``104 cases``.
SENTENCE_PATTERNS: Tuple[Tuple[str, str, str], ...] = (
    ("registers", r"\b\d+ registers\b", "how many registers there are"),
    ("query_kinds", r"\b\d+ query kinds\b", "how many query kinds"),
    ("report_subjects", r"\b\d+ report subjects\b", "how many subjects"),
    ("evaluation_cases", r"\b\d+ CLI cases\b", "the evaluation set"),
    ("test_files", r"\b\d+ test files\b", "how many test files"),
    ("lean_files", r"\b\d+ Lean files\b", "the Lean development"),
    ("suite", r"\b[\d,]+ tests across \d+(?: of the \d+)? test files, "
     r"[\d,]+ subtests(?:, outside the document check)?",
     "what a complete run counts"),
)

#  Four counts are deliberately *not* here.  "N elements", "N molecules",
#  "N probes" and "N meanings" are phrases the documentation also uses for
#  subsets -- the 17 elements the molecule register happens to cover, the 11
#  probes in one probe file, the 24 elements a fit was made on -- so a
#  pattern over them would object to sentences that are true.  Those four
#  are pinned instead by the exact-phrase check in
#  ``tests/test_figures.py``, which names the document it holds to them.
#  The rule for adding a shape here is that the unit must be one the project
#  only ever states as a whole.


def _thousands(value: object) -> str:
    return f"{int(value):,}" if isinstance(value, int) else str(value)


def sentences(data: Optional[Mapping[str, object]] = None
              ) -> Dict[str, str]:
    """The sentences a document should quote, as the generator writes them.

    A name is absent when the figure behind it has not been measured -- the
    suite totals before a complete run, the Lean counts without the tree --
    rather than being rendered as a zero.
    """
    data = data if data is not None else figures()

    def get(section: str, key: str) -> object:
        block = data.get(section) or {}
        return block.get(key)  # type: ignore[union-attr]

    out: Dict[str, str] = {}

    def add(name: str, value: object, text: str) -> None:
        if value is not None:
            out[name] = text

    add("registers", get("package", "domain_count"),
        f"{get('package', 'domain_count')} registers")
    add("query_kinds", get("package", "query_kind_count"),
        f"{get('package', 'query_kind_count')} query kinds")
    add("report_subjects", get("package", "report_subject_count"),
        f"{get('package', 'report_subject_count')} report subjects")
    add("evaluation_cases", get("evaluation", "cases"),
        f"{get('evaluation', 'cases')} CLI cases")
    add("test_files", get("tests", "test_files"),
        f"{get('tests', 'test_files')} test files")
    add("lean_files", get("lean", "files"),
        f"{get('lean', 'files')} Lean files")
    if get("suite", "tests") is not None:
        #  "M of the T test files" and "outside the document check" are part
        #  of the sentence, not a gloss on it: the totals are measured over
        #  the suite minus ``tests/test_figures.py``, and a reader comparing
        #  this row's file count against the ``test_files`` row would
        #  otherwise find them one apart with nothing to say why.  Naming the
        #  whole suite inside the sentence also keeps the two rows agreeing
        #  rather than competing: the ``test_files`` shape finds *its* figure
        #  here too, and finds it current.
        out["suite"] = (f"{_thousands(get('suite', 'tests'))} tests across "
                        f"{get('suite', 'test_files')} of the "
                        f"{get('suite', 'of_test_files')} test files, "
                        f"{_thousands(get('suite', 'subtests'))} subtests, "
                        f"outside the document check")
    return out


def _row(name: str, value: object) -> str:
    if isinstance(value, (tuple, list)):
        rendered = ", ".join(str(v) for v in value) or "(none)"
    elif isinstance(value, dict):
        rendered = ", ".join(f"{k} {v}" for k, v in value.items()) or "(none)"
    elif isinstance(value, Fraction):
        rendered = f"{value.numerator}/{value.denominator}"
    else:
        rendered = str(value)
    if len(rendered) > 1000:
        rendered = rendered[:997] + "..."
    return f"| `{name}` | {rendered} |"


_SECTION_TITLES: Tuple[Tuple[str, str], ...] = (
    ("package", "Package surface"),
    ("registers", "Registers"),
    ("chemistry", "Chemistry: the element register and its coverage"),
    ("molecules", "Chemistry: the molecules register"),
    ("semantics", "Meaning"),
    ("capabilities", "Capability probes"),
    ("evaluation", "End-to-end evaluation set"),
    ("benchmarks", "Benchmarks"),
    ("lean", "The Lean development"),
    ("tests", "The test suite"),
    ("suite", "What a complete run counted"),
)


def _headline(data: Mapping[str, object]) -> List[str]:
    """The at-a-glance paragraph, in the exact wording the READMEs use.

    The point of repeating the counts in prose is that the phrases here are
    the phrases ``tests/test_figures.py`` looks for in the documentation, so
    a reader can copy a sentence out of this file and be sure it is current.
    """
    def get(section: str, key: str) -> object:
        block = data.get(section) or {}
        return block.get(key)  # type: ignore[union-attr]

    parts: List[str] = []
    if get("package", "domain_count") is not None:
        parts.append(
            f"**{get('package', 'domain_count')} registers** holding "
            f"{get('registers', 'total_carriers')} carriers, reached through "
            f"**{get('package', 'query_kind_count')} query kinds** of which "
            f"one dispatches **{get('package', 'report_subject_count')} "
            f"report subjects**")
    if get("chemistry", "elements") is not None:
        parts.append(f"**{get('chemistry', 'elements')} elements** and "
                     f"**{get('molecules', 'molecules')} molecules**")
    if get("semantics", "meanings") is not None:
        parts.append(f"**{get('semantics', 'meanings')} meanings** in the "
                     f"lexicon")
    if get("capabilities", "probes") is not None:
        parts.append(f"**{get('capabilities', 'probes')} probes** of which "
                     f"{get('capabilities', 'holds')} hold and "
                     f"{get('capabilities', 'breaks')} break")
    if get("evaluation", "cases") is not None:
        parts.append(f"**{get('evaluation', 'cases')} cases** end to end")
    if get("tests", "test_files") is not None:
        parts.append(f"**{get('tests', 'test_files')} test files**")
    if get("lean", "files") is not None:
        parts.append(f"**{get('lean', 'files')} Lean files** carrying "
                     f"{get('lean', 'sorries')} sorries")
    if not parts:
        return []
    return ["## At a glance", "", "; ".join(parts) + ".", ""]


def _sentences_section(data: Mapping[str, object]) -> List[str]:
    """The prose fragments, and the shape each one is guarded against."""
    generated = sentences(data)
    if not generated:
        return []
    patterns = {name: pattern for name, pattern, _ in SENTENCE_PATTERNS}
    what = {name: description for name, _, description in SENTENCE_PATTERNS}
    out = [
        "## Sentences",
        "",
        "Quote these verbatim.  `tests/test_figures.py` finds every phrase "
        "of the shape in the third column in the documentation and requires "
        "it to be the sentence in the second, so a superseded phrasing fails "
        "the suite without anyone having to list it.",
        "",
        "| name | sentence | shape | counts |",
        "|---|---|---|---|",
    ]
    for name in sorted(generated):
        pattern = patterns.get(name, "")
        out.append(f"| `{name}` | {generated[name]} | "
                   f"`{pattern}` | {what.get(name, '')} |")
    out.append("")
    return out


def render_markdown(data: Optional[Mapping[str, object]] = None) -> str:
    """``FIGURES.md``, rendered from a computation of the figures."""
    data = data if data is not None else figures()
    out: List[str] = [
        "# Figures",
        "",
        "**Every number the documentation quotes, recomputed by the code "
        "that reports it.**",
        "",
        "This file is generated.  Do not edit it by hand -- run",
        "",
        "```",
        "python -m glm_universal.figures --write",
        "```",
        "",
        "from the directory holding `glm_universal/`, and commit the result "
        "alongside whatever changed.  `tests/test_figures.py` compares this "
        "file against a fresh computation, so a stale figure fails the "
        "suite rather than reaching a reader.",
        "",
        "Two rows are measured from outside the package and are marked as "
        "such: the collected test count needs `pytest` to walk the suite "
        "(`--with-tests`), and the Lean counts are read off the repository "
        "tree.",
        "",
    ]
    out.extend(_headline(data))
    out.extend(_sentences_section(data))
    for key, title in _SECTION_TITLES:
        section = data.get(key)
        if not section:
            continue
        out.append(f"## {title}")
        out.append("")
        out.append("| figure | value |")
        out.append("|---|---|")
        for name, value in section.items():  # type: ignore[union-attr]
            out.append(_row(name, value))
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def figures_path() -> str:
    """Where ``FIGURES.md`` lives: beside the package."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(here), "FIGURES.md")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m glm_universal.figures",
        description="Recompute every figure the documentation quotes.")
    parser.add_argument("--write", action="store_true",
                        help="rewrite FIGURES.md in place")
    parser.add_argument("--check", action="store_true",
                        help="compare FIGURES.md with a fresh computation "
                             "and exit 1 if they differ")
    parser.add_argument("--json", action="store_true",
                        help="emit JSON instead of Markdown")
    parser.add_argument("--with-tests", action="store_true",
                        help="also collect the test count (runs pytest)")
    parser.add_argument("--lean-root", default=None,
                        help="directory holding RequestProject/")
    args = parser.parse_args(argv)

    # The written file carries the collected test count, because that is one
    # of the figures the documentation quotes most often.
    with_tests = args.with_tests or args.write or args.check
    data = figures(with_tests=with_tests, lean_root=args.lean_root)
    if args.json:
        print(json.dumps(data, indent=2, default=str, sort_keys=True))
        return 0
    text = render_markdown(data)
    if args.check:
        path = figures_path()
        with open(path, encoding="utf-8") as handle:
            stored = handle.read()
        if stored == text:
            print(f"{path} matches a fresh computation")
            return 0
        print(f"{path} is stale; run --write")
        for line in difflib.unified_diff(stored.splitlines(),
                                         text.splitlines(),
                                         "stored", "computed", lineterm=""):
            print(line)
        return 1
    if args.write:
        path = figures_path()
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
        print(f"wrote {path}")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
