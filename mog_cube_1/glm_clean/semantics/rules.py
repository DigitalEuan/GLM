"""
rules.py — MOG cells as graded semantic rules (encoding v6).

In v5 a cell was a semantic class, and a verb slot carried a required mask and
a forbidden mask over the cells.  That works (see results/exp2) but it throws
away *how strongly* a verb expects a class: a class is either required or not.

v6 keeps the 24 binary cells but makes each cell a rule with a strictness:

    cell = (class c, direction, tau)

    direction "forbid":  the cell fires when the argument belongs to class c
                         and the verb takes class c in at most a fraction tau
                         of its attested arguments
    direction "require": the cell fires when the argument does NOT belong to
                         class c although the verb takes class c in at least a
                         fraction tau of its attested arguments

Several cells may watch the same class at different strictness levels, which
gives a thermometer code: a mildly unusual argument lights one cell, a wildly
wrong one lights three.  The MOG object stays a 24-bit binary object and every
cell still has a plain reading ("the object of this verb is almost never a
person, and this one is").

Which 24 rules to use is decided by greedy search on a development split.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from ..substrate import popcount
from .features import ClassInventory, Lexicon

FORBID_TAUS = (0.0005, 0.002, 0.01, 0.03, 0.08, 0.15, 0.30)
REQUIRE_TAUS = (0.35, 0.55, 0.75)


@dataclass(frozen=True)
class CellSpec:
    cls: int
    direction: str      # "forbid" | "require"
    tau: float

    def label(self, inv: ClassInventory) -> str:
        name = inv.classes[self.cls]
        name = name[4:] if name.startswith("LEX:") else name
        arrow = "never" if self.direction == "forbid" else "always"
        return f"{arrow}({name}, {self.tau})"


# ══════════════════════════════════════════════════════════════════════════════
# Per-verb class probabilities
# ══════════════════════════════════════════════════════════════════════════════

class VerbStats:
    """p(class | verb, slot), smoothed towards the verb's WordNet lexname and
    then towards the global slot distribution."""

    def __init__(self, inv: ClassInventory, lex: Lexicon, rows,
                 k1: float = 1.0, k2: float = 20.0):
        self.inv = inv
        self.lex = lex
        self.k1 = k1
        m = len(inv)
        n_v: Dict[str, Dict[int, float]] = defaultdict(lambda: defaultdict(float))
        N_v: Dict[str, float] = defaultdict(float)
        n_L: Dict[str, Dict[int, float]] = defaultdict(lambda: defaultdict(float))
        N_L: Dict[str, float] = defaultdict(float)
        n_0: Dict[int, float] = defaultdict(float)
        N_0 = 0.0
        for v, noun, c in rows:
            cls = inv.of(noun)
            if not cls:
                continue
            r = lex.verbs.get(v)
            L = r["lexname"] if r else None
            N_v[v] += c
            N_0 += c
            nv = n_v[v]
            if L is not None:
                N_L[L] += c
                nl = n_L[L]
            else:
                nl = None
            for cl in cls:
                nv[cl] += c
                n_0[cl] += c
                if nl is not None:
                    nl[cl] += c
        self.N_v = dict(N_v)
        self.n_v = {v: dict(d) for v, d in n_v.items()}
        self.p0 = [(n_0.get(i, 0.0) / N_0 if N_0 else 0.0) for i in range(m)]
        self.p_L: Dict[str, List[float]] = {}
        for L, nl in n_L.items():
            NL = N_L[L]
            self.p_L[L] = [(nl.get(i, 0.0) + k2 * self.p0[i]) / (NL + k2)
                           for i in range(m)]

    def base(self, verb: str) -> List[float]:
        r = self.lex.verbs.get(verb)
        if r is not None:
            b = self.p_L.get(r["lexname"])
            if b is not None:
                return b
        return self.p0

    def p(self, verb: str, cls: int) -> float:
        base = self.base(verb)
        N = self.N_v.get(verb, 0.0)
        n = self.n_v.get(verb, {}).get(cls, 0.0)
        return (n + self.k1 * base[cls]) / (N + self.k1)

    def evidence(self, verb: str) -> float:
        return self.N_v.get(verb, 0.0)


def fires(stats: VerbStats, spec: CellSpec, verb: str, noun_classes: frozenset) -> bool:
    has = spec.cls in noun_classes
    p = stats.p(verb, spec.cls)
    if spec.direction == "forbid":
        return has and p <= spec.tau
    return (not has) and p >= spec.tau


# ══════════════════════════════════════════════════════════════════════════════
# The encoder
# ══════════════════════════════════════════════════════════════════════════════

class RuleEncoder:
    """24 rules; the violation object records which of them fired."""

    def __init__(self, inv: ClassInventory, cells: Sequence[CellSpec],
                 subj: VerbStats, obj: VerbStats, min_evidence: float = 1.0):
        self.inv = inv
        self.cells = list(cells)
        self.m = len(self.cells)
        self.stats = {"subj": subj, "obj": obj}
        self.min_evidence = min_evidence
        self.layout = None
        self._cache: Dict[Tuple[str, str, str], int] = {}

    def violation_for(self, verb: str, slot: str, noun: str) -> int:
        key = (verb, slot, noun)
        v = self._cache.get(key)
        if v is not None:
            return v
        st = self.stats[slot]
        cls = self.inv.of(noun)
        out = 0
        if st.evidence(verb) >= self.min_evidence or True:
            for i, spec in enumerate(self.cells):
                if fires(st, spec, verb, cls):
                    out |= 1 << i
        self._cache[key] = out
        return out

    # Composer-compatible interface -------------------------------------
    def violation(self, verb: str, slot: str, provision: int,
                  verb_lexname: Optional[str]) -> int:      # pragma: no cover
        raise NotImplementedError("RuleEncoder works on nouns, not provisions")

    def labels(self) -> List[str]:
        return [c.label(self.inv) for c in self.cells]

    def to_json(self) -> str:
        return json.dumps({
            "cells": [{"class": self.inv.classes[c.cls],
                       "direction": c.direction, "tau": c.tau}
                      for c in self.cells]}, indent=2)


# ══════════════════════════════════════════════════════════════════════════════
# The search
# ══════════════════════════════════════════════════════════════════════════════

class RuleSearch:
    """Greedy forward selection of cells, on precomputed firing lists."""

    def __init__(self, inv: ClassInventory, lex: Lexicon,
                 tasks: Sequence[Tuple[str, object]], stats: Dict[str, VerbStats],
                 forbid_taus=FORBID_TAUS, require_taus=REQUIRE_TAUS,
                 verbose: bool = True):
        self.inv = inv
        self.verbose = verbose
        self.items: List[Tuple[str, str, str, str]] = []   # slot, verb, good, bad
        for slot, task in tasks:
            for v, g, b in task.items:
                self.items.append((slot, v, g, b))
        self.n = len(self.items)
        self.candidates: List[CellSpec] = []
        for c in range(len(inv)):
            for t in forbid_taus:
                self.candidates.append(CellSpec(c, "forbid", t))
            for t in require_taus:
                self.candidates.append(CellSpec(c, "require", t))
        if verbose:
            print(f"  {self.n} dev items, {len(self.candidates)} candidate cells",
                  flush=True)
        self.fire_good: List[List[int]] = []
        self.fire_bad: List[List[int]] = []
        self._precompute(stats)

    def _precompute(self, stats: Dict[str, VerbStats]) -> None:
        inv = self.inv
        # cache p(verb, class) per (slot, verb) as needed
        pcache: Dict[Tuple[str, str], Dict[int, float]] = {}
        cls_cache: Dict[str, frozenset] = {}
        for spec in self.candidates:
            self.fire_good.append([])
            self.fire_bad.append([])
        by_class: Dict[int, List[int]] = defaultdict(list)
        for idx, spec in enumerate(self.candidates):
            by_class[spec.cls].append(idx)
        for i, (slot, verb, good, bad) in enumerate(self.items):
            st = stats[slot]
            key = (slot, verb)
            pv = pcache.get(key)
            if pv is None:
                base = st.base(verb)
                N = st.N_v.get(verb, 0.0)
                nv = st.n_v.get(verb, {})
                k1 = st.k1
                pv = {c: (nv.get(c, 0.0) + k1 * base[c]) / (N + k1)
                      for c in range(len(inv))}
                pcache[key] = pv
            cg = cls_cache.setdefault(good, inv.of(good))
            cb = cls_cache.setdefault(bad, inv.of(bad))
            for c in range(len(inv)):
                p = pv[c]
                hg = c in cg
                hb = c in cb
                if not (hg or hb) and p < REQUIRE_TAUS[0]:
                    continue
                for idx in by_class[c]:
                    spec = self.candidates[idx]
                    if spec.direction == "forbid":
                        if p <= spec.tau:
                            if hg:
                                self.fire_good[idx].append(i)
                            if hb:
                                self.fire_bad[idx].append(i)
                    else:
                        if p >= spec.tau:
                            if not hg:
                                self.fire_good[idx].append(i)
                            if not hb:
                                self.fire_bad[idx].append(i)
        if self.verbose:
            tot = sum(len(x) for x in self.fire_good) + sum(len(x) for x in self.fire_bad)
            print(f"  precomputed {tot} firings", flush=True)

    @staticmethod
    def _pt(g: int, b: int) -> float:
        return 1.0 if g < b else (0.5 if g == b else 0.0)

    def run(self, k: int = 24, sweeps: int = 2) -> Tuple[List[CellSpec], float, List[float]]:
        g = [0] * self.n
        b = [0] * self.n
        score = 0.5 * self.n            # all ties at the start
        chosen: List[int] = []
        history: List[float] = []

        def delta(idx: int, sign: int) -> float:
            d = 0.0
            touched = set(self.fire_good[idx]) | set(self.fire_bad[idx])
            fg = set(self.fire_good[idx])
            fb = set(self.fire_bad[idx])
            for i in touched:
                old = self._pt(g[i], b[i])
                ng = g[i] + (sign if i in fg else 0)
                nb = b[i] + (sign if i in fb else 0)
                d += self._pt(ng, nb) - old
            return d

        def apply(idx: int, sign: int) -> None:
            for i in self.fire_good[idx]:
                g[i] += sign
            for i in self.fire_bad[idx]:
                b[i] += sign

        for step in range(k):
            best_idx, best_d = None, 1e-12
            for idx in range(len(self.candidates)):
                if idx in chosen:
                    continue
                d = delta(idx, +1)
                if d > best_d:
                    best_idx, best_d = idx, d
            if best_idx is None:
                if self.verbose:
                    print("  no candidate improves; stopping early")
                break
            apply(best_idx, +1)
            score += best_d
            chosen.append(best_idx)
            history.append(score / self.n)
            if self.verbose:
                print(f"    +{self.candidates[best_idx].label(self.inv):42s}"
                      f" -> {score/self.n:.4f}", flush=True)

        for sweep in range(sweeps):
            improved = False
            for pos in range(len(chosen)):
                cur = chosen[pos]
                apply(cur, -1)
                base_score = score - delta(cur, +1)   # score without `cur`
                # recompute properly: removing then measuring
                best_idx, best_d = cur, delta(cur, +1)
                for idx in range(len(self.candidates)):
                    if idx in chosen and idx != cur:
                        continue
                    d = delta(idx, +1)
                    if d > best_d + 1e-12:
                        best_idx, best_d = idx, d
                apply(best_idx, +1)
                score = base_score + best_d
                if best_idx != cur:
                    chosen[pos] = best_idx
                    improved = True
            history.append(score / self.n)
            if self.verbose:
                print(f"  swap sweep {sweep+1}: {score/self.n:.4f}", flush=True)
            if not improved:
                break
        return [self.candidates[i] for i in chosen], score / self.n, history


# ══════════════════════════════════════════════════════════════════════════════
# v7: the 24 cells are chosen per verb, not once for the whole language
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class VerbCell:
    cls: int
    direction: str          # "forbid" | "require"

    def label(self, inv: ClassInventory) -> str:
        name = inv.classes[self.cls]
        name = name[4:] if name.startswith("LEX:") else name
        return ("never(" if self.direction == "forbid" else "always(") + name + ")"


class PerVerbRuleEncoder:
    """A 24-cell MOG object whose cells are the 24 sharpest expectations of the
    particular verb and slot.

    v6 asked: which 24 rules describe English best on average?  The answer was
    a poor bargain, because a rule that matters for `eat` is dead weight for
    `sign`.  v7 spends the same 24 cells per verb: for each (verb, slot) we
    rank every semantic class by how much the verb's own distribution departs
    from the corpus-wide one,

        forbid  c :  p0(c) * log(p0(c) / p_v(c))     c is common in the slot
                                                     but this verb avoids it
        require c :  p_v(c) * log(p_v(c) / p0(c))    this verb insists on c

    and keep the top 24.  The object is still 24 binary cells, still readable
    ("cell 3: the object of `eat` is almost never a person, and `senator` is"),
    and still exactly diagnosable at weight <= 3.  What changes is that the
    budget is now spent where the verb actually has an opinion.
    """

    def __init__(self, inv: ClassInventory, subj: VerbStats, obj: VerbStats,
                 m: int = 24, floor: float = 1e-6):
        self.inv = inv
        self.m = m
        self.floor = floor
        self.stats = {"subj": subj, "obj": obj}
        self.layout = None
        self._cells: Dict[Tuple[str, str], List[VerbCell]] = {}
        self._cache: Dict[Tuple[str, str, str], int] = {}

    def cells_for(self, verb: str, slot: str) -> List[VerbCell]:
        key = (verb, slot)
        cs = self._cells.get(key)
        if cs is not None:
            return cs
        st = self.stats[slot]
        scored: List[Tuple[float, VerbCell]] = []
        for c in range(len(self.inv)):
            p0 = max(st.p0[c], self.floor)
            pv = max(st.p(verb, c), self.floor)
            if pv < p0:
                s = p0 * math.log(p0 / pv)
                d = "forbid"
            else:
                s = pv * math.log(pv / p0)
                d = "require"
            if s > 0.0:
                scored.append((s, VerbCell(c, d)))
        scored.sort(key=lambda x: -x[0])
        cs = [vc for _s, vc in scored[:self.m]]
        self._cells[key] = cs
        return cs

    def violation_for(self, verb: str, slot: str, noun: str) -> int:
        key = (verb, slot, noun)
        v = self._cache.get(key)
        if v is not None:
            return v
        cls = self.inv.of(noun)
        out = 0
        for i, vc in enumerate(self.cells_for(verb, slot)):
            has = vc.cls in cls
            if (vc.direction == "forbid" and has) or \
               (vc.direction == "require" and not has):
                out |= 1 << i
        self._cache[key] = out
        return out

    def labels_for(self, verb: str, slot: str) -> List[str]:
        return [c.label(self.inv) for c in self.cells_for(verb, slot)]

    def labels(self) -> List[str]:
        return [f"cell {i}" for i in range(self.m)]
