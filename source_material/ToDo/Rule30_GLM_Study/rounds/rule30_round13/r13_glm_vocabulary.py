"""Round 13: what does the GLM need to answer each of the three questions?

Extends the Round 12 theorem wheel with the Round 13 vocabulary and prints, for each question,
the wheel's discussion (``tool discuss``) and the vocabulary audit.

python3 r13_glm_vocabulary.py     (= r13_glm_vocabulary_output.txt)
"""
import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, "glm_overlay", "glm_universal", "reasoning"))
import theorem_wheel_round13 as w13  # noqa: E402

w13.extend()
tw = w13.tw
ok, text, _ = tw.theorem_text("wheel")
print(text.splitlines()[0])
print()
for q, t in (("Is the centre column eventually periodic? (Problem 1)", "P1"),
             ("Is the frequency of black cells one half? (Problem 2)", "P2"),
             ("Does computing a(n) cost time growing with n? (Problem 3)", "P3")):
    print("=" * 100)
    print("QUESTION:", q)
    ok, text, _ = tw.discuss_text(q)
    print(text)
    print()
    print(w13.vocabulary_audit(t))
    print()
