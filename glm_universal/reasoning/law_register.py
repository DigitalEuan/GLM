"""``glm_universal.reasoning.law_register`` -- the UBP law register, re-read.

What this module is
-------------------
The owner supplied the result of an older study: a GLM-lens review of the 426
``LAW_*`` entries of the UBP knowledge base
(``source_material/UBP_LAW_GLM_REVIEW.md``) and the 65 laws it retained in its
two strongest classes (``source_material/retained_laws_verified_65.csv``,
frozen here as ``_data/law_register_65.csv``).  This module re-reads every one
of the 65 at GLM resolution, against the declarations of
``studies/LAW_REGISTER_STUDY.md`` §1, which were written before it existed.

It does four things.

**1.  Re-grades the sixteen ``RETAINED-EXACT`` rows** (:func:`exact_regrade`).
Every figure a row quotes is recomputed (:func:`exact_checks`), and every row
is filed as *structural* (a theorem of the code, with the Lean theorem named),
*overclaimed* (the precise part holds and a generalisation is proved false),
*definitional*, *arithmetic* (true arithmetic under an untestable reading) or
*near-miss*.

**2.  Makes the decoder laws precise** (:func:`decoder_outcomes`).  The
register says "1-bit correction", "at 4 bits a vector enters a deep hole" and
"hardened storage guarantees 100% integrity at noise <= 3%".  The exact
outcome of complete decoding -- right, refused, or wrong -- is computed for
every error weight from the coset weight enumerators, and the probability of
each at a bit-flip rate ``p`` is an exact polynomial in ``p``
(:func:`outcome_probabilities`).  ``RequestProject/GLM/LawRegister.lean``
proves the three facts the table rests on: the decoder is right exactly when
the error has weight at most 3, weight 4 is always refused, weight 5 is always
miscorrected.  :func:`refusal_price` prices the refusal against the retired
"snap" that picks one of the six tied codewords.

**3.  Decides two statistics of the review** -- the two NRCI means it reports
as equal (:func:`moment_census`: equal to seven decimals, not equal, because
exactly the first seven weight moments of the code are binomial), and the
"descent in exactly ``d`` steps" it retains two laws on
(:func:`descent_check`, against ``reasoning.deep_dive``).

**4.  Audits the forty-nine ``RETAINED-NUM`` rows** (:func:`numeric_regrade`).
Each row is put in one category -- external, unit-dependent,
not-a-measurement, KB-internal, restatement, duplicate -- and every external
formula gets the look-elsewhere test (:func:`look_elsewhere`): the chance that
the formula's own template, its small integers varied over declared ranges,
would hit a target drawn from ``[T/2, 2T]`` as closely as the law hits ``T``.
:func:`admit` is the resulting refusal faculty, usable on any new claim
through :func:`look_elsewhere` directly.

Everything is exact ``int`` / ``Fraction`` arithmetic (D7).  Reals -- pi, phi,
e, square roots, logarithms, rational powers -- enter as rationals within
``2**-PRECISION`` of the true value, taken from ``reasoning.exact_real``; no
float is constructed.
"""

from __future__ import annotations

import csv
from fractions import Fraction
from itertools import combinations
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from ..derived import memo
from ..substrate import golay_decode, mog
from ..substrate.linalg import popcount
from . import coherence
from . import exact_real as xr
from . import real_expr

__all__ = [
    "DATA_PATH", "SOURCE_PATH", "LEAN_FILE", "PRECISION", "ADMIT_BELOW",
    "register_rows", "row",
    "EXACT_GRADES", "EXACT_CLASSES", "exact_checks", "exact_regrade",
    "coset_enumerators", "decoder_outcomes", "outcome_probabilities",
    "storage_hardened", "refusal_price",
    "moment_census", "nrci_means", "closure_census", "descent_check",
    "NUMERIC_CATEGORIES", "NUMERIC_GRADES", "TEMPLATES", "Template",
    "look_elsewhere", "template_result", "numeric_regrade", "admit",
    "lean_citations", "law_register_report", "tool_summary",
]

DATA_PATH = Path(__file__).resolve().parent / "_data" / "law_register_65.csv"
SOURCE_PATH = "source_material/retained_laws_verified_65.csv"
LEAN_FILE = "RequestProject/GLM/LawRegister.lean"

#: Bits of precision for every real constant (a rational within 2**-PRECISION).
PRECISION = 256

#: The declared admission threshold of the look-elsewhere test (§1.4, R8).
ADMIT_BELOW = Fraction(1, 100)

N = 24


# ===========================================================================
# 0.  THE REGISTER
# ===========================================================================

@memo
def register_rows() -> Tuple[Dict[str, str], ...]:
    """The 65 rows of the retained register, in file order."""
    with open(DATA_PATH, newline="", encoding="utf-8") as handle:
        return tuple(dict(r) for r in csv.DictReader(handle))


def row(law_id: str) -> Optional[Dict[str, str]]:
    for r in register_rows():
        if r["ubp_id"] == law_id:
            return r
    return None


# ===========================================================================
# 1.  EXACT CONSTANTS
# ===========================================================================

def _grid(q: Fraction, bits: int = PRECISION) -> Fraction:
    """``q`` rounded down to the grid ``2**-bits`` *relative* to its size."""
    if q == 0:
        return q
    sign = 1 if q > 0 else -1
    q = abs(q)
    shift = bits - (q.numerator.bit_length() - q.denominator.bit_length())
    if shift >= 0:
        scaled = (q.numerator << shift) // q.denominator
        return sign * Fraction(scaled, 1 << shift)
    scaled = q.numerator // (q.denominator << -shift)
    return sign * Fraction(scaled << -shift)


def _real(notation: str) -> Fraction:
    return _grid(xr.surrogate(real_expr.parse_expression(notation), PRECISION + 64))


@memo
def _constants() -> Dict[str, Fraction]:
    y = coherence.Y
    pi = _real("pi")
    phi = _real("phi")
    e = _real("e")
    wobble = _grid(pi * phi * e - 13)
    return {
        "Y": y, "Yinv": 1 / y, "pi": pi, "phi": phi, "e": e,
        "w": wobble, "L": wobble / 13, "Ue": Fraction(24 ** 3),
        "K": Fraction(196560), "RG": _real("ln(phi)/ln(pi)"),
    }


def _c(name: str) -> Fraction:
    return _constants()[name]


def _sqrt(q: Fraction) -> Fraction:
    return _grid(xr.rational_sqrt_approx(Fraction(q), PRECISION + 64))


def _root(q: Fraction, degree: int) -> Fraction:
    return _grid(xr.rational_nth_root_approx(Fraction(q), degree, PRECISION + 64))


def _pow(base: Fraction, n: int) -> Fraction:
    """``base ** n`` for an integer ``n``, rounded to the working grid."""
    out = Fraction(1)
    b = base if n >= 0 else 1 / base
    for _ in range(abs(n)):
        out = _grid(out * b)
    return out


def _decimal(q: Fraction, places: int) -> str:
    return coherence.decimal_str(Fraction(q), places)


def _rounds_to(value: Fraction, quoted: str) -> bool:
    """Whether ``value`` rounds (half up) to the decimal string ``quoted``."""
    places = len(quoted.split(".")[1]) if "." in quoted else 0
    scale = 10 ** places
    scaled = value * scale
    rounded = (scaled.numerator * 2 + scaled.denominator) // (2 * scaled.denominator)
    return Fraction(rounded, scale) == Fraction(quoted)


# ===========================================================================
# 2.  THE SIXTEEN RETAINED-EXACT ROWS
# ===========================================================================

EXACT_CLASSES = ("structural", "overclaimed", "definitional", "arithmetic",
                 "near-miss")

#: law id -> (class, one-line finding, ((Lean file, theorem), ...)).
EXACT_GRADES: Dict[str, Tuple[str, str, Tuple[Tuple[str, str], ...]]] = {
    "LAW_COMP_005": (
        "structural",
        "every error of weight 1 (indeed <= 3) is corrected uniquely; the "
        "decoder is right exactly up to weight 3",
        (("RequestProject/GLM/LawRegister.lean", "unique_leader_iff"),
         ("RequestProject/GLM/Golay/Census.lean", "cosetWt_of_wt_le_three"))),
    "LAW_COMP_009": (
        "structural",
        "the code has 2^12 of 2^24 words: rate 1/2, twelve message and twelve "
        "parity coordinates",
        (("RequestProject/GLM/GolayWeightEnum.lean", "card_codewords"),
         ("RequestProject/GLM/GolayWeightEnum.lean", "encode_injective"))),
    "LAW_FOURTH_FLIP_001": (
        "structural",
        "a weight-4 error lands in a coset of weight 4 with exactly six "
        "nearest codewords; the complete decoder refuses",
        (("RequestProject/GLM/Golay/Sextet.lean", "covering_radius_eq_four"),
         ("RequestProject/GLM/Golay/Sextet.lean", "tetrad_class_card"),
         ("RequestProject/GLM/LawRegister.lean", "wt_four_refused"))),
    "LAW_GATEWAY_002": (
        "structural",
        "2325 of the 4096 cosets decode uniquely (56.76%); 277/4096 = 6.76% "
        "are within distance 2",
        (("RequestProject/GLM/Golay/Census.lean", "unique_vs_ambiguous"),
         ("RequestProject/GLM/Packing.lean", "ball3_at_24"))),
    "LAW_GOLAY_UNIQUENESS_001": (
        "structural",
        "G23 is perfect (4096 x 2048 = 2^23); the extension leaves 1771/4096 "
        "= 43.24% of cosets as six-way ties",
        (("RequestProject/GLM/Packing.lean", "golay23_perfect_arithmetic"),
         ("RequestProject/GLM/Golay/Census.lean", "card_filter_cosetWt_four"))),
    "LAW_KISSING_EXPANSION_001": (
        "structural",
        "196560 = 1104 + 97152 + 98304, the three minimal-vector shapes",
        (("RequestProject/GLM/GolayMOG.lean", "leechMinimalClass_counts"),)),
    "LAW_RELATION_002": (
        "structural",
        "the minimum distance of the code is 8",
        (("RequestProject/GLM/Golay/Sextet.lean", "golay_min_distance_eight"),)),
    "LAW_RELATION_ORTHO_001": (
        "structural",
        "two words at distance 12 agree on exactly 12 of 24 coordinates; the "
        "code has 2576 dodecads",
        (("RequestProject/GLM/GolayWeightEnum.lean", "golay_weight_enumerator"),)),
    "LAW_LOGIC_GEO_001": (
        "overclaimed",
        "XOR of codewords is a codeword; AND and OR are not code operations, "
        "so Boolean logic is not isomorphic to arithmetic on the code",
        (("RequestProject/GLM/LawRegister.lean", "xor_closed"),
         ("RequestProject/GLM/LawRegister.lean", "and_not_closed"),
         ("RequestProject/GLM/LawRegister.lean", "or_not_closed"))),
    "LAW_PATH_LEAST_ACTION": (
        "overclaimed",
        "flipping the coset leader's bits reaches the nearest codeword in d "
        "steps, but descent on the syndrome energy does not: 792 cosets need "
        "more flips than their distance",
        (("RequestProject/GLM/Relaxation.lean", "relaxation_is_not_decoding"),
         ("RequestProject/GLM/LawRegister.lean", "unique_leader_iff"))),
    "LAW_LEECH_TAX_001": (
        "definitional",
        "tax = HW*Y + |v|^2/8 is coherence.tax_shell0 by definition",
        ()),
    "LAW_METRIC_002": (
        "definitional",
        "Y = 1/(pi + 2/pi) is the definition of the read quantum; no "
        "self-referential dynamics is exhibited",
        ()),
    "LAW_RESOLUTION_GAP_001": (
        "definitional",
        "RG = ln(phi)/ln(pi) = 0.4203715 is a definition",
        ()),
    "LAW_ARX_HORIZON_006": (
        "arithmetic",
        "log2 of the Hamming ball of radius 6 in 4096 coordinates is 62.505 "
        "bits; 4096 is the number of codewords, not a dimension of the code",
        ()),
    "LAW_LEECH_TENSION_001": (
        "arithmetic",
        "1 - 2.4/196560 = 0.9999878; the 2.4 is a free constant",
        ()),
    "LAW_INTERFACE_CLOSURE_001": (
        "near-miss",
        "phi^3/RG^2 = 23.97156, 0.12% short of 24",
        ()),
}


@memo
def exact_checks() -> Dict[str, Tuple[Tuple[str, str, str, bool], ...]]:
    """Every figure the sixteen rows quote: ``(label, quoted, recomputed, holds)``."""
    k = _constants()
    code = mog.GolayCode()
    words = code.codeword_masks
    out: Dict[str, List[Tuple[str, str, str, bool]]] = {}

    def add(law: str, label: str, quoted: str, value: Fraction, holds: bool,
            places: int = 6) -> None:
        out.setdefault(law, []).append((label, quoted, _decimal(value, places), holds))

    # ARX: log2(sum_{i<=6} C(4096, i)) = 62.505  <=>  2^62.5045 <= S < 2^62.5055
    s = sum(_binom(4096, i) for i in range(7))
    add("LAW_ARX_HORIZON_006", "log2 ball(4096, 6)", "62.505", Fraction(62505, 1000),
        2 ** 125009 <= s ** 2000 < 2 ** 125011, 3)
    outcomes = decoder_outcomes()
    add("LAW_COMP_005", "weight-1 errors corrected", "24",
        Fraction(outcomes["by_weight"][1]["right"]),
        outcomes["by_weight"][1]["right"] == 24, 0)
    add("LAW_COMP_009", "parity share of the word", "0.5",
        Fraction(24 - (len(words).bit_length() - 1), 24),
        len(words) == 4096, 1)
    table = golay_decode.coset_table()
    tetrad_ties = {len(table[code.syndrome_int(sum(1 << i for i in t))])
                   for t in combinations(range(N), 4)}
    add("LAW_FOURTH_FLIP_001", "nearest codewords of a weight-4 error", "6",
        Fraction(min(tetrad_ties)), tetrad_ties == {6}, 0)
    ball3 = sum(_binom(N, i) for i in range(4))
    add("LAW_GATEWAY_002", "tether 2325/4096", "0.5676",
        Fraction(ball3, 4096), ball3 == 2325 and _rounds_to(Fraction(ball3, 4096), "0.5676"), 4)
    add("LAW_GATEWAY_002", "byte-scale capture 277/4096", "0.068",
        Fraction(1 + N * (N - 1) // 2, 4096),
        _rounds_to(Fraction(277, 4096), "0.068"), 3)
    add("LAW_GOLAY_UNIQUENESS_001", "G23 perfect: 4096 x 2048", "8388608",
        Fraction(4096 * sum(_binom(23, i) for i in range(4))),
        4096 * sum(_binom(23, i) for i in range(4)) == 2 ** 23, 0)
    add("LAW_GOLAY_UNIQUENESS_001", "slack 1771/4096", "0.4324",
        Fraction(1771, 4096), _rounds_to(Fraction(1771, 4096), "0.4324"), 4)
    phi3 = k["phi"] ** 3
    interface = phi3 / k["RG"] ** 2
    add("LAW_INTERFACE_CLOSURE_001", "phi^3 / RG^2", "23.97156", interface,
        _rounds_to(interface, "23.97156"), 5)
    shapes = (_binom(24, 2) * 4, 759 * 128, 24 * 4096)
    add("LAW_KISSING_EXPANSION_001", "1104 + 97152 + 98304", "196560",
        Fraction(sum(shapes)), shapes == (1104, 97152, 98304) and sum(shapes) == 196560, 0)
    octad = next(c for c in words if popcount(c) == 8)
    tax = coherence.tax_shell0([1 if octad >> i & 1 else 0 for i in range(N)])
    add("LAW_LEECH_TAX_001", "octad tax = 8Y + 1", _decimal(8 * k["Y"] + 1, 8), tax,
        tax == 8 * k["Y"] + 1, 8)
    tension = 1 - Fraction(24, 10) / 196560
    add("LAW_LEECH_TENSION_001", "1 - 2.4/196560", "0.9999878", tension,
        _rounds_to(tension, "0.9999878"), 7)
    xor_ok = all(code.is_codeword(a ^ b) for a in words[:64] for b in words[:64])
    closure = closure_census()
    add("LAW_LOGIC_GEO_001", "XOR closure (64 x 64 codewords)", "closed",
        Fraction(int(xor_ok)), xor_ok, 0)
    add("LAW_LOGIC_GEO_001", "AND of distinct octads a codeword", "closed",
        closure["and_closed_fraction"], closure["and_closed_fraction"] == 1, 6)
    y_def = _grid(1 / (k["pi"] + 2 / k["pi"]))
    add("LAW_METRIC_002", "1/(pi + 2/pi)", "0.264675430404527", y_def,
        abs(y_def - k["Y"]) < Fraction(1, 10 ** 15), 15)
    descent = descent_check()
    add("LAW_PATH_LEAST_ACTION", "cosets whose fastest descent is minimal",
        "4096", Fraction(4096 - descent["trapped"]), descent["trapped"] == 0, 0)
    weights = sorted({popcount(a ^ b) for a in words[:256] for b in words[:256] if a != b})
    add("LAW_RELATION_002", "least distance between codewords", "8",
        Fraction(weights[0]), weights[0] == 8, 0)
    dodecads = sum(1 for c in words if popcount(c) == 12)
    add("LAW_RELATION_ORTHO_001", "shared coordinates at distance 12", "12",
        Fraction(N - 12), dodecads == 2576, 0)
    add("LAW_RESOLUTION_GAP_001", "ln(phi)/ln(pi)", "0.4203715", k["RG"],
        _rounds_to(k["RG"], "0.4203715"), 7)
    return {law: tuple(rows) for law, rows in out.items()}


def _binom(n: int, r: int) -> int:
    if r < 0 or r > n:
        return 0
    out = 1
    for i in range(r):
        out = out * (n - i) // (i + 1)
    return out


def exact_regrade() -> Dict[str, object]:
    """The sixteen rows, re-graded, with their recomputed figures."""
    rows = [r for r in register_rows() if r["verdict"] == "RETAINED-EXACT"]
    checks = exact_checks()
    graded = []
    for r in rows:
        klass, finding, lean = EXACT_GRADES[r["ubp_id"]]
        figures = checks.get(r["ubp_id"], ())
        graded.append({"id": r["ubp_id"], "class": klass, "finding": finding,
                       "lean": [f"{f}:{t}" for f, t in lean],
                       "figures": [list(f) for f in figures]})
    census = {c: sum(1 for g in graded if g["class"] == c) for c in EXACT_CLASSES}
    # A figure "holds" when the quoted number reproduces.  Two rows are
    # expected to *fail* a check -- the overclaimed generalisations -- and the
    # failure is the finding, so R1 counts the arithmetic figures only.
    arithmetic_ok = all(f[3] for g in graded if g["class"] != "overclaimed"
                        for f in g["figures"])
    overclaims_fail = all(not all(f[3] for f in g["figures"])
                          for g in graded if g["class"] == "overclaimed")
    return {"rows": graded, "census": census,
            "boilerplate_evidence": len({r["glm_test_and_result"] for r in rows}) == 1,
            "arithmetic_reproduces": arithmetic_ok,
            "overclaims_fail_as_found": overclaims_fail}


# ===========================================================================
# 3.  THE DECODER LAWS
# ===========================================================================

#: How many of the 4096 cosets have each weight (``Golay24.coset_census``).
COSET_COUNTS = (1, 24, 276, 2024, 1771)


@memo
def coset_enumerators() -> Dict[str, object]:
    """Weight enumerator of a coset of each weight ``0..4``.

    Two leaders per weight (lowest and highest coordinates) must give the same
    enumerator -- M24 is transitive on the leaders of each weight -- and the
    five enumerators weighted by the coset census must add to ``C(24, k)``.
    """
    words = mog.GolayCode().codeword_masks
    enum: List[Tuple[int, ...]] = []
    agree = True
    for j in range(5):
        pair = []
        for leader in ((1 << j) - 1, ((1 << j) - 1) << (N - j)):
            counts = [0] * (N + 1)
            for c in words:
                counts[popcount(leader ^ c)] += 1
            pair.append(tuple(counts))
        agree = agree and pair[0] == pair[1]
        enum.append(pair[0])
    closes = all(sum(COSET_COUNTS[j] * enum[j][k] for j in range(5)) == _binom(N, k)
                 for k in range(N + 1))
    return {"enumerators": tuple(enum), "leaders_agree": agree,
            "closes_to_binomial": closes}


@memo
def decoder_outcomes() -> Dict[str, object]:
    """Right / refused / wrong, for every error weight, under complete decoding.

    An error of weight ``k`` in a coset of weight ``j``: right when ``j == k
    <= 3`` (it is the unique leader), refused when ``j == 4`` (six tie), wrong
    otherwise (a unique leader that is not the error).
    """
    enum = coset_enumerators()["enumerators"]
    by_weight = {}
    for k in range(N + 1):
        right = COSET_COUNTS[k] * enum[k][k] if k <= 3 else 0
        refused = COSET_COUNTS[4] * enum[4][k]
        wrong = sum(COSET_COUNTS[j] * enum[j][k] for j in range(4) if j < k)
        by_weight[k] = {"right": right, "refused": refused, "wrong": wrong,
                        "total": right + refused + wrong}
    exact = all(v["total"] == _binom(N, k) for k, v in by_weight.items())
    return {"by_weight": by_weight, "exact": exact,
            "right_iff_le_three": all((v["right"] == v["total"]) == (k <= 3)
                                      for k, v in by_weight.items()),
            "weight_four_all_refused": by_weight[4]["refused"] == _binom(N, 4),
            "weight_five_all_wrong": by_weight[5]["wrong"] == _binom(N, 5)}


def outcome_probabilities(p: Fraction) -> Dict[str, Fraction]:
    """Exact probabilities of each outcome at independent bit-flip rate ``p``."""
    p = Fraction(p)
    out = {"right": Fraction(0), "refused": Fraction(0), "wrong": Fraction(0)}
    for k, v in decoder_outcomes()["by_weight"].items():
        weight = p ** k * (1 - p) ** (N - k)
        for key in out:
            out[key] += v[key] * weight
    out["weight_four"] = _binom(N, 4) * p ** 4 * (1 - p) ** (N - 4)
    return out


def storage_hardened() -> Dict[str, object]:
    """``LAW_STORAGE_HARDENED_001`` at noise 3%, decided exactly."""
    p = Fraction(3, 100)
    probs = outcome_probabilities(p)
    not_right = 1 - probs["right"]
    return {"p": "3/100", "not_right": not_right,
            "not_right_decimal": _decimal(not_right, 6),
            "wrong": probs["wrong"], "wrong_decimal": _decimal(probs["wrong"], 7),
            "refused_decimal": _decimal(probs["refused"], 6),
            "holds": not_right == 0}


def refusal_price(rates: Sequence[Fraction] = (Fraction(1, 100), Fraction(3, 100),
                                               Fraction(5, 100))) -> Tuple[Dict[str, object], ...]:
    """What refusing at a six-way tie buys, against a snap that picks one.

    The snap is right on a weight-4 error one time in six (the true error is
    one of the six tied leaders) and never right on a heavier error that lands
    in a weight-4 coset.  So refusing withholds ``refused - weight_four/6``
    wrong answers and gives up ``weight_four/6`` right ones.
    """
    out = []
    for p in rates:
        probs = outcome_probabilities(p)
        given_up = probs["weight_four"] / 6
        withheld = probs["refused"] - given_up
        out.append({"p": f"{p.numerator}/{p.denominator}",
                    "right": _decimal(probs["right"], 6),
                    "refused": _decimal(probs["refused"], 6),
                    "wrong": _decimal(probs["wrong"], 7),
                    "wrong_withheld": _decimal(withheld, 7),
                    "right_given_up": _decimal(given_up, 7),
                    "withheld_per_given_up": _decimal(withheld / given_up, 2),
                    "snap_wrong": _decimal(probs["wrong"] + withheld, 7)})
    return tuple(out)


# ===========================================================================
# 4.  TWO STATISTICS OF THE REVIEW
# ===========================================================================

@memo
def moment_census() -> Dict[str, object]:
    """Weight moments of the code against the binomial, ``k = 0 .. 9``."""
    words = mog.GolayCode().codeword_masks
    weights = [popcount(c) for c in words]
    rows = []
    for k in range(10):
        code = Fraction(sum(w ** k for w in weights), len(words))
        binom = Fraction(sum(_binom(N, w) * w ** k for w in range(N + 1)), 2 ** N)
        rows.append({"k": k, "equal": code == binom, "difference": code - binom})
    agree_through = max(r["k"] for r in rows if all(s["equal"] for s in rows[: r["k"] + 1]))
    return {"rows": rows, "agree_through": agree_through}


def nrci_means() -> Dict[str, object]:
    """The two shell-0 NRCI means Round 2 reports as equal, as exact rationals."""
    q = coherence.Y + Fraction(1, 8)

    def nrci(w: int) -> Fraction:
        return Fraction(10) / (10 + w * q)

    enum = {0: 1, 8: 759, 12: 2576, 16: 759, 24: 1}
    code = sum(n * nrci(w) for w, n in enum.items()) / 4096
    words = sum(_binom(N, w) * nrci(w) for w in range(N + 1)) / 2 ** N
    return {"code": _decimal(code, 9), "words": _decimal(words, 9),
            "difference": _decimal(code - words, 12), "equal": code == words,
            "agree_as_quoted": _rounds_to(code, "0.684298") and _rounds_to(words, "0.684298"),
            "floor_w24": _decimal(nrci(24), 6), "floor_above_042": nrci(24) > Fraction(42, 100)}


@memo
def closure_census() -> Dict[str, object]:
    """AND and OR over all pairs of distinct octads: how often a codeword."""
    code = mog.GolayCode()
    octads = [c for c in code.codeword_masks if popcount(c) == 8]
    pairs = and_ok = or_ok = 0
    for a, b in combinations(octads, 2):
        pairs += 1
        and_ok += code.is_codeword(a & b)
        or_ok += code.is_codeword(a | b)
    return {"octad_pairs": pairs, "and_codeword": and_ok, "or_codeword": or_ok,
            "and_closed_fraction": Fraction(and_ok, pairs),
            "or_closed_fraction": Fraction(or_ok, pairs)}


def descent_check() -> Dict[str, object]:
    """Round 2's "descent in exactly d steps", against the exhaustive census."""
    from . import deep_dive as dd
    trapped = dd.trapped_census()
    greedy = dd.greedy_descent_census()
    return {"trapped": trapped["trapped"], "joint": dict(trapped["joint_census"]),
            "greedy_is_not_optimal": greedy["greedy_is_not_optimal"],
            "holds": trapped["trapped"] == 0}


# ===========================================================================
# 5.  THE FORTY-NINE RETAINED-NUM ROWS
# ===========================================================================

NUMERIC_CATEGORIES = ("external", "unit-dependent", "not-a-measurement",
                      "KB-internal", "restatement", "duplicate", "structural")

#: law id -> (category, reason).
NUMERIC_GRADES: Dict[str, Tuple[str, str]] = {
    "LAW_LEPTON_001": ("external", "m_mu/m_e"),
    "LAW_PHYSICS_MUON_002": ("external", "m_mu/m_e"),
    "LAW_BARYON_001": ("external", "m_p/m_e"),
    "LAW_NUM_001": ("external", "m_tau/m_mu"),
    "LAW_PARTICLE_RESONANCE_001": ("external", "m_tau/m_e (and the Cabibbo formula)"),
    "LAW_TAU_RESONANCE_001": ("external", "m_tau/m_e"),
    "LAW_CABIBBO_MIXING_001": ("external", "|V_us|"),
    "LAW_CKM_SHEAR_001": ("external", "|V_ub| and |V_cb|"),
    "LAW_WEINBERG_RESONANCE_001": ("external", "sin^2 theta_W"),
    "LAW_HIGGS_TENSION_001": ("external", "m_H/m_Z"),
    "LAW_FORCE_002": ("external", "1/alpha"),
    "LAW_HORIZON_001": ("external", "1/alpha as the integer 137"),
    "LAW_PHYSICS_001_REFINED": ("external", "1/alpha"),
    "LAW_PHYSICS_003_REFINED": ("external", "electron EM/gravity force ratio"),
    "LAW_MECH_001": ("external", "m_p/m_e and m_mu/m_e as powers of Y"),
    "LAW_MESON_PION_001": ("external", "m_pi0/m_e"),
    "LAW_ISOTOPIC_FRICTION_001": ("external", "deuterium/hydrogen mass ratio"),
    "LAW_TOP_KISSING_001": ("external", "m_top/m_e"),
    "LAW_NOBLE_SCALING_001": ("external", "noble-gas boiling-point ratios"),
    "LAW_REF_INVARIANT_001": ("duplicate", "the formula and target of LAW_BARYON_001"),
    "LAW_HORIZON_002": ("duplicate", "the 137 anchor of LAW_HORIZON_001"),
    "LAW_GRAVITY_RESONANCE_001": ("duplicate", "the G formula of LAW_PHYSICS_GRAVITY_001"),
    "LAW_GEAR_G13_001": ("duplicate", "13/L = 169/w is LAW_PHYSICS_MUON_002; its isospin "
                         "formula is in MeV"),
    "LAW_FORCE_003": ("unit-dependent", "m_W and m_Z as multiples of 1/Y in GeV"),
    "LAW_FORCE_005": ("unit-dependent", "m_H in GeV"),
    "LAW_COSMOS_001_REFINED": ("unit-dependent", "H0 in km/s/Mpc"),
    "LAW_GEAR_G15_001": ("unit-dependent", "the N-Delta gap in MeV"),
    "LAW_PHYSICS_GRAVITY_001": ("unit-dependent", "G in SI units"),
    "LAW_CHEM_002": ("unit-dependent", "the water bond angle in degrees"),
    "LAW_TERRESTRIAL_GRID_001": ("unit-dependent", "a period in seconds"),
    "LAW_NEUTRINO_003": ("not-a-measurement", "an upper bound on the neutrino mass sum"),
    "LAW_NEUTRINO_SHADOW_001": ("not-a-measurement", "a cosmological range, not a value"),
    "LAW_MEASURE_003": ("not-a-measurement", "the experimental uncertainty of G"),
    "LAW_WEAK_ISOSPIN_001": ("restatement", "m_W/m_Z = cos theta_W, the tree-level "
                             "on-shell identity"),
    "LAW_BERRY_PHASE_RESONANCE_001": ("KB-internal", "8Y+1 = 3.1174 is the KB's own "
                                      "number; it is 0.77% from pi"),
    "LAW_BIO_GOLD_001": ("KB-internal", "Y*25/32 = 20.7% is the KB's own number"),
    "LAW_BIO_GOLD_002": ("KB-internal", "Y*25/32 = 20.7% is the KB's own number"),
    "LAW_FIELD_CARFE_001": ("KB-internal", "(23/24)/phi reproduces the KB's 0.592282"),
    "LAW_GEO_002": ("KB-internal", "log2(1/Y) = 1.918 is the KB's own number"),
    "LAW_MAT_STEEL_001": ("KB-internal", "11/12 + Y/24 reproduces the KB's 0.9277"),
    "LAW_MINERAL_001": ("KB-internal", "Y/pi^2 = 2.68% is the KB's own number"),
    "LAW_NSC_THUNDER_001": ("KB-internal", "phi*pi^2/e reproduces the KB's 5.8748"),
    "LAW_NUM_COLLATZ_002": ("KB-internal", "25*pi/7 reproduces the KB's 11.22"),
    "LAW_PHASE_RESONANCE_001": ("KB-internal", "1/(8Y) reproduces the KB's 0.472277"),
    "LAW_PHYSICS_MAXWELL_003": ("KB-internal", "9/484 = (3/22)^2 is an identity of "
                                "the KB's own numbers"),
    "LAW_PROJECTION_DOT_001": ("KB-internal", "i^i is real mathematics; 187 is the "
                               "KB's own number"),
    "LAW_QUANTUM_PROB_002": ("KB-internal", "e/12 reproduces the KB's 0.2265"),
    "LAW_VTE_QUANTIZATION_001": ("KB-internal", "a declared approximation to 1/phi"),
    "LAW_STORAGE_HARDENED_001": ("structural", "a decoder statement; decided exactly "
                                 "by the outcome table"),
}


class Template:
    """A formula with its small integers turned into slots.

    ``value(**slots)`` is the formula; ``ranges`` the declared slot ranges;
    ``instance`` the law's own slot values; ``target`` the value quoted in
    Round 2's numeric battery.
    """

    def __init__(self, key: str, law: str, notation: str,
                 value: Callable[..., Fraction],
                 ranges: Dict[str, Sequence[int]], instance: Dict[str, int],
                 target: Fraction, quantity: str) -> None:
        self.key, self.law, self.notation = key, law, notation
        self.value, self.ranges, self.instance = value, ranges, instance
        self.target, self.quantity = Fraction(target), quantity

    def members(self):
        names = list(self.ranges)

        def walk(i: int, chosen: Dict[str, int]):
            if i == len(names):
                yield dict(chosen)
                return
            for v in self.ranges[names[i]]:
                chosen[names[i]] = v
                yield from walk(i + 1, chosen)
        yield from walk(0, {})

    def size(self) -> int:
        out = 1
        for r in self.ranges.values():
            out *= len(r)
        return out


def _r(lo: int, hi: int) -> range:
    return range(lo, hi + 1)


def _yp(n: int) -> Fraction:
    return _c("Y") ** n if n >= 0 else _c("Yinv") ** (-n)


@memo
def _yroot100() -> Fraction:
    return _root(1 / _c("Y"), 100)


@memo
def _yinv_hundredths() -> Tuple[Fraction, ...]:
    """``(1/Y)^(a/100)`` for ``a = 0 .. 800``, by repeated multiplication."""
    r = _yroot100()
    out = [Fraction(1)]
    for _ in range(800):
        out.append(_grid(out[-1] * r))
    return tuple(out)


def _templates() -> Tuple[Template, ...]:
    Y, Yi = _c("Y"), _c("Yinv")
    D = Fraction
    return (
        Template("lepton", "LAW_LEPTON_001", "(1/Y)^a + b - Y^c",
                 lambda a, b, c: Yi ** a + b - Y ** c,
                 {"a": _r(1, 6), "b": _r(0, 24), "c": _r(1, 6)},
                 {"a": 4, "b": 3, "c": 4}, D("206.768283"), "m_mu/m_e"),
        Template("muon", "LAW_PHYSICS_MUON_002", "a^2/w",
                 lambda a: D(a * a) / _c("w"), {"a": _r(1, 24)}, {"a": 13},
                 D("206.768283"), "m_mu/m_e"),
        Template("baryon", "LAW_BARYON_001", "a*(1/Y)^b + (1/Y - c) - Y",
                 lambda a, b, c: a * Yi ** b + (Yi - c) - Y,
                 {"a": _r(1, 24), "b": _r(1, 6), "c": _r(0, 24)},
                 {"a": 9, "b": 4, "c": 1}, D("1836.15267343"), "m_p/m_e"),
        Template("tau_mu", "LAW_NUM_001", "(1/Y)^a + (1/Y - c) - Y",
                 lambda a, c: Yi ** a + (Yi - c) - Y,
                 {"a": _r(1, 6), "c": _r(0, 24)}, {"a": 2, "c": 1},
                 D("16.817"), "m_tau/m_mu"),
        Template("tau_old", "LAW_PARTICLE_RESONANCE_001", "a*(1/Y)^b + c/Y + Y",
                 lambda a, b, c: a * Yi ** b + c * Yi + Y,
                 {"a": _r(1, 24), "b": _r(1, 6), "c": _r(0, 24)},
                 {"a": 17, "b": 4, "c": 2}, D("3477.15"), "m_tau/m_e"),
        Template("tau", "LAW_TAU_RESONANCE_001",
                 "[17/Y^4 + 2/Y + Y] + (1/Y)*a/b + c*Y",
                 lambda a, b, c: 17 * Yi ** 4 + 2 * Yi + Y + Yi * D(a, b) + c * Y,
                 {"a": _r(1, 24), "b": _r(1, 24), "c": _r(0, 24)},
                 {"a": 24, "b": 23, "c": 8}, D("3477.15"), "m_tau/m_e"),
        Template("cabibbo", "LAW_CABIBBO_MIXING_001", "(Y/(1+Y))*a/b + Y/c",
                 lambda a, b, c: (Y / (1 + Y)) * D(a, b) + Y / c,
                 {"a": _r(1, 24), "b": _r(1, 24), "c": _r(1, 48)},
                 {"a": 24, "b": 23, "c": 40}, D("0.2243"), "|V_us|"),
        Template("vub", "LAW_CKM_SHEAR_001", "Y^a / b",
                 lambda a, b: Y ** a / b, {"a": _r(1, 6), "b": _r(1, 24)},
                 {"a": 3, "b": 5}, D("0.00368"), "|V_ub|"),
        Template("vcb", "LAW_CKM_SHEAR_001", "Y^a * b / c",
                 lambda a, b, c: Y ** a * D(b, c),
                 {"a": _r(1, 6), "b": _r(1, 24), "c": _r(1, 48)},
                 {"a": 2, "b": 24, "c": 40}, D("0.041"), "|V_cb|"),
        Template("weinberg", "LAW_WEINBERG_RESONANCE_001", "Y / (1 + phi/a)",
                 lambda a: Y / (1 + _c("phi") / a), {"a": _r(1, 24)}, {"a": 12},
                 D("0.23122"), "sin^2 theta_W"),
        Template("higgs", "LAW_HIGGS_TENSION_001", "(1 + Y*sqrt(a)) - Y/b",
                 lambda a, b: 1 + Y * _SQRT[a] - Y / b,
                 {"a": _r(1, 24), "b": _r(1, 240)}, {"a": 2, "b": 120},
                 D("125.25") / D("91.1876"), "m_H/m_Z"),
        Template("alpha", "LAW_FORCE_002", "(1/Y)^a + b + c*Y^d/2",
                 lambda a, b, c, d: Yi ** a + b + D(c, 2) * Y ** d,
                 {"a": _r(1, 6), "b": _r(0, 100), "c": _r(1, 24), "d": _r(1, 6)},
                 {"a": 3, "b": 83, "c": 3, "d": 2}, D("137.035999"), "1/alpha"),
        Template("horizon", "LAW_HORIZON_001", "a",
                 lambda a: D(a), {"a": _r(1, 200)}, {"a": 137},
                 D("137.035999"), "1/alpha"),
        Template("alpha_pi", "LAW_PHYSICS_001_REFINED", "a*((pi - 1) - b/13824)",
                 lambda a, b: a * ((_c("pi") - 1) - D(b, 13824)),
                 {"a": _r(1, 128), "b": _r(1, 24)}, {"a": 64, "b": 8},
                 D("137.035999"), "1/alpha"),
        Template("hierarchy", "LAW_PHYSICS_003_REFINED", "196560^a * (1/Y) / b",
                 lambda a, b: D(196560) ** a * Yi / b,
                 {"a": _r(1, 12), "b": _r(1, 24)}, {"a": 8, "b": 2},
                 D("4.17e42"), "EM/gravity force ratio"),
        Template("gear_baryon", "LAW_MECH_001", "Y^(-a/100)",
                 lambda a: _yinv_hundredths()[a], {"a": _r(100, 800)}, {"a": 565},
                 D("1836.15267343"), "m_p/m_e"),
        Template("gear_lepton", "LAW_MECH_001", "Y^(-a)",
                 lambda a: Yi ** a, {"a": _r(1, 12)}, {"a": 4},
                 D("206.768283"), "m_mu/m_e"),
        Template("pion", "LAW_MESON_PION_001", "a * 10^b * Y",
                 lambda a, b: a * 10 ** b * Y, {"a": _r(1, 24), "b": _r(0, 4)},
                 {"a": 1, "b": 3}, D("264.153"), "m_pi0/m_e"),
        Template("isotope", "LAW_ISOTOPIC_FRICTION_001", "2 - RG/a",
                 lambda a: 2 - _c("RG") / a, {"a": _r(1, 48)}, {"a": 24},
                 D("1.99785"), "m_D/m_H"),
        Template("top", "LAW_TOP_KISSING_001", "196560 * sqrt(a) * (1 - Y/b)",
                 lambda a, b: 196560 * _SQRT[a] * (1 - Y / b),
                 {"a": _r(1, 24), "b": _r(1, 48)}, {"a": 3, "b": 24},
                 D(337941), "m_top/m_e"),
        Template("argon", "LAW_NOBLE_SCALING_001", "Y^(a/b)",
                 lambda a, b: _yfrac(a, b), {"a": _r(1, 6), "b": _r(1, 6)},
                 {"a": 2, "b": 3}, D("87.3") / D("211.5"), "BP(Ar)/BP(Rn)"),
    )


class _SqrtTable(dict):
    def __missing__(self, a: int) -> Fraction:
        v = _sqrt(Fraction(a))
        self[a] = v
        return v


_SQRT = _SqrtTable()


def _yfrac(a: int, b: int) -> Fraction:
    return _root(_c("Y") ** a, b)


@memo
def _template_tuple() -> Tuple[Template, ...]:
    return _templates()


def TEMPLATES() -> Tuple[Template, ...]:  # noqa: N802 -- a declared table
    """The declared templates of §1.5, in order."""
    return _template_tuple()


def look_elsewhere(value: Callable[..., Fraction], ranges: Dict[str, Sequence[int]],
                   instance: Dict[str, int], target: Fraction) -> Dict[str, object]:
    """The within-template look-elsewhere test for one claim.

    ``eps`` is the claim's own relative error.  ``p`` is the fraction of the
    window ``[T/2, 2T]`` lying within relative error ``eps`` of some member of
    the template (linear measure): the chance a target drawn uniformly from the
    window is hit at least as well.  Admitted when ``p < ADMIT_BELOW``.
    """
    template = Template("adhoc", "", "", value, ranges, instance, target, "")
    return _look(template)


def _member_values(t: Template) -> Tuple[Fraction, ...]:
    return tuple(v for v in (Fraction(t.value(**slots)) for slots in t.members())
                 if v > 0)


def _coverage(values: Sequence[Fraction], target: Fraction, eps: Fraction) -> Tuple[Fraction, int]:
    """Fraction of ``[T/2, 2T]`` within relative ``eps`` of some value."""
    lo, hi = target / 2, 2 * target
    intervals = []
    for v in values:
        a, b = _grid(v * (1 - eps), 64), _grid(v * (1 + eps), 64)
        if b < lo or a > hi:
            continue
        intervals.append((max(a, lo), min(b, hi)))
    intervals.sort()
    covered = Fraction(0)
    cur_a: Optional[Fraction] = None
    cur_b = Fraction(0)
    for a, b in intervals:
        if cur_a is None:
            cur_a, cur_b = a, b
        elif a <= cur_b:
            cur_b = max(cur_b, b)
        else:
            covered += cur_b - cur_a
            cur_a, cur_b = a, b
    if cur_a is not None:
        covered += cur_b - cur_a
    return covered / (hi - lo), len(intervals)


def _look(t: Template) -> Dict[str, object]:
    own = Fraction(t.value(**t.instance))
    eps = abs(own - t.target) / t.target
    p, in_window = _coverage(_member_values(t), t.target, eps)
    return {"value": own, "eps": eps, "members": t.size(),
            "in_window": in_window, "p": p, "admitted": p < ADMIT_BELOW}


#: Decoy targets per template in the calibration control.
DECOYS = 100


def decoy_control(key: str, decoys: int = DECOYS) -> Dict[str, object]:
    """How often the test admits a numerologist's best fit to a decoy target.

    Decoys are ``decoys`` targets evenly spaced across ``[T/2, 2T]``.  For each
    the template's best-fitting member is taken as the "law", exactly as a
    search would take it, and the test is run at that member's own error.  The
    admission rate is the test's false-admission rate on that template.
    """
    t = next(x for x in TEMPLATES() if x.key == key)
    values = _member_values(t)
    lo, width = t.target / 2, 3 * t.target / 2
    admitted = 0
    for i in range(decoys):
        target = lo + (2 * i + 1) * width / (2 * decoys)
        eps = min(abs(v - target) for v in values) / target
        p, _ = _coverage(values, target, eps)
        admitted += p < ADMIT_BELOW
    return {"key": key, "decoys": decoys, "admitted": admitted,
            "rate": Fraction(admitted, decoys)}


#: Measured standard uncertainties of targets whose formulas are admitted
#: (CODATA 2018: m_mu/m_e = 206.7682830(46)).
MEASURED_UNCERTAINTY = {"m_mu/m_e": Fraction("0.0000046")}


def sigma_distance(key: str) -> Optional[Fraction]:
    """How many measured standard deviations an admitted formula misses by."""
    t = next(x for x in TEMPLATES() if x.key == key)
    u = MEASURED_UNCERTAINTY.get(t.quantity)
    if u is None:
        return None
    return abs(Fraction(t.value(**t.instance)) - t.target) / u


@memo
def _template_results() -> Tuple[Dict[str, object], ...]:
    out = []
    for t in TEMPLATES():
        r = _look(t)
        out.append({"key": t.key, "law": t.law, "template": t.notation,
                    "quantity": t.quantity, "target": _decimal(t.target, 8),
                    "value": _decimal(r["value"], 8),
                    "error_pct": _decimal(100 * r["eps"], 4),
                    "members": r["members"], "in_window": r["in_window"],
                    "p": r["p"], "p_decimal": _decimal(r["p"], 4),
                    "admitted": r["admitted"]})
    return tuple(out)


def template_result(key: str) -> Optional[Dict[str, object]]:
    for r in _template_results():
        if r["key"] == key:
            return r
    return None


def numeric_regrade() -> Dict[str, object]:
    """The forty-nine rows, categorised, with the look-elsewhere results."""
    rows = [r for r in register_rows() if r["verdict"] == "RETAINED-NUM"]
    results = _template_results()
    graded = []
    for r in rows:
        category, reason = NUMERIC_GRADES[r["ubp_id"]]
        tests = [t for t in results if t["law"] == r["ubp_id"]]
        graded.append({"id": r["ubp_id"], "category": category, "reason": reason,
                       "tests": [t["key"] for t in tests]})
    census = {c: sum(1 for g in graded if g["category"] == c) for c in NUMERIC_CATEGORIES}
    admitted = [t for t in results if t["admitted"]]
    controls = {t["key"]: decoy_control(t["key"]) for t in admitted}
    sigmas = {t["key"]: sigma_distance(t["key"]) for t in admitted}
    return {"decoy_controls": controls, "sigma_distance": sigmas,"rows": graded, "census": census, "templates": list(results),
            "formulas_tested": len(results), "formulas_admitted": len(admitted),
            "admitted": [t["key"] for t in admitted],
            "laws_admitted": sorted({t["law"] for t in admitted}),
            "expected_false_admissions": ADMIT_BELOW * len(results)}


def admit(law_id: str) -> Dict[str, object]:
    """The admission verdict for one retained law: admitted, or refused by name."""
    r = row(law_id)
    if r is None:
        return {"id": law_id, "known": False, "verdict": "unknown",
                "reason": "not one of the 65 retained laws"}
    if r["verdict"] == "RETAINED-EXACT":
        klass, finding, lean = EXACT_GRADES[law_id]
        return {"id": law_id, "known": True, "kind": "exact", "class": klass,
                "verdict": "admitted" if klass in ("structural", "definitional")
                else ("admitted in part" if klass == "overclaimed" else "refused"),
                "reason": finding, "lean": [f"{f}:{t}" for f, t in lean]}
    category, reason = NUMERIC_GRADES[law_id]
    if category == "structural":
        s = storage_hardened()
        return {"id": law_id, "known": True, "kind": "numeric", "class": category,
                "verdict": "refused" if not s["holds"] else "admitted",
                "reason": f"at noise 3% a complete decoder is not right with "
                          f"probability {s['not_right_decimal']} and wrong with "
                          f"probability {s['wrong_decimal']}; not 100% integrity",
                "lean": [f"{LEAN_FILE}:unique_leader_iff"]}
    if category != "external":
        return {"id": law_id, "known": True, "kind": "numeric", "class": category,
                "verdict": "refused", "reason": f"{category}: {reason}", "lean": []}
    tests = [t for t in _template_results() if t["law"] == law_id]
    ok = [t for t in tests if t["admitted"]]
    verdict = "admitted" if ok and len(ok) == len(tests) else (
        "admitted in part" if ok else "refused")
    said = "; ".join(f"{t['quantity']}: error {t['error_pct']}%, chance "
                     f"coverage {t['p_decimal']} over {t['members']} template members"
                     for t in tests)
    for t in ok:
        sigma = sigma_distance(t["key"])
        if sigma is not None:
            said += (f"; not chance within its template, but it misses the "
                     f"measured value by {_decimal(sigma, 0)} standard "
                     f"deviations, so it is an approximation, not a law")
    return {"id": law_id, "known": True, "kind": "numeric", "class": category,
            "verdict": verdict, "reason": said, "lean": []}


# ===========================================================================
# 6.  THE REPORT
# ===========================================================================

def lean_citations() -> Tuple[Tuple[str, str], ...]:
    """Every (Lean file, theorem) the re-grade cites, in order, without repeats."""
    seen: List[Tuple[str, str]] = []
    for _, _, lean in EXACT_GRADES.values():
        for pair in lean:
            if pair not in seen:
                seen.append(pair)
    return tuple(seen)


def law_register_report() -> Dict[str, object]:
    """Every measurement of ``studies/LAW_REGISTER_STUDY.md`` and its marks."""
    exact = exact_regrade()
    outcomes = decoder_outcomes()
    enum = coset_enumerators()
    storage = storage_hardened()
    price = refusal_price()
    moments = moment_census()
    means = nrci_means()
    closure = closure_census()
    descent = descent_check()
    numeric = numeric_regrade()
    refusals = [admit(r["ubp_id"]) for r in register_rows()
                if r["verdict"] == "RETAINED-NUM"
                and NUMERIC_GRADES[r["ubp_id"]][0] not in ("external",)]
    marks = {
        "R1": exact["arithmetic_reproduces"],
        "R2": (sum(exact["census"].values()) == 16
               and all(g["lean"] for g in exact["rows"]
                       if g["class"] in ("structural", "overclaimed"))),
        "R3": (outcomes["exact"] and enum["leaders_agree"]
               and enum["closes_to_binomial"] and outcomes["right_iff_le_three"]
               and outcomes["weight_four_all_refused"]
               and outcomes["weight_five_all_wrong"]),
        "R4": len(price) == 3,
        "R5": not means["equal"] and means["agree_as_quoted"]
              and moments["agree_through"] == 7,
        "R6": "holds" in descent,
        "R7": sum(numeric["census"].values()) == 49,
        "R8": numeric["formulas_tested"] == len(TEMPLATES()),
        "R9": all(r["verdict"] == "refused" for r in refusals),
    }
    return {"exact": exact, "decoder": outcomes, "enumerators": enum,
            "storage_hardened": storage, "refusal_price": price,
            "moments": moments, "nrci_means": means, "closure": closure,
            "descent": descent, "numeric": numeric, "marks": marks}


def tool_summary(arg: str = "") -> Dict[str, object]:
    """The toolbox reading: one law's verdict, or the register's census."""
    arg = (arg or "").strip()
    if arg:
        law = arg if arg.upper().startswith("LAW_") else "LAW_" + arg
        return {"law": admit(law.upper())}
    numeric = numeric_regrade()
    exact = exact_regrade()
    return {"exact_census": exact["census"], "numeric_census": numeric["census"],
            "formulas_tested": numeric["formulas_tested"],
            "formulas_admitted": numeric["formulas_admitted"],
            "admitted": numeric["admitted"]}
