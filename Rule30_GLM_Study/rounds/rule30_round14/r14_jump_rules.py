"""Round 14 (EMP + certificate generation): does the centre column follow JUMP rules?

A jump rule (a 'shortcut path' through the column's own past) predicts bit t from the bits at a
few earlier positions t - j1, ..., t - jk ('taps', which may jump far back):

    c(t) = f(c(t - j1), ..., c(t - jk)).

Lean (ShortcutNetwork.lean) proves:  Problem 1  <=>  no jump rule (any taps, any f) and equally
no LINEAR jump rule (f = XOR of the taps) holds from some time on.  So 'the path takes a hidden
shortcut forever' is exactly the negation of Problem 1; and under the Seed Typicality target every
jump rule is right exactly half of the time in the long run.

This script measures, for the Rule 30 centre column and the controls of sources.py:
  J1  linear complexity profile (Berlekamp-Massey): the shortest linear jump rule that reproduces
      the first n bits.  A pattern-free sequence has L(n) ~ n/2; a hidden linear shortcut shows up
      as L(n) stopping (lfsr31 stops at 31).
  J2  the best k-tap jump rule over 2^20 bits (all tap sets in 1..J, best f for each): its
      accuracy, against the same search on a fair-coin sequence (which has the same selection
      effect).
  J3  local shortcuts: the column might use DIFFERENT shortcuts in different places ('jumping
      between shortcut paths').  For each 256-bit segment, the best 2-tap rule's accuracy and the
      segment's own linear complexity, compared with fair-coin segments.
  J4  writes the infeasibility certificate checked in Lean (ShortcutNetworkData.lean): no linear
      jump rule with taps in 1..L reproduces c(L) .. c(n-1).
"""
import itertools, os, sys, time
import numpy as np
import sources

HERE = os.path.dirname(os.path.abspath(__file__))


def berlekamp_massey_profile(bits):
    """linear complexity profile L(1..n) over GF(2); polynomials as Python ints (bit i = x^i)"""
    n = len(bits)
    s = 0  # reversed history: bit i of s = bits[t - i]
    C, B = 1, 1
    L, m = 0, 1
    prof = np.zeros(n, dtype=np.int64)
    for t in range(n):
        s = (s << 1) | int(bits[t])
        # discrepancy d = sum_{i=0..L} C_i * bits[t-i]
        d = bin(C & s).count("1") & 1
        if d == 0:
            m += 1
        elif 2 * L <= t:
            T = C
            C ^= B << m
            L, B, m = t + 1 - L, T, 1
        else:
            C ^= B << m
            m += 1
        prof[t] = L
    return prof


def best_tap_rules(bits, k, J):
    """for every tap set of size k in 1..J: accuracy of the best f (majority per context)"""
    n = len(bits); b = bits.astype(np.int64)
    best = (0.0, None)
    accs = []
    for taps in itertools.combinations(range(1, J + 1), k):
        ctx = np.zeros(n - J, dtype=np.int64)
        for i, j in enumerate(taps):
            ctx |= b[J - j: n - j] << i
        y = b[J:]
        ones = np.bincount(ctx, weights=y, minlength=1 << k)
        tot = np.bincount(ctx, minlength=1 << k)
        acc = np.maximum(ones, tot - ones).sum() / (n - J)
        accs.append(acc)
        if acc > best[0]:
            best = (acc, taps)
    return best, np.array(accs)


def segment_stats(bits, seg=256, J=16):
    nseg = len(bits) // seg
    best2 = np.zeros(nseg); lc = np.zeros(nseg, dtype=np.int64)
    taps = list(itertools.combinations(range(1, J + 1), 2))
    for s in range(nseg):
        x = bits[s * seg:(s + 1) * seg].astype(np.int64)
        y = x[J:]
        bacc = 0
        for (j1, j2) in taps:
            ctx = x[J - j1: seg - j1] | (x[J - j2: seg - j2] << 1)
            ones = np.bincount(ctx, weights=y, minlength=4); tot = np.bincount(ctx, minlength=4)
            bacc = max(bacc, np.maximum(ones, tot - ones).sum())
        best2[s] = bacc / (seg - J)
        lc[s] = berlekamp_massey_profile(x)[-1]
    return best2, lc


def gf2_certificate(bits, L, n):
    """find T subset of [L, n) with  XOR_{t in T} row_t = 0  and  XOR_{t in T} c(t) = 1,
    row_t = (c(t-1), ..., c(t-L)).  Returns sorted T or None (then a rule of order <= L exists)."""
    rows = []
    for t in range(L, n):
        r = 0
        for j in range(1, L + 1):
            r |= int(bits[t - j]) << (j - 1)
        rows.append((r, int(bits[t]), 1 << (t - L)))
    # Gaussian elimination keeping track of combinations
    pivots = {}
    for r, rhs, comb in rows:
        while r:
            hb = r.bit_length() - 1
            if hb in pivots:
                pr, prhs, pcomb = pivots[hb]
                r ^= pr; rhs ^= prhs; comb ^= pcomb
            else:
                pivots[hb] = (r, rhs, comb)
                break
        if r == 0 and rhs == 1:
            return sorted(L + i for i in range(comb.bit_length()) if (comb >> i) & 1)
    return None


def main():
    t0 = time.time()
    out = ["Round 14 jump-rule ('shortcut path') study", ""]
    NBM = 20000
    data = {k: f(1 << 20) for k, f in sources.ALL.items()}
    out.append(f"J1  linear complexity profile L(n), n <= {NBM} (pattern-free: L(n) ~ n/2)")
    for name, bits in data.items():
        prof = berlekamp_massey_profile(bits[:NBM])
        dev = prof - (np.arange(1, NBM + 1) + 1) // 2
        cps = [100, 1000, 5000, 10000, 20000]
        out.append(f"  {name:8s} L(n) at n={cps}: {[int(prof[c - 1]) for c in cps]}; "
                   f"max |L(n) - n/2| = {int(np.abs(dev).max())}")
    out.append("")
    out.append("J2  best k-tap jump rule on 2^20 bits (accuracy 0.5 = no better than a coin)")
    for k, J in [(1, 64), (2, 48), (3, 32), (4, 20)]:
        for name in data:
            (acc, taps), accs = best_tap_rules(data[name], k, J)
            out.append(f"  k={k} taps in 1..{J:2d}  {name:8s} best accuracy {acc:.5f} taps {taps} "
                       f"(over {len(accs)} tap sets; median {np.median(accs):.5f})")
        out.append("")
    out.append("J3  local shortcuts: per 256-bit segment, best 2-tap rule (taps in 1..16) and local linear "
               "complexity (4096 segments each)")
    seg_res = {}
    for name in ("rule30", "prng", "sqrt2", "lfsr31"):
        b2, lc = segment_stats(data[name])
        seg_res[name] = (b2, lc)
        out.append(f"  {name:8s} best-2-tap accuracy: mean {b2.mean():.4f}, 99th pct {np.percentile(b2, 99):.4f}, "
                   f"max {b2.max():.4f} | local linear complexity: mean {lc.mean():.2f}, min {lc.min()}, "
                   f"max {lc.max()}  (fair coin: mean ~128)")
    r_b2, r_lc = seg_res["rule30"]; p_b2, p_lc = seg_res["prng"]
    # two-sample comparison by a permutation-free z on the means
    z1 = (r_b2.mean() - p_b2.mean()) / np.sqrt(r_b2.var() / len(r_b2) + p_b2.var() / len(p_b2))
    z2 = (r_lc.mean() - p_lc.mean()) / np.sqrt(r_lc.var() / len(r_lc) + p_lc.var() / len(p_lc))
    out.append(f"  rule30 vs prng: z(best-2-tap mean) = {z1:+.2f}, z(local LC mean) = {z2:+.2f}")
    out.append("")
    L, n = 128, 257
    T = gf2_certificate(data["rule30"], L, n)
    out.append(f"J4  certificate: no linear jump rule with taps in 1..{L} reproduces c({L})..c({n - 1}): "
               f"combination of {len(T)} equations, T = {T}")
    with open(os.path.join(HERE, "r14_linear_certificate.txt"), "w") as f:
        f.write(f"{L} {n}\n" + " ".join(map(str, T)) + "\n")
    out.append("")
    out.append(f"(elapsed {time.time() - t0:.0f}s)")
    txt = "\n".join(out)
    print(txt)
    with open(os.path.join(HERE, "r14_jump_rules_output.txt"), "w") as f:
        f.write(txt + "\n")


if __name__ == "__main__":
    main()
