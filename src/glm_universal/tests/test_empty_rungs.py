"""Tests for ``reasoning/empty_rungs`` -- Construction A rungs for the two
empty norms of the power-of-two family (Phase 123, part C).

``studies/LATTICE_COMPLETION_STUDY.md`` §2.C names five candidates and a
declared rule for trying them.  These tests pin:

* the **candidates' facts** -- minimum norm and kissing number of every
  candidate, enumerated from its definition, agree with the declared table,
  and the norm is the ``min 4 d`` of `GLM.LatticeCompletion.constructionA_normSq_ge`
  (times ``64`` for the scaled ones);
* the **quantisers** answer inside the rung and no minimal step is nearer;
* the **declared order** is norm 2 first, then norm 256, densest first;
* the stored **filling** and the final ladder's audit, read from the cache,
  which must describe the sources it was taken from (D4).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from glm_universal.reasoning import empty_rungs as er
from glm_universal.reasoning import exactness as ex


def test_the_declared_order_is_norm_two_then_norm_256_densest_first():
    assert [norm for norm, _keys in er.CANDIDATE_ORDER] == [2, 256]
    for norm, keys in er.CANDIDATE_ORDER:
        assert all(er.CANDIDATES[k]["norm"] == norm for k in keys)
        kissing = [er.CANDIDATES[k]["kissing"] for k in keys]
        assert kissing == sorted(kissing, reverse=True)
    assert {k for _n, keys in er.CANDIDATE_ORDER for k in keys} == set(
        er.CANDIDATES)


def test_the_repaired_ladder_has_no_rung_at_norm_two_or_256():
    norms = {er.rung_norm(r) for r in er.REPAIRED}
    assert 2 not in norms and 256 not in norms


@pytest.mark.parametrize("key", ["D12^2", "D8^3", "D4^6"])
def test_the_norm_two_candidates_have_the_declared_facts(key):
    facts = er.short_vectors(key)
    assert facts["agrees"] is True
    assert facts["minimum_norm"] == 2 == min(4, 2)   # min 4 d, d = 2


def test_the_scaled_hamming_and_repetition_candidates_reach_norm_256():
    for key in ("8E8^3", "8D4^6"):
        facts = er.short_vectors(key)
        assert facts["agrees"] is True
        assert facts["block_minimum"] == min(4, 4)    # d = 4
        assert facts["minimum_norm"] == 4 * 64 == 256


def test_membership_follows_the_definition():
    assert er.in_rung((1, 1) + (0,) * 22, "D4^6")
    assert not er.in_rung((1,) + (0,) * 23, "D4^6")
    assert er.in_rung((8, 8, 8, 8) + (0,) * 20, "8D4^6")
    assert not er.in_rung((8, 8) + (0,) * 22, "8D4^6")
    assert not er.in_rung((4, 4, 4, 4) + (0,) * 20, "8D4^6")


def test_the_quantiser_answers_inside_the_rung_with_no_nearer_step():
    for key in er.CANDIDATES:
        check = er.quantiser_check(key, vectors=20)
        assert check["holds"] is True, key


@pytest.fixture(scope="module")
def stored():
    data = er.current()
    assert data is not None, (
        "the measurement cache is absent or stale; re-take it with "
        "python3 -m glm_universal.tools empty-rungs --write")
    return data


def test_the_stored_round_reproduces_the_repaired_ladder(stored):
    assert stored["reproduces"] is True
    rep = stored["repaired"]
    assert (rep["correct"], rep["wrong"], rep["refused"]) == (467, 0, 101)


def test_the_candidate_facts_hold(stored):
    assert all(row["holds"] for row in stored["facts"])
    assert stored["marks"]["C1"] is True


def test_the_filling_follows_the_declared_rule(stored):
    filling = stored["filling"]
    tried = [t["candidate"] for t in filling["trials"]]
    order = [k for _n, keys in er.CANDIDATE_ORDER for k in keys]
    assert tried == [k for k in order if k in tried]
    for trial in filling["trials"]:
        assert trial["kept"] is (not trial["retired"])
    for norm, key in filling["filled"].items():
        if key is not None:
            assert er.CANDIDATES[key]["norm"] == int(norm)


def test_the_final_ladder_answers_nothing_wrongly(stored):
    assert stored["final"]["wrong"] == 0
    assert stored["final"]["safe"] is True


def test_the_module_is_exact():
    assert ex.module_float_sites(Path(er.__file__)) == {}
