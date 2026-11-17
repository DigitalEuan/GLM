"""``glm_universal.wheels.quantity_graph`` -- the typed quantity graph of the
formula wheels.

*Created 17 November 2026 (the cent-wheels round; ``WHITEBOARD.md`` item 2).*

What this module is
-------------------
A vertex is a **typed quantity**: a pair ``(wheel, name)`` -- ``("W5",
"mass")``, ``("W36", "pair_energy")``.  The same *name* in two wheels is two
vertices until an edge declares them one measurand: a **junction** (``W5 mass
= W12 mass``).  A **non-identity** forbids the identification even where the
names coincide (``W3 energy`` against ``W14 energy``: stored charge against
stored current).  The edges are the absorbed item's own
(``source_material/ToDo/cent_compiler_v12/wheels/W*.json``, ``junctions`` and
``non_identities``), transcribed here because the package never reads
``source_material/`` at run time (D20).

Contracting the edges gives the **identity classes**: the sets of typed
quantities a cross-wheel derivation may eliminate against one another.  This
is the graph the licensing needs, and nothing more: the algebra stays in
:mod:`glm_universal.engineering.union` and
:mod:`glm_universal.engineering.domains`, which already split every shared
name per wheel (``energy@W5``) and join only across a declared edge.

What it is not
--------------
The contraction is a quotient of the free abelian group on the typed
quantities by the subgroup the edges generate -- a **graph contraction**, or a
pushout of free abelian groups.  It is not an embedding into the Leech lattice
``Lambda_24``: nearest-neighbour edges on 24 vertices generate the root
lattice ``A_23``, whereas ``Lambda_24`` needs a Golay-shaped incidence (the
Miracle Octad Generator is one presentation of that code), which the supplied
junctions do not have.  The 24 absorbed wheels do index 24 coordinates, so the
resonance is real, but the faithful object here is the quotient, not the
lattice.

Audit
-----
The supplied table is kept as supplied, with one documented repair: a
non-identity record names the quantity in **one** wheel only, so five guards
were vacuous as transcribed.  Four are repaired by reading the other-wheel
name out of the reason (:data:`REPAIRS`): ``W36 pair_energy`` against ``W5
energy``, ``W39 magnetomotive_force`` against ``W1 current``, ``W41
temperature_difference`` against ``W8 temperature`` and ``W42
moment_of_inertia_of_section`` against ``W4 moment_of_inertia``.  The fifth,
``W37 relaxation_time`` against ``W4``, has no other-wheel name to read and
stays vacuous; :func:`audit` reports it.

Two copies of the junction table exist in the item.  The per-wheel
``junctions`` blocks hold 43 directional entries -- 29 distinct pairs -- and
that stale copy was transcribed first.  ``wheels/index.json``, which the
item's own loader and ``axiom_graph`` use, declares **59** distinct pairs; the
thirty extra are the W20-W35 registry edges (``W1 voltage`` against ``W20
stress``, ``W6 pressure`` against ``W32``/``W34``, ``W8 temperature`` against
``W22``/``W26``/``W35``, the W11-W27 cosmology edges, ...).  This module now
follows ``index.json``.

A declared junction is not automatically an identity.  The full table also
joins pairs whose SI7 vectors differ -- ``W1 voltage`` against ``W20 stress``,
``W12 area`` against ``W34 pipe_radius`` -- which are declared cross-domain
analogies, not one measurand.  :func:`edges` keeps only the dimensionally
equal pairs; :func:`dimension_gaps` reports the rest, and
:func:`may_identify` refuses them.  Seven junctions still name a quantity
that wheel does not hold (``W4 energy``, ``W32 viscosity``, ...); an unknown
endpoint is dropped from the graph but stays in the audit.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, FrozenSet, List, Mapping, Optional, Sequence, Tuple

__all__ = [
    "Endpoint", "Junction", "NonIdentity", "JUNCTIONS", "NON_IDENTITIES",
    "quantities_by_wheel", "audit", "edges", "classes", "wheels_of",
    "may_identify", "dimension_gaps", "BRIDGES", "ALL_JUNCTIONS", "graph_report",
]

#: A typed quantity: ``(wheel id, quantity name)``.
Endpoint = Tuple[str, str]
#: An undirected edge between two typed quantities.
Edge = FrozenSet[Endpoint]


@dataclass(frozen=True)
class Junction:
    """Two typed quantities declared one measurand, and why."""

    a: Endpoint
    b: Endpoint
    reason: str


@dataclass(frozen=True)
class NonIdentity:
    """Two typed quantities whose names coincide but which must stay apart."""

    a: Endpoint
    b: Endpoint
    reason: str


#: The absorbed item's ``wheels/index.json`` ``junctions``, verbatim:
#: ``(wheel, name, other_wheel, name_in_other_wheel, reason)``.
_JUNCTIONS = (
    ('W5', 'velocity', 'W11', 'velocity', "moving body's velocity = uniform-motion velocity"),
    ('W5', 'mass', 'W12', 'mass', 'the body whose density is read is the body that moves'),
    ('W6', 'area', 'W12', 'area', "the flow's cross-section = swept-prism cross-section"),
    ('W11', 'length', 'W12', 'length', 'the length the fluid moves = length of the swept prism'),
    ('W9', 'frequency', 'W13', 'frequency', "the oscillator's frequency = the wave's frequency"),
    ('W5', 'mass', 'W13', 'mass', 'the oscillating body = the dynamic body'),
    ('W3', 'capacitance', 'W14', 'capacitance', "the LC circuit's capacitor = the electrostatics capacitor"),
    ('W1', 'current', 'W14', 'current', "the inductor's current = the circuit's current"),
    ('W1', 'current', 'W15', 'current', "the charge and energy are carried by the circuit's current"),
    ('W1', 'power', 'W15', 'power', "the energy is delivered by the circuit's power"),
    ('W3', 'charge', 'W15', 'charge', 'the charge moved = the charge stored'),
    ('W9', 'wave_speed', 'W10', 'speed_of_light', "a photon's wave_speed = speed_of_light (light is the wave)"),
    ('W9', 'frequency', 'W10', 'frequency', "a photon's frequency = the wave's frequency (a photon is a wave)"),
    ('W20', 'stress', 'W1', 'voltage', 'piezoelectric stress-voltage coupling'),
    ('W20', 'strain', 'W1', 'charge', 'piezoelectric strain-charge coupling'),
    ('W22', 'temperature', 'W8', 'temperature', 'reaction temperature is thermodynamic temperature'),
    ('W23', 'charge', 'W1', 'charge', 'electrochemical charge is electrical charge'),
    ('W23', 'charge', 'W15', 'charge', 'Faraday charge = circuit charge'),
    ('W23', 'time', 'W15', 'time', 'electrolysis time = charging time'),
    ('W24', 'current', 'W1', 'current', 'diode current is circuit current'),
    ('W24', 'thermal_voltage', 'W1', 'voltage', 'thermal voltage is a voltage'),
    ('W25', 'magnetic_field', 'W16', 'magnetic_field', 'plasma B-field is the same B-field'),
    ('W28', 'magnetic_flux', 'W16', 'flux', 'Josephson flux is magnetic flux'),
    ('W28', 'time', 'W15', 'time', 'Josephson time is circuit time'),
    ('W29', 'magnetic_field', 'W25', 'magnetic_field', 'spin B-field is plasma B-field'),
    ('W32', 'pressure', 'W6', 'pressure', 'capillary pressure is fluid pressure'),
    ('W32', 'viscosity', 'W6', 'velocity', 'capillary viscosity relates to flow velocity'),
    ('W33', 'thermal_conductivity', 'W8', 'thermal_conductivity', 'heat transfer conductivity is thermal conductivity'),
    ('W34', 'volume_flow_rate', 'W6', 'volume_flow_rate', 'blood flow is volume flow'),
    ('W34', 'pressure', 'W6', 'pressure', 'blood pressure is fluid pressure'),
    ('W34', 'pipe_radius', 'W12', 'area', 'vessel radius relates to cross-sectional area'),
    ('W35', 'temperature', 'W8', 'temperature', 'Nernst temperature is thermodynamic temperature'),
    ('W35', 'ion_concentration', 'W12', 'amount', 'ion concentration relates to amount of substance'),
    ('W36', 'pair_penetration', 'W21', 'stress', "the crack engine's mean stress is the mean positive SAT penetration"),
    ('W36', 'pair_energy', 'W4', 'energy', 'cluster elastic energy = sum of squared penetrations'),
    ('W36', 'pair_penetration', 'W37', 'stress', 'the settling engine reads the SAT penetration as its elastic stress input'),
    ('W37', 'modulus', 'W20', 'youngs_modulus', "the piezo engine's stiffness feeds the settle's relaxation time"),
    ('W38', 'input_torque', 'W4', 'torque', 'gearbox input torque is the shaft torque'),
    ('W38', 'input_angular_velocity', 'W4', 'angular_velocity', 'gearbox input speed is the shaft speed'),
    ('W38', 'input_power', 'W5', 'power', 'mechanical power is the translated body power'),
    ('W39', 'magnetic_flux', 'W16', 'flux', 'magnetic-circuit flux is induction flux'),
    ('W40', 'voltage', 'W1', 'voltage', 'piezoelectric voltage is a circuit voltage'),
    ('W40', 'stress', 'W20', 'stress', 'the piezo stack stress is the continuum stress'),
    ('W40', 'force', 'W5', 'force', 'the piezo stack force is the dynamic force'),
    ('W41', 'voltage', 'W1', 'voltage', 'thermoelectric voltage is a circuit voltage'),
    ('W41', 'temperature', 'W8', 'temperature', 'the thermoelectric junction temperature is thermodynamic temperature'),
    ('W41', 'heat_rate', 'W15', 'power', 'Peltier heat rate is the power channel'),
    ('W26', 'mass', 'W17', 'source_mass', 'stellar mass is the gravitational source mass'),
    ('W26', 'gravitational_constant', 'W17', 'gravitational_constant', 'the same gravitational constant'),
    ('W26', 'temperature', 'W8', 'temperature', 'photospheric temperature is thermodynamic temperature'),
    ('W26', 'luminosity', 'W15', 'power', 'bolometric luminosity is radiant power in the power channel'),
    ('W27', 'distance', 'W11', 'length', 'cosmological distance is a length in the uniform-motion channel'),
    ('W27', 'recession_velocity', 'W11', 'velocity', 'cosmological recession speed is a velocity'),
    ('W27', 'hubble_time', 'W11', 'time', 'the Hubble time is a time interval'),
    ('W27', 'critical_density', 'W12', 'density', 'critical density is a mass density'),
    ('W27', 'speed_of_light', 'W19', 'speed_of_light', 'the same speed of light'),
    ('W27', 'gravitational_constant', 'W17', 'gravitational_constant', 'the same gravitational constant'),
    ('W21', 'youngs_modulus', 'W42', 'youngs_modulus', 'the same elastic modulus governs fracture and buckling'),
    ('W5', 'force', 'W42', 'applied_load', 'a column load is a force on a mechanical junction'),
)

#: The absorbed item's ``non_identities``, with the other-wheel name made
#: explicit: ``(wheel, name, other_wheel, name_in_other_wheel, reason)``.
#: The four repairs are in :data:`REPAIRS`.
_NON_IDENTITIES = (
    ('W11', 'time', 'W15', 'time', 'a travel time against a charging time'),
    ('W13', 'angular_frequency', 'W14', 'angular_frequency', 'a mechanical oscillator against an electrical one; identifying them would give spring_constant = mass / (inductance * capacitance)'),
    ('W13', 'angle', 'W9', 'angle', "Phase 158 split: the oscillator's angle convention vs the wave's angle reference; only frequency is joined"),
    ('W14', 'angular_frequency', 'W13', 'angular_frequency', 'a mechanical oscillator against an electrical one; identifying them would give spring_constant = mass / (inductance * capacitance)'),
    ('W14', 'energy', 'W3', 'energy', "the capacitor's stored energy against the inductor's"),
    ('W15', 'energy', 'W3', 'energy', 'energy stored in a capacitor against energy delivered over a time'),
    ('W15', 'time', 'W11', 'time', 'a travel time against a charging time'),
    ('W3', 'energy', 'W14', 'energy', "the capacitor's stored energy against the inductor's"),
    ('W3', 'energy', 'W15', 'energy', 'energy stored in a capacitor against energy delivered over a time'),
    ('W36', 'pair_energy', 'W5', 'energy', "the substrate's pair_energy is L2-squared penetration, not the flywheel's kinetic energy; only the relaxation channel joins"),
    ('W37', 'relaxation_time', 'W4', 'relaxation_time', "the flywheel's timescale is inertial (I/E), not viscous (eta/E); only the damped swing borrows the channel"),
    ('W39', 'magnetomotive_force', 'W1', 'current', 'ampere-turns has the dimension of current but is not current; identifying them would erase the turns count'),
    ('W41', 'temperature_difference', 'W8', 'temperature', 'a temperature difference and an absolute temperature share a dimension but not a reference point'),
    ('W42', 'moment_of_inertia_of_section', 'W4', 'moment_of_inertia', "a section's second moment of area is not a rotor's mass moment of inertia; identifying them would give a column the dynamics of a flywheel"),
    ('W9', 'angle', 'W13', 'angle', "Phase 158 split: the oscillator's angle convention vs the wave's angle reference; only frequency is joined"),
)

#: The four non-identities repaired from the supplied one-name form, with the
#: names read out of the reason: ``(wheel, supplied_name, repaired_name,
#: supplied_other_wheel, repaired_other_name)``.  Only the first changes its
#: own wheel's name (``W36`` holds ``pair_energy``, not ``energy``).
REPAIRS: Tuple[Tuple[str, str, str, str, str], ...] = (
    ('W36', 'energy', 'pair_energy', 'W5', 'energy'),
    ('W39', 'magnetomotive_force', 'magnetomotive_force', 'W1', 'current'),
    ('W41', 'temperature_difference', 'temperature_difference', 'W8', 'temperature'),
    ('W42', 'moment_of_inertia_of_section', 'moment_of_inertia_of_section', 'W4', 'moment_of_inertia'),
)

JUNCTIONS: Tuple[Junction, ...] = tuple(
    Junction((a, na), (b, nb), reason) for a, na, b, nb, reason in _JUNCTIONS)

#: The stress class repaired.  W20, W21, W37 and W40 all hold ``stress`` with
#: the same SI7 dimensions (M L^-1 T^-2), but the supplied table joins them
#: only through W36's dimensionless ``pair_penetration`` -- a dimension gap.
#: Two same-name bridges make the dimensioned class one variable directly.
BRIDGES: Tuple[Junction, ...] = (
    Junction(("W20", "stress"), ("W21", "stress"),
             "continuum and crack stress are one measurand"),
    Junction(("W20", "stress"), ("W37", "stress"),
             "continuum and viscous stress are one measurand"),
)

#: The supplied junctions and the repaired bridges.
ALL_JUNCTIONS: Tuple[Junction, ...] = JUNCTIONS + BRIDGES

NON_IDENTITIES: Tuple[NonIdentity, ...] = tuple(
    NonIdentity((a, na), (b, nb), reason) for a, na, b, nb, reason in _NON_IDENTITIES)


# ===========================================================================
# 1.  THE VERTICES
# ===========================================================================

def quantities_by_wheel() -> Dict[str, FrozenSet[str]]:
    """Every absorbed wheel's quantity names, the fifteen and the twenty-four
    cent wheels together.  Imported here, never at package import, so the
    graph cannot close an import cycle."""
    from ..engineering.wheels import wheel_quantities
    from . import ALL_WHEELS
    from .cent_wheels import CENT_WHEELS

    out: Dict[str, FrozenSet[str]] = {}
    for w in tuple(ALL_WHEELS) + tuple(CENT_WHEELS):
        out[w.id] = frozenset(wheel_quantities(w))
    return out


def _edge(a: Endpoint, b: Endpoint) -> Edge:
    return frozenset((a, b))


def _unknown_endpoints(junctions: Sequence[Junction],
                       non_identities: Sequence[NonIdentity],
                       quantities: Mapping[str, FrozenSet[str]]
                       ) -> List[Tuple[str, Endpoint]]:
    out: List[Tuple[str, Endpoint]] = []
    for pair in [(j.a, j.b) for j in junctions] + \
                [(n.a, n.b) for n in non_identities]:
        for e in pair:
            if e[0] not in quantities:
                out.append((f"no absorbed wheel {e[0]}", e))
            elif e[1] not in quantities[e[0]]:
                out.append((f"no quantity {e[1]!r} in {e[0]}", e))
    return out


def audit(junctions: Sequence[Junction] = JUNCTIONS,
          non_identities: Sequence[NonIdentity] = NON_IDENTITIES) -> Dict[str, object]:
    """What the supplied table cannot be used for, measured.

    ``unknown_endpoints`` -- an edge naming a wheel or a quantity that wheel
    does not hold; ``one_way`` -- a junction whose reverse is not declared
    (the graph symmetrises it, but the declaration is asymmetric);
    ``contradictions`` -- the same edge declared both a junction and a
    non-identity; ``duplicates`` -- the same direction declared twice (a
    mirror pair, declared both ways, is not a duplicate).
    """
    quantities = quantities_by_wheel()
    unknown = _unknown_endpoints(junctions, non_identities, quantities)
    directed = {(j.a, j.b) for j in junctions}
    one_way = [j for j in junctions if (j.b, j.a) not in directed]
    junction_edges = [_edge(j.a, j.b) for j in junctions]
    blocked = {_edge(n.a, n.b) for n in non_identities}
    contradictions = [(sorted(e), next(n.reason for n in non_identities
                                       if _edge(n.a, n.b) == e))
                      for e in junction_edges if e in blocked]
    seen: Dict[Tuple[Endpoint, Endpoint], int] = {}
    for j in junctions:
        seen[(j.a, j.b)] = seen.get((j.a, j.b), 0) + 1
    duplicates = [[list(a), list(b)] for (a, b), n in seen.items() if n > 1]

    def known(e: Endpoint) -> bool:
        return e[0] in quantities and e[1] in quantities[e[0]]

    dropped = [j for j in junctions if not (known(j.a) and known(j.b))]
    vacuous = [n for n in non_identities if not (known(n.a) and known(n.b))]
    return {"unknown_endpoints": unknown, "one_way": one_way,
            "contradictions": contradictions, "duplicates": duplicates,
            "dropped_junctions": dropped,
            "vacuous_non_identities": vacuous, "bridges": BRIDGES}


# ===========================================================================
# 2.  THE EDGES AND THE IDENTITY CLASSES
# ===========================================================================

def _edge_set(junctions: Sequence[Junction],
              non_identities: Sequence[NonIdentity]) -> Tuple[Edge, ...]:
    """The declared edges whose endpoints exist and which no non-identity
    blocks, before the dimension check."""
    quantities = quantities_by_wheel()
    blocked = {_edge(n.a, n.b) for n in non_identities}
    out: List[Edge] = []
    for j in junctions:
        if any(e[0] not in quantities or e[1] not in quantities[e[0]]
               for e in (j.a, j.b)):
            continue
        e = _edge(j.a, j.b)
        if e in blocked or e in out:
            continue
        out.append(e)
    return tuple(out)


def edges(junctions: Sequence[Junction] = ALL_JUNCTIONS,
          non_identities: Sequence[NonIdentity] = NON_IDENTITIES) -> Tuple[Edge, ...]:
    """The sound junction edges: both endpoints exist, no non-identity blocks
    the pair, and the two endpoints have the same SI7 dimension.  Undirected,
    so a one-way declaration joins its two vertices like any other."""
    gaps = {_edge(a, b) for a, b, _, _ in dimension_gaps()}
    return tuple(e for e in _edge_set(junctions, non_identities)
                 if e not in gaps)


def classes(junctions: Sequence[Junction] = ALL_JUNCTIONS,
            non_identities: Sequence[NonIdentity] = NON_IDENTITIES
            ) -> Dict[Endpoint, Tuple[Endpoint, ...]]:
    """``(wheel, name) -> the typed quantities it is one variable with``,
    by union-find over :func:`edges` (a singleton when nothing joins it)."""
    quantities = quantities_by_wheel()
    nodes = [(w, q) for w, names in quantities.items() for q in names]
    parent: Dict[Endpoint, Endpoint] = {n: n for n in nodes}

    def find(x: Endpoint) -> Endpoint:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for e in edges(junctions, non_identities):
        a, b = tuple(e)
        if a not in parent or b not in parent:
            continue
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    groups: Dict[Endpoint, List[Endpoint]] = {}
    for n in nodes:
        groups.setdefault(find(n), []).append(n)
    order = {w: i for i, w in enumerate(quantities)}
    return {n: tuple(sorted(groups[find(n)], key=lambda x: (order.get(x[0], 99), x[0], x[1])))
            for n in nodes}


def wheels_of(endpoint: Endpoint,
              table: Optional[Mapping[Endpoint, Tuple[Endpoint, ...]]] = None
              ) -> Tuple[str, ...]:
    """The wheels whose copy of a quantity is one variable with ``endpoint``'s."""
    table = classes() if table is None else table
    return tuple(dict.fromkeys(w for w, _ in table.get(endpoint, (endpoint,))))


def may_identify(a: Endpoint, b: Endpoint) -> Optional[str]:
    """``None`` when ``a`` and ``b`` may be one variable in a derivation, else
    the reason they may not.

    The same wheel may always identify its own name; across wheels a declared
    junction is required, and a declared non-identity outranks it.  The
    relation is transitive: two quantities in one identity class are one
    variable even when no single junction names the pair.
    """
    quantities = quantities_by_wheel()
    e = _edge(a, b)
    #  A declared non-identity outranks a missing endpoint: a guard whose
    #  other wheel does not carry the name is vacuous, and says so.
    for n in NON_IDENTITIES:
        if _edge(n.a, n.b) == e:
            missing = next((x for x in (n.a, n.b)
                            if x[0] not in quantities
                            or x[1] not in quantities[x[0]]), None)
            if missing is not None:
                return (f"declared non-identity, vacuous as transcribed: "
                        f"{missing[0]} holds no {missing[1]!r}")
            return f"declared non-identity: {n.reason}"
    for x in (a, b):
        if x[0] not in quantities:
            return f"{x[0]} is not an absorbed wheel"
        if x[1] not in quantities[x[0]]:
            return f"{x[0]} holds no {x[1]!r}"
    if a == b or a[0] == b[0]:
        return None
    gap = next((g for g in dimension_gaps() if _edge(g[0], g[1]) == e), None)
    if gap is not None:
        return (f"declared junction, dimension gap: {gap[0][0]} {gap[0][1]!r} "
                f"is not {gap[1][0]} {gap[1][1]!r}")
    table = classes()
    group = table.get(a)
    if group is not None and group == table.get(b) and len({w for w, _ in group}) > 1:
        return None
    return "no declared junction"


# ===========================================================================
# 3.  THE REPORT
# ===========================================================================

def _dimension_tables() -> Dict[str, Dict[str, tuple]]:
    """Every absorbed wheel's table over the eight axes: the cent item's own
    (W16-W42), the five domain tables (W11-W15) and the reference registry
    (W1-W10, keyed by quantity name)."""
    from ..engineering.wheels import REFERENCE_DIMENSIONS, wheel_quantities
    from . import ALL_WHEELS
    from .cent_wheels import CENT_TABLES, DOMAIN_TABLES

    tables: Dict[str, Dict[str, tuple]] = {}
    tables.update(CENT_TABLES)
    tables.update(DOMAIN_TABLES)
    for w in ALL_WHEELS:
        if w.id not in tables:
            tables[w.id] = {q: REFERENCE_DIMENSIONS[q]
                            for q in wheel_quantities(w)
                            if q in REFERENCE_DIMENSIONS}
    return tables


@lru_cache(maxsize=1)
def dimension_gaps() -> Tuple[Tuple[Endpoint, Endpoint, tuple, tuple], ...]:
    """Junction edges whose two endpoints have different SI7 dimensions.

    Such an identification is algebraically possible and physically
    impossible: the item joins W36's dimensionless ``pair_penetration`` to
    W21's and W37's ``stress`` (a pressure), W1's ``voltage`` to W20's
    ``stress``, and W12's ``area`` to W34's ``pipe_radius``.  This is
    enforced: :func:`edges` excludes these edges and :func:`may_identify`
    reports the gap, so a declared analogy never becomes an identity.
    """
    from .cent_wheels import SI7_AXES

    tables = _dimension_tables()
    out = []
    for e in _edge_set(ALL_JUNCTIONS, NON_IDENTITIES):
        a, b = tuple(e)
        da = tables.get(a[0], {}).get(a[1])
        db = tables.get(b[0], {}).get(b[1])
        if da is None or db is None:
            continue
        if tuple(da[:SI7_AXES]) != tuple(db[:SI7_AXES]):
            out.append((a, b, da, db))
    return tuple(out)


def graph_report() -> Dict[str, object]:
    """The graph's size, what the audit could not use, and every quantity
    joined across more than one wheel."""
    a = audit()
    table = classes()
    joined: Dict[str, List[str]] = {}
    for (wheel, name), group in table.items():
        if len({w for w, _ in group}) > 1:
            joined[f"{wheel}:{name}"] = [f"{w}:{q}" for w, q in group]
    return {
        "wheels": len(quantities_by_wheel()),
        "junctions": len(JUNCTIONS),
        "non_identities": len(NON_IDENTITIES),
        "sound_edges": len(edges()),
        "bridges": len(BRIDGES),
        "unknown_endpoints": a["unknown_endpoints"],
        "one_way": [[list(j.a), list(j.b)] for j in a["one_way"]],
        "contradictions": a["contradictions"],
        "duplicates": a["duplicates"],
        "dropped_junctions": [[list(j.a), list(j.b)] for j in a["dropped_junctions"]],
        "vacuous_non_identities": [[list(n.a), list(n.b)]
                                   for n in a["vacuous_non_identities"]],
        "dimension_gaps": [[list(x), list(y)]
                           for x, y, _, _ in dimension_gaps()],
        "joined_quantities": joined,
    }
