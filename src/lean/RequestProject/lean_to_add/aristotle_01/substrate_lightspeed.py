#!/usr/bin/env python3
"""
substrate_lightspeed.py — exact audit of the UBP "substrate speed of light".

Everything here is exact rational arithmetic (`fractions.Fraction`).  Since the
2019 SI redefinition, c, h, N_A and Delta-nu(Cs) are exact rationals, so the whole
calibration chain of `substrate_speed_of_light.md` is exact and no measurement
uncertainty enters it.

The chain
---------
    kappa                     empirical anchor, J/mol per unit of geometric work
    E1     = kappa / N_A      J per work unit
    tau    = h / E1           s per tick                     (Planck-Einstein)
    nu     = (24 + T)         ticks per cell (24 bits + T TAX)
    T_cell = nu * tau         s per cell crossing
    l_cell = c * T_cell       m per cell

Two identities make the content of the chain plain:

    tau    = h * N_A / kappa
    l_cell = (24 + T) * lambda1        with lambda1 = c * tau = h*c*N_A/kappa

i.e. the "cell length" is (24+T) wavelengths of the photon whose energy is one
unit of geometric work.  And

    l_cell / T_cell = c                for every kappa and every T,

so c is an input that the chain returns unchanged, not an output.

Usage
-----
    python3 substrate_lightspeed.py --selftest       # verify every claim
    python3 substrate_lightspeed.py --report         # full audit table
    python3 substrate_lightspeed.py --chain 190      # run the chain for kappa kJ/mol
    python3 substrate_lightspeed.py --index          # refractive-index inverse table
    python3 substrate_lightspeed.py --constants      # substrate constants + P1..P8
    python3 substrate_lightspeed.py --json out.json  # machine-readable dump
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from fractions import Fraction as F

# ───────────────────────────────────────────────────────────────────────────────
#  SI 2019 — all exact rationals by definition
# ───────────────────────────────────────────────────────────────────────────────

C_SI = F(299_792_458)                       # m/s
H_SI = F(662_607_015, 10 ** 42)             # J.s
N_A = F(602_214_076 * 10 ** 15)             # 1/mol
DNU_CS = F(9_192_631_770)                   # Hz
K_B = F(1_380_649, 10 ** 29)                # J/K
E_CHARGE = F(1_602_176_634, 10 ** 28)       # C

MOLAR_PLANCK = H_SI * N_A                   # J.s/mol, exact

# Substrate structure
BITS_PER_CELL = 24
TAX_VACUUM = 3                              # the note's "3 TAX overhead"

# The note's empirical anchor
KAPPA_BR = F(190_000)                       # J/mol per unit of geometric work


# ───────────────────────────────────────────────────────────────────────────────
#  The calibration chain
# ───────────────────────────────────────────────────────────────────────────────

def work_energy(kappa: F) -> F:
    """Energy of one unit of geometric work, J."""
    return kappa / N_A


def tick(kappa: F) -> F:
    """Tick duration, s.  Equals h*N_A/kappa."""
    return H_SI / work_energy(kappa)


def work_wavelength(kappa: F) -> F:
    """Wavelength of a photon carrying one work unit, m."""
    return C_SI * tick(kappa)


def ticks_per_cell(tax: F) -> F:
    return F(BITS_PER_CELL) + F(tax)


def cell_duration(kappa: F, tax: F = F(TAX_VACUUM)) -> F:
    return ticks_per_cell(tax) * tick(kappa)


def cell_length(kappa: F, tax: F = F(TAX_VACUUM)) -> F:
    """Cell length, m.  This is where c enters the chain."""
    return C_SI * cell_duration(kappa, tax)


def signal_speed(tax: F, tax_ref: F = F(TAX_VACUUM)) -> F:
    """Propagation speed in a region of TAX `tax`, m/s.  Independent of kappa."""
    return C_SI * ticks_per_cell(tax_ref) / ticks_per_cell(tax)


def refractive_index(tax: F, tax_ref: F = F(TAX_VACUUM)) -> F:
    """n(T) = (24+T)/(24+T_ref).  Dimensionless, anchor-free, falsifiable."""
    return ticks_per_cell(tax) / ticks_per_cell(tax_ref)


def tax_from_index(n: float, tax_ref: F = F(TAX_VACUUM)) -> float:
    """Inverse of `refractive_index`: the TAX a medium of index n must carry."""
    return float(ticks_per_cell(tax_ref)) * n - BITS_PER_CELL


# ───────────────────────────────────────────────────────────────────────────────
#  Substrate constants (mirrors ubp_unified_v5.UBPUltimateSubstrate)
# ───────────────────────────────────────────────────────────────────────────────

def _cf(coeffs):
    x = F(coeffs[-1])
    for c in reversed(coeffs[:-1]):
        x = F(c) + F(1) / x
    return x


_PI_CF = [3, 7, 15, 1, 292, 1, 1, 1, 2, 1, 3, 1, 14, 2, 1, 1, 2, 2, 2, 2, 1, 84,
          2, 1, 1, 15, 3, 13, 1, 4, 2, 6, 6, 99, 1, 2, 2, 6, 3, 5, 1, 1, 6, 8, 1,
          7, 1, 2, 3, 7]


def _e_cf(terms=50):
    coeffs, k = [2], 2
    while len(coeffs) < terms:
        coeffs.extend([1, k, 1])
        k += 2
    return coeffs[:terms]


PI = _cf(_PI_CF)
E_CONST = _cf(_e_cf(50))
PHI = _cf([1] * 50)

Y_INV = PI + F(2) / PI
Y = F(1) / Y_INV
MONAD = PI * PHI * E_CONST
WOBBLE = MONAD - int(MONAD)
SINK_L = WOBBLE / 13
SIGMA = F(29, 24)
SINK_LS = SINK_L * SIGMA

# The symmetry tax of a Golay codeword of Hamming weight w is w*Y + w/8
# (norm^2 = w for a 0/1 vector); of a Leech minimal vector it is w*Y + 32/8.
def codeword_tax(w: int) -> F:
    return F(w) * Y + F(w, 8)


def minimal_vector_tax(w: int) -> F:
    return F(w) * Y + F(4)


# ───────────────────────────────────────────────────────────────────────────────
#  Reporting helpers
# ───────────────────────────────────────────────────────────────────────────────

def sci(x, digits=6):
    return f"{float(x):.{digits}e}"


def rel_err(pred, target) -> float:
    return abs(float(pred) - float(target)) / abs(float(target))


BOND_ENERGIES = {          # kJ/mol, common tabulated mean bond enthalpies
    "Br–Br": 193, "C–C": 347, "C=O": 799, "N≡N": 946, "O=O": 498,
    "H–H": 436, "I–I": 151, "Cl–Cl": 243,
}

MATERIALS = {              # refractive index at ~589 nm
    "vacuum": 1.0, "air (STP)": 1.000293, "water": 1.3330, "ethanol": 1.3610,
    "fused silica": 1.4585, "crown glass": 1.5200, "sapphire": 1.7682,
    "diamond": 2.4175, "silicon (1.55 um)": 3.4757,
}


def run_chain(kappa_kj: float, tax: int = TAX_VACUUM, show=True):
    kappa = F(kappa_kj).limit_denominator(10 ** 9) * 1000
    e1 = work_energy(kappa)
    t = tick(kappa)
    lam = work_wavelength(kappa)
    tc = cell_duration(kappa, F(tax))
    lc = cell_length(kappa, F(tax))
    out = {
        "kappa_J_per_mol": float(kappa),
        "E1_J": float(e1),
        "tick_s": float(t),
        "tick_fs": float(t) * 1e15,
        "work_wavelength_m": float(lam),
        "work_wavelength_nm": float(lam) * 1e9,
        "work_frequency_Hz": float(1 / t),
        "wavenumber_cm-1": float(1 / lam) / 100,
        "ticks_per_cell": float(ticks_per_cell(F(tax))),
        "cell_duration_s": float(tc),
        "cell_length_m": float(lc),
        "cell_length_um": float(lc) * 1e6,
        "recovered_c": float(lc / tc),
    }
    if show:
        print(f"\n  kappa                 = {float(kappa)/1000:g} kJ/mol per work unit")
        print(f"  E1 = kappa/N_A        = {sci(e1)} J")
        print(f"  tau = h/E1            = {sci(t)} s   = {float(t)*1e15:.3f} fs")
        print(f"  nu1 = 1/tau           = {sci(1/t)} Hz")
        print(f"  lambda1 = c*tau       = {sci(lam)} m   = {float(lam)*1e9:.1f} nm"
              f"   ({float(1/lam)/100:.0f} cm^-1)")
        print(f"  ticks/cell            = 24 + {tax} = {float(ticks_per_cell(F(tax))):g}")
        print(f"  T_cell                = {sci(tc)} s")
        print(f"  l_cell = c*T_cell     = {sci(lc)} m   = {float(lc)*1e6:.4f} um")
        print(f"  l_cell / T_cell       = {float(lc/tc):.10g} m/s   <-- exactly c, always")
    return out


# ───────────────────────────────────────────────────────────────────────────────
#  Self-test
# ───────────────────────────────────────────────────────────────────────────────

def selftest() -> int:
    fails = []

    def check(name, cond, detail=""):
        (print(f"  [ ok ] {name}") if cond
         else (fails.append(name), print(f"  [FAIL] {name}  {detail}")))

    print("\nA. Exactness of the SI inputs")
    check("h*N_A is exact", MOLAR_PLANCK == F(19951563564467157, 5 * 10 ** 25))
    check("c is an integer", C_SI.denominator == 1)

    print("\nB. The published numbers of substrate_speed_of_light.md")
    e1 = work_energy(KAPPA_BR)
    t = tick(KAPPA_BR)
    tc = cell_duration(KAPPA_BR)
    lc = cell_length(KAPPA_BR)
    check("E1 = 3.16e-19 J (3.1550e-19)", abs(float(e1) - 3.155024e-19) < 1e-24,
          sci(e1))
    check("tau = 2.10 fs (2.100165 fs)", abs(float(t) * 1e15 - 2.100165) < 1e-5,
          f"{float(t)*1e15:.6f} fs")
    check("T_cell = 5.67e-14 s", abs(float(tc) - 5.670444e-14) < 1e-19, sci(tc))
    check("l_cell = 17.0 um (16.9996)", abs(float(lc) * 1e6 - 16.99956) < 1e-4,
          f"{float(lc)*1e6:.5f} um")

    print("\nC. Structural identities")
    check("tau = h*N_A/kappa", tick(KAPPA_BR) == MOLAR_PLANCK / KAPPA_BR)
    check("l_cell = 27 * lambda1",
          cell_length(KAPPA_BR) == 27 * work_wavelength(KAPPA_BR))
    ok = True
    for k in (F(1), F(10 ** 7), KAPPA_BR, F(123456789, 7)):
        for T in (F(0), F(3), F(8), F(24), F(1, 3)):
            if cell_length(k, T) / cell_duration(k, T) != C_SI:
                ok = False
    check("l_cell/T_cell == c for every (kappa, TAX)  [c is an INPUT]", ok)
    check("tau scales as 1/kappa", tick(2 * KAPPA_BR) == tick(KAPPA_BR) / 2)
    check("l_cell scales as 1/kappa",
          cell_length(3 * KAPPA_BR) == cell_length(KAPPA_BR) / 3)

    print("\nD. Dimensional obstruction (Buckingham)")
    # dimensions as (M, L, T) exponent triples
    d_action, d_energy, d_speed = (1, 2, -1), (1, 2, -2), (0, 1, -1)
    reachable = {tuple(a * x + b * y for x, y in zip(d_action, d_energy))
                 for a in range(-12, 13) for b in range(-12, 13)}
    check("no power product of (h, E) has the dimension of a speed",
          d_speed not in reachable)
    check("(h, E) do give a time", (0, 0, 1) in reachable)

    print("\nE. Refractive-index law (anchor-free)")
    check("n(3) = 1", refractive_index(F(3)) == 1)
    check("n(8) = 32/27", refractive_index(F(8)) == F(32, 27))
    check("v(T) <= c  iff  T >= 3",
          all((signal_speed(F(T)) <= C_SI) == (T >= 3) for T in range(0, 40)))
    check("n strictly increasing in TAX",
          all(refractive_index(F(a)) < refractive_index(F(a + 1)) for a in range(0, 40)))
    check("TAX <= 24  =>  n <= 16/9 (diamond, n=2.4175, is excluded)",
          refractive_index(F(24)) == F(16, 9) and 2.4175 > 16 / 9)

    print("\nF. The '3' of '24 bits + 3 TAX'")
    check("octad minimises the tax among nonzero Golay codewords",
          all(codeword_tax(8) < codeword_tax(w) for w in (12, 16, 24)))
    check("Tax(octad) = 8Y+1 = 3.1174, floor = 3",
          math.floor(codeword_tax(8)) == 3 and abs(float(codeword_tax(8)) - 3.117403) < 1e-5)
    check("but class-A minimal vectors are cheaper than octads "
          "(so P5 is false at the Leech layer)",
          minimal_vector_tax(2) < minimal_vector_tax(8))

    print("\nG. Substrate constants")
    check("MONAD = pi*phi*e = 13.81758", abs(float(MONAD) - 13.8175802272) < 1e-9)
    check("MONAD = 13 + WOBBLE", MONAD - WOBBLE == 13)
    check("MONAD/13 = 1 + L  (P6 is a tautology)", MONAD / 13 == 1 + SINK_L)
    vc = math.sqrt(1 - 1 / float(MONAD / 13) ** 2)
    check("v/c = 0.339 (0.338878)", abs(vc - 0.3388777) < 1e-6, f"{vc:.7f}")
    check("Y = 1/(pi+2/pi) = 0.2646754", abs(float(Y) - 0.2646754304) < 1e-9)

    print("\nH. Alignment points P2, P4, P7, P8")
    check("P2  169/WOBBLE, error 0.0294% (quoted 0.03%)",
          abs(rel_err(169 / WOBBLE, F(2067682830, 10 ** 7)) - 0.00029375) < 1e-7)
    check("P7  137+L, error 0.0196% (quoted 0.02%)",
          abs(rel_err(220 - 83 + SINK_L, F(137035999084, 10 ** 9)) - 0.00019624) < 1e-7)
    check("P8  1836+2L_s, error 0.0000374% (quoted 0.001%, i.e. pessimistic)",
          abs(rel_err(1836 + 2 * SINK_LS, F(183615267343, 10 ** 8)) - 3.7434e-7) < 1e-10)
    m_pred = Y ** 2 * WOBBLE * F(24) ** 4 * F(29) ** 4 * H_SI * DNU_CS / C_SI ** 2
    check("P4  Y^2*WOBBLE*24^4*29^4*h*dnu/c^2, error 0.00919% "
          "(quoted 0.007% -- too small)",
          abs(rel_err(m_pred, F(91093837015, 10 ** 41)) - 9.19013e-5) < 1e-9,
          f"{rel_err(m_pred, F(91093837015, 10**41))*100:.6f}%")

    print("\nI. The chemistry anchor")
    check("190 kJ/mol is close to, but not equal to, the tabulated Br-Br value 193",
          abs(190 - BOND_ENERGIES["Br–Br"]) == 3)
    for bond, exp in (("C–C", 1.83), ("C=O", 4.21), ("N≡N", 4.98), ("O=O", 2.62)):
        check(f"{bond}: {BOND_ENERGIES[bond]}/190 = {exp}",
              abs(BOND_ENERGIES[bond] / 190 - exp) < 0.005)

    print("\nJ. The substrate's only dimensionful assertion: PhysicsALU.G_N")
    G_N = F(39, 29) * (Y ** 18 / WOBBLE)
    hbar = H_SI / (2 * F(math.pi).limit_denominator(10 ** 15))
    l_planck = math.sqrt(float(hbar) * float(G_N) / float(C_SI) ** 3)
    check("G_N = (39/29)*Y^18/WOBBLE = 6.6832e-11 (CODATA 6.67430e-11, 0.13%)",
          abs(rel_err(G_N, F(667430, 10 ** 16)) - 0.0013267) < 1e-6,
          f"{float(G_N):.6e}")
    check("the implied Planck length is 1.617e-35 m, i.e. 1.05e30 times smaller "
          "than the 17 um cell -- two incompatible substrate length scales",
          abs(l_planck - 1.61733e-35) < 1e-40
          and abs(float(cell_length(KAPPA_BR)) / l_planck - 1.0511e30) < 1e26,
          f"{l_planck:.5e}")

    print(f"\n{'='*70}\n  {'ALL CHECKS PASSED' if not fails else str(len(fails)) + ' FAILURE(S)'}\n{'='*70}")
    return 1 if fails else 0


# ───────────────────────────────────────────────────────────────────────────────
#  Reports
# ───────────────────────────────────────────────────────────────────────────────

def report():
    print("=" * 74)
    print("  THE SUBSTRATE SPEED OF LIGHT — EXACT AUDIT")
    print("=" * 74)

    print("\n1. THE CHAIN, AT THE PUBLISHED ANCHOR kappa = 190 kJ/mol")
    run_chain(190)

    print("\n2. WHAT THE NOTE CLAIMS vs WHAT THE ARITHMETIC GIVES\n")
    rows = [
        ("Energy per work unit", "3.16e-19 J", sci(work_energy(KAPPA_BR), 3) + " J", "ok"),
        ("Tick duration", "2.10 fs", f"{float(tick(KAPPA_BR))*1e15:.4f} fs", "ok"),
        ("Cell duration", "5.67e-14 s", sci(cell_duration(KAPPA_BR), 3) + " s", "ok"),
        ("Cell length", "17.0 um", f"{float(cell_length(KAPPA_BR))*1e6:.4f} um", "ok"),
        ("'one molecular vibration'", "3.16e-19 J",
         f"{float(1/work_wavelength(KAPPA_BR))/100:.0f} cm^-1 = red light", "WRONG"),
        ("'molecular scale'", "17 um",
         "17 um is 1e5 x a molecular diameter", "WRONG"),
        ("'c is an output'", "-", "l_cell/T_cell == c identically", "WRONG"),
    ]
    print(f"  {'quantity':28s} {'claimed':14s} {'exact':32s} verdict")
    print("  " + "-" * 88)
    for a, b, c, d in rows:
        print(f"  {a:28s} {b:14s} {c:32s} {d}")

    print("\n3. SENSITIVITY OF THE CELL LENGTH TO THE ANCHOR\n")
    print(f"  {'kappa (kJ/mol)':>16s} {'tau (fs)':>12s} {'lambda1 (nm)':>14s} {'l_cell (um)':>14s}")
    for k in (100, 150, 190, 193, 250, 347, 500, 946):
        kk = F(k) * 1000
        print(f"  {k:16d} {float(tick(kk))*1e15:12.4f} "
              f"{float(work_wavelength(kk))*1e9:14.2f} {float(cell_length(kk))*1e6:14.4f}")
    print("\n  tau, lambda1 and l_cell are all exactly proportional to 1/kappa;")
    print("  the substrate contributes only the integer 27 = 24 + 3.")

    print("\n4. THE ANCHOR-FREE PREDICTION: n(T) = (24+T)/27\n")
    index_table()

    print("\n5. THE TAX SPECTRUM ON THE GOLAY LAYER  (Tax = w*(Y + 1/8))\n")
    print(f"  {'weight':>8s} {'Tax':>12s} {'ticks/cell':>12s} {'n':>10s}")
    for w in (0, 8, 12, 16, 24):
        tx = codeword_tax(w)
        print(f"  {w:8d} {float(tx):12.6f} {24+float(tx):12.6f} "
              f"{(24+float(tx))/27:10.6f}")
    print(f"\n  minimum nonzero tax = Tax(octad) = 8Y + 1 = {float(codeword_tax(8)):.6f}")
    print("  floor(3.1174) = 3  ->  this is the '3 TAX overhead' of the note.")
    print("  Using the exact value instead of 3 gives "
          f"{24+float(codeword_tax(8)):.6f} ticks/cell and "
          f"l_cell = {float(work_wavelength(KAPPA_BR))*(24+float(codeword_tax(8)))*1e6:.4f} um "
          "(+0.43%).")

    print("\n6. LEECH MINIMAL VECTORS  (Tax = w*Y + 4) — P5 is false here\n")
    print(f"  {'class':>8s} {'HW':>4s} {'Tax':>12s}")
    for name, w in (("A", 2), ("B (octad)", 8), ("C", 24)):
        print(f"  {name:>8s} {w:4d} {float(minimal_vector_tax(w)):12.6f}")
    print("\n  Class A is cheaper than the octad class B, so 'photon = minimum-Tax")
    print("  octad' holds on the Golay code layer only, not among minimal vectors.")

    constants_report()


def index_table():
    print(f"  {'medium':22s} {'n (measured)':>13s} {'required TAX':>13s} {'admissible?':>12s}")
    print("  " + "-" * 64)
    for name, n in MATERIALS.items():
        T = tax_from_index(n)
        ok = "yes" if 3 <= T <= 24 else ("superluminal" if T < 3 else "TAX > 24")
        print(f"  {name:22s} {n:13.5f} {T:13.4f} {ok:>12s}")
    print("\n  The law is falsifiable and it fails for dense media: with the TAX")
    print("  bounded by 24 the largest attainable index is 48/27 = 1.7778, so")
    print("  diamond and silicon are outside the model's range.")


def constants_report():
    print("\n7. SUBSTRATE CONSTANTS AND THE EIGHT ALIGNMENT POINTS\n")
    print(f"  pi     = {float(PI):.12f}      (50-term CF convergent)")
    print(f"  phi    = {float(PHI):.12f}")
    print(f"  e      = {float(E_CONST):.12f}")
    print(f"  MONAD  = pi*phi*e     = {float(MONAD):.12f}")
    print(f"  WOBBLE = MONAD - 13   = {float(WOBBLE):.12f}")
    print(f"  L      = WOBBLE/13    = {float(SINK_L):.12f}")
    print(f"  Y      = 1/(pi+2/pi)  = {float(Y):.12f}")
    print(f"  sigma  = 29/24,  L_s  = {float(SINK_LS):.12f}")
    print(f"\n  MONAD/13 = 1 + L : {MONAD/13 == 1 + SINK_L}   "
          "<-- P6 is this identity, nothing more")

    m_pred = Y ** 2 * WOBBLE * F(24) ** 4 * F(29) ** 4 * H_SI * DNU_CS / C_SI ** 2
    gamma = MONAD / 13
    vc = math.sqrt(1 - 1 / float(gamma) ** 2)
    rows = [
        ("P6 v/c", "sqrt(1-(13/MONAD)^2)", vc, 0.339, "0.339", "quoted value ok"),
        ("P2 m_mu/m_e", "169/WOBBLE", float(169 / WOBBLE), 206.7682830, "0.03%", ""),
        ("P7 1/alpha", "220-83+L", float(220 - 83 + SINK_L), 137.035999084, "0.02%", ""),
        ("P8 m_p/m_e", "1836+2*L_s", float(1836 + 2 * SINK_LS), 1836.15267343,
         "0.001%", "actually 0.0000374%"),
        ("P4 m_e /kg", "Y^2*W*24^4*29^4*h*dnu/c^2", float(m_pred), 9.1093837015e-31,
         "0.007%", "actually 0.00919%"),
    ]
    print(f"\n  {'point':12s} {'formula':28s} {'value':>16s} {'target':>16s} "
          f"{'err':>10s}  {'quoted':>8s}")
    print("  " + "-" * 100)
    for name, formula, val, tgt, quoted, note in rows:
        e = abs(val - tgt) / abs(tgt) * 100
        print(f"  {name:12s} {formula:28s} {val:16.9g} {tgt:16.9g} {e:9.5f}% "
              f"{quoted:>8s}  {note}")
    print("\n  Every one of these has the shape")
    print("      measured quantity  ~  (dimensionless substrate number) x (SI unit),")
    print("  with the SI unit = 1 for the ratios and = h*dnu_Cs/c^2 for the mass.")
    print("  That is legitimate; deriving c the same way is not, because no power")
    print("  product of an action and an energy has the dimension of a speed.")


def dump_json(path):
    data = {
        "si": {"c": str(C_SI), "h": str(H_SI), "N_A": str(N_A),
               "dnu_Cs": str(DNU_CS), "h_N_A": str(MOLAR_PLANCK)},
        "chain_190kJ": run_chain(190, show=False),
        "identities": {
            "tick_eq_hNA_over_kappa": tick(KAPPA_BR) == MOLAR_PLANCK / KAPPA_BR,
            "cell_is_27_wavelengths":
                cell_length(KAPPA_BR) == 27 * work_wavelength(KAPPA_BR),
            "c_recovered_identically":
                all(cell_length(F(k), F(T)) / cell_duration(F(k), F(T)) == C_SI
                    for k in (1, 190000, 7) for T in (0, 3, 8, 24)),
        },
        "refractive_index": {m: {"n": n, "required_tax": tax_from_index(n)}
                             for m, n in MATERIALS.items()},
        "golay_tax": {str(w): float(codeword_tax(w)) for w in (0, 8, 12, 16, 24)},
        "leech_minimal_tax": {str(w): float(minimal_vector_tax(w)) for w in (2, 8, 24)},
        "substrate_constants": {
            "PI": str(PI), "PHI": str(PHI), "E": str(E_CONST), "Y": str(Y),
            "MONAD": str(MONAD), "WOBBLE": str(WOBBLE), "SINK_L": str(SINK_L),
            "monad_over_13_eq_1_plus_L": MONAD / 13 == 1 + SINK_L,
        },
        "alignment_errors_percent": {
            "P2_muon_ratio": rel_err(169 / WOBBLE, F(2067682830, 10 ** 7)) * 100,
            "P7_alpha_inv": rel_err(220 - 83 + SINK_L, F(137035999084, 10 ** 9)) * 100,
            "P8_proton_ratio": rel_err(1836 + 2 * SINK_LS, F(183615267343, 10 ** 8)) * 100,
            "P4_electron_mass": rel_err(
                Y ** 2 * WOBBLE * F(24) ** 4 * F(29) ** 4 * H_SI * DNU_CS / C_SI ** 2,
                F(91093837015, 10 ** 41)) * 100,
        },
    }
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)
    print(f"wrote {path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--chain", type=float, metavar="KJ_PER_MOL")
    ap.add_argument("--tax", type=int, default=TAX_VACUUM)
    ap.add_argument("--index", action="store_true")
    ap.add_argument("--constants", action="store_true")
    ap.add_argument("--json", metavar="PATH")
    a = ap.parse_args()

    if a.selftest:
        sys.exit(selftest())
    if a.chain is not None:
        run_chain(a.chain, a.tax)
        return
    if a.index:
        index_table()
        return
    if a.constants:
        constants_report()
        return
    if a.json:
        dump_json(a.json)
        return
    report()


if __name__ == "__main__":
    main()
