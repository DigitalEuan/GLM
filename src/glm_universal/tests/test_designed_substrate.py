"""Tests for the designed substrate, brought in (Phase 133).

``studies/DESIGNED_SUBSTRATE_STUDY.md`` pre-registered eight marks.  These
tests pin:

* the **Lean file** (S1): it exists, states the theorems the mark names, and
  has no ``sorry``;
* the **stages**: the sender tag and the soft certificate write ordinary
  ledger records, quote their assumptions, and leave the ledger a partition;
* the **constants** (S3): the tag masks equal the Lean file's, and every
  octad has a non-zero tag;
* the **soft certificate** on the K4b ensemble (S4, it refuses every read)
  and on the gentle ensemble (S5, every read resolved, 0 wrong);
* the **designed alternatives** (S6): every declared one-bit extension
  miscorrects silently, the GLM's code never does;
* the **floor** (S7) as measured, with the declared one-sixth clause missed on
  the 64-codeword probe;
* the **sender tag** on all 680,064 probe reads (S2) and non-interference
  (S8), exhaustively.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.reasoning import carried_fork as cf
from glm_universal.reasoning import designed_substrate as ds
from glm_universal.substrate.mog import GOLAY_MASKS

_ROOT = Path(__file__).resolve().parents[3]
_LEAN = _ROOT / "src" / "lean" / ds.LEAN_FILE


def test_the_lean_file_states_the_theorems_without_sorry():
    text = _LEAN.read_text(encoding="utf-8")
    for name in ds.LEAN_THEOREMS:
        assert f"theorem {name}" in text, name
    assert "sorry" not in text


def test_the_tag_masks_are_the_lean_files():
    assert ds._lean_tag_masks() == ds.TAG_MASKS


def test_every_octad_has_a_nonzero_tag():
    octads = [c for c in GOLAY_MASKS if bin(c).count("1") == 8]
    assert len(octads) == 759
    assert all(ds.tag(o) != 0 for o in octads)


def test_the_tag_is_linear():
    for a, b in zip(GOLAY_MASKS[:64], GOLAY_MASKS[64:128]):
        assert ds.tag(a ^ b) == ds.tag(a) ^ ds.tag(b)


def test_the_tag_stage_resolves_a_tie_to_the_truth_and_keeps_the_ledger():
    c = GOLAY_MASKS[77]
    e = 0b1111 << 5
    fork = cf.carry(c ^ e)
    assert len(fork.candidates) == 6
    after = ds.with_tag(fork, ds.tag(c))
    assert after.status == "resolved" and after.value == c
    assert after.partition_holds()
    assert {x.stage for x in after.ledger} == {"sender tag"}
    assert after.assumptions == (ds.TAG_ASSUMPTION,)


def test_a_corrupted_tag_contradicts_or_misleads():
    c = GOLAY_MASKS[77]
    fork = cf.carry(c ^ (0b1111 << 5))
    bad = ds.with_tag(fork, ds.tag(c) ^ 1)
    assert bad.status in ("contradicted", "resolved")
    assert bad.value != c


def test_the_soft_certificate_keeps_at_most_one_candidate():
    words, errs = cf.x1_probe()
    for i, (c, e) in enumerate([(w, x) for w in words[:4] for x in errs]):
        for reading in (cf.soft_reading, ds.gentle_reading):
            soft = reading(i, c, e)
            after = ds.with_soft_certificate(cf.carry(c ^ e), soft)
            assert len(after.live) <= 1
            assert after.partition_holds()


def test_the_soft_distance_is_four_times_the_hamming_distance_on_corners():
    a, b = GOLAY_MASKS[5], GOLAY_MASKS[9]
    soft = tuple(Fraction((a >> j) & 1) for j in range(24))
    assert ds.soft_sq_distance(soft, a) == 0
    assert ds.soft_sq_distance(soft, b) == 4 * bin(a ^ b).count("1")


def test_s4_the_certificate_refuses_every_k4b_read():
    r = ds.s4_soft_k4b()
    assert r["reads"] == 768 and r["resolved"] == 0 and r["wrong"] == 0
    assert r["contradicted"] == 768 and r["truth_within_radius"] == 0
    assert r["least_reliable_right"] == 576
    assert r["passed"]


def test_s5_the_certificate_resolves_every_gentle_read():
    r = ds.s5_soft_gentle()
    assert (r["reads"], r["resolved"], r["wrong"]) == (768, 768, 0)
    assert r["resolved_equal_least_reliable"] == 768
    assert r["passed"]


def test_s6_every_declared_extension_miscorrects_silently():
    r = ds.s6_extensions()
    assert r["golay"]["silent"] == 0 and r["golay"]["weight7_words"] == 0
    silent = {row["lambda"]: row["silent"] for row in r["rows"]}
    assert silent == {1: 2695, 2: 2695, 4: 2695, 8: 2695, 3: 3920,
                      7: 4375, 15: 4480, 4095: 3920}
    assert all(row["silent"] == 35 * row["weight7_words"]
               for row in r["rows"])
    assert r["passed"]


@pytest.mark.exhaustive
def test_s7_the_floor_holds_and_the_sample_clause_is_missed():
    r = ds.s7_floor()
    assert r["received_at_distance_four"] == r["floor"] == 7254016
    assert r["snap_sample_agrees"]
    assert r["snap_right"] == 120604 != r["one_sixth"]
    assert not r["passed"]


@pytest.mark.exhaustive
def test_s2_the_sender_tag_resolves_every_probe_read():
    r = ds.s2_sender_tag()
    assert r["reads"] == r["resolved"] == 680064
    assert r["wrong"] == r["open"] == r["contradicted"] == 0
    assert r["hard_word_alone_resolved"] == 0
    bad = r["corrupted_tag"]
    assert (bad["resolved"], bad["wrong"], bad["contradicted"]) == (
        28096, 28096, 651968)
    assert r["passed"]


@pytest.mark.exhaustive
def test_s3_and_s8():
    assert ds.s3_constants()["passed"]
    assert ds.s8_noninterference()["passed"]
