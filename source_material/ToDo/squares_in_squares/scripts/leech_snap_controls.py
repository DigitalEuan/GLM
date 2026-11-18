#!/usr/bin/env python3
"""leech_snap_controls.py — controls for the snap-decisiveness statistic.

The within-residue permutation test that decides whether I(gap; beats | r) is
real: it permutes "beats" only inside each residue column, so the null keeps
the finite-sample MI bias of 17-row columns and the column marginals.
Read-only. Fills workspace/push/leech_snap_controls.json."""
import sys, csv, math
import os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sqscore as SQ
SQ.guard()
sys.path.insert(0,'scripts')
from leech_address import golay_codewords, hamming, pockets, word_of
from leech_measure import soft_profile, quantile_bins
cw = golay_codewords()
signs = np.array([[(2*((int(w)>>j)&1)-1) for j in range(24)] for w in cw], float)
bits = (signs+1)/2
per={}
with open('workspace/submission/submission.csv') as f:
    rd=csv.reader(f); hdr=next(rd); ix={h:i for i,h in enumerate(hdr)}
    for r in rd:
        per.setdefault(int(r[ix['n']]),[]).append((float(r[ix['x']]),float(r[ix['y']]),float(r[ix['angle']])))
rows=sorted(per); gap=[]; beats=[]; band=[]; res=[]
for n in rows:
    st=np.array(per[n],float)
    L = SQ.extent(st)
    r1,r2,_=soft_profile(pockets(st,L),signs,bits)
    k=int(math.floor(math.sqrt(n)))
    gap.append(r1-r2); beats.append(1 if SQ.is_beat(n, L) else 0)
    band.append(k); res.append(n-k*k)
gap=np.array(gap); q=np.array(quantile_bins(gap)); beats=np.array(beats); band=np.array(band); res=np.array(res)
def H(a):
    _,c=np.unique(a,return_counts=True); p=c/c.sum(); return float(-(p*np.log2(p)).sum())
def I(a,b,c=None):
    if c is None: return H(a)+H(b)-H([f'{x}|{y}' for x,y in zip(a,b)])
    return sum(H(np.array([f'{x}|{y}' for x,y in zip(a[c==u],b[c==u])])) for u in np.unique(c))*0+ \
           sum((c==u).mean()*(H(a[c==u])+H(b[c==u])-H([f'{x}|{y}' for x,y in zip(a[c==u],b[c==u])])) for u in np.unique(c) if (c==u).sum()>5)
print(f"I(band; beats)        {I(band,beats):.4f}  H(band)={H(band):.2f} H(beats)={H(beats):.3f}")
print(f"I(residue; beats)     {I(res,beats):.4f}")
print(f"I(gap; beats)         {I(q,beats):.4f}")
print(f"I(gap; beats | band)  {I(q,beats,band):.4f}")
print(f"I(gap; beats | res)   {I(q,beats,res):.4f}")
print(f"I(hardd; beats | band) needs hard d separately")
# per-band how much of the MI comes from few rows
for k in (10,20,31):
    m=band==k
    if m.sum()>5: print(f"  band {k}: {m.sum()} rows, beats {beats[m].mean():.2f}, gap sd {gap[m].std():.4f}")

# within-column permutation test for I(gap; beats | residue)
def condI(q,beats,res):
    tot=0.0
    for u in np.unique(res):
        m=res==u
        if m.sum()<8: continue
        tot+=(m.mean())*I(q[m],beats[m])
    return tot
obs=condI(q,beats,res)
rng=np.random.RandomState(12345)
nulls=[]
for _ in range(300):
    b=beats.copy()
    for u in np.unique(res):
        m=np.where(res==u)[0]
        if len(m)<8: continue
        b[m]=rng.permutation(beats[m])
    nulls.append(condI(q,b,res))
nulls=np.array(nulls)
print(f"\nwithin-residue permutation test (300 reps):")
print(f"  observed I(gap;beats|res) {obs:.4f}")
print(f"  null mean {nulls.mean():.4f}  sd {nulls.std():.4f}  max {nulls.max():.4f}")
print(f"  z = {(obs-nulls.mean())/nulls.std():+.2f}   p < {(nulls>=obs).mean():.4f}")

import json, os
json.dump({"I_band_beats": I(band, beats), "I_residue_beats": I(res, beats),
           "I_gap_beats": I(q, beats), "I_gap_beats_given_band": I(q, beats, band),
           "I_gap_beats_given_residue": obs,
           "null_mean": float(nulls.mean()), "null_sd": float(nulls.std()),
           "null_max": float(nulls.max()), "z": float((obs - nulls.mean()) / nulls.std()),
           "null_reps": len(nulls)},
          open(os.path.join('workspace/push/leech_snap_controls.json'), 'w'), indent=1)
print("wrote workspace/push/leech_snap_controls.json")
