"""Plain-assert self-test of the automata register (run from a GLM checkout with the overlay):
    PYTHONPATH=. python3 rule30_round9/test_automata.py
Each assertion mirrors a Lean theorem of RequestProject/GLM/Rule30 (named in the comment).
"""
import sys
sys.path.insert(0, '.')
from glm_universal.data_objects import automata as ca

# ElementaryCA.lean
assert ca.mirror_number(30) == 86                      # mirrorNum_thirty
assert ca.complement_number(30) == 135                 # complementNum_thirty
assert ca.mirror_number(ca.complement_number(30)) == 149   # mirror_complement_thirty
assert len({ca.class_rep(r) for r in range(256)}) == 88     # card_equivalence_classes
assert sum(ca.is_left_permutive(r) for r in range(256)) == 16   # card_leftPermutive
assert ca.evolve_impulse_column(90, 64) == (1,) + (0,) * 63   # ecaColumn_ninety_centre
assert ca.anf_text(30) == "L + C + R + C*R"                    # rule30_zmod
# Compute.lean / OEIS A051023
assert "".join(map(str, ca.evolve_impulse_column(30, 32))) == "11011100110001011001001110101110"
# WobbleCertificate.lean scan values (D(1000) = -38, D(10000) = 64 from the certificate script)
bits = ca.evolve_impulse_column(30, 10000)
assert ca.wobble(bits, 1000) == -38 and ca.wobble(bits, 10000) == 64
# TopMonomial.lean: deg = 2n-1 for n >= 2
for n in range(2, 8):
    assert ca.anf_of_cone(30, n)["degree"] == 2 * n - 1
# WholeCone.lean: every cell of the cone is essential
for n in range(0, 8):
    assert ca.essential_inputs(30, n) == list(range(-n, n + 1))
# ConeSeparation.lean / ElementaryCA.ecaEvolve_flip_left_edge (all left-permutive wheels)
for r in range(256):
    if ca.is_left_permutive(r):
        assert all(ca.left_edge_derivative_is_one(r, n) for n in range(0, 5))
print("automata register: all checks pass")
