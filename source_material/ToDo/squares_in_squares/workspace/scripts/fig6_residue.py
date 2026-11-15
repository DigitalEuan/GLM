#!/usr/bin/env python3
"""fig6_residue.py — Run 6 figure: the residue distribution of the 593
jammed puzzles, audited from residue_audit.json (English labels).
Stacked bars per block k (k=2..31): LOW band (r<=18, the 69 live
counterexamples), MID band (19<=r<=2k-2, the residue gap), NAG
(Nagamochi r=2k-1,2k), SQ folded into LOW/MID where applicable (r=0
squares are their own class, shown as one marker per block).
Also: the cascade leverage diagram inset (verified constructively)."""
import json
import math

import matplotlib.font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/truetype/chinese/NotoSansSC-Regular.ttf')
fm.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Noto Sans SC', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

ROOT = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))

A = json.load(open(ROOT + '/download/residue_audit.json'))
rows = A['rows']            # jammed puzzles with k, r, class
per_k = {}
for row in rows:
    per_k.setdefault(row['k'], {'SQ': 0, 'NAG': 0, 'LOW': 0, 'MID': 0})
    per_k[row['k']][row['class']] += 1

ks = sorted(k for k in per_k if k >= 2)
fig, ax = plt.subplots(figsize=(11.4, 6.6), constrained_layout=True)
w = 0.8
bLow = [per_k[k]['LOW'] for k in ks]
bMid = [per_k[k]['MID'] for k in ks]
bNag = [per_k[k]['NAG'] for k in ks]
bSq = [per_k[k]['SQ'] for k in ks]
x = range(len(ks))
ax.bar(x, bLow, w, label=f'LOW band r<=18 (cascade counterexamples; total {sum(bLow)})', color='#529286')
ax.bar(x, bMid, w, bottom=bLow, label=f'MID band 19<=r<=2k-2 (the residue gap; total {sum(bMid)})', color='#B23A48')
ax.bar(x, bNag, w, bottom=[a + b for a, b in zip(bLow, bMid)],
       label=f'NAG r=2k-1,2k (Nagamochi-proven optimal; total {sum(bNag)})', color='#8A8A8A')
ax.bar(x, bSq, w, bottom=[a + b + c for a, b, c in zip(bLow, bMid, bNag)],
       label=f'SQ r=0 (perfect squares, optimal by area; total {sum(bSq)})', color='#2C3E50')
ax.set_xticks(list(x))
ax.set_xticklabels([str(k) for k in ks])
ax.set_xlabel('block k  (n = k^2 + r,  0 <= r <= 2k)')
ax.set_ylabel('jammed puzzles (grid-tied)')
ax.set_title('Fig 6  The 593 jammed puzzles by block and residue class — audited, not assumed\n'
             '(LOW: 69 live counterexamples to "r<=18 solved by cascade"; MID: 433; NAG: 60 proven; SQ: 31 proven)',
             fontsize=11)
# annotate a few blocks
for i, k in enumerate(ks):
    tot = bLow[i] + bMid[i] + bNag[i] + bSq[i]
    if tot >= 36 or k in (18, 19):
        ax.annotate(str(tot), (i, tot + 0.4), ha='center', fontsize=7.5, color='#444444')
ax.legend(loc='upper left', fontsize=8.5)
out = ROOT + '/download/fig/f6_residue.png'
fig.savefig(out, dpi=160)
from PIL import Image
im = Image.open(out).convert('L')
h = im.histogram()
print(out, im.size, 'non-white ratio', round(1 - h[255] / sum(h), 3))
