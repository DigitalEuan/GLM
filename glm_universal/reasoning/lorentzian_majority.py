"""``glm_universal.reasoning.lorentzian_majority`` -- the declared majority
rule for conflicting evidence (Phase 184).

*Created 23 October 2026.*

Where this comes from
---------------------
Phase 183 (``studies/LORENTZIAN_EVIDENCE_STUDY.md``,
``reasoning/lorentzian_evidence.py``) combined examples of a relation as cues
in the Lorentzian evidence space and refused every set whose targets disagree
(the dispersion guard, ``evid_null_iff``). On two good examples and one decoy
the majority target answered 155 of 300 right and 0 wrong where the guard
refused all 300; ``STATUS.md`` §2.1 item 11 asked for that rule declared,
with its own soundness condition. ``studies/LORENTZIAN_MAJORITY_STUDY.md``
measures it; ``RequestProject/GLM/LorentzianMajority.lean`` is the
specification (D8).

The rule
--------
Split the cues into **agreeing groups** -- the cues stating one target. Each
group has dispersion 0 (``group_disp_zero``): in the evidence space it is a
null vector, one lifted point scaled by its weight (``group_evid_null``).
Answer the target whose group holds a **strict majority** of the weight,
``W < 2 W_v``; refuse when none does. At most one target can
(``majority_unique``), and the rule answers ``v`` exactly then
(``majorityRule_eq_some_iff``).

What it promises, and to whom
-----------------------------
* **The soundness condition** (``majority_never_wrong``): if the examples
  stating the true relation hold at least half the weight, the rule never
  answers anything else; strictly more than half and it answers right
  (``majority_sound``). With unit weights: fewer than half the examples
  decoys, the answer is right (``majority_sound_count``).
* **Tight** (``majority_misled``): below half, decoys that agree with one
  another carry the answer. The condition is the caller's obligation -- no
  rule that reads only the targets can check it.
* **What a wrong answer costs** (``majority_wrong_needs_decoys``): an answer
  whose group holds ``g`` of ``k`` examples is wrong only if at least ``g``
  of them are decoys. The tool says so with every answer.
* **It extends the guard** (``majority_extends_guard``): where the
  dispersion guard answers (all targets agree), the rule answers the same.

Exactness
---------
``Fraction`` and ``int`` only (D7).
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, Hashable, List, Mapping, Optional, Sequence, Tuple

from . import lorentzian_evidence as le

__all__ = [
    "LEAN_FILE", "LEAN_THEOREMS", "groups", "majority", "relation_majority",
    "majority_text",
]

F = Fraction

#: The Lean file this module rests on, and the theorems it quotes.
LEAN_FILE = "RequestProject/GLM/LorentzianMajority.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "majority_unique", "majorityRule_eq_some_iff", "majorityRule_eq_none_iff",
    "majority_never_wrong", "majority_sound", "majority_misled",
    "majority_wrong_needs_decoys", "majority_sound_count",
    "majority_never_wrong_count", "group_disp_zero", "group_evid_null",
    "majority_extends_guard")


# ===========================================================================
# 1.  THE RULE, OVER ANY TARGETS
# ===========================================================================

def groups(targets: Sequence[Hashable],
           weights: Optional[Sequence] = None) -> Dict[Hashable, Fraction]:
    """``target -> W_v``, the weight of each agreeing group (first-seen
    order). Weights default to 1 and must be non-negative."""
    ws = [F(1)] * len(targets) if weights is None else [F(w) for w in weights]
    if len(ws) != len(targets):
        raise ValueError("groups: one weight per target")
    if any(w < 0 for w in ws):
        raise ValueError("groups: the weights must be non-negative "
                         "(majority_unique needs it)")
    out: Dict[Hashable, Fraction] = {}
    for t, w in zip(targets, ws):
        out[t] = out.get(t, F(0)) + w
    return out


def majority(targets: Sequence[Hashable],
             weights: Optional[Sequence] = None) -> Dict[str, object]:
    """The declared rule: the target whose group holds a strict majority of
    the weight, ``W < 2 W_v`` (``majorityRule``), or ``no_majority``.

    ``decoys_needed`` is the weight of the answer's own group: by
    ``majority_wrong_needs_decoys`` the answer is wrong only if decoys weigh
    at least that much."""
    g = groups(targets, weights)
    W = sum(g.values(), F(0))
    winners = [v for v, wv in g.items() if W < 2 * wv]
    if len(winners) > 1:                       # majority_unique forbids it
        raise AssertionError("two strict majorities")
    out: Dict[str, object] = {"weight": W, "groups": g,
                              "largest": max(g.values()) if g else F(0)}
    if winners:
        v = winners[0]
        out.update(status="majority", value=v, share=g[v] / W,
                   decoys_needed=g[v])
    else:
        out.update(status="no_majority", value=None, share=None,
                   decoys_needed=None)
    return out


# ===========================================================================
# 2.  RELATIONS OVER THE PHYSICS REGISTER
# ===========================================================================

def relation_majority(examples: Sequence[Tuple[str, str]], c: str,
                      vec: Optional[Mapping[str, Tuple[Fraction, ...]]] = None,
                      cls: Optional[Mapping[Tuple[Fraction, ...], List[str]]]
                      = None) -> Dict[str, object]:
    """``a_1 : b_1 , ... :: c : ?`` under the majority rule.

    * ``no_majority`` -- no target is stated by more than half the examples;
    * ``absent`` -- a strict majority agrees and no register quantity has
      its dimension;
    * ``class`` -- a strict majority agrees on a dimension class; the class's
      names are the certificate (``evid_tie``: one name is never chosen).

    ``outvoted`` lists the examples outside the majority group.
    """
    if vec is None or cls is None:
        vec, cls = le.physics_classes()
    targets = [x for x, _ in le.target_cues(
        [(vec[a], vec[b]) for a, b in examples], vec[c])]
    m = majority(targets)
    out: Dict[str, object] = {
        "examples": list(examples), "query": c, "targets": targets,
        "dispersion": le.dispersion([(t, F(1)) for t in targets]),
        "groups": len(m["groups"]), "largest": m["largest"]}
    if m["status"] == "no_majority":
        out.update(status="no_majority", names=[], outvoted=[])
        return out
    v = m["value"]
    names = list(cls.get(v, []))
    out.update(target=v, names=names, support=m["groups"][v],
               decoys_needed=m["decoys_needed"],
               outvoted=[ex for ex, t in zip(examples, targets) if t != v],
               status="class" if names else "absent")
    return out


# ===========================================================================
# 3.  THE TOOL
# ===========================================================================

def majority_text(arg: str) -> Tuple[bool, str, Dict[str, object]]:
    """``tool majority A : B [, A2 : B2 ...] :: C`` -- examples of a relation
    that may conflict, applied to ``C`` over the physics register: the
    strict-majority target answers, the rest are named as outvoted."""
    text = arg.strip()
    if "::" not in text:
        return False, ("tool majority takes 'A : B [, A2 : B2 ...] :: C' over "
                       "the physics register: examples of one relation, some "
                       "of which may be wrong, applied to C"), {}
    left, c = (p.strip() for p in text.split("::", 1))
    c = c.rstrip("?").strip().rstrip(":").strip()
    vec, cls = le.physics_classes()
    examples = []
    for part in left.replace(";", ",").split(","):
        if not part.strip():
            continue
        if ":" not in part:
            return False, f"majority: '{part.strip()}' is not 'A : B'", {}
        a, b = (p.strip() for p in part.split(":", 1))
        examples.append((a, b))
    missing = sorted({n for ab in examples for n in ab} | {c})
    missing = [n for n in missing if n not in vec]
    if not examples or missing:
        return False, (f"majority: not in the physics register: "
                       f"{', '.join(missing) or '(no examples)'}"), {}
    res = relation_majority(examples, c, vec, cls)
    k = len(examples)
    figures: Dict[str, object] = {"status": res["status"], "examples": k,
                                  "groups": res["groups"],
                                  "largest": int(res["largest"])}
    if res["status"] == "no_majority":
        pts = "; ".join(f"{a} : {b} sends {c} to {le._dim(t)}"
                        for (a, b), t in zip(examples, res["targets"]))
        return False, (f"majority: refused -- no target is stated by more "
                       f"than half of the {k} examples (largest group "
                       f"{res['largest']} of {k}): {pts}"), figures
    g = int(res["support"])
    figures.update(support=g, decoys_needed=g, outvoted=len(res["outvoted"]))
    dim = le._dim(res["target"])
    out_txt = ""
    if res["outvoted"]:
        out_txt = (" Outvoted: " + "; ".join(f"{a} : {b}"
                                              for a, b in res["outvoted"])
                   + ".")
    guarantee = (f" The answer is right unless at least {g} of the {k} "
                 f"examples are wrong (majority_wrong_needs_decoys).")
    if res["status"] == "absent":
        return False, (f"majority: {g} of {k} examples agree, but no register "
                       f"quantity has dimension {dim}.{out_txt}"), figures
    names = res["names"]
    figures["class_size"] = len(names)
    head = f"majority: {g} of {k} examples agree; {c} goes to dimension {dim}"
    if len(names) == 1:
        figures["value"] = names[0]
        return True, (f"{head}: {names[0]}, the only register quantity of "
                      f"it.{out_txt}{guarantee}"), figures
    shown = ", ".join(names[:12]) + (" ..." if len(names) > 12 else "")
    return True, (f"{head}, held by {len(names)} register quantities "
                  f"({shown}); the dimension layer cannot choose between "
                  f"them.{out_txt}{guarantee}"), figures
