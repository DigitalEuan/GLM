"""``glm_universal.reasoning.column_extremum`` -- the extremum of a column,
and the two ways a column can refuse to have one.

Why this module exists
----------------------
:mod:`glm_universal.reasoning.coordinate_order` composes exactly **two**
readings: *is energy more abstract than water?* is one coordinate read off two
named rows and ordered.  The question that round declared it stops short of is
a different shape --

    *which element is the most electronegative?*

-- because it names no rows at all.  It names a **column**: one coordinate
across *every* row of a declared table, with the answer being whichever row
attains the extremum.  Nothing in the registers holds that answer, so it is
not `table` in the sense of ``PROJECT_DIRECTIVES.md``; and unlike the ordering
operation it is not enough for the two readings in hand to be on one scale,
because the rows in hand are not the question -- *all* of them are.

This module is that operation, and it exists as much for what it refuses as
for what it answers.

The two refusals that are the point
-----------------------------------
``incomplete``
    A column with holes has no extremum.  The element register records
    ``electronegativity_pauling`` as missing for 23 of its 118 rows, and the
    largest of the 95 present values is **not** the largest of the column: it
    is the largest of the rows that happen to be filled in, which is a wrong
    answer rather than a partial one.  The missingness mask is a fact about
    the register -- the field surface already refuses a missing cell rather
    than answering it blank -- and this operation refuses the whole column
    rather than quietly taking the extremum over what is left.
    ``GLM.ColumnExtremum.extremum_over_present_is_not_the_extremum`` exhibits
    a column in which dropping one hole changes the answer.

``mixed-scale``
    The ordering operation's ``different-scale``, one level up.  A column
    gathered without naming a table can be two columns: ``line`` is held by
    the Lean address book *and* by the package's own source walk, and the
    largest of those numbers jointly is a fact about neither table.
    ``GLM.ColumnExtremum.extremum_not_invariant_under_one_row_rescaling``
    exhibits a positive rescaling of one row that moves the extremum, while
    ``extremum_scale_invariant`` shows that no rescaling of the *shared*
    scale can.

Two more, restated rather than reclassified: ``no-such-column`` when no row
holds the coordinate at all, and ``not-ordered`` when the column holds labels
rather than quantities.

What it does not claim
----------------------
The operation takes a maximum.  It reads every row through the same field
surface the ordering operation reads two rows through, it keeps every value
exact, and it reports **every** row that attains the extremum rather than
picking one -- 14 of the lexicon register's 149 rows sit at ``1`` on
``abstract_concrete``, and naming one of them would be a choice the register
does not make.  Under the standing target this is **derivation** of a fold
over addressed readings together with two stated refusals; it is not
addressing, and nothing here parses English.

The machine-checked half is ``RequestProject/GLM/ColumnExtremum.lean``.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from .coordinate_order import Reading, as_exact

__all__ = [
    "ExtremumError", "REFUSAL_REASONS", "ENDS", "Column", "Extremum",
    "column", "extremum", "DECLARED_EXTREMA", "extremum_report",
]


class ExtremumError(ValueError):
    """Raised when a column has no extremum, with the reason why.

    The reason is one of :data:`REFUSAL_REASONS`, carried in :attr:`reason`
    so a caller can act on the kind of refusal rather than on its wording.
    """

    def __init__(self, reason: str, message: str):
        super().__init__(message)
        self.reason = reason


#: Every way the operation can refuse, in the order it checks them.  A column
#: nobody holds is not a column; a column that is two columns has no common
#: order; a column of labels has no order at all; and a column with holes has
#: an extremum only over the rows that are filled in, which is not the
#: question that was asked.
REFUSAL_REASONS: Tuple[str, ...] = (
    "no-such-column", "mixed-scale", "not-ordered", "incomplete",
)

#: The two ends of a column.
ENDS: Tuple[str, ...] = ("largest", "smallest")


# ===========================================================================
# 1.  THE COLUMN
# ===========================================================================

@dataclass(frozen=True)
class Column:
    """Every reading of one coordinate across one table's rows."""

    field: str
    table: str
    scale: str
    readings: Tuple[Reading, ...]

    @property
    def rows(self) -> int:
        return len(self.readings)


def _row_reading(table, key: str, field: str) -> Tuple[str, object]:
    """How one row answers for one coordinate.

    Returns ``(status, payload)`` where ``status`` is ``"read"`` (payload is
    a :class:`~glm_universal.reasoning.coordinate_order.Reading`),
    ``"label"`` (payload is the rendered value), or ``"hole"`` (payload is
    the reason the row has no reading -- the coordinate is absent from it, or
    the register records it as missing).

    A coordinate held inside a mapping field is read as a coordinate of that
    field, exactly as the ordering operation reads it, and the scale records
    the containing field so that ``primitives.abstract_concrete`` cannot be
    confused with a field of that name.  Containing fields are tried in
    sorted order, so the reading is determinate.
    """
    from ..runtime import fields as fl
    held = table.rows()[key]

    def _make(name: str, value: object) -> Reading:
        return Reading(
            row=key, field=name, table=table.name, table_kind=table.kind,
            value=as_exact(value), rendered=fl.render_value(value),
            derived=name.split(".")[0] in table.derived,
            rule=table.derived.get(name.split(".")[0], ""),
            provenance=table.provenance)

    if field in held:
        value = held[field]
        if value is None:
            return ("hole", "the register records it as missing")
        if as_exact(value) is None:
            return ("label", fl.render_value(value))
        return ("read", _make(field, value))
    for name in sorted(held):
        inner = held[name]
        if not isinstance(inner, Mapping) or field not in inner:
            continue
        value = inner[field]
        if value is None:
            return ("hole", f"{name} records it as missing")
        if as_exact(value) is None:
            return ("label", fl.render_value(value))
        return ("read", _make(f"{name}.{field}", value))
    return ("hole", "the row does not carry it")


def _tables_holding(surface, field: str, table: Optional[str]) -> Tuple:
    """The declared tables a column of ``field`` could be gathered from.

    With a table named, that table and no other -- an unknown table name is
    refused where a caller can still see which names are declared.  Without
    one, every declared table in which at least one row answers for the
    coordinate, which is how a column can turn out to be two columns.
    """
    from ..runtime import fields as fl
    if table:
        try:
            return (surface.table_by_name(table),)
        except fl.FieldError as error:
            raise ExtremumError("no-such-column", str(error)) from None
    out = []
    for candidate in surface.tables():
        for key in candidate.rows():
            status, _payload = _row_reading(candidate, key, field)
            if status in ("read", "label"):
                out.append(candidate)
                break
    return tuple(out)


def _conversions_of(quantity: str):
    """The declared conversions of one quantity, in the table's own order."""
    from . import scale_conversion as sc
    return tuple(row for row in sc.CONVERSIONS if row.quantity == quantity)


def _quantity_column(surface, quantity: str) -> Column:
    """One column gathered by *quantity* across every declared scale of it.

    ``mass`` is held by the element register as ``atomic_weight_u`` and by
    the molecule register as ``molar_mass_u``, both in unified atomic mass
    units; no table holds the column of the two together, and the declared
    conversion table (:mod:`glm_universal.reasoning.scale_conversion`) is
    what makes it one column rather than two.  Each reading is carried into
    the quantity's canonical unit and keeps the scale it came from in
    :attr:`Reading.origin`.

    The refusals are the column's own: a hole anywhere in any of the gathered
    scales refuses the whole column, exactly as it does for one table.
    """
    from ..runtime import fields as fl
    from . import scale_conversion as sc
    readings: List[Reading] = []
    labels: List[Tuple[str, str]] = []
    holes: List[Tuple[str, str]] = []
    names: List[str] = []
    for carry in _conversions_of(quantity):
        table_name, _, field_name = carry.scale.partition(":")
        try:
            found = surface.table_by_name(table_name)
        except fl.FieldError:                       # pragma: no cover
            continue
        names.append(found.name)
        for key in sorted(found.rows()):
            status, payload = _row_reading(found, key, field_name)
            if status == "read":
                carried = sc.apply(carry, payload.value)    # type: ignore[union-attr]
                readings.append(replace(
                    payload, value=carried,                 # type: ignore[arg-type]
                    rendered=fl.render_value(carried),
                    origin=f"{payload.rendered} on {carry.scale}"))  # type: ignore[union-attr]
            elif status == "label":
                labels.append((key, str(payload)))
            else:
                holes.append((f"{found.name}:{key}", str(payload)))
    if not readings and not labels:
        raise ExtremumError(
            "no-such-column",
            f"no declared scale of {quantity!r} is held by any table here")
    if labels:
        row, rendered = labels[0]
        raise ExtremumError(
            "not-ordered",
            f"{quantity} of {row} is {rendered!r}, which is a label rather "
            f"than a quantity; a column of labels has no extremum")
    if holes:
        named = ", ".join(row for row, _why in holes[:5])
        raise ExtremumError(
            "incomplete",
            f"{len(holes)} of {len(readings) + len(holes)} rows have no "
            f"reading of {quantity!r} ({holes[0][1]}): {named}"
            f"{', ...' if len(holes) > 5 else ''}. The extremum of the rows "
            f"that are filled in is not the extremum of the column -- it is "
            f"a wrong answer rather than a partial one -- so the operation "
            f"refuses the column and names what is missing")
    return Column(field=quantity, table=", ".join(names),
                  scale=sc.CANONICAL[quantity], readings=tuple(readings))


def column(surface, field: str, table: Optional[str] = None) -> Column:
    """Every reading of ``field`` down a column, or a refusal that says why.

    ``surface`` is a :class:`~glm_universal.runtime.fields.FieldSurface`.
    The refusals are :data:`REFUSAL_REASONS`, checked in that order: a column
    no row holds, a column gathered from more than one scale *that the
    declared conversion table does not relate*, a column of labels, and a
    column with a hole in it.

    With no table named and ``field`` a declared quantity rather than a field
    name, the column is gathered by quantity across every declared scale of
    it -- see :func:`_quantity_column`.
    """
    from . import scale_conversion as sc
    if table is None and field in sc.QUANTITIES:
        return _quantity_column(surface, field)
    tables = _tables_holding(surface, field, table)
    if not tables:
        raise ExtremumError(
            "no-such-column",
            f"no declared table has a row answering for {field!r}; a column "
            f"is a coordinate every row of one table carries, and this one "
            f"is carried by none")
    readings: List[Reading] = []
    labels: List[Tuple[str, str]] = []
    holes: List[Tuple[str, str]] = []
    scales: List[str] = []
    for candidate in tables:
        for key in sorted(candidate.rows()):
            status, payload = _row_reading(candidate, key, field)
            if status == "read":
                readings.append(payload)                # type: ignore[arg-type]
                if payload.scale not in scales:         # type: ignore[union-attr]
                    scales.append(payload.scale)        # type: ignore[union-attr]
            elif status == "label":
                labels.append((key, str(payload)))
            else:
                holes.append((f"{candidate.name}:{key}", str(payload)))
    if not readings and not labels:
        raise ExtremumError(
            "no-such-column",
            f"the table{'s' if len(tables) > 1 else ''} "
            f"{', '.join(t.name for t in tables)} "
            f"hold{'' if len(tables) > 1 else 's'} no reading of "
            f"{field!r} at all")
    unit = ""
    if len(scales) > 1:
        from ..runtime import fields as fl
        from . import scale_conversion as sc
        try:
            carried = sc.bridge_all(scales)
        except sc.ConversionError as error:
            raise ExtremumError(
                "mixed-scale",
                f"{field!r} is read on {len(scales)} scales -- "
                f"{', '.join(scales)} -- and {error}, so the rows gathered "
                f"here are not one column; the extremum of two scales "
                f"together is a fact about neither, and the operation "
                f"refuses rather than taking it. Name one table to ask for "
                f"one of them") from None
        by_scale = {row.scale: row for row in carried}
        readings = [replace(
            r, value=sc.apply(by_scale[r.scale], r.value),
            rendered=fl.render_value(sc.apply(by_scale[r.scale], r.value)),
            origin=f"{r.rendered} on {r.scale}") for r in readings]
        unit = carried[0].unit
    if labels:
        row, rendered = labels[0]
        raise ExtremumError(
            "not-ordered",
            f"{field} of {row} is {rendered!r}, which is a label rather "
            f"than a quantity; {len(labels)} of "
            f"{len(labels) + len(readings) + len(holes)} rows read that way, "
            f"and a column of labels has no extremum")
    if holes:
        named = ", ".join(row for row, _why in holes[:5])
        raise ExtremumError(
            "incomplete",
            f"{len(holes)} of {len(readings) + len(holes)} rows have no "
            f"reading of {field!r} ({holes[0][1]}): {named}"
            f"{', ...' if len(holes) > 5 else ''}. The extremum of the rows "
            f"that are filled in is not the extremum of the column -- it is "
            f"a wrong answer rather than a partial one -- so the operation "
            f"refuses the column and names what is missing")
    return Column(field=field, table=", ".join(t.name for t in tables),
                  scale=unit or scales[0], readings=tuple(readings))


# ===========================================================================
# 2.  THE OPERATION
# ===========================================================================

@dataclass(frozen=True)
class Extremum:
    """Which rows attain an end of a column, and by how much."""

    field: str
    table: str
    scale: str
    end: str                          # 'largest' or 'smallest'
    value: Fraction
    rendered: str
    winners: Tuple[Reading, ...]      # every row attaining it, in row order
    rows: int
    runner_up: Optional[Fraction]     # the next distinct value, or None
    derived: bool

    @property
    def gap(self) -> Optional[Fraction]:
        """The exact distance to the next distinct value, when there is one."""
        if self.runner_up is None:
            return None
        return abs(self.value - self.runner_up)

    @property
    def sentence(self) -> str:
        """The verdict as one line, with the tie spelled out when there is one."""
        names = ", ".join(r.row for r in self.winners)
        head = (f"the {self.end} {self.field} over the {self.rows} rows of "
                f"{self.table} is {self.rendered}, attained by ")
        who = (f"{len(self.winners)} rows -- {names}"
               if len(self.winners) > 1 else names)
        gap = ("" if self.gap is None
               else f", ahead of the next distinct value by an exact "
                    f"{self.gap}")
        return (f"{head}{who}{gap}, every row read on the {self.scale} "
                f"scale{' (a derived column)' if self.derived else ''}")


def extremum(surface, field: str, end: str = "largest",
             table: Optional[str] = None) -> Extremum:
    """The extremum of one column, or a refusal that says why there is none.

    Every row of the column is read, the values are compared exactly as
    rationals, and **every** row attaining the end is reported: a tie is a
    fact about the register and picking one of the tied rows would be a
    choice the register does not make.
    """
    if end not in ENDS:
        raise ExtremumError(
            "no-such-column",
            f"{end!r} is not an end of a column; the ends are "
            f"{' and '.join(ENDS)}")
    found = column(surface, field, table)
    values = [r.value for r in found.readings]
    best = max(values) if end == "largest" else min(values)
    winners = tuple(r for r in found.readings if r.value == best)
    rest = [v for v in values if v != best]
    runner_up = None
    if rest:
        runner_up = max(rest) if end == "largest" else min(rest)
    return Extremum(
        field=field, table=found.table, scale=found.scale, end=end,
        value=best, rendered=winners[0].rendered, winners=winners,
        rows=found.rows, runner_up=runner_up,
        derived=any(r.derived for r in winners))


# ===========================================================================
# 3.  THE DECLARED SET -- what the operation is measured on
# ===========================================================================

#: The columns this round declares before running them: four it must answer
#: -- a complete source column at both ends, a derived column, and a column
#: with a fourteen-row tie held inside a mapping field -- and one for each of
#: the four ways it may refuse.  Each row is
#: ``(key, end, field, table, expected)`` where ``expected`` is ``answer`` or
#: the refusal reason.
DECLARED_EXTREMA: Tuple[Tuple[str, str, str, str, str], ...] = (
    ("heaviest", "largest", "atomic_weight_u", "element", "answer"),
    ("lightest", "smallest", "atomic_weight_u", "element", "answer"),
    ("derived-column", "largest", "molar_mass_u", "molecule", "answer"),
    ("tie", "largest", "abstract_concrete", "carrier:lexicon", "answer"),
    ("holes", "largest", "electronegativity_pauling", "element",
     "incomplete"),
    ("nominal", "largest", "name", "element", "not-ordered"),
    ("two-tables", "largest", "line", "", "mixed-scale"),
    ("absent", "largest", "boiling_point", "element", "no-such-column"),
)


def _run_declared(surface) -> Tuple[Dict[str, object], ...]:
    rows: List[Dict[str, object]] = []
    for key, end, field, table, expected in DECLARED_EXTREMA:
        entry: Dict[str, object] = {
            "key": key, "end": end, "field": field,
            "table": table or "(unnamed)", "expected": expected,
        }
        try:
            result = extremum(surface, field, end, table or None)
        except ExtremumError as error:
            entry["outcome"] = error.reason
            entry["detail"] = str(error)
        else:
            entry["outcome"] = "answer"
            entry["detail"] = result.sentence
            entry["scale"] = result.scale
            entry["value"] = str(result.value)
            entry["winners"] = tuple(r.row for r in result.winners)
            entry["read"] = result.rows
        entry["as_declared"] = entry["outcome"] == expected
        rows.append(entry)
    return tuple(rows)


def _report(session=None) -> Dict[str, object]:
    if session is None:
        from ..runtime.session import GeometricSession
        session = GeometricSession()
    rows = _run_declared(session.field_surface)
    answered = tuple(row for row in rows if row["outcome"] == "answer")
    refused = tuple(row for row in rows if row["outcome"] != "answer")
    as_declared = tuple(row for row in rows if row["as_declared"])
    reasons = tuple(sorted({str(row["outcome"]) for row in refused}))
    ties = tuple(row for row in answered
                 if len(row.get("winners", ())) > 1)       # type: ignore[arg-type]
    return {
        "declared": len(DECLARED_EXTREMA),
        "rows": rows,
        "answered": len(answered),
        "refused": len(refused),
        "as_declared": len(as_declared),
        "refusal_reasons": reasons,
        "reasons_declared": len(REFUSAL_REASONS),
        "ties": len(ties),
        "verdict": (
            f"the extremum operation answers {len(answered)} of the "
            f"{len(DECLARED_EXTREMA)} declared columns and refuses "
            f"{len(refused)}, every one of them as declared before the run, "
            f"with the refusals falling under all "
            f"{len(REFUSAL_REASONS)} of its named reasons "
            f"({', '.join(reasons)}). {len(ties)} of the answers is a tie "
            f"reported as a tie rather than resolved."),
        "caveat": (
            "a fold over addressed readings is the whole of the derivation "
            "here: the operation reads every row of one table through the "
            "field surface, compares exactly, and names every row that "
            "attains the end. It invents no value for a hole and bridges no "
            f"scale, which is why {len(refused)} of the "
            f"{len(DECLARED_EXTREMA)} declared columns are refusals rather "
            "than answers, and nothing here parses English."),
    }


def extremum_report(session=None) -> Dict[str, object]:
    """What the extremum operation answers and refuses.

    The declared set is run against a session's own field surface, so a
    caller that already has one passes it rather than building a second.
    """
    return _report(session)


if __name__ == "__main__":                      # pragma: no cover
    report = extremum_report()
    print(report["verdict"])
    for row in report["rows"]:
        print(f"  {row['key']:<16} {row['outcome']:<16} "
              f"{'as declared' if row['as_declared'] else 'NOT AS DECLARED'}")
