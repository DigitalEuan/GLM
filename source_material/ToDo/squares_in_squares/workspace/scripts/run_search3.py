#!/usr/bin/env python3
"""Wave-3: rescue near-misses at grid-0.02 with slow shrink + heavy restarts."""
import importlib.util, json, os, time
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("eng", os.path.join(HERE, "column3", "03_pack_engine.py"))
eng = importlib.util.module_from_spec(spec); spec.loader.exec_module(eng)
TARGETS = [(11, 3.98), (18, 4.98), (27, 5.98), (12, 3.98), (29, 5.98), (10, 3.98)]
OUT = os.path.join(HERE, "..", "submission", "found2.json")
found = json.load(open(OUT)) if os.path.exists(OUT) else {}
for n, L in TARGETS:
    key = str(n)
    best = found.get(key, {}).get("L", 1e9)
    if L >= best: continue
    t0 = time.time()
    sol, e = eng.pack(n, L, restarts=22, seed=9000 + n, shrink_delta=0.002)
    dt = time.time() - t0
    if e < 1e-8:
        if e < 1e-8:
            sol = eng.settle_positions(sol, L, 300)
            e = eng.total_energy(sol, L)
        found[key] = {"L": L, "state": [[round(x,12), round(y,12), round(t,12)] for x,y,t in sol]}
        json.dump(found, open(OUT, "w"))
        print(f"FOUND n={n} L={L} in {dt:.0f}s", flush=True)
    else:
        print(f"fail  n={n} L={L} E={e:.3e} in {dt:.0f}s", flush=True)
print("done", flush=True)
