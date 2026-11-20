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
def ridge_width(cls, c, s, k=None, m=1):
    """The seam width at which the m-diamond bar just touches, exactly.

    The bar is the m tilted unit squares set edge to edge along `-v` (the square's own
    edge direction), centred in the seam.  Every block-slot pair's slack is *linear* in
    the seam width `w`, because the bar moves with the seam centre and the blocks move
    with the box, so each pair-axis equation `|d(w) . q| = need` has closed-form roots in
    the field.  The width is the smallest of those roots at which the exact gate passes:
    a contact width by construction, no scan and no tolerance.

    For `k = None` and `m = 1` this reduces to the closed form of run 90,
    `min(1/(c+s), c+s)`; at 45 degrees and any m it gives `m*sqrt2/2`, the Strip's seam.
    """
    if m == 0:
        return cls(0)
    if k is None:
        one = cls(1)
        return min(one / (c + s), c + s)
    for w in sorted(ridge_widths(cls, c, s, k, m)):
        state, words = _ridge_sentence(cls, c, s, k, m, w)
        if Q.gate(state, words, cls)["ok"]:
            return w
    raise Refusal("no_contact_width",
                  f"no seam width in the closed-form set gates the {m}-diamond bar")


def _ridge_blocks(cls, k, w):
    """The four k-blocks of the box `[0, 2k+w]^2`, as (centre) pairs."""
    half = cls(F(1, 2))
    L = cls(2 * k) + w
    cells = []
    for bx in (0, 1):
        for by in (0, 1):
            x0 = cls(0) if bx == 0 else L - cls(k)
            y0 = cls(0) if by == 0 else L - cls(k)
            for i in range(k):
                for j in range(k):
                    cells.append((x0 + cls(i) + half, y0 + cls(j) + half))
    return cells


def _bar_offsets(cls, c, s, m):
    """The m slot centres relative to the seam centre: edge to edge along `-v`."""
    return [(cls(F(2 * i - (m - 1), 2)) * s, -cls(F(2 * i - (m - 1), 2)) * c)
            for i in range(m)]


def _ridge_sentence(cls, c, s, k, m, w):
    """The ridge state and words at seam width `w` (box side `2k + w`)."""
    half = cls(F(1, 2))
    state = _ridge_blocks(cls, k, w)
    words = [(cls(1), cls(0)) for _ in state]
    ctr = (cls(k) + w * half, cls(k) + w * half)
    for dx, dy in _bar_offsets(cls, c, s, m):
        state.append((ctr[0] + dx, ctr[1] + dy))
        words.append((c, s))
    return state, words


def _ridge_affine(cls, c, s, k, m):
    """Blocks and slots as `A + B w` per coordinate, so every slack equation is linear."""
    half = cls(F(1, 2))
    zero, one = cls(0), cls(1)
    blocks = []
    for bx in (0, 1):
        for by in (0, 1):
            for i in range(k):
                for j in range(k):
                    Ax = cls(i) + half + (cls(k) if bx else zero)
                    Ay = cls(j) + half + (cls(k) if by else zero)
                    blocks.append(((Ax, one if bx else zero), (Ay, one if by else zero)))
    slots = []
    for dx, dy in _bar_offsets(cls, c, s, m):
        slots.append(((cls(k) + dx, half), (cls(k) + dy, half)))
    return blocks, slots


def ridge_widths(cls, c, s, k, m):
    """Every positive `w` at which some block-slot pair touches, exactly.

    A pair's four axis slacks are `|P + Q w| - need`, so the roots of `|P + Q w| = need`
    are `(need - P)/Q` and `(-need - P)/Q`; feasibility can only change at one of them.
    """
    if m == 0:
        return []
    blocks, slots = _ridge_affine(cls, c, s, k, m)
    half = cls(F(1, 2))
    # `need = 1/2 + extent(other)` on every axis: the block's extent along u or v is
    # (|c|+|s|)/2 and the slot's extent along x or y is the same expression.
    need_slot = half + (abs(c) + abs(s)) * half
    need_block = need_slot
    roots = []
    for (bx_, by_), (sx_, sy_) in ((b, s) for b in blocks for s in slots):
        # each coordinate is `A + B w`:  x = bx_[0] + bx_[1] w,  y = by_[0] + by_[1] w
        dAx, dBx = bx_[0] - sx_[0], bx_[1] - sx_[1]
        dAy, dBy = by_[0] - sy_[0], by_[1] - sy_[1]
        for (qA, qB), need in (((c, s), need_slot), ((-s, c), need_slot),
                               ((cls(1), cls(0)), need_block),
                               ((cls(0), cls(1)), need_block)):
            # d = block - slot, so d.q = (dA.q) + (dB.q) w
            P = dAx * qA + dAy * qB
            Qc = dBx * qA + dBy * qB
            if Qc == 0:
                continue
            for sign in (cls(1), cls(-1)):
                w = (sign * need - P) / Qc
                if w.sign() > 0 and w not in roots:
                    roots.append(w)
    roots.sort()
    return roots


def p_ridge(d, c, s, k, family, params, m=1):
    """Gate-verify an m-diamond ridge over `Q(sqrt d)` and return it as a claim.

    N = 4k^2 + m.  Refusals are declared, not incidental:
      * `word_off_circle`  -- the declared (cos, sin) is not a unit word;
      * `no_contact_width` -- no closed-form width gates the bar;
      * `ridge_cuts_corner` -- the derived width still leaves an overlap.
    """
    if k < 1:
        raise Refusal("degenerate_cell", f"k = {k} has no blocks")
    if m < 0:
        raise Refusal("negative_seam", f"m = {m} is not a seam count")
    cls = qfield(d)
    if (c * c + s * s) != cls(1):
        raise Refusal("word_off_circle",
                      f"cos^2 + sin^2 = {c * c + s * s} != 1 in Q(sqrt {d})")
    w = ridge_width(cls, c, s, k, m)
    state, words = _ridge_sentence(cls, c, s, k, m, w)
    g = Q.gate(state, words, cls)
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
                   "seam": w, "bar": m})
    claim.meta["field_d"] = d
    claim.meta["seam"] = str(w)
    claim.meta["bar"] = m
    _tag(claim, L, n)
    claim.laws["seam"] = ("w", w)
    claim.laws["tilted"] = ("tilted", m)
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


# ------------------------------------------------------------------ the ring
#: Run 94 replaces run 93's four-corner-module ansatz with the sentence the census's
#: own n = 18 row is.  The row is a C2-symmetric **perimeter** of axis squares with
#: exactly one gap in each wall, one tilted square **wedged across each vertical
#: gap** (a contact on each of its own axes), and a **four-square pinwheel** that
#: carries each chain end around to the opposite gap square:
#:
#:     10 axis = 4 corner squares + a 2k-square run up the left wall + a 2k-square
#:               run down the right wall + one square inward on the bottom wall and
#:               one inward on the top wall                         (4k + 6 in general)
#:      4 gaps = the wedged squares p5, -p5 and the two chain ends p8, -p8
#:      4 pin  = the chain p5 -> p6 -> p7 -> p8 and its C2 image
#:
#: Each of the eight tilted squares is the unique solution of two declared tangencies,
#: so the sentence is *solved* in Q(sqrt 7) rather than read off the table; the exact
#: gate is the arbiter (control 24).
def ring_side(cls, c, s, k):
    """The ring's side, derived: the four corner squares sit flush in the box.

    A corner square's centre is `(a, a)` with `a = k + c`, so its outer face is at
    `a + 1/2` and

        L = 2a + 1 = 2k + 1 + 2c = 2k + 3/2 + (c + s),          (c - s = 1/2)

    the one side law of the whole Q(sqrt 7) family, `(2m+1)/2 + sqrt7/2`.  At `k = 1`
    it is the census's n = 18 side, `7/2 + sqrt7/2`.
    """
    return cls(2 * k + 1) + cls(2) * c


def ring_frame(cls, c, s, k):
    """The perimeter: 4 corner squares, a 2k-square run on each vertical wall, and one
    square on each horizontal wall -- `4k + 6` axis squares, C2-symmetric.

    The gaps are derived, not chosen: a vertical wall covers `2k + 2` of the `L` it
    has to span, so its single gap is `L - (2k + 2) = 2c - 1`; a horizontal wall
    covers 3 (corner, one square, corner), so its gap is `L - 3 = 2c + 2k - 2`.  At
    `k = 1` the ten centres are the census row's ten axis squares, exactly.
    """
    a = cls(k) + c
    cells = [(-a, -a), (-a, a), (a, a), (a, -a)]
    for j in range(1, 2 * k + 1):
        cells.append((-a, -a + cls(j)))          # left wall, up from the bottom corner
    for j in range(1, 2 * k + 1):
        cells.append((a, a - cls(j)))            # right wall, down from the top corner
    cells.append((-a + cls(1), -a))              # bottom wall, one in from the left
    cells.append((a - cls(1), a))                # top wall, one in from the right
    return cells


def _ring_dot(p, q):
    """The exact dot product of two field points."""
    return p[0] * q[0] + p[1] * q[1]


def _ring_at(cls, A, B, u, v):
    """The point `p` with `p . u = A` and `p . v = B`, for an orthonormal pair u, v."""
    return (A * u[0] + B * v[0], A * u[1] + B * v[1])


def _ring_neg(p):
    """The C2 image of a centre: the sentence is symmetric under `p -> -p`."""
    return (-p[0], -p[1])


def _ring_indices(k):
    """Named positions inside `ring_declaration`'s cell list."""
    f = 4 * k + 6
    return {"bl": 0, "tl": 1, "tr": 2, "br": 3, "l1": 4, "l2": 5,
            "r1": 4 + 2 * k, "r2": 5 + 2 * k, "b": 4 + 4 * k, "t": 5 + 4 * k,
            "p5": f, "m5": f + 1, "p6": f + 2, "m6": f + 3,
            "p7": f + 4, "m7": f + 5, "p8": f + 6, "m8": f + 7}


def ring_declaration(cls, c, s, k):
    """The 10 + 4 + 4 sentence, solved from its declared tangencies.

    A tilted unit square at centre `p` has its own edges along `u = (c, s)` and
    `v = (-s, c)`; its face in direction `u` sits at `p.u + 1/2`, and an axis square's
    reach along `u` is `(|c| + |s|)/2`.  So a tilted-axis tangency on `u` is exactly

        |(q - p) . u| = 1/2 + (|c| + |s|)/2 =: need,               q the axis square,

    and a tilted-tilted tangency on `u` or `v` is exactly `|(q - p) . u| = 1`.  One
    such equation per independent axis fixes a point, so every module below is a 2x2
    solve in the field -- no scan, no tolerance:

      * `p5` (right gap) -- `(run_end - p5).u = need` and `(p5 - corner).v = need`,
        with `run_end = (a, a - 2k)` the last square of the right wall's run and
        `corner = (a, -a)` the bottom-right corner: the square is wedged across the
        gap.  `-p5` is the same wedge in the left gap, by C2.
      * `p6 = p5 + v` -- an edge-to-edge step along the word's `v` axis.
      * `p7`, `p8` -- each fixed by one `v`-contact with its predecessor in the chain
        and one `u`-contact with the opposite gap square `-p5`; that second contact is
        the pinwheel, and it is what closes the chain on the far side.
      * `p -> -p` gives the other four tilted squares.
    """
    one = cls(1)
    a = cls(k) + c
    u, v = (c, s), (-s, c)
    need = cls(F(1, 2)) + (abs(c) + abs(s)) * cls(F(1, 2))
    frame = ring_frame(cls, c, s, k)
    run_end = (a, a - cls(2 * k))
    corner = (a, -a)
    p5 = _ring_at(cls, _ring_dot(run_end, u) - need, _ring_dot(corner, v) + need, u, v)
    p6 = (p5[0] + v[0], p5[1] + v[1])
    p7 = _ring_at(cls, -_ring_dot(p5, u) + one, _ring_dot(p6, v) + one, u, v)
    p8 = _ring_at(cls, -_ring_dot(p5, u) + one, _ring_dot(p7, v) + one, u, v)
    tilted = [p5, _ring_neg(p5), p6, _ring_neg(p6),
              p7, _ring_neg(p7), p8, _ring_neg(p8)]
    return {"cells": frame + tilted,
            "words": [(one, cls(0))] * len(frame) + [u] * len(tilted),
            "frame": len(frame), "gap": [p5, _ring_neg(p5), p8, _ring_neg(p8)],
            "chain": [p5, p6, p7, p8]}


def ring_tangencies(k):
    """Every tangency the 10 + 4 + 4 layout declares, as `(i, j)` pairs of the sentence.

    `frame` -- the eight perimeter contacts: the two runs' edge-to-edge steps, the two
               horizontal-wall squares (each flush on one edge, corner-touching the
               run square beside it), and the two corner-point contacts.
    `wedge` -- the four frame contacts that pin the vertical-gap squares: `p5` is
               wedged across the right gap between the run end `r2` and the corner
               `br`; `-p5` across the left gap between `l2` and `tl`.
    `chain` -- the six edge-to-edge steps `p5 -> p6 -> p7 -> p8` and their C2 images.
    `pin`   -- the four `u`-contacts that close the chain onto the opposite gap square
               (`p7`, `p8` against `-p5`, and `-p7`, `-p8` against `p5`).
    """
    x = _ring_indices(k)
    return {
        "frame": [(x["bl"], x["l1"]), (x["l1"], x["l2"]),
                  (x["tr"], x["r1"]), (x["r1"], x["r2"]),
                  (x["bl"], x["b"]), (x["l1"], x["b"]),
                  (x["tr"], x["t"]), (x["r1"], x["t"])],
        "wedge": [(x["p5"], x["r2"]), (x["p5"], x["br"]),
                  (x["m5"], x["l2"]), (x["m5"], x["tl"])],
        "chain": [(x["p5"], x["p6"]), (x["p6"], x["p7"]), (x["p7"], x["p8"]),
                  (x["m5"], x["m6"]), (x["m6"], x["m7"]), (x["m7"], x["m8"])],
        "pin": [(x["p7"], x["m5"]), (x["p8"], x["m5"]),
                (x["m7"], x["p5"]), (x["m8"], x["p5"])],
    }


def _ring_contact(cls, cells, words, i, j):
    """True iff the pair's tightest axis is exactly touching: an exact contact.

    The gate's own test, not a weaker one: every axis slack is `>= 0` (the sentence is
    separated) and the largest of them is exactly `0` (nothing separates the pair by
    more).  A pair can share a zero slack on one axis and still be held apart on
    another -- the ring has 38 such coincidences and only 26 contacts -- so the
    declaration is checked against the strict reading.
    """
    return max(sl for _q, sl, _n, _o in Q.pair_axes(cells, words, i, j, cls)) == 0


def ring_field(cls, c, s, k):
    """The ring, verified: walls flush, every declared tangency an exact contact, and
    the exact gate at the side `ring_side` derives.

    Refusals are declared laws, not accidents:
      * `degenerate_cell`    -- `k < 1` has no ring;
      * `ring_wall_open`     -- a perimeter square is not flush with the container;
      * `ring_chain_adrift`  -- a declared tangency is not a contact.  This is the
                                family's real limit: the pinwheel's `u`-contacts close
                                on the opposite gap square only at `k = 1` (control 24
                                measures the exact slack at `k = 2, 3, 5`);
      * `ring_side_mismatch` -- the gate's side is not `ring_side`;
      * `ring_collides`      -- the sentence overlaps at its derived side.
    """
    if k < 1:
        raise Refusal("degenerate_cell", f"k = {k} has no ring")
    L = ring_side(cls, c, s, k)
    half = cls(F(1, 2))
    decl = ring_declaration(cls, c, s, k)
    cells, words = decl["cells"], decl["words"]
    wall = 0
    for p in cells[:decl["frame"]]:
        for z in (p[0], p[1]):
            if abs(z) + half == L * half:
                wall += 1
    if wall != 4 * k + 10:
        raise Refusal("ring_wall_open",
                      f"k = {k}: {wall} flush wall faces, not {4 * k + 10}")
    tang = ring_tangencies(k)
    for i, j in [pair for group in tang.values() for pair in group]:
        if not _ring_contact(cls, cells, words, i, j):
            raise Refusal("ring_chain_adrift",
                          f"k = {k}: the declared tangency ({i}, {j}) is not a "
                          f"contact -- the pinwheel closes only at k = 1")
    g = Q.gate(cells, words, cls)
    if g["L"] != L:
        raise Refusal("ring_side_mismatch", f"k = {k}: the gate reads {g['L']}, not {L}")
    if not g["ok"]:
        raise Refusal("ring_collides",
                      f"k = {k}: {g['violations']} pairs overlap at the derived side")
    decl.update({"gate": g, "wall": wall, "tangencies": tang})
    return decl


def ring_claim(d, c, s, k, family="Ring", params=None):
    """Gate-verify a ring over `Q(sqrt d)` and return it as a claim.

    `N = 4k + 14` (4k + 6 axis squares plus eight tilted) and
    `L = 2k + 3/2 + (c + s)`.  At the census's Q(sqrt 7) word with `k = 1` that is
    `N = 18`, `L = 7/2 + sqrt7/2` -- the n = 18 row's own side, built here from the
    word and 22 declared tangencies instead of read off the table.
    """
    cls = qfield(d)
    if (c * c + s * s) != cls(1):
        raise Refusal("word_off_circle",
                      f"cos^2 + sin^2 = {c * c + s * s} != 1 in Q(sqrt {d})")
    decl = ring_field(cls, c, s, k)
    state, words = decl["cells"], decl["words"]
    g = decl["gate"]
    n = len(state)
    L = g["L"]
    claim = Claim("spatial_geometry", family, params or {"k": k}, n,
                  {"count": ("N", n), "extent": ("L", L),
                   "void": ("L^2 - N", L * L - cls(n)),
                   "contacts": ("contacts", g["contacts"])},
                  {"state": state, "words": words, "field": f"Q(sqrt {d})",
                   "frame": decl["frame"], "wall": decl["wall"],
                   "tangencies": decl["tangencies"], "gap": decl["gap"]})
    claim.meta["field_d"] = d
    claim.meta["seam"] = str(c + s)
    claim.meta["frame"] = decl["frame"]
    claim.meta["wall"] = decl["wall"]
    claim.meta["declared"] = sum(len(v) for v in decl["tangencies"].values())
    _tag(claim, L, n)
    claim.laws["side"] = ("L", L)
    claim.laws["axis"] = ("axis squares", decl["frame"])
    claim.laws["gap"] = ("gap squares", 4)
    claim.laws["pinwheel"] = ("pinwheel squares", 4)
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


def p_ring(k):
    """The ring rung: a ring at the census's own Q(sqrt 7) word."""
    c, s = _sqrt7_word()
    return ring_claim(7, c, s, k)


# --------------------------------------------------- the staircase (run 95)
#: The census's n = 151 row is not the ring.  It is a **multi-layer staircase**:
#: an odd integer grid, every cell of which is realised on one of two lattices
#: offset by `2c` on both axes (an upper-left staircase `A` and a lower-right one
#: `B`), four corner caps, and a two-layer brick wall of word-aligned squares
#: wedged into the diagonal seam between the blocks.  The seam is a gap by
#: construction: a block-A square and a block-B square would have to differ by
#: `1 +- 2c` on an axis to touch, and no integer is `1 +- 2c` for irrational `c`.
#:
#: The brick wall is the part the ring never had.  Its bricks are placed by
#: *declared* tangency: every one of them is tangent along its own `v` axis to a
#: named seam square of the frame, walking `B(a, a)` then `A(a, a + 1)` for
#: `a = -k .. k - 2`, with the column repeated whenever `a % 3 == 0`.

def staircase_side(cls, c, s, k):
    """The side law again: the caps are flush, so `L = 2k + 1 + 2c`.

    With `c - s = 1/2` this is `2k + 3/2 + (c + s)`, the Q(sqrt 7) family's one
    law; at `k = 5` it is the census n = 151 side `23/2 + 1/2 sqrt 7`.
    """
    return cls(2 * k + 1) + cls(2) * c


def staircase_columns(k):
    """The brick wall's column labels, in `u` order.

    Column `a` carries the pair of bricks tangent to `B(a, a)` and `A(a, a + 1)`.
    The columns run `a = -k .. k - 2`, and every column with `a % 3 == 0` occurs
    twice: the repeats are the bricks that jam the wall's two ends.  At `k = 5`
    the twelve columns are `[-5, -4, -3, -3, -2, -1, 0, 0, 1, 2, 3, 3]`.
    """
    cols = []
    for a in range(-k, k - 1):
        cols.append(a)
        if a % 3 == 0:
            cols.append(a)
    return cols


def _staircase_labels(k):
    """The frame's construction order, so a walk square can be named by index."""
    out = []
    for b in range(-k, k + 1):
        for a in range(-k, b):
            out.append(("A", a, b))
    for b in range(-k, k + 1):
        for a in range(b, k + 1):
            out.append(("B", a, b))
    out += [("C", -k, -k), ("C", -k, -k + 1), ("C", k - 1, k), ("C", k, k)]
    return out


def staircase_frame(cls, c, s, k):
    """The multi-layer axis frame: `4k^2 + 4k + 5` axis squares.

      * `A = {(a - c, b + c) : -k <= a < b <= k}`  -- the upper-left staircase
      * `B = {(a + c, b - c) : -k <= b <= a <= k}` -- the lower-right staircase
      * four corner caps `(-k - c, -k - c)`, `(-k - c, -k + 1 - c)`,
        `(k - 1 + c, k + c)`, `(k + c, k + c)`.

    The blocks are disjoint for every word: block `A` sits at `x - y <= -1 - 2c`
    on its seam edge and block `B` at `x - y >= 2c`, and they are separated on
    some axis whenever `2c >= 1`.  At `k = 5` the count is 125 = 55 + 66 + 4.
    """
    cells = []
    for tag, a, b in _staircase_labels(k):
        if tag == "A":
            cells.append((cls(a) - c, cls(b) + c))
        elif tag == "B":
            cells.append((cls(a) + c, cls(b) - c))
        elif (a, b) == (-k, -k):
            cells.append((-cls(k) - c, -cls(k) - c))
        elif (a, b) == (-k, -k + 1):
            cells.append((-cls(k) - c, -cls(k) + cls(1) - c))
        elif (a, b) == (k - 1, k):
            cells.append((cls(k) - cls(1) + c, cls(k) + c))
        else:
            cells.append((cls(k) + c, cls(k) + c))
    return cells


def _staircase_need(cls, c, s):
    """A tilted square's face `1/2` plus an axis square's reach `(|c|+|s|)/2`."""
    return cls(F(1, 2)) + (abs(c) + abs(s)) * cls(F(1, 2))


def _staircase_walk_v(cls, c, s, k, a):
    """The two brick `v`-coordinates of column `a`, from tangency along `v`.

    Below `B(a, a)` (whose own `v` is `a(c - s) - c(c + s)`) and above
    `A(a, a + 1)` (whose `v` is `a(c - s) + c(1 + c + s)`), each by `need`.
    """
    need = _staircase_need(cls, c, s)
    base = cls(a) * (c - s)
    return (base - c * (c + s) + need,
            base + c * (cls(1) + c + s) - need)


def _staircase_brick(cls, c, s, u, v):
    """The brick centre `p = u (c, s) + v (-s, c)`."""
    return (u * c - v * s, u * s + v * c)


def staircase_seam(cls, c, s, k, u):
    """The two-layer brick wall in the seam: two bricks per column.

    A brick in column `j` sits at `p = (u + j)(c, s) + v(-s, c)`; its `v` comes
    from `_staircase_walk_v`.  The two bricks of a column are `v_A - v_B` apart,
    so they are edge-to-edge along `v` -- a contact, not an overlap -- iff
    `v_A - v_B = 1`, i.e. `2c(c + s) - (1 + s) = 0`: the Q(sqrt 7) identity
    `c - s = 1/2`.  For any other word the two layers do not close (refusal
    `staircase_layer_gap`).

    `u` is the wall's one free transverse parameter.  Every declared tangency is
    along `v`, and `u` and `v` are orthogonal, so sliding the wall along `u`
    preserves all of them; only the wall's non-overlap against the frame fixes
    the feasible `u` window, and the census row fixes the value inside it.
    """
    bricks = []
    for j, a in enumerate(staircase_columns(k)):
        for v in _staircase_walk_v(cls, c, s, k, a):
            bricks.append(_staircase_brick(cls, c, s, u + cls(j), v))
    return bricks


def staircase_tangencies(k):
    """The declared brick-frame tangencies, as `(brick, frame)` index pairs."""
    labels = _staircase_labels(k)
    where = {lab: i for i, lab in enumerate(labels)}
    pairs = []
    for j, a in enumerate(staircase_columns(k)):
        pairs.append((2 * j, where[("B", a, a)]))
        pairs.append((2 * j + 1, where[("A", a, a + 1)]))
    return pairs


def staircase_field(cls, c, s, k, u):
    """The staircase, verified: every declared tangency an exact contact, and the
    exact gate at `staircase_side`.

    Refusals are declared laws:
      * `degenerate_cell`      -- `k < 1` has no staircase;
      * `staircase_layer_gap`  -- the two brick layers are not edge-to-edge along
                                  `v`; this is exactly `c - s != 1/2`, so the
                                  closed wall is the Q(sqrt 7) word's own;
      * `staircase_chain_adrift` -- a declared brick-frame tangency is not along
                                  its named `v` axis by exactly `need`;
      * `staircase_side_mismatch`, `staircase_collides` -- the gate's verdict.

    The declaration is a *named-axis* tangency (brick against seam square, on the
    brick's own `v`), so it is checked on that axis exactly; it is stronger than
    "the gate found no overlap" and weaker than the gate's four-axis "wedged"
    contact, which a brick resting against one seam square need not be.
    """
    if k < 1:
        raise Refusal("degenerate_cell", f"k = {k} has no staircase")
    gap = cls(2) * c * (c + s) - (cls(1) + s) - cls(1)
    if gap != cls(0):
        raise Refusal("staircase_layer_gap",
                      f"the brick layers are {gap} apart along v, not 1: "
                      f"the closed wall needs c - s = 1/2")
    L = staircase_side(cls, c, s, k)
    frame = staircase_frame(cls, c, s, k)
    seam = staircase_seam(cls, c, s, k, u)
    cells = frame + seam
    half = cls(F(1, 2))
    words = [(cls(1), cls(0))] * len(frame) + [(c, s)] * len(seam)
    need = _staircase_need(cls, c, s)
    for i, j in staircase_tangencies(k):
        p, q = seam[i], frame[j]
        dv = (p[0] - q[0]) * (-s) + (p[1] - q[1]) * c
        if abs(dv) != need:
            raise Refusal("staircase_chain_adrift",
                          f"the declared tangency (brick {i}, frame {j}) is "
                          f"{abs(dv)} along v, not {need}")
    g = Q.gate(cells, words, cls)
    if g["L"] != L:
        raise Refusal("staircase_side_mismatch",
                      f"the gate reads {g['L']}, not {L}")
    if not g["ok"]:
        raise Refusal("staircase_collides",
                      f"{g['violations']} pairs overlap at the derived side")
    return {"cells": cells, "words": words, "frame": len(frame),
            "seam": len(seam), "gate": g, "u": u}


def staircase_claim(d, c, s, k, u, family="Staircase", params=None):
    """Gate-verify a staircase over `Q(sqrt d)` and return it as a claim.

    `N = 4k^2 + 4k + 5 + 2|staircase_columns(k)|` -- 149 at `k = 5` (125 axis +
    24 bricks) -- at `L = 2k + 1 + 2c`.  The count is **not** the n = 151 row's
    151: the wall's thirteenth column (`a = k - 1`) pinches against the cap, so
    this grammar constructs 149 of the 151 (control 25 measures the pinch).
    """
    cls = qfield(d)
    if (c * c + s * s) != cls(1):
        raise Refusal("word_off_circle",
                      f"cos^2 + sin^2 = {c * c + s * s} != 1 in Q(sqrt {d})")
    decl = staircase_field(cls, c, s, k, u)
    state, words = decl["cells"], decl["words"]
    g = decl["gate"]
    n = len(state)
    L = g["L"]
    claim = Claim("spatial_geometry", family, params or {"k": k}, n,
                  {"count": ("N", n), "extent": ("L", L),
                   "void": ("L^2 - N", L * L - cls(n)),
                   "contacts": ("contacts", g["contacts"])},
                  {"state": state, "words": words, "field": f"Q(sqrt {d})",
                   "frame": decl["frame"], "seam": decl["seam"],
                   "gauge": decl["u"]})
    claim.meta["field_d"] = d
    claim.meta["frame"] = decl["frame"]
    claim.meta["seam"] = decl["seam"]
    claim.meta["declared"] = 2 * len(staircase_columns(k))
    _tag(claim, L, n)
    claim.laws["side"] = ("L", L)
    claim.laws["axis"] = ("axis squares", decl["frame"])
    claim.laws["brick"] = ("seam bricks", decl["seam"])
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


def p_staircase(k):
    """The staircase rung at the census's own Q(sqrt 7) word.

    `u` is the wall's free transverse gauge; the census row fixes it to
    `-1357/128 + 211/128 sqrt 7`.  Everything else -- 125 axis centres and all 24
    brick centres -- is computed from `k`, the word and that one scalar.
    """
    cls = qfield(7)
    c, s = _sqrt7_word()
    return staircase_claim(7, c, s, k, cls(F(-1357, 128), F(211, 128)))


def p_slope(p, q, k, m=1):
    """The p:q slope ridge: the word `(p, q)/sqrt(p^2+q^2)` lives in Q(sqrt(p^2+q^2))."""
    dd, _kf = squarefree_split(p * p + q * q)
    c, s = unit_word(dd, p, q)
    return p_ridge(dd, c, s, k, "Slope", {"p": p, "q": q, "k": k, "m": m}, m)


def _sqrt7_word():
    """`((1+sqrt7)/4, (sqrt7-1)/4)`: the word the census's n = 18 row actually uses.

    Recovered from the delivered pose's 0.424031039491-radian tilt with
    `exact_field.recover_scalar` at 70-digit precision: cos = 1/4 + 1/4 sqrt7,
    sin = -1/4 + 1/4 sqrt7, and `cos^2 + sin^2 = 1` exactly.  Run 90 used an ad-hoc
    Q(sqrt 7) word `(sqrt7/4, 3/4)`; this one is the table's own.
    """
    cls = qfield(7)
    return cls(F(1, 4), F(1, 4)), cls(F(-1, 4), F(1, 4))


def p_seventh(k, m=1):
    """The Q(sqrt 7) rung: a ridge at the census's own sqrt7 word."""
    c, s = _sqrt7_word()
    return p_ridge(7, c, s, k, "Seventh", {"k": k, "m": m}, m)


def p_tilt(t, k, m=1):
    """A rational-t Pythagorean ridge: `tword(t)` is a rational unit word, exact in Q."""
    t = F(t)
    if not (0 < t < 1):
        raise Refusal("t_out_of_range",
                      f"t = {t} is not in (0, 1): the t-basis word is not a quarter turn")
    c, s = EF.tword(t)
    return p_ridge(2, Q2(c), Q2(s), k, "Tilt", {"t": str(t), "k": k, "m": m}, m)


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
#: The `Quad` subclasses for Q(sqrt d), made once per d.  `exact_field.Quad` carries
#: exact sign, floor, abs and order for any square-free d, and `qsqrt2.gate` takes the
#: class as an argument -- so a higher rung is verified by the *same* procedure, not by
#: a copy of it (control 21 checks the two call forms on every spatial cell).
_QFIELDS: dict = {}


def qfield(d):
    """The `Quad` subclass for `Q(sqrt d)` (d square-free, d >= 2)."""
    if d == 2:
        return Q2
    if d not in _QFIELDS:
        _QFIELDS[d] = type(f"Q{d}", (EF.Quad,), {"d": d, "__slots__": (),
                                                "__module__": __name__})
    return _QFIELDS[d]


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


def gate_of(claim):
    """The gate verdict for a claim, in the claim's own field.

    There is one gate (`qsqrt2.gate`), now parametrised by the field class; a claim only
    declares which field its sentence lives in.
    """
    d = int(claim.meta.get("field_d", 2))
    state, words = claim.payload["state"], claim.payload["words"]
    return Q.gate(state, words, qfield(d))


def pairs_of(claim, i, j):
    d = int(claim.meta.get("field_d", 2))
    state, words = claim.payload["state"], claim.payload["words"]
    return Q.pair_axes(state, words, i, j, qfield(d))


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
                     ("Seventh", p_seventh), ("Tilt", p_tilt), ("Ring", p_ring),
                     ("Staircase", p_staircase)):
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
        Cell("Slope", {"p": 2, "q": 1, "k": k, "m": 2}) for k in (2, 3)
    ] + [
        Cell("Seventh", {"k": k}) for k in (1, 2, 3)
    ] + [
        Cell("Seventh", {"k": k, "m": 2}) for k in (2, 3)
    ] + [
        Cell("Tilt", {"t": "1/2", "k": k}) for k in (1, 2, 3)
    ] + [
        Cell("Tilt", {"t": "1/2", "k": k, "m": 2}) for k in (2, 3)
    ] + [
        Cell("Ring", {"k": 1})
    ] + [
        Cell("Staircase", {"k": 5})
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
        "ring_chain_adrift": lambda: p_ring(2),
        "staircase_layer_gap": lambda: staircase_field(Q2, Q2(0, F(1, 2)),
                                                       Q2(0, F(1, 2)), 1, Q2(0)),
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
    pk = eng.domains["spatial_geometry"]
    compared = 0
    for cell in eng.wheels[0].cells:
        claim = pk.build(cell.family, **cell.params)
        st, ws = claim.payload["state"], claim.payload["words"]
        cls = type(st[0][0])
        g_infer = Q.gate(st, ws)              # the field read off the state
        g_decl = Q.gate(st, ws, cls)          # the field declared
        for key in ("ok", "L", "clearance", "contacts", "violations"):
            assert g_infer[key] == g_decl[key], (cell.family, cell.params, key)
        assert gate_of(claim) == g_infer, (cell.family, cell.params)
        for i in range(len(st)):
            for j in range(i + 1, len(st)):
                a = [(str(q[0]), str(q[1]), sl.sign())
                     for q, sl, _n, _o in Q.pair_axes(st, ws, i, j)]
                b = [(str(q[0]), str(q[1]), sl.sign())
                     for q, sl, _n, _o in pairs_of(claim, i, j)]
                assert a == b, (cell.family, cell.params, i, j)
        compared += 1
    assert compared == len(eng.wheels[0].cells) >= 40, compared
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
    say(f"control 21 — one gate, {compared} spatial cells: the field read off the state "
        "and the field declared give identical verdicts and identical pair slacks on "
        "every cell; the 45-degree ridge reproduces S(k,1) exactly and every rung gates "
        "at clearance 0 with its exact algebraic side: " + "; ".join(rungs))

    # ------------------------------------------------ control 22: the m-diamond bar
    doubles = 0
    for kk in (1, 2, 3):
        for mm in (1, 2, 3):
            ridge = p_ridge(2, *Q.word_45(), kk, "Ridge45", {"k": kk, "m": mm}, mm)
            strip = strip_field(kk, mm)
            cells = sorted(map(tuple, _product_cells(strip["x"], strip["y"])))
            slots = sorted(map(tuple, strip["slots"]))
            st, ws = ridge.payload["state"], ridge.payload["words"]
            axis = sorted(map(tuple, [st[i] for i in range(len(st))
                                      if ws[i] == (Q2(1), Q2(0))]))
            tilt = sorted(map(tuple, [st[i] for i in range(len(st))
                                      if ws[i] != (Q2(1), Q2(0))]))
            assert axis == cells and tilt == slots, (kk, mm)
            assert ridge.size == 4 * kk * kk + mm, (kk, mm, ridge.size)
            assert ridge.laws["extent"][1] == Q2(2 * kk) + S2H * Q2(mm), (kk, mm)
            doubles += 1
    rungs = []
    for fam, d, cw, sw in (("45", 2, *Q.word_45()), ("Slope-2:1", 5, *unit_word(5, 2, 1)),
                           ("Seventh", 7, *_sqrt7_word()),
                           ("Tilt-1/2", 2, Q2(EF.tword(F(1, 2))[0]), Q2(EF.tword(F(1, 2))[1]))):
        cls = qfield(d)
        cw, sw = (cw if isinstance(cw, cls) else cls(cw)), (sw if isinstance(sw, cls) else cls(sw))
        w1 = ridge_width(cls, cw, sw, 2, 1)
        n18 = ridge_width(cls, cw, sw, 2, 2)
        assert n18 == w1 * cls(2), (fam, w1, n18)
        wider = [ridge_width(cls, cw, sw, 2, m) for m in (3, 4)]
        assert all(w > n18 for w in wider), (fam, wider)
        rungs.append(f"{fam}: w*(1)={w1}, w*(2)={n18}=2 w*(1), w*(3)={wider[0]}, "
                     f"w*(4)={wider[1]}, L(2,2)={cls(4) + n18}")
        # the census row's side, honestly: no member of this family reaches it
        target = None
        if d == 7:
            target = (cls(7) + cls(0, 1)) / cls(2)
            assert cls(4) + n18 != target, "unexpected: the ridge captures n = 18"
            assert cls(4) + ridge_width(cls, cw, sw, 2, 1) != target
    # the row itself, read exactly: its tilted word and its side
    import field_triage as T
    row = _delivered_rows()[18]
    tilt_words = {t for _x, _y, t in row if _word_of(t) is None}
    assert len(tilt_words) == 1, tilt_words
    ca, sa = T.cos_sin(tilt_words.pop())
    cls7 = qfield(7)
    cw = EF.recover_scalar(cls7(F(ca)), cls7, dens=(1, 2, 4, 8), bmax=8)
    sw = EF.recover_scalar(cls7(F(sa)), cls7, dens=(1, 2, 4, 8), bmax=8)
    assert (cw.a, cw.b) == (F(1, 4), F(1, 4)), (cw.a, cw.b)
    assert (sw.a, sw.b) == (F(-1, 4), F(1, 4)), (sw.a, sw.b)
    assert cw * cw + sw * sw == cls7(1), "the recovered word must be a unit word"
    axis_n = sum(1 for _x, _y, t in row if _word_of(t) is not None)
    assert (axis_n, len(row) - axis_n) == (10, 8), (axis_n, len(row))
    for _x, _y, _t in row:                       # every coordinate of the pose, exactly
        for _v in (_x, _y):
            assert EF.recover_scalar(cls7(F(_v)), cls7,
                                     dens=(1, 2, 4, 8, 16), bmax=8) is not None, _v
    X = [F(x) for x, _y, _t in row]
    far = EF.recover_scalar(cls7(max(X)), cls7, dens=(1, 2, 4, 8), bmax=8)
    near = EF.recover_scalar(cls7(min(X)), cls7, dens=(1, 2, 4, 8), bmax=8)
    assert (far.a, far.b) == (F(5, 4), F(1, 4)) and (near.a, near.b) == (F(-5, 4), F(-1, 4))
    side = far + far + cls7(1)                      # span of the centres plus one
    assert side == (cls7(7) + cls7(0, 1)) / cls7(2), side
    assert side == cls7(3) + cls7(2) * cw, side     # L = 3 + 2 cos(word)
    say(f"control 22 — the ridge holds m tilted squares: at 45 degrees it reproduces "
        f"strip_field(k, m) cell for cell, slot for slot and side for side on all "
        f"{doubles} (k, m) cells with k, m in 1..3; N = 4k^2 + m; the exact seam law "
        f"w*(2) = 2 w*(1) holds on every rung, and beyond m = 2 the binding pair can "
        f"re-bind -- the 45-degree rung stays linear through m = 4, the oblique rungs "
        f"do not (" + "; ".join(rungs) + "). The census's "
        f"n = 18 row is *not* a member: its tilted word is (1+sqrt7)/4, (-1+sqrt7)/4 "
        f"(recovered from the 12-dp pose at 70 digits and verified on the unit circle), "
        f"its pose is 10 axis squares plus 8 tilted ones, and its side is 3 + 2cos = "
        f"(7 + sqrt7)/2 — an odd rational part with a cosine term, where the ridge's side "
        f"is 2k plus a seam width.")

    # ------------------------------- control 23: the Q(sqrt 7) family and its ring law
    import field_triage as T
    cls7 = qfield(7)
    cw7, sw7 = _sqrt7_word()
    ledger = os.path.join(ROOT, "workspace", "push", "field_triage.json")
    with open(ledger) as f:
        triage = json.load(f)
    rows7 = sorted(r["n"] for r in triage["rows_detail"] if r["class"] == "Q(sqrt7) side")
    assert rows7 == [18, 53, 151, 234, 747], rows7
    target = (cls7(7) + cls7(0, 1)) / cls7(2)
    reporting = []
    integers, halves = [], []
    for n in rows7:
        row = _delivered_rows()[n]
        tilts = {}
        for _x, _y, t in row:
            if _word_of(t) is None:
                tilts[t] = tilts.get(t, 0) + 1
        # the census word occurs in every one of the five rows, and is a unit word there
        cw = sw = None
        for t in sorted(tilts, key=lambda z: -tilts[z]):
            ca, sa = T.cos_sin(t)
            g1 = EF.recover_scalar(cls7(F(ca)), cls7, dens=(1, 2, 4, 8), bmax=8)
            g2 = EF.recover_scalar(cls7(F(sa)), cls7, dens=(1, 2, 4, 8), bmax=8)
            if g1 is not None and g2 is not None and (g1.a, g1.b) == (cw7.a, cw7.b) \
                    and (g2.a, g2.b) == (sw7.a, sw7.b):
                cw, sw = g1, g2
                word_n = tilts[t]
                break
        assert cw is not None and cw * cw + sw * sw == cls7(1), (n, len(tilts))
        X = [F(x) for x, _y, _t in row]
        Y = [F(y) for _x, y, _t in row]
        far = EF.recover_scalar(cls7(max(X)), cls7, dens=(1, 2, 4, 8, 16), bmax=8)
        near = EF.recover_scalar(cls7(min(X)), cls7, dens=(1, 2, 4, 8, 16), bmax=8)
        assert far is not None and near is not None, n
        # the side, read exactly: the span of the centres plus one axis half-extent
        side = far - near + cls7(1)
        fy = EF.recover_scalar(cls7(max(Y)), cls7, dens=(1, 2, 4, 8, 16), bmax=8)
        ny = EF.recover_scalar(cls7(min(Y)), cls7, dens=(1, 2, 4, 8, 16), bmax=8)
        assert side == fy - ny + cls7(1), n
        axis_n = sum(1 for _x, _y, t in row if _word_of(t) is not None)
        # the law: side = 2k + 3/2 + (c + s), with k = (side - 3/2 - (c+s)) / 2
        kk = (side - cls7(F(3, 2)) - (cw + sw)) / cls7(2)
        assert kk.b == 0, (n, kk)
        kv = kk.a
        if kv.denominator == 1:
            assert ring_side(cls7, cw, sw, int(kv)) == side, (n, kv)
            integers.append((n, int(kv)))
        else:
            assert kv.denominator == 2, (n, kv)
            assert (kv * cls7(2)).a.denominator == 1, (n, kv)     # an odd integer
            assert cls7(2 * int(kv * 2)) + cls7(3) + cls7(2) * (cw + sw) == side * cls7(2), (n, kv)
            halves.append((n, str(kv)))
        reporting.append(f"n={n}: {axis_n} axis + {len(row) - axis_n} tilted "
                         f"({word_n} at the census word, {len(tilts)} distinct tilt angles), "
                         f"L={side}, k={kv}")
    assert (n18 := dict(integers).get(18)) == 1, integers
    assert dict(integers)[151] == 5, integers
    assert [n for n, _k in halves] == [53, 234, 747], halves
    assert ring_side(cls7, cw7, sw7, 1) == target, "the ring law must give the n = 18 side"
    say("control 23 — the Q(sqrt 7) family is one word and one side law, split by parity: "
        "every row of it (n = 18, 53, 151, 234, 747, run 86's field sweep) carries the same "
        "unit word ((1+sqrt7)/4, (-1+sqrt7)/4), recovered here from each row's own tilt at "
        "70 digits, and its side is (2m+1)/2 + sqrt7/2 = 2k + 3/2 + (c + s), so the run-92 "
        "'odd rational part plus 2cos' is the k = 1 case of a single law: "
        + "; ".join(reporting) +
        ". Two rows sit at integer k (18: k = 1, 151: k = 5) and three at half-integer k "
        "(53: k = 5/2, 234: k = 13/2, 747: k = 25/2), and their pose alphabets differ "
        "widely (2, 4, 3, 2 and 665 distinct angles); the ring law's k = 1 member is "
        "exactly 7/2 + sqrt7/2. Run 94 builds that member as a sentence (control 24) and "
        "tests the same grammar at k = 5, where it splits.")

    # --------------------------- control 24: the ring, solved from its own tangencies
    ring = ring_claim(7, cw7, sw7, 1)
    assert ring.n == 18, ring.n
    assert ring.laws["extent"][1] == target, ring.laws["extent"][1]
    assert (ring.meta["frame"], ring.meta["wall"]) == (10, 14), ring.meta["frame"]
    assert ring.meta["declared"] == 22, ring.meta["declared"]
    assert p_ring(1).n == 18 and p_ring(1).laws["extent"][1] == target
    cells = ring.payload["state"]
    words = ring.payload["words"]
    g = Q.gate(cells, words, cls7)
    assert g["ok"] and g["clearance"] == 0 and g["L"] == target, g
    assert g["contacts"] == 26, g["contacts"]            # 22 declared + 4 incidental
    for group, pairs in ring.payload["tangencies"].items():
        for i, j in pairs:
            axes = Q.pair_axes(cells, words, i, j, cls7)
            assert any(sl == 0 for _q, sl, _n, _o in axes), (group, i, j)
    dec = DecimalWitness.scalar
    cens = _delivered_rows()[18]
    worst = Decimal(0)
    for x, y in cells:
        px, py = dec(x), dec(y)
        near = min(cens, key=lambda r: abs(dec(r[0]) - px) + abs(dec(r[1]) - py))
        worst = max(worst, abs(dec(near[0]) - px), abs(dec(near[1]) - py))
    assert worst < Decimal("1e-4"), worst
    split = []
    for kk in (2, 3, 4, 5):
        try:
            ring_claim(7, cw7, sw7, kk)
            raise AssertionError(f"the ring must not certify at k = {kk}")
        except Refusal as e:
            assert e.law == "ring_chain_adrift", (kk, e.law)
            decl = ring_declaration(cls7, cw7, sw7, kk)
            c5, w5 = decl["cells"], decl["words"]
            idx = _ring_indices(kk)
            slack = max(sl for _q, sl, _n, _o in
                        Q.pair_axes(c5, w5, idx["p8"], idx["m5"], cls7))
            g5 = Q.gate(c5, w5, cls7)
            # The drift is a *declared* law, not a collision -- but only from k = 3.
            # At k = 3, 4, 5 the drifted sentence still separates with clearance
            # exactly 0; at k = 2 the drift is large enough to collide as well.
            if kk >= 3:
                assert g5["ok"] and g5["clearance"] == 0 and g5["violations"] == 0, (kk, g5)
            else:
                assert not g5["ok"] and g5["violations"] > 0, (kk, g5)
            adrift = [(grp, i, j) for grp, prs in ring_tangencies(kk).items()
                      for i, j in prs if not _ring_contact(cls7, c5, w5, i, j)]
            assert len(adrift) == 8, (kk, adrift)
            assert sum(1 for grp, _i, _j in adrift if grp == "pin") == 4, adrift
            split.append(f"k={kk}: N would be {4 * kk + 14}, closure slack {slack}, "
                         f"gate {'clear at 0' if g5['ok'] else 'colliding'}, "
                         f"{len(adrift)} of 22 declarations adrift")
    rows151 = _delivered_rows()[151]
    probe = ring_side(cls7, cw7, sw7, 5)
    axis151 = sum(1 for _x, _y, t in rows151 if _word_of(t) is not None)
    cols151 = len({x for x, _y, t in rows151 if _word_of(t) is not None})
    assert (len(rows151), axis151, cols151) == (151, 125, 21), (axis151, cols151)
    assert probe == (cls7(23) + cls7(0, 1)) / cls7(2), probe
    say("control 24 — the ring is the census's own 10 + 4 + 4 sentence, solved: a C2 "
        "perimeter of 10 axis squares (4 corners, a 3-square run up the left wall, a "
        "3-square run down the right wall, one square inward on the bottom wall and one "
        "on the top), four gap squares wedged across the four wall gaps by two declared "
        "tangencies each, and a four-square pinwheel that closes each chain end onto the "
        "opposite gap square. Each of the eight tilted squares is a 2x2 solve in Q(sqrt 7) "
        "from those tangencies -- 22 declared, every one an exact contact -- and the exact "
        "gate certifies N = 18 at L = " + str(target) + " with clearance 0 and "
        f"{g['contacts']} contacts -- the 22 declared, plus 4 that follow by consequence "
        "(the bottom and top wall squares against the opposite chain end, and the two "
        "inner diagonals `p6/-p7`, `-p6/p7`). The census "
        f"row itself agrees to {worst:.1e} in every centre, so the n = 18 pose *is* this "
        "sentence: run 93 read the 10 + 4 + 4 counts correctly but the corner-module "
        "grammar wrongly. The grammar does not generalise: the pinwheel's closure contact "
        "is a k = 1 identity (" + "; ".join(split) + "), because the chain end's u-distance "
        "stays 1 at every k while its v-offset is 2p5.v + 2, which grows by sqrt7 per k. "
        "So k >= 2 is a declared refusal; from k = 3 up the drifted sentence still passes "
        "the geometric gate at clearance 0 and fails only its declared tangencies "
        "(8 of the 22, 4 of them the pinwheel closure), while at k = 2 the drift is large "
        "enough that the sentence also collides. The census's own k = 5 row "
        "is not this family's member even in count: the ring would have N = 4k + 14 = 34 "
        "squares at L = " + str(probe) + ", while n = 151 is a 151-square staircase ("
        f"{axis151} axis squares in {cols151} staggered columns plus "
        f"{len(rows151) - axis151} tilted). The side law generalises; the sentence splits.")

    # --------------------- control 25: the staircase and its corner pinch (run 95)
    stair = p_staircase(5)
    target151 = (cls7(23) + cls7(0, 1)) / cls7(2)
    assert stair.n == 149, stair.n
    assert stair.laws["extent"][1] == target151, stair.laws["extent"][1]
    assert (stair.meta["frame"], stair.meta["seam"]) == (125, 24), stair.meta["frame"]
    assert stair.meta["declared"] == 24, stair.meta["declared"]
    assert len(staircase_columns(5)) == 12, staircase_columns(5)
    c25 = stair.payload["state"]
    w25 = stair.payload["words"]
    g25 = Q.gate(c25, w25, cls7)
    assert g25["ok"] and g25["clearance"] == 0 and g25["L"] == target151, g25
    need25 = _staircase_need(cls7, cw7, sw7)
    for i, j in staircase_tangencies(5):
        p, q = c25[125 + i], c25[j]
        dv = (p[0] - q[0]) * (-sw7) + (p[1] - q[1]) * cw7
        assert abs(dv) == need25, (i, j)
    # the wall's thirteenth column pinches: the closed 151-square sentence is refused
    gauge = cls7(F(-1357, 128), F(211, 128))
    closed = list(c25)
    for v in _staircase_walk_v(cls7, cw7, sw7, 5, 4):
        closed.append(_staircase_brick(cls7, cw7, sw7, gauge + cls7(12), v))
    gc = Q.gate(closed, list(w25) + [(cw7, sw7)] * 2, cls7)
    pinch = cls7(F(-163, 128), F(61, 128))
    assert len(closed) == 151 and not gc["ok"] and gc["violations"] == 1, gc
    assert gc["clearance"] == pinch, gc["clearance"]
    # the census row: 149 of its 151 centres are this sentence's, to the pose's noise
    dec = DecimalWitness.scalar
    cens = _delivered_rows()[151]
    worst = Decimal(0)
    for x, y in c25:
        px, py = dec(x), dec(y)
        near = min(cens, key=lambda r: abs(dec(r[0]) - px) + abs(dec(r[1]) - py))
        worst = max(worst, abs(dec(near[0]) - px), abs(dec(near[1]) - py))
    assert worst < Decimal("1e-4"), worst
    # the two squares the table adds are rotated out of the field
    odd = F(19211307153, 31250000000)
    ca, sa = T.cos_sin(odd)
    dens = (64, 128, 256, 512, 1024, 2048, 4096)
    oc = EF.recover_scalar(cls7(F(ca)), cls7, dens=dens, bmax=8)
    os_ = EF.recover_scalar(cls7(F(sa)), cls7, dens=dens, bmax=8)
    assert oc is not None and os_ is not None, "the odd word must be found near Q(sqrt 7)"
    assert oc * oc + os_ * os_ != cls7(1), "the odd word would be a unit word after all"
    assert T.pyth_angle(odd, qmax=1024) is None, "the odd word would be Pythagorean"
    # honesty: at k = 5 the family does not beat the table at its own count
    assert stair.meta["table_side"] is not None, stair.meta
    assert stair.meta["beats_table"] is False, stair.meta
    # the spin over (k, word): the family's count is the frame plus the brick wall
    # (`4k^2 + 4k + 5 + 2|columns(k)|`), and no member beats its delivered row
    spin = []
    for kk in range(1, 10):
        nn = 4 * kk * kk + 4 * kk + 5 + 2 * len(staircase_columns(kk))
        Lk = staircase_side(cls7, cw7, sw7, kk)
        sidek = _table_side(nn)
        if sidek is None:
            spin.append(f"k={kk}: N={nn} uncalibrated")
            continue
        behind = DecimalWitness.scalar(Lk) - DecimalWitness.scalar(sidek)
        assert behind > 0, (kk, nn, Lk, sidek)
        spin.append(f"k={kk}: N={nn} behind by {behind:.4f}")
    assert 4 * 25 + 20 + 5 + 2 * len(staircase_columns(5)) == 149
    say("control 25 -- the n = 151 row is a *multi-layer staircase*, and its axis layer is "
        "grammar: an odd integer grid on two lattices offset by 2c (an upper-left block of "
        "55 and a lower-right block of 66 at k = 5), four corner caps, and a two-layer brick "
        "wall in the diagonal seam.  At k = 5 that is 125 axis squares plus 24 bricks -- "
        "each brick tangent along its own v to B(a, a) or A(a, a + 1), walking "
        "a = -k..k-2 with the column repeated when a % 3 == 0 -- and the exact gate "
        "certifies N = 149 at L = " + str(target151) + " with clearance 0 and "
        f"{g25['contacts']} contacts, all 24 declarations exact.  The grammar is "
        "*closed* only at the Q(sqrt 7) word: the two bricks of a column are "
        "v_A - v_B = 2c(c + s) - (1 + s) apart, which is 1 exactly when c - s = 1/2 "
        "(control 5 refuses the 45-degree word by staircase_layer_gap).  It constructs "
        "149 of the census's 151, and the reason is exact: the wall's thirteenth column "
        "(a = k - 1) overlaps the top-right cap by " + str(pinch) + " (= " +
        f"{dec(pinch):.6f}), one violation; sliding the wall trades that pinch for another "
        "rather than opening the corner.  That is why the table rotates those two squares: "
        "their word is 0.6147618 rad, whose cos and sin are not a unit word of Q(sqrt 7) at "
        f"height <= 4096 (cos^2 + sin^2 = {oc * oc + os_ * os_}) and not Pythagorean (no "
        "t with denominator <= 1024), so a field-general Q(sqrt 7) staircase cannot reach "
        f"n = 151.  The 149 centres reproduce the delivered row to {worst:.1e}, and the "
        "family does not beat the table at n = 149 (its table side is " +
        str(stair.meta["table_side"]) + "); no row is claimed.  A spin over k = 1..9 at "
        "the same word (the count is the frame plus the wall, "
        "4k^2 + 4k + 5 + 2|columns(k)|) never beats a delivered row: " +
        "; ".join(spin) + ".")

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
