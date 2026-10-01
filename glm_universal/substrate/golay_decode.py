"""``glm_universal.substrate.golay_decode`` -- complete Golay decoding.

Why this module exists
----------------------
The package used to decode a corrupted 24-bit carrier by *snapping*: scan the
4,096 codewords, keep the first one at least Hamming distance.  That is the
legacy ``snap`` decode, and it has two defects, both of which this module
retires.

**Defect 1 -- order-dependent ties.**  At coset weight 4 the received word has
**six** nearest codewords, not one.  The scan returns whichever of them the
enumeration happened to reach first, with no signal that a choice was made.
The answer is then an artefact of codeword ordering rather than of the data.

**Defect 2 -- silent miscorrection at weight 5.**  A weight-5 error is *always*
decoded to the wrong codeword, by any nearest-codeword rule whatsoever.  This
is not a bug in the scan; it is a theorem about the code, and this module
proves it by computation rather than quoting it:

    the octads form a Steiner system ``S(5, 8, 24)`` -- every 5-subset of the
    24 points lies in exactly one octad --

so a weight-5 error ``e`` sits inside a unique octad ``O``, and ``e + O`` has
weight 3.  The received word is therefore at distance 3 from the *wrong*
codeword and at distance 5 from the right one; the nearest-codeword answer is
unique, confident and false.  :func:`steiner_system_report` verifies the
Steiner property over all 42,504 five-subsets, and
:func:`weight5_miscorrection_report` exhibits the consequence.

What replaces the snap
----------------------
:func:`decode_complete` -- a complete decoder driven by the syndrome coset
table, which returns

* the syndrome and the exact **coset weight**;
* **every** minimum-weight coset leader, not one of them;
* a status in ``{"codeword", "corrected", "ambiguous"}``;
* ``guaranteed``: whether the answer is inside the packing radius 3, where the
  code's correction is a *proof*.

No tie is ever broken silently: at coset weight 4 the status is ``ambiguous``,
``corrected`` is ``None`` and all six leaders are returned.  A caller that
wants a total function asks for one explicitly with :func:`decode_or_detect`,
which substitutes detection for a guess.

The coset table
---------------
Built once, by enumerating every error pattern of weight at most 4 -- 12,951
patterns over 4,096 cosets.  The resulting census

    ``1 + 24 + 276 + 2024 + 1771 = 4096``   cosets of weight ``0,1,2,3,4``

with the 1,771 weight-4 cosets carrying six leaders each
(``1771 * 6 = 10626 = C(24,4)``), is *computed* in :func:`coset_census`, not
asserted.

Everything here is exact integer arithmetic on 24-bit masks.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Dict, List, Optional, Sequence, Tuple

from .linalg import popcount
from .mog import GOLAY, GOLAY_MASKS, GOLAY_SET, OCTAD_MASKS

__all__ = [
    "N", "PACKING_RADIUS", "COVERING_RADIUS",
    "Decoding",
    "coset_table", "coset_leaders", "coset_weight", "coset_census",
    "decode_complete", "decode_or_detect", "is_guaranteed_decodable",
    "legacy_snap_decode", "decoder_comparison_report",
    "steiner_system_report", "weight5_miscorrection_report",
    "golay_decode_report",
]

N = 24

#: Errors of weight at most this are corrected, and the correction is a proof.
PACKING_RADIUS = 3

#: Every coset has a leader of weight at most this.
COVERING_RADIUS = 4


# ===========================================================================
# 1.  THE COSET LEADER TABLE
# ===========================================================================

_COSET_TABLE: Optional[Dict[int, Tuple[int, ...]]] = None


def coset_table() -> Dict[int, Tuple[int, ...]]:
    """``syndrome -> all minimum-weight coset leaders``, built once.

    Every error pattern of weight ``0..4`` is enumerated and filed under its
    syndrome; for each syndrome only the patterns of least weight are kept.
    The covering radius of the Golay code is 4, so this reaches every one of
    the 4,096 cosets -- which is checked here rather than assumed.
    """
    global _COSET_TABLE
    if _COSET_TABLE is not None:
        return _COSET_TABLE
    best: Dict[int, List[int]] = {}
    best_w: Dict[int, int] = {}
    for w in range(COVERING_RADIUS + 1):
        for support in combinations(range(N), w):
            mask = 0
            for i in support:
                mask |= 1 << i
            s = GOLAY.syndrome_int(mask)
            known = best_w.get(s)
            if known is None:
                best_w[s] = w
                best[s] = [mask]
            elif known == w:
                best[s].append(mask)
    if len(best) != 1 << 12:
        raise AssertionError(
            f"coset_table: reached {len(best)} cosets, expected 4096")
    _COSET_TABLE = {s: tuple(sorted(v)) for s, v in best.items()}
    return _COSET_TABLE


def coset_leaders(mask: int) -> Tuple[int, ...]:
    """Every minimum-weight coset leader of the coset containing ``mask``."""
    _check_mask(mask, "coset_leaders")
    return coset_table()[GOLAY.syndrome_int(mask)]


def coset_weight(mask: int) -> int:
    """Distance from ``mask`` to the code: the weight of its coset leaders."""
    return popcount(coset_leaders(mask)[0])


def coset_census() -> Dict[str, object]:
    """The distribution of cosets by leader weight, and the leader counts.

    Comes out as ``{0: 1, 1: 24, 2: 276, 3: 2024, 4: 1771}`` with a unique
    leader below weight 4 and exactly six at weight 4.
    """
    table = coset_table()
    by_weight: Dict[int, int] = {}
    leaders_by_weight: Dict[int, set] = {}
    for leaders in table.values():
        w = popcount(leaders[0])
        by_weight[w] = by_weight.get(w, 0) + 1
        leaders_by_weight.setdefault(w, set()).add(len(leaders))
    total_leaders = sum(len(v) for v in table.values())
    return {
        "cosets": len(table),
        "cosets_by_leader_weight": dict(sorted(by_weight.items())),
        "leader_counts_by_weight": {
            w: sorted(v) for w, v in sorted(leaders_by_weight.items())},
        "total_leaders": total_leaders,
        "unique_below_radius_4": all(
            v == {1} for w, v in leaders_by_weight.items() if w < 4),
        "sextet_at_radius_4": leaders_by_weight.get(4) == {6},
    }


# ===========================================================================
# 2.  THE COMPLETE DECODER
# ===========================================================================

@dataclass(frozen=True)
class Decoding:
    """The complete decoding of a 24-bit word.

    Attributes
    ----------
    received
        The word handed in.
    syndrome
        ``H . received`` packed into 12 bits.
    weight
        The coset weight: the exact Hamming distance from ``received`` to the
        code.
    leaders
        *Every* minimum-weight coset leader, sorted.  One below weight 4, six
        at weight 4.
    candidates
        The nearest codewords, one per leader, sorted.
    status
        ``"codeword"`` (weight 0), ``"corrected"`` (weight 1-3, unique) or
        ``"ambiguous"`` (weight 4, six equally near codewords).
    corrected
        The unique nearest codeword, or ``None`` when ``status`` is
        ``"ambiguous"``.  A tie is never broken here.
    guaranteed
        Whether the answer lies inside the packing radius, where the code's
        correction is a proof rather than a preference.
    """

    received: int
    syndrome: int
    weight: int
    leaders: Tuple[int, ...]
    candidates: Tuple[int, ...]
    status: str
    corrected: Optional[int]
    guaranteed: bool

    def as_dict(self) -> Dict[str, object]:
        """A JSON-friendly view."""
        return {
            "received": self.received,
            "syndrome": self.syndrome,
            "weight": self.weight,
            "leaders": list(self.leaders),
            "candidates": list(self.candidates),
            "status": self.status,
            "corrected": self.corrected,
            "guaranteed": self.guaranteed,
        }


def _check_mask(mask: int, where: str) -> None:
    if not isinstance(mask, int) or isinstance(mask, bool):
        raise TypeError(f"{where}: mask must be an int")
    if not 0 <= mask < (1 << N):
        raise ValueError(f"{where}: mask must be a 24-bit integer")


def decode_complete(mask: int) -> Decoding:
    """Complete syndrome decoding, with every tie reported and none broken."""
    _check_mask(mask, "decode_complete")
    syndrome = GOLAY.syndrome_int(mask)
    leaders = coset_table()[syndrome]
    weight = popcount(leaders[0])
    candidates = tuple(sorted(mask ^ e for e in leaders))
    if weight == 0:
        status, corrected = "codeword", mask
    elif len(leaders) == 1:
        status, corrected = "corrected", candidates[0]
    else:
        status, corrected = "ambiguous", None
    return Decoding(received=mask, syndrome=syndrome, weight=weight,
                    leaders=leaders, candidates=candidates, status=status,
                    corrected=corrected,
                    guaranteed=weight <= PACKING_RADIUS)


def decode_or_detect(mask: int) -> Tuple[Optional[int], str]:
    """``(codeword, status)``: a codeword only when one is forced.

    The total-function wrapper for callers that must not branch on a
    dataclass.  Returns ``(None, "ambiguous")`` rather than guessing.
    """
    d = decode_complete(mask)
    return d.corrected, d.status


def is_guaranteed_decodable(mask: int) -> bool:
    """Whether ``mask`` lies within the packing radius of the code."""
    return coset_weight(mask) <= PACKING_RADIUS


# ===========================================================================
# 3.  THE LEGACY SNAP, AND WHAT IT COST
# ===========================================================================

def legacy_snap_decode(mask: int) -> Tuple[int, int]:
    """The retired decoder: first codeword of least distance, by scan order.

    Kept **only** so that :func:`decoder_comparison_report` can measure what
    it used to get wrong.  Nothing in the package calls it to decode.
    """
    _check_mask(mask, "legacy_snap_decode")
    best_word, best_dist = 0, N + 1
    for word in GOLAY_MASKS:
        d = popcount(mask ^ word)
        if d < best_dist:
            best_dist, best_word = d, word
    return best_word, best_dist


def _deterministic_errors(weight: int, count: int) -> List[int]:
    """A deterministic, seed-free sample of ``count`` errors of ``weight``.

    Supports are taken at a fixed stride through the lexicographic order of
    ``C(24, weight)``, so the sample is a pure function of its arguments and
    the report is reproducible in a fresh interpreter.
    """
    if weight == 0:
        return [0]
    total = 1
    for i in range(weight):
        total = total * (N - i) // (i + 1)
    stride = max(1, total // count)
    out: List[int] = []
    for idx, support in enumerate(combinations(range(N), weight)):
        if idx % stride:
            continue
        mask = 0
        for i in support:
            mask |= 1 << i
        out.append(mask)
        if len(out) >= count:
            break
    return out


def decoder_comparison_report(weights: Sequence[int] = tuple(range(8)),
                              samples: int = 60) -> Dict[str, object]:
    """Legacy snap versus complete decoding, over a deterministic sweep.

    For each error weight, a fixed sample of errors is added to the zero
    codeword and both decoders are run.  Three counts are kept per weight:

    ``recovered``
        the decoder returned the transmitted codeword;
    ``silent_miscorrection``
        the decoder returned a *different* codeword and said nothing;
    ``flagged``
        the decoder declined to choose (complete decoder only).

    The legacy row never flags anything -- that is the whole point.
    """
    rows: List[Dict[str, object]] = []
    for w in weights:
        errors = _deterministic_errors(w, samples)
        legacy = {"recovered": 0, "silent_miscorrection": 0, "flagged": 0}
        complete = {"recovered": 0, "silent_miscorrection": 0, "flagged": 0}
        legacy_tie_broken = 0
        for e in errors:
            word, _ = legacy_snap_decode(e)
            if word == 0:
                legacy["recovered"] += 1
            else:
                legacy["silent_miscorrection"] += 1
            d = decode_complete(e)
            if len(d.leaders) > 1:
                legacy_tie_broken += 1
            if d.status == "ambiguous":
                complete["flagged"] += 1
            elif d.corrected == 0:
                complete["recovered"] += 1
            else:
                complete["silent_miscorrection"] += 1
        rows.append({
            "weight": w,
            "sampled": len(errors),
            "legacy": legacy,
            "complete": complete,
            "legacy_ties_broken_silently": legacy_tie_broken,
        })
    return {
        "rows": rows,
        "legacy_flags_nothing": all(r["legacy"]["flagged"] == 0
                                    for r in rows),
        "complete_never_wrong_within_radius": all(
            r["complete"]["silent_miscorrection"] == 0
            for r in rows if r["weight"] <= PACKING_RADIUS),
        "first_weight_with_legacy_error": next(
            (r["weight"] for r in rows
             if r["legacy"]["silent_miscorrection"]), None),
        "first_weight_flagged_by_complete": next(
            (r["weight"] for r in rows if r["complete"]["flagged"]), None),
    }


# ===========================================================================
# 4.  WHY WEIGHT 5 IS HOPELESS: THE STEINER SYSTEM S(5, 8, 24)
# ===========================================================================

def steiner_system_report() -> Dict[str, object]:
    """Verify ``S(5, 8, 24)``: every 5-subset lies in exactly one octad.

    Computed by marking the ``759 * C(8,5) = 42,504`` five-subsets covered by
    the octads and comparing with ``C(24,5) = 42,504``.  Equality of the two
    counts *with no repeats* is the Steiner property.
    """
    seen: Dict[Tuple[int, ...], int] = {}
    for octad in OCTAD_MASKS:
        points = [i for i in range(N) if (octad >> i) & 1]
        for sub in combinations(points, 5):
            seen[sub] = seen.get(sub, 0) + 1
    total_subsets = 1
    for i in range(5):
        total_subsets = total_subsets * (N - i) // (i + 1)
    multiplicities = sorted(set(seen.values()))
    return {
        "octads": len(OCTAD_MASKS),
        "five_subsets_covered": len(seen),
        "five_subsets_total": total_subsets,
        "multiplicities": multiplicities,
        "is_steiner_5_8_24": (len(seen) == total_subsets
                              and multiplicities == [1]),
    }


def weight5_miscorrection_report(samples: int = 200) -> Dict[str, object]:
    """Weight-5 errors are decoded confidently and wrongly, always.

    For each sampled weight-5 error ``e``: the unique octad through its
    support is located, the coset weight of ``e`` is computed, and the
    complete decoder is run.  The invariant checked is

        ``coset_weight(e) == 3``  and  ``decode_complete(e).corrected == O``

    where ``O`` is that octad -- so the decoder is inside its packing radius,
    reports ``guaranteed``, and is wrong.  No decoder can do better: the true
    error is at distance 5 and a strictly nearer codeword exists.
    """
    octad_of_five: Dict[int, int] = {}
    for octad in OCTAD_MASKS:
        points = [i for i in range(N) if (octad >> i) & 1]
        for sub in combinations(points, 5):
            key = 0
            for i in sub:
                key |= 1 << i
            octad_of_five[key] = octad
    errors = _deterministic_errors(5, samples)
    weights: Dict[int, int] = {}
    all_wrong = True
    all_confident = True
    all_octad = True
    witness: Optional[Dict[str, object]] = None
    for e in errors:
        d = decode_complete(e)
        weights[d.weight] = weights.get(d.weight, 0) + 1
        if d.corrected == 0:
            all_wrong = False
        if not d.guaranteed or d.status != "corrected":
            all_confident = False
        if d.corrected != octad_of_five[e]:
            all_octad = False
        if witness is None:
            witness = {
                "error": e,
                "coset_weight": d.weight,
                "decoded_to_octad": d.corrected,
                "distance_to_truth": 5,
                "status": d.status,
                "guaranteed": d.guaranteed,
            }
    return {
        "sampled": len(errors),
        "coset_weights": dict(sorted(weights.items())),
        "always_coset_weight_3": list(weights) == [3],
        "always_miscorrected": all_wrong,
        "always_inside_packing_radius": all_confident,
        "always_the_containing_octad": all_octad,
        "witness": witness,
        "explanation": (
            "Every 5-subset of the 24 points lies in exactly one octad "
            "(the Steiner system S(5,8,24)), so a weight-5 error is the "
            "complement, inside that octad, of a weight-3 error.  The "
            "received word is therefore at distance 3 from the octad and 5 "
            "from the truth: nearest-codeword decoding is unique, inside "
            "the packing radius, and wrong.  The remedy is not a better "
            "decoder but a declared radius -- callers that need certainty "
            "must bound the channel, not the search."),
    }


# ===========================================================================
# 5.  ONE REPORT
# ===========================================================================

def golay_decode_report() -> Dict[str, object]:
    """Everything this module knows, recomputed."""
    census = coset_census()
    comparison = decoder_comparison_report()
    steiner = steiner_system_report()
    weight5 = weight5_miscorrection_report(samples=100)
    return {
        "coset_census": census,
        "comparison": comparison,
        "steiner": steiner,
        "weight5": weight5,
        "packing_radius": PACKING_RADIUS,
        "covering_radius": COVERING_RADIUS,
        "codewords": len(GOLAY_SET),
        "silent_tie_breaking_retired": True,
    }
