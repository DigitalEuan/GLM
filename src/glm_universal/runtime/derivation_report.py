"""``glm_universal.runtime.derivation_report`` -- the marks of Phase 106.

The measurement of ``studies/DERIVATION_STUDY.md`` against the marks R1-R9
declared before any code in :mod:`glm_universal.evaluation.derivation_cases`.
Every answered reading's column-3 script is run in a fresh ``python3 -I``
interpreter, and again with its claim altered, so the report lives in the
runtime layer.  The prover battery runs each formula's script in-process
(``exec`` of the same stand-alone text, which imports nothing of the
package) to keep two thousand checks cheap.

Nothing here uses a float (D7).
"""

from __future__ import annotations

import io
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from ..evaluation import derivation_cases as C
from ..reasoning import derivation as D
from ..reasoning import proof_search as PS
from ..reasoning import symbolic as S
from . import derivation_frames as DF
from . import derivation_scripts as DS
from .question_frames import run_gate

__all__ = ["proof_marks", "motion_marks", "transfer_marks", "profile_marks",
           "refusal_marks", "gate_mark", "prover_battery", "outside_mark",
           "lean_mark", "derivation_report", "LEAN_FILE", "LEAN_THEOREMS",
           "random_formula"]

LEAN_FILE = (Path(__file__).resolve().parent.parent.parent / "lean" /
             "RequestProject" / "GLM" / "Derivations.lean")

#: The theorems mark R9 names.
LEAN_THEOREMS = ("g4ip_sound", "curry_derivation", "slab_profile",
                 "cylinder_profile", "sphere_profile",
                 "double_pendulum_modes")


def _gate(script: str) -> bool:
    return run_gate(script, seconds=20)[0]


def _row(cid: str, ok: bool, reading=None, mutant=None, run: bool = True
         ) -> Dict[str, object]:
    row: Dict[str, object] = {"id": cid, "as_declared": ok}
    if run and reading is not None and reading.script:
        row["gate"] = _gate(reading.script)
        if mutant is not None:
            row["mutant_rejected"] = not _gate(mutant.script)
    return row


# ---------------------------------------------------------------------------
# R1-R4
# ---------------------------------------------------------------------------

def proof_marks(run_scripts: bool = True) -> Dict[str, object]:
    rows = []
    for cid, q, verdict, val in C.PROOFS:
        prem, goal = PS.parse_sequent(q.split(":", 1)[1])
        v = PS.decide(prem, goal)
        ok = v.kind == verdict and (val is None or v.valuation == val)
        rd = DF.read_operation(q)
        mut = DF.mutated_operation(q)
        rows.append(_row(cid, ok, rd, mut, run_scripts))
    return {"rows": rows, "as_declared": sum(r["as_declared"] for r in rows),
            "of": len(rows),
            "met": all(r["as_declared"] for r in rows)}


def _motion_parts(q: str) -> Tuple[List[str], str, bool]:
    head, body = q.split(":", 1)
    spec = head[len(DF.MOTION):]
    small = bool(re.search(r",\s*small oscillations\s*$", spec))
    spec = re.sub(r",\s*small oscillations\s*$", "", spec)
    return [c.strip() for c in spec.split(",")], \
        body.split("=", 1)[1].strip(), small


def motion_marks(run_scripts: bool = True) -> Dict[str, object]:
    rows = []
    for cid, q, eqs, lin, w2 in C.MOTION:
        coords, lag, small = _motion_parts(q)
        mo = D.equations_of_motion(lag, coords, small)
        dyn = D.dynamic_names(coords)
        ok = len(mo.equations) == len(eqs) and all(
            D.proportional(e, S.parse(d, mo.ctx), dyn, mo.ctx)
            for e, d in zip(mo.equations, eqs))
        if lin is not None:
            ok = ok and mo.linear is not None and all(
                D.proportional(e, S.parse(d, mo.ctx), dyn, mo.ctx)
                for e, d in zip(mo.linear, lin))
        if w2 is not None:
            fr = mo.frequencies or []
            ok = ok and len(fr) == len(w2) and all(
                any((f - S.parse(d)).is_zero() for f in fr) for d in w2)
        rows.append(_row(cid, ok, DF.read_operation(q),
                         DF.mutated_operation(q), run_scripts))
    return {"rows": rows, "as_declared": sum(r["as_declared"] for r in rows),
            "of": len(rows), "met": all(r["as_declared"] for r in rows)}


def transfer_marks(run_scripts: bool = True) -> Dict[str, object]:
    rows = []
    for cid, q, tfs in C.TRANSFER:
        head, body = q.split(":", 1)
        m = re.match(r"(.*)\s+to\s+(.*)$", head[len(DF.TRANSFER):])
        ins = [x.strip() for x in m.group(1).split(",")]
        outs = [x.strip() for x in m.group(2).split(",")]
        tr = D.transfer_functions([e.strip() for e in body.split(";")],
                                  ins, outs)
        ok = all(k in tr.functions and
                 (tr.functions[k] - S.parse(v, tr.ctx)).is_zero()
                 for k, v in tfs.items())
        rows.append(_row(cid, ok, DF.read_operation(q),
                         DF.mutated_operation(q), run_scripts))
    return {"rows": rows, "as_declared": sum(r["as_declared"] for r in rows),
            "of": len(rows), "met": all(r["as_declared"] for r in rows)}


def profile_marks(run_scripts: bool = True) -> Dict[str, object]:
    rows = []
    for cid, q, prof in C.PROFILES:
        parts = [p.strip() for p in q.split(":", 1)[1].split(";")]
        pf = D.boundary_value_profile(parts[0], parts[1:])
        ok = (pf.profile - S.parse(prof, pf.ctx)).is_zero()
        rows.append(_row(cid, ok, DF.read_operation(q),
                         DF.mutated_operation(q), run_scripts))
    return {"rows": rows, "as_declared": sum(r["as_declared"] for r in rows),
            "of": len(rows), "met": all(r["as_declared"] for r in rows)}


def refusal_marks() -> Dict[str, object]:
    rows = []
    for cid, text, code in C.REFUSALS:
        rd = DF.read_operation(text)
        rows.append({"id": cid, "code": rd.code, "want": code,
                     "as_declared": (not rd.answered) and rd.code == code})
    return {"rows": rows, "as_declared": sum(r["as_declared"] for r in rows),
            "of": len(rows), "met": all(r["as_declared"] for r in rows)}


def gate_mark(*parts) -> Dict[str, object]:
    """R6: every reading with a script verified, every mutant rejected."""
    rows = [r for p in parts for r in p["rows"] if "gate" in r]
    ok = sum(1 for r in rows if r["gate"])
    mr = sum(1 for r in rows if r.get("mutant_rejected"))
    return {"readings": len(rows), "verified": ok, "mutants_rejected": mr,
            "met": bool(rows) and ok == len(rows) == mr}


# ---------------------------------------------------------------------------
# R7: the prover battery
# ---------------------------------------------------------------------------

class _Lcg:
    def __init__(self, seed: int):
        self.s = seed

    def next(self, n: int) -> int:
        self.s = (self.s * 6364136223846793005 + 1442695040888963407) \
            % (1 << 64)
        return (self.s >> 33) % n


def random_formula(rng: _Lcg, atoms: Sequence[str], depth: int) -> str:
    if depth == 0 or rng.next(4) == 0:
        return atoms[rng.next(len(atoms))]
    k = rng.next(5)
    if k == 0:
        return "~" + _paren(random_formula(rng, atoms, depth - 1))
    op = ("->", "&", "|", "<->")[k - 1]
    return f"{_paren(random_formula(rng, atoms, depth - 1))} {op} " \
           f"{_paren(random_formula(rng, atoms, depth - 1))}"


def _paren(t: str) -> str:
    return t if re.fullmatch(r"[A-Za-z_]\w*", t) else f"({t})"


def _exec_script(script: str) -> bool:
    out = io.StringIO()
    saved, sys.stdout = sys.stdout, out
    try:
        exec(compile(script, "<column-3>", "exec"), {"__name__": "c3"})
    finally:
        sys.stdout = saved
    lines = [ln for ln in out.getvalue().splitlines() if ln.strip()]
    return bool(lines) and lines[-1].strip().endswith("VERIFIED True")


def prover_battery(count: Optional[int] = None) -> Dict[str, object]:
    n, seed, natoms, depth = C.PROVER_BATTERY
    n = count or n
    rng = _Lcg(seed)
    atoms = ["p", "q", "r", "s", "t"][:natoms]
    kinds: Dict[str, int] = {}
    unsound = gaps = script_fail = kripke = 0
    for _ in range(n):
        text = random_formula(rng, atoms, depth)
        goal = PS.parse_formula(text)
        try:
            v = PS.decide([], goal)
        except PS.ProofError:
            gaps += 1
            continue
        kinds[v.kind] = kinds.get(v.kind, 0) + 1
        if v.proof is not None:
            if not PS.check_proof(v.proof) or \
                    PS.truth_table([], goal) is not None:
                unsound += 1
        if v.kind == "classical" and v.kripke is not None:
            kripke += 1
        script = DS.proof_script([], goal, v.kind, v.proof, v.valuation,
                                 v.excluded_middle, v.kripke, "BATTERY")
        if not _exec_script(script):
            script_fail += 1
    return {"formulas": n, "kinds": kinds, "unsound": unsound, "gaps": gaps,
            "script_failures": script_fail, "classical_with_kripke": kripke,
            "met": unsound == 0 and gaps == 0 and script_fail == 0}


# ---------------------------------------------------------------------------
# R8: the outside set and no regression
# ---------------------------------------------------------------------------

def outside_mark() -> Dict[str, object]:
    from ..evaluation import question_set_b_cases as qc
    from ..evaluation.cases import CASES
    from . import question_frames as qf
    items = qc.outside()
    rows = []
    for idx, frag in C.OUTSIDE_P:
        rd = qf.read(items[idx].text)
        rows.append({"index": idx, "frame": rd.frame if rd else None,
                     "answered": bool(rd and rd.answered),
                     "gate": bool(rd and rd.gate and rd.gate[0]),
                     "fragment": bool(rd and frag in rd.value)})
    declared = {i for i, _ in C.OUTSIDE_P}
    texts = [(f"O{it.index:03d}", it.text) for it in items
             if it.index not in declared] + \
        [(it.id, it.query) for it in qc.set_b()] + \
        [(c.id, c.question) for c in CASES]

    def frame_name(text: str) -> Optional[str]:
        got = qf.frame_of(text)
        return got[0].name if got else None

    moved = []
    saved = qf.DERIVATIONS
    try:
        before = {}
        qf.DERIVATIONS = False
        for key, text in texts:
            before[key] = frame_name(text)
        qf.DERIVATIONS = True
        for key, text in texts:
            if frame_name(text) != before[key]:
                moved.append(key)
    finally:
        qf.DERIVATIONS = saved
    ok_rows = all(r["answered"] and r["gate"] and r["fragment"] for r in rows)
    return {"rows": rows, "answered": sum(r["answered"] for r in rows),
            "of": len(rows), "texts_checked": len(texts), "moved": moved,
            "evaluation_cases": len(CASES),
            "met": ok_rows and not moved}


# ---------------------------------------------------------------------------
# R9
# ---------------------------------------------------------------------------

def lean_mark() -> Dict[str, object]:
    """R9 (the source half; the build is ``lake build``)."""
    if not LEAN_FILE.exists():
        return {"exists": False, "met": False}
    src = LEAN_FILE.read_text(encoding="utf-8")
    code = re.sub(r"/-.*?-/", "", src, flags=re.S)
    code = re.sub(r"--[^\n]*", "", code)
    missing = [t for t in LEAN_THEOREMS
               if not re.search(rf"theorem\s+{t}\b", code)]
    has_sorry = bool(re.search(r"\bsorry\b", code))
    return {"exists": True, "missing": missing, "sorry": has_sorry,
            "met": not missing and not has_sorry}


def derivation_report(run_scripts: bool = True,
                      battery: Optional[int] = None) -> Dict[str, object]:
    r1 = proof_marks(run_scripts)
    r2 = motion_marks(run_scripts)
    r3 = transfer_marks(run_scripts)
    r4 = profile_marks(run_scripts)
    r5 = refusal_marks()
    r6 = gate_mark(r1, r2, r3, r4) if run_scripts else {"met": None}
    r7 = prover_battery(battery)
    r8 = outside_mark()
    r9 = lean_mark()
    marks = {"R1": r1, "R2": r2, "R3": r3, "R4": r4, "R5": r5, "R6": r6,
             "R7": r7, "R8": r8, "R9": r9}
    met = sum(1 for m in marks.values() if m.get("met"))
    return {"marks": marks, "met": met, "of": len(marks)}
