"""Tests for the carrier read and the protected tag (Phase 134).

``studies/PROTECTED_TAG_STUDY.md`` pre-registered seven marks.  These tests
pin:

* the **Lean file** (P1): it exists, states the theorems the mark names, and
  has no ``sorry``;
* the **constants** (P2): the eleven- and fifteen-bit masks equal the Lean
  file's, begin with the seven-bit tag, and give every octad a tag of weight
  at least 3 and 5 (the seven-bit tag: 1);
* the **stage**: the protected tag resolves a tie through two flipped tag
  bits, keeps the ledger a partition and quotes its assumption;
* the **read** and its **request grammar**, including every named refusal;
* the **query kind**: the nine declared questions of §3.1 through the
  session (P7's own half; the end-to-end half is the evaluation);
* the **tied battery** (P3, P4, P5) and **heavy corruption** (P6),
  exhaustively, as measured -- P5 missed as declared.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.reasoning import carried_fork as cf
from glm_universal.reasoning import carrier_read as cr
from glm_universal.reasoning import designed_substrate as ds
from glm_universal.runtime.parser import KINDS, parse_query
from glm_universal.substrate.mog import GOLAY_MASKS

_ROOT = Path(__file__).resolve().parents[3]
_LEAN = _ROOT / "src" / "lean" / cr.LEAN_FILE

_C = 0x8AD5A3            # message 0x5a3
_TIE = 0xCA97A1          # _C with coordinates 1, 9, 14, 22 flipped
_HEAVY = 0xCA9781        # ... and coordinate 5
_GENTLE = ("13/16, 7/16, 1/16, 0, 3/16, 7/8, 1/16, 1, 13/16, 9/16, 15/16, "
           "0, 13/16, 1/8, 13/32, 1, 3/16, 7/8, 1/16, 1, 3/16, 1/8, 19/32, 1")


def test_the_lean_file_states_the_theorems_without_sorry():
    text = _LEAN.read_text(encoding="utf-8")
    for name in cr.LEAN_THEOREMS:
        assert f"theorem {name}" in text, name
    assert "sorry" not in text


def test_p2_the_constants():
    out = cr.p2_constants()
    assert out["passed"]
    assert (out["min_weight_7"], out["at_min_7"]) == (1, 42)
    assert (out["min_weight_11"], out["at_min_11"]) == (3, 78)
    assert (out["min_weight_15"], out["at_min_15"]) == (5, 108)


def test_the_protected_tags_are_linear_and_extend_the_tag():
    for a, b in zip(GOLAY_MASKS[:64], GOLAY_MASKS[64:128]):
        for masks in (cr.TAG11_MASKS, cr.TAG15_MASKS):
            assert cr.mtag(a ^ b, masks) == cr.mtag(a, masks) ^ cr.mtag(b, masks)
        assert cr.mtag(a, cr.TAG15_MASKS) & 0x7F == ds.tag(a)


def test_the_protected_stage_resolves_through_two_flips():
    fork = cf.carry(_TIE)
    assert len(fork.candidates) == 6 and _C in fork.candidates
    received = cr.mtag(_C, cr.TAG15_MASKS) ^ 0b100000000010
    after = cr.with_protected_tag(fork, received)
    assert after.status == "resolved" and after.value == _C
    assert after.partition_holds()
    assert after.assumptions == (cr.PROTECTED_ASSUMPTION,)


def test_the_request_grammar():
    assert cr.parse_request("0xca97a1 tag 0x54") == {
        "word": _TIE, "tag": 0x54, "protected_tag": None, "soft": None}
    assert cr.parse_request("0xca97a1 protected tag 0x1256")[
        "protected_tag"] == 0x1256
    assert cr.parse_request("0b11 with tag 3")["word"] == 3
    soft = cr.parse_request("soft " + _GENTLE)["soft"]
    assert len(soft) == 24 and soft[0] == Fraction(13, 16)
    for bad, reason in (("0xca97a1 please", "unread-words"),
                        ("soft 1/2, 1", "soft-reading"),
                        ("soft " + ", ".join(["2"] * 24), "soft-reading")):
        with pytest.raises(cr.CarrierError) as info:
            cr.parse_request(bad)
        assert info.value.reason == reason


def test_the_read_and_its_refusals():
    assert cr.read_carrier(_C).flips == 0
    assert cr.read_carrier(_TIE).status == "open"
    read = cr.read_carrier(_TIE, tag=0x54)
    assert (read.status, read.value, read.message) == ("resolved", _C, 0x5A3)
    assert cr.read_carrier(_HEAVY).value == 0x428781      # silently wrong
    assert cr.read_carrier(_HEAVY, tag=0x54).status == "contradicted"
    soft = cr.parse_request("soft " + _GENTLE)["soft"]
    read = cr.read_carrier(None, soft=soft)
    assert read.soft_derived and read.value == _C
    for kwargs, reason in (({"word": 1 << 24}, "not-a-word"),
                           ({"word": _TIE, "tag": 0x154}, "tag-width"),
                           ({"word": _TIE, "protected_tag": 1 << 15},
                            "tag-width"),
                           ({}, "no-word"),
                           ({"soft": (Fraction(1, 2),) * 24},
                            "soft-undecided")):
        with pytest.raises(cr.CarrierError) as info:
            cr.read_carrier(**kwargs)
        assert info.value.reason == reason


def test_the_kind_is_start_only():
    assert "carrier" in KINDS
    assert parse_query("carrier 0xca97a1 tag 0x54").kind == "carrier"
    assert parse_query("read carrier 0x1").options["request"] == "0x1"
    assert parse_query("describe the carrier of energy").kind != "carrier"


_DECLARED = (
    ("carrier 0x8ad5a3", True, ("0x8ad5a3", "0x5a3", "0 flips")),
    ("carrier 0x88d5ab", True, ("0x8ad5a3", "0x5a3", "2 flips")),
    ("carrier 0xca97a1", False, ("open-fork",)),
    ("carrier 0xca97a1 tag 0x54", True, ("0x8ad5a3", "sender tag")),
    ("carrier 0xca97a1 protected tag 0x1256", True,
     ("0x8ad5a3", "protected tag")),
    ("carrier 0xca9781 tag 0x54", False, ("contradicted",)),
    ("carrier soft " + _GENTLE, True, ("0x8ad5a3", "soft certificate")),
    ("carrier 0x1000000", False, ("not-a-word",)),
    ("carrier 0xca97a1 tag 0x154", False, ("tag-width",)),
)


@pytest.mark.parametrize("question,answers,contains", _DECLARED)
def test_p7_the_declared_questions(question, answers, contains):
    from glm_universal.runtime.session import GeometricSession
    session = GeometricSession(domains=())
    solution = session.solve(parse_query(question))
    assert solution.ok is answers, solution.answer
    for text in contains:
        assert text in solution.answer, (text, solution.answer)


@pytest.mark.exhaustive
def test_p3_p4_p5_on_the_tied_battery():
    out = cr.p3_p4_p5()
    p3, p4, p5 = out["P3"], out["P4"], out["P5"]
    assert p3["passed"] and p3["reads"] == 680064
    assert p3["tag15_radius2"]["wrong"] == p3["tag11_radius1"]["wrong"] == 0
    assert p4["passed"]
    assert p4["tag7_one_flip"] == {"resolved": 28096, "wrong": 28096,
                                   "open": 0, "contradicted": 651968}
    # P5 missed as declared: the declared three-flip pattern never misleads
    # radius 2; three consecutive flips do (post hoc), radius 1 never.
    assert not p5["passed"]
    assert p5["radius2"]["wrong"] == p5["radius1"]["wrong"] == 0
    assert p5["post_hoc_consecutive"]["radius2"]["wrong"] == 26681
    assert p5["post_hoc_consecutive"]["radius1"]["wrong"] == 0


@pytest.mark.exhaustive
def test_p6_heavy_corruption():
    out = cr.p6_heavy()
    assert out["passed"]
    assert out["wrong_decoder_alone"] == 409860
    assert out["wrong_tag7_intact"] == out["wrong_tag15_radius2"] == 0
    assert {w: r["reads"] for w, r in out["by_weight"].items()} == {
        5: 42504, 6: 134596, 7: 346104}
