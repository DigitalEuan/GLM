"""``glm_universal.runtime.dependency_frames`` -- questions about what a Lean
result rests on (Phase 101, ``studies/CITATION_SCOPE_STUDY.md`` §2.1).

Three phrasings, read from the raw text because declaration names are
case-sensitive, and answered by
:mod:`glm_universal.reasoning.proof_dependency` over the elaborator's
citation graph:

* ``does A rest on B`` (or ``depend on``) -- yes with a witness path, or no
  with the closure of ``A`` as the certificate of absence;
* ``what does A rest on`` -- the closure of ``A``;
* ``what rests on A`` / ``which declarations rest on A`` -- everything a
  change to ``A`` can reach.

Every reading carries a column-3 script that re-derives it from the
adjacency it embeds; the frame layer runs it under ``python3 -I`` before the
answer is output, as for every other frame.
"""

from __future__ import annotations

import re
from typing import Optional

from ..reasoning import proof_dependency as pd
from .question_frames import Frame, Reading

__all__ = ["match_raw", "read_dependency", "DEPENDENCY_FRAME", "mutated"]

_NAME = r"`?([A-Za-z_][\w.'!?«»]*?)`?"
_DOES = re.compile(rf"^\s*does\s+{_NAME}\s+(?:rest|depend)s?\s+on\s+{_NAME}"
                   rf"\s*\??\s*$", re.I)
_WHAT_DOES = re.compile(rf"^\s*what\s+does\s+{_NAME}\s+(?:rest|depend)\s+on"
                        rf"\s*\??\s*$", re.I)
_WHAT_RESTS = re.compile(rf"^\s*(?:what|which\s+(?:declarations|results))\s+"
                         rf"(?:rests?|depends?)\s+on\s+{_NAME}\s*\??\s*$",
                         re.I)

BACKING = ("reasoning.proof_dependency (breadth-first search over the "
           "elaborator's citation graph)")


def match_raw(text: str) -> Optional[dict]:
    """The givens of a dependency question, or ``None``."""
    t = text.strip()
    m = _DOES.match(t)
    if m:
        return {"kind": "rests_on", "a": m.group(1), "b": m.group(2)}
    m = _WHAT_DOES.match(t)
    if m:
        return {"kind": "closure", "a": m.group(1)}
    m = _WHAT_RESTS.match(t)
    if m:
        return {"kind": "dependents", "a": m.group(1)}
    return None


def _shown(names, limit: int = 8) -> str:
    names = list(names)
    head = ", ".join(names[:limit])
    return head + (f" and {len(names) - limit} more" if len(names) > limit
                   else "")


def _answer(g: dict) -> pd.Answer:
    if g["kind"] == "rests_on":
        return pd.rests_on(g["a"], g["b"])
    if g["kind"] == "closure":
        return pd.what_rests_on(g["a"])
    return pd.dependents(g["a"])


def read_dependency(g: dict, mutate: bool = False) -> Reading:
    """The reading of one dependency question.  ``mutate`` builds the D2
    control: the verdict flipped (or the count moved by one), its script
    must fail."""
    try:
        ans = _answer(g)
    except pd.DependencyError as e:
        return Reading("proof_dependency", False, e.why,
                       f"The question was not answered: {e.why}.",
                       "refused " + e.code,
                       f"print('REFUSED {e.code} VERIFIED True')\n",
                       code=e.code, backing=BACKING)
    if ans.kind == "rests_on":
        if ans.verdict:
            steps = len(ans.path) - 1
            value = (f"yes: {ans.source} rests on {ans.target}, through "
                     f"{steps} elaborated use{'s' if steps != 1 else ''}: "
                     + " -> ".join(ans.path))
            col2 = "; ".join(f"{a} uses {b}"
                             for a, b in zip(ans.path, ans.path[1:]))
        else:
            value = (f"no: {ans.target} is not among the "
                     f"{len(ans.members)} declarations {ans.source} rests on")
            col2 = (f"closure of {ans.source}: {len(ans.members)} "
                    f"declarations, closed under use, {ans.target} absent")
        col1 = ("A result rests on what its elaborated statement and proof "
                "use, and on what those rest on; so the question is whether "
                f"{ans.target} is reachable from {ans.source} in the "
                "elaborator's citation graph.")
        if mutate:
            fake = (ans.source, ans.target) if not ans.verdict else None
            script = pd.script_for(ans, claim=not ans.verdict, path=fake)
        else:
            script = pd.script_for(ans)
    else:
        if ans.kind == "closure":
            value = (f"{ans.source} rests on {len(ans.members)} declarations "
                     f"of the development; directly on {len(ans.direct)}: "
                     f"{_shown(ans.direct)}")
            col1 = (f"Everything reachable from {ans.source} by elaborated "
                    "use, collected by a breadth-first search.")
        else:
            value = (f"{len(ans.members)} declarations rest on "
                     f"{ans.source}; directly {len(ans.direct)}: "
                     f"{_shown(ans.direct)}")
            col1 = (f"Everything from which {ans.source} is reachable by "
                    "elaborated use: the results a change to it can reach.")
        col2 = f"search over {len(ans.adjacency)} nodes, closed under use"
        script = pd.script_for(ans, count=(len(ans.members) + 1
                                           if mutate else None))
    return Reading("proof_dependency", True, value, col1, col2, script,
                   backing=BACKING)


def mutated(text: str) -> Optional[Reading]:
    g = match_raw(text)
    return None if g is None else read_dependency(g, mutate=True)


DEPENDENCY_FRAME = Frame("proof_dependency",
                         "what a Lean result of the development rests on, "
                         "and what rests on it", lambda t: None,
                         read_dependency, source="M")
