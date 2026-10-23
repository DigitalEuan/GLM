"""``glm_universal.reasoning.lorentzian_lift`` -- the Golay tie space lifted to
the Lorentzian lattice ``II_{25,1}`` (Phase 182).

*Created 22 October 2026. Last altered 23 October 2026 (Phase 183: `tool
lorentz` asks the settling question and guards with the certificate).*

Where this comes from
---------------------
The owner's ``source_material/iter10_lorentzian.py`` proposed that the
ambiguous part of the GLM's 24-bit space -- the Golay decoder's ties, 1771 of
the 4096 cosets (``1771/4096 ~ 43 %`` of all words) -- could be resolved by
lifting to the 26-dimensional Lorentzian lattice ``II_{25,1}``, with the lift
``L(x) = (x, (1-|x|^2)/2, (1+|x|^2)/2)`` and a Householder reflection.
``studies/LORENTZIAN_LIFT_STUDY.md`` audits that script and this module is
the part of it that survives, in exact arithmetic.

What the lift does here
-----------------------
Coordinates are the script's ``(x, t, tau)`` with ``x`` in the Leech
lattice's raw scale (true norm = raw norm / 8, as everywhere in the
substrate), and the form ``<a, b> = a.x . b.x / 8 + a.t b.t - a.tau b.tau``.

* The **Weyl vector** of the lift is ``w = (0, -1, 1)``: ``<L(x), w> = -1``
  for every ``x`` (``LorentzianLift.inner_lift_weyl``). The script's
  ``(0, 1, 1)`` is ``2 L(0)``, the lift of the origin.
* The **roots** ``r`` with ``<r, r> = 2`` and ``<r, w> = -1`` are exactly
  ``r_l = L(l) - w`` (``root_char``); they lie in ``II_{25,1}`` exactly when
  ``l`` is a Leech point. Roots are indexed by **lattice points**, not by
  deep holes (Conway).
* The **key identity** ``<L(x), r_l> = 1 - |x - l|^2 / 2``
  (``inner_lift_root``): nearest-point decoding is a linear maximisation
  upstairs, a tie is the mirror of ``r_l - r_m`` (``tie_iff``), and scores
  from several readings **add**.
* **Every Golay tie is a deep hole** (``GolayDeepHole.golay_tie_deep_hole``):
  doubled, a word of coset weight 4 sits at true squared distance 2 -- the
  covering radius -- from the lattice. Its 48 nearest lattice points (8 for
  each of the 6 tied codewords) form the diagram ``A_1^24``, and the
  primitive null vector ``z = 2 L(x)`` of ``II_{25,1}`` is orthogonal to all
  48 of their roots (``hole_orth``).

What it cannot do
-----------------
No rule that is unchanged under reflections -- the reflection the script
proposes, any score built from Lorentzian inner products, the Weyl vector --
can break a tie (``reflection_invariant_tie``): the tie's own reflection fixes
the tied point and swaps the candidates. A tie is broken only by information
from outside it. :func:`resolve` is the form that information takes here: a
second reading, scored in the same frame and added.

Exactness
---------
``Fraction`` and ``int`` only (D7).
"""

from __future__ import annotations

from fractions import Fraction
from itertools import product
from typing import Dict, List, Optional, Sequence, Tuple

from ..substrate import leech2
from ..substrate import superposition as sup_mod

__all__ = [
    "SCALE", "LEAN_FILES", "LEAN_THEOREMS", "LVec", "inner", "lift", "WEYL",
    "SCRIPT_W", "root", "reflect", "in_ii", "doubled", "hamming",
    "hole_vertices", "tie_certificate", "score", "GUARD", "resolve",
    "resolve_text",
]

#: Raw Leech coordinates carry true norm ``raw / 8``.
SCALE = 8

#: The Lean files this module rests on, and the theorems it quotes.
LEAN_FILES: Tuple[str, ...] = ("RequestProject/GLM/LorentzianLift.lean",
                               "RequestProject/GLM/GolayDeepHole.lean")
LEAN_THEOREMS: Tuple[str, ...] = (
    "lift_null", "inner_lift_lift", "inner_lift_weyl", "scriptW_eq",
    "inner_lift_scriptW", "root_norm", "root_char", "inner_lift_root",
    "nearer_iff", "tie_iff", "root_sub_norm", "hole_orth", "refl_inner",
    "refl_fix_of_orth", "refl_swap", "tie_reflection",
    "reflection_invariant_tie", "context_break", "normSq_dbl_sub",
    "dbl_isLeech", "leech_far", "leech_dist_coset_weight",
    "golay_tie_deep_hole", "summed_score_le")

F = Fraction

#: A vector of ``Q^26`` in the script's coordinates ``(x_0..x_23, t, tau)``.
LVec = Tuple[Fraction, ...]


def inner(a: Sequence, b: Sequence) -> Fraction:
    """``x.x'/8 + t t' - tau tau'`` (the Euclidean part in raw Leech scale)."""
    space = sum((F(a[i]) * F(b[i]) for i in range(24)), F(0)) / SCALE
    return space + F(a[24]) * F(b[24]) - F(a[25]) * F(b[25])


def _q(x: Sequence) -> Fraction:
    return sum((F(v) * F(v) for v in x), F(0)) / SCALE


def lift(x: Sequence) -> LVec:
    """``L(x) = (x, (1 - q)/2, (1 + q)/2)`` with ``q`` the true norm of ``x``."""
    q = _q(x)
    return tuple(F(v) for v in x) + ((1 - q) / 2, (1 + q) / 2)


#: The Weyl vector of the lift.
WEYL: LVec = tuple([F(0)] * 24) + (F(-1), F(1))

#: The script's ``w = (0, ..., 0, 1, 1)`` -- which is ``2 L(0)``.
SCRIPT_W: LVec = tuple([F(0)] * 24) + (F(1), F(1))


def _sub(a: Sequence, b: Sequence) -> LVec:
    return tuple(F(a[i]) - F(b[i]) for i in range(26))


def _scale(k: Fraction, a: Sequence) -> LVec:
    return tuple(k * F(v) for v in a)


def root(point: Sequence) -> LVec:
    """``r_l = L(l) - w``: norm 2, ``<r_l, w> = -1``."""
    return _sub(lift(point), WEYL)


def reflect(s: Sequence, v: Sequence) -> LVec:
    """The Householder reflection ``v - 2<v,s>/<s,s> s``."""
    ss = inner(s, s)
    if ss == 0:
        raise ValueError("reflect: the mirror vector is null")
    return _sub(v, _scale(2 * inner(v, s) / ss, s))


def in_ii(v: Sequence) -> bool:
    """Membership of ``II_{25,1} = Lambda + U`` in the script's coordinates:
    the Euclidean part a Leech point, ``t + tau`` an integer and
    ``(tau - t)/2`` an integer."""
    xs = [F(c) for c in v[:24]]
    if any(c.denominator != 1 for c in xs):
        return False
    if not leech2.in_leech([int(c) for c in xs]):
        return False
    e = F(v[24]) + F(v[25])
    m = (F(v[25]) - F(v[24])) / 2
    return e.denominator == 1 and m.denominator == 1


def doubled(mask: int) -> Tuple[int, ...]:
    """The doubled word ``2b`` in raw coordinates (coordinate ``i`` is bit
    ``i``): a lattice point exactly when ``b`` is a codeword."""
    return tuple(2 * ((mask >> i) & 1) for i in range(24))


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def hole_vertices(mask: int) -> List[Tuple[int, ...]]:
    """The lattice points at raw squared distance 16 from ``2b`` for a word of
    coset weight 4: for each of the six tied codewords ``c``, the eight
    vectors equal to ``2b`` off ``b xor c`` and ``2b_i +- 2`` (in the residue
    class of ``2c_i`` mod 4) on it, with the sum condition."""
    s = sup_mod.superpose(mask)
    if s.weight != 4:
        return []
    x = doubled(mask)
    out = []
    for c in s.candidates:
        diff = [i for i in range(24) if ((mask ^ c) >> i) & 1]
        for signs in product((1, -1), repeat=len(diff)):
            v = list(x)
            for i, sg in zip(diff, signs):
                v[i] = x[i] + 2 * sg
            if leech2.in_leech(v):
                out.append(tuple(v))
    return sorted(set(out))


def tie_certificate(mask: int) -> Dict[str, object]:
    """The lifted reading of one word: unique, or the exact certificate of
    its tie (the deep hole, its vertices, and the null vector naming it)."""
    s = sup_mod.superpose(mask)
    x = doubled(mask)
    lx = lift(x)
    rec: Dict[str, object] = {
        "received": mask, "coset_weight": s.weight,
        "candidates": list(s.candidates), "ambiguous": s.ambiguous,
        "distance2": F(s.weight, 2),
        "lift_null": inner(lx, lx) == 0,
        "lift_weyl": inner(lx, WEYL),
    }
    if not s.ambiguous:
        return rec
    verts = hole_vertices(mask)
    roots = [root(v) for v in verts]
    orth = all(inner(lx, r) == 0 for r in roots)
    gram = {}
    for i in range(len(roots)):
        for j in range(i + 1, len(roots)):
            g = inner(roots[i], roots[j])
            gram[g] = gram.get(g, 0) + 1
    z = _scale(F(2), lx)
    rec.update({
        "vertices": len(verts),
        "per_candidate": len(verts) // max(1, len(s.candidates)),
        "vertex_distance2_raw": sorted({sum((a - b) ** 2 for a, b in zip(v, x))
                                        for v in verts}),
        "roots_orthogonal_to_lift": orth,
        "root_gram": {str(k): v for k, v in sorted(gram.items())},
        "null_vector": z,
        "null_vector_in_ii": in_ii(z) and inner(z, z) == 0,
        "lift_in_ii": in_ii(lx),
    })
    return rec


def score(readings: Sequence[int], codeword: int) -> Fraction:
    """``sum_j <L(2 b_j), r_{2c}>`` = ``sum_j (1 - hamming(b_j, c)/4)``."""
    rc = root(doubled(codeword))
    return sum((inner(lift(doubled(b)), rc) for b in readings), F(0))


#: The consistency guard of the answering path: every reading must lie
#: within Hamming distance 6 of the answer, i.e. score at least
#: ``1 - 6/4 = -1/2`` against its root (true squared distance at most 3).
GUARD = 6


def resolve(readings: Sequence[int],
            guard: Optional[int] = None) -> Dict[str, object]:
    """Decode one message from one or more 24-bit readings of it.

    The pool is every nearest codeword of every reading; each is scored by
    the sum of its Lorentzian scores against all the readings. A unique
    maximum is the answer; a tied maximum is refused, with the tied set and
    the tie certificate of the first reading -- never an arbitrary pick.
    With ``guard``, a unique maximum farther than ``guard`` from any reading
    is refused as ``inconsistent``: the readings do not look like readings of
    one message.
    """
    if not readings:
        raise ValueError("resolve: no readings")
    pool = sorted({c for b in readings
                   for c in sup_mod.superpose(b).candidates})
    scores = {c: score(readings, c) for c in pool}
    top = max(scores.values())
    best = [c for c in pool if scores[c] == top]
    out: Dict[str, object] = {
        "readings": list(readings), "pool": pool,
        "scores": {c: scores[c] for c in pool}, "best": best,
        "status": "resolved" if len(best) == 1 else "tied",
        "value": best[0] if len(best) == 1 else None,
    }
    if (guard is not None and out["value"] is not None
            and max(hamming(b, out["value"]) for b in readings) > guard):
        out["status"], out["value"] = "inconsistent", None
    return out


def resolve_text(arg: str) -> Tuple[bool, str, Dict[str, object]]:
    """``tool lorentz MASK [; MASK ...] [; @POS=BIT,...]``: the reply the
    toolbox gives.

    Since Phase 183 (``reasoning/lorentzian_evidence.py``) the answer must
    also lie inside the first reading's tie certificate, a single tie is
    refused with the question that settles it -- the sent bits at five
    positions, one in each of five tetrads of its sextet -- and a part
    ``@POS=BIT,...`` gives those bits back.
    """
    from ..runtime.toolbox import _parse_word  # local: toolbox imports us
    from . import lorentzian_evidence as le  # local: it imports this module
    parts = [p.strip() for p in arg.replace(",", ";").split(";") if p.strip()]
    bits: Dict[int, int] = {}
    words = []
    for p in parts:
        if p.startswith("@") or ("=" in p and not p.lower().startswith("0x")):
            for item in p.lstrip("@").split():
                pos, _, bit = item.partition("=")
                if (not pos.strip().isdigit() or bit.strip() not in ("0", "1")
                        or not 0 <= int(pos) < 24):
                    return False, (f"tool lorentz: '{p}' is not a revealed "
                                   f"bit; write @POS=BIT with 0 <= POS < 24 "
                                   f"and BIT 0 or 1"), {}
                bits[int(pos)] = int(bit)
        else:
            words.append(p)
    masks = [_parse_word(p) for p in words]
    if not masks or any(m is None for m in masks):
        return False, ("tool lorentz takes one or more 24-bit readings of the "
                       "same message, separated by ';' (decimal, 0x hex or "
                       "0b binary), and optionally the sent bits the tie asks "
                       "for as '@POS=BIT ...'"), {}
    cert = tie_certificate(masks[0])  # type: ignore[arg-type]
    if bits:
        st = le.settle(masks[0], bits)  # type: ignore[arg-type]
        figures = {"status": st["status"], "pool": len(st["candidates"]),
                   "coset_weight": cert["coset_weight"],
                   "revealed": len(bits)}
        if st["status"] == "resolved":
            v = st["value"]
            far = max(hamming(b, v) for b in masks)  # type: ignore[arg-type]
            if far > GUARD:
                return False, (f"lorentz: refused -- the revealed bits pick "
                               f"{v:#08x}, but it is {far} bits from one of "
                               f"the readings, more than the guard of "
                               f"{GUARD}"), dict(figures, far=far)
            figures["value"] = v
            return True, (f"lorentz: resolved to codeword {v:#08x} -- of the "
                          f"{len(st['candidates'])} tied candidate(s) of the "
                          f"first reading it is the only one whose bits agree "
                          f"with the {len(bits)} revealed"), figures
        if st["status"] == "contradicted":
            return False, (f"lorentz: refused -- no tied candidate of the "
                           f"first reading agrees with the {len(bits)} "
                           f"revealed bit(s)"), figures
        return False, (f"lorentz: refused -- {len(st['alive'])} tied "
                       f"candidates still agree with the {len(bits)} revealed "
                       f"bit(s); reveal the bits at positions "
                       f"{', '.join(map(str, le.settling_question(masks[0])))}"
                       ), figures
    res = le.certificate_resolve(masks, guard=GUARD)  # type: ignore[arg-type]
    figures = {"status": res["status"], "pool": len(res["pool"]),
               "coset_weight": cert["coset_weight"]}
    if res["status"] == "resolved":
        v = res["value"]
        text = (f"lorentz: resolved to codeword {v:#08x} from "
                f"{len(masks)} reading(s); its summed Lorentzian score "
                f"{res['scores'][v]} is the unique maximum over "
                f"{len(res['pool'])} candidate(s)")
        figures["value"] = v
        return True, text, figures
    if res["status"] == "inconsistent":
        far = max(hamming(b, res["best"][0]) for b in masks)
        return False, (f"lorentz: refused -- the best-scoring codeword "
                       f"{res['best'][0]:#08x} is {far} bits from one of the "
                       f"readings, more than the guard of {GUARD}: these do "
                       f"not read as one message"), dict(figures, far=far)
    if res["status"] == "outside_certificate":
        return False, (f"lorentz: refused -- the best-scoring codeword "
                       f"{res['best'][0]:#08x} is not one of the "
                       f"{len(cert['candidates'])} codewords the first reading "
                       f"ties between: the further readings would overrule "
                       f"the tie instead of choosing within it"), figures
    text = (f"lorentz: refused -- {len(res['best'])} codewords tie at summed "
            f"score {res['scores'][res['best'][0]]}. The first reading has "
            f"coset weight {cert['coset_weight']}")
    if cert["ambiguous"]:
        ask = le.settling_question(masks[0])  # type: ignore[arg-type]
        text += (f": doubled, it is a deep hole of the Leech lattice at the "
                 f"covering radius, with {cert['vertices']} vertices "
                 f"({cert['per_candidate']} per tied codeword), named by the "
                 f"null vector 2L(x) of II_25,1. No reflection can break this "
                 f"tie; give another reading of the same message, or the sent "
                 f"bits at positions {', '.join(map(str, ask))} (one in each "
                 f"of {len(ask)} tetrads of its sextet; no fewer settle it) as "
                 f"'@POS=BIT ...'")
        figures["ask"] = ask
    figures["tied"] = len(res["best"])
    return False, text, figures
