#!/usr/bin/env python3
r"""verify_certificates.py — the serialized certificate verifier (run 101).

A standalone, zero-float reader for `workspace/push/galois_certificates.json`.  It
reconstructs every sentence **from the file alone** and decides it exactly:

  * every scalar is parsed as an exact field element (`Q` or `Quad(d)`), and a decimal
    spelling is refused by the parser — a decimal is a display projection, not a value;
  * every cell's rotation matrix is checked (`R^T R = I` and `det R = 1`);
  * every wall inequality is checked in the certificate's own container box;
  * every pairwise 4-axis SAT inequality is checked, recording the witness axis and the
    exact gap, with `>= 0` accepted at clearance 0;
  * the declared summary (N, L, contacts, clearance) is recomputed and compared.

The first exact failed inequality is reported, distinguishing the two questions a
certificate can fail to answer:

  kind = "infeasible"             the object is representable and an inequality is false
  kind = "outside_representation" the file does not represent an exact sentence at all
                                  (decimal string, wrong scalar shape, unknown field tag,
                                   duplicate id, a declared L that is not the paragraph's
                                   own side, a declared summary the object does not have)

Usage:
    python3 scripts/verify_certificates.py                 # default document
    python3 scripts/verify_certificates.py path/to.json --quiet
    python3 scripts/verify_certificates.py --selftest      # mutation tests (needs the doc)
"""
from __future__ import annotations

import json
import os
import re
import sys
from fractions import Fraction as F

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


def _sign(z):
    """Exact sign of a Fraction or a field element."""
    return (z > 0) - (z < 0)


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


# --------------------------------------------------------------- verification
def verify_certificate(cert):
    """Verify one certificate, returning its exact summary (or raising `Failure`)."""
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
    one = F(1) if cls is None else cls(1)
    zero = F(0) if cls is None else cls(0)
    half = F(1, 2) if cls is None else cls(F(1, 2))

    centres, frames = [], []
    for k, cell in enumerate(cells):
        if not isinstance(cell, dict) or not isinstance(cell.get("r"), list) \
                or len(cell["r"]) != 4:
            _fail(OUTSIDE, "schema", id=cid, cell=k, why="a cell is {x, y, r: [4]}")
        x = parse_scalar(cell.get("x"), tag, f"{cid}.cells[{k}].x")
        y = parse_scalar(cell.get("y"), tag, f"{cid}.cells[{k}].y")
        R = [parse_scalar(v, tag, f"{cid}.cells[{k}].r") for v in cell["r"]]
        centres.append((x, y))
        frames.append(R)

    # 1. every frame is a rotation: R^T R = I and det R = 1
    for k, (ux, vx, uy, vy) in enumerate(frames):
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
    for k, ((x, y), R) in enumerate(zip(centres, frames)):
        ex = (abs(R[0]) + abs(R[2])) * half
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
    span_x = max(x + (abs(R[0]) + abs(R[2])) * half for (x, _y), R in zip(centres, frames)) \
        - min(x - (abs(R[0]) + abs(R[2])) * half for (x, _y), R in zip(centres, frames))
    span_y = max(y + (abs(R[0]) + abs(R[2])) * half for (_x, y), R in zip(centres, frames)) \
        - min(y - (abs(R[0]) + abs(R[2])) * half for (_x, y), R in zip(centres, frames))
    span = span_x if span_x > span_y else span_y
    if span != L:
        _fail(OUTSIDE, "declared_side", id=cid, declared=_q(L), actual=_q(span),
              why="L must be the exact side of the sentence in this box")

    # 4. every pairwise 4-axis SAT inequality, with its witness
    two = F(2) if cls is None else cls(2)
    contacts, violations, worst = 0, 0, None
    witnesses = []
    for i in range(n):
        xi, yi = centres[i]
        for j in range(i + 1, n):
            if abs(centres[j][0] - xi) >= two or abs(centres[j][1] - yi) >= two:
                continue                    # exact prune: extent <= sqrt2/2 < 1
            dx = centres[j][0] - xi
            dy = centres[j][1] - yi
            best, axis = None, None
            for owner, other in ((i, j), (j, i)):
                R = frames[owner]
                Ro = frames[other]
                for kk, (qx, qy) in enumerate(((R[0], R[2]), (R[1], R[3]))):
                    proj = abs(dx * qx + dy * qy)
                    need = half + (abs(Ro[0] * qx + Ro[2] * qy)
                                   + abs(Ro[1] * qx + Ro[3] * qy)) * half
                    slack = proj - need
                    if best is None or slack > best:
                        best, axis = slack, (owner, kk, (qx, qy))
            if best is None:
                continue
            if _sign(best) < 0:
                _fail(INFEASIBLE, "sat", id=cid, pair=[i, j],
                      axis=_q(axis[2][0]) + ", " + _q(axis[2][1]),
                      gap=_q(best), owner=axis[0],
                      why="the pair overlaps on every axis")
            if best == 0:
                contacts += 1
                witnesses.append({"pair": [i, j], "owner": axis[0], "axis": axis[1],
                                  "axis_vector": [_q(axis[2][0]), _q(axis[2][1])],
                                  "gap": "0"})
            if worst is None or best < worst:
                worst = best
    summary = {"id": cid, "family": cert.get("family"), "field": tag, "N": n,
               "L": _q(L), "origin": [_q(ox), _q(oy)], "contacts": contacts,
               "violations": violations, "ok": violations == 0,
               "clearance": None if worst is None else _q(worst),
               "void": _q(L * L - (F(n) if cls is None else cls(n))),
               "witnesses": witnesses,
               "status": "verified"}
    expected = cert.get("expected")
    if isinstance(expected, dict):
        for key in ("ok", "contacts", "violations"):
            if key in expected and expected[key] != summary[key]:
                _fail(OUTSIDE, "declared_summary", id=cid, key=key,
                      declared=expected[key], actual=summary[key])
        if "clearance" in expected and expected["clearance"] is not None:
            want = parse_scalar(expected["clearance"], tag, f"{cid}.expected.clearance")
            if worst is None or want != worst:
                _fail(OUTSIDE, "declared_summary", id=cid, key="clearance",
                      declared=_q(want), actual=None if worst is None else _q(worst))
    return summary


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
    """Round-trip the document, then try to break it eight ways."""
    with open(path) as f:
        doc = json.load(f)
    clean = verify_document(doc)
    assert clean["ok"], clean
    print(f"  the document verifies: {clean['verified']} certificate(s), 0 failures")
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
