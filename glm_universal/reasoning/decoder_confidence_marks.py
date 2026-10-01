"""``glm_universal.reasoning.decoder_confidence_marks`` -- the study, measured.

``studies/DECODER_CONFIDENCE_STUDY.md`` (Phase 77) declared the marks C1-C6
before :mod:`glm_universal.reasoning.decoder_confidence` existed;
:func:`decoder_confidence_report` measures every one of them.  Kept apart from
the runtime module so that a unit that answers a query does not depend on the
study's documents.

Exactness: ``int`` masks and :class:`fractions.Fraction` only.
"""

from __future__ import annotations

from fractions import Fraction
from itertools import combinations
from typing import Dict, List, Optional, Sequence, Tuple

from ..substrate.golay_decode import decode_complete
from ..substrate.linalg import popcount
from ..substrate.mog import GOLAY_MASKS
from . import carried_fork as cf
from . import law_absorption as la
from .decoder_confidence import (CLOSED_WORLD, N, RATES, ConfidenceRefusal,
                                 agree_confidence, brute_posterior,
                                 decode_confidence, fork_bound, int_weights)

__all__ = [
    "LEAN_FILE", "LEAN_THEOREMS", "DECLARED_PROGRAMS",
    "CARRIED_FORK_FIGURES", "c1_decoder", "c2_context", "c3_second_reading",
    "c4_runtime", "c5_unchanged", "decoder_confidence_report",
]

LEAN_FILE = "RequestProject/GLM/DecoderConfidence.lean"

#: The theorems of ``RequestProject/GLM/DecoderConfidence.lean`` (mark C6).
LEAN_THEOREMS: Tuple[str, ...] = (
    "posterior_sum_one", "posterior_restrict_le",
    "equal_weight_equal_posterior", "resolved_bound", "bsc_ratio",
    "bsc_anti", "fork_confidence_bound",
)


# ===========================================================================
# 1.  THE MARKS
# ===========================================================================

def _errors_up_to_three(stride: int = 37) -> Tuple[int, ...]:
    out: List[int] = [0]
    for w in (1, 2, 3):
        pats = [sum(1 << i for i in s) for s in combinations(range(N), w)]
        out.extend(pats[::stride] if w > 1 else pats)
    return tuple(out)


def c1_decoder() -> Dict[str, object]:
    """C1: the decoder's confidence against the law and a brute-force sum."""
    words = cf.case_set(8)
    errors = _errors_up_to_three()
    checked = disagreements = 0
    by_weight: Dict[int, Dict[str, Fraction]] = {}
    for p in RATES:
        for c in words:
            for e in errors:
                r = decode_confidence(c ^ e, p)
                brute = brute_posterior((c ^ e,), r["value"], GOLAY_MASKS, p)
                checked += 1
                law = la.confidence(r["coset_weight"], p)
                if not (r["confidence"] == brute == law):
                    disagreements += 1
                by_weight.setdefault(r["coset_weight"], {})[str(p)] = law
    tie_refused = tie_equal = tie_reads = 0
    for c in words[:2]:
        for e in cf._weight4_errors()[::211]:
            tie_reads += 1
            try:
                decode_confidence(c ^ e, RATES[0])
            except ConfidenceRefusal as exc:
                tie_refused += exc.name == "TIE"
            six = decode_complete(c ^ e).candidates
            post = {brute_posterior((c ^ e,), x, GOLAY_MASKS, RATES[0])
                    for x in six}
            tie_equal += len(six) == 6 and len(post) == 1
    return {"reads_checked": checked, "disagreements": disagreements,
            "confidence_by_weight": {d: dict(v) for d, v in
                                     sorted(by_weight.items())},
            "tie_reads": tie_reads, "tie_refused": tie_refused,
            "tie_six_equal": tie_equal,
            "passed": (disagreements == 0 and checked > 0
                       and tie_refused == tie_reads == tie_equal)}


def c2_context(sizes: Sequence[int] = (2, 4, 8, 16, 32),
               stride: int = 1) -> Dict[str, object]:
    """C2: every resolved fork of K1 carries a confidence equal to the
    brute-force posterior over its case set and at least the proved bound."""
    errors = cf._weight4_errors()[::stride]
    rows = []
    ok = True
    for k in sizes:
        cases = cf.case_set(k)
        for p in RATES:
            weights = int_weights(p)
            q = 1 - p
            lik = tuple(p ** d * q ** (N - d) for d in range(N + 1))
            resolved = below = bound_fail = brute_fail = 0
            least: Optional[Fraction] = None
            min_gap: Optional[int] = None
            floor = fork_bound(k, 2, p)
            for c in cases:
                for e in errors:
                    y = c ^ e
                    ds = [popcount(y ^ s) for s in cases]
                    m = min(ds)
                    if ds.count(m) != 1:
                        continue
                    resolved += 1
                    conf = Fraction(weights[m], sum(weights[d] for d in ds))
                    brute = lik[m] / sum((lik[d] for d in ds), Fraction(0))
                    brute_fail += conf != brute
                    others = [d for d in ds if d != m]
                    if others:
                        g = min(others) - m
                        min_gap = g if min_gap is None else min(min_gap, g)
                    bound_fail += conf < floor
                    below += conf < Fraction(99, 100)
                    least = conf if least is None or conf < least else least
            ok = ok and brute_fail == 0 and bound_fail == 0
            rows.append({"k": k, "rate": p, "resolved": resolved,
                         "least": least, "bound": floor,
                         "least_gap": min_gap, "below_99": below,
                         "brute_disagreements": brute_fail,
                         "below_bound": bound_fail})
    return {"rows": rows, "stride": stride,
            "resolved": sum(r["resolved"] for r in rows),
            "assumption": CLOSED_WORLD, "passed": ok}


def c3_second_reading(brute_stride: int = 16) -> Dict[str, object]:
    """C3: the second reading's confidence over K2's 4,224 double reads."""
    words, errs = cf.x1_probe()
    pairs: List[Tuple[int, int, int]] = []
    for c in words:
        for i, j in combinations(range(len(errs)), 2):
            pairs.append((c, c ^ errs[i], c ^ errs[j]))
    rows = []
    ok = True
    for p in RATES:
        answered = wrong = brute_checked = brute_fail = 0
        least: Optional[Fraction] = None
        for n, (c, r1, r2) in enumerate(pairs):
            try:
                r = agree_confidence((r1, r2), p)
            except ConfidenceRefusal:
                continue
            answered += 1
            wrong += r["value"] != c
            conf = r["confidence"]
            least = conf if least is None or conf < least else least
            if n % brute_stride == 0:
                brute_checked += 1
                brute_fail += conf != brute_posterior((r1, r2), r["value"],
                                                      GOLAY_MASKS, p)
        ok = ok and brute_fail == 0 and answered == len(pairs) and wrong == 0
        rows.append({"rate": p, "pairs": len(pairs), "answered": answered,
                     "wrong": wrong, "least": least,
                     "brute_checked": brute_checked,
                     "brute_disagreements": brute_fail})
    # the witness: two reads whose forks keep the truth and truth + octad
    octad = next(w for w in GOLAY_MASKS if popcount(w) == 8)
    sup = [i for i in range(N) if (octad >> i) & 1]
    e1 = sum(1 << i for i in sup[:4])
    e2 = sum(1 << i for i in sup[4:])
    c0 = GOLAY_MASKS[0]
    witness = {str(p): tuple(brute_posterior((c0 ^ e1, c0 ^ e2), x,
                                             GOLAY_MASKS, p)
                             for x in (c0, c0 ^ octad)) for p in RATES}
    halves = {x for pair in witness.values() for x in pair}
    witness_equal = all(a == b for a, b in witness.values())
    try:
        agree_confidence((c0 ^ e1, c0 ^ e2), RATES[0])
        witness_refused = False
    except ConfidenceRefusal as exc:
        witness_refused = exc.name == "AMBIGUOUS"
    witness_half = halves == {Fraction(1, 2)}
    #  As declared, C3 asked for exactly 1/2 each.  Measured: the two
    #  survivors are exactly equal at every rate, but each is below 1/2,
    #  because the other codewords keep some of the mass; the declared clause
    #  is recorded as missed rather than re-read.
    return {"rows": rows, "witness_refused": witness_refused,
            "witness_each_half": witness_half,
            "witness_equal": witness_equal, "witness_posteriors": witness,
            "passed": ok and witness_refused and witness_half}


#: The declared programs of C4: ``(source, "answer")`` or ``(source, NAME)``.
#: ``e1``/``e2``/``octad`` are substituted with an octad split in two
#: tetrads (the K2 witness).
DECLARED_PROGRAMS: Tuple[Tuple[str, str], ...] = (
    ("decode_confidence(Fraction(1, 100), golay_encode(5))", "answer"),
    ("decode_confidence(Fraction(1, 100), golay_encode(5) ^ 0b111)",
     "answer"),
    ("decode_confidence(Fraction(1, 10), golay_encode(5) ^ 0b111)", "answer"),
    ("decode_confidence(Fraction(1, 100), golay_encode(5) ^ 0b1111)", "TIE"),
    ("decode_confidence(Fraction(1, 100), golay_encode(1) ^ 0b1111, "
     "golay_encode(1), golay_encode(2))", "answer"),
    ("decode_confidence(Fraction(1, 10), golay_encode(1) ^ 0b1111, "
     "golay_encode(1), golay_encode(2), golay_encode(3), golay_encode(4))",
     "answer"),
    ("decode_confidence(Fraction(1, 100), golay_encode(1) ^ 0b1111, "
     "golay_encode(2), golay_encode(3))", "UNCORRECTABLE"),
    ("decode_confidence(Fraction(1, 100), {e1}, 0, {octad})", "AMBIGUOUS"),
    ("decode_confidence(Fraction(1, 2), golay_encode(5))",
     "RATE_OUT_OF_RANGE"),
    ("decode_confidence(0, golay_encode(5))", "RATE_OUT_OF_RANGE"),
    ("decode_confidence(Fraction(1, 100), 0b1111, 5)", "OUTSIDE_SUBSTRATE"),
    ("c = golay_encode(5)\n"
     "agree_confidence(Fraction(1, 100), c ^ 0b1111, "
     "c ^ 0b111000000000000000000001)", "answer"),
    ("agree_confidence(Fraction(1, 100), {e1}, {e2})", "AMBIGUOUS"),
    ("agree_confidence(Fraction(1, 20), golay_encode(9) ^ 0b11)", "answer"),
    ("c = decode_confidence(Fraction(1, 100), golay_encode(3) ^ 0b11)\n"
     "c > Fraction(99, 100)", "answer"),
)


def _witness_masks() -> Dict[str, int]:
    octad = next(w for w in GOLAY_MASKS if popcount(w) == 8)
    sup = [i for i in range(N) if (octad >> i) & 1]
    return {"octad": octad, "e1": sum(1 << i for i in sup[:4]),
            "e2": sum(1 << i for i in sup[4:])}


def c4_runtime() -> Dict[str, object]:
    """C4: the two dialect builtins on the declared programs, each answer
    checked by its fresh-interpreter script."""
    from . import python_speech as sp
    masks = _witness_masks()
    rows = []
    for source, expected in DECLARED_PROGRAMS:
        src = source.format(**masks)
        payload = sp.speak(src)
        got = payload.refusal or "answer"
        verified = None
        if got == "answer":
            verified = bool(sp.verify_payload(payload)["verified"])
        rows.append({"source": src, "expected": expected, "got": got,
                     "value": payload.value, "verified": verified,
                     "as_declared": got == expected
                     and verified in (None, True)})
    wrong = sum(1 for r in rows if not r["as_declared"])
    return {"rows": rows, "programs": len(rows),
            "as_declared": len(rows) - wrong, "wrong": wrong,
            "passed": wrong == 0}


#: The carried fork's figures as ``studies/CARRIED_FORK_STUDY.md`` states
#: them: K1 answers 592,268 of 658,812 reads, K2 4,224 of 4,224, both with 0
#: wrong.  C5 reads them again.
CARRIED_FORK_FIGURES = {"K1": (658812, 592268, 0), "K2": (4224, 4224, 0)}


def c5_unchanged() -> Dict[str, object]:
    """C5: the carried fork's K1 and K2 figures, read again.  (The Python
    speech programs and the evaluation are the release's instruments.)"""
    k1 = cf.k1_context()
    k2 = cf.k2_second_reading()
    now = {"K1": (k1["reads"], k1["answered"], k1["wrong"]),
           "K2": (k2["double_reads"], k2["answered"], k2["wrong"])}
    return {"figures": now, "stated": CARRIED_FORK_FIGURES,
            "passed": now == CARRIED_FORK_FIGURES}


def _lean_has(names: Sequence[str]) -> bool:
    """Whether the Lean file states every named theorem and holds no
    ``sorry`` (the build itself is the release's Lean instrument)."""
    import re
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "glm_lean" / LEAN_FILE
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return "sorry" not in text and all(
        re.search(rf"\btheorem {n}\b", text) for n in names)


def decoder_confidence_report(full: bool = True) -> Dict[str, object]:
    """Every mark of the study, measured."""
    c1 = c1_decoder()
    c2 = c2_context(stride=1 if full else 23)
    c3 = c3_second_reading(brute_stride=16 if full else 128)
    c4 = c4_runtime()
    c5 = c5_unchanged()
    c6 = {"file": LEAN_FILE, "theorems": list(LEAN_THEOREMS),
          "passed": _lean_has(LEAN_THEOREMS)}
    marks = {"C1": c1["passed"], "C2": c2["passed"], "C3": c3["passed"],
             "C4": c4["passed"], "C5": c5["passed"], "C6": c6["passed"]}
    return {"C1": c1, "C2": c2, "C3": c3, "C4": c4, "C5": c5, "C6": c6,
            "marks": marks, "met": sum(marks.values()),
            "of": len(marks), "full": full}
