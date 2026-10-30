"""``glm_universal.reasoning.primality_certificate`` -- primality with a proof.

Why this module exists
----------------------
Phase 138 left this line in ``STATUS.md`` §2.2: *the primality step keeps a
ceiling of 10^12.*  The stepwise planner's ``prime`` step decided primality by
trial division, which costs up to a million divisions per check at 10^12 and is
run three times per chain (the builder, the step gate and the column-3 script);
above 10^12 it refused.

This module replaces trial division above that line by a **certificate** whose
check costs a handful of modular exponentiations, whatever the size of the
number (``studies/PRIMALITY_CERTIFICATE_STUDY.md``, Phase 139).  Each check is
proved sound in Lean (``RequestProject/GLM/PrimalityCertificate.lean``):

* ``{"kind": "small"}`` -- ``n < 2``, not prime;
* ``{"kind": "factor", "factor": f}`` -- ``1 < f < n`` and ``f`` divides
  ``n``: not prime (``GLM.PrimalityCertificate.factor_witness``);
* ``{"kind": "fermat", "base": a}`` -- ``1 <= a < n`` and
  ``a^(n-1) mod n != 1``: not prime, no factor named
  (``GLM.PrimalityCertificate.fermat_witness``);
* ``{"kind": "pratt", "chain": [[p, a, [[q, e], ...]], ...]}`` -- a Pratt
  certificate: every entry has ``p >= 2``, ``prod q^e = p - 1``, every ``q``
  certified by an earlier entry, ``a^(p-1) mod p == 1`` and
  ``a^((p-1)/q) mod p != 1`` for each ``q``; the last entry is about ``n``
  (``GLM.PrimalityCertificate.pratt_sound``);
* ``{"kind": "pocklington", "chain": [[p, [[q, e, a], ...]], ...]}`` -- a
  Pocklington certificate (Phase 140, ``studies/POCKLINGTON_CERTIFICATE_STUDY.md``):
  with ``F = prod q^e`` every entry has ``p >= 2``, ``F | p - 1``,
  ``p < (F + 1)^2``, distinct ``q`` each certified by an earlier entry, and
  for each factor ``a^(p-1) mod p == 1`` and
  ``gcd((a^((p-1)/q) mod p + p - 1) mod p, p) == 1``; only a part of ``p - 1``
  larger than ``sqrt(p)`` need be factored
  (``GLM.PrimalityCertificate.pocklington_sound``, in
  ``RequestProject/GLM/PocklingtonCertificate.lean``).  :func:`certify` emits
  one only when the Pratt search runs out of budget, so every number Phase
  139 certified keeps its Pratt certificate;
* ``{"kind": "lucas", "chain": [entry, ...]}`` -- a mixed chain (Phase 140,
  part B) whose entries are Pocklington entries ``[p, [[q, e, a], ...]]`` or
  N+1 (Lucas) entries ``[p, P, [[q, e], ...]]``: ``p >= 2``,
  ``prod q^e = p + 1``, every ``q`` certified earlier, ``X^(p+1) = 1`` in
  ``(Z/p)[X]/(X^2 - P X + 1)`` and, for each ``q``, the norm of
  ``X^((p+1)/q) - 1`` coprime to ``p``
  (``GLM.PrimalityCertificate.lucas_prime`` and ``mixed_sound``, in
  ``RequestProject/GLM/LucasCertificate.lean``).  Emitted only when both the
  Pratt and the Pocklington searches run out of budget.

:func:`check` mirrors ``checkEntry`` / ``checkChain`` / ``certifies`` line for
line.  :func:`certify` *finds* a certificate; finding one for a prime means
factoring ``p - 1`` (recursively), done by trial division over small primes and
Brent's variant of Pollard's rho.  Factoring has no size ceiling but it has a
**work budget** (``budget`` rho iterations in total); when the budget runs out
the step is refused with ``NO_CERTIFICATE``, naming the cofactor that was not
split, so the refusal is about work, never about the size of the number, and
never a guessed answer.  A probable-prime test only *steers* the search (which
cofactor to split, which to certify); no verdict rests on it.

Exact throughout: ``int`` only.
"""

from __future__ import annotations

from math import gcd, isqrt
from typing import Dict, List, Optional, Tuple

__all__ = ["certify", "check", "verdict", "NoCertificate", "BUDGET", "SLICE",
           "POCKLINGTON", "LUCAS", "ELLIPTIC",
           "SMALL_PRIMES", "TRIAL_LIMIT"]

#: The total rho iterations one certification may spend.
BUDGET = 2_000_000

#: Trial division runs over primes below this before rho starts.
TRIAL_LIMIT = 2000

SMALL_PRIMES: Tuple[int, ...] = tuple(
    p for p in range(2, TRIAL_LIMIT)
    if all(p % d for d in range(2, isqrt(p) + 1)))

_MR_BASES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41)


class NoCertificate(Exception):
    """The work budget ran out before a certificate was found."""

    def __init__(self, n: int, cofactor: int) -> None:
        super().__init__(f"no certificate for {n} within the work budget: "
                         f"the cofactor {cofactor} was not split")
        self.n, self.cofactor = n, cofactor


# ---------------------------------------------------------------------------
# The check -- mirrors GLM.PrimalityCertificate line for line
# ---------------------------------------------------------------------------

def _check_entry(known: set, p: int, a: int, fs: List[List[int]]) -> bool:
    prod = 1
    for q, e in fs:
        prod *= q ** e
    return (p >= 2 and prod == p - 1
            and all(q in known for q, _ in fs)
            and pow(a, p - 1, p) == 1
            and all(pow(a, (p - 1) // q, p) != 1 for q, _ in fs))


def _check_chain(chain) -> bool:
    known: set = set()
    for p, a, fs in chain:
        if not _check_entry(known, p, a, fs):
            return False
        known.add(p)
    return True


def _factored_part(fs) -> int:
    prod = 1
    for q, e, _ in fs:
        prod *= q ** e
    return prod


def _witness_ok(p: int, t) -> bool:
    q, _, a = t
    return (pow(a, p - 1, p) == 1
            and gcd((pow(a, (p - 1) // q, p) + (p - 1)) % p, p) == 1)


def _check_pentry(known: set, p: int, fs) -> bool:
    big_f = _factored_part(fs)
    qs = [t[0] for t in fs]
    return (p >= 2 and big_f != 0 and (p - 1) % big_f == 0
            and p < (big_f + 1) * (big_f + 1)
            and len(set(qs)) == len(qs)
            and all(q in known for q in qs)
            and all(_witness_ok(p, t) for t in fs))


def _check_pchain(chain) -> bool:
    known: set = set()
    for p, fs in chain:
        if not _check_pentry(known, p, fs):
            return False
        known.add(p)
    return True


def _qmul(p: int, big_p: int, x, y) -> Tuple[int, int]:
    return ((x[0] * y[0] + x[1] * y[1] * (p - 1)) % p,
            (x[0] * y[1] + x[1] * y[0] + big_p * x[1] * y[1]) % p)


def _qpow(p: int, big_p: int, b, e: int) -> Tuple[int, int]:
    out = (1 % p, 0)
    b = (b[0] % p, b[1] % p)
    while e:
        if e & 1:
            out = _qmul(p, big_p, out, b)
        b = _qmul(p, big_p, b, b)
        e >>= 1
    return out


def _qsub_one(p: int, x) -> Tuple[int, int]:
    return ((x[0] + (p - 1)) % p, x[1])


def _qnorm(p: int, big_p: int, x) -> int:
    return (x[0] * x[0] + big_p * x[0] * x[1] + x[1] * x[1]) % p


def _lucas_q_ok(p: int, big_p: int, q: int) -> bool:
    z = _qsub_one(p, _qpow(p, big_p, (0, 1), (p + 1) // q))
    return gcd(_qnorm(p, big_p, z), p) == 1


def _check_lentry(known: set, p: int, big_p: int, fs) -> bool:
    prod = 1
    for q, e in fs:
        prod *= q ** e
    return (p >= 2 and prod == p + 1
            and all(q in known for q, _ in fs)
            and _qpow(p, big_p, (0, 1), p + 1) == (1, 0)
            and all(_lucas_q_ok(p, big_p, q) for q, _ in fs))


def _check_mchain(chain) -> bool:
    known: set = set()
    for entry in chain:
        if len(entry) == 2:
            p, fs = entry
            ok = _check_pentry(known, p, fs)
        elif len(entry) == 3:
            p, big_p, fs = entry
            ok = _check_lentry(known, p, big_p, fs)
        else:
            return False
        if not ok:
            return False
        known.add(p)
    return True


def _finv(p: int, d: int) -> int:
    """An inverse of ``d`` modulo ``p`` (``finv``: the extended Euclidean
    algorithm); ``0`` when there is none -- the caller's check ``d i == 1``
    then fails, as ``finv``'s value fails it in Lean."""
    try:
        return pow(d % p, -1, p)
    except ValueError:
        return 0


def _ec_add(p: int, a: int, pt1, pt2):
    """``ecAdd``: the chord-and-tangent law modulo ``p``; ``None`` is the
    point at infinity, and a step the law cannot take returns ``False``."""
    if pt1 is None:
        return pt2
    if pt2 is None:
        return pt1
    (x1, y1), (x2, y2) = pt1, pt2
    if x1 % p == x2 % p:
        if (y1 + y2) % p == 0:
            return None
        if y1 % p != y2 % p:
            return False
        d = 2 * y1 % p
        i = _finv(p, d)
        if d * i % p != 1:
            return False
        lam = (3 * x1 * x1 + a) * i % p
        x3 = (lam * lam + 2 * (p - x1 % p)) % p
        return (x3, (lam * (x1 % p + p - x3) + (p - y1 % p)) % p)
    d = (x2 % p + p - x1 % p) % p
    i = _finv(p, d)
    if d * i % p != 1:
        return False
    lam = (y2 % p + p - y1 % p) * i % p
    x3 = (lam * lam + (p - x1 % p) + (p - x2 % p)) % p
    return (x3, (lam * (x1 % p + p - x3) + (p - y1 % p)) % p)


def _ec_mul(p: int, a: int, k: int, pt):
    """``ecMul``: double-and-add from the top bit (the same steps as
    ``ecMulF``'s recursion on ``k / 2``); ``False`` if a step fails."""
    acc = None
    for bit in (bin(k)[2:] if k else ""):
        acc = _ec_add(p, a, acc, acc)
        if acc is False:
            return False
        if bit == "1":
            acc = _ec_add(p, a, acc, pt)
            if acc is False:
                return False
    return acc


def _check_eentry(known: set, p: int, a: int, b: int, x: int, y: int,
                  k: int, q: int) -> bool:
    """``checkEEntry`` (``RequestProject/GLM/EllipticCertificate.lean``)."""
    if not (p >= 3 and p % 2 == 1
            and gcd((4 * a * a * a + 27 * b * b) % p, p) == 1
            and (y * y) % p == (x * x * x + a * x + b) % p
            and q in known and 4 * p < (q - 1) * (q - 1)):
        return False
    pt = _ec_mul(p, a, k, (x, y))
    if pt is None or pt is False:
        return False
    return _ec_mul(p, a, q, pt) is None


def _check_echain(chain) -> bool:
    """``checkEChain``: Pocklington ``[p, fs]``, N+1 ``[p, P, fs]`` and
    elliptic ``[p, a, b, x, y, k, q]`` entries."""
    known: set = set()
    for entry in chain:
        if len(entry) == 2:
            ok = _check_pentry(known, entry[0], entry[1])
        elif len(entry) == 3:
            ok = _check_lentry(known, entry[0], entry[1], entry[2])
        elif len(entry) == 7:
            ok = _check_eentry(known, *entry)
        else:
            return False
        if not ok:
            return False
        known.add(entry[0])
    return True


def check(n: int, cert: Dict[str, object]) -> str:
    """``"prime"`` or ``"not prime"`` if ``cert`` proves it for ``n``;
    raises ``ValueError`` if it proves nothing."""
    kind = cert.get("kind")
    if kind == "small" and n < 2:
        return "not prime"
    if kind == "factor":
        f = int(cert["factor"])                       # type: ignore[arg-type]
        if 1 < f < n and n % f == 0:
            return "not prime"
    if kind == "fermat":
        a = int(cert["base"])                         # type: ignore[arg-type]
        if 1 <= a < n and pow(a, n - 1, n) != 1:
            return "not prime"
    if kind == "pratt":
        chain = cert["chain"]
        if (_check_chain(chain)                       # type: ignore[arg-type]
                and any(e[0] == n for e in chain)):   # type: ignore[union-attr]
            return "prime"
    if kind == "pocklington":
        chain = cert["chain"]
        if (_check_pchain(chain)                      # type: ignore[arg-type]
                and any(e[0] == n for e in chain)):   # type: ignore[union-attr]
            return "prime"
    if kind == "lucas":
        chain = cert["chain"]
        if (_check_mchain(chain)                      # type: ignore[arg-type]
                and any(e[0] == n for e in chain)):   # type: ignore[union-attr]
            return "prime"
    if kind == "elliptic":
        chain = cert["chain"]
        if (_check_echain(chain)                      # type: ignore[arg-type]
                and any(e[0] == n for e in chain)):   # type: ignore[union-attr]
            return "prime"
    raise ValueError(f"the certificate proves nothing about {n}")


# ---------------------------------------------------------------------------
# The search
# ---------------------------------------------------------------------------

def _probable_prime(n: int) -> bool:
    """Steering only: a strong probable-prime test to fixed bases."""
    if n < 2:
        return False
    for p in _MR_BASES:
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d, s = d // 2, s + 1
    for a in _MR_BASES:
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def _composite_certificate(n: int) -> Optional[Dict[str, object]]:
    """A factor or a Fermat witness, if the strong test finds one."""
    for p in SMALL_PRIMES:
        if p * p > n:
            break
        if n % p == 0:
            return {"kind": "factor", "factor": p}
    d, s = n - 1, 0
    while d % 2 == 0:
        d, s = d // 2, s + 1
    for a in _MR_BASES:
        if a >= n:
            continue
        if pow(a, n - 1, n) != 1:
            return {"kind": "fermat", "base": a}
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s):
            y = x * x % n
            if y == 1:                      # x is a square root of 1, not +-1
                return {"kind": "factor", "factor": gcd(x - 1, n)}
            if y == n - 1:
                break
            x = y
    return None


class _Budget:
    def __init__(self, n: int) -> None:
        self.left = BUDGET


def _rho(n: int, budget: _Budget) -> Optional[int]:
    """Brent's rho: a proper factor of the composite ``n``, or None when the
    budget runs out."""
    if n % 2 == 0:
        return 2
    for c in range(1, 64):
        y, m, g, r, q = 2, 128, 1, 1, 1
        x = ys = y
        while g == 1:
            x = y
            for _ in range(r):
                y = (y * y + c) % n
            k = 0
            while k < r and g == 1:
                ys = y
                for _ in range(min(m, r - k)):
                    y = (y * y + c) % n
                    q = q * abs(x - y) % n
                budget.left -= min(m, r - k)
                if budget.left < 0:
                    return None
                g = gcd(q, n)
                k += m
            r *= 2
        if g == n:
            g = 1
            while g == 1:
                ys = (ys * ys + c) % n
                g = gcd(abs(x - ys), n)
        if 1 < g < n:
            return g
    return None


def _factor(n: int, budget: _Budget, top: int) -> Dict[int, int]:
    """The prime factorisation of ``n`` (primes by the steering test; each is
    certified afterwards, so a wrong steer only costs a refusal)."""
    out: Dict[int, int] = {}
    for p in SMALL_PRIMES:
        while n % p == 0:
            out[p] = out.get(p, 0) + 1
            n //= p
    stack = [n] if n > 1 else []
    while stack:
        m = stack.pop()
        if _probable_prime(m):
            out[m] = out.get(m, 0) + 1
            continue
        f = _rho(m, budget)
        if f is None:
            raise NoCertificate(top, m)
        stack += [f, m // f]
    return out


def _pratt(n: int, budget: _Budget, top: int,
           done: Dict[int, list], chain: list) -> None:
    """Append entries certifying ``n`` (and the primes of ``n - 1``) to
    ``chain``; ``done`` holds the primes already certified."""
    if n in done:
        return
    fs = sorted(_factor(n - 1, budget, top).items()) if n > 2 else []
    for q, _ in fs:
        _pratt(q, budget, top, done, chain)
    for a in range(2 if n > 2 else 1, min(n + 1, 10_000)):
        if pow(a, n - 1, n) != 1:
            raise NoCertificate(top, n)       # the steer was wrong: n composite
        if all(pow(a, (n - 1) // q, n) != 1 for q, _ in fs):
            entry = [n, a, [[q, e] for q, e in fs]]
            chain.append(entry)
            done[n] = entry
            return
    raise NoCertificate(top, n)


#: The Phase 140 control: with this off, :func:`certify` behaves exactly as
#: in Phase 139 (Pratt or refuse).
POCKLINGTON = True

#: One rho attempt on one cofactor may spend at most this many iterations
#: of the Pocklington search's budget, so one hard cofactor cannot eat it all.
SLICE = BUDGET // 8


def _rho_slice(m: int, budget: _Budget) -> Optional[int]:
    """Rho on ``m`` with at most :data:`SLICE` of what is left."""
    if budget.left <= 0:
        return None
    local = _Budget(m)
    local.left = min(SLICE, budget.left)
    start = local.left
    f = _rho(m, local)
    budget.left -= start - max(local.left, 0)
    return f


def _partial_factor(m: int, budget: _Budget,
                    enough) -> Tuple[Dict[int, int], List[int]]:
    """Split ``m`` until ``enough(F)`` for the product ``F`` of the prime
    powers found, smallest cofactor first; return the primes (by the steering
    test) and the cofactors left unsplit."""
    out: Dict[int, int] = {}
    for p in SMALL_PRIMES:
        while m % p == 0:
            out[p] = out.get(p, 0) + 1
            m //= p
    pending = [m] if m > 1 else []
    left: List[int] = []

    def found() -> int:
        prod = 1
        for q, e in out.items():
            prod *= q ** e
        return prod

    while pending and not enough(found()):
        pending.sort()
        c = pending.pop(0)
        if _probable_prime(c):
            out[c] = out.get(c, 0) + 1
            continue
        f = _rho_slice(c, budget)
        if f is None:
            left.append(c)
            continue
        pending += [f, c // f]
    return out, left + pending


def _pock(n: int, budget: _Budget, top: int,
          done: Dict[int, list], chain: list) -> bool:
    """Append Pocklington entries certifying ``n`` to ``chain``; False when
    the budget runs out (nothing half-appended is left without its own
    entries: every entry appended is accepted on its own)."""
    if n in done:
        return True
    if n < 2000:                          # small: the whole of n - 1 splits
        enough = lambda big_f: big_f == n - 1          # noqa: E731
    else:
        enough = lambda big_f: n < (big_f + 1) ** 2    # noqa: E731
    fs, _ = _partial_factor(n - 1, budget, enough) if n > 2 else ({}, [])
    # keep only the primes that are themselves certified
    usable: Dict[int, int] = {}
    for q in sorted(fs):
        big_f = 1
        for r, e in usable.items():
            big_f *= r ** e
        if n < (big_f + 1) ** 2:
            break
        if _pock(q, budget, top, done, chain):
            usable[q] = fs[q]
    big_f = 1
    for q, e in usable.items():
        big_f *= q ** e
    if not n < (big_f + 1) ** 2:
        return False
    entry_fs = []
    for q, e in sorted(usable.items()):
        for a in range(2 if n > 2 else 1, min(n, 10_000)):
            if _witness_ok(n, (q, e, a)):
                entry_fs.append([q, e, a])
                break
        else:
            return False
    entry = [n, entry_fs]
    if not _check_pentry(set(done), n, entry_fs):
        return False
    chain.append(entry)
    done[n] = entry
    return True


#: The Phase 140 part B control: with this off, no N+1 certificate is tried.
LUCAS = True

#: The values of ``P`` an N+1 entry tries.
LUCAS_P_LIMIT = 2000


def _lucas_entry(n: int, budget: _Budget, done: Dict[int, list],
                 chain: list) -> bool:
    """An N+1 entry for ``n``: all of ``n + 1`` split, every prime of it
    certified (by :func:`_mixed`), one ``P`` giving ``X`` order ``n + 1``."""
    fs, left = _partial_factor(n + 1, budget, lambda big_f: big_f == n + 1)
    big_f = 1
    for q, e in fs.items():
        big_f *= q ** e
    if left or big_f != n + 1:
        return False
    for q in sorted(fs):
        if not _mixed(q, budget, done, chain):
            return False
    qs = sorted(fs)
    for big_p in range(3, LUCAS_P_LIMIT):
        if _qpow(n, big_p, (0, 1), n + 1) != (1, 0):
            continue
        if all(_lucas_q_ok(n, big_p, q) for q in qs):
            entry_fs = [[q, fs[q]] for q in qs]
            if not _check_lentry(set(done), n, big_p, entry_fs):
                return False
            entry = [n, big_p, entry_fs]
            chain.append(entry)
            done[n] = entry
            return True
    return False


def _pock_entry(n: int, budget: _Budget, done: Dict[int, list],
                chain: list) -> bool:
    """A Pocklington entry for ``n`` whose primes are certified by
    :func:`_mixed`."""
    if n < 2000:
        enough = lambda big_f: big_f == n - 1          # noqa: E731
    else:
        enough = lambda big_f: n < (big_f + 1) ** 2    # noqa: E731
    fs, _ = _partial_factor(n - 1, budget, enough) if n > 2 else ({}, [])
    usable: Dict[int, int] = {}
    for q in sorted(fs):
        big_f = 1
        for r, e in usable.items():
            big_f *= r ** e
        if n < (big_f + 1) ** 2:
            break
        if _mixed(q, budget, done, chain):
            usable[q] = fs[q]
    big_f = 1
    for q, e in usable.items():
        big_f *= q ** e
    if not n < (big_f + 1) ** 2:
        return False
    entry_fs = []
    for q, e in sorted(usable.items()):
        for a in range(2 if n > 2 else 1, min(n, 10_000)):
            if _witness_ok(n, (q, e, a)):
                entry_fs.append([q, e, a])
                break
        else:
            return False
    if not _check_pentry(set(done), n, entry_fs):
        return False
    entry = [n, entry_fs]
    chain.append(entry)
    done[n] = entry
    return True


def _mixed(n: int, budget: _Budget, done: Dict[int, list],
           chain: list) -> bool:
    """Certify ``n`` by an N+1 entry or a Pocklington entry, whichever the
    budget reaches first (small numbers by Pocklington, which then needs
    the whole of ``n - 1``)."""
    if n in done:
        return True
    if n < 2000:
        return _pock_entry(n, budget, done, chain)
    if not _probable_prime(n):
        return False
    return (_lucas_entry(n, budget, done, chain)
            or _pock_entry(n, budget, done, chain))


#: The Phase 141 control: with this off, no elliptic certificate is tried
#: and :func:`certify` behaves exactly as in Phase 140.
ELLIPTIC = True


def _lucas(n: int) -> Dict[str, object]:
    chain: list = []
    if not _mixed(n, _Budget(n), {}, chain):
        raise NoCertificate(n, n)
    return {"kind": "lucas", "chain": chain}


def _pocklington(n: int) -> Dict[str, object]:
    chain: list = []
    if not _pock(n, _Budget(n), n, {}, chain):
        raise NoCertificate(n, n)
    return {"kind": "pocklington", "chain": chain}


def certify(n: int) -> Dict[str, object]:
    """A certificate that :func:`check` accepts for ``n``; raises
    :class:`NoCertificate` if the work budget runs out first.

    Pratt first, exactly as in Phase 139; only when its budget runs out is a
    Pocklington certificate searched for, with a fresh budget of its own.
    When both run out the refusal names the cofactor the Pratt search could
    not split."""
    if n < 2:
        return {"kind": "small"}
    comp = _composite_certificate(n)
    if comp is not None:
        return comp
    chain: list = []
    try:
        _pratt(n, _Budget(n), n, {}, chain)
    except NoCertificate as first:
        if not POCKLINGTON or not _probable_prime(n):
            raise
        try:
            cert = _pocklington(n)
        except NoCertificate:
            if not LUCAS:
                raise first
            try:
                cert = _lucas(n)
            except NoCertificate:
                if not ELLIPTIC:
                    raise first
                from . import elliptic_certificate as ec
                try:
                    cert = ec.elliptic(n)
                except NoCertificate:
                    raise first
        assert check(n, cert) == "prime"
        return cert
    cert = {"kind": "pratt", "chain": chain}
    assert check(n, cert) == "prime"
    return cert


def verdict(n: int) -> Tuple[str, Dict[str, object]]:
    """``(verdict, certificate)`` with the certificate already checked."""
    cert = certify(n)
    return check(n, cert), cert
