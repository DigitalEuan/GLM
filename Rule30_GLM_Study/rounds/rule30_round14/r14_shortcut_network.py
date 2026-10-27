"""Round 14 (EMP): is the Rule 30 centre column 'jumping through lattice shortcuts'?

The GLM reads a bit string as a walk in its Golay/Leech network: 24-bit words are snapped to the
nearest Golay codeword (a point of the network; 2 x codeword is a Leech vector), and a transition
between two snapped words is a Leech step whose squared jump norm d^2 is the weight of the XOR of
the two codewords: d^2 in {0, 8, 12, 16, 24}, and d^2 = 8 is a minimal (kissing-sphere) hop.

Lenses (ways to put the column on the network):
  block      words c(24k .. 24k+23), one network point per 24 steps (bit i of the word = c(24k+i))
  block+gray the same words passed through the GLM's byte-wise Gray map before snapping
  slide      words c(t .. t+23), one network point per step (the de Bruijn 'straight path')

For each lens, the EXACT statistics a pattern-free (fair-coin) sequence would produce are computed
by enumerating all 2^24 / 2^25 / 2^26 windows.  Then the Rule 30 walk and six controls are compared
with those predictions.  Lean (ShortcutNetwork.lean) proves the two facts that make this the right
test: every lens walk is a sliding-block image of the column (so a pattern in the walk IS a pattern
of the column, and a never-repeating walk would prove Problem 1), and if the column is normal the
walk statistics are exactly these predictions.

Run:  python3 r14_shortcut_network.py [N]      (default N = 4194304 bits)
"""
import os, sys, time
import numpy as np
import golay_net as G
import sources
from stats import chi2_test, verdict

HERE = os.path.dirname(os.path.abspath(__file__))
NORMS = [0, 8, 12, 16, 24]
NIDX = {w: i for i, w in enumerate(NORMS)}
WT = G.pop(G.CODE)                       # weight of codeword with message m
NORM_OF_MSG = np.array([NIDX[w] for w in WT])


def gray_bytes(v):
    v = np.asarray(v, dtype=np.int64)
    out = np.zeros_like(v)
    for k in range(3):
        b = (v >> (8 * k)) & 255
        g = b ^ (b >> 1)
        r = np.zeros_like(g)
        for i in range(8):
            r |= ((g >> (7 - i)) & 1) << i
        out |= r << (8 * k)
    return out


def msg(v, lead):
    """network point (message index 0..4095) of a 24-bit word"""
    return G.decode(v, lead) & 4095


def wht(f):
    f = f.astype(np.float64).copy(); h = 1
    while h < len(f):
        f = f.reshape(-1, 2, h); a = f[:, 0, :].copy(); b = f[:, 1, :].copy()
        f[:, 0, :] = a + b; f[:, 1, :] = a - b; f = f.reshape(-1); h *= 2
    return f


def xconv(p, q):
    return wht(wht(p) * wht(q)) / len(p)


# --------------------------------------------------------------------------- predictions
def predictions(lead, tag):
    cache = os.path.join(HERE, f"pred_{tag}.npz")
    if os.path.exists(cache):
        return dict(np.load(cache))
    out = {}
    v = np.arange(1 << 24, dtype=np.int64)
    node = np.bincount(msg(v, lead), minlength=4096) / float(1 << 24)
    out["node"] = node
    # block lens: points are i.i.d. with law `node`
    hop = xconv(node, node); out["block_hop"] = hop
    out["block_norm"] = np.bincount(NORM_OF_MSG, weights=hop, minlength=5)
    ind = [(NORM_OF_MSG == i).astype(float) for i in range(5)]
    Nb = [xconv(node, ind[i]) for i in range(5)]           # Nb[i][b] = P(norm(a^b)=i)
    out["block_pair"] = np.array([[np.sum(node * Nb[i] * Nb[j]) for j in range(5)] for i in range(5)])
    out["block_back"] = np.array([np.sum(node ** 2)])
    # slide lens: enumerate 26-bit windows u; points X0, X1, X2 of words u>>0, u>>1, u>>2
    M = 1 << 24
    hop_s = np.zeros(4096); pair_s = np.zeros((5, 5)); back = 0.0
    for chunk in range(4):
        u = np.arange(chunk * M, (chunk + 1) * M, dtype=np.int64)
        x0 = msg(u & (M - 1), lead); x1 = msg((u >> 1) & (M - 1), lead); x2 = msg((u >> 2) & (M - 1), lead)
        h01 = x0 ^ x1; h12 = x1 ^ x2
        hop_s += np.bincount(h01, minlength=4096)
        pair_s += np.bincount(NORM_OF_MSG[h01] * 5 + NORM_OF_MSG[h12], minlength=25).reshape(5, 5)
        back += np.count_nonzero(x0 == x2)
    tot = float(4 * M)
    out["slide_hop"] = hop_s / tot
    out["slide_norm"] = np.bincount(NORM_OF_MSG, weights=out["slide_hop"], minlength=5)
    out["slide_pair"] = pair_s / tot
    out["slide_back"] = np.array([back / tot])
    np.savez(cache, **out)
    return out


# --------------------------------------------------------------------------- walks
def words(bits, stride):
    n = (len(bits) - 24) // stride + 1
    w = np.zeros(n, dtype=np.int64)
    for i in range(24):
        w |= bits[i: i + stride * (n - 1) + 1: stride].astype(np.int64) << i
    return w


def walk_stats(points):
    h = points[:-1] ^ points[1:]
    hn = NORM_OF_MSG[h]
    return dict(node=np.bincount(points, minlength=4096), hop=np.bincount(h, minlength=4096),
                norm=np.bincount(hn, minlength=5),
                pair=np.bincount(hn[:-1] * 5 + hn[1:], minlength=25),
                back=np.count_nonzero(points[:-2] == points[2:]), nback=len(points) - 2,
                distinct=len(np.unique(points)), distinct_hops=len(np.unique(h)))


def fmt_p(p):
    return f"{p:.3g}" if p >= 1e-300 else "<1e-300"


def test_stats(st, pred, lens):
    """the five test statistics of a walk: four chi-squares and the return-in-2 z-score"""
    out = []
    for obs, p in [(st["node"], pred["node"]), (st["hop"], pred[f"{lens}_hop"]),
                   (st["norm"], pred[f"{lens}_norm"]), (st["pair"], pred[f"{lens}_pair"].reshape(-1))]:
        out.append(chi2_test(obs, p))
    pb = pred[f"{lens}_back"][0]
    z = (st["back"] - pb * st["nback"]) / np.sqrt(pb * (1 - pb) * st["nback"])
    return out, z


LABELS = ["points", "hops", "norms", "pairs", "return2"]


def report(name, st, pred, lens, lines, null):
    """null: list of (chi-square stats, z) from independent fair-coin reference walks of the same
    length.  Each statistic is turned into a z-score against the reference walks' mean and spread;
    this accounts for the clustering of rare events in overlapping windows, which makes textbook
    chi-square / binomial p-values too optimistic."""
    chis, z = test_stats(st, pred, lens)
    vals = [c[0] for c in chis] + [z]
    zs = []
    for i in range(5):
        ref = np.array([nl[0][i][0] for nl in null] if i < 4 else [nl[1] for nl in null])
        zs.append((vals[i] - ref.mean()) / (ref.std(ddof=1) + 1e-12))
    pb = pred[f"{lens}_back"][0]
    normfreq = st["norm"] / st["norm"].sum()
    worst = max(abs(x) for x in zs)
    flag = "PATTERN DETECTED" if worst > 5 else "consistent with the no-pattern prediction"
    lines.append(f"  {name:8s} | " + " ".join(f"z({l})={x:+8.1f}" for l, x in zip(LABELS, zs))
                 + f" | return-in-2 {st['back'] / st['nback']:.5f} (pred {pb:.5f}) | points {st['distinct']}, "
                 f"hop vectors {st['distinct_hops']} | d2 mix " + " ".join(f"{x:.3f}" for x in normfreq)
                 + f" | {flag}")


def null_walks(N, lens_fn, pred, lens, K, base):
    return [test_stats(walk_stats(lens_fn(sources.prng(N, seed=base + k))), pred, lens) for k in range(K)]


def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 4194304
    t0 = time.time()
    lead = G.leaders()
    lines = [f"Round 14 shortcut-network study, N = {N} bits per sequence", ""]
    pred = predictions(lead, "min")
    lines.append("EXACT predictions for a pattern-free (fair-coin) sequence (enumeration of all windows):")
    lines.append("  block lens  d2 mix " + " ".join(f"{x:.5f}" for x in pred["block_norm"])
                 + f" ; return-in-2 {pred['block_back'][0]:.6f}")
    lines.append("  slide lens  d2 mix " + " ".join(f"{x:.5f}" for x in pred["slide_norm"])
                 + f" ; return-in-2 {pred['slide_back'][0]:.6f}")
    lines.append(f"  most likely network point has probability {pred['node'].max():.6f} "
                 f"(uniform would be {1/4096:.6f}); least likely {pred['node'].min():.6f}")
    lines.append("")
    data = {k: f(N) for k, f in sources.ALL.items()}
    K = int(os.environ.get("R14_NULL", "40"))
    lenses = [("block", 24, None), ("block", 24, "gray"), ("slide", 1, None)]
    for li, (lens, stride, enc) in enumerate(lenses):
        def lens_fn(bits, stride=stride, enc=enc):
            w = words(bits, stride)
            return msg(gray_bytes(w) if enc else w, lead)
        title = lens + ("+gray (GLM byte-wise Gray map before snapping)" if enc else "")
        lines.append(f"Lens: {title}   (z-scores against {K} independent fair-coin reference walks)")
        null = null_walks(N, lens_fn, pred, lens, K, 10_000 + 1000 * li)
        for name, bits in data.items():
            report(name, walk_stats(lens_fn(bits)), pred, lens, lines, null)
        lines.append("")
    glm = G.glm_leaders()
    pg = predictions(glm, "glm")
    lines.append("Tie-break check: the GLM's own coset-leader table (Decoder.lean) instead of min-value leaders")
    for lens, stride in [("block", 24), ("slide", 1)]:
        def lens_fn(bits, stride=stride):
            return msg(words(bits, stride), glm)
        null = null_walks(N, lens_fn, pg, lens, K, 20_000 + 1000 * stride)
        lines.append(f" lens {lens}:")
        for name in ("rule30", "prng", "sqrt2", "lfsr31"):
            report(name, walk_stats(lens_fn(data[name])), pg, lens, lines, null)
    lines.append("")
    S = 16; seg = N // S
    def seg_counts(bits):
        x = msg(words(bits, 1), lead); ev = (x[:-2] == x[2:])
        return np.array([np.count_nonzero(ev[i * seg:(i + 1) * seg]) for i in range(S)])
    r = seg_counts(data["rule30"])
    q = np.concatenate([seg_counts(sources.prng(N, seed=30_000 + k)) for k in range(64)])
    lines.append(f"Slide lens, return-in-2 events in {S} consecutive segments of {seg} steps:")
    lines.append("  rule30: " + " ".join(map(str, r)))
    lines.append("  rule30 z-scores: " + " ".join(f"{(x - q.mean()) / q.std():+.1f}" for x in r))
    lines.append(f"  fair-coin reference segments: mean {q.mean():.1f}, sd {q.std():.1f}, min {q.min()}, max {q.max()} "
                 f"(over {len(q)} segments); reference segments >= rule30's first segment: "
                 f"{np.count_nonzero(q >= r[0])} of {len(q)}")
    rest = data["rule30"][seg:]
    lines.append(f"  out-of-sample: rule30 after the first segment has return-in-2 rate "
                 f"{r[1:].sum() / (N - seg):.6f} vs the exact prediction {pred['slide_back'][0]:.6f}")
    lines.append("")
    lines.append("(statistics: chi-square of points / hop vectors / hop norms / consecutive norm pairs against "
                 "the exact prediction, and the return-in-2 rate; each converted to a z-score against the "
                 f"reference walks; 'PATTERN DETECTED' if some |z| > 5.  elapsed {time.time() - t0:.0f}s)")
    txt = "\n".join(lines)
    print(txt)
    with open(os.path.join(HERE, "r14_shortcut_network_output.txt"), "w") as f:
        f.write(txt + "\n")


if __name__ == "__main__":
    main()
