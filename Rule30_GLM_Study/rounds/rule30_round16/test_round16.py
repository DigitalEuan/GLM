"""Round 16 tests: the normalisation operator and the structured reading (run: python3 test_round16.py)."""
import os
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "glm_overlay", "glm_universal", "reasoning"))

import wobble_normalize as wn          # noqa: E402
import theorem_wheel_round16 as tw16   # noqa: E402
tw = tw16.tw

# --- normalisation operator -----------------------------------------------------------------
for N in range(1, 13):
    assert wn.check_fair_coin_moments(N), N
r = wn.normalise(1536, 10 ** 6)                     # CERT wobble_1e6
assert r.z2 == Fraction(1536 ** 2, 10 ** 6) and r.at_least(Fraction(3, 2)) and not r.at_least(2)
assert wn.compare(wn.normalise(4440, 10 ** 7), r) < 0   # raw 4440 > 1536, but |z| 1.40 < 1.54
assert wn.chebyshev_fraction(Fraction(43, 10)) < Fraction(55, 1000)
print("normalisation operator: moments N <= 12 exact; D(1e6)=1536 ->", r,
      "; D(1e7)=4440 ->", wn.normalise(4440, 10 ** 7))

# --- structured reading vs the Round 12 keyword router --------------------------------------
CASES = [
    ("Is the wobble bounded over a long period of time?", "P2"),
    ("How long does the frequency take to settle in the long run?", "P2"),
    ("Does the centre column eventually alternate with period 2?", "P1"),
    ("What is the running time needed to compute a(n)?", "P3"),
    ("Is D(N)/sqrt(N) bounded for the centre column?", "P2"),
    ("Is the column eventually periodic?", "P1"),
    ("What angle does the light cone triangle make?", "GEOMETRY"),
    ("Is the frequency periodic?", None),            # genuinely ambiguous: must ask
]
ok = True
for q, want in CASES:
    old = tw._target_of(q)
    rd = tw16.read(q)
    got = None if rd.ambiguous else rd.target
    flag = "ok " if got == want else "BAD"
    ok &= got == want
    print(f"{flag} old={str(old):4s} new={str(got):8s} rung={rd.rung}  | {q}")
assert ok
good, text, info = tw16.discuss_structured("Does the centre column eventually alternate with period 2?")
assert good and "LeftWhiteAperiodic2" in text
print()
print(text.splitlines()[0])
print("\n".join(l for l in text.splitlines() if "rung" in l or "evidence" in l))
print("all Round 16 tests passed")
