"""leechlean.library -- the Lean library as a lattice-graph you author on.

The owner's application concept, made runnable: Lean 4 as a growing set of
knowledge.  A library is the lattice-graph of a trusted corpus -- every part
at its address, every construction joining with its counts, and every
(part, declaration-frame) co-occurrence recording *where* a part is known to
be usable.  Authoring a new file is then **stitching**:

  * a tick whose part AND its enclosing declaration frame already occur
    together in the library is CONTEXT-VERIFIED -- the library has already
    seen this word used in this kind of declaration, and it is imported
    rather than rebuilt;
  * a tick whose part is known but not under this frame is PART-KNOWN --
    reused material in a new usage, exactly the case the owner flagged
    ("application can change the lean meaning");
  * a tick whose part is unknown is NEW -- it gets a fresh Leech address on
    the fly (target = sqrt(32 E) on its role direction, first-fit radial
    displacement against the occupied cells), keeping the extended codebook
    injective;
  * a joining between consecutive ticks is KNOWN if the library contains
    that edge, NEW otherwise.

The stitched file still **projects**: the tick stream decodes through the
extended codebook to the exact file bytes, ready for a real Lean toolchain
(the sandbox has none; the library's notion of verified is syntactic
attestation under a frame context, stated as such).

Queries walk the graph: given a prefix of parts, the library continues along
the heaviest joinings (a count model over the part vocabulary) and projects
the completion to a file -- the graph-generated result is labelled
unverified, and the experiments measure how often such walks agree with what
the corpus actually wrote.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from .addressing import DISPLACE_STEP, BITS_PER_SHELL, _identity_direction
from .lean_parts import DECL_KW, Tok, decl_frames, structural, tokenize
from .leech_core import DIM, nearest_leech

ROLE_OF_KIND = {
    "kw": 1, "ident": 2, "sym": 3, "num": 4, "str": 4,
    "ws": 0, "comment": 0,
}
TOP_FRAME = "f:top"


def tick_frames(toks: Sequence[Tok]) -> List[str]:
    """Frame key of each token's enclosing top-level declaration ('f:top'
    before the first declaration).  Frames are the declaration parts of the
    codebook: f:<kind>|body=<body>|len2=<statement-length bucket>."""
    st = structural(toks)
    starts = [i for i, (_, t) in enumerate(st)
              if t.kind == "kw" and t.text in DECL_KW and t.col == 0]
    frames = decl_frames(toks) if starts else []
    out = [TOP_FRAME] * len(toks)
    if not starts:
        return out
    # token index ranges: structural position i -> original token index
    st_idx = [i for i, _ in st]
    for si, i0 in enumerate(starts):
        lo = st_idx[i0]
        hi = st_idx[starts[si + 1]] if si + 1 < len(starts) else len(toks)
        fk = frames[si] if si < len(frames) else TOP_FRAME
        for j in range(lo, hi):
            out[j] = fk
    return out


@dataclass
class Library:
    addresses: Dict[str, Tuple[int, ...]]
    counts: Dict[str, int]
    part_files: Dict[str, int]                     # part -> number of files
    edge_count: Dict[Tuple[str, str], int]         # directed joining -> count
    edge_files: Dict[Tuple[str, str], int]         # joining -> number of files
    ctx_files: Dict[Tuple[str, str], int]          # (part, frame) -> files
    n_library_files: int = 0
    n_library_tokens: int = 0
    occupied: set = field(default_factory=set)
    role_dir: Dict[str, np.ndarray] = field(default_factory=dict)
    _out: Optional[Dict[str, List[Tuple[str, int]]]] = None

    # ------------------------------------------------------------------
    @classmethod
    def from_corpus(cls, corpus, addresses: Dict[str, Tuple[int, ...]],
                    counts: Dict[str, int]) -> "Library":
        part_files: Counter = Counter()
        edge_count: Counter = Counter()
        edge_files: Dict[Tuple[str, str], set] = defaultdict(set)
        ctx_files: Dict[Tuple[str, str], set] = defaultdict(set)
        n_tok = 0
        for rec in corpus:
            toks = rec.toks
            frames = tick_frames(toks)
            keys = [t.key for t in toks]
            n_tok += len(keys)
            for k, f in zip(keys, frames):
                ctx_files[(k, f)].add(rec.rel)
            for k in set(keys):
                part_files[k] += 1
            for e in zip(keys, keys[1:]):
                edge_count[e] += 1
                edge_files[e].add(rec.rel)
        lib = cls(addresses=addresses, counts=counts,
                  part_files=dict(part_files),
                  edge_count=dict(edge_count),
                  edge_files={e: len(v) for e, v in edge_files.items()},
                  ctx_files={c: len(v) for c, v in ctx_files.items()},
                  n_library_files=len(corpus), n_library_tokens=n_tok)
        lib.occupied = set(addresses.values())
        return lib

    # ------------------------------------------------------------------
    def has_part(self, key: str) -> bool:
        return self.part_files.get(key, 0) > 0

    def ctx_attested(self, key: str, frame: str) -> int:
        """Number of library files using this part under this frame."""
        return self.ctx_files.get((key, frame), 0)

    def edge_attested(self, u: str, v: str) -> int:
        """Files in the library joining u to v."""
        return self.edge_files.get((u, v), 0)

    # ------------------------------------------------------------------
    # authoring
    # ------------------------------------------------------------------
    def classify_ticks(self, toks: Sequence[Tok]):
        """Per-tick and per-joining status of a candidate file against the
        library.  Status: 'ctx' (part + frame attested), 'part' (part known,
        frame context new), 'new' (part unknown).  Join status: 'known' /
        'new' (library contains the directed joining or not)."""
        frames = tick_frames(toks)
        keys = [t.key for t in toks]
        tick_status = []
        for k, f in zip(keys, frames):
            if not self.has_part(k):
                tick_status.append("new")
            elif self.ctx_attested(k, f) > 0:
                tick_status.append("ctx")
            else:
                tick_status.append("part")
        join_status = [
            ("known" if self.edge_files.get((a, b), 0) > 0 else "new")
            for a, b in zip(keys, keys[1:])]
        return keys, frames, tick_status, join_status

    def _role_direction(self, key: str) -> np.ndarray:
        """Deterministic direction for a new part: its kind's role channel
        blended with the identity-hash direction of the co-occurrence
        channels -- the same escape the corpus build uses for forced
        identities, so same-kind new parts spread instead of piling onto
        one ray."""
        if key not in self.role_dir:
            role = np.zeros(8)
            ch = ROLE_OF_KIND.get(key.split(":", 1)[0], 2)
            role[min(ch, 7)] = 1.0
            d = np.concatenate([role, _identity_direction(key)])
            self.role_dir[key] = d / np.linalg.norm(d)
        return self.role_dir[key]

    def address_new_part(self, key: str, count: int = 1) -> Tuple[int, ...]:
        """Assign a fresh Leech address to a genuinely new part, on the fly.

        Same rule as the corpus build: target radius sqrt(32 E) with
        E = log2(N_tokens / count) bits of surprisal along the part's role
        direction, quantised to the exact nearest Leech point, displaced
        radially on collision -- the extended codebook stays injective.
        Returns the address and records the part."""
        if key in self.addresses:
            return self.addresses[key]
        E = np.log2(self.n_library_tokens / max(count, 1))
        base = np.sqrt(32.0 * max(E, 1.0)) * self._role_direction(key)
        j = 0
        while True:
            T = base * (1.0 + DISPLACE_STEP * j)
            Q = nearest_leech(T[None, :].astype(np.float64))
            pt = tuple(int(v) for v in Q[0])
            if pt not in self.occupied:
                self.occupied.add(pt)
                self.addresses[key] = pt
                self.counts[key] = count
                return pt
            j += 1

    def project(self, toks: Sequence[Tok]) -> str:
        """Materialise the tick stream to exact file bytes (all parts must
        be addressed; new ones must have been assigned)."""
        out = []
        for t in toks:
            if t.key not in self.addresses:
                raise KeyError(f"unaddressed part {t.key!r}")
            out.append(t.key.split(":", 1)[1])
        return "".join(out)

    # ------------------------------------------------------------------
    # queries
    # ------------------------------------------------------------------
    def continuations(self, key: str) -> List[Tuple[str, int]]:
        """Library joinings out of a part, heaviest first."""
        if self._out is None:
            self._out = defaultdict(list)
            for (u, v), c in self.edge_count.items():
                self._out[u].append((v, c))
            for v in self._out.values():
                v.sort(key=lambda e: -e[1])
        return self._out.get(key, [])

    def query_complete(self, prefix_keys: Sequence[str], n: int = 40
                       ) -> List[str]:
        """Greedy completion: walk the heaviest joining at each tick."""
        seq = list(prefix_keys)
        for _ in range(n):
            cont = self.continuations(seq[-1])
            if not cont:
                break
            seq.append(cont[0][0])
        return seq

    # ------------------------------------------------------------------
    # persistence (package-side load)
    # ------------------------------------------------------------------
    def save_core(self, path: Path) -> None:
        """Compact npz of everything the package demos need.  Parts are
        stored as an object array: comment parts run to thousands of
        characters, and a fixed-width unicode grid would be gigantic."""
        parts = sorted(self.part_files)
        pidx = {p: i for i, p in enumerate(parts)}
        edges = [(pidx[u], pidx[v], self.edge_count[(u, v)],
                  self.edge_files[(u, v)])
                 for (u, v) in self.edge_count if u in pidx and v in pidx]
        ctxs = [(pidx[p], f, n) for (p, f), n in self.ctx_files.items()
                if p in pidx]
        np.savez_compressed(
            path,
            parts=np.array(parts, dtype=object),
            part_files=np.array([self.part_files[p] for p in parts],
                                dtype=np.int32),
            edge_u=np.array([e[0] for e in edges], dtype=np.int32),
            edge_v=np.array([e[1] for e in edges], dtype=np.int32),
            edge_c=np.array([e[2] for e in edges], dtype=np.int32),
            edge_f=np.array([e[3] for e in edges], dtype=np.int32),
            ctx_p=np.array([c[0] for c in ctxs], dtype=np.int32),
            ctx_f=np.array([c[1] for c in ctxs], dtype="U64"),
            ctx_n=np.array([c[2] for c in ctxs], dtype=np.int32),
            n_library_files=self.n_library_files,
            n_library_tokens=self.n_library_tokens,
        )

    @classmethod
    def load_core(cls, path: Path, addresses: Dict[str, Tuple[int, ...]],
                  counts: Dict[str, int]) -> "Library":
        z = np.load(path, allow_pickle=True)
        parts = list(z["parts"])
        part_files = {p: int(n) for p, n in zip(parts, z["part_files"])}
        edge_count, edge_files = {}, {}
        for u, v, c, f in zip(z["edge_u"], z["edge_v"], z["edge_c"],
                               z["edge_f"]):
            k = (parts[int(u)], parts[int(v)])
            edge_count[k] = int(c)
            edge_files[k] = int(f)
        ctx_files = {}
        for p, f, n in zip(z["ctx_p"], z["ctx_f"], z["ctx_n"]):
            ctx_files[(parts[int(p)], str(f))] = int(n)
        lib = cls(addresses=addresses, counts=counts,
                  part_files=part_files, edge_count=edge_count,
                  edge_files=edge_files, ctx_files=ctx_files,
                  n_library_files=int(z["n_library_files"]),
                  n_library_tokens=int(z["n_library_tokens"]))
        lib.occupied = set(addresses.values())
        return lib
