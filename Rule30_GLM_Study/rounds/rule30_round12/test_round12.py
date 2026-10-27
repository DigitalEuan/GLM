"""Round 12 self-test (plain asserts; each check names its Lean theorem).

From a GLM checkout after setup_round12.sh:  PYTHONPATH=. python3 rule30_round12/test_round12.py
"""
import subprocess
import sys

sys.path.insert(0, ".")
from glm_universal.data_objects import automata_round12 as r12  # noqa: E402
from glm_universal.reasoning import theorem_wheel as tw  # noqa: E402


def bits(n):
    r, out = 1, []
    for t in range(n):
        out.append((r >> t) & 1)
        r = (r << 2) ^ ((r << 1) | r)
    return out


a = bits(30000)
# strobe_wobble_table on a prefix: D_{p,r} at M = 30000 // p equals the definition
for p in range(2, 7):
    M = 30000 // p
    tot = sum(sum(2 * a[p * t + r] - 1 for t in range(M)) for r in range(p))
    assert tot == sum(2 * x - 1 for x in a[:p * M])        # wobble_strobe_sum
# OEIS A051023 start (centerCol_first_30)
assert a[:12] == [1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 0, 0]
# left diagonals: ldiag 0 is the black edge, every computed diagonal is eventually periodic
rec = r12.left_diagonal_records()
assert rec[0] == (1, 0)                                    # ldiag_zero
assert all(p & (p - 1) == 0 for p, _ in rec)               # power-of-two periods
# the theorem wheel: certificates and controls
assert tw.derivation("SeedFSTypical", "SeedAPBalanced") == ("apBalanced_of_fsTypical",)
assert tw.derives("SeedAPBalanced", "P1") and tw.derives("SeedAPBalanced", "P2")
assert not tw.derives("SeedAPBalanced", "SeedFSTypical")
assert tw.strictness("SeedAPBalanced", "SeedFSTypical").lean == "exists_apBalanced_not_fsTypical"
assert "StrobesNonconstant" in tw.equivalents("P1")        # problem1_iff_strobes
assert tw.sufficient_open("P2")[0] == "SeedAPBalanced"
assert tw.weakest_first(tw.sufficient_open("P1"))[0][0] == "SeedAPBalanced"
assert not tw.gap("P1")["closed"] and not tw.gap("P2")["closed"]
assert all(set(v) <= set(tw._CMP) for v in tw.AXIOM_FOOTPRINT.values())
# the command line
for q, want in (("tool discuss is the centre column eventually periodic", "ARROW  SeedFSTypical"
                 " -> SeedAPBalanced -> P1"),
                ("describe r30_strobe_D_3_1", "1583"),
                ("tool theorem derive SeedAPBalanced => SeedFSTypical", "negative control")):
    p = subprocess.run([sys.executable, "GLM.py", "-q", q, "--verify-tct"], capture_output=True,
                       text=True, timeout=900)
    assert want in p.stdout, (q, p.stdout[-600:])
print("round 12: all checks pass")
