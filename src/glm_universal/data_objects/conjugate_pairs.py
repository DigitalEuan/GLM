"""``glm_universal.data_objects.conjugate_pairs`` -- one register across domains.

Why this register exists
------------------------
``heat : temperature :: force : ?`` was the machine's standing example of a
question it could not answer.  Two things stopped it, and they are different
things:

* the **semantic half** -- the lexicon relates ``heat`` and ``temperature``
  only by ``temperature drives heat`` and by ``related_to``, and looking
  either up from ``force`` reaches nothing, so no relation the register states
  transports;
* the **register half** -- ``temperature`` and ``force`` are physics
  quantities and ``heat`` is not, so the query settles in the lexicon, which
  holds all three words and none of their dimensions.

Both halves are the same shortcoming seen twice: there was no register whose
rows *span* the domains.  This module is that register.  Its rows are the
**energy-conjugate pairs** -- the pairing that says an amount of energy is an
intensive *effort* acting through an extensive *extent*:

===============  ===================  ==================  ======================
domain           effort               extent              transfer
===============  ===================  ==================  ======================
thermal          ``temperature``      ``entropy``         ``heat``
mechanical       ``force``            ``length``          ``work``
hydraulic        ``pressure``         ``volume``          ``flow_work``
electrical       ``voltage``          ``charge``          ``electrical_work``
rotational       ``torque``           ``angle``           ``rotational_work``
chemical         ``chemical_potential``  ``amount``       ``chemical_work``
surface          ``surface_tension``  ``area``            ``surface_work``
===============  ===================  ==================  ======================

Read a row as ``transfer = effort x extent``: heat is ``T dS``, work is
``F dx``, flow work is ``p dV``, electrical work is ``V dq``.

What makes a row admissible
---------------------------
A register that a session may add rows to is only as good as the check it
runs on a new row, so the check is stated and is exact:

1. the **effort** and the **extent** are quantities the physics register
   already holds -- this register names nothing of its own on those two
   columns and so can no more invent a quantity than an alias can;
2. their EXT10 exponent vectors **sum to the exponent vector of** ``energy``,
   and their decimal scales sum to its scale.  This is integer arithmetic on
   the register's own numbers: it is the reason ``pressure`` pairs with
   ``volume`` and not with ``area``;
3. the **transfer** carries the dimension of energy by construction, and is
   *this* register's name for the energy moved when the row's effort acts
   through the row's extent;
4. no name occupies two roles anywhere in the table, so a name determines its
   role and the three relations below are bijections.

:func:`conjugate_audit` runs all four over the whole table and is checked by
the test suite; a row that fails any of them is a row that never loads.

The three relations
-------------------
``effort_of``
    ``temperature effort_of heat`` -- the effort conjugate to a transfer.
``extent_of``
    ``entropy extent_of heat`` -- the extent a transfer is accumulated over.
``conjugate_of``
    ``temperature conjugate_of entropy`` -- effort against extent within one
    row, which is the pairing itself.

Each is a bijection between two columns of the table, which is what makes it
transportable in *either* direction with a unique answer;
:mod:`glm_universal.reasoning.conjugate` is where that is turned into an
answer, and states the admissibility rule it uses.

Exactness
---------
Every number here is a :class:`fractions.Fraction` read out of the physics
register.  This module stores no magnitudes of its own: a row is four names
and a justification.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

from . import physics as ph

__all__ = [
    "ROLES", "RELATIONS", "RELATION_COLUMNS", "ENERGY_QUANTITY",
    "ConjugateRow", "CONJUGATE_ROWS",
    "rows", "row_of_domain", "role_of", "row_of_name", "names",
    "related", "transfer_dimension", "conjugate_audit",
]


#: The three columns of a row, which are also the three roles a name may
#: occupy.  A name occupies exactly one, and :func:`conjugate_audit` checks it.
ROLES: Tuple[str, ...] = ("transfer", "effort", "extent")

#: The relations the register states, each as the ordered pair of columns it
#: runs between: ``subject relation object``.
RELATION_COLUMNS: Dict[str, Tuple[str, str]] = {
    "effort_of": ("effort", "transfer"),
    "extent_of": ("extent", "transfer"),
    "conjugate_of": ("effort", "extent"),
}

#: The relation names, in register order.
RELATIONS: Tuple[str, ...] = tuple(RELATION_COLUMNS)

#: The physics quantity whose dimension every row must reproduce.
ENERGY_QUANTITY: str = "energy"


@dataclass(frozen=True)
class ConjugateRow:
    """One energy domain: its effort, its extent, and the transfer they make.

    ``effort`` and ``extent`` are names of the physics register.  ``transfer``
    is this register's name for the energy moved when the effort acts through
    the extent; ``heat`` and ``work`` are also lexicon words, the other five
    are named here and nowhere else, which is why each carries a
    ``definition`` saying exactly what it is.
    """

    domain: str
    effort: str
    extent: str
    transfer: str
    definition: str
    justification: str

    def column(self, role: str) -> str:
        """The name in one column of this row."""
        if role not in ROLES:
            raise KeyError(f"conjugate_pairs: unknown role {role!r}")
        return {"transfer": self.transfer, "effort": self.effort,
                "extent": self.extent}[role]


#: The table.  Seven rows, one per energy domain the physics register can
#: dimension both halves of.  A row is added by writing it here and running
#: :func:`conjugate_audit`, which decides it against the register rather than
#: against a reader's judgement.
CONJUGATE_ROWS: Tuple[ConjugateRow, ...] = (
    ConjugateRow(
        domain="thermal", effort="temperature", extent="entropy",
        transfer="heat", definition="heat = temperature x entropy",
        justification="The first law writes a reversible thermal transfer as "
                      "T dS: temperature is the intensive potential and "
                      "entropy the extensive quantity it acts through."),
    ConjugateRow(
        domain="mechanical", effort="force", extent="length",
        transfer="work", definition="work = force x length",
        justification="Mechanical work is F dx along the displacement: force "
                      "is the effort and the displacement its extent."),
    ConjugateRow(
        domain="hydraulic", effort="pressure", extent="volume",
        transfer="flow_work", definition="flow_work = pressure x volume",
        justification="Pressure-volume work, p dV, is the energy a fluid "
                      "carries across a boundary."),
    ConjugateRow(
        domain="electrical", effort="voltage", extent="charge",
        transfer="electrical_work", definition="electrical_work = voltage x charge",
        justification="Moving a charge through a potential difference costs "
                      "V dq, which is what a volt is defined to make true."),
    ConjugateRow(
        domain="rotational", effort="torque", extent="angle",
        transfer="rotational_work", definition="rotational_work = torque x angle",
        justification="Rotational work is tau dtheta; the register carries "
                      "plane angle as an axis of its own, and it is "
                      "dimensionless there, so the identity closes exactly."),
    ConjugateRow(
        domain="chemical", effort="chemical_potential", extent="amount",
        transfer="chemical_work", definition="chemical_work = chemical_potential x amount",
        justification="The chemical term of the fundamental relation is "
                      "mu dN: the chemical potential is an energy per mole "
                      "and amount of substance is what it acts through."),
    ConjugateRow(
        domain="surface", effort="surface_tension", extent="area",
        transfer="surface_work", definition="surface_work = surface_tension x area",
        justification="Making new surface costs gamma dA; surface tension is "
                      "an energy per unit area, which is the same statement."),
)


# ===========================================================================
# 1.  READING THE TABLE
# ===========================================================================

def rows() -> Tuple[ConjugateRow, ...]:
    """Every row of the register."""
    return CONJUGATE_ROWS


def row_of_domain(domain: str) -> Optional[ConjugateRow]:
    """The row of one energy domain, or ``None``."""
    for row in CONJUGATE_ROWS:
        if row.domain == domain:
            return row
    return None


@lru_cache(maxsize=1)
def _index() -> Dict[str, Tuple[ConjugateRow, str]]:
    out: Dict[str, Tuple[ConjugateRow, str]] = {}
    for row in CONJUGATE_ROWS:
        for role in ROLES:
            out[row.column(role)] = (row, role)
    return out


def role_of(name: str) -> Optional[str]:
    """Which column a name occupies, or ``None`` if the register has no such name."""
    found = _index().get(name)
    return None if found is None else found[1]


def row_of_name(name: str) -> Optional[ConjugateRow]:
    """The row a name belongs to, or ``None``."""
    found = _index().get(name)
    return None if found is None else found[0]


def names() -> Tuple[str, ...]:
    """Every name the register mentions, sorted."""
    return tuple(sorted(_index()))


def related(subject: str, other: str) -> Tuple[str, ...]:
    """Every relation of the register that holds between two names, in either order.

    The answer is a tuple because two names could in principle stand in more
    than one; on the table as it is, they never do, and
    :func:`conjugate_audit` measures that rather than assuming it.
    """
    found: List[str] = []
    for relation, (left, right) in RELATION_COLUMNS.items():
        for row in CONJUGATE_ROWS:
            pair = (row.column(left), row.column(right))
            if (subject, other) == pair or (other, subject) == pair:
                found.append(relation)
    return tuple(found)


def transfer_dimension() -> Tuple[Fraction, ...]:
    """The EXT10 exponent vector every transfer carries: that of ``energy``."""
    return ph.quantity_by_name(ENERGY_QUANTITY).exps_ext10


# ===========================================================================
# 2.  THE AUDIT -- THE FOUR CHECKS A ROW MUST PASS
# ===========================================================================

def conjugate_audit() -> Dict[str, object]:
    """Run the four admissibility checks over the whole table.

    Nothing is asserted here: each row is decided against the physics
    register, and the returned mapping says which rows passed which check.
    ``sound`` is true exactly when all four hold everywhere.
    """
    energy = ph.quantity_by_name(ENERGY_QUANTITY)
    register_names = {q.name for q in ph.load_physics_register()}
    rows_out: List[Dict[str, object]] = []
    seen: Dict[str, str] = {}
    duplicated: List[str] = []
    for row in CONJUGATE_ROWS:
        in_register = (row.effort in register_names
                       and row.extent in register_names)
        exponents_sum = None
        scale_sum = None
        dimensional = False
        if in_register:
            effort = ph.quantity_by_name(row.effort)
            extent = ph.quantity_by_name(row.extent)
            exponents_sum = tuple(x + y for x, y in
                                  zip(effort.exps_ext10, extent.exps_ext10))
            scale_sum = effort.scale + extent.scale
            dimensional = (exponents_sum == energy.exps_ext10
                           and scale_sum == energy.scale)
        for role in ROLES:
            name = row.column(role)
            if name in seen:
                duplicated.append(name)
            seen[name] = f"{row.domain}.{role}"
        rows_out.append({
            "domain": row.domain,
            "effort": row.effort,
            "extent": row.extent,
            "transfer": row.transfer,
            "definition": row.definition,
            "effort_in_register": row.effort in register_names,
            "extent_in_register": row.extent in register_names,
            "exponent_sum": None if exponents_sum is None
                            else ph.dimension_string(exponents_sum),
            "scale_sum": scale_sum,
            "dimensional": dimensional,
            "transfer_in_physics_register": row.transfer in register_names,
        })
    transfers_named_here = tuple(
        row.transfer for row in CONJUGATE_ROWS
        if row.transfer not in register_names)
    multiple = tuple(
        sorted({(a, b) for a in seen for b in seen
                if a < b and len(related(a, b)) > 1}))
    return {
        "rows": tuple(rows_out),
        "row_count": len(CONJUGATE_ROWS),
        "roles": list(ROLES),
        "relations": list(RELATIONS),
        "names": len(seen),
        "energy_dimension": energy.dimension_string(),
        "endpoints_in_register": all(bool(r["effort_in_register"])
                                     and bool(r["extent_in_register"])
                                     for r in rows_out),
        "all_dimensional": all(bool(r["dimensional"]) for r in rows_out),
        "duplicated_names": tuple(sorted(set(duplicated))),
        "roles_unique": not duplicated,
        "pairs_in_two_relations": multiple,
        "relations_disjoint": not multiple,
        "transfers_named_here": transfers_named_here,
        "sound": (all(bool(r["dimensional"]) for r in rows_out)
                  and not duplicated and not multiple),
        "check": (
            "A row is admissible when its effort and extent are quantities "
            "the physics register already holds, their EXT10 exponents and "
            "decimal scales sum to those of energy, and no name of the table "
            "occupies two roles.  All three are decided here against the "
            "register, in exact integer arithmetic."),
    }
