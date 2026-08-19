#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM-2 REASONER  —  the companion implementation
================================================================================

  Part of:  The Geometric Language Machine, second generation (GLM-2).
  Role   :  the working system that the paper (glm2_paper.py) describes.
  Deps   :  glm2_meaning, glm2_library, glm2_parse, glm2_lattice, glm2_codec,
            glm2_conway, glm2_axial.

  This is the part you use.  Everything it reports is exact: rational
  arithmetic end to end, integer lattice arithmetic in the carrier, and no
  tolerance parameters anywhere.

  What it does
  ------------
    audit(lhs, rhs)      exact admissibility of an equation, with a full
                         breakdown (dimension / decimal scale / tensor rank /
                         P, T, C parity / nominal kind), and a report of what
                         a mod-2 carrier would have concluded
    solve(target, srcs)  the exact rational exponents that build the target
                         out of the sources, or a statement that no pathway
                         exists; returns the general solution when the
                         sources are dependent
    pi_groups(names)     a basis of the dimensionless groups (Buckingham Pi)
                         over Q, exactly
    telemetry(name)      the carrier: Leech point, norm, coordinates, the
                         mod-2 class, the nominal data
    transmit(name, err)  encode, corrupt, repair — and show that the repair
                         restores the concept exactly
    neighbours(name)     the concepts nearest to a given one in the carrier
    symmetry(name)       what Aut(Lambda) = Co_0 does to a carrier
    convert(a, b)        the exact decimal factor between two commensurable
                         quantities (km -> m, GHz -> Hz, ...)
    identify(expr)       read an expression of the operator algebra and say
                         which register concepts it IS (at full meaning) and
                         which merely share its dimensions

  Command line
  ------------
      python3 glm2_reasoner.py                       demonstration suite
      python3 glm2_reasoner.py check energy "mass*speed^2"
      python3 glm2_reasoner.py check energy "mass*speed^4"
      python3 glm2_reasoner.py check energy torque
      python3 glm2_reasoner.py solve energy mass speed
      python3 glm2_reasoner.py solve speed energy mass
      python3 glm2_reasoner.py pi force density speed length
      python3 glm2_reasoner.py show energy
      python3 glm2_reasoner.py transmit energy 5
      python3 glm2_reasoner.py near energy
      python3 glm2_reasoner.py convert kilometre length
      python3 glm2_reasoner.py name "moment(position, force)"
      python3 glm2_reasoner.py name "dot(force, position)"
      python3 glm2_reasoner.py check torque "moment(position, force)"
      python3 glm2_reasoner.py symmetry energy
      python3 glm2_reasoner.py list mechanics
================================================================================
"""

from __future__ import annotations

import sys
from fractions import Fraction as F
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from glm2_axial import nullspace, rref
from glm2_codec import (N_CONTEXT, SLOTS, coords_of, decode_point, encode,
                        repair)
from glm2_conway import GENERATORS, f2_matrix
from glm2_lattice import DIM, decode, in_leech, norm2, to_coords
from glm2_library import (AFFINE_SCALES, ALIASES, CONCEPTS, DOMAINS, KINDS,
                          Concept, by_domain, lookup)
from glm2_meaning import (AXES, DENOM, Meaning, ParseError, mod2_confusable,
                          mod2_shadow)
from glm2_parse import parse

__all__ = ["Reasoner", "REASONER", "EquationAudit", "Solution", "main"]


# ══════════════════════════════════════════════════════════════════════════════
# §1.  RESULT TYPES
# ══════════════════════════════════════════════════════════════════════════════

class EquationAudit:
    """
    The verdict on 'lhs = rhs', with every reason spelled out.

    The verdict is exact commensurability of the two meanings.  It is the only
    verdict: no weaker substrate's opinion travels with it.  What an F_2
    carrier would have concluded is measurable in the appendix method
    `Reasoner.mod2_ceiling`, and nothing here consults it.
    """

    def __init__(self, lhs_text: str, rhs_text: str, lhs: Meaning,
                 rhs: Meaning) -> None:
        self.lhs_text = lhs_text
        self.rhs_text = rhs_text
        self.lhs = lhs
        self.rhs = rhs
        self.dimension_ok = lhs.same_dimension(rhs)
        self.scale_ok = lhs.scale == rhs.scale
        self.rank_ok = lhs.rank == rhs.rank
        self.parity_ok = (lhs.p, lhs.t_parity(), lhs.c_parity()) == \
                         (rhs.p, rhs.t_parity(), rhs.c_parity())
        self.kind_ok = not (lhs.kind and rhs.kind and lhs.kind != rhs.kind)
        self.admissible = lhs.commensurable(rhs)
        self.residual = lhs - rhs

    def reasons(self) -> List[str]:
        out = []
        if not self.dimension_ok:
            diff = " ".join(
                f"{ax}^{a - b}" for ax, a, b in zip(AXES, self.lhs.exps,
                                                    self.rhs.exps) if a != b)
            out.append(f"dimensions differ by {diff}")
        if not self.scale_ok:
            out.append(f"decimal scale differs by 10^"
                       f"{self.lhs.scale - self.rhs.scale}")
        if not self.rank_ok:
            out.append(f"tensor rank {self.lhs.rank} vs {self.rhs.rank}")
        if not self.parity_ok:
            names = [n for n, a, b in zip(
                ("P", "T", "C"),
                (self.lhs.p, self.lhs.t_parity(), self.lhs.c_parity()),
                (self.rhs.p, self.rhs.t_parity(), self.rhs.c_parity()))
                if a != b]
            out.append("parity mismatch: " + ", ".join(names))
        if not self.kind_ok:
            out.append(f"nominal kind {KINDS.get(self.lhs.kind)} vs "
                       f"{KINDS.get(self.rhs.kind)}")
        return out

    def __str__(self) -> str:
        head = "ADMISSIBLE" if self.admissible else "REJECTED"
        lines = [f"{head}: {self.lhs_text} = {self.rhs_text}",
                 f"  left  {self.lhs}",
                 f"  right {self.rhs}"]
        for r in self.reasons():
            lines.append(f"  ! {r}")
        return "\n".join(lines)


class Solution:
    """The exact exponents that build a target out of given sources."""

    def __init__(self, target: str, sources: Sequence[str],
                 exponents: Optional[Sequence[F]],
                 kernel: Sequence[Sequence[F]], note: str = "") -> None:
        self.target = target
        self.sources = list(sources)
        self.exponents = None if exponents is None else list(exponents)
        self.kernel = [list(k) for k in kernel]
        self.note = note

    @property
    def solvable(self) -> bool:
        return self.exponents is not None

    def formula(self) -> str:
        if self.exponents is None:
            return f"no pathway to {self.target} from {', '.join(self.sources)}"
        terms = []
        for name, e in zip(self.sources, self.exponents):
            if e == 0:
                continue
            terms.append(name if e == 1 else f"{name}^{_exp_str(e)}")
        body = " * ".join(terms) if terms else "1"
        return f"{self.target} = {body}"

    def __str__(self) -> str:
        lines = [self.formula()]
        if self.kernel:
            lines.append(f"  {len(self.kernel)} dimensionless degree(s) of "
                         f"freedom remain")
        if self.note:
            lines.append(f"  {self.note}")
        return "\n".join(lines)


def _exp_str(e: F) -> str:
    return str(e.numerator) if e.denominator == 1 else f"({e})"


# ══════════════════════════════════════════════════════════════════════════════
# §2.  THE REASONER
# ══════════════════════════════════════════════════════════════════════════════

class Reasoner:
    """The GLM-2 system: exact semantics on a Leech-lattice carrier."""

    def __init__(self) -> None:
        self._cache: Dict[str, Tuple[int, ...]] = {}

    # ── resolution ───────────────────────────────────────────────────────────
    def meaning(self, text: str) -> Meaning:
        con = lookup(text)
        if con is not None:
            return con.meaning
        return parse(text)

    def concept(self, name: str) -> Optional[Concept]:
        return lookup(name)

    def carrier(self, text: str) -> Tuple[int, ...]:
        """
        The Leech point of a concept: a DERIVED quantity, `encode(meaning)`.

        The cache is a cache and nothing else — it is keyed by the text whose
        meaning produced the point, holds no information that is not in the
        meaning, and can be dropped at any time without changing an answer.
        There is no way to give a concept a carrier that its meaning does not
        produce, because a carrier is never an input anywhere in GLM-2.
        """
        if text in self._cache:
            return self._cache[text]
        x = encode(self.meaning(text))
        self._cache[text] = x
        return x

    def carrier_is_derived(self, text: str) -> bool:
        """Re-derive the carrier and decode it: `decode(encode(m)) == m`."""
        m = self.meaning(text)
        x = self.carrier(text)
        back, _ctx = decode_point(list(x))
        return tuple(encode(m)) == tuple(x) and back == m

    # ── equations ────────────────────────────────────────────────────────────
    def audit(self, lhs: str, rhs: str) -> EquationAudit:
        return EquationAudit(lhs, rhs, self.meaning(lhs), self.meaning(rhs))

    def convert(self, a: str, b: str) -> Optional[str]:
        """The exact decimal factor taking quantity a to quantity b."""
        ma, mb = self.meaning(a), self.meaning(b)
        if not ma.same_dimension(mb) or ma.rank != mb.rank:
            return None
        power = ma.scale - mb.scale
        return f"1 {a} = 10^{power} {b}"

    # ── synthesis ────────────────────────────────────────────────────────────
    def solve(self, target: str, sources: Sequence[str]) -> Solution:
        """
        Find exact rational exponents x with sum_i x_i * meaning(source_i)
        = meaning(target), over the eleven-dimensional rational part
        (exponents and decimal scale), then check the integer-only fields.
        """
        tm = self.meaning(target)
        sms = [self.meaning(s) for s in sources]
        rows = []
        for k in range(len(AXES) + 1):
            rows.append([m.vector()[k] for m in sms] + [tm.vector()[k]])
        R, pivots = rref(rows)
        n = len(sms)
        if n in pivots:
            return Solution(target, sources, None, [],
                            "the target is outside the span of the sources")
        particular = [F(0)] * n
        for i, pc in enumerate(pivots):
            particular[pc] = R[i][n]
        kernel = nullspace([row[:n] for row in rows], n)

        # integer-only fields: rank and the three parities
        note = ""
        rank = sum(x * m.rank for x, m in zip(particular, sms))
        if rank != tm.rank:
            note = (f"warning: tensor rank {rank} of the product does not "
                    f"match the target's {tm.rank}")
        if any(x.denominator != 1 for x in particular):
            odd = [m for x, m in zip(particular, sms)
                   if x.denominator != 1 and (m.p or m.t or m.c or m.rank)]
            if odd:
                note = ("fractional power of a parity-odd or tensor quantity: "
                        "the pathway is dimensionally valid but not a legal "
                        "product of these quantities")
        return Solution(target, sources, particular, kernel, note)

    def pi_groups(self, names: Sequence[str]) -> List[Dict[str, F]]:
        """A basis of the dimensionless combinations of the given quantities."""
        ms = [self.meaning(n) for n in names]
        rows = [[m.vector()[k] for m in ms] for k in range(len(AXES) + 1)]
        basis = nullspace(rows, len(ms))
        out = []
        for v in basis:
            out.append({n: e for n, e in zip(names, v) if e != 0})
        return out

    # ── the carrier ──────────────────────────────────────────────────────────
    def telemetry(self, name: str) -> Dict[str, object]:
        m = self.meaning(name)
        x = self.carrier(name)
        u = to_coords(list(x))
        con = lookup(name)
        return {
            "concept": name,
            "meaning": str(m),
            "unit": None if con is None else con.unit,
            "gloss": None if con is None else con.gloss,
            "domain": DOMAINS.get(m.domain),
            "nominal_kind": KINDS.get(m.kind),
            "rank": m.rank,
            "parities": {"P": m.p, "T": m.t, "C": m.c},
            "pseudo": m.is_pseudo(),
            "slots": dict(zip(SLOTS, u or [])),
            "carrier_norm2": norm2(x),
            "carrier_in_lattice": in_leech(list(x)),
            "carrier_is_derived": tuple(encode(m)) == tuple(x),
            "carrier_head": tuple(x[:6]),
        }

    def mod2_ceiling(self, pairs: Sequence[Tuple[str, str]]
                     ) -> Dict[str, object]:
        """
        APPENDIX (not part of any verdict).  What the rejected F_2 carrier
        would have concluded about these pairs, kept as a measurement of why
        meaning is primary here.  See `glm2_meaning` §3.
        """
        rows = []
        confused = 0
        for a, b in pairs:
            ma, mb = self.meaning(a), self.meaning(b)
            admissible = ma.commensurable(mb)
            would = ma == mb or mod2_confusable(ma, mb)
            fooled = would and not admissible
            confused += fooled
            rows.append({"pair": f"{a} = {b}",
                         "admissible": admissible,
                         "mod2_would_accept": would,
                         "mod2_false_positive": fooled,
                         "mod2_shadow_of_left": mod2_shadow(ma)})
        return {"records": rows, "total": len(rows),
                "mod2_false_positives": confused}

    def transmit(self, name: str, weight: int = 5,
                 seed: int = 20250816) -> Dict[str, object]:
        """
        Encode a concept, corrupt the carrier with an error of squared
        magnitude `weight`, and repair it.  Errors of squared magnitude at
        most 7 are always repaired exactly.
        """
        import random
        rng = random.Random(seed)
        m = self.meaning(name)
        x = self.carrier(name)
        err = [0] * DIM
        positions = rng.sample(range(DIM), min(weight, DIM))
        for i in positions:
            err[i] = rng.choice((-1, 1))
        y = [a + b for a, b in zip(x, err)]
        res = repair(y, expected=m)
        return {
            "concept": name,
            "error_norm2": norm2(err),
            "within_packing_radius": res.within_radius,
            "repaired_exactly": res.exact,
            "recovered": str(res.meaning),
            "carrier_restored": tuple(res.point) == tuple(x),
        }

    def neighbours(self, name: str, count: int = 6) -> List[Tuple[str, int]]:
        """The library concepts whose carriers are nearest to this one."""
        x = self.carrier(name)
        out = []
        for other in CONCEPTS:
            if other == name:
                continue
            y = self.carrier(other)
            out.append((other, norm2([a - b for a, b in zip(x, y)])))
        out.sort(key=lambda t: (t[1], t[0]))
        return out[:count]

    def symmetry(self, name: str) -> Dict[str, object]:
        """
        What Aut(Lambda) = Co_0 does to a carrier: it preserves the lattice
        and the norm, and moves the point to another lattice point, which in
        general does NOT carry a meaning.  The symmetry group is a symmetry of
        the carrier, not of the semantics, and this reports exactly that.
        """
        x = self.carrier(name)
        images = []
        meaningful = 0
        for g in GENERATORS[:6]:
            y = g(list(x))
            same_norm = norm2(y) == norm2(x)
            try:
                decode_point(y)
                readable = True
            except ValueError:
                readable = False
            meaningful += 1 if readable else 0
            images.append({"generator": g.name, "norm_preserved": same_norm,
                           "carries_a_meaning": readable})
        return {
            "concept": name,
            "carrier_norm2": norm2(x),
            "generators_tested": len(images),
            "norm_preserved_by_all": all(i["norm_preserved"] for i in images),
            "images_that_carry_a_meaning": meaningful,
            "detail": images,
        }

    # ── library views ────────────────────────────────────────────────────────
    def list_concepts(self, domain: Optional[str] = None) -> List[str]:
        if domain is None:
            return sorted(CONCEPTS)
        table = by_domain()
        return table.get(domain, [])

    def identify(self, text: str) -> Dict[str, object]:
        """
        Read an expression and say what it is.

        Returns the meaning, the register concepts whose FULL meaning it
        matches (rank and parities included), and the ones that match only
        dimensionally — the near misses, which are exactly the confusions a
        dimension-only system would make.
        """
        m = self.meaning(text)
        exact = sorted(n for n, c in CONCEPTS.items()
                       if c.meaning.same_quantity(m))
        loose = sorted(n for n, c in CONCEPTS.items()
                       if c.meaning.same_dimension(m)
                       and not c.meaning.same_quantity(m))
        return {
            "expression": text,
            "meaning": str(m),
            "is": exact,
            "same dimensions only": loose,
            "carrier_norm2": norm2(encode(m)),
        }

    def summary(self) -> Dict[str, object]:
        return {
            "concepts": len(CONCEPTS),
            "aliases": len(ALIASES),
            "domains": len(by_domain()),
            "affine_scales": len(AFFINE_SCALES),
            "axes": len(AXES),
            "carrier": "Leech lattice Lambda_24",
            "carrier_capacity": "countably infinite",
            "minimum_carrier_separation_squared": 32,
        }


REASONER = Reasoner()


# ══════════════════════════════════════════════════════════════════════════════
# §3.  DEMONSTRATION SUITE
# ══════════════════════════════════════════════════════════════════════════════

def demonstrate() -> None:
    R = REASONER
    line = "─" * 78

    print(line)
    print("GLM-2 REASONER — demonstration")
    print(line)
    for k, v in R.summary().items():
        print(f"  {k:38s} {v}")

    print(f"\n{line}\n1.  EQUATION AUDIT — exact, and what mod 2 would say\n{line}")
    for lhs, rhs in [("energy", "mass*speed^2"),
                     ("energy", "mass*speed^4"),
                     ("energy", "torque"),
                     ("frequency", "activity"),
                     ("torque", "energy/angle"),
                     ("radiance", "irradiance"),
                     ("kilometre", "length"),
                     ("force", "mass*acceleration"),
                     ("angular_momentum", "moment_of_inertia*angular_velocity"),
                     ("information_rate", "bandwidth")]:
        print(R.audit(lhs, rhs))
        print()

    print(f"{line}\n2.  SYNTHESIS — exact rational exponents\n{line}")
    for target, sources in [("energy", ["mass", "speed"]),
                            ("speed", ["energy", "mass"]),
                            ("power", ["current", "resistance"]),
                            ("fracture_toughness", ["stress", "length"]),
                            ("reduced_planck", ["action", "angle"]),
                            ("landauer_energy", ["boltzmann_constant",
                                                 "temperature",
                                                 "information"]),
                            ("energy", ["length", "time"])]:
        print(R.solve(target, sources))
        print()

    print(f"{line}\n3.  DIMENSIONLESS GROUPS\n{line}")
    for names in (["force", "density", "speed", "length"],
                  ["speed", "length", "kinematic_viscosity"],
                  ["speed", "sound_speed"],
                  ["information_rate", "bandwidth", "spectral_efficiency"]):
        groups = R.pi_groups(names)
        print(f"  {names}")
        for g in groups:
            print("      " + " * ".join(f"{n}^{_exp_str(e)}"
                                        for n, e in g.items()))
        if not groups:
            print("      (none)")
        print()

    print(f"{line}\n4.  THE CARRIER\n{line}")
    for name in ("energy", "torque", "information_rate"):
        t = R.telemetry(name)
        print(f"  {name}")
        for k in ("meaning", "unit", "domain", "nominal_kind", "rank",
                  "parities", "carrier_norm2", "carrier_in_lattice",
                  "carrier_head"):
            print(f"      {k:22s} {t[k]}")
        print()

    print(f"{line}\n5.  TRANSMISSION AND EXACT REPAIR\n{line}")
    for name in ("energy", "radiance", "gigabit_per_second"):
        for w in (3, 7):
            r = R.transmit(name, w)
            print(f"  {name:22s} error^2 = {r['error_norm2']:2d}  "
                  f"within radius {str(r['within_packing_radius']):5s}  "
                  f"repaired exactly {r['repaired_exactly']}")
    print()

    print(f"{line}\n6.  CARRIER NEIGHBOURHOODS\n{line}")
    for name in ("energy", "torque"):
        print(f"  {name}: " + ", ".join(f"{n} ({d})"
                                        for n, d in R.neighbours(name, 5)))
    print()

    print(f"{line}\n7.  SYMMETRY OF THE CARRIER (Co_0)\n{line}")
    s = REASONER.symmetry("energy")
    print(f"  norm preserved by every generator : {s['norm_preserved_by_all']}")
    print(f"  images that still carry a meaning : "
          f"{s['images_that_carry_a_meaning']} of {s['generators_tested']}")
    print("  Co_0 is a symmetry of the carrier, not of the semantics: it")
    print("  permutes lattice points, and almost none of the images is in the")
    print("  image of the encoder.")
    print()

    print(f"{line}\n8.  UNIT CONVERSION\n{line}")
    for a, b in (("kilometre", "length"), ("gigahertz", "frequency"),
                 ("megapascal", "pressure"), ("gigabit", "information")):
        print(f"  {R.convert(a, b)}")
    print()

    print(f"{line}\n9.  THE OPERATOR ALGEBRA — naming what an expression is\n"
          f"{line}")
    for text in ("dot(force, position)",
                 "force * position",
                 "moment(position, momentum)",
                 "moment(position, force)",
                 "cross(electric_field, magnetic_field_h)",
                 "curl(magnetic_field_h)",
                 "rot(velocity)",
                 "grad(voltage)",
                 "div(electric_displacement)",
                 "ddt(momentum)",
                 "integral_dV(energy_density)"):
        info = R.identify(text)
        names = ", ".join(info["is"]) or "(no register concept)"
        print(f"  {text:42s} {info['meaning']}")
        print(f"  {'':42s} is: {names}")
    print()


# ══════════════════════════════════════════════════════════════════════════════
# §4.  COMMAND LINE
# ══════════════════════════════════════════════════════════════════════════════

def main(argv: Sequence[str]) -> int:
    R = REASONER
    if not argv:
        demonstrate()
        return 0
    cmd, args = argv[0], list(argv[1:])
    try:
        if cmd == "check" and len(args) == 2:
            print(R.audit(args[0], args[1]))
        elif cmd == "solve" and len(args) >= 2:
            print(R.solve(args[0], args[1:]))
        elif cmd == "pi" and args:
            groups = R.pi_groups(args)
            if not groups:
                print("no dimensionless group")
            for g in groups:
                print(" * ".join(f"{n}^{_exp_str(e)}" for n, e in g.items()))
        elif cmd == "show" and len(args) == 1:
            for k, v in R.telemetry(args[0]).items():
                print(f"{k:22s} {v}")
        elif cmd == "transmit" and args:
            weight = int(args[1]) if len(args) > 1 else 5
            for k, v in R.transmit(args[0], weight).items():
                print(f"{k:24s} {v}")
        elif cmd == "near" and args:
            for n, d in R.neighbours(args[0], 10):
                print(f"{d:10d}  {n}")
        elif cmd == "name" and len(args) == 1:
            for k, v in R.identify(args[0]).items():
                print(f"{k:24s} {v}")
        elif cmd == "convert" and len(args) == 2:
            print(R.convert(args[0], args[1]) or "not commensurable")
        elif cmd == "symmetry" and args:
            for k, v in R.symmetry(args[0]).items():
                if k != "detail":
                    print(f"{k:34s} {v}")
        elif cmd == "list":
            if args:
                for n in R.list_concepts(args[0]):
                    print(n)
            else:
                for d, names in by_domain().items():
                    print(f"{d} ({len(names)})")
        else:
            print(__doc__.split("Command line")[1])
            return 1
    except (ParseError, ValueError) as exc:
        print(f"error: {exc}")
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
