"""``glm_universal.reasoning.batch_machine`` -- GLM-BAT, an old-style machine.

The two lowest tiers of the operations ladder (``reasoning/ops_ladder.py``)
-- process, stream, file, environment variable, exit code; command, variable,
conditional, loop, jump, redirection, pipe -- made into a machine the GLM can
run a program on and so *work it out*.  The language is a small fragment of
DOS batch, chosen because it is the oldest widely known language in which
exactly those terms are the instructions: ``SET``, ``IF ERRORLEVEL``,
``GOTO``, ``CALL``, ``FOR``, ``>``, ``>>``, ``<``, ``|``, ``&&``, ``||``.

Everything here is exact and deterministic: a run is a function of the
program, the environment and the files it is given.  The fragment and its
declared departures from ``cmd.exe`` are §2.2 of
``studies/OPERATIONS_LADDER_STUDY.md``.

What the machine can say about a run
------------------------------------
* it **halted**, after ``n`` steps, with its outputs, files and exit code --
  the trace is the certificate;
* it **never halts** -- the control state (everything but the two output
  streams, which no instruction reads back) at step ``i`` recurs at step
  ``j``; ``RequestProject/GLM/OperationsLadder.lean``
  (``never_halts_of_projected_repeat``) is why that is a proof;
* it **never halts** past the control state (Phase 126) -- when the run above
  is undecided, the *inert* variables (:func:`inert_variables`: read only to
  update an inert variable) are forgotten as well, and a recurrence of what is
  left is the certificate; ``RequestProject/GLM/InertCounter.lean``
  (``never_halts_of_inert_repeat``) is why;
* it is **undecided** within the budget -- refused, never guessed.

And, built on runs: idempotence in state, drift and the reconciling program,
pipelines with gates and rollback, and the lines no control path reaches.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

__all__ = [
    "BatchError", "Cmd", "Pipe", "Chain", "If", "For", "Label", "Rem",
    "parse_line", "parse_program", "split_program", "Run", "run_program",
    "BUDGET", "idempotence", "drift", "reconcile_program", "run_pipeline",
    "unreachable_lines", "ladder_profile", "render_line", "uses_undefined",
    "files_written", "COMMANDS", "inert_variables", "is_closed_inert",
]

#: Steps a run may take before the machine refuses to say whether it halts.
BUDGET = 10_000

#: The commands of the fragment.  Anything else is ``UNKNOWN_COMMAND``.
COMMANDS: Tuple[str, ...] = ("ECHO", "SET", "TYPE", "DEL", "COPY", "MKDIR",
                             "SORT", "FIND", "GOTO", "CALL", "EXIT", "REM")

_COMPARISONS = ("EQU", "NEQ", "LSS", "LEQ", "GTR", "GEQ")

MSG_NO_FILE = "The system cannot find the file specified."
MSG_NO_PATH = "The system cannot find the path specified."
MSG_DIV_ZERO = "Divide by zero error."


class BatchError(ValueError):
    """A program the machine will not run, with the refusal's name."""

    def __init__(self, name: str, detail: str) -> None:
        super().__init__(f"{name}: {detail}")
        self.name = name
        self.detail = detail


# ===========================================================================
# 1.  THE INSTRUCTIONS
# ===========================================================================

@dataclass(frozen=True)
class Cmd:
    """One simple command: its name, its argument text, its redirections.

    ``name`` is one of ``ECHO SET SETA TYPE DEL COPY MKDIR SORT FIND FINDC
    GOTO CALL EXITB EXIT``; ``args`` is a tuple whose shape depends on it.
    """

    name: str
    args: Tuple[str, ...]
    redirs: Tuple[Tuple[str, str], ...] = ()


@dataclass(frozen=True)
class Pipe:
    stages: Tuple[Cmd, ...]


@dataclass(frozen=True)
class Chain:
    """``left op right``, ``op`` one of ``&&`` and ``||``; grouped left to
    right (``andThen_assoc``, ``orElse_assoc``)."""

    left: object
    op: str
    right: object


@dataclass(frozen=True)
class If:
    negate: bool
    cond: Tuple[str, ...]
    body: object


@dataclass(frozen=True)
class For:
    var: str
    items: Tuple[str, ...]
    body: object


@dataclass(frozen=True)
class Label:
    name: str


@dataclass(frozen=True)
class Rem:
    text: str


# ===========================================================================
# 2.  READING A LINE
# ===========================================================================

def _split_outside_quotes(text: str) -> List[Tuple[str, str]]:
    """Split ``text`` at ``&&``, ``||`` and ``|`` outside double quotes.
    Returns ``[(segment, separator_before)]``."""
    parts: List[Tuple[str, str]] = []
    buf: List[str] = []
    sep = ""
    quoted = False
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == '"':
            quoted = not quoted
            buf.append(ch)
            i += 1
            continue
        if not quoted and text.startswith("&&", i):
            parts.append(("".join(buf), sep))
            buf, sep = [], "&&"
            i += 2
            continue
        if not quoted and text.startswith("||", i):
            parts.append(("".join(buf), sep))
            buf, sep = [], "||"
            i += 2
            continue
        if not quoted and ch == "|":
            parts.append(("".join(buf), sep))
            buf, sep = [], "|"
            i += 1
            continue
        if not quoted and ch == "&":
            raise BatchError("SYNTAX", "a single '&' is not in the fragment")
        buf.append(ch)
        i += 1
    if quoted:
        raise BatchError("SYNTAX", "an unclosed double quote")
    parts.append(("".join(buf), sep))
    return parts


_REDIR = re.compile(r"\s*(>>|>|<)\s*([^\s<>|&\"]+)")


def _parse_redirs(text: str) -> Tuple[str, Tuple[Tuple[str, str], ...]]:
    quoted = False
    for i, ch in enumerate(text):
        if ch == '"':
            quoted = not quoted
        elif not quoted and ch in "<>":
            head, tail = text[:i], text[i:]
            redirs: List[Tuple[str, str]] = []
            pos = 0
            while pos < len(tail):
                m = _REDIR.match(tail, pos)
                if m is None:
                    if tail[pos:].strip():
                        raise BatchError("SYNTAX",
                                         f"a redirection is malformed: {tail!r}")
                    break
                redirs.append((m.group(1), m.group(2)))
                pos = m.end()
            return head.rstrip(), tuple(redirs)
    return text.rstrip(), ()


_NAME = r"[A-Za-z_][A-Za-z0-9_]*"
_EXPR_OK = re.compile(r"^[A-Za-z0-9_+\-*/%()%]+$")


def _parse_cmd(text: str, in_for: bool = False) -> Cmd:
    body, redirs = _parse_redirs(text.strip())
    if not body:
        raise BatchError("SYNTAX", "an empty command")
    word, _, rest = body.partition(" ")
    name = word.upper()
    rest = rest.strip()
    if name in ("MD",):
        name = "MKDIR"
    if name == "ECHO":
        if not rest:
            raise BatchError("SYNTAX", "ECHO needs text")
        if '"' in rest:
            raise BatchError("SYNTAX", "ECHO text with a double quote is not "
                             "in the fragment")
        return Cmd("ECHO", (rest,), redirs)
    if name == "SET":
        if rest.upper().startswith("/A "):
            m = re.match(rf"^({_NAME})\s*=\s*(.+)$", rest[3:].strip())
            if m is None:
                raise BatchError("SYNTAX", "SET /A needs NAME=expression")
            expr = re.sub(r"\s+", "", m.group(2))
            if not _EXPR_OK.match(expr):
                raise BatchError("SYNTAX", f"not an integer expression: {expr}")
            return Cmd("SETA", (m.group(1), expr), redirs)
        m = re.match(rf"^({_NAME})=(.*)$", rest)
        if m is None:
            raise BatchError("SYNTAX", "SET needs NAME=text")
        return Cmd("SET", (m.group(1), m.group(2)), redirs)
    if name in ("TYPE", "DEL", "MKDIR"):
        if not rest or " " in rest:
            raise BatchError("SYNTAX", f"{name} needs one path")
        return Cmd(name, (rest,), redirs)
    if name == "COPY":
        bits = rest.split()
        if len(bits) != 2:
            raise BatchError("SYNTAX", "COPY needs two paths")
        return Cmd("COPY", tuple(bits), redirs)
    if name == "SORT":
        if rest:
            raise BatchError("SYNTAX", "SORT takes no argument here")
        return Cmd("SORT", (), redirs)
    if name == "FIND":
        m = re.match(r'^(/C\s+)?"([^"]*)"$', rest, re.IGNORECASE)
        if m is None:
            raise BatchError("SYNTAX", 'FIND needs "text" or /C "text"')
        return Cmd("FINDC" if m.group(1) else "FIND", (m.group(2),), redirs)
    if name in ("GOTO", "CALL", "EXIT"):
        if redirs:
            raise BatchError("SYNTAX", f"{name} takes no redirection")
        if name == "GOTO":
            target = rest.strip()
            if not target or " " in target:
                raise BatchError("SYNTAX", "GOTO needs one label")
            if target.upper() == ":EOF":
                return Cmd("GOTO", (":EOF",))
            return Cmd("GOTO", (target.lstrip(":"),))
        if name == "CALL":
            if in_for:
                raise BatchError("SYNTAX", "CALL inside FOR is not in the "
                                 "fragment")
            if not re.match(rf"^:{_NAME}$", rest):
                raise BatchError("SYNTAX", "CALL needs :LABEL")
            return Cmd("CALL", (rest[1:],))
        m = re.match(r"^(/B)?\s*(-?\d+)?$", rest, re.IGNORECASE)
        if m is None:
            raise BatchError("SYNTAX", "EXIT needs [/B] [n]")
        code = m.group(2) or ""
        if m.group(1):
            return Cmd("EXITB", (code,))
        if not code:
            raise BatchError("SYNTAX", "EXIT needs a code here")
        return Cmd("EXIT", (code,))
    raise BatchError("UNKNOWN_COMMAND", f"{word} is not a command of the "
                     "fragment")


def _parse_chain(text: str, in_for: bool = False) -> object:
    parts = _split_outside_quotes(text)
    node: object = None
    pipe: List[Cmd] = []
    pending = ""
    for seg, sep in parts:
        if sep == "|":
            pipe.append(_parse_cmd(seg, in_for))
            continue
        if pipe:
            item = pipe[0] if len(pipe) == 1 else Pipe(tuple(pipe))
            node = item if node is None else Chain(node, pending, item)
        pipe = [_parse_cmd(seg, in_for)]
        pending = sep
    item = pipe[0] if len(pipe) == 1 else Pipe(tuple(pipe))
    node = item if node is None else Chain(node, pending, item)
    return node


def _parse_statement(text: str, in_for: bool = False) -> object:
    text = text.strip()
    upper = text.upper()
    if upper.startswith("IF "):
        rest = text[3:].strip()
        negate = False
        if rest.upper().startswith("NOT "):
            negate, rest = True, rest[4:].strip()
        m = re.match(r"^ERRORLEVEL\s+(\d+)\s+(.+)$", rest, re.IGNORECASE)
        if m:
            return If(negate, ("errorlevel", m.group(1)),
                      _parse_statement(m.group(2), in_for))
        m = re.match(r"^EXIST\s+(\S+)\s+(.+)$", rest, re.IGNORECASE)
        if m:
            return If(negate, ("exist", m.group(1)),
                      _parse_statement(m.group(2), in_for))
        m = re.match(rf"^DEFINED\s+({_NAME})\s+(.+)$", rest, re.IGNORECASE)
        if m:
            return If(negate, ("defined", m.group(1)),
                      _parse_statement(m.group(2), in_for))
        m = re.match(r'^"([^"]*)"=="([^"]*)"\s+(.+)$', rest)
        if m:
            return If(negate, ("streq", m.group(1), m.group(2)),
                      _parse_statement(m.group(3), in_for))
        m = re.match(r"^(\S+)\s+(EQU|NEQ|LSS|LEQ|GTR|GEQ)\s+(\S+)\s+(.+)$",
                     rest, re.IGNORECASE)
        if m:
            return If(negate, ("cmp", m.group(1), m.group(2).upper(),
                               m.group(3)),
                      _parse_statement(m.group(4), in_for))
        raise BatchError("SYNTAX", f"an IF the fragment does not read: {text}")
    if upper.startswith("FOR "):
        m = re.match(r"^FOR\s+%%([A-Za-z])\s+IN\s+\(([^)]*)\)\s+DO\s+(.+)$",
                     text, re.IGNORECASE)
        if m is None:
            raise BatchError("SYNTAX", "FOR needs %%V IN (items) DO command")
        items = tuple(m.group(2).split())
        if not items or any("," in it for it in items):
            raise BatchError("SYNTAX", "FOR items are words without commas")
        body = _parse_statement(m.group(3), in_for=True)
        if isinstance(body, For):
            raise BatchError("SYNTAX", "a FOR inside a FOR is not in the "
                             "fragment")
        return For(m.group(1), items, body)
    return _parse_chain(text, in_for)


def parse_line(text: str) -> object:
    """One line of a program, read into an instruction, or ``BatchError``."""
    stripped = text.strip()
    if not stripped:
        raise BatchError("SYNTAX", "an empty line")
    if stripped.startswith(":"):
        name = stripped[1:].strip()
        if not re.match(rf"^{_NAME}$", name):
            raise BatchError("SYNTAX", f"a label is one word: {stripped}")
        return Label(name)
    if stripped.upper() == "REM" or stripped.upper().startswith("REM "):
        return Rem(stripped[4:].strip())
    return _parse_statement(stripped)


def split_program(text: str) -> List[str]:
    """Lines of a program written as text: newlines or ``;;`` separate them,
    blank lines are dropped."""
    out: List[str] = []
    for raw in text.replace(";;", "\n").splitlines():
        if raw.strip():
            out.append(raw.strip())
    return out


def parse_program(lines: Sequence[str]) -> Tuple[object, ...]:
    """Every line read; the first line the machine will not read raises,
    with its line number (1-based) in the detail."""
    out = []
    for n, line in enumerate(lines, 1):
        try:
            out.append(parse_line(line))
        except BatchError as exc:
            raise BatchError(exc.name, f"line {n}: {exc.detail}") from None
    labels = [ins.name.upper() for ins in out if isinstance(ins, Label)]
    if len(labels) != len(set(labels)):
        raise BatchError("SYNTAX", "a label is declared twice")
    return tuple(out)


# ===========================================================================
# 3.  RENDERING AN INSTRUCTION BACK AS A LINE
# ===========================================================================

def _render_cmd(c: Cmd) -> str:
    n, a = c.name, c.args
    if n == "ECHO":
        head = f"ECHO {a[0]}"
    elif n == "SET":
        head = f"SET {a[0]}={a[1]}"
    elif n == "SETA":
        head = f"SET /A {a[0]}={a[1]}"
    elif n in ("TYPE", "DEL", "MKDIR"):
        head = f"{n} {a[0]}"
    elif n == "COPY":
        head = f"COPY {a[0]} {a[1]}"
    elif n == "SORT":
        head = "SORT"
    elif n == "FIND":
        head = f'FIND "{a[0]}"'
    elif n == "FINDC":
        head = f'FIND /C "{a[0]}"'
    elif n == "GOTO":
        head = f"GOTO {a[0]}"
    elif n == "CALL":
        head = f"CALL :{a[0]}"
    elif n == "EXITB":
        head = f"EXIT /B {a[0]}".rstrip()
    else:
        head = f"EXIT {a[0]}"
    for op, path in c.redirs:
        sep = "" if op != "<" and n == "ECHO" else " "
        head += f"{sep}{op} {path}"
    return head


def _render_stmt(s: object) -> str:
    if isinstance(s, Cmd):
        return _render_cmd(s)
    if isinstance(s, Pipe):
        return " | ".join(_render_cmd(c) for c in s.stages)
    if isinstance(s, Chain):
        return f"{_render_stmt(s.left)} {s.op} {_render_stmt(s.right)}"
    if isinstance(s, If):
        c = s.cond
        if c[0] == "errorlevel":
            cond = f"ERRORLEVEL {c[1]}"
        elif c[0] == "exist":
            cond = f"EXIST {c[1]}"
        elif c[0] == "defined":
            cond = f"DEFINED {c[1]}"
        elif c[0] == "streq":
            cond = f'"{c[1]}"=="{c[2]}"'
        else:
            cond = f"{c[1]} {c[2]} {c[3]}"
        return f"IF {'NOT ' if s.negate else ''}{cond} {_render_stmt(s.body)}"
    if isinstance(s, For):
        return (f"FOR %%{s.var} IN ({' '.join(s.items)}) DO "
                f"{_render_stmt(s.body)}")
    raise TypeError(s)


def render_line(ins: object) -> str:
    """The canonical text of an instruction (``parse_line`` reads it back)."""
    if isinstance(ins, Label):
        return f":{ins.name}"
    if isinstance(ins, Rem):
        return f"REM {ins.text}".rstrip()
    return _render_stmt(ins)


# ===========================================================================
# 4.  THE MACHINE
# ===========================================================================

_VAR = re.compile(rf"%({_NAME})%")


class _Ctx:
    """The mutable state of one run."""

    def __init__(self, env: Mapping[str, str], files: Mapping[str, Sequence[str]],
                 dirs: Sequence[str]) -> None:
        self.env: Dict[str, str] = {k.upper(): str(v) for k, v in env.items()}
        self.files: Dict[str, Tuple[str, ...]] = {
            k: tuple(v) for k, v in files.items()}
        self.dirs = set(dirs)
        self.out: List[str] = []
        self.err: List[str] = []
        self.errorlevel = 0
        self.undefined: List[str] = []

    def expand(self, text: str) -> str:
        def sub(m: "re.Match[str]") -> str:
            name = m.group(1).upper()
            if name in self.env:
                return self.env[name]
            if name == "ERRORLEVEL":
                return str(self.errorlevel)
            self.undefined.append(name)
            return ""
        return _VAR.sub(sub, text)

    def control(self, pc: int, stack: Tuple[int, ...],
                forget: frozenset = frozenset()) -> Tuple:
        env = (self.env.items() if not forget else
               ((k, v) for k, v in self.env.items() if k not in forget))
        return (pc, tuple(sorted(env)),
                tuple(sorted(self.files.items())), tuple(sorted(self.dirs)),
                stack, self.errorlevel)

    def parent_ok(self, path: str) -> bool:
        if "/" not in path:
            return True
        return path.rsplit("/", 1)[0] in self.dirs


def _int_expr(expr: str, ctx: _Ctx) -> Optional[int]:
    """Evaluate a ``SET /A`` expression exactly; ``None`` on division by
    zero.  Names read as integers (an unbound name reads as 0 and is recorded
    as an undefined read)."""
    tokens = re.findall(r"\d+|[A-Za-z_][A-Za-z0-9_]*|[-+*/%()]", expr)
    if "".join(tokens) != expr:
        raise BatchError("SYNTAX", f"not an integer expression: {expr}")
    pos = 0

    def peek() -> str:
        return tokens[pos] if pos < len(tokens) else ""

    def take() -> str:
        nonlocal pos
        pos += 1
        return tokens[pos - 1]

    def atom() -> Optional[int]:
        t = take() if pos < len(tokens) else ""
        if t == "(":
            v = add()
            if take() != ")":
                raise BatchError("SYNTAX", f"unbalanced parentheses: {expr}")
            return v
        if t == "-":
            v = atom()
            return None if v is None else -v
        if t.isdigit():
            return int(t)
        if re.match(_NAME, t or "0"):
            name = t.upper()
            if name not in ctx.env:
                ctx.undefined.append(name)
                return 0
            raw = ctx.env[name]
            if not re.match(r"^-?\d+$", raw):
                return 0
            return int(raw)
        raise BatchError("SYNTAX", f"not an integer expression: {expr}")

    def mul() -> Optional[int]:
        v = atom()
        while peek() in ("*", "/", "%"):
            op = take()
            w = atom()
            if v is None or w is None:
                v = None
                continue
            if op == "*":
                v = v * w
            elif w == 0:
                v = None
            else:
                q = abs(v) // abs(w)
                q = q if (v >= 0) == (w >= 0) else -q
                v = q if op == "/" else v - w * q
        return v

    def add() -> Optional[int]:
        v = mul()
        while peek() in ("+", "-"):
            op = take()
            w = mul()
            if v is None or w is None:
                v = None
                continue
            v = v + w if op == "+" else v - w
        return v

    value = add()
    if pos != len(tokens):
        raise BatchError("SYNTAX", f"not an integer expression: {expr}")
    return value


def _run_cmd(c: Cmd, ctx: _Ctx, stdin: Optional[List[str]],
             subst: Mapping[str, str]) -> Tuple[List[str], bool, bool, object]:
    """``(output lines, succeeded, sets the exit code, control effect)``."""

    def arg(i: int) -> str:
        text = c.args[i]
        for var, value in subst.items():
            text = text.replace(f"%%{var}", value)
        return ctx.expand(text)

    for op, path in c.redirs:
        if op == "<":
            p = ctx.expand(path)
            if p not in ctx.files:
                ctx.err.append(MSG_NO_FILE)
                return [], False, True, None
            stdin = list(ctx.files[p])
    n = c.name
    if n == "ECHO":
        return [arg(0)], True, False, None
    if n == "SET":
        name, value = c.args[0].upper(), arg(1)
        if value:
            ctx.env[name] = value
        else:
            ctx.env.pop(name, None)
        return [], True, False, None
    if n == "SETA":
        value = _int_expr(arg(1), ctx)
        if value is None:
            ctx.err.append(MSG_DIV_ZERO)
            return [], False, True, None
        ctx.env[c.args[0].upper()] = str(value)
        return [], True, False, None
    if n == "TYPE":
        p = arg(0)
        if p not in ctx.files:
            ctx.err.append(MSG_NO_FILE)
            return [], False, True, None
        return list(ctx.files[p]), True, True, None
    if n == "DEL":
        p = arg(0)
        if p not in ctx.files:
            ctx.err.append(f"Could Not Find {p}")
            return [], False, True, None
        del ctx.files[p]
        return [], True, True, None
    if n == "COPY":
        a, b = arg(0), arg(1)
        if a not in ctx.files:
            ctx.err.append(MSG_NO_FILE)
            return [], False, True, None
        if not ctx.parent_ok(b):
            ctx.err.append(MSG_NO_PATH)
            return [], False, True, None
        ctx.files[b] = ctx.files[a]
        return ["        1 file(s) copied."], True, True, None
    if n == "MKDIR":
        p = arg(0)
        if p in ctx.dirs or p in ctx.files:
            ctx.err.append(f"A subdirectory or file {p} already exists.")
            return [], False, True, None
        parts = p.split("/")
        for k in range(1, len(parts) + 1):
            ctx.dirs.add("/".join(parts[:k]))
        return [], True, True, None
    if n == "SORT":
        return sorted(stdin or []), True, True, None
    if n in ("FIND", "FINDC"):
        needle = arg(0)
        hits = [line for line in (stdin or []) if needle in line]
        if n == "FIND":
            return hits, bool(hits), True, None
        return [str(len(hits))], bool(hits), True, None
    if n == "GOTO":
        return [], True, False, ("goto", c.args[0])
    if n == "CALL":
        return [], True, False, ("call", c.args[0])
    if n == "EXITB":
        code = arg(0)
        return [], True, False, ("exitb", int(code) if code else None)
    if n == "EXIT":
        return [], True, False, ("exit", int(arg(0)))
    raise BatchError("UNKNOWN_COMMAND", n)  # pragma: no cover


def _run_pipe(stages: Sequence[Cmd], ctx: _Ctx,
              subst: Mapping[str, str]) -> Tuple[bool, object]:
    data: Optional[List[str]] = None
    ok, sets = True, False
    effect: object = None
    for k, c in enumerate(stages):
        data, ok, sets, effect = _run_cmd(c, ctx, data if k else None, subst)
        if effect is not None:
            break
    target = [r for r in stages[-1].redirs if r[0] in (">", ">>")]
    lines = data or []
    if target and effect is None:
        op, path = target[-1]
        p = ctx.expand(path)
        if not ctx.parent_ok(p) or p in ctx.dirs:
            ctx.err.append(MSG_NO_PATH)
            ctx.errorlevel = 1
            return False, None
        if op == ">":
            ctx.files[p] = tuple(lines)
        else:
            ctx.files[p] = ctx.files.get(p, ()) + tuple(lines)
    else:
        ctx.out.extend(lines)
    if sets:
        ctx.errorlevel = 0 if ok else 1
    return ok, effect


def _run_stmt(s: object, ctx: _Ctx,
              subst: Mapping[str, str]) -> Tuple[bool, object]:
    if isinstance(s, Cmd):
        return _run_pipe((s,), ctx, subst)
    if isinstance(s, Pipe):
        return _run_pipe(s.stages, ctx, subst)
    if isinstance(s, Chain):
        ok, effect = _run_stmt(s.left, ctx, subst)
        if effect is not None:
            return ok, effect
        if (s.op == "&&") == ok:
            return _run_stmt(s.right, ctx, subst)
        return ok, None
    if isinstance(s, If):
        c = s.cond

        def val(text: str) -> str:
            for var, value in subst.items():
                text = text.replace(f"%%{var}", value)
            return ctx.expand(text)

        if c[0] == "errorlevel":
            truth = ctx.errorlevel >= int(c[1])
        elif c[0] == "exist":
            p = val(c[1])
            truth = p in ctx.files or p in ctx.dirs
        elif c[0] == "defined":
            truth = c[1].upper() in ctx.env
        elif c[0] == "streq":
            truth = val(c[1]) == val(c[2])
        else:
            a, op, b = val(c[1]), c[2], val(c[3])
            if re.match(r"^-?\d+$", a) and re.match(r"^-?\d+$", b):
                x, y = int(a), int(b)
                cmp = (x > y) - (x < y)
            else:
                cmp = (a > b) - (a < b)
            truth = {"EQU": cmp == 0, "NEQ": cmp != 0, "LSS": cmp < 0,
                     "LEQ": cmp <= 0, "GTR": cmp > 0, "GEQ": cmp >= 0}[op]
        if truth != s.negate:
            return _run_stmt(s.body, ctx, subst)
        return True, None
    if isinstance(s, For):
        ok = True
        for item in s.items:
            inner = dict(subst)
            inner[s.var] = item
            ok, effect = _run_stmt(s.body, ctx, inner)
            if effect is not None:
                return ok, effect
        return ok, None
    raise TypeError(s)  # pragma: no cover


@dataclass
class Run:
    """What one run of a program gave."""

    status: str                     # halted | never | undecided
    steps: int
    out: Tuple[str, ...]
    err: Tuple[str, ...]
    exit_code: Optional[int]
    env: Dict[str, str]
    files: Dict[str, Tuple[str, ...]]
    dirs: Tuple[str, ...]
    trace: Tuple[int, ...]          # the 1-based line of each step
    certificate: Optional[Tuple[int, int]] = None
    undefined: Tuple[str, ...] = ()
    controls: Tuple[Tuple, ...] = field(default=(), repr=False)
    forgotten: Tuple[str, ...] = ()  # inert names left out of the certificate

    @property
    def halted(self) -> bool:
        return self.status == "halted"


def _labels(program: Sequence[object]) -> Dict[str, int]:
    return {ins.name.upper(): i for i, ins in enumerate(program)
            if isinstance(ins, Label)}


def run_program(program: Sequence[object], env: Optional[Mapping[str, str]] = None,
                files: Optional[Mapping[str, Sequence[str]]] = None,
                dirs: Sequence[str] = (), budget: int = BUDGET,
                keep_controls: bool = False, inert: bool = True,
                forget: Sequence[str] = ()) -> Run:
    """Run a parsed program from the given environment and files.

    The control state is recorded *before* each step; the first recurrence
    ``s_i = s_j`` (least ``j``) ends the run as ``never``, and ``budget``
    steps with no recurrence end it as ``undecided``.  An undecided run is
    then re-read once with the :func:`inert_variables` left out of the
    control state (``inert``, Phase 126); a recurrence there ends it as
    ``never`` with the forgotten names in ``Run.forgotten``.  ``forget``
    names the variables to leave out directly (the re-reading itself).
    """
    first = _run(program, env, files, dirs, budget, keep_controls,
                 frozenset(n.upper() for n in forget))
    if first.status != "undecided" or not inert or forget:
        return first
    names = inert_variables(program)
    if not names:
        return first
    second = _run(program, env, files, dirs, budget, keep_controls,
                  frozenset(names))
    return second if second.status == "never" else first


def _run(program: Sequence[object], env: Optional[Mapping[str, str]],
         files: Optional[Mapping[str, Sequence[str]]], dirs: Sequence[str],
         budget: int, keep_controls: bool, forget: frozenset) -> Run:
    ctx = _Ctx(env or {}, files or {}, dirs)
    labels = _labels(program)
    pc, stack = 0, ()
    seen: Dict[Tuple, int] = {}
    controls: List[Tuple] = []
    trace: List[int] = []
    steps = 0
    exit_code: Optional[int] = None
    status = "undecided"
    cert = None
    while True:
        if pc >= len(program):
            exit_code, status = ctx.errorlevel, "halted"
            break
        state = ctx.control(pc, stack, forget)
        if state in seen:
            status, cert = "never", (seen[state], steps)
            break
        seen[state] = steps
        if keep_controls:
            controls.append(state)
        if steps >= budget:
            break
        steps += 1
        trace.append(pc + 1)
        ins = program[pc]
        if isinstance(ins, (Label, Rem)):
            pc += 1
            continue
        _ok, effect = _run_stmt(ins, ctx, {})
        if effect is None:
            pc += 1
            continue
        kind, arg = effect
        if kind == "exit":
            ctx.errorlevel = arg
            exit_code, status = arg, "halted"
            break
        if kind == "exitb" or (kind == "goto" and arg == ":EOF"):
            if kind == "exitb" and arg is not None:
                ctx.errorlevel = arg
            if stack:
                pc, stack = stack[-1], stack[:-1]
                continue
            exit_code, status = ctx.errorlevel, "halted"
            break
        target = labels.get(str(arg).upper())
        if target is None:
            ctx.err.append("The system cannot find the batch label specified "
                           f"- {arg}")
            ctx.errorlevel = 1
            exit_code, status = 1, "halted"
            break
        if kind == "call":
            stack = stack + (pc + 1,)
        pc = target + 1
    return Run(status, steps, tuple(ctx.out), tuple(ctx.err), exit_code,
               dict(ctx.env), dict(ctx.files), tuple(sorted(ctx.dirs)),
               tuple(trace), cert, tuple(dict.fromkeys(ctx.undefined)),
               tuple(controls),
               tuple(sorted(forget)) if status == "never" else ())


# ---------------------------------------------------------------------------
# Inert variables (Phase 126, studies/INERT_COUNTER_STUDY.md section 2)
# ---------------------------------------------------------------------------

def _mentions(line: str, name: str) -> bool:
    return re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])",
                     line, re.IGNORECASE) is not None


def _inert_target(ins: object) -> Optional[str]:
    """The assigned name when ``ins`` is a lone assignment that may be inert:
    ``SET V=text``, or ``SET /A V=expr`` with no ``/`` or ``%`` in ``expr``,
    with no redirection, pipe or chain; otherwise ``None``."""
    if not isinstance(ins, Cmd) or ins.redirs:
        return None
    if ins.name == "SET":
        return ins.args[0].upper()
    if ins.name == "SETA" and not re.search(r"[/%]", ins.args[1]):
        return ins.args[0].upper()
    return None


def is_closed_inert(program: Sequence[object], names: Sequence[str]) -> bool:
    """Every line that mentions a name of ``names`` is a lone inert
    assignment to a name of ``names`` (section 2 of the study)."""
    F = {n.upper() for n in names}
    if "ERRORLEVEL" in F:
        return False
    for ins in program:
        line = render_line(ins)
        if any(_mentions(line, n) for n in F):
            target = _inert_target(ins)
            if target is None or target not in F or re.search(r"[<>|&]", line):
                return False
    return True


def inert_variables(program: Sequence[object]) -> Tuple[str, ...]:
    """The largest closed set of inert variable names, sorted."""
    F = {t for t in (_inert_target(ins) for ins in program) if t}
    F.discard("ERRORLEVEL")
    changed = True
    while changed:
        changed = False
        for ins in program:
            line = render_line(ins)
            hit = {n for n in F if _mentions(line, n)}
            if not hit:
                continue
            target = _inert_target(ins)
            if target is None or target not in F or re.search(r"[<>|&]", line):
                F -= hit
                changed = True
    return tuple(sorted(F))


def uses_undefined(run: Run) -> bool:
    return bool(run.undefined)


def files_written(before: Mapping[str, Sequence[str]], run: Run) -> Tuple[str, ...]:
    """The files a run created or changed, sorted."""
    return tuple(sorted(p for p, v in run.files.items()
                        if tuple(before.get(p, ())) != v or p not in before))


# ===========================================================================
# 5.  WHAT IS BUILT ON RUNS
# ===========================================================================

def idempotence(program: Sequence[object],
                files: Optional[Mapping[str, Sequence[str]]] = None,
                dirs: Sequence[str] = (),
                env: Optional[Mapping[str, str]] = None) -> Dict[str, object]:
    """Run twice from ``files``; idempotent in state when the files and
    directories after two runs equal those after one."""
    first = run_program(program, env, files, dirs)
    if not first.halted:
        raise BatchError("UNDECIDED_WITHIN_BUDGET" if first.status ==
                         "undecided" else "NEVER_HALTS",
                         "idempotence needs a run that ends")
    second = run_program(program, env, first.files, first.dirs)
    if not second.halted:
        raise BatchError("UNDECIDED_WITHIN_BUDGET", "the second run did not end")
    differ = sorted(set(p for p in set(first.files) | set(second.files)
                        if first.files.get(p) != second.files.get(p)))
    same = not differ and first.dirs == second.dirs
    return {"idempotent": same, "differing_files": differ,
            "first_exit": first.exit_code, "second_exit": second.exit_code,
            "second_err": list(second.err), "first": first, "second": second}


def drift(desired: Mapping[str, Sequence[str]],
          actual: Mapping[str, Sequence[str]]) -> Tuple[str, ...]:
    """Desired files whose actual content differs or is missing (unmanaged
    files are never drift; ``GLM.OperationsLadder.drift``)."""
    return tuple(sorted(p for p, v in desired.items()
                        if tuple(actual.get(p, ())) != tuple(v)
                        or p not in actual))


def reconcile_program(desired: Mapping[str, Sequence[str]],
                      actual: Mapping[str, Sequence[str]]) -> List[str]:
    """The GLM-BAT program that writes every drifted file."""
    lines: List[str] = []
    made: set = set()
    for path in drift(desired, actual):
        content = list(desired[path])
        if not content or any(not s.strip() or any(ch in s for ch in '<>|&%"')
                              or s != s.rstrip() for s in content):
            raise BatchError("SYNTAX", f"{path}: content ECHO cannot write")
        if "/" in path:
            parts = path.split("/")[:-1]
            d = "/".join(parts)
            if d not in made:
                lines.append(f"IF NOT EXIST {d} MKDIR {d}")
                made.add(d)
        lines.append(f"ECHO {content[0]}> {path}")
        for s in content[1:]:
            lines.append(f"ECHO {s}>> {path}")
    return lines


def run_pipeline(stages: Sequence[Tuple[str, Sequence[object]]],
                 files: Optional[Mapping[str, Sequence[str]]] = None,
                 rollback: bool = False) -> Dict[str, object]:
    """Run stages on one shared set of files; stop at the first stage whose
    exit code is not 0 (``promoted_iff_all_pass``); with ``rollback`` a failed
    pipeline restores the files it started from (``rollback_restores``)."""
    start = {k: tuple(v) for k, v in (files or {}).items()}
    current: Dict[str, Tuple[str, ...]] = dict(start)
    dirs: Tuple[str, ...] = ()
    passed: List[str] = []
    failed: Optional[str] = None
    for name, program in stages:
        r = run_program(program, None, current, dirs)
        if not r.halted:
            raise BatchError("UNDECIDED_WITHIN_BUDGET", f"stage {name}")
        current, dirs = r.files, r.dirs
        if r.exit_code != 0:
            failed = name
            break
        passed.append(name)
    promoted = failed is None
    if not promoted and rollback:
        current, dirs = dict(start), ()
    return {"promoted": promoted, "passed": passed, "failed_at": failed,
            "files": current, "dirs": dirs}


def _targets(s: object) -> List[Tuple[str, str]]:
    if isinstance(s, Cmd):
        return [(s.name, s.args[0])] if s.name in ("GOTO", "CALL") else []
    if isinstance(s, Pipe):
        return [t for c in s.stages for t in _targets(c)]
    if isinstance(s, Chain):
        return _targets(s.left) + _targets(s.right)
    if isinstance(s, (If, For)):
        return _targets(s.body)
    return []


def _ends(s: object) -> bool:
    """Whether a statement may end the program or return."""
    if isinstance(s, Cmd):
        return s.name in ("EXIT", "EXITB") or (s.name == "GOTO"
                                                and s.args[0] == ":EOF")
    if isinstance(s, Pipe):
        return any(_ends(c) for c in s.stages)
    if isinstance(s, Chain):
        return _ends(s.left) or _ends(s.right)
    if isinstance(s, (If, For)):
        return _ends(s.body)
    return False


def unreachable_lines(program: Sequence[object]) -> Tuple[int, ...]:
    """1-based lines no path of the control-flow graph reaches, every
    conditional taken both ways (sound for "unreachable" only)."""
    labels = _labels(program)
    returns = [i + 1 for i, ins in enumerate(program)
               if any(k == "CALL" for k, _ in _targets(ins))]
    succ: Dict[int, List[int]] = {}
    for i, ins in enumerate(program):
        nxt: List[int] = []
        bare = isinstance(ins, Cmd)
        unconditional_jump = bare and ins.name == "GOTO" and ins.args[0] != ":EOF"
        unconditional_end = bare and _ends(ins)
        if not (unconditional_jump or unconditional_end):
            nxt.append(i + 1)
        for kind, target in _targets(ins):
            if target == ":EOF":
                continue
            j = labels.get(target.upper())
            if j is not None:
                nxt.append(j)
        if _ends(ins):
            nxt.extend(returns)
        succ[i] = nxt
    seen = {0} if program else set()
    todo = [0] if program else []
    while todo:
        i = todo.pop()
        for j in succ.get(i, ()):
            if j < len(program) and j not in seen:
                seen.add(j)
                todo.append(j)
    return tuple(i + 1 for i in range(len(program)) if i not in seen)


# ===========================================================================
# 6.  THE LADDER TERMS A PROGRAM USES
# ===========================================================================

def _profile_stmt(s: object, out: set) -> None:
    if isinstance(s, Cmd):
        out.add("command")
        if s.args and s.name not in ("SORT",):
            out.add("argument")
        if s.name in ("SET", "SETA"):
            out.update(("variable", "assignment", "env_var"))
        if s.name in ("TYPE", "DEL", "COPY", "MKDIR"):
            out.add("file")
        if s.name in ("ECHO", "TYPE", "SORT", "FIND", "FINDC"):
            out.add("stream")
        if s.name in ("GOTO", "CALL"):
            out.add("jump")
        if s.name in ("EXIT", "EXITB"):
            out.add("exit_code")
        if any("%" in a for a in s.args):
            out.update(("substitution", "env_var"))
        if s.redirs:
            out.update(("redirection", "file", "stream"))
    elif isinstance(s, Pipe):
        out.update(("pipe", "stream"))
        for c in s.stages:
            _profile_stmt(c, out)
    elif isinstance(s, Chain):
        out.update(("exit_handling", "exit_code"))
        _profile_stmt(s.left, out)
        _profile_stmt(s.right, out)
    elif isinstance(s, If):
        out.add("conditional")
        if s.cond[0] == "errorlevel":
            out.update(("exit_handling", "exit_code"))
        if s.cond[0] == "exist":
            out.add("file")
        if s.cond[0] in ("defined",):
            out.update(("variable", "env_var"))
        if any("%" in x for x in s.cond[1:]):
            out.update(("substitution", "env_var"))
        _profile_stmt(s.body, out)
    elif isinstance(s, For):
        out.add("loop")
        _profile_stmt(s.body, out)


def ladder_profile(program: Sequence[object]) -> Tuple[str, ...]:
    """The operations-ladder terms a program uses, in ladder order."""
    from . import ops_ladder as ol
    used = {"script", "process"}
    for ins in program:
        if isinstance(ins, Label):
            used.add("jump")
        elif not isinstance(ins, Rem):
            _profile_stmt(ins, used)
    order = [t for t in ol.term_ids() if t in used]
    return tuple(order)
