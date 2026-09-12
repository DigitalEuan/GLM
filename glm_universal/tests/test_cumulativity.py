"""Tests for ``reasoning/cumulativity`` -- the refinement check a layer ships with.

``studies/CUMULATIVITY_STUDY.md`` turns the inspection the information-loss
round ran by hand into directive D12: a layer family ships only if every
declared refinement edge holds on its probe set and every declared non-edge has
a witness.  These tests pin the parts of that machinery that have to be *right*
rather than merely reported:

* the **check has teeth** -- a family whose declared edge is false is reported
  as defective, so a passing board is evidence and not a tautology;
* the **shape is declared, never inferred** -- an unknown rung is refused, and
  a declared non-edge with no witness is a defect of the declaration rather
  than of the layer;
* the **two failure modes stay apart** -- a conflation is counted and reported
  beside the edges and never as a defect, which is what
  `GLM.Info.Layer.factored_conflates` and `join_separates` say in general:
  refining a reading of a view cannot repair what the view conflates, and a
  join with a reading that sees the pair can;
* the **rejected reading stays priced** -- the integer layer read without the
  substrate's bits is registered with its non-edge, is witnessed, and does not
  ship;
* the **totals the study quotes** -- three families, two shipped, seven edges,
  two non-edges, no defect in a shipped family;
* the **exactness** of the module, by the static instrument of directive D7.

Everything here is recomputed: the module is cheap enough to run on every test
pass, so nothing is read from a cache.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.reasoning import cumulativity as cml
from glm_universal.reasoning import exactness as ex
from glm_universal.reasoning import pipeline as ppl
from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import GeometricSession


@pytest.fixture(scope="module")
def report():
    return cml.cumulativity_report()


# ---------------------------------------------------------------------------
#  1.  The check has teeth
# ---------------------------------------------------------------------------

def _parity_family(edges, non_edges=()):
    """A tiny declared family over the integers 0..5.

    ``fine`` tells every probe apart, ``parity`` sees only the parity, so
    ``parity`` does *not* refine ``fine`` and ``fine`` does refine ``parity``.
    """
    return cml.Family(
        key="test-parity",
        title="a two-rung family with a known shape",
        rungs=(
            cml.Rung(name="parity", title="the parity alone",
                     same=lambda a, b: (a % 2) == (b % 2)),
            cml.Rung(name="fine", title="the value",
                     same=lambda a, b: a == b),
        ),
        probes=lambda: (0, 1, 2, 3, 4, 5),
        edges=edges,
        non_edges=non_edges,
    )


def test_a_declared_edge_that_is_false_is_reported_as_a_defect():
    broken = _parity_family(edges=(("fine", "parity"),))
    row = cml.check_family(broken)
    assert row["passes"] is False
    assert row["defects"]
    edge = row["edges"][0]
    assert edge["refines"] is False
    # every violating pair is listed, not merely counted
    assert len(edge["violations"]) == len(tuple(
        (i, j) for i in range(6) for j in range(i + 1, 6) if i % 2 == j % 2))


def test_a_declared_edge_that_holds_passes_and_lists_no_violation():
    sound = _parity_family(edges=(("parity", "fine"),))
    row = cml.check_family(sound)
    assert row["passes"] is True
    assert row["edges"][0]["violations"] == ()
    assert row["edges"][0]["pairs"] == 15


def test_a_declared_non_edge_without_a_witness_is_a_defect_of_the_declaration():
    overclaimed = _parity_family(edges=(), non_edges=(("parity", "fine"),))
    row = cml.check_family(overclaimed)
    assert row["non_edges"][0]["witnessed"] is False
    assert row["passes"] is False
    assert "no witness" in row["defects"][0]


def test_a_witnessed_non_edge_names_the_pair_that_witnesses_it():
    denied = _parity_family(edges=(), non_edges=(("fine", "parity"),))
    row = cml.check_family(denied)
    witness = row["non_edges"][0]
    assert witness["witnessed"] is True
    left, right = witness["witness"]
    assert left != right


def test_a_rung_that_was_never_declared_is_refused_rather_than_guessed():
    family = _parity_family(edges=())
    with pytest.raises(KeyError):
        cml.check_edge(family, "parity", "not a rung")
    with pytest.raises(KeyError):
        cml.conflations(family, "not a rung")
    with pytest.raises(KeyError):
        cml.family_by_key("no such family")


# ---------------------------------------------------------------------------
#  2.  A conflation is not a defect
# ---------------------------------------------------------------------------

def test_a_conflation_is_counted_and_is_not_a_defect():
    sound = _parity_family(edges=(("parity", "fine"),))
    losses = cml.conflations(sound, "parity")
    assert losses["count"] == 6           # two parity classes of three
    assert len(losses["pairs"]) == losses["count"]
    assert "joint reading" in str(losses["remedy"])
    assert cml.check_family(sound)["passes"] is True


def test_the_finest_rung_of_a_family_conflates_nothing():
    sound = _parity_family(edges=(("parity", "fine"),))
    assert cml.conflations(sound, "fine")["count"] == 0


# ---------------------------------------------------------------------------
#  3.  The declared families
# ---------------------------------------------------------------------------

def test_the_three_declared_families_are_the_ones_the_study_names(report):
    assert [row["key"] for row in report["families"]] == [
        "dimension-stack", "dimension-stack-rejected", "deep-hole-ladder"]
    assert report["count"] == 3
    assert report["shipped"] == 2


def test_every_shipped_family_passes_its_own_check(report):
    for row in report["families"]:
        if row["shipped"]:
            assert row["defects"] == (), row["key"]
    assert report["defects"] == ()
    assert report["holds"] is True
    assert cml.rule_holds() is True
    assert cml.shipped_defects() == ()


def test_the_board_checks_the_edges_and_non_edges_the_study_quotes(report):
    assert report["edges_checked"] == 7
    assert report["non_edges_checked"] == 2
    for row in report["families"]:
        for edge in row["edges"]:
            assert edge["refines"] is True, (row["key"], edge)
        for non_edge in row["non_edges"]:
            assert non_edge["witnessed"] is True, (row["key"], non_edge)


def test_the_dimension_stack_is_the_shipped_chain_of_five_readings():
    family = cml.family_by_key("dimension-stack")
    assert family.shipped is True
    assert family.rungs[0].name == "substrate"
    assert [rung.name for rung in family.rungs] == [
        "substrate", "integer", "rational", "griess", "universal"]
    assert family.edges == (("substrate", "integer"), ("integer", "rational"),
                            ("rational", "griess"), ("griess", "universal"))


def test_the_rejected_integer_reading_is_kept_and_does_not_ship():
    family = cml.family_by_key("dimension-stack-rejected")
    assert family.shipped is False
    assert family.edges == ()
    assert family.non_edges == (("substrate", "integer_raw"),)
    row = cml.check_family(family)
    assert row["passes"] is True          # the declaration is honest
    assert row["non_edges"][0]["witnessed"] is True


def test_the_repair_of_the_rejected_reading_is_the_shipped_one():
    """The shipped integer layer refines the substrate; the raw one does not."""
    shipped = cml.check_edge(cml.family_by_key("dimension-stack"),
                             "substrate", "integer")
    assert shipped["refines"] is True
    rejected = cml.check_edge(cml.family_by_key("dimension-stack-rejected"),
                              "substrate", "integer_raw")
    assert rejected["refines"] is False


# ---------------------------------------------------------------------------
#  4.  The deep-hole ladder is a graph, not a chain
# ---------------------------------------------------------------------------

def test_the_ladder_declares_the_join_above_both_of_its_parts():
    family = cml.family_by_key("deep-hole-ladder")
    assert ("widened", "joint") in family.edges
    assert ("rational", "joint") in family.edges
    assert ("shares", "rational") in family.non_edges


def test_the_exact_rung_does_not_refine_the_share_rung_and_the_join_repairs_it():
    family = cml.family_by_key("deep-hole-ladder")
    denied = cml.check_non_edge(family, "shares", "rational")
    assert denied["witnessed"] is True
    left, right = denied["witness"]
    assert {left, right} == {"shares 2:1, no stray", "shares 1:1:1, no stray"}
    # the join sees the pair the exact rung conflates
    probes = list(family.probes())
    names = list(family.probe_names())
    i, j = names.index(left), names.index(right)
    rungs = {rung.name: rung for rung in family.rungs}
    assert rungs["rational"].same(probes[i], probes[j]) is True
    assert rungs["joint"].same(probes[i], probes[j]) is False


def test_where_the_metrics_are_commensurable_the_higher_one_dominates():
    family = cml.family_by_key("deep-hole-ladder")
    for lower, higher in family.edges:
        row = cml.check_edge(family, lower, higher)
        assert row["metrics_comparable"] is True
        assert row["metric_dominates"] is True


def test_the_ladders_distances_are_exact_rationals():
    family = cml.family_by_key("deep-hole-ladder")
    probes = list(family.probes())
    for rung in family.rungs:
        value = rung.metric(probes[0], probes[2])
        assert isinstance(value, (int, Fraction))
        assert not isinstance(value, float)


# ---------------------------------------------------------------------------
#  5.  The report, the runtime and the record
# ---------------------------------------------------------------------------

def test_the_report_states_the_rule_it_enforces(report):
    text = str(report["rule"])
    assert "every declared refinement edge" in text
    assert "conflation" in text


def test_the_subject_answers_with_the_recomputed_board():
    session = GeometricSession()
    solution = session.ask("report cumulativity")
    assert solution.kind == "report"
    assert solution.expected["families"] == "3"
    assert solution.expected["shipped"] == "2"
    assert solution.expected["edges_checked"] == "7"
    assert solution.expected["non_edges_checked"] == "2"
    assert solution.expected["holds"] == "True"


def test_column_three_renders_for_the_subject():
    session = GeometricSession()
    script = tct.render_script(session.ask("report cumulativity"))
    assert "cumulativity" in script


def test_the_pipeline_row_names_the_study_the_subject_and_the_lean_file():
    row = next(r for r in ppl.REGISTRY if r.key == "cumulativity")
    assert row.document == "CUMULATIVITY_STUDY.md"
    assert row.subject == "cumulativity"
    assert "CumulativityRule.lean" in row.lean


def test_the_module_holds_no_float(report):
    path = Path(cml.__file__)
    assert ex.module_float_sites(path) == {}


def test_the_two_copies_of_the_lean_file_agree():
    here = Path(cml.__file__).resolve().parents[2]
    mirror = here / "glm_lean" / "RequestProject" / "GLM" / \
        "CumulativityRule.lean"
    original = here.parent / "RequestProject" / "GLM" / "CumulativityRule.lean"
    assert mirror.is_file()
    text = mirror.read_text(encoding="utf-8")
    for name in ("factored_conflates", "join_separates",
                 "join_needs_a_second_reading", "refines_of_le",
                 "refinementChain_cumulativeTower"):
        assert name in text
    assert "sorry" not in text
    if original.is_file():
        assert original.read_text(encoding="utf-8") == text
