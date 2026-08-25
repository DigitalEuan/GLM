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

Everything else is exact and deterministic: no float is constructed, nothing
is sampled, and two runs on the same tree give the same table.
"""

from __future__ import annotations

import argparse
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
    "figures",
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
    }


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
    parser.add_argument("--json", action="store_true",
                        help="emit JSON instead of Markdown")
    parser.add_argument("--with-tests", action="store_true",
                        help="also collect the test count (runs pytest)")
    parser.add_argument("--lean-root", default=None,
                        help="directory holding RequestProject/")
    args = parser.parse_args(argv)

    # The written file carries the collected test count, because that is one
    # of the figures the documentation quotes most often.
    with_tests = args.with_tests or args.write
    data = figures(with_tests=with_tests, lean_root=args.lean_root)
    if args.json:
        print(json.dumps(data, indent=2, default=str, sort_keys=True))
        return 0
    text = render_markdown(data)
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
