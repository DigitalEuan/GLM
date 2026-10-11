"""``glm_universal.runtime.derivation_two_report`` -- the marks of Phase 107.

The measurement of ``studies/DERIVATION_TWO_STUDY.md`` against the marks
Q1-Q11 declared before any code in
:mod:`glm_universal.evaluation.derivation_two_cases`.  Every answered
reading's column-3 script is run in a fresh ``python3 -I`` interpreter, and
again with its claim altered.  The batteries run their scripts in-process
(``exec`` of the same stand-alone text, which imports nothing of the
package) to keep the checks cheap.

Nothing here uses a float (D7).
"""

from __future__ import annotations

import io
import re
import sys
from fractions import Fraction
from itertools import combinations, product
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from ..evaluation import derivation_two_cases as C
from ..reasoning import coding_theory as CT
from ..reasoning import fft_derivation as FD
from ..reasoning import info_inequality as II
from ..reasoning import maxent as ME
from ..reasoning import spectral as SP
from ..reasoning import symbolic as S
from . import derivation_two_frames as DF
from . import derivation_two_scripts as DS
from .question_frames import run_gate

__all__ = ["inequality_marks", "code_marks", "rd_marks", "maxent_marks",
           "eigen_marks", "other_marks", "refusal_marks", "gate_mark",
           "inequality_battery", "code_battery", "battery_mark",
           "outside_mark", "lean_mark", "derivation_two_report", "LEAN_FILE",
           "random_inequality", "random_code", "brute_force_ambiguous"]

LEAN_FILE = (Path(__file__).resolve().parent.parent.parent / "glm_lean" /
             "RequestProject" / "GLM" / "DerivationsTwo.lean")


def _gate(script: str) -> bool:
    return run_gate(script, seconds=20)[0]


def _row(cid: str, ok: bool, q: str, run: bool) -> Dict[str, object]:
    row: Dict[str, object] = {"id": cid, "as_declared": ok}
    if run:
        rd = DF.read_operation(q)
        if rd.script:
            row["gate"] = _gate(rd.script)
            row["mutant_rejected"] = not _gate(DF.mutated_operation(q).script)
    return row


def _summary(rows: List[Dict[str, object]]) -> Dict[str, object]:
    return {"rows": rows, "as_declared": sum(bool(r["as_declared"])
                                             for r in rows),
            "of": len(rows), "met": all(r["as_declared"] for r in rows)}


def _norm(t: str) -> str:
    return re.sub(r"\s+", "", t)


# ---------------------------------------------------------------------------
# Q1-Q6
# ---------------------------------------------------------------------------

def inequality_marks(run_scripts: bool = True) -> Dict[str, object]:
    rows = []
    for cid, q, verdict in C.INEQUALITIES:
        v = II.decide(II.parse_problem(q.split(":", 1)[1]))
        rows.append(_row(cid, v.kind == verdict, q, run_scripts))
    return _summary(rows)


def code_marks(run_scripts: bool = True) -> Dict[str, object]:
    rows = []
    for cid, q, ud, pf, kraft, amb in C.CODES:
        v = CT.decide_code(q.split(":", 1)[1])
        ok = (v.unique == ud and v.prefix_free == pf and
              v.kraft == Fraction(kraft) and
              (amb is None or (v.ambiguous is not None and
                               v.ambiguous[0] == amb)))
        rows.append(_row(cid, ok, q, run_scripts))
    for cid, q, words in C.PREFIX_CONSTRUCTIONS:
        rd = DF.read_operation(q)
        ok = rd.answered and rd.value.startswith(
            "prefix code " + ", ".join(words) + " ")
        rows.append(_row(cid, ok, q, run_scripts))
    return _summary(rows)


def _rd_source(q: str) -> str:
    return q.split(" for ", 1)[1].rsplit(" source", 1)[0]


def rd_marks(run_scripts: bool = True) -> Dict[str, object]:
    rows = []
    for cid, q, fn, te, zero, gap in C.RATE_DISTORTION:
        r = CT.hamming_rate_distortion(_rd_source(q))
        ok = (_norm(r.function) == _norm(fn) and r.tight_end == te and
              r.zero_from == zero and r.gap == gap)
        rd = DF.read_operation(q)
        ok = ok and (("NOT_TIGHT" in rd.value) == gap)
        rows.append(_row(cid, ok, q, run_scripts))
    return _summary(rows)


def _maxent_parts(q: str) -> Tuple[str, str]:
    body = q.split(" density on ", 1)[1]
    m = re.match(r"(\(.*?\)|\[.*?\]|\[.*?\))\s*(?:with\s+(.*))?$", body)
    return m.group(1), m.group(2) or ""


def maxent_marks(run_scripts: bool = True) -> Dict[str, object]:
    rows = []
    for cid, q, dens, h in C.MAXENT:
        r = ME.maximum_entropy(*_maxent_parts(q))
        ok = _norm(r.density) == _norm(dens) and _norm(r.entropy) == _norm(h)
        rows.append(_row(cid, ok, q, run_scripts))
    return _summary(rows)


def eigen_marks(run_scripts: bool = True) -> Dict[str, object]:
    rows = []
    for cid, q, lam, idx, ef in C.EIGEN:
        parts = [p.strip() for p in q.split(":", 1)[1].split(";")]
        e = SP.eigenvalue_problem(parts[0], parts[1:])
        ok = (_norm(e.eigenvalue) == _norm(lam) and e.index == idx and
              _norm(e.eigenfunction) == _norm(ef))
        rows.append(_row(cid, ok, q, run_scripts))
    return _summary(rows)


def other_marks(run_scripts: bool = True) -> Dict[str, object]:
    rows = []
    for cid, q, T in C.SCATTERING:
        body = q.split("V(x) =", 1)[1]
        pot, _, rel = body.partition(",")
        sc = SP.transmission(pot, rel.strip() or None)
        want = S.parse(T)
        got = sc.T_energy_rf if sc.T_energy_rf is not None else sc.T_full
        rows.append(_row(cid, (got - want).is_zero(), q, run_scripts))
    for cid, q, stages, flies, tw, out_order, in_order in C.FFT:
        n = int(q.rsplit("=", 1)[1])
        f = FD.derive_fft(n, "dif" if "frequency" in q else "dit")
        ok = (f.stages == stages and len(f.butterflies) == flies and
              f.nontrivial_twiddles == tw and
              (out_order is None or f.output_order == out_order) and
              (in_order is None or f.input_order == in_order))
        rows.append(_row(cid, ok, q, run_scripts))
    for cid, q, const, mode, peak, guard in C.POSTERIOR:
        m = re.search(r"k = (\d+) errors in n = (\d+)", q)
        k, n = (int(m.group(1)), int(m.group(2))) if m else (None, None)
        p = CT.rate_posterior(k, n, "grid" in q)
        ok = _norm(p.constant) == _norm(const) and p.mode == mode
        if peak is not None:
            ok = ok and str(p.peak) == peak and (p.peak == p.guard) == guard
        rows.append(_row(cid, ok, q, run_scripts))
    return _summary(rows)


def refusal_marks() -> Dict[str, object]:
    """Q7.  Narrowed by Phase 118 (``derivation_three_cases.
    PHASE_107_NARROWED``, declared before that round's code): a refusal the
    later round answers instead is met when the reading is answered with the
    declared fragment."""
    from ..evaluation import derivation_three_cases as C3
    from ..evaluation import derivation_four_cases as C4
    narrowed = {cid: (frag, "Phase 118")
                for cid, frag in C3.PHASE_107_NARROWED}
    # Phase 119's narrowing of Phase 118's refusals applies to the same
    # texts where Phase 107 declared them too (same id, same text)
    texts3 = {cid: t for cid, t, _ in C3.REFUSALS}
    for cid, frag in C4.PHASE_118_NARROWED:
        narrowed.setdefault(cid, (frag, "Phase 119"))
    rows = []
    for cid, text, code in C.REFUSALS:
        rd = DF.read_operation(text)
        if cid in narrowed and (narrowed[cid][1] == "Phase 118" or
                                texts3.get(cid) == text):
            frag, by = narrowed[cid]
            ok = rd.answered and frag in rd.value
            rows.append({"id": cid, "code": rd.code, "want": code,
                         "narrowed_by": by, "as_declared": ok})
            continue
        rows.append({"id": cid, "code": rd.code, "want": code,
                     "as_declared": (not rd.answered) and rd.code == code})
    return _summary(rows)


def gate_mark(*parts) -> Dict[str, object]:
    """Q8: every reading with a script verified, every mutant rejected."""
    rows = [r for p in parts for r in p["rows"] if "gate" in r]
    ok = sum(1 for r in rows if r["gate"])
    mr = sum(1 for r in rows if r.get("mutant_rejected"))
    return {"readings": len(rows), "verified": ok, "mutants_rejected": mr,
            "met": bool(rows) and ok == len(rows) == mr}


# ---------------------------------------------------------------------------
# Q9: the batteries
# ---------------------------------------------------------------------------

class _Lcg:
    def __init__(self, seed: int):
        self.s = seed

    def next(self, n: int) -> int:
        self.s = (self.s * 6364136223846793005 + 1442695040888963407) \
            % (1 << 64)
        return (self.s >> 33) % n


_VARS = ("X", "Y", "Z")


def random_inequality(rng: _Lcg, bound: int) -> str:
    """Half the time random integer coefficients on the seven joint
    entropies; half the time a random integer combination (coefficients
    -1..2) of the nine elemental forms, written out in joint entropies --
    so that valid and invalid claims both occur."""
    subsets = [s for r in (1, 2, 3) for s in combinations(_VARS, r)]
    coef: Dict[Tuple[str, ...], int] = {}
    if rng.next(2) == 0:
        for s in subsets:
            coef[s] = rng.next(2 * bound + 1) - bound
    else:
        names = list(_VARS)
        for e in II.elementals(names):
            c = rng.next(4) - 1
            for s, k in II.elemental_form(e, names).items():
                key = tuple(sorted(s, key=_VARS.index))
                coef[key] = coef.get(key, 0) + c * int(k)
    terms = [f"{c}*H({','.join(s)})" for s, c in coef.items() if c]
    if not terms:
        return "|- H(X) >= 0"
    text = " + ".join(terms).replace("+ -", "- ")
    return f"|- {text} >= 0"


def _exec_script(script: str) -> bool:
    out = io.StringIO()
    saved, sys.stdout = sys.stdout, out
    try:
        exec(compile(script, "<column-3>", "exec"), {"__name__": "c3"})
    except AssertionError:
        return False
    finally:
        sys.stdout = saved
    lines = [ln for ln in out.getvalue().splitlines() if ln.strip()]
    return bool(lines) and lines[-1].strip().endswith("VERIFIED True")


def inequality_battery(count: Optional[int] = None) -> Dict[str, object]:
    n, seed, nvars, bound = C.INEQUALITY_BATTERY
    n = count or n
    rng = _Lcg(seed)
    kinds: Dict[str, int] = {}
    unsound = undecided = script_fail = 0
    for _ in range(n):
        text = random_inequality(rng, bound)
        pr = II.parse_problem(text)
        v = II.decide(pr)
        kinds[v.kind] = kinds.get(v.kind, 0) + 1
        if v.kind == "NOT_SHANNON":
            undecided += 1
            continue
        if v.kind == "proved":
            script = DS.inequality_script(pr.names, pr.given_texts,
                                          pr.claim_text, "proved",
                                          v.certificates)
            # soundness against every extreme ray of the three-variable
            # Shannon cone (linear distributions of up to two fair bits)
            for bits, forms in II.candidate_distributions(len(pr.names)):
                if bits > 2:
                    continue
                h = II.linear_distribution_entropies(forms, pr.names)
                if II._value(pr.claims[0], h) < 0:
                    unsound += 1
                    break
        else:
            claimed = II._value(pr.claims[v.violated], v.entropies)
            script = DS.inequality_script(pr.names, pr.given_texts,
                                          pr.claim_text, "NOT_VALID", [],
                                          v.distribution, v.violated, claimed)
        if not _exec_script(script):
            script_fail += 1
    return {"inequalities": n, "kinds": kinds, "unsound": unsound,
            "undecided": undecided, "script_failures": script_fail,
            "met": unsound == 0 and undecided == 0 and script_fail == 0}


def random_code(rng: _Lcg, size: int, longest: int) -> List[str]:
    k = 2 + rng.next(size - 1)
    words = []
    for _ in range(k):
        n = 1 + rng.next(longest)
        words.append("".join(str(rng.next(2)) for _ in range(n)))
    return words


def brute_force_ambiguous(words: Sequence[str], limit: int = 14
                          ) -> Optional[str]:
    """A string of length at most ``limit`` with two parsings, found by
    enumerating codeword sequences (no dangling suffixes involved)."""
    seen: Dict[str, Tuple[int, ...]] = {}
    frontier: List[Tuple[str, Tuple[int, ...]]] = [("", ())]
    while frontier:
        nxt = []
        for s, seq in frontier:
            for i, w in enumerate(words):
                t = s + w
                if len(t) > limit:
                    continue
                q = seq + (i,)
                if t in seen and seen[t] != q:
                    return t
                if t not in seen:
                    seen[t] = q
                    nxt.append((t, q))
        frontier = nxt
    return None


def code_battery(count: Optional[int] = None) -> Dict[str, object]:
    n, seed, size, longest = C.CODE_BATTERY
    n = count or n
    rng = _Lcg(seed)
    disagree = kraft_break = construct_fail = beyond = ud_count = 0
    for _ in range(n):
        words = random_code(rng, size, longest)
        ud, _ = CT.sardinas_patterson(words)
        brute = brute_force_ambiguous(words)
        if ud:
            ud_count += 1
            if brute is not None:
                disagree += 1
            if CT.kraft_sum([len(w) for w in words], 2) > 1:
                kraft_break += 1
            pc = CT.canonical_prefix_code([len(w) for w in words], 2)
            if not CT.is_prefix_free(pc) or \
                    sorted(map(len, pc)) != sorted(map(len, words)):
                construct_fail += 1
        else:
            amb = CT.ambiguous_string(words)
            if amb is None or CT.parsings(amb[0], words) < 2 or \
                    "".join(amb[1]) != amb[0] or "".join(amb[2]) != amb[0]:
                disagree += 1
            if brute is None:
                beyond += 1           # shortest ambiguity longer than limit
                if amb is not None and len(amb[0]) <= 14:
                    disagree += 1
    return {"codes": n, "uniquely_decodable": ud_count,
            "disagreements": disagree, "kraft_violations": kraft_break,
            "construction_failures": construct_fail,
            "ambiguity_beyond_bound": beyond,
            "met": disagree == 0 and kraft_break == 0 and construct_fail == 0}


def battery_mark(count_ineq: Optional[int] = None,
                 count_codes: Optional[int] = None) -> Dict[str, object]:
    a = inequality_battery(count_ineq)
    b = code_battery(count_codes)
    return {"inequalities": a, "codes": b, "met": a["met"] and b["met"]}


# ---------------------------------------------------------------------------
# Q10: the outside set and no regression
# ---------------------------------------------------------------------------

def outside_mark() -> Dict[str, object]:
    from ..evaluation import question_set_b_cases as qc
    from ..evaluation.cases import CASES
    from . import question_frames as qf
    items = qc.outside()
    rows = []
    for idx, frag in C.OUTSIDE_P2:
        rd = qf.read(items[idx].text)
        got = qf.frame_of(items[idx].text)
        mutant = DF.mutated_outside(got[0], got[1]) if got else None
        rows.append({"index": idx, "frame": rd.frame if rd else None,
                     "answered": bool(rd and rd.answered),
                     "gate": bool(rd and rd.gate and rd.gate[0]),
                     "fragment": bool(rd and frag in rd.value),
                     "mutant_rejected": bool(mutant and
                                             not _gate(mutant.script))})
    #  Phase 120 (``explanation_cases.PREVIOUSLY_REFUSED``) answers these
    #  three with its explanation frames, tried after every other frame; the
    #  claim kept here is that no frame before them reads the three.
    saved_e = qf.EXPLANATIONS
    try:
        qf.EXPLANATIONS = False
        stays = {i: (qf.frame_of(items[i].text) is None)
                 for i in C.STAYS_REFUSED}
    finally:
        qf.EXPLANATIONS = saved_e
    taken_later = [i for i in C.STAYS_REFUSED
                   if qf.frame_of(items[i].text) is not None]
    declared = {i for i, _ in C.OUTSIDE_P2}
    texts = [(f"O{it.index:03d}", it.text) for it in items
             if it.index not in declared] + \
        [(it.id, it.query) for it in qc.set_b()] + \
        [(c.id, c.question) for c in CASES]

    def frame_name(text: str) -> Optional[str]:
        got = qf.frame_of(text)
        return got[0].name if got else None

    moved = []
    saved = qf.DERIVATIONS_TWO
    try:
        before = {}
        qf.DERIVATIONS_TWO = False
        for key, text in texts:
            before[key] = frame_name(text)
        qf.DERIVATIONS_TWO = True
        for key, text in texts:
            if frame_name(text) != before[key]:
                moved.append(key)
    finally:
        qf.DERIVATIONS_TWO = saved
    ok_rows = all(r["answered"] and r["gate"] and r["fragment"] and
                  r["mutant_rejected"] for r in rows)
    return {"rows": rows, "answered": sum(r["answered"] for r in rows),
            "of": len(rows), "stays_refused": stays,
            "taken_by_phase_120": taken_later,
            "texts_checked": len(texts), "moved": moved,
            "evaluation_cases": len(CASES),
            "met": ok_rows and all(stays.values()) and not moved}


# ---------------------------------------------------------------------------
# Q11
# ---------------------------------------------------------------------------

def lean_mark() -> Dict[str, object]:
    """Q11 (the source half; the build is ``lake build``)."""
    if not LEAN_FILE.exists():
        return {"exists": False, "met": False}
    src = LEAN_FILE.read_text(encoding="utf-8")
    code = re.sub(r"/-.*?-/", "", src, flags=re.S)
    code = re.sub(r"--[^\n]*", "", code)
    missing = [t for t in C.LEAN_THEOREMS
               if not re.search(rf"theorem\s+{t}\b", code)]
    has_sorry = bool(re.search(r"\bsorry\b", code))
    return {"exists": True, "missing": missing, "sorry": has_sorry,
            "met": not missing and not has_sorry}


def derivation_two_report(run_scripts: bool = True,
                          battery: Optional[int] = None) -> Dict[str, object]:
    q1 = inequality_marks(run_scripts)
    q2 = code_marks(run_scripts)
    q3 = rd_marks(run_scripts)
    q4 = maxent_marks(run_scripts)
    q5 = eigen_marks(run_scripts)
    q6 = other_marks(run_scripts)
    q7 = refusal_marks()
    q8 = gate_mark(q1, q2, q3, q4, q5, q6) if run_scripts else {"met": None}
    q9 = battery_mark(battery, battery)
    q10 = outside_mark()
    q11 = lean_mark()
    marks = {"Q1": q1, "Q2": q2, "Q3": q3, "Q4": q4, "Q5": q5, "Q6": q6,
             "Q7": q7, "Q8": q8, "Q9": q9, "Q10": q10, "Q11": q11}
    met = sum(1 for m in marks.values() if m.get("met"))
    return {"marks": marks, "met": met, "of": len(marks)}
