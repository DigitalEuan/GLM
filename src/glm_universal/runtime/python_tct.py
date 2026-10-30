"""Isolated execution of a Python-speech column-3 script.

The reasoning layer may not start processes, so the one step of Three Column
Thinking that needs a fresh interpreter -- running the generated
re-derivation script with ``python3 -I`` and an empty environment -- lives
here, next to the other TCT runner (``tct_engine``).
"""

from __future__ import annotations

import importlib.util
import io
import os
import subprocess
import sys
import tempfile
from typing import Dict

from .tct_engine import package_root, script_is_exact


def run_column3(text: str, timeout: int = 120) -> Dict[str, object]:
    """Run ``text`` in a fresh isolated interpreter; report VERIFIED True."""
    exact, offenders = script_is_exact(text)
    fd, path = tempfile.mkstemp(suffix=".py", prefix="glm_tct_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        proc = subprocess.run([sys.executable, "-I", path],
                              capture_output=True, text=True,
                              timeout=timeout, env={})
        out = proc.stdout
        verified = proc.returncode == 0 and "VERIFIED True" in out
        return {"verified": verified and exact, "exact": exact,
                "offenders": list(offenders), "returncode": proc.returncode,
                "stdout": out[-400:], "stderr": proc.stderr[-400:]}
    finally:
        os.unlink(path)


def question_surface_control() -> Dict[str, object]:
    """How many declared Python value programs ``GLM.py -q`` solves."""
    from ..evaluation import python_speech_cases as C
    spec = importlib.util.spec_from_file_location(
        "_glm_cli", package_root() / "GLM.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    solved = []
    for cid, src in C.VALUE_CASES:
        code = cli.main(["-q", src.replace("\n", "; ")], out=io.StringIO())
        if code == 0:
            solved.append(cid)
    return {"solved": len(solved), "of": len(C.VALUE_CASES),
            "solved_cases": solved}


def _reverse_answers():
    """Every answered declared case of the reverse study, as ``(id, Answer)``."""
    from ..evaluation import reverse_tct_cases as C
    from ..reasoning import reverse_tct as rt
    out = []
    out += [(cid, rt.say(src)) for cid, src, _ in C.SAY_CASES]
    out += [(cid, rt.entails(list(ps), c)) for cid, ps, c, _ in
            C.ENTAIL_CASES]
    out += [(cid, rt.solve(v, s)) for cid, v, s, _ in C.SOLVE_CASES]
    out += [(cid, rt.bounds(v, list(ps))) for cid, v, ps, _ in
            C.BOUNDS_CASES]
    out += [(cid, rt.equivalent(a, b)) for cid, a, b, _ in
            C.EQUIVALENCE_CASES]
    out += [(cid, rt.paraphrase(s)) for cid, s in C.PARAPHRASE_CASES]
    out += [(cid, rt.negate(s)) for cid, s, _ in C.NEGATE_CASES]
    return [(cid, a) for cid, a in out if a.answered]


def reverse_scripts() -> Dict[str, object]:
    """V3 of ``studies/REVERSE_TCT_STUDY.md``: every answered declared case's
    column-3 script re-reads column 1 and re-checks the certificate in a
    fresh ``python3 -I``; every mutated certificate is rejected."""
    from ..reasoning import reverse_tct_script as rs
    root = str(package_root())
    verified, failed, mutants, caught, escaped = 0, [], 0, 0, []
    for cid, a in _reverse_answers():
        if run_column3(rs.render_script(a, root))["verified"]:
            verified += 1
        else:
            failed.append(cid)
        bad = rs.mutated_script(a, root)
        if bad is None:
            continue
        mutants += 1
        if run_column3(bad)["verified"]:
            escaped.append(cid)
        else:
            caught += 1
    total = verified + len(failed)
    return {"scripts": total, "verified": verified, "failed": failed,
            "mutants": mutants, "caught": caught, "escaped": escaped}


def _reverse_two_answers(relay: bool = True):
    """Every answered declared case of round two (``studies/
    REVERSE_TCT_STUDY.md`` §7), as ``(id, Answer)``; ``relay`` adds the
    relayed cases, which call the planner."""
    from ..evaluation import reverse_tct_two_cases as C
    from ..reasoning import reverse_tct as rt
    out = []
    out += [(cid, rt.say(src)) for cid, src, _ in C.SAY_CASES]
    out += [(cid, rt.entails(list(ps), c)) for cid, ps, c, _ in
            C.ENTAIL_CASES]
    out += [(cid, rt.bounds(v, list(ps))) for cid, v, ps, _ in
            C.BOUNDS_CASES]
    out += [(cid, rt.equivalent(a, b)) for cid, a, b, _ in
            C.EQUIVALENCE_CASES]
    out += [(cid, rt.negate(s)) for cid, s, _ in C.NEGATE_CASES]
    if relay:
        from .reverse_relay import relay as run_relay
        out += [(cid, run_relay(None, q)) for cid, q, _ in C.RELAY_CASES]
    return [(cid, a) for cid, a in out if a.answered]


def reverse_two_scripts(relay: bool = True) -> Dict[str, object]:
    """W5 of round two: every answered round-two case's column-3 script
    prints ``VERIFIED True`` in a fresh ``python3 -I``, and every mutated
    certificate is rejected (the Phase 67 half is :func:`reverse_scripts`)."""
    from ..reasoning import reverse_tct_script as rs
    root = str(package_root())
    verified, failed, mutants, caught, escaped = 0, [], 0, 0, []
    by_kind: Dict[str, int] = {}
    for cid, a in _reverse_two_answers(relay):
        by_kind[a.operation] = by_kind.get(a.operation, 0) + 1
        if run_column3(rs.render_script(a, root))["verified"]:
            verified += 1
        else:
            failed.append(cid)
        bad = rs.mutated_script(a, root)
        if bad is None:
            continue
        mutants += 1
        if run_column3(bad)["verified"]:
            escaped.append(cid)
        else:
            caught += 1
    total = verified + len(failed)
    return {"scripts": total, "verified": verified, "failed": failed,
            "mutants": mutants, "caught": caught, "escaped": escaped,
            "by_operation": by_kind}


def reverse_questions():
    """The declared entailment, solve and bounds cases as question texts,
    with the verdict or answer each must give (V4, V5)."""
    from ..evaluation import reverse_tct_cases as C
    out = []
    for cid, ps, c, want in C.ENTAIL_CASES:
        out.append((cid, "entails: " + " ; ".join(list(ps) + [c]), want))
    for cid, v, st, want in C.SOLVE_CASES:
        out.append((cid, f"solve for {v}: {st}", want))
    for cid, v, ps, want in C.BOUNDS_CASES:
        out.append((cid, f"bounds of {v}: " + " ; ".join(ps), want))
    return out


def reverse_control() -> Dict[str, object]:
    """The control of V4/V5: the same questions on the default path as it
    stood before the reverse surface (the router with that surface skipped:
    Python dialect, engineering, then the planner)."""
    from ..engineering import speak as es
    from ..reasoning import reverse_tct as rv
    from .parser import QueryError
    from .router import python_reads
    from .session import GeometricSession
    session = GeometricSession()
    rows = []
    for cid, text, want in reverse_questions():
        if python_reads(text):
            surface = "python"
            answered, body = False, ""
        elif es.answer(text)[0] != "unread":
            surface = "engineering"
            sol = session.ask_engineering(text)
            answered, body = bool(sol.ok), str(sol.answer)
        else:
            surface = "planner"
            try:
                sol = session.ask_planned(text)
                answered, body = bool(sol.ok), str(sol.answer)
            except QueryError:
                answered, body = False, ""
        mine = rv.answer(text)
        mine_text = mine.sentence if mine.operation != "entails" else \
            mine.verdict
        mine_got = mine_text if mine.answered else mine.refusal
        rows.append({"id": cid, "surface": surface, "answered": answered,
                     "correct": answered and want in body,
                     "reverse_correct": mine_got == want})
    return {"questions": len(rows),
            "control_answered": sum(r["answered"] for r in rows),
            "control_correct": sum(r["correct"] for r in rows),
            "reverse_correct": sum(r["reverse_correct"] for r in rows),
            "surfaces": sorted({r["surface"] for r in rows}), "rows": rows}


def reverse_int_scripts() -> Dict[str, object]:
    """X3 of round three (``studies/REVERSE_TCT_STUDY.md`` §10): every
    answered declared case over the integers gets a column-3 script that
    prints ``VERIFIED True`` in a fresh ``python3 -I``, and every mutated
    certificate is rejected."""
    from ..reasoning import reverse_tct_int as ri
    root = str(package_root())
    verified, failed, mutants, caught, escaped = 0, [], 0, 0, []
    by_kind: Dict[str, int] = {}
    for cid, a in ri.declared_answers():
        by_kind[a.operation] = by_kind.get(a.operation, 0) + 1
        if run_column3(ri.render_script(a, root))["verified"]:
            verified += 1
        else:
            failed.append(cid)
        bad = ri.mutated_script(a, root)
        if bad is None:
            continue
        mutants += 1
        if run_column3(bad)["verified"]:
            escaped.append(cid)
        else:
            caught += 1
    total = verified + len(failed)
    return {"scripts": total, "verified": verified, "failed": failed,
            "mutants": mutants, "caught": caught, "escaped": escaped,
            "by_operation": by_kind}
