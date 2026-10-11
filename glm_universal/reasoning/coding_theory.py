"""``glm_universal.reasoning.coding_theory`` -- unique decodability, Kraft's
inequality, the rate-distortion function of a Hamming source and the rate
posterior of a binary symmetric channel, each derived rather than looked up
(Phase 107, ``studies/DERIVATION_TWO_STUDY.md``).

Unique decodability
-------------------
:func:`sardinas_patterson` decides whether a finite code is uniquely
decodable: the sets of *dangling suffixes* ``S_1, S_2, ...`` are built until
they repeat, and the code is uniquely decodable exactly when no codeword is
ever dangling.  :func:`ambiguous_string` searches the same states for the
shortest string with two parsings (a certificate of the refusal), and
:func:`kraft_sum` and :func:`canonical_prefix_code` give the other half of the
Kraft-McMillan theorem: every uniquely decodable code has Kraft sum at most
1 (McMillan; ``RequestProject/GLM/DerivationsTwo.lean`` proves it), and every
length vector with Kraft sum at most 1 has a prefix code (Kraft; the
canonical construction).

Rate distortion
---------------
:func:`hamming_rate_distortion` derives ``R(D)`` for a memoryless source on
``m`` symbols under Hamming distortion by the Shannon lower bound

    ``I(X; Xh) = H(X) - H(X | Xh) >= H(X) - H(X - Xh) >= H(X) - H(D) - D log(m - 1)``

(conditioning reduces entropy; the entropy of an error that is nonzero with
probability at most ``D <= 1 - 1/m`` is largest when it is uniform off zero)
and the backward test channel ``X = Xh + Z``: the reconstruction law
``q = p W^{-1}``, ``q_j = (p_j - D/(m-1))/(1 - m D/(m-1))``.  Where ``q`` is a
distribution the bound is met and is the function; that is the range
``D <= (m-1) min p``.  From ``D_max = 1 - max p`` on, ``R(D) = 0`` (send the
most probable symbol).  Between the two the bound is not met and the machine
refuses ``NOT_TIGHT`` rather than print a bound as the function.

The rate posterior
------------------
:func:`rate_posterior` is the posterior of a bit-flip rate after ``k`` flips
in ``n`` bits under a uniform prior: ``Beta(k+1, n-k+1)``, density
``(n+1)!/(k!(n-k)!) p^k (1-p)^(n-k)``, increasing on ``[0, k/n]``; and on the
machine's declared grid (:data:`glm_universal.reasoning.rate_posterior.GRID`)
the exact grid posterior and whether it peaks at the guard point.

Integers and ``Fraction`` only (D7); entropies are written as symbols.
"""

from __future__ import annotations

import heapq
import re
from dataclasses import dataclass, field
from fractions import Fraction
from math import factorial
from typing import Dict, List, Optional, Sequence, Tuple

__all__ = ["CodingError", "parse_code", "sardinas_patterson",
           "ambiguous_string", "kraft_sum", "canonical_prefix_code",
           "is_prefix_free", "parsings", "CodeVerdict", "decide_code",
           "RateDistortion", "hamming_rate_distortion", "binary_entropy_text",
           "Posterior", "rate_posterior"]


class CodingError(Exception):
    """A refusal, with the machine's code."""

    def __init__(self, code: str, why: str):
        super().__init__(f"{code}: {why}")
        self.code = code
        self.why = why


# ===========================================================================
# 1.  UNIQUE DECODABILITY
# ===========================================================================

def parse_code(text: str) -> Tuple[List[str], Optional[int]]:
    """``W1, W2, ... [over D symbols]`` -> codewords and the declared
    alphabet size."""
    d = None
    m = re.search(r"\bover\s+(\d+)\s+symbols?\s*$", text.strip())
    if m:
        d = int(m.group(1))
        text = text[:m.start()]
    words = [w.strip() for w in text.split(",")]
    if not words or any(not w for w in words):
        raise CodingError("UNREADABLE", "an empty codeword")
    if any(re.search(r"\s", w) for w in words):
        raise CodingError("UNREADABLE", "a codeword with a space in it")
    return words, d


def alphabet_size(words: Sequence[str], declared: Optional[int]) -> int:
    symbols = {ch for w in words for ch in w}
    d = max(2, len(symbols))
    if declared is not None:
        if declared < d:
            raise CodingError("UNREADABLE",
                              f"{len(symbols)} symbols used, {declared} "
                              f"declared")
        d = declared
    return d


def sardinas_patterson(words: Sequence[str]) -> Tuple[bool, List[List[str]]]:
    """``(uniquely decodable, [S_1, S_2, ...])``."""
    code = list(dict.fromkeys(words))
    if len(code) < len(words):
        return False, []
    cs = set(code)
    s1 = sorted({b[len(a):] for a in code for b in code
                 if a != b and b.startswith(a)})
    layers = [s1]
    seen = {frozenset(s1)}
    cur = set(s1)
    while cur:
        if cur & cs:
            return False, layers
        nxt = set()
        for x in cur:
            for c in code:
                if c.startswith(x) and c != x:
                    nxt.add(c[len(x):])
                if x.startswith(c) and c != x:
                    nxt.add(x[len(c):])
        key = frozenset(nxt)
        if key in seen:
            break
        seen.add(key)
        layers.append(sorted(nxt))
        cur = nxt
    return True, layers


def ambiguous_string(words: Sequence[str]
                     ) -> Optional[Tuple[str, List[str], List[str]]]:
    """The shortest string with two different parsings, as ``(string,
    parsing, parsing)``, or ``None``."""
    code = list(words)
    if len(set(code)) < len(code):
        w = next(x for x in code if code.count(x) > 1)
        return w, [w], [w]
    heap: List[Tuple[int, int, str, Tuple[str, ...], Tuple[str, ...]]] = []
    tick = 0
    for a in code:
        for b in code:
            if a != b and b.startswith(a):
                heapq.heappush(heap, (len(b), tick, b[len(a):], (a,), (b,)))
                tick += 1
    seen = set()
    while heap:
        length, _, dangling, behind, ahead = heapq.heappop(heap)
        if dangling in seen:
            continue
        seen.add(dangling)
        for c in code:
            if c == dangling:
                s = "".join(ahead)
                return s, list(behind) + [c], list(ahead)
            if dangling.startswith(c):
                heapq.heappush(heap, (length, tick, dangling[len(c):],
                                      behind + (c,), ahead))
            elif c.startswith(dangling):
                heapq.heappush(heap, (length + len(c) - len(dangling), tick,
                                      c[len(dangling):], ahead,
                                      behind + (c,)))
            tick += 1
    return None


def parsings(s: str, words: Sequence[str], limit: int = 2) -> int:
    """How many ways ``s`` splits into codewords (counted up to ``limit``)."""
    ways = [0] * (len(s) + 1)
    ways[0] = 1
    for i in range(len(s)):
        if ways[i]:
            for w in words:
                if s.startswith(w, i):
                    ways[i + len(w)] = min(limit, ways[i + len(w)] + ways[i])
    return ways[len(s)]


def kraft_sum(lengths: Sequence[int], d: int) -> Fraction:
    return sum((Fraction(1, d ** n) for n in lengths), Fraction(0))


def is_prefix_free(words: Sequence[str]) -> bool:
    return not any(a != b and b.startswith(a) for a in words for b in words) \
        and len(set(words)) == len(words)


def _digits(v: int, n: int, d: int) -> str:
    out = []
    for _ in range(n):
        v, r = divmod(v, d)
        out.append("0123456789abcdefghijklmnopqrstuvwxyz"[r])
    return "".join(reversed(out))


def canonical_prefix_code(lengths: Sequence[int], d: int = 2) -> List[str]:
    """The canonical prefix code with the given lengths (in the order
    given); refused ``KRAFT_VIOLATED`` when the Kraft sum exceeds 1."""
    if any(n < 1 for n in lengths):
        raise CodingError("UNREADABLE", "a length below 1")
    k = kraft_sum(lengths, d)
    if k > 1:
        raise CodingError("KRAFT_VIOLATED",
                          f"the Kraft sum is {k} > 1, so no prefix code -- "
                          f"and by McMillan no uniquely decodable code -- "
                          f"has these lengths")
    order = sorted(range(len(lengths)), key=lambda i: (lengths[i], i))
    out: Dict[int, str] = {}
    value, prev = 0, None
    for i in order:
        n = lengths[i]
        if prev is not None:
            value = (value + 1) * d ** (n - prev)
        out[i] = _digits(value, n, d)
        prev = n
    return [out[i] for i in range(len(lengths))]


@dataclass
class CodeVerdict:
    words: List[str]
    d: int
    unique: bool
    prefix_free: bool
    kraft: Fraction
    layers: List[List[str]]
    ambiguous: Optional[Tuple[str, List[str], List[str]]]
    prefix_code: Optional[List[str]]


def decide_code(text: str) -> CodeVerdict:
    words, declared = parse_code(text)
    d = alphabet_size(words, declared)
    ud, layers = sardinas_patterson(words)
    amb = None if ud else ambiguous_string(words)
    kraft = kraft_sum([len(w) for w in words], d)
    pc = canonical_prefix_code([len(w) for w in words], d) if ud else None
    return CodeVerdict(words, d, ud, is_prefix_free(words), kraft, layers,
                       amb, pc)


# ===========================================================================
# 2.  RATE DISTORTION UNDER HAMMING DISTORTION
# ===========================================================================

def binary_entropy_text(a: Fraction) -> str:
    """``H(a)`` with the argument folded to at most 1/2."""
    a = min(a, 1 - a)
    return f"H({a})"


@dataclass
class RateDistortion:
    source_text: str
    m: int
    probs: Optional[List[Fraction]]     # None for bernoulli(p) in a letter
    letter: Optional[str]
    function: str                       # R(D) on the tight range
    tight_end: str                      # D* (text)
    zero_from: str                      # D_max (text)
    gap: bool
    hx: str                             # H(X) as text
    channel: List[str]                  # q_j as texts
    tight_end_value: Optional[Fraction] = None
    zero_from_value: Optional[Fraction] = None


def _parse_source(spec: str) -> Tuple[int, Optional[List[Fraction]],
                                      Optional[str]]:
    spec = spec.strip()
    m = re.fullmatch(r"bernoulli\(\s*([^)]*)\)", spec, re.I)
    if m:
        a = m.group(1).strip()
        if re.fullmatch(r"\d+(?:/\d+)?", a):
            p = Fraction(a)
            if not 0 < p < 1:
                raise CodingError("UNREADABLE", "p must lie strictly between "
                                                "0 and 1")
            return 2, [1 - p, p], None
        if re.fullmatch(r"[A-Za-z_]\w*", a):
            return 2, None, a
        raise CodingError("UNREADABLE", f"cannot read bernoulli({a})")
    m = re.fullmatch(r"uniform\(\s*(\d+)\s*\)", spec, re.I)
    if m:
        k = int(m.group(1))
        if k < 2:
            raise CodingError("UNREADABLE", "a source of fewer than 2 symbols")
        return k, [Fraction(1, k)] * k, None
    m = re.fullmatch(r"\[([^\]]*)\]", spec)
    if m:
        try:
            ps = [Fraction(x.strip()) for x in m.group(1).split(",")]
        except ValueError:
            raise CodingError("UNREADABLE", f"cannot read {spec}")
        if sum(ps) != 1 or any(x <= 0 for x in ps) or len(ps) < 2:
            raise CodingError("UNREADABLE", "the probabilities must be "
                                            "positive and sum to 1")
        return len(ps), ps, None
    raise CodingError("UNREADABLE", f"cannot read the source {spec!r}")


def _dist_text(ps: Sequence[Fraction]) -> str:
    if len(set(ps)) == 1:
        return f"log2({len(ps)})"
    if len(ps) == 2:
        return binary_entropy_text(ps[1])
    return "H(" + ", ".join(str(x) for x in ps) + ")"


def _penalty(m: int) -> str:
    if m == 2:
        return ""
    if m == 3:
        return " - D"
    return f" - D*log2({m - 1})"


def hamming_rate_distortion(source: str, distortion: str = "hamming"
                            ) -> RateDistortion:
    if distortion.strip().lower() != "hamming":
        raise CodingError("UNSUPPORTED",
                          "only Hamming distortion is derived (the Shannon "
                          "lower bound with an additive test channel needs "
                          "a difference distortion)")
    m, ps, letter = _parse_source(source)
    if letter is not None:
        p = letter
        return RateDistortion(
            source, 2, None, p, f"H({p}) - H(D)", p, p, False, f"H({p})",
            [f"(1 - {p} - D)/(1 - 2*D)", f"({p} - D)/(1 - 2*D)"])
    pmin, pmax = min(ps), max(ps)
    tight = (m - 1) * pmin
    zero = 1 - pmax
    hx = _dist_text(ps)
    fn = f"{hx} - H(D){_penalty(m)}"
    chan = [f"({x} - D/{m - 1})/(1 - {m}*D/{m - 1})" if m > 2 else
            f"({x} - D)/(1 - 2*D)" for x in ps]
    return RateDistortion(source, m, list(ps), None, fn, str(tight),
                          str(zero), tight < zero, hx, chan, tight, zero)


# ===========================================================================
# 3.  THE RATE POSTERIOR OF A BINARY SYMMETRIC CHANNEL
# ===========================================================================

@dataclass
class Posterior:
    k: Optional[int]
    n: Optional[int]
    constant: str
    mode: str
    density: str
    grid: Optional[List[Tuple[Fraction, Fraction]]] = None   # (rate, mass)
    peak: Optional[Fraction] = None
    guard: Optional[Fraction] = None
    constant_value: Optional[int] = None


def rate_posterior(k: Optional[int], n: Optional[int],
                   on_grid: bool = False) -> Posterior:
    if k is None or n is None:
        return Posterior(None, None, "(n + 1)!/(k!*(n - k)!)", "k/n",
                         "(n + 1)!/(k!*(n - k)!)*p^k*(1 - p)^(n - k)")
    if k < 0 or n < 1 or k > n:
        raise CodingError("INCONSISTENT",
                          f"{k} flips cannot be observed in {n} bits")
    const = factorial(n + 1) // (factorial(k) * factorial(n - k))
    mode = Fraction(k, n)
    dens = f"{const}*p^{k}*(1 - p)^{n - k}"
    post = Posterior(k, n, str(const), str(mode), dens, constant_value=const)
    if on_grid:
        from .rate_posterior import GRID, GUARD
        lik = [p ** k * (1 - p) ** (n - k) for p in GRID]
        tot = sum(lik, Fraction(0))
        post.grid = [(p, x / tot) for p, x in zip(GRID, lik)]
        top = max(lik)
        post.peak = next(p for p, x in zip(GRID, lik) if x == top)
        post.guard = GUARD
    return post
