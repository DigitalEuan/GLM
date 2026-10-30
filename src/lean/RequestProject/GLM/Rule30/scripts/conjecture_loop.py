#!/usr/bin/env python3
"""Round 26 (EMP): the GLM conjecture loop -- propose candidate lemmas, test, narrow, loop.

Purpose
    Run the propose / test / narrow / loop cycle of `ConjectureLoop.lean` on three candidate
    families taken from the To Do list (AUDIT.md section 4), for several rounds with rising test
    levels.  Candidates are *statements* (Lean `Prop`s of the package), each the conjunction of
    finitely checkable instances, so a single failing instance refutes it and survival is only
    evidence up to the tested level.

    Proposal operators (each new candidate records where it came from):
      SEED      the targets already on the To Do list;
      ANALOGY   transport of a proved source theorem to a new object ("same shape, other object"):
                  constDrive_dies (period 1: dies by d + 2)          -> HalfLineLinear p 1 2
                  survivors_card (pre-edge: each black time halves)  -> WindowHalving after the edge
                  random binary sequence (longest echo ~ 2 log2 n)   -> EchoLogBound 2 b
                  Rule 86 counting law (exact for all T)             -> the same law for Rule 30
      NARROW    move along a graded family to the frontier (least parameters still standing)
                and probe just below it, so that the next round can refute or confirm it;
      JUNCTION  candidates that the current data cannot separate (same tight points: the data
                touches their bounds at the same places) form a junction; the loop proposes their
                MEET (both bounds at once), a sharper statement with the same support;
      REPAIR    when a candidate is refuted, propose the weakest natural repair of the refuted
                shape (the window form of halving -> the amortised form).

    Families (Lean names in brackets):
      ECHO(a, b)        excess(n) = longest echo <= a*log2(n) + b      [EchoLogBound a b]
                        implies Problem 1                               [problem1_of_echoLogBound]
      LIN(p, a, b)      every half-line of length d dies by a*d + b     [HalfLineLinear p a b]
                        implies HalfLineDies p                          [halfLineDies_of_linear]
      WIN(p, m, 1/2)    every m-step window after the edge halves        [WindowHalving p m 1 2]
      AMORT(p, c, e)    alive(d-1+m) * 2^(m // c) <= 2^(d-1+e)            [AmortizedHalving p c e]
                        implies HalfLineDies p                          [halfLineDies_of_amortized]

Usage
    python3 conjecture_loop.py > conjecture_loop_output.txt      (about one minute; needs numpy)

Everything printed here is EMP.  The certified statements (Lean, native_decide) are in
`ConjectureLoopData.lean`; this script only chooses what to certify.
"""

import sys
import numpy as np

# ----------------------------------------------------------------------------------------------
# data: the centre column and its echo profile
# ----------------------------------------------------------------------------------------------

def centre_column(N):
    row, out = 1, []
    # cell i of the row is bit (i + N) of `row`; the centre is bit N
    row <<= N + 2
    c = N + 2
    for _ in range(N):
        out.append((row >> c) & 1)
        L = row << 1
        R = row >> 1
        row = L ^ (row | R)
    return out


def echo_profile(s):
    """ex[n] = length of the longest suffix of s[:n] that occurred earlier (suffix automaton);
    also returns, for each n, one period p realising it (the distance to an earlier occurrence)."""
    n = len(s)
    size = 2 * n + 2
    length = [0] * size
    link = [-1] * size
    nxt = [[-1, -1] for _ in range(size)]
    first_end = [0] * size        # end position of the first occurrence of the state's strings
    sz, last = 1, 0
    ex = [0] * (n + 1)
    per = [0] * (n + 1)
    for i, c in enumerate(s):
        cur = sz; sz += 1
        length[cur] = length[last] + 1
        first_end[cur] = i
        p = last
        while p != -1 and nxt[p][c] == -1:
            nxt[p][c] = cur
            p = link[p]
        if p == -1:
            link[cur] = 0
        else:
            q = nxt[p][c]
            if length[p] + 1 == length[q]:
                link[cur] = q
            else:
                cl = sz; sz += 1
                length[cl] = length[p] + 1
                nxt[cl] = nxt[q][:]
                link[cl] = link[q]
                first_end[cl] = first_end[q]
                while p != -1 and nxt[p][c] == q:
                    nxt[p][c] = cl
                    p = link[p]
                link[q] = cl
                link[cur] = cl
        last = cur
        e = length[link[cur]]
        ex[i + 1] = e
        per[i + 1] = i - first_end[link[cur]] if e > 0 else 0
    return ex, per


def log2(n):
    return n.bit_length() - 1 if n > 0 else 0

# ----------------------------------------------------------------------------------------------
# data: the half-line machine
# ----------------------------------------------------------------------------------------------

def alive_profile(p, word, d, K):
    """prof[t] = number of codes of length exactly d with no failed check before time t."""
    S = np.arange(1 << (d - 1), 1 << d, dtype=object if d > 62 else np.uint64)
    s = S.copy()
    alive = np.ones(len(S), dtype=bool)
    prof = []
    one = np.uint64(1)
    for t in range(K):
        prof.append(int(alive.sum()))
        b = (word >> (t % p)) & 1
        b1 = (word >> ((t + 1) % p)) & 1
        if b:
            alive &= ((s & one) != np.uint64(b1))
        s = (s >> one) ^ (s | ((s << one) | np.uint64(b)))
    prof.append(int(alive.sum()))
    return prof


PROF = {}

def prof(p, k, d):
    key = (p, k, d)
    if key not in PROF:
        PROF[key] = alive_profile(p, k, d, 4 * d + 40)
    return PROF[key]

# ----------------------------------------------------------------------------------------------
# candidates
# ----------------------------------------------------------------------------------------------

class Cand:
    def __init__(self, family, params, origin, implies=None):
        self.family, self.params, self.origin, self.implies = family, params, origin, implies
        self.status, self.witness, self.tight = "alive", None, None

    @property
    def name(self):
        return f"{self.family}{self.params}"

    def __repr__(self):
        return self.name


def test_echo(c, N, ex, per):
    a, b = c.params
    worst, tight = None, []
    for n in range(1, N + 1):
        margin = a * log2(n) + b - ex[n]
        if margin < 0:
            return False, f"n={n}: echo of length {ex[n]} (period {per[n]}) > {a}*{log2(n)}+{b}"
        if worst is None or margin < worst:
            worst, tight = margin, [n]
        elif margin == worst:
            tight.append(n)
    c.tight = (worst, frozenset(tight))
    return True, None


def wd(k, p):
    return ''.join(str((k >> i) & 1) for i in range(p))


def words(p):
    return range(1, 2 ** p)


def test_lin(c, D):
    p, a, b = c.params
    for d in range(1, D + 1):
        for k in words(p):
            pr = prof(p, k, d)
            T = a * d + b
            if T < len(pr) and pr[T] > 0:
                return False, f"word {wd(k, p)}, d={d}: {pr[T]} code(s) alive at time {T}"
            if T >= len(pr) and pr[-1] > 0:
                return False, f"word {wd(k, p)}, d={d}: alive beyond the simulated range"
    return True, None


def test_win(c, D):
    p, m, num, den = c.params
    for d in range(1, D + 1):
        for k in words(p):
            pr = prof(p, k, d)
            for t in range(d - 1, len(pr) - m):
                if den * pr[t + m] > num * pr[t]:
                    return False, (f"word {wd(k, p)}, d={d}: {pr[t]} alive at t={t}, still {pr[t + m]} "
                                   f"at t+{m} (plateau)")
    return True, None


def test_amort(c, D):
    p, cc, e = c.params
    worst = None
    for d in range(1, D + 1):
        for k in words(p):
            pr = prof(p, k, d)
            for m in range(0, len(pr) - d + 1):
                lhs = pr[d - 1 + m] * 2 ** (m // cc)
                if lhs > 2 ** (d - 1 + e):
                    return False, f"word {wd(k, p)}, d={d}, m={m}: {pr[d - 1 + m]} alive, bound exceeded"
    return True, None

# ----------------------------------------------------------------------------------------------
# the loop
# ----------------------------------------------------------------------------------------------

def main():
    NMAX = 131072
    s = centre_column(NMAX)
    ex, per = echo_profile(s)
    print("Round 26 conjecture loop (EMP).  Data: centre column to n = %d, half-line machine "
          "for periods 2, 3, all words." % NMAX)
    print()

    pool = []
    seen = set()

    def propose(c):
        if c.name in seen:
            return
        seen.add(c.name)
        pool.append(c)
        print(f"    + propose {c.name:24s} [{c.origin}]")

    echo_levels = [100, 1000, 10000, 131072]
    half_levels = [8, 11, 14, 17]

    print("Round 0: seeds and analogies")
    propose(Cand("ECHO", (2, 2), "SEED: TuneExcessLog (Round 25)", "problem1_of_echoLogBound"))
    propose(Cand("WIN", (2, 4, 1, 2), "SEED: To Do 1/10 'post-edge halving'"))
    propose(Cand("WIN", (3, 6, 1, 2), "SEED: To Do 1/10 'post-edge halving'"))
    for b in (0, 4, 8):
        propose(Cand("ECHO", (2, b), "ANALOGY: random sequence, longest echo ~ 2 log2 n",
                     "problem1_of_echoLogBound"))
    for b in (16, 24):
        propose(Cand("ECHO", (0, b), "ANALOGY: Round 25 max excess 16 for n <= 1000",
                     "problem1_of_echoLogBound"))
    propose(Cand("ECHO", (3, 0), "NARROW: steeper than the random-sequence slope",
                 "problem1_of_echoLogBound"))
    propose(Cand("ECHO", (1, 8), "NARROW: between the constant and the slope-2 forms",
                 "problem1_of_echoLogBound"))
    for p in (2, 3):
        propose(Cand("LIN", (p, 1, 2), "ANALOGY: constDrive_dies (period 1 dies by d+2)",
                     "halfLineDies_of_linear"))
    print("    = Rule86->Rule30 counting law: refuted in Lean (runCountW_eightySix vs "
          "runCountW_thirty_edge); logged, not re-tested")
    print()

    last_junctions = []
    for r in range(4):
        N, D = echo_levels[r], half_levels[r]
        print(f"Round {r + 1}: test level n <= {N} (echo), d <= {D} (half-line)")
        for c in pool:
            if c.status != "alive":
                continue
            if c.family == "ECHO":
                ok, w = test_echo(c, N, ex, per)
            elif c.family == "LIN":
                ok, w = test_lin(c, D)
            elif c.family == "WIN":
                ok, w = test_win(c, D)
            elif c.family == "MEET":
                ok1, w1 = test_echo(Cand("ECHO", c.params[0], ""), N, ex, per)
                ok2, w2 = test_echo(Cand("ECHO", c.params[1], ""), N, ex, per)
                ok, w = ok1 and ok2, (w1 or w2)
            else:
                ok, w = test_amort(c, D)
            if not ok:
                c.status, c.witness = f"refuted (round {r + 1})", w
                print(f"    - prune   {c.name:24s} {w}")
        alive = [c for c in pool if c.status == "alive"]
        print("    survivors:", ", ".join(c.name for c in alive))

        # NARROW: frontier of each graded family
        new = []
        for a in sorted({c.params[0] for c in pool if c.family == "ECHO"}):
            bs = [c.params[1] for c in alive if c.family == "ECHO" and c.params[0] == a]
            # the sharp frontier at this level, read off the data
            bstar = max(ex[n] - a * log2(n) for n in range(1, N + 1))
            bstar = max(bstar, 0)
            print(f"    frontier ECHO(a={a}): least b standing at n <= {N} is {bstar}")
            new.append(Cand("ECHO", (a, bstar), f"NARROW: frontier at n <= {N}",
                            "problem1_of_echoLogBound"))
            if bstar > 0:
                new.append(Cand("ECHO", (a, bstar - 1), f"NARROW: probe below the frontier",
                                "problem1_of_echoLogBound"))
        for p in (2, 3):
            lins = [c for c in pool if c.family == "LIN" and c.params[0] == p]
            for a in (1, 2, 3):
                # least b with every d <= D dying by a d + b
                need = 0
                for d in range(1, D + 1):
                    for k in words(p):
                        pr = prof(p, k, d)
                        last = max(t for t in range(len(pr)) if pr[t] > 0)
                        need = max(need, last + 1 - a * d)
                print(f"    frontier LIN(p={p}, a={a}): least b at d <= {D} is {need}")
                new.append(Cand("LIN", (p, a, need), f"NARROW: frontier at d <= {D}",
                                "halfLineDies_of_linear"))
        # NARROW the amortised family on its slack e (once it has been proposed)
        for p in (2, 3):
            if not any(c.family == "AMORT" and c.params[0] == p for c in pool):
                continue
            for cc in (p, p + 1, 2 * p):
                estar = 0
                for d in range(1, D + 1):
                    for k in words(p):
                        pr = prof(p, k, d)
                        for m in range(0, len(pr) - d + 1):
                            v = pr[d - 1 + m] * 2 ** (m // cc)
                            while v > 2 ** (d - 1 + estar):
                                estar += 1
                print(f"    frontier AMORT(p={p}, c={cc}): least slack e at d <= {D} is {estar}")
                new.append(Cand("AMORT", (p, cc, estar), f"NARROW: frontier at d <= {D}",
                                "halfLineDies_of_amortized"))
        # REPAIR: refuted window halving -> amortised halving
        for c in pool:
            if c.family == "WIN" and c.status.startswith("refuted"):
                p = c.params[0]
                for cc in (p, p + 1):
                    new.append(Cand("AMORT", (p, cc, 1), f"REPAIR of {c.name}: amortise the halving",
                                    "halfLineDies_of_amortized"))
                    new.append(Cand("AMORT", (p, cc, 0), f"REPAIR of {c.name}: amortise, no slack",
                                    "halfLineDies_of_amortized"))
                for m in (2 * c.params[1], 3 * c.params[1]):
                    new.append(Cand("WIN", (p, m, 1, 2), f"NARROW: longer window than {c.name}"))
        # JUNCTION: survivors of the echo family with the same tight points
        for js in last_junctions:
            fates = {c.status for c in js}
            if len(fates) > 1:
                print(f"    junction split: {js} -> " + ", ".join(f"{c.name}: {c.status}" for c in js))
        last_junctions.clear()
        # junction: two survivors whose bounds the data touches at a common point (margin 0 at
        # the same n): no read so far separates them, and they rest on the same evidence
        tight = [c for c in alive if c.family == "ECHO" and c.tight is not None and c.tight[0] == 0]
        for i in range(len(tight)):
            for j in range(i + 1, len(tight)):
                c1, c2 = tight[i], tight[j]
                common = sorted(n for n in c1.tight[1] & c2.tight[1] if n >= 8)
                if common and c1.params[0] != c2.params[0]:
                    last_junctions.append([c1, c2])
                    a1, b1 = c1.params
                    a2, b2 = c2.params
                    print(f"    junction  {c1.name} ~ {c2.name}: both touched by the data at n = "
                          f"{common[:3]}")
                    print(f"      meet proposal: excess <= min({a1} log2 n + {b1}, {a2} log2 n + {b2})"
                          f"; the two bounds cross, so the meet is strictly sharper than either")
                    new.append(Cand("MEET", (c1.params, c2.params), f"JUNCTION meet of {c1.name}, {c2.name}",
                                    "problem1_of_echoLogBound (via either part)"))
        print("    new proposals:")
        for c in new:
            propose(c)
        print()

    print("Final report")
    print("  refuted candidates (each refutation is one finite instance; the starred ones are "
          "certified in Lean, ConjectureLoopData.lean):")
    for c in pool:
        if c.status.startswith("refuted"):
            print(f"    {c.name:24s} {c.status:20s} {c.witness}")
    print("  surviving candidates (evidence only up to the last level), with the proved implication:")
    for c in pool:
        if c.status == "alive":
            print(f"    {c.name:24s} -> {c.implies or '(no proved implication)'}   [{c.origin}]")
    print()
    print("  echo records (n, longest echo, period):",
          [(n, ex[n], per[n]) for n in range(2, NMAX + 1) if ex[n] > max(ex[1:n])])


if __name__ == "__main__":
    main()
