"""Round 7: put Rule 30 questions to the GLM session (parser.py + session.py + tct_engine.py).

Usage (from a GLM checkout, i.e. the directory that holds GLM.py):
    cp /path/to/parser.py /path/to/session.py /path/to/tct_engine.py glm_universal/runtime/
    cp /path/to/glm_reports_init_shim.py glm_universal/runtime/reports/__init__.py   # only if missing
    PYTHONPATH=. python3 /path/to/glm_probe.py > glm_probe_output.txt

Each query goes to GeometricSession.ask; the printed answer is the session's own text.
"""
import sys
sys.path.insert(0, '.')
from glm_universal.runtime.session import GeometricSession

QUERIES = [
    # the prize questions, as plain language
    "is it true that the rule 30 centre column is eventually periodic",
    "does it hold that the frequency of black cells in rule 30 tends to one half",
    "describe rule 30",
    "explain cellular automaton",
    "what is the centre column",
    # the GLM's own substrate, used in round 6
    "report golay decoding",
    "report capabilities",
    "report lean",
    # controls: exact arithmetic the GLM does handle
    "compare sqrt(2) and 7/5",
    "approximate sqrt(2) to precision 10",
]

S = GeometricSession()
for q in QUERIES:
    print("=" * 72)
    print("Q:", q)
    try:
        sol = S.ask(q)
        txt = getattr(sol, "answer", None)
        print("A:", str(txt) if txt is not None else repr(sol)[:2000])
    except Exception as e:  # report, do not hide
        print("ERROR:", type(e).__name__, str(e)[:800])
