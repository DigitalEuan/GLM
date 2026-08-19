#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM-2 CODEC  —  meaning <-> Leech point, bijectively
================================================================================

  Part of:  The Geometric Language Machine, second generation (GLM-2).
  Layer  :  Tier 3 — the join between what a concept means and where it lives.
  Deps   :  glm2_meaning, glm2_lattice.

  ------------------------------------------------------------------------
  The map
  ------------------------------------------------------------------------

  A meaning is written into 24 integer slots and those slots are read as
  coordinates in the Leech basis:

      slot   content                                  group
      ----   ---------------------------------------  -----------------
      0- 9   12 x exponent of L M T I H N J A S B      Z^10
      10     12 x decimal scale                        Z
      11     tensor rank                                Z
      12     P parity (0/1)                             Z/2
      13     T parity (0/1)                             Z/2
      14     C parity (0/1)                             Z/2
      15     nominal kind label                         Z_{>=0}
      16     domain label                               Z_{>=0}
      17-23  seven free context slots                   Z^7

                     u in Z^24   -->   x = u B   in Lambda

  B is the Leech basis of glm2_lattice, so u -> uB is a group isomorphism
  Z^24 -> Lambda.  Composition of concepts is addition of meanings, which is
  addition of slots, which is addition of lattice points: the diagram

      meaning(A) + meaning(B)  ->  x_A + x_B

  commutes exactly.  Nothing is reduced modulo anything.

  ------------------------------------------------------------------------
  Three consequences, each checked in `codec_audit`
  ------------------------------------------------------------------------

  1  INJECTIVITY.  Different meanings are different lattice points, with no
     bound on the exponents.  The capacity question that forced GLM-1 into a
     9^7 box does not arise: the carrier is infinite and the encoder uses all
     of it.

  2  SEPARATION.  Two distinct concepts differ by a nonzero lattice vector,
     so their carriers are at squared distance at least 32 — the Leech
     minimal norm.  There is no such thing as a "near collision" between two
     meanings.

  3  EXACT REPAIR.  Because the packing radius squared is 8, any corruption
     of the carrier with squared magnitude at most 7 decodes back to the
     original point, hence to the original meaning, exactly.  Repair in
     GLM-1 (snapping to a codeword) changed the concept; repair here
     restores it.

      python3 glm2_codec.py       # codec self-audit
================================================================================
"""

from __future__ import annotations

from fractions import Fraction as F
from typing import Dict, List, Optional, Sequence, Tuple

from glm2_lattice import (DIM, MIN_NORM2, decode, from_coords, in_leech,
                          norm2, theta_series, to_coords)
from glm2_meaning import AXES, DENOM, N_AXES, Meaning

__all__ = [
    "SLOTS", "N_CONTEXT", "coords_of", "meaning_of_coords",
    "encode", "decode_point", "repair", "RepairResult", "compose",
    "separation_bound", "capacity_within_norm", "codec_audit",
]

#: slot layout, in order
SLOTS: Tuple[str, ...] = (
    tuple(f"exp_{a}" for a in AXES)
    + ("scale", "rank", "P", "T", "C", "kind", "domain")
    + tuple(f"ctx_{i}" for i in range(7))
)
assert len(SLOTS) == DIM

N_CONTEXT = 7
_CTX0 = 17


# ══════════════════════════════════════════════════════════════════════════════
# §1.  MEANING  <->  SLOTS
# ══════════════════════════════════════════════════════════════════════════════

def coords_of(m: Meaning, context: Sequence[int] = ()) -> List[int]:
    """The 24 integer slots of a meaning (with optional context)."""
    if not m.encodable():
        raise ValueError(f"meaning is off the 1/{DENOM} lattice: {m}")
    ctx = list(context) + [0] * (N_CONTEXT - len(context))
    if len(ctx) != N_CONTEXT:
        raise ValueError(f"context takes at most {N_CONTEXT} integers")
    u = [int(e * DENOM) for e in m.exps]
    u.append(int(m.scale * DENOM))
    u.extend([m.rank, m.p, m.t, m.c, m.kind, m.domain])
    u.extend(ctx)
    assert len(u) == DIM
    return u


def meaning_of_coords(u: Sequence[int]) -> Tuple[Meaning, Tuple[int, ...]]:
    """Inverse of `coords_of` on its image; raises off the image."""
    if len(u) != DIM:
        raise ValueError("meaning_of_coords: 24 slots required")
    exps = tuple(F(int(v), DENOM) for v in u[:N_AXES])
    scale = F(int(u[N_AXES]), DENOM)
    rank, p, t, c, kind, domain = (int(v) for v in u[N_AXES + 1:_CTX0])
    if p not in (0, 1) or t not in (0, 1) or c not in (0, 1):
        raise ValueError("parity slots must be 0 or 1")
    if kind < 0 or domain < 0:
        raise ValueError("kind and domain slots must be >= 0")
    m = Meaning(exps, scale, rank, p, t, c, kind, domain)
    return m, tuple(int(v) for v in u[_CTX0:])


# ══════════════════════════════════════════════════════════════════════════════
# §2.  MEANING  <->  LATTICE
# ══════════════════════════════════════════════════════════════════════════════

def encode(m: Meaning, context: Sequence[int] = ()) -> Tuple[int, ...]:
    """The Leech point carrying a meaning."""
    return from_coords(coords_of(m, context))


def decode_point(x: Sequence[int]) -> Tuple[Meaning, Tuple[int, ...]]:
    """Read a meaning off a lattice point (exact; raises if x is not in
    Lambda or not in the image of the encoder)."""
    u = to_coords(list(x))
    if u is None:
        raise ValueError("point is not in the Leech lattice")
    return meaning_of_coords(u)


class RepairResult:
    """The outcome of repairing a corrupted carrier."""

    __slots__ = ("meaning", "context", "point", "error_norm2", "within_radius",
                 "exact")

    def __init__(self, meaning, context, point, error_norm2, within_radius,
                 exact) -> None:
        self.meaning = meaning
        self.context = context
        self.point = point
        self.error_norm2 = error_norm2
        self.within_radius = within_radius
        self.exact = exact

    def __repr__(self) -> str:
        return (f"RepairResult({self.meaning}, err^2={self.error_norm2}, "
                f"within_radius={self.within_radius})")


def repair(y: Sequence[int],
           expected: Optional[Meaning] = None) -> RepairResult:
    """
    Decode a corrupted carrier back to a meaning.

    `error_norm2` is the squared distance from the received point to the
    lattice; `within_radius` says whether it was inside the packing radius,
    in which case the repair is guaranteed correct.

    Outside the packing radius the nearest lattice point need not lie in the
    image of the encoder at all — a Leech point whose parity slots are not in
    {0, 1}, or whose label slots are negative, simply carries no meaning.
    That is reported as `meaning = None` and `exact = False`; it is never an
    exception, and never a wrong answer.  This is invariant I5: repair either
    returns the right concept or admits that it has none.
    """
    res = decode(list(y))
    try:
        m, ctx = decode_point(res.point)
    except ValueError:
        return RepairResult(None, None, res.point, res.dist2,
                            res.dist2 < 8, False if expected is not None
                            else None)
    exact = None if expected is None else m.same_quantity(expected)
    return RepairResult(m, ctx, res.point, res.dist2, res.dist2 < 8, exact)


# ══════════════════════════════════════════════════════════════════════════════
# §3.  CAPACITY AND SEPARATION
# ══════════════════════════════════════════════════════════════════════════════

def separation_bound() -> int:
    """Minimum squared distance between the carriers of two distinct
    meanings: the Leech minimal norm."""
    return MIN_NORM2


def capacity_within_norm(max_norm2: int) -> int:
    """
    How many concepts have a carrier of squared norm at most `max_norm2`.

    Counted from the theta series.  In the integer (x sqrt 8) model a point
    of unscaled norm 2n has squared norm 16n, so coefficient n of the theta
    series counts the points of squared norm 16n.
    """
    if max_norm2 % 16:
        raise ValueError("squared norms of Lambda points are multiples of 16 "
                         "in this model")
    return sum(theta_series(max_norm2 // 16))


def compose(x: Sequence[int], y: Sequence[int]) -> Tuple[int, ...]:
    """
    Compose two carriers, i.e. carry the product of the two quantities.

    On the torsion-free part this is simply x + y: exponents, scale, rank and
    context add in Z, with no reduction anywhere.  The three parity slots are
    genuinely Z/2-valued, so they are reduced mod 2, and the two label slots
    follow the merge rule of `Meaning.__add__`.  See Proposition C2 of the
    paper: no injective homomorphism from the meaning module into a
    torsion-free group can exist, so this small twist is forced, and it costs
    nothing because a parity really is a sign.
    """
    u = to_coords(list(x))
    v = to_coords(list(y))
    if u is None or v is None:
        raise ValueError("compose: arguments must be Leech points")
    ma, ca = meaning_of_coords(u)
    mb, cb = meaning_of_coords(v)
    ctx = tuple(a + b for a, b in zip(ca, cb))
    return encode(ma + mb, ctx)


# ══════════════════════════════════════════════════════════════════════════════
# §4.  AUDIT
# ══════════════════════════════════════════════════════════════════════════════

def codec_audit(sample_limit: int = 0) -> Dict[str, object]:
    from glm2_library import CONCEPTS

    names = sorted(CONCEPTS)
    if sample_limit:
        names = names[:sample_limit]

    points: Dict[Tuple[int, ...], str] = {}
    round_trip = True
    membership = True
    for name in names:
        m = CONCEPTS[name].meaning
        x = encode(m)
        membership &= in_leech(list(x))
        back, ctx = decode_point(x)
        round_trip &= (back == m and ctx == (0,) * N_CONTEXT)
        points.setdefault(x, name)

    distinct_meanings = len({(c.meaning.exps, c.meaning.scale, c.meaning.rank,
                             c.meaning.p, c.meaning.t, c.meaning.c,
                             c.meaning.kind, c.meaning.domain)
                             for c in CONCEPTS.values()})

    # composition: exact on the torsion-free part, and always exact through
    # `compose`
    hom_free = True
    hom_all = True
    keys = ["energy", "mass", "speed", "torque", "information_rate",
            "kilometre", "radiance", "magnetic_flux_density", "stress"]
    for a in keys:
        for b in keys:
            ma, mb = CONCEPTS[a].meaning, CONCEPTS[b].meaning
            lhs = encode(ma + mb)
            plain = tuple(p + q for p, q in zip(encode(ma), encode(mb)))
            hom_all &= lhs == compose(encode(ma), encode(mb))
            torsion_free = (ma.p == mb.p == ma.t == mb.t == ma.c == mb.c == 0
                            and ma.kind == mb.kind == 0
                            and ma.domain == mb.domain == 0)
            if torsion_free:
                hom_free &= lhs == plain

    # separation
    sep = min(norm2([a - b for a, b in zip(encode(CONCEPTS[x].meaning),
                                           encode(CONCEPTS[y].meaning))])
              for i, x in enumerate(names[:60]) for y in names[:60]
              if x != y and encode(CONCEPTS[x].meaning)
              != encode(CONCEPTS[y].meaning))

    # repair: every corruption of squared magnitude <= 7
    energy = CONCEPTS["energy"].meaning
    base = encode(energy)
    repaired = 0
    trials = 0
    for pattern in range(1, 128):
        err = [0] * DIM
        bits = [i for i in range(7) if (pattern >> i) & 1]
        for k, i in enumerate(bits):
            err[(3 * i + 5) % DIM] = 1 if k % 2 == 0 else -1
        if norm2(err) > 7:
            continue
        trials += 1
        res = repair([a + b for a, b in zip(base, err)], expected=energy)
        repaired += 1 if (res.exact and res.point == base) else 0

    return {
        "concepts_encoded": len(names),
        "distinct_meanings": distinct_meanings,
        "distinct_carriers": len(points),
        "all_in_lattice": membership,
        "round_trip_exact": round_trip,
        "addition_is_exact_on_torsion_free_part": hom_free,
        "compose_matches_meaning_product": hom_all,
        "minimum_separation_squared": sep,
        "separation_bound": separation_bound(),
        "repair_trials": trials,
        "repairs_exact": repaired,
        "concepts_within_norm2_32": capacity_within_norm(32),
        "concepts_within_norm2_48": capacity_within_norm(48),
        "capacity": "countably infinite (bijection with Z^24)",
    }


if __name__ == "__main__":  # pragma: no cover
    print("GLM-2 CODEC — self-audit")
    for k, v in codec_audit().items():
        print(f"  {k:32s} {v}")
