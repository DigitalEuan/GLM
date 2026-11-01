"""Round 6: a GLM-substrate observer on the centre column (EMP).

Cut the sequence into non-overlapping 24-bit blocks and record, for each block, its
distance to the binary Golay code (the GLM substrate's coset-leader weight,
`glm_universal.substrate.golay_decode.coset_weight`).  If every 24-bit block occurred
equally often, the distances 0,1,2,3,4 would occur in proportion 1:24:276:2024:1771
(out of the 4096 cosets).  A chi-square statistic (4 degrees of freedom; 95% point 9.49,
99.9% point 18.47) compares the observed census with that law.

This is one more finite-state observer.  Passing it is "no pattern found by this observer
at this length", not a proof of anything about the infinite column.
"""
from __future__ import annotations

import json
import os
import sys
import types
import importlib
from pathlib import Path

import r6_common as C

HERE = Path(__file__).resolve().parent
GLM_OVERLAY = Path(os.environ.get("GLM_OVERLAY", "/tmp/glm/glm_repo/overlay"))
EXPECTED = {0: 1, 1: 24, 2: 276, 3: 2024, 4: 1771}


def coset_weight_fn():
    pkg = types.ModuleType("glm_universal")
    pkg.__path__ = [str(GLM_OVERLAY / "glm_universal")]
    sys.modules.setdefault("glm_universal", pkg)
    return importlib.import_module("glm_universal.substrate.golay_decode").coset_weight


def census(bits, cw):
    counts = {w: 0 for w in EXPECTED}
    nblocks = len(bits) // 24
    for b in range(nblocks):
        m = 0
        for x in bits[24 * b: 24 * b + 24]:
            m = (m << 1) | x
        counts[cw(m)] += 1
    chi2 = sum((counts[w] - nblocks * EXPECTED[w] / 4096) ** 2 / (nblocks * EXPECTED[w] / 4096)
               for w in EXPECTED)
    return {"blocks": nblocks, "counts": counts, "chi2_4dof": round(chi2, 3)}


def main():
    cw = coset_weight_fn()
    import numpy as np
    cc = np.load(HERE.parent / "data" / "cc_1M.npy").astype(int).tolist()
    exact = C.centre_column(1 << 16)
    assert cc[: len(exact)] == exact, "supplied cc_1M.npy disagrees with the exact generator"
    N = len(cc)
    seqs = {
        "rule30-centre (supplied 1M file, prefix checked exactly)": cc,
        "sha256-counter": C.sha256_stream(N),
        "champernowne": C.champernowne_binary(N),
        "periodic-7": C.periodic(N),
    }
    out = {name: census(s, cw) for name, s in seqs.items()}
    (HERE / "r6_golay_census.json").write_text(json.dumps(out, indent=1))
    for k, v in out.items():
        print(k, v)


if __name__ == "__main__":
    main()
