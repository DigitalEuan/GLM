"""Round 16 (EMP): what is the early-time excess of near-constant 24-bit windows (Round 14)?

Round 14 counted 24-bit windows of the Rule 30 centre column with <= 3 black (or <= 3 white) cells:
125 in the first 2^17 steps against a fair-coin mean of 36.4.  Overlapping windows are not
independent: one long almost-white stretch produces many windows.  Here the windows are grouped
into *clusters* (maximal runs of consecutive qualifying window positions) and three statistics are
compared with 2000 fair-coin sequences per segment:
  W = number of qualifying windows (Round 14's statistic),
  C = number of clusters (independent events),
  M = length of the longest cluster.
Input: the centre column as /tmp/centre4M.npy (written from r15_columns output).
"""
import numpy as np

L, K = 24, 3
SEG = 2 ** 17


def stats(b):
    c = np.concatenate([[0], np.cumsum(b, dtype=np.int64)])
    w = c[L:] - c[:-L]
    q = (w <= K) | (w >= L - K)
    W = int(q.sum())
    if W == 0:
        return W, 0, 0, []
    d = np.diff(np.concatenate([[0], q.astype(np.int8), [0]]))
    starts, ends = np.where(d == 1)[0], np.where(d == -1)[0]
    lens = ends - starts
    return W, len(lens), int(lens.max()), list(zip(starts.tolist(), lens.tolist()))


def main():
    r = np.load("/tmp/centre4M.npy")
    rng = np.random.default_rng(16)
    null = np.array([stats(rng.integers(0, 2, SEG, dtype=np.uint8))[:3] for _ in range(2000)])
    mu, sd = null.mean(0), null.std(0)
    print(f"fair-coin null per segment of {SEG}: W mean {mu[0]:.1f} sd {sd[0]:.1f};"
          f" C mean {mu[1]:.2f} sd {sd[1]:.2f}; M mean {mu[2]:.1f} sd {sd[2]:.1f}")
    print(f"null 99.9th percentiles: W {np.percentile(null[:,0],99.9):.0f}, C {np.percentile(null[:,1],99.9):.0f},"
          f" M {np.percentile(null[:,2],99.9):.0f}")
    print()
    print("segment   W     C     M    zW     zC     zM")
    for i in range(len(r) // SEG):
        W, C, M, cl = stats(r[i * SEG:(i + 1) * SEG])
        print(f"{i:3d}  {W:5d} {C:5d} {M:5d}  {(W-mu[0])/sd[0]:+5.1f}  {(C-mu[1])/sd[1]:+5.1f}  {(M-mu[2])/sd[2]:+5.1f}")
    print()
    W, C, M, cl = stats(r[:SEG])
    print("segment 0 clusters (start position, number of qualifying windows):")
    print(sorted(cl, key=lambda x: -x[1])[:15])
    top = sorted(cl, key=lambda x: -x[1])[:3]
    for s, n in top:
        seg = r[s:s + n + L - 1]
        print(f"  stretch at t={s}: length {len(seg)}, black cells {int(seg.sum())}")
    # rank of segment-0 within each statistic, finer: first 2^14, 2^15, 2^16
    print()
    for n in (2 ** 14, 2 ** 15, 2 ** 16, 2 ** 17):
        W, C, M, _ = stats(r[:n])
        print(f"first {n:6d}: W {W:4d}  C {C:3d}  M {M:3d}  (fair-coin expectation of W ~ {n*mu[0]/SEG:.1f},"
              f" of C ~ {n*mu[1]/SEG:.2f})")


if __name__ == "__main__":
    main()
