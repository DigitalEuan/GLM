"""``glm_universal.evaluation.elliptic_certificate_cases`` -- the Phase 141
cases (``studies/ELLIPTIC_CERTIFICATE_STUDY.md``).

Phase 140 left a prime refused when neither ``p - 1`` (Pratt, Pocklington)
nor ``p + 1`` (N+1) splits within the work budget.  Phase 141 adds an
elliptic-curve entry (``RequestProject/GLM/EllipticCertificate.lean``,
``elliptic_prime``), found by complex multiplication.

:data:`HELD_OUT` was written and committed **before** the elliptic search
existed, and before the Phase 140 certifier was run on any of its numbers.
Its verdicts come from published sources, not from the new code:

* field primes of published elliptic-curve standards: ``2^255 - 19``
  (Curve25519, RFC 7748), ``2^448 - 2^224 - 1`` (Ed448-Goldilocks, RFC
  7748), the NIST primes P-192, P-224, P-256 and P-384 (FIPS 186-4,
  appendix D), the secp256k1 prime ``2^256 - 2^32 - 977`` (SEC 2), and the
  Poly1305 prime ``2^130 - 5`` (RFC 8439);
* the least 101-digit prime ``10^100 + 267`` and the greatest 100-digit
  prime ``10^100 - 797``; the greatest primes below ``2^64`` and ``2^128``,
  ``2^64 - 59`` and ``2^128 - 159``;
* the repunit prime ``R317`` (OEIS A004023);
* composites by construction: ``10^100 + 1`` (divisible by ``10^4 + 1``,
  since ``100 = 4 * 25`` with ``25`` odd), ``R319`` (divisible by ``R11``,
  since ``11`` divides ``319``), and the products P-224 x Poly1305 and
  ``(2^255 - 19)(2^64 - 59)``, two semiprimes with no small factor.

The questions state the numbers as decimal literals; a question is answered
right, refused, or answered **wrong** -- and wrong is the only outcome the
marks forbid.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple


def _repunit(n: int) -> int:
    return (10 ** n - 1) // 9


_P192 = 2 ** 192 - 2 ** 64 - 1
_P224 = 2 ** 224 - 2 ** 96 + 1
_P256 = 2 ** 256 - 2 ** 224 + 2 ** 192 + 2 ** 96 - 1
_P384 = 2 ** 384 - 2 ** 128 - 2 ** 96 + 2 ** 32 - 1
_C25519 = 2 ** 255 - 19
_POLY1305 = 2 ** 130 - 5

#: ``(id, name, n, published verdict)`` -- written before the search existed.
HELD_OUT: Tuple[Tuple[str, str, int, str], ...] = (
    ("e01", "2^255-19", _C25519, "prime"),
    ("e02", "2^448-2^224-1", 2 ** 448 - 2 ** 224 - 1, "prime"),
    ("e03", "P-192", _P192, "prime"),
    ("e04", "P-224", _P224, "prime"),
    ("e05", "P-256", _P256, "prime"),
    ("e06", "P-384", _P384, "prime"),
    ("e07", "2^256-2^32-977", 2 ** 256 - 2 ** 32 - 977, "prime"),
    ("e08", "2^130-5", _POLY1305, "prime"),
    ("e09", "10^100+267", 10 ** 100 + 267, "prime"),
    ("e10", "10^100-797", 10 ** 100 - 797, "prime"),
    ("e11", "2^64-59", 2 ** 64 - 59, "prime"),
    ("e12", "2^128-159", 2 ** 128 - 159, "prime"),
    ("e13", "R317", _repunit(317), "prime"),
    ("e14", "10^100+1", 10 ** 100 + 1, "not prime"),
    ("e15", "R319", _repunit(319), "not prime"),
    ("e16", "P-224*(2^130-5)", _P224 * _POLY1305, "not prime"),
    ("e17", "(2^255-19)*(2^64-59)", _C25519 * (2 ** 64 - 59), "not prime"),
)

#: Seen in exploration before :data:`HELD_OUT` was written: none of the
#: published numbers above.  The exploration used primes drawn as the next
#: probable prime after integers chosen by a seeded generator outside the
#: package (40 to 150 digits), declared here so they are not mistaken for
#: held-out numbers.
KNOWN: Tuple[Tuple[str, int, str], ...] = ()

#: The mark on :data:`HELD_OUT`, declared with it: no wrong verdict, and at
#: least half of the primes Phase 140's certifier refuses certified.
E2_SHARE = (1, 2)

LEAN_FILE = "RequestProject/GLM/EllipticCertificate.lean"
LEAN_THEOREMS = ("rep_ecAdd", "rep_ecMulF", "card_point_le", "elliptic_prime",
                 "checkEChain_sound", "elliptic_sound")
#: The kernel-checked instance (mark E5): a held-out prime, its certificate
#: copied from the run-time search after the first measurement.  The first
#: run named ``e08`` (``2^130 - 5``) before any certificate existed; the
#: Pratt search certifies it, so it carries no elliptic entry, and the
#: instance was re-chosen after that run as the held-out prime with the
#: fewest elliptic entries, ``e01`` (``2^255 - 19``) -- recorded in the
#: study as a post-hoc choice.
INSTANCE_ID = "e01"
INSTANCE_THEOREM = "prime_2_255_sub_19"


def question(n: int) -> str:
    return f"is {n} prime"


def tampered(cert: dict) -> List[Tuple[str, dict]]:
    """Altered copies of an elliptic certificate, each proving nothing (or,
    for ``cert-k``, proving nothing at the declared ``k``)."""
    import copy
    out: List[Tuple[str, dict]] = []
    if cert.get("kind") != "elliptic":
        return out
    last = max(i for i, e in enumerate(cert["chain"]) if len(e) == 7)
    entry = cert["chain"][last]
    p, a, b, x, y, k, q = entry

    def variant(name: str, new_entry=None, chain=None) -> None:
        c = copy.deepcopy(cert)
        if chain is not None:
            c["chain"] = chain
        else:
            c["chain"][last] = new_entry
        out.append((name, c))

    variant("cert-point", [p, a, b, x, (y + 1) % p, k, q])   # off the curve
    variant("cert-k", [p, a, b, x, y, k + 1, q])            # wrong cofactor
    variant("cert-curve", [p, (a + 1) % p, b, x, y, k, q])  # another curve
    small = [e[0] for e in cert["chain"][:last] if e[0] != q]
    if small:
        variant("cert-q", [p, a, b, x, y, k, small[-1]])    # a smaller prime
    variant("cert-singular", [p, 0, 0, x, y, k, q])         # y^2 = x^3
    c = copy.deepcopy(cert)
    c["chain"] = [e for e in c["chain"] if e[0] != q]       # q unproved
    out.append(("cert-unproved", c))
    variant("cert-other", chain=copy.deepcopy(cert["chain"][:last]))
    return out


class flags:
    """Set the Phase 140 and Phase 141 controls for a block."""

    def __init__(self, elliptic: bool) -> None:
        self.want = elliptic

    def __enter__(self):
        from ..reasoning import primality_certificate as pc
        self.saved = (pc.POCKLINGTON, pc.LUCAS, pc.ELLIPTIC)
        pc.POCKLINGTON, pc.LUCAS, pc.ELLIPTIC = True, True, self.want
        return self

    def __exit__(self, *exc):
        from ..reasoning import primality_certificate as pc
        pc.POCKLINGTON, pc.LUCAS, pc.ELLIPTIC = self.saved
        return False


def _verdict_with(n: int, elliptic: bool) -> Tuple[str, Optional[dict]]:
    from ..reasoning import primality_certificate as pc
    with flags(elliptic):
        try:
            return pc.verdict(n)
        except pc.NoCertificate:
            return "refuse", None


def lean_entry(e) -> str:
    """One chain entry as ``EllipticCertificate.lean`` writes it."""
    if len(e) == 2:
        return f".base (.pock {e[0]} [" + ", ".join(
            f"({q}, {x}, {a})" for q, x, a in e[1]) + "])"
    if len(e) == 3:
        return f".base (.lucas {e[0]} {e[1]} [" + ", ".join(
            f"({q}, {x})" for q, x in e[2]) + "])"
    return ".ec " + " ".join(str(v) for v in e)


def measure(scripts: bool = True) -> dict:
    """The marks E1-E6 of ``studies/ELLIPTIC_CERTIFICATE_STUDY.md`` §4."""
    import random
    import time
    from pathlib import Path
    from ..reasoning import stepwise_script as ss
    from ..runtime import router
    from ..runtime import stepwise as sw
    from ..runtime.session import GeometricSession
    from . import pocklington_certificate_cases as pkc
    from . import primality_certificate_cases as pcc
    from . import stepwise_cases as sc_cases

    marks: Dict[str, dict] = {}
    session = GeometricSession()

    # E1 -- the Lean file
    lean = Path(__file__).resolve().parents[2] / "glm_lean" / LEAN_FILE
    text = lean.read_text(encoding="utf-8") if lean.exists() else ""
    missing = [t for t in LEAN_THEOREMS + (INSTANCE_THEOREM,)
               if f"theorem {t} " not in text]
    sorry = "sorry" in text
    marks["E1"] = {"file": LEAN_FILE, "missing": missing, "sorry": sorry,
                   "met": bool(text) and not missing and not sorry}

    # E2 -- the held-out numbers: the Phase 140 certifier, the Phase 141
    # certifier, and the question through the router
    rows = []
    certs: Dict[str, dict] = {}
    for cid, name, n, want in HELD_OUT:
        t0 = time.perf_counter()
        before, _ = _verdict_with(n, False)
        t1 = time.perf_counter()
        after, cert = _verdict_with(n, True)
        t2 = time.perf_counter()
        with flags(True):
            routed = pcc.answer_of(router.route(session, question(n)))
        if cert is not None:
            certs[cid] = cert
        rows.append({"id": cid, "n": name, "want": want, "phase140": before,
                     "phase141": after, "routed": routed,
                     "kind": cert["kind"] if cert else None,
                     "entries": len(cert.get("chain", ())) if cert else 0,
                     "elliptic_entries": sum(
                         len(e) == 7 for e in cert.get("chain", ()))
                     if cert else 0,
                     "seconds_140": round(t1 - t0, 1),
                     "seconds_141": round(t2 - t1, 1),
                     "seconds": round(time.perf_counter() - t0, 1)})
    wrong = [r for r in rows
             if any(r[k] not in ("refuse", r["want"])
                    for k in ("phase140", "phase141", "routed"))]
    gap = [r for r in rows if r["want"] == "prime" and r["phase140"] == "refuse"]
    closed = [r for r in gap if r["phase141"] == "prime"]
    routed_ok = [r for r in rows if r["routed"] == r["phase141"]]
    num, den = E2_SHARE
    marks["E2"] = {"numbers": len(rows), "wrong": wrong,
                   "phase140_refused_primes": len(gap),
                   "certified_now": len(closed),
                   "routed_agree": len(routed_ok), "rows": rows,
                   "met": not wrong and len(routed_ok) == len(rows)
                   and bool(gap) and den * len(closed) >= num * len(gap)}

    # E3 -- column 3 and the step gate on every chain holding an elliptic
    # certificate, the declared mutations, and the tampered certificates
    if scripts:
        from ..runtime.python_tct import run_column3
        from ..runtime.tct_engine import package_root
        root = str(package_root())
        chains = verified = built = caught = 0
        tampers = gate_caught = script_caught = 0
        for cid, _nm, n, _w in HELD_OUT:
            if certs.get(cid, {}).get("kind") != "elliptic":
                continue
            with flags(True):
                a = sw.answer(session, question(n))
            if not a.answered:
                continue
            certified = [s for s in a.chain.steps if s.op == "prime"
                         and s.detail.get("certificate", {}).get("kind")
                         == "elliptic"]
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
        marks["E3"] = {"chains": chains, "verified": verified,
                       "mutants": built, "caught": caught,
                       "tampered": tampers, "gate_caught": gate_caught,
                       "script_caught": script_caught,
                       "met": chains > 0 and verified == chains
                       and caught == built and gate_caught == tampers
                       and script_caught == tampers}
    else:
        marks["E3"] = {"skipped": True, "met": False}

    # E4 -- the control: with the elliptic stage off the certifier is Phase
    # 140's; Phase 139's held-out questions and Phase 140's first held-out
    # set answer the same with it on
    moved = []
    for cid, q, _want in pcc.HELD_OUT:
        with flags(False):
            off = pcc.answer_of(router.route(session, q))
        with flags(True):
            on = pcc.answer_of(router.route(session, q))
        if off != on:
            moved.append((cid, off, on))
    for cid, _nm, n, _want in pkc.HELD_OUT:
        off = _verdict_with(n, False)
        on = _verdict_with(n, True)
        if off != on:
            moved.append((cid, off[0], on[0]))
    marks["E4"] = {"questions": len(pcc.HELD_OUT) + len(pkc.HELD_OUT),
                   "moved": moved, "met": not moved}

    # E5 -- the kernel instance is the tool's own certificate
    inst = certs.get(INSTANCE_ID)
    present = bool(inst) and inst["kind"] == "elliptic" and all(
        lean_entry(e) in text for e in inst["chain"])
    marks["E5"] = {"id": INSTANCE_ID, "theorem": INSTANCE_THEOREM,
                   "kind": inst["kind"] if inst else None,
                   "entries": len(inst["chain"]) if inst else 0,
                   "in_lean": present, "met": present}

    # E6 -- non-interference: Phase 140's certified numbers keep verdict and
    # certificate, and the composition corpus answers as before
    rng = random.Random(139)
    ns = [10 ** 12 + k for k in range(1, 201)] + \
        [rng.randrange(10 ** 12, 10 ** 13) for _ in range(100)] + \
        [2 ** p - 1 for p in (61, 89, 107, 127)]
    changed = [n for n in ns if _verdict_with(n, False) != _verdict_with(n, True)]
    corpus = [q for _cid, q, *_ in sc_cases.COMPOSITION_CASES]
    with flags(False):
        before = [sw.answer(session, q).summary() for q in corpus]
    with flags(True):
        after = [sw.answer(session, q).summary() for q in corpus]
    moved_c = [q for q, b, a in zip(corpus, before, after) if b != a]
    marks["E6"] = {"numbers": len(ns), "changed": changed,
                   "corpus": len(corpus), "moved": moved_c,
                   "met": not changed and not moved_c}

    return {"marks": marks,
            "met": sum(bool(m["met"]) for m in marks.values()),
            "taken": len(marks)}
