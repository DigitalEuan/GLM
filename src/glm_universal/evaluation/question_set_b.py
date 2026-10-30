"""``glm_universal.evaluation.question_set_b`` -- the Phase 89 run of the two
outside question sets, scored, with the Capability Failure Matrix.

Every question goes through the **router** (:func:`glm_universal.runtime.
router.route`) -- the same path ``GLM.py -q`` takes since K1 -- so the score
is the machine's, not a frame's in isolation.

Scores
------
*Protocol* (the question set's own scoring: +1 correct, 0 refusal, -1
confidently wrong) against the file's expectations, and *audited* against
the expectations of :data:`~glm_universal.evaluation.question_set_b_cases.
SET_B_AUDIT`, which correct the file where the machine shows a premise
false or a code name foreign.  For a REFUSAL item, +1 needs the right code; a
refusal under another code scores 0 (a refusal), an answer scores -1.  For a
VERIFIED_TRUE item, +1 needs an answer containing the item's value fragment
(:data:`VALUE_FRAGMENTS`); a refusal scores 0.

Outside O1 has no answer key.  A framed answer counts +1 only when its
column-3 script verified it **and** it was audited by hand
(``studies/QUESTION_SET_B_STUDY.md`` §3 lists the audit); every other
question is a refusal (0) and is classed by :data:`BOUNDARY`.

The contract matrix on the question sets
----------------------------------------
:func:`variant_run` re-reads every question a frame reads under each of the
four candidate-P variants (A control, B upper-credible, C session-marginal,
D combined) and reports which verdicts change.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Dict, List, Optional, Tuple

from . import question_set_b_cases as qc

__all__ = ["VALUE_FRAGMENTS", "OUTSIDE_AUDITED", "run_set_b", "run_outside",
           "variant_run", "report"]

#: For the VERIFIED_TRUE items: a fragment the answer must contain.
VALUE_FRAGMENTS: Dict[str, str] = {
    "O1-001": "retention 0.9796", "O1-007": "power = 500",
    "O1-011": "ENTAILS over the integers", "O1-012": "r = 13",
    "O1-013": "x = 2, y = -1",
}

#: Outside questions whose framed answer was audited by hand (index ->
#: the fragment the answer must contain).
OUTSIDE_AUDITED: Dict[int, str] = {
    1: "0 < K < 48", 2: "1/5 p.u.", 5: "-1 < Re(s) < 3", 6: "-1/5 - j2/5",
    9: "Z = N + P = -2", 13: "m1 = 3", 15: "P = 1/4", 20: "311.02",
    21: "1.0481", 22: "3*R*ln(3/2)", 25: "x = 0.4612", 31: "1.896361",
    34: "K_c < 5/2", 38: "completely controllable", 40: "200, 300 Hz",
    41: "1/2 < |z| < 3", 42: "[1, 1, 1, -3]", 44: "(6 - 2 z^-1)",
    46: "no aliasing", 48: "h0 = 86/161", 50: "H(X,Y) = 3/2",
    51: "L = 7/4", 53: "0.50008", 57: "1/2 bits", 58: "P = (6, 4, 0)",
    90: "quasi-perfect", 103: "1 time in 6",
}


def _verdict(r) -> Tuple[bool, Optional[str], str]:
    """``(answered, code, text)`` of a routed verdict."""
    if r.surface == "frames":
        rd = r.payload
        return rd.answered, rd.code, rd.body()
    code = None
    m = re.match(r"refused:\s*([A-Z_]+):", r.text or "")
    if m:
        code = m.group(1)
    return bool(r.answered), code, r.text or ""


def _score(expected: str, code: str, answered: bool, got_code: Optional[str],
           text: str, fragment: Optional[str]) -> int:
    if expected == "REFUSAL":
        if answered:
            return -1
        return 1 if got_code == code else 0
    if not answered:
        return 0
    return 1 if fragment is None or fragment in text else -1


def run_set_b(session=None) -> List[Dict[str, object]]:
    from ..runtime import router
    from ..runtime.session import GeometricSession
    session = session or GeometricSession()
    rows = []
    for it in qc.set_b():
        r = router.route(session, it.query)
        answered, code, text = _verdict(r)
        frag = VALUE_FRAGMENTS.get(it.id)
        aud = qc.SET_B_AUDIT.get(it.id, (it.expected_status, it.refusal_code,
                                         ""))
        rows.append({
            "id": it.id, "category": it.category, "surface": r.surface,
            "frame": getattr(r.payload, "frame", None)
            if r.surface == "frames" else None,
            "expected": (it.expected_status, it.refusal_code),
            "audited": aud[:2], "audit_note": aud[2],
            "answered": answered, "code": code,
            "headline": text.splitlines()[0][:240] if text else "",
            "gate": getattr(r.payload, "gate", None)
            if r.surface == "frames" else None,
            "protocol": _score(it.expected_status, it.refusal_code, answered,
                               code, text, frag),
            "audited_score": _score(aud[0], aud[1], answered, code, text,
                                    frag if aud[0] == "VERIFIED_TRUE"
                                    else None),
        })
    return rows


def run_outside(session=None) -> List[Dict[str, object]]:
    from ..runtime import router
    from ..runtime.session import GeometricSession
    session = session or GeometricSession()
    rows = []
    for it in qc.outside():
        try:
            r = router.route(session, it.text)
            answered, code, text = _verdict(r)
            surface = r.surface
            frame = getattr(r.payload, "frame", None) \
                if surface == "frames" else None
            gate = getattr(r.payload, "gate", None) \
                if surface == "frames" else None
        except Exception as exc:                       # pragma: no cover
            answered, code, text, surface, frame, gate = (
                False, "EXCEPTION", repr(exc), "error", None, None)
        frag = OUTSIDE_AUDITED.get(it.index)
        correct = bool(frame and gate and gate[0] and frag
                       and frag in text)
        # a framed refusal that the audit expects (Nyquist) is correct too
        cls = "F" if correct else qc.BOUNDARY.get(it.index, "?")
        rows.append({
            "index": it.index, "section": it.section,
            "difficulty": it.difficulty, "number": it.number,
            "surface": surface, "frame": frame,
            "expected_frame": qc.EXPECTED_FRAME.get(it.index),
            "answered": answered, "code": code, "gate": gate,
            "headline": text.splitlines()[0][:240] if text else "",
            "class": cls,
            "score": 1 if correct else (-1 if frame and answered and frag
                                        and frag not in text else 0),
        })
    return rows


def variant_run() -> Dict[str, object]:
    """Every question a frame reads, re-read under each candidate-P variant
    (a fresh session of frame reads per variant, in file order)."""
    from ..runtime import question_frames as qf
    texts = [("B", it.id, it.query) for it in qc.set_b()] + \
        [("O1", f"O{it.index:03d}", it.text) for it in qc.outside()]
    texts = [x for x in texts if qf.reads(x[2])]
    out: Dict[str, object] = {"items": len(texts), "variants": {}}
    base = None
    saved = (qf.CONTRACT_VARIANT, list(qf.SESSION_READS))
    try:
        for v in ("A", "B", "C", "D"):
            qf.CONTRACT_VARIANT = v
            qf.SESSION_READS.clear()
            verdicts = {}
            for src, key, text in texts:
                rd = qf.read(text, gate=False)
                verdicts[key] = (rd.verdict, rd.code)
            out["variants"][v] = {
                "answered": sum(1 for x in verdicts.values()
                                if x[0] == "ANSWER"),
                "refused": sum(1 for x in verdicts.values()
                               if x[0] == "REFUSED"),
                "codes": dict(Counter(x[1] for x in verdicts.values()
                                      if x[1])),
                "verdicts": verdicts,
            }
            base = base or verdicts
        out["differ_from_A"] = {
            v: sorted(k for k in base
                      if out["variants"][v]["verdicts"][k] != base[k])
            for v in ("B", "C", "D")}
    finally:
        qf.CONTRACT_VARIANT = saved[0]
        qf.SESSION_READS[:] = saved[1]
    return out


def report(session=None, variants: bool = True) -> Dict[str, object]:
    b = run_set_b(session)
    o = run_outside(session)
    by_class = Counter(r["class"] for r in o)
    by_section: Dict[str, Counter] = {}
    for r in o:
        by_section.setdefault(r["section"], Counter())[r["class"]] += 1
    out = {
        "set_b": {"rows": b,
                  "protocol": sum(r["protocol"] for r in b),
                  "audited": sum(r["audited_score"] for r in b),
                  "plus": sum(1 for r in b if r["protocol"] == 1),
                  "minus": sum(1 for r in b if r["protocol"] == -1),
                  "audited_plus": sum(1 for r in b
                                      if r["audited_score"] == 1),
                  "audited_minus": sum(1 for r in b
                                       if r["audited_score"] == -1)},
        "outside": {"rows": o, "score": sum(r["score"] for r in o),
                    "framed_correct": by_class.get("F", 0),
                    "wrong": sum(1 for r in o if r["score"] == -1),
                    "classes": dict(by_class),
                    "by_section": {k: dict(v) for k, v in by_section.items()},
                    "surfaces": dict(Counter(r["surface"] for r in o))},
    }
    if variants:
        out["variants"] = variant_run()
    return out
