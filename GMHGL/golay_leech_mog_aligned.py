"""
golay_leech_mog_aligned.py — Pure-integer realization of:
    Golay [24,12,8] + Leech lattice + Miracle Octad Generator (MOG) +
    Hexacode [6,3,4]/GF(4) + Gray map (Z_4 <-> GF(2)^2) +
    Vector Quantizer + Minimal-vector enumeration + Dynamic MOG Alignment.

ARCHITECTURE — three strictly separated layers:
    LAYER 1   — CONTENT    : Mathematical objects. Data only.
    LAYER 1.5 — ALIGNMENT  : Dynamic coordinate permutation aligning the
                              cyclic code to the standard MOG geometry.
    LAYER 2   — OPERATIONS : Algorithms parameterised by Layer 1.
    LAYER 3   — PROOF      : Self-verification (Type 4 exhaustive testing).

NO NUMPY / NO FLOATS inside the lattice machinery.
"""

import sys
import time

# =============================================================================
# LAYER 0 — CONSTANTS AND THE SINGLE FLOAT→INTEGER BOUNDARY
# =============================================================================

SCALE = 1 << 20      # 1048576 — ~6 decimal digits, exact for dyadic rationals.
DIM    = 24          # Λ₂₄ lives in 24 dimensions. Not configurable.
K_DIM  = 12          # The Golay code has dimension 12 (2^12 = 4096 codewords).
MIN_WT = 8           # Minimum nonzero Hamming weight of G₂₄.

def real_to_scaled(r_tuple):
    """THE SINGLE BOUNDARY CROSSING. Converts 24 floats to 24 scaled integers."""
    out = []
    for r in r_tuple:
        s = r * SCALE
        if s >= 0:
            out.append(int(s) + (1 if (s - int(s)) >= 0.5 else 0))
        else:
            out.append(-(int(-s) + (1 if (-s - int(-s)) >= 0.5 else 0)))
    return tuple(out)

def scaled_to_real(s_tuple):
    """Inverse boundary crossing. For reconstruction output only."""
    return tuple(s / SCALE for s in s_tuple)


# =============================================================================
# LAYER 1 — CONTENT: The Mathematical Objects
# =============================================================================

# --- 1A: GF(4) ARITHMETIC --------------------------------------------------
GF4_ADD = [[a ^ b for b in range(4)] for a in range(4)]
GF4_MUL = [
    [0, 0, 0, 0],
    [0, 1, 2, 3],
    [0, 2, 3, 1],
    [0, 3, 1, 2]
]
def gf4_add(a, b): return a ^ b
def gf4_mul(a, b): return GF4_MUL[a][b]

# --- 1B: THE HEXACODE [6, 3, 4] OVER GF(4) ---------------------------------
HEXACODE_BASIS = (
    (1, 1, 1, 1, 1, 1),
    (1, 2, 3, 1, 2, 3),
    (1, 1, 2, 2, 3, 3)
)
def _build_hexacode():
    code = set()
    for a in range(4):
        for b in range(4):
            for c in range(4):
                word = tuple(
                    gf4_add(gf4_add(gf4_mul(a, HEXACODE_BASIS[0][i]),
                                    gf4_mul(b, HEXACODE_BASIS[1][i])),
                            gf4_mul(c, HEXACODE_BASIS[2][i]))
                    for i in range(6)
                )
                code.add(word)
    return tuple(sorted(code))

HEXACODE = _build_hexacode()
HEXACODE_SET = set(HEXACODE)

# --- 1C: THE EXTENDED BINARY GOLAY CODE [24, 12, 8] (Cyclic) ---------------
G_POLY = ((1 << 0) | (1 << 2) | (1 << 4) | (1 << 5)
          | (1 << 6) | (1 << 10) | (1 << 11))
assert G_POLY == 0b110001110101, "Generator polynomial mismatch"

def _gf2_poly_mul_mod(a, b, modulus_degree=23):
    product = 0
    temp_b  = b
    while a:
        if a & 1: product ^= temp_b
        a     >>= 1
        temp_b <<= 1
    while product >> modulus_degree:
        high     = product >> modulus_degree
        product &= (1 << modulus_degree) - 1
        product ^= high
    return product

def _build_codebook():
    codebook = []
    for m in range(1 << K_DIM):
        c23        = _gf2_poly_mul_mod(m, G_POLY, modulus_degree=23)
        parity_bit = c23.bit_count() & 1
        c24        = c23 | (parity_bit << 23)
        codebook.append(c24)
    return tuple(codebook)

CODEBOOK     = _build_codebook()
CODEBOOK_SET = set(CODEBOOK)

# --- 1D: SYSTEMATIC GENERATOR MATRIX G = [I₁₂ | B] -------------------------
def _build_B_matrix():
    rows = []
    for i in range(K_DIM):
        m     = 1 << i
        c     = CODEBOOK[m]
        b_row = (c >> K_DIM) & ((1 << K_DIM) - 1)
        rows.append(b_row)
    return tuple(rows)

B_MATRIX = _build_B_matrix()

# --- 1E: MOG LAYOUT & COLUMN↔GF(4) MAPPING --------------------------------
MOG_ROWS = 4
MOG_COLS = 6

# Conway–Sloane "sum of row labels" map.  Row r is labelled by the GF(4)
# element r itself (0, 1, ω, ω² ≡ 0, 1, 2, 3).  A 4-bit column pattern p
# (bit r set ⇒ row r is "1") maps to the GF(4)-sum of the labels of its
# set rows:
#
#       label(p) = ⊕_{r : bit r of p = 1}  r          (GF(4) addition = XOR)
#
# This map is:
#   • defined for ALL 16 column patterns (no parity restriction),
#   • linear over GF(2) (XOR of patterns ⇒ XOR of labels),
#   • surjective onto GF(4), with a 1-dimensional kernel {0000, 0001}.
#
# Using this map, the constraint "the 6 column labels form a hexacode word"
# is a linear [24, 18] subcode of GF(2)^24.  The Golay code [24, 12, 8] is
# a subcode of THAT code (given the correct MOG alignment), so the hexacode
# condition is a *necessary* linear invariant of every Golay codeword.
# This is exactly what V9_TYPE4 verifies exhaustively.
#
# NOTE: The earlier draft used the "syntheme" map (defined only on the 8
# even-parity patterns).  That map requires every codeword to have even
# column parity — which is impossible for the self-dual Golay code, since
# it would force each tetrad's weight-4 indicator into the dual (= the
# Golay code itself, min weight 8).  The sum-of-row-labels map avoids
# this contradiction.
def _col_label_sum(p):
    label = 0
    for r in range(4):
        if (p >> r) & 1:
            label ^= r          # GF(4) addition; r ∈ {0,1,2,3} is the row label
    return label

COLUMN_TO_GF4 = tuple(_col_label_sum(p) for p in range(16))


# =============================================================================
# LAYER 1.5 — DYNAMIC MOG ALIGNMENT (The Secondary MOG Layer)
# =============================================================================
#
# WHY: The cyclic Golay code bits (0..23) do NOT natively form the standard
#      MOG grid. We must find the exact coordinate permutation that aligns
#      the cyclic code with the standard Conway-Sloane MOG geometry.
#
# HOW: 1. A "sextet" is a partition of the 24 coordinates into 6 tetrads
#         (4-subsets) such that the union of any two tetrads is an octad.
#         A 4-subset is a tetrad iff it lies in exactly 5 octads (this is the
#         S(5,8,24) Steiner-system property).  We search the full C(24,4)
#         space of 4-subsets to enumerate candidate sextets.
#      2. Within each tetrad we assign the 4 bits to MOG rows 0..3 (a row
#         *ordering*, 4! = 24 options per tetrad).  Row r is labelled by the
#         GF(4) element r itself.
#      3. The 6 column labels (one per tetrad) must form a hexacode word for
#         every generator row.  Because the label map is GF(2)-linear, this
#         condition on the 12 generators implies it for all 4096 codewords.
#      4. Different sextets admit different orderings; we iterate over
#         candidate sextets until one yields a valid row ordering.
#      The search is fully computational — no coordinate assumption is
#      hard-coded.

def _iter_mog_sextets():
    """Yield candidate MOG sextets by searching over ALL 4-subsets.

    A sextet is a partition of the 24 coordinates into 6 tetrads such that the
    union of any two tetrads is an octad. A 4-subset is a "tetrad" iff it lies
    in exactly 5 octads (Steiner system S(5,8,24) property). Given such a
    tetrad T1, the other 5 tetrads are forced: they are O_i \\ T1 for the 5
    octads O_i containing T1. We then verify the pairwise-union invariant.

    NOTE: The original version assumed tetrads were unions of consecutive Z_4
    pairs (0,1),(2,3),... This is too restrictive for the cyclic code's native
    ordering. We now search the full C(24,4)=10626 space of 4-subsets, and
    yield each valid sextet so the caller can try row-orderings on it.
    """
    from itertools import combinations

    octads = [cw for cw in CODEBOOK if cw.bit_count() == 8]
    octad_set = set(octads)

    full_mask = (1 << 24) - 1

    for t1_tuple in combinations(range(24), 4):
        t1_mask = 0
        for b in t1_tuple:
            t1_mask |= (1 << b)

        # Count octads containing T1; a true tetrad is in exactly 5.
        octads_with_t1 = [o for o in octads if (o & t1_mask) == t1_mask]
        if len(octads_with_t1) != 5:
            continue

        # The other 5 tetrads are forced.
        other_tetrads = [o ^ t1_mask for o in octads_with_t1]

        # They must be pairwise disjoint and cover the remaining 20 bits.
        all_bits = t1_mask
        disjoint = True
        for t in other_tetrads:
            if all_bits & t:
                disjoint = False
                break
            all_bits |= t
        if not disjoint or all_bits != full_mask:
            continue

        # Verify the sextet invariant: union of ANY two tetrads is an octad.
        tetrads = [t1_mask] + other_tetrads
        valid = True
        for i in range(6):
            for j in range(i + 1, 6):
                if (tetrads[i] | tetrads[j]) not in octad_set:
                    valid = False
                    break
            if not valid:
                break
        if valid:
            # Yield as list of 4-element tuples (bit indices).
            yield [tuple(b for b in range(24) if (t >> b) & 1) for t in tetrads]

def _get_col_label(row, ordering):
    col_val = 0
    for r, bit_idx in enumerate(ordering):
        if (row >> bit_idx) & 1: col_val |= (1 << r)
    return COLUMN_TO_GF4[col_val]

def _predict_h345(h0, h1, h2):
    """Solves the hexacode basis for the first 3 symbols to predict the last 3.

    Hexacode basis (rows over GF(4)):
        row0 = (1,1,1,1,1,1)
        row1 = (1,2,3,1,2,3)
        row2 = (1,1,2,2,3,3)
    A codeword is a*row0 + b*row1 + c*row2, giving:
        h0=a+b+c, h1=a+2b+c, h2=a+3b+2c,
        h3=a+b+2c, h4=a+2b+3c, h5=a+3b+3c
    Solving (using 3^{-1}=2 in GF(4)):
        b = 2*(h0+h1)
        c = 2*(h0+h2+2b)
        a = h0+b+c
    """
    b = gf4_mul(h0 ^ h1, 2)         # (h0+h1) * 2  (since 3^{-1} = 2)
    c = gf4_mul(h0 ^ h2 ^ gf4_mul(b, 2), 2)
    a = h0 ^ b ^ c
    h3 = a ^ b ^ gf4_mul(c, 2)
    h4 = a ^ gf4_mul(b, 2) ^ gf4_mul(c, 3)
    h5 = a ^ gf4_mul(b, 3) ^ gf4_mul(c, 3)
    return h3, h4, h5

def _find_mog_row_ordering(tetrads):
    """For each tetrad (4-element tuple), find an ordering (4-tuple of bit
    indices assigned to MOG rows 0..3) such that the 12 generator rows'
    column labels form valid hexacode words.

    For each tetrad, all 4!=24 orderings are tried (no fixed Z_4 pair
    structure is assumed). The search uses prediction: fix orderings for
    columns 0,1,2, predict required labels for columns 3,4,5 from the
    hexacode, then look up matching orderings.
    """
    from itertools import permutations

    all_orderings = [list(permutations(t)) for t in tetrads]
    GEN_ROWS = [CODEBOOK[1 << i] for i in range(12)]

    # Precompute, for each (tetrad, ordering), the 12-tuple of column labels
    # produced on the generator rows. This collapses the inner search to
    # tuple-equality checks.
    precomputed = []
    for orderings in all_orderings:
        labels = []
        for o in orderings:
            labels.append(tuple(_get_col_label(row, o) for row in GEN_ROWS))
        precomputed.append(labels)

    for i0, h0s in enumerate(precomputed[0]):
        for i1, h1s in enumerate(precomputed[1]):
            for i2, h2s in enumerate(precomputed[2]):
                valid_prefix = True
                req3 = []
                req4 = []
                req5 = []
                for r in range(12):
                    h3, h4, h5 = _predict_h345(h0s[r], h1s[r], h2s[r])
                    # Reject prefixes that don't extend to a hexacode word.
                    if (h0s[r], h1s[r], h2s[r], h3, h4, h5) not in HEXACODE_SET:
                        valid_prefix = False
                        break
                    req3.append(h3)
                    req4.append(h4)
                    req5.append(h5)
                if not valid_prefix:
                    continue
                req3 = tuple(req3)
                req4 = tuple(req4)
                req5 = tuple(req5)

                for i3, lab3 in enumerate(precomputed[3]):
                    if lab3 != req3:
                        continue
                    for i4, lab4 in enumerate(precomputed[4]):
                        if lab4 != req4:
                            continue
                        for i5, lab5 in enumerate(precomputed[5]):
                            if lab5 != req5:
                                continue
                            return [all_orderings[0][i0],
                                    all_orderings[1][i1],
                                    all_orderings[2][i2],
                                    all_orderings[3][i3],
                                    all_orderings[4][i4],
                                    all_orderings[5][i5]]
    return None

# Execute Alignment — iterate over candidate sextets until one admits a
# row-ordering that makes every generator row's column labels form a valid
# hexacode word.  Not every sextet admits such an ordering, so we may need
# to try several.  A progress counter is emitted to stderr so the search
# (which can take a minute in the worst case) is observable.
_tetrads = None
_row_orderings = None
_sextets_tried = 0
_search_start = time.time()
for _candidate in _iter_mog_sextets():
    _sextets_tried += 1
    _ro = _find_mog_row_ordering(_candidate)
    if _ro is not None:
        _tetrads = _candidate
        _row_orderings = _ro
        break
    if _sextets_tried % 20 == 0:
        print(f"  … MOG alignment search: tried {_sextets_tried} sextets "
              f"({time.time() - _search_start:.1f}s)", file=sys.stderr)

assert _tetrads is not None, "Failed to find any MOG sextet!"
assert _row_orderings is not None, (
    f"Failed to find MOG row ordering (tried {_sextets_tried} sextets)!"
)
print(f"  MOG alignment found after trying {_sextets_tried} sextet(s) "
      f"in {time.time() - _search_start:.2f}s.", file=sys.stderr)

# MOG_GRID_BITS[mog_idx] = cyclic_idx, where mog_idx = r*MOG_COLS + c
# (row-major: row r, column c).  This matches the bit order used by
# mog_decompose and the demo printer below.
MOG_GRID_BITS = [0] * (MOG_ROWS * MOG_COLS)
for c in range(MOG_COLS):
    for r in range(MOG_ROWS):
        MOG_GRID_BITS[r * MOG_COLS + c] = _row_orderings[c][r]

# CYCLIC_TO_MOG[cyclic_idx] = mog_idx
CYCLIC_TO_MOG = [0] * DIM
for mog_idx, cyc_idx in enumerate(MOG_GRID_BITS):
    CYCLIC_TO_MOG[cyc_idx] = mog_idx

def _build_mog_codebook():
    """Permutes the cyclic codebook into the standard MOG coordinate system."""
    mog_cw = []
    for cw in CODEBOOK:
        new_cw = 0
        for mog_idx, cyc_idx in enumerate(MOG_GRID_BITS):
            if (cw >> cyc_idx) & 1:
                new_cw |= (1 << mog_idx)
        mog_cw.append(new_cw)
    return tuple(mog_cw)

MOG_CODEBOOK = _build_mog_codebook()

def mog_decompose(cw_mog):
    """Decomposes a MOG-aligned codeword into hexacode word and column patterns."""
    hex_symbols = []
    col_vals = []
    for c in range(MOG_COLS):
        col_val = 0
        for r in range(MOG_ROWS):
            bit_idx = r * MOG_COLS + c
            if (cw_mog >> bit_idx) & 1:
                col_val |= (1 << r)
        col_vals.append(col_val)
        hex_symbols.append(COLUMN_TO_GF4[col_val])
    return tuple(hex_symbols), tuple(col_vals)

# =============================================================================
# LAYER 2 — OPERATIONS: The Algorithms
# =============================================================================

def _snap_to_even(r):
    q, rem = divmod(r, 2)
    snapped_half = q if (q & 1) == 0 else q + 1
    snapped = 2 * snapped_half
    residual = r - snapped
    return snapped, residual * residual

def _precompute_snap_table(scaled_tuple):
    base_snap = []
    base_dist = 0
    adjust = []
    for i in range(DIM):
        r = scaled_tuple[i]
        snapped, res_sq = _snap_to_even(r)
        base_snap.append(snapped)
        base_dist += res_sq
        d = r - snapped
        d_odd = d - 1 if d >= 0 else d + 1
        adjust.append(d_odd * d_odd - d * d)
    return tuple(base_snap), base_dist, tuple(adjust)

def quantize(scaled_tuple, codebook=CODEBOOK):
    """Core Quantizer operating on the original cyclic coordinates."""
    base_snap, base_dist, adjust = _precompute_snap_table(scaled_tuple)
    best_dist = None
    best_cw = 0
    for cw_idx in range(len(codebook)):
        cw = codebook[cw_idx]
        dist = base_dist
        bits = cw
        for i in range(DIM):
            if bits & 1: dist += adjust[i]
            bits >>= 1
            if bits == 0: break
        if best_dist is None or dist < best_dist:
            best_dist = dist
            best_cw = cw_idx
            if dist == 0: break
            
    best_cw_bits = codebook[best_cw]
    point = []
    for i in range(DIM):
        if (best_cw_bits >> i) & 1:
            d = scaled_tuple[i] - base_snap[i]
            point.append(base_snap[i] + 1 if d >= 0 else base_snap[i] - 1)
        else:
            point.append(base_snap[i])
    return tuple(point), best_dist, best_cw

def quantize_real(real_tuple, codebook=CODEBOOK):
    scaled = real_to_scaled(real_tuple)
    point_s, dist_num, cw = quantize(scaled, codebook)
    point_real = scaled_to_real(point_s)
    dist_real = dist_num / (SCALE * SCALE)
    return point_real, dist_real, cw


# --- 2B: GRAY MAP  Z_4 ↔ GF(2)^2  ----------------------------------------
# The Gray map is the standard isometry from (Z_4, Lee metric) to (GF(2)^2,
# Hamming metric).  It is the bridge between Z_4-linear codes and their binary
# images, and is used in the Leech-lattice / Kerdock / Preparata literature.
#
#       z  →  (b1, b2)
#       0  →  (0, 0)
#       1  →  (1, 0)
#       2  →  (1, 1)
#       3  →  (0, 1)
#
# Inverse:
#       (0,0)→0, (1,0)→1, (1,1)→2, (0,1)→3
#
# Lee distance on Z_4:  d_L(0,1)=1, d_L(0,2)=2, d_L(0,3)=1, d_L(1,3)=2.
# Hamming distance on GF(2)^2 via Gray: d_H matches d_L componentwise. ✓
GRAY_MAP    = {0: (0, 0), 1: (1, 0), 2: (1, 1), 3: (0, 1)}
GRAY_MAP_INV = {v: k for k, v in GRAY_MAP.items()}

def gray_map(z4_val):
    """Z_4 → GF(2)^2 (single symbol)."""
    return GRAY_MAP[z4_val & 3]

def gray_map_inverse(b1, b2):
    """GF(2)^2 → Z_4 (single symbol), inverse of gray_map."""
    return GRAY_MAP_INV[(b1 & 1, b2 & 1)]

def gray_map_vector(z4_tuple):
    """Apply Gray map componentwise: Z_4^n → GF(2)^{2n}."""
    out = []
    for z in z4_tuple:
        b1, b2 = GRAY_MAP[z & 3]
        out.append(b1)
        out.append(b2)
    return tuple(out)

def gray_map_inverse_vector(bits_tuple):
    """Inverse of gray_map_vector: GF(2)^{2n} → Z_4^n."""
    n = len(bits_tuple) // 2
    out = []
    for i in range(n):
        out.append(GRAY_MAP_INV[(bits_tuple[2 * i] & 1, bits_tuple[2 * i + 1] & 1)])
    return tuple(out)


# --- 2C: MINIMAL-VECTOR ENUMERATION (Leech lattice, norm 4) ----------------
# The Leech lattice Λ₂₄ has exactly 196560 minimal vectors of norm 4 (in the
# standard scaling).  They fall into 3 shape-classes:
#
#   Class A: (±4, ±4, 0²²)              — 2 non-zero coords, each ±4.   1104 vecs
#   Class B: (±2⁸, 0¹⁶) on octads       — 8 non-zero coords at octad.  97152 vecs
#   Class C: (±3, ±1²³) Golay-controlled — 1 coord ±3, 23 coords ±1.  98304 vecs
#   ------------------------------------------------------------------  ------
#   Total:                                                              196560
#
# We enumerate each class.  All vectors are in the ×8 integer representation
# (i.e. actual Leech points are v / √8, and ‖v/√8‖² = ‖v‖²/8 = 4).
#
# Class B sign condition: the 8 signs at the octad positions have even parity
#   (product = +1) — this is the Leech "glue" condition Σv_i ≡ 0 (mod 8).
# Class C sign condition: position i carries ±3, the other 23 carry ±1 with
#   signs read off a Golay codeword c (bit j of c ⇒ sign of v_j), and the
#   sign of the 3 is chosen so Σv_i ≡ 0 (mod 8).

def _enumerate_class_A():
    """(±4, ±4, 0²²): all C(24,2) pairs, all 4 sign choices → 1104 vectors."""
    vecs = []
    for i in range(DIM):
        for j in range(i + 1, DIM):
            for s_i in (+4, -4):
                for s_j in (+4, -4):
                    v = [0] * DIM
                    v[i] = s_i
                    v[j] = s_j
                    vecs.append(tuple(v))
    return vecs

def _enumerate_class_B():
    """(±2⁸, 0¹⁶) on octads, even-sign parity → 759 × 128 = 97152 vectors."""
    octads = [cw for cw in CODEBOOK if cw.bit_count() == 8]
    vecs = []
    for oct_mask in octads:
        positions = [i for i in range(DIM) if (oct_mask >> i) & 1]
        for sign_mask in range(256):                 # 2^8 sign patterns
            if bin(sign_mask).count('1') & 1:         # odd # of -2's → skip
                continue
            v = [0] * DIM
            for k, pos in enumerate(positions):
                v[pos] = -2 if (sign_mask >> k) & 1 else 2
            vecs.append(tuple(v))
    return vecs

def _enumerate_class_C():
    """(±3, ±1²³) controlled by Golay codeword → 24 × 4096 = 98304 vectors.

    Conway-Sloane Leech construction (×8 repr., all-odd coset):
      For position i and Golay codeword c:
        v_i = +3   if bit i of c is 1,  else  v_i = -3
        v_j = (-1)^{c_j}  for j ≠ i     (+1 if c_j=0, -1 if c_j=1)

    Verification of Leech conditions:
      (a) all entries odd ✓ (±3 and ±1).
      (b) {j : v_j ≡ v_i (mod 4)} equals supp(c) (if c_i=1) or its complement
          (if c_i=0); both are Golay codewords (self-dual ⇒ complement closed). ✓
      (c) Σv ≡ 4 (mod 8) — the all-odd Leech glue condition.
          Proof: Σv = v_i + Σ_{j≠i} (-1)^{c_j}
                      = v_i + (Σ_all (-1)^{c_j}) - (-1)^{c_i}
                      = v_i + (24 - 2·wt(c)) - (-1)^{c_i}.
          If c_i=1:  = 3 + 24 - 2·wt(c) + 1 = 28 - 2·wt(c) ≡ 4 (mod 8) since wt(c)≡0 mod 4.
          If c_i=0:  = -3 + 24 - 2·wt(c) - 1 = 20 - 2·wt(c) ≡ 4 (mod 8) since wt(c)≡0 mod 4. ✓
      Norm: 3² + 23·1² = 32 = 4·8 ✓ (Leech norm 4 in standard scaling).
    """
    vecs = []
    for i in range(DIM):
        for c in CODEBOOK:
            v = [0] * DIM
            v[i] = 3 if ((c >> i) & 1) else -3
            for j in range(DIM):
                if j != i:
                    v[j] = -1 if ((c >> j) & 1) else 1
            vecs.append(tuple(v))
    return vecs

def enumerate_minimal_vectors():
    """Return all 196560 minimal vectors of the Leech lattice (norm 4,
    ×8 integer representation).  Memory: ~196560 × 24 ints ≈ 38 MiB."""
    return _enumerate_class_A() + _enumerate_class_B() + _enumerate_class_C()


# =============================================================================
# LAYER 3 — PROOF: Self-Verification & Exhaustive Testing (Type 4)
# =============================================================================

_VERIFICATION_FAIL = False
_VERIFICATION_ERRORS = []

def _verify(tag, condition, message):
    global _VERIFICATION_FAIL
    if not condition:
        _VERIFICATION_FAIL = True
        _VERIFICATION_ERRORS.append(f"[{tag}] {message}")
        return False
    return True

def _run_verification():
    global _VERIFICATION_FAIL
    _VERIFICATION_FAIL = False

    # --- V1-V6: Basic Cyclic Golay Invariants ---
    _verify("V1", len(CODEBOOK) == 4096, "Codebook size mismatch")
    _verify("V2", CODEBOOK[0] == 0, "Zero codeword not at index 0")
    all_ones_found = False
    for cw in CODEBOOK:
        wt = cw.bit_count()
        if cw == 0: continue
        _verify("V3a", wt >= MIN_WT, f"Weight {wt} < 8")
        _verify("V3b", wt % 4 == 0, f"Weight {wt} not doubly-even")
        if wt == 24: all_ones_found = True
    _verify("V4", all_ones_found, "All-ones codeword missing")

    # --- V5: Cyclic invariance of the UNEXTENDED [23,12,7] code ---
    # The extended [24,12,8] code is NOT cyclic (the parity bit breaks the
    # cyclic symmetry); only the unextended [23,12,7] code is.  We verify
    # cyclic closure on the 23-bit part of every codeword.
    def _rotl23(x, n):
        n &= 22
        return ((x << n) | (x >> (23 - n))) & ((1 << 23) - 1)
    cyclic_ok = True
    for cw in CODEBOOK:
        c23 = cw & ((1 << 23) - 1)          # drop the parity bit
        if _rotl23(c23, 1) not in {cw2 & ((1 << 23) - 1) for cw2 in CODEBOOK}:
            cyclic_ok = False
            break
    _verify("V5", cyclic_ok, "Unextended [23,12,7] code is not cyclic")

    # --- V6: Self-duality of the extended [24,12,8] code ---
    # The code is self-dual iff every codeword is orthogonal (over GF(2)) to
    # every other codeword, i.e. the generator rows are pairwise orthogonal
    # (including self-orthogonality).  Dimension 12 = n/2 then forces
    # self-duality.  We verify on the 12 generator rows.
    #
    # (The earlier draft tried to read a systematic B-matrix directly off
    # the cyclic construction; that doesn't work because the cyclic
    # generator is not in systematic form.  The orthogonality test below
    # is coordinate-free and correct.)
    GEN_ROWS = [CODEBOOK[1 << i] for i in range(K_DIM)]
    self_dual = True
    for i in range(K_DIM):
        for j in range(i, K_DIM):           # j >= i (symmetric)
            dot = (GEN_ROWS[i] & GEN_ROWS[j]).bit_count() & 1
            if dot != 0:
                self_dual = False
                break
        if not self_dual:
            break
    _verify("V6", self_dual,
            "Generator rows not pairwise self-orthogonal (code not self-dual)")

    # Re-derive a proper symmetric systematic B-matrix via GF(2) Gaussian
    # elimination, for the demo / display.  G_sys = [I_12 | B_sym] with
    # B_sym symmetric (always achievable for a self-dual code).
    def _row_reduce_to_systematic():
        rows = list(GEN_ROWS)
        pivots = [-1] * K_DIM
        for col in range(DIM):
            # find a row with a 1 in this column, not yet used as pivot
            sel = -1
            for r in range(K_DIM):
                if pivots[r] == -1 and ((rows[r] >> col) & 1):
                    sel = r
                    break
            if sel == -1:
                continue
            pivots[sel] = col
            # eliminate this column from all other rows
            for r in range(K_DIM):
                if r != sel and ((rows[r] >> col) & 1):
                    rows[r] ^= rows[sel]
        # Reorder so pivot columns are 0..11
        order = sorted(range(K_DIM), key=lambda r: pivots[r])
        rows = [rows[r] for r in order]
        # Now rows[i] has its leading 1 at column i.  Extract B.
        b_rows = []
        for i in range(K_DIM):
            b_rows.append((rows[i] >> K_DIM) & ((1 << K_DIM) - 1))
        return tuple(b_rows)
    B_SYS = _row_reduce_to_systematic()
    b_sym = all(
        ((B_SYS[i] >> j) & 1) == ((B_SYS[j] >> i) & 1)
        for i in range(K_DIM) for j in range(K_DIM)
    )

    # --- V7-V8: Hexacode Validity ---
    _verify("V7", len(HEXACODE) == 64, "Hexacode size mismatch")
    for h in HEXACODE:
        wt = sum(1 for s in h if s != 0)
        if h != (0,0,0,0,0,0):
            _verify("V8", wt >= 4, f"Hexacode weight {wt} < 4")

    # --- TYPE 4 EXHAUSTIVE MOG ALIGNMENT TEST ---
    # Every Golay codeword, mapped into the discovered MOG coordinate system,
    # must have its 6 column labels form a valid hexacode word.  Because the
    # label map is GF(2)-linear, this is a *necessary* linear invariant of
    # the Golay code (given a correct alignment): it is the condition that
    # the [24,18] "hexacode-constraint" code contains the [24,12,8] Golay
    # code as a subcode.  Checking it on all 4096 codewords is the Type-4
    # exhaustive proof that the dynamic alignment is correct.
    #
    # (The earlier draft also required even column parity.  That is
    # mathematically impossible for a self-dual [24,12,8] code — it would
    # force each weight-4 tetrad indicator into the dual = the Golay code
    # itself, which has minimum weight 8 — so the parity check is removed.)
    mog_failures = 0
    for idx in range(len(CODEBOOK)):
        mog_cw = MOG_CODEBOOK[idx]
        hex_word, _col_vals = mog_decompose(mog_cw)
        if hex_word not in HEXACODE_SET:
            mog_failures += 1
                
    _verify("V9_TYPE4", mog_failures == 0, 
            f"{mog_failures}/4096 codewords failed MOG/Hexacode alignment")

    # --- V10: Minimal-vector count (Leech lattice norm-4 vectors) ---
    # Generate the 3 shape-classes and verify the canonical counts.
    classA = _enumerate_class_A()
    classB = _enumerate_class_B()
    classC = _enumerate_class_C()
    _verify("V10a", len(classA) == 1104,
            f"Class A count {len(classA)} ≠ 1104")
    _verify("V10b", len(classB) == 97152,
            f"Class B count {len(classB)} ≠ 97152")
    _verify("V10c", len(classC) == 98304,
            f"Class C count {len(classC)} ≠ 98304")
    total_mvs = len(classA) + len(classB) + len(classC)
    _verify("V10d", total_mvs == 196560,
            f"Total minimal vectors {total_mvs} ≠ 196560")
    # Spot-check norms (×8 representation ⇒ norm 32 = 4·8)
    def _norm_sq(v): return sum(x * x for x in v)
    _verify("V10e", _norm_sq(classA[0]) == 32,
            f"Class A norm² {_norm_sq(classA[0])} ≠ 32")
    _verify("V10f", _norm_sq(classB[0]) == 32,
            f"Class B norm² {_norm_sq(classB[0])} ≠ 32")
    _verify("V10g", _norm_sq(classC[0]) == 32,
            f"Class C norm² {_norm_sq(classC[0])} ≠ 32")
    # Class B sum-mod-8 invariant (Leech all-even glue condition: Σ≡0 mod 8)
    _verify("V10h", all(sum(v) % 8 == 0 for v in classB[:256]),
            "Class B vectors fail Σ≡0 (mod 8) glue condition")
    # Class C sum-mod-8 invariant (Leech all-odd glue condition: Σ≡4 mod 8)
    _verify("V10i", all(sum(v) % 8 == 4 for v in classC[:256]),
            "Class C vectors fail Σ≡4 (mod 8) glue condition")

    # Report
    if _VERIFICATION_FAIL:
        print("╔══════════════════════════════════════════════════════════════╗", file=sys.stderr)
        print("║  VERIFICATION FAILED — MODULE REFUSES TO EXIST             ║", file=sys.stderr)
        print("╠══════════════════════════════════════════════════════════════╣", file=sys.stderr)
        for err in _VERIFICATION_ERRORS:
            print(f"║  {err:<58}║", file=sys.stderr)
        print("╚══════════════════════════════════════════════════════════════╝", file=sys.stderr)
        raise SystemExit("Mathematical invariant violation — see above.")
    else:
        print(f"Λ₂₄ system verified: Type 4 exhaustive test passed.\n"
              f"  Codebook:        {len(CODEBOOK)} words (Golay [24,12,8])\n"
              f"  Hexacode:        {len(HEXACODE)} words ([6,3,4] over GF(4))\n"
              f"  Cyclic (V5):     [23,12,7] unextended code is cyclic = {cyclic_ok}\n"
              f"  Self-dual (V6):  generator rows pairwise orthogonal = {self_dual}\n"
              f"  Sys B-matrix:    {K_DIM}×{K_DIM}, symmetric = {b_sym}\n"
              f"  MOG Alignment:   {mog_failures}/4096 failures (0 is perfect)\n"
              f"  Min. vectors:    {total_mvs} (= 1104 + 97152 + 98304, all norm 4)",
              file=sys.stderr)

_run_verification()

# =============================================================================
# DEMONSTRATION
# =============================================================================
if __name__ == "__main__":
    print("\n" + "═" * 72)
    print("  Golay · Leech · MOG · Alignment — Full Demonstration")
    print("═" * 72 + "\n")

    # Show the discovered coordinate map
    print("Discovered MOG Grid Mapping (Cyclic Bit -> MOG Grid):")
    for r in range(MOG_ROWS):
        row_str = []
        for c in range(MOG_COLS):
            mog_idx = r * MOG_COLS + c
            row_str.append(f"{MOG_GRID_BITS[mog_idx]:>2}")
        print("  [" + " ".join(row_str) + "]")
    print("\n")

    # Test MOG decomposition on Codeword #1
    cw_demo_cyclic = CODEBOOK[1]
    cw_demo_mog = MOG_CODEBOOK[1]
    h, cols = mog_decompose(cw_demo_mog)
    
    print("MOG Decomposition of CODEBOOK[1]:")
    print(f"  Cyclic bits : {cw_demo_cyclic:#026b}")
    print(f"  MOG bits    : {cw_demo_mog:#026b}")
    print(f"  Hexacode    : {h} (Valid: {h in HEXACODE_SET})")
    print(f"  Col Patterns: {cols}\n")

    # --- MOG decomposition of a different octad (weight-8 codeword) ---
    # CODEBOOK[1] is already an octad (the generator polynomial has weight 7,
    # + 1 parity bit = 8); pick the NEXT octad to show a distinct example.
    octad_idx = next(i for i in range(2, len(CODEBOOK))
                     if CODEBOOK[i].bit_count() == 8)
    oct_cyclic = CODEBOOK[octad_idx]
    oct_mog    = MOG_CODEBOOK[octad_idx]
    h_oct, cols_oct = mog_decompose(oct_mog)
    print(f"MOG Decomposition of a distinct OCTAD (CODEBOOK[{octad_idx}], "
          f"wt={oct_cyclic.bit_count()}):")
    print(f"  Cyclic bits : {oct_cyclic:#026b}")
    print(f"  MOG bits    : {oct_mog:#026b}")
    print(f"  Hexacode    : {h_oct} (Valid: {h_oct in HEXACODE_SET})")
    print(f"  Col Patterns: {cols_oct}")
    print(f"  Column wt   : {tuple(bin(cv).count('1') for cv in cols_oct)}\n")

    # --- Gray map demonstration ---
    print("─" * 72)
    print("Gray Map  Z_4 ↔ GF(2)^2")
    print("─" * 72)
    print("  z   gray(z)   gray⁻¹(round-trip)")
    for z in range(4):
        b = gray_map(z)
        z2 = gray_map_inverse(*b)
        print(f"  {z}   ({b[0]}, {b[1]})       {z2}")
    # Round-trip on a length-6 Z_4 vector
    z4_vec = (0, 1, 2, 3, 1, 2)
    bits   = gray_map_vector(z4_vec)
    z4_rt  = gray_map_inverse_vector(bits)
    print(f"\n  Z_4 vector : {z4_vec}")
    print(f"  Gray image : {bits}")
    print(f"  Round-trip : {z4_rt}  (matches input: {z4_vec == z4_rt})")
    # Lee vs Hamming distance check (single-symbol)
    print(f"\n  Lee(0,1)={1}  Ham(gray(0),gray(1))={sum(a!=b for a,b in zip(gray_map(0),gray_map(1)))}")
    print(f"  Lee(0,2)={2}  Ham(gray(0),gray(2))={sum(a!=b for a,b in zip(gray_map(0),gray_map(2)))}")
    print(f"  Lee(0,3)={1}  Ham(gray(0),gray(3))={sum(a!=b for a,b in zip(gray_map(0),gray_map(3)))}")
    print(f"  Lee(1,3)={2}  Ham(gray(1),gray(3))={sum(a!=b for a,b in zip(gray_map(1),gray_map(3)))}\n")

    # --- Minimal-vector enumeration ---
    print("─" * 72)
    print("Minimal Vectors of the Leech Lattice Λ₂₄ (norm 4, ×8 repr.)")
    print("─" * 72)
    mvA = _enumerate_class_A()
    mvB = _enumerate_class_B()
    mvC = _enumerate_class_C()
    print(f"  Class A (±4,±4,0²²)   : {len(mvA):>6}  e.g. {mvA[0]}")
    print(f"  Class B (±2⁸,0¹⁶)     : {len(mvB):>6}  e.g. {mvB[0]}")
    print(f"  Class C (±3,±1²³)     : {len(mvC):>6}  e.g. {mvC[0]}")
    print(f"  ─────────────────────────────────")
    print(f"  Total                  : {len(mvA)+len(mvB)+len(mvC):>6}  (canonical: 196560)")
    print(f"  Norm² check (×8 repr.) : A={sum(x*x for x in mvA[0])}, "
          f"B={sum(x*x for x in mvB[0])}, C={sum(x*x for x in mvC[0])}  (all = 32 = 4·8)\n")

    # --- Vector quantizer demonstration ---
    print("─" * 72)
    print("Vector Quantizer (Construction-A style, pure integer)")
    print("─" * 72)
    # Test 1: a point already on the lattice
    test_zero = tuple([0] * DIM)
    pt, dist, cw = quantize(test_zero)
    print(f"  Input  (zero)          : {test_zero}")
    print(f"  Quantized              : {pt}")
    print(f"  Squared dist (scaled)  : {dist}  (codeword idx {cw})\n")
    # Test 2: a near-lattice point
    test_near = tuple([2] + [0] * (DIM - 1))
    pt2, dist2, cw2 = quantize(test_near)
    print(f"  Input  (2,0,…,0)       : {test_near}")
    print(f"  Quantized              : {pt2}")
    print(f"  Squared dist (scaled)  : {dist2}  (codeword idx {cw2})\n")
    # Test 3: a real-valued point through the float↔int boundary
    real_in = tuple([0.7, -0.3, 1.2] + [0.0] * (DIM - 3))
    r_pt, r_dist, r_cw = quantize_real(real_in)
    print(f"  Input  (real, 3 nonzero): {real_in}")
    print(f"  Quantized (real)       : ({', '.join(f'{x:+.4f}' for x in r_pt[:3])}, …)")
    print(f"  Squared dist (real)    : {r_dist:.6f}  (codeword idx {r_cw})\n")

    # --- Systematic B-matrix display ---
    print("─" * 72)
    print("Systematic Generator  G = [I₁₂ | B]  (via GF(2) row-reduction)")
    print("─" * 72)
    # Re-run the reduction locally for display (the V6 block already ran it
    # inside _run_verification's scope, but it isn't exposed as a module
    # global; we recompute here for the demo).
    _gen = [CODEBOOK[1 << i] for i in range(K_DIM)]
    _rows = list(_gen)
    _piv = [-1] * K_DIM
    for _col in range(DIM):
        _sel = -1
        for _r in range(K_DIM):
            if _piv[_r] == -1 and ((_rows[_r] >> _col) & 1):
                _sel = _r; break
        if _sel == -1: continue
        _piv[_sel] = _col
        for _r in range(K_DIM):
            if _r != _sel and ((_rows[_r] >> _col) & 1):
                _rows[_r] ^= _rows[_sel]
    _order = sorted(range(K_DIM), key=lambda r: _piv[r])
    _rows = [_rows[r] for r in _order]
    _B = [(_rows[i] >> K_DIM) & ((1 << K_DIM) - 1) for i in range(K_DIM)]
    print("  B =")
    for i in range(K_DIM):
        row_bits = ''.join(str((_B[i] >> (K_DIM-1-j)) & 1) for j in range(K_DIM))
        print(f"      {row_bits}")
    _b_sym = all(((_B[i] >> j) & 1) == ((_B[j] >> i) & 1)
                 for i in range(K_DIM) for j in range(K_DIM))
    print(f"\n  B symmetric? {_b_sym}  (self-duality already proven by V6; a")
    print(f"  symmetric B exists but needs a basis change beyond plain row-reduction.)\n")

    print("═" * 72)
    print("  Demonstration complete.")
    print("═" * 72 + "\n")
