"""Tests for role--filler binding: what a bound relation gives back.

What is pinned here is the *mechanism* and the discipline rather than the
score.  The parity binding must invert with no side condition at all, on real
carriers and not on a fixture; the role tag must be a permutation of the
coordinates and must act on a reading exactly as it acts on the carrier the
reading came from; recovering a **name** must refuse whenever the register's
parity reading does not separate the filler from everything else; and the
product binding must be shown to fail where the supplied material says it
succeeds.

The machine-checked counterparts are in ``RequestProject/GLM/RoleBinding.lean``
-- ``unbind_bind``, ``bind_injective_right``, ``bind_eq_iff_role_agrees``,
``hbind_not_injective_of_zero``, ``recover_ok_iff``,
``two_names_one_reading_is_ambiguous`` and
``recover_bind_independent_of_role``.  Directive D7 -- no float anywhere -- is
checked statically.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from glm_universal.reasoning import dimension_layers as dl
from glm_universal.reasoning import exactness as ex
from glm_universal.reasoning import role_binding as RB
from glm_universal.runtime.session import GeometricSession
from glm_universal.substrate import permute_vector

LEAN = (Path(__file__).resolve().parents[3]
        / "RequestProject" / "GLM" / "RoleBinding.lean")


@pytest.fixture(scope="module")
def session():
    return GeometricSession()


@pytest.fixture(scope="module")
def report(session):
    return RB.binding_report(session)


def _sample(session, domain, count=8):
    return tuple(obj for obj in session.register(domain))[:count]


class TestTheRoleTags:

    def test_every_role_is_a_permutation_of_the_coordinates(self, subtests):
        for name, perm in RB.ROLES.items():
            with subtests.test(role=name):
                assert sorted(perm) == list(range(RB.DIM))

    def test_the_roles_are_distinct(self):
        assert len(set(RB.ROLES.values())) == len(RB.ROLES)

    def test_equals_is_the_identity(self):
        assert RB.ROLES["equals"] == tuple(range(RB.DIM))

    def test_a_role_acts_on_a_reading_as_it_acts_on_the_carrier(
            self, session, subtests):
        """``permute_mask`` and the substrate's ``permute_vector`` agree."""
        for obj in _sample(session, "chemistry"):
            for role, perm in RB.ROLES.items():
                with subtests.test(name=obj.name, role=role):
                    moved = permute_vector(tuple(obj.carrier), perm)
                    assert (RB.permute_mask(RB.parity(obj.carrier), perm)
                            == dl.parity_bits(moved))

    def test_an_undeclared_role_is_refused(self):
        with pytest.raises(RB.BindingError) as caught:
            RB.key_mask("rhymes_with", 0)
        assert caught.value.reason == "unknown-role"


class TestTheParityBindingInverts:

    def test_unbind_undoes_bind_on_every_pair_of_a_sample(
            self, session, subtests):
        """``GLM.RoleBinding.unbind_bind``, on the real register."""
        carriers = _sample(session, "chemistry", 6)
        for role in RB.ROLES:
            for left in carriers:
                for right in carriers:
                    with subtests.test(role=role, a=left.name, b=right.name):
                        a, b = RB.parity(left.carrier), RB.parity(
                            right.carrier)
                        assert RB.unbind(role, a, RB.bind(role, a, b)) == b

    def test_binding_is_injective_in_the_filler(self, session):
        """``GLM.RoleBinding.bind_injective_right``."""
        masks = {RB.parity(obj.carrier) for obj in _sample(session,
                                                           "harmonics", 12)}
        a = next(iter(masks))
        bound = {RB.bind("causes", a, b) for b in masks}
        assert len(bound) == len(masks)

    def test_the_bound_word_is_twenty_four_bits(self, session):
        for obj in _sample(session, "chemistry", 4):
            mask = RB.parity(obj.carrier)
            assert 0 <= RB.bind("part_of", mask, mask) < (1 << RB.DIM)

    def test_two_roles_agreeing_on_the_known_side_bind_alike(self):
        """``GLM.RoleBinding.roles_differ_but_bind_alike``: a reading fixed by
        both permutations cannot tell them apart."""
        assert RB.bind("causes", 0, 5) == RB.bind("part_of", 0, 5)


class TestFromAReadingToAName:

    def test_the_declared_set_comes_out_as_declared(self, report, subtests):
        for row in report["rows"]:
            with subtests.test(binding=row["key"]):
                assert row["outcome"] == row["expected"], row["detail"]
        assert report["as_declared"] == report["declared"]

    def test_every_refusal_carries_a_declared_reason(self, report):
        for reason in report["refusal_reasons"]:
            assert reason in RB.REFUSAL_REASONS

    def test_a_unique_reading_recovers_its_name(self, session):
        bound = RB.bind_names(session, "causes", "C", "O", "chemistry")
        assert RB.recover(session, bound.word, "causes", "C",
                          "chemistry") == "O"

    def test_a_shared_reading_refuses_and_names_the_candidates(self, session):
        """``GLM.RoleBinding.two_names_one_reading_is_ambiguous``: barium and
        lead read alike, so the word that binds one names both."""
        bound = RB.bind_names(session, "causes", "C", "Ba", "chemistry")
        with pytest.raises(RB.BindingError) as caught:
            RB.recover(session, bound.word, "causes", "C", "chemistry")
        assert caught.value.reason == "ambiguous-recovery"
        assert set(caught.value.candidates) == {"Ba", "Pb"}

    def test_the_recovery_does_not_depend_on_the_role_or_the_known_side(
            self, session, subtests):
        """``GLM.RoleBinding.recover_bind_independent_of_role``."""
        for role in ("causes", "derived_from", "mentioned_after"):
            for known in ("C", "O", "H"):
                with subtests.test(role=role, a=known):
                    bound = RB.bind_names(session, role, known, "Ne",
                                          "chemistry")
                    assert RB.recover(session, bound.word, role, known,
                                      "chemistry") == "Ne"

    def test_a_name_the_register_does_not_hold_is_refused(self, session):
        with pytest.raises(RB.BindingError) as caught:
            RB.bind_names(session, "causes", "C", "phlogiston", "chemistry")
        assert caught.value.reason == "unknown-name"


class TestTheCensuses:

    def test_the_fibre_census_accounts_for_every_carrier(self, report):
        fibres = report["fibres"]
        assert fibres["recoverable"] + fibres["ambiguous"] == fibres[
            "carriers"]
        assert sum(row["carriers"] for row in fibres["rows"]) == fibres[
            "carriers"]

    def test_a_carrier_is_nameable_exactly_when_its_reading_is_its_own(
            self, session, subtests):
        from collections import Counter
        fibres = RB.register_census(session)
        for row in fibres["rows"]:
            with subtests.test(domain=row["domain"]):
                masks = [RB.parity(obj.carrier)
                         for obj in session.register(row["domain"])]
                counts = Counter(masks)
                assert row["recoverable"] == sum(1 for mask in masks
                                                 if counts[mask] == 1)
                assert row["readings"] == len(counts)

    def test_the_nearest_mask_control_is_right_once_per_reading(self, report):
        fibres = report["fibres"]
        assert fibres["control_right"] == fibres["readings"]
        assert (fibres["control_right"] + fibres["control_wrong"]
                == fibres["carriers"])

    def test_the_product_binding_needs_a_key_that_reads_nowhere_zero(
            self, report):
        """``GLM.RoleBinding.hbind_not_injective_of_zero``: one zero
        coordinate and two fillers bind alike."""
        product = report["product"]
        assert (product["recoverable"] + product["with_zero_coordinate"]
                == product["carriers"])
        assert product["recoverable"] < product["carriers"] // 100

    def test_the_keys_the_product_binding_leaves_are_not_distinct_carriers(
            self, report):
        product = report["product"]
        assert product["distinct_keys"] < product["recoverable"]


class TestTheDiscipline:

    def test_no_float_is_constructed(self):
        assert ex.module_float_sites(Path(RB.__file__)) == {}

    def test_the_lean_file_names_what_the_module_cites(self, subtests):
        text = LEAN.read_text(encoding="utf-8")
        for theorem in ("unbind_bind", "bind_injective_right",
                        "bind_eq_iff_role_agrees",
                        "roles_differ_but_bind_alike",
                        "hbind_not_injective_of_zero", "recover_ok_iff",
                        "recover_sound", "recover_bind_of_unique",
                        "recover_bind_independent_of_role",
                        "two_names_one_reading_is_ambiguous",
                        "nearest_names_the_wrong_carrier"):
            with subtests.test(theorem=theorem):
                assert f"theorem {theorem}" in text

    def test_the_lean_file_has_no_sorry(self):
        assert "sorry" not in LEAN.read_text(encoding="utf-8")
