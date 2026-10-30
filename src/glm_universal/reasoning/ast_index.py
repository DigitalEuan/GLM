"""``glm_universal.reasoning.ast_index`` -- the AST address as a retrieval key.

Phase 105 (``studies/AST_INDEX_STUDY.md``)
------------------------------------------
Round 9's item I3: index the structural address of a Python expression
beside the Lean corpus addresses, so that the GLM finds the places -- in its
own code and in the owner's archived scripts -- where a structurally equal
expression is already computed.

*Structurally equal* means: equal under a one-to-one renaming of variables
and a choice of operand order at each ``+ * & | ^`` and each single ``==`` /
``!=``, and nothing else.  Function and attribute names are fixed; a
method's receiver is a variable; keyword arguments are part of the
expression; constants compare by type and exact value.

Two keys are read:

* ``ast_v2`` (the subject) -- :func:`bucket_key`, the form with every
  variable erased and every commutative node's operands sorted by their
  erased form, which no renaming and no commutation can move
  (``GLM.AstIndex.bucket_complete``); inside a bucket, :func:`match`
  decides structural equality exactly and returns the witnessing renaming;
* ``ast_v1`` -- the Phase 64 canonical form
  (:func:`~glm_universal.reasoning.python_substrate.canonical_form`) as it
  is, which the study measures and does not repair.

:data:`REFERENCE_SOURCE` is a second decision procedure written separately
(enumerate operand orders, then one pass that builds the renaming); it is
executed here for mark A2 and carried verbatim by every column-3 script.

Everything reads the snapshot ``_data/ast_index_frozen.json``; integers and
:class:`~fractions.Fraction` only (D7).  The Lean half is
``RequestProject/GLM/AstIndex.lean``.
"""

from __future__ import annotations

import ast
import json
import re
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Sequence, Tuple

from .. import integrity

__all__ = [
    "STUDY", "LEAN_FILE", "FROZEN_PATH", "DATA_PATH", "IndexRefusal",
    "COMMUTATIVE", "ARITHMETIC", "MIN_NODES", "MAX_NODES",
    "parse_expression", "form_of", "node_count", "admit", "admitted_form",
    "sites_of_source", "write_snapshot", "frozen", "frozen_state", "sites",
    "erase", "bucket_key", "match", "structurally_equal", "tokens",
    "token_overlap", "REFERENCE_SOURCE", "reference_equal", "Index",
    "the_index", "rename_text", "commute_text", "perturb",
]

STUDY = "studies/AST_INDEX_STUDY.md"
LEAN_FILE = "RequestProject/GLM/AstIndex.lean"

_DATA = Path(__file__).resolve().parent / "_data"
FROZEN_PATH = _DATA / "ast_index_frozen.json"
DATA_PATH = _DATA / "ast_index.json"

MIN_NODES = 3
MAX_NODES = 64

#: The heads whose two operands commute under structural equality.
COMMUTATIVE = frozenset({"Add", "Mult", "BitAnd", "BitOr", "BitXor",
                         "Eq", "NotEq"})

#: The heads that count as computing something.
ARITHMETIC = frozenset({"Add", "Sub", "Mult", "Div", "FloorDiv", "Mod",
                        "Pow", "LShift", "RShift", "BitAnd", "BitOr",
                        "BitXor", "MatMult", "USub", "Invert"})


class IndexRefusal(ValueError):
    """An expression the index does not hold, with the reason by name."""

    def __init__(self, code: str, why: str):
        super().__init__(f"{code}: {why}")
        self.code = code
        self.why = why


# ===========================================================================
#  1.  The form
# ===========================================================================

def parse_expression(text: str) -> ast.expr:
    """One Python expression, or ``NOT_AN_EXPRESSION``."""
    try:
        return ast.parse(text.strip(), mode="eval").body
    except (SyntaxError, ValueError) as e:
        raise IndexRefusal("NOT_AN_EXPRESSION",
                           f"`{text.strip()}` does not parse as one Python "
                           f"expression ({type(e).__name__})") from None


def _const(v) -> Tuple[str, str, str]:
    return ("Const", type(v).__name__, repr(v))


def form_of(node: ast.AST):
    """The structural form of an admitted expression, as nested tuples.

    Raises ``OUTSIDE_INDEX`` on any node the index does not represent.
    """
    if isinstance(node, ast.Name):
        return ("Name", node.id)
    if isinstance(node, ast.Constant):
        v = node.value
        if isinstance(v, (bool, int, float, complex, str, bytes)) or v is None:
            return _const(v)
        raise IndexRefusal("OUTSIDE_INDEX", "a constant of an unindexed type")
    if isinstance(node, ast.BinOp):
        return (type(node.op).__name__, form_of(node.left),
                form_of(node.right))
    if isinstance(node, ast.UnaryOp):
        return (type(node.op).__name__, form_of(node.operand))
    if isinstance(node, ast.BoolOp):
        return (type(node.op).__name__,
                *[form_of(v) for v in node.values])
    if isinstance(node, ast.Compare):
        if len(node.ops) == 1:
            return (type(node.ops[0]).__name__, form_of(node.left),
                    form_of(node.comparators[0]))
        return ("Compare", form_of(node.left),
                *[(type(op).__name__, form_of(c))
                  for op, c in zip(node.ops, node.comparators)])
    if isinstance(node, ast.Call):
        if any(isinstance(a, ast.Starred) for a in node.args) or \
                any(k.arg is None for k in node.keywords):
            raise IndexRefusal("OUTSIDE_INDEX", "a starred argument")
        args = tuple(form_of(a) for a in node.args)
        kws = tuple(("Kw", k.arg, form_of(k.value))
                    for k in sorted(node.keywords, key=lambda k: k.arg))
        if isinstance(node.func, ast.Name):
            return ("Call", ("Func", node.func.id), *args, *kws)
        return ("CallOf", form_of(node.func), *args, *kws)
    if isinstance(node, ast.Attribute):
        return ("Attr", node.attr, form_of(node.value))
    if isinstance(node, ast.Subscript):
        return ("Index", form_of(node.value), form_of(node.slice))
    if isinstance(node, ast.Slice):
        return ("Slice", *[("Empty",) if p is None else form_of(p)
                           for p in (node.lower, node.upper, node.step)])
    if isinstance(node, ast.Tuple):
        return ("Tuple", *[form_of(e) for e in node.elts])
    if isinstance(node, ast.IfExp):
        return ("IfExp", form_of(node.test), form_of(node.body),
                form_of(node.orelse))
    raise IndexRefusal("OUTSIDE_INDEX",
                       f"a {type(node).__name__} node, which the index "
                       "does not hold")


def _is_form(x) -> bool:
    return isinstance(x, tuple) and bool(x) and isinstance(x[0], str)


def _heads(form, acc: List[str]) -> List[str]:
    if _is_form(form):
        acc.append(form[0])
        for x in form[1:]:
            _heads(x, acc)
    return acc


def node_count(form) -> int:
    """The expression nodes of a form (an argument keyword, a function
    name, an operator inside a chained comparison and an empty slice part
    are not nodes)."""
    return sum(1 for h in _heads(form, [])
               if h not in ("Kw", "Func", "Empty"))


def admit(form) -> None:
    """Raise ``NO_ARITHMETIC``, ``TOO_SMALL`` or ``TOO_LARGE`` unless the
    form is one the index holds."""
    heads = set(_heads(form, []))
    if not heads & ARITHMETIC:
        raise IndexRefusal("NO_ARITHMETIC",
                           "the expression computes nothing (no arithmetic "
                           "operator); the index holds only expressions "
                           "that do")
    n = node_count(form)
    if n < MIN_NODES:
        raise IndexRefusal("TOO_SMALL", f"{n} nodes; the index holds "
                           f"{MIN_NODES} to {MAX_NODES}")
    if n > MAX_NODES:
        raise IndexRefusal("TOO_LARGE", f"{n} nodes; the index holds "
                           f"{MIN_NODES} to {MAX_NODES}")


def admitted_form(text: str):
    """The form of ``text`` if the index would hold it; else a refusal."""
    form = form_of(parse_expression(text))
    admit(form)
    return form


def sites_of_source(source: str) -> Optional[List[Tuple[int, int, str]]]:
    """Every admitted statement-level expression of one Python file, as
    ``(line, column, text)``; ``None`` when the file does not parse."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return None
    out = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign,
                             ast.Return)) and node.value is not None:
            value = node.value
            try:
                text = ast.unparse(value)
                admitted_form(text)
            except (IndexRefusal, RecursionError, ValueError):
                continue
            out.append((value.lineno, value.col_offset, text))
    out.sort()
    return out


# ===========================================================================
#  2.  The snapshot
# ===========================================================================

def _canonical(rows) -> str:
    return json.dumps(list(rows), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def write_snapshot(rows: Sequence[Sequence[object]],
                   files: Dict[str, Dict[str, int]],
                   path: Optional[Path] = None) -> Path:
    """Store the snapshot: ``rows`` are ``[corpus, file, line, col, text]``
    in the stored order; ``files`` counts the files read and skipped."""
    rows = [list(r) for r in rows]
    payload = {"schema": 1, "study": STUDY, "files": files, "sites": rows,
               "digest": integrity.sha256_hex(
                   _canonical(rows).encode("utf-8"))}
    target = Path(path) if path is not None else FROZEN_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=0, ensure_ascii=False)
                      + "\n", encoding="utf-8")
    _cache.clear()
    return target


_cache: Dict[str, object] = {}


def frozen() -> Dict[str, object]:
    """The snapshot, its digest verified.  Raises if absent or altered."""
    if "data" in _cache:
        return _cache["data"]
    if not FROZEN_PATH.exists():
        raise FileNotFoundError(f"no snapshot at {FROZEN_PATH}; run "
                                "`tools ast-index --freeze`")
    data = json.loads(FROZEN_PATH.read_text(encoding="utf-8"))
    digest = integrity.sha256_hex(_canonical(data["sites"]).encode("utf-8"))
    if digest != data["digest"]:
        raise ValueError("the AST index snapshot does not match its digest")
    _cache["data"] = data
    return data


def frozen_state() -> Dict[str, object]:
    if not FROZEN_PATH.exists():
        return {"present": False, "intact": False}
    try:
        data = frozen()
    except ValueError:
        return {"present": True, "intact": False}
    per = {}
    for row in data["sites"]:
        per[row[0]] = per.get(row[0], 0) + 1
    return {"present": True, "intact": True, "digest": data["digest"],
            "sites": len(data["sites"]), "per_corpus": per,
            "files": data["files"]}


def sites() -> List[List[object]]:
    return frozen()["sites"]


# ===========================================================================
#  3.  The bucket key and the matcher
# ===========================================================================

@lru_cache(maxsize=None)
def erase(form):
    """The form with every variable erased and every commutative node's
    two operands sorted by their erased form."""
    if not _is_form(form):
        return form
    if form[0] == "Name":
        return ("Name",)
    kids = tuple(erase(x) for x in form[1:])
    if form[0] in COMMUTATIVE and len(kids) == 2:
        kids = tuple(sorted(kids, key=repr))
    return (form[0], *kids)


def bucket_key(form) -> str:
    """``ast_v2``'s key: no renaming and no commutation moves it."""
    return repr(erase(form))


def _m(a, b, fw: Dict[str, str], bw: Dict[str, str]
       ) -> Iterator[Tuple[Dict[str, str], Dict[str, str]]]:
    if not _is_form(a) or not _is_form(b):
        if a == b:
            yield fw, bw
        return
    if a[0] != b[0] or len(a) != len(b):
        return
    if a[0] == "Name":
        x, y = a[1], b[1]
        if fw.get(x, y) != y or bw.get(y, x) != x:
            return
        if x in fw:
            yield fw, bw
            return
        nf = dict(fw)
        nf[x] = y
        nb = dict(bw)
        nb[y] = x
        yield nf, nb
        return
    if a[0] in COMMUTATIVE and len(a) == 3:
        orders = [(b[1], b[2])]
        if b[1] != b[2]:
            orders.append((b[2], b[1]))
        for p, q in orders:
            if erase(a[1]) != erase(p) or erase(a[2]) != erase(q):
                continue
            yield from _seq((a[1], a[2]), (p, q), fw, bw)
        return
    yield from _seq(a[1:], b[1:], fw, bw)


def _seq(xs, ys, fw, bw):
    if not xs:
        yield fw, bw
        return
    for f2, b2 in _m(xs[0], ys[0], fw, bw):
        yield from _seq(xs[1:], ys[1:], f2, b2)


def match(a, b) -> Optional[Dict[str, str]]:
    """The renaming of ``a``'s variables onto ``b``'s under which the two
    forms are equal up to operand order at commutative nodes, or ``None``."""
    if erase(a) != erase(b):
        return None
    for fw, _ in _m(a, b, {}, {}):
        return fw
    return None


def structurally_equal(text_a: str, text_b: str) -> bool:
    return match(form_of(parse_expression(text_a)),
                 form_of(parse_expression(text_b))) is not None


# ===========================================================================
#  4.  The brute-force reference (carried by every column-3 script)
# ===========================================================================

REFERENCE_SOURCE = r'''
import ast

COMM = {"Add", "Mult", "BitAnd", "BitOr", "BitXor", "Eq", "NotEq"}
LIMIT = 1 << 16


def shape(n):
    """The form of an expression, built from the parse."""
    t = type(n).__name__
    if t == "Name":
        return ("Name", n.id)
    if t == "Constant":
        return ("Const", type(n.value).__name__, repr(n.value))
    if t == "BinOp":
        return (type(n.op).__name__, shape(n.left), shape(n.right))
    if t == "UnaryOp":
        return (type(n.op).__name__, shape(n.operand))
    if t == "BoolOp":
        return (type(n.op).__name__,) + tuple(shape(v) for v in n.values)
    if t == "Compare":
        if len(n.ops) == 1:
            return (type(n.ops[0]).__name__, shape(n.left),
                    shape(n.comparators[0]))
        return ("Compare", shape(n.left)) + tuple(
            (type(o).__name__, shape(c)) for o, c in zip(n.ops, n.comparators))
    if t == "Call":
        kw = tuple(("Kw", k.arg, shape(k.value))
                   for k in sorted(n.keywords, key=lambda k: k.arg))
        args = tuple(shape(a) for a in n.args)
        if type(n.func).__name__ == "Name":
            return ("Call", ("Func", n.func.id)) + args + kw
        return ("CallOf", shape(n.func)) + args + kw
    if t == "Attribute":
        return ("Attr", n.attr, shape(n.value))
    if t == "Subscript":
        return ("Index", shape(n.value), shape(n.slice))
    if t == "Slice":
        return ("Slice",) + tuple(("Empty",) if p is None else shape(p)
                                  for p in (n.lower, n.upper, n.step))
    if t == "Tuple":
        return ("Tuple",) + tuple(shape(e) for e in n.elts)
    if t == "IfExp":
        return ("IfExp", shape(n.test), shape(n.body), shape(n.orelse))
    raise ValueError("unindexed node " + t)


def isnode(x):
    return isinstance(x, tuple) and len(x) > 0 and isinstance(x[0], str)


def blank(f):
    """Variables erased, commutative operands sorted: the bucket key."""
    if not isnode(f):
        return f
    if f[0] == "Name":
        return ("Name",)
    kids = [blank(x) for x in f[1:]]
    if f[0] in COMM and len(kids) == 2:
        kids.sort(key=repr)
    return (f[0],) + tuple(kids)


def orders(f, g):
    """Every operand order of ``g`` whose blanked shape lines up with
    ``f``'s at each node (an order that does not line up cannot match)."""
    if (not isnode(g) or not isnode(f) or len(f) != len(g) or f[0] != g[0]
            or g[0] == "Name"):
        yield g
        return
    choices = [g[1:]]
    if g[0] in COMM and len(g) == 3 and g[1] != g[2]:
        choices.append((g[2], g[1]))
    for kids in choices:
        if any(blank(x) != blank(y) for x, y in zip(f[1:], kids)):
            continue
        def walk(i):
            if i == len(kids):
                yield ()
                return
            for head in orders(f[1 + i], kids[i]):
                for rest in walk(i + 1):
                    yield (head,) + rest
        for combo in walk(0):
            yield (g[0],) + combo


def one_pass(f, g):
    """The renaming built by walking ``f`` and ``g`` together, or None."""
    fw, bw = {}, {}
    stack = [(f, g)]
    while stack:
        x, y = stack.pop()
        if isnode(x) and isnode(y):
            if x[0] != y[0] or len(x) != len(y):
                return None
            if x[0] == "Name":
                if fw.setdefault(x[1], y[1]) != y[1]:
                    return None
                if bw.setdefault(y[1], x[1]) != x[1]:
                    return None
                continue
            stack.extend(zip(x[1:], y[1:]))
        elif x != y:
            return None
    return fw


def decide(a_text, b_text):
    """True / False, or None past LIMIT operand orders."""
    f = shape(ast.parse(a_text, mode="eval").body)
    g = shape(ast.parse(b_text, mode="eval").body)
    if blank(f) != blank(g):
        return False
    count = 0
    for h in orders(f, g):
        count += 1
        if count > LIMIT:
            return None
        if one_pass(f, h) is not None:
            return True
    return False
'''

_REF: Dict[str, object] = {}


def _reference() -> Dict[str, object]:
    if not _REF:
        exec(compile(REFERENCE_SOURCE, "<ast_index reference>", "exec"),
             _REF)
    return _REF


def reference_equal(text_a: str, text_b: str) -> Optional[bool]:
    """The brute-force reference's verdict (``None`` past its limit)."""
    return _reference()["decide"](text_a, text_b)


def reference_key(text: str) -> str:
    ref = _reference()
    return repr(ref["blank"](ref["shape"](ast.parse(text, mode="eval")
                                          .body)))


# ===========================================================================
#  5.  Tokens (the standard)
# ===========================================================================

_TOKEN = re.compile(r"[A-Za-z_]\w*|\d+(?:\.\d*)?(?:[eE][-+]?\d+)?|"
                    r"\*\*|//|<<|>>|==|!=|<=|>=|[-+*/%&|^~<>@]")


def tokens(text: str) -> frozenset:
    """Identifiers, numbers and operators -- no structure."""
    return frozenset(_TOKEN.findall(text))


def token_overlap(a: frozenset, b: frozenset) -> Fraction:
    union = len(a | b)
    return Fraction(len(a & b), union) if union else Fraction(0)


# ===========================================================================
#  6.  The index
# ===========================================================================

class Index:
    """The snapshot read into buckets: ``bucket_key -> [site number]``."""

    def __init__(self, rows: Sequence[Sequence[object]]):
        self.rows = rows
        self.forms = []
        self.buckets: Dict[str, List[int]] = {}
        for i, row in enumerate(rows):
            form = form_of(parse_expression(row[4]))
            self.forms.append(form)
            self.buckets.setdefault(bucket_key(form), []).append(i)

    def lookup(self, text: str, corpus: str = "all"
               ) -> Tuple[object, List[int], List[Tuple[int, Dict[str, str]]]]:
        """``(form, bucket, matches)`` for a query; ``matches`` pairs each
        structurally equal site with the renaming of the query onto it."""
        form = admitted_form(text)
        bucket = [i for i in self.buckets.get(bucket_key(form), [])
                  if corpus == "all" or self.rows[i][0] == corpus]
        found = []
        for i in bucket:
            sigma = match(form, self.forms[i])
            if sigma is not None:
                found.append((i, sigma))
        return form, bucket, found


def the_index() -> Index:
    if "index" not in _cache:
        _cache["index"] = Index(sites())
    return _cache["index"]


# ===========================================================================
#  7.  Perturbations (the study's §2)
# ===========================================================================

class _Renamer(ast.NodeTransformer):
    """Variables only: a called name is a function name, which §1 fixes."""

    def __init__(self):
        self.table: Dict[str, str] = {}

    def visit_Call(self, node):
        if not isinstance(node.func, ast.Name):
            node.func = self.visit(node.func)
        node.args = [self.visit(a) for a in node.args]
        for k in node.keywords:
            k.value = self.visit(k.value)
        return node

    def visit_Name(self, node):
        if node.id not in self.table:
            self.table[node.id] = f"zq{len(self.table)}_"
        return ast.copy_location(ast.Name(self.table[node.id], node.ctx),
                                 node)


_COMM_OPS = (ast.Add, ast.Mult, ast.BitAnd, ast.BitOr, ast.BitXor)


class _Commuter(ast.NodeTransformer):
    def visit_BinOp(self, node):
        self.generic_visit(node)
        if isinstance(node.op, _COMM_OPS):
            node.left, node.right = node.right, node.left
        return node

    def visit_Compare(self, node):
        self.generic_visit(node)
        if len(node.ops) == 1 and isinstance(node.ops[0], (ast.Eq, ast.NotEq)):
            node.left, node.comparators = node.comparators[0], [node.left]
        return node


def rename_text(text: str) -> str:
    """Every variable renamed to a fresh name, one to one."""
    tree = ast.parse(text, mode="eval")
    return ast.unparse(_Renamer().visit(tree))


def commute_text(text: str) -> str:
    """The operands of every commutative node swapped."""
    tree = ast.parse(text, mode="eval")
    return ast.unparse(_Commuter().visit(tree))


def perturb(text: str, kind: str) -> str:
    if kind == "rename":
        return rename_text(text)
    if kind == "commute":
        return commute_text(text)
    if kind == "both":
        return commute_text(rename_text(text))
    raise ValueError(kind)


# ===========================================================================
#  8.  The measurement (the study's §2)
# ===========================================================================

def structural_classes(index: Index, audit: Optional[Dict[str, int]] = None
                       ) -> List[int]:
    """The structural class of every site: inside each bucket, a site joins
    the first class whose representative it matches.  ``audit`` (when given)
    counts each matcher call checked against the reference (mark A2)."""
    cls = [-1] * len(index.rows)
    reps: List[int] = []
    for key in sorted(index.buckets):
        local: List[int] = []
        for i in index.buckets[key]:
            for r in local:
                verdict = match(index.forms[r], index.forms[i]) is not None
                if audit is not None:
                    _audit(audit, index.rows[r][4], index.rows[i][4], verdict)
                if verdict:
                    cls[i] = cls[r]
                    break
            else:
                cls[i] = len(reps)
                reps.append(i)
                local.append(i)
    return cls


def _audit(audit: Dict[str, int], a: str, b: str, verdict: bool) -> None:
    ref = reference_equal(a, b)
    audit["asked"] = audit.get("asked", 0) + 1
    if ref is None:
        audit["undecided"] = audit.get("undecided", 0) + 1
    elif ref != verdict:
        audit["disagreements"] = audit.get("disagreements", 0) + 1
        audit.setdefault("examples", []).append([a, b, verdict])


def _v1(text: str) -> str:
    from . import python_substrate as ps
    return repr(ps.canonical_form(text))


def _best(cands: Sequence[int], qtok: frozenset,
          toks: Sequence[frozenset]) -> Optional[int]:
    """The candidate with the largest token overlap, the earliest on a tie
    (compared exactly, by cross-multiplication)."""
    best, bn, bd = None, -1, 1
    for i in cands:
        t = toks[i]
        n = len(qtok & t)
        d = len(qtok | t) or 1
        if n * bd > bn * d:
            best, bn, bd = i, n, d
    return best


def _carrier_ints(text: str) -> Tuple[int, ...]:
    from . import python_substrate as ps
    scale = 1 << (20 + 5 * (MAX_NODES + 2))
    return tuple(int(c * scale) for c in ps.ast_address(text)["carrier"])


def measure(stride: int = 25, kinds: Sequence[str] = ("rename", "commute",
                                                       "both")
            ) -> Dict[str, object]:
    """Every figure of the study's §3, from the snapshot alone."""
    from .sign_test import sign_test
    index = the_index()
    rows = index.rows
    n = len(rows)
    audit: Dict[str, int] = {"asked": 0, "undecided": 0, "disagreements": 0}
    cls = structural_classes(index, audit)
    toks = [tokens(r[4]) for r in rows]
    v1 = [_v1(r[4]) for r in rows]
    v1_classes: Dict[str, List[int]] = {}
    for i, k in enumerate(v1):
        v1_classes.setdefault(k, []).append(i)
    carriers = [_carrier_ints(r[4]) for r in rows]

    queries = list(range(0, n, stride))
    invariance = {k: {"bucket": 0, "match": 0, "v1": 0} for k in kinds}
    failures_v1: Dict[str, List[str]] = {k: [] for k in kinds}
    hits = {name: {"1": 0, "5": 0} for name in ("ast_v2", "ast_v1",
                                                "carrier", "text")}
    per_query: Dict[str, List[int]] = {name: [] for name in hits}
    everyone = list(range(n))
    for q in queries:
        text = rows[q][4]
        form = index.forms[q]
        for kind in kinds:
            ptext = perturb(text, kind)
            pform = form_of(parse_expression(ptext))
            ok_b = bucket_key(pform) == bucket_key(form)
            verdict = match(pform, form) is not None
            _audit(audit, ptext, text, verdict)
            invariance[kind]["bucket"] += ok_b
            invariance[kind]["match"] += verdict
            same_v1 = _v1(ptext) == v1[q]
            invariance[kind]["v1"] += same_v1
            if not same_v1 and len(failures_v1[kind]) < 12:
                failures_v1[kind].append(text)
            if kind != "both":
                continue
            qtok = tokens(ptext)
            # ast_v2: the structural class of the perturbed query, by bucket
            bucket = index.buckets.get(bucket_key(pform), [])
            members = []
            for i in bucket:
                v = match(pform, index.forms[i]) is not None
                if v:
                    members.append(i)
            ranked = {}
            ranked["ast_v2"] = _ranked(members, qtok, toks, everyone)
            pv1 = _v1(ptext)
            ranked["ast_v1"] = _ranked(v1_classes.get(pv1, []), qtok, toks,
                                       everyone)
            ranked["text"] = _ranked([], qtok, toks, everyone)
            pc = _carrier_ints(ptext)
            dist = [sum(abs(a - b) for a, b in zip(pc, c)) for c in carriers]
            ranked["carrier"] = sorted(everyone, key=lambda i: (dist[i],
                                                                -0, i))[:5]
            for name, top in ranked.items():
                h1 = bool(top) and cls[top[0]] == cls[q]
                h5 = any(cls[i] == cls[q] for i in top[:5])
                hits[name]["1"] += h1
                hits[name]["5"] += h5
                per_query[name].append(int(h1))

    def disc(a: str, b: str) -> Dict[str, object]:
        x = sum(1 for u, v in zip(per_query[a], per_query[b]) if u and not v)
        y = sum(1 for u, v in zip(per_query[a], per_query[b]) if v and not u)
        return {"for": x, "against": y, "sign_test": sign_test(x, y)}

    # the Phase 64 address's false merges
    merges = 0
    merged_sites = 0
    merge_examples = []
    for members in v1_classes.values():
        kinds_in = {cls[i] for i in members}
        if len(kinds_in) > 1:
            merges += 1
            merged_sites += len(members)
            if len(merge_examples) < 8:
                firsts = []
                for c in sorted(kinds_in)[:2]:
                    firsts.append(next(rows[i][4] for i in members
                                       if cls[i] == c))
                merge_examples.append(firsts)

    # cross-corpus classes
    by_class: Dict[int, List[int]] = {}
    for i, c in enumerate(cls):
        by_class.setdefault(c, []).append(i)
    shared = [c for c, ms in by_class.items()
              if {rows[i][0] for i in ms} == {"live", "archive"}]
    shared_examples = sorted(
        ((len(by_class[c]), rows[by_class[c][0]][4]) for c in shared),
        key=lambda t: (-t[0], t[1]))[:10]

    return {
        "snapshot_digest": frozen()["digest"],
        "sites": n,
        "per_corpus": frozen_state()["per_corpus"],
        "buckets": len(index.buckets),
        "classes": len(by_class),
        "classes_multi": sum(1 for ms in by_class.values() if len(ms) > 1),
        "queries": len(queries),
        "stride": stride,
        "audit": audit,
        "invariance": invariance,
        "v1_failures": failures_v1,
        "hits": hits,
        "discordance": {"ast_v2_vs_text": disc("ast_v2", "text"),
                        "ast_v1_vs_text": disc("ast_v1", "text"),
                        "ast_v2_vs_ast_v1": disc("ast_v2", "ast_v1"),
                        "ast_v2_vs_carrier": disc("ast_v2", "carrier")},
        "v1_classes": len(v1_classes),
        "v1_false_merges": merges,
        "v1_merged_sites": merged_sites,
        "v1_merge_examples": merge_examples,
        "shared_classes": len(shared),
        "shared_examples": [list(t) for t in shared_examples],
        "soundness": soundness(index, cls),
    }


def _ranked(head: Sequence[int], qtok: frozenset,
            toks: Sequence[frozenset], everyone: Sequence[int]) -> List[int]:
    """The top five: the key's members by token overlap, then everyone
    else by token overlap (exact, earliest on a tie)."""
    def order(cands):
        return sorted(cands, key=lambda i: (-Fraction(len(qtok & toks[i]),
                                                      len(qtok | toks[i])
                                                      or 1), i))
    top = order(head)[:5]
    if len(top) < 5:
        chosen = set(top)
        rest = [i for i in everyone if i not in chosen]
        best = []
        for _ in range(5 - len(top)):
            b = _best(rest, qtok, toks)
            if b is None:
                break
            best.append(b)
            rest = [i for i in rest if i != b]
        top += best
    return top


# ---------------------------------------------------------------------------
#  Soundness on integer arithmetic (mark A6)
# ---------------------------------------------------------------------------

_INT_HEADS = frozenset({"Name", "Const", "Add", "Sub", "Mult", "FloorDiv",
                        "Mod", "Pow", "USub", "BitAnd", "BitOr", "BitXor",
                        "Invert", "LShift", "RShift"})

#: Five declared integer environments: variable ``j`` (in sorted order of
#: the representative's names) takes ``ENV_VALUES[k][j % 7]``.
ENV_VALUES: Tuple[Tuple[int, ...], ...] = (
    (3, 5, 7, 11, 13, 17, 19),
    (-2, 9, 4, -7, 6, 1, -5),
    (10, -3, 8, 2, -9, 12, 7),
    (1, 2, 3, 4, 5, 6, 7),
    (-11, 4, -6, 15, 3, -8, 2),
)


def _int_arith(form) -> bool:
    if not _is_form(form):
        return True
    h = form[0]
    if h not in _INT_HEADS:
        return False
    if h == "Const":
        return form[1] == "int"
    if h == "Pow":
        r = form[2]
        if not (_is_form(r) and r[0] == "Const" and r[1] == "int"
                and 0 <= int(r[2]) <= 8):
            return False
    if h in ("LShift", "RShift"):
        r = form[2]
        if not (_is_form(r) and r[0] == "Const" and r[1] == "int"
                and 0 <= int(r[2]) <= 16):
            return False
    if h == "Name":
        return True
    return all(_int_arith(x) for x in form[1:])


def _names(form, acc: List[str]) -> List[str]:
    if _is_form(form):
        if form[0] == "Name":
            if form[1] not in acc:
                acc.append(form[1])
        else:
            for x in form[1:]:
                _names(x, acc)
    return acc


def evaluate(form, env: Dict[str, int]) -> int:
    """An integer-arithmetic form's value (int only)."""
    h = form[0]
    if h == "Name":
        return env[form[1]]
    if h == "Const":
        return int(form[2])
    if h == "USub":
        return -evaluate(form[1], env)
    if h == "Invert":
        return ~evaluate(form[1], env)
    a = evaluate(form[1], env)
    b = evaluate(form[2], env)
    if h == "Add":
        return a + b
    if h == "Sub":
        return a - b
    if h == "Mult":
        return a * b
    if h == "FloorDiv":
        return a // b
    if h == "Mod":
        return a % b
    if h == "Pow":
        return a ** b
    if h == "BitAnd":
        return a & b
    if h == "BitOr":
        return a | b
    if h == "BitXor":
        return a ^ b
    if h == "LShift":
        return a << b
    if h == "RShift":
        return a >> b
    raise ValueError(h)


def _has_str_add(form) -> bool:
    if not _is_form(form):
        return False
    if form[0] == "Add" and any(_is_form(x) and x[0] == "Const" and
                                x[1] == "str" for x in form[1:]):
        return True
    return any(_has_str_add(x) for x in form[1:])


def soundness(index: Index, cls: Sequence[int]) -> Dict[str, object]:
    """Mark A6: every integer-arithmetic structural class with two
    spellings evaluates equally under the matcher's renaming."""
    by_class: Dict[int, List[int]] = {}
    for i, c in enumerate(cls):
        by_class.setdefault(c, []).append(i)
    classes = pairs = evaluations = skipped = failures = 0
    str_classes = 0
    examples = []
    for c, members in sorted(by_class.items()):
        texts = {}
        for i in members:
            texts.setdefault(index.rows[i][4], i)
        if len(texts) < 2:
            continue
        reps = list(texts.values())
        r = reps[0]
        if _has_str_add(index.forms[r]):
            str_classes += 1
        if not _int_arith(index.forms[r]):
            continue
        classes += 1
        names = sorted(_names(index.forms[r], []))
        for m in reps[1:]:
            pairs += 1
            sigma = match(index.forms[r], index.forms[m])
            if sigma is None:
                failures += 1
                continue
            for values in ENV_VALUES:
                env_r = {x: values[j % len(values)]
                         for j, x in enumerate(names)}
                env_m = {sigma[x]: v for x, v in env_r.items()}
                try:
                    a = evaluate(index.forms[r], env_r)
                    b = evaluate(index.forms[m], env_m)
                except ZeroDivisionError:
                    skipped += 1
                    continue
                evaluations += 1
                if a != b:
                    failures += 1
                    if len(examples) < 5:
                        examples.append([index.rows[r][4], index.rows[m][4]])
    return {"classes": classes, "pairs": pairs, "evaluations": evaluations,
            "skipped": skipped, "failures": failures, "examples": examples,
            "string_add_classes": str_classes}
