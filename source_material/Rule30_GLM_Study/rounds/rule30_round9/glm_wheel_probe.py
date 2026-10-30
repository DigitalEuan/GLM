"""Round 9: put the three questions to the GLM with the cellular-automaton register enabled.

The queries carry the object inside the query: a wheel is named by its truth table
(wheel_00011110 = the local map bit(4L+2C+R) of 0b00011110), and every run carrier is one exact
fact about wheel 00011110 from the impulse row delta_0, read at column 0.

Setup (from a GLM checkout, i.e. the directory that holds GLM.py):
    cp parser.py session.py tct_engine.py                    glm_universal/runtime/
    cp __init__.py lattice_geometry.py                       glm_universal/runtime/reports/
    cp rule30_round9/frozen_path_standin.py                  glm_universal/reasoning/frozen_path.py
    cp -r rule30_round9/glm_glm_universal/.          glm_universal/
    PYTHONPATH=. python3 rule30_round9/glm_wheel_probe.py > rule30_round9/glm_wheel_probe_output.txt

(`glm_overlay` replaces runtime/session.py and runtime/parser.py with the patched copies; the two
`.patch` files show exactly what changed, if you prefer to apply them to your own copies.)
"""
import sys
sys.path.insert(0, '.')
from glm_universal.runtime.session import GeometricSession

QUERIES = [
    # the family and the run
    "report wheel",
    "describe wheel_00011110",
    "describe wheel_01011010",
    "describe wheel_family",
    # Track A: the accumulator (question 2)
    "describe r30_wobble_D_10000",
    "describe r30_wobble_D_1000000",
    "is r30_wobble_D_1000000 greater than 0",
    "real value r30_wobble_D_1000000 / 1000000",
    "describe r30_delta_sigma_accumulator",
    "describe r30_question_balance",
    "is r30_question_balance equal to 1/2",
    # Track B: algebra and observers (question 1)
    "describe r30_anf_degree_7",
    "is r30_anf_degree_10 greater than 18",
    "is r30_anf_degree_10 equal to 19",
    "describe r30_cone_separation_derivative",
    "describe r30_lag_predictor",
    "describe r30_question_aperiodicity",
    # Track C: the light cone (question 3)
    "describe r30_light_cone_dependency_10",
    "describe r30_essential_inputs_6",
    "compare r30_essential_inputs_10 and 21",
    "describe r30_question_cost",
    # the neighbour where the questions are settled
    "describe wheel_90_impulse_centre",
    # query forms the GLM's grammar does not read (kept to show the refusals)
    "compare r30_anf_degree_10 to 19",
    "derive r30_fs_observer_error_rate from r30_lag_predictor",
    # plain-English controls (still refused: no English concept was added)
    "describe rule 30",
    "what is the centre column",
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
