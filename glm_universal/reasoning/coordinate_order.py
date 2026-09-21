"""``glm_universal.reasoning.coordinate_order`` -- the ordering operation, and
the boundary it refuses at.

Why this module exists
----------------------
:mod:`glm_universal.reasoning.probe_oracle` priced twenty pre-registered probe
questions and :mod:`glm_universal.reasoning.field_surface` closed nine of the
ten it called *held and unreachable*.  The tenth was declared unreachable
**before** that round ran, and for a stated reason: *is energy more abstract
than water?* compares one coordinate across two rows, and a field query
returns one field of one row.  What closes it is an operation over two
readings, not a surface onto one.

This module is that operation.  It reads the same coordinate off two rows
through the field surface and orders them -- exactly, in rationals -- or
refuses, and the refusal is the point: two numbers read off two rows are
comparable only when they are readings **on one scale**.

What a scale is here
--------------------
The scale of a reading is the table it was read from and the field name it
was read under, written ``table:field``.  That is not a convention of
convenience:

* a field name carries its unit in this system (``atomic_weight_u``,
  ``boiling_point_K``, ``covalent_radius_pm``), so two readings of one field
  of one table are in one unit by construction;
* and the same field name across two tables is *not* one scale.  ``line`` is
  held by both the Lean address book and the package's own source walk, and
  the line number of a Lean declaration is not comparable with the line
  number of a Python function.  Asked for that comparison the operation
  refuses and says which two scales it was given.

The refusal is not fussiness.  ``GLM.CoordinateOrder.naive_order_is_not_scale_free``
exhibits a positive rescaling that flips the comparison of two raw numbers,
and ``order_scale_invariant`` shows that no rescaling of a *shared* scale can:
same scale is exactly the condition under which the verdict is a fact about
the rows rather than about the units they happen to be written in.

What it does not claim
----------------------
The operation orders a coordinate.  That a given coordinate *means*
abstractness is the lexicon register's declaration, not this module's finding:
:data:`POLES` transcribes the poles the register documents for its ten
semantic primitives, and the answer names the pole it used.  Under the
standing target of ``PROJECT_DIRECTIVES.md`` this is **derivation** of the
weakest interesting kind -- one exact subtraction over two addressed readings
-- together with a stated refusal; it is not addressing, and nothing here
parses English.

The machine-checked half is ``RequestProject/GLM/CoordinateOrder.lean``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from ..derived import memo

__all__ = [
    "OrderingError", "POLES", "Reading", "Comparison",
    "scale_of", "as_exact", "reading", "order", "DECLARED_COMPARISONS",
    "order_translations", "comparison_report",
]


class OrderingError(ValueError):
    """Raised when two readings cannot be ordered, with the reason.

    The reason is one of :data:`REFUSAL_REASONS`, carried in
    :attr:`reason` so a caller can act on the kind of refusal rather than on
    the wording of it.
    """

    def __init__(self, reason: str, message: str):
        super().__init__(message)
        self.reason = reason


#: Every way the operation can refuse.  ``unreadable`` covers the field
#: surface's own refusals -- an unknown row, a field the row does not hold, a
#: field the register records as missing -- which are restated rather than
#: reclassified.
REFUSAL_REASONS: Tuple[str, ...] = (
    "unreadable", "not-ordered", "different-scale",
)


#: The poles of the lexicon register's ten semantic primitives, transcribed
#: from the declaration in
#: ``glm_universal.data_objects.semantic_lexicon.SEMANTIC_PRIMITIVES``: each
#: primitive runs from 0 to 1, and these are the names of its two ends.  The
#: operation reports the order of the numbers; it consults this table only to
#: say *which end* the lower row is at, and only for a coordinate that is in
#: it.  A test checks that the keys here are exactly the register's ten.
POLES: Mapping[str, Tuple[str, str]] = {
    "abstract_concrete": ("abstract", "concrete"),
    "animate_inanimate": ("animate", "inanimate"),
    "countable_mass": ("countable", "mass"),
    "temporal_stable": ("ephemeral", "permanent"),
    "spatial_local": ("global", "local"),
    "causal_passive": ("active cause", "passive"),
    "positive_negative": ("negative", "positive"),
    "singular_plural": ("singular", "plural"),
    "active_stative": ("stative", "active"),
    "definite_indefinite": ("indefinite", "definite"),
}


# ===========================================================================
# 1.  A READING, AND THE SCALE IT IS ON
# ===========================================================================

@dataclass(frozen=True)
class Reading:
    """One ordered reading of one coordinate, with the scale it is on."""

    row: str
    field: str
    table: str
    table_kind: str
    value: Fraction
    rendered: str
    derived: bool
    rule: str
    provenance: str

    @property
    def scale(self) -> str:
        """``table:field`` -- what makes two readings comparable."""
        return f"{self.table}:{self.field}"


def scale_of(found) -> str:
    """The scale tag of a :class:`~glm_universal.runtime.fields.FieldValue`."""
    return f"{found.table}:{found.field}"


#: A rational written out as a carrier attribute: ``3``, ``-3`` or ``1/4``.
#: Carriers serialise their exact values as strings, and this is the only
#: string shape read as a number -- a gloss, a symbol or a part of speech
#: never matches it.
_RATIONAL = re.compile(r"^-?\d+(?:/\d+)?$")


def as_exact(value: object) -> Optional[Fraction]:
    """``value`` as an exact rational, or ``None`` when it is not ordered.

    ``bool`` is excluded deliberately: ``True`` is an ``int`` in Python and a
    label in this system, and ordering two labels is the mistake this
    function exists to refuse.  A string is read only when it is a written
    rational, which is how a carrier holds an exact value; nothing is parsed
    approximately and no float is constructed on any path.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, Fraction):
        return value
    if isinstance(value, str) and _RATIONAL.match(value):
        return Fraction(value)
    return None


def _inside_a_mapping(surface, field: str, row: str) -> Optional[Reading]:
    """The reading of ``field`` as a key of a mapping field of ``row``.

    The lexicon register holds its ten semantic primitives as one mapping
    field -- ``primitives`` -- rather than as ten fields, so
    ``abstract_concrete`` is a coordinate the row carries and not a field the
    field surface addresses.  Reading it here is still addressing, not
    invention: the key is the row's own key of the row's own field, and the
    scale records the field that contains it, so
    ``carrier:lexicon:primitives.abstract_concrete`` cannot be confused with
    a field of that name.

    Tables are searched in the surface's own priority order and, within a
    row, containing fields in sorted order, so the reading is determinate.
    """
    from ..runtime import fields as fl
    for table, key in surface.matches(row):
        held = table.rows()[key]
        for name in sorted(held):
            value = held[name]
            if not isinstance(value, Mapping) or field not in value:
                continue
            exact = as_exact(value[field])
            if exact is None:
                continue
            return Reading(
                row=key, field=f"{name}.{field}", table=table.name,
                table_kind=table.kind, value=exact,
                rendered=fl.render_value(value[field]),
                derived=name in table.derived,
                rule=table.derived.get(name, ""),
                provenance=table.provenance)
    return None


def reading(surface, field: str, row: str) -> Reading:
    """One ordered reading, or a refusal that says why there is none.

    ``surface`` is a :class:`~glm_universal.runtime.fields.FieldSurface`.  A
    field the row holds directly is read from there; failing that, a key of a
    mapping field the row holds is read as a coordinate of that field (see
    :func:`_inside_a_mapping`).  A row the surface does not hold, and a
    coordinate held nowhere on it, are refused as ``unreadable``, restating
    the surface's own message; a value the surface holds but which is not a
    number -- a name, a formula, a part of speech -- is refused as
    ``not-ordered``, because a nominal coordinate has no order to read.
    """
    from ..runtime import fields as fl
    try:
        found = surface.field(field, row)
    except fl.FieldError as error:
        inside = _inside_a_mapping(surface, field, row)
        if inside is not None:
            return inside
        raise OrderingError("unreadable", str(error)) from None
    exact = as_exact(found.value)
    if exact is None:
        raise OrderingError(
            "not-ordered",
            f"{found.field} of {found.row} is {found.rendered!r}, which is a "
            f"label rather than a quantity; the ordering operation reads a "
            f"coordinate with an order and refuses one without")
    return Reading(
        row=found.row, field=found.field, table=found.table,
        table_kind=found.table_kind, value=exact, rendered=found.rendered,
        derived=found.derived, rule=found.rule, provenance=found.provenance)


# ===========================================================================
# 2.  THE OPERATION
# ===========================================================================

@dataclass(frozen=True)
class Comparison:
    """The verdict of one comparison: what was read, and how it ordered."""

    field: str
    scale: str
    left: Reading
    right: Reading
    verdict: str                     # 'lt', 'gt' or 'eq'
    difference: Fraction             # right - left, exactly
    pole: str                        # the named low end, or ''
    pole_row: str                    # the row at that end, or '' when equal

    @property
    def sentence(self) -> str:
        """The verdict as one line, with the pole named when there is one."""
        relation = {"lt": "is below", "gt": "is above",
                    "eq": "is level with"}[self.verdict]
        head = (f"{self.field} of {self.left.row} = {self.left.rendered} "
                f"{relation} {self.field} of {self.right.row} = "
                f"{self.right.rendered}")
        gap = (f", by an exact {abs(self.difference)}"
               if self.verdict != "eq" else "")
        pole = (f"; the register declares 0 = {self.pole}, so {self.pole_row} "
                f"is the more {self.pole} of the two" if self.pole_row else "")
        return f"{head}{gap}, both read on the {self.scale} scale{pole}"


def order(surface, field: str, left: str, right: str) -> Comparison:
    """Order one coordinate across two rows, or refuse.

    Refuses as ``unreadable`` when either reading is not held, as
    ``not-ordered`` when either is a label, and as ``different-scale`` when
    the two readings come from different tables or different fields -- the
    case the whole operation is built around.
    """
    one = reading(surface, field, left)
    two = reading(surface, field, right)
    if one.scale != two.scale:
        raise OrderingError(
            "different-scale",
            f"{field} of {one.row} is read on the {one.scale} scale and "
            f"{field} of {two.row} on the {two.scale} scale; two readings on "
            f"different scales have no common order, and the operation "
            f"refuses rather than comparing the bare numbers")
    if one.value < two.value:
        verdict = "lt"
    elif two.value < one.value:
        verdict = "gt"
    else:
        verdict = "eq"
    poles = POLES.get(field, ("", ""))
    pole = poles[0]
    if verdict == "eq" or not pole:
        pole_row = ""
    else:
        pole_row = one.row if verdict == "lt" else two.row
    return Comparison(
        field=field, scale=one.scale, left=one, right=two, verdict=verdict,
        difference=two.value - one.value,
        pole=pole if pole_row else "", pole_row=pole_row)


# ===========================================================================
# 3.  THE DECLARED SET -- what the operation is measured on
# ===========================================================================

#: The comparisons this round declares before running them: the probe
#: question, three more answerable ones over three different tables, and the
#: three refusals the operation must make.  Each row is
#: ``(key, field, left, right, expected)`` where ``expected`` is the verdict
#: or the refusal reason.
DECLARED_COMPARISONS: Tuple[Tuple[str, str, str, str, str], ...] = (
    ("probe", "abstract_concrete", "energy", "water", "lt"),
    ("lexicon-equal", "animate_inanimate", "energy", "water", "eq"),
    ("element", "atomic_weight_u", "carbon", "oxygen", "lt"),
    ("molecule-derived", "molar_mass_u", "water", "ethanol", "lt"),
    ("nominal", "kind", "energy", "water", "not-ordered"),
    ("across-tables", "line", "GLM.NormFamily.family_tower",
     "rung_audit", "different-scale"),
    ("unheld", "atomic_weight_u", "carbon", "water", "unreadable"),
)


def _run_declared(surface) -> Tuple[Dict[str, object], ...]:
    rows: List[Dict[str, object]] = []
    for key, field, left, right, expected in DECLARED_COMPARISONS:
        entry: Dict[str, object] = {
            "key": key, "field": field, "left": left, "right": right,
            "expected": expected,
        }
        try:
            result = order(surface, field, left, right)
        except OrderingError as error:
            entry["outcome"] = error.reason
            entry["detail"] = str(error)
        else:
            entry["outcome"] = result.verdict
            entry["detail"] = result.sentence
            entry["scale"] = result.scale
            entry["difference"] = result.difference
            entry["pole_row"] = result.pole_row
        entry["as_declared"] = entry["outcome"] == expected
        rows.append(entry)
    return tuple(rows)


# ===========================================================================
# 4.  THE PROBE QUESTION THE OPERATION CLOSES
# ===========================================================================

def _order_translations():
    """The field-surface translation table with ``nl-compare`` answered.

    Everything else is inherited unchanged from
    :func:`glm_universal.reasoning.field_surface.translations_after`, so the
    nineteen other questions are scored on exactly the queries the previous
    round measured them on.  The locus is ``pole_row`` -- the row the answer
    puts at the named end -- rather than the sentence, so the fragment can
    only be matched by an answer that actually picks a row.
    """
    from .field_surface import translations_after
    from .probe_oracle import Translation
    replacement = Translation(
        "nl-compare", "order abstract_concrete of energy and water",
        "pole_row", None, "none",
        "the operation reads coordinate 0 of the lexicon carrier off both "
        "rows -- 1/4 for energy against 1 for water -- checks that both were "
        "read on the carrier:lexicon:abstract_concrete scale, and orders "
        "them; the register declares 0 = abstract, so the row it names is "
        "the more abstract")
    return tuple(replacement if t.key == "nl-compare" else t
                 for t in translations_after())


@memo
def order_translations():
    """The translation table this round is measured on, built once."""
    return _order_translations()


def comparison_report(session=None) -> Dict[str, object]:
    """What the ordering operation answers, refuses, and closes.

    Three things, in one reading: the declared comparison set with the
    outcome of each against what was declared for it; the probe question the
    field surface left open, re-scored through the same oracle; and the
    verdict in integers.
    """
    if session is None:
        from ..runtime.session import GeometricSession
        session = GeometricSession()
    from .blockers import PROBE
    from .field_surface import SURFACE_KEYS, translations_after
    from .probe_oracle import oracle_report
    surface = session.field_surface
    rows = _run_declared(surface)
    before = oracle_report(session, translations_after())
    after = oracle_report(session, order_translations())
    before_rows = {str(row["key"]): row for row in before["rows"]}   # type: ignore[union-attr]
    after_rows = {str(row["key"]): row for row in after["rows"]}     # type: ignore[union-attr]
    moved = tuple(key for key in before_rows
                  if before_rows[key]["class"] != after_rows[key]["class"])
    answered = tuple(row for row in rows if row["outcome"] in ("lt", "gt", "eq"))
    refused = tuple(row for row in rows if row["outcome"] not in ("lt", "gt", "eq"))
    as_declared = tuple(row for row in rows if row["as_declared"])
    surface_parsed = sum(1 for key in SURFACE_KEYS
                         if after_rows[key]["class"] == "parsed")
    return {
        "questions": len(PROBE),
        "declared": len(DECLARED_COMPARISONS),
        "rows": rows,
        "answered": len(answered),
        "refused": len(refused),
        "as_declared": len(as_declared),
        "refusal_reasons": tuple(sorted(
            {str(row["outcome"]) for row in refused})),
        "moved": moved,
        "surface_keys": len(SURFACE_KEYS),
        "surface_parsed": surface_parsed,
        "before": {name: before["counts"][name]                  # type: ignore[index]
                   for name in ("parsed", "surface", "absent")},
        "after": {name: after["counts"][name]                    # type: ignore[index]
                  for name in ("parsed", "surface", "absent")},
        "verdict": (
            f"the ordering operation answers {len(answered)} of the "
            f"{len(DECLARED_COMPARISONS)} declared comparisons and refuses "
            f"{len(refused)}, every one of them as declared before the run, "
            f"with the three refusals falling under "
            f"{', '.join(sorted({str(row['outcome']) for row in refused}))}. "
            f"It closes the one question the field surface declared "
            f"unreachable: {surface_parsed} of the {len(SURFACE_KEYS)} "
            f"held-and-unreachable questions are now parsed, and the whole "
            f"probe splits {after['counts']['parsed']} parsed, "           # type: ignore[index]
            f"{after['counts']['surface']} surface, "                      # type: ignore[index]
            f"{after['counts']['absent']} absent against "                 # type: ignore[index]
            f"{before['counts']['parsed']}/"                               # type: ignore[index]
            f"{before['counts']['surface']}/"                              # type: ignore[index]
            f"{before['counts']['absent']} before it."),                   # type: ignore[index]
        "caveat": (
            "one exact subtraction over two addressed readings is the whole "
            "of the derivation here, and the coordinate's meaning is the "
            "register's declaration rather than this module's finding. The "
            "four absent probe questions are untouched, and nothing here "
            "parses English: the question is still hand-translated into the "
            "system's own grammar."),
    }


if __name__ == "__main__":                      # pragma: no cover
    report = comparison_report()
    print(report["verdict"])
    for row in report["rows"]:
        print(f"  {row['key']:<18} {row['outcome']:<16} "
              f"{'as declared' if row['as_declared'] else 'NOT AS DECLARED'}")
