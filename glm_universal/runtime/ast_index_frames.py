"""``glm_universal.runtime.ast_index_frames`` -- where an expression is
computed (Phase 105, ``studies/AST_INDEX_STUDY.md`` §1).

Four phrasings, read from the raw text because an expression is
case-sensitive, with the expression between backticks:

* ``where is `EXPR` computed?`` and ``where else is `EXPR` computed?`` --
  both corpora;
* ``where in the archive is `EXPR` computed?`` -- the owner's archived GLM
  tree (``source_material/GLM-main.zip``);
* ``where in the live code is `EXPR` computed?`` -- ``overlay/glm_universal``.

The answer is every site of the frozen index structurally equal to
``EXPR`` (:mod:`glm_universal.reasoning.ast_index`), with the renaming that
witnesses each.  Its column-3 script carries the brute-force reference,
recomputes the bucket key of the query and of every member of its bucket,
and re-decides each member; the frame layer runs it under ``python3 -I``
before the answer is output, as for every other frame.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Sequence, Tuple

from ..reasoning import ast_index as ai
from .question_frames import Frame, Reading

__all__ = ["match_raw", "read_ast_index", "AST_INDEX_FRAME", "mutated",
           "script_for"]

_WHERE = re.compile(r"^\s*where\s+(else\s+|in\s+the\s+archive\s+|in\s+the\s+"
                    r"live\s+code\s+)?is\s+`([^`]+)`\s+computed\s*\??\s*$",
                    re.I)

BACKING = ("reasoning.ast_index (bucket key, then the structural matcher, "
           "over the frozen index of the live code and the archive)")

SHOWN = 6


def match_raw(text: str) -> Optional[dict]:
    """The givens of a where-is-it-computed question, or ``None``."""
    m = _WHERE.match(text.strip())
    if not m:
        return None
    where = (m.group(1) or "").strip().lower()
    corpus = ("archive" if "archive" in where else
              "live" if "live" in where else "all")
    return {"expr": m.group(2).strip(), "corpus": corpus}


def script_for(query: str, bucket: Sequence[Sequence[object]],
               claimed: Sequence[int], digest: str) -> str:
    """The column-3 script: the reference, the bucket, the claim."""
    rows = [[str(r[0]), str(r[1]), int(r[2]), str(r[4])] for r in bucket]
    return (ai.REFERENCE_SOURCE
            + f"\nQUERY = {query!r}\nBUCKET = {rows!r}\n"
            f"CLAIMED = {list(claimed)!r}\nDIGEST = {digest!r}\n"
            "key = repr(blank(shape(ast.parse(QUERY, mode='eval').body)))\n"
            "same = all(repr(blank(shape(ast.parse(r[3], mode='eval').body)))"
            " == key for r in BUCKET)\n"
            "decided = [i for i, r in enumerate(BUCKET) "
            "if decide(QUERY, r[3])]\n"
            "ok = same and decided == CLAIMED\n"
            "print('snapshot', DIGEST[:12], 'bucket', len(BUCKET), "
            "'structurally equal', len(decided))\n"
            "print('VERIFIED', ok)\n")


def _lookup(g: dict):
    index = ai.the_index()
    form, bucket, found = index.lookup(g["expr"], g["corpus"])
    return index, form, bucket, found


def _witness(sigma: Dict[str, str]) -> str:
    moved = [f"{a}->{b}" for a, b in sorted(sigma.items()) if a != b]
    return ", ".join(moved) if moved else "same names"


def read_ast_index(g: dict, mutate: bool = False) -> Reading:
    """The reading of one question.  ``mutate`` builds the A7 control: one
    site dropped from the claim (or a site claimed absent when the answer
    is empty), and its script must fail."""
    try:
        index, form, bucket, found = _lookup(g)
    except ai.IndexRefusal as e:
        return Reading("ast_index", False, e.why,
                       f"The question was not answered: {e.why}.",
                       "refused " + e.code,
                       f"print('REFUSED {e.code} VERIFIED True')\n",
                       code=e.code, backing=BACKING)
    rows = index.rows
    digest = ai.frozen()["digest"]
    where = {"all": "the live code and the archive",
             "live": "the live code", "archive": "the archive"}[g["corpus"]]
    position = {i: k for k, i in enumerate(bucket)}
    claimed = [position[i] for i, _ in found]
    bucket_rows = [rows[i] for i in bucket]
    if mutate:
        if claimed:
            claimed = claimed[:-1]
        else:
            bucket_rows = bucket_rows + [["live", "(none)", 0, 0, g["expr"]]]
    script = script_for(g["expr"], bucket_rows, claimed, digest)
    per: Dict[str, int] = {}
    for i, _ in found:
        per[rows[i][0]] = per.get(rows[i][0], 0) + 1
    if found:
        shown = "; ".join(f"{rows[i][1]}:{rows[i][2]} `{rows[i][4]}` "
                          f"[{_witness(s)}]" for i, s in found[:SHOWN])
        more = (f"; and {len(found) - SHOWN} more" if len(found) > SHOWN
                else "")
        counts = ", ".join(f"{k} {v}" for k, v in sorted(per.items()))
        verb = "computes" if len(found) == 1 else "compute"
        value = (f"{len(found)} site{'s' if len(found) != 1 else ''} in "
                 f"{where} {verb} `{g['expr']}` up to renaming and operand "
                 f"order ({counts}): {shown}{more}")
    else:
        value = (f"no site in {where} computes `{g['expr']}` up to renaming "
                 f"and operand order (its bucket holds {len(bucket)} "
                 f"expression{'s' if len(bucket) != 1 else ''} of the same "
                 "shape, none structurally equal)")
    col1 = ("An expression is computed where a statement-level expression "
            "of the index equals it under a one-to-one renaming of variables "
            "and a choice of operand order at each commutative operator; the "
            "bucket key (variables erased, commutative operands sorted) "
            "cannot be moved by either, so only one bucket need be searched.")
    col2 = (f"bucket of {len(bucket)} in {where}, {len(found)} structurally "
            f"equal; snapshot {digest[:12]} of {len(rows)} sites")
    return Reading("ast_index", True, value, col1, col2, script,
                   backing=BACKING)


def mutated(text: str) -> Optional[Reading]:
    g = match_raw(text)
    return None if g is None else read_ast_index(g, mutate=True)


AST_INDEX_FRAME = Frame("ast_index",
                        "where a structurally equal expression is computed, "
                        "in the live code and the archived GLM tree",
                        lambda t: None, read_ast_index, source="I")
