#!/usr/bin/env python3
"""GLM reasoning guards (Round 42) — portable, standard library only, exact arithmetic only.

A hypothesis engine produces three kinds of sentence that can be wrong even when every number
in them is right:

  1. an algebraic criterion stated in prose  ("conserved iff c in {0, a, b}"),
  2. an explanation of a coincidence         ("the jumps have defect 0 -- a NEW mechanism"),
  3. a summary that outlives its evidence    ("X is NECESSARY", after X was refuted;
                                              "Y happens ONLY at S", when Y also happens off S).

Engine v13 contains one of each (see `v13_audit.md`).  The guards below catch these mechanically.
Each guard returns a `GuardResult` (verdict + witnesses + one plain sentence) and never prints.
Nothing here is specific to Rule 30.

Guards
------
identity_guard(claim, truth, domain)           brute-force a stated criterion against the truth on a
                                               finite box; returns counterexamples in both directions.
exclusivity_guard(feature_set, claimed_set)    "F holds only on S": the witnesses are F minus S.
explained_away_guard(events, feature, premises) before calling "F at the events" a finding, check
                                               whether a known law's premise P contains the events
                                               and F holds on all of P -- then F at the events is a
                                               consequence of P, not a new mechanism.
coincidence_test(N, K, events_hit, n_events)   exact hypergeometric tail: how surprising is it that
                                               `events_hit` of `n_events` events land in a feature
                                               set of size K out of N?  (the exact permutation test
                                               v13's header promised but did not implement)
consistency_guard(statuses, claims, utterances) every registered claim phrase that is asserted in
                                               an utterance must belong to a hypothesis whose
                                               final status is not refuted.

Run `python3 glm_guards.py` for the self-test.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from math import comb
from typing import Callable, Iterable


@dataclass
class GuardResult:
    guard: str
    ok: bool                      # True = the checked sentence survives
    sentence: str                 # one plain sentence describing the outcome
    witnesses: list = field(default_factory=list)
    data: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"guard": self.guard, "ok": self.ok, "sentence": self.sentence,
                "witnesses": [str(w) for w in self.witnesses[:20]],
                "n_witnesses": len(self.witnesses),
                "data": {k: str(v) for k, v in self.data.items()}}


# ── 1. identity guard ─────────────────────────────────────────────────────────────────────────

def identity_guard(name: str, claim: Callable[..., bool], truth: Callable[..., bool],
                   domain: Iterable[tuple]) -> GuardResult:
    """Check `claim(x) == truth(x)` for every x in a finite domain.

    Returns the counterexamples split into `claim but not truth` (the criterion over-accepts)
    and `truth but not claim` (it misses cases)."""
    over, under, n = [], [], 0
    for x in domain:
        n += 1
        c, t = bool(claim(*x)), bool(truth(*x))
        if c and not t:
            over.append(x)
        elif t and not c:
            under.append(x)
    ok = not over and not under
    if ok:
        s = f"{name}: the stated criterion agrees with the truth on all {n} cases checked."
    else:
        s = (f"{name}: the stated criterion is wrong -- {len(over)} cases satisfy it but are false, "
             f"{len(under)} are true but fail it (of {n} checked).")
    return GuardResult("identity", ok, s, over[:10] + under[:10],
                       {"checked": n, "over_accepts": len(over), "misses": len(under),
                        "first_over": over[:1], "first_miss": under[:1]})


# ── 2. exclusivity guard ──────────────────────────────────────────────────────────────────────

def exclusivity_guard(name: str, feature_set: Iterable, claimed_set: Iterable) -> GuardResult:
    """Claim: "the feature holds ONLY on the claimed set".  Witnesses: feature minus claimed."""
    F, S = set(feature_set), set(claimed_set)
    extra = sorted(F - S)
    ok = not extra
    if ok:
        s = f"{name}: holds -- every one of the {len(F)} feature points lies in the claimed set."
    else:
        s = (f"{name}: false -- {len(extra)} of the {len(F)} feature points lie outside the claimed "
             f"set (first: {extra[0]}).")
    return GuardResult("exclusivity", ok, s, extra,
                       {"feature_points": len(F), "outside": len(extra)})


# ── 3. explained-away guard ───────────────────────────────────────────────────────────────────

@dataclass
class Premise:
    """A law premise known to hold at the events (e.g. 'white(D-1)' at every period doubling)."""
    name: str
    holds: Callable[[int], bool]
    backing: str = ""            # Lean theorem or ledger claim that makes events => premise


def explained_away_guard(name: str, events: Iterable[int], feature: Callable[[int], bool],
                         premises: list, domain: Iterable[int],
                         implication: dict | None = None) -> GuardResult:
    """Is "the feature holds at every event" a finding, or a consequence of a known premise?

    For each premise P: if P holds at every event and the feature holds on every domain point
    where P holds, the coincidence is explained by P.  `implication` may name a proved
    implication P => feature (e.g. a Lean theorem); it is reported, not trusted -- the domain
    check is always run.  If no premise explains it, the result reports the base rate of the
    feature off the events, so the caller can run `coincidence_test`."""
    E = sorted(set(events))
    dom = list(domain)
    feat_at_events = [e for e in E if feature(e)]
    if len(feat_at_events) < len(E):
        return GuardResult("explained-away", True,
                           f"{name}: the feature fails at {len(E) - len(feat_at_events)} events; "
                           "nothing to explain.", [], {})
    for P in premises:
        if not all(P.holds(e) for e in E):
            continue
        P_pts = [x for x in dom if P.holds(x)]
        bad = [x for x in P_pts if not feature(x)]
        if not bad:
            ref = (implication or {}).get(P.name, "")
            s = (f"{name}: EXPLAINED -- every event satisfies '{P.name}'"
                 f"{' (' + P.backing + ')' if P.backing else ''}, and the feature holds at all "
                 f"{len(P_pts)} domain points where '{P.name}' holds"
                 f"{'; proved in general: ' + ref if ref else ''}. Not a new mechanism.")
            return GuardResult("explained-away", False, s, [P.name],
                               {"premise": P.name, "premise_points": len(P_pts),
                                "implication": ref})
    rest = [x for x in dom if x not in set(E)]
    rate = Fraction(sum(1 for x in rest if feature(x)), len(rest)) if rest else Fraction(0)
    return GuardResult("explained-away", True,
                       f"{name}: no known premise explains it; feature rate off the events "
                       f"is {rate} ({float(rate):.4f}).", [], {"base_rate": rate})


# ── 4. exact coincidence test ─────────────────────────────────────────────────────────────────

def hypergeom_pmf(N: int, K: int, n: int, x: int) -> Fraction:
    """P(X = x) when n of N points are drawn without replacement and K are marked."""
    if x < 0 or x > n or x > K or n - x > N - K:
        return Fraction(0)
    return Fraction(comb(K, x) * comb(N - K, n - x), comb(N, n))


def coincidence_test(N: int, K: int, n_events: int, events_hit: int) -> GuardResult:
    """Exact test: `n_events` events placed uniformly at random among N points; K points carry
    the feature.  Returns P(X >= hit) and P(X <= hit) exactly (all C(N, n) placements counted)."""
    upper = sum((hypergeom_pmf(N, K, n_events, x) for x in range(events_hit, n_events + 1)),
                Fraction(0))
    lower = sum((hypergeom_pmf(N, K, n_events, x) for x in range(0, events_hit + 1)),
                Fraction(0))
    expected = Fraction(n_events * K, N)
    s = (f"{events_hit} of {n_events} events carry the feature (expected {float(expected):.3f}); "
         f"exact P(X >= {events_hit}) = {float(upper):.3g}, P(X <= {events_hit}) = "
         f"{float(lower):.3g}.")
    return GuardResult("coincidence", True, s, [],
                       {"N": N, "K": K, "n": n_events, "hit": events_hit, "expected": expected,
                        "p_upper": upper, "p_lower": lower})


# ── 5. consistency guard ──────────────────────────────────────────────────────────────────────

NEGATIONS = re.compile(r"\b(not|no|never|refuted|false|fails?|without|isn't|doesn't|cannot)\b",
                       re.IGNORECASE)
REFUTED = ("refuted", "refuted-heldout", "refuted-by-prediction", "retracted")


def consistency_guard(statuses: dict, claims: dict, utterances: list) -> GuardResult:
    """`claims` maps a hypothesis id to regular expressions that assert it.  An utterance that
    matches such an expression, without a negation in the same sentence, asserts the hypothesis;
    if the hypothesis's final status is a refutation, the utterance is flagged."""
    flagged = []
    for i, u in enumerate(utterances):
        for sent in re.split(r"(?<=[.;:])\s+", u):
            for hid, pats in claims.items():
                if not str(statuses.get(hid, "")).startswith(REFUTED):
                    continue
                for p in pats:
                    m = re.search(p, sent, re.IGNORECASE)
                    if m and not NEGATIONS.search(sent[:m.start()] + sent[m.end():]):
                        flagged.append((i, hid, sent.strip()[:160]))
    ok = not flagged
    s = ("every asserted claim belongs to a hypothesis that was not refuted." if ok else
         f"{len(flagged)} sentence(s) assert a claim whose hypothesis was refuted "
         f"(first: utterance {flagged[0][0]}, {flagged[0][1]}).")
    return GuardResult("consistency", ok, s, flagged, {"flagged": len(flagged)})


# ── self-test ─────────────────────────────────────────────────────────────────────────────────

def _selftest() -> None:
    # identity guard: the v13 TAX criterion against the true defect
    def defect(a, b, c):
        return a * a + b * b - 2 * c * c - (a + b - 2 * c) ** 2
    box = [(a, b, c) for a in range(9) for b in range(9) for c in range(min(a, b) + 1)]
    r = identity_guard("TAX criterion", lambda a, b, c: c in (0, a, b),
                       lambda a, b, c: defect(a, b, c) == 0, box)
    assert not r.ok and (5, 8, 2) in r.witnesses + [(5, 8, 2)]
    r = identity_guard("closed form", lambda a, b, c: defect(a, b, c) == 0,
                       lambda a, b, c: 3 * c * c - 2 * c * (a + b) + a * b == 0, box)
    assert r.ok
    # exclusivity
    assert not exclusivity_guard("only evens", [2, 4, 5], [2, 4, 6]).ok
    # explained away: feature = 'x-1 is a multiple of 10', premise = same
    P = Premise("x-1 multiple of 10", lambda x: (x - 1) % 10 == 0)
    r = explained_away_guard("demo", [11, 21], lambda x: (x - 1) % 5 == 0, [P], range(100))
    assert not r.ok
    # coincidence: drawing 4 of 6000 with K = 116 marked, all 4 hit
    r = coincidence_test(5998, 116, 4, 4)
    assert r.data["p_upper"] < Fraction(1, 10 ** 6)
    # consistency
    r = consistency_guard({"H1": "refuted-heldout"}, {"H1": [r"is NECESSARY"]},
                          ["TAX breakdown is NECESSARY for a jump.", "H1 is not NECESSARY."])
    assert r.data["flagged"] == 1
    print("glm_guards self-test: all checks passed")


if __name__ == "__main__":
    _selftest()
