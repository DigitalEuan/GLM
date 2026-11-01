#!/usr/bin/env python3
"""Layered verdicts for the GLM Hypothesis Engine (Round 45, engine v17).

Portable, standard library only.  This module replaces the layer bookkeeping of v15/v16.

A *layer profile* is the outcome of one guard read at five increasing scales.  The five GLM
layer names (substrate, integer, rational, griess, universal) are kept as names, but each layer
is described by its actual scale parameter (a box size, a domain cut-off, a sample size, a
neighbourhood radius, a range of n, a set of seeds).  No residue modulo 144 or 256 is computed
anywhere, and none is claimed.

How a profile is turned into one verdict depends on what kind of claim the guard reads.

* ``universal``  - "P holds for every case in the layer's domain", domains nested and growing.
  Passing layers form a prefix (Lean: ``GateLoop.holdsAt_anti``).  The claim holds iff it holds at
  the largest layer (``GateLoop.holdsAll_iff_top``).  The first failing layer is the escalation
  index: the least scale at which the claim is refuted.
* ``largest``    - a statistic or an explanation.  The verdict is the verdict at the largest layer
  with data; smaller layers are reported as a trend.  (v16 used "explained at ANY layer", which is
  vacuously satisfied by a layer with no events; Lean: ``GateLoop.anyScale_vacuous``.)
* ``stated``     - an exclusivity claim "feature only at S".  The verdict is the verdict at the
  stated set (layer 1); the looser layers say how far the claim is from true (the passing layers
  form a suffix, Lean: ``GateLoop.exclusive_mono``).

Every profile also carries an *arrow*: the highest layer that was read, and whether the verdict
was stable between the last two layers read ("converging") or flipped ("flipped at <layer>").  This
is the read position/direction of the observer that the owner proposed: the read layer never goes
down (Lean: ``GateLoop.reads_sorted``), and a refutation, once read, is never undone by reading
higher (``GateLoop.refuted_stable``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

LAYER_NAMES = ["substrate", "integer", "rational", "griess", "universal"]


@dataclass
class LayerProfile:
    guard: str
    name: str
    kind: str                       # "universal" | "largest" | "stated"
    scales: list                    # human-readable scale per layer
    verdicts: list                  # True / False / None (no data) per layer
    witness: Any = None             # first counterexample, when there is one
    notes: list = field(default_factory=list)

    # ---- per-layer views -------------------------------------------------------------------
    def read_layers(self) -> list:
        return [i for i, v in enumerate(self.verdicts) if v is not None]

    def passing(self) -> list:
        return [LAYER_NAMES[i] for i, v in enumerate(self.verdicts) if v is True]

    def failing(self) -> list:
        return [LAYER_NAMES[i] for i, v in enumerate(self.verdicts) if v is False]

    def first_fail(self) -> Optional[int]:
        for i, v in enumerate(self.verdicts):
            if v is False:
                return i
        return None

    def first_pass(self) -> Optional[int]:
        for i, v in enumerate(self.verdicts):
            if v is True:
                return i
        return None

    def shape_ok(self) -> bool:
        """Nested domains force a shape: universal -> passes are a prefix; stated -> a suffix."""
        seq = [v for v in self.verdicts if v is not None]
        if self.kind == "universal":
            return all(not (a is False and b is True) for a, b in zip(seq, seq[1:]))
        if self.kind == "stated":
            return all(not (a is True and b is False) for a, b in zip(seq, seq[1:]))
        return True

    # ---- the single verdict ----------------------------------------------------------------
    def verdict(self) -> Optional[bool]:
        seq = [v for v in self.verdicts if v is not None]
        if not seq:
            return None
        if self.kind == "universal":
            return all(seq)
        if self.kind == "stated":
            return self.verdicts[0] if self.verdicts[0] is not None else seq[0]
        return seq[-1]              # largest

    # ---- the arrow (read position and direction) -------------------------------------------
    def arrow(self) -> dict:
        rl = self.read_layers()
        if not rl:
            return {"read_layer": None, "direction": "no data"}
        top = rl[-1]
        if len(rl) == 1:
            direction = "single read"
        else:
            a, b = self.verdicts[rl[-2]], self.verdicts[rl[-1]]
            direction = "converging" if a == b else f"flipped at {LAYER_NAMES[top]}"
        return {"read_layer": LAYER_NAMES[top], "read_index": top, "direction": direction}

    def summary(self) -> str:
        v = self.verdict()
        sc = ", ".join(f"{LAYER_NAMES[i]}={self.scales[i]}:{'-' if x is None else ('T' if x else 'F')}"
                       for i, x in enumerate(self.verdicts))
        s = f"{self.guard} [{self.kind}] {self.name}: verdict={v}; layers {sc}"
        if self.kind == "universal" and self.first_fail() is not None:
            s += f"; first failure at {LAYER_NAMES[self.first_fail()]} (scale {self.scales[self.first_fail()]})"
        if self.kind == "stated" and v is False and self.first_pass() is not None:
            s += f"; holds only from {LAYER_NAMES[self.first_pass()]} (scale {self.scales[self.first_pass()]})"
        if not self.shape_ok():
            s += "; WARNING: layer domains are not nested (shape violated)"
        return s

    def as_dict(self) -> dict:
        return {"guard": self.guard, "name": self.name, "kind": self.kind,
                "scales": [str(s) for s in self.scales],
                "verdicts": self.verdicts, "verdict": self.verdict(),
                "passing": self.passing(), "failing": self.failing(),
                "first_fail": None if self.first_fail() is None else LAYER_NAMES[self.first_fail()],
                "shape_ok": self.shape_ok(), "arrow": self.arrow(),
                "witness": None if self.witness is None else str(self.witness),
                "notes": self.notes, "summary": self.summary()}


def five_scales(lo_values: list, full) -> list:
    """Pad/trim a list of scale parameters to exactly five, the last one being `full`."""
    xs = [x for x in lo_values if x is None or full is None or x < full][:4]
    while len(xs) < 4:
        xs.insert(0, xs[0] if xs else full)
    return xs + [full]


# ─────────────────────────────────────────────────────────────────────────────────────────────
# The four layered guards
# ─────────────────────────────────────────────────────────────────────────────────────────────

def identity_layered(name: str, claim: Callable, truth: Callable, domain: list) -> LayerProfile:
    """Does `claim(x) == truth(x)` on every case whose coordinates are all < cap?

    v15/v16 reduced every coordinate mod 2/4/8/144/256 and deduplicated; on a box domain that is
    exactly "all coordinates < m", i.e. a box size.  v17 says so: the caps are box sizes.
    """
    M = max((max(c) for c in domain), default=0) + 1
    caps = sorted(set([2, 4, 8, max(2, (M + 1) // 2), M]))
    caps = five_scales(caps[:-1], caps[-1])
    verdicts, witness = [], None
    for cap in caps:
        sub = [c for c in domain if max(c) < cap]
        if not sub:
            verdicts.append(None)
            continue
        bad = [c for c in sub if bool(claim(*c)) != bool(truth(*c))]
        verdicts.append(not bad)
        if bad and witness is None:
            witness = bad[0]
    return LayerProfile("identity", name, "universal", [f"box<{c}" for c in caps], verdicts, witness)


def explained_away_layered(name: str, events: list, feature: Callable, premises: list,
                           domain: list, implication: Optional[dict] = None) -> LayerProfile:
    """The explained-away guard of Round 42 (``glm_guards.explained_away_guard``) read at five
    domain cut-offs.

    verdict True = EXPLAINED (the feature at the events is forced by a known premise) at the
    largest scale.  A layer with no events has no data (None), not a vacuous "explained".
    """
    from glm_guards import explained_away_guard
    top = max(domain) + 1 if domain else 0
    cuts = five_scales([10, 50, 200, 2000], top)
    verdicts, notes = [], []
    for cut in cuts:
        ev = [e for e in events if e < cut]
        dom = [x for x in domain if x < cut]
        if not ev or not dom:
            verdicts.append(None)
            notes.append(f"D<{cut}: no events")
            continue
        r = explained_away_guard(f"{name} @ D<{cut}", ev, feature, premises, dom,
                                 implication=implication)
        verdicts.append(not r.ok)
        notes.append(r.sentence)
    return LayerProfile("explained-away", name, "largest", [f"D<{c}" for c in cuts], verdicts,
                        notes=notes)


def _hyper_tail(N: int, K: int, n: int, k: int):
    """Exact P[X >= k] for X hypergeometric (population N, K successes, n draws)."""
    from fractions import Fraction
    from math import comb
    tot = comb(N, n)
    if tot == 0:
        return Fraction(1)
    return Fraction(sum(comb(K, j) * comb(N - K, n - j) for j in range(k, min(K, n) + 1)), tot)


def coincidence_layered(domain: list, feature: set, events: list,
                        alpha=None) -> LayerProfile:
    """Exact hypergeometric tail at five prefix sizes of the domain, recounting everything.

    v16 kept the event count and the hit count fixed while shrinking N and scaling K, which mixes
    two samples.  Here each layer is the prefix of the domain of that size, and K, the events in
    range and the hits in range are all recounted.  verdict True = significant at level alpha at the
    largest layer.
    """
    from fractions import Fraction
    alpha = Fraction(1, 20) if alpha is None else alpha
    dom = sorted(domain)
    sizes = five_scales([10, 50, 200, 2000], len(dom))
    verdicts, notes = [], []
    for s in sizes:
        part = dom[:s]
        if not part:
            verdicts.append(None)
            continue
        cut = part[-1]
        K = sum(1 for d in part if d in feature)
        ev = [e for e in events if e <= cut and e in set(part)]
        hit = sum(1 for e in ev if e in feature)
        if not ev:
            verdicts.append(None)
            notes.append(f"N={s}: no events in range")
            continue
        p = _hyper_tail(len(part), K, len(ev), hit)
        verdicts.append(p < alpha)
        notes.append(f"N={s}: K={K}, events={len(ev)}, hits={hit}, p={p} (~{float(p):.3g})")
    return LayerProfile("coincidence", "hits concentrated on the feature", "largest",
                        [f"N={s}" for s in sizes], verdicts, notes=notes)


def exclusivity_layered(name: str, feature_set: list, claimed: set,
                        radii=(0, 1, 5, 20, 100)) -> LayerProfile:
    """'feature holds only at S': is every feature point within distance r of S?

    Layer 1 (r = 0) is the claim as stated.  Larger r loosens it; the least r that makes it true
    measures how far the claim is from true.
    """
    verdicts, witness = [], None
    S = sorted(claimed)
    for r in radii:
        if r == 0:
            bad = [x for x in feature_set if x not in claimed]
        else:
            import bisect
            bad = []
            for x in feature_set:
                i = bisect.bisect_left(S, x)
                near = ((i < len(S) and S[i] - x <= r) or (i > 0 and x - S[i - 1] <= r))
                if not near:
                    bad.append(x)
        verdicts.append(not bad)
        if bad and witness is None:
            witness = bad[0]
    return LayerProfile("exclusivity", name, "stated", [f"±{r}" for r in radii], verdicts, witness)


def escalation_profile(name: str, scales: list, check: Callable) -> LayerProfile:
    """Escalate-before-assert: read a universal claim at growing scales, stop at the first failure.

    `check(scale) -> (ok, witness)`.  Layers above the first failure are not read (None): the
    refutation is final (Lean: ``GateLoop.refuted_stable``).
    """
    scales = five_scales(list(scales[:-1]), scales[-1]) if len(scales) != 5 else list(scales)
    verdicts, witness = [], None
    for s in scales:
        if witness is not None:
            verdicts.append(None)
            continue
        ok, w = check(s)
        verdicts.append(bool(ok))
        if not ok:
            witness = w
    return LayerProfile("escalation", name, "universal", scales, verdicts, witness)
