"""Tests for ``reasoning/product.fusion_report`` and its runtime wiring.

The adjoint action of a ``2A`` axis, the Ising eigenspaces it decomposes its
subalgebra into, and the two Miyamoto involutions built out of them were all
implemented in ``reasoning/product.py`` but could not be reached from a
query.  ``fusion_report`` collects them, and ``report fusion`` asks for it.

These tests pin the mathematics (eigenvalues found rather than assumed,
``tau`` derived to be the identity, ``sigma`` computed to be the transposition
of the other two axes, both maps automorphisms and isometries), the exactness
(every entry a rational), and the query end to end including the Three Column
Thinking script that reproduces column 2 in a fresh interpreter.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from glm_universal.reasoning import product as PR
from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import REPORT_SUBJECTS, GeometricSession


@pytest.fixture(scope="module")
def report():
    return PR.fusion_report()


@pytest.fixture(scope="module")
def subalgebra():
    u, v = PR.sample_two_a_pairs(1)[0]
    return PR.two_a_subalgebra(u, v)


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


# ===========================================================================
# 1.  THE ADJOINT ACTION
# ===========================================================================

class TestAdjointAction:

    def test_every_entry_is_a_rational(self, subalgebra):
        for label in subalgebra.labels:
            for row in PR.adjoint_matrix(label, subalgebra):
                for entry in row:
                    assert isinstance(entry, Fraction)

    def test_the_adjoint_reproduces_the_product(self, subalgebra):
        for label in subalgebra.labels:
            matrix = PR.adjoint_matrix(label, subalgebra)
            for other in subalgebra.labels:
                lhs = PR.apply_map(matrix, PR.axis(other), subalgebra)
                rhs = PR.algebra_product(PR.axis(label), PR.axis(other))
                assert lhs == rhs

    def test_the_trace_is_the_sum_of_the_ising_eigenvalues(self, subalgebra):
        for label in subalgebra.labels:
            matrix = PR.adjoint_matrix(label, subalgebra)
            trace = sum((matrix[i][i] for i in range(3)), Fraction(0))
            assert trace == Fraction(1) + Fraction(0) + Fraction(1, 4)

    def test_an_axis_is_idempotent_so_it_is_its_own_eigenvector(self,
                                                               subalgebra):
        for label in subalgebra.labels:
            a = PR.axis(label)
            assert PR.algebra_product(a, a) == a


# ===========================================================================
# 2.  THE FUSION SPECTRUM
# ===========================================================================

class TestFusionSpectrum:

    def test_the_eigenvalues_searched_for_are_the_ising_ones(self):
        assert PR.ISING_EIGENVALUES == (Fraction(1), Fraction(0),
                                        Fraction(1, 4), Fraction(1, 32))

    def test_each_reported_vector_really_is_an_eigenvector(self, subalgebra):
        for label in subalgebra.labels:
            spectrum = PR.fusion_spectrum(label, subalgebra)
            for lam, basis in spectrum.items():
                for coords in basis:
                    x = subalgebra.element(coords)
                    assert PR.algebra_product(PR.axis(label), x) \
                        == x.scale(lam)

    def test_the_twisted_part_is_empty_and_the_rest_spans(self, subalgebra):
        for label in subalgebra.labels:
            spectrum = PR.fusion_spectrum(label, subalgebra)
            dims = {lam: len(basis) for lam, basis in spectrum.items()}
            assert dims[Fraction(1, 32)] == 0
            assert sum(dims.values()) == 3


# ===========================================================================
# 3.  THE REPORT
# ===========================================================================

class TestFusionReport:

    def test_it_checks_more_than_one_subalgebra(self, report):
        assert report["pairs_checked"] >= 3
        assert report["axes_checked"] == 3 * report["pairs_checked"]

    def test_every_summary_flag_holds(self, report):
        for key in ("all_eigenspaces_span", "all_dimensions_as_predicted",
                    "all_adjoint_traces_five_quarters", "tau_always_identity",
                    "sigma_always_swaps", "all_automorphisms",
                    "all_isometries", "all_involutions"):
            assert report[key] is True, key

    def test_the_predicted_dimensions_are_one_one_one_zero(self, report):
        assert report["expected_eigenspace_dimensions"] == {
            "1": 1, "0": 1, "1/4": 1, "1/32": 0}

    def test_every_axis_record_carries_its_own_evidence(self, report):
        for record in report["records"]:
            assert len(record["labels"]) == 3
            assert len(record["axes"]) == 3
            for entry in record["axes"]:
                assert entry["adjoint_trace"] == "5/4"
                assert entry["tau_is_identity"]
                assert entry["sigma_is_involution"]
                assert entry["sigma_fixes_its_axis"]
                assert entry["sigma_swaps_the_others"]
                assert None not in entry["sigma_permutation"]

    def test_sigma_is_a_transposition_of_the_labels(self, report):
        for record in report["records"]:
            labels = list(record["labels"])
            for entry in record["axes"]:
                perm = list(entry["sigma_permutation"])
                assert sorted(perm) == sorted(labels)
                moved = [l for l, p in zip(labels, perm) if l != p]
                assert len(moved) == 2

    def test_the_matrices_are_rendered_as_exact_fractions(self, report):
        for record in report["records"]:
            for entry in record["axes"]:
                for matrix in (entry["adjoint"], entry["sigma"]):
                    for row in matrix:
                        for cell in row:
                            assert "/" in cell
                            Fraction(cell)          # parses exactly
                            assert "." not in cell

    def test_the_report_is_reproducible_within_the_run(self):
        assert PR.fusion_report() == PR.fusion_report()

    def test_a_caller_may_choose_the_pairs(self):
        pairs = PR.sample_two_a_pairs(2)
        chosen = PR.fusion_report(pairs)
        assert chosen["pairs_checked"] == 2
        assert chosen["axes_checked"] == 6
        assert chosen["all_automorphisms"] is True


# ===========================================================================
# 4.  RUNTIME WIRING -- `report fusion`
# ===========================================================================

class TestReportFusionQuery:

    def test_the_subject_is_advertised(self):
        assert "fusion" in REPORT_SUBJECTS

    def test_the_query_is_answered(self, sess):
        sol = sess.ask("report fusion")
        assert sol.ok
        assert sol.kind == "report"

    def test_the_aliases_all_reach_the_same_solver(self, sess):
        answers = {sess.ask(f"report {alias}").answer
                   for alias in ("fusion", "miyamoto", "ising",
                                 "eigenspaces", "adjoint")}
        assert len(answers) == 1

    def test_the_expected_values_are_the_computed_ones(self, sess):
        sol = sess.ask("report fusion")
        assert sol.expected["pairs_checked"] == "3"
        assert sol.expected["axes_checked"] == "9"
        for key in ("all_eigenspaces_span", "all_dimensions_as_predicted",
                    "all_adjoint_traces_five_quarters", "tau_always_identity",
                    "sigma_always_swaps", "all_automorphisms",
                    "all_isometries", "all_involutions"):
            assert sol.expected[key] == "True", key

    def test_the_four_steps_are_present(self, sess):
        sol = sess.ask("report fusion")
        assert len(sol.steps) == 4

    def test_the_subject_list_mentions_the_new_subject(self, sess):
        sol = sess.ask("report nonsense subject")
        assert not sol.ok
        assert "fusion" in sol.answer

    def test_the_generated_script_is_exact(self, sess):
        sol = sess.ask("report fusion")
        ok, offenders = tct.script_is_exact(tct.render_script(sol))
        assert ok, offenders

    def test_the_generated_script_reproduces_column_two(self, sess):
        sol = sess.ask("report fusion")
        trace = tct.verify_trace(tct.build_trace(sol))
        assert trace.verdict is not None
        assert trace.verdict.executed
        assert trace.verdict.returncode == 0
        assert trace.verdict.matches_column2
        assert trace.verdict.mismatches == ()
        assert trace.verdict.missing_keys == ()
