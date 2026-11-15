#!/usr/bin/env python3
"""Column 3 (TCT) — Scorecard + submission assembly.
Reads the sample submission (grid packing, all 1000 puzzles), replaces
puzzles where found.json / cascade.json hold better (verified) packings,
writes submission/submission.csv, and reports the score accounting.

Score (competition): sum over puzzles of L/sqrt(n) - 1, lower better;
grid-only baseline is computed EXACTLY in 01_grid_baseline.py; this script's
totals are MEASURED (float64, declared error bound ~1e-9 per puzzle).

Two paths for the improvement accounting: per-puzzle delta sum vs. totals
difference (must agree to 1e-9).
"""
import csv, json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
SUB = os.path.join(ROOT, "submission")

def load_best():
    best = {}
    for fname in ("found.json", "found2.json", "cascade.json"):
        path = os.path.join(SUB, fname)
        if os.path.exists(path):
            for k, rec in json.load(open(path)).items():
                n = int(k)
                if n not in best or rec["L"] < best[n]["L"]:
                    best[n] = rec
    return best

def main():
    best = load_best()
    sample_path = os.path.join(ROOT, "..", ".openclaw", "tmp", "kaggle", "sample_submission.csv")
    if not os.path.exists(sample_path):
        sample_path = os.path.join(SUB, "sample_submission.csv")
    out_rows = []
    grid_total = 0.0
    ours_total = 0.0
    delta_sum = 0.0
    improved = []
    with open(sample_path) as f:
        rd = csv.reader(f)
        header = next(rd)
        assert header == ["id", "n", "square_id", "x", "y", "angle"]
        rows_by_n = {}
        for row in rd:
            rows_by_n.setdefault(int(row[1]), []).append(row)
    for n in range(1, 1001):
        rows = rows_by_n[n]
        L_grid = math.ceil(math.sqrt(n))
        grid_score = L_grid / math.sqrt(n) - 1
        grid_total += grid_score
        rec = best.get(n)
        use_grid = True
        L_ours = L_grid
        if rec is not None and rec["L"] < L_grid - 1e-9:
            use_grid = False
            L_ours = rec["L"]
        ours_total += L_ours / math.sqrt(n) - 1
        delta_sum += (L_grid - L_ours) / math.sqrt(n)
        if use_grid:
            out_rows.extend(rows)
        else:
            improved.append((n, L_grid, L_ours))
            st = rec["state"]
            for sq, row in enumerate(rows):
                x, y, t = st[sq]
                out_rows.append([row[0], str(n), str(sq),
                                 f"{x:.12f}", f"{y:.12f}", f"{t:.12f}"])
    with open(os.path.join(SUB, "submission.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(out_rows)
    assert abs((grid_total - ours_total) - delta_sum) < 1e-9
    print(f"IMPROVED_PUZZLES={len(improved)}")
    print(f"GRID_TOTAL={grid_total:.6f}")
    print(f"OURS_TOTAL={ours_total:.6f}")
    print(f"IMPROVEMENT={grid_total - ours_total:.6f}")
    print(f"ROWS={len(out_rows)}")
    for n, lg, lo in improved[:12]:
        print(f"  n={n}: grid L={lg} -> ours L={lo:.6f}")

if __name__ == "__main__":
    main()
