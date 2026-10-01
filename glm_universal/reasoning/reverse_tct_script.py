"""``glm_universal.reasoning.reverse_tct_script`` -- column 3 of Reverse TCT.

The script that checks a generated language column, the certificate mutation
that shows the script can fail, the infix control realiser and the V1/V2
battery of ``studies/REVERSE_TCT_STUDY.md``, and the study's in-process
report.  The script re-reads every column-1 sentence with the declared
reader, ties every structure the certificate is about to a sentence of
column 1, and re-checks the certificate with its own evaluator -- never the
operation's code.  Running it is the runtime's job
(:func:`glm_universal.runtime.python_tct.reverse_scripts`).
"""

from __future__ import annotations

import json
import re
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from .reverse_tct import (Answer, ReverseRefusal, _CONVERSE, _NEGATION,
                          _dec, _enc, _from_clauses, _is_statement,
                          _lit_words, _q,
                          _variables, bounds, entails, equivalent, evaluate,
                          from_source, holds, negate, number_words,
                          paraphrase, read, realise, say, solve)

__all__ = ["render_script", "mutated_script", "infix_realise",
           "battery_terms", "reverse_report", "reverse_two_report",
           "wide_battery", "cnf_battery", "negation_battery"]


# ===========================================================================
# 10.  COLUMN 3 -- THE SCRIPT THAT CHECKS COLUMN 1
# ===========================================================================

_SCRIPT = r'''"""Column 3 of a Reverse Three Column Thinking answer -- generated.

Re-reads every column-1 sentence with the declared reader, compares it with
the column-2 structure, and re-checks the certificate with its own exact
arithmetic (a separate evaluator, not the operation's code).  Prints
VERIFIED True only if everything holds.
"""
import itertools
import json
import re
import sys
from fractions import Fraction

sys.path.insert(0, @@ROOT@@)
from glm_universal.reasoning import reverse_tct as rt

DATA = json.loads(@@DATA@@)


def F(s):
    n, d = s.split("/")
    return Fraction(int(n), int(d))


def as_int(v):
    assert isinstance(v, Fraction) and v.denominator == 1, "not an integer"
    return v.numerator


def ev(t, env):
    k = t[0]
    if k == "lit":
        return F(t[1])
    if k == "var":
        return env[t[1]]
    if k == "mask":
        assert all(0 <= p < 24 for p in t[1])
        return frozenset(t[1])
    if k == "neg":
        return -ev(t[1], env)
    if k == "abs":
        return abs(ev(t[1], env))
    if k == "compl":
        return Fraction(-as_int(ev(t[1], env)) - 1)
    if k == "size":
        return Fraction(len(ev(t[1], env)))
    if k == "pow":
        b = ev(t[1], env)
        if t[2] < 0 and b == 0:
            raise ZeroDivisionError
        return b ** t[2]
    a, b = ev(t[1], env), ev(t[2], env)
    if k == "add":
        return a + b
    if k == "sub":
        return a - b
    if k == "mul":
        return a * b
    if k == "min":
        return a if a <= b else b
    if k == "max":
        return a if a >= b else b
    if k == "inter":
        return frozenset(p for p in a if p in b)
    if k == "union":
        return frozenset(list(a) + list(b))
    if k == "symdiff":
        return frozenset([p for p in a if p not in b] +
                         [p for p in b if p not in a])
    if k == "setdiff":
        return frozenset(p for p in a if p not in b)
    if k == "dist":
        return Fraction(len([p for p in a if p not in b]) +
                        len([p for p in b if p not in a]))
    if k in ("band", "bor", "bxor"):
        x, y = as_int(a), as_int(b)
        bits = max(x.bit_length(), y.bit_length()) + 2
        mx, my = x % (1 << bits), y % (1 << bits)
        out = 0
        for i in range(bits):
            p, q = (mx >> i) & 1, (my >> i) & 1
            r = {"band": p and q, "bor": p or q, "bxor": p != q}[k]
            out |= int(r) << i
        if out >> (bits - 1):
            out -= 1 << bits
        return Fraction(out)
    if k in ("lshift", "rshift"):
        x, n = as_int(a), as_int(b)
        assert n >= 0, "a negative shift"
        return Fraction(x * 2 ** n) if k == "lshift" else Fraction(
            x // 2 ** n)
    if b == 0:
        raise ZeroDivisionError
    if k == "div":
        return a / b
    if k == "floordiv":
        return Fraction((a / b).__floor__())
    if k == "mod":
        return a - b * (a / b).__floor__()
    raise ValueError(k)


def names(t, out):
    if isinstance(t, list):
        if len(t) == 2 and t[0] == "var":
            out.add(t[1])
        for x in t:
            names(x, out)
    return out


def deg(t):
    if not names(t, set()):
        return 0
    k = t[0]
    if k == "var":
        return 1
    if k == "neg":
        return deg(t[1])
    if k == "pow":
        assert t[2] >= 0, "a negative power of a variable term"
        return t[2] * deg(t[1])
    if k in ("add", "sub"):
        return max(deg(t[1]), deg(t[2]))
    if k == "mul":
        return deg(t[1]) + deg(t[2])
    assert k == "div" and not names(t[2], set()), "not a polynomial"
    return deg(t[1])


def rel_holds(op, a, b):
    if op == "in":
        return a in b
    if op == "notin":
        return a not in b
    if op == "sub":
        return all(p in b for p in a)
    if op == "notsub":
        return not all(p in b for p in a)
    return {"=": a == b, "!=": a != b, "<": a < b, "<=": a <= b,
            ">": a > b, ">=": a >= b}[op]


def holds(s, env):
    if s[0] == "free":
        return True
    if s[0] == "and":
        return all(holds(r, env) for r in s[1])
    if s[0] == "or":
        return any(holds(r, env) for r in s[1])
    return rel_holds(s[1], ev(s[2], env), ev(s[3], env))


def identical(f, g, vs, d):
    """f == g as polynomials: equal on the grid {0..d}^n suffices."""
    for pt in itertools.product(range(d + 1), repeat=len(vs)):
        env = dict(zip(vs, map(Fraction, pt)))
        if f(env) != g(env):
            return False
    return True


def affine(t, vs):
    """Coefficients of an affine term, taken by evaluation, then checked."""
    zero = {v: Fraction(0) for v in vs}
    c0 = ev(t, zero)
    co = {}
    for v in vs:
        e = dict(zero)
        e[v] = Fraction(1)
        co[v] = ev(t, e) - c0
    # affine exactly: equal to its interpolation on the grid {0..d}^n, d the
    # syntactic degree bound (the polynomial identity check)
    assert identical(lambda e: ev(t, e),
                     lambda e: c0 + sum(co[v] * e[v] for v in vs), vs,
                     max(deg(t), 1)), "not affine"
    return co, c0


def farkas(rows, lam, vs):
    """rows [op, lhs, rhs] with op in < <= > >= =; non-negative weights on
    their <=-rows refute the system."""
    flat = []
    for op, a, b in rows:
        ca, ka = affine(a, vs)
        cb, kb = affine(b, vs)
        d = {v: ca[v] - cb[v] for v in vs}
        k = ka - kb
        neg = ({v: -c for v, c in d.items()}, -k)
        if op == "<":
            flat.append((d, k, True))
        elif op == "<=":
            flat.append((d, k, False))
        elif op == ">":
            flat.append((neg[0], neg[1], True))
        elif op == ">=":
            flat.append((neg[0], neg[1], False))
        elif op == "=":
            flat += [(d, k, False), (neg[0], neg[1], False)]
        else:
            return False
    lam = [F(x) for x in lam]
    assert len(lam) == len(flat) and all(x >= 0 for x in lam)
    for v in vs:
        assert sum(l * r[0][v] for l, r in zip(lam, flat)) == 0
    total = sum(l * r[1] for l, r in zip(lam, flat))
    strict = any(l > 0 and r[2] for l, r in zip(lam, flat))
    return total > 0 or (strict and total >= 0)


def clauses(s):
    if s[0] == "rel":
        return [[s]]
    if s[0] == "or":
        return [list(s[1])]
    if s[0] == "and":
        return [c for x in s[1] for c in clauses(x)]
    return []


def conj(s):
    return s[1] if s[0] == "and" else [s]


def from_clauses(cs):
    items = [c[0] if len(c) == 1 else ["or", list(c)] for c in cs]
    return items[0] if len(items) == 1 else ["and", items]


NEG = {"=": "!=", "!=": "=", "<": ">=", "<=": ">", ">": "<=", ">=": "<",
       "in": "notin", "notin": "in", "sub": "notsub", "notsub": "sub"}
CONV = {"=": "=", "!=": "!=", "<": ">", "<=": ">=", ">": "<", ">=": "<="}
ZERO = ["lit", "0/1"]


def pw(t):
    if not isinstance(t, list) or not t or t[0] in ("lit", "var", "mask"):
        return None
    if t[0] in ("abs", "min", "max") and names(t, set()):
        return t
    for x in t[1:]:
        if isinstance(x, list):
            got = pw(x)
            if got is not None:
                return got
    return None


def replace(t, node, by):
    if t == node:
        return by
    if not isinstance(t, list) or not t or t[0] in ("lit", "var", "mask"):
        return t
    return [replace(x, node, by) if isinstance(x, list) else x for x in t]


def pieces(case):
    n = None
    for op, a, b in case:
        n = pw(a) or pw(b)
        if n is not None:
            break
    if n is None:
        return [case]
    if n[0] == "abs":
        br = [([">=", n[1], ZERO], n[1]), (["<", n[1], ZERO], ["neg", n[1]])]
    elif n[0] == "min":
        br = [(["<=", n[1], n[2]], n[1]), ([">", n[1], n[2]], n[2])]
    else:
        br = [([">=", n[1], n[2]], n[1]), (["<", n[1], n[2]], n[2])]
    out = []
    for cond, by in br:
        out += pieces([[op, replace(a, n, by), replace(b, n, by)]
                       for op, a, b in case] + [cond])
    return out


def expected_cases(stmts):
    choices = []
    for s in stmts:
        for c in clauses(s):
            alts = []
            for r in c:
                if r[1] == "!=":
                    alts += [["<", r[2], r[3]], [">", r[2], r[3]]]
                else:
                    alts.append([r[1], r[2], r[3]])
            choices.append(alts)
    out = []
    for combo in itertools.product(*choices):
        out += pieces([list(x) for x in combo])
    return out


def refutes_all(stmts, certs, vs):
    want = expected_cases(stmts)
    if len(want) != len(certs):
        return False
    for case, cert in zip(want, certs):
        if cert["rows"] != case:
            return False
        if not farkas(cert["rows"], cert["multipliers"], vs):
            return False
    return True


def entailed(premises, conclusion, certs, vs):
    cs = clauses(conclusion)
    if len(cs) != len(certs):
        return False
    for c, cert in zip(cs, certs):
        negated = [["rel", NEG[r[1]], r[2], r[3]] for r in c]
        if cert["negated"] != negated or not refutes_all(
                premises + negated, cert["cases"], vs):
            return False
    return True


def point(p, vs):
    e = {v: Fraction(0) for v in vs}
    e.update({v: F(x) for v, x in p.items()})
    return e


def paired(s1, s2, pairing):
    c1, c2 = conj(s1), conj(s2)
    if len(c1) != len(c2) or len(pairing) != len(c1):
        return False
    if sorted(p[1] for p in pairing) != list(range(len(c2))):
        return False
    for i, j, k in pairing:
        a, b, k = c1[i], c2[j], F(k)
        if k == 0 or a[0] != "rel" or b[0] != "rel":
            return False
        if a[1] in ("=", "!="):
            if b[1] != a[1]:
                return False
        elif a[1] not in CONV or b[1] != (a[1] if k > 0 else CONV[a[1]]):
            return False
        vs = sorted(names(a, set()) | names(b, set()))
        d = max(deg(a[2]), deg(a[3]), deg(b[2]), deg(b[3]), 1)
        if not identical(lambda e: ev(a[2], e) - ev(a[3], e),
                         lambda e: k * (ev(b[2], e) - ev(b[3], e)), vs, d):
            return False
    return True


def statement_cert(c):
    s1, s2 = c["first"], c["second"]
    vs = sorted(names(s1, set()) | names(s2, set()))
    if "pairing" in c:
        return paired(s1, s2, c["pairing"])
    if "mutual" in c:
        return (entailed([s1], s2, c["mutual"][0], vs)
                and entailed([s2], s1, c["mutual"][1], vs))
    p = point(c["witness"], vs)
    return holds(s1, p) != holds(s2, p)


def term_cert(c):
    a, b = c["first"], c["second"]
    vs = sorted(names(a, set()) | names(b, set()))
    if c["kind"] == "term-pieces" and c["same"]:
        return entailed([], ["rel", "=", a, b], c["entails"], vs)
    if c["same"]:
        return identical(lambda e: ev(a, e), lambda e: ev(b, e), vs,
                         max(deg(a), deg(b), 1))
    p = point(c["witness"], vs)
    return ev(a, p) != ev(b, p)


def program_value(s):
    if s[0] == "prog":
        env = {}
        for n, t in s[1]:
            env[n] = ev(t, env)
        return ev(s[2], env)
    return ev(s, {})


def simplify(cs):
    out = []
    for c in cs:
        seen = []
        for r in c:
            if r not in seen:
                seen.append(r)
        out.append(seen)
    kept = [c for c in out
            if not any(["rel", NEG[r[1]], r[2], r[3]] in c for r in c)]
    out = kept if kept else out[:1]
    uniq = []
    for c in out:
        if not any(all(r in d for r in c) and all(r in c for r in d)
                   for d in uniq):
            uniq.append(c)
    return [c for i, c in enumerate(uniq)
            if not any(j != i and all(r in c for r in d) and
                       not all(r in d for r in c)
                       for j, d in enumerate(uniq))]


def negation(s):
    negs = [[["rel", NEG[r[1]], r[2], r[3]] for r in c] for c in clauses(s)]
    return from_clauses(simplify([list(x) for x in itertools.product(*negs)]))


# -- the relay: the planner's answers, re-read and re-checked -----------------

def nearest(v, places):
    """The nearest decimal of v at the given places (ties away from zero)."""
    scale = 10 ** places
    n = abs(v) * scale
    q = (n + Fraction(1, 2)).__floor__()
    sign = "-" if v < 0 and q else ""
    s = str(q).rjust(places + 1, "0")
    return f"{sign}{s[:-places]}.{s[-places:]}"


def number(s):
    """A number the planner writes: an integer, p/q, or a decimal."""
    if re.fullmatch(r"-?\d+", s):
        return Fraction(int(s))
    if re.fullmatch(r"-?\d+/\d+", s):
        n, d = s.split("/")
        return Fraction(int(n), int(d))
    m = re.fullmatch(r"(-?)(\d+)\.(\d+)", s)
    assert m, "not a number: " + s
    v = Fraction(int(m.group(2) + m.group(3)), 10 ** len(m.group(3)))
    return -v if m.group(1) else v


def spelled(v):
    return str(v.numerator) if v.denominator == 1 else \
        f"{v.numerator}/{v.denominator}"


def lit(v):
    return ["lit", f"{v.numerator}/{v.denominator}"]


def relay_targets(inner):
    """What the relay must hand off, re-derived from the inner certificate."""
    k = inner["kind"]
    out = []
    if k == "say" and "value" in inner:
        v = ev(inner["value"], {})
        if isinstance(v, Fraction):
            out.append(["value", v])
    elif k == "say" and "truth" in inner and inner["structure"][0] == "rel":
        s = inner["structure"]
        if s[1] in CONV:
            out.append(["pair", ev(s[2], {}), ev(s[3], {})])
    elif k == "statement" and inner["second"][0] == "rel" and \
            inner["second"][1] == "=" and not names(inner["second"][3], set()):
        out.append(["value", ev(inner["second"][3], {})])
    elif k == "bounds":
        for part in conj(inner["answer"]):
            if part[0] == "rel":
                out.append(["value", ev(part[3], {})])
    elif k == "entails" and "holds_at" in inner:
        stmts = inner["premises"] + [inner["conclusion"]]
        vs = sorted(names(stmts, set()))
        for key in ("holds_at", "fails_at"):
            p = point(inner[key], vs)
            for s in stmts:
                for c in clauses(s):
                    for r in c:
                        out.append(["pair", ev(r[2], p), ev(r[3], p)])
    return out


def in_range(v, limit):
    return abs(v.numerator) < limit and v.denominator < limit


def relay_check(c):
    if not check(c["inner"]):
        return False
    places, limit = c["places"], c["limit"]
    targets = [t for t in relay_targets(c["inner"])
               if all(in_range(x, limit) for x in t[1:])]
    hand = c["handoffs"]
    want = []
    for t in targets:
        if t[0] == "value":
            want += [("approximate", t[1]), ("recognise", t[1])]
        else:
            want.append(("compare", t[1], t[2]))
    if len(want) != len(hand) or len(hand) != len(c["readback"]):
        return False
    ok = True
    for w, h, back in zip(want, hand, c["readback"]):
        if h["surface"] != "planner" or h["type"] != w[0]:
            return False
        q, ans = h["question"], h["answer"]
        if w[0] == "approximate":
            v = w[1]
            m = re.fullmatch(r"approximate (\S+) to (\d+) places", q)
            ok = ok and bool(m) and number(m.group(1)) == v and \
                int(m.group(2)) == places
            a = re.match(r"(\S+) = (-?\d+\.\d+) \(to (\d+) places\)", ans)
            if not a:
                status, stmt = "UNREAD", None
            else:
                d = number(a.group(2))
                good = (a.group(1) == m.group(1) and int(a.group(3)) == places
                        and abs(d - v) < Fraction(1, 10 ** places))
                status = "AGREES" if good else "DISAGREES"
                stmt = ["rel", "<", ["abs", ["sub", lit(d), lit(v)]],
                        lit(Fraction(1, 10 ** places))]
        elif w[0] == "recognise":
            v = w[1]
            ok = ok and q == "what fraction rounds to " + nearest(v, places)
            a = re.match(r"(-?\d+/\d+) is the simplest fraction that rounds "
                         r"to (\S+)", ans)
            if not a:
                status, stmt = "UNREAD", None
            else:
                f = number(a.group(1))
                status = "AGREES" if f == v else "DISAGREES"
                stmt = ["rel", "=", lit(f), lit(v)]
        else:
            x, y = w[1], w[2]
            ok = ok and q == f"is {spelled(x)} less than {spelled(y)}"
            a = re.match(r"(true|false): (\S+) ([<>]) (\S+)$", ans)
            if a:
                l, r = number(a.group(2)), number(a.group(4))
                same = {l, r} == {x, y}
                good = same and ((a.group(3) == "<") == (l < r))
                status = "AGREES" if good else "DISAGREES"
                stmt = ["rel", a.group(3), lit(l), lit(r)]
            elif "not distinguished" in ans:
                status = "CONSISTENT" if x == y else "DISAGREES"
                stmt = ["rel", "=", lit(x), lit(y)]
            else:
                status, stmt = "UNREAD", None
        if status != h["status"] or stmt != back:
            return False
        if stmt is not None and not holds(stmt, {}):
            return False
    statuses = [h["status"] for h in hand]
    if c["verdict"] == "RELAYED":
        ok = ok and bool(hand) and all(s in ("AGREES", "CONSISTENT")
                                       for s in statuses)
    return ok


def check(c):
    k = c["kind"]
    if k == "say":
        s = c["structure"]
        if "value" in c and program_value(s) != ev(c["value"], {}):
            return False
        if "truth" in c and holds(s, {}) != c["truth"]:
            return False
        return True
    if k == "negate":
        return c["second"] == negation(c["first"])
    if k in ("term-identity", "term-pieces"):
        return term_cert(c)
    if k == "statement":
        return statement_cert(c)
    if k == "paraphrase":
        return all(p["certificate"]["first"] == c["original"]
                   and p["certificate"]["second"] == p["structure"]
                   and check(p["certificate"]) for p in c["paraphrases"])
    if k == "entails":
        ps, cc = c["premises"], c["conclusion"]
        vs = sorted(names(ps, set()) | names(cc, set()))
        if "inconsistent" in c:
            return refutes_all(ps, c["inconsistent"], vs)
        if "entails" in c:
            return entailed(ps, cc, c["entails"], vs)
        if "contradicts" in c:
            return refutes_all(ps + [cc], c["contradicts"], vs)
        h, f = point(c["holds_at"], vs), point(c["fails_at"], vs)
        return (all(holds(p, h) for p in ps) and holds(cc, h)
                and all(holds(p, f) for p in ps) and not holds(cc, f))
    if k == "bounds":
        ps = c["premises"]
        vs = sorted(names(ps, set()) | {c["var"]})
        ok = all(entailed(ps, e["bound"], e["certificates"], vs)
                 for e in c["entailed"])
        for a in c["attained"]:
            p = point(a["witness"], vs)
            b = a["bound"]
            ok = ok and all(holds(s, p) for s in ps) and \
                p[c["var"]] == ev(b[3], p)
        return ok
    if k == "relay":
        return relay_check(c)
    raise ValueError(k)


def claimed(c):
    """The statements and terms a certificate is about."""
    out = []
    for k in ("first", "second", "conclusion", "answer", "original",
              "structure"):
        if k in c:
            out.append(c[k])
    out += c.get("premises", [])
    for p in c.get("paraphrases", []):
        out.append(p["structure"])
    if c.get("kind") == "relay":
        out += claimed(c["inner"])
        out += [b for b in c["readback"] if b is not None]
    return out


ok = True
said = [structure for _, structure in DATA["read_back"]]
if DATA["certificate"]:
    for x in claimed(DATA["certificate"]):
        if x not in said and not any(x in y[1] for y in said
                                     if y and y[0] == "and"):
            print("NOT IN COLUMN 1", x)
            ok = False
for sentence, structure in DATA["read_back"]:
    got = rt._enc(rt.read(sentence))
    if got != structure or rt.realise(rt._dec(structure)) != sentence:
        print("MISMATCH", sentence)
        ok = False
if DATA["certificate"]:
    try:
        ok = ok and check(DATA["certificate"])
    except (AssertionError, ZeroDivisionError, KeyError) as exc:
        print("CHECK FAILED", type(exc).__name__, exc)
        ok = False
print("VERIFIED", ok)
sys.exit(0 if ok else 1)
'''


def _read_back_pairs(a: Answer) -> List[List[object]]:
    """Every column-1 sentence of the grammar, with its column-2 structure."""
    out = []
    for s in a.column1:
        try:
            out.append([s, _enc(read(s))])
        except ReverseRefusal:
            continue
    return out


def render_script(a: Answer, root: str, certificate=None) -> str:
    data = {"read_back": _read_back_pairs(a),
            "certificate": a.certificate if certificate is None
            else certificate}
    return (_SCRIPT.replace("@@ROOT@@", repr(root))
            .replace("@@DATA@@", repr(json.dumps(data, sort_keys=True))))


def _breaking_value(point: Dict[str, str], stmts) -> Optional[
        Dict[str, str]]:
    """A copy of ``point`` with one coordinate moved so that the pattern of
    which statements hold changes (a wrong witness), or ``None``."""
    env = {v: Fraction(*map(int, x.split("/"))) for v, x in point.items()}
    vs = sorted(set(env) | set(_variables(tuple(stmts))))
    for v in vs:
        env.setdefault(v, Fraction(0))

    def pattern(e):
        try:
            return tuple(holds(st, e) for st in stmts)
        except ReverseRefusal:
            return None
    want = pattern(env)
    for v in vs:
        for d in range(1, 30):
            for sign in (1, -1):
                e = dict(env)
                e[v] = env[v] + sign * Fraction(d, 2)
                if pattern(e) != want and pattern(e) is not None:
                    out = dict(point)
                    out[v] = _q(e[v])
                    return out
    return None


def _mutate(c):
    """A copy of a certificate with one entry changed so that it no longer
    certifies its claim, or ``None`` when there is nothing to change."""
    c = json.loads(json.dumps(c))
    kind = c.get("kind")

    def first_rel(t):
        if isinstance(t, list) and t and t[0] == "rel":
            return t
        if isinstance(t, list) and t and t[0] in ("and", "or"):
            return first_rel(t[1][0])
        return None

    def flip_claim(x) -> bool:
        for k in ("second", "conclusion", "answer", "structure", "first"):
            t = x.get(k)
            r = first_rel(t)
            if r is not None:
                r[1] = _NEGATION[r[1]]
                return True
            if isinstance(t, list) and t and t[0] in ("add", "sub", "mul",
                                                      "div"):
                t[0] = {"add": "sub", "sub": "add", "mul": "add",
                        "div": "mul"}[t[0]]
                return True
        return False

    def multipliers(x) -> bool:
        if isinstance(x, dict):
            if x.get("multipliers"):
                m = x["multipliers"]
                i = max(range(len(m)), key=lambda j: Fraction(
                    *map(int, m[j].split("/"))))
                m[i] = "0/1"
                return True
            return any(multipliers(x[k]) for k in sorted(x))
        if isinstance(x, list):
            return any(multipliers(y) for y in x)
        return False

    if kind == "say":
        if "truth" in c:
            c["truth"] = not c["truth"]
            return c
        v = c.get("value")
        if v is None:
            return None
        if v[0] == "mask":
            v[1] = sorted(set(v[1]).symmetric_difference({0}))
        else:
            v[1] = _q(Fraction(*map(int, v[1].split("/"))) + 1)
        return c
    if kind == "relay":
        for h in c["handoffs"]:
            if "not distinguished" in h["answer"]:
                field_, text = "question", h["question"]
                m = re.search(r"-?\d+(/\d+)?", text[3:])
                start = 3
            else:
                field_, text = "answer", h["answer"]
                start = text.rfind(" = ") + 3 if " = " in text else 0
                m = re.search(r"-?\d+(\.\d+|/\d+)?", text[start:])
            if m is None:
                continue
            s = m.group(0)
            if "." in s:
                s2 = s[:-1] + str((int(s[-1]) + 5) % 10)
            elif "/" in s:
                n, d = s.split("/")
                s2 = f"{int(n) + 1}/{d}"
            else:
                s2 = str(int(s) + 1)
            at = start + m.start()
            h[field_] = text[:at] + s2 + text[at + len(s):]
            return c
        return None
    if kind == "term-pieces" and "witness" in c:
        stmts = [("rel", "=", _dec(c["first"]), _dec(c["second"]))]
        got = _breaking_value(c["witness"], stmts)
        if got is not None:
            c["witness"] = got
            return c
    if kind == "term-pieces" and multipliers(c):
        return c
    if kind == "entails" and "holds_at" in c:
        ps = [_dec(p) for p in c["premises"]]
        stmts = ps + [_dec(c["conclusion"])]
        got = _breaking_value(c["holds_at"], stmts)
        if got is not None:
            c["holds_at"] = got
            return c
    if kind == "paraphrase":
        for p in c["paraphrases"]:
            inner = _mutate(p["certificate"])
            if inner is not None:
                p["certificate"] = inner
                return c
        return None
    if kind in ("entails", "bounds") and multipliers(c):
        return c
    if kind == "statement" and "witness" in c:
        stmts = [_dec(c["first"]), _dec(c["second"])]
        got = _breaking_value(c["witness"], stmts)
        if got is not None:
            c["witness"] = got
            return c
    if kind == "statement" and "mutual" in c and multipliers(c):
        return c
    return c if flip_claim(c) else None


def mutated_script(a: Answer, root: str) -> Optional[str]:
    """The same script with a mutated certificate, or ``None`` when the
    answer carries no number to mutate."""
    m = _mutate(a.certificate)
    if m is None:
        return None
    return render_script(a, root, m)


# ===========================================================================
# 11.  THE CONTROL AND THE BATTERY
# ===========================================================================

def infix_realise(t) -> str:
    """The natural infix control: no scope words (``two plus x times y``)."""
    k = t[0]
    if k == "lit":
        return " ".join(_lit_words(t[1]))
    if k == "var":
        return t[1]
    if k == "neg":
        return "minus " + infix_realise(t[1])
    if k == "pow":
        return f"{infix_realise(t[1])} to the {' '.join(number_words(t[2]))}"
    word = {"add": "plus", "sub": "minus", "mul": "times",
            "div": "divided by"}[k]
    return f"{infix_realise(t[1])} {word} {infix_realise(t[2])}"


def battery_terms(atoms: Sequence[str], depth: int) -> List:
    """Every term of depth at most ``depth`` over the atoms."""
    level = [from_source(a) for a in atoms]
    allt = list(level)
    for _ in range(depth):
        new = [("neg", t) for t in allt]
        for k in ("add", "sub", "mul", "div"):
            for a in allt:
                for b in allt:
                    new.append((k, a, b))
        allt = list(level) + new
    seen, out = set(), []
    for t in allt:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def reverse_report() -> Dict[str, object]:
    """The study's measurements that need no subprocess (V1, V2, V4-V6, V8
    counts); the script checks (V3) are taken by
    :func:`glm_universal.runtime.python_tct.reverse_scripts`."""
    from ..evaluation import reverse_tct_cases as C
    from . import python_speech as sp
    out: Dict[str, object] = {}
    terms = battery_terms(C.BATTERY_ATOMS, C.BATTERY_DEPTH)
    sentences: Dict[str, object] = {}
    infix: Dict[str, object] = {}
    trips = collisions = infix_collisions = 0
    for t in terms:
        s = realise(t)
        if read(s) == t:
            trips += 1
        if s in sentences and sentences[s] != t:
            collisions += 1
        sentences[s] = t
        i = infix_realise(t)
        if i in infix and infix[i] != t:
            infix_collisions += 1
        infix.setdefault(i, t)
    out["battery"] = {"terms": len(terms), "round_trips": trips,
                      "collisions": collisions,
                      "infix_collisions": infix_collisions,
                      "infix_distinct_sentences": len(infix)}
    say_ok = sum(1 for _, src, want in C.SAY_CASES
                 if say(src).sentence == want
                 and read(want) == from_source(src))
    sup = _superseded()
    say_ref = sum(1 for cid, src, name in C.SAY_REFUSALS
                  if (say(src).sentence if ("SAY_REFUSALS", cid) in sup
                      else say(src).refusal)
                  == sup.get(("SAY_REFUSALS", cid), name))
    read_ref = 0
    for _, s in C.READ_REFUSALS:
        try:
            read(s)
        except ReverseRefusal as exc:
            read_ref += exc.name == "UNREADABLE"
    out["say"] = {"sentences": say_ok, "of": len(C.SAY_CASES),
                  "refusals": say_ref, "refusals_of": len(C.SAY_REFUSALS),
                  "unreadable": read_ref, "unreadable_of": len(C.READ_REFUSALS)}

    def score(rows):
        right = wrong = 0
        wrong_ids = []
        for cid, got, want in rows:
            if got == want:
                right += 1
            else:
                wrong += 1
                wrong_ids.append(cid)
        return {"right": right, "wrong": wrong, "of": len(rows),
                "wrong_ids": wrong_ids}
    out["entails"] = score([(cid, entails(list(ps), c).verdict, want)
                            for cid, ps, c, want in C.ENTAIL_CASES])
    out["solve"] = score([(cid, (lambda a: a.sentence if a.answered
                                 else a.refusal)(solve(v, s)), want)
                          for cid, v, s, want in C.SOLVE_CASES])
    out["bounds"] = score([(cid, (lambda a: a.sentence if a.answered
                                  else a.refusal)(bounds(v, list(ps))), want)
                           for cid, v, ps, want in C.BOUNDS_CASES])
    out["equivalent"] = score([(cid, equivalent(a, b).verdict, want)
                               for cid, a, b, want in C.EQUIVALENCE_CASES])
    out["negate"] = score([(cid, (lambda a: a.sentence if a.answered
                                  else a.refusal)(negate(s)),
                            sup.get(("NEGATE_CASES", cid), want))
                           for cid, s, want in C.NEGATE_CASES])
    para = []
    for cid, s in C.PARAPHRASE_CASES:
        a = paraphrase(s)
        para.append({"id": cid, "paraphrases": len(a.column1) - 1,
                     "certified": a.answered})
    out["paraphrase"] = {"cases": para,
                         "all_at_least_two": all(p["paraphrases"] >= 2
                                                 for p in para),
                         "all_certified": all(p["certified"] for p in para)}
    # V8 -- the dialect's value programs inside the fragment
    inside = agree = 0
    outside: List[str] = []
    from ..evaluation import python_speech_cases as pc
    for cid, src in pc.VALUE_CASES:
        try:
            obj = from_source(src)
        except ReverseRefusal:
            outside.append(cid)
            continue
        if _variables(obj) and obj[0] != "prog":
            outside.append(cid)
            continue
        inside += 1
        back = read(realise(obj))
        p = sp.speak(src)
        try:
            mine = _closed_value(back)
        except ReverseRefusal:
            continue
        agree += int(p.answered and _same_value(p.value, mine))
    out["dialect"] = {"inside": inside, "agree": agree,
                      "of": len(pc.VALUE_CASES), "outside": len(outside)}
    return out


def _closed_value(obj):
    if obj[0] == "prog":
        env: Dict[str, Fraction] = {}
        for n, t in obj[1]:
            env[n] = evaluate(t, env)
        return evaluate(obj[2], env)
    if _is_statement(obj):
        return holds(obj, {})
    return evaluate(obj, {})


def _same_value(dialect_value, mine) -> bool:
    if isinstance(mine, frozenset):
        return isinstance(dialect_value, frozenset) and dialect_value == mine
    if isinstance(mine, bool):
        return dialect_value is mine
    if isinstance(dialect_value, bool):
        return False
    try:
        return Fraction(dialect_value) == mine
    except (TypeError, ValueError):
        return False


# ===========================================================================
# 12.  ROUND TWO (Phase 68) -- W1-W4 and W8 of the study's §7.2
# ===========================================================================

#: The unary and binary operators of the widened battery (W1).
WIDE_UNARY: Tuple[str, ...] = ("neg", "abs", "compl")
WIDE_BINARY: Tuple[str, ...] = ("add", "sub", "mul", "div", "floordiv", "mod",
                                "min", "max", "band", "bor", "bxor", "lshift",
                                "rshift")
MASK_BINARY: Tuple[str, ...] = ("inter", "union", "symdiff", "setdiff")

#: W3: the relations the conjunctive-normal-form battery is built from, and
#: the grid the negation is checked on.
CNF_RELATIONS: Tuple[str, ...] = ("x < 0", "x >= 1", "y == 2", "x + y != 1",
                                  "x - y <= 3")
CNF_GRID: Tuple[Fraction, ...] = tuple(Fraction(n, 2) for n in range(-4, 7))


def wide_battery(atoms: Sequence[str], depth: int, unary: Sequence[str],
                 binary: Sequence[str]) -> List:
    """Every term of depth at most ``depth`` over the atoms."""
    level = [from_source(a) for a in atoms]
    allt = list(level)
    for _ in range(depth):
        new = [(k, t) for k in unary for t in allt]
        for k in binary:
            for a in allt:
                for b in allt:
                    new.append((k, a, b))
        allt = list(level) + new
    seen, out = set(), []
    for t in allt:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _round_trip(terms) -> Dict[str, int]:
    sentences: Dict[str, object] = {}
    trips = collisions = 0
    for t in terms:
        s = realise(t)
        if read(s) == t:
            trips += 1
        if s in sentences and sentences[s] != t:
            collisions += 1
        sentences[s] = t
    return {"terms": len(terms), "round_trips": trips,
            "collisions": collisions}


def cnf_battery() -> List:
    """W3: every conjunctive normal form of one or two clauses, each clause
    one relation or an ordered pair of distinct relations of
    :data:`CNF_RELATIONS`."""
    rels = [from_source(r) for r in CNF_RELATIONS]
    clauses = [[r] for r in rels] + [[a, b] for a in rels for b in rels
                                     if a != b]
    out = []
    for c in clauses:
        out.append(_from_clauses([c]))
    for c in clauses:
        for d in clauses:
            out.append(_from_clauses([c, d]))
    return out


def negation_battery() -> Dict[str, object]:
    """W3: for every battery statement, the negation is answered, its double
    negation is certified equivalent, and the negation holds exactly where
    the statement fails on the grid."""
    import itertools as it
    from .reverse_tct import negation_of
    stmts = cnf_battery()
    answered = double_ok = grid_ok = 0
    failures: List[str] = []
    for s in stmts:
        text = realise(s)
        a = negate(text)
        if not a.answered:
            failures.append(text)
            continue
        answered += 1
        n = read(a.sentence)
        nn = negation_of(n)
        if equivalent(realise(nn), text).verdict == "SAME":
            double_ok += 1
        else:
            failures.append(text)
        good = all(holds(n, {"x": x, "y": y}) != holds(s, {"x": x, "y": y})
                   for x, y in it.product(CNF_GRID, repeat=2))
        grid_ok += good
        if not good:
            failures.append(text)
    return {"statements": len(stmts), "answered": answered,
            "double_negation_certified": double_ok, "grid_exact": grid_ok,
            "grid_points": len(CNF_GRID) ** 2, "failures": failures}


def _superseded() -> Dict[Tuple[str, str], str]:
    from ..evaluation import reverse_tct_two_cases as C2
    return {(c, i): w for c, i, w in C2.SUPERSEDED}


def reverse_two_report(batteries: bool = True) -> Dict[str, object]:
    """Round two's measurements that need no subprocess and no planner
    (W1-W4, W8); the scripts (W5) are taken by
    :func:`glm_universal.runtime.python_tct.reverse_two_scripts` and the
    loop (W6) by :func:`glm_universal.runtime.reverse_relay.relay_report`."""
    from ..evaluation import python_speech_cases as pc
    from ..evaluation import reverse_tct_cases as C1
    from ..evaluation import reverse_tct_two_cases as C
    from . import python_speech as sp
    out: Dict[str, object] = {}

    def got(a):
        return a.sentence if a.answered else a.refusal

    def score(rows):
        wrong = [cid for cid, g, w in rows if g != w]
        return {"right": len(rows) - len(wrong), "wrong": len(wrong),
                "of": len(rows), "wrong_ids": wrong}
    # W1
    if batteries:
        out["wide_battery"] = _round_trip(wide_battery(
            C.WIDE_BATTERY_ATOMS, C.WIDE_BATTERY_DEPTH, WIDE_UNARY,
            WIDE_BINARY))
        out["mask_battery"] = _round_trip(wide_battery(
            C.MASK_BATTERY_ATOMS, 2, (), MASK_BINARY))
    say_rows = [(cid, got(say(src)), want) for cid, src, want in C.SAY_CASES]
    read_back = sum(1 for _, src, want in C.SAY_CASES
                    if read(want) == from_source(src))
    ref_rows = [(cid, say(src).refusal, want)
                for cid, src, want in C.SAY_REFUSALS]
    unreadable = 0
    for _, s in C.READ_REFUSALS:
        try:
            read(s)
        except ReverseRefusal as exc:
            unreadable += exc.name == "UNREADABLE"
    out["say"] = dict(score(say_rows), read_back=read_back)
    out["say_refusals"] = score(ref_rows)
    out["unreadable"] = {"right": unreadable, "of": len(C.READ_REFUSALS)}
    # W2
    inside, agree, wrong_ids = [], 0, []
    listed = set(C.DIALECT_INSIDE)
    for cid, src in pc.VALUE_CASES:
        try:
            obj = from_source(src)
        except ReverseRefusal:
            continue
        if _variables(obj) and obj[0] != "prog":
            continue
        inside.append(cid)
        back = read(realise(obj))
        p = sp.speak(src)
        try:
            mine = _closed_value(back) if back == obj else None
        except ReverseRefusal:
            mine = None
        ok = mine is not None and p.answered and _same_value(p.value, mine)
        agree += ok
        if not ok:
            wrong_ids.append(cid)
    out["dialect"] = {"inside": len(inside), "of": len(pc.VALUE_CASES),
                      "agree": agree, "wrong_ids": wrong_ids,
                      "listed": len(listed),
                      "listed_inside": len(listed & set(inside)),
                      "unlisted_inside": sorted(set(inside) - listed)}
    # W3
    out["negate"] = score([(cid, got(negate(s)), want)
                           for cid, s, want in C.NEGATE_CASES])
    if batteries:
        out["negation_battery"] = negation_battery()
    # W4
    out["entails"] = score([(cid, entails(list(ps), c).verdict, want)
                            for cid, ps, c, want in C.ENTAIL_CASES])
    out["bounds"] = score([(cid, got(bounds(v, list(ps))), want)
                           for cid, v, ps, want in C.BOUNDS_CASES])
    out["equivalent"] = score([(cid, equivalent(a, b).verdict, want)
                               for cid, a, b, want in C.EQUIVALENCE_CASES])
    # W8
    sup = _superseded()
    rows = []
    for cid, src, want in C1.SAY_CASES:
        rows.append((f"say:{cid}", say(src).sentence, want))
    for cid, src, want in C1.SAY_REFUSALS:
        rows.append((f"say-refusal:{cid}", got(say(src)),
                     sup.get(("SAY_REFUSALS", cid), want)))
    for cid, ps, c, want in C1.ENTAIL_CASES:
        rows.append((cid, entails(list(ps), c).verdict, want))
    for cid, v, s, want in C1.SOLVE_CASES:
        rows.append((cid, got(solve(v, s)), want))
    for cid, v, ps, want in C1.BOUNDS_CASES:
        rows.append((cid, got(bounds(v, list(ps))), want))
    for cid, a, b, want in C1.EQUIVALENCE_CASES:
        rows.append((cid, equivalent(a, b).verdict, want))
    for cid, s, want in C1.NEGATE_CASES:
        rows.append((cid, got(negate(s)), sup.get(("NEGATE_CASES", cid),
                                                  want)))
    out["phase67"] = dict(score(rows), superseded=len(sup))
    return out
