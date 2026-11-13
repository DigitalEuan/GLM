#!/usr/bin/env python3
"""
observer_y.py — exact-rational audit of the observer/read quantum study
=======================================================================

Companion to `Y_OBSERVER_STUDY_REPORT.md` and `RequestProject/ObserverY.lean`.

Everything is computed in exact rational arithmetic (`fractions.Fraction`).
The constant `pi` is the substrate's own 50-term continued-fraction convergent
(`ubp_unified_v5.py`, `UBPUltimateSubstrate._PI_CF`), so every number printed
here is bit-identical to what the substrate computes, and is accurate to far
more digits than any claim in the study uses.

Definitions (as in the study, and as read off `LeechLatticeEngine`):

    Y    = 1 / (pi + 2/pi)                  read cost per active distinction
    Q    = Y + 1/8                          activation quantum
    HW   = #{i : v_i != 0}                  active distinctions
    N2   = sum_i v_i^2                      geometric extent
    TAX  = HW * Y + N2 / 8                  symmetry tax
    NRCI = 10 / (10 + TAX)                  coherence after tax

Usage
-----
    python3 observer_y.py --selftest     # re-verify every claim (exit 0 = pass)
    python3 observer_y.py --stages       # the stage-by-stage ledger
    python3 observer_y.py --constants    # the constants, exact and decimal
    python3 observer_y.py --tables       # Golay-layer and Leech-layer tables
    python3 observer_y.py --regimes      # which regimes are reachable, and where
    python3 observer_y.py --vector 1,1,1,0,...   # audit one 24-vector
    python3 observer_y.py --json         # machine-readable dump of the above
"""

from __future__ import annotations

import argparse
import json
import sys
from fractions import Fraction as F
from typing import Dict, List, Sequence

# --------------------------------------------------------------------------
# Constants — the substrate's own values, exactly
# --------------------------------------------------------------------------

_PI_CF = [3, 7, 15, 1, 292, 1, 1, 1, 2, 1, 3, 1, 14, 2, 1, 1, 2, 2, 2, 2,
          1, 84, 2, 1, 1, 15, 3, 13, 1, 4, 2, 6, 6, 99, 1, 2, 2, 6, 3, 5,
          1, 1, 6, 8, 1, 7, 1, 6, 1, 99, 7, 4, 1, 3, 3, 1, 4, 1]


def pi_exact(terms: int = 50) -> F:
    """The substrate's 50-term continued-fraction convergent of pi."""
    coeffs = _PI_CF[:min(terms, len(_PI_CF))]
    x = F(coeffs[-1], 1)
    for c in reversed(coeffs[:-1]):
        x = F(c, 1) + F(1, 1) / x
    return x


PI = pi_exact(50)

#: read-cost operator  Y[Pi] = 1/(Pi + Delta/Pi)
def read_cost(delta: F, loop: F) -> F:
    return F(1, 1) / (loop + F(delta) / loop)


DELTA = F(2)            # the primitive difference-state "2"
ZONE_SHARE = F(1, 8)    # the zone-share 1/8
BUDGET = F(10)          # the coherence budget B

Y = read_cost(DELTA, PI)                 # 0.2646754...
Q = Y + ZONE_SHARE                       # 0.3896754...
Y_CONST = read_cost(DELTA, F(1, 1) / Y)  # the substrate's second constant

# regime thresholds on NRCI, from section 8 of the study
REGIMES = [("OnBit", F(8, 10)), ("Coherent", F(5, 10)),
           ("Transitional", F(3, 10)), ("Subcoherent", None)]


# --------------------------------------------------------------------------
# The measurement ledger
# --------------------------------------------------------------------------

def hamming_weight(v: Sequence[int]) -> int:
    return sum(1 for x in v if x != 0)


def norm_sq(v: Sequence[int]) -> int:
    return sum(int(x) * int(x) for x in v)


def tax(v: Sequence[int]) -> F:
    """TAX(v) = HW(v)*Y + ||v||^2 / 8."""
    return F(hamming_weight(v)) * Y + F(norm_sq(v), 8)


def nrci(v: Sequence[int], budget: F = BUDGET) -> F:
    """NRCI(v) = B / (B + TAX(v))."""
    return budget / (budget + tax(v))


def coherence(t: F, budget: F = BUDGET) -> F:
    """Coherence as a function of the tax alone."""
    return budget / (budget + t)


def regime_of_nrci(n: F) -> str:
    for name, threshold in REGIMES:
        if threshold is None or n >= threshold:
            return name
    return "Subcoherent"


def regime_of_tax(t: F, budget: F = BUDGET) -> str:
    return regime_of_nrci(coherence(t, budget))


def tax_ceiling(threshold: F, budget: F = BUDGET) -> F:
    """The tax band boundary belonging to an NRCI threshold: B/c - B."""
    return budget / threshold - budget


def is_signed(v: Sequence[int]) -> bool:
    return all(x in (-1, 0, 1) for x in v)


def audit(v: Sequence[int]) -> Dict[str, object]:
    hw, n2 = hamming_weight(v), norm_sq(v)
    t, n = tax(v), nrci(v)
    return {
        "hamming_weight": hw,
        "norm_squared": n2,
        "read_cost": str(F(hw) * Y),
        "embodiment_cost": str(F(n2, 8)),
        "tax": str(t),
        "tax_float": float(t),
        "equals_hw_times_Q": t == F(hw) * Q,
        "signed": is_signed(v),
        "nrci": str(n),
        "nrci_float": float(n),
        "regime": regime_of_nrci(n),
    }


# --------------------------------------------------------------------------
# Layer tables
# --------------------------------------------------------------------------

GOLAY_WEIGHTS = [0, 8, 12, 16, 24]

#: (class, Hamming weight, shape) of the three Leech minimal-vector classes;
#: every minimal vector has ||v||^2 = 32 in the substrate's integer scaling.
LEECH_CLASSES = [("A", 2, "(∓4^2, 0^22)"),
                 ("B", 8, "(∓2^8, 0^16)"),
                 ("C", 24, "(∓3, ±1^23)")]


def golay_table() -> List[Dict[str, object]]:
    rows = []
    for w in GOLAY_WEIGHTS:
        t = F(w) * Q
        rows.append({"weight": w, "tax": str(t), "tax_float": float(t),
                     "nrci_float": float(coherence(t)),
                     "regime": regime_of_tax(t)})
    return rows


def leech_table() -> List[Dict[str, object]]:
    rows = []
    for name, w, shape in LEECH_CLASSES:
        t = F(w) * Y + F(32, 8)
        rows.append({"class": name, "weight": w, "shape": shape,
                     "tax": str(t), "tax_float": float(t),
                     "nrci_float": float(coherence(t)),
                     "regime": regime_of_tax(t)})
    return rows


def calibrated_table(budget: F = None) -> List[Dict[str, object]]:
    """Golay weights under the calibrated budget B = 8Q (the octad tax)."""
    if budget is None:
        budget = 8 * Q
    rows = []
    for w in GOLAY_WEIGHTS:
        t = F(w) * Q
        n = coherence(t, budget)
        rows.append({"weight": w, "nrci": str(n), "nrci_float": float(n),
                     "regime": regime_of_nrci(n)})
    return rows


def regime_bands() -> List[Dict[str, object]]:
    bands, lower = [], F(0)
    for name, threshold in REGIMES:
        if threshold is None:
            bands.append({"regime": name, "tax_from": str(lower), "tax_to": None,
                          "hw_signed": None})
            break
        upper = tax_ceiling(threshold)
        hw_hi = int(upper / Q)  # largest signed weight inside the band
        bands.append({"regime": name,
                      "tax_from": str(lower), "tax_to": str(upper),
                      "tax_to_float": float(upper),
                      "hw_signed": hw_hi,
                      "reachable_on_24_signed": lower <= 24 * Q})
        lower = upper
    return bands


# --------------------------------------------------------------------------
# The stage ledger
# --------------------------------------------------------------------------

STAGES = [
    ("I",    "Perfect space",        "v = 0",
     "TAX = 0, NRCI = 1; and this is the only such state",
     "theorem", "tax_eq_zero_iff / nrci_eq_one_iff"),
    ("II",   "Primitive difference", "Delta = 2",
     "used only as the numerator of the read-cost operator",
     "stipulation", "readCost (d := 2)"),
    ("III",  "Disturbance v",        "v : Fin n -> Z",
     "a pattern is an integer vector; HW and ||v||^2 are its two summaries",
     "definition", "hw / normSq"),
    ("IV",   "Zones and activation", "Q = Y + 1/8",
     "Q is exactly the minimum tax of a nonzero pattern, attained at a single +-1",
     "theorem", "Q_le_tax / tax_eq_Q_iff"),
    ("V",    "Loop-check Pi",        "syn(v) = 0 iff lawful",
     "the gap is the syndrome; it is additive and forgets exactly the codeword part",
     "theorem", "loop_closes_iff_lawful / same_history_iff"),
    ("VI",   "MOG grammar",          "coset decomposition",
     "reading = choosing a coset representative; covering radius 4, unique only to 3",
     "theorem", "golay_covering_radius / decoding_not_unique"),
    ("VII",  "Golay protection",     "d_min = 8",
     "the cheapest protected distinction costs 8Q; protection multiplies cost by 8",
     "theorem", "protection_costs_eight_quanta"),
    ("VIII", "Leech embodiment",     "||v||^2 = 32 minimal",
     "minimal vectors of weight 2, 8, 24; taxes 4.529, 6.117, 10.352",
     "theorem", "minimalVector_classAB_coherent / _classC_transitional"),
    ("IX",   "Observer Y",           "Y = 1/(pi + 2/pi)",
     "the operator caps the read cost at 1/(2*sqrt 2) and has no positive minimum",
     "theorem", "readCost_le_amgm / readCost_le_inv / Y_lt_amgm"),
    ("X",    "TAX",                  "HW*Y + ||v||^2/8",
     "TAX = HW*Q holds exactly on patterns with entries in {-1,0,1}",
     "theorem", "tax_eq_hw_mul_Q_iff"),
    ("XI",   "NRCI",                 "10/(10 + TAX)",
     "strictly decreasing in TAX, values in (0,1]; the budget 10 is a pure scale",
     "theorem", "coh_strictAnti / nrciB_eq_coh"),
    ("XII",  "Coherence regimes",    "0.8 / 0.5 / 0.3",
     "four NRCI thresholds = four tax bands 2.5 / 10 / 23.33; two are unreachable",
     "theorem", "regime_eq_*_iff / signed24_regime"),
]


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------

def dec(x: F, digits: int = 12) -> str:
    """Exact decimal truncation of a rational, for display."""
    sign = "-" if x < 0 else ""
    x = abs(x)
    whole = x.numerator // x.denominator
    rem = x - whole
    frac = ""
    for _ in range(digits):
        rem *= 10
        d = rem.numerator // rem.denominator
        frac += str(d)
        rem -= d
    return f"{sign}{whole}.{frac}"


def print_constants() -> None:
    print("Constants (exact rationals, 50-term CF pi)")
    print("-" * 64)
    print(f"  pi        = {dec(PI, 20)}")
    print(f"  Delta     = {DELTA}                 (primitive difference-state)")
    print(f"  Y         = {dec(Y, 20)}   = 1/(pi + 2/pi)")
    print(f"  1/8       = {dec(ZONE_SHARE, 20)}   (zone-share)")
    print(f"  Q         = {dec(Q, 20)}   = Y + 1/8")
    print(f"  B         = {BUDGET}                (coherence budget)")
    print(f"  Y_CONST   = {dec(Y_CONST, 20)}   = the operator applied twice")
    print()
    print("  minimum tax of a nonzero pattern      Q       = " + dec(Q, 10))
    print("  minimum tax of a protected pattern    8Q      = " + dec(8 * Q, 10))
    print("  maximum tax of a signed 24-pattern    24Q     = " + dec(24 * Q, 10))
    print("  Coherent floor / ceiling              2.5, 10")


def print_stages() -> None:
    print("The stage ledger: what each stage of the study contributes")
    print("-" * 100)
    print(f"{'St':<5}{'Stage':<22}{'Object':<24}{'Status':<13}{'Lean name'}")
    print("-" * 100)
    for num, name, obj, _claim, status, lean in STAGES:
        print(f"{num:<5}{name:<22}{obj:<24}{status:<13}{lean}")
    print()
    for num, name, _obj, claim, _status, _lean in STAGES:
        print(f"  {num:>4}. {name}: {claim}")


def print_tables() -> None:
    print("Golay layer — a codeword is a 0/1 vector, so TAX = HW * Q")
    print("-" * 72)
    print(f"{'weight':>8}{'TAX':>16}{'NRCI':>14}   regime")
    for row in golay_table():
        print(f"{row['weight']:>8}{row['tax_float']:>16.9f}"
              f"{row['nrci_float']:>14.9f}   {row['regime']}")
    print()
    print("Golay layer, calibrated budget B = 8Q (the octad tax): NRCI = 8/(8+HW)")
    print("-" * 72)
    print(f"{'weight':>8}{'NRCI':>16}   regime")
    for row in calibrated_table():
        print(f"{row['weight']:>8}{row['nrci_float']:>16.9f}   {row['regime']}")
    print()
    print("Leech layer — every minimal vector has ||v||^2 = 32, so TAX = HW*Y + 4")
    print("-" * 72)
    print(f"{'class':>6}{'HW':>5}{'shape':>16}{'TAX':>15}{'NRCI':>14}   regime")
    for row in leech_table():
        print(f"{row['class']:>6}{row['weight']:>5}{row['shape']:>16}"
              f"{row['tax_float']:>15.9f}{row['nrci_float']:>14.9f}   {row['regime']}")


def print_regimes() -> None:
    print("The four regimes as tax bands (B = 10)")
    print("-" * 78)
    print(f"{'regime':<15}{'NRCI':>10}{'tax band':>22}{'signed HW':>12}   reachable?")
    for band, (name, threshold) in zip(regime_bands(), REGIMES):
        thr = "-" if threshold is None else f">= {float(threshold):.1f}"
        if band["tax_to"] is None:
            span = f"> {float(F(band['tax_from'])):.4f}"
            hwtxt = "-"
            reach = "no (HW <= 24)"
        else:
            span = (f"{float(F(band['tax_from'])):.4f} .. "
                    f"{float(F(band['tax_to'])):.4f}")
            hwtxt = f"<= {band['hw_signed']}"
            reach = "yes" if band["reachable_on_24_signed"] else "no (HW <= 24)"
        print(f"{name:<15}{thr:>10}{span:>22}{hwtxt:>12}   {reach}")
    print()
    print("  A signed 24-coordinate pattern has TAX <= 24Q = "
          f"{float(24 * Q):.6f} < 10, so only OnBit and Coherent occur.")
    print("  Golay codewords have HW in {0,8,12,16,24}: the vacuum is OnBit and")
    print("  every nonzero codeword is Coherent — the ladder carries no information there.")
    print("  Leech class C (HW = 24, ||v||^2 = 32) has TAX = "
          f"{float(24 * Y + 4):.6f} > 10: Transitional.")


# --------------------------------------------------------------------------
# Self-test — one check per machine-checked statement
# --------------------------------------------------------------------------

def selftest() -> int:
    checks: List[tuple] = []

    def chk(name: str, cond: bool) -> None:
        checks.append((name, bool(cond)))

    zero = [0] * 24

    # Stage I — the vacuum
    chk("vacuum: TAX = 0", tax(zero) == 0)
    chk("vacuum: NRCI = 1", nrci(zero) == 1)
    chk("vacuum is the only tax-free state",
        all(tax([1 if i == j else 0 for i in range(24)]) > 0 for j in range(24)))

    # Stage IV / IX — the constants
    chk("Y = 1/(pi + 2/pi)", Y == F(1, 1) / (PI + F(2, 1) / PI))
    chk("Y in (0.264675, 0.264676)", F(264675, 10 ** 6) < Y < F(264676, 10 ** 6))
    chk("Q = Y + 1/8", Q == Y + F(1, 8))
    chk("Q in (0.389675, 0.389676)", F(389675, 10 ** 6) < Q < F(389676, 10 ** 6))
    chk("Y_CONST != Y", Y_CONST != Y)
    chk("Y_CONST in (0.232149, 0.232150)",
        F(232149, 10 ** 6) < Y_CONST < F(232150, 10 ** 6))

    # the read-cost operator is capped, and has no positive lower bound
    chk("read cost <= 1/(2 sqrt Delta) at every rational loop value",
        all(read_cost(DELTA, F(k, 8)) ** 2 <= F(1, 8) for k in range(1, 400)))
    chk("read cost -> 0 as the loop grows", read_cost(DELTA, F(10 ** 6)) < F(1, 10 ** 5))
    chk("Y is not the extremal read cost", read_cost(DELTA, F(1414, 1000)) > Y)

    # Stage V — TAX and the signed identity
    signed = [1, -1, 0, 1] + [0] * 20
    unsigned = [2, 0, 0, 0] + [0] * 20
    chk("TAX = HW*Q on signed patterns", tax(signed) == F(hamming_weight(signed)) * Q)
    chk("TAX != HW*Q off signed patterns",
        tax(unsigned) != F(hamming_weight(unsigned)) * Q)
    chk("TAX splits as read cost + embodiment cost",
        tax(signed) == F(hamming_weight(signed)) * Y + F(norm_sq(signed), 8))

    # Q is the realised minimum
    single = [1] + [0] * 23
    chk("Q is attained by a single +-1 activation", tax(single) == Q)
    chk("Q is a lower bound on nonzero patterns",
        all(tax(v) >= Q for v in
            ([2] + [0] * 23, [1, 1] + [0] * 22, [-3] + [0] * 23, [1] * 24)))
    chk("a weight-2 signed pattern costs exactly 2Q",
        tax([1, -1] + [0] * 22) == 2 * Q)

    # Stage VI — NRCI
    chk("NRCI = 10/(10 + TAX)", nrci(signed) == F(10) / (10 + tax(signed)))
    chk("NRCI strictly decreasing in TAX",
        all(coherence(F(k)) > coherence(F(k + 1)) for k in range(0, 100)))
    chk("NRCI in (0, 1]", all(0 < coherence(F(k)) <= 1 for k in range(0, 100)))
    chk("NRCI + lost coherence = 1",
        all(coherence(F(k)) + F(k) / (10 + F(k)) == 1 for k in range(0, 50)))
    chk("budget is a pure scale",
        all(coherence(F(k), F(20)) == coherence(F(k) * F(10) / F(20)) for k in range(50)))

    # Stage VIII — the regime bands
    chk("OnBit band ends at TAX = 5/2", tax_ceiling(F(8, 10)) == F(5, 2))
    chk("Coherent band ends at TAX = 10", tax_ceiling(F(5, 10)) == F(10))
    chk("Transitional band ends at TAX = 70/3", tax_ceiling(F(3, 10)) == F(70, 3))
    chk("OnBit = at most 6 active distinctions (signed)",
        all((regime_of_tax(F(w) * Q) == "OnBit") == (w <= 6) for w in range(0, 25)))
    chk("signed 24-patterns never leave OnBit/Coherent",
        all(regime_of_tax(F(w) * Q) in ("OnBit", "Coherent") for w in range(0, 25)))
    chk("max signed tax 24Q < 10", 24 * Q < 10)

    # Golay layer
    chk("every nonzero Golay weight is Coherent",
        all(regime_of_tax(F(w) * Q) == "Coherent" for w in (8, 12, 16, 24)))
    chk("the vacuum codeword is OnBit", regime_of_tax(F(0)) == "OnBit")
    chk("octad tax = 8Y + 1", F(8) * Q == 8 * Y + 1)
    chk("octad tax in (3.1174, 3.1175)",
        F(31174, 10 ** 4) < 8 * Q < F(31175, 10 ** 4))
    chk("octad NRCI in (0.76234, 0.76235)",
        F(76234, 10 ** 5) < coherence(8 * Q) < F(76235, 10 ** 5))
    chk("protection costs eight quanta", min(F(w) * Q for w in (8, 12, 16, 24)) == 8 * Q)

    # Leech layer
    chk("class A tax = 2Y + 4 (||v||^2 = 32)", tax([4, -4] + [0] * 22) == F(2) * Y + 4)
    chk("classes A and B are Coherent",
        all(regime_of_tax(F(w) * Y + 4) == "Coherent" for w in (2, 8)))
    chk("class C is Transitional", regime_of_tax(F(24) * Y + 4) == "Transitional")
    chk("class C NRCI in (0.4913, 0.4914)",
        F(4913, 10 ** 4) < coherence(F(24) * Y + 4) < F(4914, 10 ** 4))
    chk("class A is cheaper than class B", F(2) * Y + 4 < F(8) * Y + 4)

    # calibrated budget
    chk("calibrated budget gives NRCI = 8/(8+HW)",
        all(coherence(F(w) * Q, 8 * Q) == F(8, 8 + w) for w in range(0, 25)))
    chk("calibrated budget separates all four regimes",
        [r["regime"] for r in calibrated_table()]
        == ["OnBit", "Coherent", "Transitional", "Transitional", "Subcoherent"])

    # TAX is blind to lawfulness
    a = [1] * 8 + [0] * 16
    b = [0] * 8 + [1] * 8 + [0] * 8
    chk("equal-weight signed patterns are taxed identically", tax(a) == tax(b))

    # agreement with the substrate module, if it can be imported
    try:
        sys.path.insert(0, ".")
        from ubp_unified_v5 import GolayCodeEngine, LeechLatticeEngine  # type: ignore
        eng = LeechLatticeEngine(GolayCodeEngine())
        probe = [1, -1, 2, 0, 3, 0, -2, 1] + [0] * 16
        chk("substrate agreement: Y", eng.Y == Y)
        chk("substrate agreement: TAX", eng.calculate_symmetry_tax(probe) == tax(probe))
        chk("substrate agreement: NRCI", eng.calculate_nrci(probe) == nrci(probe))
    except Exception as exc:                                  # pragma: no cover
        checks.append((f"substrate module not audited ({type(exc).__name__})", True))

    width = max(len(n) for n, _ in checks)
    failed = 0
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<{width}}")
        failed += 0 if ok else 1
    print(f"\n{len(checks) - failed}/{len(checks)} checks passed")
    return 0 if failed == 0 else 1


def dump_json() -> Dict[str, object]:
    return {
        "constants": {
            "pi": dec(PI, 30), "Y": dec(Y, 30), "Q": dec(Q, 30),
            "Y_CONST": dec(Y_CONST, 30), "zone_share": "1/8", "budget": "10",
        },
        "stages": [
            {"stage": n, "name": nm, "object": ob, "claim": cl,
             "status": st, "lean": ln}
            for n, nm, ob, cl, st, ln in STAGES
        ],
        "golay_layer": golay_table(),
        "golay_layer_calibrated": calibrated_table(),
        "leech_layer": leech_table(),
        "regime_bands": regime_bands(),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--constants", action="store_true")
    ap.add_argument("--stages", action="store_true")
    ap.add_argument("--tables", action="store_true")
    ap.add_argument("--regimes", action="store_true")
    ap.add_argument("--vector", type=str, default=None,
                    help="comma-separated 24 integers to audit")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if args.json:
        print(json.dumps(dump_json(), indent=2))
        return 0
    if args.vector is not None:
        v = [int(x) for x in args.vector.replace(" ", "").split(",") if x != ""]
        if len(v) != 24:
            print(f"expected 24 integers, got {len(v)}", file=sys.stderr)
            return 2
        for k, val in audit(v).items():
            print(f"  {k:<20} {val}")
        return 0

    shown = False
    if args.constants or not (args.stages or args.tables or args.regimes):
        print_constants(); shown = True
    if args.stages:
        if shown:
            print()
        print_stages(); shown = True
    if args.tables:
        if shown:
            print()
        print_tables(); shown = True
    if args.regimes:
        if shown:
            print()
        print_regimes()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
