import subprocess, sys, random
def series(seed, w, W=None, T=None):
    W = W or w + 10; T = T or int(1.6 * w) + 2000
    out = subprocess.run(["./probe", str(W), str(T), seed] + [str(d) for d in range(w - 3, w + 2)],
                         capture_output=True, text=True).stdout.split("\n")
    return {int(l.split()[0]): l.split()[1] for l in out if l}
def settle(s, Q=64):
    T = len(s)
    for t in range(T - Q - 1, -1, -1):
        if s[t] != s[t + Q]: return t + 1
    return 0
random.seed(3)
seeds = ["1", format(random.getrandbits(999) | 1, "x"), format(random.getrandbits(39) | 1, "x")]
for w in map(int, sys.argv[1:]):
    for sd in seeds:
        S = series(sd, w)
        sw = S[w]
        last = max(i for i, c in enumerate(sw) if c == "1")
        taus = {d: settle(S[d]) for d in S}
        a = S[w - 1]
        print(f"w={w} seed={sd[:6]}.. lastblack(w)={last} mod16={last%16} a(last)={a[last]} "
              f"d(last+1)={S[w+1][last+1]} taus={taus}")
