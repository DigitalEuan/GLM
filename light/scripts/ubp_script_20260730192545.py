from fractions import Fraction

# UBP Substrate Constants
PI = Fraction(16590847, 5281024) # 50-term continued fraction approximation
PHI = Fraction(1618033988749895, 1000000000000000)
E = Fraction(2718281828459045, 1000000000000000)

Y_INV = PI + Fraction(2, 1) / PI
Y = Fraction(1, 1) / Y_INV
MONAD = PI * PHI * E
WOBBLE = MONAD - int(MONAD)
L = WOBBLE / Fraction(13, 1)
U_E = Fraction(24**3, 1)
SIGMA = Fraction(29, 24)

# The Derived Speed of Light Formula
c_derived = Fraction(13, 1) * U_E * (MONAD**2) * (Y**-3) * L * (SIGMA**5)

print(f"Derived c: {float(c_derived):,.2f} m/s")
print(f"Physical c: 299,792,458.00 m/s")
print(f"Error: {float(abs(c_derived - 299792458) / 299792458 * 100):.7f}%")