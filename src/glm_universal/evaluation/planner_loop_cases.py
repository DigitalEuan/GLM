"""``glm_universal.evaluation.planner_loop_cases`` -- the loop through the
planner: the declared corpus.

The declared corpus of ``studies/PLANNER_LOOP_STUDY.md`` (Phase 88), written
and committed before any code of the round.  It is round 2 of the order of
work in ``studies/ROADMAP_STUDY.md``: candidate K4 (``derive`` as a value a
program can hold), candidate I2 (a question about a Python expression routed
through a typed frame to the evaluator) and candidate O3 = M3 (the planner's
answer chooses the next reverse operation).

The dialect of ``studies/PYTHON_SPEECH_STUDY.md`` gains three builtins that
call the rest of the machine, each returning an exact value or refusing by
name:

* ``derive(target, (name, value), ...)`` -- the stepwise planner's goal mode
  over the formula wheels: *given name = value, ..., what is the target*.
  A value is an ``int``, a ``Fraction`` or a ``unit(value, name)``.  The
  answer is a ``Fraction``; a planner refusal is ``DERIVE_REFUSED``.
* ``ask(question)`` -- one stepwise-planner question in English (a register
  lookup, a composition, a comparative).  A number is a ``Fraction``,
  ``prime`` / ``not prime`` a ``bool``, a named row a ``str``; a refusal is
  ``ASK_REFUSED``.
* ``solve(var, equation, (name, value), ...)`` -- the reverse surface's
  ``solve for var: equation``, the named program values written into the
  equation as exact literals.  A unique linear solution ``var = v`` is the
  ``Fraction`` ``v``; anything else is ``SOLVE_REFUSED``.

Without the runtime's bridge (the reasoning layer alone) each of the three
refuses ``BRIDGE_UNAVAILABLE``.

Every expected value was worked by hand in exact fractions from the wheels'
axioms (``power = voltage * current``, ``voltage = current * resistance``,
``energy = entropy * temperature``, the motor law ``P_out = eta * P_in`` of
Phase 87), the element register's own values (iron: atomic number 26, melting
point 1811 K; gold: atomic number 79, density 19.282 g/cm3) and ordinary
algebra.  An expected verdict is ``("ANSWER", literal)`` -- the dialect's
literal of the value, compared in type and value -- or ``("REFUSED", NAME)``.
"""

from __future__ import annotations

from typing import Tuple

__all__ = ["NEW_REFUSAL_NAMES", "DERIVE_CASES", "ASK_CASES", "SOLVE_CASES",
           "LOOP_CASES", "FRAME_CASES", "FRAMES", "ENGLISH_PARAPHRASES",
           "BRIDGE_CASES", "MUTATION_KINDS", "MARKS"]

Verdict = Tuple[str, ...]

#: The named refusals this round adds to the dialect.
NEW_REFUSAL_NAMES: Tuple[str, ...] = (
    "BRIDGE_UNAVAILABLE",  # derive/ask/solve with no runtime bridge
    "DERIVE_REFUSED",      # the stepwise planner refused the goal
    "ASK_REFUSED",         # the stepwise planner refused the question
    "SOLVE_REFUSED",       # the reverse surface gave no unique value
)

#: The frames of candidate I2: ``E`` is the text between the backticks,
#: which must itself be read by the dialect.  ``is `E` true`` needs a
#: ``bool`` and refuses ``NOT_A_TRUTH_VALUE`` otherwise.
FRAMES: Tuple[str, ...] = (
    "what does `E` return",
    "what is the value of `E`",
    "what is `E`",
    "evaluate `E`",
    "is `E` true",
)

#: The mutations column 3 must reject on every answered bridge program:
#: ``bridge-lie`` alters the value a call returned and nothing else;
#: ``chain-lie`` alters a sub-answer's record and the value consistently;
#: ``answer`` alters the program's final claim.
MUTATION_KINDS: Tuple[str, ...] = ("bridge-lie", "chain-lie", "answer")

_PWR = 'derive("power", ("voltage", 12), ("resistance", 4))'

# (id, program, expected verdict)
DERIVE_CASES: Tuple[Tuple[str, str, Verdict], ...] = (
    ("d01", _PWR, ("ANSWER", "Fraction(36, 1)")),
    ("d02", f"p = {_PWR}\np * 60", ("ANSWER", "Fraction(2160, 1)")),
    ("d03", 'i = derive("current", ("voltage", 12), ("resistance", 4))\n'
            'derive("power", ("current", i), ("resistance", 4))',
     ("ANSWER", "Fraction(36, 1)")),
    ("d04", 'derive("power", ("voltage", 12))', ("REFUSED", "DERIVE_REFUSED")),
    ("d05", 'derive("happiness", ("voltage", 12), ("resistance", 4))',
     ("REFUSED", "DERIVE_REFUSED")),
    ("d06", 'derive("power", ("voltage", 12), ("resistance", 4), '
            '("current", 5))', ("REFUSED", "DERIVE_REFUSED")),
    ("d07", 'derive("power", ("voltage", 1.5), ("resistance", 4))',
     ("REFUSED", "FLOAT")),
    ("d08", 'derive("power", ("voltage", Fraction(3, 2)), ("resistance", 4))',
     ("ANSWER", "Fraction(9, 16)")),
    ("d09", 'total = 0\nfor r in range(1, 5):\n'
            '    total = total + derive("current", ("voltage", 12), '
            '("resistance", r))\ntotal', ("ANSWER", "Fraction(25, 1)")),
    ("d10", 'derive("power", "voltage")', ("REFUSED", "PYTHON_ERROR")),
    ("d11", 'derive("power", ("voltage", unit(12, "volts")), '
            '("resistance", unit(4, "ohms")))', ("ANSWER", "Fraction(36, 1)")),
    ("d12", 'derive("torque", ("voltage", 230), ("current", 2), '
            '("motor efficiency", Fraction(9, 10)), ("angular velocity", 100))',
     ("ANSWER", "Fraction(207, 50)")),
)

ASK_CASES: Tuple[Tuple[str, str, Verdict], ...] = (
    ("a01", 'ask("the atomic number of iron")', ("ANSWER", "Fraction(26, 1)")),
    ("a02", 'ask("the atomic number of iron") + '
            'ask("the atomic number of gold")', ("ANSWER", "Fraction(105, 1)")),
    ("a03", 'ask("is the atomic number of iron prime")', ("ANSWER", "False")),
    ("a04", 'ask("the electron affinity of helium")',
     ("REFUSED", "ASK_REFUSED")),
    ("a05", 'ask("the happiness of iron")', ("REFUSED", "ASK_REFUSED")),
    ("a06", 'ask("the density of gold")', ("ANSWER", "Fraction(9641, 500)")),
    ("a07", 'ask(26)', ("REFUSED", "PYTHON_ERROR")),
    ("a08", 'ask("which is denser, gold or lead")', ("ANSWER", "'gold'")),
)

SOLVE_CASES: Tuple[Tuple[str, str, Verdict], ...] = (
    ("s01", 'solve("x", "3 * x - 1 == x + 4")', ("ANSWER", "Fraction(5, 2)")),
    ("s02", 'solve("t", "p * t == 7200", ("p", 36))',
     ("ANSWER", "Fraction(200, 1)")),
    ("s03", 'solve("x", "x ** 2 == 4")', ("REFUSED", "SOLVE_REFUSED")),
    ("s04", 'solve("x", "x + 1 == x + 2")', ("REFUSED", "SOLVE_REFUSED")),
    ("s05", 'solve("x", "2 * x < 6")', ("REFUSED", "SOLVE_REFUSED")),
    ("s06", 'solve("y", "y * k == 1", ("k", Fraction(2, 3)))',
     ("ANSWER", "Fraction(3, 2)")),
)

#: Candidate O3 = M3: programs in which one surface's answer chooses the
#: next operation -- a branch on a derived value picks the reverse question
#: asked, a loop runs the planner until its answer crosses a bound, a solved
#: value feeds a derivation, a register value feeds a wheel.
LOOP_CASES: Tuple[Tuple[str, str, Verdict], ...] = (
    ("l01", f"p = {_PWR}\nif p > 30:\n"
            '    t = solve("t", "p * t == 7200", ("p", p))\nelse:\n'
            '    t = solve("t", "p * t == 3600", ("p", p))\nt',
     ("ANSWER", "Fraction(200, 1)")),
    ("l02", 'r = 1\nwhile derive("current", ("voltage", 12), '
            '("resistance", r)) >= 1:\n    r = r + 1\nr', ("ANSWER", "13")),
    ("l03", 'v = solve("v", "2 * v + 3 == 27")\n'
            'derive("power", ("voltage", v), ("resistance", 4))',
     ("ANSWER", "Fraction(36, 1)")),
    ("l04", 'z = ask("the atomic number of iron")\n'
            'if ask("is the atomic number of iron prime"):\n'
            '    w = z\nelse:\n'
            '    w = solve("w", "w - z == 1", ("z", z))\nw',
     ("ANSWER", "Fraction(27, 1)")),
    ("l05", 'p = derive("power", ("voltage", 12))\np + 1',
     ("REFUSED", "DERIVE_REFUSED")),
    ("l06", 'def watts(v, r):\n'
            '    return derive("power", ("voltage", v), ("resistance", r))\n'
            'out = ()\nfor v in range(1, 4):\n'
            '    out = out + (watts(v, 2),)\nout',
     ("ANSWER", "(Fraction(1, 2), Fraction(2, 1), Fraction(9, 2))")),
    ("l07", 'd = ask("the density of gold")\nif d > 19:\n'
            '    x = solve("x", "x * d == 1", ("d", d))\nelse:\n'
            '    x = Fraction(0)\nx', ("ANSWER", "Fraction(500, 9641)")),
    ("l08", 'm = ask("the melting point of iron")\n'
            'derive("energy", ("temperature", unit(m, "kelvin")), '
            '("entropy", 2))', ("ANSWER", "Fraction(3622, 1)")),
)

#: Candidate I2: questions about a Python expression, through a frame.
#: ``("SURFACE", name)`` says the frame must not read the text and which
#: surface does.
FRAME_CASES: Tuple[Tuple[str, str, Verdict], ...] = (
    ("f01", "what does `sum(range(3, 100, 7))` return?", ("ANSWER", "679")),
    ("f02", "what is the value of `2 ** 10 - 1`?", ("ANSWER", "1023")),
    ("f03", "evaluate `divmod(17, 5)`", ("ANSWER", "(3, 2)")),
    ("f04", "is `7 in range(0, 10, 3)` true?", ("ANSWER", "False")),
    ("f05", "what does `Fraction(1, 3) + Fraction(1, 6)` return?",
     ("ANSWER", "Fraction(1, 2)")),
    ("f06", "what does `1 / 3` return?", ("REFUSED", "FLOAT")),
    ("f07", 'what is `derive("power", ("voltage", 12), ("resistance", 4))`?',
     ("ANSWER", "Fraction(36, 1)")),
    ("f08", "is `len((1, 2, 3))` true?", ("REFUSED", "NOT_A_TRUTH_VALUE")),
    ("f09", "what does `the atomic number of iron` return?",
     ("SURFACE", "planner")),
    ("f10", 'evaluate `ask("the atomic number of iron") * 2`',
     ("ANSWER", "Fraction(52, 1)")),
)

#: The English questions the loop programs answer, asked of the router
#: directly: the reading of the utility gate (item 9).  Declared expectation:
#: the router answers none of them, because each needs one surface's answer
#: to choose the next step.
ENGLISH_PARAPHRASES: Tuple[Tuple[str, str], ...] = (
    ("l01", "if the power at 12 volts across 4 ohms is above 30 watts, how "
            "long does that power take to deliver 7200 joules"),
    ("l02", "what is the smallest whole resistance for which the current at "
            "12 volts is below 1 ampere"),
    ("l03", "what is the power across 4 ohms at the voltage that solves "
            "2 v + 3 = 27"),
    ("l07", "what is the reciprocal of the density of gold if it is above 19"),
    ("l08", "given the melting point of iron and entropy = 2, what is the "
            "energy, computed from the register value"),
)

#: Every case whose program calls the bridge (for the bridge-off control).
BRIDGE_CASES: Tuple[str, ...] = tuple(
    cid for cid, src, _ in DERIVE_CASES + ASK_CASES + SOLVE_CASES + LOOP_CASES
    if any(b + "(" in src for b in ("derive", "ask", "solve")))

#: The marks of the round, declared with the corpus and before any code.
MARKS: Tuple[Tuple[str, str], ...] = (
    ("W1", "every derive case as declared, 0 wrong"),
    ("W2", "every ask and solve case as declared, 0 wrong"),
    ("W3", "every loop case as declared, 0 wrong; the bridge-off control "
           "(the dialect alone) answers none of the bridge cases and refuses "
           "each by name"),
    ("W4", "every frame case as declared; on the earlier declared question "
           "sets the frames change the surface of no question"),
    ("W5", "every answered bridge program's column-3 script verifies in a "
           "fresh interpreter, re-running every sub-answer's own script, "
           "and every mutation of MUTATION_KINDS is rejected"),
    ("W6", "through the router the machine answers every ANSWER case of the "
           "corpus; before the round it answered none of the bridge cases"),
    ("W7", "nothing earlier moves: the dialect's declared value and refusal "
           "cases, its differential battery (0 wrong) and the stepwise "
           "planner's declared chains as they were"),
    ("W8", "the facts the round rests on proved in Lean, without sorry"),
)
