"""``glm_universal.evaluation.pocklington_certificate_cases`` -- the Phase 140
cases (``studies/POCKLINGTON_CERTIFICATE_STUDY.md``).

Phase 139 left a prime whose ``p - 1`` does not split within the work budget
refused (``2^521 - 1``).  Phase 140 adds the Pocklington certificate, which
needs only a factored part ``F`` of ``p - 1`` with ``p < (F + 1)^2``
(``RequestProject/GLM/PocklingtonCertificate.lean``, ``pocklington_sound``).

:data:`HELD_OUT` was written and committed **before** the Pocklington search
was run on any of its numbers, and its expected verdicts come from published
lists, not from the new code:

* factorial primes ``n! - 1``: prime for ``n = 30, 32, 33, 38, 94, 166``
  (OEIS A002982), so ``31! - 1`` and ``34! - 1`` are composite;
* primorial primes ``p# - 1``: prime for ``p = 41, 89, 317, 337`` (OEIS
  A006794), so ``43# - 1`` is composite;
* repunits ``(10^n - 1)/9``: prime for ``n = 19, 23`` (OEIS A004023), and
  ``n = 21`` is composite (digit sum 21);
* Mersenne numbers: ``2^523 - 1`` and ``2^541 - 1`` are composite (523 and
  541 are not on the published list of Mersenne prime exponents).

The questions state these numbers as decimal literals, because the stepwise
reader has no factorial or primorial; a question is answered right, refused,
or answered **wrong** -- and wrong is the only outcome the marks forbid.

:data:`KNOWN` are the numbers seen in exploration before this set was
written (``2^521 - 1`` certified; ``2^607 - 1``, ``2^1279 - 1``,
``2^2203 - 1`` and ``2^2281 - 1`` refused by the work budget), declared so
they are not counted as held out.
"""

from __future__ import annotations

from math import factorial, isqrt
from typing import Dict, List, Optional, Tuple


def _primorial(p: int) -> int:
    out = 1
    for q in range(2, p + 1):
        if all(q % d for d in range(2, isqrt(q) + 1)):
            out *= q
    return out


def _repunit(n: int) -> int:
    return (10 ** n - 1) // 9


#: ``(id, name, n, published verdict)`` -- written before the search ran.
HELD_OUT: Tuple[Tuple[str, str, int, str], ...] = (
    ("k01", "30!-1", factorial(30) - 1, "prime"),
    ("k02", "32!-1", factorial(32) - 1, "prime"),
    ("k03", "33!-1", factorial(33) - 1, "prime"),
    ("k04", "38!-1", factorial(38) - 1, "prime"),
    ("k05", "94!-1", factorial(94) - 1, "prime"),
    ("k06", "166!-1", factorial(166) - 1, "prime"),
    ("k07", "31!-1", factorial(31) - 1, "not prime"),
    ("k08", "34!-1", factorial(34) - 1, "not prime"),
    ("k09", "41#-1", _primorial(41) - 1, "prime"),
    ("k10", "89#-1", _primorial(89) - 1, "prime"),
    ("k11", "317#-1", _primorial(317) - 1, "prime"),
    ("k12", "337#-1", _primorial(337) - 1, "prime"),
    ("k13", "43#-1", _primorial(43) - 1, "not prime"),
    ("k14", "R19", _repunit(19), "prime"),
    ("k15", "R23", _repunit(23), "prime"),
    ("k16", "R21", _repunit(21), "not prime"),
    ("k17", "2^523-1", 2 ** 523 - 1, "not prime"),
    ("k18", "2^541-1", 2 ** 541 - 1, "not prime"),
)

#: The second held-out set (Phase 140, part B), written and committed after
#: the first run and **before** the N+1 (Lucas) certificate was written.  The
#: first run's five refused primes are all of the forms ``n! - 1`` and
#: ``p# - 1``, whose ``n + 1`` splits into small primes while ``n - 1`` does
#: not; an ``n + 1`` certificate was chosen because of that observation, so
#: it is scored on fresh numbers of forms whose ``n + 1`` is smooth, with
#: verdicts from published lists:
#:
#: * ``3 * 2^n - 1``: prime for ``n = 143, 206, 216, 306, 324, 391, 458, 470,
#:   827`` (OEIS A002235), composite for ``n = 144`` and ``n = 207``;
#: * ``p# - 1``: prime for ``p = 991, 1873`` (OEIS A006794);
#: * ``n! - 1``: prime for ``n = 324, 379`` (OEIS A002982), composite for
#:   ``n = 325``.
HELD_OUT_B: Tuple[Tuple[str, str, int, str], ...] = tuple(
    [(f"b{i + 1:02d}", f"3*2^{k}-1", 3 * 2 ** k - 1, "prime")
     for i, k in enumerate((143, 206, 216, 306, 324, 391, 458, 470, 827))]
    + [("b10", "3*2^144-1", 3 * 2 ** 144 - 1, "not prime"),
       ("b11", "3*2^207-1", 3 * 2 ** 207 - 1, "not prime"),
       ("b12", "991#-1", _primorial(991) - 1, "prime"),
       ("b13", "1873#-1", _primorial(1873) - 1, "prime"),
       ("b14", "324!-1", factorial(324) - 1, "prime"),
       ("b15", "379!-1", factorial(379) - 1, "prime"),
       ("b16", "325!-1", factorial(325) - 1, "not prime")])

#: Seen in exploration before :data:`HELD_OUT` was written.
KNOWN: Tuple[Tuple[str, int, str], ...] = (
    ("2^521-1", 2 ** 521 - 1, "prime"),
    ("2^607-1", 2 ** 607 - 1, "prime"),
    ("2^1279-1", 2 ** 1279 - 1, "prime"),
)

LEAN_FILE = "RequestProject/GLM/PocklingtonCertificate.lean"
LEAN_THEOREMS = ("prime_pow_dvd_of_witness", "prod_dvd_of_pow_dvd",
                 "prime_of_factor_bound", "checkPEntry_sound",
                 "checkPChain_sound", "pocklington_sound",
                 "prime_2_521_sub_one")

#: Part B's Lean file (the N+1 certificate and the mixed chain).
LEAN_FILE_B = "RequestProject/GLM/LucasCertificate.lean"
LEAN_THEOREMS_B = ("toQuad_qpow", "isUnit_of_qnorm", "card_quadRing",
                   "lucas_prime", "checkMChain_sound", "mixed_sound",
                   "prime_33_factorial_sub_one")

#: Part B's mark Q7, declared before part B's search was run on
#: :data:`HELD_OUT_B`: no wrong verdict, and at least two thirds of its primes
#: certified.
Q7_SHARE = (2, 3)


def question(n: int) -> str:
    return f"is {n} prime"


def tampered(cert: dict) -> List[Tuple[str, dict]]:
    """Altered copies of a Pocklington or mixed certificate, each proving
    nothing."""
    import copy
    out: List[Tuple[str, dict]] = []
    if cert.get("kind") == "lucas" and len(cert["chain"][-1]) == 3:
        c = copy.deepcopy(cert)
        c["chain"][-1][2] = c["chain"][-1][2][:-1]     # drop a factor of p+1
        out.append(("cert-drop", c))
        c = copy.deepcopy(cert)
        c["chain"][-1][2][0][1] += 1                   # exponent too high
        out.append(("cert-exponent", c))
        c = copy.deepcopy(cert)
        c["chain"][-1][1] = 2                          # P = 2: X - 1 nilpotent
        out.append(("cert-p", c))
        c = copy.deepcopy(cert)
        c["chain"] = c["chain"][-1:]                   # no earlier entries
        out.append(("cert-unproved", c))
        c = copy.deepcopy(cert)
        c["chain"] = c["chain"][:-1]                   # about another number
        out.append(("cert-other", c))
        return out
    if cert.get("kind") not in ("pocklington", "lucas"):
        return out
    last = cert["chain"][-1]
    c = copy.deepcopy(cert)
    c["chain"][-1][1] = c["chain"][-1][1][:1]          # too small a part
    if c["chain"][-1][1] != last[1]:
        out.append(("cert-short", c))
    c = copy.deepcopy(cert)
    c["chain"][-1][1][0][2] = 1                        # base 1: gcd(0, p) = p
    out.append(("cert-base", c))
    c = copy.deepcopy(cert)
    c["chain"][-1][1] = c["chain"][-1][1] + c["chain"][-1][1][:1]  # repeat
    out.append(("cert-repeat", c))
    c = copy.deepcopy(cert)
    c["chain"][-1][1][-1][1] += 1                      # exponent too high
    out.append(("cert-exponent", c))
    c = copy.deepcopy(cert)
    c["chain"] = c["chain"][-1:]                       # no earlier entries
    out.append(("cert-unproved", c))
    c = copy.deepcopy(cert)
    c["chain"] = c["chain"][:-1]                       # about another number
    out.append(("cert-other", c))
    return out


class flags:
    """Set the Phase 140 controls for a block, restoring them after."""

    def __init__(self, pocklington: bool, lucas: bool,
                 elliptic: bool = False) -> None:
        # Phase 141's elliptic stage is held off by default, so this round's
        # measurement still measures the certifier as Phase 140 declared it.
        self.want = (pocklington, lucas, elliptic)

    def __enter__(self):
        from ..reasoning import primality_certificate as pc
        self.saved = (pc.POCKLINGTON, pc.LUCAS, pc.ELLIPTIC)
        pc.POCKLINGTON, pc.LUCAS, pc.ELLIPTIC = self.want
        return self

    def __exit__(self, *exc):
        from ..reasoning import primality_certificate as pc
        pc.POCKLINGTON, pc.LUCAS, pc.ELLIPTIC = self.saved
        return False


def _verdict_with(n: int, pocklington: bool,
                  lucas: bool = False) -> Tuple[str, Optional[dict]]:
    from ..reasoning import primality_certificate as pc
    with flags(pocklington, lucas):
        try:
            v, cert = pc.verdict(n)
            return v, cert
        except pc.NoCertificate:
            return "refuse", None


def measure(scripts: bool = True) -> dict:
    """The marks Q1-Q6 of ``studies/POCKLINGTON_CERTIFICATE_STUDY.md`` §4."""
    import random
    import time
    from pathlib import Path
    from ..reasoning import primality_certificate as pc
    from ..reasoning import stepwise_script as ss
    from ..runtime import router
    from ..runtime import stepwise as sw
    from ..runtime.session import GeometricSession
    from . import primality_certificate_cases as pcc
    from . import stepwise_cases as sc_cases

    marks: Dict[str, dict] = {}
    session = GeometricSession()

    # Q1 -- the Lean file
    lean = Path(__file__).resolve().parents[2] / "lean" / LEAN_FILE
    text = lean.read_text(encoding="utf-8") if lean.exists() else ""
    lean_b = lean.parent / Path(LEAN_FILE_B).name
    text_b = lean_b.read_text(encoding="utf-8") if lean_b.exists() else ""
    missing = [t for t in LEAN_THEOREMS if f"theorem {t} " not in text] + \
        [t for t in LEAN_THEOREMS_B if f"theorem {t} " not in text_b]
    sorry = "sorry" in text or "sorry" in text_b
    marks["Q1"] = {"file": f"{LEAN_FILE}, {LEAN_FILE_B}", "missing": missing,
                   "sorry": sorry,
                   "met": bool(text) and bool(text_b) and not missing
                   and not sorry}

    # Q2 -- the held-out numbers: certify() with and without Pocklington,
    # and the question through the router
    # (part A as registered: the N+1 certificate off; the column "with N+1"
    # is post hoc, since part B was chosen from this set's refusals)
    rows = []
    for cid, name, n, want in HELD_OUT:
        t0 = time.perf_counter()
        before, _ = _verdict_with(n, False)
        after, cert = _verdict_with(n, True)
        with flags(True, False):
            r = router.route(session, question(n))
        routed = pcc.answer_of(r)
        with_lucas, _ = _verdict_with(n, True, True)
        rows.append({"id": cid, "n": name, "want": want, "phase139": before,
                     "phase140": after, "routed": routed,
                     "with_lucas": with_lucas,
                     "kind": cert["kind"] if cert else None,
                     "seconds": round(time.perf_counter() - t0, 3)})
    wrong = [r for r in rows
             if any(r[k] not in ("refuse", r["want"])
                    for k in ("phase139", "phase140", "routed", "with_lucas"))]
    gap = [r for r in rows if r["want"] == "prime" and r["phase139"] == "refuse"]
    closed = [r for r in gap if r["phase140"] == "prime"]
    routed_ok = [r for r in rows if r["routed"] == r["phase140"]]
    marks["Q2"] = {"numbers": len(rows), "wrong": wrong,
                   "phase139_refused_primes": len(gap),
                   "certified_now": len(closed),
                   "routed_agree": len(routed_ok), "rows": rows,
                   "with_lucas_certified": sum(
                       r["with_lucas"] == "prime" for r in gap),
                   "met": not wrong and len(routed_ok) == len(rows)
                   and 2 * len(closed) >= len(gap)}

    # Q3 -- column 3 and the step gate on every Pocklington chain, the
    # declared mutations, and the tampered certificates
    if scripts:
        from ..runtime.python_tct import run_column3
        from ..runtime.tct_engine import package_root
        root = str(package_root())
        chains = verified = built = caught = 0
        tampers = gate_caught = script_caught = 0
        qs = [question(n) for _c, _nm, n, _w in HELD_OUT] + \
            ["is 2 to the power 521 minus 1 prime",
             "is 2 to the power 607 minus 1 prime"] + \
            [question(n) for _c, _nm, n, _w in HELD_OUT_B[:3]]
        for q in qs:
            a = sw.answer(session, q)
            if not a.answered:
                continue
            certified = [s for s in a.chain.steps if s.op == "prime"
                         and s.detail.get("certificate", {}).get("kind")
                         in ("pocklington", "lucas")]
            if not certified:
                continue
            chains += 1
            verified += bool(run_column3(ss.render_script(a.chain, root))[
                "verified"])
            for _kind, data in ss.mutants(a.chain).items():
                built += 1
                caught += not run_column3(ss.render_script(
                    a.chain, root, data))["verified"]
            for s in certified:
                for _kind, bad in tampered(dict(s.detail["certificate"])):
                    tampers += 1
                    detail = dict(s.detail, certificate=bad)
                    t = ss.Step(s.index, s.op, s.inputs, s.value, s.label,
                                detail, s.origin)
                    steps = [t if x is s else x for x in a.chain.steps]
                    gate_caught += not ss.step_check(t, steps)[0]
                    data = ss.chain_data(a.chain)
                    data["steps"][s.index - 1] = dict(
                        t.as_dict(), column1=ss.sentence(t),
                        column2=ss.equation(t, steps))
                    script_caught += not run_column3(ss.render_script(
                        a.chain, root, data))["verified"]
        marks["Q3"] = {"chains": chains, "verified": verified,
                       "mutants": built, "caught": caught,
                       "tampered": tampers, "gate_caught": gate_caught,
                       "script_caught": script_caught,
                       "met": chains > 0 and verified == chains
                       and caught == built and gate_caught == tampers
                       and script_caught == tampers}
    else:
        marks["Q3"] = {"skipped": True, "met": False}

    # Q4 -- the control: Phase 139's held-out questions answer as Phase 139
    # recorded with Pocklington off; with it on, only h17 moves, and it moves
    # to the published verdict
    moved_off, moved_on = [], []
    for cid, q, want in pcc.HELD_OUT:
        expect139 = "refuse" if want is None else want
        with flags(False, False):
            off = pcc.answer_of(router.route(session, q))
        with flags(True, True):
            on = pcc.answer_of(router.route(session, q))
        if off != expect139:
            moved_off.append(cid)
        if on != expect139:
            moved_on.append((cid, on))
    marks["Q4"] = {"questions": len(pcc.HELD_OUT), "moved_off": moved_off,
                   "moved_on": moved_on,
                   "met": not moved_off and moved_on == [("h17", "prime")]}

    # Q5 -- the kernel instance is the tool's own certificate
    cert = pc.certify(2 ** 521 - 1)
    present = cert["kind"] == "pocklington" and all(
        f"({p}, [" + ", ".join(f"({q}, {e}, {a})" for q, e, a in fs) + "])"
        in text for p, fs in cert["chain"])
    cert_b = pc.certify(factorial(33) - 1)

    def lean_entry(e) -> str:
        if len(e) == 2:
            return f".pock {e[0]} [" + ", ".join(
                f"({q}, {x}, {a})" for q, x, a in e[1]) + "]"
        return f".lucas {e[0]} {e[1]} [" + ", ".join(
            f"({q}, {x})" for q, x in e[2]) + "]"
    present_b = cert_b["kind"] == "lucas" and all(
        lean_entry(e) in text_b for e in cert_b["chain"])
    marks["Q5"] = {"kind": cert["kind"], "entries": len(cert["chain"]),
                   "in_lean": present, "kind_b": cert_b["kind"],
                   "entries_b": len(cert_b["chain"]), "in_lean_b": present_b,
                   "met": present and present_b}

    # Q6 -- non-interference: every number Phase 139 certified keeps the
    # same certificate, and the composition corpus answers as before
    rng = random.Random(139)
    ns = [10 ** 12 + k for k in range(1, 201)] + \
        [rng.randrange(10 ** 12, 10 ** 13) for _ in range(100)] + \
        [2 ** p - 1 for p in (61, 89, 107, 127)]
    changed = [n for n in ns
               if _verdict_with(n, False) != _verdict_with(n, True, True)]
    corpus = [q for _cid, q, *_ in sc_cases.COMPOSITION_CASES]
    with flags(False, False):
        before = [sw.answer(session, q).summary() for q in corpus]
    after = [sw.answer(session, q).summary() for q in corpus]
    moved = [q for q, b, a in zip(corpus, before, after) if b != a]
    marks["Q6"] = {"numbers": len(ns), "changed": changed,
                   "corpus": len(corpus), "moved": moved,
                   "met": not changed and not moved}

    # Q7 -- part B's held-out set, every control on
    rows_b = []
    for cid, name, n, want in HELD_OUT_B:
        t0 = time.perf_counter()
        before, _ = _verdict_with(n, True, False)
        after, cert = _verdict_with(n, True, True)
        with flags(True, True):
            routed = pcc.answer_of(router.route(session, question(n)))
        rows_b.append({"id": cid, "n": name, "want": want,
                       "without": before, "phase140": after,
                       "routed": routed,
                       "kind": cert["kind"] if cert else None,
                       "seconds": round(time.perf_counter() - t0, 3)})
    wrong_b = [r for r in rows_b
               if any(r[k] not in ("refuse", r["want"])
                      for k in ("without", "phase140", "routed"))]
    primes_b = [r for r in rows_b if r["want"] == "prime"]
    cert_b_n = sum(r["phase140"] == "prime" for r in primes_b)
    routed_b = sum(r["routed"] == r["phase140"] for r in rows_b)
    num, den = Q7_SHARE
    marks["Q7"] = {"numbers": len(rows_b), "wrong": wrong_b,
                   "primes": len(primes_b), "certified": cert_b_n,
                   "certified_without": sum(r["without"] == "prime"
                                            for r in primes_b),
                   "routed_agree": routed_b, "rows": rows_b,
                   "met": not wrong_b and den * cert_b_n >= num * len(primes_b)}

    # Q8 (reported, not a mark) -- the numbers seen in exploration
    marks_known = []
    for name, n, want in KNOWN:
        t0 = time.perf_counter()
        v, cert = _verdict_with(n, True, True)
        marks_known.append({"n": name, "want": want, "got": v,
                            "kind": cert["kind"] if cert else None,
                            "seconds": round(time.perf_counter() - t0, 3)})

    return {"marks": marks, "known": marks_known,
            "met": sum(bool(m["met"]) for m in marks.values()),
            "taken": len(marks)}
