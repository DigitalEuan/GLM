#!/usr/bin/env python3
"""Round 43 -- executable checks of GLM_Escalation_Boundaries_Exploration.md.

Standard library only, exact arithmetic only.  Each check prints PASS/FAIL and the numbers it
used.  The Lean theorem that proves the same statement (for all cases, not only the ones run
here) is named next to each check; see rule30_round43/README.md.

    python3 escalation_checks.py          # about 5 s
    python3 escalation_checks.py --quick  # skips the full Golay census
"""
from fractions import Fraction
from itertools import product
from math import floor, gcd
import sys

RESULTS = []


def check(name, ok, detail, lean):
    RESULTS.append((name, ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}\n       {detail}\n       Lean: {lean}")


# ---------------------------------------------------------------------------------------------
# 1. The five moduli: refinement is divisibility (sketch section 3.2)
# ---------------------------------------------------------------------------------------------
def refines(mp, m, span=4000):
    """mod mp refines mod m on [-span, span]: equal mod mp => equal mod m."""
    return all((a - b) % m == 0 for a in range(-span, span, 7) for b in (a + mp, a - mp))


moduli = [2, 4, 8, 144, 256]
table = {(m, mp): refines(mp, m) for m in moduli for mp in moduli}
check("mod m' refines mod m exactly when m | m'",
      all(table[(m, mp)] == (mp % m == 0) for m in moduli for mp in moduli),
      "sampled on integers; " + ", ".join(f"{mp}>{m}:{table[(m, mp)]}"
                                         for m, mp in [(8, 144), (144, 256), (8, 256)]),
      "GLM.Escalation.residue_refines_iff")
check("8 divides 144 (the sketch says it does not)", 144 % 8 == 0, "144 = 8 * 18",
      "GLM.Escalation.eight_dvd_144, residue_144_refines_8")
check("mod 256 does NOT refine mod 144", not table[(144, 256)],
      "0 and 256 agree mod 256 and differ mod 144", "GLM.Escalation.residue_256_not_refines_144")
check("carrying mod 144 and mod 256 together = mod lcm = mod 2304",
      144 * 256 // gcd(144, 256) == 2304 and all(
          ((a % 144, a % 256) == (b % 144, b % 256)) == ((a - b) % 2304 == 0)
          for a in range(0, 5000, 13) for b in range(0, 5000, 17)),
      "lcm(144, 256) = 2304", "GLM.Escalation.residue_pair_indist_iff")

# ---------------------------------------------------------------------------------------------
# 2. The half-unit example (sketch sections 4.1 and 4.3)
# ---------------------------------------------------------------------------------------------
half = Fraction(1, 2)
fails = []
for m in moduli:
    # floor-residue filter q -> floor(q) mod m ; 1/2 ~ 0, but 1/2+1/2 = 1 is not ~ 0+0 = 0
    same_in = floor(half) % m == floor(Fraction(0)) % m
    same_out = floor(half + half) % m == floor(Fraction(0)) % m
    fails.append(same_in and not same_out)
check("no floor-residue filter (mod 2, 4, 8, 144, 256) resolves 1/2 + 1/2", all(fails),
      "each filter sees 1/2 ~ 0 but 1 !~ 0; graded escalation never stops on this stack",
      "GLM.Escalation.floorResidue_add_not_congruent, graded_escalation_claim_false")
p4 = lambda q: floor(4 * q) % 4
check("the sketch's mod-4 computation is wrong",
      (p4(half) + p4(half)) % 4 == p4(half + half),
      f"perceive4(1/2) = {p4(half)}, perceive4(1) = {p4(half + half)}, 2 + 2 = 0 mod 4",
      "GLM.Escalation.scaled_four_half_consistent")

# ---------------------------------------------------------------------------------------------
# 3. Master step: TCT roll-back deadlocks (sketch sections 2.1 and 6)
# ---------------------------------------------------------------------------------------------
def step(state, modulate, snap, gate, tct):
    c, k = state
    ch = modulate(c)
    cb, k2 = snap(ch, k)
    return (gate(cb), k2) if tct(c, ch, cb) else state


st = (Fraction(1, 3), 0)
run = [st]
for _ in range(10):
    run.append(step(run[-1], lambda c: c + Fraction(1, 7), lambda c, k: (c, k + 1),
                    lambda c: c, lambda a, b, c: False))
check("a rejected state never moves again (fixed modulation target)", len(set(run)) == 1,
      f"10 ticks, states seen: {len(set(run))}", "GLM.Escalation.Machine.iterate_of_reject")

# ---------------------------------------------------------------------------------------------
# 4. The GLM's own Golay substrate: where complete decoding is ambiguous (sketch section 5)
# ---------------------------------------------------------------------------------------------
ROWS = [16769025, 4681730, 10727428, 13750280, 6877200, 11825184,
        14299200, 15536256, 7770368, 3887616, 1946624, 9361408]   # G = [I12 | B], the GLM's rows


def word(m):
    w = 0
    for j in range(12):
        if m >> j & 1:
            w ^= ROWS[j]
    return w


CODE = [word(m) for m in range(4096)]
check("codeword weights 0, 8, 12, 16, 24 with counts 1, 759, 2576, 759, 1",
      sorted({bin(c).count("1") for c in CODE}) == [0, 8, 12, 16, 24]
      and [sum(1 for c in CODE if bin(c).count("1") == w) for w in (8, 12, 16)] == [759, 2576, 759],
      "the extended binary Golay code", "GLM.Rule30.golay_weight_census")

if "--quick" not in sys.argv:
    census = [0] * 6
    dichotomy = True
    for s in range(4096):
        x = s << 12                         # coset representative with zero message bits
        prof = [0] * 25
        for c in CODE:
            prof[bin(x ^ c).count("1")] += 1
        near = sum(prof[:4])
        dichotomy &= (near == 1) or (near == 0 and prof[4] == 6)
        census[min(i for i in range(25) if prof[i])] += 1
    check("every word: one codeword within 3, or none within 3 and exactly six at 4",
          dichotomy, "checked on all 4096 coset representatives (the reduction is proved in Lean)",
          "GLM.Escalation.Golay.golay_decoding_dichotomy")
    check("coset census 1, 24, 276, 2024, 1771 at distance 0..4", census[:6] == [1, 24, 276, 2024, 1771, 0],
          f"census = {census}", "GLM.Escalation.Golay.golay_coset_census")

# ---------------------------------------------------------------------------------------------
# 5. Leech syndromes "mod m" (sketch section 5.3) -- script check, not in Lean
# ---------------------------------------------------------------------------------------------
CODESET = set(CODE)


def leech_even_member(x):
    """Even-type membership in sqrt(8) * Leech, standard coordinates (all coordinates even)."""
    if any(v % 2 for v in x):
        return False
    mask = sum(1 << i for i, v in enumerate(x) if (v // 2) % 2)
    return mask in CODESET and sum(x) % 8 == 0


e = [[8 if j == i else 0 for j in range(24)] for i in range(24)]
check("8 Z^24 lies inside sqrt(8) Leech (so 'syndromes mod 8, 144, 256' carry no extra data)",
      all(leech_even_member(v) for v in e),
      "each 8 e_i is a Leech vector of norm 8; hence Lambda + mZ^24 = Lambda for every m divisible "
      "by 8 (8, 144 = 8*18, 256), and R^24/(Lambda + mZ^24) is a torus, not a finite group",
      "(script check only)")

# ---------------------------------------------------------------------------------------------
# 6. Niemeier list in the sketch (sections 5.1, 5.6)
# ---------------------------------------------------------------------------------------------
SKETCH = ["A1^24", "A2^12", "A3^8", "A4^6", "A5^4D4", "A6^4", "A7^2D5^2", "A8^3", "A9^2D6",
          "A11D7E6", "A12^2", "A15D9", "A17E7", "A24", "D4^6", "D6^4", "D8^3", "D10E7^2", "D12^2",
          "D16E8", "D24", "E8^3"]
H = {"A": lambda n: n + 1, "D": lambda n: 2 * n - 2, "E": lambda n: {6: 12, 7: 18, 8: 30}[n]}


def components(name):
    import re
    out = []
    for letter, rank, power in re.findall(r"([ADE])(\d+)(?:\^(\d+))?", name):
        out += [(letter, int(rank))] * int(power or 1)
    return out


def niemeier_ok(name):
    comps = components(name)
    hs = {H[l](r) for l, r in comps}
    return sum(r for _, r in comps) == 24 and len(hs) == 1


check("the sketch's list is 22 systems, all valid; the 23rd, E6^4, is missing",
      len(SKETCH) == 22 and all(niemeier_ok(n) for n in SKETCH) and niemeier_ok("E6^4")
      and "E6^4" not in SKETCH,
      "rank 24 and one common Coxeter number per system; E6^4 (h = 12) passes and is absent",
      "(script check only)")

# ---------------------------------------------------------------------------------------------
# 7. Rule 30 at the parity layer
# ---------------------------------------------------------------------------------------------
def r30(row):
    r = [0, 0] + row + [0, 0]
    return [r[i - 1] ^ (r[i] | r[i + 1]) for i in range(1, len(r) - 1)]


par = lambda r: sum(r) % 2
pairs = lambda r: sum(r[i] & r[i + 1] for i in range(len(r) - 1)) % 2
law = all(par(r30(list(r))) == (par(r) + pairs(r)) % 2
          for n in range(1, 13) for r in product([0, 1], repeat=n))
check("Rule 30 parity law: parity(next) = parity + (number of 11 pairs) mod 2", law,
      "all rows of length 1..12", "GLM.Escalation.Rule30Parity.rowParity_step")
check("one step does not descend to parity: rows 11 and 101",
      par([1, 1]) == par([1, 0, 1]) and par(r30([1, 1])) != par(r30([1, 0, 1])),
      f"next rows {r30([1, 1])} and {r30([1, 0, 1])}", "Rule30Parity.step_not_congruent_parity")
check("(parity, pair parity) does not fix the next pair parity: rows 1 and 111",
      (par([1]), pairs([1])) == (par([1, 1, 1]), pairs([1, 1, 1]))
      and pairs(r30([1])) != pairs(r30([1, 1, 1])),
      f"next rows {r30([1])} and {r30([1, 1, 1])}", "Rule30Parity.step_escalates_again")

print()
bad = [n for n, ok in RESULTS if not ok]
print(f"{len(RESULTS) - len(bad)} / {len(RESULTS)} checks passed")
sys.exit(1 if bad else 0)
