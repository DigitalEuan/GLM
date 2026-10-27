"""Round 11 probe: the GLM command line on the three tracks and the claim checker.

From a GLM checkout after the Round 11 setup:
    PYTHONPATH=. python3 rule30_round11/glm_round11_probe.py > rule30_round11/glm_round11_probe_output.txt
Every query runs as `GLM.py -q ... --verify-tct` in a fresh interpreter (column 3 replayed).
"""
import subprocess
import sys

sys.path.insert(0, ".")
from glm_universal.data_objects import automata_round11 as r11  # noqa: E402

d = r11.right_diagonals(12, 64)
rows = ["".join(str(d[D][t]) for D in range(12)) for t in range(10)]
diag_task = " ; ".join(f"{rows[t]} -> {rows[t + 1]}" for t in range(3, 7)) + " ? " + rows[7]

QUERIES = [
    # track A: the seed's right edge as a carrier
    "describe r30_seed_right_edge_zero",
    "report wheel diagonals",
    "describe r30_rdiag_5",
    "describe r30_rdiag_7",
    "describe r30_rdiag_8",
    "describe r30_rdiag_balanced",
    # the right-edge observer: same process, moving frame
    "tool induce " + diag_task,
    # track B: the off-centre observer
    "report wheel chirality",
    "describe r30_wobble_D_10000_column_1",
    "compare r30_wobble_D_10000_column_1 and r30_wobble_D_10000_column_m1",
    "describe r30_chiral_gap_first_1",
    "describe r30_chiral_gap_1_1000000",
    # track C: the parity count
    "describe r30_white_diagonal_parity",
    "tool induce 0001000 -> 0011100 ; 0011100 -> 0110010 ; 0110010 -> 1101111 ? 1101111",
    "tool induce 0001000 -> 0011100 ; 0011100 -> 0110010 ; 0110010 -> 1101111 ; "
    "1101111 -> 1001000 ? 1001000",
    # track D: claims
    "tool claim The center column observer can distinguish wheel 30 from wheel 86.",
    "tool claim the right-edge zero boundary forces frequency 1/2",
    "Is it true that every right diagonal is balanced?",
    "report wheel claims",
    # the questions themselves
    "real value r30_question_balance",
]

for q in QUERIES:
    p = subprocess.run([sys.executable, "GLM.py", "-q", q, "--verify-tct"],
                       capture_output=True, text=True, timeout=900)
    print("=" * 100)
    print(p.stdout.rstrip())
    if p.returncode not in (0, 1):
        print(f"[exit {p.returncode}] {p.stderr[-800:]}")
