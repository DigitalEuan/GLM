"""``glm_universal.engineering.context_frames_study`` -- the marks of
``studies/CONTEXT_FRAMES_STUDY.md`` (Phase 170).

The six declared contexts live in
:mod:`glm_universal.engineering.context_frames`; this module takes the
pre-registered marks (§4):

* **X1** -- ``ContextFrames.lean`` declares the ten theorems of §2 with no
  ``sorry`` (read from the text; the build itself is the Lean side's check);
* **X2** -- without a context nothing moves: the domain battery gives 21 of
  23 declared laws, refuses 9 of 9, 0 wrong, and the end-to-end evaluation
  has no failure;
* **X3** -- *the energy is delivered over a time*: energy from power and time
  and power from energy and time give ``energy = power * time`` and
  ``power = energy / time``;
* **X4** -- *the energy is stored in a capacitor*: both answer, through W3,
  with a relation different from X3's; *stored in an inductor*: energy from
  power and time is refused;
* **X5** -- *a rotating body drives the wave*: angular frequency from angular
  velocity and its reverse give ``angular_frequency = angular_velocity``,
  angular frequency from power and torque gives ``angular_frequency = power /
  torque``; without the context both are refused.  As written x5b (the
  reverse) carries x5a's law, which a comparison up to a *positive* multiple
  grades wrong; **X5′** (the amendment of §7.1) grades x5b against
  ``angular_velocity = angular_frequency``;
* **X6** -- over every two-input question on the fifteen wheels' names that a
  pinned name enters, under each pin context, no question answered without
  the context is answered differently with it (:func:`pin_census`);
* **X7** -- the domain battery with *a rotating body drives the wave*
  appended to every question grades exactly as without it;
* **X8** -- four probes refused, each with its declared reason.

A mark whose evidence is not present is reported missed and named in
``unmeasured``, never assumed: the Lean file ``ContextFrames.lean`` and the
battery ``evaluation/domain_cases.py`` were lost in the October 2026
reorganisation, so X1, X2 and X7 are missed until they are restored (X2
also needs the end-to-end evaluation, which this module does not run).

The standard apparatus: :func:`compute` (takes everything, about a quarter
of an hour on one process for X6; ``jobs`` processes), :func:`measure`,
:func:`write_measurements` (``engineering/_data/context_frames_study.json``
beside the digest of the code), :func:`measurements`, :func:`state`,
:func:`current`, :func:`module_digest` and :func:`context_frames_report`
(``available=False`` with the re-take instruction when nothing current is
stored).

Exact and float-free (D7).

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from studies/CONTEXT_FRAMES_STUDY.md
(§§1, 2, 4, 7), studies/CONTEXT_FRAMES_STUDY.yaml, MASTER_PLAN.md Phase 170
and the CLI handler ``_context_frames`` in glm_universal/tools.py.*
"""
from __future__ import annotations

import itertools
import json
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .. import integrity
from ..wheels import ALL_WHEELS
from . import context_frames as cf
from . import domains as dmn
from . import wheels as wh

__all__ = [
    "DATA_PATH", "LEAN_FILE", "LEAN_THEOREMS", "PROBES", "MARKS", "AMENDED",
    "ask", "grade_probe", "probes", "pin_questions", "pin_census",
    "lean_status", "batteries", "compute", "measure", "write_measurements",
    "measurements", "state", "current", "module_digest",
    "context_frames_report",
]

_HERE = Path(__file__).resolve().parent
DATA_PATH = _HERE / "_data" / "context_frames_study.json"

#: The ten theorems of ``ContextFrames.lean`` (§2; MASTER_PLAN.md Phase 170).
LEAN_FILE = "ContextFrames.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "pin_never_changes", "pin_answer_mem", "pin_same_answer",
    "delivered_energy", "stored_energy_half", "energyWitness_vanishes",
    "stored_energy_not_full", "reference_circle_joined",
    "circleWitness_vanishes", "reference_circle_split",
)

MARKS: Tuple[str, ...] = ("X1", "X2", "X3", "X4", "X5", "X6", "X7", "X8")
AMENDED: Tuple[str, ...] = ("X5′",)

_DELIVERED = "the energy is delivered over a time"
_CAPACITOR = "the energy is stored in a capacitor"
_INDUCTOR = "the energy is stored in an inductor"
_ROTATING = "a rotating body drives the wave"
_LC = "the oscillator is an lc circuit"

#: The probes of X3, X4, X5 and X8, each ``(key, question, expectation)``.
#: An expectation is ``("law", equation)``, ``("differs", key, wheel)`` (an
#: answer through ``wheel`` whose relation is not the one ``key`` declared),
#: ``("refuse", None)`` or ``("refuse", reason-words)`` (refused, with a
#: reason holding those words).
PROBES: Tuple[Tuple[str, str, Tuple[Any, ...]], ...] = (
    ("x3a", f"derive energy from power and time across domains where {_DELIVERED}",
     ("law", "energy = power * time")),
    ("x3b", f"derive power from energy and time across domains where {_DELIVERED}",
     ("law", "power = energy / time")),
    ("x4a", f"derive energy from power and time across domains where {_CAPACITOR}",
     ("differs", "x3a", "W3")),
    ("x4b", f"derive power from energy and time across domains where {_CAPACITOR}",
     ("differs", "x3b", "W3")),
    ("x4c", f"derive energy from power and time across domains where {_INDUCTOR}",
     ("refuse", None)),
    ("x5a", "derive angular frequency from angular velocity across domains "
            f"where {_ROTATING}",
     ("law", "angular_frequency = angular_velocity")),
    ("x5b", "derive angular velocity from angular frequency across domains "
            f"where {_ROTATING}",
     ("law", "angular_frequency = angular_velocity")),       # as written
    ("x5c", "derive angular frequency from power and torque across domains "
            f"where {_ROTATING}",
     ("law", "angular_frequency = power / torque")),
    ("x5d", "derive angular frequency from angular velocity across domains",
     ("refuse", None)),
    ("x5e", "derive angular frequency from power and torque across domains",
     ("refuse", None)),
    ("x8a", "derive energy from power and time across domains where the "
            "energy is warm", ("refuse", "is not declared")),
    ("x8b", f"derive density from mass and volume across domains where {_DELIVERED}",
     ("refuse", "does not ask about")),
    ("x8c", "derive energy from power and time across domains where "
            f"{_DELIVERED} and {_CAPACITOR}", ("refuse", "say different things")),
    ("x8d", "derive spring constant from mass and angular frequency across "
            f"domains where {_LC}", ("refuse", "no derivation remains")),
)

#: X5′: x5b's law written for its own target (amendment, §7.1).
AMENDED_LAWS: Dict[str, str] = {"x5b": "angular_velocity = angular_frequency"}


def _plain(x: Any) -> Any:
    if isinstance(x, Fraction):
        return str(x)
    if isinstance(x, dict):
        return {(k if isinstance(k, str) else str(k)): _plain(v)
                for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


# ===========================================================================
# 1.  THE PROBES (X3, X4, X5, X8)
# ===========================================================================

def ask(question: str,
        junctions: Optional[Mapping[Tuple[str, str], Sequence[str]]] = None
        ) -> Optional[dmn.DomainAnswer]:
    """An *across domains* question read by the frame's own parser and
    answered as the engineering surface answers it (a ``where`` clause by
    :func:`context_frames.derive_in_context`); ``None`` when unread."""
    got = dmn.read_question(question)
    if got is None:
        return None
    target, inputs, where = got
    if where is not None:
        return cf.derive_in_context(target, inputs, where, junctions)
    return dmn.derive_domains(target, inputs, junctions)


def grade_probe(ans: Optional[dmn.DomainAnswer], expect: Tuple[Any, ...],
                laws: Mapping[str, str]) -> str:
    """``correct`` / ``correct refusal`` (pass) or ``wrong`` / ``refused`` /
    ``refused, other reason`` / ``unread`` (fail)."""
    if ans is None:
        return "unread"
    kind = expect[0]
    if kind == "law":
        if not ans.answered:
            return "refused"
        return "correct" if dmn.same_relation(ans.equation, expect[1]) else "wrong"
    if kind == "differs":
        if not ans.answered:
            return "refused"
        other = laws[expect[1]]
        ok = expect[2] in ans.wheels and not dmn.same_relation_any(ans.equation,
                                                                   other)
        return "correct" if ok else "wrong"
    if ans.answered:
        return "wrong"
    words = expect[1]
    if not ans.reason:
        return "refused, other reason"
    if words is not None and words not in ans.reason:
        return "refused, other reason"
    return "correct refusal"


def probes(amended: bool = False) -> List[Dict[str, Any]]:
    """Every probe asked and graded (``amended``: X5′'s law for x5b)."""
    laws = {k: e[1] for k, _, e in PROBES if e[0] == "law"}
    out = []
    for key, question, expect in PROBES:
        if amended and key in AMENDED_LAWS:
            expect = ("law", AMENDED_LAWS[key])
        ans = ask(question)
        grade = grade_probe(ans, expect, laws)
        out.append({"key": key, "question": question,
                    "expect": [str(e) for e in expect], "grade": grade,
                    "passed": grade in ("correct", "correct refusal"),
                    "text": "unread" if ans is None else ans.text(),
                    "wheels": [] if ans is None else list(ans.wheels)})
    return out


def _passed(rows: Sequence[Mapping[str, Any]], prefix: str) -> bool:
    sel = [r for r in rows if r["key"].startswith(prefix)]
    return bool(sel) and all(r["passed"] for r in sel)


# ===========================================================================
# 2.  THE PIN CENSUS (X6)
# ===========================================================================

def _names() -> List[str]:
    return sorted({q for w in ALL_WHEELS for q in wh.wheel_quantities(w)})


def pin_questions(name: str, names: Optional[Sequence[str]] = None
                  ) -> List[Tuple[str, Tuple[str, str]]]:
    """Every two-input question on the wheels' names that ``name`` enters,
    as target or as an input (3,243 over the 48 names of the fifteen)."""
    names = _names() if names is None else list(names)
    others = [q for q in names if q != name]
    out = [(name, yz) for yz in itertools.combinations(others, 2)]
    for t in others:
        for z in others:
            if z != t:
                out.append((t, tuple(sorted((name, z)))))
    return out


def _kind(a: dmn.DomainAnswer) -> str:
    if a.answered:
        return "answered"
    return "ambiguous" if len(a.found) > 1 else "refused"


def _pin_row(args) -> Dict[str, Any]:
    target, inputs, phrases = args
    base = dmn.derive_domains(target, inputs)
    row = {"t": target, "inputs": list(inputs), "base": _kind(base),
           "base_formula": base.formula, "pinned": {}}
    for phrase in phrases:
        p = cf.derive_in_context(target, inputs, phrase)
        row["pinned"][phrase] = (_kind(p), p.formula)
    return row


def pin_census(jobs: int = 1, names: Optional[Sequence[str]] = None
               ) -> Dict[str, Any]:
    """X6 (§7.2): every question a pinned name enters, under each of the
    five pin contexts, classified *before → after*; ``changed_count`` the
    answered questions answered differently under a pin, ``resolved`` the
    distinct questions an ambiguity of which some pin resolves."""
    pin_contexts = [c for c in cf.CONTEXTS.values() if c.pin is not None]
    by_name: Dict[str, List[cf.Context]] = {}
    for c in pin_contexts:
        by_name.setdefault(c.pin[0], []).append(c)
    work = []
    for name, ctxs in by_name.items():
        phrases = tuple(c.phrases[0] for c in ctxs)
        work.extend((t, ins, phrases) for t, ins in pin_questions(name, names))
    if jobs > 1:
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            rows = list(pool.map(_pin_row, work, chunksize=64))
    else:
        rows = [_pin_row(w) for w in work]
    per: Dict[str, Dict[str, int]] = {c.key: {} for c in pin_contexts}
    key_of = {c.phrases[0]: c.key for c in pin_contexts}
    changed: List[Dict[str, Any]] = []
    resolved: Dict[Tuple[str, Tuple[str, ...]], Dict[str, str]] = {}
    questions = 0
    for r in rows:
        for phrase, (kind, formula) in r["pinned"].items():
            questions += 1
            if r["base"] == "answered" and kind == "answered":
                cls = ("answered → same answer" if formula == r["base_formula"]
                       else "answered → changed")
                if formula != r["base_formula"]:
                    changed.append({"t": r["t"], "inputs": r["inputs"],
                                    "context": key_of[phrase],
                                    "before": r["base_formula"],
                                    "after": formula})
            else:
                cls = f"{r['base']} → {kind}"
            tally = per[key_of[phrase]]
            tally[cls] = tally.get(cls, 0) + 1
            if r["base"] == "ambiguous" and kind == "answered":
                resolved.setdefault((r["t"], tuple(r["inputs"])), {})[
                    key_of[phrase]] = f"{r['t']} = {formula}"
    return {"questions": questions, "changed_count": len(changed),
            "changed": changed,
            "resolved": [{"t": t, "inputs": list(ins), "answers": ans}
                         for (t, ins), ans in sorted(resolved.items())],
            "per_context": per}


# ===========================================================================
# 3.  X1, X2, X7 AND THE MARKS
# ===========================================================================

def lean_status() -> Dict[str, Any]:
    """X1's reading of ``ContextFrames.lean`` (present, theorems, sorry)."""
    return dmn.lean_check(LEAN_FILE, LEAN_THEOREMS)


def _battery_line(bat: Mapping[str, Any]) -> str:
    if not bat.get("available"):
        return "not available (" + bat.get("reason", "no battery") + ")"
    t = bat["tally"]
    return (f"{t['correct']} correct of {t['answer_cases']}, "
            f"{t['correct_refusals']} correct refusals of {t['refusal_cases']}, "
            f"{t['refused']} refused, {t['wrong']} wrong")


def batteries() -> Dict[str, Any]:
    """The domain battery as written and with *a rotating body drives the
    wave* appended to every question (X2, X7)."""
    plain = dmn.battery()
    rotating = dmn.battery(where=_ROTATING) if plain.get("available") else plain
    moved = None
    if plain.get("available"):
        before = {r["id"]: r["grade"] for r in plain["rows"]}
        moved = sum(1 for r in rotating["rows"] if before.get(r["id"]) != r["grade"])
    return {"plain": plain, "rotating": rotating, "moved": moved}


def _marks(lean: Mapping[str, Any], bats: Mapping[str, Any],
           written: Sequence[Mapping[str, Any]],
           amended: Sequence[Mapping[str, Any]],
           census: Optional[Mapping[str, Any]],
           evaluation: Optional[Mapping[str, Any]]) -> Dict[str, bool]:
    plain = bats["plain"]
    t = plain.get("tally", {})
    x2 = (bool(plain.get("available")) and t.get("correct") == 21
          and t.get("answer_cases") == 23 and t.get("correct_refusals") == 9
          and t.get("refusal_cases") == 9 and t.get("wrong") == 0
          and evaluation is not None and evaluation.get("failed") == 0)
    return {
        "X1": dmn._lean_clean(lean),
        "X2": bool(x2),
        "X3": _passed(written, "x3"),
        "X4": _passed(written, "x4"),
        "X5": _passed(written, "x5"),
        "X6": census is not None and census["questions"] > 0
              and census["changed_count"] == 0,
        "X7": bats.get("moved") == 0,
        "X8": _passed(written, "x8"),
        "X5′": _passed(amended, "x5"),
    }


def _assemble(lean: Mapping[str, Any], bats: Mapping[str, Any],
              written: Sequence[Mapping[str, Any]],
              amended: Sequence[Mapping[str, Any]],
              census: Optional[Mapping[str, Any]],
              evaluation: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    marks = _marks(lean, bats, written, amended, census, evaluation)
    unmeasured = []
    if not lean.get("present"):
        unmeasured.append(f"X1: {LEAN_FILE} is not present")
    if not bats["plain"].get("available"):
        unmeasured.append("X2, X7: " + bats["plain"].get("reason", "no battery"))
    if evaluation is None:
        unmeasured.append("X2: the end-to-end evaluation is not taken here")
    if census is None:
        unmeasured.append("X6: the pin census is not taken")
    return {
        "lean": dict(lean),
        "battery": _battery_line(bats["plain"]),
        "battery_rotating": _battery_line(bats["rotating"]),
        "battery_moved": bats.get("moved"),
        "probes": list(written), "probes_amended": list(amended),
        "census": census if census is not None else {
            "questions": 0, "changed_count": None, "resolved": [],
            "per_context": {}},
        "marks": marks, "met": sum(marks.values()), "taken": len(marks),
        "declared": list(MARKS), "amended": list(AMENDED),
        "unmeasured": unmeasured,
    }


# ===========================================================================
# 4.  THE STANDARD APPARATUS
# ===========================================================================

_SOURCES: Tuple[str, ...] = (
    "engineering/context_frames.py", "engineering/context_frames_study.py",
    "engineering/domains.py", "engineering/speak.py", "engineering/union.py",
    "engineering/wheels.py", "wheels/__init__.py",
    "wheels/junctions/domain.py", "wheels/junctions/phase66.py",
    "evaluation/domain_cases.py",
)

_cache: Optional[Dict[str, Any]] = None


def module_digest() -> str:
    """One digest over the Lean file, the module, the domain wheels, the
    engineering surface and the domain battery; a file that is absent is
    named as absent in the digest."""
    root = _HERE.parent
    paths = [root / n for n in sorted(set(_SOURCES))]
    from .. import constants
    lean = constants.lean_file(LEAN_FILE)
    present = [p for p in paths if p.is_file()]
    absent = [str(p.relative_to(root)) for p in paths if not p.is_file()]
    parts = [integrity.tree_digest(present, root)]
    parts.append(integrity.file_digest(lean) if lean.is_file() else
                 f"absent:{LEAN_FILE}")
    parts.extend(f"absent:{a}" for a in absent)
    return integrity.sha256_hex("\n".join(parts).encode("utf-8"))


def compute(jobs: int = 1, census: bool = True) -> Dict[str, Any]:
    """Take every mark (X6's census about a quarter of an hour on one
    process; ``census=False`` skips it and X6 is missed)."""
    return _assemble(lean_status(), batteries(), probes(False), probes(True),
                     pin_census(jobs=jobs) if census else None)


def measure(jobs: int = 8) -> Dict[str, Any]:
    r = {"measurement": compute(jobs=jobs)}
    r["source_digest"] = module_digest()
    return r


def write_measurements(path: Optional[Path] = None, jobs: int = 8) -> Path:
    """Re-take every mark and store it beside the digest of the code."""
    out = path if path is not None else DATA_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(_plain(measure(jobs=jobs)), indent=1,
                              sort_keys=True, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    global _cache
    _cache = None
    return out


def measurements(refresh: bool = False) -> Optional[Dict[str, Any]]:
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not DATA_PATH.exists():
        _cache = None
        return None
    try:
        _cache = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _cache = None
    return _cache


def state() -> Dict[str, Any]:
    stored = measurements()
    live = module_digest()
    if stored is None:
        return {"present": False, "fresh": False, "verdict": "absent",
                "live_digest": live, "stored_digest": None}
    sd = stored.get("source_digest")
    return {"present": True, "fresh": sd == live,
            "verdict": "current" if sd == live else "stale",
            "live_digest": live, "stored_digest": sd}


def current() -> Optional[Dict[str, Any]]:
    return measurements() if state()["fresh"] else None


def context_frames_report() -> Dict[str, Any]:
    """The stored marks (``available`` True, with ``lean``, ``battery``,
    ``battery_rotating``, ``probes``, ``census``, ``marks``, ``met``,
    ``taken``), or ``available=False`` with the re-take instruction when
    the stored measurement is absent or stale."""
    stored = current()
    if stored is not None:
        out = dict(stored["measurement"])
        out["available"] = True
        out["source_digest"] = stored.get("source_digest")
        return out
    st = state()
    what = "absent" if not st["present"] else "stale (the code moved)"
    return {"available": False,
            "reason": f"the stored measurement is {what}; re-take it with "
                      f"python3 -m glm_universal.tools context-frames --write"}
