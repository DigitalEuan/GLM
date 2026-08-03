import micropip
await micropip.install("sympy")

import sympy as sp

# Test that it works
x = sp.Symbol('x')
expression = sp.sin(x)**2 + sp.cos(x)**2
simplified = sp.simplify(expression)

print(f"Original: {expression}")
print(f"Simplified: {simplified}")