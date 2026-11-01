"""``glm_universal.reasoning.fold_machine_study`` -- the marks of
``studies/FOLD_MACHINE_STUDY.md`` (Phase 160): the machine sorts -- order
folds, ranks, top rows and hole bounds computed in GLM-BAT.

*Created 31 October 2026.*

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from MASTER_PLAN.md (Phase 160),
studies/FOLD_MACHINE_STUDY.md (itself reconstructed on 31 October 2026), the
handler ``_fold_machine`` of tools.py and the row of tests/README.md for
test_fold_machine.py.  The marks' exact thresholds were not recorded; the
ones below are this reconstruction's, declared here before the measurement.*

What is measured (``--write`` re-takes it; :func:`fold_machine_report` reads
the stored measurement when its digest is current)
--------------------------------------------------------------------------
The chains are those of :func:`planner_ladder_study.answered`, run in the
reading mode with the tool machine of Phase 163 off; the fold switch
(``fold_machine.ON``) is the variable.

* **M1** with the switch off the folds are carried as Phase 153 carried
  them; with it on no fold is carried.  Reported: folds carried off -> on,
  carried steps off -> on, the newly computed folds by function.
* **M2** every chain admitted with the switch on, and said as English that
  reads back to the identical lines.
* **M3** a lie at each newly computed fold (a number raised by one, the
  upper end of a bound raised by one, the top rows reordered or swapped)
  found at its own step, nothing promoted, the seed restored.
* **M4** a declared hole of each newly computed fold given a reading in the
  register: the run stops before the fold is written.  (M4' is the same mark
  on the amended machine -- impossible shapes stop it; the first
  measurement, at which M4 was missed, was lost, so ``first`` is absent and
  both are measured on the machine as it now stands.)
* **M5** every newly computed fold that offers a witness, with the witnesses
  rotated (``fold_machine.WITNESS_SHIFT = 1``): each run stops, or writes
  the same value (a tied witness); none writes a wrong value.
* **M6** both column-3 scripts of every chain with a newly computed fold
  verify and both mutants are rejected.
* **K1** a synthetic control of :data:`SYNTHETIC` columns drawn by a declared
  linear congruential generator (:class:`Lcg`), ties and holes common: every
  column the planner's own fold rule (``stepwise_script.fold_value``,
  ``top_rows``) answers is admitted and its lie refused; every column it
  refuses (a hole leaving a side open, a position past the column, a tie
  across the top's boundary), given the naive claim, leaves the fold
  unwritten.
* **P1** the largest program halts within ``planner_ladder.BUDGET`` machine
  steps and has fewer lines than the all-pairs version of the round
  (43,346).
* **F1** the frozen path against the baseline taken with the switch off.
  The answering-path gate (``runtime/stepwise.py``: ``_ladder_gate`` in the
  reading mode) and the baseline were lost in the October 2026
  reorganisation; while the gate is absent F1 is reported **not met**,
  never assumed.
* **L1** (beside the marks): ``FoldMachine.lean`` present with the theorems
  of the study and no ``sorry`` (not met while the file is absent).

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
    "DATA_PATH", "FIRST_PATH", "BASELINE_PATH", "_SOURCES", "SYNTHETIC",
    "SEED", "ALL_PAIRS_LINES", "Lcg", "compute", "measure",
    "write_measurements", "measurements", "state", "current",
    "module_digest", "take_baseline", "fold_machine_report", "fold_lie",
    "synthetic_column", "synthetic_chain", "synthetic_part", "chains_part",
    "switches",
]

_HERE = Path(__file__).resolve().parent
DATA_PATH = _HERE / "_data" / "fold_machine_study.json"
FIRST_PATH = _HERE / "_data" / "fold_machine_study_first.json"
BASELINE_PATH = _HERE / "_data" / "fold_machine_baseline.json"

#: Columns of the synthetic control.
SYNTHETIC: int = 3000

#: The generator's declared seed.
SEED: int = 160

#: The lines of the all-pairs version of the round (the study, §1).
ALL_PAIRS_LINES: int = 43346

_SOURCES: Tuple[str, ...] = (
    "reasoning/fold_machine_study.py",
    "reasoning/fold_machine.py",
    "reasoning/planner_ladder.py",
    "reasoning/planner_ladder_study.py",
    "reasoning/carried_read.py",
    "reasoning/register_files.py",
    "reasoning/tool_machine.py",
    "reasoning/batch_machine.py",
    "reasoning/batch_speech.py",
    "reasoning/stepwise_script.py",
    "runtime/stepwise.py",
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
def switches(fold: bool, tool: bool = False,
             shift: int = 0) -> Iterator[None]:
    """The fold switch, the tool switch (Phase 163) and the witness shift,
    restored afterwards."""
    from . import fold_machine as fm
    from . import tool_machine as tm
    was = (fm.ON, tm.ON, fm.WITNESS_SHIFT)
    fm.ON, tm.ON, fm.WITNESS_SHIFT = fold, tool, shift
    try:
        yield
    finally:
        fm.ON, tm.ON, fm.WITNESS_SHIFT = was


# ---------------------------------------------------------------------------
# lies
# ---------------------------------------------------------------------------

_BETWEEN = re.compile(r"^between (\S+) and (\S+)$")


def fold_lie(step) -> Optional[object]:
    """A fold's claim altered: a number raised by one; ``between a and b``
    with ``b`` raised by one; the top rows with the first two swapped, or
    (one row) the row named after it.  ``None`` when there is none."""
    from .stepwise_script import render_value
    v = step.value
    if isinstance(v, Fraction):
        return v + 1
    text = str(v)
    m = _BETWEEN.match(text)
    if m:
        return f"between {m.group(1)} and " \
               f"{render_value(Fraction(m.group(2)) + 1)}"
    if step.detail.get("fn") == "top":
        rows = [x.strip() for x in text.split(",")]
        if len(rows) >= 2:
            return ", ".join([rows[1], rows[0]] + rows[2:])
        names = step.detail.get("names")
        if isinstance(names, dict):
            other = [str(n) for n in names.values() if str(n) != text]
            if other:
                return other[0]
    return None


# ---------------------------------------------------------------------------
# M1-M6, P1 -- the chains
# ---------------------------------------------------------------------------

def _fold_steps(chain) -> List[int]:
    return [s.index for s in chain.steps if s.op == "fold"]


def _uses_witness(step) -> bool:
    from .stepwise_script import is_order
    fn = str(step.detail.get("fn"))
    return fn == "top" or (is_order(fn) and fn != "rank")


def _hole_files(chain, k: int, seed) -> Optional[Dict[str, Tuple[str, ...]]]:
    """The seed with a reading given to the first declared hole of fold
    ``k`` (its value the fold's first reading), or ``None``."""
    from . import register_files as rf
    s = chain.steps[k - 1]
    d = s.detail
    missing = list(d.get("missing") or ())
    if not missing or not s.inputs:
        return None
    path = rf.table_path(str(d.get("table")))
    if path not in seed:
        return None
    first = chain.steps[int(s.inputs[0]) - 1].value
    line = rf.entry_line(str(missing[0]), str(d.get("field")), first)
    if line is None:
        return None
    out = dict(seed)
    out[path] = tuple(seed[path]) + (line,)
    return out


def chains_part(session, scripts: bool = True) -> Dict[str, object]:
    from . import carried_read as cr
    from . import planner_ladder as pl
    from . import planner_ladder_study as pls
    chains = pls.answered(session)
    c: Dict[str, object] = {
        "chains": len(chains), "admitted": 0, "said": 0, "read_back": 0,
        "folds": 0, "folds_carried_off": 0, "folds_carried_on": 0,
        "carried_off": 0, "carried_on": 0, "folds_newly_computed": 0,
        "lies": 0, "lies_found": 0, "hole_lies": 0, "hole_lies_stopped": 0,
        "witness_runs": 0, "witness_stopped": 0, "witness_same": 0,
        "witness_wrong": 0, "max_lines": 0, "max_steps": 0,
        "max_question": "",
    }
    by_fn: Dict[str, int] = {}
    failures: List[str] = []
    items = []
    for text, chain in chains:
        seed = cr.seed_files(chain, session)
        with switches(False):
            off = pl.check_chain(chain, say=False, read=True, files=seed)
        with switches(True):
            on = pl.check_chain(chain, say=True, read=True, files=seed,
                                ladder=True)
        folds = _fold_steps(chain)
        c["folds"] += len(folds)
        c["folds_carried_off"] += sum(1 for k in folds if k in off["carried"])
        c["folds_carried_on"] += sum(1 for k in folds if k in on["carried"])
        c["carried_off"] += len(off["carried"])
        c["carried_on"] += len(on["carried"])
        c["said"] += 1
        c["read_back"] += bool(on["said"])
        c["admitted"] += on["admitted"]
        if not (on["admitted"] and on["said"]):
            failures.append(text)
        lad = on["ladder"]
        if on["lines"] > c["max_lines"]:
            c["max_lines"] = on["lines"]
            c["max_question"] = text
        c["max_steps"] = max(c["max_steps"], on["machine_steps"])
        newly = [k for k in folds if k in off["carried"]
                 and k in on["computed"]]
        if not newly:
            continue
        c["folds_newly_computed"] += len(newly)
        for k in newly:
            fn = str(chain.steps[k - 1].detail.get("fn"))
            fn = re.sub(r":\d+$", ":k", fn)
            by_fn[fn] = by_fn.get(fn, 0) + 1
        if lad.run is not None:
            items.append((chain, lad))
        with switches(True):
            for k in newly:
                step = chain.steps[k - 1]
                lie = fold_lie(step)
                if lie is not None:
                    c["lies"] += 1
                    d = pl.check_chain(pl.lie_chain(chain, k, lie),
                                       say=False, read=True, files=seed)
                    ok = d["first_drift"] == k and not d["promoted"] and \
                        bool(d["rolled_back"])
                    c["lies_found"] += ok
                    if not ok:
                        failures.append(f"M3 {text}")
                holed = _hole_files(chain, k, seed)
                if holed is not None:
                    c["hole_lies"] += 1
                    d = pl.check_chain(chain, say=False, read=True,
                                       files=holed)
                    ok = d["first_drift"] == k and not d["promoted"]
                    c["hole_lies_stopped"] += ok
                    if not ok:
                        failures.append(f"M4 {text}")
        witnessed = [k for k in newly if _uses_witness(chain.steps[k - 1])]
        if witnessed:
            c["witness_runs"] += 1
            with switches(True, shift=1):
                d = pl.check_chain(chain, say=False, read=True, files=seed,
                                   ladder=True)
            run = d["ladder"].run
            written = run.files if run is not None else {}
            want = d["ladder"].desired
            wrong = [k for k in witnessed
                     if pl.file_of(k) in written
                     and tuple(written[pl.file_of(k)]) !=
                     tuple(want[pl.file_of(k)])]
            same = all(pl.file_of(k) in written for k in witnessed)
            if wrong:
                c["witness_wrong"] += 1
                failures.append(f"M5 {text}")
            elif same:
                c["witness_same"] += 1
            else:
                c["witness_stopped"] += 1
    c["by_fn"] = dict(sorted(by_fn.items()))
    c["failures"] = failures
    if scripts:
        cols = pls.column3_counts(items)
        c["scripts"] = len(items)
        c["scripts_ok"] = len(items) - len(cols["script_failures"])
        c["mutants"] = cols["mutants"]
        c["mutants_rejected"] = cols["mutants_rejected"]
        c["script_failures"] = cols["script_failures"]
    else:
        c.update({"scripts": 0, "scripts_ok": 0, "mutants": 0,
                  "mutants_rejected": 0})
    return c


# ---------------------------------------------------------------------------
# K1 -- the synthetic control
# ---------------------------------------------------------------------------

class Lcg:
    """The declared generator: ``x <- (1103515245 x + 12345) mod 2^31``,
    an output the high bits reduced modulo ``n``.  Exact and reproducible;
    no ``random``."""

    def __init__(self, seed: int) -> None:
        self.x = (seed * 2654435761 + 97) % (2 ** 31)

    def next(self, n: int) -> int:
        self.x = (1103515245 * self.x + 12345) % (2 ** 31)
        return (self.x >> 8) % n


_ORDER_FNS: Tuple[str, ...] = ("median", "q1", "q3", "max", "min", "max:k",
                               "min:k", "rank", "top")


def synthetic_column(rng: Lcg) -> Dict[str, object]:
    """One column: readings (ties common, a half now and then), holes, a
    fold and its shape (exact, over the present rows, bounded, bounds)."""
    n = 1 + rng.next(7)
    span = 2 + rng.next(8)
    vals = []
    for _ in range(n):
        v = Fraction(rng.next(span) - 2)
        if rng.next(6) == 0:
            v += Fraction(1, 2)
        vals.append(v)
    holes = rng.next(4) if rng.next(2) else 0
    shape = ("present", "bounded", "bounds")[rng.next(3)] \
        if holes else "exact"
    if shape == "bounds":
        fn = ("sum", "mean", "odd", "even")[rng.next(4)]
        if fn in ("odd", "even"):
            vals = [Fraction(v.numerator // v.denominator) for v in vals]
    elif shape == "present" and rng.next(3) == 0:
        fn = ("sum", "mean", "odd", "even")[rng.next(4)]
        if fn in ("odd", "even"):
            vals = [Fraction(v.numerator // v.denominator) for v in vals]
    else:
        fn = _ORDER_FNS[rng.next(len(_ORDER_FNS))]
        if shape == "bounded" and fn == "top":
            shape = "present"
    if fn in ("max:k", "min:k"):
        fn = fn[:4] + str(1 + rng.next(n + holes + 1))
    k = 1 + rng.next(n + 1)
    return {"vals": vals, "holes": holes, "shape": shape, "fn": fn,
            "k": k, "symbol": ">" if rng.next(2) else "<",
            "rank_row": rng.next(n),
            "range": (Fraction(-2), Fraction(span))}


def _planner(col: Dict[str, object]) -> Optional[object]:
    """The planner's own fold rule on the column, or ``None`` (refused)."""
    from . import stepwise_script as ss
    vals = list(col["vals"])
    fn = str(col["fn"])
    shape = col["shape"]
    holes = int(col["holes"]) if shape in ("bounded", "bounds") else 0
    if fn == "top":
        order = ss.top_rows([(v, f"r{i}") for i, v in enumerate(vals)],
                            int(col["k"]), str(col["symbol"]))
        return None if order is None else \
            ", ".join(f"row {r[1:]}" for r in order)
    if fn not in ("median", "max", "min", "rank", "sum", "mean", "odd",
                  "even") and ss.order_positions(fn, len(vals) + holes) \
            is None:
        return None
    x = vals[int(col["rank_row"])] if fn == "rank" else None
    if shape == "bounds":
        use = col["range"] if (holes and fn in ("sum", "mean")) else None
        return ss.fold_value(fn, vals, holes, rng=use, bounds=True)
    return ss.fold_value(fn, vals, holes, x)


def _naive(col: Dict[str, object]) -> object:
    """The claim given to the machine where the planner refuses: the fold
    over the present readings as if there were no hole (the top rows as
    first sorted), else 0."""
    from . import stepwise_script as ss
    vals = list(col["vals"])
    fn = str(col["fn"])
    if fn == "top":
        ranked = sorted(range(len(vals)), key=lambda i: vals[i],
                        reverse=(col["symbol"] == ">"))
        return ", ".join(f"row {i}" for i in ranked[:int(col["k"])])
    x = vals[int(col["rank_row"])] if fn == "rank" else None
    v = ss.fold_value(fn, vals, 0, x)
    return Fraction(0) if v is None else v


def synthetic_chain(col: Dict[str, object], claim: object
                    ) -> Tuple[object, Dict[str, Tuple[str, ...]]]:
    """The column as a chain (one lookup per present row, then the fold
    claiming ``claim``) and its seed files (``reg/synthetic.txt``)."""
    from . import register_files as rf
    from .stepwise_script import Chain, Step, render_value
    vals = list(col["vals"])
    n, holes, shape = len(vals), int(col["holes"]), col["shape"]
    steps: List[object] = []
    lines = []
    for i, v in enumerate(vals):
        lines.append(rf.entry_line(f"r{i}", "f", v))
        steps.append(Step(i + 1, "lookup", (), v, f"the f of row {i}",
                          {"table": "synthetic", "row": f"r{i}",
                           "field": "f", "question": f"what is f of r{i}"}))
    missing = [f"h{j}" for j in range(holes)]
    detail: Dict[str, object] = {
        "fn": col["fn"], "set": "synthetic", "field": "f",
        "table": "synthetic", "present": shape == "present",
        "bounded": bool(missing) and shape in ("bounded", "bounds"),
        "missing": missing}
    if shape == "bounds":
        detail["bounds"] = True
        if missing and col["fn"] in ("sum", "mean"):
            detail["range"] = [render_value(col["range"][0]),
                               render_value(col["range"][1])]
    if col["fn"] == "rank":
        detail["row"] = f"r{col['rank_row']}"
    if col["fn"] == "top":
        detail.update({"k": col["k"], "symbol": col["symbol"],
                       "word": "top", "bounded": False,
                       "names": {f"r{i}": f"row {i}" for i in range(n)}})
    steps.append(Step(n + 1, "fold", tuple(range(1, n + 1)), claim,
                      f"{col['fn']} over the synthetic column", detail))
    files = {rf.table_path("synthetic"): tuple(lines), "q.txt": ()}
    return Chain("a synthetic column", tuple(steps), "synthetic"), files


def synthetic_part(count: int = SYNTHETIC, seed: int = SEED
                   ) -> Dict[str, object]:
    from . import planner_ladder as pl
    rng = Lcg(seed)
    k: Dict[str, object] = {"columns": count, "answered": 0, "admitted": 0,
                            "lies": 0, "lies_refused": 0,
                            "refused_by_planner": 0, "machine_silent": 0,
                            "with_ties": 0, "with_holes": 0, "carried": 0}
    failures: List[Dict[str, object]] = []
    with switches(True):
        for _ in range(count):
            col = synthetic_column(rng)
            vals = list(col["vals"])
            k["with_ties"] += len(set(vals)) < len(vals)
            k["with_holes"] += int(col["holes"]) > 0
            value = _planner(col)
            last = len(vals) + 1
            if value is None:
                k["refused_by_planner"] += 1
                chain, files = synthetic_chain(col, _naive(col))
                d = pl.check_chain(chain, say=False, read=True, files=files,
                                   ladder=True)
                run = d["ladder"].run
                written = run is not None and pl.file_of(last) in run.files
                k["machine_silent"] += not written and \
                    last not in d["carried"]
                if written or last in d["carried"]:
                    failures.append({"refused": _plain(col)})
                continue
            k["answered"] += 1
            chain, files = synthetic_chain(col, value)
            d = pl.check_chain(chain, say=False, read=True, files=files)
            k["carried"] += last in d["carried"]
            ok = d["admitted"] and last in d["computed"]
            k["admitted"] += ok
            if not ok:
                failures.append({"answered": _plain(col),
                                 "value": _plain(value)})
            lie = fold_lie(chain.steps[-1])
            if lie is None:
                continue
            k["lies"] += 1
            e = pl.check_chain(pl.lie_chain(chain, last, lie), say=False,
                               read=True, files=files)
            k["lies_refused"] += not e["admitted"]
            if e["admitted"]:
                failures.append({"lie": _plain(col), "value": _plain(lie)})
    k["failures"] = failures[:20]
    return k


# ---------------------------------------------------------------------------
# F1 -- the frozen path
# ---------------------------------------------------------------------------

def gate_present() -> bool:
    """Whether the stepwise answering path runs its chains through the
    machine (``_ladder_gate`` in ``runtime/stepwise.py``)."""
    p = _HERE.parent / "runtime" / "stepwise.py"
    return p.exists() and "_ladder_gate" in p.read_text(encoding="utf-8")


def take_baseline() -> Path:
    """Ask every recorded text (the stepwise texts and the evaluation's
    cases) with the fold switch off and store the answers in
    :data:`BASELINE_PATH`.  Take it just before the gate goes back into the
    answering path, so that F1 compares the switch and nothing else."""
    from . import planner_ladder_study as pls
    from ..evaluation import cases as ev
    session = _session()
    rows = []
    with switches(False):
        texts = [("stepwise", f"s{i}", t)
                 for i, (_s, t) in enumerate(pls.corpus_texts())]
        texts += [("evaluation", str(c.id), c.question) for c in ev.CASES]
        for which, key, text in texts:
            sol = session.ask(text)
            rows.append({"set": which, "id": key, "text": text,
                         "ok": bool(sol.ok), "answer": str(sol.answer)})
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text(json.dumps(
        {"before": rows, "gate_present": gate_present(),
         "note": "taken with fold_machine.ON off"},
        indent=1, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8")
    return BASELINE_PATH


def frozen_part(session) -> Dict[str, object]:
    out: Dict[str, object] = {"texts": 0, "same_status": 0, "same_text": 0,
                              "baseline": BASELINE_PATH.exists(),
                              "gate": gate_present(), "measured": False}
    if not out["gate"]:
        out["note"] = ("F1 not measured: the stepwise answering path does "
                       "not run its chains through the machine "
                       "(runtime/stepwise.py has no _ladder_gate), so the "
                       "fold switch moves no answer and a comparison would "
                       "show nothing about it")
        return out
    if not out["baseline"]:
        out["note"] = ("F1 not measured: the baseline "
                       "(reasoning/_data/fold_machine_baseline.json) is "
                       "absent; take it with the switch off")
        return out
    before = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))["before"]
    moved = []
    with switches(True):
        for b in before:
            sol = session.ask(b["text"])
            out["texts"] += 1
            out["same_status"] += bool(sol.ok) == b["ok"]
            same = str(sol.answer) == b["answer"]
            out["same_text"] += same
            if not same:
                moved.append(b["id"])
    out["moved"] = moved
    out["measured"] = True
    return out


# ---------------------------------------------------------------------------
# the measurement
# ---------------------------------------------------------------------------

def compute(scripts: bool = True,
            synthetic: int = SYNTHETIC) -> Dict[str, object]:
    from . import planner_ladder as pl
    from . import planner_ladder_study as pls
    from . import fold_machine as fm
    session = _session()
    c = chains_part(session, scripts)
    k = synthetic_part(synthetic)
    f = frozen_part(session)
    n = c["chains"]
    m4 = c["hole_lies"] > 0 and c["hole_lies_stopped"] == c["hole_lies"]
    marks = {
        "M1": c["folds_carried_off"] > 0 and c["folds_carried_on"] == 0,
        "M2": n > 0 and c["admitted"] == n and c["read_back"] == c["said"],
        "M3": c["lies"] > 0 and c["lies_found"] == c["lies"],
        "M4": m4,
        "M5": c["witness_runs"] > 0 and c["witness_wrong"] == 0
        and c["witness_stopped"] + c["witness_same"] == c["witness_runs"],
        "M6": bool(scripts) and c["scripts"] > 0
        and c["scripts_ok"] == c["scripts"]
        and c["mutants_rejected"] == c["mutants"],
        "K1": k["answered"] > 0 and k["admitted"] == k["answered"]
        and k["lies_refused"] == k["lies"]
        and k["machine_silent"] == k["refused_by_planner"],
        "P1": 0 < c["max_steps"] < pl.BUDGET
        and c["max_lines"] < ALL_PAIRS_LINES,
        "F1": bool(f["measured"]) and f["texts"] > 0
        and f["same_status"] == f["texts"]
        and f["same_text"] == f["texts"],
    }
    amended = {"M4'": m4}
    rest = [v for m, v in marks.items() if m != "M4"]
    return {
        "chains": c,
        "synthetic": k,
        "frozen": f,
        "corpus": {"texts": len(pls.corpus_texts()), "chains": n},
        "lean": pls.lean_marks(fm.LEAN_FILE, fm.LEAN_THEOREMS),
        "first_note": ("the first measurement (at which M4 was missed, 22 "
                       "of 24 hole lies stopped) was lost in the October "
                       "2026 reorganisation; M4 and M4' are both measured "
                       "on the machine as it now stands"),
        "switches": "tool_machine.ON off; fold_machine.ON off and on",
        "marks": marks,
        "met": sum(1 for v in marks.values() if v),
        "taken": len(marks),
        "amended": amended,
        "amended_met": sum(1 for v in amended.values() if v),
        "amended_taken": len(amended),
        "rest_hold_again": all(rest),
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


def fold_machine_report() -> Dict[str, object]:
    stored = current()
    if stored is not None:
        out = dict(stored)
        out["available"] = True
        return out
    return {
        "available": False,
        "reason": ("the stored measurement is absent or stale; re-take it "
                   "with python3 -m glm_universal.tools fold-machine "
                   "--write"),
    }
