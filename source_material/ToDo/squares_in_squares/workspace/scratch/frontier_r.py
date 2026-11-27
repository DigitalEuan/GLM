"""The r-frontier: for every r = k^2 - n, how many rows are beaten, tied, and what the ties cost."""
import math
import os
import sys
from decimal import Decimal, getcontext

sys.path.insert(0, "scripts")
import true_geom as TG

getcontext().prec = 40
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SUB = os.path.join(ROOT, "workspace/submission/submission.csv")


def delivered():
    per = {}
    with open(SUB) as f:
        names = [h.strip() for h in f.readline().split(",")]
        ix = {h: i for i, h in enumerate(names)}
        for line in f:
            p = line.rstrip("\n").split(",")
            if len(p) < len(names):
                continue
            per.setdefault(int(p[ix["n"]]), []).append(
                (Decimal(p[ix["x"]].strip()), Decimal(p[ix["y"]].strip()),
                 Decimal(p[ix["angle"]].strip())))
    return {n: TG.side(c) for n, c in per.items()}


#: rows whose side is known exactly: s(n) = k.  r = 1, 2 Nagamochi 2005; r = 3 Daniel 2026
#: (Lean + two exact checkers, replayed by the Squares Project); r = 4 Daniel 2026 (reported,
#: ValidTilt9 reported independently by Hosono); r = 0 is the area floor.
PROVED_R = {0: "area floor", 1: "Nagamochi", 2: "Nagamochi", 3: "Daniel", 4: "Daniel (reported)"}


def main():
    deliv = delivered()
    tab = {}
    for n in range(1, 1001):
        L = deliv[n]
        k = math.isqrt(n)
        if k * k < n:
            k += 1
        r = k * k - n
        sn = Decimal(n).sqrt()
        beat = L < k - Decimal("1e-8")
        tab.setdefault(r, {"beat": 0, "tie": 0, "score": Decimal(0), "rows": []})
        rec = tab[r]
        if beat:
            rec["beat"] += 1
        else:
            rec["tie"] += 1
            rec["score"] += L / sn - 1
        rec["rows"].append(n)
    tot_tie_score = sum(rec["score"] for rec in tab.values())
    print(f"{'r':>3} {'rows':>5} {'beaten':>7} {'tied':>5} {'tie score':>10}  status")
    acc_proved = Decimal(0)
    acc_open = Decimal(0)
    acc_open_rows = 0
    for r in sorted(tab):
        rec = tab[r]
        status = ""
        if r in PROVED_R:
            status = f"proved optimal ({PROVED_R[r]})"
            acc_proved += rec["score"]
        else:
            status = "open"
            acc_open += rec["score"]
            acc_open_rows += rec["tie"]
        print(f"{r:>3} {len(rec['rows']):>5} {rec['beat']:>7} {rec['tie']:>5} "
              f"{rec['score']:>10.4f}  {status}")
    print(f"\ntie score total {tot_tie_score:.4f}")
    print(f"  locked behind proved optima (r<=4): {acc_proved:.4f}")
    print(f"  open ties (r>=5): {acc_open:.4f} over {acc_open_rows} rows "
          f"(mean {acc_open / acc_open_rows:.5f})")
    # how the beats distribute
    print("\nbeaten rows by r:")
    for r in sorted(tab):
        rec = tab[r]
        if rec["beat"]:
            print(f"   r={r:>2}: {rec['beat']:>4} beaten of {len(rec['rows'])} rows")


if __name__ == "__main__":
    main()
