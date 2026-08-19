#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM GEOMETRY  —  the versor / fibre layer  (paper section 9)
================================================================================

  Part of:  The Geometric Language Machine (GLM)
  Layer  :  optional.  Nothing in the decision path (equation audit, target
            synthesis, Pi-analysis) depends on this module.
  Deps   :  glm_substrate.py, glm_codec.py, glm_metrology.py

  This module consolidates the "versor / quaternion / conformal" line of
  development that ran through versions 9 to 19 of the archive, keeping what
  is exact, correcting what was decorative and saying which is which.

  What lives here
  ---------------
    §1  Z_4 versors           the fibre key of a MOG column is a quarter turn;
                              six fibres give an element of Z_4, exactly
    §2  quaternionic fibres   the same key read into the quaternion group Q8,
                              where composition stops commuting
    §3  walks and winding     a path through concepts accumulates quarter
                              turns; a closed path has an integer winding
                              number (proved below, verified in the paper)
    §4  holonomy              the ordered quaternion product around a closed
                              loop; path-dependent, and exactly invertible
    §5  conformal grading     the L0 of versions 15-19, computed honestly:
                              it is one half of the syndrome weight
    §6  vacua                 the sigma = 0 ("1A") concepts, counted exactly
    §7  colour                #RRGGBB <-> F_2^24, and the chromatic ground
                              states, which are exactly the 4096 codewords

  Arithmetic is exact throughout: quaternion components are Python ints, and
  the versor layer is integer arithmetic modulo 4.  No floating point is used
  anywhere in this file.

  Run standalone for a self-audit:   python3 glm_geometry.py
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from glm_codec import DimCarrier, MOGCodec
from glm_metrology import QUANTITIES, Dimension, resolve
from glm_substrate import GOLAY, BitOps

__all__ = [
    "Quaternion", "Q_ONE", "Q_I", "Q_J", "Q_K", "QUATERNION_OF_FIBRE",
    "fibre_keys", "versor_index", "versor_symbol",
    "h6_vector", "fibre_product", "h6_norm_sq",
    "quaternion_group_report", "fibre_noncommutativity_report",
    "Walk", "walk_of_names", "winding_report",
    "holonomy", "holonomy_report",
    "conformal_weight", "conformal_grading_report",
    "vacuum_census", "colour_of_word", "word_of_colour",
    "colour_of_concept", "chromatic_ground_states", "colour_report",
    "geometry_audit",
]


# ══════════════════════════════════════════════════════════════════════════════
# §1.  Z_4 VERSORS  —  the fibre key as a quarter turn
# ══════════════════════════════════════════════════════════════════════════════
#
#  The column codec of `glm_codec` splits a 4-bit MOG column into a GF(4)
#  label and a fibre key in Z_4.  The key is the choice of column *within* the
#  label's fibre; four choices, cyclically ordered.  Reading that cyclic order
#  as the fourth roots of unity  1, i, -1, -i  is the "versor" identification
#  of version 9.
#
#  It costs nothing and it buys one honest thing: a Z_4-valued invariant of a
#  word, and hence a Z-valued winding number for closed walks (§3).  It is a
#  labelling of the fibre coordinate, not a claim about the Leech lattice.

VERSOR_SYMBOL = {0: "1", 1: "i", 2: "-1", 3: "-i"}


def fibre_keys(word24: Sequence[int]) -> Tuple[int, ...]:
    """The six Z_4 fibre keys of a 24-bit word, in MOG column order."""
    return MOGCodec.project(word24, aligned=True).fibres


def versor_index(word24: Sequence[int]) -> int:
    """
    The total quarter-turn of a word: the sum of its six fibre keys in Z_4.

    This is the image of the word under

        F_2^24 --codec--> GF(4)^6 x Z_4^6 --sum--> Z_4

    and is exactly computable; no rotation is ever approximated.
    """
    return sum(fibre_keys(word24)) % 4


def versor_symbol(word24: Sequence[int]) -> str:
    """The versor index rendered as one of 1, i, -1, -i."""
    return VERSOR_SYMBOL[versor_index(word24)]


# ══════════════════════════════════════════════════════════════════════════════
# §2.  QUATERNIONIC FIBRES  —  where composition stops commuting
# ══════════════════════════════════════════════════════════════════════════════
#
#  Version 10 replaced the complex versors of version 9 by the quaternion units
#  {1, i, j, k}.  The gain is real but narrow: Z_4 is commutative, Q8 is not,
#  so the ordered product of the six fibre quaternions of a word is sensitive
#  to the order of the columns, while the Z_4 sum is not.  That sensitivity is
#  what §4 turns into a holonomy.
#
#  The map 0,1,2,3 -> 1,i,j,k is a bijection of sets, NOT a group homomorphism
#  (Z_4 is cyclic of order 4, the quaternion units generate Q8 of order 8).
#  This module says so rather than implying otherwise.


@dataclass(frozen=True)
class Quaternion:
    """A quaternion with exact integer components  w + x i + y j + z k."""

    w: int = 0
    x: int = 0
    y: int = 0
    z: int = 0

    def __mul__(self, o: "Quaternion") -> "Quaternion":
        return Quaternion(
            self.w * o.w - self.x * o.x - self.y * o.y - self.z * o.z,
            self.w * o.x + self.x * o.w + self.y * o.z - self.z * o.y,
            self.w * o.y - self.x * o.z + self.y * o.w + self.z * o.x,
            self.w * o.z + self.x * o.y - self.y * o.x + self.z * o.w,
        )

    def __neg__(self) -> "Quaternion":
        return Quaternion(-self.w, -self.x, -self.y, -self.z)

    def conjugate(self) -> "Quaternion":
        return Quaternion(self.w, -self.x, -self.y, -self.z)

    def norm_sq(self) -> int:
        return self.w ** 2 + self.x ** 2 + self.y ** 2 + self.z ** 2

    def inverse(self) -> "Quaternion":
        """Exact inverse; defined here only for the unit quaternions we use."""
        n = self.norm_sq()
        if n != 1:
            raise ValueError("inverse: only unit quaternions are supported "
                             f"exactly (norm^2 = {n})")
        return self.conjugate()

    def is_one(self) -> bool:
        return self == Q_ONE

    def __str__(self) -> str:
        parts = []
        for value, label in ((self.w, ""), (self.x, "i"),
                             (self.y, "j"), (self.z, "k")):
            if value:
                sign = "-" if value < 0 else ("+" if parts else "")
                mag = "" if abs(value) == 1 and label else str(abs(value))
                parts.append(f"{sign}{mag}{label}")
        return "".join(parts) if parts else "0"


Q_ONE = Quaternion(1, 0, 0, 0)
Q_I = Quaternion(0, 1, 0, 0)
Q_J = Quaternion(0, 0, 1, 0)
Q_K = Quaternion(0, 0, 0, 1)

#: The fibre key read into the quaternion units.  A bijection of sets.
QUATERNION_OF_FIBRE: Dict[int, Quaternion] = {0: Q_ONE, 1: Q_I, 2: Q_J, 3: Q_K}


def h6_vector(word24: Sequence[int]) -> List[Quaternion]:
    """The word's six fibre keys read as unit quaternions (the H^6 layout)."""
    return [QUATERNION_OF_FIBRE[f] for f in fibre_keys(word24)]


def h6_norm_sq(word24: Sequence[int]) -> int:
    """
    Sum of the squared norms of the six fibre quaternions.

    This is 6 for every 24-bit word without exception, because each fibre key
    maps to a *unit* quaternion.  Versions 15-19 used this quantity as a
    "Leech norm" and renormalised a conformal weight against it; see §5 for
    what that computation actually reduces to.
    """
    return sum(q.norm_sq() for q in h6_vector(word24))


def fibre_product(word24: Sequence[int], reverse: bool = False) -> Quaternion:
    """
    The ordered product of the six fibre quaternions.

    With `reverse=True` the columns are multiplied right to left.  The two
    results differ exactly when the fibre word is non-commuting, which is the
    only structural content of the quaternionic upgrade.
    """
    quats = h6_vector(word24)
    if reverse:
        quats = list(reversed(quats))
    out = Q_ONE
    for q in quats:
        out = out * q
    return out


def quaternion_group_report() -> Dict[str, object]:
    """
    Exhaustive check of the quaternion relations on the 8 units, and of the
    claim that the fibre map is a bijection of sets but not a homomorphism.
    """
    units = [Q_ONE, -Q_ONE, Q_I, -Q_I, Q_J, -Q_J, Q_K, -Q_K]
    closed = all((a * b) in units for a in units for b in units)
    associative = all(((a * b) * c) == (a * (b * c))
                      for a in units for b in units for c in units)
    relations = {
        "i^2 = -1": Q_I * Q_I == -Q_ONE,
        "j^2 = -1": Q_J * Q_J == -Q_ONE,
        "k^2 = -1": Q_K * Q_K == -Q_ONE,
        "ijk = -1": Q_I * Q_J * Q_K == -Q_ONE,
        "ij = k": Q_I * Q_J == Q_K,
        "ji = -k": Q_J * Q_I == -Q_K,
        "jk = i": Q_J * Q_K == Q_I,
        "ki = j": Q_K * Q_I == Q_J,
    }
    # bijection of sets Z_4 -> {1, i, j, k}
    images = [QUATERNION_OF_FIBRE[f] for f in range(4)]
    bijective = len(set(images)) == 4
    # but not a homomorphism: 1 + 1 = 2 in Z_4 while i * i = -1, not j
    homomorphism = (QUATERNION_OF_FIBRE[1] * QUATERNION_OF_FIBRE[1]
                    == QUATERNION_OF_FIBRE[2])
    return {
        "order": len(units),
        "closed": closed,
        "associative": associative,
        "relations": relations,
        "relations_all_hold": all(relations.values()),
        "fibre_map_bijective": bijective,
        "fibre_map_is_homomorphism": homomorphism,
    }


def fibre_noncommutativity_report(names: Optional[Sequence[str]] = None
                                  ) -> Dict[str, object]:
    """
    How often the ordered fibre product depends on the order, over the
    quantity library.  Exact counts, no sampling.
    """
    keys = list(names) if names is not None else sorted(QUANTITIES)
    order_sensitive: List[str] = []
    tested = 0
    for key in keys:
        word = _carrier_of_name(key)
        if word is None:
            continue
        tested += 1
        if fibre_product(word) != fibre_product(word, reverse=True):
            order_sensitive.append(key)
    return {
        "tested": tested,
        "order_sensitive": len(order_sensitive),
        "order_insensitive": tested - len(order_sensitive),
        "examples": order_sensitive[:8],
    }


# ══════════════════════════════════════════════════════════════════════════════
# §3.  WALKS AND WINDING
# ══════════════════════════════════════════════════════════════════════════════
#
#  Version 9 accumulated "phase" along a path of concepts and called a closed
#  path's total a winding number.  Made exact, the statement is:
#
#    Let  u(w) in Z_4  be the versor index of the word w (§1).  For a step
#    from w to w' put  s = u(w') - u(w) in Z_4  and lift it to the unique
#    representative  s~ in {-1, 0, 1, 2}.  Along any CLOSED walk the sum of
#    the lifted steps is divisible by 4, so
#
#        winding = (sum of lifted steps) / 4
#
#    is an integer.  It counts how many net full turns the lift makes, and it
#    is a genuine invariant of the lift (not of the endpoints alone: different
#    routes between the same endpoints generally give different windings).
#
#  Proof: the lift satisfies s~ = s in Z_4, so the sum of the lifted steps is
#  congruent mod 4 to the sum of the true steps, which telescopes to
#  u(w_n) - u(w_0) = 0 for a closed walk.  Hence the sum is 0 mod 4.  The
#  paper verifies the consequence over every closed walk in a generated family
#  (claim C27); no floating-point phase is ever accumulated.


def _lift_step(delta_mod4: int) -> int:
    """Lift a Z_4 step to the representative in {-1, 0, 1, 2}."""
    d = delta_mod4 % 4
    return d - 4 if d == 3 else d


@dataclass(frozen=True)
class Walk:
    """A walk through named concepts, with its exact quarter-turn accounting."""

    names: Tuple[str, ...]
    indices: Tuple[int, ...]        # versor index of each stop
    steps: Tuple[int, ...]          # lifted quarter turns, one per step
    closed: bool

    @property
    def quarter_turns(self) -> int:
        return sum(self.steps)

    @property
    def winding(self) -> Optional[int]:
        """Integer winding number, defined for closed walks."""
        if not self.closed:
            return None
        total = self.quarter_turns
        assert total % 4 == 0, "closed walk with non-integral winding"
        return total // 4

    def report(self) -> Dict[str, object]:
        return {
            "names": list(self.names),
            "versor_indices": list(self.indices),
            "steps": list(self.steps),
            "quarter_turns": self.quarter_turns,
            "closed": self.closed,
            "winding": self.winding,
        }


def walk_of_names(names: Sequence[str]) -> Walk:
    """Build a walk from concept names (unrepresentable names are rejected)."""
    words = []
    for name in names:
        word = _carrier_of_name(name)
        if word is None:
            raise ValueError(f"walk_of_names: {name!r} has no carrier word")
        words.append(word)
    indices = [versor_index(w) for w in words]
    steps = [_lift_step(indices[i + 1] - indices[i])
             for i in range(len(indices) - 1)]
    closed = len(names) > 1 and names[0] == names[-1]
    return Walk(tuple(names), tuple(indices), tuple(steps), closed)


def winding_report(walks: Optional[Sequence[Sequence[str]]] = None
                   ) -> Dict[str, object]:
    """
    Verify that every closed walk in a family has an integer winding number,
    and report the winding of the E = mc^2 round trip that version 9 quoted.
    """
    if walks is None:
        walks = _default_closed_walks()
    detail = []
    integral = True
    for names in walks:
        walk = walk_of_names(names)
        integral = integral and (walk.quarter_turns % 4 == 0)
        detail.append(walk.report())
    emc2 = walk_of_names(["energy", "mass", "speed", "speed", "energy"])
    return {
        "closed_walks": len(detail),
        "all_windings_integral": integral,
        "windings": sorted({d["winding"] for d in detail}),  # type: ignore[misc]
        "emc2_roundtrip": emc2.report(),
        "detail": detail[:6],
    }


def _default_closed_walks() -> List[List[str]]:
    """A deterministic family of closed walks over the library."""
    library = [k for k in sorted(QUANTITIES) if _carrier_of_name(k) is not None]
    walks: List[List[str]] = []
    n = len(library)
    for start in range(0, n, 3):
        for length in (2, 3, 5):
            stops = [library[(start + step * 7) % n] for step in range(length)]
            walks.append(stops + [stops[0]])
    return walks


# ══════════════════════════════════════════════════════════════════════════════
# §4.  HOLONOMY  —  the ordered product around a loop
# ══════════════════════════════════════════════════════════════════════════════
#
#  Version 12 asked for a path-dependent holonomy.  Here it is, exactly: for a
#  loop of concepts multiply their fibre-product quaternions in order.  Two
#  facts are checkable and both are checked below:
#
#    * holonomy is order-dependent (the loop traversed backwards generally
#      gives a different quaternion), which is the whole point of leaving Z_4
#      for Q8;
#    * holonomy(loop) * holonomy(loop reversed, inverted termwise) = 1, since
#      the reversed inverse product telescopes.  This is a consistency check,
#      not a new claim.


def holonomy(names: Sequence[str], reverse: bool = False) -> Quaternion:
    """Ordered product of the concepts' fibre-product quaternions."""
    out = Q_ONE
    seq = list(reversed(names)) if reverse else list(names)
    for name in seq:
        word = _carrier_of_name(name)
        if word is None:
            raise ValueError(f"holonomy: {name!r} has no carrier word")
        out = out * fibre_product(word)
    return out


def holonomy_report(loops: Optional[Sequence[Sequence[str]]] = None
                    ) -> Dict[str, object]:
    """Path dependence of the holonomy, plus the telescoping consistency check."""
    if loops is None:
        loops = [
            ["energy", "mass", "speed", "energy"],
            ["force", "mass", "acceleration", "force"],
            ["power", "voltage", "current", "power"],
            ["pressure", "force", "area", "pressure"],
        ]
    detail = []
    path_dependent = 0
    telescopes = True
    for loop in loops:
        forward = holonomy(loop)
        backward = holonomy(loop, reverse=True)
        if forward != backward:
            path_dependent += 1
        # forward * (product of inverses, reversed) = 1
        undo = Q_ONE
        for name in reversed(loop):
            word = _carrier_of_name(name)
            assert word is not None
            undo = undo * fibre_product(word).inverse()
        telescopes = telescopes and (forward * undo == Q_ONE)
        detail.append({
            "loop": list(loop),
            "holonomy": str(forward),
            "reversed": str(backward),
            "path_dependent": forward != backward,
        })
    return {
        "loops": len(detail),
        "path_dependent_loops": path_dependent,
        "telescoping_identity_holds": telescopes,
        "detail": detail,
    }


# ══════════════════════════════════════════════════════════════════════════════
# §5.  CONFORMAL GRADING  —  what L0 was, computed honestly
# ══════════════════════════════════════════════════════════════════════════════
#
#  Versions 15 to 19 carried a "renormalised Virasoro weight"
#
#        L0(concept) = (||H^6 vector||^2 - 6) / 2  +  sigma(concept) / 2
#
#  where the first term was described as a renormalisation against a "1A
#  vacuum" of norm 6.  But the H^6 vector is six UNIT quaternions, so its
#  squared norm is 6 for every concept whatsoever (see `h6_norm_sq`), and the
#  first term is identically zero.  The quantity actually computed by those
#  versions is therefore
#
#        L0 = sigma / 2,   half the Golay syndrome weight,
#
#  which is a perfectly good substrate observable and has nothing to do with a
#  Virasoro algebra.  We keep the observable, drop the name, and verify the
#  identity over the whole library (claim C29).


def conformal_weight(word24: Sequence[int]) -> Tuple[int, int]:
    """
    The grading of versions 15-19 as an exact rational (numerator, denominator).

    Returns (sigma, 2): the weight is half the syndrome weight.
    """
    return GOLAY.syndrome_weight(word24), 2


def conformal_grading_report(names: Optional[Sequence[str]] = None
                             ) -> Dict[str, object]:
    """
    Verify, over the library, that the version 15-19 grading collapses to
    sigma/2 and that the H^6 norm is constant.
    """
    keys = list(names) if names is not None else sorted(QUANTITIES)
    tested = 0
    norm_constant = True
    identity_holds = True
    grades: Dict[int, int] = {}
    for key in keys:
        word = _carrier_of_name(key)
        if word is None:
            continue
        tested += 1
        norm_constant = norm_constant and (h6_norm_sq(word) == 6)
        sigma = GOLAY.syndrome_weight(word)
        # the archive formula, evaluated in exact rational arithmetic
        archive = (h6_norm_sq(word) - 6, 2)          # first term
        archive_num = archive[0] + sigma             # + sigma/2, same denominator
        identity_holds = identity_holds and (archive_num == sigma)
        grades[sigma] = grades.get(sigma, 0) + 1
    return {
        "tested": tested,
        "h6_norm_sq_always_six": norm_constant,
        "archive_L0_equals_half_syndrome": identity_holds,
        "syndrome_histogram": dict(sorted(grades.items())),
    }


# ══════════════════════════════════════════════════════════════════════════════
# §6.  VACUA  —  the sigma = 0 concepts
# ══════════════════════════════════════════════════════════════════════════════
#
#  Version 14 searched [-3,3]^7 for "1A" concepts: dimension vectors whose
#  carrier word is a Golay codeword.  With the bijective carrier of the
#  consolidated system the same question has an exact answer over the whole
#  representable box [-4,4]^7 (claim C13 already counts them: 1168).  Here we
#  reproduce the box-by-box census and name the physical ones.


def vacuum_census(bound: int = 3) -> Dict[str, object]:
    """
    Count the lawful (syndrome-zero) dimension vectors in [-bound, bound]^7,
    and list the named quantities among them.
    """
    if not 0 <= bound <= 4:
        raise ValueError("vacuum_census: bound must lie in [0, 4]")
    side = 2 * bound + 1
    lawful: List[List[int]] = []
    exps = [-bound] * 7
    total = side ** 7
    count = 0
    while True:
        word = DimCarrier.encode(exps)
        if GOLAY.syndrome_weight(word) == 0:
            lawful.append(list(exps))
        count += 1
        # odometer over [-bound, bound]^7
        pos = 6
        while pos >= 0:
            exps[pos] += 1
            if exps[pos] <= bound:
                break
            exps[pos] = -bound
            pos -= 1
        if pos < 0:
            break
    named = [k for k in sorted(QUANTITIES)
             if list(resolve(k).exps) in lawful]  # type: ignore[union-attr]
    weights: Dict[int, int] = {}
    for dims in lawful:
        w = BitOps.weight(DimCarrier.encode(dims))
        weights[w] = weights.get(w, 0) + 1
    return {
        "box": f"[-{bound}, {bound}]^7",
        "searched": count,
        "expected": total,
        "lawful": len(lawful),
        "by_carrier_weight": dict(sorted(weights.items())),
        "named_lawful": named,
        "examples": lawful[:5],
    }


# ══════════════════════════════════════════════════════════════════════════════
# §7.  COLOUR  —  #RRGGBB is a 24-bit word
# ══════════════════════════════════════════════════════════════════════════════
#
#  The archive's version 18 noticed that a hex colour is 24 bits and so is a
#  Golay word, and asked which colours are "chromatic ground states", i.e.
#  syndrome-free.  Version 19 searched for them.  No search is needed: the
#  syndrome-free words are exactly the codewords, so there are exactly 4096
#  such colours out of 16,777,216 - one in every 4096 - and they can be listed
#  in full.  Both statements are verified in the paper (claim C31).
#
#  Convention: bit i of the word is bit i of the 24-bit integer 0xRRGGBB, so
#  the blue channel carries bits 0-7, green 8-15, red 16-23.


def colour_of_word(word24: Sequence[int]) -> str:
    """Render a 24-bit word as #RRGGBB."""
    return f"#{BitOps.to_int(word24):06X}"


def word_of_colour(colour: str) -> List[int]:
    """Parse #RRGGBB (or RRGGBB) into a 24-bit word."""
    text = colour.strip().lstrip("#")
    if len(text) != 6:
        raise ValueError(f"word_of_colour: expected 6 hex digits, got {colour!r}")
    return BitOps.from_int(int(text, 16), 24)


def colour_of_concept(name: str) -> Optional[str]:
    """The colour of a named quantity's carrier word, if it is representable."""
    word = _carrier_of_name(name)
    return None if word is None else colour_of_word(word)


def chromatic_ground_states(limit: Optional[int] = None) -> List[str]:
    """
    Every syndrome-free colour, i.e. every Golay codeword rendered as #RRGGBB.
    There are exactly 4096; `limit` truncates the list for display.
    """
    out = [colour_of_word(cw) for cw in GOLAY.all_codewords()]
    out.sort()
    return out if limit is None else out[:limit]


def colour_report(sample_names: Sequence[str] = ("energy", "mass", "speed")
                  ) -> Dict[str, object]:
    """
    The colour view: the ground states are exactly the code, the round trip is
    lossless, and snapping a colour is a chromatic correction with a
    measurable per-channel shift.
    """
    grounds = chromatic_ground_states()
    round_trip_ok = all(word_of_colour(colour_of_word(cw)) == list(cw)
                        for cw in GOLAY.all_codewords())
    black_white = {"#000000": "#000000" in grounds,
                   "#FFFFFF": "#FFFFFF" in grounds}
    shifts = []
    for name in sample_names:
        word = _carrier_of_name(name)
        if word is None:
            continue
        snapped, meta = GOLAY.snap(word)
        before, after = BitOps.to_int(word), BitOps.to_int(snapped)
        shifts.append({
            "concept": name,
            "colour": colour_of_word(word),
            "snapped_colour": colour_of_word(snapped),
            "distance": meta.distance,
            "channel_shift": {
                "R": ((after >> 16) & 0xFF) - ((before >> 16) & 0xFF),
                "G": ((after >> 8) & 0xFF) - ((before >> 8) & 0xFF),
                "B": (after & 0xFF) - (before & 0xFF),
            },
        })
    return {
        "ground_states": len(grounds),
        "total_colours": 1 << 24,
        "ground_state_fraction_one_in": (1 << 24) // len(grounds),
        "round_trip_lossless": round_trip_ok,
        "black_and_white_are_ground_states": black_white,
        "concept_colours": shifts,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  helpers and self-audit
# ══════════════════════════════════════════════════════════════════════════════

def _carrier_of_name(name: str) -> Optional[List[int]]:
    """The carrier word of a named quantity, or None if not representable."""
    try:
        dim: Dimension = resolve(name)
    except Exception:
        return None
    if dim is None or not DimCarrier.in_range(dim.exps):
        return None
    return DimCarrier.encode(dim.exps)


def geometry_audit() -> Dict[str, object]:
    """Everything this module asserts, computed."""
    return {
        "quaternion_group": quaternion_group_report(),
        "fibre_noncommutativity": fibre_noncommutativity_report(),
        "winding": winding_report(),
        "holonomy": holonomy_report(),
        "conformal_grading": conformal_grading_report(),
        "vacua": vacuum_census(bound=2),
        "colour": colour_report(),
    }


def _print_audit() -> Dict[str, object]:
    audit = geometry_audit()
    print("=" * 78)
    print("  GLM GEOMETRY  —  versor / fibre layer self-audit")
    print("=" * 78)

    qg = audit["quaternion_group"]
    print(f"\n  quaternion units          : {qg['order']}, closed={qg['closed']}, "
          f"associative={qg['associative']}")
    print(f"  Q8 relations              : all hold = {qg['relations_all_hold']}")
    print(f"  fibre map Z_4 -> {{1,i,j,k}}: bijective={qg['fibre_map_bijective']}, "
          f"homomorphism={qg['fibre_map_is_homomorphism']}")

    nc = audit["fibre_noncommutativity"]
    print(f"\n  order-sensitive fibre words: {nc['order_sensitive']} of {nc['tested']}")

    wr = audit["winding"]
    print(f"\n  closed walks               : {wr['closed_walks']}, "
          f"all windings integral = {wr['all_windings_integral']}")
    print(f"  windings observed          : {wr['windings']}")
    print(f"  E = mc^2 round trip        : winding "
          f"{wr['emc2_roundtrip']['winding']}")

    ho = audit["holonomy"]
    print(f"\n  loops                      : {ho['loops']}, path-dependent "
          f"{ho['path_dependent_loops']}, telescoping "
          f"{ho['telescoping_identity_holds']}")

    cg = audit["conformal_grading"]
    print(f"\n  H^6 norm^2 always 6        : {cg['h6_norm_sq_always_six']}")
    print(f"  archive L0 == sigma/2      : {cg['archive_L0_equals_half_syndrome']}")

    va = audit["vacua"]
    print(f"\n  vacua in {va['box']:>12}      : {va['lawful']} of {va['searched']}")

    co = audit["colour"]
    print(f"\n  chromatic ground states    : {co['ground_states']} "
          f"(one colour in {co['ground_state_fraction_one_in']})")
    for entry in co["concept_colours"]:            # type: ignore[union-attr]
        print(f"    {entry['concept']:<10} {entry['colour']} -> "
              f"{entry['snapped_colour']}  (d = {entry['distance']})")
    print()
    return audit


if __name__ == "__main__":
    _print_audit()
