"""
learn.py — fitting the selection model and searching the encoding space.

Two things are learned, both from corpus counts, never from hand-written lists.

1.  What a verb expects.  For every semantic class c and every verb v we
    estimate p(c | v, slot), the share of the verb's attested arguments in that
    slot that belong to class c, smoothed towards the verb's WordNet
    lexicographer class and then towards the global slot distribution:

        p_v(c) = (n_v(c) + k1 * p_L(c)) / (N_v + k1)
        p_L(c) = (n_L(c) + k2 * p_0(c)) / (N_L + k2)

    Then  c is required  iff p_v(c) >= theta_req
          c is forbidden iff p_v(c) <= theta_forb and p_0(c) >= base_min.

    Note that these are per-class quantities: they do not depend on which
    classes end up occupying the 24 MOG cells.  That makes the encoding search
    below cheap and exact.

2.  Which 24 WordNet classes occupy the 24 MOG cells.  Greedy forward
    selection plus a swap pass, scored on a development split of the training
    corpus.  The test corpus is never touched by the search.
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from ..substrate import popcount
from .encoding import Composer, Layout, SelectionModel, SlotModel, selection_layout
from .features import ClassInventory, Lexicon

DATA = Path(__file__).resolve().parent.parent.parent / "data"


# ══════════════════════════════════════════════════════════════════════════════
# Corpus pairs
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Pairs:
    rows: Dict[str, List[Tuple[str, str, int]]]

    @classmethod
    def load(cls, *paths: Path) -> "Pairs":
        if not paths:
            paths = tuple(p for p in (DATA / "corpus_pairs.json",
                                      DATA / "dep_pairs.json") if p.exists())
        rows: Dict[str, List[Tuple[str, str, int]]] = {}
        for p in paths:
            raw = json.loads(p.read_text())
            for k, v in raw.items():
                rows[k] = [tuple(x) for x in v]
        return cls(rows=rows)

    def get(self, key: str) -> List[Tuple[str, str, int]]:
        return self.rows.get(key, [])

    def filtered(self, lex: Lexicon) -> "Pairs":
        return Pairs({k: [(v, n, c) for v, n, c in rows
                          if v in lex.verbs and n in lex.nouns]
                      for k, rows in self.rows.items()})


def split_pairs(rows, frac: float, seed: int):
    rows = list(rows)
    random.Random(seed).shuffle(rows)
    k = int(len(rows) * frac)
    return rows[k:], rows[:k]


# ══════════════════════════════════════════════════════════════════════════════
# Per-class statistics and the required / forbidden masks
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class FitParams:
    theta_req: float = 0.90
    theta_forb: float = 0.02
    base_min: float = 0.05
    k1: float = 4.0
    k2: float = 20.0
    min_count: float = 2.0


@dataclass
class ClassMasks:
    """required / forbidden as bitmasks over the FULL class inventory."""

    required: Dict[str, int]
    forbidden: Dict[str, int]
    back_required: Dict[str, int]
    back_forbidden: Dict[str, int]
    p0: List[float]

    def masks(self, verb: str, lexname: Optional[str]) -> Tuple[int, int]:
        if verb in self.required:
            return self.required[verb], self.forbidden[verb]
        if lexname is not None and lexname in self.back_required:
            return self.back_required[lexname], self.back_forbidden[lexname]
        return 0, 0


def fit_class_masks(inv: ClassInventory, lex: Lexicon, rows, par: FitParams
                    ) -> ClassMasks:
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
        nl = n_L[L] if L is not None else None
        if L is not None:
            N_L[L] += c
        for cl in cls:
            nv[cl] += c
            n_0[cl] += c
            if nl is not None:
                nl[cl] += c
    p0 = [(n_0.get(i, 0.0) / N_0 if N_0 else 0.0) for i in range(m)]

    p_L: Dict[str, List[float]] = {}
    for L, nl in n_L.items():
        NL = N_L[L]
        p_L[L] = [(nl.get(i, 0.0) + par.k2 * p0[i]) / (NL + par.k2) for i in range(m)]

    def masks_from(p: Sequence[float]) -> Tuple[int, int]:
        req = forb = 0
        for i in range(m):
            if p[i] >= par.theta_req:
                req |= 1 << i
            elif p[i] <= par.theta_forb and p0[i] >= par.base_min:
                forb |= 1 << i
        return req, forb

    required: Dict[str, int] = {}
    forbidden: Dict[str, int] = {}
    for v, nv in n_v.items():
        NV = N_v[v]
        if NV < par.min_count:
            continue
        r = lex.verbs.get(v)
        base = p_L.get(r["lexname"] if r else None, p0)
        p = [(nv.get(i, 0.0) + par.k1 * base[i]) / (NV + par.k1) for i in range(m)]
        required[v], forbidden[v] = masks_from(p)

    back_req: Dict[str, int] = {}
    back_forb: Dict[str, int] = {}
    for L, p in p_L.items():
        back_req[L], back_forb[L] = masks_from(p)

    return ClassMasks(required, forbidden, back_req, back_forb, p0)


# ══════════════════════════════════════════════════════════════════════════════
# Projecting the class masks onto a layout
# ══════════════════════════════════════════════════════════════════════════════

def project(mask: int, sel: Sequence[int], mode: str = "any") -> int:
    """Project a full-inventory bitmask onto the cells of a selection layout."""
    out = 0
    for i, cl in enumerate(sel):
        if (mask >> cl) & 1:
            out |= 1 << i
    return out


def model_from_masks(inv: ClassInventory, sel: Sequence[int],
                     subj: ClassMasks, obj: ClassMasks,
                     name: str = "selection") -> SelectionModel:
    layout = Layout(m=len(sel), cells=[frozenset({c}) for c in sel], name=name)
    layout.rebuild(len(inv))

    def slot(cm: ClassMasks) -> SlotModel:
        return SlotModel(
            required={v: project(mk, sel) for v, mk in cm.required.items()},
            forbidden={v: project(mk, sel) for v, mk in cm.forbidden.items()},
            back_required={L: project(mk, sel) for L, mk in cm.back_required.items()},
            back_forbidden={L: project(mk, sel) for L, mk in cm.back_forbidden.items()},
        )

    return SelectionModel(layout=layout, subj=slot(subj), obj=slot(obj))


# ══════════════════════════════════════════════════════════════════════════════
# Evaluation: pseudo-disambiguation
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class PseudoTask:
    slot: str
    items: List[Tuple[str, str, str]]

    @classmethod
    def build(cls, rows, slot: str, noun_pool: Sequence[str],
              attested: Dict[str, set], seed: int, max_items: int = 5000
              ) -> "PseudoTask":
        rnd = random.Random(seed)
        rows = list(rows)
        rnd.shuffle(rows)
        items = []
        for v, n, _c in rows:
            if len(items) >= max_items:
                break
            for _ in range(20):
                m = rnd.choice(noun_pool)
                if m != n and m not in attested.get(v, ()):
                    items.append((v, n, m))
                    break
        return cls(slot=slot, items=items)


def evaluate_pseudo(comp: Composer, task: PseudoTask) -> Dict[str, float]:
    correct = 0.0
    ties = 0
    for v, good, bad in task.items:
        wg = popcount(comp.slot_violation(v, task.slot, good))
        wb = popcount(comp.slot_violation(v, task.slot, bad))
        if wg < wb:
            correct += 1
        elif wg == wb:
            correct += 0.5
            ties += 1
    n = max(1, len(task.items))
    return {"acc": correct / n, "n": n, "tie_rate": ties / n}


# ══════════════════════════════════════════════════════════════════════════════
# The encoding-space search
# ══════════════════════════════════════════════════════════════════════════════

class ItemMatrix:
    """Per-item, per-class violation indicators, precomputed once.

    For every dev item (verb, good noun, bad noun) and every class c we know
    whether c would be a violated cell for the good noun and for the bad noun.
    Because the estimator is per-class, the violation weight of any layout is
    just the sum of these indicators over the selected classes, so the search
    never has to refit the model.
    """

    def __init__(self, inv: ClassInventory, lex: Lexicon, cm: ClassMasks,
                 task: PseudoTask):
        self.n = len(task.items)
        self.good: List[int] = []
        self.bad: List[int] = []
        full = (1 << len(inv)) - 1
        for v, g, b in task.items:
            r = lex.verbs.get(v)
            req, forb = cm.masks(v, r["lexname"] if r else None)
            pg = _prov_mask(inv, g)
            pb = _prov_mask(inv, b)
            self.good.append((req & ~pg & full) | (pg & forb))
            self.bad.append((req & ~pb & full) | (pb & forb))

    def score(self, sel: Sequence[int]) -> float:
        m = 0
        for c in sel:
            m |= 1 << c
        tot = 0.0
        for g, b in zip(self.good, self.bad):
            wg = popcount(g & m)
            wb = popcount(b & m)
            if wg < wb:
                tot += 1
            elif wg == wb:
                tot += 0.5
        return tot / max(1, self.n)


_PROV_CACHE: Dict[Tuple[int, str], int] = {}


def _prov_mask(inv: ClassInventory, noun: str) -> int:
    key = (id(inv), noun)
    v = _PROV_CACHE.get(key)
    if v is None:
        v = 0
        for c in inv.of(noun):
            v |= 1 << c
        _PROV_CACHE[key] = v
    return v


def search_selection(inv: ClassInventory, mats: Sequence[ItemMatrix], k: int = 24,
                     init: Optional[Sequence[int]] = None, swaps: int = 2,
                     verbose: bool = True) -> Tuple[List[int], float, List[float]]:
    """Greedy forward selection of k classes, then swap improvement."""
    n = len(inv)

    def sc(sel):
        return sum(m.score(sel) for m in mats) / len(mats)

    sel: List[int] = list(init or [])
    history: List[float] = []
    while len(sel) < k:
        best_c, best_s = None, -1.0
        for c in range(n):
            if c in sel:
                continue
            s = sc(sel + [c])
            if s > best_s:
                best_c, best_s = c, s
        sel.append(best_c)
        history.append(best_s)
        if verbose:
            print(f"    +{inv.classes[best_c]:35s} -> {best_s:.4f}", flush=True)
    best = sc(sel)
    for sweep in range(swaps):
        improved = False
        for i in range(len(sel)):
            cur = sel[i]
            for c in range(n):
                if c in sel:
                    continue
                sel[i] = c
                s = sc(sel)
                if s > best + 1e-12:
                    best, cur, improved = s, c, True
            sel[i] = cur
        history.append(best)
        if verbose:
            print(f"  swap sweep {sweep+1}: {best:.4f}", flush=True)
        if not improved:
            break
    return sel, best, history
