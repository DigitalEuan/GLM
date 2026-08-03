import time
from fractions import Fraction
import lee_golay_core as core

# Import from ubp_unified_v5 (1).py if available, or fall back to core
try:
    import ubp_unified_v5 as master
    leech = master.LEECH_ENGINE
    golay = master.GOLAY_ENGINE
except Exception as e:
    print(f"Loading master fallback: {e}")

print("=" * 110)
print("SINGLE-BIT PERTURBATION IMPACT ON MINIMAL VECTOR CLASSES")
print("=" * 110)

# Enumerate Class A, B, C directly from core
class_A = core._enumerate_class_A() # 1,104
class_B = core._enumerate_class_B() # 97,152
class_C = core._enumerate_class_C() # 98,304

categories = [
    "M_Mass", "M_Charge", "M_Space", "M_Time", "M_Thermal", "M_Count",
    "I_Topology", "I_Symmetry", "I_Density", "I_Connectivity", "I_Dimension", "I_Complexity",
    "A_Energy", "A_Force", "A_Velocity", "A_Flux", "A_Resonance", "A_Spin",
    "P_Probability", "P_Ratio", "P_Limit", "P_Tax", "P_Coherence", "P_Phase"
]

def test_bit_flip_on_class(vec_tuple, class_name):
    base_v = list(vec_tuple)
    base_tax = leech.calculate_symmetry_tax(base_v)
    base_nrci = leech.calculate_nrci(base_v)
    
    print(f"\n--- {class_name} Base Vector: {base_v[:6]}... ---")
    print(f"  Base Tax: {float(base_tax):.6f} | Base NRCI: {float(base_nrci):.6f}")
    
    # Test flipping Bit 0 (Mass), Bit 6 (Topology), Bit 12 (Energy), Bit 18 (Probability)
    for flip_bit in [0, 6, 12, 18]:
        flipped_v = list(base_v)
        # For non-binary vectors (Class A, B, C have values 0, ±1, ±2, ±3, ±4),
        # toggling means changing coordinate value
        if flipped_v[flip_bit] == 0:
            flipped_v[flip_bit] = 1
        else:
            flipped_v[flip_bit] = 0
            
        f_tax = leech.calculate_symmetry_tax(flipped_v)
        f_nrci = leech.calculate_nrci(flipped_v)
        
        delta_tax = f_tax - base_tax
        delta_nrci = f_nrci - base_nrci
        cat = categories[flip_bit]
        
        print(f"  Toggle Bit {flip_bit:>2} ({cat:<14}): New Tax = {float(f_tax):.6f} (Δ = {float(delta_tax):+.6f}) | New NRCI = {float(f_nrci):.6f} (Δ = {float(delta_nrci):+.6f})")

test_bit_flip_on_class(class_A[0], "CLASS A (Anchor)")
test_bit_flip_on_class(class_B[0], "CLASS B (Octad / Matter)")
test_bit_flip_on_class(class_C[0], "CLASS C (Vacuum Continuum)")