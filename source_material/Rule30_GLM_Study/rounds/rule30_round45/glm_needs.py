#!/usr/bin/env python3
"""GLM needs wheel — the portable core (Round 44).

The idea (owner, `glm_wheel.py`): the engine says, explicitly, what it thinks it NEEDS; we supply
those things on a WHEEL; the engine uses them; we MEASURE whether they helped.

This module is the part that does not depend on any domain.  It defines

  Need       — a machine-readable request: kind, signature, the tasks it blocks, why, and how we
               will know a provision met it (acceptance).
  Provision  — something we can put on the wheel: a callable that answers some tasks and stays
               silent on the others, with its provenance (FORMAL / CERT / EXACT / EMP) and cost.
  Wheel      — the registry; `select(needs)` returns only the provisions that serve stated needs.
  answer()   — the combination rule of `RequestProject/GLM/HypothesisEngine/NeedsWheel.lean`:
               the first provision that speaks wins, otherwise the engine's own base answer.
  score()    — right / wrong / overclaim / abstain against a ground truth that is fixed before
               any provision is run.
  run_conditions() — the measurement protocol: the same tasks under several wheels
               (none, guard only, requested, requested + guard, all, random-same-size), so the
               effect of the stated needs can be separated from the effect of "more tools".

What the Lean file guarantees (and what it does not):
  * if every provision is SOUND (never answers wrongly), adding it can only turn wrong answers into
    right ones and never the reverse (`answer_wrong_of_wrong`, `card_wrong_le`), its effect is
    confined to the tasks where it speaks (`answer_local`), and the order of sound provisions on
    the wheel does not matter (`answer_perm`);
  * an UNSOUND provision can hurt (`unsound_can_hurt`).  Domain provisions that are heuristic
    (new ARC primitives, new sequence models) are unsound in this sense, and the measurement below
    reports the wrongs they add rather than assuming there are none.

Standard library only.  Answers are three-valued: True, False, or None (= "I do not know").
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

T, F, U = True, False, None  # answers / truth values
OPEN = "open"  # a provision's definite answer "this question is open" (scored as None)


@dataclass
class Need:
    """A request the engine makes, generated from its own state (never hand-written per task)."""
    kind: str                 # range | tool | fact | test | primitive | transform | data
    signature: str            # machine key, e.g. "range:centre-bits", "primitive:gravity"
    because: str              # generated explanation (which evidence is missing)
    blocks: list = field(default_factory=list)   # task ids this need blocks
    acceptance: str = ""      # how we will know the provision met it

    def as_dict(self) -> dict:
        return {"kind": self.kind, "signature": self.signature, "because": self.because,
                "blocks": list(self.blocks), "acceptance": self.acceptance}


@dataclass
class Provision:
    """Something we can put on the wheel."""
    pid: str
    serves: list              # signatures (exact) or prefixes ending in '*'
    fn: Callable              # fn(task, context) -> True / False / None
    provenance: str           # FORMAL / CERT / EXACT / EMP / HEURISTIC
    sound: bool               # declared soundness (FORMAL/CERT/EXACT provisions are sound)
    description: str = ""
    cost: float = 0.0         # measured seconds (filled in by the runner)

    def serves_signature(self, sig: str) -> bool:
        for s in self.serves:
            if s.endswith("*") and sig.startswith(s[:-1]):
                return True
            if s == sig:
                return True
        return False


class Wheel:
    """The registry of provisions."""

    def __init__(self, provisions: Optional[list] = None):
        self.provisions: list = list(provisions or [])

    def add(self, p: Provision):
        self.provisions.append(p)

    def select(self, needs: list) -> list:
        """Only the provisions that serve at least one stated need, in wheel order."""
        sigs = {n.signature for n in needs}
        return [p for p in self.provisions if any(p.serves_signature(s) for s in sigs)]

    def unmet(self, needs: list) -> list:
        return [n for n in needs if not any(p.serves_signature(n.signature) for p in self.provisions)]

    def manifest(self) -> list:
        return [{"pid": p.pid, "serves": p.serves, "provenance": p.provenance, "sound": p.sound,
                 "description": p.description} for p in self.provisions]


def answer(provisions: list, base: Callable, task, ctx) -> tuple:
    """NeedsWheel.lean `answer`: first provision that speaks, else the base.  Returns
    (value, who) where who is the pid of the provision that decided, or 'base'."""
    for p in provisions:
        t0 = time.time()
        v = p.fn(task, ctx)
        p.cost += time.time() - t0
        if v is not None:
            return (None if v == OPEN else v), p.pid
    return base(task, ctx), "base"


def score(answers: dict, truth: dict) -> dict:
    """right: definite or 'unknown' answer equal to the truth;
    wrong: definite answer, opposite definite truth;
    overclaim: definite answer where the truth is unknown (an open question asserted);
    abstain: 'unknown' answer where the truth is definite."""
    out = {"right": 0, "wrong": 0, "overclaim": 0, "abstain": 0}
    for tid, a in answers.items():
        t = truth[tid]
        if a == t:
            out["right"] += 1
        elif a is None:
            out["abstain"] += 1
        elif t is None:
            out["overclaim"] += 1
        else:
            out["wrong"] += 1
    out["n"] = len(answers)
    return out


def run_conditions(tasks: list, truth: dict, base: Callable, guard: Callable, needs_of: Callable,
                   wheel: Wheel, ctx, seed: int = 44, random_draws: int = 5) -> dict:
    """The measurement protocol.

    tasks     : list of task ids
    truth     : {tid: True/False/None}, fixed before anything runs
    base      : base(tid, ctx) -> answer   (the engine without a wheel)
    guard     : guard(tid, ctx, answer, unmet_needs) -> answer  (honesty guard: may only weaken
                a definite answer to None, never invent one)
    needs_of  : needs_of(tid, ctx) -> [Need]  (the engine's own statement of what it needs)
    """
    needs = {t: needs_of(t, ctx) for t in tasks}
    all_needs = [n for t in tasks for n in needs[t]]
    requested = wheel.select(all_needs)

    def run(provs: list, use_guard: bool) -> tuple:
        ans, who = {}, {}
        for t in tasks:
            v, w = answer(provs, base, t, ctx)
            if use_guard and w == "base":
                # no provision spoke on this task, so every need it stated is still unmet
                v = guard(t, ctx, v, list(needs[t]))
            ans[t], who[t] = v, w
        return ans, who

    res = {}
    for name, provs, g in [("base (no wheel)", [], False),
                           ("guard only", [], True),
                           ("requested provisions", requested, False),
                           ("requested + guard", requested, True),
                           ("all provisions + guard", list(wheel.provisions), True)]:
        for p in wheel.provisions:
            p.cost = 0.0
        t0 = time.time()
        ans, who = run(provs, g)
        res[name] = {"score": score(ans, truth), "answers": ans, "decided_by": who,
                     "provisions": [p.pid for p in provs], "seconds": round(time.time() - t0, 3)}
    # control: random provisions of the same number, not chosen by need
    rng = random.Random(seed)
    k = len(requested)
    draws = []
    for _ in range(random_draws):
        provs = rng.sample(wheel.provisions, min(k, len(wheel.provisions)))
        ans, _ = run(provs, True)
        draws.append({"provisions": [p.pid for p in provs], "score": score(ans, truth)})
    res["random same-size + guard"] = {"draws": draws}
    return {"needs": {t: [n.as_dict() for n in needs[t]] for t in tasks},
            "requested": [p.pid for p in requested],
            "unmet_needs": sorted({n.signature for n in wheel.unmet(all_needs)}),
            "conditions": res}


def to_jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, (int, float, str, bool)) or obj is None:
        return obj
    return str(obj)


def dump(path, obj):
    with open(path, "w") as f:
        json.dump(to_jsonable(obj), f, indent=1, ensure_ascii=False)
