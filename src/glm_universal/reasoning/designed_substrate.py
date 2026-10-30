"""``glm_universal.reasoning.designed_substrate`` -- the designed substrate,
brought in (Phase 133).

The question
------------
The owner's substrate study (``source_material/substrate_study/``) asked
whether the Golay-Leech substrate is optimal for the GLM or whether a designed
dimensional system could beat it.  Its answer: in the GLM's regime (24-bit
carriers holding 12 bits, corrupted by bit flips) Golay is optimal among all
4,096-word designs, the six-way tie at coset weight 4 is forced by the
parameters, and the freedom left is in **how the tie is resolved**.
``studies/DESIGNED_SUBSTRATE_STUDY.md`` pre-registered eight marks, S1-S8, for
bringing that answer into the GLM; :func:`designed_substrate_report` takes
them.

The stages
----------
Two new stages of the carried fork (:mod:`.carried_fork`).  They write
ordinary :class:`~.carried_fork.Elimination` records, so the ledger rules of
``RequestProject/GLM/CarriedFork.lean`` hold for them unchanged, and they are
kept here so that ``carried_fork.py`` is not edited.

``sender tag``        seven parities of the carrier (:data:`TAG_MASKS`),
                      computed by the sender without knowing the error.  A
                      candidate whose tag differs from the received tag is
                      removed.  ``GLM.Golay24.tag_resolves``: two codewords
                      within distance 4 of one word with one tag are equal, so
                      the stage always resolves a weight-4 read, to the truth,
                      when its assumption holds.
``soft certificate``  a candidate whose ``+-1`` image is at squared distance
                      ``>= 8`` from the soft reading is removed.
                      ``GLM.Golay24.soft_certificate``: at most one candidate
                      can be nearer than 8, and the radius is sharp
                      (``soft_certificate_sharp``).

Exactness
---------
``int`` masks and :class:`fractions.Fraction` only.  No float, no RNG.
"""

from __future__ import annotations

import re
from fractions import Fraction
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from ..substrate.golay_decode import coset_census, legacy_snap_decode
from ..substrate.mog import GOLAY_MASKS
from . import carried_fork as cf

__all__ = [
    "LEAN_FILE", "LEAN_THEOREMS", "TAG_MASKS", "TAG_ASSUMPTION",
    "SOFT_ASSUMPTION", "SOFT_RADIUS_SQ", "EXTENSION_LAMBDAS",
    "tag", "with_tag", "soft_sq_distance", "with_soft_certificate",
    "gentle_reading", "extension_code", "silent_weight4",
    "s2_sender_tag", "s3_constants", "s4_soft_k4b", "s5_soft_gentle",
    "s6_extensions", "s7_floor", "s8_noninterference",
    "designed_substrate_report",
]

N = 24
LEAN_FILE = "RequestProject/GLM/DesignedSubstrate.lean"

#: The theorems of ``RequestProject/GLM/DesignedSubstrate.lean`` (mark S1).
LEAN_THEOREMS: Tuple[str, ...] = (
    "card_ball", "decoder_sum_le", "golay_attains", "golay_optimal",
    "negative_space_floor", "negative_space_floor_4096",
    "weight4_resolved_le", "weight4_resolved_le_4096",
    "tagOf_symmDiff", "tag_nonzero_on_octads", "tag_resolves",
    "sqd_pm", "soft_certificate", "soft_certificate_sharp",
)

#: The seven tag masks (bit ``k`` is coordinate ``k``); ``tagMasks`` in the
#: Lean file.
TAG_MASKS: Tuple[int, ...] = (7442265, 11191954, 5298992, 12955048,
                              9854244, 14599079, 3151149)

TAG_ASSUMPTION = ("the tag was computed by the sender from the carrier and "
                  "arrived intact, and the carrier took at most four flips")
SOFT_ASSUMPTION = ("the soft reading lies within squared distance 8 of the "
                   "sent carrier's +-1 image")
SOFT_RADIUS_SQ = Fraction(8)

#: The declared one-bit extensions of the punctured [23,12,7] code (S6).
EXTENSION_LAMBDAS: Tuple[int, ...] = (1, 2, 4, 8, 3, 7, 15, 4095)

_STAGE_TAG = "sender tag"
_STAGE_SOFT = "soft certificate"


def _popcount(x: int) -> int:
    return bin(x).count("1")


# ===========================================================================
# 1.  THE STAGES
# ===========================================================================

def tag(word: int) -> int:
    """The seven-bit tag: bit ``i`` is the parity of ``word & TAG_MASKS[i]``."""
    out = 0
    for i, m in enumerate(TAG_MASKS):
        if _popcount(word & m) & 1:
            out |= 1 << i
    return out


def _prune(fork: cf.CarriedFork, stage: str, keep, reason: str,
           assumption: str) -> cf.CarriedFork:
    """The carried fork's own pruning, for a stage this module adds."""
    kept, out = [], list(fork.ledger)
    for c in fork.live:
        if keep(c):
            kept.append(c)
        else:
            out.append(cf.Elimination(c, stage, reason, assumption))
    return cf.CarriedFork(fork.received, fork.weight, fork.candidates,
                          tuple(kept), tuple(out))


def with_tag(fork: cf.CarriedFork, received_tag: int) -> cf.CarriedFork:
    """The sender-tag stage."""
    return _prune(fork, _STAGE_TAG, lambda c: tag(c) == received_tag,
                  f"its tag is not the received tag {received_tag:#04x}",
                  TAG_ASSUMPTION)


def soft_sq_distance(soft: Sequence[Fraction], word: int) -> Fraction:
    """Squared distance from ``x = 1 - 2s`` to the ``+-1`` image of ``word``
    (``sqd`` in the Lean file)."""
    total = Fraction(0)
    for j, s in enumerate(soft):
        x = 1 - 2 * Fraction(s)
        target = -1 if (word >> j) & 1 else 1
        total += (x - target) ** 2
    return total


def with_soft_certificate(fork: cf.CarriedFork,
                          soft: Sequence[Fraction]) -> cf.CarriedFork:
    """The soft-certificate stage."""
    return _prune(fork, _STAGE_SOFT,
                  lambda c: soft_sq_distance(soft, c) < SOFT_RADIUS_SQ,
                  "its +-1 image is at squared distance 8 or more from the "
                  "soft reading", SOFT_ASSUMPTION)


def _least_reliable(fork: cf.CarriedFork, soft: Sequence[Fraction]) -> int:
    """The candidate nearest the soft reading (the least reliable tetrad);
    ties broken by the smaller mask, reported only."""
    return min(fork.candidates, key=lambda c: (soft_sq_distance(soft, c), c))


def gentle_reading(i: int, truth: int, error: int) -> Tuple[Fraction, ...]:
    """The declared gentle ensemble G for read ``i`` (study §2)."""
    hard = truth ^ error
    out = []
    for j in range(N):
        if (error >> j) & 1:
            rho = Fraction((3 * i + j) % 4 + 1, 16)
        else:
            rho = Fraction((i + j) % 4 + 5, 8)
        out.append((1 + rho) / 2 if (hard >> j) & 1 else (1 - rho) / 2)
    return tuple(out)


# ===========================================================================
# 2.  THE MARKS
# ===========================================================================

def s2_sender_tag(corrupt_control: bool = True) -> Dict[str, object]:
    """S2: the tag stage on 64 probe codewords x all 10,626 weight-4 errors,
    with the corrupted-tag control and the hard-word baseline."""
    words, _ = cf.x1_probe()
    errors = cf._weight4_errors()
    reads = resolved = wrong = contradicted = open_ = 0
    hard_resolved = 0
    c_resolved = c_wrong = c_contradicted = c_open = 0
    for c in words:
        t = tag(c)
        for i, e in enumerate(errors):
            fork = cf.carry(c ^ e)
            reads += 1
            hard_resolved += fork.status == "resolved"
            after = with_tag(fork, t)
            if after.status == "resolved":
                resolved += 1
                wrong += after.value != c
            elif after.status == "open":
                open_ += 1
            else:
                contradicted += 1
            if corrupt_control:
                bad = with_tag(fork, t ^ (1 << (i % 7)))
                if bad.status == "resolved":
                    c_resolved += 1
                    c_wrong += bad.value != c
                elif bad.status == "open":
                    c_open += 1
                else:
                    c_contradicted += 1
    out = {"reads": reads, "resolved": resolved, "wrong": wrong,
           "open": open_, "contradicted": contradicted,
           "hard_word_alone_resolved": hard_resolved,
           "tag_bits_per_carrier": len(TAG_MASKS),
           "assumption": TAG_ASSUMPTION,
           "passed": (resolved == reads and wrong == 0
                      and contradicted == 0 and open_ == 0)}
    if corrupt_control:
        out["corrupted_tag"] = {"resolved": c_resolved, "wrong": c_wrong,
                                "open": c_open,
                                "contradicted": c_contradicted}
    return out


def closed_world_control(k: int = 32) -> Dict[str, object]:
    """The context stage over the K1 case set, every weight-4 error."""
    cases = cf.case_set(k)
    errors = cf._weight4_errors()
    reads = resolved = wrong = 0
    for c in cases:
        for e in errors:
            fork = cf.carry(c ^ e).restrict_to_cases(cases)
            reads += 1
            if fork.status == "resolved":
                resolved += 1
                wrong += fork.value != c
    return {"k": k, "reads": reads, "resolved": resolved, "wrong": wrong,
            "resolved_share": Fraction(resolved, reads)}


def _lean_tag_masks() -> Optional[Tuple[int, ...]]:
    path = (Path(__file__).resolve().parents[2] / "lean" / LEAN_FILE)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.search(r"def tagMasks : List ℕ :=\s*\[([^\]]*)\]", text)
    if not m:
        return None
    return tuple(int(v) for v in m.group(1).replace("\n", " ").split(","))


def s3_constants() -> Dict[str, object]:
    """S3: the constants against the Lean file; every octad has a non-zero
    tag; every carried weight-4 read's candidates are pairwise 32 apart in the
    +-1 picture (``sqd_pm``: 4 times the Hamming distance)."""
    lean = _lean_tag_masks()
    octads = [c for c in GOLAY_MASKS if _popcount(c) == 8]
    octads_tagged = sum(1 for o in octads if tag(o) != 0)
    words, _ = cf.x1_probe()
    errors = cf._weight4_errors()
    reads = six = pairs_ok = 0
    for c in words:
        for e in errors:
            fork = cf.carry(c ^ e)
            reads += 1
            six += len(fork.candidates) == 6
            pairs_ok += all(4 * _popcount(a ^ b) == 32
                            for a, b in combinations(fork.candidates, 2))
    return {"lean_masks_equal": lean == TAG_MASKS, "octads": len(octads),
            "octads_with_nonzero_tag": octads_tagged, "reads": reads,
            "reads_with_six": six, "reads_pairwise_32": pairs_ok,
            "passed": (lean == TAG_MASKS and octads_tagged == len(octads)
                       == 759 and six == reads == pairs_ok)}


def _soft_run(reading) -> Dict[str, object]:
    words, errs = cf.x1_probe()
    reads = resolved = wrong = contradicted = open_ = 0
    truth_inside = agree_lrt = lrt_right = 0
    i = 0
    for c in words:
        for e in errs:
            soft = reading(i, c, e)
            i += 1
            reads += 1
            fork = cf.carry(c ^ e)
            truth_inside += soft_sq_distance(soft, c) < SOFT_RADIUS_SQ
            lrt = _least_reliable(fork, soft)
            lrt_right += lrt == c
            after = with_soft_certificate(fork, soft)
            if after.status == "resolved":
                resolved += 1
                wrong += after.value != c
                agree_lrt += after.value == lrt
            elif after.status == "open":
                open_ += 1
            else:
                contradicted += 1
    return {"reads": reads, "resolved": resolved, "wrong": wrong,
            "open": open_, "contradicted": contradicted,
            "truth_within_radius": truth_inside,
            "resolved_equal_least_reliable": agree_lrt,
            "least_reliable_right": lrt_right}


def s4_soft_k4b() -> Dict[str, object]:
    """S4: the soft-certificate stage on the carried fork's K4b ensemble."""
    out = _soft_run(cf.soft_reading)
    out["passed"] = out["wrong"] == 0 and out["resolved"] == 0
    return out


def s5_soft_gentle() -> Dict[str, object]:
    """S5: the soft-certificate stage on the declared gentle ensemble G."""
    out = _soft_run(gentle_reading)
    out["resolved_share"] = Fraction(out["resolved"], out["reads"])
    out["passed"] = (out["wrong"] == 0
                     and 10 * out["resolved"] >= 9 * out["reads"]
                     and out["resolved_equal_least_reliable"]
                     == out["resolved"])
    return out


def extension_code(lam: int) -> Tuple[int, ...]:
    """The one-bit extension of the punctured code by message mask ``lam``:
    coordinate 23 of each Golay word plus the parity of ``message & lam``
    (the message is coordinates 0-11; ``lam = 0`` is the GLM's code)."""
    return tuple(w ^ ((_popcount(w & 0xFFF & lam) & 1) << 23)
                 for w in GOLAY_MASKS)


def silent_weight4(code: Sequence[int]) -> Dict[str, int]:
    """Weight-4 corruptions of the zero word that the nearest-codeword rule
    corrects to a unique wrong codeword, and those it leaves tied.

    A codeword of weight ``>= 8`` is at distance ``>= 4`` from a weight-4
    word, so only the nonzero codewords of weight ``<= 7`` can be nearer than
    the zero word; ties at distance 4 are counted as ambiguous, not silent.
    """
    light = [c for c in code if 0 < _popcount(c) <= 8]
    silent = tied = 0
    for e in cf._weight4_errors():
        dists = [_popcount(e ^ c) for c in light]
        best = min(dists) if dists else 99
        if best < 4:
            silent += dists.count(best) == 1
        elif best == 4:
            tied += 1
    return {"silent": silent, "tied": tied,
            "weight7_words": sum(1 for c in code if _popcount(c) == 7)}


def s6_extensions() -> Dict[str, object]:
    """S6: the declared one-bit extensions against the GLM's code."""
    golay = silent_weight4(GOLAY_MASKS)
    rows = []
    for lam in EXTENSION_LAMBDAS:
        r = silent_weight4(extension_code(lam))
        rows.append({"lambda": lam, **r})
    return {"golay": golay, "rows": rows,
            "passed": golay["silent"] == 0 and all(r["silent"] >= 1
                                                    for r in rows)}


def s7_floor() -> Dict[str, object]:
    """S7: the floor and the one-sixth cap on the GLM's own decoder."""
    census = coset_census()
    at_four = census["cosets_by_leader_weight"].get(4, 0) * 4096
    index = {w: i for i, w in enumerate(GOLAY_MASKS)}
    words, _ = cf.x1_probe()
    errors = cf._weight4_errors()
    reads = snap_right = 0
    for c in words:
        for e in errors:
            fork = cf.carry(c ^ e)
            reads += 1
            #  the legacy snap answers the first nearest codeword in scan
            #  order, i.e. the candidate of smallest index
            snap_right += min(fork.candidates, key=index.__getitem__) == c
    sample_agree = all(
        legacy_snap_decode(c ^ e)[0]
        == min(cf.carry(c ^ e).candidates, key=index.__getitem__)
        for c in words[:4] for e in errors[:8])
    return {"received_at_distance_four": at_four, "floor": 2 ** 24
            - 4096 * 2325, "reads": reads, "snap_right": snap_right,
            "one_sixth": 64 * 1771, "snap_sample_agrees": sample_agree,
            #  post hoc, not the declared mark: every received word at
            #  distance 4 is decoded to exactly one of its six candidates, so
            #  over all 4,096 codewords a decoder that picks one candidate
            #  corrects exactly as many weight-4 pairs as there are such
            #  words -- the cap -- while a 64-codeword sample need not hold a
            #  sixth of them
            "all_codewords_snap_right_by_coset": at_four,
            "passed": (at_four == 2 ** 24 - 4096 * 2325 == 7254016
                       and snap_right == 64 * 1771 and sample_agree)}


def s8_noninterference() -> Dict[str, object]:
    """S8: the carried fork's stages and its K4b figures are as recorded."""
    k4b = cf.k4b_soft(with_leech_decoder=False)
    return {"stages": cf.STAGES, "k4b_reads": k4b["reads"],
            "k4b_estimate_right": k4b["estimate_right"],
            "passed": (cf.STAGES == ("context", "second reading",
                                     "unsure set")
                       and k4b["reads"] == 768
                       and k4b["estimate_right"] == 512)}


def designed_substrate_report() -> Dict[str, object]:
    """S2-S8 against the marks of ``studies/DESIGNED_SUBSTRATE_STUDY.md``
    (S1 is the Lean build, pinned by the tests and the sign-off)."""
    s2 = s2_sender_tag()
    s3 = s3_constants()
    s4 = s4_soft_k4b()
    s5 = s5_soft_gentle()
    s6 = s6_extensions()
    s7 = s7_floor()
    s8 = s8_noninterference()
    control = closed_world_control()
    marks = {"S2": s2["passed"], "S3": s3["passed"], "S4": s4["passed"],
             "S5": s5["passed"], "S6": s6["passed"], "S7": s7["passed"],
             "S8": s8["passed"]}
    return {"S2": s2, "S3": s3, "S4": s4, "S5": s5, "S6": s6, "S7": s7,
            "S8": s8, "closed_world_control": control, "marks": marks,
            "met": sorted(k for k, v in marks.items() if v),
            "not_met": sorted(k for k, v in marks.items() if not v),
            "lean_file": LEAN_FILE}
