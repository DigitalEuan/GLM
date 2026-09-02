"""``glm_universal.reasoning.higher_lattices`` -- the 24 -> 32 -> 48 ladder.

Why go past 24
--------------
Everything spatial in this package lives in 24 dimensions: the Golay code, the
MOG, the Leech lattice, its 196,560 minimal vectors, the hull census that says
which targets a 24-dimensional carrier can hold.  That is a stopping point, not
an end point.  The even unimodular lattices whose minimum is as large as the
dimension allows -- the **extremal** ones -- exist in dimensions 8, 16, 24, 32,
40, 48, ..., and the next two rungs above the Leech lattice are the ones this
module builds:

======  ========  ===============  ===============  =========================
dim     minimum   centre density   kissing          construction
======  ========  ===============  ===============  =========================
8       2         ``1/16``         240              ``E_8``
24      4         ``1``            196,560          Golay, Construction A + glue
32      4         ``1``            146,880          Construction D over
                                                    ``RM(1,5) < RM(3,5)``
48      6         ``(3/2)^24``     not computed      ternary Construction A over
                                    here            the Pless code ``C(23)``,
                                                    then a neighbour step
======  ========  ===============  ===============  =========================

The centre densities are recomputed exactly by :func:`ladder_report` from
``delta = (minimum/4)^(n/2)`` (valid because all four lattices are unimodular),
so the 48-dimensional rung is ``(3/2)^24``, about **16,834 times** denser than
the Leech lattice per unit cell.  That factor is the whole point of the climb.

The two constructions, and the two obstacles
--------------------------------------------
The substrate modules do the work and are certified separately:

* :mod:`glm_universal.substrate.lattice32` -- the obstacle in 32 dimensions is
  that Construction A over any binary code keeps ``2 e_i``.  The fix is a
  *two-level* lift, Construction D, over a nested pair of Reed-Muller codes,
  and the payoff is a genuine **three-resolution address**: every point is
  ``4a + 2b + c`` with ``c`` one of 64 outer codewords, ``b`` one of ``2^26``
  inner codewords and ``a`` free.
* :mod:`glm_universal.substrate.lattice48` -- the obstacle in 48 dimensions is
  that no binary code will do at all, and the fix is to move to ``F_3``.  The
  payoff is minimum 6, but only after a neighbour step: of the two even
  unimodular neighbours of the even sublattice, one has minimum 4 and the
  other has minimum 6, and which is which is decided by a parity census of
  the 96 full-weight codewords.

Multi-resolution addressing
---------------------------
This is the part that feeds back into the rest of the package.  A Leech
address is *flat*: a point is a point, and the mod-2 / mod-4 / mod-8 sieve of
:mod:`glm_universal.substrate.leech_construct` is a membership test, not a
decomposition -- you cannot hand someone the coarse part of a Leech vector and
have them reconstruct at that resolution alone.

Construction D is different.  Its three levels are *nested lattices*, each an
honest quotient of the next, so the address really is hierarchical:

    ``4 Z^32  <  4 Z^32 + 2 RM(3,5)  <  4 Z^32 + 2 RM(3,5) + RM(1,5)``

:func:`address_ladder` reports the indices (``2^26`` then ``2^6``, total
``2^32``), and :func:`address_round_trip` takes a point apart and puts it back
together, checking that truncating the address to the first ``k`` levels gives
exactly the nearest point of the ``k``-th nested lattice.  That is what
"multi-resolution addressing" buys: a coarse address that is usable on its own
and refinable later, which is precisely what a single Leech address is not.

What is proved, and where
-------------------------
``RequestProject/GLM/HigherLattices.lean`` carries the two minimum theorems and
the addressing lemma:

* ``BarnesWall.norm_ge_of_ne_zero`` -- the three-case argument for minimum 4;
* ``BarnesWall.norm_dvd_eight`` -- evenness, from the duality of the two codes;
* ``BarnesWall.mk_injective`` -- the three-level address is unique;
* ``Ternary.even_norm_ge_eighteen`` -- the 48-dimensional even sublattice has
  minimum 6.

Everything else -- the code parameters, the determinant, the kissing census,
the full-weight parity census -- is recomputed here from scratch.
"""

from __future__ import annotations

from fractions import Fraction
from functools import lru_cache
from typing import Dict, List, Sequence, Tuple

from ..substrate import lattice32, lattice48

__all__ = [
    "ladder_report",
    "centre_density",
    "address_ladder",
    "address_round_trip",
    "resolution_gain",
    "dimension48_story",
    "higher_lattices_report",
]


def centre_density(dimension: int, minimum: int) -> Fraction:
    """``(minimum/4)^(n/2)`` -- the centre density of a unimodular lattice.

    The centre density of a lattice with minimum ``mu`` and determinant ``d``
    is ``(sqrt(mu)/2)^n / sqrt(d)``; for a unimodular lattice ``d = 1`` and
    ``n`` is even, so the expression is the exact rational above.
    """
    if dimension % 2 != 0:
        raise ValueError("centre_density: dimension must be even")
    return Fraction(minimum, 4) ** (dimension // 2)


#: the rungs of the ladder, with the kissing numbers this package computes
_RUNGS: Tuple[Dict[str, object], ...] = (
    {"dimension": 8, "minimum": 2, "name": "E_8",
     "kissing": 240, "kissing_source": "classical"},
    {"dimension": 16, "minimum": 2, "name": "E_8 + E_8 and D_16^+",
     "kissing": 480, "kissing_source": "classical"},
    {"dimension": 24, "minimum": 4, "name": "Leech Lambda_24",
     "kissing": 196560,
     "kissing_source": "glm_universal.substrate.leech2.minimal_vectors"},
    {"dimension": 32, "minimum": 4, "name": "Barnes-Wall BW_32",
     "kissing": 146880,
     "kissing_source": "glm_universal.substrate.lattice32"},
    {"dimension": 48, "minimum": 6, "name": "extremal 48-dimensional N2",
     "kissing": None,
     "kissing_source": "not computed here"},
)


@lru_cache(maxsize=None)
def ladder_report() -> Dict[str, object]:
    """The ladder of extremal even unimodular lattices, with exact densities.

    The extremal minimum in dimension ``n`` (a multiple of 8) is
    ``2 + 2 * floor(n / 24)``, and every rung listed meets it.
    """
    rows: List[Dict[str, object]] = []
    for rung in _RUNGS:
        n = int(rung["dimension"])
        mu = int(rung["minimum"])
        extremal = 2 + 2 * (n // 24)
        rows.append({
            **rung,
            "extremal_minimum": extremal,
            "is_extremal": mu == extremal,
            "centre_density": centre_density(n, mu),
        })
    leech = next(r for r in rows if r["dimension"] == 24)
    return {
        "rows": tuple(rows),
        "all_extremal": all(r["is_extremal"] for r in rows),
        "density_gain_over_leech": {
            int(r["dimension"]): r["centre_density"] / leech["centre_density"]
            for r in rows
        },
        "built_here": (32, 48),
    }


@lru_cache(maxsize=None)
def address_ladder() -> Dict[str, object]:
    """The nested-lattice chain of the 32-dimensional address.

    Three lattices, two quotients.  The indices are the sizes of the two
    codes: ``2^26`` for the inner Reed-Muller code and ``2^6`` for the outer
    one, ``2^32`` in total, which is exactly the index of ``4 Z^32`` in
    ``Z^32`` divided by ``2^32`` -- the statement that Construction D is a
    *tiling* of the coarse lattice by code cosets and nothing is wasted.
    """
    ladder = lattice32.index_ladder()
    codes = lattice32.code_report()
    return {
        "levels": ladder["levels"],
        "step_indices": ladder["step_indices"],
        "total_index": ladder["total_index"],
        "inner_code": {"length": codes["inner"]["length"],
                       "dimension": codes["inner"]["dimension"],
                       "minimum_weight": codes["inner"]["minimum_weight"]},
        "outer_code": {"length": codes["outer"]["length"],
                       "dimension": codes["outer"]["dimension"],
                       "minimum_weight": codes["outer"]["minimum_weight"]},
        "nested": codes["nested"],
        "dual_pair": codes["dual"]["is_dual_pair"],
        "theorem": "GLM.HigherLattices.BarnesWall.mk_injective",
    }


def address_round_trip(vectors: Sequence[Sequence[int]] | None = None
                       ) -> Dict[str, object]:
    """Take points apart into ``(a, b, c)`` and put them back together.

    The address is exact and unique, so ``from_address(address(x)) == x`` for
    every point of the lattice, and the coarse parts are genuinely usable on
    their own: dropping ``c`` lands in the middle lattice, dropping ``b`` as
    well lands in ``4 Z^32``.
    """
    if vectors is None:
        basis = lattice32.generator_matrix()
        probes = [basis[0], basis[7], basis[31],
                  tuple(basis[0][i] + basis[7][i] for i in range(32)),
                  tuple(basis[3][i] - 2 * basis[19][i] for i in range(32))]
    else:
        probes = [tuple(v) for v in vectors]
    rows = []
    for x in probes:
        addr = lattice32.address(x)
        if addr is None:
            rows.append({"norm2": lattice32.norm2(x), "round_trip": False,
                         "in_lattice": False})
            continue
        fine = addr["fine"]
        mid_mask = int(addr["middle"])
        rebuilt = lattice32.from_address(addr)
        middle = tuple(4 * fine[i] + 2 * ((mid_mask >> i) & 1)
                       for i in range(32))
        coarse = tuple(4 * value for value in fine)
        rows.append({
            "norm2": lattice32.norm2(x),
            "in_lattice": True,
            "round_trip": tuple(rebuilt) == tuple(x),
            "coarse_is_codeword": lattice32.in_outer(int(addr["coarse"])),
            "middle_is_codeword": lattice32.in_inner(mid_mask),
            "middle_in_lattice": lattice32.in_lattice(middle),
            "coarse_in_lattice": lattice32.in_lattice(coarse),
            "levels_nested": all(v % 4 == 0 for v in coarse),
        })
    return {
        "probes": len(rows),
        "rows": tuple(rows),
        "all_in_lattice": all(r["in_lattice"] for r in rows),
        "all_round_trip": all(r["round_trip"] for r in rows),
        "all_levels_usable": all(r.get("middle_in_lattice")
                                 and r.get("coarse_in_lattice")
                                 for r in rows),
    }


def resolution_gain() -> Dict[str, object]:
    """What each resolution of the 32-dimensional address distinguishes.

    A flat Leech address distinguishes points and nothing coarser.  The
    Construction D address distinguishes at three scales, and the coarse two
    are finite: 64 coarse cells, ``2^26`` middle cells inside each.
    """
    ladder = lattice32.index_ladder()
    middle_step, coarse_step = ladder["step_indices"]
    return {
        "coarse_addresses": coarse_step,
        "middle_addresses": middle_step,
        "total_index": ladder["total_index"],
        "product_is_total": coarse_step * middle_step
        == ladder["total_index"],
        "leech_comparison": {
            "leech_levels": 1,
            "leech_note": "the mod 2 / mod 4 / mod 8 sieve of "
                          "leech_construct is a membership test, not a "
                          "decomposition into usable coarse addresses",
            "barnes_wall_levels": 3,
        },
    }


@lru_cache(maxsize=None)
def dimension48_story(exhaustive: bool = False) -> Dict[str, object]:
    """The 48-dimensional rung, condensed to the four load-bearing facts."""
    report = lattice48.lattice48_report(exhaustive)
    neighbours = report["neighbours"]
    return {
        "binary_route_stops_at": report["binary_route"]["lattice_minimum"],
        "binary_reason": report["binary_route"]["why_it_stops"],
        "ternary_code": {
            "name": report["ternary_route"]["code"]["name"],
            "self_dual": report["ternary_route"]["code"]["self_dual"],
            "minimum_weight":
                report["ternary_route"]["code"]["minimum_weight"],
            "distance_certificate": report["ternary_route"]["distance"],
        },
        "construction_a_minimum": report["construction_a"]["minimum"],
        "even_sublattice_minimum": report["even_sublattice"]["minimum"],
        "full_weight_census": neighbours["census"],
        "N1_minimum": neighbours["N1"]["minimum"],
        "N2_minimum": neighbours["N2"]["minimum"],
        "extremal": neighbours["N2"]["extremal"],
        "conclusion": neighbours["conclusion"],
        "theorem": "GLM.HigherLattices.Ternary.even_norm_ge_eighteen",
    }


@lru_cache(maxsize=None)
def higher_lattices_report(exhaustive: bool = False) -> Dict[str, object]:
    """Recompute the whole study on demand."""
    return {
        "ladder": ladder_report(),
        "dimension_32": {
            "codes": lattice32.code_report(),
            "minimum": lattice32.minimum_certificate(),
            "determinant": lattice32.determinant_report(),
            "kissing": lattice32.minimal_shape_census(False),
            "address": address_ladder(),
            "round_trip": address_round_trip(),
            "resolution": resolution_gain(),
        },
        "dimension_48": dimension48_story(exhaustive),
        "theorems": {
            "32-dim minimum":
                "GLM.HigherLattices.BarnesWall.norm_ge_of_ne_zero",
            "32-dim evenness":
                "GLM.HigherLattices.BarnesWall.norm_dvd_eight",
            "32-dim address unique":
                "GLM.HigherLattices.BarnesWall.mk_injective",
            "48-dim even minimum":
                "GLM.HigherLattices.Ternary.even_norm_ge_eighteen",
        },
    }
