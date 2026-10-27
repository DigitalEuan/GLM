#!/usr/bin/env python3
"""Sanity check: for each CFSG sporadic group, compute the order from its
prime factorization string and verify it matches the value in cfsg_seed.
Reports any discrepancies."""
import re
import sys
sys.path.insert(0, '/home/z/my-project/aristotle')
from cfsg_seed import CFSG_GROUPS
from sympy import factorint

def parse_factorization(fact_str):
    """Parse a factorization string like '2^21 · 3^9 · 5^4 · ...' into
    a dict {prime: exponent}."""
    # match patterns like "2^21" or just "17" (implicit ^1)
    pattern = re.compile(r'(\d+)\^(\d+)|(\d+)(?!\^)')
    factors = {}
    for m in pattern.finditer(fact_str):
        if m.group(1) is not None:
            p = int(m.group(1))
            e = int(m.group(2))
        else:
            p = int(m.group(3))
            e = 1
        factors[p] = factors.get(p, 0) + e
    return factors

print(f"Sanity check on {len(CFSG_GROUPS)} sporadic groups:")
discrepancies = []
for gid, name, order, fact_str, disc, year, notes in CFSG_GROUPS:
    parsed_factors = parse_factorization(fact_str)
    expected_order = 1
    for p, e in parsed_factors.items():
        expected_order *= p ** e
    # also factorize the actual order and compare
    actual_factors = factorint(order)
    if expected_order != order or dict(actual_factors) != parsed_factors:
        print(f"  {gid:6s}  cfsg_seed order = {order}")
        print(f"         factorization string = {fact_str}")
        print(f"         computed from string = {expected_order}")
        print(f"         factorint(cfsg_seed order) = {dict(actual_factors)}")
        print(f"         parse(string) = {parsed_factors}")
        print(f"         *** MISMATCH ***")
        discrepancies.append((gid, order, expected_order, fact_str, dict(actual_factors), parsed_factors))
    else:
        print(f"  {gid:6s}  ok ({order})")

print()
if discrepancies:
    print(f"*** {len(discrepancies)} discrepancies found. Fix cfsg_seed.py:")
    for gid, order, expected, fact_str, actual, parsed in discrepancies:
        print(f"  {gid}: cfsg_seed has {order}, should be {expected}")
else:
    print("All 26 groups verified.")
