"""Round 10: the GLM works through Rule 30 step by step, induces the wheel, and reads the frame.

Setup (from a GLM checkout, i.e. the directory that holds GLM.py), after the Round 9 setup:
    cp -r rule30_round10/glm_glm_universal/.   glm_universal/
    PYTHONPATH=. python3 rule30_round10/glm_round10_probe.py > rule30_round10/glm_round10_probe_output.txt
"""
import sys
sys.path.insert(0, '.')
from glm_universal.runtime.session import GeometricSession
from glm_universal.reasoning import wheel_induction as wi
from glm_universal.data_objects import automata as ca

QUERIES = [
    # 1. the run, step by step at the centre
    "report wheel steps",
    "describe r30_step_0",
    "describe r30_step_5",
    "describe r30_step_6",
    "describe r30_step_63",
    # 2. the wheel induced from rows of the diagram (ARC-style)
    "report wheel induction",
    "describe r30_induction_rows_1",
    "describe r30_induction_rows_2",
    "describe r30_induction_rows_3",
    "describe r30_induction_rows_4",
    "is r30_induction_rows_3 greater than 1",
    # 3. what one column can tell
    "report wheel observer",
    "describe r30_observer_column_0",
    "describe r30_observer_column_1",
    "describe r30_observer_column_m1",
    "is r30_observer_column_0 greater than r30_observer_column_1",
    # 4. the frame of view and the arrow
    "report wheel perspective",
    "describe r30_arrow_mirror",
    "describe r30_arrow_colour",
    "compare r30_arrow_mirror and r30_arrow_colour",
    # 5. the questions themselves are still open
    "describe r30_question_aperiodicity",
    "real value r30_question_balance",
]

S = GeometricSession()
for q in QUERIES:
    print("=" * 78)
    print("Q:", q)
    try:
        sol = S.ask(q)
        print("A:", sol.answer)
        for st in sol.steps:
            print(f"  [{st.label}]")
            print(f"     words: {st.language}")
            print(f"     maths: {st.mathematics}")
    except Exception as e:  # report, do not hide
        print("REFUSED:", type(e).__name__, str(e)[:800])

# The induction engine directly, in the toolbox's grammar (what `tool induce` answers once
# toolbox_wheel_induction.patch is applied in a full checkout).
TASKS = [
    "0001000 -> 0011100 ; 0011100 -> 0110010 ? 0110010",
    "0001000 -> 0011100 ; 0011100 -> 0110010 ; 0110010 -> 1101111 ? 1101111",
    "000010000 -> 000111000 ; 000111000 -> 001100100 ; 001100100 -> 011011110 ; "
    "011011110 -> 110010001 ? 110010001",
    "0001000 / 0011100 / 0110010 ? 0110010",
]
for t in TASKS:
    print("=" * 78)
    print("tool induce", t)
    ok, text, figures = wi.induce_rows_text(t)
    print(text)
    print("figures:", figures)
print("=" * 78)
print("observer readings of the centre column:")
for K in (5, 6, 7, 50, 500):
    print(" ", wi.induce_column_text(ca.evolve_impulse_column(30, K, 0), 0))
