"""
UBP substrate constants — exact rational representation.

All constants are Python Fraction objects to guarantee zero floating-point drift,
matching the UBP Cortex's "Computational Sovereignty" commitment (per README.md §1).

The 50-term continued-fraction approximation of pi is treated as the canonical
UBP-pi per user decision (Phase 1 treats it as exact; precision audit is a
separate concern outside this study's scope).
"""
from fractions import Fraction as F

# ── Exact transcendental constants (UBP canonical forms) ────────────────────
# PI: 50-term continued-fraction approximation (as used in user's script)
PI = F(16590847, 5281024)

# PHI: golden ratio, rational approximation (15 significant digits, as in user's script)
PHI = F(1618033988749895, 1000000000000000)

# E: Euler's number, rational approximation (16 significant digits, as in user's script)
E = F(2718281828459045, 1000000000000000)

# ── Derived UBP substrate objects ────────────────────────────────────────────
# Y_INV = pi + 2/pi  (the "entropic wobble inverse" per README §3)
Y_INV = PI + F(2, 1) / PI

# Y = 1 / Y_INV  (the Observer / Entropic Wobble constant)
Y = F(1, 1) / Y_INV

# MONAD = pi * phi * e  (the product substrate)
MONAD = PI * PHI * E

# WOBBLE = fractional part of MONAD
WOBBLE = MONAD - int(MONAD)

# L = WOBBLE / 13  (the "Leech-length" or scale-L constant)
L = WOBBLE / F(13, 1)

# U_E = 24^3  (the 24-dimensional cubic unit)
U_E = F(24 ** 3, 1)

# SIGMA = 29/24  (the symmetry-tax modulator)
SIGMA = F(29, 24)

# ── Physical constants (SI 2019 exact where applicable) ─────────────────────
C_SI = F(299792458, 1)              # speed of light in vacuum, m/s (exact)
C_TARGET = float(C_SI)              # for comparison only

# ── The user's current "derived c" formula ───────────────────────────────────
# c_derived = 13 * U_E * MONAD^2 * Y^-3 * L * SIGMA^5
C_DERIVED_UBP = F(13, 1) * U_E * (MONAD ** 2) * (Y ** -3) * L * (SIGMA ** 5)

# ── Display helpers ──────────────────────────────────────────────────────────
def show_constants():
    """Print the exact rational and float forms of all substrate constants."""
    rows = [
        ("PI",      PI,      "50-term continued fraction"),
        ("PHI",     PHI,     "golden ratio (15-digit rational)"),
        ("E",       E,       "Euler's number (16-digit rational)"),
        ("Y_INV",   Y_INV,   "= pi + 2/pi"),
        ("Y",       Y,       "= 1 / Y_INV  (Observer / Entropic Wobble)"),
        ("MONAD",   MONAD,   "= pi * phi * e"),
        ("WOBBLE",  WOBBLE,  "= MONAD - floor(MONAD)  (fractional part)"),
        ("L",       L,       "= WOBBLE / 13"),
        ("U_E",     U_E,     "= 24^3 = 13824"),
        ("SIGMA",   SIGMA,   "= 29 / 24"),
    ]
    print(f"{'Name':<10} {'Float':>25}  {'Exact (Fraction)':<60} Origin")
    print("-" * 130)
    for name, val, origin in rows:
        print(f"{name:<10} {float(val):>25.18f}  {str(val):<60} {origin}")
    print()
    print(f"C_DERIVED_UBP  = 13 * U_E * MONAD^2 * Y^-3 * L * SIGMA^5")
    print(f"               = {float(C_DERIVED_UBP):,.6f} m/s")
    print(f"C_SI (target)  = {float(C_SI):,.6f} m/s")
    err = abs(float(C_DERIVED_UBP) - float(C_SI)) / float(C_SI)
    print(f"Relative error = {err:.10e}  ({err*100:.7f}%)")
    print(f"Absolute error = {float(C_DERIVED_UBP) - float(C_SI):+.4f} m/s")

if __name__ == "__main__":
    show_constants()
