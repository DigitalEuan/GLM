"""``glm_universal.reasoning.carrier_read`` -- a carrier read in the answering
path, and a sender tag with a code of its own (Phase 134).

The question
------------
Phase 133 (``studies/DESIGNED_SUBSTRATE_STUDY.md``) proved two new stages of
the carried fork sound -- the seven-bit sender tag and the soft certificate --
and measured them beside the fork only: no query kind read a carrier, so no
question could reach them.  It also measured the tag's weakness: a tag with
one bit flipped resolves 28,096 tied reads to the wrong carrier.
``studies/PROTECTED_TAG_STUDY.md`` declared seven marks, P1-P7, for closing
both; :func:`protected_tag_report` takes P2-P6, and the evaluation cases of
the ``carrier`` query kind take P7.

The protected tag
-----------------
Two candidates of one fork differ by an octad, and a tag of parities is
linear, so how many flips of the tag a stage absorbs is fixed by the smallest
tag weight over the 759 octads (``GLM.Golay24.mtag_separation``).  For the
seven-bit tag that weight is 1 (``tag7_one_flip_misleads``).  The protected
tags keep the seven bits and append the parities of a code on them:

``TAG11_MASKS``  the shortened Hamming ``[11,7,3]`` code: every octad's tag
                 has weight ``>= 3`` (``tag11_octad_weight``), so a stage of
                 radius 1 corrects one flipped tag bit.
``TAG15_MASKS``  the ``[15,7,5]`` BCH code: weight ``>= 5``
                 (``tag15_octad_weight``), so a stage of radius 2 corrects two
                 (``tag15_corrects_two``); radius 2 is sharp
                 (``tag15_three_flips_mislead``).

Both guarantees hold for a carrier that took up to **seven** flips, not just
four: a wrong codeword within 4 of the received word is then within 11 of the
sent one, hence an octad away (``tag_flags_miscorrection`` for the intact
seven-bit tag).  So a tag also turns the decoder's silent wrong answers on
heavy corruption into refusals.

The query kind
--------------
:func:`parse_request` reads ``carrier <word> [tag <t>] [protected tag <p>]
[soft <s1>, ..., <s24>]`` and :func:`read_carrier` answers it with the
carried fork and these stages; ``runtime/session.py`` turns the result into an
answer or a ``boundary`` refusal.

Exactness
---------
``int`` masks and :class:`fractions.Fraction` only.  No float, no RNG.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from ..substrate.mog import GOLAY_MASKS
from . import carried_fork as cf
from . import designed_substrate as dsub

__all__ = [
    "LEAN_FILE", "LEAN_THEOREMS", "TAG11_MASKS", "TAG15_MASKS",
    "PROTECTED_RADIUS", "PROTECTED_ASSUMPTION", "CarrierError",
    "CarrierRead", "mtag", "hamming", "with_protected_tag", "parse_request",
    "read_carrier", "p2_constants", "p3_protected", "p4_seven_bit_control",
    "p5_beyond_radius", "p6_heavy", "protected_tag_report",
]

N = 24
FULL = (1 << N) - 1
LEAN_FILE = "RequestProject/GLM/ProtectedTag.lean"

#: The theorems of ``RequestProject/GLM/ProtectedTag.lean`` (mark P1).
LEAN_THEOREMS: Tuple[str, ...] = (
    "mtag_tagMasks", "mtag_symmDiff", "close_pair_octad", "hdist_triangle",
    "mtag_separation", "mtag_resolves", "tag_flags_miscorrection",
    "tag7_one_flip_misleads", "tagMasks11_prefix", "tagMasks15_prefix",
    "tag11_octad_weight", "tag15_octad_weight", "tag11_corrects_one",
    "tag15_corrects_two", "tag15_radius_one_safe",
    "tag15_three_flips_mislead",
)

#: The eleven masks (``tagMasks11`` in the Lean file): the seven tag masks,
#: then the four parities of the shortened Hamming [11,7,3] code
#: (generator x^4 + x + 1) on the tag bits.
TAG11_MASKS: Tuple[int, ...] = dsub.TAG_MASKS + (
    1207032, 15741673, 6051243, 4961599)

#: The fifteen masks (``tagMasks15``): the seven tag masks, then the eight
#: parities of the [15,7,5] BCH code (generator x^8 + x^7 + x^6 + x^4 + 1).
TAG15_MASKS: Tuple[int, ...] = dsub.TAG_MASKS + (
    2024547, 7094406, 4961599, 6546849, 5667552, 8558092, 6636657, 1130820)

#: The radius the answering path reads the fifteen-bit tag at.
PROTECTED_RADIUS = 2

PROTECTED_ASSUMPTION = ("the protected tag was computed by the sender from "
                        "the carrier and took at most two flips, and the "
                        "carrier took at most seven")

_STAGE_PROTECTED = "protected tag"


def _popcount(x: int) -> int:
    return bin(x).count("1")


def hamming(a: int, b: int) -> int:
    return _popcount(a ^ b)


def mtag(word: int, masks: Sequence[int]) -> int:
    """The tag of ``word`` through ``masks``: bit ``i`` is the parity of
    ``word & masks[i]`` (``mtag`` in the Lean file)."""
    out = 0
    for i, m in enumerate(masks):
        if _popcount(word & m) & 1:
            out |= 1 << i
    return out


def with_protected_tag(fork: cf.CarriedFork, received: int,
                       masks: Sequence[int] = TAG15_MASKS,
                       radius: int = PROTECTED_RADIUS) -> cf.CarriedFork:
    """The protected-tag stage: keep the candidates whose tag lies within
    ``radius`` flips of the received tag."""
    width = len(masks)
    return dsub._prune(
        fork, _STAGE_PROTECTED,
        lambda c: hamming(mtag(c, masks), received) <= radius,
        f"its {width}-bit tag is more than {radius} flips from the received "
        f"tag {received:#06x}", PROTECTED_ASSUMPTION)


# ===========================================================================
# 1.  THE READ -- what the query kind answers
# ===========================================================================

class CarrierError(ValueError):
    """A request the carrier read refuses, with a short named reason."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


@dataclass(frozen=True)
class CarrierRead:
    """One carrier read through the carried fork and the stages asked for."""

    received: int
    weight: int
    fork: cf.CarriedFork
    stages: Tuple[str, ...]
    soft_derived: bool = False
    removed: Dict[str, int] = field(default_factory=dict)

    @property
    def status(self) -> str:
        return self.fork.status

    @property
    def value(self) -> Optional[int]:
        return self.fork.value

    @property
    def message(self) -> Optional[int]:
        """The twelve message bits (coordinates 0-11 of the codeword)."""
        return None if self.value is None else self.value & 0xFFF

    @property
    def flips(self) -> Optional[int]:
        return None if self.value is None else hamming(self.value,
                                                       self.received)

    @property
    def candidates(self) -> Tuple[int, ...]:
        return self.fork.candidates

    @property
    def live(self) -> Tuple[int, ...]:
        return self.fork.live


_NUMBER = r"0x[0-9a-f]+|0b[01]+|\d+"
_VALUE = r"\d+/\d+|\d*\.\d+|\d+"


def _int(token: str) -> int:
    t = token.lower()
    if t.startswith("0x"):
        return int(t, 16)
    if t.startswith("0b"):
        return int(t, 2)
    return int(t)


def parse_request(text: str) -> Dict[str, object]:
    """Read ``<word> [tag <t>] [protected tag <p>] [soft <s1>, ..., <s24>]``.

    Returns the parts given, each ``None`` when absent.  Every value is
    exact: a soft reading is 24 rationals in ``[0, 1]``, the chance each bit
    is a one.  Anything else in the request is refused, not skipped.
    """
    rest = " " + text.strip().lower().replace(",", " , ") + " "
    out: Dict[str, object] = {"word": None, "tag": None,
                              "protected_tag": None, "soft": None}
    m = re.search(r"\ssoft\s+(.*)$", rest)
    if m:
        values = [v for v in m.group(1).replace(",", " ").split() if v]
        try:
            soft = tuple(Fraction(v) for v in values)
        except (ValueError, ZeroDivisionError):
            raise CarrierError(
                "soft-reading", f"the soft reading {m.group(1).strip()!r} is "
                f"not a list of exact numbers") from None
        if len(soft) != N:
            raise CarrierError(
                "soft-reading", f"a soft reading has one value per "
                f"coordinate, 24 in all; {len(soft)} were given")
        if any(not 0 <= s <= 1 for s in soft):
            raise CarrierError(
                "soft-reading", "each soft value is the chance a bit is a "
                "one, so it lies between 0 and 1")
        out["soft"] = soft
        rest = rest[:m.start()] + " "
    m = re.search(rf"\sprotected\s+tag\s+({_NUMBER})\s", rest)
    if m:
        out["protected_tag"] = _int(m.group(1))
        rest = rest[:m.start()] + " " + rest[m.end():]
    m = re.search(rf"\stag\s+({_NUMBER})\s", rest)
    if m:
        out["tag"] = _int(m.group(1))
        rest = rest[:m.start()] + " " + rest[m.end():]
    m = re.match(rf"\s*({_NUMBER})\s", rest)
    if m:
        out["word"] = _int(m.group(1))
        rest = rest[m.end():]
    leftover = [w for w in re.split(r"[\s,]+", rest)
                if w and w not in ("with", "and", "of", "the", "read")]
    if leftover:
        raise CarrierError(
            "unread-words", f"the request holds words the carrier read does "
            f"not take: {' '.join(leftover)!r}; it takes "
            f"'carrier <word> [tag <t>] [protected tag <p>] "
            f"[soft <s1>, ..., <s24>]'")
    return out


def _hard_word(soft: Sequence[Fraction]) -> int:
    word = 0
    for j, s in enumerate(soft):
        if s == Fraction(1, 2):
            raise CarrierError(
                "soft-undecided", f"coordinate {j} of the soft reading is "
                f"exactly 1/2, so it names no bit; give the received word "
                f"as well")
        if s > Fraction(1, 2):
            word |= 1 << j
    return word


def read_carrier(word: Optional[int] = None, tag: Optional[int] = None,
                 protected_tag: Optional[int] = None,
                 soft: Optional[Sequence[Fraction]] = None) -> CarrierRead:
    """Read one 24-bit carrier through the carried fork and the stages the
    request supplies information for.

    Nothing is picked: the read is resolved only when exactly one candidate
    survives every stage, and each stage is one whose soundness is proved
    (``tag_resolves``, ``mtag_resolves``, ``soft_certificate``).
    """
    soft_derived = False
    if word is None:
        if soft is None:
            raise CarrierError(
                "no-word", "the request names no carrier: give a 24-bit "
                "word, e.g. 'carrier 0x5a3c21', or a soft reading")
        word = _hard_word(soft)
        soft_derived = True
    if not 0 <= word <= FULL:
        raise CarrierError(
            "not-a-word", f"{word:#x} is not a 24-bit word: it needs "
            f"{word.bit_length()} bits")
    if tag is not None and not 0 <= tag < 1 << len(dsub.TAG_MASKS):
        raise CarrierError(
            "tag-width", f"the sender tag has seven bits, and {tag:#x} "
            f"needs {tag.bit_length()}; a fifteen-bit tag is a "
            f"'protected tag'")
    if protected_tag is not None and \
            not 0 <= protected_tag < 1 << len(TAG15_MASKS):
        raise CarrierError(
            "tag-width", f"the protected tag has fifteen bits, and "
            f"{protected_tag:#x} needs {protected_tag.bit_length()}")
    fork = cf.carry(word)
    stages: List[str] = ["decoder"]
    removed: Dict[str, int] = {}

    def run(name: str, after: cf.CarriedFork) -> cf.CarriedFork:
        removed[name] = len(fork_now.live) - len(after.live)
        stages.append(name)
        return after

    fork_now = fork
    if tag is not None:
        fork_now = run("sender tag", dsub.with_tag(fork_now, tag))
    if protected_tag is not None:
        fork_now = run(_STAGE_PROTECTED,
                       with_protected_tag(fork_now, protected_tag))
    if soft is not None:
        fork_now = run("soft certificate",
                       dsub.with_soft_certificate(fork_now, soft))
    return CarrierRead(received=word, weight=fork.weight, fork=fork_now,
                       stages=tuple(stages), soft_derived=soft_derived,
                       removed=removed)


# ===========================================================================
# 2.  THE MARKS
# ===========================================================================

def _lean_list(name: str) -> Optional[Tuple[int, ...]]:
    path = (Path(__file__).resolve().parents[2] / "glm_lean" / LEAN_FILE)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.search(rf"def {name} : List ℕ :=\s*\[([^\]]*)\]", text)
    if not m:
        return None
    return tuple(int(v) for v in m.group(1).replace("\n", " ").split(","))


def _octads() -> Tuple[int, ...]:
    return tuple(c for c in GOLAY_MASKS if _popcount(c) == 8)


def p2_constants() -> Dict[str, object]:
    """P2: the masks against the Lean file, and the smallest tag weight over
    the 759 octads for the seven-, eleven- and fifteen-bit tags."""
    octads = _octads()
    lean11, lean15 = _lean_list("tagMasks11"), _lean_list("tagMasks15")
    w7 = [_popcount(dsub.tag(o)) for o in octads]
    w11 = [_popcount(mtag(o, TAG11_MASKS)) for o in octads]
    w15 = [_popcount(mtag(o, TAG15_MASKS)) for o in octads]
    out = {"lean11_equal": lean11 == TAG11_MASKS,
           "lean15_equal": lean15 == TAG15_MASKS,
           "prefix_is_tag": (TAG11_MASKS[:7] == dsub.TAG_MASKS
                             == TAG15_MASKS[:7]),
           "octads": len(octads),
           "min_weight_7": min(w7), "at_min_7": w7.count(min(w7)),
           "min_weight_11": min(w11), "at_min_11": w11.count(min(w11)),
           "min_weight_15": min(w15), "at_min_15": w15.count(min(w15))}
    out["passed"] = (out["lean11_equal"] and out["lean15_equal"]
                     and out["prefix_is_tag"] and len(octads) == 759
                     and (min(w7), min(w11), min(w15)) == (1, 3, 5))
    return out


def _flip(tag_value: int, positions: Sequence[int]) -> int:
    for p in positions:
        tag_value ^= 1 << p
    return tag_value


def _tally() -> Dict[str, int]:
    return {"resolved": 0, "wrong": 0, "open": 0, "contradicted": 0}


def _count(t: Dict[str, int], after: cf.CarriedFork, truth: int) -> None:
    if after.status == "resolved":
        t["resolved"] += 1
        t["wrong"] += after.value != truth
    else:
        t[after.status] += 1


def _tied_battery():
    """The Phase 133 battery: 64 probe codewords x all 10,626 weight-4
    errors, with the read index ``i`` the declared corruption keys off."""
    words, _ = cf.x1_probe()
    errors = cf._weight4_errors()
    i = 0
    for c in words:
        for e in errors:
            yield i, c, cf.carry(c ^ e)
            i += 1


def p3_p4_p5() -> Dict[str, object]:
    """P3, P4 and P5 in one pass over the 680,064 tied reads.

    * P3: the fifteen-bit tag at radius 2 with ``i mod 3`` flips at
      positions ``i, i+5, i+10 (mod 15)``; the eleven-bit tag at radius 1
      with ``i mod 2`` flips at position ``i mod 11``.
    * P4: the seven-bit tag with one flip at ``i mod 7`` (Phase 133's
      corrupted-tag control), reproduced.
    * P5: the fifteen-bit tag with three flips at ``i, i+5, i+10 (mod 15)``,
      read at radius 2 and at radius 1.  Post hoc, not the declared mark:
      the same with three consecutive flips ``i, i+1, i+2 (mod 15)``, added
      after the declared pattern turned out never to mislead (study §7.3).
    """
    p3_15, p3_11 = _tally(), _tally()
    p4 = _tally()
    p5_r2, p5_r1 = _tally(), _tally()
    post_r2, post_r1 = _tally(), _tally()
    reads = 0
    for i, c, fork in _tied_battery():
        reads += 1
        t15 = mtag(c, TAG15_MASKS)
        three = (i % 15, (i + 5) % 15, (i + 10) % 15)
        _count(p3_15, with_protected_tag(
            fork, _flip(t15, three[:i % 3]), TAG15_MASKS, 2), c)
        t11 = mtag(c, TAG11_MASKS)
        _count(p3_11, with_protected_tag(
            fork, _flip(t11, (i % 11,)[:i % 2]), TAG11_MASKS, 1), c)
        _count(p4, dsub.with_tag(fork, dsub.tag(c) ^ (1 << (i % 7))), c)
        bad = _flip(t15, three)
        _count(p5_r2, with_protected_tag(fork, bad, TAG15_MASKS, 2), c)
        _count(p5_r1, with_protected_tag(fork, bad, TAG15_MASKS, 1), c)
        run = _flip(t15, (i % 15, (i + 1) % 15, (i + 2) % 15))
        _count(post_r2, with_protected_tag(fork, run, TAG15_MASKS, 2), c)
        _count(post_r1, with_protected_tag(fork, run, TAG15_MASKS, 1), c)
    p3 = {"reads": reads, "tag15_radius2": p3_15, "tag11_radius1": p3_11,
          "passed": (p3_15["resolved"] == p3_11["resolved"] == reads
                     and p3_15["wrong"] == p3_11["wrong"] == 0)}
    p4_out = {"reads": reads, "tag7_one_flip": p4,
              "passed": p4["wrong"] == 28096}
    p5 = {"reads": reads, "radius2": p5_r2, "radius1": p5_r1,
          "post_hoc_consecutive": {"radius2": post_r2, "radius1": post_r1},
          "passed": p5_r2["wrong"] > 0 and p5_r1["wrong"] == 0}
    return {"P3": p3, "P4": p4_out, "P5": p5}


def p3_protected() -> Dict[str, object]:
    return p3_p4_p5()["P3"]


def p4_seven_bit_control() -> Dict[str, object]:
    return p3_p4_p5()["P4"]


def p5_beyond_radius() -> Dict[str, object]:
    return p3_p4_p5()["P5"]


def _heavy_errors(weight: int) -> Tuple[int, ...]:
    return tuple(sum(1 << b for b in combo)
                 for combo in combinations(range(N), weight))


def p6_heavy(stride: int = 64) -> Dict[str, object]:
    """P6: heavy corruption.  For each of the 64 probe codewords ``k`` and
    each weight 5, 6, 7, every ``stride``-th error in combinations order
    starting at index ``k``: what the decoder alone answers, and what the
    intact seven-bit tag and the fifteen-bit tag with ``i mod 3`` flips
    (radius 2) leave of it."""
    words, _ = cf.x1_probe()
    rows = {}
    total_wrong_alone = total_wrong_tag = total_wrong_p15 = 0
    for weight in (5, 6, 7):
        errors = _heavy_errors(weight)
        alone, tag7, p15 = _tally(), _tally(), _tally()
        reads = 0
        for k, c in enumerate(words):
            t7 = dsub.tag(c)
            t15 = mtag(c, TAG15_MASKS)
            for e in errors[k % stride::stride]:
                i = reads
                reads += 1
                fork = cf.carry(c ^ e)
                _count(alone, fork, c)
                _count(tag7, dsub.with_tag(fork, t7), c)
                three = (i % 15, (i + 5) % 15, (i + 10) % 15)
                _count(p15, with_protected_tag(
                    fork, _flip(t15, three[:i % 3]), TAG15_MASKS, 2), c)
        rows[weight] = {"reads": reads, "decoder_alone": alone,
                        "tag7_intact": tag7, "tag15_radius2": p15}
        total_wrong_alone += alone["wrong"]
        total_wrong_tag += tag7["wrong"]
        total_wrong_p15 += p15["wrong"]
    return {"stride": stride, "by_weight": rows,
            "wrong_decoder_alone": total_wrong_alone,
            "wrong_tag7_intact": total_wrong_tag,
            "wrong_tag15_radius2": total_wrong_p15,
            "passed": (total_wrong_alone > 0 and total_wrong_tag == 0
                       and total_wrong_p15 == 0)}


def protected_tag_report() -> Dict[str, object]:
    """P2-P6 against the marks of ``studies/PROTECTED_TAG_STUDY.md`` (P1 is
    the Lean build, P7 the evaluation cases of the ``carrier`` kind)."""
    p2 = p2_constants()
    tied = p3_p4_p5()
    p6 = p6_heavy()
    marks = {"P2": p2["passed"], "P3": tied["P3"]["passed"],
             "P4": tied["P4"]["passed"], "P5": tied["P5"]["passed"],
             "P6": p6["passed"]}
    return {"P2": p2, "P3": tied["P3"], "P4": tied["P4"], "P5": tied["P5"],
            "P6": p6, "marks": marks,
            "met": sorted(k for k, v in marks.items() if v),
            "not_met": sorted(k for k, v in marks.items() if not v),
            "lean_file": LEAN_FILE}
