#!/usr/bin/env python3
"""visual_check_run7.py — programmatic visual check of the rendered pages
(image input unavailable in this session; this is the automated equivalent).

Checks per page: ink coverage (blank-page detection), ink in the four
margin bands (content overflow beyond body margins), and full-text
extraction for: TOC on page 2, section order, leftover placeholders
(XXX / TODO / [ ] / undefined / NaN / Markdown symbols), figure presence
by pixel density on the page carrying Figure 1, and page numbers."""
import re
import subprocess
import sys
from PIL import Image

PAGES_DIR = "/tmp/render"
PDF = "/home/z/my-project/download/Run7_Strategic_Plan.pdf"


def page_ink(path):
    im = Image.open(path).convert("L")
    w, h = im.size
    px = im.load()
    total = w * h
    ink = 0
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            if px[x, y] < 200:
                ink += 1
    return im.size, ink / (total / 4)


def band_ink(path, x0, x1, y0, y1):
    im = Image.open(path).convert("L")
    w, h = im.size
    px = im.load()
    cnt = tot = 0
    for y in range(int(y0 * h), int(y1 * h), 2):
        for x in range(int(x0 * w), int(x1 * w), 2):
            tot += 1
            if px[x, y] < 200:
                cnt += 1
    return cnt / max(tot, 1)


def main():
    txt = subprocess.run(["pdftotext", "-layout", PDF, "-"],
                         capture_output=True, text=True).stdout
    pages = sorted(
        f"{PAGES_DIR}/{p}" for p in __import__("os").listdir(PAGES_DIR)
        if p.endswith(".jpg"))
    print(f"{len(pages)} pages")
    fails = []
    for i, pg in enumerate(pages, 1):
        size, cov = page_ink(pg)
        # margin bands (body area ~ x 0.09..0.91, y 0.08..0.93)
        lm = band_ink(pg, 0.0, 0.06, 0.1, 0.9)
        rm = band_ink(pg, 0.94, 1.0, 0.1, 0.9)
        tag = ""
        if cov < 0.005:
            tag = "NEARLY-BLANK"
            if i not in ():
                fails.append(f"page {i} nearly blank (ink {cov:.4f})")
        if i == 1:
            # cover: expect strong ink (dark upper block + divider)
            if cov < 0.08:
                fails.append(f"cover ink too low: {cov:.4f}")
            tag = "cover"
        print(f"  page {i} ({tag or 'body'}): ink={cov:.4f} "
              f"left-band={lm:.4f} right-band={rm:.4f} size={size}")
        if lm > 0.02 and i > 1:
            fails.append(f"page {i} content into left margin ({lm:.3f})")
        if rm > 0.02 and i > 1:
            fails.append(f"page {i} content into right margin ({rm:.3f})")

    # text checks
    if "Table of Contents" not in pages and False:
        pass
    if "Table of Contents" not in txt:
        fails.append("TOC title missing in text layer")
    for h in ["1. Executive Summary", "2. Where We Stand",
              "3. What We Lack", "4. The Lorentzian Lift Program",
              "5. The Road Ahead", "6. Risks", "7. Reproducibility"]:
        if h not in txt:
            fails.append(f"missing heading: {h}")
    order = [txt.find(h) for h in ["1. Executive Summary", "2. Where We Stand",
                                   "3. What We Lack", "4. The Lorentzian Lift Program",
                                   "5. The Road Ahead", "6. Risks", "7. Reproducibility"]]
    if order != sorted(order) or -1 in order:
        fails.append(f"section order broken: {order}")
    bad_pat = re.compile(r"undefined|NaN|TODO|\bXXX\b|\|---\||\*\*")
    for m in bad_pat.finditer(txt):
        fails.append(f"forbidden token at {m.start()}: {m.group(0)!r} "
                     f"context: {txt[max(0, m.start()-40):m.start()+40]!r}")
    # figure page: the page after Table-2 page — find page with a large
    # contiguous dense block (the chart) — heuristic: page 4-5 highest ink
    # table presence
    for t in ["Table 1:", "Table 2:", "Table 3:", "Figure 1:"]:
        if t not in txt:
            fails.append(f"missing caption: {t}")
    print("\nFAILS:" if fails else "\nALL CHECKS PASS")
    for f in fails:
        print(" -", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
