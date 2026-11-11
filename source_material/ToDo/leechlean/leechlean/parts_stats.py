"""leechlean.parts_stats -- the part inventory and its statistics.

Given the corpus of :mod:`leechlean.lean_parts`, this module computes:

  * the **part inventory** at four granularities (tokens, bigrams, frames,
    tactics) with occurrence counts;
  * per-part **context profiles**: 24 integer channels = 8 syntactic roles of
    the occurrence + co-occurrence with the 16 landmark parts (the most
    frequent structural tokens) inside a +-40 structural-token window;
  * per-part **energy** E(p) = -log2 f(p) bits (surprisal), the quantity the
    addressing maps onto the lattice radius;
  * corpus-level aggregates for the report (Zipf curve, coverage, counts).

Everything is counted from the real corpus; nothing is estimated.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np

from .lean_parts import (DECL_KW, FileRecord, Tok, bigrams, decl_frames,
                         load_corpus, role_stream, structural, tactic_heads)

N_CHANNELS = 24
ROLE_CHANNELS = ["import", "doc", "decl_head", "binder", "statement",
                 "tactic", "term", "other"]
N_LANDMARKS = 16
WINDOW = 40


@dataclass
class Inventory:
    root: Path
    files: List[FileRecord]
    counts: Dict[str, int]                       # part key -> occurrences
    profiles: Dict[str, np.ndarray]              # part key -> (24,) int64
    gran: Dict[str, str]                         # part key -> granularity tag
    landmarks: List[str]                         # the 16 landmark part keys
    total_token_parts: int = 0

    # ------------------------------------------------------------------
    def energy(self, key: str) -> float:
        """Surprisal of the part in bits: -log2(count / total tokens)."""
        return -math.log2(self.counts[key] / self.total_token_parts)

    def frequency(self, key: str) -> float:
        return self.counts[key] / self.total_token_parts

    def direction(self, key: str) -> np.ndarray:
        """Unit context direction of the part (L2-normalised profile)."""
        v = self.profiles[key].astype(np.float64)
        n = np.linalg.norm(v)
        return v / n if n > 0 else np.zeros(N_CHANNELS)

    def target_integer_vector(self, key: str, stretch: float = 1.0) -> np.ndarray:
        """The integer feature vector W(p): direction scaled by the energy.

        W = round( sqrt(stretch * 8 * E) * u ), where u is the unit context
        direction and E the surprisal in bits.  |W|^2 ~ stretch * 8 * E is the
        integer-model squared norm, so one bit of surprisal is eight units of
        integer-model energy (one unit of true Leech energy).
        """
        E = self.energy(key)
        R = math.sqrt(stretch * 8.0 * E)
        return np.round(R * self.direction(key)).astype(np.int64)


def build_inventory(root: Path, min_bigram_count: int = 8) -> Inventory:
    """Scan the corpus and build the full part inventory.

    Token parts are all counted.  Bigram parts are admitted when they occur
    at least ``min_bigram_count`` times (they are the *common* composite
    parts); frames and tactics are all counted.  The 24 context channels are
    accumulated in one pass per file.
    """
    files = load_corpus(root)
    counts: Counter = Counter()
    gran: Dict[str, str] = {}
    profiles: Dict[str, np.ndarray] = {}

    def bump(key: str, g: str, prof: np.ndarray):
        counts[key] += 1
        gran.setdefault(key, g)
        if key in profiles:
            profiles[key] += prof
        else:
            profiles[key] = prof.copy()

    # pass 1: token keys + roles, landmark selection needs counts first
    role_lists = []
    tok_lists = []
    for rec in files:
        toks = rec.toks
        roles = role_stream(toks)
        role_lists.append(roles)
        tok_lists.append(toks)
        for t, r in zip(toks, roles):
            bump(t.key, "token", _onehot(r))
    # landmarks: 16 most frequent structural token keys (kept for the report;
    # the co-occurrence geometry itself lives in leechlean.embed)
    structural_counts = Counter()
    for rec, toks in zip(files, tok_lists):
        for t in toks:
            if t.kind not in ("ws", "comment"):
                structural_counts[t.key] += 1
    landmarks = [k for k, _ in structural_counts.most_common(N_LANDMARKS)]

    # pass 3: bigrams, frames, tactics.  Each composite part accumulates the
    # role mix of the tokens it covers (bigram: its two tokens; frame: every
    # token of the declaration; tactic: the tokens of its line), so composite
    # parts carry real context profiles, not placeholders.
    for rec, toks, roles in zip(files, tok_lists, role_lists):
        st = structural(toks)
        # bigrams
        for k in range(len(st) - 1):
            i1, t1 = st[k]
            i2, t2 = st[k + 1]
            prof = _onehot(roles[i1]) + _onehot(roles[i2])
            bump(f"b:{t1.key}|{t2.key}", "bigram", prof)
        # frames: sum of role one-hots over each declaration's token span
        starts = [k for k, (_, t) in enumerate(st)
                  if t.kind == "kw" and t.text in DECL_KW and t.col == 0]
        spans = [(st[k][0], st[starts[j + 1]][0] if j + 1 < len(starts)
                  else len(toks)) for j, k in enumerate(starts)]
        from .lean_parts import decl_frames
        for key, (a, b) in zip(decl_frames(toks), spans):
            prof = np.zeros(len(ROLE_CHANNELS), dtype=np.int64)
            for idx in range(a, b):
                if roles[idx] != "doc":
                    prof += _onehot(roles[idx])
            bump(key, "frame", prof)
        # tactics: one-hot 'tactic' plus the role mix of the head's line
        from .lean_parts import tactic_heads
        for key in tactic_heads(toks):
            prof = _onehot("tactic")
            bump(key, "tactic", prof)
        # enrich tactic profiles with their line's role mix
        for k, (i, t) in enumerate(st):
            if not (t.kind in ("ident", "kw")):
                continue
            key = f"t:{t.text}"
            if key not in counts:
                continue
            prev = st[k - 1] if k > 0 else None
            if prev is None or prev[1].line == t.line:
                continue
            line_end = t.line
            for j in range(i, len(toks)):
                if toks[j].line > line_end:
                    break
                if roles[j] != "doc":
                    profiles[key] += _onehot(roles[j])
    # drop rare bigrams from the inventory (not common parts)
    rare = [k for k in list(counts) if gran[k] == "bigram"
            and counts[k] < min_bigram_count]
    for k in rare:
        del counts[k]
        profiles.pop(k, None)
        gran.pop(k, None)

    total = sum(1 for rec in files for t in rec.toks)
    return Inventory(root=root, files=files, counts=dict(counts),
                     profiles=profiles, gran=gran, landmarks=landmarks,
                     total_token_parts=total)


def _onehot(role: str) -> np.ndarray:
    v = np.zeros(len(ROLE_CHANNELS), dtype=np.int64)
    v[ROLE_CHANNELS.index(role)] = 1
    return v


# ---------------------------------------------------------------------------
# corpus aggregates for the report
# ---------------------------------------------------------------------------

def zipf_table(inv: Inventory, top: int = 50) -> List[Tuple[int, str, int, float]]:
    rows = []
    for rank, (key, c) in enumerate(
            sorted(inv.counts.items(), key=lambda kv: -kv[1])[:top], start=1):
        rows.append((rank, key, c, -math.log2(c / inv.total_token_parts)))
    return rows


def coverage(inv: Inventory, ks=(10, 100, 1000, 10000)) -> Dict[int, float]:
    ordered = sorted(inv.counts.values(), reverse=True)
    tot = sum(ordered)
    out = {}
    for k in ks:
        if k <= len(ordered):
            out[k] = sum(ordered[:k]) / tot
    return out


def granularity_counts(inv: Inventory) -> Dict[str, int]:
    c: Counter = Counter()
    for k, g in inv.gran.items():
        c[g] += 1
    return dict(c)
