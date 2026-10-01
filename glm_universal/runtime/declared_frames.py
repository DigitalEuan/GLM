"""``glm_universal.runtime.declared_frames`` -- the declared tables behind
round three of the stepwise planner.

Why this module exists
----------------------
Round two of the stepwise planner (``studies/STEPWISE_TWO_STUDY.md`` §6)
named the widenings it left: comparatives such as *heavier* with a declared
field, *how many more* over further count nouns, the tera- and pico-
prefixes, and folds over a whole column.  Round three
(``studies/STEPWISE_THREE_STUDY.md``, Phase 84) takes them, and every one of
them rests on a declaration rather than an inference.  This module is the
declarations, and the two readers that consult them:

* :data:`COMPARATIVES` -- each comparative word the planner reads, the
  register phrase it compares, and which way: *heavier* is the larger atomic
  weight, *older* the earlier year of discovery.  A comparative not listed
  is refused ``COMPARATIVE_UNDECLARED``: *stronger* or *harder* names no
  column the register holds, and the planner does not guess one.
* :data:`COUNT_NOUNS` -- the count nouns round three adds to round two's
  *protons*: the electrons of the neutral atom (the atomic number, by the
  definition of a neutral atom) and the valence electrons (the register's own
  column).  *Neutrons* would need a nuclide register and stay undeclared.
* :data:`DECLARED_SETS` -- the classes a fold may range over: every element,
  or the rows of one value of the element table's ``group_block`` column,
  under the plural name the question uses.  The classes are the register's
  own, so *the nonmetals* are its ``Nonmetal`` rows (halogens and noble gases
  are classes of their own there); a class the table does not name (*the
  metals*) is refused ``SET_UNDECLARED``.
* :func:`resolve_field` -- the element-table column a phrase names, through
  the planner's own synonym table and the column's own name.
* :func:`members` -- the rows of a declared set, in the register's order.

Exact throughout; nothing here reads a digest or a similarity.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

__all__ = ["COMPARATIVES", "COUNT_NOUNS", "DECLARED_SETS", "FOLD_FUNCTIONS",
           "comparative", "set_key", "resolve_field", "members",
           "names_an_element", "names_a_column", "ELEMENT_TABLE"]

#: The register table folds and comparatives read.
ELEMENT_TABLE = "element"

#: ``word -> (register phrase, direction, gloss)``.  Direction ``>`` names
#: the row with the larger value, ``<`` the row with the smaller.
COMPARATIVES: Dict[str, Tuple[str, str, str]] = {
    "heavier": ("atomic weight", ">", "the larger standard atomic weight"),
    "lighter": ("atomic weight", "<", "the smaller standard atomic weight"),
    "denser": ("density", ">", "the larger density at standard state"),
    "older": ("year discovered", "<",
              "the earlier recorded year of discovery"),
    "newer": ("year discovered", ">",
              "the later recorded year of discovery"),
}

#: ``count noun -> register phrase`` added by round three to round two's
#: :data:`glm_universal.evaluation.stepwise_two_cases.COUNT_NOUNS`.
COUNT_NOUNS: Dict[str, str] = {
    "electrons": "atomic number",          # of the neutral atom
    "valence electrons": "valence electrons",
}

_ALL = None

#: ``plural name -> group_block value`` (``None``: every row of the table).
DECLARED_SETS: Dict[str, Optional[str]] = {
    "elements": _ALL,
    "chemical elements": _ALL,
    "noble gases": "Noble gas",
    "halogens": "Halogen",
    "alkali metals": "Alkali metal",
    "alkaline earth metals": "Alkaline earth metal",
    "transition metals": "Transition metal",
    "post-transition metals": "Post-transition metal",
    "lanthanides": "Lanthanide",
    "actinides": "Actinide",
    "metalloids": "Metalloid",
    "nonmetals": "Nonmetal",
}

#: The folds: ``name -> the words column 1 writes it with``.
FOLD_FUNCTIONS: Dict[str, str] = {
    "sum": "sum", "mean": "mean", "odd": "count of odd values",
    "even": "count of even values",
}


def comparative(word: str) -> Optional[Tuple[str, str, str]]:
    """The declared reading of a comparative word, or None."""
    return COMPARATIVES.get(word)


_ELEMENT_ALIASES: List[frozenset] = []


def names_an_element(phrase: str) -> bool:
    """Whether a phrase is a row of the element table (a name or a symbol,
    as the field surface resolves it).  ``COMPARATIVE_UNDECLARED`` is a
    claim about register rows -- no column is declared to compare them -- so
    it is made only when both sides are rows; any other text is left to the
    readers that own it."""
    from .fields import surface
    from .parser import normalise
    if not _ELEMENT_ALIASES:
        table = surface().table_by_name(ELEMENT_TABLE)
        _ELEMENT_ALIASES.append(frozenset(table.aliases()))
    p = re.sub(r"^the\s+", "", phrase.strip().lower())
    return normalise(p) in _ELEMENT_ALIASES[0]


_SURFACE: List[object] = []


def names_a_column(phrase: str) -> bool:
    """Whether a phrase names a column of the element table.
    ``SET_UNDECLARED`` is a claim about the element table's classes, so it
    is made only for a fold over one of its columns."""
    from .fields import surface
    if not _SURFACE:
        _SURFACE.append(surface())
    return resolve_field(_SURFACE[0], phrase) is not None


def set_key(phrase: str) -> Tuple[Optional[str], bool]:
    """``(declared set name or None, looks like a set)`` for a phrase such as
    *the noble gases* or *all the elements*.  A phrase *looks like a set*
    when it is a plural introduced by *the* or *all*; only then is an
    undeclared one refused rather than read as something else."""
    p = re.sub(r"\s+", " ", phrase.strip().lower())
    introduced = bool(re.match(r"(?:all|the)\b", p))
    p = re.sub(r"^(?:all of the|all the|all|the)\s+", "", p)
    if p in DECLARED_SETS:
        return p, True
    return None, introduced and p.endswith("s") and " of " not in p


def resolve_field(field_surface, phrase: str) -> Optional[str]:
    """The element-table column a phrase names: the planner's synonym table
    first (its first element column), then the column's own name read as
    words.  Singular and plural are both read (*atomic numbers*)."""
    from .semantic_plan import FIELD_SYNONYMS, field_words
    table = field_surface.table_by_name(ELEMENT_TABLE)
    columns = list(next(iter(table.rows().values())).keys())
    p = re.sub(r"\s+", " ", phrase.strip().lower())
    tries = [p]
    if p.endswith("s") and not p.endswith("ss"):
        tries.append(p[:-1])
    for t in tries:
        for f in FIELD_SYNONYMS.get(t, ()):
            if f in columns:
                return f
    for t in tries:
        for f in columns:
            if t in field_words(f):
                return f
    return None


def members(field_surface, set_name: str) -> List[Tuple[str, str]]:
    """``[(row key, row name), ...]`` of a declared set, in the register's
    order."""
    want = DECLARED_SETS[set_name]
    rows = field_surface.table_by_name(ELEMENT_TABLE).rows()
    return [(k, str(v.get("name", k))) for k, v in rows.items()
            if want is None or v.get("group_block") == want]
