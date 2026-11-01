#!/usr/bin/env python3
"""Round 45: run engines v15, v16 and v17 on Rule 30 and score them against a ground truth
fixed BEFORE v17 was written (the TRUTH table of Round 44, `needs_rule30.py`).

    python3 run_round45.py            # full ranges (about 2-3 minutes)
    python3 run_round45.py --quick    # smaller ranges (about 1-2 minutes)

Scoring (as in Round 44):
  right      the final status asserts the true verdict, or asserts nothing about an open question
  wrong      it asserts the opposite of a settled verdict
  overclaim  it asserts True/False about a question whose truth is open / not a claim
  abstain    it asserts nothing about a settled question

Status -> assertion:
  v15/v16  survives, law-holds, prediction-confirmed -> True; refuted* -> False; others -> none
  v17      proved, verified-exact -> True; refuted* -> False; others -> none
Writes out/round45_results.{json,md}.
"""

from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from needs_rule30 import TRUTH  # noqa: E402  (fixed in Round 44, never read by any engine)
from hypothesis_engine_v15 import EngineV15  # noqa: E402
from hypothesis_engine_v16 import EngineV16  # noqa: E402
import hypothesis_engine_v17 as v17  # noqa: E402
from hypothesis_engine_v17 import EngineV17, answer_of, write_outputs  # noqa: E402

SCORED = sorted(k for k in TRUTH if k.startswith("H") and k[1:].isdigit())


def answer_old(status: str):
    if status in ("survives", "law-holds", "prediction-confirmed"):
        return True
    if status.startswith("refuted"):
        return False
    return None


def score(answers: dict) -> dict:
    c = Counter()
    rows = []
    for hid in SCORED:
        t = TRUTH[hid][0]
        a = answers.get(hid, None)
        if t is None:
            k = "right" if a is None else "overclaim"
        elif a is None:
            k = "abstain"
        else:
            k = "right" if a == t else "wrong"
        c[k] += 1
        rows.append((hid, t, a, k))
    return {"counts": dict(c), "rows": rows}


def run_engine(cls, quick, **kw):
    eng = cls(quick=quick, log=lambda *a, **k: None, **kw)
    t0 = time.time()
    rep = eng.run()
    return eng, rep, time.time() - t0


def main():
    quick = "--quick" in sys.argv
    out = HERE / "out"
    out.mkdir(exist_ok=True)
    results, keys = {}, {}
    for label, cls, kw, amap in [
        ("v15", EngineV15, {}, answer_old),
        ("v16", EngineV16, {}, answer_old),
        ("v17 without ledger gate", EngineV17, {"use_ledger": False}, answer_of),
        ("v17 automatic claim classes", EngineV17, {"use_ledger": True}, answer_of),
        ("v17", EngineV17, {"use_ledger": True}, answer_of),
    ]:
        print(f"running {label} ...", flush=True)
        v17.USE_REGISTRY = (label != "v17 automatic claim classes")
        eng, rep, dt = run_engine(cls, quick, **kw)
        answers = {h.hid: amap(h.status) for h in eng.hyps}
        keys[label] = {h.hid: h.key for h in eng.hyps}
        s = score(answers)
        results[label] = {"seconds": round(dt, 1), "score": s["counts"], "rows": s["rows"],
                          "statuses": {h.hid: h.status for h in eng.hyps},
                          "n_hypotheses": len(eng.hyps)}
        if isinstance(eng, EngineV17) and label != "v17 automatic claim classes":
            stem = "engine_v17" + ("_quick" if quick else "") + ("" if kw["use_ledger"] else "_noledger")
            write_outputs(rep, out, stem)
            results[label]["consistency"] = rep["v17_consistency"]
            results[label]["conflicts"] = rep["conflicts"]
            results[label]["shape_violations"] = rep["shape_violations"]
        print(f"  {label}: {s['counts']}  ({dt:.1f}s)")

    # the hypothesis ids must denote the same statements in every engine
    base = keys["v16"]
    misaligned = [(lab, hid) for lab, km in keys.items() for hid in SCORED
                  if km.get(hid) != base.get(hid)]
    results["_alignment_ok"] = not misaligned
    results["_misaligned"] = misaligned

    (out / ("round45_results" + ("_quick" if quick else "") + ".json")).write_text(
        json.dumps(results, indent=1, default=str, ensure_ascii=False))
    labels = ["v15", "v16", "v17 without ledger gate", "v17 automatic claim classes", "v17"]
    L = ["# Round 45 — engines v15, v16, v17 scored against the Round 44 ground truth", "",
         f"quick = {quick}; {len(SCORED)} statements with a ground truth fixed before v17 existed "
         f"(Round 44 `TRUTH`); ids aligned across engines: {not misaligned}", "",
         "| engine | right | wrong | overclaim | abstain | seconds |", "|---|---|---|---|---|---|"]
    for lab in labels:
        c = results[lab]["score"]
        L.append(f"| {lab} | {c.get('right', 0)} | {c.get('wrong', 0)} | {c.get('overclaim', 0)} | "
                 f"{c.get('abstain', 0)} | {results[lab]['seconds']} |")
    L += ["", "| id | key | truth (source) | " + " | ".join(labels) + " |",
          "|---|---|---|" + "---|" * len(labels)]
    for hid in SCORED:
        t, src = TRUTH[hid]
        cells = []
        for lab in labels:
            row = next(r for r in results[lab]["rows"] if r[0] == hid)
            cells.append(f"{results[lab]['statuses'].get(hid, '—')} ({row[3]})")
        L.append(f"| {hid} | `{base.get(hid)}` | {t} ({src[:70]}) | " + " | ".join(cells) + " |")
    L += ["", f"v17 dialogue consistency: {results['v17'].get('consistency')}",
          f"v17 conflicts with Lean: {results['v17'].get('conflicts') or 'none'}",
          f"v17 layer-shape violations: {results['v17'].get('shape_violations') or 'none'}"]
    (out / ("round45_results" + ("_quick" if quick else "") + ".md")).write_text("\n".join(L) + "\n")
    print("\n".join(L[:12]))


if __name__ == "__main__":
    main()
