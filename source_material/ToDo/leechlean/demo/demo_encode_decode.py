#!/usr/bin/env python3
"""Demo: a Lean file is a bunch of Leech addresses -- and back.

Run:  python3 demo_encode_decode.py [path/to/file.lean]

Encodes the file to one Leech lattice address per token using the codebook
computed from the GLM corpus, verifies every address is a true Leech lattice
point, decodes the address stream back to the exact file bytes, and reports
the file's tick dynamics (energy, path, work integral).
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import numpy as np
from leechlean.lean_parts import tokenize
from leechlean.leech_core import in_leech_many

codebook = json.load(open(HERE.parent / "data/codebook.json"))
PARTS = codebook["parts"]
CELLS = {tuple(p["address"]): k for k, p in PARTS.items()}

def main(path):
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    toks = tokenize(text)
    print(f"file: {path}")
    print(f"tokens (ticks): {len(toks)}")

    # ---- encode: one address per token
    stream = []
    for t in toks:
        p = PARTS.get(t.key)
        if p is None:
            sys.exit(f"unknown part {t.key!r} -- not in the corpus codebook; "
                     f"rebuild the codebook to admit it")
        stream.append(tuple(p["address"]))

    # ---- verify: every address is a Leech lattice point
    A = np.array(stream, dtype=np.int64)
    ok = in_leech_many(A)
    print(f"addresses on the Leech lattice: {int(ok.sum())} / {len(A)}")

    # ---- decode: addresses -> parts -> exact bytes
    back = "".join(CELLS[a].split(":", 1)[1] for a in stream)
    print(f"byte-exact round trip: {back == text}")

    # ---- tick dynamics
    energy = (A * A).sum(axis=1) / 8.0
    steps = A[1:] - A[:-1]
    path2 = float((steps * steps).sum())
    rng = np.random.default_rng(0)
    S = A[rng.permutation(len(A))]
    spath2 = float(((S[1:] - S[:-1]) ** 2).sum())
    W = A.cumsum(axis=0)
    print(f"total energy: {energy.sum():.0f} lattice units "
          f"({energy.sum()/4:.0f} bits of surprisal)")
    print(f"path length^2: {path2:.0f} (shuffled control {spath2:.0f}, "
          f"ratio {path2/spath2:.3f})")
    print(f"work integral ends at lattice point W = {W[-1].tolist()} "
          f"(on lattice: {bool(in_leech_many(W[-1][None, :])[0])})")
    print()
    print("first 6 ticks:")
    for i in range(6):
        k = CELLS[stream[i]]
        print(f"  tick {i}: {k[:34]:36} energy {int(energy[i]):4} "
              f"address {list(stream[i])}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else HERE / "sample_Golay_Code.lean")
