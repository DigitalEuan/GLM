#!/usr/bin/env python3
r"""pub_bounds_check.py — machine-check the hand-transcribed published bounds.

Run 137 embedded the published frontier for `n = 1..100` in `glm_plan.PUB` by
reading The Squares Project's 100-packing PDF, and quoted a certified room of
`1.14087` off it.  Hand transcription is exactly the kind of step that is wrong
once in a hundred numbers, so this instrument re-reads the same project's
machine-readable frontier table (`frontier.html`, saved verbatim to
`workspace/push/pub_frontier_20261020.html`) and diffs it against `PUB`.

The comparison is `Decimal` on both sides — the published values are decimal
strings in the source's `data-value` attributes, so there is no float rounding in
the verdict.  Every diff is reported with the source and the transcribed value;
the room is recomputed from the *source* numbers, and that is the figure to
quote.

Source of record: https://jlevy.github.io/squares/frontier.html (fetched
2026-11-25).  `PUB` was transcribed from the *PDF edition* (v0.7.0, 23 October
2026), so a diff against the live table can be one of two very different things:

  * **transcription** — `PUB` disagrees with the PDF edition (a reading error);
  * **drift** — `PUB` agrees with the PDF edition and the survey has moved.

The PDF edition is saved (`pub_frontier100_20261020.pdf`) with its extracted text
(`...txt`), so the classification is machine-checked, not asserted: the text is
parsed and compared in `Decimal` against `PUB` exactly as the live table is.  The
room is always recomputed from the *live* numbers, so it is the same figure
either way.

    python3 scripts/pub_bounds_check.py
    python3 scripts/pub_bounds_check.py --selftest
"""
from __future__ import annotations

import json
import os
import re
import sys
from decimal import Decimal, getcontext

getcontext().prec = 40

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import glm_plan as GP                  # noqa: E402
import sqscore as SQ                   # noqa: E402

HTML = os.path.join(ROOT, "workspace/push/pub_frontier_20261020.html")
PDF_TXT = os.path.join(ROOT, "workspace/push/pub_frontier100_20261020.txt")
PDF_SHA256 = "78677612ca2987431e0b31bc5cf02df9e5e92113b3b514e1addaa6259523a703"
PDF_EDITION = "v0.7.0, 23 October 2026"
OUT = os.path.join(ROOT, "workspace/push/pub_bounds_check.json")
TOL = Decimal("5e-5")      # data-value is sometimes rounded to 4 decimals


def parse(html: str) -> dict:
    """`{n: {status, ub, verified_ub, reported_ub, lb, gap}}` from the table."""
    out = {}
    for m in re.finditer(r'<tr id="n-(\d+)".*?</tr>', html, re.S):
        n = int(m.group(1))
        row = m.group(0)
        tds = re.findall(r"<td[^>]*>.*?</td>", row, re.S)
        if len(tds) < 7:
            continue
        nums = []
        for td in tds:
            v = re.search(r'data-value="([^"]*)"', td)
            if v:
                try:
                    nums.append(Decimal(v.group(1)))
                except Exception:
                    pass
        # `data-status` marks the case record (a proof of *some* bound); the
        # optimal badge is what "proved optimal" means in this survey.
        proved = 'aria-label="optimal"' in row
        recent = "recent result" in row
        if len(nums) < 5:
            continue
        out[n] = {"status": "proved_optimal" if proved else "open",
                  "recent": recent,
                  "ub": nums[2], "lb": nums[-2], "gap": nums[-1],
                  "verified_ub": nums[3] if len(nums) > 3 else None}
    return out


def load_pdf_table(path: str = PDF_TXT) -> dict:
    """`{(n, 'ub'|'lb'): Decimal}` from the PDF edition's extracted text."""
    txt = open(path, encoding="utf-8", errors="replace").read()
    out = {}
    for m in re.finditer(r"s\s*\(\s*(\d+)\s*\)\s*([≤≥=])\s*([0-9]+(?:\.[0-9]+)?)", txt):
        n, rel, val = int(m.group(1)), m.group(2), Decimal(m.group(3))
        if rel in ("≤", "="):
            out.setdefault((n, "ub"), val)
        if rel in ("≥", "="):
            out.setdefault((n, "lb"), val)
    return out


def check(src: dict | None = None) -> dict:
    html = open(HTML, encoding="utf-8", errors="replace").read()
    src = src or parse(html)
    pdf_table = load_pdf_table()
    missing = sorted(set(range(1, 101)) - set(src))
    rows_by_n = GP.load_rows()
    diffs = []
    for n in sorted(set(GP.PUB) & set(src)):
        ub_t, lb_t = GP.PUB[n]
        s = src[n]
        du = Decimal(str(ub_t)) - s["ub"]
        dl = Decimal(str(lb_t)) - s["lb"]
        if abs(du) > TOL or abs(dl) > TOL:
            field = "ub" if abs(du) > TOL else "lb"
            pdf = pdf_table.get((n, field))
            diffs.append({"n": n, "field": field,
                          "transcribed": str(ub_t if field == "ub" else lb_t),
                          "pdf": None if pdf is None else str(pdf),
                          "source": str(s["ub"] if field == "ub" else s["lb"]),
                          "delta": str(du if field == "ub" else dl),
                          "kind": ("transcription" if pdf is None
                                   or Decimal(str(ub_t if field == "ub" else lb_t)) != pdf
                                   else "drift"),
                          "recent": bool(s.get("recent"))})
    # room from the SOURCE numbers, Decimal all the way
    room = Decimal(0)
    rows = 0
    for n in sorted(src):
        if n > 100:
            continue
        L = Decimal(repr(SQ.extent(rows_by_n[n])))
        if L > src[n]["lb"] + TOL:
            room += (L - src[n]["lb"]) / Decimal(n).sqrt()
            rows += 1
    proved = sorted(n for n in src if src[n]["status"] == "proved_optimal")
    drift = [d for d in diffs if d["kind"] == "drift"]
    trans = [d for d in diffs if d["kind"] == "transcription"]
    return {"source": "jlevy.github.io/squares/frontier.html (fetched 2026-11-25)",
            "pdf_edition": PDF_EDITION,
            "source_file": os.path.relpath(HTML, ROOT),
            "rows_parsed": len(src), "missing_1_100": missing,
            "diffs": diffs, "n_diffs": len(diffs),
            "n_drift": len(drift), "n_transcription": len(trans),
            "n_drift_recent": sum(1 for d in drift if d["recent"]),
            "transcription_diffs": trans,
            "room_source": str(room), "room_rows": rows,
            "room_transcribed": "1.14087", "proved_rows": proved,
            "verified_table": {str(n): {"ub": str(v["ub"]), "lb": str(v["lb"]),
                                        "status": v["status"]}
                               for n, v in src.items()}}


def selftest() -> int:
    """Three controls: the parser, the diff machinery, and the source's counts."""
    html = open(HTML, encoding="utf-8", errors="replace").read()
    src = parse(html)
    assert len(src) >= 100, len(src)
    # 1. spot values that are also proved in the literature, read from source
    assert src[5]["ub"] == Decimal("2.70710678118654"), src[5]
    assert src[6]["ub"] == Decimal("3"), src[6]
    assert src[6]["status"] == "proved_optimal", src[6]["status"]
    print(f"  1. parser: {len(src)} rows; s(5) = {src[5]['ub']}, "
          f"s(6) = {src[6]['ub']} ({src[6]['status']})")

    # 2. the diff machinery catches a planted transcription error
    planted = {k: dict(v) for k, v in src.items()}
    planted[12]["lb"] = Decimal("3.900000")
    r = check(planted)
    assert any(d["n"] == 12 and d["field"] == "lb" for d in r["diffs"]), r["diffs"][:3]
    print(f"  2. planted error at n=12 caught: "
          f"{[d for d in r['diffs'] if d['n'] == 12]}")

    # 3. the proved set is the 45 the source marks, including row 6
    r = check(src)
    assert 6 in r["proved_rows"] and 12 not in r["proved_rows"], r["proved_rows"][:5]
    # the survey dates 2026-10-20 and marks 45 proved rows within 1..100; the
    # live table is newer and marks 49 (rows 44, 76, 95, 96 prove after the PDF)
    n100 = [n for n in r["proved_rows"] if n <= 100]
    assert len(n100) == 49, n100
    print(f"  3. source marks {len(n100)} proved-optimal rows in 1..100 "
          f"(PDF 2026-10-20: 45; 44, 76, 95, 96 proved since), row 6 in, row 12 not")
    # 4. the classification: PUB is faithful to its own PDF edition, so every
    #    diff against the live table is drift -- and the live table marks every
    #    one of those rows as a recent result.
    import hashlib
    pdf_path = PDF_TXT.replace(".txt", ".pdf")
    got = hashlib.sha256(open(pdf_path, "rb").read()).hexdigest()
    assert got == PDF_SHA256, got
    pdf_table = load_pdf_table()
    assert len(pdf_table) >= 190, len(pdf_table)
    assert pdf_table[(12, "lb")] == Decimal("3.971500")
    assert pdf_table[(37, "lb")] == Decimal("6.440000")
    assert pdf_table[(90, "ub")] == Decimal("10")
    r4 = check(src)
    assert r4["n_transcription"] == 0, r4["transcription_diffs"]
    assert r4["n_drift"] == r4["n_diffs"], (r4["n_drift"], r4["n_diffs"])
    assert r4["n_drift_recent"] == r4["n_drift"], r4["n_drift_recent"]
    print(f"  4. PDF edition {PDF_EDITION} (sha256 {got[:12]}): PUB agrees with it "
          f"on all {r4['n_diffs']} diff rows -> {r4['n_transcription']} transcription "
          f"errors, {r4['n_drift']} survey drift, all {r4['n_drift_recent']} marked "
          f"recent by the live table")
    print("  selftest OK (4 controls)")
    return 0


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        return selftest()
    r = check()
    with open(OUT, "w") as f:
        json.dump(r, f, indent=1, default=str)
    print(f"source: {r['source']}")
    print(f"rows parsed: {r['rows_parsed']}; missing from 1..100: "
          f"{r['missing_1_100'] or 'none'}")
    print(f"diffs: {r['n_diffs']} ({r['n_transcription']} transcription, "
          f"{r['n_drift']} survey drift; {r['n_drift_recent']} of the drift rows "
          f"are marked 'recent result' by the live table)")
    for d in r["diffs"]:
        print(f"   n={d['n']:>3} {d['field']}: PDF {d['pdf']} | PUB "
              f"{d['transcribed']} | live {d['source']} ({d['kind']}, "
              f"recent={d['recent']}, delta {d['delta']})")
    print(f"PDF edition: {r['pdf_edition']}")
    print(f"room to the source lower bounds: {Decimal(r['room_source']):.5f} "
          f"over {r['room_rows']} rows (transcribed: {r['room_transcribed']})")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
