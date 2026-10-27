#!/usr/bin/env python3
"""Curated seed for the GLM Monster Wheel.

The Monster Wheel is sourced from the AxiomMath/CFSG repository
(https://github.com/AxiomMath/CFSG), a Lean 4 formalization of the
Classification of Finite Simple Groups (Apache-2.0 license).

This file lists the **26 sporadic simple groups** discovered in the CFSG
plus the **Mathieu groups** (which are also sporadic but listed separately
in the Lean sources under `CFSG/Sporadic/Mathieu`):

    M11, M12, M22, M23, M24            (Mathieu, 1861)
    J1, J2, J3, J4                     (Janko / Hall-Janko)
    Co1, Co2, Co3                      (Conway)
    HS, McL, He, Ru, Suz, ON           (Higman-Sims / McLaughlin / Held /
                                        Rudvalis / Suzuki / O'Nan)
    Fi22, Fi23, Fi24'                  (Fischer)
    HN, Th, Ly                         (Harada-Norton / Thompson / Lyons)
    B                                  (the Baby Monster)
    M                                  (the Monster — largest sporadic)

Each entry is a tuple:

    (group_id, full_name, order, factorization_string,
     discoverer, year, notes)

The `order` is the canonical integer group order (matches the Lean
`theorem card_<X> : card <X> = <int>` declaration). The
`factorization_string` is the standard prime-power decomposition
(e.g. "2^46 · 3^20 · 5^9 · ... · 71" for the Monster).

References:
  * AxiomMath/CFSG: https://github.com/AxiomMath/CFSG  (Apache-2.0)
  * ATLAS of Finite Group Representations
  * Conway, Curtis, Norton, Parker, Wilson, "Atlas of Finite Groups"
    (Oxford, 1985)
  * OEIS A001034 analogue (local id `CFSG-SPORADIC-ORDERS`)
"""

from __future__ import annotations


# The 26 sporadic simple groups, with canonical group order and the
# discoverer/year. The list is sorted by group ID for ease of reference;
# the Monster Wheel sorts them by order when registering the
# `CFSG-SPORADIC-ORDERS` composite sequence.
CFSG_GROUPS = [
    # ── Mathieu groups (1861, Émile Léonard Mathieu) ──────────────────────
    ("M11", "Mathieu group M11", 7_920,
     "2^4 · 3^2 · 5 · 11",
     "Mathieu", 1861,
     "sharply 4-transitive permutation group on 11 points; smallest sporadic"),

    ("M12", "Mathieu group M12", 95_040,
     "2^6 · 3^3 · 5 · 11",
     "Mathieu", 1861,
     "sharply 5-transitive permutation group on 12 points"),

    ("M22", "Mathieu group M22", 443_520,
     "2^7 · 3^2 · 5 · 7 · 11",
     "Mathieu", 1861,
     "3-transitive permutation group on 22 points; preserves a Steiner "
     "system S(3,6,22)"),

    ("M23", "Mathieu group M23", 10_200_960,
     "2^7 · 3^2 · 5 · 7 · 11 · 23",
     "Mathieu", 1861,
     "4-transitive permutation group on 23 points; preserves a Steiner "
     "system S(4,7,23)"),

    ("M24", "Mathieu group M24", 244_823_040,
     "2^10 · 3^3 · 5 · 7 · 11 · 23",
     "Mathieu", 1861,
     "5-transitive permutation group on 24 points; preserves the Steiner "
     "system S(5,8,24); automorphism group of the binary Golay code"),

    # ── Janko groups (1965-1976, Zvonimir Janko) ───────────────────────────
    ("J1", "Janko group J1", 175_560,
     "2^3 · 3 · 5 · 7 · 11 · 19",
     "Janko", 1965,
     "the first new sporadic simple group found since Mathieu; smallest "
     "sporadic after Mathieu"),

    ("J2", "Hall-Janko group J2", 604_800,
     "2^7 · 3^3 · 5^2 · 7",
     "Janko / Hall-Wales", 1965,
     "rank-3 permutation group on 100 points; originally predicted by Janko, "
     "constructed by Hall and Wales"),

    ("J3", "Janko group J3", 50_232_960,
     "2^7 · 3^5 · 5 · 17 · 19",
     "Janko", 1968,
     "subgroup of G2(3)"),

    ("J4", "Janko group J4",
     86_775_571_046_077_562_880,
     "2^21 · 3^3 · 5 · 7 · 11^3 · 23 · 29 · 31 · 37 · 43",
     "Janko", 1976,
     "the largest of the Janko groups"),

    # ── Conway groups (1968, John Horton Conway) ───────────────────────────
    ("Co1", "Conway group Co1",
     4_157_776_806_543_360_000,
     "2^21 · 3^9 · 5^4 · 7^2 · 11 · 13 · 23",
     "Conway", 1968,
     "automorphism group of the Leech lattice modulo its center; centralizer "
     "of a 2A-element in the Monster"),

    ("Co2", "Conway group Co2",
     42_305_421_312_000,
     "2^18 · 3^6 · 5^3 · 7 · 11 · 23",
     "Conway", 1968,
     "stabilizer of a type-2 vector in the Leech lattice"),

    ("Co3", "Conway group Co3",
     495_766_656_000,
     "2^10 · 3^7 · 5^3 · 7 · 11 · 23",
     "Conway", 1968,
     "stabilizer of a type-3 vector in the Leech lattice"),

    # ── Higman-Sims, McLaughlin, Held, Rudvalis, Suzuki, O'Nan ─────────────
    ("HS", "Higman-Sims group HS",
     44_352_000,
     "2^9 · 3^2 · 5^3 · 7 · 11",
     "Higman-Sims", 1967,
     "rank-3 permutation group on 100 points"),

    ("McL", "McLaughlin group McL",
     898_128_000,
     "2^7 · 3^6 · 5^3 · 7 · 11",
     "McLaughlin", 1969,
     "subgroup of Co2; rank-3 permutation group on 275 points"),

    ("He", "Held group He",
     4_030_387_200,
     "2^10 · 3^3 · 5^2 · 7^3 · 17",
     "Held", 1969,
     "centralizer of a 5A-element structure in the Monster"),

    ("Ru", "Rudvalis group Ru",
     145_926_144_000,
     "2^14 · 3^3 · 5^3 · 7 · 13 · 29",
     "Rudvalis", 1972,
     "rank-3 permutation group; predicted by Rudvalis, constructed by "
     "Conway and Wales"),

    ("Suz", "Suzuki sporadic group Suz",
     448_345_497_600,
     "2^13 · 3^7 · 5^2 · 7 · 11 · 13",
     "Suzuki", 1969,
     "rank-3 permutation group on 1782 points; not to be confused with the "
     "Suzuki groups Sz(q) of Lie type"),

    ("ON", "O'Nan group ON",
     460_815_505_920,
     "2^9 · 3^4 · 5 · 7^3 · 11 · 19 · 31",
     "O'Nan", 1976,
     "discovered in O'Nan's study of sporadic groups"),

    # ── Fischer groups (1971, Bernd Fischer) ──────────────────────────────
    ("Fi22", "Fischer group Fi22",
     64_561_751_654_400,
     "2^17 · 3^9 · 5^2 · 7 · 11 · 13",
     "Fischer", 1971,
     "3-transposition group; Fi_22 in Fischer notation"),

    ("Fi23", "Fischer group Fi23",
     4_089_470_473_293_004_800,
     "2^18 · 3^13 · 5^2 · 7 · 11 · 13 · 17 · 23",
     "Fischer", 1971,
     "3-transposition group; Fi_23 in Fischer notation"),

    ("Fi24'", "Fischer group Fi24' (the commutator subgroup of Fi24)",
     1_255_205_709_190_661_721_292_800,
     "2^21 · 3^16 · 5^2 · 7^3 · 11 · 13 · 17 · 23 · 29",
     "Fischer", 1971,
     "the commutator subgroup of Fi_24; the largest of the Fischer 3-"
     "transposition groups"),

    # ── Harada-Norton, Thompson, Lyons ────────────────────────────────────
    ("HN", "Harada-Norton group HN",
     273_030_912_000_000,
     "2^14 · 3^6 · 5^6 · 7 · 11 · 19",
     "Harada-Norton", 1975,
     "centralizer of a 5A-element in the Monster"),

    ("Th", "Thompson group Th",
     90_745_943_887_872_000,
     "2^15 · 3^10 · 5^3 · 7^2 · 13 · 19 · 31",
     "Thompson", 1975,
     "centralizer of a 3A-element in the Monster"),

    ("Ly", "Lyons group Ly",
     51_765_179_004_000_000,
     "2^8 · 3^7 · 5^6 · 7 · 11 · 31 · 37 · 67",
     "Lyons-Sims", 1972,
     "discovered by Lyons and Sims; the prime 67 appears in its factorization"),

    # ── The Baby Monster and the Monster ───────────────────────────────────
    ("B", "Baby Monster group B",
     4_154_781_481_226_426_191_177_580_544_000_000,
     "2^41 · 3^13 · 5^6 · 7^2 · 11 · 13 · 17 · 19 · 23 · 31 · 47",
     "Fischer", 1973,
     "the second-largest sporadic simple group; centralizer of an involution "
     "in the Monster; predicted by Fischer, constructed by Leon and Sims"),

    ("M", "Monster group M (Fischer-Griess)",
     808_017_424_794_512_875_886_459_904_961_710_757_005_754_368_000_000_000,
     "2^46 · 3^20 · 5^9 · 7^6 · 11^2 · 13^3 · 17 · 19 · 23 · 29 · 31 · 41 · 47 · 59 · 71",
     "Fischer-Griess", 1973,
     "the largest sporadic simple group; ~8.08×10^53 elements; constructed "
     "by Griess in 1981 as the automorphism group of a 196884-dimensional "
     "non-associative algebra; contains 19 of the other 25 sporadics as "
     "subquotients (the 'happy family')"),
]


def factorize(order: int) -> list[tuple[int, int]]:
    """Return the prime factorization of `order` as a list of (prime, exponent) pairs.

    Uses sympy's `factorint` (Pollard rho + trial division) for fast factorization
    of large integers like the Monster group's ~8.08×10^53 order.
    """
    from sympy import factorint
    f = factorint(order)
    return sorted(f.items())


def order_from_factors(factors: list[tuple[int, int]]) -> int:
    """Inverse of `factorize`."""
    n = 1
    for p, e in factors:
        n *= p ** e
    return n


def exponent_vector(order: int, max_prime: int = 73) -> list[int]:
    """Return the exponent vector of `order` for primes 2, 3, 5, 7, ..., up to `max_prime`.

    E.g. for M11 = 2^4 · 3^2 · 5 · 11 = 7920:
        exponent_vector(7920) = [4, 2, 1, 0, 1, 0, 0, 0, 0, 0, 0, ...]  (for primes 2,3,5,7,11,13,...)
    """
    primes_upto_73 = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41,
                      43, 47, 53, 59, 61, 67, 71]
    primes = [p for p in primes_upto_73 if p <= max_prime]
    factors = dict(factorize(order))
    return [factors.get(p, 0) for p in primes]


# The sorted sequence of all 26 sporadic group orders (the OEIS-A001034-like
# composite sequence the wheel registers as a single multi-term entry).
SPORADIC_ORDERS_SORTED = sorted(g[2] for g in CFSG_GROUPS)


# A few OEIS sequences that are group-theoretic, useful to also have on the
# Monster Wheel for cross-referencing (these are NOT in the Integer Wheel's
# curated 183 and are added explicitly here).
GROUP_THEORY_OEIS = [
    # (oeis_id, name, terms, keywords, formula, offset)
    ("A000001", "Number of groups of order n",
     [1, 1, 1, 2, 1, 2, 1, 5, 2, 2, 1, 5, 1, 2, 1, 14, 1, 5, 1, 5],
     {"nonn", "hard", "core"}, "number of groups of order n", 1),
    ("A000688", "Number of abelian groups of order n (number of distinct partitions of the prime exponent multiset)",
     [1, 1, 1, 2, 1, 1, 1, 3, 2, 1, 1, 2, 1, 1, 1, 5, 1, 2, 1, 2],
     {"nonn", "easy"}, "number of abelian groups of order n", 1),
    ("A001034", "Orders of the 26 sporadic simple groups (sorted)",
     list(SPORADIC_ORDERS_SORTED),
     {"nonn", "hard", "famous"},
     "sporadic simple group orders, increasing", 1),
    ("A005180", "Number of simple groups of order n (1 if n is a non-abelian simple group order, 0 otherwise) — partial map",
     [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
     {"nonn"},
     "delta(n in A001229 orders)", 1),
    ("A060689", "Number of n-th powers of 2 that are orders of simple groups (always 0 for n>=1)",
     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
     {"nonn", "trivial"},
     "always 0 — 2^n is never a non-abelian simple group order", 0),
]
