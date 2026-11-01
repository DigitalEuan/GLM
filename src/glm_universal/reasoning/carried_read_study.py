"""``glm_universal.reasoning.carried_read_study`` -- the marks of
``studies/CARRIED_READ_STUDY.md`` (Phase 153): the machine reads what it
carries -- the registers as files, the typed planner and the field reads
through GLM-BAT.

*Created 29 October 2026 (as a stub). Last altered 31 October 2026
(repository check: the measurement rebuilt; the stub returned every mark
False under names the study does not use).*

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from studies/CARRIED_READ_STUDY.md
(§§0-7), MASTER_PLAN.md (Phase 153), the handler ``_carried_read`` of
tools.py and tests/README.md.*

What is measured (``--write`` re-takes it; :func:`carried_read_report` reads
the stored measurement when its digest is current)
--------------------------------------------------------------------------
Everything is taken with the switches of the later rounds off
(``fold_machine.ON`` of Phase 160 and ``tool_machine.ON`` of Phase 163), so
the machine is the one this round built.

* **R1** every register table written with unique keys; the snapshot
  reading of the element table agrees with the loaded register on every
  scalar entry.
* **R2** per table, one GLM-BAT program finds every entry with ``FIND``
  (exit 0), and one with every value altered finds none.
* **C1** every chain the stepwise planner answers over the corpus of
  :func:`planner_ladder_study.corpus_texts`, said with reads: halts with
  exit 0, no drift, the gated pipeline promotes.
* **C2**, **C3**, **C4** the last register read, the last question read and
  the last newly computed step (a step computed here that the plain mode of
  Phase 151 carries) of each chain, altered: the first drift is that step,
  nothing is promoted and the seed files are restored.  A question lie that
  is another number of the same question is counted apart (membership, as
  declared).
* **C5** both column-3 scripts of every chain verify and both mutants are
  rejected.
* **T1**, **T2** every answered typed plan of the said kinds over the typed
  planner's six sets is admitted; each whose last step the machine computes,
  with its claim altered, is refused.
* **S1**, **S2** every written register entry asked as ``field <field> of
  <row>`` is answered; each answer from the table asked is read by the
  machine and admitted, and refused with its value altered.
* **F1** the frozen path: every baseline text asked again with the round's
  switches on, the same status and the same answer text.  The answering-path
  gates of this round (``runtime/stepwise.py`` in read mode,
  ``runtime/semantic_plan.ask_planned``, ``runtime/session._solve_field``)
  and the baseline were lost in the October 2026 reorganisation; while the
  gates are absent F1 is reported **not met**, never assumed (comparing two
  runs of an answering path without the gates would show nothing about
  them).
* **L1** (beside the marks, as the study does): ``CarriedRead.lean`` is
  present, states the theorems of §1 and has no ``sorry``; the build itself
  is not run here.

Exactness
---------
Integers, :class:`fractions.Fraction`, strings, booleans.
"""
from __future__ import annotations

import json
import re
from contextlib import contextmanager
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

from .. import integrity

__all__ = [
    "DATA_PATH", "BASELINE_PATH", "_SOURCES", "LEAN_FILE", "LEAN_THEOREMS",
    "compute", "measure", "write_measurements", "measurements", "state",
    "current", "module_digest", "take_baseline", "carried_read_report",
    "registers_part", "chains_part", "typed_part", "fields_part",
    "frozen_part", "gates_present", "find_programs", "later_switches_off",
]

_HERE = Path(__file__).resolve().parent
DATA_PATH = _HERE / "_data" / "carried_read_study.json"
BASELINE_PATH = _HERE / "_data" / "carried_read_baseline.json"

LEAN_FILE: str = "CarriedRead.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "sep_cancel", "line_infix_iff", "find_iff_mem", "find_iff_eq",
    "machine_honest_below", "honest_no_drift", "first_lie_drifts",
    "no_drift_iff",
)

#: The ops the reading mode computes that the plain mode carries.
NEW_OPS: Tuple[str, ...] = ("gcd", "lcm", "parity", "prime", "larger",
                            "comparative", "fold")

_SOURCES: Tuple[str, ...] = (
    "reasoning/carried_read_study.py",
    "reasoning/carried_read.py",
    "reasoning/register_files.py",
    "reasoning/typed_ladder.py",
    "reasoning/planner_ladder.py",
    "reasoning/planner_ladder_study.py",
    "reasoning/fold_machine.py",
    "reasoning/tool_machine.py",
    "reasoning/batch_machine.py",
    "reasoning/batch_speech.py",
    "reasoning/stepwise_script.py",
    "reasoning/typed_plans.py",
    "runtime/stepwise.py",
    "runtime/semantic_plan.py",
    "runtime/session.py",
    "runtime/fields.py",
)

_cache: Optional[Dict[str, object]] = None


def _plain(x: Any) -> Any:
    if isinstance(x, Fraction):
        return str(x)
    if isinstance(x, dict):
        return {str(k): _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


def _session():
    from ..runtime.session import GeometricSession
    return GeometricSession()


@contextmanager
def later_switches_off() -> Iterator[None]:
    """The machine as this round built it: the fold machine (Phase 160) and
    the tool machine (Phase 163) switched off, restored afterwards."""
    from . import fold_machine as fm
    from . import tool_machine as tm
    was = (fm.ON, tm.ON)
    fm.ON, tm.ON = False, False
    try:
        yield
    finally:
        fm.ON, tm.ON = was


# ---------------------------------------------------------------------------
# R1, R2 -- the register files
# ---------------------------------------------------------------------------

_NUM = re.compile(r"^-?\d+(?:/\d+)?$")


def _alter_line(line: str) -> str:
    """``@k=v;`` with its value altered as :func:`typed_ladder.field_lie`
    alters a value."""
    from . import typed_ladder as tl
    key, value = line[:-1].split("=", 1)
    v: object = Fraction(value) if _NUM.match(value) else value
    alt = tl.field_lie(v)
    if isinstance(alt, Fraction):
        alt = str(alt.numerator) if alt.denominator == 1 else \
            f"{alt.numerator}/{alt.denominator}"
    return f"{key}={alt};"


def find_programs(path: str, lines: Tuple[str, ...]
                  ) -> Tuple[List[str], List[str]]:
    """The two R2 programs of one register file: one that finds every entry
    (exit 2 at the first it does not find), one that counts the altered
    entries it finds (exit 1 when any is found)."""
    found = [f"REM R2: every entry of {path} found"]
    found += [f'FIND "{x}" < {path} || EXIT /B 2' for x in lines]
    found.append("EXIT /B 0")
    altered = [f"REM R2: no altered entry of {path} found", "SET /A F=0"]
    altered += [f'FIND "{_alter_line(x)}" < {path} && SET /A F=F+1'
                for x in lines]
    altered += ["IF %F% NEQ 0 EXIT /B 1", "EXIT /B 0"]
    return found, altered


def _run(lines: List[str], files) -> object:
    from . import batch_machine as bm
    return bm.run_program(bm.parse_program(lines), None, files, (),
                          budget=4 * len(lines) + 100, inert=False,
                          jump=False)


def registers_part(session) -> Dict[str, object]:
    from . import register_files as rf
    reg = rf.register_files(session)
    tables: List[Dict[str, object]] = []
    for t in reg["tables"]:
        lines = tuple(reg["files"][t["path"]])
        row = dict(t)
        if lines:
            found, altered = find_programs(t["path"], lines)
            files = {t["path"]: lines}
            a = _run(found, files)
            b = _run(altered, files)
            row["found_exit"] = a.exit_code
            row["altered_exit"] = b.exit_code
            row["all_found"] = (a.status == "halted" and a.exit_code == 0
                                and b.status == "halted"
                                and b.exit_code == 0)
        else:
            row["found_exit"] = row["altered_exit"] = None
            row["all_found"] = False
        tables.append(row)
    return {
        "entries": sum(int(t["entries"]) for t in tables),
        "left_out": sum(int(t["left_out"]) for t in tables),
        "duplicated": sum(int(t["duplicated"]) for t in tables),
        "tables": tables,
        "holding": sum(1 for t in tables if t["entries"]),
        "snapshot": reg["snapshot"],
    }


# ---------------------------------------------------------------------------
# C1-C5 -- the stepwise chains in the reading mode
# ---------------------------------------------------------------------------

def _caught(d: Dict[str, object], k: int) -> bool:
    return d["first_drift"] == k and not d["promoted"] and \
        bool(d["rolled_back"])


def chains_part(session, scripts: bool = True) -> Dict[str, object]:
    from . import carried_read as cr
    from . import planner_ladder as pl
    from . import planner_ladder_study as pls
    chains = pls.answered(session)
    c: Dict[str, object] = {
        "chains": len(chains), "admitted": 0, "computed": 0, "read": 0,
        "read_register": 0, "read_question": 0, "carried": 0, "steps": 0,
        "newly_computed": 0, "lines": 0, "machine_steps": 0,
        "reg_lies": 0, "reg_found": 0, "q_lies": 0, "q_found": 0,
        "q_in_question": 0, "q_in_question_seen": 0, "c_lies": 0,
        "c_found": 0, "carried_lies": 0, "carried_found_at_step": 0,
        "carried_downstream": 0, "carried_unseen": 0,
    }
    carried_ops: Dict[str, int] = {}
    failures: List[str] = []
    lie_failures: List[str] = []
    items = []
    for text, chain in chains:
        seed = cr.seed_files(chain, session)
        r = pl.check_chain(chain, say=False, read=True, files=seed,
                           ladder=True)
        base = pl.check_chain(chain, say=False, read=False)
        c["steps"] += len(chain.steps)
        c["admitted"] += r["admitted"]
        c["computed"] += len(r["computed"])
        c["read_register"] += len(r["read_register"])
        c["read_question"] += len(r["read_question"])
        c["read"] += len(r["read_register"]) + len(r["read_question"])
        c["carried"] += len(r["carried"])
        c["lines"] += r["lines"]
        c["machine_steps"] += r["machine_steps"]
        for k in r["carried"]:
            op = chain.steps[k - 1].op
            carried_ops[op] = carried_ops.get(op, 0) + 1
        newly = [k for k in r["computed"] if k not in base["computed"]
                 and chain.steps[k - 1].op in NEW_OPS]
        c["newly_computed"] += len(newly)
        if not r["admitted"]:
            failures.append(text)
        if r["ladder"].run is not None:
            items.append((chain, r["ladder"]))

        def lie_at(k: int, value: object) -> Dict[str, object]:
            return pl.check_chain(pl.lie_chain(chain, k, value), say=False,
                                  read=True, files=seed)

        # C2: the last register read
        if r["read_register"]:
            k = r["read_register"][-1]
            lie = pl.value_lie(chain.steps[k - 1])
            if lie is not None:
                c["reg_lies"] += 1
                ok = _caught(lie_at(k, lie), k)
                c["reg_found"] += ok
                if not ok:
                    lie_failures.append(f"C2 {text}")
        # C3: the last question read
        if r["read_question"]:
            k = r["read_question"][-1]
            lie = chain.steps[k - 1].value + 1
            c["q_lies"] += 1
            ok = _caught(lie_at(k, lie), k)
            if lie in cr.question_numbers(chain.question):
                c["q_in_question"] += 1
                c["q_in_question_seen"] += ok
            else:
                c["q_found"] += ok
                if not ok:
                    lie_failures.append(f"C3 {text}")
        # C4: the last newly computed step
        if newly:
            k = newly[-1]
            lie = pl.value_lie(chain.steps[k - 1])
            if lie is not None:
                c["c_lies"] += 1
                ok = _caught(lie_at(k, lie), k)
                c["c_found"] += ok
                if not ok:
                    lie_failures.append(f"C4 {text}")
        # §7.2 post hoc: the last numeric carried step raised by one
        nums = [k for k in r["carried"]
                if isinstance(chain.steps[k - 1].value, Fraction)]
        if nums:
            k = nums[-1]
            c["carried_lies"] += 1
            d = lie_at(k, chain.steps[k - 1].value + 1)
            if d["first_drift"] == k:
                c["carried_found_at_step"] += 1
            elif d["drift"]:
                c["carried_downstream"] += 1
            else:
                c["carried_unseen"] += 1
    c["carried_ops"] = dict(sorted(carried_ops.items()))
    c["failures"] = failures
    c["lie_failures"] = lie_failures
    c["max_lines"] = max((len(lad.lines) for _c, lad in items), default=0)
    if scripts:
        c.update(pls.column3_counts(items))
    else:
        c.update({"scripts_run": 0, "scripts_pipeline": 0, "mutants": 0,
                  "mutants_rejected": 0})
    return c


# ---------------------------------------------------------------------------
# T1, T2 -- the typed planner
# ---------------------------------------------------------------------------

def typed_part(session) -> Dict[str, object]:
    from . import planner_ladder as pl
    from . import typed_ladder as tl
    from . import typed_plans
    from ..runtime import semantic_plan as sp
    t: Dict[str, object] = {"texts": 0, "answered": 0, "said": 0,
                            "admitted": 0, "lies": 0, "refused": 0,
                            "carried_last": 0}
    by_kind: Dict[str, int] = {}
    failures: List[str] = []
    for _name, items in typed_plans.sets().items():
        for item in items:
            t["texts"] += 1
            planned = sp.plan_question(session, item.question)
            if planned.verdict == "answered":
                t["answered"] += 1
            r = tl.plan_check(planned)
            if r is None:
                continue
            kind = str(planned.chosen.plan.compute)
            by_kind[kind] = by_kind.get(kind, 0) + 1
            t["said"] += 1
            t["admitted"] += r["admitted"]
            if not r["admitted"]:
                failures.append(item.question)
            if not r["last_computed"]:
                t["carried_last"] += 1
                continue
            lie = tl.typed_lie(r["chain"])
            if lie is None:
                continue
            t["lies"] += 1
            d = pl.check_chain(lie, say=False, read=True)
            t["refused"] += not d["admitted"]
            if d["admitted"]:
                failures.append(f"lie: {item.question}")
    t["by_kind"] = dict(sorted(by_kind.items()))
    t["failures"] = failures
    return t


# ---------------------------------------------------------------------------
# S1, S2 -- the field answers
# ---------------------------------------------------------------------------

def fields_part(session) -> Dict[str, object]:
    from . import register_files as rf
    from . import typed_ladder as tl
    files = rf.register_files(session)["files"]
    surface = session.field_surface
    f: Dict[str, object] = {"asked": 0, "answered": 0, "read": 0,
                            "admitted": 0, "lies": 0, "refused": 0}
    other: Dict[str, int] = {}
    failures: List[str] = []
    for t in rf.register_tables(surface):
        rows = rf.snapshot_element_rows() if t.name == "element" \
            else t.rows()
        for row in rows:
            for name, value in rows[row].items():
                if value is None or \
                        rf.entry_line(str(row), str(name), value) is None:
                    continue
                f["asked"] += 1
                sol = session.ask(f"field {name} of {row}")
                if not sol.ok:
                    failures.append(f"unanswered: {name} of {row}")
                    continue
                f["answered"] += 1
                held = surface.field(str(name), str(row))
                if held.table != t.name:
                    key = f"{t.name} -> {held.table}"
                    other[key] = other.get(key, 0) + 1
                    continue
                r = tl.field_check(held, files=files)
                if r is None:
                    failures.append(f"not read: {name} of {row}")
                    continue
                f["read"] += 1
                f["admitted"] += r["admitted"]
                if not r["admitted"]:
                    failures.append(f"refused: {name} of {row}")
                f["lies"] += 1
                d = tl.field_check(held, files=files,
                                   value=tl.field_lie(held.value))
                f["refused"] += not d["admitted"]
                if d["admitted"]:
                    failures.append(f"lie admitted: {name} of {row}")
    f["answered_by_other_table"] = dict(sorted(other.items()))
    f["failures"] = failures[:50]
    return f


# ---------------------------------------------------------------------------
# F1 -- the frozen path
# ---------------------------------------------------------------------------

def gates_present() -> Dict[str, bool]:
    """Whether this round's three answering-path gates are in the code: the
    stepwise gate in read mode, the typed planner's gate in ``ask_planned``
    and the field gate in ``_solve_field``."""
    root = _HERE.parent / "runtime"

    def text(name: str) -> str:
        p = root / name
        return p.read_text(encoding="utf-8") if p.exists() else ""

    sw = text("stepwise.py")
    return {
        "stepwise": "_ladder_gate" in sw and "READ" in sw,
        "semantic_plan": "typed_ladder" in text("semantic_plan.py"),
        "session": "typed_ladder" in text("session.py"),
    }


@contextmanager
def _round_switches(on: bool) -> Iterator[None]:
    from . import typed_ladder as tl
    from ..runtime import stepwise as sw
    was = (tl.ON, getattr(sw, "READ", None))
    tl.ON = on
    if hasattr(sw, "READ"):
        sw.READ = on
    try:
        yield
    finally:
        tl.ON = was[0]
        if was[1] is not None:
            sw.READ = was[1]


def frozen_texts() -> List[Tuple[str, str, str]]:
    """``(set, id, text)``: the stepwise texts (through the router), the
    typed planner's six sets (through ``ask_planned``) and the evaluation's
    cases (through ``ask``)."""
    from . import planner_ladder_study as pls
    from . import typed_plans
    from ..evaluation import cases as ev
    out: List[Tuple[str, str, str]] = []
    for i, (_src, text) in enumerate(pls.corpus_texts()):
        out.append(("stepwise", f"s{i}", text))
    for name, items in typed_plans.sets().items():
        for item in items:
            out.append((f"typed:{name}", str(item.key), item.question))
    for case in ev.CASES:
        out.append(("evaluation", str(case.id), case.question))
    return out


def _ask_all(session) -> List[Dict[str, object]]:
    from ..runtime import semantic_plan as sp
    rows = []
    for which, key, text in frozen_texts():
        if which.startswith("typed:"):
            sol = sp.ask_planned(session, text)
        else:
            sol = session.ask(text)
        rows.append({"set": which, "id": key, "text": text,
                     "ok": bool(sol.ok), "answer": str(sol.answer)})
    return rows


def take_baseline() -> Path:
    """Ask every frozen text with the round's switches off and store the
    answers in :data:`BASELINE_PATH` (about 17 minutes).  Take it just
    before the gates go into the answering path, so that F1 compares the
    gates and nothing else."""
    session = _session()
    with _round_switches(False):
        rows = _ask_all(session)
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text(json.dumps(
        {"before": rows, "gates_present": gates_present(),
         "note": "taken with typed_ladder.ON (and stepwise.READ, where "
                 "present) off"},
        indent=1, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8")
    return BASELINE_PATH


def frozen_part(session) -> Dict[str, object]:
    gates = gates_present()
    out: Dict[str, object] = {"texts": 0, "same_status": 0, "same_text": 0,
                              "baseline": BASELINE_PATH.exists(),
                              "gates": gates, "measured": False}
    if not all(gates.values()):
        out["note"] = ("F1 not measured: the answering-path gates of this "
                       "round are absent (" + ", ".join(
                           k for k, v in gates.items() if not v) +
                       "), so no answer passes through the machine; "
                       "a comparison would show nothing about them")
        return out
    if not BASELINE_PATH.exists():
        out["note"] = ("F1 not measured: the baseline "
                       "(reasoning/_data/carried_read_baseline.json) is "
                       "absent; take it with the gates switched off")
        return out
    before = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))["before"]
    with _round_switches(True):
        now = {(r["set"], r["id"]): r for r in _ask_all(session)}
    moved = []
    for b in before:
        r = now.get((b["set"], b["id"]))
        out["texts"] += 1
        if r is None:
            moved.append(b["id"])
            continue
        out["same_status"] += r["ok"] == b["ok"]
        same = r["answer"] == b["answer"]
        out["same_text"] += same
        if not same:
            moved.append(b["id"])
    out["moved"] = moved
    out["measured"] = True
    return out


# ---------------------------------------------------------------------------
# the measurement
# ---------------------------------------------------------------------------

def compute(scripts: bool = True) -> Dict[str, object]:
    from . import planner_ladder_study as pls
    session = _session()
    with later_switches_off():
        registers = registers_part(session)
        chains = chains_part(session, scripts)
        typed = typed_part(session)
        fields = fields_part(session)
    frozen = frozen_part(session)
    r, c, t, f = registers, chains, typed, fields
    n = c["chains"]
    snap = r["snapshot"]
    marks = {
        "R1": r["entries"] > 0 and r["duplicated"] == 0
        and snap["pairs"] > 0 and snap["agree"] == snap["pairs"],
        "R2": r["holding"] > 0 and sum(1 for x in r["tables"]
                                       if x["all_found"]) == r["holding"],
        "C1": n > 0 and c["admitted"] == n,
        "C2": c["reg_lies"] > 0 and c["reg_found"] == c["reg_lies"],
        "C3": c["q_lies"] > c["q_in_question"]
        and c["q_found"] == c["q_lies"] - c["q_in_question"],
        "C4": c["c_lies"] > 0 and c["c_found"] == c["c_lies"],
        "C5": bool(scripts) and c["scripts_run"] == n
        and c["scripts_pipeline"] == n
        and c["mutants_rejected"] == c["mutants"],
        "T1": t["said"] > 0 and t["admitted"] == t["said"],
        "T2": t["lies"] > 0 and t["refused"] == t["lies"],
        "S1": f["asked"] > 0 and f["answered"] == f["asked"]
        and f["read"] > 0 and f["admitted"] == f["read"],
        "S2": f["lies"] > 0 and f["refused"] == f["lies"],
        "F1": bool(frozen["measured"]) and frozen["texts"] > 0
        and frozen["same_status"] == frozen["texts"]
        and frozen["same_text"] == frozen["texts"],
    }
    return {
        "registers": registers,
        "chains": chains,
        "typed": typed,
        "fields": fields,
        "frozen": frozen,
        "corpus": {"texts": len(pls.corpus_texts()), "chains": n},
        "lean": pls.lean_marks(LEAN_FILE, LEAN_THEOREMS),
        "switches": "fold_machine.ON and tool_machine.ON off",
        "marks": marks,
        "met": sum(1 for v in marks.values() if v),
        "taken": len(marks),
    }


def module_digest() -> str:
    root = _HERE.parent
    paths = [root / n for n in sorted(set(_SOURCES))]
    return integrity.tree_digest(paths, root)


def measure() -> Dict[str, object]:
    r = compute()
    r["source_digest"] = module_digest()
    return r


def write_measurements(path: Optional[Path] = None) -> Path:
    out = path if path is not None else DATA_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(_plain(measure()), indent=1, sort_keys=True,
                      ensure_ascii=False) + "\n"
    out.write_text(text, encoding="utf-8")
    global _cache
    _cache = None
    return out


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not DATA_PATH.exists():
        return None
    try:
        _cache = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _cache = None
    return _cache


def state() -> Dict[str, object]:
    stored = measurements()
    live = module_digest()
    if stored is None:
        return {"present": False, "fresh": False, "verdict": "absent",
                "live_digest": live, "stored_digest": None}
    stored_digest = stored.get("source_digest")
    return {"present": True, "fresh": stored_digest == live,
            "verdict": "current" if stored_digest == live else "stale",
            "live_digest": live, "stored_digest": stored_digest}


def current() -> Optional[Dict[str, object]]:
    if state()["fresh"]:
        return measurements()
    return None


def carried_read_report() -> Dict[str, object]:
    stored = current()
    if stored is not None:
        out = dict(stored)
        out["available"] = True
        return out
    return {
        "available": False,
        "reason": ("the stored measurement is absent or stale; re-take it "
                   "with python3 -m glm_universal.tools carried-read "
                   "--write"),
    }
