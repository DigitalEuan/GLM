#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM-3 REASONER  —  the companion implementation
================================================================================

  Part of:  The Geometric Language Machine, third generation (GLM-3).
  Layer  :  Tier 3 — the application.
  Deps   :  glm3_leech2, glm3_griess, glm3_extraspecial, glm3_mog,
            and the GLM-2 meaning / library / codec / reasoner.

  ------------------------------------------------------------------------
  What this program is
  ------------------------------------------------------------------------

  It is the working GLM: a machine that reads quantities and equations,
  checks them exactly, and solves for missing formulas — and that carries
  out all of that reasoning inside structures of the Monster group.

  The UBP/GLM layer is kept in full and unchanged:

      meaning       an exact rational vector (10 dimensional exponents,
                    scale, tensor rank, three parities, kind, domain)
      library       660 concepts across 26 domains
      carrier       a Leech lattice point, DERIVED from the meaning
      repair        nearest-point decoding of a corrupted carrier
      audit/solve   dimensional reasoning, unit conversion, Pi groups

  ------------------------------------------------------------------------
  The bridge: a concept is a stack of Monster addresses
  ------------------------------------------------------------------------

  The Monster does not act on the Leech lattice; it acts on structures
  indexed by Lambda/2Lambda.  A single reduction mod 2 would be far too
  coarse for meaning — the 660 concepts have only 9 distinct classes,
  because the encoder's rational slots are doubled and so nearly always
  even.  What is faithful is the whole 2-adic expansion:

      the MULTI-MOG-CUBE of a concept
          plane k = the k-th binary digit of the 24 Leech-basis coordinates
                    (after a fixed offset so negatives expand too)

  Every plane is a class of Lambda/2Lambda, hence a Monster address; the
  stack of ten planes rebuilds the carrier exactly, so nothing is lost.  A
  concept is therefore a WORD of ten Monster addresses, and the reasoner
  works with the word:

      type word     the type (0, 2, 3, 4) of each plane;
                    type 2 planes are Majorana 2A AXES of the Griess algebra
      Griess vector g(concept) = sum over the axis planes of 2^-k a_{d_k},
                    an exact element of the 98,580-dimensional even part
      similarity    (g(a), g(b)) in the Monster-invariant form — a rational
                    number, and a far finer relation than the four-valued
                    class of a single plane
      relation word the Monster class (1A / 2A / 4A / 2B) of each plane pair,
                    read off the type of the plane of the PRODUCT concept
      group         plane 0 is additive, so composing meanings multiplies
                    the corresponding elements of Q = 2^(1+24), up to the
                    centre, which records the cocycle
      triangle      when two concepts are in 2A position on plane 0,
                        a . b = (1/8) (a + b - a_{ab}),
                    and the third axis is the axis of their PRODUCT: the
                    Monster's 2A algebra carrying out GLM composition
      frame         a type-4 plane gives 48 vectors — 24 orthogonal
                    directions resolving that plane of the concept
      involution    a concept's class is an involution of the even Griess
                    algebra (its Miyamoto involution), which two-colours the
                    rest of the library

      python3 glm3_reasoner.py                     # demonstration suite
      python3 glm3_reasoner.py address energy
      python3 glm3_reasoner.py stack energy
      python3 glm3_reasoner.py relation energy torque
      python3 glm3_reasoner.py similar energy
      python3 glm3_reasoner.py triangle
      python3 glm3_reasoner.py fusion energy
      python3 glm3_reasoner.py orbit energy
      python3 glm3_reasoner.py mog energy
      python3 glm3_reasoner.py frame energy
      python3 glm3_reasoner.py census
      python3 glm3_reasoner.py audit energy "mass*speed^2"
      python3 glm3_reasoner.py solve energy mass speed
================================================================================
"""

from __future__ import annotations

import sys
from fractions import Fraction as F
from typing import Dict, List, Optional, Sequence, Tuple

from glm3_common import banner, fmt_int
import glm3_extraspecial as XS
import glm3_griess as GR
import glm3_leech2 as L2
import glm3_metric as MET
import glm3_mog as MOG3
import glm3_odd as OD
import glm3_sign as SGN

import glm2_lattice as LAT
from glm2_codec import coords_of
from glm2_meaning import Meaning
from glm2_reasoner import Reasoner as Glm2Reasoner

__all__ = ["MonsterReasoner", "REASONER", "RELATION_BY_PRODUCT_TYPE",
           "FACET_SLOTS", "demonstrate", "main"]

Vec = Tuple[int, ...]

#: The Monster class of the product of the two 2A involutions attached to a
#: pair of type-2 classes, as a function of the type of the sum of the two
#: classes.  Derived in glm3_griess by computing the subalgebra the two axes
#: generate: dimension 3 / 5 / 2 with axis inner product 1/8 / 1/32 / 0.
RELATION_BY_PRODUCT_TYPE: Dict[int, Tuple[str, str, F]] = {
    0: ("1A", "the same axis", F(1)),
    2: ("2A", "Norton-Sakuma 2A, dimension 3", F(1, 8)),
    3: ("4A", "Norton-Sakuma 4A, dimension 5", F(1, 32)),
    4: ("2B", "Norton-Sakuma 2B, the axes annihilate", F(0)),
}


#: The 24 integer slots the GLM-2 codec writes a meaning into, grouped into
#: the FACETS the reasoning actually asks about.  Because the codec is
#: `from_coords o coords_of` and `from_coords` is linear, zeroing the slots
#: outside a facet is a lattice projection: each facet of a concept is again a
#: point of Lambda, hence again a word of ten Monster addresses.
FACET_SLOTS: Dict[str, Tuple[int, ...]] = {
    "dimension": tuple(range(0, 10)),   # the ten rational exponents
    "scale": (10,),                     # the decimal scale
    "tensor": (11, 12, 13, 14),         # rank and the P, T, C data
    "kind": (15,),                      # the nominal kind
    "domain": (16,),                    # the declaring namespace
    "context": tuple(range(17, 24)),    # the free context slots
}

#: The word of the origin of Lambda, at the module's default parameters.  A
#: facet is UNLABELLED exactly when its word is this one -- the digit-plane
#: expansion is offset, so the origin is not the all-zero word.
ZERO_WORD: List[int] = L2.class_stack(tuple([0] * 24))


class MonsterReasoner:
    """
    The GLM-3 companion: GLM-2 reasoning, carried out in the Monster.

    The stack parameters are constructor arguments, not constants.  `depth`
    and `offset` default to the module-level pair of glm3_leech2, which is
    itself derived from the coordinate range of the register (see
    `L2.depth_report` and paper section 6.1); a second reasoner built at a
    different admissible depth answers every equation the same way, which is
    the content of claim C53.
    """

    def __init__(self, depth: Optional[int] = None,
                 offset: Optional[int] = None) -> None:
        self.base = Glm2Reasoner()
        self.depth = L2.STACK_DEPTH if depth is None else depth
        self.offset = L2.STACK_OFFSET if offset is None else offset
        self._carrier: Dict[str, Vec] = {}
        self._stack: Dict[str, List[int]] = {}
        self._griess: Dict[str, GR.GriessVector] = {}
        self._facet: Dict[Tuple[str, str], List[int]] = {}
        self._table_loaded = False
        #: The word of the origin of Lambda AT THESE PARAMETERS.  A facet is
        #: unlabelled exactly when its word is this one.
        self.zero_word: List[int] = L2.class_stack(tuple([0] * 24),
                                                   self.depth, self.offset)

    # ── the retained GLM/UBP layer ──────────────────────────────────────
    def meaning(self, text: str) -> Meaning:
        return self.base.meaning(text)

    def carrier(self, text: str) -> Vec:
        if text not in self._carrier:
            self._carrier[text] = self.base.carrier(text)
        return self._carrier[text]

    def audit(self, lhs: str, rhs: str):
        return self.base.audit(lhs, rhs)

    def solve(self, target: str, sources: Sequence[str]):
        return self.base.solve(target, sources)

    def convert(self, a: str, b: str) -> Optional[str]:
        return self.base.convert(a, b)

    def identify(self, text: str) -> Dict[str, object]:
        return self.base.identify(text)

    def repair(self, y: Sequence[int]):
        from glm2_codec import repair as _repair
        return _repair(y)

    def list_concepts(self, domain: Optional[str] = None) -> List[str]:
        return self.base.list_concepts(domain)

    # ── types, in O(1) ──────────────────────────────────────────────────
    def _ensure_table(self) -> None:
        if not self._table_loaded:
            GR.type2_table()
            self._table_loaded = True

    def class_type(self, cls: int) -> int:
        """
        The type of a class of Lambda/2Lambda, without running the decoder:

            0  the trivial class
            3  q(class) = 1, since the non-singular classes are exactly the
               type-3 ones
            2  the class carries a minimal vector (table lookup)
            4  otherwise

        Checked against the decoder-based glm3_leech2.class_type in the
        paper and in the tests.
        """
        if cls == 0:
            return 0
        if L2.q_form(cls) == 1:
            return 3
        self._ensure_table()
        return 2 if cls in GR.type2_table() else 4

    # ── the multi-MOG-cube of Monster addresses ─────────────────────────
    def stack(self, text: str) -> List[int]:
        """The concept's stack of Lambda/2Lambda classes (its ten planes)."""
        if text not in self._stack:
            self._stack[text] = L2.class_stack(self.carrier(text),
                                               self.depth, self.offset)
        return self._stack[text]

    def address(self, text: str) -> Dict[str, object]:
        """
        The Monster address of a concept: the stack, the type of each plane,
        which planes are axes, and the faithfulness check.
        """
        x = self.carrier(text)
        planes = self.stack(text)
        types = [self.class_type(p) for p in planes]
        prim = L2.class_of(L2.primitive_point(x))
        return {
            "text": text,
            "carrier_norm": LAT.norm2(x),
            "planes": [f"0x{p:06x}" for p in planes],
            "types": types,
            "type_word": "".join(str(t) for t in types),
            "axis_planes": [k for k, t in enumerate(types) if t == 2],
            "frame_planes": [k for k, t in enumerate(types) if t == 4],
            "plane0_class": planes[0],
            "plane0_type": types[0],
            "primitive_class": prim,
            "primitive_type": self.class_type(prim),
            "stack_rebuilds_carrier":
                L2.class_stack_rebuild(planes, self.offset) == x,
        }

    # ── the group ───────────────────────────────────────────────────────
    def group_element(self, text: str, plane: int = 0) -> XS.QElement:
        """The extraspecial element x_u of one plane of a concept."""
        return XS.x_of_class(self.stack(text)[plane])

    def group_word(self, text: str) -> XS.QElement:
        """
        The product x_{d_0} x_{d_1} ... x_{d_9} in Q = 2^(1+24): a single
        element of the Monster's 2B centraliser attached to the concept.
        """
        g = XS.identity()
        for p in self.stack(text):
            g = g * XS.x_of_class(p)
        return g

    def composition_is_group_law(self, a: str, b: str) -> Dict[str, object]:
        """
        Composition of meanings is addition of carriers, hence addition of
        plane-0 classes, hence multiplication in Q up to the centre:
            x_u x_v = z^f(u,v) x_{u+v}.
        """
        xa, xb = self.carrier(a), self.carrier(b)
        xc = tuple(p + q for p, q in zip(xa, xb))
        ua, ub, uc = L2.class_of(xa), L2.class_of(xb), L2.class_of(xc)
        prod = XS.x_of_class(ua) * XS.x_of_class(ub)
        return {
            "class_of_product": uc,
            "sum_of_classes": ua ^ ub,
            "classes_add": uc == (ua ^ ub),
            "group_product_class": prod.u,
            "group_matches": prod.u == uc,
            "central_phase": prod.eps,
            "cocycle": XS.cocycle(ua, ub),
            "phase_is_the_cocycle": prod.eps == XS.cocycle(ua, ub),
        }

    # ── axes, Griess vectors, similarity ────────────────────────────────
    def axis(self, text: str, plane: Optional[int] = None
             ) -> Optional[GR.GriessVector]:
        """
        A Majorana 2A axis of the concept: the axis of the requested plane,
        or of the lowest plane that has type 2.
        """
        planes = self.stack(text)
        candidates = ([plane] if plane is not None
                      else [k for k, p in enumerate(planes)
                            if self.class_type(p) == 2])
        for k in candidates:
            if self.class_type(planes[k]) == 2:
                return SGN.canonical_axis(planes[k])
        return None

    def griess_vector(self, text: str) -> GR.GriessVector:
        """
        g(concept) = sum over the axis planes of 2^-k a_{d_k}: the concept as
        one exact element of the even part of the Griess algebra.  The
        weights 2^-k are the same weights the stack itself uses, so the
        lowest planes — the finest information in the meaning — dominate.
        """
        if text not in self._griess:
            g = GR.zero()
            for k, p in enumerate(self.stack(text)):
                if self.class_type(p) == 2:
                    g = g + SGN.canonical_axis(p).scale(F(1, 1 << k))
            self._griess[text] = g
        return self._griess[text]

    def similarity(self, a: str, b: str) -> F:
        """The Monster-invariant inner product of two concepts."""
        return self.griess_vector(a).form(self.griess_vector(b))

    def neighbours(self, name: str, count: int = 8,
                   limit: Optional[int] = None) -> List[Tuple[str, str]]:
        """The concepts closest to `name` in the Griess form."""
        names = self.list_concepts()
        if limit:
            names = names[:limit]
        g = self.griess_vector(name)
        scored = []
        for n in names:
            if n == name:
                continue
            try:
                scored.append((g.form(self.griess_vector(n)), n))
            except Exception:
                continue
        scored.sort(key=lambda t: (-t[0], t[1]))
        return [(n, str(s)) for s, n in scored[:count]]

    # ── the metric (glm3_metric) ────────────────────────────────────────
    def distance2(self, a: str, b: str) -> F:
        """
        The exact squared distance between two concepts in the plane-graded
        embedding: a genuine metric, not a similarity ranking.  Symmetric,
        zero only when the two concepts have the same stack, and obeying the
        triangle inequality because the Griess form is positive definite
        (glm3_metric, paper section 9.3).
        """
        return MET.distance2_of_stacks(self.stack(a), self.stack(b))

    def distance(self, a: str, b: str, places: int = 6) -> str:
        """The same distance as a decimal string, for printing."""
        return MET.sqrt_approx(self.distance2(a, b), places)

    def nearest(self, name: str, count: int = 8,
                limit: Optional[int] = None) -> List[Tuple[str, str]]:
        """
        True nearest neighbours in the metric.  Unlike `neighbours`, which
        ranks by the similarity form and so favours concepts with many axis
        planes, this is an honest nearest-neighbour query.
        """
        names = self.list_concepts()
        if limit:
            names = names[:limit]
        if name not in names:
            names = [name] + list(names)
        stacks = {n: self.stack(n) for n in names}
        return [(n, MET.sqrt_approx(d2))
                for n, d2 in MET.nearest(name, stacks, count)]

    def cluster(self, threshold: F,
                limit: Optional[int] = None) -> List[List[str]]:
        """
        Single-linkage clusters of the register at a threshold on the
        DISTANCE: well defined because the distance is a metric, so the
        partition depends on the data and the threshold alone.
        """
        names = self.list_concepts()
        if limit:
            names = names[:limit]
        return MET.cluster({n: self.stack(n) for n in names}, F(threshold))

    # ── the odd part (glm3_odd) ─────────────────────────────────────────
    def ledger(self) -> Dict[str, object]:
        """
        The eigenvalue ledger of a 2A axis on the WHOLE 196,884-dimensional
        Griess algebra, even part plus odd part.
        """
        return OD.ledger()

    def odd_view(self, text: str,
                 plane: Optional[int] = None) -> Dict[str, object]:
        """
        What the odd part says about a concept's axis: on the odd vector
        lambda (x) s with X_lambda s = s the two axes of the concept's class
        act by DIFFERENT eigenvalues, so the Miyamoto involutions of
        a_lambda^- and a_lambda^+ are the two different automorphisms
        x_lambda and x_lambda z.  The even part cannot see this.
        """
        planes = self.stack(text)
        if plane is None:
            plane = next((k for k, p in enumerate(planes)
                          if self.class_type(p) == 2), None)
            if plane is None:
                raise ValueError(f"odd_view: {text!r} has no axis plane")
        cls = planes[plane]
        if self.class_type(cls) != 2:
            raise ValueError("odd_view: that plane carries no axis")
        _u, minus = OD.axis_eigenvector(cls, "along+", axis_sign=-1)
        _v, plus = OD.axis_eigenvector(cls, "along+", axis_sign=+1)
        return {
            "concept": text,
            "plane": plane,
            "class": cls,
            "eigenvalue_of_the_canonical_axis": str(minus),
            "eigenvalue_of_the_other_axis": str(plus),
            "the_odd_part_separates_them": minus != plus,
            "miyamoto_of_the_canonical_axis": "x_lambda",
            "miyamoto_of_the_other_axis": "x_lambda z",
        }

    # ── relations ───────────────────────────────────────────────────────
    def relation(self, a: str, b: str) -> Dict[str, object]:
        """
        The Monster relation of two concepts, plane by plane.  On each plane
        the two classes are added; the type of the sum names the Monster
        class of the product of the two 2A involutions:

            sum type 0 -> 1A,  2 -> 2A,  3 -> 4A,  4 -> 2B.

        Where both planes are axes the predicted inner product 1, 1/8, 1/32
        or 0 is CHECKED against the algebra.
        """
        sa, sb = self.stack(a), self.stack(b)
        planes = []
        word = []
        for k, (ca, cb) in enumerate(zip(sa, sb)):
            t = self.class_type(ca ^ cb)
            name, description, ip = RELATION_BY_PRODUCT_TYPE[t]
            entry: Dict[str, object] = {
                "plane": k, "type_a": self.class_type(ca),
                "type_b": self.class_type(cb), "sum_type": t,
                "monster_class": name, "description": description,
                "predicted_inner_product": str(ip),
            }
            if entry["type_a"] == 2 and entry["type_b"] == 2:
                got = SGN.canonical_axis(ca).form(SGN.canonical_axis(cb))
                entry["inner_product"] = str(got)
                entry["matches"] = got == ip
            planes.append(entry)
            word.append(name)
        checked = [p for p in planes if "matches" in p]
        return {
            "a": a, "b": b,
            "relation_word": word,
            "planes": planes,
            "checked_planes": len(checked),
            "all_predictions_hold": all(p["matches"] for p in checked),
            "similarity": str(self.similarity(a, b)),
        }

    def triangle(self, a: str, b: str, plane: int = 0) -> Dict[str, object]:
        """
        The 2A triangle of two concepts on one plane: if [a] and [b] are
        type-2 classes whose sum is again type 2, then

            a_[a] . a_[b] = (1/8) ( a_[a] + a_[b] - a_[ab] ),

        and on plane 0 the third class is the class of the PRODUCT concept,
        because plane 0 is additive.  The Monster's 2A algebra is carrying
        out the GLM composition.
        """
        xa, xb = self.carrier(a), self.carrier(b)
        ca, cb = self.stack(a)[plane], self.stack(b)[plane]
        cc = ca ^ cb
        types = (self.class_type(ca), self.class_type(cb), self.class_type(cc))
        out: Dict[str, object] = {"a": a, "b": b, "plane": plane,
                                  "types": types}
        if types != (2, 2, 2):
            out["applicable"] = False
            return out
        av, bv, cv = (SGN.canonical_axis(ca), SGN.canonical_axis(cb),
                      SGN.canonical_axis(cc))
        product_carrier = tuple(p + q for p, q in zip(xa, xb))
        out.update({
            "applicable": True,
            "third_class_is_the_product_concept":
                (plane != 0) or L2.class_of(product_carrier) == cc,
            "sign_convention": "canonical: a = P/8 - b/2 on every class",
            "no_ad_hoc_sign": True,
            "sakuma_identity": av.mul(bv) == (av + bv - cv).scale(F(1, 8)),
            "inner_product": str(av.form(bv)),
            "subalgebra_dimension": len(GR.subalgebra_closure([av, bv])),
        })
        return out

    def find_triangle(self, names: Optional[Sequence[str]] = None,
                      limit: int = 120) -> Optional[Tuple[str, str]]:
        """Search the library for two concepts in 2A position on plane 0."""
        names = list(names or self.list_concepts())[:limit]
        axes = []
        for n in names:
            try:
                c = self.stack(n)[0]
            except Exception:
                continue
            if self.class_type(c) == 2:
                axes.append((n, c))
        for i, (na, ca) in enumerate(axes):
            for nb, cb in axes[i + 1:]:
                if self.class_type(ca ^ cb) == 2:
                    return na, nb
        return None

    # ── the fusion law, per concept ─────────────────────────────────────
    def fusion(self, text: str) -> Dict[str, object]:
        """Verify the Monster fusion law for one of the concept's own axes."""
        planes = self.stack(text)
        which = next((k for k, p in enumerate(planes)
                      if self.class_type(p) == 2), None)
        if which is None:
            return {"text": text, "is_axis": False}
        report = GR.fusion_report(planes[which], count=2)
        return {"text": text, "is_axis": True, "plane": which,
                "idempotent": report["idempotent"],
                "norm_one": report["norm_one"],
                "rules": report["rules"],
                "all_rules_hold": report["all_rules_hold"],
                "eigenspace_dimensions": GR.spectrum_dimensions()}

    # ── the involution of a concept, acting on the library ──────────────
    def involution_orbit(self, text: str, plane: int = 0,
                         names: Optional[Sequence[str]] = None,
                         limit: int = 60) -> Dict[str, object]:
        """
        A plane of a concept gives an involution of the even Griess algebra
        (the extraspecial sign automorphism x_u, which is exactly the
        Miyamoto involution of the axis when the plane is type 2).  Applied
        to the other concepts' axes it fixes those with B(u, v) = 0 and
        negates the rest: a Monster-invariant two-colouring of the library.
        """
        u = self.stack(text)[plane]
        names = list(names or self.list_concepts())[:limit]
        fixed, moved = [], []
        for n in names:
            try:
                v = self.stack(n)[plane]
            except Exception:
                continue
            (fixed if L2.b_form(u, v) == 0 else moved).append(n)
        return {"text": text, "plane": plane, "class": u,
                "fixed": fixed, "moved": moved,
                "fixed_count": len(fixed), "moved_count": len(moved)}

    # ── frames ──────────────────────────────────────────────────────────
    def frame(self, text: str, plane: Optional[int] = None
              ) -> Dict[str, object]:
        """
        The coordinate frame of a type-4 plane: 48 vectors in 24 orthogonal
        pairs, i.e. a 24-fold orthogonal resolution of that plane of the
        concept.
        """
        planes = self.stack(text)
        which = plane if plane is not None else next(
            (k for k, p in enumerate(planes) if self.class_type(p) == 4), None)
        if which is None or self.class_type(planes[which]) != 4:
            return {"text": text, "has_frame": False}
        vectors = L2.frame_of_class(planes[which])
        shapes: Dict[str, int] = {}
        for v in vectors:
            entries = sorted({abs(int(c)) for c in v if c})
            key = ",".join(str(e) for e in entries)
            shapes[key] = shapes.get(key, 0) + 1
        return {"text": text, "has_frame": True, "plane": which,
                "vectors": len(vectors),
                "orthogonal_pairs": len(vectors) // 2,
                "shape_census": shapes}

    # ── the multi-MOG-cube views ────────────────────────────────────────
    def mog(self, text: str) -> Dict[str, object]:
        """
        Both MOG readings of a concept's carrier:

          * the AMBIENT stack — the binary digit planes of the 24 integer
            coordinates, whose plane 1 is the Golay codeword that the Leech
            congruences require;
          * the BASIS stack — the digit planes of the Leech-basis
            coordinates, whose planes are the Monster addresses.
        """
        x = self.carrier(text)
        golay = MOG3.golay_plane(x)
        ambient = MOG3.plane_stack(x, depth=4)
        basis = self.stack(text)
        return {
            "text": text,
            "ambient_planes": [f"0x{p:06x}" for p in ambient],
            "ambient_plane0_constant": ambient[0] in (0, (1 << 24) - 1),
            "golay_plane": f"0x{golay:06x}",
            "golay_plane_is_a_codeword": golay in MOG3.GOLAY_SET,
            "golay_weight": bin(golay).count("1"),
            "hexacode_shadow": MOG3.hexacode_shadow(golay),
            "cube_profile": MOG3.cube_profile(golay),
            "golay_frame": MOG3.frame(golay),
            "basis_planes": [f"0x{p:06x}" for p in basis],
            "basis_types": [self.class_type(p) for p in basis],
            "basis_frame_of_plane1": MOG3.frame(basis[1]),
        }

    # ── facets: reasoning carried out inside Lambda/2Lambda ───────────
    def facet_point(self, text: str, facet: str) -> Vec:
        """
        The carrier of a concept with every slot outside `facet` set to zero.

        The GLM-2 codec writes the meaning into 24 named integer slots and
        then applies the Leech basis, a linear map.  Zeroing a set of slots is
        therefore a lattice projection: the result is again a point of Lambda,
        with its own word of ten Monster addresses.  A facet is a question one
        can ask a concept, and its word is the Monster's answer.
        """
        slots = FACET_SLOTS[facet]
        u = coords_of(self.meaning(text))
        v = [u[i] if i in slots else 0 for i in range(len(u))]
        return LAT.from_coords(v)

    def facet_word(self, text: str, facet: str) -> List[int]:
        """The word of ten Monster addresses of one facet of a concept."""
        key = (text, facet)
        if key not in self._facet:
            self._facet[key] = L2.class_stack(self.facet_point(text, facet),
                                              self.depth, self.offset)
        return self._facet[key]

    def facet_report(self, text: str) -> Dict[str, object]:
        """Every facet of a concept, as a Monster word and its type word."""
        out: Dict[str, object] = {"text": text}
        for facet in FACET_SLOTS:
            w = self.facet_word(text, facet)
            out[facet] = {
                "slots": FACET_SLOTS[facet],
                "trivial": w == self.zero_word,
                "type_word": "".join(str(self.class_type(c)) for c in w),
                "axis_planes": [k for k, c in enumerate(w)
                                if self.class_type(c) == 2],
            }
        return out

    def monster_check(self, lhs: str, rhs: str) -> Dict[str, object]:
        """
        Decide an equation ENTIRELY INSIDE the Monster index set.

        The stack is faithful, so two carriers are equal exactly when their
        ten Monster addresses agree plane by plane; and by linearity the same
        holds facet by facet.  The GLM-2 admissibility rule is a conjunction
        of facet questions, so each one becomes a word comparison:

            dimension word agrees            the ten SI-style exponents match
            scale word agrees                the decimal scales match
            tensor word agrees               rank and the P, T, C data match
            kind words agree, OR one of      nominal kind clashes only when
              them is the zero word            both concepts are labelled

        `domain` and `context` are recorded too.  The GLM audit deliberately
        ignores them, so the Monster sees strictly more here than the verdict
        uses, and says so: two concepts can be admissible and still have
        different domain words.

        The report also states what PLANE 0 OF THE FULL CARRIER alone would
        have said.  Plane 0 is a single reduction mod 2, and on nearly every
        pair it says "agree" — the classic false positive E = m c^4 is one of
        these.  That is the mod-2 ceiling of GLM-1, seen from inside the
        Monster, and the reason the system reasons with the whole stack.
        """
        facets: Dict[str, object] = {}
        agree: Dict[str, bool] = {}
        for facet in FACET_SLOTS:
            wa, wb = self.facet_word(lhs, facet), self.facet_word(rhs, facet)
            differ = [k for k in range(len(wa)) if wa[k] != wb[k]]
            agree[facet] = not differ
            facets[facet] = {
                "agrees": not differ,
                "differing_planes": differ,
                "lhs_trivial": wa == self.zero_word,
                "rhs_trivial": wb == self.zero_word,
            }
        kind_ok = (agree["kind"] or facets["kind"]["lhs_trivial"]
                   or facets["kind"]["rhs_trivial"])
        admissible = (agree["dimension"] and agree["scale"]
                      and agree["tensor"] and kind_ok)

        sa, sb = self.stack(lhs), self.stack(rhs)
        differ_full = [k for k in range(len(sa)) if sa[k] != sb[k]]
        glm = bool(self.audit(lhs, rhs).admissible)
        failed = [f for f in ("dimension", "scale", "tensor")
                  if not agree[f]] + ([] if kind_ok else ["kind"])
        return {
            "lhs": lhs, "rhs": rhs,
            "verdict": "ADMISSIBLE" if admissible else "REJECTED",
            "failing_facets": failed,
            "facets": facets,
            "same_domain": agree["domain"],
            "carriers_identical": not differ_full,
            "differing_planes": differ_full,
            "plane0_agrees": sa[0] == sb[0],
            "relation_word": [RELATION_BY_PRODUCT_TYPE[
                self.class_type(ca ^ cb)][0] for ca, cb in zip(sa, sb)],
            "mod2_false_positive": sa[0] == sb[0] and not admissible,
            "glm_verdict": "ADMISSIBLE" if glm else "REJECTED",
            "agrees_with_glm": glm == admissible,
        }

    def _griess_of_point(self, x: Vec) -> GR.GriessVector:
        """The Griess vector of a bare lattice point, as for a concept."""
        g = GR.zero()
        for k, p in enumerate(L2.class_stack(x, self.depth, self.offset)):
            if self.class_type(p) == 2:
                g = g + SGN.canonical_axis(p).scale(F(1, 1 << k))
        return g

    def analogy(self, a: str, b: str, c: str, count: int = 5,
                limit: Optional[int] = None) -> Dict[str, object]:
        """
        Solve "a is to b as c is to what?".

        Composition of meanings adds carriers, so the answer's carrier is
        x_b - x_a + x_c.  That point is a lattice point like any other, so it
        has its own Monster address and its own Griess vector, and the
        register can be ranked against it in the invariant form.  If some
        concept sits exactly on the point, it is named as the exact answer.
        """
        xa, xb, xc = self.carrier(a), self.carrier(b), self.carrier(c)
        target = tuple(q - p + r for p, q, r in zip(xa, xb, xc))
        names = self.list_concepts()
        if limit:
            names = names[:limit]
        exact = [n for n in names if tuple(self.carrier(n)) == target]
        planes = L2.class_stack(target, self.depth, self.offset)
        g = self._griess_of_point(target)
        scored = []
        for n in names:
            if n in (a, b, c):
                continue
            try:
                sn = self.stack(n)
                agree = sum(1 for p, q in zip(planes, sn) if p == q)
                scored.append((agree, g.form(self.griess_vector(n)), n))
            except Exception:
                continue
        scored.sort(key=lambda t: (-t[0], -t[1], t[2]))
        return {
            "question": f"{a} : {b} :: {c} : ?",
            "exact": exact,
            "target_types": [self.class_type(p) for p in planes],
            "target_in_lambda":
                L2.class_stack_rebuild(planes, self.offset) == target,
            "nearest": [(n, f"{agree}/{self.depth} planes, ({sim})")
                        for agree, sim, n in scored[:count]],
            "best": scored[0][2] if scored else None,
        }

    # ── censuses over the library ───────────────────────────────────────
    def census(self, limit: Optional[int] = None) -> Dict[str, object]:
        """How the library sits in the Monster."""
        names = self.list_concepts()
        if limit:
            names = names[:limit]
        by_type: Dict[int, int] = {}
        axes_per: Dict[int, int] = {}
        carriers = set()
        failed = 0
        for n in names:
            try:
                planes = self.stack(n)
            except Exception:
                failed += 1
                continue
            carriers.add(self.carrier(n))
            types = [self.class_type(p) for p in planes]
            for t in types:
                by_type[t] = by_type.get(t, 0) + 1
            k = sum(1 for t in types if t == 2)
            axes_per[k] = axes_per.get(k, 0) + 1
        return {
            "concepts": len(names),
            "distinct_carriers": len(carriers),
            "unencodable": failed,
            "planes_per_concept": self.depth,
            "plane_types": dict(sorted(by_type.items())),
            "axis_planes_per_concept": dict(sorted(axes_per.items())),
            "concepts_with_an_axis": sum(v for k, v in axes_per.items() if k),
        }

    def relation_census(self, limit: int = 40, plane: int = 0
                        ) -> Dict[str, int]:
        """The Monster class of every pair of concepts, on one plane."""
        names = self.list_concepts()[:limit]
        classes = []
        for n in names:
            try:
                classes.append(self.stack(n)[plane])
            except Exception:
                continue
        out: Dict[str, int] = {}
        for i, ca in enumerate(classes):
            for cb in classes[i + 1:]:
                name = RELATION_BY_PRODUCT_TYPE[self.class_type(ca ^ cb)][0]
                out[name] = out.get(name, 0) + 1
        return dict(sorted(out.items()))

    # ── summary ─────────────────────────────────────────────────────────
    def summary(self) -> Dict[str, object]:
        return {
            "concepts": len(self.list_concepts()),
            "carrier": "Leech lattice point, derived from the meaning",
            "monster_index_set": "Lambda/2Lambda, 2^24 classes",
            "planes_per_concept": self.depth,
            "stack_offset": self.offset,
            "even_griess_dimension": GR.DIM_EVEN,
            "axes_available": GR.DIM_B,
            "group": "Q = 2^(1+24)_+ inside 2^(1+24).Co_1",
            "rep_dimension": XS.REP_DIM,
        }


REASONER = MonsterReasoner()


# ══════════════════════════════════════════════════════════════════════════════
#  DEMONSTRATION
# ══════════════════════════════════════════════════════════════════════════════

def _line(title: str) -> None:
    print(f"\n{title}\n{'-' * len(title)}")


def demonstrate() -> None:
    r = REASONER
    print(banner("GLM-3  REASONER  —  demonstration"))
    for k, v in r.summary().items():
        print(f"  {k:26s} {v}")

    _line("1.  The retained GLM layer still works")
    for lhs, rhs in (("energy", "mass*speed^2"), ("energy", "mass*speed^4"),
                     ("force", "mass*acceleration")):
        a = r.audit(lhs, rhs)
        verdict = "ADMISSIBLE" if a.admissible else "REJECTED"
        print(f"  {lhs} = {rhs:22s} {verdict}")
    s = r.solve("energy", ["mass", "speed"])
    print(f"  solve energy from mass, speed  : {s.formula()}")

    _line("2.  A concept is a stack of Monster addresses")
    for name in ("energy", "mass", "speed", "entropy"):
        ad = r.address(name)
        print(f"  {name:10s} types {ad['type_word']}  axes at planes "
              f"{ad['axis_planes']}  frames at {ad['frame_planes']}")
    print(f"  the stack rebuilds the carrier exactly: "
          f"{r.address('energy')['stack_rebuilds_carrier']}")

    _line("3.  Composing meanings is multiplying in the extraspecial group")
    g = r.composition_is_group_law("mass", "speed")
    print(f"  classes add                    : {g['classes_add']}")
    print(f"  x_u x_v has class [u + v]      : {g['group_matches']}")
    print(f"  central phase = cocycle f(u,v) : {g['phase_is_the_cocycle']}"
          f"  (phase {g['central_phase']})")
    print(f"  the word of energy in Q        : {r.group_word('energy')}")

    _line("4.  A concept's axis satisfies the Monster fusion law")
    fu = r.fusion("energy")
    print(f"  energy carries an axis on plane {fu['plane']}: idempotent "
          f"{fu['idempotent']}, norm one {fu['norm_one']}")
    for k, v in fu["rules"].items():
        print(f"    {k:26s} {v}")
    d = fu["eigenspace_dimensions"]
    print(f"  eigenspace dimensions          : 1 -> {d['1']}, "
          f"0 -> {fmt_int(d['0'])}, 1/4 -> {fmt_int(d['1/4'])}, "
          f"1/32 -> {fmt_int(d['1/32'])}")

    _line("5.  The Monster relation of two concepts, plane by plane")
    for pair in (("energy", "torque"), ("energy", "mass"), ("mass", "speed")):
        rel = r.relation(*pair)
        print(f"  {pair[0]:8s} vs {pair[1]:8s} {' '.join(rel['relation_word'])}"
              f"   checked {rel['checked_planes']} planes, all correct: "
              f"{rel['all_predictions_hold']}")

    _line("6.  A 2A triangle: the Monster carrying out GLM composition")
    found = r.find_triangle(limit=90)
    if found:
        t = r.triangle(*found)
        print(f"  concepts                       : {found[0]} , {found[1]}")
        print(f"  third axis is their product    : "
              f"{t['third_class_is_the_product_concept']}")
        print(f"  a . b = (1/8)(a + b - a_ab)    : {t['sakuma_identity']}")
        print(f"  subalgebra dimension           : "
              f"{t['subalgebra_dimension']}  (Norton-Sakuma 2A)")

    _line("7.  Similarity in the Griess form")
    for n in ("energy", "power"):
        print(f"  nearest to {n}: " + ", ".join(
            f"{m} ({s})" for m, s in r.neighbours(n, count=5, limit=120)))

    _line("8.  A concept's involution two-colours the library")
    orb = r.involution_orbit("speed", limit=40)
    print(f"  fixed axes                     : {orb['fixed_count']}")
    print(f"  axes negated                   : {orb['moved_count']}")
    print(f"  examples negated               : {', '.join(orb['moved'][:6])}")

    _line("9.  The multi-MOG-cube of a concept")
    m = r.mog("energy")
    print(f"  Golay plane of the carrier     : {m['golay_plane']} "
          f"(weight {m['golay_weight']}, codeword "
          f"{m['golay_plane_is_a_codeword']})")
    print(f"  hexacode shadow                : {m['hexacode_shadow']}")
    print(f"  basis planes                   : {m['basis_planes'][:6]}")
    print(f"  their types                    : {m['basis_types']}")
    print("  plane 1 as a MOG frame:")
    for row in m["basis_frame_of_plane1"]:
        print(f"      {' '.join(str(b) for b in row)}")

    _line("10. Where the library sits in the Monster")
    c = r.census()
    print(f"  concepts / distinct carriers   : {c['concepts']} / "
          f"{c['distinct_carriers']}")
    print(f"  plane types over the library   : {c['plane_types']}")
    print(f"  axis planes per concept        : {c['axis_planes_per_concept']}")
    print(f"  concepts with at least one axis: {c['concepts_with_an_axis']}")
    print(f"  relation census on plane 0     : {r.relation_census(40)}")

    _line("11. Checking an equation without leaving the Monster")
    pairs = (("mass*speed^2", "speed^2*mass"),
             ("mass*speed^2", "mass*speed^4"),
             ("force*length", "mass*speed^2"))
    reports = [r.monster_check(lhs, rhs) for lhs, rhs in pairs]
    for (lhs, rhs), k in zip(pairs, reports):
        flag = "  <- mod-2 false positive" if k["mod2_false_positive"] else ""
        p0 = "AGREE" if k["plane0_agrees"] else "DIFFER"
        print(f"  {lhs:14s} = {rhs:14s} {k['verdict']:11s}"
              f"  differing planes {str(k['differing_planes']):12s}"
              f"  plane 0 alone says {p0}{flag}")
    print("  every verdict agrees with the GLM dimensional audit: "
          f"{all(k['agrees_with_glm'] for k in reports)}")

    _line("12. A metric on meanings, not a ranking")
    print(f"  d(energy, work)                : {r.distance('energy', 'work')}")
    print(f"  d(energy, mass)                : {r.distance('energy', 'mass')}")
    print(f"  d(energy, entropy)             : "
          f"{r.distance('energy', 'entropy')}")
    dab, dbc, dac = (r.distance2("energy", "mass"),
                     r.distance2("mass", "speed"),
                     r.distance2("energy", "speed"))
    print(f"  triangle inequality on that triple: "
          f"{MET.triangle_holds(dab, dbc, dac)}")
    print("  nearest neighbours of energy   :")
    for n, d in r.nearest("energy", count=5, limit=200):
        print(f"    {n:28s} {d}")

    _line("13. The whole 196,884: the odd part is present")
    led = r.ledger()
    w = led["whole"]
    print(f"  even part                      : "
          f"{fmt_int(GR.DIM_EVEN)} = 300 + 98,280")
    print(f"  odd part                       : "
          f"{fmt_int(OD.DIM_ODD)} = 24 x 4,096")
    print(f"  eigenvalues 1 / 0 / 1/4 / 1/32 : {w['1']} / "
          f"{fmt_int(w['0'])} / {fmt_int(w['1/4'])} / {fmt_int(w['1/32'])}"
          f"  = {fmt_int(w['total'])}")
    print(f"  these are the classical 2A numbers: {led['agrees']}")
    ov = r.odd_view("energy")
    print(f"  energy's axis on plane {ov['plane']}: the canonical axis acts "
          f"by {ov['eigenvalue_of_the_canonical_axis']}, the other by "
          f"{ov['eigenvalue_of_the_other_axis']}")
    print(f"  so the two signs have different Miyamoto involutions: "
          f"{ov['the_odd_part_separates_them']}")

    _line("14. Analogy solved as a lattice point")
    an = r.analogy("mass", "force", "time")
    print(f"  {an['question']}")
    print(f"  target is itself in Lambda      : {an['target_in_lambda']}")
    print(f"  target plane types              : {an['target_types']}")
    for n, s_ in an["nearest"]:
        print(f"    {n:28s} {s_}")
    print()


# ══════════════════════════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════════════════════════

def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    if not argv:
        demonstrate()
        return 0
    cmd, rest = argv[0], argv[1:]
    r = REASONER
    if cmd == "address" and rest:
        for k, v in r.address(" ".join(rest)).items():
            print(f"  {k:28s} {v}")
    elif cmd == "stack" and rest:
        name = " ".join(rest)
        for k, p in enumerate(r.stack(name)):
            t = r.class_type(p)
            print(f"  plane {k}: 0x{p:06x}  type {t}"
                  f"{'  (2A axis)' if t == 2 else ''}")
    elif cmd == "relation" and len(rest) >= 2:
        rel = r.relation(rest[0], rest[1])
        print(f"  relation word : {' '.join(rel['relation_word'])}")
        print(f"  similarity    : {rel['similarity']}")
        for p in rel["planes"]:
            print(f"    plane {p['plane']}: types {p['type_a']}/{p['type_b']}"
                  f" -> {p['monster_class']}  {p.get('inner_product', '')}"
                  f" {p.get('matches', '')}")
    elif cmd == "similar" and rest:
        for n, s in r.neighbours(" ".join(rest), count=12):
            print(f"  {n:28s} {s}")
    elif cmd == "distance" and len(rest) >= 2:
        print(f"  d({rest[0]}, {rest[1]})^2 = {r.distance2(rest[0], rest[1])}")
        print(f"  d({rest[0]}, {rest[1]})   = {r.distance(rest[0], rest[1])}")
    elif cmd == "nearest" and rest:
        for n, d in r.nearest(" ".join(rest), count=12):
            print(f"  {n:28s} {d}")
    elif cmd == "cluster" and rest:
        groups = r.cluster(F(rest[0]), limit=int(rest[1]) if len(rest) > 1
                           else 200)
        print(f"  {len(groups)} clusters at threshold {rest[0]}")
        for g in groups[:12]:
            print(f"    {len(g):3d}  {', '.join(g[:8])}"
                  f"{' ...' if len(g) > 8 else ''}")
    elif cmd == "ledger":
        led = r.ledger()
        for k, v in led["whole"].items():
            print(f"  eigenvalue {k:5s} {fmt_int(v)}")
        print(f"  agrees with the classical 2A numbers: {led['agrees']}")
    elif cmd == "odd" and rest:
        for k, v in r.odd_view(" ".join(rest)).items():
            print(f"  {k:34s} {v}")
    elif cmd == "triangle":
        found = r.find_triangle(limit=int(rest[0]) if rest else 90)
        if not found:
            print("  no 2A pair found in range")
            return 1
        print(f"  {found[0]} , {found[1]}")
        for k, v in r.triangle(*found).items():
            print(f"  {k:34s} {v}")
    elif cmd == "fusion" and rest:
        for k, v in r.fusion(" ".join(rest)).items():
            print(f"  {k:24s} {v}")
    elif cmd == "orbit" and rest:
        o = r.involution_orbit(" ".join(rest))
        print(f"  fixed  ({o['fixed_count']}): {', '.join(o['fixed'][:20])}")
        print(f"  moved  ({o['moved_count']}): {', '.join(o['moved'][:20])}")
    elif cmd == "frame" and rest:
        for k, v in r.frame(" ".join(rest)).items():
            print(f"  {k:20s} {v}")
    elif cmd == "mog" and rest:
        m = r.mog(" ".join(rest))
        for k, v in m.items():
            if k.endswith("frame") or k.startswith("basis_frame"):
                print(f"  {k}:")
                for row in v:
                    print(f"      {' '.join(str(b) for b in row)}")
            else:
                print(f"  {k:28s} {v}")
    elif cmd == "check" and len(rest) >= 2:
        for k, v in r.monster_check(rest[0], rest[1]).items():
            print(f"  {k:24s} {v}")
    elif cmd == "analogy" and len(rest) >= 3:
        out = r.analogy(rest[0], rest[1], rest[2])
        print(f"  {out['question']}")
        print(f"  exact          : {out['exact'] or 'none in the register'}")
        print(f"  target types   : {out['target_types']}")
        for n, s_ in out["nearest"]:
            print(f"    {n:28s} {s_}")
    elif cmd == "census":
        for k, v in r.census().items():
            print(f"  {k:28s} {v}")
    elif cmd == "audit" and len(rest) >= 2:
        print(r.audit(rest[0], rest[1]))
    elif cmd == "solve" and len(rest) >= 2:
        print(r.solve(rest[0], rest[1:]))
    else:
        print("  unknown command; run with no arguments for the demonstration")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
