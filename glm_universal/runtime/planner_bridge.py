"""``glm_universal.runtime.planner_bridge`` -- the loop through the planner.

Phase 88 (``studies/PLANNER_LOOP_STUDY.md``), round 2 of the order of work in
``studies/ROADMAP_STUDY.md``.  The Python dialect
(:mod:`glm_universal.reasoning.python_speech`) and the planner were two
surfaces that could not use each other: a program could not hold a
derivation, and the planner could not run a program.  This module is the
bridge between them, in both directions.

* **Into the program** (candidate K4, and O3 = M3).  Three dialect builtins
  call the rest of the machine and return an exact value:

  ``derive(target, (name, value), ...)``
      the stepwise planner's goal mode over the formula wheels,
      *given name = value, ..., what is the target*;
  ``ask(question)``
      one stepwise-planner question in English -- a register lookup (a
      single leaf, read here and nowhere else), a composition, a
      comparative;
  ``solve(var, equation, (name, value), ...)``
      the reverse surface's ``solve for var: equation``, with the named
      program values written into the equation as exact literals.

  Because each is a value, the program's own control flow is the loop: a
  branch on a derived value chooses which reverse question is asked next, a
  ``while`` runs the planner until its answer crosses a bound, a solved value
  is fed to a derivation.  Each call's answer travels with its surface's own
  checked record -- the chain of the stepwise planner, the certificate of the
  reverse surface -- and the program's column-3 script re-runs that record's
  own script in a fresh interpreter before it binds the value
  (``python_speech._SCRIPT_BRIDGE``).  A surface's refusal is the program's
  refusal, by name: ``DERIVE_REFUSED``, ``ASK_REFUSED``, ``SOLVE_REFUSED``.
  The dialect alone, with no bridge, refuses ``BRIDGE_UNAVAILABLE``.

* **Into the evaluator** (candidate I2).  :func:`frame_of` reads a question
  about a Python expression -- *what does `E` return*, *is `E` true* -- and
  the router hands ``E`` to the evaluator (``router.route``).

The reasoning layer starts no process and does not call the planner; this
module lives in the runtime layer because it does both.  Exact throughout.
"""

from __future__ import annotations

import ast
import re
from fractions import Fraction
from typing import Dict, Optional, Tuple

from ..reasoning.python_substrate import PythonRefusal

__all__ = ["PlannerBridge", "bridge_for", "frame_of", "FRAME_PATTERNS",
           "speak_text",
           "chain_value", "mutated_records"]


def chain_value(v: object) -> object:
    """A stepwise answer as a dialect value: a number is a ``Fraction``,
    ``prime`` / ``not prime`` a ``bool``, a named row a ``str``."""
    if isinstance(v, bool):
        return v
    if isinstance(v, int):
        return Fraction(v)
    if isinstance(v, Fraction):
        return v
    if isinstance(v, str):
        return {"prime": True, "not prime": False, "True": True,
                "False": False}.get(v, v)
    return None


class PlannerBridge:
    """The runtime's bridge, handed to :func:`python_speech.speak`."""

    def __init__(self, session=None, root: Optional[str] = None):
        if root is None:
            from .tct_engine import package_root
            root = str(package_root())
        self._session = session
        self.root = root
        self.calls = 0

    @property
    def session(self):
        """The planner's session, built on the first call that needs it."""
        if self._session is None:
            from .session import GeometricSession
            self._session = GeometricSession()
        return self._session

    # -- the three operations -------------------------------------------------
    def call(self, op: str, question: str, meta: Dict[str, object]
             ) -> Tuple[object, Dict[str, object]]:
        self.calls += 1
        if op == "derive":
            return self._chain(op, question, "DERIVE_REFUSED", meta)
        if op == "ask":
            return self._chain(op, question, "ASK_REFUSED", meta)
        if op == "solve":
            return self._solve(question, meta)
        raise PythonRefusal("UNSUPPORTED", f"no bridge operation {op!r}")

    def _chain(self, op: str, question: str, refusal: str,
               meta: Dict[str, object]):
        from . import stepwise as sw
        from ..reasoning import stepwise_script as ss
        from ..reasoning.python_speech import literal
        a = sw.answer(self.session, question)
        if a.verdict == "unread" and op == "ask":
            a = sw.compose(self.session, question, single=True)
        if a.verdict == "unread":
            raise PythonRefusal(refusal, f"the stepwise planner does not read "
                                         f"“{question}”")
        if not a.answered:
            name = a.refusal or "AMBIGUOUS"
            raise PythonRefusal(refusal, f"{name}: {a.reason}")
        value = chain_value(a.chain.answer)
        if value is None or (op == "derive"
                             and not isinstance(value, Fraction)):
            raise PythonRefusal(refusal, f"the answer "
                                         f"{ss.render_value(a.chain.answer)} "
                                         "is not a single exact value")
        data = ss.chain_data(a.chain)
        record = {"op": op, "question": question, "kind": "chain",
                  "value": literal(value), "data": data,
                  "script": ss.render_script(a.chain, self.root),
                  "steps": len(a.chain.steps),
                  "summary": f"{a.chain.kind} chain of "
                             f"{len(a.chain.steps)} steps"}
        record.update({k: v for k, v in meta.items()})
        return value, record

    def _solve(self, question: str, meta: Dict[str, object]):
        from ..reasoning import reverse_tct as rv
        from ..reasoning import reverse_tct_script as rts
        from ..reasoning.python_speech import literal
        var, equation = str(meta["var"]), str(meta["equation"])
        try:
            body = ast.parse(equation, mode="eval").body
        except SyntaxError:
            body = None
        if not (isinstance(body, ast.Compare) and len(body.ops) == 1
                and isinstance(body.ops[0], ast.Eq)):
            raise PythonRefusal("SOLVE_REFUSED", "solve() takes one equation "
                                                 "written in Python, with ==")
        if not re.fullmatch(r"[A-Za-z_]\w*", var):
            raise PythonRefusal("SOLVE_REFUSED", f"{var!r} is not a variable")
        a = rv.answer(question)
        if not a.answered:
            raise PythonRefusal("SOLVE_REFUSED", f"{a.refusal}: {a.reason}")
        cert = a.certificate
        second = cert.get("second") or []
        if (cert.get("kind") != "statement" or len(second) != 4
                or list(second[:3]) != ["rel", "=", ["var", var]]
                or second[3][0] != "lit"):
            raise PythonRefusal("SOLVE_REFUSED", f"{a.verdict}: the answer "
                                f"“{a.sentence}” is not one value of {var}")
        value = Fraction(second[3][1])
        data = {"read_back": rts._read_back_pairs(a), "certificate": cert}
        record = {"op": "solve", "question": question, "kind": "reverse",
                  "value": literal(value), "data": data,
                  "script": rts.render_script(a, self.root),
                  "steps": len(a.column1),
                  "summary": f"reverse {a.verdict.lower()}: {a.sentence}",
                  "var": var, "equation": equation}
        return value, record


_BRIDGES: Dict[int, PlannerBridge] = {}


def bridge_for(session) -> PlannerBridge:
    """One bridge per session (the router's); ``None`` builds its session
    on the first call that needs one."""
    got = _BRIDGES.get(id(session))
    if got is None or got._session is not session:
        got = _BRIDGES[id(session)] = PlannerBridge(session)
    return got


def speak_text(text: str, bridge=None):
    """The python surface's verdict on ``text`` -- a program, or a declared
    frame around an expression: ``(payload, answered, body)``.  The one
    place the router and the command line both read it."""
    from ..reasoning import python_speech as sp
    from .router import python_reads
    framed = None if python_reads(text) else frame_of(text)
    source = framed[1] if framed else text
    p = sp.speak(source, bridge=bridge)
    answered = p.answered
    body = (f"{p.value_literal}" if p.answered
            else f"refused: {p.refusal}: {p.reason}")
    if framed and framed[0] == "truth" and p.answered \
            and not isinstance(p.value, bool):
        answered = False
        body = (f"refused: NOT_A_TRUTH_VALUE: `{source}` is "
                f"{p.value_literal}, not True or False")
    return p, answered, body


# ===========================================================================
# THE FRAMES OF CANDIDATE I2
# ===========================================================================

#: ``(frame name, pattern)``: the expression is the text between backticks.
FRAME_PATTERNS: Tuple[Tuple[str, str], ...] = (
    ("return", r"what does `(.+)` return\??"),
    ("value", r"what is the value of `(.+)`\??"),
    ("value", r"what is `(.+)`\??"),
    ("value", r"evaluate `(.+)`\.?"),
    ("truth", r"is `(.+)` true\??"),
)


def frame_of(text: str) -> Optional[Tuple[str, str]]:
    """``(frame, expression)`` when ``text`` is a declared frame around an
    expression the dialect reads; ``None`` otherwise."""
    from .router import python_reads
    t = text.strip()
    for name, pat in FRAME_PATTERNS:
        m = re.fullmatch(pat, t, flags=re.IGNORECASE)
        if m and "`" not in m.group(1) and python_reads(m.group(1)):
            return name, m.group(1)
    return None


# ===========================================================================
# THE MUTATIONS OF MARK W5
# ===========================================================================

def _lie(literal_text: str) -> str:
    v = eval(literal_text, {"Fraction": Fraction, "__builtins__": {}})
    from ..reasoning.python_speech import literal
    if isinstance(v, bool):
        return literal(not v)
    if isinstance(v, Fraction):
        return literal(v + 1)
    return literal(str(v) + "!")


def mutated_records(records, kind: str, root: str):
    """The bridge records with one declared lie (``bridge-lie`` or
    ``chain-lie``) in the first record; ``None`` when the kind does not
    apply."""
    import json
    from ..reasoning import reverse_tct_script as rts
    from ..reasoning import stepwise_script as ss
    if not records:
        return None
    out = json.loads(json.dumps(list(records)))
    rec = out[0]
    if kind == "bridge-lie":
        rec["value"] = _lie(rec["value"])
        return out
    if kind != "chain-lie":
        return None
    new = _lie(rec["value"])
    v = eval(new, {"Fraction": Fraction, "__builtins__": {}})
    rec["value"] = new
    if rec["kind"] == "chain":
        last = rec["data"]["steps"][-1]
        shown = ss.render_value(v) if not isinstance(v, bool) else (
            "prime" if v else "not prime") if last["value"] in (
            "prime", "not prime") else str(v)
        old = last["value"]
        last["value"] = shown
        last["column1"] = last["column1"].replace(old, shown)
        last["column2"] = last["column2"].replace(old, shown)
        rec["data"]["answer"] = f"Answer: {shown}."
        rec["script"] = ss.render_script(None, root, rec["data"])
    else:
        cert = rec["data"]["certificate"]
        cert["second"][3][1] = f"{v.numerator}/{v.denominator}"
        rec["script"] = (rts._SCRIPT.replace("@@ROOT@@", repr(root))
                         .replace("@@DATA@@", repr(json.dumps(
                             rec["data"], sort_keys=True))))
    return out
