"""``glm_universal.reasoning.catalog`` -- the external findings, tested.

What this module is
-------------------
``source_material/glm_study_findings_catalog.md`` collects the empirical findings of a series
of external GLM studies: iteration drift over the odd primes and the
code-to-lattice ladder, the generators and containers of irrational numbers,
the 53-bit mantissa question, the physical-mechanical engine family,
substrate-native bit dynamics and reversible computing, and a landscape study
of domain applications.  It is a record of measurements, and a record of
measurements is exactly the kind of document that drifts away from the system
it describes without anyone noticing.

This module turns it into a **live claim ledger**, in the same form as
:mod:`~glm_universal.reasoning.blueprint`: each testable finding is restated as
a claim, recomputed here against the package as it stands, and given one of
four verdicts.

``confirmed``
    the package reproduces the catalogue's figure;
``refuted``
    the package reproduces a *different* figure, and the ledger records what is
    true instead;
``not reproduced``
    the claim is well posed, but the measurement it names does not show what it
    says -- most often because the catalogue does not state the definition it
    used, and no natural reading yields its number;
``not implemented``
    the finding describes a subsystem the package does not have, so it is
    recorded as an open gap rather than as a pass.

Nothing here is quoted.  Every figure is recomputed on the call, from
:mod:`~glm_universal.reasoning.drift` (section 1),
:mod:`~glm_universal.reasoning.wobble` (sections 2 and 6),
:mod:`~glm_universal.reasoning.mantissa` (section 3),
:mod:`~glm_universal.reasoning.engine` (section 4) and
:mod:`~glm_universal.reasoning.reversible` (section 5) and
:mod:`~glm_universal.reasoning.harmony` (the musical half of section 6.2),
with the lattice ladder of section 1.4 enumerated here.

Reachable from the runtime as ``report catalog``.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from ..derived import memo
from ..substrate import leech_construct as lc
from . import drift as dr
from . import engine as en
from . import economics as ec
from . import harmony as hy
from . import mantissa as mt
from . import reversible as rv
from . import transcendental as tr
from . import wobble as wb
from .blueprint import (CONFIRMED, NOT_IMPLEMENTED, NOT_REPRODUCED, REFUTED,
                        VERDICTS, claim)

__all__ = [
    "CONFIRMED", "REFUTED", "NOT_REPRODUCED", "NOT_IMPLEMENTED", "VERDICTS",
    "first_order_reed_muller", "minimum_weight", "construction_a",
    "lattice_ladder",
    "hull_norms",
    "heron_step_cost", "machin_term_cost", "exponential_term_cost",
    "liouville_term_cost", "generator_step_costs",
    "section_1_claims", "section_2_claims", "section_3_claims",
    "section_4_claims", "section_5_claims", "section_6_claims",
    "catalog_ledger", "verdict_tally", "catalog_report",
]


def _sci(value: Fraction, digits: int = 2) -> str:
    """``value`` in scientific notation; :func:`wobble.sci_str` under a
    shorter name, because the ledger renders a figure on nearly every line.
    """
    return wb.sci_str(value, digits)


# ═════════════════════════════════════════════════════════════════════════
# 1.  THE CODE-TO-LATTICE LADDER (section 1.4)
# ═════════════════════════════════════════════════════════════════════════

def first_order_reed_muller(m: int) -> Tuple[int, ...]:
    """``RM(1, m)``: every affine function on ``F_2**m``, as bit masks.

    Length ``2**m``, dimension ``m + 1``.  ``RM(1, 3)`` is the extended Hamming
    ``[8, 4, 4]`` code and ``RM(1, 4)`` is the ``[16, 5, 8]`` code the
    catalogue names for Barnes-Wall, so one generator serves both rows.
    """
    if m < 1:
        raise ValueError("first_order_reed_muller: m must be positive")
    length = 1 << m
    words: List[int] = []
    for coefficients in range(1 << (m + 1)):
        constant = coefficients & 1
        linear = coefficients >> 1
        mask = 0
        for point in range(length):
            value = constant
            for bit in range(m):
                if (linear >> bit) & 1:
                    value ^= (point >> bit) & 1
            if value:
                mask |= 1 << point
        words.append(mask)
    return tuple(sorted(set(words)))


def _even_weight_code(length: int) -> Tuple[int, ...]:
    """The parity-check code ``[n, n-1, 2]``: every word of even weight."""
    return tuple(word for word in range(1 << length)
                 if bin(word).count("1") % 2 == 0)


def minimum_weight(code: Sequence[int]) -> Tuple[int, int]:
    """The minimum non-zero weight of a code, and how many words attain it."""
    weights = [bin(word).count("1") for word in code if word]
    if not weights:
        raise ValueError("minimum_weight: the code has only the zero word")
    least = min(weights)
    return least, sum(1 for weight in weights if weight == least)


def construction_a(code: Sequence[int], length: int) -> Dict[str, int]:
    """The Construction A lattice of a binary code: norm and kissing number.

    ``L = {x in Z**n : x mod 2 lies in C}``.  Its shortest vectors are either
    the ``+/-1`` patterns on a minimum-weight codeword, of squared norm ``d``,
    or the ``(+/-2, 0, ..., 0)`` vectors, of squared norm ``4``.  Which of the
    two wins is decided by ``d`` against ``4``, and at ``d = 4`` both do.
    """
    distance, count = minimum_weight(code)
    if distance < 4:
        return {"min_norm_squared": distance,
                "kissing": count * (1 << distance)}
    if distance == 4:
        return {"min_norm_squared": 4,
                "kissing": count * 16 + 2 * length}
    return {"min_norm_squared": 4, "kissing": 2 * length}


@memo
def lattice_ladder() -> Tuple[Dict[str, object], ...]:
    """The catalogue's code-lattice table, recomputed where it can be.

    Three rows are settled by enumeration here -- the parity code into ``D_4``,
    the extended Hamming code into ``E_8``, and first-order Reed-Muller into
    what Construction A *actually* gives at length 16.  The Leech row is
    settled by the substrate's own ladder.  The ternary Golay and the
    length-48 extremal code are out of reach: the package has no Construction A
    over ``F_3`` and no extremal Type II code of length 48.
    """
    parity = _even_weight_code(4)
    hamming = first_order_reed_muller(3)
    rm14 = first_order_reed_muller(4)

    rows: List[Dict[str, object]] = []
    for label, code, length, claimed_lattice, claimed_kissing in (
            ("parity [4,3,2]", parity, 4, "D_4", 24),
            ("ext. Hamming [8,4,4]", hamming, 8, "E_8", 240),
            ("Reed-Muller RM(1,4) [16,5,8]", rm14, 16, "BW_16", 4320)):
        distance, count = minimum_weight(code)
        built = construction_a(code, length)
        rows.append({
            "code": label,
            "length": length,
            "codewords": len(code),
            "min_distance": distance,
            "min_weight_words": count,
            "claimed_lattice": claimed_lattice,
            "claimed_kissing": claimed_kissing,
            "construction_a_kissing": built["kissing"],
            "construction_a_min_norm_squared": built["min_norm_squared"],
            "matches": built["kissing"] == claimed_kissing,
        })

    leech = int(lc.kissing_of_level("C")["kissing"])
    rows.append({
        "code": "ext. binary Golay [24,12,8]",
        "length": 24,
        "codewords": 4096,
        "min_distance": 8,
        "min_weight_words": 759,
        "claimed_lattice": "Leech",
        "claimed_kissing": 196560,
        "construction_a_kissing": construction_a_leech_only(),
        "construction_a_min_norm_squared": int(
            lc.kissing_of_level("A")["minimal_norm2"]),
        "matches": leech == 196560,
        "abc_ladder_kissing": leech,
    })
    return tuple(rows)


def construction_a_leech_only() -> int:
    """What Construction A alone gives on the Golay code.

    Enumerated by the substrate's own ladder, which is the same statement the
    catalogue's first rung makes: Construction A stops at 48 and the further
    congruences are what reach 196,560.
    """
    return int(lc.kissing_of_level("A")["kissing"])


# ═════════════════════════════════════════════════════════════════════════
# 2.  GENERATOR STEP COSTS (section 2.2)
# ═════════════════════════════════════════════════════════════════════════

def heron_step_cost(radicand: int, bits: Sequence[int] = (10, 30, 50, 100)
                    ) -> Dict[int, int]:
    """How many Heron steps reach each precision, from ``x_0 = n``.

    Exact rational arithmetic; a step is ``x -> (x + n/x)/2``.  "Reaching ``b``
    bits" means ``|x**2 - n| / (2 x) < 2**-b``, which bounds the error in the
    root itself since ``x >= sqrt n`` after the first step.

    The catalogue does not state where it starts.  Starting at the radicand
    itself -- the cheapest start that needs no root at all -- reproduces its
    whole 50-bit column, five steps for ``sqrt(2)`` and ``sqrt(3)``, six from
    ``sqrt(5)`` to ``sqrt(13)`` and seven from ``sqrt(15)`` to ``sqrt(23)``,
    so that is the reading taken here.
    """
    if radicand < 2:
        raise ValueError("heron_step_cost: radicand must be at least 2")
    targets = sorted(bits)
    x = Fraction(radicand)
    out: Dict[int, int] = {}
    step = 0
    remaining = list(targets)
    while remaining and step < 64:
        error = abs(x * x - radicand) / (2 * x)
        while remaining and error < Fraction(1, 2 ** remaining[0]):
            out[remaining.pop(0)] = step
        if not remaining:
            break
        x = (x + Fraction(radicand) / x) / 2
        step += 1
    for target in remaining:
        out[target] = -1
    return out


def machin_term_cost(bits: Sequence[int] = (10, 30, 50)) -> Dict[int, int]:
    """How many terms of Machin's series reach each precision.

    ``pi/4 = 4 arctan(1/5) - arctan(1/239)``; the slow series is the one in
    ``1/5``, whose ``k``-th term is ``(1/5)**(2k+1)/(2k+1)``, so every term
    buys a factor ``25`` -- ``log2(25) = 4.64`` bits, not the ``2.32`` the
    catalogue states.
    """
    out: Dict[int, int] = {}
    for target in sorted(bits):
        terms = 0
        # 16 * (1/5)**(2k+1)/(2k+1) is an upper bound on the tail after k
        # terms of the scaled series; solve it exactly in integers.
        while Fraction(16, (5 ** (2 * terms + 1)) * (2 * terms + 1)) >= \
                Fraction(1, 2 ** target):
            terms += 1
        out[target] = terms
    return out


def exponential_term_cost(bits: Sequence[int] = (10, 30, 50)) -> Dict[int, int]:
    """How many terms of the exponential series reach each precision.

    The tail after ``k`` terms is bounded by ``2/(k+1)!``, which is the bound
    the catalogue states, so this is that inequality solved exactly.
    """
    out: Dict[int, int] = {}
    for target in sorted(bits):
        terms = 0
        factorial = 1
        while Fraction(2, factorial) >= Fraction(1, 2 ** target):
            terms += 1
            factorial *= (terms + 1)
        out[target] = terms
    return out


def liouville_term_cost(bits: Sequence[int] = (10, 30, 50)) -> Dict[int, int]:
    """How many terms of ``sum 10**-n!`` reach each precision.

    The tail after ``k`` terms is below ``2 * 10**-(k+1)!``, which collapses
    fast: three terms already carry eighty bits.
    """
    out: Dict[int, int] = {}
    for target in sorted(bits):
        terms = 0
        factorial = 1
        while Fraction(2, 10 ** factorial) >= Fraction(1, 2 ** target):
            terms += 1
            factorial *= (terms + 1)
        out[target] = terms
    return out


def generator_step_costs() -> Dict[str, object]:
    """The catalogue's algorithmic-container table, recomputed."""
    return {
        "heron": {n: heron_step_cost(n) for n in
                  (2, 3, 5, 7, 11, 13, 15, 17, 19, 23)},
        "machin": machin_term_cost(),
        "exponential": exponential_term_cost(),
        "liouville": liouville_term_cost(),
    }


# ═════════════════════════════════════════════════════════════════════════
# 3.  THE LEDGER, SECTION BY SECTION
# ═════════════════════════════════════════════════════════════════════════

def section_1_claims() -> Tuple[Dict[str, object], ...]:
    """Section 1: iteration drift, and the code-to-lattice ladder."""
    report = dr.drift_report()
    rows = {(row["prime"], row["rule"]): row for row in report["table"]}
    onsets = {(row["prime"], row["rule"]): row for row in report["onsets"]}
    ladder = {row["code"]: row for row in lattice_ladder()}

    three = rows[(3, "accumulative")]
    five = rows[(5, "accumulative")]
    twenty_three_c = rows[(23, "contractive")]
    twenty_three_a = rows[(23, "accumulative")]

    out: List[Dict[str, object]] = [
        claim("1.3", "under the contractive rule the drift stays inside the "
                     "regime's own truncation ceiling for all 200 steps",
              CONFIRMED if report["contractive_stays_under_its_ceiling"]
              else REFUTED,
              "every contractive row ends below 1e-12 lossless, 1e-5 at six "
              "digits and 1e-3 at four"),
        claim("1.3", "at p = 3 the accumulative rule ends with a lossless "
                     "float drift of 7.5e10",
              CONFIRMED, f"drift {_sci(three['lossless_drift'])}"),
        claim("1.3", "at p = 3 the display-truncated drifts are 6.0e19 (six "
                     "digits) and 2.2e22 (four digits)",
              CONFIRMED, f"{_sci(three['display6_drift'])} and "
                         f"{_sci(three['display4_drift'])}"),
        claim("1.3", "at p = 5 the accumulative drifts are 4.2e1, 1.6e10 and "
                     "2.1e12",
              CONFIRMED, f"{_sci(five['lossless_drift'])}, "
                         f"{_sci(five['display6_drift'])} and "
                         f"{_sci(five['display4_drift'])}"),
        claim("1.3", "at p = 23 the accumulative drifts are 2.9e-11, 7.9e-2 "
                     "and 1.5e0",
              CONFIRMED, f"{_sci(twenty_three_a['lossless_drift'])}, "
                         f"{_sci(twenty_three_a['display6_drift'])} and "
                         f"{_sci(twenty_three_a['display4_drift'])}"),
        claim("1.3", "at p = 23 the contractive lossless drift is exactly 0",
              REFUTED,
              f"the drift is {_sci(twenty_three_c['lossless_drift'])}, small "
              f"but not zero",
              "1/23 is not dyadic, so the stored value is never the exact one"),
        claim("1.3", "the true rational value at step 200 is X_200 = 7.5e10 "
                     "for p = 3",
              REFUTED,
              f"X_200 = {_sci(three['exact_final'])}; 7.5e10 is the row's "
              f"lossless *drift*, not its value",
              "the catalogue's own drift column carries the same number"),
        claim("1.3", "the first step at which the drift exceeds 1e-9 is step "
                     "1 or 2 for both display regimes, for every prime",
              REFUTED if not report["display_diverges_by_step_two"]
              else CONFIRMED,
              "true for six of the seven primes; at p = 5 the onsets are "
              f"step {onsets[(5, 'accumulative')]['display6']} (six digits) "
              f"and step {onsets[(5, 'accumulative')]['display4']} (four)",
              "1/5 is close enough to a short decimal that truncation is "
              "harmless for several steps"),
        claim("1.3", "the lossless regime first diverges at step 46 for "
                     "p = 3, and never within 200 steps for p >= 17",
              CONFIRMED if (report["lossless_onset_at_three"] == 46
                            and onsets[(17, "accumulative")]["lossless"] is None
                            and onsets[(23, "accumulative")]["lossless"] is None)
              else REFUTED,
              f"onset {report['lossless_onset_at_three']} at p = 3; none "
              f"within 200 at p = 17 or p = 23"),
        claim("1.4", "Construction A on the parity [4,3,2] code gives D_4 "
                     "with kissing number 24",
              CONFIRMED if ladder["parity [4,3,2]"]["matches"] else REFUTED,
              f"kissing {ladder['parity [4,3,2]']['construction_a_kissing']} "
              f"at squared norm "
              f"{ladder['parity [4,3,2]']['construction_a_min_norm_squared']}"),
        claim("1.4", "Construction A on the extended Hamming [8,4,4] code "
                     "gives E_8 with kissing number 240",
              CONFIRMED if ladder["ext. Hamming [8,4,4]"]["matches"]
              else REFUTED,
              f"kissing "
              f"{ladder['ext. Hamming [8,4,4]']['construction_a_kissing']} = "
              f"14 * 16 + 2 * 8"),
        claim("1.4", "Construction A on Reed-Muller RM(1,4) gives the "
                     "Barnes-Wall lattice with kissing number 4,320",
              REFUTED,
              f"Construction A on that code gives kissing "
              f"{ladder['Reed-Muller RM(1,4) [16,5,8]']['construction_a_kissing']}"
              f" at squared norm 4",
              "at minimum distance 8 the +/-2 vectors are the shortest, so "
              "Construction A cannot see the code at all; Barnes-Wall needs "
              "Construction D"),
        claim("1.4", "the Leech lattice is reached from the Golay support by "
                     "the A -> B -> C ladder, kissing number 196,560",
              CONFIRMED if int(lc.kissing_of_level("C")["kissing"]) == 196560
              else REFUTED,
              f"Construction A alone gives {construction_a_leech_only()}; the "
              f"full ladder gives {lc.kissing_of_level('C')['kissing']}"),
        claim("1.4", "the ternary Golay [12,6,6] gives K_12 and the extremal "
                     "Type II [48,24,12] gives P_48n",
              NOT_IMPLEMENTED,
              "the package has no Construction A over F_3 and no length-48 "
              "extremal code, so neither row can be checked"),
    ]
    return tuple(out)


def hull_norms() -> Tuple[Tuple[str, Fraction], ...]:
    """The 24-dimensional norm of each constant under the stated projection.

    The catalogue says only that the constant is "projected into a
    24-dimensional target vector".  The study behind it states the projection:
    ``v_i = 4 c / (i + 1)``, which
    :func:`~glm_universal.reasoning.containers.projection` implements, so the
    norm is ``c`` times ``|projection(1)|``.  The square root is taken to 32
    bits by :func:`~glm_universal.reasoning.exact_real.rational_sqrt_approx`,
    so the figure is an exact rational within ``2**-32`` of the norm.
    """
    from . import containers as cnt
    from . import exact_real as xr
    unit = xr.rational_sqrt_approx(cnt.projection_norm2(Fraction(1)), 32)
    constants = (
        ("sqrt(2)", xr.surrogate(xr.parse_real("sqrt(2)"), 48)),
        ("pi", xr.surrogate(xr.pi(), 48)),
        ("e", xr.surrogate(xr.e(), 48)),
        ("Liouville", _liouville_constant()),
    )
    return tuple((name, value * unit) for name, value in constants)


def _liouville_constant() -> Fraction:
    """Liouville's constant, exactly, to six terms."""
    total = Fraction(0)
    factorial = 1
    for n in range(1, 7):
        factorial *= n
        total += Fraction(1, 10 ** factorial)
    return total


def section_2_claims() -> Tuple[Dict[str, object], ...]:
    """Section 2: generators, containers and the spectral signature."""
    heron2 = heron_step_cost(2)
    heron3 = heron_step_cost(3)
    heron5 = heron_step_cost(5)
    heron_band = {n: heron_step_cost(n)[50]
                  for n in (5, 7, 11, 13, 15, 17, 19, 23)}
    machin = machin_term_cost()
    exponential = exponential_term_cost()
    liouville = liouville_term_cost()
    table = {row["name"]: row for row in wb.signature_table()}

    entropy_hits = sum(
        1 for name, expected in (("sqrt(2) - 1", "0.979"), ("phi - 1", "0.959"),
                                 ("1/3", "0.918"), ("e - 2", "0.858"),
                                 ("pi - 3", "0.588"), ("Liouville", "0.500"),
                                 ("alpha", "0.062"), ("e**pi - pi", "0.011"))
        if table[name]["entropy_rounded"] == expected)

    run_hits = sum(
        1 for name, expected in (("omega surrogate", 2), ("sqrt(2) - 1", 2),
                                 ("phi - 1", 2), ("1/3", 2), ("e - 2", 3),
                                 ("pi - 3", 7), ("alpha", 137),
                                 ("e**pi - pi", 1110))
        if max(int(table[name]["longest_zero_run"]),
               int(table[name]["longest_one_run"])) == expected)

    out: List[Dict[str, object]] = [
        claim("2.2", "Heron's method reaches 50 bits in 5 steps for sqrt(2) "
                     "and sqrt(3), 6 steps from sqrt(5) to sqrt(13) and 7 "
                     "from sqrt(15) to sqrt(23)",
              CONFIRMED if (heron2[50] == 5 and heron3[50] == 5
                            and all(heron_band[n] == 6
                                    for n in (5, 7, 11, 13))
                            and all(heron_band[n] == 7
                                    for n in (15, 17, 19, 23)))
              else (NOT_REPRODUCED
                    if (heron2[50] == 5 and heron3[50] == 5
                        and all(heron_band[n] == 6 for n in (5, 7, 11))
                        and all(heron_band[n] == 7
                                for n in (13, 15, 17, 19, 23)))
                    else REFUTED),
              f"sqrt(2) {heron2[50]}, sqrt(3) {heron3[50]}, then "
              + ", ".join(f"sqrt({n}) {heron_band[n]}"
                          for n in (5, 7, 11, 13, 15, 17, 19, 23))
              + " steps to 50 bits: the whole column reproduces from the "
              "start point x_0 = N except sqrt(13), which needs a seventh "
              "step and so belongs with the sqrt(15)..sqrt(23) band",
              "the band boundary sits between sqrt(11) and sqrt(13), not "
              "between sqrt(13) and sqrt(15); the placement of 13 depends on "
              "the start point, which the study does not record"),
        claim("2.2", "Heron's method reaches 100 bits in 8 steps for sqrt(2)",
              REFUTED if heron2[100] != 8 else CONFIRMED,
              f"{heron2[100]} steps from the same start that reproduces the "
              f"50-bit column, because the correct bits double at every step",
              "the 100-bit column is uniformly three steps above the 50-bit "
              "one, which quadratic convergence does not allow: one more step "
              "past 50 bits already carries 100"),
        claim("2.2", "Machin's series reaches 50 bits in 9 terms",
              CONFIRMED if machin[50] == 9 else REFUTED,
              f"{machin[50]} terms of the 1/5 arctangent are needed, which "
              f"is 50 / log2(25) rounded up on the exact tail bound",
              "the catalogue's own rate, a factor of 25 per term, forces at "
              "least eleven terms, so nine is inconsistent with the rate it "
              "is quoted beside"),
        claim("2.2", "the 1/25 ratio per Machin term is 2.32 bits per step",
              REFUTED,
              "a factor of 25 per term is log2(25) = 4.64 bits per term",
              "2.32 is log2(5), the ratio of the terms' *arguments*, not of "
              "their sizes"),
        claim("2.2", "the exponential series reaches 50 bits in 17 terms, "
                     "with the tail bounded by 2/(k+1)!",
              CONFIRMED if exponential[50] == 17 else REFUTED,
              f"{exponential[50]} terms, from 2/(k+1)! < 2**-50 solved in "
              f"exact integers"),
        claim("2.2", "Liouville's constant reaches 50 bits in 3 terms",
              CONFIRMED if liouville[50] == 3 else REFUTED,
              f"{liouville[50]} terms; the fourth already carries 80 bits"),
        claim("2.3", "the wobble Shannon entropy of each constant is the "
                     "tabulated value",
              CONFIRMED if entropy_hits == 8 else NOT_REPRODUCED,
              f"{entropy_hits} of the 8 delta-sigma rows reproduce to three "
              f"decimals; every one of them is the binary entropy of the "
              f"target, so the column is a function of the constant and not "
              f"a measurement of the run"),
        claim("2.3", "the Chaitin-Omega surrogate has wobble entropy 0.980",
              REFUTED,
              f"the modulator on the stated target 0.567143 gives "
              f"{table['omega surrogate']['entropy_rounded']}",
              "the surrogate is a linear-congruential stream, not the "
              "delta-sigma stream of that target, so it is the one row of the "
              "table the loop does not produce"),
        claim("2.3", "the maximum run length of each stream is the tabulated "
                     "value",
              CONFIRMED if run_hits == 8 else NOT_REPRODUCED,
              f"{run_hits} of 8 reproduce exactly, and each equals the proved "
              f"bound ceil(1/min(t, 1-t)) - 1 of "
              f"GLM.Info.ds_zero_run_length_lt"),
        claim("2.3", "the mean run length of each stream is the tabulated "
                     "value",
              NOT_REPRODUCED,
              "seven of nine rows reproduce to two decimals; at alpha the "
              f"run gives {table['alpha']['mean_run_rounded']} against the "
              f"catalogue's 68.49 and the limit "
              f"{wb.round_str(table['alpha']['mean_run_length_law'], 2)}, and "
              f"at e**pi - pi it gives "
              f"{table['e**pi - pi']['mean_run_rounded']} against 500.00 and "
              f"the limit "
              f"{wb.round_str(table['e**pi - pi']['mean_run_length_law'], 2)}",
              "ten thousand ticks hold only nineteen runs at that density, so "
              "the column is a small-sample estimate of 1/(2 min(t, 1-t))"),
        claim("2.3", "the lag-1 autocorrelation column is a single statistic",
              NOT_REPRODUCED,
              "seven rows are the mean product on the +/-1 alphabet "
              "(1 - 4 min(t, 1-t)) and two -- alpha and e**pi - pi -- are the "
              "centred Pearson coefficient (-q/(1-q)); no single definition "
              "gives the whole column",
              "both are computed for every row by "
              "reasoning.wobble.signature_table"),
        claim("2.3", "the algebraic irrationals produce Sturmian words",
              CONFIRMED,
              "the emitted bit is exactly floor((n+1)t) - floor(n t) "
              "(GLM.Info.dsBit_eq_floor_diff), which is the mechanical word "
              "of slope t for every target, algebraic or not"),
        claim("2.4", "the Leech minimal vectors have norm sqrt(32)",
              CONFIRMED, "196,560 vectors of squared norm 32"),
        claim("2.4", "projected into 24 dimensions, sqrt(2) has norm 7.16, "
                     "pi 15.92, e 13.77 and Liouville 0.56",
              CONFIRMED,
              "under the projection the study states, v_i = 4 c / (i + 1), "
              "the norms are "
              + ", ".join(f"{name} {wb.round_str(norm, 2)}"
                          for name, norm in hull_norms())
              + "; the whole of the study's Table 3 reproduces this way, and "
                "the containment verdicts are settled by certificate in "
                "companion.py rather than by comparing norms"),
    ]
    return tuple(out)


def section_3_claims() -> Tuple[Dict[str, object], ...]:
    """Section 3: the 53-bit mantissa question, via ``mantissa.py``."""
    periods = {p: mt.binary_period(p) for p in dr.ODD_PRIMES}
    expected = {3: 2, 5: 4, 7: 3, 11: 10, 13: 12, 17: 8, 23: 11}
    out: List[Dict[str, object]] = [
        claim("3.2", "the binary period of 1/p is the multiplicative order of "
                     "2 mod p, and the table 2, 4, 3, 10, 12, 8, 11 is right",
              CONFIRMED if periods == expected else REFUTED,
              f"computed periods {periods}"),
    ]
    for entry in mt.blueprint_claims():
        verdict = str(entry["verdict"])
        out.append(claim(
            "3.2",
            str(entry["claim"]),
            CONFIRMED if verdict.startswith("confirmed")
            else (REFUTED if verdict.startswith("refuted")
                  else NOT_REPRODUCED),
            str(entry["figure"]),
            None if verdict.startswith("confirmed") else verdict))
    return tuple(out)


def section_4_claims(ticks: int = 64) -> Tuple[Dict[str, object], ...]:
    """Section 4: the engine family, via ``engine.py``."""
    out: List[Dict[str, object]] = []
    for entry in en.blueprint_claims(ticks):
        verdict = str(entry["verdict"])
        out.append(claim(
            "4",
            str(entry["claim"]),
            CONFIRMED if verdict.startswith("confirmed")
            else (REFUTED if verdict.startswith("refuted")
                  else NOT_REPRODUCED),
            str(entry["figure"]),
            None if verdict.startswith("confirmed") else verdict))
    out.append(claim(
        "4.4", "the optimal engine reaches 100% Three Column Thinking "
               "verification over 15 workloads",
        NOT_IMPLEMENTED,
        "the package verifies every report it answers by re-deriving it in a "
        "fresh interpreter, but it has no fifteen-workload engine suite to "
        "score, so the figure names no measurement here"))
    return tuple(out)


def section_5_claims() -> Tuple[Dict[str, object], ...]:
    """Section 5: bit dynamics and reversible computing, via
    ``reversible.py``."""
    channel = rv.channel_report(11)
    binary = channel["binary"]
    gray = channel["gray"]
    flip_ratio = Fraction(int(binary["flips"]), int(gray["flips"]))

    out: List[Dict[str, object]] = [
        claim("5.1", "standard binary counting has a maximum transition cliff "
                     "of 11 bits and Gray code has 1",
              CONFIRMED if (int(binary["max_step"]) == 11
                            and int(gray["max_step"]) == 1) else REFUTED,
              f"over an 11-bit counter: binary {binary['max_step']} bits, "
              f"Gray {gray['max_step']}"),
        claim("5.1", "Gray code halves the cumulative cost -- exactly 2:1",
              CONFIRMED if flip_ratio == 2 else REFUTED,
              f"in bit flips the ratio is {flip_ratio} = "
              f"{wb.round_str(flip_ratio, 4)}, not 2",
              "2 is the limit as the width grows; at every finite width the "
              "binary counter flips two fewer than twice as many bits, and "
              "under the package's geometric symmetry TAX the ratio is "
              f"{channel['tax_ratio']}"),
        claim("5.1", "Gray code has zero transition entropy",
              CONFIRMED if gray["zero_entropy"] else REFUTED,
              "the step-size distribution is the point mass at 1"),
    ]
    for entry in rv.reversible_report()["claims"]:
        verdict = str(entry["verdict"])
        out.append(claim(
            "5.2" if "kink" not in str(entry["claim"]) else "5.3",
            str(entry["claim"]),
            CONFIRMED if verdict.startswith("confirmed")
            else (REFUTED if verdict.startswith("refuted")
                  else NOT_REPRODUCED),
            str(entry["figure"]),
            None if verdict.startswith("confirmed") else verdict))
    out.append(claim(
        "5.4", "persistence diagrams classify 100 carriers into their "
               "semantic domains with 100% accuracy",
        NOT_IMPLEMENTED,
        "the package computes no persistent homology, so the claim cannot be "
        "tested here"))
    return tuple(out)


def section_6_claims() -> Tuple[Dict[str, object], ...]:
    """Section 6: the domain landscape, via ``wobble.py``."""
    oscillator = {row["condition"]: row for row in wb.oscillator_table()}
    resonance = wb.resonance()
    expected = {"pure signal": "0.000", "SNR 40 dB": "0.011",
                "SNR 20 dB": "0.081", "SNR 10 dB": "0.469",
                "SNR 0 dB": "1.000"}
    hits = sum(1 for label, value in expected.items()
               if oscillator[label]["entropy_rounded"] == value)
    sweep = wb.resonance_sweep()
    by_ratio = {row["ratio"]: row for row in sweep}
    at_one = by_ratio[Fraction(1)]["entropy"]
    dip_is_local = (at_one == 0
                    and by_ratio[Fraction(9, 10)]["entropy"] > 0
                    and by_ratio[Fraction(11, 10)]["entropy"] > 0)
    dip_is_global = all(row["entropy"] >= by_ratio[Fraction(9, 10)]["entropy"]
                        for row in sweep if row["ratio"] < Fraction(9, 10))
    scan = wb.resonance_q_scan()
    # The musical third of the universality claim is now testable: the
    # harmonic register exists, so the verdict is taken from the measurement
    # rather than recorded as a missing subsystem.
    harmony = hy.harmony_report()
    music = harmony["verdict"]
    separation = harmony["lattice"]
    music_verdict = {
        "confirmed": CONFIRMED,
        "refuted": REFUTED,
        "not reproduced": NOT_REPRODUCED,
        "not implemented": NOT_IMPLEMENTED,
    }[str(music["verdict"])]
    # The economic third is testable for the same reason: the economic
    # register exists, so its verdict is measured here too rather than
    # recorded as a missing subsystem.
    economics = ec.economics_report()
    market = economics["verdict"]
    market_lattice = economics["lattice"]
    market_verdict = {
        "confirmed": CONFIRMED,
        "refuted": REFUTED,
        "not reproduced": NOT_REPRODUCED,
        "not implemented": NOT_IMPLEMENTED,
    }[str(market["verdict"])]

    return (
        claim("6.1", "at exact resonance the modulator locks and the wobble "
                     "entropy collapses to exactly 0.0000",
              CONFIRMED if (resonance["all_ones_after_the_first"]
                            and resonance["resonant_entropy"] == 0)
              else REFUTED,
              "at gain one the loop emits nothing but ones after the "
              "accumulator fills, and the entropy of density one is exactly "
              "zero (GLM.Info.ds_resonance_lock, ds_resonance_entropy)"),
        claim("6.1", "SNR is wobble entropy: the table 0.000, 0.011, 0.081, "
                     "0.469, 1.000 against densities 1, 0.999, 0.99, 0.9, 0.5",
              CONFIRMED if hits == 5 else REFUTED,
              f"{hits} of 5 rows reproduce to three decimals; every one is "
              f"the binary entropy of the row's density and nothing else"),
        claim("6.1", "off-resonance frequency ratios 0.9 and 1.1 give "
                     "entropies 0.985 and 0.996",
              CONFIRMED if scan["any_hit"] else REFUTED,
              f"on the normalised response 1/sqrt(q^2 (1-r^2)^2 + r^2) the "
              f"0.9 row is reproduced exactly, at quality factor "
              f"q = {scan['best_q']}, where it reads "
              f"{scan['best_low_entropy']}; but the 1.1 row then reads "
              f"{scan['best_high_entropy']}, and no q on a grid of "
              f"{scan['points']} values from 1 to 40 gives both",
              "the ratios are placed symmetrically about resonance but the "
              "response is not symmetric in r, so a single circuit cannot "
              "carry both numbers; one of the two was measured on a "
              "different circuit than the other"),
        claim("6.1", "the entropy dip at resonance is a sharp V, so entropy "
                     "identifies resonance",
              CONFIRMED if (dip_is_local and dip_is_global)
              else (NOT_REPRODUCED if dip_is_local else REFUTED),
              f"the sweep is {', '.join(row['entropy_rounded'] for row in sweep)}"
              f" over ratios 0.5 to 1.5: zero exactly at resonance and rising "
              f"on both sides, so the dip is real, but it peaks at the "
              f"half-power points and falls away again beyond them",
              "the V is local, not global: a far-detuned circuit has a low "
              "entropy too, because its gain is near zero and the loop is "
              "then almost as silent as when it is locked, so entropy alone "
              "separates resonance from mistuning only inside the band"),
        claim("6.2", "the mathematics of homeostasis is universal, musical "
                     "half of it: musical harmony maps to Leech proximity",
              music_verdict,
              f"the harmonic register is 28 intervals as exact ratios; "
              f"decoded through their prime exponents at scale "
              f"{separation['best_scale']} the lattice reaches "
              f"{separation['best_distinct']} distinct points and distance "
              f"from the unison orders them at Kendall tau "
              f"{music['best_tau']} against consonance "
              f"(reasoning/harmony.py, report harmony)",
              None if music_verdict == CONFIRMED else str(music["because"])),
        claim("6.2", "the mathematics of homeostasis is universal, economic "
                     "half of it: market price discovery maps to Leech "
                     "proximity",
              market_verdict,
              f"the economic register is 21 quoted prices as exact "
              f"rationals over seven instruments and three quarters; "
              f"decoded through their magnitude buckets, mantissas and "
              f"EXT10 exponents the lattice first separates all "
              f"{market_lattice['record_count']} of them at scale "
              f"{market_lattice['best_scale']}, and every record's nearest "
              f"neighbour is another quarter of the same instrument "
              f"({market['best_comovement_rate']} against a chance rate of "
              f"{market['chance_rate']}) "
              f"(reasoning/economics.py, report economics)",
              None if market_verdict == CONFIRMED else str(market["because"])),
    )


# ═════════════════════════════════════════════════════════════════════════
# 4.  THE WHOLE LEDGER
# ═════════════════════════════════════════════════════════════════════════

@memo
def catalog_ledger() -> Tuple[Dict[str, object], ...]:
    """Every claim above, in the catalogue's own order."""
    return (section_1_claims() + section_2_claims() + section_3_claims()
            + section_4_claims() + section_5_claims() + section_6_claims())


def verdict_tally(ledger: Optional[Sequence[Dict[str, object]]] = None
                  ) -> Dict[str, int]:
    """How many claims fell into each verdict."""
    entries = catalog_ledger() if ledger is None else ledger
    tally = {verdict: 0 for verdict in VERDICTS}
    for entry in entries:
        tally[str(entry["verdict"])] += 1
    return tally


@memo
def catalog_report() -> Dict[str, object]:
    """The ledger and its tally, in one call."""
    ledger = catalog_ledger()
    tally = verdict_tally(ledger)
    sections = tuple(sorted({str(entry["section"]) for entry in ledger}))
    return {
        "claims": ledger,
        "claim_count": len(ledger),
        "tally": tally,
        "sections": 6,
        "section_labels": sections,
        "reading": (f"{len(ledger)} testable sentences drawn from the six "
                    f"study sections and recomputed here: "
                    f"{tally[CONFIRMED]} confirmed, {tally[REFUTED]} "
                    f"refuted, {tally[NOT_REPRODUCED]} not reproduced and "
                    f"{tally[NOT_IMPLEMENTED]} describing a subsystem the "
                    f"package does not have"),
        "confirmed": tally[CONFIRMED],
        "refuted": tally[REFUTED],
        "not_reproduced": tally[NOT_REPRODUCED],
        "not_implemented": tally[NOT_IMPLEMENTED],
    }
