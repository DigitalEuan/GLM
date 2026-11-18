#!/usr/bin/env python3
"""leech_rotation_control.py — does the snap-decisiveness gap say anything

beyond "is this packing rotated?"  Run 45, closing PL-28.

Beating a grid row requires rotating squares, so a rotation indicator is the
trivial baseline any address statistic must beat.  It does not: gap AUC 0.754
overall falls to 0.3495 among rotated rows only, while rotation alone gives AUC
0.819, and MI(gap; beats | rotation) collapses.  Read-only.
"""
import sys, csv, math, numpy as np
sys.path.insert(0,'scripts')
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sqscore as SQ
SQ.guard()
from leech_address import golay_codewords, pockets
from leech_measure import soft_profile
from leech_prior import auc, spearman
cw=golay_codewords()
signs=np.array([[(2*((int(w)>>j)&1)-1) for j in range(24)] for w in cw],float); bits=(signs+1)/2
per={}
with open('workspace/submission/submission.csv') as f:
    rd=csv.reader(f); h=next(rd); ix={k:i for i,k in enumerate(h)}
    for r in rd: per.setdefault(int(r[ix['n']]),[]).append((float(r[ix['x']]),float(r[ix['y']]),float(r[ix['angle']])))
gap=[];beats=[];rot=[];delta=[]
for n in sorted(per):
    st=np.array(per[n],float)
    L = SQ.extent(st)
    r1,r2,_=soft_profile(pockets(st,L),signs,bits)
    k=int(math.floor(math.sqrt(n)))
    gap.append(r1-r2); delta.append(L-k)
    beats.append(1 if SQ.is_beat(n, L) else 0)
    rot.append(1 if np.abs(np.mod(st[:,2],math.pi/2)).max()>1e-9 else 0)
gap=np.array(gap);beats=np.array(beats);rot=np.array(rot);delta=np.array(delta)
g0=gap[beats==0]
print(f"grid rows: {len(g0)}, gap exactly 0: {(g0==0).sum()} ({(g0==0).mean():.3f}), median {np.median(g0):.5f}, max {g0.max():.5f}")
b1=gap[beats==1]
print(f"beating rows: {len(b1)}, gap exactly 0: {(b1==0).sum()}, median {np.median(b1):.5f}")
print(f"rotation indicator: beating rows rotated {rot[beats==1].mean():.3f}, grid rows {rot[beats==0].mean():.3f}")
print(f"AUC(gap->beats) all rows          {auc(gap,beats):.4f}")
m=rot==1
print(f"AUC(gap->beats) ROTATED rows only {auc(gap[m],beats[m]):.4f}  (n={m.sum()}, beats {beats[m].sum()})")
print(f"AUC(rot->beats)                   {auc(rot,beats):.4f}")
mm=(rot==1)&(beats==1)
print(f"among rotated beating rows: Spearman(gap,delta) {spearman(gap[mm],delta[mm]):+.3f}")

def H(a):
    _,c=np.unique(a,return_counts=True); p=c/c.sum(); return float(-(p*np.log2(p)).sum())
def I(a,b,c=None):
    if c is None: return H(a)+H(b)-H([f'{x}|{y}' for x,y in zip(a,b)])
    t=0.0
    for u in np.unique(c):
        m=c==u
        if m.sum()<5: continue
        t+=(m.mean())*(H(a[m])+H(b[m])-H([f'{x}|{y}' for x,y in zip(a[m],b[m])]))
    return t
q=np.digitize(gap,np.quantile(gap,[.25,.5,.75]))
rng=np.random.RandomState(99)
def nullI(a,b,reps=200):
    return np.array([I(a,rng.permutation(b)) for _ in range(reps)])
mI_rot=nullI(rot,beats); mI_gap=nullI(q,beats)
print(f"\nMI(rot;beats)      {I(rot,beats):.4f}   null {mI_rot.mean():.4f}+-{mI_rot.std():.4f}")
print(f"MI(gapQ;beats)     {I(q,beats):.4f}   null {mI_gap.mean():.4f}+-{mI_gap.std():.4f}")
print(f"MI(gapQ;beats|rot) {I(q,beats,rot):.4f}  <- gap information left after controlling rotation")
print(f"MI(rot;beats|gapQ) {I(rot,beats,q):.4f}  <- rotation information left after controlling gap")
import json
json.dump({"grid_rows":int((beats==0).sum()),"grid_gap_zero":float((g0==0).mean()),
 "beating_gap_zero":int((b1==0).sum()),"rot_beating":float(rot[beats==1].mean()),
 "rot_grid":float(rot[beats==0].mean()),"auc_gap_all":auc(gap,beats),
 "auc_gap_rotated":auc(gap[rot==1],beats[rot==1]),"auc_rot":auc(rot,beats),
 "spearman_gap_delta_rotated_beating":spearman(gap[(rot==1)&(beats==1)],delta[(rot==1)&(beats==1)]),
 "mi_rot_beats":I(rot,beats),"mi_gap_beats":I(q,beats),
 "mi_gap_beats_given_rot":I(q,beats,rot),"mi_rot_beats_given_gap":I(rot,beats,q),
 "null_gap_mean":float(mI_gap.mean()),"null_gap_sd":float(mI_gap.std())},
 open('workspace/push/leech_rotation.json','w'),indent=1)
print("wrote workspace/push/leech_rotation.json")
