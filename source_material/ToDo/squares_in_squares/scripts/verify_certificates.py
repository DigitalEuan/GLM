#!/usr/bin/env python3
r"""verify_certificates.py — the serialized certificate verifier (runs 101 and 102).

A standalone, zero-float reader for `workspace/push/galois_certificates.json`.  It
reconstructs every sentence **from the file alone** and decides it exactly:

  * every scalar is parsed as an exact field element (`Q` or `Quad(d)`), and a decimal
    spelling is refused by the parser — a decimal is a display projection, not a value;
  * every cell's rotation matrix is checked (`R^T R = I` and `det R = 1`);
  * every wall inequality is checked in the certificate's own container box;
  * every pairwise 4-axis SAT inequality is decided **on integer-scaled components**,
    recording the witness axis and the exact gap, with `>= 0` accepted at clearance 0;
  * the declared summary (N, L, contacts, clearance) is recomputed and compared.

The SAT pass is deliberately *not* the producer's formulation.  The producer
(`qsqrt2.pair_axes`) multiplies `Quad` values; this verifier scales every centre and
rotation by one common denominator `D` and works in `Z[sqrt d]` with Python integers:
`slack` is represented by the integer residual `2 D^2 slack`, `abs` is an integer sign
test, `max` is an integer comparison, and only the *printed* gap is turned back into a
field element.  The `Quad` formulation is retained as `sat_pass_reference` and used by
`cross_check`/`--selftest` as an independent witness — it never decides anything — and
`fuzz` compares the two on random exact sentences (coincident centres, near-overlaps, exact
contacts, mixed denominators), because a single document only exercises the pairs it has.

The first exact failed inequality is reported, distinguishing the two questions a
certificate can fail to answer:

  kind = "infeasible"             the object is representable and an inequality is false
  kind = "outside_representation" the file does not represent an exact sentence at all
                                  (decimal string, wrong scalar shape, unknown field tag,
                                   duplicate id, a declared L that is not the sentence's
                                   own side, a declared summary the object does not have)

Usage:
    python3 scripts/verify_certificates.py                 # default document
    python3 scripts/verify_certificates.py path/to.json --quiet
    python3 scripts/verify_certificates.py --selftest      # mutations + cross-check + fuzz
    python3 scripts/verify_certificates.py --fuzz [N] [SEED]   # random-sentence fuzz
"""
from __future__ import annotations

import json
import os
import random
import re
import sys
from fractions import Fraction as F
from math import gcd

import exact_field as EF

FORMAT = "galois-certificate/1"
#: A certificate's scalar: a canonical fraction, never a decimal and never an exponent.
NUM_RE = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:/[1-9][0-9]*)?$")
TAG_RE = re.compile(r"^(?:Q|Quad\(([1-9][0-9]*)\))$")

INFEASIBLE = "infeasible"
OUTSIDE = "outside_representation"


class Failure(Exception):
    """The first exact thing that is wrong with a certificate."""

    def __init__(self, kind, check, detail):
        super().__init__(f"{kind}: {check}")
        self.kind = kind
        self.check = check
        self.detail = detail

    def as_dict(self):
        return {"status": "failed", "kind": self.kind, "check": self.check,
                "detail": self.detail}


def _fail(kind, check, **detail):
    raise Failure(kind, check, detail)


# --------------------------------------------------------------- parsing
_CLASS_CACHE = {}


def parse_field(tag):
    """`(d, cls)` for the schema's field tag; `cls` is None for `Q` (plain Fraction)."""
    if not isinstance(tag, str) or not TAG_RE.match(tag):
        _fail(OUTSIDE, "field_tag", tag=tag,
              why="a certificate names one of Q, Quad(2), Quad(5), Quad(7), ...")
    name = TAG_RE.match(tag).group(1)
    if name is None:
        return 0, None
    d = int(name)
    if tag not in _CLASS_CACHE:
        _CLASS_CACHE[tag] = type(f"CertQ{d}", (EF.Quad,), {"d": d, "__slots__": ()})
    return d, _CLASS_CACHE[tag]


def parse_scalar(raw, tag, where):
    """One exact scalar: a canonical fraction string, or `[a, b]` for a `Quad(d)`."""
    if tag == "Q":
        if not isinstance(raw, str) or not NUM_RE.match(raw):
            _fail(OUTSIDE, "number_format", where=where, value=raw,
                  why="tag Q wants a canonical fraction string; decimals are projections")
        value = F(raw)
        if str(value) != raw:
            _fail(OUTSIDE, "number_format", where=where, value=raw,
                  why=f"not canonical: {raw} is {value}")
        return value
    if not (isinstance(raw, list) and len(raw) == 2
            and all(isinstance(v, str) and NUM_RE.match(v) for v in raw)):
        _fail(OUTSIDE, "number_format", where=where, value=raw,
              why=f"tag {tag} wants a two-string [a, b] pair; decimals are projections")
    a, b = F(raw[0]), F(raw[1])
    if str(a) != raw[0] or str(b) != raw[1]:
        _fail(OUTSIDE, "number_format", where=where, value=raw, why="not canonical")
    d, cls = parse_field(tag)
    return cls(a, b)


def _q(z):
    """Display an exact scalar the way the project's documents do."""
    return str(z)


def _sign(z):
    """Exact sign of a Fraction or a field element."""
    return (z > 0) - (z < 0)


# ------------------------------------------------ the SAT pass, on integers
#: Every arithmetic step below is Python integer arithmetic in `Z[sqrt d]`; the only
#: scalar helper it borrows from the tower is the sign rule (`integral_sign`), which is
#: the same rule the residue mask uses and is not the gate's formulation.
def _common_den(scalars):
    """An even common denominator for a list of exact scalars (field or rational)."""
    den = 2
    for z in scalars:
        a, b = (z.a, z.b) if isinstance(z, EF.Quad) else (z, F(0))
        for v in (a, b):
            den = den * v.denominator // gcd(den, v.denominator)
    return den


def _to_int(z, D):
    """`D` times an exact scalar, as an integer `(a, b)` pair of `Z[sqrt d]`."""
    a, b = (z.a, z.b) if isinstance(z, EF.Quad) else (z, F(0))
    a, b = a * D, b * D
    if a.denominator != 1 or b.denominator != 1:      # impossible: D is their common multiple
        _fail(OUTSIDE, "scale", value=_q(z), denominator=D)
    return (a.numerator, b.numerator)


def _imul(u, v, d):
    """`(a + b r)(c + e r)` in `Z[r]`."""
    a, b = u
    c, e = v
    return (a * c + d * b * e, a * e + b * c)


def _iadd(u, v):
    return (u[0] + v[0], u[1] + v[1])


def _isub(u, v):
    return (u[0] - v[0], u[1] - v[1])


def _iabs(u, d):
    return u if EF.integral_sign(u[0], u[1], d) >= 0 else (-u[0], -u[1])


def _icmp(u, v, d):
    """`sign(u - v)` on integer components."""
    return EF.integral_sign(u[0] - v[0], u[1] - v[1], d)


def _abs_ge(z, s, d):
    """`|z| >= s` for integer components and a positive integer `s`."""
    return (EF.integral_sign(z[0] - s, z[1], d) >= 0
            or EF.integral_sign(z[0] + s, z[1], d) <= 0)


def _scaled_str(z, cls, scale):
    """The exact value `z / scale` as the project prints it — display only.

    This is the single place the deciding pass touches a field element, and it happens
    *after* the verdict, to write the gap into the report.  No comparison is made here.
    Slacks are printed with `scale = 2 D^2` (the residual's own scale); a `D`-scaled
    vector component is printed with `scale = D`.
    """
    if cls is None:
        return str(F(z[0], scale))
    return str(cls(F(z[0], scale), F(z[1], scale)))


def _dot(u, v, d):
    """`u . v` for vectors of two field elements held as integer pairs."""
    return _iadd(_imul(u[0], v[0], d), _imul(u[1], v[1], d))


def sat_pass_scaled(d, centres, frames, scale, cls=None):
    """Every pair's four SAT slacks as integer residuals, `2 scale^2`-scaled.

    With `D = scale`, every coordinate and every frame component is an integer of
    `Z[sqrt d]`, so a centre is a pair of field elements and a frame row `u` is a vector
    `(ux, uy)` of them.  The four slacks of a pair are then

        slack_s  =  2 (delta . q) - (D^2 + |u_o . q| + |v_o . q|),     S = 2 D^2,

    each an exact integer pair whose sign is the sign of the real slack (`S > 0`), with

        delta = (x_j - x_i, y_j - y_i),  q in {u_i, v_i, u_j, v_j}.

    Everything is integers: `_imul`/`_iadd` are `Z[sqrt d]` arithmetic, `_iabs` is the
    sign rule, `_icmp` is the maximum.  Nothing here is the producer's `Quad` path.

    Returns `{"contacts", "violations", "verdicts", "pair_worst", "witnesses",
    "worst", "clearance"}`: `verdicts` maps `(i, j)` to the sign of that pair's largest
    slack, `pair_worst` maps it to the exact residual, and `clearance` is the printed
    value of the worst pair's largest slack (`None` when there is no candidate pair).
    """
    n = len(centres)
    lim = 2 * scale
    d2 = (scale * scale, 0)
    contacts = violations = 0
    worst = None
    verdicts, pair_worst = {}, {}
    witnesses = []
    for i in range(n):
        for j in range(i + 1, n):
            delta = (_isub(centres[j][0], centres[i][0]),
                     _isub(centres[j][1], centres[i][1]))
            if (_abs_ge(delta[0], lim, d) or _abs_ge(delta[1], lim, d)):
                continue                    # exact prune: every half-extent < 1
            best, best_axis = None, None
            for owner, other in ((i, j), (j, i)):
                Uo, Vo = frames[other][0], frames[other][1]
                for kk, q in enumerate(frames[owner]):
                    proj = _iabs(_dot(delta, q, d), d)      # slack uses |projection|
                    w1 = _iabs(_dot(Uo, q, d), d)
                    w2 = _iabs(_dot(Vo, q, d), d)
                    need_s = _iadd(_iadd(d2, w1), w2)
                    slack_s = _isub((2 * proj[0], 2 * proj[1]), need_s)
                    if best is None or _icmp(slack_s, best, d) > 0:
                        best, best_axis = slack_s, (owner, kk, q)
            if best is None:
                continue
            sgn = EF.integral_sign(best[0], best[1], d)
            verdicts[(i, j)] = sgn
            pair_worst[(i, j)] = best
            if sgn < 0:
                violations += 1
            elif best == (0, 0):
                contacts += 1
                witnesses.append({"pair": [i, j], "owner": best_axis[0],
                                  "axis": best_axis[1],
                                  "axis_vector": [_scaled_str(best_axis[2][0], cls, scale),
                                                  _scaled_str(best_axis[2][1], cls, scale)],
                                  "gap": "0"})
            if worst is None or _icmp(best, worst, d) < 0:
                worst = best
    big = 2 * scale * scale
    return {"contacts": contacts, "violations": violations, "verdicts": verdicts,
            "pair_worst": pair_worst, "worst": worst, "witnesses": witnesses,
            "clearance": None if worst is None else _scaled_str(worst, cls, big)}


def sat_pass_reference(centres, frames, cls):
    """The `Quad` formulation of the same pass — a **witness**, never a verdict.

    This is the producer's shape (`qsqrt2.pair_axes`): multiply field elements, subtract,
    compare.  It exists so the integer pass can be checked against an independently
    written one; `cross_check` compares the two pair for pair, down to the exact value
    of each pair's largest slack, and the verifier never uses this result to decide a
    certificate.
    """
    one = F(1) if cls is None else cls(1)
    half = one * F(1, 2) if cls is None else cls(F(1, 2))
    two = F(2) if cls is None else cls(2)
    n = len(centres)
    contacts = violations = 0
    worst = None
    verdicts, pair_worst = {}, {}
    for i in range(n):
        for j in range(i + 1, n):
            if abs(centres[j][0] - centres[i][0]) >= two \
                    or abs(centres[j][1] - centres[i][1]) >= two:
                continue
            dx = centres[j][0] - centres[i][0]
            dy = centres[j][1] - centres[i][1]
            best = None
            for owner, other in ((i, j), (j, i)):
                Uo, Vo = frames[other][0], frames[other][1]
                for q in frames[owner]:
                    proj = abs(dx * q[0] + dy * q[1])
                    need = half + (abs(Uo[0] * q[0] + Uo[1] * q[1])
                                   + abs(Vo[0] * q[0] + Vo[1] * q[1])) * half
                    slack = proj - need
                    if best is None or slack > best:
                        best = slack
            if best is None:
                continue
            sgn = _sign(best)
            verdicts[(i, j)] = sgn
            pair_worst[(i, j)] = best
            if sgn < 0:
                violations += 1
            if best == 0:
                contacts += 1
            if worst is None or best < worst:
                worst = best
    return {"contacts": contacts, "violations": violations, "verdicts": verdicts,
            "pair_worst": pair_worst,
            "clearance": None if worst is None else _q(worst)}


# --------------------------------------------------------------- verification
def _scaled_sentence(centres, frames):
    """The sentence as integer components: `(scale, centres, frames)`.

    One common denominator for every coordinate and every frame component, so all the
    arithmetic downstream is in `Z[sqrt d]`.  A centre becomes a pair of field elements
    and a frame row a vector of two, which is the only structural fact the SAT pass uses.
    """
    scale = _common_den([c for p in centres for c in p]
                        + [c for rows in frames for row in rows for c in row])
    icentres = [(_to_int(x, scale), _to_int(y, scale)) for x, y in centres]
    iframes = [((_to_int(frames[k][0][0], scale), _to_int(frames[k][0][1], scale)),
                (_to_int(frames[k][1][0], scale), _to_int(frames[k][1][1], scale)))
               for k in range(len(frames))]
    return scale, icentres, iframes


def _read_sentence(cert):
    """Parse one certificate into exact values.  No inequality is decided here."""
    if not isinstance(cert, dict):
        _fail(OUTSIDE, "schema", id=None, why="a certificate must be an object")
    cid = cert.get("id")
    if not isinstance(cid, str) or not cid:
        _fail(OUTSIDE, "schema", id=cid, why="every certificate needs a string id")
    tag = cert.get("field")
    d, cls = parse_field(tag)
    cells = cert.get("cells")
    if not isinstance(cells, list) or not cells:
        _fail(OUTSIDE, "schema", id=cid, why="cells must be a non-empty list")
    n = len(cells)
    if cert.get("N") != n:
        _fail(OUTSIDE, "count", id=cid, declared=cert.get("N"), cells=n)
    L = parse_scalar(cert.get("L"), tag, f"{cid}.L")
    origin = cert.get("origin")
    if not (isinstance(origin, list) and len(origin) == 2):
        _fail(OUTSIDE, "schema", id=cid, why="origin must be [x0, y0]")
    ox = parse_scalar(origin[0], tag, f"{cid}.origin[0]")
    oy = parse_scalar(origin[1], tag, f"{cid}.origin[1]")
    centres, frames = [], []
    for k, cell in enumerate(cells):
        if not isinstance(cell, dict) or not isinstance(cell.get("r"), list) \
                or len(cell["r"]) != 4:
            _fail(OUTSIDE, "schema", id=cid, cell=k, why="a cell is {x, y, r: [4]}")
        x = parse_scalar(cell.get("x"), tag, f"{cid}.cells[{k}].x")
        y = parse_scalar(cell.get("y"), tag, f"{cid}.cells[{k}].y")
        R = [parse_scalar(v, tag, f"{cid}.cells[{k}].r") for v in cell["r"]]
        centres.append((x, y))
        frames.append(((R[0], R[2]), (R[1], R[3])))     # (u, v) rows as vectors
    return {"cid": cid, "tag": tag, "d": d, "cls": cls, "n": n, "L": L,
            "ox": ox, "oy": oy, "centres": centres, "frames": frames,
            "expected": cert.get("expected"), "family": cert.get("family")}


def verify_certificate(cert):
    """Verify one certificate, returning its exact summary (or raising `Failure`)."""
    s = _read_sentence(cert)
    cid, tag, d, cls, n = s["cid"], s["tag"], s["d"], s["cls"], s["n"]
    L, ox, oy = s["L"], s["ox"], s["oy"]
    centres, frames = s["centres"], s["frames"]
    one = F(1) if cls is None else cls(1)
    zero = F(0) if cls is None else cls(0)
    half = F(1, 2) if cls is None else cls(F(1, 2))

    # 1. every frame is a rotation: R^T R = I and det R = 1
    for k, (u, v) in enumerate(frames):
        ux, uy = u
        vx, vy = v
        if ux * ux + uy * uy != one:
            _fail(INFEASIBLE, "orthonormal", id=cid, cell=k, row="u",
                  value=_q(ux * ux + uy * uy))
        if vx * vx + vy * vy != one:
            _fail(INFEASIBLE, "orthonormal", id=cid, cell=k, row="v",
                  value=_q(vx * vx + vy * vy))
        if ux * vx + uy * vy != zero:
            _fail(INFEASIBLE, "orthonormal", id=cid, cell=k, row="u.v",
                  value=_q(ux * vx + uy * vy))
        det = ux * vy - uy * vx
        if det != one:
            _fail(INFEASIBLE, "det", id=cid, cell=k, det=_q(det),
                  why="the frame is orthogonal but not a rotation (det = -1)")

    # 2. every wall inequality, in the certificate's own box
    for k, ((x, y), (u, _v)) in enumerate(zip(centres, frames)):
        ex = (abs(u[0]) + abs(u[1])) * half
        if not (ox <= x - ex):
            _fail(INFEASIBLE, "wall", id=cid, cell=k, side="left",
                  gap=_q(x - ex - ox))
        if not (x + ex <= ox + L):
            _fail(INFEASIBLE, "wall", id=cid, cell=k, side="right",
                  gap=_q(ox + L - (x + ex)))
        if not (oy <= y - ex):
            _fail(INFEASIBLE, "wall", id=cid, cell=k, side="bottom",
                  gap=_q(y - ex - oy))
        if not (y + ex <= oy + L):
            _fail(INFEASIBLE, "wall", id=cid, cell=k, side="top",
                  gap=_q(oy + L - (y + ex)))

    # 3. the declared side is the sentence's own side
    span_x = max(x + (abs(u[0]) + abs(u[1])) * half
                 for (x, _y), (u, _v) in zip(centres, frames)) \
        - min(x - (abs(u[0]) + abs(u[1])) * half
              for (x, _y), (u, _v) in zip(centres, frames))
    span_y = max(y + (abs(u[0]) + abs(u[1])) * half
                 for (_x, y), (u, _v) in zip(centres, frames)) \
        - min(y - (abs(u[0]) + abs(u[1])) * half
              for (_x, y), (u, _v) in zip(centres, frames))
    span = span_x if span_x > span_y else span_y
    if span != L:
        _fail(OUTSIDE, "declared_side", id=cid, declared=_q(L), actual=_q(span),
              why="L must be the exact side of the sentence in this box")

    # 4. every pairwise 4-axis SAT inequality, decided on INTEGER components
    scale, icentres, iframes = _scaled_sentence(centres, frames)
    sat = sat_pass_scaled(d, icentres, iframes, scale, cls)
    if sat["violations"]:
        # the first overlap, with its own witness axis and exact gap
        for (i, j), sgn in sorted(sat["verdicts"].items()):
            if sgn < 0:
                _fail(INFEASIBLE, "sat", id=cid, pair=[i, j],
                      gap=_scaled_str(sat["pair_worst"][(i, j)], cls, 2 * scale * scale),
                      scale=scale, why="the pair overlaps on every axis")
    summary = {"id": cid, "family": s["family"], "field": tag, "N": n,
               "L": _q(L), "origin": [_q(ox), _q(oy)],
               "contacts": sat["contacts"], "violations": sat["violations"],
               "ok": sat["violations"] == 0,
               "clearance": sat["clearance"],
               "void": _q(L * L - (F(n) if cls is None else cls(n))),
               "witnesses": sat["witnesses"], "scale": scale,
               "status": "verified"}
    expected = s["expected"]
    if isinstance(expected, dict):
        for key in ("ok", "contacts", "violations"):
            if key in expected and expected[key] != summary[key]:
                _fail(OUTSIDE, "declared_summary", id=cid, key=key,
                      declared=expected[key], actual=summary[key])
        if "clearance" in expected and expected["clearance"] is not None:
            want = parse_scalar(expected["clearance"], tag, f"{cid}.expected.clearance")
            want_scaled = _to_int(want, 2 * scale * scale)
            if sat["worst"] is None or want_scaled != sat["worst"]:
                _fail(OUTSIDE, "declared_summary", id=cid, key="clearance",
                      declared=_q(want),
                      actual=None if sat["worst"] is None else sat["clearance"])
    return summary


def cross_check(doc):
    """Pair-for-pair agreement of the integer pass and the `Quad` witness.

    The two implementations are written independently (`sat_pass_scaled` on integers,
    `sat_pass_reference` on field elements) and this is where that independence is
    *tested* rather than claimed: same candidate pairs, same sign for each pair's largest
    slack, same contact and violation counts, same clearance.
    """
    out = []
    for cert in doc.get("certificates", []):
        s = _read_sentence(cert)
        centres, frames, cls = s["centres"], s["frames"], s["cls"]
        scale, icentres, iframes = _scaled_sentence(centres, frames)
        sat = sat_pass_scaled(s["d"], icentres, iframes, scale, cls)
        ref = sat_pass_reference(centres, frames, cls)
        assert sat["verdicts"] == ref["verdicts"], (s["cid"], "verdicts differ")
        assert sat["contacts"] == ref["contacts"], (s["cid"], "contacts")
        assert sat["violations"] == ref["violations"], (s["cid"], "violations")
        assert sat["clearance"] == ref["clearance"], (s["cid"], "clearance")
        # the stronger statement: both paths compute the SAME exact largest slack, not
        # just the same sign, for every candidate pair (the integer residual is S slack
        # with S = 2 D^2, so the reference value is scaled by S to compare)
        big_s = 2 * scale * scale
        for key, val in ref["pair_worst"].items():
            assert _to_int(val, big_s) == sat["pair_worst"][key], (s["cid"], key)
        out.append({"id": s["cid"], "pairs": len(sat["verdicts"]),
                    "contacts": sat["contacts"], "clearance": sat["clearance"]})
    return out


# --------------------------------------------------------------- fuzzing the passes
_POOL = {}


def _unit_pool(d):
    """Exact unit vectors of `Q(sqrt d)`, found by one small integer search.

    With `ux = (a + b r)/m`, `uy = (c + e r)/m` and `r = sqrt d`, `ux^2 + uy^2 = 1` is the
    pair of integer equations `a b + c e = 0` (the `r` part) and
    `a^2 + d b^2 + c^2 + d e^2 = m^2` (the rational part), so the unit words of a field
    can be enumerated exactly instead of hard-coded.  Only the fuzz uses this; the
    verifier's own checks never trust a generated word.
    """
    if d in _POOL:
        return _POOL[d]
    seen, out = set(), []
    for m in (1, 2, 3, 4, 5, 6, 8):
        for a in range(-4, 5):
            for b in range(-4, 5):
                if d == 0 and b:
                    continue
                for c in range(-4, 5):
                    for e in range(-4, 5):
                        if d == 0 and e:
                            continue
                        if a * b + c * e != 0:
                            continue
                        if a * a + d * b * b + c * c + d * e * e != m * m:
                            continue
                        g = gcd(gcd(gcd(abs(a), abs(b)), gcd(abs(c), abs(e))), m)
                        key = (a // g, b // g, c // g, e // g, m // g)
                        if key in seen or (a, b, c, e) == (0, 0, 0, 0):
                            continue
                        seen.add(key)
                        out.append((key[0], key[1], key[2], key[3], key[4]))
    _POOL[d] = [((F(a, m), F(b, m)), (F(c, m), F(e, m)))
                for a, b, c, e, m in out]
    return _POOL[d]


def _random_sentence(rng):
    """A random exact sentence: a field, `n` centres, and unit frames in that field.

    Centres are drawn from mixed denominators (halves, thirds, quarters, fifths) with
    random `sqrt d` parts, and a third of them are copies of an earlier centre (a
    coincidence, which is a strict overlap) or a copy pushed by a small exact offset —
    so overlapping pairs, exact contacts and separated pairs all occur, and the common
    denominator `D` is usually larger than the coordinates' own denominators.
    """
    d = rng.choice([0, 2, 5, 7])
    _, cls = parse_field("Q" if d == 0 else f"Quad({d})")
    pool = _unit_pool(d)
    if not pool:                              # cannot happen: every rung has words
        raise AssertionError(f"no unit words found in Q(sqrt {d})")
    n = rng.randint(2, 7)
    dens = rng.choice([(2,), (2, 3), (2, 3, 4), (2, 3, 4, 5), (3, 4), (4, 5)])
    grid = [F(k, m) for m in dens for k in range(0, 3 * m + 1)]
    parts = [F(0)] + [F(s, m) for m in (2, 3, 4) for s in (1, -1)]

    def scalar():
        a = rng.choice(grid)
        b = rng.choice(parts) if d else F(0)
        return cls(a, b) if cls is not None else a

    centres = []
    for _ in range(n):
        if centres and rng.random() < 1 / 3:
            x, y = centres[rng.randrange(len(centres))]
            if rng.random() < 1 / 2:
                step = F(rng.choice([F(1, 10), F(9, 10), F(1, 2), F(3, 5)]))
                if rng.random() < 1 / 2:
                    x = x + cls(step) if cls is not None else x + step
                else:
                    y = y + cls(step) if cls is not None else y + step
            centres.append((x, y))
        else:
            centres.append((scalar(), scalar()))
    frames = []
    for _ in range(n):
        (uxa, uxb), (uya, uyb) = pool[rng.randrange(len(pool))]
        if cls is None:
            u, v = (uxa, uya), (-uya, uxa)
        else:
            u = (cls(uxa, uxb), cls(uya, uyb))
            v = (cls(-uya, -uyb), cls(uxa, uxb))     # the exact quarter turn
        frames.append((u, v))
    return d, cls, centres, frames


def fuzz(count=200, seed=101):
    """Compare the integer SAT pass with the `Quad` witness on random exact sentences.

    The two passes are exercised directly rather than through `verify_certificate`, since
    a random sentence rarely has the tight `L` a certificate has to declare.  Every pair's
    exact largest slack is compared (`2 D^2` times the reference value against the integer
    residual), as are the verdict signs, the contact and violation counts and the printed
    clearance — on sentences built to include coincident centres, near-overlaps, exact
    contacts and mixed denominators.
    """
    rng = random.Random(seed)
    stats = {"sentences": 0, "pairs": 0, "contacts": 0, "overlaps": 0, "separated": 0,
             "max_den": 0, "mixed_den": 0, "mismatches": 0, "failures": []}
    for _ in range(count):
        d, cls, centres, frames = _random_sentence(rng)
        scale, icentres, iframes = _scaled_sentence(centres, frames)
        sat = sat_pass_scaled(d, icentres, iframes, scale, cls)
        ref = sat_pass_reference(centres, frames, cls)
        big = 2 * scale * scale
        stats["sentences"] += 1
        stats["pairs"] += len(sat["verdicts"])
        stats["contacts"] += sat["contacts"]
        stats["overlaps"] += sat["violations"]
        stats["separated"] += len(sat["verdicts"]) - sat["contacts"] - sat["violations"]
        stats["max_den"] = max(stats["max_den"], scale)
        if scale > 2:
            stats["mixed_den"] += 1
        if sat["verdicts"] != ref["verdicts"]:
            stats["failures"].append({"why": "verdicts", "d": d, "scale": scale})
        if sat["contacts"] != ref["contacts"] or sat["violations"] != ref["violations"]:
            stats["failures"].append({"why": "counts", "d": d, "scale": scale})
        if sat["clearance"] != ref["clearance"]:
            stats["failures"].append({"why": "clearance", "d": d, "scale": scale,
                                      "integer": sat["clearance"],
                                      "witness": ref["clearance"]})
        for key, val in ref["pair_worst"].items():
            if _to_int(val, big) != sat["pair_worst"][key]:
                stats["failures"].append({"why": "pair_value", "d": d, "scale": scale,
                                          "pair": list(key)})
    stats["mismatches"] = len(stats["failures"])
    return stats


def verify_document(doc):
    """Verify every certificate in a document; the overall verdict is the AND."""
    results = []
    if not isinstance(doc, dict) or doc.get("format") != FORMAT:
        return {"ok": False, "verified": 0, "failed": 1,
                "results": [Failure(OUTSIDE, "format",
                                    {"format": None if not isinstance(doc, dict)
                                     else doc.get("format"), "want": FORMAT}).as_dict()]}
    certs = doc.get("certificates")
    if not isinstance(certs, list) or not certs:
        return {"ok": False, "verified": 0, "failed": 1,
                "results": [Failure(OUTSIDE, "schema",
                                    {"why": "no certificates"}).as_dict()]}
    seen = set()
    for cert in certs:
        cid = cert.get("id") if isinstance(cert, dict) else None
        if cid in seen:
            results.append(Failure(OUTSIDE, "duplicate_id", {"id": cid}).as_dict())
            continue
        seen.add(cid)
        try:
            results.append({"status": "verified", "summary": verify_certificate(cert)})
        except Failure as f:
            results.append(f.as_dict())
    verified = sum(1 for r in results if r["status"] == "verified")
    return {"ok": verified == len(results), "verified": verified,
            "failed": len(results) - verified, "results": results}


# --------------------------------------------------------------- self-test
def _clone(doc):
    return json.loads(json.dumps(doc))


def _bump(raw, tag, delta):
    """`raw + delta` in the schema's own spelling (delta a Fraction)."""
    if tag == "Q":
        return str(F(raw) + delta)
    return [str(F(raw[0]) + delta), raw[1]]


def selftest(path):
    """Round-trip the document, cross-check and fuzz the SAT passes, break it ten ways."""
    with open(path) as f:
        doc = json.load(f)
    clean = verify_document(doc)
    assert clean["ok"], clean
    print(f"  the document verifies: {clean['verified']} certificate(s), 0 failures")
    agree = cross_check(doc)
    print("  the integer SAT pass and the Quad witness agree pair for pair: "
          + ", ".join(f"{a['id']} {a['pairs']}p/{a['contacts']}c" for a in agree))
    fz = fuzz(30, seed=7)
    assert fz["mismatches"] == 0, fz["failures"][:3]
    assert fz["overlaps"] > 0 and fz["max_den"] > 4, fz
    print(f"  fuzz: {fz['sentences']} random exact sentences, {fz['pairs']} candidate "
          f"pairs ({fz['contacts']} contacts, {fz['overlaps']} overlaps, "
          f"{fz['separated']} separated), denominators up to {fz['max_den']}: "
          "integer pass == Quad witness on every pair")
    checks = []

    def expect(mut, kind, check, label):
        bad = verify_document(mut)
        assert not bad["ok"], label
        first = [r for r in bad["results"] if r["status"] != "verified"][0]
        assert first["kind"] == kind and first["check"] == check, (label, first)
        checks.append(label)
        return first

    cid = doc["certificates"][0]["id"]

    # 1. a decimal spelling is a projection, not a value
    mut = _clone(doc)
    mut["certificates"][0]["cells"][0]["x"] = "0.5"
    expect(mut, OUTSIDE, "number_format", "decimal string")
    # 2. a reflection: orthogonal, det = -1
    mut = _clone(doc)
    c0 = mut["certificates"][0]

    def _neg(v):
        return str(-F(v)) if c0["field"] == "Q" else [str(-F(v[0])), str(-F(v[1]))]

    c0["cells"][0]["r"] = [c0["cells"][0]["r"][0], _neg(c0["cells"][0]["r"][1]),
                            c0["cells"][0]["r"][2], _neg(c0["cells"][0]["r"][3])]
    expect(mut, INFEASIBLE, "det", "reflection frame")
    # 3. a frame that is not orthonormal
    mut = _clone(doc)
    c = mut["certificates"][0]
    if c["field"] == "Q":
        c["cells"][0]["r"][0] = "2"
    else:
        c["cells"][0]["r"][0] = ["2", "0"]
    expect(mut, INFEASIBLE, "orthonormal", "non-unit frame")
    # 4. a centre pushed through the wall
    mut = _clone(doc)
    c = mut["certificates"][0]
    c["cells"][0]["x"] = _bump(c["cells"][0]["x"], c["field"], F(2))
    expect(mut, INFEASIBLE, "wall", "centre pushed through the wall")
    # 5. an L that is not the sentence's side
    mut = _clone(doc)
    c = mut["certificates"][0]
    c["L"] = _bump(c["L"], c["field"], F(1))
    expect(mut, OUTSIDE, "declared_side", "loose declared side")
    # 6. a document that does not declare the format
    doc2 = _clone(doc)
    doc2["format"] = "galois-certificate/0"
    expect(doc2, OUTSIDE, "format", "wrong format tag")
    # 7. a duplicated id
    mut = _clone(doc)
    mut["certificates"].append(_clone(mut["certificates"][0]))
    expect(mut, OUTSIDE, "duplicate_id", "duplicate id")
    # 8. a wrong declared count
    mut = _clone(doc)
    mut["certificates"][0]["N"] = mut["certificates"][0]["N"] + 1
    expect(mut, OUTSIDE, "count", "declared count")
    # 9. a declared summary that the object does not have
    mut = _clone(doc)
    mut["certificates"][0]["expected"]["contacts"] += 1
    expect(mut, OUTSIDE, "declared_summary", "declared summary")
    # 10. a genuine SAT overlap, in an otherwise well-formed sentence: inside its box,
    # with a tight declared side, so it survives every check before the SAT pass and the
    # integer pass has to report the violation with its own exact gap.  c0 covers
    # [0,1]^2, c1 covers [9/10, 19/10] x [0,1] (overlap 1/10 in x), c2 covers
    # [1,2] x [1,2] (a contact with both), the span is exactly [0,2]^2, and L = 2.
    mut = _clone(doc)
    mut["certificates"].append({
        "id": "overlap_1_10", "family": "Overlap", "field": "Q", "N": 3,
        "L": "2", "origin": ["0", "0"],
        "cells": [{"x": "1/2", "y": "1/2", "r": ["1", "0", "0", "1"]},
                  {"x": "7/5", "y": "1/2", "r": ["1", "0", "0", "1"]},
                  {"x": "3/2", "y": "3/2", "r": ["1", "0", "0", "1"]}],
        "expected": {"ok": True, "contacts": 2, "violations": 0, "clearance": "0"}})
    first = expect(mut, INFEASIBLE, "sat", "genuine SAT overlap")
    assert first["detail"]["pair"] == [0, 1], first
    assert first["detail"]["gap"] == "-1/10", first
    # the same sentence at a different rung reports the same overlap in that field's
    # own coordinates, so the gap is not an artefact of one scale or one tag
    mut = _clone(doc)
    mut["certificates"].append({
        "id": "overlap_1_10_quad2", "family": "Overlap", "field": "Quad(2)", "N": 3,
        "L": ["2", "0"], "origin": [["0", "0"], ["0", "0"]],
        "cells": [{"x": ["1/2", "0"], "y": ["1/2", "0"],
                   "r": [["1", "0"], ["0", "0"], ["0", "0"], ["1", "0"]]},
                  {"x": ["7/5", "0"], "y": ["1/2", "0"],
                   "r": [["1", "0"], ["0", "0"], ["0", "0"], ["1", "0"]]},
                  {"x": ["3/2", "0"], "y": ["3/2", "0"],
                   "r": [["1", "0"], ["0", "0"], ["0", "0"], ["1", "0"]]}],
        "expected": {"ok": True, "contacts": 2, "violations": 0, "clearance": "0"}})
    first = expect(mut, INFEASIBLE, "sat", "genuine SAT overlap (Quad(2))")
    assert first["detail"]["gap"] == "-1/10", first
    print(f"  {len(checks)} mutations refused, each at its own check: "
          + ", ".join(checks))
    print(f"  (certificate under test: {cid}; the untouched document still verifies)")
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default = os.path.join(here, "workspace/push/galois_certificates.json")
    want_selftest = "--selftest" in argv
    want_fuzz = any(a.startswith("--fuzz") for a in argv)
    quiet = "--quiet" in argv
    argv = [a for a in argv if not a.startswith("--")]
    if want_fuzz:
        count = int(argv[0]) if argv and argv[0].isdigit() else 200
        seed = int(argv[1]) if len(argv) > 1 and argv[1].lstrip("-").isdigit() else 101
        fz = fuzz(count, seed)
        print(f"fuzz: {fz['sentences']} random exact sentences (seed {seed}), "
              f"{fz['pairs']} candidate pairs, {fz['contacts']} contacts, "
              f"{fz['overlaps']} overlaps, {fz['separated']} separated")
        print(f"      mixed denominators: {fz['mixed_den']} sentences above 2 "
              f"(max {fz['max_den']})")
        print(f"      mismatches between the integer pass and the Quad witness: "
              f"{fz['mismatches']}")
        for bad in fz["failures"][:5]:
            print(f"      MISMATCH {bad}")
        return 0 if fz["mismatches"] == 0 else 1
    path = argv[0] if argv else default
    if want_selftest:
        print(f"verifier selftest on {os.path.relpath(path, here)}")
        return selftest(path)
    with open(path) as f:
        doc = json.load(f)
    res = verify_document(doc)
    if not quiet:
        for r in res["results"]:
            if r["status"] == "verified":
                s = r["summary"]
                print(f"  verified {s['id']}: {s['field']}, N = {s['N']}, L = {s['L']}, "
                      f"contacts = {s['contacts']}, clearance = {s['clearance']}, "
                      f"void = {s['void']}")
            else:
                print(f"  FAILED {r['detail'].get('id')}: {r['kind']} / {r['check']}: "
                      f"{r['detail']}")
    print(f"  {res['verified']} verified, {res['failed']} failed "
          f"({os.path.relpath(path, here)})")
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
