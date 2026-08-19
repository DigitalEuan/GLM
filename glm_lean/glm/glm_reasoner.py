#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM GEOMETRIC REASONER  —  the companion implementation
================================================================================

  Part of:  The Geometric Language Machine (GLM)
  Layer  :  Tier 3 — the operational engine.
  Deps   :  glm_substrate.py, glm_codec.py, glm_metrology.py, glm_linalg.py

  This is the module a user of the GLM actually calls.  It holds concepts as
  exact meanings in (Z^7, +) — the only state in the system — derives the
  Golay/MOG/Leech substrate view of each one from that meaning, and exposes
  five capabilities:

    §1  Concept        a quantity — its exact meaning in (Z^7,+), which is
                       the whole of its state — together with the derived
                       views of that meaning: the 24-bit carrier, the MOG
                       shadow, the snap telemetry and the cost metrics
    §2  audit          check a proposed equation exactly, in (Z^7,+)
    §3  solve          synthesise a target quantity from given inputs, over Z
                       when possible and over Q (fractional powers) otherwise
    §4  pi_groups      complete, exact Buckingham-Pi analysis of an input set
    §5  scene          export a 3D scene of concepts for visualisation

  and, for display only, the optional layers of paper sections 8 to 10: the
  versor index of a concept, its quaternionic fibre product, its colour, the
  winding number of a walk through concepts, the M24 orbit of a carrier word,
  and the Leech dimension ledger.  No verdict depends on any of it (invariant
  I7 of the paper).

  Run it directly for a demonstration of all five:

      python3 glm_reasoner.py                 # full demonstration suite
      python3 glm_reasoner.py check "energy" "mass*speed^2"
      python3 glm_reasoner.py solve energy mass speed
      python3 glm_reasoner.py pi force density speed length
      python3 glm_reasoner.py show energy
      python3 glm_reasoner.py colour energy
      python3 glm_reasoner.py walk energy mass speed speed energy
      python3 glm_reasoner.py holonomy energy mass speed
      python3 glm_reasoner.py symmetry energy       # the M24 orbit of a word
      python3 glm_reasoner.py m24                   # Aut(Golay) = M24, computed
      python3 glm_reasoner.py ledger                # 1+299+98280+98304=196884
      python3 glm_reasoner.py list
================================================================================
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from fractions import Fraction
from functools import cached_property
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from glm_codec import DimCarrier, MOGCodec, MOGShadow, ontological_profile
from glm_geometry import (Walk, colour_of_word, fibre_product, h6_norm_sq,
                          versor_index, versor_symbol, walk_of_names)
from glm_geometry import holonomy as _loop_holonomy
from glm_linalg import kernel_basis, matvec, solve_integer_system, solve_rational_system
from glm_metrology import (QUANTITIES, Dimension, EquationAudit, ParseError,
                           audit_equation, mod2_would_accept,
                           parse_expression, resolve)
from glm_substrate import GOLAY, LEECH, SnapMeta

__all__ = [
    "Concept", "Solution", "GeometricReasoner", "REASONER",
    "run_demonstration",
]


# ══════════════════════════════════════════════════════════════════════════════
# §1.  CONCEPT — the meaning is the state, the bits are derived from it
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class _Substrate:
    """The derived substrate view of one meaning.  Never constructed by hand."""

    word: Tuple[int, ...]
    shadow: MOGShadow
    snap: SnapMeta
    snapped: Tuple[int, ...]
    tax: Fraction
    nrci: Fraction


def derive_substrate(dim: Dimension) -> Optional[_Substrate]:
    """
    The whole substrate view of a meaning, as a pure function of the meaning.

    `None` when the meaning falls outside the representable box [-4,4]^7,
    which is a property of the encoder, not a state of the concept.
    """
    if not DimCarrier.in_range(dim.exps):
        return None
    word = DimCarrier.encode(dim.exps)
    snapped, meta = GOLAY.snap(word)
    return _Substrate(
        word=tuple(word),
        shadow=MOGCodec.project(word, aligned=True),
        snap=meta,
        snapped=tuple(snapped),
        tax=LEECH.tax(word),
        nrci=LEECH.nrci(word),
    )


@dataclass(frozen=True)
class Concept:
    """
    A named quantity.  Its MEANING is the only state; the bits are derived.

    A concept is a label (name, symbol, unit) attached to

      dim            the exact dimension vector in Z^7 - the concept itself.

    Everything substrate-shaped is a *derived view*: recomputed from `dim` by
    `derive_substrate`, cached, never stored independently and never settable
    (the record is frozen and every view below is a read-only property):

      carrier        the 24-bit word `encode(dim)`, or None if some exponent
                     falls outside the representable box [-4, 4]
      shadow         the MOG projection of that word (hexacode symbols +
                     fibre keys); losslessly invertible
      snap           decoder telemetry: syndrome, distance to the code, and
                     how many codewords were tied at that distance
      lawful         True when the derived word is itself a Golay codeword
      tax, nrci      the stipulative UBP cost metrics (exact Fractions)

    So the system has exactly one direction of dependence,

        meaning  --encode-->  bits  --decode-->  meaning,

    and `carrier_is_derived` checks both halves of it at runtime.  Two
    concepts with the same meaning necessarily carry the same bits, and a
    concept cannot be given bits that disagree with its meaning because it is
    never given bits at all.  Composition and every verdict happen in
    (Z^7, +); the bits are read only for geometry, colour, symmetry and
    transport, and are composed nowhere.

    Everything structural (dim, carrier, shadow, snap) is exact; `tax` and
    `nrci` are a separable modelling layer and no decision depends on them.
    """

    name: str
    dim: Dimension
    symbol: str = ""
    unit: str = ""

    # -- the derived substrate view -------------------------------------------
    @cached_property
    def substrate(self) -> Optional[_Substrate]:
        """The derived substrate view (cached; a pure function of `dim`)."""
        return derive_substrate(self.dim)

    @property
    def carrier(self) -> Optional[List[int]]:
        s = self.substrate
        return None if s is None else list(s.word)

    @property
    def shadow(self) -> Optional[MOGShadow]:
        s = self.substrate
        return None if s is None else s.shadow

    @property
    def snap(self) -> Optional[SnapMeta]:
        s = self.substrate
        return None if s is None else s.snap

    @property
    def snapped_carrier(self) -> Optional[List[int]]:
        s = self.substrate
        return None if s is None else list(s.snapped)

    @property
    def lawful(self) -> bool:
        s = self.substrate
        return s is not None and s.snap.distance == 0

    @property
    def tax(self) -> Optional[Fraction]:
        s = self.substrate
        return None if s is None else s.tax

    @property
    def nrci(self) -> Optional[Fraction]:
        s = self.substrate
        return None if s is None else s.nrci

    # -- views ----------------------------------------------------------------
    @property
    def representable(self) -> bool:
        return self.substrate is not None

    def with_meaning(self, dim: Dimension) -> "Concept":
        """The same label with a different meaning; the bits follow the meaning."""
        return Concept(self.name, dim, self.symbol, self.unit)

    def carrier_is_derived(self) -> bool:
        """
        The defining invariant of the architecture, checked at runtime.

        The bits this concept shows are exactly what the encoder produces from
        its meaning, and decoding them returns that meaning unchanged.  For a
        meaning outside the representable box there are no bits at all, which
        is the honest answer rather than a truncation.
        """
        if not DimCarrier.in_range(self.dim.exps):
            return self.carrier is None
        word = self.carrier
        return (word is not None
                and word == DimCarrier.encode(self.dim.exps)
                and DimCarrier.decode(word) == list(self.dim.exps))

    def round_trip_ok(self) -> bool:
        """Meaning -> carrier -> MOG shadow -> carrier -> meaning, losslessly."""
        if self.carrier is None or self.shadow is None:
            return False
        recovered = MOGCodec.reconstruct(self.shadow)
        return (recovered == self.carrier
                and DimCarrier.decode(recovered) == list(self.dim.exps)
                and self.carrier_is_derived())

    def nearest_lawful_dims(self) -> Optional[List[int]]:
        """
        The dimension vector of the snapped carrier, if the snapped word is
        still inside the carrier's image.  This is the honest reading of
        "snap to the nearest lawful concept": sometimes the nearest codeword
        is not a representable dimension vector at all, and we say so.
        """
        if self.snapped_carrier is None:
            return None
        return DimCarrier.decode(self.snapped_carrier)

    def profile(self) -> Dict[str, List[int]]:
        return ontological_profile(self.dim.exps)

    def geometry(self) -> Optional[Dict[str, object]]:
        """
        The optional fibre geometry of paper section 9, for display.

        Nothing here participates in a decision: `versor_index` is the sum of
        the six Z_4 fibre keys, `fibre_product` their ordered quaternion
        product, `grading` the observable that earlier versions called L0
        (exactly half the syndrome weight), and `colour` the carrier read as
        #RRGGBB.
        """
        if self.carrier is None or self.snap is None:
            return None
        snapped = self.snapped_carrier or self.carrier
        return {
            "versor_index": versor_index(self.carrier),
            "versor": versor_symbol(self.carrier),
            "fibre_product": str(fibre_product(self.carrier)),
            "fibre_product_reversed": str(fibre_product(self.carrier,
                                                        reverse=True)),
            "order_sensitive": fibre_product(self.carrier)
            != fibre_product(self.carrier, reverse=True),
            "h6_norm_sq": h6_norm_sq(self.carrier),
            "grading": f"{self.snap.syndrome_weight}/2",
            "colour": colour_of_word(self.carrier),
            "snapped_colour": colour_of_word(snapped),
        }

    def telemetry(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "symbol": self.symbol,
            "unit": self.unit,
            "dims": list(self.dim.exps),
            "dims_str": str(self.dim),
            "representable": self.representable,
            "carrier_int": None if self.carrier is None else
            sum(b << i for i, b in enumerate(self.carrier)),
            "carrier_weight": None if self.carrier is None else sum(self.carrier),
            "hexacode_shadow": None if self.shadow is None else list(self.shadow.labels),
            "fibre_keys": None if self.shadow is None else list(self.shadow.fibres),
            "shadow_is_hexacode_word": None if self.shadow is None
            else self.shadow.is_hexacode_word(),
            "syndrome": None if self.snap is None else self.snap.syndrome,
            "syndrome_weight": None if self.snap is None else self.snap.syndrome_weight,
            "snap_distance": None if self.snap is None else self.snap.distance,
            "snap_ties": None if self.snap is None else self.snap.tie_count,
            "snap_status": None if self.snap is None else self.snap.status,
            "lawful": self.lawful,
            "codec_round_trip_ok": self.round_trip_ok(),
            "tax": None if self.tax is None else float(self.tax),
            "nrci": None if self.nrci is None else float(self.nrci),
            "profile": self.profile(),
            "geometry": self.geometry(),
        }

    def __str__(self) -> str:
        return f"{self.name} [{self.symbol}] = {self.dim}"


# ══════════════════════════════════════════════════════════════════════════════
# §3.  SOLUTIONS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Solution:
    """The result of a target-synthesis query."""

    status: str                    # "integer" | "fractional" | "impossible"
    target: str
    inputs: List[str]
    exponents: List[Fraction]
    alternatives: List[List[Fraction]]
    pi_group_count: int
    detail: str = ""

    @property
    def found(self) -> bool:
        return self.status in ("integer", "fractional")

    def formula(self) -> str:
        return _render_formula(self.target, self.inputs, self.exponents)

    def proof_steps(self) -> List[str]:
        if not self.found:
            return [f"No dimensional pathway: {self.detail}"]
        steps = [
            f"1. target dimension: {self.target} = "
            f"{resolve(self.target) if resolve(self.target) else ''}",
            "2. inputs: " + ", ".join(f"{n} = {resolve(n)}" for n in self.inputs),
            "3. solve A x = t over " + ("Z" if self.status == "integer" else "Q")
            + " where the columns of A are the input dimensions",
            "4. solution: " + self.formula(),
        ]
        if self.pi_group_count:
            steps.append(
                f"5. the input set carries {self.pi_group_count} independent "
                f"dimensionless group(s), so the exponents are unique only up "
                f"to those groups ({len(self.alternatives)} equally simple "
                f"alternative(s) found)"
            )
        else:
            steps.append("5. the input set carries no dimensionless group, so "
                         "these exponents are the unique solution")
        return steps


def _fmt_exp(e: Fraction) -> str:
    if e.denominator == 1:
        return str(e.numerator)
    return f"{e.numerator}/{e.denominator}"


def _render_formula(target: str, inputs: Sequence[str],
                    exps: Sequence[Fraction]) -> str:
    num, den = [], []
    for name, e in zip(inputs, exps):
        if e == 0:
            continue
        mag = abs(e)
        term = name if mag == 1 else f"{name}^{_fmt_exp(mag)}"
        (num if e > 0 else den).append(term)
    lhs = " * ".join(num) if num else "1"
    if den:
        lhs += " / (" + " * ".join(den) + ")" if len(den) > 1 else " / " + den[0]
    return f"{target} = {lhs}"


# ══════════════════════════════════════════════════════════════════════════════
# §2-§5.  THE REASONER
# ══════════════════════════════════════════════════════════════════════════════

class GeometricReasoner:
    """
    The GLM engine.  Construction builds a Concept for every named quantity in
    the metrology library; all queries are exact and deterministic.
    """

    def __init__(self) -> None:
        self.concepts: Dict[str, Concept] = {}
        for name, (dim, symbol, unit) in QUANTITIES.items():
            self.concepts[name] = Concept(name, dim, symbol, unit)

    # ── resolution ───────────────────────────────────────────────────────────
    def concept(self, key: str) -> Optional[Concept]:
        k = key.strip().lower()
        if k in self.concepts:
            return self.concepts[k]
        dim = resolve(k)
        if dim is None:
            return None
        for c in self.concepts.values():           # alias of a known concept
            if c.dim == dim and (c.name == k or c.symbol.lower() == k):
                return c
        return Concept(k, dim)

    def concept_of_expression(self, expr: str) -> Concept:
        """Build an (anonymous) Concept for an arbitrary expression."""
        return Concept(expr.strip(), parse_expression(expr))

    def identify(self, dim: Dimension) -> List[str]:
        """All library names sharing this dimension (may be several, or none)."""
        return sorted(n for n, c in self.concepts.items() if c.dim == dim)

    # ── §2  equation audit ───────────────────────────────────────────────────
    def audit(self, lhs: str, rhs: str, label: str = "") -> Dict[str, object]:
        """
        Check a proposed equation.

        The verdict is exact equality of the two meanings in (Z^7, +) and
        there is only one of it: no second opinion from any weaker substrate
        travels alongside a decision.  The record also carries the derived
        substrate telemetry of both sides, which is a view and not a verdict.
        (What a rejected F_2 carrier would have said is measurable, but it
        lives in the appendix method `mod2_ceiling_batch` below.)
        """
        rec: EquationAudit = audit_equation(lhs, rhs, label)
        lhs_c = Concept(lhs, rec.lhs_dim)
        rhs_c = Concept(rhs, rec.rhs_dim)
        return {
            "label": label or f"{lhs} = {rhs}",
            "lhs": lhs,
            "rhs": rhs,
            "lhs_dims": str(rec.lhs_dim),
            "rhs_dims": str(rec.rhs_dim),
            "accepted": rec.accepted,
            "residual": str(rec.residual),
            "lhs_telemetry": lhs_c.telemetry(),
            "rhs_telemetry": rhs_c.telemetry(),
            "summary": rec.summary(),
        }

    def audit_many(self, cases: Iterable[Tuple[str, str, str]]) -> Dict[str, object]:
        """Audit a batch of (lhs, rhs, label) cases and summarise."""
        records = []
        for lhs, rhs, label in cases:
            records.append(self.audit(lhs, rhs, label))
        accepted = sum(1 for r in records if r["accepted"])
        return {
            "records": records,
            "total": len(records),
            "accepted": accepted,
            "rejected": len(records) - accepted,
        }

    def mod2_ceiling_batch(
            self, cases: Iterable[Tuple[str, str, str]]) -> Dict[str, object]:
        """
        APPENDIX (not part of any verdict).  Re-run a batch of cases asking
        what the rejected F_2 carrier would have concluded, so that the
        reason for deriving the bits from the meaning — rather than the other
        way round — stays a measurement.  See `glm_metrology` §6.
        """
        rows = []
        traps = 0
        for lhs, rhs, label in cases:
            rec: EquationAudit = audit_equation(lhs, rhs, label)
            would = mod2_would_accept(rec.lhs_dim, rec.rhs_dim)
            trap = would and not rec.accepted
            traps += trap
            rows.append({
                "label": label or f"{lhs} = {rhs}",
                "accepted": rec.accepted,
                "mod2_accepted": would,
                "mod2_false_positive": trap,
            })
        return {
            "records": rows,
            "total": len(rows),
            "mod2_false_positives_prevented": traps,
        }

    # ── §3  target synthesis ─────────────────────────────────────────────────
    def solve(self, target: str, inputs: Sequence[str],
              search: int = 3) -> Solution:
        """
        Find integer (or, failing that, rational) powers of `inputs` whose
        product has the dimension of `target`.

        The integer problem is solved exactly with the Smith normal form; the
        solution set is  x0 + ker(A),  and we search small integer combinations
        of the kernel basis (coefficients in [-search, search]) for the
        simplest representative, preferring small total |exponent|.
        """
        t_dim = resolve(target)
        if t_dim is None:
            return Solution("impossible", target, list(inputs), [], [], 0,
                            f"unknown target quantity {target!r}")
        cols = []
        names = []
        for name in inputs:
            d = resolve(name)
            if d is None:
                return Solution("impossible", target, list(inputs), [], [], 0,
                                f"unknown input quantity {name!r}")
            cols.append(list(d.exps))
            names.append(name)
        A = [[cols[j][i] for j in range(len(cols))] for i in range(7)]   # 7 x k
        ker = kernel_basis(A)

        integer = solve_integer_system(A, list(t_dim.exps))
        if integer is not None:
            x0, _ = integer
            best, alts = _minimise(x0, ker, search)
            return Solution("integer", target, names,
                            [Fraction(v) for v in best],
                            [[Fraction(v) for v in a] for a in alts],
                            len(ker))

        rational = solve_rational_system(A, list(t_dim.exps))
        if rational is None:
            return Solution("impossible", target, names, [], [], len(ker),
                            "the target dimension is not in the span of the "
                            "input dimensions (no product of powers can "
                            "produce it)")
        best_q, alts_q = _minimise_rational(rational, ker, search)
        return Solution("fractional", target, names, best_q, alts_q, len(ker),
                        "no integer solution exists; fractional powers are "
                        "required (e.g. a square root)")

    # ── §4  Buckingham-Pi ────────────────────────────────────────────────────
    def pi_groups(self, inputs: Sequence[str]) -> Dict[str, object]:
        """
        Complete dimensionless-group analysis of an input set.

        Returns an exact integer basis of the kernel of the dimension matrix.
        By the Pi theorem the number of independent groups is n - rank(A);
        both numbers are reported so the identity can be checked by eye.
        """
        cols, names = [], []
        for name in inputs:
            d = resolve(name)
            if d is None:
                return {"status": "error", "reason": f"unknown quantity {name!r}"}
            cols.append(list(d.exps))
            names.append(name)
        A = [[cols[j][i] for j in range(len(cols))] for i in range(7)]
        ker = kernel_basis(A)
        rank = len(names) - len(ker)
        groups = []
        for k in ker:
            groups.append({
                "exponents": k,
                "expression": _render_formula("Pi", names,
                                              [Fraction(v) for v in k])
                .replace("Pi = ", ""),
                "verified_dimensionless": all(v == 0 for v in matvec(A, k)),
            })
        return {
            "status": "ok",
            "inputs": names,
            "rank": rank,
            "pi_group_count": len(ker),
            "pi_theorem_holds": len(ker) == len(names) - rank,
            "groups": groups,
        }

    # ── substrate reports ────────────────────────────────────────────────────
    def lawful_concepts(self) -> List[str]:
        return sorted(n for n, c in self.concepts.items() if c.lawful)

    def substrate_table(self, names: Optional[Sequence[str]] = None
                        ) -> List[Dict[str, object]]:
        keys = list(names) if names else sorted(self.concepts)
        rows = []
        for k in keys:
            c = self.concept(k)
            if c is not None:
                rows.append(c.telemetry())
        return rows

    # ── optional geometry (display only, paper section 9) ────────────────────
    def walk(self, names: Sequence[str]) -> Walk:
        """The quarter-turn accounting of a walk through concepts."""
        return walk_of_names(list(names))

    def holonomy(self, loop: Sequence[str]) -> Dict[str, object]:
        """The ordered quaternion product around a loop, both ways round."""
        forward = _loop_holonomy(list(loop))
        backward = _loop_holonomy(list(loop), reverse=True)
        return {
            "loop": list(loop),
            "holonomy": str(forward),
            "reversed": str(backward),
            "path_dependent": forward != backward,
        }

    def colour(self, name: str) -> Optional[Dict[str, object]]:
        """The concept's carrier as a colour, and the colour it snaps to."""
        concept = self.concept(name)
        if concept is None or concept.carrier is None or concept.snap is None:
            return None
        snapped = concept.snapped_carrier or concept.carrier
        return {
            "concept": concept.name,
            "colour": colour_of_word(concept.carrier),
            "snapped_colour": colour_of_word(snapped),
            "snap_distance": concept.snap.distance,
            "lawful": concept.lawful,
        }

    def symmetry_orbit(self, name: str, cap: int = 200000) -> Optional[Dict[str, object]]:
        """How M24 moves a concept's carrier (paper section 8.1).

        The automorphism group of the Golay code permutes carrier words while
        preserving what the substrate *decides* about them: the weight, the
        lawfulness and the snap distance (the minimum weight of the coset) are
        constant along an orbit, and only the coordinates move.  The syndrome
        itself is not invariant -- it is read off a fixed systematic basis, so
        it moves with the coordinates -- and the report shows that too.  The
        orbit is enumerated by breadth-first search under the four generators,
        up to `cap` words.
        """
        from glm_m24 import M24_GENERATORS, permute_word

        concept = self.concept(name)
        if concept is None or concept.carrier is None:
            return None
        word = tuple(concept.carrier)
        images = []
        for g in M24_GENERATORS:
            image = permute_word(word, g)
            meta = GOLAY.snap(list(image))[1]
            images.append({
                "weight": sum(image),
                "syndrome_weight": GOLAY.syndrome_weight(list(image)),
                "snap_distance": meta.distance,
                "lawful": GOLAY.is_codeword(list(image)),
                "colour": colour_of_word(list(image)),
            })
        seen = {word}
        frontier = [word]
        truncated = False
        while frontier and not truncated:
            nxt = []
            for w in frontier:
                for g in M24_GENERATORS:
                    image = permute_word(w, g)
                    if image not in seen:
                        seen.add(image)
                        nxt.append(image)
                        if len(seen) >= cap:
                            truncated = True
                            break
                if truncated:
                    break
            frontier = nxt
        base_syndrome = GOLAY.syndrome_weight(list(word))
        base_distance = GOLAY.snap(list(word))[1].distance
        weight = sum(word)
        all_of_weight = 1
        for k in range(weight):
            all_of_weight = all_of_weight * (24 - k) // (k + 1)
        return {
            "concept": concept.name,
            "weight": weight,
            "syndrome_weight": base_syndrome,
            "snap_distance": base_distance,
            "lawful": concept.lawful,
            "images_under_generators": images,
            "decisions_preserved": all(
                im["weight"] == weight and im["snap_distance"] == base_distance
                and im["lawful"] == concept.lawful for im in images),
            "syndrome_preserved": all(
                im["syndrome_weight"] == base_syndrome for im in images),
            "orbit_size": len(seen),
            "orbit_truncated": truncated,
            "words_of_this_weight": all_of_weight,
            "orbit_is_every_word_of_this_weight":
                (not truncated) and len(seen) == all_of_weight,
        }

    def codec_integrity(self) -> Dict[str, object]:
        """Every library concept must survive the codec chain with 0-bit loss."""
        total = 0
        failures = []
        for name, c in self.concepts.items():
            if not c.representable:
                failures.append((name, "not representable"))
                continue
            total += 1
            if not c.round_trip_ok():
                failures.append((name, "round trip"))
        return {
            "concepts_tested": total,
            "reconstruction_error_bits": 0 if not failures else None,
            "failures": failures,
            "lossless": not failures,
        }

    # ── §5  scene export ─────────────────────────────────────────────────────
    def scene(self, names: Sequence[str], relations: Sequence[Tuple[str, str]] = ()
              ) -> Dict[str, object]:
        """
        Build a 3D scene from concepts.

        Axes are the three mechanical exponents (L, M, T), which makes the
        geometry mean something: quantities sit where their dimensions put
        them.  Radius encodes the L1 size of the dimension vector, colour the
        remaining four exponents (I, Theta, N, J).
        """
        spheres, lines, pos = [], [], {}
        for name in names:
            c = self.concept(name)
            if c is None:
                continue
            L, M, T, I, Th, N, J = c.dim.exps
            p = [float(L), float(M), float(T)]
            pos[name] = p
            if J:
                colour = "#ffd700"           # photometric
            elif I:
                colour = "#00d0ff"           # electromagnetic
            elif Th or N:
                colour = "#ff7f50"           # thermal / chemical
            else:
                colour = "#a0ffa0"           # mechanical
            spheres.append({
                "x": p[0], "y": p[1], "z": p[2],
                "r": 0.25 + 0.05 * c.dim.l1(),
                "color": colour,
                "label": f"{name} [{c.dim}]",
                "lawful": c.lawful,
                "nrci": None if c.nrci is None else float(c.nrci),
            })
        for a, b in relations:
            if a in pos and b in pos:
                lines.append({"start": pos[a], "end": pos[b], "color": "#ffffff"})
        return {"spheres": spheres, "lines": lines,
                "axes": {"x": "length exponent", "y": "mass exponent",
                         "z": "time exponent"}}

    def export_scene(self, names: Sequence[str],
                     relations: Sequence[Tuple[str, str]] = (),
                     path: str = "scene_3d.json") -> str:
        scene = self.scene(names, relations)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(scene, fh, indent=2)
        return path


def _score(x: Sequence[Fraction]) -> Tuple:
    return (sum(abs(v) for v in x), max((abs(v) for v in x), default=0),
            sum(1 for v in x if v != 0), tuple(v for v in x))


def _combos(dim: int, bound: int) -> Iterable[Tuple[int, ...]]:
    if dim == 0:
        yield ()
        return
    if dim > 6:                                  # keep the search finite
        bound = 1
    idx = [-bound] * dim
    while True:
        yield tuple(idx)
        for i in range(dim - 1, -1, -1):
            if idx[i] < bound:
                idx[i] += 1
                break
            idx[i] = -bound
        else:
            return


def _minimise(x0: Sequence[int], ker: Sequence[Sequence[int]], bound: int
              ) -> Tuple[List[int], List[List[int]]]:
    """Simplest representative of x0 + span_Z(ker), plus equally simple ones."""
    best = list(x0)
    best_score = _score([Fraction(v) for v in best])
    seen = {tuple(best)}
    alts: List[List[int]] = []
    for coeffs in _combos(len(ker), bound):
        cand = list(x0)
        for c, k in zip(coeffs, ker):
            if c:
                cand = [a + c * b for a, b in zip(cand, k)]
        sc = _score([Fraction(v) for v in cand])
        key = tuple(cand)
        if sc < best_score:
            best, best_score, alts, seen = cand, sc, [], {key}
        elif sc == best_score and key not in seen:
            seen.add(key)
            alts.append(cand)
    return best, alts[:4]


def _minimise_rational(x0: Sequence[Fraction], ker: Sequence[Sequence[int]],
                       bound: int) -> Tuple[List[Fraction], List[List[Fraction]]]:
    best = [Fraction(v) for v in x0]
    best_score = _score(best)
    seen = {tuple(best)}
    alts: List[List[Fraction]] = []
    for coeffs in _combos(len(ker), bound):
        cand = [Fraction(v) for v in x0]
        for c, k in zip(coeffs, ker):
            if c:
                cand = [a + c * b for a, b in zip(cand, k)]
        sc = _score(cand)
        key = tuple(cand)
        if sc < best_score:
            best, best_score, alts, seen = cand, sc, [], {key}
        elif sc == best_score and key not in seen:
            seen.add(key)
            alts.append(cand)
    return best, alts[:4]


REASONER = GeometricReasoner()


# ══════════════════════════════════════════════════════════════════════════════
#  DEMONSTRATION SUITE  (illustrates every capability)
# ══════════════════════════════════════════════════════════════════════════════

#: (lhs, rhs, label) cases exercising true physics and adversarial traps
DEMO_EQUATIONS: Tuple[Tuple[str, str, str], ...] = (
    ("energy", "mass*speed^2", "E = m c^2"),
    ("energy", "mass*speed^4", "E = m c^4                (mod-2 trap)"),
    ("force", "mass*acceleration", "F = m a"),
    ("force", "mass*acceleration^3", "F = m a^3               (mod-2 trap)"),
    ("energy", "force*length", "E = F l"),
    ("action", "energy*time", "S = E t"),
    ("energy", "pressure*volume", "E = p V"),
    ("power", "energy/time", "P = E / t"),
    ("power", "voltage*current", "P = U I"),
    ("power", "current^2*resistance", "P = I^2 R"),
    ("voltage", "current*resistance", "U = I R"),
    ("energy", "charge*voltage", "E = q U"),
    ("momentum", "mass*speed", "p = m v"),
    ("energy", "mass*speed", "E = m v                 (plain mismatch)"),
    ("capacitance", "charge/voltage", "C = q / U"),
    ("magnetic_flux", "voltage*time", "Phi_B = U t"),
    ("pressure", "density*speed^2", "p = rho v^2"),
    ("illuminance", "luminous_flux/area", "E_v = Phi_v / A"),
    ("illuminance", "luminous_flux*area", "E_v = Phi_v A           (mod-2 trap)"),
    ("luminous_energy", "luminous_flux*time", "Q_v = Phi_v t"),
    ("entropy", "energy/temperature", "S = E / Theta"),
    ("stefan_boltzmann", "irradiance/temperature^4", "sigma = E_e / Theta^4"),
    ("stefan_boltzmann", "irradiance/temperature^2", "sigma = E_e / Theta^2   (mod-2 trap)"),
    ("gas_constant", "molar_energy/temperature", "R = E_m / Theta"),
    ("absorbed_dose", "energy/mass", "D = E / m"),
    ("gravitational_constant", "force*length^2/mass^2", "G = F l^2 / m^2"),
)

#: (target, inputs) queries for the deduction engine
DEMO_QUERIES: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("energy", ("mass", "speed")),
    ("energy", ("power", "time")),
    ("power", ("voltage", "current")),
    ("power", ("current", "resistance")),
    ("speed", ("energy", "mass")),
    ("illuminance", ("luminous_flux", "area")),
    ("luminous_energy", ("luminous_flux", "time")),
    ("pressure", ("density", "speed")),
    ("gravitational_constant", ("force", "length", "mass")),
    ("frequency", ("spring_constant", "mass")),
    ("action", ("energy", "time")),
    ("resistance", ("voltage", "current")),
    ("temperature", ("energy", "mass")),          # impossible: no pathway
)


def run_demonstration(export_path: Optional[str] = "scene_3d.json") -> Dict[str, object]:
    """Run every capability of the reasoner and print a readable report."""
    r = REASONER
    print("=" * 78)
    print("  GLM GEOMETRIC REASONER — DEMONSTRATION SUITE")
    print("=" * 78)

    # 1. codec integrity
    print("\n[1] Codec integrity over the whole library")
    integrity = r.codec_integrity()
    print(f"    concepts carried            : {integrity['concepts_tested']}")
    print(f"    reconstruction error (bits) : {integrity['reconstruction_error_bits']}")
    print(f"    failures                    : {integrity['failures'] or 'none'}")

    # 2. the derived substrate view for a few concepts
    print("\n[2] The derived view (meaning -> carrier -> shadow -> snap)")
    derived_ok = all(c.carrier_is_derived() for c in r.concepts.values())
    print(f"    every concept's bits are encode(meaning), and decode them "
          f"back: {derived_ok}")
    header = f"    {'concept':<20}{'dimension':<22}{'wt':>3}{'syn':>5}{'d':>3}{'ties':>5}  {'status':<12}{'NRCI':>8}"
    print(header)
    for name in ("dimensionless", "mass", "energy", "force", "speed", "voltage",
                 "illuminance", "capacitance", "stefan_boltzmann"):
        c = r.concept(name)
        assert c is not None and c.snap is not None
        print(f"    {name:<20}{str(c.dim):<22}{sum(c.carrier or []):>3}"
              f"{c.snap.syndrome_weight:>5}{c.snap.distance:>3}{c.snap.tie_count:>5}"
              f"  {c.snap.status:<12}{float(c.nrci or 0):>8.4f}")
    print(f"    lawful library concepts (carrier is a codeword): "
          f"{r.lawful_concepts() or 'none besides the dimensionless vacuum'}")

    # 3. equation audit
    print("\n[3] Equation audit — the exact verdict in (Z^7,+)")
    batch = r.audit_many(DEMO_EQUATIONS)
    for rec in batch["records"]:
        mark = "ACCEPT" if rec["accepted"] else "REJECT"
        print(f"    [{mark}] {rec['label']:<40} {rec['lhs_dims']} "
              f"{'=' if rec['accepted'] else '!='} {rec['rhs_dims']}")
    print(f"    accepted {batch['accepted']}, rejected {batch['rejected']}")
    ceiling = r.mod2_ceiling_batch(DEMO_EQUATIONS)
    print(f"    (appendix: a rejected F_2 carrier would have accepted "
          f"{ceiling['mod2_false_positives_prevented']} of the false ones)")

    # 4. deduction
    print("\n[4] Target synthesis (exact integer / rational power solving)")
    solved = 0
    for target, inputs in DEMO_QUERIES:
        sol = r.solve(target, inputs)
        if sol.found:
            solved += 1
            tag = "Z " if sol.status == "integer" else "Q "
            print(f"    [{tag}] {sol.formula():<52} (pi groups: {sol.pi_group_count})")
        else:
            print(f"    [--] {target} from {list(inputs)}: {sol.detail}")

    # 5. Buckingham-Pi
    print("\n[5] Buckingham-Pi analysis")
    for inputs in (("force", "density", "speed", "length"),
                   ("speed", "length", "kinematic_viscosity"),
                   ("energy", "mass", "speed", "time")):
        res = r.pi_groups(inputs)
        print(f"    inputs {list(inputs)}: rank {res['rank']}, "
              f"{res['pi_group_count']} group(s), Pi theorem holds: "
              f"{res['pi_theorem_holds']}")
        for g in res["groups"]:
            print(f"        {g['expression']}   (dimensionless: "
                  f"{g['verified_dimensionless']})")

    # 6. optional geometry (display only)
    print("\n[6] Fibre geometry (paper section 9 - display only, never a verdict)")
    print(f"    {'concept':<20}{'versor':>7}{'fibre':>8}{'grading':>9}"
          f"{'colour':>10}{'snaps to':>10}")
    for name in ("dimensionless", "mass", "energy", "speed", "voltage"):
        c = r.concept(name)
        geo = None if c is None else c.geometry()
        if geo is None:
            continue
        print(f"    {name:<20}{geo['versor']:>7}{geo['fibre_product']:>8}"
              f"{geo['grading']:>9}{geo['colour']:>10}"
              f"{geo['snapped_colour']:>10}")
    emc2 = r.walk(["energy", "mass", "speed", "speed", "energy"])
    print(f"    walk {' -> '.join(emc2.names)}: "
          f"quarter turns {emc2.quarter_turns}, winding {emc2.winding}")
    loop = r.holonomy(["pressure", "force", "area", "pressure"])
    print(f"    holonomy of {loop['loop']}: {loop['holonomy']} "
          f"(reversed {loop['reversed']}, "
          f"path-dependent {loop['path_dependent']})")

    # 7. the symmetry group of the substrate (display only)
    print("\n[7] Substrate symmetry (paper section 8.1 - display only)")
    from glm_m24 import m24_report
    m24 = m24_report(quick=True)
    print(f"    Aut(Golay) computed: order {m24['order']:,}, "
          f"5-transitive {m24['five_transitive']}, "
          f"octad-transitive {m24['octad_transitive']}")
    for name in ("energy", "force"):
        orbit = r.symmetry_orbit(name)
        if orbit is None:
            continue
        print(f"    {name:<10} carrier weight {orbit['weight']}, "
              f"orbit {orbit['orbit_size']:,} of "
              f"{orbit['words_of_this_weight']:,} words of that weight, "
              f"decisions preserved {orbit['decisions_preserved']}")

    # 8. scene
    path = None
    if export_path:
        path = r.export_scene(
            ["energy", "mass", "speed", "force", "acceleration", "power", "time",
             "voltage", "current", "resistance", "illuminance", "luminous_flux",
             "luminous_energy", "entropy", "pressure"],
            relations=[("energy", "mass"), ("energy", "speed"),
                       ("force", "mass"), ("force", "acceleration"),
                       ("power", "energy"), ("power", "time"),
                       ("voltage", "current"), ("illuminance", "luminous_flux")],
            path=export_path)
        print(f"\n[8] 3D scene exported to {path}")

    print("=" * 78)
    return {
        "codec_integrity": integrity,
        "equation_audit": {k: v for k, v in batch.items() if k != "records"},
        "queries_solved": solved,
        "queries_total": len(DEMO_QUERIES),
        "scene_path": path,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  COMMAND LINE
# ══════════════════════════════════════════════════════════════════════════════

def _cli(argv: Sequence[str]) -> int:
    if not argv:
        run_demonstration()
        return 0
    cmd, args = argv[0], list(argv[1:])
    r = REASONER
    try:
        if cmd == "check" and len(args) >= 2:
            rec = r.audit(args[0], args[1], " ".join(args[2:]))
            print(rec["summary"])
            return 0 if rec["accepted"] else 1
        if cmd == "solve" and len(args) >= 2:
            sol = r.solve(args[0], args[1:])
            print(sol.formula() if sol.found else f"no solution: {sol.detail}")
            for step in sol.proof_steps():
                print("   " + step)
            return 0 if sol.found else 1
        if cmd == "pi" and args:
            res = r.pi_groups(args)
            print(json.dumps(res, indent=2))
            return 0
        if cmd == "show" and args:
            c = r.concept(args[0])
            if c is None:
                print(f"unknown quantity {args[0]!r}")
                return 1
            print(json.dumps(c.telemetry(), indent=2))
            return 0
        if cmd == "colour" and args:
            info = r.colour(args[0])
            if info is None:
                print(f"unknown or unrepresentable quantity {args[0]!r}")
                return 1
            print(json.dumps(info, indent=2))
            return 0
        if cmd == "walk" and len(args) >= 2:
            print(json.dumps(r.walk(args).report(), indent=2))
            return 0
        if cmd == "holonomy" and len(args) >= 2:
            print(json.dumps(r.holonomy(args), indent=2))
            return 0
        if cmd == "ledger":
            from glm_moonshine import dimension_ledger, leech_voa_head
            print(json.dumps({"ledger": dimension_ledger(),
                              "J_head": leech_voa_head()}, indent=2))
            return 0
        if cmd == "m24":
            from glm_m24 import m24_report
            print(json.dumps(m24_report(quick="--quick" in args), indent=2))
            return 0
        if cmd == "symmetry" and args:
            info = r.symmetry_orbit(args[0])
            if info is None:
                print(f"unknown or unrepresentable quantity {args[0]!r}")
                return 1
            print(json.dumps(info, indent=2))
            return 0
        if cmd == "list":
            for name in sorted(QUANTITIES):
                dim, sym, unit = QUANTITIES[name]
                print(f"  {name:<26}{sym:<10}{unit:<16}{dim}")
            return 0
    except ParseError as exc:
        print(f"parse error: {exc}")
        return 2
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
