"""``glm_universal.reasoning.law_absorption`` -- the UBP laws, absorbed.

What this module is
-------------------
Phase 74 (:mod:`glm_universal.reasoning.law_register`) tested the 65 retained
UBP laws.  This module is the other half the owner asked for: each law taken
on its own, improved where it can be, and **absorbed** where it is of real
use -- not as a register the GLM consults, but as things the GLM can now
compute and say about its own substrate.

Every law gets one fate (:data:`FATES`, :data:`ABSORPTION`):

* **absorbed** -- the corrected law is a *fact* (:data:`FACTS`) computed live
  from the running substrate whenever it is asked, and the answer cites the
  law as its provenance.  Eleven laws: the eight structural ones, the two
  overclaims in their corrected form, and the hardened-storage law in its
  corrected form.
* **already GLM** -- a definition the GLM already runs on (the read quantum
  ``Y``, the shell-0 tax).
* **retested** -- a unit-bound law whose dimensionless content could be
  extracted, re-run through Phase 74's look-elsewhere test (:func:`retests`).
* **retired** -- nothing usable at GLM resolution; the reason is named.

The facts are reached from ``GLM.py --ask`` through the typed planner's
``substrate`` frame (:func:`read_question`, wired in
:mod:`glm_universal.runtime.semantic_plan`).  A question that names the
substrate and has one of the declared shapes is read; anything else is left
alone, so no existing verdict moves.

``RequestProject/GLM/LawAbsorption.lean`` proves the two corrections this
module relies on: the right-probability of complete decoding is below 1 at
every bit-flip rate strictly between 0 and 1 (the storage law corrected), and
below rate 1/2 the unique coset leader is strictly the most probable error of
its coset while equal-weight leaders are equally probable (the decoder's
confidence, and why a six-way tie is refused).

Everything is exact ``int`` / ``Fraction`` arithmetic (D7); no float is
constructed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from ..derived import memo
from ..substrate import golay_decode, mog
from ..substrate.linalg import popcount
from . import coherence
from . import law_register as lr

__all__ = [
    "FATES", "ABSORPTION", "FACTS", "Fact", "FactRefusal", "fact_value",
    "read_question", "answer_question", "coset_enumerator", "confidence",
    "brute_confidence", "RETESTS", "retests", "fate_census",
    "law_absorption_report", "tool_summary", "LEAN_FILE", "LEAN_THEOREMS",
    "brute_checks", "planner_path",
]

N = 24
LEAN_FILE = "RequestProject/GLM/LawAbsorption.lean"

FATES = ("absorbed", "already GLM", "retested", "retired")


# ===========================================================================
# 1.  THE FACTS -- each computed from the substrate when asked
# ===========================================================================

class FactRefusal(ValueError):
    """A fact asked outside its domain; ``name`` is the declared refusal."""

    def __init__(self, name: str, reason: str) -> None:
        super().__init__(f"{name}: {reason}")
        self.name = name
        self.reason = reason


@dataclass(frozen=True)
class Fact:
    """One absorbed law, as a computation over the substrate."""

    key: str
    laws: Tuple[str, ...]
    says: str
    compute: Callable[..., Tuple[str, str]]


def _code() -> "mog.GolayCode":
    return mog.GolayCode()


@memo
def _weight_distribution() -> Tuple[int, ...]:
    counts = [0] * (N + 1)
    for c in _code().codeword_masks:
        counts[popcount(c)] += 1
    return tuple(counts)


def _binom(n: int, r: int) -> int:
    return lr._binom(n, r)


def _decimal(q: Fraction, places: int) -> str:
    """Truncated toward zero, as Phase 74 displays its figures."""
    return lr._decimal(q, places)


def _round(q: Fraction, places: int) -> str:
    """``q`` rounded half-even to ``places`` decimals, by integer work."""
    scaled = Fraction(q) * 10 ** places
    n, r = divmod(scaled.numerator, scaled.denominator)
    if 2 * r > scaled.denominator or (2 * r == scaled.denominator and n % 2):
        n += 1
    sign = "-" if n < 0 else ""
    digits = str(abs(n)).rjust(places + 1, "0")
    return f"{sign}{digits[:-places]}.{digits[-places:]}" if places else sign + digits


def _rate_check(p: Fraction) -> Fraction:
    p = Fraction(p)
    if not 0 <= p <= 1:
        raise FactRefusal("NOT_A_PROBABILITY",
                          f"a bit-flip rate of {p} is not in [0, 1]")
    return p


def _weight_check(k: int, what: str) -> int:
    if not 0 <= k <= N:
        raise FactRefusal("WEIGHT_OUT_OF_RANGE",
                          f"{what} {k} is not in 0..24: a Golay word has 24 "
                          f"bits")
    return k


def _f_codewords() -> Tuple[str, str]:
    n = len(_code().codeword_masks)
    return str(n), (f"{n} -- counted over the substrate's codeword masks "
                    f"(2^12: twelve information bits of 24)")


def _f_rate() -> Tuple[str, str]:
    n = len(_code().codeword_masks)
    k = n.bit_length() - 1
    rate = Fraction(k, N)
    return str(rate), (f"{rate} -- {n} = 2^{k} codewords of length {N}: "
                       f"{k} information and {N - k} parity bits per word")


def _f_weight_count(weight: int) -> Tuple[str, str]:
    _weight_check(weight, "a codeword weight of")
    n = _weight_distribution()[weight]
    dist = ", ".join(f"{w}: {c}" for w, c in enumerate(_weight_distribution())
                     if c)
    return str(n), (f"{n} codewords of weight {weight} -- counted over the "
                    f"4096 codewords (weight distribution {dist})")


def _f_min_distance() -> Tuple[str, str]:
    d = min(w for w, c in enumerate(_weight_distribution()) if w and c)
    return str(d), (f"{d} -- the least weight of a nonzero codeword, which is "
                    f"the minimum distance because the code is linear "
                    f"(Lean: golay_min_distance_eight)")


def _f_covering_radius() -> Tuple[str, str]:
    table = golay_decode.coset_table()
    r = max(popcount(leaders[0]) for leaders in table.values())
    ties = sum(1 for leaders in table.values() if len(leaders) > 1)
    return str(r), (f"{r} -- the heaviest coset leader over all 4096 cosets; "
                    f"the {ties} cosets of weight {r} each have six nearest "
                    f"codewords (Lean: covering_radius_eq_four)")


def _outcome_row(k: int) -> Dict[str, int]:
    return lr.decoder_outcomes()["by_weight"][k]


def _f_corrects() -> Tuple[str, str]:
    t = max(k for k in range(N + 1)
            if all(_outcome_row(j)["right"] == _binom(N, j)
                   for j in range(k + 1)))
    return str(t), (f"{t} -- complete decoding corrects every error pattern "
                    f"of at most {t} bit flips and fails on some of "
                    f"{t + 1} (Lean: unique_leader_iff)")


def _f_outcome(k: int) -> Tuple[str, str]:
    _weight_check(k, "an error weight of")
    row = _outcome_row(k)
    total = _binom(N, k)
    if row["right"] == total:
        verdict = "right"
    elif row["refused"] == total:
        verdict = "refused"
    elif row["wrong"] == total:
        verdict = "wrong"
    else:
        verdict = "mixed"
    lead = {"right": "every such error is corrected",
            "refused": "every such error lands on a six-way tie and the "
                       "decoder refuses rather than guess",
            "wrong": "every such error is miscorrected to a different "
                     "codeword, silently" + (
                         " (an odd number of flips is never refused: every "
                         "codeword has even weight, so the six-way ties are "
                         "reached only by even errors; Lean: "
                         "odd_heavy_miscorrected)" if k % 2 else ""),
            "mixed": "some such errors are refused and the rest are "
                     "miscorrected"}[verdict]
    return verdict, (f"{verdict}: {lead} -- of the {total} patterns of {k} "
                     f"flips, {row['right']} right, {row['refused']} refused, "
                     f"{row['wrong']} wrong (from the coset weight "
                     f"enumerators)")


def _exact(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 \
        else f"{value.numerator}/{value.denominator}"


def _f_probability(which: str, p: Fraction) -> Tuple[str, str]:
    p = _rate_check(p)
    value = lr.outcome_probabilities(p)[which]
    return _exact(value), (
        f"{_round(value, 7)} (rounded to 7 places from the exact rational) "
        f"-- the probability that complete decoding is {which} when each of "
        f"the 24 bits flips independently with probability {p}")


def _f_always_right(p: Fraction) -> Tuple[str, str]:
    p = _rate_check(p)
    right = lr.outcome_probabilities(p)["right"]
    if right == 1:
        return "True", (f"True -- at bit-flip rate {p} no bit ever flips, so "
                        f"decoding is right with probability 1")
    return "False", (f"False -- at bit-flip rate {p} complete decoding is "
                     f"right with probability {_round(right, 7)}, not 1; "
                     f"it is right with probability 1 only at rate 0 (Lean: "
                     f"right_prob_lt_one). What does hold without exception: "
                     f"every pattern of at most 3 flips per word is corrected")


def coset_enumerator(d: int) -> Tuple[int, ...]:
    """Weights of the words of a coset whose leader has weight ``d`` (0..4)."""
    return tuple(lr.coset_enumerators()["enumerators"][d])


def confidence(d: int, p: Fraction) -> Fraction:
    """The probability that a unique decoding at distance ``d`` is the sent
    codeword, each bit flipping independently at rate ``p`` (uniform prior).

    The received word's coset holds every error that could have produced it;
    the decoded codeword is right exactly when the error was the leader, so the
    posterior is ``p^d q^(24-d)`` over the coset's weight enumerator.
    """
    p = _rate_check(p)
    if d == 4:
        raise FactRefusal("TIE", "at distance 4 six codewords are equally "
                          "near and, by the proved symmetry, equally "
                          "probable; no single decoding is licensed")
    if not 0 <= d <= 3:
        raise FactRefusal("BEYOND_COVERING_RADIUS",
                          f"no 24-bit word lies at distance {d} from the "
                          f"code: the covering radius is 4")
    q = 1 - p
    enum = coset_enumerator(d)
    total = sum(a * p ** w * q ** (N - w) for w, a in enumerate(enum) if a)
    if total == 0:
        raise FactRefusal("NOT_A_PROBABILITY",
                          f"at rate {p} a word at distance {d} cannot occur")
    return p ** d * q ** (N - d) / total


def brute_confidence(received: int, p: Fraction) -> Fraction:
    """The same posterior, by summing over all 4096 codewords (the check)."""
    p, q = Fraction(p), 1 - Fraction(p)
    code = _code()
    weights = [p ** popcount(received ^ c) * q ** (N - popcount(received ^ c))
               for c in code.codeword_masks]
    decoded = golay_decode.decode_complete(received).corrected
    assert decoded is not None
    mine = p ** popcount(received ^ decoded) * q ** (N - popcount(received ^ decoded))
    return mine / sum(weights)


def _f_confidence(d: int, p: Fraction) -> Tuple[str, str]:
    value = confidence(d, p)
    return _exact(value), (
        f"{_round(value, 7)} (rounded to 7 places) -- a word decoded at "
        f"distance {d} is the sent codeword with this probability at "
        f"bit-flip rate {p}: its coset's weight enumerator "
        f"{[(w, a) for w, a in enumerate(coset_enumerator(d)) if a]} weighs "
        f"every error that could have produced it, and the leader is the "
        f"most probable of them (Lean: leader_most_likely)")


def _f_unique_fraction() -> Tuple[str, str]:
    table = golay_decode.coset_table()
    unique = sum(1 for leaders in table.values() if len(leaders) == 1)
    frac = Fraction(unique * len(_code().codeword_masks), 2 ** N)
    return str(frac), (f"{frac} = {_round(frac, 4)} -- {unique} of the "
                       f"{len(table)} cosets have a unique leader; the other "
                       f"{len(table) - unique} tie six ways (Lean: "
                       f"unique_vs_ambiguous)")


def _f_perfect(length: int) -> Tuple[str, str]:
    n_code = len(_code().codeword_masks)
    radius = 3
    ball = sum(_binom(length, i) for i in range(radius + 1))
    perfect = n_code * ball == 2 ** length
    return str(perfect), (
        f"{perfect} -- {n_code} codewords x {ball} words within distance "
        f"{radius} = {n_code * ball}, against 2^{length} = {2 ** length}"
        + ("; the balls tile the space exactly (Lean: "
           "golay23_perfect_arithmetic)" if perfect else
           "; the rest lie at distance 4, on six-way ties"))


def _f_kissing() -> Tuple[str, str]:
    from ..substrate import leech_construct as lc
    shapes = lc.minimal_shape_census("C")
    total = sum(shapes.values())
    parts = " + ".join(f"{v} {k}" for k, v in shapes.items())
    return str(total), (f"{total} = {parts} -- enumerated from the "
                        f"substrate's Leech construction (Lean: "
                        f"leechMinimalClass_counts)")


def _f_closure(op: str) -> Tuple[str, str]:
    if op == "xor":
        return "always", ("always -- the code is linear, so the XOR of two "
                          "codewords is a codeword (Lean: xor_closed)")
    census = lr.closure_census()
    ok = census["and_codeword" if op == "and" else "or_codeword"]
    pairs = census["octad_pairs"]
    return "not always", (
        f"not always -- of the {pairs} pairs of distinct octads only {ok} "
        f"(the disjoint ones) give a codeword under {op.upper()} (Lean: "
        f"{op}_not_closed); only XOR is a code operation, so Boolean logic is "
        f"not isomorphic to arithmetic on the code")


def _f_descent() -> Tuple[str, str]:
    check = lr.descent_check()
    return str(check["holds"]), (
        f"{check['holds']} -- {check['trapped']} of the 4096 cosets have no "
        f"improving-flip descent as short as their distance "
        f"({', '.join(f'{v} at distance {k[0]} need {k[2:]} flips' for k, v in check['joint'].items())}); "
        f"flipping the coset leader's own bits reaches the nearest codeword "
        f"in d steps, which is the decoder, not a descent (Lean: "
        f"relaxation_is_not_decoding)")


FACTS: Dict[str, Fact] = {f.key: f for f in (
    Fact("codewords", ("LAW_COMP_009",), "the number of codewords",
         _f_codewords),
    Fact("rate", ("LAW_COMP_009",), "the information rate", _f_rate),
    Fact("weight-count", ("LAW_RELATION_ORTHO_001",),
         "the codewords of a given weight", _f_weight_count),
    Fact("min-distance", ("LAW_RELATION_002",), "the minimum distance",
         _f_min_distance),
    Fact("covering-radius", ("LAW_FOURTH_FLIP_001",), "the covering radius",
         _f_covering_radius),
    Fact("corrects", ("LAW_COMP_005",), "the errors always corrected",
         _f_corrects),
    Fact("outcome", ("LAW_COMP_005", "LAW_FOURTH_FLIP_001"),
         "what complete decoding does with k errors", _f_outcome),
    Fact("probability", ("LAW_STORAGE_HARDENED_001",),
         "the chance of each decoding outcome at a bit-flip rate",
         _f_probability),
    Fact("always-right", ("LAW_STORAGE_HARDENED_001",),
         "whether decoding is always right at a bit-flip rate",
         _f_always_right),
    Fact("confidence", ("LAW_FOURTH_FLIP_001", "LAW_COMP_005"),
         "the chance a decoding at distance d is right", _f_confidence),
    Fact("unique-fraction", ("LAW_GATEWAY_002", "LAW_GOLAY_UNIQUENESS_001"),
         "the share of words that decode uniquely", _f_unique_fraction),
    Fact("perfect", ("LAW_GOLAY_UNIQUENESS_001",),
         "whether the code is perfect", _f_perfect),
    Fact("kissing", ("LAW_KISSING_EXPANSION_001",),
         "the kissing number of the Leech lattice", _f_kissing),
    Fact("closure", ("LAW_LOGIC_GEO_001",),
         "whether XOR / AND / OR of codewords is a codeword", _f_closure),
    Fact("descent", ("LAW_PATH_LEAST_ACTION",),
         "whether greedy descent reaches the nearest codeword in d steps",
         _f_descent),
)}


def fact_value(key: str, *args: object) -> Tuple[str, str]:
    """``(value, answer)`` for one fact; raises :class:`FactRefusal`."""
    return FACTS[key].compute(*args)


# ===========================================================================
# 2.  READING A QUESTION -- the planner's ``substrate`` frame
# ===========================================================================

_SUBSTRATE = re.compile(r"\b(golay|leech|codewords?|octads?|dodecads?)\b")
_CODE = r"(?:the )?(?:extended |binary |24-bit )?golay code"
_NUM = r"(-?\d+(?:/\d+)?(?:\.\d+)?)"
_RATE = (r"(?:at |with )?(?:a )?(?:bit-flip rate|bit flip rate|flip rate|"
         r"noise(?: level)?|error rate) (?:of )?" + _NUM + r"\s*(%| percent)?")


def _number(text: str, percent: str = "") -> Optional[Fraction]:
    if "/" in text:
        a, b = text.split("/")
        if int(b) == 0:
            return None
        value = Fraction(int(a), int(b))
    else:
        value = Fraction(text)
    if percent:
        value /= 100
    return value


def _int(text: str) -> Optional[int]:
    return int(text) if re.fullmatch(r"-?\d+", text) else None


#: ``(pattern, fact key, argument builder)``; the pattern is matched in full
#: against the planner's cleaned text.
_SHAPES: Tuple[Tuple[str, str, Callable[..., Tuple[object, ...]]], ...] = (
    (rf"how many (?:codewords|code words) (?:does|do) {_CODE} (?:have|contain)",
     "codewords", lambda m: ()),
    (rf"how many (?:codewords|code words) are (?:there )?in {_CODE}",
     "codewords", lambda m: ()),
    (r"how many golay codewords are there", "codewords", lambda m: ()),
    (rf"what is the (?:information )?rate of {_CODE}", "rate", lambda m: ()),
    (rf"how many (octads|dodecads) (?:are there(?: in {_CODE})?|does {_CODE} "
     rf"have)", "weight-count",
     lambda m: (8 if m.group(1) == "octads" else 12,)),
    (rf"how many codewords of weight (-?\d+) (?:does {_CODE} have|are there "
     rf"in {_CODE})", "weight-count", lambda m: (int(m.group(1)),)),
    (rf"what is the minimum (?:hamming )?distance of {_CODE}", "min-distance",
     lambda m: ()),
    (rf"what is the covering radius of {_CODE}", "covering-radius",
     lambda m: ()),
    (rf"how many (?:bit )?errors can {_CODE} (?:always )?correct",
     "corrects", lambda m: ()),
    (r"can the golay (?:decoder|code) correct (-?\d+) (?:bit )?errors?",
     "outcome", lambda m: (int(m.group(1)),)),
    (r"what happens when a golay (?:codeword|code word|word) has (-?\d+) "
     r"(?:bit )?(?:errors?|flips?)", "outcome", lambda m: (int(m.group(1)),)),
    (r"what is the probability (?:that )?the golay decoder (is right|is "
     r"wrong|refuses) " + _RATE, "probability",
     lambda m: ({"is right": "right", "is wrong": "wrong",
                 "refuses": "refused"}[m.group(1)],
                _number(m.group(2), m.group(3) or ""))),
    (r"is the golay decoder always right " + _RATE, "always-right",
     lambda m: (_number(m.group(1), m.group(2) or ""),)),
    (r"how (?:likely|sure|confident) is a golay decoding at distance (-?\d+) "
     r"(?:to be right )?" + _RATE, "confidence",
     lambda m: (int(m.group(1)), _number(m.group(2), m.group(3) or ""))),
    (r"what fraction of 24-bit words (?:decode uniquely|are uniquely "
     r"decodable)(?: under {c})?".format(c=_CODE), "unique-fraction",
     lambda m: ()),
    (rf"is {_CODE} perfect", "perfect", lambda m: (24,)),
    (r"is the (?:binary )?golay code of length 23 perfect", "perfect",
     lambda m: (23,)),
    (r"what is the kissing number of the leech lattice", "kissing",
     lambda m: ()),
    (r"how many minimal vectors does the leech lattice have", "kissing",
     lambda m: ()),
    (r"is the (xor|and|or) of (?:two|2) golay codewords a codeword", "closure",
     lambda m: (m.group(1),)),
    (r"does greedy (?:syndrome )?descent always reach the nearest golay "
     r"codeword in d steps", "descent", lambda m: ()),
)


def read_question(text: str) -> Optional[Tuple[str, Tuple[object, ...]]]:
    """``(fact key, arguments)`` when ``text`` (already cleaned by the
    planner: lower case, no trailing punctuation) names the substrate and
    has a declared shape; ``None`` otherwise."""
    if not _SUBSTRATE.search(text):
        return None
    for pattern, key, build in _SHAPES:
        m = re.fullmatch(pattern, text)
        if m:
            args = build(m)
            if any(a is None for a in args):
                return None
            return key, args
    return None


def answer_question(text: str) -> Dict[str, object]:
    """Read, compute and answer one question (the harness view)."""
    from ..runtime.semantic_plan import clean
    read = read_question(clean(text))
    if read is None:
        return {"read": False}
    key, args = read
    try:
        value, answer = fact_value(key, *args)
    except FactRefusal as refusal:
        return {"read": True, "fact": key, "verdict": "REFUSED",
                "name": refusal.name, "reason": refusal.reason,
                "laws": FACTS[key].laws}
    return {"read": True, "fact": key, "verdict": "ANSWER", "value": value,
            "answer": answer, "laws": FACTS[key].laws}


# ===========================================================================
# 3.  ONE FATE PER LAW
# ===========================================================================

def _retired_reason(law: str) -> str:
    grade = lr.NUMERIC_GRADES.get(law)
    if grade is not None:
        category, reason = grade
        if category == "external":
            tests = [t for t in lr._template_results() if t["law"] == law]
            admitted = [t for t in tests if t["admitted"]]
            if admitted:
                sig = lr.sigma_distance(admitted[0]["key"])
                return (f"external, admitted at its template (chance "
                        f"coverage {admitted[0]['p_decimal']}) but it misses "
                        f"the measured {admitted[0]['quantity']} by "
                        f"{_decimal(sig, 0)} standard deviations: an "
                        f"approximation, and no GLM computation needs it")
            return (f"external, refused by the look-elsewhere test "
                    f"({'; '.join(t['quantity'] + ' p = ' + t['p_decimal'] for t in tests)})")
        return f"{category}: {reason}"
    klass, finding, _ = lr.EXACT_GRADES[law]
    return f"{klass}: {finding}"


#: law id -> (fate, the GLM statement or the reason, fact keys or attribute).
_ABSORBED: Dict[str, str] = {
    "LAW_COMP_005": "complete decoding is right exactly on errors of weight "
                    "at most 3 (not only 1)",
    "LAW_COMP_009": "the code has 2^12 of 2^24 words: rate 1/2",
    "LAW_FOURTH_FLIP_001": "a weight-4 error always lands on a six-way tie "
                           "and is refused; the covering radius is 4; a "
                           "decoding at distance d <= 3 is right with a "
                           "computable probability",
    "LAW_GATEWAY_002": "2325 of 4096 cosets decode uniquely",
    "LAW_GOLAY_UNIQUENESS_001": "the length-23 code is perfect, the extended "
                                "code is not (1771 cosets tie)",
    "LAW_KISSING_EXPANSION_001": "196560 = 1104 + 97152 + 98304 minimal "
                                 "Leech vectors, by shape",
    "LAW_RELATION_002": "the minimum distance is 8",
    "LAW_RELATION_ORTHO_001": "the weight distribution 1, 759, 2576, 759, 1",
    "LAW_LOGIC_GEO_001": "corrected: XOR is a code operation, AND and OR are "
                         "not",
    "LAW_PATH_LEAST_ACTION": "corrected: greedy descent does not reach the "
                             "nearest codeword in d steps (792 cosets)",
    "LAW_STORAGE_HARDENED_001": "corrected: integrity is certain for every "
                                "pattern of at most 3 flips per word, and "
                                "never certain at a positive random bit-flip "
                                "rate; the exact probabilities are computed",
}

_ALREADY: Dict[str, str] = {
    "LAW_METRIC_002": "glm_universal.reasoning.coherence.Y",
    "LAW_LEECH_TAX_001": "glm_universal.reasoning.coherence.tax_shell0",
}

#: The three unit-bound laws whose dimensionless content is retested (§1.5).
RETESTS: Tuple[Tuple[str, str, str], ...] = (
    ("LAW_FORCE_003", "m_W/m_Z", "a/b"),
    ("LAW_FORCE_005", "m_H/m_Z", "(a + 1/b)/c"),
    ("LAW_CHEM_002", "water bond angle / turn", "(a(1+Y) - Y/b - 1/(cY))/360"),
)

#: PDG 2022 central values (GeV) and the water bond angle (degrees).
_M_W, _M_Z, _M_H = Fraction("80.377"), Fraction("91.1876"), Fraction("125.25")
_WATER = Fraction("104.45")


@memo
def retests() -> Tuple[Dict[str, object], ...]:
    """The declared dimensionless retests of §1.5, by the Phase 74 test."""
    Y = coherence.Y
    r = lambda lo, hi: range(lo, hi + 1)  # noqa: E731
    specs = (
        ("LAW_FORCE_003", "m_W/m_Z", "a/b", lambda a, b: Fraction(a, b),
         {"a": r(1, 24), "b": r(1, 24)}, {"a": 21, "b": 24}, _M_W / _M_Z),
        ("LAW_FORCE_005", "m_H/m_Z", "(a + 1/b)/c",
         lambda a, b, c: (a + Fraction(1, b)) / c,
         {"a": r(1, 48), "b": r(1, 24), "c": r(1, 24)},
         {"a": 33, "b": 9, "c": 24}, _M_H / _M_Z),
        ("LAW_CHEM_002", "water bond angle / turn",
         "(a(1+Y) - Y/b - 1/(cY))/360",
         lambda a, b, c: (a * (1 + Y) - Y / b - 1 / (c * Y)) / 360,
         {"a": r(1, 120), "b": r(1, 24), "c": r(1, 24)},
         {"a": 83, "b": 2, "c": 10}, _WATER / 360),
    )
    out = []
    for law, quantity, notation, fn, ranges, inst, target in specs:
        res = lr.look_elsewhere(fn, ranges, inst, target)
        out.append({"law": law, "quantity": quantity, "template": notation,
                    "value": _decimal(res["value"], 6),
                    "target": _decimal(target, 6),
                    "error_pct": _decimal(100 * res["eps"], 4),
                    "members": res["members"], "p": res["p"],
                    "p_decimal": _decimal(res["p"], 4),
                    "admitted": res["admitted"]})
    return tuple(out)


@memo
def _absorption() -> Dict[str, Tuple[str, str, Tuple[str, ...]]]:
    out: Dict[str, Tuple[str, str, Tuple[str, ...]]] = {}
    retested = {r["law"]: r for r in retests()}
    for row in lr.register_rows():
        law = row["ubp_id"]
        if law in _ABSORBED:
            keys = tuple(k for k, f in FACTS.items() if law in f.laws)
            out[law] = ("absorbed", _ABSORBED[law], keys)
        elif law in _ALREADY:
            out[law] = ("already GLM", f"already a GLM definition: "
                        f"{_ALREADY[law]}", (_ALREADY[law],))
        elif law in retested:
            t = retested[law]
            verdict = "admitted" if t["admitted"] else "refused"
            out[law] = ("retested", f"{t['quantity']} = {t['value']} against "
                        f"{t['target']} ({t['error_pct']}%): chance coverage "
                        f"{t['p_decimal']} over {t['members']} template "
                        f"members, {verdict}", ())
        else:
            out[law] = ("retired", _retired_reason(law), ())
    return out


def ABSORPTION() -> Dict[str, Tuple[str, str, Tuple[str, ...]]]:  # noqa: N802
    """law id -> (fate, statement or reason, fact keys / attribute)."""
    return dict(_absorption())


def fate_census() -> Dict[str, int]:
    fates = [v[0] for v in _absorption().values()]
    return {f: fates.count(f) for f in FATES}


# ===========================================================================
# 4.  THE REPORT
# ===========================================================================

def _case_matches(expected: Tuple[str, ...], got: Dict[str, object]) -> bool:
    if not got.get("read"):
        return False
    if expected[0] == "REFUSED":
        return got["verdict"] == "REFUSED" and got["name"] == expected[1]
    if got["verdict"] != "ANSWER":
        return False
    want, value = expected[1], str(got["value"])
    if "." in want and re.fullmatch(r"-?\d+(?:/\d+)?", value):
        places = len(want.split(".")[1])
        return _round(Fraction(value), places) == want
    return value == want


@memo
def _declared_results() -> Tuple[Dict[str, object], ...]:
    from ..evaluation import law_absorption_cases as cases
    out = []
    for cid, question, expected, law in cases.CASES:
        got = answer_question(question)
        out.append({"id": cid, "question": question, "expected": expected,
                    "law": law, "got": got,
                    "ok": _case_matches(expected, got),
                    "wrong": (got.get("verdict") == "ANSWER"
                              and not _case_matches(expected, got))})
    return tuple(out)


def planner_path(with_frame: bool = True) -> Dict[str, object]:
    """The declared questions through the typed planner itself.

    ``with_frame=False`` is the control: the same planner with the
    ``substrate`` frame taken out of its table, which is the planner as it
    stood before this round.  A case counts as answered as declared only when
    the planner's verdict is ``answered`` and the value matches; a declared
    refusal counts when no plan is licensed and the named refusal is in the
    reason.
    """
    from ..runtime import semantic_plan as sp
    from ..runtime.session import GeometricSession
    from ..evaluation import law_absorption_cases as cases
    session = GeometricSession()
    saved = sp.FRAMES
    if not with_frame:
        sp.FRAMES = tuple(f for f in saved if f[0] != "substrate")
    try:
        ok = answered = wrong = 0
        for _cid, question, expected, _law in cases.CASES:
            planned = sp.plan_question(session, question)
            chosen = planned.chosen
            if planned.verdict == "answered" and chosen is not None:
                answered += 1
                got = {"read": True, "verdict": "ANSWER",
                       "value": chosen.value}
                if expected[0] == "ANSWER" and _case_matches(expected, got):
                    ok += 1
                else:
                    wrong += 1
            elif expected[0] == "REFUSED" and expected[1] in planned.reason:
                ok += 1
    finally:
        sp.FRAMES = saved
    return {"with_frame": with_frame, "as_declared": ok,
            "answered": answered, "wrong": wrong,
            "total": len(cases.CASES)}


def existing_texts_read() -> Dict[str, object]:
    """Mark A4 swept wide: every string literal of every other evaluation
    module (contract cases, route tables, held-out sets, the stepwise and
    reverse corpora), read by the frame or not."""
    import ast
    from pathlib import Path
    folder = Path(__file__).resolve().parents[1] / "evaluation"
    texts: List[str] = []
    for path in sorted(folder.glob("*.py")):
        if path.name == "law_absorption_cases.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                texts.append(node.value)
    read = sorted({t for t in texts if read_question(_clean(t)) is not None})
    return {"literals": len(texts), "read": read}


def brute_checks() -> Tuple[Dict[str, object], ...]:
    """The confidence fact against a sum over all 4096 codewords."""
    code = _code()
    word = code.codeword_masks[1]
    out = []
    for d, error in ((0, 0), (1, 1 << 5), (2, (1 << 2) | (1 << 17)),
                     (3, (1 << 0) | (1 << 9) | (1 << 21))):
        received = word ^ error
        for p in (Fraction(1, 100), Fraction(1, 10)):
            a, b = confidence(d, p), brute_confidence(received, p)
            out.append({"d": d, "p": f"{p}", "formula": _decimal(a, 9),
                        "brute": _decimal(b, 9), "equal": a == b})
    return tuple(out)


def law_absorption_report() -> Dict[str, object]:
    """Every measurement of ``studies/LAW_ABSORPTION_STUDY.md`` and its marks."""
    from ..evaluation import law_absorption_cases as cases
    table = _absorption()
    census = fate_census()
    declared = _declared_results()
    not_read = [t for t in cases.NOT_READ
                if read_question(_clean(t)) is not None]
    sweep = existing_texts_read()
    brute = brute_checks()
    rt = retests()
    live = planner_path(True)
    control = planner_path(False)
    phase74 = {
        "min-distance": (fact_value("min-distance")[0], "8"),
        "covering-radius": (fact_value("covering-radius")[0], "4"),
        "corrects": (fact_value("corrects")[0], "3"),
        "unique-fraction": (fact_value("unique-fraction")[0], "2325/4096"),
        "kissing": (fact_value("kissing")[0], "196560"),
        "codewords": (fact_value("codewords")[0], "4096"),
        "storage-3%": (_decimal(1 - lr.outcome_probabilities(Fraction(3, 100))["right"], 6),
                       lr.storage_hardened()["not_right_decimal"]),
    }
    reached = {k: any(c["got"].get("fact") == k and c["ok"] for c in declared)
               for k in FACTS}
    marks = {
        "A1": (len(table) == 65 and sum(census.values()) == 65
               and all(v[2] for v in table.values() if v[0] == "absorbed")),
        "A2": all(reached.values()) and all(a == b for a, b in phase74.values()),
        "A3": (all(c["ok"] for c in declared)
               and not any(c["wrong"] for c in declared)
               and live["as_declared"] == live["total"] and live["wrong"] == 0
               and control["answered"] == 0),
        "A4": not not_read and not sweep["read"],
        "A6": all(b["equal"] for b in brute),
        "A7": len(rt) == 3,
        "A5": _lean_has(("right_prob_lt_one", "right_prob_eq_one_iff",
                         "worst_case_integrity")),
        "A8": _lean_has(LEAN_THEOREMS),
    }
    return {"census": census, "table": {k: list(v) for k, v in table.items()},
            "declared": [{k: v for k, v in c.items() if k != "got"}
                         | {"verdict": c["got"].get("verdict"),
                            "value": c["got"].get("value", c["got"].get("name"))}
                         for c in declared],
            "declared_ok": sum(c["ok"] for c in declared),
            "declared_total": len(declared),
            "declared_wrong": sum(c["wrong"] for c in declared),
            "declared_answered": sum(1 for c in declared if c["expected"][0] == "ANSWER"),
            "declared_refused": sum(1 for c in declared if c["expected"][0] == "REFUSED"),
            "facts_reached": reached, "phase74_agreement": phase74,
            "not_read_but_read": not_read, "evaluation_sweep": sweep, "brute_checks": list(brute),
            "retests": list(rt), "planner": live, "control": control,
            "marks": marks}


#: The theorems of ``RequestProject/GLM/LawAbsorption.lean`` this round cites.
LEAN_THEOREMS: Tuple[str, ...] = (
    "total_prob", "right_prob_lt_one", "right_prob_eq_one_iff",
    "worst_case_integrity", "leader_most_likely", "equal_weight_equal_prob",
    "tie_posterior_le_sixth", "odd_error_never_refused",
    "odd_heavy_miscorrected",
)


def _lean_has(names: Sequence[str]) -> bool:
    """Whether the Lean file states every named theorem and holds no
    ``sorry`` (the build itself is the release's Lean instrument)."""
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "glm_lean" / LEAN_FILE
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return "sorry" not in text and all(
        re.search(rf"\btheorem {n}\b", text) for n in names)


def _clean(text: str) -> str:
    from ..runtime.semantic_plan import clean
    return clean(text)


def tool_summary(arg: str = "") -> Dict[str, object]:
    """The toolbox reading: one law's fate, or the census."""
    arg = (arg or "").strip()
    if arg:
        law = (arg if arg.upper().startswith("LAW_") else "LAW_" + arg).upper()
        table = _absorption()
        if law not in table:
            return {"law": law, "known": False}
        fate, said, keys = table[law]
        return {"law": law, "known": True, "fate": fate, "said": said,
                "facts": list(keys)}
    return {"census": fate_census(), "facts": sorted(FACTS)}
