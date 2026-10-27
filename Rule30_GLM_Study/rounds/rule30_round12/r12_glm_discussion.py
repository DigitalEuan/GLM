"""Round 12: a considered discussion of Rule 30, held with the GLM in its own language.

Every question runs as `GLM.py -q <question> --verify-tct` in a fresh interpreter, in four phases,
broad to narrow, then a fifth phase of deliberate probes past the edge of what the GLM holds.
The point of phase E is the limitations: each refusal says which part of the language is missing.

From a GLM checkout after setup_round12.sh:
    PYTHONPATH=. python3 rule30_round12/r12_glm_discussion.py > rule30_round12/r12_glm_discussion_output.txt
"""
import subprocess
import sys

PHASES = [
    ("A. BROAD -- what is on the wheel", [
        "show me the theorem wheel",
        "which axioms do the theorems rest on",
        "tool theorem lenses",
        "describe r30_question_balance",
    ]),
    ("B. THE THREE QUESTIONS, read over the wheel", [
        "discuss whether the centre column is eventually periodic",
        "how could we prove that black cells have frequency 1/2 in the centre column",
        "discuss the cost of computing a(n)",
    ]),
    ("C. NARROW -- the weakest sufficient hypothesis and its lens", [
        "describe r30_question_apbalanced",
        "tool theorem derive SeedFSTypical => SeedAPBalanced",
        "tool theorem derive SeedAPBalanced => SeedFSTypical",
        "tool theorem derive SeedAPBalanced => P1",
        "describe r30_strobe_D_3_1",
        "compare r30_strobe_D_3_1 and r30_strobe_D_3_1_1e7",
        "describe r30_arrow_last_zero_1e6",
    ]),
    ("D. THE READ ANGLE -- what the edges see and the centre does not", [
        "describe r30_ldiag_7",
        "describe r30_ldiag_40",
        "describe r30_rdiag_balanced",
        "tool claim right diagonal 5 is balanced",
        "tool claim right diagonal 7 is balanced",
    ]),
    ("E. PAST THE EDGE -- probes the GLM is expected to refuse", [
        "why does rule 30 look random?",
        "is the centre column a normal sequence?",
        "what is bit 10000001 of the centre column?",
        "tool theorem derive Stride1Nonconstant => P1",
        "tool theorem derive LeftDiagonalsPeriodic => P1",
        "discuss a better bound on the wobble than the square root",
        "prove that the centre column is not periodic with period 2",
    ]),
]

for title, qs in PHASES:
    print("#" * 100)
    print("# " + title)
    for q in qs:
        p = subprocess.run([sys.executable, "GLM.py", "-q", q, "--verify-tct"],
                           capture_output=True, text=True, timeout=900)
        print("=" * 100)
        print(p.stdout.rstrip())
        if p.returncode not in (0, 1):
            print(f"[exit {p.returncode}] {p.stderr[-800:]}")
