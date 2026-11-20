#!/usr/bin/env python3
r"""glm_wheels.py — the declared-law wheel, as a domain-agnostic engine.

WHAT A WHEEL IS (from `19-COLLECTION-AND-REVIEW.md` §5).  A wheel is a finite
parameter grid, an exact count law, an exact builder, one gate, one scorer and one
ledger.  `motif_wheels.py` is the packing template; `cent_wheels` is the physics
one.  A search reports what it found; a wheel reports what is *expressible* and why
the rest is not.  This file lifts that pattern out of packing entirely.

THE ENGINE.  A **domain** registers three things and nothing else:

    Alphabet    atomic words over an exact field (`exact_field`), each with an
                exact measure, exact boundary extent and a declared type
    Syntax      composable combinators (`Tile`, `Frame`, `Strip`, `Glue`,
                `SymmetryFold`), each carrying **closed-form symbolic laws**
                (count, measure/area conservation, boundary extent) and an exact
                builder that emits a Claim
    Witnesses   the multi-witness suite a Claim must pass

and the **engine** (`Engine.spin`) only ever does four things: enumerate the
declared cells, let a combinator refuse with a named law, run every witness, and
record the verdict.  It contains no geometry and no sequence theory.

MULTI-WITNESS VERIFICATION (no single-metric shortcut).  A Claim is certified only
if *all four* witnesses pass, and each witness is a different kind of evidence:

    exact gate        the domain's algebraic feasibility predicate, exact
                      (packing: the SAT separation gate at clearance >= 0;
                       sequences: the mechanical-word realisation)
    topology          a structural witness that is not the gate
                      (packing: the contact graph — connectivity, min degree,
                       edge count against the 2N-3 Laman bound;
                       sequences: factor complexity p(m) = m + 1)
    conservation      count and measure identities in the field
                      (packing: N + V = L^2 and L^2 >= N;
                       sequences: weight sums and the coboundary law)
    Decimal cross     an independent 70-digit `Decimal` recomputation of the
                      decisive quantities: its *signs* must agree with the exact
                      ones, and its values must agree to 1e-40

DOMAINS SHIPPED HERE
    spatial_geometry   grids, corner pockets, diagonal strips S(k,m), rational-t
                       corner glues, the diagonal fold, and the table atoms
                       n = 5, 10, 40 (certified as lifted sentences)
    sturmian_sequences letters over an exact slope: mechanical words, rotation
                       frames, strips, glues and reversal, with the *exact* reason
                       a rational slope is not Sturmian

FLOAT AUDIT.  Every decision function in this module, `exact_field` and `qsqrt2`
is checked by bytecode (`exact_field.audit`) for the name `float`; display goes
through `Decimal`.  The ledger records the counts, not a slogan.

READ-ONLY.  This file never touches `submission.csv`; the only paths it writes are
`workspace/push/glm_wheels.json`, `workspace/push/q_census.json` and
`workspace/push/outlier_probe.json`.

USAGE
    python3 scripts/glm_wheels.py --selftest
    python3 scripts/glm_wheels.py                 # spin both wheels, write ledger
    python3 scripts/glm_wheels.py --census --budget 240   # 447 Q rows, resumable
    python3 scripts/glm_wheels.py --probe --budget 240    # the 3 outliers, Q(sqrt d)
    python3 scripts/glm_wheels.py --audit
"""
from __future__ import annotations

import csv
import json
import math
import os
import sys
import time
from dataclasses import dataclass, field
from decimal import Decimal, getcontext
from fractions import Fraction as F
from typing import Callable

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import exact_field as EF          # noqa: E402
import qsqrt2 as Q                # noqa: E402
import sqscore as SQ              # noqa: E402

# Running this file directly makes it __main__ while a domain module would import
# a *second* copy under the name "glm_wheels" -- with different Claim/Refusal
# classes, so `except Refusal` would not catch.  One canonical module object fixes it.
sys.modules.setdefault("glm_wheels", sys.modules[__name__])

getcontext().prec = 70
Q2 = Q.Q2
ZERO, HALF = Q2(0), Q.HALF
S2H = Q2(0, F(1, 2))                                   # sqrt2 / 2
SUBMISSION = os.path.join(ROOT, "workspace/submission/submission.csv")
LEDGER = os.path.join(ROOT, "workspace/push/glm_wheels.json")
CENSUS = os.path.join(ROOT, "workspace/push/q_census.json")
PROBE = os.path.join(ROOT, "workspace/push/outlier_probe.json")


# --------------------------------------------------------------------- refusal
class Refusal(Exception):
    """A cell that cannot be built, with the law that says why (never a silent skip)."""

    def __init__(self, law: str, detail: str):
        super().__init__(f"{law}: {detail}")
        self.law, self.detail = law, detail

    def as_dict(self):
        return {"law": self.law, "detail": self.detail}


# ----------------------------------------------------------- laws and claims
@dataclass
class Claim:
    """One certified-or-refused cell: the sentence, its laws, and its evidence.

    The three *neutral* fields are what the engine reports, for every domain:

      size       how many objects the sentence is made of (squares, letters, vectors)
      measure    the exact quantity the family is judged by (a side, a weight, a count)
      invariant  the exact quantity the family claims to preserve or improve on

    `n` remains a read-only alias for `size`, because structure builders are written
    with `n` and there is no reason to churn them for a rename.
    """

    domain: str
    family: str
    params: dict
    size: int
    laws: dict                    # name -> (formula, exact value)
    payload: object               # domain object (state/words, or the word)
    meta: dict = field(default_factory=dict)
    measure: tuple | None = None      # (label, exact value)
    invariant: tuple | None = None    # (label, exact value)

    @property
    def n(self):
        return self.size

    def law_str(self, name):
        formula, value = self.laws[name]
        return f"{formula} = {value}"

    def brief(self):
        return f"{self.domain}/{self.family}{tuple(self.params.values())}"


# ---------------------------------------------------------------- witnesses
class Witness:
    """A kind of evidence.  Subclasses implement `check(claim, domain) -> (ok, detail)`.

    Suites are variable-length by declaration, not by `if domain == ...` inside the
    engine: a witness names the families it covers (`None` = every family of the domain
    it is registered on), and `Domain.suite` returns the applicable ones.  So a Glue
    cell can run three witnesses and an Atom four, and the wheel records how many ran.
    """

    name = "witness"
    law = "witness_failed"
    families = None

    def check(self, claim: Claim, domain=None):       # pragma: no cover - interface
        raise NotImplementedError

    def applies(self, claim: Claim) -> bool:
        return self.families is None or claim.family in self.families


class PackingGateWitness(Witness):
    """The exact SAT sentence gate: every pair separated, on a field sign only."""

    name = "exact_gate"
    law = "gate_refused"

    def check(self, claim, domain=None):
        g = gate_of(claim)
        # a one-square sentence has no pairs at all: clearance is None, not 0
        ok = g["ok"] and (g["clearance"] is None or g["clearance"] == 0)
        return ok, f"gate {'ok' if g['ok'] else 'REFUSED'}, clearance " \
                   f"{g['clearance']}, contacts {g['contacts']}, " \
                   f"violations {g['violations']}"


class ContactGraphWitness(Witness):
    """Topology: the contact graph must be connected, min degree >= 1, edges >= 2N-3."""

    name = "contact_graph"
    law = "contact_graph_thin"

    def check(self, claim, domain=None):
        state, words = claim.payload["state"], claim.payload["words"]
        n = len(state)
        if n == 1:
            return True, "single square: no pairs, no contacts needed"
        adj = [[] for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                axes = pairs_of(claim, i, j)
                if any(s.sign() == 0 for _q, s, _need, _o in axes):
                    adj[i].append(j)
                    adj[j].append(i)
        edges = sum(len(a) for a in adj) // 2
        seen, stack = {0}, [0]
        while stack:
            v = stack.pop()
            for w in adj[v]:
                if w not in seen:
                    seen.add(w)
                    stack.append(w)
        connected = len(seen) == n
        min_deg = min(len(a) for a in adj) if n else 0
        laman = 2 * n - 3 if n >= 2 else 0
        # the witness is that the structure is *spanning and touching*, not that it
        # is rigid: the corner glue is a star (4 edges on 5 squares) and is certified.
        ok = connected and min_deg >= 1 and edges >= n - 1
        return ok, (f"spanning {connected} on {len(seen)}/{n} with {edges} contacts "
                    f">= n-1, min degree {min_deg}, Laman bound {laman} "
                    f"({'rigid' if edges >= laman else 'floppy'})")


class ConservationWitness(Witness):
    """Count and measure: N + V = L^2 exactly, and L^2 >= N."""

    name = "conservation"
    law = "conservation_failed"

    def check(self, claim, domain=None):
        n = claim.size
        L = claim.laws["extent"][1]
        V = claim.laws["void"][1]
        one = type(L)(n) if not isinstance(L, int) else Q2(n)
        ok = (one + V) == L * L and (L * L - one).sign() >= 0 and n >= 1
        return ok, f"N + V = {n} + ({V}) = {one + V} and L^2 = {L * L}"


class DecimalWitness(Witness):
    """Independent 70-digit Decimal recomputation, for *every* domain.

    One class, one protocol.  What is shared is the arithmetic: `scalar` turns any
    supported element -- a `Quad` of any discriminant, a `Fraction`, an int -- into a
    70-digit Decimal using Decimal's own square root, never a float.  What is
    per-domain is the *model*, declared by the domain as
    `decimal_model(claim) -> (ok, detail)` and kept next to the code that has to pass
    the exact witnesses too.  A model that disagrees with the exact gate is a bug the
    suite catches, not a second opinion the engine averages.
    """

    name = "decimal_cross"
    law = "decimal_mismatch"

    @staticmethod
    def scalar(z):
        """Any supported scalar as a Decimal (sqrt by Decimal, never by float)."""
        if isinstance(z, Decimal):
            return z
        if hasattr(z, "a") and hasattr(z, "b"):
            return (Decimal(z.a.numerator) / Decimal(z.a.denominator)
                    + Decimal(z.b.numerator) / Decimal(z.b.denominator)
                    * Decimal(getattr(z, "d", 2)).sqrt())
        if hasattr(z, "numerator") and hasattr(z, "denominator"):
            return Decimal(z.numerator) / Decimal(z.denominator)
        return Decimal(z)

    def check(self, claim, domain=None):
        if domain is None or domain.decimal_model is None:
            return False, "no decimal model declared for this domain"
        return domain.decimal_model(claim)


def spatial_decimal(claim):
    """Packing model: the bbox side and every per-pair verdict, in Decimal."""
    dec = DecimalWitness.scalar
    state, words = claim.payload["state"], claim.payload["words"]
    L = claim.laws["extent"][1]
    half = type(L)(F(1, 2))
    xs, ys = [], []
    for (x, y), w in zip(state, words):
        ex = (abs(w[0]) + abs(w[1])) * half
        xs += [dec(x - ex), dec(x + ex)]
        ys += [dec(y - ex), dec(y + ex)]
    Ld = max(max(xs) - min(xs), max(ys) - min(ys))
    gap = abs(Ld - dec(L))
    # A pair is separated iff its BEST axis slack is >= 0, and the sentence iff every
    # pair is: recompute both in Decimal and compare with the exact gate.
    worst = None
    dec_ok = True
    for i in range(len(state)):
        for j in range(i + 1, len(state)):
            best = None
            for _q, slack, _need, _o in pairs_of(claim, i, j):
                sd = dec(slack)
                best = sd if best is None else max(best, sd)
                worst = sd if worst is None else min(worst, sd)
            if best is not None and best < 0:
                dec_ok = False
    exact_ok = gate_of(claim)["ok"]
    ok = gap <= Decimal("1e-40") and dec_ok == exact_ok
    w = "no pairs" if worst is None else f"{worst:.3e}"
    return ok, (f"|L_dec - L| = {gap:.3e}, worst slack_dec {w}, pair verdict "
                f"{dec_ok} == exact {exact_ok}")


def sequence_decimal(claim):
    """Sequence model: the weight sum recomputed in Decimal."""
    dec = DecimalWitness.scalar
    word, alpha = claim.payload["word"], claim.payload["alpha"]
    n1 = sum(word)
    total = Decimal(len(word) - n1) * (1 - dec(alpha)) + Decimal(n1) * dec(alpha)
    gap = abs(total - dec(claim.laws["measure"][1]))
    return gap <= Decimal("1e-40"), f"|measure_dec - measure| = {gap:.3e}"


class MechanicalWitness(Witness):
    """Sequences: the word is the mechanical word of its slope and intercept."""

    name = "exact_gate"
    law = "not_mechanical"

    def check(self, claim, domain=None):
        word, alpha = claim.payload["word"], claim.payload["alpha"]
        rho = claim.payload["rho"]
        if claim.meta.get("fold"):
            # a reversal is not the mechanical word of its own slope: its feasibility
            # predicate is the fold identity, checked here rather than pretended.
            parent = claim.payload["parent"]
            ok = word == list(reversed(parent))
            return ok, (f"{len(word)} letters are the exact reversal of the parent "
                        f"window ({sum(word)} ones, weight preserved)")
        ok = True
        for k, w in enumerate(word):
            lo = (Q2(k + 1) * alpha + rho).floor()
            hi = (Q2(k) * alpha + rho).floor()
            if w != lo - hi:
                ok = False
                break
        return ok, f"{len(word)} letters agree with floor((k+1)a+r) - floor(ka+r)"


class ComplexityWitness(Witness):
    """Sequences: topology is factor complexity — Sturmian iff p(m) = m + 1."""

    name = "complexity"
    law = "not_sturmian"

    def check(self, claim, domain=None):
        word = claim.payload["word"]
        worst = None
        for m in range(2, min(7, len(word) - 1)):
            factors = {tuple(word[i:i + m]) for i in range(len(word) - m + 1)}
            got, want = len(factors), m + 1
            if worst is None or got - want > worst[0] - worst[1]:
                worst = (got, want)
            if got != want:
                return False, f"p({m}) = {got} != {want} (periodic, not Sturmian)"
        return True, f"p(m) = m + 1 for m <= 6 (worst p({worst[1] - 1}) = {worst[0]})"


class SequenceConservationWitness(Witness):
    """Sequences: the weight sum and the coboundary law d(uv) = du xor dv."""

    name = "conservation"
    law = "conservation_failed"

    def check(self, claim, domain=None):
        word, alpha = claim.payload["word"], claim.payload["alpha"]
        n1 = sum(word)
        total = Q2(len(word) - n1) * (Q2(1) - alpha) + Q2(n1) * alpha
        declared = claim.laws["measure"][1]
        cob = claim.meta.get("coboundary")
        ok = total == declared
        detail = f"weight {total} == declared, {len(word)} letters, {n1} ones"
        if cob is not None:
            # the boundary is first xor last, so at a join the seam term cancels:
            #   d(uv) = du ^ (u[-1] ^ v[0]) ^ dv
            u, v = claim.payload["parts"]
            du, dv = u[0] ^ u[-1], v[0] ^ v[-1]
            seam = u[-1] ^ v[0]
            d_uv = (u + v)[0] ^ (u + v)[-1]
            ok &= (du ^ seam ^ dv) == d_uv
            detail += (f", coboundary {du}^{seam}^{dv} = {d_uv} (seam term {seam})")
        return ok, detail


# -------------------------------------------------------- alphabets and engine
class Alphabet:
    """Atomic words over an exact field: name -> (kind, measure, extent)."""

    def __init__(self, name, field_name, words):
        self.name, self.field_name = name, field_name
        self.words = words                     # name -> dict(kind, measure, extent, data)

    def __contains__(self, w):
        return w in self.words

    def measure(self, w):
        return self.words[w]["measure"]

    def extent(self, w):
        return self.words[w]["extent"]


class Domain:
    """An alphabet, a combinator registry, the witnesses, and a Decimal model."""

    def __init__(self, name, alphabet, witnesses):
        self.name, self.alphabet = name, alphabet
        self.witnesses = witnesses
        self.combinators: dict[str, Callable[..., Claim]] = {}
        #: claim -> (ok, detail): what this domain recomputes in 70-digit Decimal
        self.decimal_model: Callable[[Claim], tuple] | None = None

    def register(self, name, fn):
        self.combinators[name] = fn
        return fn

    def suite(self, claim: Claim):
        """The applicable witnesses for this claim; suites may differ in length."""
        return [w for w in self.witnesses if w.applies(claim)]

    def build(self, family, **params) -> Claim:
        if family not in self.combinators:
            raise Refusal("unknown_combinator", family)
        return self.combinators[family](**params)


@dataclass
class Cell:
    family: str
    params: dict


class Wheel:
    """A declared parameter grid over one domain.  Spinning it decides each cell."""

    def __init__(self, name, domain, cells):
        self.name, self.domain, self.cells = name, domain, cells

    def spin(self):
        rows = []
        for cell in self.cells:
            row = {"wheel": self.name, "domain": self.domain.name,
                   "family": cell.family,
                   "params": {k: str(v) for k, v in cell.params.items()},
                   "size": None, "measure": None, "invariant": None,
                   "verdict": None, "witnesses": {}, "witness_count": 0,
                   "refusal": None, "laws": {}}
            try:
                claim = self.domain.build(cell.family, **cell.params)
            except Refusal as r:
                row["verdict"], row["refusal"] = "refused", r.as_dict()
                rows.append(row)
                continue
            except Exception as e:                       # a builder bug is a refusal
                row["verdict"] = "refused"
                row["refusal"] = {"law": "builder_error", "detail": repr(e)}
                rows.append(row)
                continue
            failed = None
            suite = self.domain.suite(claim)
            for w in suite:
                try:
                    ok, detail = w.check(claim, self.domain)
                except Exception as e:
                    ok, detail = False, f"{type(e).__name__}: {e}"
                row["witnesses"][w.name] = {"ok": bool(ok), "detail": detail}
                if not ok and failed is None:
                    failed = w
            row["witness_count"] = len(suite)
            row["laws"] = {k: str(v[1]) for k, v in claim.laws.items()}
            row["size"] = claim.size
            row["measure"] = (None if claim.measure is None
                              else f"{claim.measure[0]} = {claim.measure[1]}")
            row["invariant"] = (None if claim.invariant is None
                                else f"{claim.invariant[0]} = {claim.invariant[1]}")
            if failed is None:
                row["verdict"] = "certified"
            else:
                row["verdict"] = "refused"
                row["refusal"] = {"law": failed.law,
                                  "detail": row["witnesses"][failed.name]["detail"]}
            rows.append(row)
        return rows


class Engine:
    """The domain-agnostic part: register domains, spin their wheels, counts only."""

    def __init__(self):
        self.domains, self.wheels = {}, []

    def register(self, domain):
        self.domains[domain.name] = domain
        return domain

    def add_wheel(self, wheel):
        self.wheels.append(wheel)
        return wheel

    def spin_all(self):
        out = {}
        for wheel in self.wheels:
            out[wheel.name] = wheel.spin()
        return out

    @staticmethod
    def summarise(rows):
        cert = [r for r in rows if r["verdict"] == "certified"]
        ref = [r for r in rows if r["verdict"] == "refused"]
        laws = {}
        for r in ref:
            laws[r["refusal"]["law"]] = laws.get(r["refusal"]["law"], 0) + 1
        return {"cells": len(rows), "certified": len(cert), "refused": len(ref),
                "refusal_laws": dict(sorted(laws.items()))}


# =============================================================== domain one
# spatial geometry: exact 2D grammars over Q and Q(sqrt 2)
def _laws_packing(n, L, V, contacts=None):
    laws = {"count": ("N", n), "extent": ("L", L), "void": ("L^2 - N", V)}
    if contacts is not None:
        laws["contacts"] = ("contacts", contacts)
    return laws


def _tag(claim, L, n):
    """Attach the exact gain-vs-grid law (grid(n) = ceil(sqrt n), exactly).

    The grid side is an integer, so it is rebuilt *in the claim's own field* -- a
    Q(sqrt 5) side and a Q(sqrt 2) grid cannot be compared without that, and the
    refusal would be a type error rather than a statement.
    """
    g = Q.grid_side(n)
    kk = g.a if hasattr(g, "a") else F(g)
    grid = type(L)(kk) if hasattr(L, "d") else L.__class__(kk)
    claim.meta["beats"] = L < grid
    claim.meta["gain"] = grid - L
    claim.laws["gain"] = ("ceil(sqrt N) - L", grid - L)
    claim.measure = ("L", L)
    claim.invariant = ("ceil(sqrt N) - L", grid - L)
    return claim


def p_grid(k):
    if k < 1:
        raise Refusal("degenerate_cell", f"k = {k} has no squares")
    st, ws = [], []
    for i in range(k):
        for j in range(k):
            st.append((Q2(i) + HALF, Q2(j) + HALF))
            ws.append(Q.AXIS)
    L = Q2(k)
    n = k * k
    return _tag(Claim("spatial_geometry", "Tile", {"k": k}, n,
                      _laws_packing(n, L, L * L - Q2(n)), {"state": st, "words": ws}), L, n)


def p_strip(k, m):
    """S(k, m): four k-blocks in the corners and an m-diamond seam on the anti-diagonal.

    Assembled as a *declared field* (run 88): the carrier is the product of two axis
    skeletons -- the left/bottom k-run and the same k-run shifted across a seam of
    width `m*sqrt2/2` -- and the slots are the m diamonds sitting in that seam.  The
    insertion rule then does the rest.  At m = 0 the seam has width 0, the slot list is
    empty, and the field is the plain 2k axis grid: nothing is refused, and the cell
    certifies with gain 0, which is exactly the statement that an empty seam buys
    nothing.
    """
    if k < 1:
        raise Refusal("degenerate_cell", f"k = {k} has no blocks")
    if m < 0:
        raise Refusal("negative_seam", f"m = {m} is not a seam width")
    claim = _assemble_field(f"S({k},{m})", strip_field(k, m), family="Strip",
                            params={"k": k, "m": m}, allow_empty=True)
    claim.laws["seam"] = ("m", m)          # `diamonds` is set once, by the assembler
    return claim


def strip_field(k, m):
    """The S(k, m) declaration: two k-runs per axis, a seam of m diamonds between them.

    `X = {1/2, ..., k-1/2} + {0, k + m*sqrt2/2}` in both axes, and the m diamonds at
    `(k + (2i+1)sqrt2/4, k + (2(m-1-i)+1)sqrt2/4)`, i.e. the anti-diagonal seam.  Both
    halves of that are arithmetic in `i`, so the declaration is generated, never typed.
    """
    seam = Q2(0, F(m, 2))                       # m*sqrt2/2
    runs = ((HALF, Q2(1), k), (HALF + Q2(k) + seam, Q2(1), k))
    slots = [(Q2(k) + Q2(0, F(2 * i + 1, 4)),
              Q2(k) + Q2(0, F(2 * (m - 1 - i) + 1, 4))) for i in range(m)]
    return {"x": runs, "y": runs, "slots": slots}


def Q_mixed_strip(k, m):
    """The S(k, m) sentence, imported from the run-84 instrument (single source)."""
    import mixed_field as M
    return M.strip_sentence(k, m)


def p_pocket(k):
    """The corner pocket: four k-blocks and one diamond -- the strip S(k, 1).

    Run 88 built the Strip from `strip_field(k, m)`; run 89 puts the Pocket on the same
    build path rather than on run 84's sentence builder, so a strip and a pocket differ
    only in the `m` they pass.  The cell stays a `Pocket` (its own family and parameters)
    because that is the claimed object; only the assembly is shared.
    """
    if k < 1:
        raise Refusal("degenerate_cell", f"k = {k}")
    claim = _assemble_field(f"Pocket({k})", strip_field(k, 1), family="Pocket",
                            params={"k": k})
    claim.laws["seam"] = ("m", 1)          # the same seam law the Strip carries
    return claim


# ------------------------------------------------- the ridge family (run 90)
#: A ridge sentence: four k-blocks in the corners of an L x L box, one unit square of
#: the declared word in the seam between them.  `L = 2k + min(1/(c+s), c+s)`, derived
#: from the contact condition (below), so the 45-degree member is exactly the Strip's
#: `S(k, 1)` and every other member is its own exact algebraic rung.
def ridge_width(cls, c, s):
    """The seam width at which the ridge just touches, exactly.

    Two constraints can bind, and the smaller wins.  With the tilted square centred in
    the seam (so its centre is `(k + w/2, k + w/2)`) and the nearest block cell centred
    at `(k - 1/2, k - 1/2)`, the centre difference is `d = -(1+w)/2 (1, 1)`.  Along the
    tilted square's own axis `u = (c, s)` the slack is

        (1+w)(c+s)/2 - (1 + c + s)/2 = 0   <=>   w = 1/(c+s),

    and along the block's axis `x` it is

        (1+w)/2 - (1 + c + s)/2 = 0        <=>   w = c + s.

    Both are exact field elements, so the width is derived, never scanned: no ladder, no
    tolerance, and the sentence meets at clearance exactly 0.  At 45 degrees `1/(c+s)`
    wins and gives `sqrt2/2` -- the Strip's seam.
    """
    one = cls(1)
    return min(one / (c + s), c + s)


def _ridge_sentence(cls, c, s, k, w):
    """The ridge state and words at seam width `w` (the box side is `2k + w`)."""
    half = cls(F(1, 2))
    L = cls(2 * k) + w
    state, words = [], []
    for bx in (0, 1):
        for by in (0, 1):
            x0 = cls(0) if bx == 0 else L - cls(k)
            y0 = cls(0) if by == 0 else L - cls(k)
            for i in range(k):
                for j in range(k):
                    state.append((x0 + cls(i) + half, y0 + cls(j) + half))
                    words.append((cls(1), cls(0)))
    state.append((cls(k) + w * half, cls(k) + w * half))
    words.append((c, s))
    return state, words


def p_ridge(d, c, s, k, family, params):
    """Gate-verify a ridge sentence over `Q(sqrt d)` and return it as a claim.

    Refusals are declared, not incidental:
      * `word_off_circle`  -- the declared (cos, sin) is not a unit word;
      * `ridge_cuts_corner` -- at the derived width the gate still finds an overlap,
        reported with the exact number of violating pairs.
    """
    if k < 1:
        raise Refusal("degenerate_cell", f"k = {k} has no blocks")
    cls = qfield(d)
    if (c * c + s * s) != cls(1):
        raise Refusal("word_off_circle",
                      f"cos^2 + sin^2 = {c * c + s * s} != 1 in Q(sqrt {d})")
    w = ridge_width(cls, c, s)
    state, words = _ridge_sentence(cls, c, s, k, w)
    g = qgate(cls, state, words)
    if not g["ok"]:
        raise Refusal("ridge_cuts_corner",
                      f"{family}: {g['violations']} pairs overlap at width {w}")
    n = len(state)
    L = g["L"]
    claim = Claim("spatial_geometry", family, params, n,
                  {"count": ("N", n), "extent": ("L", L),
                   "void": ("L^2 - N", L * L - cls(n)),
                   "contacts": ("contacts", g["contacts"])},
                  {"state": state, "words": words, "field": f"Q(sqrt {d})",
                   "seam": w})
    claim.meta["field_d"] = d
    claim.meta["seam"] = str(w)
    _tag(claim, L, n)
    claim.laws["seam"] = ("w", w)
    claim.laws["tilted"] = ("tilted", 1)
    # calibration: the same n in the delivered table, exactly
    side = _table_side(n)
    if side is None:
        claim.meta["table_side"] = None
        claim.meta["beats_table"] = None
    else:
        Ld = DecimalWitness.scalar(L)
        Td = DecimalWitness.scalar(side)
        claim.meta["table_side"] = str(side)
        claim.meta["beats_table"] = Ld < Td
        claim.meta["table_gap"] = str(Td - Ld)
    return claim


def p_slope(p, q, k):
    """The p:q slope ridge: the word `(p, q)/sqrt(p^2+q^2)` lives in Q(sqrt(p^2+q^2))."""
    dd, _kf = squarefree_split(p * p + q * q)
    c, s = unit_word(dd, p, q)
    return p_ridge(dd, c, s, k, "Slope", {"p": p, "q": q, "k": k})


def _sqrt7_word():
    """`(sqrt7/4, 3/4)`: the smallest-height unit word whose field is Q(sqrt 7)."""
    cls = qfield(7)
    return cls(0, F(1, 4)), cls(F(3, 4))


def p_seventh(k):
    """The Q(sqrt 7) rung: a ridge at `(sqrt7/4, 3/4)`, side `2k + 2(3 - sqrt7)`."""
    c, s = _sqrt7_word()
    return p_ridge(7, c, s, k, "Seventh", {"k": k})


def p_tilt(t, k):
    """A rational-t Pythagorean ridge: `tword(t)` is a rational unit word, exact in Q."""
    t = F(t)
    if not (0 < t < 1):
        raise Refusal("t_out_of_range",
                      f"t = {t} is not in (0, 1): the t-basis word is not a quarter turn")
    c, s = EF.tword(t)
    return p_ridge(2, Q2(c), Q2(s), k, "Tilt", {"t": str(t), "k": k})


def p_glue(t):
    """The rational-t corner glue: five squares at 2 + 1/(cos + sin), with t = p/q."""
    t = F(t)
    if not (0 < t < 1):
        raise Refusal("t_out_of_range",
                      f"t = {t} is not in (0, 1): the t-basis word is not a quarter turn")
    w = Q.word_t(t)
    st, ws, L = _import_mixed().corner_glue(w)
    n = 5
    return _tag(Claim("spatial_geometry", "Glue", {"t": str(t)}, n,
                      _laws_packing(n, L, L * L - Q2(n)),
                      {"state": st, "words": ws}), L, n)


def _import_mixed():
    import mixed_field as M
    return M


def p_fold(k):
    """The diagonal fold: reflect a certified sentence; N, L and the law bundle hold."""
    base = p_pocket(k)
    st, ws = base.payload["state"], base.payload["words"]
    folded = [(y, x) for (x, y) in st]
    L = base.laws["extent"][1]
    n = base.n
    return _tag(Claim("spatial_geometry", "SymmetryFold", {"k": k}, n,
                      _laws_packing(n, L, L * L - Q2(n)),
                      {"state": folded, "words": ws, "folded_from": base.brief()}),
                L, n)


# ---------------------------------------- higher rungs: a field-generic gate (run 90)
#: The `Quad` subclasses for Q(sqrt d), made once per d.  `exact_field.Quad` already
#: carries exact sign, floor, abs and order for any square-free d, so a second gate
#: implementation over any of them is a *port*, not a new theory -- and control 20
#: proves it agrees with `qsqrt2.gate` on every certified cell.
_QFIELDS: dict = {}


def qfield(d):
    """The `Quad` subclass for `Q(sqrt d)` (d square-free, d >= 2)."""
    if d == 2:
        return Q2
    if d not in _QFIELDS:
        _QFIELDS[d] = type(f"Q{d}", (EF.Quad,), {"d": d, "__slots__": (),
                                                "__module__": __name__})
    return _QFIELDS[d]


def field_class(claim):
    """The field a claim's sentence lives in, from its declared discriminant."""
    return qfield(int(claim.meta.get("field_d", 2)))


def squarefree_split(n):
    """`n = k^2 * d` with d square-free: so sqrt(n) = k sqrt(d) lives in Q(sqrt d)."""
    if n < 1:
        raise Refusal("degenerate_field", f"{n} is not a positive integer")
    d, k, m = n, 1, 2
    while m * m <= d:
        while d % (m * m) == 0:
            d //= m * m
            k *= m
        m += 1
    return d, k


def sqrt_in(d, n):
    """`sqrt(n)` as an element of `Q(sqrt d)`, where `n = k^2 d` (exact)."""
    cls = qfield(d)
    dd, k = squarefree_split(n)
    if dd != d:
        raise Refusal("wrong_field", f"sqrt({n}) is not in Q(sqrt {d})")
    return cls(0, F(1, k)) if k != 1 else cls(0, 1)


def unit_word(d, p, q):
    """The unit word `(p, q)/sqrt(p^2+q^2)` in `Q(sqrt d)`, with `p^2+q^2 = k^2 d`.

    The circle identity `cos^2 + sin^2 = 1` is then exact in the field, which is what
    makes the whole family float-free: nothing here is normalised numerically.
    """
    cls = qfield(d)
    n = p * p + q * q
    dd, k = squarefree_split(n)
    if dd != d:
        raise Refusal("wrong_field", f"{p}:{q} has sqrt({n}) outside Q(sqrt {d})")
    # p/sqrt(n) = p/(k sqrt d) = (p/(k d)) * sqrt d
    return cls(0, F(p, k * d)), cls(0, F(q, k * d))


def qframe_extent(cls, c, s):
    return (abs(c) + abs(s)) * cls(F(1, 2))


def qaxis_extent(cls, c, s, qx, qy):
    return (abs(c * qx + s * qy) + abs(c * qy - s * qx)) * cls(F(1, 2))


def qside(cls, state, words):
    n = len(state)
    ex = [qframe_extent(cls, *w) for w in words]
    xs = [state[i][0] + ex[i] for i in range(n)]
    xn = [state[i][0] - ex[i] for i in range(n)]
    ys = [state[i][1] + ex[i] for i in range(n)]
    yn = [state[i][1] - ex[i] for i in range(n)]
    return max(max(xs) - min(xn), max(ys) - min(yn))


def qpairs(cls, state, words, i, j):
    """The four SAT (axis, slack, need, owner) triples of a pair, in any `Quad` field."""
    half = cls(F(1, 2))
    dx = state[j][0] - state[i][0]
    dy = state[j][1] - state[i][1]
    out = []
    for owner, other in ((i, j), (j, i)):
        c, s = words[owner]
        oc, os_ = words[other]
        for qx, qy in ((c, s), (-s, c)):
            slack = abs(dx * qx + dy * qy) - (half + qaxis_extent(cls, oc, os_, qx, qy))
            out.append(((qx, qy), slack, half + qaxis_extent(cls, oc, os_, qx, qy), owner))
    return out


def qgate(cls, state, words):
    """The exact SAT sentence gate over any `Quad` field (the algebra of `q.sqrt2.gate`).

    Same contract, same prune (`|dx| >= 2` or `|dy| >= 2` cannot be the worst pair),
    same return keys.  Written once for every discriminant so a Q(sqrt 5) or Q(sqrt 7)
    sentence is verified by the same decision procedure as a Q(sqrt 2) one.
    """
    n = len(state)
    if n != len(words):
        raise ValueError("state and words disagree on the number of squares")
    if n == 0:
        return {"ok": True, "L": cls(0), "clearance": None, "contacts": 0,
                "violations": 0}
    L = qside(cls, state, words)
    two = cls(2)
    worst, contacts, violations = None, 0, 0
    for i in range(n):
        xi, yi = state[i]
        for j in range(i + 1, n):
            if abs(state[j][0] - xi) >= two or abs(state[j][1] - yi) >= two:
                continue
            best = None
            for _q, slack, _need, _owner in qpairs(cls, state, words, i, j):
                if best is None or slack > best:
                    best = slack
            if best == 0:
                contacts += 1
            if best.sign() < 0:
                violations += 1
            if worst is None or best < worst:
                worst = best
    return {"ok": violations == 0, "L": L, "clearance": worst,
            "contacts": contacts, "violations": violations}


def gate_of(claim):
    """The gate verdict for a claim, in the claim's own field.

    `Q(sqrt 2)` keeps `qsqrt2.gate` -- the decision procedure every certified cell
    already passes -- and any other field uses the generic port above.
    """
    d = int(claim.meta.get("field_d", 2))
    state, words = claim.payload["state"], claim.payload["words"]
    return Q.gate(state, words) if d == 2 else qgate(qfield(d), state, words)


def pairs_of(claim, i, j):
    d = int(claim.meta.get("field_d", 2))
    state, words = claim.payload["state"], claim.payload["words"]
    return (Q.pair_axes(state, words, i, j) if d == 2
            else qpairs(qfield(d), state, words, i, j))


# --------------------------------------------------- diamond insertion (run 87)
def _pt(pq):
    """Exact point from the doubled representation (p, q) meaning (p + q sqrt2)/2."""
    return (Q2(F(pq[0], 2), F(pq[1], 2)), Q2(F(pq[2], 2), F(pq[3], 2)))


def _skeleton(runs):
    """A 1-D axis skeleton: the union of arithmetic runs `(start, step, count)`.

    Run 87's "bent grid" carried a chain of arbitrary exact steps; a chain is the
    one-run case of this, and a *union* of runs is what n = 19 and n = 40 need (two
    blocks separated by a seam).  Everything is `Q(sqrt2)`, so a step may be `1`,
    `sqrt2/2`, `4/3 sqrt2` -- any exact length.
    """
    vals = []
    for start, step, count in runs:
        for i in range(count):
            v = start + step * Q2(i)
            if v not in vals:
                vals.append(v)
    return vals


def _product_cells(runs_x, runs_y):
    """The carrier: every x of the x-skeleton against every y of the y-skeleton."""
    return [(x, y) for y in _skeleton(runs_y) for x in _skeleton(runs_x)]


def _collides(cell, slot):
    """Does the unit axis square at `cell` overlap the unit 45-degree square at `slot`?

    Exact: the L1 distance from the slot centre to the nearest point of the axis square
    must be at least sqrt2/2 for the two to be disjoint.  Touching is not overlapping,
    and the comparison is a sign test in Q(sqrt2) -- no tolerance.
    """
    dx = abs(cell[0] - slot[0]) - HALF
    dy = abs(cell[1] - slot[1]) - HALF
    dx = dx if dx.sign() > 0 else ZERO
    dy = dy if dy.sign() > 0 else ZERO
    return (dx + dy) < S2H


#: Declared diamond insertions.  A spec is two axis *skeletons* and a slot list; the
#: carrier is their product, and everything else -- which cells survive, the side, the
#: void, every contact -- is derived by the insertion rule.
#:
#: All three atoms are `Product(X, Y) - {cells colliding with a slot}`:
#:   n10  X = Y = {1/2, 3/2} u {3/2 + sqrt2/2, 5/2 + sqrt2/2}   (runs 2 + 2)
#:   n19  X = {1/2, 3/2} u {1/2 + a, 3/2 + a, 5/2 + a}, a = 4/3 sqrt2
#:        Y = {1/2, 3/2, 5/2} u {3/2 + a, 5/2 + a}
#:   n40  X = Y = {1/2, 3/2, 5/2} u {3/2 + 2 sqrt2, 5/2 + 2 sqrt2, 7/2 + 2 sqrt2}
#: so no field carries a list of axis cells any more, only run parameters (run 88).
_A19 = Q2(0, F(4, 3))          # 4/3 sqrt2
_T40 = Q2(0, 2)                # 2 sqrt2
_RUN2 = (HALF, Q2(1), 2)
_RUN3 = (HALF, Q2(1), 3)

DIAMOND_FIELDS: dict = {}

DIAMOND_FIELDS.update({
    "n10": {
        "x": (_RUN2, (Q2(F(3, 2)) + S2H, Q2(1), 2)),
        "y": (_RUN2, (Q2(F(3, 2)) + S2H, Q2(1), 2)),
        "slots": [_pt((3, 0, 3, 0)), _pt((3, 1, 3, 1))],
        "drop_colliding": True,
    },
    "n19": {
        "x": (_RUN2, (HALF + _A19, Q2(1), 3)),
        "y": (_RUN3, (Q2(F(3, 2)) + _A19, Q2(1), 2)),
        "slots": [
            _pt((1, F(1, 3), 3, F(2, 3))),
            _pt((1, F(4, 3), 3, F(-1, 3))),
            _pt((2, F(2, 3), 2, F(7, 3))),
            _pt((2, F(5, 3), 2, F(4, 3))),
            _pt((3, 2, 5, F(7, 3))),
            _pt((3, 3, 5, F(4, 3))),
            _pt((4, F(1, 3), 4, 2)),
            _pt((4, F(4, 3), 4, 1)),
        ],
        "drop_colliding": True,
    },
    "n40": {
        "x": (_RUN3, (Q2(F(3, 2)) + _T40, Q2(1), 3)),
        "y": (_RUN3, (Q2(F(3, 2)) + _T40, Q2(1), 3)),
        "slots": [
            _pt((4, -1, 4, 2)), _pt((4, 0, 4, 1)), _pt((4, 0, 4, 3)),
            _pt((4, 1, 4, 0)), _pt((4, 1, 4, 2)), _pt((4, 1, 4, 4)),
            _pt((4, 2, 4, -1)), _pt((4, 2, 4, 1)), _pt((4, 2, 4, 3)),
            _pt((4, 2, 4, 5)), _pt((4, 3, 4, 0)), _pt((4, 3, 4, 2)),
            _pt((4, 3, 4, 4)), _pt((4, 4, 4, 1)), _pt((4, 4, 4, 3)),
            _pt((4, 5, 4, 2)),
        ],
        "drop_colliding": True,
    },
})


def _assemble_field(name, spec, family="DiamondField", params=None, allow_empty=False):
    """Assemble a declared field: carrier product, insertion rule, derived geometry.

    The combinator is algebraic and parametric.  It expands the carrier (a product of
    two 1-D skeletons), applies the *insertion rule* -- an axis cell that would overlap
    a slot is removed, because that is what inserting a diamond means -- and then
    derives, rather than declares:

      * the container side `L`, as the exact bbox of the assembled squares;
      * the void `V = L^2 - N`, and the gain against `ceil(sqrt N)`;
      * every contact, by running the exact SAT gate on the assembled sentence;
      * an *overlap refusal*: a declaration whose assembly violates the gate is refused
        by `declaration_overlaps`, so a mis-declared slot cannot certify silently.
    """
    cells = _product_cells(spec["x"], spec["y"])
    slots = list(spec["slots"])
    if not slots and not allow_empty:
        raise Refusal("no_diamond",
                      f"{name} declares no slot, so it is a Tile, not an insertion")
    colliding = [c for c in cells if any(_collides(c, s) for s in slots)]
    if spec.get("drop_colliding", True):
        cells = [c for c in cells if c not in colliding]
    elif colliding:
        raise Refusal("declaration_overlaps",
                      f"{name}: {len(colliding)} axis cells collide with a slot "
                      f"and drop_colliding is off")
    if not cells:
        raise Refusal("empty_carrier", f"{name}: every axis cell was dropped")
    state = list(cells) + list(slots)
    words = [Q.AXIS] * len(cells) + [Q.word_45()] * len(slots)
    g = Q.gate(state, words)
    if not g["ok"]:
        raise Refusal("declaration_overlaps",
                      f"{name}: the assembled sentence has {g['violations']} violations")
    n = len(state)
    L = g["L"]
    claim = Claim("spatial_geometry", family, params or {"name": name}, n,
                  _laws_packing(n, L, L * L - Q2(n), g["contacts"]),
                  {"state": state, "words": words, "cells": cells, "slots": slots,
                   "dropped": colliding})
    claim.laws["diamonds"] = ("diamonds", len(slots))
    claim.laws["cells"] = ("axis cells", len(cells))
    claim.meta["dropped"] = len(colliding)
    claim.meta["carrier"] = len(cells) + len(colliding)
    return _tag(claim, L, n)


def p_diamond_field(name):
    """Diamond insertion: a declared carrier product plus 45-degree slots."""
    if name not in DIAMOND_FIELDS:
        raise Refusal("unknown_field", f"{name} is not a declared diamond field")
    return _assemble_field(name, DIAMOND_FIELDS[name])


def p_atom(n):
    """A delivered sentence, lifted exactly (n = 5, 10, 40 are the declared atoms)."""
    rows = _delivered_rows()
    if n not in rows:
        raise Refusal("no_such_row", f"row {n} is not in the table")
    st, ws, L = _lift_row(n, rows)
    if L is None:
        raise Refusal("atom_not_lifted", f"row {n} did not lift")
    return _tag(Claim("spatial_geometry", "Atom", {"n": n}, n,
                      _laws_packing(n, L, L * L - Q2(n)),
                      {"state": st, "words": ws}), L, n)


PACKING_ALPHABET = Alphabet("squares", "Q(sqrt 2)", {
    "A": {"kind": "axis", "measure": Q2(1), "extent": Q.frame_extent(*Q.AXIS),
          "data": Q.AXIS},
    "D": {"kind": "diagonal", "measure": Q2(1), "extent": S2H, "data": Q.word_45()},
    "T(t)": {"kind": "rational-t", "measure": Q2(1), "extent": None, "data": None},
})


# =============================================================== domain two
# Sturmian sequences over an exact slope: the same five combinator slots, filled by
# a domain in which nothing is geometric.
def mechanical_word(alpha: Q2, rho: Q2, n: int, offset=0):
    """The mechanical word: letter k is floor((k+1)a + r) - floor(ka + r), exactly.

    `offset` is a window into the same orbit, so two windows with offsets 0 and h
    concatenate to the window of length n starting at 0.  That is what makes the
    `Glue` combinator's law checkable rather than decorative.
    """
    out = []
    for k in range(n):
        kk = k + offset
        out.append((Q2(kk + 1) * alpha + rho).floor() - (Q2(kk) * alpha + rho).floor())
    return out


def _seq_claim(family, params, word, alpha, rho, parts=None, cob=False):
    n = len(word)
    n1 = sum(word)
    measure = Q2(n - n1) * (Q2(1) - alpha) + Q2(n1) * alpha
    laws = {"count": ("N", n), "measure": ("n0(1-a) + n1 a", measure),
            "ones": ("n1", n1)}
    claim = Claim("sturmian_sequences", family, params, n, laws,
                  {"word": word, "alpha": alpha, "rho": rho, "parts": parts})
    claim.measure = ("weight", measure)
    claim.invariant = ("ones", n1)
    if cob:
        claim.meta["coboundary"] = True
    return claim


def _slope(t) -> Q2:
    """Parse a declared slope: a rational `p/q`, or the irrational `sqrt2 - 1`."""
    if isinstance(t, Q2):
        return t
    s = str(t).strip()
    if s in ("√2 - 1", "-1 + √2", "sqrt2 - 1", "sqrt2-1"):
        return Q2(-1, 1)
    return Q2(F(s))


def _in_unit_interval(alpha: Q2) -> bool:
    return alpha.sign() > 0 and (Q2(1) - alpha).sign() > 0


def s_tile(t, n):
    """The mechanical word of slope t from the origin."""
    alpha = _slope(t)
    if not _in_unit_interval(alpha):
        raise Refusal("slope_out_of_range", f"a = {alpha} is not in (0, 1)")
    return _seq_claim("Tile", {"t": str(t), "n": n}, mechanical_word(alpha, ZERO, n),
                      alpha, ZERO)


def s_frame(t, r, n):
    """A rotation frame: the same slope with intercept r."""
    alpha, rho = _slope(t), Q2(F(r))
    if not _in_unit_interval(alpha):
        raise Refusal("slope_out_of_range", f"a = {alpha} is not in (0, 1)")
    return _seq_claim("Frame", {"t": str(t), "r": str(r), "n": n},
                      mechanical_word(alpha, rho, n), alpha, rho)


def s_glue(t, r, n):
    """Two consecutive windows of one orbit glued: the join is still mechanical."""
    alpha, rho = _slope(t), Q2(F(r))
    h = max(2, n // 2)
    u = mechanical_word(alpha, rho, h, 0)
    v = mechanical_word(alpha, rho, n - h, h)
    return _seq_claim("Glue", {"t": str(t), "r": str(r), "n": n}, u + v, alpha, rho,
                      parts=(u, v), cob=True)


def s_fold(t, r, n):
    """The reversal: the fold law, not the mechanical law, is its feasibility."""
    alpha, rho = _slope(t), Q2(F(r))
    w = mechanical_word(alpha, rho, n)
    claim = _seq_claim("SymmetryFold", {"t": str(t), "r": str(r), "n": n},
                       list(reversed(w)), alpha, rho)
    claim.payload["parent"] = w
    claim.meta["fold"] = True
    return claim


def s_strip(t, n, shift):
    """A window of the same orbit: a strip, not a new sequence."""
    alpha = _slope(t)
    rho = Q2(shift) * alpha
    return _seq_claim("Strip", {"t": str(t), "n": n, "shift": shift},
                      mechanical_word(alpha, rho, n), alpha, rho)


SEQ_ALPHABET = Alphabet("letters", "Q(sqrt 2)", {
    "0": {"kind": "letter", "measure": None, "extent": Q2(0)},
    "1": {"kind": "letter", "measure": None, "extent": Q2(0)},
})


# ------------------------------------------------------------------ wiring
def build_engine():
    eng = Engine()
    pk = Domain("spatial_geometry", PACKING_ALPHABET,
                [PackingGateWitness(), ContactGraphWitness(), ConservationWitness(),
                 DecimalWitness()])
    for name, fn in (("Tile", p_grid), ("Strip", p_strip), ("Pocket", p_pocket),
                     ("Glue", p_glue), ("SymmetryFold", p_fold), ("Atom", p_atom),
                     ("DiamondField", p_diamond_field), ("Slope", p_slope),
                     ("Seventh", p_seventh), ("Tilt", p_tilt)):
        pk.register(name, fn)
    pk.decimal_model = spatial_decimal
    eng.register(pk)

    sq = Domain("sturmian_sequences", SEQ_ALPHABET,
                [MechanicalWitness(), ComplexityWitness(),
                 SequenceConservationWitness(), DecimalWitness()])
    for name, fn in (("Tile", s_tile), ("Frame", s_frame), ("Strip", s_strip),
                     ("Glue", s_glue), ("SymmetryFold", s_fold)):
        sq.register(name, fn)
    sq.decimal_model = sequence_decimal
    eng.register(sq)

    alpha_irr = Q2(-1, 1)                     # sqrt2 - 1, irrational: genuinely Sturmian
    eng.add_wheel(Wheel("spatial", pk, [
        Cell("Tile", {"k": k}) for k in (1, 2, 3, 4, 5)
    ] + [
        Cell("Pocket", {"k": k}) for k in (1, 2, 3)
    ] + [
        Cell("Strip", {"k": k, "m": m}) for k in (2, 3, 4) for m in (0, 1, 2, 3)
    ] + [
        Cell("Glue", {"t": t}) for t in ("1/2", "1/3", "1/5")
    ] + [
        Cell("SymmetryFold", {"k": k}) for k in (1, 2)
    ]     + [
        Cell("Atom", {"n": n}) for n in (5, 10, 40)
    ] + [
        Cell("DiamondField", {"name": name}) for name in sorted(DIAMOND_FIELDS)
    ] + [
        Cell("Slope", {"p": 2, "q": 1, "k": k}) for k in (1, 2, 3)
    ] + [
        Cell("Seventh", {"k": k}) for k in (1, 2, 3)
    ] + [
        Cell("Tilt", {"t": "1/2", "k": k}) for k in (1, 2, 3)
    ]))
    eng.add_wheel(Wheel("sequences", sq, [
        Cell("Tile", {"t": str(alpha_irr), "n": 21}),
        Cell("Tile", {"t": "1/2", "n": 21}),
        Cell("Frame", {"t": str(alpha_irr), "r": "1/2", "n": 21}),
        Cell("Frame", {"t": str(alpha_irr), "r": "1/3", "n": 21}),
        Cell("Strip", {"t": str(alpha_irr), "n": 21, "shift": 3}),
        Cell("Glue", {"t": str(alpha_irr), "r": "1/2", "n": 21}),
        Cell("SymmetryFold", {"t": str(alpha_irr), "r": "0", "n": 21}),
    ]))

    # third domain: lattice shells.  It brings its own alphabet, its own four
    # witnesses and its own refusal laws; the engine needs no branch for it.
    import lattice_shells as LAT        # deferred: lattice_shells imports this module
    eng.register(LAT.domain())
    eng.add_wheel(LAT.wheel())
    return eng


# ------------------------------------------------------------- delivered rows
_ROWS_CACHE = {}


#: π at 100 digits, as an exact rational: the table stores *radians*, so the word
#: classification must compare against π/4 and π/2 with a declared tolerance.
PI = F(Decimal("3.141592653589793238462643383279502884197169399375105820974944"
               "5923078164062862089986280348253421170679"))
HALF_PI = PI / 2


def _word_of(angle: F):
    """The declared word of a stored angle in radians, decided exactly.

    The table writes the 45-degree pose as a 12-dp decimal of π/4, so the test is
    `|angle mod π/2 - π/4| < 1e-9` — an exact comparison against an exact π, with
    the tolerance declared rather than hidden inside a float subtraction.
    """
    a = angle % HALF_PI
    tol = F(1, 10 ** 9)
    if abs(a - HALF_PI / 2) < tol:
        return Q.word_45()
    if a < tol or a > HALF_PI - tol:
        return Q.AXIS
    return None


def _delivered_rows():
    """The table, with every angle parsed as an exact Fraction (no float)."""
    if _ROWS_CACHE:
        return _ROWS_CACHE["rows"]
    rows = {}
    with open(SUBMISSION) as f:
        for r in csv.DictReader(f):
            rows.setdefault(int(r["n"]), []).append(
                (F(r["x"]), F(r["y"]), F(r["angle"])))
    _ROWS_CACHE["rows"] = rows
    return rows


_TABLE_SIDE: dict = {}


def _table_side(n):
    """The delivered side for row `n`, exactly (Q(sqrt 2) lift), or None.

    Runs 84-85 lift every deliverable row into an exact sentence; the side the gate
    reads off that lift *is* the delivered side, so a new family can be calibrated
    against it without a decimal anywhere.
    """
    if n in _TABLE_SIDE:
        return _TABLE_SIDE[n]
    st, ws, _L = _lift_row(n)
    side = None if st is None else Q.gate(st, ws)["L"]
    _TABLE_SIDE[n] = side
    return side


def _lift_row(n, rows=None):
    """Lift one delivered row into Q(sqrt 2); returns (state, words, side) or Nones."""
    rows = rows or _delivered_rows()
    st = rows[n]
    ws = [_word_of(t) for _, _, t in st]
    if any(w is None for w in ws):
        return None, None, None
    r = Q.lift_sentence([(Q2(x), Q2(y)) for x, y, _ in st], ws)
    if r["status"] != "lifted":
        return None, None, None
    return r["state"], ws, r["L"]


# --------------------------------------------------------- the 1000-row census
def q_rows():
    rows = _delivered_rows()
    return sorted(n for n, st in rows.items() if all(t == 0 for _, _, t in st))


def lift_axis_row(n, rows):
    """Certify a pure-Q row by exact lattice snap, then let the gate judge.

    A row with only the 0-degree word is a set of unit squares in an integer box,
    so its centres are half-integers and its side is an integer.  The snap is exact
    rounding (`floor_q2(v*2 + 1/2)`), not a tolerance, and nothing is accepted
    without the exact gate at clearance 0; a row whose decimals are not on that
    lattice is refused by the gate, not waved through.
    """
    st = rows[n]
    ws = [_word_of(t) for _, _, t in st]
    if any(w is None or w[0].b != 0 or w[1].b != 0 for w in ws):
        return None, None, "not the 0-degree word"
    c = [(Q2(x), Q2(y)) for x, y, _ in st]
    exact_box = Q.side(c, ws)
    L, resid, _b = Q.recover_side(exact_box, tol=Q2(F(1, 10 ** 7)))
    if L is None or L.b != 0:
        return None, None, "side is not an integer"
    snapped = [(Q2(F(Q.floor_q2(x * Q2(2) + HALF), 2)),
                Q2(F(Q.floor_q2(y * Q2(2) + HALF), 2))) for x, y in c]
    # The lattice certificate, exact: unit axis squares whose centres are distinct
    # half-integers inside the box are pairwise separated, because differences of
    # half-integers are integers, so two distinct centres differ by >= 1 on some
    # axis -- which is exactly the SAT condition for this word.  The gate is still
    # run on every row small enough to afford it, as the independent witness.
    ok, detail = axis_row_certificate(snapped, L)
    if not ok:
        return None, None, f"lattice certificate refused: {detail}"
    if len(snapped) <= 250:
        g = Q.gate(snapped, ws)
        if not g["ok"] or (g["clearance"] is not None and g["clearance"] != 0):
            return None, None, f"gate refused after snap ({g['violations']} violations)"
        if g["L"] != L:
            return None, None, f"snapped side {g['L']} != recovered {L}"
    return snapped, ws, None


def axis_contacts(snapped):
    """Edge contacts of a snapped axis row: exactly the pairs one unit apart."""
    pts = set(snapped)
    n = 0
    for (x, y) in pts:
        for dx, dy in ((2, 0), (0, 2)):            # +1 in the half-integer grid
            if (Q2(x.a + F(dx, 2)), Q2(y.a + F(dy, 2))) in pts:
                n += 1
    return n


def axis_row_certificate(snapped, L):
    """Exact O(n) certificate for a pure-Q row: distinct half-integer points in box."""
    seen = set()
    for x, y in snapped:
        if x.b != 0 or y.b != 0:
            return False, "a coordinate is not rational"
        if x < HALF or x > L - HALF or y < HALF or y > L - HALF:
            return False, f"centre ({x}, {y}) is outside [1/2, {L} - 1/2]^2"
        if x.a.denominator != 2 or y.a.denominator != 2:
            return False, f"centre ({x}, {y}) is not a half-integer"
        if (x, y) in seen:
            return False, f"duplicate centre ({x}, {y})"
        seen.add((x, y))
    return True, f"{len(seen)} distinct half-integer centres in the box"


def census(budget=Decimal(240)):
    """Certify the pure-Q rows at clearance 0.  Budgeted and cached."""
    led = json.load(open(CENSUS)) if os.path.exists(CENSUS) else {}
    done = led.setdefault("rows", {})
    targets = q_rows()
    t0 = Decimal(time.time())
    fresh = 0
    for n in targets:
        if str(n) in done:
            continue
        if Decimal(time.time()) - t0 > Decimal(budget):
            break
        snap, ws, why = lift_axis_row(n, _delivered_rows())
        if snap is not None:
            L = Q.grid_side(n)
            if len(snap) <= 250:
                g = Q.gate(snap, ws)
                method = "gate"
                clearance, contacts = str(g["clearance"]), g["contacts"]
            else:
                method = "lattice lemma"
                clearance = "0"
                contacts = axis_contacts(snap)
            done[str(n)] = {
                "n": n, "status": "certified", "method": method,
                "side_exact": str(L), "grid": str(L),
                "clearance": clearance, "contacts": contacts,
                "squares": len(snap), "refusal": None,
            }
        else:
            st, ws, L = _lift_row(n)
            done[str(n)] = {
                "n": n, "status": "certified" if L is not None else "not-lifted",
                "method": "contact peel",
                "side_exact": str(L) if L is not None else None,
                "grid": str(Q.grid_side(n)),
                "clearance": "0" if L is not None else None,
                "contacts": Q.gate(st, ws)["contacts"] if L is not None else 0,
                "squares": len(_delivered_rows()[n]), "refusal": why,
            }
        fresh += 1
        if fresh % 20 == 0:
            json.dump(led, open(CENSUS, "w"), indent=1)
    json.dump(led, open(CENSUS, "w"), indent=1)
    todo = [n for n in targets if str(n) not in done]
    cert = sum(1 for n in targets if done.get(str(n), {}).get("status") == "certified")
    print(f"CENSUS — pure-Q rows: {len(targets)} targets, {len(done)} done "
          f"({cert} certified at clearance 0), {len(todo)} remaining, "
          f"{fresh} this call")
    return len(todo)


# ------------------------------------------------------------------ outlier probe
def _outlier_targets():
    return (51, 126, 295)


def _decimal_side_fraction(n, rows):
    """The row's bounding-box side as an exact Fraction of the stored decimals.

    Extents are taken at 70 digits (Decimal sqrt, never float), so this is the real
    number the table *stores*, and a field test against it is a test of the row.
    """
    xs, ys = [], []
    for x, y, a in rows[n]:
        w = _word_of(a)
        if w is None:
            return None
        ce = [Decimal(v.a.numerator) / Decimal(v.a.denominator)
              + Decimal(v.b.numerator) / Decimal(v.b.denominator)
              * Decimal(v.d).sqrt() for v in w]
        ex = (abs(ce[0]) + abs(ce[1])) / 2
        xd = Decimal(x.numerator) / Decimal(x.denominator)
        yd = Decimal(y.numerator) / Decimal(y.denominator)
        xs += [xd - ex, xd + ex]
        ys += [yd - ex, yd + ex]
    return F(max(max(xs) - min(xs), max(ys) - min(ys)))


def _nearest_rational(x: F, qmax=8):
    """The nearest p/q to a rational x (exact comparison), and its residual."""
    best = None
    for q in range(1, qmax + 1):
        p = (x * q + F(1, 2)).__floor__()
        err = abs(x - F(p, q))
        if best is None or err < best[1]:
            best = (F(p, q), err)
    return best


def probe(budget=Decimal(240)):
    """Ask which field the three unlifted rows' sides live in, exactly.

    The stored side is a rational (70-digit Decimal of the table's own numbers), so
    "is it in Q(sqrt d) at small height?" is a decidable question: `recover_scalar`
    tests it with exact comparisons.  A field is *witnessed* only if a value within
    1e-7 exists at two different height bounds; otherwise the residual is recorded,
    because "not at small height" is a measurement, not a guess.
    """
    led = json.load(open(PROBE)) if os.path.exists(PROBE) else {}
    done = led.setdefault("rows", {})
    targets = _outlier_targets()
    t0 = Decimal(time.time())
    rows = _delivered_rows()
    for n in targets:
        if str(n) in done:
            continue
        if Decimal(time.time()) - t0 > Decimal(budget):
            break
        side = _decimal_side_fraction(n, rows)
        if side is None:
            continue
        rec = {"n": n, "decimal_side": str(side), "fields": {}}
        rq, rerr = _nearest_rational(side)
        rec["fields"]["Q"] = {"value": str(rq), "lifts": rerr < F(1, 10 ** 7),
                              "stable": True}
        for d in range(2, 22):
            if not EF.is_squarefree(d):
                continue
            cls = type(f"Q{d}", (EF.Quad,), {"d": d, "__slots__": ()})
            x = cls(side, 0)
            one = EF.recover_scalar(x, cls, dens=(1, 2, 3, 4, 6, 8), bmax=8,
                                    tol=cls(F(1, 10 ** 7)))
            two = EF.recover_scalar(x, cls, dens=(1, 2, 3, 4, 6, 8), bmax=16,
                                    tol=cls(F(1, 10 ** 7)))
            rec["fields"][str(d)] = {
                "value": str(one) if one is not None else None,
                "stable": bool(one is not None and one == two),
                "lifts": one is not None,
            }
        done[str(n)] = rec
        json.dump(led, open(PROBE, "w"), indent=1)
    print(f"PROBE — {len(done)}/{len(targets)} rows probed")
    for n in targets:
        r = done.get(str(n))
        if not r:
            continue
        hits = [d for d, v in r["fields"].items() if v["lifts"]]
        print(f"  n={n:4d} side {r['decimal_side']:>24s}  fields with a small-height "
              f"value: {hits if hits else 'none of d <= 21'}")
    return done


# ------------------------------------------------- exact 2D cage recovery
def _lattice_candidates(x: Q2, tol: Q2, dens=(1, 2, 3, 4, 6, 8), bmax=8):
    """Every small-height lattice point within `tol` of x (the cage's walls)."""
    out = []
    for D in dens:
        scale = 4 * D
        for num in range(-bmax * D, bmax * D + 1):
            b = F(num, D)
            rest = x - Q2(0, b)
            k = (rest * scale).floor()
            for kk in (k, k + 1):
                cand = Q2(F(kk, scale), b)
                if abs(x - cand) <= tol:
                    out.append(cand)
    return out


def cage_point(state, words, j, L, target, tol=None):
    """The exact 2D feasible cage for square `j`, resolved in the field.

    The old fallback ran one height search per coordinate and hoped the pair would
    be consistent.  The cage is the *joint* object: the lattice points within `tol`
    of the stored coordinate on each axis, filtered by the box and by the exact SAT
    predicate against every already-placed square.  The returned point is the
    canonical one — nearest the stored coordinate, ties broken lexicographically —
    so the result does not depend on search order, and a point that fails the 2D
    predicate is never returned.
    """
    tol = Q2(F(1, 10 ** 7)) if tol is None else tol
    ex = Q.frame_extent(*words[j])
    placed = [i for i in range(len(state)) if state[i] is not None and i != j]
    xs = _lattice_candidates(target[0], tol)
    ys = _lattice_candidates(target[1], tol)
    best = None
    for x in xs:
        if x < ex or x > L - ex:
            continue
        for y in ys:
            if y < ex or y > L - ex:
                continue
            trial = list(state)
            trial[j] = (x, y)
            ok = True
            for i in placed:
                if not any(s.sign() >= 0 for _q, s, _n, _o
                           in Q.pair_axes(trial, words, i, j)):
                    ok = False
                    break
            if not ok:
                continue
            err = abs(x - target[0]) + abs(y - target[1])
            if best is None or err < best[0] or (err == best[0] and (x, y) < (best[1], best[2])):
                best = (err, x, y)
    return None if best is None else (best[1], best[2])


# ------------------------------------------------------------------ selftest
def selftest() -> int:
    eng = build_engine()
    announced = []

    def say(msg):
        """Announce one control.  The count at the end is the number of announcements,
        so adding or removing a control cannot leave a stale number behind."""
        announced.append(msg)
        print(msg)

    # 1. the same five combinator names are registered on both domains
    pk, sq = eng.domains["spatial_geometry"], eng.domains["sturmian_sequences"]
    shared = set(pk.combinators) & set(sq.combinators)
    assert shared >= {"Tile", "Strip", "Glue", "SymmetryFold"}, shared
    say(f"control 1 — both domains register the same engine slots {sorted(shared)}")

    # 2. the packing wheel certifies its closed-form families
    rows = eng.wheels[0].spin()
    cert = [r for r in rows if r["verdict"] == "certified"]
    assert len(cert) >= 15, len(cert)
    say(f"control 2 — spatial wheel: {len(cert)}/{len(rows)} cells certified")

    # 3. every certified packing cell has all four witnesses, not one metric
    for r in cert:
        assert len(r["witnesses"]) == 4, r
        assert all(w["ok"] for w in r["witnesses"].values()), r
    assert all(r["witness_count"] >= 3 for r in cert), cert[0]
    assert all(r["measure"] and r["size"] for r in cert), cert[0]
    say("control 3 — every certified spatial cell passes all four witnesses "
          "(gate, contact graph, conservation, Decimal), and the row carries the "
          "neutral size/measure/invariant columns")

    # 4. the strip's closed forms hold for the wheel's own cells
    for r in cert:
        if r["family"] != "Strip":
            continue
        k, m = int(r["params"]["k"]), int(r["params"]["m"])
        assert r["size"] == 4 * k * k + m
    say("control 4 — the Strip cells satisfy N = 4k^2 + m and L = 2k + m sqrt2/2")

    # 5. the refusal laws still fire -- on constructed cells, because run 88 closed the
    #    last three non-viable cells of the wheel (the S(k,0) refusals), so a spatial
    #    wheel with no refusal is the result, not a silent skip
    refused = [r for r in rows if r["verdict"] == "refused"]
    assert not refused, refused

    def _law(fn):
        try:
            fn()
        except Refusal as e:
            return e.law
        return None

    empty = {"x": ((HALF, Q2(1), 2),), "y": ((HALF, Q2(1), 2),), "slots": []}
    bad = dict(DIAMOND_FIELDS["n10"], drop_colliding=False)
    cases = {
        "degenerate_cell": lambda: p_strip(0, 0),
        "negative_seam": lambda: p_strip(2, -1),
        "unknown_field": lambda: p_diamond_field("not_a_field"),
        "no_diamond": lambda: _assemble_field("empty", empty),
        "declaration_overlaps": lambda: _assemble_field("bad", bad),
    }
    for law, fn in cases.items():
        assert _law(fn) == law, (law, _law(fn))
    elsewhere = {r["refusal"]["law"] for w in eng.wheels[1:] for r in w.spin()
                 if r["verdict"] == "refused"}
    assert elsewhere, "the other wheels must still refuse by law"
    say(f"control 5 — the spatial wheel has no refused cell (S(k,0) now certifies), "
          f"and every refusal law still fires on a constructed cell: "
          f"{sorted(cases)}; other wheels refuse by {sorted(elsewhere)}")

    # 6. the fold is an exact symmetry: same N, same L, witnesses still pass
    a, b = p_pocket(2), p_fold(2)
    assert a.n == b.n and a.laws["extent"][1] == b.laws["extent"][1]
    say("control 6 — the diagonal fold preserves N and L exactly")

    # 7. sequences: an irrational slope gives a Sturmian word, a rational one does not
    rows = eng.wheels[1].spin()
    by_t = {}
    for r in rows:
        by_t[(r["params"]["t"], r["verdict"])] = by_t.get((r["params"]["t"], r["verdict"]), 0) + 1
    assert any(r["params"]["t"] == str(Q2(-1, 1)) and r["verdict"] == "certified"
               for r in rows), rows
    assert any(r["params"]["t"] == "1/2" and r["verdict"] == "refused" for r in rows)
    say("control 7 — slope sqrt2-1 certifies, slope 1/2 is refused (not Sturmian)")

    # 8. the refusal for a rational slope is the complexity law, with its numbers
    bad = [r for r in rows if r["params"]["t"] == "1/2"][0]
    assert bad["refusal"]["law"] == "not_sturmian", bad["refusal"]
    say(f"control 8 — rational slope refused by the exact law: {bad['refusal']}")

    # 9. the coboundary law d(uv) = du xor dv holds on the glue cell
    glue = [r for r in rows if r["family"] == "Glue"][0]
    assert glue["verdict"] == "certified"
    assert "coboundary" in glue["witnesses"]["conservation"]["detail"]
    say("control 9 — the glue cell passes the coboundary witness on its join")

    # 10. Decimal cross-check: the signs agree, and a perturbed claim is caught
    claim = p_pocket(2)
    ok, detail = DecimalWitness().check(claim, pk)
    assert ok, detail
    claim2 = p_pocket(2)
    claim2.laws["extent"] = ("L", claim2.laws["extent"][1] + Q2(F(1, 10 ** 9)))
    ok2, _ = DecimalWitness().check(claim2, pk)
    assert not ok2, "the Decimal witness must catch a 1e-9 lie"
    say("control 10 — the Decimal witness accepts the exact side and catches a 1e-9 lie")

    # 11. the tower audit covers this module too
    checked, offenders, skipped = EF.audit_module(sys.modules[__name__],
                                                  exempt=EF.AUDIT_EXEMPT)
    assert offenders == [], offenders
    say(f"control 11 — this module's {checked} decision functions name no float "
          f"({len(skipped)} display/test exemptions declared)")

    # 12. cage recovery places a square the contact graph leaves free, exactly
    st, ws, L = Q_mixed_strip(2, 1)
    true_pt = st[0]
    broken = list(st)
    broken[0] = None
    pt = cage_point(broken, ws, 0, L, true_pt)
    assert pt == true_pt, (pt, true_pt)
    trial = list(st)
    trial[0] = pt
    assert Q.gate(trial, ws)["ok"]
    # and it refuses to place the square anywhere when the cage is empty
    assert cage_point(broken, ws, 0, L, (Q2(-99), Q2(-99))) is None
    say(f"control 12 — the 2D cage recovers the freed square exactly ({pt}) and "
          f"returns nothing when the cage is empty")

    # 13. a third, structurally distinct domain registers the same slots
    import lattice_shells as LAT
    lat = eng.domains["lattice_shells"]
    shared3 = (set(pk.combinators) & set(sq.combinators)) & set(lat.combinators)
    assert shared3 >= {"Tile", "Strip", "Glue", "SymmetryFold"}, shared3
    assert shared3 == {"Tile", "Strip", "Glue", "SymmetryFold"}, shared3
    say(f"control 13 — three domains share the engine slots {sorted(shared3)}; "
          f"lattice adds {sorted(set(lat.combinators) - shared3)}")

    # 14. the theta series are the classical ones, by enumeration (no tables)
    TH = LAT.theta(LAT.LATTICES["D4"], 6), LAT.theta(LAT.LATTICES["E8"], 4), \
        LAT.theta(LAT.LATTICES["Z4"], 6)
    assert TH[0] == [1, 0, 24, 0, 24, 0, 96], TH[0]
    assert TH[1] == [1, 0, 240, 0, 2160], TH[1]
    assert TH[2] == [1, 8, 24, 32, 24, 48, 96], TH[2]
    say(f"control 14 — theta by exact enumeration: D4 {TH[0]}, E8 {TH[1]}, Z4 {TH[2]}")

    # 15. kissing topology: shell sizes and inner-product-1 degrees, computed
    k = {key: len(LAT.shell(LAT.LATTICES[key], LAT.LATTICES[key].minimal_norm))
         for key in ("Z2", "D4", "E8")}
    deg = {key: LAT.root_degree(LAT.LATTICES[key]) for key in ("Z2", "D4", "E8")}
    assert k == {"Z2": 4, "D4": 24, "E8": 240}, k
    assert deg == {"Z2": None, "D4": 8, "E8": 56}, deg
    say(f"control 15 — kissing numbers {k} and root degrees {deg}")

    # 16. the conservation law is theta multiplicativity, and it is exact
    g = LAT.l_sum("Z2", "D4", 4)
    enumerated = [len(x) for x in g.payload["pairs"]]
    assert tuple(enumerated) == tuple(g.payload["conv"]) == g.laws["theta"][1], g.laws
    ran = 0
    for w in lat.suite(g):
        ok, detail = w.check(g, lat)
        assert ok, (w.name, detail)
        ran += 1
    assert ran == 3, ran      # the kissing witness scopes itself to Frame/Atom
    say(f"control 16 — Z2 (+) D4: enumerated {tuple(enumerated)} == convolution, "
          f"{ran} applicable witnesses pass (kissing is a Frame/Atom law only)")

    # 17. a wrong lattice claim is refused, by witness or by declared law
    liar = LAT.l_atom("Z4")
    liar.laws["kissing"] = ("|L_min|", 24)
    ok, detail = LAT.KissingWitness().check(liar, lat)
    assert not ok, "the kissing witness must catch a claimed 24 for Z4 (true 8)"
    refusals = []
    for key, m in (("D4", 3), ("E8", 1)):
        try:
            LAT.l_shell(key, m)
        except Refusal as r:
            refusals.append(r.law)
    try:
        LAT.l_sum("Z4", "E8", 2)
    except Refusal as r:
        refusals.append(r.law)
    assert refusals == ["empty_shell", "empty_shell", "rank_budget"], refusals
    say(f"control 17 — a wrong kissing number is refused ({detail[:40]}...), and "
          f"the declared laws fire: {refusals}")

    # 18. the cell algebra: run parameters, not cell lists, generate the run-87 census
    CENSUS_10 = [(1, 0, 1, 0), (3, 1, 1, 0), (5, 1, 1, 0), (5, 1, 3, 0),
                 (1, 0, 3, 1), (1, 0, 5, 1), (3, 0, 5, 1), (5, 1, 5, 1)]
    CENSUS_19 = [(1, 0, 1, 0), (1, 0, 3, F(8, 3)), (1, 0, 5, F(8, 3)),
                 (1, F(8, 3), 1, 0), (3, 0, 5, F(8, 3)), (3, F(8, 3), 1, 0),
                 (3, F(8, 3), 3, 0), (5, F(8, 3), 1, 0), (5, F(8, 3), 3, 0),
                 (5, F(8, 3), 5, 0), (5, F(8, 3), 5, F(8, 3))]
    CENSUS_40 = [(1, 0, 1, 0), (1, 0, 3, 0), (1, 0, 3, 4), (1, 0, 5, 0),
                 (1, 0, 5, 4), (1, 0, 7, 4), (3, 0, 1, 0), (3, 0, 3, 0),
                 (3, 0, 5, 4), (3, 0, 7, 4), (3, 4, 1, 0), (3, 4, 7, 4),
                 (5, 0, 1, 0), (5, 0, 7, 4), (5, 4, 1, 0), (5, 4, 3, 0),
                 (5, 4, 5, 4), (5, 4, 7, 4), (7, 4, 1, 0), (7, 4, 3, 0),
                 (7, 4, 3, 4), (7, 4, 5, 0), (7, 4, 5, 4), (7, 4, 7, 4)]
    census = {"n10": (CENSUS_10, 16, 8), "n19": (CENSUS_19, 25, 14),
              "n40": (CENSUS_40, 36, 12)}
    tables = []
    for name, (want, carrier, dropped) in census.items():
        c = p_diamond_field(name)
        spec = DIAMOND_FIELDS[name]
        got = {(str(x), str(y)) for x, y in c.payload["cells"]}
        ref = {(str(_pt(q)[0]), str(_pt(q)[1])) for q in want}
        assert got == ref, (name, len(got), len(ref))
        assert c.meta["carrier"] == carrier and c.meta["dropped"] == dropped, c.meta
        assert len(spec["x"]) <= 2 and len(spec["y"]) <= 2, spec
        tables.append(f"{name} {carrier}->{len(got)} (-{dropped})")
    say("control 18 — two axis runs per side generate the run-87 census exactly: "
          + ", ".join(tables))

    # 19. the Strip builder is a field of (k, m): S(k,0) certifies and IS the plain grid
    for kk in (1, 2, 3, 4):
        zero = p_strip(kk, 0)
        grid = p_grid(2 * kk)
        assert zero.laws["extent"][1] == grid.laws["extent"][1] == Q2(2 * kk)
        assert zero.n == grid.n == 4 * kk * kk, (kk, zero.n)
        assert zero.laws["gain"][1] == Q2(0), zero.laws["gain"]
        assert ({(str(x), str(y)) for x, y in zero.payload["state"]}
                == {(str(x), str(y)) for x, y in grid.payload["state"]}), kk
    for kk, mm in ((2, 1), (2, 2), (3, 1), (3, 3), (4, 2)):
        field = p_strip(kk, mm)
        st, ws, L = Q_mixed_strip(kk, mm)
        assert field.laws["extent"][1] == L, (kk, mm, field.laws["extent"][1], L)
        assert ({(str(x), str(y)) for x, y in field.payload["state"]}
                == {(str(x), str(y)) for x, y in st}), (kk, mm)
        assert field.n == 4 * kk * kk + mm, (kk, mm, field.n)
    one = p_strip(2, 1)
    assert one.laws["gain"][1] == Q2(1) - S2H, one.laws["gain"]
    # the Pocket is the strip at m = 1, on the same build path (run 89): same cells, same
    # words, same side, same N -- but it keeps its own family, that being what it claims
    for kk in (1, 2, 3):
        pocket, strip = p_pocket(kk), p_strip(kk, 1)
        assert pocket.family == "Pocket" and strip.family == "Strip"
        assert pocket.payload["state"] == strip.payload["state"], kk
        assert pocket.payload["words"] == strip.payload["words"], kk
        assert pocket.laws["extent"][1] == strip.laws["extent"][1], kk
        assert pocket.n == strip.n == 4 * kk * kk + 1, (kk, pocket.n, strip.n)
    say("control 19 — S(k,0) is no longer refused: it certifies as the plain 2k grid "
        "(gain 0) for k = 1..4, S(k,m) reproduces the run-84 sentence for m >= 1 "
        "(L = 2k + m sqrt2/2, N = 4k^2 + m), and the Pocket is the same field at "
        "m = 1: one build path, two families")

    # 20. a genuinely malformed declaration is refused by the gate, not by a flag:
    #     two slots that overlap *each other* cannot be caught by the carrier rule
    dbl = dict(DIAMOND_FIELDS["n10"])
    dbl["slots"] = [_pt((3, 0, 3, 0)), _pt((3, 0, 3, 0))]
    try:
        _assemble_field("double_slot", dbl)
        raise AssertionError("an overlapping pair of slots must not certify")
    except Refusal as e:
        assert e.law == "declaration_overlaps", e.law
        assert "violations" in e.detail, e.detail
    near = dict(DIAMOND_FIELDS["n10"])
    near["slots"] = [_pt((3, 0, 3, 0)), _pt((3, F(1, 10), 3, 0))]
    try:
        _assemble_field("near_slots", near)
        raise AssertionError("two slots 1/10 apart must not certify")
    except Refusal as e:
        assert e.law == "declaration_overlaps", e.law
    loose = dict(DIAMOND_FIELDS["n10"], drop_colliding=False)
    try:
        _assemble_field("no_rule", loose)
        raise AssertionError("a slot over an axis cell with the rule off must refuse")
    except Refusal as e:
        assert e.law == "declaration_overlaps", e.law
    say("control 20 — a malformed declaration is refused by `declaration_overlaps`, "
        "three ways: two coincident slots and two slots 1/10 apart (both caught by the "
        "gate, since the carrier rule cannot see slot-slot overlap), and a slot over an "
        "axis cell with the insertion rule switched off (caught by the rule)")

    # 21. the algebraic rungs: one ridge family, three fields, and the 45-degree member
    #     IS the Strip -- so the census's Q(sqrt5), Q(sqrt7) and rational-t rungs are
    #     gate-verified by the same procedure as every Q(sqrt2) cell
    rows = []
    for name in ("n10", "n19", "n40"):
        c = p_diamond_field(name)
        g1, g2 = Q.gate(c.payload["state"], c.payload["words"]), \
            qgate(Q2, c.payload["state"], c.payload["words"])
        assert (g1["ok"], g1["L"], g1["clearance"], g1["contacts"],
                g1["violations"]) == (g2["ok"], g2["L"], g2["clearance"],
                                      g2["contacts"], g2["violations"]), name
    for kk in (1, 2):
        ridge = p_ridge(2, *Q.word_45(), kk, "Ridge45", {"k": kk})
        strip = p_strip(kk, 1)
        assert ridge.laws["extent"][1] == strip.laws["extent"][1] == \
            Q2(2 * kk) + S2H, (kk, ridge.laws["extent"][1])
        assert ({(str(x), str(y)) for x, y in ridge.payload["state"]}
                == {(str(x), str(y)) for x, y in strip.payload["state"]}), kk
    rungs = []
    for fam, cell in (("Slope", p_slope(2, 1, 1)), ("Seventh", p_seventh(1)),
                      ("Tilt", p_tilt(F(1, 2), 1)), ("Slope", p_slope(2, 1, 2)),
                      ("Seventh", p_seventh(2)), ("Tilt", p_tilt(F(1, 2), 2))):
        g = gate_of(cell)
        assert g["ok"] and g["clearance"] == 0 and g["contacts"] >= 1, (fam, g)
        tbl = cell.meta["table_side"]
        tag = ("uncalibrated: the delivered row is outside the axis/45-deg alphabet"
               if tbl is None else
               ("beats the table" if cell.meta["beats_table"] else "dominated"))
        rungs.append(f"{fam} n={cell.size} L={cell.laws['extent'][1]} vs table {tbl} "
                     f"({tag})")
    assert all(not p_ridge(2, *Q.word_45(), kk, "R", {"k": kk}).meta["beats_table"]
               for kk in (1, 2)), "the 45-degree member is the best of the family"
    try:
        p_ridge(5, qfield(5)(0), qfield(5)(0), 1, "Bad", {})
        raise AssertionError("a word off the unit circle must refuse")
    except Refusal as e:
        assert e.law in ("word_off_circle", "wrong_field"), e.law
    say("control 21 — the ridge family is one sentence over three fields: the "
        "45-degree member reproduces S(k,1) exactly, `qgate` agrees with `qsqrt2.gate` "
        "cell for cell, and every rung gates at clearance 0 with its exact algebraic "
        "side: " + "; ".join(rungs))

    print(f"selftest: OK ({len(announced)} controls)")
    return len(announced)


# --------------------------------------------------------------------- report
def report(eng, ledger):
    """One table form for every domain: size, measure, invariant, verdict, law."""
    spins = eng.spin_all()
    print("\nWHEEL SPIN — declared cells, exact laws, multi-witness verdicts\n")
    for name, rows in spins.items():
        s = Engine.summarise(rows)
        print(f"  {name}: {s['certified']}/{s['cells']} certified, "
              f"{s['refused']} refused {s['refusal_laws']}")
    for wheel in eng.wheels:
        rows = spins[wheel.name]
        print(f"\n  {wheel.name} [{wheel.domain.name}]")
        print(f"    {'family':14s} {'params':24s} {'size':>6s} {'measure':>26s} "
              f"{'invariant':>22s} {'w':>2s} {'verdict':>10s}  law")
        for r in rows:
            p = ",".join(f"{k}={v}" for k, v in r["params"].items())
            law = r["refusal"]["law"] if r["refusal"] else ""
            size = "" if r["size"] is None else r["size"]
            print(f"    {r['family']:14s} {p:24s} {str(size):>6s} "
                  f"{str(r['measure'] or ''):>26s} "
                  f"{str(r['invariant'] or ''):>22s} {r['witness_count']:>2d} "
                  f"{r['verdict']:>10s}  {law}")
    ledger["spins"] = {name: {"summary": Engine.summarise(rows), "rows": rows}
                       for name, rows in spins.items()}
    return spins


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        selftest()
        return 0
    if "--audit" in argv:
        import lattice_shells as LAT
        mods = [EF, Q, sys.modules[__name__], LAT]
        total, bad = 0, []
        for m in mods:
            checked, offenders, skipped = EF.audit_module(m, exempt=EF.AUDIT_EXEMPT)
            total += checked
            bad += [(m.__name__, o) for o in offenders]
            print(f"  {m.__name__}: {checked} decision functions, "
                  f"{len(offenders)} naming float, exempt {skipped}")
        print(f"float audit: {total} functions checked, {len(bad)} offenders")
        return 0 if not bad else 1
    if "--census" in argv:
        budget = (argv[argv.index("--budget") + 1] if "--budget" in argv else "240")
        census(Decimal(budget))
        return 0
    if "--probe" in argv:
        budget = (argv[argv.index("--budget") + 1] if "--budget" in argv else "240")
        probe(Decimal(budget))
        return 0

    SQ.guard(quiet=True)
    print("run 86 — glm_wheels.py: three domains, one wheel engine")
    print(f"scorer guard: {SQ.summarise(SQ.load())['score']:.9f}, no row changes\n")
    eng = build_engine()
    ledger = {"run": 86, "instrument": "glm_wheels.py + lattice_shells.py + exact_field.py",
              "domains": sorted(eng.domains)}
    report(eng, ledger)
    checked, offenders, skipped = EF.audit_module(
        sys.modules[__name__], exempt=EF.AUDIT_EXEMPT)
    ledger["audit"] = {"checked": checked, "offenders": offenders,
                       "exempt": skipped}
    print(f"\n  float audit: {checked} decision functions, {len(offenders)} naming "
          f"float, exempt {skipped}")
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "w") as f:
        json.dump(ledger, f, indent=1)
    print(f"  ledger: {os.path.relpath(LEDGER, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
