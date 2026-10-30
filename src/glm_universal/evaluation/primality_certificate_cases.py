"""``glm_universal.evaluation.primality_certificate_cases`` -- the Phase 139
cases (``studies/PRIMALITY_CERTIFICATE_STUDY.md``).

:data:`HELD_OUT` was written and committed **before** the certified
``prime`` step was run on any of its questions, and the expected verdicts do
not come from the new code.  They come from outside it:

* Mersenne numbers ``2^p - 1``: prime for ``p = 61, 89, 107, 127, 521`` and
  composite for ``p = 67`` (Cole, 1903: ``193707721 x 761838257287``) -- the
  published list of Mersenne prime exponents;
* ``2^32 + 1 = 641 x 6700417`` (Euler);
* ``10^12 + 39``, ``10^15 + 37`` and ``10^18 + 3`` are the least primes above
  ``10^12``, ``10^15`` and ``10^18`` (published tables), and
  ``999999999989`` the greatest prime below ``10^12``;
* ``10^12 + 1`` and ``10^18 + 1`` are divisible by ``101 = 10^2 + 1``
  (``x^2 + 1`` divides ``x^6 + 1`` and ``x^18 + 1``);
* ``1042789205881 = 5581 x 11161 x 16741`` is a Carmichael number (Chernick's
  form ``(6k+1)(12k+1)(18k+1)`` with ``k = 930``, the three factors prime by
  trial division at the time of writing), so no coprime base is a Fermat
  witness for it;
* ``1000003 x 1000033`` is a product, so not prime.

``None`` means the question should be **refused**: ``2^521 - 1`` is prime,
but certifying it means factoring ``2^520 - 1``'s cofactors, which the
declared work budget does not reach; the right answer under the budget is a
refusal that names the cofactor, never a guess.

Two phrasings (``h11``, ``h12``) say *a prime*; the stepwise reader's
pattern ``is (.+) (?:a )?prime`` captured *… a* greedily, which was seen in
exploration before this set was written and is fixed in the same round, so
those two are declared as known, not held out.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

#: ``(id, question, expected answer or None for a refusal)``.
HELD_OUT: Tuple[Tuple[str, str, Optional[str]], ...] = (
    ("h01", "is 1000000000039 prime", "prime"),
    ("h02", "is 1000000000001 prime", "not prime"),
    ("h03", "is 2 to the power 61 minus 1 prime", "prime"),
    ("h04", "is 2 to the power 67 minus 1 prime", "not prime"),
    ("h05", "is 2 to the power 32 plus 1 prime", "not prime"),
    ("h06", "is 2 to the power 89 minus 1 prime", "prime"),
    ("h07", "is 2 to the power 127 minus 1 prime", "prime"),
    ("h08", "is 1000000000000000003 prime", "prime"),
    ("h09", "is 1000000000000000001 prime", "not prime"),
    ("h10", "if 2 to the power 61 minus 1 is prime, 1, otherwise 0", "1"),
    ("h11", "is 1000000000039 a prime", "prime"),
    ("h12", "is 2 to the power 107 minus 1 a prime number", "prime"),
    ("h13", "is 1000000000000037 prime", "prime"),
    ("h14", "is 999999999989 prime", "prime"),
    ("h15", "is 1042789205881 prime", "not prime"),
    ("h16", "is 1000003 times 1000033 prime", "not prime"),
    ("h17", "is 2 to the power 521 minus 1 prime", None),
)

#: Phase 140 (``studies/POCKLINGTON_CERTIFICATE_STUDY.md``) certifies
#: ``2^521 - 1`` by a Pocklington certificate, so the refusal Phase 139
#: expected under its budget is superseded by the published verdict.  With
#: ``primality_certificate.POCKLINGTON`` off, :data:`HELD_OUT` holds as written.
SUPERSEDED = {"h17": "prime"}


def expected(cid: str, want: Optional[str]) -> str:
    """The outcome mark P2 scores against, under the current certifier."""
    from ..reasoning import primality_certificate as pc
    if pc.POCKLINGTON and cid in SUPERSEDED:
        return SUPERSEDED[cid]
    return "refuse" if want is None else want


# ---------------------------------------------------------------------------
# The measurement (marks P1-P6 of studies/PRIMALITY_CERTIFICATE_STUDY.md §4)
# ---------------------------------------------------------------------------

LEAN_FILE = "RequestProject/GLM/PrimalityCertificate.lean"
LEAN_THEOREMS = ("powMod_eq", "factor_witness", "fermat_witness",
                 "checkEntry_sound", "checkChain_sound", "pratt_sound",
                 "prime_10_12_39", "not_prime_10_12_1")

#: Mersenne exponents whose number is prime (the published list) -- mark P6.
MERSENNE_PRIME_EXPONENTS: Tuple[int, ...] = (61, 89, 107, 127, 521, 607)

#: Composites far past the old ceiling, each with its construction -- P6.
LARGE_COMPOSITES: Tuple[Tuple[str, int], ...] = (
    ("(2^89-1)(2^107-1)", (2 ** 89 - 1) * (2 ** 107 - 1)),
    ("(2^127-1)^2", (2 ** 127 - 1) ** 2),
    ("2^128+1", 2 ** 128 + 1),       # Fermat F7, composite (Morrison-Brillhart)
    ("10^60", 10 ** 60),
    ("(10^18+3)(10^18+9)", (10 ** 18 + 3) * (10 ** 18 + 9)),
)


def answer_of(r) -> str:
    """The verdict a routed answer states, or ``refuse``.  The typed planner
    words a primality answer as a sentence (*yes, 97 is prime: …*), so that
    sentence is read too (a reader fix after the first run, recorded in the
    study)."""
    import re
    from .tool_values_cases import _verdict
    got = _verdict(r)
    m = re.match(r"(?:yes, )?-?\d+ is (not )?prime\b", got)
    if m is None:
        m = re.match(r"no, -?\d+ is (not) prime\b", got)
    if m is not None:
        return "not prime" if m.group(1) else "prime"
    return got


def _trial(n: int) -> str:
    """The old method, run here without its ceiling: trial division."""
    if n < 2:
        return "not prime"
    if n % 2 == 0:
        return "prime" if n == 2 else "not prime"
    d = 3
    while d * d <= n:
        if n % d == 0:
            return "not prime"
        d += 2
    return "prime"


def _tampered(cert: dict) -> List[Tuple[str, dict]]:
    """Altered copies of a certificate, each of which proves nothing."""
    import copy
    out: List[Tuple[str, dict]] = []
    if cert["kind"] == "factor":
        out.append(("cert-factor", dict(cert, factor=1)))
    elif cert["kind"] == "fermat":
        out.append(("cert-base", dict(cert, base=1)))
    elif cert["kind"] == "pratt":
        c = copy.deepcopy(cert)
        c["chain"][-1][2] = c["chain"][-1][2][:-1]      # drop a factor of p-1
        out.append(("cert-drop", c))
        c = copy.deepcopy(cert)
        c["chain"][-1][1] = 1                           # base 1 has order 1
        out.append(("cert-base", c))
        c = copy.deepcopy(cert)
        c["chain"] = c["chain"][-1:]                    # no earlier entries
        out.append(("cert-unproved", c))
        c = copy.deepcopy(cert)
        c["chain"] = c["chain"][:-1]                    # about another number
        out.append(("cert-other", c))
    return out


def measure(scripts: bool = True) -> dict:
    """The marks P1-P6."""
    import random
    import time
    from pathlib import Path
    from ..reasoning import primality_certificate as pc
    from ..reasoning import stepwise_script as ss
    from ..runtime import router
    from ..runtime import stepwise as sw
    from ..runtime.session import GeometricSession
    from . import stepwise_cases as sc_cases

    marks: dict = {}
    session = GeometricSession()

    # P1 -- the Lean file
    lean = Path(__file__).resolve().parents[2] / "lean" / LEAN_FILE
    text = lean.read_text(encoding="utf-8") if lean.exists() else ""
    missing = [t for t in LEAN_THEOREMS if f"theorem {t} " not in text]
    marks["P1"] = {"file": LEAN_FILE, "missing": missing,
                   "sorry": "sorry" in text,
                   "met": bool(text) and not missing and "sorry" not in text}

    # P2 -- the held-out questions, through the router
    rows = []
    for cid, question, want in HELD_OUT:
        r = router.route(session, question)
        got = answer_of(r)
        ok = got == expected(cid, want)
        rows.append({"id": cid, "question": question, "got": got,
                     "want": want, "ok": ok, "surface": r.surface})
    wrong = [r for r in rows if r["got"] != "refuse" and not r["ok"]]
    marks["P2"] = {"questions": len(rows),
                   "as_expected": sum(r["ok"] for r in rows),
                   "wrong": wrong, "rows": rows,
                   "met": all(r["ok"] for r in rows)}

    # P3 -- column 3 on every answered chain that holds a certificate; the
    # declared mutations; and every tampered certificate, which both the step
    # gate and the script must reject
    if scripts:
        from ..runtime.python_tct import run_column3
        from ..runtime.tct_engine import package_root
        root = str(package_root())
        chains = verified = built = caught = 0
        tampers = gate_caught = script_caught = 0
        for _cid, question, _want in HELD_OUT:
            a = sw.answer(session, question)
            if not a.answered:
                continue
            certified = [s for s in a.chain.steps
                         if s.op == "prime" and "certificate" in s.detail]
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
                for _kind, bad in _tampered(dict(s.detail["certificate"])):
                    tampers += 1
                    detail = dict(s.detail, certificate=bad)
                    if bad["kind"] != "factor":
                        detail.pop("factor", None)
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
        marks["P3"] = {"chains": chains, "verified": verified,
                       "mutants": built, "caught": caught,
                       "tampered": tampers, "gate_caught": gate_caught,
                       "script_caught": script_caught,
                       "met": chains > 0 and verified == chains
                       and caught == built and gate_caught == tampers
                       and script_caught == tampers}
    else:
        marks["P3"] = {"skipped": True, "met": False}

    # P4 -- agreement with the old method just above the old ceiling
    rng = random.Random(139)
    ns = [10 ** 12 + k for k in range(1, 201)] + \
        [rng.randrange(10 ** 12, 10 ** 13) for _ in range(100)]
    disagree = []
    primes = 0
    for n in ns:
        v, cert = pc.verdict(n)
        primes += v == "prime"
        if v != _trial(n) or pc.check(n, cert) != v:
            disagree.append(n)
    marks["P4"] = {"numbers": len(ns), "primes": primes,
                   "disagree": disagree, "met": not disagree}

    # P5 -- non-interference: the stepwise composition corpus answers as it
    # did with the certified step switched off
    corpus = [q for _cid, q, *_ in sc_cases.COMPOSITION_CASES]
    sw.CERTIFIED_PRIMALITY = False
    try:
        before = [sw.answer(session, q).summary() for q in corpus]
    finally:
        sw.CERTIFIED_PRIMALITY = True
    after = [sw.answer(session, q).summary() for q in corpus]
    moved = [q for q, b, a in zip(corpus, before, after) if b != a]
    marks["P5"] = {"corpus": len(corpus), "moved": moved, "met": not moved}

    # P6 -- scale: Mersenne primes and large composites, certified or refused
    # by the work budget, never answered wrongly
    scale = []
    for p in MERSENNE_PRIME_EXPONENTS:
        n = 2 ** p - 1
        t0 = time.perf_counter()
        try:
            v, cert = pc.verdict(n)
            row = {"n": f"2^{p}-1", "want": "prime", "got": v,
                   "kind": cert["kind"],
                   "entries": len(cert.get("chain", ()))}
        except pc.NoCertificate as exc:
            row = {"n": f"2^{p}-1", "want": "prime", "got": "refuse",
                   "cofactor_digits": len(str(exc.cofactor))}
        row["seconds"] = round(time.perf_counter() - t0, 3)
        scale.append(row)
    for name, n in LARGE_COMPOSITES:
        t0 = time.perf_counter()
        v, cert = pc.verdict(n)
        scale.append({"n": name, "want": "not prime", "got": v,
                      "kind": cert["kind"],
                      "seconds": round(time.perf_counter() - t0, 3)})
    wrong6 = [r for r in scale if r["got"] not in ("refuse", r["want"])]
    certified = [r for r in scale if r["got"] == r["want"]]
    marks["P6"] = {"cases": len(scale), "certified": len(certified),
                   "refused": sum(r["got"] == "refuse" for r in scale),
                   "wrong": wrong6, "rows": scale,
                   "met": not wrong6 and all(
                       r["got"] == r["want"] for r in scale
                       if r["n"] in ("2^61-1", "2^89-1", "2^107-1",
                                     "2^127-1") or r["want"] == "not prime")}

    return {"marks": marks,
            "met": sum(bool(m["met"]) for m in marks.values()),
            "taken": len(marks)}
