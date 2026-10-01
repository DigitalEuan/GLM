"""``glm_universal.reasoning.rate_posterior`` -- the rate read off the reads themselves.

The question
------------
Every confidence the decoder, the carried fork and the second reading give is
conditioned on a bit-flip rate the caller declares
(:mod:`glm_universal.reasoning.decoder_confidence`), and Phase 80 measured the
price of declaring it too low: a floor's promise broke in 30 of 210 cells.
The rate-posterior study (Phase 82) declared its marks J1-J9 before this
module existed; :mod:`glm_universal.reasoning.rate_posterior_marks` measures
them.

The object
----------
A declared grid of rates ``GRID`` (Phase 80's five and a guard at 1/5) with a
declared prior.  The likelihood of one read at rate ``p``, the truth summed out
over the 4096 codewords, is its coset mass over 4096 -- a function of the
read's coset weight alone (:func:`read_likelihood`); the likelihood of two
reads of one carrier is ``(1/4096) sum_c p^D(c) q^(48 - D(c))`` with ``D`` the
summed distance (:func:`pair_likelihood`, the sum of the agree-channel study).
The posterior over the grid is exact (:func:`rate_posterior`).

The **soft reading** answers what the reading answers -- the complete
decoder's value (:func:`decode_soft`) or ``agree``'s (:func:`agree_soft`) --
with its **marginal confidence**: Phase 77's confidence at each grid rate,
weighted by the posterior.  It refuses ``RATE_GRID_EXCEEDED`` when the guard
rate is (one of) the most probable, since the reads then say the rate may lie
above every rate a floor was hunted at; the soft floor refuses
``BELOW_FLOOR`` under a declared floor.

Exactness
---------
``int`` masks, ``int`` weights and :class:`fractions.Fraction` only.  No
float, no RNG.
"""

from __future__ import annotations

from fractions import Fraction
from functools import lru_cache
from typing import Dict, List, Optional, Sequence, Tuple

from ..substrate.golay_decode import decode_complete
from ..substrate.mog import GOLAY_MASKS
from . import law_absorption as la
from .confidence_floor import band, floor_check
from .decoder_confidence import ConfidenceRefusal, N, agree_confidence

__all__ = [
    "GRID", "GUARD", "PRIORS", "COSET_COUNTS", "ASSUMPTION",
    "coset_class_mass", "read_likelihood", "pair_likelihood",
    "rate_posterior", "most_probable", "decode_soft", "agree_soft",
    "decode_soft_floor",
]

#: The declared grid of rates: Phase 80's five and the guard.
GRID: Tuple[Fraction, ...] = (Fraction(1, 1000), Fraction(1, 100),
                              Fraction(1, 50), Fraction(1, 20),
                              Fraction(1, 10), Fraction(1, 5))
#: The guard point: a posterior most probable here is refused.
GUARD = Fraction(1, 5)
#: The declared priors: uniform (the one the runtime uses) and cautious
#: (weights proportional to the rate; for sensitivity only).
PRIORS: Dict[str, Tuple[Fraction, ...]] = {
    "uniform": tuple(Fraction(1, len(GRID)) for _ in GRID),
    "cautious": tuple(p / sum(GRID) for p in GRID),
}
#: How many cosets have each weight 0..4.
COSET_COUNTS: Tuple[int, ...] = (1, 24, 276, 2024, 1771)

ASSUMPTION = ("one unknown rate for every read of the call, from the declared "
              "grid under the uniform prior; each bit of each read flips "
              "independently; each carrier's truth equally likely a priori")


@lru_cache(maxsize=None)
def coset_class_mass(d: int, p: Fraction) -> Fraction:
    """``W_d(p) = sum_w A_w(d) p^w q^(24-w)``: the probability that the error
    lies in one given coset of weight ``d``."""
    q = 1 - p
    return sum((a * p ** w * q ** (N - w)
                for w, a in enumerate(la.coset_enumerator(d)) if a),
               Fraction(0))


def read_likelihood(y: int, p: Fraction) -> Fraction:
    """``P(y | p) = (1/4096) sum_c p^d(y,c) q^(24-d(y,c))`` -- the coset mass
    of ``y`` over 4096."""
    return coset_class_mass(decode_complete(y).weight, p) / len(GOLAY_MASKS)


def _summed_distance_histogram(y1: int, y2: int) -> Dict[int, int]:
    hist: Dict[int, int] = {}
    for c in GOLAY_MASKS:
        d = (y1 ^ c).bit_count() + (y2 ^ c).bit_count()
        hist[d] = hist.get(d, 0) + 1
    return hist


def pair_likelihood(y1: int, y2: int, p: Fraction,
                    hist: Optional[Dict[int, int]] = None) -> Fraction:
    """``P(y1, y2 | p) = (1/4096) sum_c p^D(c) q^(48-D(c))`` for two reads of
    one carrier."""
    if hist is None:
        hist = _summed_distance_histogram(y1, y2)
    q = 1 - p
    return sum((n * p ** d * q ** (2 * N - d) for d, n in hist.items()),
               Fraction(0)) / len(GOLAY_MASKS)


def rate_posterior(reads: Sequence[int] = (),
                   pairs: Sequence[Tuple[int, int]] = (),
                   prior: str = "uniform") -> Tuple[Fraction, ...]:
    """The exact posterior over ``GRID`` given single reads (each its own
    carrier) and pairs (two reads of one carrier)."""
    weights = PRIORS[prior]
    hists = [_summed_distance_histogram(a, b) for a, b in pairs]
    classes = [decode_complete(y).weight for y in reads]
    unnorm = []
    for w, p in zip(weights, GRID):
        x = w
        for d in classes:
            x *= coset_class_mass(d, p)
        for (a, b), h in zip(pairs, hists):
            x *= pair_likelihood(a, b, p, h)
        unnorm.append(x)
    total = sum(unnorm, Fraction(0))
    return tuple(x / total for x in unnorm)


def most_probable(post: Sequence[Fraction]) -> Tuple[Fraction, ...]:
    """Every grid rate of greatest posterior (ties kept)."""
    top = max(post)
    return tuple(p for p, x in zip(GRID, post) if x == top)


def _check_grid(post: Sequence[Fraction]) -> None:
    top = most_probable(post)
    if GUARD in top:
        raise ConfidenceRefusal(
            "RATE_GRID_EXCEEDED",
            f"the reads make the guard rate {GUARD} the most probable of the "
            f"declared grid (posterior {max(post)}): the rate may lie above "
            f"every rate a floor was hunted at, and underdeclaring it breaks "
            f"the floor's promise")


def _masks(xs: Sequence[object]) -> List[int]:
    out = []
    for x in xs:
        if isinstance(x, bool) or not isinstance(x, int) or not \
                0 <= x < (1 << N):
            raise ConfidenceRefusal("OUTSIDE_SUBSTRATE",
                                    f"{x!r} is not a 24-bit word")
        out.append(x)
    return out


def decode_soft(subject: int, corpus: Sequence[int] = ()
                ) -> Dict[str, object]:
    """The complete decoder's value for ``subject`` with its confidence
    marginalized over the rate posterior of the subject and the corpus."""
    subject, = _masks([subject])
    corpus = _masks(corpus)
    d = decode_complete(subject)
    if d.corrected is None:
        raise ConfidenceRefusal(
            "TIE", f"coset weight {d.weight}: {len(d.candidates)} codewords "
            f"are equally near and, at any rate, equally likely")
    post = rate_posterior([subject] + corpus)
    _check_grid(post)
    conf = sum((x * la.confidence(d.weight, p) for x, p in zip(post, GRID)),
               Fraction(0))
    return {"reading": "decoder, soft", "value": d.corrected,
            "coset_weight": d.weight, "reads": 1 + len(corpus),
            "posterior": post, "most_probable": most_probable(post),
            "confidence": conf, "band": band(conf),
            "assumption": ASSUMPTION}


def agree_soft(r1: int, r2: int, corpus: Sequence[int] = ()
               ) -> Dict[str, object]:
    """``agree``'s value for two reads of one carrier with its confidence
    marginalized over the rate posterior of the pair and the corpus."""
    r1, r2 = _masks([r1, r2])
    corpus = _masks(corpus)
    #  the reading's own refusals first (at any rate: the fork does not
    #  depend on the rate)
    agree_confidence([r1, r2], GRID[0])
    post = rate_posterior(corpus, [(r1, r2)])
    _check_grid(post)
    value = None
    conf = Fraction(0)
    for x, p in zip(post, GRID):
        r = agree_confidence([r1, r2], p)
        value = r["value"]
        conf += x * r["confidence"]
    return {"reading": "second reading, soft", "value": value,
            "reads": 2 + len(corpus), "posterior": post,
            "most_probable": most_probable(post), "confidence": conf,
            "band": band(conf), "assumption": ASSUMPTION}


def decode_soft_floor(t: object, subject: int, corpus: Sequence[int] = ()
                      ) -> Dict[str, object]:
    """:func:`decode_soft` answered only at a marginal confidence of at least
    ``t``; otherwise ``BELOW_FLOOR``."""
    t = floor_check(t)
    r = decode_soft(subject, corpus)
    if r["confidence"] < t:
        raise ConfidenceRefusal(
            "BELOW_FLOOR", f"the answer is the codeword sent with marginal "
            f"probability {r['confidence']} ({r['band']}), below the declared "
            f"floor {t}")
    out = dict(r)
    out["floor"] = t
    return out
