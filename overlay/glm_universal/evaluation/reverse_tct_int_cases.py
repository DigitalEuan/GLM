"""``glm_universal.evaluation.reverse_tct_int_cases`` -- round three's corpus.

The held-out corpus of ``studies/REVERSE_TCT_STUDY.md`` §10 (round three,
the integer sort), written and committed before any round-three code.  Every
expected answer below was worked by hand: every variable ranges over the
integers, floor quotient and remainder follow Python's sign convention, and a
bound is the tightest *integer* bound.

* :data:`ENTAIL_CASES` -- ``entails over the integers:`` questions, with the
  declared verdict or refusal.
* :data:`BOUNDS_CASES` -- ``bounds over the integers of x:`` questions, with
  the declared answer sentence or refusal.
* :data:`BOX`, :data:`BATTERY_ATOMS_X`, :data:`BATTERY_ATOMS_XY` -- the X4
  battery: every ordered pair of distinct atoms, inside a declared box, so a
  brute-force enumeration of the box is the exact truth to compare with.
* :data:`NEW_REFUSAL_NAMES` -- the refusal round three adds.
* :data:`RESIDUE_LIMIT` -- the largest divisor whose residues are split.
"""

from __future__ import annotations

from typing import Tuple

__all__ = ["ENTAIL_CASES", "BOUNDS_CASES", "BOX", "BATTERY_ATOMS_X",
           "BATTERY_ATOMS_XY", "NEW_REFUSAL_NAMES", "RESIDUE_LIMIT"]

#: Refusal names round three adds to those of rounds one and two.
NEW_REFUSAL_NAMES: Tuple[str, ...] = ("INTEGER_UNDECIDED",)

#: A floor quotient or remainder by a constant of absolute value above this
#: is refused (``NOT_IN_FRAGMENT``) rather than split into residue cases.
RESIDUE_LIMIT = 64


# (id, premises, conclusion, expected verdict or refusal)
ENTAIL_CASES: Tuple[Tuple[str, Tuple[str, ...], str, str], ...] = (
    # -- residues ----------------------------------------------------------
    ("i01", ("x % 2 == 1",), "x != 4", "ENTAILS"),
    ("i02", ("x % 2 == 0",), "(x + 1) % 2 == 1", "ENTAILS"),
    ("i03", ("x % 4 == 1",), "x % 2 == 1", "ENTAILS"),
    ("i04", ("x % 2 == 1",), "x % 4 == 1", "INDEPENDENT"),
    ("i05", ("x % 2 == 0", "y % 2 == 0"), "(x + y) % 2 == 0", "ENTAILS"),
    ("i06", ("x % 2 == 1", "y % 2 == 1"), "(x + y) % 2 == 1", "CONTRADICTS"),
    ("i07", ("x % 3 == 0", "x % 2 == 0"), "x % 6 == 0", "ENTAILS"),
    ("i08", ("x % 5 == 3",), "(2 * x) % 5 == 1", "ENTAILS"),
    ("i09", ("x % -3 == 0 or x % -3 == -1",), "x % 3 != 1", "ENTAILS"),
    ("i10", ("x % 7 == 3", "x > 0", "x < 20"),
     "x == 3 or x == 10 or x == 17", "ENTAILS"),
    ("i11", ("x % 2 == 1",), "x / 2 != 1", "ENTAILS"),
    # -- floor quotients ---------------------------------------------------
    ("i12", ("x // 3 == 2",), "x >= 6 and x <= 8", "ENTAILS"),
    ("i13", ("x // 3 == 2",), "x == 7", "INDEPENDENT"),
    ("i14", ("x // 3 == 2",), "x == 9", "CONTRADICTS"),
    ("i15", ("-7 <= x", "x <= -5"), "x // 2 == -3 or x // 2 == -4",
     "ENTAILS"),
    # -- integrality alone -------------------------------------------------
    ("i16", ("x > 2",), "x >= 3", "ENTAILS"),
    ("i17", ("2 * x < 7",), "x <= 3", "ENTAILS"),
    ("i18", ("x > 0", "y > 0", "x + y <= 2"), "x == 1 and y == 1", "ENTAILS"),
    ("i19", ("x + y == 10", "x - y > 3"), "x >= 7", "ENTAILS"),
    ("i20", ("x == 2 * y + 1",), "x != 2 * z", "ENTAILS"),
    ("i21", ("abs(x) < 2", "x != 0"), "x == 1 or x == -1", "ENTAILS"),
    ("i22", ("2 * x == 1",), "x == 0", "INCONSISTENT_PREMISES"),
    ("i23", ("x > 0", "x < 1"), "x == 5", "INCONSISTENT_PREMISES"),
    ("i24", ("6 * x + 10 * y == 7",), "x == 0", "INCONSISTENT_PREMISES"),
    # -- refusals ----------------------------------------------------------
    ("i25", ("(x * x) % 3 == 1",), "x % 3 != 0", "NONLINEAR"),
    ("i26", ("x % Fraction(1, 2) == 0",), "x >= 0", "NOT_INTEGER"),
    ("i27", ("(x / 2) % 3 == 0",), "x >= 0", "NOT_INTEGER"),
    ("i28", ("(x & 1) == 1",), "x != 2", "NOT_POLYNOMIAL"),
    ("i29", ("x % 100 == 1",), "x != 0", "NOT_IN_FRAGMENT"),
)


# (id, variable, premises, expected answer sentence or refusal)
BOUNDS_CASES: Tuple[Tuple[str, str, Tuple[str, ...], str], ...] = (
    ("j01", "x", ("x // 3 == 1",),
     "x is at least three, and x is at most five"),
    ("j02", "x", ("2 * x > 3", "2 * x < 11"),
     "x is at least two, and x is at most five"),
    ("j03", "x", ("x % 4 == 3", "x > 0", "x < 20"),
     "x is at least three, and x is at most nineteen"),
    ("j04", "y", ("x + y == 10", "x - y > 3"), "y is at most three"),
    ("j05", "x", ("x > 0", "x < 1"), "INCONSISTENT_PREMISES"),
    ("j06", "x", ("x % 2 == 0",), "nothing bounds x"),
    ("j07", "x", ("3 * x >= 1", "3 * x <= 2"), "INCONSISTENT_PREMISES"),
    ("j08", "x", ("x % 5 == 2", "x >= 10", "x <= 30"),
     "x is at least twelve, and x is at most twenty-seven"),
    ("j09", "x", ("x // 2 == 2", "x % 2 == 0"), "x equals four"),
    ("j10", "x", ("abs(x - 3) < 2",),
     "x is at least two, and x is at most four"),
)


#: X4: the box every battery question carries, per variable (inclusive).
BOX = (-6, 6)

#: X4: atoms over ``x``; every ordered pair of distinct atoms is one question
#: (premises: the box and the first; conclusion: the second), and each atom
#: alone is one ``bounds`` question.
BATTERY_ATOMS_X: Tuple[str, ...] = (
    "x % 2 == 0", "x % 2 == 1", "x % 3 == 1", "x // 2 == 1", "x // 3 == -1",
    "2 * x > 3", "3 * x < 4", "x % -3 == -1", "(x + 1) % 4 == 0",
    "abs(x) >= 2",
)

#: X4: atoms over ``x`` and ``y``, paired the same way with a box on both.
BATTERY_ATOMS_XY: Tuple[str, ...] = (
    "x + y == 3", "x - y > 1", "(x + y) % 2 == 0", "x // 2 == y",
)
