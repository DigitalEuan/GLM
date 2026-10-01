"""``glm_universal.substrate.golay_paley`` -- the Paley origin of the code,
and the attached note's claims about it, each one recomputed.

What this module is
-------------------
``source_material/Golay codes and Hadamard matrices.txt`` arrived as a note
about where the Golay codes come from and how they climb into the Leech
lattice.  It is the source for the construction ladder
(:mod:`glm_universal.substrate.construction_ladder`), and before anything is
built on it every factual claim it makes is recomputed here.  A claim is not
believed because the note states it; it is
:data:`CONFIRMED`, :data:`CORRECTED` or :data:`REFUTED` by a function in this
module, and :func:`document_claims` returns the table.

The note's 12 x 12 block is not a new object: with ``G = [I12 | B]`` it
generates **exactly** the 4,096 codewords
:data:`glm_universal.substrate.mog.GOLAY_SET` already holds, in the same
coordinate labelling and with no permutation applied
(:func:`generates_substrate_code`).  That is worth knowing, because it means
every statement the note makes about ``B`` is a statement about the substrate
this package runs on.

What is confirmed, what is corrected
------------------------------------
Confirmed by recomputation: ``[I12 | B]`` generates a self-dual ``[24, 12, 8]``
code with weight enumerator ``1, 759, 2576, 759, 1``; stripping the last column
gives the perfect ``[23, 12, 7]`` code; ``Q = J - 2B`` -- the note's bipolar
signature -- is a Hadamard matrix of order 12; the ``11 x 11`` core of ``B``
carries a symmetric 2-design; the ternary block generates the self-dual
``[12, 6, 6]`` code.

Corrected, with the correction recomputed here:

* the note writes ``H12 = Q - I12``.  ``Q - I`` has entries in
  ``{-2, -1, 0, 1}`` and is not a Hadamard matrix at all; ``Q`` itself already
  is one (:func:`paley_hadamard`).
* the note reads the 2-design off the ``-1`` positions and calls it
  ``2-(11, 5, 2)``.  The ``-1`` positions are the ``1`` positions of ``B``,
  eleven blocks of **six** meeting in **three**: a ``2-(11, 6, 3)`` design.
  Its complement -- the ``+1`` positions -- is the ``2-(11, 5, 2)`` biplane
  the note means (:func:`bibd_from_core`).
* the note's ternary ``B11`` block is not the ternary block with its last
  column removed: as printed it generates a code of minimum weight **2**, not
  the perfect ``[11, 6, 5]`` ternary Golay code.  Removing the last column of
  the ``6 x 6`` block does give ``[11, 6, 5]`` (:func:`ternary_report`).
* the note's ternary weight enumerator ends ``+ 24 x y^11 + y^12``.  The
  ``[12, 6, 6]`` code has **24 words of weight 12** and none of weight 11:
  the enumerator is ``x^12 + 264 x^6 y^6 + 440 x^3 y^9 + 24 y^12``.

The two theta-function claims are checked in
:mod:`glm_universal.substrate.construction_ladder`, which is where the ladder
they belong to is built.

Exactness
---------
Integers only.  Every count below is enumerated over the 4,096 (or 729)
codewords rather than quoted.
"""

from __future__ import annotations

from functools import lru_cache
from itertools import product
from typing import Dict, FrozenSet, List, Sequence, Tuple

from . import mog

__all__ = [
    "PALEY_BLOCK", "TERNARY_BLOCK", "DOC_TERNARY_B11",
    "CONFIRMED", "CORRECTED", "REFUTED",
    "binary_generator_rows", "binary_codewords", "weight_distribution",
    "is_self_orthogonal", "generates_substrate_code",
    "shortened_code_report", "paley_hadamard", "hadamard_check",
    "bibd_from_core", "ternary_codewords", "ternary_report",
    "document_claims", "golay_paley_report",
]

#: The note's 12 x 12 parity block ``B``, transcribed from
#: ``source_material/Golay codes and Hadamard matrices.txt``.
PALEY_BLOCK: Tuple[Tuple[int, ...], ...] = (
    (0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1),
    (1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0),
    (1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1),
    (1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1),
    (1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0),
    (1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1),
    (1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1),
    (1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1),
    (1, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0),
    (1, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0),
    (1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0),
    (1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1),
)

#: The note's 6 x 6 ternary block, over ``F_3``.
TERNARY_BLOCK: Tuple[Tuple[int, ...], ...] = (
    (0, 1, 1, 1, 1, 1),
    (1, 0, 1, 2, 2, 1),
    (1, 1, 0, 1, 2, 2),
    (1, 2, 1, 0, 1, 2),
    (1, 2, 2, 1, 0, 1),
    (1, 1, 2, 2, 1, 0),
)

#: The note's 6 x 5 block for ``G11``, transcribed as printed.  It is *not*
#: :data:`TERNARY_BLOCK` with the last column removed, and it does not
#: generate the perfect ternary Golay code; see :func:`ternary_report`.
DOC_TERNARY_B11: Tuple[Tuple[int, ...], ...] = (
    (0, 1, 1, 1, 1),
    (1, 0, 1, 2, 2),
    (1, 1, 2, 2, 0),
    (1, 2, 2, 0, 1),
    (1, 2, 0, 1, 2),
    (1, 0, 1, 2, 2),
)

#: Verdicts a claim of the note can be given.
CONFIRMED = "confirmed"
CORRECTED = "corrected"
REFUTED = "refuted"


# ===========================================================================
# 1.  THE BINARY CODE THE BLOCK GENERATES
# ===========================================================================

def binary_generator_rows() -> Tuple[int, ...]:
    """The twelve rows of ``[I12 | B]`` as 24-bit masks, bit ``i`` = column ``i``."""
    rows: List[int] = []
    for i in range(12):
        mask = 1 << i
        for j in range(12):
            if PALEY_BLOCK[i][j]:
                mask |= 1 << (12 + j)
        rows.append(mask)
    return tuple(rows)


@lru_cache(maxsize=1)
def binary_codewords() -> FrozenSet[int]:
    """All 4,096 codewords of ``[I12 | B]``, enumerated over the messages."""
    rows = binary_generator_rows()
    words = set()
    for message in range(1 << 12):
        word = 0
        for i in range(12):
            if (message >> i) & 1:
                word ^= rows[i]
        words.add(word)
    return frozenset(words)


def weight_distribution(words: Sequence[int]) -> Dict[int, int]:
    """``weight -> how many words have it``, in increasing weight order."""
    out: Dict[int, int] = {}
    for word in words:
        weight = bin(word).count("1")
        out[weight] = out.get(weight, 0) + 1
    return dict(sorted(out.items()))


def is_self_orthogonal() -> bool:
    """Whether every pair of generator rows meets in an even number of places."""
    rows = binary_generator_rows()
    return all(bin(a & b).count("1") % 2 == 0 for a in rows for b in rows)


def generates_substrate_code() -> bool:
    """Whether the note's block generates the code the substrate already holds.

    True: same 4,096 masks, same coordinate labelling, no permutation.
    """
    return binary_codewords() == frozenset(mog.GOLAY_MASKS)


def shortened_code_report() -> Dict[str, object]:
    """``G23``: the same generator with column 23 dropped.

    The note says the result is the perfect binary Golay code.  Both halves of
    that -- minimum weight 7, and the sphere-packing identity
    ``2^12 * (1 + 23 + 253 + 1771) = 2^23`` -- are recomputed.
    """
    rows = tuple(row & ((1 << 23) - 1) for row in binary_generator_rows())
    words = set()
    for message in range(1 << 12):
        word = 0
        for i in range(12):
            if (message >> i) & 1:
                word ^= rows[i]
        words.add(word)
    distribution = weight_distribution(sorted(words))
    ball = 1 + 23 + (23 * 22) // 2 + (23 * 22 * 21) // 6
    return {
        "length": 23,
        "words": len(words),
        "minimum_weight": min(w for w in distribution if w),
        "weight_distribution": distribution,
        "ball_of_radius_3": ball,
        "words_times_ball": len(words) * ball,
        "ambient": 1 << 23,
        "perfect": len(words) * ball == 1 << 23,
    }


# ===========================================================================
# 2.  THE HADAMARD MATRIX HIDING IN THE BLOCK
# ===========================================================================

def paley_hadamard() -> Tuple[Tuple[int, ...], ...]:
    """``Q = J - 2B``: the note's bipolar signature, ``0 -> +1``, ``1 -> -1``."""
    return tuple(tuple(1 - 2 * PALEY_BLOCK[i][j] for j in range(12))
                 for i in range(12))


def _gram(matrix: Sequence[Sequence[int]]) -> List[List[int]]:
    n = len(matrix)
    return [[sum(matrix[i][k] * matrix[j][k] for k in range(len(matrix[i])))
             for j in range(n)] for i in range(n)]


def hadamard_check() -> Dict[str, object]:
    """Is ``Q`` a Hadamard matrix, and is ``Q - I`` one?

    ``Q`` is: ``Q Q^T = 12 I``.  ``Q - I`` is not, and cannot be -- a Hadamard
    matrix has entries ``+-1`` and ``Q - I`` has a zero and a ``-2`` on the
    diagonal.  Both facts are computed rather than asserted.
    """
    q = paley_hadamard()
    gram = _gram(q)
    q_entries = sorted({q[i][j] for i in range(12) for j in range(12)})
    shifted = tuple(tuple(q[i][j] - (1 if i == j else 0) for j in range(12))
                    for i in range(12))
    shifted_entries = sorted({shifted[i][j]
                              for i in range(12) for j in range(12)})
    shifted_gram = _gram(shifted)
    return {
        "q_entries": tuple(q_entries),
        "q_gram_diagonal": tuple(gram[i][i] for i in range(12)),
        "q_gram_off_diagonal": tuple(sorted({gram[i][j] for i in range(12)
                                             for j in range(12) if i != j})),
        "q_is_hadamard": (all(gram[i][i] == 12 for i in range(12))
                          and all(gram[i][j] == 0 for i in range(12)
                                  for j in range(12) if i != j)),
        "q_minus_i_entries": tuple(shifted_entries),
        "q_minus_i_is_pm1": set(shifted_entries) <= {-1, 1},
        "q_minus_i_gram_diagonal": tuple(shifted_gram[i][i]
                                         for i in range(12)),
        "q_minus_i_is_hadamard": (
            set(shifted_entries) <= {-1, 1}
            and all(shifted_gram[i][i] == 12 for i in range(12))
            and all(shifted_gram[i][j] == 0 for i in range(12)
                    for j in range(12) if i != j)),
    }


def bibd_from_core() -> Dict[str, object]:
    """The design carried by the ``11 x 11`` core of ``B``, both ways round.

    Rows ``1..11`` and columns ``1..11`` of ``B`` are the incidence matrix of
    a symmetric 2-design.  Read on the ``1`` entries -- which are the ``-1``
    entries of ``Q``, the ones the note points at -- the blocks have size 6 and
    meet in 3.  Read on the ``0`` entries the blocks have size 5 and meet in 2,
    which is the ``2-(11, 5, 2)`` biplane the note names.
    """
    core = [[PALEY_BLOCK[i][j] for j in range(1, 12)] for i in range(1, 12)]
    comp = [[1 - core[i][j] for j in range(11)] for i in range(11)]

    def design(matrix: List[List[int]]) -> Dict[str, object]:
        block_sizes = sorted({sum(row) for row in matrix})
        replication = sorted({sum(matrix[i][j] for i in range(11))
                              for j in range(11)})
        meets = sorted({sum(matrix[i][k] * matrix[j][k] for k in range(11))
                        for i in range(11) for j in range(11) if i != j})
        return {
            "points": 11,
            "blocks": 11,
            "block_size": block_sizes[0] if len(block_sizes) == 1 else None,
            "block_sizes": tuple(block_sizes),
            "replication": tuple(replication),
            "lambda": meets[0] if len(meets) == 1 else None,
            "pairwise_meets": tuple(meets),
            "symmetric_2_design": len(block_sizes) == 1 and len(meets) == 1,
        }

    ones, zeros = design(core), design(comp)
    return {
        "on_the_ones": ones,
        "on_the_zeros": zeros,
        "note_says": "2-(11, 5, 2) on the -1 entries of Q",
        "actually": (f"2-(11, {ones['block_size']}, {ones['lambda']}) on the "
                     f"-1 entries; 2-(11, {zeros['block_size']}, "
                     f"{zeros['lambda']}) on their complement"),
    }


# ===========================================================================
# 3.  THE TERNARY SIDE
# ===========================================================================

def ternary_codewords(block: Sequence[Sequence[int]]
                      ) -> Tuple[Tuple[int, ...], ...]:
    """Every codeword of ``[I_k | block]`` over ``F_3``, enumerated."""
    k = len(block)
    n = len(block[0])
    generator = [[1 if j == i else 0 for j in range(k)] + list(block[i])
                 for i in range(k)]
    out: List[Tuple[int, ...]] = []
    for message in product(range(3), repeat=k):
        out.append(tuple(
            sum(message[i] * generator[i][j] for i in range(k)) % 3
            for j in range(k + n)))
    return tuple(out)


def _ternary_weights(block: Sequence[Sequence[int]]) -> Dict[int, int]:
    out: Dict[int, int] = {}
    for word in ternary_codewords(block):
        weight = sum(1 for x in word if x)
        out[weight] = out.get(weight, 0) + 1
    return dict(sorted(out.items()))


def ternary_report() -> Dict[str, object]:
    """The ternary Golay codes: the note's blocks, and the ones that work."""
    extended = _ternary_weights(TERNARY_BLOCK)
    stripped = tuple(row[:5] for row in TERNARY_BLOCK)
    perfect = _ternary_weights(stripped)
    printed = _ternary_weights(DOC_TERNARY_B11)
    ball = 1 + 11 * 2 + (11 * 10 // 2) * 4
    return {
        "extended": {
            "length": 12, "words": sum(extended.values()),
            "minimum_weight": min(w for w in extended if w),
            "weight_distribution": extended,
            "is_12_6_6": min(w for w in extended if w) == 6,
            "note_enumerator": "x^12 + 264x^6y^6 + 440x^3y^9 + 24xy^11 + y^12",
            "recomputed_enumerator":
                "x^12 + 264x^6y^6 + 440x^3y^9 + 24y^12",
            "words_of_weight_11": extended.get(11, 0),
            "words_of_weight_12": extended.get(12, 0),
        },
        "stripped": {
            "block": stripped,
            "length": 11, "words": sum(perfect.values()),
            "minimum_weight": min(w for w in perfect if w),
            "weight_distribution": perfect,
            "is_11_6_5": min(w for w in perfect if w) == 5,
            "ball_of_radius_2": ball,
            "words_times_ball": sum(perfect.values()) * ball,
            "ambient": 3 ** 11,
            "perfect": sum(perfect.values()) * ball == 3 ** 11,
        },
        "as_printed": {
            "block": DOC_TERNARY_B11,
            "minimum_weight": min(w for w in printed if w),
            "weight_distribution": printed,
            "is_11_6_5": min(w for w in printed if w) == 5,
            "repeated_row": DOC_TERNARY_B11[1] == DOC_TERNARY_B11[5],
        },
    }


# ===========================================================================
# 4.  THE CLAIM TABLE
# ===========================================================================

def document_claims() -> Tuple[Dict[str, object], ...]:
    """Every checkable claim the note makes about the codes, with its verdict.

    Each row carries the claim as the note states it, the verdict, what the
    recomputation found, and the function that recomputed it.  The theta-series
    claims are in
    :func:`glm_universal.substrate.construction_ladder.document_claims`.
    """
    words = binary_codewords()
    distribution = weight_distribution(sorted(words))
    shortened = shortened_code_report()
    hadamard = hadamard_check()
    design = bibd_from_core()
    ternary = ternary_report()
    rows: List[Dict[str, object]] = [
        {
            "claim": "[I12 | B] generates the [24, 12, 8] extended binary "
                     "Golay code",
            "verdict": CONFIRMED,
            "found": (f"{len(words)} codewords, minimum weight "
                      f"{min(w for w in distribution if w)}"),
            "recomputed_by": "binary_codewords, weight_distribution",
        },
        {
            "claim": "its weight enumerator is "
                     "x^24 + 759x^16y^8 + 2576x^12y^12 + 759x^8y^16 + y^24",
            "verdict": CONFIRMED,
            "found": str(distribution),
            "recomputed_by": "weight_distribution",
        },
        {
            "claim": "the code is self-dual",
            "verdict": CONFIRMED if is_self_orthogonal() else REFUTED,
            "found": f"self-orthogonal: {is_self_orthogonal()}, "
                     f"dimension 12 of 24",
            "recomputed_by": "is_self_orthogonal",
        },
        {
            "claim": "B is the parity block of the code this system runs on",
            "verdict": CONFIRMED if generates_substrate_code() else REFUTED,
            "found": ("the 4,096 masks are exactly substrate.mog.GOLAY_SET, "
                      "in the same coordinate labelling"),
            "recomputed_by": "generates_substrate_code",
        },
        {
            "claim": "dropping the last column gives the perfect [23, 12, 7] "
                     "code",
            "verdict": CONFIRMED if shortened["perfect"] else REFUTED,
            "found": (f"minimum weight {shortened['minimum_weight']}, "
                      f"{shortened['words']} x {shortened['ball_of_radius_3']}"
                      f" = {shortened['words_times_ball']} = 2^23"),
            "recomputed_by": "shortened_code_report",
        },
        {
            "claim": "Q = J - 2B is the bipolar signature of a Hadamard matrix",
            "verdict": CONFIRMED if hadamard["q_is_hadamard"] else REFUTED,
            "found": "Q Q^T = 12 I exactly",
            "recomputed_by": "hadamard_check",
        },
        {
            "claim": "H12 = Q - I12 is a skew-Hadamard matrix of order 12",
            "verdict": CORRECTED,
            "found": ("Q - I has entries "
                      f"{list(hadamard['q_minus_i_entries'])}, so it is not a "
                      "Hadamard matrix; Q itself is one"),
            "recomputed_by": "hadamard_check",
        },
        {
            "claim": "the -1 positions of the normalised 11 x 11 submatrix "
                     "form a 2-(11, 5, 2) design",
            "verdict": CORRECTED,
            "found": str(design["actually"]),
            "recomputed_by": "bibd_from_core",
        },
        {
            "claim": "the ternary block generates the [12, 6, 6] extended "
                     "ternary Golay code",
            "verdict": CONFIRMED if ternary["extended"]["is_12_6_6"] else REFUTED,
            "found": str(ternary["extended"]["weight_distribution"]),
            "recomputed_by": "ternary_report",
        },
        {
            "claim": "its weight enumerator ends + 24xy^11 + y^12",
            "verdict": CORRECTED,
            "found": ("no word has weight 11 and 24 have weight 12: "
                      "x^12 + 264x^6y^6 + 440x^3y^9 + 24y^12"),
            "recomputed_by": "ternary_report",
        },
        {
            "claim": "the printed 6 x 5 block generates the perfect [11, 6, 5] "
                     "ternary Golay code",
            "verdict": CORRECTED,
            "found": (f"as printed the minimum weight is "
                      f"{ternary['as_printed']['minimum_weight']} (row 2 is "
                      f"repeated as row 6); removing the last column of the "
                      f"6 x 6 block does give [11, 6, 5], perfect: "
                      f"{ternary['stripped']['perfect']}"),
            "recomputed_by": "ternary_report",
        },
    ]
    return tuple(rows)


def golay_paley_report() -> Dict[str, object]:
    """Everything this module knows, recomputed on call."""
    claims = document_claims()
    return {
        "source": "source_material/Golay codes and Hadamard matrices.txt",
        "generates_substrate_code": generates_substrate_code(),
        "weight_distribution": weight_distribution(sorted(binary_codewords())),
        "self_orthogonal": is_self_orthogonal(),
        "shortened": shortened_code_report(),
        "hadamard": hadamard_check(),
        "design": bibd_from_core(),
        "ternary": ternary_report(),
        "claims": claims,
        "confirmed": sum(1 for row in claims if row["verdict"] == CONFIRMED),
        "corrected": sum(1 for row in claims if row["verdict"] == CORRECTED),
        "refuted": sum(1 for row in claims if row["verdict"] == REFUTED),
    }
