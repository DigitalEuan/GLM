"""``glm_universal.reasoning.niemeier`` -- the 23 Niemeier root systems.

The directive (``ubp_universal_1.txt``) lists "The 23 Niemeier Lattices
for Semantic Disambiguation (Deep Holes)" as one of the things to try:

    the Leech lattice, the points at the maximum distance from any
    lattice point are called "deep holes."  It is a classical result
    that there are exactly 23 types of deep holes in Lambda_24, and
    they correspond one-to-one with the 23 other even unimodular
    24-dimensional lattices (the Niemeier lattices)

Derived, not stored
-------------------
An earlier version of this module held the 23 root systems as a literal
table.  A table is a thing that can be wrong, and that one was: it listed
``D_10 E_8^2`` (rank 26), ``A_11 D_7 A_11`` (rank 29) and a fabricated
``A_2 D_3 ...`` entry, and it was missing ``D_8^3``, ``D_12^2`` and
``D_10 E_7^2``.  The ranks it recorded were the ranks it *claimed*, so the
test that checked "every rank is 24" checked the claim against itself.

The table is now **computed**.  A Niemeier root system is a union of ADE
components in which

* every component has the **same Coxeter number** ``h``, and
* the **total rank is 24**,

and the ADE data each component contributes -- rank, Coxeter number, root
count -- is itself a formula, not a list:

    ``A_n``: rank ``n``, ``h = n + 1``,   ``n(n+1)`` roots
    ``D_n`` (``n >= 4``): rank ``n``, ``h = 2n - 2``, ``2n(n-1)`` roots
    ``E_6``: ``h = 12``, 72 roots; ``E_7``: ``h = 18``, 126;
    ``E_8``: ``h = 30``, 240.

:func:`enumerate_niemeier_root_systems` runs that search and finds exactly
23 solutions -- the classical list, reproduced rather than copied.  Every
one automatically has ``24 h`` roots, since the ranks sum to 24 and the
Coxeter numbers agree; :func:`niemeier_report` checks that too.  The
24th even unimodular lattice in this dimension is the Leech lattice
itself, which has **no** roots and so is not in the search's range; it is
reported separately as :data:`LEECH_ROOT_SYSTEM`.

Holes, and where they live
--------------------------
Classifying a *carrier* by its nearest Niemeier type is a question about
the Leech lattice's Delaunay cells, not about this catalogue, and it is
answered next door in
:mod:`glm_universal.reasoning.deep_holes` -- by running the modulator at
the carrier and reading the cell off the trajectory, rather than by
materialising a Voronoi cell with 196,560 facets.

Everything here is exact integer arithmetic.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

__all__ = [
    "ADE_FAMILIES",
    "LEECH_ROOT_SYSTEM",
    "NIEMEIER_ROOT_SYSTEMS",
    "NIEMIER_BY_NAME",
    "ade_component",
    "enumerate_niemeier_root_systems",
    "root_system_summary",
    "root_system_components",
    "deep_hole_type",
    "niemeier_report",
]

#: The dimension, and hence the total rank a Niemeier root system must have.
DIMENSION = 24

#: The Leech lattice's root system: there are no roots at all.
LEECH_ROOT_SYSTEM = "(empty)"

#: The three ADE families, as rules rather than rows.  ``E`` is finite and
#: is listed by its three members; ``A`` and ``D`` are formulas in ``n``.
ADE_FAMILIES: Tuple[str, ...] = ("A", "D", "E")


# ===========================================================================
# 1.  THE ADE DATA, AS FORMULAS
# ===========================================================================

def ade_component(letter: str, rank: int) -> Dict[str, int]:
    """The rank, Coxeter number and root count of one ADE component.

    ``D_n`` is only defined for ``n >= 4``: ``D_3`` is ``A_3`` and ``D_2``
    is ``A_1 + A_1``, so admitting them would double-count.  ``E`` exists
    only for ranks 6, 7, 8.
    """
    if letter == "A":
        if rank < 1:
            raise ValueError("ade_component: A_n needs n >= 1")
        return {"rank": rank, "coxeter_number": rank + 1,
                "roots": rank * (rank + 1)}
    if letter == "D":
        if rank < 4:
            raise ValueError("ade_component: D_n is only distinct for n >= 4")
        return {"rank": rank, "coxeter_number": 2 * rank - 2,
                "roots": 2 * rank * (rank - 1)}
    if letter == "E":
        if rank not in (6, 7, 8):
            raise ValueError("ade_component: E_n exists only for n = 6, 7, 8")
        return {"rank": rank,
                "coxeter_number": {6: 12, 7: 18, 8: 30}[rank],
                "roots": {6: 72, 7: 126, 8: 240}[rank]}
    raise ValueError(f"ade_component: unknown family {letter!r}")


def _component_name(letter: str, rank: int, count: int) -> str:
    base = f"{letter}_{rank}"
    return base if count == 1 else f"{base}^{count}"


def _system_name(components: Sequence[Tuple[str, int, int]]) -> str:
    return " ".join(_component_name(l, n, c) for l, n, c in components)


# ===========================================================================
# 2.  THE SEARCH
# ===========================================================================

def enumerate_niemeier_root_systems(
        dimension: int = DIMENSION
) -> Tuple[Tuple[str, Tuple[Tuple[str, int, int], ...], int], ...]:
    """Every ADE union of total rank ``dimension`` with one Coxeter number.

    Returns a tuple of ``(name, components, coxeter_number)``, ordered by
    Coxeter number and then by name.  ``components`` is a tuple of
    ``(letter, rank, multiplicity)``.

    For ``dimension = 24`` this returns the 23 Niemeier root systems.  The
    result is a search, not a table: change the dimension and the function
    answers the corresponding question rather than raising.
    """
    catalogue: List[Tuple[str, int]] = []
    for rank in range(1, dimension + 1):
        catalogue.append(("A", rank))
        if rank >= 4:
            catalogue.append(("D", rank))
        if rank in (6, 7, 8):
            catalogue.append(("E", rank))

    by_coxeter: Dict[int, List[Tuple[str, int]]] = {}
    for letter, rank in catalogue:
        h = ade_component(letter, rank)["coxeter_number"]
        by_coxeter.setdefault(h, []).append((letter, rank))

    found: List[Tuple[str, Tuple[Tuple[str, int, int], ...], int]] = []
    for h in sorted(by_coxeter):
        items = sorted(by_coxeter[h])
        solutions: List[List[Tuple[str, int, int]]] = []

        def search(index: int, remaining: int,
                   chosen: List[Tuple[str, int, int]]) -> None:
            if remaining == 0:
                solutions.append(list(chosen))
                return
            if index >= len(items):
                return
            letter, rank = items[index]
            for count in range(remaining // rank, -1, -1):
                if count:
                    chosen.append((letter, rank, count))
                search(index + 1, remaining - count * rank, chosen)
                if count:
                    chosen.pop()

        search(0, dimension, [])
        for components in solutions:
            found.append((_system_name(components), tuple(components), h))
    return tuple(sorted(found, key=lambda row: (row[2], row[0])))


_DERIVED = enumerate_niemeier_root_systems()

#: The 23 Niemeier root systems, as ``(name, total_rank, coxeter_number)``.
#: Derived by :func:`enumerate_niemeier_root_systems` at import time, so the
#: ranks quoted here are the ranks the components actually have.
NIEMEIER_ROOT_SYSTEMS: Tuple[Tuple[str, int, int], ...] = tuple(
    (name, sum(rank * count for _l, rank, count in components), h)
    for name, components, h in _DERIVED)

#: ``name -> (rank, coxeter number)``, including the rootless Leech entry so
#: that the Leech lattice can be asked about by name like the other 23.
NIEMIER_BY_NAME: Dict[str, Tuple[int, int]] = dict(
    {name: (rank, h) for name, rank, h in NIEMEIER_ROOT_SYSTEMS},
    **{LEECH_ROOT_SYSTEM: (0, 0)})

_COMPONENTS_BY_NAME: Dict[str, Tuple[Tuple[str, int, int], ...]] = {
    name: components for name, components, _h in _DERIVED}


def root_system_components(root_system: str
                           ) -> Tuple[Tuple[str, int, int], ...]:
    """The ``(letter, rank, multiplicity)`` components of a root system."""
    if root_system == LEECH_ROOT_SYSTEM:
        return ()
    if root_system not in _COMPONENTS_BY_NAME:
        raise ValueError(f"niemeier: unknown root system {root_system!r}; "
                         f"see NIEMEIER_ROOT_SYSTEMS for the 23 valid names")
    return _COMPONENTS_BY_NAME[root_system]


def root_system_summary(root_system: str) -> Dict[str, object]:
    """A summary of one Niemeier root system, recomputed from its components.

    ``n_roots`` is summed over the components from the ADE formulas, and the
    identity ``n_roots = rank * h`` is reported rather than assumed.
    """
    if root_system not in NIEMIER_BY_NAME:
        raise ValueError(f"niemeier: unknown root system {root_system!r}; "
                         f"see NIEMEIER_ROOT_SYSTEMS for the 23 valid names")
    components = root_system_components(root_system)
    rank = sum(rank * count for _l, rank, count in components)
    roots = sum(ade_component(letter, r)["roots"] * count
                for letter, r, count in components)
    coxeter = (ade_component(*components[0][:2])["coxeter_number"]
               if components else 0)
    return {
        "root_system": root_system,
        "components": components,
        "rank": rank,
        "coxeter_number": coxeter,
        "n_roots": roots,
        "roots_equal_rank_times_coxeter": roots == rank * coxeter,
        "is_leech": root_system == LEECH_ROOT_SYSTEM,
        "extended_diagram_nodes": rank + len(
            [1 for _l, _r, count in components for _ in range(count)]),
    }


def deep_hole_type(root_system: str) -> str:
    """The deep-hole type corresponding to one Niemeier root system.

    A deep hole of the Leech lattice is a point at the covering radius from
    the lattice.  Conway, Parker and Sloane showed there are 23 classes of
    them, in bijection with the 23 Niemeier lattices that have roots: the
    lattice points nearest the hole form the *extended* Dynkin diagram of
    that root system.  The Leech lattice itself, the 24th even unimodular
    lattice in this dimension, has no roots and is not the type of any hole.
    """
    summary = root_system_summary(root_system)
    if summary["is_leech"]:
        return ("the Leech lattice itself -- the one even unimodular "
                "24-dimensional lattice with no roots, and therefore the "
                "type of no deep hole")
    return (f"deep hole of type {root_system} -- the lattice points nearest "
            f"the hole form the extended Dynkin diagram of {root_system}: "
            f"{summary['extended_diagram_nodes']} vertices, rank "
            f"{summary['rank']}, Coxeter number "
            f"{summary['coxeter_number']}, {summary['n_roots']} roots")


# ===========================================================================
# 3.  THE REPORT
# ===========================================================================

def niemeier_report() -> Dict[str, object]:
    """Recompute the catalogue, and check it against its own constraints."""
    summaries = [root_system_summary(name)
                 for name, _rank, _h in NIEMEIER_ROOT_SYSTEMS]
    ranks_ok = all(s["rank"] == DIMENSION for s in summaries)
    roots_ok = all(s["roots_equal_rank_times_coxeter"] for s in summaries)
    names = [s["root_system"] for s in summaries]
    return {
        "n_niemeier_lattices": len(NIEMEIER_ROOT_SYSTEMS),
        "n_even_unimodular_lattices_in_24_dimensions":
            len(NIEMEIER_ROOT_SYSTEMS) + 1,
        "catalogue": summaries,
        "names": tuple(names),
        "all_ranks_are_24": ranks_ok,
        "all_root_counts_equal_rank_times_coxeter": roots_ok,
        "distinct_names": len(set(names)) == len(names),
        "coxeter_numbers": tuple(sorted({s["coxeter_number"]
                                         for s in summaries})),
        "leech_root_system": LEECH_ROOT_SYSTEM,
        "leech_is_the_24th": True,
        "derivation": (
            "The 23 root systems are not stored.  They are the solutions of "
            "a search: unions of ADE components, all with the same Coxeter "
            "number, of total rank 24.  The rank, Coxeter number and root "
            "count of each component come from the ADE formulas, so the "
            "only inputs are those formulas and the two constraints."),
        "status": (
            "The catalogue is derived and self-checked.  Classifying an "
            "actual carrier by its hole is a separate question, answered by "
            "reasoning.deep_holes: it runs the modulator at the carrier and "
            "reads the Delaunay cell off the trajectory, so the 196,560 "
            "facets of the Voronoi cell are never materialised."),
    }
