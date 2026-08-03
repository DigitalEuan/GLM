#!/usr/bin/env python3
"""Reproducible Golay–MOG periodic-table experiment suite (standard library only).

The suite treats each 24-bit object as a data representation.  It measures
whether fixed MOG/3-D arrangements help predict held-out tabular element
properties; it does not assume that an embedding is a physical law.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Callable, Iterable

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data/raw/pubchem_periodic_table.csv"
PROCESSED = ROOT / "data/processed/elements.csv"
RESULTS = ROOT / "results"
SEED = 20260802

# Same systematic extended binary Golay [24,12,8] convention as ubp_unified_v5.
B = (
 (0,1,1,1,1,1,1,1,1,1,1,1),(1,1,1,0,1,1,1,0,0,0,1,0),
 (1,1,0,1,1,1,0,0,0,1,0,1),(1,0,1,1,1,0,0,0,1,0,1,1),
 (1,1,1,1,0,0,0,1,0,1,1,0),(1,1,1,0,0,0,1,0,1,1,0,1),
 (1,1,0,0,0,1,0,1,1,0,1,1),(1,0,0,0,1,0,1,1,0,1,1,1),
 (1,0,0,1,0,1,1,0,1,1,1,0),(1,0,1,0,1,1,0,1,1,1,0,0),
 (1,1,0,1,1,0,1,1,1,0,0,0),(1,0,1,1,0,1,1,1,0,0,0,1))
MOG_GRID_BITS = (0,4,6,19,16,11, 1,17,15,5,9,13,
                 3,21,20,8,10,22, 2,23,14,12,7,18)
TARGETS = ("Electronegativity", "AtomicRadius", "IonizationEnergy",
           "ElectronAffinity", "MeltingPoint", "BoilingPoint", "Density")

# Conventional period/group locations. Lanthanides and actinides are assigned
# group 3 for a reproducible coarse periodic-family split.
PERIOD_ENDS = (2,10,18,36,54,86,118)
GROUP_ROWS = {
 1:[1,18], 2:[1,2,13,14,15,16,17,18], 3:list(range(1,19)),
 4:list(range(1,19)), 5:list(range(1,19)),
 6:[1,2,3]+list(range(4,19)), 7:[1,2,3]+list(range(4,19))}

def period_of(z: int) -> int:
    return next(i+1 for i, end in enumerate(PERIOD_ENDS) if z <= end)

def group_of(z: int) -> int:
    # Explicit starts avoid ambiguity in detached f-block display.
    if z == 1: return 1
    if z == 2: return 18
    rows = {
      2:list(range(3,11)), 3:list(range(11,19)), 4:list(range(19,37)),
      5:list(range(37,55)), 6:list(range(55,87)), 7:list(range(87,119))}
    p=period_of(z); row=rows[p]
    if p in (2,3): return [1,2,13,14,15,16,17,18][row.index(z)]
    if p in (4,5): return row.index(z)+1
    i=row.index(z)
    if i == 0:return 1
    if i == 1:return 2
    if i <= 15:return 3
    return i-12

def message12(z: int) -> list[int]:
    """Legacy injective binary address retained as a comparison control."""
    if not 1 <= z <= 118: raise ValueError("atomic number must be 1..118")
    return [(z >> i) & 1 for i in range(7)] + [0]*5

def gray12(z: int) -> list[int]:
    """Reflected-Gray identity: consecutive atomic numbers differ by one bit."""
    if not 1 <= z <= 118: raise ValueError("atomic number must be 1..118")
    g=z^(z>>1)
    return [(g >> i) & 1 for i in range(12)]

def golay_encode(msg: list[int]) -> list[int]:
    if len(msg) != 12 or any(type(x) is not int or x not in (0,1) for x in msg):
        raise ValueError("message must contain twelve binary integers")
    return msg + [sum(msg[i]*B[j][i] for i in range(12)) % 2 for j in range(12)]

def mog_bits(cw: list[int], permutation: tuple[int,...]=MOG_GRID_BITS) -> list[int]:
    return [cw[i] for i in permutation]

def positions(kind: str) -> list[tuple[float,float,float]]:
    out=[]
    for r in range(4):
      for c in range(6):
        if kind == "planar": out.append((float(c),float(r),0.0))
        elif kind == "stacked": out.append((float(c%3),float(r),float(c//3)))
        elif kind == "cylinder":
          a=2*math.pi*c/6; out.append((math.cos(a),math.sin(a),float(r)))
        elif kind == "sphere":
          i=r*6+c; phi=math.acos(1-2*(i+.5)/24); a=math.pi*(3-math.sqrt(5))*i
          out.append((math.sin(phi)*math.cos(a),math.sin(phi)*math.sin(a),math.cos(phi)))
        else: raise ValueError(kind)
    return out

def geometry_features(bits: list[int], kind: str) -> list[float]:
    pts=[p for p,b in zip(positions(kind),bits) if b]
    if not pts:return [0.0]*10
    n=len(pts); cen=[sum(p[k] for p in pts)/n for k in range(3)]
    ds=[math.dist(pts[i],pts[j]) for i in range(n) for j in range(i)]
    inertia=[sum((p[k]-cen[k])**2 for p in pts)/n for k in range(3)]
    return [float(n),*cen,*inertia,
            sum(ds)/len(ds) if ds else 0.0,
            max(ds) if ds else 0.0,
            sum(math.dist(p,cen)**2 for p in pts)/n]

def descriptor(z:int, config:str, random_perms:dict[str,tuple[int,...]]) -> list[float]:
    use_gray=config.startswith("gray_")
    msg=gray12(z) if use_gray else message12(z); cw=golay_encode(msg)
    core=config[5:] if use_gray else config
    if core == "z_poly": return [z/118,(z/118)**2,(z/118)**3]
    if core == "message_bits": return [float(x) for x in msg]
    if core == "golay_bits": return [float(x) for x in cw]
    if core.startswith("random"):
        perm=random_perms[core]; kind="planar"
    else:
        perm=MOG_GRID_BITS; kind=core.split("_",1)[1]
    mb=mog_bits(cw,perm)
    rows=[sum(mb[6*r:6*r+6]) for r in range(4)]
    cols=[sum(mb[c::6]) for c in range(6)]
    # Aggregate MOG occupancy plus intrinsic geometry.  Omitting raw cell bits
    # keeps model complexity appropriate for the small table.
    return [float(x) for x in rows+cols]+geometry_features(mb,kind)

def read_and_normalize() -> list[dict[str,str]]:
    with RAW.open(newline="",encoding="utf-8-sig") as f: rows=list(csv.DictReader(f))
    if len(rows)!=118 or [int(r["AtomicNumber"]) for r in rows] != list(range(1,119)):
        raise ValueError("raw table must have exactly atomic numbers 1..118")
    fields=list(rows[0])+["Period","Group"]
    PROCESSED.parent.mkdir(parents=True,exist_ok=True)
    with PROCESSED.open("w",newline="",encoding="utf-8") as f:
      w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader()
      for r in rows:
        r=dict(r);z=int(r["AtomicNumber"]);r.update(Period=str(period_of(z)),Group=str(group_of(z)));w.writerow(r)
    return rows

def solve(a:list[list[float]],b:list[float])->list[float]:
    n=len(b); aug=[a[i][:]+[b[i]] for i in range(n)]
    for c in range(n):
      p=max(range(c,n),key=lambda r:abs(aug[r][c]))
      aug[c],aug[p]=aug[p],aug[c]
      if abs(aug[c][c])<1e-12:continue
      q=aug[c][c];aug[c]=[v/q for v in aug[c]]
      for r in range(n):
        if r!=c:
          q=aug[r][c];aug[r]=[x-q*y for x,y in zip(aug[r],aug[c])]
    return [aug[i][-1] for i in range(n)]

def ridge_fit(x:list[list[float]],y:list[float],lam:float)->tuple[list[float],list[float],list[float]]:
    d=len(x[0]); means=[statistics.fmean(r[j] for r in x) for j in range(d)]
    scales=[max(statistics.pstdev(r[j] for r in x),1e-9) for j in range(d)]
    xx=[[1.0]+[(v-m)/s for v,m,s in zip(r,means,scales)] for r in x];d+=1
    a=[[sum(r[i]*r[j] for r in xx)+(lam if i==j and i else 0.0) for j in range(d)] for i in range(d)]
    b=[sum(r[i]*v for r,v in zip(xx,y)) for i in range(d)]
    return solve(a,b),means,scales

def predict(model, x):
    w,m,s=model;return w[0]+sum(w[j+1]*(x[j]-m[j])/s[j] for j in range(len(x)))

def folds_for(items:list[tuple[int,float]], mode:str):
    keys=(lambda z:period_of(z)) if mode=="period" else (lambda z:group_of(z))
    groups=defaultdict(list)
    for i,(z,_) in enumerate(items):groups[keys(z)].append(i)
    return [v for _,v in sorted(groups.items()) if len(v) and len(v)<len(items)]

def cv_predictions(items, config, perms, mode="period", shuffled=False):
    y=[v for _,v in items]
    if shuffled:
      y=y[:];random.Random(SEED+len(items)).shuffle(y)
    pred=[None]*len(items)
    for test in folds_for(items,mode):
      train=[i for i in range(len(items)) if i not in set(test)]
      # A predeclared regularization value avoids configuration selection on
      # test data; future larger benchmarks can tune it in nested inner folds.
      model=ridge_fit([descriptor(items[i][0],config,perms) for i in train],[y[i] for i in train],10.0)
      for i in test:pred[i]=predict(model,descriptor(items[i][0],config,perms))
    return y,[float(p) for p in pred]

def metrics(y,p):
    err=[a-b for a,b in zip(y,p)];mean=statistics.fmean(y)
    return {"n":len(y),"mae":statistics.fmean(abs(e) for e in err),
      "rmse":math.sqrt(statistics.fmean(e*e for e in err)),
      "r2":1-sum(e*e for e in err)/sum((v-mean)**2 for v in y)}

def classification_cv(items, config, perms, shuffled=False):
    """Deterministic five-fold one-vs-rest ridge classification."""
    labels=[v for _,v in items]
    if shuffled:
      labels=labels[:];random.Random(SEED+97+len(items)).shuffle(labels)
    classes=sorted(set(labels)); pred=[None]*len(items)
    for fold in range(5):
      test=[i for i,(z,_) in enumerate(items) if z%5==fold]
      train=[i for i in range(len(items)) if i not in set(test)]
      models={c:ridge_fit([descriptor(items[i][0],config,perms) for i in train],
                          [1.0 if labels[i]==c else 0.0 for i in train],10.0)
              for c in classes}
      for i in test:
        x=descriptor(items[i][0],config,perms)
        pred[i]=max(classes,key=lambda c:predict(models[c],x))
    return labels,pred

def classification_metrics(y,p):
    classes=sorted(set(y)); acc=sum(a==b for a,b in zip(y,p))/len(y)
    recalls=[]
    for c in classes:
      idx=[i for i,v in enumerate(y) if v==c]
      recalls.append(sum(p[i]==c for i in idx)/len(idx))
    return {"n":len(y),"accuracy":acc,"balanced_accuracy":statistics.fmean(recalls),"classes":len(classes)}

def exact_audit(perms):
    cws=[golay_encode(message12(z)) for z in range(1,119)]
    allc=[golay_encode([(n>>i)&1 for i in range(12)]) for n in range(4096)]
    weights=defaultdict(int)
    for c in allc:weights[sum(c)]+=1
    # H=[B^T|I], so every generated codeword has zero syndrome.
    parity_ok=all(all((sum(c[i]*B[i][j] for i in range(12))+c[12+j])%2==0 for j in range(12)) for c in allc)
    # Geometry invariance: pair-distance feature unchanged under rigid rotation/translation.
    sample=mog_bits(cws[41]);f=geometry_features(sample,"planar")
    ps=positions("planar");a=.731;rot=[(math.cos(a)*x-math.sin(a)*y+7,math.sin(a)*x+math.cos(a)*y-3,z+11) for x,y,z in ps]
    active=[p for p,b in zip(rot,sample) if b];ds=[math.dist(active[i],active[j]) for i in range(len(active)) for j in range(i)]
    rotated_mean=sum(ds)/len(ds) if ds else 0
    return {"identity_count":len(set(tuple(c) for c in cws)),"round_trips":sum(sum(message12(z)[i]<<i for i in range(7))==z for z in range(1,119)),
      "all_codewords":len(set(tuple(c) for c in allc)),"weight_distribution":dict(sorted(weights.items())),
      "parity_checks_all_zero":parity_ok,"mog_is_permutation":sorted(MOG_GRID_BITS)==list(range(24)),
      "rigid_distance_invariance_error":abs(f[7]-rotated_mean)}

def run():
    rows=read_and_normalize();RESULTS.mkdir(exist_ok=True)
    rng=random.Random(SEED);perms={}
    for k in range(8):
      p=list(range(24));rng.shuffle(p);perms[f"random_{k:02d}"]=tuple(p)
    configs=["z_poly","message_bits","golay_bits","mog_planar","mog_stacked","mog_cylinder","mog_sphere",
      "gray_message_bits","gray_golay_bits","gray_mog_planar","gray_mog_stacked","gray_mog_cylinder","gray_mog_sphere",*perms]
    audit=exact_audit(perms)
    records=[];pred_rows=[]
    for target in TARGETS:
      items=[]
      for r in rows:
        try:items.append((int(r["AtomicNumber"]),float(r[target])))
        except ValueError:pass
      for mode in ("period","group"):
       for config in configs:
        y,p=cv_predictions(items,config,perms,mode)
        m=metrics(y,p);records.append({"target":target,"split":f"leave_{mode}_out","config":config,**m})
        if mode=="period":pred_rows += [{"target":target,"config":config,"Z":z,"observed":a,"predicted":b} for (z,_),a,b in zip(items,y,p)]
      # Target shuffle negative control on two representative encodings.
      for config in ("z_poly","mog_planar"):
        y,p=cv_predictions(items,config,perms,"period",True);records.append({"target":target,"split":"shuffled_target","config":config,**metrics(y,p)})
    with (RESULTS/"metrics.csv").open("w",newline="") as f:
      w=csv.DictWriter(f,fieldnames=records[0],lineterminator="\n");w.writeheader();w.writerows(records)
    with (RESULTS/"predictions.csv").open("w",newline="") as f:
      w=csv.DictWriter(f,fieldnames=pred_rows[0],lineterminator="\n");w.writeheader();w.writerows(pred_rows)
    class_records=[]
    class_targets={"Period":lambda r:str(period_of(int(r["AtomicNumber"]))),
      "Group":lambda r:str(group_of(int(r["AtomicNumber"]))),
      "StandardState":lambda r:r["StandardState"],"GroupBlock":lambda r:r["GroupBlock"]}
    for target,get_label in class_targets.items():
      items=[(int(r["AtomicNumber"]),get_label(r)) for r in rows if get_label(r)]
      for config in configs:
        y,p=classification_cv(items,config,perms)
        class_records.append({"target":target,"split":"z_mod_5","config":config,**classification_metrics(y,p)})
      for config in ("z_poly","mog_planar"):
        y,p=classification_cv(items,config,perms,True)
        class_records.append({"target":target,"split":"shuffled_target","config":config,**classification_metrics(y,p)})
    with (RESULTS/"classification_metrics.csv").open("w",newline="") as f:
      w=csv.DictWriter(f,fieldnames=class_records[0],lineterminator="\n");w.writeheader();w.writerows(class_records)
    # Rank configurations across endpoints/splits; lower normalized MAE wins.
    normal=[]
    for target in TARGETS:
      base=[r for r in records if r["target"]==target and r["config"]=="z_poly" and r["split"]!="shuffled_target"]
      denom={r["split"]:r["mae"] for r in base}
      for r in records:
       if r["target"]==target and r["split"] in denom:normal.append((r["config"],r["mae"]/denom[r["split"]]))
    scores={c:statistics.fmean(v for k,v in normal if k==c) for c in configs}
    result={"schema_version":1,"seed":SEED,"raw_sha256":hashlib.sha256(RAW.read_bytes()).hexdigest(),
      "audit":audit,"configuration_normalized_mae":dict(sorted(scores.items(),key=lambda x:x[1])),
      "best_experimental_configuration":min(scores,key=scores.get),
      "interpretation":"Best means lowest average normalized held-out MAE in this atomic-property suite, not a universal physical optimum."}
    (RESULTS/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--run",action="store_true");args=ap.parse_args()
    if args.run:run()
    else:ap.print_help()
if __name__=="__main__":main()
