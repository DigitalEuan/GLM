"""``glm_universal.wheels.cent_union`` -- derivation across the cent family
and the fifteen registry wheels, over the typed quantity graph.

*Created 17 November 2026 (the cent-wheels round; ``WHITEBOARD.md`` item 2).*

What this module is
-------------------
:mod:`glm_universal.wheels.quantity_graph` gives the graph: typed quantities
as vertices, declared junctions as edges, declared non-identities as refused
edges.  This module feeds **the graph's identity classes** into the existing
split system of :mod:`glm_universal.engineering.domains`, over all 39 wheels
(W1-W15 and the 24 absorbed cent wheels), and measures what the licensed
union refuses that the naive union derives.

Three junction tables meet here
-------------------------------
The fifteen-wheel system already has two: Phase 66's five junctions
(:mod:`glm_universal.wheels.junctions.phase66`) and the ten domain junctions
(:mod:`glm_universal.wheels.junctions.domain`).  The absorbed item supplies a
third, which **duplicates most of the first two** and adds the cross-family
edges the cent wheels need (``W39 magnetic_flux = W16 flux``, ``W41 heat_rate
= W15 power``).  :data:`JUNCTIONS` merges them with per-pair de-duplication,
so a name declared by two tables is joined once.

The third table also joins **different names** (``W36 pair_penetration = W21
stress``), which the fifteen-wheel split system could not express.  Those are
passed as :data:`PAIRINGS`, explicit endpoint pairs, and the split system
labels a whole class by one canonical name.

The energy family
-----------------
:func:`energy_family_report` asks every two-input question over the names of
the energy-bearing wheels (W3, W5, W8, W14, W15, W36), keeps the naive
derivations that use at least two of them, and reports how many the licensed
union answers and how many it refuses.  The four energy non-identities
(capacitor against inductor, capacitor against delivered, kinetic against
stored heat, SAT pair energy against kinetic energy) are the ones that make
the difference.
"""

from __future__ import annotations

from typing import Dict, Sequence, Tuple

from ..engineering import domains as dmn
from ..engineering import wheels as wh
from . import ALL_WHEELS, quantity_graph as qg
from .cent_wheels import CENT_WHEELS, relation_vector_q
from .junctions import domain as _dj
from .junctions import phase66 as _p66

__all__ = [
    "WHEELS", "JUNCTIONS", "PAIRINGS", "NON_IDENTITIES", "ENERGY_WHEELS",
    "ENERGY_QUESTIONS", "split_system", "derive_across", "energy_family_report",
]

#: All 39 absorbed wheels: the fifteen registry wheels and the 24 cent wheels.
WHEELS = tuple(ALL_WHEELS) + tuple(CENT_WHEELS)

#: The three supplied tables merged, per pair de-duplicated.  The cent table
#: repeats most of the first two; the merge is what makes the third table
#: usable instead of a second, conflicting source.
JUNCTIONS: Dict[Tuple[str, str], Tuple[str, ...]] = {}
for _table in (_p66.JUNCTIONS, _dj.JUNCTIONS):
    for _pair, _names in _table.items():
        JUNCTIONS[_pair] = tuple(dict.fromkeys(JUNCTIONS.get(_pair, ()) + tuple(_names)))

#: The graph's sound edges as explicit endpoint pairs, so a junction between
#: differently named quantities (``pair_penetration``/``stress``) joins.
PAIRINGS: Tuple[Tuple[Tuple[str, str], Tuple[str, str]], ...] = tuple(
    tuple(sorted(edge)) for edge in qg.edges())

#: The declared non-identities, keyed by wheel pair, for the refusal message.
NON_IDENTITIES: Dict[Tuple[str, str], str] = {}
for _n in qg.NON_IDENTITIES:
    NON_IDENTITIES[(_n.a[0], _n.b[0])] = _n.reason
for _pair, _why in _p66.NON_IDENTITIES.items():
    NON_IDENTITIES.setdefault(_pair, _why)
for _pair, _why in _dj.NON_IDENTITIES.items():
    NON_IDENTITIES.setdefault(_pair, _why)

#: The wheels whose shared name ``energy`` is a declared non-identity.
ENERGY_WHEELS: Tuple[str, ...] = ("W3", "W5", "W8", "W14", "W15", "W36")

#: The pre-registered energy-family questions: a target and two inputs that
#: one energy wheel answers and another either answers differently (the
#: factor-2 capacitor/delivered pair) or cannot answer at all.
ENERGY_QUESTIONS: Tuple[Tuple[str, Tuple[str, str]], ...] = (
    ("energy", ("charge", "voltage")),        # W3 (1/2) against W15 (1)
    ("energy", ("capacitance", "voltage")),   # W3's capacitor
    ("energy", ("inductance", "current")),    # W14's inductor
    ("energy", ("mass", "velocity")),         # W5's kinetic energy
    ("energy", ("mass", "temperature")),      # W8's stored heat
    ("energy", ("power", "time")),            # W15 against W4/W5 power
    ("power", ("energy", "time")),            # W15's power
    ("power", ("force", "velocity")),         # W5's mechanical power
)


def split_system(split: bool = True):
    """The 39-wheel split system over the merged table and the graph's
    pairings; ``split=False`` is the naive union.  The rational-power engine
    reads the cent wheels' fractional exponents (``W36``); the fifteen
    wheels read the same there."""
    return dmn.split_system(JUNCTIONS, split, WHEELS,
                            PAIRINGS if split else (), relation_vector_q)


def derive_across(target: str, inputs: Sequence[str]):
    """Answer *derive target from inputs across all 39 wheels*, or refuse with
    the naive formula and the identification it would need."""
    return dmn.derive_domains(target, tuple(inputs), junctions=JUNCTIONS,
                              wheels=WHEELS, non_identities=NON_IDENTITIES,
                              pairings=PAIRINGS, relation=relation_vector_q)


def energy_family_report() -> Dict[str, object]:
    """The pre-registered energy-family questions, naive against licensed.

    The naive union merges every ``energy`` into one variable, so it either
    gives a formula no single wheel gives or, more often, no unique formula
    at all.  The licensed union splits the copies at the declared
    non-identities and either answers from one wheel or reports the exact
    ambiguity.
    """
    naive = split_system(False)
    six = dmn.split_system(JUNCTIONS, False,
                           tuple(w for w in WHEELS if w.id in ENERGY_WHEELS),
                           (), relation_vector_q)
    rows = []
    for t, (y, z) in ENERGY_QUESTIONS:
        f = dmn.derive_relations(t, (y, z), naive)
        f6 = dmn.derive_relations(t, (y, z), six)
        got = derive_across(t, (y, z))
        rows.append({"target": t, "inputs": (y, z),
                     "naive": None if f is None else f.formula,
                     "naive_wheels": () if f is None else tuple(f.wheels),
                     "naive_six": None if f6 is None else f6.formula,
                     "licensed": got.formula, "answered": got.answered,
                     "reason": got.reason})
    # A conflation is a formula the six energy wheels derive between them
    # which the full licensed union will not endorse (it refuses, or answers
    # a different formula) once the cross-family junctions are in the table.
    conflations = [r for r in rows
                   if r["naive_six"] is not None
                   and (not r["answered"] or r["licensed"] != r["naive_six"])]
    return {"questions": len(rows),
            "naive_answered": sum(1 for r in rows if r["naive"] is not None),
            "naive_ill_posed": sum(1 for r in rows if r["naive"] is None),
            "naive_six_answered": sum(1 for r in rows if r["naive_six"] is not None),
            "licensed_answered": sum(1 for r in rows if r["answered"]),
            "licensed_refused": sum(1 for r in rows if not r["answered"]),
            "conflations": conflations,
            "rows": rows}
