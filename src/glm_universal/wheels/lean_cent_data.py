"""``glm_universal.wheels.lean_cent_data`` -- what ``Wheels/CentWheels.lean``
states, read from its source text and checked against the Python.

*Created 31 October 2026 (intake of ``source_material/ToDo/cent_compiler_v12``,
directive D22; ``studies/CENT_WHEELS_STUDY.md``, mark L1).*

``Wheels/CentWheels.lean`` (namespace ``GLM.CentWheels``) proves, for every
wheel :mod:`glm_universal.wheels.cent_wheels` absorbs (and for the W4 / W6
additions and the W11-W15 supplied cases), three kinds of finite fact:

* ``axioms_balanced`` (or ``axiom_i_residual``) -- the dimension map of the
  wheel's table sends each axiom's relation vector to ``0`` (or to the stated
  residual);
* ``q_<id> : Derivable (Set.range ax) v`` with the certificate
  ``derivable_of_combo ax c _`` -- ``v`` is the rational combination ``c`` of
  the axioms;
* ``q_<id> : ¬ Derivable (Set.range ax) v`` with ``not_derivable_of_dot ax w _``
  -- the functional ``w`` vanishes on every axiom and not on ``v``;

and, in the section ``Supplied``, the exact SI7 residual of each supplied
axiom that fails on its own table.

This module reads those statements back out of the text (no Lean is run here;
the build is the owner's, ``scripts/rebuild_lean.sh``) and
:func:`agreement` re-checks every one of them against the Python in exact
arithmetic: the coordinates, the axiom vectors and the table rows are the
Python's; each certificate and each functional is re-verified on the numbers
the Lean file states; each verdict is the rational-power engine's.  A file
that is missing or does not parse gives empty results and ``ok = False`` (a
reader reports the absence, never a guess).  Exact throughout (directive D7):
``Fraction`` only.
"""
from __future__ import annotations

import re
from fractions import Fraction
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from ..constants import lean_file

__all__ = [
    "CENT_WHEELS_LEAN", "lean_text", "blocks", "parse_block", "parse_supplied",
    "theorem_names", "agreement",
]

#: The Lean file, as a name :func:`glm_universal.constants.lean_file` resolves.
CENT_WHEELS_LEAN = "Wheels/CentWheels.lean"

_NS = re.compile(r"^namespace (\w+)\n(.*?)^end \1$", re.MULTILINE | re.DOTALL)
_ROW = re.compile(r"!\[([^\[\]!]*)\]")
_COORDS = re.compile(r"\bdef (\w*?)_?coords : List String :=\s*\[([^\]]*)\]")
_MATRIX_DEF = re.compile(r"\bdef (\w+) : Fin (\d+) → Fin (\d+) → ℚ :=\s*(!\[.*?\]\])\n",
                         re.DOTALL)
_VECTOR_DEF = re.compile(r"\bdef (\w+) : Fin (\d+) → ℚ := !\[([^\]]*)\]")
_RESIDUAL = re.compile(r"\btheorem axiom_(\d+)_residual : dimL dim \(ax \d+\) = !\[([^\]]*)\]")
_QUESTION = re.compile(
    r"/-- `([^`]+)`: (.*?) -/\ntheorem (q_\w+) : (¬ )?Derivable \(Set\.range ax\) !\[([^\]]*)\] :=\n"
    r"  (derivable_of_combo|not_derivable_of_dot) ax !\[([^\]]*)\] _")
_WITHOUT = re.compile(
    r"\btheorem (q_\w+_without_addition) :\s*¬ Derivable \(Set\.range \(fun i : Fin (\d+) => "
    r"ax \(Fin\.castSucc i\)\)\) !\[([^\]]*)\] :=\n  not_derivable_of_dot _ !\[([^\]]*)\] _")
_SUPPLIED_DOC = re.compile(r"/-- (W\d+) axiom (\d+) as supplied: (.*?) -/")
_SUPPLIED_RES = re.compile(r"\btheorem (W\d+_axiom_\d+)_residual : dimL \w+ \w+ = !\[([^\]]*)\]")
_THEOREM = re.compile(r"^theorem ([\w']+)", re.MULTILINE)


def _q(text: str) -> Fraction:
    return Fraction(text.strip().replace(" ", ""))


def _vec(body: str) -> Tuple[Fraction, ...]:
    body = body.strip()
    return tuple(_q(t) for t in body.split(",")) if body else ()


def _matrix(text: str) -> Tuple[Tuple[Fraction, ...], ...]:
    return tuple(_vec(r) for r in _ROW.findall(text))


def _code_only(text: str) -> str:
    """The text with its comments and docstrings removed (they do not nest in
    this file) and its string literals emptied."""
    text = re.sub(r"/-.*?-/", " ", text, flags=re.DOTALL)
    text = re.sub(r"--[^\n]*", " ", text)
    return re.sub(r'"[^"\n]*"', '""', text)


def lean_text() -> str:
    """The source text of ``Wheels/CentWheels.lean``, ``""`` if absent."""
    path = lean_file(CENT_WHEELS_LEAN)
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def blocks(text: Optional[str] = None) -> Dict[str, str]:
    """``{namespace: body}`` of the inner namespaces (``W16`` ... ``Supplied``)."""
    text = lean_text() if text is None else text
    return {m.group(1): m.group(2) for m in _NS.finditer(text)}


def parse_block(body: str) -> Dict[str, object]:
    """One wheel's namespace: ``coords``, ``ax``, ``dim``, ``balanced``,
    ``residuals`` ``{i: vector}``, ``questions`` ``{qid: {...}}`` and the
    W6 ``without`` theorem when present."""
    out: Dict[str, object] = {"coords": (), "ax": (), "dim": (), "balanced": False,
                              "residuals": {}, "questions": {}, "without": None}
    m = _COORDS.search(body)
    if m:
        out["coords"] = tuple(re.findall(r'"([^"]*)"', m.group(2)))
    for m in _MATRIX_DEF.finditer(body):
        if m.group(1) in ("ax", "dim"):
            out[m.group(1)] = _matrix(m.group(4))
    out["balanced"] = "theorem axioms_balanced : ∀ i, dimL dim (ax i) = 0" in body
    out["residuals"] = {int(m.group(1)): _vec(m.group(2)) for m in _RESIDUAL.finditer(body)}
    qs: Dict[str, Dict[str, object]] = {}
    for m in _QUESTION.finditer(body):
        derivable = m.group(4) is None
        if derivable != (m.group(6) == "derivable_of_combo"):
            raise ValueError(f"{m.group(3)}: statement and certificate disagree")
        qs[m.group(1)] = {"equation": m.group(2), "name": m.group(3), "derivable": derivable,
                          "vector": _vec(m.group(5)), "certificate": _vec(m.group(7))}
    out["questions"] = qs
    m = _WITHOUT.search(body)
    if m:
        out["without"] = {"name": m.group(1), "k": int(m.group(2)), "vector": _vec(m.group(3)),
                          "functional": _vec(m.group(4))}
    return out


def parse_supplied(body: str) -> Dict[str, Dict[str, object]]:
    """``{"W22_axiom_2": {"wheel", "index", "text", "coords", "vector", "dim",
    "residual"}}`` for the section ``Supplied``."""
    out: Dict[str, Dict[str, object]] = {}
    for m in _SUPPLIED_DOC.finditer(body):
        out[f"{m.group(1)}_axiom_{m.group(2)}"] = {
            "wheel": m.group(1), "index": int(m.group(2)), "text": m.group(3)}
    for m in _COORDS.finditer(body):
        if m.group(1) in out:
            out[m.group(1)]["coords"] = tuple(re.findall(r'"([^"]*)"', m.group(2)))
    for m in _VECTOR_DEF.finditer(body):
        if m.group(1) in out:
            out[m.group(1)]["vector"] = _vec(m.group(3))
    for m in _MATRIX_DEF.finditer(body):
        name = m.group(1)
        if name.endswith("_dim") and name[:-4] in out:
            out[name[:-4]]["dim"] = _matrix(m.group(4))
    for m in _SUPPLIED_RES.finditer(body):
        if m.group(1) in out:
            out[m.group(1)]["residual"] = _vec(m.group(2))
    return out


def theorem_names(text: Optional[str] = None) -> List[str]:
    """Every ``theorem`` the file states, in order."""
    text = lean_text() if text is None else text
    return _THEOREM.findall(text)


# ---------------------------------------------------------------------------
# Agreement with the Python
# ---------------------------------------------------------------------------

def _dot(a: Sequence[Fraction], b: Sequence[Fraction]) -> Fraction:
    return sum((x * y for x, y in zip(a, b)), Fraction(0))


def _dim_image(dim: Sequence[Sequence[Fraction]], v: Sequence[Fraction]) -> Tuple[Fraction, ...]:
    return tuple(sum((v[j] * dim[j][a] for j in range(len(v))), Fraction(0)) for a in range(8))


def _check_wheel(ns: str, parsed: Mapping, axioms: Sequence[str],
                 table: Mapping[str, Sequence[Fraction]],
                 questions: Sequence[Tuple[str, str]],
                 expected: Mapping[str, bool], problems: List[str]) -> Dict[str, int]:
    """Check one namespace against the Python wheel; append every disagreement."""
    from . import cent_wheels as CW
    rels = [CW.relation_vector_q(a) for a in axioms]
    qrels = [CW.relation_vector_q(eq) for _, eq in questions]
    cols = tuple(CW.columns(*rels, *qrels))
    zero = (Fraction(0),) * 8
    counts = {"axioms": 0, "derivable": 0, "refused": 0}
    if tuple(parsed["coords"]) != cols:
        problems.append(f"{ns}: coordinates {parsed['coords']} != {cols}")
        return counts
    ax = parsed["ax"]
    if tuple(ax) != tuple(tuple(r.get(c, Fraction(0)) for c in cols) for r in rels):
        problems.append(f"{ns}: the axiom vectors differ from the Python")
        return counts
    dim = parsed["dim"]
    want_dim = tuple(tuple(table.get(c, zero)) if not c.startswith("#") else zero for c in cols)
    if tuple(dim) != want_dim:
        problems.append(f"{ns}: the dimension table differs from the Python")
        return counts
    counts["axioms"] = len(axioms)
    py_res = [CW.residual(a, table) for a in axioms]
    lean_res = [_dim_image(dim, row) for row in ax]
    for i, (p, l) in enumerate(zip(py_res, lean_res)):
        if p is None or tuple(p) != l:
            problems.append(f"{ns}: axiom {i} residual {l} != Python {p}")
    if all(not any(r) for r in lean_res):
        if not parsed["balanced"]:
            problems.append(f"{ns}: every axiom balances but axioms_balanced is not stated")
    else:
        if parsed["balanced"]:
            problems.append(f"{ns}: axioms_balanced is stated but an axiom has a residual")
        for i, r in enumerate(lean_res):
            if parsed["residuals"].get(i) != r:
                problems.append(f"{ns}: axiom_{i}_residual states {parsed['residuals'].get(i)}, "
                                f"the arithmetic gives {r}")
    lean_qs = parsed["questions"]
    if set(lean_qs) != {q for q, _ in questions}:
        problems.append(f"{ns}: questions {sorted(lean_qs)} != {sorted(q for q, _ in questions)}")
    for (qid, eq), rel in zip(questions, qrels):
        lq = lean_qs.get(qid)
        if lq is None:
            continue
        v = tuple(rel.get(c, Fraction(0)) for c in cols)
        if lq["equation"] != eq or tuple(lq["vector"]) != v:
            problems.append(f"{ns}: {qid} states another formula")
            continue
        verdict = CW.is_derivable_q(eq, axioms)
        if lq["derivable"] != verdict:
            problems.append(f"{ns}: {qid} Lean {lq['derivable']} != engine {verdict}")
        if qid in expected and expected[qid] != verdict:
            problems.append(f"{ns}: {qid} expected_derivable {expected[qid]} != span {verdict}")
        cert = lq["certificate"]
        if lq["derivable"]:
            combo = tuple(sum((cert[i] * ax[i][j] for i in range(len(ax))), Fraction(0))
                          for j in range(len(cols)))
            if len(cert) != len(ax) or combo != v:
                problems.append(f"{ns}: {qid} certificate does not give the formula")
            else:
                counts["derivable"] += 1
        else:
            if len(cert) != len(cols) or any(_dot(cert, row) for row in ax) or not _dot(cert, v):
                problems.append(f"{ns}: {qid} functional does not separate")
            else:
                counts["refused"] += 1
    return counts


def agreement(text: Optional[str] = None) -> Dict[str, object]:
    """Re-check every statement of ``Wheels/CentWheels.lean`` against the
    Python, exactly.  Returns ``{"ok", "wheels", "axioms", "derivable",
    "refused", "supplied", "theorems", "problems"}``."""
    from . import cent_wheels as CW
    from . import DOMAIN_WHEELS
    from .cent_wheels_study import wheel_questions
    from ..engineering.wheels import wheel_named
    text = lean_text() if text is None else text
    problems: List[str] = []
    out: Dict[str, object] = {"ok": False, "wheels": 0, "axioms": 0, "derivable": 0,
                              "refused": 0, "supplied": [], "theorems": 0, "problems": problems}
    if not text:
        problems.append(f"{CENT_WHEELS_LEAN} is missing")
        return out
    code = _code_only(text)
    for bad in ("sorry", "admit", "native_decide", "axiom"):
        if re.search(rf"(^|[^\w.']){bad}\b", code, re.MULTILINE):
            problems.append(f"the file's code contains {bad!r}")
    bl = blocks(text)
    groups: List[Tuple[str, Sequence[str], Mapping, Sequence[Tuple[str, str]], Mapping]] = []
    for w in CW.CENT_WHEELS:
        groups.append((w.id, w.axioms, CW.CENT_TABLES[w.id], wheel_questions(w),
                       {c.id: c.expected_derivable for c in w.cases}))
    for wid in ("W4", "W6"):
        ext = CW.extended_wheel(wid)
        groups.append((f"{wid}Ext", ext.axioms, CW.ADDITION_TABLES[wid],
                       [(c.id, c.equation) for c in ext.cases],
                       {c.id: c.expected_derivable for c in ext.cases}))
    for base in DOMAIN_WHEELS:
        cases = CW.DOMAIN_CASES[base.id]
        groups.append((f"{base.id}Dom", base.axioms, CW.DOMAIN_TABLES[base.id],
                       [(c.id, c.equation) for c in cases],
                       {c.id: c.expected_derivable for c in cases}))
    for ns, axioms, table, questions, expected in groups:
        if ns not in bl:
            problems.append(f"namespace {ns} is missing")
            continue
        try:
            parsed = parse_block(bl[ns])
        except ValueError as exc:
            problems.append(f"{ns}: {exc}")
            continue
        c = _check_wheel(ns, parsed, axioms, table, questions, expected, problems)
        out["wheels"] += 1
        for k in ("axioms", "derivable", "refused"):
            out[k] += c[k]
    # W6-03 without the addition: refused by the registry's W6 axioms alone.
    if "W6Ext" in bl:
        parsed = parse_block(bl["W6Ext"])
        wo = parsed["without"]
        base = wheel_named("W6")
        eq = CW.ENGINEERING_ADDITIONS["W6"][1].equation
        if wo is None or wo["k"] != len(base.axioms):
            problems.append("W6Ext: the theorem without the addition is missing")
        else:
            ax = parsed["ax"][:wo["k"]]
            if (any(_dot(wo["functional"], r) for r in ax) or not _dot(wo["functional"], wo["vector"])
                    or CW.is_derivable_q(eq, base.axioms)):
                problems.append("W6Ext: W6-03 without the addition is not refused as stated")
            else:
                out["refused"] += 1
    # The supplied axioms that fail at SI7.
    sup = parse_supplied(bl.get("Supplied", ""))
    if not sup:
        problems.append("the section Supplied is missing")
    for name, s in sorted(sup.items()):
        need = ("coords", "vector", "dim", "residual")
        if any(k not in s for k in need):
            problems.append(f"Supplied.{name}: incomplete")
            continue
        rel = CW.relation_vector_q(s["text"])
        cols = tuple(CW.columns(rel))
        if tuple(s["coords"]) != cols or tuple(s["vector"]) != tuple(rel[c] for c in cols):
            problems.append(f"Supplied.{name}: the vector is not the supplied text's")
            continue
        res = _dim_image(s["dim"], s["vector"])
        if res != tuple(s["residual"]) or not any(res[:CW.SI7_AXES]):
            problems.append(f"Supplied.{name}: the residual is wrong or zero at SI7")
            continue
        out["supplied"].append((s["wheel"], s["index"], s["text"]))
    out["theorems"] = len(theorem_names(text))
    out["ok"] = not problems
    return out
