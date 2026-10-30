"""``glm_universal.runtime.reverse_relay`` -- the planner loop of Reverse TCT.

``relay: Q`` (``studies/REVERSE_TCT_STUDY.md`` §7.1, mark W6) answers the
reverse question ``Q`` on the reverse surface, then hands what its column 2
holds to the planner **as questions in the planner's own input language**,
generated from column 2 and never from the English sentence:

* a closed value ``v`` becomes ``approximate v to 20 places`` and ``what
  fraction rounds to R`` (``R`` the exact nearest 20-place decimal of ``v``);
* a closed order or equality relation, and every relation of an
  ``INDEPENDENT`` verdict at its two witness points, becomes ``is a less
  than b``.

Each handoff goes through the router (so it is the default path that answers
it), must be read by the planner surface, and its answer is read back into
column 2 by a declared reader: ``AGREES``, ``CONSISTENT`` (the planner
declines to order two equal values), ``DISAGREES`` or ``UNREAD``.  What the
planner returned is realised as sentences of the reverse grammar, so the
downstream answer re-enters column 1, and the column-3 script
(:mod:`glm_universal.reasoning.reverse_tct_script`) re-reads the handoff
questions, the planner's answers and those sentences and re-checks them with
its own arithmetic.

This module lives in the runtime layer because it calls the planner through
the router; the reasoning layer does not.  Exact throughout.
"""

from __future__ import annotations

import re
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from ..evaluation.reverse_tct_two_cases import RELAY_LIMIT, RELAY_PLACES
from ..reasoning import reverse_tct as rv

__all__ = ["relay", "relay_targets", "nearest_decimal", "answer_any",
           "relay_report", "planner_only_chain", "verbatim_control"]

_SESSION = None


def _session(session):
    global _SESSION
    if session is not None:
        return session
    if _SESSION is None:
        from .session import GeometricSession
        _SESSION = GeometricSession()
    return _SESSION


# ===========================================================================
# 1.  WHAT COLUMN 2 HOLDS THAT THE PLANNER CAN BE ASKED ABOUT
# ===========================================================================

def relay_targets(cert: Dict[str, object]) -> List[Tuple]:
    """``("value", v)`` and ``("pair", a, b)`` targets of an answer's
    certificate, in a declared order."""
    kind = cert.get("kind")
    dec = rv._dec
    out: List[Tuple] = []
    if kind == "say" and "value" in cert:
        v = rv.evaluate(dec(cert["value"]), {})
        if isinstance(v, Fraction):
            out.append(("value", v))
    elif kind == "say" and "truth" in cert:
        s = dec(cert["structure"])
        if s[0] == "rel" and s[1] in rv._CONVERSE:
            out.append(("pair", rv.evaluate(s[2], {}), rv.evaluate(s[3], {})))
    elif kind == "statement":
        s = dec(cert["second"])
        if s[0] == "rel" and s[1] == "=" and not rv._variables(s[3]):
            out.append(("value", rv.evaluate(s[3], {})))
    elif kind == "bounds":
        for part in rv._conjuncts(dec(cert["answer"])):
            if part[0] == "rel":
                out.append(("value", rv.evaluate(part[3], {})))
    elif kind == "entails" and "holds_at" in cert:
        stmts = [dec(p) for p in cert["premises"]] + [dec(cert["conclusion"])]
        vs = rv._variables(tuple(stmts))
        for key in ("holds_at", "fails_at"):
            env = {v: Fraction(0) for v in vs}
            env.update({v: Fraction(*map(int, x.split("/")))
                        for v, x in cert[key].items()})
            for s in stmts:
                for c in rv._clauses(s):
                    for r in c:
                        out.append(("pair", rv.evaluate(r[2], env),
                                    rv.evaluate(r[3], env)))
    return out


def _in_range(v: Fraction) -> bool:
    return abs(v.numerator) < RELAY_LIMIT and v.denominator < RELAY_LIMIT


def spelled(v: Fraction) -> str:
    """A rational as the planner's expression grammar writes it."""
    return str(v.numerator) if v.denominator == 1 else \
        f"{v.numerator}/{v.denominator}"


def nearest_decimal(v: Fraction, places: int) -> str:
    """The nearest decimal of ``v`` at ``places`` places, ties away from
    zero, exact."""
    q = (abs(v) * 10 ** places + Fraction(1, 2)) // 1
    digits = str(q).rjust(places + 1, "0")
    sign = "-" if v < 0 and q else ""
    return f"{sign}{digits[:-places]}.{digits[-places:]}"


def _number(s: str) -> Optional[Fraction]:
    if re.fullmatch(r"-?\d+", s):
        return Fraction(int(s))
    if re.fullmatch(r"-?\d+/\d+", s):
        n, d = s.split("/")
        return Fraction(int(n), int(d)) if int(d) else None
    m = re.fullmatch(r"(-?)(\d+)\.(\d+)", s)
    if not m:
        return None
    v = Fraction(int(m.group(2) + m.group(3)), 10 ** len(m.group(3)))
    return -v if m.group(1) else v


def _lit(v: Fraction):
    return ("lit", Fraction(v))


# ===========================================================================
# 2.  THE HANDOFFS AND THEIR ANSWER READERS
# ===========================================================================

def _questions(targets: Sequence[Tuple]) -> List[Tuple[str, Tuple, str]]:
    out = []
    for t in targets:
        if t[0] == "value":
            v = t[1]
            out.append(("approximate", t,
                        f"approximate {spelled(v)} to {RELAY_PLACES} places"))
            out.append(("recognise", t, "what fraction rounds to "
                        + nearest_decimal(v, RELAY_PLACES)))
        else:
            out.append(("compare", t,
                        f"is {spelled(t[1])} less than {spelled(t[2])}"))
    return out


def read_handoff(kind: str, target: Tuple, answer: str):
    """Read the planner's answer back into column 2: ``(status, statement)``
    where the statement is the planner's claim as a closed statement of the
    reverse grammar (``None`` when it could not be read)."""
    if kind == "approximate":
        v = target[1]
        m = re.match(r"(\S+) = (-?\d+\.\d+) \(to (\d+) places\)", answer)
        if not m:
            return "UNREAD", None
        d = _number(m.group(2))
        good = (_number(m.group(1)) == v and int(m.group(3)) == RELAY_PLACES
                and abs(d - v) < Fraction(1, 10 ** RELAY_PLACES))
        stmt = ("rel", "<", ("abs", ("sub", _lit(d), _lit(v))),
                _lit(Fraction(1, 10 ** RELAY_PLACES)))
        return ("AGREES" if good else "DISAGREES"), stmt
    if kind == "recognise":
        v = target[1]
        m = re.match(r"(-?\d+/\d+) is the simplest fraction that rounds to "
                     r"(\S+)", answer)
        if not m or _number(m.group(1)) is None:
            return "UNREAD", None
        f = _number(m.group(1))
        return ("AGREES" if f == v else "DISAGREES"), ("rel", "=", _lit(f),
                                                        _lit(v))
    x, y = target[1], target[2]
    m = re.match(r"(true|false): (\S+) ([<>]) (\S+)$", answer)
    if m:
        l, r = _number(m.group(2)), _number(m.group(4))
        if l is None or r is None:
            return "UNREAD", None
        good = {l, r} == {x, y} and ((m.group(3) == "<") == (l < r))
        return ("AGREES" if good else "DISAGREES"), ("rel", m.group(3),
                                                      _lit(l), _lit(r))
    if "not distinguished" in answer:
        return ("CONSISTENT" if x == y else "DISAGREES"), ("rel", "=",
                                                            _lit(x), _lit(y))
    return "UNREAD", None


# ===========================================================================
# 3.  THE RELAY
# ===========================================================================

def _inner(body: str) -> rv.Answer:
    if body.lower().startswith("relay:"):
        return rv._refused("relay", rv.ReverseRefusal(
            "UNREADABLE", "a relay of a relay"))
    if rv.reads(body):
        return rv.answer(body)
    return rv.say(body)


def relay(session, text: str) -> rv.Answer:
    """Answer ``relay: Q`` -- the reverse answer, handed to the planner and
    read back."""
    from .router import route
    body = text.strip()
    if body.lower().startswith("relay:"):
        body = body[len("relay:"):].strip()
    inner = _inner(body)
    if not inner.answered:
        out = rv._refused("relay", rv.ReverseRefusal(inner.refusal,
                                                     inner.reason))
        out.column1 = list(inner.column1)
        return out
    targets = relay_targets(inner.certificate)
    if not targets:
        return _with_inner(inner, rv.ReverseRefusal(
            "NOTHING_TO_RELAY", "the answer holds no closed value, relation "
            "or witness the planner can be asked about"))
    kept = [t for t in targets if all(_in_range(x) for x in t[1:])]
    if not kept:
        return _with_inner(inner, rv.ReverseRefusal(
            "OUT_OF_RANGE", "every value to hand off has a numerator or "
            f"denominator of {RELAY_LIMIT} or more"))
    s = _session(session)
    col1, col2 = list(inner.column1), list(inner.column2)
    handoffs, readback = [], []
    for kind, target, question in _questions(kept):
        r = route(s, question)
        status, stmt = read_handoff(kind, target, r.text)
        if r.surface != "planner":
            status = "UNREAD"
        handoffs.append({"type": kind, "question": question,
                         "surface": r.surface, "answer": r.text,
                         "status": status})
        readback.append(rv._enc(stmt) if stmt is not None else None)
        col1.append(f"handed to the planner: {question}")
        col1.append(f"the planner answers: {r.text}")
        if stmt is not None:
            col1.append(rv.realise(stmt))
            col2.append(rv._math(stmt) + f"  [{status}]")
    statuses = [h["status"] for h in handoffs]
    verdict = ("RELAYED" if all(x in ("AGREES", "CONSISTENT")
                                for x in statuses) else "DISAGREES")
    agree = sum(x == "AGREES" for x in statuses)
    cons = sum(x == "CONSISTENT" for x in statuses)
    col1.append(f"{agree} of {len(statuses)} handoffs agree"
                + (f", {cons} consistent" if cons else ""))
    cert = {"kind": "relay", "verdict": verdict, "inner": inner.certificate,
            "places": RELAY_PLACES, "limit": RELAY_LIMIT,
            "handoffs": handoffs, "readback": readback}
    return rv.Answer("relay", verdict, inner.sentence, col1, col2, cert)


def _with_inner(inner: rv.Answer, exc: rv.ReverseRefusal) -> rv.Answer:
    out = rv._refused("relay", exc)
    out.column1 = list(inner.column1) + out.column1
    return out


def answer_any(text: str, session=None) -> rv.Answer:
    """One reverse-surface question, ``relay:`` included."""
    if text.strip().lower().startswith("relay:"):
        return relay(session, text)
    return rv.answer(text)


# ===========================================================================
# 4.  THE MEASUREMENT OF W6 AND ITS CONTROLS
# ===========================================================================

def verbatim_control(session, answers) -> Dict[str, object]:
    """Control A: each relayed answer's column-1 sentence, given verbatim to
    the default path (the router)."""
    from .router import route
    rows = []
    for cid, a in answers:
        r = route(session, a.sentence)
        rows.append({"id": cid, "sentence": a.sentence, "surface": r.surface,
                     "answered": r.answered, "text": r.text[:160]})
    return {"sentences": len(rows),
            "answered": sum(1 for r in rows if r["answered"]), "rows": rows}


def planner_only_chain(session, values: Sequence[Fraction]) -> Dict[str, object]:
    """Control B: the planner chained to itself without column 2 -- its own
    ``approximate`` decimal handed to its own rational recognition.

    The recognition reads a decimal of N places as the interval of half a
    unit in the last place around it, and answers a fraction inside that
    interval.  So when the planner's decimal leaves ``v`` outside that
    interval the chain cannot give ``v`` back, whatever the recogniser
    returns; the recogniser is asked only where the chain can recover
    (``RequestProject/GLM/ReverseTCTTwo.lean``, ``chain_floor_misses``, is
    the fact for 2/3)."""
    from .router import route
    half = Fraction(1, 2 * 10 ** RELAY_PLACES)
    rows = []
    for v in values:
        r1 = route(session, f"approximate {spelled(v)} to {RELAY_PLACES} "
                            "places")
        m = re.match(r"\S+ = (-?\d+\.\d+) ", r1.text)
        decimal = m.group(1) if m else None
        d = _number(decimal) if decimal else None
        inside = d is not None and abs(d - v) <= half
        back = None
        if inside:
            r2 = route(session, f"what fraction rounds to {decimal}")
            m2 = re.match(r"(-?\d+/\d+) is the simplest", r2.text)
            back = _number(m2.group(1)) if m2 else None
        rows.append({"value": spelled(v), "decimal": decimal,
                     "value_in_interval": inside,
                     "back": spelled(back) if back is not None else None,
                     "recovered": back == v})
    return {"values": len(rows),
            "recoverable": sum(1 for r in rows if r["value_in_interval"]),
            "recovered": sum(1 for r in rows if r["recovered"]), "rows": rows}


def relay_report(session=None) -> Dict[str, object]:
    """W6: every declared relay case, its handoffs, and the two controls."""
    from ..evaluation import reverse_tct_two_cases as C
    s = _session(session)
    rows, relayed = [], []
    handoffs = statuses_ok = disagree = questions_back = 0
    for cid, question, want in C.RELAY_CASES:
        a = relay(s, question)
        got = a.verdict
        hs = a.certificate.get("handoffs", []) if a.answered else []
        handoffs += len(hs)
        for h in hs:
            statuses_ok += (h["surface"] == "planner"
                            and h["status"] in ("AGREES", "CONSISTENT"))
            disagree += h["status"] == "DISAGREES"
        for (kind, target, q), h in zip(
                _questions([t for t in relay_targets(a.certificate["inner"])
                            if all(_in_range(x) for x in t[1:])])
                if a.answered else [], hs):
            questions_back += q == h["question"] and _reads_back(kind,
                                                                  target, q)
        if a.answered:
            relayed.append((cid, a))
        rows.append({"id": cid, "verdict": got, "want": want,
                     "right": got == want, "handoffs": len(hs),
                     "statuses": [h["status"] for h in hs]})
    inner_answers = []
    values = []
    for cid, a in relayed:
        inner_answers.append((cid, a))
        for t in relay_targets(a.certificate["inner"]):
            if t[0] == "value" and _in_range(t[1]):
                values.append(t[1])
    return {"cases": len(rows), "right": sum(r["right"] for r in rows),
            "wrong": [r["id"] for r in rows if not r["right"]],
            "handoffs": handoffs, "handoffs_ok": statuses_ok,
            "disagrees": disagree, "questions_read_back": questions_back,
            "rows": rows,
            "control_verbatim": verbatim_control(s, inner_answers),
            "control_chain": planner_only_chain(s, values)}


def _reads_back(kind: str, target: Tuple, question: str) -> bool:
    """A handoff question reads back to its column-2 value(s)."""
    if kind == "approximate":
        m = re.fullmatch(r"approximate (\S+) to (\d+) places", question)
        return bool(m) and _number(m.group(1)) == target[1]
    if kind == "recognise":
        m = re.fullmatch(r"what fraction rounds to (\S+)", question)
        return bool(m) and abs(_number(m.group(1)) - target[1]) <= Fraction(
            1, 2 * 10 ** RELAY_PLACES)
    m = re.fullmatch(r"is (\S+) less than (\S+)", question)
    return bool(m) and (_number(m.group(1)), _number(m.group(2))) == (
        target[1], target[2])
