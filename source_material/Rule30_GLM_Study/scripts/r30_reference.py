"""Reference Rule 30 simulator using a slow but obviously-correct algorithm."""
import numpy as np

def reference_center_column(N):
    """Return first N center-column cells of Rule 30, by direct simulation.
    
    Uses a dict-based row indexed by column position (can be negative).
    Boundary cells default to 0. At each step, the active region grows by 1
    cell on each side. This is O(N^2) but obviously correct.
    """
    # Use a Python list with offset; row[t] is the column-position-t cell.
    # Active columns at step t are in [-t, t].
    # Use a dict {col: val} for clarity.
    row = {0: 1}
    cc = np.zeros(N, dtype=np.uint8)
    cc[0] = 1
    for t in range(1, N):
        new_row = {}
        lo, hi = -t, t
        for c in range(lo, hi + 1):
            L = row.get(c - 1, 0)
            C = row.get(c, 0)
            R = row.get(c + 1, 0)
            new_row[c] = L ^ (C | R)
        row = new_row
        cc[t] = row.get(0, 0)
    return cc

if __name__ == "__main__":
    cc = reference_center_column(64)
    print("Reference (dict) first 64:", "".join(str(b) for b in cc))
    print("Wolfram's published first 32: 11011100110100100010110100110001")
    print("Match first 32:", "".join(str(b) for b in cc[:32]) == "11011100110100100010110100110001")
