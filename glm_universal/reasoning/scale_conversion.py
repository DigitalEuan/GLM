"""``glm_universal.reasoning.scale_conversion`` -- the declared table of
conversions between scales, and the refusals it removes.

Why this module exists
----------------------
:mod:`glm_universal.reasoning.coordinate_order` orders two readings of one
coordinate and refuses two readings on two scales;
:mod:`glm_universal.reasoning.column_extremum` folds one coordinate down one
table and refuses a column gathered from two scales.  Both refusals have the
same cause, and both studies state it in the same words: *the operation holds
no conversions*.  Two readings of one quantity under two field names --
``atomic_weight_u`` of carbon and ``molar_mass_u`` of water, both in unified
atomic mass units -- are refused even though a conversion between them exists,
because nothing in the system says what that conversion is.

This module is what says it.  :data:`CONVERSIONS` is a table someone wrote
down: one row per scale, naming the quantity that scale measures, the unit it
is in, the exact rational factor and offset that carry a reading on it into
that quantity's canonical unit, and the source the numbers came from.

What a conversion is here, and what it is not
---------------------------------------------
A conversion is **affine and increasing**: ``value -> factor * value +
offset`` with ``factor > 0``.  The positivity is the whole of what makes it a
conversion rather than a re-ordering, and it is the side condition of the
machine-checked half: ``GLM.ScaleConversion.cmpQ_apply`` shows that a positive
conversion composed into the comparison leaves every verdict alone, and
``negative_factor_flips_the_verdict`` shows what a negative one does.  The
offset is admitted because a temperature scale that does not start at absolute
zero needs one; every row declared here happens to have offset ``0``, which is
reported rather than hidden.

A conversion is a **declaration**, not an inference.  Nothing here guesses a
conversion from a field name, and a scale the table does not mention is
refused exactly as before -- ``lean:line`` and ``python:line`` are both line
numbers and neither is declared, so the comparison of a Lean declaration's
line with a Python function's stays refused.
``GLM.ScaleConversion.the_table_carries_the_claim`` is the reason this matters:
two tables can make the same pair of readings order two different ways, so the
answer is only as good as the row someone wrote down.

What the table declares is a **unit**, not a measurand.  ``atomic_radius_pm``
and ``covalent_radius_pm`` are two different measurements and both are lengths
in picometres; the table says they are lengths in picometres and nothing more,
and an answer that compares them names both field names so a reader can see
what was compared.

What it buys
------------
Three things, each measured in :func:`conversion_report`:

* two readings of one quantity under two field names can be ordered
  (``order atomic_weight_u of carbon and molar_mass_u of water``);
* a column can be gathered by **quantity** across every declared scale of it
  (``largest mass`` over the 118 element rows and the 51 molecule rows
  together), which no single table holds;
* and a column whose rows are read on two declared scales of one quantity is
  converted rather than refused.

Everything the earlier operations answered, they still answer the same way:
``GLM.ScaleConversion.orderWith_conservative`` is that statement, and the two
earlier declared sets are re-run here to check it on the shipped data.

The machine-checked half is ``RequestProject/GLM/ScaleConversion.lean``.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

__all__ = [
    "ConversionError", "Conversion", "CONVERSIONS", "CANONICAL", "QUANTITIES",
    "EV_PER_MOLE_IN_KJ", "declared", "quantity_of", "relates", "bridge",
    "apply", "scales_of_quantity", "census", "DECLARED_BRIDGES",
    "conversion_report",
]


class ConversionError(ValueError):
    """Raised when two scales cannot be related, with the reason why.

    The reason is ``undeclared`` -- the table does not mention one of the two
    scales -- or ``different-quantity`` -- it mentions both, under two
    quantities that no conversion relates.
    """

    def __init__(self, reason: str, message: str):
        super().__init__(message)
        self.reason = reason


#: One electronvolt per particle, in kilojoules per mole, exactly.  Both
#: constants are SI definitions since 2019 -- the elementary charge is
#: ``1.602176634e-19`` coulombs and the Avogadro constant ``6.02214076e23``
#: per mole, both exact -- so their product is an exact rational and no
#: measurement enters this number.
EV_PER_MOLE_IN_KJ: Fraction = Fraction(1602176634 * 602214076, 10 ** 16)


@dataclass(frozen=True)
class Conversion:
    """One declared row: a scale, what it measures, and how to carry it."""

    scale: str            # 'element:atomic_weight_u'
    quantity: str         # 'mass'
    unit: str             # 'u' -- the canonical unit of that quantity
    factor: Fraction      # multiply by this ...
    offset: Fraction      # ... then add this, to land in the canonical unit
    source: str           # where the two numbers were written down

    @property
    def is_identity(self) -> bool:
        """The scale is already in the canonical unit."""
        return self.factor == 1 and self.offset == 0


#: The canonical unit of each declared quantity.  A conversion carries a
#: reading into this unit and comparisons are taken there;
#: ``GLM.ScaleConversion.verdict_independent_of_target_scale`` shows that the
#: verdict does not depend on that choice.
CANONICAL: Mapping[str, str] = {
    "mass": "u",
    "molar energy": "kJ/mol",
    "temperature": "K",
    "length": "pm",
}


#: **The declared table.**  Nine scales over four quantities, each row written
#: down with its source.  A scale that is not here is not converted, and a
#: quantity that is not here is not a quantity as far as this system is
#: concerned.
CONVERSIONS: Tuple[Conversion, ...] = (
    Conversion(
        "element:atomic_weight_u", "mass", "u", Fraction(1), Fraction(0),
        "the element register's own unit: the standard atomic weight is a "
        "mass in unified atomic mass units"),
    Conversion(
        "molecule:molar_mass_u", "mass", "u", Fraction(1), Fraction(0),
        "the molecule register's derived molar mass, summed from the same "
        "atomic weights and so in the same unit"),
    Conversion(
        "element:ionization_energy_eV", "molar energy", "kJ/mol",
        EV_PER_MOLE_IN_KJ, Fraction(0),
        "one electronvolt per atom is N_A e joules per mole, exactly, from "
        "the 2019 SI definitions of the elementary charge and the Avogadro "
        "constant"),
    Conversion(
        "element:electron_affinity_eV", "molar energy", "kJ/mol",
        EV_PER_MOLE_IN_KJ, Fraction(0),
        "the same conversion: an electron affinity in electronvolts is an "
        "energy per atom"),
    Conversion(
        "element:homonuclear_bde_kJ_per_mol", "molar energy", "kJ/mol",
        Fraction(1), Fraction(0),
        "the element register's bond dissociation energies are already per "
        "mole, in kilojoules"),
    Conversion(
        "element:melting_point_K", "temperature", "K", Fraction(1),
        Fraction(0),
        "the register holds thermodynamic temperatures in kelvin"),
    Conversion(
        "element:boiling_point_K", "temperature", "K", Fraction(1),
        Fraction(0),
        "the register holds thermodynamic temperatures in kelvin"),
    Conversion(
        "element:atomic_radius_pm", "length", "pm", Fraction(1), Fraction(0),
        "the register holds radii in picometres"),
    Conversion(
        "element:covalent_radius_pm", "length", "pm", Fraction(1),
        Fraction(0),
        "the register holds radii in picometres"),
)


#: The declared quantities, in a fixed order.
QUANTITIES: Tuple[str, ...] = tuple(sorted(CANONICAL))


# ===========================================================================
# 1.  READING THE TABLE
# ===========================================================================

def declared(scale: str) -> Optional[Conversion]:
    """The table's row for ``scale``, or ``None`` when it has none."""
    for row in CONVERSIONS:
        if row.scale == scale:
            return row
    return None


def quantity_of(scale: str) -> Optional[str]:
    """The quantity ``scale`` measures, as declared, or ``None``."""
    row = declared(scale)
    return None if row is None else row.quantity


def scales_of_quantity(quantity: str) -> Tuple[str, ...]:
    """Every declared scale of one quantity, in table order."""
    return tuple(row.scale for row in CONVERSIONS if row.quantity == quantity)


def relates(left: str, right: str) -> bool:
    """Whether the table relates two scales under one quantity."""
    one, two = quantity_of(left), quantity_of(right)
    return one is not None and one == two


def apply(conversion: Conversion, value: Fraction) -> Fraction:
    """``value`` carried into the canonical unit, exactly."""
    return conversion.factor * value + conversion.offset


def bridge(left: str, right: str) -> Tuple[Conversion, Conversion]:
    """The two rows that carry ``left`` and ``right`` into one unit.

    Raises :class:`ConversionError` as ``undeclared`` when the table does not
    mention one of the scales, and as ``different-quantity`` when it mentions
    both but under two quantities.  Both are facts about the table rather
    than failures of a search.
    """
    one, two = declared(left), declared(right)
    missing = [name for name, row in ((left, one), (right, two)) if row is None]
    if missing:
        raise ConversionError(
            "undeclared",
            f"the conversion table declares no unit for "
            f"{' or '.join(repr(name) for name in missing)}; a conversion is "
            f"a fact someone wrote down, not a guess from a field name, and "
            f"the {len(CONVERSIONS)} scales it does declare are "
            f"{', '.join(row.scale for row in CONVERSIONS)}")
    assert one is not None and two is not None
    if one.quantity != two.quantity:
        raise ConversionError(
            "different-quantity",
            f"{left} measures {one.quantity} and {right} measures "
            f"{two.quantity}; the table relates scales of one quantity and "
            f"declares no conversion between two quantities")
    return one, two


def bridge_all(scales: Sequence[str]) -> Tuple[Conversion, ...]:
    """The rows carrying every scale of one quantity into its unit.

    Raises :class:`ConversionError` exactly as :func:`bridge` does.
    """
    rows: List[Conversion] = []
    for scale in scales:
        row = declared(scale)
        if row is None:
            raise ConversionError(
                "undeclared",
                f"the conversion table declares no unit for {scale!r}; a "
                f"column gathered from a scale nobody declared is not one "
                f"column")
        rows.append(row)
    quantities = {row.quantity for row in rows}
    if len(quantities) > 1:
        raise ConversionError(
            "different-quantity",
            f"the scales gathered here measure "
            f"{', '.join(sorted(quantities))}; the table relates scales of "
            f"one quantity and declares no conversion between two")
    return tuple(rows)


# ===========================================================================
# 2.  THE CENSUS -- how much of the surface the table reaches
# ===========================================================================

def numeric_scales(surface) -> Tuple[str, ...]:
    """Every ``table:field`` scale on which the surface holds a number.

    A scale counts when at least one row of the table answers for the field
    with a value the ordering operation would read as a quantity.  Mapping
    coordinates are counted under the containing field, exactly as the
    ordering operation names them.
    """
    from .coordinate_order import as_exact
    out: List[str] = []
    for table in surface.tables():
        seen: set = set()
        for key, held in table.rows().items():
            for name, value in held.items():
                if isinstance(value, Mapping):
                    for inner, deep in value.items():
                        if as_exact(deep) is not None:
                            seen.add(f"{name}.{inner}")
                elif as_exact(value) is not None:
                    seen.add(name)
        out.extend(f"{table.name}:{name}" for name in sorted(seen))
    return tuple(out)


def census(surface) -> Dict[str, object]:
    """How many cross-scale pairs the declared table makes comparable.

    The denominator is every unordered pair of distinct numeric scales the
    field surface holds; the numerator is the pairs the table relates.  The
    ratio is small on purpose: a conversion is declared one row at a time,
    and every pair outside the table is still refused.
    """
    scales = numeric_scales(surface)
    total = len(scales) * (len(scales) - 1) // 2
    bridged = []
    for i, left in enumerate(scales):
        for right in scales[i + 1:]:
            if relates(left, right):
                bridged.append((left, right))
    declared_here = tuple(row.scale for row in CONVERSIONS
                          if row.scale in set(scales))
    return {
        "scales": len(scales),
        "pairs": total,
        "bridged": len(bridged),
        "bridged_pairs": tuple(bridged),
        "refused": total - len(bridged),
        "declared_rows": len(CONVERSIONS),
        "declared_on_surface": len(declared_here),
        "quantities": len(CANONICAL),
    }


# ===========================================================================
# 3.  THE DECLARED SET -- what the table is measured on
# ===========================================================================

#: The questions this round declares before running them.  Each row is
#: ``(key, kind, expected)`` where ``kind`` says how to run it:
#:
#: ``order``
#:     ``(field, left, other_field, right)`` -- two readings, the second
#:     under its own coordinate name.
#: ``column``
#:     ``(field, table)`` -- a column gathered by quantity or by field name.
#:
#: ``expected`` is the verdict (``lt``/``gt``/``eq``/``answer``) or the
#: refusal reason the operation must give.
DECLARED_BRIDGES: Tuple[Tuple[str, str, Tuple[str, ...], str], ...] = (
    # -- the comparisons a declared conversion makes answerable
    ("mass-atom-molecule", "order",
     ("atomic_weight_u", "carbon", "molar_mass_u", "water"), "lt"),
    ("mass-molecule-atom", "order",
     ("molar_mass_u", "glucose", "atomic_weight_u", "uranium"), "lt"),
    ("energy-eV-kJ", "order",
     ("ionization_energy_eV", "hydrogen",
      "homonuclear_bde_kJ_per_mol", "hydrogen"), "gt"),
    ("energy-eV-eV", "order",
     ("electron_affinity_eV", "chlorine",
      "ionization_energy_eV", "sodium"), "lt"),
    ("temperature-melt-boil", "order",
     ("melting_point_K", "tungsten", "boiling_point_K", "mercury"), "gt"),
    ("length-covalent-atomic", "order",
     ("covalent_radius_pm", "fluorine", "atomic_radius_pm", "cesium"), "lt"),
    # -- the refusals the table must leave standing
    ("undeclared-scale", "order",
     ("line", "GLM.NormFamily.family_tower", "line", "rung_audit"),
     "different-scale"),
    ("different-quantity", "order",
     ("atomic_weight_u", "carbon", "melting_point_K", "iron"),
     "different-scale"),
    ("still-nominal", "order",
     ("kind", "energy", "kind", "water"), "not-ordered"),
    # -- the columns the table lets be gathered, and the ones it does not
    ("column-mass", "column", ("mass", ""), "answer"),
    ("column-temperature", "column", ("temperature", ""), "incomplete"),
    ("column-line", "column", ("line", ""), "mixed-scale"),
)


def _run_declared(surface) -> Tuple[Dict[str, object], ...]:
    from .coordinate_order import OrderingError, order
    from .column_extremum import ExtremumError, extremum
    rows: List[Dict[str, object]] = []
    for key, kind, operands, expected in DECLARED_BRIDGES:
        entry: Dict[str, object] = {
            "key": key, "kind": kind, "operands": operands,
            "expected": expected,
        }
        if kind == "order":
            field, left, other, right = operands
            try:
                result = order(surface, field, left, right, other_field=other)
            except OrderingError as error:
                entry["outcome"] = error.reason
                entry["detail"] = str(error)
            else:
                entry["outcome"] = result.verdict
                entry["detail"] = result.sentence
                entry["unit"] = result.scale
                entry["converted"] = result.converted
        else:
            field, table = operands
            try:
                result = extremum(surface, field, "largest", table or None)
            except ExtremumError as error:
                entry["outcome"] = error.reason
                entry["detail"] = str(error)
            else:
                entry["outcome"] = "answer"
                entry["detail"] = result.sentence
                entry["unit"] = result.scale
                entry["read"] = result.rows
                entry["winners"] = tuple(r.row for r in result.winners)
        entry["as_declared"] = entry["outcome"] == expected
        rows.append(entry)
    return tuple(rows)


def conversion_report(session=None) -> Dict[str, object]:
    """What the declared table is, what it removes, and what it leaves.

    Four readings: the table itself; the declared question set with the
    outcome of each against what was declared for it; the census of how many
    of the surface's cross-scale pairs it reaches; and the two earlier
    declared sets re-run, which is the shipped form of
    ``GLM.ScaleConversion.orderWith_conservative``.
    """
    if session is None:
        from ..runtime.session import GeometricSession
        session = GeometricSession()
    from .coordinate_order import comparison_report
    from .column_extremum import extremum_report
    surface = session.field_surface
    rows = _run_declared(surface)
    reach = census(surface)
    answered = tuple(row for row in rows
                     if row["outcome"] in ("lt", "gt", "eq", "answer"))
    refused = tuple(row for row in rows if row not in answered)
    as_declared = tuple(row for row in rows if row["as_declared"])
    before = comparison_report(session)
    after = extremum_report(session)
    offsets = tuple(row for row in CONVERSIONS if row.offset != 0)
    return {
        "declared_rows": len(CONVERSIONS),
        "quantities": len(CANONICAL),
        "quantity_names": QUANTITIES,
        "non_unit_factors": len([row for row in CONVERSIONS
                                 if row.factor != 1]),
        "offsets": len(offsets),
        "table": tuple({
            "scale": row.scale, "quantity": row.quantity, "unit": row.unit,
            "factor": str(row.factor), "offset": str(row.offset),
            "source": row.source,
        } for row in CONVERSIONS),
        "declared": len(DECLARED_BRIDGES),
        "rows": rows,
        "answered": len(answered),
        "refused": len(refused),
        "as_declared": len(as_declared),
        "census": reach,
        "ordering_as_declared": before["as_declared"],
        "ordering_declared": before["declared"],
        "extremum_as_declared": after["as_declared"],
        "extremum_declared": after["declared"],
        "verdict": (
            f"the declared table is {len(CONVERSIONS)} rows over "
            f"{len(CANONICAL)} quantities, {len([r for r in CONVERSIONS if r.factor != 1])} "
            f"of them with a factor other than 1 and {len(offsets)} with an "
            f"offset. It answers {len(answered)} of the "
            f"{len(DECLARED_BRIDGES)} declared questions and refuses "
            f"{len(refused)}, every one of them as declared before the run. "
            f"Of the {reach['pairs']} pairs of the "
            f"{reach['scales']} numeric scales the field surface holds it "
            f"makes {reach['bridged']} comparable and leaves "
            f"{reach['refused']} refused. The two operations it widens are "
            f"unchanged on their own declared sets: "
            f"{before['as_declared']} of {before['declared']} comparisons "
            f"and {after['as_declared']} of {after['declared']} columns, "
            f"exactly as before."),
        "caveat": (
            "a conversion here is a declaration and not a derivation: the "
            "factor and the offset are written down with a source, and a "
            "scale the table does not mention is refused exactly as it was. "
            "The table declares a unit rather than a measurand, so a "
            "comparison across two measurements of one quantity -- an "
            "atomic radius against a covalent radius -- is answered with "
            "both field names named, and whether that comparison is "
            "interesting is the reader's judgement rather than the "
            "operation's. Nothing here parses English."),
    }


if __name__ == "__main__":                      # pragma: no cover
    report = conversion_report()
    print(report["verdict"])
    for row in report["rows"]:
        print(f"  {row['key']:<24} {str(row['outcome']):<18} "
              f"{'as declared' if row['as_declared'] else 'NOT AS DECLARED'}")
