"""
"""
================================================================================
UBP ldp_codec — Geometric Batch Grouping Analysis
================================================================================
Author  : E R A Craig, New Zealand
Version : 0.2
Date    : 28 July 2026

THE CONCEPT
=========
Getting more data-per-bit than encoded and using the additional meta-data for computational use.
===============================================
A deterministic analysis/grouping library for integer batches.

Integers are grouped by a lossy 10-bit structural fingerprint.  The fingerprint
is not an invertible encoding: exact members still have to be stored.  Therefore
this module does **not** claim compression from class headers alone.  Its size
figures include each integer's range code plus the class headers.

Usage:
    from ldp_codec import compress, decompress

    # Group and analyze a batch of integers
    data = [7, 13, 42, 100, 169, 500, 997]
    compressed = compress(data)
    print(compressed.summary())

    # Decompress
    recovered = decompress(compressed)
    assert recovered == data

    # Get storage-overhead stats (negative savings means overhead)
    print(f"Savings estimate: {compressed.savings_pct:.1f}%")
    print(f"Bits/int: {compressed.bits_per_int:.2f} (vs {compressed.raw_bits_per_int:.2f} raw)")

No dependencies. Python 3.8+.

================================================================================
"""
"""

import math
from typing import List, Tuple, Dict, Any, Optional
from collections import defaultdict
from dataclasses import dataclass, field

# ==============================================================================
# CORE NUMBER THEORY (self-contained, no external deps)
# ==============================================================================

def _phi(n: int) -> int:
    """Euler's totient φ(n)."""
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

def _is_prime(n: int) -> bool:
    if n < 2: return False
    if n < 4: return True
    if n % 2 == 0 or n % 3 == 0: return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0: return False
        i += 6
    return True

def _factorize(n: int) -> Dict[int, int]:
    f = {}; d = 2
    while d * d <= n:
        while n % d == 0: f[d] = f.get(d, 0) + 1; n //= d
        d += 1
    if n > 1: f[n] = f.get(n, 0) + 1
    return f

def _sub_cycles(n: int) -> int:
    if n < 3: return 0
    return (n // 2) - (_phi(n) // 2)

# ==============================================================================
# GEOMETRIC CLASS — the 10-bit structural fingerprint
# ==============================================================================

def geo_class(n: int) -> Tuple[int, int, int, int]:
    """
    Geometric class: a 10-bit structural fingerprint.
    Returns (C_depth, omega_total, omega_distinct, is_prime).
    """
    f = _factorize(n)
    return (
        min(_sub_cycles(n), 15),      # 4 bits: sub-cycle depth
        min(sum(f.values()), 7),       # 3 bits: total prime factors
        min(len(f), 3),                # 2 bits: distinct primes
        int(_is_prime(n)),             # 1 bit:  primality flag
    )

GEO_CLASS_BITS = 10  # total bits for geometric class

# ==============================================================================
# COMPRESSED DATA STRUCTURE
# ==============================================================================

@dataclass
class CompressedBatch:
    """A grouped batch with honest standalone-storage estimates.

    The historical class name is retained for API compatibility.  ``integers``
    and ``groups`` contain exact members; a geometric class alone cannot recover
    them.
    
    Attributes:
        integers: the original integers (for verification)
        groups: dict mapping geo_class → sorted list of integers
        n_integers: count of integers
        n_groups: count of unique geometric classes
        total_bits: standalone estimate including exact values and headers
        bits_per_int: average bits per integer
        raw_bits_per_int: raw encoding bits per integer
        savings_pct: percentage saved vs raw
    """
    integers: List[int]
    groups: Dict[Tuple[int,int,int,int], List[int]]
    n_integers: int
    n_groups: int
    total_bits: int
    bits_per_int: float
    raw_bits_per_int: float
    savings_pct: float
    
    def summary(self) -> str:
        return (
            f"GroupedBatch: {self.n_integers} integers → "
            f"{self.n_groups} groups, "
            f"{self.bits_per_int:.2f} estimated bits/int "
            f"({self.savings_pct:.1f}% savings vs raw {self.raw_bits_per_int:.2f}; "
            "negative means metadata overhead)"
        )
    
    def header_info(self) -> List[Dict[str, Any]]:
        """Return info about each geometric class group."""
        result = []
        for gc, members in sorted(self.groups.items()):
            c_depth, omega_t, omega_d, is_p = gc
            idx_bits = math.ceil(math.log2(max(len(members), 1)))
            result.append({
                "geo_class": gc,
                "c_depth": c_depth,
                "omega_total": omega_t,
                "omega_distinct": omega_d,
                "is_prime": bool(is_p),
                "n_members": len(members),
                "idx_bits": idx_bits,
                "index_only_bits": GEO_CLASS_BITS + len(members) * idx_bits,
                "members": members,
            })
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize summary data to a JSON-compatible dict.

        Tuple keys are rendered for display; use a purpose-built wire format if
        this dictionary itself must later be decoded.
        """
        return {
            "n_integers": self.n_integers,
            "n_groups": self.n_groups,
            "total_bits": self.total_bits,
            "bits_per_int": self.bits_per_int,
            "raw_bits_per_int": self.raw_bits_per_int,
            "savings_pct": self.savings_pct,
            "groups": {
                str(gc): members for gc, members in self.groups.items()
            },
        }

# ==============================================================================
# COMPRESS / DECOMPRESS
# ==============================================================================

def compress(integers: List[int], N_range: Tuple[int, int] = (3, 1000)) -> CompressedBatch:
    """
    Group a batch and estimate standalone storage with geometric headers.

    Each group shares a 10-bit descriptive header, but exact integer range
    codes are still counted because the fingerprint is many-to-one.
    
    Args:
        integers: list of integers to compress
        N_range: the expected range (for computing raw bits)
    
    Returns:
        API-compatible CompressedBatch with grouping/storage statistics
    """
    lo, hi = N_range
    if lo > hi:
        raise ValueError("N_range lower bound must not exceed upper bound")
    if any(isinstance(n, bool) or not isinstance(n, int) for n in integers):
        raise TypeError("integers must contain only int values")
    if any(n < lo or n > hi for n in integers):
        raise ValueError("every integer must lie within N_range")
    raw_bits = max(1, math.ceil(math.log2(hi - lo + 1)))

    # Group by geometric class.  Exact values remain necessary because many
    # integers share each class.
    groups = defaultdict(list)
    for n in integers:
        groups[geo_class(n)].append(n)
    
    # Sort each group for deterministic indexing
    for gc in groups:
        groups[gc].sort()
    
    # Honest standalone estimate: each exact range code plus one class header.
    # The previous implementation counted only an index into an unstored
    # codebook, then retained the original integers in memory; that was not a
    # decodable compressed representation.
    total_bits = len(integers) * raw_bits + len(groups) * GEO_CLASS_BITS
    
    n_integers = len(integers)
    bits_per_int = total_bits / n_integers if n_integers > 0 else 0
    savings_pct = (1 - bits_per_int / raw_bits) * 100 if raw_bits > 0 else 0
    
    return CompressedBatch(
        integers=list(integers),
        groups=dict(groups),
        n_integers=n_integers,
        n_groups=len(groups),
        total_bits=total_bits,
        bits_per_int=bits_per_int,
        raw_bits_per_int=raw_bits,
        savings_pct=savings_pct,
    )

def decompress(batch: CompressedBatch) -> List[int]:
    """
    Recover the sorted exact members retained in a CompressedBatch.

    This is lossless because the batch stores the members, not because the
    geometric fingerprint is invertible.
    
    Args:
        batch: a CompressedBatch from compress()
    
    Returns:
        the original list of integers
    """
    result = []
    for gc, members in sorted(batch.groups.items()):
        result.extend(members)
    # Restore original order by sorting
    # Note: compression groups and sorts, so we lose original order
    # If order matters, use compress_ordered() instead
    return sorted(result)

def compress_ordered(integers: List[int], N_range: Tuple[int, int] = (3, 1000)) -> Tuple[CompressedBatch, List[int]]:
    """
    Group while recording enough references to preserve original order.
    
    Returns:
        (CompressedBatch, order_indices) where order_indices records
        the position of each integer in the original list.
    """
    batch = compress(integers, N_range)
    
    # Build index mapping
    index_map = {}
    for gc, members in batch.groups.items():
        for idx, member in enumerate(members):
            index_map[member] = (gc, idx)
    
    # Record order
    order = []
    for n in integers:
        gc, idx = index_map[n]
        order.append((gc, idx))
    
    return batch, order

def decompress_ordered(batch: CompressedBatch, order: List[Tuple]) -> List[int]:
    """Decompress with original order restored."""
    # Build lookup
    lookup = {}
    for gc, members in batch.groups.items():
        for idx, member in enumerate(members):
            lookup[(gc, idx)] = member
    
    return [lookup[o] for o in order]

# ==============================================================================
# ANALYSIS UTILITIES
# ==============================================================================

def analyze_distribution(integers: List[int]) -> Dict[str, Any]:
    """Analyze the geometric class distribution of a batch."""
    groups = defaultdict(list)
    for n in integers:
        groups[geo_class(n)].append(n)
    
    sizes = [len(v) for v in groups.values()]
    
    return {
        "n_integers": len(integers),
        "n_classes": len(groups),
        "class_sizes": {
            "min": min(sizes) if sizes else 0,
            "max": max(sizes) if sizes else 0,
            "mean": sum(sizes) / len(sizes) if sizes else 0,
            "median": sorted(sizes)[len(sizes)//2] if sizes else 0,
        },
        "singleton_classes": sum(1 for s in sizes if s == 1),
        "large_classes": sum(1 for s in sizes if s > 10),
        "largest_class": max(sizes) if sizes else 0,
    }

def estimate_savings(n_integers: int, N_range: Tuple[int, int] = (3, 1000)) -> float:
    """Estimate storage savings (normally metadata overhead) for a sample."""
    import random
    random.seed(42)
    lo, hi = N_range
    batch = random.sample(range(lo, hi + 1), min(n_integers, hi - lo + 1))
    compressed = compress(batch, N_range)
    return compressed.savings_pct

# ==============================================================================
# CLI
# ==============================================================================

def _demo():
    """Demonstrate the grouping-analysis library."""
    import random
    
    print("=" * 60)
    print(" ldp_codec — Geometric Batch Grouping Analysis")
    print("=" * 60)
    
    # Example 1: Small batch
    print("\n[1] Small batch:")
    data = [7, 13, 42, 100, 169, 500, 997]
    compressed = compress(data)
    print(f"  {compressed.summary()}")
    recovered = decompress(compressed)
    print(f"  Roundtrip: {data} → {recovered}")
    print(f"  Order preserved: {data == recovered}")
    
    # Example 2: Ordered compression
    print("\n[2] Ordered compression:")
    batch, order = compress_ordered(data)
    recovered_ordered = decompress_ordered(batch, order)
    print(f"  Original:   {data}")
    print(f"  Recovered:  {recovered_ordered}")
    print(f"  Order preserved: {data == recovered_ordered}")
    
    # Example 3: Various batch sizes
    print("\n[3] Standalone storage estimate by batch size:")
    random.seed(42)
    ns = list(range(3, 1001))
    print(f"  {'Size':>6} {'Groups':>7} {'Bits/int':>9} {'Raw':>7} {'Savings':>8}")
    print("  " + "-" * 42)
    for size in [10, 25, 50, 100, 250, 500]:
        batch = random.sample(ns, size)
        comp = compress(batch)
        print(f"  {size:>6} {comp.n_groups:>7} {comp.bits_per_int:>9.2f} "
              f"{comp.raw_bits_per_int:>7.2f} {comp.savings_pct:>7.1f}%")
    
    # Example 4: Distribution analysis
    print("\n[4] Distribution analysis (100 random ints):")
    batch = random.sample(ns, 100)
    analysis = analyze_distribution(batch)
    print(f"  Classes: {analysis['n_classes']}")
    print(f"  Singletons: {analysis['singleton_classes']}")
    print(f"  Large (>10): {analysis['large_classes']}")
    print(f"  Largest: {analysis['largest_class']}")
    
    # Example 5: Structured batch (all primes)
    print("\n[5] Structured batch (all primes in [3,200]):")
    primes = [n for n in range(3, 201) if _is_prime(n)]
    comp = compress(primes)
    print(f"  {comp.summary()}")
    print("  All primes share one descriptive class; exact values are still stored")
    
    # Example 6: Header info
    print("\n[6] Header info (first 5 groups):")
    comp = compress(random.sample(ns, 100))
    for info in comp.header_info()[:5]:
        gc = info['geo_class']
        print(f"  Class {gc}: {info['n_members']} members, "
              f"{info['idx_bits']} idx bits, {info['index_only_bits']} index-only bits")

    print("\n" + "=" * 60)
    print(" Usage:")
    print("   from ldp_codec import compress, decompress")
    print("   compressed = compress([7, 13, 42, 100, 169])")
    print("   recovered = decompress(compressed)")
    print("=" * 60)

if __name__ == "__main__":
    _demo()
