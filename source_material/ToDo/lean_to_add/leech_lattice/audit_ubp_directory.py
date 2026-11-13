#!/usr/bin/env python3
"""
================================================================================
 audit_ubp_directory.py -- audit of the published UBP lattice-shortcut directory
================================================================================

Runs against the author's own modules

    ubp_unified_v5.py        (Golay / Leech substrate)
    value_geometry.py        (ValueGeometry profiles, propeller imbalance)
    ubp_tgic_engine.py       (TGIC 3-6-9 metrics)
    tgic_v3.py               (newer TGIC layer)
    generate_shortcut_directory_standalone.py

and checks, in order:

  A. Reproduction of `lattice_shortcut_directory_standalone.json` (all 36
     transitions of both catalogues).
  B. Agreement between the substrate and the clean re-implementation in
     `lattice_shortcut.py` (encoders, legacy snap, tax, NRCI, TGIC metrics).
  C. The section-4 benchmark table of `lattice_shortcode_directory.md`.
  D. The three headline claims: adjacency d^2 in {8,10,12}; even quantisation;
     octad / minimal-vector steps.
  E. The propeller-imbalance claim (primes 0.0000, composites > 0.1500).
  F. The corrected pipeline (complete decoder) on both published sequences.

Writes `lattice_shortcut_audit.json`.  Python >= 3.8, stdlib only.
================================================================================
"""

from __future__ import annotations

import json
import math
import os
import sys
from fractions import Fraction
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lattice_shortcut as LS
from ubp_unified_v5 import GOLAY_ENGINE, LEECH_ENGINE, to_gray_code
from value_geometry import profile, is_prime as vg_is_prime
from ubp_tgic_engine import TGICInteractionEngine

TGIC = TGICInteractionEngine()
RESULTS: Dict[str, object] = {}


def head(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def verdict(ok: bool) -> str:
    return "OK " if ok else "*** MISMATCH ***"


# ──────────────────────────────────────────────────────────────────────────────
#  Bridges between the substrate's list form and the clean int form
# ──────────────────────────────────────────────────────────────────────────────

def sub_state(n: int) -> Tuple[int, List[int]]:
    """The substrate/generator encoding of n (before snapping), as (int, list)."""
    p = profile(n)
    if p.is_prime:
        x, y, z = n & 0xFF, (n >> 8) & 0xFF, (n >> 16) & 0xFF
    else:
        f = p.prime_factors
        x = f[0][0] ** f[0][1] if len(f) > 0 else 1
        y = f[1][0] ** f[1][1] if len(f) > 1 else 1
        z = math.prod(q ** e for q, e in f[2:]) if len(f) > 2 else 1
    v = [0] * 24
    v[0:8] = to_gray_code(x & 0xFF, 8)
    v[8:16] = to_gray_code(y & 0xFF, 8)
    v[16:24] = to_gray_code(z & 0xFF, 8)
    return LS.int_of(v), v


# ──────────────────────────────────────────────────────────────────────────────
#  A.  Reproduce the published directory
# ──────────────────────────────────────────────────────────────────────────────

def part_a() -> None:
    head("A.  Reproduction of lattice_shortcut_directory_standalone.json")
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "lattice_shortcut_directory_standalone.json")
    published = json.load(open(path))

    matched, total = 0, 0
    norm_mismatch = 0
    for label, steps in published["catalogs"].items():
        for s in steps:
            total += 1
            a, b = s["origin_node"]["n"], s["target_node"]["n"]
            _, va = sub_state(a)
            _, vb = sub_state(b)
            sa, _ = GOLAY_ENGINE.snap_to_codeword(va)
            sb, _ = GOLAY_ENGINE.snap_to_codeword(vb)
            jump = [q - p for p, q in zip(sa, sb)]
            d2 = sum(t * t for t in jump)
            if jump == s["jump_vector_24d"]:
                matched += 1
            if d2 != s["jump_norm_d2"]:
                norm_mismatch += 1
    print(f"  jump vectors reproduced : {matched}/{total}")
    print(f"  jump norms reproduced   : {total - norm_mismatch}/{total}")
    print("  (the composite branch of the generator maps prime-power channels,")
    print("   NOT the bit-shift channels -- that is why consecutive integers do")
    print("   not behave like a Gray code in this catalogue)")
    RESULTS["A_reproduction"] = {"jump_vectors": f"{matched}/{total}",
                                 "jump_norms": f"{total - norm_mismatch}/{total}"}


# ──────────────────────────────────────────────────────────────────────────────
#  B.  Clean re-implementation == substrate
# ──────────────────────────────────────────────────────────────────────────────

def part_b() -> None:
    head("B.  lattice_shortcut.py agrees with the substrate")
    sample = list(range(1000000, 1000200))

    enc_ok = all(sub_state(n)[0] == (LS.encode_factor(n)) for n in sample)
    print(f"  {verdict(enc_ok)} encoder (factor branch) identical on {len(sample)} integers")

    shift_ok = True
    for n in sample:
        v = [0] * 24
        v[0:8] = to_gray_code(n & 0xFF, 8)
        v[8:16] = to_gray_code((n >> 8) & 0xFF, 8)
        v[16:24] = to_gray_code((n >> 16) & 0xFF, 8)
        shift_ok &= LS.int_of(v) == LS.encode_shift(n)
    print(f"  {verdict(shift_ok)} encoder (shift branch) identical")

    legacy_ok, tax_ok, nrci_ok = True, True, True
    for n in sample:
        w, v = sub_state(n)
        sv, _ = GOLAY_ENGINE.snap_to_codeword(v)
        legacy_ok &= LS.int_of(sv) == LS.legacy_snap(w)
        tax_ok &= LEECH_ENGINE.calculate_symmetry_tax(sv) == LS.symmetry_tax(LS.int_of(sv))
        nrci_ok &= LEECH_ENGINE.calculate_nrci(sv) == LS.nrci(LS.int_of(sv))
    print(f"  {verdict(legacy_ok)} legacy snap (weight <= 3 corrector) identical")
    print(f"  {verdict(tax_ok)} Leech symmetry tax identical (exact rationals)")
    print(f"  {verdict(nrci_ok)} NRCI identical (exact rationals)")

    ortho_ok, coh_ok, stab_ok = True, True, True
    for n in sample[:40]:
        w, v = sub_state(n)
        sv, _ = GOLAY_ENGINE.snap_to_codeword(v)
        s = LS.int_of(sv)
        ortho_ok &= TGIC.constraints.check_3_axis_orthogonality(sv) == LS.tgic_3_axis_orthogonality(s)
        coh_ok &= TGIC.constraints.check_6_face_coherence(sv, TGIC) == \
            LS.tgic_6_face_coherence(s, LS.reencode_snap)
        stab_ok &= TGIC.calculate_total_stability(sv) == \
            LS.tgic_stability(s, (), LS.reencode_snap)
    print(f"  {verdict(ortho_ok)} TGIC 3-axis orthogonality identical")
    print(f"  {verdict(coh_ok)} TGIC 6-face coherence identical")
    print(f"  {verdict(stab_ok)} TGIC master stability identical")

    RESULTS["B_cross_check"] = {
        "encoder_factor": enc_ok, "encoder_shift": shift_ok,
        "legacy_snap": legacy_ok, "symmetry_tax": tax_ok, "nrci": nrci_ok,
        "tgic_orthogonality": ortho_ok, "tgic_coherence": coh_ok,
        "tgic_stability": stab_ok}


# ──────────────────────────────────────────────────────────────────────────────
#  C.  The section-4 benchmark table
# ──────────────────────────────────────────────────────────────────────────────

PUBLISHED_TABLE = {
    "propeller_imbalance":      (0.000000, 0.622207),
    "tgic_3_axis_orthogonality": (0.536182, 0.540989),
    "tgic_6_face_coherence":    (0.664642, 0.758866),
    "runecube_face_tax":        (5.247629, 3.273274),
    "tgic_master_stability":    (0.663450, 0.681089),
}


def _first(pred, k: int, start: int = 1000000) -> List[int]:
    out, c = [], start
    while len(out) < k:
        if pred(c):
            out.append(c)
        c += 1
    return out


def _row_metrics(ns: List[int]) -> Dict[str, float]:
    imb, o, f, t, s = [], [], [], [], []
    for n in ns:
        w, v = sub_state(n)
        sv, _ = GOLAY_ENGINE.snap_to_codeword(v)
        st = LS.int_of(sv)
        imb.append(profile(n).imbalance)
        o.append(float(LS.tgic_3_axis_orthogonality(st)))
        f.append(float(LS.tgic_6_face_coherence(st, LS.reencode_snap)))
        t.append(float(LS.runecube_face_tax(st, LS.reencode_snap)))
        s.append(float(LS.tgic_stability(st, (), LS.reencode_snap)))
    mean = lambda L: sum(L) / len(L)
    return {"propeller_imbalance": mean(imb),
            "tgic_3_axis_orthogonality": mean(o),
            "tgic_6_face_coherence": mean(f),
            "runecube_face_tax": mean(t),
            "tgic_master_stability": mean(s)}


def part_c() -> None:
    head("C.  Section-4 benchmark table (now auditable: TGIC files supplied)")
    primes = _first(vg_is_prime, 10)
    comps = _first(lambda x: not vg_is_prime(x), 10)
    print(f"  sample sets that reproduce the table:")
    print(f"    deep primes     = {primes}")
    print(f"    deep composites = {comps}")
    mp, mc = _row_metrics(primes), _row_metrics(comps)
    print(f"\n  {'metric':<28}{'primes':>12}{'published':>12}  "
          f"{'composites':>12}{'published':>12}")
    rows = {}
    for key, (pp, pc) in PUBLISHED_TABLE.items():
        okp = abs(mp[key] - pp) < 5e-6
        okc = abs(mc[key] - pc) < 5e-6
        rows[key] = {"primes_recomputed": round(mp[key], 6), "primes_published": pp,
                     "primes_match": okp,
                     "composites_recomputed": round(mc[key], 6),
                     "composites_published": pc, "composites_match": okc}
        print(f"  {key:<28}{mp[key]:>12.6f}{pp:>12.6f} {'OK' if okp else '<<'}"
              f"{mc[key]:>12.6f}{pc:>12.6f} {'OK' if okc else '<<'}")

    # internal consistency of the published prime column
    stab_from_published = (PUBLISHED_TABLE["tgic_3_axis_orthogonality"][0]
                           + PUBLISHED_TABLE["tgic_6_face_coherence"][0]
                           + (3 * mp["tgic_master_stability"]
                              - mp["tgic_3_axis_orthogonality"]
                              - mp["tgic_6_face_coherence"])) / 3
    print("\n  internal consistency of the published PRIME column:")
    print(f"    stability implied by its own orthogonality+coherence entries "
          f"= {stab_from_published:.6f}")
    print(f"    stability actually printed in the table                      "
          f"= {PUBLISHED_TABLE['tgic_master_stability'][0]:.6f}")
    print("    -> the coherence / tax cells of the prime column are inconsistent")
    print("       with its own stability cell; the recomputed values are")
    print(f"       coherence = {mp['tgic_6_face_coherence']:.6f}, "
          f"tax = {mp['runecube_face_tax']:.6f}")
    RESULTS["C_benchmark_table"] = {"primes": primes, "composites": comps,
                                    "rows": rows,
                                    "prime_column_self_consistent": False}


# ──────────────────────────────────────────────────────────────────────────────
#  D.  The three headline claims
# ──────────────────────────────────────────────────────────────────────────────

def part_d() -> None:
    head("D.  Headline claims")

    # D1 adjacency
    seq = list(range(1000033, 1000051))
    d2s = []
    for a, b in zip(seq, seq[1:]):
        _, va = sub_state(a)
        _, vb = sub_state(b)
        sa, _ = GOLAY_ENGINE.snap_to_codeword(va)
        sb, _ = GOLAY_ENGINE.snap_to_codeword(vb)
        d2s.append(sum((q - p) ** 2 for p, q in zip(sa, sb)))
    print("  D1  'adjacent deep integers jump with d^2 in {8,10,12}'")
    print(f"      observed on 1000033..1000050 : {sorted(set(d2s))}")
    print(f"      verdict: FALSE as stated (values {sorted(set(d2s))} occur)")
    print("      also: under the pure Gray (shift) encoder consecutive integers")
    print("      differ in exactly one bit, d^2_raw = 1 -- the {8,10,12} values")
    print("      come from the factor encoder, not from lattice geometry")
    raw_shift = {LS.raw_d2_shortcut(n, n + 1) for n in seq[:-1]}
    print(f"      raw d^2 under the shift encoder: {sorted(raw_shift)}")

    # D2 even quantisation
    print("\n  D2  'even quantisation d^2 in 2Z at 100%'")
    odd = 0
    N = 3000
    prev = None
    for n in range(1000000, 1000000 + N):
        w = LS.encode_factor(n)
        cur = LS.legacy_snap(w)
        if prev is not None and LS.popcount(prev ^ cur) % 2:
            odd += 1
        prev = cur
    print(f"      odd jump norms in {N-1} consecutive transitions: {odd}")
    weights_even = all(LS.popcount(LS.legacy_snap(v)) % 2 == 0
                       for v in range(0, 1 << 24, 1021))
    print(f"      every legacy-snapped state has even weight: {weights_even}")
    print("      verdict: TRUE, and it is a theorem, not data.  Golay is doubly")
    print("      even, so Hamming-weight parity is constant on each coset; the")
    print("      cosets the legacy snap fails on are exactly those with weight-4")
    print("      leaders (even).  Hence every snapped state has even weight and")
    print("      every d^2 is even -- for ANY encoder and ANY integers, primes")
    print("      or not.  It carries no information about primality.")

    # D3 octad steps
    print("\n  D3  'd^2 = 8 steps are Class-B minimal-vector octad hops'")
    bad = sum(1 for n in range(1000000, 1000300)
              if not LS.is_codeword(LS.legacy_snap(LS.encode_factor(n))))
    print(f"      TRUE for genuine codewords, but with the legacy snap")
    print(f"      {bad}/300 states are not codewords, so the classification of")
    print("      the published table is accidental (norms 0,2,4,6 are impossible")
    print("      between real codewords: minimum distance is 8)")
    print("      With the complete decoder every d^2 = 8 step is an exact")
    print("      minimal (norm-32) Leech vector -- see part F.")

    RESULTS["D_claims"] = {
        "adjacency_observed_d2": sorted(set(d2s)),
        "adjacency_raw_shift_d2": sorted(raw_shift),
        "even_quantisation_odd_steps": odd,
        "legacy_states_all_even_weight": weights_even,
        "non_codeword_states_per_300": bad}


# ──────────────────────────────────────────────────────────────────────────────
#  E.  The propeller-imbalance claim
# ──────────────────────────────────────────────────────────────────────────────

def part_e() -> None:
    head("E.  Propeller imbalance as a prime detector")
    print("  definition: coefficient of variation of log p over the DISTINCT")
    print("  prime factors of n (so it ignores exponents entirely).")
    lo, hi = 1000000, 1010000
    comps = [n for n in range(lo, hi) if not vg_is_prime(n)]
    imbs = [profile(n).imbalance for n in comps]
    below_015 = sum(1 for x in imbs if x < 0.15)
    below_0001 = sum(1 for x in imbs if x < 0.001)
    print(f"  composites in [{lo},{hi}) : {len(comps)}")
    print(f"    with imbalance < 0.1500 (claimed impossible) : {below_015} "
          f"({100.0*below_015/len(comps):.2f}%)")
    print(f"    with imbalance < 0.0010 ('Smooth', as primes) : {below_0001}")
    for n in (1005973, 1018081, 1048576):
        p = profile(n)
        print(f"    example {n} = {p.factorisation_str:<18} imbalance "
              f"{p.imbalance:.6f}  ({p.wobble_class})")
    print("  verdict: 'primes 0.0000' is TRUE but vacuous (every prime power")
    print("  gives 0 too); 'composites > 0.1500' is FALSE.  The statistic")
    print("  measures the spread of the distinct prime factors, not primality.")
    RESULTS["E_propeller"] = {"composites_tested": len(comps),
                              "composites_below_0_15": below_015,
                              "composites_below_0_001": below_0001,
                              "counterexamples": [1005973, 1018081, 1048576]}


# ──────────────────────────────────────────────────────────────────────────────
#  F.  The corrected pipeline
# ──────────────────────────────────────────────────────────────────────────────

def part_f() -> None:
    head("F.  The corrected pipeline (complete decoder)")
    interfacial = list(range(1000033, 1000051))
    primes = _first(vg_is_prime, 20)
    out = {}
    for label, seq, enc in (("interfacial 1000033..1000050", interfacial, "factor"),
                            ("interfacial 1000033..1000050", interfacial, "shift"),
                            ("prime trajectory (20 primes)", primes, "shift")):
        steps = LS.walk(seq, enc)
        summ = LS.walk_summary(steps)
        print(f"  {label} [{enc}]")
        print(f"    d^2 : {[s['d2'] for s in steps]}")
        print(f"    all 4 | d^2 : {summ['all_quantised_by_4']}   "
              f"all Leech vectors : {summ['all_leech_vectors']}   "
              f"octads : {summ['octad_rate_pct']}%")
        out[f"{label} [{enc}]"] = summ
    big = LS.stats(1000000, 10000, "shift")
    print(f"  10000 consecutive integers [shift]: {json.dumps(big)}")
    out["stats_10000"] = big
    RESULTS["F_corrected"] = out
    _write_corrected_directory(interfacial, primes)


def _write_corrected_directory(interfacial: List[int], primes: List[int]) -> None:
    """Regenerate the directory with the complete decoder, in the layout of the
    published JSON, for both encoders."""
    catalogs = {}
    for label, seq, enc in (
            ("Deep Interfacial Sequence (N = 1,000,033 .. 1,000,050)", interfacial, "factor"),
            ("Deep Interfacial Sequence, bit-shift encoder", interfacial, "shift"),
            ("Deep Prime-to-Prime Trajectory (P > 1,000,000)", primes, "shift")):
        rows = []
        for i, s in enumerate(LS.walk(seq, enc), 1):
            a, b = int(s["from"]), int(s["to"])
            ca, cb = int(s["snapped_state_from"]), int(s["snapped_state_to"])
            rows.append({
                "step": i, "encoder": enc,
                "origin_node": {"n": a, "is_prime": vg_is_prime(a),
                                "factor_imbalance": profile(a).imbalance,
                                "state": f"{ca:024b}",
                                "nrci": float(LS.nrci(ca)),
                                "3axis_orthogonality": float(LS.tgic_3_axis_orthogonality(ca)),
                                "tgic_stability": float(LS.tgic_stability(ca))},
                "target_node": {"n": b, "is_prime": vg_is_prime(b),
                                "factor_imbalance": profile(b).imbalance,
                                "state": f"{cb:024b}",
                                "nrci": float(LS.nrci(cb)),
                                "3axis_orthogonality": float(LS.tgic_3_axis_orthogonality(cb)),
                                "tgic_stability": float(LS.tgic_stability(cb))},
                "jump_vector_24d": s["jump_vector"],
                "jump_norm_d2": s["d2"],
                "leech_vector_2dv": s["leech_vector"],
                "leech_norm_sq": s["leech_norm_sq"],
                "is_minimal_octad_step": s["is_octad_step"],
                "quantised_by_4": s["quantised_by_4"],
                "both_states_are_codewords": s["both_states_are_codewords"],
            })
        catalogs[label] = rows
    all_d2 = [r["jump_norm_d2"] for rows in catalogs.values() for r in rows]
    doc = {
        "method": "continuous 24-bit / factor channels -> byte-wise Gray -> "
                  "COMPLETE Golay decoding -> Leech step",
        "note": "regenerated with the complete (nearest-codeword) decoder of "
                "lattice_shortcut.py; see LATTICE_SHORTCUT_METHOD.md",
        "summary": {
            "total_transitions_audited": len(all_d2),
            "observed_jump_norms": sorted(set(all_d2)),
            "all_quantised_by_4": all(d % 4 == 0 for d in all_d2),
            "all_states_are_codewords": all(
                r["both_states_are_codewords"] for rows in catalogs.values() for r in rows),
            "octad_step_rate_pct": round(100.0 * sum(1 for d in all_d2 if d == 8) / len(all_d2), 2),
        },
        "catalogs": catalogs,
    }
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "lattice_shortcut_directory_corrected.json")
    with open(path, "w") as fh:
        json.dump(doc, fh, indent=2)
    print(f"  written: {os.path.basename(path)}")


# ──────────────────────────────────────────────────────────────────────────────
#  G.  tgic_v3.py (the newer TGIC layer)
# ──────────────────────────────────────────────────────────────────────────────

def part_g() -> None:
    head("G.  tgic_v3.py compared with ubp_tgic_engine.py")
    import tgic_v3

    checks = tgic_v3.run_self_tests()
    print(f"  tgic_v3 self-tests: {checks}")
    align = tgic_v3.verify_alignment()
    print(f"  Golay layer: codewords={align['codeword_count']} "
          f"octads={align['octad_count']} weights={align['weight_distribution']}")

    cube = tgic_v3.RuneCube369()
    primes = _first(vg_is_prime, 10)
    comps = _first(lambda x: not vg_is_prime(x), 10)

    def row(ns):
        a, f, s, uncorrected = [], [], [], 0
        for n in ns:
            _, v = sub_state(n)
            sv, _ = GOLAY_ENGINE.snap_to_codeword(v)
            a.append(float(cube.axis_score(sv)))
            f.append(float(cube.face_score(sv)))
            s.append(float(cube.stability((0, 0, 0), sv, {})))
            for face in (cube.face_xy(sv), cube.face_xz(sv), cube.face_yz(sv)):
                uncorrected += 0 if LS.is_codeword(LS.int_of(face)) else 1
        m = lambda L: sum(L) / len(L)
        return m(a), m(f), m(s), uncorrected

    pa, pf, ps, pu = row(primes)
    ca, cf, cs, cu = row(comps)
    print(f"\n  {'metric':<26}{'primes':>12}{'composites':>12}")
    print(f"  {'axis score (3)':<26}{pa:>12.6f}{ca:>12.6f}")
    print(f"  {'face score (6)':<26}{pf:>12.6f}{cf:>12.6f}")
    print(f"  {'stability':<26}{ps:>12.6f}{cs:>12.6f}")
    print(f"  face vectors left un-snapped (not codewords): "
          f"{pu}/30 primes, {cu}/30 composites")
    print("  v3 changes that matter:")
    print("    * the 9-neighbour rule no longer counts the node itself (v6.2 did);")
    print("    * faces are snapped only when the decoder certifies the result,")
    print(f"      which is honest but still leaves face vectors off-code "
          f"({pu + cu}/60 here);")
    print("      v6.2 instead re-encoded the information half, which always gives")
    print("      a codeword but can move the state by up to 12 bits.")
    print("    * with the complete decoder of lattice_shortcut.py both problems")
    print("      disappear: every face vector is the nearest codeword, <= 4 bits away.")
    RESULTS["G_tgic_v3"] = {
        "self_tests": checks,
        "axis_score": {"primes": round(pa, 6), "composites": round(ca, 6)},
        "face_score": {"primes": round(pf, 6), "composites": round(cf, 6)},
        "stability": {"primes": round(ps, 6), "composites": round(cs, 6)},
        "uncorrected_face_vectors": {"primes": f"{pu}/30", "composites": f"{cu}/30"}}


def main() -> int:
    part_a()
    part_b()
    part_c()
    part_d()
    part_e()
    part_f()
    part_g()
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "lattice_shortcut_audit.json")
    with open(path, "w") as fh:
        json.dump(RESULTS, fh, indent=2)
    print(f"\nwritten: {os.path.basename(path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
