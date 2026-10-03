"""``glm_universal.runtime.discourse_report`` -- the measurement of
``studies/DISCOURSE_STATE_STUDY.md`` (Phase 92), mark by mark.

D1  every column case as declared (0b), 0 wrong;
D2  every fourth-shape case as declared (D = 0a), 0 wrong;
D3  every surface case as declared (K3), 0 wrong;
D4  the controls: Phase 55's layer, the first-winner rule, the recency rule
    for *the one before that*, the session alone as the licence, and the
    switch ``carry=False``;
D5  nothing earlier moves: Phase 55's fifteen declared follow-ups keep their
    outcomes under the new layer, but for the one move declared in advance;
D6  the column computes nothing: every cell is the answer its rewritten text
    gets asked alone, and so is every single binding's answer;
D7  (Lean) ``RequestProject/GLM/DiscourseState.lean`` -- checked by the test;
D8  the shape census: which earlier declared texts the new phrasings would
    take for a follow-up.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Sequence, Tuple

from ..evaluation import discourse_cases as C
from .conversation import (Conversation, DECLARED_FOLLOW_UPS, FollowUpError,
                           PRONOUNS)
from .discourse import Discourse

__all__ = ["outcome_of", "group_report", "control_report", "earlier_report",
           "cells_report", "census_report", "discourse_report"]

_SESSION = None


def _session():
    global _SESSION
    if _SESSION is None:
        from .session import GeometricSession
        _SESSION = GeometricSession()
    return _SESSION


def _run(layer, script: Sequence[str]):
    """Run every turn but the last, and return the last turn's result."""
    for text in script[:-1]:
        try:
            layer.ask(text)
        except FollowUpError:
            pass
    return layer.ask(script[-1])


def outcome_of(layer, script: Sequence[str]) -> Dict[str, object]:
    """What the last turn of ``script`` comes to under ``layer``, in the
    vocabulary of :mod:`glm_universal.evaluation.discourse_cases`."""
    try:
        solution = _run(layer, script)
    except FollowUpError as error:
        return {"outcome": error.reason, "detail": str(error)}
    if solution.kind == "column":
        return {"outcome": ("column", tuple(solution.payload["members"])),
                "detail": solution.answer, "solution": solution}
    if solution.kind == "why":
        return {"outcome": ("why", solution.payload["subject"]),
                "detail": solution.answer, "solution": solution}
    turn = layer.turns[-1]
    if not solution.ok:
        return {"outcome": "unlicensed", "detail": solution.answer}
    name = turn.binding.name if turn.binding is not None else "whole"
    return {"outcome": name or "answer", "detail": solution.answer,
            "solution": solution, "rewritten": turn.asked}


GROUPS = (("column", C.COLUMN_CASES, False),
          ("fourth", C.FOURTH_CASES, False),
          ("surface", C.SURFACE_CASES, True))


def group_report() -> Dict[str, Dict[str, object]]:
    """D1-D3: every declared case under the layer it is declared for."""
    session = _session()
    out: Dict[str, Dict[str, object]] = {}
    for name, cases, surfaces in GROUPS:
        rows = []
        for key, script, want, note in cases:
            got = outcome_of(Discourse(session, surfaces=surfaces), script)
            rows.append({"key": key, "want": want, "got": got["outcome"],
                         "ok": got["outcome"] == want,
                         "detail": str(got["detail"])[:200]})
        refused = [r for r in rows if isinstance(r["want"], str)
                   and r["want"] in ("no-antecedent", "ambiguous-antecedent",
                                     "unlicensed", "column-incomplete",
                                     "number-mismatch")]
        out[name] = {"cases": len(rows), "met": sum(r["ok"] for r in rows),
                     "wrong": [r["key"] for r in rows if not r["ok"]],
                     "refusals": len(refused), "rows": rows}
    return out


def _first_member(script: Sequence[str], members: Sequence[str]) -> str:
    """The first-winner control: bind the first row of the set alone."""
    text = script[-1]
    pattern = re.compile(r"(?i)(?<![\w])(?:both of them|each of them|"
                         r"all of them|them|the one before that|"
                         + "|".join(PRONOUNS) + r")(?![\w])")
    return pattern.sub(lambda _m: members[0], text, count=1)


def control_report() -> Dict[str, object]:
    """D4: the five controls, each on the cases it has an opinion about."""
    session = _session()
    base_rows = []
    for key, script, want, _ in C.COLUMN_CASES + C.FOURTH_CASES:
        got = outcome_of(Conversation(session), script)
        base_rows.append({"key": key, "want": want, "got": got["outcome"],
                          "ok": got["outcome"] == want})
    new_cases = [r for r in base_rows if r["key"] not in
                 ("dead-set-walked-past", "no-tie-unchanged",
                  "comparison-still-ambiguous")]
    # the first-winner rule on every case declared to be a column
    first_rows = []
    for key, script, want, _ in C.ALL_CASES:
        if not (isinstance(want, tuple) and want[0] == "column"):
            continue
        members = want[1]
        surfaces = any(key == k for k, *_ in C.SURFACE_CASES)
        layer = Discourse(session, surfaces=surfaces)
        for text in script[:-1]:
            layer.ask(text)
        text = _first_member(script, members)
        answered = bool(layer._ask_one(text).ok)
        first_rows.append({"key": key, "rows": len(members),
                           "answered": answered, "covers": 1})
    # the recency rule for the prior phrasing: the second most recent mention
    prior_rows = []
    for key, script, want, _ in C.FOURTH_CASES:
        if not key.startswith("prior"):
            continue
        layer = Discourse(session)
        for text in script[:-1]:
            layer.ask(text)
        names = []
        for m in layer.mentions():
            if m.name not in names:
                names.append(m.name)
        pick = names[1] if len(names) > 1 else None
        if pick is None:
            got = "no-antecedent"
        else:
            sol = session.ask(script[-1].replace("the one before that", pick))
            got = pick if sol.ok else "unlicensed"
        prior_rows.append({"key": key, "want": want, "got": got,
                           "agrees": got == want})
    # the session alone as the licence, on the surface cases
    alone_rows = []
    for key, script, want, _ in C.SURFACE_CASES:
        got = outcome_of(Discourse(session, surfaces=False), script)
        alone_rows.append({"key": key, "want": want, "got": got["outcome"],
                           "ok": got["outcome"] == want})
    # the switch: carry off returns every tie to Phase 55's refusal
    carry_rows = []
    for key, script, want, _ in C.COLUMN_CASES:
        got = outcome_of(Discourse(session, carry=False), script)
        carry_rows.append({"key": key, "want": want, "got": got["outcome"]})
    tie_keys = ("tie-describe", "tie-field", "tie-incomplete",
                "column-carried")
    carry_reverted = [r["key"] for r in carry_rows if r["key"] in tie_keys
                      and r["got"] == "ambiguous-antecedent"]
    alone_answers = [r["key"] for r in alone_rows if r["ok"]
                     and r["want"] != "unlicensed"]
    met = (not any(r["ok"] for r in new_cases)
           and all(r["answered"] for r in first_rows)
           and any(not r["agrees"] for r in prior_rows)
           and not alone_answers
           and len(carry_reverted) == len(tie_keys))
    return {"base": {"cases": len(base_rows),
                     "as_declared": [r["key"] for r in base_rows if r["ok"]],
                     "new_cases": len(new_cases),
                     "new_as_declared": [r["key"] for r in new_cases
                                         if r["ok"]],
                     "rows": base_rows},
            "first_winner": {"cases": len(first_rows),
                             "answered": sum(r["answered"]
                                             for r in first_rows),
                             "rows_dropped": sum(r["rows"] - 1
                                                 for r in first_rows),
                             "rows": first_rows},
            "recency": {"cases": len(prior_rows),
                        "differs": [r["key"] for r in prior_rows
                                    if not r["agrees"]],
                        "rows": prior_rows},
            "session_alone": {"cases": len(alone_rows),
                              "answers_as_declared": alone_answers,
                              "rows": alone_rows},
            "carry_off": {"ties": len(tie_keys),
                          "reverted": carry_reverted, "rows": carry_rows},
            "met": met}


def earlier_report() -> Dict[str, object]:
    """D5: Phase 55's declared follow-ups under the new layer."""
    session = _session()
    rows = []
    for key, script, expected, _ in DECLARED_FOLLOW_UPS:
        got = outcome_of(Discourse(session), script)["outcome"]
        want = C.DECLARED_MOVES.get(key, expected)
        rows.append({"key": key, "phase55": expected, "got": got,
                     "declared_now": want, "ok": got == want})
    moved = [r["key"] for r in rows if r["got"] != r["phase55"]]
    return {"cases": len(rows), "met_count": sum(r["ok"] for r in rows),
            "moved": moved, "declared_moves": sorted(C.DECLARED_MOVES),
            "rows": rows,
            "met": all(r["ok"] for r in rows)
            and sorted(moved) == sorted(C.DECLARED_MOVES)}


def cells_report() -> Dict[str, object]:
    """D6: every cell, and every single answer, is the answer its rewritten
    text gets asked alone of a fresh asker."""
    from .router import ask_routed
    from .session import GeometricSession
    fresh = GeometricSession()
    cells = singles = 0
    differ: List[str] = []
    for name, cases, surfaces in GROUPS:
        for key, script, want, _ in cases:
            got = outcome_of(Discourse(_session(), surfaces=surfaces), script)
            sol = got.get("solution")
            if sol is None:
                continue
            ask = ((lambda t: ask_routed(fresh, t)) if surfaces
                   else fresh.ask)
            if sol.kind == "column":
                for cell in sol.payload["cells"]:
                    cells += 1
                    if ask(cell["asked"]).answer != cell["answer"]:
                        differ.append(f"{key}:{cell['row']}")
            elif sol.kind != "why" and "rewritten" in got:
                singles += 1
                if ask(got["rewritten"]).answer != sol.answer:
                    differ.append(key)
    return {"cells": cells, "singles": singles, "differ": differ,
            "met": not differ and cells > 0}


def census_report() -> Dict[str, object]:
    """D8: the earlier declared texts the new phrasings take for a
    follow-up -- every string of twelve characters or more of every earlier
    declared corpus and both outside sets -- and whether the machine answers
    any of them alone.  One it answers alone is answered alone by the layer
    too (whole first), so only a text it refuses alone can change: from one
    refusal to another."""
    from .router import ask_routed
    from .typed_operators_report import earlier_questions
    session = _session()
    new = Discourse(session)
    old = Conversation(session)
    texts = [(m, s) for m, s in earlier_questions()
             if m != "discourse_cases"]
    taken: List[Tuple[str, str, str]] = []
    released: List[Tuple[str, str, str]] = []
    for module, text in texts:
        a = old.shape_of(text)
        b = new.shape_of(text)
        if a is None and b is not None:
            taken.append((module, b, text))
        elif a is not None and b is None:
            released.append((module, str(a), text))
    alone = [t for t in taken if ask_routed(session, t[2]).ok]
    trim = lambda rows: [(m, k, t[:90]) for m, k, t in rows]  # noqa: E731
    return {"strings": len(texts), "taken": trim(taken),
            "released": trim(released),
            "taken_count": len(taken), "released_count": len(released),
            "taken_answered_alone": len(alone),
            "distinct_taken": len({t for _, _, t in taken}),
            "met": not released}


def discourse_report(census: bool = True) -> Dict[str, object]:
    """Every measured mark of the study."""
    groups = group_report()
    control = control_report()
    earlier = earlier_report()
    cells = cells_report()
    rep: Dict[str, object] = {
        "groups": groups, "control": control, "earlier": earlier,
        "cells": cells,
        "census": census_report() if census else None,
    }
    rep["marks"] = {
        "D1": groups["column"]["met"] == groups["column"]["cases"],
        "D2": groups["fourth"]["met"] == groups["fourth"]["cases"],
        "D3": groups["surface"]["met"] == groups["surface"]["cases"],
        "D4": control["met"],
        "D5": earlier["met"],
        "D6": cells["met"],
        "D8": rep["census"]["met"] if census else None,
    }
    return rep
