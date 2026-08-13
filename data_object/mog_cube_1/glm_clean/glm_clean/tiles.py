"""
tiles.py — GolayHex-Upsilon: the MOG as an irregular-tile computational system.

THE GEOMETRY
------------
A tile is a cube.  Its six faces are the six columns of the MOG, so a tile
carries 6 x 4 = 24 cells, which is exactly one MOG object.  Each face therefore
has a state

        (score in GF(4), parity in F2)

and, by the MOG construction in `hexacode.py`, a *lawful* tile is one whose six
face scores form a hexacode word and whose six face parities agree.  This is
the reading of "each grid is the face of a cube" that survives contact with the
arithmetic: the cube is realised by the hexacode, one GF(4) digit per face.

The other reading -- six whole 4x6 MOG grids as the six faces of a cube -- does
not close, and the reason is elementary and worth recording: a cube face is a
square, so its four sides are interchangeable, while a 4x6 grid has two sides
of length 6 and two of length 4.  No consistent edge-matching exists.  See
`why_not_six_grids()`.

THE PRICES
----------
Every tile prints a receipt, in exact rational arithmetic:

    TAX_MOG(v) = HW(v) . Q  +  q(v) . Q          q(v) = coset leader weight

The first term is the lawful cost of distinction; the second is the *closure
failure*, which is 0 exactly on codewords and is bounded by 4Q because the
Golay code has covering radius 4.  q(v) <= 3 is transient (the substrate can
name the failing cells and heal them); q(v) = 4 is persistent (six leaders tie,
so no repair is preferred) and only those tiles may anchor.

WHAT IS STIPULATED
------------------
Following the labelling discipline: [def] definition, [stip] stipulation,
[thm] proved or exhaustively verified here, [open] not established.

  * Pi = pi                                        [stip]
  * B = 10 (or the calibrated B = 8Q)              [stip]
  * the 13 sinks, and the number 13 itself         [stip]  -- and see
    `thirteen_report()`, which records that 13 divides neither |M24| nor any
    of the code's parameters, so nothing in the substrate forces it
  * Y_CONST (the nesting surcharge)                [stip], and its numeric
    value 0.232150 comes from a file that is not in this repository, so it is
    reported as UNVERIFIABLE rather than assumed
  * the Fibonacci substitution that produces phi   [stip] -- phi is put in by
    the choice of substitution; nothing in the Golay/MOG arithmetic forces it
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from math import isqrt
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .hexacode import (MOG_CODE, column_bits, column_parity, column_score,
                       decompose, gf_add, gf_mul, hexacode, top_row_parity)
from .substrate import SUBSTRATE, popcount

# ══════════════════════════════════════════════════════════════════════════════
# 1.  Exact constants
# ══════════════════════════════════════════════════════════════════════════════

PREC = 10 ** 60


def _sqrt_frac(n: int) -> Tuple[Fraction, Fraction]:
    """Rational lower and upper bounds for sqrt(n), to 60 digits."""
    r = isqrt(n * PREC * PREC)
    return Fraction(r, PREC), Fraction(r + 1, PREC)


def _e_bounds(terms: int = 60) -> Tuple[Fraction, Fraction]:
    """Rational lower/upper bounds for e = sum 1/k!."""
    s = Fraction(0)
    fact = 1
    for k in range(terms):
        if k:
            fact *= k
        s += Fraction(1, fact)
    tail = Fraction(2, fact * terms)          # crude but ample bound
    return s, s + tail


_C = SUBSTRATE.get_constants(60)
PI: Fraction = _C["PI"]
Y: Fraction = _C["Y"]
Q: Fraction = _C["Q"]
B: Fraction = _C["B"]                          # 10, stipulated
B_CAL: Fraction = 8 * Q                        # the calibrated budget

_PHI_LO, _PHI_HI = _sqrt_frac(5)
PHI: Fraction = (1 + _PHI_LO) / 2
_E_LO, _E_HI = _e_bounds()
E: Fraction = _E_LO


def wobble_bounds() -> Tuple[Fraction, Fraction]:
    """Interval bounds for the fractional part of pi.phi.e."""
    lo = PI * ((1 + _PHI_LO) / 2) * _E_LO
    hi = PI * ((1 + _PHI_HI) / 2) * _E_HI
    n_lo, n_hi = int(lo), int(hi)
    if n_lo != n_hi:                            # interval straddles an integer
        raise RuntimeError("insufficient precision for the wobble")
    return lo - n_lo, hi - n_lo


WOBBLE: Fraction = wobble_bounds()[0]
N_SINKS = 13                                    # [stip]
SINK_L: Fraction = WOBBLE / N_SINKS


# ══════════════════════════════════════════════════════════════════════════════
# 2.  The code, its syndromes, and the tax
# ══════════════════════════════════════════════════════════════════════════════

class MogSyndromes:
    """Syndrome table of the MOG-presented Golay code (self-dual, so the code
    is its own parity check)."""

    def __init__(self) -> None:
        self.basis = list(MOG_CODE.basis)
        self.leader: Dict[int, List[int]] = {}
        for w in range(5):
            for pat in self._patterns(w):
                s = self.syndrome(pat)
                cur = self.leader.get(s)
                if cur is None:
                    self.leader[s] = [pat]
                elif popcount(cur[0]) == w:
                    cur.append(pat)
        assert len(self.leader) == 4096, len(self.leader)

    @staticmethod
    def _patterns(w: int, n: int = 24) -> Iterable[int]:
        if w == 0:
            yield 0
            return
        idx = list(range(w))
        while True:
            v = 0
            for i in idx:
                v |= 1 << i
            yield v
            for k in range(w - 1, -1, -1):
                if idx[k] != k + n - w:
                    idx[k] += 1
                    for j in range(k + 1, w):
                        idx[j] = idx[j - 1] + 1
                    break
            else:
                return

    def syndrome(self, v: int) -> int:
        s = 0
        for i, b in enumerate(self.basis):
            if popcount(v & b) & 1:
                s |= 1 << i
        return s

    def leader_weight(self, v: int) -> int:
        return popcount(self.leader[self.syndrome(v)][0])

    def n_leaders(self, v: int) -> int:
        return len(self.leader[self.syndrome(v)])

    def is_codeword(self, v: int) -> bool:
        return self.syndrome(v) == 0

    def snap(self, v: int) -> Tuple[Optional[int], int, int]:
        """(repaired tile or None if ambiguous, leader weight, #leaders)."""
        ls = self.leader[self.syndrome(v)]
        q = popcount(ls[0])
        if len(ls) == 1:
            return v ^ ls[0], q, 1
        return None, q, len(ls)


SYN = MogSyndromes()


def tax(v: int) -> Fraction:
    """The plain UBP tax: HW.Y + ||v||^2/8 = HW.Q for a 0/1 object."""
    return popcount(v) * Q


def syndrome_penalty(v: int) -> Fraction:
    """The closure-failure charge: 0 on codewords, at most 4Q anywhere."""
    return SYN.leader_weight(v) * Q


def tax_mog(v: int) -> Fraction:
    """The MOG-aware tax: lawful cost plus closure failure."""
    return tax(v) + syndrome_penalty(v)


def nrci(t: Fraction, budget: Fraction = B) -> Fraction:
    return budget / (budget + t)


def nrci_calibrated(weight: int) -> Fraction:
    """With the budget calibrated to B = 8Q the ladder is Q-free."""
    return Fraction(8, 8 + weight)


# ══════════════════════════════════════════════════════════════════════════════
# 3.  The tile taxonomy
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Tile:
    v: int

    @property
    def weight(self) -> int:
        return popcount(self.v)

    @property
    def lawful(self) -> bool:
        return SYN.is_codeword(self.v)

    @property
    def defect(self) -> int:
        return SYN.leader_weight(self.v)

    @property
    def persistent(self) -> bool:
        """A weight-4 defect: six leaders tie, so no repair is preferred."""
        return self.defect == 4

    @property
    def faces(self) -> Tuple[Tuple[int, int], ...]:
        """(score, parity) for each of the six faces."""
        return tuple((column_score(column_bits(self.v, c)),
                      column_parity(column_bits(self.v, c))) for c in range(6))

    @property
    def hex_word(self) -> Tuple[int, ...]:
        return tuple(s for s, _p in self.faces)

    def receipt(self) -> Dict[str, object]:
        return {
            "kind": self.kind(),
            "HW": self.weight,
            "defect_q": self.defect,
            "n_leaders": SYN.n_leaders(self.v),
            "TAX": tax(self.v),
            "penalty": syndrome_penalty(self.v),
            "TAX_MOG": tax_mog(self.v),
            "NRCI": nrci(tax_mog(self.v)),
            "NRCI_calibrated": nrci_calibrated(self.weight),
            "faces": self.faces,
        }

    def kind(self) -> str:
        if self.v == 0:
            return "T0 vacuum"
        if self.lawful:
            return f"T_reg(w={self.weight})"
        if self.persistent:
            return "T_def(4) persistent / anchor"
        return f"T_def({self.defect}) transient"


# ══════════════════════════════════════════════════════════════════════════════
# 4.  The cube and its matching rule
# ══════════════════════════════════════════════════════════════════════════════
#
# Faces 0..5 are +x, -x, +y, -y, +z, -z, i.e. face 2d is the positive face of
# axis d and face 2d+1 the negative one.  Two cubes glued along axis d meet on
# the +d face of the lower and the -d face of the upper.

AXES = 3
OPPOSITE = {0: 1, 1: 0, 2: 3, 3: 2, 4: 5, 5: 4}


def faces_match(a: Tile, b: Tile, axis: int) -> bool:
    """`b` sits on the +axis side of `a`.

    The shared interface is closed when the two faces carry the same hexacode
    digit (the geometry agrees) and opposite parity (the charges cancel).
    """
    fa = a.faces[2 * axis]
    fb = b.faces[2 * axis + 1]
    return fa[0] == fb[0] and fa[1] != fb[1]


def lawful_tiles() -> List[Tile]:
    return [Tile(w) for w in MOG_CODE.words]


def count_chain(n: int) -> int:
    """Legal 1-D chains of n lawful tiles, counted exactly by transfer."""
    tiles = lawful_tiles()
    # state = (digit on the exposed +x face, parity of the tile)
    from collections import Counter
    cur = Counter()
    for t in tiles:
        cur[t.faces[0]] += 1
    for _ in range(n - 1):
        nxt = Counter()
        # index tiles by their -x face
        by_minus: Dict[Tuple[int, int], List[Tile]] = {}
        for t in tiles:
            by_minus.setdefault(t.faces[1], []).append(t)
        for state, k in cur.items():
            s, p = state
            for t in by_minus.get((s, 1 - p), ()):
                nxt[t.faces[0]] += k
        cur = nxt
    return sum(cur.values())


# -- the hexacode layer is MDS, and that is what makes the tiling compute ----

def information_sets() -> Dict[str, object]:
    """Is every triple of faces an information set?  (MDS: d = n - k + 1.)"""
    from itertools import combinations
    H = hexacode()
    out = {}
    for tri in combinations(range(6), 3):
        seen = {tuple(h[i] for i in tri) for h in H}
        out[str(tri)] = len(seen) == 64
    return {"all_triples_are_information_sets": all(out.values()),
            "per_triple": out,
            "n_words": len(H)}


def _incoming_table() -> Dict[Tuple[int, int, int], Tuple[int, ...]]:
    """The 3-D update rule: the three incoming face digits fix the tile.

    Faces 1, 3, 5 are the -x, -y, -z faces (what the neighbours hand us) and
    faces 0, 2, 4 are the +x, +y, +z faces (what we hand on).  Because the
    hexacode is MDS, the three incoming digits determine the outgoing three
    exactly: at the hexacode layer the assembly is a deterministic, reversible
    three-dimensional automaton.
    """
    tab: Dict[Tuple[int, int, int], Tuple[int, ...]] = {}
    for h in hexacode():
        key = (h[1], h[3], h[5])
        assert key not in tab, "faces 1,3,5 are not an information set"
        tab[key] = h
    return tab


UPDATE = _incoming_table()


def count_hex_assignments(nx: int, ny: int, nz: int) -> int:
    """Exact number of legal hexacode assignments to an nx x ny x nz box.

    Profile dynamic programming over the cells in (z, y, x) order.  Exact
    count, no sampling.
    """
    from collections import defaultdict
    L = nx * ny
    H = hexacode()
    states: Dict[object, int] = {((), (), None): 1}
    for z in range(nz):
        for y in range(ny):
            for x in range(nx):
                nxt: Dict[object, int] = defaultdict(int)
                for (dys, dzs, dx), k in states.items():
                    need_y = dys[0] if (y > 0 and len(dys) == nx) else None
                    need_z = dzs[0] if (z > 0 and len(dzs) == L) else None
                    need_x = dx if x > 0 else None
                    for h in H:
                        if need_x is not None and h[1] != need_x:
                            continue
                        if need_y is not None and h[3] != need_y:
                            continue
                        if need_z is not None and h[5] != need_z:
                            continue
                        ndys = (dys + (h[2],))[-nx:]
                        ndzs = (dzs + (h[4],))[-L:]
                        nxt[(ndys, ndzs, h[0])] += k
                states = dict(nxt)
    return sum(states.values())


def count_box(nx: int, ny: int, nz: int) -> int:
    """Legal fillings of the box by lawful tiles (exact).

    Each (hexacode word, parity) is carried by exactly 32 of the 4096 lawful
    tiles, and the parities alternate, so the tile count is the hexacode count
    times 32^N times 2 for the parity of the origin.
    """
    n = nx * ny * nz
    return 2 * (32 ** n) * count_hex_assignments(nx, ny, nz)


def why_not_six_grids() -> Dict[str, object]:
    """Why the other reading of the cube does not close."""
    return {
        "claim": "six whole 4x6 MOG grids cannot be the six faces of a cube "
                 "with consistent edge matching",
        "reason": "a cube face is a square: its four sides are congruent and "
                  "each is shared with a neighbouring face. A 4x6 grid has two "
                  "sides of 6 cells and two of 4 cells, so at four of the "
                  "twelve cube edges a 6-cell side would have to be glued to a "
                  "4-cell side.",
        "sides_of_a_4x6_grid": [6, 6, 4, 4],
        "cube_edges": 12,
        "resolution": "the cube is realised one level down: 6 faces x 4 cells "
                      "= 24 cells = one MOG object, one hexacode digit per "
                      "face.",
    }


# ══════════════════════════════════════════════════════════════════════════════
# 5.  The assembly grammar (ConstructionPath D / X / N / J)
# ══════════════════════════════════════════════════════════════════════════════

Y_CONST_STIPULATED = Fraction(23215, 100000)     # [stip], see the header


@dataclass
class Assembly:
    """A program in the D/X/N/J language, with its receipt."""

    ops: List[Tuple[str, object]]
    children: List["Assembly"]

    def counts(self) -> Tuple[int, int]:
        d = sum(int(m) for op, m in self.ops if op == "D")
        x = sum(int(m) for op, m in self.ops if op == "X")
        return d, x

    def closed(self) -> bool:
        d, x = self.counts()
        return abs(d - x) <= 2

    def voxels(self) -> int:
        d, x = self.counts()
        return max(d - x, 0)

    def tax(self, y_const: Fraction = Y_CONST_STIPULATED) -> Fraction:
        d, x = self.counts()
        t = (d + x) * y_const
        t += Fraction(self.voxels() ** 2, 800)
        for i, ch in enumerate(self.children):
            t += ch.tax(y_const) + (y_const / 2 if i % 2 == 0 else y_const / 4)
        return t


# ══════════════════════════════════════════════════════════════════════════════
# 6.  Substitution (phi) and assembly growth (e)
# ══════════════════════════════════════════════════════════════════════════════

FIB_SUBSTITUTION = {"S": ("S", "D"), "D": ("S",)}     # [stip]


def substitute(word: Sequence[str], n: int) -> Tuple[int, int]:
    """Counts of (S, D) after n applications, computed by matrix power."""
    a, b = word.count("S"), word.count("D")
    for _ in range(n):
        a, b = a + b, a
    return a, b


def substitution_ratio(n: int) -> Fraction:
    a, b = substitute(["S"], n)
    return Fraction(a, b) if b else Fraction(0)


def perron_fibonacci() -> Dict[str, object]:
    """The substitution matrix [[1,1],[1,0]] and its Perron root."""
    r20 = substitution_ratio(20)
    r40 = substitution_ratio(40)
    return {
        "matrix": ((1, 1), (1, 0)),
        "char_poly": "x^2 - x - 1",
        "perron_root": "phi",
        "ratio_after_20": float(r20),
        "ratio_after_40": float(r40),
        "phi": float(PHI),
        "err_after_40": float(abs(r40 - PHI)),
        "stipulated": True,
    }


def growth_rates(max_chain: int = 6) -> Dict[str, object]:
    """Legal-assembly growth, measured, not assumed."""
    chain = [count_chain(n) for n in range(1, max_chain + 1)]
    ratios = [Fraction(chain[i + 1], chain[i]) for i in range(len(chain) - 1)]
    out: Dict[str, object] = {
        "chain_counts": chain,
        "chain_ratio": [int(r) if r.denominator == 1 else float(r)
                        for r in ratios],
    }
    sheets = {}
    for (nx, ny) in ((2, 2), (3, 2), (3, 3), (4, 3)):
        c = count_box(nx, ny, 1)
        sheets[f"{nx}x{ny}x1"] = c
    out["sheet_counts"] = sheets
    boxes = {}
    for (nx, ny, nz) in ((2, 2, 2), (3, 2, 2)):
        boxes[f"{nx}x{ny}x{nz}"] = count_box(nx, ny, nz)
    out["box_counts"] = boxes
    return out


# ══════════════════════════════════════════════════════════════════════════════
# 7.  The thirteen sinks
# ══════════════════════════════════════════════════════════════════════════════

M24_ORDER = 244823040          # |M24|, standard
M24_ELEMENT_ORDERS = (1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 14, 15, 21, 23)


def factorise(n: int) -> Dict[int, int]:
    f: Dict[int, int] = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            f[d] = f.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        f[n] = f.get(n, 0) + 1
    return f


def thirteen_report() -> Dict[str, object]:
    f = factorise(M24_ORDER)
    return {
        "wobble": float(WOBBLE),
        "sink_L": float(SINK_L),
        "balance_exact": N_SINKS * SINK_L == WOBBLE,
        "M24_order": M24_ORDER,
        "M24_factorisation": f,
        "13_divides_M24": M24_ORDER % 13 == 0,
        "13_is_an_element_order": 13 in M24_ELEMENT_ORDERS,
        "13_divides_any_code_parameter": [
            p for p in (24, 12, 8, 4096, 759, 2576, 1771, 2325, 196560)
            if p % 13 == 0],
        "verdict": "13 divides neither the order of M24 nor any parameter of "
                   "the Golay code, and is not an element order of M24. It "
                   "does divide the kissing number 196560 = 13 x 15120, which "
                   "is the one foothold it has. On this evidence 13 stays a "
                   "stipulation [stip] and 'why 13' stays [open].",
    }


def box_formula(nx: int, ny: int, nz: int) -> int:
    """Closed form for `count_hex_assignments`: 4 to the area of the three
    incoming boundary planes.

    Because the hexacode is MDS, every cell with a neighbour below it in each
    of the three axes is *determined*; the only free choices are the incoming
    digits on the three boundary planes x = 0, y = 0, z = 0, one GF(4) digit
    each.  So the legal assemblies of a box are parameterised by its boundary
    and computed in its interior: the entropy of the hexacode layer is a
    surface entropy, not a volume one.
    """
    return 4 ** (nx * ny + ny * nz + nz * nx)


# ══════════════════════════════════════════════════════════════════════════════
# 8.  The receipts of section 6
# ══════════════════════════════════════════════════════════════════════════════

def leech_minimal_vectors() -> Dict[str, object]:
    """The three shapes of the Leech minimal shell, counted, with their tax."""
    n_octad = len(MOG_CODE.octads()) * 2 ** 7          # (+-2)^8 on an octad
    n_four = (24 * 23 // 2) * 4                        # (+-4)^2 shape
    n_odd = 24 * 2 ** 12                               # (-3, 1^23) shape
    shapes = {
        "A  (+-4)^2 0^22": {"HW": 2, "count": n_four},
        "B  (+-2)^8 on an octad": {"HW": 8, "count": n_octad},
        "C  (-+3, +-1^23)": {"HW": 24, "count": n_odd},
    }
    for k, v in shapes.items():
        t = v["HW"] * Y + 4                            # ||v||^2 = 32
        v["TAX"] = float(t)
        v["NRCI"] = float(nrci(t))
    total = sum(v["count"] for v in shapes.values())
    return {"shapes": shapes, "total": total, "expected": 196560,
            "ok": total == 196560}


def amgm_report() -> Dict[str, object]:
    """The read operator Y[P] = 1/(P + 2/P) and its AM-GM cap."""
    lo, hi = _sqrt_frac(8)
    cap_lo, cap_hi = 1 / hi, 1 / lo                    # 1/(2 sqrt 2)
    at_sqrt2_lo, at_sqrt2_hi = _sqrt_frac(2)
    val = 1 / (at_sqrt2_lo + 2 / at_sqrt2_hi)
    return {
        "cap_1_over_2sqrt2": float(cap_lo),
        "Y_at_pi": float(Y),
        "Y_below_cap": Y < cap_lo,
        "value_at_sqrt2": float(val),
        "equality_at_sqrt2": abs(float(val) - float(cap_lo)) < 1e-15,
    }


def syndrome_census() -> Dict[str, object]:
    by_w: Dict[int, int] = {}
    ambiguous = 0
    for s, ls in SYN.leader.items():
        w = popcount(ls[0])
        by_w[w] = by_w.get(w, 0) + 1
        if len(ls) > 1:
            ambiguous += 1
            assert len(ls) == 6
    shallow = sum(v for k, v in by_w.items() if k <= 3)
    return {"cosets_by_leader_weight": dict(sorted(by_w.items())),
            "shallow_le3": shallow,
            "deep_eq4": by_w.get(4, 0),
            "ambiguous": ambiguous,
            "expected_shallow": 2325, "expected_deep": 1771}


def admissibility_window(lo: float = 0.70, hi: float = 0.80) -> Dict[str, object]:
    """Which weights actually land in the `is_stable` NRCI window."""
    ws = [w for w in range(25) if lo <= float(nrci(w * Q)) <= hi]
    return {"window": [lo, hi], "weights_in_window": ws,
            "octad_in_window": 8 in ws,
            "note": "the window does not single out weight 8; that the "
                    "keystone is an octad is an extra stipulation."}


def calibrated_ladder() -> Dict[str, object]:
    return {str(w): float(nrci_calibrated(w)) for w in (0, 8, 12, 16, 24)}


def receipts() -> List[Tuple[str, str, str]]:
    """Every claim of section 6, checked.  (name, verdict, evidence)."""
    out: List[Tuple[str, str, str]] = []

    def chk(name, ok, evidence):
        out.append((name, "PASS" if ok else "FAIL", str(evidence)))

    chk("Y = 0.2646754...", abs(float(Y) - 0.2646754) < 1e-7, float(Y))
    chk("Q = 0.3896754...", abs(float(Q) - 0.3896754) < 1e-7, float(Q))
    chk("8Q = 3.1174032... (8 x the rounded Q)",
        abs(float(8 * Q) - 3.1174032) < 1e-6, float(8 * Q))
    chk("24Q = 9.3522096 < 10",
        abs(float(24 * Q) - 9.3522096) < 1e-5 and 24 * Q < B, float(24 * Q))
    lad = calibrated_ladder()
    chk("calibrated ladder 1 / .5 / .4 / .333 / .25",
        [round(lad[k], 3) for k in ("0", "8", "12", "16", "24")]
        == [1.0, 0.5, 0.4, 0.333, 0.25], lad)
    lch = leech_minimal_vectors()
    vals = [round(v["NRCI"], 6) for v in lch["shapes"].values()]
    chk("Leech A / B / C = 0.688262 / 0.620447 / 0.491347",
        vals == [0.688262, 0.620447, 0.491347], vals)
    chk("196560 minimal vectors", lch["ok"], lch["total"])
    am = amgm_report()
    chk("AM-GM cap 0.353553 > Y, equality at sqrt 2",
        am["Y_below_cap"] and am["equality_at_sqrt2"]
        and abs(am["cap_1_over_2sqrt2"] - 0.353553) < 1e-6, am)
    cen = syndrome_census()
    chk("2325 shallow / 1771 deep syndromes",
        cen["shallow_le3"] == 2325 and cen["deep_eq4"] == 1771, cen)
    chk("snap repairs every defect of weight <= 3, uniquely",
        all(SYN.snap(p)[2] == 1 for w in (1, 2, 3)
            for p in list(MogSyndromes._patterns(w))[:200]),
        "600 patterns of weight 1, 2, 3")
    chk("13 . L == wobble exactly (as Fractions)",
        N_SINKS * SINK_L == WOBBLE, (float(WOBBLE), float(SINK_L)))
    chk("wobble = 0.81757..., L = 0.062890...",
        abs(float(WOBBLE) - 0.81758) < 1e-4 and abs(float(SINK_L) - 0.062890) < 1e-6,
        (float(WOBBLE), float(SINK_L)))
    from .hexacode import verify as hexverify
    hv = hexverify()
    chk("MOG / hexacode: 0 failures out of 4096",
        hv["decompose_failures"] == 0 and hv["decompose_checked"] == 4096, hv)
    chk("the MOG grid really is the Golay code",
        hv["is_golay_enumerator"] and hv["self_dual"] and hv["doubly_even"],
        hv["weight_enumerator"])
    out.append(("Y_CONST = 0.232150 (nesting surcharge)", "UNVERIFIABLE",
                "this constant comes from ubp_unified_v5.py, which is not in "
                "the repository, and it is not derivable from anything that "
                "is; it is carried as a stipulated parameter"))
    return out


def update_matrix() -> Dict[str, object]:
    """Is the 3-D update rule linear over GF(4), and what is its matrix?

    The incoming faces are (1, 3, 5) = (-x, -y, -z) and the outgoing are
    (0, 2, 4).  The hexacode is GF(4)-linear, so the map incoming -> outgoing
    is linear; we extract its 3x3 matrix, check it against all 64 words, and
    compute its multiplicative order.
    """
    basis = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
    cols = []
    for b in basis:
        h = UPDATE[b]
        cols.append((h[0], h[2], h[4]))
    M = [[cols[j][i] for j in range(3)] for i in range(3)]

    def apply(M, v):
        return tuple(gf_add(gf_add(gf_mul(M[i][0], v[0]), gf_mul(M[i][1], v[1])),
                            gf_mul(M[i][2], v[2])) for i in range(3))

    ok = all(apply(M, (h[1], h[3], h[5])) == (h[0], h[2], h[4])
             for h in hexacode())
    # multiplicative order
    def matmul(A, Bm):
        return [[
            gf_add(gf_add(gf_mul(A[i][0], Bm[0][j]), gf_mul(A[i][1], Bm[1][j])),
                   gf_mul(A[i][2], Bm[2][j])) for j in range(3)]
            for i in range(3)]
    I = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    P, order = M, 1
    while P != I and order < 100:
        P = matmul(P, M)
        order += 1
    return {"linear": ok, "matrix": M, "order": order if P == I else None}


def automaton_demo(n: int = 5) -> Dict[str, object]:
    """Propagate a block from its three boundary planes and check determinism
    and reversibility."""
    import random
    rnd = random.Random(11)
    h: Dict[Tuple[int, int, int], Tuple[int, ...]] = {}
    for z in range(n):
        for y in range(n):
            for x in range(n):
                inc = (h[(x - 1, y, z)][0] if x else rnd.randrange(4),
                       h[(x, y - 1, z)][2] if y else rnd.randrange(4),
                       h[(x, y, z - 1)][4] if z else rnd.randrange(4))
                h[(x, y, z)] = UPDATE[inc]
    legal = all(h[(x, y, z)][0] == h[(x + 1, y, z)][1]
                for x in range(n - 1) for y in range(n) for z in range(n))
    # reversibility: the outgoing triple determines the incoming triple
    back = {}
    for w in hexacode():
        back[(w[0], w[2], w[4])] = (w[1], w[3], w[5])
    rev = all(back[(w[0], w[2], w[4])] == (w[1], w[3], w[5]) for w in hexacode())
    return {"cells": n ** 3, "all_joins_legal": legal, "reversible": rev,
            "corner_word": h[(n - 1, n - 1, n - 1)]}
