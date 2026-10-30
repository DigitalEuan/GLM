"""``glm_universal.reasoning.lorentzian_evidence`` -- the Lorentzian lift as an
evidence space for reasoning in general (Phase 183).

*Created 23 October 2026.*

Where this comes from
---------------------
Phase 182 (``studies/LORENTZIAN_LIFT_STUDY.md``, ``reasoning/lorentzian_lift.py``)
lifted the Golay tie space to ``II_{25,1}`` and found that the lift certifies a
tie exactly but no reflection can break one; summed scores over further
readings did. It left three lines (``STATUS.md`` §2.1 item 11): a guard that
keeps a reading of a different message from misleading the sum, the same
machinery on ties beyond the Golay layer, and a surface that collects the
further readings. The owner asked for the deeper question behind them: can
the ambiguous space be of use for *general* reasoning, not only puzzles?

``studies/LORENTZIAN_EVIDENCE_STUDY.md`` answers it; this module is the
mechanism, and ``RequestProject/GLM/LorentzianEvidence.lean`` is the
specification (D8). Nothing in it is specific to the Golay code: points are
rational vectors of any length, candidates are any labelled points, and a
*cue* is a point with a weight.

What the lift gives a reasoner
------------------------------
With ``L(x) = (x, (1 - |x|^2)/2, (1 + |x|^2)/2)`` and ``w = (0, -1, 1)``:

* **Cues add** (``inner_evid``, ``evid_score``): the evidence vector
  ``V = sum w_i L(x_i)`` scores a candidate ``l`` by
  ``W - (1/2) sum w_i |x_i - l|^2``.
* **The decomposition** (``evidence_decomp``): ``V = W L(xbar) + (D/2) w``,
  where ``xbar`` is the weighted consensus and ``D`` the dispersion. So the
  evidence ranks candidates by distance to the consensus (``evid_rank``) and
  ties exactly on the consensus's mirrors (``evid_tie``).
* **Disagreement is a norm** (``evid_norm``): ``<V, V> = -W D``. With
  positive weights the evidence is null exactly when every cue agrees
  (``evid_null_iff``): agreement is light-like, conflict time-like.
* **A sound guard** (``dispersion_guard_sound``): cues that are honest
  readings of one point within budgets ``rho_i`` have ``D <= sum w_i rho_i``.
* **Analogy is evidence** (``analogy_evidence``): ``A : B :: C : ?`` is
  ``L B - L A + L C``, whose consensus is the displacement target
  ``C + B - A``. Several examples of one relation are several such vectors,
  summed; whether they state *one* relation is whether their targets agree,
  which is ``D = 0`` on the targets.
* **The question a tie asks** (``agree_on_iff``, ``separates_iff``,
  ``card_ge_of_separates``): for a Golay tie the six candidates are the word
  flipped on the six tetrads of a sextet; revealing a set ``Q`` of positions
  tells two candidates apart exactly when ``Q`` meets one of their tetrads, so
  five positions (one in each of five tetrads) settle the tie and no four do.

Exactness
---------
``Fraction`` and ``int`` only (D7).
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from ..substrate import superposition as sup_mod
from . import lorentzian_lift as ll

__all__ = [
    "LEAN_FILE", "LEAN_THEOREMS", "Cue", "weight", "consensus", "dispersion",
    "lift", "weyl", "inner", "root", "evidence", "decomposition_holds",
    "decide", "analogy_cues", "target_cues", "sextet_blocks",
    "settling_question", "settle", "certificate_resolve", "relation_answer",
    "physics_classes", "evidence_text",
]

F = Fraction

#: The Lean file this module rests on, and the theorems it quotes.
LEAN_FILE = "RequestProject/GLM/LorentzianEvidence.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "inner_evid", "evid_score", "steiner", "evidence_decomp",
    "evid_score_cent", "evid_rank", "evid_tie", "evid_norm", "disp_nonneg",
    "disp_le", "dispersion_guard_sound", "disp_eq_zero_iff", "evid_null_iff",
    "analogy_evidence", "analogy_score", "agree_on_iff", "separates_iff",
    "card_ge_of_separates")

#: A cue: a rational point and its weight.
Cue = Tuple[Tuple[Fraction, ...], Fraction]


# ===========================================================================
# 1.  THE EVIDENCE VECTOR, IN ANY DIMENSION
# ===========================================================================
# ``scale`` divides the Euclidean part of the form, so that raw Leech
# coordinates (true norm = raw / 8) and register coordinates (scale 1) use the
# same code.

def _vec(x: Sequence) -> Tuple[Fraction, ...]:
    return tuple(F(v) for v in x)


def _nsq(x: Sequence, scale: int = 1) -> Fraction:
    return sum((F(v) * F(v) for v in x), F(0)) / scale


def _d2(x: Sequence, y: Sequence, scale: int = 1) -> Fraction:
    return sum(((F(a) - F(b)) ** 2 for a, b in zip(x, y)), F(0)) / scale


def weight(cues: Sequence[Cue]) -> Fraction:
    """``W = sum w_i``."""
    return sum((F(w) for _, w in cues), F(0))


def consensus(cues: Sequence[Cue]) -> Tuple[Fraction, ...]:
    """The weighted centroid ``xbar = W^-1 sum w_i x_i`` (``W != 0``)."""
    W = weight(cues)
    if W == 0:
        raise ValueError("consensus: the total weight is zero")
    n = len(cues[0][0])
    return tuple(sum((F(w) * F(x[j]) for x, w in cues), F(0)) / W
                 for j in range(n))


def dispersion(cues: Sequence[Cue], scale: int = 1) -> Fraction:
    """``D = sum w_i |x_i - xbar|^2`` -- the disagreement of the cues."""
    c = consensus(cues)
    return sum((F(w) * _d2(x, c, scale) for x, w in cues), F(0))


def lift(x: Sequence, scale: int = 1) -> Tuple[Fraction, ...]:
    """``L(x) = (x, (1 - |x|^2)/2, (1 + |x|^2)/2)``."""
    q = _nsq(x, scale)
    return _vec(x) + ((1 - q) / 2, (1 + q) / 2)


def weyl(n: int) -> Tuple[Fraction, ...]:
    """``w = (0, ..., 0, -1, 1)``."""
    return tuple([F(0)] * n) + (F(-1), F(1))


def inner(a: Sequence, b: Sequence, scale: int = 1) -> Fraction:
    """``x . x' / scale + t t' - tau tau'``."""
    n = len(a) - 2
    space = sum((F(a[i]) * F(b[i]) for i in range(n)), F(0)) / scale
    return space + F(a[n]) * F(b[n]) - F(a[n + 1]) * F(b[n + 1])


_ROOTS: Dict[Tuple[Tuple[Fraction, ...], int], Tuple[Fraction, ...]] = {}


def root(point: Sequence, scale: int = 1) -> Tuple[Fraction, ...]:
    """``r_l = L(l) - w`` (remembered per point: candidate sets are reused)."""
    key = (_vec(point), scale)
    got = _ROOTS.get(key)
    if got is None:
        lx, w = lift(point, scale), weyl(len(point))
        got = tuple(p - q for p, q in zip(lx, w))
        if len(_ROOTS) < 100000:
            _ROOTS[key] = got
    return got


def evidence(cues: Sequence[Cue], scale: int = 1) -> Tuple[Fraction, ...]:
    """``V = sum w_i L(x_i)``."""
    n = len(cues[0][0])
    out = [F(0)] * (n + 2)
    for x, w in cues:
        for j, v in enumerate(lift(x, scale)):
            out[j] += F(w) * v
    return tuple(out)


def decomposition_holds(cues: Sequence[Cue], scale: int = 1) -> bool:
    """``V == W L(xbar) + (D/2) w`` and ``<V, V> == -W D``, exactly
    (``evidence_decomp``, ``evid_norm``)."""
    W, c, D = weight(cues), consensus(cues), dispersion(cues, scale)
    V = evidence(cues, scale)
    rhs = tuple(W * a + D / 2 * b
                for a, b in zip(lift(c, scale), weyl(len(c))))
    return V == rhs and inner(V, V, scale) == -W * D


# ===========================================================================
# 2.  DECIDING OVER ANY LABELLED CANDIDATE SET
# ===========================================================================

def decide(cues: Sequence[Cue], candidates: Mapping[str, Sequence],
           scale: int = 1, budget: Optional[Fraction] = None
           ) -> Dict[str, object]:
    """Rank ``candidates`` by the evidence score ``<V, r_l>``.

    * a unique maximum is ``resolved``;
    * a tied maximum is ``tied``: the tied names are the certificate, and
      by ``evid_tie`` the tie is the consensus lying on their mirrors;
    * with ``budget``, evidence whose dispersion exceeds it is
      ``conflicting`` -- the cues do not read as one point within the budget
      (``dispersion_guard_sound``: an honest set is never refused).
    """
    if not cues:
        raise ValueError("decide: no cues")
    V = evidence(cues, scale)
    D = dispersion(cues, scale)
    scores = {name: inner(V, root(p, scale), scale)
              for name, p in candidates.items()}
    top = max(scores.values())
    best = sorted(name for name, s in scores.items() if s == top)
    rest = [s for s in scores.values() if s != top]
    out: Dict[str, object] = {
        "weight": weight(cues), "consensus": consensus(cues),
        "dispersion": D, "norm": inner(V, V, scale),
        "best": best, "top": top,
        "margin": (top - max(rest)) if rest else None,
        "status": "resolved" if len(best) == 1 else "tied",
        "value": best[0] if len(best) == 1 else None,
    }
    if budget is not None and D > budget:
        out["status"], out["value"] = "conflicting", None
    return out


def analogy_cues(a: Sequence, b: Sequence, c: Sequence) -> List[Cue]:
    """``A : B :: C : ?`` as cues with weights ``1, -1, 1``
    (``analogy_evidence``)."""
    return [(_vec(b), F(1)), (_vec(a), F(-1)), (_vec(c), F(1))]


def target_cues(examples: Sequence[Tuple[Sequence, Sequence]],
                c: Sequence) -> List[Cue]:
    """Several examples of one relation applied to ``c``: one unit cue at
    each displacement target ``c + b_i - a_i``. By ``analogy_evidence`` the
    sum of the analogies' evidence vectors differs from this one's only by a
    multiple of ``w``, which scores every candidate alike; by
    ``evid_null_iff`` its dispersion is zero exactly when the examples state
    one relation."""
    return [(tuple(F(z) + F(y) - F(x) for x, y, z in zip(a, b, c)), F(1))
            for a, b in examples]


# ===========================================================================
# 3.  THE QUESTION A GOLAY TIE ASKS
# ===========================================================================

def sextet_blocks(mask: int) -> List[Tuple[int, int]]:
    """``(candidate, block)`` for each nearest codeword of ``mask``: the
    block is ``mask xor candidate``. At coset weight 4 these are the six
    tetrads of a sextet, pairwise disjoint."""
    s = sup_mod.superpose(mask)
    return [(c, mask ^ c) for c in sorted(s.candidates)]


def settling_question(mask: int) -> List[int]:
    """The positions whose sent bits settle the tie: the least position of
    every block but the last (``separates_iff``), so ``m - 1`` positions for
    ``m`` candidates -- five for a sextet, and no fewer will do
    (``card_ge_of_separates``). Empty when the reading is not a tie."""
    blocks = sextet_blocks(mask)
    if len(blocks) < 2:
        return []
    return sorted(min(i for i in range(24) if (blk >> i) & 1)
                  for _, blk in blocks[:-1])


def settle(mask: int, revealed: Mapping[int, int]) -> Dict[str, object]:
    """Keep the tied candidates whose bits agree with the ``revealed`` sent
    bits; resolved when exactly one survives."""
    blocks = sextet_blocks(mask)
    alive = [c for c, _ in blocks
             if all(((c >> i) & 1) == int(bit) for i, bit in revealed.items())]
    return {"candidates": [c for c, _ in blocks], "alive": alive,
            "status": ("resolved" if len(alive) == 1 else
                       "contradicted" if not alive else "tied"),
            "value": alive[0] if len(alive) == 1 else None}


def certificate_resolve(readings: Sequence[int],
                        guard: int = ll.GUARD) -> Dict[str, object]:
    """Phase 182's guarded summed score, with the certificate as a second
    guard: when the first reading is a tie the answer must be one of its tied
    candidates -- further readings choose *within* the certificate, they do
    not overrule it. Sound: whenever the first reading's tied set holds the
    sent codeword this refuses no answer the guarded rule got right."""
    res = ll.resolve(readings, guard=guard)
    first = sup_mod.superpose(readings[0])
    if (res["value"] is not None and first.ambiguous
            and res["value"] not in first.candidates):
        res = dict(res, status="outside_certificate", value=None)
    return res


# ===========================================================================
# 4.  RELATIONS OVER A REGISTER: THE PHYSICS DIMENSION LAYER
# ===========================================================================

def physics_classes() -> Tuple[Dict[str, Tuple[Fraction, ...]],
                               Dict[Tuple[Fraction, ...], List[str]]]:
    """``name -> EXT10 exponents`` and ``exponents -> names`` for the
    physics register."""
    from ..data_objects import physics as ph
    vec: Dict[str, Tuple[Fraction, ...]] = {}
    cls: Dict[Tuple[Fraction, ...], List[str]] = {}
    for q in ph.load_physics_register():
        e = tuple(F(v) for v in q.exps_ext10)
        vec[q.name] = e
        cls.setdefault(e, []).append(q.name)
    for k in cls:
        cls[k].sort()
    return vec, cls


def relation_answer(examples: Sequence[Tuple[str, str]], c: str,
                    vec: Optional[Mapping[str, Tuple[Fraction, ...]]] = None,
                    cls: Optional[Mapping[Tuple[Fraction, ...], List[str]]]
                    = None) -> Dict[str, object]:
    """``a_1 : b_1 , a_2 : b_2 , ... :: c : ?`` at the physics dimension
    layer.

    * ``conflicting`` -- the examples' targets disagree (``D > 0``): they do
      not state one relation, and nothing is answered;
    * ``absent`` -- they agree, and no register quantity has the target
      dimension;
    * ``class`` -- they agree and the target is a dimension class; the
      class's names are the certificate. One name is never chosen: every
      member of a class is equidistant from the target, so by ``evid_tie``
      the dimension layer cannot choose between them.
    """
    if vec is None or cls is None:
        vec, cls = physics_classes()
    cues = target_cues([(vec[a], vec[b]) for a, b in examples], vec[c])
    D = dispersion(cues)
    out: Dict[str, object] = {"examples": list(examples), "query": c,
                              "dispersion": D,
                              "targets": [x for x, _ in cues]}
    if D != 0:
        out.update(status="conflicting", names=[])
        return out
    target = cues[0][0]
    names = list(cls.get(target, []))
    out.update(target=target, names=names,
               status="class" if names else "absent")
    return out


# ===========================================================================
# 5.  THE TOOL
# ===========================================================================

def _dim(e: Sequence[Fraction]) -> str:
    from ..data_objects import physics as ph
    return ph.dimension_string(tuple(e))


def evidence_text(arg: str) -> Tuple[bool, str, Dict[str, object]]:
    """``tool evidence A : B [, A2 : B2 ...] :: C`` -- one relation stated by
    one or more examples, applied to ``C`` over the physics register."""
    text = arg.strip()
    if "::" not in text:
        return False, ("tool evidence takes 'A : B [, A2 : B2 ...] :: C' over "
                       "the physics register: one relation, stated by one or "
                       "more examples, applied to C"), {}
    left, c = (p.strip() for p in text.split("::", 1))
    c = c.rstrip("?").strip().rstrip(":").strip()
    vec, cls = physics_classes()
    examples = []
    for part in left.replace(";", ",").split(","):
        if not part.strip():
            continue
        if ":" not in part:
            return False, f"evidence: '{part.strip()}' is not 'A : B'", {}
        a, b = (p.strip() for p in part.split(":", 1))
        examples.append((a, b))
    missing = sorted({n for ab in examples for n in ab} | {c}) 
    missing = [n for n in missing if n not in vec]
    if not examples or missing:
        return False, (f"evidence: not in the physics register: "
                       f"{', '.join(missing) or '(no examples)'}"), {}
    res = relation_answer(examples, c, vec, cls)
    figures: Dict[str, object] = {"status": res["status"],
                                  "examples": len(examples),
                                  "dispersion": str(res["dispersion"])}
    if res["status"] == "conflicting":
        pts = "; ".join(f"{a} : {b} sends {c} to {_dim(t)}"
                        for (a, b), t in zip(examples, res["targets"]))
        return False, (f"evidence: refused -- the examples do not state one "
                       f"relation (dispersion {res['dispersion']}, not 0): "
                       f"{pts}"), figures
    if res["status"] == "absent":
        return False, (f"evidence: the {len(examples)} example(s) agree, "
                       f"but no register quantity has dimension "
                       f"{_dim(res['target'])}"), figures
    names = res["names"]
    figures["class_size"] = len(names)
    head = (f"evidence: {len(examples)} example(s) agree (dispersion 0); "
            f"{c} goes to dimension {_dim(res['target'])}")
    if len(names) == 1:
        figures["value"] = names[0]
        return True, f"{head}: {names[0]}, the only register quantity of it", \
            figures
    shown = ", ".join(names[:12]) + (" ..." if len(names) > 12 else "")
    return True, (f"{head}, held by {len(names)} register quantities ({shown}). "
                  f"The dimension layer cannot choose between them: every one "
                  f"is equidistant from the target, so the choice needs a cue "
                  f"from another layer"), figures
