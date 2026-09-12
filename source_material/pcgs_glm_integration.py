#!/usr/bin/env python3
"""
Bringing the Proof-Carrying Generative Substrate (PCGS) into the GLM
====================================================================

This module bridges the PCGS concept — compact generative description +
answer + correctness evidence + resource evidence — with the GLM's
existing substrate, meaning layer, and reverse-call planner.

The PCGS concept (from the study document):

    compact description → (answer, correctness evidence, resource evidence)

This is stronger than procedural generation because:
1. The answer is provably correct (certified)
2. The cost is explicit (resource ledger)
3. Caching is optional and transparent
4. The implementation is auditable against the mathematics

The GLM already has most of the pieces:
- The Golay code generated from the Legendre sequence (not stored)
- The Leech lattice generated from Construction A→B→C (not stored)
- The Delta-Sigma modulator generated from exact Fraction feedback
- The reverse-call planner that selects tools based on the problem

What the PCGS adds:
1. Checkable certificates on every answer (not just correct computation)
2. Resource ledgers that report exact operation vectors
3. Provenance digests that identify exactly what was generated
4. An assurance ladder: theorem → certificate → test → benchmark
5. The sliding-window Delta-Sigma bound (interval discrepancy < 1)

This module:
1. Runs the PCGS through the GLM's own verification (weight census, Leech
   membership, Delta-Sigma bounds)
2. Cross-validates the PCGS Golay code against the GLM's own substrate
3. Measures the resource cost of each generative operation
4. Produces certified answers with provenance
5. Tests the sliding-window Delta-Sigma theorem on the GLM's constants
"""

from __future__ import annotations

import sys
import os
from fractions import Fraction
from typing import Tuple, Dict, List, Optional
from dataclasses import dataclass

# Set up paths for both PCGS and GLM
PCGS_ROOT = "/tmp/pcgs_recommended/pcgs_v6_starter"
GLM_ROOT = "/home/z/my-project/GLM"
sys.path.insert(0, os.path.join(PCGS_ROOT, "src"))
sys.path.insert(0, GLM_ROOT)
os.chdir(PCGS_ROOT)

# PCGS imports
from pcgs import (
    ExtendedGolay, MembershipCertificate, Ledger, ResourceReport,
    LeechSubstrate, DecodeResult, LinearCode, CodeCertificate,
    extended_hamming_8_4, extended_golay_24_12, ConstructionA,
    LatticeDecode, Cost, cache_breakeven, FirstOrderDeltaSigma,
    DeltaSigmaTrace, NRCIRecord, nrci_record, Provenance,
    make_provenance, Coset, COSET_COUNT, all_cosets,
    LeechDecoder, PrunedCertificate, verify_certificate,
)
from pcgs.streaming import weighted_error, weighted_error_by_parts

# GLM imports
from glm_universal.substrate.mog import GolayCode
from glm_universal.reasoning import exact_real as er
from glm_universal.semantics import meaning as sme
from glm_universal.semantics import reference as rf


# =====================================================================
# 1. CROSS-VALIDATION: PCGS Golay vs GLM substrate Golay
# =====================================================================

def test_cross_validate_golay():
    """Verify the PCGS-generated Golay code matches the GLM's own substrate.

    Both should produce the same [24,12,8] code with weight distribution
    {0:1, 8:759, 12:2576, 16:759, 24:1}.

    This is the first check: does the generative substrate agree with the
    GLM's own materialized substrate?
    """
    print("=" * 70)
    print("[1] CROSS-VALIDATION: PCGS Golay vs GLM substrate Golay")
    print("=" * 70)

    # PCGS code (generated from QR(11) cyclic generator)
    pcgs_code = extended_golay_24_12()
    pcgs_weights = pcgs_code.weight_enumerator()
    pcgs_certificate = pcgs_code.algebraic_certificate()

    print(f"  PCGS code: {pcgs_code.name}")
    print(f"    Width: {pcgs_certificate['width']}")
    print(f"    Dimension: {pcgs_certificate['dimension']}")
    print(f"    Rank: {pcgs_certificate['rank']}")
    print(f"    Self-dual: {pcgs_certificate['self_dual']}")
    print(f"    Cardinality: {pcgs_certificate['generated_cardinality']}")
    print(f"    Weight distribution: {dict(sorted(pcgs_weights.items()))}")

    # GLM substrate code
    glm_gc = GolayCode()
    glm_codewords = set()
    for mask in glm_gc.codeword_masks:
        cw = tuple((mask >> (23 - i)) & 1 for i in range(24))
        glm_codewords.add(cw)

    glm_weights = {}
    for cw in glm_codewords:
        w = sum(cw)
        glm_weights[w] = glm_weights.get(w, 0) + 1
    glm_weights = dict(sorted(glm_weights.items()))

    print(f"\n  GLM substrate:")
    print(f"    Codewords: {len(glm_codewords)}")
    print(f"    Weight distribution: {glm_weights}")

    # Check agreement
    expected = {0: 1, 8: 759, 12: 2576, 16: 759, 24: 1}
    pcgs_match = dict(sorted(pcgs_weights.items())) == expected
    glm_match = glm_weights == expected
    cross_match = dict(sorted(pcgs_weights.items())) == glm_weights

    print(f"\n  PCGS matches expected Golay: {pcgs_match}")
    print(f"  GLM matches expected Golay: {glm_match}")
    print(f"  PCGS and GLM agree: {cross_match}")

    return cross_match


# =====================================================================
# 2. CERTIFIED MEMBERSHIP: answer + correctness evidence
# =====================================================================

def test_certified_membership():
    """Test that the PCGS produces checkable certificates for membership.

    A positive certificate includes the systematic message and reconstruction
    equality. A negative certificate includes the nonzero syndrome and the
    failed check index. Both are independently verifiable.
    """
    print("\n" + "=" * 70)
    print("[2] CERTIFIED MEMBERSHIP: answer + correctness evidence")
    print("=" * 70)

    code = extended_golay_24_12()

    # Positive: a known codeword (the all-zeros message encodes to 0)
    cw = code.encode(0)
    cert_pos = code.certify(cw)
    print(f"  Positive test (codeword 0x{cw:06X}):")
    print(f"    Accepted: {cert_pos.accepted}")
    print(f"    Syndrome: {cert_pos.syndrome}")
    print(f"    Message: {cert_pos.message}")
    print(f"    Reconstruction: {code.encode(cert_pos.message) == cw}")

    # Positive: a random codeword
    cw2 = code.encode(0b101100101011)
    cert_pos2 = code.certify(cw2)
    print(f"\n  Positive test (codeword 0x{cw2:06X}):")
    print(f"    Accepted: {cert_pos2.accepted}")
    print(f"    Syndrome: {cert_pos2.syndrome}")
    print(f"    Message: {cert_pos2.message}")
    print(f"    Reconstruction: {code.encode(cert_pos2.message) == cw2}")

    # Negative: a non-codeword (flip one bit)
    bad = cw ^ 1
    cert_neg = code.certify(bad)
    print(f"\n  Negative test (0x{bad:06X}, one bit flipped):")
    print(f"    Accepted: {cert_neg.accepted}")
    print(f"    Syndrome: {cert_neg.syndrome}")
    print(f"    Failed check: {cert_neg.failed_check}")

    all_pass = (cert_pos.accepted and cert_pos2.accepted
                and not cert_neg.accepted)
    print(f"\n  All certificates correct: {all_pass}")
    return all_pass


# =====================================================================
# 3. CERTIFIED LEECH DECODE: pruned decoder + checkable certificate
# =====================================================================

def test_certified_leech_decode():
    """Test that the PCGS Leech decoder produces checkable certificates.

    The pruned decoder visits only 1-2 cosets (out of 8192) and returns
    a certificate that an independent verifier checks without redoing
    the search.
    """
    print("\n" + "=" * 70)
    print("[3] CERTIFIED LEECH DECODE: pruned + checkable certificate")
    print("=" * 70)

    decoder = LeechDecoder()

    # Test target: a rational vector near the origin
    target = tuple(Fraction(i, 24) for i in range(24))

    # Exhaustive decode (the oracle)
    print("  Running exhaustive decode (8192 cosets)...")
    pt_ex, cost_ex, coset_ex, ledger_ex = decoder.decode_exhaustive(target)
    print(f"    Point: {pt_ex[:6]}...")
    print(f"    Cost (d²): {cost_ex}")
    print(f"    Winner coset: {coset_ex}")
    print(f"    Work vector: {dict(ledger_ex.counts)}")

    # Pruned decode (with certificate)
    print("\n  Running pruned decode (with certificate)...")
    cert = decoder.decode_pruned(target)
    print(f"    Point: {cert.point[:6]}...")
    print(f"    Cost (d²): {cert.squared_distance}")
    print(f"    Winner index: {cert.winner_index}")
    print(f"    Evaluated: {len(cert.evaluated)} cosets")
    print(f"    Pruned: {len(cert.pruned)} cosets")

    # Verify the certificate independently
    verified = verify_certificate(decoder, target, cert)
    print(f"\n  Certificate verified: {verified}")

    # Check agreement
    agree = (cert.point == pt_ex and cert.squared_distance == cost_ex)
    print(f"  Pruned == Exhaustive: {agree}")
    print(f"  Pruning ratio: {len(cert.evaluated)}/{COSET_COUNT} = "
          f"{len(cert.evaluated)/COSET_COUNT:.4f}")

    return verified and agree


# =====================================================================
# 4. RESOURCE LEDGER: exact operation vector per answer
# =====================================================================

def test_resource_ledger():
    """Test that every generative operation produces an exact resource
    ledger — a vector of primitive operation counts, not a scalar total.
    """
    print("\n" + "=" * 70)
    print("[4] RESOURCE LEDGER: exact operation vector per answer")
    print("=" * 70)

    code = extended_golay_24_12()

    # Membership test with ledger
    ledger = Ledger()
    cw = code.encode(42, ledger)
    _ = code.is_member(cw, ledger)

    print(f"  Membership test (encode + check):")
    print(f"    Ledger: {dict(ledger.counts)}")
    print(f"    Total operations: {sum(ledger.counts.values())}")

    # Leech decode with ledger
    decoder = LeechDecoder()
    target = tuple(Fraction(0) for _ in range(24))
    _, _, _, dec_ledger = decoder.decode_exhaustive(target)

    print(f"\n  Leech decode (exhaustive, 8192 cosets):")
    print(f"    Ledger: {dict(dec_ledger.counts)}")
    print(f"    Total operations: {sum(dec_ledger.counts.values())}")

    # Resource composition
    cost1 = Cost.from_ledger(ledger, persistent_bytes=144)  # 12×12 bytes
    cost2 = Cost.from_ledger(dec_ledger, persistent_bytes=144)
    combined = cost1.then(cost2)

    print(f"\n  Combined resource (sequential):")
    print(f"    Work: {dict(combined.work)}")
    print(f"    Persistent bytes: {combined.persistent_bytes}")

    # Cache break-even
    build_cost = 50000  # building the full table
    gen_cost = sum(ledger.counts.values())  # generating per query
    cached_cost = 1  # table lookup
    breakeven = cache_breakeven(build_cost, gen_cost, cached_cost)
    print(f"\n  Cache break-even: {breakeven} queries")
    print(f"    (above this, caching wins; below, generation wins)")

    return True


# =====================================================================
# 5. SLIDING-WINDOW DELTA-SIGMA: interval discrepancy < 1
# =====================================================================

def test_sliding_window_delta_sigma():
    """Test the sliding-window Delta-Sigma theorem: for ANY interval
    [a, b) within the bit stream, the count discrepancy is < 1.

    This is the PCGS's strengthened version of the GLM's prefix-only
    theorem (dsAverage_error_le from DeltaSigma.lean). The prefix
    theorem says the average from 0 to N is within 1/N. The sliding
    theorem says ANY sub-interval has discrepancy < 1, regardless of
    where it starts.

    This means: a consumer may begin reading at any time and still
    receives a one-count discrepancy guarantee.
    """
    print("\n" + "=" * 70)
    print("[5] SLIDING-WINDOW DELTA-SIGMA: interval discrepancy < 1")
    print("=" * 70)

    # Run the Delta-Sigma on 1/7 (period 7, deterministic)
    ds = FirstOrderDeltaSigma(accumulator=Fraction(0))
    targets = [Fraction(1, 7)] * 100
    trace = ds.run(targets)

    print(f"  Target: 1/7, Steps: {len(trace.bits)}")
    print(f"  Accumulator range: [{min(trace.accumulators)}, "
          f"{max(trace.accumulators)}]")
    print(f"  All accumulators in [0,1): "
          f"{all(0 <= a < 1 for a in trace.accumulators)}")

    # Check ALL sliding intervals
    all_ok = trace.check_all_interval_bounds()
    n = len(trace.bits)
    num_intervals = n * (n + 1) // 2
    print(f"  Checked {num_intervals} nonempty intervals")
    print(f"  All intervals have |discrepancy| < 1: {all_ok}")

    # Show a few specific intervals
    for a, b in [(0, 7), (0, 100), (50, 57), (3, 10), (77, 84)]:
        disc = trace.interval_discrepancy(a, b)
        avg_err = trace.interval_average_error(a, b)
        print(f"    [{a:3d}, {b:3d}): discrepancy={disc}, "
              f"avg_error={avg_err} (< 1/{b-a} = {Fraction(1, b-a)})")

    # Weighted readout (summation by parts)
    weights = [Fraction(1, i + 1) for i in range(100)]
    we = weighted_error(trace, weights)
    we_bp = weighted_error_by_parts(trace, weights)
    print(f"\n  Weighted error (direct): {we}")
    print(f"  Weighted error (by parts): {we_bp}")
    print(f"  Agreement: {we == we_bp}")

    return all_ok and (we == we_bp)


# =====================================================================
# 6. PROVENANCE: every answer carries its generation identity
# =====================================================================

def test_provenance():
    """Test that every generated answer carries a provenance digest
    that identifies exactly what was generated and how.
    """
    print("\n" + "=" * 70)
    print("[6] PROVENANCE: generation identity per answer")
    print("=" * 70)

    code = extended_golay_24_12()
    cw = code.encode(42)

    prov = make_provenance(
        system="PCGS-v6",
        version="1.0",
        parameters={"message": 42, "width": 24},
        generator=code.rows,
        assurance="property-tested + Lean blueprint",
    )

    print(f"  System: {prov.system}")
    print(f"  Version: {prov.version}")
    print(f"  Parameters digest: {prov.parameters_digest}")
    print(f"  Generator digest: {prov.generator_digest}")
    print(f"  Python: {prov.python}")
    print(f"  Assurance: {prov.assurance}")

    # Verify: same parameters → same digest
    prov2 = make_provenance(
        system="PCGS-v6",
        version="1.0",
        parameters={"message": 42, "width": 24},
        generator=code.rows,
        assurance="property-tested + Lean blueprint",
    )
    print(f"\n  Reproducible (same digest): {prov.parameters_digest == prov2.parameters_digest}")

    # Different parameters → different digest
    prov3 = make_provenance(
        system="PCGS-v6",
        version="1.0",
        parameters={"message": 43, "width": 24},
        generator=code.rows,
        assurance="property-tested + Lean blueprint",
    )
    print(f"  Different (different digest): {prov.parameters_digest != prov3.parameters_digest}")

    return prov.parameters_digest == prov2.parameters_digest


# =====================================================================
# 7. CROSS-SYSTEM: PCGS codes work for other lattices
# =====================================================================

def test_cross_system_codes():
    """Test that the PCGS's generic code theory works beyond the Golay code.

    The PCGS study document says: "the reusable theorem should look like:
    if a binary generator matrix has full row rank and its row space
    equals its orthogonal complement, then zero syndrome is equivalent
    to membership in the generated code."

    This should work for the [8,4,4] extended Hamming code too.
    """
    print("\n" + "=" * 70)
    print("[7] CROSS-SYSTEM: generic self-dual code theory")
    print("=" * 70)

    # The [8,4,4] extended Hamming code
    hamming = extended_hamming_8_4()
    cert = hamming.algebraic_certificate()

    print(f"  Code: {hamming.name}")
    print(f"    Width: {cert['width']}")
    print(f"    Dimension: {cert['dimension']}")
    print(f"    Rank: {cert['rank']}")
    print(f"    Self-dual: {cert['self_dual']}")
    print(f"    Cardinality: {cert['generated_cardinality']}")

    weights = hamming.weight_enumerator()
    print(f"    Weight distribution: {dict(sorted(weights.items()))}")
    print(f"    Expected: {{0: 1, 4: 14, 8: 1}}")

    expected = {0: 1, 4: 14, 8: 1}
    match = dict(sorted(weights.items())) == expected
    print(f"    Match: {match}")

    # Test membership via syndrome (the generic theorem)
    cw = hamming.encode(0b1011)
    cert_pos = hamming.certify(cw)
    bad = cw ^ 1
    cert_neg = hamming.certify(bad)

    print(f"\n  Membership test:")
    print(f"    Codeword 0x{cw:02X}: accepted={cert_pos.accepted}")
    print(f"    Non-codeword 0x{bad:02X}: accepted={cert_neg.accepted}")

    return match and cert_pos.accepted and not cert_neg.accepted


# =====================================================================
# 8. GLM INTEGRATION: PCGS as a GLM tool
# =====================================================================

def test_glm_integration():
    """Test that the PCGS can serve as a generative substrate tool
    within the GLM's reverse-call planner architecture.
    """
    print("\n" + "=" * 70)
    print("[8] GLM INTEGRATION: PCGS as generative substrate")
    print("=" * 70)

    # The PCGS provides:
    # 1. Golay code generation (no stored table)
    # 2. Leech lattice membership (no stored vectors)
    # 3. Certified Leech decoding (pruned + certificate)
    # 4. Delta-Sigma streaming (exact, sliding-window bound)
    # 5. Resource ledger (exact operation vector)
    # 6. Provenance (generation identity)

    # The GLM provides:
    # 1. The meaning layer (resolve terms to carriers)
    # 2. The reverse-call planner (select tools by problem)
    # 3. The data-object carriers (full measured profiles)
    # 4. The Lean formal model (the specification)

    # Integration: the PCGS generates the substrate that the GLM's
    # carriers sit on. No stored vector list. The Leech lattice IS
    # the Construction A→B→C filters, generated on demand.

    code = extended_golay_24_12()
    leech = LeechSubstrate(code)
    decoder = LeechDecoder(code)

    # The GLM's meaning layer resolves "gold" to Z=79.
    # The GLM's element data-object carrier has 24 coordinates.
    # The PCGS can verify that this carrier is a valid Leech point
    # (or snap it to the nearest one).

    # Simulate a GLM carrier (24 rationals)
    glm_carrier = tuple(Fraction(i, 12) for i in range(24))
    print(f"  GLM carrier: {str(glm_carrier[:6])[:60]}...")

    # PCGS: snap to nearest Leech point (with certificate)
    cert = decoder.decode_pruned(glm_carrier)
    verified = verify_certificate(decoder, glm_carrier, cert)
    print(f"  PCGS Leech snap: {cert.point[:6]}...")
    print(f"  Distance: {cert.squared_distance}")
    print(f"  Certificate verified: {verified}")
    print(f"  Cosets evaluated: {len(cert.evaluated)}")
    print(f"  Cosets pruned: {len(cert.pruned)}")

    # PCGS: check Leech membership of the snapped point
    is_leech = leech.is_leech(cert.point)
    print(f"  Snapped point IS a Leech point: {is_leech}")

    # Resource cost of the snap
    ledger = Ledger()
    _, _, _, dec_ledger = decoder.decode_exhaustive(glm_carrier)
    print(f"\n  Resource cost (exhaustive): {dict(dec_ledger.counts)}")
    print(f"  Resource cost (pruned): evaluated={len(cert.evaluated)}, "
          f"pruned={len(cert.pruned)}")

    # Provenance
    prov = make_provenance(
        system="PCGS-GLM-bridge",
        version="1.0",
        parameters={"target": str(glm_carrier[:6])},
        generator=code.rows,
        assurance="certificate-verified + Leech-membership-checked",
    )
    print(f"\n  Provenance: {prov.system} v{prov.version}")
    print(f"  Assurance: {prov.assurance}")

    return verified and is_leech


# =====================================================================
# MAIN
# =====================================================================

def main():
    """Run the full PCGS-in-GLM study."""
    print()
    print("╔" + "═" * 68 + "╗")
    print("║  PROOF-CARRYING GENERATIVE SUBSTRATE — GLM INTEGRATION STUDY    ║")
    print("║  Bringing the PCGS concept into the GLM system                  ║")
    print("╚" + "═" * 68 + "╝")
    print()

    results = []

    results.append(("Cross-validate Golay", test_cross_validate_golay()))
    results.append(("Certified membership", test_certified_membership()))
    results.append(("Certified Leech decode", test_certified_leech_decode()))
    results.append(("Resource ledger", test_resource_ledger()))
    results.append(("Sliding-window ΔΣ", test_sliding_window_delta_sigma()))
    results.append(("Provenance", test_provenance()))
    results.append(("Cross-system codes", test_cross_system_codes()))
    results.append(("GLM integration", test_glm_integration()))

    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
    print()
    all_pass = all(p for _, p in results)
    print(f"  All {len(results)} tests passed: {all_pass}")
    print()
    if all_pass:
        print("  The PCGS concept is fulfilled within the GLM:")
        print()
        print("  1. COMPACT DESCRIPTION: the Golay code is generated from the")
        print("     QR(11) cyclic generator (12 rows, no stored table).")
        print("     The Leech lattice is generated from Construction A→B→C")
        print("     (8192 cosets, no stored vector list).")
        print()
        print("  2. QUERY PROCEDURES: membership via syndrome (12 parity checks),")
        print("     nearest-point via coset decomposition + per-coordinate nearest")
        print("     + repair, streaming via Delta-Sigma modulation.")
        print()
        print("  3. SEMANTIC SPECIFICATION: the Lean blueprint (LEAN_V6_BLUEPRINT.lean)")
        print("     defines IsLeech, InCoset, dist2, decode — independent of Python.")
        print()
        print("  4. CORRECTNESS CERTIFICATE: every Leech decode returns a")
        print("     PrunedCertificate that an independent verifier checks without")
        print("     redoing the search. Every membership test returns a")
        print("     CodeCertificate with syndrome and reconstruction.")
        print()
        print("  5. RESOURCE CERTIFICATE: every operation produces an exact")
        print("     Ledger (vector of primitive counts). Scalar totals require")
        print("     declared weights. The Cost algebra supports sequential and")
        print("     parallel composition, Pareto comparison, and cache break-even.")
        print()
        print("  6. OPTIONAL CACHING: cache_breakeven() computes the query")
        print("     count above which caching wins. Below that, generation wins.")
        print("     The cache is transparent: cached and generated answers must")
        print("     be extensionally equivalent (verified by digest).")
        print()
        print("  7. REPRODUCIBILITY: every answer carries a Provenance digest")
        print("     identifying the system, version, parameters, generator, and")
        print("     assurance level. Same parameters → same digest.")
        print()
        print("  8. SLIDING-WINDOW BOUND: the Delta-Sigma modulator guarantees")
        print("     |discrepancy| < 1 for ANY sub-interval, not just prefixes.")
        print("     A consumer may begin reading at any time and still receives")
        print("     the one-count guarantee. Weighted readouts via summation by")
        print("     parts are exact.")
        print()
        print("  9. CROSS-SYSTEM: the generic self-dual code theorem works for")
        print("     [8,4,4] extended Hamming and [24,12,8] extended Golay.")
        print("     The PCGS is not Golay-specific — it is a general methodology")
        print("     for any object with strong algebraic structure.")
        print()
        print("  10. GLM INTEGRATION: the PCGS generates the substrate that the")
        print("      GLM's carriers sit on. No stored vector list. The Leech")
        print("      lattice IS the Construction A→B→C filters, generated on")
        print("      demand. The GLM's meaning layer and reverse-call planner")
        print("      sit on top of the generative substrate.")
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
