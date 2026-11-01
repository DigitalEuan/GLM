"""``glm_universal.reasoning.tool_machine_study`` -- the marks of
``studies/TOOL_MACHINE_STUDY.md`` (Phase 163): the machine works the tools
out -- convergents, nearest fractions, gate moves and the Leech kissing
number computed in GLM-BAT.

*Created 31 October 2026.*

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from MASTER_PLAN.md (Phase 163),
studies/TOOL_MACHINE_STUDY.md (itself reconstructed on 31 October 2026), the
handler ``_tool_machine`` of tools.py, the row of tests/README.md for
test_tool_machine.py, the docstring of reasoning/tool_machine.py and the
stored measurement reasoning/_data/tool_machine_study.json (whose shape this
module's report keeps).  The marks' thresholds and the held-out control's
generator were not recorded; the ones below are this reconstruction's,
declared here before the measurement.*

**The stored measurement is the original's.**  ``_data/tool_machine_study.json``
was written by the lost module; this reconstruction does not reproduce it
(its corpus, its control and its program lines are its own), so
:func:`write_measurements` writes to :data:`DATA_PATH` only when asked to
and :func:`compare_with_stored` lists every figure that differs.  While the
stored file's digest is not this module's, :func:`tool_machine_report` says
it is stale (never presents the old figures as a re-take).

What is measured
----------------
The chains are those of :func:`planner_ladder_study.answered`, in the
reading mode with the fold machine (Phase 160) on; the tool switch
(``tool_machine.ON``) is the variable.

* **T1** with the switch on no step is carried; reported: carried steps off
  -> on, the newly computed steps by category.
* **T2** every chain admitted with the switch on, and read back.
* **T3** the last newly computed step of every chain that has one, altered:
  found at its own step, nothing promoted.
* **T4** every chain whose newly computed steps enclose a square root, with
  the offered root moved by one: the run stops.
* **T5** both column-3 scripts of every chain with a newly computed step
  verify and both mutants are rejected.
* **K1** a held-out control of :data:`HELD_OUT` tool questions in seven
  kinds, drawn by a declared linear congruential generator: every answer
  the tool gives is admitted and its lie refused; every question the tool
  refuses, given a naive claim, leaves the step unwritten.
* **G1** the Leech texts (:data:`LEECH_TEXTS`): the kissing number counted
  from the Golay census, each admitted and its lie found; the shells the
  machine does not count (:data:`LEECH_UNCOUNTED`) kept carried.
* **P1** every program halts within ``planner_ladder.BUDGET`` machine steps.
* **F1** (and the amendment **F1'**, off and on in the same run): the
  answering-path gate (``runtime/stepwise.py``: ``_ladder_gate``) is absent,
  so the tool switch moves no answer; both are reported **not met** while it
  is absent, never assumed.
* **L1** (beside the marks): ``ToolMachine.lean`` and ``LeechMachine.lean``
  present with their theorems and no ``sorry`` (not met while absent).

Exactness
---------
Integers, :class:`fractions.Fraction`, strings, booleans.
"""
from __future__ import annotations

import json
import math
from contextlib import contextmanager
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

from .. import integrity

__all__ = [
    "DATA_PATH", "BASELINE_PATH", "_SOURCES", "HELD_OUT", "SEED",
    "LEECH_TEXTS", "LEECH_UNCOUNTED", "LEECH_LEAN_FILE",
    "LEECH_LEAN_THEOREMS", "Lcg", "compute", "measure", "write_measurements",
    "measurements", "stored", "state", "current", "module_digest",
    "take_baseline", "tool_machine_report", "compare_with_stored",
    "held_out_question", "held_out_chain", "held_out_part", "chains_part",
    "leech_part", "switches", "category",
]

_HERE = Path(__file__).resolve().parent
DATA_PATH = _HERE / "_data" / "tool_machine_study.json"
BASELINE_PATH = _HERE / "_data" / "tool_machine_baseline.json"

#: Questions of the held-out control.
HELD_OUT: int = 3000

#: The generator's declared seed.
SEED: int = 163

#: The Leech texts the machine counts (the stored measurement's four).
LEECH_TEXTS: Tuple[str, ...] = (
    "the kissing number of the leech lattice divided by 24",
    "the kissing number of the leech lattice minus 196560",
    "the kissing number of the leech lattice plus 1",
    "the number of vectors of norm 4 in the leech lattice plus 1",
)

#: A Leech text whose shell the machine does not count (kept carried).
LEECH_UNCOUNTED: Tuple[str, ...] = (
    "the number of vectors of norm 6 in the leech lattice plus 1",
)

LEECH_LEAN_FILE: str = "LeechMachine.lean"
LEECH_LEAN_THEOREMS: Tuple[str, ...] = (
    "gray_step", "gray_nodup", "machine_octads", "machine_codewords",
    "leech_kissing_from_census")

_SOURCES: Tuple[str, ...] = (
    "reasoning/tool_machine_study.py",
    "reasoning/tool_machine.py",
    "reasoning/fold_machine.py",
    "reasoning/planner_ladder.py",
    "reasoning/planner_ladder_study.py",
    "reasoning/carried_read.py",
    "reasoning/register_files.py",
    "reasoning/batch_machine.py",
    "reasoning/batch_speech.py",
    "reasoning/stepwise_script.py",
    "runtime/stepwise.py",
    "runtime/toolbox.py",
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
def switches(tool: bool, fold: bool = True,
             root=None) -> Iterator[None]:
    """The tool switch, the fold switch and the square-root witness,
    restored afterwards."""
    from . import fold_machine as fm
    from . import tool_machine as tm
    was = (tm.ON, fm.ON, tm._root)
    tm.ON, fm.ON = tool, fold
    if root is not None:
        tm._root = root
    try:
        yield
    finally:
        tm.ON, fm.ON, tm._root = was


def _moved_root(n: int) -> int:
    """The square-root witness moved by one (T4)."""
    return math.isqrt(n) + 1


def category(step) -> str:
    """A carried step's category: the planned step's computation (``convert``
    read as ``conversion``), else its op."""
    if step.op == "planned":
        comp = str(step.detail.get("computation", "planned"))
        return "conversion" if comp == "convert" else comp
    return step.op


# ---------------------------------------------------------------------------
# T1-T5, P1 -- the chains
# ---------------------------------------------------------------------------

def _encloses_sqrt(step) -> bool:
    from . import tool_machine as tm
    r = tm._recompute(step) if step.op == "planned" else None
    if not r or r[0] not in ("tool", "verdict") or len(r) < 2:
        return False
    got = tm.parse_tool(r[1])
    if got is None or got[0] not in ("convergent", "continued fraction",
                                     "best approximation"):
        return False
    expr = got[1][1] if got[0] == "convergent" else got[1][0]
    kind = tm.enclosure_kind(str(expr))
    return kind is not None and kind[0] == "sqrt"


def chains_part(session, scripts: bool = True) -> Dict[str, object]:
    from . import carried_read as cr
    from . import planner_ladder as pl
    from . import planner_ladder_study as pls
    chains = pls.answered(session)
    c: Dict[str, object] = {
        "chains": len(chains), "admitted": 0, "said": 0, "read_back": 0,
        "carried_off": 0, "carried_on": 0, "newly_computed": 0,
        "lies": 0, "lies_found": 0, "witness_runs": 0,
        "witness_stopped": 0, "max_lines": 0, "max_question": "",
        "max_steps": 0, "max_steps_question": "",
    }
    by_cat: Dict[str, int] = {}
    still: Dict[str, int] = {}
    failures: List[str] = []
    items = []
    for text, chain in chains:
        seed = cr.seed_files(chain, session)
        with switches(False):
            off = pl.check_chain(chain, say=False, read=True, files=seed)
        with switches(True):
            on = pl.check_chain(chain, say=True, read=True, files=seed,
                                ladder=True)
        c["carried_off"] += len(off["carried"])
        c["carried_on"] += len(on["carried"])
        for k in on["carried"]:
            cat = category(chain.steps[k - 1])
            still[cat] = still.get(cat, 0) + 1
        c["said"] += 1
        c["read_back"] += bool(on["said"])
        c["admitted"] += on["admitted"]
        if not (on["admitted"] and on["said"]):
            failures.append(text)
        if on["lines"] > c["max_lines"]:
            c["max_lines"], c["max_question"] = on["lines"], text
        if on["machine_steps"] > c["max_steps"]:
            c["max_steps"], c["max_steps_question"] = on["machine_steps"], \
                text
        newly = [k for k in off["carried"] if k in on["computed"]]
        if not newly:
            continue
        c["newly_computed"] += len(newly)
        for k in newly:
            cat = category(chain.steps[k - 1])
            by_cat[cat] = by_cat.get(cat, 0) + 1
        if on["ladder"].run is not None:
            items.append((chain, on["ladder"]))
        k = newly[-1]
        lie = pl.value_lie(chain.steps[k - 1])
        if lie is not None:
            c["lies"] += 1
            with switches(True):
                d = pl.check_chain(pl.lie_chain(chain, k, lie), say=False,
                                   read=True, files=seed)
            ok = d["first_drift"] == k and not d["promoted"]
            c["lies_found"] += ok
            if not ok:
                failures.append(f"T3 {text}")
        if any(_encloses_sqrt(chain.steps[j - 1]) for j in newly):
            c["witness_runs"] += 1
            with switches(True, root=_moved_root):
                d = pl.check_chain(chain, say=False, read=True, files=seed)
            stopped = d["status"] == "halted" and d["exit"] != 0 and \
                not d["promoted"]
            c["witness_stopped"] += stopped
            if not stopped:
                failures.append(f"T4 {text}")
    c["by_category"] = dict(sorted(by_cat.items()))
    c["still_carried"] = dict(sorted(still.items()))
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
# K1 -- the held-out control
# ---------------------------------------------------------------------------

class Lcg:
    """The declared generator: ``x <- (1103515245 x + 12345) mod 2^31``,
    an output the high bits reduced modulo ``n``.  No ``random``."""

    def __init__(self, seed: int) -> None:
        self.x = (seed * 2654435761 + 97) % (2 ** 31)

    def next(self, n: int) -> int:
        self.x = (1103515245 * self.x + 12345) % (2 ** 31)
        return (self.x >> 8) % n


KINDS: Tuple[str, ...] = ("convergent value", "convergent denominator",
                          "term verdict", "best value", "best verdict",
                          "gates moves", "gates verdict")

_BOUNDS: Tuple[int, ...] = (10, 30, 50, 100, 500, 1000, 10 ** 4, 10 ** 6)


def _real(rng: Lcg) -> str:
    j = rng.next(10)
    if j == 0:
        return "pi"
    if j == 1:
        return "e"
    while True:
        m = 2 + rng.next(98)
        if math.isqrt(m) ** 2 != m:
            return f"sqrt({m})"


def _word(rng: Lcg) -> str:
    """A 24-bit word, its blocks drawn so that both reachable and
    unreachable pairs are common."""
    return hex(rng.next(2 ** 24))


def _near(rng: Lcg, a: str) -> str:
    """A word block by block in the orbit of ``a``'s blocks under the two
    gates (``substrate_cognition.gate_orbit_distances``, used only to draw
    the question): a pair the tool answers, unless the draw keeps no
    block."""
    from . import substrate_cognition as sc
    dist = sc.gate_orbit_distances()
    w = int(a, 16)
    out = 0
    for j in range(8):
        s3 = (w // (8 ** j)) % 8
        ts = sorted(t for (x, t) in dist if x == s3)
        t3 = ts[rng.next(len(ts))] if ts else s3
        out += t3 * (8 ** j)
    return hex(out)


def _fig(got, name: str) -> Optional[str]:
    v = got.figures.get(name)
    return None if v is None else str(v)


def _terms(got) -> List[int]:
    import ast
    t = got.figures.get("terms")
    t = ast.literal_eval(t) if isinstance(t, str) else t
    return [int(x) for x in t]


def held_out_question(rng: Lcg, kind: str) -> Tuple[str, Tuple[str, ...]]:
    """``(question, recompute)`` of one held-out question of ``kind``: the
    tool line and the selector (or verdict test) the planner would record.
    A stated value in a verdict is the tool's own answer or a near miss."""
    from ..runtime.toolbox import run_tool
    if kind in ("convergent value", "convergent denominator"):
        x, k = _real(rng), 1 + rng.next(12)
        line = f"tool convergent {k} of {x}"
        sel = ("value", "value") if kind == "convergent value" else \
            ("part", "value", "denominator")
        return f"{kind}: convergent {k} of {x}", ("tool", line) + sel
    if kind == "term verdict":
        x, k = _real(rng), 1 + rng.next(12)
        line = f"tool continued fraction {x} terms {k}"
        got = run_tool(line)
        t = _terms(got)[k - 1] if got.ok and len(_terms(got)) >= k else 1
        stated = t if rng.next(2) else t + 1 + rng.next(3)
        return (f"is {stated} term {k} of the continued fraction of {x}",
                ("verdict", line, "equals", "index", "terms", str(k - 1),
                 str(stated)))
    if kind in ("best value", "best verdict"):
        x, n = _real(rng), _BOUNDS[rng.next(len(_BOUNDS))]
        line = f"tool best approximation {x} denominator {n}"
        if kind == "best value":
            return f"the fraction nearest {x} with denominator at most {n}", \
                ("tool", line, "value", "value")
        got = run_tool(line)
        best = Fraction(_fig(got, "value") or "0") if got.ok else Fraction(0)
        if rng.next(2):
            stated = best
        else:
            import ast
            cands = got.figures.get("candidates") if got.ok else None
            cands = ast.literal_eval(cands) if isinstance(cands, str) \
                else (cands or [])
            other = [Fraction(str(c)) for c in cands
                     if Fraction(str(c)) != best]
            stated = other[0] if other else best + Fraction(1, n)
        return (f"is {stated} the fraction nearest {x} with denominator at "
                f"most {n}",
                ("verdict", line, "equals", "value", "value", str(stated)))
    a = _word(rng)
    c = _near(rng, a) if rng.next(2) else _word(rng)
    line = f"tool gates {a} to {c}"
    if kind == "gates moves":
        return f"the gate moves from {a} to {c}", \
            ("tool", line, "value", "moves")
    return f"is {c} reachable from {a} by gate moves", \
        ("verdict", line, "flag", "reachable")


def _tool_answer(rec: Tuple[str, ...]) -> Optional[object]:
    """The tool's own answer to a recorded line and selector, read with
    ``stepwise_script``'s selectors; ``None`` when the tool refuses."""
    from ..runtime.toolbox import run_tool
    from .stepwise_script import parse_value
    got = run_tool(rec[1])
    if rec[0] == "verdict" and rec[2] in ("flag", "flag-not"):
        flag = got.figures.get(rec[3])
        if isinstance(flag, str) and flag in ("True", "False"):
            flag = flag == "True"
        if not isinstance(flag, bool):
            return None
        return str(flag if rec[2] == "flag" else not flag)
    if not got.ok:
        return None
    sel = rec[2:] if rec[0] == "tool" else rec[3:-1]
    try:
        fig = got.figures[sel[1]]
        if sel[0] == "index":
            import ast
            seq = ast.literal_eval(fig) if isinstance(fig, str) else fig
            v = Fraction(str(seq[int(sel[2])]))
        elif sel[0] == "part":
            q = Fraction(str(fig))
            v = Fraction(q.numerator if sel[2] == "numerator"
                         else q.denominator)
        else:
            v = parse_value(str(fig))
    except (KeyError, IndexError, ValueError, SyntaxError):
        return None
    if rec[0] == "verdict":
        return str(v == Fraction(rec[-1]))
    return v


def held_out_chain(question: str, rec: Tuple[str, ...], claim: object):
    """One planned step claiming ``claim``."""
    from .stepwise_script import Chain, Step
    comp = rec[1].split(" ", 1)[1]
    for name in ("convergent", "continued fraction", "best approximation",
                 "gates"):
        if comp.startswith(name):
            comp = "tool " + name
    if rec[0] == "verdict":
        comp += " verdict"
    step = Step(1, "planned", (), claim, question,
                {"computation": comp, "question": question,
                 "recompute": list(rec)})
    return Chain(question, (step,), "held-out")


def held_out_part(count: int = HELD_OUT, seed: int = SEED
                  ) -> Dict[str, object]:
    from . import planner_ladder as pl
    rng = Lcg(seed)
    k: Dict[str, object] = {"questions": count, "answered": 0,
                            "admitted": 0, "lies": 0, "lies_refused": 0,
                            "refused_by_tool": 0, "machine_silent": 0,
                            "carried": 0, "max_steps": 0}
    by_kind: Dict[str, List[int]] = {x: [0, 0, 0] for x in KINDS}
    failures: List[Dict[str, object]] = []
    files = {"q.txt": ()}
    with switches(True):
        for i in range(count):
            kind = KINDS[i % len(KINDS)]
            question, rec = held_out_question(rng, kind)
            by_kind[kind][0] += 1
            value = _tool_answer(rec)
            if value is None:
                k["refused_by_tool"] += 1
                naive = Fraction(0) if rec[0] == "tool" else "False"
                d = pl.check_chain(held_out_chain(question, rec, naive),
                                   say=False, read=True, files=files,
                                   ladder=True)
                run = d["ladder"].run
                written = run is not None and pl.file_of(1) in run.files
                silent = not written and 1 not in d["carried"]
                k["machine_silent"] += silent
                if not silent:
                    failures.append({"refused": question})
                continue
            k["answered"] += 1
            by_kind[kind][1] += 1
            chain = held_out_chain(question, rec, value)
            d = pl.check_chain(chain, say=False, read=True, files=files)
            k["carried"] += 1 in d["carried"]
            k["max_steps"] = max(k["max_steps"], d["machine_steps"])
            ok = d["admitted"] and 1 in d["computed"]
            k["admitted"] += ok
            by_kind[kind][2] += ok
            if not ok:
                failures.append({"answered": question,
                                 "value": _plain(value),
                                 "status": d["status"], "exit": d["exit"],
                                 "error": d["error"]})
            lie = pl.value_lie(chain.steps[0])
            if lie is None:
                continue
            k["lies"] += 1
            e = pl.check_chain(pl.lie_chain(chain, 1, lie), say=False,
                               read=True, files=files)
            k["lies_refused"] += not e["admitted"]
            if e["admitted"]:
                failures.append({"lie": question})
    k["by_kind"] = by_kind
    k["failure_count"] = len(failures)
    k["failures"] = failures[:20]
    return k


# ---------------------------------------------------------------------------
# G1 -- the Leech kissing number
# ---------------------------------------------------------------------------

def leech_part(session) -> Dict[str, object]:
    from . import carried_read as cr
    from . import planner_ladder as pl
    from ..runtime import stepwise as sw
    g: Dict[str, object] = {"texts": len(LEECH_TEXTS), "answered": 0,
                            "admitted": 0, "carried_off": 0,
                            "computed_on": 0, "lies": 0, "lies_found": 0,
                            "machine_steps": 0, "uncounted":
                            len(LEECH_UNCOUNTED), "uncounted_carried": 0}
    values: Dict[str, str] = {}
    failures: List[str] = []

    def llvq(chain) -> List[int]:
        return [s.index for s in chain.steps if s.op == "planned" and
                "tool llvq" in str(s.detail.get("recompute"))]

    for text in LEECH_TEXTS + LEECH_UNCOUNTED:
        a = sw.answer(session, text)
        if not a.answered:
            failures.append(f"unanswered: {text}")
            continue
        chain = a.chain
        ks = llvq(chain)
        seed = cr.seed_files(chain, session)
        with switches(False):
            off = pl.check_chain(chain, say=False, read=True, files=seed)
        with switches(True):
            on = pl.check_chain(chain, say=False, read=True, files=seed)
        if text in LEECH_UNCOUNTED:
            g["uncounted_carried"] += bool(ks) and all(
                k in on["carried"] for k in ks) and on["admitted"]
            continue
        g["answered"] += 1
        values[text] = str(chain.answer)
        g["admitted"] += on["admitted"]
        g["carried_off"] += bool(ks) and all(k in off["carried"] for k in ks)
        g["computed_on"] += bool(ks) and all(k in on["computed"] for k in ks)
        g["machine_steps"] = max(g["machine_steps"], on["machine_steps"])
        if not on["admitted"]:
            failures.append(text)
        if ks:
            k = ks[-1]
            g["lies"] += 1
            with switches(True):
                d = pl.check_chain(pl.lie_chain(
                    chain, k, chain.steps[k - 1].value + 1), say=False,
                    read=True, files=seed)
            ok = d["first_drift"] == k and not d["promoted"]
            g["lies_found"] += ok
            if not ok:
                failures.append(f"lie: {text}")
    g["values"] = values
    g["failures"] = failures
    return g


# ---------------------------------------------------------------------------
# F1 -- the frozen path
# ---------------------------------------------------------------------------

def gate_present() -> bool:
    p = _HERE.parent / "runtime" / "stepwise.py"
    return p.exists() and "_ladder_gate" in p.read_text(encoding="utf-8")


def take_baseline() -> Path:
    """Ask every recorded text (the stepwise texts and the evaluation's
    cases) with the tool switch off and store the answers in
    :data:`BASELINE_PATH`.  Take it just before the gate goes back into the
    answering path."""
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
         "note": "taken with tool_machine.ON off"},
        indent=1, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8")
    return BASELINE_PATH


def _frozen() -> Dict[str, object]:
    out: Dict[str, object] = {"texts": 0, "same_status": 0, "same_text": 0,
                              "gate": gate_present(), "measured": False}
    if not out["gate"]:
        out["note"] = ("F1 and F1' not measured: the stepwise answering "
                       "path does not run its chains through the machine "
                       "(runtime/stepwise.py has no _ladder_gate), so the "
                       "tool switch moves no answer and a comparison would "
                       "show nothing about it")
    else:
        out["note"] = ("F1 and F1' not measured by this reconstruction: "
                       "the gate is present, take the baseline and add the "
                       "comparison before reporting them")
    return out


# ---------------------------------------------------------------------------
# the measurement
# ---------------------------------------------------------------------------

def compute(scripts: bool = True,
            held_out: int = HELD_OUT) -> Dict[str, object]:
    from . import planner_ladder as pl
    from . import planner_ladder_study as pls
    from . import tool_machine as tm
    session = _session()
    c = chains_part(session, scripts)
    k = held_out_part(held_out)
    g = leech_part(session)
    f = _frozen()
    n = c["chains"]
    marks = {
        "T1": c["carried_off"] > 0 and c["carried_on"] == 0,
        "T2": n > 0 and c["admitted"] == n and c["read_back"] == c["said"],
        "T3": c["lies"] > 0 and c["lies_found"] == c["lies"],
        "T4": c["witness_runs"] > 0
        and c["witness_stopped"] == c["witness_runs"],
        "T5": bool(scripts) and c["scripts"] > 0
        and c["scripts_ok"] == c["scripts"]
        and c["mutants_rejected"] == c["mutants"],
        "K1": k["answered"] > 0 and k["admitted"] == k["answered"]
        and k["lies_refused"] == k["lies"]
        and k["machine_silent"] == k["refused_by_tool"],
        "G1": g["answered"] == g["texts"] > 0
        and g["admitted"] == g["texts"] and g["lies_found"] == g["lies"]
        and g["computed_on"] == g["texts"]
        and g["uncounted_carried"] == g["uncounted"],
        "P1": 0 < max(c["max_steps"], g["machine_steps"], k["max_steps"])
        < pl.BUDGET,
        "F1": False,
    }
    amended = {"F1'": False}
    lean_tm = pls.lean_marks(Path(tm.LEAN_FILE).name, tm.LEAN_THEOREMS)
    lean_lm = pls.lean_marks(LEECH_LEAN_FILE, LEECH_LEAN_THEOREMS)
    return {
        "chains": c,
        "held_out": k,
        "leech": g,
        "frozen": f,
        "paired": {},
        "corpus": {"texts": len(pls.corpus_texts()), "chains": n},
        "lean": {"tool_machine": lean_tm, "leech_machine": lean_lm,
                 "met": bool(lean_tm["met"] and lean_lm["met"])},
        "first_note": ("the first measurement (F1 699 of 702) was lost in "
                       "the October 2026 reorganisation"),
        "switches": "fold_machine.ON on; tool_machine.ON off and on",
        "marks": marks,
        "met": sum(1 for v in marks.values() if v),
        "taken": len(marks),
        "amended": amended,
        "amended_met": sum(1 for v in amended.values() if v),
        "amended_taken": len(amended),
        "rest_hold_again": all(v for m, v in marks.items() if m != "F1"),
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
    """Re-take the measurement.  The stored file is the original module's
    record; re-taking replaces it with this reconstruction's figures (see
    :func:`compare_with_stored` first)."""
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


def stored() -> Optional[Dict[str, object]]:
    """The stored measurement as it is, fresh or not."""
    return measurements()


def state() -> Dict[str, object]:
    got = measurements()
    live = module_digest()
    if got is None:
        return {"present": False, "fresh": False, "verdict": "absent",
                "live_digest": live, "stored_digest": None}
    stored_digest = got.get("source_digest")
    return {"present": True, "fresh": stored_digest == live,
            "verdict": "current" if stored_digest == live else "stale",
            "live_digest": live, "stored_digest": stored_digest}


def current() -> Optional[Dict[str, object]]:
    if state()["fresh"]:
        return measurements()
    return None


def _flat(x: Any, prefix: str = "") -> Dict[str, object]:
    out: Dict[str, object] = {}
    if isinstance(x, dict):
        for key, v in x.items():
            out.update(_flat(v, f"{prefix}{key}."))
    else:
        out[prefix[:-1]] = x
    return out


def compare_with_stored(live: Dict[str, object]) -> List[Tuple[str, object,
                                                                object]]:
    """``(key, stored, live)`` for every scalar figure the two disagree on
    (lists and the digest left out)."""
    old = measurements() or {}
    a, b = _flat(_plain(old)), _flat(_plain(live))
    out = []
    for key in sorted(set(a) | set(b)):
        if key.endswith("source_digest"):
            continue
        va, vb = a.get(key), b.get(key)
        if isinstance(va, list) or isinstance(vb, list):
            continue
        if va != vb:
            out.append((key, va, vb))
    return out


def tool_machine_report() -> Dict[str, object]:
    got = current()
    if got is not None:
        out = dict(got)
        out["available"] = True
        return out
    st = state()
    if st["present"]:
        reason = ("the stored measurement (reasoning/_data/"
                  "tool_machine_study.json) was written by the original "
                  "module, lost in the October 2026 reorganisation; its "
                  "digest is not this reconstruction's, so it is stale and "
                  "is not shown as a re-take (stored(): 8 of 9 marks, F1 "
                  "missed, F1' met).  Re-take it with python3 -m "
                  "glm_universal.tools tool-machine --write")
    else:
        reason = ("the stored measurement is absent; re-take it with "
                  "python3 -m glm_universal.tools tool-machine --write")
    return {"available": False, "reason": reason}
