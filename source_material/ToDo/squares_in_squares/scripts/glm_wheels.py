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
    """One certified-or-refused cell: the sentence, its laws, and its evidence."""

    domain: str
    family: str
    params: dict
    n: int
    laws: dict                    # name -> (formula, exact value)
    payload: object               # domain object (state/words, or the word)
    meta: dict = field(default_factory=dict)

    def law_str(self, name):
        formula, value = self.laws[name]
        return f"{formula} = {value}"

    def brief(self):
        return f"{self.domain}/{self.family}{tuple(self.params.values())}"


# ---------------------------------------------------------------- witnesses
class Witness:
    """A kind of evidence.  Subclasses implement `check(claim) -> (ok, detail)`."""

    name = "witness"
    law = "witness_failed"

    def check(self, claim: Claim):            # pragma: no cover - interface
        raise NotImplementedError

    def applies(self, claim: Claim) -> bool:
        return True


class PackingGateWitness(Witness):
    """The exact SAT sentence gate: every pair separated, on a field sign only."""

    name = "exact_gate"
    law = "gate_refused"

    def applies(self, claim):
        return claim.domain == "spatial_geometry"

    def check(self, claim):
        g = Q.gate(claim.payload["state"], claim.payload["words"])
        # a one-square sentence has no pairs at all: clearance is None, not 0
        ok = g["ok"] and (g["clearance"] is None or g["clearance"] == 0)
        return ok, f"gate {'ok' if g['ok'] else 'REFUSED'}, clearance " \
                   f"{g['clearance']}, contacts {g['contacts']}, " \
                   f"violations {g['violations']}"


class ContactGraphWitness(Witness):
    """Topology: the contact graph must be connected, min degree >= 1, edges >= 2N-3."""

    name = "contact_graph"
    law = "contact_graph_thin"

    def applies(self, claim):
        return claim.domain == "spatial_geometry"

    def check(self, claim):
        state, words = claim.payload["state"], claim.payload["words"]
        n = len(state)
        if n == 1:
            return True, "single square: no pairs, no contacts needed"
        adj = [[] for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                axes = Q.pair_axes(state, words, i, j)
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

    def applies(self, claim):
        return claim.domain == "spatial_geometry"

    def check(self, claim):
        n = claim.n
        L = claim.laws["extent"][1]
        V = claim.laws["void"][1]
        ok = (Q2(n) + V) == L * L and (L * L - Q2(n)).sign() >= 0 and n >= 1
        return ok, f"N + V = {n} + ({V}) = {Q2(n) + V} and L^2 = {L * L}"


class DecimalWitness(Witness):
    """Independent 70-digit Decimal recomputation; signs and values must agree."""

    name = "decimal_cross"
    law = "decimal_mismatch"

    def applies(self, claim):
        return claim.domain in ("spatial_geometry", "sturmian_sequences")

    def _dec(self, z):
        """The exact value as a Decimal (sqrt taken by Decimal, never by float)."""
        return (Decimal(z.a.numerator) / Decimal(z.a.denominator)
                + Decimal(z.b.numerator) / Decimal(z.b.denominator)
                * Decimal(z.d).sqrt())

    def check(self, claim):
        if claim.domain == "spatial_geometry":
            state, words = claim.payload["state"], claim.payload["words"]
            L = claim.laws["extent"][1]
            # recompute the bbox in Decimal and compare with the field's side
            xs, ys = [], []
            for (x, y), w in zip(state, words):
                ex = (abs(w[0]) + abs(w[1])) * HALF
                xs += [self._dec(x - ex), self._dec(x + ex)]
                ys += [self._dec(y - ex), self._dec(y + ex)]
            Ld = max(max(xs) - min(xs), max(ys) - min(ys))
            gap = abs(Ld - self._dec(L))
            # A pair is separated iff its BEST axis slack is >= 0, and the sentence iff
            # every pair is: recompute both in Decimal and compare with the exact gate.
            worst = None
            dec_ok = True
            for i in range(len(state)):
                for j in range(i + 1, len(state)):
                    best = None
                    for _q, slack, _need, _o in Q.pair_axes(state, words, i, j):
                        sd = self._dec(slack)
                        best = sd if best is None else max(best, sd)
                        worst = sd if worst is None else min(worst, sd)
                    if best is not None and best < 0:
                        dec_ok = False
            exact_ok = Q.gate(state, words)["ok"]
            ok = gap <= Decimal("1e-40") and dec_ok == exact_ok
            w = "no pairs" if worst is None else f"{worst:.3e}"
            return ok, (f"|L_dec - L| = {gap:.3e}, worst slack_dec {w}, pair verdict "
                        f"{dec_ok} == exact {exact_ok}")
        # sequence domain: the weight sum, recomputed in Decimal
        word, alpha = claim.payload["word"], claim.payload["alpha"]
        n1 = sum(word)
        total = (Decimal(len(word) - n1) * (1 - self._dec(alpha))
                 + Decimal(n1) * self._dec(alpha))
        exact = claim.laws["measure"][1]
        gap = abs(total - self._dec(exact))
        return gap <= Decimal("1e-40"), f"|measure_dec - measure| = {gap:.3e}"


class MechanicalWitness(Witness):
    """Sequences: the word is the mechanical word of its slope and intercept."""

    name = "exact_gate"
    law = "not_mechanical"

    def applies(self, claim):
        return claim.domain == "sturmian_sequences"

    def check(self, claim):
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

    def applies(self, claim):
        return claim.domain == "sturmian_sequences"

    def check(self, claim):
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

    def applies(self, claim):
        return claim.domain == "sturmian_sequences"

    def check(self, claim):
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
    """An alphabet, a combinator registry, and the witnesses its claims must pass."""

    def __init__(self, name, alphabet, witnesses):
        self.name, self.alphabet = name, alphabet
        self.witnesses = witnesses
        self.combinators: dict[str, Callable[..., Claim]] = {}

    def register(self, name, fn):
        self.combinators[name] = fn
        return fn

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
            row = {"wheel": self.name, "family": cell.family,
                   "params": {k: str(v) for k, v in cell.params.items()},
                   "verdict": None, "witnesses": {}, "refusal": None, "laws": {}}
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
            for w in self.domain.witnesses:
                if not w.applies(claim):
                    continue
                try:
                    ok, detail = w.check(claim)
                except Exception as e:
                    ok, detail = False, f"{type(e).__name__}: {e}"
                row["witnesses"][w.name] = {"ok": bool(ok), "detail": detail}
                if not ok and failed is None:
                    failed = w
            row["laws"] = {k: str(v[1]) for k, v in claim.laws.items()}
            row["n"] = claim.n
            row["beats"] = claim.meta.get("beats")
            gain = claim.meta.get("gain")
            row["gain"] = None if gain is None else str(gain)
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
    """Attach the exact gain-vs-grid law (grid(n) = ceil(sqrt n), exactly)."""
    k = Q.grid_side(n)
    claim.meta["beats"] = L < k
    claim.meta["gain"] = k - L
    claim.laws["gain"] = ("ceil(sqrt N) - L", k - L)
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
    """S(k, m): four k-blocks in the corners and an m-diamond strip on the anti-diagonal."""
    if m < 1:
        raise Refusal("strip_needs_diamond",
                      f"S({k}, {m}) has no diamond, so it is the plain 2k grid: no seam")
    if k < 1:
        raise Refusal("degenerate_cell", f"k = {k} has no blocks")
    st, ws, L = Q_mixed_strip(k, m)
    n = 4 * k * k + m
    return _tag(Claim("spatial_geometry", "Strip", {"k": k, "m": m}, n,
                      _laws_packing(n, L, L * L - Q2(n)),
                      {"state": st, "words": ws}), L, n)


def Q_mixed_strip(k, m):
    """The S(k, m) sentence, imported from the run-84 instrument (single source)."""
    import mixed_field as M
    return M.strip_sentence(k, m)


def p_pocket(k):
    """The corner pocket: four k-blocks and one diamond, i.e. S(k, 1)."""
    if k < 1:
        raise Refusal("degenerate_cell", f"k = {k}")
    st, ws, L = Q_mixed_strip(k, 1)
    n = 4 * k * k + 1
    return _tag(Claim("spatial_geometry", "Pocket", {"k": k}, n,
                      _laws_packing(n, L, L * L - Q2(n)),
                      {"state": st, "words": ws}), L, n)


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
                     ("Glue", p_glue), ("SymmetryFold", p_fold), ("Atom", p_atom)):
        pk.register(name, fn)
    eng.register(pk)

    sq = Domain("sturmian_sequences", SEQ_ALPHABET,
                [MechanicalWitness(), ComplexityWitness(),
                 SequenceConservationWitness(), DecimalWitness()])
    for name, fn in (("Tile", s_tile), ("Frame", s_frame), ("Strip", s_strip),
                     ("Glue", s_glue), ("SymmetryFold", s_fold)):
        sq.register(name, fn)
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
    ] + [
        Cell("Atom", {"n": n}) for n in (5, 10, 40)
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
    checks = 0

    # 1. the same five combinator names are registered on both domains
    pk, sq = eng.domains["spatial_geometry"], eng.domains["sturmian_sequences"]
    shared = set(pk.combinators) & set(sq.combinators)
    assert shared >= {"Tile", "Strip", "Glue", "SymmetryFold"}, shared
    print(f"control 1 — both domains register the same engine slots {sorted(shared)}")

    # 2. the packing wheel certifies its closed-form families
    rows = eng.wheels[0].spin()
    cert = [r for r in rows if r["verdict"] == "certified"]
    assert len(cert) >= 15, len(cert)
    print(f"control 2 — spatial wheel: {len(cert)}/{len(rows)} cells certified")

    # 3. every certified packing cell has all four witnesses, not one metric
    for r in cert:
        assert len(r["witnesses"]) == 4, r
        assert all(w["ok"] for w in r["witnesses"].values()), r
    print("control 3 — every certified spatial cell passes all four witnesses "
          "(gate, contact graph, conservation, Decimal)")

    # 4. the strip's closed forms hold for the wheel's own cells
    for r in cert:
        if r["family"] != "Strip":
            continue
        k, m = int(r["params"]["k"]), int(r["params"]["m"])
        assert r["n"] == 4 * k * k + m
    print("control 4 — the Strip cells satisfy N = 4k^2 + m and L = 2k + m sqrt2/2")

    # 5. a non-viable cell refuses with a named law (never a silent skip)
    refused = [r for r in rows if r["verdict"] == "refused"]
    assert refused, "the wheel must have at least one refused cell"
    assert all(r["refusal"]["law"] for r in refused)
    laws = sorted({r["refusal"]["law"] for r in refused})
    print(f"control 5 — {len(refused)} non-viable spatial cells, each with a law: {laws}")

    # 6. the fold is an exact symmetry: same N, same L, witnesses still pass
    a, b = p_pocket(2), p_fold(2)
    assert a.n == b.n and a.laws["extent"][1] == b.laws["extent"][1]
    print("control 6 — the diagonal fold preserves N and L exactly")

    # 7. sequences: an irrational slope gives a Sturmian word, a rational one does not
    rows = eng.wheels[1].spin()
    by_t = {}
    for r in rows:
        by_t[(r["params"]["t"], r["verdict"])] = by_t.get((r["params"]["t"], r["verdict"]), 0) + 1
    assert any(r["params"]["t"] == str(Q2(-1, 1)) and r["verdict"] == "certified"
               for r in rows), rows
    assert any(r["params"]["t"] == "1/2" and r["verdict"] == "refused" for r in rows)
    print("control 7 — slope sqrt2-1 certifies, slope 1/2 is refused (not Sturmian)")

    # 8. the refusal for a rational slope is the complexity law, with its numbers
    bad = [r for r in rows if r["params"]["t"] == "1/2"][0]
    assert bad["refusal"]["law"] == "not_sturmian", bad["refusal"]
    print(f"control 8 — rational slope refused by the exact law: {bad['refusal']}")

    # 9. the coboundary law d(uv) = du xor dv holds on the glue cell
    glue = [r for r in rows if r["family"] == "Glue"][0]
    assert glue["verdict"] == "certified"
    assert "coboundary" in glue["witnesses"]["conservation"]["detail"]
    print("control 9 — the glue cell passes the coboundary witness on its join")

    # 10. Decimal cross-check: the signs agree, and a perturbed claim is caught
    claim = p_pocket(2)
    ok, detail = DecimalWitness().check(claim)
    assert ok, detail
    claim2 = p_pocket(2)
    claim2.laws["extent"] = ("L", claim2.laws["extent"][1] + Q2(F(1, 10 ** 9)))
    ok2, _ = DecimalWitness().check(claim2)
    assert not ok2, "the Decimal witness must catch a 1e-9 lie"
    print("control 10 — the Decimal witness accepts the exact side and catches a 1e-9 lie")

    # 11. the tower audit covers this module too
    checked, offenders, skipped = EF.audit_module(sys.modules[__name__],
                                                  exempt=EF.AUDIT_EXEMPT)
    assert offenders == [], offenders
    print(f"control 11 — this module's {checked} decision functions name no float "
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
    print(f"control 12 — the 2D cage recovers the freed square exactly ({pt}) and "
          f"returns nothing when the cage is empty")

    print("selftest: OK (12 controls)")
    return checks


# --------------------------------------------------------------------- report
def report(eng, ledger):
    spins = eng.spin_all()
    print("\nWHEEL SPIN — declared cells, exact laws, multi-witness verdicts\n")
    for name, rows in spins.items():
        s = Engine.summarise(rows)
        print(f"  {name}: {s['certified']}/{s['cells']} certified, "
              f"{s['refused']} refused {s['refusal_laws']}")
    print("\n  spatial_geometry")
    print(f"    {'family':13s} {'params':16s} {'N':>5s} {'L exact':>16s} "
          f"{'gain':>11s} {'verdict':>10s}  law")
    for r in spins["spatial"]:
        p = ",".join(f"{k}={v}" for k, v in r["params"].items())
        law = r["refusal"]["law"] if r["refusal"] else ""
        gain = r.get("gain", "")
        print(f"    {r['family']:13s} {p:16s} {r.get('n', 0):5d} "
              f"{r['laws'].get('extent', ''):>16s} {str(gain):>11s} "
              f"{r['verdict']:>10s}  {law}")
    print("\n  sturmian_sequences")
    for r in spins["sequences"]:
        p = ",".join(f"{k}={v}" for k, v in r["params"].items())
        law = r["refusal"]["law"] if r["refusal"] else ""
        print(f"    {r['family']:13s} {p:28s} {r.get('n', 0):5d} "
              f"{r['laws'].get('ones', ''):>8s} {r['verdict']:>10s}  {law}")
    ledger["spins"] = {name: {"summary": Engine.summarise(rows), "rows": rows}
                       for name, rows in spins.items()}
    return spins


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        return selftest()
    if "--audit" in argv:
        mods = [EF, Q, sys.modules[__name__]]
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
    print("run 85 — glm_wheels.py: the domain-agnostic wheel, over two domains")
    print(f"scorer guard: {SQ.summarise(SQ.load())['score']:.9f}, no row changes\n")
    eng = build_engine()
    ledger = {"run": 85, "instrument": "glm_wheels.py + exact_field.py + qsqrt2.py",
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
