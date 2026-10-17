"""``glm_universal.reasoning.batch_speech`` -- GLM-BAT learnt as a language.

Three things, so that the machine of :mod:`batch_machine` is something the
GLM *speaks* rather than a sandbox it calls:

* **sentences** -- every instruction has exactly one English sentence,
  generated from the parsed instruction (:func:`say_line`), and the sentence
  reads back to exactly that instruction (:func:`read_sentence`).  A program
  may be written in either form (:func:`read_program`);
* **questions** -- *what does it print*, *does it halt*, *is it idempotent*,
  *which lines are unreachable*, *what does it use* … asked in English about a
  program, answered from a run or from the program's text, or refused by name
  (:func:`answer`);
* **column 3** -- every answer carries a stand-alone Python script that
  re-derives it with a *second, separately written* interpreter of the same
  fragment and asserts it; the script is run under ``python3 -I`` before the
  answer is given, and every mutation of the claim must make it fail
  (:func:`column3_script`, :func:`mutations`).

Exact and deterministic (D7).  ``studies/OPERATIONS_LADDER_STUDY.md`` §2.3.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from . import batch_machine as bm

__all__ = [
    "say_line", "say_program", "read_sentence", "read_english",
    "read_program", "split_sentences", "Answer", "answer", "column3_script",
    "run_script", "mutations", "never_claim", "REFUSALS", "say_shift", "say_growth",
    "say_jumps", "output_runs", "decode_runs", "say_runs", "growth_claim",
    "say_diagnosis", "RUN_FORM_LINES",
]

#: Every refusal this surface can give, by name.
REFUSALS: Tuple[str, ...] = ("UNKNOWN_COMMAND", "UNDEFINED_VARIABLE",
                             "SYNTAX", "UNDECIDED_WITHIN_BUDGET",
                             "NEVER_HALTS", "UNREAD_QUESTION",
                             "UNREAD_SENTENCE", "NO_SUCH_FILE",
                             "NOT_UNDECIDED")

_NAME = r"[A-Za-z_][A-Za-z0-9_]*"

# ===========================================================================
# 1.  SAYING AN INSTRUCTION
# ===========================================================================

_CMP_WORDS = {"LSS": "is less than", "LEQ": "is at most",
              "GTR": "is greater than", "GEQ": "is at least",
              "EQU": "is equal to", "NEQ": "is not equal to"}
_WORD_CMP = {v: k for k, v in _CMP_WORDS.items()}
_REDIR_WORDS = {">": "writing to", ">>": "appending to", "<": "reading from"}
_WORD_REDIR = {v: k for k, v in _REDIR_WORDS.items()}


def _say_seta(name: str, expr: str) -> str:
    for op, verb in (("+", "add {n} to {v}"), ("-", "subtract {n} from {v}"),
                     ("*", "multiply {v} by {n}")):
        m = re.match(rf"^{re.escape(name)}{re.escape(op)}(\d+)$", expr)
        if m:
            return verb.format(n=m.group(1), v=name)
    return f"compute {name} as {expr}"


def _say_cmd(c: bm.Cmd) -> str:
    n, a = c.name, c.args
    base = {
        "ECHO": lambda: f'print "{a[0]}"',
        "SET": lambda: f'set {a[0]} to "{a[1]}"',
        "SETA": lambda: _say_seta(a[0], a[1]),
        "TYPE": lambda: f"show file {a[0]}",
        "DEL": lambda: f"delete file {a[0]}",
        "COPY": lambda: f"copy file {a[0]} to {a[1]}",
        "MKDIR": lambda: f"make directory {a[0]}",
        "SORT": lambda: "sort the lines",
        "FIND": lambda: f'keep lines containing "{a[0]}"',
        "FINDC": lambda: f'count lines containing "{a[0]}"',
        "GOTO": lambda: ("go to the end" if a[0] == ":EOF"
                         else f"go to {a[0]}"),
        "CALL": lambda: f"call {a[0]}",
        "EXITB": lambda: (f"return with code {a[0]}" if a[0] else "return"),
        "EXIT": lambda: f"stop with code {a[0]}",
    }[n]()
    for op, path in c.redirs:
        base += f", {_REDIR_WORDS[op]} file {path}"
    return base


def _say_stmt(s: object) -> str:
    if isinstance(s, bm.Cmd):
        return _say_cmd(s)
    if isinstance(s, bm.Pipe):
        return ", then ".join(_say_cmd(c) for c in s.stages)
    if isinstance(s, bm.Chain):
        word = "succeeds" if s.op == "&&" else "fails"
        return f"{_say_stmt(s.left)}, and if that {word}, {_say_stmt(s.right)}"
    if isinstance(s, bm.If):
        c, neg = s.cond, s.negate
        if c[0] == "errorlevel":
            cond = f"the exit code is {'below' if neg else 'at least'} {c[1]}"
        elif c[0] == "exist":
            cond = f"file {c[1]} {'does not exist' if neg else 'exists'}"
        elif c[0] == "defined":
            cond = f"{c[1]} {'is not defined' if neg else 'is defined'}"
        elif c[0] == "streq":
            cond = (f'"{c[1]}" {"does not equal" if neg else "equals"} '
                    f'"{c[2]}"')
        else:
            cond = (("it is not true that " if neg else "")
                    + f"{c[1]} {_CMP_WORDS[c[2]]} {c[3]}")
        return f"if {cond}, {_say_stmt(s.body)}"
    if isinstance(s, bm.For):
        return f"for each {s.var} in {', '.join(s.items)}: {_say_stmt(s.body)}"
    raise TypeError(s)


def say_line(ins: object) -> str:
    """The one sentence of an instruction, ending in a full stop."""
    if isinstance(ins, bm.Label):
        return f"label {ins.name}."
    if isinstance(ins, bm.Rem):
        return f"note: {ins.text}." if ins.text else "note."
    return _say_stmt(ins) + "."


def say_program(program: Sequence[object]) -> List[str]:
    return [say_line(ins) for ins in program]


# ===========================================================================
# 2.  READING A SENTENCE BACK
# ===========================================================================

class _Unread(bm.BatchError):
    def __init__(self, text: str) -> None:
        super().__init__("UNREAD_SENTENCE", f"no sentence form reads {text!r}")


def _split_marker(text: str, markers: Sequence[str]) -> List[Tuple[str, str]]:
    """Split at any of ``markers`` outside double quotes: ``[(part, marker
    before it)]``."""
    out: List[Tuple[str, str]] = []
    buf, before, quoted, i = [], "", False, 0
    while i < len(text):
        if text[i] == '"':
            quoted = not quoted
        if not quoted:
            hit = next((m for m in markers if text.startswith(m, i)), None)
            if hit is not None:
                out.append(("".join(buf), before))
                buf, before = [], hit
                i += len(hit)
                continue
        buf.append(text[i])
        i += 1
    out.append(("".join(buf), before))
    return out


def _read_cmd(text: str) -> bm.Cmd:
    text = text.strip()
    redirs: List[Tuple[str, str]] = []
    while True:
        m = re.match(r'^(.*), (writing to|appending to|reading from) file '
                     r'([^\s"]+)$', text)
        if m is None:
            break
        redirs.insert(0, (_WORD_REDIR[m.group(2)], m.group(3)))
        text = m.group(1)
    rd = tuple(redirs)
    forms = [
        (r'^print "([^"]+)"$', lambda m: bm.Cmd("ECHO", (m.group(1),), rd)),
        (rf'^set ({_NAME}) to "([^"]*)"$',
         lambda m: bm.Cmd("SET", (m.group(1), m.group(2)), rd)),
        (rf"^add (\d+) to ({_NAME})$",
         lambda m: bm.Cmd("SETA", (m.group(2), f"{m.group(2)}+{m.group(1)}"),
                          rd)),
        (rf"^subtract (\d+) from ({_NAME})$",
         lambda m: bm.Cmd("SETA", (m.group(2), f"{m.group(2)}-{m.group(1)}"),
                          rd)),
        (rf"^multiply ({_NAME}) by (\d+)$",
         lambda m: bm.Cmd("SETA", (m.group(1), f"{m.group(1)}*{m.group(2)}"),
                          rd)),
        (rf"^compute ({_NAME}) as (\S+)$",
         lambda m: bm.Cmd("SETA", (m.group(1), m.group(2)), rd)),
        (r"^show file (\S+)$", lambda m: bm.Cmd("TYPE", (m.group(1),), rd)),
        (r"^delete file (\S+)$", lambda m: bm.Cmd("DEL", (m.group(1),), rd)),
        (r"^copy file (\S+) to (\S+)$",
         lambda m: bm.Cmd("COPY", (m.group(1), m.group(2)), rd)),
        (r"^make directory (\S+)$",
         lambda m: bm.Cmd("MKDIR", (m.group(1),), rd)),
        (r"^sort the lines$", lambda m: bm.Cmd("SORT", (), rd)),
        (r'^keep lines containing "([^"]*)"$',
         lambda m: bm.Cmd("FIND", (m.group(1),), rd)),
        (r'^count lines containing "([^"]*)"$',
         lambda m: bm.Cmd("FINDC", (m.group(1),), rd)),
        (r"^go to the end$", lambda m: bm.Cmd("GOTO", (":EOF",), rd)),
        (rf"^go to ({_NAME})$", lambda m: bm.Cmd("GOTO", (m.group(1),), rd)),
        (rf"^call ({_NAME})$", lambda m: bm.Cmd("CALL", (m.group(1),), rd)),
        (r"^return with code (-?\d+)$",
         lambda m: bm.Cmd("EXITB", (m.group(1),), rd)),
        (r"^return$", lambda m: bm.Cmd("EXITB", ("",), rd)),
        (r"^stop with code (-?\d+)$",
         lambda m: bm.Cmd("EXIT", (m.group(1),), rd)),
    ]
    for pattern, build in forms:
        m = re.match(pattern, text)
        if m:
            return build(m)
    raise _Unread(text)


def _read_stmt(text: str) -> object:
    text = text.strip()
    if text.startswith("if "):
        forms = [
            (r"^if the exit code is (at least|below) (\d+), (.+)$",
             lambda m: (m.group(1) == "below", ("errorlevel", m.group(2)),
                        m.group(3))),
            (r"^if file (\S+) (exists|does not exist), (.+)$",
             lambda m: (m.group(2) != "exists", ("exist", m.group(1)),
                        m.group(3))),
            (rf"^if ({_NAME}) (is defined|is not defined), (.+)$",
             lambda m: (m.group(2) != "is defined", ("defined", m.group(1)),
                        m.group(3))),
            (r'^if "([^"]*)" (equals|does not equal) "([^"]*)", (.+)$',
             lambda m: (m.group(2) != "equals",
                        ("streq", m.group(1), m.group(3)), m.group(4))),
            (r"^if (it is not true that )?(\S+) (is less than|is at most|"
             r"is greater than|is at least|is equal to|is not equal to) "
             r"(\S+), (.+)$",
             lambda m: (bool(m.group(1)),
                        ("cmp", m.group(2), _WORD_CMP[m.group(3)],
                         m.group(4)), m.group(5))),
        ]
        for pattern, build in forms:
            m = re.match(pattern, text)
            if m:
                neg, cond, body = build(m)
                return bm.If(neg, cond, _read_stmt(body))
        raise _Unread(text)
    if text.startswith("for each "):
        m = re.match(r"^for each ([A-Za-z]) in (.+?): (.+)$", text)
        if m is None:
            raise _Unread(text)
        items = tuple(x.strip() for x in m.group(2).split(","))
        return bm.For(m.group(1), items, _read_stmt(m.group(3)))
    parts = _split_marker(text, (", and if that succeeds, ",
                                 ", and if that fails, "))
    node: object = None
    for part, marker in parts:
        stages = [_read_cmd(p) for p, _ in _split_marker(part, (", then ",))]
        item = stages[0] if len(stages) == 1 else bm.Pipe(tuple(stages))
        if node is None:
            node = item
        else:
            node = bm.Chain(node, "&&" if "succeeds" in marker else "||",
                            item)
    return node


def read_sentence(text: str) -> object:
    """The instruction a sentence says (``UNREAD_SENTENCE`` if none)."""
    t = text.strip()
    if t.endswith("."):
        t = t[:-1]
    m = re.match(rf"^label ({_NAME})$", t)
    if m:
        return bm.Label(m.group(1))
    if t == "note":
        return bm.Rem("")
    m = re.match(r"^note: (.*)$", t)
    if m:
        return bm.Rem(m.group(1))
    return _read_stmt(t)


def split_sentences(text: str) -> List[str]:
    """Sentences end at a full stop followed by a space or the end, outside
    double quotes, or at a newline."""
    out: List[str] = []
    for line in text.splitlines():
        buf, quoted = [], False
        for i, ch in enumerate(line):
            buf.append(ch)
            if ch == '"':
                quoted = not quoted
            if (ch == "." and not quoted
                    and (i + 1 == len(line) or line[i + 1] == " ")):
                s = "".join(buf).strip()
                if s:
                    out.append(s)
                buf = []
        rest = "".join(buf).strip()
        if rest:
            out.append(rest)
    return out


def read_english(text: str) -> List[str]:
    """An English program read into canonical GLM-BAT lines."""
    return [bm.render_line(read_sentence(s)) for s in split_sentences(text)]


def read_program(text: str) -> Tuple[Tuple[object, ...], str]:
    """A program written as GLM-BAT lines or as English sentences:
    ``(instructions, "batch" | "english")``.  GLM-BAT is tried first; if it
    does not read, the sentences are; if neither reads, the GLM-BAT refusal
    stands."""
    lines = bm.split_program(text)
    try:
        return bm.parse_program(lines), "batch"
    except bm.BatchError as first:
        try:
            english = read_english(text)
        except bm.BatchError:
            raise first from None
        return bm.parse_program(english), "english"


# ===========================================================================
# 3.  COLUMN 3 -- A SECOND INTERPRETER, AS A STAND-ALONE SCRIPT
# ===========================================================================

#: The second interpreter.  Written separately from :mod:`batch_machine`
#: (its own reading of each line, by regular expressions over the raw text,
#: and its own execution), so agreement between the two is evidence about
#: both.  It reads ``PROGRAM``, ``ENV``, ``FILES``, ``DIRS`` and ``CLAIM``.
CHECKER = r'''
import re, sys
from math import isqrt
V = re.compile(r"%([A-Za-z_][A-Za-z0-9_]*)%")

def split_ops(s):
    out, cur, op, q, i = [], "", None, False, 0
    while i < len(s):
        c = s[i]
        if c == '"':
            q = not q
        if not q and s[i:i+2] in ("&&", "||"):
            out.append((op, cur)); cur, op = "", s[i:i+2]; i += 2; continue
        cur += c; i += 1
    out.append((op, cur))
    return out

def split_pipe(s):
    out, cur, q = [], "", False
    for c in s:
        if c == '"':
            q = not q
        if c == "|" and not q:
            out.append(cur); cur = ""
        else:
            cur += c
    out.append(cur)
    return out

class M:
    def __init__(m, env, files, dirs):
        m.env = {k.upper(): v for k, v in env.items()}
        m.files = {k: list(v) for k, v in files.items()}
        m.dirs = set(dirs); m.out = []; m.err = []; m.el = 0; m.forget = set()
    def x(m, t, sub):
        for k, v in sub.items():
            t = t.replace("%%" + k, v)
        def r(g):
            n = g.group(1).upper()
            if n in m.env: return m.env[n]
            if n == "ERRORLEVEL": return str(m.el)
            return ""
        return V.sub(r, t)
    def state(m, pc, stack):
        return (pc, sorted(kv for kv in m.env.items() if kv[0] not in m.forget),
                sorted((k, tuple(v)) for k, v in m.files.items()),
                sorted(m.dirs), tuple(stack), m.el)
    def parent(m, p):
        return "/" not in p or p.rsplit("/", 1)[0] in m.dirs

def arith(e, m):
    toks = re.findall(r"\d+|[A-Za-z_]\w*|[-+*/%()]", e)
    pos = [0]
    def pk(): return toks[pos[0]] if pos[0] < len(toks) else ""
    def tk(): pos[0] += 1; return toks[pos[0]-1]
    def at():
        t = tk()
        if t == "(":
            v = ad(); tk(); return v
        if t == "-":
            v = at(); return None if v is None else -v
        if t.isdigit(): return int(t)
        s = m.env.get(t.upper(), "0")
        return int(s) if re.fullmatch(r"-?\d+", s) else 0
    def tdiv(a, b):
        q = abs(a) // abs(b)
        return q if (a >= 0) == (b >= 0) else -q
    def mu():
        v = at()
        while pk() in ("*", "/", "%"):
            o = tk(); w = at()
            if v is None or w is None: v = None; continue
            if o == "*": v = v * w
            elif w == 0: v = None
            elif o == "/": v = tdiv(v, w)
            else: v = v - w * tdiv(v, w)
        return v
    def ad():
        v = mu()
        while pk() in ("+", "-"):
            o = tk(); w = mu()
            if v is None or w is None: v = None; continue
            v = v + w if o == "+" else v - w
        return v
    return ad()

def simple(t, m, sub, inp):
    t = t.strip()
    red = None
    rm = re.search(r'\s*(>>|>|<)\s*([^\s<>|&"]+)\s*$', t)
    if rm and '"' not in t[rm.start():]:
        red = (rm.group(1), rm.group(2)); t = t[:rm.start()].rstrip()
    if red and red[0] == "<":
        p = m.x(red[1], sub)
        if p not in m.files:
            m.err.append("The system cannot find the file specified."); return [], False, True, None, None
        inp = list(m.files[p]); red = None
    w, _, a = t.partition(" "); W = w.upper(); a = a.strip()
    if W == "ECHO": return [m.x(a, sub)], True, False, None, red
    if W == "SET":
        if a.upper().startswith("/A "):
            n, e = a[3:].split("=", 1)
            v = arith(re.sub(r"\s+", "", m.x(e, sub)), m)
            if v is None:
                m.err.append("Divide by zero error."); return [], False, True, None, red
            m.env[n.strip().upper()] = str(v); return [], True, False, None, red
        n, v = a.split("=", 1); v = m.x(v, sub)
        if v: m.env[n.upper()] = v
        else: m.env.pop(n.upper(), None)
        return [], True, False, None, red
    if W == "TYPE":
        p = m.x(a, sub)
        if p not in m.files:
            m.err.append("The system cannot find the file specified."); return [], False, True, None, red
        return list(m.files[p]), True, True, None, red
    if W == "DEL":
        p = m.x(a, sub)
        if p not in m.files:
            m.err.append("Could Not Find " + p); return [], False, True, None, red
        del m.files[p]; return [], True, True, None, red
    if W == "COPY":
        s, d = [m.x(z, sub) for z in a.split()]
        if s not in m.files:
            m.err.append("The system cannot find the file specified."); return [], False, True, None, red
        if not m.parent(d):
            m.err.append("The system cannot find the path specified."); return [], False, True, None, red
        m.files[d] = list(m.files[s]); return ["        1 file(s) copied."], True, True, None, red
    if W in ("MKDIR", "MD"):
        p = m.x(a, sub)
        if p in m.dirs or p in m.files:
            m.err.append("A subdirectory or file " + p + " already exists."); return [], False, True, None, red
        bits = p.split("/")
        for k in range(1, len(bits) + 1): m.dirs.add("/".join(bits[:k]))
        return [], True, True, None, red
    if W == "SORT": return sorted(inp or []), True, True, None, red
    if W == "FIND":
        c = a.upper().startswith("/C")
        s = m.x(re.search(r'"([^"]*)"', a).group(1), sub)
        hits = [l for l in (inp or []) if s in l]
        return ([str(len(hits))] if c else hits), bool(hits), True, None, red
    if W == "GOTO":
        return [], True, False, ("goto", ":EOF" if a.upper() == ":EOF" else a.lstrip(":")), None
    if W == "CALL": return [], True, False, ("call", a[1:]), None
    if W == "EXIT":
        mm = re.fullmatch(r"(/B)?\s*(-?\d+)?", a, re.I)
        if mm.group(1): return [], True, False, ("ret", int(mm.group(2)) if mm.group(2) else None), None
        return [], True, False, ("exit", int(mm.group(2))), None
    raise SystemExit("checker: unknown command " + W)

def pipeline(t, m, sub):
    data, ok, sets, eff, red = None, True, False, None, None
    stages = split_pipe(t)
    for k, st in enumerate(stages):
        data, ok, sets, eff, red = simple(st, m, sub, data if k else None)
        if eff: break
    if red and not eff:
        p = m.x(red[1], sub)
        if not m.parent(p) or p in m.dirs:
            m.err.append("The system cannot find the path specified."); m.el = 1; return False, None
        if red[0] == ">": m.files[p] = list(data or [])
        else: m.files[p] = m.files.get(p, []) + list(data or [])
    else:
        m.out.extend(data or [])
    if sets: m.el = 0 if ok else 1
    return ok, eff

def stmt(t, m, sub):
    t = t.strip()
    if t.upper().startswith("IF "):
        r = t[3:].strip(); neg = False
        if r.upper().startswith("NOT "): neg, r = True, r[4:].strip()
        g = re.match(r"ERRORLEVEL\s+(\d+)\s+(.+)$", r, re.I)
        if g: ok = m.el >= int(g.group(1)); body = g.group(2)
        else:
            g = re.match(r"EXIST\s+(\S+)\s+(.+)$", r, re.I)
            if g:
                p = m.x(g.group(1), sub); ok = p in m.files or p in m.dirs; body = g.group(2)
            else:
                g = re.match(r"DEFINED\s+(\S+)\s+(.+)$", r, re.I)
                if g: ok = g.group(1).upper() in m.env; body = g.group(2)
                else:
                    g = re.match(r'"([^"]*)"=="([^"]*)"\s+(.+)$', r)
                    if g: ok = m.x(g.group(1), sub) == m.x(g.group(2), sub); body = g.group(3)
                    else:
                        g = re.match(r"(\S+)\s+(EQU|NEQ|LSS|LEQ|GTR|GEQ)\s+(\S+)\s+(.+)$", r, re.I)
                        a, b = m.x(g.group(1), sub), m.x(g.group(3), sub)
                        if re.fullmatch(r"-?\d+", a) and re.fullmatch(r"-?\d+", b): a, b = int(a), int(b)
                        o = g.group(2).upper()
                        ok = {"EQU": a == b, "NEQ": a != b, "LSS": a < b, "LEQ": a <= b,
                              "GTR": a > b, "GEQ": a >= b}[o]; body = g.group(4)
        if ok != neg: return stmt(body, m, sub)
        return True, None
    if t.upper().startswith("FOR "):
        g = re.match(r"FOR\s+%%(\w)\s+IN\s+\(([^)]*)\)\s+DO\s+(.+)$", t, re.I)
        ok = True
        for it in g.group(2).split():
            s2 = dict(sub); s2[g.group(1)] = it
            ok, eff = stmt(g.group(3), m, s2)
            if eff: return ok, eff
        return ok, None
    ok, eff = True, None
    for op, part in split_ops(t):
        if op == "&&" and not ok: continue
        if op == "||" and ok: continue
        ok, eff = pipeline(part, m, sub)
        if eff: return ok, eff
    return ok, None

def execute(prog, env, files, dirs, limit=None, keep=False, forget=(), rec=None):
    m = M(env, files, dirs); m.forget = {n.upper() for n in forget}
    labels = {l.strip()[1:].strip().upper(): i for i, l in enumerate(prog) if l.strip().startswith(":")}
    pc, stack, steps, seen, states = 0, [], 0, {}, []
    while True:
        if pc >= len(prog): return m, "halted", steps, m.el, states, None
        st = m.state(pc, stack); key = repr(st)
        if keep: states.append(key)
        if limit is None:
            if key in seen: return m, "never", steps, None, states, (seen[key], steps)
            seen[key] = steps
        elif steps >= limit: return m, "stopped", steps, None, states, None
        if rec is not None: rec.append((pc, dict(m.env), {f: tuple(v) for f, v in m.files.items()}))
        steps += 1
        line = prog[pc].strip()
        if line.startswith(":") or line.upper().startswith("REM"):
            pc += 1; continue
        ok, eff = stmt(line, m, {})
        if not eff: pc += 1; continue
        k, a = eff
        if k == "exit": m.el = a; return m, "halted", steps, a, states, None
        if k == "ret" or (k == "goto" and a == ":EOF"):
            if k == "ret" and a is not None: m.el = a
            if stack: pc = stack.pop(); continue
            return m, "halted", steps, m.el, states, None
        if a.upper() not in labels:
            m.err.append("The system cannot find the batch label specified - " + a); m.el = 1
            return m, "halted", steps, 1, states, None
        if k == "call": stack.append(pc + 1)
        pc = labels[a.upper()] + 1

def closed(prog, names):
    F = {n.upper() for n in names}
    if "ERRORLEVEL" in F: return False
    for l in prog:
        t = l.strip()
        if not any(re.search(r"(?<![A-Za-z0-9_])" + re.escape(n) + r"(?![A-Za-z0-9_])", t, re.I) for n in F):
            continue
        if re.search(r"[<>|&]", t): return False
        g = re.fullmatch(r"SET\s+/A\s+([A-Za-z_]\w*)\s*=\s*([^/%]+)", t, re.I) or \
            re.fullmatch(r"SET\s+([A-Za-z_]\w*)=(.*)", t, re.I)
        if not g or g.group(1).upper() not in F: return False
    return True

def reach(prog):
    labels = {l.strip()[1:].strip().upper(): i for i, l in enumerate(prog) if l.strip().startswith(":")}
    def gotos(l):
        return [g.group(2) for g in re.finditer(r"\b(GOTO|CALL)\s+:?(\w+)", l, re.I)
                if g.group(2).upper() != "EOF"]
    def ends(l):
        return bool(re.search(r"\bEXIT\b|\bGOTO\s+:EOF\b", l, re.I))
    rets = [i + 1 for i, l in enumerate(prog) if re.search(r"\bCALL\b", l, re.I)]
    seen, todo = {0}, [0]
    while todo:
        i = todo.pop(); l = prog[i].strip(); U = l.upper()
        nxt = []
        bare_goto = U.startswith("GOTO ") and U != "GOTO :EOF"
        bare_end = U.startswith("EXIT") or U == "GOTO :EOF"
        if not (bare_goto or bare_end): nxt.append(i + 1)
        nxt += [labels[g.upper()] for g in gotos(l) if g.upper() in labels]
        if ends(l): nxt += rets
        for j in nxt:
            if j < len(prog) and j not in seen: seen.add(j); todo.append(j)
    return [i + 1 for i in range(len(prog)) if i not in seen]

TRIGGERS = {
    "process": lambda P: True, "script": lambda P: True,
    "command": lambda P: any(not l.startswith(":") and not l.upper().startswith("REM") for l in P),
}
def uses(prog):
    T = set(["process", "script"])
    for l in prog:
        U = l.upper()
        if l.startswith(":"): T.add("jump"); continue
        if U.startswith("REM"): continue
        T.add("command")
        nop = re.sub(r'"[^"]*"', '""', U)
        bare = re.sub(r"\bECHO\b[^|&<>]*", "ECHO ", nop)
        words = re.findall(r"(?:^|&&|\|\||\||\bDO\b|\s)(ECHO|SET|TYPE|DEL|COPY|MKDIR|MD|SORT|FIND|GOTO|CALL|EXIT)\b", bare)
        if re.search(r"(?<!\|)\|(?!\|)", nop): T.update(["pipe", "stream"])
        if re.search(r"[<>]", nop): T.update(["redirection", "file", "stream"])
        if "&&" in nop or "||" in nop: T.update(["exit_handling", "exit_code"])
        if re.search(r"\bIF\b", nop): T.add("conditional")
        if re.search(r"\bERRORLEVEL\s+\d", nop): T.update(["exit_handling", "exit_code"])
        if re.search(r"\bEXIST\b", nop): T.add("file")
        if re.search(r"\bDEFINED\b", nop): T.update(["variable", "env_var"])
        if re.search(r"^FOR\b", nop): T.add("loop")
        if "%" in l: T.update(["substitution", "env_var"])
        for w in words:
            if w == "SET": T.update(["variable", "assignment", "env_var"])
            if w in ("TYPE", "DEL", "COPY", "MKDIR", "MD"): T.add("file")
            if w in ("ECHO", "TYPE", "SORT", "FIND"): T.add("stream")
            if w in ("GOTO", "CALL"): T.add("jump")
            if w == "EXIT": T.add("exit_code")
            if w != "SORT": T.add("argument")
    return sorted(T)

CNT = re.compile(r"SET\s+/A\s+([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\s*([+-])\s*(\d+)", re.I)
IFC = re.compile(r"IF\s+(NOT\s+)?(\S+)\s+(EQU|NEQ|LSS|LEQ|GTR|GEQ)\s+(\S+)\s+(.+)", re.I)
CMPS = {"EQU": lambda e: e == 0, "NEQ": lambda e: e != 0, "LSS": lambda e: e < 0,
        "LEQ": lambda e: e <= 0, "GTR": lambda e: e > 0, "GEQ": lambda e: e >= 0}

def counters_of(prog):
    out = set()
    for l in prog:
        g = CNT.fullmatch(l.strip())
        if g and g.group(1).upper() == g.group(2).upper() and g.group(1).upper() != "ERRORLEVEL":
            out.add(g.group(1).upper())
    return sorted(out)

ACC = re.compile(r"SET\s+/A\s+([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\s*([+-])\s*(%?)([A-Za-z_]\w*)\4", re.I)

def accline(l):
    g = ACC.fullmatch(l.strip())
    if not g or g.group(1).upper() != g.group(2).upper(): return None
    v, w = g.group(1).upper(), g.group(5).upper()
    if v == w or "ERRORLEVEL" in (v, w): return None
    return v, w, (1 if g.group(3) == "+" else -1)

def accs_of(prog):
    cnt = set(counters_of(prog))
    ups = [a for a in map(accline, prog) if a]
    tg = {a[0] for a in ups}
    return sorted({v for v, w, s in ups if w in cnt and w not in tg})

def canon(v):
    return v is not None and re.fullmatch(r"-?\d+", v) is not None and str(int(v)) == v

def word(t, n):
    return re.search(r"(?<![A-Za-z0-9_])" + re.escape(n) + r"(?![A-Za-z0-9_])", t, re.I) is not None

def opnd(t, live, consts):
    g = re.fullmatch(r"%([A-Za-z_]\w*)%", t)
    if g and g.group(1).upper() in live: return (g.group(1).upper(), 0)
    if g and g.group(1).upper() != "ERRORLEVEL" and canon(consts.get(g.group(1).upper())):
        return ("", int(consts[g.group(1).upper()]))
    if re.fullmatch(r"-?\d+", t): return ("", int(t))
    return None

def opnames(l):
    g = IFC.fullmatch(l.strip())
    if not g: return []
    return [h.group(1).upper() for h in (re.fullmatch(r"%([A-Za-z_]\w*)%", g.group(k)) for k in (2, 4)) if h]

def kind(l, live, consts, quad=None):
    t = l.strip()
    if t.startswith(":") or t.upper().startswith("REM"): return "free", None
    if re.search(r"\bFOR\b", t, re.I): return "no", None
    if not any(word(t, n) for n in live): return "free", None
    g = CNT.fullmatch(t)
    if g and g.group(1).upper() == g.group(2).upper() and g.group(1).upper() in live:
        return "add", None
    if quad:
        a = accline(t)
        if a and a[0] in quad[0] and a[0] in live and a[1] in quad[1] and a[1] in live:
            return "acc", a
    g = IFC.fullmatch(t)
    if g:
        a, b = opnd(g.group(2), live, consts), opnd(g.group(4), live, consts)
        if a and b and not any(word(g.group(5), n) for n in live):
            return "test", (a, g.group(3).upper(), b)
    if re.fullmatch(r"ECHO\s+[^<>|&]+", t, re.I): return "echo", None
    return "no", None

def flip(x, sl, op):
    f = CMPS[op]
    if sl == 0: return None
    q = (-x) // sl
    for mm in sorted({1, q, q + 1, q + 2}):
        if mm >= 1 and f(x + sl * mm) != f(x): return mm
    return None

def qflip(x, b, c, op):
    # the least t >= 1 where x + b t + c t(t-1)/2 OP 0 changes: t = 1, or an
    # integer within reach of a real root of c t^2 + (2b - c) t + 2x
    if c == 0: return flip(x, b, op)
    f = CMPS[op]
    v = lambda t: x + b * t + c * (t * (t - 1) // 2)
    A, B, C0 = c, 2 * b - c, 2 * x
    D = B * B - 4 * A * C0
    cands = {1}
    if D >= 0:
        r0 = isqrt(D)
        for sq in (r0, -r0, r0 + 1, -r0 - 1):
            q = (-B + sq) // (2 * A)
            cands.update(range(q - 3, q + 4))
    for t in sorted(cands):
        if t >= 1 and f(v(t)) != f(x): return t
    return None

def template(line, m, names):
    t = line.strip()
    if not re.fullmatch(r"ECHO\s+[^<>|&]+", t, re.I): return None
    bits = V.split(t.partition(" ")[2].strip())
    out = []
    for i, b in enumerate(bits):
        if i % 2 == 0: out.append(b)
        elif b.upper() in names: out.append([b.upper()])
        elif b.upper() in m.env: out.append(m.env[b.upper()])
        elif b.upper() == "ERRORLEVEL": out.append(str(m.el))
        else: out.append("")
    return out

def passread(prog, names, hist, end, quad=None):
    st, en = hist[0][2], end[2]
    live = [n for n in names if canon(st.get(n))]
    d = {n: int(en[n]) - int(st[n]) for n in live}
    q = (set(quad[0]) & set(live), set(quad[1]) & set(live)) if quad else None
    best, echo, hok = None, False, True
    kinds = [kind(prog[h[1]], live, h[5], q) for h in hist]
    if any(kd == "no" for kd, _ in kinds): return None
    gam, gr = {n: 0 for n in live}, []
    for kd, info in kinds:
        gr.append(dict(gam))
        if kd == "acc": gam[info[0]] += info[2] * d[info[1]]
    for r, ((g, pc, vals, o, e, cs, tp), (kd, info)) in enumerate(zip(hist, kinds)):
        if kd == "echo":
            echo = True
            if tp is None or any(isinstance(x, list) and x[0] not in live for x in tp): hok = False
        if kd == "test":
            (na, ka), op, (nb, kb) = info
            x = (int(vals[na]) if na else ka) - (int(vals[nb]) if nb else kb)
            sl = ((d[na] + gr[r][na]) if na else 0) - ((d[nb] + gr[r][nb]) if nb else 0)
            cu = (gam[na] if na else 0) - (gam[nb] if nb else 0)
            f = qflip(x, sl, cu, op)
            if f is not None and (best is None or f < best): best = f
    return (d, best, echo or end[3] != hist[0][3] or end[4] != hist[0][4], echo, hok,
            {n: v for n, v in gam.items() if v}, gr)

def jumped(prog, env, files, dirs, budget):
    m = M(env, files, dirs)
    labels = {l.strip()[1:].strip().upper(): i for i, l in enumerate(prog) if l.strip().startswith(":")}
    names = counters_of(prog)
    quad, ac = None, accs_of(prog)
    if ac:
        quad = (set(ac), set(names) - set(ac))
        names = sorted(set(names) | set(ac))
    pc, stack, steps, off, seen, hist, jumps = 0, [], 0, 0, {}, [], []
    while True:
        if pc >= len(prog): return m, "halted", steps + off, m.el, jumps, None
        key = repr((pc, sorted((k, "#" if k in names and canon(v) else "=" + v) for k, v in m.env.items()),
                    sorted((k, tuple(v)) for k, v in m.files.items()), sorted(m.dirs), tuple(stack), m.el))
        snap = (steps + off, pc, {n: m.env.get(n) for n in names}, len(m.out), len(m.err),
                {n: m.env.get(n) for n in (opnames(prog[pc]) if pc < len(prog) else [])},
                template(prog[pc], m, names) if pc < len(prog) else None)
        if key in seen and names:
            k = seen[key]
            res = passread(prog, names, hist[k:], snap, quad)
            if res is not None:
                d, mm, writes, echo, hok, gam, gr = res
                if mm is None: return m, "never", steps + off, None, jumps, (hist[k][0], snap[0], d, gam)
                bo, be = m.out[hist[k][3]:snap[3]], m.err[hist[k][4]:snap[4]]
                ok = not writes or ((not echo or hok) and len(m.out) + len(m.err) + (mm - 1) * (len(bo) + len(be)) <= 1000000)
                if ok and len(jumps) < 100:
                    if mm > 1:
                        if echo:
                            span = hist[k:] + [snap]; per = []
                            for r in range(len(span) - 1):
                                a_, b_ = span[r], span[r + 1]
                                tp = a_[6] if a_[6] and any(isinstance(x, list) for x in a_[6]) else None
                                per.append((tp, a_[2], m.out[a_[3]:b_[3]], m.err[a_[4]:b_[4]], gr[r]))
                            for t in range(1, mm):
                                for tp, vals, lo, le, gq in per:
                                    if tp is None: m.out.extend(lo); m.err.extend(le)
                                    else: m.out.append("".join(str(int(vals[x[0]]) + t * (d[x[0]] + gq.get(x[0], 0)) + t * (t - 1) // 2 * gam.get(x[0], 0)) if isinstance(x, list) else x for x in tp))
                        else:
                            m.out.extend(bo * (mm - 1)); m.err.extend(be * (mm - 1))
                        for n, dn in d.items(): m.env[n] = str(int(hist[k][2][n]) + mm * dn + mm * (mm - 1) // 2 * gam.get(n, 0))
                        off += (mm - 1) * (snap[0] - hist[k][0])
                        jumps.append([hist[k][0], snap[0], mm])
                    seen, hist = {}, []
                    continue
        seen[key] = len(hist); hist.append(snap)
        if steps >= budget: return m, "stopped", steps + off, None, jumps, None
        steps += 1
        line = prog[pc].strip()
        if line.startswith(":") or line.upper().startswith("REM"):
            pc += 1; continue
        ok, eff = stmt(line, m, {})
        if not eff: pc += 1; continue
        k2, a = eff
        if k2 == "exit": m.el = a; return m, "halted", steps + off, a, jumps, None
        if k2 == "ret" or (k2 == "goto" and a == ":EOF"):
            if k2 == "ret" and a is not None: m.el = a
            if stack: pc = stack.pop(); continue
            return m, "halted", steps + off, m.el, jumps, None
        if a.upper() not in labels:
            m.err.append("The system cannot find the batch label specified - " + a); m.el = 1
            return m, "halted", steps + off, 1, jumps, None
        if k2 == "call": stack.append(pc + 1)
        pc = labels[a.upper()] + 1

def unruns(segs):
    out = []
    for block, count, steps in segs:
        toks = [re.split(r"(-?\d+)", l) for l in block]
        for t in range(count):
            j = 0
            for tk in toks:
                line = ""
                for i, piece in enumerate(tk):
                    if i % 2: line += str(int(piece) + t * steps[j]) if t else piece; j += 1
                    else: line += piece
                out.append(line)
    return out

def outputs(c):
    if "out_runs" in c: return unruns(c["out_runs"]), unruns(c["err_runs"])
    return c["out"], c["err"]

def gshape(x):
    a = [x[i + 1] - x[i] for i in range(len(x) - 1)]
    if min(a) == max(a): return ["translation", a[0]]
    b = [a[i + 1] - a[i] for i in range(len(a) - 1)]
    if min(b) == max(b) and b[0] != 0: return ["quadratic", b[0]]
    if 0 not in x and x[1] % x[0] == 0:
        r = x[1] // x[0]
        if all(x[i + 1] == r * x[i] for i in range(len(x) - 1)): return ["geometric", r]
    return ["irregular", None]

def check(c):
    k = c["kind"]
    if k == "run":
        m, st, steps, code, _, _ = execute(PROGRAM, ENV, FILES, DIRS)
        assert st == "halted", st
        assert m.out == c["out"], (m.out, c["out"])
        assert m.err == c["err"], (m.err, c["err"])
        assert code == c["exit"], (code, c["exit"])
        assert steps == c["steps"], (steps, c["steps"])
        assert {k2: list(v) for k2, v in m.files.items()} == c["files"], (m.files, c["files"])
        assert sorted(m.dirs) == c["dirs"], (m.dirs, c["dirs"])
        for n, v in c.get("values", {}).items():
            assert m.env.get(n.upper()) == v, (n, m.env.get(n.upper()), v)
    elif k == "never":
        i, j = c["certificate"]
        m, st, steps, code, states, _ = execute(PROGRAM, ENV, FILES, DIRS, limit=j, keep=True)
        assert st == "stopped" and len(states) == j + 1, (st, len(states))
        assert states[i] == states[j], "the control state does not recur"
        assert len(set(states[:j])) == j, "not the first recurrence"
    elif k == "never_inert":
        i, j = c["certificate"]
        assert closed(PROGRAM, c["forgotten"]), "a forgotten variable is read"
        m, st, steps, code, states, _ = execute(PROGRAM, ENV, FILES, DIRS, limit=j, keep=True,
                                                forget=c["forgotten"])
        assert st == "stopped" and len(states) == j + 1, (st, len(states))
        assert states[i] == states[j], "the forgetful state does not recur"
        assert len(set(states[:j])) == j, "not the first recurrence"
    elif k == "run_jump":
        m, st, steps, code, jumps, _ = jumped(PROGRAM, ENV, FILES, DIRS, c["budget"])
        assert st == "halted", st
        assert jumps and jumps == c["jumps"], (jumps, c["jumps"])
        co, ce = outputs(c)
        assert m.out == co, "standard output differs from the claim"
        assert m.err == ce, "standard error differs from the claim"
        assert code == c["exit"], (code, c["exit"])
        assert steps == c["steps"], (steps, c["steps"])
        assert {k2: list(v) for k2, v in m.files.items()} == c["files"], (m.files, c["files"])
        assert sorted(m.dirs) == c["dirs"], (m.dirs, c["dirs"])
        for n, v in c.get("values", {}).items():
            assert m.env.get(n.upper()) == v, (n, m.env.get(n.upper()), v)
    elif k == "never_lasso":
        m, st, steps, code, jumps, cert = jumped(PROGRAM, ENV, FILES, DIRS, c["budget"])
        assert st == "never", st
        assert jumps == c["jumps"], (jumps, c["jumps"])
        assert [cert[0], cert[1]] == c["certificate"], (cert, c["certificate"])
        assert cert[2] == c["d"], (cert[2], c["d"])
        assert cert[3] == c.get("g", {}), (cert[3], c.get("g", {}))
    elif k == "growth":
        rec = []
        execute(PROGRAM, ENV, FILES, DIRS, limit=c["budget"], rec=rec)
        cnt = {}
        for pc, e, f in rec: cnt[pc] = cnt.get(pc, 0) + 1
        top = max(cnt.values()); head = min(p for p in cnt if cnt[p] == top)
        assert [head + 1, top] == [c["head"], c["visits"]], (head + 1, top)
        win = [(e, f) for pc, e, f in rec if pc == head][-c["window"]:]
        shapes = {}
        for n in sorted({n for e, _ in win for n in e}):
            vs = [e.get(n) for e, _ in win]
            if len(set(vs)) == 1: continue
            shapes[n] = gshape([int(v) for v in vs]) if all(canon(v) for v in vs) else ["text", None]
        assert shapes == c["shapes"], (shapes, c["shapes"])
        ch = sorted(p for p in {p for _, f in win for p in f} if len({f.get(p) for _, f in win}) > 1)
        assert ch == c["files"], (ch, c["files"])
    elif k == "idempotent":
        m1, s1, *_ = execute(PROGRAM, ENV, FILES, DIRS)
        m2, s2, *_ = execute(PROGRAM, ENV, m1.files, m1.dirs)
        assert s1 == s2 == "halted"
        differ = sorted(p for p in set(m1.files) | set(m2.files) if m1.files.get(p) != m2.files.get(p))
        same = not differ and m1.dirs == m2.dirs
        assert same == c["idempotent"], (same, c["idempotent"])
        assert differ == c["differing"], (differ, c["differing"])
    elif k == "unreachable":
        assert reach(PROGRAM) == c["lines"], (reach(PROGRAM), c["lines"])
    elif k == "uses":
        assert uses(PROGRAM) == sorted(c["terms"]), (uses(PROGRAM), c["terms"])
    elif k == "say":
        m1, s1, n1, c1, *_ = execute(PROGRAM, ENV, FILES, DIRS, limit=c["limit"])
        m2, s2, n2, c2, *_ = execute(c["read_back"], ENV, FILES, DIRS, limit=c["limit"])
        assert (m1.out, m1.err, c1, m1.files, m1.dirs, s1, n1) == (m2.out, m2.err, c2, m2.files, m2.dirs, s2, n2), "the sentences say another program"
        assert len(c["read_back"]) == len(PROGRAM)
    elif k == "pipeline":
        files, dirs = {k2: list(v) for k2, v in FILES.items()}, set(DIRS)
        start = dict(files); failed = None; passed = []
        for name, prog in c["stages"]:
            m, st, *_ = execute(prog, {}, files, dirs)
            assert st == "halted"
            files, dirs = m.files, m.dirs
            if m.el != 0:
                failed = name; break
            passed.append(name)
        if failed and c["rollback"]: files, dirs = start, set()
        assert (failed is None) == c["promoted"], (failed, c["promoted"])
        assert failed == c["failed_at"], (failed, c["failed_at"])
        assert {k2: list(v) for k2, v in files.items()} == c["files"], (files, c["files"])
    else:
        raise SystemExit("checker: unknown claim " + k)

check(CLAIM)
print("VERIFIED")
'''


def column3_script(program_lines: Sequence[str], claim: Mapping[str, object],
                   env: Optional[Mapping[str, str]] = None,
                   files: Optional[Mapping[str, Sequence[str]]] = None,
                   dirs: Sequence[str] = ()) -> str:
    """The stand-alone script: the inputs and the claim as literals, then the
    second interpreter, then the check."""
    def lit(value: object) -> str:
        return repr(value)

    head = ("# GLM-BAT column 3: re-derive the claim with a second interpreter\n"
            f"PROGRAM = {lit(list(program_lines))}\n"
            f"ENV = {lit(dict(sorted((env or {}).items())))}\n"
            f"FILES = {lit({k: list(v) for k, v in sorted((files or {}).items())})}\n"
            f"DIRS = {lit(sorted(dirs))}\n"
            f"CLAIM = {lit(_plain(claim))}\n")
    return head + CHECKER


def _plain(value: object) -> object:
    """A claim with its mappings sorted and its tuples made lists, so that its
    ``repr`` is a deterministic Python literal."""
    if isinstance(value, Mapping):
        return {k: _plain(value[k]) for k in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


def run_script(script: str) -> Tuple[bool, str]:
    """Run a column-3 script under ``python3 -I``; ``(passed, last line)``."""
    proc = subprocess.run([sys.executable, "-I", "-"], input=script,
                          capture_output=True, text=True, timeout=120)
    text = (proc.stdout.strip().splitlines() or [""])[-1] if proc.returncode \
        == 0 else (proc.stderr.strip().splitlines() or ["failed"])[-1]
    return proc.returncode == 0 and text == "VERIFIED", text


def mutations(claim: Mapping[str, object],
              program_lines: Sequence[str] = ()) -> List[Dict[str, object]]:
    """Altered claims, each of which the script must reject (mark O7; for a
    ``never_inert`` claim, mark I4 of the inert-counter study, where
    ``program_lines`` supplies a name a non-assignment line reads)."""
    c = json.loads(json.dumps(claim))
    out: List[Dict[str, object]] = []

    def alt(**changes: object) -> None:
        d = json.loads(json.dumps(c))
        d.update(changes)
        out.append(d)

    k = c["kind"]
    if k == "run":
        alt(out=c["out"] + ["extra"])
        if c["out"]:
            alt(out=[c["out"][0] + "x"] + c["out"][1:])
        alt(exit=(c["exit"] or 0) + 1)
        alt(steps=c["steps"] + 1)
        files = dict(c["files"])
        files["phantom.txt"] = ["x"]
        alt(files=files)
        for name, v in c.get("values", {}).items():
            vals = dict(c["values"])
            vals[name] = v + "0"
            alt(values=vals)
    elif k == "never":
        i, j = c["certificate"]
        alt(certificate=[i, j + 1])
        alt(certificate=[i, j - 1] if j - 1 > i else [i + 1, j + 1])
    elif k == "never_inert":
        i, j = c["certificate"]
        F = list(c["forgotten"])
        alt(certificate=[i, j + 1])
        alt(certificate=[i, j - 1] if j - 1 > i else [i + 1, j + 1])
        alt(forgotten=[])
        alt(forgotten=F[1:])
        alt(forgotten=sorted(F + [_read_name(program_lines, F)]))
    elif k == "run_jump":
        first = c["jumps"][0]
        alt(steps=c["steps"] + 1)
        alt(jumps=[[first[0], first[1], first[2] + 1]] + c["jumps"][1:])
        alt(jumps=[[first[0], first[1], first[2] - 1]] + c["jumps"][1:])
        alt(jumps=[[first[0], first[1] + 1, first[2]]] + c["jumps"][1:])
        alt(jumps=[])
        if "out_runs" in c:
            # Phase 132: a claim in run form -- a count lowered by one, and
            # a step raised by one.
            key = "out_runs"
            idx = next((n for n, seg in enumerate(c["out_runs"])
                        if seg[1] > 1), None)
            if idx is None:
                key = "err_runs"
                idx = next((n for n, seg in enumerate(c["err_runs"])
                            if seg[1] > 1), None)
            if idx is not None:
                segs = json.loads(json.dumps(c[key]))
                segs[idx][1] -= 1
                alt(**{key: segs})
            for key in ("out_runs", "err_runs"):
                idx = next((n for n, seg in enumerate(c[key])
                            if seg[1] > 1 and seg[2]), None)
                if idx is not None:
                    segs = json.loads(json.dumps(c[key]))
                    segs[idx][2][0] += 1
                    alt(**{key: segs})
                    break
        else:
            if c["out"]:
                alt(out=[c["out"][0] + "x"] + c["out"][1:])
            else:
                alt(out=["extra"])
            rep = next((n for n in range(1, len(c["out"]))
                        if c["out"][n] in c["out"][:n]), None)
            if rep is not None:
                alt(out=c["out"][:rep] + c["out"][rep + 1:])
    elif k == "never_lasso":
        i, j = c["certificate"]
        alt(certificate=[i, j + 1])
        alt(certificate=[i, j - 1])
        name = sorted(c["d"])[0]
        d1 = dict(c["d"])
        d1[name] = c["d"][name] + 1
        alt(d=d1)
        d0 = dict(c["d"])
        d0[name] = 0 if c["d"][name] else 1
        alt(d=d0)
        if c.get("g"):
            gname = sorted(c["g"])[0]
            g1 = dict(c["g"])
            g1[gname] = c["g"][gname] + 1
            alt(g=g1)
            g0 = dict(c["g"])
            del g0[gname]
            alt(g=g0)
    elif k == "growth":
        alt(head=c["head"] + 1)
        alt(visits=c["visits"] + 1)
        shapes = json.loads(json.dumps(c["shapes"]))
        name = next((n for n in sorted(shapes) if shapes[n][1] is not None),
                    None)
        if name is not None:
            shapes[name][1] += 1
        elif shapes:
            shapes[sorted(shapes)[0]] = ["translation", 1]
        else:
            shapes["PHANTOM"] = ["translation", 1]
        alt(shapes=shapes)
    elif k == "idempotent":
        alt(idempotent=not c["idempotent"])
        alt(differing=c["differing"] + ["phantom.txt"])
    elif k == "unreachable":
        alt(lines=sorted(set(c["lines"]).symmetric_difference({1})))
    elif k == "uses":
        extra = next(t for t in ("loop", "pipe", "conditional", "jump",
                                 "redirection", "assignment")
                     if t not in c["terms"])
        alt(terms=sorted(c["terms"] + [extra]))
        alt(terms=[t for t in c["terms"] if t != "command"])
    elif k == "say":
        rb = list(c["read_back"])
        idx = max((n for n, line in enumerate(rb) if re.search(r"\d", line)),
                  default=None)
        if idx is not None:
            rb[idx] = re.sub(r"(\d+)(?!.*\d)",
                             lambda m: str(int(m.group(1)) + 1), rb[idx])
        else:
            rb.append("ECHO mutated")
        alt(read_back=rb)
    elif k == "pipeline":
        alt(promoted=not c["promoted"])
        files = dict(c["files"])
        files["phantom.txt"] = ["x"]
        alt(files=files)
    return out


def _read_name(program_lines: Sequence[str], forgotten: Sequence[str]) -> str:
    """A variable a line other than an inert assignment reads, not already
    forgotten; ``ERRORLEVEL`` when there is none."""
    F = {n.upper() for n in forgotten}
    for line in program_lines:
        t = line.strip()
        if re.match(r"SET\s", t, re.I) and not re.search(r"[<>|&]", t):
            continue
        for name in re.findall(r"%([A-Za-z_][A-Za-z0-9_]*)%", t):
            if name.upper() not in F and name.upper() != "ERRORLEVEL":
                return name.upper()
    return "ERRORLEVEL"


def never_claim(run: "bm.Run") -> Dict[str, object]:
    """The column-3 claim for a run that never halts: the Phase 125
    certificate, or with the inert names forgotten (Phase 126), or a counter
    lasso (Phase 130)."""
    i, j = run.certificate
    if run.lasso:
        claim = {"kind": "never_lasso", "certificate": [i, j],
                 "d": {n: dn for n, dn in run.lasso},
                 "jumps": [list(jp[:3]) for jp in run.jumps],
                 "budget": bm.BUDGET}
        if run.growth:
            claim["g"] = {n: gn for n, gn in run.growth}
        return claim
    if run.forgotten:
        return {"kind": "never_inert", "certificate": [i, j],
                "forgotten": list(run.forgotten)}
    return {"kind": "never", "certificate": [i, j]}


# ===========================================================================
# 4.  QUESTIONS
# ===========================================================================

@dataclass
class Answer:
    """One verdict: answered with its three columns, or refused by name."""

    question: str
    answered: bool
    text: str
    refusal: str = ""
    column1: List[str] = field(default_factory=list)
    column2: List[str] = field(default_factory=list)
    script: str = ""
    claim: Dict[str, object] = field(default_factory=dict)
    verified: Optional[bool] = None
    value: object = None
    faculty: str = ""
    form: str = ""

    def body(self) -> str:
        return self.text if self.answered else f"refused: {self.refusal}: {self.text}"


_QUESTIONS: Tuple[Tuple[str, str], ...] = (
    (r"^what does it print\??$", "print"),
    (r"^what does it write to standard error\??$", "stderr"),
    (rf"^what is (?:the value of )?({_NAME})(?: at the end)?\??$", "value"),
    (r"^what is the exit code\??$", "exit"),
    (r"^(?:does it halt|does it stop|does it terminate|does it end)\??$",
     "halts"),
    (r"^is it idempotent\??$", "idempotent"),
    (r"^(?:which lines are unreachable|is there dead code)\??$",
     "unreachable"),
    (r"^which files does it write\??$", "files"),
    (r"^what is in file (\S+?)\??$", "file"),
    (r"^what does it say\??$", "say"),
    (r"^what does it use\??$", "uses"),
    (r"^how many steps(?: does it take)?\??$", "steps"),
    (r"^why (?:is it undecided|can it not decide|can't it decide)\??$",
     "why"),
)


def _classify(question: str) -> Tuple[Optional[str], Optional[str]]:
    q = question.strip()
    for pattern, kind in _QUESTIONS:
        m = re.match(pattern, q, re.IGNORECASE)
        if m:
            if kind == "value" and m.group(1).lower() in ("the", "it"):
                continue
            arg = m.group(1) if m.groups() else None
            return kind, arg
    return None, None


def _refuse(question: str, name: str, why: str, **kw: object) -> Answer:
    return Answer(question, False, why, refusal=name, faculty="refusal", **kw)


#: Phase 132: a claim whose two output streams together hold more lines than
#: this states them in run form (``out_runs``, ``err_runs``).
RUN_FORM_LINES = 100_000

#: The longest block the run encoder tries.
_MAX_BLOCK = 16

_NUM = re.compile(r"(-?\d+)")


def _tokens(line: str) -> Tuple[Tuple[str, ...], Tuple[int, ...], bool]:
    """``(skeleton, integers, canonical)`` of a line: the pieces between the
    matches of ``-?\\d+``, the matches as integers, and whether every match is
    written as ``str(int(.))`` writes it."""
    bits = _NUM.split(line)
    nums = bits[1::2]
    return (tuple(bits[0::2]), tuple(int(n) for n in nums),
            all(str(int(n)) == n for n in nums))


def output_runs(lines: Sequence[str]) -> List[List[object]]:
    """The run form of a stream (``studies/AFFINE_OUTPUT_STUDY.md`` section
    2): segments ``[block, count, steps]``, ``count`` copies of ``block`` in
    which copy ``t`` advances the ``j``-th integer by ``t * steps[j]``.
    Greedy: at each position the block length ``q`` in ``1..16`` and the
    largest ``count >= 2`` covering the most lines (ties to the smaller
    ``q``), else one line.  :func:`decode_runs` gives the lines back."""
    toks = [_tokens(l) for l in lines]
    n = len(lines)
    out: List[List[object]] = []
    k = 0
    while k < n:
        best = (1, 1, None)              # coverage, q, (count, steps)
        for q in range(1, _MAX_BLOCK + 1):
            if k + 2 * q > n:
                break
            b0 = toks[k:k + q]
            b1 = toks[k + q:k + 2 * q]
            if not all(a[2] and b[2] and a[0] == b[0] and len(a[1]) == len(b[1])
                       for a, b in zip(b0, b1)):
                continue
            steps = [y - x for a, b in zip(b0, b1)
                     for x, y in zip(a[1], b[1])]
            count = 2
            while k + (count + 1) * q <= n:
                bt = toks[k + count * q:k + (count + 1) * q]
                flat = [x for a in b0 for x in a[1]]
                ok = all(c[2] and c[0] == a[0] and len(c[1]) == len(a[1])
                         for a, c in zip(b0, bt))
                if ok:
                    got = [x for c in bt for x in c[1]]
                    ok = got == [x + count * s for x, s in zip(flat, steps)]
                if not ok:
                    break
                count += 1
            if count * q > best[0]:
                best = (count * q, q, (count, steps))
        if best[2] is None:
            out.append([[lines[k]], 1, [0] * len(toks[k][1])])
            k += 1
        else:
            _cov, q, (count, steps) = best
            out.append([list(lines[k:k + q]), count, steps])
            k += count * q
    return out


def decode_runs(segs: Sequence[Sequence[object]]) -> List[str]:
    """The lines of a stream in run form."""
    out: List[str] = []
    for block, count, steps in segs:
        split = [_NUM.split(l) for l in block]
        for t in range(count):
            j = 0
            for bits in split:
                pieces = []
                for i, piece in enumerate(bits):
                    if i % 2:
                        pieces.append(str(int(piece) + t * steps[j])
                                      if t else piece)
                        j += 1
                    else:
                        pieces.append(piece)
                out.append("".join(pieces))
    return out


def say_runs(lines: Sequence[str]) -> str:
    """A stream in segments (Phase 132): a repeated line as ``"tick" (500000
    times)``, a progression as ``"1" … "20000" (20000 lines; the number steps
    by 1)``, a progression of blocks as ``["tick", "N=1"] … ["tick",
    "N=30000"] (30000 times; the number steps by 1)``."""
    def show(block: Sequence[str]) -> str:
        if len(block) == 1:
            return f'"{block[0]}"'
        return "[" + ", ".join(f'"{l}"' for l in block) + "]"

    parts: List[str] = []
    for block, count, steps in output_runs(lines):
        if count == 1:
            parts.append(show(block))
        elif not any(steps):
            parts.append(f"{show(block)} ({count} times)")
        else:
            last = decode_runs([[block, 2, [(count - 1) * s
                                           for s in steps]]])[len(block):]
            unit = "lines" if len(block) == 1 else "times"
            how = (f"the number steps by {steps[0]}" if len(steps) == 1 else
                   "the numbers step by " + ", ".join(map(str, steps)))
            parts.append(f"{show(block)} … {show(last)} ({count} {unit}; "
                         f"{how})")
    return ", ".join(parts)


def _run_claim(run: bm.Run, values: Mapping[str, str]) -> Dict[str, object]:
    claim = {"kind": "run", "out": list(run.out), "err": list(run.err),
             "exit": run.exit_code, "steps": run.steps,
             "files": {k: list(v) for k, v in sorted(run.files.items())},
             "dirs": list(run.dirs), "values": dict(values)}
    if run.jumps:
        claim.update(kind="run_jump", budget=bm.BUDGET,
                     jumps=[list(jp[:3]) for jp in run.jumps])
        if len(run.out) + len(run.err) > RUN_FORM_LINES:
            del claim["out"], claim["err"]
            claim.update(out_runs=output_runs(run.out),
                         err_runs=output_runs(run.err))
    return claim


def growth_claim(diag: Mapping[str, object]) -> Dict[str, object]:
    """The column-3 claim of a diagnosis: the head, its visits, the shapes
    and the changing files (the block and the NRCI are not claimed)."""
    return {"kind": "growth", "budget": diag["budget"],
            "window": diag["window"], "head": diag["head"],
            "visits": diag["visits"],
            "shapes": {n: list(v) for n, v in sorted(diag["shapes"].items())},
            "files": list(diag["files"])}


_SHAPE_WORDS = {
    "translation": lambda n, p: (f"{n} moves by a fixed step "
                                 f"({'+' if p > 0 else ''}{p} per visit)"),
    "quadratic": lambda n, p: (f"{n} grows quadratically (second difference "
                               f"{p})"),
    "geometric": lambda n, p: f"{n} grows geometrically (ratio {p})",
    "irregular": lambda n, p: f"{n} changes irregularly",
    "text": lambda n, p: f"{n} changes as text",
}


def say_diagnosis(diag: Mapping[str, object]) -> str:
    """The answer to *why is it undecided?* (section 2 of the study)."""
    if diag["head"] is None:
        return (f"undecided: no line was visited {bm._MIN_VISITS} times in "
                f"{diag['budget']} steps")
    bits = [_SHAPE_WORDS[k](n, p) for n, (k, p) in sorted(diag["shapes"].items())]
    bits += [f"file {f} changes" for f in diag["files"]]
    blocked = diag["blocked"]
    if not blocked or blocked[0] == "no_recurrence":
        why = "found no recurring state with the counters masked"
    elif blocked[0] == "line":
        why = (f"found a recurring pass, but line {blocked[1]} cannot sit on "
               "one")
    elif blocked[0] == "cap":
        why = (f"found a jumpable pass, but its output would pass "
               f"{blocked[1]} lines")
    else:
        why = f"reached its limit of {bm.MAX_JUMPS} jumps"
    text = (f"undecided: at line {diag['head']} (visited {diag['visits']} "
            f"times in {diag['budget']} steps), "
            + ("; ".join(bits) if bits else "nothing changes")
            + f"; the counter-lasso reading {why}")
    notes = [f"a straight line fits {n}'s last {diag['window']} values with "
             f"NRCI {bm.nrci_decimal(v[1], 4)}" for n, v in sorted(diag["nrci"].items())
             if v is not None]
    if notes:
        text += (" (" + "; ".join(notes)
                 + "; this is a diagnosis, not a certificate)")
    return text


def say_shift(d: Sequence[Tuple[str, int]]) -> str:
    """``adds 3 to I and 1 to J`` -- what one pass does to the counters."""
    parts = [(f"adds {dn} to {n}" if dn > 0 else
              f"subtracts {-dn} from {n}" if dn < 0 else f"leaves {n} as it is")
             for n, dn in d]
    return " and ".join(parts) if parts else "changes no counter"


def say_growth(g: Sequence[Tuple[str, int]]) -> str:
    """``, adding 1 more to B on each later pass`` -- how a quadratic pass's
    step grows (Phase 142); empty for a translation."""
    parts = [(f"{gn} more to {n}" if gn > 0 else f"{-gn} less to {n}")
             for n, gn in g]
    return (", adding " + " and ".join(parts) + " on each later pass"
            if parts else "")


def say_jumps(run: bm.Run, program: Sequence[object]) -> str:
    """The jumps of a halting run, in words (Phase 130)."""
    out = []
    for jp in run.jumps:
        i, j, m, d, line, w = jp[:6]
        named = jp[6] if len(jp) > 6 else ()
        test = bm.render_line(program[line - 1]) if line else "a test"
        wrote = (f", writing {w} line{'s' if w != 1 else ''} each time"
                 if w else "")
        if w and named:
            wrote += f" (naming {', '.join(named)})"
        grow = say_growth(jp[7]) if len(jp) > 7 else ""
        out.append(f"the pass from step {i} to step {j} {say_shift(d)}{grow}, "
                   f"and was taken {m} times in one jump{wrote}, until {test} "
                   "changed")
    return "; ".join(out)


def say_lines(lines: Sequence[str]) -> str:
    """Runs of equal consecutive lines as ``"tick" (50000 times)`` (Phase
    131, for the output of a run that jumped a writing pass)."""
    parts: List[str] = []
    k = 0
    while k < len(lines):
        n = k
        while n < len(lines) and lines[n] == lines[k]:
            n += 1
        parts.append(f'"{lines[k]}"' + (f" ({n - k} times)" if n - k > 1
                                         else ""))
        k = n
    return ", ".join(parts)


def answer(question: str, program_text: str,
           env: Optional[Mapping[str, str]] = None,
           files: Optional[Mapping[str, Sequence[str]]] = None,
           dirs: Sequence[str] = (), verify: bool = True,
           jump: bool = True, extended: bool = True,
           affine: bool = True, quadratic: bool = True) -> Answer:
    """Answer an English question about a program, or refuse by name.
    ``jump=False`` reads runs as Phase 126 did, without the counter-lasso
    reading of Phase 130; ``extended=False`` reads them as Phase 130 did,
    without Phase 131's constant operands and writing passes; ``affine=False``
    reads them as Phase 131 did, without Phase 132's passes that write a
    counter (``studies/AFFINE_OUTPUT_STUDY.md``); ``quadratic=False`` reads
    them as Phase 132 did, without Phase 142's accumulators
    (``studies/QUADRATIC_LASSO_STUDY.md``)."""
    kind, arg = _classify(question)
    if kind is None:
        return _refuse(question, "UNREAD_QUESTION",
                       "no question form of the machine reads this")
    try:
        program, form = read_program(program_text)
    except bm.BatchError as exc:
        return _refuse(question, exc.name, exc.detail)
    lines = [bm.render_line(i) for i in program]
    col1 = say_program(program)
    col2 = list(lines)
    env = dict(env or {})
    files = {k: tuple(v) for k, v in (files or {}).items()}

    def done(text: str, claim: Dict[str, object], value: object,
             faculty: str = "derive") -> Answer:
        a = Answer(question, True, text, column1=col1, column2=col2,
                   claim=claim, value=value, faculty=faculty, form=form)
        if claim:
            a.script = column3_script(lines, claim, env, files, dirs)
            if verify:
                ok, last = run_script(a.script)
                a.verified = ok
                if not ok:
                    return _refuse(question, "SYNTAX", "column 3 did not verify: "
                                   + last, column1=col1, column2=col2)
        return a

    # ----- questions read from the text alone -----
    if kind == "say":
        rb = [bm.render_line(read_sentence(s)) for s in col1]
        claim = {"kind": "say", "read_back": rb, "limit": 200}
        return done(" ".join(col1), claim, col1, faculty="address")
    if kind == "uses":
        terms = list(bm.ladder_profile(program))
        from . import ops_ladder as ol
        return done("it uses " + ", ".join(ol.display(t) for t in terms),
                    {"kind": "uses", "terms": terms}, terms, faculty="address")
    if kind == "unreachable":
        dead = list(bm.unreachable_lines(program))
        text = ("no line is unreachable" if not dead else
                "unreachable: " + ", ".join(f"line {n}" for n in dead))
        return done(text, {"kind": "unreachable", "lines": dead}, dead)

    # ----- questions read from a run -----
    run = bm.run_program(program, env, files, dirs, jump=jump,
                         extended=extended, affine=affine,
                         quadratic=quadratic)
    col2 = col2 + [f"trace: {run.status} after {run.steps} steps"
                   + (f", lines {', '.join(map(str, run.trace[:40]))}"
                      if run.trace else "")]
    if kind == "why":
        if run.status != "undecided":
            return _refuse(question, "NOT_UNDECIDED",
                           f"the run is decided ({run.status} after "
                           f"{run.steps} steps)", column1=col1, column2=col2)
        third = bm.jumped_run(program, env, files, dirs,
                              extended=extended, affine=affine,
                              quadratic=quadratic)
        diag = bm.growth_diagnosis(program, env, files, dirs, run=third)
        claim = growth_claim(diag) if diag["head"] is not None else {}
        a = done(say_diagnosis(diag), claim, diag, faculty="refusal")
        return a
    if kind == "halts":
        if run.status == "never":
            i, j = run.certificate
            claim = never_claim(run)
            if run.forgotten:
                names = ", ".join(run.forgotten)
                return done(f"no, it never halts: with {names} forgotten (no "
                            "instruction reads "
                            + ("it" if len(run.forgotten) == 1 else "them")
                            + " except to update a forgotten variable), the "
                            f"control state before step {i} recurs before "
                            f"step {j}", claim, False)
            if run.lasso:
                return done(f"no, it never halts: the pass from step {i} to "
                            f"step {j} {say_shift(run.lasso)}"
                            f"{say_growth(run.growth)}, and no "
                            "comparison on it ever changes", claim, False)
            return done(f"no, it never halts: the control state before step "
                        f"{i} recurs before step {j}", claim, False)
        if run.status == "undecided":
            return _refuse(question, "UNDECIDED_WITHIN_BUDGET",
                           f"no control state recurred in {bm.BUDGET} steps; "
                           "it may halt later or never", column1=col1,
                           column2=col2)
    if run.status == "never" and run.lasso:
        return _refuse(question, "NEVER_HALTS", "the run never ends (the pass "
                       f"from step {run.certificate[0]} to step "
                       f"{run.certificate[1]} {say_shift(run.lasso)}"
                       f"{say_growth(run.growth)}, and no "
                       "comparison on it ever changes), so it has no final "
                       "answer", column1=col1, column2=col2)
    if run.status == "never":
        return _refuse(question, "NEVER_HALTS", "the run never ends ("
                       + (f"with {', '.join(run.forgotten)} forgotten, "
                          if run.forgotten else "")
                       + f"control state {run.certificate[0]} recurs at "
                       f"{run.certificate[1]}), so it has no final answer",
                       column1=col1, column2=col2)
    if run.status == "undecided":
        return _refuse(question, "UNDECIDED_WITHIN_BUDGET",
                       f"the run did not end within {bm.BUDGET} steps",
                       column1=col1, column2=col2)
    if run.undefined:
        return _refuse(question, "UNDEFINED_VARIABLE",
                       f"the answer depends on {', '.join(run.undefined)}, "
                       "which nothing binds", column1=col1, column2=col2)
    if kind == "idempotent":
        info = bm.idempotence(program, files, dirs, env)
        claim = {"kind": "idempotent", "idempotent": info["idempotent"],
                 "differing": info["differing_files"]}
        if info["idempotent"]:
            text = "yes, idempotent in state"
            if info["second_exit"] != info["first_exit"]:
                text += (f" (but the second run exits {info['second_exit']}"
                         f" where the first exits {info['first_exit']})")
        else:
            what = info["differing_files"] or ["the directories"]
            text = ("no: after a second run, " + ", ".join(what)
                    + (" differs" if len(what) == 1 else " differ"))
        return done(text, claim, info["idempotent"])
    values = {}
    if kind == "value":
        name = arg.upper()
        if name not in run.env:
            return _refuse(question, "UNDEFINED_VARIABLE",
                           f"{arg} is not bound at the end", column1=col1,
                           column2=col2)
        values = {name: run.env[name]}
    if kind == "file" and arg not in run.files:
        return _refuse(question, "NO_SUCH_FILE", f"no file {arg} at the end",
                       column1=col1, column2=col2)
    claim = _run_claim(run, values)
    if kind == "print":
        if any(jp[5] and len(jp) > 6 and jp[6] for jp in run.jumps) or (
                run.jumps and len(run.out) + len(run.err) > RUN_FORM_LINES):
            text = "it prints " + (say_runs(run.out) if run.out else "nothing")
        elif any(jp[5] for jp in run.jumps):
            text = "it prints " + (say_lines(run.out) if run.out else "nothing")
        else:
            text = "it prints " + (", ".join(f'"{s}"' for s in run.out)
                                   if run.out else "nothing")
        return done(text, claim, list(run.out))
    if kind == "stderr":
        return done("standard error: " + (", ".join(run.err) or "nothing"),
                    claim, list(run.err))
    if kind == "value":
        return done(f"{arg} is {run.env[arg.upper()]}", claim,
                    run.env[arg.upper()])
    if kind == "exit":
        return done(f"the exit code is {run.exit_code}", claim, run.exit_code)
    if kind == "halts":
        return done(f"yes, it halts after {run.steps} steps with exit code "
                    f"{run.exit_code}"
                    + (f" ({say_jumps(run, program)})" if run.jumps else ""),
                    claim, True)
    if kind == "steps":
        return done(f"{run.steps} steps", claim, run.steps)
    if kind == "files":
        written = list(bm.files_written(files, run))
        return done("it writes " + (", ".join(written) or "no file"), claim,
                    written)
    if kind == "file":
        return done(f"{arg} holds " + ", ".join(f'"{s}"' for s in
                                                run.files[arg]),
                    claim, list(run.files[arg]))
    return _refuse(question, "UNREAD_QUESTION", kind)  # pragma: no cover
