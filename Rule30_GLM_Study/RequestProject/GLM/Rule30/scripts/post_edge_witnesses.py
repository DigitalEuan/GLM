#!/usr/bin/env python3
"""Round 27 (EMP, outside Lean): Experiment A -- post-edge witnesses and plateaus.

For the period-2 drive words `10` (word 1, black at even times) and `01` (word 2) and every code
length d <= DMAX this records

  * the longest life Lmax(d) (first failure time) and ALL codes achieving it;
  * for each such witness: the state at the edge (time d - 1), the death time, and every inner
    column c - k that follows an alternating drive for >= MINSTRETCH consecutive steps, with the
    inner code behind it at the start of the stretch and that inner code's own life under the
    matching word (by `inner_alternation_bound` the stretch cannot outlast it);
  * inner codes shared between witnesses of different lengths (the sound form of
    "a wide survivor reduces to a narrower one");
  * the population of alive codes of length d from the edge to extinction, its plateaus (maximal
    runs of black-time tests that kill nobody) and the event that ends each plateau.

Codes are written as integers (bit i = cell c - 1 - i) and as strings, cell c - 1 first.
The Lean side checks Lmax(d) for d <= 32 (`ProofRoutesData.lmaxTwo_spec`) and one shared inner
survivor (`ProofRoutesData.shared_inner_survivor`).

Usage: python3 post_edge_witnesses.py [DMAX] [MINSTRETCH]   (defaults 22, 10)
"""
import sys

def step(b, S): return (S >> 1) ^ (S | ((S << 1) | b))
def drive(w): return lambda t: (w >> (t % 2)) & 1
def life(S, bd, cap=10**5):
    t = 0
    while t < cap:
        if bd(t) and (S & 1) == bd(t + 1): return t
        S = step(bd(t), S); t += 1
    return None
def s(X, n=None):
    n = X.bit_length() if n is None else n
    return ''.join('1' if (X >> i) & 1 else '0' for i in range(n))

def edge_survivors(d, bd):
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

def trajectory(S, bd, L):
    tr = []; X = S
    for t in range(L + 2): tr.append(X); X = step(bd(t), X)
    return tr

def stretches(tr, minlen):
    """inner columns c-k (bit k-1) following an alternating drive; (k, word, start, end)"""
    res = []
    for j in range(tr[-1].bit_length()):
        for w in (1, 2):
            run = 0; start = 0
            for t, X in enumerate(tr + [None]):
                ok = X is not None and ((X >> j) & 1) == ((w >> (t % 2)) & 1)
                if ok:
                    if run == 0: start = t
                    run += 1
                else:
                    if run >= minlen: res.append((j + 1, w, start, start + run - 1))
                    run = 0
    return res

def main():
    DMAX = int(sys.argv[1]) if len(sys.argv) > 1 else 22
    MIN = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    shared = {}
    for w in (1, 2):
        bd = drive(w)
        print(f"=== drive word {'10' if w == 1 else '01'} (driveN 2 {w}) ===")
        for d in range(1, DMAX + 1):
            alive = edge_survivors(d, bd)
            lives = {S: life(S, bd) for S in alive}
            L = max(lives.values()) if lives else None
            W = [S for S in alive if lives[S] == L]
            print(f"\nd={d} Lmax={L} excess={L - d + 1 if L is not None else None} "
                  f"alive_at_edge={len(alive)} witnesses={len(W)}")
            # population after the edge
            pop = []
            for t in range(d - 1, (L or 0) + 2):
                pop.append((t, sum(1 for S in alive if lives[S] >= t)))
            plateaus = []; t0 = None
            for (t, n), (t2, n2) in zip(pop, pop[1:]):
                if bd(t) and n > 0:          # a test at time t
                    if n2 == n:
                        if t0 is None: t0 = t
                    else:
                        if t0 is not None:
                            plateaus.append((t0, t, n, n - n2))
                        t0 = None
            print("  population (t: alive):", ' '.join(f"{t}:{n}" for t, n in pop))
            print("  plateaus (first test, ending test, alive, killed at the end):", plateaus)
            for S in W:
                tr = trajectory(S, bd, L)
                st = stretches(tr, MIN)
                info = []
                for (k, ww, a, b) in st:
                    if k < 2: continue
                    inner = tr[a] >> k
                    shift = drive(ww if a % 2 == 0 else 3 - ww)
                    il = life(inner, shift) if inner > 0 else None
                    info.append(f"k={k} word={ww} t={a}..{b} inner={inner}(len {inner.bit_length()}) inner_life={il}")
                    shared.setdefault((inner, ww if a % 2 == 0 else 3 - ww), set()).add((w, d, S))
                print(f"  witness S={S} cells={s(S, d)} edge_state={s(tr[d - 1], 2 * d - 1)} death={L}")
                for x in info: print("     inner column:", x)
    print("\n=== inner codes shared by witnesses of different lengths ===")
    for (inner, ww), occ in sorted(shared.items()):
        ds = sorted({d for (_, d, _) in occ})
        if len(ds) > 1:
            print(f"inner code {inner} (cells {s(inner)}) under word {ww}: in witnesses (word, d, S) {sorted(occ)}")

if __name__ == "__main__":
    main()
