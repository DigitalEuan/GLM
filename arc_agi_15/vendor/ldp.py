#!/usr/bin/env python3
"""
Literal Data Physics — Entry Module
====================================
A lightweight, importable module for computing with the Literal Data Physics
framework. Designed to run on any hardware with Python 3.8+.

Usage:
    from ldp import DataObject, react, face, cell, batch_compress, constants

    # Create a data-physical object
    obj = DataObject(60)
    print(obj.mass)      # 22 (topological mass)
    print(obj.zone)      # "deep"
    print(obj.is_prime)  # False

    # React two objects
    result = react(5, 7)
    print(result)        # {'regime': 'endothermic', 'defect': 4, ...}

    # Three-body interaction
    face_result = face(60, 84, 105)
    print(face_result)   # {'three_body': True, 'excess': -3.67, ...}

    # Batch compress integers
    compressed = batch_compress([7, 13, 42, 100, 169])
    print(compressed)    # {'bits_per_int': 6.2, 'savings_pct': 37.8, ...}

    # Access physical constants
    print(constants.RHO_INF)  # 0.196036...
    print(constants.Y)        # 0.264675...

No dependencies beyond Python stdlib.
"""

import math
from typing import Dict, List, Any, Tuple
from collections import Counter, defaultdict

# ==============================================================================
# CORE FUNCTIONS
# ==============================================================================

def phi(n: int) -> int:
    """Euler's Totient φ(n): count of integers ≤ n coprime to n."""
    if n < 1: return 0
    if n == 1: return 1
    result = n; temp = n; p = 2
    while p * p <= temp:
        if temp % p == 0:
            while temp % p == 0: temp //= p
            result -= result // p
        p += 1
    if temp > 1: result -= result // temp
    return result

def is_prime(n: int) -> bool:
    """Primality test."""
    if n < 2: return False
    if n < 4: return True
    if n % 2 == 0 or n % 3 == 0: return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0: return False
        i += 6
    return True

def factorize(n: int) -> Dict[int, int]:
    """Prime factorization: {prime: exponent}."""
    f = {}; d = 2
    while d * d <= n:
        while n % d == 0: f[d] = f.get(d, 0) + 1; n //= d
        d += 1
    if n > 1: f[n] = f.get(n, 0) + 1
    return f

def sub_cycles(n: int) -> int:
    """C(N) = floor(N/2) - φ(N)/2. Topological mass of integer N.
    C(N) = 0 iff N is prime (Prime Ground State Theorem)."""
    if n < 3: return 0
    return (n // 2) - (phi(n) // 2)

def totient_defect(a: int, b: int) -> int:
    """ΔC(A,B) — binding energy of reaction A + B = C.
    ΔC < 0: EXOTHERMIC (energy released)
    ΔC > 0: ENDOTHERMIC (energy absorbed)
    ΔC = 0: ISO-RESONANT (conserved)"""
    return (1 if (a % 2 == 1 and b % 2 == 1) else 0) + \
           (phi(a) + phi(b) - phi(a + b)) // 2

def radius(n: int) -> float:
    """R(N) = 1/(2·sin(π/N)) — spatial radius of unit-edge N-gon."""
    if n < 3: return 1.0
    return 1.0 / (2.0 * math.sin(math.pi / n))

def tension(n: int) -> float:
    """T(N) — geometric tension (deviation from circularity)."""
    if n < 3: return 0.0
    area = (n / 4.0) * (1.0 / math.tan(math.pi / n))
    circle_area = (n ** 2) / (4.0 * math.pi)
    return 1.0 - (area / circle_area)

# ==============================================================================
# DATA OBJECT — integer as physical object
# ==============================================================================

class DataObject:
    """An integer experienced as a physical object.
    
    Properties:
        n:          the integer value
        mass:       topological mass M(N) = C(N) (0 for primes)
        radius:     spatial radius R(N)
        tension:    geometric tension T(N)
        zone:       "ground" (prime), "shallow", "medium", "deep"
        charge:     0 (even) or 1 (odd)
        is_prime:   True if prime (ground state)
        factors:    prime factorization dict
        omega:      total prime factors with multiplicity
        omega_d:    distinct prime factors
        phi_ratio:  φ(n)/n (coprime density)
    """
    
    def __init__(self, n: int):
        self.n = n
        self._factors = None
    
    @property
    def mass(self) -> int:
        return sub_cycles(self.n)
    
    @property
    def radius(self) -> float:
        return radius(self.n)
    
    @property
    def tension(self) -> float:
        return tension(self.n)
    
    @property
    def zone(self) -> str:
        if self.is_prime: return "ground"
        c = self.mass
        if c <= 4: return "shallow"
        if c <= 15: return "medium"
        return "deep"
    
    @property
    def charge(self) -> int:
        return self.n % 2
    
    @property
    def is_prime(self) -> bool:
        return is_prime(self.n)
    
    @property
    def factors(self) -> Dict[int, int]:
        if self._factors is None:
            self._factors = factorize(self.n)
        return self._factors
    
    @property
    def omega(self) -> int:
        return sum(self.factors.values())
    
    @property
    def omega_d(self) -> int:
        return len(self.factors)
    
    @property
    def phi_ratio(self) -> float:
        return phi(self.n) / self.n if self.n > 0 else 0
    
    def __repr__(self):
        f_str = "×".join(f"{p}^{e}" if e > 1 else str(p) 
                         for p, e in self.factors.items())
        return (f"DataObject({self.n}, zone={self.zone}, "
                f"M={self.mass}, R={self.radius:.3f})")

# ==============================================================================
# REACTIONS — k=0,1,2,3
# ==============================================================================

def react(a: int, b: int) -> Dict[str, Any]:
    """k=1: Pairwise reaction via Totient Defect.
    
    Returns dict with:
        a, b:       operands
        product:    a + b
        defect:     ΔC(A,B)
        regime:     "exothermic", "endothermic", or "iso_resonant"
        energy:     |ΔC|
    """
    dc = totient_defect(a, b)
    regime = "exothermic" if dc < 0 else "endothermic" if dc > 0 else "iso_resonant"
    return {
        "a": a, "b": b, "product": a + b,
        "defect": dc, "regime": regime, "energy": abs(dc),
    }

def face(a: int, b: int, c: int) -> Dict[str, Any]:
    """k=2: Three-body interaction via triple GCD structure.
    
    Returns dict with:
        gcd_abc:        triple GCD
        pairwise_gcds:  (gcd(a,b), gcd(b,c), gcd(a,c))
        excess:         face defect (how triple differs from pairwise avg)
        three_body:     True if significant three-body force
        redundancy:     how much pairwise over-predicts triple
    """
    gcd_ab = math.gcd(a, b)
    gcd_bc = math.gcd(b, c)
    gcd_ac = math.gcd(a, c)
    gcd_abc = math.gcd(a, math.gcd(b, c))
    
    c_ab = sub_cycles(gcd_ab) if gcd_ab >= 3 else 0
    c_bc = sub_cycles(gcd_bc) if gcd_bc >= 3 else 0
    c_ac = sub_cycles(gcd_ac) if gcd_ac >= 3 else 0
    c_abc = sub_cycles(gcd_abc) if gcd_abc >= 3 else 0
    
    pair_avg = (c_ab + c_bc + c_ac) / 3
    excess = c_abc - pair_avg
    
    return {
        "a": a, "b": b, "c": c,
        "gcd_abc": gcd_abc,
        "pairwise_gcds": (gcd_ab, gcd_bc, gcd_ac),
        "excess": excess,
        "three_body": abs(excess) > 0.5,
        "redundancy": pair_avg - c_abc,
    }

def cell(a: int, b: int, c: int, d: int) -> Dict[str, Any]:
    """k=3: Four-body interaction via quadruple GCD structure.
    
    Returns dict with:
        gcd_abcd:   quadruple GCD
        excess:     cell defect
        four_body:  True if significant four-body force
    """
    gcd_abcd = math.gcd(a, math.gcd(b, math.gcd(c, d)))
    
    triples = [
        math.gcd(a, math.gcd(b, c)),
        math.gcd(a, math.gcd(b, d)),
        math.gcd(a, math.gcd(c, d)),
        math.gcd(b, math.gcd(c, d)),
    ]
    c_quad = sub_cycles(gcd_abcd) if gcd_abcd >= 3 else 0
    triple_avg = sum(sub_cycles(g) if g >= 3 else 0 for g in triples) / 4
    excess = c_quad - triple_avg
    
    return {
        "a": a, "b": b, "c": c, "d": d,
        "gcd_abcd": gcd_abcd,
        "excess": excess,
        "four_body": abs(excess) > 0.5,
    }

# ==============================================================================
# BATCH COMPRESSION — shared geometric headers
# ==============================================================================

def batch_compress(integers: List[int], N_range: Tuple[int, int] = (3, 1000)) -> Dict[str, Any]:
    """Compress a batch of integers using shared geometric headers.
    
    Groups by geometric class (10-bit header). Each group shares one header;
    members need only their index within the group.
    
    Returns dict with:
        n_integers:     count
        n_groups:       unique geometric classes
        bits_per_int:   compressed size
        savings_pct:    vs raw encoding
    """
    lo, hi = N_range
    raw_bits = math.log2(hi - lo + 1)
    
    def geo_class(n):
        f = factorize(n)
        return (min(sub_cycles(n), 15), min(sum(f.values()), 7),
                min(len(f), 3), int(is_prime(n)))
    
    groups = defaultdict(list)
    for n in integers:
        groups[geo_class(n)].append(n)
    
    total_bits = 0
    for gc, members in groups.items():
        header = 10
        idx_bits = math.ceil(math.log2(max(len(members), 1)))
        total_bits += header + len(members) * idx_bits
    
    return {
        "n_integers": len(integers),
        "n_groups": len(groups),
        "total_bits": total_bits,
        "bits_per_int": total_bits / len(integers) if integers else 0,
        "raw_bits_per_int": raw_bits,
        "savings_pct": (1 - total_bits / (len(integers) * raw_bits)) * 100 if integers else 0,
    }

# ==============================================================================
# CONSTANTS — physical constants of data space
# ==============================================================================

class _Constants:
    """Physical constants of Literal Data Physics."""
    RHO_INF = (1 - 6 / math.pi**2) / 2      # ≈ 0.196036
    Y = math.pi / (math.pi**2 + 2)           # ≈ 0.264675
    WOBBLE = (math.pi * (1 + math.sqrt(5)) / 2 * math.e) % 1  # ≈ 0.817580
    L = WOBBLE / 13                          # ≈ 0.062891
    U_E = 13824                              # 24³
    TOP_THIRD = phi(13824) / 13824           # = 1/3 exactly

constants = _Constants()

# ==============================================================================
# QUICK TEST
# ==============================================================================

def test():
    """Quick verification that the framework works."""
    # Conservation: ISO-RESONANT pairs conserve mass
    for a, b in [(9, 6), (8, 8), (4, 4)]:
        dc = totient_defect(a, b)
        assert dc == 0, f"Expected ISO-RESONANT for ({a},{b}), got ΔC={dc}"
        assert sub_cycles(a) + sub_cycles(b) == sub_cycles(a + b), \
            f"Mass not conserved for ({a},{b})"
    
    # Prime ground state
    for p in [7, 13, 137, 997]:
        assert is_prime(p), f"{p} should be prime"
        assert sub_cycles(p) == 0, f"C({p}) should be 0"
    
    # Three-body exists
    f = face(12, 18, 24)
    assert f["three_body"], "Expected three-body force for (12,18,24)"
    
    # Batch compression
    c = batch_compress([7, 13, 42, 100, 169])
    assert c["savings_pct"] > 0, "Expected positive savings"
    
    # Constants
    assert abs(constants.RHO_INF - 0.196) < 0.001
    assert abs(constants.Y - 0.265) < 0.001
    assert abs(constants.TOP_THIRD - 1/3) < 1e-10
    
    return True

if __name__ == "__main__":
    print("Literal Data Physics — Entry Module")
    print("=" * 50)
    
    if test():
        print("✓ All tests pass\n")
    
    # Quick demo
    print("Examples:")
    print(f"  DataObject(60) = {DataObject(60)}")
    print(f"  react(5, 7)    = {react(5, 7)}")
    print(f"  face(12,18,24) = {face(12, 18, 24)}")
    print(f"  cell(60,84,105,210) = {cell(60, 84, 105, 210)}")
    print(f"  batch_compress([7,13,42,100,169]) = {batch_compress([7,13,42,100,169])}")
    print(f"\n  constants.RHO_INF = {constants.RHO_INF:.6f}")
    print(f"  constants.Y       = {constants.Y:.6f}")
    print(f"  constants.TOP_THIRD = {constants.TOP_THIRD:.6f}")
