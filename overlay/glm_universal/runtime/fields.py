"""``glm_universal.runtime.fields`` -- the field surface: one named field of
one named row.

Why this module exists
----------------------
[`studies/PROBE_ORACLE_STUDY.md`] priced two instruments against the twenty
pre-registered probe questions and found the split inverted: a parser from
open English is worth four questions, and **ten** are held by a shipped
register row or a shipped function that *no query kind returns*.  The element
register holds ``atomic_weight_u = 12011/1000`` for carbon, and asking the
system for it was impossible -- ``describe C`` answers with the carrier's
geometry and never with the row's own fields.

This module is the cheap instrument that study recommended, built with the
label the study insisted on: a field surface is **table**, the weakest of the
three faculties named in ``PROJECT_DIRECTIVES.md``.  It derives nothing and
addresses nothing; it makes what is already held *reachable*, and that is all
it claims.

What is addressable, and what is not
------------------------------------
A field is addressed by two names -- the row and the field -- against a fixed
list of declared tables, in a fixed priority order:

``element`` / ``molecule``
    the *source rows* the chemistry and molecule registers are built from,
    which hold far more than the 24 coordinates a carrier keeps.  The
    molecule table also exposes the register's declared derived properties
    (``molar_mass_u`` and the rest of :data:`MOLECULE_DERIVED`), labelled as
    derived, with the rule that computes each one.
``carrier:<domain>``
    the attributes every loaded carrier keeps, one table per register.  The
    lexicon's table additionally exposes each relation it holds as a field,
    so ``field derivative_of of velocity`` answers ``position``.
``lean``
    the Lean address book: one row per declaration, with the file, the line,
    the kind and the namespace it was found at.
``python``
    the package's own top-level functions and classes, read by the AST walk
    the package already ships, with the module that defines each one.
``function:<dotted name>``
    a **declared** zero-argument function returning a mapping, whose keys are
    the fields.  The registry is :data:`FUNCTION_SURFACES` and nothing else is
    callable from here: a field query never imports a module the surface was
    not declared with, and never evaluates a string.

Two shapes, and what each refuses
---------------------------------
``field <name> of <row>``
    the value, exactly, with the table and the provenance beside it.
``fields of <row>``
    the field names that row answers to -- which is how *what does this
    return?* is asked without naming the answer in the question.

A row no table holds is refused with the nearest row names; a field no table
holds *for that row* is refused with the fields that row does answer to; a
field the register records as missing for that row is refused as missing
rather than answered with a blank.  Refusing at a named boundary rather than
guessing is the same discipline the rest of the runtime is held to.

Exactness
---------
Every value crosses this boundary as an ``int``, a
:class:`~fractions.Fraction`, a string or a tuple of those.  A rational is
rendered as ``n/d``, and beside it as an exact decimal *only* when the
denominator is a product of twos and fives, so a terminating expansion exists
and no rounding is performed.  No float is constructed anywhere in this
module.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field as dc_field
from fractions import Fraction
from pathlib import Path
from typing import (Callable, Dict, List, Mapping, Optional, Sequence, Tuple)

from .parser import normalise

__all__ = [
    "FieldError", "FieldValue", "RowFields", "FieldTable",
    "MOLECULE_DERIVED", "FUNCTION_SURFACES", "TABLE_KINDS",
    "FieldSurface", "surface", "render_value", "exact_decimal",
]


class FieldError(ValueError):
    """Raised when a row, or a field of a row, is not addressable.

    Carries the reason in its message: which of the two names failed, and
    what the surface does hold near it.
    """


#: What a table is made of.  The order is the order provenance is reported
#: in, from the data the system is built on to the text it merely ships.
TABLE_KINDS: Tuple[str, ...] = ("source", "carrier", "address", "code",
                                "function")


#: The molecule register's declared derived properties, and the rule that
#: computes each.  They are *not* stored fields: they are recomputed from the
#: formula and the element register on every read, which is why the surface
#: labels them derived rather than letting them pass as held facts.
MOLECULE_DERIVED: Mapping[str, str] = {
    "atom_count": "sum of the formula's counts",
    "distinct_elements": "size of the formula's support",
    "molar_mass_u": "sum over the formula of atomic_weight_u times count, "
                    "from the element register",
    "electron_count": "sum over the formula of z times count, less the charge",
    "valence_electron_total": "sum over the formula of valence_electrons "
                              "times count, less the charge",
    "heteroatom_count": "count of atoms that are neither carbon nor hydrogen",
}


def _norm_family_completeness() -> Mapping[str, object]:
    from ..substrate import norm_family
    return norm_family.completeness()


def _molecules_report() -> Mapping[str, object]:
    from ..data_objects import molecules
    return molecules.molecules_report()


def _element_coverage() -> Mapping[str, object]:
    from ..reasoning import element_coverage
    return element_coverage.coverage_table()


#: The declared function surfaces: dotted name -> the zero-argument function
#: whose returned mapping the keys are read from.  Declaring them is the
#: whole safety line -- a field query cannot reach a function that is not
#: here, so asking the surface about code can never run code the surface was
#: not built with.
FUNCTION_SURFACES: Mapping[str, Callable[[], Mapping[str, object]]] = {
    "glm_universal.substrate.norm_family.completeness":
        _norm_family_completeness,
    "glm_universal.data_objects.molecules.molecules_report":
        _molecules_report,
    "glm_universal.reasoning.element_coverage.coverage_table":
        _element_coverage,
}


# ===========================================================================
# 1.  RENDERING -- exact, and decimal only when a decimal exists
# ===========================================================================

def exact_decimal(value: Fraction) -> Optional[str]:
    """``value`` as a terminating decimal, or ``None`` when it has none.

    A rational has a finite decimal expansion exactly when its reduced
    denominator is a product of twos and fives.  When it does, the expansion
    here is exact -- computed by integer division after scaling -- and when
    it does not, nothing is returned rather than something rounded.
    """
    denominator = value.denominator
    twos = fives = 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    if denominator != 1:
        return None
    places = max(twos, fives)
    if places == 0:
        return str(value.numerator)
    scaled = abs(value.numerator) * 10 ** places // value.denominator
    digits = str(scaled).rjust(places + 1, "0")
    sign = "-" if value.numerator < 0 else ""
    return f"{sign}{digits[:-places]}.{digits[-places:]}"


def render_value(value: object) -> str:
    """The canonical rendering of one field value.

    Integers and strings render as themselves; a rational renders as ``n/d``
    with its exact decimal beside it when one exists; a sequence renders as
    its elements, comma separated; a mapping as ``key=value`` pairs in sorted
    key order, so the rendering of a dictionary does not depend on insertion
    order.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, Fraction):
        decimal = exact_decimal(value)
        text = f"{value.numerator}/{value.denominator}"
        return text if decimal is None else f"{text} (= {decimal})"
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        return ", ".join(f"{k}={render_value(value[k])}"
                         for k in sorted(value, key=str))
    if isinstance(value, (tuple, list, frozenset, set)):
        items = sorted(value, key=str) if isinstance(value, (set, frozenset)) \
            else list(value)
        return ", ".join(render_value(item) for item in items)
    if value is None:
        return "none"
    return str(value)


# ===========================================================================
# 2.  WHAT A LOOKUP RETURNS
# ===========================================================================

@dataclass(frozen=True)
class FieldValue:
    """One field of one row, with where it came from."""

    table: str
    table_kind: str
    row: str
    field: str
    value: object
    rendered: str
    provenance: str
    derived: bool = False
    rule: str = ""


@dataclass(frozen=True)
class RowFields:
    """Every field one row answers to, across the tables that hold it."""

    row: str
    tables: Tuple[str, ...]
    names: Tuple[str, ...]


@dataclass(frozen=True)
class FieldTable:
    """One addressable table: rows by name, fields by name.

    ``build`` is called at most once and its result cached, so a query that
    is answered by the first table never pays for the Lean address book or
    the source walk behind it.
    """

    name: str
    kind: str
    gloss: str
    build: Callable[[], Mapping[str, Mapping[str, object]]]
    provenance: str
    derived: Mapping[str, str] = dc_field(default_factory=dict)
    _cache: Dict[str, Mapping[str, Mapping[str, object]]] = dc_field(
        default_factory=dict, repr=False, compare=False)

    def rows(self) -> Mapping[str, Mapping[str, object]]:
        """The table, built on first use and cached thereafter."""
        if "rows" not in self._cache:
            self._cache["rows"] = self.build()
        return self._cache["rows"]

    def aliases(self) -> Mapping[str, str]:
        """Normalised surface form -> row key, for every row of the table."""
        if "aliases" not in self._cache:
            staged: Dict[str, str] = {}
            for key, fields in self.rows().items():
                for alias in _row_aliases(key, fields):
                    staged.setdefault(alias, key)
            self._cache["aliases"] = staged            # type: ignore[assignment]
        return self._cache["aliases"]                  # type: ignore[return-value]


def _row_aliases(key: str, fields: Mapping[str, object]) -> Tuple[str, ...]:
    """The surface forms one row answers to.

    The key itself, its normalised form, and -- when the row carries a
    ``name`` or a ``symbol`` field that is a string -- those too.  Nothing is
    invented: an alias is always a name the row itself holds.
    """
    out: List[str] = [normalise(key), key.lower()]
    for label in ("name", "symbol", "formula", "identifier"):
        value = fields.get(label)
        if isinstance(value, str) and value:
            out.append(normalise(value))
    return tuple(dict.fromkeys(a for a in out if a))


# ===========================================================================
# 3.  THE TABLES
# ===========================================================================

def _element_rows() -> Mapping[str, Mapping[str, object]]:
    from ..data_objects import elements
    out: Dict[str, Mapping[str, object]] = {}
    for row in elements.load_element_register():
        out[row.symbol] = {name: getattr(row, name)
                           for name in vars(row)}
    return out


def _molecule_rows() -> Mapping[str, Mapping[str, object]]:
    from ..data_objects import molecules
    out: Dict[str, Mapping[str, object]] = {}
    for row in molecules.load_molecule_register():
        fields: Dict[str, object] = {
            "name": row.name, "formula": row.formula, "charge": row.charge,
            "counts": dict(row.counts),
        }
        for name in MOLECULE_DERIVED:
            fields[name] = getattr(row, name)
        out[row.name] = fields
    return out


def _carrier_rows(objects: Sequence) -> Mapping[str, Mapping[str, object]]:
    """The attributes of every carrier of one register, by carrier name.

    A relation triple is exploded into one field per relation -- the lexicon
    holds ``('velocity', 'derivative_of', 'position')`` as an attribute, and
    the field surface makes ``derivative_of`` the field name and the other
    end the value, because that is what the triple *is*.
    """
    out: Dict[str, Mapping[str, object]] = {}
    for obj in objects:
        fields: Dict[str, object] = dict(obj.attributes)
        triples = fields.get("triples")
        if isinstance(triples, (tuple, list)):
            grouped: Dict[str, List[str]] = {}
            for triple in triples:
                if len(triple) != 3:                  # pragma: no cover
                    continue
                _subject, relation, target = triple
                grouped.setdefault(str(relation), []).append(str(target))
            for relation, targets in grouped.items():
                fields.setdefault(relation, tuple(targets))
        out[obj.name] = fields
    return out


def _lean_rows() -> Mapping[str, Mapping[str, object]]:
    """The Lean rows, read from the stored address book.

    Deliberately the *book* and not the development.  Reading the sources
    live would put every Lean file into the closure of every unit that builds
    a session -- which it did, at a cost of 79 stale units per Lean edit
    (``studies/ITERATION_COST_STUDY.md`` §5e) -- and would buy nothing the
    book does not already hold.  The book is regenerated by
    ``corpus --refresh`` and reported stale by ``corpus --check``.
    """
    from ..reasoning import lean_book
    return lean_book.declaration_rows()


def _python_rows() -> Mapping[str, Mapping[str, object]]:
    """Every top-level function and class of the package, by its own name.

    The same AST walk :func:`glm_universal.reasoning.blockers.python_features`
    performs, kept to top-level definitions: a name defined twice keeps the
    first module in path order and records the second in ``also_in``, so an
    ambiguity is reported rather than silently resolved.
    """
    root = Path(__file__).resolve().parent.parent
    out: Dict[str, Dict[str, object]] = {}
    for path in sorted(root.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):              # pragma: no cover
            continue
        module = path.relative_to(root.parent).with_suffix("")
        dotted = ".".join(module.parts)
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                     ast.ClassDef)):
                continue
            kind = "class" if isinstance(node, ast.ClassDef) else "function"
            existing = out.get(node.name)
            if existing is None:
                out[node.name] = {
                    "module": path.stem, "qualified_module": dotted,
                    "file": str(path.relative_to(root.parent)),
                    "line": node.lineno, "kind": kind, "also_in": (),
                }
            else:
                existing["also_in"] = tuple(existing["also_in"]) + (path.stem,)
    return {name: dict(fields) for name, fields in out.items()}


def _function_rows() -> Mapping[str, Mapping[str, object]]:
    out: Dict[str, Mapping[str, object]] = {}
    for dotted, call in FUNCTION_SURFACES.items():
        returned = call()
        out[dotted] = {str(key): value for key, value in returned.items()}
    return out


#: The domains whose carriers are loaded when no session supplies them.  The
#: spatial register is built by the session itself, so a standalone surface
#: reports seven carrier tables and a session's reports eight; the census
#: says which, rather than pretending they are the same.
_STANDALONE_CARRIERS: Tuple[Tuple[str, str], ...] = (
    ("physics", "physics_objects"),
    ("chemistry", "element_objects"),
    ("molecules", "molecule_objects"),
    ("mathematics", "mathematics_objects"),
    ("lexicon", "semantic_lexicon_carriers"),
    ("harmonics", "harmonic_objects"),
    ("economics", "economics_objects"),
)


def _standalone_carrier(loader: str) -> Sequence:
    from .. import data_objects as do
    if loader == "semantic_lexicon_carriers":
        return do.semantic_lexicon_objects()[0]
    return getattr(do, loader)()


# ===========================================================================
# 4.  THE SURFACE
# ===========================================================================

class FieldSurface:
    """The declared tables, and the two questions they answer.

    Parameters
    ----------
    registers
        Domain name -> loaded carriers, normally the session's own, so a
        query pays nothing to reload a register the session already holds.
        Without it the seven registers that load standalone are loaded here.
    """

    def __init__(self, registers: Optional[Mapping[str, Sequence]] = None):
        self._registers = dict(registers) if registers is not None else None
        self._tables: Optional[Tuple[FieldTable, ...]] = None

    # -- the tables, in the declared priority order ----------------------

    def tables(self) -> Tuple[FieldTable, ...]:
        """Every declared table, in the order a lookup consults them."""
        if self._tables is not None:
            return self._tables
        out: List[FieldTable] = [
            FieldTable(
                "element", "source",
                "the 118 element rows the chemistry register is built from",
                _element_rows,
                "glm_universal.data_objects.elements.load_element_register"),
            FieldTable(
                "molecule", "source",
                "the 51 molecule rows, with the register's declared derived "
                "properties beside the two fields it stores",
                _molecule_rows,
                "glm_universal.data_objects.molecules.load_molecule_register",
                derived=MOLECULE_DERIVED),
        ]
        if self._registers is None:
            pairs = [(domain, lambda loader=loader: _standalone_carrier(loader))
                     for domain, loader in _STANDALONE_CARRIERS]
        else:
            pairs = [(domain, lambda objs=self._registers[domain]: objs)
                     for domain in sorted(self._registers)]
        for domain, load in pairs:
            out.append(FieldTable(
                f"carrier:{domain}", "carrier",
                f"the attributes every carrier of the {domain} register "
                f"keeps",
                lambda load=load: _carrier_rows(load()),
                f"glm_universal.runtime.session.GeometricSession"
                f".register({domain!r})"))
        out.append(FieldTable(
            "lean", "address",
            "the Lean address book: one row per declaration of the "
            "development",
            _lean_rows,
            "glm_universal.reasoning.lean_book.declaration_rows"))
        out.append(FieldTable(
            "python", "code",
            "the package's own top-level functions and classes, read by an "
            "AST walk",
            _python_rows,
            "glm_universal.runtime.fields._python_rows"))
        out.append(FieldTable(
            "function", "function",
            "the declared zero-argument functions whose returned mapping is "
            "addressable by key",
            _function_rows,
            "glm_universal.runtime.fields.FUNCTION_SURFACES"))
        self._tables = tuple(out)
        return self._tables

    def table_by_name(self, name: str) -> FieldTable:
        """One table by its declared name."""
        for table in self.tables():
            if table.name == name:
                return table
        raise FieldError(f"no table named {name!r}; the declared tables are "
                         f"{', '.join(t.name for t in self.tables())}")

    # -- resolution ------------------------------------------------------

    def matches(self, row: str) -> Tuple[Tuple[FieldTable, str], ...]:
        """Every ``(table, row key)`` the surface form resolves to.

        In table priority order, so the first element is what a lookup that
        does not name a field will use.
        """
        wanted = normalise(row)
        out: List[Tuple[FieldTable, str]] = []
        for table in self.tables():
            key = table.aliases().get(wanted)
            if key is not None:
                out.append((table, key))
        return tuple(out)

    def near_rows(self, row: str, limit: int = 5) -> Tuple[str, ...]:
        """Row names near a surface form, by exact integer edit distance."""
        from .parser import levenshtein
        wanted = normalise(row)
        scored: List[Tuple[int, str, str]] = []
        for table in self.tables():
            for alias, key in table.aliases().items():
                scored.append((levenshtein(wanted, alias), table.name, key))
        scored.sort()
        seen: List[str] = []
        for _distance, table_name, key in scored:
            label = f"{key} ({table_name})"
            if label not in seen:
                seen.append(label)
            if len(seen) >= limit:
                break
        return tuple(seen)

    # -- the two questions ------------------------------------------------

    def fields(self, row: str) -> RowFields:
        """Every field name the row answers to, across the tables holding it.

        This is the shape that asks *what does this hold?* without naming the
        answer -- which is what makes it a fair translation of a question
        about what a function returns.
        """
        found = self.matches(row)
        if not found:
            raise FieldError(
                f"no row named {row!r}; nearest rows: "
                f"{', '.join(self.near_rows(row)) or 'none'}")
        names: List[str] = []
        tables: List[str] = []
        key = found[0][1]
        for table, row_key in found:
            tables.append(table.name)
            for name in table.rows()[row_key]:
                if name not in names:
                    names.append(name)
        return RowFields(row=key, tables=tuple(tables),
                         names=tuple(sorted(names)))

    def field(self, name: str, row: str) -> FieldValue:
        """One field of one row, from the first table that holds both.

        Refuses, with the reason, when the row is unknown, when no table
        holding the row holds the field, or when the row records the field as
        missing -- the element register's missingness mask is a fact about
        the data, and answering ``none`` as though it were a value would hide
        it.
        """
        wanted = name.strip()
        surface_form = normalise(row)
        held = False
        for table in self.tables():
            row_key = table.aliases().get(surface_form)
            if row_key is None:
                continue
            held = True
            fields = table.rows()[row_key]
            if wanted not in fields:
                continue
            value = fields[wanted]
            if value is None:
                raise FieldError(
                    f"{table.name} holds the row {row_key!r} and records "
                    f"{wanted!r} as missing for it; the surface refuses a "
                    f"missing field rather than answering with a blank")
            return FieldValue(
                table=table.name, table_kind=table.kind, row=row_key,
                field=wanted, value=value, rendered=render_value(value),
                provenance=table.provenance,
                derived=wanted in table.derived,
                rule=table.derived.get(wanted, ""))
        if not held:
            raise FieldError(
                f"no row named {row!r}; nearest rows: "
                f"{', '.join(self.near_rows(row)) or 'none'}")
        holds = self.fields(row)
        raise FieldError(
            f"the row {holds.row!r} is held by "
            f"{', '.join(holds.tables)} and has no field {wanted!r}; "
            f"it answers to: {', '.join(holds.names)}")

    # -- the census, for the report and the figures -----------------------

    def census(self) -> Dict[str, object]:
        """How much is addressable: tables, rows and distinct field names.

        Every table is built, so this is the expensive call of the module and
        the only one that is: an ordinary query builds one table.
        """
        rows_total = 0
        field_names: Dict[str, int] = {}
        per_table: List[Dict[str, object]] = []
        for table in self.tables():
            rows = table.rows()
            names: Dict[str, int] = {}
            for fields in rows.values():
                for name in fields:
                    names[name] = names.get(name, 0) + 1
                    field_names[name] = field_names.get(name, 0) + 1
            rows_total += len(rows)
            per_table.append({
                "table": table.name, "kind": table.kind,
                "rows": len(rows), "fields": len(names),
                "gloss": table.gloss, "provenance": table.provenance,
                "derived": tuple(sorted(table.derived)),
            })
        return {
            "tables": len(per_table),
            "rows": rows_total,
            "distinct_fields": len(field_names),
            "addressable_pairs": _pairs(self),
            "per_table": tuple(per_table),
        }


def _pairs(self: FieldSurface) -> int:
    """The number of ``(row, field)`` pairs the surface addresses."""
    total = 0
    for table in self.tables():
        for fields in table.rows().values():
            total += len(fields)
    return total


def surface(registers: Optional[Mapping[str, Sequence]] = None
            ) -> FieldSurface:
    """A field surface over ``registers``, or over the standalone loaders."""
    return FieldSurface(registers)
