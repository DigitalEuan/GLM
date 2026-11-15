#!/usr/bin/env python3
"""Column 3 (TCT) — The cascade planner (original method: systematic
L-extension closure). Established ingredient: Friedman's L-extension
("put an L of squares around a packing"); original contribution: systematic
chaining + base selection + exact two-path accounting.

Closure (exact): from m squares packed in side L (inner square at [1,1+L]^2),
place floor(L+1) squares along the bottom band and floor(L) squares up the
left band -> m2 = m + floor(L+1) + floor(L) squares in side L+1.

Two disjoint derivation paths for chain counts:
  A. recursive application of the closure
  B. closed form: m_j = m0 + sum_{i<j} (floor(L0+i+1) + floor(L0+i))
All generated packings are checked here (containment + SAT <= 1e-9) before
being written to submission/cascade.json.

UBP: counts exact in Z; coordinates float64 with declared 1e-9 certificate.
"""
import importlib.util, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("eng", os.path.join(HERE, "03_pack_engine.py"))
eng = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eng)
spec2 = importlib.util.spec_from_file_location("ver", os.path.join(HERE, "04_verify_packing.py"))
ver = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(ver)

def normalize(state):
    """translate so bbox min = (0,0)"""
    lo_x = min(x - eng.half_extent(t) for x, y, t in state)
    lo_y = min(y - eng.half_extent(t) for x, y, t in state)
    return [(x - lo_x, y - lo_y, t) for x, y, t in state]

def extend(m, L, state):
    """L-extension closure: returns (m2, L2, state2)."""
    state = normalize(state)
    row = int(L + 1)          # floor(L+1) for L >= 0
    col = int(L)              # floor(L)
    st2 = [(x + 1.0, y + 1.0, t) for x, y, t in state]
    for i in range(row):
        st2.append((i + 0.5, 0.5, 0.0))
    for j in range(col):
        st2.append((0.5, 1 + j + 0.5, 0.0))
    return m + row + col, L + 1.0, st2

def closed_form_count(m0, L0, steps):
    """path B: m after `steps` closures, without building coordinates."""
    m = m0
    for i in range(steps):
        m += int(L0 + i + 1) + int(L0 + i)
    return m

def main():
    root = os.path.join(HERE, "..", "..", "submission")
    found = {}
    for fname in ("found.json", "found2.json"):
        p = os.path.join(root, fname)
        if os.path.exists(p):
            for k, v in json.load(open(p)).items():
                if k not in found or v["L"] < found[k]["L"]:
                    found[k] = v
    out = {}
    checked = 0
    for key, rec in sorted(found.items(), key=lambda kv: int(kv[0])):
        m0 = int(key)
        L0 = rec["L"]
        state = normalize([tuple(q) for q in rec["state"]])
        # quench: deepen convergence below certificate tolerance (1e-9)
        state = eng.settle_positions(state, L0, 300)
        ok, Lchk, _ = ver.verify(state)
        assert ok, f"base {key} failed verification"
        m, L, st = m0, L0, state
        j = 0
        while m <= 1000:
            if m > m0:
                ok, Lact, _ = ver.verify(st)
                assert ok, f"cascade n={m} from base {m0} failed verification"
                # two-path count check
                assert m == closed_form_count(m0, L0, j), (m, j)
                checked += 1
                prev = out.get(str(m))
                if prev is None or L < prev["L"]:
                    out[str(m)] = {"L": L, "state": [[round(x, 12), round(y, 12), round(t, 12)] for x, y, t in st]}
            m, L, st = extend(m, L, st)
            j += 1
            if j > 1000:
                break
    json.dump(out, open(os.path.join(root, "cascade.json"), "w"))
    print(f"CASCADE_GENERATED={len(out)}")
    print(f"CASCADE_CHECKED={checked}")
    print("TWO_PATH_COUNTS_OK=1")

if __name__ == "__main__":
    main()
