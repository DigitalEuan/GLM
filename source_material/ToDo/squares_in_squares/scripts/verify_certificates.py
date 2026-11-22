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
`cross_check`/`--selftest` as an independent witness — it never decides anything.

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
    python3 scripts/verify_certificates.py --selftest      # mutations + cross-check
"""
from __future__ import annotations

import json
import os
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
    return {"contacts": contacts, "violations": violations, "verdicts": verdicts,
            "pair_worst": pair_worst, "worst": worst, "witnesses": witnesses,
            "clearance": None if worst is None else _scaled_str(worst, cls, scale)}


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
                      gap=_scaled_str(sat["pair_worst"][(i, j)], cls, scale),
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
            want_scaled = _to_int(want, scale)
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
    """Round-trip the document, cross-check the two SAT passes, try to break it nine ways."""
    with open(path) as f:
        doc = json.load(f)
    clean = verify_document(doc)
    assert clean["ok"], clean
    print(f"  the document verifies: {clean['verified']} certificate(s), 0 failures")
    agree = cross_check(doc)
    print("  the integer SAT pass and the Quad witness agree pair for pair: "
          + ", ".join(f"{a['id']} {a['pairs']}p/{a['contacts']}c" for a in agree))
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
    print(f"  {len(checks)} mutations refused, each at its own check: "
          + ", ".join(checks))
    print(f"  (certificate under test: {cid}; the untouched document still verifies)")
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default = os.path.join(here, "workspace/push/galois_certificates.json")
    want_selftest = "--selftest" in argv
    quiet = "--quiet" in argv
    argv = [a for a in argv if not a.startswith("--")]
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
