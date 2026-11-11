"""leechlean.lean_parts -- tokenize Lean 4 files into the recurring "parts".

A **part** is any fragment that recurs across a Lean development.  This module
recognises four granularities:

  * **token parts** -- lexer tokens.  Whitespace runs, comments and string
    literals are kept verbatim (kind ``ws``/``comment``/``str``) so that the
    token sequence concatenates back to the exact file bytes.  Structural
    tokens are classified ``kw`` (keyword), ``ident`` (identifier, including
    dotted/primed/Unicode names), ``num``, ``sym`` (operator/punctuation),
    ``doc`` (the ``/-!``, ``/--`` ... comment *tags* are folded into the
    comment token).
  * **bigram parts** -- adjacent structural token pairs (the composite
    fragments: ``:= by``, ``theorem <name>``, ``) (`` ...).
  * **frame parts** -- one per declaration: keyword + shape (has ``by``,
    statement length bucket).
  * **tactic parts** -- tactic head names, from the token following ``by`` and
    the heads of the indented tactic lines of its block (a lexical reading of
    proof blocks, stated precisely in the report).

The tokenizer is a hand-written lexer for the fragment of Lean 4 the corpus
uses (validated by the byte-exact round-trip of :mod:`leechlean.codec`); it is
not the elaborator, and the report says so.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

# --------------------------------------------------------------------------
# lexer tables
# --------------------------------------------------------------------------

KEYWORDS = frozenset("""
theorem def lemma instance abbrev example structure inductive class
axiom import open namespace end section variable universe set_option
noncomputable partial unsafe opaque by let have show from in do if then else
match with at as return mut for while try catch finally deriving where extends
private protected public macro syntax elab attr
fun forall exists
""".split())

HASH_COMMANDS = frozenset(("#check", "#eval", "#print", "#reduce", "#explain",
                           "#minimports", "#exit"))

# multi-character ASCII symbols first, then single
SYMBOLS = ["<;>", ":=", "=>", "<|", "|>", "<=", ">=", "==", "!=", "/=",
           "&&", "||", "++", "::", "..", "<>", "!}"]
_SINGLE_SYM = set("()[]{}<>|=+-*/^.,;:!?'@$&~#⟨⟩⟦⟧‹›«»∘·×∑∀∃∈∉∧∨¬→←↔≤≥≠≈⁻¹₀₁₂₃₄₅₆₇₈₉᾿")

# Identifier alphabet: ASCII, Greek (0x374-0x3ff), superscripts/subscripts and
# Letterlike symbols (0x2070-0x218f: ℕ ℤ ℚ ℝ ⁻ ¹ ₂ ...), and mathematical
# alphanumerics (U+1D400-U+1D7FF, written with the 8-digit \U escape: \u1d400
# would be read as \u1d40 + '0').  Operators (0x2190-0x2bff: ∀ ∈ ∧ → ∑ ...) are
# symbols, not identifier characters.
_IDENT_START = re.compile(r"[A-Za-z_\u0374-\u03ff\u2070-\u218f\U0001d400-\U0001d7ff]")
_IDENT_CONT = re.compile(r"[A-Za-z0-9_.'!?\u0374-\u03ff\u2070-\u218f\U0001d400-\U0001d7ff]")
_NUM_START = re.compile(r"[0-9]")
_NUM_CONT = re.compile(r"[0-9a-zA-Z_]")


@dataclass
class Tok:
    kind: str      # kw, ident, num, str, sym, ws, comment
    text: str
    line: int
    col: int

    @property
    def key(self) -> str:
        return f"{self.kind}:{self.text}"


def tokenize(text: str) -> List[Tok]:
    """Lex one Lean 4 file into a token list whose concatenation is the file.

    Nested block comments (Lean's ``/- ... -/`` nests), line comments, string
    and char literals, backtick-quoted identifiers, numeric literals with
    0x/0b/0o prefixes and Unicode identifiers are handled.  Whitespace runs
    and whole comments are single tokens with their exact bytes.
    """
    out: List[Tok] = []
    i, n = 0, len(text)
    line, col = 1, 0

    def emit(kind: str, start: int, end: int):
        out.append(Tok(kind, text[start:end], line, col))

    while i < n:
        c = text[i]
        # newline bookkeeping
        if c == "\n":
            j = i
            while j < n and text[j] in "\n":
                j += 1
            emit("ws", i, j)
            line += j - i
            col = 0
            i = j
            continue
        if c in " \t\r\f\v":
            j = i
            while j < n and text[j] in " \t\r\f\v":
                j += 1
            emit("ws", i, j)
            col += j - i
            i = j
            continue
        # line comment
        if c == "-" and i + 1 < n and text[i + 1] == "-":
            j = text.find("\n", i)
            j = n if j < 0 else j
            emit("comment", i, j)
            col += j - i
            i = j
            continue
        # block comment (nests!)
        if c == "/" and i + 1 < n and text[i + 1] == "-":
            depth, j = 1, i + 2
            while j < n and depth:
                if text.startswith("/-", j):
                    depth += 1
                    j += 2
                elif text.startswith("-/", j):
                    depth -= 1
                    j += 2
                else:
                    j += 1
            emit("comment", i, j)
            col += j - i
            i = j
            continue
        # string literal
        if c == '"':
            j = i + 1
            while j < n:
                if text[j] == "\\":
                    j += 2
                elif text[j] == '"':
                    j += 1
                    break
                else:
                    j += 1
            emit("str", i, j)
            col += j - i
            i = j
            continue
        # backtick-quoted identifier
        if c == "`":
            j = i + 1
            if j < n and _IDENT_START.match(text[j]):
                k = j + 1
                while k < n and _IDENT_CONT.match(text[k]):
                    k += 1
                emit("ident", i, k)
                col += k - i
                i = k
                continue
            emit("sym", i, i + 1)
            col += 1
            i += 1
            continue
        # hash commands
        if c == "#":
            k = i + 1
            while k < n and _IDENT_CONT.match(text[k]):
                k += 1
            word = text[i:k]
            emit("kw" if word in HASH_COMMANDS else "sym", i, k)
            col += k - i
            i = k
            continue
        # number
        if _NUM_START.match(c):
            j = i + 1
            while j < n and _NUM_CONT.match(text[j]):
                j += 1
            # do not swallow a trailing '.' that starts '.foo'?  Lean numbers
            # can continue with '.', but '1.foo' vs '1 .foo' -- keep the dot
            # only if followed by a digit
            while j < n and text[j] == "." and j + 1 < n and _NUM_START.match(text[j + 1]):
                j += 1
                while j < n and _NUM_CONT.match(text[j]):
                    j += 1
            emit("num", i, j)
            col += j - i
            i = j
            continue
        # identifier / keyword
        if _IDENT_START.match(c):
            j = i + 1
            while j < n and _IDENT_CONT.match(text[j]):
                j += 1
            # '!' / '?' suffix used by some tactic aliases: already in CONT
            word = text[i:j]
            emit("kw" if word in KEYWORDS else "ident", i, j)
            col += j - i
            i = j
            continue
        # symbols: longest match
        matched = False
        for s in SYMBOLS:
            if text.startswith(s, i):
                emit("sym", i, i + len(s))
                col += len(s)
                i += len(s)
                matched = True
                break
        if matched:
            continue
        if c in _SINGLE_SYM:
            emit("sym", i, i + 1)
            col += 1
            i += 1
            continue
        # unknown single character (unicode symbol seen once etc.)
        emit("sym", i, i + 1)
        col += 1
        i += 1
    return out


# --------------------------------------------------------------------------
# structure extraction on top of the token stream
# --------------------------------------------------------------------------

DECL_KW = frozenset(("theorem", "def", "lemma", "instance", "abbrev",
                     "example", "structure", "inductive", "class", "axiom",
                     "opaque"))


def structural(toks: Sequence[Tok]) -> List[Tuple[int, Tok]]:
    """Indices+tokens of non-ws, non-comment tokens."""
    return [(i, t) for i, t in enumerate(toks)
            if t.kind not in ("ws", "comment")]


def bigrams(toks: Sequence[Tok]) -> List[str]:
    """Adjacent structural token pairs, as part keys ``b:<k1>|<k2>``."""
    st = structural(toks)
    return [f"b:{st[k][1].key}|{st[k + 1][1].key}" for k in range(len(st) - 1)]


def decl_frames(toks: Sequence[Tok]) -> List[str]:
    """One frame part per top-level declaration.

    A declaration starts at a DECL_KW token whose column is 0 (the corpus
    convention: top-level declarations are not indented) and runs to the next
    such token.  The frame records the keyword, whether the body opens with
    ``by`` (tactic proof) and the statement length bucket (log2 of structural
    tokens before the body ``:=``).
    """
    st = structural(toks)
    starts = [k for k, (_, t) in enumerate(st)
              if t.kind == "kw" and t.text in DECL_KW and t.col == 0]
    frames: List[str] = []
    for idx, k in enumerate(starts):
        end = starts[idx + 1] if idx + 1 < len(starts) else len(st)
        body = None
        for j in range(k + 1, end):
            if st[j][1].kind == "sym" and st[j][1].text == ":=":
                nxt = st[j + 1][1] if j + 1 < end else None
                body = "by" if (nxt is not None and nxt.kind == "kw"
                                and nxt.text == "by") else "term"
                break
        stmt_len = 0
        for j in range(k + 1, end):
            if st[j][1].kind == "sym" and st[j][1].text == ":=":
                stmt_len = j - k - 1
                break
        bucket = min(int(stmt_len).bit_length(), 8) if stmt_len else 0
        frames.append(f"f:{st[k][1].text}|body={body}|len2={bucket}")
    return frames


def tactic_heads(toks: Sequence[Tok]) -> List[str]:
    """Tactic head names: a lexical reading of proof blocks.

    A proof block opens at a ``by`` token; its first tactic is the next
    structural token.  Every line inside the block whose first structural
    token is more indented than the declaration line (or than ``by`` itself
    when ``by`` ends the line), and every token after a ``<;>`` or ``;``,
    contributes its head (kind ident/kw) as a tactic invocation.
    """
    st = structural(toks)
    out: List[str] = []
    k = 0
    while k < len(st):
        i, t = st[k]
        if t.kind == "kw" and t.text == "by":
            base_col = t.col
            # first tactic right after by
            if k + 1 < len(st):
                out.append(f"t:{st[k + 1][1].text}")
            # scan forward: tactics are heads of lines indented past base
            j = k + 1
            while j < len(st):
                ti, tt = st[j]
                # stop at the next top-level declaration
                if tt.kind == "kw" and tt.text in DECL_KW and tt.col == 0:
                    break
                # line-head tactic: previous structural token is on an earlier
                # line and this token is indented > base
                prev = st[j - 1]
                if prev[1].line < tt.line and tt.col > base_col and \
                        tt.kind in ("ident", "kw") and not tt.text.isdigit():
                    out.append(f"t:{tt.text}")
                # after a combinator
                if tt.kind == "sym" and tt.text in ("<;>", ";") and j + 1 < len(st):
                    out.append(f"t:{st[j + 1][1].text}")
                j += 1
            k = j
        else:
            k += 1
    return out


# --------------------------------------------------------------------------
# corpus
# --------------------------------------------------------------------------

@dataclass
class FileRecord:
    path: Path
    rel: str
    module: str          # ground-truth label for clustering
    toks: List[Tok]

    @property
    def token_keys(self) -> List[str]:
        return [t.key for t in self.toks]


def module_of(rel: str) -> str:
    """Ground-truth label: the GLM subproject directory (or top dir)."""
    parts = rel.split("/")
    if len(parts) >= 4 and parts[0] == "RequestProject" and parts[1] == "GLM":
        return parts[2] if len(parts) > 3 else "GLM-root"
    return parts[0] if parts else "?"


def load_corpus(root: Path) -> List[FileRecord]:
    recs = []
    for f in sorted(root.rglob("*.lean")):
        text = f.read_text(encoding="utf-8", errors="replace")
        rel = str(f.relative_to(root))
        recs.append(FileRecord(f, rel, module_of(rel), tokenize(text)))
    return recs


ROLE_CHANNELS = ["import", "doc", "decl_head", "binder", "statement",
                 "tactic", "term", "other"]
N_ROLE = len(ROLE_CHANNELS)


TOPLEVEL_OTHER = frozenset(("variable", "open", "set_option", "namespace",
                            "end", "section", "universe", "private",
                            "protected", "public", "noncomputable",
                            "export", "local", "attribute", "macro",
                            "syntax", "elab", "in", "mutual"))


def role_stream(toks: Sequence[Tok]) -> List[str]:
    """Role channel of every token (the first 8 context channels).

    A lexical mode machine over the token stream:
      * comment tokens are ``doc``; whitespace tokens carry the current mode;
      * ``import`` on an import line;
      * a top-level declaration keyword (column 0) opens ``decl_head``; inside
        ``(...)`` there the role is ``binder``; its ``:`` at depth 0 switches
        to ``statement``; its ``:=`` opens the body;
      * a body opened by ``:= by`` is ``tactic`` until the next top-level
        declaration; a body opened by ``:=`` without ``by`` is ``term``;
      * other top-level keywords (``variable``, ``open``, ...) return to
        ``other``.
    This is a lexical reading, not the elaborator's parse; the report states
    the approximation.
    """
    roles: List[str] = []
    mode = "other"
    depth = 0
    for t in toks:
        if t.kind == "comment":
            roles.append("doc")
            continue
        if t.kind == "ws":
            roles.append("term" if mode == "pending_body" else mode)
            continue
        # structural token
        if t.kind == "kw" and t.col == 0:
            if t.text in DECL_KW:
                mode, depth = "decl_head", 0
            elif t.text == "import":
                mode = "import"
            elif t.text in TOPLEVEL_OTHER:
                mode = "other"
            roles.append("decl_head" if t.text in DECL_KW else mode)
            continue
        if mode in ("decl_head", "statement"):
            if t.kind == "sym" and t.text == "(":
                depth += 1
            elif t.kind == "sym" and t.text == ")":
                depth = max(0, depth - 1)
            elif t.kind == "sym" and t.text == ":=":
                roles.append("statement")
                mode = "pending_body"
                continue
            elif t.kind == "sym" and t.text == ":" and depth == 0:
                mode = "statement"
        elif mode == "pending_body":
            mode = "tactic" if (t.kind == "kw" and t.text == "by") else "term"
        if mode == "decl_head":
            roles.append("binder" if depth > 0 else "decl_head")
        elif mode == "statement":
            roles.append("binder" if depth > 0 else "statement")
        else:
            roles.append(mode)
    return roles
