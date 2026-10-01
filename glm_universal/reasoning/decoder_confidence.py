"""``glm_universal.reasoning.decoder_confidence`` -- how likely an answer is.

The question
------------
Phase 75 absorbed two decoder laws as the ``confidence`` fact of
:mod:`glm_universal.reasoning.law_absorption`: a word decoded at distance
``d <= 3`` is the sent codeword with probability
``p^d q^(24-d) / sum_w A_w p^w q^(24-w)``, where ``A_w`` is the weight
enumerator of the received word's coset.  The GLM could say that number when
asked for it by distance, but not when it decoded: the complete decoder, the
carried fork's context stage (``resolve``) and the second reading (``agree``)
each reported an answer with no probability attached.
The decoder-confidence study (Phase 77) declared its marks C1-C6 before this
module existed; :mod:`glm_universal.reasoning.decoder_confidence_marks`
measures them.

The object
----------
A reading at a declared bit-flip rate ``p`` with ``0 < p < 1/2``.  The
likelihood of a candidate codeword ``c`` given reads ``r_1 .. r_m`` is
``prod_i p^d(r_i, c) q^(24 - d(r_i, c))``; the prior is uniform over the
candidates the reading allows -- every codeword for the decoder and the second
reading, the declared cases for the context stage (the closed world, which
every answer quotes).  The **confidence** of an answer is the posterior of the
answered codeword.  It is attached to a reading's own answer and refuses where
the reading refuses, by the same name.

Three computations, kept apart so that each checks another:

* :func:`decode_confidence` without cases takes the absorbed law, i.e. the
  coset weight enumerator (no codeword is visited);
* with cases, and in :func:`agree_confidence`, the posterior is computed in
  integers: at ``p = a/b`` the likelihood at distance ``d`` is proportional to
  ``a^d (b-a)^(24-d)``, so a posterior is a ratio of two integers;
* :func:`brute_posterior` is the check -- a direct ``Fraction`` sum of
  ``p^d q^(24-d)`` products over every allowed candidate.

The Lean half of the study proves what the numbers rest on: posteriors sum to one, restriction never lowers a survivor's posterior,
equal likelihoods give equal posteriors, and a survivor whose rivals are all
at least ``g`` further away has posterior at least
``1 / (1 + (k - 1)(p/q)^g)`` (``GLM.DecoderConfidence.fork_confidence_bound``).

Exactness
---------
``int`` masks, ``int`` weights and :class:`fractions.Fraction` only.  No
float, no RNG.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from ..substrate.golay_decode import decode_complete
from ..substrate.linalg import popcount
from ..substrate.mog import GOLAY_MASKS, GOLAY_SET
from . import carried_fork as cf
from . import law_absorption as la

__all__ = [
    "N", "RATES", "ConfidenceRefusal", "rate_check", "likelihood",
    "brute_posterior", "int_posterior", "int_weights", "decode_confidence",
    "agree_confidence", "fork_bound",
]

N = 24

#: The three declared bit-flip rates of the study.
RATES: Tuple[Fraction, ...] = (Fraction(1, 100), Fraction(1, 20),
                               Fraction(1, 10))

CLOSED_WORLD = cf.CLOSED_WORLD


class ConfidenceRefusal(ValueError):
    """A confidence that is not licensed, refused by name."""

    def __init__(self, name: str, reason: str):
        ValueError.__init__(self, f"{name}: {reason}")
        self.name = name
        self.reason = reason


# ===========================================================================
# 1.  THE LIKELIHOODS
# ===========================================================================

def rate_check(p: object) -> Fraction:
    """The declared rate as a ``Fraction`` in ``(0, 1/2)``, or a refusal."""
    if isinstance(p, bool) or not isinstance(p, (int, Fraction)):
        raise ConfidenceRefusal("RATE_OUT_OF_RANGE",
                                "the bit-flip rate must be an exact rational")
    p = Fraction(p)
    if not 0 < p < Fraction(1, 2):
        raise ConfidenceRefusal(
            "RATE_OUT_OF_RANGE",
            f"a bit-flip rate of {p} is outside (0, 1/2): at 0 nothing is "
            f"ever wrong and at 1/2 or above the nearer codeword is not the "
            f"more likely one")
    return p


def int_weights(p: Fraction) -> Tuple[int, ...]:
    """``a^d (b-a)^(24-d)`` for ``d = 0..24`` at ``p = a/b``: the likelihoods
    up to the common factor ``b^24``."""
    a, b = p.numerator, p.denominator
    return tuple(a ** d * (b - a) ** (N - d) for d in range(N + 1))


def likelihood(reads: Sequence[int], candidate: int, p: Fraction) -> Fraction:
    """``prod_i p^d(r_i, c) q^(24 - d(r_i, c))`` -- the check's likelihood."""
    q = 1 - p
    out = Fraction(1)
    for r in reads:
        d = popcount(r ^ candidate)
        out *= p ** d * q ** (N - d)
    return out


def brute_posterior(reads: Sequence[int], candidate: int,
                    allowed: Sequence[int], p: Fraction) -> Fraction:
    """The posterior of ``candidate`` among ``allowed``, by a direct
    ``Fraction`` sum over every allowed candidate (the check)."""
    total = sum((likelihood(reads, c, p) for c in allowed), Fraction(0))
    return likelihood(reads, candidate, p) / total


def int_posterior(reads: Sequence[int], candidate: int,
                   allowed: Sequence[int], weights: Sequence[int]) -> Fraction:
    """The same posterior, in integers over the joint distance census."""
    census: Dict[Tuple[int, ...], int] = {}
    for c in allowed:
        key = tuple(popcount(r ^ c) for r in reads)
        census[key] = census.get(key, 0) + 1

    def weight(key: Tuple[int, ...]) -> int:
        out = 1
        for d in key:
            out *= weights[d]
        return out

    total = sum(n * weight(key) for key, n in census.items())
    mine = weight(tuple(popcount(r ^ candidate) for r in reads))
    return Fraction(mine, total)


def fork_bound(k: int, gap: int, p: Fraction) -> Fraction:
    """``1 / (1 + (k - 1)(p/q)^gap)``: the proved floor on a survivor's
    posterior when its ``k - 1`` rivals are each at least ``gap`` further."""
    r = p / (1 - p)
    return 1 / (1 + (k - 1) * r ** gap)


# ===========================================================================
# 2.  THE CONFIDENCE OF A READING
# ===========================================================================

def _cases_check(cases: Sequence[int]) -> Tuple[int, ...]:
    out: List[int] = []
    for c in cases:
        if c not in GOLAY_SET:
            raise ConfidenceRefusal("OUTSIDE_SUBSTRATE",
                                    f"case {c} is not a Golay codeword")
        if c not in out:
            out.append(c)
    return tuple(out)


def decode_confidence(subject: int, p: object,
                      cases: Optional[Sequence[int]] = None
                      ) -> Dict[str, object]:
    """The decoding of ``subject`` with the probability that it is right.

    Without ``cases`` this is the complete decoder: a read at coset weight
    ``d <= 3`` decodes to one codeword, whose confidence is the absorbed law's
    ``confidence(d, p)``; at coset weight 4 six codewords are equally likely
    and the confidence refuses ``TIE``.  With ``cases`` it is the carried
    fork's context stage (``resolve``): the fork pruned to the declared cases
    under the closed world, and the survivor's posterior among the cases.
    """
    p = rate_check(p)
    if cases is None:
        d = decode_complete(subject)
        if d.corrected is None:
            raise ConfidenceRefusal(
                "TIE", f"coset weight {d.weight}: {len(d.candidates)} "
                f"codewords are equally near and, at any rate, equally "
                f"likely; no single decoding is licensed")
        return {"reading": "decoder", "value": d.corrected,
                "coset_weight": d.weight, "allowed": len(GOLAY_MASKS),
                "confidence": la.confidence(d.weight, p), "rate": p,
                "assumption": "each bit flips independently at the declared "
                              "rate; every codeword equally likely a priori"}
    declared = _cases_check(cases)
    fork = cf.carry(subject).restrict_to_cases(declared)
    if fork.status == "open":
        live = fork.live
        each = int_posterior((subject,), live[0], declared,
                              int_weights(p))
        raise ConfidenceRefusal(
            "AMBIGUOUS", f"{len(live)} candidates survive the declared cases, "
            f"each with posterior {each}")
    if fork.status == "contradicted":
        raise ConfidenceRefusal(
            "UNCORRECTABLE", "no candidate of the carried fork is a declared "
            "case")
    value = fork.value
    rivals = [c for c in declared if c != value]
    gap = (min(popcount(subject ^ c) for c in rivals)
           - popcount(subject ^ value)) if rivals else None
    return {"reading": "context", "value": value,
            "index": list(cases).index(value),
            "coset_weight": fork.weight, "allowed": len(declared),
            "confidence": int_posterior((subject,), value, declared,
                                         int_weights(p)),
            "gap": gap,
            "bound": (fork_bound(len(declared), gap, p)
                      if gap is not None else Fraction(1)),
            "rate": p, "assumption": CLOSED_WORLD}


def agree_confidence(reads: Sequence[int], p: object) -> Dict[str, object]:
    """The second reading of one carrier, with the probability that the
    agreed codeword is the carrier: the product of the reads' likelihoods,
    over every codeword."""
    p = rate_check(p)
    if not reads:
        raise ConfidenceRefusal("UNCORRECTABLE", "no read to agree on")
    fork = cf.carry(reads[0])
    for r in reads[1:]:
        fork = fork.intersect(cf.carry(r))
    weights = int_weights(p)
    if fork.status == "open":
        each = [int_posterior(reads, c, GOLAY_MASKS, weights)
                for c in fork.live]
        raise ConfidenceRefusal(
            "AMBIGUOUS", f"{len(fork.live)} candidates survive every read, "
            f"with posteriors {', '.join(str(x) for x in each)}")
    if fork.status == "contradicted":
        raise ConfidenceRefusal("UNCORRECTABLE",
                                "no candidate survives every read")
    return {"reading": "second reading", "value": fork.value,
            "reads": len(reads), "allowed": len(GOLAY_MASKS),
            "confidence": int_posterior(reads, fork.value, GOLAY_MASKS,
                                         weights),
            "rate": p,
            "assumption": "the reads are of one carrier, each bit of each "
                          "read flipping independently at the declared rate"}
