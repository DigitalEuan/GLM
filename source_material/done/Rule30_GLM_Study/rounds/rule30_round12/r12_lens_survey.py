"""Round 12 (EMP, exact counts; statistics are descriptive, not proofs).

Reads the Rule 30 centre column (data/cc_1M.npy, 10^6 bits; its wobble D(10^6) = 1536 is the
Lean certificate `wobble_1e6`) through several lenses, and prints each read as a z-score
(value / its standard deviation for a fair i.i.d. coin).  A fair coin gives |z| <~ 3 for a single
read; with many reads, the largest |z| grows like sqrt(2 log(#reads)).

Lenses: plain wobble, strobe (clock) phases, echo (lag), words (blocks), Walsh window
characters, arrow (sign / zero crossings), Cesaro-smoothed wobble.
The same lenses are applied to a control: a Mersenne-twister coin (seed 12345).

Run: python3 r12_lens_survey.py [path/to/cc_1M.npy | cc_10M.bin from r12_centre_column.c]
"""
import sys, math, json
import numpy as np

path = sys.argv[1] if len(sys.argv) > 1 else "../data/cc_1M.npy"
cc = (np.load(path) if path.endswith(".npy") else np.fromfile(path, dtype=np.uint8)).astype(np.int8)
N = len(cc)
assert int(2 * cc[:1000000].sum() - 1000000) == 1536, "centre column does not match the Lean certificate"
rng = np.random.RandomState(12345)
ctrl = rng.randint(0, 2, N).astype(np.int8)


def lenses(a):
    w = 2 * a.astype(np.int64) - 1
    out = {}
    D = np.cumsum(w)
    out["plain wobble D(N)"] = (int(D[-1]), D[-1] / math.sqrt(N))
    # strobe phases p = 2..16 : wobble of a(p t + r), t < N // p
    zs, chis = [], {}
    for p in range(2, 17):
        M = N // p
        ph = w[: p * M].reshape(M, p).sum(axis=0)
        z = ph / math.sqrt(M)
        zs += list(z)
        chis[p] = float((z ** 2).sum())   # ~ chi^2 with p d.o.f.
    out["strobe max|z| (p<=16, 135 phases)"] = (None, float(np.max(np.abs(zs))))
    out["strobe chi2/dof worst p"] = (max(chis, key=lambda p: chis[p] / p),
                                      max(chis[p] / p for p in chis))
    # echo at lags 1..64
    ez = [float((w[:-k] * w[k:]).sum()) / math.sqrt(N - k) for k in range(1, 65)]
    out["echo max|z| (lags 1..64)"] = (int(np.argmax(np.abs(ez))) + 1, float(np.max(np.abs(ez))))
    # words of length k: chi^2 / dof
    for k in (4, 8, 12):
        code = np.zeros(N - k + 1, dtype=np.int64)
        for j in range(k):
            code = (code << 1) | a[j: N - k + 1 + j]
        cnt = np.bincount(code, minlength=2 ** k)
        E = (N - k + 1) / 2 ** k
        out[f"words k={k} chi2/dof"] = (None, float(((cnt - E) ** 2 / E).sum() / (2 ** k - 1)))
    # Walsh characters chi_S(t) = prod_{s in S} w(t+s), S nonempty subset of {0..9}
    k = 10
    best = (None, 0.0)
    for S in range(1, 2 ** k):
        prod = np.ones(N - k + 1, dtype=np.int64)
        for j in range(k):
            if S >> j & 1:
                prod = prod * w[j: N - k + 1 + j]
        z = prod.sum() / math.sqrt(N - k + 1)
        if abs(z) > abs(best[1]):
            best = (bin(S), float(z))
    out["Walsh max|z| (1023 window characters, width 10)"] = best
    # arrow: zero crossings, fraction of time D > 0
    zeros = int((D == 0).sum())
    out["arrow: returns to D=0"] = (zeros, zeros / math.sqrt(N))
    out["arrow: fraction of time D>0"] = (None, float((D > 0).mean()))
    # Cesaro-smoothed wobble
    out["Cesaro mean of D"] = (None, float(D.mean() / math.sqrt(N)))
    return out


res = {"centre": lenses(cc), "control": lenses(ctrl)}
print(f"N = {N}")
print(f"{'lens':52s} {'centre column':>24s} {'control coin':>24s}")
for key in res["centre"]:
    c, r = res["centre"][key], res["control"][key]
    f = lambda v: f"{str(v[0]) if v[0] is not None else '':>10s} {v[1]:>12.4f}"
    print(f"{key:52s} {f(c)} {f(r)}")
json.dump({k: {kk: [vv[0], vv[1]] for kk, vv in v.items()} for k, v in res.items()},
          open(f"r12_lens_survey_{N}.json", "w"), indent=1, default=str)
