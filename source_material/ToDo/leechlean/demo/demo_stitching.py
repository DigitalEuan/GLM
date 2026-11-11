#!/usr/bin/env python3
"""Demo: authoring a Lean file by stitching lattice-graph addresses.

Run:  python3 demo/demo_stitching.py

The library is the lattice-graph of the trusted 442-file corpus (bundled
compactly as data/library_core.npz).  This demo authors a NEW file --
Golay/Code_v2.lean, a rename of the coset-naming theorem plus a corollary --
without writing it out word-for-word:

  1. every tick of the new file is classified against the library:
       context-verified  -- this part is attested under this declaration
                            frame in the library (no new work needed);
       part-known        -- part known, but not under this frame (reuse in a
                            new usage -- the case the owner flagged);
       new               -- the part does not exist; it gets a fresh Leech
                            address on the fly, and the extended codebook
                            stays injective;
  2. every joining between consecutive ticks is checked against the
     library's joinings;
  3. the stitched file is PROJECTED: the tick stream decodes through the
     extended codebook to exact file bytes, ready for a real Lean toolchain
     (this sandbox has none -- 'verified' here means syntactically attested
     in the trusted library under the same frame context);
  4. a query walks the graph: sampled continuation of the new theorem's
     proof from the joining distribution.

Everything is measured and printed; the projected file and the delta
manifest are written next to this demo.
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from leechlean.library import Library
from leechlean.lean_parts import tokenize
from leechlean.leech_core import in_leech_many

codebook = json.load(open(HERE.parent / "data/codebook.json"))
PARTS = codebook["parts"]
ADDRESSES = {k: tuple(p["address"]) for k, p in PARTS.items()}
COUNTS = {k: p.get("count", 1) for k, p in PARTS.items()}

lib = Library.load_core(HERE.parent / "data/library_core.npz",
                        ADDRESSES, COUNTS)
print(f"library: {len(lib.part_files):,} parts, "
      f"{len(lib.edge_count):,} joinings, {len(lib.ctx_files):,} "
      f"(part, frame) contexts, from {lib.n_library_files} trusted files "
      f"({lib.n_library_tokens:,} tokens)")

# ------------------------------------------------ the authoring scenario
text = (HERE / "sample_Golay_Code.lean").read_text(encoding="utf-8",
                                                   errors="replace")
OLD = "syn_eq_iff_isCodeword_symmDiff"
NEW = "cosets_named_by_syndromes"
v2 = text.replace(OLD, NEW)                       # rename (2 references)
corollary = (
    "\n/-- The syndromes name the cosets: equal syndromes give a codeword\n"
    "difference, ready for transport along the coset. -/\n"
    "theorem syn_eq_coset (a b : Word) (h : syn a = syn b) :\n"
    "    IsCodeword (symmDiff a b) :=\n"
    f"  ({NEW} a b).mp h\n"
)
v2 = v2.replace("\nend GLM.Golay24\n", corollary + "\nend GLM.Golay24\n")
toks = tokenize(v2)
print(f"\nauthoring Golay/Code_v2.lean: rename {OLD} -> {NEW}; "
      f"add corollary syn_eq_coset")
print(f"ticks: {len(toks)}  "
      f"(structural: {sum(1 for t in toks if t.kind not in ('ws', 'comment'))})")

# ------------------------------------------------ classify + address
keys, frames, tick_status, join_status = lib.classify_ticks(toks)
from collections import Counter
st, js = Counter(tick_status), Counter(join_status)
new_parts = sorted({k for k, s in zip(keys, tick_status) if s == "new"})
for k in new_parts:
    lib.address_new_part(k, count=keys.count(k))

print("\n-- classification --")
print(f"context-verified ticks: {st.get('ctx', 0):,} "
      f"({st.get('ctx', 0)/len(toks)*100:.1f}%)")
print(f"part-known ticks:      {st.get('part', 0):,}")
print(f"new ticks:             {st.get('new', 0):,}")
print(f"known joinings:        {js.get('known', 0):,}   "
      f"new joinings: {js.get('new', 0):,}")
print("\n-- the delta (the parts in question) --")
A_new = np.array([lib.addresses[k] for k in new_parts], dtype=np.int64)
for k in new_parts:
    a = lib.addresses[k]
    print(f"  {k[:46].replace(chr(10), ' '):48} count {keys.count(k)}  "
          f"address {list(a)[:4]}...  energy {sum(c*c for c in a)//8}")
print(f"  new addresses on the Leech lattice: "
      f"{bool(in_leech_many(A_new).all())}")
print(f"  extended codebook still injective:  "
      f"{len(set(lib.addresses.values())) == len(lib.addresses)}")

# ------------------------------------------------ projection
proj = lib.project(toks)
print(f"\n-- projection --")
print(f"byte-exact through the extended codebook: {proj == v2}")
out = HERE / "stitched_Golay_Code_v2.lean"
out.write_text(v2)
print(f"projected file written: {out.name} (ready for a Lean toolchain; "
      f"not compiled here -- this sandbox has no Lean/Mathlib)")

# provenance: how well-attested are the stitched contexts?
print("\n-- provenance of the stitched proof body --")
i0 = keys.index(f"ident:{NEW}")
shown = set()
for i in range(i0, min(i0 + 80, len(keys))):
    if tick_status[i] == "ctx" and toks[i].kind not in ("ws",) \
            and keys[i] not in shown:
        shown.add(keys[i])
        print(f"  {keys[i][:26]:28} under {frames[i][:26]:28} "
              f"attested in {lib.ctx_attested(keys[i], frames[i])} library files")
    if len(shown) >= 6:
        break

# ------------------------------------------------ a query
i_by = v2.index("theorem " + NEW)
j_by = v2[i_by:].index(":= by") + len(":= by\n")
prefix = [t.key for t in tokenize(v2[:i_by + j_by])]
rng = np.random.default_rng(7)
seq = list(prefix)
for _ in range(44):
    conts = lib.continuations(seq[-1])[:8]
    if not conts:
        break
    w = np.array([c for _, c in conts], dtype=float)
    w /= w.sum()
    seq.append(conts[int(rng.choice(len(conts), p=w))][0])
tail = "".join(k.split(":", 1)[1] for k in seq[-46:])
print("\n-- query: 'prove this' (sampled continuation of the new theorem) --")
print("  " + tail.replace("\n", "\n  ")[:400])
print("  [unverified graph proposal; greedy top-1 continuation accuracy "
      "over the corpus: 40.6%]")
