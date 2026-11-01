"""Reference implementation of the recommended GLM substrate protocol.

Golay G24 substrate + triggered sextet mirror + soft (free) resolution.

This module is a plain-Python reference implementation (standard library only) of the
protocol recommended in ``glm_package/README.md``. It uses the same generator, the same
coset-leader order and the same tag masks as the Lean development in
``RequestProject/GLM/``, so the guarantees proved there apply to these objects. The Python
code itself is *not* formally verified: ``test_glm_substrate.py`` checks it against the proved
facts (exhaustively where that is cheap).

Conventions
-----------
* A 24-bit word is an ``int`` in ``[0, 2**24)``; bit ``j`` is coordinate ``j``.
* A message is an ``int`` in ``[0, 4096)``; bit ``i`` selects generator row ``i``.
* Soft values use BPSK: bit 0 is sent as ``+1.0``, bit 1 as ``-1.0`` (``phase`` in the Lean
  files). The hard decision of ``r[j]`` is bit 1 iff ``r[j] < 0``.

Proved facts this module relies on (Lean names, ``RequestProject/GLM/``)
----------------------------------------------------------------------
* ``golay_optimal``              : the syndrome decoder is optimal on the binary symmetric channel.
* ``golay_corrects_weight_le3``  : every corruption of weight <= 3 is corrected.
* ``golayTrigger_off_le3``, ``golayTrigger_on_4``, ``golayTrigger_error_only`` : the trigger.
* ``golay_triggered_candidates``, ``golay_triggered_candidates_dist`` : six candidates, pairwise 8 apart.
* ``golay_side_info_six_suffice``, ``golay_triggered_list_mirror`` : labels on demand.
* ``golay_batch_labels_suffice`` : m events share 6**m joint labels.
* ``golay_tag_upper``, ``golay_on_demand`` : the 7-bit sender tag.
* ``soft_certificate``, ``sqDist_flip_tetrad``, ``posterior_gate_silent_error_le`` : soft resolution.
"""

from __future__ import annotations

import math
from typing import Iterable, List, Optional, Sequence, Tuple

N = 24          # symbol length (bits)
K = 12          # payload (bits)
NUM_WORDS = 1 << K

# --- the code -----------------------------------------------------------------------------

#: QR generator polynomial of the [23,12,7] Golay code, x^11+x^9+x^7+x^6+x^5+x+1 (Golay.lean).
GEN_POLY = (1 << 11) | (1 << 9) | (1 << 7) | (1 << 6) | (1 << 5) | (1 << 1) | 1
#: Generator rows: g(x) * x^i plus the overall parity bit 23 (``golayRowMask``).
ROWS: Tuple[int, ...] = tuple((GEN_POLY << i) | (1 << 23) for i in range(K))
#: The seven tag masks of ``golayTagMask`` (Tag.lean).
TAG_MASKS: Tuple[int, ...] = (7869672, 12267227, 14636573, 16216258, 4298017, 4882549, 11591092)


def weight(x: int) -> int:
    """Hamming weight."""
    return bin(x).count("1")


def parity(x: int) -> int:
    return weight(x) & 1


def encode(m: int) -> int:
    """Linear encoder F_2^12 -> F_2^24 (``golayEncode``)."""
    c = 0
    for i in range(K):
        if (m >> i) & 1:
            c ^= ROWS[i]
    return c


CODE: Tuple[int, ...] = tuple(encode(m) for m in range(NUM_WORDS))
_MESSAGE_OF = {c: m for m, c in enumerate(CODE)}


def message_of(c: int) -> int:
    """Inverse of :func:`encode` on codewords (raises ``KeyError`` on non-codewords)."""
    return _MESSAGE_OF[c]


def syndrome(y: int) -> int:
    """12-bit syndrome; bit i is <row_i, y> (``golaySyndrome``; G24 is self-dual)."""
    s = 0
    for i in range(K):
        if parity(ROWS[i] & y):
            s |= 1 << i
    return s


def _low_weight_masks() -> List[int]:
    """All words of weight <= 4 in the same order as ``lowWeightMasks`` (Golay.lean)."""
    out = [0]
    out += [1 << a for a in range(24)]
    out += [(1 << a) | (1 << b) for a in range(24) for b in range(a)]
    out += [(1 << a) | (1 << b) | (1 << c) for a in range(24) for b in range(a) for c in range(b)]
    out += [(1 << a) | (1 << b) | (1 << c) | (1 << d)
            for a in range(24) for b in range(a) for c in range(b) for d in range(c)]
    return out


def _build_tables() -> Tuple[List[int], List[List[int]]]:
    leader = [-1] * NUM_WORDS
    low: List[List[int]] = [[] for _ in range(NUM_WORDS)]   # words of weight <= 4 per coset
    for v in _low_weight_masks():
        s = syndrome(v)
        if leader[s] < 0:
            leader[s] = v
        low[s].append(v)
    assert all(v >= 0 for v in leader)
    return leader, low


#: ``LEADER[s]``: first minimum-weight word with syndrome ``s`` (same order as ``leaderTable``).
#: ``_LOW[s]``: every word of weight <= 4 with syndrome ``s``.
LEADER, _LOW = _build_tables()

# --- decoding and the trigger -------------------------------------------------------------


def is_triggered_syndrome(s: int) -> bool:
    """The trigger: the coset leader has weight 4 (``golayTrigger``)."""
    return weight(LEADER[s]) == 4


def sextet(s: int) -> Tuple[int, ...]:
    """For a triggered syndrome: its six disjoint tetrads, sorted (canonical label order).

    For a non-triggered syndrome: the single coset leader.
    """
    if is_triggered_syndrome(s):
        tet = tuple(sorted(v for v in _LOW[s] if weight(v) == 4))
        assert len(tet) == 6
        return tet
    return (LEADER[s],)


def hard_decode(y: int) -> Tuple[int, bool]:
    """Syndrome decoder (``golayDecode``) plus the trigger flag.

    Returns ``(codeword, triggered)``. If ``triggered`` is ``False`` the codeword is within
    distance 3 of ``y`` and is correct whenever at most 3 bits were flipped. If ``True``, ``y``
    is at distance exactly 4 from six codewords and the returned one is only one of them.
    """
    s = syndrome(y)
    return y ^ LEADER[s], is_triggered_syndrome(s)


def candidates(y: int) -> Tuple[int, ...]:
    """The codewords within distance 4 of ``y``, in canonical label order.

    One codeword if the trigger is off, six (pairwise at distance 8) if it is on.
    """
    return tuple(y ^ t for t in sextet(syndrome(y)))

# --- the mirror: labels that depend on the corruption -------------------------------------


def mirror_label(error: int) -> int:
    """Corruption-aware label in {0..5}: the position of the error tetrad in its sextet.

    Defined for corruptions of weight <= 4. Returns 0 when no label is needed (trigger off),
    so nothing has to be sent below the threshold. Depends only on the error, never on the
    message (``golayTrigger_error_only``).
    """
    if weight(error) > 4:
        raise ValueError("the mirror is specified for corruptions of weight <= 4")
    tet = sextet(syndrome(error))
    return tet.index(error) if len(tet) == 6 else 0


def list_label(error: int, num_labels: int) -> int:
    """Label for a K-label on-demand mirror: which block of ceil(6/K) candidates holds the truth."""
    if num_labels < 1:
        raise ValueError("num_labels must be >= 1")
    block = math.ceil(6 / num_labels)
    return mirror_label(error) // block


def resolve_with_label(y: int, label: int, num_labels: int = 6) -> Tuple[int, ...]:
    """Receiver side of the on-demand mirror (``golay_triggered_list_mirror``).

    Returns a list of codewords that contains the transmitted one for every corruption of
    weight <= 4. Its length is 1 if the trigger is off and at most ceil(6/num_labels) if it is
    on; with ``num_labels = 6`` it is always a single codeword. No K-label scheme can guarantee
    shorter lists (``golay_triggered_list_lower``).
    """
    cand = candidates(y)
    if len(cand) == 1:
        return cand
    block = math.ceil(6 / num_labels)
    return cand[label * block:(label + 1) * block]


def batch_labels(labels: Sequence[int]) -> int:
    """Pack m six-way labels into one integer in [0, 6**m) (``golay_batch_labels_suffice``).

    Bits needed: ``batch_bits(m)``; e.g. 5 events fit in 13 bits.
    """
    v = 0
    for lab in reversed(labels):
        if not 0 <= lab < 6:
            raise ValueError("labels must lie in 0..5")
        v = 6 * v + lab
    return v


def unbatch_labels(v: int, m: int) -> List[int]:
    out = []
    for _ in range(m):
        out.append(v % 6)
        v //= 6
    return out


def batch_bits(m: int) -> int:
    """Smallest number of bits holding 6**m values."""
    return (6 ** m - 1).bit_length()

# --- the sender tag: clarification from a sender who does not know the error --------------


def tag(c: int) -> int:
    """The proved 7-bit linear tag of a codeword (``golayTag``): seven parities."""
    t = 0
    for k, mask in enumerate(TAG_MASKS):
        if parity(mask & c):
            t |= 1 << k
    return t


def resolve_with_tag(y: int, t: int) -> int:
    """Recover the codeword from ``y`` and the sender's 7-bit tag (``golay_tag_upper``).

    Correct for every corruption of weight <= 4. Golay needs at least 86 tag values for this
    (``golay_tag_lower``), so 7 bits is the fewest whole bits possible.
    """
    hits = [c for c in candidates(y) if tag(c) == t]
    if len(hits) != 1:
        raise ValueError("tag does not match exactly one candidate (more than 4 flips?)")
    return hits[0]

# --- soft information: resolving the ambiguous space for free -----------------------------


def bpsk(c: int) -> List[float]:
    """The +-1 embedding (bit 0 -> +1.0)."""
    return [-1.0 if (c >> j) & 1 else 1.0 for j in range(N)]


def hard_decision(r: Sequence[float]) -> int:
    y = 0
    for j, x in enumerate(r):
        if x < 0:
            y |= 1 << j
    return y


def sq_dist(r: Sequence[float], c: int) -> float:
    """Squared Euclidean distance between ``r`` and ``bpsk(c)``."""
    return sum((x - (-1.0 if (c >> j) & 1 else 1.0)) ** 2 for j, x in enumerate(r))


def least_reliable_tetrad(r: Sequence[float]) -> int:
    """Among the candidates of the hard decision, the one nearest to ``r``.

    Flipping a tetrad ``t`` of the hard decision changes the squared distance by
    ``4 * sum(|r_j| for j in t)`` (``sqDist_flip_tetrad``), so the nearest candidate is the one
    whose tetrad has the smallest total reliability. No label is used.
    """
    y = hard_decision(r)
    s = syndrome(y)

    def cost(t: int) -> float:
        return sum(abs(r[j]) for j in range(N) if (t >> j) & 1)

    return y ^ min(sextet(s), key=cost)


#: Radius of the proved free-resolution certificate (``soft_certificate``; sharp).
CERTIFICATE_RADIUS_SQ = 8.0


def certified(r: Sequence[float], c: int) -> bool:
    """True iff ``||r - bpsk(c)||^2 < 8``: then ``c`` is the unique nearest codeword."""
    return sq_dist(r, c) < CERTIFICATE_RADIUS_SQ


def posterior(r: Sequence[float], c: int, sigma: float,
              pool: Optional[Iterable[int]] = None) -> float:
    """Posterior probability of codeword ``c`` under AWGN with std ``sigma`` and a uniform prior.

    ``P(c | r)`` is a softmax of ``<r, bpsk(c')> / sigma**2`` over ``pool``. With
    ``pool=None`` all 4096 codewords are used (the exact posterior). Passing the six candidates
    is cheaper but overestimates the posterior, so use it only with a safety margin.
    """
    words = CODE if pool is None else tuple(pool)
    inv = 1.0 / (sigma * sigma)

    def score(w: int) -> float:
        return inv * sum(-x if (w >> j) & 1 else x for j, x in enumerate(r))

    scores = [score(w) for w in words]
    top = max(scores)
    z = sum(math.exp(v - top) for v in scores)
    return math.exp(score(c) - top) / z

# --- the full receiver --------------------------------------------------------------------


def receive_soft(r: Sequence[float], sigma: Optional[float] = None,
                 epsilon: float = 1e-2) -> Tuple[int, str]:
    """Receiver of the recommended protocol for one soft symbol.

    Returns ``(codeword, status)`` with status

    * ``"clean"``      trigger off: syndrome decision accepted (never wrong for <= 3 flips);
    * ``"certified"``  trigger on, least reliable tetrad accepted by the proved certificate;
    * ``"gated"``      trigger on, accepted because its posterior is >= 1 - epsilon
                       (silent errors <= epsilon of accepted cases,
                       ``posterior_gate_silent_error_le``);
    * ``"ask"``        a label is needed; the codeword returned is only the best guess. Request
                       ``mirror_label`` (3 bits), a ``list_label``, or the 7-bit ``tag``.

    The posterior gate is used only when ``sigma`` (the noise level) is supplied.
    """
    y = hard_decision(r)
    c, triggered = hard_decode(y)
    if not triggered:
        return c, "clean"
    best = least_reliable_tetrad(r)
    if certified(r, best):
        return best, "certified"
    if sigma is not None and posterior(r, best, sigma) >= 1.0 - epsilon:
        return best, "gated"
    return best, "ask"


__all__ = [
    "N", "K", "ROWS", "TAG_MASKS", "CODE", "LEADER",
    "weight", "encode", "message_of", "syndrome", "hard_decode", "is_triggered_syndrome",
    "sextet", "candidates", "mirror_label", "list_label", "resolve_with_label",
    "batch_labels", "unbatch_labels", "batch_bits", "tag", "resolve_with_tag",
    "bpsk", "hard_decision", "sq_dist", "least_reliable_tetrad", "certified",
    "CERTIFICATE_RADIUS_SQ", "posterior", "receive_soft",
]
