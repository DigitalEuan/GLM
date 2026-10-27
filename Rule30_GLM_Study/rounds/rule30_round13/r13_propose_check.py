"""Round 13: the GLM's propose-and-check loop, run through the stack (EMP; the Lean theorems
named in the output prove the general statements).

Part A  rows -> wheel.  Look at rows 0..T of the impulse run, keep every elementary rule (wheel
        0..255) that reproduces them, PROPOSE row T+1 with each survivor, CHECK it against the
        real row T+1, repeat.  (Lean: rows_agree_iff, next_row_determined_iff,
        rows_identify_thirty, rows_three_do_not_identify, thirty_sixtyTwo_differ_only_at_101.)
Part B  the column.  The questions are about the centre column, not the rows.  Propose "the
        centre column has period p from time N on", look for the observation that refutes it,
        repeat.  Problem 1 says every proposal is refuted (problem1_iff_every_proposal_refuted).
        For p = 1 the refutation provably arrives by time 4N + 6 (refutation_horizon_one).
Part C  the lifted loop.  Every row of the stack is left-white, so the same loop can be run on
        all left-white rows at once (LeftWhiteLift.lean); the horizons are the run bounds
        (r13_periodic_runs_output.txt; RunBoundData.lean).

python3 r13_propose_check.py     (= r13_propose_check_output.txt)
"""


def eca(rule, L, C, R):
    return (rule >> (4 * L + 2 * C + R)) & 1


def run(rule, T):
    """Rows 0..T of the impulse run on the whole line: each row is (cells on [-t, t], the value
    of every cell outside [-t, t]).  Wheels with f(000) = 1 turn the white background black."""
    rows = [({0: 1}, 0)]
    for t in range(T):
        prev, bg = rows[-1]
        get = lambda c: prev.get(c, bg)
        rows.append(({c: eca(rule, get(c - 1), get(c), get(c + 1)) for c in range(-t - 1, t + 2)},
                     eca(rule, bg, bg, bg)))
    return rows


def cone(rows, t):
    return "".join(str(rows[t][0].get(c, rows[t][1])) for c in range(-t, t + 1))


def nbhds_shown(rows, T):
    seen = set()
    for t in range(T):
        cells, bg = rows[t]
        get = lambda c: cells.get(c, bg)
        for c in range(-t - 1, t + 2):
            seen.add((get(c - 1), get(c), get(c + 1)))
    return seen


def part_a(Tmax=8):
    print("PART A  rows -> wheel (propose row T+1, check, repeat)")
    real = run(30, Tmax + 1)
    for T in range(0, Tmax + 1):
        survivors = [r for r in range(256)
                     if all(cone(run(r, T), t) == cone(real, t) for t in range(T + 1))]
        proposals = {}
        for r in survivors:
            proposals.setdefault(cone(run(r, T + 1), T + 1), []).append(r)
        actual = cone(real, T + 1)
        shown = sorted("".join(map(str, n)) for n in nbhds_shown(real, T + 1))
        print(f"  rows 0..{T}: {len(survivors):3d} wheels fit; {len(proposals)} different proposals "
              f"for row {T + 1}; neighbourhoods shown by rows 0..{T}: {len(shown)}/8")
        if len(proposals) > 1 and len(proposals) <= 4:
            for row, rs in sorted(proposals.items()):
                mark = "CHECK OK " if row == actual else "refuted  "
                print(f"      {mark} row {T + 1} = {row}   proposed by wheels {rs[:6]}"
                      f"{' ...' if len(rs) > 6 else ''}")
        if len(proposals) == 1:
            print(f"      every fitting wheel proposes the same row {T + 1} = {actual}: CHECK OK, "
                  "the row is now derived, not observed")
    print("  Why row 4: the neighbourhood 101 first appears in row 3, so rows 1..3 were produced")
    print("  without ever using it, and wheels 30 and 62 differ only on 101. Row 4 is the first row")
    print("  produced with 101, so it is the first proposal that separates them. From rows 0..4 on")
    print("  only wheel 30 is left and every later proposal is confirmed: the loop runs through the")
    print("  whole stack, but it never again learns anything new.")


def centre_column(n):
    r, out = 1, []
    for t in range(n):
        out.append((r >> t) & 1)
        r = (r << 2) ^ ((r << 1) | r)
    return out


def part_b(n=6000, Nmax=1500, pmax=8):
    print("PART B  the centre column: propose 'period p from time N', find the refutation")
    a = centre_column(n)
    for p in range(1, pmax + 1):
        worst, worstN = -1, None
        for N in range(0, Nmax + 1):
            t = N
            while a[t + p] == a[t]:
                t += 1
            if t - N > worst:
                worst, worstN = t - N, N
        extra = "  (proved horizon: refuted by time 4N + 6)" if p == 1 else ""
        print(f"  p = {p}: every proposal with N <= {Nmax} is refuted; longest wait {worst} steps "
              f"(at N = {worstN}){extra}")
    print("  The waits are tiny, but no finite table closes the loop for every N (Lean:")
    print("  no_finite_certificate_problem1). A horizon valid for EVERY N is a run bound.")


def part_c():
    print("PART C  the lifted loop: every left-white row at once")
    print("  The longest p-periodic run at distance d from the black edge, over ALL left-white rows")
    print("  (exact search; Lean re-checks p = 2 for d <= 7 and p = 3..6 for d <= 4):")
    try:
        table = {}
        for line in open("r13_periodic_runs_output.txt"):
            if line.startswith("exact"):
                f = dict(kv.split("=") for kv in line.split()[1:])
                table.setdefault(int(f["p"]), []).append(f["longest_run"])
        for p in sorted(table):
            print(f"    p = {p}: d = 0.. -> {', '.join(table[p])}")
    except FileNotFoundError:
        print("    (run r13_periodic_runs first)")
    print("  p = 1 is proved for every d (runBound_one: at most 3d + 5). If such a bound existed for")
    print("  every p, Problem 1 would follow (problem1_of_runBoundsAll), and the loop of Part B would")
    print("  have a guaranteed horizon N + B_p(N) + 1 for every proposal (refutation_horizon_of_runBound).")
    print("  Conversely a bound exists for p exactly when no left-white row has an eventually")
    print("  p-periodic column (leftWhiteAperiodic_iff_runBound, a compactness argument).")


if __name__ == "__main__":
    part_a()
    print()
    part_b()
    print()
    part_c()
