#!/usr/bin/env python3
r"""parse_kingbird.py — parse the kingbird mirror of Friedman's
squares-in-squares catalogue and diff its values against table.json.

Page format per record:
  <div class="box"><font size="+3">N<br><a href="square-N.svg">...
  ... $s = <formula> = \Nn{VALUE}$ <br> [Rigid.] <br> attribution
Some records have no \Nn{} (plain number), some give only a formula.
Output: kingbird values dict; a diff report:
  - WORSE: Friedman s < our L  (candidates to import)
  - BETTER/EQUAL: our table already at or below the catalogue.
Saves /tmp/kingbird.json.
"""
import json
import math
import re
import html as H
from math import sqrt

TAB = "/home/z/my-project/workspace/submission/table.json"
PAGE = "/tmp/kb.html"


def parse():
    h = open(PAGE, errors="ignore").read()
    # blocks: from <div class="box"> to </div></div> pairs; simpler: split on
    # 'square-N.svg' anchors and look backwards for the n and forwards for s.
    boxes = re.split(r'<div class="box">', h)[1:]
    out = {}
    for b in boxes:
        m = re.match(r'\s*<font size="\+3">\s*(\d+)\s*<br>', b)
        if not m:
            continue
        n = int(m.group(1))
        # value: \Nn{...} first, else formula-only, else bare $s = 6$
        vm = re.search(r'\\Nn\{([0-9.]+)\}', b)
        if vm:
            s = float(vm.group(1))
            kind = "nn"
        else:
            fm = re.search(r'\$s\s*=\s*(.*?)\$', b)
            if not fm:
                continue
            f = H.unescape(fm.group(1))
            # try to eval simple LaTeX-ish: replace \sqrt 2, {1\over 2} etc.
            e = f
            e = re.sub(r'\\sqrt\s*(\d+)', r'sqrt(\1)', e)
            e = e.replace('\\!', '').replace('\\,', '')
            e = re.sub(r'\{([^{}]*)\\over\s*([^{}]*)\}', r'((\1)/(\2))', e)
            e = e.replace('{', '(').replace('}', ')')
            e = re.sub(r'sqrt\s*(\d+)', r'sqrt(\1)', e)
            try:
                s = float(eval(e, {"sqrt": sqrt, "__builtins__": {}}))
                kind = "formula"
            except Exception:
                continue
        out[n] = (s, kind)
    return out


def main():
    kb = parse()
    print(f"catalogue records parsed: {len(kb)} (n range {min(kb)}..{max(kb)})")
    tab = json.load(open(TAB))
    worse, better, equal = [], [], []
    for n, (s, kind) in sorted(kb.items()):
        if n > 1000:
            continue
        ours = tab[str(n)]["L"]
        if s < ours - 1e-9:
            worse.append((n, ours, s, kind))
        elif abs(s - ours) < 1e-9:
            equal.append(n)
        else:
            better.append(n)
    print(f"n<=1000: Friedman-beats-us: {len(worse)} | equal: {len(equal)} | we-beat: {len(better)}")
    for n, ours, s, kind in worse[:25]:
        print(f"  IMPORT n={n}: ours={ours:.9f} catalogue={s:.9f} ({kind}) src={tab[str(n)].get('src','?')[:24]}")
    json.dump({str(n): v for n, v in kb.items()}, open("/tmp/kingbird.json", "w"))
    json.dump(worse, open("/tmp/kb_import.json", "w"))


if __name__ == "__main__":
    main()
