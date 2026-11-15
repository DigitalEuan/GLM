#!/usr/bin/env python3
"""Search driver — runs the packing engine (03) over target (n, L) pairs and
saves verified candidates to submission/found.json. Experimental instrument:
results are MEASURED; certification margin documented in 04_verify_packing.py.
"""
import importlib.util, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("eng", os.path.join(HERE, "column3", "03_pack_engine.py"))
eng = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eng)

TARGETS = [
    (5, 2.72), (5, 2.75), (5, 2.80),
    (10, 3.72), (10, 3.75), (10, 3.85),
    (11, 3.90), (11, 3.95),
    (17, 4.75), (17, 4.85), (17, 4.95),
    (19, 4.95),
    (26, 5.85), (27, 5.90), (28, 5.95), (29, 5.98),
    (37, 6.90), (41, 6.98),
    (50, 7.95),
]

OUT = os.path.join(HERE, "..", "submission", "found.json")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
found = {}
if os.path.exists(OUT):
    found = json.load(open(OUT))

for n, L in TARGETS:
    key = f"{n}"
    best_for_n = found.get(key, {}).get("L", 1e9)
    if L >= best_for_n:
        continue
    restarts = max(8, 30 - n // 2)
    t0 = time.time()
    sol, e = eng.pack(n, L, restarts=restarts, seed=1000 + n, shrink_delta=0.005)
    dt = time.time() - t0
    if e < 1e-8:
        if e < 1e-8:
            sol = eng.settle_positions(sol, L, 300)
            e = eng.total_energy(sol, L)
        found[key] = {"L": L, "state": [[round(x, 12), round(y, 12), round(t, 12)] for x, y, t in sol]}
        json.dump(found, open(OUT, "w"))
        print(f"FOUND n={n} L={L} in {dt:.1f}s", flush=True)
    else:
        print(f"fail  n={n} L={L} E={e:.3e} in {dt:.1f}s", flush=True)
print("done", flush=True)
