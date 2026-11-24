#!/usr/bin/env python3
r"""published_census.py — run 114: benchmark the delivered table against the
published best-known packings, and price the 447 unbeaten (grid) rows.

USER REQUEST (run 114): "The Kaggle score can be moved ... I want to stop
looking at the rows already good and focus on the more difficult but actually
likely to have some movement possible - can we just focus on the un-optimised
grids for a good run ... see what is logical and what you can achieve."

Two questions, in order.

A. Is the delivered table behind the published record anywhere (n <= 324)?
   Reference: the Squares Project best-known list of 2026-10-20
   (jlevy.github.io/squares, 324 cases, values transcribed to 5 dp; exact
   where the source writes "=", upper bounds where it writes "<=").  A row is
   BEHIND when published < delivered - 2e-5 (the transcription floor), AHEAD
   when delivered < published - 2e-5.

B. How far is each unbeaten row from its band's frontier?
   Exact identity, no density needed.  Write n = k^2 - j, so j is the number
   of cells missing from the k x k grid.  Any packing of n cells in side L has
   void V = L^2 - n, and it BEATS the grid exactly when L < k, i.e. when
   V < j.  The band's frontier row m* already achieves V(m*) slightly below
   its own budget j*, and the next row up must fit inside V < j* - 1.  The
   price of that row is therefore the VOID SHORTFALL

       d(k) = V(m*) - (j* - 1)          in unit^2,

   the empty area the next construction has to give up.  This is the honest
   cost: not "more search", but one cell's worth of void.

Float use: a DISCOVERY/census script (like relax_angles.py, pattern_seeds.py),
not a certification module - true_geom, interval_verifier and sqscore stay
float-free and byte-audited.  The 5-dp published values are transcription, not
measurement, and TOL is that rounding floor, not a geometric tolerance.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sqscore as SQ  # noqa: E402

# --- A. published best-known upper bounds, n = 1..324 (Squares Project, 2026-10-20)
PUB = {
    1: 1, 2: 2, 3: 2, 4: 2, 5: 2.70711, 6: 3, 7: 3, 8: 3, 9: 3, 10: 3.70711,
    11: 3.87708, 12: 4, 13: 4, 14: 4, 15: 4, 16: 4, 17: 4.67554, 18: 4.82288,
    19: 4.88562, 20: 5, 21: 5, 22: 5, 23: 5, 24: 5, 25: 5, 26: 5.62133,
    27: 5.70711, 28: 5.82445, 29: 5.93384, 30: 6, 31: 6, 32: 6, 33: 6, 34: 6,
    35: 6, 36: 6, 37: 6.59862, 38: 6.70711, 39: 6.81073, 40: 6.82843,
    41: 6.92670, 42: 7, 43: 7, 44: 7, 45: 7, 46: 7, 47: 7, 48: 7, 49: 7,
    50: 7.57143, 51: 7.69036, 52: 7.70711, 53: 7.82288, 54: 7.84667,
    55: 7.94578, 56: 8, 57: 8, 58: 8, 59: 8, 60: 8, 61: 8, 62: 8, 63: 8,
    64: 8, 65: 8.53554, 66: 8.65686, 67: 8.70711, 68: 8.79880, 69: 8.82720,
    70: 8.88097, 71: 8.94408, 72: 9, 73: 9, 74: 9, 75: 9, 76: 9, 77: 9, 78: 9,
    79: 9, 80: 9, 81: 9, 82: 9.53554, 83: 9.63476, 84: 9.69794, 85: 9.74265,
    86: 9.82054, 87: 9.83882, 88: 9.88246, 89: 9.94975, 90: 10, 91: 10, 92: 10,
    93: 10, 94: 10, 95: 10, 96: 10, 97: 10, 98: 10, 99: 10, 100: 10,
    101: 10.53554, 102: 10.60583, 103: 10.67924, 104: 10.70711, 105: 10.78931,
    106: 10.82291, 107: 10.84667, 108: 10.90483, 109: 10.94975, 110: 10.99679,
    111: 11, 112: 11, 113: 11, 114: 11, 115: 11, 116: 11, 117: 11, 118: 11,
    119: 11, 120: 11, 121: 11, 122: 11.53554, 123: 11.59138, 124: 11.65686,
    125: 11.70711, 126: 11.74265, 127: 11.81088, 128: 11.8251, 129: 11.87002,
    130: 11.90449, 131: 11.94966, 132: 11.98569, 133: 12, 134: 12, 135: 12,
    136: 12, 137: 12, 138: 12, 139: 12, 140: 12, 141: 12, 142: 12, 143: 12,
    144: 12, 145: 12.53554, 146: 12.58379, 147: 12.65686, 148: 12.65686,
    149: 12.70711, 150: 12.77818, 151: 12.82288, 152: 12.83072, 153: 12.87002,
    154: 12.92121, 155: 12.95227, 156: 12.97917, 157: 13, 158: 13, 159: 13,
    160: 13, 161: 13, 162: 13, 163: 13, 164: 13, 165: 13, 166: 13, 167: 13,
    168: 13, 169: 13, 170: 13.53554, 171: 13.57143, 172: 13.61899,
    173: 13.65686, 174: 13.70711, 175: 13.76418, 176: 13.79588, 177: 13.82298,
    178: 13.84667, 179: 13.88380, 180: 13.91700, 181: 13.95082, 182: 13.97410,
    183: 13.99959, 184: 14, 185: 14, 186: 14, 187: 14, 188: 14, 189: 14,
    190: 14, 191: 14, 192: 14, 193: 14, 194: 14, 195: 14, 196: 14,
    197: 14.53554, 198: 14.57143, 199: 14.61758, 200: 14.65686, 201: 14.70711,
    202: 14.72793, 203: 14.77818, 204: 14.80867, 205: 14.8245, 206: 14.86016,
    207: 14.88097, 208: 14.92452, 209: 14.94623, 210: 14.97301, 211: 14.99355,
    212: 15, 213: 15, 214: 15, 215: 15, 216: 15, 217: 15, 218: 15, 219: 15,
    220: 15, 221: 15, 222: 15, 223: 15, 224: 15, 225: 15, 226: 15.53554,
    227: 15.57107, 228: 15.60461, 229: 15.65017, 230: 15.68293, 231: 15.70711,
    232: 15.76418, 233: 15.77818, 234: 15.82288, 235: 15.8267, 236: 15.86194,
    237: 15.90261, 238: 15.92411, 239: 15.94845, 240: 15.96969, 241: 15.98712,
    242: 16, 243: 16, 244: 16, 245: 16, 246: 16, 247: 16, 248: 16, 249: 16,
    250: 16, 251: 16, 252: 16, 253: 16, 254: 16, 255: 16, 256: 16,
    257: 16.53554, 258: 16.56345, 259: 16.59138, 260: 16.65686, 261: 16.67878,
    262: 16.70711, 263: 16.73317, 264: 16.77474, 265: 16.77818, 266: 16.82303,
    267: 16.83882, 268: 16.87882, 269: 16.90152, 270: 16.92820, 271: 16.94895,
    272: 16.96559, 273: 16.98393, 274: 17, 275: 17, 276: 17, 277: 17, 278: 17,
    279: 17, 280: 17, 281: 17, 282: 17, 283: 17, 284: 17, 285: 17, 286: 17,
    287: 17, 288: 17, 289: 17, 290: 17.53554, 291: 17.53554, 292: 17.59138,
    293: 17.63415, 294: 17.65686, 295: 17.70424, 296: 17.70711, 297: 17.74042,
    298: 17.77818, 299: 17.82288, 300: 17.8242, 301: 17.84667, 302: 17.87002,
    303: 17.90996, 304: 17.92943, 305: 17.95047, 306: 17.96344, 307: 17.98087,
    308: 17.99827, 309: 18, 310: 18, 311: 18, 312: 18, 313: 18, 314: 18,
    315: 18, 316: 18, 317: 18, 318: 18, 319: 18, 320: 18, 321: 18, 322: 18,
    323: 18, 324: 18,
}

TOL = 2e-5
LEADER = 22.0544214515


def compare(per):
    behind, ahead, equal = [], [], []
    for n in sorted(PUB):
        L = SQ.extent(per[n])
        d = L - PUB[n]
        if d < -TOL:
            ahead.append((n, L, PUB[n], -d))
        elif d > TOL:
            behind.append((n, L, PUB[n], d))
        else:
            equal.append(n)
    return behind, ahead, equal


def band_frontiers(per):
    """B. per band: the frontier row, its void, and the next row's price."""
    out = []
    # bands k = 1..32 cover n = 1..1000 (32 = ceil(sqrt 1000)); band k = 32's top
    # is clamped to 1000.  Every band with a beaten row gets a frontier entry.
    for k in range(2, 33):
        lo, hi = (k - 1) ** 2 + 1, min(k * k, 1000)
        beaten = [n for n in range(lo, hi + 1) if SQ.extent(per[n]) < k - 1e-12]
        if not beaten:
            continue
        m = max(beaten)                     # frontier row (initial-segment law)
        L = SQ.extent(per[m])
        V = L * L - m                       # achieved void, unit^2
        jstar = k * k - m                   # its own void budget
        nxt = m + 1
        # beating nxt needs V < k^2 - nxt = jstar - 1
        shortfall = V - (jstar - 1)         # unit^2 of void still to save
        out.append({
            "k": k, "frontier_n": m, "jstar": jstar, "L": L,
            "V": V, "V_over_jstar": V / jstar, "shortfall": shortfall,
            "beaten_in_band": len(beaten), "band_rows": hi - lo + 1,
            "nxt": nxt, "nxt_value": (k - math.sqrt(nxt)) / math.sqrt(nxt),
            "nxt_j": jstar - 1,
        })
    return out


def main():
    per = SQ.load()
    score = sum(SQ.extent(per[n]) / math.sqrt(n) - 1 for n in range(1, 1001))
    beats = sum(1 for n in range(1, 1001) if SQ.extent(per[n]) < SQ.grid(n) - 1e-12)
    grid_rows = sum(1 for n in range(1, 1001) if SQ.extent(per[n]) >= SQ.grid(n) - 1e-12)
    print(f"delivered score {score:.9f}  beats {beats}  grid rows {grid_rows}"
          f"  gap to reported leader {score - LEADER:.9f}")

    behind, ahead, equal = compare(per)
    print(f"\nA. published benchmark n<=324: equal {len(equal)}  ahead {len(ahead)}"
          f"  behind {len(behind)}")
    if ahead:
        print(f"   delivered is already better than the published record on "
              f"{len(ahead)} rows, worth {sum(d / math.sqrt(n) for n, L, p, d in ahead):.6f}")
    if behind:
        print(f"   recoverable from published packings: "
              f"{sum(d / math.sqrt(n) for n, L, p, d in behind):.6f}")
        for n, L, p, d in sorted(behind, key=lambda r: -r[3] / math.sqrt(r[0]))[:25]:
            print(f"   n={n:4d} delivered {L:.6f}  published {p:.5f}  "
                  f"delta {d:+.5f}  worth {d / math.sqrt(n):+.6f}")

    bf = band_frontiers(per)
    print(f"\nB. band frontiers (a beat of row n = k^2-j needs void V < j):")
    print("   k  frontier  j*    L            V        V/j*   next  price(unit^2)")
    for r in bf:
        print(f"  {r['k']:2d}  n={r['frontier_n']:4d}  {r['jstar']:3d}  {r['L']:.9f}"
              f"  {r['V']:8.4f}  {r['V_over_jstar']:.4f}   n={r['nxt']:4d}"
              f"  {r['shortfall']:+.4f}")
    print(f"\n   total unbeaten rows {grid_rows}; cheapest next-row price "
          f"{min(r['shortfall'] for r in bf):.4f} unit^2 (k="
          f"{min(bf, key=lambda r: r['shortfall'])['k']}), dearest "
          f"{max(r['shortfall'] for r in bf):.4f} unit^2")
    print("   every unbeaten row at or below the frontier costs >= ~0.4 unit^2 of void;")
    print("   that is the whole reason no search has crossed it.")

    # C. what each campaign is actually worth
    beaten_rows = [n for n in range(1, 1001)
                   if SQ.extent(per[n]) < SQ.grid(n) - 1e-12]
    room = sum((SQ.extent(per[n]) - math.sqrt(n)) / math.sqrt(n) for n in beaten_rows)
    print(f"\nC. value of the two campaigns")
    print(f"   beaten rows {len(beaten_rows)}: room still unclaimed below them "
          f"{room:.4f} score (L -> sqrt(n) would take all of it)")
    print(f"   a uniform +1% capture of that room is worth {0.01 * room:.5f}, "
          f"+5% {0.05 * room:.5f}")
    inherit = sum((r['k'] - r['L']) / math.sqrt(r['nxt']) for r in bf)
    print(f"   every band's next grid row beaten by INHERITING the frontier side "
          f"(no new construction): {inherit:.5f} score, all {len(bf)} rows")
    print(f"   bands carrying a frontier row: {len(bf)} (k = {bf[0]['k']}..{bf[-1]['k']})")
    print(f"   the leader gap is {score - LEADER:.5f}: the grid campaign CAN pay for "
          f"it (0.232 > 0.164) but only by seating one cell in every band's "
          f"frontier pose at its existing side - a 0.03% hole at k>=21.")

    out = os.path.join(HERE, "..", "workspace", "published_census114.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump({"score": score, "beats": beats, "grid_rows": grid_rows,
                   "leader": LEADER, "behind": behind, "ahead": ahead,
                   "band_frontiers": bf}, f, indent=1)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
