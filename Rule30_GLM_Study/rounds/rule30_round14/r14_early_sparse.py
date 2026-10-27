"""Round 14 (EMP): an early-time excess of near-white 24-bit windows in the Rule 30 centre column.

Found while checking the slide-lens walk (r14_shortcut_network.py): in the first 2^17 steps the walk
returns to a network point two steps later far more often than a fair-coin walk.  The events come
from 24-bit windows with at most 3 black cells (or at most 3 white cells), which all snap to the
same network point.  The statistic below needs no lattice at all: it counts such windows directly.

The finding came from exploration, so it is reported with that caveat; the null distribution comes
from 5000 independent fair-coin sequences of the same length.  Neighbouring columns (k = -2..2) are
shown too (they are not independent evidence: they share the same white triangles).
"""
import math, os
import numpy as np
import sources

HERE = os.path.dirname(os.path.abspath(__file__))
L, K = 24, 3
P = sum(math.comb(L, i) for i in range(K + 1)) / 2 ** L     # P(window has <= 3 black cells)


def counts(b):
    c = np.concatenate([[0], np.cumsum(b, dtype=np.int64)]); w = c[L:] - c[:-L]
    return np.count_nonzero(w <= K), np.count_nonzero(w >= L - K)


def main():
    out = [f"Near-white (<= {K} black) and near-black (<= {K} white) windows of {L} bits; "
           f"expected rate {P:.3e} each per position", ""]
    r = sources.rule30(4194304)
    out.append("Rule 30 centre column, cumulative counts:")
    for n in [2 ** 14, 2 ** 15, 2 ** 16, 2 ** 17, 2 ** 18, 2 ** 19, 2 ** 20, 2 ** 22]:
        lo, hi = counts(r[:n])
        out.append(f"  first {n:8d} steps: near-white {lo:5d}  near-black {hi:5d}  (expected {n * P:8.1f} each)")
    n = 2 ** 17
    null = np.array([sum(counts(sources.prng(n, seed=50_000 + k))) for k in range(5000)])
    x = sum(counts(r[:n]))
    out.append("")
    out.append(f"First {n} steps, near-white + near-black windows: rule30 {x}; fair-coin null over 5000 sequences: "
               f"mean {null.mean():.1f}, sd {null.std():.1f}, 99.9th percentile {np.percentile(null, 99.9):.0f}, "
               f"max {null.max()}; null sequences >= rule30: {np.count_nonzero(null >= x)}")
    lo, hi = counts(r[n:])
    m = len(r) - n
    out.append(f"Out of sample, steps {n}..{len(r) - 1}: near-white {lo}, near-black {hi}, expected {m * P:.1f} each "
               f"(ratio {(lo + hi) / (2 * m * P):.3f})")
    out.append("")
    out.append(f"All 32 consecutive segments of {n} steps (look-elsewhere check), against the same null "
               f"(99th percentile {np.percentile(null, 99):.0f}, max {null.max()}):")
    for name in ("rule30", "sqrt2"):
        b = sources.ALL[name](32 * n)
        segs = [sum(counts(b[i * n:(i + 1) * n])) for i in range(32)]
        out.append(f"  {name:6s}: " + " ".join(map(str, segs)) + f"   (segments above the null maximum: "
                   f"{sum(x > null.max() for x in segs)})")
    out.append("  Chance that at least one of 32 fair-coin segments exceeds the maximum of 5000 null segments: "
               "about 32/5001 = 0.6%.  The statistic was chosen after seeing the data, so this is a lead to "
               "explain, not a confirmed pattern.")
    out.append("")
    out.append(f"Neighbouring columns, first {n} steps (near-white + near-black):")
    for k in (-2, -1, 1, 2):
        p = os.path.join(HERE, f"col{k}.bin")
        if os.path.exists(p):
            b = np.fromfile(p, dtype=np.uint8)
            out.append(f"  column {k:+d}: {sum(counts(b[:n]))}  (out of sample {n}..{len(b) - 1}: "
                       f"{sum(counts(b[n:]))}, expected {2 * (len(b) - n - L + 1) * P:.1f})")
    out.append("")
    out.append("Reading: a transient confined to the first segment, not a persistent pattern.  Over the first 2^17 steps the centre column "
               "has several long, almost-white stretches (isolated black cells in white), which a fair coin "
               "produces far less often; afterwards the rate is the fair-coin rate.  A transient can never be a "
               "shortcut for Problems 1-3, which are about the infinite tail.")
    txt = "\n".join(out)
    print(txt)
    open(os.path.join(HERE, "r14_early_sparse_output.txt"), "w").write(txt + "\n")


if __name__ == "__main__":
    main()
