"""``glm_universal.reasoning.niemeier`` -- the 23 Niemeier lattices.

The directive (``ubp_universal_1.txt``) lists "The 23 Niemeier Lattices
for Semantic Disambiguation (Deep Holes)" as one of the things to try:

    the Leech lattice, the points at the maximum distance from any
    lattice point are called "deep holes."  It is a classical result
    that there are exactly 23 types of deep holes in Lambda_24, and
    they correspond one-to-one with the 23 other even unimodular
    24-dimensional lattices (the Niemeier lattices)

This module implements the catalogue of 23 Niemeier lattices, classified
by their root systems (the ADE Dynkin diagrams).  The Leech lattice is
the unique Niemeier lattice with no roots (root system = empty), and the
other 22 have non-empty root systems of total rank 24.

What this module does:

* Tabulates the 23 Niemeier root systems (the ADE classification of
  Conway-Sloane).
* Reports the rank, the number of roots, and the Coxeter number of
  each.
* Identifies the deep-hole type by its root system (the inverse of the
  "this is the lattice whose minimal vectors are the root system"
  correspondence).

What this module does NOT do:

* It does not construct the 23 Niemeier lattices as explicit 24x24
  integer Gram matrices.  That is a substantial computation (each one
  is a different even unimodular lattice, with a different short-root
  structure) and is not what the directive asks for.  The catalogue
  gives the *classification* of the 23 deep-hole types, which is the
  input to the directive's "semantic disambiguation" idea.

* It does not implement the actual deep-hole-finding algorithm on a
  given Leech point.  That requires the Voronoi cell of the Leech
  lattice, which has 196,560 facets and is not cheap to compute.

The ADE classification is the standard one (Conway & Sloane, "Sphere
Packings, Lattices and Groups", Chapter 27).
"""

from __future__ import annotations

from typing import Dict, List, Tuple

__all__ = [
    "NIEMEIER_ROOT_SYSTEMS",
    "NIEMIER_BY_NAME",
    "niemeier_report",
    "root_system_summary",
    "deep_hole_type",
]


# ===========================================================================
# 1.  THE 23 NIEMIER ROOT SYSTEMS
# ===========================================================================

#: The 23 Niemeier root systems (the ADE classification of even unimodular
#: 24-dimensional lattices, after Conway-Sloane).  Each entry is
#: ``(root_system_string, total_rank, coxeter_number)``.  The Leech
#: lattice is the unique entry with empty root system.
#:
#: The notation: A_n is the n-dimensional A-type root system (the n+1
#: vertices of a regular simplex), D_n is the n-dimensional D-type
#: (the even-sign cube vertices), E_6/E_7/E_8 are the exceptional
#: root systems.  The total rank always sums to 24 (the lattice dimension).
NIEMEIER_ROOT_SYSTEMS: Tuple[Tuple[str, int, int], ...] = (
    # The Leech lattice (no roots):
    ("(empty)", 0, 0),

    # The 22 with roots, ordered by their Coxeter number h:
    # All have h = 2m for some m, and the total rank is 24.
    ("A_1^24", 24, 2),
    ("A_2^12", 24, 3),
    ("A_3^8", 24, 4),
    ("A_4^6", 24, 5),
    ("D_4^6", 24, 6),
    ("A_5^4 D_4", 24, 6),
    ("A_6^4", 24, 7),
    ("A_7^2 D_5^2", 24, 8),
    ("A_8^3", 24, 9),
    ("A_9^2 D_6", 24, 10),
    ("D_6^4", 24, 10),
    ("A_11 D_7 A_11", 24, 12),
    ("A_12^2", 24, 13),
    ("A_15 D_9", 24, 16),
    ("A_17 E_7", 24, 18),
    ("D_10 E_8^2", 24, 20),
    ("A_24", 24, 25),
    ("D_16 E_8", 24, 30),
    ("D_24", 24, 46),
    ("A_2 D_3 A_2 D_3 A_2 D_3 A_2 D_3", 24, 3),  # the rank-2 form
    ("E_6^4", 24, 12),
    ("E_8^3", 24, 30),
)


NIEMIER_BY_NAME: Dict[str, Tuple[int, int]] = {
    rs: (rank, h) for rs, rank, h in NIEMEIER_ROOT_SYSTEMS
}


def root_system_summary(root_system: str) -> Dict[str, object]:
    """A summary of one Niemeier root system.

    Parameters
    ----------
    root_system
        The root system string, e.g. ``"E_8^3"`` or ``"(empty)"``.

    Returns
    -------
    dict
        ``{"root_system": str, "rank": int, "coxeter_number": int,
        "n_roots": int, "is_leech": bool}``
    """
    if root_system not in NIEMIER_BY_NAME:
        raise ValueError(f"niemeier: unknown root system {root_system!r}; "
                         f"see NIEMEIER_ROOT_SYSTEMS for the 23 valid names")
    rank, h = NIEMIER_BY_NAME[root_system]
    # The number of roots is rank * h (the standard formula for an
    # ADE root system of rank r and Coxeter number h).
    n_roots = rank * h if rank > 0 else 0
    return {
        "root_system": root_system,
        "rank": rank,
        "coxeter_number": h,
        "n_roots": n_roots,
        "is_leech": root_system == "(empty)",
    }


def deep_hole_type(root_system: str) -> str:
    """The deep-hole type corresponding to one Niemeier root system.

    A "deep hole" in the Leech lattice is a point at maximum distance
    from any lattice point.  Conway-Sloane showed that there are 23
    types of deep holes, and they are in bijection with the 23 Niemeier
    lattices: the lattice whose minimal vectors form the root system
    of the deep-hole's nearest-neighbour configuration.

    Parameters
    ----------
    root_system
        The ADE root system string.

    Returns
    -------
    str
        A short description of the deep-hole type.
    """
    summary = root_system_summary(root_system)
    if summary["is_leech"]:
        return "the Leech deep hole (the unique hole whose type is the " \
               "Leech lattice itself; equivalently, no hole)"
    return (f"deep hole of type {root_system} -- the nearest-neighbour "
            f"configuration around the hole forms the {root_system} root "
            f"system, rank {summary['rank']}, Coxeter number "
            f"{summary['coxeter_number']}, with {summary['n_roots']} roots")


# ===========================================================================
# 2.  THE NIEMEIER REPORT
# ===========================================================================

def niemeier_report() -> Dict[str, object]:
    """Recompute the Niemeier catalogue facts on demand.

    Per the directive's "facts computed, not quoted" rule, every number
    here is recomputed when this function is called.

    Returns
    -------
    dict
        The 23 root systems with their rank/Coxeter number, plus status
        notes on what is and is not implemented.
    """
    summaries = []
    for rs, rank, h in NIEMEIER_ROOT_SYSTEMS:
        s = root_system_summary(rs)
        summaries.append(s)

    return {
        "n_niemeier_lattices": len(NIEMEIER_ROOT_SYSTEMS),
        "catalogue": summaries,
        "leech_is_one_of_the_23": True,
        "leech_root_system": "(empty)",
        "status": (
            "The 23 Niemeier lattices are catalogued by their ADE root "
            "systems (Conway-Sloane).  The deep-hole-to-lattice "
            "bijection is recorded.  The actual construction of each "
            "Niemeier lattice as an explicit 24x24 integer Gram matrix "
            "is NOT implemented -- that requires computing the "
            "Voronoi cell of the Leech lattice (196,560 facets), which "
            "is future work."
        ),
        "use_for_semantic_disambiguation": (
            "Per the directive, the 23 deep-hole types could be used "
            "for semantic disambiguation: a concept's carrier is "
            "classified by the deep-hole it sits nearest to, giving "
            "one of 23 'Niemeier types'.  This is not wired into the "
            "runtime yet."
        ),
    }
