#!/usr/bin/env python3
"""Round 27 (EMP, outside Lean): Experiment B -- a declared family of progress measures.

For the period-2 drive word `10` (black at even times) and every potential P in the declared
family below, search for the smallest counterexample to

    "the machine survives the c steps after time t (t >= d - 1, after the edge)
     ==> P(state(t + c), t + c) < P(state(t), t)"

for c = 1..20, over codes of length d = 1, 2, ... (in that order, then by code, then by t).
The potentials match the Lean definitions `rankPot i` in `ProofRoutesData.lean`; the witnesses
printed at the end are the table `rankWitness` there, checked by `native_decide`.

Usage: python3 progress_measures.py [DMAX]   (default 30)
"""
import sys

def step(b, S): return (S >> 1) ^ (S | ((S << 1) | b))
def bd(t): return 1 if t % 2 == 0 else 0          # driveN 2 1
def life(S, cap=10**5):
    t = 0
    while t < cap:
        if bd(t) and (S & 1) == bd(t + 1): return t
        S = step(bd(t), S); t += 1
    return None

def size(X): return X.bit_length()
def pop(X): return bin(X).count('1')
def first(p, n):
    for i in range(n):
        if p(i): return i
    return n
POTS = [
    ("width",          lambda X, t: size(X)),
    ("popcount",       lambda X, t: pop(X)),
    ("transitions",    lambda X, t: pop(X ^ (X >> 1))),
    ("trailingOnes",   lambda X, t: first(lambda i: not (X >> i) & 1, size(X) + 1)),
    ("firstWhitePair", lambda X, t: first(lambda i: not (X >> i) & 1 and not (X >> (i + 1)) & 1, size(X) + 1)),
    ("whiteCells",     lambda X, t: size(X) - pop(X)),
    ("lowWindowPop",   lambda X, t: pop(X % (1 << max(size(X) - t, 0)))),
    ("altBlock",       lambda X, t: first(lambda n: n >= 1 and ((X >> n) & 1) == ((X >> (n - 1)) & 1), size(X) + 2)),
]

def edge_survivors(d):
    """codes of length d alive at the edge, by the sound prefix search"""
    out = []
    def pf(P, k):
        X = P
        for t in range(k):
            if bd(t) and (X & 1) == bd(t + 1): return True
            X = step(bd(t), X)
        return False
    def dfs(k, P):
        if pf(P, k): return
        if k == d - 1:
            out.append(P | (1 << k)); return
        dfs(k + 1, P); dfs(k + 1, P | (1 << k))
    dfs(0, 0)
    return sorted(out)

def main():
    DMAX = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    C = 20
    wit = {i: {} for i in range(len(POTS))}
    for d in range(1, DMAX + 1):
        for S in edge_survivors(d):
            L = life(S)
            tr = []; X = S
            for t in range(L + 1): tr.append(X); X = step(bd(t), X)
            for t in range(d - 1, L + 1):
                for c in range(1, C + 1):
                    if t + c > L: break
                    for i, (_, P) in enumerate(POTS):
                        if c not in wit[i] and P(tr[t + c], t + c) >= P(tr[t], t):
                            wit[i][c] = (d, S, t)
        if all(len(wit[i]) == C for i in wit): break
    for i, (name, _) in enumerate(POTS):
        miss = [c for c in range(1, C + 1) if c not in wit[i]]
        print(f"{i} {name:15s} refuted for every c in 1..{C}" if not miss else
              f"{i} {name:15s} NOT refuted for c = {miss}")
        print("   smallest counterexamples (c: d, S, t):",
              ", ".join(f"{c}:{wit[i][c]}" for c in sorted(wit[i])))
    print("\nLean table (pot, c, d, S, t):")
    print("[" + ",\n ".join(f"({i}, {c}, {w[0]}, {w[1]}, {w[2]})"
                           for i in wit for c, w in sorted(wit[i].items())) + "]")

if __name__ == "__main__":
    main()
