#!/usr/bin/env python3
r"""record_guard.py — the record guard (`19-COLLECTION-AND-REVIEW.md` §7).

`sqscore.guard()` stops a *wrong* score from being printed. Nothing stopped a
*stale* score from being read as current: ten documents quote a total from
before Run 47, and `00-OVERVIEW.md` called 22.642386651 canonical for nine runs.

Two fatal rules:

  R1 currency   a line that asserts currency (current / canonical / delivered /
                latest / "the score is" / "scores") and quotes a total must
                quote the delivered one. The test is the prefix 22.21742, so
                every rounding of 22.217428576 passes and 22.218056945 does not.
  R2 headline   a total quoted in a document's title block (first 10 lines)
                must be the current one, unless the document is declared
                historical in HISTORICAL.
  R3 beats      a line that counts the beats — "554 / 1000" — must quote
                `sqscore`'s own count when it is a claim: a table row, a
                currency sentence, a line naming the current score, or any line
                inside a **current-state section** (a heading naming the
                canonical/current/delivered state, as `RECONCILIATION.md`'s
                "## Canonical state" does).  Fenced code is not prose and is
                skipped.  R1/R2 cannot see any of this: their scan is anchored
                to score literals (`2x.xxxxxx`), so "553 / 1000" was never even
                counted as a claim when row 90 moved it to 554.

A line opts out explicitly by carrying one of TAGS ("historical", "stale",
"superseded", "withdrawn"): that is the convention the prose already uses. A
document opts out of R2 by being listed in HISTORICAL — for documents whose job
is to record an older state.

Two notes, never fatal: `workspace/push/table.json` if it disagrees with the
delivered table (it must never be written back), and the highest run number in
`04-RUN-LOG.md` versus the ledgers.

    python3 scripts/record_guard.py        # exit 1 on a violation

Nothing here writes anything.
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import sqscore                  # noqa: E402

CANON = "22.21742"              # prefix of 22.217428576 and every rounding of it
SCORE_RE = re.compile(r"(?<![\d.])2[0-9]\.\d{5,9}(?![\d])")
#: R3: a beat fraction, and the vocabulary that makes a line a *claim* about it
BEAT_RE = re.compile(r"(?<![\d.])(\d{3})\s*/\s*1000(?![\d])")
BEAT_LABEL_RE = re.compile(r"(beats?\b|beating\b|beat grid)", re.I)
#: a heading that says "this section states the current system" (R3's section rule)
CURRENT_HEAD_RE = re.compile(r"(canonical|current|delivered|results?|status|frontier|state)\b", re.I)

def section_current(heading: str) -> bool:
    """True iff a markdown heading declares a current-state section."""
    return bool(heading) and bool(CURRENT_HEAD_RE.search(heading))
#: a line is a *claim about the current state* only if it uses this vocabulary.
#: "Score history: A -> B -> C" and run-log notes are history, not claims; they
#: are inventoried below rather than failed.
CURRENCY_RE = re.compile(
    r"(\bcurrent (?:canonical|score|state)\b|\bcanonical score\b|"
    r"\bsubmission score\b|\bdelivered (?:table|frontier|system)\b|"
    r"\bthe score is\b|\blatest score\b|\bstands at\b)", re.I)
TAGS = ("historical", "stale", "superseded", "withdrawn", "at that time")
HEAD_LINES = 10
#: documents whose subject is an older state (exempt from R2 only)
HISTORICAL: tuple = ()


def violating(line: str, lit: str) -> bool:
    low = line.lower()
    if any(t in low for t in TAGS):
        return False
    return not lit.startswith(CANON)


def stale_paragraphs(lines) -> set:
    """Line numbers that sit in a paragraph quoting a superseded score.

    A run-log entry can put its score at the end of one line and its beat count at
    the start of the next; the paragraph, not the line, is what makes it history.
    """
    out, para = set(), []
    for i, line in enumerate(lines, 1):
        if not line.strip():
            para = []
            continue
        if any(stale_score_quoted(p) for p in para[-4:]):
            out.add(i)
        para.append(line)
    return out


def stale_score_quoted(line: str) -> bool:
    """True iff the line names a score and none of them is the current one.

    A beat count printed next to a *superseded* score is describing that
    superseded state (the run-38 quote in `09-CASCADE.md`), not claiming the
    current one; the same convention R1 already uses for history lines.
    """
    lits = SCORE_RE.findall(line)
    return bool(lits) and not any(l.startswith(CANON) for l in lits)


def main() -> int:
    s = sqscore.guard(quiet=True)
    cur = f"{s['score']:.9f}"
    docs = sorted(glob.glob(os.path.join(ROOT, "*.md")))
    bad: list = []
    hist: list = []
    claims = 0

    for path in docs:
        name = os.path.basename(path)
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
        for i, line in enumerate(lines, 1):
            for m in SCORE_RE.finditer(line):
                lit = m.group(0)
                claims += 1
                if any(l.startswith(CANON) for l in SCORE_RE.findall(line)):
                    continue          # a history line that ends at current
                if not violating(line, lit):
                    continue
                if i <= HEAD_LINES and name not in HISTORICAL:
                    kind = "R2 headline"
                elif CURRENCY_RE.search(line):
                    kind = "R1 currency claim"
                else:
                    hist.append(name)
                    continue
                bad.append((name, i, lit, kind, line.strip()))

    # ---- R3: the beat count is a separate record from the score, and it drifts
    beat_claims = 0
    for path in docs:
        name = os.path.basename(path)
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
        heading, fenced = "", False
        stale_ctx = stale_paragraphs(lines)
        for i, line in enumerate(lines, 1):
            if line.lstrip().startswith("```"):
                fenced = not fenced
                continue
            if fenced:
                continue                       # a code block is not prose
            if line.startswith("#"):
                heading = line
            counts = [int(m.group(1)) for m in BEAT_RE.finditer(line)]
            if not counts:
                continue
            if not BEAT_LABEL_RE.search(line):
                continue      # a count of something else (verified rows, support rows)
            current = any(l.startswith(CANON) for l in SCORE_RE.findall(line))
            claim = ("| " in line or current or section_current(heading)
                     or CURRENCY_RE.search(line))
            if not claim:
                continue                       # prose history is inventory
            beat_claims += len(counts)
            if s["beats"] in counts:
                continue          # a correction table: the line states the true count too
            if any(t in line.lower() for t in TAGS) or stale_score_quoted(line) \
                    or i in stale_ctx:
                continue
            for m in BEAT_RE.finditer(line):
                bad.append((name, i, m.group(0), "R3 beat count", line.strip()))

    print(f"[record_guard] delivered {cur}, beats {s['beats']}, "
          f"rows {s['rows']}; scanned {len(docs)} docs, {claims} totals, "
          f"{beat_claims} beat counts")
    for name, i, lit, kind, text in bad:
        print(f"  {name}:{i}: {lit}  [{kind}]\n      {text[:110]}")
    if bad:
        print(f"[record_guard] FAILED: {len(bad)} stale total(s) presented as "
              "current. Update the line, or tag it historical/stale.")
        return 1
    print("[record_guard] OK: no stale total is presented as current")
    if hist:
        inv = sorted(set(hist))
        print(f"[record_guard] {len(hist)} historical total(s) quoted below the "
              f"title block in {len(inv)} doc(s) — inventory, not claims:"
              f" {', '.join(inv)}")
        if "--list-history" in sys.argv:
            for name in inv:
                print(f"    {name}")

    # ---- notes (never fatal)
    tp = os.path.join(ROOT, "workspace/push/table.json")
    if os.path.exists(tp):
        try:
            tbl = json.load(open(tp))
            if isinstance(tbl, dict) and tbl and all(str(k).isdigit() for k in tbl):
                per = {int(k): [tuple(r) for r in v] for k, v in tbl.items()}
                ts = sqscore.summarise(per)
                same = abs(ts["score"] - s["score"]) < sqscore.TOL
                print(f"[record_guard] note: table.json scores {ts['score']:.9f} "
                      f"over {ts['rows']} rows, {ts['beats']} beats"
                      + (" (current)" if same else
                         " -- STALE, read-only, never write back"))
            else:
                print("[record_guard] note: table.json schema not a per-n state "
                      "map; staleness not checked")
        except Exception as e:                       # noqa: BLE001
            print(f"[record_guard] note: table.json unreadable ({e.__class__.__name__})")

    log = os.path.join(ROOT, "04-RUN-LOG.md")
    if os.path.exists(log):
        runs = [int(m) for m in re.findall(r"[Rr]un (\d+)", open(log).read())]
        led = []
        for f in glob.glob(os.path.join(ROOT, "workspace/push/*.json")):
            try:
                d = json.load(open(f))
            except Exception:                        # noqa: BLE001
                continue
            if isinstance(d, dict) and isinstance(d.get("run"), int):
                led.append((d["run"], os.path.basename(f)))
        if runs and led:
            rmax, lmax = max(runs), max(led)
            if rmax < lmax[0]:
                print(f"[record_guard] note: run log stops at run {rmax} but "
                      f"{lmax[1]} is run {lmax[0]} — log an entry")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
